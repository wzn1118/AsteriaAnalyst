from __future__ import annotations

from app.services.dataset_service import load_dataset_frame
from app.services.report_service import (
    _append_procurement_metric_mining_sections,
    _final_procurement_sales_management_render,
    _procurement_sales_object_decision_registry,
)
from app.services.procurement_sales_metric_mining_service import build_procurement_sales_metric_mining_result


def _resolve_frame(dataset_id: str):
    loaded = load_dataset_frame(dataset_id)
    if isinstance(loaded, tuple):
        for item in loaded:
            if hasattr(item, "columns"):
                return item
    return loaded


def test_procurement_final_action_table_includes_key_statistics() -> None:
    frame = _resolve_frame("6490e1d9994d")
    registry = _procurement_sales_object_decision_registry(frame)
    payload = _final_procurement_sales_management_render(
        {
            "title": "test",
            "report_lens": "procurement_sales_review",
            "procurement_sales_readiness": {"report_mode": "sales_fulfillment_product_report"},
            "object_decision_registry": registry,
        }
    )
    section = next(section for section in payload["sections"] if section["id"] == "final_action_table")
    table = next(table for table in section["tables"] if table["title"] == "action_table")
    assert len(table["columns"]) >= 18
    first_row = table["rows"][0]
    rendered_values = [str(value or "") for value in first_row.values()]
    assert any("76,570.99" in value or "76,570" in value for value in rendered_values)
    assert any("5.3" in value or "5.28" in value for value in rendered_values)
    assert any("577" in value for value in rendered_values)
    assert any("575" in value for value in rendered_values)


def test_procurement_metric_sections_keep_structure_statistics() -> None:
    frame = _resolve_frame("6490e1d9994d")
    metric_payload = build_procurement_sales_metric_mining_result(
        raw_data=frame,
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
