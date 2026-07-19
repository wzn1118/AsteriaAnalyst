from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Any

from .field_semantic_mapper import AIClientAdapter, AIRequiredButUnavailableError
from .metric_registry import get_metric_registry, known_role_names
from .schemas import (
    AIBusinessRoutingResult,
    AIFieldSemanticMappingResult,
    AIMetricDerivationPlan,
    AIMetricPlanItem,
)
from .trace_writer import write_ai_metric_derivation_plan_trace


class AIMetricDerivationPlannerValidationError(ValueError):
    pass


EVIDENCE_MAP = {
    "direct": "A_DIRECT",
    "derived": "B_DERIVED",
    "proxy": "C_PROXY",
    "diagnostic": "D_DIAGNOSTIC",
    "unavailable": "E_UNSUPPORTED",
}

FEASIBILITY_MAP = {
    "direct": "calculable",
    "derived": "calculable",
    "proxy": "proxy_only",
    "diagnostic": "diagnostic_only",
    "unavailable": "unsupported",
}

METRIC_MINING_DIRNAME = "metric_mining"
FORMULA_FIELD_FUNCTIONS = {
    "sum",
    "avg",
    "mean",
    "count",
    "distinct",
    "nunique",
    "countdistinct",
    "day",
    "week",
    "month",
    "min",
    "max",
}

ROLE_SYNONYM_MAP = {
    "inventory": "inventory_field",
    "stock": "inventory_field",
    "inventoryfield": "inventory_field",
    "stockfield": "inventory_field",
    "inventorybalance": "inventory_field",
    "stockbalance": "inventory_field",
    "inventoryonhand": "inventory_field",
    "stockonhand": "inventory_field",
    "availableinventory": "inventory_field",
    "endinginventory": "inventory_field",
    "beginninginventory": "inventory_field",
    "inventorysnapshot": "inventory_field",
    "inventoryposition": "inventory_field",
    "inventorylevel": "inventory_field",
    "purchaseprice": "purchase_price_field",
    "purchasepricefield": "purchase_price_field",
    "purchasecost": "purchase_price_field",
    "unitcost": "cost_field",
    "grossprofit": "cost_field",
    "salesamount": "amount_field",
    "revenuefield": "amount_field",
    "gmvfield": "amount_field",
}


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _normalize(value: Any) -> str:
    return "".join(ch for ch in _safe_text(value).lower() if ch.isalnum() or "\u4e00" <= ch <= "\u9fff")


def _canonical_role_name(role_name: Any) -> str:
    safe_role = _safe_text(role_name)
    if not safe_role:
        return ""
    normalized = _normalize(safe_role)
    if normalized in ROLE_SYNONYM_MAP:
        return ROLE_SYNONYM_MAP[normalized]
    if safe_role in known_role_names():
        return safe_role
    if normalized in known_role_names():
        return normalized
    return safe_role


def _formula_referenced_fields(formula: str, field_names: set[str]) -> set[str]:
    refs: set[str] = set()
    normalized_lookup = {_normalize(field): field for field in field_names}
    formula_text = _safe_text(formula)
    for field in field_names:
        if field and field in formula_text:
            refs.add(field)
    for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]*|[\u4e00-\u9fff][\u4e00-\u9fffA-Za-z0-9_]*", formula_text):
        normalized = _normalize(token)
        if normalized in FORMULA_FIELD_FUNCTIONS:
            continue
        if normalized in normalized_lookup:
            refs.add(normalized_lookup[normalized])
    return refs


def _write_json(path: Path, payload: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path.resolve())


def _semantic_roles(mapping_result: AIFieldSemanticMappingResult) -> dict[str, Any]:
    field_names = [mapping.field_name for mapping in mapping_result.field_mappings]
    canonical_to_fields: dict[str, list[str]] = {}
    business_roles: dict[str, list[str]] = {}
    granularity_hints: dict[str, list[str]] = {}
    for mapping in mapping_result.field_mappings:
        canonical_to_fields.setdefault(_safe_text(mapping.canonical_concept), []).append(mapping.field_name)
        business_roles.setdefault(_safe_text(mapping.business_role), []).append(mapping.field_name)
        granularity_hints.setdefault(_safe_text(mapping.granularity_hint), []).append(mapping.field_name)
    return {
        "field_names": field_names,
        "canonical_to_fields": canonical_to_fields,
        "business_roles": business_roles,
        "granularity_hints": granularity_hints,
        "object_grain": _safe_text(mapping_result.object_grain),
        "time_grain": _safe_text(mapping_result.time_grain),
        "uncertain_fields": list(mapping_result.uncertain_fields),
    }


def _time_window_info(dataframe_profile: dict[str, Any], time_grain: str) -> dict[str, Any]:
    profile = dataframe_profile or {}
    time_profile = profile.get("time_profile") or {}
    distinct_points = int(
        time_profile.get("distinct_time_points")
        or profile.get("distinct_time_points")
        or 0
    )
    window_days = float(time_profile.get("window_days") or profile.get("window_days") or 0.0)
    return {
        "time_grain": time_grain,
        "distinct_time_points": distinct_points,
        "window_days": window_days,
        "retention_sufficient": distinct_points >= 7 or window_days >= 7,
        "trend_sufficient": distinct_points >= 2,
    }


