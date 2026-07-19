from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any

from pypdf import PdfReader
from app.services.ecommerce_render_guard_service import ecommerce_field_boundary_errors


PROCUREMENT_FORBIDDEN_TERMS = [
    "核心主推",
    "资源倾斜",
    "清理退场",
    "补货放量",
    "预算倾斜",
    "继续主推",
    "release gate",
    "release_gate",
    "下一轮",
    "正式报告里",
    "同一条监控链",
    "推荐统计方法实跑与解读",
    "ANOVA",
    "Tukey HSD",
    "Kruskal-Wallis",
    "Principal Component Analysis",
    "OrderStatus group means",
    "Pairwise mean differences",
]

INTERNET_OPS_FORBIDDEN_TERMS = [
    "采销",
    "SKU",
    "供应商",
    "库存",
    "采购价",
    "registry",
    "guardrail",
    "schema",
    "validator",
    "raw_action",
    "debug",
    "workflow",
]

INTERNET_OPS_REQUIRED_OBJECT_ACTION_COLUMNS = [
    "负责人角色",
    "时间要求",
    "验证指标",
    "成功标准",
    "结论强度",
    "置信度",
]

INTERNET_OPS_REQUIRED_ROADMAP_COLUMNS = [
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
]

INTERNET_OPS_REQUIRED_BACKLOG_COLUMNS = [
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
]

INTERNET_OPS_REQUIRED_SECTIONS = [
    "internet_ops_data_scope",
    "internet_ops_can_judge",
    "internet_ops_north_star",
    "internet_ops_aarrr",
    "internet_ops_action_table",
    "internet_ops_7day_actions",
    "internet_ops_30day_backlog",
]

ECOMMERCE_REQUIRED_ACTION_COLUMNS = [
    "负责人角色",
    "时间要求",
    "验证指标",
    "成功标准",
    "结论强度",
    "置信度",
]

ECOMMERCE_REQUIRED_7DAY_COLUMNS = [
    "负责人角色",
    "截止时间",
    "验证标准",
]

ECOMMERCE_REQUIRED_BACKLOG_COLUMNS = [
    "核心指标",
    "护栏指标",
    "成功标准",
]

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

ECOMMERCE_WRONG_TITLES = [
    "互联网运营数据分析报告",
    "内容运营数据分析报告",
    "用户增长数据分析报告",
    "社区运营数据分析报告",
]

GENERIC_LONG_REQUIRED_CHAIN_FILES = [
    "codex_interpretation_call_log.jsonl",
    "business_context_interpretation.md",
    "field_semantic_map.md",
    "metric_derivation_plan.json",
    "derived_metric_execution_review.md",
    "generic_kpi_tree.md",
    "management_question_bank.md",
    "object_level_interpretation.md",
    "interpretation_conflict_check.md",
    "executive_readability_review.md",
    "business_rigor_review.md",
    "final_codex_interpretation_review.md",
]

GENERIC_LONG_REQUIRED_ACTION_COLUMNS = [
    "负责人角色",
    "时间要求",
    "验证指标",
    "成功标准",
]

GENERIC_LONG_REQUIRED_7DAY_COLUMNS = [
    "负责人角色",
    "截止时间",
    "验证标准",
]

GENERIC_LONG_REQUIRED_BACKLOG_COLUMNS = [
    "核心指标",
    "护栏指标",
    "成功标准",
]

GENERIC_LONG_WRONG_TITLES = [
    "互联网运营数据分析报告",
    "内容运营数据分析报告",
    "用户增长数据分析报告",
    "社区运营数据分析报告",
    "渠道投放与增长运营复盘报告",
    "中文销售履约与商品经营复盘主报告",
    "销售履约与商品经营复盘",
]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _extract_pdf_text(path: Path) -> str:
    return "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)


def _pdf_text(path: Path) -> tuple[str, int]:
    if not path.exists():
        return ("", 0)
    reader = PdfReader(str(path))
    return ("\n".join(page.extract_text() or "" for page in reader.pages), len(reader.pages))


def _extract_html_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"<script[\s\S]*?</script>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _call_log_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _page_draft_jsons(report_dir: Path) -> list[Path]:
    page_drafts_dir = report_dir / "page_drafts"
    if not page_drafts_dir.exists():
        return []
    return sorted(page_drafts_dir.glob("page_*.json"))


