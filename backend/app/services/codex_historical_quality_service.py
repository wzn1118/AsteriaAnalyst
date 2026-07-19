from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.services.codex_historical_reader_quality_gate_service import evaluate_historical_reader_quality_gate
from app.services.codex_runtime_output_guard_service import inspect_reader_facing_text


_ALLOWED_ENGLISH_TERMS = {
    "AOV",
    "BCG",
    "CEO",
    "CFO",
    "COO",
    "CAGR",
    "GMV",
    "KPI",
    "PDF",
    "ROI",
    "RFM",
    "SKU",
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


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 4)


def _template_counts(deck_layout_payload: dict[str, Any]) -> dict[str, int]:
    raw = deck_layout_payload.get("template_counts")
    if isinstance(raw, dict):
        return {str(key): int(value or 0) for key, value in raw.items()}
    counts: dict[str, int] = {}
    for page in list(deck_layout_payload.get("pages") or []):
        if isinstance(page, dict):
            key = str(page.get("page_template_type") or "").strip()
            if key:
                counts[key] = counts.get(key, 0) + 1
    return counts


def _page_type_coverage_score(
    *,
    family: str,
    template_counts: dict[str, int],
    source_page_count: int,
) -> tuple[float, list[str]]:
    if 0 < source_page_count <= 10:
        required = ["cover_page", "thesis_chart_page", "summary_map_page"]
        return_missing = [template for template in required if int(template_counts.get(template) or 0) <= 0]
        has_table_or_matrix = any(
            int(template_counts.get(template) or 0) > 0
            for template in ("comparison_matrix_page", "ranking_table_page", "kpi_scorecard_page")
        )
        if not has_table_or_matrix:
            return_missing.append("table_or_matrix_page")
        score = 1.0 - (len(return_missing) / max(1, len(required)))
        return _clamp(score), return_missing
    required = ["cover_page", "toc_navigation_page", "summary_map_page"]
    required.extend(["thesis_chart_page", "comparison_matrix_page", "ranking_table_page"])
    if source_page_count >= 12:
        required.extend(["module_divider_page", "appendix_detail_table_page"])
    missing = [template for template in required if int(template_counts.get(template) or 0) <= 0]
    score = 1.0 - (len(missing) / max(1, len(required)))
    return _clamp(score), missing


def _visual_density_score(
    *,
    planned_page_count: int,
    chart_asset_count: int,
    table_asset_count: int,
    collage_asset_count: int,
    visual_reference_payload: dict[str, Any],
) -> float:
    source_stats = dict(visual_reference_payload.get("suspected_area_stats") or {})
    source_chart_pages = int(source_stats.get("chart_like_page_count") or 0)
    source_table_pages = int(source_stats.get("table_like_page_count") or 0)
    expected_visuals = max(4, source_chart_pages + source_table_pages)
    if planned_page_count >= 20:
        expected_visuals = max(expected_visuals, 10)
    available_visuals = chart_asset_count + table_asset_count + collage_asset_count
    asset_score = available_visuals / max(1, expected_visuals)
    density_per_page = available_visuals / max(1, planned_page_count)
    page_density_score = min(1.0, density_per_page / 0.55)
    return _clamp(asset_score * 0.65 + page_density_score * 0.35)


_OBSOLETE_LANGUAGE_QUALITY_SCORE = r"""
    visible = len(re.findall(r"\S", text))
    cjk = len(re.findall(r"[\u4e00-\u9fff]", text))
    english_words = re.findall(r"\b[A-Za-z]{3,}\b", text)
    disallowed_english = [
        word
        for word in english_words
        if word.upper() not in _ALLOWED_ENGLISH_TERMS
    ]
    mojibake_matches = re.findall(r"[\ufffd]|锟|Ã|Â|æ|ç|å|鍘|鏍|缁|涓|鐨|浠", text)
    question_runs = re.findall(r"\?{2,}", text)
    cjk_ratio = cjk / max(1, visible)
    english_ratio = len("".join(disallowed_english)) / max(1, visible)
    mojibake_ratio = len(mojibake_matches) / max(1, visible)
    score = 1.0
    if cjk_ratio < 0.18:
        score -= 0.35
    score -= min(0.35, english_ratio * 2.5)
    score -= min(0.45, mojibake_ratio * 8)
    if question_runs:
        score -= min(0.2, len(question_runs) * 0.03)
    return _clamp(score), {
        "visible_char_count": visible,
        "cjk_char_count": cjk,
        "cjk_ratio": round(cjk_ratio, 4),
        "english_word_count": len(english_words),
        "disallowed_english_word_count": len(disallowed_english),
        "disallowed_english_ratio": round(english_ratio, 4),
        "mojibake_count": len(mojibake_matches),
        "mojibake_ratio": round(mojibake_ratio, 6),
        "question_run_count": len(question_runs),
        "sample_disallowed_english": disallowed_english[:20],
    }
"""


