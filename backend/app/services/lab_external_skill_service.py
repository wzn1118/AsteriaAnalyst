from __future__ import annotations

import io
import json
import os
import re
import shutil
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from app.services.path_service import STORAGE_DIR


DEFAULT_ANTHROPIC_KNOWLEDGE_WORK_PLUGINS_REPO = "https://github.com/anthropics/knowledge-work-plugins"
DEFAULT_ANTHROPIC_SKILLS_REPO = DEFAULT_ANTHROPIC_KNOWLEDGE_WORK_PLUGINS_REPO
LEGACY_ANTHROPIC_SKILLS_REPO = "https://github.com/anthropics/skills"
MAX_SKILLS_PER_INSTALL = 160
MAX_INSTRUCTION_CHARS_PER_SKILL = 24000
MAX_INSTRUCTION_CHARS_PER_PLUGIN = 52000
MAX_TOTAL_INSTRUCTION_CHARS = 180000
MAX_FILES_PER_SKILL = 80
MAX_FILES_PER_PLUGIN = 800
MAX_BYTES_PER_FILE = 512_000
MAX_BYTES_PER_PLUGIN_FILE = 5_000_000
MAX_PLUGIN_README_CHARS = 16000
MAX_PLUGIN_CONNECTORS_CHARS = 12000
MAX_PLUGIN_COMMAND_CHARS = 12000
MAX_PLUGIN_MCP_CHARS = 20000
MAX_PLUGIN_SKILLS_PER_PLUGIN = 160
MAX_COMMANDS_PER_PLUGIN = 120
SKIPPED_PACKAGE_PARTS = {
    ".git",
    ".github",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_slug(value: str, fallback: str = "skill") -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", str(value or "").strip().lower()).strip(".-")
    return slug[:96] or fallback


def _skills_root() -> Path:
    override = os.getenv("ASTERIA_LAB_EXTERNAL_SKILLS_DIR")
    root = Path(override).expanduser().resolve() if override else (STORAGE_DIR / "lab_external_skills").resolve()
    root.mkdir(parents=True, exist_ok=True)
    (root / "packages").mkdir(parents=True, exist_ok=True)
    return root


def _manifest_path() -> Path:
    return _skills_root() / "manifest.json"


def _packages_root() -> Path:
    root = _skills_root() / "packages"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _load_manifest() -> dict[str, Any]:
    path = _manifest_path()
    if not path.exists():
        return {"version": 1, "skills": []}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"version": 1, "skills": []}
    skills = payload.get("skills") if isinstance(payload, dict) else []
    if not isinstance(skills, list):
        skills = []
    return {"version": 1, "skills": [item for item in skills if isinstance(item, dict)]}


def _save_manifest(manifest: dict[str, Any]) -> None:
    root = _skills_root()
    payload = {
        "version": 1,
        "updated_at": _now_iso(),
        "skills": sorted(list(manifest.get("skills") or []), key=lambda item: str(item.get("id") or "")),
    }
    path = _manifest_path()
    temp_path = root / f"manifest.tmp.{uuid.uuid4().hex}.json"
    try:
        temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        temp_path.replace(path)
    finally:
        try:
            if temp_path.exists():
                temp_path.unlink()
        except Exception:
            pass


def _skill_records_by_id(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in list(manifest.get("skills") or []):
        if not isinstance(item, dict):
            continue
        skill_id = str(item.get("id") or "").strip()
        if skill_id:
            result[skill_id] = item
    return result


def _parse_github_repo_url(source_url: str) -> tuple[str, str, str]:
    parsed = urlparse(str(source_url or "").strip())
    if parsed.scheme != "https" or parsed.netloc.lower() != "github.com":
        raise ValueError("Only https://github.com/{owner}/{repo} skill sources are supported.")
    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) < 2:
        raise ValueError("GitHub skill source must include both owner and repo.")
    owner = parts[0]
    repo = parts[1]
    if repo.endswith(".git"):
        repo = repo[:-4]
    embedded_ref = ""
    if len(parts) >= 4 and parts[2] == "tree":
        embedded_ref = "/".join(parts[3:])
    return owner, repo, embedded_ref


def _http_get(url: str, *, accept: str = "application/json") -> bytes:
    request = Request(
        url,
        headers={
            "Accept": accept,
            "User-Agent": "Asteria-Lab-External-Skills",
        },
    )
    try:
        with urlopen(request, timeout=60) as response:
            return response.read()
    except HTTPError as exc:
        raise ValueError(f"GitHub request failed with HTTP {exc.code}: {url}") from exc
    except URLError as exc:
        raise ValueError(f"GitHub request failed: {exc.reason}") from exc


def _github_default_branch(owner: str, repo: str) -> str:
    try:
        raw = _http_get(f"https://api.github.com/repos/{owner}/{repo}")
        payload = json.loads(raw.decode("utf-8"))
    except Exception:
        return "main"
    branch = str(payload.get("default_branch") or "").strip() if isinstance(payload, dict) else ""
    return branch or "main"


def _download_github_archive(source_url: str, ref: str | None = None) -> tuple[bytes, str, str, str]:
    owner, repo, embedded_ref = _parse_github_repo_url(source_url)
    resolved_ref = str(ref or embedded_ref or "").strip() or _github_default_branch(owner, repo)
    archive_url = f"https://api.github.com/repos/{owner}/{repo}/zipball/{quote(resolved_ref, safe='')}"
    return _http_get(archive_url, accept="application/zip"), owner, repo, resolved_ref


