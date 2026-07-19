from __future__ import annotations

import re
from typing import Any


_PHRASE_MAP = {
    "Strategy consulting deck": "咨询式经营报告",
    "Historical-style runtime CLI package": "历史报告复刻运行包",
    "Historical Style Consulting Deck": "历史报告复刻咨询报告",
    "Historical Style Deck": "历史报告复刻报告",
    "historical_support_tables": "历史支持表",
    "visual synthesis": "视觉综合",
    "Signal Collage": "信号拼版",
    "historical PDF": "历史报告 PDF",
    "Metric & Dimension Glossary": "指标与维度口径表",
    "Appendix Detail Table": "附录明细表",
    "KPI Snapshot": "核心指标快照",
    "Dimension Signal Matrix": "维度信号矩阵",
    "Priority Action Table": "优先行动表",
    "Correlation Focus": "相关关系重点表",
    "Signal Tag Board": "信号标签板",
    "Segment Badge Board": "细分对象卡片",
    "Benchmark Callout Board": "对标提示板",
    "Executive Summary Map": "执行摘要地图",
    "Module Navigation Board": "模块导航板",
    "Action Roadmap Board": "行动路线图",
    "Gap Matrix Board": "差距矩阵",
    "Action Roadmap": "行动路线图",
    "Gap Matrix": "差距矩阵",
    "Module Navigation": "模块导航",
    "Value Bridge": "价值桥",
    "Priority Bubble Map": "优先级气泡图",
    "Pareto View": "帕累托视图",
    "Share Map": "份额图",
    "Top Pairs": "重点关系组合",
    "Quadrant Map": "象限图",
    "Portfolio Matrix": "组合矩阵",
    "Cumulative Curve": "累计曲线",
    "Contribution bridge to total": "总量贡献桥",
    "Sources": "来源",
    "Source": "来源",
    "Notes": "说明",
    "Note": "说明",
    "Appendix": "附录",
    "Exhibit": "图表",
    "REPORT": "报告",
    "high": "高优先级",
    "medium": "中优先级",
    "low": "低优先级",
}


_TOKEN_MAP = {
    "retail_format": "零售业态",
    "consumer_segment": "消费客群",
    "gross_sales": "销售额",
    "sales": "销售额",
    "net_revenue": "净收入",
    "revenue": "收入",
    "gross_margin": "毛利率",
    "margin": "毛利",
    "member_repeat_rate": "会员复购率",
    "repeat_purchase_rate": "复购率",
    "repeat_rate": "复购率",
    "service_satisfaction": "服务满意度",
    "service_level": "服务水平",
    "basket_value": "客单价",
    "discount_depth": "折扣深度",
    "conversion_rate": "转化率",
    "traffic_index": "流量指数",
    "inventory_turns": "库存周转",
    "refund_rate": "退款率",
    "order_count": "订单量",
    "column": "字段",
    "dtype": "类型",
    "missing_ratio": "缺失率",
    "unique_count": "唯一值数量",
    "source_dimension": "来源维度",
    "dimension": "维度",
    "rank": "排名",
    "segment": "分层",
    "signal_pack": "信号组合",
    "priority_zone": "优先区域",
    "current_signal": "当前信号",
    "management_question": "管理问题",
    "action_lens": "行动视角",
    "metric": "指标",
    "aggregation": "聚合方式",
    "value": "数值",
    "top_values": "高频值",
    "left": "左侧指标",
    "right": "右侧指标",
    "correlation": "相关系数",
    "abs_correlation": "相关强度",
    "analysis_module": "分析模块",
    "executive_signal": "高层信号",
    "style": "风格",
    "field": "字段",
    "category": "类别",
    "number": "数值",
    "snapshot": "快照",
    "sum": "合计",
    "mean": "均值",
    "marketplace": "平台",
    "direct": "直营",
    "wholesale": "批发",
    "social commerce": "社交电商",
    "retail partner": "零售伙伴",
    "east": "东区",
    "south": "南区",
    "north": "北区",
    "west": "西区",
    "value seekers": "价格敏感客群",
    "quality upgraders": "品质升级客群",
    "convenience driven": "便利驱动客群",
    "promotion sensitive": "促销敏感客群",
    "corporate_blue_white": "企业蓝白风格",
    "presentation_report": "演示型报告",
    "clean_module_layout": "清爽模块布局",
    "section_header_bar": "章节标题栏",
    "footer_source_plus_page_number": "来源页脚与页码",
    "source": "来源",
    "page": "页面",
    "pages": "页",
    "template": "页型",
    "chart": "图表",
    "table": "表格",
    "driver": "驱动因素",
    "analysis": "分析",
    "management": "管理",
    "module": "模块",
    "executive": "高层结论",
    "section": "章节",
    "priority": "优先级",
    "growth": "增长",
    "gap": "差距",
    "benchmark": "对标",
    "action": "行动",
    "score": "评分",
    "index": "指数",
}


_ACRONYM_KEEP = {"CEO", "COO", "CFO", "KPI", "SKU", "ROI", "GMV", "AOV", "RFM", "PDF", "CLI", "BCG"}
_MOJIBAKE_RE = re.compile(
    r"(?:锟|�|閿|鐨|涓|绋|瀹|姣|杞|澶|鏈|闁|閸|閻|粻|鐘|劕|鍣|"
    r"脙|脗|氓|莽|鍘|彶|鎶|憡|钀|鍛|勬|屽|粡|鏁|嵁|鎻|愭|丠|銆|Ã|Â|â€)"
)


def looks_like_mojibake(value: Any) -> bool:
    text = str(value or "")
    return bool(_MOJIBAKE_RE.search(text))


def _replace_case_insensitive(text: str, source: str, target: str) -> str:
    return re.sub(re.escape(source), target, text, flags=re.IGNORECASE)


def _humanize_snake_case(text: str) -> str:
    if "_" not in text:
        return text
    parts = [part for part in text.split("_") if part]
    translated = [_TOKEN_MAP.get(part.lower(), part) for part in parts]
    return "".join(translated)


def localize_historical_text(value: Any, *, fallback: str = "") -> str:
    """Localize deterministic historical-style deck labels into readable Chinese."""

    text = re.sub(r"\s+", " ", str(value or "").strip())
    if not text:
        return fallback
    localized = text
    for source, target in sorted(_PHRASE_MAP.items(), key=lambda item: len(item[0]), reverse=True):
        localized = _replace_case_insensitive(localized, source, target)
    for source, target in sorted(_TOKEN_MAP.items(), key=lambda item: len(item[0]), reverse=True):
        localized = _replace_case_insensitive(localized, source, target)

    def replace_unknown(match: re.Match[str]) -> str:
        token = match.group(0)
        if token.upper() in _ACRONYM_KEEP:
            return token.upper()
        if "_" in token:
            return _humanize_snake_case(token)
        return token

    localized = re.sub(r"\b[A-Za-z][A-Za-z0-9_]{2,}\b", replace_unknown, localized)
    localized = _MOJIBAKE_RE.sub("", localized)
    localized = re.sub(r"\s+", " ", localized).strip()
    return localized or fallback


def localize_historical_key(value: Any, *, fallback: str = "") -> str:
    return localize_historical_text(value, fallback=fallback)


def localize_historical_record(row: dict[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in row.items():
        localized_key = localize_historical_key(key, fallback=str(key))
        if isinstance(value, str):
            output[localized_key] = localize_historical_text(value)
        else:
            output[localized_key] = value
    return output
