from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
import sys
import time
from collections import Counter
from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = CURRENT_DIR.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.context_compaction_service import build_context_compaction, build_context_compaction_base
from app.services.dataset_service import categorical_columns, load_dataset_frame, load_dataset_metadata, numeric_columns
from app.services.followup_mining_service import build_followup_mining_context
from app.services.generic_deep_mining_service import build_generic_relation_context, build_generic_rows_by_dimension
from app.services.path_service import REPORTS_DIR
from app.services.procurement_sales_relation_service import build_procurement_sales_relation_context
from app.services.report_service import (
    _build_procurement_sales_fusion_context,
    _category_mix_rows,
    _correlation_rows,
    _date_like_columns,
    _outlier_table,
    _preferred_category_column,
    _preferred_temporal_column,
    _procurement_sales_judge_context,
    _statistical_numeric_columns,
    _temporal_rows,
)
from app.services.codex_service import _fallback_followup_mining, _fallback_generic_deep_mining, _fallback_procurement_sales_judge


KEYWORDS: tuple[str, ...] = (
    "sales",
    "procurement",
    "purchase",
    "order",
    "seller",
    "supplier",
    "sku",
    "spu",
    "gmv",
    "revenue",
    "taobao",
    "jd",
    "product sales",
    "purchase order",
    "商品",
    "订单",
    "销售",
    "采销",
    "采购",
    "供应商",
    "履约",
)

STRONG_KEYWORDS: tuple[str, ...] = (
    "taobao",
    "olist",
    "procurement-sales",
    "sales data",
    "product sales",
    "purchase order",
    "采购",
    "采销",
    "销售",
    "订单",
    "供应商",
)

IGNORE_SHEET_NAMES: set[str] = {"contents", "content", "index", "readme", "说明", "目录"}
EXCLUDE_NAME_TERMS: tuple[str, ...] = (
    "smoke",
    "shape",
    "stock",
    "guizhoumaotai",
    "experiment",
    "benchmark",
    "画像",
    "ops-",
    "multi-sheet-demo",
)

SECTION_MAPPING: dict[str, tuple[str, str]] = {
    "品类": ("sales_category_impact", "品类经营影响评估"),
    "商品": ("sales_product_impact", "商品经营影响评估"),
    "SKU": ("sales_sku_impact", "SKU经营影响评估"),
    "供应商": ("sales_supplier_impact", "供应商协同与履约评估"),
}


@dataclass(slots=True)
class Candidate:
    dataset_id: str
    name: str
    row_count: int
    sheet_count: int
    active_sheet: str
    keyword_score: int


def _normalize_name(name: str) -> str:
    text = str(name or "").strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def _keyword_score(text: str) -> int:
    lowered = text.lower()
    score = sum(1 for token in KEYWORDS if token.lower() in lowered)
    score += 3 * sum(1 for token in STRONG_KEYWORDS if token.lower() in lowered)
    return score


def _pick_sheet_name(metadata: dict[str, Any]) -> str:
    sheets = metadata.get("sheets") or []
    active_sheet = str(metadata.get("active_sheet") or "").strip()
    if active_sheet and active_sheet.lower() not in IGNORE_SHEET_NAMES:
        return active_sheet
    if sheets:
        sorted_sheets = sorted(
            sheets,
            key=lambda item: (0 if str(item.get("name") or "").strip().lower() not in IGNORE_SHEET_NAMES else 1, -int(item.get("rows") or 0)),
        )
        return str(sorted_sheets[0].get("name") or active_sheet or "Sheet1")
    return active_sheet or "Sheet1"


def select_candidates(limit: int = 100, max_rows: int = 20000) -> list[Candidate]:
    dataset_root = REPORTS_DIR.parent / "datasets"
    rows: list[Candidate] = []
    for meta_path in dataset_root.glob("*/metadata.json"):
        try:
            metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        text = json.dumps(metadata, ensure_ascii=False)
        if not any(token.lower() in text.lower() for token in KEYWORDS):
            continue
        row_count = int(metadata.get("row_count") or 0)
        if row_count <= 0 or row_count > max_rows:
            continue
        name = str(metadata.get("name") or meta_path.parent.name).strip()
        lowered_name = name.lower()
        if any(term in lowered_name for term in EXCLUDE_NAME_TERMS):
            continue
        rows.append(
            Candidate(
                dataset_id=meta_path.parent.name,
                name=name,
                row_count=row_count,
                sheet_count=len(metadata.get("sheets") or []),
                active_sheet=_pick_sheet_name(metadata),
                keyword_score=_keyword_score(text),
            )
        )

    rows.sort(key=lambda item: (_normalize_name(item.name), item.row_count, item.sheet_count, item.dataset_id))
    unique: dict[str, Candidate] = {}
    for item in rows:
        key = _normalize_name(item.name)
        if key not in unique:
            unique[key] = item

    candidates = list(unique.values())
    candidates.sort(
        key=lambda item: (
            -item.keyword_score,
            0 if item.sheet_count == 1 else 1,
            item.row_count,
            item.dataset_id,
        )
    )
    return candidates[:limit]


