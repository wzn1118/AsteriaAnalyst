from __future__ import annotations

import copy
import json
from pathlib import Path

import pandas as pd
import pytest

from app.models import SmartReportRequest
from app.services import codex_runtime_pipeline_service as pipeline_service_module
from app.services import report_service as report_service_module
from app.services.codex_runtime_pipeline_service import create_pipeline_job
from app.services.codex_runtime_prompt_templates import (
    build_derived_metric_family_planning_prompt,
    build_ecommerce_delivery_consistency_audit_prompt,
    build_ecommerce_frontline_workorder_prompt,
    build_ecommerce_metric_consistency_audit_prompt,
    build_ecommerce_long_outline_prompt,
    build_ecommerce_section_batch_prompt,
)
from app.services.derived_metric_family_execution_service import execute_derived_metric_family_specs
from app.services.report_service import (
    _append_current_turn_export_manifest,
    _prepare_ecommerce_long_cli_workspace,
    register_ecommerce_long_cli_pipeline_output,
)


@pytest.fixture(autouse=True)
def _isolate_report_outputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(report_service_module, "REPORTS_DIR", tmp_path / "reports")


def _frame() -> pd.DataFrame:
    rows = []
    for index in range(24):
        rows.append(
            {
                "item_id": f"item-{index % 6}",
                "sku_id": f"sku-{index % 10}",
                "shop_id": f"shop-{index % 3}",
                "brand": f"brand-{index % 4}",
                "category": ["鎶よ偆", "鎵嬫満", "瀹舵竻", "鏈嶉グ"][index % 4],
                "price": 49 + index,
                "sales_volume": 10 + index,
                "GMV": 500 + index * 30,
                "order_count": 5 + (index % 7),
                "inventory": 20 + (index % 9),
                "refund_rate": 0.01 + (index % 3) * 0.01,
                "rating": 4.2 + (index % 4) * 0.1,
                "PV": 300 + index * 10,
                "UV": 120 + index * 5,
                "click": 35 + index,
                "pay": 6 + (index % 5),
                "gross_margin": 0.12 + (index % 4) * 0.03,
                "date": f"2026-05-{(index % 9) + 1:02d}",
            }
        )
    return pd.DataFrame(rows)


def _runtime_cli_frame() -> pd.DataFrame:
    rows = []
    for index in range(18):
        revenue = 120 + index * 11
        freight = 8 + (index % 5) * 1.5
        rows.append(
            {
                "OrderID": f"order-{index // 2}",
                "OrderPurchaseTimestamp": f"2026-05-{(index % 6) + 1:02d}",
                "DeliveredCustomerDate": f"2026-05-{(index % 6) + 3:02d}",
                "EstimatedDeliveryDate": f"2026-05-{(index % 6) + 4:02d}",
                "OrderStatus": "delivered" if index % 4 else "shipped",
                "Category": ["health_beauty", "housewares", "sports_leisure"][index % 3],
                "Product": f"product-{index % 7}",
                "SKU": f"sku-{index % 9}",
                "Seller": f"seller-{index % 4}",
                "SellerState": ["SP", "RJ", "MG"][index % 3],
                "CustomerState": ["BA", "SP", "PR"][index % 3],
                "Revenue": revenue,
                "FreightCost": freight,
                "GMV": revenue + freight,
                "Quantity": 1 + (index % 3),
                "ReviewScore": 5 - (index % 3),
                "DelayDays": index % 4,
                "IsLate": 1 if index % 4 else 0,
            }
        )
    return pd.DataFrame(rows)


def _request(*, use_r_workflow: bool = False) -> SmartReportRequest:
    return SmartReportRequest(
        sheet_name="Sheet1",
        business_profile="ecommerce_product_operations_report",
        report_style="deep_dive",
        user_requirement="鍋氫竴浠界數鍟嗙粡钀ユ繁搴︽姤鍛婏紝鍏虫敞鍟嗗搧銆佺被鐩€佸簵閾恒€佽浆鍖栥€佸簱瀛樺拰姣涘埄銆?",
        problem_to_solve="璇嗗埆鐢靛晢缁忚惀闂鍜屾湰鏈熷姩浣滀紭鍏堢骇銆?",
        target_audience="绠＄悊灞?",
        core_purpose="缁忚惀璇婃柇",
        expected_result="鐢靛晢娣卞害绠＄悊鎶ュ憡",
        use_r_workflow=use_r_workflow,
    )


def _report(report_id: str = "ecomshadow01") -> dict[str, object]:
    return {
        "report_id": report_id,
        "dataset_name": "鐢靛晢娴嬭瘯鏁版嵁闆?",
        "sheet_name": "Sheet1",
        "business_profile": "ecommerce_product_operations_report",
        "report_lens": "procurement_sales_review",
        "ecommerce_field_availability_registry": {
            "report_mode": "full_ecommerce_management",
            "available_field_groups": ["product_fields", "category_fields", "transaction_fields"],
        },
        "ecommerce_field_semantic_map": {
            "subject_type": "ecommerce_product_operations",
            "important_columns": ["item_id", "category", "GMV", "sales_volume"],
        },
        "product_operations_analysis_modules": {
            "product_performance_analyzer": {
                "business_question": "鍝簺鍟嗗搧鍊煎緱浼樺厛杩借釜锛?",
                "key_findings": ["澶撮儴鍟嗗搧璐＄尞鏄庢樉"],
                "recommended_actions": ["澶嶆牳澶撮儴鍟嗗搧鍔ㄤ綔"],
            }
        },
        "ecommerce_object_decision_registry": {
            "rows": [{"object_level": "product", "object_name": "鍟嗗搧姹?", "final_action": "澶嶆牳"}]
        },
        "ecommerce_action_table": [{"priority": "P1", "action": "鍏堝鏍稿ご閮ㄥ晢鍝佹睜"}],
        "ecommerce_action_roadmap": {
            "seven_day_ecommerce_action_table": [{"owner": "商品运营", "action": "复核头部商品池"}]
        },
        "metric_mining_output_files": {
            "derived_metrics_table.csv": "outputs/metric_mining/derived_metrics_table.csv",
            "proxy_metrics_table.csv": "outputs/metric_mining/proxy_metrics_table.csv",
            "universal_metric_mining_result.json": "outputs/metric_mining/universal_metric_mining_result.json",
            "semantic_metric_result.json": "outputs/metric_mining/semantic_metric_result.json",
        },
    }


