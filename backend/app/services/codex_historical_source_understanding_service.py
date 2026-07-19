from __future__ import annotations

import json
import re
import colorsys
from pathlib import Path
from typing import Any


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


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _hex(rgb: tuple[int, int, int]) -> str:
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def _mix_with_white(rgb: tuple[int, int, int], amount: float = 0.86) -> str:
    amount = min(0.98, max(0.0, amount))
    mixed = tuple(int(round(channel * (1 - amount) + 255 * amount)) for channel in rgb)
    return _hex(mixed)


def _infer_palette_from_previews(preview_paths: list[str]) -> dict[str, Any]:
    """Infer source colors from rendered PDF pages.

    The upstream visual reference may provide a generic palette. This helper
    samples the actual source-page screenshots so rendering can follow the PDF
    instead of a family/default style token.
    """

    try:
        from PIL import Image
    except Exception:
        return {}

    buckets: dict[tuple[int, int, int], int] = {}
    neutral_buckets: dict[tuple[int, int, int], int] = {}
    for raw_path in preview_paths[:4]:
        path = Path(raw_path)
        if not path.exists():
            continue
        try:
            with Image.open(path) as image:
                image = image.convert("RGB")
                width, height = image.size
                if width > 220:
                    height = max(1, int(height * (220 / width)))
                    image = image.resize((220, height))
                for red, green, blue in image.getdata():
                    high = max(red, green, blue)
                    low = min(red, green, blue)
                    saturation = high - low
                    luminance = 0.299 * red + 0.587 * green + 0.114 * blue
                    if luminance > 246:
                        continue
                    rounded = (round(red / 16) * 16, round(green / 16) * 16, round(blue / 16) * 16)
                    rounded = tuple(max(0, min(255, int(value))) for value in rounded)
                    if saturation >= 24 and luminance < 230:
                        buckets[rounded] = buckets.get(rounded, 0) + 1
                    elif saturation < 18 and 35 <= luminance <= 180:
                        neutral_buckets[rounded] = neutral_buckets.get(rounded, 0) + 1
        except Exception:
            continue
    if not buckets and not neutral_buckets:
        return {}

    def _hue(rgb: tuple[int, int, int]) -> float:
        red, green, blue = [channel / 255 for channel in rgb]
        hue, _sat, _val = colorsys.rgb_to_hsv(red, green, blue)
        return hue * 360

    def _hue_distance(left: tuple[int, int, int], right: tuple[int, int, int]) -> float:
        distance = abs(_hue(left) - _hue(right))
        return min(distance, 360 - distance)

    def _luminance(rgb: tuple[int, int, int]) -> float:
        red, green, blue = rgb
        return 0.299 * red + 0.587 * green + 0.114 * blue

    def _is_greenish(rgb: tuple[int, int, int]) -> bool:
        hue = _hue(rgb)
        return 72 <= hue <= 176

    def _is_warm(rgb: tuple[int, int, int]) -> bool:
        hue = _hue(rgb)
        return hue <= 58 or hue >= 330

    def _pick_diverse_series(items: list[tuple[tuple[int, int, int], int]], *, limit: int = 6) -> list[tuple[int, int, int]]:
        selected: list[tuple[int, int, int]] = []
        for rgb, _count in sorted(items, key=_accent_score, reverse=True):
            luminance = _luminance(rgb)
            if luminance < 34 or luminance > 236:
                continue
            if all(_hue_distance(rgb, existing) >= 16 for existing in selected):
                selected.append(rgb)
            if len(selected) >= limit:
                break
        if len(selected) < limit:
            for rgb, _count in sorted(items, key=_accent_score, reverse=True):
                if rgb not in selected:
                    selected.append(rgb)
                if len(selected) >= limit:
                    break
        return selected[:limit]
    def _accent_score(item: tuple[tuple[int, int, int], int]) -> float:
        (red, green, blue), count = item
        high = max(red, green, blue)
        low = min(red, green, blue)
        saturation = high - low
        luminance = _luminance((red, green, blue))
        darkness = max(0.12, (255 - luminance) / 255)
        return count * (saturation / 255) * (darkness ** 1.35)

    def _neutral_score(item: tuple[tuple[int, int, int], int]) -> float:
        (red, green, blue), count = item
        luminance = _luminance((red, green, blue))
        return count * max(0.1, (190 - luminance) / 190)

    ranked_accents = sorted(buckets.items(), key=_accent_score, reverse=True)
    series = _pick_diverse_series(ranked_accents)
    accent = series[0] if series else (12, 126, 86)
    neutral = max(neutral_buckets.items(), key=_neutral_score)[0] if neutral_buckets else (74, 74, 74)
    neutral_luminance = _luminance(neutral)
    if neutral_luminance > 165:
        neutral = (74, 74, 74)
    positive = next((rgb for rgb in series if _is_greenish(rgb)), accent)
    negative = next((rgb for rgb in series if _is_warm(rgb)), None)
    if negative is None:
        negative = next((rgb for rgb in series[1:] if _hue_distance(rgb, positive) >= 42), (176, 87, 56))
    secondary = series[1] if len(series) > 1 else negative
    table_header = _mix_with_white(accent, 0.78)
    table_header_stronger = _mix_with_white(accent, 0.68)
    return {
        "background": "#ffffff",
        "accent": _hex(accent),
        "accent_soft": _mix_with_white(accent),
        "secondary": _hex(secondary),
        "secondary_soft": _mix_with_white(secondary),
        "positive_delta": _hex(positive),
        "negative_delta": _hex(negative),
        "table_header_fill": table_header,
        "table_header_strong_fill": table_header_stronger,
        "footnote_gray": "#6f7377",
        "series_palette": [_hex(item) for item in series],
        "secondary_palette": [_hex(item) for item in series[1:]],
        "text": _hex(neutral),
        "heading": _hex(accent),
        "muted": "#8a8a8a",
        "rule": "#d6d6d6",
        "palette_source": "pdf_preview_pixels",
    }


