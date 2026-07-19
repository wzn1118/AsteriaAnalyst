from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.services.path_service import DATASETS_DIR, PUBLIC_ARTIFACTS_DIR, STORAGE_DIR

PDCA_DIR = STORAGE_DIR / "analysis_lab_pdca"
PDCA_STATUS_PATH = PDCA_DIR / "status.json"
PDCA_HISTORY_PATH = PDCA_DIR / "history.jsonl"
PDCA_LATEST_MARKDOWN_PATH = PDCA_DIR / "latest.md"
AUTO_ANALYSIS_ROOT = PUBLIC_ARTIFACTS_DIR / "auto-analysis"

LARGE_SAMPLE_THRESHOLD = int(os.getenv("ASTERIA_ANALYSIS_LAB_PDCA_LARGE_SAMPLE_THRESHOLD", "5000"))
DEFAULT_INTERVAL_SEC = max(60, int(os.getenv("ASTERIA_ANALYSIS_LAB_PDCA_INTERVAL_SEC", "900")))
MAX_REPORT_SCAN = max(5, int(os.getenv("ASTERIA_ANALYSIS_LAB_PDCA_MAX_REPORTS", "40")))
MAX_DATASET_SCAN = max(10, int(os.getenv("ASTERIA_ANALYSIS_LAB_PDCA_MAX_DATASETS", "40")))
SCAN_TIME_BUDGET_SEC = max(0.5, float(os.getenv("ASTERIA_ANALYSIS_LAB_PDCA_SCAN_BUDGET_SEC", "2.5")))
MAX_JSON_READ_BYTES = max(32_768, int(os.getenv("ASTERIA_ANALYSIS_LAB_PDCA_MAX_JSON_READ_BYTES", "262144")))

REQUIRED_REPORT_FILES = (
    "runtime_package_manifest.json",
    "report_part_bundle.json",
    "lab_report.md",
    "lab_report.html",
    "method_artifact_index.json",
    "method_artifact_index.csv",
    "method_artifact_index.xlsx",
    "method_artifact_integrity.json",
    "codex_method_interpretation_input.json",
    "codex_method_interpretation_prompt.md",
    "codex_method_interpretations.json",
    "codex_method_interpretations.md",
    "chart_asset_index.json",
    "chart_asset_index.csv",
    "chart_asset_index.xlsx",
)

