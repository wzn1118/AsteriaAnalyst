from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from app.services.internet_ops_profile_service import internet_ops_action_guardrail


STRENGTH_RANK = {
    "observe_only": 0,
    "candidate": 1,
    "soft_action": 2,
    "hard_action": 3,
}


def _truncate(text: str, limit: int = 120) -> str:
    value = str(text or "").strip()
    if len(value) <= limit:
        return value
    return value[: limit - 1] + "…"

MODULE_OBJECT_MAP = {
    "north_star_metric_selector": {"object_level": "metric", "object_id": "north_star_metric", "object_name": "北极星指标"},
    "aarrr_funnel_analyzer": {"object_level": "page_function", "object_id": "growth_funnel", "object_name": "AARRR漏斗"},
    "traffic_structure_analyzer": {"object_level": "channel", "object_id": "channel_portfolio", "object_name": "渠道池"},
    "user_growth_analyzer": {"object_level": "user_segment", "object_id": "user_segment_portfolio", "object_name": "用户分层"},
    "funnel_conversion_analyzer": {"object_level": "page_function", "object_id": "growth_funnel", "object_name": "核心转化漏斗"},
    "retention_cohort_analyzer": {"object_level": "user_segment", "object_id": "user_segment_portfolio", "object_name": "用户留存分层"},
    "content_operations_analyzer": {"object_level": "content", "object_id": "content_portfolio", "object_name": "内容资产池"},
    "content_asset_matrix": {"object_level": "content", "object_id": "content_portfolio", "object_name": "内容资产矩阵"},
    "channel_operations_analyzer": {"object_level": "channel", "object_id": "channel_portfolio", "object_name": "渠道池"},
    "campaign_operations_analyzer": {"object_level": "campaign", "object_id": "campaign_portfolio", "object_name": "活动池"},
    "community_operations_analyzer": {"object_level": "community", "object_id": "community_portfolio", "object_name": "社群运营"},
    "monetization_analyzer": {"object_level": "user_segment", "object_id": "monetization_users", "object_name": "付费用户群"},
    "risk_and_anomaly_analyzer": {"object_level": "page_function", "object_id": "risk_anomaly", "object_name": "风险与异常节点"},
}


def _evidence_type(conclusion_type: str) -> str:
    return {
        "evidence_based_decision": "直接字段证据",
        "proxy_based_inference": "代理指标证据",
        "business_hypothesis": "业务假设",
        "risk_flag": "风险提示",
        "data_required": "待补字段",
    }.get(str(conclusion_type or ""), "待补字段")


def _success_criteria(validation_metric: str, missing_fields: list[str]) -> str:
    if missing_fields:
        return f"{validation_metric or '关键字段'}补齐并可复核"
    if validation_metric:
        return f"{validation_metric} 改善或达标"
    return "形成可复核的经营判断"


def _priority(action_strength: str, blocked_actions: list[str]) -> str:
    if action_strength == "observe_only":
        return "P3"
    if blocked_actions:
        return "P1"
    if action_strength == "candidate":
        return "P2"
    return "P1"


def _sample_size_flag(module_payloads: list[dict[str, Any]]) -> str:
    for payload in module_payloads:
        sample_size = payload.get("sample_size") or {}
        if int(sample_size.get("user_count") or 0) < 100 or int(sample_size.get("event_count") or 0) < 500:
            return "low_sample"
    if any("低样本" in str(payload.get("core_conclusion") or "") for payload in module_payloads):
        return "low_sample"
    return ""


