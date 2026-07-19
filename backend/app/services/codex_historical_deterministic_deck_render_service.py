from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any

from app.services.codex_historical_localization_service import localize_historical_text


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


_MOJIBAKE_RE = re.compile(r"[閿鏂鍙鍥鐩绠鏉娓犲愬噺鏍熸垚]{2,}|[�]")


def _looks_mojibake(text: str) -> bool:
    return bool(_MOJIBAKE_RE.search(str(text or "")))


def _fallback_clean_sentence(text: str = "") -> str:
    lower = str(text or "").lower()
    if any(token in lower for token in ("revenue", "sales", "growth", "order")):
        return "增长信号集中在少数渠道、区域或品类，管理层需要区分可复制增长和一次性波动。"
    if any(token in lower for token in ("margin", "profit", "price", "cost", "discount")):
        return "利润质量与价格、折扣和成本结构有关，应把规模增长和经济性放在同一页判断。"
    if any(token in lower for token in ("segment", "customer", "persona")):
        return "不同客群呈现不同价值、复购和服务需求，应采用分层经营动作。"
    if any(token in lower for token in ("correlation", "driver", "relationship")):
        return "指标关系提示可控经营杠杆，适合转化为跨团队行动清单。"
    return ""


def _visual_reference(workspace: Path) -> dict[str, Any]:
    return _read_json(workspace / "historical_visual_reference.json")


def _style_contract(workspace: Path, *, family: str = "") -> dict[str, Any]:
    visual = _visual_reference(workspace)
    contract = visual.get("style_transfer_contract")
    base_contract = dict(contract) if isinstance(contract, dict) else {}
    semantic = _read_json(workspace / "visual_semantic_spec.json")
    semantic_regions = dict(semantic.get("layout_region_contract") or {})
    semantic_colors = dict(semantic.get("color_tokens") or {})
    semantic_page = dict(semantic.get("page_tokens") or {})
    semantic_layout = dict(semantic.get("layout_tokens") or {})
    semantic_furniture = dict(semantic.get("furniture_tokens") or {})
    if base_contract:
        merged = dict(base_contract)
        base_colors = dict(base_contract.get("colors") or {})
        merged_colors = {**base_colors, **semantic_colors}
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
                    merged_colors[key] = base_colors[key]
        merged["colors"] = merged_colors
        if semantic_regions:
            regions = dict(base_contract.get("regions") or {})
            regions["average_regions"] = {**dict(regions.get("average_regions") or {}), **semantic_regions}
            for key in (
                "title_region_norm",
                "primary_visual_region_norm",
                "right_annotation_region_norm",
                "narrative_region_norm",
                "footer_region_norm",
                "margin_norm",
            ):
                if key in semantic_regions:
                    regions[key] = semantic_regions[key]
            merged["regions"] = regions
        merged["page"] = {**dict(base_contract.get("page") or {}), **semantic_page}
        merged["layout"] = {**dict(base_contract.get("layout") or {}), **semantic_layout}
        merged["furniture"] = {**dict(base_contract.get("furniture") or {}), **semantic_furniture}
        return merged
    orientation = str((visual.get("page_orientation_summary") or {}).get("dominant_orientation") or "")
    if not orientation:
        orientation = "landscape"
    return {
        "page": {
            "orientation": orientation,
            "width_mm": 210 if orientation == "portrait" else 297,
            "height_mm": 297 if orientation == "portrait" else 210,
            "margin_top_mm": 20 if orientation == "portrait" else 18,
            "margin_x_mm": 18 if orientation == "portrait" else 20,
        },
        "colors": {
            "background": "#ffffff",
            "accent": semantic_colors.get("accent") or (visual.get("accent_palette_hint") or visual.get("dominant_palette_hint") or ["#1f5f9f"])[0],
            "accent_soft": "#eef6f2",
            "text": "#4a4a4a",
            "heading": semantic_colors.get("heading") or semantic_colors.get("accent") or (visual.get("accent_palette_hint") or visual.get("dominant_palette_hint") or ["#1f5f9f"])[0],
            "muted": "#8a8a8a",
            "rule": "#d6d6d6",
        },
        "furniture": {
            "side_rail": False,
            "footer_mode": "source_note_page_number",
            "exhibit_mode": "numbered_exhibit",
            "source_note_footer": True,
        },
        "layout": {
            "body_columns": 2 if orientation == "portrait" else 1,
            "primary_visual_ratio": 0.58,
            "visual_text_ratio": 0.58,
            "density_mode": "moderate",
            "balance_mode": "balanced_exhibit",
        },
        "layout_harmony": {
            "available": False,
            "version": "layout-harmony-fallback",
            "balance_mode": "balanced_exhibit",
            "density_mode": "moderate",
            "margin_mode": "standard",
            "recommended_content_columns": 2 if orientation == "portrait" else 1,
            "recommended_visual_text_ratio": 0.58,
            "recommended_section_gap_ratio": 0.025,
            "recommended_page_grid": f"{orientation}_balanced_exhibit",
            "harmony_rules": ["keep_title_visual_gap", "reserve_footer_clearance"],
        },
        "regions": semantic_regions,
    }


def _contract_page_size(contract: dict[str, Any]) -> tuple[int, int, str]:
    page = dict(contract.get("page") or {})
    width = int(page.get("width_mm") or 297)
    height = int(page.get("height_mm") or 210)
    orientation = str(page.get("orientation") or ("landscape" if width > height else "portrait"))
    return width, height, orientation


def _contract_color(contract: dict[str, Any], key: str, fallback: str) -> str:
    colors = dict(contract.get("colors") or {})
    value = str(colors.get(key) or fallback).strip()
    return value if re.fullmatch(r"#[0-9a-fA-F]{6}", value) else fallback


def _region_box(contract: dict[str, Any], key: str) -> list[float]:
    regions = dict(contract.get("regions") or {})
    value = regions.get(key)
    if not isinstance(value, list) or len(value) != 4:
        return []
    try:
        box = [max(0.0, min(1.0, float(item))) for item in value]
    except Exception:
        return []
    if box[2] <= box[0] or box[3] <= box[1]:
        return []
    return box


def _region_mm_box(contract: dict[str, Any], key: str) -> list[float]:
    width_mm, height_mm, _orientation = _contract_page_size(contract)
    box = _region_box(contract, key)
    if not box:
        return []
    return [
        round(box[0] * width_mm, 2),
        round(box[1] * height_mm, 2),
        round(box[2] * width_mm, 2),
        round(box[3] * height_mm, 2),
    ]


def _contract_region_css(contract: dict[str, Any]) -> dict[str, Any]:
    width_mm, height_mm, orientation = _contract_page_size(contract)
    page = dict(contract.get("page") or {})
    margin_x = float(page.get("margin_x_mm") or (18 if orientation == "portrait" else 20))
    margin_top = float(page.get("margin_top_mm") or (18 if orientation == "portrait" else 18))
    title = _region_mm_box(contract, "title_region_norm")
    visual = _region_mm_box(contract, "primary_visual_region_norm")
    narrative = _region_mm_box(contract, "narrative_region_norm")
    footer = _region_mm_box(contract, "footer_region_norm")
    right_annotation = _region_mm_box(contract, "right_annotation_region_norm")

    if not title:
        title = [margin_x, margin_top, width_mm - margin_x, margin_top + (34 if orientation == "portrait" else 28)]
    if not visual:
        visual = [
            margin_x,
            title[3] + 4,
            width_mm - margin_x,
            min(height_mm - 36, title[3] + (128 if orientation == "portrait" else 96)),
        ]
    if not footer:
        footer = [margin_x, height_mm - 18, width_mm - margin_x, height_mm - 8]
    if not narrative:
        narrative = [margin_x, min(footer[1] - 28, visual[3] + 4), width_mm - margin_x, footer[1] - 3]

    content_left = max(6.0, min(42.0, min(title[0], visual[0], narrative[0])))
    content_right = max(6.0, min(42.0, width_mm - max(title[2], visual[2], narrative[2])))
    title_top = max(6.0, min(height_mm - 40.0, title[1]))
    title_height = max(14.0, min(45.0, title[3] - title[1]))
    visual_top = max(title_top + title_height + 2.0, min(height_mm - 80.0, visual[1]))
    footer_top = max(visual_top + 40.0, min(height_mm - 8.0, footer[1]))
    visual_height = max(44.0, min(footer_top - visual_top - 16.0, visual[3] - visual[1]))
    narrative_top = max(visual_top + visual_height + 3.0, min(footer_top - 18.0, narrative[1]))
    narrative_height = max(16.0, min(62.0, footer_top - narrative_top - 2.0))
    body_height = max(70.0, min(height_mm - visual_top - 18.0, footer_top - visual_top - 2.0))
    right_annotation_width = 0.0
    if right_annotation:
        right_annotation_width = max(0.0, right_annotation[2] - right_annotation[0])

    return {
        "available": bool((contract.get("regions") or {}).get("available")),
        "content_left_mm": round(content_left, 2),
        "content_right_mm": round(content_right, 2),
        "title_top_mm": round(title_top, 2),
        "title_height_mm": round(title_height, 2),
        "visual_top_mm": round(visual_top, 2),
        "visual_height_mm": round(visual_height, 2),
        "narrative_top_mm": round(narrative_top, 2),
        "narrative_height_mm": round(narrative_height, 2),
        "body_height_mm": round(body_height, 2),
        "footer_top_mm": round(footer_top, 2),
        "right_annotation_width_mm": round(right_annotation_width, 2),
        "right_annotation_column": right_annotation_width >= (width_mm * 0.12),
    }


def _strip_html_fragment(text: str) -> str:
    text = re.sub(r"(?is)^.*?<body[^>]*>", "", text)
    text = re.sub(r"(?is)</body>.*$", "", text)
    return text.strip()


_LABEL_REPLACEMENTS = {
    "Benchmark Callout Board": "关键指标提示板",
    "Callout Board": "提示板",
    "Executive Summary Map": "执行摘要地图",
    "Correlation Focus": "相关关系重点表",
    "Region Ranking": "区域排名",
    "Operating driver": "经营驱动因素",
    "Top Pairs": "重点组合",
    "pairs": "组合",
    "map": "图",
    "chart": "图",
    "Dimension Signal Matrix": "维度信号矩阵",
    "Priority Action Table": "优先动作表",
    "Value Bridge": "价值桥",
    "Priority Bubble Map": "优先级气泡图",
    "2x2 Portfolio Matrix": "2x2 组合矩阵",
    "Value build": "价值培育",
    "Scale and protect": "放量并保护",
    "Watch list": "观察区",
    "Price risk": "价格风险区",
    "Total": "合计",
    "net_revenue": "净收入",
    "revenue": "收入",
    "gross_margin": "毛利率",
    "margin": "毛利",
    "repeat_rate": "复购率",
    "repeat_rat": "复购率",
    "repeat_ra": "复购率",
    "repeat_r": "复购率",
    "repea": "复购率",
    "repeat_purchase_rate": "复购率",
    "conversion_rate": "转化率",
    "Repeat purchase": "复购率",
    "Price": "价格",
    "service_level": "服务水平",
    "service_l": "服务水平",
    "service_": "服务水平",
    "servi": "服务水平",
    "inventory_turns": "库存周转",
    "inventory_": "库存周转",
    "inventor": "库存周转",
    "customer_segment": "客户分层",
    "customer": "客户",
    "segment": "细分客群",
    "region": "区域",
    "channel": "渠道",
    "channels": "渠道",
    "category": "品类",
    "product": "产品",
    "sku": "SKU",
    "left": "左侧指标",
    "right": "右侧指标",
    "row_count": "样本数",
    "abs_correlation": "相关强度",
    "correlation": "相关系数",
    "marketplace": "平台",
    "direct": "直销",
    "East": "东区",
    "South": "南区",
    "North": "北区",
    "West": "西区",
    "growth": "增长",
    "gap": "差距",
    "benchmark": "对标",
    "priority": "优先级",
    "action": "动作",
    "score": "评分",
    "rank": "排名",
    "index": "指数",
    "mean": "均值",
    "sum": "合计",
}


_PHRASE_REPLACEMENTS = {
    "Revenue mix by channel Value Bridge": "渠道收入结构价值桥",
    "Revenue mix by channel Priority Bubble Map": "渠道收入优先级气泡图",
    "Revenue mix by channel Pareto View": "渠道收入帕累托视图",
    "Revenue mix by channel Share Map": "渠道收入结构份额图",
    "Revenue mix by channel": "渠道收入结构",
    "Price index vs repeat purchase rate 2x2 Portfolio Matrix": "价格指数 x 复购率 2x2 组合矩阵",
    "Price index vs repeat purchase rate": "价格指数 x 复购率",
    "repeat purchase rate": "复购率",
    "Portfolio Matrix": "组合矩阵",
    "Quadrant Map": "象限图",
    "Scale leaders": "头部放量区",
    "Repair candidates": "修复候选区",
    "Price index vs repeat purchase rate Quadrant Map": "价格指数 x 复购率象限图",
    "Operating driver correlation map Top Pairs": "经营驱动因素相关性重点组合",
    "top correlation pairs chart rendered from deterministic chart_bundle asset pack": "基于当前样本生成的相关性重点组合图",
    "waterfall bridge rendered from deterministic category mix": "基于当前样本生成的结构桥图",
    "priority bubble map rendered from deterministic category mix": "基于当前样本生成的优先级气泡图",
    "2x2 portfolio matrix rendered from deterministic scatter points": "基于当前样本生成的2x2组合矩阵",
    "Contribution bridge to total": "总量贡献结构桥",
    "high Repeat purchase  / high Price 指数": "高复购 / 高价格指数",
    "high Repeat purchase / high Price 指数": "高复购 / 高价格指数",
    "Operating driver 相关系数 map Top Pairs": "经营驱动因素相关性重点组合",
    "Gross margin distribution by category Cumulative Curve": "品类毛利累计曲线",
    "Gross margin distribution by category": "品类毛利分布",
    "Cumulative Curve": "累计曲线",
    "High Repeat Purchase / High Price Index": "高复购 / 高价格指数",
    "Low / low watchlist": "低位观察区",
    "quadrant view rendered from deterministic scatter points": "基于当前样本生成的象限诊断图",
    "distribution chart rendered from deterministic chart bundle": "基于当前样本生成的分布图",
    "distribution chart rendered from deterministic chart_bundle asset pack": "基于当前样本生成的分布图",
    "cumulative curve rendered from deterministic distribution": "基于当前分布生成的累计曲线",
    "top 相关系数 pairs chart rendered from deterministic chart_bundle asset pack": "基于当前样本生成的相关性重点组合图",
    "growth is concentrated in direct and marketplace channels, but": "增长集中在直销与平台渠道，但",
    "the management agenda should separate scale candidates from": "管理议题应区分可放量单元与需要修复的",
    "repair and service": "修复与服务可靠性",
    "channels but": "渠道，但",
    "quality differs": "质量存在差异",
    "economics": "经济性",
}