def _extract_snippet(text: str, max_len: int = 32) -> str:
    return re.sub(r"\s+", "", text or "")[:max_len]


def _find_existing(report_dir: Path, *names: str) -> Path | None:
    for name in names:
        path = report_dir / name
        if path.exists():
            return path
    return None


def _validate_uniqueness(rows: list[dict[str, str]]) -> list[str]:
    seen: dict[str, tuple[str, str]] = {}
    conflicts: list[str] = []
    for row in rows:
        object_id = str(row.get("object_id") or "")
        current = (str(row.get("final_label") or ""), str(row.get("final_action") or ""))
        previous = seen.get(object_id)
        if previous and previous != current:
            conflicts.append(object_id)
        seen[object_id] = current
    return sorted(set(conflicts))


def _validate_internet_ops(report_dir: Path, report_id: str) -> dict[str, Any]:
    management_pdf = report_dir / f"{report_id}-management_report.pdf"
    management_html = report_dir / f"{report_id}-management_report.html"
    quality_gate_json = report_dir / f"{report_id}-quality_gate_result.json"
    score_json = report_dir / f"{report_id}-report_quality_score.json"
    field_json = _find_existing(
        report_dir,
        f"{report_id}-internet_ops_field_availability_registry.json",
        "internet_ops_field_availability_registry.json",
        f"{report_id}-field_availability_registry.json",
    )
    registry_csv = _find_existing(
        report_dir,
        f"{report_id}-internet_ops_object_decision_registry.csv",
        "internet_ops_object_decision_registry.csv",
        f"{report_id}-object_decision_registry.csv",
    )
    object_action_csv = _find_existing(report_dir, "internet_ops_action_table.csv")
    seven_day_csv = report_dir / "7_day_action_table.csv"
    backlog_csv = report_dir / "30_day_growth_experiment_backlog.csv"

    missing_outputs = [
        path.name
        for path in [management_pdf, management_html, quality_gate_json, score_json, seven_day_csv, backlog_csv]
        if not path.exists()
    ]
    if field_json is None:
        missing_outputs.append(f"{report_id}-internet_ops_field_availability_registry.json")
    if registry_csv is None:
        missing_outputs.append("internet_ops_object_decision_registry.csv")
    if object_action_csv is None:
        missing_outputs.append("internet_ops_action_table.csv")

    pdf_text = _extract_pdf_text(management_pdf) if management_pdf.exists() else ""
    html_text = _extract_html_text(management_html) if management_html.exists() else ""
    html_raw = management_html.read_text(encoding="utf-8") if management_html.exists() else ""
    combined_text = f"{html_text}\n{pdf_text}"

    forbidden_terms_found = [term for term in INTERNET_OPS_FORBIDDEN_TERMS if term in combined_text]

    field_boundary_errors: list[str] = []
    field_registry = _read_json(field_json) if field_json else {}
    if field_registry:
        if not field_registry.get("has_cost_fields", False):
            for term in ["ROI", "CAC", "预算加码", "砍渠道"]:
                if term in combined_text:
                    field_boundary_errors.append(f"缺 cost_fields 却出现 {term}")
        if not field_registry.get("has_retention_fields", False):
            for term in ["用户质量高", "长期价值高", "用户黏性强", "长期留存好"]:
                if term in combined_text:
                    field_boundary_errors.append(f"缺 retention_fields 却出现 {term}")
        if not field_registry.get("has_revenue_fields", False):
            for term in ["LTV高", "商业价值高", "规模化投放", "高价值用户"]:
                if term in combined_text:
                    field_boundary_errors.append(f"缺 revenue_fields 却出现 {term}")
        if not field_registry.get("has_funnel_fields", False) and "完整转化链路健康" in combined_text:
            field_boundary_errors.append("缺 funnel_fields 却出现完整漏斗健康判断")
        if not field_registry.get("has_content_fields", False):
            for term in ["内容策略有效", "内容主推", "作者表现最好"]:
                if term in combined_text:
                    field_boundary_errors.append(f"缺 content_fields 却出现 {term}")

    registry_rows = _csv_rows(registry_csv) if registry_csv else []
    conflicting_object_actions = _validate_uniqueness(registry_rows)

    action_table_errors: list[str] = []
    object_action_rows = _csv_rows(object_action_csv) if object_action_csv and object_action_csv.exists() else []
    seven_day_rows = _csv_rows(seven_day_csv) if seven_day_csv.exists() else []
    backlog_rows = _csv_rows(backlog_csv) if backlog_csv.exists() else []
    if not object_action_rows or not set(INTERNET_OPS_REQUIRED_OBJECT_ACTION_COLUMNS).issubset(set(object_action_rows[0].keys())):
        action_table_errors.append("对象级行动表缺少负责人/时间/验证指标/成功标准等必需列")
    if not seven_day_rows or not set(INTERNET_OPS_REQUIRED_ROADMAP_COLUMNS).issubset(set(seven_day_rows[0].keys())):
        action_table_errors.append("7日运营动作表缺少负责人/时间/验证标准等必需列")
    if not backlog_rows or not set(INTERNET_OPS_REQUIRED_BACKLOG_COLUMNS).issubset(set(backlog_rows[0].keys())):
        action_table_errors.append("30日增长实验 backlog 缺少必需列")

    missing_required_sections = [section for section in INTERNET_OPS_REQUIRED_SECTIONS if f'id="{section}"' not in html_raw]
    pages = len(PdfReader(str(management_pdf)).pages) if management_pdf.exists() else 0
    if not (35 <= pages <= 50):
        missing_required_sections.append(f"页数异常:{pages}")

    score = int((_read_json(score_json).get("score") or 0)) if score_json.exists() else 0
    quality_gate_passed = bool((_read_json(quality_gate_json).get("passed")) if quality_gate_json.exists() else False)

    fail_items: list[str] = []
    if missing_outputs:
        fail_items.append(f"缺少输出文件：{', '.join(missing_outputs)}")
    if forbidden_terms_found:
        fail_items.append(f"发现禁词：{', '.join(forbidden_terms_found)}")
    fail_items.extend(field_boundary_errors)
    if conflicting_object_actions:
        fail_items.append(f"同一对象存在多个 final_action：{', '.join(conflicting_object_actions)}")
    if missing_required_sections:
        fail_items.append(f"缺少必需章节或页数不符：{', '.join(missing_required_sections)}")
    fail_items.extend(action_table_errors)
    if score < 90:
        fail_items.append(f"score < 90: {score}")
    if not quality_gate_passed:
        fail_items.append("quality_gate_result.passed != true")

    return {
        "report_id": report_id,
        "business_profile": "internet_operations_report",
        "passed": not fail_items,
        "score": score,
        "forbidden_terms_found": forbidden_terms_found,
        "field_boundary_errors": field_boundary_errors,
        "missing_required_sections": missing_required_sections,
        "action_table_errors": action_table_errors,
        "conflicting_object_actions": conflicting_object_actions,
        "missing_outputs": missing_outputs,
        "quality_gate_passed": quality_gate_passed,
        "fail_items": fail_items,
    }


