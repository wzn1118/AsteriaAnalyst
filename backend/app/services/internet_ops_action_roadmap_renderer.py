from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


ALLOWED_ACTION_TYPES = {
    "补字段",
    "归因",
    "复核",
    "修复",
    "小流量验证",
    "加码",
    "降权",
    "止损",
    "观察",
    "优化",
}

FORBIDDEN_DIRECT_ACTIONS = {
    "直接加预算",
    "直接砍渠道",
    "直接主推内容",
    "直接扩大拉新",
    "直接判断 ROI 成立",
    "直接判断 LTV 高",
    "直接判断长期用户质量好",
}


def _truncate(text: str, limit: int = 120) -> str:
    value = str(text or "").strip()
    if len(value) <= limit:
        return value
    return value[: limit - 1] + "…"


def _priority(action_strength: str) -> str:
    if action_strength == "observe_only":
        return "P3"
    if action_strength == "candidate":
        return "P2"
    return "P1"


def _deadline(action_type: str, action_strength: str) -> str:
    if action_type == "止损":
        return "Day 1"
    if action_type == "降权":
        return "Day 2"
    if action_type == "加码":
        return "Day 2-Day 5"
    if action_type == "优化":
        return "Day 3-Day 5"
    if action_type == "观察":
        return "Day 6"
    if action_type == "补字段":
        return "T+3"
    if action_type == "归因":
        return "T+5"
    if action_type == "复核":
        return "T+7"
    if action_type == "修复":
        return "T+7"
    if action_type == "小流量验证":
        return "T+14"
    return "T+7"


def _guardrail_metric(row: dict[str, Any]) -> str:
    missing = list(row.get("missing_fields") or [])
    if "cost_fields" in missing:
        return "不得使用 ROI / CAC 下加预算结论"
    if "retention_fields" in missing:
        return "不得使用长期留存 / 黏性结论"
    if "revenue_fields" in missing:
        return "不得使用 LTV / 商业化效率结论"
    if "funnel_fields" in missing:
        return "不得使用完整漏斗健康结论"
    if "content_fields" in missing:
        return "不得使用内容主推结论"
    return "保持字段边界，不越级下强增长结论"


def _allowed_action_type(row: dict[str, Any]) -> str:
    final_action = str(row.get("final_action") or "")
    missing = list(row.get("missing_fields") or [])
    object_name = str(row.get("object_name") or "")
    if any(token in final_action for token in ["止损", "冻结", "刹车"]):
        return "止损"
    if any(token in final_action for token in ["降权", "砍", "暂停"]):
        return "降权"
    if any(token in final_action for token in ["加码", "放量", "倾斜"]):
        return "加码"
    if any(token in final_action for token in ["优化", "修复", "承接"]):
        return "优化"
    if "观察" in final_action:
        return "观察"
    if "补" in final_action:
        allowed_gap = any(token in object_name for token in ["Referral", "社群", "社区"]) or any(
            field in {"referral_fields", "engagement_fields", "community_fields"} for field in missing
        )
        return "补字段" if allowed_gap else "观察"
    if "归因" in final_action:
        return "归因"
    if "复核" in final_action or "观察" in final_action:
        return "复核"
    if "修复" in final_action:
        return "修复"
    if "测试" in final_action or "验证" in final_action:
        return "小流量验证"
    if row.get("sample_size_flag"):
        return "复核"
    return "复核"


def _input_data(row: dict[str, Any]) -> str:
    evidence = str(row.get("evidence_summary") or "").strip()
    missing = " / ".join(row.get("missing_fields") or [])
    if evidence and missing:
        return _truncate(f"{evidence} / 缺失字段={missing}", 150)
    if evidence:
        return _truncate(evidence, 150)
    if missing:
        return _truncate(f"缺失字段={missing}", 150)
    return "当前对象级证据"


def _output_result(action_type: str, row: dict[str, Any]) -> str:
    if action_type == "止损":
        return "冻结新增预算或流量入口，输出止损对象与原因清单"
    if action_type == "降权":
        return "完成预算/入口/内容位降权，并保留复核口径"
    if action_type == "加码":
        return "完成加码对象清单和资源倾斜方案"
    if action_type == "优化":
        return "完成承接链路、素材、活动或模块优化动作"
    if action_type == "观察":
        return "进入观察名单并明确下次复核条件"
    if action_type == "补字段":
        return _truncate(f"补齐 {(' / '.join(row.get('missing_fields') or [])) or '关键字段'} 并形成复核结论", 120)
    if action_type == "归因":
        return "形成归因结论并明确下一步修复动作"
    if action_type == "复核":
        return "完成低样本/异常对象复核并确认是否继续观察"
    if action_type == "修复":
        return "完成节点修复并进入下一轮验证"
    return "形成小流量验证结果并决定是否扩展实验"


def _success_standard(row: dict[str, Any], action_type: str) -> str:
    validation_metric = str(row.get("validation_metric") or "").strip()
    if validation_metric:
        return f"{validation_metric} 达到预期或完成补齐"
    if action_type in {"止损", "降权", "加码", "优化", "观察"}:
        return "roi / cac / CTR / retention_d7 / nps / paid_users / contribution_margin 至少一项改善或风险收敛"
    if action_type == "补字段":
        return "关键字段补齐并可复盘"
    if action_type == "小流量验证":
        return "实验指标达到预期且护栏指标稳定"
    return "形成可复核的对象级判断"


