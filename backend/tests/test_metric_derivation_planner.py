from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services.ai_mandatory.field_semantic_mapper import AIClientAdapter, AIRequiredButUnavailableError
from app.services.ai_mandatory.metric_derivation_planner import (
    AIMetricDerivationPlannerValidationError,
    plan_metrics_with_ai,
)
from app.services.ai_mandatory.schemas import (
    AIBusinessRoutingResult,
    AIFieldSemanticMapping,
    AIFieldSemanticMappingResult,
)


class FakeAIClient(AIClientAdapter):
    def __init__(self, payload: dict):
        self.payload = payload
        self.called = False

    def complete_json(self, *, system_prompt: str, user_payload: dict) -> dict:
        self.called = True
        self.system_prompt = system_prompt
        self.user_payload = user_payload
        return dict(self.payload)


def _mapping(field_name: str, canonical: str, role: str, grain: str = "") -> AIFieldSemanticMapping:
    return AIFieldSemanticMapping(
        field_name=field_name,
        canonical_concept=canonical,
        business_role=role,
        granularity_hint=grain or canonical,
        confidence=0.95,
        evidence=["ai semantic mapping"],
        alternative_mappings=[],
        risk_note="",
    )


def _semantic_result(
    *,
    mappings: list[AIFieldSemanticMapping],
    object_grain: str,
    time_grain: str,
    context: str = "generic business context",
) -> AIFieldSemanticMappingResult:
    return AIFieldSemanticMappingResult(
        inferred_business_context=context,
        object_grain=object_grain,
        time_grain=time_grain,
        field_mappings=mappings,
        uncertain_fields=[],
        provider="OpenAI",
        model="gpt-5.4",
        trace_id="trace-semantic-plan-001",
    )


def _routing_result(route: str, confidence: float = 0.9) -> AIBusinessRoutingResult:
    return AIBusinessRoutingResult(
        selected_by_user=None,
        ai_route=route,
        final_route=route,
        confidence=confidence,
        alternative_routes=[],
        reason="ai route selected",
        blocked_routes=[],
        trace_id="trace-route-plan-001",
    )


def _plan_payload(metric_plans: list[dict], *, provider: str = "OpenAI", model: str = "gpt-5.4") -> dict:
    return {
        "available_metrics": [item["metric_id"] for item in metric_plans if item["metric_type"] in {"direct", "derived"}],
        "unavailable_metrics": [item["metric_id"] for item in metric_plans if item["metric_type"] == "unavailable"],
        "proxy_metrics": [item["metric_id"] for item in metric_plans if item["metric_type"] == "proxy"],
        "diagnostic_questions": [item["business_question_answered"] for item in metric_plans if item["metric_type"] == "diagnostic"],
        "metric_plans": metric_plans,
        "provider": provider,
        "model": model,
        "trace_id": "trace-plan-001",
    }


def _plan_item(
    *,
    metric_id: str,
    metric_family: str,
    metric_type: str,
    required_field_roles: list[str],
    matched_fields: list[str],
    missing_fields: list[str],
    grain: str,
    evidence_level: str,
    confidence: float,
    calculation_feasibility: str,
    business_question_answered: str,
    formula_or_logic: str = "",
    caveat: str = "",
    allowed_downstream_usage: list[str] | None = None,
    forbidden_downstream_usage: list[str] | None = None,
    metric_name_cn: str | None = None,
    metric_name_en: str | None = None,
) -> dict:
    return {
        "metric_id": metric_id,
        "metric_name_cn": metric_name_cn or metric_id,
        "metric_name_en": metric_name_en or metric_id,
        "metric_family": metric_family,
        "business_domain": "test_domain",
        "business_object": "test_object",
        "metric_type": metric_type,
        "required_field_roles": required_field_roles,
        "matched_fields": matched_fields,
        "missing_fields": missing_fields,
        "formula_or_logic": formula_or_logic,
        "grain": grain,
        "time_window_requirement": "",
        "minimum_data_requirement": "rows >= 1",
        "evidence_level": evidence_level,
        "confidence": confidence,
        "calculation_feasibility": calculation_feasibility,
        "business_question_answered": business_question_answered,
        "allowed_downstream_usage": allowed_downstream_usage or ["management_report"],
        "forbidden_downstream_usage": forbidden_downstream_usage or ["renderer_side_field_understanding"],
        "caveat": caveat,
        "reason": "ai planned metric from semantic roles",
    }


