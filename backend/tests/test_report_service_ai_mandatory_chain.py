from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from app.models import SmartReportRequest
from app.services import report_service as report_service_module
from app.services.report_service import generate_smart_report


@pytest.fixture(autouse=True)
def _isolate_report_outputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(report_service_module, "REPORTS_DIR", tmp_path / "reports")


def _write(path: Path, payload: dict | str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, str):
        path.write_text(payload, encoding="utf-8")
    else:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _fake_orchestration_factory(
    *,
    ai_passed: bool,
    failure_code: str = "",
    failure_reason: str = "",
    include_trace: bool = True,
    include_metric_result: bool = True,
    old_router_profile: str = "generic_business_report",
    business_profile: str = "generic_business_report",
    report_lens: str = "mixed_business_review",
    include_runtime_fields: bool = False,
):
    calls: dict[str, Path] = {}

    def _fake(dataset_id: str, request: SmartReportRequest, *, ai_trace_output_dir=None):
        report_dir = Path(ai_trace_output_dir)
        calls["report_dir"] = report_dir
        if include_trace:
            _write(
                report_dir / "outputs" / "ai_traces" / "ai_field_semantic_mapping.json",
                {
                    "inferred_business_context": "test",
                    "object_grain": "sku",
                    "time_grain": "day",
                    "field_mappings": [],
                    "uncertain_fields": [],
                    "provider": "OpenAI",
                    "model": "gpt-5.4",
                    "trace_id": "trace-semantic-001",
                },
            )
            _write(
                report_dir / "outputs" / "ai_traces" / "ai_business_routing.json",
                {
                    "selected_by_user": None,
                    "ai_route": "ecommerce_product_operations_report",
                    "final_route": "ecommerce_product_operations_report",
                    "confidence": 0.92,
                    "alternative_routes": [],
                    "reason": "test route",
                    "blocked_routes": [],
                    "trace_id": "trace-route-001",
                },
            )
            _write(
                report_dir / "outputs" / "ai_traces" / "ai_metric_derivation_plan.json",
                {
                    "available_metrics": ["gmv"],
                    "unavailable_metrics": [],
                    "proxy_metrics": [],
                    "diagnostic_questions": [],
                    "metric_plans": [],
                    "provider": "OpenAI",
                    "model": "gpt-5.4",
                    "trace_id": "trace-plan-001",
                },
            )
        if include_metric_result:
            _write(
                report_dir / "outputs" / "metric_mining" / "semantic_metric_result.json",
                {
                    "trace_id": "trace-plan-001",
                    "results": [
                        {
                            "metric_id": "gmv",
                            "metric_name_cn": "GMV",
                            "value": 123.0,
                            "status": "calculated",
                            "calculation_method": "sum(gmv)",
                            "evidence_level": "A_DIRECT",
                        }
                    ],
                },
            )
            _write(
                report_dir / "outputs" / "metric_mining" / "metric_derivation_log.csv",
                "metric_id,status\nGMV,calculated\n",
            )
        gate_payload = {
            "passed": ai_passed,
            "formal_pdf_allowed": ai_passed,
            "failure_code": failure_code,
            "failure_reason": failure_reason,
            "failure_reasons": [failure_reason] if failure_reason else [],
        }
        _write(report_dir / "outputs" / "quality" / "ai_usage_gate_result.json", gate_payload)

        payload = {
            "metadata": {
                "name": "test-dataset",
                "active_sheet": "Sheet1",
                "sheets": [{"name": "Sheet1"}],
            },
            "selected_sheet_names": ["Sheet1"],
            "multi_mode": "single",
            "business_profile_router": {
                "business_profile": old_router_profile,
                "profile_entrypoint": "generic_business_report_profile",
                "report_lens": report_lens,
            },
            "ai_mandatory": {
                "passed": ai_passed,
                "formal_pdf_allowed": ai_passed,
                "failure_code": failure_code,
                "failure_reason": failure_reason,
                "quality_gate_path": str((report_dir / "outputs" / "quality" / "ai_usage_gate_result.json").resolve()),
                "ai_usage_gate_result": gate_payload,
                "semantic_metric_result": {
                    "results": [
                        {
                            "metric_id": "gmv",
                            "metric_name_cn": "GMV",
                            "value": 123.0,
                            "status": "calculated",
                            "calculation_method": "sum(gmv)",
                            "evidence_level": "A_DIRECT",
                        }
                    ]
                }
                if include_metric_result
                else {},
                "semantic_metric_result_path": str((report_dir / "outputs" / "metric_mining" / "semantic_metric_result.json").resolve())
                if include_metric_result
                else "",
                "metric_derivation_log_path": str((report_dir / "outputs" / "metric_mining" / "metric_derivation_log.csv").resolve())
                if include_metric_result
                else "",
                "router_result": {
                    "business_profile": business_profile,
                    "profile_entrypoint": "ecommerce_product_operations_report_profile",
                    "report_lens": report_lens,
                    "final_route": "ecommerce_product_operations_report",
                },
            },
        }
        if include_runtime_fields:
            payload.update(
                {
                    "frame": __import__("pandas").DataFrame({"value": [1]}),
                    "sheet": {"name": "Sheet1"},
                    "request": SmartReportRequest(),
                    "program_bundle": {},
                    "blueprint": {
                        "sheet_profiles": [{"name": "Sheet1", "role": "analytical_fact"}],
                        "relationships": [],
                        "quality_score": 88,
                        "complexity_score": 42,
                    },
                    "statistical_scope": {"keep_numeric_columns": [], "exclude_numeric_columns": []},
                    "market_intelligence": {},
                    "execution_steps": [],
                    "thinking_steps": [],
                }
            )
        return payload

    return _fake, calls


