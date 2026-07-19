from __future__ import annotations

import html
import json
import math
import csv
import re
from contextvars import ContextVar
from pathlib import Path
from typing import Any

from app.services.codex_historical_localization_service import localize_historical_text

_ACTIVE_CHART_STYLE: ContextVar[dict[str, Any]] = ContextVar("_ACTIVE_CHART_STYLE", default={})


def _read_json_payload(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _normalize_hex(value: Any, fallback: str) -> str:
    text = str(value or "").strip()
    if len(text) == 7 and text.startswith("#"):
        try:
            int(text[1:], 16)
            return text.lower()
        except Exception:
            return fallback
    return fallback


def _historical_visual_reference(workspace: Path) -> dict[str, Any]:
    return _read_json_payload(workspace / "historical_visual_reference.json")


def _style_transfer_contract(workspace: Path) -> dict[str, Any]:
    visual_reference = _historical_visual_reference(workspace)
    contract = visual_reference.get("style_transfer_contract")
    return contract if isinstance(contract, dict) else {}


def _chart_style_for_workspace(workspace: Path) -> dict[str, Any]:
    visual_reference = _historical_visual_reference(workspace)
    semantic = _read_json_payload(workspace / "visual_semantic_spec.json")
    contract = _style_transfer_contract(workspace)
    chart_style = contract.get("chart_style")
    if not isinstance(chart_style, dict):
        chart_style = {}
    colors = contract.get("colors")
    if not isinstance(colors, dict):
        colors = {}
    semantic_colors = semantic.get("color_tokens")
    if isinstance(semantic_colors, dict):
        base_colors = dict(colors)
        colors = {**base_colors, **semantic_colors}
        if str(base_colors.get("palette_source") or "") == "pdf_preview_pixels":
            for key in (
                "secondary",
                "positive_delta",
                "negative_delta",
                "table_header_fill",
                "table_header_strong_fill",
                "footnote_gray",
                "series_palette",
                "secondary_palette",
                "palette_source",
            ):
                if key in base_colors:
                    if key in {"series_palette", "secondary_palette"} and len({str(item).lower() for item in list(base_colors.get(key) or [])}) < 4:
                        continue
                    colors[key] = base_colors[key]
    signature = visual_reference.get("visual_style_signature")
    if not isinstance(signature, dict):
        signature = {}
    accent_candidates = list(visual_reference.get("accent_palette_hint") or [])
    accent = _normalize_hex(colors.get("primary_accent"), "")
    if not accent:
        accent = _normalize_hex(colors.get("accent"), "")
    if not accent:
        accent = _normalize_hex(colors.get("heading"), "")
    if not accent and accent_candidates:
        accent = _normalize_hex(accent_candidates[0], "")
    if not accent:
        accent = "#1d8bc8"
    secondary = _normalize_hex(colors.get("secondary_accent"), "")
    if not secondary:
        secondary = _normalize_hex(colors.get("secondary"), "")
    if not secondary:
        secondary = _normalize_hex(colors.get("accent_soft"), "#f59e0b")
    background = _normalize_hex(colors.get("page_background"), "")
    if not background:
        background = _normalize_hex(colors.get("background"), "#ffffff")
    series_palette = [
        _normalize_hex(item, "")
        for item in list(colors.get("series_palette") or [])
        if _normalize_hex(item, "")
    ]
    if not series_palette:
        series_palette = [accent, secondary, "#b05738", "#5f7fa8", "#7a6f56"]
    positive_delta = _normalize_hex(colors.get("positive_delta"), accent)
    negative_delta = _normalize_hex(colors.get("negative_delta"), "#b05738")
    avoid = {
        str(item or "").strip()
        for item in list(chart_style.get("avoid_chart_kinds") or [])
        + list(chart_style.get("avoid_chart_families_when_possible") or [])
        if str(item or "").strip()
    }
    preferred = [
        str(item or "").strip()
        for item in list(chart_style.get("preferred_chart_kinds") or [])
        + list(chart_style.get("preferred_chart_families") or [])
        if str(item or "").strip()
    ]
    exhibit_mode = str(((signature.get("exhibit_system") or {}) if isinstance(signature.get("exhibit_system"), dict) else {}).get("mode") or "")
    if signature.get("page_orientation") == "portrait" and exhibit_mode == "numbered_exhibit":
        preferred = ["paired_horizontal_bar", "right_annotation_columns", *preferred]
    furniture = contract.get("furniture")
    if not isinstance(furniture, dict):
        furniture = {}
    regions = contract.get("regions")
    if not isinstance(regions, dict):
        regions = {}
    visual_primitives = contract.get("visual_primitives")
    if not isinstance(visual_primitives, dict):
        visual_primitives = {}
    chart_grammar_contract = chart_style.get("chart_grammar_contract")
    if not isinstance(chart_grammar_contract, dict):
        chart_grammar_contract = visual_primitives.get("chart_grammar_contract")
    if not isinstance(chart_grammar_contract, dict):
        chart_grammar_contract = {}
    workspace_contract = _read_json_payload(workspace / "chart_grammar_contract.json")
    if workspace_contract:
        chart_grammar_contract = {**chart_grammar_contract, **workspace_contract}
    chart_profile_pack = _read_json_payload(workspace / "source_chart_grammar_profile_pack.json")
    profile_required_kinds = [
        str(item or "").strip()
        for item in list(chart_profile_pack.get("required_chart_kinds") or [])
        if str(item or "").strip()
    ]
    grammar_preferred = [
        str(item or "").strip()
        for item in list(chart_grammar_contract.get("preferred_chart_kinds") or [])
        if str(item or "").strip()
    ]
    grammar_avoid = {
        str(item or "").strip()
        for item in list(chart_grammar_contract.get("avoid_chart_kinds") or [])
        if str(item or "").strip()
    }
    preferred = [*profile_required_kinds, *grammar_preferred, *preferred]
    avoid.update(grammar_avoid)
    return {
        "accent": accent,
        "secondary": secondary,
        "series_palette": series_palette[:6],
        "positive_delta": positive_delta,
        "negative_delta": negative_delta,
        "table_header_fill": _normalize_hex(colors.get("table_header_fill"), "#e8f3ef"),
        "background": background,
        "ink": "#24312f" if signature.get("background_mode") == "white_document" else "#12324a",
        "muted": "#66736f",
        "soft": "#e4efe9" if signature.get("background_mode") == "white_document" else "#eef6fb",
        "frame": "exhibit" if signature.get("background_mode") == "white_document" else "card",
        "show_side_rail": bool(furniture.get("side_rail")),
        "show_source_footer": bool(furniture.get("source_footer", True)),
        "avoid_chart_kinds": sorted(avoid),
        "preferred_chart_kinds": preferred,
        "chart_grammar_contract": chart_grammar_contract,
        "chart_grammar_tokens": list(chart_grammar_contract.get("chart_grammar_tokens") or []),
        "dominant_chart_grammar": chart_grammar_contract.get("dominant_chart_grammar") or visual_primitives.get("dominant_visual_grammar"),
        "source_chart_grammar_profile_pack": chart_profile_pack,
        "visual_style_signature": signature,
        "style_transfer_contract": contract,
        "region_system": regions,
        "visual_primitives": visual_primitives,
    }


def _active_chart_style() -> dict[str, Any]:
    style = _ACTIVE_CHART_STYLE.get({})
    return style if isinstance(style, dict) else {}


def _style_color(key: str, fallback: str) -> str:
    return _normalize_hex(_active_chart_style().get(key), fallback)


def _chart_kind_avoided(kind: str) -> bool:
    avoid = {str(item or "").strip() for item in list(_active_chart_style().get("avoid_chart_kinds") or [])}
    return kind in avoid


def _chart_kind_preferred(kind: str) -> bool:
    preferred = {str(item or "").strip() for item in list(_active_chart_style().get("preferred_chart_kinds") or [])}
    aliases = {
        "bar": {"bar", "horizontal_bar", "paired_horizontal_bar", "vertical_bar"},
        "paired_horizontal_bar": {"paired_horizontal_bar", "paired_horizontal_bar_with_delta", "horizontal_bar", "bar"},
        "histogram": {"histogram", "vertical_bar", "bar"},
        "line": {"line", "indexed_trend", "indexed_multi_line", "right_labeled_index_line"},
        "indexed_multi_line": {"line", "indexed_trend", "indexed_multi_line", "right_labeled_index_line"},
        "right_labeled_index_line": {"line", "indexed_trend", "indexed_multi_line", "right_labeled_index_line"},
        "grouped_bar": {"grouped_bar", "vertical_bar", "bar", "paired_horizontal_bar"},
        "scatter": {"scatter", "scatter_quadrant", "portfolio_matrix"},
        "donut": {"donut", "share_map", "pie"},
        "heatmap": {"heatmap", "matrix", "table_grid", "matrix_table_with_group_headers"},
        "matrix_table_with_group_headers": {"heatmap", "matrix", "table_grid", "matrix_table_with_group_headers"},
    }
    return kind in preferred or bool(aliases.get(kind, {kind}) & preferred)


def _chart_kind_matches_grammar(kind: str) -> bool:
    contract = _active_chart_style().get("chart_grammar_contract")
    if not isinstance(contract, dict):
        return False
    preferred = {str(item or "").strip() for item in list(contract.get("preferred_chart_kinds") or [])}
    profile_pack = _active_chart_style().get("source_chart_grammar_profile_pack")
    required = {
        str(item or "").strip()
        for item in list((profile_pack if isinstance(profile_pack, dict) else {}).get("required_chart_kinds") or [])
        if str(item or "").strip()
    }
    return kind in preferred or kind in required or _chart_kind_preferred(kind)


def _source_chart_profile_matches(kind: str) -> tuple[list[str], list[str]]:
    style = _active_chart_style()
    pack = style.get("source_chart_grammar_profile_pack")
    profiles = list((pack if isinstance(pack, dict) else {}).get("profiles") or [])
    matched_ids: list[str] = []
    required_kinds: list[str] = []
    kind_aliases = {
        kind,
        *({
            "indexed_multi_line": {"line", "indexed_trend", "right_labeled_index_line"},
            "right_labeled_index_line": {"line", "indexed_multi_line", "indexed_trend"},
            "paired_horizontal_bar": {"paired_horizontal_bar_with_delta", "horizontal_bar", "bar"},
            "grouped_bar": {"vertical_bar", "bar"},
            "heatmap": {"matrix_table_with_group_headers", "table_grid", "matrix"},
            "scatter": {"scatter_quadrant", "portfolio_matrix"},
        }.get(kind, set())),
    }
    for profile in profiles:
        if not isinstance(profile, dict):
            continue
        required = str(profile.get("required_chart_kind") or "").strip()
        fallback = {str(item or "").strip() for item in list(profile.get("fallback_chart_kinds") or []) if str(item or "").strip()}
        if required:
            required_kinds.append(required)
        if required in kind_aliases or bool(fallback & kind_aliases):
            profile_id = str(profile.get("source_chart_grammar_profile_id") or "")
            if profile_id:
                matched_ids.append(profile_id)
    return sorted(set(matched_ids)), sorted(set(required_kinds))


def _apply_active_svg_style(text: str) -> str:
    style = _active_chart_style()
    if not style:
        return text
    accent = _style_color("accent", "#1d8bc8")
    secondary = _style_color("secondary", "#f59e0b")
    series = [
        _normalize_hex(item, "")
        for item in list(style.get("series_palette") or [])
        if _normalize_hex(item, "")
    ]
    while len(series) < 5:
        series.append([accent, secondary, "#b05738", "#5f7fa8", "#7a6f56"][len(series)])
    positive = _style_color("positive_delta", accent)
    negative = _style_color("negative_delta", "#b05738")
    muted = str(style.get("muted") or "#66736f")
    soft = str(style.get("soft") or "#e4efe9")
    replacements = {
        "#1d8bc8": series[0],
        "#0f4f84": series[0],
        "#8ab8d7": soft,
        "#63bf43": positive,
        "#f59e0b": series[1],
        "#ef4444": negative,
        "#dc2626": negative,
        "#b05738": negative,
        "#5f7fa8": series[3],
        "#7a6f56": series[4],
        "#6a7e90": muted,
        "#4a6174": muted,
        "#4f6579": muted,
        "#9ab7cb": "#c8d6d0",
        "#cfe1ec": "#d8e4df",
        "#d7e7f2": "#d8e4df",
    }
    styled = text
    for source, target in replacements.items():
        styled = styled.replace(source, target)
    return styled


_PHRASE_LOCALIZATION = {
    "Revenue Distribution": "收入分布",
    "Channel Mix": "渠道收入结构",
    "Metric Correlation": "指标相关图",
    "CAC vs Retention": "获客成本 x 留存",
    "Gross margin distribution by category": "品类毛利分布",
    "Gross margin distribution by category Cumulative Curve": "品类毛利累计曲线",
    "Revenue mix by channel": "渠道收入结构",
    "Revenue mix by channel Share Map": "渠道收入结构份额图",
    "Revenue mix by channel Pareto View": "渠道收入帕累托视图",
    "Revenue mix by channel Value Bridge": "渠道收入结构价值桥",
    "Revenue mix by channel Priority Bubble Map": "渠道收入优先级气泡图",
    "Operating driver correlation map": "经营驱动因素相关图",
    "Operating driver correlation map Top Pairs": "经营驱动因素相关性重点组合",
    "Price index vs repeat purchase rate": "价格指数 x 复购率",
    "Price index vs repeat purchase rate Quadrant Map": "价格指数 x 复购率象限图",
    "Price index vs repeat purchase rate 2x2 Portfolio Matrix": "价格指数 x 复购率 2x2 组合矩阵",
    "Value build": "价值培育区",
    "Scale and protect": "放量保护区",
    "Watch list": "观察区",
    "Price risk": "价格风险区",
    "Scale leaders": "头部放量区",
    "Repair candidates": "修复候选区",
    "Total": "合计",
}

_TOKEN_LOCALIZATION = {
    "Marketplace": "平台",
    "Direct store": "直营",
    "Wholesale": "批发",
    "Social commerce": "社交电商",
    "Retail partner": "零售伙伴",
    "Price index": "价格指数",
    "Repeat purchase rate": "复购率",
    "repeat_purchase_rate": "复购率",
    "repeat_rate": "复购率",
    "revenue": "收入",
    "net_revenue": "净收入",
    "margin": "毛利率",
    "gross_margin": "毛利率",
    "inventory_turns": "库存周转",
    "service_level": "服务水平",
    "channel": "渠道",
    "category": "品类",
    "region": "区域",
    "Cumulative Curve": "累计曲线",
    "Share Map": "结构份额图",
    "Pareto View": "帕累托视图",
    "Value Bridge": "价值桥",
    "Priority Bubble Map": "优先级气泡图",
    "Top Pairs": "重点组合",
    "Quadrant Map": "象限图",
    "Portfolio Matrix": "组合矩阵",
}

_KIND_SUBTITLE_LOCALIZATION = {
    "distribution": "基于当前样本生成的分布图",
    "category": "基于当前样本生成的结构图",
    "top correlation pairs": "基于当前样本生成的相关性重点组合图",
}


def _localize_text(value: Any) -> str:
    text = localize_historical_text(value)
    if not text:
        return ""
    localized = text
    for source, target in sorted(_PHRASE_LOCALIZATION.items(), key=lambda item: len(item[0]), reverse=True):
        localized = localized.replace(source, target)
    for source, target in sorted(_TOKEN_LOCALIZATION.items(), key=lambda item: len(item[0]), reverse=True):
        localized = localized.replace(source, target)
    return localized


def _localize_labels(values: list[str]) -> list[str]:
    return [_localize_text(value) for value in values]


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".svg":
        text = _apply_active_svg_style(text)
    path.write_text(text, encoding="utf-8")


def _safe_title(value: Any, fallback: str) -> str:
    text = str(value or "").strip()
    return text or fallback


def _as_number_list(values: Any) -> list[float]:
    output: list[float] = []
    for value in values or []:
        try:
            output.append(float(value))
        except Exception:
            output.append(0.0)
    return output


def _as_text_list(values: Any, *, limit: int = 24) -> list[str]:
    output: list[str] = []
    for value in values or []:
        text = str(value or "").strip()
        if not text:
            continue
        output.append(text)
        if len(output) >= limit:
            break
    return output


def _as_scatter_points(values: Any, *, limit: int = 240) -> list[list[float]]:
    output: list[list[float]] = []
    for item in values or []:
        try:
            if isinstance(item, dict):
                x_raw = item.get("x", item.get("x_value", item.get("left")))
                y_raw = item.get("y", item.get("y_value", item.get("right")))
            else:
                if len(item) < 2:
                    continue
                x_raw = item[0]
                y_raw = item[1]
            output.append([float(x_raw), float(y_raw)])
        except Exception:
            continue
        if len(output) >= limit:
            break
    return output


def _svg_shell(title: str, subtitle: str, body: str, *, width: int = 1200, height: int = 720, compact_exhibit: bool = False) -> str:
    style = _active_chart_style()
    accent = _style_color("accent", "#1d8bc8")
    secondary = _style_color("secondary", "#f59e0b")
    background = _style_color("background", "#ffffff")
    ink = str(style.get("ink") or "#12324a")
    muted = str(style.get("muted") or "#66736f")
    soft = str(style.get("soft") or "#e4efe9")
    if style.get("frame") == "exhibit":
        subtitle_y = 48 if compact_exhibit else 88
        rule_y = 70 if compact_exhibit else 112
        rail = (
            f'<rect x="62" y="58" width="8" height="46" fill="{accent}"/>'
            if style.get("show_side_rail")
            else ""
        )
        source = (
            f'<text x="64" y="{height-42}" font-size="13" fill="{muted}" font-family="Microsoft YaHei, PingFang SC, Arial">来源：当前数据资产包</text>'
            if style.get("show_source_footer")
            else ""
        )
        if style.get("show_source_footer"):
            source = (
                f'<text x="64" y="{height-36}" font-size="13" fill="{muted}" '
                'font-family="Microsoft YaHei, PingFang SC, Arial">来源：当前数据资产包</text>'
            )
        preserve = ' preserveAspectRatio="xMidYMin meet"' if compact_exhibit else ""
        return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}"{preserve}>
  <rect width="{width}" height="{height}" fill="{background}"/>
  {rail}
  <text x="{width/2:.1f}" y="{subtitle_y}" font-size="15" text-anchor="middle" fill="{muted}" font-family="Microsoft YaHei, PingFang SC, Arial">{html.escape(subtitle)}</text>
  <line x1="80" y1="{rule_y}" x2="{width-116}" y2="{rule_y}" stroke="#cdd8d2" stroke-width="1.2"/>
  {body}
  {source}
