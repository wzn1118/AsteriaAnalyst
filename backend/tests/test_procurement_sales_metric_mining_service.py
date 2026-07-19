from __future__ import annotations

import pandas as pd

from app.services.procurement_sales_metric_mining_service import (
    build_procurement_sales_metric_mining_result,
    procurement_sales_metric_mining_failures,
    write_procurement_sales_metric_mining_outputs,
)


def _sample_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "sku_id": ["sku1", "sku2", "sku3", "sku1", "sku2", "sku3"],
            "category": ["A", "A", "B", "A", "A", "B"],
            "supplier": ["s1", "s1", "s2", "s1", "s1", "s2"],
            "date": [
                "2026-01-01",
                "2026-01-01",
                "2026-01-01",
                "2026-02-01",
                "2026-02-01",
                "2026-02-01",
            ],
            "sales_amount": [1000, 300, 120, 1100, 280, 100],
            "units_sold": [100, 40, 20, 105, 35, 18],
            "order_count": [20, 8, 4, 21, 7, 3],
            "purchase_qty": [90, 60, 40, 100, 50, 30],
            "purchase_amount": [600, 220, 90, 650, 200, 80],
            "cost": [700, 250, 90, 720, 230, 85],
            "inventory": [15, 120, 180, 12, 130, 170],
            "sale_price": [10, 8, 6, 10.5, 8.0, 5.8],
            "original_price": [12, 10, 8, 12, 10, 8],
        }
    )


def test_procurement_metric_mining_builds_rankings_and_profit_metrics() -> None:
    payload = build_procurement_sales_metric_mining_result(
        raw_data=_sample_frame(),
        field_names=[],
        sample_values=[],
        data_types={},
        universal_metric_mining_result={},
        business_profile_router_result={"business_profile": "procurement_sales_report"},
    )

    checks = payload["quality_checks"]
    derived_ids = {row["metric_id"] for row in payload["derived_metrics"]}

    assert checks["has_sku_sales_ranking"]
    assert checks["has_category_contribution"]
    assert checks["has_supplier_contribution"]
    assert checks["has_gross_profit_and_margin"]
    assert checks["has_inventory_turnover_proxy"]
    assert "gross_profit" in derived_ids
    assert "gross_margin" in derived_ids
    assert payload["summary_tables"]["sku_ranking"]
    assert payload["opportunity_risk_rows"]
    assert payload["action_table_rows"]


def test_procurement_metric_mining_respects_missing_cost_and_inventory_boundaries() -> None:
    frame = _sample_frame().drop(columns=["cost", "inventory"])
    payload = build_procurement_sales_metric_mining_result(
        raw_data=frame,
        field_names=[],
        sample_values=[],
        data_types={},
        universal_metric_mining_result={},
        business_profile_router_result={"business_profile": "procurement_sales_report"},
    )

    derived_ids = {row["metric_id"] for row in payload["derived_metrics"]}
    assert "gross_profit" not in derived_ids
    assert "gross_margin" not in derived_ids
    assert "inventory_turnover_proxy" not in derived_ids
    assert "毛利、利润、毛利率" in payload["narrative"]["cannot_judge"]
    assert "库存周转、滞销库存、缺货风险" in payload["narrative"]["cannot_judge"]


def test_procurement_metric_mining_failures_catch_profit_and_inventory_misuse() -> None:
    frame = _sample_frame().drop(columns=["cost", "inventory"])
    payload = build_procurement_sales_metric_mining_result(
        raw_data=frame,
        field_names=[],
        sample_values=[],
        data_types={},
        universal_metric_mining_result={},
        business_profile_router_result={"business_profile": "procurement_sales_report"},
    )

    failures = procurement_sales_metric_mining_failures(
        metric_payload=payload,
        management_markdown="当前毛利率很高，建议加码，同时缺货风险正在上升。",
    )

    assert any("profit judgement" in item for item in failures)
    assert any("inventory judgement" in item for item in failures)


def test_procurement_metric_mining_writes_required_outputs(tmp_path) -> None:
    payload = build_procurement_sales_metric_mining_result(
        raw_data=_sample_frame(),
        field_names=[],
        sample_values=[],
        data_types={},
        universal_metric_mining_result={},
        business_profile_router_result={"business_profile": "procurement_sales_report"},
    )
    files = write_procurement_sales_metric_mining_outputs(tmp_path, payload)

    assert {
        "procurement_sales_metric_mining_result.json",
        "procurement_sales_derived_metrics.csv",
        "procurement_sales_object_registry.csv",
        "procurement_sales_opportunity_risk_table.csv",
        "procurement_sales_action_table.csv",
    } == set(files.keys())
    for name in files:
        assert (tmp_path / name).exists()
