from __future__ import annotations

from typing import Any


def build_followup_mining_context(
    *,
    dataset_name: str,
    sheet_name: str,
    report_lens: str,
    request: dict[str, Any],
    report: dict[str, Any],
    business_judgement_layer: dict[str, Any],
    challenge_layer: dict[str, Any],
    semantic_expansion: dict[str, Any] | None = None,
    context_compaction: dict[str, Any] | None = None,
    fusion_context: dict[str, Any] | None = None,
    rows_by_dimension: dict[str, list[dict[str, Any]]] | None = None,
    gate_feedback_layer: dict[str, Any] | None = None,
) -> dict[str, Any]:
    compact_sections = [
        {
            "id": str(section.get("id") or ""),
            "title": str(section.get("title") or ""),
            "summary": str(section.get("summary") or ""),
            "bullets": [str(item) for item in (section.get("bullets") or [])[:4]],
        }
        for section in report.get("sections", [])[:24]
    ]
    return {
        "dataset_name": dataset_name,
        "sheet_name": sheet_name,
        "report_lens": report_lens,
        "request": request,
        "current_report": {
            "title": report.get("title"),
            "executive_summary": report.get("executive_summary", [])[:6],
            "sections": compact_sections,
        },
        "business_judgement_layer": business_judgement_layer,
        "challenge_layer": challenge_layer,
        "gate_feedback_layer": gate_feedback_layer or {},
        "semantic_expansion": semantic_expansion or {},
        "semantic_followup_prompts": (semantic_expansion or {}).get("followup_prompts", []),
        "context_compaction": context_compaction or {},
        "fusion_context": fusion_context or {},
        "rows_by_dimension": rows_by_dimension or (fusion_context or {}).get("rows_by_dimension") or {},
    }


def followup_mining_section(layer: dict[str, Any] | None) -> dict[str, Any] | None:
    if not layer:
        return None
    bullets = [str(item).strip() for item in (layer.get("section_bullets") or []) if str(item).strip()]
    if not bullets:
        bullets = [
            str(item.get("deeper_read") or "").strip()
            for item in (layer.get("drilldown_findings") or [])[:6]
            if str(item.get("deeper_read") or "").strip()
        ]
    rows = [
        {
            "洞察标题": item.get("title"),
            "触发结论": item.get("trigger_finding"),
            "继续挖到的结论": item.get("deeper_read"),
            "业务动作": item.get("business_move"),
            "证据锚点": item.get("evidence_refs"),
        }
        for item in (layer.get("drilldown_findings") or [])[:8]
        if item.get("title")
    ]
    if not bullets and not rows:
        return None
    return {
        "id": "followup_mining",
        "title": "继续深挖洞察",
        "summary": "这部分不是重复现有结论，而是把已经成立的判断再往下挖一层，优先拆出头部对象背后的结构矛盾、承接角色和止损点。",
        "bullets": bullets[:6],
        "tables": [
            {
                "title": "继续深挖洞察卡",
                "columns": ["洞察标题", "触发结论", "继续挖到的结论", "业务动作", "证据锚点"],
                "rows": rows,
            }
        ]
        if rows
        else [],
        "charts": [],
    }
