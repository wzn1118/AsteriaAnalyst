from __future__ import annotations

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import uuid
from typing import Any, Callable

from fastapi import HTTPException

from app.models import CodexRunRequest, CodexRunTaskResponse
from app.services.codex_runtime_service import (
    cancel_codex_run,
    normalize_runtime_telemetry_contract,
    run_headless_codex,
)
from app.services.codex_runtime_store import sanitize_runtime_task_payload, task_path


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


_TASKS: dict[str, dict[str, Any]] = {}
_TASK_LOCK = threading.Lock()
_TASK_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="codex-runtime-task")

StageListener = Callable[[dict[str, Any]], None]


def _persist_task(task: dict[str, Any]) -> None:
    payload = sanitize_runtime_task_payload(task)
    path = task_path(str(task.get("job_id") or ""))
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _normalize_runtime_task_contract(task: dict[str, Any]) -> dict[str, Any]:
    return normalize_runtime_telemetry_contract(
        {
            **task,
            "task_id": str(task.get("task_id") or task.get("job_id") or ""),
        },
        request=task.get("request") if isinstance(task.get("request"), dict) else None,
        default_artifact_source="codex_runtime_task",
        parent_report_job_id=str(task.get("parent_report_job_id") or ""),
        parent_report_id=str(task.get("parent_report_id") or ""),
        parent_stage_id=str(task.get("parent_stage_id") or ""),
        child_index=int(task.get("child_index") or 0),
        stage_id=str(task.get("stage_id") or ""),
        purpose=str(task.get("purpose") or ""),
    )


def _stage_progress(stage_id: str, status: str) -> int:
    base = {
        "queued": 2,
        "prompt_prepared": 12,
        "workspace_validated": 20,
        "session_started": 36,
        "artifact_collection": 88,
        "completed": 100,
        "failed": 100,
        "cancelled": 100,
        "timed_out": 100,
    }
    progress = base.get(stage_id, 48)
    if status == "completed" and progress < 100:
        progress = min(progress + 4, 99)
    return progress


def _update_task(job_id: str, **updates: Any) -> dict[str, Any]:
    with _TASK_LOCK:
        task = dict(_TASKS.get(job_id) or {})
        task.update(updates)
        task["updated_at"] = _now_iso()
        task = _normalize_runtime_task_contract(task)
        _TASKS[job_id] = task
        _persist_task(task)
        return dict(task)


def _append_stage_event(job_id: str, event: dict[str, Any]) -> None:
    with _TASK_LOCK:
        task = dict(_TASKS.get(job_id) or {})
        events = list(task.get("stage_events") or [])
        events.append(event)
        event_payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        event_status = str(event_payload.get("status") or "")
        stage_id = str(event.get("stage_id") or "")
        progress = max(int(task.get("progress_percent") or 0), _stage_progress(stage_id, event_status))
        task.update(
            {
                "status": "running" if event_status not in {"failed"} else "failed",
                "progress_percent": progress,
                "current_stage_id": stage_id,
                "current_stage_title": str(event.get("title") or ""),
                "current_stage_detail": str(event.get("detail") or ""),
                "stage_events": events[-120:],
                "updated_at": _now_iso(),
            }
        )
        task = _normalize_runtime_task_contract(task)
        _TASKS[job_id] = task
        _persist_task(task)


