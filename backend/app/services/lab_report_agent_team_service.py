from __future__ import annotations

import json
import os
import re
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.models import CodexRunRequest
from app.services.codex_runtime_task_service import create_codex_run_task
from app.services.path_service import REPORTS_DIR, STORAGE_DIR


TEAM_CONTRACT_VERSION = "lab_report_agent_team_v1"
DEFAULT_SOURCE_URL = "https://github.com/openai/codex"
MAX_TEAM_FILES = 120
MAX_AGENT_FILES = 24


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_slug(value: str, fallback: str = "team") -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", str(value or "").strip().lower()).strip(".-")
    return slug[:96] or fallback


def _teams_root() -> Path:
    override = os.getenv("ASTERIA_LAB_REPORT_AGENT_TEAMS_DIR")
    root = Path(override).expanduser().resolve() if override else (STORAGE_DIR / "lab_report_agent_teams").resolve()
    root.mkdir(parents=True, exist_ok=True)
    (root / "packages").mkdir(parents=True, exist_ok=True)
    return root


def _packages_root() -> Path:
    root = _teams_root() / "packages"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _manifest_path() -> Path:
    return _teams_root() / "manifest.json"


def _load_manifest() -> dict[str, Any]:
    path = _manifest_path()
    if not path.exists():
        return {"version": 1, "teams": []}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"version": 1, "teams": []}
    teams = payload.get("teams") if isinstance(payload, dict) else []
    if not isinstance(teams, list):
        teams = []
    return {"version": 1, "teams": [item for item in teams if isinstance(item, dict)]}


def _save_manifest(manifest: dict[str, Any]) -> None:
    root = _teams_root()
    payload = {
        "version": 1,
        "updated_at": _now_iso(),
        "teams": sorted(list(manifest.get("teams") or []), key=lambda item: str(item.get("id") or "")),
    }
    temp_path = root / f"manifest.tmp.{uuid.uuid4().hex}.json"
    try:
        temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        temp_path.replace(_manifest_path())
    finally:
        try:
            if temp_path.exists():
                temp_path.unlink()
        except Exception:
            pass


def _teams_by_id(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in list(manifest.get("teams") or []):
        team_id = str(item.get("id") or "").strip()
        if team_id:
            result[team_id] = item
    return result


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _discover_agent_files(team_dir: Path) -> list[Path]:
    candidates = []
    agents_dir = team_dir / "agents"
    if agents_dir.exists():
        candidates.extend(sorted(path for path in agents_dir.rglob("*.md") if path.is_file()))
    root_agents = sorted(path for path in team_dir.glob("*.md") if path.is_file() and path.name.lower() != "readme.md")
    for path in root_agents:
        if path.name.lower() in {"team.md", "agents.md"}:
            candidates.append(path)
    unique: list[Path] = []
    seen: set[str] = set()
    for path in candidates:
        marker = str(path.resolve()).lower()
        if marker in seen:
            continue
        seen.add(marker)
        unique.append(path)
    return unique[:MAX_AGENT_FILES]


def _team_metadata_from_dir(team_dir: Path) -> dict[str, Any]:
    manifest_path = team_dir / "team.json"
    manifest_payload = {}
    if manifest_path.exists():
        try:
            manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            manifest_payload = {}
    team_name = str(manifest_payload.get("name") or team_dir.name).strip() or team_dir.name
    team_description = str(manifest_payload.get("description") or "").strip()
    agents = []
    for agent_path in _discover_agent_files(team_dir):
        relative = agent_path.relative_to(team_dir).as_posix()
        content = _read_text(agent_path)
        title = content.splitlines()[0].lstrip("# ").strip() if content.strip() else agent_path.stem
        agents.append(
            {
                "id": _safe_slug(relative.replace("/", "-"), fallback=agent_path.stem),
                "name": title or agent_path.stem,
                "role": str(manifest_payload.get("agent_roles", {}).get(relative) or "").strip(),
                "path": relative,
                "chars": len(content),
            }
        )
    return {
        "name": team_name,
        "description": team_description,
        "agents": agents,
    }


def _count_files(team_dir: Path) -> int:
    count = 0
    for path in team_dir.rglob("*"):
        if path.is_file():
            count += 1
            if count > MAX_TEAM_FILES:
                break
    return count


def _public_team_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": record.get("id"),
        "name": record.get("name") or "",
        "description": record.get("description") or "",
        "source": record.get("source") or "",
        "source_url": record.get("source_url") or "",
        "source_ref": record.get("source_ref") or "",
        "source_path": record.get("source_path") or "",
        "package_path": record.get("package_path") or "",
        "mounted": bool(record.get("mounted")),
        "installed_at": record.get("installed_at") or "",
        "updated_at": record.get("updated_at") or "",
        "version": record.get("version") or "",
        "agent_count": int(record.get("agent_count") or 0),
        "agents": list(record.get("agents") or []),
        "entry_file": record.get("entry_file") or "",
        "codex_ready": bool(record.get("codex_ready")),
    }