def _role_aliases(canonical_concept: str, business_role: str) -> set[str]:
    aliases: set[str] = set()
    concept = _normalize(canonical_concept)
    role = _normalize(business_role)
    if any(token in concept for token in ["userid", "uid"]):
        aliases.update({"user_key", "object_key"})
    if any(token in concept for token in ["orderid"]):
        aliases.update({"order_key", "object_key"})
    if any(token in concept for token in ["skuid"]):
        aliases.update({"sku_key", "product_key", "object_key"})
    if any(token in concept for token in ["productid"]):
        aliases.update({"product_key", "object_key"})
    if "category" in concept:
        aliases.update({"category_key", "object_key"})
    if "supplierid" in concept:
        aliases.update({"supplier_key", "object_key"})
    if "sellerid" in concept:
        aliases.update({"seller_key", "object_key"})
    if concept in {"revenue", "gmv"} or "amount" in concept:
        aliases.add("amount_field")
        aliases.add("numeric_measure")
    if concept in {"quantity"} or "qty" in concept:
        aliases.add("quantity_field")
        aliases.add("numeric_measure")
    if concept in {"cost"}:
        aliases.add("cost_field")
        aliases.add("numeric_measure")
    if concept in {"price"}:
        aliases.add("price_field")
        aliases.add("numeric_measure")
    if concept in {"inventory", "stock"}:
        aliases.add("inventory_field")
        aliases.add("numeric_measure")
    if concept in {"rating"}:
        aliases.add("rating_field")
        aliases.add("numeric_measure")
    if concept in {"reviewscore"}:
        aliases.add("review_score_field")
        aliases.add("numeric_measure")
    if concept in {"commenttext"}:
        aliases.add("text_feedback_field")
    if concept in {"impression"}:
        aliases.add("impression_field")
        aliases.add("numeric_measure")
    if concept in {"click"}:
        aliases.add("click_field")
        aliases.add("numeric_measure")
    if concept in {"conversion"}:
        aliases.add("conversion_field")
        aliases.add("numeric_measure")
    if concept in {"eventtype"}:
        aliases.add("event_field")
    if concept in {"channel"}:
        aliases.add("channel_key")
        aliases.add("object_key")
    if concept in {"campaign"}:
        aliases.add("campaign_key")
        aliases.add("object_key")
    if concept in {"sessionid"}:
        aliases.add("session_key")
        aliases.add("object_key")
    if concept in {"date"}:
        aliases.add("time_key")
    if "content" in concept:
        aliases.update({"content_key", "object_key"})
    if "region" in concept:
        aliases.update({"region_key", "object_key"})
    if "customertype" in concept or "customertype" in concept:
        aliases.update({"customer_type_key", "object_key"})

    if "object" in role or "dimension" in role:
        aliases.add("object_key")
    if "time" in role:
        aliases.add("time_key")
    if "amount" in role or "revenue" in role:
        aliases.add("amount_field")
    if "quantity" in role or "count" in role:
        aliases.add("quantity_field")
    if "cost" in role:
        aliases.add("cost_field")
    if "price" in role:
        aliases.add("price_field")
    if "inventory" in role or "stock" in role:
        aliases.add("inventory_field")
    if "rating" in role:
        aliases.add("rating_field")
    if "text" in role or "comment" in role or "feedback" in role:
        aliases.add("text_feedback_field")
    if "event" in role or "step" in role:
        aliases.add("event_field")
    if "status" in role:
        aliases.add("status_field")
    if "benchmark" in role:
        aliases.add("benchmark_field")
    return aliases


def _profile_field_names(dataframe_profile: dict[str, Any] | None) -> set[str]:
    profile = dataframe_profile or {}
    names: set[str] = set()
    for key in ["field_names", "columns"]:
        value = profile.get(key)
        if isinstance(value, list):
            names.update(str(item.get("name") if isinstance(item, dict) else item) for item in value)
    for item in profile.get("column_summaries") or []:
        if isinstance(item, dict) and item.get("name"):
            names.add(str(item["name"]))
    return {name for name in names if name}


