from __future__ import annotations

import re
import json
from pathlib import Path

from app.models import AutoAnalysisRequest
import app.services.auto_analysis_service as auto_analysis_service


def _same_name_method_packages() -> list[dict]:
    return [
        {
            "package_id": "pkg-1",
            "file_name": "method-package-001.json",
            "method_id": "same_method_a",
            "method_run_id": "run-1",
            "method_name": "Same Method Card",
            "family": "visual",
            "method_card": {"method_name": "Same Method Card", "evidence_refs": ["table:first"]},
            "assets": [{"asset_ref": "asset:first", "evidence_refs": ["chart:first"]}],
            "runtime_handoffs": [{"task": "execute_method_asset:first", "evidence_refs": ["handoff:first"]}],
            "artifact_exports": {"data_csv_path": "method_artifacts/001/data.csv"},
        },
        {
            "package_id": "pkg-2",
            "file_name": "method-package-002.json",
            "method_id": "same_method_b",
            "method_run_id": "run-2",
            "method_name": "Same Method Card",
            "family": "visual",
            "method_card": {"method_name": "Same Method Card", "evidence_refs": ["table:second"]},
            "assets": [{"asset_ref": "asset:second", "evidence_refs": ["chart:second"]}],
            "runtime_handoffs": [{"task": "execute_method_asset:second", "evidence_refs": ["handoff:second"]}],
            "artifact_exports": {"data_csv_path": "method_artifacts/002/data.csv"},
        },
        {
            "package_id": "pkg-3",
            "file_name": "method-package-003.json",
            "method_id": "other_method",
            "method_run_id": "run-3",
            "method_name": "Other Method Card",
            "family": "diagnostic",
            "method_card": {"method_name": "Other Method Card", "evidence_refs": ["table:third"]},
            "assets": [{"asset_ref": "asset:third", "evidence_refs": ["chart:third"]}],
            "runtime_handoffs": [{"task": "execute_method_asset:third", "evidence_refs": ["handoff:third"]}],
            "artifact_exports": {"data_csv_path": "method_artifacts/003/data.csv"},
        },
    ]


def test_method_card_display_collapses_same_name_cards_without_dropping_raw_evidence() -> None:
    request = AutoAnalysisRequest(dataset_id="demo")
    packages = _same_name_method_packages()

    display_packages = auto_analysis_service._method_display_packages(packages)
    display_policy = auto_analysis_service._method_display_policy(packages, display_packages)
    guidance = auto_analysis_service._method_card_report_guidance_list(packages)

    assert len(display_packages) == 2
    assert display_policy["raw_method_package_count"] == 3
    assert display_policy["display_method_package_count"] == 2
    assert display_policy["collapsed_duplicate_run_count"] == 1
    assert display_policy["raw_packages_preserved"] is True
    assert display_packages[0]["display_group"]["total_runs"] == 2
    assert display_packages[0]["display_group"]["collapsed_run_count"] == 1
    assert display_packages[0]["display_group"]["method_run_ids"] == ["run-1", "run-2"]
    assert "Display this repeated method card once" in guidance[0]["writer_action"]

    writer_input = auto_analysis_service._build_report_writer_agent_input(
        request=request,
        dataset_name="Demo Dataset",
        sheet_name="Sheet1",
        selected={},
        field_profiles=[],
        charts=[],
        method_execution_packages=packages,
        external_skill_context=None,
        large_sample_policy=None,
        generated_at="2026-06-02T00:00:00Z",
    )
    assert writer_input["method_package_count"] == 3
    assert writer_input["method_display_package_count"] == 2
    assert len(writer_input["method_package_summaries"]) == 2

    smart_merge_brief = auto_analysis_service._smart_merge_brief_payload(
        request=request,
        dataset_name="Demo Dataset",
        sheet_name="Sheet1",
        selected={},
        method_execution_packages=packages,
        report_part_bundle={},
        report_part_generation_blueprints=[],
        report_part_asset_manifest=[],
        external_skill_context=None,
    )
    assert smart_merge_brief["method_count"] == 3
    assert smart_merge_brief["method_display_count"] == 2
    assert len(smart_merge_brief["method_threads"]) == 2

    markdown = auto_analysis_service._render_lab_report_markdown(
        title="Demo Lab Report",
        request=request,
        dataset_name="Demo Dataset",
        sheet_name="Sheet1",
        selected={},
        report_parts=[],
        tables=[],
        charts=[],
        method_execution_packages=packages,
        method_artifact_summary={"method_count": 3, "integrity_complete_count": 3, "integrity_status": "passed"},
        agent_review={},
        report_part_asset_manifest=[],
        external_skill_context=None,
        generated_at="2026-06-02T00:00:00Z",
    )
    assert "分析方法数：3" in markdown
    assert "已列出方法证据：2/2。" in markdown
    assert len(re.findall(r"(?m)^- 证据 \d{3}:", markdown)) == 2