def _summary(teams: list[dict[str, Any]]) -> dict[str, Any]:
    mounted = [item for item in teams if item.get("mounted")]
    return {
        "count": len(teams),
        "mounted_count": len(mounted),
        "team_ids": [str(item.get("id") or "") for item in teams if item.get("id")],
        "mounted_team_ids": [str(item.get("id") or "") for item in mounted if item.get("id")],
    }


def list_lab_report_agent_teams() -> dict[str, Any]:
    manifest = _load_manifest()
    teams = list(_teams_by_id(manifest).values())
    return {
        "summary": _summary(teams),
        "teams": [_public_team_record(item) for item in teams],
        "default_source_url": DEFAULT_SOURCE_URL,
        "storage_dir": str(_teams_root()),
    }


def import_lab_report_agent_team_from_local_path(local_path: str, *, mount: bool = True) -> dict[str, Any]:
    clean_path = str(local_path or "").strip()
    if not clean_path:
        raise ValueError("Local agent team path is required.")
    team_dir = Path(clean_path).expanduser().resolve()
    if not team_dir.exists() or not team_dir.is_dir():
        raise FileNotFoundError(f"Local agent team path not found: {team_dir}")
    metadata = _team_metadata_from_dir(team_dir)
    if not metadata["agents"]:
        raise ValueError(f"Local agent team must contain at least one markdown agent file: {team_dir}")
    if _count_files(team_dir) > MAX_TEAM_FILES:
        raise ValueError(f"Local agent team exceeds file limit ({MAX_TEAM_FILES}): {team_dir}")
    manifest = _load_manifest()
    existing = _teams_by_id(manifest)
    team_id = _safe_slug(f"local-{team_dir.name}")
    updated_at = _now_iso()
    previous = existing.get(team_id, {})
    record = {
        "id": team_id,
        "name": metadata["name"],
        "description": metadata["description"],
        "source": "local",
        "source_url": "",
        "source_ref": "",
        "source_path": str(team_dir),
        "package_path": str(team_dir),
        "mounted": bool(mount or previous.get("mounted")),
        "installed_at": previous.get("installed_at") or updated_at,
        "updated_at": updated_at,
        "version": str(previous.get("version") or "local"),
        "agent_count": len(metadata["agents"]),
        "agents": metadata["agents"],
        "entry_file": "team.json" if (team_dir / "team.json").exists() else metadata["agents"][0]["path"],
        "codex_ready": True,
    }
    existing[team_id] = record
    manifest["teams"] = list(existing.values())
    _save_manifest(manifest)
    return {
        "summary": _summary(list(existing.values())),
        "installed_count": 1,
        "teams": [_public_team_record(record)],
        "local_path": str(team_dir),
    }


def set_lab_report_agent_team_mounted(team_id: str, mounted: bool) -> dict[str, Any]:
    clean_id = str(team_id or "").strip()
    manifest = _load_manifest()
    records = _teams_by_id(manifest)
    record = records.get(clean_id)
    if not record:
        raise FileNotFoundError(f"Report agent team not found: {clean_id}")
    record["mounted"] = bool(mounted)
    record["updated_at"] = _now_iso()
    manifest["teams"] = list(records.values())
    _save_manifest(manifest)
    return {"summary": _summary(list(records.values())), "team": _public_team_record(record)}


def delete_lab_report_agent_team(team_id: str) -> dict[str, Any]:
    clean_id = str(team_id or "").strip()
    manifest = _load_manifest()
    records = _teams_by_id(manifest)
    record = records.pop(clean_id, None)
    if not record:
        raise FileNotFoundError(f"Report agent team not found: {clean_id}")
    manifest["teams"] = list(records.values())
    _save_manifest(manifest)
    return {"summary": _summary(list(records.values())), "deleted_team_id": clean_id}


def mounted_lab_report_agent_teams() -> list[dict[str, Any]]:
    manifest = _load_manifest()
    return [_public_team_record(item) for item in _teams_by_id(manifest).values() if item.get("mounted")]