def _run_plan(
    tmp_path: Path,
    *,
    semantic_result: AIFieldSemanticMappingResult,
    routing_result: AIBusinessRoutingResult,
    dataframe_profile: dict,
    payload: dict,
    available_field_roles: list[str] | dict | None = None,
    user_task_description: str = "generate metric plan",
    business_route: str | None = None,
) -> tuple[FakeAIClient, Any]:
    client = FakeAIClient(payload)
    plan = plan_metrics_with_ai(
        output_dir=tmp_path,
        semantic_mapping_result=semantic_result,
        routing_result=routing_result,
        dataframe_profile=dataframe_profile,
        user_task_description=user_task_description,
        available_field_roles=available_field_roles or [],
        object_grain=semantic_result.object_grain,
        time_grain=semantic_result.time_grain,
        business_route=business_route or routing_result.final_route,
        existing_metric_registry=None,
        user_selected_analysis_depth="deep_dive",
        ai_client=client,
    )
    return client, plan


def test_metric_planner_calls_ai(tmp_path: Path) -> None:
    semantic = _semantic_result(
        mappings=[
            _mapping("user_id", "user_id", "user_key"),
            _mapping("event_date", "date", "time_key"),
        ],
        object_grain="user",
        time_grain="day",
        context="internet ops",
    )
    routing = _routing_result("internet_operations_report")
    payload = _plan_payload(
        [
            _plan_item(
                metric_id="active_users_by_day",
                metric_family="retention_metric",
                metric_type="derived",
                required_field_roles=["user_key", "time_key"],
                matched_fields=["user_id", "event_date"],
                missing_fields=[],
                grain="day",
                evidence_level="B_DERIVED",
                confidence=0.88,
                calculation_feasibility="calculable",
                business_question_answered="当前活跃用户规模如何变化",
                formula_or_logic="nunique(user_id) by day(event_date)",
                caveat="not equivalent to long-term retention",
            )
        ]
    )
    client, plan = _run_plan(
        tmp_path,
        semantic_result=semantic,
        routing_result=routing,
        dataframe_profile={"time_profile": {"distinct_time_points": 10, "window_days": 10}},
        payload=payload,
    )

    assert client.called is True
    assert plan.trace_id == "trace-plan-001"
    assert (tmp_path / "outputs" / "ai_traces" / "ai_metric_derivation_plan.json").exists()
    assert (tmp_path / "outputs" / "metric_mining" / "semantic_metric_plan.json").exists()


def test_metric_planner_rejects_nonexistent_fields(tmp_path: Path) -> None:
    semantic = _semantic_result(
        mappings=[_mapping("gmv_amount", "revenue", "amount_field")],
        object_grain="sku",
        time_grain="day",
    )
    routing = _routing_result("ecommerce_product_operations_report")
    payload = _plan_payload(
        [
            _plan_item(
                metric_id="sales_scale",
                metric_family="scale_metric",
                metric_type="derived",
                required_field_roles=["amount_field"],
                matched_fields=["nonexistent_field"],
                missing_fields=[],
                grain="sku_day",
                evidence_level="B_DERIVED",
                confidence=0.8,
                calculation_feasibility="calculable",
                business_question_answered="销售规模是多少",
                formula_or_logic="sum(nonexistent_field)",
                caveat="",
            )
        ]
    )
    with pytest.raises(AIMetricDerivationPlannerValidationError):
        _run_plan(
            tmp_path,
            semantic_result=semantic,
            routing_result=routing,
            dataframe_profile={},
            payload=payload,
        )


def test_metric_planner_requires_formula_for_calculable_metrics(tmp_path: Path) -> None:
    semantic = _semantic_result(
        mappings=[_mapping("gmv_amount", "revenue", "amount_field")],
        object_grain="sku",
        time_grain="day",
    )
    routing = _routing_result("ecommerce_product_operations_report")
    payload = _plan_payload(
        [
            _plan_item(
                metric_id="sales_scale",
                metric_family="scale_metric",
                metric_type="derived",
                required_field_roles=["amount_field"],
                matched_fields=["gmv_amount"],
                missing_fields=[],
                grain="sku_day",
                evidence_level="B_DERIVED",
                confidence=0.8,
                calculation_feasibility="calculable",
                business_question_answered="销售规模是多少",
                formula_or_logic="",
                caveat="",
            )
        ]
    )
    with pytest.raises(AIMetricDerivationPlannerValidationError, match="requires executable formula_or_logic"):
        _run_plan(tmp_path, semantic_result=semantic, routing_result=routing, dataframe_profile={}, payload=payload)