</svg>"""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    <linearGradient id="bg" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0%" stop-color="{background}"/>
      <stop offset="100%" stop-color="{soft}"/>
    </linearGradient>
  </defs>
  <rect width="{width}" height="{height}" fill="url(#bg)"/>
  <rect x="34" y="30" width="{width-68}" height="{height-60}" rx="28" fill="#ffffff" stroke="#d7e7f2" stroke-width="2"/>
  <rect x="64" y="72" width="14" height="72" fill="{accent}"/>
  <text x="100" y="100" font-size="30" font-weight="700" fill="{accent}" font-family="Microsoft YaHei, PingFang SC, Arial">{html.escape(title)}</text>
  <text x="100" y="136" font-size="16" fill="{muted}" font-family="Microsoft YaHei, PingFang SC, Arial">{html.escape(subtitle)}</text>
  {body}
</svg>"""


def _format_chart_value(value: float, *, max_value: float | None = None) -> str:
    reference = max(abs(float(max_value or 0.0)), abs(float(value or 0.0)))
    if 0 < reference <= 2.0:
        return f"{value * 100:.1f}%"
    if reference < 100:
        return f"{value:.2f}"
    return f"{value:,.0f}"


def _render_bar_like(title: str, labels: list[str], values: list[float], *, kind_label: str) -> str:
    width = 1200
    height = 720
    chart_left = 150
    chart_top = 170
    chart_width = 930
    chart_height = 430
    max_value = max(values) if values else 1.0
    rows: list[str] = []
    step = chart_height / max(1, len(labels))
    for index, (label, value) in enumerate(zip(labels, values)):
        y = chart_top + index * step + 10
        bar_width = 0 if max_value <= 0 else (value / max_value) * (chart_width - 180)
        rows.append(
            f'<text x="{chart_left}" y="{y+18:.1f}" font-size="16" fill="#2e4051" font-family="Microsoft YaHei, PingFang SC, Arial">{html.escape(label[:18])}</text>'
            f'<rect x="{chart_left+180}" y="{y:.1f}" width="{bar_width:.1f}" height="26" rx="8" fill="#1d8bc8"/>'
            f'<text x="{chart_left+190+bar_width:.1f}" y="{y+18:.1f}" font-size="15" fill="#1d8bc8" font-family="Microsoft YaHei, PingFang SC, Arial">{_format_chart_value(value, max_value=max_value)}</text>'
        )
    body = "\n".join(rows)
    subtitle = _KIND_SUBTITLE_LOCALIZATION.get(kind_label, "基于当前样本生成的图表资产")
    return _svg_shell(title, subtitle, body, width=width, height=height)


def _render_vertical_bar_like(title: str, labels: list[str], values: list[float], *, kind_label: str) -> str:
    width = 1200
    height = 760
    left = 130
    top = 170
    chart_w = 900
    chart_h = 440
    values = [max(0.0, value) for value in values[:12]]
    labels = labels[: len(values)]
    max_value = max(values) if values else 1.0
    bar_w = chart_w / max(1, len(values))
    accent = _style_color("accent", "#1d8bc8")
    muted = str(_active_chart_style().get("muted") or "#66736f")
    gridline = "#dbe5e1"
    parts: list[str] = [
        f'<line x1="{left}" y1="{top + chart_h}" x2="{left + chart_w}" y2="{top + chart_h}" stroke="{gridline}" stroke-width="2"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + chart_h}" stroke="{gridline}" stroke-width="2"/>',
    ]
    for tick in range(1, 5):
        y = top + chart_h - tick * chart_h / 5
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + chart_w}" y2="{y:.1f}" stroke="{gridline}" stroke-width="1" stroke-dasharray="5 7"/>')
    for index, (label, value) in enumerate(zip(labels, values)):
        x = left + index * bar_w + max(5, bar_w * 0.14)
        h = 0 if max_value <= 0 else (value / max_value) * (chart_h - 30)
        y = top + chart_h - h
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(8, bar_w * 0.68):.1f}" height="{h:.1f}" rx="7" fill="{accent}" fill-opacity="0.88"/>')
        parts.append(f'<text x="{x + max(8, bar_w * 0.68)/2:.1f}" y="{y-8:.1f}" font-size="13" text-anchor="middle" fill="{accent}" font-weight="700" font-family="Microsoft YaHei, PingFang SC, Arial">{_format_chart_value(value, max_value=max_value)}</text>')
        parts.append(
            f'<text x="{x + max(8, bar_w * 0.68)/2:.1f}" y="{top + chart_h + 30}" font-size="12" text-anchor="middle" fill="{muted}" transform="rotate(-24 {x + max(8, bar_w * 0.68)/2:.1f} {top + chart_h + 30})" font-family="Microsoft YaHei, PingFang SC, Arial">{html.escape(label[:12])}</text>'
        )
    subtitle = _KIND_SUBTITLE_LOCALIZATION.get(kind_label, "基于当前样本生成的纵向柱状图资产")
    return _svg_shell(title, subtitle, "\n".join(parts), width=width, height=height)