def _runtime_child_stage_event(
    *,
    job_id: str,
    parent_report_job_id: str,
    parent_report_id: str,
    parent_stage_id: str,
    child_index: int,
    artifact_source: str,
    stage_id: str,
    purpose: str,
    event: dict[str, Any],
) -> dict[str, Any]:
    payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
    runtime_status = str(payload.get("status") or "")
    raw_stage_id = str(event.get("stage_id") or "")
    stage_scope = purpose or stage_id or "runtime"
    event_payload = normalize_runtime_telemetry_contract(
        {
            **payload,
            "status": runtime_status,
            "run_id": str(payload.get("run_id") or ""),
        },
        default_artifact_source="codex_runtime_task",
        parent_report_job_id=parent_report_job_id,
        parent_report_id=parent_report_id,
        parent_stage_id=parent_stage_id,
        child_index=child_index,
        stage_id=stage_id,
        purpose=purpose,
    )
    event_payload.update(
        {
            "source": "runtime_child_task",
            "runtime_child_job_id": job_id,
            "runtime_child_run_id": str(payload.get("run_id") or ""),
            "runtime_parent_report_job_id": parent_report_job_id,
            "runtime_parent_report_id": parent_report_id,
            "runtime_parent_stage_id": parent_stage_id,
            "runtime_child_index": child_index,
            "runtime_stage_id": stage_id,
            "runtime_purpose": purpose,
            "artifact_source": artifact_source or event_payload.get("artifact_source") or "",
            "runtime_child_status": runtime_status,
            "runtime_child_progress_percent": _stage_progress(raw_stage_id, runtime_status),
            "runtime_child_current_stage_id": raw_stage_id,
            "runtime_child_current_stage_title": str(event.get("title") or ""),
            "runtime_child_current_stage_detail": str(event.get("detail") or ""),
        }
    )
    return {
        "stage_id": f"runtime_child::{stage_scope}::{raw_stage_id or 'event'}",
        "title": f"Runtime child: {str(event.get('title') or 'External runtime')}",
        "detail": str(event.get("detail") or ""),
        "timestamp": str(event.get("timestamp") or _now_iso()),
        "payload": event_payload,
    }


def _run_task(
    job_id: str,
    request: CodexRunRequest,
    parent_report_job_id: str,
    parent_report_id: str,
    parent_stage_id: str,
    child_index: int,
    artifact_source: str,
    stage_id: str,
    purpose: str,
    stage_listener: StageListener | None = None,
) -> None:
    def _listener(event: dict[str, Any]) -> None:
        _append_stage_event(job_id, event)
        if stage_listener:
            try:
                stage_listener(
                    _runtime_child_stage_event(
                        job_id=job_id,
                        parent_report_job_id=parent_report_job_id,
                        parent_report_id=parent_report_id,
                        parent_stage_id=parent_stage_id,
                        child_index=child_index,
                        artifact_source=artifact_source,
                        stage_id=stage_id,
                        purpose=purpose,
                        event=event,
                    )
                )
            except Exception:
                pass

    _update_task(
        job_id,
        status="running",
        progress_percent=2,
        current_stage_id="queued",
        current_stage_title="Codex task queued",
        current_stage_detail="The Codex runtime task is waiting for backend execution.",
    )
    try:
        result = run_headless_codex(request, stage_listener=_listener)
        result = normalize_runtime_telemetry_contract(
            result,
            request=request,
            parent_report_job_id=parent_report_job_id,
            parent_report_id=parent_report_id,
            parent_stage_id=parent_stage_id,
            child_index=child_index,
            default_artifact_source=artifact_source or "codex_runtime_manifest",
            stage_id=stage_id,
            purpose=purpose,
        )
        final_status = str(result.get("status") or "completed")
        _update_task(
            job_id,
            run_id=str(result.get("run_id") or ""),
            author_mode=str(result.get("author_mode") or ""),
            runtime_state=str(result.get("runtime_state") or ""),
            degradation_state=str(result.get("degradation_state") or ""),
            artifact_source=str(result.get("artifact_source") or ""),
            parent_stage_id=str(result.get("parent_stage_id") or ""),
            child_index=int(result.get("child_index") or 0),
            status=final_status,
            progress_percent=100 if final_status in {"completed", "failed", "cancelled", "timed_out"} else 96,
            current_stage_id=final_status,
            current_stage_title="Codex runtime completed" if final_status == "completed" else "Codex runtime finished",
            current_stage_detail=str(result.get("summary") or result.get("error") or ""),
            result_summary={
                "run_id": result.get("run_id"),
                "session_id": result.get("session_id"),
                "summary": result.get("summary"),
                "changed_files": result.get("changed_files", []),
                "git_diff_url": result.get("git_diff_url"),
                "transcript_url": result.get("transcript_url"),
                "status": final_status,
                "author_mode": result.get("author_mode"),
                "runtime_state": result.get("runtime_state"),
                "degradation_state": result.get("degradation_state"),
                "artifact_source": result.get("artifact_source"),
                "parent_report_job_id": result.get("parent_report_job_id"),
                "parent_report_id": result.get("parent_report_id"),
                "parent_stage_id": result.get("parent_stage_id"),
                "child_index": result.get("child_index"),
                "stage_id": result.get("stage_id"),
                "purpose": result.get("purpose"),
            },
            error=str(result.get("error") or ""),
        )
    except Exception as exc:
        _update_task(
            job_id,
            status="failed",
            progress_percent=100,
            current_stage_id="failed",
            current_stage_title="Codex runtime failed",
            current_stage_detail=str(exc),
            error=str(exc),
        )