def _safe_zip_parts(name: str) -> tuple[str, ...] | None:
    parts = PurePosixPath(str(name or "")).parts
    if not parts or any(part in {"", ".", ".."} for part in parts):
        return None
    if str(name).startswith("/") or "\\" in str(name):
        return None
    return tuple(parts)


def _parse_skill_frontmatter(markdown: str) -> tuple[dict[str, str], str]:
    text = markdown.lstrip("\ufeff")
    if not text.startswith("---"):
        return {}, text
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    end_index = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = index
            break
    if end_index is None:
        return {}, text
    metadata: dict[str, str] = {}
    for line in lines[1:end_index]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        clean_key = key.strip().lower()
        clean_value = value.strip().strip("'\"")
        if clean_key:
            metadata[clean_key] = clean_value
    body = "\n".join(lines[end_index + 1 :]).strip()
    return metadata, body


def _skill_source_path(parent_parts: tuple[str, ...]) -> str:
    parts = list(parent_parts)
    if "skills" in parts:
        start = parts.index("skills")
        return "/".join(parts[start:])
    return "/".join(parts[1:] if len(parts) > 1 else parts)


def _copy_skill_from_archive(
    archive: zipfile.ZipFile,
    parent_parts: tuple[str, ...],
    package_dir: Path,
) -> int:
    package_root = _packages_root().resolve()
    if package_dir.exists():
        resolved = package_dir.resolve()
        if not (resolved == package_root or package_root in resolved.parents):
            raise ValueError("Refusing to replace a skill package outside the Lab skills directory.")
        shutil.rmtree(package_dir)
    package_dir.mkdir(parents=True, exist_ok=True)
    file_count = 0
    for info in archive.infolist():
        if info.is_dir():
            continue
        parts = _safe_zip_parts(info.filename)
        if not parts or len(parts) <= len(parent_parts) or parts[: len(parent_parts)] != parent_parts:
            continue
        relative_parts = parts[len(parent_parts) :]
        if any(part in SKIPPED_PACKAGE_PARTS for part in relative_parts):
            continue
        if file_count >= MAX_FILES_PER_SKILL and relative_parts[-1].lower() != "skill.md":
            continue
        if int(getattr(info, "file_size", 0) or 0) > MAX_BYTES_PER_FILE and relative_parts[-1].lower() != "skill.md":
            continue
        target = package_dir.joinpath(*relative_parts).resolve()
        if not (target == package_dir.resolve() or package_dir.resolve() in target.parents):
            raise ValueError("Refusing to extract a skill file outside the package directory.")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(archive.read(info))
        file_count += 1
    return file_count


def _copy_package_from_archive(
    archive: zipfile.ZipFile,
    parent_parts: tuple[str, ...],
    package_dir: Path,
    *,
    max_files: int,
    max_bytes_per_file: int,
    required_filenames: set[str] | None = None,
) -> int:
    package_root = _packages_root().resolve()
    if package_dir.exists():
        resolved = package_dir.resolve()
        if not (resolved == package_root or package_root in resolved.parents):
            raise ValueError("Refusing to replace a skill package outside the Lab skills directory.")
        shutil.rmtree(package_dir)
    package_dir.mkdir(parents=True, exist_ok=True)
    file_count = 0
    required = {name.lower() for name in (required_filenames or set())}
    package_resolved = package_dir.resolve()
    for info in archive.infolist():
        if info.is_dir():
            continue
        parts = _safe_zip_parts(info.filename)
        if not parts or len(parts) <= len(parent_parts) or parts[: len(parent_parts)] != parent_parts:
            continue
        relative_parts = parts[len(parent_parts) :]
        if any(part in SKIPPED_PACKAGE_PARTS for part in relative_parts):
            continue
        filename = relative_parts[-1].lower()
        is_required = filename in required
        if file_count >= max_files and not is_required:
            continue
        if int(getattr(info, "file_size", 0) or 0) > max_bytes_per_file and not is_required:
            continue
        target = package_dir.joinpath(*relative_parts).resolve()
        if not (target == package_resolved or package_resolved in target.parents):
            raise ValueError("Refusing to extract a skill file outside the package directory.")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(archive.read(info))
        file_count += 1
    return file_count


def _indexed_archive_files(archive: zipfile.ZipFile) -> list[tuple[zipfile.ZipInfo, tuple[str, ...]]]:
    indexed: list[tuple[zipfile.ZipInfo, tuple[str, ...]]] = []
    for info in archive.infolist():
        if info.is_dir():
            continue
        parts = _safe_zip_parts(info.filename)
        if parts:
            indexed.append((info, parts))
    return indexed


def _copy_indexed_package_from_archive(
    archive: zipfile.ZipFile,
    indexed_files: list[tuple[zipfile.ZipInfo, tuple[str, ...]]],
    parent_parts: tuple[str, ...],
    package_dir: Path,
    *,
    max_files: int,
    max_bytes_per_file: int,
    required_filenames: set[str] | None = None,
) -> int:
    package_root = _packages_root().resolve()
    if package_dir.exists():
        resolved = package_dir.resolve()
        if not (resolved == package_root or package_root in resolved.parents):
            raise ValueError("Refusing to replace a skill package outside the Lab skills directory.")
        shutil.rmtree(package_dir)
    package_dir.mkdir(parents=True, exist_ok=True)
    file_count = 0
    required = {name.lower() for name in (required_filenames or set())}
    package_resolved = package_dir.resolve()
    parent_len = len(parent_parts)
    for info, parts in indexed_files:
        if len(parts) <= parent_len or parts[:parent_len] != parent_parts:
            continue
        relative_parts = parts[parent_len:]
        if any(part in SKIPPED_PACKAGE_PARTS for part in relative_parts):
            continue
        filename = relative_parts[-1].lower()
        is_required = filename in required
        if file_count >= max_files and not is_required:
            continue
        if int(getattr(info, "file_size", 0) or 0) > max_bytes_per_file and not is_required:
            continue
        target = package_dir.joinpath(*relative_parts).resolve()
        if not (target == package_resolved or package_resolved in target.parents):
            raise ValueError("Refusing to extract a skill file outside the package directory.")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(archive.read(info))
        file_count += 1
    return file_count


