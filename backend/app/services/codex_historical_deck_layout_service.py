from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


PAGE_TEMPLATE_TYPES = {
    "cover_page",
    "toc_navigation_page",
    "module_divider_page",
    "thesis_chart_page",
    "comparison_matrix_page",
    "kpi_scorecard_page",
    "funnel_diagnosis_page",
    "scatter_diagnosis_page",
    "heatmap_leverage_page",
    "ranking_table_page",
    "summary_map_page",
    "appendix_glossary_page",
    "appendix_detail_table_page",
    "collage_preference_page",
}


ROLE_TO_TEMPLATE = {
    "cover": "cover_page",
    "toc": "toc_navigation_page",
    "directory": "toc_navigation_page",
    "navigation": "toc_navigation_page",
    "divider": "module_divider_page",
    "module": "module_divider_page",
    "chart": "thesis_chart_page",
    "visual": "thesis_chart_page",
    "comparison": "comparison_matrix_page",
    "matrix": "comparison_matrix_page",
    "kpi": "kpi_scorecard_page",
    "scorecard": "kpi_scorecard_page",
    "funnel": "funnel_diagnosis_page",
    "scatter": "scatter_diagnosis_page",
    "heatmap": "heatmap_leverage_page",
    "ranking": "ranking_table_page",
    "summary": "summary_map_page",
    "map": "summary_map_page",
    "appendix": "appendix_detail_table_page",
    "glossary": "appendix_glossary_page",
    "collage": "collage_preference_page",
    "preference": "collage_preference_page",
}


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _clean_text(value: Any, *, fallback: str = "") -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip())
    return text or fallback


_READER_LABEL_MAP = {
    "gross_sales": "销售额",
    "revenue": "收入",
    "net_revenue": "净收入",
    "order_count": "订单量",
    "orders": "订单量",
    "basket_value": "客单价",
    "aov": "客单价",
    "gross_margin": "毛利率",
    "margin": "毛利率",
    "conversion_rate": "转化率",
    "repeat_purchase_rate": "复购率",
    "repeat_rate": "复购率",
    "service_satisfaction": "服务满意度",
    "inventory_turns": "库存周转",
    "discount_depth": "折扣深度",
    "return_rate": "退货率",
    "traffic_index": "流量指数",
    "region": "区域",
    "channel": "渠道",
    "category": "类别",
    "consumer_segment": "消费客群",
    "date": "日期",
    "platform": "平台",
    "city": "城市",
    "store": "门店",
    "West": "西区",
    "East": "东区",
    "North": "北区",
    "South": "南区",
    "Retail partner": "零售伙伴",
    "Marketplace": "平台",
    "Direct store": "直营",
    "Wholesale": "批发",
    "Social commerce": "社交电商",
    "Seasonal bundle": "季节组合",
    "Body care": "身体护理",
    "Travel size": "旅行装",
    "Core skincare": "核心护肤",
    "Price sensitive": "价格敏感客群",
    "Promotion sensitive": "促销敏感客群",
}


def _reader_label(value: Any, *, fallback: str = "", limit: int = 36) -> str:
    text = _clean_text(value)
    if not text:
        return fallback
    localized = _READER_LABEL_MAP.get(text, text)
    localized = localized.replace("_", " ")
    localized = re.sub(r"\s+", " ", localized).strip()
    return localized[:limit] if limit > 0 else localized


def _format_reader_value(value: Any, *, metric: str = "") -> str:
    try:
        number = float(value)
    except Exception:
        return _reader_label(value, fallback="")
    metric_text = str(metric or "").lower()
    is_rate = any(token in metric_text for token in ("率", "rate", "margin", "ratio", "share"))
    if is_rate and abs(number) <= 1.5:
        return f"{number * 100:.2f}%"
    if is_rate:
        return f"{number:.2f}%"
    if abs(number) >= 10000:
        return f"{number:,.0f}"
    if abs(number) >= 100:
        return f"{number:,.0f}"
    return f"{number:.2f}".rstrip("0").rstrip(".")


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


def _asset_rows(asset: dict[str, Any]) -> list[dict[str, Any]]:
    insight = asset.get("insight_input") if isinstance(asset.get("insight_input"), dict) else {}
    return [row for row in list(insight.get("rows") or []) if isinstance(row, dict)]


def _first_non_empty(*values: Any, fallback: str = "") -> str:
    for value in values:
        text = _clean_text(value)
        if text:
            return text
    return fallback


def _asset_metric_label(asset: dict[str, Any]) -> str:
    insight = asset.get("insight_input") if isinstance(asset.get("insight_input"), dict) else {}
    rows = _asset_rows(asset)
    row = rows[0] if rows else {}
    return _reader_label(
        _first_non_empty(
            insight.get("metric_localized_label"),
            insight.get("metric_label"),
            insight.get("metric"),
            insight.get("metric_raw_key"),
            row.get("metric_label"),
            row.get("metric"),
            row.get("metric_raw_key"),
            (asset.get("source_metric_names") or [""])[0] if isinstance(asset.get("source_metric_names"), list) and asset.get("source_metric_names") else "",
        ),
        fallback="关键指标",
    )


def _asset_dimension_label(asset: dict[str, Any]) -> str:
    insight = asset.get("insight_input") if isinstance(asset.get("insight_input"), dict) else {}
    rows = _asset_rows(asset)
    row = rows[0] if rows else {}
    return _reader_label(
        _first_non_empty(
            insight.get("dimension_localized_label"),
            insight.get("dimension_label"),
            insight.get("dimension"),
            insight.get("dimension_raw_key"),
            insight.get("dimension_a_label"),
            row.get("dimension"),
            row.get("dimension_label"),
            row.get("dimension_raw_key"),
            row.get("dimension_a_label"),
            (asset.get("source_dimension_names") or [""])[0] if isinstance(asset.get("source_dimension_names"), list) and asset.get("source_dimension_names") else "",
        ),
        fallback="关键维度",
    )


def _asset_top_bottom(asset: dict[str, Any]) -> tuple[str, str, str, str]:
    rows = _asset_rows(asset)
    if not rows:
        return "", "", "", ""
    metric = _asset_metric_label(asset)
    top = rows[0]
    bottom = rows[-1]
    top_name = _reader_label(
        _first_non_empty(
            top.get("dimension_value_label"),
            top.get("dimension_a_value_label"),
            top.get("segment"),
            top.get("top_segment"),
            top.get("top_segment_label"),
            top.get("类别"),
            top.get("消费客群"),
            top.get("区域"),
            top.get("渠道"),
        ),
        fallback="头部对象",
    )
    bottom_name = _reader_label(
        _first_non_empty(
            bottom.get("dimension_value_label"),
            bottom.get("dimension_a_value_label"),
            bottom.get("segment"),
            bottom.get("bottom_segment"),
            bottom.get("bottom_segment_label"),
            bottom.get("类别"),
            bottom.get("消费客群"),
            bottom.get("区域"),
            bottom.get("渠道"),
        ),
        fallback="尾部对象",
    )
    top_value = _format_reader_value(
        _first_non_empty(
            top.get("value"),
            top.get("top_value"),
            top.get("share_of_total") if _share_is_reader_meaningful(top) else "",
            fallback="",
        ),
        metric=metric,
    )
    bottom_value = _format_reader_value(
        _first_non_empty(
            bottom.get("value"),
            bottom.get("bottom_value"),
            bottom.get("share_of_total") if _share_is_reader_meaningful(bottom) else "",
            fallback="",
        ),
        metric=metric,
    )
    return top_name, top_value, bottom_name, bottom_value


def _weak_reader_title(title: Any) -> bool:
    text = _clean_text(title)
    if not text:
        return True
    weak_tokens = (
        "阅读路径",
        "主要发现",
        "执行摘要地图",
        "核心指标指数化趋势对比",
        "排名",
        "头部与尾部差异",
        "管理层应同时",
        "当前经营表现复盘",
    )
    if any(token in text for token in weak_tokens):
        return True
    if re.fullmatch(r"(图表|Exhibit)\s*\d+[:：]?", text, flags=re.I):
        return True
    return len(text) < 10


def _compile_asset_based_page_insight(page: dict[str, Any]) -> dict[str, str]:
    assets = [asset for asset in list(page.get("asset_refs") or []) if isinstance(asset, dict)]
    primary = assets[0] if assets else {}
    if not primary:
        return {}
    insight = primary.get("insight_input") if isinstance(primary.get("insight_input"), dict) else {}
    metric = _asset_metric_label(primary)
    dimension = _asset_dimension_label(primary)
    kind = str(primary.get("kind") or primary.get("asset_type") or "").lower()
    top_name, top_value, bottom_name, bottom_value = _asset_top_bottom(primary)
    rows = _asset_rows(primary)
    title = ""
    evidence = ""
    mechanism = ""
    action = ""
    if str(primary.get("asset_type") or "") == "collage":
        values = []
        for row in rows[:3]:
            row_metric = _reader_label(row.get("metric") or row.get("metric_label"), fallback="指标")
            row_value = _format_reader_value(row.get("value"), metric=row_metric)
            if row_metric and row_value:
                values.append(f"{row_metric}{row_value}")
        evidence_bits = "、".join(values[:3])
        title = f"{evidence_bits or metric}构成本期管理基准，行动页应锁定责任对象"
        evidence = f"当前摘要页汇总了{evidence_bits or metric}，这些指标需要共同决定资源优先级，而不是分散解读。"
        mechanism = f"摘要类页面的价值在于把规模、效率和风险压成同一套经营语言，帮助管理层快速确定复盘顺序。"
        action = f"经营负责人应把{evidence_bits or metric}拆成责任清单，明确每个对象的本期目标、复盘频率和纠偏动作。"
    elif "line" in kind or "index" in kind:
        metrics = [
            _reader_label(item)
            for item in list(insight.get("metric_raw_keys") or insight.get("source_metric_names") or primary.get("source_metric_names") or [])
            if _reader_label(item)
        ]
        metric_phrase = "、".join(metrics[:3]) + (f"等{len(metrics)}项指标" if len(metrics) > 3 else "")
        min_value = _format_reader_value(insight.get("min"), metric=metric)
        max_value = _format_reader_value(insight.get("max"), metric=metric)
        title = f"{metric_phrase or metric}按{dimension}波动扩大，最高值{max_value}高于低点{min_value}"
        evidence = f"{metric}在{dimension}维度的观测区间为{min_value}至{max_value}，说明规模、订单和效率指标不能只看单点均值。"
        mechanism = f"{dimension}上的波动会同时改变{metric}与资源回报顺序，需把高点成因和低点约束拆开复盘。"
        action = f"{dimension}负责人应把最高点{max_value}与低点{min_value}对应对象列入同一张周复盘表，分别定义放大动作和修复动作。"
    elif "matrix" in kind or "table" in str(primary.get("asset_type") or ""):
        if rows and ("dimension_a_value_label" in rows[0] or "dimension_b_value_label" in rows[0]):
            first = rows[0]
            dim_a = _reader_label(first.get("dimension_a_value_label") or first.get("dimension_a"), fallback="维度A")
            dim_b = _reader_label(first.get("dimension_b_value_label") or first.get("dimension_b"), fallback="维度B")
            value = _format_reader_value(first.get("value"), metric=metric)
            share = _format_reader_value(first.get("share_of_total"), metric="share") if _share_is_reader_meaningful(first) else ""
            title = f"{dim_a} x {dim_b}贡献{metric}{value}，交叉维度比单维排名更适合定优先级"
            evidence = f"{dim_a} x {dim_b}组合的{metric}达到{value}" + (f"，占比{share}" if share else "") + "，是当前交叉分层里最应先看的对象。"
            mechanism = f"交叉维度能区分区域、渠道或客群之间的组合效应，避免把单一排名误判为全局策略。"
            action = f"{dim_a}与{dim_b}的共同负责人应先复盘该组合的{metric}来源，再决定复制打法还是补齐短板。"
        elif top_name:
            title = f"{top_name}领先{metric}{top_value}，{bottom_name}决定尾部修复优先级"
            evidence = f"{top_name}的{metric}为{top_value}，{bottom_name}为{bottom_value}，头尾差距已经足以影响资源排序。"
            mechanism = f"{dimension}分层把规模贡献和尾部风险同时摊开，能避免只看总体均值导致的资源误配。"
            action = f"{dimension}负责人应保护{top_name}的有效打法，并给{bottom_name}设定{metric}修复阈值和复盘周期。"
    elif "bar" in kind or "pareto" in kind or top_name:
        title = f"{top_name}在{dimension}上贡献{metric}{top_value}，尾部{bottom_name}需要单独治理"
        evidence = f"{top_name}的{metric}为{top_value}，{bottom_name}为{bottom_value}，说明同一指标在不同{dimension}对象间差异明显。"
        mechanism = f"头部对象决定规模上限，尾部对象决定效率和风险下限，两类对象不应使用同一套动作。"
        action = f"{dimension}负责人应把{top_name}列为放大样板，把{bottom_name}列为修复清单，并分别跟踪{metric}变化。"
    if not title or not evidence:
        return {}
    return {
        "reader_claim": _clean_text(title, fallback=title),
        "evidence_sentence": _clean_text(evidence, fallback=title),
        "mechanism_sentence": _clean_text(mechanism, fallback=evidence),
        "action_sentence": _clean_text(action, fallback=evidence),
    }


def _apply_asset_based_reader_logic(pages: list[dict[str, Any]]) -> dict[str, Any]:
    rewritten_pages: list[int] = []
    blocked_pages: list[int] = []
    for page in pages:
        page_number = int(page.get("page_number") or 0)
        template = str(page.get("page_template_type") or "")
        if template in {"cover_page", "toc_navigation_page", "module_divider_page"}:
            continue
        contract = _compile_asset_based_page_insight(page)
        if not contract:
            blocked_pages.append(page_number)
            continue
        title = contract["reader_claim"]
        current_title = _clean_text(page.get("title"))
        evidence_title = contract["reader_claim"]
        should_rewrite = (
            _weak_reader_title(current_title)
            or _weak_reader_title(page.get("management_thesis"))
            or (bool(re.search(r"\d", evidence_title)) and not bool(re.search(r"\d", current_title)))
        )
        if should_rewrite:
            page["title_before_reader_logic_rewrite"] = page.get("title")
            page["title"] = evidence_title
            rewritten_pages.append(page_number)
        page["management_thesis"] = evidence_title
        page["claim"] = evidence_title
        page["page_insight_contract"] = contract
        page["claim_evidence_action"] = {
            "claim_role": "answer_first_title",
            "evidence_role": "primary_exhibit_or_table",
            "action_role": "specific_management_action",
            "claim_seed": contract["reader_claim"],
            "evidence_seed": contract["evidence_sentence"],
            "action_seed": contract["action_sentence"],
        }
    return {
        "rewritten_page_numbers": [page for page in rewritten_pages if page > 0],
        "blocked_page_numbers": [page for page in blocked_pages if page > 0],
    }


