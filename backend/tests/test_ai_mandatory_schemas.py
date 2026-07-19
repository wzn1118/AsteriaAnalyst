from __future__ import annotations

from app.services.ai_mandatory.schemas import (
    AIBusinessRoutingResult,
    AIFieldSemanticMapping,
    AIFieldSemanticMappingResult,
    AIMetricDerivationPlan,
    AIMetricPlanItem,
)


def test_ai_field_semantic_mapping_schema_roundtrip() -> None:
    mapping = AIFieldSemanticMapping(
        field_name="gmv",
        canonical_concept="sales_amount",
        business_role="amount_metric",
        granularity_hint="sku_day",
        confidence=0.92,
        evidence=["column name", "sample values"],
        alternative_mappings=["revenue"],
        risk_note="gmv may include cancelled orders if raw export not cleaned",
    )
    result = AIFieldSemanticMappingResult(
        inferred_business_context="平台电商商品经营",
        object_grain="sku",
        time_grain="day",
        field_mappings=[mapping],
        uncertain_fields=["profit"],
        provider="OpenAI",
        model="gpt-5.4",
        trace_id="trace-semantic-001",
    )
    dumped = result.model_dump(mode="json")
    restored = AIFieldSemanticMappingResult.model_validate(dumped)
    assert restored.trace_id == "trace-semantic-001"
    assert restored.field_mappings[0].canonical_concept == "sales_amount"


def test_ai_business_routing_schema() -> None:
    routing = AIBusinessRoutingResult(
        selected_by_user="auto",
        ai_route="ecommerce_product_operations_report",
        final_route="ecommerce_product_operations_report",
        confidence=0.88,
        alternative_routes=["procurement_sales_report"],
        reason="商品字段与交易字段同时存在",
        blocked_routes=["internet_operations_report"],
        trace_id="trace-route-001",
    )
    assert routing.final_route == "ecommerce_product_operations_report"
    assert routing.confidence == 0.88


def test_ai_metric_derivation_plan_schema() -> None:
    item = AIMetricPlanItem(
        metric_id="gross_margin",
        metric_name_cn="毛利率",
        metric_name_en="gross_margin",
        metric_family="profitability_metric",
        business_domain="procurement_sales",
        business_object="sku",
        metric_type="derived",
        required_field_roles=["amount_field", "cost_field"],
        matched_fields=["sales_amount", "cost"],
        missing_fields=[],
        formula="(sales_amount - cost) / sales_amount",
        grain="sku_day",
        time_window_requirement="same_period",
        minimum_data_requirement="at least one row with sales_amount and cost",
        evidence_level="B_DERIVED",
        confidence=0.92,
        calculation_feasibility="calculable",
        business_question_answered="哪些 SKU 具有健康的盈利能力",
        caveat="requires deterministic executor",
        downstream_usage=["management_report"],
        forbidden_usage=["renderer_side_field_understanding"],
        reason="revenue and cost fields both exist",
    )
    plan = AIMetricDerivationPlan(
        available_metrics=["gross_margin"],
        unavailable_metrics=["roi"],
        proxy_metrics=["review_per_order_proxy"],
        diagnostic_questions=["缺库存时需补库存字段后再看周转"],
        metric_plans=[item],
        provider="OpenAI",
        model="gpt-5.4",
        trace_id="trace-plan-001",
    )
    dumped = plan.model_dump(mode="json")
    restored = AIMetricDerivationPlan.model_validate(dumped)
    assert restored.metric_plans[0].metric_type == "derived"
    assert restored.trace_id == "trace-plan-001"