def _language_quality_score(text: str) -> tuple[float, dict[str, Any]]:
    diagnostics = inspect_reader_facing_text(
        text,
        label="historical_style_reader_facing_output",
        min_visible_chars=400,
        min_cjk_ratio=0.18,
    )
    score = 1.0
    if float(diagnostics.get("cjk_ratio") or 0) < 0.18:
        score -= 0.35
    score -= min(0.35, float(diagnostics.get("disallowed_english_ratio") or 0) * 2.5)
    if int(diagnostics.get("mojibake_count") or 0) > 0:
        score -= 0.6
    if int(diagnostics.get("placeholder_count") or 0) > 0:
        score -= 0.5
    if int(diagnostics.get("internal_path_reference_count") or 0) > 0:
        score -= 0.25
    if int(diagnostics.get("question_run_count") or 0) > 0:
        score -= min(0.2, int(diagnostics.get("question_run_count") or 0) * 0.03)
    if int(diagnostics.get("visible_char_count") or 0) < 400:
        score -= 0.35
    return _clamp(score), diagnostics


def _family_match(
    *,
    selected_family: str,
    visual_reference_payload: dict[str, Any],
) -> dict[str, Any]:
    # Family is kept only as a diagnostic label. It must not affect pass/fail
    # quality scoring or rendering decisions.
    hint = str(visual_reference_payload.get("historical_report_family_hint") or "").strip()
    return {
        "source_family_hint": hint,
        "selected_family_debug_label": selected_family,
        "family_match": "diagnostic_only",
        "family_match_score": 1.0,
        "family_is_diagnostic_only": True,
    }


def _visual_reference_match_score(
    *,
    css_text: str,
    visual_reference_payload: dict[str, Any],
    rendered_page_count: int,
) -> tuple[float, dict[str, Any]]:
    contract = visual_reference_payload.get("style_transfer_contract")
    if not isinstance(contract, dict) or not contract:
        return 0.55, {"reason": "missing_style_transfer_contract"}
    page = dict(contract.get("page") or {})
    colors = dict(contract.get("colors") or {})
    furniture = dict(contract.get("furniture") or {})
    layout = dict(contract.get("layout") or {})
    orientation = str(page.get("orientation") or "").lower()
    accent = str(colors.get("accent") or "").lower()
    expected_side_rail = bool(furniture.get("side_rail"))
    target_pages = dict(layout.get("target_pages") or {})
    css_lower = css_text.lower()
    checks: dict[str, bool] = {
        "orientation": bool(orientation and f"a4 {orientation}" in css_lower),
        "accent_color": bool(accent and accent in css_lower),
        "side_rail": ("display: none" not in css_lower) if expected_side_rail else ("display: none" in css_lower),
        "source_footer": (not furniture.get("source_note_footer")) or ("来源" in css_text or "source" in css_lower),
    }
    min_pages = int(target_pages.get("min") or 0)
    max_pages = int(target_pages.get("max") or 0)
    if min_pages:
        # Historical PDFs can be short reference samples while the adapted deck
        # expands for current-data coverage. Treat the max as a style hint, not
        # a hard blocker, so richer reports are not penalized for being longer.
        checks["page_count"] = rendered_page_count >= min_pages
    else:
        checks["page_count"] = rendered_page_count > 0
    score = sum(1 for ok in checks.values() if ok) / max(1, len(checks))
    return _clamp(score), {
        "expected_orientation": orientation,
        "expected_accent": accent,
        "expected_side_rail": expected_side_rail,
        "target_pages": target_pages,
        "checks": checks,
    }


def _chart_grammar_match_score(
    *,
    visual_reference_payload: dict[str, Any],
    chart_assets_payload: dict[str, Any],
) -> tuple[float, dict[str, Any]]:
    contract = visual_reference_payload.get("style_transfer_contract")
    if not isinstance(contract, dict):
        contract = {}
    chart_style = contract.get("chart_style")
    if not isinstance(chart_style, dict):
        chart_style = {}
    chart_grammar = chart_style.get("chart_grammar_contract")
    if not isinstance(chart_grammar, dict):
        chart_grammar = {}
    expected_mode = str(chart_style.get("chart_grammar_mode") or "").strip()
    dominant = str(chart_style.get("dominant_chart_grammar") or chart_grammar.get("dominant_chart_grammar") or "").strip()
    preferred = {
        str(item or "").strip()
        for item in list(chart_style.get("preferred_chart_kinds") or [])
        + list(chart_style.get("preferred_chart_families") or [])
        + list(chart_grammar.get("preferred_chart_kinds") or [])
        if str(item or "").strip()
    }
    assets = [item for item in list(chart_assets_payload.get("assets") or []) if isinstance(item, dict)]
    completed = [item for item in assets if str(item.get("status") or "") == "completed"]
    kinds = [str(item.get("kind") or "").strip() for item in completed]
    kind_set = set(kinds)
    matched_grammar_count = sum(
        1
        for item in completed
        if bool((item.get("visual_contract_tokens") if isinstance(item.get("visual_contract_tokens"), dict) else {}).get("matched_chart_grammar"))
    )
    dominant_kind_map = {
        "paired_horizontal_bar_matrix": {"paired_horizontal_bar", "heatmap", "table_grid", "bar"},
        "horizontal_bar_chart": {"bar", "paired_horizontal_bar", "pareto", "waterfall_bridge"},
        "vertical_bar_chart": {"vertical_bar", "histogram", "pareto", "line"},
        "line_chart": {"line", "scatter", "pareto"},
        "scatter_plot": {"scatter", "scatter_quadrant", "portfolio_matrix", "priority_bubble"},
        "table_grid": {"heatmap", "paired_horizontal_bar", "bar"},
        "donut_or_pie": {"donut", "pareto", "bar"},
    }
    expected_kinds = dominant_kind_map.get(dominant, set())
    diagnostics = {
        "expected_chart_grammar_mode": expected_mode,
        "dominant_chart_grammar": dominant,
        "preferred_chart_families": sorted(preferred),
        "expected_kind_family": sorted(expected_kinds),
        "completed_chart_count": len(completed),
        "kind_counts": {kind: kinds.count(kind) for kind in sorted(kind_set)},
        "matched_grammar_count": matched_grammar_count,
        "chart_grammar_contract": chart_grammar,
    }
    if not expected_mode and not dominant:
        return 0.75, diagnostics
    if expected_mode == "exhibit_horizontal_bar_matrix" or dominant == "paired_horizontal_bar_matrix":
        has_paired = "paired_horizontal_bar" in kind_set
        has_matrix_like = bool(kind_set & {"heatmap", "portfolio_matrix", "paired_horizontal_bar"})
        has_decorative_donut = "donut" in kind_set and "decorative_donut" in preferred
        score = 0.4 + (0.35 if has_paired else 0) + (0.2 if has_matrix_like else 0) + (0.05 if not has_decorative_donut else 0)
        return _clamp(score), diagnostics
    preferred_hits = len(kind_set & preferred)
    expected_hits = len(kind_set & expected_kinds)
    score = 0.45 + min(0.25, preferred_hits * 0.08) + min(0.22, expected_hits * 0.11) + min(0.08, matched_grammar_count * 0.02)
    return _clamp(score), diagnostics