def _render_paired_horizontal_bars(title: str, labels: list[str], values: list[float], insight_input: dict[str, Any]) -> str:
    style = _active_chart_style()
    regions = dict(style.get("region_system") or {})
    primitives = dict(style.get("visual_primitives") or {})
    average_regions = dict(regions.get("average_regions") or {})
    visual_ratio = float(average_regions.get("primary_visual_height_ratio") or 0.42)
    right_annotation_likelihood = max(
        float(regions.get("right_annotation_column_likelihood") or average_regions.get("right_annotation_column_likelihood") or 0),
        float(primitives.get("right_numeric_column_likelihood") or 0),
    )
    width = 1200
    left_label_x = 118
    chart_left = 320
    chart_top = 92
    right_col_x = 900 if right_annotation_likelihood >= 0.22 else 935
    chart_width = max(430, right_col_x - chart_left - 78)
    values = [max(0.0, value) for value in values[:8]]
    labels = labels[: len(values)]
    if not values:
        values = [0.0]
        labels = ["分组"]
    if len(values) <= 4:
        row_height = 92
    elif len(values) <= 6:
        row_height = 84
    else:
        row_height = 72 if float(primitives.get("paired_bar_likelihood") or 0) >= 0.35 else 78
    bar_h = 30 if len(values) <= 4 else 26
    bar_gap = 10 if len(values) <= 4 else 8
    height = int(max(560, min(900, chart_top + row_height * len(values) + 190)))
    if visual_ratio >= 0.48 and len(values) >= 6:
        height = int(min(920, height + 60))
    if float(primitives.get("paired_bar_likelihood") or 0) >= 0.35 and len(values) > 6:
        row_height = max(54, min(row_height, 72))
    benchmark = sum(values) / max(1, len(values))
    raw_max_value = max(max(values), benchmark, 0.0)
    # Rate / percentage metrics often live below 1.0; scaling them against 1.0
    # makes the exhibit look empty even when the segment differences are real.
    max_value = raw_max_value * 1.08 if 0 < raw_max_value <= 1.0 else max(raw_max_value, 1.0)
    def format_value(value: float) -> str:
        if max_value <= 2.0:
            return f"{value:.1%}"
        if max_value <= 100:
            return f"{value:,.1f}"
        return f"{value:,.0f}"
    accent = _style_color("accent", "#1d8bc8")
    secondary = _style_color("secondary", "#66cb92")
    muted = str(_active_chart_style().get("muted") or "#66736f")
    parts: list[str] = [
        f'<text x="{chart_left}" y="{chart_top - 18}" font-size="17" fill="{muted}" font-family="Microsoft YaHei, PingFang SC, Arial">当前值与均值基准对比</text>',
        f'<text x="{right_col_x}" y="{chart_top - 18}" font-size="16" fill="{muted}" font-family="Microsoft YaHei, PingFang SC, Arial">相对均值</text>',
        f'<line x1="80" y1="{chart_top - 2}" x2="{width-116}" y2="{chart_top - 2}" stroke="#d5ddd8" stroke-width="1.4"/>',
    ]
    for index, (label, value) in enumerate(zip(labels, values)):
        y = chart_top + index * row_height
        current_w = max(2.0, (value / max_value) * chart_width)
        benchmark_w = max(2.0, (benchmark / max_value) * chart_width)
        lift = (value / benchmark - 1.0) if benchmark else 0.0
        current_y = y + bar_h + bar_gap
        parts.append(f'<line x1="80" y1="{y + row_height - 12}" x2="{width-116}" y2="{y + row_height - 12}" stroke="#e5ebe8" stroke-width="1.15"/>')
        parts.append(f'<text x="{left_label_x}" y="{y + bar_h - 4}" font-size="18" fill="#555" font-family="Microsoft YaHei, PingFang SC, Arial">{html.escape(label[:18])}</text>')
        parts.append(f'<text x="{chart_left-22}" y="{y + bar_h * .68:.1f}" font-size="13" text-anchor="end" fill="{muted}" font-family="Microsoft YaHei, PingFang SC, Arial">均值</text>')
        parts.append(f'<rect x="{chart_left}" y="{y}" width="{benchmark_w:.1f}" height="{bar_h}" fill="{secondary}" fill-opacity="0.62"/>')
        parts.append(f'<text x="{chart_left-22}" y="{current_y + bar_h * .68:.1f}" font-size="13" text-anchor="end" fill="{muted}" font-family="Microsoft YaHei, PingFang SC, Arial">当前</text>')
        parts.append(f'<rect x="{chart_left}" y="{current_y}" width="{current_w:.1f}" height="{bar_h}" fill="{accent}"/>')
        parts.append(f'<text x="{chart_left + current_w + 10:.1f}" y="{current_y + bar_h * .68:.1f}" font-size="16" font-weight="800" fill="{accent}" font-family="Microsoft YaHei, PingFang SC, Arial">{format_value(value)}</text>')
        lift_color = accent if lift >= 0 else "#b45309"
        parts.append(f'<text x="{right_col_x}" y="{current_y + bar_h * .68:.1f}" font-size="18" font-weight="800" fill="{lift_color}" font-family="Microsoft YaHei, PingFang SC, Arial">{lift:+.1%}</text>')
    note = str(insight_input.get("metric_localized_label") or insight_input.get("metric_raw_key") or insight_input.get("raw_key") or "核心指标")
    parts.append(f'<text x="80" y="{height-82}" font-size="14" fill="{muted}" font-family="Microsoft YaHei, PingFang SC, Arial">Note: 基准为当前数据中同一维度分组均值；用于复刻历史报告的横向 exhibit 语法，不复制源报告旧结论。</text>')
    parts.append(f'<text x="80" y="{height-58}" font-size="14" fill="{muted}" font-family="Microsoft YaHei, PingFang SC, Arial">Metric: {html.escape(note[:42])}</text>')
    return _svg_shell(title, "基于当前数据生成的横向分组 exhibit", "\n".join(parts), width=width, height=height, compact_exhibit=True)


def _render_donut(title: str, labels: list[str], values: list[float]) -> str:
    width = 1200
    height = 760
    total = sum(max(0.0, value) for value in values) or 1.0
    cx = 420
    cy = 410
    radius = 190
    palette = ["#1d8bc8", "#63bf43", "#f59e0b", "#ef4444", "#64748b", "#14b8a6", "#8b5cf6", "#0f766e"]
    start = -90.0
    parts: list[str] = []
    legend: list[str] = []
    for index, (label, value) in enumerate(zip(labels[:8], values[:8])):
        share = max(0.0, value) / total
        end = start + share * 360.0
        large_arc = 1 if end - start > 180 else 0
        x1 = cx + radius * math.cos(math.radians(start))
        y1 = cy + radius * math.sin(math.radians(start))
        x2 = cx + radius * math.cos(math.radians(end))
        y2 = cy + radius * math.sin(math.radians(end))
        color = palette[index % len(palette)]
        parts.append(
            f'<path d="M {cx} {cy} L {x1:.1f} {y1:.1f} A {radius} {radius} 0 {large_arc} 1 {x2:.1f} {y2:.1f} Z" fill="{color}" fill-opacity="0.88"/>'
        )
        legend.append(
            f'<rect x="720" y="{230 + index * 44}" width="18" height="18" rx="5" fill="{color}"/>'
            f'<text x="750" y="{245 + index * 44}" font-size="17" fill="#2e4051" font-family="Microsoft YaHei, PingFang SC, Arial">{html.escape(label[:24])} {share:.1%}</text>'
        )
        start = end
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="104" fill="#ffffff"/>')
    parts.append(
        f'<text x="{cx}" y="{cy-6}" font-size="30" font-weight="700" text-anchor="middle" fill="#1d8bc8" font-family="Microsoft YaHei, PingFang SC, Arial">{len(labels[:8])}</text>'
        f'<text x="{cx}" y="{cy+28}" font-size="16" text-anchor="middle" fill="#6a7e90" font-family="Microsoft YaHei, PingFang SC, Arial">细分单元</text>'
    )
    return _svg_shell(title, "基于当前样本生成的结构份额图", "\n".join(parts + legend), width=width, height=height)


def _render_pareto(title: str, labels: list[str], values: list[float]) -> str:
    paired = sorted(zip(labels, values), key=lambda item: item[1], reverse=True)[:12]
    labels = [label for label, _value in paired]
    values = [max(0.0, value) for _label, value in paired]
    total = sum(values) or 1.0
    cumulative: list[float] = []
    running = 0.0
    for value in values:
        running += value
        cumulative.append(running / total)
    width = 1200
    height = 760
    left = 130
    top = 165
    chart_w = 910
    chart_h = 450
    max_value = max(values) if values else 1.0
    bar_w = chart_w / max(1, len(values))
    parts = [
        f'<line x1="{left}" y1="{top + chart_h}" x2="{left + chart_w}" y2="{top + chart_h}" stroke="#9ab7cb" stroke-width="2"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + chart_h}" stroke="#9ab7cb" stroke-width="2"/>',
    ]
    points: list[str] = []
    for index, (label, value) in enumerate(zip(labels, values)):
        x = left + index * bar_w + 8
        h = 0 if max_value <= 0 else (value / max_value) * (chart_h - 40)
        y = top + chart_h - h
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(8, bar_w-16):.1f}" height="{h:.1f}" rx="8" fill="#1d8bc8" fill-opacity="0.86"/>')
        parts.append(
            f'<text x="{x + bar_w/2 - 8:.1f}" y="{top + chart_h + 28}" font-size="13" text-anchor="middle" fill="#4a6174" transform="rotate(-20 {x + bar_w/2 - 8:.1f} {top + chart_h + 28})" font-family="Microsoft YaHei, PingFang SC, Arial">{html.escape(label[:12])}</text>'
        )
        line_y = top + chart_h - cumulative[index] * (chart_h - 40)
        points.append(f"{x + bar_w/2 - 8:.1f},{line_y:.1f}")
        parts.append(f'<circle cx="{x + bar_w/2 - 8:.1f}" cy="{line_y:.1f}" r="5" fill="#f59e0b"/>')
    if len(points) >= 2:
        parts.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="#f59e0b" stroke-width="4" stroke-linecap="round"/>')
    parts.append(f'<text x="{left + chart_w - 20}" y="{top + 30}" font-size="16" text-anchor="end" fill="#f59e0b" font-family="Microsoft YaHei, PingFang SC, Arial">累计贡献</text>')
    return _svg_shell(title, "基于当前样本生成的帕累托视图", "\n".join(parts), width=width, height=height)