def test_metric_planner_repairs_formula_fields_into_matched_fields(tmp_path: Path) -> None:
    semantic = _semantic_result(
        mappings=[
            _mapping("gmv_amount", "revenue", "amount_field"),
            _mapping("cost_amount", "cost", "cost_field"),
        ],
        object_grain="sku",
        time_grain="day",
    )
    routing = _routing_result("ecommerce_product_operations_report")
    payload = _plan_payload(
        [
            _plan_item(
                metric_id="gross_profit",
                metric_family="profitability_metric",
                metric_type="derived",
                required_field_roles=["amount_field", "cost_field"],
                matched_fields=["gmv_amount"],
                missing_fields=[],
                grain="sku_day",
                evidence_level="B_DERIVED",
                confidence=0.8,
                calculation_feasibility="calculable",
                business_question_answered="毛利是多少",
                formula_or_logic="SUM(gmv_amount) - SUM(cost_amount)",
                caveat="",
            )
        ]
    )
    _, plan = _run_plan(tmp_path, semantic_result=semantic, routing_result=routing, dataframe_profile={}, payload=payload)
    gross_profit = next(item for item in plan.metric_plans if item.metric_id == "gross_profit")
    assert gross_profit.matched_fields == ["gmv_amount", "cost_amount"]


def test_metric_planner_repairs_proxy_feasibility_and_evidence(tmp_path: Path) -> None:
    semantic = _semantic_result(
        mappings=[
            _mapping("gmv_amount", "gmv", "amount_field"),
            _mapping("freight_cost", "cost", "cost_field"),
        ],
        object_grain="product",
        time_grain="day",
    )
    routing = _routing_result("procurement_sales_report")
    payload = _plan_payload(
        [
            _plan_item(
                metric_id="freight_cost_rate_to_gmv",
                metric_family="efficiency_metric",
                metric_type="proxy",
                required_field_roles=["amount_field", "cost_field"],
                matched_fields=["gmv_amount", "freight_cost"],
                missing_fields=[],
                grain="product_day",
                evidence_level="A_DIRECT",
                confidence=0.76,
                calculation_feasibility="calculable",
                business_question_answered="运费负担是否偏高",
                formula_or_logic="SUM(freight_cost) / SUM(gmv_amount)",
                caveat="proxy only for logistics burden, not full profitability.",
            )
        ]
    )
    _, plan = _run_plan(tmp_path, semantic_result=semantic, routing_result=routing, dataframe_profile={}, payload=payload)
    metric = next(item for item in plan.metric_plans if item.metric_id == "freight_cost_rate_to_gmv")
    assert metric.evidence_level == "C_PROXY"
    assert metric.calculation_feasibility == "proxy_only"


def test_metric_planner_allows_existing_uncertain_dataframe_fields(tmp_path: Path) -> None:
    semantic = _semantic_result(
        mappings=[
            _mapping("SKU", "sku_id", "sku_key"),
            _mapping("GMV", "gmv", "amount_field"),
        ],
        object_grain="sku",
        time_grain="day",
    )
    semantic.uncertain_fields = ["IsLate"]
    routing = _routing_result("procurement_sales_report")
    payload = _plan_payload(
        [
            _plan_item(
                metric_id="late_order_risk_by_sku",
                metric_family="risk_metric",
                metric_type="derived",
                required_field_roles=["sku_key", "status_field"],
                matched_fields=["SKU", "IsLate"],
                missing_fields=[],
                grain="sku",
                evidence_level="B_DERIVED",
                confidence=0.82,
                calculation_feasibility="calculable",
                business_question_answered="Which SKUs carry fulfillment lateness risk?",
                formula_or_logic="GROUP BY SKU; MEAN(IsLate)",
                caveat="IsLate must be interpreted as an observed late-delivery flag, not root cause.",
            )
        ]
    )
    _, plan = _run_plan(
        tmp_path,
        semantic_result=semantic,
        routing_result=routing,
        dataframe_profile={"column_summaries": [{"name": "SKU"}, {"name": "GMV"}, {"name": "IsLate"}]},
        payload=payload,
    )
    assert plan.metric_plans[0].matched_fields == ["SKU", "IsLate"]


