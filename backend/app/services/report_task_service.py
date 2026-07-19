from __future__ import annotations

import json
import os
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from fastapi import HTTPException

from app.models import CodexRunRequest
from app.models import SmartReportRequest
from app.services.codex_runtime_learning_ledger_service import capture_report_failure_learning_ledger
from app.services.path_service import STORAGE_DIR


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


TASK_DIR = STORAGE_DIR / "runs" / "report_tasks"
TASK_DIR.mkdir(parents=True, exist_ok=True)
QUEUE_REJECTION_LOG_PATH = TASK_DIR / "queue_rejections.jsonl"

_TASKS: dict[str, dict[str, Any]] = {}
_TASK_LOCK = threading.Lock()
_TASK_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="report-task")
MAX_ACTIVE_REPORT_TASKS = max(1, int(os.getenv("ASTERIA_MAX_ACTIVE_REPORT_TASKS", "6")))
_PIPELINE_RECONCILIATION_SPECS = (
    {
        "job_id_key": "generic_long_cli_pipeline_job_id",
        "snapshot_key": "generic_long_cli_pipeline",
        "final_output_key": "generic_long_cli_final_output",
        "summary_prefix": "generic_long_cli_pipeline",
    },
    {
        "job_id_key": "multi_table_generic_long_cli_pipeline_job_id",
        "snapshot_key": "multi_table_generic_long_cli_pipeline",
        "final_output_key": "multi_table_generic_long_cli_final_output",
        "summary_prefix": "multi_table_generic_long_cli_pipeline",
    },
    {
        "job_id_key": "internet_ops_long_cli_pipeline_job_id",
        "snapshot_key": "internet_ops_long_cli_pipeline",
        "final_output_key": "internet_ops_long_cli_final_output",
        "summary_prefix": "internet_ops_long_cli_pipeline",
    },
    {
        "job_id_key": "ecommerce_long_cli_pipeline_job_id",
        "snapshot_key": "ecommerce_long_cli_pipeline",
        "final_output_key": "ecommerce_long_cli_final_output",
        "summary_prefix": "ecommerce_long_cli_pipeline",
    },
    {
        "job_id_key": "procurement_sales_long_cli_pipeline_job_id",
        "snapshot_key": "procurement_sales_long_cli_pipeline",
        "final_output_key": "procurement_sales_long_cli_final_output",
        "summary_prefix": "procurement_sales_long_cli_pipeline",
    },
)


def create_codex_run_task(*args: Any, **kwargs: Any) -> dict[str, Any]:
    from app.services.codex_runtime_task_service import create_codex_run_task as _create_codex_run_task

    return _create_codex_run_task(*args, **kwargs)


def generate_smart_report(*args: Any, **kwargs: Any) -> dict[str, Any]:
    from app.services.report_service import generate_smart_report as _generate_smart_report

    return _generate_smart_report(*args, **kwargs)


def _task_path(job_id: str) -> Path:
    return TASK_DIR / f"{job_id}.json"


