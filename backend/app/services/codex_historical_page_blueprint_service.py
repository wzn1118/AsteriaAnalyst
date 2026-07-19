from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


VISUAL_PAGE_ROLES = {
    "thesis_chart_page": "diagnostic_exhibit",
    "comparison_matrix_page": "comparison_exhibit",
    "kpi_scorecard_page": "scorecard_exhibit",
    "funnel_diagnosis_page": "driver_exhibit",
    "scatter_diagnosis_page": "relationship_exhibit",
    "heatmap_leverage_page": "relationship_exhibit",
    "ranking_table_page": "ranked_detail_exhibit",
    "summary_map_page": "action_synthesis_exhibit",
    "appendix_glossary_page": "method_or_definition_exhibit",
    "appendix_detail_table_page": "detail_table_exhibit",
    "collage_preference_page": "collage_synthesis_exhibit",
    "toc_navigation_page": "navigation_exhibit",
    "module_divider_page": "transition_exhibit",
    "cover_page": "opening_cover",
}


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig", errors="ignore")
    except Exception:
        return ""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(_read_text(path))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def _clean(value: Any, *, fallback: str = "") -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip())
    return text or fallback


def _sequence(page_plan: dict[str, Any]) -> list[dict[str, Any]]:
    raw = page_plan.get("page_type_sequence")
    if isinstance(raw, list):
        return [dict(item) if isinstance(item, dict) else {"title": str(item)} for item in raw]
    return []


def _visual_regions_for_page(visual_semantic_spec: dict[str, Any], index: int) -> dict[str, Any]:
    regions = dict(visual_semantic_spec.get("layout_region_contract") or {})
    if not regions:
        return {}
    return {
        "title": regions.get("title_region_norm") or [],
        "primary_visual": regions.get("primary_visual_region_norm") or [],
        "right_annotation": regions.get("right_annotation_region_norm") or [],
        "narrative": regions.get("narrative_region_norm") or [],
        "footer": regions.get("footer_region_norm") or [],
        "source_page_template_index": index,
    }


def _norm_box(value: Any) -> list[float]:
    if not isinstance(value, list) or len(value) != 4:
        return []
    try:
        box = [max(0.0, min(1.0, float(item))) for item in value]
    except Exception:
        return []
    if box[2] <= box[0] or box[3] <= box[1]:
        return []
    return [round(item, 4) for item in box]


def _profile_layout_regions(profile: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": _norm_box(profile.get("title_box_norm")),
        "primary_visual": _norm_box(profile.get("primary_visual_box_norm")),
        "right_annotation": _norm_box(profile.get("right_annotation_box_norm")),
        "narrative": _norm_box(profile.get("narrative_box_norm")),
        "footer": _norm_box(profile.get("footer_box_norm")),
        "source_page_template_index": int(profile.get("source_page_number") or 0),
    }


def _mode_for_template(template: str) -> str:
    if template in {"ranking_table_page", "comparison_matrix_page", "appendix_detail_table_page", "appendix_glossary_page", "kpi_scorecard_page"}:
        return "table_dense"
    if template in {"summary_map_page", "collage_preference_page", "toc_navigation_page", "module_divider_page"}:
        return "collage_grid"
    if template in {"cover_page"}:
        return "visual_only"
    return "visual_with_right_annotation"


def _profile_score(profile: dict[str, Any], *, template: str, desired_mode: str, index: int) -> tuple[float, str]:
    modes = {str(item) for item in list(profile.get("allowed_renderer_modes") or [])}
    role = str(profile.get("dominant_page_role_guess") or "")
    density = str(profile.get("density_class") or "")
    source_page = int(profile.get("source_page_number") or 0)
    score = 0.0
    reasons: list[str] = []
    if desired_mode in modes:
        score += 5.0
        reasons.append(f"mode:{desired_mode}")
    if desired_mode == "collage_grid" and ("visual_only" in modes or "visual_then_lower_narrative" in modes):
        score += 2.0
        reasons.append("collage-compatible")
    if desired_mode == "table_dense" and ("table" in role or density == "dense"):
        score += 4.0
        reasons.append("dense-table-source")
    if desired_mode == "visual_with_right_annotation" and float(profile.get("right_annotation_width_ratio") or 0) >= 0.12:
        score += 4.0
        reasons.append("right-annotation-space")
    if template == "cover_page" and source_page == 1:
        score += 6.0
        reasons.append("source-cover")
    if template != "cover_page" and source_page > 1:
        score += 1.0
    score += max(0.0, 2.0 - abs((source_page or index) - index) * 0.25)
    if float(profile.get("visual_area_ratio") or 0) >= 0.34:
        score += 1.0
    return score, ", ".join(reasons) or "nearest-region-profile"