def _visual_region_match_score(
    *,
    css_text: str,
    visual_reference_payload: dict[str, Any],
) -> tuple[float, dict[str, Any]]:
    contract = visual_reference_payload.get("style_transfer_contract")
    if not isinstance(contract, dict):
        contract = {}
    regions = contract.get("regions")
    if not isinstance(regions, dict) or not regions.get("available"):
        return 0.55, {"reason": "missing_visual_region_contract"}
    required = [
        "title_region_norm",
        "primary_visual_region_norm",
        "narrative_region_norm",
        "footer_region_norm",
    ]
    region_checks = {
        key: isinstance(regions.get(key), list) and len(regions.get(key) or []) == 4
        for key in required
    }
    css_lower = css_text.lower()
    css_checks = {
        "region_css_variables": "--region-visual-top" in css_lower and "--region-narrative-height" in css_lower,
        "absolute_title_region": ".content-page h2" in css_text and "position: absolute" in css_lower,
        "absolute_body_region": ".page-body" in css_text and "var(--region-visual-top)" in css_lower,
        "footer_region": "var(--region-footer-top)" in css_lower,
    }
    score = (
        sum(1 for ok in region_checks.values() if ok) / max(1, len(region_checks)) * 0.55
        + sum(1 for ok in css_checks.values() if ok) / max(1, len(css_checks)) * 0.45
    )
    return _clamp(score), {
        "region_contract_version": regions.get("version"),
        "region_checks": region_checks,
        "css_checks": css_checks,
        "right_annotation_column_likelihood": regions.get("right_annotation_column_likelihood"),
        "two_column_narrative_likelihood": regions.get("two_column_narrative_likelihood"),
    }


def _visual_primitive_match_score(
    *,
    visual_reference_payload: dict[str, Any],
    chart_assets_payload: dict[str, Any],
) -> tuple[float, dict[str, Any]]:
    contract = visual_reference_payload.get("style_transfer_contract")
    if not isinstance(contract, dict):
        contract = {}
    primitives = contract.get("visual_primitives")
    if not isinstance(primitives, dict) or not primitives.get("available"):
        return 0.55, {"reason": "missing_visual_primitive_contract"}
    chart_assets = [asset for asset in list(chart_assets_payload.get("assets") or []) if isinstance(asset, dict)]
    kinds = {str(asset.get("kind") or "").strip() for asset in chart_assets if str(asset.get("status") or "") == "completed"}
    dominant = str(primitives.get("dominant_visual_grammar") or "").strip()
    checks: dict[str, bool] = {
        "has_dominant_visual_grammar": bool(dominant and dominant != "unknown"),
        "has_chart_grammar_contract": isinstance(primitives.get("chart_grammar_contract"), dict)
        and bool((primitives.get("chart_grammar_contract") or {}).get("dominant_chart_grammar")),
        "has_footer_line_count": float(primitives.get("footer_line_count") or 0) > 0,
        "has_rule_or_grid_signal": float(primitives.get("horizontal_rule_count") or 0) > 0
        or float(primitives.get("table_grid_likelihood") or 0) > 0.1,
    }
    if dominant == "paired_horizontal_bar_matrix":
        checks["paired_bar_assets"] = "paired_horizontal_bar" in kinds
        checks["right_numeric_signal"] = float(primitives.get("right_numeric_column_likelihood") or 0) >= 0.18
    elif dominant == "table_grid":
        checks["matrix_or_table_assets"] = bool(kinds & {"heatmap", "paired_horizontal_bar", "bar"})
        checks["table_grid_signal"] = float(primitives.get("table_grid_likelihood") or 0) >= 0.35
    elif dominant == "vertical_bar_chart":
        checks["vertical_or_histogram_assets"] = bool(kinds & {"vertical_bar", "histogram", "pareto"})
        checks["axis_signal"] = float(primitives.get("axis_likelihood") or 0) >= 0.2
    elif dominant == "line_chart":
        checks["line_assets"] = "line" in kinds
        checks["axis_signal"] = float(primitives.get("axis_likelihood") or 0) >= 0.2
    elif dominant == "scatter_plot":
        checks["scatter_assets"] = bool(kinds & {"scatter", "scatter_quadrant", "portfolio_matrix"})
        checks["scatter_signal"] = float(primitives.get("scatter_likelihood") or 0) >= 0.25
    elif dominant == "donut_or_pie":
        checks["share_assets"] = bool(kinds & {"donut", "bar", "pareto"})
        checks["share_signal"] = float(primitives.get("donut_or_pie_likelihood") or 0) >= 0.25
    else:
        checks["has_visual_assets"] = bool(kinds)
    score = sum(1 for ok in checks.values() if ok) / max(1, len(checks))
    return _clamp(score), {
        "dominant_visual_grammar": dominant,
        "visual_primitives": primitives,
        "completed_chart_kinds": sorted(kind for kind in kinds if kind),
        "checks": checks,
    }