def _render_waterfall_bridge(title: str, labels: list[str], values: list[float]) -> str:
    paired = sorted(zip(labels, values), key=lambda item: item[1], reverse=True)[:8]
    if not paired:
        paired = [("Segment", 0.0)]
    labels = [label for label, _value in paired]
    values = [max(0.0, value) for _label, value in paired]
    total = sum(values) or 1.0
    width = 1200
    height = 760
    left = 130
    top = 165
    chart_w = 910
    chart_h = 445
    bar_w = chart_w / max(1, len(values) + 1)
    parts = [
        f'<line x1="{left}" y1="{top + chart_h}" x2="{left + chart_w}" y2="{top + chart_h}" stroke="#9ab7cb" stroke-width="2"/>',
        f'<text x="{left}" y="{top - 20}" font-size="17" fill="#2e4051" font-family="Microsoft YaHei, PingFang SC, Arial">总量贡献结构桥：{total:,.0f}</text>',
    ]
    running = 0.0
    max_total = max(total, max(values))
    previous_top_y = top + chart_h
    for index, (label, value) in enumerate(zip(labels, values)):
        x = left + index * bar_w + 12
        start_y = top + chart_h - (running / max_total) * (chart_h - 40)
        running += value
        end_y = top + chart_h - (running / max_total) * (chart_h - 40)
        y = min(start_y, end_y)
        h = max(8.0, abs(start_y - end_y))
        color = "#1d8bc8" if index < 3 else "#8ab8d7"
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w-24:.1f}" height="{h:.1f}" rx="7" fill="{color}"/>')
        parts.append(f'<text x="{x + (bar_w-24)/2:.1f}" y="{y-8:.1f}" font-size="14" text-anchor="middle" fill="#1d8bc8" font-family="Microsoft YaHei, PingFang SC, Arial">{value:,.0f}</text>')
        parts.append(f'<text x="{x + (bar_w-24)/2:.1f}" y="{top + chart_h + 28}" font-size="13" text-anchor="middle" fill="#4a6174" transform="rotate(-18 {x + (bar_w-24)/2:.1f} {top + chart_h + 28})" font-family="Microsoft YaHei, PingFang SC, Arial">{html.escape(label[:14])}</text>')
        if index > 0:
            parts.append(f'<line x1="{left + index * bar_w - 10:.1f}" y1="{previous_top_y:.1f}" x2="{x:.1f}" y2="{previous_top_y:.1f}" stroke="#b7c9d8" stroke-width="2" stroke-dasharray="6 6"/>')
        previous_top_y = end_y
    total_x = left + len(values) * bar_w + 12
    total_h = (total / max_total) * (chart_h - 40)
    parts.append(f'<rect x="{total_x:.1f}" y="{top + chart_h - total_h:.1f}" width="{bar_w-24:.1f}" height="{total_h:.1f}" rx="7" fill="#0f4f84"/>')
    parts.append(f'<text x="{total_x + (bar_w-24)/2:.1f}" y="{top + chart_h - total_h - 8:.1f}" font-size="15" text-anchor="middle" fill="#0f4f84" font-family="Microsoft YaHei, PingFang SC, Arial">{total:,.0f}</text>')
    parts.append(f'<text x="{total_x + (bar_w-24)/2:.1f}" y="{top + chart_h + 28}" font-size="13" text-anchor="middle" fill="#4a6174" font-family="Microsoft YaHei, PingFang SC, Arial">合计</text>')
    return _svg_shell(title, "基于当前样本生成的结构桥图", "\n".join(parts), width=width, height=height)


def _render_priority_bubble_map(title: str, labels: list[str], values: list[float]) -> str:
    paired = sorted(zip(labels, values), key=lambda item: item[1], reverse=True)[:10]
    if not paired:
        paired = [("Segment", 1.0)]
    width = 1200
    height = 760
    left = 120
    top = 170
    chart_w = 940
    chart_h = 470
    max_value = max(max(0.0, value) for _label, value in paired) or 1.0
    total = sum(max(0.0, value) for _label, value in paired) or 1.0
    parts = [
        f'<rect x="{left}" y="{top}" width="{chart_w}" height="{chart_h}" rx="22" fill="#f8fbff" stroke="#cfe1ec"/>',
        f'<line x1="{left + chart_w/2:.1f}" y1="{top}" x2="{left + chart_w/2:.1f}" y2="{top + chart_h}" stroke="#f59e0b" stroke-width="3" stroke-dasharray="10 10"/>',
        f'<line x1="{left}" y1="{top + chart_h/2:.1f}" x2="{left + chart_w}" y2="{top + chart_h/2:.1f}" stroke="#f59e0b" stroke-width="3" stroke-dasharray="10 10"/>',
        f'<text x="{left + 20}" y="{top + 32}" font-size="18" fill="#1d8bc8" font-family="Microsoft YaHei, PingFang SC, Arial">头部放量区</text>',
        f'<text x="{left + chart_w - 20}" y="{top + chart_h - 22}" text-anchor="end" font-size="18" fill="#64748b" font-family="Microsoft YaHei, PingFang SC, Arial">修复候选区</text>',
    ]
    for index, (label, value) in enumerate(paired):
        share = max(0.0, value) / total
        x = left + 80 + (index / max(1, len(paired) - 1)) * (chart_w - 160)
        y = top + chart_h - 80 - (max(0.0, value) / max_value) * (chart_h - 160)
        radius = 18 + math.sqrt(max(0.0, value) / max_value) * 34
        color = "#1d8bc8" if index < 3 else "#8ab8d7"
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius:.1f}" fill="{color}" fill-opacity="0.72" stroke="#ffffff" stroke-width="3"/>')
        parts.append(f'<text x="{x:.1f}" y="{y + radius + 18:.1f}" font-size="13" text-anchor="middle" fill="#2e4051" font-family="Microsoft YaHei, PingFang SC, Arial">{html.escape(label[:14])}</text>')
        if index < 3:
            parts.append(f'<text x="{x:.1f}" y="{y+5:.1f}" font-size="13" text-anchor="middle" fill="#ffffff" font-weight="700" font-family="Microsoft YaHei, PingFang SC, Arial">{share:.0%}</text>')
    return _svg_shell(title, "基于当前样本生成的优先级气泡图", "\n".join(parts), width=width, height=height)


def _render_cumulative_line(title: str, labels: list[str], values: list[float]) -> str:
    total = sum(max(0.0, value) for value in values) or 1.0
    running = 0.0
    cumulative: list[float] = []
    for value in values:
        running += max(0.0, value)
        cumulative.append(running / total)
    width = 1200
    height = 700
    left = 130
    top = 180
    chart_w = 910
    chart_h = 380
    parts = [
        f'<line x1="{left}" y1="{top + chart_h}" x2="{left + chart_w}" y2="{top + chart_h}" stroke="#9ab7cb" stroke-width="2"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + chart_h}" stroke="#9ab7cb" stroke-width="2"/>',
    ]
    points: list[str] = []
    step = chart_w / max(1, len(cumulative) - 1)
    for index, share in enumerate(cumulative[:18]):
        x = left + index * step
        y = top + chart_h - share * chart_h
        points.append(f"{x:.1f},{y:.1f}")
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="#1d8bc8"/>')
        if index in {0, len(cumulative[:18]) - 1}:
            parts.append(f'<text x="{x:.1f}" y="{y-14:.1f}" font-size="14" text-anchor="middle" fill="#1d8bc8" font-family="Microsoft YaHei, PingFang SC, Arial">{share:.0%}</text>')
    if len(points) >= 2:
        parts.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="#1d8bc8" stroke-width="4" stroke-linecap="round"/>')
    return _svg_shell(title, "基于当前分布生成的累计曲线", "\n".join(parts), width=width, height=height)


def _normalize_index_series(values: list[float]) -> list[float]:
    cleaned = [float(value or 0.0) for value in values]
    baseline = next((abs(value) for value in cleaned if abs(value) > 1e-9), 0.0)
    if baseline <= 0:
        max_value = max([abs(value) for value in cleaned] or [1.0]) or 1.0
        return [round(value / max_value * 100.0, 2) for value in cleaned]
    return [round(value / baseline * 100.0, 2) for value in cleaned]


