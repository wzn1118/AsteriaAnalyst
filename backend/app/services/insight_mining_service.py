from __future__ import annotations

from typing import Any


def build_insight_mining_context(
    *,
    dataset_name: str,
    sheet_name: str,
    report_lens: str,
    request: dict[str, Any],
    evidence_digest_layer: dict[str, Any],
    business_background_layer: dict[str, Any],
    business_object_layer: dict[str, Any],
    relation_context: dict[str, Any] | None = None,
    context_compaction: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "dataset_name": dataset_name,
        "sheet_name": sheet_name,
        "report_lens": report_lens,
        "request": request,
        "evidence_digest_layer": evidence_digest_layer,
        "business_background_layer": business_background_layer,
        "business_object_layer": business_object_layer,
        "relation_context": relation_context or {},
        "context_compaction": context_compaction or {},
    }


def insight_mining_section(layer: dict[str, Any] | None) -> dict[str, Any] | None:
    if not layer:
        return None
    bullets = [str(item).strip() for item in (layer.get("important_findings") or []) if str(item).strip()]
    bullets.extend(str(item).strip() for item in (layer.get("mechanism_hypotheses") or [])[:2] if str(item).strip())
    if not bullets:
        return None
    rows = [
        {
            "洞察标题": item.get("title"),
            "为什么重要": item.get("why_it_matters"),
            "证据锚点": item.get("evidence_refs"),
        }
        for item in (layer.get("priority_insights") or [])[:8]
        if item.get("title")
    ]
    return {
        "id": "insight_mining",
        "title": "洞察挖掘层",
        "summary": "这部分只保留非显然、值得进入主报告的洞察，不重复底层指标和方法结果。",
        "bullets": bullets[:6],
        "tables": [
            {
                "title": "优先洞察卡",
                "columns": ["洞察标题", "为什么重要", "证据锚点"],
                "rows": rows,
            }
        ]
        if rows
        else [],
        "charts": [],
    }