def _validate_procurement(report_dir: Path, report_id: str) -> dict[str, Any]:
    management_pdf = report_dir / f"{report_id}-management_report.pdf"
    management_html = report_dir / f"{report_id}-management_report.html"
    quality_gate_json = report_dir / f"{report_id}-quality_gate_result.json"
    quality_score_json = report_dir / f"{report_id}-report_quality_score.json"
    registry_csv = report_dir / f"{report_id}-object_decision_registry.csv"
    field_json = report_dir / f"{report_id}-field_availability_registry.json"
    missing_outputs = [
        path.name
        for path in [management_pdf, management_html, quality_gate_json, quality_score_json, registry_csv, field_json]
        if not path.exists()
    ]
    pdf_text = _extract_pdf_text(management_pdf) if management_pdf.exists() else ""
    html_text = _extract_html_text(management_html) if management_html.exists() else ""
    forbidden_terms_found = [term for term in PROCUREMENT_FORBIDDEN_TERMS if term in f"{html_text}\n{pdf_text}"]
    field_consistency_errors: list[str] = []
    field_registry = _read_json(field_json) if field_json.exists() else {}
    if field_registry and not field_registry.get("has_profit_fields", False):
        for term in ["毛利率", "毛利贡献", "利润质量", "促销后毛利", "毛利空间", "当前已具备毛利率口径"]:
            if term in html_text:
                field_consistency_errors.append(f"缺利润字段却出现：{term}")
    if field_registry and not field_registry.get("has_inventory_fields", False):
        for term in ["补货", "清仓", "清理退场", "停止补货", "并柜", "移出主推池"]:
            if term in html_text:
                field_consistency_errors.append(f"缺库存字段却出现：{term}")
    registry_rows = _csv_rows(registry_csv) if registry_csv.exists() else []
    conflicting_object_actions = _validate_uniqueness(registry_rows)
    score = int((_read_json(quality_score_json).get("score") or 0)) if quality_score_json.exists() else 0
    quality_gate_passed = bool((_read_json(quality_gate_json).get("passed")) if quality_gate_json.exists() else False)

    fail_items: list[str] = []
    if missing_outputs:
        fail_items.append(f"缺少输出文件：{', '.join(missing_outputs)}")
    if forbidden_terms_found:
        fail_items.append(f"正式报告出现禁词：{', '.join(forbidden_terms_found)}")
    fail_items.extend(field_consistency_errors)
    if conflicting_object_actions:
        fail_items.append(f"同一对象存在多个 final_action：{', '.join(conflicting_object_actions)}")
    if score < 90:
        fail_items.append(f"score < 90: {score}")
    if not quality_gate_passed:
        fail_items.append("quality_gate_result.passed != true")

    return {
        "report_id": report_id,
        "business_profile": "procurement_sales_report",
        "passed": not fail_items,
        "score": score,
        "forbidden_terms_found": forbidden_terms_found,
        "field_consistency_errors": field_consistency_errors,
        "conflicting_object_actions": conflicting_object_actions,
        "registry_pdf_mismatch": [],
        "action_table_errors": [],
        "missing_outputs": missing_outputs,
        "quality_gate_passed": quality_gate_passed,
        "fail_items": fail_items,
    }


