from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from .field_semantic_mapper import AIClientAdapter, AIRequiredButUnavailableError
from .schemas import AIBusinessRoutingResult, AIFieldSemanticMappingResult
from .trace_writer import write_ai_business_routing_trace


ALLOWED_MAIN_REPORT_ROUTES = {
    "procurement_sales_report",
    "ecommerce_product_operations_report",
    "internet_operations_report",
    "media_campaign_report",
    "generic_long_business_report",
    "generic_business_report",
    "insufficient_for_management_decision",
}

OPTIONAL_ONLY_ROUTE = "independent_industry_research_chain"

ROUTE_ALIASES = {
    "auto": "auto",
    "procurement_sales": "procurement_sales_report",
    "procurement_sales_report": "procurement_sales_report",
    "ecommerce_product_operations_report": "ecommerce_product_operations_report",
    "internet_operations_report": "internet_operations_report",
    "internet_ops_review": "internet_operations_report",
    "media_campaign_report": "media_campaign_report",
    "media_review": "media_campaign_report",
    "generic_long_business_report": "generic_long_business_report",
    "generic_business_report": "generic_business_report",
    "insufficient_for_management_decision": "insufficient_for_management_decision",
}

ECOMMERCE_SIGNAL_CONCEPTS = {
    "sku_id",
    "product_id",
    "category",
    "seller_id",
    "supplier_id",
    "order_id",
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
}

INTERNET_SIGNAL_CONCEPTS = {
    "date",
    "user_id",
    "event_type",
    "channel",
    "campaign",
    "session_id",
    "impression",
    "click",
    "conversion",
}

PROCUREMENT_HINT_TOKENS = (
    "采购",
    "procurement",
    "supply",
    "supplier",
    "inventory",
    "库存",
    "毛利",
    "成本",
    "供应商",
)

INTERNET_HINT_TOKENS = (
    "用户",
    "增长",
    "留存",
    "漏斗",
    "活跃",
    "user",
    "retention",
    "funnel",
    "session",
)

ECOMMERCE_HINT_TOKENS = (
    "商品",
    "sku",
    "类目",
    "店铺",
    "供应商",
    "销量",
    "销售额",
    "电商",
    "订单",
    "gmv",
    "淘宝",
    "天猫",
    "京东",
    "拼多多",
)


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _normalize_route(route: str | None) -> str:
    normalized = _safe_text(route)
    return ROUTE_ALIASES.get(normalized, normalized)


def _normalize_text(value: Any) -> str:
    return "".join(ch for ch in _safe_text(value).lower() if ch.isalnum() or "\u4e00" <= ch <= "\u9fff")


def _mapping_concepts(mapping_result: AIFieldSemanticMappingResult) -> set[str]:
    concepts: set[str] = set()
    for mapping in mapping_result.field_mappings:
        concept = _safe_text(mapping.canonical_concept)
        if concept:
            concepts.add(concept)
        role = _safe_text(mapping.business_role)
        if role:
            concepts.add(role)
    return concepts


def _deterministic_router_hint(deterministic_data_profile: dict[str, Any] | None) -> str:
    profile = deterministic_data_profile or {}
    for key in [
        "business_profile",
        "ai_route_hint",
        "deterministic_router_result",
        "router_result",
    ]:
        value = profile.get(key)
        if isinstance(value, dict):
            candidate = _safe_text(value.get("business_profile"))
            if candidate:
                return _normalize_route(candidate)
        else:
            candidate = _safe_text(value)
            if candidate:
                return _normalize_route(candidate)
    return ""


def _semantic_signal_strength(mapping_result: AIFieldSemanticMappingResult) -> dict[str, Any]:
    concepts = _mapping_concepts(mapping_result)
    ecommerce_hits = sorted(concepts.intersection(ECOMMERCE_SIGNAL_CONCEPTS))
    internet_hits = sorted(concepts.intersection(INTERNET_SIGNAL_CONCEPTS))
    object_grain = _safe_text(mapping_result.object_grain).lower()
    return {
        "ecommerce_hits": ecommerce_hits,
        "internet_hits": internet_hits,
        "object_grain": object_grain,
        "ecommerce_strong": len(ecommerce_hits) >= 4 or any(token in object_grain for token in ["sku", "product", "category", "seller", "supplier"]),
        "internet_strong": len(internet_hits) >= 4 or any(token in object_grain for token in ["user", "session", "event", "content"]),
        "procurement_strong": any(token in concepts for token in {"supplier_id", "cost", "inventory", "stock"}) or "supplier" in object_grain,
    }