def build_team_runtime_context(team_ids: list[str] | None = None) -> dict[str, Any]:
    manifest = _load_manifest()
    records = _teams_by_id(manifest)
    requested_ids = [str(item or "").strip() for item in team_ids or [] if str(item or "").strip()]
    selected_ids = requested_ids or [str(item.get("id") or "") for item in records.values() if item.get("mounted")]
    teams: list[dict[str, Any]] = []
    for team_id in selected_ids:
        record = records.get(team_id)
        if not record or not record.get("mounted"):
            continue
        public = _public_team_record(record)
        package_path = Path(str(record.get("package_path") or "")).expanduser().resolve()
        agents = []
        for agent in list(record.get("agents") or []):
            agent_path = package_path / str(agent.get("path") or "")
            instructions = _read_text(agent_path) if agent_path.exists() else ""
            agents.append({**agent, "instructions": instructions})
        teams.append({**public, "agents": agents})
    return {
        "contract": TEAM_CONTRACT_VERSION,
        "enabled": bool(teams),
        "count": len(teams),
        "team_ids": [str(item.get("id") or "") for item in teams],
        "requested_team_ids": requested_ids,
        "teams": teams,
    }


def launch_lab_report_agent_team_run(
    *,
    report_id: str,
    dataset_id: str,
    sheet_name: str,
    workspace_path: str,
    user_requirement: str,
    team_ids: list[str] | None = None,
) -> dict[str, Any]:
    context = build_team_runtime_context(team_ids)
    mounted_team_ids = list(context.get("team_ids") or [])
    if not mounted_team_ids:
        raise ValueError("At least one mounted report agent team is required.")
    safe_report_id = _safe_slug(report_id or dataset_id or str(uuid.uuid4()), fallback="lab-agent-team")
    workspace = (
        Path(str(workspace_path or "").strip()).expanduser().resolve()
        if str(workspace_path or "").strip()
        else (REPORTS_DIR / f"smart-report-{safe_report_id}" / "lab_agent_team_workspace").resolve()
    )
    workspace.mkdir(parents=True, exist_ok=True)
    codex_dir = workspace / ".codex"
    agents_dir = codex_dir / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    team_manifest = {
        "contract": TEAM_CONTRACT_VERSION,
        "report_id": report_id,
        "dataset_id": dataset_id,
        "sheet_name": sheet_name,
        "team_ids": mounted_team_ids,
        "generated_at": _now_iso(),
    }
    (codex_dir / "lab-report-agent-team.json").write_text(json.dumps(team_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    agents_md_lines = [
        "# Lab Report Agent Team",
        "",
        "Use the team manifests in `.codex/agents/*.md` when planning and executing this report-writing run.",
        "Preserve evidence fidelity, coordinate across agents, and summarize which agent handled which section.",
        "",
    ]
    for team in list(context.get("teams") or []):
        team_slug = _safe_slug(str(team.get("id") or "team"))
        for agent in list(team.get("agents") or []):
            file_slug = _safe_slug(str(agent.get("id") or agent.get("name") or "agent"))
            agent_file = agents_dir / f"{team_slug}--{file_slug}.md"
            agent_file.write_text(str(agent.get("instructions") or ""), encoding="utf-8")
            agents_md_lines.append(f"- `{agent_file.name}`: {agent.get('name') or agent.get('id')}")
    (workspace / "AGENTS.md").write_text("\n".join(agents_md_lines).strip() + "\n", encoding="utf-8")
    prompt_lines = [
        "You are coordinating a Lab report-writing agent team.",
        f"Report ID: {report_id}",
        f"Dataset ID: {dataset_id}",
        f"Sheet Name: {sheet_name}",
        "",
        "Use the agent definitions under `.codex/agents/` and the top-level `AGENTS.md` to assign responsibilities.",
        "You may create/update report artifacts in this workspace and must mention which agent handled each major output.",
        "",
        "User requirement:",
        user_requirement.strip() or "Generate and refine the report package for this Lab run.",
    ]
    run_request = CodexRunRequest(
        workspace_path=str(workspace),
        prompt="\n".join(prompt_lines).strip(),
        user_requirement=user_requirement.strip() or "Generate and refine the report package for this Lab run.",
        context_payload={
            "report_id": report_id,
            "dataset_id": dataset_id,
            "sheet_name": sheet_name,
            "agent_team_context": context,
        },
        report_id=report_id,
        parent_report_id=report_id,
        dataset_id=dataset_id,
        sheet_name=sheet_name,
        stage_id="lab_report_agent_team",
        purpose="lab_report_agent_team",
        artifact_source="lab_report_agent_team_manifest.json",
    )
    task = create_codex_run_task(run_request)
    return {
        "team_context": context,
        "mounted_team_ids": mounted_team_ids,
        "workspace_path": str(workspace),
        "task": task,
    }