def _render_indexed_multi_line(title: str, x_labels: list[str], series: list[dict[str, Any]], insight_input: dict[str, Any]) -> str:
    width = 1200
    height = 700
    left = 98
    top = 86
    chart_w = 830
    chart_h = 500
    right_x = 960
    palette = [
        _normalize_hex(item, "")
        for item in list(_active_chart_style().get("series_palette") or [])
        if _normalize_hex(item, "")
    ]
    while len(palette) < 6:
        palette.append(["#1d8bc8", "#f59e0b", "#b05738", "#5f7fa8", "#7a6f56", "#2aa876"][len(palette)])
    x_labels = [str(label or "").strip() for label in x_labels[:12] if str(label or "").strip()]
    if len(x_labels) < 2:
        x_labels = [f"P{index}" for index in range(1, 7)]
    normalized_series: list[dict[str, Any]] = []
    for item in series[:5]:
        name = str(item.get("name") or item.get("metric") or "").strip()
        values = _normalize_index_series(_as_number_list(item.get("values"))[: len(x_labels)])
        if name and len(values) >= 2 and max(values) != min(values):
            normalized_series.append({"name": name, "values": values})
    if not normalized_series:
        normalized_series = [{"name": "Index", "values": [100.0 for _ in x_labels]}]
    all_values = [value for item in normalized_series for value in list(item.get("values") or [])]
    min_value = min(all_values or [80.0])
    max_value = max(all_values or [120.0])
    if max_value - min_value < 1:
        max_value += 5
        min_value -= 5
    y_min = max(0.0, min_value - (max_value - min_value) * 0.18)
    y_max = max_value + (max_value - min_value) * 0.18

    def sx(index: int) -> float:
        return left + index * chart_w / max(1, len(x_labels) - 1)

    def sy(value: float) -> float:
        return top + chart_h - ((value - y_min) / max(1e-9, y_max - y_min)) * chart_h

    muted = str(_active_chart_style().get("muted") or "#66736f")
    parts: list[str] = [
        f'<line x1="{left}" y1="{top+chart_h}" x2="{left+chart_w}" y2="{top+chart_h}" stroke="#d5ddd8" stroke-width="1.4"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+chart_h}" stroke="#d5ddd8" stroke-width="1.4"/>',
    ]
    for tick in range(5):
        value = y_min + (y_max - y_min) * tick / 4
        y = sy(value)
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left+chart_w}" y2="{y:.1f}" stroke="#e4ebe8" stroke-width="1" stroke-dasharray="6 8"/>')
        parts.append(f'<text x="{left-14}" y="{y+5:.1f}" font-size="12" text-anchor="end" fill="{muted}" font-family="Microsoft YaHei, PingFang SC, Arial">{value:.0f}</text>')
    base_y = sy(100.0)
    if top <= base_y <= top + chart_h:
        parts.append(f'<line x1="{left}" y1="{base_y:.1f}" x2="{left+chart_w}" y2="{base_y:.1f}" stroke="#8c9a95" stroke-width="1.4" stroke-dasharray="10 9"/>')
        parts.append(f'<text x="{right_x}" y="{base_y-7:.1f}" font-size="13" fill="{muted}" font-family="Microsoft YaHei, PingFang SC, Arial">100基准线</text>')
    label_step = max(1, len(x_labels) // 6)
    for index, label in enumerate(x_labels):
        x = sx(index)
        if index % label_step == 0 or index == len(x_labels) - 1:
            parts.append(f'<text x="{x:.1f}" y="{top+chart_h+30}" font-size="12" text-anchor="middle" fill="{muted}" font-family="Microsoft YaHei, PingFang SC, Arial">{html.escape(label[:12])}</text>')
    for series_index, item in enumerate(normalized_series):
        color = palette[series_index % len(palette)]
        values = list(item.get("values") or [])
        points = [f"{sx(index):.1f},{sy(float(value)):.1f}" for index, value in enumerate(values)]
        if len(points) >= 2:
            parts.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" stroke-width="5.6" stroke-linecap="round" stroke-linejoin="round"/>')
        for index, value in enumerate(values):
            if index in {0, len(values) - 1}:
                parts.append(f'<circle cx="{sx(index):.1f}" cy="{sy(float(value)):.1f}" r="6.4" fill="{color}" stroke="#fff" stroke-width="2.4"/>')
        end_value = float(values[-1]) if values else 0.0
        end_y = sy(end_value)
        parts.append(f'<text x="{right_x}" y="{end_y+5:.1f}" font-size="15" font-weight="800" fill="{color}" font-family="Microsoft YaHei, PingFang SC, Arial">{html.escape(str(item.get("name") or "")[:18])} {end_value:.0f}</text>')
    metric_names = ", ".join(str(item.get("name") or "") for item in normalized_series[:4])
    dimension = str(insight_input.get("dimension_raw_key") or insight_input.get("dimension") or insight_input.get("x_axis") or "").strip()
    footer = f"指数化序列；维度={dimension or '有序分组'}；指标={metric_names}"
    parts.append(f'<text x="{left}" y="{height-58}" font-size="13" fill="{muted}" font-family="Microsoft YaHei, PingFang SC, Arial">{html.escape(footer[:118])}</text>')
    return _svg_shell(title, "按源页图表语法生成的指数化多序列折线", "\n".join(parts), width=width, height=height, compact_exhibit=True)


def _render_heatmap(title: str, labels: list[str], matrix: list[list[float]]) -> str:
    width = 1200
    height = 900
    grid_left = 250
    grid_top = 210
    cell = 72
    body_parts: list[str] = []
    size = min(len(labels), 8)
    trimmed_labels = labels[:size]
    trimmed_matrix = [row[:size] for row in matrix[:size]]
    for idx, label in enumerate(trimmed_labels):
        x = grid_left + idx * cell + cell / 2
        y = grid_top - 18
        body_parts.append(
            f'<text x="{x:.1f}" y="{y:.1f}" font-size="14" text-anchor="middle" fill="#4a6174" font-family="Microsoft YaHei, PingFang SC, Arial">{html.escape(label[:10])}</text>'
        )
        y2 = grid_top + idx * cell + cell / 2 + 6
        body_parts.append(
            f'<text x="{grid_left-14}" y="{y2:.1f}" font-size="14" text-anchor="end" fill="#4a6174" font-family="Microsoft YaHei, PingFang SC, Arial">{html.escape(label[:10])}</text>'
        )
    for row_idx, row in enumerate(trimmed_matrix):
        for col_idx, value in enumerate(row):
            x = grid_left + col_idx * cell
            y = grid_top + row_idx * cell
            normalized = max(-1.0, min(1.0, float(value)))
            if normalized >= 0:
                intensity = int(255 - normalized * 100)
                color = f"rgb({intensity}, {235-int(normalized*40)}, 255)"
            else:
                intensity = int(255 - abs(normalized) * 80)
                color = f"rgb(255, {intensity}, {intensity})"
            body_parts.append(f'<rect x="{x}" y="{y}" width="{cell-3}" height="{cell-3}" rx="10" fill="{color}" stroke="#d5e2ec"/>')
            body_parts.append(
                f'<text x="{x + cell/2:.1f}" y="{y + cell/2 + 6:.1f}" font-size="13" text-anchor="middle" fill="#294056" font-family="Microsoft YaHei, PingFang SC, Arial">{normalized:.2f}</text>'
            )
    return _svg_shell(title, "基于相关矩阵生成的热力图", "\n".join(body_parts), width=width, height=height)


def _render_correlation_pairs(title: str, labels: list[str], matrix: list[list[float]]) -> str:
    pairs: list[tuple[str, float]] = []
    for left_index, left in enumerate(labels):
        for right_index, right in enumerate(labels):
            if right_index <= left_index:
                continue
            try:
                value = float(matrix[left_index][right_index])
            except Exception:
                continue
            pairs.append((f"{left[:10]} / {right[:10]}", value))
    pairs.sort(key=lambda item: abs(item[1]), reverse=True)
    pair_labels = [label for label, _value in pairs[:10]]
    pair_values = [abs(value) for _label, value in pairs[:10]]
    return _render_bar_like(title, pair_labels, pair_values, kind_label="top correlation pairs")


def _render_scatter(title: str, x_label: str, y_label: str, points: list[list[float]]) -> str:
    width = 1200
    height = 760
    chart_left = 120
    chart_top = 160
    chart_width = 940
    chart_height = 470
    xs = [float(point[0]) for point in points if len(point) >= 2]
    ys = [float(point[1]) for point in points if len(point) >= 2]
    x_min = min(xs) if xs else 0.0
    x_max = max(xs) if xs else 1.0
    y_min = min(ys) if ys else 0.0
    y_max = max(ys) if ys else 1.0
    span_x = max(1e-9, x_max - x_min)
    span_y = max(1e-9, y_max - y_min)
    dots: list[str] = [
        f'<line x1="{chart_left}" y1="{chart_top + chart_height}" x2="{chart_left + chart_width}" y2="{chart_top + chart_height}" stroke="#9ab7cb" stroke-width="2"/>',
        f'<line x1="{chart_left}" y1="{chart_top}" x2="{chart_left}" y2="{chart_top + chart_height}" stroke="#9ab7cb" stroke-width="2"/>',
        f'<text x="{chart_left + chart_width/2:.1f}" y="{chart_top + chart_height + 42:.1f}" font-size="16" text-anchor="middle" fill="#4f6579" font-family="Microsoft YaHei, PingFang SC, Arial">{html.escape(x_label)}</text>',
        f'<text x="34" y="{chart_top + chart_height/2:.1f}" font-size="16" text-anchor="middle" fill="#4f6579" transform="rotate(-90 34 {chart_top + chart_height/2:.1f})" font-family="Microsoft YaHei, PingFang SC, Arial">{html.escape(y_label)}</text>',
    ]
    for point in points[:240]:
        if len(point) < 2:
            continue
        x = chart_left + ((float(point[0]) - x_min) / span_x) * chart_width
        y = chart_top + chart_height - ((float(point[1]) - y_min) / span_y) * chart_height
        dots.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.2" fill="#1d8bc8" fill-opacity="0.56"/>')
    subtitle = "基于当前样本生成的散点关系图"
    return _svg_shell(title, subtitle, "\n".join(dots), width=width, height=height)


def _render_scatter_quadrant(title: str, x_label: str, y_label: str, points: list[list[float]]) -> str:
    width = 1200
    height = 760
    chart_left = 120
    chart_top = 160
    chart_width = 940
    chart_height = 470
    xs = [float(point[0]) for point in points if len(point) >= 2]
    ys = [float(point[1]) for point in points if len(point) >= 2]
    if not xs or not ys:
        return _render_scatter(title, x_label, y_label, points)
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    x_mid = sum(xs) / len(xs)
    y_mid = sum(ys) / len(ys)
    span_x = max(1e-9, x_max - x_min)
    span_y = max(1e-9, y_max - y_min)
    mid_x_px = chart_left + ((x_mid - x_min) / span_x) * chart_width
    mid_y_px = chart_top + chart_height - ((y_mid - y_min) / span_y) * chart_height
    parts = [
        f'<rect x="{chart_left}" y="{chart_top}" width="{chart_width}" height="{chart_height}" rx="20" fill="#f8fbff" stroke="#cfe1ec"/>',
        f'<line x1="{mid_x_px:.1f}" y1="{chart_top}" x2="{mid_x_px:.1f}" y2="{chart_top + chart_height}" stroke="#f59e0b" stroke-width="3" stroke-dasharray="10 10"/>',
        f'<line x1="{chart_left}" y1="{mid_y_px:.1f}" x2="{chart_left + chart_width}" y2="{mid_y_px:.1f}" stroke="#f59e0b" stroke-width="3" stroke-dasharray="10 10"/>',
        f'<text x="{chart_left + chart_width - 18}" y="{chart_top + 28}" text-anchor="end" font-size="18" fill="#1d8bc8" font-family="Microsoft YaHei, PingFang SC, Arial">高{html.escape(y_label[:12])} / 高{html.escape(x_label[:12])}</text>',
        f'<text x="{chart_left + 18}" y="{chart_top + chart_height - 18}" font-size="18" fill="#64748b" font-family="Microsoft YaHei, PingFang SC, Arial">低位观察区</text>',
    ]
    for point in points[:240]:
        if len(point) < 2:
            continue
        x = chart_left + ((float(point[0]) - x_min) / span_x) * chart_width
        y = chart_top + chart_height - ((float(point[1]) - y_min) / span_y) * chart_height
        color = "#1d8bc8" if float(point[0]) >= x_mid and float(point[1]) >= y_mid else "#64748b"
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.4" fill="{color}" fill-opacity="0.58"/>')
    return _svg_shell(title, "基于当前样本生成的象限诊断图", "\n".join(parts), width=width, height=height)


def _render_scatter_portfolio_matrix(title: str, x_label: str, y_label: str, points: list[list[float]]) -> str:
    width = 1200
    height = 760
    chart_left = 120
    chart_top = 160
    chart_width = 940
    chart_height = 470
    xs = [float(point[0]) for point in points if len(point) >= 2]
    ys = [float(point[1]) for point in points if len(point) >= 2]
    if not xs or not ys:
        return _render_scatter_quadrant(title, x_label, y_label, points)
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    x_mid = sum(xs) / len(xs)
    y_mid = sum(ys) / len(ys)
    span_x = max(1e-9, x_max - x_min)
    span_y = max(1e-9, y_max - y_min)
    mid_x_px = chart_left + ((x_mid - x_min) / span_x) * chart_width
    mid_y_px = chart_top + chart_height - ((y_mid - y_min) / span_y) * chart_height
    zones = [
        (chart_left, chart_top, mid_x_px - chart_left, mid_y_px - chart_top, "#eff8ff", "Value build"),
        (mid_x_px, chart_top, chart_left + chart_width - mid_x_px, mid_y_px - chart_top, "#e8f6ef", "Scale and protect"),
        (chart_left, mid_y_px, mid_x_px - chart_left, chart_top + chart_height - mid_y_px, "#fff7ed", "Watch list"),
        (mid_x_px, mid_y_px, chart_left + chart_width - mid_x_px, chart_top + chart_height - mid_y_px, "#fef2f2", "Price risk"),
    ]
    parts: list[str] = []
    for x, y, w, h, color, label in zones:
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(0, w):.1f}" height="{max(0, h):.1f}" fill="{color}" stroke="#ffffff" stroke-width="2"/>')
        parts.append(f'<text x="{x + 18:.1f}" y="{y + 30:.1f}" font-size="17" fill="#1d8bc8" font-family="Microsoft YaHei, PingFang SC, Arial">{html.escape(label)}</text>')
    parts.append(f'<line x1="{mid_x_px:.1f}" y1="{chart_top}" x2="{mid_x_px:.1f}" y2="{chart_top + chart_height}" stroke="#f59e0b" stroke-width="3" stroke-dasharray="10 10"/>')
    parts.append(f'<line x1="{chart_left}" y1="{mid_y_px:.1f}" x2="{chart_left + chart_width}" y2="{mid_y_px:.1f}" stroke="#f59e0b" stroke-width="3" stroke-dasharray="10 10"/>')
    for index, point in enumerate(points[:240], start=1):
        if len(point) < 2:
            continue
        x = chart_left + ((float(point[0]) - x_min) / span_x) * chart_width
        y = chart_top + chart_height - ((float(point[1]) - y_min) / span_y) * chart_height
        color = "#1d8bc8" if float(point[0]) >= x_mid and float(point[1]) >= y_mid else "#64748b"
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="{color}" fill-opacity="0.72" stroke="#ffffff" stroke-width="2"/>')
        if index <= 6:
            parts.append(f'<text x="{x+10:.1f}" y="{y-10:.1f}" font-size="12" fill="#334155" font-family="Microsoft YaHei, PingFang SC, Arial">#{index}</text>')
    parts.append(f'<text x="{chart_left + chart_width/2:.1f}" y="{chart_top + chart_height + 42:.1f}" font-size="16" text-anchor="middle" fill="#4f6579" font-family="Microsoft YaHei, PingFang SC, Arial">{html.escape(x_label)}</text>')
    parts.append(f'<text x="34" y="{chart_top + chart_height/2:.1f}" font-size="16" text-anchor="middle" fill="#4f6579" transform="rotate(-90 34 {chart_top + chart_height/2:.1f})" font-family="Microsoft YaHei, PingFang SC, Arial">{html.escape(y_label)}</text>')
    return _svg_shell(title, "基于当前样本生成的2x2组合矩阵", "\n".join(parts), width=width, height=height)


