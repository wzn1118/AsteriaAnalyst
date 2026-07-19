from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.models import SmartReportRequest  # noqa: E402
from app.services.codex_runtime_pipeline_service import create_pipeline_job, run_pipeline_job_to_completion  # noqa: E402
from app.services.dataset_service import load_dataset_frame  # noqa: E402
from app.services.path_service import REPORTS_DIR  # noqa: E402
from app.services.report_service import (  # noqa: E402
    _prepare_internet_ops_long_cli_workspace,
    register_internet_ops_long_cli_pipeline_output,
)


def _json_print(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False), flush=True)


def main() -> None:
    dataset_id = sys.argv[1] if len(sys.argv) > 1 else "gomaskdededd"
    frame, metadata, sheet = load_dataset_frame(dataset_id, "Sheet1")
    report_id = f"pubops{uuid.uuid4().hex[:6]}"
    report_dir = REPORTS_DIR / f"smart-report-{report_id}"
    report_dir.mkdir(parents=True, exist_ok=True)

    public_source = metadata.get("public_source") or {}
    (report_dir / f"{report_id}-public_source.json").write_text(
        json.dumps(public_source, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    frame.to_csv(report_dir / f"{report_id}-normalized_public_source.csv", index=False, encoding="utf-8-sig")

    request = SmartReportRequest(
        sheet_name="Sheet1",
        selected_sheets=["Sheet1"],
        multi_table_mode="single",
        business_profile="internet_operations_report",
        report_style="deep_dive",
        report_language="zh-CN",
        user_requirement=(
            "使用 GoMask 公开 Campaign Channel Conversion Breakdown 数据实测互联网运营专项链。"
            "重点检查 canonical 口径一致、连续叙事、图表解释、Day 1-Day 7 可执行动作、管理版和完整表长版。"
        ),
        core_purpose="公开互联网营销投放数据的经营复盘与预算迁移决策",
        target_audience="管理层、增长负责人、投放负责人",
        expected_result="产出主报告、管理版和完整表长版，并通过互联网运营口径一致性质检门。",
        generate_full_table_version=True,
    )
    requirement_intent = {
        "optimized_user_requirement": request.user_requirement,
        "target_audience": request.target_audience,
        "core_purpose": request.core_purpose,
        "expected_result": request.expected_result,
        "required_detail_dimensions": [
            "channel",
            "traffic_source",
            "campaign",
            "content_category",
            "product_module",
            "user_segment",
            "city_tier",
            "date",
        ],
        "must_include_sections": [
            "口径闭环",
            "连续经营分析",
            "图表解释",
            "Day 1-Day 7 可执行动作",
            "管理版",
            "完整表长版",
        ],
        "public_source": public_source,
    }
    context_payload = {
        "style_preset": request.premium_style_preset,
        "language": request.report_language,
        "report_goal": "public_dataset_internet_operations_smoke",
        "analysis_mode": "internet_ops_long_cli_pipeline",
        "business_focus": request.core_purpose,
        "user_requirement": request.user_requirement,
        "target_audience": request.target_audience,
        "request": request.model_dump(),
        "requirement_intent": requirement_intent,
        "prefer_existing_requirement_intent": True,
        "prefer_deterministic_internet_ops_foundation": True,
        "prefer_deterministic_internet_ops_chart_insights": True,
        "codex_model_override": "gpt-5.4",
        "generate_full_table_version": True,
        "dataset_id": dataset_id,
        "dataset_name": metadata.get("name") or dataset_id,
        "sheet_name": sheet.get("name") or "Sheet1",
        "report_id": report_id,
        "public_source": public_source,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    _json_print(
        {
            "event": "direct_report_workspace_ready",
            "dataset_id": dataset_id,
            "report_id": report_id,
            "report_dir": str(report_dir.resolve()),
            "rows": int(frame.shape[0]),
            "columns": int(frame.shape[1]),
            "source_url": public_source.get("source_url"),
        }
    )

    pipeline = create_pipeline_job(
        pipeline_type="internet_ops_long_cli_pipeline",
        workspace_path=str(report_dir / "codex_premium" / "internet_ops_shadow" / "{pipeline_job_id}"),
        linked_report_id=report_id,
        context_payload=context_payload,
        auto_start=False,
    )
    pipeline_job_id = str(pipeline.get("pipeline_job_id") or "")
    workspace = Path(str(pipeline.get("workspace_path") or ""))
    copied_inputs = _prepare_internet_ops_long_cli_workspace(
        workspace_dir=workspace,
        report_dir=report_dir,
        report_id=report_id,
        frame=frame,
        request=request,
        requirement_intent=requirement_intent,
        context_payload={**context_payload, "pipeline_job_id": pipeline_job_id},
    )
    _json_print(
        {
            "event": "pipeline_created",
            "pipeline_job_id": pipeline_job_id,
            "workspace": str(workspace.resolve()),
            "copied_input_count": len(copied_inputs),
        }
    )

    def progress(manifest: dict) -> None:
        _json_print(
            {
                "event": "pipeline_progress",
                "pipeline_job_id": manifest.get("pipeline_job_id"),
                "status": manifest.get("status"),
                "current_stage_id": manifest.get("current_stage_id"),
                "progress_percent": manifest.get("progress_percent"),
                "error": manifest.get("error"),
            }
        )

    final_manifest = run_pipeline_job_to_completion(pipeline_job_id, progress_callback=progress)
    _json_print(
        {
            "event": "pipeline_done",
            "pipeline_job_id": pipeline_job_id,
            "status": final_manifest.get("status"),
            "current_stage_id": final_manifest.get("current_stage_id"),
            "progress_percent": final_manifest.get("progress_percent"),
            "error": final_manifest.get("error"),
        }
    )
    if str(final_manifest.get("status") or "") != "completed":
        raise SystemExit(2)

    registered = register_internet_ops_long_cli_pipeline_output(pipeline_job_id)
    _json_print(
        {
            "event": "registered",
            "report_id": registered.get("report_id"),
            "pipeline_job_id": registered.get("pipeline_job_id"),
            "downloadables": [
                {
                    "name": item.get("name"),
                    "type": item.get("type"),
                    "purpose": item.get("purpose"),
                    "file_path": item.get("file_path"),
                }
                for item in registered.get("downloadables", [])
            ],
            "manifest_asset": registered.get("manifest_asset"),
        }
    )


if __name__ == "__main__":
    main()