def _match_source_region_profile(
    *,
    template: str,
    index: int,
    profiles: list[dict[str, Any]],
    visual_semantic_spec: dict[str, Any],
) -> dict[str, Any]:
    desired_mode = _mode_for_template(template)
    if not profiles:
        return {
            "source_region_profile_id": "",
            "source_page_match_reason": "missing_source_region_profile_pack",
            "visual_region_mode": desired_mode,
            "region_layout_contract": {
                "layout_regions": _visual_regions_for_page(visual_semantic_spec, index),
                "fallback_reason": "source_region_profile_pack_missing",
            },
        }
    scored = [
        (*_profile_score(profile, template=template, desired_mode=desired_mode, index=index), profile)
        for profile in profiles
    ]
    scored.sort(key=lambda item: item[0], reverse=True)
    score, reason, profile = scored[0]
    regions = _profile_layout_regions(profile)
    mode = desired_mode if desired_mode in set(profile.get("allowed_renderer_modes") or []) else str((profile.get("allowed_renderer_modes") or [desired_mode])[0])
    if float(profile.get("right_annotation_width_ratio") or 0) >= 0.12 and desired_mode != "visual_only":
        mode = "visual_with_right_annotation"
    return {
        "source_region_profile_id": str(profile.get("source_region_profile_id") or ""),
        "source_page_match_reason": reason,
        "visual_region_mode": mode,
        "region_layout_contract": {
            "source_region_profile_id": str(profile.get("source_region_profile_id") or ""),
            "source_page_number": int(profile.get("source_page_number") or 0),
            "layout_regions": regions,
            "visual_region_mode": mode,
            "page_aspect": float(profile.get("page_aspect") or 0),
            "right_annotation_width_ratio": float(profile.get("right_annotation_width_ratio") or 0),
            "visual_area_ratio": float(profile.get("visual_area_ratio") or 0),
            "title_to_visual_gap": float(profile.get("title_to_visual_gap") or 0),
            "visual_to_narrative_gap": float(profile.get("visual_to_narrative_gap") or 0),
            "footer_height_ratio": float(profile.get("footer_height_ratio") or 0),
            "density_class": str(profile.get("density_class") or ""),
            "match_score": round(float(score), 4),
            "match_reason": reason,
        },
    }


def _match_source_chart_profile(
    *,
    index: int,
    template: str,
    region_contract: dict[str, Any],
    profiles: list[dict[str, Any]],
) -> dict[str, Any]:
    if template == "cover_page":
        return {
            "source_chart_grammar_profile_id": "",
            "required_chart_kind": "",
            "fallback_chart_kinds": [],
            "chart_similarity_contract": {},
            "source_chart_match_reason": "cover_page_has_no_required_chart",
        }
    if not profiles:
        return {
            "source_chart_grammar_profile_id": "",
            "required_chart_kind": "",
            "fallback_chart_kinds": [],
            "chart_similarity_contract": {"fallback_reason": "source_chart_grammar_profile_pack_missing"},
            "source_chart_match_reason": "missing_source_chart_grammar_profile_pack",
        }
    source_page = int(region_contract.get("source_page_number") or 0)
    exact = [profile for profile in profiles if int(profile.get("source_page_number") or 0) == source_page]
    if exact:
        profile = exact[0]
        reason = f"matched_source_region_page:{source_page}"
    else:
        profile = profiles[(index - 1) % len(profiles)]
        reason = "nearest_source_chart_profile"
    return {
        "source_chart_grammar_profile_id": str(profile.get("source_chart_grammar_profile_id") or ""),
        "required_chart_kind": str(profile.get("required_chart_kind") or profile.get("primary_chart_kind") or ""),
        "fallback_chart_kinds": list(profile.get("fallback_chart_kinds") or []),
        "chart_similarity_contract": profile.get("chart_similarity_contract") if isinstance(profile.get("chart_similarity_contract"), dict) else {},
        "source_chart_match_reason": reason,
        "source_chart_primitive_scores": profile.get("primitive_scores") if isinstance(profile.get("primitive_scores"), dict) else {},
    }


