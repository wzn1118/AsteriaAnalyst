from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import pandas as pd


GENERIC_GROUPS = {
    "entity_fields": ["项目", "客户", "用户", "机构", "部门", "人员", "地区", "产品", "服务", "任务", "活动", "课程", "供应商", "object_id", "project", "customer", "department", "team", "region"],
    "time_fields": ["date", "month", "quarter", "year", "start", "end", "completed", "周期", "日期", "月份", "季度", "年份", "完成时间"],
    "category_fields": ["type", "category", "tag", "status", "level", "channel", "source", "region", "department", "project_type", "类型", "类别", "标签", "状态", "部门"],
    "volume_fields": ["count", "quantity", "number", "人数", "次数", "件数", "订单数", "任务数", "活动数", "服务次数", "参与人数"],
    "amount_fields": ["amount", "revenue", "cost", "budget", "expense", "price", "金额", "收入", "成本", "预算", "支出", "费用"],
    "progress_fields": ["progress", "completion", "达成率", "完成率", "milestone", "延期", "准时率", "阶段"],
    "quality_fields": ["score", "rating", "satisfaction", "complaint", "problem", "risk", "评分", "满意度", "投诉", "问题数", "风险等级"],
    "conversion_fields": ["register", "submit", "complete", "成交", "续约", "流转", "留存", "复购", "报名", "通过"],
    "people_fields": ["owner", "负责人", "执行人", "team", "岗位", "工时", "绩效", "培训"],
    "geography_fields": ["country", "province", "city", "district", "region", "store", "国家", "省", "市", "区县", "区域", "门店"],
    "text_feedback_fields": ["comment", "feedback", "remark", "note", "问题描述", "建议", "访谈", "评论", "反馈", "备注"],
    "target_fields": ["target", "plan", "budget_target", "kpi", "okr", "目标值", "计划值", "预算值", "KPI", "OKR"],
}

GENERIC_FORBIDDEN_BY_FIELD = {
    "target_fields": ["目标达成", "KPI完成", "绩效优秀", "超额完成", "未达标"],
    "amount_fields": ["投入产出比高", "成本效率高", "预算合理", "财务表现好", "ROI高"],
    "time_fields": ["趋势改善", "持续增长", "周期性下降", "同比提升", "环比变化"],
    "quality_fields": ["质量优秀", "满意度高", "问题改善", "服务质量稳定"],
}


def _compact(value: str) -> str:
    return "".join(ch for ch in str(value or "").lower().strip() if ch.isalnum() or "\u4e00" <= ch <= "\u9fff")


def _column_names(frame: pd.DataFrame) -> list[str]:
    return [str(column) for column in frame.columns]


def _match(columns: list[str], aliases: list[str]) -> dict[str, list[str]]:
    compact_columns = {column: _compact(column) for column in columns}
    compact_aliases = {alias: _compact(alias) for alias in aliases}
    matched_columns: list[str] = []
    matched_aliases: list[str] = []
    for column, compact_column in compact_columns.items():
        if not compact_column:
            continue
        for alias, compact_alias in compact_aliases.items():
            if compact_alias and (compact_alias == compact_column or compact_alias in compact_column):
                matched_columns.append(column)
                matched_aliases.append(alias)
                break
    return {
        "matched_columns": list(dict.fromkeys(matched_columns)),
        "matched_aliases": list(dict.fromkeys(matched_aliases)),
    }


