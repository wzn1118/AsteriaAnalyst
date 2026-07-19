from __future__ import annotations

from typing import Any, Iterable

import pandas as pd

from app.services.dataset_service import clean_records
from app.services.procurement_sales_relation_service import representative_rows_for_dimension

TEXT_JOINER = "；"

OBJECT_KEYS = ["对象", "商品", "SKU", "品类", "供应商", "卖家", "seller_id", "product_id", "sku_id", "category", "segment"]
REVENUE_KEYS = ["销售额", "Revenue", "GMV", "成交额", "占比", "数值", "value", "相关系数", "correlation", "数量", "count"]
ORDER_KEYS = ["订单覆盖", "订单总量", "订单量", "Orders", "OrderCount"]
CUSTOMER_KEYS = ["客户覆盖", "客户数", "Customers", "CustomerCount"]
ACTION_KEYS = ["合作建议", "经营判断", "当前用途", "业务含义", "判断依据", "business_meaning", "decision", "action"]


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none"}:
        return ""
    return text


def _first_present(row: dict[str, Any], keys: Iterable[str]) -> str:
    for key in keys:
        value = _stringify(row.get(key))
        if value and value.lower() != "n/a":
            return value
    return ""


def _compact_row_text(row: dict[str, Any]) -> str:
    if not row:
        return ""
    fields = [
        ("对象", _first_present(row, OBJECT_KEYS)),
        ("关键数值", _first_present(row, REVENUE_KEYS)),
        ("订单覆盖", _first_present(row, ORDER_KEYS)),
        ("客户覆盖", _first_present(row, CUSTOMER_KEYS)),
        ("动作/判断", _first_present(row, ACTION_KEYS)),
    ]
    parts = [f"{label} {value}" for label, value in fields if value]
    return TEXT_JOINER.join(parts)


def _compact_object_summary(dimension: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    representatives = representative_rows_for_dimension(rows)
    head = representatives.get("head") or {}
    middle = representatives.get("middle") or {}
    tail = representatives.get("tail") or {}
    return {
        "dimension": dimension,
        "row_count": len(rows),
        "head": head,
        "middle": middle,
        "tail": tail,
        "head_summary": _compact_row_text(head),
        "middle_summary": _compact_row_text(middle),
        "tail_summary": _compact_row_text(tail),
    }


def _dedupe(values: Iterable[str], *, limit: int | None = None) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        text = _stringify(value)
        if not text or text in seen:
            continue
        seen.add(text)
        ordered.append(text)
        if limit is not None and len(ordered) >= limit:
            break
    return ordered


def build_context_compaction_base(
    *,
    frame: pd.DataFrame,
    report_lens: str,
    rows_by_dimension: dict[str, list[dict[str, Any]]],
    relation_context: dict[str, Any],
) -> dict[str, Any]:
    raw_rows = {
        "observation_count": int(len(frame)),
        "column_count": int(len(frame.columns)),
        "columns": frame.columns.astype(str).tolist(),
        "sample_rows": clean_records(frame, limit=24),
    }
    object_summaries = [
        _compact_object_summary(dimension, rows)
        for dimension, rows in rows_by_dimension.items()
        if rows
    ]
    relation_matrix = {
        "dimension_profiles": relation_context.get("dimension_profiles", []),
        "relation_findings": relation_context.get("relation_findings", []),
    }
    return {
        "report_lens": report_lens,
        "raw_rows": raw_rows,
        "object_summaries": object_summaries,
        "relation_matrix": relation_matrix,
        "compact_evidence_pack": {},
        "judge_pack": {},
    }


def build_context_compaction(
    *,
    base: dict[str, Any],
    report: dict[str, Any],
    metric_interpretation_layer: dict[str, Any],
    method_review_layer: dict[str, Any],
    reasoning_layers: dict[str, Any],
    intelligence_runtime: dict[str, Any],
) -> dict[str, Any]:
    compact = dict(base)
    object_summaries = compact.get("object_summaries", [])
    relation_matrix = compact.get("relation_matrix") or {}
    relation_findings = relation_matrix.get("relation_findings") or []

    metric_cards = metric_interpretation_layer.get("metric_cards", []) or []
    method_reviews = method_review_layer.get("method_reviews", []) or []
    evidence_layer = reasoning_layers.get("evidence_digest_layer", {}) or {}
    insight_layer = reasoning_layers.get("insight_mining_layer", {}) or {}
    challenge_layer = reasoning_layers.get("challenge_layer", {}) or {}
    business_layer = reasoning_layers.get("business_judgement_layer", {}) or {}

    compact_evidence_pack = {
        "priority_evidence": _dedupe(
            [
                *relation_findings[:6],
                *(evidence_layer.get("priority_evidence") or [])[:8],
                *(insight_layer.get("important_findings") or [])[:4],
            ],
            limit=10,
        ),
        "key_metrics": _dedupe(
            [
                *(item.get("metric") for item in metric_cards[:8]),
                *(evidence_layer.get("key_metrics") or [])[:6],
            ],
            limit=8,
        ),
        "key_objects": _dedupe(
            [
                *(summary.get("head_summary") for summary in object_summaries[:8]),
                *(summary.get("middle_summary") for summary in object_summaries[:4]),
                *(summary.get("tail_summary") for summary in object_summaries[:4]),
            ],
            limit=10,
        ),
        "key_relations": _dedupe(relation_findings[:8], limit=8),
        "key_methods": _dedupe(
            [
                *(item.get("method") for item in method_reviews[:8]),
                *(evidence_layer.get("key_methods") or [])[:6],
            ],
            limit=8,
        ),
        "risk_signals": _dedupe(
            [
                *(challenge_layer.get("boundary_alerts") or [])[:5],
                *(challenge_layer.get("unresolved_gaps") or [])[:5],
                *(challenge_layer.get("overreach_risks") or [])[:3],
            ],
            limit=8,
        ),
    }

    judge_pack = {
        "executive_summary": report.get("executive_summary", [])[:6],
        "management_summary": _stringify(business_layer.get("management_summary")),
        "section_summaries": [
            {
                "id": section.get("id"),
                "title": section.get("title"),
                "summary": section.get("summary"),
                "bullets": (section.get("bullets") or [])[:4],
            }
            for section in report.get("sections", [])[:30]
        ],
        "object_summaries": object_summaries[:12],
        "relation_findings": relation_findings[:10],
        "priority_insights": insight_layer.get("priority_insights", [])[:8],
        "risk_signals": compact_evidence_pack["risk_signals"][:6],
        "runtime_status": intelligence_runtime,
    }

    compact["compact_evidence_pack"] = compact_evidence_pack
    compact["judge_pack"] = judge_pack
    return compact