def test_method_card_display_policy_is_written_to_export_surfaces(tmp_path: Path) -> None:
    packages = _same_name_method_packages()
    downloadables: list[dict] = []

    auto_analysis_service._export_runtime_packages(
        export_dir=tmp_path,
        report_part_bundle={
            "file_name": "report_part_bundle.json",
            "requested_report_parts": ["method_note"],
            "generated_part_ids": ["method_note"],
            "generation_blueprints": [],
        },
        method_execution_packages=packages,
        downloadables=downloadables,
        method_artifact_summary={"method_count": 3, "integrity_status": "passed"},
        chart_asset_summary={"chart_count": 0, "integrity_status": "passed"},
        external_skill_context=None,
        large_sample_policy=None,
        public_base_path="/storage/auto-analysis/demo/run-display-policy",
    )
    writer_input = auto_analysis_service._build_report_writer_agent_input(
        request=AutoAnalysisRequest(dataset_id="demo"),
        dataset_name="Demo Dataset",
        sheet_name="Sheet1",
        selected={},
        field_profiles=[],
        charts=[],
        method_execution_packages=packages,
        external_skill_context=None,
        large_sample_policy=None,
        generated_at="2026-06-02T00:00:00Z",
    )
    markdown = auto_analysis_service._render_lab_report_markdown(
        title="Demo Lab Report",
        request=AutoAnalysisRequest(dataset_id="demo"),
        dataset_name="Demo Dataset",
        sheet_name="Sheet1",
        selected={},
        report_parts=[],
        tables=[],
        charts=[],
        method_execution_packages=packages,
        method_artifact_summary={"method_count": 3, "integrity_complete_count": 3, "integrity_status": "passed"},
        agent_review={},
        report_part_asset_manifest=[],
        external_skill_context=None,
        generated_at="2026-06-02T00:00:00Z",
    )

    (tmp_path / "report_writer_agent_input.json").write_text(json.dumps(writer_input, ensure_ascii=False), encoding="utf-8")
    (tmp_path / "lab_report.md").write_text(markdown, encoding="utf-8")

    runtime_manifest = json.loads((tmp_path / "runtime_package_manifest.json").read_text(encoding="utf-8"))
    raw_package_index = json.loads((tmp_path / "method_execution_packages.json").read_text(encoding="utf-8"))
    written_writer_input = json.loads((tmp_path / "report_writer_agent_input.json").read_text(encoding="utf-8"))
    written_markdown = (tmp_path / "lab_report.md").read_text(encoding="utf-8")

    assert len(raw_package_index) == 3
    assert runtime_manifest["method_package_count"] == 3
    assert runtime_manifest["method_display_package_count"] == 2
    assert runtime_manifest["method_display_policy"]["collapsed_duplicate_run_count"] == 1
    assert written_writer_input["method_package_count"] == 3
    assert written_writer_input["method_display_package_count"] == 2
    assert written_writer_input["method_display_policy"]["raw_packages_preserved"] is True
    assert "分析方法数：3" in written_markdown
    assert "已列出方法证据：2/2。" in written_markdown
    assert len(re.findall(r"(?m)^- 证据 \d{3}:", written_markdown)) == 2
    assert {item["name"] for item in downloadables} >= {
        "runtime_package_manifest.json",
        "method_execution_packages.json",
        "external_skill_context.json",
    }