_SAFE_LABEL_REPLACEMENTS = {
    "region": "区域",
    "channel": "渠道",
    "channels": "渠道",
    "store": "门店",
    "category": "类目",
    "product": "商品",
    "customer": "客户",
    "segment": "客群",
    "rowcount": "样本数",
    "row_count": "样本数",
    "shareoftotal": "总量占比",
    "share_of_total": "总量占比",
    "liftvsoverall": "相对整体提升",
    "lift_vs_overall": "相对整体提升",
    "scaleleader": "规模领先单元",
    "repairlaggard": "修复滞后单元",
    "Seasonal": "季节型",
    "bundle": "组合",
    "Core": "核心",
    "skincare": "护肤",
    "Body": "身体",
    "care": "护理",
    "Travel": "旅行",
    "Premium": "高端",
    "anti": "抗",
    "aging": "老化",
    "date": "日期",
    "object": "对象",
    "current": "当前",
    "dataset": "数据集",
    "contains": "包含",
    "repeat": "复购",
    "service": "服务",
    "inventory": "库存",
    "regression": "回归",
    "Entry": "入口",
    "set": "集合",
    "str": "文本",
    "float64": "数值",
    "float32": "数值",
    "int64": "整数",
    "int32": "整数",
    "bcgquarterlywatch": "",
    "renderedpdfpreviews": "",
    "shortconsultingwatch": "",
    "dimension_signal_matrix": "维度信号矩阵",
    "segment_badges": "分层卡片",
    "tag_board": "信号标签板",
    "summary_map_nodes": "执行摘要节点",
    "summary_map": "执行摘要地图",
    "action_roadmap": "行动路线图",
    "benchmark_callouts": "关键指标提示板",
    "gap_matrix_blocks": "差距矩阵",
    "gap_matrix": "差距矩阵",
    "customer_scorecards": "客群评分卡",
    "scorecards": "评分卡",
    "cards": "卡片",
    "consulting": "咨询式",
    "portrait": "纵向",
    "page": "页面",
    "system": "系统",
    "visual": "视觉",
    "rhythm": "节奏",
    "structure": "结构",
    "Economics": "经营效益",
    "retention": "留存",
    "The": "",
    "should": "",
    "prove": "",
    "that": "",
    "real": "真实",
    "can": "",
    "control": "控制",
    "and": "",
}


def _apply_safe_label_replacements(text: str) -> str:
    normalized = text
    for source, target in sorted(_SAFE_LABEL_REPLACEMENTS.items(), key=lambda item: len(item[0]), reverse=True):
        normalized = re.sub(rf"(?i)(?<![A-Za-z]){re.escape(source)}(?![A-Za-z])", target, normalized)
    return normalized


def _normalize_text_labels(text: str) -> str:
    normalized = _apply_safe_label_replacements(text)
    normalized = localize_historical_text(normalized)
    for source, target in sorted(_PHRASE_REPLACEMENTS.items(), key=lambda item: len(item[0]), reverse=True):
        normalized = re.sub(re.escape(source), target, normalized, flags=re.I)
    for source, target in sorted(_LABEL_REPLACEMENTS.items(), key=lambda item: len(item[0]), reverse=True):
        normalized = re.sub(rf"(?i)\b{re.escape(source)}\b", target, normalized)
    normalized = _apply_safe_label_replacements(normalized)
    return localize_historical_text(normalized)