def _minimal_section_rows(rows: list[dict[str, Any]], *, limit: int = 50) -> list[dict[str, Any]]:
    return rows[:limit]


def _build_minimal_report(
    *,
    dataset_name: str,
    sheet_name: str,
    rows_by_dimension: dict[str, list[dict[str, Any]]],
    relation_context: dict[str, Any],
    followup_layer: dict[str, Any],
) -> dict[str, Any]:
    sections: list[dict[str, Any]] = []
    for dimension, (section_id, title) in SECTION_MAPPING.items():
        rows = rows_by_dimension.get(dimension) or []
        if not rows:
            continue
        sections.append(
            {
                "id": section_id,
                "title": title,
                "summary": f"{dimension}层对象已整理为头中尾代表对象与判断依据。",
                "bullets": [str(item.get("判断依据") or "") for item in rows[:3] if str(item.get("判断依据") or "").strip()],
                "tables": [
                    {
                        "title": f"{title}表",
                        "columns": list(rows[0].keys()) if rows else [],
                        "rows": _minimal_section_rows(rows),
                    }
                ]
                if rows
                else [],
            }
        )
    sections.append(
        {
            "id": "followup_mining",
            "title": "继续深挖洞察",
            "summary": str(followup_layer.get("headline") or "继续深挖已有结构与关系线索。"),
            "bullets": [str(item).strip() for item in (followup_layer.get("section_bullets") or [])[:6] if str(item).strip()],
            "tables": [
                {
                    "title": "继续深挖洞察表",
                    "columns": ["标题", "触发", "深读", "动作", "证据"],
                    "rows": [
                        {
                            "标题": item.get("title"),
                            "触发": item.get("trigger_finding"),
                            "深读": item.get("deeper_read"),
                            "动作": item.get("business_move"),
                            "证据": item.get("evidence_refs"),
                        }
                        for item in (followup_layer.get("drilldown_findings") or [])[:8]
                        if item.get("title")
                    ],
                }
            ]
            if followup_layer.get("drilldown_findings")
            else [],
        }
    )
    return {
        "report_lens": "procurement_sales_review",
        "dataset_name": dataset_name,
        "sheet_name": sheet_name,
        "executive_summary": [str(item).strip() for item in relation_context.get("relation_findings", [])[:4] if str(item).strip()],
        "sections": sections,
    }


