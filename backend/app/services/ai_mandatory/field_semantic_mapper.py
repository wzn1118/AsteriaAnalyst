from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from app.services.codex_service import _request_codex_json

from .schemas import AIFieldSemanticMappingResult
from .trace_writer import write_ai_field_semantic_mapping_trace


CANONICAL_CONCEPTS = [
    "date",
    "user_id",
    "order_id",
    "sku_id",
    "product_id",
    "category",
    "seller_id",
    "supplier_id",
    "revenue",
    "gmv",
    "cost",
    "price",
    "quantity",
    "inventory",
    "stock",
    "rating",
    "review_score",
    "comment_text",
    "impression",
    "click",
    "conversion",
    "event_type",
    "channel",
    "campaign",
    "session_id",
]


class AIRequiredButUnavailableError(RuntimeError):
    pass


class AIFieldSemanticMappingValidationError(ValueError):
    pass


class AIClientAdapter:
    def __init__(
        self,
        *,
        model: str = "gpt-5.4",
        reasoning_effort: str = "minimal",
        timeout_seconds: int = 300,
    ) -> None:
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.timeout_seconds = timeout_seconds

    def complete_json(
        self,
        *,
        system_prompt: str,
        user_payload: dict[str, Any],
    ) -> dict[str, Any]:
        return _request_codex_json(
            system_prompt=system_prompt,
            user_payload=user_payload,
            fallback_builder=lambda reason, payload: {
                "__ai_unavailable__": True,
                "reason": reason,
                "input_echo": payload,
            },
            model_override=self.model,
            reasoning_effort_override=self.reasoning_effort,
            timeout_seconds=self.timeout_seconds,
            store=False,
        )


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _normalize(value: Any) -> str:
    return "".join(ch for ch in _safe_text(value).lower() if ch.isalnum() or "\u4e00" <= ch <= "\u9fff")


def _field_set(field_names: list[str]) -> set[str]:
    return {str(name) for name in field_names}


def _build_prompt_payload(
    *,
    dataframe_profile: dict[str, Any] | None,
    file_name: str,
    sheet_name: str,
    user_task_description: str,
    field_names: list[str],
    inferred_data_types: dict[str, Any],
    sample_values: dict[str, Any] | list[Any] | None,
    missing_rate: dict[str, Any],
    unique_count: dict[str, Any],
    numeric_distribution: dict[str, Any],
    top_values: dict[str, Any],
    date_parse_rate: dict[str, Any],
) -> dict[str, Any]:
    return {
        "task": "ai_field_semantic_mapping",
        "file_name": file_name,
        "sheet_name": sheet_name,
        "user_task_description": user_task_description,
        "allowed_canonical_concepts": CANONICAL_CONCEPTS,
        "dataframe_profile": dataframe_profile or {},
        "field_names": field_names,
        "inferred_data_types": inferred_data_types,
        "sample_values": sample_values or {},
        "missing_rate": missing_rate,
        "unique_count": unique_count,
        "numeric_distribution": numeric_distribution,
        "top_values": top_values,
        "date_parse_rate": date_parse_rate,
        "required_output_schema": {
            "inferred_business_context": "string",
            "object_grain": "string",
            "time_grain": "string",
            "field_mappings": [
                {
                    "field_name": "string",
                    "canonical_concept": "string",
                    "business_role": "string",
                    "granularity_hint": "string",
                    "confidence": "float 0-1",
                    "evidence": ["string"],
                    "alternative_mappings": ["string"],
                    "risk_note": "string",
                }
            ],
            "uncertain_fields": ["string"],
            "provider": "string",
            "model": "string",
            "trace_id": "string",
        },
    }


def _build_system_prompt() -> str:
    return (
        "You are AIFieldSemanticMapper for AsteriaAnalyst. "
        "You must perform real semantic interpretation from field names, sample values, missingness, uniqueness, "
        "numeric distribution, top values, date parse rate, file name, sheet name, and user task description. "
        "Do not guess fields that are not present. "
        "Return JSON only. "
        "Do not fabricate numeric facts. "
        "Use the allowed canonical_concepts list when possible, otherwise use the closest stable concept name. "
        "You must map each field_name only if you have evidence. "
        "Fields with ambiguity should go into uncertain_fields. "
        "Output must be valid for the requested schema."
    )


def _validate_fields_exist(
    result: AIFieldSemanticMappingResult,
    available_fields: set[str],
) -> None:
    missing_fields = [
        mapping.field_name
        for mapping in result.field_mappings
        if mapping.field_name not in available_fields
    ]
    missing_uncertain = [
        field_name for field_name in result.uncertain_fields if field_name not in available_fields
    ]
    if missing_fields or missing_uncertain:
        details = []
        if missing_fields:
            details.append(f"field_mappings unknown fields: {missing_fields}")
        if missing_uncertain:
            details.append(f"uncertain_fields unknown fields: {missing_uncertain}")
        raise AIFieldSemanticMappingValidationError("; ".join(details))


def map_fields_with_ai(
    *,
    output_dir: str | Path,
    dataframe_profile: dict[str, Any] | None,
    file_name: str,
    sheet_name: str,
    user_task_description: str,
    field_names: list[str],
    inferred_data_types: dict[str, Any],
    sample_values: dict[str, Any] | list[Any] | None,
    missing_rate: dict[str, Any],
    unique_count: dict[str, Any],
    numeric_distribution: dict[str, Any],
    top_values: dict[str, Any],
    date_parse_rate: dict[str, Any],
    ai_client: AIClientAdapter | None = None,
) -> AIFieldSemanticMappingResult:
    client = ai_client or AIClientAdapter()
    user_payload = _build_prompt_payload(
        dataframe_profile=dataframe_profile,
        file_name=file_name,
        sheet_name=sheet_name,
        user_task_description=user_task_description,
        field_names=field_names,
        inferred_data_types=inferred_data_types,
        sample_values=sample_values,
        missing_rate=missing_rate,
        unique_count=unique_count,
        numeric_distribution=numeric_distribution,
        top_values=top_values,
        date_parse_rate=date_parse_rate,
    )
    raw = client.complete_json(
        system_prompt=_build_system_prompt(),
        user_payload=user_payload,
    )

    if raw.get("__ai_unavailable__") or raw.get("live_available") is False or raw.get("runtime_state") == "fallback":
        raise AIRequiredButUnavailableError(_safe_text(raw.get("reason") or raw.get("fallback_reason") or "AI unavailable"))

    payload = dict(raw)
    payload["provider"] = _safe_text(payload.get("provider") or payload.get("provider_label") or "OpenAI Codex API")
    payload["model"] = _safe_text(payload.get("model") or "unknown")
    payload["trace_id"] = _safe_text(payload.get("trace_id") or f"ai-field-semantic-{uuid.uuid4().hex[:12]}")

    try:
        validated = AIFieldSemanticMappingResult.model_validate(payload)
    except Exception as exc:
        raise AIFieldSemanticMappingValidationError(f"schema validation failed: {exc}") from exc

    _validate_fields_exist(validated, _field_set(field_names))
    write_ai_field_semantic_mapping_trace(output_dir, validated)
    return validated


__all__ = [
    "AIClientAdapter",
    "AIRequiredButUnavailableError",
    "AIFieldSemanticMappingValidationError",
    "map_fields_with_ai",
]
