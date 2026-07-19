from __future__ import annotations

import json

from app.services.ai_mandatory.ai_usage_gate import validate_ai_mandatory_artifacts
from app.services.ai_mandatory.schemas import (
    AIBusinessRoutingResult,
    AIFieldSemanticMappingResult,
    AIMetricDerivationPlan,
)
from app.services.ai_mandatory.trace_writer import (
    write_ai_business_routing_trace,
    write_ai_field_semantic_mapping_trace,
    write_ai_metric_derivation_plan_trace,
    write_ai_usage_gate_trace,
)


def _write_deterministic_metric_artifacts(tmp_path, trace_id: str) -> None:
    metric_dir = tmp_path / "outputs" / "metric_mining"
    metric_dir.mkdir(parents=True, exist_ok=True)
    (metric_dir / "semantic_metric_result.json").write_text(
        json.dumps(
            {
                "trace_id": trace_id,
                "provider": "deterministic",
                "model": "deterministic-metric-executor",
                "results": [],
                "summary": {
                    "calculated_count": 0,
                    "proxy_calculated_count": 0,
                    "unavailable_count": 0,
                    "failed_count": 0,
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (metric_dir / "metric_derivation_log.csv").write_text(
        "metric_id,metric_name_cn,status,source_fields,formula,calculation_method,evidence_level,confidence,caveat,unsupported_reason\n",
        encoding="utf-8",
    )


def test_ai_usage_gate_missing_trace_blocks_release(tmp_path) -> None:
    field_mapping = AIFieldSemanticMappingResult(
        inferred_business_context="平台电商商品经营",
        object_grain="sku",
        time_grain="day",
        field_mappings=[],
        uncertain_fields=[],
        provider="OpenAI",
        model="gpt-5.4",
        trace_id="trace-semantic-001",
    )
    routing = AIBusinessRoutingResult(
        selected_by_user="auto",
        ai_route="ecommerce_product_operations_report",
        final_route="ecommerce_product_operations_report",
        confidence=0.9,
        alternative_routes=[],
        reason="商品字段与交易字段同时存在",
        blocked_routes=[],
        trace_id="trace-route-001",
    )

    write_ai_field_semantic_mapping_trace(tmp_path, field_mapping)
    write_ai_business_routing_trace(tmp_path, routing)
    _write_deterministic_metric_artifacts(tmp_path, "trace-plan-001")

    result = validate_ai_mandatory_artifacts(tmp_path)

    assert result["passed"] is False
    assert "ai_metric_derivation_plan.json missing" in result["failure_reasons"]


def test_ai_usage_gate_passes_with_complete_trace_set(tmp_path) -> None:
    field_mapping = AIFieldSemanticMappingResult(
        inferred_business_context="平台电商商品经营",
        object_grain="sku",
        time_grain="day",
        field_mappings=[],
        uncertain_fields=[],
        provider="OpenAI",
        model="gpt-5.4",
        trace_id="trace-semantic-001",
    )
    routing = AIBusinessRoutingResult(
        selected_by_user="auto",
        ai_route="ecommerce_product_operations_report",
        final_route="ecommerce_product_operations_report",
        confidence=0.9,
        alternative_routes=[],
        reason="商品字段与交易字段同时存在",
        blocked_routes=[],
        trace_id="trace-route-001",
    )
    plan = AIMetricDerivationPlan(
        available_metrics=["gmv", "average_order_value"],
        unavailable_metrics=["roi"],
        proxy_metrics=["review_per_order_proxy"],
        diagnostic_questions=["缺成本时不得判断利润"],
        metric_plans=[],
        trace_id="trace-plan-001",
    )

    write_ai_field_semantic_mapping_trace(tmp_path, field_mapping)
    write_ai_business_routing_trace(tmp_path, routing)
    write_ai_metric_derivation_plan_trace(tmp_path, plan)
    _write_deterministic_metric_artifacts(tmp_path, plan.trace_id)

    result = validate_ai_mandatory_artifacts(tmp_path)
    write_ai_usage_gate_trace(tmp_path, result)

    assert result["passed"] is True
    gate_path = tmp_path / "outputs" / "ai_traces" / "ai_usage_gate_result.json"
    assert gate_path.exists()
    persisted = json.loads(gate_path.read_text(encoding="utf-8"))
    assert persisted["passed"] is True


def test_ai_usage_gate_warns_but_passes_on_low_route_confidence(tmp_path) -> None:
    field_mapping = AIFieldSemanticMappingResult(
        inferred_business_context="ambiguous business context",
        object_grain="mixed",
        time_grain="day",
        field_mappings=[],
        uncertain_fields=[],
        provider="OpenAI",
        model="gpt-5.4",
        trace_id="trace-semantic-low-confidence",
    )
    routing = AIBusinessRoutingResult(
        selected_by_user=None,
        ai_route="generic_long_business_report",
        final_route="generic_long_business_report",
        confidence=0.42,
        alternative_routes=["internet_operations_report", "ecommerce_product_operations_report"],
        reason="mixed signals",
        blocked_routes=[],
        trace_id="trace-route-low-confidence",
    )
    plan = AIMetricDerivationPlan(
        available_metrics=["row_count"],
        unavailable_metrics=[],
        proxy_metrics=[],
        diagnostic_questions=[],
        metric_plans=[],
        trace_id="trace-plan-low-confidence",
    )

    write_ai_field_semantic_mapping_trace(tmp_path, field_mapping)
    write_ai_business_routing_trace(tmp_path, routing)
    write_ai_metric_derivation_plan_trace(tmp_path, plan)
    _write_deterministic_metric_artifacts(tmp_path, plan.trace_id)

    result = validate_ai_mandatory_artifacts(tmp_path)

    assert result["passed"] is True
    assert result["failure_reasons"] == []
    assert result["diagnostics"]["warnings"][0]["code"] == "ROUTE_CONFIDENCE_LOW"


def test_ai_usage_gate_missing_deterministic_artifacts_blocks_release(tmp_path) -> None:
    field_mapping = AIFieldSemanticMappingResult(
        inferred_business_context="ecommerce operations",
        object_grain="sku",
        time_grain="day",
        field_mappings=[],
        uncertain_fields=[],
        provider="OpenAI",
        model="gpt-5.4",
        trace_id="trace-semantic-002",
    )
    routing = AIBusinessRoutingResult(
        selected_by_user="auto",
        ai_route="ecommerce_product_operations_report",
        final_route="ecommerce_product_operations_report",
        confidence=0.9,
        alternative_routes=[],
        reason="test routing",
        blocked_routes=[],
        trace_id="trace-route-002",
    )
    plan = AIMetricDerivationPlan(
        available_metrics=["gmv"],
        unavailable_metrics=[],
        proxy_metrics=[],
        diagnostic_questions=[],
        metric_plans=[],
        trace_id="trace-plan-002",
    )

    write_ai_field_semantic_mapping_trace(tmp_path, field_mapping)
    write_ai_business_routing_trace(tmp_path, routing)
    write_ai_metric_derivation_plan_trace(tmp_path, plan)

    result = validate_ai_mandatory_artifacts(tmp_path)

    assert result["passed"] is False
    assert "semantic_metric_result.json missing" in result["failure_reasons"]
    assert "metric_derivation_log.csv missing" in result["failure_reasons"]
