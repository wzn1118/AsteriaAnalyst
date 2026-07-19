from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


ALLOWED_ACTION_TYPES = {"补字段", "复核", "归因", "修复", "小范围验证"}


def _priority(action_strength: str) -> str:
    if action_strength == "observe_only":
        return "P3"
    if action_strength == "candidate":
        return "P2"
    return "P1"


def _deadline(action_type: str) -> str:
    if action_type == "补字段":
        return "T+3"
    if action_type == "归因":
        return "T+5"
    if action_type == "复核":
        return "T+7"
    if action_type == "修复":
        return "T+7"
    return "T+14"


def _guardrail_metric(row: dict[str, Any]) -> str:
    missing = list(row.get("missing_fields") or [])
    if "margin_cost_fields" in missing:
        return "不得输出毛利/利润/ROI/加码判断"
    if "inventory_fields" in missing:
        return "不得输出补货/清仓/压货判断"
    if "fulfillment_fields" in missing:
        return "不得输出履约/物流问题拍板"
    if "aftersales_fields" in missing:
        return "不得输出售后风险拍板"
    if "review_fields" in missing:
        return "不得输出口碑判断"
    if "traffic_fields" in missing:
        return "不得输出曝光/点击问题判断"
    if "conversion_fields" in missing:
        return "不得输出漏斗断点拍板"
    if "time_fields" in missing:
        return "不得输出趋势/环比/同比判断"
    return "保持字段边界，不越权下强结论"


def _allowed_action_type(row: dict[str, Any]) -> str:
    final_action = str(row.get("final_action") or "")
    if "补" in final_action and "字段" in final_action:
        return "补字段"
    if "归因" in final_action:
        return "归因"
    if "复核" in final_action or "观察" in final_action:
        return "复核"
    if "修复" in final_action:
        return "修复"
    if "验证" in final_action or "测试" in final_action:
        return "小范围验证"
    if row.get("sample_size_flag"):
        return "复核"
    return "补字段"


def _input_data(row: dict[str, Any]) -> str:
    evidence = str(row.get("evidence_summary") or "").strip()
    missing = " / ".join(row.get("missing_fields") or [])
    if evidence and missing:
        return f"{evidence} / 缺失字段={missing}"
    if evidence:
        return evidence
    if missing:
        return f"缺失字段={missing}"
    return "当前对象级证据"


def _output_result(action_type: str, row: dict[str, Any]) -> str:
    if action_type == "补字段":
        return f"补齐 {(' / '.join(row.get('missing_fields') or [])) or '关键字段'} 并形成复核结论"
    if action_type == "归因":
        return "形成商品/类目/店铺问题归因结论"
    if action_type == "复核":
        return "完成低样本或异常对象复核并确认是否继续观察"
    if action_type == "修复":
        return "完成商品、库存、履约、售后或评价承接修复"
    return "形成小范围验证结果并决定是否继续扩大"


def _success_standard(row: dict[str, Any]) -> str:
    validation_metric = str(row.get("validation_metric") or "").strip()
    if validation_metric:
        return f"{validation_metric} 达到预期或完成补齐"
    return "形成可复核的经营判断"


def _failure_handling() -> str:
    return "回退到补字段、复核或小范围验证阶段"


def build_7_day_ecommerce_action_table(registry_payload: dict[str, Any]) -> list[dict[str, Any]]:
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
                "截止时间": _deadline(action_type),
                "验证标准": _success_standard(row),
                "护栏指标": _guardrail_metric(row),
                "依赖字段": " / ".join(row.get("missing_fields") or []),
                "当前结论强度": row.get("action_strength", ""),
            }
        )
    return rows


def _experiment_type(row: dict[str, Any]) -> str:
    object_level = str(row.get("object_level") or "")
    final_label = str(row.get("final_label") or "")
    if object_level == "product":
        if "价格" in final_label:
            return "商品实验"
        if "库存" in final_label:
            return "库存实验"
        return "商品实验"
    if object_level in {"category", "brand"}:
        return "流量实验"
    if object_level in {"shop_seller", "supplier"}:
        return "店铺/供应商实验"
    return "转化实验"