def _coerce_sequence(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        output: list[dict[str, Any]] = []
        for index, item in enumerate(value, start=1):
            if isinstance(item, dict):
                output.append(dict(item))
            elif str(item or "").strip():
                output.append({"page": index, "page_template_type": str(item).strip()})
        return output
    if isinstance(value, dict):
        return [
            {"page": index, "name": str(key), **(item if isinstance(item, dict) else {"value": item})}
            for index, (key, item) in enumerate(value.items(), start=1)
        ]
    text = str(value or "").strip()
    return [{"page": 1, "page_template_type": text}] if text else []


def _template_from_item(item: dict[str, Any]) -> str:
    explicit = _clean_text(
        item.get("page_template_type")
        or item.get("template_type")
        or item.get("page_type")
        or item.get("type")
        or item.get("role")
    ).lower()
    explicit = explicit.replace(" ", "_").replace("-", "_")
    if explicit in PAGE_TEMPLATE_TYPES:
        return explicit
    haystack = " ".join(str(value).lower() for value in item.values())
    for token, template in ROLE_TO_TEMPLATE.items():
        if token in haystack:
            return template
    return "thesis_chart_page"


def _collect_numbers(value: Any) -> list[float]:
    numbers: list[float] = []
    if isinstance(value, dict):
        for nested in value.values():
            numbers.extend(_collect_numbers(nested))
    elif isinstance(value, list):
        for item in value:
            numbers.extend(_collect_numbers(item))
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        numbers.append(float(value))
    return numbers


def _normalize_reader_asset_title(title: Any) -> str:
    text = _clean_text(title)
    text = text.replace("ranking", "排名").replace("Ranking", "排名")
    text = text.replace("排名ing", "排名")
    return text


def _valid_reader_asset(asset: dict[str, Any], *, asset_type: str) -> bool:
    title = _normalize_reader_asset_title(asset.get("title"))
    insight = asset.get("insight_input") if isinstance(asset.get("insight_input"), dict) else {}
    if "排名ing" in title or "Data Coverage Page" in title or "Evidence Page" in title:
        return False
    if asset_type in {"table", "collage"} and not insight:
        return False
    numbers = _collect_numbers(insight)
    if asset_type == "chart" and numbers and max(abs(number) for number in numbers) == 0:
        return False
    if title in {"信号标签板", "业态与客群卡片", "模块导航板"} and not insight:
        return False
    return True


def _read_assets(index_path: Path, *, key: str) -> list[dict[str, Any]]:
    payload = _read_json(index_path)
    assets = list(payload.get("assets") or [])
    output: list[dict[str, Any]] = []
    for item in assets:
        if not isinstance(item, dict):
            continue
        insight = item.get("insight_input") if isinstance(item.get("insight_input"), dict) else {}
        source_metric_names = list(item.get("source_metric_names") or [])
        source_dimension_names = list(item.get("source_dimension_names") or [])
        for metric_key in ("metric", "metric_raw_key", "raw_key", "localized_label"):
            metric_text = str(insight.get(metric_key) or "").strip()
            if metric_text and metric_text not in source_metric_names:
                source_metric_names.append(metric_text)
        for dimension_key in ("dimension", "dimension_raw_key", "group_column", "category_column"):
            dimension_text = str(insight.get(dimension_key) or "").strip()
            if dimension_text and dimension_text not in source_dimension_names:
                source_dimension_names.append(dimension_text)
        asset_payload = {
            "asset_id": str(item.get("asset_id") or item.get("chart_id") or item.get("table_id") or ""),
            "asset_type": key,
            "kind": str(item.get("kind") or key),
            "title": _normalize_reader_asset_title(item.get("title") or key),
            "path": str(item.get("path") or ""),
            "file_name": str(item.get("file_name") or ""),
            "recommended_page_role": str(item.get("recommended_page_role") or ""),
            "insight_input": insight,
            "source_metric_names": source_metric_names,
            "source_dimension_names": source_dimension_names,
            "visual_contract_tokens": item.get("visual_contract_tokens") if isinstance(item.get("visual_contract_tokens"), dict) else {},
            "valid_reader_asset": True,
        }
        if not _valid_reader_asset(asset_payload, asset_type=key):
            continue
        output.append(asset_payload)
    return output


def _asset_name_count(asset: dict[str, Any], key: str) -> int:
    value = asset.get(key)
    if isinstance(value, list):
        return len({str(item).strip() for item in value if str(item).strip()})
    return 0


def _asset_data_richness(asset: dict[str, Any]) -> int:
    kind = str(asset.get("kind") or "").lower()
    role = str(asset.get("recommended_page_role") or "").lower()
    score = _asset_name_count(asset, "source_metric_names") * 3 + _asset_name_count(asset, "source_dimension_names") * 4
    if any(token in kind for token in ("heatmap", "scatter", "pareto", "waterfall", "matrix", "bar")):
        score += 3
    if "paired_horizontal_bar" in kind:
        score += 12
    tokens = asset.get("visual_contract_tokens") if isinstance(asset.get("visual_contract_tokens"), dict) else {}
    if bool(tokens.get("matched_chart_grammar")):
        score += 10
    dominant_chart_grammar = str(tokens.get("dominant_chart_grammar") or "")
    if dominant_chart_grammar and dominant_chart_grammar != "chart_or_text_exhibit":
        score += 2
    if "pareto" in kind:
        score -= 5
    if any(token in role for token in ("category", "correlation", "priority", "relationship")):
        score += 2
    if "donut" in kind or "pie" in kind:
        score -= 6
    return score


def _kind_aliases(kind: str) -> set[str]:
    normalized = str(kind or "").strip().lower()
    groups = [
        {"right_labeled_index_line", "indexed_multi_line", "line", "indexed_trend"},
        {"paired_horizontal_bar_with_delta", "paired_horizontal_bar", "horizontal_bar", "grouped_bar", "bar"},
        {"pareto"},
        {"waterfall", "waterfall_bridge", "value_bridge"},
        {"matrix_table_with_group_headers", "table_grid", "heatmap", "matrix", "table"},
        {"grouped_bar", "vertical_bar", "bar", "pareto"},
        {"scatter_quadrant", "scatter", "portfolio_matrix"},
        {"stacked_bar_share", "share_map", "donut", "bar"},
        {"waterfall", "waterfall_bridge", "value_bridge"},
    ]
    for group in groups:
        if normalized in group:
            return set(group)
    return {normalized} if normalized else set()


def _asset_chart_match(asset: dict[str, Any], page_item: dict[str, Any] | None) -> tuple[float, str]:
    page_item = page_item if isinstance(page_item, dict) else {}
    required = str(
        page_item.get("required_chart_kind")
        or (page_item.get("chart_similarity_contract") if isinstance(page_item.get("chart_similarity_contract"), dict) else {}).get("required_chart_kind")
        or ""
    ).strip().lower()
    fallback = {
        str(item or "").strip().lower()
        for item in list(page_item.get("fallback_chart_kinds") or [])
        if str(item or "").strip()
    }
    if not required or str(asset.get("asset_type") or "") != "chart":
        return 0.5, "no_required_chart_kind"
    kind = str(asset.get("kind") or "").strip().lower()
    if kind == required or kind in _kind_aliases(required):
        return 1.0, "required_chart_kind_match"
    if required in {"right_labeled_index_line", "indexed_multi_line"}:
        return -0.55, "line_source_requires_indexed_line_asset"
    fallback_aliases: set[str] = set()
    for item in fallback:
        fallback_aliases.update(_kind_aliases(item))
    if kind in fallback or kind in fallback_aliases:
        return 0.74, "fallback_chart_kind_match"
    tokens = asset.get("visual_contract_tokens") if isinstance(asset.get("visual_contract_tokens"), dict) else {}
    profile_ids = {
        str(item or "")
        for item in list(tokens.get("source_chart_grammar_profile_ids") or [])
        if str(item or "").strip()
    }
    if str(page_item.get("source_chart_grammar_profile_id") or "") in profile_ids:
        return 0.85, "source_chart_profile_id_match"
    if kind in {"histogram", "line"} and required not in _kind_aliases(kind):
        return -0.4, "weak_distribution_asset_not_source_matched"
    return 0.0, "chart_kind_mismatch"


def _pick_assets(
    template_type: str,
    assets_by_type: dict[str, list[dict[str, Any]]],
    page_index: int,
    page_item: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    if template_type == "cover_page":
        return []
    if template_type in {"toc_navigation_page", "module_divider_page"}:
        candidates.extend(assets_by_type.get("collage", []))
        candidates.extend(assets_by_type.get("table", []))
        candidates.extend(assets_by_type.get("chart", []))
    if template_type in {"thesis_chart_page", "funnel_diagnosis_page", "scatter_diagnosis_page", "heatmap_leverage_page"}:
        candidates.extend(assets_by_type.get("chart", []))
    if template_type in {"comparison_matrix_page", "ranking_table_page", "appendix_glossary_page", "appendix_detail_table_page", "kpi_scorecard_page"}:
        candidates.extend(assets_by_type.get("table", []))
    if template_type in {"summary_map_page", "collage_preference_page", "comparison_matrix_page"}:
        candidates.extend(assets_by_type.get("collage", []))
    if not candidates:
        return []
    if template_type in {"thesis_chart_page", "funnel_diagnosis_page", "scatter_diagnosis_page", "heatmap_leverage_page"}:
        candidates = sorted(
            candidates,
            key=lambda asset: (_asset_chart_match(asset, page_item)[0] * 100, _asset_data_richness(asset)),
            reverse=True,
        )
    required_score = _asset_chart_match(candidates[0], page_item)[0]
    start = 0 if required_score >= 0.65 else max(0, (page_index - 1) % len(candidates))
    picked = candidates[start : start + 2]
    if len(picked) < 2 and len(candidates) > len(picked):
        picked.extend(candidates[: 2 - len(picked)])
    return picked[:2]


def _rebind_pages_to_chart_grammar(pages: list[dict[str, Any]], assets_by_type: dict[str, list[dict[str, Any]]]) -> None:
    chart_assets = list(assets_by_type.get("chart") or [])
    if not chart_assets:
        return
    for page in pages:
        required = str(page.get("required_chart_kind") or "").strip()
        if not required:
            continue
        current_assets = [asset for asset in list(page.get("asset_refs") or []) if isinstance(asset, dict)]
        current_score = max((_asset_chart_match(asset, page)[0] for asset in current_assets), default=-1.0)
        candidates = sorted(
            chart_assets,
            key=lambda asset: (_asset_chart_match(asset, page)[0] * 100, _asset_data_richness(asset)),
            reverse=True,
        )
        if not candidates:
            page["chart_fallback_reason"] = "no_chart_assets_available"
            continue
        best = candidates[0]
        best_score, best_reason = _asset_chart_match(best, page)
        if best_score >= max(0.65, current_score):
            secondary = [asset for asset in current_assets if str(asset.get("asset_id") or "") != str(best.get("asset_id") or "")]
            page["asset_refs"] = [best, *secondary[:1]]
            page["chart_type_match_score"] = round(best_score, 4)
            page["chart_type_match_reason"] = best_reason
        else:
            page["chart_type_match_score"] = round(current_score, 4)
            page["chart_fallback_reason"] = "no_asset_matching_required_chart_kind"


def _source_page_number_from_profile_id(value: Any) -> int:
    match = re.search(r"(\d+)$", str(value or "").strip())
    if not match:
        return 0
    try:
        return int(match.group(1))
    except Exception:
        return 0


def _align_chart_profiles_to_region_profiles(
    pages: list[dict[str, Any]],
    profiles_by_source_page: dict[int, dict[str, Any]],
) -> None:
    if not profiles_by_source_page:
        return
    for page in pages:
        if str(page.get("page_template_type") or "") == "cover_page":
            continue
        region_source_page = _source_page_number_from_profile_id(page.get("source_region_profile_id"))
        chart_source_page = _source_page_number_from_profile_id(page.get("source_chart_grammar_profile_id"))
        if region_source_page <= 0 or region_source_page == chart_source_page:
            continue
        profile = profiles_by_source_page.get(region_source_page)
        if not profile:
            continue
        existing_reason = str(page.get("source_chart_match_reason") or "").strip()
        page["source_chart_grammar_profile_id"] = str(profile.get("source_chart_grammar_profile_id") or page.get("source_chart_grammar_profile_id") or "")
        page["source_chart_match_reason"] = (
            f"{existing_reason}, aligned-to-source-region-profile"
            if existing_reason
            else "aligned-to-source-region-profile"
        )
        page["source_chart_primitive_scores"] = profile.get("primitive_scores") if isinstance(profile.get("primitive_scores"), dict) else page.get("source_chart_primitive_scores", {})
        chart_contract = page.get("chart_similarity_contract") if isinstance(page.get("chart_similarity_contract"), dict) else {}
        page["chart_similarity_contract"] = {
            **chart_contract,
            "source_chart_grammar_profile_id": page["source_chart_grammar_profile_id"],
            "source_region_profile_id": str(page.get("source_region_profile_id") or ""),
            "source_reference_alignment": "chart_profile_aligned_to_region_profile",
        }


def _asset_visual_key(asset: dict[str, Any]) -> str:
    return _asset_key(asset) or str(asset.get("asset_id") or asset.get("title") or "")


def _asset_kind_family(asset: dict[str, Any]) -> str:
    asset_type = str(asset.get("asset_type") or "").strip().lower()
    kind = str(asset.get("kind") or "").strip().lower()
    role = str(asset.get("recommended_page_role") or "").strip().lower()
    title = str(asset.get("title") or "").strip().lower()
    combined = f"{asset_type} {kind} {role} {title}"
    if asset_type == "table":
        if "scorecard" in combined or "kpi" in combined:
            return "kpi_scorecard"
        if "action" in combined or "priority" in combined:
            return "priority_action_table"
        if "ranking" in combined:
            return "ranking_detail_table"
        if "matrix" in combined or "correlation" in combined or "dimension" in combined:
            return "matrix_table_with_group_headers"
        return "detail_table"
    if asset_type == "collage":
        if "summary" in combined or "roadmap" in combined or "action" in combined:
            return "summary_map"
        if "gap" in combined or "benchmark" in combined or "matrix" in combined:
            return "gap_or_benchmark_collage"
        return "collage_grid"
    if "right_labeled" in combined or "indexed" in combined:
        return "right_labeled_index_line"
    if "line" in combined:
        return "line"
    if "heatmap" in combined or "correlation" in combined:
        return "heatmap"
    if "scatter" in combined or "quadrant" in combined or "portfolio" in combined:
        return "scatter_quadrant"
    if "waterfall" in combined or "bridge" in combined:
        return "waterfall"
    if "pareto" in combined:
        return "pareto"
    if "bar" in combined:
        return "bar"
    return kind or asset_type or "asset"


def _asset_business_question_ref(asset: dict[str, Any]) -> str:
    for key in ("business_question_ref", "story_role", "recommended_page_role", "title"):
        text = str(asset.get(key) or "").strip()
        if text:
            return text
    insight = asset.get("insight_input") if isinstance(asset.get("insight_input"), dict) else {}
    for key in ("management_meaning", "action_meaning", "question", "headline"):
        text = str(insight.get(key) or "").strip()
        if text:
            return text[:120]
    return ""


def _asset_binding_metadata(asset: dict[str, Any]) -> dict[str, Any]:
    metric_refs = sorted(_asset_metric_names(asset))
    dimension_refs = sorted(_asset_dimension_names(asset))
    return {
        "asset_id": str(asset.get("asset_id") or ""),
        "asset_key": _asset_visual_key(asset),
        "asset_type": str(asset.get("asset_type") or ""),
        "kind": str(asset.get("kind") or ""),
        "title": str(asset.get("title") or ""),
        "business_question_ref": _asset_business_question_ref(asset),
        "metric_refs": metric_refs,
        "dimension_refs": dimension_refs,
        "chart_kind_family": _asset_kind_family(asset),
        "source_chart_match_score": float(asset.get("source_chart_match_score") or 0),
        "reuse_priority": "low" if _asset_kind_family(asset) in {"heatmap", "line", "pareto"} else "normal",
        "primary_visual_eligible": bool(asset.get("valid_reader_asset", True)) and bool(_asset_visual_key(asset)),
    }


def _page_role_tokens(page: dict[str, Any]) -> str:
    return " ".join(
        str(page.get(key) or "").strip().lower()
        for key in (
            "page_template_type",
            "expected_conclusion_type",
            "logic_role",
            "argument_step",
            "title",
            "module",
            "required_chart_kind",
            "visual_region_mode",
        )
    )


def _asset_template_fit_score(asset: dict[str, Any], page: dict[str, Any]) -> tuple[float, str]:
    asset_type = str(asset.get("asset_type") or "").strip().lower()
    family = _asset_kind_family(asset)
    template = str(page.get("page_template_type") or "").strip().lower()
    required = str(page.get("required_chart_kind") or "").strip().lower()
    role_tokens = _page_role_tokens(page)
    asset_text = f"{asset.get('title') or ''} {asset.get('path') or ''} {asset.get('recommended_page_role') or ''}".lower()
    if required:
        if asset_type == "chart":
            if required in {"right_labeled_index_line", "indexed_multi_line"}:
                if family == "line" and any(token in asset_text for token in ("cumulative", "distribution", "累计", "分布")):
                    return 0.22, "distribution_cumulative_line_is_support_only"
                if family not in {"right_labeled_index_line", "line"} and str(asset.get("kind") or "").strip().lower() not in {
                    "right_labeled_index_line",
                    "indexed_multi_line",
                    "indexed_trend",
                    "line",
                }:
                    return -0.55, "line_source_requires_indexed_line_asset"
            if required == "paired_horizontal_bar_with_delta" and family in {"pareto", "waterfall"}:
                return 0.7, "paired_bar_source_visual_diversity_fallback"
            return _asset_chart_match(asset, page)
        if required in {"right_labeled_index_line", "indexed_multi_line"} and asset_type == "table":
            return -0.65, "line_source_cannot_be_replaced_by_table"
        if required == "matrix_table_with_group_headers":
            if asset_type == "table" and family in {
                "matrix_table_with_group_headers",
                "kpi_scorecard",
                "priority_action_table",
                "ranking_detail_table",
            }:
                return 0.96, "source_matrix_grammar_matched_by_structured_table"
            if asset_type == "collage" and family in {"summary_map", "gap_or_benchmark_collage"}:
                return 0.78, "source_matrix_grammar_matched_by_collage"
        if asset_type == "table" and template in {"comparison_matrix_page", "kpi_scorecard_page", "ranking_table_page"}:
            return 0.62, "table_fallback_for_chart_grammar"
        if asset_type == "collage" and template in {"summary_map_page", "collage_preference_page"}:
            return 0.58, "collage_fallback_for_chart_grammar"
        return -0.2, "asset_type_not_suitable_for_required_chart_kind"
    if template in {"comparison_matrix_page", "kpi_scorecard_page", "ranking_table_page"}:
        if asset_type == "table":
            return 0.95, "page_template_table_fit"
        if asset_type == "collage" and family == "gap_or_benchmark_collage":
            return 0.72, "page_template_collage_matrix_fit"
    if template in {"summary_map_page", "collage_preference_page"}:
        if asset_type == "collage":
            return 0.96, "page_template_collage_fit"
        if asset_type == "table" and family == "priority_action_table":
            return 0.9, "summary_page_action_table_fit"
    if template in {"thesis_chart_page", "funnel_diagnosis_page", "scatter_diagnosis_page", "heatmap_leverage_page"}:
        if asset_type == "chart":
            return 0.9, "page_template_chart_fit"
        if asset_type == "table" and "matrix" in role_tokens:
            return 0.68, "matrix_table_visual_fit"
    return 0.35, "generic_visual_asset_fit"


def _candidate_visual_assets_for_page(
    page: dict[str, Any],
    assets_by_type: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    if str(page.get("page_template_type") or "") == "cover_page":
        return []
    required = str(page.get("required_chart_kind") or "").strip().lower()
    template = str(page.get("page_template_type") or "").strip().lower()
    candidates: list[dict[str, Any]] = []
    if template in {"appendix_glossary_page", "appendix_detail_table_page"}:
        candidates.extend(assets_by_type.get("table", []))
        candidates.extend(assets_by_type.get("collage", []))
    elif template in {"summary_map_page", "collage_preference_page"}:
        # Summary pages should synthesize multiple signals. A single core chart
        # page reads like a mislabeled exhibit and is now blocked by the reader
        # quality gate, so prefer collage/action-table assets before charts.
        candidates.extend(assets_by_type.get("collage", []))
        candidates.extend(assets_by_type.get("table", []))
        if not candidates:
            candidates.extend(assets_by_type.get("chart", []))
    elif template in {"comparison_matrix_page", "kpi_scorecard_page", "ranking_table_page"}:
        candidates.extend(assets_by_type.get("table", []))
        candidates.extend(assets_by_type.get("collage", []))
        if not candidates:
            candidates.extend(assets_by_type.get("chart", []))
    elif required == "matrix_table_with_group_headers":
        candidates.extend(assets_by_type.get("table", []))
        candidates.extend(assets_by_type.get("collage", []))
        candidates.extend(assets_by_type.get("chart", []))
    elif required:
        candidates.extend(assets_by_type.get("chart", []))
        if required in {"right_labeled_index_line", "indexed_multi_line"} and template in {"comparison_matrix_page", "kpi_scorecard_page", "ranking_table_page"}:
            candidates.extend(assets_by_type.get("table", []))
    else:
        candidates.extend(assets_by_type.get("chart", []))
        candidates.extend(assets_by_type.get("table", []))
        candidates.extend(assets_by_type.get("collage", []))
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for asset in candidates:
        key = _asset_visual_key(asset)
        if not key or key in seen:
            continue
        seen.add(key)
        if not bool(_asset_binding_metadata(asset).get("primary_visual_eligible")):
            continue
        unique.append(asset)
    return unique


def _normalize_page_role_chart_contracts(pages: list[dict[str, Any]]) -> None:
    """Keep source chart grammar compatible with the page's reader role.

    A ranking/table/summary page should not inherit a source-page bar grammar
    and then fail later because it correctly chose a table/collage asset. The
    source grammar still matters, but page role wins for non-chart synthesis
    pages.
    """

    matrix_like_templates = {
        "comparison_matrix_page",
        "kpi_scorecard_page",
        "ranking_table_page",
        "summary_map_page",
        "collage_preference_page",
        "appendix_glossary_page",
        "appendix_detail_table_page",
    }
    matrix_fallbacks = [
        "table_grid",
        "heatmap",
        "matrix",
        "kpi_scorecard",
        "ranking_detail_table",
        "priority_action_table",
        "gap_or_benchmark_collage",
        "summary_map",
        "collage_grid",
    ]
    for page in pages:
        template = str(page.get("page_template_type") or "").strip().lower()
        if template not in matrix_like_templates:
            continue
        page["source_chart_match_reason"] = (
            str(page.get("source_chart_match_reason") or "").strip()
            or "page_role_chart_contract_normalized"
        )
        page["required_chart_kind"] = "matrix_table_with_group_headers"
        page["fallback_chart_kinds"] = list(dict.fromkeys(matrix_fallbacks + list(page.get("fallback_chart_kinds") or [])))
        chart_contract = page.get("chart_similarity_contract") if isinstance(page.get("chart_similarity_contract"), dict) else {}
        page["chart_similarity_contract"] = {
            **chart_contract,
            "required_chart_kind": "matrix_table_with_group_headers",
            "fallback_chart_kinds": page["fallback_chart_kinds"],
            "page_role_override": template,
        }


def _asset_binding_score(
    asset: dict[str, Any],
    page: dict[str, Any],
    *,
    usage_counts: dict[str, int],
    covered_metrics: set[str],
    covered_dimensions: set[str],
    family_usage_counts: dict[str, int],
    previous_asset_key: str,
    available_metrics: set[str],
    available_dimensions: set[str],
) -> tuple[float, dict[str, Any]]:
    key = _asset_visual_key(asset)
    fit_score, fit_reason = _asset_template_fit_score(asset, page)
    metrics = _asset_metric_names(asset)
    dimensions = _asset_dimension_names(asset)
    if available_metrics:
        metrics = metrics & available_metrics
    if available_dimensions:
        dimensions = dimensions & available_dimensions
    new_metrics = metrics - covered_metrics
    new_dimensions = dimensions - covered_dimensions
    use_count = int(usage_counts.get(key) or 0)
    family = _asset_kind_family(asset)
    family_use_count = int(family_usage_counts.get(family) or 0)
    asset_type = str(asset.get("asset_type") or "")
    score = fit_score * 100
    score += min(40, _asset_data_richness(asset) * 2)
    score += len(new_metrics) * 8 + len(new_dimensions) * 12
    if not metrics and not dimensions:
        score -= 250
    if str(page.get("required_chart_kind") or "").strip().lower() not in {"", "matrix_table_with_group_headers"} and not metrics:
        score -= 1000
    score += 28 if use_count == 0 else -18 * use_count
    if use_count >= 2:
        score -= 1000
    required = str(page.get("required_chart_kind") or "").strip().lower()
    if required and required != "matrix_table_with_group_headers" and fit_score < 0.5:
        score -= 1000
    if previous_asset_key and key == previous_asset_key:
        score -= 160
    score += 18 if family_use_count == 0 else -24 * family_use_count
    if family_use_count >= 2:
        score -= 86
    if family == "heatmap" and use_count >= 1:
        score -= 120
    if required == "matrix_table_with_group_headers" and asset_type == "collage":
        score -= 80
    if family in {"histogram", "line", "pareto"} and fit_score < 0.75:
        score -= 35
    asset_text = f"{asset.get('title') or ''} {asset.get('path') or ''} {asset.get('recommended_page_role') or ''}".lower()
    if any(token in asset_text for token in ("cumulative", "distribution", "累计", "分布")) and fit_score < 0.75:
        score -= 90
    template = str(page.get("page_template_type") or "").strip().lower()
    if template in {"comparison_matrix_page", "kpi_scorecard_page", "ranking_table_page"} and asset_type == "table":
        score += 24
    if template in {"summary_map_page", "collage_preference_page"} and asset_type == "collage":
        score += 24
    return score, {
        "fit_score": round(fit_score, 4),
        "fit_reason": fit_reason,
        "new_metric_refs": sorted(new_metrics),
        "new_dimension_refs": sorted(new_dimensions),
        "usage_count_before": use_count,
        "family_usage_count_before": family_use_count,
        "asset_kind_family": family,
    }


def _page_visual_density_plan(page: dict[str, Any], primary_asset: dict[str, Any] | None) -> dict[str, Any]:
    asset_type = str((primary_asset or {}).get("asset_type") or "").lower()
    family = _asset_kind_family(primary_asset or {})
    template = str(page.get("page_template_type") or "").lower()
    region_mode = str(page.get("visual_region_mode") or "").lower()
    if asset_type == "table" or "table" in template or "matrix" in family:
        target = 0.66
        boost = 1.24
    elif asset_type == "chart":
        target = 0.62 if family != "heatmap" else 0.68
        boost = 1.16
    elif asset_type == "collage":
        target = 0.58
        boost = 1.1
    else:
        target = 0.52
        boost = 1.0
    narrative_mode = "right_annotation" if "right" in region_mode else "bottom_two_column"
    if template in {"summary_map_page", "collage_preference_page"}:
        narrative_mode = "bottom_two_column"
    return {
        "visual_area_ratio_target": round(target, 4),
        "visual_height_boost": round(boost, 4),
        "narrative_mode": narrative_mode,
        "overflow_strategy": "split_table_or_promote_to_detail_page",
        "min_primary_visual_ratio": 0.42,
        "density_reason": f"{asset_type or 'asset'}:{family or 'generic'}",
    }


def _binding_coverage_summary(
    bindings: list[dict[str, Any]],
    *,
    available_metrics: set[str],
    available_dimensions: set[str],
) -> dict[str, Any]:
    primary_keys = [
        str(item.get("primary_asset_key") or "")
        for item in bindings
        if str(item.get("primary_asset_key") or "")
    ]
    counts: dict[str, int] = {}
    for key in primary_keys:
        counts[key] = counts.get(key, 0) + 1
    overused = sorted([key for key, count in counts.items() if count > 2])
    unique_primary = len(set(primary_keys))
    if primary_keys:
        overuse_excess = sum(max(0, count - 2) for count in counts.values())
        primary_asset_reuse_score = max(0.0, 1.0 - overuse_excess / max(1, len(primary_keys)))
    else:
        primary_asset_reuse_score = 1.0
    used_metrics: set[str] = set()
    used_dimensions: set[str] = set()
    low_visual_density_pages: list[int] = []
    family_counts: dict[str, int] = {}
    for item in bindings:
        family = str(item.get("primary_chart_kind_family") or "")
        if family:
            family_counts[family] = family_counts.get(family, 0) + 1
        used_metrics.update(_as_name_set(item.get("metric_refs")))
        used_dimensions.update(_as_name_set(item.get("dimension_refs")))
        density = item.get("page_visual_density_plan") if isinstance(item.get("page_visual_density_plan"), dict) else {}
        if float(density.get("visual_area_ratio_target") or 0) < 0.42 and str(item.get("page_template_type") or "") != "cover_page":
            low_visual_density_pages.append(int(item.get("page_number") or 0))
    key_diversity = min(1.0, unique_primary / max(1, min(5, len(primary_keys)))) if primary_keys else 1.0
    family_diversity = min(1.0, len(family_counts) / max(1, min(5, len(primary_keys)))) if primary_keys else 1.0
    chart_diversity_score = round(key_diversity * 0.45 + family_diversity * 0.55, 4)
    if available_metrics:
        used_metrics = used_metrics & available_metrics
    if available_dimensions:
        used_dimensions = used_dimensions & available_dimensions
    metric_target = min(6, len(available_metrics)) if len(available_metrics) >= 8 else max(1, len(available_metrics))
    dimension_target = min(3, len(available_dimensions)) if len(available_dimensions) >= 4 else max(1, len(available_dimensions))
    metric_score = min(1.0, len(used_metrics) / max(1, metric_target)) if available_metrics else 1.0
    dimension_score = min(1.0, len(used_dimensions) / max(1, dimension_target)) if available_dimensions else 1.0
    layout_density_score = 1.0 - min(1.0, len([p for p in low_visual_density_pages if p > 0]) / max(1, len(primary_keys)))
    return {
        "primary_asset_counts": counts,
        "primary_asset_family_counts": family_counts,
        "overused_asset_ids": overused,
        "primary_asset_reuse_score": round(primary_asset_reuse_score, 4),
        "chart_diversity_score": chart_diversity_score,
        "metric_dimension_coverage_score": round(metric_score * 0.58 + dimension_score * 0.42, 4),
        "layout_density_score": round(layout_density_score, 4),
        "low_visual_density_page_numbers": sorted({p for p in low_visual_density_pages if p > 0}),
        "used_metric_names": sorted(used_metrics),
        "used_dimension_names": sorted(used_dimensions),
    }


def _build_visual_asset_binding_plan(
    *,
    pages: list[dict[str, Any]],
    assets_by_type: dict[str, list[dict[str, Any]]],
    data_manifest: dict[str, Any],
    output_path: Path,
) -> dict[str, Any]:
    available_metrics = _available_metric_names(data_manifest)
    available_dimensions = _available_dimension_names(data_manifest)
    if not available_metrics:
        for assets in assets_by_type.values():
            for asset in assets:
                available_metrics.update(_asset_metric_names(asset))
    if not available_dimensions:
        for assets in assets_by_type.values():
            for asset in assets:
                available_dimensions.update(_asset_dimension_names(asset))
    usage_counts: dict[str, int] = {}
    family_usage_counts: dict[str, int] = {}
    covered_metrics: set[str] = set()
    covered_dimensions: set[str] = set()
    previous_asset_key = ""
    bindings: list[dict[str, Any]] = []
    candidate_diagnostics: list[dict[str, Any]] = []
    for page in pages:
        page_number = int(page.get("page_number") or len(bindings) + 1)
        candidates = _candidate_visual_assets_for_page(page, assets_by_type)
        scored: list[tuple[float, dict[str, Any], dict[str, Any]]] = []
        for asset in candidates:
            score, reason = _asset_binding_score(
                asset,
                page,
                usage_counts=usage_counts,
                covered_metrics=covered_metrics,
                covered_dimensions=covered_dimensions,
                family_usage_counts=family_usage_counts,
                previous_asset_key=previous_asset_key,
                available_metrics=available_metrics,
                available_dimensions=available_dimensions,
            )
            scored.append((score, asset, reason))
        if not scored:
            for asset in list(page.get("asset_refs") or []):
                if isinstance(asset, dict):
                    score, reason = _asset_binding_score(
                        asset,
                        page,
                        usage_counts=usage_counts,
                        covered_metrics=covered_metrics,
                        covered_dimensions=covered_dimensions,
                        family_usage_counts=family_usage_counts,
                        previous_asset_key=previous_asset_key,
                        available_metrics=available_metrics,
                        available_dimensions=available_dimensions,
                    )
                    scored.append((score, asset, reason))
        scored.sort(key=lambda item: item[0], reverse=True)
        primary = scored[0][1] if scored else None
        primary_score = scored[0][0] if scored else 0.0
        primary_reason = scored[0][2] if scored else {}
        secondary: dict[str, Any] | None = None
        if primary:
            primary_key = _asset_visual_key(primary)
            for _score, asset, _reason in scored[1:]:
                if _asset_visual_key(asset) != primary_key:
                    secondary = asset
                    break
            usage_counts[primary_key] = usage_counts.get(primary_key, 0) + 1
            primary_family = _asset_kind_family(primary)
            family_usage_counts[primary_family] = family_usage_counts.get(primary_family, 0) + 1
            covered_metrics.update(_asset_metric_names(primary))
            covered_dimensions.update(_asset_dimension_names(primary))
            if available_metrics:
                covered_metrics = covered_metrics & available_metrics
            if available_dimensions:
                covered_dimensions = covered_dimensions & available_dimensions
            previous_asset_key = primary_key
        primary_meta = _asset_binding_metadata(primary or {})
        bound_assets = [asset for asset in (primary, secondary) if isinstance(asset, dict)]
        usage_after = usage_counts.get(str(primary_meta.get("asset_key") or ""), 0)
        binding = {
            "page_number": page_number,
            "page_template_type": str(page.get("page_template_type") or ""),
            "required_chart_kind": str(page.get("required_chart_kind") or ""),
            "source_chart_grammar_profile_id": str(page.get("source_chart_grammar_profile_id") or ""),
            "source_region_profile_id": str(page.get("source_region_profile_id") or ""),
            "primary_asset_key": primary_meta.get("asset_key", ""),
            "primary_asset_id": primary_meta.get("asset_id", ""),
            "primary_asset_type": primary_meta.get("asset_type", ""),
            "primary_asset_kind": primary_meta.get("kind", ""),
            "primary_chart_kind_family": primary_meta.get("chart_kind_family", ""),
            "primary_asset_title": primary_meta.get("title", ""),
            "business_question_ref": primary_meta.get("business_question_ref", ""),
            "metric_refs": primary_meta.get("metric_refs", []),
            "dimension_refs": primary_meta.get("dimension_refs", []),
            "binding_score": round(primary_score, 4),
            "binding_reason": primary_reason,
            "reuse_reason": "allowed_second_use_for_source_chart_grammar" if usage_after == 2 else "",
            "secondary_asset_keys": [_asset_visual_key(asset) for asset in bound_assets[1:] if _asset_visual_key(asset)],
            "page_visual_density_plan": _page_visual_density_plan(page, primary),
            "candidate_count": len(scored),
        }
        bindings.append(binding)
        candidate_diagnostics.append({
            "page_number": page_number,
            "top_candidates": [
                {
                    "asset_key": _asset_visual_key(asset),
                    "asset_type": str(asset.get("asset_type") or ""),
                    "kind": str(asset.get("kind") or ""),
                    "title": str(asset.get("title") or ""),
                    "score": round(score, 4),
                    "reason": reason,
                }
                for score, asset, reason in scored[:6]
            ],
        })
    coverage = _binding_coverage_summary(
        bindings,
        available_metrics=available_metrics,
        available_dimensions=available_dimensions,
    )
    plan = {
        "visual_asset_binding_plan_version": "visual-asset-binding-plan-v1",
        "planner_goal": "avoid_repeated_primary_visuals_and_expand_metric_dimension_coverage",
        "max_primary_asset_reuse": 2,
        "bindings": bindings,
        "candidate_diagnostics": candidate_diagnostics,
        **coverage,
    }
    _write_json(output_path, plan)
    return plan


def _apply_visual_asset_binding_plan(
    pages: list[dict[str, Any]],
    assets_by_type: dict[str, list[dict[str, Any]]],
    binding_plan: dict[str, Any],
) -> None:
    asset_lookup: dict[str, dict[str, Any]] = {}
    for assets in assets_by_type.values():
        for asset in assets:
            key = _asset_visual_key(asset)
            if key:
                asset_lookup[key] = asset
    bindings_by_page = {
        int(item.get("page_number") or 0): item
        for item in list(binding_plan.get("bindings") or [])
        if isinstance(item, dict)
    }
    for page in pages:
        page_number = int(page.get("page_number") or 0)
        binding = bindings_by_page.get(page_number)
        if not binding:
            continue
        primary_key = str(binding.get("primary_asset_key") or "")
        primary_asset = asset_lookup.get(primary_key)
        secondary_assets = [
            asset_lookup[key]
            for key in list(binding.get("secondary_asset_keys") or [])
            if str(key or "") in asset_lookup
        ]
        table_templates = {
            "kpi_scorecard_page",
            "comparison_matrix_page",
            "ranking_table_page",
            "appendix_detail_table_page",
            "appendix_glossary_page",
        }
        template_type = str(page.get("page_template_type") or "")
        if primary_asset and template_type in table_templates:
            primary_key_for_compare = _asset_visual_key(primary_asset)
            table_candidates = [
                asset
                for asset in list(assets_by_type.get("table") or [])
                if _asset_visual_key(asset) and _asset_visual_key(asset) != primary_key_for_compare
            ]
            if not secondary_assets or str(secondary_assets[0].get("asset_type") or secondary_assets[0].get("kind") or "").lower() != "table":
                replacement = next(
                    (
                        asset
                        for asset in table_candidates
                        if _asset_visual_key(asset) not in {
                            _asset_visual_key(item) for item in secondary_assets if isinstance(item, dict)
                        }
                    ),
                    None,
                )
                if replacement:
                    secondary_assets = [replacement, *secondary_assets[:1]]
        if primary_asset:
            page["asset_refs"] = [primary_asset, *secondary_assets[:1]]
        page["visual_asset_binding"] = {
            key: value
            for key, value in binding.items()
            if key not in {"candidate_count"}
        }
        page["primary_asset_id"] = str(binding.get("primary_asset_id") or "")
        page["primary_asset_kind"] = str(binding.get("primary_asset_kind") or "")
        page["primary_asset_key"] = primary_key
        page["page_visual_density_plan"] = binding.get("page_visual_density_plan") if isinstance(binding.get("page_visual_density_plan"), dict) else {}
        if (
            str(binding.get("primary_asset_type") or "").strip().lower() in {"table", "collage"}
            and str(page.get("visual_region_mode") or "") == "visual_then_lower_narrative"
        ):
            region_contract = page.get("region_layout_contract") if isinstance(page.get("region_layout_contract"), dict) else {}
            if float(region_contract.get("right_annotation_width_ratio") or 0) >= 0.12:
                page["visual_region_mode"] = "visual_with_right_annotation"
                page["source_page_match_reason"] = f"{page.get('source_page_match_reason') or ''}, bound-asset-uses-right-reader-column".strip(", ")
                page["region_layout_contract"] = {**region_contract, "visual_region_mode": "visual_with_right_annotation"}
        if binding.get("reuse_reason"):
            page["asset_reuse_reason"] = str(binding.get("reuse_reason") or "")


def _page_management_thesis(title: str, template_type: str) -> str:
    cleaned = _clean_text(title, fallback="本页经营判断")
    if template_type in {"cover_page", "toc_navigation_page", "module_divider_page"}:
        return cleaned
    return cleaned


def _logic_reference_payload(workspace: Path) -> dict[str, Any]:
    return _read_json(workspace / "historical_logic_reference.json")


def _logic_contract_from_sources(reverse_spec: dict[str, Any], logic_reference: dict[str, Any]) -> dict[str, Any]:
    contract = reverse_spec.get("logic_flow_contract")
    if not isinstance(contract, dict) or not contract:
        contract = logic_reference.get("logic_flow_contract")
    if not isinstance(contract, dict):
        contract = {}
    argument_arc = reverse_spec.get("argument_arc")
    if not isinstance(argument_arc, list) or not argument_arc:
        argument_arc = contract.get("argument_arc") if isinstance(contract.get("argument_arc"), list) else []
    if not argument_arc:
        argument_arc = logic_reference.get("argument_arc") if isinstance(logic_reference.get("argument_arc"), list) else []
    return {
        "available": bool(contract or logic_reference.get("available")),
        "dominant_logic_pattern": str(
            contract.get("dominant_logic_pattern")
            or logic_reference.get("dominant_logic_pattern")
            or ""
        ),
        "title_chain_mode": str(contract.get("title_chain_mode") or ""),
        "argument_arc": [str(item) for item in list(argument_arc or []) if str(item).strip()],
        "recommended_argument_arc": [
            str(item)
            for item in list(contract.get("recommended_argument_arc") or logic_reference.get("argument_arc") or [])
            if str(item).strip()
        ],
        "claim_evidence_action_required": bool(
            contract.get("claim_evidence_action_required")
            or contract.get("claim_evidence_action_page_count")
            or logic_reference.get("available")
        ),
        "transition_rules": list(contract.get("transition_rules") or logic_reference.get("page_transition_rules") or [])[:30],
    }


def _logic_role_for_page(page: dict[str, Any], *, index: int, total: int) -> str:
    explicit = str(page.get("logic_role") or page.get("argument_step") or page.get("page_logic_role") or "").strip()
    if explicit:
        return explicit
    template = str(page.get("page_template_type") or "").lower()
    conclusion = str(page.get("expected_conclusion_type") or "").lower()
    title = str(page.get("title") or "").lower()
    combined = f"{template} {conclusion} {title}"
    if index == 1 or template == "cover_page":
        return "opening_thesis"
    if template in {"toc_navigation_page", "module_divider_page"}:
        return "business_question" if index <= max(3, total // 4) else "transition_navigation"
    if template in {"appendix_glossary_page", "appendix_detail_table_page"} or index >= max(1, total - 1):
        return "appendix_support"
    if "action" in combined or "recommend" in combined or template == "summary_map_page":
        return "recommendation" if index >= max(4, int(total * 0.65)) else "management_implication"
    if template in {"comparison_matrix_page", "ranking_table_page", "kpi_scorecard_page"}:
        return "contrast_or_segmentation"
    if template in {"funnel_diagnosis_page", "scatter_diagnosis_page", "heatmap_leverage_page"}:
        return "driver_explanation"
    if template == "collage_preference_page":
        return "management_implication"
    if template == "thesis_chart_page":
        return "diagnostic_evidence"
    return "management_implication" if index >= max(3, int(total * 0.7)) else "diagnostic_evidence"


def _claim_evidence_action_for_page(page: dict[str, Any]) -> dict[str, Any]:
    existing = page.get("claim_evidence_action")
    if isinstance(existing, dict) and existing:
        return existing
    role = str(page.get("logic_role") or page.get("argument_step") or "").strip()
    template = str(page.get("page_template_type") or "").strip()
    title = _clean_text(page.get("title"), fallback=template)
    asset_refs = [asset for asset in list(page.get("asset_refs") or []) if isinstance(asset, dict)]
    evidence_labels = [
        _clean_text(asset.get("title") or asset.get("asset_id") or asset.get("kind"), fallback="evidence_asset")
        for asset in asset_refs[:3]
    ]
    if not evidence_labels and template not in {"cover_page", "toc_navigation_page", "module_divider_page"}:
        evidence_labels = [str(page.get("storyline_source") or "page_plan")]
    return {
        "claim_role": "answer_first_title" if role not in {"appendix_support", "transition_navigation"} else "support_or_navigation_claim",
        "evidence_role": "primary_exhibit_or_table" if evidence_labels else "section_positioning",
        "action_role": "explicit_action_or_implication" if role in {"management_implication", "recommendation"} else "diagnostic_next_step",
        "claim_seed": title[:240],
        "evidence_seeds": evidence_labels,
        "action_seed": _clean_text(page.get("management_thesis"), fallback=title)[:280],
    }


def _apply_report_logic_to_pages(
    pages: list[dict[str, Any]],
    *,
    reverse_spec: dict[str, Any],
    logic_reference: dict[str, Any],
) -> dict[str, Any]:
    contract = _logic_contract_from_sources(reverse_spec, logic_reference)
    total = len(pages)
    for index, page in enumerate(pages, start=1):
        role = _logic_role_for_page(page, index=index, total=total)
        page["logic_role"] = role
        page["argument_step"] = str(page.get("argument_step") or role)
        page["claim_evidence_action"] = _claim_evidence_action_for_page(page)
        if index == 1:
            page["logic_transition"] = "open_argument"
        else:
            previous_role = str(pages[index - 2].get("logic_role") or "")
            page["logic_transition"] = f"{previous_role}_to_{role}" if previous_role else "continue_argument"
    role_counts: dict[str, int] = {}
    for page in pages:
        role = str(page.get("logic_role") or "")
        if role:
            role_counts[role] = role_counts.get(role, 0) + 1
    return {
        **contract,
        "applied_page_count": len(pages),
        "applied_logic_role_counts": role_counts,
    }


def _template_for_chart_asset(asset: dict[str, Any]) -> str:
    role = str(asset.get("recommended_page_role") or "").lower()
    kind = str(asset.get("asset_type") or asset.get("kind") or "").lower()
    title = str(asset.get("title") or "").lower()
    combined = f"{role} {kind} {title}"
    if "scatter" in combined or "quadrant" in combined:
        return "scatter_diagnosis_page"
    if "heatmap" in combined or "correlation" in combined:
        return "heatmap_leverage_page"
    if "waterfall" in combined or "bridge" in combined:
        return "funnel_diagnosis_page"
    if "bubble" in combined or "portfolio" in combined or "2x2" in combined:
        return "scatter_diagnosis_page"
    if "pareto" in combined or "share" in combined:
        return "comparison_matrix_page"
    return "thesis_chart_page"


def _template_for_table_asset(asset: dict[str, Any]) -> str:
    role = str(asset.get("recommended_page_role") or "").lower()
    title = str(asset.get("title") or "").lower()
    combined = f"{role} {title}"
    if "kpi" in combined or "scorecard" in combined:
        return "kpi_scorecard_page"
    if "ranking" in combined:
        return "ranking_table_page"
    if "glossary" in combined:
        return "appendix_glossary_page"
    if "appendix" in combined or "detail" in combined:
        return "appendix_detail_table_page"
    if "action" in combined or "summary" in combined:
        return "summary_map_page"
    return "comparison_matrix_page"


def _template_for_collage_asset(asset: dict[str, Any]) -> str:
    role = str(asset.get("recommended_page_role") or "").lower()
    title = str(asset.get("title") or "").lower()
    combined = f"{role} {title}"
    if "module" in combined or "navigation" in combined:
        return "summary_map_page"
    if "summary" in combined or "roadmap" in combined or "action" in combined:
        return "summary_map_page"
    if "gap" in combined or "matrix" in combined or "benchmark" in combined:
        return "comparison_matrix_page"
    return "collage_preference_page"


def _asset_key(asset: dict[str, Any]) -> str:
    return str(asset.get("path") or asset.get("file_name") or asset.get("asset_id") or asset.get("title") or "")


def _page_has_asset_type(page: dict[str, Any], asset_type: str) -> bool:
    return any(
        isinstance(asset, dict) and str(asset.get("asset_type") or "") == asset_type
        for asset in list(page.get("asset_refs") or [])
    )


def _asset_page_count(pages: list[dict[str, Any]], asset_type: str) -> int:
    return sum(1 for page in pages if _page_has_asset_type(page, asset_type))


def _used_asset_keys(pages: list[dict[str, Any]], asset_type: str) -> set[str]:
    return {
        _asset_key(asset)
        for page in pages
        for asset in list(page.get("asset_refs") or [])
        if isinstance(asset, dict) and str(asset.get("asset_type") or "") == asset_type
    }


def _append_asset_pages_if_needed(
    pages: list[dict[str, Any]],
    *,
    assets: list[dict[str, Any]],
    asset_type: str,
    target: int,
    template_for_asset: Any,
    module: str,
    conclusion_type: str,
    auto_added_reason: str = "asset_density_floor",
) -> None:
    if not assets or target <= 0:
        return
    page_count = _asset_page_count(pages, asset_type)
    if page_count >= target:
        return
    used_keys = _used_asset_keys(pages, asset_type)
    for asset in assets:
        if page_count >= target:
            break
        key = _asset_key(asset)
        if key and key in used_keys:
            continue
        page_count += 1
        pages.append(
            {
                "page_number": len(pages) + 1,
                "page_template_type": template_for_asset(asset),
                "module": module,
                "title": _clean_text(asset.get("title"), fallback=f"{asset_type.title()} Page {page_count}"),
                "density_class": "visual" if asset_type != "table" else "dense",
                "expected_conclusion_type": conclusion_type,
                "asset_refs": [asset],
                "reader_facing": True,
                "storyline_source": str(asset.get("source_view") or "asset_index"),
                "management_thesis": _page_management_thesis(
                    _clean_text(asset.get("title"), fallback=f"{asset_type.title()} Page {page_count}"),
                    template_for_asset(asset),
                ),
                "fallback_points_source": str(asset.get("source_view") or "asset_index"),
                "primary_asset_role": str(asset.get("story_role") or asset.get("recommended_page_role") or asset.get("kind") or ""),
                "auto_added_reason": auto_added_reason,
            }
        )
        if key:
            used_keys.add(key)


def _append_chart_pages_if_needed(
    pages: list[dict[str, Any]],
    *,
    chart_assets: list[dict[str, Any]],
) -> None:
    target = min(len(chart_assets), 12)
    _append_asset_pages_if_needed(
        pages,
        assets=chart_assets,
        asset_type="chart",
        target=target,
        template_for_asset=_template_for_chart_asset,
        module="可视化诊断",
        conclusion_type="chart_driven_management_thesis",
    )


def _family_from_reverse_spec(payload: dict[str, Any]) -> str:
    family = _clean_text(payload.get("historical_report_family"))
    if family:
        return family
    combined = " ".join(str(value).lower() for value in payload.values())
    if "mckinsey" in combined or "consulting" in combined or "pyramid" in combined or "issue tree" in combined:
        return "mckinsey_consulting_deck_family"
    if "yili" in combined or "brand" in combined or "blue" in combined:
        return "brand_analysis_deck_yili_family"
    if "dark" in combined or "editorial" in combined:
        return "dark_editorial_management_family"
    if "management" in combined and "blue" in combined:
        return "management_report_light_blue_family"
    return "generic_chinese_analysis_deck"


def _append_scaffold_page(pages: list[dict[str, Any]], *, template_type: str, title: str, module: str) -> None:
    pages.append(
        {
            "page_number": len(pages) + 1,
            "page_template_type": template_type,
            "module": module,
            "title": title,
            "density_class": "navigation" if template_type in {"cover_page", "toc_navigation_page", "module_divider_page"} else "standard",
            "expected_conclusion_type": "deck_scaffold",
            "asset_refs": [],
            "reader_facing": template_type not in {"appendix_glossary_page", "appendix_detail_table_page"},
            "storyline_source": "family_scaffold",
            "management_thesis": _page_management_thesis(title, template_type),
            "fallback_points_source": "family_scaffold",
            "primary_asset_role": "",
        }
    )


def _ensure_min_template_count(
    pages: list[dict[str, Any]],
    *,
    template_type: str,
    minimum: int,
    title: str,
    module: str,
) -> None:
    current = sum(1 for page in pages if str(page.get("page_template_type") or "") == template_type)
    while current < minimum:
        suffix = "" if minimum == 1 else f" {current + 1}"
        _append_scaffold_page(pages, template_type=template_type, title=f"{title}{suffix}", module=module)
        current += 1


def _ensure_family_scaffold_pages(
    pages: list[dict[str, Any]],
    *,
    family: str,
    assets_by_type: dict[str, list[dict[str, Any]]],
) -> None:
    _ensure_min_template_count(pages, template_type="cover_page", minimum=1, title="报告封面", module="navigation")
    _ensure_min_template_count(pages, template_type="toc_navigation_page", minimum=1, title="阅读路径", module="navigation")
    if family == "brand_analysis_deck_yili_family":
        _ensure_min_template_count(pages, template_type="module_divider_page", minimum=3, title="核心议题分节", module="navigation")
        _ensure_min_template_count(pages, template_type="summary_map_page", minimum=1, title="核心结论地图", module="summary")
        if assets_by_type.get("table"):
            _ensure_min_template_count(pages, template_type="ranking_table_page", minimum=1, title="排序明细", module="data appendix")
            _ensure_min_template_count(pages, template_type="appendix_glossary_page", minimum=1, title="指标口径", module="appendix")
            _ensure_min_template_count(pages, template_type="appendix_detail_table_page", minimum=1, title="附录明细", module="appendix")
        if assets_by_type.get("collage"):
            _ensure_min_template_count(pages, template_type="collage_preference_page", minimum=1, title="综合信号图", module="visual synthesis")
    elif family == "mckinsey_consulting_deck_family":
        _ensure_min_template_count(pages, template_type="summary_map_page", minimum=1, title="核心结论地图", module="summary")
        if assets_by_type.get("table"):
            _ensure_min_template_count(pages, template_type="ranking_table_page", minimum=1, title="排序明细", module="data appendix")
    else:
        _ensure_min_template_count(pages, template_type="summary_map_page", minimum=1, title="核心结论地图", module="summary")
        if assets_by_type.get("table"):
            _ensure_min_template_count(pages, template_type="appendix_detail_table_page", minimum=1, title="附录明细", module="appendix")


def _append_first_unused_asset_page(
    pages: list[dict[str, Any]],
    *,
    assets: list[dict[str, Any]],
    asset_type: str,
    template_for_asset: Any,
    module: str,
    conclusion_type: str,
) -> bool:
    used_keys = _used_asset_keys(pages, asset_type)
    for asset in assets:
        key = _asset_key(asset)
        if key and key in used_keys:
            continue
        pages.append(
            {
                "page_number": len(pages) + 1,
                "page_template_type": template_for_asset(asset),
                "module": module,
                "title": _clean_text(asset.get("title"), fallback=f"{asset_type.title()} Detail"),
                "density_class": "dense" if asset_type == "table" else "visual",
                "expected_conclusion_type": conclusion_type,
                "asset_refs": [asset],
                "reader_facing": asset_type != "table",
                "storyline_source": str(asset.get("source_view") or "family_minimum_page_fill"),
                "management_thesis": _page_management_thesis(
                    _clean_text(asset.get("title"), fallback=f"{asset_type.title()} Detail"),
                    template_for_asset(asset),
                ),
                "fallback_points_source": str(asset.get("source_view") or "family_minimum_page_fill"),
                "primary_asset_role": str(asset.get("story_role") or asset.get("recommended_page_role") or asset.get("kind") or ""),
                "auto_added_reason": "family_minimum_page_count",
            }
        )
        return True
    return False


def _ensure_family_acceptance_floor(
    pages: list[dict[str, Any]],
    *,
    family: str,
    assets_by_type: dict[str, list[dict[str, Any]]],
) -> None:
    if family not in {"brand_analysis_deck_yili_family", "mckinsey_consulting_deck_family"}:
        return
    _ensure_family_scaffold_pages(pages, family=family, assets_by_type=assets_by_type)
    required_floor = 12
    while len(pages) < required_floor:
        if _append_first_unused_asset_page(
            pages,
            assets=assets_by_type.get("chart", []),
            asset_type="chart",
            template_for_asset=_template_for_chart_asset,
            module="Visual diagnosis",
            conclusion_type="chart_driven_management_thesis",
        ):
            continue
        if _append_first_unused_asset_page(
            pages,
            assets=assets_by_type.get("table", []),
            asset_type="table",
            template_for_asset=_template_for_table_asset,
            module="Data detail",
            conclusion_type="table_driven_management_detail",
        ):
            continue
        if _append_first_unused_asset_page(
            pages,
            assets=assets_by_type.get("collage", []),
            asset_type="collage",
            template_for_asset=_template_for_collage_asset,
            module="Synthesis",
            conclusion_type="collage_driven_storytelling",
        ):
            continue
        break


def _ensure_visual_asset_density_floor(
    pages: list[dict[str, Any]],
    *,
    family: str,
    assets_by_type: dict[str, list[dict[str, Any]]],
) -> None:
    """Keep enough current-data exhibits after short source-PDF compaction.

    A 7-page source deck can still be used to produce a richer current-data
    report. This floor prevents the visual contract page bounds from trimming
    away nearly all chart/table/collage evidence.
    """
    chart_assets = assets_by_type.get("chart", [])
    table_assets = assets_by_type.get("table", [])
    collage_assets = assets_by_type.get("collage", [])
    chart_target = min(len(chart_assets), 9)
    table_target = min(len(table_assets), 3)
    collage_target = min(len(collage_assets), 2)
    _append_asset_pages_if_needed(
        pages,
        assets=chart_assets,
        asset_type="chart",
        target=chart_target,
        template_for_asset=_template_for_chart_asset,
        module="可视化诊断",
        conclusion_type="chart_driven_management_thesis",
        auto_added_reason="visual_asset_density_floor",
    )
    _append_asset_pages_if_needed(
        pages,
        assets=table_assets,
        asset_type="table",
        target=table_target,
        template_for_asset=_template_for_table_asset,
        module="数据明细",
        conclusion_type="table_driven_management_detail",
        auto_added_reason="visual_asset_density_floor",
    )
    _append_asset_pages_if_needed(
        pages,
        assets=collage_assets,
        asset_type="collage",
        target=collage_target,
        template_for_asset=_template_for_collage_asset,
        module="综合研判",
        conclusion_type="collage_driven_storytelling",
        auto_added_reason="visual_asset_density_floor",
    )


def _ensure_recommendation_page(
    pages: list[dict[str, Any]],
    *,
    assets_by_type: dict[str, list[dict[str, Any]]],
) -> None:
    if any(str(page.get("logic_role") or page.get("argument_step") or "") == "recommendation" for page in pages):
        return
    assets: list[dict[str, Any]] = []
    for asset_type in ("collage", "table", "chart"):
        for asset in list(assets_by_type.get(asset_type) or []):
            if _asset_key(asset) not in _used_asset_keys(pages, asset_type):
                assets.append(asset)
                break
        if assets:
            break
    page: dict[str, Any] = {
        "page_number": len(pages) + 1,
        "page_template_type": "summary_map_page",
        "module": "行动建议",
        "title": "下一步管理动作与资源配置优先级",
        "density_class": "standard",
        "expected_conclusion_type": "recommendation",
        "asset_refs": assets[:1],
        "reader_facing": True,
        "storyline_source": "recommendation_floor",
        "management_thesis": "把已经识别的增长、结构、效率与风险信号转成当期可执行动作，优先处理影响规模和利润质量的关键杠杆。",
        "fallback_points_source": "recommendation_floor",
        "primary_asset_role": str(assets[0].get("recommended_page_role") or assets[0].get("kind") or "") if assets else "",
        "logic_role": "recommendation",
        "argument_step": "recommendation",
        "auto_added_reason": "report_logic_recommendation_floor",
    }
    pages.append(page)


def _asset_usage_summary(pages: list[dict[str, Any]], assets_by_type: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for asset_type, assets in assets_by_type.items():
        used = _used_asset_keys(pages, asset_type)
        available = {_asset_key(asset) for asset in assets if _asset_key(asset)}
        summary[asset_type] = {
            "available": len(assets),
            "used": len([key for key in used if not available or key in available]),
            "page_count": _asset_page_count(pages, asset_type),
            "coverage_ratio": round((len(used) / len(available)), 4) if available else 0,
        }
    return summary


def _as_name_set(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {str(item).strip() for item in value if str(item).strip()}


def _read_manifest_artifact(data_manifest: dict[str, Any], artifact_key: str) -> dict[str, Any]:
    source_artifacts = data_manifest.get("source_artifacts")
    if not isinstance(source_artifacts, dict):
        return {}
    path_text = str(source_artifacts.get(artifact_key) or "").strip()
    if not path_text:
        return {}
    return _read_json(Path(path_text))


def _available_metric_names(data_manifest: dict[str, Any]) -> set[str]:
    names = _as_name_set(data_manifest.get("used_metric_names"))
    names.update(_as_name_set(data_manifest.get("metric_names")))
    if names:
        return names
    metric_inventory = _read_manifest_artifact(data_manifest, "metric_inventory")
    for item in list(metric_inventory.get("metrics") or []):
        if not isinstance(item, dict):
            continue
        for key in ("raw_key", "metric_raw_key", "localized_label", "metric_localized_label"):
            text = str(item.get(key) or "").strip()
            if text:
                names.add(text)
    cube = _read_manifest_artifact(data_manifest, "dimension_metric_cube")
    for item in list(cube.get("cube") or []):
        if not isinstance(item, dict):
            continue
        for key in ("metric_raw_key", "metric_localized_label"):
            text = str(item.get(key) or "").strip()
            if text:
                names.add(text)
    return names


def _available_derived_metric_names(data_manifest: dict[str, Any]) -> set[str]:
    names = _as_name_set(data_manifest.get("used_derived_metric_names"))
    names.update(_as_name_set(data_manifest.get("derived_metric_names")))
    derived_inventory = _read_manifest_artifact(data_manifest, "derived_metric_inventory")
    for item in list(derived_inventory.get("metrics") or []):
        if not isinstance(item, dict):
            continue
        for key in ("raw_key", "metric_raw_key", "localized_label", "metric_localized_label", "metric", "metric_name"):
            text = str(item.get(key) or "").strip()
            if text:
                names.add(text)
    if names:
        return names
    metric_inventory = _read_manifest_artifact(data_manifest, "metric_inventory")
    for item in list(metric_inventory.get("metrics") or []):
        if not isinstance(item, dict):
            continue
        if not (item.get("is_derived") or str(item.get("metric_kind") or "") == "derived_metric"):
            continue
        for key in ("raw_key", "metric_raw_key", "localized_label", "metric_localized_label", "metric", "metric_name"):
            text = str(item.get(key) or "").strip()
            if text:
                names.add(text)
    return names


def _available_dimension_names(data_manifest: dict[str, Any]) -> set[str]:
    names = _as_name_set(data_manifest.get("used_dimension_names"))
    names.update(_as_name_set(data_manifest.get("dimension_names")))
    if names:
        return names
    data_profile = _read_manifest_artifact(data_manifest, "data_profile")
    for item in list(data_profile.get("main_business_objects") or []):
        if not isinstance(item, dict):
            continue
        for key in ("raw_key", "localized_label", "dimension_raw_key", "dimension_localized_label"):
            text = str(item.get(key) or "").strip()
            if text:
                names.add(text)
    cube = _read_manifest_artifact(data_manifest, "dimension_metric_cube")
    for item in list(cube.get("cube") or []):
        if not isinstance(item, dict):
            continue
        for key in ("dimension_raw_key", "dimension_localized_label"):
            text = str(item.get(key) or "").strip()
            if text:
                names.add(text)
    return names


def _collect_metric_names_from_insight(value: Any) -> set[str]:
    names: set[str] = set()
    if isinstance(value, dict):
        for key in (
            "metric",
            "metric_name",
            "metric_key",
            "metric_raw_key",
            "raw_key",
            "left",
            "right",
            "left_metric",
            "right_metric",
            "x_label",
            "y_label",
            "x_metric",
            "y_metric",
            "measure",
            "value_column",
        ):
            text = str(value.get(key) or "").strip()
            if text:
                names.add(text)
        for key in ("metrics", "metric_names", "source_metric_names", "used_metric_names"):
            names.update(_as_name_set(value.get(key)))
        text = str(value.get("name") or "").strip()
        if text and any(key in value for key in ("metric_type", "aggregation", "sum", "mean")):
            names.add(text)
        for key in ("x_metric", "y_metric"):
            nested = value.get(key)
            if isinstance(nested, dict):
                text = str(nested.get("name") or "").strip()
                if text:
                    names.add(text)
        for nested in value.values():
            names.update(_collect_metric_names_from_insight(nested))
    elif isinstance(value, list):
        for item in value:
            names.update(_collect_metric_names_from_insight(item))
    return names


def _collect_dimension_names_from_insight(value: Any) -> set[str]:
    names: set[str] = set()
    if isinstance(value, dict):
        for key in (
            "dimension",
            "dimension_name",
            "dimension_raw_key",
            "group_column",
            "label_dimension",
            "segment_dimension",
            "category_column",
        ):
            text = str(value.get(key) or "").strip()
            if text:
                names.add(text)
        for key in ("dimensions", "dimension_names", "source_dimension_names", "used_dimension_names"):
            names.update(_as_name_set(value.get(key)))
        for nested in value.values():
            names.update(_collect_dimension_names_from_insight(nested))
    elif isinstance(value, list):
        for item in value:
            names.update(_collect_dimension_names_from_insight(item))
    return names


def _data_coverage_summary(
    pages: list[dict[str, Any]],
    assets_by_type: dict[str, list[dict[str, Any]]],
    data_manifest: dict[str, Any],
) -> dict[str, Any]:
    available_metrics = _available_metric_names(data_manifest)
    available_derived_metrics = _available_derived_metric_names(data_manifest)
    available_dimensions = _available_dimension_names(data_manifest)
    used_metrics: set[str] = set()
    used_dimensions: set[str] = set()
    for page in pages:
        for asset in list(page.get("asset_refs") or []):
            if not isinstance(asset, dict):
                continue
            insight = asset.get("insight_input") or {}
            used_metrics.update(_collect_metric_names_from_insight(insight))
            used_dimensions.update(_collect_dimension_names_from_insight(insight))
            used_metrics.update(_asset_metric_names(asset))
            used_dimensions.update(_asset_dimension_names(asset))
    if available_metrics:
        used_metrics = {name for name in used_metrics if name in available_metrics}
    used_derived_metrics = used_metrics & available_derived_metrics
    if available_dimensions:
        used_dimensions = {name for name in used_dimensions if name in available_dimensions}
    metric_target_count = int(data_manifest.get("metric_count") or len(available_metrics))
    derived_metric_target_count = int(data_manifest.get("derived_metric_count") or len(available_derived_metrics))
    dimension_target_count = int(data_manifest.get("dimension_count") or len(available_dimensions))
    metric_ratio = round(min(1.0, len(used_metrics) / max(1, metric_target_count)), 4) if available_metrics else 0
    derived_metric_ratio = (
        round(min(1.0, len(used_derived_metrics) / max(1, derived_metric_target_count)), 4)
        if available_derived_metrics
        else 0
    )
    dimension_ratio = round(min(1.0, len(used_dimensions) / max(1, dimension_target_count)), 4) if available_dimensions else 0
    asset_usage = _asset_usage_summary(pages, assets_by_type)
    chart_ratio = float((asset_usage.get("chart") or {}).get("coverage_ratio") or 0)
    table_ratio = float((asset_usage.get("table") or {}).get("coverage_ratio") or 0)
    metric_component = metric_ratio * (0.25 if available_derived_metrics else 0.4)
    derived_component = derived_metric_ratio * 0.2 if available_derived_metrics else 0
    asset_component_weight = 0.2 if available_derived_metrics else 0.25
    score = round(
        min(
            1.0,
            metric_component
            + derived_component
            + dimension_ratio * 0.35
            + min(1.0, (chart_ratio + table_ratio) / 2) * asset_component_weight,
        ),
        4,
    )
    return {
        "data_coverage_score": score,
        "available_metric_count": metric_target_count,
        "available_derived_metric_count": derived_metric_target_count,
        "available_dimension_count": dimension_target_count,
        "used_metric_count": len(used_metrics),
        "used_derived_metric_count": len(used_derived_metrics),
        "used_dimension_count": len(used_dimensions),
        "metric_coverage_ratio": metric_ratio,
        "derived_metric_coverage_ratio": derived_metric_ratio,
        "dimension_coverage_ratio": dimension_ratio,
        "used_metric_names": sorted(used_metrics),
        "used_derived_metric_names": sorted(used_derived_metrics),
        "used_dimension_names": sorted(used_dimensions),
    }


def _asset_metric_names(asset: dict[str, Any]) -> set[str]:
    names = _collect_metric_names_from_insight(asset.get("insight_input") or {})
    names.update(_as_name_set(asset.get("source_metric_names")))
    names.update(_as_name_set(asset.get("used_metric_names")))
    return names


def _asset_dimension_names(asset: dict[str, Any]) -> set[str]:
    names = _collect_dimension_names_from_insight(asset.get("insight_input") or {})
    names.update(_as_name_set(asset.get("source_dimension_names")))
    names.update(_as_name_set(asset.get("used_dimension_names")))
    return names


def _append_data_coverage_pages(
    pages: list[dict[str, Any]],
    *,
    assets_by_type: dict[str, list[dict[str, Any]]],
    data_manifest: dict[str, Any],
) -> None:
    available_metrics = _available_metric_names(data_manifest)
    available_derived_metrics = _available_derived_metric_names(data_manifest)
    available_dimensions = _available_dimension_names(data_manifest)
    if not available_metrics and not available_dimensions:
        return
    metric_target_count = int(data_manifest.get("metric_count") or len(available_metrics))
    derived_metric_target_count = int(data_manifest.get("derived_metric_count") or len(available_derived_metrics))
    dimension_target_count = int(data_manifest.get("dimension_count") or len(available_dimensions))
    min_metric_count = min(metric_target_count, 6 if metric_target_count >= 8 else metric_target_count)
    min_derived_metric_count = min(derived_metric_target_count, 3)
    min_dimension_count = min(dimension_target_count, 3 if dimension_target_count >= 4 else dimension_target_count)
    used_keys = {
        _asset_key(asset)
        for page in pages
        for asset in list(page.get("asset_refs") or [])
        if isinstance(asset, dict)
    }
    candidates: list[tuple[int, str, dict[str, Any]]] = []
    for asset_type in ("chart", "table", "collage"):
        for asset in list(assets_by_type.get(asset_type) or []):
            key = _asset_key(asset)
            if key and key in used_keys:
                continue
            metric_names = _asset_metric_names(asset) & available_metrics
            derived_metric_names = metric_names & available_derived_metrics
            dimension_names = _asset_dimension_names(asset) & available_dimensions
            if not metric_names and not dimension_names:
                continue
            score = len(metric_names) * 2 + len(derived_metric_names) * 4 + len(dimension_names) * 3
            if asset_type == "chart":
                score += 2
            elif asset_type == "table":
                score += 1
            candidates.append((score, asset_type, asset))
    candidates.sort(key=lambda item: item[0], reverse=True)

    def _current_coverage() -> dict[str, Any]:
        return _data_coverage_summary(pages, assets_by_type, data_manifest)

    coverage = _current_coverage()
    for _score, asset_type, asset in candidates:
        if (
            int(coverage.get("used_metric_count") or 0) >= min_metric_count
            and int(coverage.get("used_derived_metric_count") or 0) >= min_derived_metric_count
            and int(coverage.get("used_dimension_count") or 0) >= min_dimension_count
            and float(coverage.get("data_coverage_score") or 0) >= 0.7
        ):
            break
        key = _asset_key(asset)
        if key and key in used_keys:
            continue
        if asset_type == "chart":
            template_type = _template_for_chart_asset(asset)
            module = "Data coverage visuals"
            conclusion_type = "data_coverage_chart"
        elif asset_type == "table":
            template_type = _template_for_table_asset(asset)
            module = "Data coverage detail"
            conclusion_type = "data_coverage_table"
        else:
            template_type = _template_for_collage_asset(asset)
            module = "Data coverage synthesis"
            conclusion_type = "data_coverage_collage"
        pages.append(
            {
                "page_number": len(pages) + 1,
                "page_template_type": template_type,
                "module": module,
                "title": _clean_text(asset.get("title"), fallback="Data Coverage Page"),
                "density_class": "dense" if asset_type == "table" else "visual",
                "expected_conclusion_type": conclusion_type,
                "asset_refs": [asset],
                "reader_facing": asset_type != "table",
                "auto_added_reason": "data_coverage_gap",
            }
        )
        if key:
            used_keys.add(key)
        coverage = _current_coverage()


def _report_logic_coverage_summary(pages: list[dict[str, Any]]) -> dict[str, Any]:
    required_roles = [
        "opening_thesis",
        "diagnostic_evidence",
        "contrast_or_segmentation",
        "management_implication",
        "recommendation",
        "appendix_support",
    ]
    role_counts: dict[str, int] = {}
    claim_evidence_action_pages = 0
    pages_with_evidence = 0
    pages_with_action = 0
    for page in pages:
        role = str(page.get("logic_role") or "").strip()
        if role:
            role_counts[role] = role_counts.get(role, 0) + 1
        chain = page.get("claim_evidence_action")
        if isinstance(chain, dict):
            if chain.get("claim_seed") or chain.get("page_claim_seed"):
                claim_evidence_action_pages += 1
            if chain.get("evidence_seeds") or chain.get("evidence_source_seed"):
                pages_with_evidence += 1
            if chain.get("action_seed") or chain.get("action_role") == "explicit_action_or_implication":
                pages_with_action += 1
    present_roles = [role for role in required_roles if role_counts.get(role, 0) > 0]
    role_score = len(present_roles) / max(1, len(required_roles))
    chain_score = claim_evidence_action_pages / max(1, len(pages))
    evidence_score = pages_with_evidence / max(1, len([page for page in pages if str(page.get("page_template_type") or "") not in {"cover_page", "toc_navigation_page", "module_divider_page"}]))
    action_score = min(1.0, pages_with_action / max(1, int(len(pages) * 0.25)))
    return {
        "required_logic_roles": required_roles,
        "present_logic_roles": present_roles,
        "missing_logic_roles": [role for role in required_roles if role not in present_roles],
        "logic_role_counts": role_counts,
        "claim_evidence_action_page_count": claim_evidence_action_pages,
        "pages_with_evidence_count": pages_with_evidence,
        "pages_with_action_count": pages_with_action,
        "logic_role_coverage_score": round(min(1.0, role_score * 0.4 + chain_score * 0.25 + evidence_score * 0.2 + action_score * 0.15), 4),
    }


def _quality_metrics(
    pages: list[dict[str, Any]],
    template_counts: dict[str, int],
    assets_by_type: dict[str, list[dict[str, Any]]],
    family: str,
    data_manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    required = [
        "cover_page",
        "toc_navigation_page",
        "module_divider_page",
        "thesis_chart_page",
        "summary_map_page",
        "comparison_matrix_page",
        "ranking_table_page",
    ]
    present = [template for template in required if int(template_counts.get(template) or 0) > 0]
    visual_pages = sum(1 for page in pages if _page_has_asset_type(page, "chart") or _page_has_asset_type(page, "collage"))
    dense_pages = sum(1 for page in pages if _page_has_asset_type(page, "table"))
    harmony_tagged_pages = sum(1 for page in pages if isinstance(page.get("layout_harmony"), dict))
    return {
        "required_template_coverage": {
            "required": required,
            "present": present,
            "missing": [template for template in required if template not in present],
            "coverage_ratio": round(len(present) / max(1, len(required)), 4),
        },
        "visual_page_count": visual_pages,
        "table_page_count": dense_pages,
        "asset_usage_summary": _asset_usage_summary(pages, assets_by_type),
        "visual_density_ratio": round(visual_pages / max(1, len(pages)), 4),
        "table_density_ratio": round(dense_pages / max(1, len(pages)), 4),
        "layout_harmony_coverage_ratio": round(harmony_tagged_pages / max(1, len(pages)), 4),
        "data_coverage": _data_coverage_summary(pages, assets_by_type, dict(data_manifest or {})),
        "report_logic": _report_logic_coverage_summary(pages),
    }


def _visual_contract_payload(workspace: Path) -> dict[str, Any]:
    visual_reference = _read_json(workspace / "historical_visual_reference.json")
    contract = visual_reference.get("style_transfer_contract")
    return contract if isinstance(contract, dict) else {}


def _visual_signature_payload(workspace: Path) -> dict[str, Any]:
    visual_reference = _read_json(workspace / "historical_visual_reference.json")
    signature = visual_reference.get("visual_style_signature")
    return signature if isinstance(signature, dict) else {}


def _layout_harmony_payload(contract: dict[str, Any]) -> dict[str, Any]:
    harmony = contract.get("layout_harmony")
    if not isinstance(harmony, dict):
        harmony = {}
    return {
        "available": bool(harmony.get("available")),
        "version": str(harmony.get("version") or "layout-harmony-unavailable"),
        "balance_mode": str(harmony.get("balance_mode") or "balanced_exhibit"),
        "density_mode": str(harmony.get("density_mode") or "moderate"),
        "margin_mode": str(harmony.get("margin_mode") or "standard"),
        "recommended_content_columns": int(harmony.get("recommended_content_columns") or 1),
        "recommended_visual_text_ratio": float(harmony.get("recommended_visual_text_ratio") or 0.58),
        "recommended_section_gap_ratio": float(harmony.get("recommended_section_gap_ratio") or 0.025),
        "recommended_page_grid": str(harmony.get("recommended_page_grid") or ""),
        "harmony_rules": [str(item) for item in list(harmony.get("harmony_rules") or []) if str(item).strip()],
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


def _profile_regions(profile: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": _norm_box(profile.get("title_box_norm")),
        "primary_visual": _norm_box(profile.get("primary_visual_box_norm")),
        "right_annotation": _norm_box(profile.get("right_annotation_box_norm")),
        "narrative": _norm_box(profile.get("narrative_box_norm")),
        "footer": _norm_box(profile.get("footer_box_norm")),
        "source_page_template_index": int(profile.get("source_page_number") or 0),
    }


def _right_region_is_numeric_chart_column(profile: dict[str, Any]) -> bool:
    primitives = profile.get("detected_visual_primitives")
    primitives = primitives if isinstance(primitives, dict) else {}
    right_numeric = float(primitives.get("right_numeric_column_likelihood") or 0)
    right_box = _norm_box(profile.get("right_annotation_box_norm"))
    visual_box = _norm_box(profile.get("primary_visual_box_norm"))
    narrative_box = _norm_box(profile.get("narrative_box_norm"))
    if right_numeric < 0.45 or not right_box or not visual_box or not narrative_box:
        return False
    overlaps_visual_y = right_box[1] >= visual_box[1] - 0.04 and right_box[3] <= visual_box[3] + 0.06
    narrative_height = max(0.0, narrative_box[3] - narrative_box[1])
    return overlaps_visual_y and narrative_height >= 0.12


def _profile_prefers_narrative_above_visual(profile: dict[str, Any]) -> bool:
    visual_box = _norm_box(profile.get("primary_visual_box_norm"))
    title_box = _norm_box(profile.get("title_box_norm"))
    if not visual_box or not title_box:
        return False
    title_gap = max(0.0, visual_box[1] - title_box[3])
    visual_height = max(0.0, visual_box[3] - visual_box[1])
    # Some consulting pages place two-column narrative above the exhibit. The
    # visual parser may still label the below-chart notes as "narrative", so
    # use the visual start and title gap as the source of truth.
    return visual_box[1] >= 0.27 and title_gap >= 0.13 and visual_height <= 0.46


def _desired_region_mode(page: dict[str, Any]) -> str:
    template = str(page.get("page_template_type") or "")
    if template in {"ranking_table_page", "comparison_matrix_page", "appendix_detail_table_page", "appendix_glossary_page", "kpi_scorecard_page"}:
        return "table_dense"
    if template in {"summary_map_page", "collage_preference_page", "toc_navigation_page", "module_divider_page"}:
        return "collage_grid"
    if template == "cover_page":
        return "visual_only"
    return "visual_with_right_annotation"


def _match_region_profile(
    page: dict[str, Any],
    profiles: list[dict[str, Any]],
    profile_usage: dict[int, int] | None = None,
) -> tuple[dict[str, Any], str, str]:
    desired = _desired_region_mode(page)
    if not profiles:
        return {}, "missing_source_region_profile_pack", desired
    template = str(page.get("page_template_type") or "")
    page_number = int(page.get("page_number") or 1)
    best_profile: dict[str, Any] = profiles[0]
    best_score = -1.0
    best_reason = "nearest-region-profile"
    for profile in profiles:
        modes = {str(item) for item in list(profile.get("allowed_renderer_modes") or [])}
        role = str(profile.get("dominant_page_role_guess") or "")
        source_page = int(profile.get("source_page_number") or 0)
        usage_count = int((profile_usage or {}).get(source_page, 0))
        score = 0.0
        reasons: list[str] = []
        if desired in modes:
            score += 5.0
            reasons.append(f"mode:{desired}")
        if desired == "table_dense" and ("table" in role or str(profile.get("density_class") or "") == "dense"):
            score += 4.0
            reasons.append("table-density")
        if desired == "table_dense":
            visual_area = float(profile.get("visual_area_ratio") or 0)
            if visual_area >= 0.5:
                score += 2.2
                reasons.append("large-table-visual-area")
            elif visual_area >= 0.4:
                score += 1.1
                reasons.append("medium-table-visual-area")
            elif visual_area < 0.34:
                score -= 2.4
                reasons.append("avoid-small-table-visual-area")
        if desired == "visual_with_right_annotation" and float(profile.get("right_annotation_width_ratio") or 0) >= 0.12:
            score += 4.0
            reasons.append("right-note")
        if template == "cover_page" and source_page == 1:
            score += 6.0
            reasons.append("cover")
        score += max(0.0, 2.0 - abs((source_page or page_number) - page_number) * 0.25)
        if source_page and profiles:
            source_cycle = ((max(1, page_number) - 1) % max(1, len(profiles))) + 1
            if source_page == source_cycle:
                score += 0.9
                reasons.append("source-cycle-balance")
        score -= usage_count * 1.8
        score += min(1.5, float(profile.get("visual_area_ratio") or 0) * 2.5)
        if score > best_score:
            best_score = score
            best_profile = profile
            best_reason = ", ".join(reasons) or "nearest-region-profile"
    mode = desired if desired in {str(item) for item in list(best_profile.get("allowed_renderer_modes") or [])} else str((best_profile.get("allowed_renderer_modes") or [desired])[0])
    if (
        desired in {"visual_with_right_annotation", "visual_with_right_delta"}
        and _profile_prefers_narrative_above_visual(best_profile)
    ):
        mode = "narrative_above_visual"
        best_reason = f"{best_reason}, source-narrative-above-visual"
    elif desired in {"visual_with_right_annotation", "visual_with_right_delta"} and _right_region_is_numeric_chart_column(best_profile):
        mode = "visual_then_lower_narrative"
        best_reason = f"{best_reason}, right-numeric-column-not-reader-annotation"
    elif desired == "table_dense" and float(best_profile.get("right_annotation_width_ratio") or 0) >= 0.12:
        mode = "visual_with_right_annotation"
        best_reason = f"{best_reason}, table-uses-source-right-column-for-reader-notes"
    elif float(best_profile.get("right_annotation_width_ratio") or 0) >= 0.12 and desired != "visual_only":
        mode = "visual_with_right_annotation"
    return best_profile, best_reason, mode


def _region_contract_for_page(
    page: dict[str, Any],
    profiles: list[dict[str, Any]],
    profile_usage: dict[int, int] | None = None,
) -> dict[str, Any]:
    existing = page.get("region_layout_contract")
    if not profiles and isinstance(existing, dict) and isinstance(existing.get("layout_regions"), dict):
        if float(existing.get("right_annotation_width_ratio") or 0) >= 0.12 and str(existing.get("visual_region_mode") or "") not in {"visual_only", "visual_with_right_annotation", "visual_with_right_delta", "visual_then_lower_narrative", "narrative_above_visual"}:
            existing = {**existing, "visual_region_mode": "visual_with_right_annotation"}
        return existing
    profile, reason, mode = _match_region_profile(page, profiles, profile_usage=profile_usage)
    if not profile:
        return {
            "layout_regions": page.get("layout_regions") if isinstance(page.get("layout_regions"), dict) else {},
            "visual_region_mode": mode,
            "match_reason": reason,
        }
    binding = page.get("visual_asset_binding") if isinstance(page.get("visual_asset_binding"), dict) else {}
    if (
        str(binding.get("primary_asset_type") or "").strip().lower() in {"table", "collage"}
        and mode == "visual_then_lower_narrative"
        and float(profile.get("right_annotation_width_ratio") or 0) >= 0.12
    ):
        mode = "visual_with_right_annotation"
        reason = f"{reason}, bound-asset-uses-right-reader-column"
    return {
        "source_region_profile_id": str(profile.get("source_region_profile_id") or ""),
        "source_page_number": int(profile.get("source_page_number") or 0),
        "layout_regions": _profile_regions(profile),
        "visual_region_mode": mode,
        "page_aspect": float(profile.get("page_aspect") or 0),
        "right_annotation_width_ratio": float(profile.get("right_annotation_width_ratio") or 0),
        "visual_area_ratio": float(profile.get("visual_area_ratio") or 0),
        "title_to_visual_gap": float(profile.get("title_to_visual_gap") or 0),
        "visual_to_narrative_gap": float(profile.get("visual_to_narrative_gap") or 0),
        "footer_height_ratio": float(profile.get("footer_height_ratio") or 0),
        "density_class": str(profile.get("density_class") or ""),
        "match_reason": reason,
    }


def _apply_region_contracts_to_pages(pages: list[dict[str, Any]], *, workspace: Path) -> dict[str, Any]:
    pack = _read_json(workspace / "historical_source_region_profile_pack.json")
    profiles = [profile for profile in list(pack.get("profiles") or []) if isinstance(profile, dict)]
    mode_counts: dict[str, int] = {}
    matched_pages: list[int] = []
    profile_usage: dict[int, int] = {}
    for page in pages:
        contract = _region_contract_for_page(page, profiles, profile_usage=profile_usage)
        page["region_layout_contract"] = contract
        page["layout_regions"] = contract.get("layout_regions") if isinstance(contract.get("layout_regions"), dict) else dict(page.get("layout_regions") or {})
        page["source_region_profile_id"] = str(contract.get("source_region_profile_id") or page.get("source_region_profile_id") or "")
        page["source_page_match_reason"] = str(contract.get("match_reason") or page.get("source_page_match_reason") or "")
        page["visual_region_mode"] = str(contract.get("visual_region_mode") or page.get("visual_region_mode") or _desired_region_mode(page))
        if page["source_region_profile_id"]:
            matched_pages.append(int(page.get("page_number") or 0))
        source_page_number = int(contract.get("source_page_number") or 0)
        if source_page_number > 0:
            profile_usage[source_page_number] = profile_usage.get(source_page_number, 0) + 1
        mode_counts[page["visual_region_mode"]] = mode_counts.get(page["visual_region_mode"], 0) + 1
    return {
        "path": str((workspace / "historical_source_region_profile_pack.json").resolve()),
        "profile_count": len(profiles),
        "matched_page_numbers": [page for page in matched_pages if page > 0],
        "per_page_region_mode_counts": mode_counts,
    }


def _apply_layout_harmony_to_pages(pages: list[dict[str, Any]], harmony: dict[str, Any]) -> None:
    if not pages:
        return
    balance_mode = str(harmony.get("balance_mode") or "balanced_exhibit")
    density_mode = str(harmony.get("density_mode") or "moderate")
    content_columns = int(harmony.get("recommended_content_columns") or 1)
    visual_text_ratio = float(harmony.get("recommended_visual_text_ratio") or 0.58)
    section_gap_ratio = float(harmony.get("recommended_section_gap_ratio") or 0.025)
    for page in pages:
        template = str(page.get("page_template_type") or "")
        if template in {"cover_page", "toc_navigation_page", "module_divider_page"}:
            page_density = "navigation"
        elif template in {"appendix_detail_table_page", "ranking_table_page", "kpi_scorecard_page"} and density_mode != "sparse":
            page_density = "dense"
        elif template in {"thesis_chart_page", "scatter_diagnosis_page", "heatmap_leverage_page", "funnel_diagnosis_page"}:
            page_density = "visual"
        else:
            page_density = str(page.get("density_class") or "standard")
        page["density_class"] = page_density
        page["layout_harmony"] = {
            "balance_mode": balance_mode,
            "density_mode": density_mode,
            "content_columns": content_columns,
            "visual_text_ratio": round(max(0.42, min(0.76, visual_text_ratio)), 4),
            "section_gap_ratio": round(max(0.012, min(0.055, section_gap_ratio)), 4),
            "recommended_page_grid": harmony.get("recommended_page_grid") or "",
            "harmony_rules": list(harmony.get("harmony_rules") or []),
        }
        if template in {"thesis_chart_page", "comparison_matrix_page", "kpi_scorecard_page"}:
            page["layout_balance_mode"] = balance_mode
            page["layout_density_mode"] = density_mode


def _contract_target_bounds(contract: dict[str, Any]) -> tuple[int, int]:
    layout = dict(contract.get("layout") or {})
    target = dict(layout.get("target_pages") or {})
    min_pages = int(target.get("min") or 0)
    max_pages = int(target.get("max") or 0)
    if min_pages <= 0 and max_pages <= 0:
        return 0, 0
    if max_pages and min_pages > max_pages:
        min_pages = max_pages
    return min_pages, max_pages


def _page_priority_for_visual_contract(page: dict[str, Any]) -> int:
    template = str(page.get("page_template_type") or "")
    score = 0
    if template == "cover_page":
        score += 1000
    elif template == "toc_navigation_page":
        score += 950
    elif template in {"thesis_chart_page", "scatter_diagnosis_page", "heatmap_leverage_page", "funnel_diagnosis_page"}:
        score += 820
    elif template in {"comparison_matrix_page", "kpi_scorecard_page", "ranking_table_page"}:
        score += 760
    elif template == "summary_map_page":
        score += 720
    elif template in {"appendix_detail_table_page", "appendix_glossary_page"}:
        score += 520
    elif template == "module_divider_page":
        score += 430
    if _page_has_asset_type(page, "chart"):
        score += 70
    if _page_has_asset_type(page, "table"):
        score += 55
    if _page_has_asset_type(page, "collage"):
        score += 35
    for asset in list(page.get("asset_refs") or []):
        if isinstance(asset, dict):
            score += min(120, _asset_data_richness(asset) * 12)
    if str(page.get("auto_added_reason") or "") == "data_coverage_gap":
        score += 120
    return score


def _page_metric_names(page: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    for asset in list(page.get("asset_refs") or []):
        if isinstance(asset, dict):
            names.update(_asset_metric_names(asset))
    return names


def _page_dimension_names(page: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    for asset in list(page.get("asset_refs") or []):
        if isinstance(asset, dict):
            names.update(_asset_dimension_names(asset))
    return names


def _apply_visual_contract_page_bounds(
    pages: list[dict[str, Any]],
    *,
    contract: dict[str, Any],
) -> list[dict[str, Any]]:
    min_pages, max_pages = _contract_target_bounds(contract)
    if max_pages <= 0 or len(pages) <= max_pages:
        return pages
    # Compact real short-form PDF references by keeping the strongest
    # evidence-bearing pages instead of blindly preserving every generated asset.
    selected: list[dict[str, Any]] = []
    seen_ids: set[int] = set()
    for template in ("cover_page", "toc_navigation_page"):
        for index, page in enumerate(pages):
            if index in seen_ids:
                continue
            if str(page.get("page_template_type") or "") == template:
                selected.append(page)
                seen_ids.add(index)
                break
    required_groups = [
        {"thesis_chart_page", "scatter_diagnosis_page", "heatmap_leverage_page", "funnel_diagnosis_page"},
        {"comparison_matrix_page", "kpi_scorecard_page", "ranking_table_page"},
        {"summary_map_page", "collage_preference_page"},
    ]
    for group in required_groups:
        if len(selected) >= max_pages:
            break
        best: tuple[int, int, dict[str, Any]] | None = None
        for index, page in enumerate(pages):
            if index in seen_ids:
                continue
            if str(page.get("page_template_type") or "") not in group:
                continue
            score = _page_priority_for_visual_contract(page)
            if best is None or score > best[0]:
                best = (score, index, page)
        if best is not None:
            _score, index, page = best
            selected.append(page)
            seen_ids.add(index)
    remaining = [(index, page) for index, page in enumerate(pages) if index not in seen_ids]
    while remaining and len(selected) < max_pages:
        used_metrics: set[str] = set()
        used_dimensions: set[str] = set()
        for page in selected:
            used_metrics.update(_page_metric_names(page))
            used_dimensions.update(_page_dimension_names(page))
        best_position = 0
        best_score = -1
        for position, (index, page) in enumerate(remaining):
            new_metrics = _page_metric_names(page) - used_metrics
            new_dimensions = _page_dimension_names(page) - used_dimensions
            coverage_score = len(new_metrics) * 190 + len(new_dimensions) * 230
            score = coverage_score + _page_priority_for_visual_contract(page)
            if score > best_score:
                best_score = score
                best_position = position
        index, page = remaining.pop(best_position)
        if len(selected) >= max_pages:
            break
        selected.append(page)
        seen_ids.add(index)
    selected.sort(key=lambda page: int(page.get("page_number") or 0))
    if min_pages and len(selected) < min_pages:
        for index, page in enumerate(pages):
            if index in seen_ids:
                continue
            selected.append(page)
            seen_ids.add(index)
            if len(selected) >= min_pages:
                break
    return selected


def render_historical_deck_layout_pack(
    *,
    workspace: Path,
    reverse_spec_path: Path,
    page_plan_path: Path,
    chart_assets_index_path: Path,
    table_assets_index_path: Path,
    collage_assets_index_path: Path,
    current_report_context_path: Path | None = None,
    data_asset_manifest_path: Path | None = None,
    data_storyline_scan_path: Path | None = None,
    page_blueprint_contract_path: Path | None = None,
    visual_asset_manifest_path: Path | None = None,
    index_name: str = "historical_deck_layout_pack.json",
) -> dict[str, Any]:
    reverse_spec = _read_json(reverse_spec_path)
    page_plan = _read_json(page_plan_path)
    logic_reference = _logic_reference_payload(workspace)
    context = _read_json(current_report_context_path) if current_report_context_path else {}
    data_manifest = _read_json(data_asset_manifest_path) if data_asset_manifest_path and data_asset_manifest_path.exists() else {}
    data_storyline_scan = _read_json(data_storyline_scan_path) if data_storyline_scan_path and data_storyline_scan_path.exists() else {}
    page_blueprint_contract = _read_json(page_blueprint_contract_path) if page_blueprint_contract_path and page_blueprint_contract_path.exists() else {}
    visual_asset_manifest = _read_json(visual_asset_manifest_path) if visual_asset_manifest_path and visual_asset_manifest_path.exists() else {}
    visual_contract = _visual_contract_payload(workspace)
    visual_signature = _visual_signature_payload(workspace)
    layout_harmony = _layout_harmony_payload(visual_contract)
    assets_by_type = {
        "chart": _read_assets(chart_assets_index_path, key="chart"),
        "table": _read_assets(table_assets_index_path, key="table"),
        "collage": _read_assets(collage_assets_index_path, key="collage"),
    }
    initial_blueprint_pages = [
        page for page in list(page_blueprint_contract.get("pages") or [])
        if isinstance(page, dict)
    ]

    sequence = _coerce_sequence(page_plan.get("page_type_sequence"))
    if not sequence:
        sequence = [
            {"page": 1, "page_template_type": "cover_page", "title": "报告封面"},
            {"page": 2, "page_template_type": "toc_navigation_page", "title": "阅读路径"},
            {"page": 3, "page_template_type": "summary_map_page", "title": "核心结论地图"},
        ]

    family = _family_from_reverse_spec(reverse_spec)
    pages: list[dict[str, Any]] = []
    for index, item in enumerate(sequence, start=1):
        blueprint_for_index = initial_blueprint_pages[index - 1] if index - 1 < len(initial_blueprint_pages) else {}
        template_type = _template_from_item(item)
        if template_type in {"toc_navigation_page", "module_divider_page"}:
            # Navigation-only pages were the main source of title + bullet
            # failures. Keep the logic role, but render it as a visual summary
            # page unless a later source-derived renderer supports a true
            # visual navigation component.
            template_type = "thesis_chart_page"
        title = _clean_text(
            item.get("title")
            or item.get("headline")
            or item.get("page_title")
            or item.get("name")
            or item.get("value"),
            fallback=f"第 {index} 页",
        )
        pages.append(
            {
                "page_number": index,
                "page_template_type": template_type,
                "module": _clean_text(item.get("module") or item.get("section"), fallback=""),
                "title": title,
                "density_class": _clean_text(item.get("density_class") or item.get("density"), fallback="standard"),
                "expected_conclusion_type": _clean_text(
                    item.get("expected_conclusion_type") or item.get("conclusion_type"),
                    fallback="management_thesis",
                ),
                "asset_refs": _pick_assets(template_type, assets_by_type, index, blueprint_for_index),
                "reader_facing": template_type not in {"appendix_glossary_page", "appendix_detail_table_page"},
                "storyline_source": _clean_text(item.get("primary_asset_source") or item.get("storyline_source"), fallback="page_plan"),
                "management_thesis": _clean_text(item.get("management_thesis"), fallback=_page_management_thesis(title, template_type)),
                "fallback_points_source": _clean_text(item.get("fallback_asset_source") or item.get("fallback_points_source"), fallback="deterministic_asset_fallback"),
                "primary_asset_role": "",
            }
        )
    _append_chart_pages_if_needed(
        pages,
        chart_assets=assets_by_type.get("chart", []),
    )
    _append_asset_pages_if_needed(
        pages,
        assets=assets_by_type.get("table", []),
        asset_type="table",
        target=min(len(assets_by_type.get("table", [])), 8),
        template_for_asset=_template_for_table_asset,
        module="数据明细",
        conclusion_type="table_driven_management_detail",
    )
    _append_asset_pages_if_needed(
        pages,
        assets=assets_by_type.get("collage", []),
        asset_type="collage",
        target=min(len(assets_by_type.get("collage", [])), 3),
        template_for_asset=_template_for_collage_asset,
        module="视觉综述",
        conclusion_type="collage_driven_storytelling",
    )
    _append_data_coverage_pages(
        pages,
        assets_by_type=assets_by_type,
        data_manifest=data_manifest,
    )
    pages = _apply_visual_contract_page_bounds(
        pages,
        contract=visual_contract,
    )
    _ensure_visual_asset_density_floor(
        pages,
        family="source_derived",
        assets_by_type=assets_by_type,
    )
    _ensure_recommendation_page(
        pages,
        assets_by_type=assets_by_type,
    )
    pages = _apply_visual_contract_page_bounds(
        pages,
        contract=visual_contract,
    )
    _apply_layout_harmony_to_pages(pages, layout_harmony)
    blueprint_pages = [
        page for page in list(page_blueprint_contract.get("pages") or [])
        if isinstance(page, dict)
    ]
    for index, page in enumerate(pages, start=1):
        blueprint = blueprint_pages[index - 1] if index - 1 < len(blueprint_pages) else {}
        if blueprint:
            page["page_blueprint"] = blueprint
            page["layout_regions"] = blueprint.get("layout_regions") if isinstance(blueprint.get("layout_regions"), dict) else {}
            page["source_region_profile_id"] = str(blueprint.get("source_region_profile_id") or "")
            page["source_page_match_reason"] = str(blueprint.get("source_page_match_reason") or "")
            page["visual_region_mode"] = str(blueprint.get("visual_region_mode") or "")
            page["region_layout_contract"] = blueprint.get("region_layout_contract") if isinstance(blueprint.get("region_layout_contract"), dict) else {}
            page["visual_grammar_id"] = str(blueprint.get("visual_grammar_id") or "")
            page["required_data_assets"] = blueprint.get("required_data_assets") if isinstance(blueprint.get("required_data_assets"), dict) else {}
            page["claim"] = str(blueprint.get("claim") or page.get("title") or "")
            page["evidence_refs"] = list(blueprint.get("evidence_refs") or [])
            page["action_implication"] = str(blueprint.get("action_implication") or page.get("management_thesis") or "")
            page["source_chart_grammar_profile_id"] = str(blueprint.get("source_chart_grammar_profile_id") or "")
            page["source_chart_match_reason"] = str(blueprint.get("source_chart_match_reason") or "")
            page["required_chart_kind"] = str(blueprint.get("required_chart_kind") or "")
            page["fallback_chart_kinds"] = list(blueprint.get("fallback_chart_kinds") or [])
            page["chart_similarity_contract"] = blueprint.get("chart_similarity_contract") if isinstance(blueprint.get("chart_similarity_contract"), dict) else {}
            page["source_chart_primitive_scores"] = blueprint.get("source_chart_primitive_scores") if isinstance(blueprint.get("source_chart_primitive_scores"), dict) else {}
    source_chart_profile_pack_payload = _read_json(workspace / "source_chart_grammar_profile_pack.json")
    source_chart_profiles = [
        profile for profile in list(source_chart_profile_pack_payload.get("profiles") or [])
        if isinstance(profile, dict)
    ]
    profiles_by_source_page = {
        int(profile.get("source_page_number") or 0): profile
        for profile in source_chart_profiles
        if int(profile.get("source_page_number") or 0) > 0
    }
    if source_chart_profiles:
        for page in pages:
            if str(page.get("page_template_type") or "") == "cover_page":
                continue
            if str(page.get("required_chart_kind") or "").strip():
                continue
            page_number = int(page.get("page_number") or 0)
            profile = profiles_by_source_page.get(page_number)
            if not profile:
                profile = source_chart_profiles[(max(1, page_number) - 1) % len(source_chart_profiles)]
            page["source_chart_grammar_profile_id"] = str(profile.get("source_chart_grammar_profile_id") or "")
            page["source_chart_match_reason"] = "source_chart_profile_cycle_when_blueprint_missing"
            page["required_chart_kind"] = str(profile.get("required_chart_kind") or profile.get("primary_chart_kind") or "")
            page["fallback_chart_kinds"] = list(profile.get("fallback_chart_kinds") or [])
            page["chart_similarity_contract"] = profile.get("chart_similarity_contract") if isinstance(profile.get("chart_similarity_contract"), dict) else {}
    _normalize_page_role_chart_contracts(pages)
    _rebind_pages_to_chart_grammar(pages, assets_by_type)
    visual_asset_binding_plan = _build_visual_asset_binding_plan(
        pages=pages,
        assets_by_type=assets_by_type,
        data_manifest=data_manifest,
        output_path=workspace / "visual_asset_binding_plan.json",
    )
    _apply_visual_asset_binding_plan(pages, assets_by_type, visual_asset_binding_plan)
    source_region_profile_pack_summary = _apply_region_contracts_to_pages(pages, workspace=workspace)
    _align_chart_profiles_to_region_profiles(pages, profiles_by_source_page)
    report_logic_contract = _apply_report_logic_to_pages(
        pages,
        reverse_spec=reverse_spec,
        logic_reference=logic_reference,
    )
    for index, page in enumerate(pages, start=1):
        page["page_number"] = index
        asset_refs = [asset for asset in list(page.get("asset_refs") or []) if isinstance(asset, dict)]
        primary_asset = asset_refs[0] if asset_refs else {}
        page["primary_asset_role"] = str(
            primary_asset.get("story_role")
            or primary_asset.get("recommended_page_role")
            or primary_asset.get("kind")
            or ""
        )
    reader_logic_rewrite = _apply_asset_based_reader_logic(pages)

    template_counts: dict[str, int] = {}
    for page in pages:
        template = str(page.get("page_template_type") or "")
        template_counts[template] = template_counts.get(template, 0) + 1

    payload = {
        "historical_report_family": family,
        "page_count": len(pages),
        "page_template_types": sorted(PAGE_TEMPLATE_TYPES),
        "template_counts": template_counts,
        "pages": pages,
        "quality_metrics": _quality_metrics(pages, template_counts, assets_by_type, family, data_manifest),
        "visual_style_signature": visual_signature,
        "style_transfer_contract": visual_contract,
        "layout_harmony": layout_harmony,
        "report_logic_contract": report_logic_contract,
        "reader_logic_rewrite": reader_logic_rewrite,
        "page_blueprint_contract": {
            "path": str(page_blueprint_contract_path.resolve()) if page_blueprint_contract_path else "",
            "page_count": int(page_blueprint_contract.get("page_count") or len(blueprint_pages)),
            "quality_contract": page_blueprint_contract.get("quality_contract") if isinstance(page_blueprint_contract.get("quality_contract"), dict) else {},
        },
        "source_region_profile_pack": source_region_profile_pack_summary,
        "source_chart_grammar_profile_pack": {
            "path": str((workspace / "source_chart_grammar_profile_pack.json").resolve()),
            "profile_count": int(source_chart_profile_pack_payload.get("profile_count") or 0),
            "required_chart_kind_counts": source_chart_profile_pack_payload.get("required_chart_kind_counts") if isinstance(source_chart_profile_pack_payload.get("required_chart_kind_counts"), dict) else {},
        },
        "visual_asset_binding_plan": {
            "path": str((workspace / "visual_asset_binding_plan.json").resolve()),
            "primary_asset_reuse_score": float(visual_asset_binding_plan.get("primary_asset_reuse_score") or 0),
            "chart_diversity_score": float(visual_asset_binding_plan.get("chart_diversity_score") or 0),
            "metric_dimension_coverage_score": float(visual_asset_binding_plan.get("metric_dimension_coverage_score") or 0),
            "layout_density_score": float(visual_asset_binding_plan.get("layout_density_score") or 0),
            "overused_asset_ids": list(visual_asset_binding_plan.get("overused_asset_ids") or []),
            "low_visual_density_page_numbers": list(visual_asset_binding_plan.get("low_visual_density_page_numbers") or []),
            "primary_asset_counts": dict(visual_asset_binding_plan.get("primary_asset_counts") or {}),
        },
        "visual_asset_manifest": {
            "path": str(visual_asset_manifest_path.resolve()) if visual_asset_manifest_path else "",
            "asset_counts": visual_asset_manifest.get("asset_counts") if isinstance(visual_asset_manifest.get("asset_counts"), dict) else {},
            "missing_primary_visual_page_numbers": list(visual_asset_manifest.get("missing_primary_visual_page_numbers") or []),
        },
        "asset_indexes": {
            "chart": str(chart_assets_index_path.resolve()),
            "table": str(table_assets_index_path.resolve()),
            "collage": str(collage_assets_index_path.resolve()),
        },
        "source_contract": {
            "reverse_spec": str(reverse_spec_path.resolve()),
            "page_plan": str(page_plan_path.resolve()),
            "current_report_context": str(current_report_context_path.resolve()) if current_report_context_path else "",
            "data_asset_manifest": str(data_asset_manifest_path.resolve()) if data_asset_manifest_path else "",
            "data_storyline_scan": str(data_storyline_scan_path.resolve()) if data_storyline_scan_path else "",
        },
        "data_storyline_scan_summary": {
            "headline_data_story": _clean_text(data_storyline_scan.get("headline_data_story")),
            "coverage_targets": data_storyline_scan.get("coverage_targets") if isinstance(data_storyline_scan.get("coverage_targets"), dict) else {},
        },
        "deck_goal": {
            "dataset_name": _clean_text(context.get("dataset_name")),
            "sheet_name": _clean_text(context.get("sheet_name")),
            "target_page_count_min": context.get("target_page_count_min"),
            "target_page_count_max": context.get("target_page_count_max"),
        },
    }
    index_path = workspace / index_name
    _write_json(index_path, payload)
    return {
        "index_path": str(index_path.resolve()),
        "historical_report_family": payload["historical_report_family"],
        "page_count": len(pages),
        "template_counts": template_counts,
        "quality_metrics": payload["quality_metrics"],
        "report_logic_contract": report_logic_contract,
        "pages": pages,
    }
