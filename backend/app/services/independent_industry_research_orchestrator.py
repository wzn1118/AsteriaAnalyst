from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

import pandas as pd

from app.models import SmartReportRequest
from app.services.independent_industry_research_chain import (
    run_independent_industry_research_chain,
)
from app.services.path_service import REPORTS_DIR


BLOCKED_MAIN_OUTPUTS = [
    "management_report.pdf",
    "management_report.html",
    "analyst_appendix.xlsx",
    "main_report_page_plan.json",
    "main_report_quality_score.json",
    "main_report_quality_gate_result.json",
]

BLOCKED_R_OUTPUTS = [
    "r_cleaned_data",
    "r_analysis_outputs",
    "r_visualization_outputs",
    "r_pdf_explanation",
]


def run_independent_industry_research_orchestrator(
    *,
    report_dir: Path,
    report_id: str,
    dataset_name: str,
    sheet_name: str,
    frame: pd.DataFrame,
    request: SmartReportRequest,
    router_result: dict[str, Any] | None,
    deep_context_understanding: dict[str, Any] | None = None,
    main_report_job_id: str,
    r_workflow_job_id: str,
) -> dict[str, Any]:
    router_result = router_result or {}
    job_id = f"industry-{uuid.uuid4().hex[:12]}"
    output_dir = report_dir / "outputs" / "industry_research"

    base_result = {
        "enabled": bool(request.industry_research_standalone_enabled),
        "industry_research_mode": "standalone" if request.industry_research_standalone_enabled else "disabled",
        "industry_research_job_id": job_id if request.industry_research_standalone_enabled else "",
        "main_report_job_id": main_report_job_id,
        "r_workflow_job_id": r_workflow_job_id,
        "industry_research_chain_executed": False,
        "shared_inputs_used": [],
        "blocked_shared_outputs": [*BLOCKED_MAIN_OUTPUTS, *BLOCKED_R_OUTPUTS],
        "skipped_reason": "",
        "success": False,
        "output_dir": str(output_dir.resolve()),
        "downloadables": [],
    }

    if not request.industry_research_standalone_enabled:
        base_result["skipped_reason"] = "industry_research_standalone_enabled=false"
        return base_result

    output_dir.mkdir(parents=True, exist_ok=True)
    chain_result = run_independent_industry_research_chain(
        output_dir=output_dir,
        user_task_description=request.user_requirement or request.problem_to_solve or request.core_purpose,
        uploaded_file_name=dataset_name,
        sheet_names=[sheet_name],
        field_names=frame.columns.astype(str).tolist(),
        sample_values=[
            str(item)
            for summary in chain_result_placeholder(frame)
            for item in summary.get("sample_values", [])[:2]
        ][:20],
        business_profile_router_result=router_result,
        deep_context_understanding=deep_context_understanding,
        optional_data_summary={
            "dataset_name": dataset_name,
            "sheet_name": sheet_name,
            "row_count": int(len(frame)),
            "column_count": int(len(frame.columns)),
            "data_types": {str(column): str(frame[column].dtype) for column in frame.columns},
        },
        request=request,
        frame=frame,
    )

    try:
        relative_dir = output_dir.relative_to(REPORTS_DIR.parent).as_posix()
    except ValueError:
        relative_dir = output_dir.name

    downloadables = []
    for filename in chain_result.get("output_files", []):
        path = output_dir / filename
        if not path.exists():
            continue
        suffix = path.suffix.lower().lstrip(".")
        downloadables.append(
            {
                "name": path.name,
                "path": f"/storage/{relative_dir}/{path.name}",
                "file_path": str(path.resolve()),
                "purpose": f"{path.name}。",
                "is_main": path.name == "industry_research_report.pdf",
                "type": suffix or "txt",
            }
        )

    return {
        **base_result,
        "industry_research_chain_executed": True,
        "shared_inputs_used": chain_result.get("shared_inputs_used", []),
        "success": bool(chain_result.get("quality_gate_result", {}).get("passed")),
        "downloadables": downloadables,
        "quality_score_path": str((output_dir / "industry_research_quality_score.json").resolve()),
        "quality_gate_path": str((output_dir / "industry_research_quality_gate_result.json").resolve()),
        "stage_trace_path": chain_result.get("stage_trace_path", str((output_dir / "stage_trace.json").resolve())),
        "stage_trace_markdown_path": chain_result.get("stage_trace_markdown_path", str((output_dir / "stage_trace.md").resolve())),
    }


def chain_result_placeholder(frame: pd.DataFrame) -> list[dict[str, Any]]:
    from app.services.dataset_service import build_column_summaries

    return build_column_summaries(frame)