def _source_pdf_palette_tokens(visual_reference: dict[str, Any]) -> dict[str, Any]:
    """Prefer source-derived palette roles over coarse screenshot re-sampling.

    `historical_visual_reference.json` already contains role-aware colors such
    as accent, series palette, delta colors, and table fills. Those are closer
    to the source PDF than the fallback preview sampler, so they should be the
    canonical semantic tokens used by downstream renderers.
    """

    contract = _as_dict(visual_reference.get("style_transfer_contract"))
    colors = dict(_as_dict(contract.get("colors")))
    signature = _as_dict(visual_reference.get("visual_style_signature"))
    candidates = [
        _as_dict(visual_reference.get("source_palette_roles")),
        _as_dict(signature.get("source_palette_roles")),
        colors,
    ]
    merged = dict(colors)
    for candidate in candidates:
        for key, value in candidate.items():
            if value not in (None, "", [], {}):
                merged[key] = value
    if merged:
        merged.setdefault("background", "#ffffff")
        merged.setdefault("text", "#4a4a4a")
        merged.setdefault("heading", merged.get("accent") or "#4a4a4a")
        merged.setdefault("muted", "#8a8a8a")
        merged.setdefault("rule", "#d6d6d6")
        merged.setdefault("palette_source", "pdf_preview_pixels")
    return merged


def _box_area(box: Any) -> float:
    if not isinstance(box, list) or len(box) != 4:
        return 0.0
    try:
        x0, y0, x1, y1 = [float(item) for item in box]
    except Exception:
        return 0.0
    return max(0.0, x1 - x0) * max(0.0, y1 - y0)


def _logic_lines(text: str) -> list[str]:
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    return [line for line in lines if line]


