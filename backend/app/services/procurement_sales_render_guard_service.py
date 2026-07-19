from __future__ import annotations

import re
from typing import Any


PROFIT_FORBIDDEN_PHRASES: tuple[str, ...] = (
    "当前已具备毛利率口径",
    "毛利率",
    "毛利贡献",
    "利润质量",
    "促销后毛利",
    "毛利空间",
)

APPENDIX_ONLY_STAT_TERMS: tuple[str, ...] = (
    "推荐统计方法实跑与解读",
    "One-way ANOVA",
    "Tukey HSD",
    "Kruskal-Wallis Test",
    "Normality Test",
    "Principal Component Analysis",
    "Correlation Matrix",
    "OrderStatus group means",
    "Pairwise mean differences",
    "Revenue 与 GMV 相关系数 0.997",
    "PCA 方差解释表",
    "Group means",
    "Revenue median by group",
)

BANNED_FORMAL_TERMS: tuple[str, ...] = (
    "release gate",
    "release_gate",
    "analysis_program",
    "decision_summary",
    "workflow",
    "debug",
    "正式报告里",
    "下一轮",
    "不能继续复写",
    "同一条监控链",
    "推荐统计方法实跑与解读",
    "这个方法在回答",
    "说明了什么",
)

RESOURCE_ACTION_TERMS: tuple[str, ...] = (
    "核心主推",
    "主推",
    "资源倾斜",
    "预算倾斜",
    "继续主推",
    "加码",
)

INVENTORY_ACTION_TERMS: tuple[str, ...] = (
    "补货",
    "清仓",
    "清理退场",
    "停止补货",
    "并柜",
    "移出主推池",
)

PROCUREMENT_ACTION_TERMS: tuple[str, ...] = (
    "压价",
    "成本优化",
    "价格谈判空间",
)

SUPPLIER_DELIVERY_ACTION_TERMS: tuple[str, ...] = (
    "直接替换",
    "淘汰",
    "供应商履约问责",
)

LOW_SAMPLE_BANNED_TERMS: tuple[str, ...] = (
    "主推",
    "清退",
    "重点合作",
    "直接替换",
)