def _seed_report_dir(report_dir: Path, report_id: str) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / f"{report_id}-management_report.md").write_text("# management\n\ncontent", encoding="utf-8")
    (report_dir / f"{report_id}-management_report.html").write_text("<html>management</html>", encoding="utf-8")
    (report_dir / f"{report_id}-analyst_appendix.md").write_text("# appendix\n\ncontent", encoding="utf-8")
    (report_dir / f"{report_id}-analyst_appendix.html").write_text("<html>appendix</html>", encoding="utf-8")
    (report_dir / f"{report_id}.md").write_text("# full\n\ncontent", encoding="utf-8")
    (report_dir / f"{report_id}.html").write_text("<html>full</html>", encoding="utf-8")
    metric_dir = report_dir / "outputs" / "metric_mining"
    metric_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "business_profile": "ecommerce_product_operations_report",
                "metric_id": "cpm_derived",
                "metric_name": "千次触达成本参考指标",
                "source_columns": "['FreightCost', 'ReviewScore']",
                "formula": "FreightCost * 1000 / ReviewScore",
                "value": "4118.9203",
                "evidence_level": "B_DERIVED",
                "confidence": "high",
                "metric_kind": "derived_metric",
                "business_meaning": "鍙敤浜庡垽鏂洕鍏夎幏鍙栨垚鏈€?",
                "note": "",
            },
            {
                "business_profile": "ecommerce_product_operations_report",
                "metric_id": "top_object_amount_contribution",
                "metric_name": "瀵硅薄閲戦璐＄尞",
                "source_columns": "['Category', 'Revenue']",
                "formula": "top1(sum(Revenue) by Category) / sum(Revenue)",
                "value": "0.2004",
                "evidence_level": "B_DERIVED",
                "confidence": "medium",
                "metric_kind": "derived_metric",
                "business_meaning": "瀵硅薄閲戦璐＄尞鍙敤浜庡垽鏂泦涓害銆?",
                "note": "",
            },
        ]
    ).to_csv(metric_dir / "derived_metrics_table.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(
        [
            {
                "business_profile": "ecommerce_product_operations_report",
                "metric_id": "quality_proxy",
                "metric_name": "鍟嗗搧璐ㄩ噺浠ｇ悊",
                "source_columns": "['ReviewScore']",
                "formula": "mean(ReviewScore)",
                "value": "4.308",
                "evidence_level": "C_PROXY",
                "confidence": "medium",
                "metric_kind": "proxy_metric",
                "business_meaning": "璇勪环鍒嗗彲浣滀负璐ㄩ噺鍜屽敭鍚庝綋楠岀殑浠ｇ悊淇″彿銆?",
                "note": "",
            }
        ]
    ).to_csv(metric_dir / "proxy_metrics_table.csv", index=False, encoding="utf-8-sig")
    (metric_dir / "universal_metric_mining_result.json").write_text(
        json.dumps(
            {
                "derived_metrics": [
                    {
                        "metric_id": "cpm_derived",
                        "metric_name": "鍗冩瑙﹁揪鎴愭湰鍙傝€冩寚鏍?",
                        "source_columns": ["FreightCost", "ReviewScore"],
                        "formula": "FreightCost * 1000 / ReviewScore",
                        "value": "4118.9203",
                        "evidence_level": "B_DERIVED",
                        "confidence": "high",
                        "metric_kind": "derived_metric",
                        "business_meaning": "鍙敤浜庡垽鏂洕鍏夎幏鍙栨垚鏈€?",
                    },
                    {
                        "metric_id": "top_object_amount_contribution",
                        "metric_name": "瀵硅薄閲戦璐＄尞",
                        "source_columns": ["Category", "Revenue"],
                        "formula": "top1(sum(Revenue) by Category) / sum(Revenue)",
                        "value": "0.2004",
                        "evidence_level": "B_DERIVED",
                        "confidence": "medium",
                        "metric_kind": "derived_metric",
                        "business_meaning": "瀵硅薄閲戦璐＄尞鍙敤浜庡垽鏂泦涓害銆?",
                    },
                ],
                "proxy_metrics": [
                    {
                        "metric_id": "quality_proxy",
                        "metric_name": "鍟嗗搧璐ㄩ噺浠ｇ悊",
                        "source_columns": ["ReviewScore"],
                        "formula": "mean(ReviewScore)",
                        "value": "4.308",
                        "evidence_level": "C_PROXY",
                        "confidence": "medium",
                        "metric_kind": "proxy_metric",
                        "business_meaning": "璇勪环鍒嗗彲浣滀负璐ㄩ噺鍜屽敭鍚庝綋楠岀殑浠ｇ悊淇″彿銆?",
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (metric_dir / "semantic_metric_result.json").write_text("{}", encoding="utf-8")
    r_dir = report_dir / "r-workflow"
    r_dir.mkdir(parents=True, exist_ok=True)
    (r_dir / "r_summary.csv").write_text("metric,value\nGMV,100\n", encoding="utf-8")


def _seed_metric_mining_workspace(workspace: Path) -> None:
    metric_dir = workspace / "metric_mining"
    metric_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "business_profile": "ecommerce_product_operations_report",
                "metric_id": "cpm_derived",
                "metric_name": "千次触达成本参考指标",
                "source_columns": "['FreightCost', 'ReviewScore']",
                "formula": "FreightCost * 1000 / ReviewScore",
                "value": "4118.9203",
                "evidence_level": "B_DERIVED",
                "confidence": "high",
                "metric_kind": "derived_metric",
                "business_meaning": "鍙敤浜庡垽鏂洕鍏夎幏鍙栨垚鏈€?",
                "note": "",
            },
            {
                "business_profile": "ecommerce_product_operations_report",
                "metric_id": "cpa_derived",
                "metric_name": "单次转化成本参考指标",
                "source_columns": "['FreightCost', 'OrderPurchaseTimestamp']",
                "formula": "FreightCost / OrderPurchaseTimestamp",
                "value": "0",
                "evidence_level": "B_DERIVED",
                "confidence": "high",
                "metric_kind": "derived_metric",
                "business_meaning": "鍙敤浜庡垽鏂崟娆¤浆鍖栨垚鏈€?",
                "note": "",
            },
            {
                "business_profile": "ecommerce_product_operations_report",
                "metric_id": "top_object_amount_contribution",
                "metric_name": "瀵硅薄閲戦璐＄尞",
                "source_columns": "['Category', 'Revenue']",
                "formula": "top1(sum(Revenue) by Category) / sum(Revenue)",
                "value": "0.2004",
                "evidence_level": "B_DERIVED",
                "confidence": "medium",
                "metric_kind": "derived_metric",
                "business_meaning": "瀵硅薄閲戦璐＄尞鍙敤浜庡垽鏂泦涓害銆?",
                "note": "",
            },
            {
                "business_profile": "ecommerce_product_operations_report",
                "metric_id": "overall_trend_change",
                "metric_name": "瓒嬪娍鍙樺寲",
                "source_columns": "['Category', 'DeliveredCustomerDate', 'Revenue']",
                "formula": "last(sum(Revenue) by DeliveredCustomerDate) / first(sum(Revenue) by DeliveredCustomerDate) - 1",
                "value": "2.7966",
                "evidence_level": "B_DERIVED",
                "confidence": "medium",
                "metric_kind": "derived_metric",
                "business_meaning": "鍙敤浜庡垽鏂秼鍔垮彉鍖栥€?",
                "note": "",
            },
        ]
    ).to_csv(metric_dir / "derived_metrics_table.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(
        [
            {
                "business_profile": "ecommerce_product_operations_report",
                "metric_id": "quality_proxy",
                "metric_name": "鍟嗗搧璐ㄩ噺浠ｇ悊",
                "source_columns": "['ReviewScore']",
                "formula": "mean(ReviewScore)",
                "value": "4.308",
                "evidence_level": "C_PROXY",
                "confidence": "medium",
                "metric_kind": "proxy_metric",
                "business_meaning": "璇勪环鍒嗗彲浣滀负璐ㄩ噺鍜屽敭鍚庝綋楠岀殑浠ｇ悊淇″彿銆?",
                "note": "",
            }
        ]
    ).to_csv(metric_dir / "proxy_metrics_table.csv", index=False, encoding="utf-8-sig")
    (metric_dir / "universal_metric_mining_result.json").write_text(
        json.dumps(
            {
                "derived_metrics": [
                    {
                        "metric_id": "cpm_derived",
                        "metric_name": "千次触达成本参考指标",
                        "source_columns": ["FreightCost", "ReviewScore"],
                        "formula": "FreightCost * 1000 / ReviewScore",
                        "value": "4118.9203",
                        "evidence_level": "B_DERIVED",
                        "confidence": "high",
                        "metric_kind": "derived_metric",
                        "business_meaning": "鍙敤浜庡垽鏂洕鍏夎幏鍙栨垚鏈€?",
                    },
                    {
                        "metric_id": "cpa_derived",
                        "metric_name": "单次转化成本参考指标",
                        "source_columns": ["FreightCost", "OrderPurchaseTimestamp"],
                        "formula": "FreightCost / OrderPurchaseTimestamp",
                        "value": "0",
                        "evidence_level": "B_DERIVED",
                        "confidence": "high",
                        "metric_kind": "derived_metric",
                        "business_meaning": "鍙敤浜庡垽鏂崟娆¤浆鍖栨垚鏈€?",
                    },
                    {
                        "metric_id": "top_object_amount_contribution",
                        "metric_name": "瀵硅薄閲戦璐＄尞",
                        "source_columns": ["Category", "Revenue"],
                        "formula": "top1(sum(Revenue) by Category) / sum(Revenue)",
                        "value": "0.2004",
                        "evidence_level": "B_DERIVED",
                        "confidence": "medium",
                        "metric_kind": "derived_metric",
                        "business_meaning": "瀵硅薄閲戦璐＄尞鍙敤浜庡垽鏂泦涓害銆?",
                    },
                    {
                        "metric_id": "overall_trend_change",
                        "metric_name": "瓒嬪娍鍙樺寲",
                        "source_columns": ["Category", "DeliveredCustomerDate", "Revenue"],
                        "formula": "last(sum(Revenue) by DeliveredCustomerDate) / first(sum(Revenue) by DeliveredCustomerDate) - 1",
                        "value": "2.7966",
                        "evidence_level": "B_DERIVED",
                        "confidence": "medium",
                        "metric_kind": "derived_metric",
                        "business_meaning": "鍙敤浜庡垽鏂秼鍔垮彉鍖栥€?",
                    },
                ],
                "proxy_metrics": [
                    {
                        "metric_id": "quality_proxy",
                        "metric_name": "鍟嗗搧璐ㄩ噺浠ｇ悊",
                        "source_columns": ["ReviewScore"],
                        "formula": "mean(ReviewScore)",
                        "value": "4.308",
                        "evidence_level": "C_PROXY",
                        "confidence": "medium",
                        "metric_kind": "proxy_metric",
                        "business_meaning": "璇勪环鍒嗗彲浣滀负璐ㄩ噺鍜屽敭鍚庝綋楠岀殑浠ｇ悊淇″彿銆?",
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (metric_dir / "semantic_metric_result.json").write_text("{}", encoding="utf-8")


def test_ecommerce_pipeline_stage_order_matches_shadow_contract() -> None:
    stage_ids = [
        stage["stage_id"]
        for stage in pipeline_service_module._default_stage_order("ecommerce_long_cli_pipeline")
    ]
    assert stage_ids == [
        "requirement_intent",
        "ecommerce_table_fact_pack",
        "derived_metric_family_input_pack",
        "derived_metric_family_planning",
        "derived_metric_family_execution",
        "ecommerce_metric_consumption_pack",
        "ecommerce_inventory",
        "ecommerce_question_tree",
        "ecommerce_long_outline",
        "ecommerce_section_batch_01",
        "ecommerce_section_batch_02",
        "ecommerce_section_batch_03",
        "ecommerce_section_batch_04",
        "ecommerce_report_assembly",
        "ecommerce_metric_consistency_audit",
        "ecommerce_data_utilization_gate",
        "metric_chart_planning",
        "metric_chart_render",
        "ecommerce_chart_insights",
        "ecommerce_html_css_package",
        "ecommerce_review",
        "ecommerce_frontline_workorder_pack",
        "ecommerce_delivery_consistency_audit",
        "ecommerce_pdf_render",
    ]


def test_ecommerce_pipeline_stage_titles_are_chinese_reader_facing() -> None:
    stages = pipeline_service_module._default_stage_order("ecommerce_long_cli_pipeline")
    assert all(any("\u4e00" <= char <= "\u9fff" for char in str(stage.get("title") or "")) for stage in stages)
    assert [stage["stage_id"] for stage in stages][:5] == [
        "requirement_intent",
        "ecommerce_table_fact_pack",
        "derived_metric_family_input_pack",
        "derived_metric_family_planning",
        "derived_metric_family_execution",
    ]


def test_create_pipeline_job_accepts_ecommerce_pipeline_type(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, object] = {}

    def _fake_create_manifest(payload: dict[str, object]) -> dict[str, object]:
        captured.update(payload)
        return payload

    monkeypatch.setattr(pipeline_service_module, "create_pipeline_manifest", _fake_create_manifest)
    manifest = create_pipeline_job(
        pipeline_type="ecommerce_long_cli_pipeline",
        workspace_path=str(tmp_path / "{pipeline_job_id}"),
        linked_report_id="report-001",
        context_payload={"business_profile": "ecommerce_product_operations_report"},
        auto_start=False,
    )

    assert manifest["pipeline_type"] == "ecommerce_long_cli_pipeline"
    assert str(manifest["workspace_path"]).startswith(str(tmp_path))
    assert any(stage["stage_id"] == "ecommerce_inventory" for stage in manifest["stage_order"])
    assert captured["linked_report_id"] == "report-001"


def test_prepare_ecommerce_workspace_writes_required_bundle(tmp_path: Path) -> None:
    report_id = "ecomshadow01"
    report_dir = tmp_path / "smart-report-ecomshadow01"
    workspace_dir = tmp_path / "workspace"
    _seed_report_dir(report_dir, report_id)

    copied = _prepare_ecommerce_long_cli_workspace(
        workspace_dir=workspace_dir,
        report_dir=report_dir,
        report_id=report_id,
        frame=_frame(),
        request=_request(use_r_workflow=True),
        report=_report(report_id),
        requirement_intent={"optimized_user_requirement": "鏇撮暱鐨勭數鍟嗙粡钀ユ姤鍛?"},
        artifact_bundle={"downloadables": [{"name": "base.pdf", "path": "/storage/base.pdf", "purpose": "main"}]},
        context_payload={"pipeline_job_id": "codex-pipeline-demo"},
    )

    required_paths = [
        workspace_dir / "pipeline_context.json",
        workspace_dir / "existing_requirement_intent.json",
        workspace_dir / "ecommerce_runtime_source_bundle.json",
        workspace_dir / "ecommerce_runtime_source_index.json",
        workspace_dir / "current_management_report.md",
        workspace_dir / "current_management_report.html",
        workspace_dir / "current_analyst_appendix.md",
        workspace_dir / "current_analyst_appendix.html",
    ]
    for path in required_paths:
        assert path.exists(), path

    bundle = json.loads((workspace_dir / "ecommerce_runtime_source_bundle.json").read_text(encoding="utf-8"))
    assert bundle["report_metadata"]["business_profile"] == "ecommerce_product_operations_report"
    assert "ecommerce_field_availability_registry" in bundle
    assert "product_operations_analysis_modules" in bundle
    assert "metric_mining_output_files" in bundle
    assert bundle["optional_r_workflow_files"]
    assert copied["ecommerce_runtime_source_index_path"].endswith("ecommerce_runtime_source_index.json")


def test_prepare_ecommerce_workspace_skips_optional_r_when_disabled(tmp_path: Path) -> None:
    report_id = "ecomshadow02"
    report_dir = tmp_path / "smart-report-ecomshadow02"
    workspace_dir = tmp_path / "workspace"
    _seed_report_dir(report_dir, report_id)

    _prepare_ecommerce_long_cli_workspace(
        workspace_dir=workspace_dir,
        report_dir=report_dir,
        report_id=report_id,
        frame=_frame(),
        request=_request(use_r_workflow=False),
        report=_report(report_id),
        requirement_intent={"optimized_user_requirement": "鏇撮暱鐨勭數鍟嗙粡钀ユ姤鍛?"},
        artifact_bundle={"downloadables": []},
        context_payload={"pipeline_job_id": "codex-pipeline-demo"},
    )

    bundle = json.loads((workspace_dir / "ecommerce_runtime_source_bundle.json").read_text(encoding="utf-8"))
    assert bundle["optional_r_workflow_files"] == []


def test_validate_ecommerce_inventory_requires_keys(tmp_path: Path) -> None:
    md_path = tmp_path / "01_ecommerce_inventory.md"
    json_path = tmp_path / "01_ecommerce_inventory.json"
    md_path.write_text("# inventory\n", encoding="utf-8")
    json_path.write_text(json.dumps({"business_model": "marketplace"}, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(ValueError, match="ecommerce_inventory JSON `object_hierarchy` must be a non-empty object"):
        pipeline_service_module._validate_ecommerce_inventory(md_path, json_path)


def test_validate_ecommerce_inventory_normalizes_string_and_list_shapes(tmp_path: Path) -> None:
    md_path = tmp_path / "01_ecommerce_inventory.md"
    json_path = tmp_path / "01_ecommerce_inventory.json"
    md_path.write_text("# inventory\n", encoding="utf-8")
    json_path.write_text(
        json.dumps(
            {
                "business_model": "marketplace",
                "object_hierarchy": "product / category / seller",
                "priority_operating_axes": ["fulfillment", "freight"],
                "data_coverage_summary": "褰撳墠瀛楁瑕嗙洊灞ョ害銆佽瘎浠峰拰浜ゆ槗銆?",
                "current_period_focus_objects": "top products",
                "evidence_package_index": ["bundle.json", "registry.json"],
                "analysis_opportunities": "late delivery review",
                "recommended_detail_dimensions": "category",
                "current_period_kpis_used": "gmv",
                "dimensions_covered": ["category", "product"],
                "focus_pools_used": "top products",
                "routes_used": "SP鈫扲J",
                "text_evidence_used": "review themes",
                "unused_but_available_dimensions": "brand",
                "derived_metric_inventory_summary": "5 metrics classified",
                "body_primary_metric_ids": "top_object_amount_contribution",
                "body_support_metric_ids": "overall_trend_change",
                "appendix_metric_ids": "cpm_derived, cpa_derived, quality_proxy",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    payload = pipeline_service_module._validate_ecommerce_inventory(md_path, json_path)

    assert payload["data_coverage_summary"]["narrative"]
    assert payload["evidence_package_index"]["items"] == ["bundle.json", "registry.json"]
    assert payload["business_model"]["model_type"] == "marketplace"
    assert payload["object_hierarchy"]["legacy_items"] == ["product / category / seller"]
    assert payload["priority_operating_axes"][0]["axis"] == "fulfillment"
    assert payload["current_period_focus_objects"]["legacy_focus_items"] == ["top products"]
    assert payload["analysis_opportunities"][0]["opportunity_id"] == "value"
    assert payload["current_period_kpis_used"][0]["kpi_id"] == "gmv"
    assert payload["focus_pools_used"]["legacy_focus_pool_items"] == ["top products"]
    assert payload["text_evidence_used"]["legacy_text_evidence_items"] == ["review themes"]
    assert payload["unused_but_available_dimensions"][0]["dimension_id"] == "brand"
    assert payload["body_primary_metric_ids"] == ["top_object_amount_contribution"]
    assert payload["appendix_metric_ids"] == ["cpm_derived", "cpa_derived", "quality_proxy"]


def test_validate_ecommerce_inventory_accepts_structured_inventory_contract(tmp_path: Path) -> None:
    md_path = tmp_path / "01_ecommerce_inventory.md"
    json_path = tmp_path / "01_ecommerce_inventory.json"
    md_path.write_text("# inventory\n", encoding="utf-8")
    json_path.write_text(
        json.dumps(
            {
                "business_model": {"model_type": "marketplace", "reportable_core": "category x seller"},
                "object_hierarchy": {
                    "management_reading_order": ["鎬荤洏", "绫荤洰", "鍗栧"],
                    "primary_decision_grains": ["category", "shop_seller"],
                },
                "priority_operating_axes": [{"axis": "fulfillment"}, {"axis": "freight"}],
                "data_coverage_summary": {"coverage_note": "good"},
                "current_period_focus_objects": {"headline_categories": ["health_beauty"]},
                "evidence_package_index": {"primary_files": ["bundle.json"]},
                "analysis_opportunities": [{"opportunity_id": "opp_01", "summary": "review delayed orders"}],
                "recommended_detail_dimensions": ["category", "seller_state"],
                "current_period_kpis_used": [{"kpi_id": "gmv", "column": "GMV"}],
                "dimensions_covered": ["category", "product"],
                "focus_pools_used": {"category": ["health_beauty"]},
                "routes_used": ["SP鈫扲J"],
                "text_evidence_used": {"themes_used": ["delivery"]},
                "unused_but_available_dimensions": [{"dimension_id": "brand", "reason_not_chosen": "secondary"}],
                "derived_metric_inventory_summary": {"metric_universe_count": 5},
                "body_primary_metric_ids": ["top_object_amount_contribution"],
                "body_support_metric_ids": ["overall_trend_change"],
                "appendix_metric_ids": ["cpm_derived", "cpa_derived", "quality_proxy"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    payload = pipeline_service_module._validate_ecommerce_inventory(md_path, json_path)

    assert payload["business_model"]["model_type"] == "marketplace"
    assert payload["object_hierarchy"]["primary_decision_grains"] == ["category", "shop_seller"]
    assert payload["current_period_kpis_used"][0]["kpi_id"] == "gmv"
    assert payload["focus_pools_used"]["category"] == ["health_beauty"]
    assert payload["derived_metric_inventory_summary"]["metric_universe_count"] == 5


def _patch_pipeline_store(monkeypatch: pytest.MonkeyPatch) -> dict[str, dict[str, object]]:
    manifests: dict[str, dict[str, object]] = {}

    def _clone(value: object) -> object:
        return copy.deepcopy(value)

    def _fake_create_manifest(payload: dict[str, object]) -> dict[str, object]:
        manifests[str(payload["pipeline_job_id"])] = _clone(payload)  # type: ignore[assignment]
        return _clone(payload)  # type: ignore[return-value]

    def _fake_read_manifest(pipeline_job_id: str) -> dict[str, object]:
        return _clone(manifests[pipeline_job_id])  # type: ignore[return-value]

    def _fake_update_manifest(pipeline_job_id: str, updates: dict[str, object]) -> dict[str, object]:
        current = _clone(manifests[pipeline_job_id])  # type: ignore[assignment]
        assert isinstance(current, dict)
        current.update(_clone(updates))  # type: ignore[arg-type]
        manifests[pipeline_job_id] = current
        return _clone(current)  # type: ignore[return-value]

    def _fake_persist_stage_artifact_metadata(pipeline_job_id: str, *, stage_id: str, artifact: dict[str, object]) -> dict[str, object]:
        entry = {
            "artifact_id": f"artifact-{len(list((manifests[pipeline_job_id].get('artifact_index') or []))) + 1}",
            "stage_id": stage_id,
            **artifact,
        }
        manifests[pipeline_job_id].setdefault("artifact_index", []).append(_clone(entry))  # type: ignore[union-attr]
        return _clone(entry)  # type: ignore[return-value]

    monkeypatch.setattr(pipeline_service_module, "create_pipeline_manifest", _fake_create_manifest)
    monkeypatch.setattr(pipeline_service_module, "read_pipeline_manifest", _fake_read_manifest)
    monkeypatch.setattr(pipeline_service_module, "update_pipeline_manifest", _fake_update_manifest)
    monkeypatch.setattr(pipeline_service_module, "persist_stage_artifact_metadata", _fake_persist_stage_artifact_metadata)
    return manifests


def test_retry_inventory_keeps_requirement_and_fact_pack_but_resets_downstream(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifests = _patch_pipeline_store(monkeypatch)
    manifest = create_pipeline_job(
        pipeline_type="ecommerce_long_cli_pipeline",
        workspace_path=str(tmp_path / "{pipeline_job_id}"),
        linked_report_id="report-001",
        context_payload={"business_profile": "ecommerce_product_operations_report"},
        auto_start=False,
    )
    pipeline_job_id = str(manifest["pipeline_job_id"])
    manifests[pipeline_job_id].update(
        {
            "status": "failed",
            "current_stage_id": "ecommerce_inventory",
            "current_stage_title": "鐢靛晢缁忚惀鐩樼偣",
            "current_stage": {"stage_id": "ecommerce_inventory", "title": "鐢靛晢缁忚惀鐩樼偣", "status": "failed"},
            "error": "inventory failed",
            "stage_outputs": {
                "requirement_intent": {"status": "completed"},
                "ecommerce_table_fact_pack": {"status": "completed"},
                "derived_metric_family_planning": {"status": "completed"},
                "derived_metric_family_execution": {"status": "completed"},
                "ecommerce_metric_consumption_pack": {"status": "completed"},
                "ecommerce_inventory": {"status": "failed"},
                "ecommerce_question_tree": {"status": "completed"},
            },
            "artifact_index": [
                {"stage_id": "requirement_intent", "name": "00_requirement_intent.json"},
                {"stage_id": "ecommerce_table_fact_pack", "name": "01a_ecommerce_table_fact_pack.json"},
                {"stage_id": "ecommerce_metric_consumption_pack", "name": "01b_ecommerce_metric_consumption_index.json"},
                {"stage_id": "ecommerce_inventory", "name": "01_ecommerce_inventory.json"},
                {"stage_id": "ecommerce_question_tree", "name": "02_ecommerce_question_tree.json"},
            ],
        }
    )

    updated = pipeline_service_module.retry_pipeline_stage(
        pipeline_job_id,
        stage_id="ecommerce_inventory",
        auto_start=False,
    )

    assert updated["status"] == "queued"
    assert set(updated["stage_outputs"].keys()) == {
        "requirement_intent",
        "ecommerce_table_fact_pack",
        "derived_metric_family_planning",
        "derived_metric_family_execution",
        "ecommerce_metric_consumption_pack",
    }
    assert all(item["stage_id"] in {"requirement_intent", "ecommerce_table_fact_pack", "ecommerce_metric_consumption_pack"} for item in updated["artifact_index"])
    assert updated["current_stage_id"] == "ecommerce_inventory"


def test_inventory_stage_completion_advances_to_question_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifests = _patch_pipeline_store(monkeypatch)
    manifest = create_pipeline_job(
        pipeline_type="ecommerce_long_cli_pipeline",
        workspace_path=str(tmp_path / "{pipeline_job_id}"),
        linked_report_id="report-001",
        context_payload={"business_profile": "ecommerce_product_operations_report"},
        auto_start=False,
    )
    pipeline_job_id = str(manifest["pipeline_job_id"])
    workspace = Path(str(manifest["workspace_path"]))
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "00_requirement_intent.md").write_text("# intent\n", encoding="utf-8")
    (workspace / "00_requirement_intent.json").write_text(
        json.dumps(
            {
                "optimized_user_requirement": "demo",
                "detected_business_profile": "ecommerce_product_operations_report",
                "business_questions": ["q1"],
                "target_audience": "management",
                "core_purpose": "diagnosis",
                "expected_result": "report",
                "analysis_depth": "deep_dive",
                "required_detail_dimensions": ["category"],
                "must_include_sections": ["summary"],
                "recommendation_style": "actionable",
                "visual_style": "premium",
                "color_palette": "navy_white_premium",
                "layout_preference": "A4",
                "pdf_design_brief": "boardroom",
                "output_contract": {"main_report": "pdf"},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (workspace / "01a_ecommerce_table_fact_pack.md").write_text("# fact pack\n", encoding="utf-8")
    (workspace / "01a_ecommerce_table_fact_pack.json").write_text(
        json.dumps(
            {
                "source_dataset_path": str((workspace / "source_dataset.csv").resolve()),
                "row_count": 10,
                "column_count": 5,
                "metric_columns": {"gmv": "GMV"},
                "current_period_kpis": {"row_count": 10},
                "dimension_count": 2,
                "dimension_catalog_path": "01a_dimension_catalog.json",
                "dimension_detail_summary_path": "01a_dimension_detail_summary.csv",
                "dimension_pair_summary_path": "01a_dimension_pair_summary.csv",
                "object_pool_registry_path": "01a_object_pool_registry.json",
                "exception_casebook_path": "01a_exception_casebook.json",
                "route_cube_path": "01a_route_cube.csv",
                "review_text_theme_summary_path": "01a_review_text_theme_summary.json",
                "metric_cube_overview_path": "01a_metric_cube_overview.json",
                "query_guide_path": "query_guide.md",
                "query_examples_sql_path": "query_examples.sql",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (workspace / "01b_ecommerce_metric_consumption_index.md").write_text("# metric pack\n", encoding="utf-8")
    (workspace / "01b_ecommerce_metric_consumption_index.json").write_text(
        json.dumps(
            {
                "metric_universe": [
                    {
                        "metric_id": "cpm_derived",
                        "metric_name": "千次触达成本参考指标",
                        "metric_kind": "derived_metric",
                        "formula": "f",
                        "value": "1",
                        "confidence": "high",
                        "evidence_level": "B_DERIVED",
                        "business_meaning": "鐢ㄤ簬浣滀负鏇濆厜鎴栬Е杈炬垚鏈殑闄勫綍鍙傝€冦€?",
                        "source_columns": ["FreightCost"],
                        "consumption_target": "body_primary",
                        "target_sections": ["S03"],
                        "must_appear_in_body": True,
                        "must_appear_in_appendix": True,
                        "chart_candidate": True,
                        "consumption_reason": "r",
                    }
                ],
                "body_primary_metrics": [
                    {
                        "metric_id": "cpm_derived",
                        "metric_name": "鍗冩瑙﹁揪鎴愭湰鍙傝€冩寚鏍?",
                        "metric_kind": "derived_metric",
                        "formula": "f",
                        "value": "1",
                        "confidence": "high",
                        "evidence_level": "B_DERIVED",
                        "business_meaning": "鐢ㄤ簬浣滀负鏇濆厜鎴栬Е杈炬垚鏈殑闄勫綍鍙傝€冦€?",
                        "source_columns": ["FreightCost"],
                        "consumption_target": "body_primary",
                        "target_sections": ["S03"],
                        "must_appear_in_body": True,
                        "must_appear_in_appendix": True,
                        "chart_candidate": True,
                        "consumption_reason": "r",
                    }
                ],
                "body_support_metrics": [],
                "appendix_metrics": [],
                "consumption_contract": {"body_primary_count": 1, "body_support_count": 0, "appendix_count": 0, "all_metric_ids_classified": True},
                "target_sections_by_metric": {"cpm_derived": ["S03"]},
                "metric_usage_requirements": [{"metric_id": "cpm_derived", "consumption_target": "body_primary"}],
                "metric_source_index": {"metric_universe_count": 1},
                "metric_universe_count": 1,
                "all_metric_ids_classified": True,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    manifests[pipeline_job_id].update(
        {
            "status": "queued",
            "current_stage_id": "ecommerce_inventory",
            "current_stage_title": "鐢靛晢缁忚惀鐩樼偣",
                "stage_outputs": {
                        "requirement_intent": {"status": "completed"},
                        "ecommerce_table_fact_pack": {"status": "completed"},
                        "derived_metric_family_input_pack": {"status": "completed"},
                        "derived_metric_family_planning": {"status": "completed"},
                        "derived_metric_family_execution": {"status": "completed"},
                        "ecommerce_metric_consumption_pack": {"status": "completed"},
                    },
            }
    )

    def _fake_run_codex_stage(_pipeline_job_id: str, *, manifest: dict[str, object], stage: dict[str, object], prompt: str) -> dict[str, str]:
        del manifest, stage, prompt
        (workspace / "01_ecommerce_inventory.md").write_text("# inventory\n", encoding="utf-8")
        (workspace / "01_ecommerce_inventory.json").write_text(
            json.dumps(
                {
                    "business_model": {"model_type": "marketplace"},
                    "object_hierarchy": {"management_reading_order": ["鎬荤洏"], "primary_decision_grains": ["category"]},
                    "priority_operating_axes": [{"axis": "fulfillment"}],
                    "data_coverage_summary": {"coverage_note": "good"},
                    "current_period_focus_objects": {"headline_categories": ["health_beauty"]},
                    "evidence_package_index": {"primary_files": ["bundle.json"]},
                    "analysis_opportunities": [{"opportunity_id": "opp_01"}],
                    "recommended_detail_dimensions": ["category"],
                    "current_period_kpis_used": [{"kpi_id": "gmv"}],
                    "dimensions_covered": ["category"],
                    "focus_pools_used": {"category": ["health_beauty"]},
                    "routes_used": [],
                    "text_evidence_used": {"themes_used": []},
                    "unused_but_available_dimensions": [],
                    "derived_metric_inventory_summary": {"metric_universe_count": 1},
                    "body_primary_metric_ids": ["cpm_derived"],
                    "body_support_metric_ids": [],
                    "appendix_metric_ids": [],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return {"run_id": "run-123", "session_id": "session-123", "summary": "inventory completed"}

    monkeypatch.setattr(pipeline_service_module, "_run_codex_stage", _fake_run_codex_stage)

    updated = pipeline_service_module.run_pipeline(pipeline_job_id)

    assert updated["status"] == "blocked"
    assert updated["current_stage_id"] == "ecommerce_question_tree"
    assert updated["stage_outputs"]["ecommerce_inventory"]["status"] == "completed"
    assert updated["stage_outputs"]["ecommerce_inventory"]["run_id"] == "run-123"


def test_compact_ecommerce_question_tree_context_uses_summary_only() -> None:
    requirement_payload = {
        "optimized_user_requirement": "x" * 2000,
        "detected_business_profile": "ecommerce_product_operations_report",
        "business_questions": [f"q{i}" for i in range(10)],
        "target_audience": "management",
        "core_purpose": "diagnosis",
        "expected_result": "report",
        "required_detail_dimensions": [f"d{i}" for i in range(20)],
        "must_include_sections": [f"s{i}" for i in range(20)],
    }
    inventory_payload = {
        "business_model": {"model_type": "marketplace", "reportable_core": "category x seller"},
        "object_hierarchy": {
            "management_reading_order": [f"g{i}" for i in range(12)],
            "primary_decision_grains": [f"p{i}" for i in range(12)],
            "secondary_decision_grains": [f"s{i}" for i in range(12)],
        },
        "priority_operating_axes": [{"axis": f"a{i}", "why": "x" * 200} for i in range(12)],
        "current_period_focus_objects": {"category": [f"c{i}" for i in range(20)]},
        "analysis_opportunities": [{"opportunity_id": f"o{i}", "summary": "y" * 200} for i in range(12)],
        "recommended_detail_dimensions": [f"rd{i}" for i in range(20)],
        "current_period_kpis_used": [{"kpi_id": f"k{i}", "column": "GMV"} for i in range(12)],
        "dimensions_covered": [f"dc{i}" for i in range(20)],
        "focus_pools_used": {"category": [f"pool{i}" for i in range(20)]},
        "routes_used": [f"r{i}" for i in range(20)],
        "text_evidence_used": {
            "text_column": "ReviewText",
            "coverage_note": "z" * 400,
            "themes_used": [f"t{i}" for i in range(20)],
            "sample_quotes_used": [f"quote{i}" for i in range(20)],
        },
        "unused_but_available_dimensions": [{"dimension_id": f"u{i}", "reason_not_chosen": "later"} for i in range(20)],
    }
    fact_pack_payload = {
        "row_count": 500,
        "column_count": 31,
        "dimension_count": 14,
        "metric_columns": {"gmv": "GMV"},
        "current_period_focus_pools": {"category": [f"c{i}" for i in range(20)]},
        "route_count": 20,
        "exception_case_count": 16,
        "text_theme_count": 15,
        "dimension_catalog_path": "01a_dimension_catalog.json",
        "dimension_detail_summary_path": "01a_dimension_detail_summary.csv",
        "dimension_pair_summary_path": "01a_dimension_pair_summary.csv",
        "object_pool_registry_path": "01a_object_pool_registry.json",
        "exception_casebook_path": "01a_exception_casebook.json",
        "route_cube_path": "01a_route_cube.csv",
        "review_text_theme_summary_path": "01a_review_text_theme_summary.json",
    }

    compact = pipeline_service_module._compact_ecommerce_question_tree_context(
        base_context={
            "style_preset": "navy_white_premium",
            "language": "zh-CN",
            "report_goal": "ecommerce_shadow_business_report",
            "target_audience": "management",
            "analysis_mode": "ecommerce_long_cli_pipeline",
            "business_focus": "focus" * 400,
            "request": {"very": "large"},
        },
        requirement_intent_payload=requirement_payload,
        inventory_payload=inventory_payload,
        fact_pack_payload=fact_pack_payload,
    )

    assert "request" not in compact
    assert "requirement_intent_summary" in compact
    assert "ecommerce_inventory_summary" in compact
    assert "ecommerce_table_fact_pack_summary" in compact
    assert len(compact["requirement_intent_summary"]["business_questions"]) == 6
    assert len(compact["ecommerce_inventory_summary"]["routes_used"]) == 8


def test_complete_codex_stage_uses_next_incomplete_stage_not_next_sequential(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifests = _patch_pipeline_store(monkeypatch)
    manifest = create_pipeline_job(
        pipeline_type="ecommerce_long_cli_pipeline",
        workspace_path=str(tmp_path / "{pipeline_job_id}"),
        linked_report_id="report-001",
        context_payload={"business_profile": "ecommerce_product_operations_report"},
        auto_start=False,
    )
    pipeline_job_id = str(manifest["pipeline_job_id"])
    workspace = Path(str(manifest["workspace_path"]))
    workspace.mkdir(parents=True, exist_ok=True)
    md_path = workspace / "03_ecommerce_long_outline.md"
    json_path = workspace / "03_ecommerce_long_outline.json"
    md_path.write_text("# outline\n", encoding="utf-8")
    json_path.write_text(
        json.dumps(
            {
                "headline_thesis": "demo",
                "section_plan": [{"section_id": "S01", "table_inputs": ["T1"], "dimension_focus": ["category"], "object_pools": ["category"]}] * 6,
                "batch_plan": [
                    {"batch_index": 1},
                    {"batch_index": 2},
                    {"batch_index": 3},
                    {"batch_index": 4},
                ],
                "required_tables": ["T1"],
                "required_figures_or_visual_blocks": ["F1"],
                "recommendation_backbone": ["A1"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    manifests[pipeline_job_id].update(
        {
            "status": "running",
            "current_stage_id": "ecommerce_long_outline",
            "current_stage_title": "鐢靛晢闀挎姤鍛婂ぇ绾?",
                "stage_outputs": {
                        "requirement_intent": {"status": "completed"},
                        "ecommerce_table_fact_pack": {"status": "completed"},
                        "derived_metric_family_input_pack": {"status": "completed"},
                        "derived_metric_family_planning": {"status": "completed"},
                        "derived_metric_family_execution": {"status": "completed"},
                        "ecommerce_metric_consumption_pack": {"status": "completed"},
                        "ecommerce_inventory": {"status": "completed"},
                "ecommerce_question_tree": {"status": "completed"},
                "ecommerce_section_batch_01": {"status": "completed"},
            },
        }
    )
    stage = next(item for item in list(manifest["stage_order"]) if item["stage_id"] == "ecommerce_long_outline")
    artifacts = pipeline_service_module._register_artifact_pair(
        pipeline_job_id,
        stage_id="ecommerce_long_outline",
        markdown_path=md_path,
        json_path=json_path,
    )
    updated = pipeline_service_module._complete_codex_stage(
        pipeline_job_id,
        manifest=manifest,
        stage=stage,
        run_result={"run_id": "run-outline", "session_id": "session-outline", "summary": "done"},
        output_files=[md_path, json_path],
        artifacts=artifacts,
        progress_percent=44,
    )

    assert updated["current_stage_id"] == "ecommerce_section_batch_02"


def test_complete_codex_stage_ignores_stale_downstream_completion_when_current_stage_differs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifests = _patch_pipeline_store(monkeypatch)
    manifest = create_pipeline_job(
        pipeline_type="ecommerce_long_cli_pipeline",
        workspace_path=str(tmp_path / "{pipeline_job_id}"),
        linked_report_id="report-001",
        context_payload={"business_profile": "ecommerce_product_operations_report"},
        auto_start=False,
    )
    pipeline_job_id = str(manifest["pipeline_job_id"])
    workspace = Path(str(manifest["workspace_path"]))
    workspace.mkdir(parents=True, exist_ok=True)
    md_path = workspace / "04_ecommerce_section_batch_01.md"
    json_path = workspace / "04_ecommerce_section_batch_01.json"
    md_path.write_text("# batch\n", encoding="utf-8")
    json_path.write_text(
        json.dumps(
            {
                "batch_index": 1,
                "section_ids": ["S01"],
                "section_titles": ["s1"],
                "completion_status": "completed",
                "tables_used": ["T1"],
                "named_objects_used": ["health_beauty"],
                "dimension_tables_used": ["category"],
                "route_tables_used": [],
                "text_evidence_blocks_used": [],
                "current_period_metrics_used": ["gmv"],
                "table_fact_ids_used": ["fact"],
                "derived_metrics_used": ["cpm_derived"],
                "derived_metric_tables_used": ["01b_ecommerce_metric_body_priority.csv"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    manifests[pipeline_job_id].update(
        {
            "status": "running",
            "current_stage_id": "ecommerce_long_outline",
            "current_stage_title": "鐢靛晢闀挎姤鍛婂ぇ绾?",
            "stage_outputs": {
                "requirement_intent": {"status": "completed"},
                "ecommerce_table_fact_pack": {"status": "completed"},
                "derived_metric_family_planning": {"status": "completed"},
                "derived_metric_family_execution": {"status": "completed"},
                "ecommerce_metric_consumption_pack": {"status": "completed"},
                "ecommerce_inventory": {"status": "completed"},
                "ecommerce_question_tree": {"status": "completed"},
            },
        }
    )
    stage = next(item for item in list(manifest["stage_order"]) if item["stage_id"] == "ecommerce_section_batch_01")
    artifacts = pipeline_service_module._register_artifact_pair(
        pipeline_job_id,
        stage_id="ecommerce_section_batch_01",
        markdown_path=md_path,
        json_path=json_path,
    )
    updated = pipeline_service_module._complete_codex_stage(
        pipeline_job_id,
        manifest=manifest,
        stage=stage,
        run_result={"run_id": "run-batch-1", "session_id": "session-batch-1", "summary": "done"},
        output_files=[md_path, json_path],
        artifacts=artifacts,
        progress_percent=52,
    )

    assert updated["current_stage_id"] == "ecommerce_long_outline"
    assert "ecommerce_section_batch_01" not in (updated.get("stage_outputs") or {})


def test_ecommerce_outline_prompt_uses_specialized_output_names() -> None:
    prompt = build_ecommerce_long_outline_prompt(
        workspace_path="E:/workspace",
        question_tree_path="E:/workspace/02_ecommerce_question_tree.json",
        context_payload={},
        language="zh-CN",
    )
    assert "outline.md" in prompt
    assert "outline.json" in prompt
    assert "05_long_report_outline.md" not in prompt


def test_ecommerce_section_batch_prompt_uses_specialized_output_names() -> None:
    prompt = build_ecommerce_section_batch_prompt(
        workspace_path="E:/workspace",
        batch_index=1,
        outline_path="E:/workspace/03_ecommerce_long_outline.json",
        question_tree_path="E:/workspace/02_ecommerce_question_tree.json",
        ecommerce_inventory_path="E:/workspace/01_ecommerce_inventory.json",
        context_payload={},
        language="zh-CN",
    )
    assert "04_ecommerce_section_batch_01.md" in prompt
    assert "04_ecommerce_section_batch_01.json" in prompt
    assert "05_section_batch_01.md" not in prompt


def test_ecommerce_question_tree_prompt_uses_grounding_index_path() -> None:
    from app.services.codex_runtime_prompt_templates import build_ecommerce_question_tree_prompt

    prompt = build_ecommerce_question_tree_prompt(
        workspace_path="E:/workspace",
        requirement_intent_path="E:/workspace/00_requirement_intent.json",
        ecommerce_inventory_path="E:/workspace/01_ecommerce_inventory.json",
        grounding_index_path="E:/workspace/ecommerce_question_tree_grounding.json",
        context_payload={"stage_grounding_mode": "file_grounded"},
        language="zh-CN",
    )

    assert "Question-tree grounding index JSON" in prompt
    assert "ecommerce_question_tree_grounding.json" in prompt


def test_ecommerce_html_css_prompt_uses_grounding_index_and_direct_write_rules() -> None:
    from app.services.codex_runtime_prompt_templates import build_ecommerce_html_css_prompt

    prompt = build_ecommerce_html_css_prompt(
        workspace_path="E:/workspace",
        markdown_report_path="E:/workspace/05_report.md",
        chart_insights_path="E:/workspace/chart_insights.json",
        grounding_index_path="E:/workspace/ecommerce_html_css_grounding.json",
        reader_interpretation_path="E:/workspace/05b_ecommerce_reader_interpretation_pack.json",
        context_payload={"stage_grounding_mode": "file_grounded"},
        language="zh-CN",
        style_preset="navy_white_premium",
    )

    assert "Stage-local grounding index JSON" in prompt
    assert "ecommerce_html_css_grounding.json" in prompt
    assert "Reader interpretation pack JSON" in prompt
    assert "table-reading-card" in prompt
    assert "figure-notes" in prompt
    assert "指标使用地图" in prompt
    assert "Do not generate helper scripts or intermediary tooling" in prompt


def _write_html_css_pair(tmp_path: Path, html_text: str, css_text: str | None = None) -> tuple[Path, Path]:
    html_path = tmp_path / "06_report.html"
    css_path = tmp_path / "06_report.css"
    if len(html_text) < 700:
        html_text = html_text.replace(
            "</body>",
            "<section>管理层阅读背景：本段用于模拟真实电商经营报告正文，包含商品运营、履约、卖家责任、路线治理、派生指标使用、检查点和本周复盘安排，确保 HTML 基础体量足以进入专项校验。</section>"
            * 3
            + "</body>",
        )
    html_path.write_text(html_text, encoding="utf-8")
    css_path.write_text(
        css_text
        or (
            "@page { size: A4; margin: 18mm; } "
            "body { font-family: sans-serif; color: #102033; } "
            "table { width: 100%; border-collapse: collapse; break-inside: avoid; page-break-inside: avoid; } "
            "thead { display: table-header-group; } "
            ".table-reading-card, .figure-notes, .metric-usage-map { border: 1px solid #d8dee8; padding: 10px; margin: 10px 0; }"
        ),
        encoding="utf-8",
    )
    return html_path, css_path


def test_ecommerce_html_validation_rejects_tables_without_reader_cards(tmp_path: Path) -> None:
    html_path, css_path = _write_html_css_pair(
        tmp_path,
        '<html><head><link rel="stylesheet" href="06_report.css"></head><body>'
        '<section><table><tr><th>对象</th></tr><tr><td>health_beauty</td></tr></table></section>'
        '<section class="metric-usage-map">指标使用地图 top_object_amount_contribution</section>'
        '</body></html>',
    )

    with pytest.raises(ValueError, match="table-reading-card"):
        pipeline_service_module._validate_html_css(
            html_path,
            css_path,
            require_ecommerce_reader_interpretation=True,
            require_clean_chinese=True,
        )


def test_ecommerce_html_validation_rejects_weak_reader_cards(tmp_path: Path) -> None:
    html_path, css_path = _write_html_css_pair(
        tmp_path,
        '<html><head><link rel="stylesheet" href="06_report.css"></head><body>'
        '<div class="table-reading-card">怎么看：看表。说明什么：用于观察。下一步动作：继续看。</div>'
        '<table><tr><th>对象</th></tr><tr><td>health_beauty</td></tr></table>'
        '<section class="metric-usage-map">指标使用地图 top_object_amount_contribution</section>'
        '</body></html>',
    )

    with pytest.raises(ValueError, match="too short|lacks"):
        pipeline_service_module._validate_html_css(
            html_path,
            css_path,
            require_ecommerce_reader_interpretation=True,
            require_clean_chinese=True,
        )


def test_ecommerce_html_validation_rejects_mojibake(tmp_path: Path) -> None:
    html_path, css_path = _write_html_css_pair(
        tmp_path,
        '<html><head><link rel="stylesheet" href="06_report.css"></head><body>'
        '<div class="table-reading-card">怎么看：先看 health_beauty 的 19.40%。说明什么：绠＄悊文本乱码。下一步动作：本周复盘。</div>'
        '<table><tr><th>对象</th></tr><tr><td>health_beauty 19.40%</td></tr></table>'
        '<section class="metric-usage-map">指标使用地图 top_object_amount_contribution</section>'
        '</body></html>',
    )

    with pytest.raises(ValueError, match="mojibake"):
        pipeline_service_module._validate_html_css(
            html_path,
            css_path,
            require_ecommerce_reader_interpretation=True,
            require_clean_chinese=True,
        )


def test_ecommerce_html_validation_requires_figure_notes_for_assets(tmp_path: Path) -> None:
    html_path, css_path = _write_html_css_pair(
        tmp_path,
        '<html><head><link rel="stylesheet" href="06_report.css"></head><body>'
        '<div class="table-reading-card">怎么看：先看 health_beauty 19.40% 与 housewares 17.04% 的差异，再看本周动作列是否已经分到责任人。说明什么：对象池已经分层，头部类目和高费率类目不能用同一套动作处理。下一步动作：本周由商品运营负责人复盘 P1 对象池，并把高费率对象交给履约负责人确认。</div>'
        '<table><tr><th>对象</th></tr><tr><td>health_beauty 19.40%</td></tr></table>'
        '<figure><img src="source_visual_assets/chart.png" alt="chart"></figure>'
        '<section class="metric-usage-map">指标使用地图 top_object_amount_contribution</section>'
        '</body></html>',
    )
    visual_path = tmp_path / "source_visual_assets_index.json"
    visual_path.write_text(
        json.dumps({"image_assets": [{"name": "chart.png", "relative_path": "source_visual_assets/chart.png", "chart_type": "bubble"}]}, ensure_ascii=False),
        encoding="utf-8",
    )
    chart_path = tmp_path / "chart_insights.json"
    chart_path.write_text(
        json.dumps(
            {
                "figures": [
                    {
                        "figure_id": "chart.png",
                        "relative_path": "source_visual_assets/chart.png",
                        "observation": "health_beauty 19.40% 明显高于其他对象。",
                        "implication": "说明头部对象需要优先治理。",
                        "action": "本周由商品运营负责人复盘。",
                        "evidence_numbers": ["health_beauty 19.40%"],
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="figure"):
        pipeline_service_module._validate_html_css(
            html_path,
            css_path,
            chart_insights_path=chart_path,
            visual_asset_index_path=visual_path,
            require_ecommerce_reader_interpretation=True,
            require_clean_chinese=True,
        )


def test_ensure_html_figure_evidence_notes_injects_validation_language(tmp_path: Path) -> None:
    html_path = tmp_path / "06_report.html"
    chart_path = tmp_path / "chart_insights.json"
    html_path.write_text(
        '<html><body><figure><img src="source_visual_assets/chart.png"><div class="figure-notes"><p><strong>观察：</strong>health_beauty 占 19.40%。</p><p><strong>含义：</strong>头部类目要优先治理。</p><p><strong>动作：</strong>商品运营复盘。</p></div></figure></body></html>',
        encoding="utf-8",
    )
    chart_path.write_text(
        json.dumps(
            {
                "figures": [
                    {
                        "figure_id": "chart.png",
                        "relative_path": "source_visual_assets/chart.png",
                        "observation": "health_beauty 占 19.40%。",
                        "implication": "头部类目要优先治理。",
                        "action": "商品运营复盘。",
                        "evidence_numbers": ["19.40%"],
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    pipeline_service_module._ensure_html_figure_evidence_notes(html_path, chart_insights_path=chart_path)
    updated = html_path.read_text(encoding="utf-8")

    assert "验证：" in updated
    assert "边界：" in updated
    assert "后续问题：" in updated


def test_ecommerce_html_validation_passes_with_reader_cards_and_metric_map(tmp_path: Path) -> None:
    html_path, css_path = _write_html_css_pair(
        tmp_path,
        '<html><head><link rel="stylesheet" href="06_report.css"></head><body>'
        '<div class="table-reading-card">怎么看：先看 health_beauty 19.40% 与 housewares 17.04% 的差异，再比较动作列。说明什么：头部类目与高费率类目已经分层。下一步动作：本周由商品运营负责人复盘 P1 对象池。</div>'
        '<table><tr><th>对象</th><th>读数</th></tr><tr><td>health_beauty</td><td>19.40%</td></tr></table>'
        '<section class="metric-usage-map">指标使用地图：top_object_amount_contribution 用在管理摘要，quality_proxy 用在附录指标。</section>'
        '</body></html>',
    )
    metric_path = tmp_path / "01b_ecommerce_metric_consumption_index.json"
    metric_path.write_text(
        json.dumps(
            {
                "body_primary_metrics": [{"metric_id": "top_object_amount_contribution"}],
                "body_support_metrics": [],
                "appendix_metrics": [{"metric_id": "quality_proxy"}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    pipeline_service_module._validate_html_css(
        html_path,
        css_path,
        require_ecommerce_reader_interpretation=True,
        metric_consumption_path=metric_path,
        require_clean_chinese=True,
    )


def test_ecommerce_frontline_action_pack_writes_execution_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "09_frontline_workorder_pack.json").write_text(
        json.dumps(
            {
                "stage_id": "ecommerce_frontline_workorder_pack",
                "role_queues": [
                    {"role": "商品运营", "tasks": ["FW-001"], "waiting_items": []},
                    {"role": "卖家/店铺运营", "tasks": [], "waiting_items": ["等待卖家证据"]},
                    {"role": "物流履约", "tasks": [], "waiting_items": ["等待路线证据"]},
                    {"role": "客服体验", "tasks": [], "waiting_items": ["等待低评分证据"]},
                    {"role": "数据分析", "tasks": [], "waiting_items": ["等待字段补齐"]},
                ],
                "workorders": [
                    {
                        "workorder_id": "FW-001",
                        "role": "商品运营",
                        "object_type": "category",
                        "object_name": "health_beauty",
                        "priority": "P1",
                        "why_now": "health_beauty GMV 10168，运费/GMV 9.08%，需要本周处理。",
                        "action_steps": ["拉出高运费 SKU 清单", "核对包材重量", "确认承运路线"],
                        "owner_role": "商品运营",
                        "deadline": "T+3",
                        "validation_metrics": ["GMV", "运费/GMV", "freight_to_gmv"],
                        "pass_criteria": "完成清单并给出处理路径。",
                        "fail_criteria": "无法定位 SKU 或无法解释运费异常。",
                        "blockers": [],
                        "escalation_rule": "T+3 未完成则升级给商品负责人。",
                        "derived_metric_ids": ["freight_to_gmv"],
                        "evidence": ["health_beauty GMV 10168", "运费/GMV 9.08%"],
                        "source_refs": ["09a_frontline_task_index.json"],
                    }
                ],
                "blocked_items": [],
                "daily_standup_script": ["先看 P1 类目是否完成 SKU 清单。"],
                "source_index": ["09a_frontline_task_index.json"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (workspace / "09_frontline_workorder_pack.md").write_text(
        "# 一线工单\n\n- health_beauty：拉出高运费 SKU 清单。\n",
        encoding="utf-8",
    )

    def _fake_render_html_to_pdf(*, html_path: Path, css_path: Path, output_pdf_path: Path, timeout_sec: int = 120):
        output_pdf_path.write_bytes(b"%PDF-1.4 frontline")
        return {"engine": "fake", "bytes": output_pdf_path.stat().st_size}

    monkeypatch.setattr(pipeline_service_module, "render_html_to_pdf", _fake_render_html_to_pdf)

    result = pipeline_service_module._write_ecommerce_frontline_action_pack(workspace)

    assert Path(result["pdf_path"]).exists()
    html_text = Path(result["html_path"]).read_text(encoding="utf-8")
    assert "对象级任务卡" in html_text
    assert "表格怎么用" not in html_text
    assert "图表怎么用" not in html_text
    assert Path(result["markdown_path"]).read_text(encoding="utf-8").count("拉出高运费 SKU 清单") >= 1
    payload = json.loads((workspace / "09_frontline_action_pack.json").read_text(encoding="utf-8"))
    assert payload["workorder_count"] == 1
    assert payload["frontline_workorders"][0]["object_name"] == "health_beauty"


def test_ecommerce_frontline_task_index_extracts_concrete_objects(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "01a_object_pool_registry.json").write_text(
        json.dumps(
            {
                "category": [{"dimension_value": "health_beauty", "sample_size": 20, "gmv_sum": 12000, "freight_sum": 1400, "rating_mean": 4.2}],
                "shop_seller": [{"dimension_value": "seller_001", "gmv_sum": 3000, "freight_mean": 22, "rating_mean": 3.9}],
                "sku": [{"dimension_value": "sku_abc", "gmv_sum": 800, "weight_mean": 3300, "freight_mean": 28}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (workspace / "01a_exception_casebook.json").write_text(
        json.dumps({"cases": [{"case_id": "case_low_rating_01", "summary": "评分 1 分订单"}]}, ensure_ascii=False),
        encoding="utf-8",
    )
    (workspace / "01a_route_cube.csv").write_text(
        "left_value,right_value,sample_size,gmv_sum,freight_mean,rating_mean\nSP,RJ,12,1600,25,4.1\n",
        encoding="utf-8",
    )
    (workspace / "01b_ecommerce_metric_consumption_index.json").write_text(
        json.dumps({"body_primary_metrics": [{"metric_id": "freight_to_gmv"}]}, ensure_ascii=False),
        encoding="utf-8",
    )
    (workspace / "ecommerce_action_table.json").write_text("[]", encoding="utf-8")

    payload = pipeline_service_module._write_ecommerce_frontline_task_index(workspace)

    names = {item["object_name"] for item in payload["task_candidates"]}
    assert "health_beauty" in names
    assert "seller_001" in names
    assert "sku_abc" in names
    assert "SP->RJ" in names
    assert not {"商品池", "类目池"} & names
    assert (workspace / "09a_frontline_task_index.csv").exists()


def test_ecommerce_frontline_workorder_validator_rejects_generic_review_only(tmp_path: Path) -> None:
    md_path = tmp_path / "09_frontline_workorder_pack.md"
    json_path = tmp_path / "09_frontline_workorder_pack.json"
    md_path.write_text("# 一线工单\n", encoding="utf-8")
    json_path.write_text(
        json.dumps(
            {
                "role_queues": [
                    {"role": "商品运营", "tasks": ["FW-001"], "waiting_items": []},
                    {"role": "卖家/店铺运营", "tasks": [], "waiting_items": ["等待证据"]},
                    {"role": "物流履约", "tasks": [], "waiting_items": ["等待证据"]},
                    {"role": "客服体验", "tasks": [], "waiting_items": ["等待证据"]},
                    {"role": "数据分析", "tasks": [], "waiting_items": ["等待证据"]},
                ],
                "workorders": [
                    {
                        "workorder_id": "FW-001",
                        "role": "商品运营",
                        "object_name": "商品池",
                        "action_steps": ["复核"],
                        "why_now": "GMV 1000",
                        "owner_role": "商品运营",
                        "deadline": "T+7",
                        "validation_metrics": ["GMV"],
                        "pass_criteria": "完成",
                        "fail_criteria": "未完成",
                        "escalation_rule": "升级",
                        "derived_metric_ids": ["freight_to_gmv"],
                        "evidence": [],
                        "source_refs": ["09a"],
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        pipeline_service_module._validate_ecommerce_frontline_workorder_pack(md_path, json_path)


def test_ecommerce_frontline_workorder_prompt_defines_role_workorders() -> None:
    prompt = build_ecommerce_frontline_workorder_prompt(
        workspace_path="E:/workspace",
        task_index_path="E:/workspace/09a_frontline_task_index.json",
        metric_consumption_path="E:/workspace/01b_ecommerce_metric_consumption_index.json",
    )

    assert "role-based task board" in prompt
    assert "09_frontline_workorder_pack.json" in prompt
    assert "商品运营" in prompt
    assert "Do not use `复核` as the only action" in prompt


def test_sanitize_ecommerce_frontline_workorder_pack_removes_appendix_only_metrics(tmp_path: Path) -> None:
    md_path = tmp_path / "09_frontline_workorder_pack.md"
    json_path = tmp_path / "09_frontline_workorder_pack.json"
    metric_payload = {
        "body_primary_metrics": [
            {"metric_id": "category_gmv_contribution_planned", "metric_name": "类目GMV贡献度", "business_meaning": "头部类目规模贡献"},
            {"metric_id": "freight_to_gmv_planned", "metric_name": "运费占GMV比率", "business_meaning": "运费压力"},
        ],
        "appendix_metrics": [
            {"metric_id": "cpm_derived", "metric_name": "千次触达成本参考指标", "business_meaning": "附录技术留档"},
            {"metric_id": "quality_proxy", "metric_name": "商品质量代理", "business_meaning": "附录风险注记"},
        ],
    }
    md_path.write_text("# 一线工单\n- 为什么现在处理：housewares ... cpm_derived\n", encoding="utf-8")
    json_path.write_text(
        json.dumps(
            {
                "role_queues": [
                    {"role": "商品运营", "tasks": ["FW-003"], "waiting_items": []},
                    {"role": "卖家/店铺运营", "tasks": [], "waiting_items": ["等待证据"]},
                    {"role": "物流履约", "tasks": [], "waiting_items": ["等待证据"]},
                    {"role": "客服体验", "tasks": [], "waiting_items": ["等待证据"]},
                    {"role": "数据分析", "tasks": [], "waiting_items": ["等待证据"]},
                ],
                "workorders": [
                    {
                        "workorder_id": "FW-003",
                        "role": "商品运营",
                        "object_type": "category",
                        "object_name": "housewares",
                        "priority": "P1",
                        "why_now": "housewares 当前 GMV 5,067.71、运费/GMV 17.04%，且 cpm_derived 参考值 5,821.35 很高。",
                        "action_steps": ["拉出高费率订单", "核对包材和重量带"],
                        "owner_role": "商品运营",
                        "deadline": "T+3",
                        "validation_metrics": ["category_gmv_contribution_planned", "freight_to_gmv_planned", "cpm_derived", "quality_proxy"],
                        "pass_criteria": "完成 01b_ecommerce_metric_consumption_index.json 对照",
                        "fail_criteria": "未完成",
                        "escalation_rule": "升级给商品负责人",
                        "derived_metric_ids": ["category_gmv_contribution_planned", "freight_to_gmv_planned", "cpm_derived"],
                        "evidence": ["09a: housewares sample_size=57, gmv_sum=5,067.71, freight_sum=863.41"],
                        "source_refs": ["01b_ecommerce_metric_consumption_index.json", "chart_insights.json"],
                    }
                ],
                "blocked_items": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    payload = pipeline_service_module._sanitize_ecommerce_frontline_workorder_pack(md_path, json_path, metric_payload)
    workorder = payload["workorders"][0]

    assert "cpm_derived" not in " ".join(workorder["validation_metrics"])
    assert "quality_proxy" not in " ".join(workorder["validation_metrics"])
    assert "类目GMV贡献度" in " ".join(workorder["validation_metrics"])
    assert "指标合同" not in " ".join(workorder.get("source_refs") or [])
    assert "cpm_derived" not in workorder["why_now"]
    assert "09a:" not in workorder["why_now"]
    assert "类目GMV贡献度" in workorder["why_now"] or "运费占GMV比率" in workorder["why_now"]
    assert "cpm_derived" not in " ".join(workorder.get("derived_metric_ids") or [])
    assert "cpm_derived" not in " ".join(workorder.get("evidence") or [])
    assert "quality_proxy" not in " ".join(workorder.get("validation_metrics") or [])


def test_sanitize_ecommerce_reader_html_labels_rewrites_machine_titles(tmp_path: Path) -> None:
    html_path = tmp_path / "06_report.html"
    html_path.write_text(
        "<html><body><h3>metric_id 全量索引</h3><table><tr><th>metric_id</th></tr></table>"
        "<p class=\"footer-note\">本 HTML 按 <code>05_report.md</code> 的章节顺序组织，并按 reader interpretation pack 增加表格阅读卡。</p></body></html>",
        encoding="utf-8",
    )

    pipeline_service_module._sanitize_ecommerce_reader_html_labels(html_path)
    updated = html_path.read_text(encoding="utf-8")

    assert "metric_id 全量索引" not in updated
    assert "指标全量索引" in updated
    assert ">指标代码<" in updated
    assert "reader interpretation pack" not in updated
    assert "05_report.md" not in updated


def test_register_ecommerce_long_cli_pipeline_output_copies_shadow_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    report_id = "ecomshadow03"
    report_dir = report_service_module.REPORTS_DIR / f"smart-report-{report_id}"
    report_dir.mkdir(parents=True, exist_ok=True)

    workspace_dir = tmp_path / "pipeline-workspace"
    workspace_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = workspace_dir / "07_report.pdf"
    md_path = workspace_dir / "05_report.md"
    html_path = workspace_dir / "06_report.html"
    css_path = workspace_dir / "06_report.css"
    chart_insights_path = workspace_dir / "chart_insights.json"
    pdf_path.write_bytes(b"%PDF-1.4 ecommerce shadow")
    md_path.write_text("# shadow report\n", encoding="utf-8")
    html_path.write_text("<html><body>shadow</body></html>", encoding="utf-8")
    css_path.write_text("body { color: #111; }", encoding="utf-8")
    chart_insights_path.write_text(json.dumps({"figures": []}, ensure_ascii=False), encoding="utf-8")

    pipeline_payload = {
        "pipeline_type": "ecommerce_long_cli_pipeline",
        "status": "completed",
        "linked_report_id": report_id,
        "pipeline_job_id": "codex-pipeline-ecomshadow03",
        "linked_codex_run_ids": ["run-001"],
        "final_output": {
            "main_artifact_path": str(pdf_path.resolve()),
            "main_artifact_url": "/storage/workspace/07_report.pdf",
            "markdown_path": str(md_path.resolve()),
            "html_path": str(html_path.resolve()),
            "css_path": str(css_path.resolve()),
            "chart_insights_path": str(chart_insights_path.resolve()),
        },
    }
    monkeypatch.setattr(report_service_module, "get_pipeline_job", lambda _job_id: pipeline_payload)

    result = register_ecommerce_long_cli_pipeline_output("codex-pipeline-ecomshadow03")

    assert (report_dir / f"{report_id}-ecommerce_cli_shadow.pdf").exists()
    assert (report_dir / f"{report_id}-ecommerce_cli_shadow.md").exists()
    assert (report_dir / f"{report_id}-ecommerce_cli_shadow.html").exists()
    assert (report_dir / f"{report_id}-ecommerce_cli_shadow.css").exists()
    assert (report_dir / f"{report_id}-ecommerce_cli_shadow_chart_insights.json").exists()
    assert result["registered_downloadable"]["name"] == f"{report_id}-ecommerce_cli_shadow.pdf"
    assert result["pipeline_type"] == "ecommerce_long_cli_pipeline"


def test_register_ecommerce_long_cli_pipeline_output_copies_frontline_pack(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    report_id = "ecomfrontline01"
    report_dir = report_service_module.REPORTS_DIR / f"smart-report-{report_id}"
    report_dir.mkdir(parents=True, exist_ok=True)

    workspace_dir = tmp_path / "pipeline-workspace-frontline"
    workspace_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = workspace_dir / "07_report.pdf"
    md_path = workspace_dir / "05_report.md"
    html_path = workspace_dir / "06_report.html"
    css_path = workspace_dir / "06_report.css"
    chart_insights_path = workspace_dir / "chart_insights.json"
    frontline_pdf = workspace_dir / "09_frontline_action_pack.pdf"
    frontline_md = workspace_dir / "09_frontline_action_pack.md"
    frontline_html = workspace_dir / "09_frontline_action_pack.html"
    frontline_css = workspace_dir / "09_frontline_action_pack.css"
    frontline_json = workspace_dir / "09_frontline_action_pack.json"
    pdf_path.write_bytes(b"%PDF-1.4 ecommerce shadow")
    md_path.write_text("# shadow report\n", encoding="utf-8")
    html_path.write_text("<html><body>shadow</body></html>", encoding="utf-8")
    css_path.write_text("body { color: #111; }", encoding="utf-8")
    chart_insights_path.write_text(json.dumps({"figures": []}, ensure_ascii=False), encoding="utf-8")
    frontline_pdf.write_bytes(b"%PDF-1.4 frontline")
    frontline_md.write_text("# 一线执行版\n", encoding="utf-8")
    frontline_html.write_text("<html><body>一线执行版</body></html>", encoding="utf-8")
    frontline_css.write_text("body { color: #123; }", encoding="utf-8")
    frontline_json.write_text(json.dumps({"frontline_actions": []}, ensure_ascii=False), encoding="utf-8")

    pipeline_payload = {
        "pipeline_type": "ecommerce_long_cli_pipeline",
        "status": "completed",
        "linked_report_id": report_id,
        "pipeline_job_id": "codex-pipeline-ecomfrontline01",
        "linked_codex_run_ids": ["run-001"],
        "final_output": {
            "main_artifact_path": str(pdf_path.resolve()),
            "main_artifact_url": "/storage/workspace/07_report.pdf",
            "markdown_path": str(md_path.resolve()),
            "html_path": str(html_path.resolve()),
            "css_path": str(css_path.resolve()),
            "chart_insights_path": str(chart_insights_path.resolve()),
            "frontline_action_pack_pdf_path": str(frontline_pdf.resolve()),
            "frontline_action_pack_markdown_path": str(frontline_md.resolve()),
            "frontline_action_pack_html_path": str(frontline_html.resolve()),
            "frontline_action_pack_css_path": str(frontline_css.resolve()),
            "frontline_action_pack_json_path": str(frontline_json.resolve()),
        },
    }
    monkeypatch.setattr(report_service_module, "get_pipeline_job", lambda _job_id: pipeline_payload)

    result = register_ecommerce_long_cli_pipeline_output("codex-pipeline-ecomfrontline01")

    assert (report_dir / f"{report_id}-ecommerce_cli_frontline_action_pack.pdf").exists()
    assert (report_dir / f"{report_id}-ecommerce_cli_frontline_action_pack.html").exists()
    frontline_items = [
        item
        for item in result["downloadables"]
        if item.get("name") == f"{report_id}-ecommerce_cli_frontline_action_pack.pdf"
    ]
    assert frontline_items
    assert frontline_items[0]["purpose"] == "Codex CLI 电商一线执行版 PDF"


def test_register_ecommerce_long_cli_pipeline_output_preserves_existing_main_downloadable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    report_id = "ecomshadowmain01"
    report_dir = report_service_module.REPORTS_DIR / f"smart-report-{report_id}"
    report_dir.mkdir(parents=True, exist_ok=True)

    main_pdf = report_dir / f"{report_id}-management_report.pdf"
    main_pdf.write_bytes(b"%PDF-1.4 main report")
    existing_manifest = {
        "report_id": report_id,
        "dataset_name": "鐢靛晢鏁版嵁",
        "sheet_name": "Sheet1",
        "business_profile": "ecommerce_product_operations_report",
        "report_lens": "procurement_sales_review",
        "generated_at": "2026-05-02T00:00:00Z",
        "main_downloadable": main_pdf.name,
        "downloadables": [
            {
                "name": main_pdf.name,
                "file_path": str(main_pdf.resolve()),
                "purpose": "main report",
                "is_main": True,
                "type": "pdf",
            }
        ],
    }
    (report_dir / f"{report_id}-current_turn_export_manifest.json").write_text(
        json.dumps(existing_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    workspace_dir = tmp_path / "pipeline-workspace-main"
    workspace_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = workspace_dir / "07_report.pdf"
    md_path = workspace_dir / "05_report.md"
    html_path = workspace_dir / "06_report.html"
    css_path = workspace_dir / "06_report.css"
    chart_insights_path = workspace_dir / "chart_insights.json"
    pdf_path.write_bytes(b"%PDF-1.4 ecommerce shadow")
    md_path.write_text("# shadow report\n", encoding="utf-8")
    html_path.write_text("<html><body>shadow</body></html>", encoding="utf-8")
    css_path.write_text("body { color: #111; }", encoding="utf-8")
    chart_insights_path.write_text(json.dumps({"figures": []}, ensure_ascii=False), encoding="utf-8")

    pipeline_payload = {
        "pipeline_type": "ecommerce_long_cli_pipeline",
        "status": "completed",
        "linked_report_id": report_id,
        "pipeline_job_id": "codex-pipeline-ecomshadowmain01",
        "linked_codex_run_ids": ["run-001"],
        "final_output": {
            "main_artifact_path": str(pdf_path.resolve()),
            "main_artifact_url": "/storage/workspace/07_report.pdf",
            "markdown_path": str(md_path.resolve()),
            "html_path": str(html_path.resolve()),
            "css_path": str(css_path.resolve()),
            "chart_insights_path": str(chart_insights_path.resolve()),
        },
    }
    monkeypatch.setattr(report_service_module, "get_pipeline_job", lambda _job_id: pipeline_payload)

    register_ecommerce_long_cli_pipeline_output("codex-pipeline-ecomshadowmain01")

    rewritten_manifest = json.loads(
        (report_dir / f"{report_id}-current_turn_export_manifest.json").read_text(encoding="utf-8")
    )
    assert rewritten_manifest["main_downloadable"] == main_pdf.name
    main_items = [item for item in rewritten_manifest["downloadables"] if item.get("name") == main_pdf.name]
    assert main_items and bool(main_items[0].get("is_main")) is True
    shadow_items = [
        item for item in rewritten_manifest["downloadables"] if item.get("name") == f"{report_id}-ecommerce_cli_shadow.pdf"
    ]
    assert shadow_items and bool(shadow_items[0].get("is_main")) is False


def test_register_ecommerce_long_cli_pipeline_output_recovers_main_downloadable_when_manifest_lost_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    report_id = "ecomshadowrecover01"
    report_dir = report_service_module.REPORTS_DIR / f"smart-report-{report_id}"
    report_dir.mkdir(parents=True, exist_ok=True)

    main_pdf = report_dir / f"{report_id}-management_report.pdf"
    main_pdf.write_bytes(b"%PDF-1.4 main report")
    broken_manifest = {
        "report_id": report_id,
        "dataset_name": "鐢靛晢鏁版嵁",
        "sheet_name": "Sheet1",
        "business_profile": "ecommerce_product_operations_report",
        "report_lens": "procurement_sales_review",
        "generated_at": "2026-05-02T00:00:00Z",
        "main_downloadable": "",
        "downloadables": [
            {
                "name": main_pdf.name,
                "file_path": str(main_pdf.resolve()),
                "purpose": "main report",
                "is_main": False,
                "type": "pdf",
            }
        ],
    }
    (report_dir / f"{report_id}-current_turn_export_manifest.json").write_text(
        json.dumps(broken_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    workspace_dir = tmp_path / "pipeline-workspace-recover"
    workspace_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = workspace_dir / "07_report.pdf"
    md_path = workspace_dir / "05_report.md"
    html_path = workspace_dir / "06_report.html"
    css_path = workspace_dir / "06_report.css"
    chart_insights_path = workspace_dir / "chart_insights.json"
    pdf_path.write_bytes(b"%PDF-1.4 ecommerce shadow")
    md_path.write_text("# shadow report\n", encoding="utf-8")
    html_path.write_text("<html><body>shadow</body></html>", encoding="utf-8")
    css_path.write_text("body { color: #111; }", encoding="utf-8")
    chart_insights_path.write_text(json.dumps({"figures": []}, ensure_ascii=False), encoding="utf-8")

    pipeline_payload = {
        "pipeline_type": "ecommerce_long_cli_pipeline",
        "status": "completed",
        "linked_report_id": report_id,
        "pipeline_job_id": "codex-pipeline-ecomshadowrecover01",
        "linked_codex_run_ids": ["run-001"],
        "final_output": {
            "main_artifact_path": str(pdf_path.resolve()),
            "main_artifact_url": "/storage/workspace/07_report.pdf",
            "markdown_path": str(md_path.resolve()),
            "html_path": str(html_path.resolve()),
            "css_path": str(css_path.resolve()),
            "chart_insights_path": str(chart_insights_path.resolve()),
        },
    }
    monkeypatch.setattr(report_service_module, "get_pipeline_job", lambda _job_id: pipeline_payload)

    register_ecommerce_long_cli_pipeline_output("codex-pipeline-ecomshadowrecover01")

    rewritten_manifest = json.loads(
        (report_dir / f"{report_id}-current_turn_export_manifest.json").read_text(encoding="utf-8")
    )
    assert rewritten_manifest["main_downloadable"] == main_pdf.name
    main_items = [item for item in rewritten_manifest["downloadables"] if item.get("name") == main_pdf.name]
    assert main_items and bool(main_items[0].get("is_main")) is True


def test_export_manifest_includes_ecommerce_shadow_fields(tmp_path: Path) -> None:
    report_dir = tmp_path / "report"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_payload = {
        "report_id": "ecomshadow04",
        "dataset_name": "鐢靛晢鏁版嵁",
        "sheet_name": "Sheet1",
        "business_profile": "ecommerce_product_operations_report",
        "report_lens": "procurement_sales_review",
        "ecommerce_long_cli_pipeline_job_id": "codex-pipeline-ecomshadow04",
        "ecommerce_long_cli_pipeline": {
            "status": "running",
            "current_stage_id": "ecommerce_inventory",
        },
        "ecommerce_long_cli_final_output": {"main_artifact_url": "/storage/demo.pdf"},
        "ecommerce_metric_consumption_index_path": "E:/workspace/01b_ecommerce_metric_consumption_index.json",
        "ecommerce_metric_coverage_summary": {"metric_universe_count": 5, "missing_metric_ids": []},
        "ecommerce_metric_universe_count": 5,
        "ecommerce_metric_missing_ids": [],
    }
    _append_current_turn_export_manifest(
        report_dir=report_dir,
        report_id="ecomshadow04",
        report=report_payload,
        artifact_bundle={"downloadables": []},
    )
    manifest = json.loads(
        (report_dir / "ecomshadow04-current_turn_export_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["ecommerce_long_cli_pipeline_job_id"] == "codex-pipeline-ecomshadow04"
    assert manifest["ecommerce_long_cli_pipeline_status"] == "running"
    assert manifest["ecommerce_long_cli_pipeline_current_stage"] == "ecommerce_inventory"
    assert manifest["ecommerce_long_cli_final_output"]["main_artifact_url"] == "/storage/demo.pdf"
    assert manifest["ecommerce_metric_universe_count"] == 5
    assert manifest["ecommerce_metric_missing_ids"] == []


def test_ecommerce_table_fact_pack_creates_required_artifacts(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    _frame().to_csv(workspace / "source_dataset.csv", index=False, encoding="utf-8-sig")

    payload = pipeline_service_module._write_ecommerce_table_fact_pack(
        workspace,
        {"source_dataset_path": "source_dataset.csv"},
    )

    assert payload["dimension_count"] > 0
    assert (workspace / "01a_ecommerce_table_fact_pack.md").exists()
    assert (workspace / "01a_ecommerce_table_fact_pack.json").exists()
    assert (workspace / "01a_dimension_catalog.json").exists()
    assert (workspace / "01a_dimension_detail_summary.csv").exists()
    assert (workspace / "01a_object_pool_registry.json").exists()
    assert (workspace / "01a_exception_casebook.json").exists()
    assert (workspace / "01a_metric_cube_overview.json").exists()


def test_derived_metric_family_planning_prompt_forbids_final_values() -> None:
    prompt = build_derived_metric_family_planning_prompt(
        workspace_path="E:/workspace",
        planning_input_pack_path="E:/workspace/01c_metric_planning_input_pack.json",
        context_payload={"allowed_formula_families": ["ratio", "contribution"]},
    )

    assert "Do NOT compute final metric values" in prompt
    assert "01c_metric_planning_input_pack.json" in prompt
    assert "Do NOT run PowerShell or shell exploration" in prompt
    assert "formula_family" in prompt
    assert "Simplified Chinese" in prompt
    assert "metric_name`, `business_meaning`" in prompt
    assert "eligible_metric_family_targets" in prompt


def test_derived_metric_family_input_pack_detects_core_ecommerce_roles(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    _runtime_cli_frame().to_csv(workspace / "source_dataset.csv", index=False, encoding="utf-8-sig")
    (workspace / "00_requirement_intent.md").write_text("# intent\n", encoding="utf-8")
    (workspace / "00_requirement_intent.json").write_text(
        json.dumps({"target_audience": "管理层", "core_purpose": "经营诊断"}, ensure_ascii=False),
        encoding="utf-8",
    )
    pipeline_service_module._write_ecommerce_table_fact_pack(
        workspace,
        {"source_dataset_path": "source_dataset.csv"},
    )

    payload = pipeline_service_module._write_derived_metric_family_input_pack(workspace, {"source_dataset_path": "source_dataset.csv"})

    role_index = dict(payload.get("role_index") or {})
    assert role_index["gmv"] == "GMV"
    assert role_index["revenue"] == "Revenue"
    assert role_index["freight"] == "FreightCost"
    assert role_index["order_id"] == "OrderID"
    assert role_index["order_purchase_time"] == "OrderPurchaseTimestamp"
    assert role_index["review_score"] == "ReviewScore"
    assert role_index["seller_state"] == "SellerState"
    assert role_index["customer_state"] == "CustomerState"
    target_ids = {str(item.get("target_metric_id") or "") for item in list(payload.get("eligible_metric_family_targets") or [])}
    assert {
        "freight_to_gmv_planned",
        "freight_to_revenue_planned",
        "late_fulfillment_rate_planned",
        "route_delay_risk_planned",
        "gmv_time_trend_planned",
    }.issubset(target_ids)
    assert (workspace / "01c_metric_planning_input_pack.json").exists()
    assert (workspace / "01c_metric_planning_input_pack.md").exists()


def test_validate_derived_metric_family_plan_rejects_empty_specs_even_with_fallback_shape(tmp_path: Path) -> None:
    md_path = tmp_path / "01c_derived_metric_family_plan.md"
    json_path = tmp_path / "01c_derived_metric_family_plan.json"
    input_pack_path = tmp_path / "01c_metric_planning_input_pack.json"
    md_path.write_text("# plan\n", encoding="utf-8")
    input_pack_path.write_text(
        json.dumps(
            {
                "dataset_summary": {"row_count": 18},
                "field_role_candidates": [{"role_id": "gmv", "column_name": "GMV"}],
                "role_index": {"gmv": "GMV"},
                "column_profiles": [{"column_name": "GMV"}],
                "metric_cube_overview_summary": {},
                "dimension_catalog_summary": {},
                "route_summary": {},
                "legacy_metric_summary": {},
                "eligible_metric_family_targets": [
                    {"target_metric_id": "freight_to_gmv_planned", "reader_title": "运费成交额占比"}
                ],
                "core_field_usage_requirements": [{"role_id": "gmv", "column_name": "GMV", "must_be_used_or_explained": True}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    json_path.write_text(
        json.dumps(
            {
                "field_role_candidates": [{"role_id": "gmv", "column_name": "GMV"}],
                "metric_families": ["freight_efficiency"],
                "metric_specs_draft": [],
                "unsupported_metric_families": [
                    {"metric_family": "derived_metric_family_planning", "reason": "timeout"}
                ],
                "execution_requirements": {},
                "risk_notes": ["timeout"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="metric_specs_draft"):
        pipeline_service_module._validate_derived_metric_family_plan(md_path, json_path)


def test_derived_metric_family_execution_computes_whitelisted_specs(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    _frame().to_csv(workspace / "source_dataset.csv", index=False, encoding="utf-8-sig")
    (workspace / "01c_derived_metric_family_plan.json").write_text(
        json.dumps(
            {
                "field_role_candidates": [],
                "metric_families": ["ratio", "contribution", "rating_risk"],
                "metric_specs_draft": [
                    {
                        "metric_id": "gmv_per_order_planned",
                        "metric_name": "鍗曞潎鎴愪氦棰?",
                        "formula_family": "ratio",
                        "source_columns": ["GMV", "order_count"],
                        "numerator_column": "GMV",
                        "denominator_column": "order_count",
                        "business_meaning": "鐢ㄤ簬鍒ゆ柇鍗曠瑪璁㈠崟鎴愪氦鏁堢巼銆?",
                    },
                    {
                        "metric_id": "category_gmv_contribution_planned",
                        "metric_name": "绫荤洰鎴愪氦棰濋泦涓害",
                        "formula_family": "contribution",
                        "source_columns": ["category", "GMV"],
                        "dimension_column": "category",
                        "value_column": "GMV",
                        "business_meaning": "鐢ㄤ簬鍒ゆ柇绫荤洰鎴愪氦棰濇槸鍚﹁繃搴﹂泦涓€?",
                    },
                    {
                        "metric_id": "low_rating_risk_planned",
                        "metric_name": "浣庤瘎鍒嗛闄╃巼",
                        "formula_family": "rating_risk",
                        "source_columns": ["rating"],
                        "rating_column": "rating",
                        "low_rating_threshold": 4.3,
                        "business_meaning": "鐢ㄤ簬鍒ゆ柇鍟嗗搧浣撻獙鍜屽敭鍚庨闄┿€?",
                    },
                ],
                "unsupported_metric_families": [],
                "execution_requirements": {},
                "risk_notes": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    payload = execute_derived_metric_family_specs(workspace)

    assert payload["derived_metric_family_count"] == 3
    assert payload["derived_metric_family_executed_count"] == 3
    assert (workspace / "01c_derived_metrics_table.csv").exists()
    assert (workspace / "01c_proxy_metrics_table.csv").exists()
    assert (workspace / "01c_derived_metric_execution_log.csv").exists()
    derived_rows = pd.read_csv(workspace / "01c_derived_metrics_table.csv", encoding="utf-8-sig")
    proxy_rows = pd.read_csv(workspace / "01c_proxy_metrics_table.csv", encoding="utf-8-sig")
    assert {"gmv_per_order_planned", "category_gmv_contribution_planned"}.issubset(set(derived_rows["metric_id"]))
    assert "low_rating_risk_planned" in set(proxy_rows["metric_id"])
    assert all(any("\u4e00" <= char <= "\u9fff" for char in str(value)) for value in derived_rows["metric_name"])
    assert all(any("\u4e00" <= char <= "\u9fff" for char in str(value)) for value in proxy_rows["metric_name"])


def test_derived_metric_family_execution_marks_unknown_or_missing_specs_unsupported(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    _frame().to_csv(workspace / "source_dataset.csv", index=False, encoding="utf-8-sig")
    (workspace / "01c_derived_metric_family_plan.json").write_text(
        json.dumps(
            {
                "field_role_candidates": [],
                "metric_families": ["unknown"],
                "metric_specs_draft": [
                    {
                        "metric_id": "bad_metric",
                        "metric_name": "鏃犳晥鎸囨爣",
                        "formula_family": "freeform_python",
                        "source_columns": ["GMV"],
                    },
                    {
                        "metric_id": "missing_metric",
                        "metric_name": "缂哄瓧娈垫寚鏍?",
                        "formula_family": "ratio",
                        "source_columns": ["missing_col", "GMV"],
                        "numerator_column": "missing_col",
                        "denominator_column": "GMV",
                    },
                ],
                "unsupported_metric_families": [],
                "execution_requirements": {},
                "risk_notes": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    payload = execute_derived_metric_family_specs(workspace)

    assert payload["derived_metric_family_executed_count"] == 0
    assert payload["derived_metric_family_unsupported_count"] == 2
    unsupported = pd.read_csv(workspace / "01c_unsupported_metrics_table.csv", encoding="utf-8-sig")
    assert {"bad_metric", "missing_metric"}.issubset(set(unsupported["metric_id"]))


def test_derived_metric_family_execution_supports_distinct_count_and_row_count_denominators(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    _runtime_cli_frame().to_csv(workspace / "source_dataset.csv", index=False, encoding="utf-8-sig")
    (workspace / "01c_derived_metric_family_plan.json").write_text(
        json.dumps(
            {
                "field_role_candidates": [{"role_id": "order_id", "column_name": "OrderID"}],
                "metric_families": ["freight_efficiency", "ratio", "late_fulfillment"],
                "metric_specs_draft": [
                    {
                        "metric_id": "freight_to_revenue_planned",
                        "metric_name": "运费收入占比",
                        "formula_family": "freight_efficiency",
                        "source_columns": ["FreightCost", "Revenue"],
                        "freight_column": "FreightCost",
                        "denominator_column": "Revenue",
                        "denominator_mode": "sum",
                        "business_meaning": "用于判断运费成本相对收入的压力。",
                    },
                    {
                        "metric_id": "gmv_per_order_planned",
                        "metric_name": "单均成交额",
                        "formula_family": "ratio",
                        "source_columns": ["GMV", "OrderID"],
                        "numerator_column": "GMV",
                        "denominator_column": "OrderID",
                        "denominator_mode": "distinct_count",
                        "business_meaning": "用于判断订单层面的平均成交贡献。",
                    },
                    {
                        "metric_id": "late_fulfillment_rate_planned",
                        "metric_name": "延迟履约率",
                        "formula_family": "late_fulfillment",
                        "source_columns": ["IsLate"],
                        "late_flag_column": "IsLate",
                        "proxy_only": True,
                        "business_meaning": "用于判断当前周期的延迟履约风险。",
                    },
                ],
                "unsupported_metric_families": [],
                "execution_requirements": {},
                "risk_notes": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    payload = execute_derived_metric_family_specs(workspace)

    assert payload["derived_metric_family_executed_count"] == 3
    derived_rows = pd.read_csv(workspace / "01c_derived_metrics_table.csv", encoding="utf-8-sig")
    proxy_rows = pd.read_csv(workspace / "01c_proxy_metrics_table.csv", encoding="utf-8-sig")
    assert "gmv_per_order_planned" in set(derived_rows["metric_id"])
    assert "freight_to_revenue_planned" in set(derived_rows["metric_id"])
    assert "late_fulfillment_rate_planned" in set(proxy_rows["metric_id"])


def test_ecommerce_metric_consumption_pack_reads_all_derived_and_proxy_metrics(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    _seed_metric_mining_workspace(workspace)

    payload = pipeline_service_module._write_ecommerce_metric_consumption_pack(workspace)

    metric_ids = {str(item.get("metric_id") or "") for item in list(payload.get("metric_universe") or [])}
    assert metric_ids == {
        "cpm_derived",
        "cpa_derived",
        "top_object_amount_contribution",
        "overall_trend_change",
        "quality_proxy",
    }
    assert (workspace / "01b_ecommerce_metric_consumption_index.json").exists()
    assert (workspace / "01b_ecommerce_metric_body_priority.csv").exists()
    assert (workspace / "01b_ecommerce_metric_appendix_priority.csv").exists()
    assert all(
        any("\u4e00" <= char <= "\u9fff" for char in str(item.get("metric_name") or ""))
        for item in list(payload.get("metric_universe") or [])
    )
    assert all(
        any("\u4e00" <= char <= "\u9fff" for char in str(item.get("business_meaning") or ""))
        for item in list(payload.get("metric_universe") or [])
    )


def test_ecommerce_metric_consumption_pack_merges_derived_family_execution(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    _seed_metric_mining_workspace(workspace)
    pd.DataFrame(
        [
            {
                "business_profile": "ecommerce_product_operations_report",
                "metric_id": "freight_to_gmv_planned",
                "metric_name": "杩愯垂鎴愪氦棰濆崰姣?",
                "source_columns": "['freight', 'GMV']",
                "formula": "sum(freight) / sum(GMV)",
                "value": "0.08",
                "evidence_level": "B_DERIVED",
                "confidence": "medium",
                "metric_kind": "derived_metric",
                "business_meaning": "鐢ㄤ簬鍒ゆ柇杩愯垂鎴愭湰鐩稿鎴愪氦棰濈殑鍘嬪姏銆?",
                "note": "computed from 01c execution",
            }
        ]
    ).to_csv(workspace / "01c_derived_metrics_table.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame([]).to_csv(workspace / "01c_proxy_metrics_table.csv", index=False, encoding="utf-8-sig")
    (workspace / "01c_derived_metric_family_execution.json").write_text(
        json.dumps(
            {
                "derived_metric_family_count": 1,
                "derived_metric_family_executed_count": 1,
                "derived_metric_family_unsupported_count": 0,
            }
        ),
        encoding="utf-8",
    )

    payload = pipeline_service_module._write_ecommerce_metric_consumption_pack(workspace)

    metric_ids = {str(item.get("metric_id") or "") for item in list(payload.get("metric_universe") or [])}
    assert "freight_to_gmv_planned" in metric_ids
    assert payload["metric_source_index"]["derived_metric_family_executed_count"] == 1


def test_ecommerce_metric_consumption_pack_classifies_every_metric_id(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    _seed_metric_mining_workspace(workspace)

    payload = pipeline_service_module._write_ecommerce_metric_consumption_pack(workspace)

    assert payload["all_metric_ids_classified"] is True
    assert payload["metric_universe_count"] == (
        len(payload["body_primary_metrics"]) + len(payload["body_support_metrics"]) + len(payload["appendix_metrics"])
    )
    appendix_ids = {str(item.get("metric_id") or "") for item in list(payload["appendix_metrics"])}
    assert {"cpm_derived", "cpa_derived", "quality_proxy"}.issubset(appendix_ids)


def test_ecommerce_question_tree_requires_derived_metric_ids(tmp_path: Path) -> None:
    md_path = tmp_path / "02_ecommerce_question_tree.md"
    json_path = tmp_path / "02_ecommerce_question_tree.json"
    md_path.write_text("# question tree\n", encoding="utf-8")
    json_path.write_text(
        json.dumps(
            {
                "root_question": "濡備綍鎻愬崌缁忚惀璐ㄩ噺",
                "question_nodes": [
                    {
                        "node_id": "Q1",
                        "node_title": "绫荤洰缁撴瀯",
                        "evidence_sources": ["01a_dimension_detail_summary.csv:category"],
                        "dimension_ids": ["category"],
                        "object_pool_ids": ["category_pool"],
                        "route_ids": [],
                        "text_theme_ids": [],
                    }
                ],
                "analysis_paths": ["Q1"],
                "decision_questions": ["Q1"],
                "recommended_sections": ["S03"],
                "action_focus_objects": ["health_beauty"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="derived_metric_ids"):
        pipeline_service_module._validate_ecommerce_question_tree(md_path, json_path)


def test_parse_dimension_tokens_preserves_double_colon_and_extra_prefix() -> None:
    assert pipeline_service_module._parse_dimension_tokens_from_table_ref(
        "01a_dimension_detail_summary.csv::extra_DelayDays"
    ) == ["extra_DelayDays"]
    assert pipeline_service_module._parse_dimension_tokens_from_table_ref(
        "01a_dimension_pair_summary.csv::category__shop_seller"
    ) == ["category", "shop_seller"]


def test_ecommerce_long_outline_requires_metric_usage_per_section(tmp_path: Path) -> None:
    md_path = tmp_path / "03_ecommerce_long_outline.md"
    json_path = tmp_path / "03_ecommerce_long_outline.json"
    md_path.write_text("# outline\n", encoding="utf-8")
    json_path.write_text(
        json.dumps(
            {
                "headline_thesis": "demo",
                "section_plan": [
                    {"section_id": f"S0{i}", "section_title": f"s{i}", "table_inputs": ["T1"], "dimension_focus": ["category"], "object_pools": ["category_pool"]}
                    for i in range(1, 7)
                ],
                "batch_plan": [{"batch_index": 1}, {"batch_index": 2}, {"batch_index": 3}, {"batch_index": 4}],
                "required_tables": ["T1"],
                "required_figures_or_visual_blocks": ["F1"],
                "recommendation_backbone": ["A1"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="derived_metric_ids"):
        pipeline_service_module._validate_ecommerce_long_report_outline(md_path, json_path)


def test_ecommerce_section_batch_requires_derived_metrics_used(tmp_path: Path) -> None:
    md_path = tmp_path / "04_ecommerce_section_batch_01.md"
    json_path = tmp_path / "04_ecommerce_section_batch_01.json"
    md_path.write_text(("# Batch 1\n\n| KPI | value |\n| --- | --- |\n" + "缁忚惀寤鸿 鏄庣粏 KPI 琛屽姩\n" * 220), encoding="utf-8")
    json_path.write_text(
        json.dumps(
            {
                "batch_index": 1,
                "section_ids": ["s1", "s2"],
                "section_titles": ["products", "categories"],
                "completion_status": "completed",
                "tables_used": ["category"],
                "named_objects_used": ["health_beauty"],
                "dimension_tables_used": ["category"],
                "route_tables_used": [],
                "text_evidence_blocks_used": [],
                "current_period_metrics_used": ["gmv"],
                "table_fact_ids_used": ["category_01"],
                "derived_metrics_used": [],
                "derived_metric_tables_used": ["01b_ecommerce_metric_body_priority.csv"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="derived metrics used"):
        pipeline_service_module._validate_ecommerce_section_batch(md_path, json_path, 1)


def test_validate_ecommerce_section_batch_requires_data_grounding(tmp_path: Path) -> None:
    md_path = tmp_path / "04_ecommerce_section_batch_01.md"
    json_path = tmp_path / "04_ecommerce_section_batch_01.json"
    md_path.write_text(("# Batch 1\n\n| KPI | value |\n| --- | --- |\n" + "缁忚惀寤鸿 鏄庣粏 KPI 琛屽姩\n" * 220), encoding="utf-8")
    json_path.write_text(
        json.dumps(
            {
                "batch_index": 1,
                "section_ids": ["s1", "s2"],
                "section_titles": ["products", "categories"],
                "completion_status": "completed",
                "tables_used": ["category"],
                "named_objects_used": [],
                "dimension_tables_used": ["category"],
                "route_tables_used": [],
                "text_evidence_blocks_used": [],
                "current_period_metrics_used": ["gmv"],
                "table_fact_ids_used": ["category_01"],
                "derived_metrics_used": ["cpm_derived"],
                "derived_metric_tables_used": ["01b_ecommerce_metric_body_priority.csv"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="must name concrete objects"):
        pipeline_service_module._validate_ecommerce_section_batch(md_path, json_path, 1)


def test_ecommerce_data_utilization_gate_passes_with_grounded_batches(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    _frame().to_csv(workspace / "source_dataset.csv", index=False, encoding="utf-8-sig")
    pipeline_service_module._write_ecommerce_table_fact_pack(
        workspace,
        {"source_dataset_path": "source_dataset.csv"},
    )
    _seed_metric_mining_workspace(workspace)
    pipeline_service_module._write_ecommerce_metric_consumption_pack(workspace)
    (workspace / "05_report.md").write_text(
        "\n".join(
            [
                "# 涓绘姤鍛?",
                "姝ｆ枃浣跨敤 top_object_amount_contribution 鍜?overall_trend_change 浣滀负涓诲垽鏂俊鍙枫€?",
                "## 闄勫綍锛氭淳鐢熸寚鏍?",
                "appendix: cpm_derived / cpa_derived / quality_proxy",
            ]
        ),
        encoding="utf-8",
    )

    object_pools = json.loads((workspace / "01a_object_pool_registry.json").read_text(encoding="utf-8"))
    category_names = [
        str(item.get("dimension_value") or "")
        for item in list(object_pools.get("category") or [])[:2]
        if str(item.get("dimension_value") or "").strip()
    ]
    cases = json.loads((workspace / "01a_exception_casebook.json").read_text(encoding="utf-8"))
    case_ids = [
        str(item.get("case_id") or "")
        for item in list(cases.get("cases") or [])[:2]
        if str(item.get("case_id") or "").strip()
    ]
    if not case_ids:
        case_ids = ["product_01", "category_01"]

    for index in range(1, 5):
        (workspace / f"04_ecommerce_section_batch_{index:02d}.md").write_text(
            ("# Batch\n\n| KPI | value |\n| --- | --- |\n" + "缁忚惀寤鸿 鏄庣粏 KPI 琛屽姩\n" * 220),
            encoding="utf-8",
        )
        (workspace / f"04_ecommerce_section_batch_{index:02d}.json").write_text(
            json.dumps(
                {
                    "batch_index": index,
                    "section_ids": [f"s{index}"],
                    "section_titles": [f"section {index}"],
                    "completion_status": "completed",
                    "tables_used": ["category", "product", "shop_seller"],
                    "named_objects_used": [*category_names, "item-0", "item-1", "item-2", "item-3", "item-4", "shop-0", "shop-1"],
                    "dimension_tables_used": ["category", "product", "shop_seller", "brand"],
                    "route_tables_used": [],
                    "text_evidence_blocks_used": [],
                    "current_period_metrics_used": ["gmv", "sales_volume", "order_count", "inventory", "gross_margin", "refund_rate"],
                    "table_fact_ids_used": case_ids,
                    "derived_metrics_used": ["top_object_amount_contribution", "overall_trend_change", "cpm_derived", "cpa_derived", "quality_proxy"],
                    "derived_metric_tables_used": ["01b_ecommerce_metric_body_priority.csv", "01b_ecommerce_metric_appendix_priority.csv"],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    payload = pipeline_service_module._write_ecommerce_data_utilization_gate(workspace)

    assert payload["passed"] is True
    assert payload["missing_metric_ids"] == []
    assert (workspace / "05a_data_utilization_gate.md").exists()
    assert (workspace / "05a_data_utilization_gate.json").exists()


def test_ecommerce_metric_consistency_prompt_requires_runtime_cli_and_01b_contract() -> None:
    prompt = build_ecommerce_metric_consistency_audit_prompt(
        workspace_path="E:/workspace",
        evidence_pack_path="E:/workspace/05c_metric_consistency_evidence_pack.json",
        metric_consumption_path="E:/workspace/01b_ecommerce_metric_consumption_index.json",
        markdown_report_path="E:/workspace/05_report.md",
        context_payload={"canonical_metric_count": 3},
    )

    assert "runtime CLI" in prompt
    assert "01b_ecommerce_metric_consumption_index.json" in prompt
    assert "appendix_only" in prompt
    assert "headline conclusions" in prompt


def test_ecommerce_delivery_consistency_prompt_forbids_appendix_only_frontline_validation() -> None:
    prompt = build_ecommerce_delivery_consistency_audit_prompt(
        workspace_path="E:/workspace",
        evidence_pack_path="E:/workspace/09b_delivery_consistency_evidence_pack.json",
        metric_consumption_path="E:/workspace/01b_ecommerce_metric_consumption_index.json",
        html_report_path="E:/workspace/06_report.html",
        frontline_workorder_path="E:/workspace/09_frontline_workorder_pack.json",
        metric_consistency_audit_path="E:/workspace/05c_metric_consistency_audit.json",
        context_payload={"canonical_metric_count": 3},
    )

    assert "appendix_only metrics in frontline `validation_metrics`" in prompt
    assert "passed=false" in prompt
    assert "raw `metric_id`" in prompt


def test_validate_ecommerce_runtime_consistency_audit_rejects_blocking_issues(tmp_path: Path) -> None:
    md_path = tmp_path / "05c_metric_consistency_audit.md"
    json_path = tmp_path / "05c_metric_consistency_audit.json"
    md_path.write_text("# audit\n", encoding="utf-8")
    json_path.write_text(
        json.dumps(
            {
                "canonical_metric_contract": [],
                "report_body_findings": [],
                "html_findings": [],
                "frontline_findings": [],
                "blocking_issues": [
                    {
                        "metric_id": "quality_proxy",
                        "issue_type": "appendix_only_frontline_validation",
                        "severity": "blocking",
                    }
                ],
                "retry_recommendations": [],
                "passed": False,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="quality_proxy|appendix_only_frontline_validation"):
        pipeline_service_module._validate_ecommerce_runtime_consistency_audit(
            md_path,
            json_path,
            "ecommerce_metric_consistency_audit",
        )


def test_validate_ecommerce_runtime_consistency_audit_requires_core_keys(tmp_path: Path) -> None:
    md_path = tmp_path / "09b_delivery_consistency_audit.md"
    json_path = tmp_path / "09b_delivery_consistency_audit.json"
    md_path.write_text("# audit\n", encoding="utf-8")
    json_path.write_text(
        json.dumps(
            {
                "canonical_metric_contract": [],
                "report_body_findings": [],
                "html_findings": [],
                "blocking_issues": [],
                "retry_recommendations": [],
                "passed": True,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="frontline_findings"):
        pipeline_service_module._validate_ecommerce_runtime_consistency_audit(
            md_path,
            json_path,
            "ecommerce_delivery_consistency_audit",
        )


def test_ensure_ecommerce_table_card_evidence_injects_reader_pack_numbers(tmp_path: Path) -> None:
    html_path = tmp_path / "06_report.html"
    reader_pack_path = tmp_path / "05b_ecommerce_reader_interpretation_pack.json"
    html_path.write_text(
        """
<html><body>
<div class="table-reading-card">
  <p><strong>怎么看：</strong>先看经营议题，再横向比较读数、对象池、责任人和检查点。</p>
  <p><strong>说明什么：</strong>规模底盘、类目、卖家、运费、路线和节奏共同说明本期要做对象治理。</p>
  <p><strong>下一步动作：</strong>分析负责人本周建立统一周会看板。</p>
</div>
<table><tr><th>KPI</th></tr><tr><td>GMV</td></tr></table>
</body></html>
""".strip(),
        encoding="utf-8",
    )
    reader_pack_path.write_text(
        json.dumps(
            {
                "table_reading_cards": [
                    {
                        "table_id": "T01",
                        "evidence": [
                            "规模底盘: 500 行、443 单、GMV 57,641.47、运费 6,907.65",
                            "头部类目: health_beauty 占 19.40% GMV",
                        ]
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    pipeline_service_module._ensure_ecommerce_table_card_evidence(html_path, reader_pack_path)
    repaired_html = html_path.read_text(encoding="utf-8")

    assert "证据：" in repaired_html
    assert "57,641.47" in repaired_html
    pipeline_service_module._validate_ecommerce_table_reading_cards(repaired_html)


def test_ecommerce_consistency_evidence_pack_marks_appendix_only_forbidden_uses(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "01b_ecommerce_metric_consumption_index.json").write_text(
        json.dumps(
            {
                "body_primary_metrics": [
                    {
                        "metric_id": "gmv_share_planned",
                        "metric_name": "GMV贡献度",
                        "value": "0.42",
                        "formula": "sum(GMV)/total",
                        "business_meaning": "判断主力对象贡献",
                    }
                ],
                "body_support_metrics": [],
                "appendix_metrics": [
                    {
                        "metric_id": "quality_proxy",
                        "metric_name": "质量代理指标",
                        "value": "4.1",
                        "formula": "mean(ReviewScore)",
                        "business_meaning": "仅作为质量观察信号",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (workspace / "05_report.md").write_text("# report\nGMV贡献度\n", encoding="utf-8")

    _, _, payload = pipeline_service_module._write_ecommerce_metric_consistency_evidence_pack(workspace)

    contract = {item["metric_id"]: item for item in payload["canonical_metric_contract"]}
    assert contract["quality_proxy"]["consumption_target"] == "appendix_only"
    assert "frontline_validation_metric" in contract["quality_proxy"]["forbidden_uses"]


def test_ecommerce_data_utilization_gate_parses_dimension_refs_and_case_ids(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    _frame().to_csv(workspace / "source_dataset.csv", index=False, encoding="utf-8-sig")
    pipeline_service_module._write_ecommerce_table_fact_pack(
        workspace,
        {"source_dataset_path": "source_dataset.csv"},
    )
    _seed_metric_mining_workspace(workspace)
    pipeline_service_module._write_ecommerce_metric_consumption_pack(workspace)
    (workspace / "05_report.md").write_text(
        "# 涓绘姤鍛奬n姝ｆ枃浣跨敤 top_object_amount_contribution 鍜?overall_trend_change銆俓n## 闄勫綍\nquality_proxy cpm_derived cpa_derived\n",
        encoding="utf-8",
    )

    for index in range(1, 5):
        (workspace / f"04_ecommerce_section_batch_{index:02d}.md").write_text(
            ("# Batch\n\n| KPI | value |\n| --- | --- |\n" + "缁忚惀寤鸿 鏄庣粏 KPI 琛屽姩\n" * 220),
            encoding="utf-8",
        )
        (workspace / f"04_ecommerce_section_batch_{index:02d}.json").write_text(
            json.dumps(
                {
                    "batch_index": index,
                    "section_ids": [f"s{index}"],
                    "section_titles": [f"section {index}"],
                    "completion_status": "completed",
                    "tables_used": ["category", "product", "shop_seller"],
                    "named_objects_used": ["health_beauty", "construction_tools_construction", "category_01", "product_01", "product_02", "shop-0"],
                    "dimension_tables_used": [
                        "01a_dimension_detail_summary.csv:category",
                        "01a_dimension_detail_summary.csv:product",
                        "01a_dimension_detail_summary.csv:shop_seller",
                        "01a_dimension_pair_summary.csv:category脳review_score_band",
                    ],
                    "route_tables_used": ["01a_route_cube.csv"],
                    "text_evidence_blocks_used": ["01a_review_text_theme_summary.json:top_themes"],
                    "current_period_metrics_used": ["gmv", "freight", "rating", "order_count", "inventory"],
                    "table_fact_ids_used": ["01a_exception_casebook.json"],
                    "derived_metrics_used": ["top_object_amount_contribution", "overall_trend_change", "cpm_derived", "cpa_derived", "quality_proxy"],
                    "derived_metric_tables_used": ["01b_ecommerce_metric_body_priority.csv", "01b_ecommerce_metric_appendix_priority.csv"],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    payload = pipeline_service_module._write_ecommerce_data_utilization_gate(workspace)

    assert payload["scores"]["exception_case_count"] >= 2
    assert payload["scores"]["dimension_coverage_ratio"] > 0
    assert payload["metric_coverage"]["all_metric_ids_classified"] is True


def test_ecommerce_data_utilization_gate_accepts_exception_casebook_reference_when_case_ids_not_explicit(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    _frame().to_csv(workspace / "source_dataset.csv", index=False, encoding="utf-8-sig")
    pipeline_service_module._write_ecommerce_table_fact_pack(
        workspace,
        {"source_dataset_path": "source_dataset.csv"},
    )
    _seed_metric_mining_workspace(workspace)
    pipeline_service_module._write_ecommerce_metric_consumption_pack(workspace)
    (workspace / "05_report.md").write_text(
        "# 主报告\n正文使用 top_object_amount_contribution 与 overall_trend_change。\n## 附录\nquality_proxy cpm_derived cpa_derived\n",
        encoding="utf-8",
    )

    for index in range(1, 5):
        (workspace / f"04_ecommerce_section_batch_{index:02d}.md").write_text(
            ("# Batch\n\n| KPI | value |\n| --- | --- |\n" + "经营建议 明细 KPI 行动\n" * 220),
            encoding="utf-8",
        )
        (workspace / f"04_ecommerce_section_batch_{index:02d}.json").write_text(
            json.dumps(
                {
                    "batch_index": index,
                    "section_ids": [f"s{index}"],
                    "section_titles": [f"section {index}"],
                    "completion_status": "completed",
                    "tables_used": ["category", "product", "shop_seller"],
                    "named_objects_used": ["category_main", "item-0", "item-1", "shop-0"],
                    "dimension_tables_used": [
                        "01a_dimension_detail_summary.csv::category",
                        "01a_dimension_detail_summary.csv::product",
                        "01a_dimension_detail_summary.csv::shop_seller",
                        "01a_dimension_detail_summary.csv::extra_DelayDays",
                    ],
                    "route_tables_used": ["01a_route_cube.csv::seller_state|customer_state"],
                    "text_evidence_blocks_used": [],
                    "current_period_metrics_used": ["gmv", "sales_volume", "order_count", "inventory", "gross_margin"],
                    "table_fact_ids_used": ["01a_ecommerce_table_fact_pack.json::exception_casebook_path"],
                    "derived_metrics_used": ["top_object_amount_contribution", "overall_trend_change", "quality_proxy", "cpm_derived", "cpa_derived"],
                    "derived_metric_tables_used": ["01b_ecommerce_metric_body_priority.csv", "01b_ecommerce_metric_appendix_priority.csv"],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    payload = pipeline_service_module._write_ecommerce_data_utilization_gate(workspace)
    assert payload["scores"]["exception_case_count"] >= payload["thresholds"]["exception_case_count"]


def test_ecommerce_data_utilization_gate_fails_when_any_metric_id_unconsumed(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    _frame().to_csv(workspace / "source_dataset.csv", index=False, encoding="utf-8-sig")
    pipeline_service_module._write_ecommerce_table_fact_pack(
        workspace,
        {"source_dataset_path": "source_dataset.csv"},
    )
    _seed_metric_mining_workspace(workspace)
    pipeline_service_module._write_ecommerce_metric_consumption_pack(workspace)
    (workspace / "05_report.md").write_text(
        "# 涓绘姤鍛奬n姝ｆ枃鍙敤浜?top_object_amount_contribution銆俓n## 闄勫綍\nquality_proxy\n",
        encoding="utf-8",
    )

    for index in range(1, 5):
        (workspace / f"04_ecommerce_section_batch_{index:02d}.md").write_text(
            ("# Batch\n\n| KPI | value |\n| --- | --- |\n" + "缁忚惀寤鸿 鏄庣粏 KPI 琛屽姩\n" * 220),
            encoding="utf-8",
        )
        (workspace / f"04_ecommerce_section_batch_{index:02d}.json").write_text(
            json.dumps(
                {
                    "batch_index": index,
                    "section_ids": [f"s{index}"],
                    "section_titles": [f"section {index}"],
                    "completion_status": "completed",
                    "tables_used": ["category", "product", "shop_seller"],
                    "named_objects_used": ["health_beauty", "item-0", "item-1", "shop-0"],
                    "dimension_tables_used": ["category", "product", "shop_seller", "brand"],
                    "route_tables_used": [],
                    "text_evidence_blocks_used": [],
                    "current_period_metrics_used": ["gmv", "sales_volume", "order_count", "inventory", "gross_margin"],
                    "table_fact_ids_used": ["category_01"],
                    "derived_metrics_used": ["top_object_amount_contribution"],
                    "derived_metric_tables_used": ["01b_ecommerce_metric_body_priority.csv"],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    with pytest.raises(ValueError, match="missing_metric_ids"):
        pipeline_service_module._write_ecommerce_data_utilization_gate(workspace)


def test_ecommerce_data_utilization_gate_fails_when_01c_metric_is_not_consumed(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    _frame().to_csv(workspace / "source_dataset.csv", index=False, encoding="utf-8-sig")
    pipeline_service_module._write_ecommerce_table_fact_pack(
        workspace,
        {"source_dataset_path": "source_dataset.csv"},
    )
    _seed_metric_mining_workspace(workspace)
    pd.DataFrame(
        [
            {
                "business_profile": "ecommerce_product_operations_report",
                "metric_id": "freight_to_gmv_planned",
                "metric_name": "运费成交额占比",
                "source_columns": "['freight', 'GMV']",
                "formula": "sum(freight) / sum(GMV)",
                "value": "0.08",
                "evidence_level": "B_DERIVED",
                "confidence": "medium",
                "metric_kind": "derived_metric",
                "business_meaning": "用于判断运费成本相对成交额的压力。",
                "note": "computed from 01c execution",
            }
        ]
    ).to_csv(workspace / "01c_derived_metrics_table.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame([]).to_csv(workspace / "01c_proxy_metrics_table.csv", index=False, encoding="utf-8-sig")
    (workspace / "01c_derived_metric_family_execution.json").write_text(
        json.dumps(
            {
                "derived_metric_family_count": 1,
                "derived_metric_family_executed_count": 1,
                "derived_metric_family_unsupported_count": 0,
            }
        ),
        encoding="utf-8",
    )
    pipeline_service_module._write_ecommerce_metric_consumption_pack(workspace)
    (workspace / "05_report.md").write_text(
        "# 主报告\n正文只用了 top_object_amount_contribution。\n## 附录\nquality_proxy cpm_derived cpa_derived\n",
        encoding="utf-8",
    )

    for index in range(1, 5):
        (workspace / f"04_ecommerce_section_batch_{index:02d}.md").write_text(
            ("# Batch\n\n| KPI | value |\n| --- | --- |\n" + "经营建议 明细 KPI 行动\n" * 220),
            encoding="utf-8",
        )
        (workspace / f"04_ecommerce_section_batch_{index:02d}.json").write_text(
            json.dumps(
                {
                    "batch_index": index,
                    "section_ids": [f"s{index}"],
                    "section_titles": [f"section {index}"],
                    "completion_status": "completed",
                    "tables_used": ["category", "product", "shop_seller"],
                    "named_objects_used": ["health_beauty", "item-0", "item-1", "shop-0"],
                    "dimension_tables_used": ["category", "product", "shop_seller", "brand"],
                    "route_tables_used": [],
                    "text_evidence_blocks_used": [],
                    "current_period_metrics_used": ["gmv", "sales_volume", "order_count", "inventory", "gross_margin"],
                    "table_fact_ids_used": ["category_01"],
                    "derived_metrics_used": ["top_object_amount_contribution", "quality_proxy"],
                    "derived_metric_tables_used": ["01b_ecommerce_metric_body_priority.csv", "01b_ecommerce_metric_appendix_priority.csv"],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    with pytest.raises(ValueError, match="freight_to_gmv_planned"):
        pipeline_service_module._write_ecommerce_data_utilization_gate(workspace)
