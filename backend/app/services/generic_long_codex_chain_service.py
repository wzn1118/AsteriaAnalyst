from __future__ import annotations

import hashlib
import json
import math
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from app.models import CodexRunRequest, SmartReportRequest
from app.services.codex_service import (
    codex_business_object_interpretation,
    codex_challenge_review,
    codex_complete_input_fields,
    codex_generic_business_rigor_review,
    codex_generic_exploratory_interpretation,
    codex_generic_final_review,
    codex_generic_long_page_plan,
    codex_generic_management_question_bank,
    codex_generic_metric_derivation_plan,
    codex_generic_page_generation_batch,
    codex_judge_feedback,
    codex_metric_interpretation,
    codex_semantic_analysis,
)
from app.services.codex_runtime_service import load_runtime_json_artifact
from app.services.codex_runtime_store import describe_artifact, write_json_artifact
from app.services.codex_runtime_task_service import get_codex_run_task
from app.services.dataset_service import build_column_summaries, clean_records, datetime_columns, numeric_columns
from app.services.derived_metric_usage_contract_service import (
    assert_derived_metric_usage_gate,
    collect_derived_metric_usage_contract,
    summarize_derived_metric_usage,
)
from app.services.settings_service import load_runtime_settings_raw


class RequiredPassFailure(RuntimeError):
    pass


PASS_MIN_LENGTHS: dict[str, int] = {
    "business_context_interpretation": 800,
    "field_semantic_map": 800,
    "metric_derivation_plan": 1000,
    "derived_metric_execution_review": 900,
    "management_question_bank": 1200,
    "exploratory_interpretation": 1200,
    "object_level_interpretation": 1200,
    "interpretation_conflict_check": 800,
    "long_report_page_plan": 2000,
    "page_generation_batch": 2000,
    "executive_readability_review": 800,
    "business_rigor_review": 800,
    "final_codex_interpretation_review": 800,
}

REQUIRED_PASS_NAMES = [
    "business_context_interpretation",
    "field_semantic_map",
    "metric_derivation_plan",
    "derived_metric_execution_review",
    "management_question_bank",
    "exploratory_interpretation",
    "object_level_interpretation",
    "interpretation_conflict_check",
    "long_report_page_plan",
    "page_generation_batch",
    "executive_readability_review",
    "business_rigor_review",
    "final_codex_interpretation_review",
]

RECHECK_FILES = (
    "generic_field_availability_registry.json",
    "generic_object_decision_registry.csv",
    "generic_action_table.csv",
    "7_day_action_table.csv",
    "30_day_improvement_backlog.csv",
    "report_quality_score.json",
    "quality_gate_result.json",
    "management_report.html",
)

PAGE_PLAN_CONTRACT_FILENAME = "page_plan.json"
PAGE_DRAFTS_CONTRACT_FILENAME = "page_drafts.json"
PAGE_PLAN_SCHEMA_FILENAME = "page_plan.schema.json"
PAGE_DRAFTS_SCHEMA_FILENAME = "page_drafts.schema.json"

PAGE_PLAN_CONTRACT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["pages"],
    "properties": {
        "pages": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "page_number",
                    "page_title",
                    "management_question",
                    "page_purpose",
                    "required_metrics",
                    "required_dimensions",
                    "available_fields",
                    "derived_metrics",
                    "evidence_query",
                    "objects_to_discuss",
                    "allowed_claim_types",
                    "forbidden_claim_types",
                    "required_table_or_chart",
                    "action_type",
                    "source_passes",
                ],
            },
        }
    },
}

PAGE_DRAFTS_CONTRACT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["pages"],
    "properties": {
        "pages": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "page_number",
                    "page_title",
                    "management_question",
                    "diagnosis",
                    "evidence",
                    "derived_metrics_used",
                    "derived_metric_explanation",
                    "business_interpretation",
                    "recommended_action",
                    "data_limitations",
                    "forbidden_misreadings",
                    "source_passes",
                    "low_data_boundary_page",
                    "ai_content_hash",
                ],
            },
        }
    },
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_jsonable(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        text = _safe_text(item)
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _count_cjk(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text or ""))


def _to_request_dict(request: SmartReportRequest | dict[str, Any]) -> dict[str, Any]:
    if isinstance(request, SmartReportRequest):
        return request.model_dump()
    return dict(request)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _generic_long_runtime_enabled(runtime_child_task_creator: Callable[..., dict[str, Any]] | None) -> bool:
    if runtime_child_task_creator is None:
        return False
    try:
        settings = load_runtime_settings_raw()
    except Exception:
        return False
    return bool(settings.get("codex_runtime_enabled", False))


def _write_contract_schema_files(report_dir: Path) -> list[Path]:
    return [
        write_json_artifact(report_dir / PAGE_PLAN_SCHEMA_FILENAME, PAGE_PLAN_CONTRACT_SCHEMA),
        write_json_artifact(report_dir / PAGE_DRAFTS_SCHEMA_FILENAME, PAGE_DRAFTS_CONTRACT_SCHEMA),
    ]


def _plan_page_numbers(pages: list[dict[str, Any]]) -> list[int]:
    return [int(page.get("page_number") or 0) for page in pages if int(page.get("page_number") or 0) > 0]


def _validate_page_draft_batch_subset(drafts: list[dict[str, Any]], page_plan_batch: list[dict[str, Any]]) -> bool:
    if not drafts or not page_plan_batch:
        return False
    batch_numbers = set(_plan_page_numbers(page_plan_batch))
    subset = [draft for draft in drafts if int(draft.get("page_number") or 0) in batch_numbers]
    if len(subset) != len(batch_numbers):
        return False
    return _validate_page_drafts(subset, page_plan_batch)