def evaluate_candidate(candidate: Candidate) -> dict[str, Any]:
    started = time.perf_counter()
    metadata = load_dataset_metadata(candidate.dataset_id)
    frame, _, _ = load_dataset_frame(candidate.dataset_id, candidate.active_sheet)

    num_cols = numeric_columns(frame)
    temporal_cols = _date_like_columns(frame)
    categorical_cols = categorical_columns(frame, num_cols, temporal_cols)
    stat_numeric_cols = _statistical_numeric_columns(frame, num_cols, temporal_cols)
    correlation_rows = _correlation_rows(frame, stat_numeric_cols)
    primary_category_column = _preferred_category_column(categorical_cols, "procurement_sales_review")
    category_rows = _category_mix_rows(frame, primary_category_column) if primary_category_column else []
    temporal_value_column = next((column for column in stat_numeric_cols if column != (_preferred_temporal_column(temporal_cols, report_lens="procurement_sales_review") or (temporal_cols[0] if temporal_cols else None))), None) if temporal_cols and stat_numeric_cols else None
    temporal_rows = _temporal_rows(frame, _preferred_temporal_column(temporal_cols, report_lens="procurement_sales_review") or temporal_cols[0], temporal_value_column) if temporal_cols and temporal_value_column else []
    outlier_rows = _outlier_table(frame, stat_numeric_cols)

    program_bundle = {"lens": "procurement_sales_review"}
    fusion_context = _build_procurement_sales_fusion_context(frame=frame, program_bundle=program_bundle) or {}
    fusion_enabled = bool(fusion_context.get("procurement_sales_management"))
    generic_rows_by_dimension = build_generic_rows_by_dimension(
        primary_category_column=primary_category_column,
        category_rows=category_rows,
        temporal_rows=temporal_rows,
        correlation_rows=correlation_rows,
        outlier_rows=outlier_rows,
    )
    rows_by_dimension = (fusion_context.get("rows_by_dimension") or {}) if fusion_enabled else generic_rows_by_dimension
    relation_context = (
        build_procurement_sales_relation_context(rows_by_dimension)
        if fusion_enabled
        else build_generic_relation_context(
            rows_by_dimension=generic_rows_by_dimension,
            primary_category_column=primary_category_column,
            category_rows=category_rows,
            temporal_rows=temporal_rows,
            correlation_rows=correlation_rows,
            outlier_rows=outlier_rows,
        )
    )

    context_compaction = build_context_compaction(
        base=build_context_compaction_base(
            frame=frame,
            report_lens="procurement_sales_review",
            rows_by_dimension=rows_by_dimension,
            relation_context=relation_context,
        ),
        report={"title": candidate.name, "executive_summary": relation_context.get("relation_findings", [])[:4], "sections": []},
        metric_interpretation_layer={},
        method_review_layer={},
        reasoning_layers={
            "evidence_digest_layer": {},
            "insight_mining_layer": {},
            "challenge_layer": {},
            "business_judgement_layer": {},
        },
        intelligence_runtime={},
    )

    if fusion_enabled:
        followup_layer = _fallback_followup_mining(
            "batch_structural_scoring",
            build_followup_mining_context(
                dataset_name=candidate.name,
                sheet_name=candidate.active_sheet,
                report_lens="procurement_sales_review",
                request={"user_requirement": "采销批量评测"},
                report={"title": candidate.name, "executive_summary": relation_context.get("relation_findings", [])[:4], "sections": []},
                business_judgement_layer={},
                challenge_layer={},
                semantic_expansion={},
                context_compaction=context_compaction,
                fusion_context=fusion_context,
                rows_by_dimension=rows_by_dimension,
            ),
        )
    else:
        followup_layer = _fallback_generic_deep_mining(
            "batch_structural_scoring",
            {
                "category_rows": category_rows,
                "temporal_rows": temporal_rows,
                "correlation_rows": correlation_rows,
                "outlier_rows": outlier_rows,
                "relation_context": relation_context,
                "context_compaction": context_compaction,
            },
        )

    report = _build_minimal_report(
        dataset_name=candidate.name,
        sheet_name=candidate.active_sheet,
        rows_by_dimension=rows_by_dimension,
        relation_context=relation_context,
        followup_layer=followup_layer,
    )
    context_compaction = build_context_compaction(
        base=build_context_compaction_base(
            frame=frame,
            report_lens="procurement_sales_review",
            rows_by_dimension=rows_by_dimension,
            relation_context=relation_context,
        ),
        report=report,
        metric_interpretation_layer={},
        method_review_layer={},
        reasoning_layers={
            "evidence_digest_layer": {},
            "insight_mining_layer": {},
            "challenge_layer": {},
            "business_judgement_layer": {},
        },
        intelligence_runtime={"critical_layers": [], "hard_degraded": False},
    )

    gate = _fallback_procurement_sales_judge(
        "batch_structural_scoring",
        _procurement_sales_judge_context(
            report=report,
            relation_context=relation_context,
            intelligence_runtime={"critical_layers": [], "fallback_layers": [], "hard_degraded": False},
            context_compaction=context_compaction,
        ),
    )

    elapsed = round(time.perf_counter() - started, 3)
    return {
        "dataset_id": candidate.dataset_id,
        "dataset_name": candidate.name,
        "sheet_name": candidate.active_sheet,
        "row_count": candidate.row_count,
        "sheet_count": candidate.sheet_count,
        "keyword_score": candidate.keyword_score,
        "fusion_enabled": fusion_enabled,
        "score_mode": "structural_local_procurement_gate",
        "score": int(gate.get("total_score") or 0),
        "threshold": int(gate.get("threshold") or 80),
        "verdict": str(gate.get("verdict") or "block"),
        "strengths": gate.get("strengths") or [],
        "weaknesses": gate.get("weaknesses") or [],
        "improvement_actions": gate.get("improvement_actions") or [],
        "relation_findings": relation_context.get("relation_findings") or [],
        "rows_by_dimension": list(rows_by_dimension.keys()),
        "elapsed_seconds": elapsed,
    }


def summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    scores = [int(item["score"]) for item in results]
    verdict_counter = Counter(str(item["verdict"]) for item in results)
    weakness_counter = Counter()
    action_counter = Counter()
    dimension_counter = Counter()
    for item in results:
        weakness_counter.update(str(text) for text in item.get("weaknesses", []) if str(text).strip())
        action_counter.update(str(text) for text in item.get("improvement_actions", []) if str(text).strip())
        dimension_counter.update(str(text) for text in item.get("rows_by_dimension", []) if str(text).strip())
    return {
        "dataset_count": len(results),
        "average_score": round(sum(scores) / len(scores), 2) if scores else 0,
        "median_score": statistics.median(scores) if scores else 0,
        "min_score": min(scores) if scores else 0,
        "max_score": max(scores) if scores else 0,
        "pass_count": int(verdict_counter.get("pass", 0)),
        "block_count": int(verdict_counter.get("block", 0)),
        "fusion_enabled_count": sum(1 for item in results if item.get("fusion_enabled")),
        "top_weaknesses": weakness_counter.most_common(12),
        "top_improvement_actions": action_counter.most_common(12),
        "top_dimensions": dimension_counter.most_common(12),
        "top_scores": sorted(results, key=lambda item: (-int(item["score"]), item["dataset_name"]))[:10],
        "bottom_scores": sorted(results, key=lambda item: (int(item["score"]), item["dataset_name"]))[:10],
    }


def write_outputs(output_dir: Path, candidates: list[Candidate], results: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "selected_datasets.json").write_text(
        json.dumps([asdict(candidate) for candidate in candidates], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "batch_results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with (output_dir / "batch_results.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "dataset_id",
                "dataset_name",
                "sheet_name",
                "row_count",
                "sheet_count",
                "keyword_score",
                "fusion_enabled",
                "score_mode",
                "score",
                "threshold",
                "verdict",
                "elapsed_seconds",
            ],
        )
        writer.writeheader()
        for row in results:
            writer.writerow({key: row.get(key) for key in writer.fieldnames})

    summary_lines = [
        "# Procurement-Sales Batch Scoring",
        "",
        f"- Generated at: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Dataset count: `{summary['dataset_count']}`",
        f"- Score mode: `structural_local_procurement_gate`",
        f"- Average score: `{summary['average_score']}`",
        f"- Median score: `{summary['median_score']}`",
        f"- Score range: `{summary['min_score']} - {summary['max_score']}`",
        f"- Pass count: `{summary['pass_count']}`",
        f"- Block count: `{summary['block_count']}`",
        f"- Fusion-enabled count: `{summary['fusion_enabled_count']}`",
        "",
        "## Top Weaknesses",
        "",
    ]
    for text, count in summary["top_weaknesses"]:
        summary_lines.append(f"- `{count}` x {text}")
    summary_lines.extend(["", "## Top Improvement Actions", ""])
    for text, count in summary["top_improvement_actions"]:
        summary_lines.append(f"- `{count}` x {text}")
    summary_lines.extend(["", "## Top Scores", ""])
    for item in summary["top_scores"]:
        summary_lines.append(f"- `{item['score']}` | `{item['dataset_id']}` | {item['dataset_name']}")
    summary_lines.extend(["", "## Bottom Scores", ""])
    for item in summary["bottom_scores"]:
        summary_lines.append(f"- `{item['score']}` | `{item['dataset_id']}` | {item['dataset_name']}")
    (output_dir / "summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch-score 100 procurement/sales related datasets.")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--max-rows", type=int, default=20000)
    args = parser.parse_args()

    candidates = select_candidates(limit=args.limit, max_rows=args.max_rows)
    results: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates, start=1):
        print(f"[{index}/{len(candidates)}] {candidate.dataset_id} | {candidate.name}")
        try:
            results.append(evaluate_candidate(candidate))
        except Exception as exc:
            results.append(
                {
                    "dataset_id": candidate.dataset_id,
                    "dataset_name": candidate.name,
                    "sheet_name": candidate.active_sheet,
                    "row_count": candidate.row_count,
                    "sheet_count": candidate.sheet_count,
                    "keyword_score": candidate.keyword_score,
                    "fusion_enabled": False,
                    "score_mode": "structural_local_procurement_gate",
                    "score": 0,
                    "threshold": 80,
                    "verdict": "error",
                    "strengths": [],
                    "weaknesses": [f"batch_error: {exc}"],
                    "improvement_actions": ["检查数据装载或评测脚本异常。"],
                    "relation_findings": [],
                    "rows_by_dimension": [],
                    "elapsed_seconds": 0,
                }
            )

    summary = summarize_results(results)
    output_dir = REPORTS_DIR / f"batch-procurement-sales-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    write_outputs(output_dir, candidates, results, summary)
    print(json.dumps({"output_dir": str(output_dir), **summary}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
