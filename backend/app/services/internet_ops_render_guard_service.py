from __future__ import annotations

from typing import Any


INTERNET_OPS_ENGINEERING_TERMS = (
    "registry",
    "guardrail",
    "schema",
    "validator",
    "raw_action",
    "debug",
    "workflow",
)

INTERNET_OPS_PROCUREMENT_TERMS = (
    "采销",
    "SKU",
    "供应商",
    "库存",
    "采购价",
)

INTERNET_OPS_COST_FORBIDDEN = (
    "ROI",
    "CAC",
    "预算加码",
    "砍渠道",
    "加大投放",
    "规模化投放",
)

INTERNET_OPS_RETENTION_FORBIDDEN = (
    "用户质量高",
    "长期留存好",
    "用户黏性强",
    "长期价值高",
)

INTERNET_OPS_REVENUE_FORBIDDEN = (
    "商业价值高",
    "LTV高",
    "高价值用户",
    "值得规模化投放",
)

INTERNET_OPS_FUNNEL_FORBIDDEN = (
    "完整转化链路健康",
    "漏斗效率高",
    "支付转化好",
)

INTERNET_OPS_CONTENT_FORBIDDEN = (
    "内容策略有效",
    "内容主推",
    "作者表现最好",
)

INTERNET_OPS_REQUIRED_ACTION_COLUMNS = {
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

INTERNET_OPS_REQUIRED_ROADMAP_COLUMNS = {
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

INTERNET_OPS_REQUIRED_BACKLOG_COLUMNS = {
    "实验编号",
    "实验假设",
    "目标用户",
    "实验对象",
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

INTERNET_OPS_REQUIRED_SECTIONS = [
    "internet_ops_data_scope",
    "internet_ops_can_judge",
    "internet_ops_north_star",
    "internet_ops_aarrr",
    "internet_ops_acquisition",
    "internet_ops_activation",
    "internet_ops_retention",
    "internet_ops_revenue",
    "internet_ops_referral",
    "internet_ops_traffic_structure",
    "internet_ops_user_growth",
    "internet_ops_funnel_conversion",
    "internet_ops_user_segment",
    "internet_ops_content_overview",
    "internet_ops_content_matrix",
    "internet_ops_channel_overview",
    "internet_ops_campaign",
    "internet_ops_community",
    "internet_ops_monetization",
    "internet_ops_risk_users",
    "internet_ops_anomaly",
    "internet_ops_problem_diagnosis",
    "internet_ops_action_table",
    "internet_ops_7day_actions",
    "internet_ops_30day_backlog",
    "internet_ops_forbidden_judgements",
    "internet_ops_data_gap_priority",
    "internet_ops_roadmap",
    "internet_ops_appendix_note",
]


def _contains_any(text: str, terms: tuple[str, ...] | list[str]) -> bool:
    return any(term in text for term in terms)


def internet_operations_quality_gate(
    *,
    management_markdown: str,
    total_pages: int,
    business_profile: str,
    field_registry: dict[str, Any],
    action_rows: list[dict[str, Any]],
    seven_day_rows: list[dict[str, Any]],
    backlog_rows: list[dict[str, Any]],
    section_ids: list[str] | None = None,
) -> dict[str, Any]:
    text = str(management_markdown or "")
    fail_items: list[str] = []
    affected_sections: list[str] = []

    if str(business_profile or "") != "internet_operations_report":
        fail_items.append("business_profile 不是 internet_operations_report")
        affected_sections.append("management_report")

    if not (35 <= total_pages <= 50):
        fail_items.append(f"management_report 页数不在 35-50 之间：{total_pages}")
        affected_sections.append("management_report")

    if _contains_any(text, INTERNET_OPS_PROCUREMENT_TERMS):
        fail_items.append("management_report 混入采销专属标题或术语")
        affected_sections.append("management_report")

    if _contains_any(text.lower(), INTERNET_OPS_ENGINEERING_TERMS):
        fail_items.append("management_report 混入工程内部词")
        affected_sections.append("management_report")

    section_id_set = set(section_ids or [])
    for section in INTERNET_OPS_REQUIRED_SECTIONS:
        if section not in section_id_set:
            fail_items.append(f"缺少必需章节：{section}")
            affected_sections.append("management_report")

    if not field_registry.get("has_cost_fields", False) and _contains_any(text, INTERNET_OPS_COST_FORBIDDEN):
        fail_items.append("缺 cost_fields 却出现 ROI/CAC/预算加码/砍渠道 类结论")
        affected_sections.append("management_report")

    if not field_registry.get("has_retention_fields", False) and _contains_any(text, INTERNET_OPS_RETENTION_FORBIDDEN):
        fail_items.append("缺 retention_fields 却出现长期用户质量判断")
        affected_sections.append("management_report")

    if not field_registry.get("has_revenue_fields", False) and _contains_any(text, INTERNET_OPS_REVENUE_FORBIDDEN):
        fail_items.append("缺 revenue_fields 却出现商业价值/LTV/规模化投放判断")
        affected_sections.append("management_report")

    if not field_registry.get("has_funnel_fields", False) and _contains_any(text, INTERNET_OPS_FUNNEL_FORBIDDEN):
        fail_items.append("缺 funnel_fields 却出现完整漏斗健康判断")
        affected_sections.append("management_report")

    if not field_registry.get("has_content_fields", False) and _contains_any(text, INTERNET_OPS_CONTENT_FORBIDDEN):
        fail_items.append("缺 content_fields 却出现内容策略有效或内容主推判断")
        affected_sections.append("management_report")

    if any("low_sample" in str(row.get("样本量标记") or "").lower() for row in action_rows):
        for row in action_rows:
            final_action = str(row.get("最终动作") or "")
            if any(term in final_action for term in ["加码", "主推", "砍掉", "放量", "扩大投放"]):
                fail_items.append(f"低样本对象出现强增长结论：{row.get('对象名称')}")
                affected_sections.append("action_table")
                break

    if not action_rows or not INTERNET_OPS_REQUIRED_ACTION_COLUMNS.issubset(set(action_rows[0].keys())):
        fail_items.append("对象级行动表缺少必需列")
        affected_sections.append("action_table")

    if not seven_day_rows or not INTERNET_OPS_REQUIRED_ROADMAP_COLUMNS.issubset(set(seven_day_rows[0].keys())):
        fail_items.append("7日运营动作表缺少必需列")
        affected_sections.append("7_day_action_table")

    if not backlog_rows or not INTERNET_OPS_REQUIRED_BACKLOG_COLUMNS.issubset(set(backlog_rows[0].keys())):
        fail_items.append("30日增长实验 backlog 缺少必需列")
        affected_sections.append("30_day_growth_experiment_backlog")

    if len(action_rows) > 30:
        fail_items.append("主报告对象级行动表超过 30 行")
        affected_sections.append("action_table")

    return {
        "passed": not fail_items,
        "business_profile": business_profile,
        "fail_items": fail_items,
        "affected_sections": sorted(set(affected_sections)),
        "suggested_fixes": [] if not fail_items else [
            "删除字段不足下的强结论",
            "补齐行动表与路线图必需列",
            "必要时切换到极简高合规版 management_report",
        ],
    }


def report_quality_scorer(
    *,
    management_markdown: str,
    total_pages: int,
    business_profile: str,
    field_registry: dict[str, Any],
    action_rows: list[dict[str, Any]],
    seven_day_rows: list[dict[str, Any]],
    backlog_rows: list[dict[str, Any]],
    strict_gate_result: dict[str, Any],
    output_names: list[str],
    section_ids: list[str] | None = None,
) -> dict[str, Any]:
    text = str(management_markdown or "")
    breakdown: dict[str, int] = {}
    hard_fail_items: list[str] = []

    profile_ok = str(business_profile or "") == "internet_operations_report" and "互联网运营" in text
    breakdown["business_profile_accuracy"] = 10 if profile_ok else 0
    if not profile_ok:
        hard_fail_items.append("业务类型识别错误或未体现为互联网运营报告")

    indicators_ok = (
        "北极星指标判断" in text
        and "AARRR 漏斗总览" in text
        and "流量结构分析" in text
        and "用户增长分析" in text
        and "渠道运营总览" in text
        and "付费与商业化分析" in text
    )
    breakdown["metric_coverage"] = 10 if indicators_ok else 5

    field_boundary_ok = "字段边界：" in text and "缺失字段：" in text
    breakdown["field_boundary_clarity"] = 10 if field_boundary_ok else 4
    if not field_boundary_ok:
        hard_fail_items.append("字段边界未被明确写出")

    funnel_ok = "漏斗转化分析" in text and ("不可判断环节" in text or "最大流失环节" in text)
    breakdown["funnel_quality"] = 10 if funnel_ok else 4

    retention_ok = field_registry.get("has_retention_fields", False) or "需先补 D1/D7/D30" in text or "留存字段缺失" in text
    breakdown["retention_control"] = 10 if retention_ok else 0
    if not retention_ok:
        hard_fail_items.append("没有留存字段却未明确压住用户长期质量判断")

    object_analysis_ok = bool(action_rows) and bool(seven_day_rows)
    breakdown["object_level_analysis"] = 15 if object_analysis_ok else 5

    dispatch_ok = (
        bool(action_rows)
        and INTERNET_OPS_REQUIRED_ACTION_COLUMNS.issubset(set(action_rows[0].keys()))
        and bool(seven_day_rows)
        and INTERNET_OPS_REQUIRED_ROADMAP_COLUMNS.issubset(set(seven_day_rows[0].keys()))
    )
    breakdown["dispatchability"] = 10 if dispatch_ok else 0
    if not dispatch_ok:
        hard_fail_items.append("动作可派单字段不完整")

    forbidden_control_ok = not (
        (not field_registry.get("has_cost_fields", False) and _contains_any(text, INTERNET_OPS_COST_FORBIDDEN))
        or (not field_registry.get("has_retention_fields", False) and _contains_any(text, INTERNET_OPS_RETENTION_FORBIDDEN))
        or (not field_registry.get("has_revenue_fields", False) and _contains_any(text, INTERNET_OPS_REVENUE_FORBIDDEN))
        or (not field_registry.get("has_funnel_fields", False) and _contains_any(text, INTERNET_OPS_FUNNEL_FORBIDDEN))
        or (not field_registry.get("has_content_fields", False) and _contains_any(text, INTERNET_OPS_CONTENT_FORBIDDEN))
    )
    breakdown["misjudgement_control"] = 10 if forbidden_control_ok else 0
    if not forbidden_control_ok:
        hard_fail_items.append("字段不足下仍存在被禁止误判")

    pdf_ok = 35 <= total_pages <= 50 and all(section in set(section_ids or []) for section in INTERNET_OPS_REQUIRED_SECTIONS)
    breakdown["pdf_completeness"] = 10 if pdf_ok else 4
    if not pdf_ok:
        hard_fail_items.append("PDF 页数或章节完整性不达标")

    readable_ok = len((management_markdown or "").split("## 管理层摘要")) > 1 and text.count("核心结论：") >= 5
    breakdown["management_readability"] = 5 if readable_ok else 2

    outputs_ok = all(
        any(name.endswith(required) for name in output_names)
        for required in [
            "management_report.pdf",
            "management_report.html",
            "analyst_appendix.xlsx",
            "internet_ops_field_availability_registry.json",
            "internet_ops_object_decision_registry.csv",
            "7_day_action_table.csv",
            "30_day_growth_experiment_backlog.csv",
            "report_quality_score.json",
            "quality_gate_result.json",
        ]
    )
    if not outputs_ok:
        hard_fail_items.append("输出文件不完整")

    score = sum(breakdown.values())
    if hard_fail_items or not strict_gate_result.get("passed", False):
        score = min(score, 89)

    return {
        "business_profile": business_profile,
        "score": score,
        "passed": score >= 90 and bool(strict_gate_result.get("passed", False)),
        "breakdown": breakdown,
        "hard_fail_items": hard_fail_items,
    }