def _fallback_role_aliases_for_field_name(field_name: str) -> set[str]:
    normalized = _normalize(field_name)
    aliases: set[str] = set()
    if any(token in normalized for token in ["userid", "customerid", "memberid", "visitorid"]):
        aliases.update({"user_key", "object_key"})
    if "orderid" in normalized:
        aliases.update({"order_key", "object_key"})
    if "sku" in normalized:
        aliases.update({"sku_key", "product_key", "object_key"})
    if "product" in normalized:
        aliases.update({"product_key", "object_key"})
    if "category" in normalized or "cate" in normalized:
        aliases.update({"category_key", "object_key"})
    if "seller" in normalized or "supplier" in normalized:
        aliases.update({"seller_key", "supplier_key", "object_key"})
    if "channel" in normalized:
        aliases.update({"channel_key", "object_key"})
    if "campaign" in normalized or "activity" in normalized:
        aliases.update({"campaign_key", "object_key"})
    if "date" in normalized or "time" in normalized or "timestamp" in normalized:
        aliases.add("time_key")
    if "gmv" in normalized or "revenue" in normalized or "salesamount" in normalized or "amount" in normalized:
        aliases.update({"amount_field", "numeric_measure"})
    if "qty" in normalized or "quantity" in normalized or "units" in normalized:
        aliases.update({"quantity_field", "numeric_measure"})
    if "cost" in normalized or "freight" in normalized or "spend" in normalized:
        aliases.update({"cost_field", "numeric_measure"})
        if "spend" in normalized:
            aliases.add("spend_field")
    if "price" in normalized:
        aliases.update({"price_field", "numeric_measure"})
    if "stock" in normalized or "inventory" in normalized:
        aliases.update({"inventory_field", "numeric_measure"})
    if "rating" in normalized or "reviewscore" in normalized or normalized.endswith("score"):
        aliases.update({"rating_field", "review_score_field", "numeric_measure"})
    if "reviewtext" in normalized or "comment" in normalized or "text" in normalized:
        aliases.add("text_feedback_field")
    if "late" in normalized or "delay" in normalized or "status" in normalized or "delivered" in normalized:
        aliases.add("status_field")
        if "day" in normalized or "delay" in normalized or "late" in normalized:
            aliases.add("numeric_measure")
    if "impression" in normalized or "exposure" in normalized:
        aliases.update({"impression_field", "numeric_measure"})
    if "click" in normalized:
        aliases.update({"click_field", "numeric_measure"})
    if "conversion" in normalized or "purchase" in normalized:
        aliases.update({"conversion_field", "numeric_measure"})
    if "event" in normalized or "action" in normalized:
        aliases.add("event_field")
    return aliases


def _known_field_names(
    mapping_result: AIFieldSemanticMappingResult,
    dataframe_profile: dict[str, Any] | None = None,
) -> set[str]:
    field_names = {mapping.field_name for mapping in mapping_result.field_mappings}
    field_names.update(str(field) for field in mapping_result.uncertain_fields if str(field).strip())
    field_names.update(_profile_field_names(dataframe_profile))
    return field_names


def _available_role_map(
    mapping_result: AIFieldSemanticMappingResult,
    dataframe_profile: dict[str, Any] | None = None,
) -> dict[str, list[str]]:
    roles: dict[str, list[str]] = {}
    mapped_fields: set[str] = set()
    for mapping in mapping_result.field_mappings:
        mapped_fields.add(mapping.field_name)
        for alias in _role_aliases(mapping.canonical_concept, mapping.business_role):
            roles.setdefault(alias, [])
            if mapping.field_name not in roles[alias]:
                roles[alias].append(mapping.field_name)
        roles.setdefault(_safe_text(mapping.canonical_concept), [])
        if mapping.field_name not in roles[_safe_text(mapping.canonical_concept)]:
            roles[_safe_text(mapping.canonical_concept)].append(mapping.field_name)
        roles.setdefault(_safe_text(mapping.business_role), [])
        if mapping.field_name not in roles[_safe_text(mapping.business_role)]:
            roles[_safe_text(mapping.business_role)].append(mapping.field_name)
    for field_name in sorted(_known_field_names(mapping_result, dataframe_profile) - mapped_fields):
        for alias in _fallback_role_aliases_for_field_name(field_name):
            roles.setdefault(alias, [])
            if field_name not in roles[alias]:
                roles[alias].append(field_name)
    return roles


def _field_alias_map(mapping_result: AIFieldSemanticMappingResult) -> dict[str, set[str]]:
    aliases: dict[str, set[str]] = {}
    for mapping in mapping_result.field_mappings:
        field_aliases = set(_role_aliases(mapping.canonical_concept, mapping.business_role))
        field_aliases.add(_safe_text(mapping.canonical_concept))
        field_aliases.add(_safe_text(mapping.business_role))
        aliases[mapping.field_name] = field_aliases
    return aliases


def _match_roles(role_map: dict[str, list[str]], required_roles: list[str]) -> tuple[list[str], list[str]]:
    matched_fields: list[str] = []
    missing_roles: list[str] = []
    for role in required_roles:
        canonical_role = _canonical_role_name(role)
        if role_map.get(canonical_role):
            matched_fields.extend(role_map[canonical_role])
        else:
            missing_roles.append(canonical_role)
    return list(dict.fromkeys(matched_fields)), missing_roles


def _is_orderable_step(role_map: dict[str, list[str]]) -> bool:
    return bool(role_map.get("step_key")) or any(
        key in role_map for key in ["step_order", "event_order", "funnel_step"]
    )