def generic_field_availability_registry(frame: pd.DataFrame) -> dict[str, Any]:
    columns = _column_names(frame)
    matched: dict[str, Any] = {}
    registry: dict[str, Any] = {
        "business_profile": "generic_long_business_report",
    }
    for group_name, aliases in GENERIC_GROUPS.items():
        detail = _match(columns, aliases)
        matched[group_name] = detail
        registry[f"has_{group_name}"] = bool(detail["matched_columns"])
    registry["available_field_groups"] = [group for group in GENERIC_GROUPS if registry[f"has_{group}"]]
    registry["missing_field_groups"] = [group for group in GENERIC_GROUPS if not registry[f"has_{group}"]]
    registry["matched_field_signals"] = matched
    supported: list[str] = []
    if registry["has_entity_fields"]:
        supported.append("object_structure_review")
    if registry["has_time_fields"]:
        supported.append("time_trend_review")
    if registry["has_category_fields"]:
        supported.append("category_structure_review")
    if registry["has_geography_fields"]:
        supported.append("geography_review")
    if registry["has_amount_fields"]:
        supported.append("financial_operation_review")
    if registry["has_progress_fields"]:
        supported.append("progress_review")
    if registry["has_quality_fields"]:
        supported.append("quality_review")
    if registry["has_conversion_fields"]:
        supported.append("conversion_review")
    if registry["has_people_fields"]:
        supported.append("people_review")
    if registry["has_text_feedback_fields"]:
        supported.append("feedback_theme_review")
    if registry["has_target_fields"]:
        supported.append("target_gap_review")
    registry["supported_analysis_modules"] = supported
    registry["unsupported_analysis_modules"] = [
        item
        for item in [
            "object_structure_review",
            "time_trend_review",
            "category_structure_review",
            "geography_review",
            "financial_operation_review",
            "progress_review",
            "quality_review",
            "conversion_review",
            "people_review",
            "feedback_theme_review",
            "target_gap_review",
        ]
        if item not in supported
    ]
    if registry["has_entity_fields"] and registry["has_progress_fields"]:
        mode = "project_performance_review"
    elif registry["has_entity_fields"] and registry["has_conversion_fields"] and registry["has_quality_fields"]:
        mode = "customer_service_review"
    elif registry["has_amount_fields"]:
        mode = "financial_operation_review"
    elif registry["has_people_fields"]:
        mode = "organization_performance_review"
    elif registry["has_conversion_fields"] and registry["has_progress_fields"]:
        mode = "training_program_review"
    elif registry["has_entity_fields"] and registry["has_geography_fields"] and registry["has_quality_fields"]:
        mode = "nonprofit_project_review"
    elif registry["has_entity_fields"] and registry["has_time_fields"]:
        mode = "generic_management_review"
    elif sum(1 for group in registry["available_field_groups"] if group in {"entity_fields", "time_fields", "category_fields", "volume_fields", "amount_fields", "progress_fields", "quality_fields", "conversion_fields"}) >= 3:
        mode = "mixed_business_diagnostic_report"
    else:
        mode = "insufficient_for_management_decision"
    registry["report_mode"] = mode
    return registry


def generic_inference_controller(
    *,
    object_level: str,
    object_id: str,
    object_name: str,
    evidence: dict[str, Any],
    field_registry: dict[str, Any],
    sample_size: dict[str, Any] | None = None,
) -> dict[str, Any]:
    sample_size = sample_size or {}
    record_count = int(sample_size.get("record_count") or 0)
    entity_count = int(sample_size.get("entity_count") or 0)
    missing_fields: list[str] = []
    forbidden_actions: list[str] = []
    conclusion_type = "evidence_based_decision"
    confidence_level = "high"
    conclusion = "进入对象级复核"

    if record_count < 100 or entity_count < 20:
        conclusion_type = "risk_flag"
        confidence_level = "low"
        conclusion = "低样本复核"
        forbidden_actions.extend(["强管理动作"])

    if not field_registry.get("has_target_fields", False):
        missing_fields.append("target_fields")
        forbidden_actions.extend(GENERIC_FORBIDDEN_BY_FIELD["target_fields"])
    if not field_registry.get("has_amount_fields", False):
        missing_fields.append("amount_fields")
        forbidden_actions.extend(GENERIC_FORBIDDEN_BY_FIELD["amount_fields"])
    if not field_registry.get("has_time_fields", False):
        missing_fields.append("time_fields")
        forbidden_actions.extend(GENERIC_FORBIDDEN_BY_FIELD["time_fields"])
    if not field_registry.get("has_quality_fields", False):
        missing_fields.append("quality_fields")
        forbidden_actions.extend(GENERIC_FORBIDDEN_BY_FIELD["quality_fields"])
    if not field_registry.get("has_people_fields", False):
        missing_fields.append("people_fields")
    if not field_registry.get("has_entity_fields", False):
        missing_fields.append("entity_fields")

    if missing_fields and conclusion_type == "evidence_based_decision":
        conclusion_type = "proxy_based_inference" if evidence else "data_required"
        confidence_level = "medium" if evidence else "low"
        conclusion = "补字段验证"

    owner_role = "数据分析"
    if field_registry.get("has_people_fields", False):
        owner_role = "业务负责人 + 数据分析"
    return {
        "business_profile": "generic_long_business_report",
        "object_level": object_level,
        "object_id": object_id,
        "object_name": object_name,
        "evidence": " / ".join(f"{k}={v}" for k, v in evidence.items() if v not in (None, "", [], {})) or "当前无稳定证据",
        "missing_fields": list(dict.fromkeys(missing_fields)),
        "conclusion": conclusion,
        "conclusion_type": conclusion_type,
        "confidence_level": confidence_level,
        "forbidden_actions": list(dict.fromkeys(forbidden_actions)),
        "recommended_validation_action": "补字段验证" if missing_fields else "进入对象级复核",
        "validation_metric": "关键字段补齐 / 关键指标复核",
        "owner_role": owner_role,
        "time_requirement": "T+7 复核" if conclusion_type == "evidence_based_decision" else "T+3 补字段",
    }


