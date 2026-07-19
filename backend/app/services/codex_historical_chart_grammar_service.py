from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _chart_style(visual_reference: dict[str, Any]) -> dict[str, Any]:
    contract = visual_reference.get("style_transfer_contract")
    if not isinstance(contract, dict):
        return {}
    chart_style = contract.get("chart_style")
    return chart_style if isinstance(chart_style, dict) else {}


def build_historical_chart_grammar_spec(
    *,
    visual_reference_payload: dict[str, Any],
    visual_reverse_spec_v2: dict[str, Any] | None = None,
) -> dict[str, Any]:
    chart_style = _chart_style(visual_reference_payload)
    grammar_contract = chart_style.get("chart_grammar_contract")
    if not isinstance(grammar_contract, dict):
        grammar_contract = {}
    dominant = str(
        chart_style.get("dominant_chart_grammar")
        or grammar_contract.get("dominant_chart_grammar")
        or "chart_or_text_exhibit"
    )
    preferred = [
        str(item)
        for item in list(chart_style.get("preferred_chart_kinds") or [])
        + list(grammar_contract.get("preferred_chart_kinds") or [])
        if str(item).strip()
    ]
    if dominant == "paired_horizontal_bar_matrix":
        renderer_contract = {
            "chart_grammar_id": "bcg_paired_horizontal_bar_right_delta",
            "required_regions": ["title", "primary_visual", "right_numeric_annotation", "source_footer"],
            "preferred_asset_kinds": ["paired_horizontal_bar", "heatmap", "bar", "table_grid"],
            "required_exhibit_features": [
                "answer_first_title",
                "grouped_horizontal_bars",
                "right_delta_or_index_column",
                "thin_source_footer",
            ],
        }
    else:
        renderer_contract = {
            "chart_grammar_id": f"{dominant or 'generic'}_exhibit",
            "required_regions": ["title", "primary_visual", "source_footer"],
            "preferred_asset_kinds": preferred or ["bar", "heatmap", "table_grid"],
            "required_exhibit_features": ["answer_first_title", "source_footer"],
        }
    pages = list((visual_reverse_spec_v2 or {}).get("pages") or [])
    return {
        "chart_grammar_spec_version": "historical-chart-grammar-v1",
        "chart_grammar_contract_version": "source-derived-chart-grammar-contract-v1",
        "family_is_diagnostic_only": True,
        "dominant_chart_grammar": dominant,
        "preferred_chart_kinds": sorted(set(preferred or renderer_contract["preferred_asset_kinds"])),
        "avoid_chart_kinds": list(chart_style.get("avoid_chart_kinds") or grammar_contract.get("avoid_chart_kinds") or []),
        "renderer_contract": renderer_contract,
        "source_page_chart_grammar": [
            {
                "source_page_number": int(page.get("source_page_number") or index),
                "chart_grammar_id": renderer_contract["chart_grammar_id"],
                "layout_regions": page.get("layout_regions") if isinstance(page, dict) else {},
            }
            for index, page in enumerate(pages, start=1)
            if isinstance(page, dict)
        ],
    }


def write_historical_chart_grammar_spec(
    *,
    workspace: Path,
    visual_reference_path: Path,
    visual_reverse_spec_v2_path: Path | None = None,
    output_path: Path | None = None,
) -> dict[str, Any]:
    visual_reference = _read_json(visual_reference_path)
    reverse_v2 = _read_json(visual_reverse_spec_v2_path) if visual_reverse_spec_v2_path and visual_reverse_spec_v2_path.exists() else {}
    payload = build_historical_chart_grammar_spec(
        visual_reference_payload=visual_reference,
        visual_reverse_spec_v2=reverse_v2,
    )
    target = output_path or workspace / "historical_chart_grammar_spec.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return payload