def _merge_page_draft_contract(existing_pages: list[dict[str, Any]], new_pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[int, dict[str, Any]] = {}
    for draft in existing_pages:
        page_number = int(draft.get("page_number") or 0)
        if page_number:
            merged[page_number] = dict(draft)
    for draft in new_pages:
        page_number = int(draft.get("page_number") or 0)
        if page_number:
            merged[page_number] = dict(draft)
    return [merged[number] for number in sorted(merged)]


def _runtime_stage_user_requirement(request_payload: dict[str, Any], default_text: str) -> str:
    return (
        _safe_text(request_payload.get("user_requirement"))
        or _safe_text(request_payload.get("problem_to_solve"))
        or _safe_text(request_payload.get("core_purpose"))
        or default_text
    )


def _run_runtime_json_stage(
    *,
    report_dir: Path,
    request_payload: dict[str, Any],
    runtime_child_task_creator: Callable[..., dict[str, Any]] | None,
    parent_report_id: str,
    stage_id: str,
    purpose: str,
    artifact_name: str,
    prompt_template: str,
    context_payload: dict[str, Any],
    validator: Callable[[dict[str, Any]], bool],
) -> dict[str, Any] | None:
    if not _generic_long_runtime_enabled(runtime_child_task_creator):
        return None
    report_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = report_dir / artifact_name
    if artifact_path.exists():
        try:
            artifact_path.unlink()
        except Exception:
            pass
    try:
        request_model = CodexRunRequest(
            workspace_path=str(report_dir.resolve()),
            prompt_template=prompt_template,
            user_requirement=_runtime_stage_user_requirement(request_payload, purpose),
            context_payload=context_payload,
            report_id=parent_report_id,
            parent_report_id=parent_report_id,
            parent_stage_id=stage_id,
            dataset_id=_safe_text(context_payload.get("dataset_name")),
            sheet_name=_safe_text(context_payload.get("sheet_name")),
            stage_id=stage_id,
            purpose=purpose,
            artifact_source=artifact_name,
            capture_git_diff=False,
        )
        try:
            child_task = runtime_child_task_creator(
                request_model,
                parent_report_id=parent_report_id,
                parent_stage_id=stage_id,
                stage_id=stage_id,
                purpose=purpose,
                artifact_source=artifact_name,
            )
        except TypeError:
            # Older in-process test hooks and lightweight callers only accept the
            # original small keyword set. Retry without the newer trace fields so
            # the real runtime path remains reachable instead of silently falling
            # back to the local runner.
            child_task = runtime_child_task_creator(
                request_model,
                parent_report_id=parent_report_id,
                stage_id=stage_id,
                purpose=purpose,
            )
    except Exception:
        return None
    child_job_id = _safe_text(child_task.get("job_id"))
    if not child_job_id:
        return None
    deadline = datetime.now(timezone.utc).timestamp() + 240.0
    latest = dict(child_task)
    while datetime.now(timezone.utc).timestamp() < deadline:
        try:
            snapshot = get_codex_run_task(child_job_id)
        except Exception:
            return None
        latest = dict(snapshot)
        status = _safe_text(snapshot.get("status")).lower()
        if status in {"completed", "failed", "cancelled", "timed_out"}:
            break
        time.sleep(0.5)
    else:
        return None
    if _safe_text(latest.get("status")).lower() != "completed":
        return None
    try:
        payload = load_runtime_json_artifact(
            report_dir,
            artifact_name,
            required_keys=["pages"],
        )
    except Exception:
        return None
    if not validator(payload):
        return None
    payload["runtime_child_job_id"] = child_job_id
    payload["runtime_child_run_id"] = _safe_text(latest.get("run_id"))
    payload["author_mode"] = "codex_cli_runtime"
    payload["runtime_state"] = "live"
    payload["degradation_state"] = "none"
    payload["artifact_source"] = artifact_name
    return payload


def _write_markdown(path: Path, title: str, sections: list[tuple[str, list[str] | str]]) -> None:
    lines = [f"# {title}", ""]
    for heading, body in sections:
        lines.append(f"## {heading}")
        lines.append("")
        if isinstance(body, str):
            lines.append(body)
        else:
            for item in body:
                lines.append(f"- {item}")
        lines.append("")
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def _tracked_dependency_state(report_dir: Path) -> dict[str, str]:
    state: dict[str, str] = {}
    for name in RECHECK_FILES:
        path = report_dir / name
        state[name] = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else "missing"
    return state


def _is_fallback_result(result: dict[str, Any]) -> bool:
    mode = _safe_text(result.get("mode")).lower()
    runtime_state = _safe_text(result.get("runtime_state")).lower()
    degradation = _safe_text(result.get("degradation_state")).lower()
    return "fallback" in mode or runtime_state == "fallback" or "fallback" in degradation


def _estimate_tokens(payload: dict[str, Any]) -> int:
    return max(1, math.ceil(len(json.dumps(payload, ensure_ascii=False, default=str)) / 4))


def _runner_name(runner: Callable[..., Any]) -> str:
    return getattr(runner, "__name__", runner.__class__.__name__)


def _cache_key(pass_name: str, payload: dict[str, Any], dependency_state: dict[str, str]) -> str:
    return _hash_jsonable({"pass_name": pass_name, "payload": payload, "dependency_state": dependency_state})


def _load_cache(cache_dir: Path, key: str) -> dict[str, Any] | None:
    path = cache_dir / f"{key}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _save_cache(cache_dir: Path, key: str, payload: dict[str, Any]) -> None:
    _write_json(cache_dir / f"{key}.json", payload)


def _append_call_log(path: Path, record: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _choose_entity_column(frame: pd.DataFrame) -> str | None:
    lower_map = {str(column).lower(): str(column) for column in frame.columns}
    preferred = [
        "project_name",
        "project",
        "customer_name",
        "customer",
        "department",
        "team",
        "region",
        "service",
        "task_name",
        "task",
        "course_name",
        "course",
        "entity_name",
        "entity_id",
    ]
    for item in preferred:
        if item in lower_map:
            return lower_map[item]
    for column in frame.columns.astype(str):
        lowered = column.lower()
        if any(token in lowered for token in ("project", "customer", "department", "team", "region", "service", "task", "course", "entity")):
            return column
    return None


def _top_entities(frame: pd.DataFrame, entity_column: str | None, limit: int = 30) -> list[dict[str, Any]]:
    if not entity_column or entity_column not in frame.columns:
        return []
    counts = frame[entity_column].astype(str).value_counts(dropna=True).head(limit)
    return [
        {
            "object_id": str(name),
            "object_name": str(name),
            "record_count": int(count),
        }
        for name, count in counts.items()
    ]


def _available_missing_groups(field_registry: dict[str, Any]) -> tuple[list[str], list[str]]:
    available = [str(item) for item in field_registry.get("available_field_groups") or []]
    missing = [str(item) for item in field_registry.get("missing_field_groups") or []]
    return available, missing


def _generic_question_seed(field_registry: dict[str, Any]) -> list[dict[str, Any]]:
    available, missing = _available_missing_groups(field_registry)
    mapping = [
        ("当前总体规模和结构是什么", "这是管理层判断经营盘子的起点", "数据范围与字段可用性", ["entity_fields", "volume_fields"], "先做对象与结构复核"),
        ("最重要的主对象是谁", "主对象决定后续拆解粒度", "主对象识别", ["entity_fields"], "统一主对象口径"),
        ("当前指标体系是否完整", "没有指标树就难以进入动作", "指标体系搭建", ["volume_fields", "amount_fields", "progress_fields", "quality_fields"], "先补缺口后升级结论"),
        ("整体表现有没有异常", "异常往往对应风险对象", "当前整体表现", ["volume_fields", "quality_fields"], "优先抽检异常对象"),
        ("是否能看时间变化", "趋势决定复核窗口", "时间趋势分析", ["time_fields", "volume_fields"], "无时间字段时先补日期口径"),
        ("哪些对象规模大但效率待验证", "大对象更影响经营结果", "对象结构分析", ["entity_fields", "volume_fields"], "优先复核头部对象"),
        ("哪些分类维度最影响结果分布", "分类结构决定资源是否失衡", "分类结构分析", ["category_fields"], "锁定结构失衡维度"),
        ("地区之间是否存在显著差异", "空间差异影响资源配置", "地区/空间分析", ["geography_fields"], "缺地域字段时不下地区结论"),
        ("金额与预算结构是否合理", "关系到财务健康", "金额/预算分析", ["amount_fields"], "缺金额时只做规模分析"),
        ("进度与完成率是否失衡", "执行异常需要尽快复核", "进度/完成分析", ["progress_fields", "time_fields"], "补执行阶段字段"),
        ("质量与满意度是否稳定", "质量问题会放大经营风险", "质量/满意度分析", ["quality_fields"], "缺质量字段时不下质量判断"),
        ("是否存在关键转化断点", "转化链决定后续动作", "转化/流转分析", ["conversion_fields"], "补链路字段后复核"),
        ("负责人和团队表现差异是否明显", "组织管理需要责任主体", "负责人/团队分析", ["people_fields", "entity_fields"], "无负责人字段时不归责"),
        ("文本反馈透露哪些主题候选", "反馈是问题诊断补充", "文本反馈主题分析", ["text_feedback_fields"], "未分类文本只作候选主题"),
        ("高风险对象集中在哪里", "短期动作顺序由风险对象决定", "异常对象识别", ["entity_fields", "quality_fields", "progress_fields"], "先锁定复核名单"),
        ("哪些对象最值得优先复核", "管理层需要明确复核名单", "重点对象复核表", ["entity_fields"], "生成对象级复核表"),
        ("当前最重要的管理问题是什么", "问题诊断决定路线图", "管理问题诊断", ["entity_fields", "volume_fields"], "按问题派单"),
        ("未来7天先做什么", "短周期动作决定执行推进", "7日动作表", ["people_fields"], "动作必须带负责人和时间"),
        ("未来30天验证哪些改进假设", "中期 backlog 决定实验顺序", "30日改进 backlog", ["target_fields", "time_fields"], "写清样本要求和指标"),
        ("哪些结论当前绝对不能下", "禁止误判清单是最后保险", "禁止误判清单", ["target_fields", "amount_fields", "time_fields", "quality_fields", "people_fields"], "把高风险结论全部降级"),
    ]
    rows = []
    for index, item in enumerate(mapping, start=1):
        required_fields = item[3]
        can_answer_now = "可以" if set(required_fields).issubset(set(available)) else "部分可答" if any(field in available for field in required_fields) else "不可判断"
        rows.append(
            {
                "priority": index,
                "business_question": item[0],
                "why_it_matters": item[1],
                "can_answer_now": can_answer_now,
                "required_fields": required_fields,
                "report_section": item[2],
                "management_action": item[4],
            }
        )
    if missing:
        rows.append(
            {
                "priority": 21,
                "business_question": f"由于字段缺口，当前不能回答哪些问题",
                "why_it_matters": "先把不可判断边界说清楚，避免越权结论",
                "can_answer_now": "可以",
                "required_fields": missing[:6],
                "report_section": "禁止误判清单",
                "management_action": "先补字段，再升级结论",
            }
        )
    return rows[:20]


def _normalize_metric_id(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]+", "_", _safe_text(text).lower()).strip("_")
    return cleaned or "metric"


def _build_metric_candidates(frame: pd.DataFrame, field_registry: dict[str, Any]) -> list[dict[str, Any]]:
    cols = {str(column).lower(): str(column) for column in frame.columns}
    candidates: list[dict[str, Any]] = []
    time_col = next((cols[key] for key in cols if any(token in key for token in ("date", "month", "quarter", "year"))), None)
    user_col = next((cols[key] for key in cols if "user_id" in key or key == "user"), None)
    budget_col = next((cols[key] for key in cols if "budget" in key), None)
    spend_col = next((cols[key] for key in cols if "spend" in key or "cost" in key or "expense" in key), None)
    sales_col = next((cols[key] for key in cols if "sales" in key or "revenue" in key or "amount" in key), None)
    order_col = next((cols[key] for key in cols if "order_count" in key or "order" == key or "count" == key), None)
    progress_col = next((cols[key] for key in cols if "progress" in key or "completion" in key), None)
    quality_col = next((cols[key] for key in cols if "score" in key or "rating" in key or "satisfaction" in key), None)
    issue_col = next((cols[key] for key in cols if "issue" in key or "complaint" in key or "risk" in key), None)
    entity_col = _choose_entity_column(frame)

    def add(metric_name: str, formula: str, source_fields: list[str], business_value: str, claim_strength: str = "medium") -> None:
        candidates.append(
            {
                "metric_id": _normalize_metric_id(metric_name),
                "metric_name": metric_name,
                "formula": formula,
                "source_fields": source_fields,
                "business_value": business_value,
                "claim_strength": claim_strength,
            }
        )

    if time_col and user_col:
        add("active_users_by_period", f"按 {time_col} 去重 {user_col}", [time_col, user_col], "识别活跃规模与波动")
        add("activity_volatility", f"{time_col} 维度下活跃规模波动", [time_col, user_col], "识别异常波动与节奏风险", "weak")
    if time_col and sales_col:
        add("latest_period_change", f"按 {time_col} 比较 {sales_col} 最近窗口变化", [time_col, sales_col], "识别短期变化与拐点", "medium")
    if budget_col and spend_col:
        add("spend_rate", f"{spend_col}/{budget_col}", [budget_col, spend_col], "判断预算执行率")
        add("budget_gap", f"{budget_col}-{spend_col}", [budget_col, spend_col], "判断预算偏差")
        add("overspend_flag", f"{spend_col}>{budget_col}", [budget_col, spend_col], "识别超支风险", "weak")
    if sales_col and order_col:
        add("average_order_value", f"{sales_col}/{order_col}", [sales_col, order_col], "衡量单笔产出效率")
        add("sales_contribution", f"各对象 {sales_col} 占比", [sales_col, entity_col or sales_col], "识别头部贡献结构", "medium")
    if entity_col and sales_col:
        add("top_entity_share", f"头部 {entity_col} 的 {sales_col} 占比", [entity_col, sales_col], "识别结构集中度", "medium")
    if entity_col and progress_col:
        add("entity_progress_gap", f"各 {entity_col} 的 {progress_col} 差异", [entity_col, progress_col], "识别执行失衡")
    if entity_col and quality_col:
        add("entity_quality_gap", f"各 {entity_col} 的 {quality_col} 差异", [entity_col, quality_col], "识别质量差异")
    if entity_col and issue_col:
        add("entity_issue_density", f"各 {entity_col} 的 {issue_col} 暴露强度", [entity_col, issue_col], "识别高风险对象", "weak")

    if not candidates:
        numeric_cols = numeric_columns(frame)
        for column in numeric_cols[:8]:
            add(f"{column}_level", f"直接读取 {column}", [column], "作为通用经营观察指标", "weak")
    return candidates[:24]


def _compute_metric_rows(frame: pd.DataFrame, metric_candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    cols = {str(column).lower(): str(column) for column in frame.columns}
    for candidate in metric_candidates:
        metric_id = candidate["metric_id"]
        metric_name = candidate["metric_name"]
        source_fields = candidate["source_fields"]
        value = "待补数据"
        comparison = "当前无稳定对比口径"
        evidence_strength = "medium"
        try:
            if metric_id == "spend_rate":
                budget = pd.to_numeric(frame[source_fields[0]], errors="coerce")
                spend = pd.to_numeric(frame[source_fields[1]], errors="coerce")
                ratio = float((spend.sum() / budget.sum())) if budget.sum() else 0.0
                value = f"{ratio:.4f}"
                comparison = "1.0 为预算完全消耗的参考值"
            elif metric_id == "budget_gap":
                budget = pd.to_numeric(frame[source_fields[0]], errors="coerce")
                spend = pd.to_numeric(frame[source_fields[1]], errors="coerce")
                gap = float((budget.sum() - spend.sum()))
                value = f"{gap:.2f}"
                comparison = "正值代表预算剩余，负值代表超支"
            elif metric_id == "average_order_value":
                sales = pd.to_numeric(frame[source_fields[0]], errors="coerce")
                orders = pd.to_numeric(frame[source_fields[1]], errors="coerce")
                aov = float((sales.sum() / orders.sum())) if orders.sum() else 0.0
                value = f"{aov:.2f}"
                comparison = "与整体均值对照"
            elif metric_id == "top_entity_share":
                entity = frame[source_fields[0]].astype(str)
                metric = pd.to_numeric(frame[source_fields[1]], errors="coerce").fillna(0)
                top_share = float(metric.groupby(entity).sum().sort_values(ascending=False).head(1).sum() / metric.sum()) if metric.sum() else 0.0
                value = f"{top_share:.4f}"
                comparison = "越高代表结构越集中"
            elif metric_id == "sales_contribution":
                entity = frame[source_fields[1]].astype(str) if source_fields[1] in frame.columns else None
                metric = pd.to_numeric(frame[source_fields[0]], errors="coerce").fillna(0)
                if entity is not None and metric.sum():
                    top_share = float(metric.groupby(entity).sum().sort_values(ascending=False).head(3).sum() / metric.sum())
                    value = f"{top_share:.4f}"
                    comparison = "Top3 对象贡献占比"
                else:
                    value = f"{metric.sum():.2f}"
            elif metric_id == "active_users_by_period":
                time_col, user_col = source_fields[0], source_fields[1]
                grouped = frame.groupby(time_col)[user_col].nunique(dropna=True)
                value = f"{float(grouped.iloc[-1]) if not grouped.empty else 0:.0f}"
                comparison = "最近期活跃用户数"
            elif metric_id == "latest_period_change":
                time_col, metric_col = source_fields[0], source_fields[1]
                grouped = pd.to_numeric(frame[metric_col], errors="coerce").groupby(frame[time_col]).sum()
                if len(grouped) >= 2 and grouped.iloc[-2] != 0:
                    change = float((grouped.iloc[-1] - grouped.iloc[-2]) / grouped.iloc[-2])
                    value = f"{change:.4f}"
                    comparison = "最近期相较上一期的变化率"
                else:
                    value = f"{float(grouped.iloc[-1]) if len(grouped) else 0:.2f}"
            elif metric_id == "activity_volatility":
                time_col, user_col = source_fields[0], source_fields[1]
                grouped = frame.groupby(time_col)[user_col].nunique(dropna=True)
                value = f"{float(grouped.std()) if len(grouped) > 1 else 0:.2f}"
                comparison = "越高说明波动越强"
            elif source_fields and source_fields[0] in frame.columns:
                series = pd.to_numeric(frame[source_fields[0]], errors="coerce")
                value = f"{float(series.mean()) if series.notna().any() else 0:.2f}"
                comparison = f"{source_fields[0]} 平均值"
        except Exception:
            evidence_strength = "low"
        rows.append(
            {
                "metric_id": metric_id,
                "metric_name": metric_name,
                "formula": candidate["formula"],
                "source_fields": source_fields,
                "value": value,
                "comparison": comparison,
                "evidence_strength": evidence_strength,
                "claim_strength": candidate.get("claim_strength", "weak"),
            }
        )
    return rows


def _field_semantic_rows(frame: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    summaries = build_column_summaries(frame)
    time_cols = set(datetime_columns(frame))
    entity_column = _choose_entity_column(frame)
    for summary in summaries:
        name = str(summary.get("name") or "")
        dtype = str(summary.get("dtype") or "").lower()
        metric_type = "分类维度"
        if name == entity_column:
            metric_type = "对象维度"
        elif name in time_cols:
            metric_type = "时间维度"
        elif any(token in dtype for token in ("int", "float", "bool")):
            metric_type = "数值指标"
        elif any(len(str(item)) > 16 for item in summary.get("sample_values") or []):
            metric_type = "文本反馈"
        usable_for = ["结构分析", "对象比较"]
        not_usable_for = []
        if metric_type == "时间维度":
            usable_for = ["趋势分析", "节奏分析"]
            not_usable_for = ["责任归因"]
        elif metric_type == "数值指标":
            usable_for = ["规模分析", "效率分析", "异常识别"]
            not_usable_for = ["因果证明"]
        elif metric_type == "文本反馈":
            usable_for = ["主题候选识别", "问题样本抽检"]
            not_usable_for = ["总体事实结论"]
        rows.append(
            {
                "field_name": name,
                "guessed_business_meaning": metric_type,
                "metric_type": metric_type,
                "usable_for": usable_for,
                "not_usable_for": not_usable_for,
                "needs_manual_confirmation": metric_type in {"对象维度", "文本反馈"},
                "risk_note": "需要结合样例值和分布人工复核" if metric_type in {"对象维度", "文本反馈"} else "按当前样例分布做初步解释",
                "sample_values": summary.get("sample_values", []),
                "missing_ratio": summary.get("missing_ratio"),
                "unique_count": summary.get("unique_count"),
                "dtype": summary.get("dtype"),
            }
        )
    return rows


def _build_kpi_tree_from_metrics(metric_rows: list[dict[str, Any]], field_registry: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    buckets: dict[str, list[dict[str, Any]]] = {
        "规模指标": [],
        "结构指标": [],
        "效率指标": [],
        "质量指标": [],
        "进度指标": [],
        "金额指标": [],
        "转化指标": [],
        "风险指标": [],
    }
    for row in metric_rows:
        metric_id = str(row.get("metric_id") or "")
        metric_name = str(row.get("metric_name") or "")
        target_bucket = "结构指标"
        lowered = f"{metric_id} {metric_name}".lower()
        if any(token in lowered for token in ("count", "share", "contribution", "用户", "数量", "人数")):
            target_bucket = "规模指标"
        elif any(token in lowered for token in ("rate", "gap", "average", "效率")):
            target_bucket = "效率指标"
        elif any(token in lowered for token in ("quality", "satisfaction", "score", "issue")):
            target_bucket = "质量指标"
        elif any(token in lowered for token in ("progress", "completion")):
            target_bucket = "进度指标"
        elif any(token in lowered for token in ("budget", "spend", "amount", "cost", "sales")):
            target_bucket = "金额指标"
        elif any(token in lowered for token in ("conversion", "complete", "renew")):
            target_bucket = "转化指标"
        elif any(token in lowered for token in ("risk", "volatility", "flag", "issue")):
            target_bucket = "风险指标"
        buckets[target_bucket].append(
            {
                "metric": metric_name,
                "metric_id": metric_id,
                "value": row.get("value"),
                "comparison": row.get("comparison"),
                "evidence_strength": row.get("evidence_strength"),
            }
        )
    missing = set(field_registry.get("missing_field_groups") or [])
    if "amount_fields" in missing:
        buckets["金额指标"].append(
            {
                "metric": "金额字段缺口",
                "metric_id": "missing_amount_fields",
                "value": "待补",
                "comparison": "缺少金额字段",
                "evidence_strength": "low",
            }
        )
    if "time_fields" in missing:
        buckets["进度指标"].append(
            {
                "metric": "时间字段缺口",
                "metric_id": "missing_time_fields",
                "value": "待补",
                "comparison": "缺少时间字段",
                "evidence_strength": "low",
            }
        )
    if "quality_fields" in missing:
        buckets["质量指标"].append(
            {
                "metric": "质量字段缺口",
                "metric_id": "missing_quality_fields",
                "value": "待补",
                "comparison": "缺少质量字段",
                "evidence_strength": "low",
            }
        )
    return buckets


def _build_business_context(raw_result: dict[str, Any], dataset_name: str, sheet_name: str, request_payload: dict[str, Any], field_registry: dict[str, Any], entity_column: str | None) -> dict[str, Any]:
    available, missing = _available_missing_groups(field_registry)
    possible = [
        f"当前按 `{field_registry.get('report_mode', 'generic_management_review')}` 口径优先解释",
        "这是无法稳定归入采销、电商、互联网运营或媒体投放模板的通用经营分析数据",
        "报告需要围绕对象结构、效率、质量、进度和风险建立管理诊断",
    ]
    management_questions = [
        request_payload.get("problem_to_solve") or "当前最重要的经营问题是什么",
        "哪些对象最值得优先复核",
        "未来7天谁做什么，30天验证哪些改进假设",
    ]
    readability_fixed = bool(readability_review.get("fixed_status"))
    rigor_fixed = bool(rigor_review.get("fixed_status"))
    final_review_score = int(final_review.get("total_score") or 0)

    return {
        "possible_business_scenarios": _dedupe(possible),
        "core_object_grain": entity_column or "当前未识别稳定主对象字段",
        "management_questions": _dedupe([question for question in management_questions if _safe_text(question)])[:5],
        "supported_questions": [
            f"当前可判断字段组：{', '.join(available[:8]) or '无'}",
            "可以做对象结构、分类结构和风险对象复核",
            *([ "可以做时间趋势与节奏分析" ] if "time_fields" in available else []),
            *([ "可以做金额/预算结构分析" ] if "amount_fields" in available else []),
            *([ "可以做质量与问题分布分析" ] if "quality_fields" in available else []),
        ],
        "unsupported_questions": [
            *([ "缺 target_fields，不能判断目标达成/KPI完成" ] if "target_fields" in missing else []),
            *([ "缺 amount_fields，不能判断 ROI/成本效率/预算合理性" ] if "amount_fields" in missing else []),
            *([ "缺 time_fields，不能判断趋势/同比/环比" ] if "time_fields" in missing else []),
            *([ "缺 quality_fields，不能判断满意度高/质量稳定" ] if "quality_fields" in missing else []),
            *([ "缺 people_fields，不能做责任归因" ] if "people_fields" in missing else []),
        ],
        "ambiguity_points": [
            "如果字段同时命中多个业务模板但没有明确主对象，必须继续留在 generic_long 主链",
            "文本反馈只能作为主题候选，不能直接写成整体事实",
            f"AI 输入补齐结果仅作为业务背景补完，不替代字段边界判断：{_safe_text(raw_result.get('completed_problem_to_solve')) or '无'}",
        ],
    }


def _build_question_bank(raw_result: dict[str, Any], field_registry: dict[str, Any]) -> list[dict[str, Any]]:
    seed = _generic_question_seed(field_registry)
    refined_problem = _safe_text(raw_result.get("refined_problem"))
    if refined_problem:
        seed.insert(
            0,
            {
                "priority": 0,
                "business_question": refined_problem,
                "why_it_matters": _safe_text(raw_result.get("refined_purpose")) or "这是当前报告最优先要回答的管理问题",
                "can_answer_now": "部分可答",
                "required_fields": ["entity_fields", "volume_fields"],
                "report_section": "管理层摘要",
                "management_action": _safe_text(raw_result.get("next_step")) or "围绕这个问题组织全文",
            },
        )
    return seed[:20]


def _build_exploratory(frame: pd.DataFrame, raw_result: dict[str, Any], field_registry: dict[str, Any], metric_rows: list[dict[str, Any]], object_registry_rows: list[dict[str, Any]]) -> dict[str, Any]:
    findings = [str(item) for item in raw_result.get("pattern_findings") or [] if _safe_text(item)]
    anomalies = [str(item) for item in raw_result.get("anomaly_findings") or [] if _safe_text(item)]
    reasons = [str(item) for item in raw_result.get("drilldown_prompts") or [] if _safe_text(item)]
    if metric_rows:
        findings.extend([f"{row['metric_name']} 当前值 {row['value']}；比较口径：{row['comparison']}" for row in metric_rows[:4]])
    if object_registry_rows:
        anomalies.append(f"已识别 {len(object_registry_rows)} 个对象进入对象级注册表")
    return {
        "main_findings": _dedupe(findings)[:8],
        "anomalies": _dedupe(anomalies)[:6],
        "possible_reasons": _dedupe(reasons)[:6],
        "missing_fields": list(field_registry.get("missing_field_groups") or []),
        "cannot_conclude": [
            *([ "缺 target_fields，不能判断目标达成" ] if not field_registry.get("has_target_fields", False) else []),
            *([ "缺 amount_fields，不能判断 ROI/成本效率" ] if not field_registry.get("has_amount_fields", False) else []),
            *([ "缺 time_fields，不能判断趋势变化" ] if not field_registry.get("has_time_fields", False) else []),
            *([ "缺 quality_fields，不能判断质量改善" ] if not field_registry.get("has_quality_fields", False) else []),
        ],
        "next_validations": ["围绕字段缺口、对象异常和关键指标先做验证动作"],
    }


def _build_object_rows(raw_result: dict[str, Any], registry_rows: list[dict[str, Any]], field_registry: dict[str, Any], batch_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    headline = _safe_text(raw_result.get("headline")) or "当前对象进入经营复核名单"
    findings = list(raw_result.get("drilldown_findings") or [])
    rows: list[dict[str, Any]] = []
    registry_lookup = {str(row.get("object_id") or ""): row for row in registry_rows}
    for index, batch_row in enumerate(batch_rows, start=1):
        object_id = _safe_text(batch_row.get("object_id") or batch_row.get("object_name"))
        registry_row = registry_lookup.get(object_id, {})
        finding = findings[index - 1] if index - 1 < len(findings) and isinstance(findings[index - 1], dict) else {}
        rows.append(
            {
                "object_id": object_id,
                "object_name": _safe_text(batch_row.get("object_name") or object_id),
                "performance_summary": _safe_text(finding.get("deeper_read")) or headline,
                "trigger_evidence": _safe_text(registry_row.get("evidence_summary") or batch_row.get("record_count") or finding.get("trigger_finding") or "对象样本量与结构差异"),
                "possible_issues": [ _safe_text(finding.get("title")) or "当前存在结构与风险复核空间" ],
                "possible_opportunities": [ _safe_text(finding.get("business_move")) or "若补齐关键字段，可升级为改进实验候选" ],
                "missing_fields": list(registry_row.get("missing_fields") or field_registry.get("missing_field_groups") or []),
                "final_label_suggestion": _safe_text(registry_row.get("final_label")) or "改进实验候选",
                "final_action_suggestion": _safe_text(registry_row.get("final_action")) or "先做复核和补字段",
                "conclusion_strength": _safe_text(registry_row.get("action_strength")) or "soft_action",
                "confidence_level": _safe_text(registry_row.get("confidence_level")) or "medium",
                "owner_role": _safe_text(registry_row.get("owner_role")) or "业务负责人 + 数据分析",
                "validation_metric": _safe_text(registry_row.get("validation_metric")) or "关键字段补齐 / 关键指标复核",
            }
        )
    return rows


def _apply_conflict_repairs(field_registry: dict[str, Any], registry_payload: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    repaired_rows = []
    issues: list[str] = []
    for row in list(registry_payload.get("rows") or []):
        row = dict(row)
        missing = set(row.get("missing_fields") or [])
        action = _safe_text(row.get("final_action"))
        blocked_actions = list(row.get("blocked_actions") or [])
        if "target_fields" in missing and any(token in action for token in ("目标达成", "KPI", "绩效优秀", "超额完成", "未达标")):
            issues.append(f"{row.get('object_id')} 缺 target_fields 却判断目标达成")
            row["final_action"] = "当前只能描述实际表现，无法判断目标达成情况"
            row["conclusion_type"] = "risk_flag"
            row["confidence_level"] = "low"
            blocked_actions.append("目标达成判断")
        if "amount_fields" in missing and any(token in action for token in ("ROI", "成本效率", "预算合理", "财务表现好")):
            issues.append(f"{row.get('object_id')} 缺 amount_fields 却判断财务效率")
            row["final_action"] = "金额字段缺失，只能分析规模、进度或质量表现"
            row["conclusion_type"] = "risk_flag"
            row["confidence_level"] = "low"
            blocked_actions.append("财务效率判断")
        if "time_fields" in missing and any(token in action for token in ("趋势", "同比", "环比", "持续增长", "持续下降")):
            issues.append(f"{row.get('object_id')} 缺 time_fields 却判断趋势")
            row["final_action"] = "时间字段缺失，只能做截面结构分析"
            row["conclusion_type"] = "risk_flag"
            row["confidence_level"] = "low"
            blocked_actions.append("趋势判断")
        if "quality_fields" in missing and any(token in action for token in ("满意度高", "质量稳定", "问题改善")):
            issues.append(f"{row.get('object_id')} 缺 quality_fields 却判断质量")
            row["final_action"] = "质量字段缺失，无法判断质量表现"
            row["conclusion_type"] = "risk_flag"
            row["confidence_level"] = "low"
            blocked_actions.append("质量判断")
        if "people_fields" in missing and any(token in action for token in ("负责人", "团队", "归责")):
            issues.append(f"{row.get('object_id')} 缺 people_fields 却直接归责")
            row["final_action"] = "责任主体字段缺失，需要补充负责人/团队字段"
            row["conclusion_type"] = "data_required"
            row["confidence_level"] = "low"
            blocked_actions.append("责任归因")
        row["blocked_actions"] = _dedupe(blocked_actions)
        repaired_rows.append(row)
    return issues, {**registry_payload, "rows": repaired_rows}


def _seed_page_plan(
    field_registry: dict[str, Any],
    question_bank: list[dict[str, Any]],
    metric_rows: list[dict[str, Any]],
    registry_rows: list[dict[str, Any]],
    exploratory: dict[str, Any],
) -> list[dict[str, Any]]:
    titles = [
        "封面与报告定位", "管理层摘要", "数据范围与字段可用性", "主对象识别", "指标体系搭建", "当前整体表现", "时间趋势分析", "时间字段缺口或节奏解释",
        "对象结构分析（上）", "对象结构分析（下）", "分类结构分析（上）", "分类结构分析（下）", "地区/空间分析", "金额/预算分析", "进度/完成分析", "质量/满意度分析",
        "转化/流转分析", "负责人/团队分析", "文本反馈主题分析", "异常对象识别", "重点对象复核表（上）", "重点对象复核表（下）",
        "管理问题诊断（1）", "管理问题诊断（2）", "管理问题诊断（3）", "管理问题诊断（4）", "管理问题诊断（5）",
        "对象级行动表（上）", "对象级行动表（下）", "7日动作表", "30日改进 backlog（上）", "30日改进 backlog（下）", "禁止误判清单", "数据补充优先级",
        "管理层行动路线图 T+1/T+3", "管理层行动路线图 T+7/T+14/T+30", "附录说明",
    ]
    seed: list[dict[str, Any]] = []
    for index, title in enumerate(titles, start=1):
        q = question_bank[(index - 1) % len(question_bank)]
        metrics = metric_rows[(index - 1) % max(len(metric_rows), 1) : ((index - 1) % max(len(metric_rows), 1)) + 2] if metric_rows else []
        objects = [str(row.get("object_name") or row.get("object_id")) for row in registry_rows[:4]]
        seed.append(
            {
                "page_number": index,
                "page_title": title,
                "management_question": q["business_question"],
                "page_purpose": q["management_action"],
                "required_metrics": [row["metric_id"] for row in metrics],
                "required_dimensions": [field for field in q["required_fields"]][:4],
                "available_fields": [str(item) for item in field_registry.get("available_field_groups") or []][:12],
                "derived_metrics": [
                    {
                        "metric_id": row["metric_id"],
                        "metric_name": row["metric_name"],
                        "formula": row["formula"],
                        "value": row["value"],
                        "comparison": row["comparison"],
                        "evidence_strength": row["evidence_strength"],
                    }
                    for row in metrics
                ],
                "evidence_query": "围绕当前页的对象、维度、异常和字段边界抽取证据",
                "objects_to_discuss": objects[:6],
                "allowed_claim_types": ["structure", "efficiency", "risk", "opportunity"],
                "forbidden_claim_types": ["causal attribution without evidence"],
                "required_table_or_chart": "table",
                "action_type": q["management_action"],
                "source_passes": [
                    "business_context_interpretation",
                    "field_semantic_map",
                    "metric_derivation_plan",
                    "derived_metric_execution_review",
                    "management_question_bank",
                    "exploratory_interpretation",
                    "object_level_interpretation",
                    "interpretation_conflict_check",
                ],
            }
        )
    return seed


def _metric_lookup(metric_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("metric_id") or ""): row for row in metric_rows}


def _build_page_plan(ai_pages: list[dict[str, Any]], seed_pages: list[dict[str, Any]], metric_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    metric_map = _metric_lookup(metric_rows)
    seed_by_number = {int(page["page_number"]): page for page in seed_pages}
    pages: list[dict[str, Any]] = []
    for ai_page in ai_pages:
        page_number = int(ai_page.get("page_number") or 0)
        seed = seed_by_number.get(page_number)
        if not seed:
            continue
        ai_metric_ids = []
        for metric in ai_page.get("derived_metrics") or []:
            metric_id = _safe_text(metric.get("metric_id"))
            if metric_id:
                ai_metric_ids.append(metric_id)
        if not ai_metric_ids:
            ai_metric_ids = [str(item.get("metric_id")) for item in seed.get("derived_metrics", []) if _safe_text(item.get("metric_id"))]
        derived_metrics = []
        for metric_id in ai_metric_ids[:4]:
            metric = metric_map.get(metric_id) or next((item for item in seed.get("derived_metrics", []) if str(item.get("metric_id")) == metric_id), {})
            if not metric_id or not metric:
                continue
            derived_metrics.append(
                {
                    "metric_id": metric_id,
                    "metric_name": _safe_text(metric.get("metric_name")),
                    "formula": _safe_text(metric.get("formula")),
                    "value": _safe_text(metric.get("value")),
                    "comparison": _safe_text(metric.get("comparison")),
                    "evidence_strength": _safe_text(metric.get("evidence_strength") or "medium"),
                }
            )
        page = {
            "page_number": page_number,
            "page_title": _safe_text(ai_page.get("page_title")) or seed["page_title"],
            "management_question": _safe_text(ai_page.get("management_question")) or seed["management_question"],
            "page_purpose": _safe_text(ai_page.get("page_purpose")) or seed["page_purpose"],
            "required_metrics": _dedupe([str(metric_id) for metric_id in ai_metric_ids])[:6],
            "required_dimensions": [str(item) for item in (ai_page.get("required_dimensions") or seed["required_dimensions"])][:6],
            "available_fields": [str(item) for item in (ai_page.get("available_fields") or seed["available_fields"])][:12],
            "derived_metrics": derived_metrics,
            "evidence_query": _safe_text(ai_page.get("evidence_query")) or seed["evidence_query"],
            "objects_to_discuss": [str(item) for item in (ai_page.get("objects_to_discuss") or seed["objects_to_discuss"])][:8],
            "allowed_claim_types": [str(item) for item in (ai_page.get("allowed_claim_types") or seed["allowed_claim_types"])][:6],
            "forbidden_claim_types": [str(item) for item in (ai_page.get("forbidden_claim_types") or seed["forbidden_claim_types"])][:6],
            "required_table_or_chart": _safe_text(ai_page.get("required_table_or_chart")) or seed["required_table_or_chart"],
            "action_type": _safe_text(ai_page.get("action_type")) or seed["action_type"],
            "source_passes": [str(item) for item in (ai_page.get("source_passes") or seed["source_passes"])][:12],
        }
        pages.append(page)
    return sorted(pages, key=lambda item: int(item.get("page_number") or 0))


def _ensure_page_plan_valid(pages: list[dict[str, Any]]) -> bool:
    if not (35 <= len(pages) <= 50):
        return False
    required_keys = {
        "page_number",
        "page_title",
        "management_question",
        "page_purpose",
        "required_metrics",
        "required_dimensions",
        "available_fields",
        "derived_metrics",
        "evidence_query",
        "objects_to_discuss",
        "allowed_claim_types",
        "forbidden_claim_types",
        "required_table_or_chart",
        "action_type",
        "source_passes",
    }
    page_numbers = set()
    for page in pages:
        if not required_keys.issubset(page.keys()):
            return False
        page_number = int(page.get("page_number") or 0)
        if page_number in page_numbers:
            return False
        page_numbers.add(page_number)
        if not page.get("derived_metrics"):
            return False
        if not all(_safe_text(metric.get("metric_id")) for metric in page.get("derived_metrics") or []):
            return False
    return True


def _enforce_page_plan_derived_metric_contract(pages: list[dict[str, Any]], contract: dict[str, Any]) -> list[dict[str, Any]]:
    if not pages or not (contract.get("usage_gate") or {}).get("enabled"):
        return pages
    metric_lookup = {
        str(row.get("metric_id") or ""): row
        for row in contract.get("metrics") or []
        if row.get("metric_id")
    }
    minimum = int((contract.get("usage_gate") or {}).get("minimum_body_metric_count") or 0)
    required_ids = [
        str(item)
        for item in list(contract.get("required_metric_ids") or [])[: max(1, minimum)]
        if str(item) in metric_lookup
    ]
    if not required_ids:
        return pages
    used_ids = {
        _safe_text(metric.get("metric_id") if isinstance(metric, dict) else metric)
        for page in pages
        for metric in page.get("derived_metrics") or []
        if _safe_text(metric.get("metric_id") if isinstance(metric, dict) else metric)
    }
    missing_ids = [metric_id for metric_id in required_ids if metric_id not in used_ids]
    if not missing_ids:
        return pages
    updated_pages = [dict(page) for page in pages]
    for index, metric_id in enumerate(missing_ids):
        target = updated_pages[index % len(updated_pages)]
        metric = metric_lookup[metric_id]
        target_metrics = list(target.get("derived_metrics") or [])
        target_metrics.append(
            {
                "metric_id": metric_id,
                "metric_name": _safe_text(metric.get("metric_name")) or metric_id,
                "formula": _safe_text(metric.get("formula")),
                "value": _safe_text(metric.get("value")),
                "comparison": _safe_text(metric.get("comparison")),
                "evidence_strength": _safe_text(metric.get("evidence_strength") or "medium"),
                "status": _safe_text(metric.get("status") or "executed"),
            }
        )
        target["derived_metrics"] = target_metrics
        target["required_metrics"] = _dedupe([*list(target.get("required_metrics") or []), metric_id])[:8]
        target["source_passes"] = _dedupe([*list(target.get("source_passes") or []), "derived_metric_usage_contract"])[:12]
        updated_pages[index % len(updated_pages)] = target
    return updated_pages


def _normalize_page_metric_refs(metrics: list[Any]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in metrics:
        if isinstance(item, dict):
            metric_id = _safe_text(item.get("metric_id") or item.get("raw_key") or item.get("metric_name") or item.get("metric"))
            metric_name = _safe_text(item.get("metric_name") or item.get("localized_label") or item.get("metric") or metric_id)
            status = _safe_text(item.get("status") or "executed")
            value = _safe_text(item.get("value") or item.get("current_value"))
            comparison = _safe_text(item.get("comparison") or item.get("benchmark"))
        else:
            metric_id = _safe_text(item)
            metric_name = metric_id
            status = "executed"
            value = ""
            comparison = ""
        if not metric_id or metric_id in seen:
            continue
        seen.add(metric_id)
        normalized.append(
            {
                "metric_id": metric_id,
                "metric_name": metric_name or metric_id,
                "status": status or "executed",
                "value": value,
                "comparison": comparison,
            }
        )
    return normalized


def _derived_metrics_used_for_page(ai_page: dict[str, Any], plan: dict[str, Any], evidence: list[dict[str, Any]], recommended_action: dict[str, Any]) -> list[dict[str, Any]]:
    plan_metrics = _normalize_page_metric_refs(list(plan.get("derived_metrics") or []))
    known_by_id = {item["metric_id"]: item for item in plan_metrics}
    used_ids: list[str] = []
    for item in ai_page.get("derived_metrics_used") or []:
        metric_id = _safe_text(item.get("metric_id") if isinstance(item, dict) else item)
        if metric_id and metric_id not in used_ids:
            used_ids.append(metric_id)
    for item in evidence:
        metric_id = _safe_text(item.get("metric_id"))
        if metric_id in known_by_id and metric_id not in used_ids:
            used_ids.append(metric_id)
    for key in ("trigger_metric", "verification_metric"):
        metric_id = _safe_text(recommended_action.get(key))
        if metric_id in known_by_id and metric_id not in used_ids:
            used_ids.append(metric_id)
    for item in plan_metrics:
        if item["metric_id"] not in used_ids:
            used_ids.append(item["metric_id"])
    if not used_ids:
        used_ids = [item["metric_id"] for item in plan_metrics[:2]]
    result: list[dict[str, Any]] = []
    for metric_id in used_ids[:4]:
        source = known_by_id.get(metric_id) or {"metric_id": metric_id, "metric_name": metric_id, "status": "executed"}
        result.append(
            {
                "metric_id": metric_id,
                "metric_name": source.get("metric_name") or metric_id,
                "status": source.get("status") or "executed",
                "usage_role": "recommendation_driver" if metric_id == _safe_text(recommended_action.get("trigger_metric")) else "page_evidence",
                "value": source.get("value") or "",
                "comparison": source.get("comparison") or "",
            }
        )
    return result


def _build_page_drafts(ai_pages: list[dict[str, Any]], page_plan: list[dict[str, Any]]) -> list[dict[str, Any]]:
    plan_by_number = {int(page["page_number"]): page for page in page_plan}
    drafts: list[dict[str, Any]] = []
    for ai_page in ai_pages:
        page_number = int(ai_page.get("page_number") or 0)
        plan = plan_by_number.get(page_number)
        if not plan:
            continue
        diagnosis = _safe_text(ai_page.get("diagnosis"))
        business_interpretation = _safe_text(ai_page.get("business_interpretation"))
        evidence = list(ai_page.get("evidence") or [])
        low_data_page = bool(ai_page.get("low_data_boundary_page"))
        recommended_action = ai_page.get("recommended_action") or {}
        plan_metrics = _normalize_page_metric_refs(list(plan.get("derived_metrics") or []))
        derived_metrics_used = _derived_metrics_used_for_page(ai_page, plan, evidence, recommended_action)
        if not _safe_text(recommended_action.get("trigger_metric")) and derived_metrics_used:
            recommended_action = {**recommended_action, "trigger_metric": derived_metrics_used[0]["metric_id"]}
        derived_metric_explanation = _safe_text(ai_page.get("derived_metric_explanation"))
        usage_sentence = ""
        if derived_metrics_used:
            usage_sentence = "本页派生指标主线：" + "、".join(
                f"{item.get('metric_name') or item.get('metric_id')}({item.get('metric_id')})"
                for item in derived_metrics_used[:4]
            )
        if not derived_metric_explanation and plan_metrics:
            metric_names = "、".join(
                f"{item['metric_name']}({item['metric_id']})"
                for item in plan_metrics[:3]
            )
            derived_metric_explanation = f"本页把派生指标 {metric_names} 作为主线证据，先使用后端确定性执行结果，再把它们连接到对象差异、风险判断和建议动作。"
        elif usage_sentence and not all(item.get("metric_id") in derived_metric_explanation for item in derived_metrics_used[:4]):
            derived_metric_explanation = f"{derived_metric_explanation}\n{usage_sentence}".strip()
        draft = {
            "page_number": page_number,
            "page_title": _safe_text(ai_page.get("page_title")) or plan["page_title"],
            "management_question": _safe_text(ai_page.get("management_question")) or plan["management_question"],
            "diagnosis": diagnosis,
            "evidence": [
                {
                    "metric_id": _safe_text(item.get("metric_id")),
                    "metric_name": _safe_text(item.get("metric_name")),
                    "value": _safe_text(item.get("value")),
                    "comparison": _safe_text(item.get("comparison")),
                    "object_or_dimension": _safe_text(item.get("object_or_dimension")),
                    "evidence_strength": _safe_text(item.get("evidence_strength") or "medium"),
                }
                for item in evidence
                if _safe_text(item.get("metric_id"))
            ],
            "derived_metrics_used": derived_metrics_used,
            "derived_metric_explanation": derived_metric_explanation,
            "business_interpretation": business_interpretation,
            "recommended_action": {
                "object": _safe_text(recommended_action.get("object")),
                "trigger_metric": _safe_text(recommended_action.get("trigger_metric")),
                "current_value": _safe_text(recommended_action.get("current_value")),
                "threshold_or_comparison": _safe_text(recommended_action.get("threshold_or_comparison")),
                "owner_role": _safe_text(recommended_action.get("owner_role")),
                "action": _safe_text(recommended_action.get("action")),
                "deadline": _safe_text(recommended_action.get("deadline")),
                "verification_metric": _safe_text(recommended_action.get("verification_metric")),
            },
            "data_limitations": _safe_text(ai_page.get("data_limitations")),
            "forbidden_misreadings": [str(item) for item in (ai_page.get("forbidden_misreadings") or []) if _safe_text(item)],
            "source_passes": [str(item) for item in (ai_page.get("source_passes") or plan.get("source_passes") or [])][:12],
            "low_data_boundary_page": low_data_page,
        }
        draft["ai_content_hash"] = hashlib.sha256(
            json.dumps(
                {
                    "diagnosis": draft["diagnosis"],
                    "business_interpretation": draft["business_interpretation"],
                    "recommended_action": draft["recommended_action"],
                },
                ensure_ascii=False,
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()
        drafts.append(draft)
    return sorted(drafts, key=lambda item: int(item.get("page_number") or 0))


def _validate_page_drafts(drafts: list[dict[str, Any]], page_plan: list[dict[str, Any]]) -> bool:
    if len(drafts) != len(page_plan):
        return False
    plan_numbers = {int(page["page_number"]) for page in page_plan}
    draft_numbers = {int(draft["page_number"]) for draft in drafts}
    if plan_numbers != draft_numbers:
        return False
    plan_by_number = {int(page["page_number"]): page for page in page_plan}
    for draft in drafts:
        plan = plan_by_number.get(int(draft["page_number"]))
        plan_metric_ids = {
            _safe_text(item.get("metric_id") if isinstance(item, dict) else item)
            for item in (plan or {}).get("derived_metrics") or []
            if _safe_text(item.get("metric_id") if isinstance(item, dict) else item)
        }
        used_metric_ids = {
            _safe_text(item.get("metric_id") if isinstance(item, dict) else item)
            for item in draft.get("derived_metrics_used") or []
            if _safe_text(item.get("metric_id") if isinstance(item, dict) else item)
        }
        evidence_metric_ids = {_safe_text(item.get("metric_id")) for item in draft.get("evidence") or [] if _safe_text(item.get("metric_id"))}
        trigger_metric = _safe_text((draft.get("recommended_action") or {}).get("trigger_metric"))
        if plan_metric_ids:
            if not used_metric_ids:
                return False
            if not (used_metric_ids & plan_metric_ids or evidence_metric_ids & plan_metric_ids or trigger_metric in plan_metric_ids):
                return False
        if _count_cjk(draft["diagnosis"]) < 180:
            return False
        if _count_cjk(draft["business_interpretation"]) < 150:
            return False
        evidence_count = len(draft["evidence"])
        if draft.get("low_data_boundary_page"):
            if evidence_count < 1:
                return False
        elif evidence_count < 2:
            return False
        if not _safe_text(draft["recommended_action"].get("action")):
            return False
        if plan_metric_ids and not trigger_metric:
            return False
        if not _safe_text(draft.get("ai_content_hash")):
            return False
    return True


def _render_page_markdown(draft: dict[str, Any]) -> str:
    lines = [
        f"# 第 {draft['page_number']} 页：{draft['page_title']}",
        "",
        f"管理问题：{draft['management_question']}",
        "",
        "## 诊断判断",
        "",
        draft["diagnosis"],
        "",
        "## 证据",
        "",
    ]
    for evidence in draft["evidence"]:
        lines.append(
            f"- {evidence['metric_id']} | {evidence['metric_name']} | 值={evidence['value']} | 比较={evidence['comparison']} | 对象={evidence['object_or_dimension']} | 强度={evidence['evidence_strength']}"
        )
    lines.extend(
        [
            "",
            "## 指标推导",
            "",
            draft["derived_metric_explanation"],
            "",
            "## 业务解释",
            "",
            draft["business_interpretation"],
            "",
            "## 建议动作",
            "",
            f"- 对象：{draft['recommended_action']['object']}",
            f"- 触发指标：{draft['recommended_action']['trigger_metric']}",
            f"- 当前值：{draft['recommended_action']['current_value']}",
            f"- 阈值/对比：{draft['recommended_action']['threshold_or_comparison']}",
            f"- 负责人角色：{draft['recommended_action']['owner_role']}",
            f"- 动作：{draft['recommended_action']['action']}",
            f"- 截止时间：{draft['recommended_action']['deadline']}",
            f"- 验证指标：{draft['recommended_action']['verification_metric']}",
            "",
            "## 数据边界",
            "",
            draft["data_limitations"],
            "",
            "## 禁止误读",
            "",
            *(f"- {item}" for item in draft["forbidden_misreadings"]),
            "",
            f"AI内容指纹：{draft['ai_content_hash']}",
            f"解释来源：{' / '.join(draft['source_passes'])}",
            "",
        ]
    )
    return "\n".join(lines)


def _validate_output_schema(pass_name: str, payload: Any) -> bool:
    if pass_name == "business_context_interpretation":
        return isinstance(payload, dict) and all(key in payload for key in ["possible_business_scenarios", "core_object_grain", "management_questions", "supported_questions", "unsupported_questions", "ambiguity_points"])
    if pass_name == "field_semantic_map":
        return isinstance(payload, dict) and isinstance(payload.get("rows"), list) and bool(payload.get("rows"))
    if pass_name == "metric_derivation_plan":
        return isinstance(payload, dict) and isinstance(payload.get("metrics"), list) and bool(payload.get("metrics"))
    if pass_name == "derived_metric_execution_review":
        return isinstance(payload, dict) and isinstance(payload.get("metrics"), list) and bool(payload.get("metrics"))
    if pass_name == "management_question_bank":
        return isinstance(payload, dict) and isinstance(payload.get("questions"), list) and len(payload.get("questions") or []) >= 20
    if pass_name == "exploratory_interpretation":
        return isinstance(payload, dict) and bool(payload.get("main_findings"))
    if pass_name == "object_level_interpretation":
        return isinstance(payload, dict) and isinstance(payload.get("rows"), list) and bool(payload.get("rows"))
    if pass_name == "interpretation_conflict_check":
        return isinstance(payload, dict) and "conflicts_found" in payload and "auto_repairs" in payload
    if pass_name == "long_report_page_plan":
        return isinstance(payload, dict) and _ensure_page_plan_valid(list(payload.get("pages") or []))
    if pass_name == "page_generation_batch":
        return isinstance(payload, dict) and isinstance(payload.get("pages"), list) and bool(payload.get("pages"))
    if pass_name in {"executive_readability_review", "business_rigor_review", "final_codex_interpretation_review"}:
        return isinstance(payload, dict) and bool(payload)
    return bool(payload)


def _invoke_pass(
    *,
    report_dir: Path,
    cache_dir: Path,
    log_path: Path,
    pass_name: str,
    required: bool,
    input_payload: dict[str, Any],
    runner: Callable[[dict[str, Any]], dict[str, Any]],
    build_output: Callable[[dict[str, Any], dict[str, Any]], tuple[dict[str, Any], list[Path]]],
    downstream_usage: list[str],
    min_output_length: int | None = None,
) -> dict[str, Any]:
    dependency_state = _tracked_dependency_state(report_dir)
    input_hash = _hash_jsonable(input_payload)
    cache_key = _hash_jsonable({"pass_name": pass_name, "input_hash": input_hash, "deps": dependency_state})
    cache_record = _load_cache(cache_dir, cache_key)
    started_at = datetime.now(timezone.utc)
    raw_result: dict[str, Any] = {}
    structured_output: dict[str, Any] = {}
    output_files: list[Path] = []
    cache_used = False
    cache_valid = False
    error_message: str | None = None
    retry_count = 0

    cache_record_ok = (
        cache_record
        and cache_record.get("input_hash") == input_hash
        and cache_record.get("dependency_state") == dependency_state
        and cache_record.get("status") in {"success", "cache_hit"}
        and not cache_record.get("fallback_used")
    )
    if cache_record_ok:
        raw_result = cache_record.get("raw_result") or {}
        structured_output = cache_record.get("structured_output") or {}
        cache_used = True
        cache_valid = True
        output_files = [Path(path) for path in cache_record.get("output_files") or []]
    else:
        try:
            raw_result = runner(input_payload) or {}
            if not isinstance(raw_result, dict):
                raw_result = {"raw_result": raw_result}
        except Exception as exc:  # pragma: no cover - defensive
            error_message = str(exc)
            raw_result = {"error": str(exc), "mode": "exception", "runtime_state": "failed"}
        try:
            structured_output, output_files = build_output(raw_result, input_payload)
        except Exception as exc:  # pragma: no cover - defensive
            error_message = error_message or str(exc)
            structured_output = {}
            output_files = []
    finished_at = datetime.now(timezone.utc)
    fallback_used = _is_fallback_result(raw_result)
    files_written = bool(output_files) and all(path.exists() for path in output_files)
    output_json_valid = _validate_output_schema(pass_name, structured_output)
    output_hash = _hash_jsonable(structured_output) if structured_output else ""
    output_text_length = len(json.dumps(structured_output, ensure_ascii=False, default=str)) if structured_output else 0
    threshold = min_output_length or PASS_MIN_LENGTHS.get(pass_name, 1)

    failed_reasons: list[str] = []
    if error_message:
        failed_reasons.append(error_message)
    if not structured_output:
        failed_reasons.append("structured_output_empty")
    if not output_json_valid:
        failed_reasons.append("schema_validation_failed")
    if output_text_length < threshold:
        failed_reasons.append(f"output_text_length_below_threshold:{output_text_length}<{threshold}")
    if fallback_used:
        failed_reasons.append("fallback_used")
    if not files_written:
        failed_reasons.append("files_written=false")

    if failed_reasons:
        status = "fallback" if fallback_used else "failed"
    elif cache_used:
        status = "cache_hit"
    else:
        status = "success"

    if not cache_used:
        _save_cache(
            cache_dir,
            cache_key,
            {
                "input_hash": input_hash,
                "dependency_state": dependency_state,
                "raw_result": raw_result,
                "structured_output": structured_output,
                "output_files": [str(path) for path in output_files],
                "status": status,
                "fallback_used": fallback_used,
            },
        )

    record = {
        "call_id": f"{pass_name}-{cache_key[:12]}",
        "pass_name": pass_name,
        "required": required,
        "status": status,
        "runner_name": _runner_name(runner),
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "latency_ms": int((finished_at - started_at).total_seconds() * 1000),
        "input_hash": input_hash,
        "output_hash": output_hash,
        "output_text_length": output_text_length,
        "output_json_valid": output_json_valid,
        "output_files": [str(path.relative_to(report_dir)) if str(path).startswith(str(report_dir)) else str(path) for path in output_files],
        "files_written": files_written,
        "fallback_used": fallback_used,
        "cache_used": cache_used,
        "cache_valid": cache_valid,
        "downstream_usage": downstream_usage,
        "error": "; ".join(failed_reasons) if failed_reasons else None,
        "retry_count": retry_count,
    }
    _append_call_log(log_path, record)

    return {
        "pass_name": pass_name,
        "required": required,
        "raw_result": raw_result,
        "structured_output": structured_output,
        "output_files": output_files,
        "record": record,
        "success": status in {"success", "cache_hit"},
    }


def _write_pass_outputs(
    *,
    report_dir: Path,
    file_map: dict[str, Any],
) -> list[Path]:
    written: list[Path] = []
    for relative_name, payload in file_map.items():
        path = report_dir / relative_name
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(payload, (dict, list)):
            _write_json(path, payload)
        else:
            path.write_text(str(payload), encoding="utf-8")
        written.append(path)
    return written


def _business_context_output(raw_result: dict[str, Any], _: dict[str, Any], dataset_name: str, sheet_name: str, request_payload: dict[str, Any], field_registry: dict[str, Any], entity_column: str | None, report_dir: Path) -> tuple[dict[str, Any], list[Path]]:
    structured = _build_business_context(raw_result, dataset_name, sheet_name, request_payload, field_registry, entity_column)
    markdown = [
        ("possible_business_scenarios", structured["possible_business_scenarios"]),
        ("core_object_grain", structured["core_object_grain"]),
        ("management_questions", structured["management_questions"]),
        ("supported_questions", structured["supported_questions"]),
        ("unsupported_questions", structured["unsupported_questions"]),
        ("ambiguity_points", structured["ambiguity_points"]),
    ]
    path = report_dir / "business_context_interpretation.md"
    _write_markdown(path, "business_context_interpretation", markdown)
    return structured, [path]


def _field_semantic_output(raw_result: dict[str, Any], _: dict[str, Any], frame: pd.DataFrame, report_dir: Path) -> tuple[dict[str, Any], list[Path]]:
    rows = _field_semantic_rows(frame)
    structured = {
        "subject_type": _safe_text(raw_result.get("subject_type") or "generic_subject"),
        "creator_profile": _safe_text(raw_result.get("creator_profile")),
        "rows": rows,
    }
    md_path = report_dir / "field_semantic_map.md"
    json_path = report_dir / "field_semantic_map.json"
    _write_markdown(
        md_path,
        "field_semantic_map",
        [
            ("subject_type", structured["subject_type"]),
            ("creator_profile", structured["creator_profile"] or "当前按通用经营对象解释"),
            (
                "field_semantics",
                [
                    f"{row['field_name']} | 含义={row['guessed_business_meaning']} | 可用于={','.join(row['usable_for'])} | 不可用于={','.join(row['not_usable_for'])}"
                    for row in rows
                ],
            ),
        ],
    )
    _write_json(json_path, structured)
    return structured, [md_path, json_path]


def _metric_derivation_output(raw_result: dict[str, Any], _: dict[str, Any], metric_candidates: list[dict[str, Any]], metric_rows: list[dict[str, Any]], report_dir: Path) -> tuple[dict[str, Any], list[Path]]:
    metric_map = {row["metric_id"]: row for row in metric_rows}
    metrics = []
    for item in raw_result.get("metrics") or []:
        metric_id = _safe_text(item.get("metric_id"))
        if not metric_id:
            continue
        value_row = metric_map.get(metric_id, {})
        metrics.append(
            {
                "metric_id": metric_id,
                "metric_name": _safe_text(item.get("metric_name") or value_row.get("metric_name")),
                "formula": _safe_text(item.get("formula") or value_row.get("formula")),
                "source_fields": [str(field) for field in item.get("source_fields", [])[:6]] or list(value_row.get("source_fields", [])),
                "business_value": _safe_text(item.get("business_value")),
                "claim_strength": _safe_text(item.get("claim_strength") or value_row.get("claim_strength") or "weak"),
                "caution": _safe_text(item.get("caution")),
                "value": _safe_text(value_row.get("value")),
                "comparison": _safe_text(value_row.get("comparison")),
                "evidence_strength": _safe_text(value_row.get("evidence_strength") or "medium"),
            }
        )
    if not metrics:
        metrics = [
            {
                **candidate,
                **next((row for row in metric_rows if row["metric_id"] == candidate["metric_id"]), {}),
                "caution": "未获得 live AI 派生指标解释。",
            }
            for candidate in metric_candidates[:12]
        ]
    structured = {"metrics": metrics, "notes": [str(item) for item in raw_result.get("notes") or []]}
    md_path = report_dir / "metric_derivation_plan.md"
    json_path = report_dir / "metric_derivation_plan.json"
    _write_markdown(
        md_path,
        "metric_derivation_plan",
        [("metrics", [f"{row['metric_id']} | {row['metric_name']} | 公式={row['formula']} | 值={row['value']} | 比较={row['comparison']} | 口径={row['claim_strength']}" for row in metrics])],
    )
    _write_json(json_path, structured)
    return structured, [md_path, json_path]


def _derived_metric_execution_output(raw_result: dict[str, Any], _: dict[str, Any], metric_rows: list[dict[str, Any]], report_dir: Path) -> tuple[dict[str, Any], list[Path]]:
    cards = list(raw_result.get("metric_cards") or [])
    metrics = []
    for row in metric_rows:
        card = next((item for item in cards if _safe_text(item.get("metric")) == row["metric_name"] or _safe_text(item.get("metric")) == row["metric_id"]), {})
        metrics.append(
            {
                "metric_id": row["metric_id"],
                "metric_name": row["metric_name"],
                "value": row["value"],
                "comparison": row["comparison"],
                "business_meaning": _safe_text(card.get("business_meaning")),
                "management_impact": _safe_text(card.get("management_impact")),
                "caution": _safe_text(card.get("caution")),
                "evidence_strength": row["evidence_strength"],
            }
        )
    structured = {"metrics": metrics}
    md_path = report_dir / "derived_metric_execution_review.md"
    json_path = report_dir / "derived_metric_execution_review.json"
    _write_markdown(
        md_path,
        "derived_metric_execution_review",
        [("metrics", [f"{row['metric_id']} | 值={row['value']} | 比较={row['comparison']} | 含义={row['business_meaning']} | 管理影响={row['management_impact']} | 注意={row['caution']}" for row in metrics])],
    )
    _write_json(json_path, structured)
    return structured, [md_path, json_path]


def _question_bank_output(raw_result: dict[str, Any], _: dict[str, Any], field_registry: dict[str, Any], report_dir: Path) -> tuple[dict[str, Any], list[Path]]:
    questions = _build_question_bank(raw_result, field_registry)
    structured = {"questions": questions}
    path = report_dir / "management_question_bank.md"
    _write_markdown(
        path,
        "management_question_bank",
        [
            (
                "questions",
                [
                    f"P{row['priority']} | {row['business_question']} | 重要性={row['why_it_matters']} | 当前能否回答={row['can_answer_now']} | 需要字段={','.join(row['required_fields'])} | 章节={row['report_section']} | 动作={row['management_action']}"
                    for row in questions
                ],
            )
        ],
    )
    return structured, [path]


def _exploratory_output(raw_result: dict[str, Any], _: dict[str, Any], frame: pd.DataFrame, field_registry: dict[str, Any], metric_rows: list[dict[str, Any]], registry_rows: list[dict[str, Any]], report_dir: Path) -> tuple[dict[str, Any], list[Path]]:
    structured = _build_exploratory(frame, raw_result, field_registry, metric_rows, registry_rows)
    path = report_dir / "exploratory_interpretation.md"
    _write_markdown(
        path,
        "exploratory_interpretation",
        [
            ("main_findings", structured["main_findings"]),
            ("anomalies", structured["anomalies"]),
            ("possible_reasons", structured["possible_reasons"]),
            ("missing_fields", structured["missing_fields"] or ["无"]),
            ("cannot_conclude", structured["cannot_conclude"] or ["当前无明显硬性边界"]),
            ("next_validations", structured["next_validations"]),
        ],
    )
    return structured, [path]


def _object_output(raw_result: dict[str, Any], _: dict[str, Any], registry_rows: list[dict[str, Any]], field_registry: dict[str, Any], batch_rows: list[dict[str, Any]], report_dir: Path, append: bool) -> tuple[dict[str, Any], list[Path]]:
    structured_rows = _build_object_rows(raw_result, registry_rows, field_registry, batch_rows)
    json_path = report_dir / "object_level_interpretation.json"
    md_path = report_dir / "object_level_interpretation.md"
    existing = _read_json(json_path).get("rows", []) if append and json_path.exists() else []
    rows = [*existing, *structured_rows]
    structured = {"rows": rows}
    _write_json(json_path, structured)
    _write_markdown(
        md_path,
        "object_level_interpretation",
        [
            (
                "objects",
                [
                    f"{row['object_name']} | 表现摘要={row['performance_summary']} | 证据={row['trigger_evidence']} | 缺失字段={','.join(row['missing_fields']) or '无'} | 标签建议={row['final_label_suggestion']} | 动作建议={row['final_action_suggestion']} | 结论强度={row['conclusion_strength']} | 置信度={row['confidence_level']} | 负责人={row['owner_role']} | 验证指标={row['validation_metric']}"
                    for row in rows
                ],
            )
        ],
    )
    return structured, [md_path, json_path]


def _conflict_output(raw_result: dict[str, Any], _: dict[str, Any], field_registry: dict[str, Any], registry_payload: dict[str, Any], report_dir: Path) -> tuple[dict[str, Any], list[Path], dict[str, Any]]:
    issues, adjusted_registry = _apply_conflict_repairs(field_registry, registry_payload)
    structured = {
        "conflicts_found": _dedupe(issues + [str(item.get("claim") or "") for item in raw_result.get("challenge_points") or []])[:12],
        "auto_repairs": (
            [f"已将 {item} 自动降级为待验证/风险提示" for item in issues]
            or ["本轮未发现需要继续降级的严重冲突"]
        ),
        "blocked_actions": [str(item) for row in (adjusted_registry.get("rows") or []) for item in (row.get("blocked_actions") or [])],
    }
    md_path = report_dir / "interpretation_conflict_check.md"
    json_path = report_dir / "interpretation_conflict_check.json"
    _write_markdown(
        md_path,
        "interpretation_conflict_check",
        [
            ("conflicts_found", structured["conflicts_found"] or ["未发现严重冲突"]),
            ("auto_repairs", structured["auto_repairs"]),
            ("blocked_actions", structured["blocked_actions"][:12] or ["当前无新增 blocked_actions"]),
        ],
    )
    _write_json(json_path, structured)
    return structured, [md_path, json_path], adjusted_registry


def _page_plan_output(raw_result: dict[str, Any], _: dict[str, Any], seed_plan: list[dict[str, Any]], metric_rows: list[dict[str, Any]], report_dir: Path) -> tuple[dict[str, Any], list[Path]]:
    pages_payload = list(raw_result.get("pages") or [])
    if _ensure_page_plan_valid(pages_payload):
        pages = pages_payload
    else:
        pages = _build_page_plan(pages_payload, seed_plan, metric_rows)
    structured = {"pages": pages}
    md_path = report_dir / "long_report_page_plan.md"
    json_path = report_dir / "long_report_page_plan.json"
    contract_path = report_dir / PAGE_PLAN_CONTRACT_FILENAME
    _write_markdown(
        md_path,
        "long_report_page_plan",
        [
            (
                "pages",
                [
                    f"第 {row['page_number']} 页 | {row['page_title']} | 管理问题={row['management_question']} | 页面目的={row['page_purpose']} | metric_ids={','.join(row['required_metrics'])} | 证据查询={row['evidence_query']}"
                    for row in pages
                ],
            )
        ],
    )
    _write_json(json_path, structured)
    write_json_artifact(contract_path, structured)
    schema_paths = _write_contract_schema_files(report_dir)
    return structured, [md_path, json_path, contract_path, *schema_paths]


def _page_draft_batch_output(raw_result: dict[str, Any], _: dict[str, Any], page_plan_batch: list[dict[str, Any]], report_dir: Path, page_drafts_dir: Path) -> tuple[dict[str, Any], list[Path]]:
    pages_payload = list(raw_result.get("pages") or [])
    if _validate_page_draft_batch_subset(pages_payload, page_plan_batch):
        drafts = pages_payload
    else:
        drafts = _build_page_drafts(pages_payload, page_plan_batch)
    written: list[Path] = []
    for draft in drafts:
        json_path = page_drafts_dir / f"page_{int(draft['page_number']):03d}.json"
        md_path = page_drafts_dir / f"page_{int(draft['page_number']):03d}.md"
        _write_json(json_path, draft)
        md_path.write_text(_render_page_markdown(draft), encoding="utf-8")
        written.extend([json_path, md_path])
    contract_path = report_dir / PAGE_DRAFTS_CONTRACT_FILENAME
    existing_contract = _read_json(contract_path).get("pages", []) if contract_path.exists() else []
    merged_contract = {"pages": _merge_page_draft_contract(existing_contract, drafts)}
    write_json_artifact(contract_path, merged_contract)
    schema_paths = _write_contract_schema_files(report_dir)
    return {"pages": drafts}, [*written, contract_path, *schema_paths]


def _run_page_plan_runtime_first(
    *,
    report_dir: Path,
    request_payload: dict[str, Any],
    runtime_child_task_creator: Callable[..., dict[str, Any]] | None,
    parent_report_id: str,
    input_payload: dict[str, Any],
) -> dict[str, Any]:
    prompt_template = (
        "You are Codex running the `long_report_page_plan` stage for Asteria Analyst generic_long_report.\n"
        "Use only the Context JSON below.\n"
        f"Write exactly one JSON file named `{PAGE_PLAN_CONTRACT_FILENAME}` into the current workspace.\n"
        "Do not use markdown fences.\n"
        "The JSON file must be an object with a top-level `pages` array.\n"
        "Each page must contain exactly the page-plan contract fields already implied by the Context JSON and existing chain.\n"
        "Keep the report between 35 and 50 pages.\n"
        "Every page must include concrete derived_metrics with metric_id values.\n"
        "Do not invent a new schema.\n\n"
        "Context JSON:\n{context_json}\n"
    )
    runtime_payload = _run_runtime_json_stage(
        report_dir=report_dir,
        request_payload=request_payload,
        runtime_child_task_creator=runtime_child_task_creator,
        parent_report_id=parent_report_id,
        stage_id="long_report_page_plan",
        purpose="long_report_page_plan",
        artifact_name=PAGE_PLAN_CONTRACT_FILENAME,
        prompt_template=prompt_template,
        context_payload=input_payload,
        validator=lambda payload: isinstance(payload, dict) and _ensure_page_plan_valid(list(payload.get("pages") or [])),
    )
    if runtime_payload is not None:
        runtime_payload["contract_artifacts"] = [describe_artifact(report_dir / PAGE_PLAN_CONTRACT_FILENAME)]
        return runtime_payload
    return codex_generic_long_page_plan(input_payload)


def _run_page_generation_batch_runtime_first(
    *,
    report_dir: Path,
    request_payload: dict[str, Any],
    runtime_child_task_creator: Callable[..., dict[str, Any]] | None,
    parent_report_id: str,
    input_payload: dict[str, Any],
    batch_index: int,
    page_plan_batch: list[dict[str, Any]],
) -> dict[str, Any]:
    prompt_template = (
        "You are Codex running the `page_generation_batch` stage for Asteria Analyst generic_long_report.\n"
        "Use only the Context JSON below.\n"
        f"Read `{PAGE_PLAN_CONTRACT_FILENAME}` from the workspace if needed.\n"
        f"Update or create exactly one JSON file named `{PAGE_DRAFTS_CONTRACT_FILENAME}` in the workspace.\n"
        "Do not use markdown fences.\n"
        "The JSON file must be an object with a top-level `pages` array using the existing page-draft contract.\n"
        "You must preserve any existing pages already present in the file and update only the current batch pages from the Context JSON.\n"
        "Every page must include `derived_metrics_used`: non-empty metric_id objects copied from page_plan. At least one derived metric must drive diagnosis, evidence, and recommended_action.trigger_metric.\n"
        "If a derived metric is only planned_only, use it only for metric definition or pending-execution guidance; do not write it as a current numeric fact.\n"
        "Do not invent a new schema.\n\n"
        "Context JSON:\n{context_json}\n"
    )
    runtime_payload = _run_runtime_json_stage(
        report_dir=report_dir,
        request_payload=request_payload,
        runtime_child_task_creator=runtime_child_task_creator,
        parent_report_id=parent_report_id,
        stage_id=f"page_generation_batch_{batch_index:02d}",
        purpose="page_generation_batch",
        artifact_name=PAGE_DRAFTS_CONTRACT_FILENAME,
        prompt_template=prompt_template,
        context_payload=input_payload,
        validator=lambda payload: isinstance(payload, dict) and bool(list(payload.get("pages") or [])),
    )
    if runtime_payload is not None:
        batch_numbers = set(_plan_page_numbers(page_plan_batch))
        runtime_payload["pages"] = [
            page
            for page in list(runtime_payload.get("pages") or [])
            if int(page.get("page_number") or 0) in batch_numbers
        ]
        runtime_payload["contract_artifacts"] = [describe_artifact(report_dir / PAGE_DRAFTS_CONTRACT_FILENAME)]
        return runtime_payload
    return codex_generic_page_generation_batch(input_payload)


def _review_output(name: str, raw_result: dict[str, Any], report_dir: Path) -> tuple[dict[str, Any], list[Path]]:
    path = report_dir / f"{name}.md"
    if name == "executive_readability_review":
        severe = [str(item.get("message") or item) for item in raw_result.get("issues") or [] if _safe_text((item.get("severity") if isinstance(item, dict) else "")).lower() == "high"]
        structured = {
            "verdict": _safe_text(raw_result.get("verdict") or "pass"),
            "serious_issues": severe,
            "revise_instructions": [str(item) for item in raw_result.get("revise_instructions") or [] if _safe_text(item)],
            "fixed_status": not severe,
        }
        _write_markdown(
            path,
            name,
            [
                ("verdict", [f"VERDICT: {'PASS' if structured['verdict'] == 'pass' else 'REPAIR_REQUIRED'}", f"READABILITY_DELIVERABLE: {'YES' if structured['verdict'] == 'pass' else 'NO'}"]),
                ("serious_issues", structured["serious_issues"] or ["SERIOUS_ISSUES: NONE"]),
                ("revise_instructions", structured["revise_instructions"] or ["当前摘要、动作表和页面结构已经满足管理层阅读要求"]),
                ("fixed_status", [f"SEVERE_ISSUES_FIXED: {'YES' if structured['fixed_status'] else 'NO'}"]),
            ],
        )
    elif name == "business_rigor_review":
        raw_score = raw_result.get("total_score")
        score = 0 if raw_score is None else int(raw_score)
        serious = [str(item) for item in raw_result.get("weaknesses") or [] if _safe_text(item)]
        fixed_status = score >= 90 and not serious
        structured = {
            "total_score": score,
            "verdict": _safe_text(raw_result.get("verdict") or ("pass" if fixed_status else "revise")),
            "serious_issues": serious if not fixed_status else [],
            "improvement_actions": [str(item) for item in raw_result.get("improvement_actions") or [] if _safe_text(item)],
            "fixed_status": fixed_status,
        }
        _write_markdown(
            path,
            name,
            [
                ("score", f"{structured['total_score']}"),
                ("verdict", [f"VERDICT: {'PASS' if fixed_status else 'REPAIR_REQUIRED'}", f"RIGOR_DELIVERABLE: {'YES' if fixed_status else 'NO'}"]),
                ("serious_issues", structured["serious_issues"] or ["SERIOUS_ISSUES: NONE"]),
                ("improvement_actions", structured["improvement_actions"] or ["字段边界与动作强度已同步收紧"]),
                ("fixed_status", [f"SEVERE_ISSUES_FIXED: {'YES' if fixed_status else 'NO'}"]),
            ],
        )
    else:
        raw_score = raw_result.get("total_score")
        score = 0 if raw_score is None else int(raw_score)
        severe = [str(item) for item in raw_result.get("weaknesses") or [] if _safe_text(item)]
        deliverable = score >= 90 and not severe
        structured = {
            "total_score": score,
            "deliverable": deliverable,
            "residual_issues": severe[:10],
            "recommend_pdf": deliverable,
        }
        _write_markdown(
            path,
            name,
            [
                ("deliverable", [f"DELIVERABLE_STATUS: {'PASS' if deliverable else 'BLOCK'}", f"RECOMMEND_PDF: {'YES' if deliverable else 'NO'}"]),
                ("score", f"FINAL_REVIEW_SCORE: {score}"),
                ("residual_issues", structured["residual_issues"] or ["无严重残留问题"]),
                ("recommendation", ["建议生成正式 PDF" if deliverable else "暂不建议生成正式 PDF"]),
            ],
        )
    return structured, [path]


def _split_batches(items: list[dict[str, Any]], batch_count: int) -> list[list[dict[str, Any]]]:
    if not items:
        return []
    size = math.ceil(len(items) / batch_count)
    return [items[index : index + size] for index in range(0, len(items), size)]


def _write_summary(report_dir: Path, call_records: list[dict[str, Any]], degraded_mode: bool, failed_passes: list[str]) -> None:
    path = report_dir / "codex_interpretation_summary.md"
    used_in_report = [
        "business_context_interpretation",
        "field_semantic_map",
        "metric_derivation_plan",
        "derived_metric_execution_review",
        "management_question_bank",
        "exploratory_interpretation",
        "object_level_interpretation",
        "interpretation_conflict_check",
        "long_report_page_plan",
        "page_generation_batch",
    ]
    blocked = [record["pass_name"] for record in call_records if record["status"] != "success" and record["status"] != "cache_hit"]
    _write_markdown(
        path,
        "codex_interpretation_summary",
        [
            ("total_calls", f"总调用次数：{len(call_records)}"),
            ("uses", [f"{record['pass_name']} | 用途={','.join(record.get('downstream_usage') or [])} | 状态={record['status']}" for record in call_records]),
            ("written_into_report", used_in_report),
            ("blocked_or_degraded", blocked or ["无"]),
            ("degraded_status", [f"degraded_mode={degraded_mode}", f"failed_passes={', '.join(failed_passes) or '无'}"]),
        ],
    )


def _write_degraded_state(report_dir: Path, failed_passes: list[str], fallback_sections: list[str]) -> None:
    _write_json(
        report_dir / "generic_long_ai_chain_degraded.json",
        {
            "failed_passes": failed_passes,
            "fallback_sections": fallback_sections,
            "degraded_claim_policy": "只允许观察级、风险提示级或补字段级结论；禁止 strict_90_pdf。",
            "why_pdf_is_not_strict_90": "required pass 失败、fallback_used=true、结构化 page plan/page draft 不完整，或审稿未确认可交付。",
        },
    )


def run_multi_pass_codex_interpretation_chain(
    *,
    report_dir: Path,
    parent_report_id: str = "",
    dataset_name: str,
    sheet_name: str,
    frame: pd.DataFrame,
    request: SmartReportRequest | dict[str, Any],
    field_registry: dict[str, Any],
    registry_payload: dict[str, Any],
    action_rows: list[dict[str, Any]],
    roadmap_payload: dict[str, Any],
    runtime_child_task_creator: Callable[..., dict[str, Any]] | None = None,
    repair_round: int = 0,
) -> dict[str, Any]:
    report_dir.mkdir(parents=True, exist_ok=True)
    page_drafts_dir = report_dir / "page_drafts"
    cache_dir = report_dir / "interpretation_cache"
    page_drafts_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)
    log_path = report_dir / "codex_interpretation_call_log.jsonl"
    log_path.write_text("", encoding="utf-8")

    request_payload = _to_request_dict(request)
    entity_column = _choose_entity_column(frame)
    top_entities = _top_entities(frame, entity_column, limit=30)
    registry_rows = list(registry_payload.get("rows") or [])
    metric_candidates = _build_metric_candidates(frame, field_registry)
    metric_rows = _compute_metric_rows(frame, metric_candidates)

    call_records: list[dict[str, Any]] = []
    failed_passes: list[str] = []
    fallback_sections: list[str] = []

    # 1 business context
    pass_result = _invoke_pass(
        report_dir=report_dir,
        cache_dir=cache_dir,
        log_path=log_path,
        pass_name="business_context_interpretation",
        required=True,
        input_payload={
            "dataset_name": dataset_name,
            "sheet_name": sheet_name,
            "request": request_payload,
            "field_registry": field_registry,
            "columns": frame.columns.astype(str).tolist()[:80],
            "sample_rows": clean_records(frame, limit=10),
        },
        runner=codex_complete_input_fields,
        build_output=lambda raw, payload: _business_context_output(raw, payload, dataset_name, sheet_name, request_payload, field_registry, entity_column, report_dir),
        downstream_usage=["field_semantic_map", "management_question_bank", "long_report_page_plan", "management_report"],
        min_output_length=PASS_MIN_LENGTHS["business_context_interpretation"],
    )
    call_records.append(pass_result["record"])
    if not pass_result["success"]:
        failed_passes.append("business_context_interpretation")
    business_context = pass_result["structured_output"]

    # 2 field semantics
    pass_result = _invoke_pass(
        report_dir=report_dir,
        cache_dir=cache_dir,
        log_path=log_path,
        pass_name="field_semantic_map",
        required=True,
        input_payload={
            "dataset_name": dataset_name,
            "sheet_name": sheet_name,
            "headers": frame.columns.astype(str).tolist()[:80],
            "sample_rows": clean_records(frame, limit=10),
            "column_summaries": build_column_summaries(frame)[:32],
        },
        runner=codex_semantic_analysis,
        build_output=lambda raw, payload: _field_semantic_output(raw, payload, frame, report_dir),
        downstream_usage=["metric_derivation_plan", "management_question_bank", "page_generation_batch", "management_report"],
        min_output_length=PASS_MIN_LENGTHS["field_semantic_map"],
    )
    call_records.append(pass_result["record"])
    if not pass_result["success"]:
        failed_passes.append("field_semantic_map")
    semantic_map = pass_result["structured_output"]

    # 3 metric derivation plan
    pass_result = _invoke_pass(
        report_dir=report_dir,
        cache_dir=cache_dir,
        log_path=log_path,
        pass_name="metric_derivation_plan",
        required=True,
        input_payload={
            "dataset_name": dataset_name,
            "sheet_name": sheet_name,
            "business_context": business_context,
            "field_semantic_map": semantic_map,
            "metric_candidates": metric_candidates,
        },
        runner=codex_generic_metric_derivation_plan,
        build_output=lambda raw, payload: _metric_derivation_output(raw, payload, metric_candidates, metric_rows, report_dir),
        downstream_usage=["derived_metric_execution_review", "long_report_page_plan", "page_generation_batch", "management_report"],
        min_output_length=PASS_MIN_LENGTHS["metric_derivation_plan"],
    )
    call_records.append(pass_result["record"])
    if not pass_result["success"]:
        failed_passes.append("metric_derivation_plan")
    metric_plan = pass_result["structured_output"]

    # 4 derived metric execution review
    pass_result = _invoke_pass(
        report_dir=report_dir,
        cache_dir=cache_dir,
        log_path=log_path,
        pass_name="derived_metric_execution_review",
        required=True,
        input_payload={
            "dataset_name": dataset_name,
            "sheet_name": sheet_name,
            "metric_candidates": [{"metric": row["metric_name"], "role": "候选派生指标", "management_question": row["metric_name"], "caution": row["comparison"]} for row in metric_rows[:12]],
            "numeric_summaries": [{"metric": row["metric_name"], "n": len(frame), "mean": row["value"], "median": row["value"], "std": None, "p25": None, "p75": None} for row in metric_rows[:12]],
            "method_findings": [],
            "core_purpose": request_payload.get("core_purpose", ""),
            "problem_to_solve": request_payload.get("problem_to_solve", ""),
        },
        runner=codex_metric_interpretation,
        build_output=lambda raw, payload: _derived_metric_execution_output(raw, payload, metric_rows, report_dir),
        downstream_usage=["long_report_page_plan", "page_generation_batch", "management_report"],
        min_output_length=PASS_MIN_LENGTHS["derived_metric_execution_review"],
    )
    call_records.append(pass_result["record"])
    if not pass_result["success"]:
        failed_passes.append("derived_metric_execution_review")
    metric_execution = pass_result["structured_output"]
    generic_kpi_tree = _build_kpi_tree_from_metrics(metric_execution.get("metrics") or metric_rows, field_registry)
    _write_markdown(
        report_dir / "generic_kpi_tree.md",
        "generic_kpi_tree",
        [
            (
                bucket,
                [
                    f"{item.get('metric_id')} | {item.get('metric')} | 值={item.get('value')} | 比较={item.get('comparison')} | 强度={item.get('evidence_strength')}"
                    for item in items
                ] or ["当前无稳定指标"],
            )
            for bucket, items in generic_kpi_tree.items()
        ],
    )
    _write_json(report_dir / "generic_kpi_tree.json", generic_kpi_tree)
    derived_metric_usage_contract = collect_derived_metric_usage_contract(
        workspace=report_dir,
        context_payload={
            "request": request_payload,
            "field_registry": field_registry,
            "metric_derivation_plan": metric_plan,
            "derived_metric_execution_review": metric_execution,
        },
        metric_rows=metric_rows,
        metric_execution=metric_execution,
        output_path=report_dir / "derived_metric_usage_contract.json",
    )

    # 5 question bank
    pass_result = _invoke_pass(
        report_dir=report_dir,
        cache_dir=cache_dir,
        log_path=log_path,
        pass_name="management_question_bank",
        required=True,
        input_payload={
            "dataset_name": dataset_name,
            "sheet_name": sheet_name,
            "user_requirement": request_payload.get("user_requirement", ""),
            "problem_to_solve": request_payload.get("problem_to_solve", ""),
            "target_audience": request_payload.get("target_audience", ""),
            "core_purpose": request_payload.get("core_purpose", ""),
            "expected_result": request_payload.get("expected_result", ""),
            "field_registry": field_registry,
        },
        runner=codex_generic_management_question_bank,
        build_output=lambda raw, payload: _question_bank_output(raw, payload, field_registry, report_dir),
        downstream_usage=["long_report_page_plan", "page_generation_batch", "management_report"],
        min_output_length=PASS_MIN_LENGTHS["management_question_bank"],
    )
    call_records.append(pass_result["record"])
    if not pass_result["success"]:
        failed_passes.append("management_question_bank")
    question_bank = pass_result["structured_output"]

    # 6 exploratory
    pass_result = _invoke_pass(
        report_dir=report_dir,
        cache_dir=cache_dir,
        log_path=log_path,
        pass_name="exploratory_interpretation",
        required=True,
        input_payload={
            "dataset_name": dataset_name,
            "sheet_name": sheet_name,
            "field_registry": field_registry,
            "metric_execution": metric_execution,
            "question_bank": question_bank,
            "top_entities": top_entities[:10],
            "sample_rows": clean_records(frame, limit=10),
        },
        runner=codex_generic_exploratory_interpretation,
        build_output=lambda raw, payload: _exploratory_output(raw, payload, frame, field_registry, metric_rows, registry_rows, report_dir),
        downstream_usage=["object_level_interpretation", "interpretation_conflict_check", "long_report_page_plan", "management_report"],
        min_output_length=PASS_MIN_LENGTHS["exploratory_interpretation"],
    )
    call_records.append(pass_result["record"])
    if not pass_result["success"]:
        failed_passes.append("exploratory_interpretation")
    exploratory = pass_result["structured_output"]

    # 7 object level interpretation
    object_batches = _split_batches(registry_rows if registry_rows else top_entities, 2 if len(registry_rows if registry_rows else top_entities) > 20 else 1)
    object_output = {"rows": []}
    for batch_index, batch in enumerate(object_batches, start=1):
        pass_result = _invoke_pass(
            report_dir=report_dir,
            cache_dir=cache_dir,
            log_path=log_path,
            pass_name="object_level_interpretation" if batch_index == 1 else f"object_level_interpretation_batch_{batch_index:02d}",
            required=True,
            input_payload={
                "dataset_name": dataset_name,
                "sheet_name": sheet_name,
                "business_context": business_context,
                "field_registry": field_registry,
                "objects": batch,
                "exploratory": exploratory,
            },
            runner=codex_business_object_interpretation,
            build_output=lambda raw, payload, batch_rows=batch, append=(batch_index > 1): _object_output(raw, payload, registry_rows, field_registry, batch_rows, report_dir, append),
            downstream_usage=["interpretation_conflict_check", "long_report_page_plan", "page_generation_batch", "management_report"],
            min_output_length=PASS_MIN_LENGTHS["object_level_interpretation"],
        )
        call_records.append(pass_result["record"])
        if not pass_result["success"]:
            failed_passes.append("object_level_interpretation")
        object_output = pass_result["structured_output"]

    # 8 conflict check
    pass_result = _invoke_pass(
        report_dir=report_dir,
        cache_dir=cache_dir,
        log_path=log_path,
        pass_name="interpretation_conflict_check",
        required=True,
        input_payload={
            "dataset_name": dataset_name,
            "sheet_name": sheet_name,
            "exploratory_interpretation": exploratory,
            "object_level_interpretation": object_output,
            "field_registry": field_registry,
        },
        runner=codex_challenge_review,
        build_output=lambda raw, payload: _conflict_output(raw, payload, field_registry, registry_payload, report_dir)[:2],
        downstream_usage=["long_report_page_plan", "page_generation_batch", "management_report"],
        min_output_length=PASS_MIN_LENGTHS["interpretation_conflict_check"],
    )
    call_records.append(pass_result["record"])
    if not pass_result["success"]:
        failed_passes.append("interpretation_conflict_check")
    conflict_output, _, adjusted_registry = _conflict_output(pass_result["raw_result"], pass_result["structured_output"], field_registry, registry_payload, report_dir)
    registry_payload = adjusted_registry

    # 9 page plan (AI primary, seed only as input)
    seed_plan = _seed_page_plan(field_registry, question_bank["questions"], metric_rows, registry_payload.get("rows") or [], exploratory)
    pass_result = _invoke_pass(
        report_dir=report_dir,
        cache_dir=cache_dir,
        log_path=log_path,
        pass_name="long_report_page_plan",
        required=True,
        input_payload={
            "dataset_name": dataset_name,
            "sheet_name": sheet_name,
            "business_context": business_context,
            "field_semantic_map": semantic_map,
            "metric_derivation_plan": metric_plan,
            "derived_metric_execution_review": metric_execution,
            "management_question_bank": question_bank,
            "exploratory_interpretation": exploratory,
            "object_level_interpretation": object_output,
            "seed_page_plan": seed_plan,
            "derived_metric_usage_contract": derived_metric_usage_contract,
        },
        runner=lambda payload: _run_page_plan_runtime_first(
            report_dir=report_dir,
            request_payload=request_payload,
            runtime_child_task_creator=runtime_child_task_creator,
            parent_report_id=parent_report_id,
            input_payload=payload,
        ),
        build_output=lambda raw, payload: _page_plan_output(raw, payload, seed_plan, metric_rows, report_dir),
        downstream_usage=["page_generation_batch", "management_report"],
        min_output_length=PASS_MIN_LENGTHS["long_report_page_plan"],
    )
    call_records.append(pass_result["record"])
    page_plan = pass_result["structured_output"]
    if page_plan.get("pages"):
        page_plan = {
            **page_plan,
            "pages": _enforce_page_plan_derived_metric_contract(
                list(page_plan.get("pages") or []),
                derived_metric_usage_contract,
            ),
        }
        _write_json(report_dir / "long_report_page_plan.json", page_plan)
        write_json_artifact(report_dir / PAGE_PLAN_CONTRACT_FILENAME, page_plan)
    if not pass_result["success"] or not _ensure_page_plan_valid(page_plan.get("pages") or []):
        failed_passes.append("long_report_page_plan")
        # one AI repair attempt before degraded mode
        repair_result = _invoke_pass(
            report_dir=report_dir,
            cache_dir=cache_dir,
            log_path=log_path,
            pass_name="long_report_page_plan_repair",
            required=True,
            input_payload={
                "dataset_name": dataset_name,
                "sheet_name": sheet_name,
                "repair_reason": pass_result["record"].get("error"),
                "seed_page_plan": seed_plan,
                "business_context": business_context,
                "metric_derivation_plan": metric_plan,
                "derived_metric_usage_contract": derived_metric_usage_contract,
                "management_question_bank": question_bank,
                "object_level_interpretation": object_output,
            },
            runner=lambda payload: _run_page_plan_runtime_first(
                report_dir=report_dir,
                request_payload=request_payload,
                runtime_child_task_creator=runtime_child_task_creator,
                parent_report_id=parent_report_id,
                input_payload=payload,
            ),
            build_output=lambda raw, payload: _page_plan_output(raw, payload, seed_plan, metric_rows, report_dir),
            downstream_usage=["page_generation_batch", "management_report"],
            min_output_length=PASS_MIN_LENGTHS["long_report_page_plan"],
        )
        call_records.append(repair_result["record"])
        repaired_page_plan = repair_result["structured_output"]
        if repaired_page_plan.get("pages"):
            repaired_page_plan = {
                **repaired_page_plan,
                "pages": _enforce_page_plan_derived_metric_contract(
                    list(repaired_page_plan.get("pages") or []),
                    derived_metric_usage_contract,
                ),
            }
        if repair_result["success"] and _ensure_page_plan_valid(repaired_page_plan.get("pages") or []):
            page_plan = repaired_page_plan
            _write_json(report_dir / "long_report_page_plan.json", page_plan)
            write_json_artifact(report_dir / PAGE_PLAN_CONTRACT_FILENAME, page_plan)
            failed_passes = [item for item in failed_passes if item != "long_report_page_plan"]
        else:
            page_plan = {
                "pages": _enforce_page_plan_derived_metric_contract(seed_plan, derived_metric_usage_contract)
            }
            _write_json(report_dir / "long_report_page_plan.json", page_plan)
            write_json_artifact(report_dir / PAGE_PLAN_CONTRACT_FILENAME, page_plan)

    # 10 page generation batches
    page_batches = _split_batches(list(page_plan.get("pages") or []), 8)
    all_drafts: list[dict[str, Any]] = []
    page_generation_fail = False
    for batch_index, batch in enumerate(page_batches, start=1):
        pass_result = _invoke_pass(
            report_dir=report_dir,
            cache_dir=cache_dir,
            log_path=log_path,
            pass_name=f"page_generation_batch_{batch_index:02d}",
            required=True,
            input_payload={
                "dataset_name": dataset_name,
                "sheet_name": sheet_name,
                "pages": batch,
                "business_context": business_context,
                "field_semantic_map": semantic_map,
                "metric_derivation_plan": metric_plan,
                "derived_metric_execution_review": metric_execution,
                "derived_metric_usage_contract": derived_metric_usage_contract,
                "exploratory_interpretation": exploratory,
                "object_level_interpretation": object_output,
            },
            runner=lambda payload, batch_rows=batch, current_batch_index=batch_index: _run_page_generation_batch_runtime_first(
                report_dir=report_dir,
                request_payload=request_payload,
                runtime_child_task_creator=runtime_child_task_creator,
                parent_report_id=parent_report_id,
                input_payload=payload,
                batch_index=current_batch_index,
                page_plan_batch=batch_rows,
            ),
            build_output=lambda raw, payload, batch_rows=batch: _page_draft_batch_output(raw, payload, batch_rows, report_dir, page_drafts_dir),
            downstream_usage=["management_report", "quality_gate", "independent_validator"],
            min_output_length=PASS_MIN_LENGTHS["page_generation_batch"],
        )
        call_records.append(pass_result["record"])
        if not pass_result["success"]:
            page_generation_fail = True
        all_drafts.extend(pass_result["structured_output"].get("pages") or [])
    if page_generation_fail or not _validate_page_drafts(all_drafts, list(page_plan.get("pages") or [])):
        failed_passes.append("page_generation_batch")
    page_plan_asset_metric_ids = []
    for page in list(page_plan.get("pages") or []):
        if not _safe_text(page.get("required_table_or_chart")):
            continue
        for metric in page.get("derived_metrics") or []:
            metric_id = _safe_text(metric.get("metric_id") if isinstance(metric, dict) else metric)
            if metric_id:
                page_plan_asset_metric_ids.append(metric_id)
    derived_metric_usage_summary = summarize_derived_metric_usage(
        contract=derived_metric_usage_contract,
        page_plan=list(page_plan.get("pages") or []),
        page_drafts=all_drafts,
        asset_coverage={"used_derived_metric_names": _dedupe(page_plan_asset_metric_ids)},
    )
    _write_json(report_dir / "derived_metric_usage_summary.json", derived_metric_usage_summary)
    try:
        assert_derived_metric_usage_gate(
            derived_metric_usage_contract,
            derived_metric_usage_summary,
            stage_name="generic_long_page_generation_batch",
        )
    except ValueError:
        if "derived_metric_usage_gate" not in failed_passes:
            failed_passes.append("derived_metric_usage_gate")

    # 11 readability review
    pass_result = _invoke_pass(
        report_dir=report_dir,
        cache_dir=cache_dir,
        log_path=log_path,
        pass_name="executive_readability_review",
        required=True,
        input_payload={
            "page_plan": page_plan,
            "page_drafts": all_drafts[:8],
            "derived_metric_usage_contract": derived_metric_usage_contract,
            "derived_metric_usage_summary": derived_metric_usage_summary,
            "action_rows": action_rows[:10],
            "seven_day_action_table": (roadmap_payload.get("seven_day_action_table") or [])[:10],
        },
        runner=codex_judge_feedback,
        build_output=lambda raw, payload: _review_output("executive_readability_review", raw, report_dir),
        downstream_usage=["management_report", "final_codex_interpretation_review", "quality_gate"],
        min_output_length=PASS_MIN_LENGTHS["executive_readability_review"],
    )
    call_records.append(pass_result["record"])
    if not pass_result["success"]:
        failed_passes.append("executive_readability_review")
    readability_review = pass_result["structured_output"]

    # 12 rigor review
    pass_result = _invoke_pass(
        report_dir=report_dir,
        cache_dir=cache_dir,
        log_path=log_path,
        pass_name="business_rigor_review",
        required=True,
        input_payload={
            "business_context": business_context,
            "field_registry": field_registry,
            "metric_derivation_plan": metric_plan,
            "derived_metric_usage_contract": derived_metric_usage_contract,
            "derived_metric_usage_summary": derived_metric_usage_summary,
            "page_plan": page_plan,
            "page_drafts": all_drafts[:8],
            "object_level_interpretation": object_output,
        },
        runner=codex_generic_business_rigor_review,
        build_output=lambda raw, payload: _review_output("business_rigor_review", raw, report_dir),
        downstream_usage=["management_report", "final_codex_interpretation_review", "quality_gate"],
        min_output_length=PASS_MIN_LENGTHS["business_rigor_review"],
    )
    call_records.append(pass_result["record"])
    if not pass_result["success"]:
        failed_passes.append("business_rigor_review")
    rigor_review = pass_result["structured_output"]

    # 13 final review
    required_success = not failed_passes
    pass_result = _invoke_pass(
        report_dir=report_dir,
        cache_dir=cache_dir,
        log_path=log_path,
        pass_name="final_codex_interpretation_review",
        required=True,
        input_payload={
            "business_context": business_context,
            "metric_derivation_plan": metric_plan,
            "derived_metric_usage_contract": derived_metric_usage_contract,
            "derived_metric_usage_summary": derived_metric_usage_summary,
            "page_plan": page_plan,
            "page_drafts": all_drafts[:8],
            "readability_review": readability_review,
            "rigor_review": rigor_review,
            "required_passes_success": required_success,
        },
        runner=codex_generic_final_review,
        build_output=lambda raw, payload: _review_output("final_codex_interpretation_review", raw, report_dir),
        downstream_usage=["management_report", "quality_gate", "independent_validator"],
        min_output_length=PASS_MIN_LENGTHS["final_codex_interpretation_review"],
    )
    call_records.append(pass_result["record"])
    if not pass_result["success"]:
        failed_passes.append("final_codex_interpretation_review")
    final_review = pass_result["structured_output"]

    degraded_mode = bool(failed_passes)
    if degraded_mode:
        fallback_sections = [record["pass_name"] for record in call_records if record["status"] == "fallback"]
        _write_degraded_state(report_dir, failed_passes, fallback_sections)

    _write_summary(report_dir, call_records, degraded_mode, failed_passes)
    readability_fixed = bool(readability_review.get("fixed_status"))
    rigor_fixed = bool(rigor_review.get("fixed_status"))
    final_review_score = int(final_review.get("total_score") or 0)

    return {
        "business_context": business_context,
        "field_semantic_map": semantic_map,
        "generic_kpi_tree": generic_kpi_tree,
        "metric_derivation_plan": metric_plan,
        "derived_metric_execution_review": metric_execution,
        "derived_metric_usage_contract": derived_metric_usage_contract,
        "derived_metric_usage_summary": derived_metric_usage_summary,
        "derived_metric_usage_contract_path": report_dir / "derived_metric_usage_contract.json",
        "derived_metric_usage_summary_path": report_dir / "derived_metric_usage_summary.json",
        "derived_metric_count": int(derived_metric_usage_contract.get("derived_metric_count") or 0),
        "used_derived_metric_names": list(derived_metric_usage_summary.get("used_derived_metric_names") or []),
        "missing_derived_metric_names": list(derived_metric_usage_summary.get("missing_derived_metric_names") or []),
        "derived_metric_coverage_ratio": float(derived_metric_usage_summary.get("derived_metric_coverage_ratio") or 0),
        "management_question_bank": question_bank,
        "exploratory_interpretation": exploratory,
        "object_level_interpretation": object_output,
        "interpretation_conflict_check": conflict_output,
        "long_report_page_plan": page_plan,
        "page_drafts": all_drafts,
        "registry_payload": registry_payload,
        "call_log_path": log_path,
        "page_drafts_dir": page_drafts_dir,
        "cache_dir": cache_dir,
        "contract_artifacts": {
            "page_plan": describe_artifact(report_dir / PAGE_PLAN_CONTRACT_FILENAME),
            "page_drafts": describe_artifact(report_dir / PAGE_DRAFTS_CONTRACT_FILENAME),
            "page_plan_schema": describe_artifact(report_dir / PAGE_PLAN_SCHEMA_FILENAME),
            "page_drafts_schema": describe_artifact(report_dir / PAGE_DRAFTS_SCHEMA_FILENAME),
            "derived_metric_usage_contract": describe_artifact(report_dir / "derived_metric_usage_contract.json"),
            "derived_metric_usage_summary": describe_artifact(report_dir / "derived_metric_usage_summary.json"),
        },
        "pass_records": {record["pass_name"]: record for record in call_records},
        "required_passes_success": not failed_passes,
        "failed_passes": failed_passes,
        "degraded_mode": degraded_mode,
        "strict_90_eligible": (
            (not degraded_mode)
            and readability_fixed
            and rigor_fixed
            and final_review_score >= 90
        ),
        "all_page_drafts_written": _validate_page_drafts(all_drafts, list(page_plan.get("pages") or [])),
        "final_review": final_review,
        "final_review_score": final_review_score,
    }