def test_metric_planner_repairs_compound_required_role_text(tmp_path: Path) -> None:
    semantic = _semantic_result(
        mappings=[
            _mapping("Revenue", "revenue", "amount_field"),
            _mapping("FreightCost", "cost", "cost_field"),
        ],
        object_grain="order_item",
        time_grain="day",
    )
    routing = _routing_result("procurement_sales_report")
    payload = _plan_payload(
        [
            _plan_item(
                metric_id="freight_cost_ratio",
                metric_family="profitability_metric",
                metric_type="derived",
                required_field_roles=["amount_field", "purchase_price_field or full cost_field"],
                matched_fields=["Revenue", "FreightCost"],
                missing_fields=[],
                grain="overall",
                evidence_level="B_DERIVED",
                confidence=0.78,
                calculation_feasibility="calculable",
                business_question_answered="How much freight cost weighs on merchandise revenue?",
                formula_or_logic="SUM(FreightCost) / SUM(Revenue)",
                caveat="FreightCost is a logistics cost proxy, not full procurement cost.",
            )
        ]
    )
    _, plan = _run_plan(
        tmp_path,
        semantic_result=semantic,
        routing_result=routing,
        dataframe_profile={"column_summaries": [{"name": "Revenue"}, {"name": "FreightCost"}]},
        payload=payload,
    )
    assert "cost_field" in plan.metric_plans[0].required_field_roles


def test_metric_planner_blocks_proxy_as_direct(tmp_path: Path) -> None:
    semantic = _semantic_result(
        mappings=[_mapping("review_score", "review_score", "review_score_field")],
        object_grain="sku",
        time_grain="day",
    )
    routing = _routing_result("ecommerce_product_operations_report")
    payload = _plan_payload(
        [
            _plan_item(
                metric_id="review_quality",
                metric_family="quality_metric",
                metric_type="direct",
                required_field_roles=["review_score_field"],
                matched_fields=["review_score"],
                missing_fields=[],
                grain="sku_day",
                evidence_level="C_PROXY",
                confidence=0.6,
                calculation_feasibility="calculable",
                business_question_answered="评价质量是否稳定",
                formula_or_logic="mean(review_score)",
            )
        ]
    )
    with pytest.raises(AIMetricDerivationPlannerValidationError):
        _run_plan(
            tmp_path,
            semantic_result=semantic,
            routing_result=routing,
            dataframe_profile={},
            payload=payload,
        )


def test_metric_planner_does_not_require_fixed_metric_names(tmp_path: Path) -> None:
    semantic = _semantic_result(
        mappings=[
            _mapping("visitor_code", "user_id", "user_key"),
            _mapping("event_day", "date", "time_key"),
        ],
        object_grain="user",
        time_grain="day",
        context="user operations",
    )
    routing = _routing_result("internet_operations_report")
    payload = _plan_payload(
        [
            _plan_item(
                metric_id="daily_engaged_visitors",
                metric_family="retention_metric",
                metric_type="derived",
                required_field_roles=["user_key", "time_key"],
                matched_fields=["visitor_code", "event_day"],
                missing_fields=[],
                grain="day",
                evidence_level="B_DERIVED",
                confidence=0.84,
                calculation_feasibility="calculable",
                business_question_answered="活跃用户规模是否变化",
                formula_or_logic="nunique(visitor_code) by day(event_day)",
                caveat="not equivalent to D7/D30 retention",
            )
        ]
    )
    _, plan = _run_plan(
        tmp_path,
        semantic_result=semantic,
        routing_result=routing,
        dataframe_profile={"time_profile": {"distinct_time_points": 14, "window_days": 14}},
        payload=payload,
    )
    assert plan.metric_plans[0].metric_id == "daily_engaged_visitors"
    semantic_plan = json.loads((tmp_path / "outputs" / "metric_mining" / "semantic_metric_plan.json").read_text(encoding="utf-8"))
    assert "retention_metric" in semantic_plan["available_metric_families"]