def _user_task_bias(user_task_description: str) -> dict[str, bool]:
    text = _safe_text(user_task_description).lower()
    return {
        "prefers_procurement": any(token in text for token in [item.lower() for item in PROCUREMENT_HINT_TOKENS]),
        "prefers_ecommerce": any(token in text for token in [item.lower() for item in ECOMMERCE_HINT_TOKENS]),
        "prefers_internet": any(token in text for token in [item.lower() for item in INTERNET_HINT_TOKENS]),
    }


def _choose_ecommerce_or_procurement(signal_strength: dict[str, Any], task_bias: dict[str, bool]) -> str:
    if signal_strength["procurement_strong"] or task_bias["prefers_procurement"]:
        return "procurement_sales_report"
    return "ecommerce_product_operations_report"


def _build_system_prompt() -> str:
    return (
        "You are AIBusinessContextRouter for AsteriaAnalyst. "
        "You must classify the main report route using AIFieldSemanticMappingResult, deterministic profile hints, file name, sheet name, and user task description. "
        "Return JSON only. "
        "Allowed main report routes are procurement_sales_report, ecommerce_product_operations_report, "
        "internet_operations_report, media_campaign_report, generic_long_business_report, generic_business_report, insufficient_for_management_decision. "
        "independent_industry_research_chain is optional only and must not be used as the main report route. "
        "When ecommerce/product-operation signals and internet-behavior signals coexist, prioritize object_grain and task intent instead of date/pv/uv alone."
    )


def _build_user_payload(
    *,
    user_selected_report_type: str,
    semantic_mapping_result: AIFieldSemanticMappingResult,
    deterministic_data_profile: dict[str, Any] | None,
    file_name: str,
    sheet_name: str,
    user_task_description: str,
) -> dict[str, Any]:
    return {
        "task": "ai_business_context_routing",
        "user_selected_report_type": user_selected_report_type,
        "file_name": file_name,
        "sheet_name": sheet_name,
        "user_task_description": user_task_description,
        "semantic_mapping_result": semantic_mapping_result.model_dump(mode="json"),
        "deterministic_data_profile": deterministic_data_profile or {},
        "required_output_schema": {
            "selected_by_user": "string|null",
            "ai_route": "string",
            "final_route": "string",
            "confidence": "float 0-1",
            "alternative_routes": ["string"],
            "reason": "string",
            "blocked_routes": ["string"],
            "trace_id": "string",
        },
    }


def _validate_route(route: str, field_name: str) -> str:
    normalized = _normalize_route(route)
    if normalized not in ALLOWED_MAIN_REPORT_ROUTES and normalized != OPTIONAL_ONLY_ROUTE:
        raise ValueError(f"{field_name} invalid route: {route}")
    return normalized


