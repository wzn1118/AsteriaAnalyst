from __future__ import annotations

from typing import Any


def build_evidence_digest_context(
    *,
    dataset_name: str,
    sheet_name: str,
    report_style: str,
    report_lens: str,
    request: dict[str, Any],
    requirement_layer: dict[str, Any],
    data_understanding: dict[str, Any],
    semantic_layer: dict[str, Any],
    metric_interpretation_layer: dict[str, Any],
    method_review_layer: dict[str, Any],
    business_background_layer: dict[str, Any],
    business_object_layer: dict[str, Any],
    codex_layer: dict[str, Any],
    sections: list[dict[str, Any]],
    relation_context: dict[str, Any] | None = None,
    context_compaction: dict[str, Any] | None = None,
) -> dict[str, Any]:
    compact_sections = [
        {
            "id": str(section.get("id") or ""),
            "title": str(section.get("title") or ""),
            "summary": str(section.get("summary") or ""),
            "bullets": [str(item) for item in (section.get("bullets") or [])[:4]],
        }
        for section in sections[:24]
    ]
    return {
        "dataset_name": dataset_name,
        "sheet_name": sheet_name,
        "report_style": report_style,
        "report_lens": report_lens,
        "request": request,
        "requirement_layer": requirement_layer,
        "data_understanding": data_understanding,
        "semantic_layer": semantic_layer,
        "metric_interpretation_layer": metric_interpretation_layer,
        "method_review_layer": method_review_layer,
        "business_background_layer": business_background_layer,
        "business_object_layer": business_object_layer,
        "codex_layer": codex_layer,
        "relation_context": relation_context or {},
        "context_compaction": context_compaction or {},
        "section_drafts": compact_sections,
    }


def evidence_digest_section(layer: dict[str, Any] | None) -> dict[str, Any] | None:
    if not layer:
        return None
    bullets = [str(item).strip() for item in (layer.get("priority_evidence") or []) if str(item).strip()]
    bullets.extend(str(item).strip() for item in (layer.get("key_boundaries") or [])[:2] if str(item).strip())
    if not bullets:
        return None
    rows = [
        {"证据类型": "关键指标", "内容": item}
        for item in (layer.get("key_metrics") or [])[:4]
    ] + [
        {"证据类型": "关键切片", "内容": item}
        for item in (layer.get("key_slices") or [])[:4]
    ] + [
        {"证据类型": "关键方法", "内容": item}
        for item in (layer.get("key_methods") or [])[:4]
    ]
    return {
        "id": "evidence_digest",
        "title": "证据摘要层",
        "summary": "这部分只保留最重要的证据视图，目的是让后续洞察和判断层在更短、更稳的证据底座上工作。",
        "bullets": bullets[:6],
        "tables": [
            {
                "title": "关键证据清单",
                "columns": ["证据类型", "内容"],
                "rows": rows[:12],
            }
        ]
        if rows
        else [],
        "charts": [],
    }