def build_metric_opportunity_graph(
    *,
    semantic_mapping_result: AIFieldSemanticMappingResult,
    routing_result: AIBusinessRoutingResult,
    dataframe_profile: dict[str, Any] | None,
    user_task_description: str,
    available_field_roles: list[str] | dict[str, Any] | None,
    object_grain: str,
    time_grain: str,
    business_route: str,
    existing_metric_registry: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    role_map = _available_role_map(semantic_mapping_result, dataframe_profile)
    role_hints = available_field_roles if isinstance(available_field_roles, list) else list((available_field_roles or {}).keys())
    time_info = _time_window_info(dataframe_profile or {}, time_grain)
    registry = existing_metric_registry or get_metric_registry()

    nodes: list[dict[str, Any]] = []
    for item in registry:
        if business_route not in item.get("allowed_domains", []):
            continue
        matched_patterns: list[dict[str, Any]] = []
        best_feasibility = "unsupported"
        for pattern in item.get("required_role_patterns", []):
            matched_fields, missing_roles = _match_roles(role_map, pattern)
            if not missing_roles:
                feasibility = "calculable"
            elif matched_fields:
                feasibility = "proxy_only" if item["metric_family"] not in {"retention_metric", "unavailable_metric"} else "diagnostic_only"
            else:
                feasibility = "unsupported"

            if item["metric_family"] == "retention_metric" and feasibility == "calculable" and not time_info["retention_sufficient"]:
                feasibility = "diagnostic_only"
            if item["metric_family"] == "trend_metric" and feasibility == "calculable" and not time_info["trend_sufficient"]:
                feasibility = "diagnostic_only"
            if item["metric_family"] == "conversion_metric" and "event_field" in pattern and "user_key" in pattern and not _is_orderable_step(role_map):
                feasibility = "diagnostic_only"

            matched_patterns.append(
                {
                    "required_roles": pattern,
                    "matched_fields": matched_fields,
                    "missing_roles": missing_roles,
                    "feasibility": feasibility,
                }
            )
            order = {"calculable": 4, "proxy_only": 3, "diagnostic_only": 2, "unsupported": 1}
            if order[feasibility] > order[best_feasibility]:
                best_feasibility = feasibility

        nodes.append(
            {
                "metric_family": item["metric_family"],
                "candidate_metric_ids": list(item.get("candidate_metric_ids") or []),
                "required_role_patterns": list(item.get("required_role_patterns") or []),
                "optional_role_patterns": list(item.get("optional_role_patterns") or []),
                "forbidden_without_roles": list(item.get("forbidden_without_roles") or []),
                "allowed_domains": list(item.get("allowed_domains") or []),
                "matched_patterns": matched_patterns,
                "best_feasibility": best_feasibility,
                "calculation_executor": item.get("calculation_executor", ""),
                "downstream_usage_rules": list(item.get("downstream_usage_rules") or []),
                "evidence_rules": dict(item.get("evidence_rules") or {}),
            }
        )

    return {
        "business_route": business_route,
        "user_task_description": user_task_description,
        "object_grain": object_grain,
        "time_grain": time_grain,
        "route_confidence": routing_result.confidence,
        "alternative_routes": list(routing_result.alternative_routes),
        "role_hints": sorted(set(role_hints)),
        "available_roles": sorted(role_map.keys()),
        "time_window_info": time_info,
        "dataframe_profile": dataframe_profile or {},
        "nodes": nodes,
    }


def _build_system_prompt() -> str:
    return (
        "You are AIMetricDerivationPlanner for AsteriaAnalyst. "
        "You must read AIFieldSemanticMappingResult, AIBusinessRoutingResult, dataframe profile, available role combinations, "
        "metric opportunity graph, and registry seed, then generate a dynamic metric derivation plan. "
        "Do not limit yourself to fixed metric names. "
        "You may generate new metric ids and names when the business context supports them. "
        "Do not invent final numeric values. "
        "Do not reference fields that do not exist. "
        "Do not mark proxy metrics as direct. "
        "Do not mark diagnostic or unavailable metrics as calculable. "
        "For every direct, derived, or proxy metric, formula_or_logic is mandatory and must be executable by a deterministic pandas executor. "
        "Use explicit source field names from matched_fields in formula_or_logic. "
        "Prefer formula patterns such as SUM(field), GROUP BY dimension; SUM(field), "
        "SUM(field) by dimension / SUM(field) overall, GROUP BY date; COUNT(DISTINCT user_id), "
        "SUM(click) / SUM(impression), SUM(conversion) / SUM(click), "
        "(SUM(revenue) - SUM(cost)) / SUM(revenue), and COUNT users with more than one active date. "
        "Do not put formulas on unavailable metrics. "
        "Return JSON only matching the requested schema."
    )


def _compact_semantic_mapping_for_prompt(
    semantic_mapping_result: AIFieldSemanticMappingResult,
) -> dict[str, Any]:
    return {
        "inferred_business_context": semantic_mapping_result.inferred_business_context,
        "object_grain": semantic_mapping_result.object_grain,
        "time_grain": semantic_mapping_result.time_grain,
        "field_mappings": [
            {
                "field_name": item.field_name,
                "canonical_concept": item.canonical_concept,
                "business_role": item.business_role,
                "granularity_hint": item.granularity_hint,
                "confidence": item.confidence,
            }
            for item in semantic_mapping_result.field_mappings
        ],
        "uncertain_fields": list(semantic_mapping_result.uncertain_fields),
        "trace_id": semantic_mapping_result.trace_id,
    }


def _compact_metric_registry_for_prompt(metric_registry: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in metric_registry[:40]:
        rows.append(
            {
                "metric_family": item.get("metric_family", ""),
                "candidate_metric_ids": list(item.get("candidate_metric_ids") or [])[:6],
                "required_role_patterns": list(item.get("required_role_patterns") or []),
                "forbidden_without_roles": list(item.get("forbidden_without_roles") or []),
                "allowed_domains": list(item.get("allowed_domains") or []),
                "downstream_usage_rules": list(item.get("downstream_usage_rules") or [])[:6],
            }
        )
    return rows


def _compact_metric_opportunity_graph_for_prompt(metric_opportunity_graph: dict[str, Any]) -> dict[str, Any]:
    nodes = []
    for item in metric_opportunity_graph.get("nodes") or []:
        if str(item.get("best_feasibility") or "") == "unsupported":
            continue
        nodes.append(
            {
                "metric_family": item.get("metric_family", ""),
                "candidate_metric_ids": list(item.get("candidate_metric_ids") or [])[:6],
                "best_feasibility": item.get("best_feasibility", ""),
                "matched_patterns": list(item.get("matched_patterns") or [])[:4],
                "forbidden_without_roles": list(item.get("forbidden_without_roles") or []),
                "downstream_usage_rules": list(item.get("downstream_usage_rules") or [])[:6],
            }
        )
    return {
        "business_route": metric_opportunity_graph.get("business_route", ""),
        "object_grain": metric_opportunity_graph.get("object_grain", ""),
        "time_grain": metric_opportunity_graph.get("time_grain", ""),
        "route_confidence": metric_opportunity_graph.get("route_confidence", ""),
        "alternative_routes": list(metric_opportunity_graph.get("alternative_routes") or [])[:4],
        "available_roles": list(metric_opportunity_graph.get("available_roles") or []),
        "time_window_info": metric_opportunity_graph.get("time_window_info") or {},
        "nodes": nodes[:24],
    }


def _build_user_payload(
    *,
    semantic_mapping_result: AIFieldSemanticMappingResult,
    routing_result: AIBusinessRoutingResult,
    dataframe_profile: dict[str, Any] | None,
    user_task_description: str,
    available_field_roles: list[str] | dict[str, Any] | None,
    object_grain: str,
    time_grain: str,
    business_route: str,
    metric_registry: list[dict[str, Any]],
    metric_opportunity_graph: dict[str, Any],
    user_selected_analysis_depth: str | None,
) -> dict[str, Any]:
    return {
        "task": "ai_metric_derivation_planner",
        "semantic_mapping_result": _compact_semantic_mapping_for_prompt(semantic_mapping_result),
        "routing_result": routing_result.model_dump(mode="json"),
        "dataframe_profile": dataframe_profile or {},
        "user_task_description": user_task_description,
        "available_field_roles": available_field_roles or [],
        "object_grain": object_grain,
        "time_grain": time_grain,
        "business_route": business_route,
        "metric_registry_seed": _compact_metric_registry_for_prompt(metric_registry),
        "metric_opportunity_graph": _compact_metric_opportunity_graph_for_prompt(metric_opportunity_graph),
        "user_selected_analysis_depth": user_selected_analysis_depth or "",
        "required_output_schema": {
            "available_metrics": ["string"],
            "unavailable_metrics": ["string"],
            "proxy_metrics": ["string"],
            "diagnostic_questions": ["string"],
            "metric_plans": [
                {
                    "metric_id": "string",
                    "metric_name_cn": "string",
                    "metric_name_en": "string",
                    "metric_family": "string",
                    "business_domain": "string",
                    "business_object": "string",
                    "metric_type": "direct|derived|proxy|diagnostic|unavailable",
                    "required_field_roles": ["string"],
                    "matched_fields": ["string"],
                    "missing_fields": ["string"],
                    "formula_or_logic": "required executable formula for direct/derived/proxy; empty only for unavailable",
                    "grain": "string",
                    "time_window_requirement": "string",
                    "minimum_data_requirement": "string",
                    "evidence_level": "A_DIRECT|B_DERIVED|C_PROXY|D_DIAGNOSTIC|E_UNSUPPORTED",
                    "confidence": "float 0-1",
                    "calculation_feasibility": "calculable|proxy_only|diagnostic_only|unsupported",
                    "business_question_answered": "string",
                    "allowed_downstream_usage": ["string"],
                    "forbidden_downstream_usage": ["string"],
                    "caveat": "string",
                    "reason": "string",
                }
            ],
            "provider": "string",
            "model": "string",
            "trace_id": "string",
        },
    }


def _validate_metric_plan_item(
    *,
    item: AIMetricPlanItem,
    field_names: set[str],
    role_map: dict[str, list[str]],
    time_info: dict[str, Any],
) -> None:
    for field in item.matched_fields:
        if field not in field_names:
            raise AIMetricDerivationPlannerValidationError(f"matched_fields unknown field: {field}")
    required_roles = [_canonical_role_name(role) for role in item.required_field_roles]
    for role in required_roles:
        if role not in known_role_names() and role not in role_map:
            raise AIMetricDerivationPlannerValidationError(f"required_field_roles unsupported role: {role}")
    if item.metric_type in {"direct", "derived"}:
        missing_roles = [role for role in required_roles if role not in role_map]
        if missing_roles:
            raise AIMetricDerivationPlannerValidationError(
                f"{item.metric_id} calculable metric missing required roles: {missing_roles}"
            )
        if item.missing_fields:
            raise AIMetricDerivationPlannerValidationError(
                f"{item.metric_id} calculable metric cannot keep missing_fields: {item.missing_fields}"
            )
    if item.metric_type in {"direct", "derived", "proxy"} and not _safe_text(item.formula_or_logic):
        raise AIMetricDerivationPlannerValidationError(f"{item.metric_id} requires executable formula_or_logic")
    formula_refs = _formula_referenced_fields(item.formula_or_logic, field_names)
    unknown_formula_refs = sorted(field for field in formula_refs if field not in field_names)
    if unknown_formula_refs:
        raise AIMetricDerivationPlannerValidationError(
            f"{item.metric_id} formula references unknown fields: {unknown_formula_refs}"
        )
    if item.metric_type in {"direct", "derived", "proxy"} and formula_refs:
        matched_fields = set(item.matched_fields)
        missing_from_matched = sorted(field for field in formula_refs if field not in matched_fields)
        if missing_from_matched:
            raise AIMetricDerivationPlannerValidationError(
                f"{item.metric_id} formula fields must be listed in matched_fields: {missing_from_matched}"
            )

    expected_evidence = EVIDENCE_MAP[item.metric_type]
    if item.evidence_level != expected_evidence:
        raise AIMetricDerivationPlannerValidationError(
            f"{item.metric_id} metric_type/evidence_level mismatch: {item.metric_type} vs {item.evidence_level}"
        )
    expected_feasibility = FEASIBILITY_MAP[item.metric_type]
    if item.calculation_feasibility != expected_feasibility:
        raise AIMetricDerivationPlannerValidationError(
            f"{item.metric_id} metric_type/calculation_feasibility mismatch: {item.metric_type} vs {item.calculation_feasibility}"
        )
    if item.metric_type == "unavailable" and _safe_text(item.formula_or_logic):
        raise AIMetricDerivationPlannerValidationError(f"{item.metric_id} unavailable metric cannot contain formula")
    if item.metric_type == "diagnostic" and item.calculation_feasibility == "calculable":
        raise AIMetricDerivationPlannerValidationError(f"{item.metric_id} diagnostic metric cannot be calculable")
    if item.metric_type in {"proxy", "diagnostic", "unavailable"}:
        if not _safe_text(item.caveat):
            raise AIMetricDerivationPlannerValidationError(f"{item.metric_id} requires caveat")
        if not item.forbidden_downstream_usage:
            raise AIMetricDerivationPlannerValidationError(f"{item.metric_id} requires forbidden_downstream_usage")
    if not item.required_field_roles:
        raise AIMetricDerivationPlannerValidationError(f"{item.metric_id} missing required_field_roles")

    roles = set(required_roles)
    if item.metric_family == "profitability_metric" and item.metric_type in {"direct", "derived"} and "cost_field" not in roles:
        raise AIMetricDerivationPlannerValidationError(f"{item.metric_id} profitability metric requires cost_field")
    if item.metric_family == "inventory_metric" and item.metric_type in {"direct", "derived"} and "inventory_field" not in roles:
        raise AIMetricDerivationPlannerValidationError(f"{item.metric_id} inventory metric requires inventory_field")
    if item.metric_family == "retention_metric" and item.metric_type in {"direct", "derived"} and not time_info.get("retention_sufficient"):
        raise AIMetricDerivationPlannerValidationError(f"{item.metric_id} retention requires sufficient time window")
    if item.metric_family == "conversion_metric" and "funnel" in _normalize(item.metric_id + " " + item.metric_name_en + " " + item.metric_name_cn):
        if item.metric_type in {"direct", "derived"} and "step_key" not in roles:
            raise AIMetricDerivationPlannerValidationError(f"{item.metric_id} funnel metric requires orderable step")


def _validate_metric_plan(
    plan: AIMetricDerivationPlan,
    *,
    semantic_mapping_result: AIFieldSemanticMappingResult,
    metric_opportunity_graph: dict[str, Any],
) -> AIMetricDerivationPlan:
    dataframe_profile = metric_opportunity_graph.get("dataframe_profile") or {}
    field_names = _known_field_names(semantic_mapping_result, dataframe_profile)
    role_map = _available_role_map(semantic_mapping_result, dataframe_profile)
    time_info = metric_opportunity_graph.get("time_window_info") or {}

    for item in plan.metric_plans:
        _validate_metric_plan_item(
            item=item,
            field_names=field_names,
            role_map=role_map,
            time_info=time_info,
        )

    return plan


def _repair_metric_plan_for_validation(
    plan: AIMetricDerivationPlan,
    *,
    semantic_mapping_result: AIFieldSemanticMappingResult,
    dataframe_profile: dict[str, Any] | None = None,
) -> AIMetricDerivationPlan:
    payload = plan.model_dump(mode="json")
    repaired = False
    field_aliases = _field_alias_map(semantic_mapping_result)
    role_map = _available_role_map(semantic_mapping_result, dataframe_profile)
    field_names = _known_field_names(semantic_mapping_result, dataframe_profile)
    for item in payload.get("metric_plans", []):
        metric_type = _safe_text(item.get("metric_type"))
        required_roles = list(item.get("required_field_roles") or [])
        normalized_required_roles: list[str] = []
        for role_name in required_roles:
            original_role = _safe_text(role_name)
            safe_role = _canonical_role_name(role_name)
            if safe_role != original_role:
                repaired = True
            if safe_role in known_role_names():
                normalized_required_roles.append(safe_role)
                continue
            extracted_roles = [
                known_role
                for known_role in sorted(known_role_names(), key=len, reverse=True)
                if known_role in safe_role
            ]
            if extracted_roles:
                if " or " in safe_role or "/" in safe_role:
                    available = [role for role in extracted_roles if role_map.get(role)]
                    normalized_required_roles.extend(available[:1] or extracted_roles[:1])
                else:
                    normalized_required_roles.extend(extracted_roles)
                repaired = True
                continue
            normalized_required_roles.append(safe_role)
        required_roles = list(dict.fromkeys(normalized_required_roles))
        matched_fields = list(item.get("matched_fields") or [])
        matched_aliases: set[str] = set()
        for field_name in matched_fields:
            matched_aliases.update(field_aliases.get(field_name, set()))
            matched_aliases.update(_fallback_role_aliases_for_field_name(field_name))
        metric_family = _safe_text(item.get("metric_family"))
        if metric_family == "profitability_metric":
            for role_name in ("amount_field", "cost_field"):
                if role_name in matched_aliases and role_name not in required_roles:
                    required_roles.append(role_name)
                    repaired = True
        if metric_family == "inventory_metric":
            for role_name in ("inventory_field", "quantity_field"):
                if role_name in matched_aliases and role_name not in required_roles:
                    required_roles.append(role_name)
                    repaired = True
        if metric_family == "retention_metric":
            for role_name in ("user_key", "time_key"):
                if role_name in matched_aliases and role_name not in required_roles:
                    required_roles.append(role_name)
                    repaired = True
        if metric_family == "conversion_metric":
            for role_name in ("event_field", "user_key", "step_key"):
                if role_name in matched_aliases and role_name not in required_roles:
                    required_roles.append(role_name)
                    repaired = True
        item["required_field_roles"] = required_roles
        formula_refs = _formula_referenced_fields(_safe_text(item.get("formula_or_logic")), field_names)
        if metric_type in {"direct", "derived", "proxy"} and formula_refs:
            matched_fields = list(item.get("matched_fields") or [])
            for field_name in sorted(formula_refs):
                if field_name not in matched_fields:
                    matched_fields.append(field_name)
                    repaired = True
            item["matched_fields"] = matched_fields
        expected_evidence = EVIDENCE_MAP.get(metric_type)
        if metric_type in {"proxy", "diagnostic", "unavailable"} and expected_evidence and item.get("evidence_level") != expected_evidence:
            item["evidence_level"] = expected_evidence
            repaired = True
        expected_feasibility = FEASIBILITY_MAP.get(metric_type)
        if metric_type in {"proxy", "diagnostic", "unavailable"} and expected_feasibility and item.get("calculation_feasibility") != expected_feasibility:
            item["calculation_feasibility"] = expected_feasibility
            repaired = True
        if metric_type == "unavailable" and _safe_text(item.get("formula_or_logic")):
            item["formula_or_logic"] = ""
            repaired = True
        if metric_type == "diagnostic" and item.get("calculation_feasibility") == "calculable":
            item["calculation_feasibility"] = "diagnostic_only"
            repaired = True
        if metric_type in {"proxy", "diagnostic", "unavailable"} and not _safe_text(item.get("caveat")):
            item["caveat"] = "当前仅适合作为边界说明或后续验证线索，不能直接写成管理层强结论。"
            repaired = True
        if metric_type in {"proxy", "diagnostic", "unavailable"} and not (item.get("forbidden_downstream_usage") or []):
            item["forbidden_downstream_usage"] = ["formal_management_conclusion"]
            repaired = True
    if not repaired:
        return plan
    return AIMetricDerivationPlan.model_validate(payload)


def _semantic_metric_plan_artifact(plan: AIMetricDerivationPlan) -> dict[str, Any]:
    return {
        "available_metric_families": sorted({item.metric_family for item in plan.metric_plans if item.metric_type in {"direct", "derived"}}),
        "calculated_candidate_metrics": [item.metric_id for item in plan.metric_plans if item.metric_type in {"direct", "derived"}],
        "proxy_candidate_metrics": [item.metric_id for item in plan.metric_plans if item.metric_type == "proxy"],
        "diagnostic_candidate_metrics": [item.metric_id for item in plan.metric_plans if item.metric_type == "diagnostic"],
        "unavailable_metrics": [item.metric_id for item in plan.metric_plans if item.metric_type == "unavailable"],
        "metric_plans": [item.model_dump(mode="json") for item in plan.metric_plans],
    }


def _unavailable_metric_reasons(plan: AIMetricDerivationPlan) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for item in plan.metric_plans:
        if item.metric_type not in {"diagnostic", "unavailable", "proxy"}:
            continue
        rows.append(
            {
                "metric_id": item.metric_id,
                "metric_name_cn": item.metric_name_cn,
                "want_to_answer": item.business_question_answered,
                "missing_fields": item.missing_fields,
                "weak_judgement_possible": item.metric_type in {"proxy", "diagnostic"},
                "forbidden_management_conclusions": item.forbidden_downstream_usage,
                "next_required_data": item.missing_fields,
                "reason": item.reason,
                "calculation_feasibility": item.calculation_feasibility,
            }
        )
    return {"rows": rows}


def _metric_mining_dir(output_dir: str | Path) -> Path:
    path = Path(output_dir) / "outputs" / METRIC_MINING_DIRNAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def plan_metrics_with_ai(
    *,
    output_dir: str | Path,
    semantic_mapping_result: AIFieldSemanticMappingResult,
    routing_result: AIBusinessRoutingResult,
    dataframe_profile: dict[str, Any] | None,
    user_task_description: str,
    available_field_roles: list[str] | dict[str, Any] | None,
    object_grain: str,
    time_grain: str,
    business_route: str,
    existing_metric_registry: list[dict[str, Any]] | None = None,
    user_selected_analysis_depth: str | None = None,
    ai_client: AIClientAdapter | None = None,
) -> AIMetricDerivationPlan:
    registry = existing_metric_registry or get_metric_registry()
    opportunity_graph = build_metric_opportunity_graph(
        semantic_mapping_result=semantic_mapping_result,
        routing_result=routing_result,
        dataframe_profile=dataframe_profile,
        user_task_description=user_task_description,
        available_field_roles=available_field_roles,
        object_grain=object_grain or semantic_mapping_result.object_grain,
        time_grain=time_grain or semantic_mapping_result.time_grain,
        business_route=business_route or routing_result.final_route,
        existing_metric_registry=registry,
    )
    client = ai_client or AIClientAdapter()
    raw = client.complete_json(
        system_prompt=_build_system_prompt(),
        user_payload=_build_user_payload(
            semantic_mapping_result=semantic_mapping_result,
            routing_result=routing_result,
            dataframe_profile=dataframe_profile,
            user_task_description=user_task_description,
            available_field_roles=available_field_roles,
            object_grain=object_grain or semantic_mapping_result.object_grain,
            time_grain=time_grain or semantic_mapping_result.time_grain,
            business_route=business_route or routing_result.final_route,
            metric_registry=registry,
            metric_opportunity_graph=opportunity_graph,
            user_selected_analysis_depth=user_selected_analysis_depth,
        ),
    )

    if raw.get("__ai_unavailable__") or raw.get("live_available") is False or raw.get("runtime_state") == "fallback":
        raise AIRequiredButUnavailableError(_safe_text(raw.get("reason") or raw.get("fallback_reason") or "AI unavailable"))

    payload = dict(raw)
    payload["provider"] = _safe_text(payload.get("provider") or payload.get("provider_label") or "OpenAI Codex API")
    payload["model"] = _safe_text(payload.get("model") or "unknown")
    payload["trace_id"] = _safe_text(payload.get("trace_id") or f"ai-metric-plan-{uuid.uuid4().hex[:12]}")

    try:
        plan = AIMetricDerivationPlan.model_validate(payload)
    except Exception as exc:
        raise AIMetricDerivationPlannerValidationError(f"schema validation failed: {exc}") from exc

    repaired_plan = _repair_metric_plan_for_validation(
        plan,
        semantic_mapping_result=semantic_mapping_result,
        dataframe_profile=dataframe_profile,
    )
    validated_plan = _validate_metric_plan(
        repaired_plan,
        semantic_mapping_result=semantic_mapping_result,
        metric_opportunity_graph=opportunity_graph,
    )

    write_ai_metric_derivation_plan_trace(output_dir, validated_plan)
    metric_dir = _metric_mining_dir(output_dir)
    _write_json(metric_dir / "semantic_metric_plan.json", _semantic_metric_plan_artifact(validated_plan))
    _write_json(metric_dir / "metric_opportunity_graph.json", opportunity_graph)
    _write_json(metric_dir / "unavailable_metric_reasons.json", _unavailable_metric_reasons(validated_plan))
    return validated_plan


__all__ = [
    "AIMetricDerivationPlannerValidationError",
    "build_metric_opportunity_graph",
    "plan_metrics_with_ai",
]
