from __future__ import annotations

from _procurement_sales_fixture import procurement_sales_frame
from app.services.procurement_sales_metric_mining_service import build_procurement_sales_metric_mining_result
from app.services.report_service import (
    _append_procurement_metric_mining_sections,
    _final_procurement_sales_management_render,
    _procurement_sales_object_decision_registry,
)


def test_procurement_final_action_table_includes_fixture_statistics() -> None:
    frame = procurement_sales_frame()
    registry = _procurement_sales_object_decision_registry(frame)
    payload = _final_procurement_sales_management_render(
        {
            "title": "public fixture",
            "report_lens": "procurement_sales_review",
            "procurement_sales_readiness": {"report_mode": "sales_fulfillment_product_report"},
            "object_decision_registry": registry,
        }
    )
    section = next(section for section in payload["sections"] if section["id"] == "final_action_table")
    table = next(table for table in section["tables"] if table["title"] == "action_table")
    assert len(table["columns"]) >= 18
    rendered = " | ".join(str(value) for row in table["rows"] for value in row.values())
    expected_category_a_sales = f"{frame.loc[frame['category'] == 'category-a', 'sales_amount'].sum():,.0f}"
    assert expected_category_a_sales in rendered
    assert "Category A" in rendered
    assert "Category B" in rendered


def test_procurement_metric_sections_keep_structure_statistics() -> None:
    metric_payload = build_procurement_sales_metric_mining_result(
        raw_data=procurement_sales_frame(),
        field_names=[],
        sample_values=[],
        data_types={},
        universal_metric_mining_result={},
        business_profile_router_result={"business_profile": "procurement_sales_report"},
    )
    variant = _append_procurement_metric_mining_sections(
        {
            "sections": [
                {"id": "field_availability", "title": "field_availability", "summary": "", "bullets": [], "tables": []}
            ]
        },
        metric_payload,
    )
    section = next(section for section in variant["sections"] if section["id"] == "procurement_structure_analysis")
    table_titles = {table["title"] for table in section["tables"]}
    assert {"sku_sales_ranking", "category_contribution", "price_band_summary", "sales_trend"}.issubset(table_titles)