def test_metric_planner_generates_metric_opportunity_graph(tmp_path: Path) -> None:
    semantic = _semantic_result(
        mappings=[_mapping("order_id", "order_id", "order_key"), _mapping("amount", "revenue", "amount_field")],
        object_grain="order",
        time_grain="day",
    )
    routing = _routing_result("generic_long_business_report")
    payload = _plan_payload(
        [
            _plan_item(
                metric_id="order_value_mix",
                metric_family="structure_metric",
                metric_type="derived",
                required_field_roles=["order_key", "amount_field"],
                matched_fields=["order_id", "amount"],
                missing_fields=[],
                grain="order_day",
                evidence_level="B_DERIVED",
                confidence=0.8,
                calculation_feasibility="calculable",
                business_question_answered="订单金额结构如何分布",
                formula_or_logic="share(order amount by order)",
                caveat="structure only",
            )
        ]
    )
    _run_plan(tmp_path, semantic_result=semantic, routing_result=routing, dataframe_profile={}, payload=payload)
    graph_path = tmp_path / "outputs" / "metric_mining" / "metric_opportunity_graph.json"
    assert graph_path.exists()
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    assert graph["nodes"]


def test_metric_planner_not_limited_to_examples(tmp_path: Path) -> None:
    semantic = _semantic_result(
        mappings=[
            _mapping("region_name", "region", "region_key"),
            _mapping("customer_segment", "customer_type", "customer_type_key"),
            _mapping("net_revenue", "revenue", "amount_field"),
        ],
        object_grain="region",
        time_grain="unknown",
        context="regional business mix",
    )
    routing = _routing_result("generic_long_business_report")
    payload = _plan_payload(
        [
            _plan_item(
                metric_id="customer_segment_revenue_structure",
                metric_family="structure_metric",
                metric_type="derived",
                required_field_roles=["object_key", "amount_field"],
                matched_fields=["customer_segment", "net_revenue"],
                missing_fields=[],
                grain="customer_type",
                evidence_level="B_DERIVED",
                confidence=0.83,
                calculation_feasibility="calculable",
                business_question_answered="不同客户类型收入结构如何分布",
                formula_or_logic="share(net_revenue by customer_segment)",
                caveat="structure metric",
            )
        ]
    )
    _, plan = _run_plan(tmp_path, semantic_result=semantic, routing_result=routing, dataframe_profile={}, payload=payload)
    assert plan.metric_plans[0].metric_family == "structure_metric"


def test_metric_planner_blocks_profit_without_cost(tmp_path: Path) -> None:
    semantic = _semantic_result(
        mappings=[_mapping("gmv", "revenue", "amount_field")],
        object_grain="sku",
        time_grain="day",
    )
    routing = _routing_result("procurement_sales_report")
    payload = _plan_payload(
        [
            _plan_item(
                metric_id="gross_margin",
                metric_family="profitability_metric",
                metric_type="derived",
                required_field_roles=["amount_field", "cost_field"],
                matched_fields=["gmv"],
                missing_fields=[],
                grain="sku_day",
                evidence_level="B_DERIVED",
                confidence=0.9,
                calculation_feasibility="calculable",
                business_question_answered="盈利能力如何",
                formula_or_logic="(gmv - cost) / gmv",
                caveat="requires cost",
            )
        ]
    )
    with pytest.raises(AIMetricDerivationPlannerValidationError):
        _run_plan(tmp_path, semantic_result=semantic, routing_result=routing, dataframe_profile={}, payload=payload)


def test_metric_planner_blocks_inventory_action_without_inventory(tmp_path: Path) -> None:
    semantic = _semantic_result(
        mappings=[
            _mapping("sku_id", "sku_id", "sku_key"),
            _mapping("sales_qty", "quantity", "quantity_field"),
        ],
        object_grain="sku",
        time_grain="day",
    )
    routing = _routing_result("procurement_sales_report")
    payload = _plan_payload(
        [
            _plan_item(
                metric_id="inventory_turnover_proxy",
                metric_family="inventory_metric",
                metric_type="derived",
                required_field_roles=["inventory_field", "quantity_field"],
                matched_fields=["sales_qty"],
                missing_fields=[],
                grain="sku_day",
                evidence_level="B_DERIVED",
                confidence=0.82,
                calculation_feasibility="calculable",
                business_question_answered="库存周转是否健康",
                formula_or_logic="sales_qty / inventory",
                caveat="requires inventory",
            )
        ]
    )
    with pytest.raises(AIMetricDerivationPlannerValidationError):
        _run_plan(tmp_path, semantic_result=semantic, routing_result=routing, dataframe_profile={}, payload=payload)


