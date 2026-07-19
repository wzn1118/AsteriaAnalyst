from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time
from typing import Any, Callable
import uuid

from fastapi import HTTPException

from app.models import CodexRunRequest, CodexRunResponse, RuntimeStageSpec
from app.services.codex_cli_resolver_service import resolve_codex_cli_command
from app.services.codex_runtime_learning_ledger_service import capture_runtime_run_learning_ledger
from app.services.codex_runtime_store import (
    append_stderr_text,
    append_stdout_line,
    read_run_manifest,
    read_stdout_log,
    run_manifest_path,
    transcript_path as transcript_artifact_path,
    summary_path as summary_artifact_path,
    stdout_log_path,
    stderr_log_path,
    git_diff_path as git_diff_artifact_path,
    write_changed_files,
    write_git_diff,
    write_git_status_after,
    write_git_status_before,
    write_run_manifest,
    write_summary,
    write_transcript,
)
from app.services.path_service import PROJECT_ROOT, PUBLIC_ARTIFACTS_DIR
from app.services.settings_service import load_runtime_settings_raw


StageListener = Callable[[dict[str, Any]], None]

_PROCESS_LOCK = threading.Lock()
_RUNNING_PROCS: dict[str, subprocess.Popen[str]] = {}
_CANCEL_REQUESTS: set[str] = set()


def _now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _storage_url_for(path: Path) -> str:
    try:
        relative = path.resolve().relative_to(PUBLIC_ARTIFACTS_DIR).as_posix()
    except Exception:
        return ""
    return f"/storage/{relative}"


def _safe_json_loads(text: str) -> Any:
    try:
        return json.loads(text)
    except Exception:
        return None