def _validate_ecommerce(report_dir: Path, report_id: str) -> dict[str, Any]:
    management_pdf = report_dir / f"{report_id}-management_report.pdf"
    management_html = report_dir / f"{report_id}-management_report.html"
    quality_gate_json = report_dir / f"{report_id}-quality_gate_result.json"
    quality_score_json = report_dir / f"{report_id}-report_quality_score.json"
    field_json = _find_existing(
        report_dir,
        f"{report_id}-ecommerce_field_availability_registry.json",
        "ecommerce_field_availability_registry.json",
    )
    semantic_json = _find_existing(
        report_dir,
        f"{report_id}-ecommerce_field_semantic_map.json",
        "ecommerce_field_semantic_map.json",
    )
    registry_csv = _find_existing(
        report_dir,
        "ecommerce_object_decision_registry.csv",
        f"{report_id}-ecommerce_object_decision_registry.csv",
    )
    action_csv = _find_existing(report_dir, "ecommerce_action_table.csv")
    seven_day_csv = report_dir / "7_day_ecommerce_action_table.csv"
    backlog_csv = report_dir / "30_day_ecommerce_experiment_backlog.csv"
    call_log = report_dir / "ecommerce_codex_call_log.jsonl"
    router_json = _find_existing(
        report_dir,
        f"{report_id}-business_profile_router_result.json",
        "business_profile_router_result.json",
    )

    missing_outputs = [
        path.name
        for path in [management_pdf, management_html, quality_gate_json, quality_score_json, seven_day_csv, backlog_csv, call_log]
        if not path.exists()
    ]
    if field_json is None:
        missing_outputs.append("ecommerce_field_availability_registry.json")
    if semantic_json is None:
        missing_outputs.append("ecommerce_field_semantic_map.json")
    if registry_csv is None:
        missing_outputs.append("ecommerce_object_decision_registry.csv")
    if action_csv is None:
        missing_outputs.append("ecommerce_action_table.csv")

    pdf_text, pages = _pdf_text(management_pdf)
    html_text = _extract_html_text(management_html) if management_html.exists() else ""
    html_raw = management_html.read_text(encoding="utf-8") if management_html.exists() else ""
    combined_text = f"{html_text}\n{pdf_text}"

    forbidden_terms_found = [term for term in ECOMMERCE_WRONG_TITLES if term in combined_text]
    field_boundary_errors: list[str] = []
    field_registry = _read_json(field_json) if field_json else {}
    if field_registry:
        field_boundary_errors = [
            item
            .replace("missing_margin_cost_fields_but_found:", "缺 margin_cost_fields 却出现：")
            .replace("missing_inventory_fields_but_found:", "缺 inventory_fields 却出现：")
            .replace("missing_traffic_fields_but_found:", "缺 traffic_fields 却出现：")
            .replace("missing_conversion_fields_but_found:", "缺 conversion_fields 却出现：")
            .replace("missing_aftersales_fields_but_found:", "缺 aftersales_fields 却出现：")
            .replace("missing_review_fields_but_found:", "缺 review_fields 却出现：")
            .replace("missing_fulfillment_fields_but_found:", "缺 fulfillment_fields 却出现：")
            .replace("missing_time_fields_but_found:", "缺 time_fields 却出现：")
            for item in ecommerce_field_boundary_errors(combined_text, field_registry)
        ]

    action_table_errors: list[str] = []
    action_rows = _csv_rows(action_csv) if action_csv else []
    seven_day_rows = _csv_rows(seven_day_csv) if seven_day_csv.exists() else []
    backlog_rows = _csv_rows(backlog_csv) if backlog_csv.exists() else []
    if not action_rows or not set(ECOMMERCE_REQUIRED_ACTION_COLUMNS).issubset(set(action_rows[0].keys())):
        action_table_errors.append("ecommerce_action_table 缺少负责人/时间/验证指标/成功标准等必需列")
    if not seven_day_rows or not set(ECOMMERCE_REQUIRED_7DAY_COLUMNS).issubset(set(seven_day_rows[0].keys())):
        action_table_errors.append("7_day_ecommerce_action_table 缺少负责人/截止时间/验证标准")
    if not backlog_rows or not set(ECOMMERCE_REQUIRED_BACKLOG_COLUMNS).issubset(set(backlog_rows[0].keys())):
        action_table_errors.append("30_day_ecommerce_experiment_backlog 缺少核心指标/护栏指标/成功标准")

    missing_required_sections: list[str] = []
    if not (35 <= pages <= 50):
        missing_required_sections.append(f"页数异常:{pages}")
    for section in ECOMMERCE_REQUIRED_SECTIONS:
        if f'id="{section}"' not in html_raw:
            missing_required_sections.append(section)

    call_rows = _call_log_rows(call_log)
    if len(call_rows) < 8:
        missing_required_sections.append(f"Codex/LLM 调用次数不足:{len(call_rows)}")

    router_payload = _read_json(router_json) if router_json else {}
    if str(router_payload.get("business_profile") or "") == "internet_operations_report":
        missing_required_sections.append("电商商品数据被判为 internet_operations_report")

    score = int((_read_json(quality_score_json).get("score") or 0)) if quality_score_json.exists() else 0
    quality_gate_passed = bool((_read_json(quality_gate_json).get("passed")) if quality_gate_json.exists() else False)

    fail_items: list[str] = []
    if missing_outputs:
        fail_items.append(f"缺少输出文件：{', '.join(sorted(set(missing_outputs)))}")
    if forbidden_terms_found:
        fail_items.append(f"误套互联网运营标题：{', '.join(forbidden_terms_found)}")
    fail_items.extend(field_boundary_errors)
    if missing_required_sections:
        fail_items.append(f"缺少必需章节或链路条件：{', '.join(missing_required_sections)}")
    fail_items.extend(action_table_errors)
    if score < 90:
        fail_items.append(f"score < 90: {score}")
    if not quality_gate_passed:
        fail_items.append("quality_gate_result.passed != true")

    return {
        "report_id": report_id,
        "business_profile": "ecommerce_product_operations_report",
        "passed": not fail_items,
        "score": score,
        "forbidden_terms_found": forbidden_terms_found,
        "field_boundary_errors": field_boundary_errors,
        "missing_required_sections": missing_required_sections,
        "action_table_errors": action_table_errors,
        "missing_outputs": sorted(set(missing_outputs)),
        "quality_gate_passed": quality_gate_passed,
        "fail_items": fail_items,
    }