def _sentence_style(lines: list[str]) -> dict[str, Any]:
    if not lines:
        return {
            "avg_line_chars": 0,
            "answer_first_likelihood": 0.0,
            "source_footer_likelihood": 0.0,
            "numeric_evidence_likelihood": 0.0,
            "paragraph_density": "unknown",
        }
    lengths = [len(line) for line in lines]
    numeric_lines = sum(1 for line in lines if re.search(r"\d|%|pct|bps|倍|元|万|亿", line, flags=re.I))
    source_lines = sum(1 for line in lines if re.search(r"\b(source|note|notes|copyright)\b|来源|注：|资料来源", line, flags=re.I))
    claim_lines = sum(1 for line in lines[: min(10, len(lines))] if len(line) >= 16 and re.search(r"增长|下降|领先|落后|分化|驱动|需要|应|机会|风险|优先|修复|increase|decline|growth|shift|must|should", line, flags=re.I))
    avg = sum(lengths) / max(1, len(lengths))
    return {
        "avg_line_chars": round(avg, 2),
        "answer_first_likelihood": round(min(1.0, claim_lines / max(1, min(5, len(lines))))),
        "source_footer_likelihood": round(min(1.0, source_lines / max(1, len(lines) * 0.12)), 4),
        "numeric_evidence_likelihood": round(min(1.0, numeric_lines / max(1, len(lines) * 0.45)), 4),
        "paragraph_density": "dense" if avg >= 52 else ("sparse" if avg < 24 else "moderate"),
    }


