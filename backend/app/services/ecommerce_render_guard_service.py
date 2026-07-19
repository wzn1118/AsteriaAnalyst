from __future__ import annotations

from typing import Any


ECOMMERCE_ENGINEERING_TERMS = (
    "registry",
    "guardrail",
    "schema",
    "validator",
    "raw_action",
    "debug",
    "workflow",
)

ECOMMERCE_WRONG_TITLES = (
    "互联网运营数据分析报告",
    "内容运营数据分析报告",
    "用户增长数据分析报告",
    "社区运营数据分析报告",
    "渠道投放与增长运营复盘报告",
)

ECOMMERCE_REQUIRED_ACTION_COLUMNS = {
    "优先级",
    "对象层级",
    "对象名称",
    "最终标签",
    "触发证据",
    "现有证据类型",
    "缺失字段",
    "被拦截动作",
    "最终动作",
    "负责人角色",
    "时间要求",
    "验证指标",
    "成功标准",
    "结论强度",
    "置信度",
}

ECOMMERCE_REQUIRED_7DAY_COLUMNS = {
    "优先级",
    "动作",
    "对象",
    "负责人角色",
    "输入数据",
    "产出结果",
    "截止时间",
    "验证标准",
    "护栏指标",
    "依赖字段",
    "当前结论强度",
}

ECOMMERCE_REQUIRED_BACKLOG_COLUMNS = {
    "实验编号",
    "实验假设",
    "目标对象",
    "实验动作",
    "核心指标",
    "护栏指标",
    "样本要求",
    "数据依赖",
    "预计周期",
    "成功标准",
    "失败后处理",
    "结论类型",
}

ECOMMERCE_REQUIRED_SECTIONS = [
    "ecommerce_cover",
    "ecommerce_management_summary",
    "ecommerce_data_scope",
    "ecommerce_can_and_cannot_judge",
    "ecommerce_object_grain",
    "ecommerce_kpi_tree",
    "ecommerce_overview",
    "ecommerce_gmv_order_mix",
    "ecommerce_product_structure",
    "ecommerce_core_product",
    "ecommerce_high_traffic_low_conversion",
    "ecommerce_high_sales_high_aftersales",
    "ecommerce_low_sales_high_inventory",
    "ecommerce_category_review",
    "ecommerce_shop_review",
    "ecommerce_brand_review",
    "ecommerce_price_promotion",
    "ecommerce_traffic_structure",
    "ecommerce_funnel",
    "ecommerce_cart_favorite_pay",
    "ecommerce_inventory",
    "ecommerce_inventory_gap",
    "ecommerce_fulfillment",
    "ecommerce_aftersales",
    "ecommerce_review",
    "ecommerce_bad_review",
    "ecommerce_margin_profit",
    "ecommerce_promotion_impact",
    "ecommerce_anomaly",
    "ecommerce_lifecycle",
    "ecommerce_management_diagnosis",
    "ecommerce_action_table",
    "ecommerce_7day_actions",
    "ecommerce_30day_backlog",
    "ecommerce_forbidden_judgement",
    "ecommerce_data_gap_priority",
    "ecommerce_roadmap",
    "ecommerce_appendix_note",
]

EcommerceForbiddenByMissingField = {
    "margin_cost_fields": ("利润高", "利润好", "ROI高", "成本效率高", "供应商利润贡献高", "值得加码"),
    "inventory_fields": ("补货", "清仓", "压货", "缺货", "库存周转慢", "库存健康"),
    "traffic_fields": ("曝光不足", "流量差", "点击不足", "商品承接差"),
    "conversion_fields": ("转化率低", "漏斗断点", "加购弱", "支付转化差"),
    "aftersales_fields": ("退款风险高", "退货风险高", "售后问题严重"),
    "review_fields": ("口碑好", "满意度高", "差评风险", "评价稳定"),
    "fulfillment_fields": ("履约差", "物流慢", "发货问题", "签收效率低"),
    "time_fields": ("增长", "下滑", "趋势", "环比", "同比", "波动"),
}


def _contains_any(text: str, terms: tuple[str, ...] | list[str]) -> bool:
    return any(term in text for term in terms)


def _has_safe_context(text: str, term: str) -> bool:
    lowered = str(text or "")
    index = lowered.find(term)
    while index >= 0:
        window = lowered[max(0, index - 24): index + len(term) + 24]
        if any(
            safe in window
            for safe in (
                "不能判断",
                "无法判断",
                "待补",
                "字段缺失",
                "后判断",
                "后复核",
                "只能做截面结构判断",
                "不能得出的结论",
            )
        ):
            return True
        index = lowered.find(term, index + len(term))
    return False


