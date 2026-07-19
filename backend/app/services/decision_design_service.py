from __future__ import annotations

from typing import Any


def build_decision_design_context(
    *,
    dataset_name: str,
    sheet_name: str,
    report_lens: str,
    request: dict[str, Any],
    business_judgement_layer: dict[str, Any],
    challenge_layer: dict[str, Any],
) -> dict[str, Any]:
    return {
        "dataset_name": dataset_name,
        "sheet_name": sheet_name,
        "report_lens": report_lens,
        "request": request,
        "business_judgement_layer": business_judgement_layer,
        "challenge_layer": challenge_layer,
    }


def decision_design_section(layer: dict[str, Any] | None) -> dict[str, Any] | None:
    if not layer:
        return None
    bullets = [str(item).strip() for item in (layer.get("scenario_options") or [])[:3] if str(item).strip()]
    bullets.extend(str(item).strip() for item in (layer.get("management_questions") or [])[:2] if str(item).strip())
    rows = [
        {
            "优先级": item.get("priority"),
            "动作": item.get("action"),
            "依据": item.get("rationale"),
            "执行顺序": item.get("sequence"),
            "验证信号": item.get("expected_signal"),
        }
        for item in (layer.get("priority_actions") or [])[:8]
        if item.get("action")
    ]
    if not rows and not bullets:
        return None
    return {
        "id": "decision_design",
        "title": "决策设计层",
        "summary": "这部分把业务判断翻成优先级、执行顺序、情景方案和验证议程，让报告从“有洞察”变成“能决策”。",
        "bullets": bullets[:6],
        "tables": [
            {
                "title": "决策路线图",
                "columns": ["优先级", "动作", "依据", "执行顺序", "验证信号"],
                "rows": rows,
            }
        ]
        if rows
        else [],
        "charts": [],
    }