def _asset_requirements(template: str, chart_grammar_contract: dict[str, Any]) -> dict[str, Any]:
    renderer_contract = dict(chart_grammar_contract.get("renderer_contract") or {})
    preferred = list(renderer_contract.get("preferred_asset_kinds") or chart_grammar_contract.get("preferred_chart_kinds") or [])
    if template in {"cover_page"}:
        return {"primary_visual_required": False, "allowed_asset_types": [], "preferred_renderer_kinds": []}
    if template in {"toc_navigation_page", "module_divider_page", "summary_map_page", "collage_preference_page"}:
        return {"primary_visual_required": True, "allowed_asset_types": ["collage", "table", "chart"], "preferred_renderer_kinds": ["summary_map", "module_collage_grid", *preferred]}
    if template in {"ranking_table_page", "comparison_matrix_page", "appendix_glossary_page", "appendix_detail_table_page", "kpi_scorecard_page"}:
        return {"primary_visual_required": True, "allowed_asset_types": ["table", "collage", "chart"], "preferred_renderer_kinds": ["matrix_table_with_group_headers", "kpi_strip_with_commentary", *preferred]}
    return {"primary_visual_required": True, "allowed_asset_types": ["chart", "table", "collage"], "preferred_renderer_kinds": preferred or ["paired_horizontal_bar_with_right_delta", "matrix_table_with_group_headers", "kpi_strip_with_commentary"]}