def _layout_harmony_match_score(
    *,
    css_text: str,
    deck_layout_payload: dict[str, Any],
    visual_reference_payload: dict[str, Any],
) -> tuple[float, dict[str, Any]]:
    contract = visual_reference_payload.get("style_transfer_contract")
    if not isinstance(contract, dict):
        contract = {}
    harmony = contract.get("layout_harmony")
    if not isinstance(harmony, dict) or not harmony:
        harmony = deck_layout_payload.get("layout_harmony") if isinstance(deck_layout_payload.get("layout_harmony"), dict) else {}
    if not harmony:
        return 0.55, {"reason": "missing_layout_harmony_contract"}
    pages = [page for page in list(deck_layout_payload.get("pages") or []) if isinstance(page, dict)]
    tagged_pages = sum(1 for page in pages if isinstance(page.get("layout_harmony"), dict))
    css_lower = css_text.lower()
    checks = {
        "has_harmony_contract": bool(harmony),
        "pages_carry_harmony_tags": tagged_pages >= max(1, int(len(pages) * 0.8)) if pages else False,
        "css_has_section_gap_var": "--layout-section-gap" in css_lower,
        "css_has_visual_text_ratio_var": "--layout-visual-text-ratio" in css_lower,
        "css_has_harmony_classes": ".harmony-" in css_lower,
        "css_has_density_classes": ".density-" in css_lower,
        "css_uses_region_grid": "grid-template-columns" in css_lower and "var(--layout-section-gap)" in css_lower,
    }
    score = sum(1 for ok in checks.values() if ok) / max(1, len(checks))
    return _clamp(score), {
        "layout_harmony": harmony,
        "tagged_page_count": tagged_pages,
        "page_count": len(pages),
        "checks": checks,
    }


def _report_logic_match_score(
    *,
    reverse_spec_payload: dict[str, Any],
    page_plan_payload: dict[str, Any],
    deck_layout_payload: dict[str, Any],
    report_logic_blueprint_payload: dict[str, Any],
    reader_text: str,
) -> tuple[float, dict[str, Any]]:
    pages = [page for page in list(deck_layout_payload.get("pages") or []) if isinstance(page, dict)]
    report_logic = dict((dict(deck_layout_payload.get("quality_metrics") or {}).get("report_logic") or {}))
    required_roles = list(report_logic.get("required_logic_roles") or [
        "opening_thesis",
        "diagnostic_evidence",
        "contrast_or_segmentation",
        "management_implication",
        "recommendation",
        "appendix_support",
    ])
    present_roles = set(str(role) for role in list(report_logic.get("present_logic_roles") or []) if str(role).strip())
    if not present_roles:
        present_roles = {str(page.get("logic_role") or "") for page in pages if str(page.get("logic_role") or "").strip()}
    role_score = len([role for role in required_roles if role in present_roles]) / max(1, len(required_roles))
    chain_pages = int(report_logic.get("claim_evidence_action_page_count") or 0)
    if not chain_pages:
        chain_pages = sum(1 for page in pages if isinstance(page.get("claim_evidence_action"), dict))
    chain_score = min(1.0, chain_pages / max(1, len(pages)))
    reverse_logic_fields = [
        reverse_spec_payload.get("logic_blueprint"),
        reverse_spec_payload.get("logic_flow_contract"),
        reverse_spec_payload.get("narrative_progression_rules"),
        reverse_spec_payload.get("claim_evidence_action_rules"),
        reverse_spec_payload.get("argument_arc"),
    ]
    reverse_score = sum(1 for item in reverse_logic_fields if bool(item)) / max(1, len(reverse_logic_fields))
    blueprint_fields = [
        report_logic_blueprint_payload.get("executive_thesis_seed"),
        report_logic_blueprint_payload.get("decision_question"),
        report_logic_blueprint_payload.get("argument_arc"),
        report_logic_blueprint_payload.get("logic_modules"),
        report_logic_blueprint_payload.get("recommendation_backbone"),
        report_logic_blueprint_payload.get("logic_quality_gates"),
    ]
    blueprint_score = sum(1 for item in blueprint_fields if bool(item)) / max(1, len(blueprint_fields))
    planned_logic_pages = [
        item
        for item in list(page_plan_payload.get("page_type_sequence") or [])
        if isinstance(item, dict) and (item.get("logic_role") or item.get("argument_step") or item.get("claim_evidence_action"))
    ]
    page_plan_score = min(1.0, len(planned_logic_pages) / max(1, len(page_plan_payload.get("page_type_sequence") or [])))
    text = str(reader_text or "")
    connector_patterns = [
        r"结论|判断|发现|启示",
        r"因为|由于|因此|所以|说明|意味着|驱动|导致",
        r"相比|对比|高于|低于|分化|差异",
        r"建议|行动|应当|需要|优先|落地|复盘",
        r"证据|数据|图表|表格|样本|指标|维度",
    ]
    connector_hits = {
        pattern: bool(re.search(pattern, text))
        for pattern in connector_patterns
    }
    connector_score = sum(1 for ok in connector_hits.values() if ok) / max(1, len(connector_hits))
    ordered_roles = [str(page.get("logic_role") or "") for page in pages]
    progression_checks = {
        "opens_with_thesis": bool(ordered_roles and ordered_roles[0] == "opening_thesis"),
        "has_evidence_before_recommendation": (
            "diagnostic_evidence" in ordered_roles
            and "recommendation" in ordered_roles
            and ordered_roles.index("diagnostic_evidence") < ordered_roles.index("recommendation")
        ),
        "has_implication_or_driver": bool({"driver_explanation", "management_implication"} & set(ordered_roles)),
        "has_appendix_after_main": (
            "appendix_support" in ordered_roles
            and ordered_roles.index("appendix_support") >= max(0, int(len(ordered_roles) * 0.55))
        ),
    }
    progression_score = sum(1 for ok in progression_checks.values() if ok) / max(1, len(progression_checks))
    score = _clamp(
        role_score * 0.25
        + chain_score * 0.2
        + reverse_score * 0.14
        + blueprint_score * 0.14
        + page_plan_score * 0.12
        + connector_score * 0.13
        + progression_score * 0.06
    )
    return score, {
        "required_logic_roles": required_roles,
        "present_logic_roles": sorted(present_roles),
        "role_score": _clamp(role_score),
        "claim_evidence_action_page_count": chain_pages,
        "chain_score": _clamp(chain_score),
        "reverse_spec_logic_score": _clamp(reverse_score),
        "report_logic_blueprint_score": _clamp(blueprint_score),
        "report_logic_blueprint_summary": {
            "argument_arc": list(report_logic_blueprint_payload.get("argument_arc") or [])[:12],
            "logic_module_count": len(list(report_logic_blueprint_payload.get("logic_modules") or [])),
            "recommendation_backbone_count": len(list(report_logic_blueprint_payload.get("recommendation_backbone") or [])),
            "decision_question": str(report_logic_blueprint_payload.get("decision_question") or "")[:400],
        },
        "page_plan_logic_score": _clamp(page_plan_score),
        "connector_score": _clamp(connector_score),
        "connector_hits": connector_hits,
        "progression_score": _clamp(progression_score),
        "progression_checks": progression_checks,
        "deck_layout_report_logic": report_logic,
    }