def _persist_task(task: dict[str, Any]) -> None:
    _task_path(str(task.get("job_id") or "")).write_text(
        json.dumps(task, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


def _append_queue_rejection_event(*, dataset_id: str, active_count: int, limit: int) -> None:
    payload = {
        "event": "report_task_queue_rejected",
        "timestamp": _now_iso(),
        "dataset_id": dataset_id,
        "active_task_count": int(active_count),
        "limit": int(limit),
        "reason": "active_report_task_limit_exceeded",
    }
    with QUEUE_REJECTION_LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _active_report_task_count() -> int:
    return sum(
        1
        for task in _TASKS.values()
        if str(task.get("status") or "").strip().lower() in {"queued", "running"}
    )


def _stage_progress(stage_id: str, status: str) -> int:
    base = {
        "queued": 2,
        "orchestration_start": 8,
        "orchestration_ready": 14,
        "init": 18,
        "statistical_method_selection": 24,
        "relation_context": 32,
        "analysis_job_graph": 44,
        "reasoning_chain": 68,
        "generic_agent_workflow": 78,
        "followup_mining": 84,
        "post_gate": 90,
        "rendering": 94,
        "packaging": 97,
        "completed": 100,
        "failed": 100,
    }
    progress = base.get(stage_id, 12 if stage_id.endswith("_start") else 88 if stage_id.startswith("release_gate") else 40)
    if status == "completed" and progress < 100:
        progress = min(progress + 4, 99)
    return progress


def _update_task(job_id: str, **updates: Any) -> dict[str, Any]:
    with _TASK_LOCK:
        task = dict(_TASKS.get(job_id) or {})
        task.update(updates)
        task["updated_at"] = _now_iso()
        _TASKS[job_id] = task
        _persist_task(task)
        return dict(task)


def _build_pipeline_snapshot(pipeline: dict[str, Any], existing: dict[str, Any] | None = None) -> dict[str, Any]:
    snapshot = dict(existing or {})
    snapshot.update(
        {
            "status": str(pipeline.get("status") or ""),
            "error": str(pipeline.get("error") or ""),
            "progress_percent": int(pipeline.get("progress_percent") or 0),
            "current_stage_id": str(pipeline.get("current_stage_id") or ""),
            "current_stage_title": str(pipeline.get("current_stage_title") or ""),
            "current_stage_detail": str(pipeline.get("current_stage_detail") or ""),
            "linked_codex_run_ids": list(pipeline.get("linked_codex_run_ids") or []),
            "stage_outputs": dict(pipeline.get("stage_outputs") or {}),
            "artifact_index": list(pipeline.get("artifact_index") or []),
        }
    )
    return snapshot


def _refresh_linked_pipeline_snapshots(task: dict[str, Any], *, job_id: str) -> dict[str, Any]:
    refreshed = dict(task)
    result = dict(refreshed.get("result") or {}) if isinstance(refreshed.get("result"), dict) else None
    result_summary = dict(refreshed.get("result_summary") or {})
    result_changed = False
    summary_changed = False

    for spec in _PIPELINE_RECONCILIATION_SPECS:
        pipeline_job_id = ""
        if result is not None:
            pipeline_job_id = str(result.get(spec["job_id_key"]) or "").strip()
        if not pipeline_job_id:
            pipeline_job_id = str(result_summary.get(spec["job_id_key"]) or "").strip()
        if not pipeline_job_id:
            continue
        try:
            from app.services.codex_runtime_pipeline_service import get_pipeline_job

            pipeline = get_pipeline_job(pipeline_job_id)
        except Exception:
            continue

        snapshot = _build_pipeline_snapshot(
            pipeline,
            existing=(result.get(spec["snapshot_key"]) if result is not None and isinstance(result.get(spec["snapshot_key"]), dict) else None),
        )
        if result is not None and result.get(spec["snapshot_key"]) != snapshot:
            result[spec["snapshot_key"]] = snapshot
            result_changed = True

        final_output = dict(pipeline.get("final_output") or {})
        if result is not None and final_output and result.get(spec["final_output_key"]) != final_output:
            result[spec["final_output_key"]] = final_output
            result_changed = True

        next_summary_fields = {
            spec["job_id_key"]: pipeline_job_id,
            f"{spec['summary_prefix']}_status": str(pipeline.get("status") or ""),
            f"{spec['summary_prefix']}_current_stage": str(pipeline.get("current_stage_id") or ""),
            f"{spec['summary_prefix']}_progress_percent": int(pipeline.get("progress_percent") or 0),
        }
        full_table_artifact_name = str(final_output.get("full_table_artifact_name") or "").strip()
        if full_table_artifact_name:
            next_summary_fields[f"{spec['summary_prefix']}_full_table_artifact"] = full_table_artifact_name
        for key, value in next_summary_fields.items():
            if result_summary.get(key) != value:
                result_summary[key] = value
                summary_changed = True

    if not result_changed and not summary_changed:
        return refreshed

    if result is not None:
        refreshed["result"] = result
    refreshed["result_summary"] = result_summary
    refreshed["updated_at"] = _now_iso()

    with _TASK_LOCK:
        _TASKS[job_id] = dict(refreshed)
        if result_changed or summary_changed:
            _persist_task(refreshed)
    return dict(refreshed)


def _append_stage_event(job_id: str, event: dict[str, Any]) -> None:
    with _TASK_LOCK:
        task = dict(_TASKS.get(job_id) or {})
        events = list(task.get("stage_events") or [])
        events.append(event)
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        result_summary = dict(task.get("result_summary") or {})
        stage_id = str(event.get("stage_id") or "")
        if stage_id in {
            "generic_long_cli_pipeline",
            "multi_table_generic_long_cli_pipeline",
            "internet_ops_long_cli_pipeline",
            "ecommerce_long_cli_pipeline",
            "procurement_sales_long_cli_pipeline",
        }:
            summary_prefix = {
                "generic_long_cli_pipeline": "generic_long_cli_pipeline",
                "multi_table_generic_long_cli_pipeline": "multi_table_generic_long_cli_pipeline",
                "internet_ops_long_cli_pipeline": "internet_ops_long_cli_pipeline",
                "ecommerce_long_cli_pipeline": "ecommerce_long_cli_pipeline",
                "procurement_sales_long_cli_pipeline": "procurement_sales_long_cli_pipeline",
            }.get(stage_id, "generic_long_cli_pipeline")
            pipeline_job_id = str(payload.get("pipeline_job_id") or "").strip()
            if pipeline_job_id:
                linked_pipeline_ids = list(task.get("linked_codex_pipeline_job_ids") or [])
                linked_pipeline_ids.append(pipeline_job_id)
                task["linked_codex_pipeline_job_ids"] = list(dict.fromkeys(linked_pipeline_ids))
                result_summary[f"{summary_prefix}_job_id"] = pipeline_job_id
                result_summary[f"{summary_prefix}_status"] = str(
                    payload.get("pipeline_status") or payload.get("status") or ""
                )
                result_summary[f"{summary_prefix}_current_stage"] = str(
                    payload.get("pipeline_current_stage_id") or ""
                )
                try:
                    result_summary[f"{summary_prefix}_progress_percent"] = int(
                        payload.get("pipeline_progress_percent") or 0
                    )
                except Exception:
                    result_summary[f"{summary_prefix}_progress_percent"] = 0
                existing_summary_ids = list(result_summary.get("linked_codex_pipeline_job_ids") or [])
                existing_summary_ids.append(pipeline_job_id)
                result_summary["linked_codex_pipeline_job_ids"] = list(dict.fromkeys(existing_summary_ids))
        progress_candidates = [
            _stage_progress(str(event.get("stage_id") or ""), str(payload.get("status") or "")),
        ]
        try:
            progress_candidates.append(int(payload.get("report_progress_percent") or 0))
        except Exception:
            pass
        progress = max(int(task.get("progress_percent") or 0), *progress_candidates)
        task.update(
            {
                "status": "running",
                "progress_percent": progress,
                "current_stage_id": event.get("stage_id") or "",
                "current_stage_title": event.get("title") or "",
                "current_stage_detail": event.get("detail") or "",
                "stage_events": events[-80:],
                "result_summary": result_summary,
                "updated_at": _now_iso(),
            }
        )
        _TASKS[job_id] = task
        _persist_task(task)


def _register_runtime_child_job(parent_job_id: str, child_task: dict[str, Any]) -> dict[str, Any]:
    from app.services.codex_runtime_service import normalize_runtime_telemetry_contract

    with _TASK_LOCK:
        task = dict(_TASKS.get(parent_job_id) or {})
        children = list(task.get("runtime_child_jobs") or [])
        child_job_id = str(child_task.get("job_id") or "")
        child_task = normalize_runtime_telemetry_contract(
            dict(child_task),
            request=child_task.get("request") if isinstance(child_task.get("request"), dict) else None,
            default_artifact_source="codex_runtime_task",
            parent_report_job_id=str(child_task.get("parent_report_job_id") or parent_job_id),
            parent_report_id=str(child_task.get("parent_report_id") or ""),
            stage_id=str(child_task.get("stage_id") or ""),
            purpose=str(child_task.get("purpose") or ""),
        )
        normalized = {
            "job_id": child_job_id,
            "run_id": str(child_task.get("run_id") or ""),
            "author_mode": str(child_task.get("author_mode") or ""),
            "runtime_state": str(child_task.get("runtime_state") or ""),
            "degradation_state": str(child_task.get("degradation_state") or ""),
            "artifact_source": str(child_task.get("artifact_source") or ""),
            "parent_report_job_id": str(child_task.get("parent_report_job_id") or parent_job_id),
            "parent_report_id": str(child_task.get("parent_report_id") or ""),
            "parent_stage_id": str(child_task.get("parent_stage_id") or ""),
            "child_index": int(child_task.get("child_index") or 0),
            "stage_id": str(child_task.get("stage_id") or ""),
            "purpose": str(child_task.get("purpose") or ""),
            "status": str(child_task.get("status") or ""),
            "progress_percent": int(child_task.get("progress_percent") or 0),
            "current_stage_id": str(child_task.get("current_stage_id") or ""),
            "current_stage_title": str(child_task.get("current_stage_title") or ""),
            "current_stage_detail": str(child_task.get("current_stage_detail") or ""),
        }
        replaced = False
        for index, existing in enumerate(children):
            if str(existing.get("job_id") or "") == child_job_id:
                children[index] = {**existing, **normalized}
                replaced = True
                break
        if not replaced:
            children.append(normalized)
        task["runtime_child_jobs"] = children
        runtime_ids = [str(item.get("job_id") or "") for item in children if str(item.get("job_id") or "").strip()]
        task["runtime_child_job_ids"] = list(dict.fromkeys(runtime_ids))
        task["updated_at"] = _now_iso()
        _TASKS[parent_job_id] = task
        _persist_task(task)
        return dict(task)


def _handle_runtime_child_stage_event(parent_job_id: str, event: dict[str, Any]) -> None:
    payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
    child_job_id = str(payload.get("runtime_child_job_id") or "").strip()
    if child_job_id:
        _register_runtime_child_job(
            parent_job_id,
            {
                "job_id": child_job_id,
                "run_id": str(payload.get("run_id") or payload.get("runtime_child_run_id") or ""),
                "author_mode": str(payload.get("author_mode") or ""),
                "runtime_state": str(payload.get("runtime_state") or ""),
                "degradation_state": str(payload.get("degradation_state") or ""),
                "artifact_source": str(payload.get("artifact_source") or ""),
                "parent_report_job_id": str(payload.get("parent_report_job_id") or payload.get("runtime_parent_report_job_id") or parent_job_id),
                "parent_report_id": str(payload.get("parent_report_id") or payload.get("runtime_parent_report_id") or ""),
                "parent_stage_id": str(payload.get("parent_stage_id") or payload.get("runtime_parent_stage_id") or ""),
                "child_index": int(payload.get("child_index") or payload.get("runtime_child_index") or 0),
                "stage_id": str(payload.get("stage_id") or payload.get("runtime_stage_id") or ""),
                "purpose": str(payload.get("purpose") or payload.get("runtime_purpose") or ""),
                "status": str(payload.get("runtime_child_status") or payload.get("status") or ""),
                "progress_percent": int(payload.get("runtime_child_progress_percent") or 0),
                "current_stage_id": str(payload.get("runtime_child_current_stage_id") or event.get("stage_id") or ""),
                "current_stage_title": str(payload.get("runtime_child_current_stage_title") or event.get("title") or ""),
                "current_stage_detail": str(payload.get("runtime_child_current_stage_detail") or event.get("detail") or ""),
            },
        )
    parent_event = dict(event)
    parent_payload = dict(payload)
    if str(parent_payload.get("status") or "").strip().lower() in {"failed", "cancelled", "timed_out"}:
        parent_payload["status"] = "running"
    parent_event["payload"] = parent_payload
    _append_stage_event(parent_job_id, parent_event)


def _create_runtime_child_task_for_parent(
    parent_job_id: str,
) -> Callable[..., dict[str, Any]]:
    child_counter = {"value": 0}

    def _creator(
        request: CodexRunRequest,
        *,
        parent_report_id: str = "",
        parent_stage_id: str = "",
        stage_id: str = "",
        purpose: str = "",
        artifact_source: str = "",
        stage_listener: Callable[[dict[str, Any]], None] | None = None,
    ) -> dict[str, Any]:
        child_counter["value"] += 1

        def _combined_listener(event: dict[str, Any]) -> None:
            _handle_runtime_child_stage_event(parent_job_id, event)
            if stage_listener:
                try:
                    stage_listener(dict(event))
                except Exception:
                    pass

        child_task = create_codex_run_task(
            request,
            parent_report_job_id=parent_job_id,
            parent_report_id=parent_report_id,
            parent_stage_id=parent_stage_id or stage_id,
            child_index=int(child_counter["value"]),
            stage_id=stage_id,
            purpose=purpose,
            artifact_source=artifact_source,
            stage_listener=_combined_listener,
            return_full=True,
        )
        _register_runtime_child_job(parent_job_id, child_task)
        return child_task

    return _creator


def _run_task(job_id: str, dataset_id: str, request: SmartReportRequest) -> None:
    def progress_callback(event: dict[str, Any]) -> None:
        _append_stage_event(job_id, event)

    _update_task(
        job_id,
        status="running",
        progress_percent=2,
        current_stage_id="queued",
        current_stage_title="任务已创建",
        current_stage_detail="报告任务已进入后台队列，等待开始执行。",
    )
    try:
        runtime_child_task_creator = _create_runtime_child_task_for_parent(job_id)
        result = generate_smart_report(
            dataset_id,
            request,
            progress_callback=progress_callback,
            report_job_id=job_id,
            runtime_child_task_creator=runtime_child_task_creator,
        )
        for child_task in list(result.get("runtime_child_jobs") or []):
            _register_runtime_child_job(job_id, child_task)
        runtime_child_jobs = list(_TASKS.get(job_id, {}).get("runtime_child_jobs") or [])
        main_downloadable = result.get("main_downloadable") or {}
        _update_task(
            job_id,
            status="completed",
            progress_percent=100,
            current_stage_id="completed",
            current_stage_title="报告生成完成",
            current_stage_detail="主报告、附录与导出物已经生成完成。",
            result=result,
            linked_codex_run_ids=list(result.get("linked_codex_run_ids") or []),
            linked_codex_task_ids=list(result.get("linked_codex_task_ids") or []),
            runtime_child_jobs=runtime_child_jobs,
            runtime_child_job_ids=[str(item.get("job_id") or "") for item in runtime_child_jobs if str(item.get("job_id") or "").strip()],
            result_summary={
                "report_id": result.get("report_id"),
                "dataset_name": result.get("dataset_name"),
                "sheet_name": result.get("sheet_name"),
                "main_downloadable": main_downloadable.get("name"),
                "main_downloadable_name": main_downloadable.get("name"),
                "main_downloadable_path": main_downloadable.get("path"),
                "formal_pdf_allowed": bool(result.get("formal_pdf_allowed")),
                "release_blocked": bool(result.get("release_blocked")),
                "linked_codex_run_ids": list(result.get("linked_codex_run_ids") or []),
                "linked_codex_task_ids": list(result.get("linked_codex_task_ids") or []),
                "linked_codex_pipeline_job_ids": list(result.get("linked_codex_pipeline_job_ids") or []),
                "historical_style_cli_pipeline_job_id": result.get("historical_style_cli_pipeline_job_id") or "",
                "historical_style_cli_pipeline_status": (
                    (result.get("historical_style_cli_pipeline") or {}).get("status")
                    if isinstance(result.get("historical_style_cli_pipeline"), dict)
                    else ""
                ),
                "historical_style_cli_main_artifact": (
                    (result.get("historical_style_cli_final_output") or {}).get("main_artifact_name")
                    if isinstance(result.get("historical_style_cli_final_output"), dict)
                    else ""
                ),
                "historical_style_cli_report_family": (
                    (result.get("historical_style_cli_final_output") or {}).get("historical_report_family")
                    if isinstance(result.get("historical_style_cli_final_output"), dict)
                    else ""
                ),
                "historical_style_cli_rendered_page_count": (
                    (result.get("historical_style_cli_final_output") or {}).get("rendered_page_count")
                    if isinstance(result.get("historical_style_cli_final_output"), dict)
                    else 0
                ),
                "historical_style_cli_planned_page_count": (
                    (result.get("historical_style_cli_final_output") or {}).get("planned_page_count")
                    if isinstance(result.get("historical_style_cli_final_output"), dict)
                    else 0
                ),
                "generic_long_cli_pipeline_job_id": result.get("generic_long_cli_pipeline_job_id") or "",
                "generic_long_cli_pipeline_status": (
                    (result.get("generic_long_cli_pipeline") or {}).get("status")
                    if isinstance(result.get("generic_long_cli_pipeline"), dict)
                    else ""
                ),
                "generic_long_cli_main_artifact": (
                    (result.get("generic_long_cli_final_output") or {}).get("main_artifact_name")
                    if isinstance(result.get("generic_long_cli_final_output"), dict)
                    else ""
                ),
                "internet_ops_long_cli_pipeline_job_id": result.get("internet_ops_long_cli_pipeline_job_id") or "",
                "internet_ops_long_cli_pipeline_status": (
                    (result.get("internet_ops_long_cli_pipeline") or {}).get("status")
                    if isinstance(result.get("internet_ops_long_cli_pipeline"), dict)
                    else ""
                ),
                "internet_ops_long_cli_main_artifact": (
                    (result.get("internet_ops_long_cli_final_output") or {}).get("main_artifact_name")
                    if isinstance(result.get("internet_ops_long_cli_final_output"), dict)
                    else ""
                ),
                "procurement_sales_long_cli_pipeline_job_id": result.get("procurement_sales_long_cli_pipeline_job_id") or "",
                "procurement_sales_long_cli_pipeline_status": (
                    (result.get("procurement_sales_long_cli_pipeline") or {}).get("status")
                    if isinstance(result.get("procurement_sales_long_cli_pipeline"), dict)
                    else ""
                ),
                "procurement_sales_long_cli_main_artifact": (
                    (result.get("procurement_sales_long_cli_final_output") or {}).get("main_artifact_name")
                    if isinstance(result.get("procurement_sales_long_cli_final_output"), dict)
                    else ""
                ),
                "procurement_sales_long_cli_full_table_artifact": (
                    (result.get("procurement_sales_long_cli_final_output") or {}).get("full_table_artifact_name")
                    if isinstance(result.get("procurement_sales_long_cli_final_output"), dict)
                    else ""
                ),
                "multi_table_generic_long_cli_pipeline_job_id": result.get("multi_table_generic_long_cli_pipeline_job_id") or "",
                "multi_table_generic_long_cli_pipeline_status": (
                    (result.get("multi_table_generic_long_cli_pipeline") or {}).get("status")
                    if isinstance(result.get("multi_table_generic_long_cli_pipeline"), dict)
                    else ""
                ),
                "multi_table_generic_long_cli_main_artifact": (
                    (result.get("multi_table_generic_long_cli_final_output") or {}).get("main_artifact_name")
                    if isinstance(result.get("multi_table_generic_long_cli_final_output"), dict)
                    else ""
                ),
                "runtime_child_job_ids": [str(item.get("job_id") or "") for item in runtime_child_jobs if str(item.get("job_id") or "").strip()],
            },
        )
    except Exception as exc:
        try:
            capture_report_failure_learning_ledger(
                dataset_id=dataset_id,
                report_job_id=job_id,
                request_payload=request.model_dump() if isinstance(request, SmartReportRequest) else {},
                error=str(exc),
            )
        except Exception:
            pass
        _update_task(
            job_id,
            status="failed",
            progress_percent=100,
            current_stage_id="failed",
            current_stage_title="报告生成失败",
            current_stage_detail=str(exc),
            error=str(exc),
        )


def create_report_task(dataset_id: str, request: SmartReportRequest) -> dict[str, Any]:
    job_id = f"report-task-{uuid.uuid4().hex[:12]}"
    task = {
        "job_id": job_id,
        "dataset_id": dataset_id,
        "status": "queued",
        "progress_percent": 0,
        "current_stage_id": "queued",
        "current_stage_title": "任务排队中",
        "current_stage_detail": "任务已创建，等待后台开始执行。",
        "stage_events": [],
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "error": "",
        "result_summary": {},
        "linked_codex_run_ids": [],
        "linked_codex_task_ids": [],
        "runtime_child_jobs": [],
        "runtime_child_job_ids": [],
    }
    with _TASK_LOCK:
        active_count = _active_report_task_count()
        if active_count >= MAX_ACTIVE_REPORT_TASKS:
            _append_queue_rejection_event(
                dataset_id=dataset_id,
                active_count=active_count,
                limit=MAX_ACTIVE_REPORT_TASKS,
            )
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Too many active report jobs. "
                    f"Current queued+running={active_count}, limit={MAX_ACTIVE_REPORT_TASKS}."
                ),
            )
        _TASKS[job_id] = dict(task)
        _persist_task(task)
    _TASK_EXECUTOR.submit(_run_task, job_id, dataset_id, request)
    return dict(task)


