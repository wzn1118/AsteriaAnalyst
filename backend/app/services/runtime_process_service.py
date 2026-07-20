from __future__ import annotations

import csv
import hashlib
import json
import os
import time
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from app.services.codex_native_app_server_service import list_native_bridge_processes
from app.services.codex_runtime_pipeline_store import CODEX_PIPELINE_JOBS_DIR, read_pipeline_manifest, update_pipeline_manifest
from app.services.codex_runtime_task_service import get_codex_run_task
from app.services.path_service import CODEX_RUNTIME_TASKS_DIR, REPORTS_DIR, RUNS_DIR
from app.services.report_catalog_index_service import report_catalog_index_report_dirs


REPORT_DIR_PREFIX = "smart-report-"
RUNNING_STATUSES = {"queued", "running", "cancelling", "starting"}
TERMINAL_STATUSES = {"completed", "failed", "cancelled", "timed_out"}
PIPELINE_RESUMABLE_STATUSES = {"failed", "cancelled", "blocked", "error", "timed_out"}
ACTIVE_PROCESS_STATUSES = RUNNING_STATUSES | {"verifying", "auto_repairing"}
ACTIONABLE_PROCESS_STATUSES = {"failed", "cancelled", "blocked", "error", "timed_out"}
STALE_PROCESS_STATUSES = {"stale_queued", "stale_running", "stale_turn", "stale_cancelling"}
STALE_QUEUED_SECONDS = 30 * 60
STALE_RUNNING_SECONDS = 60 * 60
PIPELINE_NO_LIVE_EVIDENCE_STALE_SECONDS = 10 * 60
STALE_CANCELLING_SECONDS = 30
STALE_TURN_SECONDS = 20 * 60
RECENT_ACTIONABLE_SECONDS = 24 * 60 * 60
ACTIVE_SESSION_SCAN_LIMIT = 320
ACTIVE_REPORT_SCAN_LIMIT = 12
ACTIVE_PROCESS_CACHE_SECONDS = 5.0
_ACTIVE_PROCESS_CACHE: dict[str, Any] = {"key": None, "expires_at": 0.0, "payload": None}
_ACTIVE_PROCESS_CACHE_LOCK = threading.Lock()
_ACTIVE_PROCESS_CACHE_REFRESHING: set[tuple[int, int]] = set()
INTERNET_OPS_TOP12_TABLE_CSV = "ops_channel_source_aarrr_topn_small_multiples.csv"
INTERNET_OPS_TOP12_TABLE_TITLE = "Top12 组合漏斗配表"
CONTRACT_BATCH_MANIFEST_NAME = "runtime_contract_batch_manifest.json"
TASK_DIR = RUNS_DIR / "report_tasks"
CONTRACT_FRESHNESS_WINDOW_SECONDS = 36 * 60 * 60
INTERNET_OPS_CONTRACT_FILES: tuple[str, ...] = (
    "ops_full_field_metric_contract.json",
    "ops_derived_visual_manifest.json",
    "ops_metric_semantics_contract.json",
    "ops_consistency_issue_registry.json",
    "ops_channel_source_kpi_canonical.csv",
    "ops_management_thresholds.json",
    "ops_executive_action_rules.json",
    "ops_daily_action_plan.json",
    "ops_daily_action_owner_matrix.csv",
    "ops_canonical_fact_tables.json",
)
COMMON_RUNTIME_CONTRACT_FILES: tuple[str, ...] = (
    "pipeline_context.json",
    "source_schema.json",
    "source_profile.json",
    "source_dataset_profile.json",
    "source_visual_assets_index.json",
    "metric_semantic_contract.json",
    "metric_visual_registry.json",
    "05a_metric_chart_plan.json",
    "05b_metric_chart_render_log.json",
    "05c_claim_consistency_audit.json",
    "chart_insights.json",
)
PIPELINE_RUNTIME_CONTRACT_FILES: dict[str, tuple[str, ...]] = {
    "internet_ops_long_cli_pipeline": INTERNET_OPS_CONTRACT_FILES
    + (
        "ops_metric_glossary.json",
        "ops_dimension_kpi_summary.csv",
        "ops_cross_dimension_priority_tables.json",
        "ops_time_window_summary.csv",
        "ops_action_grounding.json",
    ),
    "procurement_sales_long_cli_pipeline": (
        "procurement_context_bundle.json",
        "procurement_field_registry.json",
        "procurement_readiness_check.json",
        "procurement_metric_mining_result.json",
        "procurement_relation_context.json",
        "05d_procurement_full_table_plan.json",
    ),
    "ecommerce_long_cli_pipeline": (
        "ecommerce_context_bundle.json",
        "ecommerce_field_registry.json",
        "ecommerce_readiness_check.json",
        "ecommerce_metric_mining_result.json",
        "ecommerce_relation_context.json",
    ),
    "multi_table_generic_long_cli_pipeline": (
        "multi_table_inventory.json",
        "multi_table_relationship_model.json",
        "multi_table_metric_specs.json",
        "multi_table_metric_execution.json",
    ),
    "media_campaign_cli_pipeline": (),
    "generic_long_cli_pipeline": (),
    "analyst_appendix_premium_pdf": (
        "analyst_appendix_context.json",
        "analyst_appendix_evidence_manifest.json",
    ),
}
PIPELINE_CONTRACT_ROLLBACK_STAGES: dict[str, tuple[str, ...]] = {
    "internet_ops_long_cli_pipeline": ("ops_inventory", "requirement_intent"),
    "procurement_sales_long_cli_pipeline": ("procurement_inventory", "metric_chart_planning", "requirement_intent"),
    "ecommerce_long_cli_pipeline": ("ecommerce_inventory", "metric_chart_planning", "requirement_intent"),
    "multi_table_generic_long_cli_pipeline": (
        "multi_table_inventory",
        "multi_table_data_inventory",
        "relation_modeling",
        "metric_chart_planning",
        "requirement_intent",
        "data_understanding",
    ),
    "media_campaign_cli_pipeline": ("data_understanding", "metric_chart_planning", "requirement_intent"),
    "generic_long_cli_pipeline": ("data_understanding", "metric_chart_planning", "requirement_intent"),
    "analyst_appendix_premium_pdf": ("appendix_intake", "premium_appendix_intake", "requirement_intent"),
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_datetime(value: str | None) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except Exception:
        return None


def _age_seconds(value: str | None) -> int | None:
    parsed = _parse_datetime(value)
    if parsed is None:
        return None
    return max(0, int((datetime.now(timezone.utc) - parsed).total_seconds()))


def _is_active_status(status: str) -> bool:
    return _canonical_runtime_status(status) in ACTIVE_PROCESS_STATUSES


def _is_actionable_status(status: str) -> bool:
    return _canonical_runtime_status(status) in ACTIONABLE_PROCESS_STATUSES


def _is_stale_status(status: str) -> bool:
    return str(status or "") in STALE_PROCESS_STATUSES


def _canonical_runtime_status(status: str) -> str:
    """Normalize internal revision/pipeline status variants for UI display.

    Raw task status is still preserved in `raw_status` and metadata; this only
    decides the user-facing observed state. It prevents custom verifier states
    such as `text_fast_path_completed` from leaking into the workbench.
    """
    text = str(status or "").strip()
    lowered = text.lower()
    if not lowered:
        return ""
    if lowered in {
        "text_fast_path_completed",
        "chart_fast_path_completed",
        "attachment_chart_path_completed",
        "attachment_profile_path_completed",
    } or lowered.endswith("_completed"):
        return "completed"
    if lowered in {"verification_failed", "failed_scope_miss", "failed_partial_application", "failed_scope_violation"}:
        return "failed"
    if lowered.startswith("failed_"):
        return "failed"
    if lowered in {"blocked_numeric_change", "blocked_change"} or lowered.startswith("blocked_"):
        return "blocked"
    return lowered


def _display_status(status: str, *, can_resume: bool = False) -> str:
    labels = {
        "not_started": "未启动",
        "queued": "排队中",
        "starting": "启动中",
        "running": "运行中",
        "cancelling": "取消中",
        "verifying": "验收中",
        "auto_repairing": "自动纠偏中",
        "active": "在线",
        "online": "在线",
        "idle": "空闲",
        "available": "可用",
        "completed": "已完成",
        "failed": "失败",
        "error": "错误",
        "cancelled": "已取消",
        "timed_out": "超时",
        "blocked": "已阻断",
        "stale_queued": "排队已停滞",
        "stale_running": "运行已停滞",
        "stale_turn": "对话已停滞",
        "stale_cancelling": "取消已停滞",
    }
    label = labels.get(str(status or ""), str(status or "未知"))
    if _is_stale_status(status) and can_resume:
        return f"{label}，可续跑"
    return label


def _stale_status_for(kind: str, status: str) -> str:
    if status in {"queued", "starting"}:
        return "stale_queued"
    if status == "cancelling":
        return "stale_cancelling"
    if kind == "report_agent_turn" or status in {"verifying", "auto_repairing"}:
        return "stale_turn"
    return "stale_running"


def _stale_limit_seconds(kind: str, status: str) -> int | None:
    if status in {"queued", "starting"}:
        return STALE_QUEUED_SECONDS
    if status == "cancelling":
        return STALE_CANCELLING_SECONDS
    if kind == "report_agent_turn" or status in {"verifying", "auto_repairing"}:
        return STALE_TURN_SECONDS
    if status == "running":
        return STALE_RUNNING_SECONDS
    return None


def _runtime_observation(
    *,
    kind: str,
    status: str,
    updated_at: str = "",
    started_at: str = "",
    live_evidence: bool = False,
) -> dict[str, Any]:
    raw_status = str(status or "")
    canonical_status = _canonical_runtime_status(raw_status)
    age_anchor = updated_at or started_at
    age = _age_seconds(age_anchor)
    observed_status = canonical_status or raw_status
    stale_reason = ""
    stale_limit = _stale_limit_seconds(kind, raw_status)
    if canonical_status in ACTIVE_PROCESS_STATUSES and not live_evidence:
        if age is None:
            observed_status = _stale_status_for(kind, canonical_status)
            stale_reason = "missing_runtime_heartbeat"
        elif stale_limit is not None and age > stale_limit:
            observed_status = _stale_status_for(kind, canonical_status)
            stale_reason = f"heartbeat_expired_{age}s_gt_{stale_limit}s"
    if _is_stale_status(observed_status) and not stale_reason:
        stale_reason = "manifest_marked_stale"
    return {
        "raw_status": raw_status,
        "observed_status": observed_status,
        "is_stale": _is_stale_status(observed_status),
        "is_active": _is_active_status(observed_status),
        "heartbeat_age_seconds": age,
        "stale_reason": stale_reason,
        "reconciliation_reason": "live_evidence" if live_evidence else stale_reason or "fresh_or_terminal",
    }


def _report_title(report_id: str) -> str:
    if not report_id:
        return ""
    report_dir = REPORTS_DIR / f"{REPORT_DIR_PREFIX}{report_id}"
    manifest = _read_json(report_dir / f"{report_id}-current_turn_export_manifest.json", {})
    if isinstance(manifest, dict):
        title = str(manifest.get("title") or manifest.get("report_title") or "").strip()
        if title:
            return title
    return f"报告 {report_id}"


def _read_json(path: Path, fallback: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return fallback


def _looks_corrupt_text(value: str) -> bool:
    text = str(value or "")
    if not text:
        return False
    if any(marker in text for marker in ("�", "鎶", "鍚", "缁", "灞", "娉", "鍙")):
        return True
    question_count = text.count("?")
    return len(text) >= 8 and question_count >= 5 and question_count / max(1, len(text)) > 0.35


def _reader_safe_text(value: Any, fallback: str = "") -> str:
    text = str(value or "")
    if _looks_corrupt_text(text):
        return fallback
    return text


def _reader_safe_payload(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _reader_safe_payload(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_reader_safe_payload(item) for item in value]
    if isinstance(value, str):
        return _reader_safe_text(value, "历史字段不可读")
    return value


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return path


def _report_dir(report_id: str) -> Path:
    clean_id = "".join(ch for ch in str(report_id or "") if ch.isalnum() or ch in {"_", "-"})
    path = (REPORTS_DIR / f"{REPORT_DIR_PREFIX}{clean_id}").resolve()
    try:
        path.relative_to(REPORTS_DIR.resolve())
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid report_id.") from exc
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Report not found: {clean_id}")
    return path


def _report_id_from_dir(report_dir: Path) -> str:
    return report_dir.name.removeprefix(REPORT_DIR_PREFIX)


def _walk_pipeline_ids(value: Any) -> set[str]:
    ids: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key or "")
            if key_text.endswith("pipeline_job_id") or key_text == "pipeline_job_id":
                ids.update(_walk_pipeline_ids(item))
            elif key_text.endswith("pipeline_job_ids") or key_text == "linked_codex_pipeline_job_ids":
                ids.update(_walk_pipeline_ids(item))
            else:
                ids.update(_walk_pipeline_ids(item))
    elif isinstance(value, list):
        for item in value:
            ids.update(_walk_pipeline_ids(item))
    else:
        text = str(value or "").strip()
        if text.startswith("codex-pipeline-"):
            ids.add(text)
    return ids


def _pipeline_ids_for_report_dir(report_id: str, report_dir: Path) -> set[str]:
    manifest = _read_json(report_dir / f"{report_id}-current_turn_export_manifest.json", {})
    ids = _walk_pipeline_ids(manifest) if isinstance(manifest, dict) else set()
    rebuild_root = report_dir / "codex_runtime_rebuild"
    if rebuild_root.is_dir():
        try:
            for profile_dir in rebuild_root.iterdir():
                if not profile_dir.is_dir():
                    continue
                for job_dir in profile_dir.iterdir():
                    if job_dir.is_dir() and job_dir.name.startswith("codex-pipeline-"):
                        ids.add(job_dir.name)
        except Exception:
            pass
    return ids


def _pipeline_manifest_paths_for_report(report_id: str, report_dir: Path) -> list[Path]:
    paths: list[Path] = []
    seen: set[str] = set()
    for pipeline_id in _pipeline_ids_for_report_dir(report_id, report_dir):
        path = CODEX_PIPELINE_JOBS_DIR / pipeline_id / "pipeline.json"
        key = str(path).lower()
        if key in seen or not path.is_file():
            continue
        seen.add(key)
        paths.append(path)
    return paths


def _codex_task_ids_for_report_dir(report_dir: Path) -> set[str]:
    ids: set[str] = set()
    session_root = report_dir / "codex_agent_sessions"
    if not session_root.is_dir():
        return ids
    try:
        session_paths = session_root.glob("*/session.json")
        for session_path in session_paths:
            session = _read_json(session_path, {})
            if not isinstance(session, dict):
                continue
            for value in (session.get("current_task_id"), (session.get("current_turn") or {}).get("task_id")):
                text = str(value or "").strip()
                if text:
                    ids.add(text)
    except Exception:
        return ids
    return ids


def _item(
    *,
    kind: str,
    item_id: str,
    report_id: str,
    status: str,
    label: str,
    stage_id: str = "",
    stage_title: str = "",
    progress_percent: int | None = None,
    error: str = "",
    can_cancel: bool = False,
    can_resume: bool = False,
    resume_label: str = "",
    disabled_reason: str = "",
    updated_at: str = "",
    started_at: str = "",
    last_event: str = "",
    scope: str = "report",
    linked_report_title: str = "",
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    status_text = str(status or "")
    age_anchor = updated_at or started_at
    meta_payload = _reader_safe_payload(dict(meta or {}))
    observation = _runtime_observation(
        kind=kind,
        status=status_text,
        updated_at=updated_at,
        started_at=started_at,
        live_evidence=bool(meta_payload.get("live_evidence")),
    )
    observed_status = str(observation.get("observed_status") or status_text)
    stale = bool(observation.get("is_stale"))
    active = bool(observation.get("is_active"))
    can_cancel = bool(can_cancel and active)
    can_resume = bool(can_resume)
    action_state = "running" if active else "stale" if stale else "resumable" if can_resume else "cancellable" if can_cancel else "idle"
    meta_payload.update(
        {
            "raw_status": status_text,
            "observed_status": observed_status,
            "is_stale": stale,
            "stale_reason": observation.get("stale_reason") or "",
            "heartbeat_age_seconds": observation.get("heartbeat_age_seconds"),
            "reconciliation_reason": observation.get("reconciliation_reason") or "",
        }
    )
    return {
        "kind": kind,
        "id": item_id,
        "report_id": report_id,
        "label": label,
        "status": observed_status,
        "raw_status": status_text,
        "observed_status": observed_status,
        "display_status": _display_status(observed_status, can_resume=can_resume),
        "is_active": active,
        "is_stale": stale,
        "scope": scope,
        "linked_report_title": _reader_safe_text(linked_report_title or _report_title(report_id), f"报告 {report_id}"),
        "stage_id": stage_id,
        "stage_title": _reader_safe_text(stage_title, stage_id or "历史状态"),
        "progress_percent": int(progress_percent) if progress_percent is not None else None,
        "error": _reader_safe_text(error, "历史错误信息不可读"),
        "can_cancel": bool(can_cancel),
        "can_resume": bool(can_resume),
        "resume_label": _reader_safe_text(resume_label, ""),
        "disabled_reason": _reader_safe_text(disabled_reason, ""),
        "started_at": started_at,
        "updated_at": updated_at,
        "age_seconds": _age_seconds(age_anchor),
        "last_event": _reader_safe_text(last_event or stage_title or error or "", stage_id or "历史事件"),
        "action_state": action_state,
        "meta": meta_payload,
    }


def _stage_order_ids(manifest: dict[str, Any]) -> list[str]:
    return [str(stage.get("stage_id") or "") for stage in list(manifest.get("stage_order") or []) if str(stage.get("stage_id") or "")]


def _stage_output_status(manifest: dict[str, Any], stage_id: str) -> str:
    stage_outputs = manifest.get("stage_outputs") if isinstance(manifest.get("stage_outputs"), dict) else {}
    return str((stage_outputs.get(stage_id) or {}).get("status") or "")


def _pipeline_retry_stage(manifest: dict[str, Any]) -> str:
    current_stage = manifest.get("current_stage") if isinstance(manifest.get("current_stage"), dict) else {}
    failed_stage = str(manifest.get("failed_stage") or current_stage.get("failed_stage") or "")
    current_stage_id = str(current_stage.get("stage_id") or manifest.get("current_stage_id") or "")
    stage_ids = _stage_order_ids(manifest)
    for candidate in (failed_stage, current_stage_id):
        if candidate and candidate in stage_ids:
            return candidate
    for stage_id in stage_ids:
        if _stage_output_status(manifest, stage_id) != "completed":
            return stage_id
    return stage_ids[-1] if stage_ids else ""


def _pipeline_error_text(manifest: dict[str, Any]) -> str:
    """Collect user-visible failure text without assuming where the stage wrote it."""
    parts = [
        str(manifest.get("error") or ""),
        str(manifest.get("last_error") or ""),
    ]
    current_stage = manifest.get("current_stage") if isinstance(manifest.get("current_stage"), dict) else {}
    parts.extend(
        [
            str(current_stage.get("error") or ""),
            str(current_stage.get("detail") or ""),
            str(current_stage.get("stage_detail") or ""),
        ]
    )
    stage_outputs = manifest.get("stage_outputs") if isinstance(manifest.get("stage_outputs"), dict) else {}
    for output in stage_outputs.values():
        if not isinstance(output, dict):
            continue
        parts.extend(
            [
                str(output.get("error") or ""),
                str(output.get("detail") or ""),
                str(output.get("message") or ""),
            ]
        )
    return "\n".join(part for part in parts if part).strip()


def _is_stale_codex_resume_error(error: str) -> bool:
    lowered = str(error or "").lower()
    return any(
        marker in lowered
        for marker in [
            "thread/resume failed",
            "no rollout found",
            "invalid thread",
            "invalid session",
            "unknown thread",
            "session not found",
        ]
    )


def _stage_id_containing(manifest: dict[str, Any], *needles: str) -> str:
    normalized_needles = [str(needle or "").lower() for needle in needles if str(needle or "").strip()]
    if not normalized_needles:
        return ""
    for stage_id in _stage_order_ids(manifest):
        lowered = stage_id.lower()
        if all(needle in lowered for needle in normalized_needles):
            return stage_id
    return ""


def _first_existing_stage(manifest: dict[str, Any], candidates: list[str]) -> str:
    stage_ids = set(_stage_order_ids(manifest))
    for candidate in candidates:
        if candidate in stage_ids:
            return candidate
    for candidate in candidates:
        lowered = candidate.lower()
        for stage_id in stage_ids:
            if lowered in stage_id.lower():
                return stage_id
    return ""


def _pipeline_resume_label(status: str, error: str) -> str:
    if status == "queued":
        return ""
    if status not in PIPELINE_RESUMABLE_STATUSES:
        return ""
    normalized_error = str(error or "").lower()
    if "gate" in normalized_error or "missing" in normalized_error:
        return "检查依赖并续跑"
    return "重试当前阶段"


def _pipeline_disabled_reason(status: str, retry_stage_id: str = "") -> str:
    if status in PIPELINE_RESUMABLE_STATUSES and retry_stage_id:
        return ""
    if status in PIPELINE_RESUMABLE_STATUSES and not retry_stage_id:
        return "找不到可重试阶段，请检查 pipeline manifest。"
    if status == "completed":
        return "已完成，无需续跑。"
    if status in RUNNING_STATUSES:
        return "正在运行，可取消但不能重复续跑。"
    return "当前 pipeline 不处于可续跑状态。"


def _pipeline_workspace(manifest: dict[str, Any]) -> Path | None:
    workspace = str(manifest.get("workspace_path") or "").strip()
    if not workspace:
        return None
    try:
        path = Path(workspace).resolve()
    except Exception:
        return None
    return path if path.exists() else None


def _pipeline_is_completed_report_retrofit(manifest: dict[str, Any]) -> bool:
    context = manifest.get("context_payload") if isinstance(manifest.get("context_payload"), dict) else {}
    if context.get("retrofit_from_completed_report") or context.get("retrofit_mode"):
        return True
    workspace = _pipeline_workspace(manifest)
    return bool(
        workspace
        and (
            (workspace / "retrofit_evidence_boundary.json").exists()
            or (workspace / "retrofit_source_asset_manifest.json").exists()
        )
    )


def _specialized_pipeline_label(
    pipeline_type: str,
    *,
    business_profile: str = "",
    report_lens: str = "",
) -> str:
    if pipeline_type == "media_campaign_cli_pipeline":
        return "投放智能链"
    if pipeline_type == "procurement_sales_long_cli_pipeline":
        return "采销智能链"
    if pipeline_type == "internet_ops_long_cli_pipeline":
        return "互联网运营智能链"
    if pipeline_type == "generic_long_cli_pipeline":
        if business_profile == "media_campaign_report" or report_lens == "media_review":
            return "投放智能链"
        if business_profile == "internet_operations_report":
            return "互联网运营智能链"
        if business_profile == "procurement_sales_report":
            return "采销智能链"
    return pipeline_type or "Codex pipeline"


def _completed_report_route_meta(business_profile: str, report_lens: str = "") -> dict[str, str]:
    label = _specialized_pipeline_label("generic_long_cli_pipeline", business_profile=business_profile, report_lens=report_lens)
    if label == "投放智能链":
        return {
            "pipeline_label": label,
            "resume_label": "启动投放智能链",
            "resume_strategy": "start_media_campaign_cli_pipeline",
            "specialized_pipeline_type": "media_campaign_cli_pipeline",
            "blocked_action": "start_media_campaign_cli_blocked",
        }
    if label == "互联网运营智能链":
        return {
            "pipeline_label": label,
            "resume_label": "启动互联网运营智能链",
            "resume_strategy": "start_internet_ops_cli_pipeline",
            "specialized_pipeline_type": "internet_ops_cli_pipeline",
            "blocked_action": "start_internet_ops_cli_blocked",
        }
    if label == "采销智能链":
        return {
            "pipeline_label": label,
            "resume_label": "启动采销智能链",
            "resume_strategy": "start_procurement_sales_cli_pipeline",
            "specialized_pipeline_type": "procurement_sales_cli_pipeline",
            "blocked_action": "start_procurement_sales_cli_blocked",
        }
    return {
        "pipeline_label": "普通报告 CLI 长链",
        "resume_label": "启动 CLI 长报告链",
        "resume_strategy": "start_generic_long_cli_pipeline",
        "specialized_pipeline_type": "generic_long_cli_pipeline",
        "blocked_action": "start_generic_long_cli_blocked",
    }


def _lightweight_completed_report_route_hint(report_id: str) -> dict[str, str]:
    try:
        from app.services.report_agent_session_service import _report_summary
    except Exception:
        return {"business_profile": "", "report_lens": ""}
    try:
        summary = _report_summary(_report_dir(report_id), catalog_mode=True)
    except Exception:
        return {"business_profile": "", "report_lens": ""}
    title_text = " ".join(
        [
            str(summary.get("title") or ""),
            str(summary.get("content_title") or ""),
            str(summary.get("dataset_name") or ""),
        ]
    ).lower()
    media_markers = ("投放", "campaign", "media", "曝光", "点击", "cpm", "cpc", "cpa", "硬广", "素材", "版位")
    internet_ops_markers = ("运营", "留存", "激活", "注册", "渠道", "新增", "转化", "用户生命周期")
    if any(marker in title_text for marker in media_markers):
        return {"business_profile": "media_campaign_report", "report_lens": "media_review"}
    if any(marker in title_text for marker in internet_ops_markers):
        return {"business_profile": "internet_operations_report", "report_lens": "internet_ops_review"}
    return {"business_profile": "", "report_lens": ""}


def _misrouted_completed_report_retrofit_preflight(manifest: dict[str, Any]) -> dict[str, Any]:
    pipeline_type = str(manifest.get("pipeline_type") or "")
    if pipeline_type != "generic_long_cli_pipeline" or not _pipeline_is_completed_report_retrofit(manifest):
        return {}
    context = manifest.get("context_payload") if isinstance(manifest.get("context_payload"), dict) else {}
    current_profile = str(context.get("business_profile") or "")
    current_lens = str(context.get("report_lens") or "")
    report_id = str(manifest.get("linked_report_id") or context.get("report_id") or "").strip()
    if not report_id:
        return {}
    route = _lightweight_completed_report_route_hint(report_id)
    target_profile = str(route.get("business_profile") or "")
    target_lens = str(route.get("report_lens") or "")
    if target_profile not in {"media_campaign_report", "internet_operations_report"}:
        return {}
    if target_profile == current_profile and target_lens == current_lens:
        return {}
    return {
        "handled": True,
        "resume_strategy": "rebuild_workspace_then_restart_pipeline",
        "resume_issue_kind": "misrouted_completed_report_retrofit",
        "repair_rule_id": "completed_report_retrofit_reprofile",
        "target_business_profile": target_profile,
        "target_report_lens": target_lens,
        "blocking_missing_inputs": [],
    }


def _mtime_iso(path: Path) -> str:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat().replace("+00:00", "Z")
    except Exception:
        return ""


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return ""


def _pipeline_contract_candidates(pipeline_type: str) -> list[str]:
    names = list(COMMON_RUNTIME_CONTRACT_FILES)
    names.extend(PIPELINE_RUNTIME_CONTRACT_FILES.get(str(pipeline_type or ""), ()))
    return list(dict.fromkeys(name for name in names if name))


def _contract_owner_stage(manifest: dict[str, Any], name: str) -> str:
    lowered = name.lower()
    if lowered.startswith("05a_"):
        return _first_existing_stage(manifest, ["metric_chart_planning"])
    if lowered.startswith("05b_"):
        return _first_existing_stage(manifest, ["metric_chart_render", "metric_chart_planning"])
    if lowered.startswith("05c_"):
        return _first_existing_stage(manifest, ["claim_consistency_audit", "review"])
    if lowered == "chart_insights.json":
        return _stage_id_containing(manifest, "chart_insights")
    if lowered.startswith("ops_"):
        return _first_existing_stage(manifest, ["ops_inventory", "ops_chart_insights"])
    if lowered.startswith("procurement_"):
        return _first_existing_stage(manifest, ["procurement_inventory"])
    if lowered.startswith("ecommerce_"):
        return _first_existing_stage(manifest, ["ecommerce_inventory"])
    if lowered.startswith("multi_table_"):
        return _first_existing_stage(manifest, ["multi_table_inventory", "relation_modeling"])
    if lowered.startswith("source_") or lowered == "pipeline_context.json":
        return _first_existing_stage(manifest, ["data_understanding", "requirement_intent", "ops_inventory", "procurement_inventory", "ecommerce_inventory"])
    return _pipeline_retry_stage(manifest)


def _contract_rollback_stage(manifest: dict[str, Any]) -> str:
    pipeline_type = str(manifest.get("pipeline_type") or "")
    candidates = list(PIPELINE_CONTRACT_ROLLBACK_STAGES.get(pipeline_type, ()))
    candidates.extend(["data_understanding", "requirement_intent"])
    retry_stage = _first_existing_stage(manifest, candidates)
    return retry_stage or _pipeline_retry_stage(manifest)


def _contract_batch_status(manifest: dict[str, Any]) -> dict[str, Any]:
    workspace = _pipeline_workspace(manifest)
    pipeline_type = str(manifest.get("pipeline_type") or "")
    pipeline_specific_names = set(PIPELINE_RUNTIME_CONTRACT_FILES.get(pipeline_type, ()))
    if not workspace:
        return {
            "workspace_missing": True,
            "records": [],
            "existing_records": [],
            "missing": _pipeline_contract_candidates(pipeline_type),
            "mtime_span_seconds": 0,
            "is_mixed_batch": False,
        }
    records: list[dict[str, Any]] = []
    existing_records: list[dict[str, Any]] = []
    missing: list[str] = []
    for name in _pipeline_contract_candidates(pipeline_type):
        path = workspace / name
        record: dict[str, Any] = {
            "name": name,
            "relative_path": name,
            "exists": path.exists(),
            "owner_stage": _contract_owner_stage(manifest, name),
        }
        if path.exists() and path.is_file():
            stat = path.stat()
            record.update(
                {
                    "size_bytes": stat.st_size,
                    "mtime": _mtime_iso(path),
                    "mtime_epoch": stat.st_mtime,
                    "hash": _sha256_file(path),
                }
            )
            existing_records.append(record)
        else:
            missing.append(name)
        records.append(record)
    freshness_records = [
        record
        for record in existing_records
        if (not pipeline_specific_names or str(record.get("name") or "") in pipeline_specific_names)
    ]
    mtimes = [float(record.get("mtime_epoch") or 0) for record in freshness_records if record.get("mtime_epoch")]
    span = max(mtimes) - min(mtimes) if len(mtimes) >= 2 else 0
    oldest = min(freshness_records, key=lambda record: float(record.get("mtime_epoch") or 0), default={})
    newest = max(freshness_records, key=lambda record: float(record.get("mtime_epoch") or 0), default={})
    return {
        "workspace_missing": False,
        "records": records,
        "existing_records": existing_records,
        "missing": missing,
        "mtime_span_seconds": int(span),
        "is_mixed_batch": span > CONTRACT_FRESHNESS_WINDOW_SECONDS,
        "oldest_contract": oldest.get("name") or "",
        "newest_contract": newest.get("name") or "",
    }


def _write_runtime_contract_batch_manifest(
    manifest: dict[str, Any],
    *,
    issue_kind: str,
    resume_strategy: str,
    status: dict[str, Any] | None = None,
) -> str:
    workspace = _pipeline_workspace(manifest)
    if not workspace:
        return ""
    batch_status = status or _contract_batch_status(manifest)
    payload = {
        "schema_version": "runtime_contract_batch_manifest.v1",
        "batch_id": f"resume-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{str(manifest.get('pipeline_job_id') or '')[:12]}",
        "pipeline_job_id": manifest.get("pipeline_job_id"),
        "pipeline_type": manifest.get("pipeline_type"),
        "issue_kind": issue_kind,
        "resume_strategy": resume_strategy,
        "created_at": _now_iso(),
        "contract_freshness_window_seconds": CONTRACT_FRESHNESS_WINDOW_SECONDS,
        "mtime_span_seconds": batch_status.get("mtime_span_seconds"),
        "is_mixed_batch": batch_status.get("is_mixed_batch"),
        "oldest_contract": batch_status.get("oldest_contract"),
        "newest_contract": batch_status.get("newest_contract"),
        "missing_contracts": list(batch_status.get("missing") or []),
        "records": list(batch_status.get("records") or []),
    }
    return str(_write_json(workspace / CONTRACT_BATCH_MANIFEST_NAME, payload).resolve())


def _is_contract_batch_error(error_text: str) -> bool:
    lowered = str(error_text or "").lower()
    return any(
        marker in lowered
        for marker in [
            "mixed-batch",
            "same-batch",
            "artifact freshness",
            "freshness gate",
            "contract batch",
            "stale contract",
            "regenerate workspace preparation",
            "runtime_contract_batch",
        ]
    )


def _is_downstream_contract_consumer(stage_id: str) -> bool:
    lowered = str(stage_id or "").lower()
    return any(token in lowered for token in ["review", "pdf", "html", "claim_consistency", "chart_insights"])


def _regenerate_internet_ops_contracts(manifest: dict[str, Any], batch_status: dict[str, Any]) -> dict[str, Any]:
    workspace = _pipeline_workspace(manifest)
    if not workspace:
        return {
            "handled": True,
            "resume_strategy": "blocked_missing_inputs",
            "resume_issue_kind": "missing_pipeline_workspace",
            "blocking_missing_inputs": ["pipeline_workspace"],
        }
    source_candidates = [
        workspace / "source_dataset.csv",
        workspace / "public_source_dataset.csv",
        workspace / "normalized_dataset.csv",
    ]
    source_dataset = next((path for path in source_candidates if path.exists()), None)
    if source_dataset is None:
        return {
            "handled": True,
            "resume_strategy": "blocked_missing_inputs",
            "resume_issue_kind": "missing_workspace_source_dataset_for_contract_rebuild",
            "blocking_missing_inputs": ["source_dataset.csv"],
            "contract_batch_manifest_path": _write_runtime_contract_batch_manifest(
                manifest,
                issue_kind="missing_workspace_source_dataset_for_contract_rebuild",
                resume_strategy="blocked_missing_inputs",
                status=batch_status,
            ),
        }
    try:
        import pandas as pd

        from app.services.report_service import _write_internet_ops_cli_evidence_pack

        frame = pd.read_csv(source_dataset, encoding="utf-8-sig")
        regenerated_outputs = _write_internet_ops_cli_evidence_pack(workspace_dir=workspace, frame=frame)
    except Exception as exc:
        return {
            "handled": True,
            "resume_strategy": "blocked_missing_inputs",
            "resume_issue_kind": "internet_ops_contract_rebuild_failed",
            "blocking_missing_inputs": [f"internet_ops_contract_rebuild_failed:{exc}"],
            "contract_batch_manifest_path": _write_runtime_contract_batch_manifest(
                manifest,
                issue_kind="internet_ops_contract_rebuild_failed",
                resume_strategy="blocked_missing_inputs",
                status=batch_status,
            ),
        }
    refreshed_status = _contract_batch_status(manifest)
    contract_manifest_path = _write_runtime_contract_batch_manifest(
        manifest,
        issue_kind="mixed_or_stale_runtime_contract_batch",
        resume_strategy="regenerate_workspace_contracts_then_continue",
        status=refreshed_status,
    )
    log = {
        "pipeline_job_id": manifest.get("pipeline_job_id"),
        "pipeline_type": manifest.get("pipeline_type"),
        "resume_strategy": "regenerate_workspace_contracts_then_continue",
        "resume_issue_kind": "mixed_or_stale_runtime_contract_batch",
        "source_dataset": str(source_dataset.resolve()),
        "regenerated_outputs": regenerated_outputs,
        "contract_batch_manifest_path": contract_manifest_path,
        "retry_stage_id": _contract_rollback_stage(manifest),
        "created_at": _now_iso(),
    }
    log_path = _write_json(workspace / "pipeline_contract_repair_log.json", log)
    return {
        "handled": True,
        "resume_strategy": "regenerate_workspace_contracts_then_continue",
        "resume_issue_kind": "mixed_or_stale_runtime_contract_batch",
        "retry_stage_id": _contract_rollback_stage(manifest),
        "rollback_stage_id": _contract_rollback_stage(manifest),
        "repair_log_path": str(log_path.resolve()),
        "contract_batch_manifest_path": contract_manifest_path,
        "blocking_missing_inputs": [],
    }


def _preflight_contract_batch_consistency(manifest: dict[str, Any], *, repair: bool = False) -> dict[str, Any]:
    retry_stage_id = _pipeline_retry_stage(manifest)
    error_text = _pipeline_error_text(manifest)
    explicit_contract_error = _is_contract_batch_error(error_text)
    batch_status = _contract_batch_status(manifest)
    if batch_status.get("workspace_missing"):
        context_payload = manifest.get("context_payload") if isinstance(manifest.get("context_payload"), dict) else {}
        linked_report_id = str(manifest.get("linked_report_id") or context_payload.get("report_id") or "")
        if linked_report_id:
            return {
                "handled": True,
                "resume_strategy": "rebuild_workspace_then_restart_pipeline",
                "resume_issue_kind": "missing_pipeline_workspace",
                "workspace_rebuild_path": str((REPORTS_DIR / f"{REPORT_DIR_PREFIX}{linked_report_id}" / "codex_runtime_rebuild").resolve()),
                "blocking_missing_inputs": [],
            }
        return {
            "handled": True,
            "resume_strategy": "blocked_missing_inputs",
            "resume_issue_kind": "missing_pipeline_workspace",
            "blocking_missing_inputs": ["pipeline_workspace"],
        }
    mixed_batch = bool(batch_status.get("is_mixed_batch"))
    should_handle = explicit_contract_error or (mixed_batch and _is_downstream_contract_consumer(retry_stage_id))
    if not should_handle:
        return {}
    pipeline_type = str(manifest.get("pipeline_type") or "")
    issue_kind = "mixed_runtime_contract_batch" if mixed_batch else "stale_or_missing_runtime_contract_batch"
    if pipeline_type == "internet_ops_long_cli_pipeline":
        if repair:
            result = _regenerate_internet_ops_contracts(manifest, batch_status)
        else:
            result = {
                "handled": True,
                "resume_strategy": "regenerate_workspace_contracts_then_continue",
                "resume_issue_kind": issue_kind,
                "retry_stage_id": _contract_rollback_stage(manifest),
                "rollback_stage_id": _contract_rollback_stage(manifest),
                "contract_batch_manifest_path": str((_pipeline_workspace(manifest) / CONTRACT_BATCH_MANIFEST_NAME).resolve())
                if _pipeline_workspace(manifest)
                else "",
                "blocking_missing_inputs": [],
            }
        result.setdefault("repair_rule_id", "runtime_contract_batch_preflight_v2")
        return result
    contract_manifest_path = _write_runtime_contract_batch_manifest(
        manifest,
        issue_kind=issue_kind,
        resume_strategy="rollback_upstream_stage",
        status=batch_status,
    )
    rollback_stage_id = _contract_rollback_stage(manifest)
    return {
        "handled": True,
        "repair_rule_id": "runtime_contract_batch_preflight_v2",
        "resume_strategy": "rollback_upstream_stage",
        "resume_issue_kind": issue_kind,
        "retry_stage_id": rollback_stage_id,
        "rollback_stage_id": rollback_stage_id,
        "contract_batch_manifest_path": contract_manifest_path,
        "blocking_missing_inputs": [],
    }


def _read_csv_dicts(path: Path, *, limit: int = 40) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            for index, row in enumerate(reader):
                if index >= limit:
                    break
                rows.append({str(key or ""): str(value or "") for key, value in dict(row).items()})
    except Exception:
        return []
    return rows


def _format_ops_table_value(key: str, value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        number = float(text)
    except Exception:
        return text.replace("|", "\\|")
    integer_fields = {
        "展示排序",
        "sample_size",
        "impressions",
        "clicks",
        "registrations",
        "activations",
        "paid_users",
    }
    if key in integer_fields:
        return f"{number:,.0f}"
    ratio_fields = {
        "retention_d7",
        "点击率",
        "点击到注册率",
        "注册到激活率",
        "激活到付费率",
        "点击到付费率",
    }
    if key in ratio_fields:
        return f"{number * 100:.2f}%"
    if key in {"roi", "cac", "nps"}:
        return f"{number:.2f}"
    if abs(number) >= 100:
        return f"{number:,.0f}"
    return f"{number:.2f}"


def _as_float(value: Any) -> float | None:
    text = str(value or "").strip().replace(",", "")
    if not text:
        return None
    try:
        return float(text)
    except Exception:
        return None


def _parse_period_month(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m", "%Y/%m", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(text[:10], fmt).strftime("%Y-%m")
        except Exception:
            continue
    if len(text) >= 7 and text[4:5] in {"-", "/"}:
        return text[:7].replace("/", "-")
    return ""


def _load_source_dataset_rows(path: Path, *, max_rows: int = 20000) -> tuple[list[str], list[dict[str, str]]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = [str(field or "") for field in (reader.fieldnames or [])]
            rows: list[dict[str, str]] = []
            for index, row in enumerate(reader):
                if index >= max_rows:
                    break
                rows.append({str(key or ""): str(value or "") for key, value in dict(row).items()})
            return fields, rows
    except Exception:
        return [], []


def _detect_numeric_columns(fields: list[str], rows: list[dict[str, str]]) -> list[str]:
    numeric: list[str] = []
    for field in fields:
        values = [row.get(field, "") for row in rows[:500]]
        present = [value for value in values if str(value or "").strip()]
        if not present:
            continue
        parsed = [_as_float(value) for value in present]
        parseable = [value for value in parsed if value is not None]
        if len(parseable) >= max(3, int(len(present) * 0.6)):
            numeric.append(field)
    preferred = [
        "\u8ba2\u5355\u6570",  # orders
        "\u6d3b\u8dc3\u7528\u6237",  # active users
        "\u65b0\u589e\u7528\u6237",  # new users
        "\u7559\u5b58\u7528\u6237",  # retained users
        "revenue",
        "orders",
        "paid_users",
        "active_users",
        "new_users",
        "retained_users",
        "\u7559\u5b58\u7387",  # retention rate
        "\u8f6c\u5316\u7387",  # conversion rate
        "retention_rate",
        "conversion_rate",
        "roi",
        "cac",
    ]
    return sorted(numeric, key=lambda item: (preferred.index(item) if item in preferred else 999, fields.index(item)))


def _detect_dimension_columns(fields: list[str], rows: list[dict[str, str]], numeric_cols: set[str]) -> list[str]:
    preferred = [
        "\u6e20\u9053",  # channel
        "\u6d41\u91cf\u6765\u6e90",  # traffic source
        "\u6d3b\u52a8",  # campaign/activity
        "\u5185\u5bb9\u4e3b\u9898",  # content theme
        "\u7528\u6237\u5206\u7fa4",  # user segment
        "\u57ce\u5e02\u5c42\u7ea7",  # city tier
        "\u4ea7\u54c1\u6a21\u5757",  # product module
        "channel",
        "traffic_source",
        "campaign",
        "activity",
        "content_theme",
        "content_category",
        "user_segment",
        "city_tier",
        "product_module",
    ]
    date_like = {"date", "\u65e5\u671f", "day", "dt"}
    candidates: list[tuple[int, str]] = []
    for field in fields:
        if field in numeric_cols:
            continue
        lowered = field.lower()
        if lowered in date_like or field in date_like:
            continue
        values = [str(row.get(field, "")).strip() for row in rows[:1000] if str(row.get(field, "")).strip()]
        if not values:
            continue
        unique_count = len(set(values))
        if 2 <= unique_count <= max(40, int(len(values) * 0.75)):
            priority = preferred.index(field) if field in preferred else 500 + unique_count
            candidates.append((priority, field))
    return [field for _, field in sorted(candidates, key=lambda item: (item[0], fields.index(item[1])))]


def _detect_date_column(fields: list[str], rows: list[dict[str, str]]) -> str:
    preferred = ["\u65e5\u671f", "date", "day", "dt", "event_date", "created_at"]
    for field in preferred:
        if field in fields:
            return field
    for field in fields:
        sample = [row.get(field, "") for row in rows[:100]]
        parsed = [_parse_period_month(value) for value in sample]
        if sum(1 for value in parsed if value) >= 3:
            return field
    return ""


def _metric_aggregation_kind(metric: str, values: list[float]) -> str:
    lowered = metric.lower()
    if any(token in lowered for token in ["rate", "ratio", "conversion", "retention", "roi", "cac"]):
        return "mean"
    if metric in {"\u7559\u5b58\u7387", "\u8f6c\u5316\u7387"}:
        return "mean"
    if values and max(abs(value) for value in values) <= 1.5 and any(token in metric for token in ["\u7387", "\u6bd4"]):
        return "mean"
    return "sum"


def _build_ops_cross_dimension_tables_from_source(source_dataset: Path) -> dict[str, Any]:
    fields, rows = _load_source_dataset_rows(source_dataset)
    if not fields or not rows:
        return {"tables": [], "blocking_missing_inputs": ["source_dataset.csv:readable_rows"]}
    numeric_cols = _detect_numeric_columns(fields, rows)
    if not numeric_cols:
        return {"tables": [], "blocking_missing_inputs": ["source_dataset.csv:numeric_metrics"]}
    dimension_cols = _detect_dimension_columns(fields, rows, set(numeric_cols))
    if len(dimension_cols) < 2:
        return {"tables": [], "blocking_missing_inputs": ["source_dataset.csv:cross_dimensions"]}

    date_col = _detect_date_column(fields, rows)
    virtual_month = "__period_month"
    enriched_rows = [dict(row) for row in rows]
    if date_col:
        for row in enriched_rows:
            row[virtual_month] = _parse_period_month(row.get(date_col, ""))

    pair_candidates: list[tuple[str, str]] = []
    for left_index, left in enumerate(dimension_cols[:6]):
        for right in dimension_cols[left_index + 1 : 6]:
            pair_candidates.append((left, right))
    if date_col:
        for dim in dimension_cols[:6]:
            pair_candidates.append((virtual_month, dim))

    primary_metric = numeric_cols[0]
    metric_values: dict[str, list[float]] = {metric: [] for metric in numeric_cols[:8]}
    for row in rows[:2000]:
        for metric in metric_values:
            value = _as_float(row.get(metric))
            if value is not None:
                metric_values[metric].append(value)
    metric_kinds = {metric: _metric_aggregation_kind(metric, values) for metric, values in metric_values.items()}

    tables: list[dict[str, Any]] = []
    seen_pairs: set[tuple[str, str]] = set()
    for left, right in pair_candidates:
        if len(tables) >= 8:
            break
        if (left, right) in seen_pairs:
            continue
        seen_pairs.add((left, right))
        groups: dict[tuple[str, str], dict[str, Any]] = {}
        for row in enriched_rows:
            left_value = str(row.get(left, "")).strip()
            right_value = str(row.get(right, "")).strip()
            if not left_value or not right_value:
                continue
            key = (left_value, right_value)
            bucket = groups.setdefault(key, {"row_count": 0, "_metric_values": {metric: [] for metric in metric_values}})
            bucket["row_count"] += 1
            for metric in metric_values:
                value = _as_float(row.get(metric))
                if value is not None:
                    bucket["_metric_values"][metric].append(value)
        if not groups:
            continue
        output_rows: list[dict[str, Any]] = []
        for (left_value, right_value), bucket in groups.items():
            output_row: dict[str, Any] = {
                (date_col if left == virtual_month else left): left_value,
                (date_col if right == virtual_month else right): right_value,
                "row_count": bucket["row_count"],
            }
            for metric, values in bucket["_metric_values"].items():
                if not values:
                    continue
                output_row[metric] = sum(values) / len(values) if metric_kinds.get(metric) == "mean" else sum(values)
            output_rows.append(output_row)
        output_rows.sort(key=lambda item: float(item.get(primary_metric) or item.get("row_count") or 0), reverse=True)
        dimensions = [date_col if left == virtual_month else left, date_col if right == virtual_month else right]
        tables.append(
            {
                "table_id": f"deterministic_cross_dimension_{len(tables) + 1:02d}",
                "title": " x ".join(dimensions) + " priority table",
                "dimensions": dimensions,
                "primary_metric": primary_metric,
                "metric_aggregation": metric_kinds,
                "source": "deterministic_resume_repair_from_source_dataset",
                "row_count": min(12, len(output_rows)),
                "rows": output_rows[:12],
            }
        )
    return {
        "version": "internet_ops_cross_dimension_priority_tables.v1",
        "source": "deterministic_resume_repair_from_source_dataset",
        "source_dataset": str(source_dataset.resolve()),
        "dimension_candidates": dimension_cols,
        "numeric_metric_candidates": numeric_cols,
        "tables": tables,
        "blocking_missing_inputs": [] if len(tables) >= 4 else ["source_dataset.csv:at_least_four_cross_dimension_tables"],
    }


def _patch_ops_inventory_with_cross_tables(workspace: Path, tables: list[dict[str, Any]]) -> list[str]:
    repaired_files: list[str] = []
    inventory_json = workspace / "01_ops_inventory.json"
    if inventory_json.exists():
        try:
            payload = json.loads(inventory_json.read_text(encoding="utf-8"))
            payload["cross_dimension_tables"] = tables
            inventory_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            repaired_files.append(str(inventory_json.resolve()))
        except Exception:
            pass
    inventory_md = workspace / "01_ops_inventory.md"
    if inventory_md.exists():
        try:
            text = inventory_md.read_text(encoding="utf-8", errors="ignore")
            lines = [
                line if not line.lower().startswith("- cross-dimension tables:") else f"- cross-dimension tables: {len(tables)}"
                for line in text.splitlines()
            ]
            inventory_md.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
            repaired_files.append(str(inventory_md.resolve()))
        except Exception:
            pass
    return repaired_files


def _write_csv_rows(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(str(key))
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames or ["value"])
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})
    return path


def _repair_internet_ops_inventory_support_contracts(
    workspace: Path,
    source_dataset: Path,
    *,
    cross_tables: list[dict[str, Any]],
) -> list[str]:
    fields, rows = _load_source_dataset_rows(source_dataset)
    numeric_cols = _detect_numeric_columns(fields, rows)
    dimension_cols = _detect_dimension_columns(fields, rows, set(numeric_cols))
    date_col = _detect_date_column(fields, rows)
    primary_metric = numeric_cols[0] if numeric_cols else "row_count"
    repaired: list[str] = []

    if date_col and rows:
        grouped: dict[str, dict[str, Any]] = {}
        for row in rows:
            period = _parse_period_month(row.get(date_col, ""))
            if not period:
                continue
            bucket = grouped.setdefault(period, {"period": period, "row_count": 0, primary_metric: 0.0})
            bucket["row_count"] += 1
            value = _as_float(row.get(primary_metric))
            if value is not None:
                bucket[primary_metric] = float(bucket.get(primary_metric) or 0) + value
        ordered = sorted(grouped.values(), key=lambda item: str(item.get("period") or ""))
        previous: float | None = None
        time_rows: list[dict[str, Any]] = []
        for item in ordered[-12:]:
            current = float(item.get(primary_metric) or 0)
            delta = "" if previous is None else current - previous
            change_rate = "" if previous in {None, 0} else (current - float(previous)) / abs(float(previous))
            time_rows.append(
                {
                    "period": item.get("period"),
                    "row_count": item.get("row_count"),
                    "primary_metric": primary_metric,
                    "primary_metric_value": round(current, 6),
                    "period_delta": "" if delta == "" else round(float(delta), 6),
                    "period_change_rate": "" if change_rate == "" else round(float(change_rate), 6),
                    "source": "deterministic_resume_repair_from_source_dataset",
                }
            )
            previous = current
        if time_rows:
            repaired.append(str(_write_csv_rows(workspace / "ops_time_window_summary.csv", time_rows).resolve()))

    action_objects: list[dict[str, Any]] = []
    for table in cross_tables[:4]:
        for row in list(table.get("rows") or [])[:3]:
            dimensions = list(table.get("dimensions") or [])
            object_name = " / ".join(str(row.get(dim) or "").strip() for dim in dimensions if str(row.get(dim) or "").strip())
            if not object_name:
                continue
            action_objects.append(
                {
                    "object_name": object_name,
                    "object_scope": " x ".join(dimensions),
                    "evidence_metric": table.get("primary_metric") or primary_metric,
                    "evidence_value": row.get(str(table.get("primary_metric") or primary_metric), row.get(primary_metric, "")),
                    "owner_role": "operation_owner",
                    "recommended_action": "prioritize review and allocate next-cycle experiment resources",
                    "success_metric": table.get("primary_metric") or primary_metric,
                    "check_point": "next weekly operating review",
                    "evidence_source": "ops_cross_dimension_priority_tables.json",
                }
            )
    current_week_actions = action_objects[:8]
    action_grounding = {
        "source": "deterministic_resume_repair_from_source_dataset",
        "priority_object_pools": {
            "cross_dimension_priority_pool": current_week_actions,
            "dimension_candidates": dimension_cols[:8],
            "metric_candidates": numeric_cols[:8],
        },
        "current_week_actions": current_week_actions,
    }
    repaired.append(str(_write_json(workspace / "ops_action_grounding.json", action_grounding).resolve()))

    day_slots: list[dict[str, Any]] = []
    owner_rows: list[dict[str, Any]] = []
    for index, action in enumerate((current_week_actions or action_objects)[:7], start=1):
        slot = {
            "day": f"Day {index}",
            "owner_role": action.get("owner_role") or "operation_owner",
            "object_name": action.get("object_name") or f"priority object {index}",
            "action": action.get("recommended_action") or "review and prioritize",
            "success_metric": action.get("success_metric") or primary_metric,
            "check_point": action.get("check_point") or "next weekly operating review",
            "evidence_source": action.get("evidence_source") or "source_dataset.csv",
        }
        day_slots.append(slot)
        owner_rows.append(slot)
    if not day_slots:
        day_slots = [
            {
                "day": "Day 1",
                "owner_role": "operation_owner",
                "object_name": "dataset operating baseline",
                "action": "review available dimensions and define the next recovery run",
                "success_metric": primary_metric,
                "check_point": "next weekly operating review",
                "evidence_source": "source_dataset.csv",
            }
        ]
        owner_rows = list(day_slots)
    repaired.append(
        str(
            _write_json(
                workspace / "ops_daily_action_plan.json",
                {"source": "deterministic_resume_repair_from_source_dataset", "day_slots": day_slots},
            ).resolve()
        )
    )
    repaired.append(str(_write_csv_rows(workspace / "ops_daily_action_owner_matrix.csv", owner_rows).resolve()))

    diagnosis_cards = [
        {
            "metric_id": metric,
            "metric_name": metric,
            "status": "usable_from_source_dataset",
            "business_use": "ranking and monitoring within the recovered runtime workspace",
            "evidence_source": "source_dataset.csv",
        }
        for metric in numeric_cols[:6]
    ] or [
        {
            "metric_id": "row_count",
            "metric_name": "row_count",
            "status": "diagnostic_only",
            "business_use": "row-count evidence is available, but numeric operating metrics were not detected",
            "evidence_source": "source_dataset.csv",
        }
    ]
    repaired.append(
        str(
            _write_json(
                workspace / "ops_derived_metric_diagnosis_cards.json",
                {"source": "deterministic_resume_repair_from_source_dataset", "cards": diagnosis_cards},
            ).resolve()
        )
    )
    return repaired


def _repair_internet_ops_cross_dimension_tables(manifest: dict[str, Any]) -> dict[str, Any]:
    workspace = _pipeline_workspace(manifest)
    if not workspace:
        return {
            "handled": True,
            "resume_strategy": "blocked_missing_inputs",
            "blocking_missing_inputs": ["pipeline_workspace"],
        }
    source_dataset = workspace / "source_dataset.csv"
    if not source_dataset.exists():
        return {
            "handled": True,
            "resume_strategy": "blocked_missing_inputs",
            "blocking_missing_inputs": ["source_dataset.csv"],
        }
    cross_payload = _build_ops_cross_dimension_tables_from_source(source_dataset)
    tables = list(cross_payload.get("tables") or [])
    if len(tables) < 4:
        return {
            "handled": True,
            "resume_strategy": "blocked_missing_inputs",
            "resume_issue_kind": "cannot_rebuild_internet_ops_cross_dimension_tables",
            "blocking_missing_inputs": list(cross_payload.get("blocking_missing_inputs") or ["source_dataset.csv:cross_dimension_tables"]),
        }
    cross_path = workspace / "ops_cross_dimension_priority_tables.json"
    cross_path.write_text(json.dumps(cross_payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    support_files = _repair_internet_ops_inventory_support_contracts(workspace, source_dataset, cross_tables=tables)
    repaired_files = [str(cross_path.resolve()), *support_files, *_patch_ops_inventory_with_cross_tables(workspace, tables)]
    log = {
        "pipeline_job_id": manifest.get("pipeline_job_id"),
        "pipeline_type": manifest.get("pipeline_type"),
        "resume_strategy": "deterministic_repair_then_continue",
        "gate_failure_kind": "internet_ops_missing_cross_dimension_tables",
        "evidence_files": [str(source_dataset.resolve())],
        "repaired_files": repaired_files,
        "retry_stage_id": "ops_inventory",
        "table_count": len(tables),
        "created_at": _now_iso(),
    }
    log_path = _write_json(workspace / "pipeline_resume_cross_dimension_repair_log.json", log)
    return {
        "handled": True,
        "resume_strategy": "deterministic_repair_then_continue",
        "resume_issue_kind": "missing_internet_ops_cross_dimension_tables",
        "retry_stage_id": "ops_inventory",
        "repair_log_path": str(log_path.resolve()),
        "repaired_files": repaired_files,
        "blocking_missing_inputs": [],
    }


def _preflight_internet_ops_cross_dimension_tables(manifest: dict[str, Any], *, repair: bool = False) -> dict[str, Any]:
    pipeline_type = str(manifest.get("pipeline_type") or "")
    if pipeline_type != "internet_ops_long_cli_pipeline":
        return {}
    error_text = _pipeline_error_text(manifest)
    lowered = error_text.lower()
    inventory_contract_tokens = [
        "cross_dimension_tables",
        "cross-dimension",
        "time_window_focus",
        "current_week_actions",
        "daily_action_summary",
        "owner_schedule_summary",
        "derived_metric_diagnosis_summary",
    ]
    matches_gate = any(token in lowered for token in inventory_contract_tokens)
    if "ops_inventory" not in lowered or not matches_gate:
        return {}
    workspace = _pipeline_workspace(manifest)
    source_dataset = workspace / "source_dataset.csv" if workspace else None
    if not source_dataset or not source_dataset.exists():
        return {
            "handled": True,
            "repair_rule_id": "internet_ops_cross_dimension_tables",
            "resume_issue_kind": "missing_internet_ops_cross_dimension_tables",
            "resume_strategy": "blocked_missing_inputs",
            "retry_stage_id": "ops_inventory",
            "blocking_missing_inputs": ["source_dataset.csv"],
        }
    if repair:
        result = _repair_internet_ops_cross_dimension_tables(manifest)
    else:
        result = {
            "handled": True,
            "resume_strategy": "deterministic_repair_then_continue",
            "resume_issue_kind": "missing_internet_ops_cross_dimension_tables",
            "retry_stage_id": "ops_inventory",
            "repair_log_path": str((workspace / "pipeline_resume_cross_dimension_repair_log.json").resolve()),
            "blocking_missing_inputs": [],
        }
    result.setdefault("repair_rule_id", "internet_ops_cross_dimension_tables")
    return result


def _ops_top12_table_markdown(csv_path: Path) -> str:
    rows = _read_csv_dicts(csv_path, limit=12)
    if not rows:
        return ""
    columns = [
        ("展示排序", "排序"),
        ("入选原因", "入选原因"),
        ("channel", "渠道"),
        ("traffic_source", "流量来源"),
        ("sample_size", "样本数"),
        ("impressions", "曝光"),
        ("clicks", "点击"),
        ("registrations", "注册"),
        ("activations", "激活"),
        ("paid_users", "付费用户"),
        ("revenue", "收入"),
        ("operating_cost", "运营成本"),
        ("contribution_margin", "贡献毛利"),
        ("roi", "ROI"),
        ("cac", "CAC"),
        ("点击率", "点击率"),
        ("点击到注册率", "点击-注册率"),
        ("注册到激活率", "注册-激活率"),
        ("激活到付费率", "激活-付费率"),
        ("点击到付费率", "点击-付费率"),
    ]
    header = "| " + " | ".join(label for _, label in columns) + " |"
    divider = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = [
        "| " + " | ".join(_format_ops_table_value(key, row.get(key, "")) for key, _ in columns) + " |"
        for row in rows
    ]
    return "\n".join([header, divider, *body])


def _insert_section_once(markdown: str, section: str) -> tuple[str, bool]:
    if INTERNET_OPS_TOP12_TABLE_TITLE in markdown:
        return markdown, False
    figure_markers = [
        INTERNET_OPS_TOP12_TABLE_CSV.replace(".csv", ".png"),
        "Top12 渠道 × 流量来源 AARRR 差异图组",
    ]
    for marker in figure_markers:
        index = markdown.find(marker)
        if index < 0:
            continue
        line_end = markdown.find("\n", index)
        if line_end < 0:
            return markdown.rstrip() + "\n\n" + section + "\n", True
        return markdown[: line_end + 1].rstrip() + "\n\n" + section + "\n\n" + markdown[line_end + 1 :].lstrip(), True
    return markdown.rstrip() + "\n\n" + section + "\n", True


def _repair_internet_ops_top12_combo_table(manifest: dict[str, Any]) -> dict[str, Any]:
    workspace = _pipeline_workspace(manifest)
    pipeline_job_id = str(manifest.get("pipeline_job_id") or "")
    if not workspace:
        return {
            "handled": True,
            "resume_strategy": "blocked_missing_inputs",
            "blocking_missing_inputs": ["pipeline_workspace"],
        }
    csv_path = workspace / "source_visual_assets" / INTERNET_OPS_TOP12_TABLE_CSV
    if not csv_path.exists():
        return {
            "handled": True,
            "resume_strategy": "blocked_missing_inputs",
            "blocking_missing_inputs": [f"source_visual_assets/{INTERNET_OPS_TOP12_TABLE_CSV}"],
        }
    table_md = _ops_top12_table_markdown(csv_path)
    if not table_md:
        return {
            "handled": True,
            "resume_strategy": "blocked_missing_inputs",
            "blocking_missing_inputs": [f"{INTERNET_OPS_TOP12_TABLE_CSV}:readable_rows"],
        }
    section = "\n".join(
        [
            f"## {INTERNET_OPS_TOP12_TABLE_TITLE}",
            "",
            "这张配表展开上方 Top12 渠道 × 流量来源 AARRR 差异图组的底层组合。续跑修复只使用已落盘 CSV，不新增指标、不改确定性数字。",
            "",
            table_md,
        ]
    )
    repaired_files: list[str] = []
    for file_name in ["05_report.md", "05_report_with_tables.md"]:
        target = workspace / file_name
        if not target.exists():
            continue
        text = target.read_text(encoding="utf-8", errors="ignore")
        updated, changed = _insert_section_once(text, section)
        if changed:
            target.write_text(updated, encoding="utf-8")
            repaired_files.append(str(target.resolve()))
    if not repaired_files:
        repaired_files = [str((workspace / "05_report.md").resolve())]
    log = {
        "pipeline_job_id": pipeline_job_id,
        "pipeline_type": manifest.get("pipeline_type"),
        "resume_strategy": "deterministic_repair_then_continue",
        "gate_failure_kind": "internet_ops_missing_top12_combo_funnel_table",
        "evidence_files": [str(csv_path.resolve())],
        "repaired_files": repaired_files,
        "retry_stage_id": "ops_html_css_package",
        "created_at": _now_iso(),
    }
    log_path = _write_json(workspace / "pipeline_resume_repair_log.json", log)
    return {
        "handled": True,
        "resume_strategy": "deterministic_repair_then_continue",
        "retry_stage_id": "ops_html_css_package",
        "repair_log_path": str(log_path.resolve()),
        "repaired_files": repaired_files,
        "blocking_missing_inputs": [],
    }


def _preflight_internet_ops_top12_combo_table(manifest: dict[str, Any], *, repair: bool = False) -> dict[str, Any]:
    pipeline_type = str(manifest.get("pipeline_type") or "")
    error_text = _pipeline_error_text(manifest)
    lowered = error_text.lower()
    matches_top12_gate = INTERNET_OPS_TOP12_TABLE_TITLE in error_text or (
        "top12" in lowered
        and any(token in lowered for token in ["combo", "funnel", "aarrr", "object_decision", "漏斗", "配表"])
    )
    if (
        pipeline_type != "internet_ops_long_cli_pipeline"
        or not matches_top12_gate
        or "missing" not in lowered
    ):
        return {}
    workspace = _pipeline_workspace(manifest)
    csv_path = workspace / "source_visual_assets" / INTERNET_OPS_TOP12_TABLE_CSV if workspace else None
    if csv_path and csv_path.exists():
        if repair:
            result = _repair_internet_ops_top12_combo_table(manifest)
        else:
            result = {
                "handled": True,
                "resume_strategy": "deterministic_repair_then_continue",
                "retry_stage_id": "ops_html_css_package",
                "repair_log_path": str((workspace / "pipeline_resume_repair_log.json").resolve()),
                "blocking_missing_inputs": [],
            }
        result.setdefault("repair_rule_id", "internet_ops_top12_combo_table")
        result.setdefault("resume_issue_kind", "missing_reader_required_top12_combo_table")
        return result
    return {
        "handled": True,
        "repair_rule_id": "internet_ops_top12_combo_table",
        "resume_issue_kind": "missing_reader_required_top12_combo_table",
        "resume_strategy": "blocked_missing_inputs",
        "retry_stage_id": "ops_chart_insights",
        "blocking_missing_inputs": [f"source_visual_assets/{INTERNET_OPS_TOP12_TABLE_CSV}"],
    }


PIPELINE_REPAIR_REGISTRY: tuple[dict[str, Any], ...] = (
    {
        "rule_id": "internet_ops_cross_dimension_tables",
        "pipeline_types": {"internet_ops_long_cli_pipeline"},
        "handler": _preflight_internet_ops_cross_dimension_tables,
    },
    {
        "rule_id": "internet_ops_top12_combo_table",
        "pipeline_types": {"internet_ops_long_cli_pipeline"},
        "handler": _preflight_internet_ops_top12_combo_table,
    },
)


def _apply_pipeline_repair_registry(manifest: dict[str, Any], *, repair: bool) -> dict[str, Any]:
    pipeline_type = str(manifest.get("pipeline_type") or "")
    for rule in PIPELINE_REPAIR_REGISTRY:
        pipeline_types = rule.get("pipeline_types")
        if pipeline_types and pipeline_type not in pipeline_types:
            continue
        handler = rule.get("handler")
        if not callable(handler):
            continue
        try:
            result = handler(manifest, repair=repair)
        except Exception as exc:
            return {
                "handled": True,
                "repair_rule_id": str(rule.get("rule_id") or ""),
                "resume_strategy": "blocked_missing_inputs",
                "blocking_missing_inputs": [f"repair_rule_error:{exc}"],
            }
        if result:
            result.setdefault("repair_rule_id", str(rule.get("rule_id") or ""))
            return result
    return {}


def _common_missing_dependency_preflight(manifest: dict[str, Any]) -> dict[str, Any]:
    """Infer a safe rollback stage for common missing-artifact failures.

    This does not fabricate assets. It only points retry at the closest upstream
    stage that can legitimately rebuild the missing reader/runtime artifact.
    """
    error_text = _pipeline_error_text(manifest)
    lowered = error_text.lower()
    if not any(token in lowered for token in ["missing", "not found", "no such file", "cannot find"]):
        return {}
    workspace = _pipeline_workspace(manifest)
    source_missing: list[str] = []
    if "source_dataset.csv" in lowered and (not workspace or not (workspace / "source_dataset.csv").exists()):
        source_missing.append("source_dataset.csv")
    if "pipeline_context.json" in lowered and (not workspace or not (workspace / "pipeline_context.json").exists()):
        source_missing.append("pipeline_context.json")
    if source_missing:
        return {
            "handled": True,
            "resume_strategy": "blocked_missing_inputs",
            "resume_issue_kind": "missing_unrecoverable_workspace_inputs",
            "blocking_missing_inputs": source_missing,
        }

    retry_stage_id = ""
    issue_kind = "missing_runtime_artifact"
    inferred_missing_inputs: list[str] = []
    if any(token in lowered for token in ["05_report.md", "05_report_with_tables.md", "report markdown"]):
        retry_stage_id = _stage_id_containing(manifest, "report_assembly")
        issue_kind = "missing_report_markdown"
        inferred_missing_inputs = ["05_report.md"]
    elif any(token in lowered for token in ["05a_metric_chart_plan.json", "metric_chart_plan"]):
        retry_stage_id = _first_existing_stage(manifest, ["metric_chart_planning"])
        issue_kind = "missing_metric_chart_plan"
        inferred_missing_inputs = ["05a_metric_chart_plan.json"]
    elif any(token in lowered for token in ["05b_metric_chart_render_log.json", "metric_chart_render"]):
        retry_stage_id = _first_existing_stage(manifest, ["metric_chart_render", "metric_chart_planning"])
        issue_kind = "missing_metric_chart_render"
        inferred_missing_inputs = ["05b_metric_chart_render_log.json"]
    elif any(token in lowered for token in ["chart_insights.json", "chart insights"]):
        retry_stage_id = _stage_id_containing(manifest, "chart_insights")
        issue_kind = "missing_chart_insights"
        inferred_missing_inputs = ["chart_insights.json"]
    elif any(token in lowered for token in ["06_report.html", "06_report.css", "html/css", "html_css"]):
        retry_stage_id = _stage_id_containing(manifest, "html_css_package")
        issue_kind = "missing_html_css_package"
        inferred_missing_inputs = ["06_report.html", "06_report.css"]
    elif any(token in lowered for token in ["08_review_notes.md", "review notes", "review"]):
        retry_stage_id = _stage_id_containing(manifest, "review")
        issue_kind = "missing_review_output"
        inferred_missing_inputs = ["08_review_notes.md"]
    elif any(token in lowered for token in ["07_report.pdf", "pdf"]):
        retry_stage_id = _stage_id_containing(manifest, "pdf_render")
        issue_kind = "missing_pdf_output"
        inferred_missing_inputs = ["07_report.pdf"]
    elif any(token in lowered for token in ["source_visual_assets_index.json", "source_visual_assets"]):
        retry_stage_id = _first_existing_stage(manifest, ["metric_chart_planning", "metric_chart_render"])
        issue_kind = "missing_visual_asset_index"
        inferred_missing_inputs = ["source_visual_assets_index.json"]

    if retry_stage_id:
        return {
            "handled": True,
            "resume_strategy": "rollback_upstream_stage",
            "resume_issue_kind": issue_kind,
            "retry_stage_id": retry_stage_id,
            "blocking_missing_inputs": [],
        }
    return {
        "handled": True,
        "resume_strategy": "blocked_missing_inputs",
        "resume_issue_kind": issue_kind if inferred_missing_inputs else "unknown_missing_dependency",
        "blocking_missing_inputs": inferred_missing_inputs or [error_text[:500] or "unknown_missing_dependency"],
    }


def _pipeline_resume_preflight(manifest: dict[str, Any], *, repair: bool = False) -> dict[str, Any]:
    pipeline_type = str(manifest.get("pipeline_type") or "")
    retry_stage_id = _pipeline_retry_stage(manifest)
    error_text = _pipeline_error_text(manifest)
    preflight: dict[str, Any] = {
        "resume_strategy": "retry_current_stage",
        "retry_stage_id": retry_stage_id,
        "pipeline_type": pipeline_type,
        "blocking_missing_inputs": [],
    }
    if _is_stale_codex_resume_error(error_text):
        preflight.update(
            {
                "handled": True,
                "resume_strategy": "stale_codex_session_fresh_retry",
                "resume_issue_kind": "stale_codex_runtime_session",
                "retry_stage_id": retry_stage_id,
                "stale_session_id": str(manifest.get("session_id") or ""),
                "blocking_missing_inputs": [],
            }
        )
        return preflight
    contract_result = _preflight_contract_batch_consistency(manifest, repair=repair)
    if contract_result:
        preflight.update(contract_result)
        return preflight
    reroute_result = _misrouted_completed_report_retrofit_preflight(manifest)
    if reroute_result:
        preflight.update(reroute_result)
        return preflight
    if _pipeline_is_completed_report_retrofit(manifest) and "generic visual band index is missing chart rows" in error_text.lower():
        preflight.update(
            {
                "handled": True,
                "resume_strategy": "retry_current_stage",
                "resume_issue_kind": "retrofit_visual_contract_relaxed_retry",
                "retry_stage_id": retry_stage_id,
                "blocking_missing_inputs": [],
            }
        )
        return preflight
    repair_result = _apply_pipeline_repair_registry(manifest, repair=repair)
    if repair_result:
        preflight.update(repair_result)
        return preflight
    common_result = _common_missing_dependency_preflight(manifest)
    if common_result:
        preflight.update(common_result)
    return preflight


def _completed_report_cli_bootstrap_status(report_id: str, *, fast: bool = False) -> dict[str, Any]:
    report_dir = _report_dir(report_id)
    route_hint = _lightweight_completed_report_route_hint(report_id)
    business_profile = str(route_hint.get("business_profile") or "")
    report_lens = str(route_hint.get("report_lens") or "")
    route_meta = _completed_report_route_meta(business_profile, report_lens)
    if fast:
        available: list[str] = []
        top_level_tabular = sorted(
            [
                path
                for path in report_dir.iterdir()
                if path.is_file() and path.suffix.lower() in {".csv", ".xlsx", ".xls", ".tsv"}
            ],
            key=lambda path: path.stat().st_mtime if path.exists() else 0.0,
            reverse=True,
        )
        top_level_text = sorted(
            [
                path
                for path in report_dir.iterdir()
                if path.is_file() and path.suffix.lower() in {".md", ".html", ".txt"}
            ],
            key=lambda path: path.stat().st_mtime if path.exists() else 0.0,
            reverse=True,
        )
        primary_csv_available = bool(top_level_tabular)
        analysis_csv_available = primary_csv_available
        usable_report_text_available = bool(top_level_text)
        metric_dir = report_dir / "outputs" / "metric_mining"
        r_dir = report_dir / "r-workflow"
        metric_mining_available = metric_dir.exists()
        r_workflow_available = r_dir.exists()
        auxiliary_assets_available = any(
            path.is_file()
            for path in report_dir.iterdir()
            if path.suffix.lower() in {".json", ".pdf", ".docx", ".pptx"}
        )
        for path in top_level_tabular[:12]:
            available.append(path.name)
        for path in top_level_text[:8]:
            available.append(path.name)
        if metric_mining_available:
            available.append("outputs/metric_mining/")
        if r_workflow_available:
            available.append("r-workflow/")
        missing: list[str] = []
        if not primary_csv_available:
            missing.append("original_source_dataset")
        if not (usable_report_text_available or analysis_csv_available or metric_mining_available or r_workflow_available):
            missing.append("reader_report_or_analysis_outputs")
        can_start = bool(
            primary_csv_available
            or analysis_csv_available
            or usable_report_text_available
            or metric_mining_available
            or r_workflow_available
            or auxiliary_assets_available
        )
        retrofit_mode = "full_retrofit" if primary_csv_available else "degraded_report_retrofit" if can_start else ""
        return {
            "can_start_generic_long_cli": can_start,
            "available_source_assets": available[:80],
            "missing_required_assets": missing,
            "primary_csv_available": primary_csv_available,
            "usable_report_text_available": usable_report_text_available,
            "analysis_csv_available": analysis_csv_available,
            "auxiliary_assets_available": auxiliary_assets_available,
            "retrofit_mode": retrofit_mode,
            "evidence_limited": can_start and not primary_csv_available,
            "probe_mode": "fast",
            "business_profile": business_profile,
            "report_lens": report_lens,
            "pipeline_label": route_meta.get("pipeline_label") or "",
            "resume_label": route_meta.get("resume_label") or "",
            "resume_strategy": route_meta.get("resume_strategy") or "",
            "specialized_pipeline_type": route_meta.get("specialized_pipeline_type") or "",
        }
    try:
        from app.services.report_service import _scan_retrofit_source_assets

        source_assets = _scan_retrofit_source_assets(report_dir, report_id)
    except Exception:
        source_assets = {}
    available: list[str] = []
    for item in list(source_assets.get("csv_candidates") or [])[:40]:
        rel = str(item.get("relative_path") or item.get("name") or "").strip()
        if rel:
            available.append(rel)
    for item in list(source_assets.get("text_assets") or [])[:20]:
        rel = str(item.get("relative_path") or item.get("name") or "").strip()
        if rel:
            available.append(rel)
    for item in list(source_assets.get("auxiliary_assets") or [])[:20]:
        rel = str(item.get("relative_path") or item.get("name") or "").strip()
        if rel:
            available.append(rel)
    if bool(source_assets.get("metric_mining_available")):
        available.append("outputs/metric_mining/")
    if bool(source_assets.get("r_workflow_available")):
        available.append("r-workflow/")
    missing = list(source_assets.get("missing_required_assets") or [])
    return {
        "can_start_generic_long_cli": bool(source_assets.get("can_retrofit_cli")),
        "available_source_assets": available[:80],
        "missing_required_assets": missing,
        "primary_csv_available": bool(source_assets.get("primary_csv_available")),
        "usable_report_text_available": bool(source_assets.get("usable_report_text_available")),
        "analysis_csv_available": bool(source_assets.get("analysis_csv_available")),
        "auxiliary_assets_available": bool(source_assets.get("auxiliary_assets_available")),
        "retrofit_mode": source_assets.get("retrofit_mode") or "",
        "evidence_limited": bool(source_assets.get("evidence_limited")),
        "probe_mode": "deep",
        "business_profile": business_profile,
        "report_lens": report_lens,
        "pipeline_label": route_meta.get("pipeline_label") or "",
        "resume_label": route_meta.get("resume_label") or "",
        "resume_strategy": route_meta.get("resume_strategy") or "",
        "specialized_pipeline_type": route_meta.get("specialized_pipeline_type") or "",
    }


def _pipeline_has_live_task_evidence(manifest: dict[str, Any]) -> bool:
    task_ids = [
        str(item or "").strip()
        for item in list(manifest.get("linked_codex_task_ids") or [])
        if str(item or "").strip()
    ]
    task_ids.extend(
        [
            str(manifest.get("current_run_task_id") or "").strip(),
            str(manifest.get("codex_run_task_id") or "").strip(),
        ]
    )
    for task_id in dict.fromkeys(task_ids):
        if not task_id:
            continue
        try:
            task = get_codex_run_task(task_id)
        except Exception:
            continue
        observation = _runtime_observation(
            kind="codex_run_task",
            status=str(task.get("status") or ""),
            updated_at=str(task.get("updated_at") or ""),
            started_at=str(task.get("created_at") or task.get("started_at") or ""),
        )
        if bool(observation.get("is_active")):
            return True
    return False


def _pipeline_runtime_observation(manifest: dict[str, Any]) -> dict[str, Any]:
    status = str(manifest.get("status") or "")
    live_evidence = _pipeline_has_live_task_evidence(manifest)
    observation = _runtime_observation(
        kind="pipeline",
        status=status,
        updated_at=str(manifest.get("updated_at") or ""),
        started_at=str(manifest.get("created_at") or manifest.get("started_at") or ""),
        live_evidence=live_evidence,
    )
    if status in ACTIVE_PROCESS_STATUSES and not live_evidence and not bool(observation.get("is_stale")):
        age = observation.get("heartbeat_age_seconds")
        no_live_limit = STALE_CANCELLING_SECONDS if status == "cancelling" else PIPELINE_NO_LIVE_EVIDENCE_STALE_SECONDS
        if isinstance(age, int) and age > no_live_limit:
            observed_status = _stale_status_for("pipeline", status)
            observation.update(
                {
                    "observed_status": observed_status,
                    "is_stale": True,
                    "is_active": False,
                    "stale_reason": f"pipeline_has_no_live_codex_task_evidence_{age}s_gt_{no_live_limit}s",
                    "reconciliation_reason": "no_live_pipeline_task_evidence",
                }
            )
    observation["live_evidence"] = live_evidence
    return observation


def _pipeline_process_item(manifest_path: Path, manifest: dict[str, Any], report_id: str, *, scope: str = "report") -> dict[str, Any]:
    status = str(manifest.get("status") or "")
    error = str(manifest.get("error") or "")
    observation = _pipeline_runtime_observation(manifest)
    live_evidence = bool(observation.get("live_evidence"))
    is_stale = bool(observation.get("is_stale"))
    observed_status = str(observation.get("observed_status") or status)
    item_status = observed_status if is_stale else status
    retry_stage_id = _pipeline_retry_stage(manifest)
    preflight = _pipeline_resume_preflight(manifest, repair=False) if status in PIPELINE_RESUMABLE_STATUSES or is_stale else {}
    effective_retry_stage_id = str(preflight.get("retry_stage_id") or retry_stage_id)
    strategy = str(preflight.get("resume_strategy") or "")
    context = manifest.get("context_payload") if isinstance(manifest.get("context_payload"), dict) else {}
    business_profile = str(preflight.get("target_business_profile") or context.get("business_profile") or "")
    report_lens = str(preflight.get("target_report_lens") or context.get("report_lens") or "")
    can_resume = (status in PIPELINE_RESUMABLE_STATUSES or is_stale) and bool(
        effective_retry_stage_id
        or strategy
        in {
            "blocked_missing_inputs",
            "rebuild_workspace_then_restart_pipeline",
            "regenerate_workspace_contracts_then_continue",
        }
    )
    resume_label = _pipeline_resume_label(status, error)
    if str(preflight.get("resume_strategy") or "") == "stale_codex_session_fresh_retry":
        resume_label = "清理旧 Codex 会话并续跑"
    elif str(preflight.get("resume_strategy") or "") == "deterministic_repair_then_continue":
        resume_label = "补齐缺失依赖并续跑"
    elif str(preflight.get("resume_strategy") or "") == "regenerate_workspace_contracts_then_continue":
        resume_label = "重建合同并续跑"
    elif str(preflight.get("resume_strategy") or "") == "rebuild_workspace_then_restart_pipeline":
        target_label = _specialized_pipeline_label(
            "generic_long_cli_pipeline",
            business_profile=str(preflight.get("target_business_profile") or business_profile),
            report_lens=str(preflight.get("target_report_lens") or report_lens),
        )
        if target_label == "投放智能链":
            resume_label = "重建投放 workspace 并重跑"
        elif target_label == "互联网运营智能链":
            resume_label = "重建互联网运营 workspace 并重跑"
        elif target_label == "采销智能链":
            resume_label = "重建采销 workspace 并重跑"
        else:
            resume_label = "重建 workspace 并重跑"
    elif str(preflight.get("resume_strategy") or "") == "rollback_upstream_stage":
        resume_label = "回滚上游阶段并续跑"
    elif str(preflight.get("resume_strategy") or "") == "blocked_missing_inputs":
        resume_label = "检查缺失依赖"
    if is_stale and not strategy:
        resume_label = "续跑停滞阶段"
    return _item(
        kind="pipeline",
        item_id=str(manifest.get("pipeline_job_id") or manifest_path.parent.name),
        report_id=report_id,
        label=_specialized_pipeline_label(str(manifest.get("pipeline_type") or ""), business_profile=business_profile, report_lens=report_lens),
        status=item_status,
        stage_id=str(manifest.get("current_stage_id") or effective_retry_stage_id),
        stage_title=str(manifest.get("current_stage_title") or effective_retry_stage_id),
        progress_percent=int(manifest.get("progress_percent") or 0),
        error=error,
        can_cancel=status in RUNNING_STATUSES and not is_stale,
        can_resume=can_resume,
        resume_label=resume_label,
        disabled_reason="" if can_resume else _pipeline_disabled_reason(item_status, effective_retry_stage_id),
        updated_at=str(manifest.get("updated_at") or ""),
        started_at=str(manifest.get("created_at") or manifest.get("started_at") or ""),
        scope=scope,
        meta={
            "pipeline_type": manifest.get("pipeline_type"),
            "retry_stage_id": effective_retry_stage_id,
            "rollback_stage_id": preflight.get("rollback_stage_id") or "",
            "resume_strategy": preflight.get("resume_strategy") or "retry_current_stage",
            "resume_issue_kind": preflight.get("resume_issue_kind") or "",
            "repair_rule_id": preflight.get("repair_rule_id") or "",
            "stale_session_id": preflight.get("stale_session_id") or "",
            "blocking_missing_inputs": list(preflight.get("blocking_missing_inputs") or []),
            "last_repair_log_path": preflight.get("repair_log_path") or "",
            "contract_batch_manifest_path": preflight.get("contract_batch_manifest_path") or "",
            "workspace_rebuild_path": preflight.get("workspace_rebuild_path") or "",
            "repaired_files": list(preflight.get("repaired_files") or []),
            "workspace_path": manifest.get("workspace_path") or "",
            "manifest_path": str(manifest_path),
            "live_evidence": live_evidence,
            "runtime_observed_status": observation.get("observed_status") or status,
            "runtime_stale_reason": observation.get("stale_reason") or "",
            "target_business_profile": preflight.get("target_business_profile") or "",
            "target_report_lens": preflight.get("target_report_lens") or "",
        },
    )


def _pipeline_manifest_time(manifest_path: Path, manifest: dict[str, Any]) -> float:
    parsed = _parse_datetime(str(manifest.get("updated_at") or manifest.get("created_at") or ""))
    if parsed is not None:
        return parsed.timestamp()
    try:
        return manifest_path.stat().st_mtime
    except Exception:
        return 0.0


def _retrofit_supersede_key(manifest: dict[str, Any]) -> str:
    if not _pipeline_is_completed_report_retrofit(manifest):
        return ""
    pipeline_type = str(manifest.get("pipeline_type") or "")
    context = manifest.get("context_payload") if isinstance(manifest.get("context_payload"), dict) else {}
    if pipeline_type == "media_campaign_cli_pipeline":
        return "media_campaign_cli_pipeline"
    preflight = _misrouted_completed_report_retrofit_preflight(manifest)
    business_profile = str(preflight.get("target_business_profile") or context.get("business_profile") or "")
    report_lens = str(preflight.get("target_report_lens") or context.get("report_lens") or "")
    return str(_completed_report_route_meta(business_profile, report_lens).get("specialized_pipeline_type") or pipeline_type)


def _filter_superseded_retrofit_manifests(
    entries: list[tuple[Path, dict[str, Any], str]],
) -> list[tuple[Path, dict[str, Any], str]]:
    annotated: list[tuple[Path, dict[str, Any], str, str, tuple[float, str]]] = []
    latest_by_key: dict[tuple[str, str], tuple[float, str]] = {}
    for manifest_path, manifest, report_id in entries:
        key = _retrofit_supersede_key(manifest)
        rank = (_pipeline_manifest_time(manifest_path, manifest), str(manifest.get("pipeline_job_id") or manifest_path.parent.name))
        annotated.append((manifest_path, manifest, report_id, key, rank))
        if not key:
            continue
        group_key = (str(report_id or ""), key)
        if group_key not in latest_by_key or rank > latest_by_key[group_key]:
            latest_by_key[group_key] = rank

    filtered: list[tuple[Path, dict[str, Any], str]] = []
    for manifest_path, manifest, report_id, key, rank in annotated:
        if not key:
            filtered.append((manifest_path, manifest, report_id))
            continue
        group_key = (str(report_id or ""), key)
        if rank == latest_by_key.get(group_key):
            filtered.append((manifest_path, manifest, report_id))
    return filtered


def _load_pipeline_items(report_id: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    report_dir = _report_dir(report_id)
    if not CODEX_PIPELINE_JOBS_DIR.exists():
        return items
    entries: list[tuple[Path, dict[str, Any], str]] = []
    for manifest_path in _pipeline_manifest_paths_for_report(report_id, report_dir):
        manifest = _read_json(manifest_path, {})
        if not isinstance(manifest, dict):
            continue
        linked_report_id = str(manifest.get("linked_report_id") or (manifest.get("context_payload") or {}).get("report_id") or "")
        workspace = str(manifest.get("workspace_path") or "")
        if linked_report_id and linked_report_id != report_id:
            continue
        if not linked_report_id and str(report_dir.resolve()) not in workspace:
            continue
        entries.append((manifest_path, manifest, report_id))
    for manifest_path, manifest, entry_report_id in _filter_superseded_retrofit_manifests(entries):
        items.append(_pipeline_process_item(manifest_path, manifest, entry_report_id))
    return items


def _load_report_task_items(report_id: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for path in TASK_DIR.glob("*.json"):
        task = _read_json(path, {})
        if not isinstance(task, dict):
            continue
        summary = task.get("result_summary") if isinstance(task.get("result_summary"), dict) else {}
        result = task.get("result") if isinstance(task.get("result"), dict) else {}
        if str(summary.get("report_id") or result.get("report_id") or "") != report_id:
            continue
        items.append(
            _item(
                kind="report_task",
                item_id=str(task.get("job_id") or path.stem),
                report_id=report_id,
                label="报告任务",
                status=str(task.get("status") or ""),
                stage_id=str(task.get("current_stage_id") or ""),
                stage_title=str(task.get("current_stage_title") or ""),
                progress_percent=int(task.get("progress_percent") or 0),
                error=str(task.get("error") or ""),
                disabled_reason="报告任务暂不支持从工作台重放；请使用 linked CLI pipeline 续跑。",
                updated_at=str(task.get("updated_at") or ""),
            )
        )
    return items


def _load_codex_task_items(report_id: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    report_dir = _report_dir(report_id)
    task_ids = _codex_task_ids_for_report_dir(report_dir)
    for task_id in task_ids:
        path = CODEX_RUNTIME_TASKS_DIR / f"{task_id}.json"
        task = _read_json(path, {})
        if not isinstance(task, dict):
            continue
        parent_report_id = str(task.get("parent_report_id") or "")
        if parent_report_id and parent_report_id != report_id:
            continue
        status = str(task.get("status") or "")
        items.append(
            _item(
                kind="codex_run_task",
                item_id=str(task.get("job_id") or path.stem),
                report_id=report_id,
                label="Codex runtime task",
                status=status,
                stage_id=str(task.get("current_stage_id") or ""),
                stage_title=str(task.get("current_stage_title") or ""),
                progress_percent=int(task.get("progress_percent") or 0),
                error=str(task.get("error") or ""),
                can_cancel=status in RUNNING_STATUSES,
                disabled_reason="单次 Codex task 不直接续跑；请重试所属 pipeline 或发送新的后续改造消息。",
                updated_at=str(task.get("updated_at") or ""),
            )
        )
    return items


def _load_agent_session_items(report_id: str, session_id: str = "") -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    session_root = _report_dir(report_id) / "codex_agent_sessions"
    if not session_root.exists():
        return items
    session_paths = sorted(
        session_root.glob("*/session.json"),
        key=lambda path: path.stat().st_mtime if path.exists() else 0.0,
        reverse=True,
    )
    bridge_by_workspace = {str(item.get("workspace_path") or ""): item for item in list_native_bridge_processes()}
    for session_path in session_paths:
        session = _read_json(session_path, {})
        if not isinstance(session, dict):
            continue
        session = _reconcile_agent_session_for_read(session)
        sid = str(session.get("session_id") or session_path.parent.name)
        if session_id and sid != session_id:
            continue
        if not session_id and _is_internal_agent_session(session):
            continue
        workspace = str(session.get("workspace_path") or "")
        bridge = bridge_by_workspace.get(workspace)
        bridge_running = bool(bridge and str(bridge.get("status") or "") == "running")
        turn = session.get("current_turn") if isinstance(session.get("current_turn"), dict) else {}
        turn_status = str(turn.get("status") or session.get("current_turn_status") or "")
        turn_progress = 100 if turn_status in TERMINAL_STATUSES else None
        if turn_status:
            items.append(
                _item(
                    kind="report_agent_turn",
                    item_id=sid,
                    report_id=report_id,
                    label="后续改造 Codex turn",
                    status=turn_status,
                    stage_id=str(turn.get("turn_id") or ""),
                    stage_title=str(turn.get("user_message") or "report-agent turn")[:80],
                    progress_percent=turn_progress,
                    error=str(turn.get("error") or session.get("native_protocol_error") or ""),
                    can_cancel=turn_status in RUNNING_STATUSES,
                    disabled_reason="继续修改请在左侧对话框发送新消息；运行中可发送引导。",
                    updated_at=str(session.get("updated_at") or ""),
                    meta={"session_id": sid, "native_turn_id": turn.get("native_turn_id"), "live_evidence": bridge_running},
                )
            )
        if bridge or str(session.get("mode") or "") == "native_app_server":
            items.append(
                _item(
                    kind="native_app_server",
                    item_id=sid,
                    report_id=report_id,
                    label="Codex app-server",
                    status=str((bridge or {}).get("status") or session.get("native_connection_status") or "idle"),
                    stage_id=str((bridge or {}).get("thread_id") or session.get("codex_thread_id") or ""),
                    stage_title="原生 Codex 会话",
                    progress_percent=None,
                    disabled_reason="app-server 随会话按需启动，无需手动续跑。",
                    updated_at=str(session.get("updated_at") or ""),
                    meta={"pid": (bridge or {}).get("pid"), "workspace_path": workspace, "live_evidence": bridge_running},
                )
            )
    return items


def list_runtime_processes(report_id: str, session_id: str = "") -> dict[str, Any]:
    _report_dir(report_id)
    items: list[dict[str, Any]] = []
    items.extend(_load_report_task_items(report_id))
    items.extend(_load_pipeline_items(report_id))
    items.extend(_load_codex_task_items(report_id))
    items.extend(_load_agent_session_items(report_id, session_id=session_id))
    if not any(item["kind"] == "pipeline" for item in items):
        bootstrap = _completed_report_cli_bootstrap_status(report_id, fast=True)
        can_start = bool(bootstrap.get("can_start_generic_long_cli"))
        bootstrap_label = str(bootstrap.get("pipeline_label") or "普通报告 CLI 长链")
        bootstrap_resume_label = str(bootstrap.get("resume_label") or "启动 CLI 长报告链")
        items.append(
            _item(
                kind="runtime_bootstrap",
                item_id=report_id,
                report_id=report_id,
                label=bootstrap_label,
                status="not_started",
                can_resume=can_start,
                resume_label=bootstrap_resume_label if can_start else "",
                disabled_reason="" if can_start else "报告目录缺少原始数据、分析表和可读报告文本，无法补建 CLI 长链。",
                meta={
                    "can_start_generic_long_cli": can_start,
                    "available_source_assets": list(bootstrap.get("available_source_assets") or []),
                    "missing_required_assets": list(bootstrap.get("missing_required_assets") or []),
                    "retrofit_mode": bootstrap.get("retrofit_mode") or "",
                    "evidence_limited": bool(bootstrap.get("evidence_limited")),
                    "primary_csv_available": bool(bootstrap.get("primary_csv_available")),
                    "usable_report_text_available": bool(bootstrap.get("usable_report_text_available")),
                    "analysis_csv_available": bool(bootstrap.get("analysis_csv_available")),
                    "auxiliary_assets_available": bool(bootstrap.get("auxiliary_assets_available")),
                    "business_profile": bootstrap.get("business_profile") or "",
                    "report_lens": bootstrap.get("report_lens") or "",
                    "resume_strategy": bootstrap.get("resume_strategy") or "",
                    "specialized_pipeline_type": bootstrap.get("specialized_pipeline_type") or "",
                },
            )
        )
    items.sort(key=lambda item: str(item.get("updated_at") or ""), reverse=True)
    return {"report_id": report_id, "processes": items}


def _iter_report_ids() -> list[str]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    return [
        path.name.removeprefix(REPORT_DIR_PREFIX)
        for path in REPORTS_DIR.glob(f"{REPORT_DIR_PREFIX}*")
        if path.is_dir()
    ]


def _recent_session_paths(limit: int = ACTIVE_SESSION_SCAN_LIMIT) -> list[Path]:
    session_paths: list[Path] = []
    scan_limit = max(1, min(int(limit or ACTIVE_SESSION_SCAN_LIMIT), ACTIVE_REPORT_SCAN_LIMIT))
    for report_dir in report_catalog_index_report_dirs(limit=scan_limit):
        session_root = report_dir / "codex_agent_sessions"
        if not session_root.is_dir():
            continue
        session_paths.extend(path for path in session_root.glob("*/session.json") if path.is_file())
    session_paths.sort(key=lambda path: path.stat().st_mtime if path.exists() else 0.0, reverse=True)
    return session_paths[: max(1, int(limit or ACTIVE_SESSION_SCAN_LIMIT))]


def _session_active_or_recent(session: dict[str, Any], *, recent_terminal_seconds: int) -> bool:
    turn = session.get("current_turn") if isinstance(session.get("current_turn"), dict) else {}
    current_status = str(turn.get("status") or session.get("current_turn_status") or "")
    native_status = str(session.get("native_connection_status") or "")
    updated_at = str(session.get("updated_at") or session.get("created_at") or "")
    if current_status in RUNNING_STATUSES:
        return True
    if native_status in RUNNING_STATUSES:
        return True
    age = _age_seconds(updated_at)
    return bool(age is not None and age <= recent_terminal_seconds)


def _is_internal_agent_session(session: dict[str, Any]) -> bool:
    try:
        from app.services.report_agent_session_service import (
            _is_internal_test_session,
            _is_low_value_failed_session,
        )

        return _is_internal_test_session(session) or _is_low_value_failed_session(session)
    except Exception:
        title = str(session.get("title") or "").strip().lower()
        return any(marker in title for marker in ("smoke", "retest"))


def _reconcile_agent_session_for_read(session: dict[str, Any]) -> dict[str, Any]:
    try:
        from app.services.report_agent_session_service import _reconcile_session_for_read

        return _reconcile_session_for_read(session)
    except Exception:
        return session


def _active_scope_includes(item: dict[str, Any], *, recent_terminal_seconds: int) -> bool:
    status = str(item.get("observed_status") or item.get("status") or "")
    age = item.get("age_seconds")
    heartbeat_age = (item.get("meta") or {}).get("heartbeat_age_seconds") if isinstance(item.get("meta"), dict) else None
    effective_age = heartbeat_age if isinstance(heartbeat_age, int) else age
    if bool(item.get("is_active")) or _is_active_status(status):
        return True
    if (bool(item.get("can_resume")) and (_is_actionable_status(status) or bool(item.get("is_stale")))) and (
        effective_age is None or (isinstance(effective_age, int) and effective_age <= RECENT_ACTIONABLE_SECONDS)
    ):
        return True
    if status in TERMINAL_STATUSES:
        if isinstance(age, int) and age <= recent_terminal_seconds:
            return True
    return False


def _active_scope_sort_key(item: dict[str, Any]) -> tuple[int, int, float]:
    status = str(item.get("observed_status") or item.get("status") or "")
    if bool(item.get("is_active")) or _is_active_status(status):
        priority = 0
    elif bool(item.get("is_stale")) and bool(item.get("can_resume")):
        priority = 1
    elif _is_actionable_status(status):
        priority = 2
    elif status in TERMINAL_STATUSES:
        priority = 3
    else:
        priority = 4
    kind_priority = {
        "report_agent_turn": 0,
        "pipeline": 1,
        "report_task": 2,
        "codex_run_task": 3,
        "native_app_server": 4,
        "runtime_bootstrap": 5,
    }.get(str(item.get("kind") or ""), 9)
    updated = _parse_datetime(str(item.get("updated_at") or item.get("started_at") or ""))
    updated_ts = updated.timestamp() if updated else 0.0
    return (priority, kind_priority, -updated_ts)


def _load_all_report_task_items() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for path in TASK_DIR.glob("*.json"):
        task = _read_json(path, {})
        if not isinstance(task, dict):
            continue
        summary = task.get("result_summary") if isinstance(task.get("result_summary"), dict) else {}
        result = task.get("result") if isinstance(task.get("result"), dict) else {}
        report_id = str(summary.get("report_id") or result.get("report_id") or "")
        if not report_id:
            continue
        items.append(
            _item(
                kind="report_task",
                item_id=str(task.get("job_id") or path.stem),
                report_id=report_id,
                label="报告任务",
                status=str(task.get("status") or ""),
                stage_id=str(task.get("current_stage_id") or ""),
                stage_title=str(task.get("current_stage_title") or ""),
                progress_percent=int(task.get("progress_percent") or 0),
                error=str(task.get("error") or ""),
                disabled_reason="报告任务不能直接重放；请使用 linked CLI pipeline 续跑。",
                updated_at=str(task.get("updated_at") or ""),
                started_at=str(task.get("created_at") or task.get("started_at") or ""),
                scope="active",
            )
        )
    return items


def _load_all_pipeline_items() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if not CODEX_PIPELINE_JOBS_DIR.exists():
        return items
    entries: list[tuple[Path, dict[str, Any], str]] = []
    for report_dir in report_catalog_index_report_dirs(limit=ACTIVE_REPORT_SCAN_LIMIT):
        report_id = _report_id_from_dir(report_dir)
        if not report_id:
            continue
        for manifest_path in _pipeline_manifest_paths_for_report(report_id, report_dir):
            manifest = _read_json(manifest_path, {})
            if not isinstance(manifest, dict):
                continue
            entries.append((manifest_path, manifest, report_id))
    for manifest_path, manifest, report_id in _filter_superseded_retrofit_manifests(entries):
        items.append(_pipeline_process_item(manifest_path, manifest, report_id, scope="active"))
    return items


def _load_all_codex_task_items() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    task_paths: list[Path] = []
    seen: set[str] = set()
    for report_dir in report_catalog_index_report_dirs(limit=ACTIVE_REPORT_SCAN_LIMIT):
        for task_id in _codex_task_ids_for_report_dir(report_dir):
            path = CODEX_RUNTIME_TASKS_DIR / f"{task_id}.json"
            key = str(path).lower()
            if key not in seen and path.is_file():
                seen.add(key)
                task_paths.append(path)
    for path in task_paths:
        task = _read_json(path, {})
        if not isinstance(task, dict):
            continue
        report_id = str(task.get("parent_report_id") or "")
        if not report_id:
            continue
        status = str(task.get("status") or "")
        items.append(
            _item(
                kind="codex_run_task",
                item_id=str(task.get("job_id") or path.stem),
                report_id=report_id,
                label="Codex runtime task",
                status=status,
                stage_id=str(task.get("current_stage_id") or ""),
                stage_title=str(task.get("current_stage_title") or ""),
                progress_percent=int(task.get("progress_percent") or 0),
                error=str(task.get("error") or ""),
                can_cancel=status in RUNNING_STATUSES,
                disabled_reason="单次 Codex task 不直接续跑；请重试所属 pipeline 或发送新的后续改造消息。",
                updated_at=str(task.get("updated_at") or ""),
                started_at=str(task.get("created_at") or task.get("started_at") or ""),
                scope="active",
            )
        )
    return items


def _load_all_agent_session_items() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    bridge_by_workspace = {str(item.get("workspace_path") or ""): item for item in list_native_bridge_processes()}
    for session_path in _recent_session_paths():
        session = _read_json(session_path, {})
        if not isinstance(session, dict):
            continue
        session = _reconcile_agent_session_for_read(session)
        if _is_internal_agent_session(session):
            continue
        if not _session_active_or_recent(session, recent_terminal_seconds=RECENT_ACTIONABLE_SECONDS):
            continue
        report_id = str(session.get("report_id") or "")
        if not report_id:
            continue
        sid = str(session.get("session_id") or session_path.parent.name)
        workspace = str(session.get("workspace_path") or "")
        bridge = bridge_by_workspace.get(workspace)
        bridge_running = bool(bridge and str(bridge.get("status") or "") == "running")
        turn = session.get("current_turn") if isinstance(session.get("current_turn"), dict) else {}
        turn_status = str(turn.get("status") or session.get("current_turn_status") or "")
        turn_progress = 100 if turn_status in TERMINAL_STATUSES else None
        updated_at = str(session.get("updated_at") or "")
        if turn_status:
            items.append(
                _item(
                    kind="report_agent_turn",
                    item_id=sid,
                    report_id=report_id,
                    label="后续改造 Codex turn",
                    status=turn_status,
                    stage_id=str(turn.get("turn_id") or ""),
                    stage_title=str(turn.get("user_message") or "report-agent turn")[:80],
                    progress_percent=turn_progress,
                    error=str(turn.get("error") or session.get("native_protocol_error") or ""),
                    can_cancel=turn_status in RUNNING_STATUSES,
                    disabled_reason="继续修改请在左侧对话框发送新消息；运行中可发送引导。",
                    updated_at=updated_at,
                    scope="active",
                    meta={"session_id": sid, "native_turn_id": turn.get("native_turn_id"), "live_evidence": bridge_running},
                )
            )
        if bridge or str(session.get("mode") or "") == "native_app_server":
            items.append(
                _item(
                    kind="native_app_server",
                    item_id=sid,
                    report_id=report_id,
                    label="Codex app-server",
                    status=str((bridge or {}).get("status") or session.get("native_connection_status") or "idle"),
                    stage_id=str((bridge or {}).get("thread_id") or session.get("codex_thread_id") or ""),
                    stage_title="原生 Codex 会话",
                    progress_percent=None,
                    disabled_reason="app-server 随会话按需启动，无需手动续跑。",
                    updated_at=updated_at,
                    scope="active",
                    meta={"pid": (bridge or {}).get("pid"), "workspace_path": workspace, "live_evidence": bridge_running},
                )
            )
    return items


def _compute_active_runtime_processes(*, limit: int, recent_terminal_seconds: int) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    items.extend(_load_all_report_task_items())
    items.extend(_load_all_pipeline_items())
    items.extend(_load_all_codex_task_items())
    items.extend(_load_all_agent_session_items())
    filtered = [
        item
        for item in items
        if _active_scope_includes(item, recent_terminal_seconds=recent_terminal_seconds)
    ]
    filtered.sort(key=_active_scope_sort_key)
    filtered = filtered[: max(1, min(int(limit or 80), 250))]
    return {"scope": "active", "processes": filtered}


def _refresh_active_process_cache_async(cache_key: tuple[int, int]) -> None:
    with _ACTIVE_PROCESS_CACHE_LOCK:
        if cache_key in _ACTIVE_PROCESS_CACHE_REFRESHING:
            return
        _ACTIVE_PROCESS_CACHE_REFRESHING.add(cache_key)

    def _runner() -> None:
        try:
            payload = _compute_active_runtime_processes(limit=cache_key[0], recent_terminal_seconds=cache_key[1])
            with _ACTIVE_PROCESS_CACHE_LOCK:
                _ACTIVE_PROCESS_CACHE.update(
                    {
                        "key": cache_key,
                        "expires_at": time.monotonic() + ACTIVE_PROCESS_CACHE_SECONDS,
                        "payload": payload,
                    }
                )
        finally:
            with _ACTIVE_PROCESS_CACHE_LOCK:
                _ACTIVE_PROCESS_CACHE_REFRESHING.discard(cache_key)

    threading.Thread(target=_runner, name=f"runtime-active-cache-{cache_key[0]}-{cache_key[1]}", daemon=True).start()


def list_active_runtime_processes(*, limit: int = 80, recent_terminal_seconds: int = 1800) -> dict[str, Any]:
    cache_key = (max(1, min(int(limit or 80), 250)), int(recent_terminal_seconds or 1800))
    now = time.monotonic()
    with _ACTIVE_PROCESS_CACHE_LOCK:
        cached_key = _ACTIVE_PROCESS_CACHE.get("key")
        cached_expires_at = float(_ACTIVE_PROCESS_CACHE.get("expires_at") or 0.0)
        cached_payload = _ACTIVE_PROCESS_CACHE.get("payload")
    if cached_key == cache_key and now < cached_expires_at and isinstance(cached_payload, dict):
        return dict(cached_payload)
    _refresh_active_process_cache_async(cache_key)
    if cached_key == cache_key and isinstance(cached_payload, dict):
        return dict(cached_payload)
    return {"scope": "active", "processes": [], "warming": True}


def cancel_runtime_process(kind: str, process_id: str, *, report_id: str, session_id: str = "") -> dict[str, Any]:
    if kind == "pipeline":
        from app.services.codex_runtime_pipeline_service import cancel_pipeline_job

        result = cancel_pipeline_job(process_id)
    elif kind == "codex_run_task":
        from app.services.codex_runtime_task_service import cancel_codex_run_task

        result = cancel_codex_run_task(process_id)
    elif kind == "report_agent_turn":
        from app.services.report_agent_session_service import cancel_report_agent_turn

        result = cancel_report_agent_turn(report_id, process_id or session_id)
    else:
        raise HTTPException(status_code=400, detail=f"Runtime process is not cancellable: {kind}")
    return {"action": "cancel", "kind": kind, "id": process_id, "result": result, **list_runtime_processes(report_id, session_id)}


def resume_runtime_process(kind: str, process_id: str, *, report_id: str, session_id: str = "") -> dict[str, Any]:
    if kind == "pipeline":
        manifest = read_pipeline_manifest(process_id)
        status = str(manifest.get("status") or "")
        observation = _pipeline_runtime_observation(manifest)
        is_stale = bool(observation.get("is_stale"))
        if is_stale and status not in PIPELINE_RESUMABLE_STATUSES and status not in TERMINAL_STATUSES:
            retry_stage_hint = _pipeline_retry_stage(manifest)
            manifest = update_pipeline_manifest(
                process_id,
                {
                    "status": "failed",
                    "error": (
                        "Runtime resume marked stale pipeline as failed for safe retry: "
                        f"{observation.get('stale_reason') or 'missing live execution evidence'}"
                    ),
                    "current_stage_detail": "Pipeline execution became stale; runtime resume will retry the current stage.",
                    "result_summary": {
                        **dict(manifest.get("result_summary") or {}),
                        "stale_recovered_from_status": status,
                        "stale_recovered_stage_id": retry_stage_hint,
                        "stale_recovery_reason": observation.get("stale_reason") or "",
                    },
                },
            )
            status = str(manifest.get("status") or "")
            observation = _pipeline_runtime_observation(manifest)
            is_stale = bool(observation.get("is_stale"))
        preflight = _pipeline_resume_preflight(manifest, repair=True)
        retry_stage_id = str(preflight.get("retry_stage_id") or _pipeline_retry_stage(manifest))
        resume_strategy = str(preflight.get("resume_strategy") or "")
        if status not in PIPELINE_RESUMABLE_STATUSES and not is_stale:
            raise HTTPException(
                status_code=409,
                detail=_pipeline_disabled_reason(status, retry_stage_id) or f"Pipeline is not resumable in status `{status}`.",
            )
        if resume_strategy == "blocked_missing_inputs":
            return {
                "action": "resume_blocked",
                "kind": kind,
                "id": process_id,
                "pipeline_job_id": process_id,
                "pipeline_type": manifest.get("pipeline_type"),
                "resume_strategy": preflight.get("resume_strategy"),
                "resume_issue_kind": preflight.get("resume_issue_kind") or "",
                "repair_rule_id": preflight.get("repair_rule_id") or "",
                "stale_session_id": preflight.get("stale_session_id") or "",
                "retry_stage_id": retry_stage_id,
                "rollback_stage_id": preflight.get("rollback_stage_id") or "",
                "workspace_path": manifest.get("workspace_path"),
                "workspace_rebuild_path": preflight.get("workspace_rebuild_path") or "",
                "repair_log_path": preflight.get("repair_log_path") or "",
                "contract_batch_manifest_path": preflight.get("contract_batch_manifest_path") or "",
                "blocking_missing_inputs": list(preflight.get("blocking_missing_inputs") or []),
                "result": preflight,
                **list_runtime_processes(report_id, session_id),
            }
        if resume_strategy == "rebuild_workspace_then_restart_pipeline":
            from app.services.report_service import create_generic_long_cli_pipeline_from_completed_report

            result = create_generic_long_cli_pipeline_from_completed_report(report_id, auto_start=True)
            return {
                "action": "rebuild_workspace_then_restart_pipeline",
                "kind": kind,
                "id": process_id,
                "pipeline_job_id": (result or {}).get("pipeline_job_id") if isinstance(result, dict) else "",
                "pipeline_type": (result or {}).get("specialized_pipeline_type") or (result or {}).get("pipeline_type") if isinstance(result, dict) else "generic_long_cli_pipeline",
                "raw_pipeline_type": (result or {}).get("pipeline_type") if isinstance(result, dict) else "generic_long_cli_pipeline",
                "pipeline_label": (result or {}).get("pipeline_label") if isinstance(result, dict) else "",
                "resume_strategy": resume_strategy,
                "resume_issue_kind": preflight.get("resume_issue_kind") or "",
                "repair_rule_id": preflight.get("repair_rule_id") or "",
                "retry_stage_id": "",
                "rollback_stage_id": preflight.get("rollback_stage_id") or "",
                "workspace_path": (result or {}).get("workspace_path") if isinstance(result, dict) else "",
                "workspace_rebuild_path": preflight.get("workspace_rebuild_path") or "",
                "repair_log_path": preflight.get("repair_log_path") or "",
                "contract_batch_manifest_path": preflight.get("contract_batch_manifest_path") or "",
                "blocking_missing_inputs": [],
                "result": result,
                **list_runtime_processes(report_id, session_id),
            }
        if status == "queued":
            from app.services.codex_runtime_pipeline_service import start_pipeline_job

            result = start_pipeline_job(process_id)
        else:
            if not retry_stage_id:
                raise HTTPException(status_code=400, detail="No retryable pipeline stage could be inferred from the manifest.")
            try:
                from app.services.codex_runtime_pipeline_service import retry_pipeline_stage

                result = retry_pipeline_stage(process_id, stage_id=retry_stage_id, auto_start=True)
            except Exception as exc:
                raise HTTPException(
                    status_code=500,
                    detail={
                        "message": str(exc),
                        "pipeline_job_id": process_id,
                        "retry_stage_id": retry_stage_id,
                        "pipeline_type": manifest.get("pipeline_type"),
                    },
                ) from exc
    elif kind == "runtime_bootstrap":
        bootstrap = _completed_report_cli_bootstrap_status(report_id)
        if not bootstrap.get("can_start_generic_long_cli"):
            blocked_action = str(_completed_report_route_meta(str(bootstrap.get("business_profile") or ""), str(bootstrap.get("report_lens") or "")).get("blocked_action") or "start_generic_long_cli_blocked")
            return {
                "action": blocked_action,
                "kind": kind,
                "id": process_id,
                "resume_strategy": "blocked_missing_inputs",
                "blocking_missing_inputs": list(bootstrap.get("missing_required_assets") or []),
                "result": bootstrap,
                **list_runtime_processes(report_id, session_id),
            }
        from app.services.report_service import create_generic_long_cli_pipeline_from_completed_report

        result = create_generic_long_cli_pipeline_from_completed_report(report_id, auto_start=True)
    elif kind == "codex_run_task":
        task = get_codex_run_task(process_id)
        raise HTTPException(
            status_code=400,
            detail=f"Codex runtime task cannot resume directly; retry its parent pipeline instead. status={task.get('status')}",
        )
    else:
        raise HTTPException(status_code=400, detail=f"Runtime process is not resumable: {kind}")
    return {
        "action": "resume",
        "kind": kind,
        "id": process_id,
        "pipeline_job_id": (result or {}).get("pipeline_job_id") if isinstance(result, dict) else "",
        "pipeline_type": (result or {}).get("specialized_pipeline_type") or (result or {}).get("pipeline_type") if isinstance(result, dict) else manifest.get("pipeline_type") if kind == "pipeline" else "",
        "raw_pipeline_type": (result or {}).get("pipeline_type") if isinstance(result, dict) else manifest.get("pipeline_type") if kind == "pipeline" else "",
        "pipeline_label": (result or {}).get("pipeline_label") if isinstance(result, dict) else "",
        "resume_strategy": (
            preflight.get("resume_strategy")
            if kind == "pipeline"
            else (
                (result or {}).get("resume_strategy") or "start_generic_long_cli_pipeline"
                if isinstance(result, dict) and kind == "runtime_bootstrap"
                else ""
            )
        ),
        "resume_issue_kind": preflight.get("resume_issue_kind") if kind == "pipeline" else "",
        "repair_rule_id": preflight.get("repair_rule_id") if kind == "pipeline" else "",
        "stale_session_id": preflight.get("stale_session_id") if kind == "pipeline" else "",
        "retry_stage_id": retry_stage_id if kind == "pipeline" else "",
        "rollback_stage_id": preflight.get("rollback_stage_id") if kind == "pipeline" else "",
        "workspace_path": (result or {}).get("workspace_path") if isinstance(result, dict) else manifest.get("workspace_path") if kind == "pipeline" else "",
        "workspace_rebuild_path": preflight.get("workspace_rebuild_path") if kind == "pipeline" else "",
        "repair_log_path": preflight.get("repair_log_path") if kind == "pipeline" else "",
        "contract_batch_manifest_path": preflight.get("contract_batch_manifest_path") if kind == "pipeline" else "",
        "blocking_missing_inputs": list(preflight.get("blocking_missing_inputs") or []) if kind == "pipeline" else list((result or {}).get("missing_required_assets") or []) if isinstance(result, dict) else [],
        "result": result,
        **list_runtime_processes(report_id, session_id),
    }