def _write_uncertainty_report(output_dir: str | Path, result: AIBusinessRoutingResult) -> str:
    trace_dir = Path(output_dir) / "outputs" / "ai_traces"
    trace_dir.mkdir(parents=True, exist_ok=True)
    path = trace_dir / "routing_uncertainty_report.md"
    lines = [
        "# routing_uncertainty_report",
        "",
        f"- ai_route: `{result.ai_route}`",
        f"- final_route: `{result.final_route}`",
        f"- confidence: `{result.confidence}`",
        f"- reason: {result.reason}",
        f"- blocked_routes: {', '.join(result.blocked_routes) or 'none'}",
        "",
        "- confidence < 0.70, so the report should show route uncertainty and manual-confirmation notes.",
        "- Low route confidence is explanatory metadata; it must not block formal or exploratory report release.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(path.resolve())


def route_business_context_with_ai(
    *,
    output_dir: str | Path,
    user_selected_report_type: str,
    semantic_mapping_result: AIFieldSemanticMappingResult,
    deterministic_data_profile: dict[str, Any] | None,
    file_name: str,
    sheet_name: str,
    user_task_description: str,
    ai_client: AIClientAdapter | None = None,
) -> AIBusinessRoutingResult:
    selected = _normalize_route(user_selected_report_type)
    if selected and selected != "auto":
        result = AIBusinessRoutingResult(
            selected_by_user=selected,
            ai_route=selected,
            final_route=selected,
            confidence=1.0,
            alternative_routes=[],
            reason="selected_by_user",
            blocked_routes=[OPTIONAL_ONLY_ROUTE],
            trace_id=f"ai-route-{uuid.uuid4().hex[:12]}",
        )
        write_ai_business_routing_trace(output_dir, result)
        return result

    client = ai_client or AIClientAdapter()
    raw = client.complete_json(
        system_prompt=_build_system_prompt(),
        user_payload=_build_user_payload(
            user_selected_report_type=user_selected_report_type,
            semantic_mapping_result=semantic_mapping_result,
            deterministic_data_profile=deterministic_data_profile,
            file_name=file_name,
            sheet_name=sheet_name,
            user_task_description=user_task_description,
        ),
    )

    if raw.get("__ai_unavailable__") or raw.get("live_available") is False or raw.get("runtime_state") == "fallback":
        raise AIRequiredButUnavailableError(_safe_text(raw.get("reason") or raw.get("fallback_reason") or "AI unavailable"))

    payload = dict(raw)
    payload["selected_by_user"] = None
    payload["ai_route"] = _validate_route(payload.get("ai_route"), "ai_route")
    payload["final_route"] = _validate_route(payload.get("final_route"), "final_route")
    payload["trace_id"] = _safe_text(payload.get("trace_id") or f"ai-route-{uuid.uuid4().hex[:12]}")

    try:
        validated = AIBusinessRoutingResult.model_validate(payload)
    except Exception as exc:
        raise ValueError(f"business routing schema validation failed: {exc}") from exc

    signal_strength = _semantic_signal_strength(semantic_mapping_result)
    task_bias = _user_task_bias(user_task_description)
    blocked_routes = list(validated.blocked_routes)
    final_route = validated.final_route

    if final_route == OPTIONAL_ONLY_ROUTE:
        blocked_routes.append(OPTIONAL_ONLY_ROUTE)
        final_route = "generic_long_business_report"

    deterministic_hint = _deterministic_router_hint(deterministic_data_profile)
    if signal_strength["ecommerce_strong"] and final_route == "internet_operations_report":
        blocked_routes.append("internet_operations_report")
        final_route = _choose_ecommerce_or_procurement(signal_strength, task_bias)
    elif signal_strength["internet_strong"] and not signal_strength["ecommerce_strong"] and final_route not in {"internet_operations_report", "media_campaign_report"}:
        if task_bias["prefers_internet"] or deterministic_hint == "internet_operations_report":
            final_route = "internet_operations_report"
    elif signal_strength["ecommerce_strong"] and signal_strength["internet_strong"]:
        if task_bias["prefers_internet"] and not task_bias["prefers_ecommerce"] and "user" in signal_strength["object_grain"]:
            final_route = "internet_operations_report"
        else:
            final_route = _choose_ecommerce_or_procurement(signal_strength, task_bias)

    if deterministic_hint in ALLOWED_MAIN_REPORT_ROUTES and validated.confidence < 0.70:
        blocked_routes.append(f"low_confidence_ai_route:{validated.ai_route}")
        final_route = deterministic_hint

    result = AIBusinessRoutingResult(
        selected_by_user=validated.selected_by_user,
        ai_route=validated.ai_route,
        final_route=final_route,
        confidence=validated.confidence,
        alternative_routes=list(dict.fromkeys(validated.alternative_routes)),
        reason=validated.reason,
        blocked_routes=list(dict.fromkeys(blocked_routes)),
        trace_id=validated.trace_id,
    )

    write_ai_business_routing_trace(output_dir, result)
    if result.confidence < 0.70:
        _write_uncertainty_report(output_dir, result)
    return result


__all__ = ["route_business_context_with_ai"]