def get_report_task(job_id: str) -> dict[str, Any]:
    task: dict[str, Any] | None = None
    with _TASK_LOCK:
        existing = _TASKS.get(job_id)
        if existing is not None:
            task = dict(existing)
    if task is not None:
        return _refresh_linked_pipeline_snapshots(task, job_id=job_id)
    path = _task_path(job_id)
    if not path.exists():
        raise KeyError(job_id)
    task = json.loads(path.read_text(encoding="utf-8"))
    refreshed = _refresh_linked_pipeline_snapshots(task, job_id=job_id)
    with _TASK_LOCK:
        _TASKS[job_id] = dict(refreshed)
    return refreshed


def register_codex_pipeline_output_for_report_task(pipeline_job_id: str) -> dict[str, Any]:
    from app.services.report_service import register_codex_main_report_pipeline_output

    registration = register_codex_main_report_pipeline_output(pipeline_job_id)
    report_id = str(registration.get("report_id") or "")
    pipeline_type = str(registration.get("pipeline_type") or "")
    is_multi_table = pipeline_type == "multi_table_generic_long_cli_pipeline"
    is_procurement_shadow = pipeline_type == "procurement_sales_long_cli_pipeline"
    updated_task_ids: list[str] = []
    with _TASK_LOCK:
        known_task_ids = set(_TASKS.keys())
        for path in TASK_DIR.glob("*.json"):
            known_task_ids.add(path.stem)
        for job_id in sorted(known_task_ids):
            task = dict(_TASKS.get(job_id) or {})
            if not task:
                path = _task_path(job_id)
                if not path.exists():
                    continue
                try:
                    task = json.loads(path.read_text(encoding="utf-8"))
                except Exception:
                    continue
            result = task.get("result")
            if not isinstance(result, dict) or str(result.get("report_id") or "") != report_id:
                continue
            if is_multi_table:
                result["multi_table_generic_long_cli_pipeline_job_id"] = pipeline_job_id
                result["multi_table_generic_long_cli_final_output"] = (
                    registration.get("multi_table_generic_long_cli_final_output") or {}
                )
                result["multi_table_generic_long_cli_downloadable"] = registration.get("registered_downloadable") or {}
            elif is_procurement_shadow:
                procurement_full_table_downloadable = next(
                    (
                        item
                        for item in list(registration.get("downloadables") or [])
                        if "procurement_sales_cli_shadow_with_tables.pdf" in str(item.get("name") or "")
                    ),
                    {},
                )
                result["procurement_sales_long_cli_pipeline_job_id"] = pipeline_job_id
                result["procurement_sales_long_cli_final_output"] = (
                    registration.get("procurement_sales_long_cli_final_output") or {}
                )
                result["procurement_sales_long_cli_downloadable"] = registration.get("registered_downloadable") or {}
                result["procurement_sales_long_cli_full_table_downloadable"] = procurement_full_table_downloadable
                result["procurement_sales_long_cli_full_table_artifact_name"] = (
                    (registration.get("procurement_sales_long_cli_final_output") or {}).get("full_table_artifact_name")
                    or procurement_full_table_downloadable.get("name")
                    or ""
                )
            else:
                result["generic_long_cli_pipeline_job_id"] = pipeline_job_id
                result["generic_long_cli_final_output"] = registration.get("generic_long_cli_final_output") or {}
                result["generic_long_cli_downloadable"] = registration.get("registered_downloadable") or {}
            result["downloadables"] = registration.get("downloadables") or result.get("downloadables") or []
            result["main_downloadable"] = registration.get("main_downloadable") or result.get("main_downloadable") or {}
            if not is_multi_table and not is_procurement_shadow:
                result["quality_gate_result"] = registration.get("quality_gate_result") or result.get("quality_gate_result") or {}
                result["report_quality_score"] = registration.get("report_quality_score") or result.get("report_quality_score") or {}
            linked_pipeline_ids = list(result.get("linked_codex_pipeline_job_ids") or [])
            if pipeline_job_id not in linked_pipeline_ids:
                linked_pipeline_ids.append(pipeline_job_id)
            result["linked_codex_pipeline_job_ids"] = linked_pipeline_ids
            task["result"] = result
            summary = dict(task.get("result_summary") or {})
            main_downloadable = result.get("main_downloadable") or {}
            summary.update(
                {
                    "report_id": report_id,
                    "main_downloadable": main_downloadable.get("name"),
                    "main_downloadable_name": main_downloadable.get("name"),
                    "main_downloadable_path": main_downloadable.get("path"),
                    "linked_codex_pipeline_job_ids": linked_pipeline_ids,
                }
            )
            if is_multi_table:
                summary.update(
                    {
                        "multi_table_generic_long_cli_pipeline_job_id": pipeline_job_id,
                        "multi_table_generic_long_cli_pipeline_status": "completed",
                        "multi_table_generic_long_cli_main_artifact": (
                            (registration.get("multi_table_generic_long_cli_final_output") or {}).get("main_artifact_name")
                            or (registration.get("registered_downloadable") or {}).get("name")
                        ),
                    }
                )
            elif is_procurement_shadow:
                summary.update(
                    {
                        "procurement_sales_long_cli_pipeline_job_id": pipeline_job_id,
                        "procurement_sales_long_cli_pipeline_status": "completed",
                        "procurement_sales_long_cli_main_artifact": (
                            (registration.get("procurement_sales_long_cli_final_output") or {}).get("main_artifact_name")
                            or (registration.get("registered_downloadable") or {}).get("name")
                        ),
                        "procurement_sales_long_cli_full_table_artifact": (
                            (registration.get("procurement_sales_long_cli_final_output") or {}).get("full_table_artifact_name")
                            or (result.get("procurement_sales_long_cli_full_table_downloadable") or {}).get("name")
                            or ""
                        ),
                    }
                )
            else:
                summary.update(
                    {
                        "generic_long_cli_pipeline_job_id": pipeline_job_id,
                        "generic_long_cli_pipeline_status": "completed",
                        "generic_long_cli_main_artifact": (
                            (registration.get("generic_long_cli_final_output") or {}).get("main_artifact_name")
                            or (registration.get("registered_downloadable") or {}).get("name")
                        ),
                    }
                )
            task["result_summary"] = summary
            task["updated_at"] = _now_iso()
            _TASKS[job_id] = task
            _persist_task(task)
            updated_task_ids.append(job_id)
    registration["updated_report_task_ids"] = updated_task_ids
    return registration


def register_generic_long_cli_output_for_report_task(pipeline_job_id: str) -> dict[str, Any]:
    """Backward-compatible wrapper for the existing API import path."""
    return register_codex_pipeline_output_for_report_task(pipeline_job_id)
