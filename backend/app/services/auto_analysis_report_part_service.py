from __future__ import annotations

from typing import Any

from app.services.analysis_service import SUPPORTED_ANALYSIS_TYPES


STATISTICAL_OUTPUT_VARIANTS = ("text", "table", "data", "chart", "image_spec", "report_section")


def _zh(value: str) -> str:
    return value.encode("ascii").decode("unicode_escape")


Z = {
    "executive_summary": _zh(r"\u7ba1\u7406\u6458\u8981"),
    "chapter": _zh(r"\u5206\u6790\u7ae0\u8282"),
    "visual_gallery": _zh(r"\u56fe\u7ec4\u4e0e\u7ba1\u7406\u89e3\u8bfb"),
    "appendix": _zh(r"\u5206\u6790\u9644\u5f55"),
    "method_note": _zh(r"\u65b9\u6cd5\u8bf4\u660e"),
    "field_glossary": _zh(r"\u5b57\u6bb5\u89e3\u91ca"),
    "action_plan": _zh(r"\u884c\u52a8\u5efa\u8bae"),
    "evidence_index": _zh(r"\u8bc1\u636e\u7d22\u5f15"),
    "current_dataset": _zh(r"\u5f53\u524d\u6570\u636e\u96c6"),
    "current_sheet": _zh(r"\u5f53\u524d\u5de5\u4f5c\u8868"),
    "unknown": _zh(r"\u672a\u8bc6\u522b"),
    "route_table": _zh(r"\u65b9\u6cd5\u8def\u7531\u8bc1\u636e"),
    "pre_method_audit_table": _zh(r"\u65b9\u6cd5\u9009\u62e9\u524d\u7f6e\u5ba1\u8ba1"),
    "method_route_evidence_table": _zh(r"\u65b9\u6cd5\u8def\u7531\u8bc1\u636e\u660e\u7ec6"),
    "quadrant_action_table": _zh(r"\u8c61\u9650\u884c\u52a8\u5efa\u8bae"),
    "evidence_table": _zh(r"\u8bc1\u636e\u7d22\u5f15"),
    "field_relationship_graph": _zh(r"\u5b57\u6bb5\u5173\u7cfb\u56fe\u8c31"),
    "field_semantic_route_plan": _zh(r"\u5b57\u6bb5\u8bed\u4e49\u8def\u7531\u7b56\u7565"),
    "chapter_narrative": _zh(r"\u672c\u7ae0\u8282\u6309\u201c\u5b57\u6bb5\u8bed\u4e49 -> \u6d3e\u751f\u5b57\u6bb5 -> \u65b9\u6cd5\u8def\u7531 -> \u56fe\u8868\u89e3\u91ca\u201d\u7684\u987a\u5e8f\u7ec4\u7ec7\uff0c\u53ef\u76f4\u63a5\u5d4c\u5165\u957f\u62a5\u544a\u6b63\u6587\u3002"),
    "visual_narrative": _zh(r"\u56fe\u7ec4\u4f18\u5148\u8986\u76d6\u6c14\u6ce1\u3001\u8c61\u9650\u3001\u6563\u70b9\u3001\u5206\u5e03\u3001\u76f8\u5173\u77e9\u9635\u3001\u65f6\u95f4\u5e8f\u5217\u3001\u9884\u6d4b\u3001\u5206\u7fa4\u548c\u5f02\u5e38\u68c0\u6d4b\uff0c\u5e76\u4e3a\u6bcf\u5f20\u56fe\u8865\u5145\u7ba1\u7406\u89e3\u8bfb\u548c\u8bc1\u636e\u6307\u9488\u3002"),
    "appendix_narrative": _zh(r"\u9644\u5f55\u4fdd\u7559\u5b57\u6bb5\u753b\u50cf\u3001\u6d3e\u751f\u5b57\u6bb5\u548c\u8def\u7531\u65b9\u6cd5\uff0c\u4fbf\u4e8e\u5ba1\u8ba1\u62a5\u544a\u7ed3\u8bba\u5982\u4f55\u4ea7\u751f\u3002"),
    "field_narrative": _zh(r"\u5b57\u6bb5\u89e3\u91ca\u628a\u539f\u59cb\u5217\u540d\u8f6c\u6210\u4e1a\u52a1\u8bed\u4e49\u3001\u5206\u6790\u89d2\u8272\u548c\u540e\u7eed\u53ef\u7528\u573a\u666f\u3002"),
    "action_narrative": _zh(r"\u884c\u52a8\u5efa\u8bae\u57fa\u4e8e\u81ea\u52a8\u8c61\u9650\u5207\u5206\u548c\u5b57\u6bb5\u9009\u62e9\u7ed3\u679c\uff0c\u5148\u7ed9\u51fa\u53ef\u6267\u884c\u7684\u7ba1\u7406\u52a8\u4f5c\uff0c\u800c\u4e0d\u662f\u505c\u7559\u5728\u63cf\u8ff0\u7edf\u8ba1\u3002"),
    "evidence_narrative": _zh(r"\u8bc1\u636e\u7d22\u5f15\u7528\u4e8e\u628a\u6458\u8981\u3001\u56fe\u8868\u3001\u8868\u683c\u548c\u65b9\u6cd5\u8bf4\u660e\u4e32\u56de\u540c\u4e00\u6279\u7ed3\u6784\u5316\u6570\u636e\uff0c\u65b9\u4fbf\u5ba1\u8ba1\u548c\u590d\u7528\u3002"),
    "executive_narrative": _zh(r"\u5df2\u5b8c\u6210\u5b57\u6bb5\u7406\u89e3\u3001\u6d3e\u751f\u6307\u6807\u3001\u65b9\u6cd5\u9009\u62e9\u548c\u56fe\u8868\u8bc1\u636e\u7ec4\u88c5\uff1b\u4e0b\u6587\u5c06\u628a\u8fd9\u4e9b\u7ed3\u679c\u8f6c\u6210\u7ba1\u7406\u5c42\u53ef\u9605\u8bfb\u7684\u5224\u65ad\u3001\u8bc1\u636e\u548c\u884c\u52a8\u6e05\u5355\u3002"),
    "method_note_narrative": _zh(r"\u65b9\u6cd5\u9009\u62e9\u7efc\u5408\u5b57\u6bb5\u53e3\u5f84\u3001\u62a5\u544a\u76ee\u6807\u3001\u8f93\u51fa\u7c7b\u578b\u548c\u53ef\u89e3\u91ca\u6027\uff0c\u4f18\u5148\u4fdd\u7559\u80fd\u652f\u6491\u4e1a\u52a1\u5224\u65ad\u7684\u8bc1\u636e\u3002"),
}

REPORT_PART_TITLES = {key: Z[key] for key in ["executive_summary", "chapter", "visual_gallery", "appendix", "method_note", "field_glossary", "action_plan", "evidence_index"]}
ASSET_MANIFEST_TITLE = _zh(r"\u62a5\u544a\u90e8\u4ef6\u8d44\u4ea7\u6e05\u5355")
GENERATION_BLUEPRINT_TITLE = _zh(r"\u62a5\u544a\u90e8\u4ef6\u751f\u6210\u84dd\u56fe")

QUADRANT_ACTIONS = {
    "high_high": _zh(r"\u4f18\u5148\u653e\u5927\uff1a\u4fdd\u7559\u8d44\u6e90\u6295\u5165\uff0c\u6c89\u6dc0\u53ef\u590d\u7528\u6253\u6cd5\u3002"),
    "high_low": _zh(r"\u6548\u7387\u6821\u6b63\uff1a\u5b9a\u4f4d\u6210\u672c\u3001\u8f6c\u5316\u6216\u7ed3\u6784\u6027\u62d6\u7d2f\uff0c\u4f18\u5148\u505a\u8bca\u65ad\u3002"),
    "low_high": _zh(r"\u6f5c\u529b\u57f9\u80b2\uff1a\u8865\u9f50\u89c4\u6a21\u3001\u66dd\u5149\u6216\u8986\u76d6\uff0c\u9a8c\u8bc1\u653e\u91cf\u7a7a\u95f4\u3002"),
    "low_low": _zh(r"\u4f4e\u4f18\u5148\u7ea7/\u9700\u8bca\u65ad\uff1a\u907f\u514d\u65e0\u5dee\u522b\u6295\u5165\uff0c\u5148\u5224\u65ad\u662f\u5426\u9000\u51fa\u3001\u5408\u5e76\u6216\u91cd\u6784\u3002"),
}


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