def test_report_service_calls_ai_mandatory_chain(tmp_path: Path) -> None:
    fake, calls = _fake_orchestration_factory(
        ai_passed=False,
        failure_code="AI_USAGE_GATE_FAILED",
        failure_reason="trace missing",
    )
    with patch("app.services.report_service.build_report_orchestration", side_effect=fake):
        result = generate_smart_report("demo", SmartReportRequest())
    assert calls["report_dir"].name.startswith("smart-report-")
    assert (calls["report_dir"] / "outputs" / "quality" / "ai_usage_gate_result.json").exists()
    assert result["failure_code"] == "AI_USAGE_GATE_FAILED"


def test_report_service_blocks_pdf_when_ai_unavailable(tmp_path: Path) -> None:
    fake, _ = _fake_orchestration_factory(
        ai_passed=False,
        failure_code="AI_REQUIRED_BUT_UNAVAILABLE",
        failure_reason="AI unavailable",
    )
    with patch("app.services.report_service.build_report_orchestration", side_effect=fake):
        result = generate_smart_report("demo", SmartReportRequest())
    download_names = [item["name"] for item in result["downloadables"]]
    assert not any("management_report.pdf" in name for name in download_names)
    assert result["failure_code"] == "AI_REQUIRED_BUT_UNAVAILABLE"
    assert result["main_downloadable"]["name"].endswith("debug_report.pdf")


def test_report_service_blocks_pdf_when_ai_trace_missing(tmp_path: Path) -> None:
    fake, _ = _fake_orchestration_factory(
        ai_passed=False,
        failure_code="AI_USAGE_GATE_FAILED",
        failure_reason="ai_field_semantic_mapping.json missing",
        include_trace=False,
    )
    with patch("app.services.report_service.build_report_orchestration", side_effect=fake):
        result = generate_smart_report("demo", SmartReportRequest())
    download_names = [item["name"] for item in result["downloadables"]]
    assert not any("management_report.pdf" in name for name in download_names)
    assert result["formal_pdf_allowed"] is False