_LOCK = threading.Lock()
_STOP_EVENT = threading.Event()
_SCHEDULER_THREAD: threading.Thread | None = None
_STATE: dict[str, Any] = {
    "scheduler_status": "not_started",
    "last_cycle": {},
    "next_run_at": "",
    "interval_sec": DEFAULT_INTERVAL_SEC,
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _read_json(path: Path, *, max_bytes: int = MAX_JSON_READ_BYTES) -> dict[str, Any]:
    try:
        if not path.exists():
            return {}
        size = path.stat().st_size
        if size > max_bytes:
            return {"_read_skipped": "file_too_large", "_size_bytes": size}
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception as exc:
        return {"_read_error": str(exc)}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")


def _latest_auto_analysis_report_dirs(*, limit: int, deadline: float) -> list[Path]:
    if not AUTO_ANALYSIS_ROOT.exists():
        return []
    report_dirs: list[Path] = []
    dataset_dirs = []
    for path in AUTO_ANALYSIS_ROOT.iterdir():
        if time.time() >= deadline:
            break
        if path.is_dir():
            dataset_dirs.append(path)
    dataset_dirs.sort(key=lambda item: item.stat().st_mtime if item.exists() else 0.0, reverse=True)
    for dataset_dir in dataset_dirs:
        if time.time() >= deadline or len(report_dirs) >= limit:
            break
        if not dataset_dir.is_dir():
            continue
        report_candidates = []
        for path in dataset_dir.iterdir():
            if time.time() >= deadline:
                break
            if path.is_dir():
                report_candidates.append(path)
        report_candidates.sort(key=lambda item: item.stat().st_mtime if item.exists() else 0.0, reverse=True)
        for report_dir in report_candidates:
            if time.time() >= deadline or len(report_dirs) >= limit:
                break
            if not report_dir.is_dir():
                continue
            if (report_dir / "runtime_package_manifest.json").is_file():
                report_dirs.append(report_dir)
    report_dirs.sort(key=lambda item: item.stat().st_mtime if item.exists() else 0.0, reverse=True)
    return report_dirs[:limit]


def _dataset_inventory() -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    large_count = 0
    scanned_count = 0
    deadline = time.time() + SCAN_TIME_BUDGET_SEC
    if DATASETS_DIR.exists():
        dataset_dirs = []
        for path in DATASETS_DIR.iterdir():
            if time.time() >= deadline:
                break
            if path.is_dir():
                dataset_dirs.append(path)
        dataset_dirs.sort(key=lambda item: item.stat().st_mtime if item.exists() else 0.0, reverse=True)
        for dataset_dir in dataset_dirs[:MAX_DATASET_SCAN]:
            if time.time() >= deadline:
                break
            metadata_path = dataset_dir / "metadata.json"
            if not metadata_path.exists():
                continue
            scanned_count += 1
            metadata = _read_json(metadata_path)
            row_count = int(metadata.get("row_count") or 0)
            enhanced = metadata.get("enhanced_data_profile") if isinstance(metadata.get("enhanced_data_profile"), dict) else {}
            is_large = row_count >= LARGE_SAMPLE_THRESHOLD
            if is_large:
                large_count += 1
            items.append(
                {
                    "dataset_id": str(metadata.get("dataset_id") or metadata_path.parent.name),
                    "name": str(metadata.get("name") or metadata.get("filename") or ""),
                    "active_sheet": str(metadata.get("active_sheet") or ""),
                    "row_count": row_count,
                    "column_count": int(metadata.get("column_count") or 0),
                    "large_sample": is_large,
                    "enhanced_profile_contract": str(enhanced.get("contract") or ""),
                    "profile_sample_strategy": str(enhanced.get("profile_sample_strategy") or ""),
                    "profile_row_count": int(enhanced.get("profile_row_count") or 0),
                    "metadata_path": str(metadata_path),
                }
            )
    return {
        "dataset_count": len(items),
        "large_dataset_count": large_count,
        "scanned_dataset_count": scanned_count,
        "scan_limited": bool(DATASETS_DIR.exists() and len(items) >= MAX_DATASET_SCAN),
        "items": items[:50],
    }


def _file_status(report_dir: Path, file_name: str) -> dict[str, Any]:
    path = report_dir / file_name
    exists = path.exists()
    return {
        "name": file_name,
        "exists": exists,
        "size_bytes": path.stat().st_size if exists else 0,
    }


def _report_inventory() -> dict[str, Any]:
    deadline = time.time() + SCAN_TIME_BUDGET_SEC
    report_dirs = _latest_auto_analysis_report_dirs(limit=MAX_REPORT_SCAN, deadline=deadline)
    reports: list[dict[str, Any]] = []
    missing_file_count = 0
    large_policy_count = 0
    complete_count = 0
    async_needed_count = 0
    async_deferred_count = 0

    for report_dir in report_dirs:
        manifest_path = report_dir / "runtime_package_manifest.json"
        manifest = _read_json(manifest_path)
        bundle = _read_json(report_dir / "report_part_bundle.json")
        interpretations = _read_json(report_dir / "codex_method_interpretations.json")
        lab_report = bundle.get("lab_report") if isinstance(bundle.get("lab_report"), dict) else {}
        large_policy = (
            manifest.get("large_sample_policy")
            if isinstance(manifest.get("large_sample_policy"), dict)
            else bundle.get("large_sample_policy")
            if isinstance(bundle.get("large_sample_policy"), dict)
            else {}
        )
        required = [_file_status(report_dir, file_name) for file_name in REQUIRED_REPORT_FILES]
        missing = [item["name"] for item in required if not item["exists"] or int(item["size_bytes"] or 0) <= 0]
        missing_file_count += len(missing)
        is_large = bool(large_policy.get("large_sample")) or int(large_policy.get("row_count") or 0) >= LARGE_SAMPLE_THRESHOLD
        if large_policy:
            large_policy_count += 1
        sync_cli = interpretations.get("sync_codex_cli") if isinstance(interpretations.get("sync_codex_cli"), dict) else {}
        sync_status = str(sync_cli.get("runtime_status") or "")
        if is_large:
            async_needed_count += 1
        if sync_status == "codex_cli_sync_deferred_large_sample_local_numeric_analysis_used":
            async_deferred_count += 1
        complete = not missing and str((manifest.get("method_artifact_summary") or {}).get("integrity_status") or "") in {"passed", ""}
        if complete:
            complete_count += 1
        reports.append(
            {
                "report_dir": str(report_dir),
                "generated_at": str(manifest.get("generated_at") or lab_report.get("generated_at") or ""),
                "large_sample": is_large,
                "large_sample_policy": large_policy,
                "method_package_count": int(manifest.get("method_package_count") or 0),
                "runtime_handoff_count": int(manifest.get("runtime_handoff_count") or 0),
                "artifact_integrity_status": str((manifest.get("method_artifact_summary") or {}).get("integrity_status") or ""),
                "sync_codex_cli_status": sync_status,
                "missing_required_files": missing,
                "complete": complete,
            }
        )

    return {
        "report_count": len(reports),
        "complete_report_count": complete_count,
        "missing_required_file_count": missing_file_count,
        "large_policy_report_count": large_policy_count,
        "large_async_needed_count": async_needed_count,
        "large_async_deferred_count": async_deferred_count,
        "scan_limited": len(reports) >= MAX_REPORT_SCAN or time.time() >= deadline,
        "reports": reports,
    }


def _build_actions(dataset_inventory: dict[str, Any], report_inventory: dict[str, Any]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    if int(dataset_inventory.get("large_dataset_count") or 0) > 0:
        actions.append(
            {
                "phase": "act",
                "priority": "high",
                "action_id": "large_sample_policy_enforced",
                "status": "active",
                "detail": "Large datasets are present; keep deterministic sampling, non-blocking sync CLI, and manifest policy checks enabled.",
            }
        )
    if int(report_inventory.get("missing_required_file_count") or 0) > 0:
        actions.append(
            {
                "phase": "act",
                "priority": "critical",
                "action_id": "repair_incomplete_lab_exports",
                "status": "needs_attention",
                "detail": "Some Analysis Lab report directories are missing required JSON/CSV/XLSX/PNG/Markdown discovery files.",
            }
        )
    if int(report_inventory.get("large_async_needed_count") or 0) > int(report_inventory.get("large_async_deferred_count") or 0):
        actions.append(
            {
                "phase": "act",
                "priority": "high",
                "action_id": "backfill_large_sample_async_interpretation",
                "status": "recommended",
                "detail": "Some large-sample outputs need async Codex interpretation tracking or backfill.",
            }
        )
    if not actions:
        actions.append(
            {
                "phase": "act",
                "priority": "normal",
                "action_id": "continue_scheduled_pdca",
                "status": "healthy",
                "detail": "No critical Analysis Lab backend capability gaps were found in this cycle.",
            }
        )
    return actions


def _render_markdown(cycle: dict[str, Any]) -> str:
    plan = cycle.get("plan") if isinstance(cycle.get("plan"), dict) else {}
    check = cycle.get("check") if isinstance(cycle.get("check"), dict) else {}
    actions = cycle.get("act") if isinstance(cycle.get("act"), list) else []
    lines = [
        "# Analysis Lab PDCA Status",
        "",
        f"- cycle_id: `{cycle.get('cycle_id')}`",
        f"- trigger: `{cycle.get('trigger')}`",
        f"- generated_at: `{cycle.get('generated_at')}`",
        f"- large_sample_threshold: `{plan.get('large_sample_threshold')}`",
        f"- dataset_count: `{check.get('dataset_count')}`",
        f"- large_dataset_count: `{check.get('large_dataset_count')}`",
        f"- report_count: `{check.get('report_count')}`",
        f"- complete_report_count: `{check.get('complete_report_count')}`",
        f"- missing_required_file_count: `{check.get('missing_required_file_count')}`",
        "",
        "## Actions",
    ]
    for action in actions:
        lines.append(
            f"- `{action.get('priority')}` `{action.get('action_id')}`: {action.get('status')} - {action.get('detail')}"
        )
    return "\n".join(lines).strip() + "\n"


def run_analysis_lab_pdca_cycle(trigger: str = "manual") -> dict[str, Any]:
    with _LOCK:
        started_at = time.time()
        generated_at = _now_iso()
        cycle_id = f"analysis-lab-pdca-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
        dataset_inventory = _dataset_inventory()
        report_inventory = _report_inventory()
        actions = _build_actions(dataset_inventory, report_inventory)
        cycle = {
            "contract": "analysis_lab_backend_pdca_cycle_v1",
            "cycle_id": cycle_id,
            "trigger": trigger,
            "generated_at": generated_at,
            "duration_ms": 0,
            "plan": {
                "large_sample_threshold": LARGE_SAMPLE_THRESHOLD,
                "required_report_files": list(REQUIRED_REPORT_FILES),
                "target": "Keep large-sample Analysis Lab runs responsive while preserving JSON/CSV/XLSX/PNG/report artifacts.",
            },
            "do": {
                "scheduler_enabled": scheduler_enabled(),
                "interval_sec": DEFAULT_INTERVAL_SEC,
                "scan_time_budget_sec": SCAN_TIME_BUDGET_SEC,
                "max_dataset_scan": MAX_DATASET_SCAN,
                "max_report_scan": MAX_REPORT_SCAN,
                "max_json_read_bytes": MAX_JSON_READ_BYTES,
                "scan_roots": {
                    "datasets": str(DATASETS_DIR),
                    "auto_analysis": str(AUTO_ANALYSIS_ROOT),
                    "pdca": str(PDCA_DIR),
                },
                "capability_guards": [
                    "deterministic_even_sample_profile",
                    "analysis_work_frame_large_sample_policy",
                    "sync_codex_cli_deferred_for_large_samples",
                    "runtime_manifest_artifact_discovery",
                ],
            },
            "check": {
                "dataset_count": dataset_inventory["dataset_count"],
                "large_dataset_count": dataset_inventory["large_dataset_count"],
                "scanned_dataset_count": dataset_inventory["scanned_dataset_count"],
                "dataset_scan_limited": dataset_inventory["scan_limited"],
                "report_count": report_inventory["report_count"],
                "complete_report_count": report_inventory["complete_report_count"],
                "missing_required_file_count": report_inventory["missing_required_file_count"],
                "large_policy_report_count": report_inventory["large_policy_report_count"],
                "large_async_needed_count": report_inventory["large_async_needed_count"],
                "large_async_deferred_count": report_inventory["large_async_deferred_count"],
                "report_scan_limited": report_inventory["scan_limited"],
            },
            "act": actions,
            "datasets": dataset_inventory["items"],
            "reports": report_inventory["reports"],
        }
        cycle["duration_ms"] = int((time.time() - started_at) * 1000)
        _write_json(PDCA_STATUS_PATH, cycle)
        _append_jsonl(PDCA_HISTORY_PATH, cycle)
        PDCA_LATEST_MARKDOWN_PATH.write_text(_render_markdown(cycle), encoding="utf-8")
        _STATE.update(
            {
                "scheduler_status": _STATE.get("scheduler_status") or "not_started",
                "last_cycle": cycle,
                "last_run_at": generated_at,
                "status_path": str(PDCA_STATUS_PATH),
                "history_path": str(PDCA_HISTORY_PATH),
                "markdown_path": str(PDCA_LATEST_MARKDOWN_PATH),
            }
        )
        return cycle


def scheduler_enabled() -> bool:
    raw = os.getenv("ASTERIA_ANALYSIS_LAB_PDCA_ENABLED", "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def _scheduler_loop() -> None:
    while not _STOP_EVENT.is_set():
        next_run_at = time.time() + DEFAULT_INTERVAL_SEC
        _STATE["next_run_at"] = datetime.fromtimestamp(next_run_at, timezone.utc).isoformat().replace("+00:00", "Z")
        if _STOP_EVENT.wait(DEFAULT_INTERVAL_SEC):
            break
        try:
            run_analysis_lab_pdca_cycle(trigger="scheduled")
        except Exception as exc:
            _STATE.update({"scheduler_status": "error", "last_error": str(exc), "last_error_at": _now_iso()})


def start_analysis_lab_pdca_scheduler(*, run_immediately: bool = True) -> dict[str, Any]:
    global _SCHEDULER_THREAD
    if not scheduler_enabled():
        _STATE.update({"scheduler_status": "disabled", "interval_sec": DEFAULT_INTERVAL_SEC})
        return get_analysis_lab_pdca_status()
    if _SCHEDULER_THREAD and _SCHEDULER_THREAD.is_alive():
        return get_analysis_lab_pdca_status()
    _STOP_EVENT.clear()
    _STATE.update({"scheduler_status": "running", "interval_sec": DEFAULT_INTERVAL_SEC, "started_at": _now_iso()})
    if run_immediately:
        try:
            run_analysis_lab_pdca_cycle(trigger="startup")
        except Exception as exc:
            _STATE.update({"scheduler_status": "error", "last_error": str(exc), "last_error_at": _now_iso()})
    _SCHEDULER_THREAD = threading.Thread(target=_scheduler_loop, name="analysis-lab-pdca", daemon=True)
    _SCHEDULER_THREAD.start()
    return get_analysis_lab_pdca_status()


def stop_analysis_lab_pdca_scheduler() -> dict[str, Any]:
    _STOP_EVENT.set()
    if _SCHEDULER_THREAD and _SCHEDULER_THREAD.is_alive():
        _SCHEDULER_THREAD.join(timeout=3)
    _STATE.update({"scheduler_status": "stopped", "stopped_at": _now_iso()})
    return get_analysis_lab_pdca_status()


def get_analysis_lab_pdca_status() -> dict[str, Any]:
    status = dict(_STATE)
    if not status.get("last_cycle") and PDCA_STATUS_PATH.exists():
        status["last_cycle"] = _read_json(PDCA_STATUS_PATH)
    status.setdefault("scheduler_enabled", scheduler_enabled())
    status.setdefault("interval_sec", DEFAULT_INTERVAL_SEC)
    status.setdefault("status_path", str(PDCA_STATUS_PATH))
    status.setdefault("history_path", str(PDCA_HISTORY_PATH))
    status.setdefault("markdown_path", str(PDCA_LATEST_MARKDOWN_PATH))
    return status
