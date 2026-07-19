from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services.ai_mandatory.ai_usage_gate import validate_ai_mandatory_artifacts
from app.services.ai_mandatory.business_context_router import route_business_context_with_ai
from app.services.ai_mandatory.field_semantic_mapper import AIClientAdapter
from app.services.ai_mandatory.schemas import (
    AIFieldSemanticMapping,
    AIFieldSemanticMappingResult,
    AIMetricDerivationPlan,
)
from app.services.ai_mandatory.trace_writer import write_ai_metric_derivation_plan_trace


class FakeAIClient(AIClientAdapter):
    def __init__(self, payload: dict):
        self.payload = payload
        self.called = False

    def complete_json(self, *, system_prompt: str, user_payload: dict) -> dict:
        self.called = True
        self.system_prompt = system_prompt
        self.user_payload = user_payload
        return dict(self.payload)


def _write_deterministic_metric_artifacts(tmp_path: Path, trace_id: str) -> None:
    metric_dir = tmp_path / "outputs" / "metric_mining"
    metric_dir.mkdir(parents=True, exist_ok=True)
    (metric_dir / "semantic_metric_result.json").write_text(
        json.dumps(
            {
                "trace_id": trace_id,
                "provider": "deterministic",
                "model": "deterministic-metric-executor",
                "results": [],
                "summary": {},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (metric_dir / "metric_derivation_log.csv").write_text(
        "metric_id,metric_name_cn,status,source_fields,formula,calculation_method,evidence_level,confidence,caveat,unsupported_reason\n",
        encoding="utf-8",
    )


def _mapping_result(*, grain: str = "sku_day") -> AIFieldSemanticMappingResult:
    return AIFieldSemanticMappingResult(
        inferred_business_context="商品经营场景",
        object_grain=grain,
        time_grain="day",
        field_mappings=[
            AIFieldSemanticMapping(
                field_name="sku_id",
                canonical_concept="sku_id",
                business_role="product_key",
                granularity_hint="sku",
                confidence=0.98,
                evidence=["field name"],
                alternative_mappings=[],
                risk_note="",
            ),
            AIFieldSemanticMapping(
                field_name="gmv",
                canonical_concept="gmv",
                business_role="amount_metric",
                granularity_hint="sku_day",
                confidence=0.95,
                evidence=["field name"],
                alternative_mappings=["revenue"],
                risk_note="",
            ),
            AIFieldSemanticMapping(
                field_name="seller_id",
                canonical_concept="seller_id",
                business_role="merchant_key",
                granularity_hint="seller",
                confidence=0.91,
                evidence=["field name"],
                alternative_mappings=["supplier_id"],
                risk_note="",
            ),
            AIFieldSemanticMapping(
                field_name="category",
                canonical_concept="category",
                business_role="category_dimension",
                granularity_hint="category",
                confidence=0.9,
                evidence=["field name"],
                alternative_mappings=[],
                risk_note="",
            ),
        ],
        uncertain_fields=[],
        provider="OpenAI Codex API",
        model="gpt-5.4",
        trace_id="trace-semantic-router-001",
    )


def test_ai_business_router_calls_ai(tmp_path: Path) -> None:
    client = FakeAIClient(
        {
            "ai_route": "ecommerce_product_operations_report",
            "final_route": "ecommerce_product_operations_report",
            "confidence": 0.92,
            "alternative_routes": ["procurement_sales_report"],
            "reason": "sku/gmv/category/seller signals dominate",
            "blocked_routes": [],
            "trace_id": "trace-route-001",
        }
    )

    result = route_business_context_with_ai(
        output_dir=tmp_path,
        user_selected_report_type="auto",
        semantic_mapping_result=_mapping_result(),
        deterministic_data_profile={"deterministic_router_result": {"business_profile": "ecommerce_product_operations_report"}},
        file_name="taobao_sku.xlsx",
        sheet_name="Sheet1",
        user_task_description="判断商品经营主链",
        ai_client=client,
    )

    assert client.called is True
    assert result.final_route == "ecommerce_product_operations_report"
    assert (tmp_path / "outputs" / "ai_traces" / "ai_business_routing.json").exists()


def test_user_selected_report_type_takes_priority(tmp_path: Path) -> None:
    client = FakeAIClient({})
    result = route_business_context_with_ai(
        output_dir=tmp_path,
        user_selected_report_type="procurement_sales_report",
        semantic_mapping_result=_mapping_result(),
        deterministic_data_profile={},
        file_name="jd_procurement.xlsx",
        sheet_name="Sheet1",
        user_task_description="采销复盘",
        ai_client=client,
    )

    assert result.final_route == "procurement_sales_report"
    assert client.called is False


def test_taobao_ecommerce_not_misrouted_to_internet_ops(tmp_path: Path) -> None:
    client = FakeAIClient(
        {
            "ai_route": "internet_operations_report",
            "final_route": "internet_operations_report",
            "confidence": 0.87,
            "alternative_routes": ["ecommerce_product_operations_report"],
            "reason": "date and traffic-like columns exist",
            "blocked_routes": [],
            "trace_id": "trace-route-002",
        }
    )

    result = route_business_context_with_ai(
        output_dir=tmp_path,
        user_selected_report_type="auto",
        semantic_mapping_result=_mapping_result(grain="sku"),
        deterministic_data_profile={"deterministic_router_result": {"business_profile": "ecommerce_product_operations_report"}},
        file_name="淘宝商品聚合数据.xlsx",
        sheet_name="Sheet1",
        user_task_description="分析商品结构、销售额、类目和供应商表现",
        ai_client=client,
    )

    assert result.final_route in {"ecommerce_product_operations_report", "procurement_sales_report"}
    assert result.final_route != "internet_operations_report"
    assert "internet_operations_report" in result.blocked_routes


def test_low_route_confidence_does_not_block_ai_usage_gate(tmp_path: Path) -> None:
    client = FakeAIClient(
        {
            "ai_route": "generic_long_business_report",
            "final_route": "generic_long_business_report",
            "confidence": 0.62,
            "alternative_routes": ["internet_operations_report"],
            "reason": "signals mixed and ambiguous",
            "blocked_routes": [],
            "trace_id": "trace-route-003",
        }
    )

    result = route_business_context_with_ai(
        output_dir=tmp_path,
        user_selected_report_type="auto",
        semantic_mapping_result=_mapping_result(grain="unknown"),
        deterministic_data_profile={"deterministic_router_result": {"business_profile": "generic_long_business_report"}},
        file_name="mixed_dataset.xlsx",
        sheet_name="Sheet1",
        user_task_description="自动识别主链",
        ai_client=client,
    )

    assert result.confidence < 0.70
    uncertainty_path = tmp_path / "outputs" / "ai_traces" / "routing_uncertainty_report.md"
    assert uncertainty_path.exists()
    uncertainty_text = uncertainty_path.read_text(encoding="utf-8")
    assert "must not block formal or exploratory report release" in uncertainty_text

    field_mapping_trace = tmp_path / "outputs" / "ai_traces" / "ai_field_semantic_mapping.json"
    field_mapping_trace.parent.mkdir(parents=True, exist_ok=True)
    field_mapping_trace.write_text(
        json.dumps(_mapping_result().model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_ai_metric_derivation_plan_trace(
        tmp_path,
        AIMetricDerivationPlan(
            available_metrics=["gmv"],
            unavailable_metrics=[],
            proxy_metrics=[],
            diagnostic_questions=[],
            metric_plans=[],
            trace_id="trace-plan-low-confidence",
        ),
    )
    _write_deterministic_metric_artifacts(tmp_path, "trace-plan-low-confidence")

    gate = validate_ai_mandatory_artifacts(tmp_path)
    assert gate["passed"] is True
    assert "ai_business_routing.json confidence below 0.70" not in gate["failure_reasons"]
    assert gate["diagnostics"]["warnings"][0]["code"] == "ROUTE_CONFIDENCE_LOW"