def write_historical_chart_grammar_contract(
    *,
    workspace: Path,
    source_page_observations_path: Path,
    visual_semantic_spec_path: Path,
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Compile chart grammar from source observations without family branches."""

    observations = _read_json(source_page_observations_path)
    visual_semantic = _read_json(visual_semantic_spec_path)
    primitives = dict(observations.get("visual_primitives") or {})
    average_primitives = dict(primitives.get("average_primitives") or primitives)
    dominant = str(average_primitives.get("dominant_visual_grammar") or "").strip()
    if not dominant:
        pages = [page for page in list(observations.get("pages") or []) if isinstance(page, dict)]
        paired = sum(
            1 for page in pages
            if float((dict(page.get("detected_visual_primitives") or {})).get("paired_bar_likelihood") or 0) >= 0.2
        )
        table = sum(
            1 for page in pages
            if float((dict(page.get("detected_visual_primitives") or {})).get("table_grid_likelihood") or 0) >= 0.25
        )
        dominant = "paired_horizontal_bar_with_right_delta" if paired else ("matrix_table_with_group_headers" if table else "source_derived_exhibit")
    primitive_to_kinds = {
        "paired_horizontal_bar_matrix": ["paired_horizontal_bar", "heatmap", "bar", "table_grid"],
        "paired_horizontal_bar_with_right_delta": ["paired_horizontal_bar", "bar", "table_grid"],
        "table_grid": ["heatmap", "table_grid", "paired_horizontal_bar"],
        "matrix_table_with_group_headers": ["heatmap", "table_grid", "paired_horizontal_bar"],
        "horizontal_bar_chart": ["bar", "paired_horizontal_bar", "pareto"],
        "vertical_bar_chart": ["vertical_bar", "histogram", "pareto"],
        "line_chart": ["line", "indexed_trend"],
        "scatter_plot": ["scatter", "scatter_quadrant", "portfolio_matrix"],
        "donut_or_pie": ["bar", "pareto", "share_map"],
        "source_derived_exhibit": ["paired_horizontal_bar", "bar", "heatmap", "table_grid"],
    }
    preferred = primitive_to_kinds.get(dominant, primitive_to_kinds["source_derived_exhibit"])
    right_annotation_ratio = float(dict(visual_semantic.get("page_visual_density") or {}).get("right_annotation_page_ratio") or 0)
    grammar_id = dominant
    if right_annotation_ratio >= 0.18 and "right_delta" not in grammar_id:
        grammar_id = f"{grammar_id}_with_right_annotation"
    payload = {
        "chart_grammar_contract_version": "source-derived-chart-grammar-contract-v1",
        "workspace_path": str(workspace.resolve()),
        "family_is_diagnostic_only": True,
        "dominant_chart_grammar": dominant,
        "renderer_contract": {
            "chart_grammar_id": grammar_id,
            "required_regions": ["title", "primary_visual", "source_footer"],
            "optional_regions": ["right_annotation", "narrative"],
            "preferred_asset_kinds": preferred,
            "required_exhibit_features": [
                "answer_first_title",
                "primary_visual_region",
                "source_footer_rhythm",
                "data_bound_annotation",
            ],
        },
        "preferred_chart_kinds": preferred,
        "avoid_chart_kinds": ["bullet_list", "all_zero_distribution", "placeholder_card"],
        "primitive_evidence": average_primitives,
        "source_page_chart_grammar": [
            {
                "source_page_number": int(page.get("source_page_number") or index),
                "chart_grammar_id": grammar_id,
                "layout_regions": page.get("layout_regions") if isinstance(page, dict) else {},
                "detected_visual_primitives": page.get("detected_visual_primitives") if isinstance(page, dict) else {},
            }
            for index, page in enumerate(list(observations.get("pages") or []), start=1)
            if isinstance(page, dict)
        ],
    }
    target = output_path or workspace / "chart_grammar_contract.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return payload


def _as_float(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return fallback


def _page_primitive_map(source_observations: dict[str, Any]) -> dict[int, dict[str, Any]]:
    """Return the richest primitive payload available for every source page."""

    output: dict[int, dict[str, Any]] = {}
    primitives = source_observations.get("visual_primitives")
    if isinstance(primitives, dict):
        for item in list(primitives.get("pages") or []):
            if not isinstance(item, dict):
                continue
            page_number = int(item.get("page") or item.get("source_page_number") or len(output) + 1)
            output[page_number] = dict(item)
    for index, item in enumerate(list(source_observations.get("pages") or []), start=1):
        if not isinstance(item, dict):
            continue
        page_number = int(item.get("source_page_number") or index)
        merged = dict(output.get(page_number) or {})
        detected = item.get("detected_visual_primitives")
        if isinstance(detected, dict):
            merged.update(detected)
        merged["layout_regions"] = item.get("layout_regions") if isinstance(item.get("layout_regions"), dict) else merged.get("layout_regions")
        merged["source_page_number"] = page_number
        output[page_number] = merged
    return output


def _classify_page_chart_profile(primitives: dict[str, Any]) -> dict[str, Any]:
    """Convert visual primitive likelihoods into an executable chart grammar."""

    horizontal = _as_float(primitives.get("horizontal_bar_likelihood"))
    paired = _as_float(primitives.get("paired_bar_likelihood"))
    vertical = _as_float(primitives.get("vertical_bar_likelihood"))
    line = _as_float(primitives.get("line_chart_likelihood"))
    scatter = _as_float(primitives.get("scatter_likelihood"))
    table = _as_float(primitives.get("table_grid_likelihood"))
    axis = _as_float(primitives.get("axis_likelihood"))
    right_numeric = _as_float(primitives.get("right_numeric_column_likelihood"))
    legend = _as_float(primitives.get("legend_likelihood"))
    gridline = _as_float(primitives.get("gridline_density"))
    # PDF previews often confuse line charts with table grids because gridlines
    # dominate the pixel structure. Treat a line signal with axes, legend/right
    # labels, and lower bar confidence as a line grammar even when table_grid is
    # high. This is the critical fix for BCG-like exhibit pages.
    if line >= 0.42 and axis >= 0.45 and horizontal < 0.62:
        required = "right_labeled_index_line" if right_numeric >= 0.45 else "indexed_multi_line"
        fallback = ["indexed_multi_line", "grouped_bar", "matrix_table_with_group_headers"]
    elif paired >= 0.55 or horizontal >= 0.55:
        required = "paired_horizontal_bar_with_delta" if right_numeric >= 0.4 else "paired_horizontal_bar"
        fallback = ["paired_horizontal_bar", "grouped_bar", "matrix_table_with_group_headers"]
    elif scatter >= 0.58 and axis >= 0.4 and horizontal < 0.55 and line < 0.42:
        required = "scatter_quadrant"
        fallback = ["scatter", "portfolio_matrix", "grouped_bar"]
    elif table >= 0.72 and horizontal < 0.34 and paired < 0.35:
        required = "matrix_table_with_group_headers"
        fallback = ["heatmap", "table_grid", "grouped_bar"]
    elif vertical >= 0.5 and axis >= 0.4:
        required = "grouped_bar"
        fallback = ["vertical_bar", "pareto", "paired_horizontal_bar"]
    elif table >= 0.55:
        required = "matrix_table_with_group_headers"
        fallback = ["heatmap", "table_grid", "paired_horizontal_bar"]
    else:
        required = "source_derived_exhibit"
        fallback = ["paired_horizontal_bar", "matrix_table_with_group_headers", "indexed_multi_line"]
    contract = {
        "required_chart_kind": required,
        "fallback_chart_kinds": fallback,
        "requires_axis": axis >= 0.35,
        "requires_right_labels": right_numeric >= 0.45,
        "requires_legend_or_series_labels": legend >= 0.25 or line >= 0.42,
        "requires_grid_or_rule_system": gridline >= 0.45 or table >= 0.55,
        "minimum_series_count": 2 if required in {"indexed_multi_line", "right_labeled_index_line", "grouped_bar"} else 1,
        "forbid_core_asset_kinds": ["histogram", "distribution_cumulative", "generic_cumulative_line"],
    }
    return {
        "primary_chart_kind": required,
        "required_chart_kind": required,
        "fallback_chart_kinds": fallback,
        "chart_similarity_contract": contract,
        "primitive_scores": {
            "horizontal_bar_likelihood": round(horizontal, 4),
            "paired_bar_likelihood": round(paired, 4),
            "vertical_bar_likelihood": round(vertical, 4),
            "line_chart_likelihood": round(line, 4),
            "scatter_likelihood": round(scatter, 4),
            "table_grid_likelihood": round(table, 4),
            "axis_likelihood": round(axis, 4),
            "right_numeric_column_likelihood": round(right_numeric, 4),
            "legend_likelihood": round(legend, 4),
            "gridline_density": round(gridline, 4),
        },
    }


def write_source_chart_grammar_profile_pack(
    *,
    workspace: Path,
    source_page_observations_path: Path,
    chart_grammar_contract_path: Path,
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Write per-source-page chart grammar profiles used by asset binding.

    The older contract had one dominant grammar for the whole PDF. This pack is
    intentionally page-level: if source page 2 is a multi-line exhibit, the
    generated page matched to source page 2 carries a line-chart requirement.
    """

    observations = _read_json(source_page_observations_path)
    chart_contract = _read_json(chart_grammar_contract_path)
    primitive_by_page = _page_primitive_map(observations)
    profiles: list[dict[str, Any]] = []
    for page_number in sorted(primitive_by_page):
        primitives = primitive_by_page[page_number]
        classified = _classify_page_chart_profile(primitives)
        profile_id = f"source-chart-page-{page_number:02d}"
        profile = {
            "source_chart_grammar_profile_id": profile_id,
            "source_page_number": page_number,
            "source_preview_path": str(primitives.get("path") or ""),
            "layout_regions": primitives.get("layout_regions") if isinstance(primitives.get("layout_regions"), dict) else {},
            "global_chart_grammar_debug": str(chart_contract.get("dominant_chart_grammar") or ""),
            **classified,
        }
        profiles.append(profile)
    kind_counts: dict[str, int] = {}
    for profile in profiles:
        kind = str(profile.get("required_chart_kind") or "")
        if kind:
            kind_counts[kind] = kind_counts.get(kind, 0) + 1
    required_kinds = sorted(kind_counts)
    payload = {
        "source_chart_grammar_profile_pack_version": "source-chart-grammar-profile-pack-v1",
        "workspace_path": str(workspace.resolve()),
        "family_is_diagnostic_only": True,
        "profile_count": len(profiles),
        "required_chart_kind_counts": kind_counts,
        "required_chart_kinds": required_kinds,
        "profiles": profiles,
        "quality_contract": {
            "core_pages_must_match_required_chart_kind": True,
            "fallback_requires_explicit_reason": True,
            "histogram_and_cumulative_line_are_appendix_only_unless_source_matches": True,
        },
    }
    target = output_path or workspace / "source_chart_grammar_profile_pack.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return payload
