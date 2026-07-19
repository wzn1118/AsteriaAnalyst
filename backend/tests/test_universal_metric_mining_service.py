from __future__ import annotations

import json

import pandas as pd

from app.models import SmartReportRequest
from app.services.independent_industry_research_chain import _scope_payload
from app.services.universal_metric_mining_service import (
    build_universal_metric_mining_result,
    metric_mining_quality_failures,
    write_universal_metric_mining_outputs,
)


def test_universal_metric_mining_derives_ecommerce_metrics() -> None:
    frame = pd.DataFrame(
        {
            "item_id": ["a", "b", "a"],
            "sales_amount": [100.0, 80.0, 40.0],
            "order_count": [5, 4, 2],
            "impression": [1000, 800, 500],
            "click": [100, 64, 40],
            "add_to_cart": [20, 16, 10],
            "pay": [10, 8, 5],
            "review_count": [4, 3, 2],
        }
    )

    payload = build_universal_metric_mining_result(
        frame=frame,
        business_profile="ecommerce_product_operations_report",
    )

    derived_ids = {row["metric_id"] for row in payload["derived_metrics"]}
    proxy_ids = {row["metric_id"] for row in payload["proxy_metrics"]}

    assert "average_order_value" in derived_ids
    assert "ctr_derived" in derived_ids
    assert "pay_conversion_rate" in derived_ids
    assert "review_per_order_proxy" in proxy_ids
    assert payload["domain_metric_registry"]["recommended_report_chain"] == "ecommerce_product_operations_report"


def test_universal_metric_mining_derives_internet_metrics() -> None:
    frame = pd.DataFrame(
        {
            "user_id": ["u1", "u2", "u1", "u3"],
            "date": ["2026-01-01", "2026-01-01", "2026-01-02", "2026-01-02"],
            "register": [10, 0, 8, 0],
            "activation": [5, 0, 4, 0],
            "revenue": [100.0, 20.0, 120.0, 10.0],
            "dau": [50, 50, 60, 60],
        }
    )

    payload = build_universal_metric_mining_result(
        frame=frame,
        business_profile="internet_operations_report",
    )

    derived_ids = {row["metric_id"] for row in payload["derived_metrics"]}
    assert "activation_rate" in derived_ids
    assert "revenue_per_active_user" in derived_ids
    assert "active_user_change" in derived_ids


def test_universal_metric_mining_writes_required_outputs(tmp_path) -> None:
    frame = pd.DataFrame(
        {
            "project_id": ["p1", "p2"],
            "budget": [100, 200],
            "actual_spend": [50, 100],
            "progress": [0.4, 0.8],
            "target": [1.0, 1.0],
        }
    )
    payload = build_universal_metric_mining_result(
        frame=frame,
        business_profile="generic_long_business_report",
    )

    files = write_universal_metric_mining_outputs(tmp_path, payload)

    expected = {
        "universal_metric_mining_result.json",
        "universal_metric_mining_report.md",
        "derived_metrics_table.csv",
        "proxy_metrics_table.csv",
        "unsupported_metrics_table.csv",
        "inference_confidence_registry.csv",
        "domain_metric_registry.json",
    }
    assert expected == set(files.keys())
    for path in files.values():
        assert pd.notna(path)
        assert json.loads((tmp_path / "universal_metric_mining_result.json").read_text(encoding="utf-8"))["business_profile"] == "generic_long_business_report"
        break
    for name in expected:
        assert (tmp_path / name).exists()


def test_metric_mining_quality_failures_when_report_ignores_calculable_metrics() -> None:
    frame = pd.DataFrame(
        {
            "sales_amount": [100, 200],
            "order_count": [10, 20],
        }
    )
    payload = build_universal_metric_mining_result(
        frame=frame,
        business_profile="procurement_sales_report",
    )

    failures = metric_mining_quality_failures(
        management_markdown="当前报告仍然写待补数据，无法判断。",
        metric_payload=payload,
        business_profile="procurement_sales_report",
    )
    assert failures

    ok_failures = metric_mining_quality_failures(
        management_markdown="当前可直接使用客单价与销售额判断交易结构。",
        metric_payload=payload,
        business_profile="procurement_sales_report",
    )
    assert not ok_failures


def test_industry_scope_reads_metric_mining_context() -> None:
    frame = pd.DataFrame(
        {
            "item_id": ["i1", "i2"],
            "shop_id": ["s1", "s1"],
            "gmv": [100, 120],
            "review_count": [4, 5],
        }
    )
    metric_payload = build_universal_metric_mining_result(
        frame=frame,
        business_profile="independent_industry_research_chain",
    )

    scope = _scope_payload(
        dataset_name="taobao_items.xlsx",
        uploaded_file_name="taobao_items.xlsx",
        sheet_names=["Sheet1"],
        field_names=frame.columns.astype(str).tolist(),
        sample_values=["taobao", "item_id", "gmv"],
        request=SmartReportRequest(),
        router_result={"business_profile": "ecommerce_product_operations_report"},
        deep_context_understanding={"universal_metric_mining_result": metric_payload},
    )

    assert "metric_mining_context" in scope
    assert scope["metric_mining_context"]["recommended_report_chain"] == "independent_industry_research_chain"
    assert scope["metric_mining_context"]["direct_metrics"]