def ecommerce_field_boundary_errors(text: str, field_registry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for group_name, terms in EcommerceForbiddenByMissingField.items():
        if not field_registry.get(f"has_{group_name}", False):
            for term in terms:
                if term in text and not _has_safe_context(text, term):
                    errors.append(f"missing_{group_name}_but_found:{term}")
    return errors


def ecommerce_quality_gate(
    *,
    management_markdown: str,
    total_pages: int,
    business_profile: str,
    field_registry: dict[str, Any],
    action_rows: list[dict[str, Any]],
    seven_day_rows: list[dict[str, Any]],
    backlog_rows: list[dict[str, Any]],
    codex_call_count: int,
    section_ids: list[str] | None = None,
    router_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    text = str(management_markdown or "")
    fail_items: list[str] = []
    affected_sections: list[str] = []
    router_result = router_result or {}

    if str(business_profile or "") != "ecommerce_product_operations_report":
        fail_items.append("business_profile 不是 ecommerce_product_operations_report")
        affected_sections.append("management_report")

    if str(router_result.get("business_profile") or "") == "internet_operations_report":
        fail_items.append("电商商品数据被判为 internet_operations_report")
        affected_sections.append("business_profile_router")

    decisive_grain = str(router_result.get("decisive_object_grain") or "")
    if any(token in decisive_grain.lower() for token in ["item", "sku", "shop", "seller"]) and str(business_profile or "") != "ecommerce_product_operations_report":
        fail_items.append("核心对象为 item_id / sku_id / shop_id / seller_id，却未进入电商报告")
        affected_sections.append("business_profile_router")

    if not (35 <= total_pages <= 50):
        fail_items.append(f"management_report 页数不在 35-50 之间：{total_pages}")
        affected_sections.append("management_report")

    if codex_call_count < 8:
        fail_items.append(f"Codex/LLM 解读调用少于 8 轮：{codex_call_count}")
        affected_sections.append("ecommerce_codex_chain")

    if _contains_any(text, ECOMMERCE_WRONG_TITLES):
        fail_items.append("误套互联网运营报告标题")
        affected_sections.append("management_report")

    if _contains_any(text.lower(), ECOMMERCE_ENGINEERING_TERMS):
        fail_items.append("management_report 混入工程内部词")
        affected_sections.append("management_report")

    section_id_set = set(section_ids or [])
    for section in ECOMMERCE_REQUIRED_SECTIONS:
        if section not in section_id_set:
            fail_items.append(f"缺少必需章节：{section}")
            affected_sections.append("management_report")

    boundary_errors = ecommerce_field_boundary_errors(text, field_registry)
    if boundary_errors:
        fail_items.extend(boundary_errors)
        affected_sections.append("management_report")

    if not action_rows or not ECOMMERCE_REQUIRED_ACTION_COLUMNS.issubset(set(action_rows[0].keys())):
        fail_items.append("ecommerce_action_table 缺少负责人/时间/验证指标/成功标准等必需列")
        affected_sections.append("action_table")

    if not seven_day_rows or not ECOMMERCE_REQUIRED_7DAY_COLUMNS.issubset(set(seven_day_rows[0].keys())):
        fail_items.append("7_day_ecommerce_action_table 缺少必需列")
        affected_sections.append("7_day_ecommerce_action_table")

    if not backlog_rows or not ECOMMERCE_REQUIRED_BACKLOG_COLUMNS.issubset(set(backlog_rows[0].keys())):
        fail_items.append("30_day_ecommerce_experiment_backlog 缺少必需列")
        affected_sections.append("30_day_ecommerce_experiment_backlog")

    for row in action_rows:
        sample_flag = str(row.get("样本量标记") or row.get("sample_size_flag") or "")
        final_action = str(row.get("最终动作") or "")
        if "低样本" in sample_flag or "低样本" in str(row.get("最终标签") or ""):
            if any(term in final_action for term in ["加码", "主推", "补货", "清仓", "压货", "放量"]):
                fail_items.append(f"低样本对象出现强动作：{row.get('对象名称')}")
                affected_sections.append("action_table")
                break

    return {
        "passed": not fail_items,
        "business_profile": business_profile,
        "fail_items": fail_items,
        "affected_sections": sorted(set(affected_sections)),
        "suggested_fixes": [] if not fail_items else [
            "切回 ecommerce_product_operations_report_profile",
            "删除字段不支持的强结论并降级为 proxy_based_inference / business_hypothesis / risk_flag / data_required",
            "补齐 7 日动作表、30 日实验 backlog 和对象级行动表必需列",
            "必要时切换为极简高合规版电商报告",
        ],
    }


def ecommerce_report_quality_scorer(
    *,
    management_markdown: str,
    total_pages: int,
    business_profile: str,
    field_registry: dict[str, Any],
    action_rows: list[dict[str, Any]],
    seven_day_rows: list[dict[str, Any]],
    backlog_rows: list[dict[str, Any]],
    codex_call_count: int,
    gate_result: dict[str, Any],
    section_ids: list[str] | None = None,
    router_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    text = str(management_markdown or "")
    router_result = router_result or {}
    breakdown: dict[str, int] = {}
    hard_fail_items: list[str] = []

    profile_ok = (
        str(business_profile or "") == "ecommerce_product_operations_report"
        and str(router_result.get("business_profile") or business_profile) != "internet_operations_report"
        and not _contains_any(text, ECOMMERCE_WRONG_TITLES)
    )
    breakdown["business_profile_accuracy"] = 10 if profile_ok else 0
    if not profile_ok:
        hard_fail_items.append("业务类型识别错误")

    grain_ok = (
        "核心对象粒度识别" in text
        and all(token in text for token in ["商品", "SKU", "类目", "店铺", "品牌"])
    )
    breakdown["object_grain_accuracy"] = 10 if grain_ok else 4

    metric_coverage_count = sum(
        1
        for section_title in ["整体经营盘面", "价格带与促销分析", "流量结构分析", "商品转化漏斗分析", "库存与周转分析", "履约与物流分析", "售后退款退货分析", "评价与口碑分析", "毛利、成本与利润分析"]
        if section_title in text
    )
    breakdown["metric_coverage"] = 10 if metric_coverage_count >= 7 else 6 if metric_coverage_count >= 5 else 2

    field_boundary_ok = text.count("字段边界：") >= 30
    breakdown["field_boundary_clarity"] = 10 if field_boundary_ok else 4

    object_analysis_ok = bool(action_rows) and all(key in action_rows[0] for key in ["最终标签", "触发证据", "最终动作", "验证指标"])
    breakdown["object_level_analysis"] = 15 if object_analysis_ok else 5

    misjudgement_ok = not ecommerce_field_boundary_errors(text, field_registry)
    breakdown["misjudgement_control"] = 15 if misjudgement_ok else 0
    if not misjudgement_ok:
        hard_fail_items.append("字段不支持的强结论未被拦住")

    actionability_ok = (
        bool(action_rows)
        and ECOMMERCE_REQUIRED_ACTION_COLUMNS.issubset(set(action_rows[0].keys()))
        and bool(seven_day_rows)
        and ECOMMERCE_REQUIRED_7DAY_COLUMNS.issubset(set(seven_day_rows[0].keys()))
    )
    breakdown["actionability"] = 10 if actionability_ok else 0
    if not actionability_ok:
        hard_fail_items.append("行动可执行性字段不完整")

    roadmap_ok = (
        bool(seven_day_rows)
        and bool(backlog_rows)
        and ECOMMERCE_REQUIRED_7DAY_COLUMNS.issubset(set(seven_day_rows[0].keys()))
        and ECOMMERCE_REQUIRED_BACKLOG_COLUMNS.issubset(set(backlog_rows[0].keys()))
    )
    breakdown["roadmap_tables"] = 10 if roadmap_ok else 0

    pdf_ok = 35 <= total_pages <= 50 and all(section in set(section_ids or []) for section in ECOMMERCE_REQUIRED_SECTIONS)
    breakdown["pdf_completeness"] = 5 if pdf_ok else 0
    if not pdf_ok:
        hard_fail_items.append("PDF 页数或章节完整性不达标")

    readability_ok = len((text or "").split("管理层摘要")) > 1 and not _contains_any(text.lower(), ECOMMERCE_ENGINEERING_TERMS)
    breakdown["management_readability"] = 5 if readability_ok else 2

    score = sum(breakdown.values())
    if codex_call_count < 8:
        hard_fail_items.append("Codex/LLM 解读调用少于 8 轮")
    if hard_fail_items or not gate_result.get("passed", False):
        score = min(score, 89)

    return {
        "business_profile": business_profile,
        "score": score,
        "passed": score >= 90 and bool(gate_result.get("passed", False)),
        "breakdown": breakdown,
        "hard_fail_items": hard_fail_items,
    }
