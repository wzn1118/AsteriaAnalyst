from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.path_service import RUNS_DIR


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _slug_time() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _http_json(url: str, *, method: str = "GET", payload: dict[str, Any] | None = None, timeout: int = 120) -> dict[str, Any]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"} if payload is not None else {},
        method=method,
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _procurement_downloadables(report_payload: dict[str, Any]) -> list[dict[str, Any]]:
    downloadables = list(report_payload.get("downloadables") or [])
    matched: list[dict[str, Any]] = []
    for item in downloadables:
        name = str((item or {}).get("name") or "")
        purpose = str((item or {}).get("purpose") or "")
        if "procurement_sales_cli_shadow" in name or "Codex CLI 采销高级分析" in purpose:
            matched.append(dict(item))
    return matched


def run_smoke(
    *,
    base_url: str,
    dataset_id: str,
    poll_interval_sec: float,
    max_seconds: float,
    output_dir: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    started_at = time.time()
    created_at = _now_iso()

    payload = {
        "sheet_name": "Sheet1",
        "selected_sheets": ["Sheet1"],
        "multi_table_mode": "single",
        "business_profile": "procurement_sales_report",
        "report_style": "executive",
        "report_language": "zh-CN",
        "user_requirement": "请生成采销经营复盘，重点看品类、SKU、供应商、库存与履约动作。",
        "problem_to_solve": "识别当前采销结构问题和本周优先动作。",
        "target_audience": "management",
        "core_purpose": "management_review",
        "expected_result": "main report plus procurement shadow pipeline outputs",
        "key_constraints": "main report must remain available",
        "use_r_workflow": False,
        "industry_research_standalone_enabled": False,
        "enable_premium_pipeline": False,
    }
    created = _http_json(
        f"{base_url}/api/datasets/{dataset_id}/smart-report-jobs",
        method="POST",
        payload=payload,
    )
    report_job_id = str(created.get("job_id") or "")
    checkpoints: list[dict[str, Any]] = []
    report_id = ""
    main_report_completed_at = ""
    shadow_pipeline_job_id = ""
    shadow_first_seen_at = ""
    shadow_first_running_at = ""
    final_pipeline_status = ""
    registered_downloadables: list[dict[str, Any]] = []
    report_task_payload: dict[str, Any] = {}
    pipeline_payload: dict[str, Any] = {}

    while time.time() - started_at < max_seconds:
        report_task_payload = _http_json(f"{base_url}/api/report-jobs/{report_job_id}")
        result_summary = dict(report_task_payload.get("result_summary") or {})
        result_payload = dict(report_task_payload.get("result") or {})
        report_id = str(result_payload.get("report_id") or result_summary.get("report_id") or report_id)
        shadow_pipeline_job_id = str(
            result_summary.get("procurement_sales_long_cli_pipeline_job_id")
            or result_payload.get("procurement_sales_long_cli_pipeline_job_id")
            or shadow_pipeline_job_id
        ).strip()
        shadow_status = str(
            result_summary.get("procurement_sales_long_cli_pipeline_status")
            or ((result_payload.get("procurement_sales_long_cli_pipeline") or {}).get("status") if isinstance(result_payload, dict) else "")
            or ""
        ).strip()
        checkpoint = {
            "t_sec": round(time.time() - started_at, 1),
            "task_status": report_task_payload.get("status"),
            "task_stage": report_task_payload.get("current_stage_id"),
            "task_title": report_task_payload.get("current_stage_title"),
            "task_progress": report_task_payload.get("progress_percent"),
            "shadow_pipeline_job_id": shadow_pipeline_job_id,
            "shadow_pipeline_status": shadow_status,
        }
        checkpoints.append(checkpoint)

        if shadow_pipeline_job_id and not shadow_first_seen_at:
            shadow_first_seen_at = _now_iso()
        if shadow_status == "running" and not shadow_first_running_at:
            shadow_first_running_at = _now_iso()

        if str(report_task_payload.get("status") or "") == "failed":
            break

        if str(report_task_payload.get("status") or "") == "completed":
            if not main_report_completed_at:
                main_report_completed_at = _now_iso()
            if shadow_pipeline_job_id:
                if shadow_status == "running":
                    pipeline_payload = _http_json(
                        f"{base_url}/api/codex-pipeline-jobs/{shadow_pipeline_job_id}"
                    )
                    final_pipeline_status = str(pipeline_payload.get("status") or "")
                    break
                if shadow_status in {"completed", "failed", "cancelled"}:
                    pipeline_payload = _http_json(
                        f"{base_url}/api/codex-pipeline-jobs/{shadow_pipeline_job_id}"
                    )
                    final_pipeline_status = str(pipeline_payload.get("status") or "")
                    registered_downloadables = _procurement_downloadables(result_payload)
                    break
            time.sleep(poll_interval_sec)
            continue

        time.sleep(poll_interval_sec)

    if shadow_pipeline_job_id and not pipeline_payload:
        try:
            pipeline_payload = _http_json(
                f"{base_url}/api/codex-pipeline-jobs/{shadow_pipeline_job_id}"
            )
            final_pipeline_status = str(pipeline_payload.get("status") or "")
        except Exception:
            pipeline_payload = {}

    if not registered_downloadables and isinstance(report_task_payload.get("result"), dict):
        registered_downloadables = _procurement_downloadables(
            dict(report_task_payload.get("result") or {})
        )

    captured_report_task_snapshot_path = _write_json(
        output_dir / "report_task_snapshot.json",
        report_task_payload,
    )
    captured_pipeline_snapshot_path = _write_json(
        output_dir / "pipeline_snapshot.json",
        pipeline_payload,
    )
    canonical_report_task_path = (RUNS_DIR / "report_tasks" / f"{report_job_id}.json").resolve()
    canonical_pipeline_manifest_path = (
        (RUNS_DIR / "codex_pipeline" / "jobs" / shadow_pipeline_job_id / "pipeline.json").resolve()
        if shadow_pipeline_job_id
        else Path()
    )
    result = {
        "created_at": created_at,
        "base_url": base_url,
        "dataset_id": dataset_id,
        "report_job_id": report_job_id,
        "report_id": report_id,
        "main_report_completed_at": main_report_completed_at,
        "procurement_shadow_pipeline_job_id": shadow_pipeline_job_id,
        "procurement_shadow_pipeline_first_seen_at": shadow_first_seen_at,
        "procurement_shadow_pipeline_first_running_at": shadow_first_running_at,
        "final_pipeline_status": final_pipeline_status,
        "registered_downloadables": registered_downloadables,
        "report_task_snapshot_path": str(canonical_report_task_path),
        "pipeline_manifest_path": str(canonical_pipeline_manifest_path) if shadow_pipeline_job_id else "",
        "captured_report_task_snapshot_path": str(captured_report_task_snapshot_path.resolve()),
        "captured_pipeline_snapshot_path": str(captured_pipeline_snapshot_path.resolve()),
        "checkpoints": checkpoints[-20:],
        "pass": bool(main_report_completed_at and shadow_pipeline_job_id and shadow_first_running_at),
    }
    _write_json(output_dir / "result.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a real async procurement shadow end-to-end smoke via the backend API."
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="Backend API base URL.",
    )
    parser.add_argument(
        "--dataset-id",
        default="realolist500a1",
        help="Dataset id to use for the smoke run.",
    )
    parser.add_argument(
        "--poll-interval-sec",
        type=float,
        default=8.0,
        help="Polling interval in seconds.",
    )
    parser.add_argument(
        "--max-seconds",
        type=float,
        default=1800.0,
        help="Maximum time budget for the smoke run.",
    )
    parser.add_argument(
        "--output-dir",
        default="",
        help="Optional output directory for smoke artifacts.",
    )
    args = parser.parse_args()

    if args.output_dir:
        output_dir = Path(args.output_dir).expanduser().resolve()
    else:
        output_dir = (
            RUNS_DIR
            / "smokes"
            / f"procurement_shadow_e2e_smoke_{_slug_time()}"
        ).resolve()

    result = run_smoke(
        base_url=str(args.base_url).rstrip("/"),
        dataset_id=str(args.dataset_id),
        poll_interval_sec=float(args.poll_interval_sec),
        max_seconds=float(args.max_seconds),
        output_dir=output_dir,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