def test_metric_planner_handles_date_user_id_as_active_metric_family(tmp_path: Path) -> None:
    semantic = _semantic_result(
        mappings=[
            _mapping("member_id", "user_id", "user_key"),
            _mapping("ds", "date", "time_key"),
        ],
        object_grain="user",
        time_grain="day",
    )
    routing = _routing_result("internet_operations_report")
    payload = _plan_payload(
        [
            _plan_item(
                metric_id="member_activity_scale",
                metric_family="retention_metric",
                metric_type="derived",
                required_field_roles=["user_key", "time_key"],
                matched_fields=["member_id", "ds"],
                missing_fields=[],
                grain="day",
                evidence_level="B_DERIVED",
                confidence=0.86,
                calculation_feasibility="calculable",
                business_question_answered="活跃用户规模是否变化",
                formula_or_logic="nunique(member_id) by day(ds)",
                caveat="active metric, not full retention",
            )
        ]
    )
    _run_plan(
        tmp_path,
        semantic_result=semantic,
        routing_result=routing,
        dataframe_profile={"time_profile": {"distinct_time_points": 8, "window_days": 8}},
        payload=payload,
    )
    semantic_plan = json.loads((tmp_path / "outputs" / "metric_mining" / "semantic_metric_plan.json").read_text(encoding="utf-8"))
    assert "retention_metric" in semantic_plan["available_metric_families"]


def test_metric_planner_retention_requires_sufficient_time_window(tmp_path: Path) -> None:
    semantic = _semantic_result(
        mappings=[_mapping("user_id", "user_id", "user_key"), _mapping("date", "date", "time_key")],
        object_grain="user",
        time_grain="day",
    )
    routing = _routing_result("internet_operations_report")
    payload = _plan_payload(
        [
            _plan_item(
                metric_id="d7_retention",
                metric_family="retention_metric",
                metric_type="derived",
                required_field_roles=["user_key", "time_key"],
                matched_fields=["user_id", "date"],
                missing_fields=[],
                grain="cohort_day",
                evidence_level="B_DERIVED",
                confidence=0.8,
                calculation_feasibility="calculable",
                business_question_answered="D7 留存是否稳定",
                formula_or_logic="retained_users_d7 / cohort_users",
                caveat="requires >= 7 day window",
            )
        ]
    )
    with pytest.raises(AIMetricDerivationPlannerValidationError):
        _run_plan(
            tmp_path,
            semantic_result=semantic,
            routing_result=routing,
            dataframe_profile={"time_profile": {"distinct_time_points": 3, "window_days": 3}},
            payload=payload,
        )


def test_metric_planner_funnel_requires_orderable_steps(tmp_path: Path) -> None:
    semantic = _semantic_result(
        mappings=[
            _mapping("user_id", "user_id", "user_key"),
            _mapping("event_name", "event_type", "event_field"),
        ],
        object_grain="user",
        time_grain="day",
    )
    routing = _routing_result("internet_operations_report")
    payload = _plan_payload(
        [
            _plan_item(
                metric_id="event_funnel_completion",
                metric_family="conversion_metric",
                metric_type="derived",
                required_field_roles=["event_field", "user_key"],
                matched_fields=["user_id", "event_name"],
                missing_fields=[],
                grain="event_step",
                evidence_level="B_DERIVED",
                confidence=0.75,
                calculation_feasibility="calculable",
                business_question_answered="事件漏斗完成率如何",
                formula_or_logic="last_step_users / first_step_users",
                caveat="requires orderable steps",
            )
        ]
    )
    with pytest.raises(AIMetricDerivationPlannerValidationError):
        _run_plan(tmp_path, semantic_result=semantic, routing_result=routing, dataframe_profile={}, payload=payload)