def build_30_day_ecommerce_experiment_backlog(registry_payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(registry_payload.get("rows") or [], start=1):
        experiment_type = _experiment_type(row)
        rows.append(
            {
                "实验编号": f"ECOM-EXP-{index:03d}",
                "实验假设": f"{row.get('object_name', '当前对象')} 在执行 `{row.get('final_action', '验证动作')}` 后，核心经营指标会改善。",
                "目标对象": row.get("object_name", ""),
                "实验动作": row.get("final_action", ""),
                "核心指标": row.get("validation_metric", ""),
                "护栏指标": _guardrail_metric(row),
                "样本要求": "order_count >= 50 / object_record_count >= 30 / product_count >= 20",
                "数据依赖": " / ".join(row.get("missing_fields") or []) or "当前已具备关键字段",
                "预计周期": "14-30天",
                "成功标准": _success_standard(row),
                "失败后处理": _failure_handling(),
                "结论类型": row.get("conclusion_type", ""),
                "实验类型": experiment_type,
            }
        )
    return rows


def build_ecommerce_forbidden_judgement_rows(field_registry: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not field_registry.get("has_margin_cost_fields", False):
        rows.append({"禁止误判": "缺毛利/成本：不能判断利润、ROI、加码价值。"})
    if not field_registry.get("has_inventory_fields", False):
        rows.append({"禁止误判": "缺库存：不能判断补货、清仓、压货。"})
    if not field_registry.get("has_fulfillment_fields", False):
        rows.append({"禁止误判": "缺履约：不能判断物流和发货问题。"})
    if not field_registry.get("has_aftersales_fields", False):
        rows.append({"禁止误判": "缺售后：不能判断退款退货风险。"})
    if not field_registry.get("has_review_fields", False):
        rows.append({"禁止误判": "缺评价：不能判断口碑。"})
    if not field_registry.get("has_traffic_fields", False):
        rows.append({"禁止误判": "缺流量：不能判断曝光和点击问题。"})
    if not field_registry.get("has_conversion_fields", False):
        rows.append({"禁止误判": "缺转化：不能判断漏斗断点。"})
    if not field_registry.get("has_time_fields", False):
        rows.append({"禁止误判": "缺时间：不能判断趋势、环比、同比。"})
    return rows


def build_ecommerce_action_roadmap(
    registry_payload: dict[str, Any],
    field_registry: dict[str, Any],
) -> dict[str, Any]:
    return {
        "seven_day_ecommerce_action_table": build_7_day_ecommerce_action_table(registry_payload),
        "thirty_day_ecommerce_experiment_backlog": build_30_day_ecommerce_experiment_backlog(registry_payload),
        "forbidden_judgement_rows": build_ecommerce_forbidden_judgement_rows(field_registry),
    }


def write_ecommerce_action_roadmap_artifacts(
    output_dir: str | Path,
    roadmap_payload: dict[str, Any],
) -> dict[str, str]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    seven_day_path = output_path / "7_day_ecommerce_action_table.csv"
    backlog_path = output_path / "30_day_ecommerce_experiment_backlog.csv"

    seven_day_rows = roadmap_payload.get("seven_day_ecommerce_action_table") or []
    backlog_rows = roadmap_payload.get("thirty_day_ecommerce_experiment_backlog") or []
    if seven_day_rows:
        with seven_day_path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(seven_day_rows[0].keys()))
            writer.writeheader()
            for row in seven_day_rows:
                writer.writerow(row)
    if backlog_rows:
        with backlog_path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(backlog_rows[0].keys()))
            writer.writeheader()
            for row in backlog_rows:
                writer.writerow(row)
    return {
        "seven_day_csv": str(seven_day_path),
        "thirty_day_backlog_csv": str(backlog_path),
    }