def test_report_service_does_not_fallback_to_old_router_for_formal_pdf(tmp_path: Path) -> None:
    fake, _ = _fake_orchestration_factory(
        ai_passed=False,
        failure_code="AI_USAGE_GATE_FAILED",
        failure_reason="AI mandatory failed",
        old_router_profile="procurement_sales_report",
    )
    with patch("app.services.report_service.build_report_orchestration", side_effect=fake), patch(
        "app.services.report_service._downloadable_bundle_cn_procurement",
        side_effect=AssertionError("formal renderer should not run"),
    ):
        result = generate_smart_report("demo", SmartReportRequest())
    assert result["release_blocked"] is True
    assert result["failure_code"] == "AI_USAGE_GATE_FAILED"


def test_report_service_uses_semantic_metric_result(tmp_path: Path) -> None:
    fake, calls = _fake_orchestration_factory(
        ai_passed=False,
        failure_code="AI_USAGE_GATE_FAILED",
        failure_reason="blocked for test",
        include_metric_result=True,
    )
    with patch("app.services.report_service.build_report_orchestration", side_effect=fake):
        result = generate_smart_report("demo", SmartReportRequest())
    download_names = [item["name"] for item in result["downloadables"]]
    assert "semantic_metric_result.json" in download_names
    assert "metric_derivation_log.csv" in download_names


def test_ai_mandatory_debug_report_uses_tables(tmp_path: Path) -> None:
    fake, _ = _fake_orchestration_factory(
        ai_passed=False,
        failure_code="AI_USAGE_GATE_FAILED",
        failure_reason="trace missing",
        include_metric_result=True,
    )
    with patch("app.services.report_service.build_report_orchestration", side_effect=fake):
        result = generate_smart_report("demo", SmartReportRequest())
    assert "| 检查项 |" in result["report_markdown"]
    assert "| 失败原因 |" in result["report_markdown"]


def test_media_campaign_report_uses_dedicated_bundle_branch(tmp_path: Path) -> None:
    report_dir = tmp_path / "media"
    report_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "report_id": "media-test",
        "title": "media report",
        "dataset_name": "demo",
        "sheet_name": "Sheet1",
        "generated_at": "2026-04-27T00:00:00Z",
        "report_language": "zh-CN",
        "business_profile": "media_campaign_report",
        "report_lens": "media_review",
        "executive_summary": ["summary"],
        "sections": [],
        "universal_metric_mining_result": {},
    }
    bundle = report_service_module._downloadable_bundle_cn_media(report_dir, "media-test", report, __import__("pandas").DataFrame({"value": [1]}), {})
    download_names = [item["name"] for item in bundle["downloadables"]]
    assert "media-test-quality_gate_result.json" in download_names
    assert "media-test-report_quality_score.json" in download_names


def test_insufficient_profile_uses_dedicated_bundle_branch(tmp_path: Path) -> None:
    report_dir = tmp_path / "insufficient"
    report_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "report_id": "insufficient-test",
        "title": "insufficient report",
        "dataset_name": "demo",
        "sheet_name": "Sheet1",
        "generated_at": "2026-04-27T00:00:00Z",
        "report_language": "zh-CN",
        "business_profile": "insufficient_for_management_decision",
        "report_lens": "mixed_business_review",
        "executive_summary": ["summary"],
        "sections": [],
        "universal_metric_mining_result": {},
    }
    bundle = report_service_module._downloadable_bundle_cn_insufficient(report_dir, "insufficient-test", report, __import__("pandas").DataFrame({"value": [1]}), {})
    download_names = [item["name"] for item in bundle["downloadables"]]
    assert "insufficient-test-quality_gate_result.json" in download_names
    assert "insufficient-test-report_quality_score.json" in download_names


def test_current_turn_export_manifest_is_exposed(tmp_path: Path) -> None:
    fake, _ = _fake_orchestration_factory(
        ai_passed=False,
        failure_code="AI_USAGE_GATE_FAILED",
        failure_reason="blocked for test",
        include_metric_result=True,
    )
    with patch("app.services.report_service.build_report_orchestration", side_effect=fake):
        result = generate_smart_report("demo", SmartReportRequest())
    download_names = [item["name"] for item in result["downloadables"]]
    assert any(name.endswith("current_turn_export_manifest.json") for name in download_names)