def test_metric_planner_outputs_forbidden_downstream_usage(tmp_path: Path) -> None:
    semantic = _semantic_result(
        mappings=[
            _mapping("comment_text", "comment_text", "text_feedback_field"),
            _mapping("date", "date", "time_key"),
        ],
        object_grain="sku",
        time_grain="day",
    )
    routing = _routing_result("generic_long_business_report")
    payload = _plan_payload(
        [
            _plan_item(
                metric_id="comment_risk_proxy",
                metric_family="quality_metric",
                metric_type="proxy",
                required_field_roles=["text_feedback_field"],
                matched_fields=["comment_text"],
                missing_fields=["rating_field"],
                grain="sku_day",
                evidence_level="C_PROXY",
                confidence=0.61,
                calculation_feasibility="proxy_only",
                business_question_answered="评论是否暴露质量风险",
                formula_or_logic="keyword_scan(comment_text)",
                caveat="text only, no rating support",
                forbidden_downstream_usage=["formal_quality_pass_fail"],
            ),
            _plan_item(
                metric_id="need_rating_validation",
                metric_family="diagnostic_metric",
                metric_type="diagnostic",
                required_field_roles=["text_feedback_field", "time_key"],
                matched_fields=["comment_text", "date"],
                missing_fields=["rating_field"],
                grain="sku_day",
                evidence_level="D_DIAGNOSTIC",
                confidence=0.55,
                calculation_feasibility="diagnostic_only",
                business_question_answered="是否需要补评分后再做质量结论",
                caveat="diagnostic only",
                forbidden_downstream_usage=["formal_management_decision"],
            ),
            _plan_item(
                metric_id="formal_quality_score",
                metric_family="quality_metric",
                metric_type="unavailable",
                required_field_roles=["rating_field"],
                matched_fields=[],
                missing_fields=["rating_field"],
                grain="sku_day",
                evidence_level="E_UNSUPPORTED",
                confidence=0.2,
                calculation_feasibility="unsupported",
                business_question_answered="当前质量得分是否稳定",
                caveat="missing rating support",
                forbidden_downstream_usage=["formal_management_decision"],
            ),
        ]
    )
    _, plan = _run_plan(tmp_path, semantic_result=semantic, routing_result=routing, dataframe_profile={}, payload=payload)
    for item in plan.metric_plans:
        if item.metric_type in {"proxy", "diagnostic", "unavailable"}:
            assert item.forbidden_downstream_usage


def test_metric_planner_repairs_unavailable_formula_noise(tmp_path: Path) -> None:
    semantic = _semantic_result(
        mappings=[_mapping("gmv", "revenue", "amount_field")],
        object_grain="sku",
        time_grain="day",
    )
    routing = _routing_result("ecommerce_product_operations_report")
    payload = _plan_payload(
        [
            _plan_item(
                metric_id="conversion_rate",
                metric_family="conversion_metric",
                metric_type="unavailable",
                required_field_roles=["conversion_field", "click_field"],
                matched_fields=[],
                missing_fields=["conversion_field", "click_field"],
                grain="sku_day",
                evidence_level="E_UNSUPPORTED",
                confidence=0.2,
                calculation_feasibility="unsupported",
                business_question_answered="当前转化率是否稳定",
                formula_or_logic="conversion / click",
                caveat="missing conversion and click",
                forbidden_downstream_usage=["formal_management_conclusion"],
            )
        ]
    )
    _, plan = _run_plan(tmp_path, semantic_result=semantic, routing_result=routing, dataframe_profile={}, payload=payload)
    assert plan.metric_plans[0].metric_type == "unavailable"
    assert plan.metric_plans[0].formula_or_logic == ""


def test_metric_planner_normalizes_inventory_balance_role_alias(tmp_path: Path) -> None:
    semantic = _semantic_result(
        mappings=[
            _mapping("sku", "sku_id", "sku_key"),
            _mapping("revenue", "revenue", "amount_field"),
        ],
        object_grain="sku",
        time_grain="day",
        context="procurement sales",
    )
    routing = _routing_result("procurement_sales_report")
    payload = _plan_payload(
        [
            _plan_item(
                metric_id="inventory_balance_gap",
                metric_family="inventory_metric",
                metric_type="unavailable",
                required_field_roles=["inventory_balance", "sku_key"],
                matched_fields=["sku"],
                missing_fields=["inventory_field"],
                grain="sku_day",
                evidence_level="E_UNSUPPORTED",
                confidence=0.2,
                calculation_feasibility="unsupported",
                business_question_answered="当前库存余额是否支持补货结论",
                caveat="missing inventory balance field",
                forbidden_downstream_usage=["formal_management_conclusion"],
            )
        ]
    )
    _, plan = _run_plan(
        tmp_path,
        semantic_result=semantic,
        routing_result=routing,
        dataframe_profile={},
        payload=payload,
    )
    assert plan.metric_plans[0].required_field_roles == ["inventory_field", "sku_key"]
