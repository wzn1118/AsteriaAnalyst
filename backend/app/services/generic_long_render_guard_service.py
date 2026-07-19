from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

from pypdf import PdfReader


GENERIC_LONG_REQUIRED_ACTION_COLUMNS = {
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

GENERIC_LONG_REQUIRED_7DAY_COLUMNS = {
    "动作",
    "负责人角色",
    "输入数据",
    "产出结果",
    "截止时间",
    "验证标准",
    "护栏指标",
}

GENERIC_LONG_REQUIRED_BACKLOG_COLUMNS = {
    "改进假设",
    "对象",
    "动作",
    "核心指标",
    "护栏指标",
    "样本要求",
    "数据依赖",
    "预计周期",
    "成功标准",
    "失败后处理",
}

GENERIC_LONG_REQUIRED_CHAIN_FILES = [
    "codex_interpretation_call_log.jsonl",
    "business_context_interpretation.md",
    "field_semantic_map.md",
    "metric_derivation_plan.json",
    "derived_metric_execution_review.md",
    "management_question_bank.md",
    "object_level_interpretation.md",
    "interpretation_conflict_check.md",
    "executive_readability_review.md",
    "business_rigor_review.md",
    "final_codex_interpretation_review.md",
]

WRONG_TEMPLATE_TOKENS = (
    "互联网运营数据分析报告",
    "内容运营数据分析报告",
    "用户增长数据分析报告",
    "社区运营数据分析报告",
    "渠道投放与增长运营复盘报告",
    "中文销售履约与商品经营复盘主报告",
    "销售履约与商品经营复盘",
    "ROI最高",
    "加大投放",
    "SKU经营复核",
)

TARGET_FORBIDDEN = ("目标达成", "KPI完成", "绩效优秀", "超额完成", "未达标")
AMOUNT_FORBIDDEN = ("ROI", "成本效率", "预算合理", "财务表现好")
TIME_FORBIDDEN = ("趋势改善", "持续增长", "持续下降", "同比", "环比")
QUALITY_FORBIDDEN = ("满意度高", "质量稳定", "问题改善", "服务质量稳定")
PEOPLE_FORBIDDEN = ("责任归因", "归责到", "某团队负责", "某个人负责")

PASS_MIN_LENGTHS = {
    "business_context_interpretation": 800,
    "field_semantic_map": 800,
    "metric_derivation_plan": 1000,
    "exploratory_interpretation": 1200,
    "object_level_interpretation": 1200,
    "long_report_page_plan": 2000,
    "page_generation_batch": 2000,
    "final_codex_interpretation_review": 800,
}


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
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


def _extract_pdf_text(path: Path) -> tuple[str, int]:
    if not path.exists():
        return ("", 0)
    reader = PdfReader(str(path))
    return ("\n".join(page.extract_text() or "" for page in reader.pages), len(reader.pages))


def _contains_any(text: str, terms: tuple[str, ...]) -> list[str]:
    return [term for term in terms if term in text]


def _page_draft_paths(report_dir: Path) -> list[Path]:
    page_drafts_dir = report_dir / "page_drafts"
    if not page_drafts_dir.exists():
        return []
    return sorted(page_drafts_dir.glob("page_*.json"))


def _extract_snippet(text: str, min_len: int = 20, max_len: int = 40) -> str:
    clean = re.sub(r"\s+", "", text or "")
    if len(clean) < min_len:
        return clean
    return clean[: max_len if len(clean) >= max_len else len(clean)]


def _snippet_hit_rate(page_drafts: list[dict[str, Any]], combined_text: str) -> tuple[float, list[int]]:
    normalized = re.sub(r"\s+", "", combined_text or "")
    misses: list[int] = []
    hits = 0
    for draft in page_drafts:
        diagnosis = _extract_snippet(str(draft.get("diagnosis") or ""))
        interpretation = _extract_snippet(str(draft.get("business_interpretation") or ""))
        found = (diagnosis and diagnosis in normalized) or (interpretation and interpretation in normalized)
        if found:
            hits += 1
        else:
            misses.append(int(draft.get("page_number") or 0))
    return ((hits / len(page_drafts)) if page_drafts else 0.0, misses)


def _validate_page_drafts(report_dir: Path) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    drafts: list[dict[str, Any]] = []
    for path in _page_draft_paths(report_dir):
        try:
            draft = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            errors.append(f"无法读取 page draft: {path.name}")
            continue
        drafts.append(draft)
        if len(re.findall(r"[\u4e00-\u9fff]", str(draft.get("diagnosis") or ""))) < 180:
            errors.append(f"{path.name} diagnosis 中文字数不足 180")
        if len(re.findall(r"[\u4e00-\u9fff]", str(draft.get("business_interpretation") or ""))) < 150:
            errors.append(f"{path.name} business_interpretation 中文字数不足 150")
        evidence = list(draft.get("evidence") or [])
        if draft.get("low_data_boundary_page"):
            if len(evidence) < 1:
                errors.append(f"{path.name} low_data_boundary_page 但 evidence < 1")
        elif len(evidence) < 2:
            errors.append(f"{path.name} evidence < 2")
        if any(not str(item.get("metric_id") or "").strip() for item in evidence):
            errors.append(f"{path.name} evidence 缺少 metric_id")
        if not str((draft.get("recommended_action") or {}).get("action") or "").strip():
            errors.append(f"{path.name} recommended_action.action 为空")
        if not str(draft.get("ai_content_hash") or "").strip():
            errors.append(f"{path.name} ai_content_hash 缺失")
    return drafts, errors


def _validate_call_log(report_dir: Path) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    rows = _call_log_rows(report_dir / "codex_interpretation_call_log.jsonl")
    if len(rows) < 12:
        errors.append(f"Codex/LLM 实际调用次数不足 12：{len(rows)}")
    page_calls = [row for row in rows if str(row.get("pass_name") or "").startswith("page_generation_batch_")]
    if len(page_calls) < 8:
        errors.append(f"页面级正文生成调用次数不足 8：{len(page_calls)}")
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
    pass_map: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        pass_map.setdefault(str(row.get("pass_name") or ""), []).append(row)
    for pass_name in required_passes:
        matched = [row for name, items in pass_map.items() for row in items if name == pass_name or name.startswith(f"{pass_name}_batch_")]
        if not matched:
            errors.append(f"缺少 required pass：{pass_name}")
            continue
        for row in matched:
            if row.get("status") not in {"success", "cache_hit"}:
                errors.append(f"required pass 未成功：{pass_name}")
            if row.get("fallback_used"):
                errors.append(f"required pass fallback_used=true：{pass_name}")
            if row.get("cache_used") and not row.get("cache_valid"):
                errors.append(f"required pass cache_used 但 cache_valid=false：{pass_name}")
            threshold = PASS_MIN_LENGTHS["page_generation_batch"] if str(row.get("pass_name") or "").startswith("page_generation_batch_") else PASS_MIN_LENGTHS.get(pass_name)
            if threshold and int(row.get("output_text_length") or 0) < threshold:
                errors.append(f"{row.get('pass_name')} output_text_length 低于阈值")
            if not row.get("output_json_valid"):
                errors.append(f"{row.get('pass_name')} output_json_valid=false")
            if not row.get("files_written"):
                errors.append(f"{row.get('pass_name')} files_written=false")
    return rows, errors


def _validate_ai_content_consumption(report_dir: Path, management_markdown: str) -> tuple[list[str], float, list[int]]:
    html_path = next(iter([path for path in [report_dir / f"{report_dir.name.replace('smart-report-','')}-management_report.html"] if path.exists()]), None)
    html_text = html_path.read_text(encoding="utf-8") if html_path and html_path.exists() else ""
    pdf_path = report_dir / f"{report_dir.name.replace('smart-report-','')}-management_report.pdf"
    pdf_text, _ = _extract_pdf_text(pdf_path)
    combined_text = f"{management_markdown}\n{html_text}\n{pdf_text}"
    drafts, draft_errors = _validate_page_drafts(report_dir)
    hit_rate, misses = _snippet_hit_rate(drafts, combined_text)
    errors = list(draft_errors)
    if drafts and hit_rate < 0.9:
        errors.append("AI page drafts were generated but not consumed by final PDF.")
    if "管理问题：" not in combined_text or "诊断判断：" not in combined_text or "指标推导：" not in combined_text or "业务解释：" not in combined_text or "建议动作：" not in combined_text:
        errors.append("management_report 未完整展示管理问题/诊断判断/指标推导/业务解释/建议动作")
    return errors, hit_rate, misses


def generic_long_quality_gate(
    *,
    report_dir: Path,
    management_markdown: str,
    total_pages: int,
    business_profile: str,
    field_registry: dict[str, Any],
    action_rows: list[dict[str, Any]],
    seven_day_rows: list[dict[str, Any]],
    backlog_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    fail_items: list[str] = []
    affected_sections: list[str] = []

    if business_profile != "generic_long_business_report":
        fail_items.append("business_profile 不是 generic_long_business_report")
        affected_sections.append("management_report")
    if not (35 <= total_pages <= 50):
        fail_items.append(f"management_report 页数不在 35-50 之间：{total_pages}")
        affected_sections.append("management_report")

    for file_name in GENERIC_LONG_REQUIRED_CHAIN_FILES:
        if not (report_dir / file_name).exists():
            fail_items.append(f"缺少解释链文件：{file_name}")
            affected_sections.append("codex_chain")

    log_rows, call_log_errors = _validate_call_log(report_dir)
    if call_log_errors:
        fail_items.extend(call_log_errors)
        affected_sections.append("codex_chain")

    wrong_templates = _contains_any(management_markdown, WRONG_TEMPLATE_TOKENS)
    if wrong_templates:
        fail_items.append(f"误套专用模板标题或术语：{', '.join(wrong_templates)}")
        affected_sections.append("management_report")

    if not field_registry.get("has_target_fields", False):
        target_terms = _contains_any(management_markdown, TARGET_FORBIDDEN)
        if target_terms:
            fail_items.append(f"缺 target_fields 却输出目标/KPI结论：{', '.join(target_terms)}")
            affected_sections.append("management_report")
    if not field_registry.get("has_amount_fields", False):
        amount_terms = _contains_any(management_markdown, AMOUNT_FORBIDDEN)
        if amount_terms:
            fail_items.append(f"缺 amount_fields 却输出财务效率结论：{', '.join(amount_terms)}")
            affected_sections.append("management_report")
    if not field_registry.get("has_time_fields", False):
        time_terms = _contains_any(management_markdown, TIME_FORBIDDEN)
        if time_terms:
            fail_items.append(f"缺 time_fields 却输出趋势结论：{', '.join(time_terms)}")
            affected_sections.append("management_report")
    if not field_registry.get("has_quality_fields", False):
        quality_terms = _contains_any(management_markdown, QUALITY_FORBIDDEN)
        if quality_terms:
            fail_items.append(f"缺 quality_fields 却输出质量结论：{', '.join(quality_terms)}")
            affected_sections.append("management_report")
    if not field_registry.get("has_people_fields", False):
        people_terms = _contains_any(management_markdown, PEOPLE_FORBIDDEN)
        if people_terms:
            fail_items.append(f"缺 people_fields 却输出责任归因：{', '.join(people_terms)}")
            affected_sections.append("management_report")

    if not action_rows or not GENERIC_LONG_REQUIRED_ACTION_COLUMNS.issubset(set(action_rows[0].keys())):
        fail_items.append("对象级行动表缺少负责人、时间、验证指标或成功标准")
        affected_sections.append("action_table")
    if not seven_day_rows or not GENERIC_LONG_REQUIRED_7DAY_COLUMNS.issubset(set(seven_day_rows[0].keys())):
        fail_items.append("7日动作表缺少负责人、截止时间或验证标准")
        affected_sections.append("7_day_action_table")
    if not backlog_rows or not GENERIC_LONG_REQUIRED_BACKLOG_COLUMNS.issubset(set(backlog_rows[0].keys())):
        fail_items.append("30日改进 backlog 缺少核心指标、护栏指标或成功标准")
        affected_sections.append("30_day_backlog")

    content_errors, hit_rate, misses = _validate_ai_content_consumption(report_dir, management_markdown)
    if content_errors:
        fail_items.extend(content_errors)
        affected_sections.append("ai_content_consumption")

    final_review_text = (report_dir / "final_codex_interpretation_review.md").read_text(encoding="utf-8") if (report_dir / "final_codex_interpretation_review.md").exists() else ""
    if "DELIVERABLE_STATUS: PASS" not in final_review_text:
        fail_items.append("final_codex_interpretation_review.md 未明确写出可交付")
        affected_sections.append("codex_chain")

    readability_text = (report_dir / "executive_readability_review.md").read_text(encoding="utf-8") if (report_dir / "executive_readability_review.md").exists() else ""
    rigor_text = (report_dir / "business_rigor_review.md").read_text(encoding="utf-8") if (report_dir / "business_rigor_review.md").exists() else ""
    if "SEVERE_ISSUES_FIXED: YES" not in readability_text:
        fail_items.append("executive_readability_review 严重问题未确认已修复")
        affected_sections.append("management_report")
    if "SEVERE_ISSUES_FIXED: YES" not in rigor_text:
        fail_items.append("business_rigor_review 严重问题未确认已修复")
        affected_sections.append("management_report")

    return {
        "passed": not fail_items,
        "business_profile": business_profile,
        "report_mode": str(field_registry.get("report_mode") or ""),
        "total_pages": total_pages,
        "fail_items": fail_items,
        "affected_sections": sorted(set(affected_sections)),
        "suggested_fixes": [] if not fail_items else [
            "required pass 必须全部为 success 且 fallback_used=false",
            "禁止使用 page_plan 模板句替代 page_draft 正文",
            "确保 metric_id、diagnosis、business_interpretation、recommended_action 真正进入 PDF/HTML",
            "若 AI 内容未进入最终报告，必须阻断 strict_90_pdf",
        ],
        "ai_content_hit_rate": round(hit_rate, 4),
        "ai_content_misses": misses,
    }


def generic_long_report_quality_scorer(
    *,
    report_dir: Path,
    management_markdown: str,
    total_pages: int,
    business_profile: str,
    field_registry: dict[str, Any],
    action_rows: list[dict[str, Any]],
    seven_day_rows: list[dict[str, Any]],
    backlog_rows: list[dict[str, Any]],
    gate_result: dict[str, Any],
) -> dict[str, Any]:
    hard_fail_items = list(gate_result.get("fail_items") or [])
    breakdown: dict[str, int] = {}

    breakdown["business_type_accuracy"] = 10 if business_profile == "generic_long_business_report" else 0
    breakdown["field_boundary_clarity"] = 10 if "字段边界：" in management_markdown and "数据边界：" in management_markdown else 0
    available = set(field_registry.get("available_field_groups") or [])
    coverage = sum(1 for key in ("volume_fields", "amount_fields", "progress_fields", "quality_fields", "conversion_fields") if key in available)
    breakdown["kpi_completeness"] = 10 if coverage >= 3 else 6 if coverage >= 2 else 3
    breakdown["object_level_quality"] = 15 if action_rows and len(action_rows) >= 5 else 0
    breakdown["missing_field_control"] = 15 if not any("缺 " in item or "缺" in item for item in hard_fail_items) else 0
    breakdown["actionability"] = 10 if action_rows and seven_day_rows else 0
    breakdown["roadmap_presence"] = 10 if seven_day_rows and backlog_rows else 0
    breakdown["pdf_integrity"] = 10 if 35 <= total_pages <= 50 else 0
    breakdown["executive_readability"] = 5 if "管理层摘要" in management_markdown else 0
    breakdown["forbidden_judgement_list"] = 5 if "禁止误判清单" in management_markdown else 0

    log_rows = _call_log_rows(report_dir / "codex_interpretation_call_log.jsonl")
    page_calls = [row for row in log_rows if str(row.get("pass_name") or "").startswith("page_generation_batch_")]
    breakdown["multi_pass_chain"] = 10 if len(log_rows) >= 12 and len(page_calls) >= 8 else 0

    content_errors, hit_rate, _ = _validate_ai_content_consumption(report_dir, management_markdown)
    breakdown["ai_content_consumption"] = 5 if not content_errors and hit_rate >= 0.9 else 0

    score = min(100, sum(breakdown.values()))
    if hard_fail_items:
        score = min(score, 89)
    return {
        "passed": score >= 90 and not hard_fail_items,
        "score": score,
        "breakdown": breakdown,
        "hard_fail_items": hard_fail_items,
        "business_profile": business_profile,
    }