def generic_action_guardrail(inference: dict[str, Any]) -> dict[str, Any]:
    blocked_reason = ""
    action_strength = "soft_action"
    final_action = str(inference.get("conclusion") or "补字段验证")
    if inference.get("conclusion_type") == "data_required":
        action_strength = "observe_only"
        final_action = "补字段验证"
    if "target_fields" in (inference.get("missing_fields") or []) and "达成" in final_action:
        blocked_reason = "缺目标字段，不能判断目标达成"
        final_action = "补字段验证"
    if "amount_fields" in (inference.get("missing_fields") or []) and any(term in final_action for term in ["成本", "预算", "ROI"]):
        blocked_reason = "缺金额字段，不能判断财务效率"
        final_action = "金额字段缺失，只能分析规模、进度或质量表现"
    if "time_fields" in (inference.get("missing_fields") or []) and any(term in final_action for term in ["趋势", "同比", "环比", "持续增长"]):
        blocked_reason = "缺时间字段，不能判断趋势"
        final_action = "时间字段缺失，只能做截面结构分析"
    if "quality_fields" in (inference.get("missing_fields") or []) and any(term in final_action for term in ["满意度", "质量", "问题改善"]):
        blocked_reason = "缺质量字段，无法判断质量表现"
        final_action = "质量字段缺失，无法判断质量表现"
    if "people_fields" in (inference.get("missing_fields") or []) and any(term in final_action for term in ["负责人", "团队", "归责"]):
        blocked_reason = "缺负责人字段，不能直接归责"
        final_action = "责任主体字段缺失，需要补充负责人/团队字段"
    return {
        **inference,
        "blocked_reason": blocked_reason,
        "blocked_actions": inference.get("forbidden_actions") or [],
        "action_strength": action_strength,
        "final_action": final_action,
    }


def build_generic_object_decision_registry(
    frame: pd.DataFrame,
    field_registry: dict[str, Any],
) -> dict[str, Any]:
    object_column = next(
        (
            column
            for column in frame.columns.astype(str).tolist()
            if any(token in column.lower() for token in ["project", "customer", "department", "team", "region", "service", "task", "course", "object", "机构", "项目", "客户", "部门", "地区", "活动", "课程", "任务"])
        ),
        None,
    )
    rows: list[dict[str, Any]] = []
    if object_column and object_column in frame.columns:
        counts = frame[object_column].astype(str).value_counts(dropna=True).head(20)
        for object_name, count in counts.items():
            inference = generic_inference_controller(
                object_level="entity",
                object_id=str(object_name),
                object_name=str(object_name),
                evidence={"record_count": int(count)},
                field_registry=field_registry,
                sample_size={"record_count": len(frame), "entity_count": int(counts.shape[0])},
            )
            guarded = generic_action_guardrail(inference)
            rows.append(
                {
                    "business_profile": "generic_long_business_report",
                    "report_mode": field_registry.get("report_mode", ""),
                    "object_level": "entity",
                    "object_id": str(object_name),
                    "object_name": str(object_name),
                    "final_label": "低样本观察对象" if guarded["conclusion_type"] == "risk_flag" else ("数据缺口对象" if guarded["conclusion_type"] == "data_required" else "高表现对象候选"),
                    "final_action": guarded["final_action"],
                    "action_strength": guarded["action_strength"],
                    "conclusion_type": guarded["conclusion_type"],
                    "confidence_level": guarded["confidence_level"],
                    "evidence_summary": guarded["evidence"],
                    "missing_fields": guarded["missing_fields"],
                    "blocked_actions": guarded["blocked_actions"],
                    "blocked_reason": guarded["blocked_reason"],
                    "sample_size_flag": "low_sample" if guarded["conclusion_type"] == "risk_flag" else "",
                    "owner_role": guarded["owner_role"],
                    "time_requirement": guarded["time_requirement"],
                    "validation_metric": guarded["validation_metric"],
                    "success_criteria": f"{guarded['validation_metric']} 达标或字段补齐",
                }
            )
    return {"rows": rows, "field_registry": field_registry}


