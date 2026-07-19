from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from app.services import report_service as report_service_module
from app.services import runtime_process_service as runtime_process_service_module


@pytest.fixture
def isolated_report_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(report_service_module, "REPORTS_DIR", reports_dir)
    monkeypatch.setattr(runtime_process_service_module, "REPORTS_DIR", reports_dir)
    return reports_dir


def test_completed_report_cli_bootstrap_accepts_xlsx_plus_existing_report(isolated_report_dirs: Path) -> None:
    report_id = "retrofit-xlsx-001"
    report_dir = isolated_report_dirs / f"smart-report-{report_id}"
    report_dir.mkdir(parents=True, exist_ok=True)

    source_frame = pd.DataFrame(
        {
            "order_id": [f"o-{index}" for index in range(12)],
            "gmv": [100 + index * 5 for index in range(12)],
            "category": ["A", "B", "C"] * 4,
            "city": ["HZ", "SH", "SZ"] * 4,
        }
    )
    source_frame.to_excel(report_dir / f"{report_id}.xlsx", index=False, sheet_name="tableau_extract")

    workbook_report_sheet = pd.DataFrame({"关键决策问题": ["要不要扩品", "要不要调价", "要不要加投"]})
    with pd.ExcelWriter(report_dir / f"{report_id}-report-export.xlsx", engine="openpyxl") as writer:
        workbook_report_sheet.to_excel(writer, index=False, sheet_name="business_j_关键决策问题")
        pd.DataFrame({"优先级": ["P1"], "动作": ["聚焦高毛利品类"]}).to_excel(
            writer,
            index=False,
            sheet_name="decision_d_决策路线图",
        )

    (report_dir / f"{report_id}.md").write_text("# 存量报告\n\n这里是已有报告正文。", encoding="utf-8")

    source_assets = report_service_module._scan_retrofit_source_assets(report_dir, report_id)
    bootstrap = runtime_process_service_module._completed_report_cli_bootstrap_status(report_id)
    frame, source_metadata = report_service_module._load_retrofit_frame(report_dir, report_id, source_assets)

    assert source_assets["can_retrofit_cli"] is True
    assert source_assets["primary_csv_available"] is True
    assert bootstrap["can_start_generic_long_cli"] is True
    assert bootstrap["missing_required_assets"] == []
    assert frame.shape == (12, 4)
    assert source_metadata["source_kind"] == "report_tabular_asset"
    assert source_metadata["source_file_format"] == "xlsx"
    assert source_metadata["sheet_name"] == "tableau_extract"
    assert source_metadata["source_dataset_degraded"] is False
    assert source_metadata["missing_required_assets"] == []


def test_completed_report_cli_bootstrap_falls_back_to_text_when_only_report_workbook_exists(isolated_report_dirs: Path) -> None:
    report_id = "retrofit-text-001"
    report_dir = isolated_report_dirs / f"smart-report-{report_id}"
    report_dir.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(report_dir / f"{report_id}.xlsx", engine="openpyxl") as writer:
        pd.DataFrame({"关键决策问题": ["问题一", "问题二", "问题三"]}).to_excel(
            writer,
            index=False,
            sheet_name="business_j_关键决策问题",
        )
        pd.DataFrame({"优先级": ["P1"], "动作": ["继续观察"]}).to_excel(
            writer,
            index=False,
            sheet_name="decision_d_决策路线图",
        )

    (report_dir / f"{report_id}.md").write_text("# 存量报告\n\n已有报告仍可作为续跑证据。", encoding="utf-8")

    source_assets = report_service_module._scan_retrofit_source_assets(report_dir, report_id)
    bootstrap = runtime_process_service_module._completed_report_cli_bootstrap_status(report_id)
    frame, source_metadata = report_service_module._load_retrofit_frame(report_dir, report_id, source_assets)

    assert source_assets["can_retrofit_cli"] is True
    assert source_assets["primary_csv_available"] is False
    assert "original_source_dataset" in source_assets["missing_required_assets"]
    assert bootstrap["can_start_generic_long_cli"] is True
    assert frame.shape[0] >= 1
    assert source_metadata["source_kind"] == "report_text_inventory"
    assert source_metadata["source_dataset_degraded"] is True
    assert "original_source_dataset" in source_metadata["missing_required_assets"]