def _as_record(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return value
    return None


def _as_string(value: Any, fallback: str = "") -> str:
    return value if isinstance(value, str) else fallback


def _as_number(value: Any, fallback: int = 0) -> int:
    if isinstance(value, bool):
        return fallback
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return fallback


def _error_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    record = _as_record(value)
    if not record:
        return ""
    for key in ("message", "error", "code"):
        text = record.get(key)
        if isinstance(text, str) and text.strip():
            return text.strip()
    try:
        return json.dumps(record, ensure_ascii=False)
    except Exception:
        return str(record)


def _stringify_unknown(value: Any) -> str:
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    try:
        return json.dumps(value, ensure_ascii=False, indent=2)
    except Exception:
        return str(value)


def _first_non_empty_line(text: str) -> str:
    fatal_markers = (
        "unexpected status",
        "service unavailable",
        "timed out",
        "rate limit",
        "turn.failed",
        "error:",
        "failed:",
    )
    fallback = ""
    for line in text.splitlines():
        candidate = line.strip()
        if not candidate:
            continue
        lowered = candidate.lower()
        if (
            lowered in {"<head>", "</head>", "<body>", "</body>", "</html>", "<html>"}
            or lowered.startswith("<meta ")
            or lowered.startswith("<script")
            or lowered.startswith("<style")
            or lowered.startswith("<svg")
            or lowered.startswith("<path")
            or lowered.startswith("<div")
            or lowered.startswith("<span")
            or lowered.startswith("width=")
            or lowered.startswith("height=")
            or lowered.startswith("viewbox=")
            or lowered.startswith("xmlns=")
            or lowered.startswith("stroke")
            or lowered.startswith("class=")
            or lowered.startswith("fill=")
            or lowered.startswith("d=")
            or "cloudflare" in lowered
            or "enable javascript and cookies" in lowered
            or "challenge-platform" in lowered
            or "__cf_chl" in lowered
        ):
            continue
        if any(marker in lowered for marker in fatal_markers):
            return candidate
        if not fallback and not (
            " warn " in lowered
            or "startup remote plugin sync failed" in lowered
            or "failed to remove legacy logs db file" in lowered
            or "failed to open state db" in lowered
            or "failed to load plugin" in lowered
            or "failed to warm featured plugin ids cache" in lowered
            or "shell snapshot not supported" in lowered
        ):
            fallback = candidate
    return fallback


class _SafeFormatDict(dict[str, Any]):
    def __missing__(self, key: str) -> str:
        return ""


def _prompt_source_kind(request: CodexRunRequest) -> str:
    if str(request.prompt).strip():
        return "prompt"
    if str(request.prompt_template).strip():
        return "prompt_template"
    return "default_template"


def _request_field(request: CodexRunRequest | dict[str, Any] | None, field: str) -> Any:
    if isinstance(request, CodexRunRequest):
        return getattr(request, field, None)
    if isinstance(request, dict):
        return request.get(field)
    return None


def _first_non_empty_text(*values: Any) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def _derive_runtime_state(payload: dict[str, Any]) -> str:
    explicit = str(payload.get("runtime_state") or "").strip().lower()
    if explicit:
        return explicit
    if bool(payload.get("cache_hit")):
        return "cached"
    if payload.get("live_available") is False:
        return "local"
    status = str(payload.get("status") or "").strip().lower()
    if status in {"queued", "preparing", "running", "cancelling", "completed", "failed", "cancelled", "timed_out"}:
        return "live"
    return "live"


def _derive_degradation_state(payload: dict[str, Any], runtime_state: str) -> str:
    explicit = str(payload.get("degradation_state") or "").strip()
    if explicit:
        return explicit
    status = str(payload.get("status") or "").strip().lower()
    if status == "failed":
        return "runtime_failed"
    if status == "timed_out":
        return "timed_out"
    if status == "cancelled":
        return "cancelled"
    if runtime_state == "fallback":
        return "hard_fallback"
    if runtime_state == "local":
        return "soft_local"
    return "none"


def _derive_artifact_source(payload: dict[str, Any], default_artifact_source: str) -> str:
    explicit = str(payload.get("artifact_source") or "").strip()
    if explicit:
        return explicit
    if any(str(payload.get(key) or "").strip() for key in ("transcript_path", "summary_path", "git_diff_path")):
        return "codex_runtime_manifest"
    if str(payload.get("job_id") or "").strip():
        return "codex_runtime_task"
    if str(payload.get("run_id") or "").strip():
        return "codex_runtime_run"
    return default_artifact_source or "codex_runtime"


def normalize_runtime_telemetry_contract(
    payload: dict[str, Any],
    *,
    request: CodexRunRequest | dict[str, Any] | None = None,
    default_artifact_source: str = "",
    parent_report_job_id: str = "",
    parent_report_id: str = "",
    parent_stage_id: str = "",
    child_index: int | None = None,
    stage_id: str = "",
    purpose: str = "",
) -> dict[str, Any]:
    normalized = dict(payload)
    normalized_parent_report_job_id = _first_non_empty_text(
        normalized.get("parent_report_job_id"),
        normalized.get("runtime_parent_report_job_id"),
        parent_report_job_id,
    )
    normalized_parent_report_id = _first_non_empty_text(
        normalized.get("parent_report_id"),
        normalized.get("runtime_parent_report_id"),
        parent_report_id,
        _request_field(request, "parent_report_id"),
        _request_field(request, "report_id"),
    )
    normalized_parent_stage_id = _first_non_empty_text(
        normalized.get("parent_stage_id"),
        normalized.get("runtime_parent_stage_id"),
        parent_stage_id,
        _request_field(request, "parent_stage_id"),
        stage_id,
        _request_field(request, "stage_id"),
    )
    normalized_stage_id = _first_non_empty_text(
        normalized.get("stage_id"),
        normalized.get("runtime_stage_id"),
        stage_id,
        _request_field(request, "stage_id"),
    )
    normalized_purpose = _first_non_empty_text(
        normalized.get("purpose"),
        normalized.get("runtime_purpose"),
        purpose,
        _request_field(request, "purpose"),
    )
    normalized_child_index = (
        _as_number(normalized.get("child_index"), fallback=-1)
        if normalized.get("child_index") is not None
        else -1
    )
    if normalized_child_index < 0 and normalized.get("runtime_child_index") is not None:
        normalized_child_index = _as_number(normalized.get("runtime_child_index"), fallback=-1)
    if normalized_child_index < 0 and child_index is not None:
        normalized_child_index = int(child_index)
    if normalized_child_index < 0:
        request_child_index = _request_field(request, "child_index")
        if request_child_index is not None:
            normalized_child_index = _as_number(request_child_index, fallback=0)
    if normalized_child_index < 0:
        normalized_child_index = 0
    runtime_state = _derive_runtime_state(normalized)
    normalized.update(
        {
            "author_mode": _first_non_empty_text(normalized.get("author_mode"), "codex_cli_runtime"),
            "runtime_state": runtime_state,
            "degradation_state": _derive_degradation_state(normalized, runtime_state),
            "artifact_source": _first_non_empty_text(
                normalized.get("artifact_source"),
                normalized.get("runtime_artifact_source"),
                _request_field(request, "artifact_source"),
                _derive_artifact_source(normalized, default_artifact_source),
            ),
            "parent_report_job_id": normalized_parent_report_job_id,
            "parent_report_id": normalized_parent_report_id,
            "parent_stage_id": normalized_parent_stage_id,
            "child_index": normalized_child_index,
            "stage_id": normalized_stage_id,
            "purpose": normalized_purpose,
        }
    )
    return normalized


def load_runtime_json_artifact(
    workspace_path: str | Path,
    artifact_name: str,
    *,
    required_keys: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    artifact_path = Path(workspace_path).expanduser().resolve() / artifact_name
    if not artifact_path.exists():
        raise FileNotFoundError(str(artifact_path))
    try:
        payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"Invalid runtime JSON artifact: {artifact_path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Runtime JSON artifact must be an object: {artifact_path}")
    if required_keys:
        missing = [key for key in required_keys if key not in payload]
        if missing:
            raise ValueError(f"Runtime JSON artifact missing keys {missing}: {artifact_path}")
    return payload


def build_runtime_stage_request(
    spec: RuntimeStageSpec,
    *,
    stage_context: dict[str, Any],
    report_id: str,
    report_job_id: str = "",
    dataset_id: str,
    sheet_name: str,
    user_requirement: str,
) -> CodexRunRequest:
    prompt_template = str(spec.prompt_builder(stage_context) or "")
    workspace_path = str(spec.workspace_path_builder(stage_context) or "").strip()
    context_payload = (
        dict(spec.context_payload_builder(stage_context) or {})
        if spec.context_payload_builder
        else dict(stage_context.get("context_payload") or {})
    )
    return CodexRunRequest(
        workspace_path=workspace_path,
        prompt_template=prompt_template,
        user_requirement=user_requirement,
        context_payload=context_payload,
        report_id=report_id,
        parent_report_id=report_id,
        parent_report_job_id=report_job_id,
        parent_stage_id=str(spec.stage_id or ""),
        child_index=int(stage_context.get("child_index") or 0),
        dataset_id=dataset_id,
        sheet_name=sheet_name,
        stage_id=spec.stage_id,
        purpose=str(spec.purpose or spec.stage_id or "generic"),
        artifact_source=(spec.expected_artifact_files[0] if spec.expected_artifact_files else ""),
        timeout_sec=int(spec.timeout_sec or 180),
        capture_git_diff=bool(spec.capture_git_diff),
    )


def _render_prompt(request: CodexRunRequest) -> str:
    if str(request.prompt).strip():
        return str(request.prompt)
    context_json = json.dumps(request.context_payload or {}, ensure_ascii=False, indent=2)
    if str(request.prompt_template).strip():
        return str(request.prompt_template).format_map(
            _SafeFormatDict(
                {
                    "workspace_path": request.workspace_path,
                    "user_requirement": request.user_requirement,
                    "context_json": context_json,
                    "report_id": request.report_id,
                    "dataset_id": request.dataset_id,
                    "sheet_name": request.sheet_name,
                    "stage_id": request.stage_id,
                    "purpose": request.purpose,
                }
            )
        )
    return (
        "You are the headless Codex backend executor.\n\n"
        f"Workspace: {request.workspace_path}\n"
        f"Purpose: {request.purpose or 'generic'}\n"
        f"Report ID: {request.report_id}\n"
        f"Dataset ID: {request.dataset_id}\n"
        f"Sheet Name: {request.sheet_name}\n"
        f"Stage ID: {request.stage_id}\n\n"
        "Task:\n"
        f"{request.user_requirement}\n\n"
        "Context JSON:\n"
        f"{context_json}\n\n"
        "At the end, summarize what you changed, what commands ran, which files matter, and any validation gaps.\n"
    )


def _resolve_codex_command(settings: dict[str, Any]) -> str:
    return resolve_codex_cli_command(settings)


def _workspace_allowed(workspace_path: Path, settings: dict[str, Any]) -> bool:
    configured_root = str(settings.get("codex_workspace_root") or "").strip()
    if not configured_root:
        return False
    root_path = Path(configured_root).expanduser().resolve()
    try:
        return workspace_path.is_relative_to(root_path)
    except AttributeError:
        workspace_lower = str(workspace_path).lower()
        root_lower = str(root_path).lower()
        return workspace_lower == root_lower or workspace_lower.startswith(root_lower + os.sep.lower())


def _unsandboxed_runtime_authorized() -> bool:
    return str(os.getenv("ASTERIA_ALLOW_UNSANDBOXED_CODEX_RUNTIME", "")).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _build_codex_args(
    *,
    command: str,
    settings: dict[str, Any],
    workspace_path: Path,
    model: str,
    search: bool,
    resume_session_id: str,
    dangerously_bypass_approvals_and_sandbox: bool,
) -> list[str]:
    args = [command]
    args.extend(_codex_config_overrides(settings))
    if search:
        args.append("--search")
    if model:
        args.extend(["--model", model])
    if dangerously_bypass_approvals_and_sandbox:
        args.append("--dangerously-bypass-approvals-and-sandbox")
    else:
        args.extend(["--ask-for-approval", "never", "--sandbox", "workspace-write"])
    args.extend(["-C", str(workspace_path)])
    args.extend(["exec", "--json", "--skip-git-repo-check"])
    if resume_session_id:
        args.extend(["resume", resume_session_id, "-"])
    else:
        args.append("-")
    return args


def _preferred_runtime_python_executable() -> str:
    configured = os.getenv("ASTERIA_RUNTIME_PYTHON") or os.getenv("PYTHON")
    if configured:
        candidate = Path(configured).expanduser().resolve()
        if candidate.exists() and candidate.is_file():
            return str(candidate)
    candidates = [
        Path(sys.executable).resolve(),
        (PROJECT_ROOT / ".venv" / "Scripts" / "python.exe").resolve(),
    ]
    launcher = shutil.which("py") or shutil.which("py.exe")
    if launcher:
        candidates.append(Path(launcher).resolve())
    for candidate in candidates:
        try:
            if candidate.exists() and candidate.is_file():
                return str(candidate)
        except Exception:
            continue
    return str(Path(sys.executable).resolve())


def _prepare_codex_subprocess_env(settings: dict[str, Any]) -> dict[str, str]:
    env = os.environ.copy()
    api_key = str(settings.get("api_key") or "").strip()
    base_url = str(settings.get("base_url") or "").strip()
    if api_key:
        env["OPENAI_API_KEY"] = api_key
    if base_url:
        env["OPENAI_BASE_URL"] = base_url

    python_executable = _preferred_runtime_python_executable()
    python_dir = str(Path(python_executable).resolve().parent)
    existing_path = str(env.get("PATH") or "")
    preferred_dirs = [
        python_dir,
        str((PROJECT_ROOT / ".venv" / "Scripts").resolve()),
        str((PROJECT_ROOT / ".venv").resolve()),
    ]
    ordered_dirs: list[str] = []
    seen: set[str] = set()
    for raw_dir in preferred_dirs + existing_path.split(os.pathsep):
        directory = str(raw_dir or "").strip()
        if not directory:
            continue
        marker = directory.lower()
        if marker in seen:
            continue
        seen.add(marker)
        ordered_dirs.append(directory)
    env["PATH"] = os.pathsep.join(ordered_dirs)
    env["PYTHON"] = python_executable
    env["UV_PYTHON"] = python_executable
    env["PY_PYTHON"] = "3"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def _normalize_codex_provider_base_url(base_url: str) -> str:
    normalized = str(base_url or "").strip().rstrip("/")
    if not normalized:
        return "https://api.openai.com/v1"
    if normalized.endswith("/v1"):
        return normalized
    return f"{normalized}/v1"


def _codex_config_overrides(settings: dict[str, Any]) -> list[str]:
    reasoning_effort = str(settings.get("reasoning_effort") or "").strip()
    reasoning_overrides: list[str] = []
    if reasoning_effort in {"minimal", "low", "medium", "high", "xhigh"}:
        reasoning_overrides.extend(["-c", f'model_reasoning_effort="{reasoning_effort}"'])
    if bool(settings.get("codex_use_login_auth", True)):
        return reasoning_overrides
    base_url = _normalize_codex_provider_base_url(str(settings.get("base_url") or ""))
    return [
        *reasoning_overrides,
        "-c",
        'model_provider="OpenAI"',
        "-c",
        'model_providers.OpenAI.name="OpenAI"',
        "-c",
        f'model_providers.OpenAI.base_url="{base_url}"',
        "-c",
        'model_providers.OpenAI.wire_api="responses"',
        "-c",
        'model_providers.OpenAI.requires_openai_auth=false',
        "-c",
        'model_providers.OpenAI.env_key="OPENAI_API_KEY"',
    ]


def _run_git(cwd: Path, args: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _git_available() -> bool:
    return shutil.which("git") is not None


def _git_snapshot(cwd: Path) -> dict[str, str]:
    if not _git_available():
        return {"head": "", "status": ""}
    code, stdout, _stderr = _run_git(cwd, ["rev-parse", "--is-inside-work-tree"])
    if code != 0 or stdout.strip().lower() != "true":
        return {"head": "", "status": ""}
    head_code, head_stdout, _ = _run_git(cwd, ["rev-parse", "HEAD"])
    status_code, status_stdout, _ = _run_git(cwd, ["status", "--porcelain"])
    return {
        "head": head_stdout.strip() if head_code == 0 else "",
        "status": status_stdout if status_code == 0 else "",
    }


def _git_diff(cwd: Path) -> tuple[str, list[str]]:
    if not _git_available():
        return "", []
    code, stdout, _stderr = _run_git(cwd, ["rev-parse", "--is-inside-work-tree"])
    if code != 0 or stdout.strip().lower() != "true":
        return "", []
    _diff_code, diff_stdout, _ = _run_git(cwd, ["diff", "--no-ext-diff"])
    status_code, status_stdout, _ = _run_git(cwd, ["status", "--porcelain"])
    changed_files: list[str] = []
    if status_code == 0:
        for line in status_stdout.splitlines():
            text = line.strip()
            if not text:
                continue
            path_part = line[3:] if len(line) > 3 else line
            if " -> " in path_part:
                path_part = path_part.split(" -> ", 1)[1]
            changed_files.append(path_part.strip())
    return diff_stdout, changed_files


def _entry(
    kind: str,
    *,
    ts: str,
    text: str = "",
    name: str = "",
    is_error: bool = False,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "kind": kind,
        "ts": ts,
        "text": text,
        "name": name,
        "is_error": is_error,
        "payload": payload or {},
    }


def _parse_command_execution_item(item: dict[str, Any], ts: str, phase: str) -> list[dict[str, Any]]:
    item_id = _as_string(item.get("id"))
    command = _as_string(item.get("command"))
    status = _as_string(item.get("status"))
    exit_code = item.get("exit_code")
    output = _as_string(item.get("aggregated_output")).rstrip()
    if phase == "started":
        return [_entry("tool_call", ts=ts, name="command_execution", payload={"id": item_id, "command": command})]

    lines: list[str] = []
    if command:
        lines.append(f"command: {command}")
    if status:
        lines.append(f"status: {status}")
    if isinstance(exit_code, int):
        lines.append(f"exit_code: {exit_code}")
    if output:
        if lines:
            lines.append("")
        lines.append(output)

    is_error = (
        (isinstance(exit_code, int) and exit_code != 0)
        or status in {"failed", "errored", "error", "cancelled"}
    )
    return [
        _entry(
            "tool_result",
            ts=ts,
            text="\n".join(lines).strip() or "command completed",
            is_error=is_error,
            payload={"tool_use_id": item_id or command or "command_execution"},
        )
    ]


def _parse_file_change_item(item: dict[str, Any], ts: str) -> list[dict[str, Any]]:
    changes = item.get("changes")
    if not isinstance(changes, list):
        return [_entry("system", ts=ts, text="file changes applied")]
    entries: list[str] = []
    for raw_change in changes:
        change = _as_record(raw_change)
        if not change:
            continue
        kind = _as_string(change.get("kind"), "update")
        path = _as_string(change.get("path"), "unknown")
        entries.append(f"{kind} {path}")
    preview = ", ".join(entries[:6])
    more = f" (+{len(entries) - 6} more)" if len(entries) > 6 else ""
    return [_entry("system", ts=ts, text=f"file changes: {preview}{more}" if preview else "file changes applied", payload={"changes": entries})]


def _parse_codex_item(item: dict[str, Any], ts: str, phase: str) -> list[dict[str, Any]]:
    item_type = _as_string(item.get("type"))
    if item_type == "agent_message":
        text = _as_string(item.get("text"))
        return [_entry("assistant", ts=ts, text=text)] if text else []
    if item_type == "reasoning":
        text = _as_string(item.get("text"))
        if text:
            return [_entry("thinking", ts=ts, text=text)]
        return [_entry("system", ts=ts, text="reasoning started" if phase == "started" else "reasoning completed")]
    if item_type == "command_execution":
        return _parse_command_execution_item(item, ts, phase)
    if item_type == "file_change" and phase == "completed":
        return _parse_file_change_item(item, ts)
    if item_type == "tool_use":
        return [_entry("tool_call", ts=ts, name=_as_string(item.get("name"), "unknown"), payload=_as_record(item.get("input")) or {})]
    if item_type == "tool_result" and phase == "completed":
        content = (
            _as_string(item.get("content"))
            or _as_string(item.get("output"))
            or _as_string(item.get("result"))
            or _stringify_unknown(item.get("content") or item.get("output") or item.get("result"))
        )
        return [
            _entry(
                "tool_result",
                ts=ts,
                text=content,
                is_error=item.get("is_error") is True or _as_string(item.get("status")) == "error",
                payload={"tool_use_id": _as_string(item.get("tool_use_id"), _as_string(item.get("id")))},
            )
        ]
    if item_type == "error" and phase == "completed":
        return [_entry("stderr", ts=ts, text=_error_text(item.get("message") or item.get("error") or item) or "error", is_error=True)]

    item_id = _as_string(item.get("id"))
    status = _as_string(item.get("status"))
    meta_parts = [f"id={item_id}" if item_id else "", f"status={status}" if status else ""]
    meta = " ".join(part for part in meta_parts if part)
    text = f"item {phase}: {item_type or 'unknown'}"
    if meta:
        text = f"{text} ({meta})"
    return [_entry("system", ts=ts, text=text)]


def _parse_codex_stdout(stdout_text: str) -> tuple[list[dict[str, Any]], str, str]:
    transcript: list[dict[str, Any]] = []
    session_id = ""
    assistant_messages: list[str] = []
    result_texts: list[str] = []

    for raw_line in stdout_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parsed = _as_record(_safe_json_loads(line))
        ts = _now_iso()
        if not parsed:
            transcript.append(_entry("stdout", ts=ts, text=line))
            continue

        event_type = _as_string(parsed.get("type"))
        if event_type == "thread.started":
            session_id = _as_string(parsed.get("thread_id")) or session_id
            transcript.append(_entry("system", ts=ts, text="thread started", payload={"session_id": session_id, "model": _as_string(parsed.get("model"))}))
            continue
        if event_type == "turn.started":
            transcript.append(_entry("system", ts=ts, text="turn started"))
            continue
        if event_type in {"item.started", "item.completed"}:
            item = _as_record(parsed.get("item"))
            if not item:
                transcript.append(_entry("system", ts=ts, text=event_type.replace(".", " ")))
                continue
            entries = _parse_codex_item(item, ts, "started" if event_type == "item.started" else "completed")
            transcript.extend(entries)
            for entry in entries:
                if entry["kind"] == "assistant" and entry["text"]:
                    assistant_messages.append(str(entry["text"]))
            continue
        if event_type == "turn.completed":
            text = _as_string(parsed.get("result"))
            transcript.append(
                _entry(
                    "result",
                    ts=ts,
                    text=text,
                    is_error=parsed.get("is_error") is True,
                    payload={
                        "subtype": _as_string(parsed.get("subtype")),
                        "input_tokens": _as_number((_as_record(parsed.get("usage")) or {}).get("input_tokens")),
                        "output_tokens": _as_number((_as_record(parsed.get("usage")) or {}).get("output_tokens")),
                        "cached_input_tokens": _as_number(
                            (_as_record(parsed.get("usage")) or {}).get("cached_input_tokens"),
                            _as_number((_as_record(parsed.get("usage")) or {}).get("cache_read_input_tokens")),
                        ),
                        "cost_usd": parsed.get("total_cost_usd"),
                    },
                )
            )
            if text:
                result_texts.append(text)
            continue
        if event_type == "turn.failed":
            text = _as_string(parsed.get("result"))
            error_text = _error_text(parsed.get("error") or parsed.get("message"))
            transcript.append(_entry("result", ts=ts, text=text, is_error=True, payload={"subtype": _as_string(parsed.get("subtype"), "turn.failed"), "errors": [error_text] if error_text else []}))
            if error_text:
                result_texts.append(error_text)
            continue
        if event_type == "error":
            error_text = _error_text(parsed.get("message") or parsed.get("error") or parsed)
            transcript.append(_entry("stderr", ts=ts, text=error_text or line, is_error=True))
            if error_text:
                result_texts.append(error_text)
            continue

        transcript.append(_entry("stdout", ts=ts, text=line))

    summary = "\n\n".join(message for message in assistant_messages if message).strip()
    if not summary:
        summary = "\n\n".join(text for text in result_texts if text).strip()
    return transcript, session_id, summary


def _first_transcript_error_text(transcript: list[dict[str, Any]]) -> str:
    for entry in reversed(transcript):
        if not isinstance(entry, dict):
            continue
        payload = entry.get("payload")
        if isinstance(payload, dict):
            for value in reversed(list(payload.get("errors") or [])):
                error_text = str(value or "").strip()
                if error_text:
                    return error_text
        text = str(entry.get("text") or "").strip()
        if bool(entry.get("is_error")) and text:
            return text
    return ""


def _is_model_capacity_error(text: str) -> bool:
    lowered = str(text or "").strip().lower()
    if not lowered:
        return False
    return "selected model is at capacity" in lowered or ("model" in lowered and "capacity" in lowered)


def _next_capacity_retry_model(current_model: str) -> str:
    normalized = str(current_model or "").strip()
    ordered = ["gpt-5.5", "gpt-5.4", "gpt-5.4-mini", "gpt-5.2"]
    if normalized in ordered:
        index = ordered.index(normalized)
        for candidate in ordered[index + 1 :]:
            if candidate != normalized:
                return candidate
        return ""
    return "gpt-5.4" if normalized != "gpt-5.4" else "gpt-5.4-mini"


def _emit_stage(
    listener: StageListener | None,
    stage_id: str,
    title: str,
    detail: str,
    *,
    status: str = "running",
    payload: dict[str, Any] | None = None,
) -> None:
    if not listener:
        return
    try:
        listener(
            {
                "stage_id": stage_id,
                "title": title,
                "detail": detail,
                "timestamp": _now_iso(),
                "payload": {"status": status, **(payload or {})},
            }
        )
    except Exception:
        pass


def _terminate_process(proc: subprocess.Popen[str]) -> None:
    try:
        proc.terminate()
        proc.wait(timeout=5)
        return
    except Exception:
        pass
    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
            proc.wait(timeout=5)
            return
        except Exception:
            pass
    try:
        proc.kill()
        proc.wait(timeout=5)
    except Exception:
        pass


def _base_manifest(
    *,
    run_id: str,
    request: CodexRunRequest,
    status: str,
    created_at: str,
) -> dict[str, Any]:
    stdout_path = stdout_log_path(run_id)
    stderr_path = stderr_log_path(run_id)
    transcript_path = transcript_artifact_path(run_id)
    summary_file_path = summary_artifact_path(run_id)
    git_diff_path = git_diff_artifact_path(run_id)
    return normalize_runtime_telemetry_contract(
        {
        "run_id": run_id,
        "status": status,
        "workspace_path": str(Path(request.workspace_path).expanduser().resolve()),
        "session_id": "",
        "summary": "",
        "changed_files": [],
        "git_diff_path": str(git_diff_path.resolve()),
        "git_diff_url": _storage_url_for(git_diff_path),
        "transcript_path": str(transcript_path.resolve()),
        "transcript_url": _storage_url_for(transcript_path),
        "stdout_path": str(stdout_path.resolve()),
        "stdout_url": _storage_url_for(stdout_path),
        "stderr_path": str(stderr_path.resolve()),
        "stderr_url": _storage_url_for(stderr_path),
        "summary_path": str(summary_file_path.resolve()),
        "summary_url": _storage_url_for(summary_file_path),
        "created_at": created_at,
        "updated_at": created_at,
        "error": "",
        "transcript_entry_count": 0,
        "request": request.model_dump(),
        },
        request=request,
        default_artifact_source="codex_runtime_manifest",
    )


def _update_manifest(run_id: str, **updates: Any) -> dict[str, Any]:
    manifest = read_run_manifest(run_id)
    manifest.update(updates)
    manifest["updated_at"] = _now_iso()
    write_run_manifest(run_id, manifest)
    return manifest


def run_headless_codex(
    request: CodexRunRequest,
    *,
    stage_listener: StageListener | None = None,
) -> dict[str, Any]:
    settings = load_runtime_settings_raw()
    if not bool(settings.get("codex_runtime_enabled", False)):
        raise HTTPException(status_code=400, detail="Codex runtime is disabled in runtime settings.")
    configured_root = str(settings.get("codex_workspace_root") or "").strip()
    if not configured_root:
        raise HTTPException(
            status_code=400,
            detail=(
                "Codex runtime requires a constrained workspace root. "
                "Set ASTERIA_CODEX_WORKSPACE_ROOT or configure codex_workspace_root before executing runtime runs."
            ),
        )

    workspace_path = Path(request.workspace_path).expanduser().resolve()
    if not workspace_path.exists() or not workspace_path.is_dir():
        raise HTTPException(status_code=400, detail=f"Workspace path is not a directory: {workspace_path}")
    if not _workspace_allowed(workspace_path, settings):
        raise HTTPException(status_code=403, detail=f"Workspace path is outside the allowed Codex runtime root: {workspace_path}")

    command = _resolve_codex_command(settings)
    if not bool(settings.get("codex_use_login_auth", True)) and not str(settings.get("api_key") or "").strip():
        raise HTTPException(status_code=400, detail="Codex runtime requires an API key when login auth is disabled.")

    run_id = uuid.uuid4().hex[:12]
    created_at = _now_iso()
    prompt = _render_prompt(request)
    model = str(request.model or "").strip() or str(settings.get("model") or "gpt-5.4")
    search = bool(request.search or settings.get("codex_search_enabled", False))
    timeout_sec = int(request.timeout_sec or settings.get("codex_timeout_sec") or 1800)
    timeout_sec = max(0, timeout_sec)
    bypass_requested = bool(
        request.dangerously_bypass_approvals_and_sandbox
        or settings.get("codex_dangerously_bypass_approvals_and_sandbox", False)
    )
    if bypass_requested and not _unsandboxed_runtime_authorized():
        raise HTTPException(
            status_code=403,
            detail=(
                "Unsandboxed Codex runtime is disabled. "
                "Set ASTERIA_ALLOW_UNSANDBOXED_CODEX_RUNTIME=1 to authorize it."
            ),
        )
    bypass = bypass_requested
    resume_session_id = str(request.resume_session_id or "").strip()

    initial_manifest = _base_manifest(run_id=run_id, request=request, status="preparing", created_at=created_at)
    initial_manifest["command"] = _build_codex_args(
        command=command,
        settings=settings,
        workspace_path=workspace_path,
        model=model,
        search=search,
        resume_session_id=resume_session_id,
        dangerously_bypass_approvals_and_sandbox=bypass,
    )
    initial_manifest["model"] = model
    initial_manifest["search"] = search
    initial_manifest["timeout_sec"] = timeout_sec
    initial_manifest["prompt_source"] = _prompt_source_kind(request)
    initial_manifest["prompt"] = prompt
    write_run_manifest(run_id, initial_manifest)

    _emit_stage(stage_listener, "prompt_prepared", "Prompt prepared", "The Codex runtime prompt has been rendered.")
    _emit_stage(stage_listener, "workspace_validated", "Workspace validated", f"Workspace {workspace_path} passed runtime validation.")

    before_git = _git_snapshot(workspace_path) if request.capture_git_diff else {"head": "", "status": ""}
    write_git_status_before(run_id, before_git.get("status", ""))
    _update_manifest(run_id, git_head_before=before_git.get("head", ""), status="running")

    args = _build_codex_args(
        command=command,
        settings=settings,
        workspace_path=workspace_path,
        model=model,
        search=search,
        resume_session_id=resume_session_id,
        dangerously_bypass_approvals_and_sandbox=bypass,
    )

    env = _prepare_codex_subprocess_env(settings)
    if not resume_session_id:
        # Fresh pipeline stages must not inherit a stale Codex Desktop thread from
        # the shared user state DB. The prompt already carries explicit evidence
        # paths, so an isolated CODEX_HOME keeps the model context clean while
        # preserving API-key based execution.
        isolated_codex_home = run_manifest_path(run_id).parent / "codex_home"
        isolated_codex_home.mkdir(parents=True, exist_ok=True)
        env["CODEX_HOME"] = str(isolated_codex_home.resolve())
        _update_manifest(run_id, isolated_codex_home=str(isolated_codex_home.resolve()))

    try:
        proc = subprocess.Popen(
            args,
            cwd=str(workspace_path),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            env=env,
        )
    except OSError as exc:
        _update_manifest(run_id, status="failed", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Failed to start Codex CLI: {exc}") from exc

    with _PROCESS_LOCK:
        _RUNNING_PROCS[run_id] = proc
    _emit_stage(stage_listener, "session_started", "Codex session started", f"Codex CLI process started for run {run_id}.")

    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []
    stream_state = {
        "last_stdout_monotonic": time.monotonic(),
        "saw_turn_completed": False,
        "saw_turn_failed": False,
        "fatal_stdout_error": "",
    }

    def _stdout_reader() -> None:
        if proc.stdout is None:
            return
        for line in iter(proc.stdout.readline, ""):
            stdout_chunks.append(line)
            stream_state["last_stdout_monotonic"] = time.monotonic()
            parsed = _as_record(_safe_json_loads(line.strip()))
            event_type = _as_string(parsed.get("type")) if parsed else ""
            message_text = _as_string(parsed.get("message")) if parsed else ""
            if event_type == "turn.completed":
                stream_state["saw_turn_completed"] = True
            elif event_type == "turn.failed":
                stream_state["saw_turn_failed"] = True
            elif event_type == "error":
                lowered = message_text.lower()
                if "system memory overloaded" in lowered and "reconnecting... 5/5" in lowered:
                    stream_state["fatal_stdout_error"] = message_text.strip()
            append_stdout_line(run_id, {"ts": _now_iso(), "chunk": line})
        proc.stdout.close()

    def _stderr_reader() -> None:
        if proc.stderr is None:
            return
        for line in iter(proc.stderr.readline, ""):
            stderr_chunks.append(line)
            append_stderr_text(run_id, line)
        proc.stderr.close()

    stdout_thread = threading.Thread(target=_stdout_reader, name=f"codex-stdout-{run_id}", daemon=True)
    stderr_thread = threading.Thread(target=_stderr_reader, name=f"codex-stderr-{run_id}", daemon=True)
    stdout_thread.start()
    stderr_thread.start()

    try:
        if proc.stdin is not None:
            proc.stdin.write(prompt)
            if not prompt.endswith("\n"):
                proc.stdin.write("\n")
            proc.stdin.flush()
            proc.stdin.close()
    except OSError:
        pass

    timed_out = False
    soft_terminal_status = ""
    quiet_completion_grace_sec = 8.0
    deadline = (time.monotonic() + timeout_sec) if timeout_sec > 0 else None
    try:
        while True:
            try:
                proc.wait(timeout=1)
                break
            except subprocess.TimeoutExpired:
                now = time.monotonic()
                last_stdout = float(stream_state.get("last_stdout_monotonic") or now)
                quiet_for = now - last_stdout
                if stream_state["saw_turn_completed"] and quiet_for >= quiet_completion_grace_sec:
                    soft_terminal_status = "completed"
                    _terminate_process(proc)
                    break
                if stream_state["saw_turn_failed"] and quiet_for >= quiet_completion_grace_sec:
                    soft_terminal_status = "failed"
                    _terminate_process(proc)
                    break
                if stream_state["fatal_stdout_error"] and quiet_for >= 5.0:
                    soft_terminal_status = "failed"
                    _terminate_process(proc)
                    break
                if deadline is not None and now >= deadline:
                    timed_out = True
                    with _PROCESS_LOCK:
                        _CANCEL_REQUESTS.discard(run_id)
                    _terminate_process(proc)
                    break
        if deadline is None and proc.poll() is None and stream_state["saw_turn_completed"]:
            soft_terminal_status = "completed"
            _terminate_process(proc)
    except Exception:
        _terminate_process(proc)
        raise

    stdout_thread.join(timeout=5)
    stderr_thread.join(timeout=5)

    with _PROCESS_LOCK:
        _RUNNING_PROCS.pop(run_id, None)
        cancelled = run_id in _CANCEL_REQUESTS
        _CANCEL_REQUESTS.discard(run_id)

    stdout_text = "".join(stdout_chunks)
    stderr_text = "".join(stderr_chunks)
    transcript, parsed_session_id, summary = _parse_codex_stdout(stdout_text)
    transcript_error_text = _first_transcript_error_text(transcript)
    session_id = parsed_session_id or resume_session_id

    after_git = _git_snapshot(workspace_path) if request.capture_git_diff else {"head": "", "status": ""}
    write_git_status_after(run_id, after_git.get("status", ""))
    git_diff_text, changed_files = _git_diff(workspace_path) if request.capture_git_diff else ("", [])
    write_git_diff(run_id, git_diff_text)
    write_changed_files(run_id, changed_files)
    write_transcript(run_id, transcript)

    result_text = summary.strip()
    if not result_text:
        result_text = "No assistant summary was returned."
    changed_file_lines = [f"- `{path}`" for path in changed_files] or ["- none"]
    summary_markdown = "\n".join(
        [
            "# Codex Run Summary",
            "",
            f"- Status: {'cancelled' if cancelled else 'timed_out' if timed_out else 'completed' if proc.returncode == 0 else 'failed'}",
            f"- Workspace: `{workspace_path}`",
            f"- Session: `{session_id or 'none'}`",
            "",
            "## Summary",
            "",
            result_text,
            "",
            "## Changed Files",
            "",
            *changed_file_lines,
        ]
    )
    write_summary(run_id, summary_markdown)

    status = "completed"
    error_message = ""
    if cancelled:
        status = "cancelled"
        error_message = "Cancelled by user."
    elif timed_out:
        status = "timed_out"
        error_message = f"Timed out after {timeout_sec} seconds."
    elif soft_terminal_status == "failed":
        status = "failed"
        error_message = (
            stream_state.get("fatal_stdout_error")
            or transcript_error_text
            or _first_non_empty_line(stderr_text)
            or "Codex CLI emitted a terminal failure event."
        )
    elif soft_terminal_status == "completed":
        status = "completed"
    elif (proc.returncode or 0) != 0:
        status = "failed"
        error_message = transcript_error_text or _first_non_empty_line(stderr_text) or "Codex CLI exited with a non-zero status."

    final_manifest = _update_manifest(
        run_id,
        status=status,
        session_id=session_id,
        summary=result_text,
        changed_files=changed_files,
        transcript_entry_count=len(transcript),
        error=error_message,
        git_head_after=after_git.get("head", ""),
        exit_code=proc.returncode,
    )

    retry_model = ""
    if status == "failed" and _is_model_capacity_error(error_message):
        retry_model = _next_capacity_retry_model(model)
    if retry_model and retry_model != model:
        _emit_stage(
            stage_listener,
            "capacity_retry",
            "Codex model fallback",
            f"Model {model} is at capacity. Retrying with {retry_model}.",
            status="running",
            payload={"run_id": run_id, "failed_model": model, "retry_model": retry_model},
        )
        retry_request = request.model_copy(update={"model": retry_model, "resume_session_id": ""})
        return run_headless_codex(retry_request, stage_listener=stage_listener)

    if status == "completed":
        _emit_stage(stage_listener, "artifact_collection", "Artifacts collected", "Transcript, logs, and git diff have been persisted.", status="completed", payload={"changed_file_count": len(changed_files)})
        _emit_stage(stage_listener, "completed", "Codex run completed", "The headless Codex runtime finished successfully.", status="completed", payload={"run_id": run_id, "session_id": session_id})
    elif status == "cancelled":
        _emit_stage(stage_listener, "cancelled", "Codex run cancelled", error_message, status="failed", payload={"run_id": run_id})
    elif status == "timed_out":
        _emit_stage(stage_listener, "timed_out", "Codex run timed out", error_message, status="failed", payload={"run_id": run_id})
    else:
        _emit_stage(stage_listener, "failed", "Codex run failed", error_message or "Codex CLI execution failed.", status="failed", payload={"run_id": run_id})

    response = CodexRunResponse.model_validate(final_manifest).model_dump()
    normalized_response = normalize_runtime_telemetry_contract(
        response,
        request=request,
        default_artifact_source="codex_runtime_manifest",
    )
    try:
        capture_runtime_run_learning_ledger(final_manifest)
    except Exception:
        pass
    return normalized_response


def get_codex_run(run_id: str) -> dict[str, Any]:
    try:
        manifest = read_run_manifest(run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    response = CodexRunResponse.model_validate(manifest).model_dump()
    return normalize_runtime_telemetry_contract(
        response,
        request=manifest.get("request") if isinstance(manifest.get("request"), dict) else None,
        default_artifact_source="codex_runtime_manifest",
    )


def read_codex_run_log(run_id: str, offset: int = 0, limit_bytes: int = 256000) -> dict[str, Any]:
    try:
        return read_stdout_log(run_id, offset=offset, limit_bytes=limit_bytes)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def cancel_codex_run(run_id: str) -> dict[str, Any]:
    with _PROCESS_LOCK:
        proc = _RUNNING_PROCS.get(run_id)
        if proc is not None:
            _CANCEL_REQUESTS.add(run_id)
            try:
                proc.terminate()
            except Exception:
                pass
            try:
                manifest = _update_manifest(run_id, status="cancelling")
            except FileNotFoundError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc
            return CodexRunResponse.model_validate(manifest).model_dump()

    try:
        manifest = read_run_manifest(run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return CodexRunResponse.model_validate(manifest).model_dump()