def build_source_page_observations(
    *,
    workspace: Path,
    visual_reference_path: Path,
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Compile PDF-native visual observations into a renderer-neutral contract."""

    visual_reference = _read_json(visual_reference_path)
    contract = _as_dict(visual_reference.get("style_transfer_contract"))
    region_features = _as_dict(visual_reference.get("visual_region_features"))
    primitive_features = _as_dict(visual_reference.get("visual_primitive_features"))
    regions = dict(_as_dict(contract.get("regions")) or {})
    if region_features:
        regions["pages"] = list(regions.get("pages") or region_features.get("pages") or [])
        regions["average_regions"] = {
            **dict(region_features.get("average_regions") or {}),
            **dict(regions.get("average_regions") or {}),
        }
        for key in (
            "right_annotation_column_likelihood",
            "two_column_narrative_likelihood",
            "title_region_norm",
            "primary_visual_region_norm",
            "right_annotation_region_norm",
            "narrative_region_norm",
            "footer_region_norm",
            "margin_norm",
        ):
            if key not in regions and key in region_features:
                regions[key] = region_features.get(key)
    if not regions:
        regions = region_features
    primitives = dict(_as_dict(contract.get("visual_primitives")) or {})
    if primitive_features:
        primitives["pages"] = list(primitives.get("pages") or primitive_features.get("pages") or [])
        for key, value in primitive_features.items():
            if key not in primitives:
                primitives[key] = value
    if not primitives:
        primitives = primitive_features
    chart_style = _as_dict(contract.get("chart_style"))
    typography = _as_dict(contract.get("typography"))
    colors = _source_pdf_palette_tokens(visual_reference) or _as_dict(contract.get("colors"))
    preview_paths = [str(path) for path in list(visual_reference.get("preview_image_paths") or []) if str(path).strip()]
    inferred_colors = _infer_palette_from_previews(preview_paths)
    if inferred_colors:
        if str(colors.get("palette_source") or "") == "pdf_preview_pixels":
            colors = {**inferred_colors, **colors}
        else:
            colors = {**colors, **inferred_colors}
    region_pages = [
        page for page in list(regions.get("pages") or [])
        if isinstance(page, dict)
    ]
    primitive_pages = {
        int(page.get("page") or page.get("source_page_number") or 0): page
        for page in list(primitives.get("pages") or [])
        if isinstance(page, dict)
    }
    pages: list[dict[str, Any]] = []
    fallback_regions = dict(regions.get("average_regions") or {})
    chart_contract = _as_dict(primitives.get("chart_grammar_contract")) or _as_dict(chart_style.get("chart_grammar_contract"))
    average_primitives = {
        key: primitives.get(key)
        for key in (
            "dominant_visual_grammar",
            "horizontal_bar_likelihood",
            "paired_bar_likelihood",
            "table_grid_likelihood",
            "right_numeric_column_likelihood",
            "axis_likelihood",
            "legend_likelihood",
            "gridline_density",
            "line_chart_likelihood",
            "scatter_likelihood",
            "donut_or_pie_likelihood",
        )
        if key in primitives
    }
    for key in (
        "dominant_chart_grammar",
        "horizontal_bar_likelihood",
        "table_grid_likelihood",
        "right_numeric_column_likelihood",
        "axis_likelihood",
        "legend_likelihood",
        "gridline_density",
        "line_chart_likelihood",
        "scatter_likelihood",
        "donut_or_pie_likelihood",
    ):
        if key in chart_contract and key not in average_primitives:
            average_primitives[key] = chart_contract.get(key)
    for index, preview in enumerate(preview_paths or [""], start=1):
        region = region_pages[index - 1] if index - 1 < len(region_pages) else {}
        primitive = primitive_pages.get(index, {})
        layout_regions = {
            "title": region.get("title_region_norm") or fallback_regions.get("title_region_norm") or [],
            "primary_visual": region.get("primary_visual_region_norm") or fallback_regions.get("primary_visual_region_norm") or [],
            "right_annotation": region.get("right_annotation_region_norm") or fallback_regions.get("right_annotation_region_norm") or [],
            "narrative": region.get("narrative_region_norm") or fallback_regions.get("narrative_region_norm") or [],
            "footer": region.get("footer_region_norm") or fallback_regions.get("footer_region_norm") or [],
        }
        pages.append(
            {
                "source_page_number": index,
                "preview_path": str(Path(preview).resolve()) if preview else "",
                "layout_regions": layout_regions,
                "visual_area_ratio": round(_box_area(layout_regions["primary_visual"]), 4),
                "right_annotation_likelihood": float(region.get("right_annotation_column_likelihood") or fallback_regions.get("right_annotation_column_likelihood") or 0),
                "two_column_narrative_likelihood": float(region.get("two_column_narrative_likelihood") or fallback_regions.get("two_column_narrative_likelihood") or 0),
                "ink_ratio": float(region.get("ink_ratio") or fallback_regions.get("ink_ratio") or 0),
                "colored_ink_ratio": float(region.get("colored_ink_ratio") or fallback_regions.get("colored_ink_ratio") or 0),
                "detected_visual_primitives": {
                    key: primitive.get(key, average_primitives.get(key))
                    for key in (
                        "horizontal_bar_likelihood",
                        "paired_bar_likelihood",
                        "table_grid_likelihood",
                        "right_numeric_column_likelihood",
                        "axis_likelihood",
                        "footer_line_count",
                    )
                    if key in primitive
                },
            }
        )
    payload = {
        "source_page_observations_version": "pdf-native-observations-v1",
        "workspace_path": str(workspace.resolve()),
        "source_is_real_pdf": bool(visual_reference.get("source_is_real_pdf")),
        "source_page_count": int(visual_reference.get("source_page_count") or len(pages)),
        "preview_page_count": int(visual_reference.get("preview_page_count") or len(preview_paths)),
        "family_debug_label": str(visual_reference.get("historical_report_family_hint") or ""),
        "family_is_diagnostic_only": True,
        "render_decisions_must_use": [
            "color_tokens",
            "typography_tokens",
            "layout_regions",
            "visual_primitives",
            "chart_grammar_contract",
        ],
        "color_tokens": colors,
        "typography_tokens": typography,
        "page_tokens": _as_dict(contract.get("page")),
        "layout_tokens": _as_dict(contract.get("layout")),
        "furniture_tokens": _as_dict(contract.get("furniture")),
        "visual_primitives": {
            "available": bool(primitives),
            "dominant_visual_grammar": primitives.get("dominant_visual_grammar") or chart_contract.get("dominant_chart_grammar") or chart_style.get("dominant_chart_grammar"),
            "chart_grammar_contract": chart_contract,
            "average_primitives": average_primitives,
            "pages": list(primitives.get("pages") or []),
        },
        "average_regions": fallback_regions,
        "pages": pages,
    }
    target = output_path or workspace / "source_page_observations.json"
    _write_json(target, payload)
    return payload


def build_source_logic_blueprint(
    *,
    workspace: Path,
    historical_text_excerpt_path: Path,
    current_report_context_path: Path | None = None,
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Extract source-report writing logic without copying source facts."""

    text = _read_text(historical_text_excerpt_path)
    current_context = _read_json(current_report_context_path) if current_report_context_path else {}
    lines = _logic_lines(text)
    style = _sentence_style(lines)
    source_like_lines = [line for line in lines if re.search(r"\b(source|note|notes)\b|来源|注：|资料来源", line, flags=re.I)]
    title_like_lines = [
        line for line in lines[:80]
        if 10 <= len(line) <= 110 and not re.search(r"\b(source|note|copyright)\b|来源|注：", line, flags=re.I)
    ][:20]
    claim_markers = [
        marker for marker in [
            "answer_first_title",
            "claim_evidence_action",
            "numbered_exhibit",
            "source_footer",
            "short_dense_caption",
            "management_implication",
        ]
        if (
            marker == "source_footer" and source_like_lines
        )
        or (
            marker == "numbered_exhibit" and re.search(r"\b(exhibit|figure)\s*\d+", text, flags=re.I)
        )
        or (
            marker in {"answer_first_title", "claim_evidence_action", "management_implication"} and style["answer_first_likelihood"] >= 0.2
        )
        or (
            marker == "short_dense_caption" and style["paragraph_density"] in {"moderate", "dense"}
        )
    ]
    payload = {
        "source_logic_blueprint_version": "text-logic-blueprint-v1",
        "workspace_path": str(workspace.resolve()),
        "dataset_name": str(current_context.get("dataset_name") or ""),
        "title_sentence_patterns": title_like_lines,
        "claim_evidence_action_rhythm": {
            "claim_position": "title_or_first_line",
            "evidence_position": "primary_visual_or_table",
            "action_position": "right_annotation_or_lower_narrative",
            "must_not_copy_source_facts": True,
        },
        "source_footer_rules": {
            "sample_lines": source_like_lines[:8],
            "required": bool(source_like_lines),
            "reader_visible_internal_source_forbidden": True,
        },
        "paragraph_density": style["paragraph_density"],
        "terminology_style": {
            "numeric_evidence_likelihood": style["numeric_evidence_likelihood"],
            "answer_first_likelihood": style["answer_first_likelihood"],
            "source_footer_likelihood": style["source_footer_likelihood"],
        },
        "logic_markers": claim_markers,
        "quality_rules": [
            "Every content page needs a claim, evidence refs, and action implication.",
            "No page may explain that the historical PDF is only used for style reversal.",
            "No bullet-only visual fallback is allowed.",
        ],
    }
    target = output_path or workspace / "source_logic_blueprint.json"
    _write_json(target, payload)
    return payload


def build_visual_semantic_spec(
    *,
    workspace: Path,
    source_page_observations_path: Path,
    source_logic_blueprint_path: Path,
    output_path: Path | None = None,
) -> dict[str, Any]:
    observations = _read_json(source_page_observations_path)
    logic = _read_json(source_logic_blueprint_path)
    visual_reference = _read_json(workspace / "historical_visual_reference.json")
    contract = _as_dict(visual_reference.get("style_transfer_contract"))
    colors = {
        **dict(observations.get("color_tokens") or {}),
        **_source_pdf_palette_tokens(visual_reference),
    }
    typography = dict(observations.get("typography_tokens") or {})
    page_tokens = dict(observations.get("page_tokens") or {})
    layout_tokens = {
        **dict(observations.get("layout_tokens") or {}),
        **_as_dict(contract.get("layout")),
    }
    furniture_tokens = {
        **dict(observations.get("furniture_tokens") or {}),
        **_as_dict(contract.get("furniture")),
    }
    visual_primitives = dict(observations.get("visual_primitives") or {})
    chart_style = _as_dict(contract.get("chart_style"))
    chart_grammar_contract = (
        _as_dict(chart_style.get("chart_grammar_contract"))
        or _as_dict(visual_primitives.get("chart_grammar_contract"))
        or _as_dict(_as_dict(visual_primitives.get("average_primitives")).get("chart_grammar_contract"))
    )
    average_primitives = _as_dict(visual_primitives.get("average_primitives"))
    chart_grammar_tokens = {
        "dominant_chart_grammar": (
            chart_style.get("dominant_chart_grammar")
            or chart_grammar_contract.get("dominant_chart_grammar")
            or visual_primitives.get("dominant_visual_grammar")
            or average_primitives.get("dominant_chart_grammar")
            or ""
        ),
        "chart_grammar_tokens": list(
            chart_style.get("chart_grammar_tokens")
            or chart_grammar_contract.get("chart_grammar_tokens")
            or []
        ),
        "preferred_chart_kinds": list(
            chart_style.get("preferred_chart_kinds")
            or chart_grammar_contract.get("preferred_chart_kinds")
            or []
        ),
        "avoid_chart_kinds": list(
            chart_style.get("avoid_chart_kinds")
            or chart_grammar_contract.get("avoid_chart_kinds")
            or []
        ),
        "axis_likelihood": float(chart_style.get("axis_likelihood") or chart_grammar_contract.get("axis_likelihood") or average_primitives.get("axis_likelihood") or 0),
        "legend_likelihood": float(chart_style.get("legend_likelihood") or chart_grammar_contract.get("legend_likelihood") or average_primitives.get("legend_likelihood") or 0),
        "gridline_density": float(chart_style.get("gridline_density") or chart_grammar_contract.get("gridline_density") or average_primitives.get("gridline_density") or 0),
        "horizontal_bar_likelihood": float(chart_grammar_contract.get("horizontal_bar_likelihood") or average_primitives.get("horizontal_bar_likelihood") or 0),
        "line_chart_likelihood": float(chart_grammar_contract.get("line_chart_likelihood") or average_primitives.get("line_chart_likelihood") or 0),
        "scatter_likelihood": float(chart_grammar_contract.get("scatter_likelihood") or average_primitives.get("scatter_likelihood") or 0),
        "table_grid_likelihood": float(chart_style.get("table_grid_likelihood") or average_primitives.get("table_grid_likelihood") or 0),
        "right_numeric_column_likelihood": float(chart_style.get("right_numeric_column_likelihood") or chart_grammar_contract.get("right_numeric_column_likelihood") or average_primitives.get("right_numeric_column_likelihood") or 0),
        "contract_source": "historical_visual_reference.style_transfer_contract.chart_style",
    }
    pages = [page for page in list(observations.get("pages") or []) if isinstance(page, dict)]
    visual_ratios = [float(page.get("visual_area_ratio") or 0) for page in pages]
    right_annotation_pages = sum(1 for page in pages if float(page.get("right_annotation_likelihood") or 0) >= 0.16)
    section_presence = {
        "color_tokens": bool(colors),
        "page_tokens": bool(page_tokens),
        "layout_tokens": bool(layout_tokens),
        "furniture_tokens": bool(furniture_tokens),
        "visual_primitives": bool(visual_primitives),
        "chart_grammar_tokens": bool(chart_grammar_tokens.get("dominant_chart_grammar") or chart_grammar_tokens.get("preferred_chart_kinds")),
        "layout_region_contract": bool(observations.get("average_regions")),
        "text_logic_contract": bool(logic),
    }
    coverage_score = round(
        sum(1 for enabled in section_presence.values() if enabled) / max(1, len(section_presence)),
        4,
    )
    payload = {
        "visual_semantic_spec_version": "source-derived-render-contract-v2",
        "workspace_path": str(workspace.resolve()),
        "family_debug_label": str(observations.get("family_debug_label") or ""),
        "family_is_diagnostic_only": True,
        "rendering_decision_basis": "source_page_observations + source_logic_blueprint + historical_visual_reference.style_transfer_contract",
        "source_is_real_pdf": bool(observations.get("source_is_real_pdf") or visual_reference.get("source_is_real_pdf")),
        "source_page_count": int(observations.get("source_page_count") or visual_reference.get("source_page_count") or len(pages)),
        "color_tokens": colors,
        "typography_tokens": typography,
        "page_tokens": page_tokens,
        "layout_tokens": layout_tokens,
        "furniture_tokens": furniture_tokens,
        "visual_primitives": visual_primitives,
        "chart_grammar_tokens": chart_grammar_tokens,
        "layout_region_contract": dict(observations.get("average_regions") or {}),
        "page_visual_density": {
            "avg_primary_visual_area_ratio": round(sum(visual_ratios) / max(1, len(visual_ratios)), 4),
            "right_annotation_page_ratio": round(right_annotation_pages / max(1, len(pages)), 4),
            "source_page_count": int(observations.get("source_page_count") or len(pages)),
        },
        "text_logic_contract": {
            "claim_evidence_action_rhythm": dict(logic.get("claim_evidence_action_rhythm") or {}),
            "source_footer_rules": dict(logic.get("source_footer_rules") or {}),
            "paragraph_density": str(logic.get("paragraph_density") or ""),
            "logic_markers": list(logic.get("logic_markers") or []),
        },
        "page_contract_rules": [
            "cover pages may be visual-light; every other generated page needs a primary visual component.",
            "chart/table/collage assets must be renderer-native visual blocks, never bullet-only text.",
            "renderer must use color_tokens and layout_region_contract, not a hard-coded family branch.",
            "color tokens must preserve source PDF palette roles; preview re-sampling may fill missing values but must not override source role colors.",
            "chart grammar tokens must be present for real-PDF sources and must guide asset selection before any family label.",
        ],
        "semantic_coverage": {
            "score": coverage_score,
            "section_presence": section_presence,
            "blocking_threshold_for_real_pdf": 0.75,
        },
        "source_artifacts": {
            "source_page_observations_path": str(source_page_observations_path.resolve()),
            "source_logic_blueprint_path": str(source_logic_blueprint_path.resolve()),
            "historical_visual_reference_path": str((workspace / "historical_visual_reference.json").resolve()),
        },
    }
    target = output_path or workspace / "visual_semantic_spec.json"
    _write_json(target, payload)
    return payload


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


def _box_width(box: list[float]) -> float:
    return max(0.0, float(box[2] - box[0])) if len(box) == 4 else 0.0


def _box_height(box: list[float]) -> float:
    return max(0.0, float(box[3] - box[1])) if len(box) == 4 else 0.0


def _box_gap(upper: list[float], lower: list[float]) -> float:
    if len(upper) != 4 or len(lower) != 4:
        return 0.0
    return round(max(0.0, lower[1] - upper[3]), 4)


def _density_class(page: dict[str, Any], *, visual_area: float, right_width: float) -> str:
    ink_ratio = float(page.get("ink_ratio") or 0)
    if visual_area >= 0.46 or ink_ratio >= 0.18:
        return "dense"
    if visual_area <= 0.24 and right_width <= 0.08:
        return "sparse"
    return "moderate"


def _role_guess(
    *,
    source_page_number: int,
    visual_area: float,
    right_width: float,
    footer_height: float,
    primitive: dict[str, Any],
) -> str:
    if source_page_number == 1 and visual_area < 0.36:
        return "cover_or_opening"
    table_grid = float(primitive.get("table_grid_likelihood") or 0)
    horizontal_bar = float(primitive.get("horizontal_bar_likelihood") or 0)
    right_numeric = float(primitive.get("right_numeric_column_likelihood") or 0)
    if table_grid >= 0.55 and visual_area >= 0.34:
        return "dense_table_or_matrix_exhibit"
    if horizontal_bar >= 0.35 and right_numeric >= 0.35:
        return "bar_exhibit_with_right_delta"
    if right_width >= 0.14:
        return "exhibit_with_right_annotation"
    if footer_height >= 0.035:
        return "source_footer_exhibit"
    return "general_exhibit"


def _renderer_modes(
    *,
    role_guess: str,
    right_width: float,
    visual_area: float,
    primitive: dict[str, Any],
) -> list[str]:
    modes: list[str] = []
    if visual_area >= 0.25:
        modes.append("visual_only")
    if right_width >= 0.12:
        modes.append("visual_with_right_annotation")
    if float(primitive.get("table_grid_likelihood") or 0) >= 0.45 or "table" in role_guess:
        modes.append("table_dense")
    if float(primitive.get("right_numeric_column_likelihood") or 0) >= 0.35:
        modes.append("visual_with_right_delta")
    if not modes:
        modes.append("visual_then_lower_narrative")
    if "general_exhibit" in role_guess and "visual_then_lower_narrative" not in modes:
        modes.append("visual_then_lower_narrative")
    return modes


def build_source_region_profile_pack(
    *,
    workspace: Path,
    source_page_observations_path: Path,
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Compile source PDF page regions into per-page renderer profiles.

    This keeps the per-page layout proportions intact so downstream layout and
    render stages do not collapse the source PDF into one average CSS grid.
    """

    observations = _read_json(source_page_observations_path)
    pages = [page for page in list(observations.get("pages") or []) if isinstance(page, dict)]
    page_tokens = dict(observations.get("page_tokens") or {})
    width = float(page_tokens.get("width_mm") or 210)
    height = float(page_tokens.get("height_mm") or 297)
    page_aspect = round(width / max(1.0, height), 4)
    profiles: list[dict[str, Any]] = []
    for index, page in enumerate(pages, start=1):
        regions = dict(page.get("layout_regions") or {})
        title = _norm_box(regions.get("title"))
        primary_visual = _norm_box(regions.get("primary_visual"))
        right_annotation = _norm_box(regions.get("right_annotation"))
        narrative = _norm_box(regions.get("narrative"))
        footer = _norm_box(regions.get("footer"))
        primitive = dict(page.get("detected_visual_primitives") or {})
        visual_area = round(_box_area(primary_visual), 4)
        right_width = round(_box_width(right_annotation), 4)
        footer_height = round(_box_height(footer), 4)
        source_page_number = int(page.get("source_page_number") or index)
        role_guess = _role_guess(
            source_page_number=source_page_number,
            visual_area=visual_area,
            right_width=right_width,
            footer_height=footer_height,
            primitive=primitive,
        )
        density = _density_class(page, visual_area=visual_area, right_width=right_width)
        profile_id = f"source-page-{source_page_number:02d}"
        profiles.append(
            {
                "source_region_profile_id": profile_id,
                "source_page_number": source_page_number,
                "preview_path": str(page.get("preview_path") or ""),
                "page_aspect": page_aspect,
                "title_box_norm": title,
                "primary_visual_box_norm": primary_visual,
                "right_annotation_box_norm": right_annotation,
                "narrative_box_norm": narrative,
                "footer_box_norm": footer,
                "title_to_visual_gap": _box_gap(title, primary_visual),
                "visual_to_narrative_gap": _box_gap(primary_visual, narrative),
                "right_annotation_width_ratio": right_width,
                "footer_height_ratio": footer_height,
                "visual_area_ratio": visual_area,
                "density_class": density,
                "dominant_page_role_guess": role_guess,
                "allowed_renderer_modes": _renderer_modes(
                    role_guess=role_guess,
                    right_width=right_width,
                    visual_area=visual_area,
                    primitive=primitive,
                ),
                "detected_visual_primitives": primitive,
            }
        )
    mode_counts: dict[str, int] = {}
    for profile in profiles:
        for mode in list(profile.get("allowed_renderer_modes") or []):
            mode_counts[str(mode)] = mode_counts.get(str(mode), 0) + 1
    payload = {
        "source_region_profile_pack_version": "source-region-profile-pack-v1",
        "workspace_path": str(workspace.resolve()),
        "source_page_count": int(observations.get("source_page_count") or len(profiles)),
        "profile_count": len(profiles),
        "family_is_diagnostic_only": True,
        "page_aspect": page_aspect,
        "profiles": profiles,
        "renderer_mode_counts": mode_counts,
        "quality_contract": {
            "renderer_must_bind_each_generated_page": True,
            "global_average_regions_are_fallback_only": True,
            "source_family_must_not_drive_layout": True,
        },
    }
    target = output_path or workspace / "historical_source_region_profile_pack.json"
    _write_json(target, payload)
    return payload