def _names_from_value(value: Any) -> set[str]:
    if isinstance(value, str):
        text = value.strip()
        return {text} if text else set()
    if isinstance(value, list):
        names: set[str] = set()
        for item in value:
            names.update(_names_from_value(item))
        return names
    return set()


def _source_metric_names(insight: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    for key in (
        "metric_raw_key",
        "raw_key",
        "metric",
        "metric_name",
        "metric_key",
        "left_metric",
        "right_metric",
        "x_metric",
        "y_metric",
        "x_label",
        "y_label",
        "measure",
        "value_column",
    ):
        value = insight.get(key)
        if isinstance(value, dict):
            names.update(_source_metric_names(value))
        else:
            names.update(_names_from_value(value))
    for key in ("metrics", "metric_names", "source_metric_names", "used_metric_names"):
        names.update(_names_from_value(insight.get(key)))
    for row in list(insight.get("rows") or []):
        if isinstance(row, dict):
            for key in ("metric_raw_key", "raw_key", "metric"):
                names.update(_names_from_value(row.get(key)))
    return {name for name in names if name and name.lower() not in {"x", "y", "total", "segment"}}


def _source_dimension_names(insight: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    for key in (
        "dimension_raw_key",
        "dimension",
        "dimension_name",
        "group_column",
        "label_dimension",
        "segment_dimension",
        "category_column",
    ):
        value = insight.get(key)
        if isinstance(value, dict):
            names.update(_source_dimension_names(value))
        else:
            names.update(_names_from_value(value))
    for key in ("dimensions", "dimension_names", "source_dimension_names", "used_dimension_names"):
        names.update(_names_from_value(insight.get(key)))
    for row in list(insight.get("rows") or []):
        if isinstance(row, dict):
            for key in ("dimension_raw_key", "dimension", "group_column"):
                names.update(_names_from_value(row.get(key)))
    return {name for name in names if name and name.lower() not in {"x", "y", "total", "segment"}}


def _append_asset(
    assets: list[dict[str, Any]],
    *,
    path: Path,
    chart_id: str,
    kind: str,
    title: str,
    role: str,
    insight_input: dict[str, Any] | None = None,
    source_view: str = "",
    management_use: str = "",
) -> None:
    insight = dict(insight_input or {})
    source_metric_names = _source_metric_names(insight)
    source_dimension_names = _source_dimension_names(insight)
    source_profile_ids, required_kinds = _source_chart_profile_matches(kind)
    assets.append(
        {
            "chart_id": chart_id,
            "asset_type": "chart",
            "kind": kind,
            "title": title,
            "localized_title": _localize_text(title) or title,
            "file_name": path.name,
            "path": str(path.resolve()),
            "recommended_page_role": role,
            "insight_input": insight,
            "source_metric_names": sorted(source_metric_names),
            "source_dimension_names": sorted(source_dimension_names),
            "visual_contract_tokens": {
                "preferred_chart_kinds": list(_active_chart_style().get("preferred_chart_kinds") or []),
                "avoid_chart_kinds": list(_active_chart_style().get("avoid_chart_kinds") or []),
                "chart_grammar_contract": dict(_active_chart_style().get("chart_grammar_contract") or {}),
                "chart_grammar_tokens": list(_active_chart_style().get("chart_grammar_tokens") or []),
                "dominant_chart_grammar": str(_active_chart_style().get("dominant_chart_grammar") or ""),
                "matched_chart_grammar": _chart_kind_matches_grammar(kind),
                "source_chart_grammar_profile_ids": source_profile_ids,
                "required_chart_kinds_in_source": required_kinds,
                "accent": _style_color("accent", "#1d8bc8"),
                "frame": str(_active_chart_style().get("frame") or ""),
            },
            "source_view": source_view,
            "management_use": management_use,
            "status": "completed",
        }
    )


def _append_skipped_asset(
    assets: list[dict[str, Any]],
    *,
    chart_id: str,
    kind: str,
    title: str,
    role: str,
    source_view: str,
    reason: str,
) -> None:
    assets.append(
        {
            "chart_id": chart_id,
            "asset_type": "chart",
            "kind": kind,
            "title": title,
            "localized_title": _localize_text(title) or title,
            "file_name": "",
            "path": "",
            "recommended_page_role": role,
            "insight_input": {},
            "source_view": source_view,
            "management_use": "",
            "status": "skipped",
            "reason": reason,
        }
    )


def _safe_id(value: Any, *, fallback: str) -> str:
    text = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in str(value or "").strip())
    text = "_".join(part for part in text.split("_") if part)
    return text[:80] or fallback


def _metric_distributions_from_manifest(manifest_payload: dict[str, Any], *, limit: int = 10) -> list[dict[str, Any]]:
    source_artifacts = dict(manifest_payload.get("source_artifacts") or {})
    metric_path = Path(str(source_artifacts.get("metric_inventory") or "")).expanduser()
    metric_inventory = _read_json_payload(metric_path) if metric_path.exists() else {}
    distributions: list[dict[str, Any]] = []
    for index, metric in enumerate(list(metric_inventory.get("metrics") or [])[:limit], start=1):
        if not isinstance(metric, dict):
            continue
        raw_key = str(metric.get("raw_key") or metric.get("metric_raw_key") or "").strip()
        label = str(metric.get("localized_label") or metric.get("metric_localized_label") or raw_key or f"指标{index}").strip()
        values = [metric.get("min"), metric.get("q25"), metric.get("median"), metric.get("q75"), metric.get("max")]
        numeric_values = _as_number_list(values)
        if len(numeric_values) < 5 or not raw_key:
            continue
        if max(abs(value) for value in numeric_values) == 0:
            continue
        distributions.append(
            {
                "id": f"metric_distribution_{_safe_id(raw_key, fallback=str(index))}",
                "kind": "histogram",
                "title": f"{label} 分布",
                "x": ["最小值", "下四分位", "中位数", "上四分位", "最大值"],
                "y": numeric_values,
                "insight_input": dict(metric),
            }
        )
    return distributions


def _cube_categories_from_manifest(manifest_payload: dict[str, Any], *, limit: int = 18) -> list[dict[str, Any]]:
    source_artifacts = dict(manifest_payload.get("source_artifacts") or {})
    cube_path = Path(str(source_artifacts.get("dimension_metric_cube") or "")).expanduser()
    cube_payload = _read_json_payload(cube_path) if cube_path.exists() else {}
    categories: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in list(cube_payload.get("cube") or []):
        if not isinstance(item, dict):
            continue
        dimension_key = str(item.get("dimension_raw_key") or "").strip()
        metric_key = str(item.get("metric_raw_key") or "").strip()
        if not dimension_key or not metric_key:
            continue
        key = f"{dimension_key}::{metric_key}"
        if key in seen:
            continue
        seen.add(key)
        rows = [row for row in list(item.get("rows") or []) if isinstance(row, dict)]
        rows.sort(key=lambda row: float(row.get("value") or 0), reverse=True)
        labels = [str(row.get("dimension_value_label") or row.get("dimension_value_raw") or "").strip() for row in rows[:12]]
        values = _as_number_list([row.get("value") for row in rows[:12]])
        if not labels or not values:
            continue
        dim_label = str(item.get("dimension_localized_label") or dimension_key)
        metric_label = str(item.get("metric_localized_label") or metric_key)
        aggregation = str(item.get("aggregation") or "").strip()
        share_eligible = aggregation == "sum" and any(
            row.get("share_semantics") == "contribution_share" and row.get("share_of_total") is not None
            for row in rows
        )
        categories.append(
            {
                "id": f"cube_{_safe_id(dimension_key, fallback='dimension')}_{_safe_id(metric_key, fallback='metric')}",
                "kind": "bar",
                "title": f"{dim_label} x {metric_label} {'贡献结构' if share_eligible else '分层对比'}",
                "x": labels,
                "y": values,
                "aggregation": aggregation,
                "share_eligible": share_eligible,
                "insight_input": dict(item),
            }
        )
        if len(categories) >= limit:
            break
    return categories


def _source_artifact_path(workspace: Path, manifest_payload: dict[str, Any], key: str, fallback_name: str) -> Path:
    source_artifacts = dict(manifest_payload.get("source_artifacts") or {})
    raw = str(source_artifacts.get(key) or "").strip()
    path = Path(raw).expanduser() if raw else workspace / fallback_name
    if not path.is_absolute():
        path = workspace / path
    return path


def _read_snapshot_rows(path: Path, *, limit: int = 8000) -> list[dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            return [dict(row) for _index, row in zip(range(limit), reader)]
    except Exception:
        return []


def _to_float(value: Any) -> float | None:
    text = str(value or "").strip().replace(",", "")
    if not text:
        return None
    try:
        return float(text)
    except Exception:
        return None


def _choose_line_axis(rows: list[dict[str, str]]) -> str:
    if not rows:
        return ""
    columns = list(rows[0].keys())
    time_patterns = re.compile(r"(date|month|quarter|week|period|time|日期|月份|季度|周期|时间)", re.I)
    for column in columns:
        if time_patterns.search(column):
            unique = {str(row.get(column) or "").strip() for row in rows if str(row.get(column) or "").strip()}
            if len(unique) >= 4:
                return column
    best_column = ""
    best_unique = 0
    for column in columns:
        values = [str(row.get(column) or "").strip() for row in rows if str(row.get(column) or "").strip()]
        unique = set(values)
        if 4 <= len(unique) <= 18 and len(unique) > best_unique:
            best_column = column
            best_unique = len(unique)
    return best_column


def _choose_line_metrics(rows: list[dict[str, str]], axis: str, *, limit: int = 4) -> list[str]:
    if not rows:
        return []
    columns = [column for column in rows[0].keys() if column != axis]
    scored: list[tuple[float, str]] = []
    metric_hint = re.compile(r"(sales|revenue|gmv|order|count|margin|rate|satisfaction|traffic|value|index|amount|销售|收入|订单|金额|毛利|转化|复购|满意|流量|指数|数量)", re.I)
    for column in columns:
        numeric = [_to_float(row.get(column)) for row in rows[:400]]
        values = [value for value in numeric if value is not None]
        if len(values) < max(8, int(len(rows[:400]) * 0.25)):
            continue
        spread = max(values) - min(values)
        if spread <= 0:
            continue
        score = spread / max(1.0, abs(sum(values) / len(values)))
        if metric_hint.search(column):
            score += 3.0
        scored.append((score, column))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [column for _score, column in scored[:limit]]


def _aggregate_line_series(rows: list[dict[str, str]], axis: str, metrics: list[str]) -> tuple[list[str], list[dict[str, Any]], dict[str, Any]]:
    grouped: dict[str, dict[str, list[float]]] = {}
    for row in rows:
        label = str(row.get(axis) or "").strip()
        if not label:
            continue
        bucket = grouped.setdefault(label, {metric: [] for metric in metrics})
        for metric in metrics:
            value = _to_float(row.get(metric))
            if value is not None:
                bucket.setdefault(metric, []).append(value)
    if not grouped:
        return [], [], {}
    labels = sorted(grouped)
    if len(labels) > 12:
        # Dates sort lexically in ISO form. For non-date categories, this still
        # gives a stable indexed profile rather than a random top-N list.
        step = max(1, len(labels) // 12)
        labels = labels[::step][:12]
    series: list[dict[str, Any]] = []
    for metric in metrics:
        values: list[float] = []
        for label in labels:
            samples = grouped.get(label, {}).get(metric, [])
            if not samples:
                values.append(0.0)
            elif re.search(r"(rate|margin|satisfaction|turn|depth|指数|率|满意|周转|折扣)", metric, re.I):
                values.append(sum(samples) / len(samples))
            else:
                values.append(sum(samples))
        if len(values) >= 2 and max(values) != min(values):
            series.append({"name": _localize_text(metric) or metric, "metric_raw_key": metric, "values": values})
    insight_input = {
        "x_axis": axis,
        "dimension_raw_key": axis,
        "metric_raw_keys": metrics,
        "source_metric_names": metrics,
        "source_dimension_names": [axis],
        "management_use": "source_chart_grammar_matched_indexed_multi_line",
    }
    primary = series[0] if series else {}
    primary_values = _as_number_list(primary.get("values"))
    primary_metric = str(primary.get("metric_raw_key") or primary.get("name") or (metrics[0] if metrics else "")).strip()
    if primary_values:
        insight_input.update({
            "metric_raw_key": primary_metric,
            "metric": primary_metric,
            "min": min(primary_values),
            "max": max(primary_values),
            "median": sorted(primary_values)[len(primary_values) // 2],
            "rows": [
                {"dimension": axis, "metric": primary_metric, "segment": label, "value": value}
                for label, value in zip(labels[:12], primary_values[:12])
            ],
        })
    return labels, series, insight_input


def _indexed_line_spec_from_snapshot(workspace: Path, manifest_payload: dict[str, Any]) -> dict[str, Any]:
    snapshot_path = _source_artifact_path(workspace, manifest_payload, "data_snapshot", "historical_data_snapshot.csv")
    rows = _read_snapshot_rows(snapshot_path)
    axis = _choose_line_axis(rows)
    metrics = _choose_line_metrics(rows, axis, limit=4) if axis else []
    labels, series, insight_input = _aggregate_line_series(rows, axis, metrics)
    if len(labels) < 2 or len(series) < 2:
        return {
            "status": "skipped",
            "reason": "snapshot_lacks_axis_or_multi_metric_series",
            "snapshot_path": str(snapshot_path.resolve()) if snapshot_path.exists() else "",
        }
    return {
        "status": "completed",
        "id": "source_like_indexed_multi_line",
        "kind": "right_labeled_index_line",
        "title": "核心指标指数化趋势对比",
        "x": labels,
        "series": series,
        "insight_input": insight_input,
        "snapshot_path": str(snapshot_path.resolve()),
    }


def _expected_chart_specs() -> dict[str, dict[str, str]]:
    return {
        "distribution": {"source_view": "historical_metric_inventory.json", "management_use": "用于识别指标分布是否集中、是否存在长尾与异常区间。"},
        "distribution_cumulative": {"source_view": "historical_metric_inventory.json", "management_use": "用于识别贡献是否由少数区间集中驱动。"},
        "category_mix": {"source_view": "historical_dimension_metric_cube.json", "management_use": "用于展示关键业务维度的规模结构。"},
        "category_share_donut": {"source_view": "historical_dimension_metric_cube.json", "management_use": "用于展示头部结构占比与组合集中度。"},
        "category_pareto": {"source_view": "historical_dimension_metric_cube.json", "management_use": "用于识别头部贡献与长尾稀释边界。"},
        "category_value_bridge": {"source_view": "historical_cross_dimension_priority_tables.json", "management_use": "用于展示不同业务单元如何累积构成总量贡献。"},
        "category_priority_bubble": {"source_view": "historical_cross_dimension_priority_tables.json", "management_use": "用于同时比较规模、重要性与资源优先级。"},
        "correlation_heatmap": {"source_view": "historical_pairwise_relationships.json", "management_use": "用于识别经营变量之间的强弱联动关系。"},
        "correlation_top_pairs": {"source_view": "historical_pairwise_relationships.json", "management_use": "用于突出最值得管理层关注的高相关组合。"},
        "scatter": {"source_view": "historical_segment_scorecards.json", "management_use": "用于观察两个关键指标之间的基础关系分布。"},
        "scatter_quadrant": {"source_view": "historical_segment_scorecards.json", "management_use": "用于把对象分到高价值、观察和风险象限。"},
        "scatter_portfolio_matrix": {"source_view": "historical_cross_dimension_priority_tables.json", "management_use": "用于形成 2x2 组合矩阵，服务资源取舍与优先级讨论。"},
    }


def _render_category_family(
    *,
    asset_dir: Path,
    assets: list[dict[str, Any]],
    category: dict[str, Any],
    prefix: str,
) -> None:
    labels = _localize_labels(_as_text_list(category.get("x"), limit=12))
    values = _as_number_list(category.get("y"))[: len(labels)]
    if not labels or not values:
        return
    title = _localize_text(_safe_title(category.get("title"), "Category Mix"))
    insight_input = dict(category.get("insight_input") or {})
    aggregation = str(category.get("aggregation") or insight_input.get("aggregation") or "").strip()
    share_eligible = category.get("share_eligible")
    if share_eligible is None:
        share_eligible = aggregation == "sum"
    path = asset_dir / f"{prefix}.svg"
    if _chart_kind_preferred("paired_horizontal_bar"):
        _write_text(path, _render_paired_horizontal_bars(title, labels, values, insight_input))
        source_profile_pack = _active_chart_style().get("source_chart_grammar_profile_pack")
        required_source_kinds = {
            str(item or "").strip()
            for item in list((source_profile_pack if isinstance(source_profile_pack, dict) else {}).get("required_chart_kinds") or [])
            if str(item or "").strip()
        }
        paired_kind = "paired_horizontal_bar_with_delta" if "paired_horizontal_bar_with_delta" in required_source_kinds else "paired_horizontal_bar"
        _append_asset(assets, path=path, chart_id=prefix, kind=paired_kind, title=title, role="category_mix_page", insight_input=insight_input)
    elif _chart_kind_preferred("vertical_bar"):
        _write_text(path, _render_vertical_bar_like(title, labels, values, kind_label="category"))
        _append_asset(assets, path=path, chart_id=prefix, kind="vertical_bar", title=title, role="category_mix_page", insight_input=insight_input)
    else:
        _write_text(path, _render_bar_like(title, labels, values, kind_label="category"))
        _append_asset(assets, path=path, chart_id=prefix, kind="bar", title=title, role="category_mix_page", insight_input=insight_input)
    if share_eligible and len(labels) >= 2 and not (
        _chart_kind_avoided("decorative_donut")
        or _chart_kind_avoided("donut")
        or _chart_kind_avoided("pie")
    ):
        donut_title = _localize_text(f"{title} Share Map")
        donut_path = asset_dir / f"{prefix}_share_donut.svg"
        _write_text(donut_path, _render_donut(donut_title, labels, values))
        _append_asset(assets, path=donut_path, chart_id=f"{prefix}_share_donut", kind="donut", title=donut_title, role="share_composition_page", insight_input=insight_input)
    if share_eligible and len(labels) >= 3:
        pareto_title = _localize_text(f"{title} Pareto View")
        pareto_path = asset_dir / f"{prefix}_pareto.svg"
        _write_text(pareto_path, _render_pareto(pareto_title, labels, values))
        _append_asset(assets, path=pareto_path, chart_id=f"{prefix}_pareto", kind="pareto", title=pareto_title, role="pareto_priority_page", insight_input=insight_input)
        bridge_title = _localize_text(f"{title} Value Bridge")
        bridge_path = asset_dir / f"{prefix}_value_bridge.svg"
        _write_text(bridge_path, _render_waterfall_bridge(bridge_title, labels, values))
        _append_asset(assets, path=bridge_path, chart_id=f"{prefix}_value_bridge", kind="waterfall_bridge", title=bridge_title, role="value_bridge_page", insight_input=insight_input)
        bubble_title = _localize_text(f"{title} Priority Bubble Map")
        bubble_path = asset_dir / f"{prefix}_priority_bubble.svg"
        _write_text(bubble_path, _render_priority_bubble_map(bubble_title, labels, values))
        _append_asset(assets, path=bubble_path, chart_id=f"{prefix}_priority_bubble", kind="priority_bubble", title=bubble_title, role="priority_bubble_page", insight_input=insight_input)


def _render_distribution_family(
    *,
    asset_dir: Path,
    assets: list[dict[str, Any]],
    distribution: dict[str, Any],
    prefix: str,
) -> None:
    labels = _localize_labels(_as_text_list(distribution.get("x"), limit=18))
    values = _as_number_list(distribution.get("y"))[: len(labels)]
    if not labels or not values:
        return
    title = _localize_text(_safe_title(distribution.get("title"), "Distribution"))
    insight_input = dict(distribution.get("insight_input") or {})
    path = asset_dir / f"{prefix}.svg"
    if _chart_kind_preferred("vertical_bar"):
        _write_text(path, _render_vertical_bar_like(title, labels, values, kind_label="distribution"))
        _append_asset(assets, path=path, chart_id=prefix, kind="vertical_bar", title=title, role="distribution_overview", insight_input=insight_input)
    else:
        _write_text(path, _render_bar_like(title, labels, values, kind_label="distribution"))
        _append_asset(assets, path=path, chart_id=prefix, kind="histogram", title=title, role="distribution_overview", insight_input=insight_input)
    if len(labels) >= 3:
        cumulative_title = _localize_text(f"{title} Cumulative Curve")
        cumulative_path = asset_dir / f"{prefix}_cumulative.svg"
        _write_text(cumulative_path, _render_cumulative_line(cumulative_title, labels, values))
        _append_asset(assets, path=cumulative_path, chart_id=f"{prefix}_cumulative", kind="line", title=cumulative_title, role="trend_cumulative_page", insight_input=insight_input)


def render_historical_chart_asset_pack(
    *,
    workspace: Path,
    chart_bundle_path: Path,
    data_asset_manifest_path: Path | None = None,
    asset_dir_name: str = "historical_chart_assets",
    index_name: str = "historical_chart_assets_index.json",
) -> dict[str, Any]:
    chart_style = _chart_style_for_workspace(workspace)
    _ACTIVE_CHART_STYLE.set(chart_style)
    manifest_payload: dict[str, Any] = {}
    if data_asset_manifest_path is None:
        candidate = workspace / "historical_data_asset_manifest.json"
        data_asset_manifest_path = candidate if candidate.exists() else None
    if data_asset_manifest_path and data_asset_manifest_path.exists():
        try:
            manifest_payload = json.loads(data_asset_manifest_path.read_text(encoding="utf-8-sig"))
        except Exception:
            manifest_payload = {}
        source_artifacts = dict(manifest_payload.get("source_artifacts") or {})
        chart_bundle_candidate = Path(str(source_artifacts.get("chart_bundle") or "")).expanduser()
        if chart_bundle_candidate.exists():
            chart_bundle_path = chart_bundle_candidate
    chart_bundle = json.loads(chart_bundle_path.read_text(encoding="utf-8-sig"))
    if not isinstance(chart_bundle, dict):
        chart_bundle = {}
    asset_dir = workspace / asset_dir_name
    asset_dir.mkdir(parents=True, exist_ok=True)
    assets: list[dict[str, Any]] = []
    source_profile_pack = chart_style.get("source_chart_grammar_profile_pack")
    required_source_kinds = {
        str(item or "").strip()
        for item in list((source_profile_pack if isinstance(source_profile_pack, dict) else {}).get("required_chart_kinds") or [])
        if str(item or "").strip()
    }
    if required_source_kinds & {"indexed_multi_line", "right_labeled_index_line"}:
        line_spec = _indexed_line_spec_from_snapshot(workspace, manifest_payload)
        if str(line_spec.get("status") or "") == "completed":
            line_path = asset_dir / "source_like_indexed_multi_line.svg"
            title = _localize_text(line_spec.get("title")) or str(line_spec.get("title") or "Indexed Multi-line")
            _write_text(
                line_path,
                _render_indexed_multi_line(
                    title,
                    _as_text_list(line_spec.get("x"), limit=12),
                    [dict(item) for item in list(line_spec.get("series") or []) if isinstance(item, dict)],
                    dict(line_spec.get("insight_input") or {}),
                ),
            )
            _append_asset(
                assets,
                path=line_path,
                chart_id="source_like_indexed_multi_line",
                kind="right_labeled_index_line",
                title=title,
                role="source_matched_index_line_page",
                insight_input=dict(line_spec.get("insight_input") or {}),
                source_view="historical_data_snapshot.csv",
                management_use="Matches a source-page indexed/multi-line chart grammar when the historical PDF uses line exhibits.",
            )
        else:
            _append_skipped_asset(
                assets,
                chart_id="source_like_indexed_multi_line",
                kind="right_labeled_index_line",
                title="Indexed Multi-line",
                role="source_matched_index_line_page",
                source_view="historical_data_snapshot.csv",
                reason=str(line_spec.get("reason") or "not_eligible"),
            )

    distribution = chart_bundle.get("distribution") or {}
    if distribution:
        _render_distribution_family(asset_dir=asset_dir, assets=assets, distribution=distribution, prefix="distribution")
    for index, extra_distribution in enumerate(list(chart_bundle.get("extra_distributions") or [])[:8], start=1):
        if isinstance(extra_distribution, dict):
            prefix = _safe_id(extra_distribution.get("id"), fallback=f"distribution_extra_{index:02d}")
            _render_distribution_family(asset_dir=asset_dir, assets=assets, distribution=extra_distribution, prefix=prefix)
    existing_distribution_ids = {
        str((asset.get("insight_input") or {}).get("raw_key") or (asset.get("insight_input") or {}).get("metric_raw_key") or "")
        for asset in assets
    }
    for extra_distribution in _metric_distributions_from_manifest(manifest_payload, limit=10):
        metric_key = str((extra_distribution.get("insight_input") or {}).get("raw_key") or "").strip()
        if metric_key and metric_key in existing_distribution_ids:
            continue
        prefix = _safe_id(extra_distribution.get("id"), fallback=f"metric_distribution_{len(assets)+1:02d}")
        _render_distribution_family(asset_dir=asset_dir, assets=assets, distribution=extra_distribution, prefix=prefix)
        if metric_key:
            existing_distribution_ids.add(metric_key)

    category = chart_bundle.get("category") or {}
    if category:
        _render_category_family(asset_dir=asset_dir, assets=assets, category=category, prefix="category_mix")
    for index, extra_category in enumerate(list(chart_bundle.get("extra_categories") or [])[:10], start=1):
        if isinstance(extra_category, dict):
            prefix = _safe_id(extra_category.get("id"), fallback=f"category_extra_{index:02d}")
            _render_category_family(asset_dir=asset_dir, assets=assets, category=extra_category, prefix=prefix)
    existing_category_ids = {
        (
            str((asset.get("insight_input") or {}).get("dimension_raw_key") or ""),
            str((asset.get("insight_input") or {}).get("metric_raw_key") or ""),
        )
        for asset in assets
    }
    for extra_category in _cube_categories_from_manifest(manifest_payload, limit=18):
        insight = dict(extra_category.get("insight_input") or {})
        key = (str(insight.get("dimension_raw_key") or ""), str(insight.get("metric_raw_key") or ""))
        if key in existing_category_ids:
            continue
        prefix = _safe_id(extra_category.get("id"), fallback=f"cube_category_{len(assets)+1:02d}")
        _render_category_family(asset_dir=asset_dir, assets=assets, category=extra_category, prefix=prefix)
        existing_category_ids.add(key)

    correlation = chart_bundle.get("correlation") or {}
    if correlation:
        labels = _localize_labels(_as_text_list(correlation.get("labels"), limit=8))
        matrix = correlation.get("matrix") or []
        title = _localize_text(_safe_title(correlation.get("title"), "Correlation Map"))
        insight_input = dict(correlation.get("insight_input") or {})
        svg = _render_heatmap(title, labels, matrix)
        path = asset_dir / "correlation_heatmap.svg"
        _write_text(path, svg)
        _append_asset(assets, path=path, chart_id="correlation_heatmap", kind="heatmap", title=title, role="correlation_page", insight_input=insight_input)
        if len(labels) >= 3 and matrix:
            pairs_title = _localize_text(f"{title} Top Pairs")
            pairs_path = asset_dir / "correlation_top_pairs.svg"
            _write_text(pairs_path, _render_correlation_pairs(pairs_title, labels, matrix))
            _append_asset(assets, path=pairs_path, chart_id="correlation_top_pairs", kind="bar", title=pairs_title, role="correlation_pairs_page", insight_input=insight_input)

    scatter = chart_bundle.get("scatter") or {}
    if scatter:
        points = _as_scatter_points(scatter.get("points") or [])
        title = _localize_text(_safe_title(scatter.get("title"), "Scatter Analysis"))
        x_label = _localize_text(_safe_title(scatter.get("x_label"), "X"))
        y_label = _localize_text(_safe_title(scatter.get("y_label"), "Y"))
        insight_input = dict(scatter.get("insight_input") or {})
        svg = _render_scatter(
            title,
            x_label,
            y_label,
            points,
        )
        path = asset_dir / "scatter.svg"
        _write_text(path, svg)
        _append_asset(assets, path=path, chart_id="scatter", kind="scatter", title=title, role="relationship_page", insight_input=insight_input)
        if len(points or []) >= 8:
            quadrant_title = _localize_text(f"{title} Quadrant Map")
            quadrant_path = asset_dir / "scatter_quadrant.svg"
            _write_text(quadrant_path, _render_scatter_quadrant(quadrant_title, x_label, y_label, points))
            _append_asset(assets, path=quadrant_path, chart_id="scatter_quadrant", kind="scatter_quadrant", title=quadrant_title, role="scatter_diagnosis_page", insight_input=insight_input)
            matrix_title = _localize_text(f"{title} 2x2 Portfolio Matrix")
            matrix_path = asset_dir / "scatter_portfolio_matrix.svg"
            _write_text(matrix_path, _render_scatter_portfolio_matrix(matrix_title, x_label, y_label, points))
            _append_asset(assets, path=matrix_path, chart_id="scatter_portfolio_matrix", kind="portfolio_matrix", title=matrix_title, role="portfolio_matrix_page", insight_input=insight_input)
    for index, extra_scatter in enumerate(list(chart_bundle.get("extra_scatters") or [])[:6], start=1):
        if not isinstance(extra_scatter, dict):
            continue
        points = _as_scatter_points(extra_scatter.get("points") or [])
        if not points:
            continue
        prefix = _safe_id(extra_scatter.get("id"), fallback=f"scatter_extra_{index:02d}")
        title = _localize_text(_safe_title(extra_scatter.get("title"), "Scatter Analysis"))
        x_label = _localize_text(_safe_title(extra_scatter.get("x_label"), "X"))
        y_label = _localize_text(_safe_title(extra_scatter.get("y_label"), "Y"))
        insight_input = dict(extra_scatter.get("insight_input") or {})
        path = asset_dir / f"{prefix}.svg"
        _write_text(path, _render_scatter(title, x_label, y_label, points))
        _append_asset(assets, path=path, chart_id=prefix, kind="scatter", title=title, role="relationship_page", insight_input=insight_input)

    specs = _expected_chart_specs()
    existing_ids = {str(asset.get("chart_id") or "") for asset in assets}
    for asset in assets:
        chart_id = str(asset.get("chart_id") or "")
        spec = specs.get(chart_id, {})
        asset["localized_title"] = asset.get("localized_title") or _localize_text(asset.get("title")) or asset.get("title")
        asset["source_view"] = asset.get("source_view") or spec.get("source_view", "")
        asset["management_use"] = asset.get("management_use") or spec.get("management_use", "")
        asset["status"] = asset.get("status") or "completed"
    for chart_id, spec in specs.items():
        if chart_id in existing_ids:
            continue
        _append_skipped_asset(
            assets,
            chart_id=chart_id,
            kind="chart",
            title=spec.get("source_view", chart_id),
            role="thesis_chart_page",
            source_view=spec.get("source_view", ""),
            reason="input_bundle_missing_or_not_eligible",
        )

    index_payload = {
        "asset_dir": str(asset_dir.resolve()),
        "chart_count": sum(1 for asset in assets if str(asset.get("status") or "") == "completed"),
        "expected_chart_count": len(specs),
        "visual_style_signature": chart_style.get("visual_style_signature") or {},
        "style_transfer_contract": chart_style.get("style_transfer_contract") or {},
        "chart_style_constraints": {
            "preferred_chart_kinds": chart_style.get("preferred_chart_kinds") or [],
            "avoid_chart_kinds": chart_style.get("avoid_chart_kinds") or [],
            "dominant_chart_grammar": chart_style.get("dominant_chart_grammar") or "",
            "chart_grammar_contract": chart_style.get("chart_grammar_contract") or {},
            "chart_grammar_tokens": chart_style.get("chart_grammar_tokens") or [],
            "accent": chart_style.get("accent"),
            "frame": chart_style.get("frame"),
        },
        "assets": assets,
    }
    index_path = workspace / index_name
    _write_text(index_path, json.dumps(index_payload, ensure_ascii=False, indent=2))
    return {
        "index_path": str(index_path.resolve()),
        "asset_dir": str(asset_dir.resolve()),
        "chart_count": len(assets),
        "assets": assets,
    }