def _contains_cjk(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def _english_heavy(text: str) -> bool:
    letters = len(re.findall(r"[A-Za-z]", text))
    visible = len(re.findall(r"\S", text))
    cjk = len(re.findall(r"[\u4e00-\u9fff]", text))
    if visible <= 0:
        return False
    if not _contains_cjk(text):
        return letters / visible > 0.35
    return letters > 22 and letters / max(1, letters + cjk) > 0.35


def _consulting_chinese_fallback(text: str) -> str:
    lower = text.lower()
    if any(token in lower for token in ("revenue", "growth", "demand", "sales")):
        return "增长信号集中在少数渠道、品类或区域，管理层应优先判断这些单元是否具备可复制的高质量增长基础。"
    if any(token in lower for token in ("margin", "cost", "price", "profit")):
        return "利润质量与成本压力存在结构性差异，应把毛利改善、价格带管理和费用投放效率放在同一张经营看板中判断。"
    if any(token in lower for token in ("segment", "customer", "persona")):
        return "客户分层呈现出不同的价值、复购和服务需求，应采用差异化运营动作而不是平均化资源分配。"
    if any(token in lower for token in ("benchmark", "gap", "score")):
        return "对标差距已经足够形成管理议题，需要把差距拆成可负责、可衡量、可复盘的行动包。"
    return "该页资产提示一个需要管理层关注的结构性经营信号，应结合图表和明细表转化为明确的优先动作。"


def _normalize_html_fragment(fragment: str) -> str:
    return _normalize_text_labels(fragment)


def _localize_html_text_nodes(fragment: str) -> str:
    parts = re.split(r"(<[^>]+>)", fragment)
    localized: list[str] = []
    for part in parts:
        if not part:
            continue
        if part.startswith("<") and part.endswith(">"):
            localized.append(part)
        else:
            text = _normalize_text_labels(part)
            if _contains_cjk(text):
                text = _drop_residual_english_words(text)
            localized.append(text)
    return "".join(localized)


def _drop_residual_english_words(text: str) -> str:
    keep = {"CEO", "COO", "CFO", "KPI", "SKU", "ROI", "GMV", "AOV", "RFM"}

    def repl(match: re.Match[str]) -> str:
        word = match.group(0)
        return word if word.upper() in keep else " "

    return re.sub(r"\b[A-Za-z]{3,}\b", repl, text)


def _clean_text(value: Any, *, limit: int = 220) -> str:
    text = str(value or "")
    text = re.sub(r"[*`>#|]+", " ", text)
    text = re.sub(r"\s*-{2,}:?(?:\s*-{2,}:?)+\s*", " ", text)
    text = re.sub(r"\b(executive|section|sum|mean)\b", " ", text, flags=re.I)
    text = _normalize_text_labels(text)
    if _contains_cjk(text):
        text = _drop_residual_english_words(text)
    text = re.sub(r"历史\s+仅", "历史报告仅", text)
    text = text.replace("来源:", "来源：").replace("注:", "注：")
    text = text.replace("核心指标 页面", "核心指标页")
    text = text.replace("核心 核心指标", "核心指标")
    text = text.replace("核心指标 当前值", "核心指标当前值")
    text = text.replace("来源： ", "来源：").replace("注： ", "注：")
    text = text.replace("历史支持表. . 注：", "历史支持表。注：")
    text = text.replace("历史支持表.。注：", "历史支持表。注：")
    text = re.sub(r"\.\s*\.", "。", text)
    text = re.sub(r"\s+", " ", text).strip()
    if _english_heavy(text):
        text = _consulting_chinese_fallback(text)
    return text[:limit]


def _zh_asset_title(title: str) -> str:
    replacements = {
        "Benchmark Callout Board": "关键指标提示板",
        "Executive Summary Map": "执行摘要地图",
        "Signal Tag Board": "信号标签板",
        "Segment Badge Board": "细分对象卡片",
        "Module Navigation Board": "模块导航板",
        "Action Roadmap Board": "行动路线图",
        "Gap Matrix Board": "差距矩阵",
        "KPI Snapshot": "核心 KPI 快照",
        "Correlation Focus": "相关关系重点表",
        "Dimension Signal Matrix": "维度信号矩阵",
        "Priority Action Table": "优先动作表",
        "Metric & Dimension Glossary": "指标与维度口径表",
        "Appendix Detail Table": "附录明细表",
    }
    return localize_historical_text(replacements.get(title, _normalize_text_labels(title)), fallback=title)


def _relative_url(path: Path, *, html_path: Path) -> str:
    try:
        return path.resolve().relative_to(html_path.parent.resolve()).as_posix()
    except Exception:
        try:
            return path.resolve().as_uri()
        except Exception:
            return path.as_posix()


def _asset_path(asset: dict[str, Any], *, workspace: Path) -> Path:
    raw = str(asset.get("path") or "").strip()
    if raw:
        path = Path(raw)
        return path if path.is_absolute() else workspace / path
    return workspace / str(asset.get("file_name") or "")


def _hydrate_asset(asset: dict[str, Any], *, workspace: Path) -> dict[str, Any]:
    """Refresh stale layout-embedded asset metadata from current asset indexes."""

    file_name = str(asset.get("file_name") or Path(str(asset.get("path") or "")).name or "").strip()
    if not file_name:
        return asset
    for index_name in (
        "historical_chart_assets_index.json",
        "historical_table_assets_index.json",
        "historical_collage_assets_index.json",
    ):
        payload = _read_json(workspace / index_name)
        for indexed in list(payload.get("assets") or []):
            if not isinstance(indexed, dict):
                continue
            indexed_file = str(indexed.get("file_name") or Path(str(indexed.get("path") or "")).name or "").strip()
            if indexed_file == file_name:
                return {**asset, **indexed}
    return asset


def _localized_svg_path(path: Path, *, workspace: Path) -> Path:
    try:
        svg_text = path.read_text(encoding="utf-8-sig")
    except Exception:
        return path
    localized = _normalize_text_labels(svg_text)
    if localized == svg_text:
        return path
    out_dir = workspace / "historical_localized_assets"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / path.name
    out_path.write_text(localized, encoding="utf-8")
    return out_path


def _markdown_blocks(markdown_text: str, *, limit: int = 80) -> list[str]:
    cleaned = re.sub(r"```.*?```", "", markdown_text, flags=re.S)
    blocks: list[str] = []
    for raw in re.split(r"\n\s*\n", cleaned):
        if any(token in raw for token in ("建议可视化", "图表标题建议", "页面意图")):
            continue
        text = _clean_text(raw.replace("#", " ").replace("|", " "), limit=240)
        if len(text) < 18:
            continue
        blocks.append(text[:220])
        if len(blocks) >= limit:
            break
    return blocks or ["本页根据当前经营数据和历史报告结构自动生成，用于形成咨询式管理分析页面。"]


def _markdown_page_sections(markdown_text: str) -> dict[int, str]:
    matches = list(re.finditer(r"(?m)^##\s*第\s*0*(\d{1,3})\s*页[^\n]*$", markdown_text))
    sections: dict[int, str] = {}
    for idx, match in enumerate(matches):
        page_number = int(match.group(1))
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(markdown_text)
        section = markdown_text[start:end]
        section = re.sub(r"(?m)^---\s*$", "", section).strip()
        if section:
            sections[page_number] = section
    return sections


def _section_content_points(section_text: str, *, fallback: list[str], count: int = 2) -> list[str]:
    if not section_text:
        return fallback[:count]
    cleaned = re.sub(r"```.*?```", "", section_text, flags=re.S)
    cleaned = re.sub(r"(?m)^\|.*\|$", " ", cleaned)
    cleaned = re.sub(r"(?m)^#{1,6}\s*", "", cleaned)
    cleaned = re.sub(r"\*\*(?:建议可视化|图表标题建议|页面意图|目录结构)\*\*.*?(?=\n\n|\Z)", " ", cleaned, flags=re.S)
    raw_parts = re.split(r"\n\s*\n|(?<=[。；])", cleaned)
    banned_scaffold_tokens = (
        "该页把当前数据证据压缩成一个可执行的管理判断",
        "重点是决定资源应投向哪里",
        "这一页应形成可执行的管理判断",
        "而不是只描述图形",
        "这页可视化把复杂结构压缩成单页经营判断",
        "历史 PDF 仅用于页面系统逆向",
        "页面节奏来自历史 PDF 视觉识别",
        "排名ing",
    )
    points: list[str] = []
    for raw in raw_parts:
        if any(token in raw for token in banned_scaffold_tokens):
            continue
        if any(token in raw for token in ("建议可视化", "图表标题建议", "页面意图", "目录结构")):
            continue
        text = _clean_text(raw.replace("|", " "), limit=150)
        if len(text) < 18:
            continue
        points.append(text[:140])
        if len(points) >= count:
            break
    if len(points) < count:
        points.extend(fallback[: count - len(points)])
    return points[:count]


def _asset_management_points(assets: list[dict[str, Any]], *, title: str) -> list[str]:
    text = _normalize_text_labels(f"{title} " + " ".join(str(asset.get('title') or '') for asset in assets))
    lower = text.lower()
    if any(token in lower for token in ("价值桥", "value bridge", "收入 mix")):
        return [
            "价值桥用于识别总量贡献最集中的增长来源，管理上应先保护头部贡献单元，再决定尾部单元是放大还是收缩。",
            "如果头部贡献集中且尾部效率偏弱，预算分配应从平均主义转向分层投放与结构修复。",
        ]
    if any(token in lower for token in ("气泡图", "bubble")):
        return [
            "气泡图用于同时比较规模、重要性与优先级，面积较大且落在高价值象限的单元应成为资源倾斜对象。",
            "落在低价值或高风险区域的单元不应继续机械放量，而应先定义修复条件与退出阈值。",
        ]
    if any(token in lower for token in ("2x2", "组合矩阵", "portfolio matrix", "象限图")):
        return [
            "二维组合矩阵适合区分放量保护、价值培育、观察区和风险区，核心不是看单点高低，而是看资源优先级。",
            "位于高价值象限的单元应优先放大，位于风险象限的单元应先修复价格、服务或结构问题。",
        ]
    if any(token in lower for token in ("heatmap", "热力", "相关")):
        return [
            "热力或相关图用于识别联动最强的经营变量，强联动项更适合作为跨团队协同的管理抓手。",
            "如果几个变量长期一起变化，就不应分散治理，而应把它们纳入同一张经营看板与责任闭环。",
        ]
    if any(token in lower for token in ("pareto", "累计曲线", "cumulative", "分布")):
        return [
            "分布与帕累托图用于识别结构是否由少数单元驱动，管理重点是找到头部贡献与长尾稀释的边界。",
            "若贡献高度集中，头部单元需要保护；若长尾过长，则应尽快做结构压缩与资源回收。",
        ]
    return [
        "这页可视化用于把复杂结构压缩成单页经营判断，重点不是描述图形本身，而是确定资源应投向哪里。",
        "当图形已经给出结构差异时，下一步动作应围绕头部放大、尾部修复和风险隔离来设计。",
    ]


def _asset_markup(
    asset: dict[str, Any],
    *,
    workspace: Path,
    html_path: Path,
    card_class: str = "",
) -> str:
    path = _asset_path(asset, workspace=workspace)
    raw_title = _zh_asset_title(str(asset.get("title") or path.stem))
    title = html.escape(raw_title)
    class_attr = html.escape(f"exhibit-card {card_class}".strip())
    if not path.exists():
        raise FileNotFoundError(f"Historical visual asset file is missing: {path}")
    suffix = path.suffix.lower()
    if suffix == ".svg":
        path = _localized_svg_path(path, workspace=workspace)
        src = html.escape(_relative_url(path, html_path=html_path))
        return f'<figure class="{class_attr}"><figcaption>{title}</figcaption><img src="{src}" alt="{title}" /></figure>'
    if suffix in {".html", ".htm"}:
        try:
            raw_fragment = _strip_html_fragment(path.read_text(encoding="utf-8-sig"))
            # Keep HTML asset tags intact. The text localizer is intentionally
            # not applied here because it can turn tags such as
            # `<section class="...">` into reader-visible garbage.
            fragment = _localize_html_text_nodes(raw_fragment)
        except Exception:
            raw_fragment = ""
            fragment = ""
        lower_fragment = raw_fragment.lower()
        has_visual_component = any(
            token in lower_fragment
            for token in (
                "<table",
                "<svg",
                "<img",
                "historical-collage",
                "summary-map",
                "action-roadmap",
                "gap-matrix",
                "kpi-strip",
                "asset-matrix",
                "visual-block",
            )
        )
        if not has_visual_component:
            raise ValueError(f"Historical HTML asset is not a renderable visual component: {path.name}")
        if "<table" in lower_fragment and "<table" not in fragment.lower():
            fragment = raw_fragment
        if "<table" not in fragment.lower() and not has_visual_component:
            plain = re.sub(r"<[^>]+>", " ", fragment)
            bits = [
                _clean_text(bit, limit=95)
                for bit in re.split(r"\s{2,}|(?<=[。；;])", plain)
                if _clean_text(bit, limit=95)
            ]
            cards = "".join(f"<li>{html.escape(bit)}</li>" for bit in bits[:5])
            return f'<figure class="{class_attr} exhibit-fragment"><figcaption>{title}</figcaption><ul class="asset-bullets">{cards}</ul></figure>'
        if "historical-table-asset" in lower_fragment or "historical-collage-asset" in lower_fragment:
            fragment = re.sub(r"(?is)<h3\b[^>]*>.*?</h3>", "", fragment, count=1)
            return f'<figure class="{class_attr} exhibit-fragment no-outer-caption">{fragment}</figure>'
        return f'<figure class="{class_attr} exhibit-fragment"><figcaption>{title}</figcaption>{fragment}</figure>'
    src = html.escape(_relative_url(path, html_path=html_path))
    return f'<figure class="{class_attr}"><figcaption>{title}</figcaption><a href="{src}">{html.escape(path.name)}</a></figure>'


def _page_visual_class(template_type: str) -> str:
    if template_type in {
        "thesis_chart_page",
        "scatter_diagnosis_page",
        "heatmap_leverage_page",
        "funnel_diagnosis_page",
    }:
        return "hero-exhibit-page"
    if template_type in {
        "kpi_scorecard_page",
        "comparison_matrix_page",
        "ranking_table_page",
        "appendix_detail_table_page",
        "appendix_glossary_page",
    }:
        return "matrix-exhibit-page"
    if template_type in {"summary_map_page", "collage_preference_page"}:
        return "collage-exhibit-page"
    return "standard-exhibit-page"


def _select_assets_for_template(template_type: str, assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not assets:
        return []
    def _asset_has_number(asset: dict[str, Any]) -> bool:
        try:
            payload = json.dumps(asset.get("insight_input") or asset, ensure_ascii=False, default=str)
        except Exception:
            payload = str(asset)
        return _has_numeric_evidence(payload) or bool(re.search(r"-?\d+(?:\.\d+)?", payload))
    if template_type in {"thesis_chart_page", "scatter_diagnosis_page", "heatmap_leverage_page", "funnel_diagnosis_page"}:
        chart_like = [
            asset for asset in assets
            if str(asset.get("asset_type") or asset.get("kind") or "").lower() not in {"table", "collage"}
        ]
        return chart_like[:1] if chart_like else assets[:2]
    if template_type in {"summary_map_page", "collage_preference_page"}:
        collage_like = [
            asset for asset in assets
            if str(asset.get("asset_type") or asset.get("kind") or "").lower() == "collage"
        ]
        numeric_candidates = [asset for asset in assets if _asset_has_number(asset)]
        collage_like = sorted(collage_like, key=lambda asset: (not _asset_has_number(asset), str(asset.get("file_name") or "")))
        source_key = str(((collage_like[0].get("insight_input") if collage_like and isinstance(collage_like[0].get("insight_input"), dict) else {}) or {}).get("source_key") or "")
        if collage_like and _asset_has_number(collage_like[0]) and source_key not in {"tag_board", "segment_badges"}:
            return collage_like[:1]
        selected = numeric_candidates or collage_like or assets
        return selected[:2] if not collage_like else selected[:1]
    if template_type in {
        "kpi_scorecard_page",
        "comparison_matrix_page",
        "ranking_table_page",
        "appendix_detail_table_page",
        "appendix_glossary_page",
    }:
        table_like = [
            asset for asset in assets
            if str(asset.get("asset_type") or asset.get("kind") or "").lower() == "table"
        ]
        selected = table_like or assets
        if template_type in {"appendix_detail_table_page", "appendix_glossary_page"}:
            return selected[:1]
        if len(selected) < 2:
            for asset in assets:
                if asset in selected:
                    continue
                if _asset_has_number(asset):
                    selected.append(asset)
                if len(selected) >= 2:
                    break
        # Core exhibit pages should not leave a large visual region empty when
        # the layout planner already supplied a second evidence table.
        return selected[:2]
    return assets[:2]


def _page_kicker(template_type: str, module: str, page_number: int) -> str:
    template_labels = {
        "cover_page": "封面",
        "toc_navigation_page": "目录",
        "module_divider_page": "模块扉页",
        "thesis_chart_page": "图表论点页",
        "comparison_matrix_page": "对比矩阵页",
        "kpi_scorecard_page": "KPI 看板页",
        "funnel_diagnosis_page": "漏斗诊断页",
        "scatter_diagnosis_page": "散点诊断页",
        "heatmap_leverage_page": "热力杠杆页",
        "ranking_table_page": "排行明细页",
        "summary_map_page": "总结地图页",
        "appendix_glossary_page": "附录口径页",
        "appendix_detail_table_page": "附录明细页",
        "collage_preference_page": "拼版洞察页",
    }
    module_text = module or template_labels.get(template_type, template_type.replace("_", " "))
    return f"第 {page_number:02d} 页 | {module_text}"


def _content_points(blocks: list[str], page_number: int, *, count: int = 3) -> list[str]:
    start = max(0, (page_number - 1) * count % max(1, len(blocks)))
    points = blocks[start : start + count]
    if len(points) < count:
        points.extend(blocks[: count - len(points)])
    return points[:count]


def _render_page(
    page: dict[str, Any],
    *,
    workspace: Path,
    html_path: Path,
    blocks: list[str],
    page_sections: dict[int, str],
    total_pages: int,
) -> str:
    page_number = int(page.get("page_number") or 1)
    template_type = str(page.get("page_template_type") or "thesis_chart_page")
    raw_title = _normalize_text_labels(str(page.get("title") or f"Page {page_number}")).strip()
    raw_module = _normalize_text_labels(str(page.get("module") or "")).strip()
    title = html.escape(raw_title or f"Page {page_number}")
    module = raw_module
    assets = _select_assets_for_template(
        template_type,
        [asset for asset in list(page.get("asset_refs") or []) if isinstance(asset, dict)],
    )
    assets = [_hydrate_asset(asset, workspace=workspace) for asset in assets]
    visual_class = _page_visual_class(template_type)
    management_thesis = _normalize_text_labels(str(page.get("management_thesis") or "")).strip()
    fallback_points = _asset_management_points(assets, title=raw_title)
    if management_thesis:
        fallback_points = [management_thesis, *fallback_points][:2]
    non_asset_fallback = _content_points(blocks, page_number, count=2)
    if management_thesis:
        non_asset_fallback = [management_thesis, *non_asset_fallback][:2]
    points = _section_content_points(
        page_sections.get(page_number, ""),
        fallback=fallback_points if assets else non_asset_fallback,
        count=2,
    )

    if template_type == "cover_page":
        return (
            '<section class="deck-page cover-page">'
            '<div class="blue-rule"></div>'
            '<p class="eyebrow">咨询式经营报告</p>'
            f"<h1>{title}</h1>"
            '<p class="cover-subtitle">中文经营诊断 | 结论先行 | 图表驱动 | 管理动作导向</p>'
            '<div class="cover-grid"><span>增长</span><span>利润</span><span>运营</span><span>行动</span></div>'
            f'<footer>历史报告复刻运行时产物 | {page_number}/{total_pages}</footer>'
            "</section>"
        )

    if template_type == "toc_navigation_page":
        toc_items = "".join(f"<li><span>{idx:02d}</span>{html.escape(point[:72])}</li>" for idx, point in enumerate(blocks[:8], start=1))
        toc_asset_html = "".join(
            _asset_markup(asset, workspace=workspace, html_path=html_path, card_class="toc-visual-card")
            for asset in assets[:1]
        )
        if not toc_asset_html:
            raise ValueError(f"Historical TOC page {page_number} has no source-bound navigation visual asset.")
        return (
            '<section class="deck-page toc-page">'
            '<p class="kicker">目录</p><h2>本报告按咨询式问题树展开经营诊断</h2>'
            f"<ol>{toc_items}</ol>"
            f'<div class="toc-visual">{toc_asset_html}</div>'
            f'<footer>{page_number}/{total_pages}</footer>'
            "</section>"
        )

    if template_type == "module_divider_page":
        agenda_points = points[:3] or [raw_title or "本模块经营判断"]
        agenda_html = "".join(
            f"<li>{html.escape(_clean_text(point, limit=120))}</li>"
            for point in agenda_points
        )
        return (
            '<section class="deck-page divider-page">'
            f'<p class="kicker">{html.escape(module or "模块")}</p>'
            f"<h2>{title}</h2>"
            f"<p>{html.escape(points[0])}</p>"
            '<div class="divider-agenda"><h3>本模块回答</h3>'
            f"<ul>{agenda_html}</ul></div>"
            '<div class="divider-band"><span>01</span><strong>诊断</strong><em>证据</em><em>动作</em></div>'
            f'<footer>{page_number}/{total_pages}</footer>'
            "</section>"
        )

    asset_html = "".join(
        _asset_markup(
            asset,
            workspace=workspace,
            html_path=html_path,
            card_class="hero-card" if visual_class == "hero-exhibit-page" and idx == 0 else "",
        )
        for idx, asset in enumerate(assets)
    )
    if not asset_html:
        raise ValueError(f"Historical page {page_number} has no primary visual asset.")
        asset_html = (
            '<div class="consulting-insight-card">'
            f"<h3>{html.escape(points[0][:88])}</h3>"
            f"<p>{html.escape(points[1])}</p>"
            "</div>"
        )
    bullet_html = "".join(f"<li>{html.escape(point)}</li>" for point in points)
    return (
        f'<section class="deck-page content-page {html.escape(template_type)} {html.escape(visual_class)}">'
        f'<p class="kicker">{html.escape(_page_kicker(template_type, module, page_number))}</p>'
        f"<h2>{title}</h2>"
        '<div class="page-body">'
        f'<div class="exhibit-zone">{asset_html}</div>'
        '<aside class="implication-panel"><h3>管理含义</h3>'
        f"<ul>{bullet_html}</ul>"
        '<div class="action-box">管理动作：明确责任人，确认可控经营杠杆，并把本页信号转成下一周期动作。</div>'
        "</aside></div>"
        f'<footer>{page_number}/{total_pages}</footer>'
        "</section>"
    )


def _css(*, family: str = "") -> str:
    family_css = ""
    if False and family == "mckinsey_consulting_deck_family":
        family_css = """
body.family-mckinsey_consulting_deck_family .deck-page::before { background: #111827; }
body.family-mckinsey_consulting_deck_family .blue-rule { background: #111827; }
body.family-mckinsey_consulting_deck_family h2,
body.family-mckinsey_consulting_deck_family .exhibit-card figcaption,
body.family-mckinsey_consulting_deck_family .kicker { color: #111827; }
body.family-mckinsey_consulting_deck_family .exhibit-card { border-color: #cbd5e1; background: #ffffff; }
"""
    elif False and family == "brand_analysis_deck_yili_family":
        family_css = """
body.family-brand_analysis_deck_yili_family .deck-page::before { background: #1d8bc8; }
body.family-brand_analysis_deck_yili_family .blue-rule { background: linear-gradient(90deg, #0b6fb3, #63bf43); }
body.family-brand_analysis_deck_yili_family h2,
body.family-brand_analysis_deck_yili_family .exhibit-card figcaption,
body.family-brand_analysis_deck_yili_family .kicker { color: #0b6fb3; }
body.family-brand_analysis_deck_yili_family .exhibit-card { border-color: #b9dff3; background: #f7fbff; }
"""
    elif False and family == "dark_editorial_management_family":
        family_css = """
body.family-dark_editorial_management_family { background: #0f172a; }
body.family-dark_editorial_management_family .deck-page { background: #111827; color: #f8fafc; }
body.family-dark_editorial_management_family .deck-page::before { background: #e5e7eb; }
body.family-dark_editorial_management_family h2,
body.family-dark_editorial_management_family .exhibit-card figcaption,
body.family-dark_editorial_management_family .kicker { color: #f8fafc; }
body.family-dark_editorial_management_family .exhibit-card { border-color: #334155; background: #1f2937; }
"""
    return """
@page { size: A4 landscape; margin: 0; }
* { box-sizing: border-box; }
body {
  margin: 0;
  background: #e8edf2;
  color: #17202a;
  font-family: "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", Arial, sans-serif;
}
.deck-page {
  position: relative;
  width: 297mm;
  height: 210mm;
  min-height: 210mm;
  max-height: 210mm;
  padding: 18mm 20mm 14mm;
  break-after: page;
  page-break-after: always;
  background: #fff;
  overflow: hidden;
}
.deck-page::before {
  content: "";
  position: absolute;
  left: 0;
  top: 0;
  width: 7mm;
  height: 100%;
  background: #1f5f9f;
}
.kicker, .eyebrow {
  margin: 0 0 7mm;
  color: #1f5f9f;
  font-size: 9pt;
  font-weight: 700;
  letter-spacing: .08em;
  text-transform: uppercase;
}
h1, h2, h3 { margin: 0; color: #111827; }
h1 { max-width: 210mm; font-size: 34pt; line-height: 1.08; letter-spacing: -.02em; }
h2 { max-width: 245mm; font-size: 23pt; line-height: 1.12; letter-spacing: -.015em; }
h3 { font-size: 12pt; line-height: 1.25; }
footer {
  position: absolute;
  left: 20mm;
  right: 18mm;
  bottom: 8mm;
  border-top: 1px solid #d6dde5;
  padding-top: 3mm;
  color: #697586;
  font-size: 8pt;
  text-align: right;
}
.cover-page {
  background: linear-gradient(135deg, #ffffff 0%, #f4f7fb 52%, #e9f1f8 100%);
  padding-top: 34mm;
}
.blue-rule {
  width: 46mm;
  height: 7mm;
  background: #1f5f9f;
  margin-bottom: 18mm;
}
.cover-subtitle {
  margin-top: 11mm;
  max-width: 190mm;
  color: #536170;
  font-size: 15pt;
}
.cover-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 5mm;
  position: absolute;
  left: 20mm;
  right: 20mm;
  bottom: 28mm;
}
.cover-grid span {
  border-top: 4px solid #1f5f9f;
  padding-top: 4mm;
  color: #17202a;
  font-weight: 700;
}
.toc-page ol {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 5mm 14mm;
  margin: 18mm 0 0;
  padding: 0;
  list-style: none;
}
.toc-page li {
  display: grid;
  grid-template-columns: 15mm 1fr;
  gap: 4mm;
  padding: 4mm 0;
  border-top: 1px solid #d6dde5;
  color: #2c3744;
  font-size: 11pt;
  line-height: 1.45;
}
.toc-page li span { color: #1f5f9f; font-weight: 800; }
.divider-page {
  display: grid;
  align-content: center;
  background: #f7f9fb;
}
.divider-page h2 { max-width: 210mm; font-size: 31pt; }
.divider-page p:not(.kicker) {
  margin-top: 8mm;
  max-width: 175mm;
  color: #536170;
  font-size: 14pt;
  line-height: 1.6;
}
.divider-band {
  position: absolute;
  right: 0;
  top: 42mm;
  width: 82mm;
  height: 126mm;
  background: linear-gradient(135deg, rgba(31,95,159,.12), rgba(31,95,159,.02));
}
.page-body {
  display: grid;
  grid-template-columns: minmax(0, 1.65fr) 78mm;
  gap: 10mm;
  margin-top: 10mm;
  height: 130mm;
  overflow: hidden;
}
.exhibit-zone {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6mm;
  align-content: start;
  max-height: 132mm;
  overflow: hidden;
}
.exhibit-card {
  margin: 0;
  padding: 4mm;
  min-height: 58mm;
  border: 1px solid #d7e0ea;
  background: #fbfcfe;
}
.exhibit-card figcaption {
  margin-bottom: 3mm;
  color: #1f5f9f;
  font-size: 9pt;
  font-weight: 800;
}
.exhibit-card img {
  width: 100%;
  max-height: 100mm;
  object-fit: contain;
  display: block;
}
.hero-exhibit-page .page-body {
  grid-template-columns: minmax(0, 1.85fr) 72mm;
}
.hero-exhibit-page .exhibit-zone {
  grid-template-columns: 1fr;
  gap: 4mm;
}
.hero-exhibit-page .hero-card {
  min-height: 118mm;
}
.hero-exhibit-page .hero-card img {
  max-height: 108mm;
}
.hero-exhibit-page .exhibit-card:not(.hero-card) {
  min-height: 34mm;
  padding: 3mm;
}
.hero-exhibit-page .exhibit-card:not(.hero-card) img {
  max-height: 27mm;
}
.matrix-exhibit-page .exhibit-zone {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}
.collage-exhibit-page .exhibit-zone {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}
.exhibit-fragment {
  max-height: 118mm;
  overflow: hidden;
}
.exhibit-fragment table {
  width: 100%;
  table-layout: fixed;
  border-collapse: collapse;
  font-size: 7.5pt;
}
.asset-bullets {
  margin: 0;
  padding-left: 5mm;
  color: #2c3744;
  font-size: 10pt;
  line-height: 1.45;
}
.asset-bullets li {
  margin-bottom: 3mm;
}
.exhibit-fragment th, .exhibit-fragment td {
  border-bottom: 1px solid #e1e7ee;
  padding: 2mm;
  text-align: left;
  vertical-align: top;
  overflow-wrap: anywhere;
  word-break: break-word;
  white-space: normal;
}
.exhibit-fragment th {
  background: #eef4fa;
  color: #1f5f9f;
}
.implication-panel {
  padding: 6mm;
  border-left: 4px solid #1f5f9f;
  background: #f5f8fb;
  max-height: 130mm;
  overflow: hidden;
}
.implication-panel h3 {
  color: #1f5f9f;
  text-transform: uppercase;
  letter-spacing: .05em;
}
.implication-panel ul {
  margin: 5mm 0;
  padding-left: 5mm;
  color: #2c3744;
  font-size: 9pt;
  line-height: 1.38;
}
.implication-panel li { margin-bottom: 2.2mm; }
.action-box {
  margin-top: 4mm;
  padding: 3.2mm;
  background: #17202a;
  color: #fff;
  font-size: 8pt;
  line-height: 1.32;
}
.consulting-insight-card {
  grid-column: span 2;
  padding: 8mm;
  border: 1px solid #d7e0ea;
  background: #fbfcfe;
}
.consulting-insight-card p {
  color: #536170;
  font-size: 12pt;
  line-height: 1.6;
}
""" + family_css


# ---------------------------------------------------------------------------
# Clean dynamic visual-transfer layer.
#
# The earlier renderer grew from a small set of hard-coded families. For real
# historical-PDF imitation we must let the PDF-derived visual contract drive
# orientation, colors, page furniture, and footer/exhibit rhythm. These
# definitions intentionally override the legacy helpers above without deleting
# them yet, so existing callers remain stable while the renderer stops
# collapsing every sample into the same blue landscape deck.


def _normalize_text_labels(text: str) -> str:  # type: ignore[no-redef]
    normalized = _apply_safe_label_replacements(text)
    normalized = localize_historical_text(normalized)
    normalized = _apply_safe_label_replacements(normalized)
    return _fallback_clean_sentence(text) if _looks_mojibake(normalized) else normalized


def _consulting_chinese_fallback(text: str) -> str:  # type: ignore[no-redef]
    return _fallback_clean_sentence(text)


def _clean_text(value: Any, *, limit: int = 220) -> str:  # type: ignore[no-redef]
    text = str(value or "")
    text = re.sub(r"[*`>#|]+", " ", text)
    text = re.sub(r"\s*-{2,}:?(?:\s*-{2,}:?)+\s*", " ", text)
    text = _normalize_text_labels(text)
    text = re.sub(r"(?<=[\u4e00-\u9fff])[_/\\-]+(?=[\u4e00-\u9fff])", "", text)
    text = re.sub(r"(?<=[\u4e00-\u9fff])[_/\\-]+(?=[A-Za-z])", "", text)
    text = re.sub(r"(?<=[A-Za-z])[_/\\-]+(?=[\u4e00-\u9fff])", "", text)
    if _contains_cjk(text):
        text = _drop_residual_english_words(text)
    text = text.replace("来源:", "来源：").replace("Note:", "说明：")
    text = re.sub(r"\.\s*\.", "。", text)
    text = re.sub(r"\s+", " ", text).strip()
    if _english_heavy(text) or _looks_mojibake(text):
        text = _consulting_chinese_fallback(text)
    return text[:limit]


def _zh_asset_title(title: str) -> str:  # type: ignore[no-redef]
    replacements = {
        "Benchmark Callout Board": "关键指标提示板",
        "Executive Summary Map": "执行摘要地图",
        "Signal Tag Board": "信号标签板",
        "Segment Badge Board": "细分对象卡片",
        "Module Navigation Board": "模块导航板",
        "Action Roadmap Board": "行动路线图",
        "Gap Matrix Board": "差距矩阵",
        "KPI Snapshot": "核心 KPI 快照",
        "Correlation Focus": "相关关系重点表",
        "Dimension Signal Matrix": "维度信号矩阵",
        "Priority Action Table": "优先行动表",
        "Metric & Dimension Glossary": "指标与维度口径表",
        "Appendix Detail Table": "附录明细表",
    }
    return _normalize_text_labels(localize_historical_text(replacements.get(title, title), fallback=title))


def _format_insight_number(value: Any) -> str:
    try:
        number = float(value)
    except Exception:
        return str(value or "").strip()
    if abs(number) >= 10000:
        return f"{number / 10000:.1f}万"
    if abs(number) >= 100:
        return f"{number:.0f}"
    if abs(number) >= 1:
        return f"{number:.2f}".rstrip("0").rstrip(".")
    return f"{number:.2%}"


def _share_is_reader_meaningful(row: dict[str, Any]) -> bool:
    semantics = str(row.get("share_semantics") or "").strip()
    share = row.get("share_of_total")
    if semantics and semantics != "contribution_share":
        return False
    try:
        share_value = float(share)
    except Exception:
        return False
    return share_value > 1e-9


_INTERNAL_READER_LABELS = {
    "action_roadmap": "行动路线图",
    "benchmark_callouts": "关键指标提示板",
    "summary_map_nodes": "执行摘要地图",
    "summary_map": "执行摘要地图",
    "tag_board": "信号标签板",
    "segment_badges": "分层画像",
    "gap_matrix_blocks": "差距矩阵",
    "gap_matrix": "差距矩阵",
    "customer_scorecards": "客群评分卡",
    "scorecards": "评分卡",
    "cards": "卡片",
    "ranking_dimension": "维度排名",
    "ranking_table": "排名明细表",
}


def _internal_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")


def _reader_label(value: Any, *, default: str = "", limit: int = 48) -> str:
    raw = str(value or "").strip()
    if not raw:
        return default
    key = _internal_key(raw)
    if key in _INTERNAL_READER_LABELS:
        return _INTERNAL_READER_LABELS[key]
    text = raw
    for source, target in sorted(_INTERNAL_READER_LABELS.items(), key=lambda item: len(item[0]), reverse=True):
        text = re.sub(rf"(?i){re.escape(source)}", target, text)
    text = re.sub(r"(?i)cards?", "卡片", text)
    text = re.sub(r"[_/\\-]+", " ", text)
    text = _clean_text(text, limit=limit)
    if not text or re.search(r"[A-Za-z_]{3,}", text):
        return default
    return text


def _insight_label(row: dict[str, Any], dimension: str = "") -> str:
    for key in (
        dimension,
        "dimension_value_label",
        "dimension_value_raw",
        "segment_localized_label",
        "segment_raw_value",
        "dimension_a_value_label",
        "dimension_b_value_label",
        "label",
        "name",
        "category",
        "segment",
    ):
        value = row.get(key)
        if value is not None and str(value).strip():
            return _clean_text(value, limit=40)
    for value in row.values():
        if isinstance(value, str) and value.strip():
            return _clean_text(value, limit=40)
    return ""


def _asset_insight_points(asset: dict[str, Any]) -> list[str]:
    insight = asset.get("insight_input") if isinstance(asset.get("insight_input"), dict) else {}
    if not insight:
        return []
    metric = _reader_label(
        insight.get("metric")
        or insight.get("metric_localized_label")
        or insight.get("localized_label")
        or insight.get("metric_raw_key")
        or insight.get("raw_key"),
        limit=48,
    )
    dimension = _reader_label(
        insight.get("dimension")
        or insight.get("dimension_localized_label")
        or insight.get("dimension_raw_key"),
        limit=48,
    )
    rows = [row for row in list(insight.get("rows") or []) if isinstance(row, dict)]
    if rows and not metric:
        metric = _reader_label(
            rows[0].get("metric")
            or rows[0].get("metric_label")
            or rows[0].get("metric_localized_label")
            or rows[0].get("metric_raw_key"),
            limit=48,
        )
    if rows and not dimension:
        dimension = _reader_label(
            rows[0].get("dimension")
            or rows[0].get("dimension_localized_label")
            or rows[0].get("dimension_raw_key")
            or rows[0].get("dimension_a_label")
            or rows[0].get("dimension_a"),
            limit=48,
        )
    points: list[str] = []
    relationships = [row for row in list(insight.get("relationships") or []) if isinstance(row, dict)]
    if relationships:
        for row in relationships[:2]:
            left = _reader_label(row.get("left_localized_label") or row.get("left_raw_key"), limit=42)
            right = _reader_label(row.get("right_localized_label") or row.get("right_raw_key"), limit=42)
            corr = row.get("correlation", row.get("abs_correlation"))
            hint = _clean_text(row.get("management_hint"), limit=90)
            if left and right and corr is not None:
                sentence = f"{left}与{right}的相关读数为{_format_insight_number(corr)}"
                if hint:
                    sentence += f"，{hint}"
                points.append(sentence + "。")
        if points:
            return points[:3]
    if rows and any(
        "top_segment" in row or "bottom_segment" in row or "top_分层" in row or "bottom_分层" in row
        for row in rows
    ):
        for row in rows[:2]:
            metric_name = _reader_label(row.get("metric") or metric, limit=48)
            dimension_name = _reader_label(row.get("dimension") or dimension, limit=48)
            top_segment = _reader_label(row.get("top_segment") or row.get("top_分层"), limit=48)
            bottom_segment = _reader_label(row.get("bottom_segment") or row.get("bottom_分层"), limit=48)
            top_value = row.get("top_value", row.get("top_数值"))
            bottom_value = row.get("bottom_value", row.get("bottom_数值"))
            if metric_name and top_segment and bottom_segment:
                points.append(
                    f"{dimension_name or '关键维度'}中，{top_segment}在{metric_name}上领先"
                    f"（{_format_insight_number(top_value)}），"
                    f"{bottom_segment}处于尾部（{_format_insight_number(bottom_value)}）。"
                )
        if points:
            return points[:3]
    actions = [row for row in list(insight.get("actions") or []) if isinstance(row, dict)]
    if actions:
        for action in actions[:2]:
            signal = _reader_label(action.get("current_signal") or action.get("focus"), limit=72)
            question = _clean_text(action.get("management_question") or action.get("action"), limit=120)
            priority = _clean_text(action.get("priority_zone"), limit=24)
            if signal and question:
                prefix = f"{priority}优先级：" if priority else ""
                points.append(f"{prefix}{signal}需要进入本期行动清单，{question}")
        if points:
            return points[:3]
    source_key = str(insight.get("source_key") or "")
    if source_key == "tag_board" and rows:
        labels = [_clean_text(row.get("label"), limit=24) for row in rows if _clean_text(row.get("label"), limit=24)]
        if labels:
            points.append(f"本页覆盖{', '.join(labels[:6])}等关键字段，后续判断应围绕这些指标和维度展开。")
    elif source_key == "segment_badges" and rows:
        for first in rows[:3]:
            label = _clean_text(first.get("label"), limit=48)
            metrics = [str(item) for item in list(first.get("metrics") or [])[:2] if str(item).strip()]
            if label and metrics:
                points.append(f"{label}是当前分层中的关键对象，核心读数为{';'.join(metrics)}。")
    elif False and source_key == "segment_badges" and rows:
        first = rows[0]
        label = _clean_text(first.get("label"), limit=48)
        metrics = [str(item) for item in list(first.get("metrics") or [])[:2] if str(item).strip()]
        if label and metrics:
            points.append(f"{label}是当前分层中的关键对象，核心读数为{'；'.join(metrics)}。")
    elif source_key in {"benchmark_callouts", "action_roadmap"} and rows:
        first = rows[0]
        focus = _reader_label(first.get("metric") or first.get("focus"), limit=48)
        value = first.get("value", first.get("basis"))
        action = _clean_text(first.get("action") or first.get("interpretation"), limit=110)
        if focus and value is not None:
            points.append(f"{focus}当前读数为{_format_insight_number(value)}，应作为本页判断的管理基准。")
        if action:
            points.append(action)
    elif source_key == "summary_map_nodes" and rows:
        labels = [
            _clean_text(row.get("label"), limit=80)
            for row in rows
            if _clean_text(row.get("label"), limit=80)
        ]
        if labels:
            points.extend(label if label.endswith("。") else f"{label}。" for label in labels[:3] if _has_numeric_evidence(label))
    if points:
        return points[:3]
    if rows and metric:
        first = rows[0]
        last = rows[-1]
        first_label = _insight_label(first, dimension)
        last_label = _insight_label(last, dimension)
        first_value = first.get("value", first.get("mean", first.get("sum")))
        last_value = last.get("value", last.get("mean", last.get("sum")))
        if first_label and first_value is not None:
            sentence = f"{first_label}在{metric}上位于前列，当前值为{_format_insight_number(first_value)}"
            share = first.get("share_of_total")
            if _share_is_reader_meaningful(first):
                sentence += f"，占比{_format_insight_number(share)}"
            points.append(sentence + "。")
        if last_label and last_label != first_label and last_value is not None:
            sentence = f"{last_label}在{metric}上处于尾部，当前值为{_format_insight_number(last_value)}"
            lift = last.get("lift_vs_overall")
            if lift is not None:
                sentence += f"，相对整体差异{_format_insight_number(lift)}"
            points.append(sentence + "。")
    if metric and insight.get("min") is not None and insight.get("max") is not None:
        median = insight.get("median")
        spread = (
            f"{metric}的样本范围为{_format_insight_number(insight.get('min'))}"
            f"至{_format_insight_number(insight.get('max'))}"
        )
        if median is not None:
            spread += f"，中位数{_format_insight_number(median)}"
        points.append(spread + "。")
    if metric and dimension and insight.get("overall_value") is not None:
        points.append(f"{dimension}维度下的{metric}整体基准为{_format_insight_number(insight.get('overall_value'))}，应优先核查头尾差异能否转化为分层动作。")
    action = _clean_text(insight.get("action") or insight.get("management_implication") or insight.get("interpretation"), limit=130)
    if action:
        points.append(action)
    return [point for point in points if point][:3]


def _asset_management_points(assets: list[dict[str, Any]], *, title: str) -> list[str]:  # type: ignore[no-redef]
    points: list[str] = []
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        for point in _asset_insight_points(asset):
            if point not in points:
                points.append(point)
        if len(points) >= 3:
            break
    return points


_GENERIC_MANAGEMENT_COPY = (
    "不缺少数据",
    "资源重新排序",
    "持续关注",
    "转化为行动",
    "真正的管理抓手",
    "管理层应",
    "下一步动作应围绕",
)


def _has_numeric_evidence(text: str) -> bool:
    return bool(re.search(r"\d+(?:\.\d+)?\s*(?:%|万|亿|个|元|单|次|分|名)?", str(text or "")))


def _sentence_is_specific(text: str) -> bool:
    raw = str(text or "")
    cleaned = _clean_text(text, limit=260)
    if len(cleaned) < 18:
        return False
    scan_text = f"{raw} {cleaned}"
    if any(token in scan_text for token in _GENERIC_MANAGEMENT_COPY) and not _has_numeric_evidence(scan_text):
        return False
    has_object = bool(re.search(r"(区域|渠道|品类|类别|客群|门店|城市|平台|分层|对象|指标|销售额|订单量|毛利|转化率|复购率|满意度|库存|退货)", scan_text))
    has_action = bool(re.search(r"(负责人|预算|复盘|拆解|压降|放大|修复|迁移|校准|优先|下钻|跟进|调整)", scan_text))
    return _has_numeric_evidence(scan_text) or has_object or has_action


def _sentences_too_similar(left: str, right: str) -> bool:
    def _norm(value: str) -> str:
        return re.sub(r"[\W_]+", "", str(value or ""), flags=re.UNICODE)

    l_norm = _norm(left)
    r_norm = _norm(right)
    if not l_norm or not r_norm:
        return False
    if l_norm in r_norm or r_norm in l_norm:
        return True
    l_chars = set(l_norm)
    r_chars = set(r_norm)
    shared = len(l_chars & r_chars)
    return shared / max(1, min(len(l_chars), len(r_chars))) > 0.92


def _first_metric_name(asset: dict[str, Any]) -> str:
    insight = asset.get("insight_input") if isinstance(asset.get("insight_input"), dict) else {}
    source_key = _internal_key(insight.get("source_key"))
    if source_key == "summary_map_nodes":
        return "执行摘要指标组合"
    if source_key == "action_roadmap":
        return "行动路线图"
    candidates = [
        insight.get("metric"),
        insight.get("metric_localized_label"),
        insight.get("localized_label"),
        insight.get("metric_raw_key"),
        asset.get("title"),
    ]
    rows = [row for row in list(insight.get("rows") or []) if isinstance(row, dict)]
    if rows:
        candidates.extend([
            rows[0].get("metric"),
            rows[0].get("metric_label"),
            rows[0].get("metric_raw_key"),
        ])
    for item in candidates:
        text = _reader_label(item, limit=36)
        if text:
            return text
    source_label = _reader_label(source_key, default="", limit=36)
    if source_label:
        return source_label
    return "关键指标"


def _first_dimension_name(asset: dict[str, Any]) -> str:
    insight = asset.get("insight_input") if isinstance(asset.get("insight_input"), dict) else {}
    source_key = _internal_key(insight.get("source_key"))
    if source_key == "summary_map_nodes":
        return "执行摘要节点"
    if source_key == "action_roadmap":
        return "行动对象"
    if source_key == "benchmark_callouts":
        return "关键指标"
    candidates = [
        insight.get("dimension"),
        insight.get("dimension_localized_label"),
        insight.get("dimension_raw_key"),
        asset.get("story_role"),
    ]
    rows = [row for row in list(insight.get("rows") or []) if isinstance(row, dict)]
    if rows:
        candidates.extend([
            rows[0].get("dimension"),
            rows[0].get("dimension_label"),
            rows[0].get("dimension_raw_key"),
            rows[0].get("priority_zone"),
        ])
    for item in candidates:
        text = _reader_label(item, limit=32)
        if text:
            return text
    source_label = _reader_label(source_key, default="", limit=32)
    if source_label:
        return source_label
    return "关键分层"


def _compile_page_insight_contract(
    page: dict[str, Any],
    assets: list[dict[str, Any]],
    *,
    title: str,
) -> dict[str, str]:
    existing = page.get("page_insight_contract") if isinstance(page.get("page_insight_contract"), dict) else {}
    required_keys = ("reader_claim", "evidence_sentence", "mechanism_sentence", "action_sentence")
    if existing and all(_clean_text(existing.get(key), limit=260) for key in required_keys):
        contract = {key: _clean_text(existing.get(key), limit=260) for key in required_keys}
        if _has_numeric_evidence(contract["evidence_sentence"]) and all(_sentence_is_specific(value) for value in contract.values()):
            return contract
    points: list[str] = []
    for asset in assets:
        for point in _asset_insight_points(asset):
            point = _clean_text(point, limit=220)
            if point and point not in points and _sentence_is_specific(point):
                points.append(point)
    numeric_points = [point for point in points if _has_numeric_evidence(point)]
    if len(numeric_points) < 1:
        raise ValueError(f"Historical page lacks numeric evidence sentence: {page.get('page_number') or ''} {title}")
    primary_asset = assets[0] if assets else {}
    metric = _first_metric_name(primary_asset)
    dimension = _first_dimension_name(primary_asset)
    claim_seed = _clean_text(page.get("management_thesis") or points[0], limit=180)
    evidence = numeric_points[0]
    evidence_number_match = re.search(r"\d+(?:\.\d+)?\s*(?:%|万|亿|个|元|单|次|分|名)?", evidence)
    evidence_number = evidence_number_match.group(0) if evidence_number_match else ""
    mechanism_source = points[1] if len(points) > 1 and points[1] != evidence else ""
    mechanism = (
        f"机制上，{dimension}会改变{metric}的资源回报和复盘顺序"
        + (f"：{mechanism_source}" if mechanism_source else f"，本页应优先比较{dimension}中最高读数对象与最低读数对象的动作差异。")
    )
    action_target = dimension if dimension != "关键分层" else metric
    action = (
        f"{action_target}负责人应围绕{metric}设定一组本周期动作：保留高读数对象的打法，"
        f"同时把{evidence_number or '最高读数'}对应对象列入复盘和资源校准清单。"
    )
    claim = claim_seed
    if not _has_numeric_evidence(claim) or "主判断来自" in claim or "_" in claim:
        claim = f"{title}的经营结论是：{evidence}"
    if _sentences_too_similar(claim, evidence):
        for candidate in [*numeric_points[1:], *points]:
            if candidate and not _sentences_too_similar(candidate, claim):
                evidence = candidate
                break
    if _sentences_too_similar(mechanism, evidence) or _sentences_too_similar(mechanism, claim):
        mechanism_detail = ""
        for candidate in points:
            if (
                candidate
                and not _sentences_too_similar(candidate, claim)
                and not _sentences_too_similar(candidate, evidence)
            ):
                mechanism_detail = candidate
                break
        mechanism = (
            f"机制上，{dimension}会改变{metric}的资源回报和复盘顺序"
            + (f"：{mechanism_detail}" if mechanism_detail else f"，本页应优先比较{dimension}中最高读数对象与最低读数对象的动作差异。")
        )
    contract = {
        "reader_claim": _clean_text(claim, limit=220),
        "evidence_sentence": _clean_text(evidence, limit=220),
        "mechanism_sentence": _clean_text(mechanism, limit=260),
        "action_sentence": _clean_text(action, limit=240),
    }
    contract_values: list[str] = []
    for sentence in contract.values():
        if any(_sentences_too_similar(sentence, existing) for existing in contract_values):
            raise ValueError(f"Historical page insight contract has repeated reader-facing sentence: {page.get('page_number') or ''} {title}")
        contract_values.append(sentence)
    if not all(_sentence_is_specific(sentence) for sentence in contract.values()):
        raise ValueError(f"Historical page insight contract is too generic: {page.get('page_number') or ''} {title}")
    return contract


def _page_kicker(template_type: str, module: str, page_number: int) -> str:  # type: ignore[no-redef]
    template_labels = {
        "cover_page": "封面",
        "toc_navigation_page": "目录",
        "module_divider_page": "模块扉页",
        "thesis_chart_page": "图表论点页",
        "comparison_matrix_page": "对比矩阵页",
        "kpi_scorecard_page": "KPI 看板页",
        "funnel_diagnosis_page": "漏斗诊断页",
        "scatter_diagnosis_page": "散点诊断页",
        "heatmap_leverage_page": "热力杠杆页",
        "ranking_table_page": "排行明细页",
        "summary_map_page": "总结地图页",
        "appendix_glossary_page": "附录口径页",
        "appendix_detail_table_page": "附录明细页",
        "collage_preference_page": "拼版洞察页",
    }
    module_text = module or template_labels.get(template_type, template_type.replace("_", " "))
    return f"第 {page_number:02d} 页 | {module_text}"


def _source_footer(page_number: int, total_pages: int, contract: dict[str, Any]) -> str:
    furniture = dict(contract.get("furniture") or {})
    if furniture.get("source_note_footer"):
        return (
            f'<footer><span>来源：当前数据分析与系统生成图表。</span>'
            f'<span>{page_number}</span></footer>'
        )
    if furniture.get("source_note_footer"):
        return (
            f'<footer><span>来源：当前数据资产包与历史报告视觉规范。</span>'
            f'<span>{page_number}</span></footer>'
        )
    return f"<footer>{page_number}/{total_pages}</footer>"


def _norm_box(value: Any) -> list[float]:
    if not isinstance(value, list) or len(value) != 4:
        return []
    try:
        box = [max(0.0, min(1.0, float(item))) for item in value]
    except Exception:
        return []
    if box[2] <= box[0] or box[3] <= box[1]:
        return []
    return box


def _mm_box_from_norm(box: list[float], *, width_mm: int, height_mm: int) -> list[float]:
    if len(box) != 4:
        return []
    return [
        round(box[0] * width_mm, 2),
        round(box[1] * height_mm, 2),
        round(box[2] * width_mm, 2),
        round(box[3] * height_mm, 2),
    ]


def _page_region_css_vars(page: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    width_mm, height_mm, orientation = _contract_page_size(contract)
    global_css = _contract_region_css(contract)
    region_contract = page.get("region_layout_contract")
    region_contract = region_contract if isinstance(region_contract, dict) else {}
    regions = region_contract.get("layout_regions")
    regions = regions if isinstance(regions, dict) else dict(page.get("layout_regions") or {})
    title = _mm_box_from_norm(_norm_box(regions.get("title")), width_mm=width_mm, height_mm=height_mm)
    visual = _mm_box_from_norm(_norm_box(regions.get("primary_visual")), width_mm=width_mm, height_mm=height_mm)
    right_annotation = _mm_box_from_norm(_norm_box(regions.get("right_annotation")), width_mm=width_mm, height_mm=height_mm)
    narrative = _mm_box_from_norm(_norm_box(regions.get("narrative")), width_mm=width_mm, height_mm=height_mm)
    footer = _mm_box_from_norm(_norm_box(regions.get("footer")), width_mm=width_mm, height_mm=height_mm)
    mode = str(page.get("visual_region_mode") or (region_contract or {}).get("visual_region_mode") or "").strip()
    if not title or not visual or not footer:
        return global_css
    content_left = max(4.0, min(45.0, min(title[0], visual[0], narrative[0] if narrative else title[0])))
    content_right = max(4.0, min(45.0, width_mm - max(title[2], visual[2], narrative[2] if narrative else title[2])))
    title_top = max(4.0, min(height_mm - 45.0, title[1]))
    title_height = max(10.0, min(50.0, title[3] - title[1]))
    visual_top = max(title_top + title_height + 1.5, min(height_mm - 70.0, visual[1]))
    footer_top = max(visual_top + 46.0, min(height_mm - 6.0, footer[1]))
    visual_height = max(36.0, min(max(40.0, footer_top - visual_top - 4.0), visual[3] - visual[1]))
    right_width = max(0.0, right_annotation[2] - right_annotation[0]) if right_annotation else 0.0
    right_present = right_width >= width_mm * 0.10
    right_height = max(0.0, right_annotation[3] - right_annotation[1]) if right_annotation else 0.0
    narrative_top = narrative[1] if narrative else min(footer_top - 22.0, visual_top + visual_height + 3.0)
    narrative_height = (narrative[3] - narrative[1]) if narrative else max(14.0, footer_top - narrative_top - 2.0)
    visual_offset = 0.0
    if mode == "narrative_above_visual":
        upper_narrative_top = max(title_top + title_height + 5.0, min(height_mm - 110.0, title[3] + 5.0))
        source_visual_top = max(upper_narrative_top + 30.0, min(height_mm - 86.0, visual[1]))
        upper_narrative_height = max(28.0, min(62.0, source_visual_top - upper_narrative_top - 5.0))
        visual_height = max(70.0, min(footer_top - source_visual_top - 14.0, visual[3] - visual[1]))
        visual_top = upper_narrative_top
        narrative_top = upper_narrative_top
        narrative_height = upper_narrative_height
        visual_offset = narrative_height + 5.0
        body_height = max(96.0, min(height_mm - visual_top - 8.0, narrative_height + visual_height + 9.0))
        right_width = 0.0
        right_present = False
        return {
            **global_css,
            "available": True,
            "content_left_mm": round(content_left, 2),
            "content_right_mm": round(content_right, 2),
            "title_top_mm": round(title_top, 2),
            "title_height_mm": round(title_height, 2),
            "visual_top_mm": round(visual_top, 2),
            "visual_height_mm": round(visual_height, 2),
            "visual_offset_mm": round(visual_offset, 2),
            "narrative_top_mm": round(narrative_top, 2),
            "narrative_height_mm": round(narrative_height, 2),
            "body_height_mm": round(body_height, 2),
            "footer_top_mm": round(footer_top, 2),
            "right_annotation_width_mm": 0.0,
            "right_annotation_column": False,
        }
    if right_present and str(page.get("visual_region_mode") or "").startswith("visual_with_right"):
        body_height = max(48.0, min(height_mm - visual_top - 8.0, max(visual_height, right_height) + 6.0))
    else:
        body_height = max(48.0, min(height_mm - visual_top - 8.0, footer_top - visual_top - 2.0))
    density_plan = page.get("page_visual_density_plan")
    density_plan = density_plan if isinstance(density_plan, dict) else {}
    if density_plan:
        compact_visual_top = title_top + min(title_height, 19.0) + 8.0
        if visual_top > compact_visual_top:
            freed_height = visual_top - compact_visual_top
            visual_top = compact_visual_top
            visual_height = min(max(visual_height, footer_top - visual_top - 24.0), visual_height + min(42.0, freed_height * 0.85))
            narrative_top = narrative[1] if narrative else min(footer_top - 22.0, visual_top + visual_height + 3.0)
            body_height = max(64.0, min(height_mm - visual_top - 8.0, footer_top - visual_top - 2.0))
    visual_boost = max(1.0, min(1.38, float(density_plan.get("visual_height_boost") or 1.0)))
    if visual_boost > 1.0:
        max_visual_height = max(visual_height, footer_top - visual_top - 16.0)
        visual_height = min(max_visual_height, visual_height * visual_boost)
        if str(density_plan.get("narrative_mode") or "") != "right_annotation" or not right_present:
            narrative_top = min(footer_top - 14.0, visual_top + visual_height + 3.0)
            narrative_height = max(12.0, footer_top - narrative_top - 2.0)
        if right_present and str(page.get("visual_region_mode") or "").startswith("visual_with_right"):
            body_height = max(body_height, min(height_mm - visual_top - 8.0, max(visual_height, right_height) + 6.0))
        else:
            body_height = max(body_height, min(height_mm - visual_top - 8.0, visual_height + narrative_height + 6.0))
    if right_present and str(page.get("visual_region_mode") or "").startswith("visual_with_right"):
        # Keep right-annotation pages tied to the source page's actual exhibit
        # height. Expanding the image column to the footer makes the page look
        # like a sparse canvas even when the source page used a compact exhibit.
        visual_height = min(height_mm - visual_top - 12.0, max(visual_height, right_height * 0.92))
        body_height = max(48.0, min(height_mm - visual_top - 8.0, max(visual_height, right_height) + 6.0))
    return {
        **global_css,
        "available": True,
        "content_left_mm": round(content_left, 2),
        "content_right_mm": round(content_right, 2),
        "title_top_mm": round(title_top, 2),
        "title_height_mm": round(title_height, 2),
        "visual_top_mm": round(visual_top, 2),
        "visual_height_mm": round(visual_height, 2),
        "visual_offset_mm": 0.0,
        "narrative_top_mm": round(max(visual_top, min(footer_top - 10.0, narrative_top)), 2),
        "narrative_height_mm": round(max(12.0, min(70.0, narrative_height)), 2),
        "body_height_mm": round(body_height, 2),
        "footer_top_mm": round(footer_top, 2),
        "right_annotation_width_mm": round(right_width, 2),
        "right_annotation_column": right_present,
    }


def _section_style_from_region(region_css: dict[str, Any]) -> str:
    pairs = {
        "--region-content-left": f"{float(region_css.get('content_left_mm') or 18):.2f}mm",
        "--region-content-right": f"{float(region_css.get('content_right_mm') or 18):.2f}mm",
        "--region-title-top": f"{float(region_css.get('title_top_mm') or 18):.2f}mm",
        "--region-title-height": f"{float(region_css.get('title_height_mm') or 28):.2f}mm",
        "--region-visual-top": f"{float(region_css.get('visual_top_mm') or 58):.2f}mm",
        "--region-visual-height": f"{float(region_css.get('visual_height_mm') or 108):.2f}mm",
        "--region-visual-offset": f"{float(region_css.get('visual_offset_mm') or 0):.2f}mm",
        "--region-narrative-top": f"{float(region_css.get('narrative_top_mm') or 170):.2f}mm",
        "--region-narrative-height": f"{float(region_css.get('narrative_height_mm') or 36):.2f}mm",
        "--region-body-height": f"{float(region_css.get('body_height_mm') or 130):.2f}mm",
        "--region-footer-top": f"{float(region_css.get('footer_top_mm') or 195):.2f}mm",
        "--region-right-annotation-width": f"{float(region_css.get('right_annotation_width_mm') or 0):.2f}mm",
    }
    return "; ".join(f"{key}: {value}" for key, value in pairs.items())


def _render_page(  # type: ignore[no-redef]
    page: dict[str, Any],
    *,
    workspace: Path,
    html_path: Path,
    blocks: list[str],
    page_sections: dict[int, str],
    total_pages: int,
) -> str:
    contract = _style_contract(workspace)
    _width_mm, _height_mm, orientation = _contract_page_size(contract)
    harmony = dict(contract.get("layout_harmony") or {})
    balance_mode = re.sub(r"[^a-z0-9_-]+", "-", str(harmony.get("balance_mode") or "balanced_exhibit").lower()).strip("-")
    density_mode = re.sub(r"[^a-z0-9_-]+", "-", str(harmony.get("density_mode") or "moderate").lower()).strip("-")
    page_number = int(page.get("page_number") or 1)
    template_type = str(page.get("page_template_type") or "thesis_chart_page")
    region_css = _page_region_css_vars(page, contract)
    section_style = _section_style_from_region(region_css)
    visual_region_mode = re.sub(r"[^a-z0-9_-]+", "-", str(page.get("visual_region_mode") or (page.get("region_layout_contract") or {}).get("visual_region_mode") or "visual_then_lower_narrative").lower()).strip("-")
    source_region_profile_id = html.escape(str(page.get("source_region_profile_id") or (page.get("region_layout_contract") or {}).get("source_region_profile_id") or ""))
    raw_title = _clean_text(page.get("title") or f"Page {page_number}", limit=150)
    raw_module = _clean_text(page.get("module") or "", limit=60)
    title = html.escape(raw_title or f"Page {page_number}")
    assets = _select_assets_for_template(
        template_type,
        [asset for asset in list(page.get("asset_refs") or []) if isinstance(asset, dict)],
    )
    assets = [_hydrate_asset(asset, workspace=workspace) for asset in assets]
    management_thesis = _clean_text(page.get("management_thesis") or "", limit=180)
    fallback_points = [management_thesis] if management_thesis else []
    fallback_points.extend(_asset_management_points(assets, title=raw_title))
    if not fallback_points:
        fallback_points = _content_points(blocks, page_number, count=3)
    points = _section_content_points(
        page_sections.get(page_number, ""),
        fallback=fallback_points,
        count=3,
    )
    points = [point for point in points if _clean_text(point, limit=220)]
    footer = _source_footer(page_number, total_pages, contract)

    if template_type == "cover_page":
        return (
            '<section class="deck-page cover-page">'
            '<div class="brand-mark">报告</div>'
            '<p class="eyebrow">咨询式经营报告</p>'
            f"<h1>{title}</h1>"
            '<p class="cover-subtitle">结论先行 | 图表驱动 | 管理行动导向</p>'
            '<div class="cover-grid"><span>增长</span><span>结构</span><span>效率</span><span>行动</span></div>'
            f"{footer}</section>"
        )

    if template_type == "toc_navigation_page":
        toc_items = "".join(f"<li><span>{idx:02d}</span>{html.escape(point[:72])}</li>" for idx, point in enumerate(blocks[:8], start=1))
        return (
            '<section class="deck-page toc-page">'
            '<p class="kicker">目录</p><h2>本报告按问题树展开经营诊断</h2>'
            f"<ol>{toc_items}</ol>"
            f"{footer}</section>"
        )

    if template_type == "module_divider_page":
        agenda_points = points[:3] or [raw_title or "本模块经营判断"]
        agenda_html = "".join(
            f"<li>{html.escape(_clean_text(point, limit=120))}</li>"
            for point in agenda_points
        )
        return (
            '<section class="deck-page divider-page">'
            f'<p class="kicker">{html.escape(raw_module or "模块")}</p>'
            f"<h2>{title}</h2>"
            f"<p>{html.escape(points[0])}</p>"
            '<div class="divider-agenda"><h3>本模块回答</h3>'
            f"<ul>{agenda_html}</ul></div>"
            '<div class="divider-band"><span>01</span><strong>诊断</strong><em>证据</em><em>动作</em></div>'
            f"{footer}</section>"
        )

    asset_html = "".join(
        _asset_markup(
            asset,
            workspace=workspace,
            html_path=html_path,
            card_class="hero-card" if idx == 0 else "",
        )
        for idx, asset in enumerate(assets)
    )
    if not asset_html:
        raise ValueError(f"Historical page {page_number} has no primary visual asset.")
    insight_contract = _compile_page_insight_contract(page, assets, title=raw_title)
    title_length_class = "title-long" if len(raw_title) >= 34 else ("title-medium" if len(raw_title) >= 24 else "title-short")
    exhibit_label = "图表"
    implication_html = (
        '<aside class="implication-panel narrative-panel" data-page-insight-contract="true">'
        '<div><h3>管理解读</h3>'
        f"<p>{html.escape(insight_contract['reader_claim'])}</p>"
        f"<p>{html.escape(insight_contract['evidence_sentence'])}</p>"
        f"<p>{html.escape(insight_contract['mechanism_sentence'])}</p></div>"
        '<div><h3>行动含义</h3>'
        f"<p>{html.escape(insight_contract['action_sentence'])}</p></div>"
        "</aside>"
    )
    return (
        f'<section class="deck-page content-page {html.escape(template_type)} {html.escape(title_length_class)} orientation-{html.escape(orientation)} harmony-{html.escape(balance_mode)} density-{html.escape(density_mode)} region-mode-{html.escape(visual_region_mode)}" '
        f'data-source-region-profile-id="{source_region_profile_id}" style="{html.escape(section_style)}">'
        f'<p class="kicker">{html.escape(exhibit_label)} {page_number - 2 if page_number > 2 else page_number}</p>'
        f"<h2>{title}</h2>"
        '<div class="page-body">'
        f'<div class="exhibit-zone">{asset_html}</div>'
        f"{implication_html}</div>"
        f"{footer}</section>"
    )


def _css(*, family: str = "", contract: dict[str, Any] | None = None) -> str:  # type: ignore[no-redef]
    contract = contract or {}
    width_mm, height_mm, orientation = _contract_page_size(contract)
    colors = dict(contract.get("colors") or {})
    furniture = dict(contract.get("furniture") or {})
    accent = _contract_color(contract, "accent", "#0b7f5c")
    heading = _contract_color(contract, "heading", accent)
    text = _contract_color(contract, "text", "#4a4a4a")
    muted = _contract_color(contract, "muted", "#8a8a8a")
    rule = _contract_color(contract, "rule", "#d6d6d6")
    background = _contract_color(contract, "background", "#ffffff")
    accent_soft = _contract_color(contract, "accent_soft", "#eef6f2")
    secondary = _contract_color(contract, "secondary", "#b05738")
    positive_delta = _contract_color(contract, "positive_delta", accent)
    negative_delta = _contract_color(contract, "negative_delta", "#b05738")
    table_header_fill = _contract_color(contract, "table_header_fill", accent_soft)
    footnote_gray = _contract_color(contract, "footnote_gray", muted)
    series_palette = [
        str(item).strip()
        for item in list(colors.get("series_palette") or [])
        if re.fullmatch(r"#[0-9a-fA-F]{6}", str(item).strip())
    ]
    while len(series_palette) < 5:
        series_palette.append([accent, secondary, positive_delta, negative_delta, muted][len(series_palette)])
    side_rail_css = f"background: {accent};" if furniture.get("side_rail") else "display: none;"
    content_grid = "minmax(0, 1fr)" if orientation == "portrait" else "minmax(0, 1.85fr) 72mm"
    page_body_height = "196mm" if orientation == "portrait" else "130mm"
    exhibit_max = "136mm" if orientation == "portrait" else "108mm"
    region_css = _contract_region_css(contract)
    content_left_mm = float(region_css.get("content_left_mm") or 18)
    content_right_mm = float(region_css.get("content_right_mm") or 18)
    title_top_mm = float(region_css.get("title_top_mm") or 18)
    title_height_mm = float(region_css.get("title_height_mm") or 28)
    visual_top_mm = float(region_css.get("visual_top_mm") or 58)
    visual_height_mm = float(region_css.get("visual_height_mm") or (136 if orientation == "portrait" else 108))
    narrative_top_mm = float(region_css.get("narrative_top_mm") or (visual_top_mm + visual_height_mm + 4))
    narrative_height_mm = float(region_css.get("narrative_height_mm") or 36)
    body_height_region_mm = float(region_css.get("body_height_mm") or (196 if orientation == "portrait" else 130))
    footer_top_mm = float(region_css.get("footer_top_mm") or (height_mm - 15))
    right_annotation_width_mm = float(region_css.get("right_annotation_width_mm") or 0)
    harmony = dict(contract.get("layout_harmony") or {})
    balance_mode = str(harmony.get("balance_mode") or "balanced_exhibit")
    density_mode = str(harmony.get("density_mode") or "moderate")
    recommended_columns = max(1, min(3, int(harmony.get("recommended_content_columns") or (2 if orientation == "portrait" else 1))))
    visual_text_ratio = max(0.42, min(0.76, float(harmony.get("recommended_visual_text_ratio") or 0.58)))
    section_gap_mm = round(max(4.0, min(14.0, float(harmony.get("recommended_section_gap_ratio") or 0.025) * height_mm)), 2)
    white_space_ratio = max(0.0, min(1.0, float(harmony.get("white_space_ratio_hint") or 0.82)))
    kicker_top_mm = max(5.0, title_top_mm - 8.0)
    base_exhibit_max_mm = 136.0 if orientation == "portrait" else 108.0
    image_max_mm = min(base_exhibit_max_mm, max(34.0, visual_height_mm))
    region_available = bool(region_css.get("available"))
    portrait_region_grid = (
        f"{max(44.0, visual_height_mm)}mm {max(16.0, narrative_height_mm)}mm"
        if region_available and orientation == "portrait"
        else "auto 1fr"
    )
    region_content_grid = "minmax(0, 1fr)"
    if orientation == "landscape":
        if balance_mode == "visual_first":
            region_content_grid = "minmax(0, 2.15fr) 58mm"
        elif balance_mode == "text_first":
            region_content_grid = "minmax(0, 1.35fr) 84mm"
        elif balance_mode == "visual_with_right_annotation":
            region_content_grid = "minmax(0, 1.85fr) minmax(50mm, 72mm)"
        else:
            region_content_grid = content_grid
    elif bool(region_css.get("right_annotation_column")):
        region_content_grid = "minmax(0, 1fr)"
    density_font_delta = -0.4 if density_mode == "dense" else (0.5 if density_mode == "sparse" else 0)
    body_font_size = round(9.2 + density_font_delta, 2)
    panel_gap_mm = max(5.0, min(11.0, section_gap_mm))
    family_extra_css = ""
    if False and family in {"mckinsey_consulting_deck_family", "bcg_consulting_quarterly_watch_family"}:
        family_extra_css = """
body.family-mckinsey_consulting_deck_family,
body.family-bcg_consulting_quarterly_watch_family {
  background: #ffffff;
}
body.family-mckinsey_consulting_deck_family .deck-page,
body.family-bcg_consulting_quarterly_watch_family .deck-page {
  padding: 16mm 15mm 12mm;
}
body.family-mckinsey_consulting_deck_family .deck-page::before,
body.family-bcg_consulting_quarterly_watch_family .deck-page::before {
  display: none;
}
body.family-mckinsey_consulting_deck_family .kicker,
body.family-bcg_consulting_quarterly_watch_family .kicker {
  color: #666;
  font-size: 8pt;
  letter-spacing: .02em;
  text-transform: none;
}
body.family-mckinsey_consulting_deck_family h2,
body.family-bcg_consulting_quarterly_watch_family h2 {
  color: #007a53;
  font-size: 18.8pt;
  line-height: 1.16;
  font-weight: 500;
  max-width: 178mm;
}
body.family-mckinsey_consulting_deck_family .content-page h2,
body.family-bcg_consulting_quarterly_watch_family .content-page h2 {
  top: 13mm;
  max-height: 22mm;
}
body.family-mckinsey_consulting_deck_family .content-page .kicker,
body.family-bcg_consulting_quarterly_watch_family .content-page .kicker {
  top: 9mm;
}
body.family-mckinsey_consulting_deck_family .page-body,
body.family-bcg_consulting_quarterly_watch_family .page-body {
  top: 43mm;
  height: 210mm;
}
body.family-mckinsey_consulting_deck_family .exhibit-card figcaption,
body.family-bcg_consulting_quarterly_watch_family .exhibit-card figcaption {
  display: none;
}
body.family-mckinsey_consulting_deck_family .exhibit-card img,
body.family-bcg_consulting_quarterly_watch_family .exhibit-card img {
  max-height: 128mm;
}
body.family-mckinsey_consulting_deck_family .implication-panel,
body.family-bcg_consulting_quarterly_watch_family .implication-panel {
  border-top: 0;
  padding-top: 5mm;
  grid-template-columns: 1fr 1fr;
  column-gap: 16mm;
}
body.family-mckinsey_consulting_deck_family h3,
body.family-bcg_consulting_quarterly_watch_family h3 {
  color: #444;
  font-size: 9.5pt;
  letter-spacing: .05em;
  text-transform: uppercase;
}
body.family-mckinsey_consulting_deck_family footer,
body.family-bcg_consulting_quarterly_watch_family footer {
  color: #9b9b9b;
  font-size: 7pt;
  border-top: 0;
  padding-top: 0;
}
"""
    return f"""
@page {{ size: A4 {orientation}; margin: 0; }}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  background: #e8edf2;
  color: {text};
  font-family: "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", Arial, sans-serif;
}}
.deck-page {{
  position: relative;
  width: {width_mm}mm;
  height: {height_mm}mm;
  min-height: {height_mm}mm;
  max-height: {height_mm}mm;
  padding: 18mm 18mm 13mm;
  break-after: page;
  page-break-after: always;
  background: {background};
  overflow: hidden;
}}
.deck-page {{
  --region-content-left: {content_left_mm}mm;
  --region-content-right: {content_right_mm}mm;
  --region-title-top: {title_top_mm}mm;
  --region-title-height: {title_height_mm}mm;
  --region-visual-top: {visual_top_mm}mm;
  --region-visual-height: {visual_height_mm}mm;
  --region-visual-offset: 0mm;
  --region-narrative-top: {narrative_top_mm}mm;
  --region-narrative-height: {narrative_height_mm}mm;
  --region-body-height: {body_height_region_mm}mm;
  --region-footer-top: {footer_top_mm}mm;
  --region-right-annotation-width: {right_annotation_width_mm}mm;
  --layout-section-gap: {section_gap_mm}mm;
  --layout-visual-text-ratio: {round(visual_text_ratio, 4)};
  --layout-white-space-ratio: {round(white_space_ratio, 4)};
  --layout-content-columns: {recommended_columns};
  --color-series-1: {series_palette[0]};
  --color-series-2: {series_palette[1]};
  --color-series-3: {series_palette[2]};
  --color-series-4: {series_palette[3]};
  --color-series-5: {series_palette[4]};
  --color-positive: {positive_delta};
  --color-negative: {negative_delta};
  --color-table-header: {table_header_fill};
  --color-footnote: {footnote_gray};
}}
.deck-page::before {{
  content: "";
  position: absolute;
  left: 0;
  top: 0;
  width: 6mm;
  height: 100%;
  {side_rail_css}
}}
.kicker, .eyebrow {{
  margin: 0 0 6mm;
  color: {muted};
  font-size: 9pt;
  letter-spacing: .08em;
  text-transform: uppercase;
}}
h1 {{
  margin: 0;
  max-width: 165mm;
  color: {heading};
  font-size: 31pt;
  line-height: 1.12;
  font-weight: 500;
}}
h2 {{
  margin: 0 0 9mm;
  color: {heading};
  font-size: {21 if orientation == "portrait" else 25}pt;
  line-height: 1.12;
  font-weight: 500;
}}
.content-page {{
  padding: 0;
}}
.content-page .kicker {{
  position: absolute;
  left: var(--region-content-left);
  right: var(--region-content-right);
  top: {round(kicker_top_mm, 2)}mm;
  margin: 0;
}}
.content-page h2 {{
  position: absolute;
  left: var(--region-content-left);
  right: var(--region-content-right);
  top: var(--region-title-top);
  max-height: var(--region-title-height);
  overflow: hidden;
  margin: 0;
}}
.content-page.title-medium h2 {{
  font-size: {19.5 if orientation == "portrait" else 23.2}pt;
  line-height: 1.13;
}}
.content-page.title-long h2 {{
  font-size: {18.2 if orientation == "portrait" else 22.0}pt;
  line-height: 1.12;
  letter-spacing: -.01em;
}}
h3 {{ margin: 0 0 3mm; color: {heading}; font-size: 11pt; }}
footer {{
  position: absolute;
  left: var(--region-content-left);
  right: var(--region-content-right);
  top: var(--region-footer-top);
  bottom: auto;
  display: flex;
  justify-content: space-between;
  gap: 8mm;
  color: #9a9a9a;
  font-size: 7.5pt;
  border-top: 1px solid {rule};
  padding-top: 3mm;
}}
.brand-mark {{
  margin-bottom: 34mm;
  width: 38mm;
  height: 12mm;
  color: {accent};
  font-size: 21pt;
  font-weight: 800;
  letter-spacing: -.04em;
}}
.cover-page {{ padding-top: 18mm; }}
.cover-subtitle {{
  margin-top: 12mm;
  color: {text};
  font-size: 13pt;
}}
.cover-grid {{
  position: absolute;
  left: 18mm;
  right: 18mm;
  bottom: 28mm;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8mm;
}}
.cover-grid span {{
  border-top: 3px solid {accent};
  padding-top: 5mm;
  color: {text};
  font-weight: 700;
}}
.toc-page ol {{ list-style: none; padding: 0; margin: 16mm 0 0; display: grid; gap: 7mm; }}
.toc-page li {{ display: grid; grid-template-columns: 16mm 1fr; border-top: 1px solid {rule}; padding-top: 4mm; color: {text}; font-size: 11pt; line-height: 1.45; }}
.toc-page li span {{ color: {accent}; font-weight: 700; }}
.divider-page h2 {{ max-width: 145mm; }}
.divider-page p:not(.kicker) {{ max-width: 132mm; color: {text}; font-size: 13pt; line-height: 1.55; }}
.divider-agenda {{
  position: absolute;
  left: 18mm;
  bottom: 46mm;
  width: 118mm;
  border-top: 2px solid {accent};
  padding-top: 6mm;
}}
.divider-agenda h3 {{ margin-bottom: 4mm; }}
.divider-agenda ul {{ margin: 0; padding-left: 5mm; color: {text}; font-size: 10.2pt; line-height: 1.5; }}
.divider-agenda li {{ margin-bottom: 2.4mm; }}
.divider-band {{
  position: absolute;
  right: 0;
  top: 42mm;
  width: 70mm;
  height: 130mm;
  background: linear-gradient(135deg, {accent_soft}, rgba(255,255,255,0));
  padding: 18mm 10mm;
  display: grid;
  align-content: start;
  gap: 5mm;
  color: {accent};
}}
.divider-band span {{ font-size: 34pt; line-height: 1; font-weight: 700; opacity: .22; }}
.divider-band strong {{ font-size: 18pt; font-weight: 600; }}
.divider-band em {{ font-style: normal; font-size: 10pt; border-top: 1px solid {rule}; padding-top: 3mm; color: {text}; }}
.page-body {{
  display: grid;
  grid-template-columns: {region_content_grid};
  gap: var(--layout-section-gap);
  position: absolute;
  left: var(--region-content-left);
  right: var(--region-content-right);
  top: var(--region-visual-top);
  margin-top: 0;
  height: var(--region-body-height);
  overflow: hidden;
}}
.orientation-portrait .page-body {{ grid-template-rows: {portrait_region_grid}; }}
.harmony-visual_first .page-body {{ grid-template-columns: minmax(0, 2.15fr) 58mm; }}
.harmony-text_first .page-body {{ grid-template-columns: minmax(0, 1.35fr) 84mm; }}
.harmony-visual_with_right_annotation .page-body {{ grid-template-columns: minmax(0, 1.85fr) minmax(50mm, 72mm); }}
.orientation-portrait.harmony-visual_first .page-body,
.orientation-portrait.harmony-text_first .page-body,
.orientation-portrait.harmony-visual_with_right_annotation .page-body {{ grid-template-columns: 1fr; }}
.region-mode-visual_with_right_annotation .page-body,
.region-mode-visual_with_right_delta .page-body {{
  grid-template-columns: minmax(0, calc(100% - var(--region-right-annotation-width) - var(--layout-section-gap))) minmax(32mm, var(--region-right-annotation-width));
  grid-template-rows: none;
}}
.region-mode-visual_with_right_annotation.orientation-portrait .page-body,
.region-mode-visual_with_right_delta.orientation-portrait .page-body {{
  grid-template-columns: minmax(0, 1fr) clamp(54mm, var(--region-right-annotation-width), 68mm);
  grid-template-rows: none;
}}
.region-mode-visual_then_lower_narrative .page-body,
.region-mode-visual_only.orientation-portrait .page-body {{
  grid-template-columns: 1fr;
  grid-template-rows: var(--region-visual-height) minmax(0, var(--region-narrative-height));
}}
.region-mode-narrative_above_visual .page-body {{
  grid-template-columns: 1fr;
  grid-template-rows: var(--region-narrative-height) minmax(0, var(--region-visual-height));
}}
.region-mode-narrative_above_visual .implication-panel {{
  order: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: max(5mm, var(--layout-section-gap));
  border-top: 0;
  padding: 0;
  min-height: var(--region-narrative-height);
  overflow: visible;
}}
.region-mode-narrative_above_visual .exhibit-zone {{
  order: 2;
  height: var(--region-visual-height);
  max-height: var(--region-visual-height);
}}
.region-mode-narrative_above_visual .hero-card img {{
  height: var(--region-visual-height);
  max-height: var(--region-visual-height);
  object-fit: fill;
}}
.region-mode-table_dense .page-body {{
  grid-template-columns: 1fr;
  grid-template-rows: minmax(0, var(--region-visual-height)) minmax(0, var(--region-narrative-height));
}}
.region-mode-collage_grid .page-body {{
  grid-template-columns: 1fr;
  grid-template-rows: minmax(0, var(--region-visual-height)) minmax(0, var(--region-narrative-height));
}}
.density-dense .page-body {{ gap: max(4mm, calc(var(--layout-section-gap) * .72)); }}
.density-sparse .page-body {{ gap: min(14mm, calc(var(--layout-section-gap) * 1.18)); }}
.exhibit-zone {{ display: grid; grid-template-columns: 1fr; gap: 4mm; align-content: stretch; height: var(--region-visual-height); overflow: visible; }}
.exhibit-zone:has(.exhibit-card + .exhibit-card) {{
  grid-template-rows: minmax(0, 1.25fr) minmax(0, .9fr);
  align-content: stretch;
}}
.exhibit-zone:has(.exhibit-card + .exhibit-card) .exhibit-card {{
  height: auto;
  min-height: 0;
  overflow: hidden;
}}
.exhibit-zone:has(.exhibit-card + .exhibit-card) .exhibit-card img {{
  height: 100%;
  max-height: 100%;
  object-fit: fill;
}}
.orientation-landscape .exhibit-zone {{ grid-template-columns: 1fr; }}
.exhibit-card {{ margin: 0; padding: 0; border: 0; background: transparent; min-height: 0; height: 100%; display: flex; flex-direction: column; }}
.exhibit-card figcaption {{ margin-bottom: 3mm; color: {heading}; font-size: 10pt; font-weight: 600; }}
.exhibit-card img {{ width: 100%; height: min({round(image_max_mm, 2)}mm, var(--region-visual-height)); max-height: var(--region-visual-height); object-fit: contain; object-position: 50% 0; display: block; flex: 1 1 auto; }}
.orientation-portrait .exhibit-zone {{ max-height: var(--region-visual-height); }}
.orientation-portrait .hero-card img {{ height: var(--region-visual-height); max-height: var(--region-visual-height); }}
.region-mode-visual_then_lower_narrative.orientation-portrait .hero-card img {{
  height: var(--region-visual-height);
  object-fit: fill;
}}
.region-mode-visual_with_right_annotation.orientation-portrait .hero-card img,
.region-mode-visual_with_right_delta.orientation-portrait .hero-card img {{
  height: var(--region-visual-height);
  object-fit: fill;
}}
.orientation-portrait .implication-panel {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: {panel_gap_mm}mm;
  border: 0;
  border-top: 1px solid {rule};
  padding: 6mm 0 0;
  min-height: var(--region-narrative-height);
  max-height: none;
  overflow: visible;
  background: transparent;
}}
.region-mode-visual_with_right_annotation.orientation-portrait .implication-panel,
.region-mode-visual_with_right_delta.orientation-portrait .implication-panel {{
  grid-template-columns: 1fr;
  gap: 3.6mm;
  border-top: 0;
  border-left: 1px solid {rule};
  padding: 0 0 0 5mm;
  align-content: start;
  min-height: 0;
  overflow: visible;
}}
.region-mode-visual_with_right_annotation.orientation-portrait .implication-panel > div,
.region-mode-visual_with_right_delta.orientation-portrait .implication-panel > div {{
  padding: 0 0 3mm;
  border-bottom: 1px solid {rule};
}}
.region-mode-visual_with_right_annotation.orientation-portrait .implication-panel > div:last-child,
.region-mode-visual_with_right_delta.orientation-portrait .implication-panel > div:last-child {{
  border-bottom: 0;
}}
.orientation-landscape .implication-panel {{
  padding: {max(4.5, min(7.0, panel_gap_mm * 0.72))}mm;
  border-left: 4px solid {accent};
  background: {accent_soft};
  max-height: none;
  overflow: visible;
}}
.implication-panel ul {{ margin: 0; padding-left: 5mm; font-size: {body_font_size}pt; line-height: 1.42; color: {text}; }}
.implication-panel li {{ margin-bottom: 2.4mm; }}
.implication-panel > div {{ min-width: 0; overflow: visible; max-height: none; }}
.implication-panel p {{
  margin: 0;
  color: {text};
  font-size: {max(7.6, body_font_size - 0.8)}pt;
  line-height: 1.32;
  overflow: visible;
}}
.region-mode-visual_with_right_annotation.orientation-portrait .implication-panel p,
.region-mode-visual_with_right_delta.orientation-portrait .implication-panel p {{
  font-size: {max(8.2, body_font_size - 0.35)}pt;
  line-height: 1.44;
  margin: 0 0 2mm;
}}
.region-mode-visual_with_right_annotation.orientation-portrait .implication-panel h3,
.region-mode-visual_with_right_delta.orientation-portrait .implication-panel h3 {{
  font-size: 10pt;
  margin: 0 0 2mm;
}}
.orientation-landscape .implication-panel p {{ max-height: none; }}
.action-box {{ padding: 3mm; background: {accent}; color: #fff; font-size: 8pt; line-height: 1.35; }}
.action-box {{ max-height: none; overflow: visible; }}
.consulting-insight-card {{ padding: 8mm; border: 1px solid {rule}; background: #fbfcfe; }}
.consulting-insight-card p {{ margin: 0; font-size: 9pt; line-height: 1.38; max-height: 52mm; overflow: hidden; }}
.exhibit-zone > .exhibit-fragment.no-outer-caption:only-child {{ height: 100%; }}
.exhibit-fragment table {{ width: 100%; table-layout: fixed; border-collapse: collapse; font-size: 7.7pt; border-top: 1.6px solid {accent}; }}
.exhibit-fragment th, .exhibit-fragment td {{ border-bottom: 1px solid {rule}; padding: 2.05mm; text-align: left; vertical-align: top; overflow-wrap: anywhere; }}
.exhibit-fragment th {{ color: {heading}; background: #eef2f1; border-bottom-color: {rule}; font-weight: 800; }}
.exhibit-fragment tbody tr:nth-child(even) td {{ background: #f5f6f5; }}
.exhibit-fragment tbody tr:nth-child(odd) td {{ background: #ffffff; }}
.summary_map_page .exhibit-fragment.no-outer-caption,
.ranking_table_page .exhibit-fragment.no-outer-caption,
.comparison_matrix_page .exhibit-fragment.no-outer-caption {{
  border-left: .9mm solid {rule};
  padding-left: 2.2mm;
  background: linear-gradient(90deg, rgba(74,74,74,.045), transparent 42%);
}}
.summary_map_page .exhibit-fragment table,
.ranking_table_page .exhibit-fragment table,
.comparison_matrix_page .exhibit-fragment table {{ font-size: 7.9pt; }}
.summary_map_page .exhibit-fragment th,
.summary_map_page .exhibit-fragment td,
.ranking_table_page .exhibit-fragment th,
.ranking_table_page .exhibit-fragment td,
.comparison_matrix_page .exhibit-fragment th,
.comparison_matrix_page .exhibit-fragment td {{ padding-top: 2.15mm; padding-bottom: 2.15mm; }}
.historical-collage-asset {{ width: 100%; height: 100%; max-height: var(--region-visual-height); overflow: hidden; display: flex; flex-direction: column; }}
.historical-collage-asset h3 {{ margin: 0 0 4mm; color: {heading}; font-size: 10pt; }}
.tag-grid, .badge-grid, .callout-grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); grid-auto-rows: minmax(0, 1fr); gap: 3mm; flex: 1; min-height: 0; }}
.roadmap-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); grid-auto-rows: minmax(0, 1fr); gap: 3.2mm; }}
.historical-collage-asset.action-roadmap .roadmap-grid {{ flex: 1; min-height: 0; }}
.collage-tag, .badge-card, .callout-card {{ border: 1px solid {rule}; background: #fff; padding: 3mm; min-height: 18mm; display: flex; flex-direction: column; justify-content: space-between; }}
.roadmap-step {{ border: 1px solid {rule}; background: #fff; padding: 3mm; min-height: 28mm; display: grid; grid-template-columns: 9mm 1fr; column-gap: 2.5mm; align-items: start; }}
.roadmap-step strong {{ grid-row: span 3; display: grid; place-items: center; width: 8mm; height: 8mm; border-radius: 99px; background: var(--color-series-1); color: #fff; font-size: 7pt; }}
.roadmap-step h4 {{ margin: 0 0 1mm; color: {text}; font-size: 8.5pt; line-height: 1.15; }}
.roadmap-step .basis {{ margin: 0 0 1mm; color: var(--color-series-2); font-size: 8pt; font-weight: 700; }}
.roadmap-step p {{ margin: 0; color: {text}; font-size: 7.1pt; line-height: 1.32; }}
.badge-card:nth-child(3n+1), .summary-node:nth-child(3n+1) {{ border-top: 2px solid var(--color-series-1); }}
.badge-card:nth-child(3n+2), .summary-node:nth-child(3n+2) {{ border-top: 2px solid var(--color-series-2); }}
.badge-card:nth-child(3n), .summary-node:nth-child(3n) {{ border-top: 2px solid var(--color-series-3); }}
.collage-tag b, .badge-card h4, .callout-card h4 {{ display: block; color: {text}; font-size: 9pt; line-height: 1.2; overflow-wrap: anywhere; }}
.collage-tag small, .badge-kicker, .callout-card p {{ display: block; margin: 0 0 1.5mm; color: {muted}; font-size: 6.8pt; text-transform: uppercase; letter-spacing: .04em; }}
.badge-card ul {{ margin: 2mm 0 0; padding: 0; list-style: none; color: {text}; font-size: 7.2pt; line-height: 1.3; }}
.badge-card li {{ margin: 0 0 1mm; border-top: 1px solid {rule}; padding-top: 1mm; }}
.callout-card strong {{ display: block; margin-top: 2mm; color: {heading}; font-size: 13pt; line-height: 1.15; overflow-wrap: anywhere; }}
.historical-table-asset {{ width: 100%; max-height: none; overflow: visible; }}
.historical-table-asset h3 {{ margin: 0 0 3mm; color: {heading}; font-size: 10pt; }}
.historical-table-asset .table-note {{ margin: 2mm 0 0; color: var(--color-footnote); font-size: 6.5pt; line-height: 1.25; }}
.implication-panel strong, .action-box {{ color: var(--color-series-2); }}
{family_extra_css}
"""


def render_deterministic_historical_deck(
    *,
    workspace: Path,
    markdown_report_path: Path,
    deck_layout_pack_path: Path,
    html_path: Path,
    css_path: Path,
) -> dict[str, Any]:
    """Render a complete consulting-style deck from deterministic layout/assets.

    This is a backend fallback/accelerator for cases where the Codex HTML/CSS
    stage stalls after producing the report, assets, and deck layout pack.
    """
    deck_layout = _read_json(deck_layout_pack_path)
    pages = [page for page in list(deck_layout.get("pages") or []) if isinstance(page, dict)]
    markdown_text = markdown_report_path.read_text(encoding="utf-8-sig") if markdown_report_path.exists() else ""
    blocks = _markdown_blocks(markdown_text)
    page_sections = _markdown_page_sections(markdown_text)
    total_pages = len(pages)
    family = str(deck_layout.get("historical_report_family") or "generic_chinese_analysis_deck")
    style_contract = _style_contract(workspace, family=family)
    _width_mm, _height_mm, orientation = _contract_page_size(style_contract)
    family_class = re.sub(r"[^a-zA-Z0-9_-]+", "_", family).strip("_") or "generic_chinese_analysis_deck"
    visual_class_counts: dict[str, int] = {}
    for page in pages:
        visual_class = _page_visual_class(str(page.get("page_template_type") or ""))
        visual_class_counts[visual_class] = visual_class_counts.get(visual_class, 0) + 1
    html_pages = [
        _render_page(
            page,
            workspace=workspace,
            html_path=html_path,
            blocks=blocks,
            page_sections=page_sections,
            total_pages=total_pages,
        )
        for page in pages
    ]
    html_doc = (
        "<!doctype html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\" />"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />"
        f"<link rel=\"stylesheet\" href=\"{html.escape(css_path.name)}\" />"
        "<title>历史报告复刻咨询式报告</title></head><body>"
        + "\n".join(html_pages)
        + "</body></html>"
    )
    html_doc = re.sub(r"(?is)<title>.*?</title>", "<title>历史风格复刻经营报告</title>", html_doc, count=1)
    for broken, fixed in {
        "鍜ㄨ寮忕粡钀ユ姤鍛?": "咨询式经营报告",
        "涓枃缁忚惀璇婃柇": "中文经营诊断",
        "缁撹鍏堣": "结论先行",
        "鍥捐〃椹卞姩": "图表驱动",
        "绠＄悊鍔ㄤ綔瀵煎悜": "管理动作导向",
        "澧為暱": "增长",
        "鍒╂鼎": "利润",
        "杩愯惀": "运营",
        "琛屽姩": "行动",
        "鍘嗗彶鎶ュ憡澶嶅埢杩愯鏃朵骇鐗?": "历史报告复刻运行时产物",
        "鐩綍": "目录",
        "鏈姤鍛婃寜鍜ㄨ寮忛棶棰樻爲灞曞紑缁忚惀璇婃柇": "本报告按咨询式问题树展开经营诊断",
        "绠＄悊鍚箟": "管理含义",
        "绠＄悊鍔ㄤ綔锛氭槑纭矗浠讳汉锛岀‘璁ゅ彲鎺х粡钀ユ潬鏉嗭紝骞舵妸鏈〉淇″彿杞垚涓嬩竴鍛ㄦ湡鍔ㄤ綔銆?": "管理动作：明确责任人，确认可控经营杠杆，并把本页信号转成下一周期动作。",
    }.items():
        html_doc = html_doc.replace(broken, fixed)
    html_doc = html_doc.replace("<body>", f'<body class="family-{html.escape(family_class)} orientation-{html.escape(orientation)}">', 1)
    html_path.write_text(html_doc, encoding="utf-8")
    css_path.write_text(_css(family=family, contract=style_contract), encoding="utf-8")
    return {
        "html_path": str(html_path.resolve()),
        "css_path": str(css_path.resolve()),
        "page_count": total_pages,
        "mapped_page_sections": len(page_sections),
        "family": family,
        "visual_orientation": orientation,
        "style_transfer_contract": style_contract,
        "template_counts": dict(deck_layout.get("template_counts") or {}),
        "visual_class_counts": visual_class_counts,
    }