def write_historical_page_blueprint_contract(
    *,
    workspace: Path,
    page_plan_path: Path,
    source_logic_blueprint_path: Path,
    visual_semantic_spec_path: Path,
    chart_grammar_contract_path: Path,
    data_storyline_scan_path: Path,
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Build a per-page execution contract before rendering assets into a deck."""

    page_plan = _read_json(page_plan_path)
    logic = _read_json(source_logic_blueprint_path)
    visual_semantic_spec = _read_json(visual_semantic_spec_path)
    chart_grammar = _read_json(chart_grammar_contract_path)
    storyline = _read_json(data_storyline_scan_path)
    region_profile_pack = _read_json(workspace / "historical_source_region_profile_pack.json")
    region_profiles = [
        profile for profile in list(region_profile_pack.get("profiles") or [])
        if isinstance(profile, dict)
    ]
    chart_profile_pack = _read_json(workspace / "source_chart_grammar_profile_pack.json")
    chart_profiles = [
        profile for profile in list(chart_profile_pack.get("profiles") or [])
        if isinstance(profile, dict)
    ]
    sequence = _sequence(page_plan)
    if not sequence:
        sequence = [
            {"page_template_type": "cover_page", "title": _clean(storyline.get("headline_data_story"), fallback="历史报告复刻分析")},
            {"page_template_type": "thesis_chart_page", "title": _clean(storyline.get("headline_data_story"), fallback="核心经营信号需要用图表验证")},
            {"page_template_type": "summary_map_page", "title": "行动摘要地图"},
        ]
    action_candidates = list(storyline.get("action_candidates") or [])
    metric_priorities = list(storyline.get("metric_priorities") or [])
    dimension_priorities = list(storyline.get("dimension_priorities") or [])
    pages: list[dict[str, Any]] = []
    for index, item in enumerate(sequence, start=1):
        template = _clean(item.get("page_template_type") or item.get("template_type") or item.get("type"), fallback="thesis_chart_page")
        title = _clean(item.get("title") or item.get("headline") or item.get("page_title"), fallback=f"Page {index}")
        requirements = _asset_requirements(template, chart_grammar)
        metric_ref = metric_priorities[(index - 1) % len(metric_priorities)] if metric_priorities else {}
        dim_ref = dimension_priorities[(index - 1) % len(dimension_priorities)] if dimension_priorities else {}
        action_ref = action_candidates[(index - 1) % len(action_candidates)] if action_candidates else {}
        region_match = _match_source_region_profile(
            template=template,
            index=index,
            profiles=region_profiles,
            visual_semantic_spec=visual_semantic_spec,
        )
        region_contract = dict(region_match.get("region_layout_contract") or {})
        chart_match = _match_source_chart_profile(
            index=index,
            template=template,
            region_contract=region_contract,
            profiles=chart_profiles,
        )
        if chart_match.get("required_chart_kind"):
            requirements["required_chart_kind"] = chart_match.get("required_chart_kind")
            requirements["fallback_chart_kinds"] = list(chart_match.get("fallback_chart_kinds") or [])
        pages.append(
            {
                "page_number": index,
                "page_role": VISUAL_PAGE_ROLES.get(template, "diagnostic_exhibit"),
                "page_template_type": template,
                "source_region_profile_id": str(region_match.get("source_region_profile_id") or ""),
                "source_page_match_reason": str(region_match.get("source_page_match_reason") or ""),
                "visual_region_mode": str(region_match.get("visual_region_mode") or ""),
                "region_layout_contract": region_contract,
                "layout_regions": region_contract.get("layout_regions") if isinstance(region_contract.get("layout_regions"), dict) else _visual_regions_for_page(visual_semantic_spec, index),
                "visual_grammar_id": str((dict(chart_grammar.get("renderer_contract") or {})).get("chart_grammar_id") or chart_grammar.get("dominant_chart_grammar") or "source_derived_exhibit"),
                "source_chart_grammar_profile_id": str(chart_match.get("source_chart_grammar_profile_id") or ""),
                "source_chart_match_reason": str(chart_match.get("source_chart_match_reason") or ""),
                "required_chart_kind": str(chart_match.get("required_chart_kind") or ""),
                "fallback_chart_kinds": list(chart_match.get("fallback_chart_kinds") or []),
                "chart_similarity_contract": chart_match.get("chart_similarity_contract") if isinstance(chart_match.get("chart_similarity_contract"), dict) else {},
                "source_chart_primitive_scores": chart_match.get("source_chart_primitive_scores") if isinstance(chart_match.get("source_chart_primitive_scores"), dict) else {},
                "required_data_assets": requirements,
                "claim": title,
                "evidence_refs": [
                    _clean(metric_ref.get("metric") if isinstance(metric_ref, dict) else metric_ref),
                    _clean(dim_ref.get("dimension") if isinstance(dim_ref, dict) else dim_ref),
                ],
                "action_implication": _clean(
                    action_ref.get("action") if isinstance(action_ref, dict) else action_ref,
                    fallback=_clean(item.get("management_thesis"), fallback=title),
                ),
                "source_logic_markers": list(logic.get("logic_markers") or []),
                "must_not_render_as_bullets_only": template != "cover_page",
            }
        )
    payload = {
        "page_blueprint_contract_version": "source-derived-page-blueprint-v1",
        "workspace_path": str(workspace.resolve()),
        "family_is_diagnostic_only": True,
        "page_count": len(pages),
        "pages": pages,
        "source_region_profile_pack": {
            "path": str((workspace / "historical_source_region_profile_pack.json").resolve()),
            "profile_count": len(region_profiles),
            "renderer_mode_counts": region_profile_pack.get("renderer_mode_counts") if isinstance(region_profile_pack.get("renderer_mode_counts"), dict) else {},
        },
        "source_chart_grammar_profile_pack": {
            "path": str((workspace / "source_chart_grammar_profile_pack.json").resolve()),
            "profile_count": len(chart_profiles),
            "required_chart_kind_counts": chart_profile_pack.get("required_chart_kind_counts") if isinstance(chart_profile_pack.get("required_chart_kind_counts"), dict) else {},
        },
        "quality_contract": {
            "non_cover_pages_require_primary_visual": True,
            "bullet_only_page_allowed": False,
            "missing_primary_visual_is_blocker": True,
            "placeholder_copy_is_blocker": True,
        },
    }
    target = output_path or workspace / "page_blueprint_contract.json"
    _write_json(target, payload)
    return payload


def _asset_has_visual(asset: dict[str, Any]) -> bool:
    path = str(asset.get("path") or asset.get("file_name") or "").lower()
    kind = str(asset.get("kind") or asset.get("asset_type") or "").lower()
    insight = asset.get("insight_input")
    return bool(path and (path.endswith((".svg", ".html", ".htm", ".png", ".jpg", ".jpeg")))) and (
        isinstance(insight, dict) and bool(insight)
        or kind in {"bar", "heatmap", "paired_horizontal_bar", "table", "collage", "summary_map", "matrix"}
    )


def _load_assets(path: Path, asset_type: str) -> list[dict[str, Any]]:
    payload = _read_json(path)
    assets: list[dict[str, Any]] = []
    for item in list(payload.get("assets") or []):
        if isinstance(item, dict) and _asset_has_visual(item):
            assets.append({**item, "asset_type": asset_type})
    return assets


def _chart_kind_aliases(kind: str) -> set[str]:
    normalized = str(kind or "").strip().lower()
    alias_groups = [
        {"right_labeled_index_line", "indexed_multi_line", "line", "indexed_trend"},
        {"paired_horizontal_bar_with_delta", "paired_horizontal_bar", "horizontal_bar", "bar"},
        {"matrix_table_with_group_headers", "table_grid", "heatmap", "matrix", "table"},
        {"grouped_bar", "vertical_bar", "bar", "pareto"},
        {"scatter_quadrant", "scatter", "portfolio_matrix"},
        {"stacked_bar_share", "share_map", "donut", "bar"},
        {"waterfall", "waterfall_bridge", "value_bridge"},
    ]
    for group in alias_groups:
        if normalized in group:
            return set(group)
    return {normalized} if normalized else set()


def _chart_match_score(asset: dict[str, Any], page: dict[str, Any]) -> tuple[float, str]:
    required = str(page.get("required_chart_kind") or "").strip().lower()
    fallback = {str(item or "").strip().lower() for item in list(page.get("fallback_chart_kinds") or []) if str(item or "").strip()}
    asset_kind = str(asset.get("kind") or "").strip().lower()
    if not required or str(asset.get("asset_type") or "") != "chart":
        return 0.5, "not_chart_contract_page"
    if asset_kind == required or asset_kind in _chart_kind_aliases(required):
        return 1.0, "required_chart_kind_match"
    fallback_aliases: set[str] = set()
    for item in fallback:
        fallback_aliases.update(_chart_kind_aliases(item))
    if asset_kind in fallback or asset_kind in fallback_aliases:
        return 0.75, "fallback_chart_kind_match"
    tokens = asset.get("visual_contract_tokens") if isinstance(asset.get("visual_contract_tokens"), dict) else {}
    required_profiles = {
        str(item or "")
        for item in list(tokens.get("source_chart_grammar_profile_ids") or [])
        if str(item or "").strip()
    }
    if str(page.get("source_chart_grammar_profile_id") or "") in required_profiles:
        return 0.85, "source_chart_profile_id_match"
    return 0.0, "chart_kind_mismatch"


def write_historical_visual_asset_manifest(
    *,
    workspace: Path,
    page_blueprint_contract_path: Path,
    chart_assets_index_path: Path,
    table_assets_index_path: Path,
    collage_assets_index_path: Path,
    output_path: Path | None = None,
) -> dict[str, Any]:
    blueprint = _read_json(page_blueprint_contract_path)
    assets_by_type = {
        "chart": _load_assets(chart_assets_index_path, "chart"),
        "table": _load_assets(table_assets_index_path, "table"),
        "collage": _load_assets(collage_assets_index_path, "collage"),
    }
    pages = [page for page in list(blueprint.get("pages") or []) if isinstance(page, dict)]
    missing_pages: list[int] = []
    visual_bindings: list[dict[str, Any]] = []
    for page in pages:
        page_number = int(page.get("page_number") or 0)
        requirements = dict(page.get("required_data_assets") or {})
        if not bool(requirements.get("primary_visual_required")):
            continue
        allowed = [str(item) for item in list(requirements.get("allowed_asset_types") or [])]
        candidates: list[dict[str, Any]] = []
        for asset_type in allowed or ["chart", "table", "collage"]:
            candidates.extend(assets_by_type.get(asset_type, []))
        if not candidates:
            missing_pages.append(page_number)
            continue
        candidates = sorted(candidates, key=lambda candidate: _chart_match_score(candidate, page)[0], reverse=True)
        asset = candidates[0]
        chart_score, chart_reason = _chart_match_score(asset, page)
        visual_bindings.append(
            {
                "page_number": page_number,
                "asset_id": str(asset.get("asset_id") or asset.get("chart_id") or asset.get("table_id") or asset.get("file_name") or ""),
                "asset_type": str(asset.get("asset_type") or ""),
                "renderer_kind": str(asset.get("kind") or ""),
                "source_chart_grammar_profile_id": str(page.get("source_chart_grammar_profile_id") or ""),
                "required_chart_kind": str(page.get("required_chart_kind") or ""),
                "fallback_chart_kinds": list(page.get("fallback_chart_kinds") or []),
                "chart_type_match_score": round(chart_score, 4),
                "chart_type_match_reason": chart_reason,
                "path": str(asset.get("path") or ""),
                "title": str(asset.get("title") or ""),
            }
        )
    failed_chart_bindings = [
        int(binding.get("page_number") or 0)
        for binding in visual_bindings
        if str(binding.get("required_chart_kind") or "")
        and float(binding.get("chart_type_match_score") or 0) < 0.65
        and str(binding.get("asset_type") or "") == "chart"
    ]
    payload = {
        "visual_asset_manifest_version": "source-derived-visual-assets-v1",
        "workspace_path": str(workspace.resolve()),
        "asset_counts": {key: len(value) for key, value in assets_by_type.items()},
        "total_visual_asset_count": sum(len(value) for value in assets_by_type.values()),
        "page_visual_bindings": visual_bindings,
        "missing_primary_visual_page_numbers": missing_pages,
        "failed_chart_grammar_page_numbers": failed_chart_bindings,
        "passes_visual_asset_gate": not missing_pages and not failed_chart_bindings,
        "quality_contract": {
            "bullet_fallback_for_visual_assets_allowed": False,
            "table_or_collage_without_insight_allowed": False,
        },
    }
    target = output_path or workspace / "visual_asset_manifest.json"
    _write_json(target, payload)
    return payload