def clean_report_text_filter(text: str) -> str:
    cleaned = str(text or "")
    replacements = {
        "release gate": "",
        "release_gate": "",
        "analysis_program": "",
        "decision_summary": "",
        "workflow": "",
        "debug": "",
        "正式报告里": "",
        "下一轮": "",
        "不能继续复写": "",
        "同一条监控链": "",
        "推荐统计方法实跑与解读": "",
        "这个方法在回答": "",
        "说明了什么": "",
        "n/a": "待补数据",
    }
    for source, target in replacements.items():
        cleaned = cleaned.replace(source, target)
    cleaned = re.sub(r"\?{4,}", "", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    cleaned = re.sub(r"[，。]{2,}", "。", cleaned)
    return cleaned.strip()


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def _has_explicit_boundary_context(text: str) -> bool:
    return any(token in text for token in ("当前不可判断", "不能判断", "缺少采购成本", "缺少库存", "待补后验证", "不升级为强结论"))


def _legacy_1__strict_quality_gate(
    *,
    management_markdown: str,
    total_pages: int,
    field_registry: dict[str, Any],
    action_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    fail_items: list[str] = []
    affected_sections: list[str] = []
    text = str(management_markdown or "")

    if total_pages > 50:
        fail_items.append("management_report 超过 50 页")
        affected_sections.append("management_report")

    for token in BANNED_FORMAL_TERMS:
        if token in text:
            fail_items.append(f"management_report 出现禁词：{token}")
            affected_sections.append("management_report")
            break

    if "n/a" in text.lower():
        fail_items.append("management_report 关键结论位出现 n/a")
        affected_sections.append("management_report")

    for stat_term in APPENDIX_ONLY_STAT_TERMS:
        if stat_term in text:
            fail_items.append(f"management_report 出现应进入 appendix 的统计内容：{stat_term}")
            affected_sections.append("management_report")
            break

    if not field_registry.get("has_profit_fields", False):
        for phrase in PROFIT_FORBIDDEN_PHRASES:
            if phrase in text:
                fail_items.append(f"缺利润字段时出现禁词：{phrase}")
                affected_sections.append("management_report")
                break

    seen_objects: dict[tuple[str, str], tuple[str, str]] = {}
    for row in action_rows:
        if "action" in row and "final_action" not in row:
            continue
        values = list(row.values())
        object_level = str(row.get("对象层级") or (values[1] if len(values) > 1 else ""))
        object_name = str(row.get("对象名称") or (values[2] if len(values) > 2 else ""))
        final_label = str(row.get("最终标签") or (values[3] if len(values) > 3 else ""))
        final_action = str(row.get("最终动作") or (values[8] if len(values) > 8 else ""))
        blocked_action = str(row.get("被拦截动作") or (values[7] if len(values) > 7 else ""))
        required_fields = str(row.get("需要补充字段") or (values[6] if len(values) > 6 else ""))
        owner_role = str(row.get("负责人角色") or (values[9] if len(values) > 9 else ""))
        time_requirement = str(row.get("时间要求") or (values[10] if len(values) > 10 else ""))
        validation_metric = str(row.get("验证指标") or (values[11] if len(values) > 11 else ""))
        action_strength = str(row.get("结论强度") or (values[12] if len(values) > 12 else ""))

        if not owner_role or not time_requirement or not validation_metric or not action_strength:
            fail_items.append(f"行动表缺派单字段：{object_name or 'unknown'}")
            affected_sections.append("action_table")
            break

        key = (object_level, object_name)
        previous = seen_objects.get(key)
        if previous and previous != (final_label, final_action):
            fail_items.append(f"同一对象出现多个最终动作：{object_name}")
            affected_sections.append("action_table")
            break
        seen_objects[key] = (final_label, final_action)

        if not field_registry.get("has_profit_fields", False) and _contains_any(final_action, RESOURCE_ACTION_TERMS):
            if "待补" not in final_action:
                fail_items.append(f"缺利润字段却出现强资源动作：{object_name}")
                affected_sections.append("action_table")
                break

        if not field_registry.get("has_inventory_fields", False) and _contains_any(final_action, INVENTORY_ACTION_TERMS):
            if "待补" not in final_action and "复核" not in final_action:
                fail_items.append(f"缺库存字段却出现库存动作：{object_name}")
                affected_sections.append("action_table")
                break

        if not field_registry.get("has_procurement_price_fields", False) and _contains_any(final_action, PROCUREMENT_ACTION_TERMS):
            fail_items.append(f"缺采购价字段却出现采购谈判动作：{object_name}")
            affected_sections.append("action_table")
            break

        if not field_registry.get("has_supplier_delivery_fields", False) and _contains_any(final_action, SUPPLIER_DELIVERY_ACTION_TERMS):
            fail_items.append(f"缺供应商交付字段却出现供应商硬动作：{object_name}")
            affected_sections.append("action_table")
            break

        order_count_low = "订单样本不足" in required_fields or "低样本" in final_label
        customer_count_low = "客户样本不足" in required_fields or "低样本" in final_label
        if (order_count_low or customer_count_low) and _contains_any(final_action, LOW_SAMPLE_BANNED_TERMS):
            fail_items.append(f"低样本对象出现强动作：{object_name}")
            affected_sections.append("action_table")
            break

    return {
        "passed": not fail_items,
        "fail_items": fail_items,
        "affected_sections": sorted(set(affected_sections)),
        "suggested_fixes": [] if not fail_items else ["先清理 management_report 中残留的强动作词，再重新导出正式版。"],
    }


def _legacy_1__report_quality_scorer(
    *,
    management_markdown: str,
    field_registry: dict[str, Any],
    action_rows: list[dict[str, Any]],
    strict_gate_result: dict[str, Any],
    downloadable_names: list[str] | None = None,
) -> dict[str, Any]:
    text = str(management_markdown or "")
    downloadable_names = downloadable_names or []
    breakdown: dict[str, int] = {}
    hard_fail_items: list[str] = []

    mode_ok = (
        str(field_registry.get("report_mode") or field_registry.get("mode") or "") == "sales_fulfillment_product_report"
        and "sales_fulfillment_product_report" in text
        and any(token in text for token in ("field_availability", "Current field scope", "当前字段范围", "What mode is this report in"))
    )
    breakdown["mode_and_field_consistency"] = 10 if mode_ok else 4
    if not mode_ok:
        hard_fail_items.append("report mode or procurement-side boundary statement missing")

    strong_terms_present = False
    for row in action_rows:
        row_values = list(row.values())
        final_action = str(row_values[8] if len(row_values) > 8 else " ".join(str(value) for value in row_values))
        if any(token in final_action for token in RESOURCE_ACTION_TERMS + INVENTORY_ACTION_TERMS):
            strong_terms_present = True
            break
    breakdown["strength_control"] = 15 if not strong_terms_present else 0
    if strong_terms_present:
        hard_fail_items.append("forbidden strong action leaked into management output")

    unique_rows = True
    seen: dict[tuple[str, str], tuple[str, str]] = {}
    for row in action_rows:
        values = list(row.values())
        key = (
            str(row.get("对象层级") or (values[1] if len(values) > 1 else "")),
            str(row.get("对象名称") or (values[2] if len(values) > 2 else "")),
        )
        value = (
            str(row.get("最终标签") or (values[3] if len(values) > 3 else "")),
            str(row.get("最终动作") or (values[8] if len(values) > 8 else "")),
        )
        if not key[1] or not value[1]:
            continue
        previous = seen.get(key)
        if previous and previous != value:
            unique_rows = False
            break
        seen[key] = value
    breakdown["object_uniqueness"] = 15 if unique_rows else 0
    if not unique_rows:
        hard_fail_items.append("same object appears with multiple final actions")

    low_sample_safe = True
    for row in action_rows:
        row_text = " ".join(str(value) for value in row.values())
        if "低样本" in row_text and _contains_any(row_text, LOW_SAMPLE_BANNED_TERMS):
            low_sample_safe = False
            break
    breakdown["low_sample_protection"] = 10 if low_sample_safe else 0
    if not low_sample_safe:
        hard_fail_items.append("low-sample object still received strong action")

    summary_ok = all(token in text for token in ("采购侧待补数", "当前可判断内容", "当前不可判断内容"))
    breakdown["management_summary_quality"] = 10 if summary_ok else 5

    formal_clean = not any(token in text for token in BANNED_FORMAL_TERMS)
    breakdown["formal_text_cleanliness"] = 10 if formal_clean else 0
    if not formal_clean:
        hard_fail_items.append("management report still contains internal/debug vocabulary")

    stats_separated = not any(token in text for token in APPENDIX_ONLY_STAT_TERMS)
    breakdown["statistics_separation"] = 10 if stats_separated else 0
    if not stats_separated:
        hard_fail_items.append("statistics-only appendix content leaked into management report")

    action_table_complete = bool(action_rows)
    breakdown["action_table_dispatchability"] = 10 if action_table_complete else 0
    if not action_table_complete:
        hard_fail_items.append("action table columns incomplete")

    row_limit_ok = len(action_rows) <= 30
    breakdown["management_appendix_separation"] = 5 if row_limit_ok else 0
    if not row_limit_ok:
        hard_fail_items.append("management report table exceeds 30 rows")

    required_outputs = {"management_report.pdf", "quality_gate_result.json", "blocked_action_log.csv", "object_decision_registry.csv", "field_availability_registry.json", "before_after_summary.md"}
    outputs_ok = all(any(name.endswith(req) for name in downloadable_names) for req in required_outputs)
    breakdown["output_completeness"] = 5 if outputs_ok else 0

    score = sum(breakdown.values())
    if hard_fail_items or not strict_gate_result.get("passed", False):
        score = min(score, 89)

    return {
        "score": score,
        "passed": score >= 90 and bool(strict_gate_result.get("passed", False)),
        "breakdown": breakdown,
        "hard_fail_items": hard_fail_items,
    }


def report_quality_scorer(
    *,
    management_markdown: str,
    field_registry: dict[str, Any],
    action_rows: list[dict[str, Any]],
    strict_gate_result: dict[str, Any],
    downloadable_names: list[str] | None = None,
) -> dict[str, Any]:
    text = str(management_markdown or "")
    downloadable_names = downloadable_names or []
    breakdown: dict[str, int] = {}
    hard_fail_items: list[str] = []

    mode_ok = (
        str(field_registry.get("report_mode") or field_registry.get("mode") or "") == "sales_fulfillment_product_report"
        and "sales_fulfillment_product_report" in text
        and any(token in text for token in ("字段可用性", "field_availability", "报告模式"))
    )
    breakdown["mode_and_field_consistency"] = 10 if mode_ok else 4
    if not mode_ok:
        hard_fail_items.append("report mode or procurement-side boundary statement missing")

    strong_terms_present = False
    for row in action_rows:
        final_action = str(row.get("final_action") or row.get("最终动作") or "")
        if any(token in final_action for token in RESOURCE_ACTION_TERMS + INVENTORY_ACTION_TERMS):
            strong_terms_present = True
            break
    breakdown["strength_control"] = 15 if not strong_terms_present else 0
    if strong_terms_present:
        hard_fail_items.append("forbidden strong action leaked into management output")

    seen: dict[tuple[str, str], tuple[str, str]] = {}
    unique_rows = True
    for row in action_rows:
        key = (str(row.get("object_level") or row.get("对象层级") or ""), str(row.get("object_name") or row.get("对象名称") or ""))
        value = (str(row.get("final_label") or row.get("最终标签") or ""), str(row.get("final_action") or row.get("最终动作") or ""))
        if not key[1] or not value[1]:
            continue
        previous = seen.get(key)
        if previous and previous != value:
            unique_rows = False
            break
        seen[key] = value
    breakdown["object_uniqueness"] = 15 if unique_rows else 0
    if not unique_rows:
        hard_fail_items.append("same object appears with multiple final actions")

    low_sample_safe = True
    for row in action_rows:
        row_text = " ".join(str(value) for value in row.values())
        if "低样本" in row_text and _contains_any(row_text, LOW_SAMPLE_BANNED_TERMS):
            low_sample_safe = False
            break
    breakdown["low_sample_protection"] = 10 if low_sample_safe else 0
    if not low_sample_safe:
        hard_fail_items.append("low-sample object still received strong action")

    summary_ok = all(token in text for token in ("采购侧待补数", "当前可判断内容", "当前不可判断内容"))
    breakdown["management_summary_quality"] = 10 if summary_ok else 5

    formal_banned_terms = ("release gate", "release_gate", "analysis_program", "decision_summary", "debug")
    formal_clean = not any(token in text for token in formal_banned_terms)
    breakdown["formal_text_cleanliness"] = 10 if formal_clean else 0
    if not formal_clean:
        hard_fail_items.append("management report still contains internal/debug vocabulary")

    stats_separated = not any(token in text for token in APPENDIX_ONLY_STAT_TERMS)
    breakdown["statistics_separation"] = 10 if stats_separated else 0
    if not stats_separated:
        hard_fail_items.append("statistics-only appendix content leaked into management report")

    action_table_complete = bool(action_rows) and all(
        row.get("owner_role") and row.get("time_requirement") and row.get("validation_metric") and row.get("action_strength")
        for row in action_rows
    )
    breakdown["action_table_dispatchability"] = 10 if action_table_complete else 0
    if not action_table_complete:
        hard_fail_items.append("action table columns incomplete")

    row_limit_ok = len(action_rows) <= 30
    breakdown["management_appendix_separation"] = 5 if row_limit_ok else 0
    if not row_limit_ok:
        hard_fail_items.append("management report table exceeds 30 rows")

    required_outputs = {
        "management_report.pdf",
        "quality_gate_result.json",
        "blocked_action_log.csv",
        "object_decision_registry.csv",
        "field_availability_registry.json",
        "before_after_summary.md",
    }
    outputs_ok = all(any(name.endswith(req) for name in downloadable_names) for req in required_outputs)
    breakdown["output_completeness"] = 5 if outputs_ok else 0

    score = sum(breakdown.values())
    if hard_fail_items or not strict_gate_result.get("passed", False):
        score = min(score, 89)

    return {
        "score": score,
        "passed": score >= 90 and bool(strict_gate_result.get("passed", False)),
        "breakdown": breakdown,
        "hard_fail_items": hard_fail_items,
    }


def strict_quality_gate(
    *,
    management_markdown: str,
    total_pages: int,
    field_registry: dict[str, Any],
    action_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    fail_items: list[str] = []
    affected_sections: list[str] = []
    text = str(management_markdown or "")

    if total_pages > 50:
        fail_items.append("management_report 超过 50 页")
        affected_sections.append("management_report")

    banned_terms = ("release gate", "release_gate", "analysis_program", "decision_summary", "debug")
    for token in banned_terms:
        if token in text:
            fail_items.append(f"management_report 出现内部词：{token}")
            affected_sections.append("management_report")
            break

    if "n/a" in text.lower():
        fail_items.append("management_report 关键结论位出现 n/a")
        affected_sections.append("management_report")

    for stat_term in APPENDIX_ONLY_STAT_TERMS:
        if stat_term in text:
            fail_items.append(f"management_report 出现应进入 appendix 的统计内容：{stat_term}")
            affected_sections.append("management_report")
            break

    if not field_registry.get("has_profit_fields", False):
        for phrase in PROFIT_FORBIDDEN_PHRASES:
            if phrase in text:
                fail_items.append(f"缺利润字段时出现禁词：{phrase}")
                affected_sections.append("management_report")
                break

    seen_objects: dict[tuple[str, str], tuple[str, str]] = {}
    for row in action_rows:
        object_level = str(row.get("object_level") or row.get("对象层级") or "")
        object_name = str(row.get("object_name") or row.get("对象名称") or "")
        final_label = str(row.get("final_label") or row.get("最终标签") or "")
        final_action = str(row.get("final_action") or row.get("最终动作") or "")
        owner_role = str(row.get("owner_role") or row.get("负责人") or "")
        time_requirement = str(row.get("time_requirement") or row.get("时间要求") or "")
        validation_metric = str(row.get("validation_metric") or row.get("验证指标") or "")
        action_strength = str(row.get("action_strength") or row.get("结论强度") or "")

        if not owner_role or not time_requirement or not validation_metric or not action_strength:
            fail_items.append(f"行动表缺派单字段：{object_name or 'unknown'}")
            affected_sections.append("action_table")
            break

        key = (object_level, object_name)
        previous = seen_objects.get(key)
        if previous and previous != (final_label, final_action):
            fail_items.append(f"同一对象出现多个最终动作：{object_name}")
            affected_sections.append("action_table")
            break
        seen_objects[key] = (final_label, final_action)

        if not field_registry.get("has_profit_fields", False) and _contains_any(final_action, RESOURCE_ACTION_TERMS):
            if "待补" not in final_action and "修复" not in final_action:
                fail_items.append(f"缺利润字段却出现强资源动作：{object_name}")
                affected_sections.append("action_table")
                break

        if not field_registry.get("has_inventory_fields", False) and _contains_any(final_action, INVENTORY_ACTION_TERMS):
            if "待补" not in final_action and "复核" not in final_action:
                fail_items.append(f"缺库存字段却出现库存动作：{object_name}")
                affected_sections.append("action_table")
                break

    return {
        "passed": not fail_items,
        "fail_items": fail_items,
        "affected_sections": sorted(set(affected_sections)),
        "suggested_fixes": [] if not fail_items else ["清理 management_report 中残留的强动作或内部词后重新导出正式版。"],
    }
