from __future__ import annotations

from app.main import _auto_analysis_export_paths
from app.models import AutoAnalysisRequest


def test_auto_analysis_export_paths_are_storage_backed() -> None:
    export_dir, public_base_path = _auto_analysis_export_paths(
        AutoAnalysisRequest(dataset_id="demo data/2026", active_sheet="Sheet 1", report_part="action_plan"),
        surface="lab-run",
    )

    assert "auto-analysis" in export_dir.parts
    assert "demo-data-2026" in export_dir.parts
    assert export_dir.name.endswith("-lab-run-Sheet-1-action_plan")
    assert public_base_path.startswith("/storage/auto-analysis/demo-data-2026/")
    assert public_base_path.endswith("-lab-run-Sheet-1-action_plan")
