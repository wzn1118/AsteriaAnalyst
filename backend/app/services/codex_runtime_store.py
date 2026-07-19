from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any

from app.services.path_service import CODEX_RUNTIME_RUNS_DIR, CODEX_RUNTIME_TASKS_DIR


def ensure_codex_runtime_dirs() -> None:
    CODEX_RUNTIME_RUNS_DIR.mkdir(parents=True, exist_ok=True)
    CODEX_RUNTIME_TASKS_DIR.mkdir(parents=True, exist_ok=True)


def run_dir(run_id: str) -> Path:
    ensure_codex_runtime_dirs()
    path = CODEX_RUNTIME_RUNS_DIR / str(run_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def task_path(job_id: str) -> Path:
    ensure_codex_runtime_dirs()
    return CODEX_RUNTIME_TASKS_DIR / f"{job_id}.json"


def run_manifest_path(run_id: str) -> Path:
    return run_dir(run_id) / "run.json"


def stdout_log_path(run_id: str) -> Path:
    return run_dir(run_id) / "stdout.jsonl"


def stderr_log_path(run_id: str) -> Path:
    return run_dir(run_id) / "stderr.log"


def transcript_path(run_id: str) -> Path:
    return run_dir(run_id) / "transcript.json"


def summary_path(run_id: str) -> Path:
    return run_dir(run_id) / "summary.md"


def git_status_before_path(run_id: str) -> Path:
    return run_dir(run_id) / "git_status_before.txt"


def git_status_after_path(run_id: str) -> Path:
    return run_dir(run_id) / "git_status_after.txt"


def git_diff_path(run_id: str) -> Path:
    return run_dir(run_id) / "git_diff.patch"


def changed_files_path(run_id: str) -> Path:
    return run_dir(run_id) / "changed_files.json"


def _text_summary(text: Any, *, preview_limit: int = 240) -> dict[str, Any]:
    raw = str(text or "")
    normalized = re.sub(r"\s+", " ", raw).strip()
    preview = normalized[:preview_limit]
    if len(normalized) > preview_limit:
        preview = preview.rstrip() + "..."
    return {
        "hash": hashlib.sha256(raw.encode("utf-8")).hexdigest() if raw else "",
        "preview": preview,
        "length": len(raw),
    }


def _context_summary(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {
            "hash": "",
            "size": 0,
            "top_level_keys": [],
        }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return {
        "hash": hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
        "size": len(serialized.encode("utf-8")),
        "top_level_keys": sorted(str(key) for key in payload.keys())[:20],
    }


def sanitize_runtime_request_payload(payload: dict[str, Any]) -> dict[str, Any]:
    request = dict(payload or {})
    if request.get("request_redacted") is True and "prompt" not in request and "context_payload" not in request:
        return request

    prompt_summary = _text_summary(request.pop("prompt", ""))
    user_requirement_summary = _text_summary(request.pop("user_requirement", ""))
    context_summary = _context_summary(request.pop("context_payload", {}))
    resume_session_id = str(request.pop("resume_session_id", "") or "").strip()

    request["prompt_hash"] = request.get("prompt_hash") or prompt_summary["hash"]
    request["prompt_preview"] = request.get("prompt_preview") or prompt_summary["preview"]
    request["prompt_length"] = int(request.get("prompt_length") or prompt_summary["length"] or 0)
    request["user_requirement_hash"] = request.get("user_requirement_hash") or user_requirement_summary["hash"]
    request["user_requirement_preview"] = request.get("user_requirement_preview") or user_requirement_summary["preview"]
    request["user_requirement_length"] = int(
        request.get("user_requirement_length") or user_requirement_summary["length"] or 0
    )
    request["context_payload_hash"] = request.get("context_payload_hash") or context_summary["hash"]
    request["context_size"] = int(request.get("context_size") or context_summary["size"] or 0)
    request["context_top_level_keys"] = request.get("context_top_level_keys") or context_summary["top_level_keys"]
    request["resume_session_id_present"] = bool(
        request.get("resume_session_id_present") or bool(resume_session_id)
    )
    request["request_redacted"] = True
    return request


def sanitize_runtime_manifest_payload(payload: dict[str, Any]) -> dict[str, Any]:
    manifest = dict(payload or {})
    if "request" in manifest and isinstance(manifest["request"], dict):
        manifest["request"] = sanitize_runtime_request_payload(manifest["request"])

    if "prompt" in manifest:
        prompt_summary = _text_summary(manifest.pop("prompt", ""))
        manifest["prompt_hash"] = manifest.get("prompt_hash") or prompt_summary["hash"]
        manifest["prompt_preview"] = manifest.get("prompt_preview") or prompt_summary["preview"]
        manifest["prompt_length"] = int(manifest.get("prompt_length") or prompt_summary["length"] or 0)
        manifest["prompt_redacted"] = True
    elif "prompt_hash" in manifest or "prompt_preview" in manifest or "prompt_length" in manifest:
        manifest["prompt_redacted"] = True

    return manifest


def sanitize_runtime_task_payload(payload: dict[str, Any]) -> dict[str, Any]:
    task = dict(payload or {})
    if "request" in task and isinstance(task["request"], dict):
        task["request"] = sanitize_runtime_request_payload(task["request"])
    return task


def write_json_artifact(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return path


def describe_artifact(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "name": path.name,
            "file_path": str(path.resolve()),
            "exists": False,
            "size_bytes": 0,
            "sha256": "",
        }
    content = path.read_bytes()
    return {
        "name": path.name,
        "file_path": str(path.resolve()),
        "exists": True,
        "size_bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def write_run_manifest(run_id: str, payload: dict[str, Any]) -> Path:
    path = run_manifest_path(run_id)
    safe_payload = sanitize_runtime_manifest_payload(payload)
    path.write_text(json.dumps(safe_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def read_run_manifest(run_id: str) -> dict[str, Any]:
    path = run_manifest_path(run_id)
    if not path.exists():
        raise FileNotFoundError(f"Codex run not found: {run_id}")
    return json.loads(path.read_text(encoding="utf-8"))


def append_stdout_line(run_id: str, payload: dict[str, Any]) -> None:
    path = stdout_log_path(run_id)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def append_stderr_text(run_id: str, text: str) -> None:
    if not text:
        return
    path = stderr_log_path(run_id)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(text)


def write_transcript(run_id: str, transcript: list[dict[str, Any]]) -> Path:
    path = transcript_path(run_id)
    path.write_text(json.dumps(transcript, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def write_summary(run_id: str, text: str) -> Path:
    path = summary_path(run_id)
    path.write_text(text, encoding="utf-8")
    return path


def write_git_status_before(run_id: str, text: str) -> Path:
    path = git_status_before_path(run_id)
    path.write_text(text, encoding="utf-8")
    return path


def write_git_status_after(run_id: str, text: str) -> Path:
    path = git_status_after_path(run_id)
    path.write_text(text, encoding="utf-8")
    return path


def write_git_diff(run_id: str, patch_text: str) -> Path:
    path = git_diff_path(run_id)
    path.write_text(patch_text, encoding="utf-8")
    return path


def write_changed_files(run_id: str, paths: list[str]) -> Path:
    path = changed_files_path(run_id)
    path.write_text(json.dumps(paths, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def read_stdout_log(run_id: str, offset: int = 0, limit_bytes: int = 256000) -> dict[str, Any]:
    path = stdout_log_path(run_id)
    if not path.exists():
        raise FileNotFoundError(f"Codex stdout log not found for run: {run_id}")
    data = path.read_bytes()
    start = max(0, min(int(offset or 0), len(data)))
    end = min(len(data), start + max(1, int(limit_bytes or 256000)))
    content = data[start:end].decode("utf-8", errors="replace")
    return {
        "run_id": run_id,
        "log_path": str(path.resolve()),
        "content": content,
        "next_offset": end if end < len(data) else None,
    }
