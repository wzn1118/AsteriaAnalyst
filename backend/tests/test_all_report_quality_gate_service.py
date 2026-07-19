from __future__ import annotations

from app.services.all_report_quality_gate_service import universal_field_blindness_guardrail


def test_universal_field_blindness_guardrail_requires_metric_payload_when_configured() -> None:
    result = universal_field_blindness_guardrail(
        business_profile="generic_long_business_report",
        management_markdown="当前可判断销售结构。",
        metric_payload=None,
        action_rows=[],
        require_metric_payload=True,
    )
    assert not result["passed"]
    assert "universal_metric_mining_result.json missing" in result["fail_items"]
    assert "domain_metric_registry.json missing" in result["fail_items"]


def test_universal_field_blindness_guardrail_blocks_procurement_blindness() -> None:
    metric_payload = {
        "field_presence": {
            "has_object_fields": True,
            "has_time_field": True,
            "has_numeric_field": True,
            "has_amount_field": True,
            "has_quantity_field": True,
            "has_sku_field": True,
            "has_category_field": True,
            "has_supplier_field": True,
            "has_cost_field": False,
            "has_inventory_field": False,
        },
        "domain_metric_registry": {"direct_metrics": ["sales_amount"], "derived_metrics": [], "proxy_metrics": [], "hypothesis_metrics": [], "unsupported_metrics": []},
        "direct_metrics": [{"metric_id": "sales_amount", "metric_name": "销售额"}],
        "derived_metrics": [],
        "proxy_metrics": [],
        "hypothesis_metrics": [],
        "unsupported_metrics": [],
    }
    result = universal_field_blindness_guardrail(
        business_profile="procurement_sales_report",
        management_markdown="当前毛利很高，存在缺货风险，待补数据。",
        metric_payload=metric_payload,
        action_rows=[
            {"priority": "P1", "action": "补库存"},
            {"priority": "P1", "action": "补成本"},
        ],
        extra_context={"procurement_metric_payload": {"quality_checks": {}}},
        require_metric_payload=True,
    )
    assert not result["passed"]
    assert any("SKU + 销售额" in item for item in result["fail_items"])
    assert any("毛利" in item or "profit" in item for item in result["fail_items"])
    assert any("stock risk" in item or "库存" in item for item in result["fail_items"])
    assert any("50%+ actions" in item for item in result["fail_items"])
    assert any("all action priorities are P1" in item for item in result["fail_items"])


def test_universal_field_blindness_guardrail_blocks_internet_blindness() -> None:
    metric_payload = {
        "field_presence": {
            "has_object_fields": True,
            "has_time_field": True,
            "has_numeric_field": True,
            "has_user_field": True,
            "has_event_field": True,
            "has_content_field": True,
            "has_channel_field": True,
            "has_amount_field": False,
            "has_quantity_field": False,
            "has_cost_field": False,
        },
        "domain_metric_registry": {"direct_metrics": [], "derived_metrics": [], "proxy_metrics": [], "hypothesis_metrics": [], "unsupported_metrics": []},
        "direct_metrics": [],
        "derived_metrics": [],
        "proxy_metrics": [],
        "hypothesis_metrics": [],
        "unsupported_metrics": [],
    }
    result = universal_field_blindness_guardrail(
        business_profile="internet_operations_report",
        management_markdown="当前增长很好，但仍待补数据。",
        metric_payload=metric_payload,
        action_rows=[{"priority": "P2", "action": "复核留存"}],
        require_metric_payload=True,
    )
    assert not result["passed"]
    assert any("DAU/WAU/MAU" in item for item in result["fail_items"])
    assert any("cohort retention" in item for item in result["fail_items"])
    assert any("funnel" in item for item in result["fail_items"])
    assert any("content performance" in item for item in result["fail_items"])
    assert any("channel contribution" in item for item in result["fail_items"])


def test_universal_field_blindness_guardrail_blocks_media_efficiency_blindness() -> None:
    metric_payload = {
        "field_presence": {
            "has_object_fields": True,
            "has_time_field": False,
            "has_numeric_field": True,
            "has_campaign_field": True,
            "has_spend_field": True,
            "has_conversion_field": True,
            "has_amount_field": True,
            "has_quantity_field": False,
        },
        "domain_metric_registry": {"direct_metrics": [], "derived_metrics": [], "proxy_metrics": [], "hypothesis_metrics": [], "unsupported_metrics": []},
        "direct_metrics": [],
        "derived_metrics": [],
        "proxy_metrics": [],
        "hypothesis_metrics": [],
        "unsupported_metrics": [],
    }
    result = universal_field_blindness_guardrail(
        business_profile="media_campaign_report",
        management_markdown="本轮投放待补数据。",
        metric_payload=metric_payload,
        action_rows=[{"priority": "P2", "action": "复核投放"}],
        require_metric_payload=True,
    )
    assert not result["passed"]
    assert any("media efficiency" in item for item in result["fail_items"])