def create_codex_run_task(
    request: CodexRunRequest,
    *,
    parent_report_job_id: str = "",
    parent_report_id: str = "",
    parent_stage_id: str = "",
    child_index: int = 0,
    stage_id: str = "",
    purpose: str = "",
    artifact_source: str = "",
    stage_listener: StageListener | None = None,
    return_full: bool = False,
) -> dict[str, Any]:
    request = request.model_copy(
        update={
            "parent_report_id": str(parent_report_id or request.parent_report_id or "").strip(),
            "parent_report_job_id": str(parent_report_job_id or request.parent_report_job_id or "").strip(),
            "parent_stage_id": str(parent_stage_id or request.parent_stage_id or stage_id or request.stage_id or "").strip(),
            "child_index": int(child_index or request.child_index or 0),
            "artifact_source": str(artifact_source or request.artifact_source or "").strip(),
        }
    )
    job_id = f"codex-task-{uuid.uuid4().hex[:12]}"
    task = _normalize_runtime_task_contract(
        {
        "job_id": job_id,
        "run_id": "",
        "parent_report_job_id": str(request.parent_report_job_id or parent_report_job_id or "").strip(),
        "parent_report_id": str(request.parent_report_id or parent_report_id or "").strip(),
        "parent_stage_id": str(request.parent_stage_id or parent_stage_id or stage_id or request.stage_id or "").strip(),
        "child_index": int(request.child_index or child_index or 0),
        "stage_id": str(stage_id or request.stage_id or "").strip(),
        "purpose": str(purpose or request.purpose or "").strip(),
        "artifact_source": str(request.artifact_source or artifact_source or "").strip(),
        "status": "queued",
        "progress_percent": 0,
        "current_stage_id": "queued",
        "current_stage_title": "Task created",
        "current_stage_detail": "The headless Codex runtime task has been created.",
        "stage_events": [],
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "error": "",
        "result_summary": {},
        "request": request.model_dump(),
        }
    )
    with _TASK_LOCK:
        _TASKS[job_id] = dict(task)
        _persist_task(task)
    _TASK_EXECUTOR.submit(
        _run_task,
        job_id,
        request,
        str(parent_report_job_id or "").strip(),
        str(parent_report_id or "").strip(),
        str(parent_stage_id or request.parent_stage_id or stage_id or request.stage_id or "").strip(),
        int(child_index or request.child_index or 0),
        str(artifact_source or request.artifact_source or "").strip(),
        str(stage_id or request.stage_id or "").strip(),
        str(purpose or request.purpose or "").strip(),
        stage_listener,
    )
    if return_full:
        return dict(task)
    response = CodexRunTaskResponse.model_validate(task).model_dump()
    return _normalize_runtime_task_contract(response)


def get_codex_run_task(job_id: str) -> dict[str, Any]:
    with _TASK_LOCK:
        task = _TASKS.get(job_id)
        if task is not None:
            return _normalize_runtime_task_contract(dict(task))
    path = task_path(job_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Codex runtime task not found: {job_id}")
    return _normalize_runtime_task_contract(json.loads(path.read_text(encoding="utf-8")))


def cancel_codex_run_task(job_id: str) -> dict[str, Any]:
    task = get_codex_run_task(job_id)
    run_id = str(task.get("run_id") or "")
    if run_id:
        cancel_codex_run(run_id)
    updated = _update_task(
        job_id,
        status="cancelling",
        current_stage_id="cancelling",
        current_stage_title="Cancellation requested",
        current_stage_detail="A cancellation request was sent to the running Codex process.",
    )
    response = CodexRunTaskResponse.model_validate(updated).model_dump()
    return _normalize_runtime_task_contract(response)