FAMILY_SELECTION_FLOORS = {
    "report_part": 4,
    "descriptive": 4,
    "association": 4,
    "comparison": 3,
    "regression": 3,
    "machine_learning": 3,
    "causal": 3,
    "visual": 6,
}

FAMILY_SELECTION_CAP_RATIO = {
    "visual": 0.32,
    "report_part": 0.18,
}


def _list_text(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [_clean_text(item) for item in values if _clean_text(item)]


def _role_counts(field_profiles: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {"measure": 0, "dimension": 0, "time": 0, "entity": 0}
    for profile in field_profiles:
        role = _clean_text(profile.get("role"))
        if role in counts:
            counts[role] += 1
    return counts


def _method_feasible(method: dict[str, Any], context: dict[str, int]) -> bool:
    roles = {_clean_text(item) for item in list(method.get("required_roles") or [])}
    if not roles or "full_dataset" in roles:
        return True
    checks = {
        "single_field": context["field_count"] >= 1,
        "field_pair": context["measure"] >= 2,
        "field_set": context["measure"] >= 2 or context["field_count"] >= 3,
        "grouped": context["dimension"] + context["entity"] >= 1,
        "time_window": context["time"] >= 1,
        "entity_level": context["entity"] >= 1,
        "derived_metric": context["derived_field_count"] >= 1,
    }
    for role, ok in checks.items():
        if role in roles:
            return ok
    if {"continuous", "numeric", "measure"} & roles:
        return context["measure"] >= 1
    if {"categorical", "dimension"} & roles:
        return context["dimension"] >= 1
    return True


def _method_has_blocking_missing_bindings(method: dict[str, Any]) -> bool:
    if _clean_text(method.get("binding_quality")) != "partial":
        return False
    missing = set(_list_text((method.get("method_card") or {}).get("missing_bindings") if isinstance(method.get("method_card"), dict) else []))
    family = _clean_text(method.get("family"))
    if family == "time_series" and "time" in missing:
        return True
    if family in {"mean_tests", "nonparametric"} and ("group" in missing or "y" in missing):
        return True
    return False


def _selection_family_cap(family: str, max_methods: int) -> int:
    ratio = FAMILY_SELECTION_CAP_RATIO.get(family)
    if ratio is None:
        return max_methods
    return max(1, int(round(max_methods * ratio)))


def _select_diverse_routed_methods(routed: list[dict[str, Any]], max_methods: int) -> list[dict[str, Any]]:
    if max_methods <= 0:
        return []
    eligible = [item for item in routed if not _method_has_blocking_missing_bindings(item)]
    if not eligible:
        eligible = list(routed)
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    family_counts: dict[str, int] = {}

    def _add(item: dict[str, Any]) -> bool:
        method_run_id = _clean_text(item.get("method_run_id") or item.get("id"))
        if not method_run_id or method_run_id in selected_ids:
            return False
        family = _clean_text(item.get("family"))
        if family_counts.get(family, 0) >= _selection_family_cap(family, max_methods):
            return False
        selected.append(item)
        selected_ids.add(method_run_id)
        family_counts[family] = family_counts.get(family, 0) + 1
        return True

    for family, floor in FAMILY_SELECTION_FLOORS.items():
        if len(selected) >= max_methods:
            break
        candidates = [item for item in eligible if _clean_text(item.get("family")) == family]
        for item in candidates[:floor]:
            if len(selected) >= max_methods:
                break
            _add(item)

    for item in eligible:
        if len(selected) >= max_methods:
            break
        _add(item)

    if len(selected) < max_methods:
        for item in routed:
            if len(selected) >= max_methods:
                break
            method_run_id = _clean_text(item.get("method_run_id") or item.get("id"))
            if method_run_id and method_run_id not in selected_ids:
                selected.append(item)
                selected_ids.add(method_run_id)
    selected.sort(key=lambda item: (int(item.get("route_score") or 0), _clean_text(item.get("id"))), reverse=True)
    return selected[:max_methods]


def _first(values: list[str]) -> str:
    return values[0] if values else ""


def _role_fields(field_profiles: list[dict[str, Any]]) -> dict[str, list[str]]:
    fields: dict[str, list[str]] = {"measure": [], "dimension": [], "time": [], "entity": []}
    for profile in field_profiles:
        role = _clean_text(profile.get("role"))
        column = _clean_text(profile.get("column"))
        if role in fields and column:
            fields[role].append(column)
    return fields


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        item = _clean_text(value)
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def normalize_report_part_ids(request_part: str = "auto", selected_report_parts: list[str] | None = None) -> list[str]:
    available = set(REPORT_PART_TITLES)
    values: list[str] = []
    for raw in list(selected_report_parts or []):
        values.extend(part.strip() for part in _clean_text(raw).split(","))
    if not values:
        values.extend(part.strip() for part in _clean_text(request_part).split(","))
    parts = [part for part in _unique(values) if part and part != "auto"]
    valid = [part for part in parts if part in available]
    return valid or list(REPORT_PART_TITLES)


def _chart_refs_for_method(method_id: str, family: str, outputs: set[str], charts: list[dict[str, Any]]) -> list[str]:
    if not charts:
        return []
    wants_visual = family == "visual" or method_id.endswith("_chart") or method_id.endswith("_image_spec")
    if not wants_visual:
        return []
    refs: list[str] = []
    for chart in charts:
        kind = _clean_text(chart.get("kind"))
        normalized = kind.replace("-", "_")
        if normalized and (normalized in method_id or family == "visual"):
            refs.append(f"chart:{kind}")
    return _unique(refs)[:6] or [f"chart:{_clean_text(charts[0].get('kind'))}"]


def _method_wants_visual_asset(method_id: str, family: str) -> bool:
    return family == "visual" or method_id.endswith("_chart") or method_id.endswith("_image_spec")


def _binding_field_values(bindings: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for value in bindings.values():
        if isinstance(value, list):
            values.extend(_clean_text(item) for item in value)
        elif isinstance(value, str):
            values.append(_clean_text(value))
    return _unique([value for value in values if value and value != "all_rows"])


def _merge_bindings(default: dict[str, Any], override: dict[str, Any] | None) -> dict[str, Any]:
    merged = dict(default)
    if not isinstance(override, dict):
        return merged
    for key, value in override.items():
        if value is None:
            continue
        if isinstance(value, list):
            cleaned = _unique([_clean_text(item) for item in value if _clean_text(item)])
            if cleaned:
                merged[key] = cleaned
            continue
        if isinstance(value, dict):
            nested = {
                nested_key: _clean_text(nested_value)
                for nested_key, nested_value in value.items()
                if _clean_text(nested_value)
            }
            if nested:
                merged[key] = nested
            continue
        text = _clean_text(value)
        if text:
            merged[key] = text
    return merged


def _binding_override_for_method(
    method_id: str,
    method_field_bindings: dict[str, dict[str, Any]] | None = None,
    method_run_spec: dict[str, Any] | None = None,
    method_default_bindings: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    if isinstance(method_run_spec, dict):
        binding = method_run_spec.get("field_bindings")
        if isinstance(binding, dict):
            return binding
        binding = method_run_spec.get("binding")
        if isinstance(binding, dict):
            return binding
    if isinstance(method_field_bindings, dict):
        binding = method_field_bindings.get(method_id)
        if isinstance(binding, dict):
            return binding
    if isinstance(method_default_bindings, dict) and method_default_bindings:
        return method_default_bindings
    return None


def _semantic_route_rows_for_bindings(bindings: dict[str, Any], field_semantic_route_plan: dict[str, Any] | None) -> list[dict[str, Any]]:
    rows = list((field_semantic_route_plan or {}).get("rows") or [])
    if not rows:
        return []
    wanted = set(_binding_field_values(bindings))
    if not wanted:
        return []
    compact_rows: list[dict[str, Any]] = []
    for row in rows:
        field = _clean_text(row.get("field"))
        if field not in wanted:
            continue
        compact_rows.append(
            {
                "field": field,
                "source": row.get("source"),
                "semantic_role": row.get("semantic_role"),
                "business_meaning": row.get("business_meaning"),
                "analysis_roles": row.get("analysis_roles"),
                "compatible_method_families": row.get("compatible_method_families"),
                "recommended_report_parts": row.get("recommended_report_parts"),
                "relationship_refs": row.get("relationship_refs"),
                "derived_from": row.get("derived_from"),
            }
        )
    return compact_rows


def _semantic_route_contract(bindings: dict[str, Any], semantic_rows: list[dict[str, Any]], field_semantic_route_plan: dict[str, Any] | None) -> dict[str, Any]:
    bound_fields = _binding_field_values(bindings)
    derived_fields = [row["field"] for row in semantic_rows if row.get("source") == "derived_field"]
    report_parts = _unique(
        [
            item.strip()
            for row in semantic_rows
            for item in _clean_text(row.get("recommended_report_parts")).split(",")
            if item.strip()
        ]
    )
    method_families = _unique(
        [
            item.strip()
            for row in semantic_rows
            for item in _clean_text(row.get("compatible_method_families")).split(",")
            if item.strip()
        ]
    )
    return {
        "status": "ready" if semantic_rows or not bound_fields else "partial",
        "pre_method_preprocessing_status": _clean_text((field_semantic_route_plan or {}).get("pre_method_preprocessing_status"))
        or "derived_fields_completed_before_method_routing",
        "bound_fields": bound_fields,
        "semantic_route_field_count": len(semantic_rows),
        "derived_bound_fields": derived_fields,
        "compatible_method_families": method_families,
        "recommended_report_parts": report_parts,
        "selection_basis": "field bindings are explained by the semantic route plan generated after derived-field preprocessing",
    }


def _csv_tokens(value: Any) -> list[str]:
    return _unique([item.strip() for item in _clean_text(value).split(",") if item.strip()])


def _semantic_route_match_score(
    method: dict[str, Any],
    method_card: dict[str, Any],
    requested_parts: set[str],
) -> tuple[int, list[str]]:
    family = _clean_text(method.get("family"))
    outputs = {_clean_text(item) for item in list(method.get("output_types") or [])}
    semantic_rows = list(method_card.get("semantic_field_routes") or []) if isinstance(method_card.get("semantic_field_routes"), list) else []
    contract = method_card.get("runtime_field_selection_contract") if isinstance(method_card.get("runtime_field_selection_contract"), dict) else {}
    compatible_families = set(_list_text(contract.get("compatible_method_families")))
    recommended_parts = set(_list_text(contract.get("recommended_report_parts")))
    derived_bound_fields = _list_text(contract.get("derived_bound_fields"))
    relationship_ref_count = sum(len(_csv_tokens(row.get("relationship_refs"))) for row in semantic_rows)

    score = 0
    reasons: list[str] = []
    if semantic_rows:
        score += 10
        reasons.append("semantic_field_binding")
    elif _clean_text(contract.get("status")) == "partial":
        score -= 8
        reasons.append("semantic_binding_partial")
    if family and family in compatible_families:
        score += 12
        reasons.append("semantic_method_family_match")
    if requested_parts and recommended_parts & requested_parts:
        score += 10
        reasons.append("semantic_report_part_match")
    if relationship_ref_count:
        score += min(8, relationship_ref_count * 2)
        reasons.append("field_relationship_evidence")
    if derived_bound_fields:
        score += 8
        reasons.append("derived_field_bound")
    method_id = _clean_text(method.get("id"))
    if _method_wants_visual_asset(method_id, family) and "visual_gallery" in recommended_parts:
        score += 6
        reasons.append("semantic_visual_slot_fit")
    if ("report_section" in outputs or family == "report_part") and recommended_parts:
        score += 6
        reasons.append("semantic_report_writer_fit")
    return score, reasons


def _report_slots_for_method(method_id: str, family: str, outputs: set[str], requested: str) -> list[str]:
    slots: list[str] = []
    requested_parts = set(normalize_report_part_ids(requested))
    for part_id in REPORT_PART_TITLES:
        if part_id in method_id:
            slots.append(part_id)
    if requested != "auto":
        slots.extend(part for part in requested_parts if part in REPORT_PART_TITLES)
    if _method_wants_visual_asset(method_id, family):
        slots.append("visual_gallery")
    if family == "report_part" or "report_section" in outputs:
        slots.append(requested if requested != "auto" else "chapter")
    if "table" in outputs or "data" in outputs:
        slots.extend(["appendix", "evidence_index"])
    if family == "causal":
        slots.extend(["action_plan", "method_note"])
    if family == "time_series":
        slots.extend(["chapter", "action_plan"])
    return _unique(slots)[:5] or ["chapter"]


def _executor_hint_for_method(method_id: str, family: str, outputs: set[str]) -> str:
    clean_method_id = _clean_text(method_id)
    statistical_candidates = [clean_method_id]
    for suffix in STATISTICAL_OUTPUT_VARIANTS:
        if clean_method_id.endswith(f"_{suffix}"):
            statistical_candidates.append(clean_method_id[: -(len(suffix) + 1)])
    if any(candidate in SUPPORTED_ANALYSIS_TYPES for candidate in statistical_candidates):
        return "statistical_analysis_executor"
    if _method_wants_visual_asset(method_id, family):
        return "chart_asset_builder"
    if family == "report_part" or "report_section" in outputs:
        return "report_section_writer"
    if family == "time_series":
        return "time_series_diagnostic_executor"
    if family == "causal":
        return "causal_screen_executor"
    if family in {"association", "categorical_association"}:
        return "association_executor"
    if family in {"regression", "regression_glm", "machine_learning"}:
        return "runtime_model_executor"
    if family == "descriptive":
        return "profile_table_executor"
    if "table" in outputs:
        return "table_builder"
    return "runtime_explainer"


def _route_evidence_record(
    method: dict[str, Any],
    method_card: dict[str, Any],
    *,
    score: int,
    reasons: list[str],
    context: dict[str, int],
    requested: str,
) -> dict[str, Any]:
    contract = method_card.get("runtime_field_selection_contract") if isinstance(method_card.get("runtime_field_selection_contract"), dict) else {}
    bindings = method_card.get("field_bindings") if isinstance(method_card.get("field_bindings"), dict) else {}
    semantic_rows = list(method_card.get("semantic_field_routes") or []) if isinstance(method_card.get("semantic_field_routes"), list) else []
    return {
        "method_id": _clean_text(method.get("id")),
        "family": _clean_text(method.get("family")),
        "route_score": score,
        "route_reasons": reasons,
        "requested_part": requested,
        "pre_method_preprocessing_status": _clean_text(contract.get("pre_method_preprocessing_status")) or "derived_fields_completed_before_method_routing",
        "field_context": {
            "field_count": context["field_count"],
            "measure_fields": context["measure"],
            "dimension_fields": context["dimension"],
            "time_fields": context["time"],
            "entity_fields": context["entity"],
            "derived_fields": context["derived_field_count"],
            "charts": context["chart_count"],
        },
        "bound_fields": _binding_field_values(bindings),
        "semantic_route_field_count": int(contract.get("semantic_route_field_count") or len(semantic_rows)),
        "semantic_route_refs": _list_text(method_card.get("semantic_route_refs")),
        "derived_bound_fields": _list_text(contract.get("derived_bound_fields")),
        "compatible_method_families": _list_text(contract.get("compatible_method_families")),
        "recommended_report_parts": _list_text(contract.get("recommended_report_parts")),
        "report_slots": _list_text(method_card.get("report_slots")),
        "executor_hint": _clean_text(method_card.get("executor_hint")),
        "binding_quality": _clean_text(method_card.get("binding_quality")),
        "output_types": _list_text(method.get("output_types")),
        "required_roles": _list_text(method.get("required_roles")),
        "management_use": "Audit method routing: why this method was selected and how it can generate text, tables, data, charts, images or report sections.",
    }


def _build_method_card(
    method: dict[str, Any],
    *,
    selected: dict[str, Any],
    field_profiles: list[dict[str, Any]],
    derived_fields: list[dict[str, Any]],
    field_semantic_route_plan: dict[str, Any] | None,
    charts: list[dict[str, Any]],
    requested: str,
    method_field_bindings: dict[str, dict[str, Any]] | None = None,
    method_run_spec: dict[str, Any] | None = None,
) -> dict[str, Any]:
    method_id = _clean_text(method.get("id"))
    family = _clean_text(method.get("family"))
    outputs = {_clean_text(item) for item in list(method.get("output_types") or [])}
    roles = {_clean_text(item) for item in list(method.get("required_roles") or [])}
    fields = _role_fields(field_profiles)
    derived_names = [_clean_text(item.get("field")) for item in derived_fields if _clean_text(item.get("field"))]
    target = _clean_text(selected.get("target")) or _first(fields["measure"])
    features = _unique([_clean_text(item) for item in list(selected.get("features") or [])] + fields["measure"])
    group = _clean_text(selected.get("group")) or _first(fields["dimension"] + fields["entity"])
    label = _clean_text(selected.get("label")) or _first(fields["entity"] + fields["dimension"])
    time_field = _first(fields["time"])

    bindings: dict[str, Any] = {}
    if "full_dataset" in roles or not roles:
        bindings["dataset_scope"] = "all_rows"
    if family == "visual" and "bubble" in method_id:
        bubble = selected.get("bubble") or {}
        bindings.update({"x": _clean_text(bubble.get("x")) or target, "y": _clean_text(bubble.get("y")) or _first(features), "size": _clean_text(bubble.get("size")) or target, "color": group, "label": label})
    elif family == "visual" and "quadrant" in method_id:
        quadrant = selected.get("quadrant") or {}
        bindings.update({"x": _clean_text(quadrant.get("x")) or target, "y": _clean_text(quadrant.get("y")) or _first(features), "group": group, "label": label})
    elif "field_pair" in roles or family in {"association", "comparison", "causal"}:
        bindings.update({"x": target, "y": _first([item for item in features if item != target])})
    elif "field_set" in roles or family in {"regression", "machine_learning"}:
        bindings.update({"target": target, "features": [item for item in features if item != target][:4]})
    elif "single_field" in roles:
        bindings["field"] = target
    else:
        bindings["target"] = target
        if features:
            bindings["features"] = [item for item in features if item != target][:3]
    if "grouped" in roles or "categorical" in roles or "dimension" in roles or "binary_group" in roles or "group" in roles:
        bindings["group"] = group
    if "time_window" in roles or "time" in roles or family == "time_series":
        bindings["time"] = time_field
    if "entity_level" in roles or "entity" in roles:
        bindings["entity"] = label
    if "derived_metric" in roles or family in {"causal", "time_series"}:
        bindings["derived_metric"] = _first(derived_names)

    method_default_bindings = method.get("field_bindings") if isinstance(method.get("field_bindings"), dict) else {}
    manual_bindings = _binding_override_for_method(method_id, method_field_bindings, method_run_spec, method_default_bindings)
    if isinstance(manual_bindings, dict) and manual_bindings:
        bindings = _merge_bindings(bindings, manual_bindings)
    run_id = _clean_text((method_run_spec or {}).get("run_id") if isinstance(method_run_spec, dict) else "")
    run_label = _clean_text((method_run_spec or {}).get("label") if isinstance(method_run_spec, dict) else "")
    selection_mode = _clean_text((method_run_spec or {}).get("selection_mode") if isinstance(method_run_spec, dict) else "") or _clean_text(method.get("selection_mode"))
    object_selection = (
        dict(method_run_spec.get("object_selection") or {})
        if isinstance(method_run_spec, dict) and isinstance(method_run_spec.get("object_selection"), dict)
        else (dict(method.get("object_selection") or {}) if isinstance(method.get("object_selection"), dict) else {})
    )
    statistical_options = dict(method.get("statistical_options") or {}) if isinstance(method.get("statistical_options"), dict) else {}
    if isinstance(method_run_spec, dict) and isinstance(method_run_spec.get("statistical_options"), dict):
        statistical_options.update(dict(method_run_spec.get("statistical_options") or {}))
    smart_merge_group = _clean_text((method_run_spec or {}).get("smart_merge_group") if isinstance(method_run_spec, dict) else "")
    binding_source = "auto"
    if isinstance(method_run_spec, dict) and method_run_spec:
        binding_source = "run_spec"
    elif isinstance(method_field_bindings, dict) and isinstance(method_field_bindings.get(method_id), dict):
        binding_source = "manual"
    elif isinstance(method_default_bindings, dict) and method_default_bindings:
        binding_source = "saved_method_card"

    missing = [key for key, value in bindings.items() if key != "dataset_scope" and not value]
    semantic_rows = _semantic_route_rows_for_bindings(bindings, field_semantic_route_plan)
    semantic_refs = [f"field_semantic_route:{row['field']}" for row in semantic_rows if _clean_text(row.get("field"))]
    chart_refs = _chart_refs_for_method(method_id, family, outputs, charts)
    evidence_refs = _unique(["data:selected_fields", "table:derived_fields", "table:field_semantic_route_plan", "data:field_semantic_route_plan", "data:routed_methods", *semantic_refs, *chart_refs])
    if family == "causal":
        evidence_refs.extend(["table:causal_candidate_paths", "table:causal_light_executor_results"])
    if family == "time_series":
        evidence_refs.append("table:time_series_diagnostics")
    evidence_refs = _unique(evidence_refs)
    return {
        "method_id": method_id,
        "method_run_id": run_id or method_id,
        "method_run_label": run_label,
        "family": family,
        "output_types": sorted(outputs),
        "required_roles": sorted(roles),
        "field_bindings": bindings,
        "selection_mode": selection_mode or ("object" if object_selection else "fields"),
        "object_selection": object_selection,
        "statistical_options": statistical_options,
        "smart_merge_group": smart_merge_group,
        "semantic_field_routes": semantic_rows,
        "semantic_route_refs": semantic_refs,
        "runtime_field_selection_contract": _semantic_route_contract(bindings, semantic_rows, field_semantic_route_plan),
        "binding_quality": "partial" if missing else "ready",
        "missing_bindings": missing,
        "binding_source": binding_source,
        "executor_hint": _executor_hint_for_method(method_id, family, outputs),
        "cli_interpretation_enabled": True,
        "cli_interpretation": _zh(r"CLI \u667a\u80fd\u89e3\u8bfb\u5df2\u542f\u7528\uff1a\u672c\u65b9\u6cd5\u4f1a\u628a\u6267\u884c\u7ed3\u679c\u8f6c\u6210\u4e2d\u6587\u4e1a\u52a1\u542b\u4e49\u3001\u8bc1\u636e\u5f15\u7528\u548c\u53ef\u6267\u884c\u5efa\u8bae\u3002"),
        "report_slots": _report_slots_for_method(method_id, family, outputs, requested),
        "evidence_refs": evidence_refs,
    }


def route_methods_for_report_parts(
    registry: list[dict[str, Any]],
    *,
    field_profiles: list[dict[str, Any]],
    derived_fields: list[dict[str, Any]],
    field_semantic_route_plan: dict[str, Any] | None = None,
    selected: dict[str, Any],
    charts: list[dict[str, Any]],
    requested_part: str,
    priority_ids: set[str],
    max_methods: int,
    method_field_bindings: dict[str, dict[str, Any]] | None = None,
    method_run_specs: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    role_counts = _role_counts(field_profiles)
    context = {**role_counts, "field_count": len(field_profiles), "derived_field_count": len(derived_fields), "chart_count": len(charts)}
    requested = _clean_text(requested_part) or "auto"
    requested_parts = set(normalize_report_part_ids(requested))
    alias_to_method_id: dict[str, str] = {}
    for method in registry:
        method_id = _clean_text(method.get("id"))
        if not method_id:
            continue
        alias_to_method_id.setdefault(method_id, method_id)
        for alias in list(method.get("compatibility_alias_ids") or []):
            alias_text = _clean_text(alias)
            if alias_text:
                alias_to_method_id.setdefault(alias_text, method_id)
    run_specs_by_method: dict[str, list[dict[str, Any]]] = {}
    if isinstance(method_run_specs, list):
        for spec in method_run_specs:
            if not isinstance(spec, dict):
                continue
            method_id = _clean_text(spec.get("method_id"))
            if not method_id:
                continue
            canonical_id = alias_to_method_id.get(method_id, method_id)
            if canonical_id != method_id:
                spec = {**spec, "requested_method_id": method_id, "method_id": canonical_id}
            run_specs_by_method.setdefault(canonical_id, []).append(spec)
    routed: list[dict[str, Any]] = []
    for method in registry:
        method_id = _clean_text(method.get("id"))
        family = _clean_text(method.get("family"))
        outputs = {_clean_text(item) for item in list(method.get("output_types") or [])}
        score = 0
        reasons: list[str] = []
        if method_id in priority_ids:
            score += 40
            reasons.append("priority_catalog")
        if _method_feasible(method, context):
            score += 20
            reasons.append("field_roles_available")
        else:
            score -= 30
            reasons.append("field_roles_missing")
        if requested != "auto" and (any(part in method_id for part in requested_parts) or family in requested_parts):
            score += 24
            reasons.append("requested_report_part_match")
        if "report_section" in outputs:
            score += 18
            reasons.append("can_write_report_section")
        if _method_wants_visual_asset(method_id, family):
            score += 10 if charts else 2
            reasons.append("visual_output_candidate")
        if "table" in outputs:
            score += 8
            reasons.append("table_output_candidate")
        if family in {"visual", "report_part", "descriptive", "association", "time_series", "causal"}:
            score += 6
            reasons.append("core_auto_analysis_family")
        specs = run_specs_by_method.get(method_id) or [None]
        for run_index, run_spec in enumerate(specs, start=1):
            method_card = _build_method_card(
                method,
                selected=selected,
                field_profiles=field_profiles,
                derived_fields=derived_fields,
                field_semantic_route_plan=field_semantic_route_plan,
                charts=charts,
                requested=requested,
                method_field_bindings=method_field_bindings,
                method_run_spec=run_spec,
            )
            route_score = score
            route_reasons = list(reasons)
            semantic_score, semantic_reasons = _semantic_route_match_score(method, method_card, requested_parts)
            route_score += semantic_score
            route_reasons.extend(semantic_reasons)
            route_evidence = _route_evidence_record(method, method_card, score=route_score, reasons=route_reasons, context=context, requested=requested)
            route_evidence["method_run_id"] = method_card.get("method_run_id")
            route_evidence["method_run_label"] = method_card.get("method_run_label")
            route_evidence["selection_mode"] = method_card.get("selection_mode")
            route_evidence["smart_merge_group"] = method_card.get("smart_merge_group")
            route_evidence["cli_interpretation_enabled"] = method_card.get("cli_interpretation_enabled")
            route_evidence["cli_interpretation"] = method_card.get("cli_interpretation")
            routed.append({
                **method,
                "route_score": route_score,
                "route_reasons": route_reasons,
                "route_context": {"requested_part": requested, "requested_parts": sorted(requested_parts), "measure_fields": context["measure"], "dimension_fields": context["dimension"], "time_fields": context["time"], "derived_fields": context["derived_field_count"], "charts": context["chart_count"]},
                "route_evidence": route_evidence,
                "method_card": method_card,
                "method_run_id": method_card.get("method_run_id") or f"{method_id}__{run_index}",
                "method_run_label": method_card.get("method_run_label") or "",
                "field_bindings": method_card["field_bindings"],
                "selection_mode": method_card.get("selection_mode"),
                "object_selection": method_card.get("object_selection"),
                "smart_merge_group": method_card.get("smart_merge_group"),
                "executor_hint": method_card["executor_hint"],
                "cli_interpretation_enabled": method_card.get("cli_interpretation_enabled"),
                "cli_interpretation": method_card.get("cli_interpretation"),
                "report_slots": method_card["report_slots"],
                "binding_quality": method_card["binding_quality"],
            })
    routed.sort(key=lambda item: (int(item.get("route_score") or 0), _clean_text(item.get("id"))), reverse=True)
    return _select_diverse_routed_methods(routed, max_methods)


def _selected_field_bullets(selected: dict[str, Any]) -> list[str]:
    bubble = selected.get("bubble") or {}
    quadrant = selected.get("quadrant") or {}
    return [
        f"target: {_clean_text(selected.get('target')) or Z['unknown']}",
        f"features: {', '.join(selected.get('features') or []) or Z['unknown']}",
        f"group/label: {_clean_text(selected.get('group')) or Z['unknown']} / {_clean_text(selected.get('label')) or Z['unknown']}",
        f"bubble: x={_clean_text(bubble.get('x'))}, y={_clean_text(bubble.get('y'))}, size={_clean_text(bubble.get('size'))}",
        f"quadrant: x={_clean_text(quadrant.get('x'))}, y={_clean_text(quadrant.get('y'))}",
    ]


def _evidence_rows_by_title(evidence_tables: list[dict[str, Any]], title: str) -> list[dict[str, Any]]:
    for table in evidence_tables:
        if table.get("title") == title:
            return list(table.get("rows") or [])
    return []


def _action_priority_rows(evidence_tables: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return _evidence_rows_by_title(evidence_tables, _zh(r"\u884c\u52a8\u4f18\u5148\u7ea7\u8bc4\u5206"))


def _action_plan_bullets(action_rows: list[dict[str, Any]], evidence_tables: list[dict[str, Any]]) -> list[str]:
    priority_bullets = [
        f"{_clean_text(row.get('priority'))} priority: {_clean_text(row.get('action'))}; next={_clean_text(row.get('next_step'))}; evidence={_clean_text(row.get('source_ref'))}"
        for row in _action_priority_rows(evidence_tables)[:5]
    ]
    if priority_bullets:
        return priority_bullets
    return [row["recommended_action"] for row in action_rows] or ["diagnose first"]


def _tables_by_title(tables: list[dict[str, Any]], title: str) -> list[dict[str, Any]]:
    return [table for table in tables if _clean_text(table.get("title")) == title]


def _chart_management_interpretation(chart: dict[str, Any], quadrant_counts: dict[str, int]) -> str:
    kind = _clean_text(chart.get("kind"))
    if kind == "bubble":
        return _zh(r"\u7ba1\u7406\u89e3\u8bfb\uff1a\u628a\u6bcf\u6761\u8bb0\u5f55\u5f53\u4f5c\u4e00\u4e2a\u4e1a\u52a1\u5bf9\u8c61\uff0c\u6a2a\u7eb5\u8f74\u770b\u4e24\u9879\u6838\u5fc3\u8868\u73b0\uff0c\u6c14\u6ce1\u5927\u5c0f\u770b\u5f3a\u5ea6\u6216\u89c4\u6a21\uff0c\u4f18\u5148\u5bfb\u627e\u53f3\u4e0a\u89d2\u7684\u5927\u6c14\u6ce1\u3001\u79bb\u7fa4\u5927\u6c14\u6ce1\u548c\u540c\u7ec4\u5185\u663e\u8457\u5206\u5316\u5bf9\u8c61\u3002")
    if kind == "quadrant":
        dominant = max(quadrant_counts.items(), key=lambda item: item[1])[0] if quadrant_counts else ""
        action = QUADRANT_ACTIONS.get(dominant, _zh(r"\u5148\u8865\u9f50\u6837\u672c\u548c\u5b57\u6bb5\uff0c\u518d\u505a\u884c\u52a8\u5206\u5c42\u3002"))
        intro = _zh(r"\u7ba1\u7406\u89e3\u8bfb\uff1a\u7528\u4e2d\u4f4d\u6570\u5207\u5206\u56db\u8c61\u9650\uff0c\u5f53\u524d\u6837\u672c\u6700\u591a\u7684\u8c61\u9650\u662f")
        suggestion = _zh(r"\u5efa\u8bae\uff1a")
        return f"{intro} {dominant or 'unknown'} {suggestion}{action}"
    if kind == "scatter":
        return _zh(r"\u7ba1\u7406\u89e3\u8bfb\uff1a\u89c2\u5bdf\u4e24\u4e2a\u6307\u6807\u7684\u65b9\u5411\u5173\u7cfb\u3001\u79bb\u7fa4\u70b9\u548c\u5206\u5c42\u7ed3\u6784\uff0c\u4f18\u5148\u5b9a\u4f4d\u6700\u504f\u79bb\u4e3b\u8d8b\u52bf\u7684\u5bf9\u8c61\u3002")
    if kind == "histogram":
        return _zh(r"\u7ba1\u7406\u89e3\u8bfb\uff1a\u89c2\u5bdf\u6838\u5fc3\u6307\u6807\u662f\u5426\u957f\u5c3e\u3001\u96c6\u4e2d\u6216\u5b58\u5728\u5f02\u5e38\u5cf0\u503c\uff0c\u7528\u4e8e\u5224\u65ad\u5206\u5c42\u548c\u9608\u503c\u3002")
    if kind == "heatmap":
        return _zh(r"\u7ba1\u7406\u89e3\u8bfb\uff1a\u5f3a\u76f8\u5173\u5b57\u6bb5\u53ef\u80fd\u8868\u793a\u5171\u540c\u9a71\u52a8\u6216\u6307\u6807\u5197\u4f59\uff0c\u9002\u5408\u8fdb\u5165\u6a21\u578b\u6216\u89e3\u91ca\u7ae0\u8282\u3002")
    if kind == "line":
        return _zh(r"\u7ba1\u7406\u89e3\u8bfb\uff1a\u89c2\u5bdf\u65f6\u95f4\u8d8b\u52bf\u3001\u6ce2\u52a8\u548c\u9636\u6bb5\u6027\u62d0\u70b9\uff0c\u9002\u5408\u751f\u6210\u8d8b\u52bf\u7ae0\u8282\u548c\u884c\u52a8\u8282\u594f\u3002")
    if kind == "forecast":
        return _zh(r"\u7ba1\u7406\u89e3\u8bfb\uff1a\u9884\u6d4b\u7ebf\u53ea\u8868\u793a\u65b9\u5411\u6027\u5916\u63a8\uff0c\u9002\u5408\u505a\u98ce\u9669\u9884\u8b66\u548c\u8d44\u6e90\u8282\u594f\u8ba8\u8bba\uff0c\u4e0d\u5e94\u66ff\u4ee3\u6b63\u5f0f\u9884\u6d4b\u6a21\u578b\u3002")
    if kind == "cluster-scatter":
        return _zh(r"\u7ba1\u7406\u89e3\u8bfb\uff1a\u5206\u7fa4\u7ed3\u679c\u7528\u4e8e\u8bc6\u522b\u4e0d\u540c\u5bf9\u8c61\u7c7b\u578b\uff0c\u4f18\u5148\u6bd4\u8f83\u7fa4\u7ec4\u89c4\u6a21\u3001\u5747\u503c\u5dee\u5f02\u548c\u53ef\u6267\u884c\u7b56\u7565\u3002")
    if kind == "anomaly-scatter":
        return _zh(r"\u7ba1\u7406\u89e3\u8bfb\uff1a\u5f02\u5e38\u70b9\u4ee3\u8868\u591a\u6307\u6807\u8054\u5408\u504f\u79bb\uff0c\u4f18\u5148\u533a\u5206\u771f\u5b9e\u4e1a\u52a1\u673a\u4f1a\u3001\u98ce\u9669\u4e8b\u4ef6\u548c\u6570\u636e\u8d28\u91cf\u95ee\u9898\u3002")
    return _clean_text(chart.get("explanation")) or _zh(r"\u7ba1\u7406\u89e3\u8bfb\uff1a\u8be5\u56fe\u7528\u4e8e\u628a\u7ed3\u6784\u3001\u5dee\u5f02\u548c\u4f18\u5148\u7ea7\u8f6c\u6210\u53ef\u8ba8\u8bba\u7684\u7ba1\u7406\u95ee\u9898\u3002")


def _method_asset_kind(asset_type: str) -> str:
    if asset_type in {"chart_asset"}:
        return "image"
    if asset_type in {"report_section_contract", "text_contract"}:
        return "text"
    if asset_type in {"table_contract", "time_series_summary", "causal_screen_reference", "profile_summary"}:
        return "table"
    return "structured_data"


def _asset_refs_for_part(asset_manifest: list[dict[str, Any]], part_id: str, asset_kind: str = "") -> list[str]:
    refs: list[str] = []
    for row in asset_manifest:
        if _clean_text(row.get("report_part_id")) != part_id:
            continue
        if asset_kind and _clean_text(row.get("asset_kind")) != asset_kind:
            continue
        ref = _clean_text(row.get("asset_ref"))
        if ref:
            refs.append(ref)
    return _unique(refs)


def _method_evidence_for_part(routed_methods: list[dict[str, Any]], part_id: str, limit: int = 12) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for method in routed_methods:
        slots = set(_list_text(method.get("report_slots")))
        card = method.get("method_card") if isinstance(method.get("method_card"), dict) else {}
        card_slots = set(_list_text(card.get("report_slots")))
        if part_id not in {"method_note", "evidence_index"} and part_id not in slots and part_id not in card_slots:
            continue
        evidence = method.get("route_evidence") if isinstance(method.get("route_evidence"), dict) else {}
        rows.append(
            {
                "method_id": _clean_text(method.get("id")),
                "family": _clean_text(method.get("family")),
                "route_score": method.get("route_score"),
                "executor_hint": _clean_text(method.get("executor_hint")),
                "binding_quality": _clean_text(method.get("binding_quality")),
                "bound_fields": _binding_field_values(dict(method.get("field_bindings") or {})),
                "route_reasons": _list_text(method.get("route_reasons")),
                "semantic_route_refs": _list_text(evidence.get("semantic_route_refs")),
            }
        )
        if len(rows) >= limit:
            break
    return rows


def _blueprint_readiness(required_kinds: list[str], available: dict[str, list[str]]) -> str:
    missing = [kind for kind in required_kinds if not available.get(kind)]
    if not missing:
        return "ready"
    if len(missing) < len(required_kinds):
        return "partial"
    return "blocked"


def build_report_part_generation_blueprints(
    *,
    report_parts: list[dict[str, Any]],
    asset_manifest: list[dict[str, Any]],
    routed_methods: list[dict[str, Any]],
    field_semantic_route_plan: dict[str, Any],
    pre_method_routing_audit: list[dict[str, Any]] | None = None,
    method_route_evidence: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Create machine-readable instructions for generating any report part.

    The blueprints are the bridge from Analysis Lab assets to a runtime writer:
    each part declares required asset kinds, evidence refs, method evidence, and
    the exact handoff payload a Codex/exec runtime can consume.
    """
    pre_audit = list(pre_method_routing_audit or [])
    route_evidence = list(method_route_evidence or [])
    semantic_status = _clean_text(field_semantic_route_plan.get("pre_method_preprocessing_status")) or "derived_fields_completed_before_method_routing"
    semantic_rows = list(field_semantic_route_plan.get("rows") or [])
    required_by_part: dict[str, list[str]] = {
        "executive_summary": ["text", "structured_data"],
        "chapter": ["text", "table", "image", "structured_data"],
        "visual_gallery": ["image", "table", "structured_data"],
        "appendix": ["table", "structured_data"],
        "method_note": ["text", "table", "structured_data"],
        "field_glossary": ["table", "structured_data"],
        "action_plan": ["text", "table", "structured_data"],
        "evidence_index": ["table", "structured_data"],
    }
    blueprints: list[dict[str, Any]] = []
    for part in report_parts:
        part_id = _clean_text(part.get("id"))
        if not part_id:
            continue
        available = {
            "text": _asset_refs_for_part(asset_manifest, part_id, "text"),
            "table": _asset_refs_for_part(asset_manifest, part_id, "table"),
            "image": _asset_refs_for_part(asset_manifest, part_id, "image"),
            "structured_data": _asset_refs_for_part(asset_manifest, part_id, "structured_data"),
        }
        required_kinds = required_by_part.get(part_id, ["text", "table", "structured_data"])
        missing_kinds = [kind for kind in required_kinds if not available.get(kind)]
        method_evidence = _method_evidence_for_part(routed_methods, part_id)
        evidence_refs = _list_text(part.get("evidence_refs"))
        narrative = _clean_text(part.get("narrative"))
        bullets = _list_text(part.get("bullets"))
        table_titles = [_clean_text(table.get("title")) for table in list(part.get("tables") or []) if _clean_text(table.get("title"))]
        chart_refs = [f"chart:{_clean_text(chart.get('kind'))}" for chart in list(part.get("charts") or []) if _clean_text(chart.get("kind"))]
        blueprints.append(
            {
                "report_part_id": part_id,
                "report_part_title": _clean_text(part.get("title")),
                "readiness": _blueprint_readiness(required_kinds, available),
                "required_asset_kinds": required_kinds,
                "available_asset_refs": available,
                "missing_asset_kinds": missing_kinds,
                "text_seed_count": int(bool(narrative)) + len(bullets),
                "narrative_seed": narrative,
                "bullet_seeds": bullets[:12],
                "table_titles": table_titles[:20],
                "chart_refs": chart_refs[:20],
                "table_count": len(table_titles),
                "chart_count": len(chart_refs),
                "method_evidence_count": len(method_evidence),
                "semantic_route_field_count": int(field_semantic_route_plan.get("field_count") or len(semantic_rows)),
                "pre_method_preprocessing_status": semantic_status,
                "input_contract": {
                    "narrative_seed": narrative,
                    "bullet_seeds": bullets[:12],
                    "table_titles": table_titles[:20],
                    "chart_refs": chart_refs[:20],
                    "asset_refs": [ref for refs in available.values() for ref in refs],
                    "evidence_refs": evidence_refs[:40],
                    "semantic_route_refs": ["table:field_semantic_route_plan", "data:field_semantic_route_plan"],
                    "pre_method_audit_refs": ["table:pre_method_routing_audit", "data:pre_method_routing_audit"],
                    "route_evidence_refs": ["table:method_route_evidence", "data:method_route_evidence"],
                },
                "runtime_handoff": {
                    "target": "codex_cli_exec_runtime",
                    "task": f"generate_report_part:{part_id}",
                    "required_outputs": required_kinds,
                    "must_use_pre_method_audit": True,
                    "must_use_method_route_evidence": True,
                    "must_preserve_evidence_refs": True,
                    "allowed_outputs": ["text", "table", "structured_data", "chart", "image_spec", "report_section"],
                    "blocked_if_missing": missing_kinds,
                },
                "method_evidence": method_evidence,
                "audit_summary": {
                    "pre_method_stage_count": len(pre_audit),
                    "route_evidence_count": len(route_evidence),
                    "semantic_route_status": semantic_status,
                },
                "management_use": "Use this blueprint to generate or regenerate this report part from routed methods, evidence tables, chart assets and semantic field contracts.",
            }
        )
    return blueprints


def build_report_part_asset_manifest(
    *,
    report_parts: list[dict[str, Any]],
    method_execution_assets: list[dict[str, Any]],
    method_asset_limit_per_part: int = 40,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def append_row(part: dict[str, Any], *, asset_kind: str, asset_ref: str, source: str, title: str, payload_keys: list[str], management_use: str) -> None:
        part_id = _clean_text(part.get("id"))
        if not part_id or not asset_ref:
            return
        rows.append(
            {
                "report_part_id": part_id,
                "report_part_title": _clean_text(part.get("title")),
                "asset_kind": asset_kind,
                "asset_ref": asset_ref,
                "asset_title": title,
                "source": source,
                "payload_keys": ", ".join(payload_keys),
                "management_use": management_use,
            }
        )

    for part in report_parts:
        part_id = _clean_text(part.get("id"))
        if not part_id:
            continue
        narrative = _clean_text(part.get("narrative"))
        if narrative:
            append_row(
                part,
                asset_kind="text",
                asset_ref=f"text:{part_id}:narrative",
                source="report_part",
                title=f"{part_id} narrative",
                payload_keys=["narrative"],
                management_use="ready-to-place report narrative",
            )
        if _list_text(part.get("bullets")):
            append_row(
                part,
                asset_kind="text",
                asset_ref=f"text:{part_id}:bullets",
                source="report_part",
                title=f"{part_id} bullets",
                payload_keys=["bullets"],
                management_use="management bullets for the requested slot",
            )
        data = part.get("data") if isinstance(part.get("data"), dict) else {}
        if data:
            append_row(
                part,
                asset_kind="structured_data",
                asset_ref=f"data:{part_id}",
                source="report_part",
                title=f"{part_id} structured data",
                payload_keys=sorted(str(key) for key in data.keys()),
                management_use="machine-readable backing data for regeneration or audit",
            )
        for chart in list(part.get("charts") or []):
            kind = _clean_text(chart.get("kind"))
            if not kind:
                continue
            append_row(
                part,
                asset_kind="image",
                asset_ref=f"chart:{kind}",
                source="chart",
                title=_clean_text(chart.get("title")) or kind,
                payload_keys=sorted(str(key) for key in chart.keys()),
                management_use="chart or image asset with management interpretation",
            )
        for table in list(part.get("tables") or []):
            title = _clean_text(table.get("title"))
            append_row(
                part,
                asset_kind="table",
                asset_ref=f"table:{title or part_id}",
                source="table",
                title=title or f"{part_id} table",
                payload_keys=_list_text(table.get("columns")),
                management_use="tabular evidence or appendix-ready output",
            )

        evidence_refs = set(_list_text(part.get("evidence_refs")))
        attached = 0
        for asset in method_execution_assets:
            slots = set(_list_text(asset.get("report_slots")))
            asset_refs = set(_list_text(asset.get("evidence_refs")))
            if part_id not in slots and not evidence_refs.intersection(asset_refs):
                continue
            payload = asset.get("payload") if isinstance(asset.get("payload"), dict) else {}
            runtime_handoff = asset.get("runtime_handoff") if isinstance(asset.get("runtime_handoff"), dict) else {}
            payload_keys = sorted(str(key) for key in payload.keys())
            if runtime_handoff:
                payload_keys.append("runtime_handoff")
            asset_type = _clean_text(asset.get("asset_type")) or "execution_contract"
            append_row(
                part,
                asset_kind=_method_asset_kind(asset_type),
                asset_ref=_clean_text(asset.get("asset_ref")) or f"method_asset:{_clean_text(asset.get('method_id'))}",
                source="method_execution_asset",
                title=_clean_text(asset.get("method_id")) or asset_type,
                payload_keys=payload_keys,
                management_use=f"{asset_type} reusable by report-slot generator",
            )
            attached += 1
            if attached >= method_asset_limit_per_part:
                break

    return rows


def build_report_parts(
    *,
    request_part: str,
    dataset_name: str,
    sheet_name: str,
    field_profiles: list[dict[str, Any]],
    derived_fields: list[dict[str, Any]],
    selected: dict[str, Any],
    charts: list[dict[str, Any]],
    tables: list[dict[str, Any]],
    routed_methods: list[dict[str, Any]],
    method_execution_tables: list[dict[str, Any]] | None = None,
    evidence_tables: list[dict[str, Any]] | None = None,
    field_semantic_route_plan: dict[str, Any] | None = None,
    registry_total: int,
    quadrant_counts: dict[str, int],
) -> list[dict[str, Any]]:
    dataset_label = dataset_name or Z["current_dataset"]
    sheet_label = sheet_name or Z["current_sheet"]
    role_counts = _role_counts(field_profiles)
    method_execution_tables = list(method_execution_tables or [])
    evidence_tables = list(evidence_tables or [])
    routed_method_rows = [
        {
            "method_id": method.get("id"),
            "family": method.get("family"),
            "score": method.get("route_score"),
            "reasons": ", ".join(method.get("route_reasons") or []),
            "binding_quality": method.get("binding_quality"),
            "executor_hint": method.get("executor_hint"),
            "bound_fields": ", ".join(f"{key}={value}" for key, value in dict(method.get("field_bindings") or {}).items()),
            "report_slots": ", ".join(method.get("report_slots") or []),
        }
        for method in routed_methods[:12]
    ]
    field_relationship_tables = _tables_by_title(tables, Z["field_relationship_graph"])
    semantic_route_tables = _tables_by_title(tables, Z["field_semantic_route_plan"])
    semantic_route_plan = dict(field_semantic_route_plan or {})
    pre_method_audit_tables = _tables_by_title(tables, Z["pre_method_audit_table"])
    method_route_evidence_tables = _tables_by_title(tables, Z["method_route_evidence_table"])
    evidence_refs = ["table:field_profiles", "table:derived_fields", "table:selected_fields", "table:pre_method_routing_audit", "table:field_semantic_route_plan", "table:field_relationship_graph", "table:method_route_evidence", "table:method_card_execution_results", "table:method_card_execution_assets", "chart:bubble", "chart:quadrant", "chart:scatter", "chart:histogram", "chart:correlation_heatmap", "chart:time_series", "chart:forecast", "chart:cluster", "chart:anomaly", "table:forecast_risk_summary", "table:cluster_profile", "table:anomaly_top_n", "table:driver_hypotheses", "table:time_series_diagnostics", "table:causal_candidate_paths", "table:causal_light_executor_results", "table:action_priority_scores", "data:routed_methods", "data:method_route_evidence", "data:method_card_executions", "data:method_execution_assets", "data:field_semantic_route_plan", "data:field_relationships"]
    visual_cards = [{"chart_title": chart.get("title"), "chart_kind": chart.get("kind"), "management_interpretation": _chart_management_interpretation(chart, quadrant_counts), "evidence_ref": f"chart:{chart.get('kind')}"} for chart in charts]
    action_rows = [{"quadrant": quadrant, "count": int(count), "recommended_action": QUADRANT_ACTIONS.get(quadrant, "diagnose first")} for quadrant, count in sorted(quadrant_counts.items())]
    action_priority_rows = _action_priority_rows(evidence_tables)
    parts = [
        {"id": "executive_summary", "title": REPORT_PART_TITLES["executive_summary"], "narrative": f"{dataset_label}/{sheet_label}: {Z['executive_narrative']}", "bullets": [f"字段数={len(field_profiles)}，派生字段={len(derived_fields)}，语义路由字段={semantic_route_plan.get('field_count', 0)}，候选方法={registry_total}，入选方法={len(routed_methods)}", f"字段角色：指标={role_counts['measure']}，维度={role_counts['dimension']}，时间={role_counts['time']}，对象={role_counts['entity']}", f"图表数={len(charts)}；目标指标={_clean_text(selected.get('target')) or Z['unknown']}"], "tables": [], "charts": [], "data": {"selected_fields": selected, "role_counts": role_counts, "field_semantic_route_plan": semantic_route_plan}, "evidence_refs": evidence_refs[:7]},
        {"id": "chapter", "title": REPORT_PART_TITLES["chapter"], "narrative": Z["chapter_narrative"], "bullets": ["field roles first", "derived fields before method routing", "route by report part and field availability"], "tables": tables[:3], "charts": charts, "data": {"selected_fields": selected, "visual_cards": visual_cards}, "evidence_refs": evidence_refs},
        {"id": "visual_gallery", "title": REPORT_PART_TITLES["visual_gallery"], "narrative": Z["visual_narrative"], "bullets": [item["management_interpretation"] for item in visual_cards], "tables": ([tables[3]] if len(tables) > 3 else []) + evidence_tables, "charts": charts, "data": {"visual_cards": visual_cards}, "evidence_refs": evidence_refs[3:20]},
        {"id": "appendix", "title": REPORT_PART_TITLES["appendix"], "narrative": Z["appendix_narrative"], "bullets": ["field_profiles", "derived_fields", "field_relationship_graph", "routed_methods"], "tables": tables, "charts": [], "data": {"routed_methods": routed_methods[:30]}, "evidence_refs": evidence_refs},
        {"id": "method_note", "title": REPORT_PART_TITLES["method_note"], "narrative": Z["method_note_narrative"], "bullets": ["先完成字段口径与派生指标整理，再选择分析方法", "方法目录可扩展，但进入报告的证据必须可解释", "每个入选方法都保留选择原因和证据来源", "方法卡片会绑定具体字段、输出资产和报告位置", "方法执行结果会导出为可复用的数据、图片和说明文件"], "tables": [*pre_method_audit_tables, *method_route_evidence_tables, {"title": Z["route_table"], "columns": ["method_id", "family", "score", "reasons", "binding_quality", "executor_hint", "bound_fields", "report_slots"], "rows": routed_method_rows}, *method_execution_tables], "charts": [], "data": {"route_policy": "pre-method audit + priority + field-role feasibility + report-part fit + output-type fit + semantic field binding + executor registry + reusable assets", "pre_method_audit": pre_method_audit_tables[0]["rows"] if pre_method_audit_tables else [], "method_route_evidence": method_route_evidence_tables[0]["rows"] if method_route_evidence_tables else [], "method_cards": [method.get("method_card") for method in routed_methods[:30] if method.get("method_card")], "method_card_executions": method_execution_tables[0]["rows"] if method_execution_tables else [], "method_execution_assets": method_execution_tables[1]["rows"] if len(method_execution_tables) > 1 else []}, "evidence_refs": ["data:routed_methods", "data:method_registry_summary", "data:method_route_evidence", "data:method_cards", "data:method_card_executions", "data:method_execution_assets", "table:pre_method_routing_audit", "table:method_route_evidence", "table:method_card_execution_results", "table:method_card_execution_assets"]},
        {"id": "field_glossary", "title": REPORT_PART_TITLES["field_glossary"], "narrative": Z["field_narrative"], "bullets": _selected_field_bullets(selected), "tables": ([tables[0]] if tables else []) + semantic_route_tables + field_relationship_tables, "charts": [], "data": {"field_profiles": field_profiles[:120], "field_semantic_route_plan": semantic_route_plan, "field_relationships": field_relationship_tables[0]["rows"] if field_relationship_tables else []}, "evidence_refs": ["table:field_profiles", "table:field_semantic_route_plan", "table:field_relationship_graph", "data:selected_fields", "data:field_semantic_route_plan", "data:field_relationships"]},
        {"id": "action_plan", "title": REPORT_PART_TITLES["action_plan"], "narrative": Z["action_narrative"], "bullets": _action_plan_bullets(action_rows, evidence_tables), "tables": [{"title": Z["quadrant_action_table"], "columns": ["quadrant", "count", "recommended_action"], "rows": action_rows}, *evidence_tables], "charts": [chart for chart in charts if chart.get("kind") == "quadrant"], "data": {"quadrant_counts": quadrant_counts, "selected_fields": selected, "action_priority_scores": action_priority_rows}, "evidence_refs": ["chart:quadrant", "table:quadrant_actions", "table:forecast_risk_summary", "table:cluster_profile", "table:anomaly_top_n", "table:driver_hypotheses", "table:time_series_diagnostics", "table:causal_candidate_paths", "table:causal_light_executor_results", "table:action_priority_scores", "data:selected_fields"]},
        {"id": "evidence_index", "title": REPORT_PART_TITLES["evidence_index"], "narrative": Z["evidence_narrative"], "bullets": evidence_refs, "tables": [{"title": Z["evidence_table"], "columns": ["evidence_id", "kind", "description"], "rows": [{"evidence_id": ref, "kind": ref.split(":", 1)[0], "description": ref.split(":", 1)[-1]} for ref in evidence_refs]}], "charts": [], "data": {"evidence_refs": evidence_refs}, "evidence_refs": evidence_refs},
    ]
    requested = _clean_text(request_part) or "auto"
    requested_parts = set(normalize_report_part_ids(requested))
    if requested == "auto" and len(requested_parts) == len(REPORT_PART_TITLES):
        return parts
    matched = [part for part in parts if part["id"] in requested_parts]
    return matched or parts