def _failure_handling(action_type: str) -> str:
    if action_type in {"加码", "优化"}:
        return "停止扩量，转入降权或止损复核"
    if action_type in {"止损", "降权"}:
        return "保留止损状态，进入原因拆解和下周复盘"
    if action_type == "观察":
        return "若 roi/cac/retention_d7 无改善，升级为降权或止损"
    if action_type == "小流量验证":
        return "停止扩量，回到补字段/归因阶段"
    if action_type == "修复":
        return "保留观察，追加埋点或补字段"
    return "回退到补字段或人工判断"


def build_7_day_action_table(registry_payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in registry_payload.get("rows") or []:
        action_type = _allowed_action_type(row)
        if action_type not in ALLOWED_ACTION_TYPES:
            action_type = "补字段"
        rows.append(
            {
                "优先级": _priority(str(row.get("action_strength") or "")),
                "动作": action_type,
                "对象": row.get("object_name", ""),
                "负责人角色": row.get("owner_role", ""),
                "输入数据": _input_data(row),
                "产出结果": _output_result(action_type, row),
                "截止时间": _deadline(action_type, str(row.get("action_strength") or "")),
                "验证标准": _success_standard(row, action_type),
                "护栏指标": _guardrail_metric(row),
                "依赖字段": " / ".join(row.get("missing_fields") or []),
                "当前结论强度": row.get("action_strength", ""),
            }
        )
    return rows


def _experiment_type(row: dict[str, Any]) -> str:
    object_level = str(row.get("object_level") or "")
    if object_level == "channel":
        return "获客实验"
    if object_level == "content":
        return "内容实验"
    if object_level == "campaign":
        return "获客实验"
    if object_level == "community":
        return "社区实验"
    if object_level == "page_function":
        if "激活" in str(row.get("final_label") or ""):
            return "激活实验"
        return "转化实验"
    if object_level == "user_segment":
        if "留存" in str(row.get("final_label") or "") or "流失" in str(row.get("final_label") or ""):
            return "留存实验"
        return "转化实验"
    return "获客实验"


def build_30_day_growth_experiment_backlog(registry_payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(registry_payload.get("rows") or [], start=1):
        experiment_type = _experiment_type(row)
        rows.append(
            {
                "实验编号": f"EXP-{index:03d}",
                "实验假设": f"{row.get('object_name', '当前对象')} 在执行 `{row.get('final_action', '验证动作')}` 后，关键指标会改善。",
                "目标用户": row.get("object_name", ""),
                "实验对象": experiment_type,
                "实验动作": row.get("final_action", ""),
                "核心指标": row.get("validation_metric", ""),
                "护栏指标": _guardrail_metric(row),
                "样本要求": "核心KPI样本覆盖率 >= 80% / 至少覆盖3个有效对象",
                "数据依赖": " / ".join(row.get("missing_fields") or []) or "当前已具备核心字段",
                "预计周期": "14-30天",
                "成功标准": _success_standard(row, "小流量验证"),
                "失败后处理": _failure_handling("小流量验证"),
                "结论类型": row.get("conclusion_type", ""),
            }
        )
    return rows


def build_forbidden_judgement_rows(field_registry: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not field_registry.get("has_cost_fields", False):
        rows.append({"禁止误判": "缺成本：不能判断 ROI、CAC、预算加码、渠道砍停。"})
    if not field_registry.get("has_retention_fields", False):
        rows.append({"禁止误判": "缺留存：不能判断用户长期质量、用户黏性、长期价值。"})
    if not field_registry.get("has_revenue_fields", False):
        rows.append({"禁止误判": "缺收入：不能判断商业化效率、LTV、高价值用户。"})
    if not field_registry.get("has_funnel_fields", False):
        rows.append({"禁止误判": "缺漏斗：不能判断完整转化链路健康。"})
    if not field_registry.get("has_content_fields", False):
        rows.append({"禁止误判": "缺内容字段：不能判断内容策略有效或作者表现。"})
    rows.append({"禁止误判": "缺实验数据：不能声称策略已经验证。"})
    return rows


def build_internet_ops_action_roadmap(
    registry_payload: dict[str, Any],
    field_registry: dict[str, Any],
) -> dict[str, Any]:
    action_rows = build_7_day_action_table(registry_payload)
    backlog_rows = build_30_day_growth_experiment_backlog(registry_payload)
    forbidden_rows = build_forbidden_judgement_rows(field_registry)
    return {
        "seven_day_action_table": action_rows,
        "thirty_day_growth_experiment_backlog": backlog_rows,
        "forbidden_judgement_rows": forbidden_rows,
    }


def write_internet_ops_action_roadmap_artifacts(
    output_dir: str | Path,
    roadmap_payload: dict[str, Any],
) -> dict[str, str]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    seven_day_path = output_path / "7_day_action_table.csv"
    backlog_path = output_path / "30_day_growth_experiment_backlog.csv"

    seven_day_rows = roadmap_payload.get("seven_day_action_table") or []
    backlog_rows = roadmap_payload.get("thirty_day_growth_experiment_backlog") or []

    if seven_day_rows:
        with seven_day_path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(seven_day_rows[0].keys()))
            writer.writeheader()
            for row in seven_day_rows:
                writer.writerow(row)

    if backlog_rows:
        with backlog_path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(backlog_rows[0].keys()))
            writer.writeheader()
            for row in backlog_rows:
                writer.writerow(row)

    return {
        "seven_day_csv": str(seven_day_path),
        "thirty_day_backlog_csv": str(backlog_path),
    }