def _validate_generic_long(report_dir: Path, report_id: str) -> dict[str, Any]:
    management_pdf = report_dir / f"{report_id}-management_report.pdf"
    management_html = report_dir / f"{report_id}-management_report.html"
    quality_gate_json = report_dir / f"{report_id}-quality_gate_result.json"
    quality_score_json = report_dir / f"{report_id}-report_quality_score.json"
    field_json = _find_existing(
        report_dir,
        f"{report_id}-generic_field_availability_registry.json",
        "generic_field_availability_registry.json",
    )
    registry_csv = _find_existing(
        report_dir,
        f"{report_id}-generic_object_decision_registry.csv",
        "generic_object_decision_registry.csv",
    )
    action_csv = report_dir / "generic_action_table.csv"
    seven_day_csv = report_dir / "7_day_action_table.csv"
    backlog_csv = report_dir / "30_day_improvement_backlog.csv"
    call_log = report_dir / "codex_interpretation_call_log.jsonl"
    page_plan_json = report_dir / "long_report_page_plan.json"
    final_review_md = report_dir / "final_codex_interpretation_review.md"

    missing_outputs = [
        path.name
        for path in [management_pdf, management_html, quality_gate_json, quality_score_json, seven_day_csv, backlog_csv, call_log, page_plan_json, final_review_md]
        if not path.exists()
    ]
    if field_json is None:
        missing_outputs.append("generic_field_availability_registry.json")
    if registry_csv is None:
        missing_outputs.append("generic_object_decision_registry.csv")
    if not action_csv.exists():
        missing_outputs.append("generic_action_table.csv")
    for file_name in GENERIC_LONG_REQUIRED_CHAIN_FILES:
        if not (report_dir / file_name).exists():
            missing_outputs.append(file_name)

    pdf_text, pages = _pdf_text(management_pdf)
    html_text = _extract_html_text(management_html) if management_html.exists() else ""
    combined_text = f"{html_text}\n{pdf_text}"

    forbidden_terms_found = [term for term in GENERIC_LONG_WRONG_TITLES if term in combined_text]
    field_boundary_errors: list[str] = []
    field_registry = _read_json(field_json) if field_json else {}
    if field_registry:
        if not field_registry.get("has_target_fields", False):
            for term in ["目标达成", "KPI完成", "绩效优秀", "超额完成", "未达标"]:
                if term in combined_text:
                    field_boundary_errors.append(f"缺 target_fields 却出现：{term}")
        if not field_registry.get("has_amount_fields", False):
            for term in ["ROI", "成本效率", "预算合理", "财务表现好"]:
                if term in combined_text:
                    field_boundary_errors.append(f"缺 amount_fields 却出现：{term}")
        if not field_registry.get("has_time_fields", False):
            for term in ["趋势改善", "同比", "环比", "持续增长", "持续下降"]:
                if term in combined_text:
                    field_boundary_errors.append(f"缺 time_fields 却出现：{term}")
        if not field_registry.get("has_quality_fields", False):
            for term in ["满意度高", "质量稳定", "问题改善", "服务质量稳定"]:
                if term in combined_text:
                    field_boundary_errors.append(f"缺 quality_fields 却出现：{term}")
        if not field_registry.get("has_people_fields", False):
            for term in ["责任归因", "归责到", "某团队负责", "某个人负责"]:
                if term in combined_text:
                    field_boundary_errors.append(f"缺 people_fields 却出现：{term}")

    action_table_errors: list[str] = []
    action_rows = _csv_rows(action_csv)
    seven_day_rows = _csv_rows(seven_day_csv)
    backlog_rows = _csv_rows(backlog_csv)
    if not action_rows or not set(GENERIC_LONG_REQUIRED_ACTION_COLUMNS).issubset(set(action_rows[0].keys())):
        action_table_errors.append("generic_action_table 缺少负责人/时间/验证指标/成功标准")
    if not seven_day_rows or not set(GENERIC_LONG_REQUIRED_7DAY_COLUMNS).issubset(set(seven_day_rows[0].keys())):
        action_table_errors.append("7_day_action_table 缺少负责人/截止时间/验证标准")
    if not backlog_rows or not set(GENERIC_LONG_REQUIRED_BACKLOG_COLUMNS).issubset(set(backlog_rows[0].keys())):
        action_table_errors.append("30_day_improvement_backlog 缺少核心指标/护栏指标/成功标准")

    missing_required_sections: list[str] = []
    if not (35 <= pages <= 50):
        missing_required_sections.append(f"页数异常:{pages}")
    page_plan = (_read_json(page_plan_json).get("pages") or []) if page_plan_json.exists() else []
    if len(page_plan) < 35:
        missing_required_sections.append("long_report_page_plan 页数不足 35")

    draft_jsons = _page_draft_jsons(report_dir)
    if len(draft_jsons) < 35:
        missing_required_sections.append("page_drafts/page_*.json 数量不足 35")

    call_rows = _call_log_rows(call_log)
    if len(call_rows) < 12:
        missing_required_sections.append(f"Codex/LLM 调用次数不足:{len(call_rows)}")
    page_generation_calls = [row for row in call_rows if str(row.get("pass_name") or "").startswith("page_generation_batch_")]
    if len(page_generation_calls) < 8:
        missing_required_sections.append(f"页面级生成调用次数不足:{len(page_generation_calls)}")
    required_passes = {
        "business_context_interpretation",
        "field_semantic_map",
        "metric_derivation_plan",
        "derived_metric_execution_review",
        "management_question_bank",
        "exploratory_interpretation",
        "object_level_interpretation",
        "interpretation_conflict_check",
        "long_report_page_plan",
        "executive_readability_review",
        "business_rigor_review",
        "final_codex_interpretation_review",
    }
    for pass_name in required_passes:
        matched = [row for row in call_rows if str(row.get("pass_name") or "") == pass_name or str(row.get("pass_name") or "").startswith(f"{pass_name}_batch_")]
        if not matched:
            missing_required_sections.append(f"缺少 required pass:{pass_name}")
            continue
        for row in matched:
            if row.get("status") not in {"success", "cache_hit"}:
                missing_required_sections.append("AI调用日志存在，但 required pass 未成功")
                break
            if row.get("fallback_used"):
                missing_required_sections.append("required pass fallback_used=true")
                break

    final_review_text = final_review_md.read_text(encoding="utf-8") if final_review_md.exists() else ""
    if "DELIVERABLE_STATUS: PASS" not in final_review_text and "可交付：是" not in final_review_text:
        missing_required_sections.append("final_codex_interpretation_review 未建议交付")
    if "FINAL_REVIEW_SCORE: 90" in final_review_text and "score\": 90" not in (quality_score_json.read_text(encoding="utf-8") if quality_score_json.exists() else "") and score < 90:
        missing_required_sections.append("final_review_score 存在默认 90 或托底 90")

    normalized_combined = re.sub(r"\s+", "", combined_text)
    draft_objects: list[dict[str, Any]] = []
    missing_draft_pages: list[int] = []
    diagnosis_seen: dict[str, int] = {}
    evidence_signature_seen: dict[str, int] = {}
    repeated_rate_errors: list[str] = []
    snippet_hits = 0
    previous_diag = ""
    repeat_streak = 0
    for page in page_plan:
        page_number = int(page.get("page_number") or 0)
        draft_path = report_dir / "page_drafts" / f"page_{page_number:03d}.json"
        if not draft_path.exists():
            missing_draft_pages.append(page_number)
            continue
        draft = json.loads(draft_path.read_text(encoding="utf-8"))
        draft_objects.append(draft)
        diagnosis = str(draft.get("diagnosis") or "")
        interpretation = str(draft.get("business_interpretation") or "")
        evidence = list(draft.get("evidence") or [])
        if len(re.findall(r"[\u4e00-\u9fff]", diagnosis)) < 180:
            missing_required_sections.append(f"page_{page_number:03d}.json diagnosis 长度不足")
        if len(re.findall(r"[\u4e00-\u9fff]", interpretation)) < 150:
            missing_required_sections.append(f"page_{page_number:03d}.json business_interpretation 长度不足")
        if any(not str(item.get("metric_id") or "").strip() for item in evidence):
            missing_required_sections.append("test_metric_id_required_for_claims")
        snippet = _extract_snippet(diagnosis) or _extract_snippet(interpretation)
        if snippet and snippet in normalized_combined:
            snippet_hits += 1
        diag_signature = _extract_snippet(diagnosis, max_len=80)
        diagnosis_seen[diag_signature] = diagnosis_seen.get(diag_signature, 0) + 1
        evidence_signature = "|".join(str(item.get("metric_id") or "") for item in evidence[:3])
        if evidence_signature:
            evidence_signature_seen[evidence_signature] = evidence_signature_seen.get(evidence_signature, 0) + 1
        if diag_signature and diag_signature == previous_diag:
            repeat_streak += 1
        else:
            repeat_streak = 1
            previous_diag = diag_signature
        if repeat_streak >= 3:
            repeated_rate_errors.append("连续 3 页同一句")
    if missing_draft_pages:
        missing_required_sections.append("PDF 只渲染 page_plan，未渲染 page_draft")
    if draft_objects:
        hit_rate = snippet_hits / len(draft_objects)
        if hit_rate < 0.9:
            missing_required_sections.append("AI page draft 未写入最终 PDF")
    else:
        hit_rate = 0.0
    if any(count >= 3 for count in diagnosis_seen.values()):
        repeated_rate_errors.append("diagnosis 相似度过高")
    if any(count >= max(5, len(draft_objects) // 3 if draft_objects else 5) for count in evidence_signature_seen.values()):
        repeated_rate_errors.append("evidence 重复使用过高")
    if repeated_rate_errors:
        missing_required_sections.append("页面重复率过高")

    score = int((_read_json(quality_score_json).get("score") or 0)) if quality_score_json.exists() else 0
    quality_gate_passed = bool((_read_json(quality_gate_json).get("passed")) if quality_gate_json.exists() else False)

    readability_text = (report_dir / "executive_readability_review.md").read_text(encoding="utf-8") if (report_dir / "executive_readability_review.md").exists() else ""
    rigor_text = (report_dir / "business_rigor_review.md").read_text(encoding="utf-8") if (report_dir / "business_rigor_review.md").exists() else ""
    if "SEVERE_ISSUES_FIXED: YES" not in readability_text and "严重问题：无" not in readability_text and "严重问题已修复" not in readability_text:
        missing_required_sections.append("executive_readability_review 严重问题未确认已修复")
    if "SEVERE_ISSUES_FIXED: YES" not in rigor_text and "严重问题：无" not in rigor_text and "严重问题已修复" not in rigor_text:
        missing_required_sections.append("business_rigor_review 严重问题未确认已修复")

    fail_items: list[str] = []
    if missing_outputs:
        fail_items.append(f"缺少输出文件：{', '.join(sorted(set(missing_outputs)))}")
    if forbidden_terms_found:
        fail_items.append(f"误套其他模板标题：{', '.join(forbidden_terms_found)}")
    fail_items.extend(field_boundary_errors)
    if missing_required_sections:
        fail_items.append(f"缺少必需章节或链路条件：{', '.join(missing_required_sections)}")
    fail_items.extend(action_table_errors)
    if score < 90:
        fail_items.append(f"score < 90: {score}")
    if not quality_gate_passed:
        fail_items.append("quality_gate_result.passed != true")

    return {
        "report_id": report_id,
        "business_profile": "generic_long_business_report",
        "passed": not fail_items,
        "score": score,
        "forbidden_terms_found": forbidden_terms_found,
        "field_boundary_errors": field_boundary_errors,
        "missing_required_sections": missing_required_sections,
        "action_table_errors": action_table_errors,
        "missing_outputs": sorted(set(missing_outputs)),
        "quality_gate_passed": quality_gate_passed,
        "ai_content_hit_rate": round(hit_rate, 4),
        "fail_items": fail_items,
    }


def validate_report_dir(report_dir: Path) -> dict[str, Any]:
    report_id = report_dir.name.replace("smart-report-", "")
    if _find_existing(
        report_dir,
        f"{report_id}-ecommerce_field_availability_registry.json",
        "ecommerce_field_availability_registry.json",
    ):
        return _validate_ecommerce(report_dir, report_id)
    if _find_existing(
        report_dir,
        f"{report_id}-generic_field_availability_registry.json",
        "generic_field_availability_registry.json",
    ):
        return _validate_generic_long(report_dir, report_id)
    if _find_existing(
        report_dir,
        f"{report_id}-internet_ops_field_availability_registry.json",
        "internet_ops_field_availability_registry.json",
    ):
        return _validate_internet_ops(report_dir, report_id)
    return _validate_procurement(report_dir, report_id)


def write_validation_outputs(report_dir: Path, result: dict[str, Any]) -> None:
    report_id = report_dir.name.replace("smart-report-", "")
    result_path = report_dir / f"{report_id}-independent_validator_result.json"
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    fail_md = report_dir / f"{report_id}-validator_fail_items.md"
    if result.get("passed"):
        if fail_md.exists():
            fail_md.unlink()
        return
    lines = ["# validator fail items", ""] + [f"- {item}" for item in result.get("fail_items") or ["unknown fail"]]
    fail_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-dir", required=True)
    args = parser.parse_args()
    result = validate_report_dir(Path(args.report_dir))
    write_validation_outputs(Path(args.report_dir), result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