def build_historical_style_quality_report(
    *,
    workspace: Path,
    reverse_spec_path: Path,
    page_plan_path: Path,
    deck_layout_path: Path,
    markdown_path: Path,
    html_path: Path,
    css_path: Path,
    pdf_path: Path,
    data_manifest_path: Path,
    visual_reference_path: Path,
    chart_assets_index_path: Path,
    table_assets_index_path: Path,
    collage_assets_index_path: Path,
    rendered_page_count: int,
    output_path: Path | None = None,
) -> dict[str, Any]:
    reverse_spec_payload = _read_json(reverse_spec_path)
    page_plan_payload = _read_json(page_plan_path)
    deck_layout_payload = _read_json(deck_layout_path)
    report_logic_blueprint_payload = _read_json(workspace / "03_report_logic_blueprint.json")
    data_manifest_payload = _read_json(data_manifest_path)
    visual_reference_payload = _read_json(visual_reference_path)
    chart_assets_payload = _read_json(chart_assets_index_path)
    table_assets_payload = _read_json(table_assets_index_path)
    collage_assets_payload = _read_json(collage_assets_index_path)
    reader_quality_gate_path = workspace / "historical_reader_quality_gate.json"
    reader_quality_gate = evaluate_historical_reader_quality_gate(
        workspace=workspace,
        markdown_path=markdown_path,
        html_path=html_path,
        pdf_path=pdf_path,
        deck_layout_path=deck_layout_path,
        chart_assets_index_path=chart_assets_index_path,
        table_assets_index_path=table_assets_index_path,
        collage_assets_index_path=collage_assets_index_path,
        output_path=reader_quality_gate_path,
    )
    screenshot_quality_gate_path = workspace / "historical_screenshot_quality_gate.json"
    screenshot_quality_gate = (
        _read_json(screenshot_quality_gate_path)
        if screenshot_quality_gate_path.exists()
        else {}
    )

    template_counts = _template_counts(deck_layout_payload)
    family = str(
        deck_layout_payload.get("historical_report_family")
        or reverse_spec_payload.get("historical_report_family")
        or "generic_chinese_analysis_deck"
    )
    planned_page_count = int(deck_layout_payload.get("page_count") or len(deck_layout_payload.get("pages") or []))
    source_page_count = int(visual_reference_payload.get("source_page_count") or 0)
    chart_asset_count = int(chart_assets_payload.get("chart_count") or len(chart_assets_payload.get("assets") or []))
    table_asset_count = int(table_assets_payload.get("table_count") or len(table_assets_payload.get("assets") or []))
    collage_asset_count = int(collage_assets_payload.get("collage_count") or len(collage_assets_payload.get("assets") or []))
    data_coverage = dict((dict(deck_layout_payload.get("quality_metrics") or {}).get("data_coverage") or {}))
    data_coverage_score = float(
        data_coverage.get("data_coverage_score")
        or data_manifest_payload.get("data_coverage_score")
        or 0
    )

    page_type_score, missing_templates = _page_type_coverage_score(
        family=family,
        template_counts=template_counts,
        source_page_count=source_page_count,
    )
    visual_density = _visual_density_score(
        planned_page_count=planned_page_count,
        chart_asset_count=chart_asset_count,
        table_asset_count=table_asset_count,
        collage_asset_count=collage_asset_count,
        visual_reference_payload=visual_reference_payload,
    )
    language_text = "\n".join(
        [
            _read_text(markdown_path)[:80000],
            re.sub(r"<[^>]+>", " ", _read_text(html_path))[:80000],
        ]
    )
    language_score, language_diagnostics = _language_quality_score(language_text)
    css_text = _read_text(css_path)
    visual_semantic_payload = _read_json(workspace / "visual_semantic_spec.json")
    if isinstance(visual_semantic_payload, dict) and visual_semantic_payload.get("color_tokens"):
        merged_contract = dict(visual_reference_payload.get("style_transfer_contract") or {})
        merged_contract["colors"] = {
            **dict(merged_contract.get("colors") or {}),
            **dict(visual_semantic_payload.get("color_tokens") or {}),
        }
        visual_reference_payload = {
            **visual_reference_payload,
            "style_transfer_contract": merged_contract,
        }
    visual_reference_match_score, visual_reference_diagnostics = _visual_reference_match_score(
        css_text=css_text,
        visual_reference_payload=visual_reference_payload,
        rendered_page_count=rendered_page_count,
    )
    chart_grammar_match_score, chart_grammar_diagnostics = _chart_grammar_match_score(
        visual_reference_payload=visual_reference_payload,
        chart_assets_payload=chart_assets_payload,
    )
    visual_region_match_score, visual_region_diagnostics = _visual_region_match_score(
        css_text=css_text,
        visual_reference_payload=visual_reference_payload,
    )
    visual_primitive_match_score, visual_primitive_diagnostics = _visual_primitive_match_score(
        visual_reference_payload=visual_reference_payload,
        chart_assets_payload=chart_assets_payload,
    )
    layout_harmony_match_score, layout_harmony_diagnostics = _layout_harmony_match_score(
        css_text=css_text,
        deck_layout_payload=deck_layout_payload,
        visual_reference_payload=visual_reference_payload,
    )
    report_logic_score, report_logic_diagnostics = _report_logic_match_score(
        reverse_spec_payload=reverse_spec_payload,
        page_plan_payload=page_plan_payload,
        deck_layout_payload=deck_layout_payload,
        report_logic_blueprint_payload=report_logic_blueprint_payload,
        reader_text=language_text,
    )
    family_result = _family_match(selected_family=family, visual_reference_payload=visual_reference_payload)
    render_score = 1.0 if pdf_path.exists() and rendered_page_count > 0 else 0.0
    if planned_page_count and rendered_page_count:
        render_score = min(render_score, 1.0 - min(0.4, abs(rendered_page_count - planned_page_count) / max(10, planned_page_count) * 0.2))

    overall = _clamp(
        page_type_score * 0.2
        + visual_density * 0.17
        + _clamp(data_coverage_score) * 0.2
        + language_score * 0.17
        + visual_reference_match_score * 0.08
        + chart_grammar_match_score * 0.05
        + visual_region_match_score * 0.05
        + visual_primitive_match_score * 0.04
        + layout_harmony_match_score * 0.05
        + report_logic_score * 0.07
        + float(family_result.get("family_match_score") or 0) * 0.04
        + render_score * 0.03
    )
    blocking_issues: list[str] = []
    if overall < 0.75:
        blocking_issues.append("overall_style_score_below_0_75")
    if _clamp(data_coverage_score) < 0.7:
        blocking_issues.append("data_coverage_score_below_0_70")
    if language_score < 0.9:
        blocking_issues.append("language_quality_score_below_0_90")
    if visual_reference_match_score < 0.75:
        blocking_issues.append("visual_reference_match_score_below_0_75")
    if chart_grammar_match_score < 0.75:
        blocking_issues.append("chart_grammar_match_score_below_0_75")
    if visual_region_match_score < 0.75:
        blocking_issues.append("visual_region_match_score_below_0_75")
    if visual_primitive_match_score < 0.7:
        blocking_issues.append("visual_primitive_match_score_below_0_70")
    if layout_harmony_match_score < 0.7:
        blocking_issues.append("layout_harmony_match_score_below_0_70")
    if report_logic_score < 0.7:
        blocking_issues.append("report_logic_score_below_0_70")
    if int(language_diagnostics.get("mojibake_count") or 0) > 0:
        blocking_issues.append("mojibake_detected")
    if int(language_diagnostics.get("placeholder_count") or 0) > 0:
        blocking_issues.append("placeholder_or_filler_detected")
    if int(language_diagnostics.get("internal_path_reference_count") or 0) > 0:
        blocking_issues.append("internal_path_or_artifact_name_leaked")
    if int(language_diagnostics.get("visible_char_count") or 0) < 400:
        blocking_issues.append("reader_facing_output_too_short")
    if float(language_diagnostics.get("cjk_ratio") or 0) < 0.18:
        blocking_issues.append("reader_facing_cjk_ratio_too_low")
    if missing_templates:
        blocking_issues.append("missing_required_page_templates")
    if not bool(reader_quality_gate.get("passed")):
        blocking_issues.append("reader_quality_gate_failed")
    if screenshot_quality_gate and not bool(screenshot_quality_gate.get("passed")):
        blocking_issues.append("screenshot_quality_gate_failed")
    if float(screenshot_quality_gate.get("region_similarity_score") or 0) and float(screenshot_quality_gate.get("region_similarity_score") or 0) < 0.75:
        blocking_issues.append("region_similarity_score_below_0_75")
    if float(screenshot_quality_gate.get("right_annotation_presence_match") or 1) < 0.8:
        blocking_issues.append("right_annotation_presence_match_below_0_80")
    if int(screenshot_quality_gate.get("region_overflow_count") or 0) > 0:
        blocking_issues.append("region_layout_issues_detected")
    if int(screenshot_quality_gate.get("low_information_page_count") or 0) > 0:
        blocking_issues.append("low_information_pages_detected")
    if int(screenshot_quality_gate.get("duplicate_heading_count") or 0) > 0:
        blocking_issues.append("duplicate_visual_headings_detected")
    if int(screenshot_quality_gate.get("table_clip_issue_count") or 0) > 0:
        blocking_issues.append("table_rendering_issues_detected")
    if float(screenshot_quality_gate.get("chart_type_match_score") or 0) and float(screenshot_quality_gate.get("chart_type_match_score") or 0) < 0.75:
        blocking_issues.append("chart_type_match_score_below_0_75")
    if list(screenshot_quality_gate.get("failed_chart_grammar_page_numbers") or []):
        blocking_issues.append("chart_grammar_page_failures_detected")
    if float(screenshot_quality_gate.get("primary_asset_reuse_score") or 0) and float(screenshot_quality_gate.get("primary_asset_reuse_score") or 0) < 0.8:
        blocking_issues.append("primary_asset_reuse_score_below_0_80")
    if float(screenshot_quality_gate.get("chart_diversity_score") or 0) and float(screenshot_quality_gate.get("chart_diversity_score") or 0) < 0.7:
        blocking_issues.append("chart_diversity_score_below_0_70")
    if float(screenshot_quality_gate.get("metric_dimension_coverage_score") or 0) and float(screenshot_quality_gate.get("metric_dimension_coverage_score") or 0) < 0.7:
        blocking_issues.append("metric_dimension_coverage_score_below_0_70")
    if float(screenshot_quality_gate.get("layout_density_score") or 0) and float(screenshot_quality_gate.get("layout_density_score") or 0) < 0.7:
        blocking_issues.append("layout_density_score_below_0_70")
    if list(screenshot_quality_gate.get("overused_asset_ids") or []):
        blocking_issues.append("overused_primary_assets_detected")
    if list(screenshot_quality_gate.get("low_visual_density_page_numbers") or []):
        blocking_issues.append("low_visual_density_pages_detected")
    if list(screenshot_quality_gate.get("white_space_issue_pages") or []):
        blocking_issues.append("white_space_issue_pages_detected")
    if list(screenshot_quality_gate.get("chart_grammar_fallback_pages") or []):
        blocking_issues.append("chart_grammar_fallback_pages_detected")
    if list(screenshot_quality_gate.get("weak_logic_pages") or []):
        blocking_issues.append("weak_logic_pages_detected")
    if int(screenshot_quality_gate.get("source_page_overuse_count") or 0) > 0:
        blocking_issues.append("source_page_overuse_detected")
    if list(screenshot_quality_gate.get("reader_quality_blockers") or []):
        blocking_issues.append("reader_quality_blockers_detected")

    blocking_issues = list(dict.fromkeys(blocking_issues))

    report = {
        "quality_report_version": "historical-style-quality-v1",
        "workspace_path": str(workspace.resolve()),
        "overall_style_score": overall,
        "page_type_coverage_score": page_type_score,
        "visual_density_score": visual_density,
        "data_coverage_score": _clamp(data_coverage_score),
        "language_quality_score": language_score,
        "visual_reference_match_score": visual_reference_match_score,
        "chart_grammar_match_score": chart_grammar_match_score,
        "visual_region_match_score": visual_region_match_score,
        "visual_primitive_match_score": visual_primitive_match_score,
        "layout_harmony_match_score": layout_harmony_match_score,
        "report_logic_score": report_logic_score,
        "visual_similarity_score": float(screenshot_quality_gate.get("visual_similarity_score") or visual_reference_match_score),
        "region_similarity_score": float(screenshot_quality_gate.get("region_similarity_score") or 0),
        "right_annotation_presence_match": float(screenshot_quality_gate.get("right_annotation_presence_match") or 0),
        "region_overflow_count": int(screenshot_quality_gate.get("region_overflow_count") or 0),
        "failed_region_page_numbers": list(screenshot_quality_gate.get("failed_region_page_numbers") or []),
        "matched_source_page_numbers": list(screenshot_quality_gate.get("matched_source_page_numbers") or []),
        "page_region_scores": list(screenshot_quality_gate.get("page_region_scores") or []),
        "chart_type_match_score": float(screenshot_quality_gate.get("chart_type_match_score") or 0),
        "page_chart_grammar_scores": list(screenshot_quality_gate.get("page_chart_grammar_scores") or []),
        "failed_chart_grammar_page_numbers": list(screenshot_quality_gate.get("failed_chart_grammar_page_numbers") or []),
        "chart_fallback_reasons": list(screenshot_quality_gate.get("chart_fallback_reasons") or []),
        "primary_asset_reuse_score": float(screenshot_quality_gate.get("primary_asset_reuse_score") or 0),
        "chart_diversity_score": float(screenshot_quality_gate.get("chart_diversity_score") or 0),
        "metric_dimension_coverage_score": float(screenshot_quality_gate.get("metric_dimension_coverage_score") or 0),
        "layout_density_score": float(screenshot_quality_gate.get("layout_density_score") or 0),
        "overused_asset_ids": list(screenshot_quality_gate.get("overused_asset_ids") or []),
        "primary_asset_counts": dict(screenshot_quality_gate.get("primary_asset_counts") or {}),
        "primary_asset_family_counts": dict(screenshot_quality_gate.get("primary_asset_family_counts") or {}),
        "low_visual_density_page_numbers": list(screenshot_quality_gate.get("low_visual_density_page_numbers") or []),
        "white_space_issue_pages": list(screenshot_quality_gate.get("white_space_issue_pages") or []),
        "chart_grammar_fallback_pages": list(screenshot_quality_gate.get("chart_grammar_fallback_pages") or []),
        "weak_logic_pages": list(screenshot_quality_gate.get("weak_logic_pages") or []),
        "source_page_usage_counts": dict(screenshot_quality_gate.get("source_page_usage_counts") or {}),
        "source_page_overuse_count": int(screenshot_quality_gate.get("source_page_overuse_count") or 0),
        "reader_quality_blockers": list(screenshot_quality_gate.get("reader_quality_blockers") or []),
        "text_logic_similarity_score": report_logic_score,
        "page_blueprint_coverage_score": float(screenshot_quality_gate.get("page_blueprint_coverage_score") or 0),
        "bullet_only_page_count": int(screenshot_quality_gate.get("bullet_only_page_count") or 0),
        "missing_visual_page_count": int(screenshot_quality_gate.get("missing_visual_page_count") or 0),
        "low_information_page_count": int(screenshot_quality_gate.get("low_information_page_count") or 0),
        "duplicate_heading_count": int(screenshot_quality_gate.get("duplicate_heading_count") or 0),
        "table_clip_issue_count": int(screenshot_quality_gate.get("table_clip_issue_count") or 0),
        "failed_page_numbers": list(screenshot_quality_gate.get("failed_page_numbers") or []),
        "family_match": family_result.get("family_match"),
        "source_family_hint": family_result.get("source_family_hint"),
        "selected_family": family,
        "render_score": _clamp(render_score),
        "blocking_issues": blocking_issues,
        "passes_quality_gate": not blocking_issues,
        "reader_quality_gate": reader_quality_gate,
        "reader_quality_gate_path": str(reader_quality_gate_path.resolve()),
        "screenshot_quality_gate": screenshot_quality_gate,
        "screenshot_quality_gate_path": str(screenshot_quality_gate_path.resolve()) if screenshot_quality_gate_path.exists() else "",
        "page_metrics": {
            "source_page_count": source_page_count,
            "planned_page_count": planned_page_count,
            "rendered_page_count": rendered_page_count,
            "template_counts": template_counts,
            "missing_required_templates": missing_templates,
        },
        "asset_metrics": {
            "chart_asset_count": chart_asset_count,
            "table_asset_count": table_asset_count,
            "collage_asset_count": collage_asset_count,
        },
        "data_metrics": {
            "metric_count": int(data_manifest_payload.get("metric_count") or 0),
            "dimension_count": int(data_manifest_payload.get("dimension_count") or 0),
            "used_metric_names": list(data_coverage.get("used_metric_names") or data_manifest_payload.get("used_metric_names") or []),
            "used_dimension_names": list(data_coverage.get("used_dimension_names") or data_manifest_payload.get("used_dimension_names") or []),
        },
        "language_diagnostics": language_diagnostics,
        "visual_reference_diagnostics": visual_reference_diagnostics,
        "chart_grammar_diagnostics": chart_grammar_diagnostics,
        "visual_region_diagnostics": visual_region_diagnostics,
        "visual_primitive_diagnostics": visual_primitive_diagnostics,
        "layout_harmony_diagnostics": layout_harmony_diagnostics,
        "report_logic_diagnostics": report_logic_diagnostics,
        "visual_reference_summary": {
            "source_is_real_pdf": bool(visual_reference_payload.get("source_is_real_pdf")),
            "preview_page_count": int(visual_reference_payload.get("preview_page_count") or 0),
            "dominant_palette_hint": list(visual_reference_payload.get("dominant_palette_hint") or [])[:8],
            "visual_style_tokens": list(visual_reference_payload.get("visual_style_tokens") or [])[:20],
            "visual_style_signature": dict(visual_reference_payload.get("visual_style_signature") or {}),
            "style_transfer_contract": dict(visual_reference_payload.get("style_transfer_contract") or {}),
            "visual_region_features": dict(visual_reference_payload.get("visual_region_features") or {}),
            "visual_primitive_features": dict(visual_reference_payload.get("visual_primitive_features") or {}),
            "layout_harmony_features": dict(visual_reference_payload.get("layout_harmony_features") or {}),
            "suspected_area_stats": dict(visual_reference_payload.get("suspected_area_stats") or {}),
        },
    }
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return report