def render_generic_action_table(registry_payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(registry_payload.get("rows") or [], start=1):
        rows.append(
            {
                "优先级": f"P{1 if index <= 5 else 2 if index <= 12 else 3}",
                "对象层级": row.get("object_level", ""),
                "对象名称": row.get("object_name", ""),
                "最终标签": row.get("final_label", ""),
                "触发证据": row.get("evidence_summary", ""),
                "现有证据类型": row.get("conclusion_type", ""),
                "缺失字段": " / ".join(row.get("missing_fields") or []),
                "被拦截动作": " / ".join(row.get("blocked_actions") or []),
                "最终动作": row.get("final_action", ""),
                "负责人角色": row.get("owner_role", ""),
                "时间要求": row.get("time_requirement", ""),
                "验证指标": row.get("validation_metric", ""),
                "成功标准": row.get("success_criteria", ""),
                "结论强度": row.get("action_strength", ""),
                "置信度": row.get("confidence_level", ""),
            }
        )
    return rows


def build_generic_action_roadmap(registry_payload: dict[str, Any], field_registry: dict[str, Any]) -> dict[str, Any]:
    action_rows = []
    backlog_rows = []
    for index, row in enumerate(registry_payload.get("rows") or [], start=1):
        action_rows.append(
            {
                "动作": "补字段" if row.get("missing_fields") else "复核",
                "负责人角色": row.get("owner_role", ""),
                "输入数据": row.get("evidence_summary", ""),
                "产出结果": row.get("final_action", ""),
                "截止时间": row.get("time_requirement", ""),
                "验证标准": row.get("validation_metric", ""),
                "护栏指标": "不得越权下强结论",
            }
        )
        backlog_rows.append(
            {
                "改进假设": f"{row.get('object_name', '当前对象')} 通过 {row.get('final_action', '验证动作')} 后，指标会改善。",
                "对象": row.get("object_name", ""),
                "动作": row.get("final_action", ""),
                "核心指标": row.get("validation_metric", ""),
                "护栏指标": "字段边界不越权",
                "样本要求": "record_count >= 100 / entity_count >= 20",
                "数据依赖": " / ".join(row.get("missing_fields") or []),
                "预计周期": "14-30天",
                "成功标准": row.get("success_criteria", ""),
                "失败后处理": "回退到补字段或人工判断",
            }
        )
    return {
        "seven_day_action_table": action_rows,
        "thirty_day_improvement_backlog": backlog_rows,
        "forbidden_judgement_rows": [
            {"禁止误判": "缺目标字段：不能判断目标达成/KPI完成。"} if not field_registry.get("has_target_fields", False) else {},
            {"禁止误判": "缺金额字段：不能判断 ROI、成本效率、预算合理。"} if not field_registry.get("has_amount_fields", False) else {},
            {"禁止误判": "缺时间字段：不能判断趋势、同比、环比。"} if not field_registry.get("has_time_fields", False) else {},
            {"禁止误判": "缺质量字段：不能判断满意度高、质量稳定。"} if not field_registry.get("has_quality_fields", False) else {},
            {"禁止误判": "缺负责人字段：不能直接做责任归因。"} if not field_registry.get("has_people_fields", False) else {},
        ],
    }


def write_generic_registry_artifacts(output_dir: str | Path, registry_payload: dict[str, Any], roadmap_payload: dict[str, Any]) -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    registry_csv_path = output_path / "generic_object_decision_registry.csv"
    action_csv_path = output_path / "7_day_action_table.csv"
    backlog_csv_path = output_path / "30_day_improvement_backlog.csv"
    field_json_path = output_path / "generic_field_availability_registry.json"

    registry_rows = registry_payload.get("rows") or []
    if registry_rows:
        with registry_csv_path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(registry_rows[0].keys()))
            writer.writeheader()
            for row in registry_rows:
                writer.writerow({**row, "missing_fields": " / ".join(row.get("missing_fields") or []), "blocked_actions": " / ".join(row.get("blocked_actions") or [])})

    action_rows = roadmap_payload.get("seven_day_action_table") or []
    if action_rows:
        with action_csv_path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(action_rows[0].keys()))
            writer.writeheader()
            for row in action_rows:
                writer.writerow(row)

    backlog_rows = roadmap_payload.get("thirty_day_improvement_backlog") or []
    if backlog_rows:
        with backlog_csv_path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(backlog_rows[0].keys()))
            writer.writeheader()
            for row in backlog_rows:
                writer.writerow(row)

    field_json_path.write_text(json.dumps(registry_payload.get("field_registry") or {}, ensure_ascii=False, indent=2), encoding="utf-8")