def _read_text(path: Path, limit: int | None = None) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="replace")
    if limit is not None and len(text) > limit:
        return text[:limit]
    return text


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(_read_text(path))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _count_local_package_files(local_dir: Path, *, max_files: int, max_bytes_per_file: int) -> int:
    file_count = 0
    for item in local_dir.rglob("*"):
        if not item.is_file():
            continue
        try:
            relative_parts = item.relative_to(local_dir).parts
        except ValueError:
            relative_parts = item.parts
        if any(part in SKIPPED_PACKAGE_PARTS for part in relative_parts):
            continue
        file_count += 1
        if file_count > max_files:
            raise ValueError(f"Local skill package exceeds file limit ({max_files}): {local_dir}")
        try:
            if item.stat().st_size > max_bytes_per_file:
                raise ValueError(f"Local skill package file exceeds size limit ({max_bytes_per_file} bytes): {item}")
        except OSError as exc:
            raise ValueError(f"Unable to stat local skill package file: {item}") from exc
    return file_count


def _relative_package_path(path: Path, package_dir: Path) -> str:
    try:
        return path.resolve().relative_to(package_dir.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def _first_markdown_paragraph(text: str, *, limit: int = 360) -> str:
    clean_lines = []
    for raw_line in str(text or "").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("|") or line.startswith("```"):
            if clean_lines:
                break
            continue
        clean_lines.append(line)
    return " ".join(" ".join(clean_lines).split())[:limit]


def _plugin_source_path(parent_parts: tuple[str, ...]) -> str:
    parts = list(parent_parts)
    return "/".join(parts[1:] if len(parts) > 1 else parts)


def _plugin_display_name(plugin_meta: dict[str, Any], package_name: str) -> str:
    for key in ("displayName", "display_name", "title", "name"):
        value = str(plugin_meta.get(key) or "").strip()
        if value:
            return value
    return package_name.replace("-", " ").title()


def _plugin_description(plugin_meta: dict[str, Any], readme_text: str) -> str:
    for key in ("description", "summary"):
        value = str(plugin_meta.get(key) or "").strip()
        if value:
            return value
    return _first_markdown_paragraph(readme_text)


def _summarize_mcp_servers(mcp_config: dict[str, Any]) -> list[dict[str, Any]]:
    servers = mcp_config.get("mcpServers")
    if not isinstance(servers, dict):
        servers = mcp_config.get("servers")
    if not isinstance(servers, dict):
        return []
    result: list[dict[str, Any]] = []
    for name, payload in servers.items():
        if not isinstance(payload, dict):
            payload = {}
        result.append(
            {
                "name": str(name or ""),
                "type": payload.get("type") or payload.get("transport") or "",
                "url": payload.get("url") or payload.get("endpoint") or "",
                "command": payload.get("command") or "",
                "oauth": bool(payload.get("oauth") or payload.get("authorization") or payload.get("auth")),
            }
        )
    return [item for item in result if item.get("name")]


def _extract_command_description(markdown: str) -> str:
    metadata, body = _parse_skill_frontmatter(markdown)
    for key in ("description", "summary"):
        if metadata.get(key):
            return str(metadata[key])
    return _first_markdown_paragraph(body or markdown, limit=280)


def _collect_plugin_commands(package_dir: Path, readme_text: str) -> list[dict[str, Any]]:
    commands: list[dict[str, Any]] = []
    seen: set[str] = set()
    commands_dir = package_dir / "commands"
    if commands_dir.exists() and commands_dir.is_dir():
        for path in sorted(commands_dir.rglob("*.md"))[:MAX_COMMANDS_PER_PLUGIN]:
            command_text = _read_text(path, MAX_PLUGIN_COMMAND_CHARS)
            command_name = "/" + path.stem.strip().lstrip("/")
            if command_name in seen:
                continue
            seen.add(command_name)
            commands.append(
                {
                    "name": command_name,
                    "description": _extract_command_description(command_text),
                    "path": _relative_package_path(path, package_dir),
                    "instruction_chars": len(command_text),
                }
            )
    for line in str(readme_text or "").splitlines():
        if len(commands) >= MAX_COMMANDS_PER_PLUGIN:
            break
        stripped = line.strip()
        if not stripped.startswith("|") or "/" not in stripped:
            continue
        cells = [cell.strip().strip("`") for cell in stripped.strip("|").split("|")]
        if not cells:
            continue
        command_cell = next((cell for cell in cells if cell.startswith("/")), "")
        if not command_cell:
            continue
        command_name = command_cell.split()[0].strip()
        if command_name in seen:
            continue
        seen.add(command_name)
        description = next((cell for cell in cells if cell and cell != command_cell and not set(cell) <= {"-", ":"}), "")
        commands.append({"name": command_name, "description": description, "path": "README.md", "instruction_chars": 0})
    return commands


def _collect_plugin_skills(package_dir: Path) -> list[dict[str, Any]]:
    skills_dir = package_dir / "skills"
    if not skills_dir.exists() or not skills_dir.is_dir():
        return []
    skills: list[dict[str, Any]] = []
    for skill_md_path in sorted(skills_dir.rglob("SKILL.md"))[:MAX_PLUGIN_SKILLS_PER_PLUGIN]:
        markdown = _read_text(skill_md_path)
        metadata, body = _parse_skill_frontmatter(markdown)
        skill_dir = skill_md_path.parent
        skill_id = _safe_slug(skill_dir.name)
        skills.append(
            {
                "id": skill_id,
                "name": metadata.get("name") or skill_dir.name.replace("-", " ").title(),
                "description": metadata.get("description") or _first_markdown_paragraph(body or markdown),
                "path": _relative_package_path(skill_dir, package_dir),
                "skill_md_path": _relative_package_path(skill_md_path, package_dir),
                "instruction_chars": len(markdown),
                "instruction_excerpt": " ".join((body or markdown).split())[:360],
            }
        )
    return skills


def _selection_feature_lines(selected_features: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for feature in selected_features:
        if not isinstance(feature, dict):
            continue
        name = str(feature.get("name") or feature.get("feature_id") or "").strip()
        kind = str(feature.get("feature_kind") or "").strip()
        description = str(feature.get("description") or "").strip()
        if not name:
            continue
        suffix = f": {description}" if description else ""
        lines.append(f"- {kind or 'feature'} {name}{suffix}")
    return lines


def _plugin_instruction_text(record: dict[str, Any], selected_features: list[dict[str, Any]] | None = None) -> str:
    package_dir = Path(str(record.get("package_path") or ""))
    if not package_dir.exists():
        return ""
    selected_features = [item for item in list(selected_features or []) if isinstance(item, dict)]
    sections = [
        f"# Claude Knowledge Work Plugin: {record.get('name') or record.get('plugin_name') or record.get('id')}",
        f"Plugin id: {record.get('id') or ''}",
        f"Description: {record.get('description') or ''}",
        f"Source: {record.get('source_repo') or record.get('source_url') or ''}@{record.get('source_ref') or ''}",
    ]
    if selected_features:
        sections.append("\n## Selected Lab Report Features")
        sections.append(
            "These selected plugin functions must participate in Analysis Lab report writing, not as a separate one-off trial. "
            "Use them to shape method selection, evidence interpretation, report structure, quality review, and revision guidance."
        )
        sections.extend(_selection_feature_lines(selected_features))
    commands = record.get("commands") if isinstance(record.get("commands"), list) else []
    if commands:
        sections.append("\n## Slash Commands")
        for command in commands[:MAX_COMMANDS_PER_PLUGIN]:
            if isinstance(command, dict):
                sections.append(f"- {command.get('name') or ''}: {command.get('description') or ''}".strip())
    mcp_servers = record.get("mcp_servers") if isinstance(record.get("mcp_servers"), list) else []
    if mcp_servers:
        sections.append("\n## MCP Connectors")
        for server in mcp_servers:
            if isinstance(server, dict):
                label = server.get("name") or ""
                server_type = server.get("type") or server.get("command") or server.get("url") or ""
                sections.append(f"- {label}: {server_type}".strip())
    readme_path = package_dir / "README.md"
    readme_text = _read_text(readme_path, MAX_PLUGIN_README_CHARS)
    if readme_text:
        sections.append("\n## Plugin README")
        sections.append(readme_text)
    connectors_text = _read_text(package_dir / "CONNECTORS.md", MAX_PLUGIN_CONNECTORS_CHARS)
    if connectors_text:
        sections.append("\n## Connector Notes")
        sections.append(connectors_text)
    mcp_text = _read_text(package_dir / ".mcp.json", MAX_PLUGIN_MCP_CHARS)
    if mcp_text:
        sections.append("\n## MCP Configuration")
        sections.append(mcp_text)
    for plugin_skill in list(record.get("plugin_skills") or [])[:MAX_PLUGIN_SKILLS_PER_PLUGIN]:
        if not isinstance(plugin_skill, dict):
            continue
        relative_path = str(plugin_skill.get("skill_md_path") or "").strip()
        if not relative_path:
            continue
        skill_text = _read_text(package_dir / relative_path, MAX_INSTRUCTION_CHARS_PER_SKILL)
        if not skill_text:
            continue
        sections.append(f"\n## Embedded Skill: {plugin_skill.get('name') or plugin_skill.get('id') or relative_path}")
        sections.append(skill_text)
    return "\n".join(part for part in sections if str(part).strip())


def _record_plugin_from_package_dir(
    package_dir: Path,
    *,
    skill_id: str,
    package_name: str,
    source: str,
    source_url: str,
    source_repo: str,
    source_ref: str,
    source_path: str,
    mount: bool,
    previous: dict[str, Any] | None = None,
    file_count: int | None = None,
) -> dict[str, Any]:
    plugin_json_path = package_dir / ".claude-plugin" / "plugin.json"
    plugin_meta = _read_json(plugin_json_path)
    readme_text = _read_text(package_dir / "README.md", MAX_PLUGIN_README_CHARS)
    mcp_config = _read_json(package_dir / ".mcp.json")
    plugin_skills = _collect_plugin_skills(package_dir)
    commands = _collect_plugin_commands(package_dir, readme_text)
    previous = previous or {}
    updated_at = _now_iso()
    total_instruction_chars = len(readme_text)
    for plugin_skill in plugin_skills:
        total_instruction_chars += int(plugin_skill.get("instruction_chars") or 0)
    primary_skill_md = ""
    if plugin_skills:
        primary_skill_md = str(package_dir / str(plugin_skills[0].get("skill_md_path") or ""))
    record = {
        "id": skill_id,
        "name": _plugin_display_name(plugin_meta, package_name),
        "description": _plugin_description(plugin_meta, readme_text),
        "license": plugin_meta.get("license") or "",
        "source": source,
        "source_url": source_url,
        "source_repo": source_repo,
        "source_ref": source_ref,
        "source_path": source_path,
        "package_path": str(package_dir),
        "skill_md_path": primary_skill_md,
        "mounted": bool(mount or previous.get("mounted")),
        "installed_at": previous.get("installed_at") or updated_at,
        "updated_at": updated_at,
        "file_count": int(file_count if file_count is not None else sum(1 for item in package_dir.rglob("*") if item.is_file())),
        "instruction_chars": total_instruction_chars,
        "instruction_excerpt": _first_markdown_paragraph(readme_text) or " ".join(
            str(item.get("instruction_excerpt") or "") for item in plugin_skills[:2]
        )[:360],
        "package_kind": "claude_plugin",
        "kind": "claude_plugin",
        "plugin_name": plugin_meta.get("name") or package_name,
        "plugin_version": plugin_meta.get("version") or "",
        "plugin_author": plugin_meta.get("author") or "",
        "plugin_manifest_path": str(plugin_json_path),
        "readme_path": str(package_dir / "README.md") if (package_dir / "README.md").exists() else "",
        "mcp_config_path": str(package_dir / ".mcp.json") if (package_dir / ".mcp.json").exists() else "",
        "mcp_config": mcp_config,
        "mcp_servers": _summarize_mcp_servers(mcp_config),
        "commands": commands,
        "plugin_skills": plugin_skills,
        "skill_count": len(plugin_skills),
        "command_count": len(commands),
        "mcp_server_count": len(_summarize_mcp_servers(mcp_config)),
    }
    return record


def _install_from_archive(
    archive_bytes: bytes,
    *,
    owner: str,
    repo: str,
    source_url: str,
    source_ref: str,
    mount: bool,
) -> dict[str, Any]:
    manifest = _load_manifest()
    existing = _skill_records_by_id(manifest)
    installed: list[dict[str, Any]] = []
    updated_at = _now_iso()
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        indexed_files = _indexed_archive_files(archive)
        plugin_dirs: list[tuple[str, ...]] = []
        candidate_dirs: list[tuple[str, ...]] = []
        for _info, parts in indexed_files:
            if parts and len(parts) >= 3 and parts[-2:] == (".claude-plugin", "plugin.json"):
                plugin_dirs.append(parts[:-2])
            if parts and parts[-1].lower() == "skill.md":
                candidate_dirs.append(parts[:-1])
        if plugin_dirs:
            selected_plugin_dirs = sorted(set(plugin_dirs))[:MAX_SKILLS_PER_INSTALL]
            if not selected_plugin_dirs:
                raise ValueError("No Claude plugin manifests were found in the GitHub archive.")
            for parent_parts in selected_plugin_dirs:
                source_path = _plugin_source_path(parent_parts)
                package_name = parent_parts[-1]
                skill_id = _safe_slug(f"{owner}-{repo}-{package_name}")
                package_dir = (_packages_root() / skill_id).resolve()
                file_count = _copy_indexed_package_from_archive(
                    archive,
                    indexed_files,
                    parent_parts,
                    package_dir,
                    max_files=MAX_FILES_PER_PLUGIN,
                    max_bytes_per_file=MAX_BYTES_PER_PLUGIN_FILE,
                    required_filenames={"plugin.json", "README.md", ".mcp.json", "CONNECTORS.md", "SKILL.md"},
                )
                previous = existing.get(skill_id, {})
                record = _record_plugin_from_package_dir(
                    package_dir,
                    skill_id=skill_id,
                    package_name=package_name,
                    source="github",
                    source_url=source_url,
                    source_repo=f"{owner}/{repo}",
                    source_ref=source_ref,
                    source_path=source_path,
                    mount=mount,
                    previous=previous,
                    file_count=file_count,
                )
                existing[skill_id] = record
                installed.append(record)
            manifest["skills"] = list(existing.values())
            _save_manifest(manifest)
            return {
                "summary": _summary(list(existing.values())),
                "installed_count": len(installed),
                "skills": [_public_skill_record(item) for item in installed],
                "source_url": source_url,
                "source_ref": source_ref,
            }
        under_skills = [parts for parts in candidate_dirs if "skills" in parts]
        selected_dirs = (under_skills or candidate_dirs)[:MAX_SKILLS_PER_INSTALL]
        if not selected_dirs:
            raise ValueError("No SKILL.md files were found in the GitHub archive.")
        for parent_parts in selected_dirs:
            source_path = _skill_source_path(parent_parts)
            package_name = parent_parts[-1]
            skill_id = _safe_slug(f"{owner}-{repo}-{package_name}")
            package_dir = (_packages_root() / skill_id).resolve()
            file_count = _copy_skill_from_archive(archive, parent_parts, package_dir)
            skill_md_path = package_dir / "SKILL.md"
            skill_md = _read_text(skill_md_path)
            metadata, body = _parse_skill_frontmatter(skill_md)
            previous = existing.get(skill_id, {})
            record = {
                "id": skill_id,
                "name": metadata.get("name") or package_name.replace("-", " ").title(),
                "description": metadata.get("description") or "",
                "license": metadata.get("license") or "",
                "source": "github",
                "source_url": source_url,
                "source_repo": f"{owner}/{repo}",
                "source_ref": source_ref,
                "source_path": source_path,
                "package_path": str(package_dir),
                "skill_md_path": str(skill_md_path),
                "mounted": bool(mount or previous.get("mounted")),
                "installed_at": previous.get("installed_at") or updated_at,
                "updated_at": updated_at,
                "file_count": file_count,
                "instruction_chars": len(skill_md),
                "instruction_excerpt": " ".join((body or skill_md).split())[:360],
            }
            existing[skill_id] = record
            installed.append(record)
    manifest["skills"] = list(existing.values())
    _save_manifest(manifest)
    return {
        "summary": _summary(list(existing.values())),
        "installed_count": len(installed),
        "skills": [_public_skill_record(item) for item in installed],
        "source_url": source_url,
        "source_ref": source_ref,
    }


def _summary(skills: list[dict[str, Any]]) -> dict[str, Any]:
    mounted = [item for item in skills if item.get("mounted")]
    plugins = [item for item in skills if item.get("package_kind") == "claude_plugin"]
    mounted_plugins = [item for item in plugins if item.get("mounted")]
    return {
        "count": len(skills),
        "mounted_count": len(mounted),
        "plugin_count": len(plugins),
        "mounted_plugin_count": len(mounted_plugins),
        "embedded_skill_count": sum(int(item.get("skill_count") or 0) for item in plugins),
        "command_count": sum(int(item.get("command_count") or 0) for item in plugins),
        "mcp_server_count": sum(int(item.get("mcp_server_count") or 0) for item in plugins),
        "skill_ids": [str(item.get("id") or "") for item in skills if item.get("id")],
        "mounted_skill_ids": [str(item.get("id") or "") for item in mounted if item.get("id")],
    }


def _public_skill_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": record.get("id"),
        "name": record.get("name"),
        "description": record.get("description") or "",
        "license": record.get("license") or "",
        "source": record.get("source") or "",
        "source_url": record.get("source_url") or "",
        "source_repo": record.get("source_repo") or "",
        "source_ref": record.get("source_ref") or "",
        "source_path": record.get("source_path") or "",
        "package_path": record.get("package_path") or "",
        "skill_md_path": record.get("skill_md_path") or "",
        "mounted": bool(record.get("mounted")),
        "installed_at": record.get("installed_at") or "",
        "updated_at": record.get("updated_at") or "",
        "file_count": int(record.get("file_count") or 0),
        "instruction_chars": int(record.get("instruction_chars") or 0),
        "instruction_excerpt": record.get("instruction_excerpt") or "",
        "package_kind": record.get("package_kind") or record.get("kind") or "skill",
        "kind": record.get("kind") or record.get("package_kind") or "skill",
        "plugin_name": record.get("plugin_name") or "",
        "plugin_version": record.get("plugin_version") or "",
        "plugin_author": record.get("plugin_author") or "",
        "plugin_manifest_path": record.get("plugin_manifest_path") or "",
        "readme_path": record.get("readme_path") or "",
        "mcp_config_path": record.get("mcp_config_path") or "",
        "skill_count": int(record.get("skill_count") or 0),
        "command_count": int(record.get("command_count") or 0),
        "mcp_server_count": int(record.get("mcp_server_count") or 0),
        "plugin_skills": list(record.get("plugin_skills") or [])[:MAX_PLUGIN_SKILLS_PER_PLUGIN],
        "commands": list(record.get("commands") or [])[:MAX_COMMANDS_PER_PLUGIN],
        "mcp_servers": list(record.get("mcp_servers") or []),
    }


def _read_skill_record_from_local_dir(local_dir: Path) -> tuple[str, dict[str, Any]]:
    if not local_dir.exists():
        raise FileNotFoundError(f"Local skill path not found: {local_dir}")
    if not local_dir.is_dir():
        raise ValueError(f"Local skill path must be a directory: {local_dir}")
    plugin_json_path = local_dir / ".claude-plugin" / "plugin.json"
    if plugin_json_path.exists() and plugin_json_path.is_file():
        file_count = _count_local_package_files(
            local_dir,
            max_files=MAX_FILES_PER_PLUGIN,
            max_bytes_per_file=MAX_BYTES_PER_PLUGIN_FILE,
        )
        skill_id = _safe_slug(f"local-{local_dir.name}")
        record = _record_plugin_from_package_dir(
            local_dir,
            skill_id=skill_id,
            package_name=local_dir.name,
            source="local",
            source_url="",
            source_repo="",
            source_ref="",
            source_path=str(local_dir),
            mount=True,
            file_count=file_count,
        )
        return skill_id, record
    skill_md_path = (local_dir / "SKILL.md").resolve()
    if not skill_md_path.exists() or not skill_md_path.is_file():
        raise ValueError(f"Local skill directory must contain SKILL.md or .claude-plugin/plugin.json: {local_dir}")
    markdown = _read_text(skill_md_path)
    metadata, body = _parse_skill_frontmatter(markdown)
    skill_name = str(metadata.get("name") or local_dir.name).strip() or local_dir.name
    skill_id = _safe_slug(f"local-{local_dir.name}")
    file_count = _count_local_package_files(
        local_dir,
        max_files=MAX_FILES_PER_SKILL,
        max_bytes_per_file=MAX_BYTES_PER_FILE,
    )
    updated_at = _now_iso()
    record = {
        "id": skill_id,
        "name": skill_name,
        "description": metadata.get("description") or "",
        "license": metadata.get("license") or "",
        "source": "local",
        "source_url": "",
        "source_repo": "",
        "source_ref": "",
        "source_path": str(local_dir),
        "package_path": str(local_dir),
        "skill_md_path": str(skill_md_path),
        "mounted": True,
        "installed_at": updated_at,
        "updated_at": updated_at,
        "file_count": file_count,
        "instruction_chars": len(markdown),
        "instruction_excerpt": " ".join((body or markdown).split())[:360],
    }
    return skill_id, record


def list_lab_external_skills() -> dict[str, Any]:
    manifest = _load_manifest()
    skills = list(_skill_records_by_id(manifest).values())
    return {
        "summary": _summary(skills),
        "skills": [_public_skill_record(item) for item in skills],
        "default_source_url": DEFAULT_ANTHROPIC_SKILLS_REPO,
        "storage_dir": str(_skills_root()),
    }


def install_lab_external_skills(source_url: str, ref: str | None = None, *, mount: bool = True) -> dict[str, Any]:
    clean_source = str(source_url or DEFAULT_ANTHROPIC_SKILLS_REPO).strip() or DEFAULT_ANTHROPIC_SKILLS_REPO
    archive_bytes, owner, repo, resolved_ref = _download_github_archive(clean_source, ref)
    return _install_from_archive(
        archive_bytes,
        owner=owner,
        repo=repo,
        source_url=clean_source,
        source_ref=resolved_ref,
        mount=mount,
    )


def import_lab_external_skill_from_local_path(local_path: str, *, mount: bool = True) -> dict[str, Any]:
    clean_path = str(local_path or "").strip()
    if not clean_path:
        raise ValueError("Local skill path is required.")
    local_dir = Path(clean_path).expanduser().resolve()
    manifest = _load_manifest()
    existing = _skill_records_by_id(manifest)
    skill_id, record = _read_skill_record_from_local_dir(local_dir)
    previous = existing.get(skill_id, {})
    record["mounted"] = bool(mount or previous.get("mounted"))
    record["installed_at"] = previous.get("installed_at") or record["installed_at"]
    existing[skill_id] = record
    manifest["skills"] = list(existing.values())
    _save_manifest(manifest)
    return {
        "summary": _summary(list(existing.values())),
        "installed_count": 1,
        "skills": [_public_skill_record(record)],
        "source_url": "",
        "source_ref": "",
        "local_path": str(local_dir),
    }


def set_lab_external_skill_mounted(skill_id: str, mounted: bool) -> dict[str, Any]:
    clean_id = str(skill_id or "").strip()
    manifest = _load_manifest()
    records = _skill_records_by_id(manifest)
    record = records.get(clean_id)
    if not record:
        raise FileNotFoundError(f"External skill not found: {clean_id}")
    record["mounted"] = bool(mounted)
    record["updated_at"] = _now_iso()
    manifest["skills"] = list(records.values())
    _save_manifest(manifest)
    return {"summary": _summary(list(records.values())), "skill": _public_skill_record(record)}


def delete_lab_external_skill(skill_id: str) -> dict[str, Any]:
    clean_id = str(skill_id or "").strip()
    manifest = _load_manifest()
    records = _skill_records_by_id(manifest)
    record = records.pop(clean_id, None)
    if not record:
        raise FileNotFoundError(f"External skill not found: {clean_id}")
    package_path = Path(str(record.get("package_path") or ""))
    packages_root = _packages_root().resolve()
    if package_path.exists():
        resolved = package_path.resolve()
        if not (resolved == packages_root or packages_root in resolved.parents):
            raise ValueError("Refusing to delete a skill package outside the Lab skills directory.")
        shutil.rmtree(resolved)
    manifest["skills"] = list(records.values())
    _save_manifest(manifest)
    return {"summary": _summary(list(records.values())), "deleted_skill_id": clean_id}


def list_mounted_lab_external_skills() -> list[dict[str, Any]]:
    manifest = _load_manifest()
    return [
        _public_skill_record(item)
        for item in _skill_records_by_id(manifest).values()
        if item.get("mounted")
    ]


def _normalize_feature_selections(values: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    selections: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for raw in values or []:
        if not isinstance(raw, dict):
            continue
        plugin_id = str(raw.get("plugin_id") or raw.get("skill_id") or "").strip()
        feature_kind = str(raw.get("feature_kind") or "").strip()
        feature_id = str(raw.get("feature_id") or "").strip()
        if feature_kind not in {"command", "embedded_skill"} or not plugin_id or not feature_id:
            continue
        key = (plugin_id, feature_kind, feature_id)
        if key in seen:
            continue
        seen.add(key)
        selections.append(
            {
                "plugin_id": plugin_id,
                "feature_kind": feature_kind,
                "feature_id": feature_id,
                "name": str(raw.get("name") or feature_id).strip(),
                "description": str(raw.get("description") or "").strip(),
                "path": str(raw.get("path") or "").strip(),
                "selection_source": str(raw.get("selection_source") or "lab_ui").strip(),
            }
        )
    return selections


def _selected_features_for_record(record: dict[str, Any], selections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    plugin_id = str(record.get("id") or "")
    if not plugin_id:
        return []
    available: dict[tuple[str, str], dict[str, Any]] = {}
    for command in list(record.get("commands") or []):
        if isinstance(command, dict):
            feature_id = str(command.get("name") or "").strip()
            if feature_id:
                available[("command", feature_id)] = {
                    "feature_kind": "command",
                    "feature_id": feature_id,
                    "name": feature_id,
                    "description": str(command.get("description") or ""),
                    "path": str(command.get("path") or ""),
                }
    for plugin_skill in list(record.get("plugin_skills") or []):
        if isinstance(plugin_skill, dict):
            feature_id = str(plugin_skill.get("id") or plugin_skill.get("path") or "").strip()
            if feature_id:
                available[("embedded_skill", feature_id)] = {
                    "feature_kind": "embedded_skill",
                    "feature_id": feature_id,
                    "name": str(plugin_skill.get("name") or feature_id),
                    "description": str(plugin_skill.get("description") or ""),
                    "path": str(plugin_skill.get("path") or plugin_skill.get("skill_md_path") or ""),
                }
    selected: list[dict[str, Any]] = []
    for selection in selections:
        if selection.get("plugin_id") != plugin_id:
            continue
        base = available.get((str(selection.get("feature_kind") or ""), str(selection.get("feature_id") or "")), {})
        selected.append({**base, **selection})
    return selected


def lab_external_skill_runtime_context(
    skill_ids: list[str] | None = None,
    feature_selections: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    manifest = _load_manifest()
    records = _skill_records_by_id(manifest)
    selected_feature_rows = _normalize_feature_selections(feature_selections)
    requested_ids = []
    for raw in skill_ids or []:
        clean = str(raw or "").strip()
        if clean and clean not in requested_ids:
            requested_ids.append(clean)
    for selection in selected_feature_rows:
        plugin_id = str(selection.get("plugin_id") or "")
        if plugin_id and plugin_id not in requested_ids:
            requested_ids.append(plugin_id)
    selected_ids = requested_ids or [
        str(item.get("id") or "")
        for item in records.values()
        if item.get("mounted") and item.get("id")
    ]
    mounted_records: list[tuple[dict[str, Any], list[dict[str, Any]]]] = []
    for skill_id in selected_ids:
        record = records.get(skill_id)
        if not record or not record.get("mounted"):
            continue
        mounted_records.append((record, _selected_features_for_record(record, selected_feature_rows)))
    skills: list[dict[str, Any]] = []
    total_chars = 0
    for record, selected_features in mounted_records:
        if record.get("package_kind") == "claude_plugin":
            full_text = _plugin_instruction_text(record, selected_features)
        else:
            skill_md_path = Path(str(record.get("skill_md_path") or ""))
            if not skill_md_path.exists():
                continue
            full_text = _read_text(skill_md_path)
        if not full_text:
            continue
        remaining = MAX_TOTAL_INSTRUCTION_CHARS - total_chars
        if remaining <= 0:
            break
        per_package_limit = (
            MAX_INSTRUCTION_CHARS_PER_PLUGIN
            if record.get("package_kind") == "claude_plugin"
            else MAX_INSTRUCTION_CHARS_PER_SKILL
        )
        instruction_limit = min(per_package_limit, remaining)
        instructions = full_text[:instruction_limit]
        total_chars += len(instructions)
        public_record = _public_skill_record(record)
        skills.append(
            {
                **public_record,
                "selected_features": selected_features,
                "selected_feature_count": len(selected_features),
                "instructions": instructions,
                "instructions_truncated": len(instructions) < len(full_text),
                "mcp_config": record.get("mcp_config") if record.get("package_kind") == "claude_plugin" else {},
            }
        )
    loaded_by_id = {str(item.get("id") or ""): item for item in skills if item.get("id")}
    mounted_skills: list[dict[str, Any]] = []
    for record, selected_features in mounted_records:
        public_record = _public_skill_record(record)
        skill_id = str(public_record.get("id") or "")
        loaded = loaded_by_id.get(skill_id) or {}
        instructions_included = bool(loaded)
        mounted_skills.append(
            {
                **public_record,
                "selected_features": selected_features,
                "selected_feature_count": len(selected_features),
                "instructions_included": instructions_included,
                "instructions_loaded_chars": len(str(loaded.get("instructions") or "")),
                "instructions_truncated": bool(loaded.get("instructions_truncated")) if instructions_included else False,
                "mcp_config": record.get("mcp_config") if record.get("package_kind") == "claude_plugin" else {},
            }
        )
    return {
        "contract": "analysis_lab_external_skill_context_v2",
        "enabled": bool(skills or mounted_skills),
        "count": len(skills),
        "plugin_count": sum(1 for item in skills if item.get("package_kind") == "claude_plugin"),
        "mounted_count": len(mounted_skills),
        "mounted_plugin_count": sum(1 for item in mounted_skills if item.get("package_kind") == "claude_plugin"),
        "embedded_skill_count": sum(int(item.get("skill_count") or 0) for item in skills),
        "command_count": sum(int(item.get("command_count") or 0) for item in skills),
        "mcp_server_count": sum(int(item.get("mcp_server_count") or 0) for item in skills),
        "skill_ids": [str(item.get("id") or "") for item in skills],
        "instruction_skill_count": len(skills),
        "instruction_skill_ids": [str(item.get("id") or "") for item in skills],
        "mounted_skill_ids": [str(item.get("id") or "") for item in mounted_skills],
        "requested_skill_ids": requested_ids,
        "feature_selection_count": len(selected_feature_rows),
        "feature_selections": selected_feature_rows,
        "total_instruction_chars": total_chars,
        "skills": skills,
        "mounted_skills": mounted_skills,
    }