def _merged_evidence(module_payloads: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for payload in module_payloads:
        question = str(payload.get("business_question") or "").strip()
        conclusion = str(payload.get("core_conclusion") or "").strip()
        if question:
            parts.append(question)
        if conclusion:
            parts.append(conclusion)
    seen: list[str] = []
    for part in parts:
        if part not in seen:
            seen.append(part)
    return _truncate(" / ".join(seen[:4]), 180)


def _labels_for_group(
    *,
    object_id: str,
    object_level: str,
    object_name: str,
    module_payloads: list[dict[str, Any]],
    missing_fields: list[str],
    sample_size_flag: str,
) -> tuple[str, str]:
    combined_text = " ".join(
        [str(payload.get("core_conclusion") or "") for payload in module_payloads]
        + [str(payload.get("business_question") or "") for payload in module_payloads]
    )
    normalized_object_id = str(object_id or "").strip()
    if sample_size_flag:
        if object_level == "channel":
            return "低样本渠道复核", "低样本复核"
        if object_level == "content":
            return "低样本内容复核", "低样本复核"
        if object_level == "campaign":
            return "低样本活动复核", "低样本复核"
        return "低样本复核", "低样本复核"

    if object_level == "channel" and "cost_fields" in missing_fields:
        return "成本待补渠道", "观察"
    if object_level == "user_segment" and "revenue_fields" in missing_fields:
        return "付费潜力待验证用户群", "观察"

    if normalized_object_id == "north_star_metric":
        return "管理北极星指标组合", "北极星经营看板复盘"
    if normalized_object_id == "growth_funnel":
        return "AARRR漏斗可执行拆解", "AARRR漏斗转化拆解"
    if normalized_object_id == "risk_anomaly":
        return "风险与异常止损节点", "止损"
    if normalized_object_id == "user_segment_portfolio":
        return "用户分层经营对象池", "用户分层加码/降权/止损/观察"
    if normalized_object_id == "channel_portfolio":
        return "渠道池经营对象池", "渠道池加码/降权/止损/观察"

    if sample_size_flag:
        if object_level == "channel":
            return "低样本渠道复核", "低样本复核"
        if object_level == "content":
            return "低样本内容复核", "低样本复核"
        if object_level == "campaign":
            return "低样本活动复核", "低样本复核"
        return "低样本复核", "低样本复核"

    if object_level == "channel":
        if "cost_fields" in missing_fields:
            return "成本待复核渠道", "观察"
        if "风险" in combined_text or "异常" in combined_text:
            return "低质流量风险渠道", "止损"
        if "放量" in combined_text or "候选" in combined_text:
            return "放量候选渠道", "加码"
        return "高转化渠道候选", "加码"

    if object_level == "content":
        if "高曝光低互动" in combined_text:
            return "高曝光低互动内容", "优化"
        if "低曝光高互动" in combined_text:
            return "低曝光高互动内容", "加码"
        if "content_fields" in missing_fields or "funnel_fields" in missing_fields or "revenue_fields" in missing_fields:
            return "转化待复核内容", "观察"
        return "核心内容资产候选", "加码"

    if object_level == "user_segment":
        if "revenue_fields" in missing_fields:
            return "付费潜力待复核用户群", "观察"
        if "retention_fields" in missing_fields:
            return "低价值待复核用户群", "观察"
        if "流失" in combined_text:
            return "流失风险用户群", "止损"
        if "回流" in combined_text:
            return "回流用户群", "加码"
        return "高活跃用户群", "加码"

    if object_level == "campaign":
        if "campaign_fields" in missing_fields:
            return "活动复访待复核", "观察"
        if "风险" in combined_text or "不可判断" in combined_text:
            return "活动承接风险", "降权"
        if "高参与" in combined_text:
            return "高参与低转化活动", "优化"
        return "低参与高转化活动", "加码"

    if object_level == "page_function":
        if "funnel_fields" in missing_fields:
            return "数据埋点待复核节点", "观察"
        if "流失" in combined_text:
            return "高流失节点", "止损"
        if "激活" in combined_text:
            return "激活阻塞节点", "优化"
        if "转化" in combined_text:
            return "转化承接节点", "优化"
        return "高点击低转化节点", "降权"

    return object_name, "观察"


def _merge_object_payloads(
    *,
    business_profile: str,
    object_level: str,
    object_id: str,
    object_name: str,
    module_payloads: list[dict[str, Any]],
    field_registry: dict[str, Any],
) -> dict[str, Any]:
    sample_size_flag = _sample_size_flag(module_payloads)
    inferred_missing_fields: list[str] = []
    blocked_actions: list[str] = []
    confidence_levels: list[str] = []
    conclusion_types: list[str] = []
    for payload in module_payloads:
        inferred_missing_fields.extend(list(payload.get("missing_fields") or []))
        blocked_actions.extend(list(payload.get("forbidden_actions") or []))
        confidence_levels.append(str(payload.get("confidence_level") or "low"))
        conclusion_types.append(str(payload.get("conclusion_type") or "data_required"))
    missing_fields = list(dict.fromkeys(inferred_missing_fields))
    if object_id == "channel_portfolio" and not bool(field_registry.get("has_cost_fields")):
        missing_fields = list(dict.fromkeys([*missing_fields, "cost_fields"]))
    if object_id == "user_segment_portfolio" and not bool(field_registry.get("has_revenue_fields")):
        missing_fields = list(dict.fromkeys([*missing_fields, "revenue_fields"]))
    blocked_actions = list(dict.fromkeys(blocked_actions))
    final_label, attempted_action = _labels_for_group(
        object_id=object_id,
        object_level=object_level,
        object_name=object_name,
        module_payloads=module_payloads,
        missing_fields=missing_fields,
        sample_size_flag=sample_size_flag,
    )
    guardrail = internet_ops_action_guardrail(
        object_level=object_level,
        object_id=object_id,
        candidate_label=final_label,
        candidate_action=attempted_action,
        evidence={"facts": _merged_evidence(module_payloads)},
        field_availability_registry=field_registry,
        sample_size=(module_payloads[0].get("sample_size") or {}),
    )
    if blocked_actions:
        blocked_reason = guardrail.get("blocked_reason") or "字段缺失或低样本，强动作已被拦截"
    else:
        blocked_reason = guardrail.get("blocked_reason") or ""
    validation_metric = " / ".join(
        list(
            dict.fromkeys(
                [
                    str(payload.get("validation_metric") or "")
                    for payload in module_payloads
                    if str(payload.get("validation_metric") or "").strip()
                ]
            )
        )[:3]
    )
    owner_role = " + ".join(
        list(
            dict.fromkeys(
                [
                    str(payload.get("owner_role") or "")
                    for payload in module_payloads
                    if str(payload.get("owner_role") or "").strip()
                ]
            )
        )[:3]
    ) or guardrail.get("owner_role", "")
    time_requirement = " / ".join(
        list(
            dict.fromkeys(
                [
                    str(payload.get("time_requirement") or "")
                    for payload in module_payloads
                    if str(payload.get("time_requirement") or "").strip()
                ]
            )
        )[:2]
    ) or guardrail.get("time_requirement", "")
    confidence_level = "low"
    if "high" in confidence_levels:
        confidence_level = "high"
    elif "medium" in confidence_levels:
        confidence_level = "medium"
    conclusion_type = "data_required"
    for candidate in ["risk_flag", "business_hypothesis", "proxy_based_inference", "evidence_based_decision"]:
        if candidate in conclusion_types:
            conclusion_type = candidate
            break
    if any(payload.get("status") == "skipped" for payload in module_payloads) and conclusion_type == "data_required":
        conclusion_type = "risk_flag"
    success_criteria = _success_criteria(validation_metric, missing_fields)
    return {
        "business_profile": business_profile,
        "object_level": object_level,
        "object_id": object_id,
        "object_name": object_name,
        "final_label": final_label,
        "final_action": guardrail.get("downgraded_action") or attempted_action,
        "action_strength": guardrail.get("action_strength") or "candidate",
        "conclusion_type": conclusion_type,
        "confidence_level": confidence_level,
        "evidence_summary": _truncate(_merged_evidence(module_payloads), 180),
        "missing_fields": missing_fields,
        "blocked_actions": blocked_actions,
        "blocked_reason": blocked_reason,
        "sample_size_flag": sample_size_flag,
        "owner_role": owner_role,
        "time_requirement": time_requirement,
        "validation_metric": validation_metric,
        "success_criteria": success_criteria,
    }


def build_internet_ops_object_decision_registry(
    modules: dict[str, dict[str, Any]],
    field_registry: dict[str, Any],
) -> dict[str, Any]:
    grouped: dict[str, dict[str, Any]] = {}
    for module_id, payload in modules.items():
        mapping = MODULE_OBJECT_MAP.get(module_id)
        if not mapping:
            continue
        key = mapping["object_id"]
        grouped.setdefault(
            key,
            {
                "object_level": mapping["object_level"],
                "object_name": mapping["object_name"],
                "module_payloads": [],
            },
        )
        grouped[key]["module_payloads"].append(payload)

    rows: list[dict[str, Any]] = []
    for object_id, group in grouped.items():
        rows.append(
            _merge_object_payloads(
                business_profile="internet_operations_report",
                object_level=group["object_level"],
                object_id=object_id,
                object_name=group["object_name"],
                module_payloads=group["module_payloads"],
                field_registry=field_registry,
            )
        )

    conflicts: list[dict[str, Any]] = []
    seen: dict[str, tuple[str, str]] = {}
    for row in rows:
        key = str(row["object_id"])
        value = (str(row["final_label"]), str(row["final_action"]))
        previous = seen.get(key)
        if previous and previous != value:
            conflicts.append(
                {
                    "object_id": key,
                    "first": {"final_label": previous[0], "final_action": previous[1]},
                    "second": {"final_label": value[0], "final_action": value[1]},
                }
            )
        seen[key] = value

    return {
        "business_profile": "internet_operations_report",
        "action_source": "internet_ops_object_decision_registry",
        "rows": rows,
        "conflicting_object_actions": conflicts,
        "field_registry": field_registry,
        "modules": modules,
    }


def render_internet_ops_action_table(registry_payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in registry_payload.get("rows") or []:
        rows.append(
            {
                "优先级": _priority(str(item.get("action_strength") or ""), list(item.get("blocked_actions") or [])),
                "对象层级": item.get("object_level", ""),
                "对象名称": item.get("object_name", ""),
                "最终标签": item.get("final_label", ""),
                "触发证据": item.get("evidence_summary", ""),
                "现有证据类型": _evidence_type(str(item.get("conclusion_type") or "")),
                "缺失字段": " / ".join(item.get("missing_fields") or []),
                "被拦截动作": " / ".join(item.get("blocked_actions") or []),
                "最终动作": item.get("final_action", ""),
                "负责人角色": item.get("owner_role", ""),
                "时间要求": item.get("time_requirement", ""),
                "验证指标": item.get("validation_metric", ""),
                "成功标准": item.get("success_criteria", ""),
                "结论强度": item.get("action_strength", ""),
                "置信度": item.get("confidence_level", ""),
            }
        )
    return rows


def write_internet_ops_registry_artifacts(
    output_dir: str | Path,
    registry_payload: dict[str, Any],
) -> dict[str, str]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    registry_csv_path = output_path / "internet_ops_object_decision_registry.csv"
    action_csv_path = output_path / "internet_ops_action_table.csv"
    conflicts_json_path = output_path / "conflicting_actions_check.json"

    action_rows = render_internet_ops_action_table(registry_payload)

    registry_columns = [
        "business_profile",
        "object_level",
        "object_id",
        "object_name",
        "final_label",
        "final_action",
        "action_strength",
        "conclusion_type",
        "confidence_level",
        "evidence_summary",
        "missing_fields",
        "blocked_actions",
        "blocked_reason",
        "sample_size_flag",
        "owner_role",
        "time_requirement",
        "validation_metric",
        "success_criteria",
    ]
    with registry_csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=registry_columns)
        writer.writeheader()
        for row in registry_payload.get("rows") or []:
            writer.writerow(
                {
                    **row,
                    "missing_fields": " / ".join(row.get("missing_fields") or []),
                    "blocked_actions": " / ".join(row.get("blocked_actions") or []),
                }
            )

    action_columns = [
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
    ]
    with action_csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=action_columns)
        writer.writeheader()
        for row in action_rows:
            writer.writerow(row)

    conflicts_payload = {
        "passed": not bool(registry_payload.get("conflicting_object_actions")),
        "conflicting_object_actions": registry_payload.get("conflicting_object_actions") or [],
    }
    conflicts_json_path.write_text(json.dumps(conflicts_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "registry_csv": str(registry_csv_path),
        "action_table_csv": str(action_csv_path),
        "conflicts_json": str(conflicts_json_path),
    }
