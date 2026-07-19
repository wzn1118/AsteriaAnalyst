from __future__ import annotations

from pathlib import Path

import pytest

from app.services.ai_mandatory.field_semantic_mapper import (
    AIClientAdapter,
    AIFieldSemanticMappingValidationError,
    AIRequiredButUnavailableError,
    map_fields_with_ai,
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


def _common_kwargs(tmp_path: Path) -> dict:
    return {
        "output_dir": tmp_path,
        "dataframe_profile": {"row_count": 10, "column_count": 4},
        "file_name": "orders.xlsx",
        "sheet_name": "Sheet1",
        "user_task_description": "识别字段语义并准备后续路由",
        "field_names": ["order_id", "sku_id", "gmv", "date"],
        "inferred_data_types": {"order_id": "string", "sku_id": "string", "gmv": "float", "date": "datetime"},
        "sample_values": {"order_id": ["o1", "o2"], "sku_id": ["s1", "s2"], "gmv": [100.0, 120.0], "date": ["2026-01-01"]},
        "missing_rate": {"order_id": 0.0, "sku_id": 0.0, "gmv": 0.0, "date": 0.0},
        "unique_count": {"order_id": 10, "sku_id": 8, "gmv": 10, "date": 5},
        "numeric_distribution": {"gmv": {"mean": 110.0, "p50": 108.0}},
        "top_values": {"sku_id": ["s1", "s2"], "date": ["2026-01-01", "2026-01-02"]},
        "date_parse_rate": {"date": 1.0},
    }


def test_field_semantic_mapper_calls_ai_client(tmp_path: Path) -> None:
    client = FakeAIClient(
        {
            "inferred_business_context": "电商交易场景",
            "object_grain": "order",
            "time_grain": "day",
            "field_mappings": [
                {
                    "field_name": "order_id",
                    "canonical_concept": "order_id",
                    "business_role": "transaction_key",
                    "granularity_hint": "order",
                    "confidence": 0.98,
                    "evidence": ["field name match"],
                    "alternative_mappings": [],
                    "risk_note": "",
                },
                {
                    "field_name": "sku_id",
                    "canonical_concept": "sku_id",
                    "business_role": "product_key",
                    "granularity_hint": "sku",
                    "confidence": 0.95,
                    "evidence": ["field name match"],
                    "alternative_mappings": [],
                    "risk_note": "",
                },
            ],
            "uncertain_fields": [],
            "provider": "OpenAI Codex API",
            "model": "gpt-5.4",
            "trace_id": "trace-semantic-001",
        }
    )

    result = map_fields_with_ai(ai_client=client, **_common_kwargs(tmp_path))

    assert client.called is True
    assert result.trace_id == "trace-semantic-001"
    assert (tmp_path / "outputs" / "ai_traces" / "ai_field_semantic_mapping.json").exists()


def test_field_semantic_mapper_rejects_nonexistent_fields(tmp_path: Path) -> None:
    client = FakeAIClient(
        {
            "inferred_business_context": "电商交易场景",
            "object_grain": "order",
            "time_grain": "day",
            "field_mappings": [
                {
                    "field_name": "nonexistent_field",
                    "canonical_concept": "gmv",
                    "business_role": "amount_metric",
                    "granularity_hint": "order",
                    "confidence": 0.7,
                    "evidence": ["hallucinated"],
                    "alternative_mappings": [],
                    "risk_note": "",
                }
            ],
            "uncertain_fields": [],
            "provider": "OpenAI Codex API",
            "model": "gpt-5.4",
            "trace_id": "trace-semantic-002",
        }
    )

    with pytest.raises(AIFieldSemanticMappingValidationError):
        map_fields_with_ai(ai_client=client, **_common_kwargs(tmp_path))


def test_field_semantic_mapper_no_ai_no_formal_path(tmp_path: Path) -> None:
    client = FakeAIClient(
        {
            "__ai_unavailable__": True,
            "reason": "missing_api_key",
            "live_available": False,
            "runtime_state": "fallback",
        }
    )

    with pytest.raises(AIRequiredButUnavailableError):
        map_fields_with_ai(ai_client=client, **_common_kwargs(tmp_path))
