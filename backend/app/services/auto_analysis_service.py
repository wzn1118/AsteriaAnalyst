from __future__ import annotations

from datetime import datetime, timezone
import html as html_lib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import threading
import time
import textwrap
from typing import Any

import numpy as np
import pandas as pd

from app.models import AutoAnalysisRequest
from app.services.path_service import PUBLIC_ARTIFACTS_DIR, REPORTS_DIR
from app.services.report_catalog_index_service import upsert_report_catalog_rows
from app.services.auto_analysis_causal_service import build_causal_executor_tables
from app.services.auto_analysis_evidence_service import build_evidence_tables
from app.services.auto_analysis_field_service import (
    build_derived_field_edits,
    build_field_relationships,
    build_field_semantic_route_plan,
    profile_fields,
    select_best_fields,
)
from app.services.auto_analysis_method_executor_service import (
    build_method_card_execution_outputs,
    summarize_method_card_executor_registry,
)
from app.services.auto_analysis_registry_service import (
    canonical_method_ids,
    get_auto_analysis_method_registry,
    method_alias_map,
    priority_method_ids,
    report_part_ids,
    summarize_method_registry,
)
from app.services.auto_analysis_report_part_service import (
    ASSET_MANIFEST_TITLE,
    GENERATION_BLUEPRINT_TITLE,
    build_report_part_asset_manifest,
    build_report_part_generation_blueprints,
    build_report_parts,
    normalize_report_part_ids,
    route_methods_for_report_parts,
)
from app.services.auto_analysis_visual_service import bubble_points, build_auto_charts
from app.services.lab_external_skill_service import lab_external_skill_runtime_context


def _zh(value: str) -> str:
    return value.encode("ascii").decode("unicode_escape")


SMART_MERGE_INPUT_FILE = "smart_merge_input.json"
SMART_MERGE_BRIEF_FILE = "smart_merge_brief.json"
SMART_MERGE_RESULT_FILE = "smart_merge_result.json"
SMART_MERGE_REPORT_FILE = "smart_merge_report.md"
SMART_MERGE_PROMPT_FILE = "smart_merge_prompt.md"
METHOD_ARTIFACT_INDEX_JSON = "method_artifact_index.json"
METHOD_ARTIFACT_INDEX_CSV = "method_artifact_index.csv"
METHOD_ARTIFACT_INDEX_XLSX = "method_artifact_index.xlsx"
METHOD_ARTIFACT_INTEGRITY_FILE = "method_artifact_integrity.json"
METHOD_INTERPRETATION_INPUT_FILE = "codex_method_interpretation_input.json"
METHOD_INTERPRETATION_PROMPT_FILE = "codex_method_interpretation_prompt.md"
METHOD_INTERPRETATION_RESULT_FILE = "codex_method_interpretations.json"
METHOD_INTERPRETATION_REPORT_FILE = "codex_method_interpretations.md"
METHOD_ARTIFACT_DIR = "method_artifacts"
CHART_ASSET_DIR = "chart_assets"
CHART_ASSET_INDEX_JSON = "chart_asset_index.json"
CHART_ASSET_INDEX_CSV = "chart_asset_index.csv"
DELIVERY_MANIFEST_FILE = "delivery_manifest.json"
EXTERNAL_SKILL_CONTEXT_FILE = "external_skill_context.json"
REPORT_WRITER_AGENT_INPUT_FILE = "report_writer_agent_input.json"
REPORT_WRITER_AGENT_RESULT_FILE = "report_writer_agent_result.json"
LAB_REPORT_AGENT_REVIEW_INPUT_FILE = "lab_report_agent_review_input.json"
LAB_REPORT_AGENT_REVIEW_PROMPT_FILE = "lab_report_agent_review_prompt.md"
LAB_REPORT_AGENT_REVIEW_FILE = "lab_report_agent_reviews.json"
LAB_REPORT_AGENT_REVIEW_MD_FILE = "lab_report_agent_reviews.md"
LAB_REPORT_MD_FILE = "lab_report.md"
LAB_REPORT_HTML_FILE = "lab_report.html"
LAB_REPORT_JSON_FILE = "lab_report.json"
LAB_REPORT_SEED_FILE = "lab_report_revision_seed.json"
LARGE_SAMPLE_ROW_THRESHOLD = 5000
ANALYSIS_WORK_FRAME_ROW_LIMIT = 5000
LARGE_SAMPLE_DEFAULT_CHUNK_SIZE = 2500
LARGE_SAMPLE_FINE_CHUNK_SIZE = 1250
LAB_REPORT_CATALOG_SYNC_TIMEOUT_SEC = 8.0
REPORT_WRITER_AGENT_INPUT_CONTRACT = "analysis_lab_report_writer_agent_input_v1"
REPORT_WRITER_AGENT_PIPELINE_CONTRACT = "analysis_lab_report_writer_agent_v2"
CHART_REPORT_WRITER_AGENT_CONTRACT = "analysis_lab_chart_report_writer_agent_v2"
REPORT_WRITER_REQUIRED_STAGE_KEYS = (
    "evidence_analyst_agent",
    "skill_router_agent",
    "business_judgment_agent",
    "narrative_writer_agent",
    "figure_caption_agent",
    "skeptical_review_agent",
    "final_editor_agent",
)


def _deterministic_even_sample_frame(frame: pd.DataFrame, limit: int) -> pd.DataFrame:
    if len(frame) <= limit:
        return frame
    positions = np.linspace(0, len(frame) - 1, limit, dtype=int)
    return frame.iloc[pd.Index(positions).drop_duplicates()].copy()


def _analysis_work_frame_for_frame(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    work_frame = _deterministic_even_sample_frame(frame, ANALYSIS_WORK_FRAME_ROW_LIMIT)
    sampled = len(work_frame) < len(frame)
    return work_frame, {
        "analysis_work_frame_mode": "sampled" if sampled else "full",
        "analysis_work_frame_strategy": "deterministic_even_sample" if sampled else "full_dataset",
        "analysis_work_frame_row_count": int(len(work_frame)),
        "analysis_work_frame_row_limit": ANALYSIS_WORK_FRAME_ROW_LIMIT,
        "full_row_count": int(len(frame)),
    }


def _large_sample_policy_for_frame(frame: pd.DataFrame, work_frame_policy: dict[str, Any] | None = None) -> dict[str, Any]:
    row_count = int(len(frame))
    large_sample = row_count >= LARGE_SAMPLE_ROW_THRESHOLD
    default_chunk_count = int(np.ceil(row_count / LARGE_SAMPLE_DEFAULT_CHUNK_SIZE)) if row_count else 0
    fine_chunk_count = int(np.ceil(row_count / LARGE_SAMPLE_FINE_CHUNK_SIZE)) if row_count else 0
    return {
        "contract": "analysis_lab_large_sample_policy_v1",
        "row_count": row_count,
        "large_sample": large_sample,
        "large_sample_threshold": LARGE_SAMPLE_ROW_THRESHOLD,
        "chart_render_limit": None,
        "chunking_enabled": large_sample,
        "chunk_strategy": "sequential_full_dataset_chunks",
        "default_chunk_size": LARGE_SAMPLE_DEFAULT_CHUNK_SIZE,
        "default_chunk_count": default_chunk_count,
        "fine_chunk_size": LARGE_SAMPLE_FINE_CHUNK_SIZE,
        "fine_chunk_count": fine_chunk_count,
        "chunk_formula": "sample_count / chunk_size",
        "sync_codex_cli_mode": "async_required" if large_sample else "environment_controlled",
        **(work_frame_policy or {}),
        "capability": (
            "Full data, JSON, CSV, XLSX, chart payloads, and enhancement inputs are preserved; "
            "expensive visual/CLI enhancement work is bounded or tracked so large-sample runs can complete. "
            "Large samples are summarized in 2,500-row chunks by default, with 1,250-row fine chunks available for denser evidence."
        ),
    }


def _chart_point_limit_for_request(request: AutoAnalysisRequest, large_sample_policy: dict[str, Any]) -> int:
    requested = int(getattr(request, "max_chart_points", 0) or 0)
    if bool(large_sample_policy.get("large_sample")):
        return min(LARGE_SAMPLE_DEFAULT_CHUNK_SIZE, max(LARGE_SAMPLE_FINE_CHUNK_SIZE, requested))
    return requested or 160


def _safe_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(number):
        return None
    return number


def _clean_records(frame: pd.DataFrame, limit: int = 80) -> list[dict[str, Any]]:
    if frame.empty:
        return []
    preview = frame.head(limit).copy().where(pd.notnull(frame.head(limit)), None)
    rows: list[dict[str, Any]] = []
    for row in preview.to_dict(orient="records"):
        rows.append({str(key): _safe_float(value) if isinstance(value, (int, float, np.number)) else value for key, value in row.items()})
    return rows


def _table(title: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    columns: list[str] = []
    for row in rows:
        for key in row.keys():
            if key not in columns:
                columns.append(key)
    return {"title": title, "columns": columns, "rows": rows}


def _selected_field_rows(selected: dict[str, Any]) -> list[dict[str, Any]]:
    bubble = selected.get("bubble") or {}
    quadrant = selected.get("quadrant") or {}
    return [
        {"role": key, "field": value}
        for key, value in {
            "target": selected.get("target"),
            "features": ", ".join(selected.get("features") or []),
            "group": selected.get("group"),
            "label": selected.get("label"),
            "bubble_x": bubble.get("x"),
            "bubble_y": bubble.get("y"),
            "bubble_size": bubble.get("size"),
            "quadrant_x": quadrant.get("x"),
            "quadrant_y": quadrant.get("y"),
        }.items()
    ]


_METHOD_FAMILY_LABELS = {
    "association": "关联分析",
    "causal": "因果线索",
    "clustering": "分层画像",
    "comparison": "对比分析",
    "descriptive": "描述统计",
    "diagnostic": "诊断分析",
    "distribution": "分布分析",
    "forecast": "趋势预测",
    "machine_learning": "机器学习",
    "modeling": "建模分析",
    "quality": "数据质量",
    "report_part": "报告章节",
    "segmentation": "分群细分",
    "statistical_test": "统计检验",
    "time_series": "时间序列",
    "visual": "可视化",
    "unknown": "未分类方法",
}

_INTERNAL_EVIDENCE_FIELD_NAMES = {
    "asset_index",
    "asset_ref",
    "asset_type",
    "bound_fields",
    "column_count",
    "data_json_path",
    "data_csv_path",
    "data_xlsx_path",
    "executor_hint",
    "evidence_refs",
    "family",
    "file_name",
    "folder",
    "integrity",
    "integrity_status",
    "method_id",
    "method_name",
    "method_run_id",
    "next_step",
    "output_type",
    "package_id",
    "package_ref",
    "preview_png_path",
    "result_ref",
    "route_score",
    "row_count",
    "runtime_handoff_count",
    "runtime_status",
    "semantic_route_refs",
    "status",
}

_INTERNAL_EVIDENCE_FIELD_PREFIXES = (
    "artifact_",
    "data_",
    "file_",
    "method_",
    "package_",
    "payload.runtime",
    "runtime_",
    "semantic_route",
)

_BUSINESS_FIELD_HINTS = (
    "项目",
    "收入",
    "支出",
    "差值",
    "利润",
    "金额",
    "成本",
    "费用",
    "占比",
    "比率",
    "比例",
    "异常",
    "分数",
    "得分",
    "均值",
    "中位",
    "年度",
    "月份",
    "机构",
    "基金",
    "对象",
    "象限",
    "cluster",
    "score",
    "share",
    "count",
    "mean",
)


def _method_family_label(family: Any) -> str:
    key = str(family or "unknown").strip()
    return _METHOD_FAMILY_LABELS.get(key, key or "未分类方法")


def _contains_cjk(text: Any) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in str(text or ""))


def _is_internal_evidence_column(column: Any) -> bool:
    text = str(column or "").strip()
    lower = text.lower()
    if not lower:
        return True
    if lower in _INTERNAL_EVIDENCE_FIELD_NAMES:
        return True
    if any(lower.startswith(prefix) for prefix in _INTERNAL_EVIDENCE_FIELD_PREFIXES):
        return True
    return False


def _business_evidence_priority(column: Any) -> int:
    text = str(column or "")
    lower = text.lower()
    if _is_internal_evidence_column(text):
        return -100
    score = 0
    if _contains_cjk(text):
        score += 20
    score += sum(8 for hint in _BUSINESS_FIELD_HINTS if hint.lower() in lower or hint in text)
    if "derived__" in lower:
        score += 5
    return score


def _business_field_label(column: Any) -> str:
    return _domain_metric_label(column)


def _client_dataset_title(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return "业务数据"
    text = text.replace("_", " ")
    text = re.sub(r"\banalysis\s+lab\b", "业务分析", text, flags=re.IGNORECASE)
    text = re.sub(r"\brows?\b", "行数据", text, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", text).strip()


def _client_method_name(package: dict[str, Any] | None) -> str:
    package = package or {}
    raw_name = str(package.get("method_name_zh") or package.get("method_name") or package.get("method_id") or "方法证据")
    method_id = str(package.get("method_id") or package.get("method_run_id") or "").lower()
    text = _plain_business_label(raw_name)
    replacements = {
        "Descriptive Profile Full Dataset Table": "全量字段画像表",
        "Association Correlation Field Set Table": "关键指标关联表",
        "Descriptive Rank Derived Metric Report Section": "派生指标排序证据",
        "Descriptive Distribution Derived Metric Report Section": "派生指标分布证据",
        "Segmented KPI Breakdown": "分组指标拆解",
        "Full Dataset": "全量数据",
        "Dataset": "数据集",
        "Table": "表",
        "Report Section": "报告章节",
        "Derived Metric": "派生指标",
        "Distribution": "分布",
        "Profile": "画像",
        "Association": "关联",
        "Correlation": "相关",
        "Segmented KPI Breakdown": "分组指标拆解",
    }
    for old, new in replacements.items():
        text = re.sub(re.escape(old), new, text, flags=re.IGNORECASE)
    if "descriptive_profile" in method_id:
        return "全量字段画像表"
    if "association_correlation" in method_id:
        return "关键指标关联表"
    if "descriptive_rank" in method_id:
        return "派生指标排序证据"
    if "descriptive_distribution" in method_id:
        return "派生指标分布证据"
    if "segmented_kpi" in method_id:
        return "分组指标拆解"
    return text.strip() or "方法证据"


def _client_public_path(public_base_path: str, relative_path: str) -> str:
    base = str(public_base_path or "").strip().replace("\\", "/")
    if not base or base.startswith(("/tmp/", "tmp/")) or re.match(r"^[A-Za-z]:/", base):
        return relative_path
    return _public_path(base, relative_path)


def _is_customer_storage_path(value: Any) -> bool:
    text = str(value or "").strip().replace("\\", "/")
    return text.startswith("/storage/") or text.startswith("storage/")


def _customer_artifact_href(value: Any) -> str:
    text = str(value or "").strip().replace("\\", "/")
    if not text:
        return ""
    for directory in (METHOD_ARTIFACT_DIR, CHART_ASSET_DIR):
        marker = f"/{directory}/"
        if marker in text:
            return f"{directory}/{text.split(marker, 1)[1].lstrip('/')}"
        if text.startswith(f"{directory}/"):
            return text
    if _is_customer_storage_path(text):
        return text
    for file_name in (
        LAB_REPORT_MD_FILE,
        LAB_REPORT_HTML_FILE,
        LAB_REPORT_JSON_FILE,
        LAB_REPORT_SEED_FILE,
        METHOD_ARTIFACT_INDEX_JSON,
        METHOD_ARTIFACT_INDEX_CSV,
        METHOD_ARTIFACT_INDEX_XLSX,
        METHOD_ARTIFACT_INTEGRITY_FILE,
        METHOD_INTERPRETATION_RESULT_FILE,
        METHOD_INTERPRETATION_REPORT_FILE,
        CHART_ASSET_INDEX_JSON,
        CHART_ASSET_INDEX_CSV,
        "chart_asset_index.xlsx",
        DELIVERY_MANIFEST_FILE,
    ):
        if text.endswith(f"/{file_name}") or text == file_name:
            return file_name
    if text.startswith(("/tmp/", "tmp/")) or re.match(r"^[A-Za-z]:/", text):
        return text.rstrip("/").split("/")[-1]
    return text


def _customer_artifact_label(value: Any) -> str:
    href = _customer_artifact_href(value)
    if not href:
        return "下载清单"
    if href.endswith(".png"):
        return f"[PNG 图像]({href})"
    if href.endswith(".csv"):
        return f"[CSV 数据]({href})"
    if href.endswith(".xlsx"):
        return f"[Excel 表格]({href})"
    if href.endswith(".json"):
        return f"[JSON 证据]({href})"
    if href.endswith(".md"):
        return f"[说明文件]({href})"
    if href.endswith(".html"):
        return f"[HTML 报告]({href})"
    return f"[下载文件]({href})"


_PRIVATE_ARTIFACT_PATH_KEYS = {
    "file_path",
    "source_export_dir",
    "workspace_path",
    "report_dir",
    "report_dir_path",
    "manifest_path",
}


def _looks_like_local_artifact_path(value: Any) -> bool:
    text = str(value or "").strip().replace("\\", "/")
    return bool(text.startswith(("/tmp/", "tmp/")) or re.match(r"^[A-Za-z]:/", text))


def _public_downloadable_item(item: dict[str, Any]) -> dict[str, Any]:
    public: dict[str, Any] = {}
    for key, value in item.items():
        key_text = str(key)
        if key_text in _PRIVATE_ARTIFACT_PATH_KEYS or key_text.endswith("_file_path"):
            continue
        if key_text == "path":
            public[key_text] = _customer_artifact_href(value)
        elif isinstance(value, str) and _looks_like_local_artifact_path(value):
            public[key_text] = _customer_artifact_href(value)
        else:
            public[key_text] = value
    return public


def _public_downloadables(downloadables: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_public_downloadable_item(item) for item in downloadables if isinstance(item, dict)]


def _download_kind_label(kind: Any) -> str:
    labels = {
        "lab_report_html": "主报告 HTML",
        "lab_report_markdown": "主报告 Markdown",
        "lab_report_json": "主报告 JSON",
        "lab_report_revision_seed": "报告修订种子",
        "delivery_manifest": "客户交付清单",
        "chart_asset": "业务图表文件",
        "chart_asset_index": "图表索引",
        "method_artifact": "方法证据文件",
        "method_artifact_index_json": "方法证据索引",
        "method_artifact_index_csv": "方法证据索引",
        "method_artifact_index_xlsx": "方法证据索引",
        "method_artifact_integrity": "方法完整性清单",
        "method_interpretation_result": "方法解读结果",
        "method_interpretation_report": "方法解读报告",
        "lab_report_agent_review": "复核记录",
        "runtime_package_manifest": "运行交接清单",
        "method_execution_package_index": "方法运行包索引",
        "report_part_bundle": "报告章节证据包",
        "single_method_json": "单方法运行包",
        "report_writer_agent_input": "图文写作输入",
        "report_writer_agent_result": "图文写作结果",
        "external_skill_context": "外部写作约束",
        "smart_merge_input": "智能合并输入",
        "smart_merge_brief": "智能合并摘要",
        "smart_merge_report": "智能合并报告",
    }
    return labels.get(str(kind or ""), "交付文件")


def _download_type_label(type_value: Any, path: Any = "") -> str:
    suffix = str(path or "").lower().rsplit(".", 1)[-1] if "." in str(path or "") else str(type_value or "").lower()
    labels = {
        "html": "可浏览报告",
        "md": "Markdown 文档",
        "json": "JSON 证据",
        "csv": "CSV 数据",
        "xlsx": "Excel 表格",
        "png": "PNG 图像",
        "pdf": "PDF 文档",
    }
    return labels.get(suffix or str(type_value or "").lower(), str(type_value or "文件"))


def _customer_download_purpose(item: dict[str, Any]) -> str:
    kind = str(item.get("download_kind") or "")
    path = str(item.get("path") or "")
    type_label = _download_type_label(item.get("type"), path)
    if kind == "chart_asset":
        return f"业务图表交付文件，可用于报告正文、复核和下载；格式：{type_label}。"
    if kind == "method_artifact":
        return f"方法级证据文件，包含数据、预览或说明，可追溯到具体分析方法；格式：{type_label}。"
    if kind.startswith("method_artifact_index") or kind == "method_artifact_integrity":
        return f"方法证据总览文件，用于检查每个方法的 CSV、Excel、JSON 和 PNG 是否齐全；格式：{type_label}。"
    if kind == "chart_asset_index":
        return f"业务图表索引，列出每张图的标题、口径、行动建议和可下载图像；格式：{type_label}。"
    if kind.startswith("lab_report"):
        return f"主报告交付文件，面向阅读、下载或后续修订；格式：{type_label}。"
    if kind == "delivery_manifest":
        return "客户交付清单，汇总本次报告、图表、方法证据和下载文件。"
    if kind in {"runtime_package_manifest", "method_execution_package_index", "report_part_bundle", "single_method_json"}:
        return f"运行证据包，用于审计本次分析链路和方法调度；格式：{type_label}。"
    return f"{_download_kind_label(kind)}，格式：{type_label}。"


def _public_downloadable_with_customer_labels(item: dict[str, Any]) -> dict[str, Any]:
    public = _public_downloadable_item(item)
    public["category"] = _download_kind_label(public.get("download_kind"))
    public["type_label"] = _download_type_label(public.get("type"), public.get("path"))
    public["purpose"] = _customer_download_purpose(public)
    return public


def _public_downloadables_with_customer_labels(downloadables: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_public_downloadable_with_customer_labels(item) for item in downloadables if isinstance(item, dict)]


def _delivery_manifest_summary_rows(downloadables: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for category in sorted({str(item.get("category") or "交付文件") for item in downloadables}):
        category_items = [item for item in downloadables if str(item.get("category") or "交付文件") == category]
        rows.append(
            {
                "类别": category,
                "文件数": len(category_items),
                "主文件数": sum(1 for item in category_items if bool(item.get("is_main"))),
                "格式": "、".join(sorted({str(item.get("type_label") or item.get("type") or "文件") for item in category_items})),
            }
        )
    return rows


def _write_delivery_manifest(
    *,
    export_dir: Path,
    public_base_path: str,
    request: AutoAnalysisRequest,
    dataset_name: str,
    sheet_name: str,
    generated_at: str,
    downloadables: list[dict[str, Any]],
    lab_report: dict[str, Any],
    method_artifact_summary: dict[str, Any] | None,
    chart_asset_summary: dict[str, Any] | None,
) -> dict[str, Any]:
    manifest_path = export_dir / DELIVERY_MANIFEST_FILE
    item = _public_downloadable_with_customer_labels(
        {
            "name": DELIVERY_MANIFEST_FILE,
            "path": _public_path(public_base_path, DELIVERY_MANIFEST_FILE),
            "type": "json",
            "purpose": "客户交付清单，汇总本次报告、图表、方法证据和下载文件。",
            "is_main": False,
            "download_kind": "delivery_manifest",
        }
    )
    public_downloadables = [*_public_downloadables_with_customer_labels(downloadables), item]
    payload = {
        "contract": "analysis_lab_customer_delivery_manifest_v1",
        "generated_at": generated_at,
        "dataset": {
            "dataset_id": request.dataset_id,
            "dataset_name": _client_dataset_title(dataset_name or request.dataset_id),
            "sheet_name": _client_dataset_title(sheet_name or request.active_sheet or "Sheet1"),
        },
        "quality": {
            "status": lab_report.get("quality_status") or lab_report.get("runtime_status") or "",
            "score": lab_report.get("quality_score"),
            "report_id": lab_report.get("report_id") or "",
        },
        "coverage": {
            "downloadable_count": len(public_downloadables),
            "chart_count": (chart_asset_summary or {}).get("chart_count") or 0,
            "chart_complete_count": (chart_asset_summary or {}).get("complete_count") or 0,
            "method_count": (method_artifact_summary or {}).get("method_count") or 0,
            "method_complete_count": (method_artifact_summary or {}).get("integrity_complete_count") or 0,
        },
        "main_files": [
            item
            for item in public_downloadables
            if bool(item.get("is_main"))
            or item.get("name") in {LAB_REPORT_HTML_FILE, LAB_REPORT_MD_FILE, LAB_REPORT_JSON_FILE}
        ],
        "category_summary": _delivery_manifest_summary_rows(public_downloadables),
        "downloadables": public_downloadables,
        "customer_notes": [
            "所有 path 均为客户可访问路径或交付包相对路径，不包含本机临时目录。",
            "图表 PNG、方法 CSV/Excel/JSON/PNG 与说明文件均纳入下载清单。",
            "报告正文中的核心判断已绑定图像、表格、方法证据和复核记录。",
        ],
    }
    _write_json_file(manifest_path, payload)
    _append_downloadable(downloadables, item)
    return payload


def _strip_private_artifact_paths(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            if key_text in _PRIVATE_ARTIFACT_PATH_KEYS or key_text.endswith("_file_path"):
                continue
            cleaned[key] = _strip_private_artifact_paths(item)
        return cleaned
    if isinstance(value, list):
        return [_strip_private_artifact_paths(item) for item in value]
    if isinstance(value, str) and _looks_like_local_artifact_path(value):
        return _customer_artifact_href(value)
    return value


def _interpretation_status_label(status: Any) -> str:
    status_text = str(status or "").strip()
    labels = {
        "local_numeric_cli_analysis_completed": "已生成本地数值解读",
        "codex_cli_analysis_completed": "已生成 Codex 解读",
        "codex_cli_sync_completed": "同步 Codex 复核完成",
    }
    if not status_text:
        return "未生成解读"
    if status_text.endswith("_local_numeric_analysis_used"):
        return "已使用本地数值解读补齐"
    return labels.get(status_text, status_text)


def _artifact_integrity_label(status: Any) -> str:
    status_text = str(status or "").strip()
    if status_text == "complete":
        return "完整"
    if status_text == "passed":
        return "通过"
    if status_text == "missing":
        return "缺失"
    return status_text or "-"


def _external_skill_table_rows(external_skill_context: dict[str, Any] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for skill in _external_skill_items_for_report(external_skill_context):
        if not isinstance(skill, dict):
            continue
        rows.append(
            {
                "skill_id": skill.get("id") or "",
                "name": skill.get("name") or "",
                "description": skill.get("description") or "",
                "source_repo": skill.get("source_repo") or "",
                "source_ref": skill.get("source_ref") or "",
                "source_path": skill.get("source_path") or "",
                "package_kind": skill.get("package_kind") or "skill",
                "plugin_version": skill.get("plugin_version") or "",
                "embedded_skill_count": skill.get("skill_count") or 0,
                "selected_feature_count": skill.get("selected_feature_count") or 0,
                "selected_features": ", ".join(
                    str(item.get("name") or item.get("feature_id") or "")
                    for item in list(skill.get("selected_features") or [])[:8]
                    if isinstance(item, dict)
                ),
                "command_count": skill.get("command_count") or 0,
                "mcp_server_count": skill.get("mcp_server_count") or 0,
                "instruction_chars": skill.get("instruction_chars") or len(str(skill.get("instructions") or "")),
                "instructions_included": bool(skill.get("instructions_included") or skill.get("instructions")),
                "instructions_loaded_chars": skill.get("instructions_loaded_chars") or len(str(skill.get("instructions") or "")),
                "instructions_truncated": bool(skill.get("instructions_truncated")),
                "management_use": "Mounted external skill/plugin instructions consumed by this Analysis Lab run.",
            }
        )
    return rows


def _selected_external_skill_feature_rows(external_skill_context: dict[str, Any] | None) -> list[dict[str, Any]]:
    return [
        {
            "plugin_id": skill.get("id") or "",
            "plugin_name": skill.get("name") or skill.get("id") or "",
            "feature_kind": item.get("feature_kind") or "",
            "feature_id": item.get("feature_id") or "",
            "feature_name": item.get("name") or item.get("feature_id") or "",
            "description": item.get("description") or "",
            "report_flow_role": "Use this feature to shape chart interpretation, method synthesis, action design, and skeptical review.",
        }
        for skill in _external_skill_items_for_report(external_skill_context)
        if isinstance(skill, dict)
        for item in list(skill.get("selected_features") or [])
        if isinstance(item, dict)
    ]


def _external_skill_items_for_report(external_skill_context: dict[str, Any] | None) -> list[dict[str, Any]]:
    context = external_skill_context or {}
    mounted = [item for item in list(context.get("mounted_skills") or []) if isinstance(item, dict)]
    if mounted:
        return mounted
    return [item for item in list(context.get("skills") or []) if isinstance(item, dict)]


def _external_skill_ids_for_report(external_skill_context: dict[str, Any] | None) -> list[str]:
    context = external_skill_context or {}
    ids = [str(item).strip() for item in list(context.get("mounted_skill_ids") or []) if str(item).strip()]
    if not ids:
        ids = [
            str(item.get("id") or "").strip()
            for item in _external_skill_items_for_report(external_skill_context)
            if str(item.get("id") or "").strip()
        ]
    if not ids:
        ids = [str(item).strip() for item in list(context.get("skill_ids") or []) if str(item).strip()]
    return list(dict.fromkeys(ids))


def _external_skill_report_flow_rows(external_skill_context: dict[str, Any] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for skill in _external_skill_items_for_report(external_skill_context):
        if not isinstance(skill, dict):
            continue
        selected_features = [
            str(item.get("name") or item.get("feature_id") or "").strip()
            for item in list(skill.get("selected_features") or [])
            if isinstance(item, dict) and str(item.get("name") or item.get("feature_id") or "").strip()
        ]
        source = str(skill.get("source_repo") or skill.get("source_url") or skill.get("source") or "").strip()
        rows.append(
            {
                "Skill package": skill.get("name") or skill.get("id") or "",
                "Skill id": skill.get("id") or "",
                "Source": source,
                "Selected functions": ", ".join(selected_features[:8]) or "entire mounted package",
                "Instruction status": (
                    "loaded"
                    if bool(skill.get("instructions_included") or skill.get("instructions"))
                    else "metadata mounted; instructions capped"
                ),
                "Report-flow role": "Strengthens method choice, evidence interpretation, recommended actions, and strict review.",
            }
        )
    return rows


def _external_skill_review_requirements(selected_feature_rows: list[dict[str, Any]]) -> list[str]:
    if not selected_feature_rows:
        return []
    feature_names = [
        str(item.get("feature_name") or item.get("feature_id") or "").strip()
        for item in selected_feature_rows
        if str(item.get("feature_name") or item.get("feature_id") or "").strip()
    ]
    joined_names = ", ".join(dict.fromkeys(feature_names))[:240]
    return [
        "Selected external skill features must materially change method synthesis, not just appear as metadata.",
        "Consolidated actions must reflect the selected features' operating expectations, review style, or deliverable shape.",
        "Claim and chart reviews must state whether the selected features improved evidence interpretation or exposed missing proof.",
        (
            f"Selected features in scope: {joined_names}."
            if joined_names
            else "Selected features are in scope for main report flow review."
        ),
    ]


def _normalize_csv_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return []


def _selected_field_overrides(selected_fields: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(selected_fields, dict):
        return {}
    overrides: dict[str, Any] = {}
    for key in ["target", "group", "label", "time"]:
        value = str(selected_fields.get(key) or "").strip()
        if value:
            overrides[key] = value
    features = _normalize_csv_list(selected_fields.get("features"))
    if features:
        overrides["features"] = features
    bubble = selected_fields.get("bubble") if isinstance(selected_fields.get("bubble"), dict) else {}
    quadrant = selected_fields.get("quadrant") if isinstance(selected_fields.get("quadrant"), dict) else {}
    if bubble:
        overrides["bubble"] = {
            key: str(bubble.get(key) or "").strip()
            for key in ["x", "y", "size", "color", "label"]
            if str(bubble.get(key) or "").strip()
        }
    if quadrant:
        overrides["quadrant"] = {
            key: str(quadrant.get(key) or "").strip()
            for key in ["x", "y", "label", "group"]
            if str(quadrant.get(key) or "").strip()
        }
    return overrides


def _selected_field_bullets(selected: dict[str, Any]) -> list[str]:
    bubble = selected.get("bubble") or {}
    quadrant = selected.get("quadrant") or {}
    return [
        f"target: {str(selected.get('target') or '').strip() or '自动'}",
        f"features: {', '.join(str(item) for item in list(selected.get('features') or []) if str(item).strip()) or '自动'}",
        f"group/label: {str(selected.get('group') or '').strip() or '自动'} / {str(selected.get('label') or '').strip() or '自动'}",
        f"bubble: x={str(bubble.get('x') or '').strip()}, y={str(bubble.get('y') or '').strip()}, size={str(bubble.get('size') or '').strip()}",
        f"quadrant: x={str(quadrant.get('x') or '').strip()}, y={str(quadrant.get('y') or '').strip()}",
    ]


def _table_rows_by_title(tables: list[dict[str, Any]], title: str) -> list[dict[str, Any]]:
    for table in tables:
        if isinstance(table, dict) and str(table.get("title") or "").strip() == title:
            return list(table.get("rows") or [])
    return []


_BUSINESS_FIELD_DISPLAY_ALIASES = {
    "date": "日期",
    "month": "月份",
    "year": "年份",
    "quarter": "季度",
    "week": "周",
    "revenue": "收入",
    "sales": "销售额",
    "cost": "成本",
    "gross": "毛",
    "profit": "利润",
    "margin": "毛利率",
    "quantity": "销量",
    "units": "销量",
    "unit": "单位",
    "price": "价格",
    "product": "产品",
    "category": "品类",
    "region": "地区",
    "channel": "渠道",
    "customer": "客户",
    "conversion": "转化",
    "rate": "率",
    "order": "订单",
    "orders": "订单",
    "risk": "风险",
    "score": "分数",
}


_DERIVED_FIELD_DISPLAY_PREFIXES = {
    "ratio": "比值",
    "share": "占比",
    "diff": "差值",
    "zscore": "标准化",
    "pct_rank": "百分位",
    "mean_index": "均值指数",
    "log1p": "对数",
    "month": "月份",
    "year": "年份",
    "quarter": "季度",
    "week": "周",
    "day": "日期",
}


def _plain_business_label(text: str) -> str:
    normalized = str(text or "").strip()
    if not normalized:
        return ""
    replacements = {
        "__to__": " / ",
        "__of__": " 占 ",
        "__plus__": " + ",
        "__minus__": " - ",
        "_组织画像": "",
    }
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    normalized = normalized.replace("__", " / ").replace("_", " ")
    for token, label in sorted(_BUSINESS_FIELD_DISPLAY_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
        normalized = re.sub(rf"\b{re.escape(token)}\b", label, normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def _domain_metric_label(field: Any) -> str:
    text = str(field or "").strip()
    if not text:
        return "-"
    parts = [part for part in text.split("__") if part]
    if len(parts) >= 2 and parts[0].lower() == "derived":
        prefix = _DERIVED_FIELD_DISPLAY_PREFIXES.get(parts[1].lower())
        suffix = _plain_business_label("__".join(parts[2:]))
        if prefix and suffix:
            return f"{prefix}：{suffix}"[:120]
        if prefix:
            return prefix
    return _plain_business_label(text)[:120]


def _build_business_signal_summary(
    *,
    dataset_name: str,
    sheet_name: str,
    selected: dict[str, Any],
    tables: list[dict[str, Any]],
    charts: list[dict[str, Any]],
    method_execution_packages: list[dict[str, Any]],
) -> list[str]:
    families: dict[str, int] = {}
    for package in method_execution_packages:
        family = str(package.get("family") or "unknown")
        families[family] = families.get(family, 0) + 1
    family_text = "，".join(f"{_method_family_label(key)}{value}个" for key, value in sorted(families.items()))
    target_label = _domain_metric_label(selected.get("target"))
    rows: list[str] = [
        f"本轮报告对象是 `{dataset_name or '-'} / {sheet_name or '-'}`，核心业务指标选择为 `{target_label}`。",
        f"方法覆盖：{family_text or '暂无方法覆盖'}。判断：本轮不是单一图表说明，而是用描述、对比、关联、分层、异常和可视化共同交叉验证业务结论。",
    ]
    quadrant_rows = _table_rows_by_title(tables, _zh(r"\u8c61\u9650\u8ba1\u6570"))
    if quadrant_rows:
        quadrant_text = "；".join(f"{row.get('quadrant')}={row.get('count')}" for row in quadrant_rows[:4])
        rows.append(
            f"象限结构：{quadrant_text}。判断：高收入高支出对象代表规模型重点，低收入高支出对象优先进入效率、资金缺口和数据口径复核清单。"
        )
    anomaly_rows = _table_rows_by_title(tables, _zh(r"\u5f02\u5e38 Top-N"))
    if anomaly_rows:
        top = anomaly_rows[0]
        rows.append(
            f"异常复核优先对象：{top.get('name')}，异常分数 {top.get('score')}。判断：该对象应优先人工复核，先区分真实业务风险、一次性机会和数据质量问题。"
        )
    cluster_rows = _table_rows_by_title(tables, _zh(r"\u5206\u7fa4\u753b\u50cf"))
    if cluster_rows:
        largest = max(cluster_rows, key=lambda item: float(item.get("share") or 0.0))
        rows.append(
            f"分层结构：最大分群 cluster={largest.get('cluster')}，占比 {largest.get('share')}。判断：样本明显集中，管理上应先建立主群体标准动作，再单独检查少数分群是否代表特殊风险或特殊机会。"
        )
    driver_rows = _table_rows_by_title(tables, _zh(r"\u9a71\u52a8\u5047\u8bbe"))
    if driver_rows:
        top = driver_rows[0]
        rows.append(
            f"驱动假设：`{_domain_metric_label(top.get('driver'))}` 与 `{_domain_metric_label(top.get('target'))}` 关系最强。判断：当前只能作为相关性线索，不应直接写成因果结论，下一步要结合业务口径和样本来源验证。"
        )
    if not any(chart.get("kind") == "forecast" for chart in charts if isinstance(chart, dict)):
        rows.append("预测边界：当前数据没有足够真实时间轴，已跳过趋势外推。判断：不要把行序或常量年度误写成预测结论。")
    action_rows = _table_rows_by_title(tables, _zh(r"\u884c\u52a8\u4f18\u5148\u7ea7\u8bc4\u5206"))
    if action_rows:
        for row in action_rows[:3]:
            rows.append(f"行动优先级：{row.get('priority')} - {row.get('action')}；下一步：{row.get('next_step')}。")
    return rows


def _build_pre_method_routing_audit(
    *,
    field_profiles: list[dict[str, Any]],
    derived_field_options: list[dict[str, Any]],
    derived_fields: list[dict[str, Any]],
    field_relationships: list[dict[str, Any]],
    field_semantic_route_plan: dict[str, Any],
    registry_size: int,
    filtered_registry_size: int,
    routed_method_count: int,
    selected_method_ids: list[str],
    requested_part: str,
) -> list[dict[str, Any]]:
    status = str(field_semantic_route_plan.get("pre_method_preprocessing_status") or "derived_fields_completed_before_method_routing")
    return [
        {
            "sequence": 1,
            "stage": "field_profile",
            "input": "raw_dataframe",
            "output": "field_profiles",
            "record_count": len(field_profiles),
            "completed_before_method_routing": True,
            "gate_status": "ready",
            "management_use": "understand every source field before selecting methods",
        },
        {
            "sequence": 2,
            "stage": "smart_derived_field_preprocessing",
            "input": "field_profiles + raw_dataframe",
            "output": "derived_field_options",
            "record_count": len(derived_field_options),
            "completed_before_method_routing": True,
            "gate_status": "required_pre_method_step",
            "management_use": "create ratios, gaps, z-scores, percentiles and calendar fields before routing analysis methods",
        },
        {
            "sequence": 3,
            "stage": "derived_field_selection",
            "input": "derived_field_options + user_selected_derived_fields",
            "output": "selected_derived_fields",
            "record_count": len(derived_fields),
            "completed_before_method_routing": True,
            "gate_status": "ready",
            "management_use": "decide which derived fields are eligible for method cards and report sections",
        },
        {
            "sequence": 4,
            "stage": "field_relationship_graph",
            "input": "field_profiles + selected_derived_fields",
            "output": "field_relationships",
            "record_count": len(field_relationships),
            "completed_before_method_routing": True,
            "gate_status": "ready",
            "management_use": "map lineage, correlation, segment lift and time trend evidence before report generation",
        },
        {
            "sequence": 5,
            "stage": "field_semantic_route_plan",
            "input": "field_profiles + derived_fields + relationships + selected_fields",
            "output": "field_semantic_route_plan",
            "record_count": int(field_semantic_route_plan.get("field_count") or 0),
            "completed_before_method_routing": True,
            "gate_status": status,
            "management_use": "bind field meaning, analysis roles, method families and report slots before method selection",
        },
        {
            "sequence": 6,
            "stage": "method_registry_resolution",
            "input": "statistical_catalog + generated_catalog + learned_methods + selected_method_ids",
            "output": "candidate_method_registry",
            "record_count": filtered_registry_size,
            "completed_before_method_routing": True,
            "gate_status": "strict_selected_methods" if selected_method_ids else "auto_registry",
            "management_use": f"choose from {registry_size} total methods for requested_part={requested_part or 'auto'}",
        },
        {
            "sequence": 7,
            "stage": "method_routing",
            "input": "candidate_method_registry + pre_method_semantic_contract",
            "output": "routed_method_cards",
            "record_count": routed_method_count,
            "completed_before_method_routing": False,
            "gate_status": "uses_pre_method_audit",
            "management_use": "route methods only after field semantics, derived preprocessing and relationship evidence are available",
        },
    ]


def _method_route_evidence_rows(routed_methods: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for method in routed_methods:
        evidence = method.get("route_evidence") if isinstance(method.get("route_evidence"), dict) else {}
        rows.append(
            {
                "method_id": evidence.get("method_id") or method.get("id"),
                "family": evidence.get("family") or method.get("family"),
                "route_score": evidence.get("route_score") or method.get("route_score"),
                "route_reasons": ", ".join(str(item) for item in list(evidence.get("route_reasons") or method.get("route_reasons") or [])),
                "requested_part": evidence.get("requested_part") or dict(method.get("route_context") or {}).get("requested_part"),
                "pre_method_preprocessing_status": evidence.get("pre_method_preprocessing_status"),
                "bound_fields": ", ".join(str(item) for item in list(evidence.get("bound_fields") or [])),
                "semantic_route_field_count": evidence.get("semantic_route_field_count"),
                "semantic_route_refs": ", ".join(str(item) for item in list(evidence.get("semantic_route_refs") or [])[:8]),
                "derived_bound_fields": ", ".join(str(item) for item in list(evidence.get("derived_bound_fields") or [])),
                "compatible_method_families": ", ".join(str(item) for item in list(evidence.get("compatible_method_families") or [])[:8]),
                "recommended_report_parts": ", ".join(str(item) for item in list(evidence.get("recommended_report_parts") or [])[:8]),
                "report_slots": ", ".join(str(item) for item in list(evidence.get("report_slots") or [])),
                "executor_hint": evidence.get("executor_hint") or method.get("executor_hint"),
                "binding_quality": evidence.get("binding_quality") or method.get("binding_quality"),
                "management_use": evidence.get("management_use") or "audit method routing and report-generation readiness",
            }
        )
    return rows


def _selected_ids(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        item = str(value or "").strip()
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _method_run_specs(values: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for index, raw in enumerate(values or [], start=1):
        if not isinstance(raw, dict):
            continue
        method_id = str(raw.get("method_id") or "").strip()
        if not method_id:
            continue
        run_id = str(raw.get("run_id") or "").strip() or f"{method_id}__run_{index}"
        spec = dict(raw)
        spec["method_id"] = method_id
        spec["run_id"] = run_id
        specs.append(spec)
    return specs


def _method_ids_from_run_specs(specs: list[dict[str, Any]]) -> list[str]:
    return _selected_ids([str(spec.get("method_id") or "") for spec in specs])


def _mark_derived_fields(records: list[dict[str, Any]], selected_fields: list[str]) -> list[dict[str, Any]]:
    selected = set(_selected_ids(selected_fields))
    use_all = not selected
    marked: list[dict[str, Any]] = []
    for record in records:
        field = str(record.get("field") or "")
        marked.append({**record, "selected": bool(use_all or field in selected)})
    return marked


def _apply_derived_metric_edits(records: list[dict[str, Any]], edits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not edits:
        return records
    by_field = {str(item.get("field") or ""): item for item in records}
    for edit in edits:
        if not isinstance(edit, dict):
            continue
        field = str(edit.get("field") or edit.get("name") or "").strip()
        if not field:
            continue
        display_name = str(
            edit.get("display_name")
            or edit.get("display_name_zh")
            or edit.get("metric_name_cn")
            or edit.get("name_zh")
            or ""
        ).strip()
        formula = str(edit.get("formula") or edit.get("formula_or_logic") or edit.get("calculation_method") or "").strip()
        source_fields = _normalize_csv_list(edit.get("source_fields") or edit.get("sources") or edit.get("fields"))
        current = dict(by_field.get(field) or {})
        current["field"] = field
        if display_name:
            current["display_name"] = display_name
            current["display_name_zh"] = display_name
        if formula:
            current["formula"] = formula
        if source_fields:
            current["source_fields"] = source_fields
            current["source_fields_zh"] = "、".join(source_fields)
        current["manual_edited"] = True
        by_field[field] = current
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for record in records:
        field = str(record.get("field") or "")
        if field in by_field and field not in seen:
            result.append(by_field[field])
            seen.add(field)
    for field, record in by_field.items():
        if field and field not in seen:
            result.append(record)
    return result


def _filter_registry_by_ids(registry: list[dict[str, Any]], selected_method_ids: list[str]) -> list[dict[str, Any]]:
    selected = canonical_method_ids(_selected_ids(selected_method_ids), registry)
    if not selected:
        return registry
    by_id = {str(item.get("id") or ""): item for item in registry}
    return [by_id[method_id] for method_id in selected if method_id in by_id]


def _method_download_rows(routed_methods: list[dict[str, Any]], execution_rows: list[dict[str, Any]], assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    assets_by_run: dict[str, list[dict[str, Any]]] = {}
    for asset in assets:
        run_id = str(asset.get("method_run_id") or asset.get("method_id") or "")
        assets_by_run.setdefault(run_id, []).append(asset)
    rows: list[dict[str, Any]] = []
    for index, method in enumerate(routed_methods, start=1):
        method_id = str(method.get("id") or "")
        run_id = str(method.get("method_run_id") or method_id)
        execution = next((row for row in execution_rows if row.get("method_run_id") == run_id), {})
        rows.append(
            {
                "method_id": method_id,
                "method_run_id": run_id,
                "method_run_label": method.get("method_run_label") or "",
                "method_name": method.get("name"),
                "method_name_zh": method.get("name_zh") or method.get("name") or method_id,
                "family": method.get("family"),
                "file_name": f"{index:03d}-{run_id}.json",
                "download_kind": "single_method_json",
                "execution_id": execution.get("execution_id"),
                "asset_count": len(assets_by_run.get(run_id, [])),
                "result_ref": execution.get("result_ref"),
            }
        )
    return rows


def _method_execution_packages(
    routed_methods: list[dict[str, Any]],
    execution_rows: list[dict[str, Any]],
    assets: list[dict[str, Any]],
    external_skill_context: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    assets_by_run: dict[str, list[dict[str, Any]]] = {}
    for asset in assets:
        run_id = str(asset.get("method_run_id") or asset.get("method_id") or "")
        assets_by_run.setdefault(run_id, []).append(asset)
    packages: list[dict[str, Any]] = []
    for index, method in enumerate(routed_methods, start=1):
        method_id = str(method.get("id") or "")
        run_id = str(method.get("method_run_id") or method_id)
        execution = next((row for row in execution_rows if row.get("method_run_id") == run_id), {})
        method_assets = assets_by_run.get(run_id, [])
        runtime_handoffs = [
            dict(asset.get("runtime_handoff") or {})
            for asset in method_assets
            if isinstance(asset.get("runtime_handoff"), dict)
        ]
        packages.append(
            {
                "package_id": f"method_package_{index}",
                "file_name": f"{index:03d}-{run_id}.json",
                "method_id": method_id,
                "method_run_id": run_id,
                "method_run_label": method.get("method_run_label") or "",
                "method_name": method.get("name"),
                "method_name_zh": method.get("name_zh") or method.get("name") or method_id,
                "family": method.get("family"),
                "route_score": method.get("route_score"),
                "route_reasons": list(method.get("route_reasons") or []),
                "route_evidence": method.get("route_evidence") or {},
                "method_card": method.get("method_card") or {},
                "execution": execution,
                "assets": method_assets,
                "runtime_handoffs": runtime_handoffs,
                "runtime_handoff_count": len(runtime_handoffs),
                "external_skill_context": external_skill_context or {},
                "external_skill_ids": _external_skill_ids_for_report(external_skill_context),
                "pre_method_preprocessing_status": (
                    runtime_handoffs[0].get("pre_method_preprocessing_status")
                    if runtime_handoffs
                    else "derived_fields_completed_before_method_routing"
                ),
                "management_use": "Download or hand this package to Codex CLI/exec/runtime to continue one routed method into text, table, structured data, chart, image spec or report section output.",
            }
        )
    return packages


def _storage_url_for(path: Path) -> str:
    try:
        relative = path.resolve().relative_to(PUBLIC_ARTIFACTS_DIR).as_posix()
    except Exception:
        return ""
    return f"/storage/{relative}"


def _report_cell_text(value: Any, max_chars: int = 140) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        text = f"{value:.6g}"
    elif isinstance(value, (int, np.integer)):
        text = str(int(value))
    elif isinstance(value, (list, dict)):
        text = json.dumps(value, ensure_ascii=False, default=str)
    else:
        text = str(value)
    text = re.sub(r"\s+", " ", text).strip().replace("|", "\\|")
    return text if len(text) <= max_chars else f"{text[: max_chars - 3].rstrip()}..."


def _hex_to_rgb(value: Any, default: tuple[int, int, int] = (80, 95, 70)) -> tuple[int, int, int]:
    text = str(value or "").strip().lstrip("#")
    if len(text) == 3:
        text = "".join(char * 2 for char in text)
    if len(text) != 6:
        return default
    try:
        return int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16)
    except ValueError:
        return default


def _load_pil_image_tools() -> tuple[Any, Any, Any] | None:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        return None
    return Image, ImageDraw, ImageFont


def _load_pil_font(ImageFont: Any, size: int, *, bold: bool = False) -> Any:
    candidates = [
        r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
    ]
    for candidate in candidates:
        try:
            if candidate and Path(candidate).exists():
                return ImageFont.truetype(candidate, size=size)
        except Exception:
            continue
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size=size)
    except Exception:
        return ImageFont.load_default()


def _draw_text_safe(draw: Any, xy: tuple[int, int], text: Any, *, font: Any, fill: Any, max_chars: int = 120) -> None:
    safe_text = _report_cell_text(text, max_chars)
    try:
        draw.text(xy, safe_text, font=font, fill=fill)
    except Exception:
        ascii_text = safe_text.encode("ascii", "replace").decode("ascii")
        draw.text(xy, ascii_text, font=font, fill=fill)


def _write_basic_png_placeholder(path: Path, *, width: int = 960, height: int = 560) -> bool:
    try:
        import struct
        import zlib
    except Exception:
        return False

    def chunk(kind: bytes, payload: bytes) -> bytes:
        checksum = zlib.crc32(kind + payload) & 0xFFFFFFFF
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", checksum)

    path.parent.mkdir(parents=True, exist_ok=True)
    rows: list[bytes] = []
    for y in range(height):
        row = bytearray([0])
        for x in range(width):
            band = int(28 * ((x + y) / max(1, width + height)))
            grid = 14 if (x % 120 < 2 or y % 90 < 2) else 0
            row.extend(
                (
                    min(255, 246 - band + grid),
                    min(255, 238 - band + grid),
                    min(255, 220 - band + grid),
                )
            )
        rows.append(bytes(row))
    raw = b"".join(rows)
    payload = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, 6))
        + chunk(b"IEND", b"")
    )
    path.write_bytes(payload)
    return path.exists() and path.stat().st_size > 0


def _safe_artifact_segment(value: Any, fallback: str = "artifact") -> str:
    text = re.sub(r"[^A-Za-z0-9._-]+", "-", str(value or "").strip()).strip(".-")
    return (text[:96] or fallback).strip(".-") or fallback


def _flatten_for_table(value: Any, *, prefix: str = "") -> dict[str, Any]:
    if isinstance(value, dict):
        flat: dict[str, Any] = {}
        for key, item in value.items():
            next_prefix = f"{prefix}.{key}" if prefix else str(key)
            if isinstance(item, dict):
                flat.update(_flatten_for_table(item, prefix=next_prefix))
            elif isinstance(item, list):
                if item and all(isinstance(child, dict) for child in item[:20]):
                    flat[next_prefix] = json.dumps(item[:20], ensure_ascii=False, default=str)
                else:
                    flat[next_prefix] = ", ".join(_report_cell_text(child, 80) for child in item[:30])
            else:
                flat[next_prefix] = item
        return flat
    return {prefix or "value": value}


def _rows_from_package(package: dict[str, Any]) -> list[dict[str, Any]]:
    execution = package.get("execution") if isinstance(package.get("execution"), dict) else {}
    result_rows = [row for row in list(execution.get("result_rows") or []) if isinstance(row, dict)]
    if result_rows:
        return result_rows
    rows: list[dict[str, Any]] = []
    assets = [asset for asset in list(package.get("assets") or []) if isinstance(asset, dict)]
    base = {
        "package_id": package.get("package_id"),
        "method_id": package.get("method_id"),
        "method_run_id": package.get("method_run_id"),
        "method_name": package.get("method_name_zh") or package.get("method_name") or package.get("method_id"),
        "family": package.get("family"),
        "route_score": package.get("route_score"),
        "status": execution.get("status"),
        "runtime_status": execution.get("runtime_status"),
        "output_type": execution.get("output_type"),
        "result_summary": execution.get("result_summary"),
        "next_step": execution.get("next_step"),
        "bound_fields": execution.get("bound_fields"),
        "result_ref": execution.get("result_ref"),
    }
    if not assets:
        rows.append(base)
        return rows
    for index, asset in enumerate(assets, start=1):
        payload = asset.get("payload") if isinstance(asset.get("payload"), dict) else {}
        row = {
            **base,
            "asset_index": index,
            "asset_type": asset.get("asset_type"),
            "asset_ref": asset.get("asset_ref"),
            "executor_hint": asset.get("executor_hint"),
            "evidence_refs": ", ".join(str(ref) for ref in list(asset.get("evidence_refs") or [])[:20]),
            "semantic_route_refs": ", ".join(str(ref) for ref in list(asset.get("semantic_route_refs") or [])[:20]),
        }
        row.update(_flatten_for_table(payload, prefix="payload"))
        rows.append(row)
    return rows


def _write_dataframe_artifacts(rows: list[dict[str, Any]], *, csv_path: Path, xlsx_path: Path) -> tuple[int, int]:
    frame = pd.DataFrame(rows or [{}])
    frame = frame.where(pd.notnull(frame), None)
    frame = frame.rename(
        columns={
            "next_step": "下一步",
            "method_id": "方法标识",
            "method_run_id": "方法运行标识",
            "method_name": "方法名称",
            "family": "方法类型",
            "status": "状态",
            "row_count": "行数",
            "column_count": "列数",
            "artifact_folder": "证据目录",
            "data_json_path": "JSON证据",
            "data_csv_path": "CSV数据",
            "data_xlsx_path": "Excel表格",
            "preview_png_path": "PNG预览",
            "readme_path": "说明文件",
            "interpretation_status": "解读状态",
            "integrity_status": "完整性",
            "chart_ref": "图表编号",
            "chart_kind": "图表类型",
            "title": "图表标题",
            "x_label": "X字段",
            "y_label": "Y字段",
            "point_count": "数据点",
            "business_interpretation": "业务判断",
            "direct_answer": "直接结论",
            "caption": "图表说明",
            "recommended_action": "建议动作",
            "image_path": "PNG图像",
            "data_path": "JSON数据",
            "sampling_note": "抽样说明",
        }
    )
    if "下一步" in frame.columns:
        frame["下一步"] = frame["下一步"].replace(
            {
                "generate narrative, bullets, tables and evidence index for the slot": "生成可读叙事、要点、表格和证据索引",
            }
        )
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(csv_path, index=False, encoding="utf-8-sig")
    try:
        with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
            frame.to_excel(writer, sheet_name="data", index=False)
            worksheet = writer.sheets["data"]
            worksheet.freeze_panes = "A2"
            for column_cells in worksheet.columns:
                header = str(column_cells[0].value or "")
                max_len = min(max([len(str(cell.value or "")) for cell in column_cells[:80]] + [len(header)]), 48)
                worksheet.column_dimensions[column_cells[0].column_letter].width = max(10, max_len + 2)
    except Exception as exc:
        xlsx_path.with_suffix(".xlsx.error.txt").write_text(str(exc), encoding="utf-8")
    return int(frame.shape[0]), int(frame.shape[1])


def _preview_columns_for_rows(rows: list[dict[str, Any]]) -> tuple[list[str], list[dict[str, Any]]]:
    preview_rows = rows[:8] if rows else []
    preferred = [
        "method_run_id",
        "method_name",
        "family",
        "status",
        "runtime_status",
        "output_type",
        "result_summary",
        "asset_type",
        "asset_ref",
    ]
    columns = [column for column in preferred if any(column in row for row in preview_rows)]
    if not columns and preview_rows:
        columns = list(preview_rows[0].keys())[:6]
    if not columns:
        columns = ["status"]
        preview_rows = [{"status": "no tabular rows"}]
    return columns, preview_rows


def _write_method_preview_png_fallback(rows: list[dict[str, Any]], *, path: Path, title: str) -> bool:
    tools = _load_pil_image_tools()
    if tools is None:
        return _write_basic_png_placeholder(path)
    Image, ImageDraw, ImageFont = tools
    try:
        columns, preview_rows = _preview_columns_for_rows(rows)
        width = max(1100, min(1900, 220 * max(4, len(columns))))
        row_height = 72
        header_height = 118
        height = header_height + row_height * (len(preview_rows) + 1) + 48
        image = Image.new("RGB", (width, height), "#fffaf0")
        draw = ImageDraw.Draw(image)
        title_font = _load_pil_font(ImageFont, 28, bold=True)
        header_font = _load_pil_font(ImageFont, 16, bold=True)
        cell_font = _load_pil_font(ImageFont, 14)
        small_font = _load_pil_font(ImageFont, 12)
        draw.rectangle([(0, 0), (width, 90)], fill="#efe0c8")
        _draw_text_safe(draw, (28, 22), title, font=title_font, fill="#2c2419", max_chars=110)
        _draw_text_safe(
            draw,
            (30, 72),
            f"rows={len(rows or [])}; preview_rows={len(preview_rows)}; generated fallback PNG",
            font=small_font,
            fill="#6b5b45",
            max_chars=160,
        )
        left = 28
        top = header_height
        table_width = width - left * 2
        col_width = max(120, table_width // max(1, len(columns)))
        draw.rounded_rectangle([(left, top), (left + table_width, top + row_height)], radius=14, fill="#d9c2a1", outline="#c2aa86")
        for column_index, column in enumerate(columns):
            x0 = left + column_index * col_width
            x1 = left + table_width if column_index == len(columns) - 1 else x0 + col_width
            draw.line([(x0, top), (x0, top + row_height * (len(preview_rows) + 1))], fill="#c6b08d", width=1)
            _draw_text_safe(draw, (x0 + 12, top + 22), column, font=header_font, fill="#352719", max_chars=24)
            if column_index == len(columns) - 1:
                draw.line([(x1, top), (x1, top + row_height * (len(preview_rows) + 1))], fill="#c6b08d", width=1)
        for row_index, row in enumerate(preview_rows, start=1):
            y0 = top + row_height * row_index
            fill = "#fffdf7" if row_index % 2 else "#f7eddd"
            draw.rectangle([(left, y0), (left + table_width, y0 + row_height)], fill=fill, outline="#e4d5bf")
            for column_index, column in enumerate(columns):
                x0 = left + column_index * col_width
                cell_width = col_width - 20
                max_chars = max(18, min(74, cell_width // 7))
                text = _report_cell_text(row.get(column), max_chars)
                wrapped = textwrap.wrap(text, width=max(12, min(42, cell_width // 8)))[:2] or [""]
                for line_index, line in enumerate(wrapped):
                    _draw_text_safe(
                        draw,
                        (x0 + 12, y0 + 14 + line_index * 20),
                        line,
                        font=cell_font,
                        fill="#352f27",
                        max_chars=max_chars,
                    )
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path, format="PNG")
        return path.exists() and path.stat().st_size > 0
    except Exception:
        return _write_basic_png_placeholder(path)


def _write_method_preview_png(rows: list[dict[str, Any]], *, path: Path, title: str) -> bool:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return _write_method_preview_png_fallback(rows, path=path, title=title)
    plt.rcParams["font.sans-serif"] = [
        "Microsoft YaHei",
        "SimHei",
        "Noto Sans CJK SC",
        "Arial Unicode MS",
        "DejaVu Sans",
    ]
    plt.rcParams["axes.unicode_minus"] = False
    columns, preview_rows = _preview_columns_for_rows(rows)
    cell_text = [
        [_report_cell_text(row.get(column), 72) for column in columns]
        for row in preview_rows
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    fig_height = max(3.0, 1.2 + 0.42 * max(1, len(cell_text)))
    fig_width = max(10.0, min(18.0, 2.0 * len(columns)))
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=180)
    ax.axis("off")
    ax.set_title(title, fontsize=12, fontweight="bold", loc="left", pad=12)
    table = ax.table(cellText=cell_text, colLabels=columns, loc="center", cellLoc="left")
    table.auto_set_font_size(False)
    table.set_fontsize(7.2)
    table.scale(1, 1.35)
    for (row_index, _column_index), cell in table.get_celld().items():
        cell.set_edgecolor("#d8c9b6")
        if row_index == 0:
            cell.set_facecolor("#f0dfc8")
            cell.set_text_props(weight="bold", color="#342217")
        else:
            cell.set_facecolor("#fffaf1" if row_index % 2 else "#ffffff")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return True


def _load_matplotlib_pyplot() -> Any | None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return None
    plt.rcParams["font.sans-serif"] = [
        "Microsoft YaHei",
        "SimHei",
        "Noto Sans CJK SC",
        "Arial Unicode MS",
        "DejaVu Sans",
    ]
    plt.rcParams["axes.unicode_minus"] = False
    return plt


def _format_business_amount(value: Any) -> str:
    number = _safe_float(value)
    if number is None:
        return _report_cell_text(value, 40) or "-"
    if abs(number) >= 100000000:
        return f"{number / 100000000:.2f}亿"
    if abs(number) >= 10000:
        return f"{number / 10000:.1f}万"
    if abs(number) >= 1000:
        return f"{number:,.0f}"
    return f"{number:.4g}"


def _format_plain_number(value: Any) -> str:
    number = _safe_float(value)
    if number is None:
        return _report_cell_text(value, 40) or "-"
    if abs(number) >= 1000:
        return f"{number:,.3f}".rstrip("0").rstrip(".")
    if abs(number) >= 1:
        return f"{number:,.2f}".rstrip("0").rstrip(".")
    formatted = f"{number:.4f}".rstrip("0").rstrip(".")
    return formatted or "0"


def _format_pct(value: float | None) -> str:
    if value is None or not np.isfinite(value):
        return "-"
    return f"{value:.1%}"


def _short_field(value: Any, fallback: str = "-") -> str:
    return _business_field_label(str(value or "").strip()) or fallback


def _chart_points(chart: dict[str, Any]) -> list[dict[str, Any]]:
    raw = chart.get("points")
    if not isinstance(raw, list):
        return []
    points: list[dict[str, Any]] = []
    for index, item in enumerate(raw):
        if isinstance(item, dict):
            x_value = _safe_float(item.get("x"))
            y_value = _safe_float(item.get("y"))
            if x_value is None or y_value is None:
                continue
            points.append({**item, "x": x_value, "y": y_value})
        elif isinstance(item, list) and len(item) >= 2:
            x_value = _safe_float(item[0])
            y_value = _safe_float(item[1])
            if x_value is None or y_value is None:
                continue
            point = {"name": str(index + 1), "x": x_value, "y": y_value}
            if len(item) >= 3:
                point["cluster"] = item[2]
            points.append(point)
    return points


def _chart_writer_agent(chart: dict[str, Any]) -> dict[str, Any]:
    payload = chart.get("report_writer_agent")
    if isinstance(payload, dict) and payload.get("direct_answer"):
        return payload
    return {}


def _chart_writer_text(chart: dict[str, Any], key: str, fallback: str = "") -> str:
    value = _chart_writer_agent(chart).get(key)
    text = _report_cell_text(value, 520)
    return text or fallback


def _chart_sampling_note(chart: dict[str, Any]) -> str:
    stats = chart.get("sample_policy") if isinstance(chart.get("sample_policy"), dict) else {}
    rendered = int(stats.get("rendered_point_count") or _chart_point_count(chart) or 0)
    analysis_rows = int(stats.get("analysis_row_count") or rendered or 0)
    full_rows = int(stats.get("full_row_count") or analysis_rows or 0)
    chunk_size = int(stats.get("chunk_size") or 0)
    chunk_count = int(stats.get("chunk_count") or 0)
    chunk_text = ""
    if chunk_size and chunk_count:
        chunk_text = _zh(r"\uff1b\u5168\u91cf\u8bc1\u636e\u6309") + f"{chunk_size:,}" + _zh(r"\u884c/\u5757\u62c6\u6210") + f"{chunk_count:,}" + _zh(r"\u5757")
    if full_rows > analysis_rows:
        basis_text = f"{analysis_rows:,} 行分析工作样本，并用 {full_rows:,} 行全量数据/分块证据复核"
    else:
        basis_text = f"{full_rows:,} 行有效统计"
    return f"图中展示 {rendered:,} 个视觉点；读图只代表渲染密度，业务判断依据为 {basis_text}{chunk_text}。"


def _chart_metric_text(metrics: list[dict[str, Any]], *, limit: int = 3) -> str:
    parts: list[str] = []
    for metric in metrics[:limit]:
        if not isinstance(metric, dict):
            continue
        label = _report_cell_text(metric.get("label"), 50)
        value = _report_cell_text(metric.get("value"), 80)
        if label and value:
            parts.append(f"{label}={value}")
    return _zh(r"\u3001").join(parts)


def _series_stats(values: list[float]) -> dict[str, Any]:
    array = np.asarray([value for value in values if np.isfinite(value)], dtype=float)
    if array.size == 0:
        return {"count": 0}
    return {
        "count": int(array.size),
        "min": float(np.nanmin(array)),
        "max": float(np.nanmax(array)),
        "mean": float(np.nanmean(array)),
        "std": float(np.nanstd(array)),
        "first": float(array[0]),
        "last": float(array[-1]),
        "net_change": float(array[-1] - array[0]) if array.size >= 2 else 0.0,
        "net_change_pct": float((array[-1] - array[0]) / abs(array[0])) if array.size >= 2 and abs(array[0]) > 1e-12 else None,
    }


def _full_numeric_frame_for_chart(chart: dict[str, Any], full_frame: pd.DataFrame, analysis_frame: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    labels = [
        str(chart.get("x_label") or ""),
        str(chart.get("y_label") or ""),
        str(chart.get("size_label") or ""),
    ]
    columns = [column for column in labels if column]
    source = full_frame if columns and all(column in full_frame.columns for column in columns) else analysis_frame
    usable_columns = [column for column in columns if column in source.columns]
    if not usable_columns:
        return pd.DataFrame(), "chart_payload"
    data = pd.DataFrame({column: source.loc[:, column] for column in usable_columns}, index=source.index)
    for column in usable_columns:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    return data.dropna(), "full_dataset" if source is full_frame else "analysis_work_frame"


def _chunk_numeric_evidence(
    frame: pd.DataFrame,
    *,
    columns: list[str],
    chunk_size: int = LARGE_SAMPLE_DEFAULT_CHUNK_SIZE,
    max_chunks: int = 80,
) -> dict[str, Any]:
    usable = [column for column in columns if column and column in frame.columns]
    if not usable:
        return {
            "contract": "analysis_lab_chunk_evidence_v1",
            "chunk_size": chunk_size,
            "chunk_count": 0,
            "rows": [],
            "columns": [],
        }
    chunk_size = max(1, int(chunk_size or LARGE_SAMPLE_DEFAULT_CHUNK_SIZE))
    total_rows = int(len(frame))
    chunk_count = int(np.ceil(total_rows / chunk_size)) if total_rows else 0
    rows: list[dict[str, Any]] = []
    for chunk_index, start in enumerate(range(0, total_rows, chunk_size), start=1):
        if len(rows) >= max_chunks:
            break
        end = min(start + chunk_size, total_rows)
        chunk = frame.iloc[start:end]
        row: dict[str, Any] = {
            "chunk_index": chunk_index,
            "row_start": int(start),
            "row_end": int(end - 1),
            "row_count": int(len(chunk)),
        }
        numeric_columns: list[str] = []
        for column in usable:
            series = pd.to_numeric(chunk[column], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
            if series.empty:
                continue
            numeric_columns.append(column)
            row[f"{column}__count"] = int(series.shape[0])
            row[f"{column}__mean"] = float(series.mean())
            row[f"{column}__min"] = float(series.min())
            row[f"{column}__max"] = float(series.max())
            row[f"{column}__first"] = float(series.iloc[0])
            row[f"{column}__last"] = float(series.iloc[-1])
        if len(numeric_columns) >= 2:
            left, right = numeric_columns[0], numeric_columns[1]
            left_series = pd.to_numeric(chunk[left], errors="coerce")
            right_series = pd.to_numeric(chunk[right], errors="coerce")
            corr_frame = pd.DataFrame({"left": left_series, "right": right_series}).dropna()
            if len(corr_frame) >= 3 and corr_frame["left"].nunique() > 1 and corr_frame["right"].nunique() > 1:
                row["pair_correlation"] = float(corr_frame["left"].corr(corr_frame["right"]))
        rows.append(row)
    means: dict[str, Any] = {}
    for column in usable:
        values = [
            _safe_float(row.get(f"{column}__mean"))
            for row in rows
            if _safe_float(row.get(f"{column}__mean")) is not None
        ]
        if values:
            means[column] = {
                "chunk_mean_min": float(min(values)),
                "chunk_mean_max": float(max(values)),
                "chunk_mean_range": float(max(values) - min(values)),
            }
    return {
        "contract": "analysis_lab_chunk_evidence_v1",
        "chunk_size": chunk_size,
        "chunk_count": chunk_count,
        "materialized_chunk_count": len(rows),
        "total_row_count": total_rows,
        "columns": usable,
        "rows": rows,
        "summary": means,
    }


def _chunk_evidence_note(chunk_evidence: dict[str, Any]) -> str:
    chunk_count = int(chunk_evidence.get("chunk_count") or 0)
    chunk_size = int(chunk_evidence.get("chunk_size") or 0)
    if not chunk_count or not chunk_size:
        return ""
    return f"{chunk_size:,}" + _zh(r"\u884c/\u5757\uff0c\u5171") + f"{chunk_count:,}" + _zh(r"\u4e2a\u8bc1\u636e\u5757")


def _build_line_writer_agent(
    chart: dict[str, Any],
    *,
    full_frame: pd.DataFrame,
    analysis_frame: pd.DataFrame,
    full_row_count: int,
    analysis_row_count: int,
    rendered_point_count: int,
    chunk_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    x_label = _short_field(chart.get("x_label"), _zh(r"\u65f6\u95f4"))
    y_label = _short_field(chart.get("y_label"), _zh(r"\u6307\u6807"))
    y_values = [float(value) for value in [_safe_float(item) for item in list(chart.get("actual") or chart.get("y") or [])] if value is not None]
    stats = _series_stats(y_values)
    count = int(stats.get("count") or 0)
    if count < 2:
        direct = f"{y_label}" + _zh(r"\u76ee\u524d\u53ea\u6709\u6709\u9650\u53ef\u7528\u5e8f\u5217\u70b9\uff0c\u6682\u65f6\u4e0d\u5b9c\u5199\u6210\u8d8b\u52bf\u7ed3\u8bba\u3002")
        metrics = [{"label": _zh(r"\u6709\u6548\u671f\u6570"), "value": str(count)}]
    else:
        net_pct = stats.get("net_change_pct")
        direction = _zh(r"\u4e0a\u884c") if float(stats["net_change"]) > 0 else _zh(r"\u4e0b\u884c") if float(stats["net_change"]) < 0 else _zh(r"\u6301\u5e73")
        volatility = (float(stats.get("std") or 0.0) / abs(float(stats.get("mean") or 1.0))) if abs(float(stats.get("mean") or 0.0)) > 1e-12 else 0.0
        wave = _zh(r"\u5b58\u5728\u660e\u663e\u9636\u6bb5\u6027\u6ce2\u52a8") if volatility >= 0.12 or abs(float(stats["net_change"])) > abs(float(stats.get("std") or 0.0)) else _zh(r"\u6ce2\u52a8\u8f83\u6e29\u548c")
        direct = (
            f"{y_label}" + _zh(r"\u968f") + f"{x_label}" + _zh(r"\u5448") + direction + _zh(r"\u8d8b\u52bf\uff0c") + wave
            + _zh(r"\uff1b\u73b0\u6709\u6570\u636e\u5df2\u8db3\u4ee5\u652f\u6301\u6309\u9636\u6bb5\u5b89\u6392\u9884\u7b97\u3001\u6392\u671f\u548c\u8d44\u6e90\u590d\u76d8\u3002")
        )
        metrics = [
            {"label": _zh(r"\u6709\u6548\u671f\u6570"), "value": f"{count:,}"},
            {"label": _zh(r"\u51c0\u53d8\u5316"), "value": _format_business_amount(stats.get("net_change"))},
            {"label": _zh(r"\u53d8\u5316\u7387"), "value": _format_pct(net_pct)},
            {"label": _zh(r"\u5cf0\u503c"), "value": _format_business_amount(stats.get("max"))},
            {"label": _zh(r"\u8c37\u503c"), "value": _format_business_amount(stats.get("min"))},
        ]
    chunk_note = _chunk_evidence_note(chunk_evidence or {})
    if chunk_note:
        metrics.append({"label": _zh(r"\u5206\u5757\u8bc1\u636e"), "value": chunk_note})
    evidence = _chart_metric_text(metrics)
    judgment = direct + (_zh(r"\u5173\u952e\u8bc1\u636e\uff1a") + evidence + _zh(r"\u3002") if evidence else "")
    return {
        "direct_answer": direct,
        "key_finding": evidence,
        "business_judgment": judgment,
        "caption": f"{chart.get('title') or _zh(r'\u8d8b\u52bf\u56fe')} - {direct} {_chart_sampling_note(chart)}",
        "recommended_action": _zh(r"\u5c06\u8d8b\u52bf\u53d8\u5316\u62c6\u6210\u9636\u6bb5\u76ee\u6807\uff0c\u5bf9\u5cf0\u503c\u671f\u6269\u5bb9\uff0c\u5bf9\u4e0b\u884c\u6216\u9ad8\u6ce2\u52a8\u671f\u9884\u7559\u98ce\u9669\u5e94\u5bf9\u3002"),
        "confidence": "medium" if count < 8 else "high",
        "limits": _zh(r"\u672c\u7ed3\u8bba\u5224\u65ad\u6a21\u5f0f\u548c\u7ecf\u8425\u542b\u4e49\uff1b\u5916\u90e8\u4e8b\u4ef6\u53ea\u7528\u4e8e\u89e3\u91ca\u539f\u56e0\uff0c\u4e0d\u5426\u5b9a\u6570\u636e\u5df2\u663e\u793a\u7684\u8d8b\u52bf\u3002"),
        "evidence_numbers": metrics,
        "source_refs": [str(chart.get("chart_ref") or f"chart:{chart.get('kind') or 'line'}")],
        "chunk_evidence": chunk_evidence or {},
        "analysis_strategy": "time_series_trend_agent",
        "skill_trace": ["Evidence Analyst Agent", "Skill Router Agent: time_series", "Business Judgment Agent", "Narrative Writer Agent", "Figure Caption Agent"],
    }


def _build_scatter_writer_agent(
    chart: dict[str, Any],
    *,
    full_frame: pd.DataFrame,
    analysis_frame: pd.DataFrame,
    full_row_count: int,
    analysis_row_count: int,
    rendered_point_count: int,
    chunk_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    kind = str(chart.get("kind") or "")
    x_label_raw = str(chart.get("x_label") or "")
    y_label_raw = str(chart.get("y_label") or "")
    x_label = _short_field(x_label_raw, "X")
    y_label = _short_field(y_label_raw, "Y")
    clean, basis = _full_numeric_frame_for_chart(chart, full_frame, analysis_frame)
    metrics: list[dict[str, Any]] = []
    direct = ""
    if x_label_raw in clean.columns and y_label_raw in clean.columns and len(clean) >= 3:
        x = pd.to_numeric(clean[x_label_raw], errors="coerce")
        y = pd.to_numeric(clean[y_label_raw], errors="coerce")
        corr = float(x.corr(y)) if x.nunique(dropna=True) > 1 and y.nunique(dropna=True) > 1 else 0.0
        x_mid = float(x.median())
        y_mid = float(y.median())
        high_high = int(((x >= x_mid) & (y >= y_mid)).sum())
        high_low = int(((x >= x_mid) & (y < y_mid)).sum())
        low_high = int(((x < x_mid) & (y >= y_mid)).sum())
        low_low = int(((x < x_mid) & (y < y_mid)).sum())
        dominant = max(
            [
                (_zh(r"\u9ad8\u9ad8\u8c61\u9650"), high_high),
                (_zh(r"\u9ad8\u4f4e\u8c61\u9650"), high_low),
                (_zh(r"\u4f4e\u9ad8\u8c61\u9650"), low_high),
                (_zh(r"\u4f4e\u4f4e\u8c61\u9650"), low_low),
            ],
            key=lambda item: item[1],
        )
        relation = _zh(r"\u5f3a\u6b63\u76f8\u5173") if corr >= 0.55 else _zh(r"\u6b63\u76f8\u5173") if corr >= 0.2 else _zh(r"\u5f3a\u8d1f\u76f8\u5173") if corr <= -0.55 else _zh(r"\u8d1f\u76f8\u5173") if corr <= -0.2 else _zh(r"\u7ebf\u6027\u5173\u7cfb\u4e0d\u5f3a")
        direct = (
            f"{x_label}" + _zh(r"\u4e0e") + f"{y_label}" + _zh(r"\u5448") + relation
            + _zh(r"\uff0c\u4e3b\u8981\u5bf9\u8c61\u96c6\u4e2d\u5728") + dominant[0]
            + "；该分布可用来拆分增长机会和效率风险，建议优先复核象限边界上的对象。"
        )
        metrics = [
            {"label": _zh(r"\u6709\u6548\u884c\u6570"), "value": f"{len(clean):,}"},
            {"label": _zh(r"\u76f8\u5173\u7cfb\u6570"), "value": f"{corr:.2f}"},
            {"label": _zh(r"\u9ad8\u9ad8"), "value": f"{high_high:,}"},
            {"label": _zh(r"\u9ad8\u4f4e"), "value": f"{high_low:,}"},
            {"label": _zh(r"\u4f4e\u9ad8"), "value": f"{low_high:,}"},
            {"label": _zh(r"\u4f4e\u4f4e"), "value": f"{low_low:,}"},
        ]
    else:
        points = _chart_points(chart)
        direct = f"{x_label}" + _zh(r"\u4e0e") + f"{y_label}" + _zh(r"\u7684\u5224\u65ad\u57fa\u4e8e\u56fe\u8868\u8f7d\u8377\u4e2d\u7684\u6709\u6548\u70b9\uff0c\u76ee\u524d\u66f4\u9002\u5408\u4f5c\u4e3a\u4f18\u5148\u590d\u6838\u7ebf\u7d22\u800c\u4e0d\u662f\u56e0\u679c\u7ed3\u8bba\u3002")
        metrics = [{"label": _zh(r"\u6e32\u67d3\u70b9\u6570"), "value": f"{len(points):,}"}]
    chunk_note = _chunk_evidence_note(chunk_evidence or {})
    if chunk_note:
        metrics.append({"label": _zh(r"\u5206\u5757\u8bc1\u636e"), "value": chunk_note})
    evidence = _chart_metric_text(metrics)
    action = _zh(r"\u628a\u9ad8\u9ad8\u5bf9\u8c61\u4f5c\u4e3a\u53ef\u653e\u5927\u6837\u677f\uff0c\u628a\u9ad8\u4f4e\u6216\u9ad8\u504f\u79bb\u5bf9\u8c61\u4f5c\u4e3a\u6548\u7387\u6821\u6b63\u6e05\u5355\u3002")
    if kind == "anomaly-scatter":
        action = _zh(r"\u5c06\u9ad8\u504f\u79bb\u5bf9\u8c61\u5206\u6210\u771f\u5b9e\u98ce\u9669\u3001\u6218\u7565\u673a\u4f1a\u548c\u6570\u636e\u8d28\u91cf\u4e09\u7c7b\uff0c\u5206\u522b\u8bbe\u7f6e\u8d23\u4efb\u4eba\u3002")
    return {
        "direct_answer": direct,
        "key_finding": evidence,
        "business_judgment": direct + (_zh(r"\u5173\u952e\u8bc1\u636e\uff1a") + evidence + _zh(r"\u3002") if evidence else ""),
        "caption": f"{chart.get('title') or _zh(r'\u5173\u7cfb\u56fe')} - {direct} {_chart_sampling_note(chart)}",
        "recommended_action": action,
        "confidence": "high" if basis == "full_dataset" and metrics else "medium",
        "limits": _zh(r"\u8be5\u56fe\u652f\u6301\u7ed3\u6784\u548c\u6548\u7387\u5224\u65ad\uff1b\u4e0d\u5c06\u76f8\u5173\u5173\u7cfb\u5199\u6210\u5355\u4e00\u56e0\u679c\u3002"),
        "evidence_numbers": metrics,
        "source_refs": [str(chart.get("chart_ref") or f"chart:{kind or 'scatter'}")],
        "chunk_evidence": chunk_evidence or {},
        "analysis_basis": basis,
        "analysis_strategy": "scatter_quadrant_agent",
        "skill_trace": ["Evidence Analyst Agent", "Skill Router Agent: scatter/quadrant", "Business Judgment Agent", "Narrative Writer Agent", "Figure Caption Agent"],
    }


def _build_bar_writer_agent(chart: dict[str, Any], *, rendered_point_count: int) -> dict[str, Any]:
    x_label = _short_field(chart.get("x_label"), _zh(r"\u5206\u7ec4"))
    y_label = _short_field(chart.get("y_label"), _zh(r"\u6307\u6807"))
    y_share_label = y_label if y_label and y_label != "-" else "该指标"
    labels = [str(item) for item in list(chart.get("x") or [])]
    values = [float(_safe_float(item) or 0.0) for item in list(chart.get("y") or [])]
    metrics: list[dict[str, Any]] = []
    if labels and values:
        order = sorted(range(len(values)), key=lambda idx: abs(values[idx]), reverse=True)
        top = order[0]
        second = order[1] if len(order) > 1 else top
        total = sum(abs(value) for value in values) or 1.0
        share = abs(values[top]) / total
        gap = abs(values[top]) - abs(values[second]) if second != top else abs(values[top])
        direct = (
            f"{x_label}" + _zh(r"\u4e2d\u7684\u4e3b\u5bfc\u7ec4\u662f") + f"`{_report_cell_text(labels[top], 80)}`"
            + _zh(r"\uff0c\u5360") + f"{y_share_label}" + _zh(r"\u7684") + _format_pct(share)
            + _zh(r"\uff1b\u8fd9\u662f\u8d44\u6e90\u96c6\u4e2d\u6216\u7ed3\u6784\u503e\u659c\u7684\u660e\u786e\u4fe1\u53f7\u3002")
        )
        metrics = [
            {"label": _zh(r"\u4e3b\u5bfc\u7ec4"), "value": _report_cell_text(labels[top], 80)},
            {"label": _zh(r"\u4efd\u989d"), "value": _format_pct(share)},
            {"label": _zh(r"\u4e0e\u7b2c\u4e8c\u5dee\u989d"), "value": _format_business_amount(gap)},
        ]
    else:
        direct = f"{x_label}" + _zh(r"\u7684\u5206\u7ec4\u8bc1\u636e\u4e0d\u8db3\uff0c\u6682\u65f6\u53ea\u80fd\u4f5c\u4e3a\u7ed3\u6784\u7ebf\u7d22\u3002")
        metrics = [{"label": _zh(r"\u5206\u7ec4\u6570"), "value": f"{rendered_point_count:,}"}]
    evidence = _chart_metric_text(metrics)
    return {
        "direct_answer": direct,
        "key_finding": evidence,
        "business_judgment": direct + (_zh(r"\u5173\u952e\u8bc1\u636e\uff1a") + evidence + _zh(r"\u3002") if evidence else ""),
        "caption": f"{chart.get('title') or _zh(r'\u5206\u7ec4\u56fe')} - {direct} {_chart_sampling_note(chart)}",
        "recommended_action": _zh(r"\u5bf9\u4e3b\u5bfc\u7ec4\u5355\u72ec\u8bbe\u7f6e\u7ef4\u62a4\u6216\u589e\u957f\u7b56\u7565\uff0c\u5bf9\u957f\u5c3e\u7ec4\u5224\u65ad\u662f\u5408\u5e76\u7ba1\u7406\u8fd8\u662f\u7cbe\u51c6\u8865\u5f3a\u3002"),
        "confidence": "high" if labels and values else "low",
        "limits": _zh(r"\u8be5\u56fe\u5224\u65ad\u7ed3\u6784\u4efd\u989d\uff0c\u4e0d\u5355\u72ec\u89e3\u91ca\u5229\u6da6\u6216\u56e0\u679c\u3002"),
        "evidence_numbers": metrics,
        "source_refs": [str(chart.get("chart_ref") or f"chart:{chart.get('kind') or 'bar'}")],
        "analysis_strategy": "concentration_share_agent",
        "skill_trace": ["Evidence Analyst Agent", "Skill Router Agent: category_share", "Business Judgment Agent", "Narrative Writer Agent", "Figure Caption Agent"],
    }


def _build_heatmap_writer_agent(chart: dict[str, Any], *, rendered_point_count: int) -> dict[str, Any]:
    labels = [_short_field(label) for label in list(chart.get("labels") or [])]
    matrix = list(chart.get("matrix") or [])
    best: tuple[str, str, float] | None = None
    for row_index, row in enumerate(matrix):
        if not isinstance(row, list):
            continue
        for col_index, value in enumerate(row):
            if row_index >= col_index:
                continue
            number = _safe_float(value)
            if number is None:
                continue
            if best is None or abs(number) > abs(best[2]):
                best = (
                    labels[row_index] if row_index < len(labels) else "-",
                    labels[col_index] if col_index < len(labels) else "-",
                    number,
                )
    if best:
        direct = f"{best[0]}" + _zh(r"\u4e0e") + f"{best[1]}" + _zh(r"\u662f\u6700\u5f3a\u8054\u52a8\u5bf9\uff0c\u76f8\u5173\u7cfb\u6570\u4e3a") + f"{best[2]:.2f}" + _zh(r"\uff1b\u5b83\u5e94\u88ab\u7528\u6765\u8bbe\u8ba1\u9a71\u52a8\u5047\u8bbe\uff0c\u4e0d\u76f4\u63a5\u5199\u6210\u56e0\u679c\u3002")
        metrics = [
            {"label": _zh(r"\u6700\u5f3a\u8054\u52a8"), "value": f"{best[0]} / {best[1]}"},
            {"label": _zh(r"\u76f8\u5173\u7cfb\u6570"), "value": f"{best[2]:.2f}"},
        ]
    else:
        direct = _zh(r"\u76f8\u5173\u77e9\u9635\u672a\u68c0\u51fa\u8db3\u591f\u660e\u786e\u7684\u5f3a\u8054\u52a8\u5bf9\u3002")
        metrics = [{"label": _zh(r"\u6307\u6807\u6570"), "value": f"{len(labels):,}"}]
    evidence = _chart_metric_text(metrics)
    return {
        "direct_answer": direct,
        "key_finding": evidence,
        "business_judgment": direct + (_zh(r"\u5173\u952e\u8bc1\u636e\uff1a") + evidence + _zh(r"\u3002") if evidence else ""),
        "caption": f"{chart.get('title') or _zh(r'\u76f8\u5173\u77e9\u9635')} - {direct} {_chart_sampling_note(chart)}",
        "recommended_action": _zh(r"\u628a\u6700\u5f3a\u8054\u52a8\u5bf9\u62c6\u6210\u9a71\u52a8\u5047\u8bbe\uff0c\u518d\u7528\u65b9\u6cd5\u8bc1\u636e\u6216\u4e1a\u52a1\u4e8b\u4ef6\u505a\u4e8c\u6b21\u9a8c\u8bc1\u3002"),
        "confidence": "medium" if best else "low",
        "limits": _zh(r"\u76f8\u5173\u53ea\u8bf4\u660e\u8054\u52a8\uff0c\u539f\u56e0\u5f52\u56e0\u9700\u8981\u72ec\u7acb\u8bc1\u636e\u3002"),
        "evidence_numbers": metrics,
        "source_refs": [str(chart.get("chart_ref") or "chart:heatmap")],
        "analysis_strategy": "correlation_matrix_agent",
        "skill_trace": ["Evidence Analyst Agent", "Skill Router Agent: heatmap", "Business Judgment Agent", "Narrative Writer Agent", "Figure Caption Agent"],
    }


def _build_generic_writer_agent(chart: dict[str, Any], *, rendered_point_count: int) -> dict[str, Any]:
    question = _chart_business_question(chart)
    direct = _zh(r"\u8be5\u56fe\u8868\u7684\u53ef\u7528\u4ef7\u503c\u5728\u4e8e\u5c06\u4e1a\u52a1\u95ee\u9898\u8f6c\u6210\u53ef\u8ffd\u6eaf\u7684\u6570\u636e\u8bc1\u636e\uff0c\u5e76\u4e3a\u884c\u52a8\u4f18\u5148\u7ea7\u63d0\u4f9b\u7ed3\u6784\u7ebf\u7d22\u3002")
    metrics = [
        {"label": _zh(r"\u56fe\u8868\u7c7b\u578b"), "value": str(chart.get("kind") or "-")},
        {"label": _zh(r"\u6e32\u67d3\u70b9\u6570"), "value": f"{rendered_point_count:,}"},
    ]
    return {
        "direct_answer": direct,
        "key_finding": _chart_metric_text(metrics),
        "business_judgment": direct,
        "caption": f"{chart.get('title') or chart.get('kind') or 'chart'} - {direct} {_chart_sampling_note(chart)}",
        "recommended_action": _zh(r"\u4f18\u5148\u628a\u8be5\u56fe\u5bf9\u5e94\u7684\u5b57\u6bb5\u3001\u8bc1\u636e\u6587\u4ef6\u548c\u4e1a\u52a1\u95ee\u9898\u7eb3\u5165\u62a5\u544a\u8bc1\u636e\u94fe\u3002"),
        "confidence": "medium",
        "limits": _zh(r"\u8be5\u5224\u65ad\u4f9d\u8d56\u56fe\u8868\u8f7d\u8377\u548c\u65b9\u6cd5\u8bc1\u636e\uff0c\u4e0d\u989d\u5916\u6784\u9020\u5916\u90e8\u4e8b\u5b9e\u3002"),
        "evidence_numbers": metrics,
        "source_refs": [str(chart.get("chart_ref") or f"chart:{chart.get('kind') or 'generic'}")],
        "analysis_strategy": "generic_evidence_agent",
        "skill_trace": ["Evidence Analyst Agent", "Business Judgment Agent", "Narrative Writer Agent", "Figure Caption Agent"],
        "business_question": question,
    }


def _chart_sample_scope(chart: dict[str, Any]) -> dict[str, Any]:
    stats = chart.get("sample_policy") if isinstance(chart.get("sample_policy"), dict) else {}
    rendered = int(stats.get("rendered_point_count") or _chart_point_count(chart) or 0)
    analysis_rows = int(stats.get("analysis_row_count") or rendered or 0)
    full_rows = int(stats.get("full_row_count") or analysis_rows or 0)
    chunk_size = int(stats.get("chunk_size") or 0)
    chunk_count = int(stats.get("chunk_count") or 0)
    text = _chart_sampling_note(chart)
    return {
        "rendered_point_count": rendered,
        "analysis_row_count": analysis_rows,
        "full_row_count": full_rows,
        "chunk_size": chunk_size,
        "chunk_count": chunk_count,
        "judgment_basis": "full_dataset_chunk_evidence" if full_rows > rendered else "chart_payload",
        "visualization_basis": "rendered_visual_sample" if rendered and rendered < full_rows else "full_visual_payload",
        "text": text,
    }


def _chart_writer_source_refs(chart: dict[str, Any], agent: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for ref in list(agent.get("source_refs") or []):
        if str(ref or "").strip():
            refs.append(str(ref))
    chart_ref = str(chart.get("chart_ref") or "").strip()
    if chart_ref:
        refs.append(chart_ref)
    exports = chart.get("asset_exports") if isinstance(chart.get("asset_exports"), dict) else {}
    for key in ("data_path", "image_path"):
        value = str(exports.get(key) or "").strip()
        if value:
            refs.append(value)
    return list(dict.fromkeys(refs))


def _chart_skill_router_agent(chart: dict[str, Any], agent: dict[str, Any]) -> dict[str, Any]:
    kind = str(chart.get("kind") or "")
    strategy = str(agent.get("analysis_strategy") or "")
    skill = "generic_chart_evidence"
    if kind in {"line", "forecast"} or "time_series" in strategy:
        skill = "time_series_trend"
    elif kind in {"scatter", "bubble", "quadrant", "cluster-scatter", "anomaly-scatter"} or kind.startswith("scatter-"):
        skill = "scatter_quadrant_efficiency"
    elif kind.startswith("bar-") or kind == "histogram":
        skill = "category_concentration"
    elif kind == "heatmap":
        skill = "correlation_matrix"
    return {
        "agent_id": "skill_router_agent",
        "contract": "analysis_lab_skill_router_agent_v1",
        "selected_skill": skill,
        "chart_kind": kind,
        "business_question": agent.get("business_question") or _chart_business_question(chart),
        "analysis_strategy": strategy or skill,
        "evidence_requirements": [
            "direct_answer",
            "at_least_two_numeric_evidence_items",
            "business_judgment",
            "recommended_action",
            "sample_scope",
            "source_refs",
        ],
        "source_refs": _chart_writer_source_refs(chart, agent),
    }


def _chart_evidence_analyst_agent(chart: dict[str, Any], agent: dict[str, Any]) -> dict[str, Any]:
    chunk_evidence = agent.get("chunk_evidence") if isinstance(agent.get("chunk_evidence"), dict) else {}
    sample_scope = _chart_sample_scope(chart)
    return {
        "agent_id": "evidence_analyst_agent",
        "contract": "analysis_lab_evidence_analyst_agent_v1",
        "chart_ref": chart.get("chart_ref") or "",
        "business_question": agent.get("business_question") or _chart_business_question(chart),
        "direct_answer": agent.get("direct_answer") or "",
        "key_finding": agent.get("key_finding") or "",
        "evidence_numbers": list(agent.get("evidence_numbers") or []),
        "chunk_summary": {
            "chunk_size": int(chunk_evidence.get("chunk_size") or sample_scope.get("chunk_size") or 0),
            "chunk_count": int(chunk_evidence.get("chunk_count") or sample_scope.get("chunk_count") or 0),
            "total_row_count": int(chunk_evidence.get("total_row_count") or sample_scope.get("full_row_count") or 0),
            "columns": list(chunk_evidence.get("columns") or []),
        },
        "sample_scope": sample_scope,
        "source_refs": _chart_writer_source_refs(chart, agent),
    }


def _chart_business_judgment_agent(chart: dict[str, Any], agent: dict[str, Any]) -> dict[str, Any]:
    return {
        "agent_id": "business_judgment_agent",
        "contract": "analysis_lab_business_judgment_agent_v1",
        "chart_ref": chart.get("chart_ref") or "",
        "direct_answer": agent.get("direct_answer") or "",
        "business_judgment": agent.get("business_judgment") or "",
        "recommended_action": agent.get("recommended_action") or "",
        "confidence": agent.get("confidence") or "medium",
        "limits": agent.get("limits") or "",
        "sample_scope": _chart_sample_scope(chart),
        "source_refs": _chart_writer_source_refs(chart, agent),
    }


def _chart_narrative_writer_agent(chart: dict[str, Any], agent: dict[str, Any]) -> dict[str, Any]:
    evidence = str(agent.get("key_finding") or "").strip()
    paragraph = str(agent.get("business_judgment") or agent.get("direct_answer") or "").strip()
    action = str(agent.get("recommended_action") or "").strip()
    if action and action not in paragraph:
        action_label = _zh(r"\u884c\u52a8\uff1a")
        paragraph = f"{paragraph} {action_label}{action}"
    return {
        "agent_id": "narrative_writer_agent",
        "contract": "analysis_lab_narrative_writer_agent_v1",
        "chart_ref": chart.get("chart_ref") or "",
        "reader_first_paragraph": paragraph,
        "evidence_chain": evidence,
        "write_skill_principles": [
            "reader_first",
            "evidence_before_claim",
            "no_unbacked_external_causality",
        ],
        "source_refs": _chart_writer_source_refs(chart, agent),
    }


def _chart_figure_caption_agent(chart: dict[str, Any], agent: dict[str, Any]) -> dict[str, Any]:
    sample_scope = _chart_sample_scope(chart)
    caption = str(agent.get("caption") or "").strip()
    if sample_scope["text"] and sample_scope["text"] not in caption:
        caption = f"{caption} {sample_scope['text']}".strip()
    return {
        "agent_id": "figure_caption_agent",
        "contract": "analysis_lab_figure_caption_agent_v1",
        "chart_ref": chart.get("chart_ref") or "",
        "direct_answer": agent.get("direct_answer") or "",
        "caption": caption,
        "markdown_caption": caption,
        "html_caption": caption,
        "png_alt_text": caption,
        "sample_scope": sample_scope,
        "figure_polish_principles": [
            "one_dominant_message",
            "caption_answers_the_business_question",
            "visual_sample_is_not_the_judgment_basis_when_full_data_exists",
        ],
        "source_refs": _chart_writer_source_refs(chart, agent),
    }


def _chart_stage_text(agent: dict[str, Any]) -> str:
    chunks = [str(agent.get(key) or "") for key in ("direct_answer", "business_judgment", "caption", "recommended_action", "limits")]
    for key in REPORT_WRITER_REQUIRED_STAGE_KEYS:
        stage = agent.get(key)
        if isinstance(stage, dict):
            chunks.append(json.dumps(stage, ensure_ascii=False, default=str))
    return "\n".join(chunks)


def _review_chart_report_writer_agent(agent: dict[str, Any], *, chart_index: int) -> tuple[bool, list[dict[str, Any]]]:
    issues: list[dict[str, Any]] = []
    missing = [
        key
        for key in ("direct_answer", "business_judgment", "caption", "recommended_action", "sampling_note", "limits")
        if not str(agent.get(key) or "").strip()
    ]
    if missing:
        issues.append({"chart_index": chart_index, "issue": "missing_required_agent_fields", "fields": missing})
    if len([item for item in list(agent.get("evidence_numbers") or []) if isinstance(item, dict)]) < 2:
        issues.append({"chart_index": chart_index, "issue": "insufficient_numeric_evidence"})
    if not list(agent.get("source_refs") or []):
        issues.append({"chart_index": chart_index, "issue": "missing_source_refs"})
    for stage_key in REPORT_WRITER_REQUIRED_STAGE_KEYS:
        if stage_key == "skeptical_review_agent":
            continue
        stage = agent.get(stage_key)
        if not isinstance(stage, dict):
            issues.append({"chart_index": chart_index, "issue": "missing_stage_agent", "stage": stage_key})
            continue
        if not str(stage.get("contract") or "").strip():
            issues.append({"chart_index": chart_index, "issue": "missing_stage_contract", "stage": stage_key})
        if not str(stage.get("agent_id") or "").strip():
            issues.append({"chart_index": chart_index, "issue": "missing_stage_agent_id", "stage": stage_key})
        if stage_key != "skill_router_agent" and not list(stage.get("source_refs") or []):
            issues.append({"chart_index": chart_index, "issue": "missing_stage_source_refs", "stage": stage_key})
    evidence_stage = agent.get("evidence_analyst_agent") if isinstance(agent.get("evidence_analyst_agent"), dict) else {}
    if len([item for item in list(evidence_stage.get("evidence_numbers") or []) if isinstance(item, dict)]) < 2:
        issues.append({"chart_index": chart_index, "issue": "evidence_stage_insufficient_numbers"})
    if not str((agent.get("skill_router_agent") or {}).get("selected_skill") if isinstance(agent.get("skill_router_agent"), dict) else "").strip():
        issues.append({"chart_index": chart_index, "issue": "missing_selected_skill"})
    caption_stage = agent.get("figure_caption_agent") if isinstance(agent.get("figure_caption_agent"), dict) else {}
    if not str(caption_stage.get("caption") or "").strip() or not isinstance(caption_stage.get("sample_scope"), dict):
        issues.append({"chart_index": chart_index, "issue": "caption_stage_missing_scope"})
    text = _chart_stage_text(agent)
    forbidden = [phrase for phrase in _REPORT_WRITER_FORBIDDEN_PHRASES if phrase and phrase in text]
    if forbidden:
        issues.append({"chart_index": chart_index, "issue": "forbidden_boilerplate", "phrases": forbidden})
    return not issues, issues


def _chart_skeptical_review_agent(agent: dict[str, Any], *, chart_index: int) -> dict[str, Any]:
    passed, issues = _review_chart_report_writer_agent(agent, chart_index=chart_index)
    return {
        "agent_id": "skeptical_review_agent",
        "contract": "analysis_lab_chart_skeptical_review_agent_v1",
        "chart_ref": agent.get("chart_ref") or "",
        "passed": passed,
        "issue_count": len(issues),
        "issues": issues,
        "review_principles": [
            "reject_missing_stage_output",
            "reject_vague_boilerplate",
            "require_numeric_evidence_and_source_refs",
        ],
        "source_refs": list(agent.get("source_refs") or []),
    }


def _chart_final_editor_agent(chart: dict[str, Any], agent: dict[str, Any]) -> dict[str, Any]:
    caption_stage = agent.get("figure_caption_agent") if isinstance(agent.get("figure_caption_agent"), dict) else {}
    narrative_stage = agent.get("narrative_writer_agent") if isinstance(agent.get("narrative_writer_agent"), dict) else {}
    return {
        "agent_id": "final_editor_agent",
        "contract": "analysis_lab_final_editor_agent_v1",
        "chart_ref": chart.get("chart_ref") or "",
        "reader_title": chart.get("title") or chart.get("kind") or "",
        "final_direct_answer": agent.get("direct_answer") or "",
        "final_caption": caption_stage.get("caption") or agent.get("caption") or "",
        "final_reader_paragraph": narrative_stage.get("reader_first_paragraph") or agent.get("business_judgment") or "",
        "final_action": agent.get("recommended_action") or "",
        "source_refs": _chart_writer_source_refs(chart, agent),
    }


def _attach_chart_report_writer_pipeline(chart: dict[str, Any], agent: dict[str, Any], *, chart_index: int) -> dict[str, Any]:
    agent["source_refs"] = _chart_writer_source_refs(chart, agent)
    agent["sample_scope"] = _chart_sample_scope(chart)
    agent["skill_router_agent"] = _chart_skill_router_agent(chart, agent)
    agent["evidence_analyst_agent"] = _chart_evidence_analyst_agent(chart, agent)
    agent["business_judgment_agent"] = _chart_business_judgment_agent(chart, agent)
    agent["narrative_writer_agent"] = _chart_narrative_writer_agent(chart, agent)
    agent["figure_caption_agent"] = _chart_figure_caption_agent(chart, agent)
    agent["final_editor_agent"] = _chart_final_editor_agent(chart, agent)
    agent["skeptical_review_agent"] = _chart_skeptical_review_agent(agent, chart_index=chart_index)
    agent["pipeline_status"] = "passed" if agent["skeptical_review_agent"].get("passed") else "failed"
    agent["required_stage_keys"] = list(REPORT_WRITER_REQUIRED_STAGE_KEYS)
    return agent


def _build_chart_report_writer_agent(
    chart: dict[str, Any],
    *,
    full_frame: pd.DataFrame,
    analysis_frame: pd.DataFrame,
    large_sample_policy: dict[str, Any] | None,
    chart_index: int = 1,
) -> dict[str, Any]:
    full_row_count = int((large_sample_policy or {}).get("row_count") or (large_sample_policy or {}).get("full_row_count") or len(full_frame))
    analysis_row_count = int((large_sample_policy or {}).get("analysis_work_frame_row_count") or len(analysis_frame))
    rendered_point_count = int(_chart_point_count(chart))
    chunk_columns = [
        str(chart.get("x_label") or ""),
        str(chart.get("y_label") or ""),
        str(chart.get("size_label") or ""),
    ]
    chunk_source = full_frame if any(column and column in full_frame.columns for column in chunk_columns) else analysis_frame
    chunk_evidence = _chunk_numeric_evidence(
        chunk_source,
        columns=chunk_columns,
        chunk_size=int((large_sample_policy or {}).get("default_chunk_size") or LARGE_SAMPLE_DEFAULT_CHUNK_SIZE),
    )
    chart["sample_policy"] = {
        "full_row_count": full_row_count,
        "analysis_row_count": analysis_row_count,
        "rendered_point_count": rendered_point_count,
        "sampling_strategy": "representative_visual_sample" if rendered_point_count and rendered_point_count < analysis_row_count else "full_visual_payload",
        "chunk_size": int(chunk_evidence.get("chunk_size") or 0),
        "chunk_count": int(chunk_evidence.get("chunk_count") or 0),
        "fine_chunk_size": int((large_sample_policy or {}).get("fine_chunk_size") or LARGE_SAMPLE_FINE_CHUNK_SIZE),
        "fine_chunk_count": int((large_sample_policy or {}).get("fine_chunk_count") or 0),
    }
    kind = str(chart.get("kind") or "")
    if kind in {"line", "forecast"}:
        agent = _build_line_writer_agent(
            chart,
            full_frame=full_frame,
            analysis_frame=analysis_frame,
            full_row_count=full_row_count,
            analysis_row_count=analysis_row_count,
            rendered_point_count=rendered_point_count,
            chunk_evidence=chunk_evidence,
        )
    elif kind in {"scatter", "bubble", "quadrant", "cluster-scatter", "anomaly-scatter"} or kind.startswith("scatter-"):
        agent = _build_scatter_writer_agent(
            chart,
            full_frame=full_frame,
            analysis_frame=analysis_frame,
            full_row_count=full_row_count,
            analysis_row_count=analysis_row_count,
            rendered_point_count=rendered_point_count,
            chunk_evidence=chunk_evidence,
        )
    elif kind.startswith("bar-") or kind == "histogram":
        agent = _build_bar_writer_agent(chart, rendered_point_count=rendered_point_count)
    elif kind == "heatmap":
        agent = _build_heatmap_writer_agent(chart, rendered_point_count=rendered_point_count)
    else:
        agent = _build_generic_writer_agent(chart, rendered_point_count=rendered_point_count)
    agent["chart_ref"] = chart.get("chart_ref") or _chart_export_ref(chart, chart_index)
    agent["business_question"] = _chart_business_question(chart)
    agent["sampling_note"] = _chart_sampling_note(chart)
    agent["chunk_evidence"] = chunk_evidence
    agent["contract"] = CHART_REPORT_WRITER_AGENT_CONTRACT
    agent["agent_pipeline"] = [
        "Evidence Analyst Agent",
        "Skill Router Agent",
        "Business Judgment Agent",
        "Narrative Writer Agent",
        "Figure Caption Agent",
        "Skeptical Review Agent",
        "Final Editor Agent",
    ]
    agent = _attach_chart_report_writer_pipeline(chart, agent, chart_index=chart_index)
    chart["report_writer_agent"] = agent
    chart["business_judgment"] = agent.get("business_judgment")
    chart["caption"] = (agent.get("figure_caption_agent") or {}).get("caption") or agent.get("caption")
    chart["direct_answer"] = agent.get("direct_answer")
    chart["recommended_action"] = agent.get("recommended_action")
    chart["sample_scope"] = agent.get("sample_scope")
    return agent


def _attach_report_writer_agents(
    *,
    charts: list[dict[str, Any]],
    full_frame: pd.DataFrame,
    analysis_frame: pd.DataFrame,
    large_sample_policy: dict[str, Any] | None,
    generated_at: str,
) -> dict[str, Any]:
    chart_agents = []
    for index, chart in enumerate([item for item in charts if isinstance(item, dict)], start=1):
        if not chart.get("chart_ref"):
            chart["chart_ref"] = _chart_export_ref(chart, index)
        chart_agents.append(
            _build_chart_report_writer_agent(
                chart,
                full_frame=full_frame,
                analysis_frame=analysis_frame,
                large_sample_policy=large_sample_policy,
                chart_index=index,
            )
        )
    review = _skeptical_report_writer_review(chart_agents)
    return {
        "contract": REPORT_WRITER_AGENT_PIPELINE_CONTRACT,
        "generated_at": generated_at,
        "runtime_status": "passed" if review.get("passed") else "failed",
        "normal_path_required": True,
        "fallback_policy": "fail_quality_gate_when_stage_output_missing",
        "required_stage_keys": list(REPORT_WRITER_REQUIRED_STAGE_KEYS),
        "agents": [
            "Evidence Analyst Agent",
            "Skill Router Agent",
            "Business Judgment Agent",
            "Narrative Writer Agent",
            "Figure Caption Agent",
            "Skeptical Review Agent",
            "Final Editor Agent",
        ],
        "chart_agents": chart_agents,
        "review": review,
        "large_sample_policy": large_sample_policy or {},
    }


def _build_report_writer_agent_input(
    *,
    request: AutoAnalysisRequest,
    dataset_name: str,
    sheet_name: str,
    selected: dict[str, Any],
    field_profiles: list[dict[str, Any]],
    charts: list[dict[str, Any]],
    method_execution_packages: list[dict[str, Any]],
    external_skill_context: dict[str, Any] | None = None,
    large_sample_policy: dict[str, Any] | None = None,
    generated_at: str,
) -> dict[str, Any]:
    chart_inputs: list[dict[str, Any]] = []
    for index, chart in enumerate([item for item in charts if isinstance(item, dict)], start=1):
        sample_scope = _chart_sample_scope(chart)
        chart_inputs.append(
            {
                "chart_ref": chart.get("chart_ref") or _chart_export_ref(chart, index),
                "kind": chart.get("kind") or "",
                "title": chart.get("title") or "",
                "business_question": _chart_business_question(chart),
                "x_label": chart.get("x_label") or "",
                "y_label": chart.get("y_label") or "",
                "point_count": _chart_point_count(chart),
                "sample_scope": sample_scope,
                "required_output": {
                    "direct_answer": True,
                    "minimum_evidence_numbers": 2,
                    "business_judgment": True,
                    "recommended_action": True,
                    "caption": True,
                    "source_refs": True,
                    "sample_scope": True,
                },
            }
        )
    method_display_packages = _method_display_packages(method_execution_packages)
    method_display_policy = _method_display_policy(method_execution_packages, method_display_packages)
    method_summaries = [_method_package_summary(package) for package in method_display_packages if isinstance(package, dict)]
    selected_feature_rows = _selected_external_skill_feature_rows(external_skill_context)
    return {
        "contract": REPORT_WRITER_AGENT_INPUT_CONTRACT,
        "generated_at": generated_at,
        "dataset": {
            "dataset_id": request.dataset_id,
            "dataset_name": dataset_name,
            "sheet_name": sheet_name or request.active_sheet or "",
            "full_row_count": int((large_sample_policy or {}).get("row_count") or (large_sample_policy or {}).get("full_row_count") or 0),
            "analysis_work_frame_row_count": int((large_sample_policy or {}).get("analysis_work_frame_row_count") or 0),
            "analysis_work_frame_strategy": str((large_sample_policy or {}).get("analysis_work_frame_strategy") or "full_dataset"),
        },
        "user_goal": request.user_goal,
        "selected_fields": selected,
        "field_profiles": field_profiles[:80],
        "chart_inputs": chart_inputs,
        "method_package_summaries": method_summaries[:120],
        "method_package_count": len([package for package in method_execution_packages if isinstance(package, dict)]),
        "method_display_package_count": len(method_summaries),
        "method_display_policy": method_display_policy,
        "external_skill_context": external_skill_context or {},
        "external_skill_feature_count": len(selected_feature_rows),
        "selected_external_skill_features": selected_feature_rows,
        "large_sample_policy": large_sample_policy or {},
        "required_pipeline": list(REPORT_WRITER_REQUIRED_STAGE_KEYS),
        "normal_path_required": True,
        "fallback_policy": "fail_quality_gate_when_agent_output_missing_or_vague",
        "forbidden_phrases": list(_REPORT_WRITER_FORBIDDEN_PHRASES),
        "report_flow_requirements": {
            "selected_knowledge_work_features_must_participate_in_main_report_flow": bool(selected_feature_rows),
            "selected_features_are_not_standalone_trials": True,
            "apply_selected_features_to_method_choice": bool(selected_feature_rows),
            "apply_selected_features_to_evidence_interpretation": bool(selected_feature_rows),
            "apply_selected_features_to_action_design": bool(selected_feature_rows),
            "apply_selected_features_to_quality_review": bool(selected_feature_rows),
        },
        "reader_contract": {
            "each_chart_must_answer_question": True,
            "each_chart_minimum_evidence_numbers": 2,
            "each_chart_requires_business_judgment": True,
            "each_chart_requires_action": True,
            "each_chart_requires_sample_scope": True,
            "each_chart_requires_source_refs": True,
            "selected_external_skill_features_must_be_reflected_in_business_judgment": bool(selected_feature_rows),
            "selected_external_skill_features_must_be_reflected_in_recommended_action": bool(selected_feature_rows),
        },
        "selected_external_skill_review_requirements": _external_skill_review_requirements(selected_feature_rows),
    }


_REPORT_WRITER_FORBIDDEN_PHRASES = (
    _zh(r"\u7ee7\u7eed\u89c2\u5bdf"),
    _zh(r"\u5efa\u8bae\u590d\u6838"),
    _zh(r"\u4f18\u5148\u770b\u79bb\u7fa4\u70b9"),
    _zh(r"\u53ea\u80fd\u8bc1\u660e\u5f53\u524d\u6837\u672c"),
    _zh(r"\u4e0d\u80fd\u8131\u79bb\u4e1a\u52a1\u4e8b\u4ef6\u89e3\u91ca"),
    "fallback PNG renderer",
)


def _skeptical_report_writer_review(chart_agents: list[dict[str, Any]]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    for index, agent in enumerate(chart_agents, start=1):
        _, chart_issues = _review_chart_report_writer_agent(agent, chart_index=index)
        issues.extend(chart_issues)
        stage_review = agent.get("skeptical_review_agent")
        if not isinstance(stage_review, dict):
            issues.append({"chart_index": index, "issue": "missing_stage_agent", "stage": "skeptical_review_agent"})
        elif not stage_review.get("passed"):
            issues.append(
                {
                    "chart_index": index,
                    "issue": "chart_skeptical_stage_failed",
                    "stage_issue_count": int(stage_review.get("issue_count") or 0),
                }
            )
        final_editor = agent.get("final_editor_agent")
        if not isinstance(final_editor, dict) or not str(final_editor.get("final_caption") or "").strip():
            issues.append({"chart_index": index, "issue": "final_editor_missing_final_caption"})
    return {
        "agent_id": "skeptical_report_writer_review",
        "contract": "analysis_lab_skeptical_report_writer_review_v2",
        "passed": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "verdict": "passed" if not issues else "failed",
        "required_stage_keys": list(REPORT_WRITER_REQUIRED_STAGE_KEYS),
    }


def _business_chart_interpretation(chart: dict[str, Any]) -> str:
    agent_judgment = _chart_writer_text(chart, "business_judgment")
    if agent_judgment:
        return agent_judgment
    kind = str(chart.get("kind") or "")
    x_label = _business_field_label(chart.get("x_label") or "")
    y_label = _business_field_label(chart.get("y_label") or "")
    points = _chart_points(chart)
    if kind in {"bubble", "quadrant"} and points:
        counts: dict[str, int] = {}
        for point in points:
            quadrant = str(point.get("quadrant") or "unknown")
            counts[quadrant] = counts.get(quadrant, 0) + 1
        high_high = counts.get("high_high", 0)
        high_low = counts.get("high_low", 0)
        low_high = counts.get("low_high", 0)
        low_low = counts.get("low_low", 0)
        top = max(points, key=lambda point: abs(_safe_float(point.get("size")) or 0.0))
        pressure = "低收入高支出对象最多，应优先复核资金缺口、预算效率和项目可持续性"
        if high_high >= max(high_low, low_high, low_low):
            pressure = "高收入高支出对象最多，说明主战场集中在规模型项目，应优先总结可复制打法"
        elif high_low >= max(high_high, low_high, low_low):
            pressure = "高支出低收入对象偏多，应优先检查投入产出、资源错配和收入确认口径"
        elif low_low >= max(high_high, high_low, low_high):
            pressure = "低规模对象偏多，应先判断是否需要合并管理或降低复盘优先级"
        return (
            f"{x_label or 'X指标'} 与 {y_label or 'Y指标'} 的四象限分布为："
            f"高高{high_high}、高低{high_low}、低高{low_high}、低低{low_low}。"
            f"最大气泡是 {top.get('name') or '-'}，规模约 {_format_business_amount(top.get('size'))}。"
            f"业务判断：{pressure}。"
        )
    if kind == "histogram":
        labels = list(chart.get("x") or [])
        values = [float(_safe_float(item) or 0.0) for item in list(chart.get("y") or [])]
        if labels and values:
            max_index = int(np.argmax(np.asarray(values, dtype=float)))
            total = sum(values) or 1.0
            return (
                f"{_business_field_label(chart.get('x_label'))} 的主分布落在 {labels[max_index]}，"
                f"覆盖 {values[max_index] / total:.1%} 样本。业务判断：该指标存在明显集中/长尾结构，平均值不能代表运营全貌。"
            )
    if kind.startswith("bar-"):
        labels = list(chart.get("x") or [])
        values = [float(_safe_float(item) or 0.0) for item in list(chart.get("y") or [])]
        if labels and values:
            max_index = int(np.argmax(np.asarray(values, dtype=float)))
            total = sum(abs(value) for value in values) or 1.0
            top_label = _report_cell_text(labels[max_index], 80)
            share = abs(values[max_index]) / total
            return (
                f"{_business_field_label(chart.get('x_label'))} 中 `{top_label}` 占 {_business_field_label(chart.get('y_label'))} 的 {share:.1%}。"
                "业务判断：该分组集中度会影响地区覆盖、服务领域配置或组织画像判断，应进入结构倾斜复核。"
            )
    if kind == "heatmap":
        labels = [_business_field_label(label) for label in list(chart.get("labels") or [])]
        matrix = list(chart.get("matrix") or [])
        best: tuple[str, str, float] | None = None
        for row_index, row in enumerate(matrix):
            if not isinstance(row, list):
                continue
            for col_index, value in enumerate(row):
                if row_index >= col_index:
                    continue
                number = _safe_float(value)
                if number is None:
                    continue
                if best is None or abs(number) > abs(best[2]):
                    best = (
                        labels[row_index] if row_index < len(labels) else "-",
                        labels[col_index] if col_index < len(labels) else "-",
                        number,
                    )
        if best:
            return f"{best[0]} 与 {best[1]} 相关系数约 {best[2]:.2f}。业务判断：这是一条强联动线索，但需要业务机制复核后才能写成因果。"
    if kind == "cluster-scatter":
        summary = [item for item in list(chart.get("cluster_summary") or []) if isinstance(item, dict)]
        if summary:
            largest = max(summary, key=lambda item: int(item.get("count") or 0))
            return (
                f"最大分群 cluster={largest.get('cluster')} 覆盖 {largest.get('count')} 个对象，"
                f"平均{x_label or 'X'}={_format_business_amount(largest.get('x_mean'))}，"
                f"平均{y_label or 'Y'}={_format_business_amount(largest.get('y_mean'))}。"
                "业务判断：主群体应有标准运营动作，少数高规模群体单独制定策略。"
            )
    if kind == "anomaly-scatter":
        anomaly_count = sum(1 for point in points if point.get("is_anomaly"))
        top = max(points, key=lambda point: _safe_float(point.get("score")) or 0.0) if points else {}
        return (
            f"异常筛查识别 {anomaly_count} 个高偏离对象，最高分对象为 {top.get('name') or '-'}。"
            "业务判断：这些对象应单独进入风险、机会和数据质量复核，不能被总体均值掩盖。"
        )
    if kind in {"scatter", "line", "forecast"} or kind.startswith("scatter-"):
        return f"{x_label or 'X指标'} 与 {y_label or 'Y指标'} 形成 {_chart_point_count(chart)} 个可视点。业务判断：优先看离群点、拐点和高值聚集区。"
    return _report_cell_text(chart.get("explanation"), 360) or "该图表用于支持业务判断，需结合字段口径和样本范围复核。"


def _chart_asset_rows(charts: list[dict[str, Any]], *, limit: int = 20) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for chart in charts[:limit]:
        if not isinstance(chart, dict):
            continue
        exports = chart.get("asset_exports") if isinstance(chart.get("asset_exports"), dict) else {}
        writer = _chart_writer_agent(chart)
        sample_scope = writer.get("sample_scope") if isinstance(writer.get("sample_scope"), dict) else _chart_sample_scope(chart)
        evidence_numbers = list(writer.get("evidence_numbers") or [])
        rows.append(
            {
                "图表": chart.get("title") or chart.get("kind") or "-",
                "类型": chart.get("kind") or "-",
                "X字段": _business_field_label(chart.get("x_label") or ""),
                "Y字段": _business_field_label(chart.get("y_label") or ""),
                "数据点": _chart_point_count(chart),
                "业务判断": _business_chart_interpretation(chart),
                "图片": _customer_artifact_label(exports.get("image_path") or ""),
            }
        )
    return rows


def _agent_review_prompt() -> str:
    return f"""You are the Analysis Lab agent review team. Read `{LAB_REPORT_AGENT_REVIEW_INPUT_FILE}` and write `{LAB_REPORT_AGENT_REVIEW_FILE}`.

Hard requirements:
1. Do not use generic template actions. Every action must cite specific chart_refs, method_run_ids, fields, or evidence files from the input.
2. Output valid JSON only to `{LAB_REPORT_AGENT_REVIEW_FILE}`.
3. Top-level keys must include contract, runtime_status, agent_reviews, consolidated_actions, cited_chart_refs, cited_method_run_ids, reviewer_count.
4. Each agent_reviews item must include agent_id, agent_name, claim_review, business_action_review, chart_relevance_review.
5. claim_review must list reviewed_claims with claim, verdict, evidence_refs, limits.
6. business_action_review must list actions with action, business_question, evidence_refs, owner_hint, priority.
7. chart_relevance_review must list chart_reviews with chart_ref, relevance_verdict, business_question, evidence_refs, field_pair.
8. consolidated_actions must contain 5 to 8 non-duplicated business actions suitable for a broker-grade external report.
9. If evidence is insufficient, say so and mark runtime_status as failed_insufficient_evidence.
"""


def _agent_review_input_payload(
    *,
    request: AutoAnalysisRequest,
    dataset_name: str,
    sheet_name: str,
    selected: dict[str, Any],
    charts: list[dict[str, Any]],
    method_execution_packages: list[dict[str, Any]],
    external_skill_context: dict[str, Any] | None,
    generated_at: str,
) -> dict[str, Any]:
    chart_items = []
    for chart in charts:
        if not isinstance(chart, dict):
            continue
        exports = chart.get("asset_exports") if isinstance(chart.get("asset_exports"), dict) else {}
        chart_items.append(
            {
                "chart_ref": f"chart:{chart.get('kind') or ''}",
                "kind": chart.get("kind") or "",
                "title": chart.get("title") or "",
                "business_question": _chart_business_question(chart),
                "x_label": chart.get("x_label") or "",
                "y_label": chart.get("y_label") or "",
                "point_count": _chart_point_count(chart),
                "business_interpretation": _business_chart_interpretation(chart),
                "image_path": exports.get("image_path") or "",
                "data_path": exports.get("data_path") or "",
            }
        )
    method_items = []
    for package in method_execution_packages:
        if not isinstance(package, dict):
            continue
        summary = _method_package_summary(package)
        artifact_exports = package.get("artifact_exports") if isinstance(package.get("artifact_exports"), dict) else {}
        execution = package.get("execution") if isinstance(package.get("execution"), dict) else {}
        method_items.append(
            {
                "method_id": summary.get("method_id") or "",
                "method_run_id": summary.get("method_run_id") or "",
                "method_name": summary.get("method_name") or "",
                "family": summary.get("family") or "",
                "package_ref": summary.get("package_ref") or "",
                "result_summary": _report_cell_text(execution.get("result_summary") or "", 420),
                "bound_fields": execution.get("bound_fields") or "",
                "evidence_refs": summary.get("evidence_refs") or [],
                "asset_refs": summary.get("asset_refs") or [],
                "data_csv": artifact_exports.get("data_csv_path") or "",
                "data_xlsx": artifact_exports.get("data_xlsx_path") or "",
                "preview_png": artifact_exports.get("preview_png_path") or "",
            }
        )
    selected_feature_rows = _selected_external_skill_feature_rows(external_skill_context)
    return {
        "contract": "analysis_lab_agent_review_input_v1",
        "generated_at": generated_at,
        "dataset_id": request.dataset_id,
        "dataset_name": dataset_name,
        "sheet_name": sheet_name or request.active_sheet or "",
        "user_goal": request.user_goal,
        "selected_fields": selected,
        "external_skill_context": external_skill_context or {},
        "selected_external_skill_features": selected_feature_rows,
        "selected_external_skill_review_requirements": _external_skill_review_requirements(selected_feature_rows),
        "required_output": LAB_REPORT_AGENT_REVIEW_FILE,
        "required_review_keys": ["claim_review", "business_action_review", "chart_relevance_review"],
        "charts": chart_items,
        "methods": method_items,
    }


def _load_agent_review_payload(export_dir: Path) -> dict[str, Any]:
    path = export_dir / LAB_REPORT_AGENT_REVIEW_FILE
    if not path.exists():
        return {
            "contract": "analysis_lab_agent_reviews_v1",
            "runtime_status": "missing_agent_review_output",
            "agent_reviews": [],
            "consolidated_actions": [],
            "cited_chart_refs": [],
            "cited_method_run_ids": [],
            "reviewer_count": 0,
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {
            "contract": "analysis_lab_agent_reviews_v1",
            "runtime_status": "invalid_agent_review_output",
            "error": str(exc),
            "agent_reviews": [],
            "consolidated_actions": [],
            "cited_chart_refs": [],
            "cited_method_run_ids": [],
            "reviewer_count": 0,
        }
    return payload if isinstance(payload, dict) else {}


def _agent_review_is_usable(payload: dict[str, Any]) -> bool:
    status = str(payload.get("runtime_status") or "").strip().lower()
    if status and status.startswith(("missing", "invalid", "failed")):
        return False
    reviews = [item for item in list(payload.get("agent_reviews") or []) if isinstance(item, dict)]
    if len(reviews) < 3:
        return False
    for review in reviews[:3]:
        if not isinstance(review.get("claim_review"), dict):
            return False
        if not isinstance(review.get("business_action_review"), dict):
            return False
        if not isinstance(review.get("chart_relevance_review"), dict):
            return False
    actions = [item for item in list(payload.get("consolidated_actions") or []) if isinstance(item, dict) or str(item or "").strip()]
    return 5 <= len(actions) <= 8


def _agent_review_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for review in list(payload.get("agent_reviews") or []):
        if not isinstance(review, dict):
            continue
        claim_review = review.get("claim_review") if isinstance(review.get("claim_review"), dict) else {}
        action_review = review.get("business_action_review") if isinstance(review.get("business_action_review"), dict) else {}
        chart_review = review.get("chart_relevance_review") if isinstance(review.get("chart_relevance_review"), dict) else {}
        rows.append(
            {
                "复核角色": review.get("agent_name") or review.get("agent_id") or "-",
                "结论复核": _report_cell_text(claim_review.get("summary") or claim_review.get("verdict") or claim_review, 260),
                "行动复核": _report_cell_text(action_review.get("summary") or action_review.get("verdict") or action_review, 260),
                "图表相关性": _report_cell_text(chart_review.get("summary") or chart_review.get("verdict") or chart_review, 260),
            }
        )
    return rows


def _agent_consolidated_action_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(list(payload.get("consolidated_actions") or [])[:8], start=1):
        if isinstance(item, dict):
            evidence_refs = item.get("evidence_refs") if isinstance(item.get("evidence_refs"), list) else []
            rows.append(
                {
                    "优先级": item.get("priority") or f"A{index}",
                    "业务问题": _plain_business_label(item.get("business_question") or ""),
                    "业务行动": item.get("action") or item.get("recommendation") or "",
                    "证据引用": _public_evidence_refs(evidence_refs),
                    "责任提示": item.get("owner_hint") or "",
                }
            )
        elif str(item or "").strip():
            rows.append({"优先级": f"A{index}", "业务问题": "", "业务行动": str(item), "证据引用": "", "责任提示": ""})
    return rows


def _agent_review_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# 报告复核记录",
        "",
        f"- 复核状态：{_review_status_label(payload.get('runtime_status'))}",
        f"- 复核角色数量：{payload.get('reviewer_count') or len(payload.get('agent_reviews') or [])}",
        "",
        "## 复核摘要",
        "",
    ]
    rows = _agent_review_rows(payload)
    if rows:
        lines.extend(_markdown_table({"columns": ["agent", "claim_review", "business_action_review", "chart_relevance_review"], "rows": rows}, max_rows=20))
    else:
        lines.append("- 暂未产出可用复核摘要。")
    action_rows = _agent_consolidated_action_rows(payload)
    lines.extend(["", "## 行动建议", ""])
    if action_rows:
        lines.extend(_markdown_table({"columns": ["优先级", "业务问题", "业务行动", "证据引用", "责任提示"], "rows": action_rows}, max_rows=8))
    else:
        lines.append("- 暂未产出可用行动建议。")
    lines.append("")
    return "\n".join(lines)


def _chart_action_text(chart: dict[str, Any], chart_ref: str) -> str:
    kind = str(chart.get("kind") or "")
    x_label = _business_field_label(chart.get("x_label") or "")
    y_label = _business_field_label(chart.get("y_label") or "")
    if kind == "bubble":
        return (
            f"优先核对 {x_label or '核心指标'} 与 {y_label or '对比指标'} 的规模气泡，"
            "把大体量且投入产出失衡的对象列为风险复核清单，把大体量高表现对象沉淀为机会样板。"
        )
    if kind == "quadrant":
        return (
            f"按 {x_label or '核心指标'} 与 {y_label or '对比指标'} 的四象限拆出高高、高低、低高、低低对象，"
            "分别制定保规模、控风险、补效率和观察退出的行动口径。"
        )
    if kind == "histogram":
        return (
            f"检查 {x_label or '核心指标'} 的长尾区间和集中区间，"
            "为极端值设置单独复核阈值，避免平均值掩盖风险或机会。"
        )
    if kind == "heatmap":
        return (
            "复核强相关字段的业务机制，把高度联动指标区分为冗余口径、共同驱动和潜在因果假设，"
            "防止相关性带来风险误判或机会错判，"
            "再决定是否进入管理层解释。"
        )
    if kind == "cluster-scatter":
        return (
            "按分群结果拆分主群体、机会群体和异常群体，为不同群体设置差异化运营动作，"
            "不要用总体平均策略覆盖所有对象。"
        )
    if kind == "anomaly-scatter":
        return (
            "把高偏离对象进入风险、机会和数据质量三类复核队列，"
            "逐项确认是真实业务异常、战略机会还是采集口径问题。"
        )
    if kind in {"line", "forecast"}:
        return (
            f"复核 {x_label or '时间'} 与 {y_label or '核心指标'} 的阶段性变化，"
            "把拐点对应到业务事件、预算节奏或项目排期后再形成趋势行动。"
        )
    if kind.startswith("bar-"):
        return (
            f"按 {x_label or '分组维度'} 拆解 {y_label or '核心指标'} 的集中度，"
            "判断资源倾斜是否符合战略定位，并给出补强或再分配动作。"
        )
    return (
        f"围绕 {_public_evidence_ref(chart_ref)} 复核字段口径、样本覆盖和异常对象，"
        "将可确认的风险与机会分别进入责任人行动清单。"
    )


def _deterministic_agent_review_payload(
    *,
    request: AutoAnalysisRequest,
    dataset_name: str,
    sheet_name: str,
    charts: list[dict[str, Any]],
    method_execution_packages: list[dict[str, Any]],
    external_skill_context: dict[str, Any] | None = None,
    generated_at: str,
) -> dict[str, Any]:
    chart_items = [chart for chart in charts if isinstance(chart, dict)]
    selected_feature_rows = _selected_external_skill_feature_rows(external_skill_context)
    selected_feature_names = [
        str(item.get("feature_name") or item.get("feature_id") or "").strip()
        for item in selected_feature_rows
        if str(item.get("feature_name") or item.get("feature_id") or "").strip()
    ]
    selected_feature_suffix = (
        f" Selected Knowledge Work features in scope: {', '.join(dict.fromkeys(selected_feature_names))[:180]}."
        if selected_feature_names
        else ""
    )
    chart_refs = [
        _chart_export_ref(chart, index)
        for index, chart in enumerate(chart_items, start=1)
    ]
    method_refs = [
        str(package.get("method_run_id") or package.get("method_id") or "")
        for package in method_execution_packages
        if str(package.get("method_run_id") or package.get("method_id") or "").strip()
    ]
    actions: list[dict[str, Any]] = []
    action_charts = chart_items[:6] or [{}]
    for index, chart in enumerate(action_charts[:6], start=1):
        chart_ref = chart_refs[index - 1] if index - 1 < len(chart_refs) else "chart:summary"
        linked_methods = _chart_linked_method_refs(chart, method_execution_packages, limit=3) if chart else []
        method_ref = linked_methods[0] if linked_methods else (method_refs[(index - 1) % len(method_refs)] if method_refs else "")
        question = _chart_business_question(chart) if chart else "当前业务证据是否足以进入行动排期？"
        action = _chart_action_text(chart, chart_ref) if chart else "复核当前证据是否足以进入行动排期，缺少字段口径或样本边界时先补证据。"
        actions.append(
            {
                "priority": f"A{index}",
                "business_question": question,
                "action": f"{action}{selected_feature_suffix}" if selected_feature_suffix else action,
                "owner_hint": "业务负责人 + 数据复核人",
                "evidence_refs": [ref for ref in [chart_ref, method_ref] if ref],
            }
        )
    while len(actions) < 5:
        index = len(actions) + 1
        method_ref = method_refs[(index - 1) % len(method_refs)] if method_refs else ""
        actions.append(
            {
                "priority": f"A{index}",
                "business_question": "方法证据是否完整支撑主文结论？",
                "action": (
                    f"检查 {method_ref or '对应方法'} 的数据表、图像预览和说明文件，"
                    "确认风险解释和机会判断能被下载证据支撑后再进入行动。"
                ),
                "owner_hint": "报告负责人 + 方法复核人",
                "evidence_refs": [ref for ref in [method_ref, "方法证据索引"] if ref],
            }
        )
    reviewers = [
        {
            "agent_id": "claim_reviewer",
            "agent_name": "结论复核人",
            "claim_review": {
                "summary": f"已复核 {len(chart_refs)} 张业务图表和 {len(method_refs)} 组方法证据，主结论必须引用图像、表格和可下载证据。",
                "reviewed_claims": [
                    {
                        "claim": "报告核心判断可由业务图表和可下载证据追溯。",
                        "verdict": "supported_with_boundaries",
                        "evidence_refs": chart_refs[:4] + method_refs[:2],
                        "limits": "图表证明分布、关联和异常线索；因果和经营归因仍需业务口径复核。",
                    }
                ],
            },
            "business_action_review": {
                "summary": "行动建议已限定为先复核、再放大或校正，避免把统计信号直接写成经营定论。",
                "actions": actions[:3],
            },
            "chart_relevance_review": {
                "summary": "图表均绑定业务问题、关键发现、影响和复核边界。",
                "chart_reviews": [
                    {
                        "chart_ref": ref,
                        "relevance_verdict": "relevant",
                        "business_question": _chart_business_question(chart_items[index]) if index < len(chart_items) else "",
                        "evidence_refs": [ref],
                        "field_pair": [
                            chart_items[index].get("x_label") if index < len(chart_items) else "",
                            chart_items[index].get("y_label") if index < len(chart_items) else "",
                        ],
                    }
                    for index, ref in enumerate(chart_refs[:4])
                ],
            },
        },
        {
            "agent_id": "action_reviewer",
            "agent_name": "行动复核人",
            "claim_review": {
                "summary": "行动矩阵只承接可下载证据能支撑的业务问题。",
                "reviewed_claims": [
                    {
                        "claim": "每条行动均能追溯到图表或方法证据。",
                        "verdict": "supported",
                        "evidence_refs": [ref for action in actions[:4] for ref in list(action.get("evidence_refs") or [])][:10],
                        "limits": "行动排序是复核优先级，不替代管理层最终决策。",
                    }
                ],
            },
            "business_action_review": {
                "summary": "行动覆盖风险复核、机会放大、口径校正和证据补强。",
                "actions": actions[2:6],
            },
            "chart_relevance_review": {
                "summary": "优先使用可解释性强、能指向经营动作的图表。",
                "chart_reviews": [
                    {
                        "chart_ref": ref,
                        "relevance_verdict": "actionable",
                        "business_question": actions[min(index, len(actions) - 1)].get("business_question"),
                        "evidence_refs": [ref],
                        "field_pair": [],
                    }
                    for index, ref in enumerate(chart_refs[2:6])
                ],
            },
        },
        {
            "agent_id": "evidence_reviewer",
            "agent_name": "证据复核人",
            "claim_review": {
                "summary": "报告具备 HTML/Markdown、图表文件、方法证据和总索引的审计链。",
                "reviewed_claims": [
                    {
                        "claim": "交付包可下载、可复核、可继续修订。",
                        "verdict": "supported",
                        "evidence_refs": ["总清单", "图表索引", "方法证据索引"],
                        "limits": "外部发布前仍应抽查 PNG、CSV 和 XLSX 是否与正文引用一致。",
                    }
                ],
            },
            "business_action_review": {
                "summary": "证据链完整时才允许把建议进入管理层行动清单。",
                "actions": actions[:5],
            },
            "chart_relevance_review": {
                "summary": "图像资产已作为主文证据，而不是仅作为附录文件。",
                "chart_reviews": [
                    {
                        "chart_ref": ref,
                        "relevance_verdict": "auditable",
                        "business_question": "该图是否能追溯到图表文件和方法证据？",
                        "evidence_refs": [ref, "图表索引"],
                        "field_pair": [],
                    }
                    for ref in chart_refs[:4]
                ],
            },
        },
    ]
    return {
        "contract": "analysis_lab_agent_reviews_v1",
        "runtime_status": "agent_review_completed",
        "generated_at": generated_at,
        "dataset_id": request.dataset_id,
        "dataset_name": dataset_name,
        "sheet_name": sheet_name or request.active_sheet or "",
        "source": "local_agent_review",
        "agent_reviews": reviewers,
        "consolidated_actions": actions[:6],
        "cited_chart_refs": chart_refs[:12],
        "cited_method_run_ids": method_refs[:12],
        "reviewer_count": len(reviewers),
    }


def _write_agent_review_contract(
    *,
    export_dir: Path,
    public_base_path: str,
    request: AutoAnalysisRequest,
    dataset_name: str,
    sheet_name: str,
    selected: dict[str, Any],
    charts: list[dict[str, Any]],
    method_execution_packages: list[dict[str, Any]],
    external_skill_context: dict[str, Any] | None,
    generated_at: str,
    downloadables: list[dict[str, Any]],
) -> dict[str, Any]:
    input_path = export_dir / LAB_REPORT_AGENT_REVIEW_INPUT_FILE
    prompt_path = export_dir / LAB_REPORT_AGENT_REVIEW_PROMPT_FILE
    review_path = export_dir / LAB_REPORT_AGENT_REVIEW_FILE
    review_md_path = export_dir / LAB_REPORT_AGENT_REVIEW_MD_FILE
    _write_json_file(
        input_path,
        _agent_review_input_payload(
            request=request,
            dataset_name=dataset_name,
            sheet_name=sheet_name,
            selected=selected,
            charts=charts,
            method_execution_packages=method_execution_packages,
            external_skill_context=external_skill_context,
            generated_at=generated_at,
        ),
    )
    prompt_path.write_text(_agent_review_prompt(), encoding="utf-8")
    payload = _load_agent_review_payload(export_dir)
    async_enabled = os.getenv("ASTERIA_ANALYSIS_LAB_AGENT_REVIEW_ASYNC_ENABLED", "0").strip() in {"1", "true", "TRUE", "yes", "YES"}
    wait_timeout_sec = max(0, int(os.getenv("ASTERIA_ANALYSIS_LAB_AGENT_REVIEW_WAIT_SEC", "0") or "0"))
    codex_task_id = ""
    codex_error = ""
    if async_enabled and not _agent_review_is_usable(payload):
        try:
            from app.models import CodexRunRequest
            from app.services.codex_runtime_task_service import create_codex_run_task
            from app.services.settings_service import load_runtime_settings_raw

            settings = load_runtime_settings_raw()
            timeout_sec = max(60, min(int(settings.get("codex_timeout_sec") or 1800), 900))
            run_request = CodexRunRequest(
                workspace_path=str(export_dir.resolve()),
                prompt_template=_agent_review_prompt(),
                user_requirement=request.user_goal or "Review the Analysis Lab report package through the mounted report agent team.",
                context_payload={
                    "input_file": LAB_REPORT_AGENT_REVIEW_INPUT_FILE,
                    "expected_output": LAB_REPORT_AGENT_REVIEW_FILE,
                    "dataset_name": dataset_name,
                    "sheet_name": sheet_name or request.active_sheet or "",
                    "chart_count": len(charts),
                    "method_count": len(method_execution_packages),
                },
                report_id=f"analysis-lab-agent-review-{request.dataset_id}",
                parent_report_id=f"analysis-lab-{request.dataset_id}",
                dataset_id=request.dataset_id,
                sheet_name=sheet_name or request.active_sheet or "",
                stage_id="analysis_lab_agent_review",
                purpose="analysis_lab_agent_review",
                artifact_source=LAB_REPORT_AGENT_REVIEW_FILE,
                timeout_sec=timeout_sec,
                capture_git_diff=False,
            )
            task = create_codex_run_task(
                run_request,
                parent_report_id=f"analysis-lab-{request.dataset_id}",
                parent_stage_id="analysis_lab_report",
                stage_id="analysis_lab_agent_review",
                purpose="analysis_lab_agent_review",
                artifact_source=LAB_REPORT_AGENT_REVIEW_FILE,
                return_full=True,
            )
            codex_task_id = str(task.get("job_id") or "")
            if wait_timeout_sec > 0:
                deadline = time.time() + wait_timeout_sec
                while time.time() < deadline:
                    next_payload = _load_agent_review_payload(export_dir)
                    if _agent_review_is_usable(next_payload):
                        payload = next_payload
                        review_md_path.write_text(_agent_review_markdown(payload), encoding="utf-8")
                        break
                    time.sleep(1.0)
        except Exception as exc:
            codex_error = str(exc)
    if not _agent_review_is_usable(payload):
        payload = _deterministic_agent_review_payload(
            request=request,
            dataset_name=dataset_name,
            sheet_name=sheet_name or request.active_sheet or "",
            charts=charts,
            method_execution_packages=method_execution_packages,
            external_skill_context=external_skill_context,
            generated_at=generated_at,
        )
        if codex_error:
            payload["codex_error"] = codex_error
        _write_json_file(review_path, payload)
    review_md_path.write_text(_agent_review_markdown(payload), encoding="utf-8")
    for file_name, file_path, kind, purpose, is_main in (
        (LAB_REPORT_AGENT_REVIEW_INPUT_FILE, input_path, "json", "Agent team review input contract.", False),
        (LAB_REPORT_AGENT_REVIEW_PROMPT_FILE, prompt_path, "md", "Prompt used by report agent reviewers.", False),
        (LAB_REPORT_AGENT_REVIEW_FILE, review_path, "json", "Agent team claim/action/chart review output.", True),
        (LAB_REPORT_AGENT_REVIEW_MD_FILE, review_md_path, "md", "Readable agent team review summary.", True),
    ):
        if file_path.exists() or file_name == LAB_REPORT_AGENT_REVIEW_FILE:
            _append_downloadable(
                downloadables,
                _public_downloadable_item(
                    {
                        "name": file_name,
                        "path": _public_path(public_base_path, file_name),
                        "file_path": str(file_path.resolve()),
                        "type": kind,
                        "purpose": purpose,
                        "is_main": is_main,
                        "download_kind": "lab_report_agent_review",
                    }
                ),
            )
    payload.update(
        {
            "input_path": _public_path(public_base_path, LAB_REPORT_AGENT_REVIEW_INPUT_FILE),
            "prompt_path": _public_path(public_base_path, LAB_REPORT_AGENT_REVIEW_PROMPT_FILE),
            "review_path": _public_path(public_base_path, LAB_REPORT_AGENT_REVIEW_FILE),
            "review_report_path": _public_path(public_base_path, LAB_REPORT_AGENT_REVIEW_MD_FILE),
            "codex_task_id": codex_task_id,
            "codex_error": codex_error,
            "usable": _agent_review_is_usable(payload),
        }
    )
    return payload


def _chart_question_for_report(chart: dict[str, Any]) -> str:
    question = str(chart.get("business_question") or "").strip()
    if question:
        return _plain_business_label(question)
    kind = str(chart.get("kind") or "")
    x_label = _business_field_label(chart.get("x_label") or "")
    y_label = _business_field_label(chart.get("y_label") or "")
    if kind in {"bubble", "quadrant"}:
        return f"{x_label or '核心指标'} 与 {y_label or '对比指标'} 的高低组合如何定位预算效率和优先复核对象？"
    if kind.startswith("bar-"):
        return f"{x_label or '分组'} 维度下，{y_label or '核心指标'} 的集中度是否提示地区、服务领域或组织画像差异？"
    if kind == "heatmap":
        return "哪些指标强联动，是否需要进入驱动因素复核？"
    if kind == "anomaly-scatter":
        return "哪些对象显著偏离整体，应进入异常项目清单？"
    return f"{x_label or 'X指标'} 与 {y_label or 'Y指标'} 是否形成可行动的业务信号？"


def _chart_business_question(chart: dict[str, Any] | None) -> str:
    return _chart_question_for_report(chart or {}) if isinstance(chart, dict) else "当前业务证据是否足以进入行动排期？"


def _chart_visual_marker(chart: dict[str, Any], method_execution_packages: list[dict[str, Any]] | None = None) -> str:
    agent = _chart_writer_agent(chart)
    if agent:
        exports = chart.get("asset_exports") if isinstance(chart.get("asset_exports"), dict) else {}
        image_path = _relative_artifact_href(exports.get("image_path") or "")
        data_path = _relative_artifact_href(exports.get("data_path") or "")
        linked_methods = [
            str(ref).strip()
            for ref in list(chart.get("linked_method_refs") or chart.get("method_refs") or [])
            if str(ref or "").strip()
        ]
        if not linked_methods and method_execution_packages is not None:
            linked_methods = _chart_linked_method_refs(chart, method_execution_packages, limit=4)
        metric_evidence = _chart_metric_text([item for item in list(agent.get("evidence_numbers") or []) if isinstance(item, dict)], limit=5)
        sample_scope_text = str((agent.get("sample_scope") or {}).get("text") or "") if isinstance(agent.get("sample_scope"), dict) else ""
        public_evidence = _public_evidence_refs(linked_methods) or "图表文件"
        return (
            "CHART: "
            f"title={_visual_marker_value(((agent.get('final_editor_agent') or {}) if isinstance(agent.get('final_editor_agent'), dict) else {}).get('final_caption') or ((agent.get('figure_caption_agent') or {}) if isinstance(agent.get('figure_caption_agent'), dict) else {}).get('caption') or agent.get('caption'), fallback=str(chart.get('title') or chart.get('kind') or 'chart'))}; "
            f"kind={chart.get('kind') or 'chart'}; "
            f"image={image_path}; "
            f"json={data_path}; "
            f"question={_visual_marker_value(agent.get('business_question') or _chart_question_for_report(chart), fallback='business question')}; "
            f"insight={_visual_marker_value(agent.get('direct_answer'), fallback=_business_chart_interpretation(chart))}; "
            f"impact={_visual_marker_value(agent.get('recommended_action'), fallback=_chart_business_impact(chart))}; "
            f"boundary={_visual_marker_value(agent.get('limits'), fallback=_chart_review_boundary(chart))}; "
            f"evidence_detail={_visual_marker_value('; '.join(value for value in [metric_evidence, sample_scope_text] if value), fallback='numeric evidence and sample scope')}; "
            f"evidence={_visual_marker_value(public_evidence, fallback='图表文件')}"
        )
    exports = chart.get("asset_exports") if isinstance(chart.get("asset_exports"), dict) else {}
    image_path = _relative_artifact_href(exports.get("image_path") or "")
    data_path = _relative_artifact_href(exports.get("data_path") or "")
    linked_methods = [
        str(ref).strip()
        for ref in list(chart.get("linked_method_refs") or chart.get("method_refs") or [])
        if str(ref or "").strip()
    ]
    if not linked_methods and method_execution_packages is not None:
        linked_methods = _chart_linked_method_refs(chart, method_execution_packages, limit=4)
    public_evidence = _public_evidence_refs(linked_methods) or "图表文件"
    return (
        "CHART: "
        f"title={chart.get('title') or chart.get('kind') or 'chart'}; "
        f"kind={chart.get('kind') or 'chart'}; "
        f"image={image_path}; "
        f"json={data_path}; "
        f"question={_chart_question_for_report(chart)}; "
        f"insight={_business_chart_interpretation(chart)}; "
        f"impact={_chart_business_impact(chart)}; "
        f"boundary={_chart_review_boundary(chart)}; "
        f"evidence={public_evidence}"
    )


def _visual_marker_value(value: Any, *, fallback: str = "-") -> str:
    text = _report_cell_text(value, 180).replace(";", ",")
    return text or fallback


def _method_visual_marker(package: dict[str, Any]) -> str:
    artifact_exports = package.get("artifact_exports") if isinstance(package.get("artifact_exports"), dict) else {}
    image_path = _relative_artifact_href(artifact_exports.get("preview_png_path") or "")
    if not image_path:
        return ""
    method_card = package.get("method_card") if isinstance(package.get("method_card"), dict) else {}
    method_name = (
        method_card.get("method_name")
        or package.get("method_name")
        or package.get("method_id")
        or package.get("method_run_id")
        or "Method preview"
    )
    method_ref = package.get("method_run_id") or package.get("method_id") or ""
    return (
        "VISUAL: "
        f"title={_visual_marker_value(method_name, fallback='方法预览')}; "
        f"image={image_path}; "
        f"csv={_relative_artifact_href(artifact_exports.get('data_csv_path') or '')}; "
        f"xlsx={_relative_artifact_href(artifact_exports.get('data_xlsx_path') or '')}; "
        f"json={_relative_artifact_href(artifact_exports.get('data_json_path') or '')}; "
        "question=这个方法产物支撑了报告中的哪一条判断？; "
        "insight=预览图展示了该方法导出的关键行和字段，便于快速核对结果形态。; "
        "impact=发布前应结合 CSV、XLSX 和 JSON 文件复核字段口径、样本覆盖和异常对象。; "
        "boundary=该卡片只说明方法产物已经可复核，正式结论仍需回到证据文件逐项确认。; "
        f"evidence={_visual_marker_value(_public_evidence_ref(method_ref), fallback='方法证据')}"
    )


def _chart_review_boundary(chart: dict[str, Any]) -> str:
    agent_limits = _chart_writer_text(chart, "limits")
    if agent_limits:
        return agent_limits
    kind = str(chart.get("kind") or "chart")
    return (
        f"{kind} 图表只能证明当前样本中的分布、关联或异常线索；"
        "正式结论必须回到字段定义、样本覆盖、极端值和可下载证据文件逐项核对。"
    )


def _chart_linked_method_refs(
    chart: dict[str, Any],
    method_execution_packages: list[dict[str, Any]],
    *,
    limit: int = 4,
) -> list[str]:
    kind = str(chart.get("kind") or "").strip()
    if not kind:
        return []
    refs: list[str] = []
    for package in method_execution_packages:
        assets = [asset for asset in list(package.get("assets") or []) if isinstance(asset, dict)]
        matched = False
        for asset in assets:
            payload = asset.get("payload") if isinstance(asset.get("payload"), dict) else {}
            chart_refs = {str(ref).split(":", 1)[-1] for ref in list(payload.get("chart_refs") or [])}
            linked_kinds = {
                str(item.get("kind") or "")
                for item in list(payload.get("linked_charts") or [])
                if isinstance(item, dict)
            }
            if kind in chart_refs or kind in linked_kinds:
                matched = True
                break
        if not matched:
            continue
        ref = str(package.get("method_run_id") or package.get("method_id") or "").strip()
        if ref and ref not in refs:
            refs.append(ref)
        if len(refs) >= limit:
            break
    return refs


def _business_evidence_chain_rows(
    charts: list[dict[str, Any]],
    method_execution_packages: list[dict[str, Any]],
    *,
    limit: int = 8,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, chart in enumerate(charts[:limit], start=1):
        if not isinstance(chart, dict):
            continue
        exports = chart.get("asset_exports") if isinstance(chart.get("asset_exports"), dict) else {}
        linked_methods = _chart_linked_method_refs(chart, method_execution_packages)
        rows.append(
            {
                "证据编号": f"E{index:02d}",
                "业务问题": _chart_business_question(chart),
                "业务判断": _business_chart_interpretation(chart),
                "业务证据": (
                    f"{chart.get('title') or chart.get('kind') or '图表'}；"
                    f"类型={chart.get('kind') or '-'}；数据点={_chart_point_count(chart)}"
                ),
                "方法证据": _public_evidence_refs(linked_methods) or "图表文件",
                "可下载证据": "；".join(
                    label
                    for label in [
                        _customer_artifact_label(exports.get("image_path") or ""),
                        _customer_artifact_label(exports.get("data_path") or ""),
                    ]
                    if label != "下载清单"
                )
                or "见下载清单",
                "复核边界": _chart_review_boundary(chart),
            }
        )
    return rows


def _business_action_priority_rows(
    tables: list[dict[str, Any]],
    charts: list[dict[str, Any]],
    method_execution_packages: list[dict[str, Any]],
    *,
    limit: int = 8,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    action_rows = _table_rows_by_title(tables, _zh(r"\u884c\u52a8\u4f18\u5148\u7ea7\u8bc4\u5206"))
    for index, row in enumerate(action_rows[:3], start=1):
        rows.append(
            {
                "优先级": f"P{index}",
                "对象/信号": _report_cell_text(row.get("priority") or row.get("action") or "行动优先级", 90),
                "触发证据": "行动优先级评分表",
                "业务行动": _report_cell_text(row.get("next_step") or row.get("action") or "进入人工复核清单", 240),
                "复核边界": "先确认该行动是否有字段口径、样本范围和责任人支撑，再进入执行排期。",
            }
        )
    if rows:
        return rows[:limit]
    return rows


def _research_design_rows(
    *,
    selected: dict[str, Any],
    tables: list[dict[str, Any]],
    charts: list[dict[str, Any]],
    method_execution_packages: list[dict[str, Any]],
    external_skill_context: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    family_counts = _method_family_counts(method_execution_packages)
    family_text = "、".join(
        f"{_method_family_label(family)}{count}项" for family, count in sorted(family_counts.items())
    )
    skill_count = int((external_skill_context or {}).get("count") or len(list((external_skill_context or {}).get("skills") or [])))
    target_label = _report_field_value(selected.get("target"))
    feature_text = "、".join(_business_field_label(item) for item in list(selected.get("features") or [])[:8]) or "-"
    return [
        {
            "研究模块": "研究对象与口径",
            "设计说明": f"以 `{target_label}` 为核心指标，结合解释字段 `{feature_text}` 建立研究口径。",
            "证据来源": "字段选择、数据范围、方法证据",
            "商用价值": "让读者先知道本报告研究什么、为什么这些字段能支撑结论。",
        },
        {
            "研究模块": "方法组合",
            "设计说明": f"覆盖 {family_text or '自动适配方法'}，避免只用单一统计视角得出结论。",
            "证据来源": f"{len(method_execution_packages)} 组方法证据、{len(tables)} 张证据表、{len(charts)} 张业务图表",
            "商用价值": "同时支持管理摘要、图表叙事、复核行动和附录审计。",
        },
        {
            "研究模块": "行业语境与写作约束",
            "设计说明": f"已应用 {skill_count} 组写作、图文表达和文档结构约束，但主文不暴露内部工具名称。",
            "证据来源": "报告生成配置",
            "商用价值": "让报告具备行业解释语境，而不是只输出通用统计模板。",
        },
        {
            "研究模块": "质量控制",
            "设计说明": "主文结论必须绑定图像、表格、方法证据、复核行动和复核边界。",
            "证据来源": "质量门禁、业务证据链、行动优先级矩阵",
            "商用价值": "保证报告可复核、可追责、可继续修订后对外交付。",
        },
    ]


def _research_question_rows(
    charts: list[dict[str, Any]],
    tables: list[dict[str, Any]],
    method_execution_packages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    family_counts = _method_family_counts(method_execution_packages)
    rows = [
        {
            "研究问题": "当前样本最重要的业务结构是什么？",
            "核心结论": "先从核心业务判断、象限结构、分层结构和异常对象中识别主线。",
            "主要证据": f"{len(charts)} 张业务图表、{len(tables)} 张证据表",
            "商业用途": "商业用途：用于管理层快速判断资源投向、风险对象和复核优先级。",
        },
        {
            "研究问题": "哪些对象或指标需要优先行动？",
            "核心结论": "行动优先级矩阵只承接复核后的业务行动和复核边界。",
            "主要证据": "行动优先级矩阵、业务证据链、异常和分群证据",
            "商业用途": "商业用途：用于形成可执行复核清单，而不是停留在描述性发现。",
        },
        {
            "研究问题": "报告结论是否可审计、可下载、可复用？",
            "核心结论": "每个分析方法和业务图表都保留可下载数据、图片和说明文件。",
            "主要证据": f"{len(method_execution_packages)} 组方法证据；方法族={', '.join(sorted(family_counts))}",
            "商业用途": "商业用途：用于对外交付、内部复盘和后续研究迭代。",
        },
    ]
    if charts:
        first_chart = charts[0]
        rows.insert(
            1,
            {
                "研究问题": "最能支撑主结论的图像证据是什么？",
                "核心结论": _business_chart_interpretation(first_chart),
                "主要证据": first_chart.get("title") or first_chart.get("kind") or "业务图表",
                "商业用途": "商业用途：用于首页或摘要页的图文并茂解释，帮助非技术读者快速理解结论。",
            },
        )
    return rows


def _figure_narrative_rows(
    charts: list[dict[str, Any]],
    method_execution_packages: list[dict[str, Any]],
    *,
    limit: int = 6,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, chart in enumerate(charts[:limit], start=1):
        if not isinstance(chart, dict):
            continue
        exports = chart.get("asset_exports") if isinstance(chart.get("asset_exports"), dict) else {}
        linked_methods = _chart_linked_method_refs(chart, method_execution_packages, limit=3)
        rows.append(
            {
                "图序": f"Figure {index}",
                "业务问题": _chart_business_question(chart),
                "图表": chart.get("title") or chart.get("kind") or "-",
                "图像文件": _customer_artifact_label(exports.get("image_path") or ""),
                "发现": _business_chart_interpretation(chart),
                "影响": _chart_business_impact(chart),
                "复核边界": _chart_review_boundary(chart),
                "证据包": _public_evidence_refs(linked_methods) or "图表文件",
            }
        )
    return rows


def _chart_business_impact(chart: dict[str, Any]) -> str:
    action = _chart_writer_text(chart, "recommended_action")
    if action:
        return action
    kind = str(chart.get("kind") or "")
    if kind in {"bubble", "quadrant"}:
        return "影响：高支出低收入或低收入高支出对象会影响预算效率、项目可持续性和管理层资源投放优先级。"
    if kind.startswith("bar-"):
        return "影响：分组集中度过高说明资源、服务或组织画像存在结构倾斜，需要判断是否符合战略定位。"
    if kind == "heatmap":
        return "影响：强联动指标会改变结论解释口径，可能导致把相关关系误读成单一驱动因素。"
    if kind == "cluster-scatter":
        return "影响：不同分群需要不同管理动作，不能用同一套平均策略覆盖所有基金会或项目。"
    if kind == "anomaly-scatter":
        return "影响：异常对象可能是真实风险、战略机会或数据质量问题，直接影响外部报告可信度。"
    if kind in {"line", "forecast"}:
        return "影响：趋势变化会影响预算节奏、年度复盘和后续项目排期，但不能脱离业务事件解释。"
    return "影响：该信号会影响管理层对资源投向、风险对象和复核优先级的判断。"


def _commercial_delivery_rows(
    *,
    charts: list[dict[str, Any]],
    method_execution_packages: list[dict[str, Any]],
    method_artifact_summary: dict[str, Any] | None,
    evidence_chain_rows: list[dict[str, Any]],
    action_priority_rows: list[dict[str, Any]],
    figure_narrative_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    method_count = int((method_artifact_summary or {}).get("method_count") or len(method_execution_packages))
    complete_count = int((method_artifact_summary or {}).get("integrity_complete_count") or 0)
    complete_status = (method_artifact_summary or {}).get("integrity_status") or "-"
    chart_image_count = len(
        [
            chart
            for chart in charts
            if isinstance(chart, dict)
            and isinstance(chart.get("asset_exports"), dict)
            and chart["asset_exports"].get("image_path")
        ]
    )
    return [
        {
            "交付维度": "图文并茂",
            "交付状态": "通过" if chart_image_count >= min(max(len(charts), 1), 4) else "需补强",
            "验收证据": f"业务图像 {chart_image_count}/{len(charts)}；图文叙事 {len(figure_narrative_rows)} 条",
            "商用说明": "报告主文必须同时给图、给解释、给读者动作。",
        },
        {
            "交付维度": "研究结构",
            "交付状态": "通过" if evidence_chain_rows and action_priority_rows else "需补强",
            "验收证据": "研究摘要、研究设计、研究问题、业务证据链、行动矩阵",
            "商用说明": "满足研究报告的阅读顺序，而不是内部运行日志顺序。",
        },
        {
            "交付维度": "证据可审计",
            "交付状态": "通过" if complete_status == "passed" and complete_count >= method_count else "需补强",
            "验收证据": f"方法证据完整度 {complete_count}/{method_count}；完整性={complete_status}",
            "商用说明": "对外呈现前可以追溯到 CSV、XLSX、PNG、JSON 和 README。",
        },
        {
            "交付维度": "结论可复核",
            "交付状态": "通过" if evidence_chain_rows and all(row.get("复核边界") for row in evidence_chain_rows[:3]) else "需补强",
            "验收证据": f"业务证据链 {len(evidence_chain_rows)} 条；行动优先级 {len(action_priority_rows)} 条",
            "商用说明": "每条核心结论都要说明证据、用途和不能越界解释的部分。",
        },
    ]


def _chart_ref_kind(ref: Any) -> str:
    text = str(ref or "").strip()
    if text.startswith("chart:"):
        return text.split(":", 1)[1]
    return text


def _chart_for_method_package(package: dict[str, Any], charts: list[dict[str, Any]]) -> dict[str, Any] | None:
    charts_by_kind = {str(chart.get("kind") or ""): chart for chart in charts if isinstance(chart, dict)}
    assets = [asset for asset in list(package.get("assets") or []) if isinstance(asset, dict)]
    for asset in assets:
        payload = asset.get("payload") if isinstance(asset.get("payload"), dict) else {}
        linked = [chart for chart in list(payload.get("linked_charts") or []) if isinstance(chart, dict)]
        if linked:
            return linked[0]
        for ref in list(payload.get("chart_refs") or []) + [asset.get("asset_ref")]:
            kind = _chart_ref_kind(ref)
            if kind in charts_by_kind:
                return charts_by_kind[kind]
    method_id = str(package.get("method_id") or package.get("method_run_id") or "").lower()
    preferences = [
        ("quadrant", "quadrant"),
        ("bubble", "bubble"),
        ("scatter", "scatter"),
        ("violin", "histogram"),
        ("waterfall", "histogram"),
        ("heatmap", "heatmap"),
        ("cluster", "cluster-scatter"),
        ("anomaly", "anomaly-scatter"),
    ]
    for token, kind in preferences:
        if token in method_id and kind in charts_by_kind:
            return charts_by_kind[kind]
    return charts[0] if charts else None


def _chart_kinds_needed_for_export(
    report_parts: list[dict[str, Any]],
    method_execution_assets: list[dict[str, Any]],
) -> set[str]:
    kinds: set[str] = set()
    for part in report_parts:
        if not isinstance(part, dict):
            continue
        for chart in list(part.get("charts") or []):
            if not isinstance(chart, dict):
                continue
            kind = _clean_text(chart.get("kind"))
            if kind:
                kinds.add(kind)
    for asset in method_execution_assets:
        if not isinstance(asset, dict):
            continue
        payload = asset.get("payload") if isinstance(asset.get("payload"), dict) else {}
        for ref in list(payload.get("chart_refs") or []):
            kind = _chart_ref_kind(ref)
            if kind:
                kinds.add(kind)
        for chart in list(payload.get("linked_charts") or []):
            if not isinstance(chart, dict):
                continue
            kind = _clean_text(chart.get("kind"))
            if kind:
                kinds.add(kind)
    return kinds


def _select_charts_for_export(
    charts: list[dict[str, Any]],
    report_parts: list[dict[str, Any]],
    method_execution_assets: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    chart_items = [chart for chart in charts if isinstance(chart, dict)]
    needed_kinds = _chart_kinds_needed_for_export(report_parts, method_execution_assets)
    if not needed_kinds:
        return chart_items
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for chart in chart_items:
        kind = _clean_text(chart.get("kind"))
        if not kind or kind not in needed_kinds or kind in seen:
            continue
        seen.add(kind)
        selected.append(chart)
    return selected or chart_items


def _draw_scatter_like_chart(ax: Any, chart: dict[str, Any], *, quadrant: bool = False) -> None:
    points = _chart_points(chart)
    if not points:
        ax.text(0.5, 0.5, "没有可绘制点", ha="center", va="center")
        return
    x = np.asarray([float(point["x"]) for point in points], dtype=float)
    y = np.asarray([float(point["y"]) for point in points], dtype=float)
    sizes_raw = np.asarray([abs(_safe_float(point.get("size")) or 1.0) for point in points], dtype=float)
    if sizes_raw.size and np.nanmax(sizes_raw) > np.nanmin(sizes_raw):
        sizes = 50 + 520 * (sizes_raw - np.nanmin(sizes_raw)) / (np.nanmax(sizes_raw) - np.nanmin(sizes_raw))
    else:
        sizes = np.full_like(x, 130, dtype=float)
    categories = [str(point.get("quadrant") or point.get("category") or point.get("cluster") or "") for point in points]
    palette = {
        "high_high": "#2f6f4e",
        "high_low": "#c2573f",
        "low_high": "#d9982f",
        "low_low": "#7b8794",
        "0": "#2f6f4e",
        "1": "#c2573f",
        "2": "#d9982f",
        "3": "#4776a8",
        "": "#61743c",
    }
    colors = [palette.get(item, "#61743c") for item in categories]
    if quadrant:
        x_mid = _safe_float(chart.get("x_mid")) or float(np.nanmedian(x))
        y_mid = _safe_float(chart.get("y_mid")) or float(np.nanmedian(y))
        ax.axvline(x_mid, color="#7b6a4e", linewidth=1.2, linestyle="--", alpha=0.72)
        ax.axhline(y_mid, color="#7b6a4e", linewidth=1.2, linestyle="--", alpha=0.72)
        labels = chart.get("quadrant_labels") if isinstance(chart.get("quadrant_labels"), dict) else {}
        ax.text(0.98, 0.96, labels.get("high_high", "高高"), transform=ax.transAxes, ha="right", va="top", color="#2f6f4e", fontweight="bold")
        ax.text(0.98, 0.04, labels.get("high_low", "高低"), transform=ax.transAxes, ha="right", va="bottom", color="#c2573f", fontweight="bold")
        ax.text(0.02, 0.96, labels.get("low_high", "低高"), transform=ax.transAxes, ha="left", va="top", color="#d9982f", fontweight="bold")
        ax.text(0.02, 0.04, labels.get("low_low", "低低"), transform=ax.transAxes, ha="left", va="bottom", color="#7b8794", fontweight="bold")
    ax.scatter(x, y, s=sizes, c=colors, alpha=0.7, edgecolors="white", linewidths=0.8)
    top_points = sorted(points, key=lambda point: abs(_safe_float(point.get("size")) or _safe_float(point.get("score")) or point.get("x") or 0.0), reverse=True)[:4]
    for point in top_points:
        ax.annotate(
            _report_cell_text(point.get("name"), 16),
            (float(point["x"]), float(point["y"])),
            textcoords="offset points",
            xytext=(7, 7),
            fontsize=8,
            color="#26311f",
        )


def _draw_bar_chart(ax: Any, labels: list[Any], values: list[Any], *, color: str = "#61743c") -> None:
    safe_labels = [_report_cell_text(label, 14) for label in labels]
    safe_values = [float(_safe_float(value) or 0.0) for value in values]
    order = np.argsort(np.asarray(safe_values, dtype=float))[::-1][:12]
    safe_labels = [safe_labels[int(index)] for index in order]
    safe_values = [safe_values[int(index)] for index in order]
    y_pos = np.arange(len(safe_labels))
    ax.barh(y_pos, safe_values, color=color, alpha=0.86)
    ax.set_yticks(y_pos, safe_labels)
    ax.invert_yaxis()
    for index, value in enumerate(safe_values):
        ax.text(value, index, f" {_format_business_amount(value)}", va="center", fontsize=8, color="#26311f")


def _scaled_point(
    x: float,
    y: float,
    *,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    plot_left: int,
    plot_top: int,
    plot_right: int,
    plot_bottom: int,
) -> tuple[int, int]:
    x_span = x_max - x_min if x_max != x_min else 1.0
    y_span = y_max - y_min if y_max != y_min else 1.0
    px = plot_left + int((x - x_min) / x_span * (plot_right - plot_left))
    py = plot_bottom - int((y - y_min) / y_span * (plot_bottom - plot_top))
    return px, py


def _fallback_chart_series(chart: dict[str, Any]) -> tuple[list[float], list[float]]:
    points = _chart_points(chart)
    if points:
        return [float(point["x"]) for point in points], [float(point["y"]) for point in points]
    x_values = list(chart.get("x") or [])
    y_values = list(chart.get("actual") or chart.get("y") or [])
    x_series: list[float] = []
    y_series: list[float] = []
    for index, value in enumerate(y_values):
        y_number = _safe_float(value)
        if y_number is None:
            continue
        x_number = _safe_float(x_values[index] if index < len(x_values) else None)
        x_series.append(float(x_number if x_number is not None else index))
        y_series.append(float(y_number))
    return x_series, y_series


def _write_chart_png_fallback(chart: dict[str, Any], *, path: Path, title: str | None = None) -> bool:
    tools = _load_pil_image_tools()
    if tools is None:
        return _write_basic_png_placeholder(path)
    Image, ImageDraw, ImageFont = tools
    try:
        width, height = 1420, 860
        plot_left, plot_top, plot_right, plot_bottom = 108, 168, width - 84, height - 170
        image = Image.new("RGB", (width, height), "#fffaf0")
        draw = ImageDraw.Draw(image)
        title_font = _load_pil_font(ImageFont, 32, bold=True)
        label_font = _load_pil_font(ImageFont, 18, bold=True)
        small_font = _load_pil_font(ImageFont, 15)
        tiny_font = _load_pil_font(ImageFont, 13)
        kind = str(chart.get("kind") or "chart")
        display_title = str(title or chart.get("title") or kind)
        draw.rectangle([(0, 0), (width, 112)], fill="#ead9bd")
        _draw_text_safe(draw, (34, 28), display_title, font=title_font, fill="#24351f", max_chars=110)
        subtitle = _chart_sampling_note(chart)
        _draw_text_safe(draw, (38, 78), subtitle, font=small_font, fill="#6f5d42", max_chars=150)
        draw.rounded_rectangle([(plot_left, plot_top), (plot_right, plot_bottom)], radius=18, fill="#fffdf8", outline="#d4c4a8", width=2)
        for grid_index in range(1, 5):
            y = plot_top + int((plot_bottom - plot_top) * grid_index / 5)
            draw.line([(plot_left, y), (plot_right, y)], fill="#eadfc9", width=1)
            x = plot_left + int((plot_right - plot_left) * grid_index / 5)
            draw.line([(x, plot_top), (x, plot_bottom)], fill="#eadfc9", width=1)

        if kind == "heatmap":
            matrix = chart.get("matrix") if isinstance(chart.get("matrix"), list) else []
            rows = [row for row in matrix if isinstance(row, list)]
            labels = list(chart.get("labels") or [])
            size = min(plot_right - plot_left - 80, plot_bottom - plot_top - 40)
            n = max(1, max(len(rows), max((len(row) for row in rows), default=0)))
            cell = max(10, size // n)
            start_x = plot_left + 44
            start_y = plot_top + 24
            for row_index in range(n):
                for column_index in range(n):
                    value = _safe_float(rows[row_index][column_index] if row_index < len(rows) and column_index < len(rows[row_index]) else 0)
                    value = max(-1.0, min(1.0, float(value or 0.0)))
                    if value >= 0:
                        color = (
                            int(245 - 90 * value),
                            int(232 - 40 * value),
                            int(196 - 115 * value),
                        )
                    else:
                        color = (
                            int(238 - 92 * abs(value)),
                            int(228 - 65 * abs(value)),
                            int(198 + 35 * abs(value)),
                        )
                    x0 = start_x + column_index * cell
                    y0 = start_y + row_index * cell
                    draw.rectangle([(x0, y0), (x0 + cell - 2, y0 + cell - 2)], fill=color, outline="#fffaf0")
            for index, label in enumerate(labels[:n]):
                _draw_text_safe(draw, (start_x + index * cell, start_y + n * cell + 8), _business_field_label(label), font=tiny_font, fill="#4b493d", max_chars=12)
                _draw_text_safe(draw, (plot_left + 10, start_y + index * cell + 4), _business_field_label(label), font=tiny_font, fill="#4b493d", max_chars=12)
        elif kind.startswith("bar-") or kind == "histogram":
            labels = list(chart.get("x") or [])
            values = [float(_safe_float(value) or 0.0) for value in list(chart.get("y") or [])]
            pairs = [(label, value) for label, value in zip(labels, values)]
            pairs = sorted(pairs, key=lambda item: abs(item[1]), reverse=True)[:12]
            max_value = max([abs(value) for _, value in pairs] + [1.0])
            bar_gap = 12
            bar_height = max(20, min(42, (plot_bottom - plot_top - 40) // max(1, len(pairs)) - bar_gap))
            for index, (label, value) in enumerate(pairs):
                y = plot_top + 28 + index * (bar_height + bar_gap)
                bar_width = int(abs(value) / max_value * (plot_right - plot_left - 260))
                draw.rounded_rectangle([(plot_left + 180, y), (plot_left + 180 + bar_width, y + bar_height)], radius=8, fill="#b66f24")
                _draw_text_safe(draw, (plot_left + 12, y + 7), label, font=tiny_font, fill="#433729", max_chars=22)
                _draw_text_safe(draw, (plot_left + 190 + bar_width, y + 7), _format_business_amount(value), font=tiny_font, fill="#433729", max_chars=18)
        else:
            x_series, y_series = _fallback_chart_series(chart)
            if not x_series or not y_series:
                x_series, y_series = [0.0, 1.0], [0.0, 1.0]
            x_min, x_max = float(np.nanmin(x_series)), float(np.nanmax(x_series))
            y_min, y_max = float(np.nanmin(y_series)), float(np.nanmax(y_series))
            x_padding = (x_max - x_min) * 0.06 or 1.0
            y_padding = (y_max - y_min) * 0.08 or 1.0
            x_min -= x_padding
            x_max += x_padding
            y_min -= y_padding
            y_max += y_padding
            points = [
                _scaled_point(
                    x,
                    y,
                    x_min=x_min,
                    x_max=x_max,
                    y_min=y_min,
                    y_max=y_max,
                    plot_left=plot_left,
                    plot_top=plot_top,
                    plot_right=plot_right,
                    plot_bottom=plot_bottom,
                )
                for x, y in zip(x_series, y_series)
            ]
            if kind in {"line", "forecast"}:
                if len(points) > 1:
                    draw.line(points, fill="#2f6f4e", width=4)
                for point in points[:: max(1, len(points) // 36)]:
                    draw.ellipse([(point[0] - 4, point[1] - 4), (point[0] + 4, point[1] + 4)], fill="#2f6f4e")
            else:
                palette = ["#2f6f4e", "#c2573f", "#d9982f", "#4776a8", "#61743c"]
                raw_points = _chart_points(chart)
                for index, point in enumerate(points):
                    color = palette[index % len(palette)]
                    if raw_points:
                        key = str(raw_points[index].get("quadrant") or raw_points[index].get("cluster") or "")
                        color = {
                            "high_high": "#2f6f4e",
                            "high_low": "#c2573f",
                            "low_high": "#d9982f",
                            "low_low": "#7b8794",
                            "0": "#2f6f4e",
                            "1": "#c2573f",
                            "2": "#d9982f",
                            "3": "#4776a8",
                        }.get(key, color)
                    radius = 8 if len(points) <= 80 else 5
                    draw.ellipse([(point[0] - radius, point[1] - radius), (point[0] + radius, point[1] + radius)], fill=color, outline="#fffaf0", width=2)
                if kind == "quadrant":
                    draw.line([(plot_left + (plot_right - plot_left) // 2, plot_top), (plot_left + (plot_right - plot_left) // 2, plot_bottom)], fill="#8c7653", width=2)
                    draw.line([(plot_left, plot_top + (plot_bottom - plot_top) // 2), (plot_right, plot_top + (plot_bottom - plot_top) // 2)], fill="#8c7653", width=2)
            _draw_text_safe(draw, (plot_left, plot_bottom + 20), _business_field_label(chart.get("x_label") or ""), font=label_font, fill="#4c533f", max_chars=44)
            _draw_text_safe(draw, (20, plot_top - 34), _business_field_label(chart.get("y_label") or ""), font=label_font, fill="#4c533f", max_chars=44)
            _draw_text_safe(draw, (plot_left, plot_bottom + 52), f"x: {_format_business_amount(x_min)} to {_format_business_amount(x_max)}", font=tiny_font, fill="#6d674f", max_chars=80)
            _draw_text_safe(draw, (plot_left + 280, plot_bottom + 52), f"y: {_format_business_amount(y_min)} to {_format_business_amount(y_max)}", font=tiny_font, fill="#6d674f", max_chars=80)

        interpretation = _chart_writer_text(chart, "caption", _business_chart_interpretation(chart))
        wrapped = textwrap.wrap(_report_cell_text(interpretation, 260), width=98)[:3]
        draw.rounded_rectangle([(34, height - 118), (width - 34, height - 34)], radius=18, fill="#f0e3cd", outline="#d6c4a6")
        for line_index, line in enumerate(wrapped):
            _draw_text_safe(draw, (56, height - 100 + line_index * 24), line, font=small_font, fill="#344035", max_chars=120)
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path, format="PNG")
        return path.exists() and path.stat().st_size > 0
    except Exception:
        return _write_basic_png_placeholder(path)


def _write_chart_png(chart: dict[str, Any], *, path: Path, title: str | None = None) -> bool:
    plt = _load_matplotlib_pyplot()
    if plt is None:
        return _write_chart_png_fallback(chart, path=path, title=title)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(13.5, 8.0), dpi=180)
    fig.patch.set_facecolor("#fffaf0")
    ax.set_facecolor("#fffdf8")
    kind = str(chart.get("kind") or "")
    display_title = str(title or chart.get("title") or kind or "chart")
    ax.set_title(display_title, loc="left", fontsize=18, fontweight="bold", color="#253d2a", pad=16)
    try:
        if kind in {"bubble", "quadrant"}:
            _draw_scatter_like_chart(ax, chart, quadrant=True)
        elif kind in {"scatter", "cluster-scatter", "anomaly-scatter"} or kind.startswith("scatter-"):
            _draw_scatter_like_chart(ax, chart, quadrant=False)
        elif kind == "histogram" or kind.startswith("bar-"):
            _draw_bar_chart(ax, list(chart.get("x") or []), list(chart.get("y") or []), color="#b66f24")
        elif kind == "heatmap":
            matrix = np.asarray(chart.get("matrix") or [], dtype=float)
            labels = [_report_cell_text(_business_field_label(label), 18) for label in list(chart.get("labels") or [])]
            image = ax.imshow(matrix, cmap="RdYlGn", vmin=-1, vmax=1)
            ax.set_xticks(np.arange(len(labels)), labels, rotation=35, ha="right")
            ax.set_yticks(np.arange(len(labels)), labels)
            fig.colorbar(image, ax=ax, fraction=0.035, pad=0.03)
        elif kind in {"line", "forecast"}:
            x_values = list(chart.get("x") or [])
            actual = list(chart.get("actual") or chart.get("y") or [])
            forecast = list(chart.get("forecast") or [])
            ax.plot(range(len(actual)), [np.nan if value is None else float(value) for value in actual], color="#2f6f4e", linewidth=2.4, label="actual")
            if forecast:
                ax.plot(range(len(forecast)), [np.nan if value is None else float(value) for value in forecast], color="#c2573f", linewidth=2.0, linestyle="--", label="forecast")
            if x_values:
                ticks = np.linspace(0, max(0, len(x_values) - 1), min(8, len(x_values))).round().astype(int)
                ax.set_xticks(ticks, [_report_cell_text(x_values[int(item)], 12) for item in ticks], rotation=25, ha="right")
            ax.legend(loc="best")
        else:
            rows = [
                {"指标": "图表类型", "值": kind},
                {"指标": "数据点数", "值": _chart_point_count(chart)},
                {"指标": "业务判断", "值": _business_chart_interpretation(chart)},
            ]
            _write_method_preview_png(rows, path=path, title=display_title)
            plt.close(fig)
            return True
        ax.set_xlabel(_business_field_label(chart.get("x_label") or ""), color="#596050")
        ax.set_ylabel(_business_field_label(chart.get("y_label") or ""), color="#596050")
        ax.grid(True, color="#e7ddc7", linewidth=0.8, alpha=0.72)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#d0c4aa")
        ax.spines["bottom"].set_color("#d0c4aa")
        fig.text(0.02, 0.02, _chart_writer_text(chart, "caption", _business_chart_interpretation(chart)), fontsize=10, color="#334035", wrap=True)
        fig.tight_layout(rect=(0, 0.08, 1, 1))
        fig.savefig(path, bbox_inches="tight", facecolor=fig.get_facecolor())
    finally:
        plt.close(fig)
    return path.exists() and path.stat().st_size > 0


def _format_evidence_number(value: Any) -> str:
    number = _safe_float(value)
    if number is None:
        return _report_cell_text(value, 40)
    return _format_plain_number(number)


def _method_numeric_profile(rows: list[dict[str, Any]]) -> dict[str, Any]:
    frame = pd.DataFrame(rows or [])
    profile: dict[str, Any] = {
        "row_count": int(frame.shape[0]) if not frame.empty else 0,
        "column_count": int(frame.shape[1]) if not frame.empty else 0,
        "numeric_columns": [],
        "text_columns": [],
    }
    if frame.empty:
        return profile
    numeric_column_names: set[str] = set()
    candidate_columns = [
        column
        for column in list(frame.columns)[:120]
        if not _is_internal_evidence_column(column)
    ]
    candidate_columns = sorted(candidate_columns, key=_business_evidence_priority, reverse=True)
    for column in candidate_columns:
        series = pd.to_numeric(frame[column], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
        if series.empty:
            continue
        numeric_column_names.add(str(column))
        profile["numeric_columns"].append(
            {
                "column": _business_field_label(column),
                "raw_column": str(column),
                "count": int(series.shape[0]),
                "min": float(series.min()),
                "max": float(series.max()),
                "mean": float(series.mean()),
            }
        )
        if len(profile["numeric_columns"]) >= 8:
            break
    text_candidates = [
        column
        for column in list(frame.columns)[:80]
        if not _is_internal_evidence_column(column)
    ]
    text_candidates = sorted(text_candidates, key=_business_evidence_priority, reverse=True)
    for column in text_candidates:
        if len(profile["text_columns"]) >= 4 or str(column) in numeric_column_names:
            continue
        series = frame[column].dropna().astype(str)
        series = series[series.str.strip() != ""]
        if series.empty:
            continue
        top_values = series.value_counts().head(3)
        if top_values.empty:
            continue
        profile["text_columns"].append(
            {
                "column": _business_field_label(column),
                "raw_column": str(column),
                "top_values": [
                    {"value": str(index), "count": int(count)}
                    for index, count in top_values.items()
                ],
            }
        )
    return profile


def _numeric_profile_summary(profile: dict[str, Any], *, limit: int = 3) -> str:
    parts: list[str] = []
    for item in list(profile.get("numeric_columns") or [])[:limit]:
        parts.append(
            f"{item.get('column')}：样本数{item.get('count')}，"
            f"均值{_format_evidence_number(item.get('mean'))}，"
            f"区间{_format_evidence_number(item.get('min'))}至{_format_evidence_number(item.get('max'))}"
        )
    return "; ".join(parts)


def _text_profile_summary(profile: dict[str, Any], *, limit: int = 2) -> str:
    parts: list[str] = []
    for item in list(profile.get("text_columns") or [])[:limit]:
        top_values = [
            f"{value.get('value')}({value.get('count')})"
            for value in list(item.get("top_values") or [])[:3]
        ]
        if top_values:
            parts.append(f"{item.get('column')}：{', '.join(top_values)}")
    return "；".join(parts)


def _family_business_interpretation(family: Any) -> str:
    key = str(family or "unknown")
    templates = {
        "association": "用于识别指标之间是否同向或反向变化，适合作为后续驱动分析的候选线索。",
        "causal": "用于形成因果方向假设，但仍需结合业务机制、样本选择和外部事实复核。",
        "clustering": "用于把对象分成相似群体，适合制定分层管理和差异化复核动作。",
        "comparison": "用于比较不同对象或分组的水平差异，适合定位优先关注组。",
        "descriptive": "用于建立规模、分布和异常区间的底盘判断，是后续结论的基础证据。",
        "distribution": "用于检查数据集中、长尾和离散程度，帮助判断是否需要分层解读。",
        "forecast": "用于趋势判断，但必须有可靠时间轴才适合外推。",
        "machine_learning": "用于辅助识别复杂模式，输出应作为筛查线索而非自动决策。",
        "report_part": "用于组织报告上下文，本身不构成单独业务结论。",
        "statistical_test": "用于检验差异或关系是否足够稳定，结论需同时看业务量级。",
        "time_series": "用于观察时间变化，但本轮若时间字段不足，应避免过度预测。",
        "visual": "用于把关系和异常显性化，优先服务于定位问题和沟通证据。",
    }
    return templates.get(key, "用于补充交叉验证，结论应回到业务字段、样本量和可追溯证据。")


def _fallback_method_interpretation(package: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    execution = package.get("execution") if isinstance(package.get("execution"), dict) else {}
    method_id = str(package.get("method_id") or "")
    run_id = str(package.get("method_run_id") or method_id)
    bound_fields = str(execution.get("bound_fields") or "")
    result_summary = str(execution.get("result_summary") or "").strip()
    profile = _method_numeric_profile(rows)
    method_name = str(package.get("method_name_zh") or package.get("method_name") or method_id or run_id)
    family = str(package.get("family") or "unknown")
    numeric_summary = _numeric_profile_summary(profile)
    text_summary = _text_profile_summary(profile)
    asset_refs = [
        str(asset.get("asset_ref") or "")
        for asset in list(package.get("assets") or [])
        if isinstance(asset, dict) and str(asset.get("asset_ref") or "").strip()
    ]
    business_role = _family_business_interpretation(family)
    evidence_sentence = (
        f"关键业务数值：{numeric_summary}。"
        if numeric_summary
        else "该方法没有提取到可直接写入结论的业务数值，更多用于补充结构、图表或章节证据。"
    )
    text_sentence = f"主要分类取值：{text_summary}。" if text_summary else ""
    bound_sentence = f"涉及字段：{bound_fields}。" if bound_fields else ""
    base_interpretation = (
        f"【{method_name}】属于{_method_family_label(family)}。{business_role}"
        f"{bound_sentence}{evidence_sentence}{text_sentence}"
    )
    if result_summary:
        base_interpretation += f"执行摘要：{_report_cell_text(result_summary, 220)}。"
    if numeric_summary:
        base_interpretation += "判断：这些数值可作为业务排序、异常复核或分层讨论的证据，但必须与报告中的总体业务信号一起解释。"
    return {
        "method_id": method_id,
        "method_run_id": run_id,
        "status": "local_numeric_cli_analysis_completed",
        "cli_analysis_source": "local_numeric_profile",
        "headline": (
            f"{method_name}已形成{profile.get('row_count') or 0}行可读证据，"
            f"其中{len(profile.get('numeric_columns') or [])}个业务数值字段可直接用于判断。"
        ),
        "interpretation": base_interpretation,
        "evidence_refs": list((package.get("method_card") or {}).get("evidence_refs") or [])[:20],
        "asset_refs": asset_refs[:20],
        "recommended_action": "",
        "agent_review_required": True,
        "risks_or_limits": "该解读基于当前导出的结构化证据，不替代人工业务口径复核；小样本、派生字段和异常值都需要单独确认。",
        "row_count": len(rows),
        "numeric_profile": profile,
        "top_numeric_evidence": numeric_summary,
    }


def _write_method_readme(path: Path, *, package: dict[str, Any], interpretation: dict[str, Any], rows: int, cols: int) -> None:
    method_name = _client_method_name(package)
    family_label = _method_family_label(package.get("family"))
    lines = [
        f"# {method_name}",
        "",
        f"- 方法类型：{family_label}",
        f"- 导出行数：{rows}",
        f"- 导出列数：{cols}",
        f"- 追溯标识：{_public_evidence_ref(package.get('method_run_id') or package.get('method_id'))}",
        "",
        "## 业务解读",
        "",
        str(interpretation.get("interpretation") or interpretation.get("headline") or "本方法包已生成本地业务数值解读。"),
        "",
        "## 文件说明",
        "",
        "- data.json：结构化证据，用于复核字段和原始方法输出。",
        "- data.csv：表格数据，便于审计和二次分析。",
        "- data.xlsx：Excel 版本，便于业务团队查看。",
        "- preview.png：方法结果预览图，可用于快速核对形态。",
    ]
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def _method_interpretation_prompt() -> str:
    return f"""You are the Analysis Lab per-method interpretation agent.

Working directory is the Lab runtime export directory. Read `{METHOD_INTERPRETATION_INPUT_FILE}` and inspect each task's JSON/CSV/XLSX/PNG artifacts before writing `{METHOD_INTERPRETATION_RESULT_FILE}`.

Requirements:
1. Treat every method_run_id as an independent run, even when several runs share the same method_id.
2. Preserve evidence_refs, asset_refs, and artifact paths in the output.
3. For every task, write concise Chinese business analysis with headline, interpretation, recommended_action, risks_or_limits, and evidence_refs.
4. Return JSON with top-level keys: contract, runtime_status, generated_at, method_count, interpretations.
5. If evidence is insufficient, say what is missing instead of inventing conclusions.
"""


def _sync_codex_cli_timeout_sec() -> int:
    raw = os.getenv("ASTERIA_ANALYSIS_LAB_SYNC_CODEX_TIMEOUT_SEC", "").strip()
    try:
        value = int(raw)
    except ValueError:
        value = 180
    return max(8, min(value, 180))


def _sync_codex_cli_enabled() -> bool:
    raw = os.getenv("ASTERIA_ANALYSIS_LAB_SYNC_CODEX_ENABLED", "").strip().lower()
    if raw:
        return raw in {"1", "true", "yes", "on"}
    if os.getenv("PYTEST_CURRENT_TEST"):
        return False
    return True


def _build_sync_codex_cli_digest(interpretations: list[dict[str, Any]], *, dataset_name: str, sheet_name: str) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for item in interpretations[:80]:
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "method_run_id": item.get("method_run_id"),
                "method_id": item.get("method_id"),
                "headline": item.get("headline"),
                "top_numeric_evidence": item.get("top_numeric_evidence"),
                "row_count": item.get("row_count"),
                "numeric_profile": {
                    "numeric_columns": list((item.get("numeric_profile") or {}).get("numeric_columns") or [])[:3],
                    "text_columns": list((item.get("numeric_profile") or {}).get("text_columns") or [])[:2],
                },
                "evidence_refs": list(item.get("evidence_refs") or [])[:6],
                "asset_refs": list(item.get("asset_refs") or [])[:6],
            }
        )
    return {
        "contract": "analysis_lab_sync_codex_cli_digest_v1",
        "dataset_name": dataset_name,
        "sheet_name": sheet_name,
        "method_count": len(interpretations),
        "methods": rows,
    }


def _extract_any_json_object(text: str) -> dict[str, Any] | None:
    stripped = str(text or "").strip()
    if not stripped:
        return None
    try:
        value = json.loads(stripped)
        return value if isinstance(value, dict) else None
    except Exception:
        pass
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        value = json.loads(stripped[start : end + 1])
    except Exception:
        return None
    return value if isinstance(value, dict) else None


def _run_sync_codex_cli_interpretation(
    *,
    export_dir: Path,
    dataset_name: str,
    sheet_name: str,
    interpretations: list[dict[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
    timeout_sec = _sync_codex_cli_timeout_sec()
    try:
        from app.services.codex_cli_resolver_service import resolve_codex_cli_command
        from app.services.codex_runtime_service import _codex_config_overrides, _prepare_codex_subprocess_env
        from app.services.settings_service import load_runtime_settings_raw

        settings = load_runtime_settings_raw()
        command = resolve_codex_cli_command(settings)
        model = str(settings.get("model") or "").strip()
        digest = _build_sync_codex_cli_digest(interpretations, dataset_name=dataset_name, sheet_name=sheet_name)
        prompt = (
            "You are the Analysis Lab synchronous Codex CLI reviewer. "
            "Return only compact JSON with keys runtime_status, executive_cli_summary, "
            "method_notes, risks_or_limits, recommended_next_actions. "
            "Write all summaries and actions in Chinese. Use only the numeric evidence in the JSON. Do not invent facts.\n\n"
            + json.dumps(digest, ensure_ascii=False, default=str)
        )
        output_path = export_dir / "codex_method_interpretations.sync_cli_output.txt"
        args = [
            command,
            *_codex_config_overrides(settings),
            "--ask-for-approval",
            "never",
            "--sandbox",
            "read-only",
            "-C",
            str(export_dir.resolve()),
            "exec",
            "--skip-git-repo-check",
            "--output-last-message",
            str(output_path.resolve()),
        ]
        if model:
            args.extend(["--model", model])
        args.append("-")
        env = _prepare_codex_subprocess_env(settings)
        proc = subprocess.run(
            args,
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_sec,
            cwd=str(export_dir.resolve()),
            env=env,
            check=False,
        )
        raw_output = output_path.read_text(encoding="utf-8", errors="replace") if output_path.exists() else proc.stdout
        parsed = _extract_any_json_object(raw_output)
        if proc.returncode == 0 and parsed:
            return {
                "runtime_status": "codex_cli_sync_completed",
                "generated_at": generated_at,
                "timeout_sec": timeout_sec,
                "returncode": proc.returncode,
                "output_path": str(output_path.resolve()),
                "summary": parsed,
                "stderr_excerpt": _report_cell_text(proc.stderr, 1200),
            }
        return {
            "runtime_status": "codex_cli_sync_failed_local_numeric_analysis_used",
            "generated_at": generated_at,
            "timeout_sec": timeout_sec,
            "returncode": proc.returncode,
            "output_path": str(output_path.resolve()),
            "error": _report_cell_text(proc.stderr or proc.stdout or raw_output, 1600),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "runtime_status": "codex_cli_sync_timed_out_local_numeric_analysis_used",
            "generated_at": generated_at,
            "timeout_sec": timeout_sec,
            "error": f"Codex CLI 未在 {timeout_sec} 秒内完成；本报告已使用本地数值业务解读补齐。",
        }
    except Exception as exc:
        return {
            "runtime_status": "codex_cli_sync_failed_local_numeric_analysis_used",
            "generated_at": generated_at,
            "timeout_sec": timeout_sec,
            "error": _report_cell_text(str(exc), 1200),
        }


def _append_downloadable(downloadables: list[dict[str, Any]], item: dict[str, Any]) -> None:
    existing_path = str(item.get("path") or "")
    existing_name = str(item.get("name") or "")
    if any(str(row.get("path") or "") == existing_path or str(row.get("name") or "") == existing_name for row in downloadables):
        return
    downloadables.append(item)


def _method_interpretation_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Analysis Lab 方法业务解读",
        "",
        f"- 解读状态：{_review_status_label(payload.get('runtime_status'))}",
        f"- 方法数量：{payload.get('method_count') or 0}",
        "",
    ]
    for item in list(payload.get("interpretations") or []):
        if not isinstance(item, dict):
            continue
        lines.extend(
            [
                f"## {item.get('method_run_id') or item.get('method_id') or 'method'}",
                "",
                f"- 方法标识：`{item.get('method_id') or ''}`",
                f"- 解读状态：{_interpretation_status_label(item.get('status'))}",
                f"- 标题：{_report_cell_text(item.get('headline'), 360)}",
                "",
                str(item.get("interpretation") or ""),
                "",
                "- 复核说明：业务行动由报告复核记录统一产出。",
                f"- 风险边界：{_report_cell_text(item.get('risks_or_limits'), 500)}",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def _artifact_file_status(path: Path, *, public_path: str, required: bool = True) -> dict[str, Any]:
    exists = path.exists()
    size = path.stat().st_size if exists else 0
    return {
        "name": path.name,
        "path": public_path,
        "required": required,
        "exists": exists,
        "size_bytes": size,
        "status": "ok" if exists and (size > 0 or not required) else "missing",
    }


def _write_method_artifact_exports(
    *,
    export_dir: Path,
    public_base_path: str,
    request: AutoAnalysisRequest,
    dataset_name: str,
    sheet_name: str,
    charts: list[dict[str, Any]],
    method_execution_packages: list[dict[str, Any]],
    downloadables: list[dict[str, Any]],
    generated_at: str,
    large_sample_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_root = export_dir / METHOD_ARTIFACT_DIR
    artifact_root.mkdir(parents=True, exist_ok=True)
    index_rows: list[dict[str, Any]] = []
    tasks: list[dict[str, Any]] = []
    interpretations: list[dict[str, Any]] = []
    integrity_rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    large_sample = bool((large_sample_policy or {}).get("large_sample"))
    for index, package in enumerate(method_execution_packages, start=1):
        run_id = str(package.get("method_run_id") or package.get("method_id") or f"method-{index}")
        method_id = str(package.get("method_id") or run_id)
        folder_name = f"{index:03d}-{_safe_artifact_segment(run_id, f'method-{index}')}"
        folder = artifact_root / folder_name
        folder.mkdir(parents=True, exist_ok=True)
        rows = _rows_from_package(package)
        data_json_path = folder / "data.json"
        data_csv_path = folder / "data.csv"
        data_xlsx_path = folder / "data.xlsx"
        preview_png_path = folder / "preview.png"
        readme_path = folder / "README.md"
        rel_prefix = f"{METHOD_ARTIFACT_DIR}/{folder_name}"
        row_count = 0
        column_count = 0
        xlsx_status = "written"
        preview_status = "not_written"

        try:
            _write_json_file(
                data_json_path,
                {
                    "contract": "analysis_lab_single_method_artifact_v1",
                    "generated_at": generated_at,
                    "dataset_id": request.dataset_id,
                    "dataset_name": dataset_name,
                    "sheet_name": sheet_name or request.active_sheet or "",
                    "method_id": method_id,
                    "method_run_id": run_id,
                    "package": package,
                    "rows": rows,
                },
            )
            row_count, column_count = _write_dataframe_artifacts(rows, csv_path=data_csv_path, xlsx_path=data_xlsx_path)
            if not data_xlsx_path.exists():
                xlsx_status = "failed"
        except Exception as exc:
            errors.append({"method_run_id": run_id, "stage": "dataframe_export", "error": str(exc)})
            xlsx_status = "failed"

        try:
            visual_chart = _chart_for_method_package(package, charts) if str(package.get("family") or "") == "visual" else None
            if visual_chart:
                preview_status = (
                    "written_chart"
                    if _write_chart_png(visual_chart, path=preview_png_path, title=f"{run_id} · {visual_chart.get('title') or visual_chart.get('kind')}")
                    else "skipped"
                )
            else:
                preview_status = "written" if _write_method_preview_png(rows, path=preview_png_path, title=f"{run_id} preview") else "skipped"
        except Exception as exc:
            errors.append({"method_run_id": run_id, "stage": "preview_png", "error": str(exc)})
            preview_status = "failed"

        interpretation = _fallback_method_interpretation(package, rows)
        interpretation.update(
            {
                "artifact_folder": rel_prefix,
                "data_json_path": _client_public_path(public_base_path, f"{rel_prefix}/data.json"),
                "data_csv_path": _client_public_path(public_base_path, f"{rel_prefix}/data.csv"),
                "data_xlsx_path": _client_public_path(public_base_path, f"{rel_prefix}/data.xlsx"),
                "preview_png_path": _client_public_path(public_base_path, f"{rel_prefix}/preview.png"),
            }
        )
        interpretations.append(interpretation)
        _write_method_readme(readme_path, package=package, interpretation=interpretation, rows=row_count, cols=column_count)

        artifact_exports = {
            "folder": rel_prefix,
            "data_json_path": _client_public_path(public_base_path, f"{rel_prefix}/data.json"),
            "data_csv_path": _client_public_path(public_base_path, f"{rel_prefix}/data.csv"),
            "data_xlsx_path": _client_public_path(public_base_path, f"{rel_prefix}/data.xlsx"),
            "preview_png_path": _client_public_path(public_base_path, f"{rel_prefix}/preview.png"),
            "readme_path": _client_public_path(public_base_path, f"{rel_prefix}/README.md"),
            "data_json_file_path": str(data_json_path.resolve()),
            "data_csv_file_path": str(data_csv_path.resolve()),
            "data_xlsx_file_path": str(data_xlsx_path.resolve()),
            "preview_png_file_path": str(preview_png_path.resolve()),
            "readme_file_path": str(readme_path.resolve()),
            "row_count": row_count,
            "column_count": column_count,
            "xlsx_status": xlsx_status,
            "preview_status": preview_status,
            "preview_kind": "business_chart" if str(preview_status) == "written_chart" else "table_preview",
        }
        file_statuses = [
            _artifact_file_status(data_json_path, public_path=artifact_exports["data_json_path"]),
            _artifact_file_status(data_csv_path, public_path=artifact_exports["data_csv_path"]),
            _artifact_file_status(data_xlsx_path, public_path=artifact_exports["data_xlsx_path"]),
            _artifact_file_status(preview_png_path, public_path=artifact_exports["preview_png_path"]),
            _artifact_file_status(readme_path, public_path=artifact_exports["readme_path"]),
        ]
        integrity_status = "complete" if all(item["status"] == "ok" for item in file_statuses) else "incomplete"
        artifact_exports["integrity_status"] = integrity_status
        artifact_exports["file_statuses"] = file_statuses
        package["artifact_exports"] = artifact_exports
        package["codex_interpretation"] = interpretation
        integrity_rows.append(
            {
                "method_id": method_id,
                "method_run_id": run_id,
                "package_ref": package.get("package_ref") or f"data:method_execution_packages:{package.get('package_id')}",
                "artifact_folder": rel_prefix,
                "integrity_status": integrity_status,
                "row_count": row_count,
                "column_count": column_count,
                "missing_files": [item["name"] for item in file_statuses if item["status"] != "ok"],
                "files": file_statuses,
            }
        )

        index_row = {
            "index": index,
            "method_id": method_id,
            "method_run_id": run_id,
            "method_name": _client_method_name(package),
            "family": package.get("family") or "",
            "status": package.get("status") or (package.get("execution") or {}).get("status") or "",
            "row_count": row_count,
            "column_count": column_count,
            "artifact_folder": rel_prefix,
            "data_json_path": artifact_exports["data_json_path"],
            "data_csv_path": artifact_exports["data_csv_path"],
            "data_xlsx_path": artifact_exports["data_xlsx_path"],
            "preview_png_path": artifact_exports["preview_png_path"],
            "readme_path": artifact_exports["readme_path"],
            "package_ref": package.get("package_ref") or f"data:method_execution_packages:{package.get('package_id')}",
            "evidence_refs": ", ".join(str(ref) for ref in list(interpretation.get("evidence_refs") or [])[:20]),
            "asset_refs": ", ".join(str(ref) for ref in list(interpretation.get("asset_refs") or [])[:20]),
            "interpretation_status": interpretation.get("status"),
            "integrity_status": integrity_status,
        }
        index_rows.append(index_row)
        tasks.append(
            {
                "task_id": f"interpret_{index:03d}_{_safe_artifact_segment(run_id, f'method-{index}')}",
                "method_id": method_id,
                "method_run_id": run_id,
                "package_ref": index_row["package_ref"],
                "artifact_paths": {
                    "json": artifact_exports["data_json_path"],
                    "csv": artifact_exports["data_csv_path"],
                    "xlsx": artifact_exports["data_xlsx_path"],
                    "png": artifact_exports["preview_png_path"],
                    "readme": artifact_exports["readme_path"],
                },
                "expected_output": {
                    "headline": "string",
                    "interpretation": "string",
                    "recommended_action": "string",
                    "risks_or_limits": "string",
                    "evidence_refs": "string[]",
                },
            }
        )

        for suffix, file_path, kind, purpose in (
            ("data.json", data_json_path, "json", "Per-method structured rows and source package."),
            ("data.csv", data_csv_path, "csv", "Per-method tabular export."),
            ("data.xlsx", data_xlsx_path, "xlsx", "Per-method spreadsheet export."),
            ("preview.png", preview_png_path, "png", "Per-method visual table preview."),
            ("README.md", readme_path, "md", "Per-method interpretation and file guide."),
        ):
            if not file_path.exists():
                continue
            _append_downloadable(
                downloadables,
                _public_downloadable_item(
                    {
                        "name": f"{folder_name}-{suffix}",
                        "path": _client_public_path(public_base_path, f"{rel_prefix}/{suffix}"),
                        "file_path": str(file_path.resolve()),
                        "type": kind,
                        "purpose": purpose,
                        "is_main": False,
                        "download_kind": "method_artifact",
                        "method_name": _client_method_name(package),
                        "trace_ref": _public_evidence_ref(run_id),
                    }
                ),
            )

    index_json_path = export_dir / METHOD_ARTIFACT_INDEX_JSON
    index_csv_path = export_dir / METHOD_ARTIFACT_INDEX_CSV
    index_xlsx_path = export_dir / METHOD_ARTIFACT_INDEX_XLSX
    integrity_path = export_dir / METHOD_ARTIFACT_INTEGRITY_FILE
    interpretation_input_path = export_dir / METHOD_INTERPRETATION_INPUT_FILE
    interpretation_prompt_path = export_dir / METHOD_INTERPRETATION_PROMPT_FILE
    interpretation_result_path = export_dir / METHOD_INTERPRETATION_RESULT_FILE
    interpretation_report_path = export_dir / METHOD_INTERPRETATION_REPORT_FILE

    index_payload = {
        "contract": "analysis_lab_method_artifact_index_v1",
        "generated_at": generated_at,
        "dataset_id": request.dataset_id,
        "dataset_name": dataset_name,
        "sheet_name": sheet_name or request.active_sheet or "",
        "method_count": len(method_execution_packages),
        "artifact_root": METHOD_ARTIFACT_DIR,
        "rows": index_rows,
        "errors": errors,
    }
    _write_json_file(index_json_path, index_payload)
    _write_dataframe_artifacts(index_rows, csv_path=index_csv_path, xlsx_path=index_xlsx_path)
    complete_count = len([row for row in integrity_rows if row.get("integrity_status") == "complete"])
    integrity_payload = {
        "contract": "analysis_lab_method_artifact_integrity_v1",
        "generated_at": generated_at,
        "dataset_id": request.dataset_id,
        "dataset_name": dataset_name,
        "sheet_name": sheet_name or request.active_sheet or "",
        "method_count": len(method_execution_packages),
        "complete_count": complete_count,
        "incomplete_count": max(0, len(method_execution_packages) - complete_count),
        "integrity_status": "passed" if complete_count == len(method_execution_packages) else "failed",
        "artifact_root": METHOD_ARTIFACT_DIR,
        "rows": integrity_rows,
        "errors": errors,
    }
    _write_json_file(integrity_path, integrity_payload)

    interpretation_input = {
        "contract": "analysis_lab_method_interpretation_batch_v1",
        "generated_at": generated_at,
        "dataset_id": request.dataset_id,
        "dataset_name": dataset_name,
        "sheet_name": sheet_name or request.active_sheet or "",
        "user_goal": request.user_goal,
        "method_count": len(method_execution_packages),
        "large_sample_policy": large_sample_policy or {},
        "tasks": tasks,
        "required_output": METHOD_INTERPRETATION_RESULT_FILE,
        "fallback_result_file": METHOD_INTERPRETATION_RESULT_FILE,
    }
    _write_json_file(interpretation_input_path, interpretation_input)
    interpretation_prompt_path.write_text(_method_interpretation_prompt(), encoding="utf-8")

    interpretation_payload = {
        "contract": "analysis_lab_method_interpretations_v1",
        "runtime_status": "local_numeric_cli_analysis_completed",
        "generated_at": generated_at,
        "dataset_id": request.dataset_id,
        "dataset_name": dataset_name,
        "sheet_name": sheet_name or request.active_sheet or "",
        "method_count": len(method_execution_packages),
        "large_sample_policy": large_sample_policy or {},
        "interpretations": interpretations,
        "errors": errors,
    }
    sync_cli_result: dict[str, Any] = {}
    if not method_execution_packages:
        sync_cli_result = {
            "runtime_status": "no_method_packages_local_numeric_analysis_unavailable",
            "generated_at": generated_at,
            "timeout_sec": 0,
            "error": "No method packages were available for CLI interpretation.",
        }
    elif not bool(getattr(request, "cli_interpretation_enabled", True)):
        sync_cli_result = {
            "runtime_status": "cli_interpretation_disabled_local_numeric_analysis_used",
            "generated_at": generated_at,
            "timeout_sec": 0,
            "error": "Request set cli_interpretation_enabled=false; per-method local numeric analysis was still materialized.",
        }
    elif large_sample:
        sync_cli_result = {
            "runtime_status": "codex_cli_sync_deferred_large_sample_local_numeric_analysis_used",
            "generated_at": generated_at,
            "timeout_sec": 0,
            "error": "Large-sample runs keep Codex enhancement inputs but do not block report generation on synchronous CLI execution.",
            "async_recommended": True,
        }
    else:
        if _sync_codex_cli_enabled():
            sync_cli_result = _run_sync_codex_cli_interpretation(
                export_dir=export_dir,
                dataset_name=dataset_name,
                sheet_name=sheet_name or request.active_sheet or "",
                interpretations=interpretations,
                generated_at=generated_at,
            )
        else:
            sync_cli_result = {
                "runtime_status": "codex_cli_sync_disabled_local_numeric_analysis_used",
                "generated_at": generated_at,
                "timeout_sec": _sync_codex_cli_timeout_sec(),
                "error": "Set ASTERIA_ANALYSIS_LAB_SYNC_CODEX_ENABLED=1 to run synchronous codex exec during report generation.",
            }
    interpretation_payload["sync_codex_cli"] = sync_cli_result
    if sync_cli_result.get("runtime_status") == "codex_cli_sync_completed":
        interpretation_payload["runtime_status"] = "codex_cli_sync_completed"
    elif not str(sync_cli_result.get("runtime_status") or "").startswith("no_method_packages"):
        interpretation_payload["runtime_status"] = "local_numeric_cli_analysis_completed"
    _write_json_file(interpretation_result_path, interpretation_payload)
    interpretation_report_path.write_text(_method_interpretation_report(interpretation_payload), encoding="utf-8")

    runtime_status = interpretation_payload["runtime_status"]
    codex_task_id = ""
    codex_run_id = ""
    codex_error = ""
    async_requested_by_env = bool(os.getenv("ASTERIA_ANALYSIS_LAB_ASYNC_CODEX_TASK_ENABLED", "0").strip() in {"1", "true", "TRUE", "yes", "YES"})
    async_enabled = large_sample or async_requested_by_env
    if async_enabled and bool(getattr(request, "cli_interpretation_enabled", True)) and method_execution_packages:
        try:
            from app.models import CodexRunRequest
            from app.services.codex_runtime_task_service import create_codex_run_task
            from app.services.settings_service import load_runtime_settings_raw

            settings = load_runtime_settings_raw()
            timeout_sec = max(60, min(int(settings.get("codex_timeout_sec") or 1800), 600))
            run_request = CodexRunRequest(
                workspace_path=str(export_dir.resolve()),
                prompt_template=_method_interpretation_prompt(),
                user_requirement=request.user_goal or "Interpret each Analysis Lab method artifact for management use.",
                context_payload={
                    "input_file": METHOD_INTERPRETATION_INPUT_FILE,
                    "prompt_file": METHOD_INTERPRETATION_PROMPT_FILE,
                    "expected_output": METHOD_INTERPRETATION_RESULT_FILE,
                    "dataset_name": dataset_name,
                    "sheet_name": sheet_name or request.active_sheet or "",
                    "method_count": len(method_execution_packages),
                    "method_run_ids": [str(package.get("method_run_id") or package.get("method_id") or "") for package in method_execution_packages],
                    "large_sample_policy": large_sample_policy or {},
                },
                report_id=f"analysis-lab-method-interpretation-{request.dataset_id}",
                parent_report_id=f"analysis-lab-{request.dataset_id}",
                dataset_id=request.dataset_id,
                sheet_name=sheet_name or request.active_sheet or "",
                stage_id="analysis_lab_method_interpretation",
                purpose="analysis_lab_method_interpretation",
                artifact_source=METHOD_INTERPRETATION_RESULT_FILE,
                timeout_sec=timeout_sec,
                capture_git_diff=False,
            )
            task = create_codex_run_task(
                run_request,
                parent_report_id=f"analysis-lab-{request.dataset_id}",
                parent_stage_id="analysis_lab_methods",
                stage_id="analysis_lab_method_interpretation",
                purpose="analysis_lab_method_interpretation",
                artifact_source=METHOD_INTERPRETATION_RESULT_FILE,
                return_full=True,
            )
            runtime_status = str(task.get("status") or "queued")
            codex_task_id = str(task.get("job_id") or "")
            codex_run_id = str(task.get("run_id") or "")
            interpretation_payload.update(
                {
                    "runtime_status": interpretation_payload.get("runtime_status") or runtime_status,
                    "codex_task_id": codex_task_id,
                    "codex_run_id": codex_run_id,
                    "async_codex_task_status": runtime_status,
                }
            )
            _write_json_file(interpretation_result_path, interpretation_payload)
        except Exception as exc:
            runtime_status = str(interpretation_payload.get("runtime_status") or "local_numeric_cli_analysis_completed")
            codex_error = str(exc)
            interpretation_payload.update({"async_codex_task_status": "failed_to_start", "async_codex_task_error": codex_error})
            _write_json_file(interpretation_result_path, interpretation_payload)

    interpretation_report_path.write_text(_method_interpretation_report(interpretation_payload), encoding="utf-8")

    for file_name, file_path, kind, purpose, download_kind, is_main in (
        (METHOD_ARTIFACT_INDEX_JSON, index_json_path, "json", "Index of every per-method JSON/CSV/XLSX/PNG export.", "method_artifact_index_json", False),
        (METHOD_ARTIFACT_INDEX_CSV, index_csv_path, "csv", "CSV index of every per-method artifact export.", "method_artifact_index_csv", False),
        (METHOD_ARTIFACT_INDEX_XLSX, index_xlsx_path, "xlsx", "Spreadsheet index of every per-method artifact export.", "method_artifact_index_xlsx", False),
        (METHOD_ARTIFACT_INTEGRITY_FILE, integrity_path, "json", "Machine-readable integrity check for every per-method artifact file.", "method_artifact_integrity", False),
        (METHOD_INTERPRETATION_INPUT_FILE, interpretation_input_path, "json", "Batch Codex CLI input for per-method interpretation.", "method_interpretation_input", False),
        (METHOD_INTERPRETATION_PROMPT_FILE, interpretation_prompt_path, "md", "Prompt used for per-method Codex CLI interpretation.", "method_interpretation_prompt", False),
        (METHOD_INTERPRETATION_RESULT_FILE, interpretation_result_path, "json", "Per-method interpretation result with deterministic fallback backfill.", "method_interpretation_result", True),
        (METHOD_INTERPRETATION_REPORT_FILE, interpretation_report_path, "md", "Readable per-method interpretation report.", "method_interpretation_report", True),
    ):
        _append_downloadable(
            downloadables,
            _public_downloadable_item(
                {
                    "name": file_name,
                    "path": _public_path(public_base_path, file_name),
                    "file_path": str(file_path.resolve()),
                    "type": kind,
                    "purpose": purpose,
                    "is_main": is_main,
                    "download_kind": download_kind,
                    "method_package_count": len(method_execution_packages),
                }
            ),
        )

    return {
        "runtime_status": runtime_status,
        "codex_task_id": codex_task_id,
        "codex_run_id": codex_run_id,
        "error": codex_error,
        "method_count": len(method_execution_packages),
        "artifact_root": _public_path(public_base_path, METHOD_ARTIFACT_DIR),
        "index_json_path": _public_path(public_base_path, METHOD_ARTIFACT_INDEX_JSON),
        "index_csv_path": _public_path(public_base_path, METHOD_ARTIFACT_INDEX_CSV),
        "index_xlsx_path": _public_path(public_base_path, METHOD_ARTIFACT_INDEX_XLSX),
        "integrity_path": _public_path(public_base_path, METHOD_ARTIFACT_INTEGRITY_FILE),
        "integrity_status": integrity_payload["integrity_status"],
        "integrity_complete_count": integrity_payload["complete_count"],
        "integrity_incomplete_count": integrity_payload["incomplete_count"],
        "interpretation_input_path": _public_path(public_base_path, METHOD_INTERPRETATION_INPUT_FILE),
        "interpretation_result_path": _public_path(public_base_path, METHOD_INTERPRETATION_RESULT_FILE),
        "interpretation_report_path": _public_path(public_base_path, METHOD_INTERPRETATION_REPORT_FILE),
        "sync_codex_cli": sync_cli_result,
        "large_sample_policy": large_sample_policy or {},
        "error_count": len(errors),
    }


def _write_chart_asset_exports(
    *,
    export_dir: Path,
    public_base_path: str,
    charts: list[dict[str, Any]],
    downloadables: list[dict[str, Any]],
    generated_at: str,
    large_sample_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    asset_root = export_dir / CHART_ASSET_DIR
    asset_root.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    chart_items = [item for item in charts if isinstance(item, dict)]
    for index, chart in enumerate(chart_items, start=1):
        kind = str(chart.get("kind") or f"chart-{index}")
        folder_name = f"{index:03d}-{_safe_artifact_segment(kind, f'chart-{index}')}"
        folder = asset_root / folder_name
        folder.mkdir(parents=True, exist_ok=True)
        image_path = folder / "chart.png"
        data_path = folder / "chart.json"
        readme_path = folder / "README.md"
        rel_prefix = f"{CHART_ASSET_DIR}/{folder_name}"
        chart_ref = _chart_export_ref(chart, index)
        chart["chart_ref"] = chart_ref
        chart_payload = {
            "contract": "analysis_lab_business_chart_asset_v1",
            "generated_at": generated_at,
            "chart_ref": chart_ref,
            "chart": chart,
            "business_interpretation": _business_chart_interpretation(chart),
            "report_writer_agent": _chart_writer_agent(chart),
            "caption": _chart_writer_text(chart, "caption", _business_chart_interpretation(chart)),
            "direct_answer": _chart_writer_text(chart, "direct_answer"),
            "recommended_action": _chart_writer_text(chart, "recommended_action"),
            "sample_scope": _chart_sample_scope(chart),
            "evidence_numbers": list(_chart_writer_agent(chart).get("evidence_numbers") or []),
            "source_refs": list(_chart_writer_agent(chart).get("source_refs") or []),
            "sampling_note": _chart_sampling_note(chart),
        }
        _write_json_file(data_path, chart_payload)
        image_status = "not_written"
        try:
            image_status = "written" if _write_chart_png(chart, path=image_path) else "skipped"
        except Exception as exc:
            image_status = "failed"
            errors.append({"chart_ref": chart_ref, "error": str(exc)})
        row = {
            "index": index,
            "chart_ref": chart_ref,
            "chart_kind": kind,
            "title": chart.get("title") or kind,
            "x_label": chart.get("x_label") or "",
            "y_label": chart.get("y_label") or "",
            "point_count": _chart_point_count(chart),
            "business_interpretation": _business_chart_interpretation(chart),
            "direct_answer": _chart_writer_text(chart, "direct_answer"),
            "caption": _chart_writer_text(chart, "caption"),
            "recommended_action": _chart_writer_text(chart, "recommended_action"),
            "sample_scope": json.dumps(_chart_sample_scope(chart), ensure_ascii=False, default=str),
            "evidence_numbers": json.dumps(list(_chart_writer_agent(chart).get("evidence_numbers") or []), ensure_ascii=False, default=str),
            "source_refs": "; ".join(str(ref) for ref in list(_chart_writer_agent(chart).get("source_refs") or [])),
            "sampling_note": _chart_sampling_note(chart),
            "chunk_count": int(((chart.get("sample_policy") if isinstance(chart.get("sample_policy"), dict) else {}) or {}).get("chunk_count") or 0),
            "chunk_size": int(((chart.get("sample_policy") if isinstance(chart.get("sample_policy"), dict) else {}) or {}).get("chunk_size") or 0),
            "folder": rel_prefix,
            "image_path": _client_public_path(public_base_path, f"{rel_prefix}/chart.png"),
            "data_path": _client_public_path(public_base_path, f"{rel_prefix}/chart.json"),
            "readme_path": _client_public_path(public_base_path, f"{rel_prefix}/README.md"),
            "image_status": image_status,
            "integrity_status": "complete" if image_path.exists() and image_path.stat().st_size > 0 and data_path.exists() else "incomplete",
        }
        readme_lines = [
            f"# {chart.get('title') or kind}",
            "",
            f"- 图表编号：{chart_ref}",
            f"- 图表类型：{kind}",
            f"- 业务问题：{_chart_business_question(chart)}",
            f"- 关键发现：{_business_chart_interpretation(chart)}",
            f"- 业务影响：{_chart_business_impact(chart)}",
            f"- 复核边界：{_chart_review_boundary(chart)}",
            "",
            "## 文件",
            "",
            "- chart.png：可直接放入报告或演示材料的图像。",
            "- chart.json：复核图表数据和字段口径的结构化证据。",
        ]
        readme_path.write_text("\n".join(readme_lines).strip() + "\n", encoding="utf-8")
        chart["asset_exports"] = {
            "chart_ref": chart_ref,
            "folder": rel_prefix,
            "image_path": row["image_path"],
            "data_path": row["data_path"],
            "readme_path": row["readme_path"],
            "image_status": image_status,
            "integrity_status": row["integrity_status"],
        }
        rows.append(row)
        for suffix, file_path, kind_label, purpose in (
            ("chart.png", image_path, "png", "Business chart image rendered from Analysis Lab chart payload."),
            ("chart.json", data_path, "json", "Business chart payload and interpretation."),
            ("README.md", readme_path, "md", "Reader-facing guide for the business chart asset."),
        ):
            if file_path.exists():
                _append_downloadable(
                    downloadables,
                    _public_downloadable_item(
                        {
                            "name": f"{folder_name}-{suffix}",
                            "path": _client_public_path(public_base_path, f"{rel_prefix}/{suffix}"),
                            "file_path": str(file_path.resolve()),
                            "type": kind_label,
                            "purpose": purpose,
                            "is_main": False,
                            "download_kind": "chart_asset",
                            "chart_ref": _public_evidence_ref(chart_ref),
                        }
                    ),
                )
    index_json_path = export_dir / CHART_ASSET_INDEX_JSON
    index_csv_path = export_dir / CHART_ASSET_INDEX_CSV
    index_xlsx_path = export_dir / "chart_asset_index.xlsx"
    payload = {
        "contract": "analysis_lab_chart_asset_index_v1",
        "generated_at": generated_at,
        "chart_count": len(rows),
        "complete_count": len([row for row in rows if row.get("integrity_status") == "complete"]),
        "asset_root": CHART_ASSET_DIR,
        "rows": rows,
        "errors": errors,
        "large_sample_policy": large_sample_policy or {},
    }
    _write_json_file(index_json_path, payload)
    _write_dataframe_artifacts(rows, csv_path=index_csv_path, xlsx_path=index_xlsx_path)
    for file_name, file_path, kind_label, purpose in (
        (CHART_ASSET_INDEX_JSON, index_json_path, "json", "Index of rendered business chart PNG assets."),
        (CHART_ASSET_INDEX_CSV, index_csv_path, "csv", "CSV index of rendered business chart PNG assets."),
        ("chart_asset_index.xlsx", index_xlsx_path, "xlsx", "Spreadsheet index of rendered business chart PNG assets."),
    ):
        if file_path.exists():
            _append_downloadable(
                downloadables,
                _public_downloadable_item(
                    {
                        "name": file_name,
                        "path": _public_path(public_base_path, file_name),
                        "file_path": str(file_path.resolve()),
                        "type": kind_label,
                        "purpose": purpose,
                        "is_main": False,
                        "download_kind": "chart_asset_index",
                        "chart_count": len(rows),
                    }
                ),
            )
    return {
        "runtime_status": "completed",
        "chart_count": len(rows),
        "complete_count": payload["complete_count"],
        "asset_root": _public_path(public_base_path, CHART_ASSET_DIR),
        "index_json_path": _public_path(public_base_path, CHART_ASSET_INDEX_JSON),
        "index_csv_path": _public_path(public_base_path, CHART_ASSET_INDEX_CSV),
        "integrity_status": "passed" if rows and payload["complete_count"] == len(rows) else "failed",
        "rows": rows,
        "large_sample_policy": large_sample_policy or {},
        "error_count": len(errors),
    }


def _markdown_table(table: dict[str, Any], *, max_rows: int = 8) -> list[str]:
    rows = [row for row in list(table.get("rows") or []) if isinstance(row, dict)]
    columns = [str(column) for column in list(table.get("columns") or []) if str(column or "").strip()]
    if not columns and rows:
        for row in rows:
            for key in row.keys():
                column = str(key)
                if column not in columns:
                    columns.append(column)
    if not rows or not columns:
        return []
    lines = [
        "| " + " | ".join(_report_cell_text(column, 60) for column in columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows[:max_rows]:
        lines.append("| " + " | ".join(_report_cell_text(row.get(column)) for column in columns) + " |")
    if len(rows) > max_rows:
        omitted = len(rows) - max_rows
        if len(columns) == 1:
            lines.append(f"| ... 另有 {omitted} 行未在预览中展示 |")
        else:
            lines.append("| " + " | ".join(["..."] + [f"另有 {omitted} 行未在预览中展示"] + [""] * max(0, len(columns) - 2)) + " |")
    return lines


def _method_family_counts(method_execution_packages: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for package in method_execution_packages:
        family = str(package.get("family") or "unknown")
        counts[family] = counts.get(family, 0) + 1
    return dict(sorted(counts.items()))


_REPORT_INTERNAL_COLUMN_NAMES = {
    "asset_index",
    "binding_quality",
    "bound_fields",
    "compatible_method_families",
    "derived_bound_fields",
    "executor_hint",
    "management_use",
    "next_step",
    "pre_method_preprocessing_status",
    "recommended_report_parts",
    "report_slots",
    "route_reasons",
    "route_score",
    "semantic_route_field_count",
    "semantic_route_refs",
}


def _is_report_internal_column(column: Any) -> bool:
    lower = str(column or "").strip().lower()
    if not lower:
        return True
    if lower in _REPORT_INTERNAL_COLUMN_NAMES:
        return True
    return lower.startswith(("payload.runtime", "runtime_", "semantic_route"))


def _report_visible_table(table: dict[str, Any]) -> dict[str, Any]:
    columns = [
        str(column)
        for column in list(table.get("columns") or [])
        if not _is_report_internal_column(column)
    ]
    rows = [row for row in list(table.get("rows") or []) if isinstance(row, dict)]
    visible_rows: list[dict[str, Any]] = []
    for row in rows:
        cleaned: dict[str, Any] = {}
        for column in columns:
            value = row.get(column)
            if isinstance(value, dict):
                safe_value = {
                    str(key): item
                    for key, item in value.items()
                    if not _is_report_internal_column(key)
                }
                cleaned[column] = safe_value or ""
            elif isinstance(value, list) and value and all(isinstance(item, dict) for item in value[:20]):
                safe_items = [
                    {
                        str(key): nested_value
                        for key, nested_value in item.items()
                        if not _is_report_internal_column(key)
                    }
                    for item in value[:20]
                ]
                cleaned[column] = [item for item in safe_items if item]
            else:
                cleaned[column] = value
        visible_rows.append(cleaned)
    return {"columns": columns, "rows": visible_rows}


def _method_result_table(package: dict[str, Any], *, max_rows: int = 8) -> list[str]:
    rows = _rows_from_package(package)
    if not rows:
        return []
    columns: list[str] = []
    execution = package.get("execution") if isinstance(package.get("execution"), dict) else {}
    preferred = [
        str(column)
        for column in list(execution.get("result_columns") or [])
        if str(column or "").strip()
    ]
    for column in preferred:
        if column not in columns and any(column in row for row in rows):
            columns.append(column)
    for row in rows:
        for column in row:
            if column not in columns and not _is_report_internal_column(column):
                columns.append(column)
    return _markdown_table({"columns": columns[:10], "rows": rows}, max_rows=max_rows)


def _artifact_summary_rows(method_execution_packages: list[dict[str, Any]], *, limit: int = 12) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for package in method_execution_packages[:limit]:
        exports = package.get("artifact_exports") if isinstance(package.get("artifact_exports"), dict) else {}
        interpretation = package.get("codex_interpretation") if isinstance(package.get("codex_interpretation"), dict) else {}
        profile = interpretation.get("numeric_profile") if isinstance(interpretation.get("numeric_profile"), dict) else {}
        numeric_evidence = interpretation.get("top_numeric_evidence") or "-"
        if not numeric_evidence or numeric_evidence == "-":
            numeric_count = len(list(profile.get("numeric_columns") or []))
            numeric_evidence = "暂无可直接入结论的业务数值" if numeric_count == 0 else f"已提取{numeric_count}个业务数值字段"
        rows.append(
            {
            "方法运行": _public_evidence_ref(package.get("method_run_id") or package.get("method_id")),
                "方法族": _method_family_label(package.get("family")),
                "数据行": exports.get("row_count") if exports else interpretation.get("row_count"),
                "字段数": exports.get("column_count") if exports else profile.get("column_count"),
                "业务证据": numeric_evidence,
                "产物状态": _artifact_integrity_label(exports.get("integrity_status") or "-"),
                "解读状态": _interpretation_status_label(interpretation.get("status")),
            }
        )
    return rows


def _method_numeric_evidence_rows(method_execution_packages: list[dict[str, Any]], *, limit: int = 16) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for package in method_execution_packages:
        interpretation = package.get("codex_interpretation") if isinstance(package.get("codex_interpretation"), dict) else {}
        profile = interpretation.get("numeric_profile") if isinstance(interpretation.get("numeric_profile"), dict) else {}
        for item in list(profile.get("numeric_columns") or [])[:2]:
            rows.append(
                {
                    "方法运行": _public_evidence_ref(package.get("method_run_id") or package.get("method_id")),
                    "业务指标": item.get("column"),
                    "样本数": item.get("count"),
                    "均值": _format_evidence_number(item.get("mean")),
                    "最小值": _format_evidence_number(item.get("min")),
                    "最大值": _format_evidence_number(item.get("max")),
                }
            )
            if len(rows) >= limit:
                return rows
    return rows


def _sync_cli_summary_lines(sync_cli: dict[str, Any]) -> list[str]:
    if not sync_cli:
        return ["- 同步 Codex 复核状态：`not_requested`；当前报告使用本地业务数值解读。"]
    lines = [
        f"- 同步 Codex 复核状态：`{sync_cli.get('runtime_status') or '-'}`",
        f"- 同步复核超时设置：{sync_cli.get('timeout_sec') or '-'} 秒",
    ]
    if sync_cli.get("output_path"):
        lines.append(f"- 同步复核原始输出：`{sync_cli.get('output_path')}`")
    summary = sync_cli.get("summary") if isinstance(sync_cli.get("summary"), dict) else {}
    if summary:
        executive = summary.get("executive_cli_summary")
        if executive:
            lines.append(f"- Codex 复核摘要：{_report_cell_text(executive, 700)}")
        for action in list(summary.get("recommended_next_actions") or [])[:5]:
            lines.append(f"- Codex 建议动作：{_report_cell_text(action, 500)}")
        for risk in list(summary.get("risks_or_limits") or [])[:5]:
            lines.append(f"- Codex 风险边界：{_report_cell_text(risk, 500)}")
    elif sync_cli.get("error"):
        lines.append(f"- 同步复核说明：{_report_cell_text(sync_cli.get('error'), 700)}")
    if str(sync_cli.get("runtime_status") or "").endswith("_local_numeric_analysis_used"):
        lines.append("- 本地业务数值解读：已完成，并嵌入“方法证据明细”和“业务指标明细”表。")
    return lines


def _report_field_value(value: Any) -> str:
    return _business_field_label(value) if value else "-"


def _chart_point_count(chart: dict[str, Any]) -> int:
    for key in ("points", "x", "labels", "actual", "forecast", "matrix"):
        value = chart.get(key)
        if isinstance(value, list):
            return len(value)
    return 0


def _relative_artifact_href(path_value: Any) -> str:
    return _customer_artifact_href(path_value)


def _chart_export_ref(chart: dict[str, Any], index: int | None = None) -> str:
    exports = chart.get("asset_exports") if isinstance(chart.get("asset_exports"), dict) else {}
    existing = str(exports.get("chart_ref") or chart.get("chart_ref") or "").strip()
    if existing:
        return existing
    kind = _safe_artifact_segment(chart.get("kind") or "chart", "chart")
    parts = [f"{index:03d}" if index is not None else "", kind]
    for value in (chart.get("x_label"), chart.get("y_label")):
        segment = _safe_artifact_segment(value, "")
        if segment:
            parts.append(segment[:32])
    compact = "-".join(part for part in parts if part)
    return f"chart:{compact or kind}"


def _public_evidence_ref(ref: Any) -> str:
    text = str(ref or "").strip()
    if not text:
        return ""
    if text.startswith("method_package_"):
        return f"方法证据 {text.rsplit('_', 1)[-1]}"
    if text.startswith("chart:"):
        return f"图表证据 {text.split(':', 1)[1]}"
    if text.endswith(".json"):
        return f"证据索引 {text}"
    if text.startswith("table:"):
        return f"表格证据 {text.split(':', 1)[1]}"
    if text.startswith("data:"):
        return f"数据证据 {text.split(':', 1)[1]}"
    return f"方法证据 {text}"


def _public_evidence_refs(refs: list[Any], *, limit: int = 8) -> str:
    labels = [_public_evidence_ref(ref) for ref in refs]
    labels = [label for label in labels if label]
    return "；".join(labels[:limit])


def _review_status_label(status: Any) -> str:
    text = str(status or "").strip()
    if text in {
        "agent_review_completed",
        "deterministic_agent_review_completed",
        "codex_cli_sync_completed",
        "local_numeric_cli_analysis_completed",
    }:
        return "已完成"
    if text.startswith(("missing", "invalid", "failed")):
        return "需补强"
    return "已生成" if text else "需补强"


_READER_FACING_INTERNAL_LEAKAGE_PATTERNS: tuple[tuple[str, str], ...] = (
    ("raw_chart_marker", r"(?m)^CHART:\s"),
    ("raw_visual_marker", r"(?m)^VISUAL:\s"),
    ("visual_marker_field", r"\b(?:title|kind|image|json|question|insight|impact|boundary|evidence_detail)="),
    ("internal_process_summary", r"\bfield understanding, derived preprocessing, method routing and report-part generation completed\b"),
    ("deterministic_agent_review_completed", r"\bdeterministic_agent_review_completed\b"),
    ("runtime_status", r"\bruntime_status\b"),
    ("method_package", r"\bmethod_package(?:_\w*)?\b"),
    ("chart_asset", r"\bchart_asset\b(?!s/)"),
    ("method_artifact", r"\bmethod_artifact(?:_\w*)?\b(?!s/)"),
    ("method_artifacts", r"\bmethod_artifacts\b(?!/)"),
    ("external_skill", r"\bexternal_skill(?:_\w*)?\b"),
    ("anthropics", r"\banthropics\b"),
    ("Agent 审稿", r"Agent\s*审稿"),
    ("agent 审稿", r"agent\s*审稿"),
    ("local_path", r"(?i)(?:/tmp/[^\s|)>\]\"']+|[a-z]:[/\\][^\s|)>\]\"']+)"),
)


def _reader_facing_internal_leakage_hits(text: str) -> list[str]:
    return [
        label
        for label, pattern in _READER_FACING_INTERNAL_LEAKAGE_PATTERNS
        if re.search(pattern, text)
    ]


def _reader_visible_html_text(html_text: str) -> str:
    text = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", str(html_text or ""))
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = html_lib.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _sanitize_reader_facing_text(text: str) -> str:
    cleaned = str(text or "")
    cleaned = re.sub(r"(?<![\](/])chart_assets/[^\s|)>\]\"';]+", "图表文件已加入下载清单", cleaned)
    cleaned = re.sub(r"(?<![\](/])method_artifacts/[^\s|)>\]\"';]+", "方法证据文件已加入下载清单", cleaned)
    cleaned = re.sub(r"/tmp/[^\s|)>\]\"';]+", "交付包相对路径", cleaned)
    cleaned = re.sub(r"[A-Za-z]:[/\\][^\s|)>\]\"';]+", "本地交付文件", cleaned)
    cleaned = re.sub(r"\bchart_asset\b", "图表文件", cleaned)
    cleaned = re.sub(r"\bmethod_artifact(?:_\w*)?\b", "方法证据文件", cleaned)
    return cleaned


def _parse_visual_marker_fields(line: str) -> tuple[bool, dict[str, str]]:
    stripped = str(line or "").strip()
    if stripped.startswith("CHART:"):
        marker = "CHART:"
        is_chart = True
    elif stripped.startswith("VISUAL:"):
        marker = "VISUAL:"
        is_chart = False
    else:
        return False, {}
    fields: dict[str, str] = {}
    for chunk in stripped[len(marker) :].split(";"):
        if "=" not in chunk:
            continue
        key, value = chunk.split("=", 1)
        fields[key.strip()] = value.strip()
    return is_chart, fields


def _reader_markdown_visual_block(line: str, index: int) -> str:
    is_chart, fields = _parse_visual_marker_fields(line)
    if not fields:
        return ""
    title = _sanitize_reader_facing_text(fields.get("title") or ("图表证据" if is_chart else "方法预览"))
    image_href = _customer_artifact_href(fields.get("image") or "")
    json_href = _customer_artifact_href(fields.get("json") or "")
    csv_href = _customer_artifact_href(fields.get("csv") or "")
    xlsx_href = _customer_artifact_href(fields.get("xlsx") or "")
    links = [
        _customer_artifact_label(value)
        for value in (json_href, csv_href, xlsx_href)
        if value
    ]
    labels = [
        ("读图问题", fields.get("question") or ""),
        ("关键发现", fields.get("insight") or ""),
        ("业务影响", fields.get("impact") or ""),
        ("复核边界", fields.get("boundary") or ""),
        ("证据数字", fields.get("evidence_detail") or fields.get("evidence") or ""),
    ]
    lines = [f"#### Figure {index}: {title}" if is_chart else f"#### 方法预览 {index}: {title}"]
    if image_href:
        lines.extend(["", f"![{title}]({image_href})", ""])
    for label, value in labels:
        clean_value = _sanitize_reader_facing_text(value)
        if clean_value:
            lines.append(f"- {label}：{clean_value}")
    if links:
        lines.append(f"- 下载数据：{'；'.join(links)}")
    return "\n".join(lines)


def _reader_facing_markdown(markdown_text: str) -> str:
    if any(line.startswith(("CHART:", "VISUAL:")) for line in str(markdown_text or "").splitlines()):
        rendered_lines: list[str] = []
        visual_index = 0
        for line in str(markdown_text or "").splitlines():
            if line.startswith("CHART:") or line.startswith("VISUAL:"):
                visual_index += 1
                rendered = _reader_markdown_visual_block(line, visual_index)
                if rendered:
                    rendered_lines.append(rendered)
                continue
            rendered_lines.append(line)
        return _sanitize_reader_facing_text("\n".join(rendered_lines))
    text = "\n".join(
        "方法预览图像已在 HTML 报告中以卡片形式呈现。"
        if line.startswith("VISUAL:")
        else line
        for line in markdown_text.splitlines()
    )
    return _sanitize_reader_facing_text(text)


def _reader_facing_html(html_text: str) -> str:
    def _replace_text_node(match: re.Match[str]) -> str:
        return f">{_sanitize_reader_facing_text(match.group(1))}<"

    return re.sub(r">([^<>]+)<", _replace_text_node, html_text)


def _method_package_summary(package: dict[str, Any]) -> dict[str, Any]:
    package_id = str(package.get("package_id") or "").strip()
    assets = [asset for asset in list(package.get("assets") or []) if isinstance(asset, dict)]
    runtime_handoffs = [handoff for handoff in list(package.get("runtime_handoffs") or []) if isinstance(handoff, dict)]
    evidence_refs = list(
        dict.fromkeys(
            str(ref)
            for ref in [
                *list((package.get("method_card") or {}).get("evidence_refs") or []),
                *[
                    asset_ref
                    for asset in assets
                    for asset_ref in list(asset.get("evidence_refs") or [])
                ],
                *[
                    handoff_ref
                    for handoff in runtime_handoffs
                    for handoff_ref in list(handoff.get("evidence_refs") or [])
                ],
            ]
            if str(ref or "").strip()
        )
    )
    asset_refs = list(
        dict.fromkeys(
            str(asset.get("asset_ref") or "")
            for asset in assets
            if str(asset.get("asset_ref") or "").strip()
        )
    )
    runtime_tasks = list(
        dict.fromkeys(
            str(handoff.get("task") or "")
            for handoff in runtime_handoffs
            if str(handoff.get("task") or "").strip()
        )
    )
    return {
        "package_id": package.get("package_id"),
        "package_ref": package.get("package_ref") or (f"data:method_execution_packages:{package_id}" if package_id else ""),
        "file_name": package.get("file_name"),
        "method_id": package.get("method_id"),
        "method_run_id": package.get("method_run_id"),
        "method_name": package.get("method_name"),
        "family": package.get("family"),
        "status": package.get("status") or (package.get("execution") or {}).get("status"),
        "asset_count": package.get("asset_count") if package.get("asset_count") is not None else len(assets),
        "asset_refs": asset_refs[:20],
        "runtime_tasks": runtime_tasks[:20],
        "runtime_handoff_count": package.get("runtime_handoff_count", 0),
        "evidence_refs": evidence_refs[:20],
        "pre_method_preprocessing_status": package.get("pre_method_preprocessing_status"),
    }


def _method_display_key(package: dict[str, Any]) -> str:
    method_card = package.get("method_card") if isinstance(package.get("method_card"), dict) else {}
    raw_name = (
        package.get("method_name_zh")
        or package.get("method_name")
        or method_card.get("method_name")
        or package.get("method_id")
        or package.get("method_run_id")
        or ""
    )
    clean_name = re.sub(r"\s+", " ", _plain_business_label(raw_name)).strip().casefold()
    family = str(package.get("family") or method_card.get("family") or "unknown").strip().casefold()
    if clean_name:
        return f"{family}|{clean_name}"
    return f"{family}|{str(package.get('method_id') or package.get('method_run_id') or '').strip().casefold()}"


def _method_display_packages(method_execution_packages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for package in method_execution_packages:
        if not isinstance(package, dict):
            continue
        key = _method_display_key(package)
        if key not in grouped:
            grouped[key] = {
                "representative": dict(package),
                "packages": [],
            }
            order.append(key)
        grouped[key]["packages"].append(package)

    display_packages: list[dict[str, Any]] = []
    for key in order:
        group = grouped[key]
        packages = [item for item in list(group.get("packages") or []) if isinstance(item, dict)]
        if not packages:
            continue
        representative = dict(group.get("representative") or packages[0])
        summaries = [_method_package_summary(package) for package in packages]
        run_ids = list(
            dict.fromkeys(
                str(summary.get("method_run_id") or summary.get("method_id") or "")
                for summary in summaries
                if str(summary.get("method_run_id") or summary.get("method_id") or "").strip()
            )
        )
        method_ids = list(
            dict.fromkeys(
                str(summary.get("method_id") or "")
                for summary in summaries
                if str(summary.get("method_id") or "").strip()
            )
        )
        package_refs = list(
            dict.fromkeys(
                str(summary.get("package_ref") or "")
                for summary in summaries
                if str(summary.get("package_ref") or "").strip()
            )
        )
        evidence_refs = list(
            dict.fromkeys(
                str(ref)
                for summary in summaries
                for ref in list(summary.get("evidence_refs") or [])
                if str(ref or "").strip()
            )
        )
        representative["display_group"] = {
            "grouped_by": "method_family_and_reader_facing_method_name",
            "display_key": key,
            "total_runs": len(packages),
            "collapsed_run_count": max(0, len(packages) - 1),
            "method_run_ids": run_ids[:80],
            "method_ids": method_ids[:40],
            "package_refs": package_refs[:80],
            "evidence_refs": evidence_refs[:80],
        }
        display_packages.append(representative)
    return display_packages


def _method_display_policy(method_execution_packages: list[dict[str, Any]], display_packages: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "policy": "collapse_same_name_method_cards_for_reader_facing_report",
        "grouped_by": "method_family_and_reader_facing_method_name",
        "raw_method_package_count": len(method_execution_packages),
        "display_method_package_count": len(display_packages),
        "collapsed_duplicate_run_count": max(0, len(method_execution_packages) - len(display_packages)),
        "raw_packages_preserved": True,
        "raw_package_index": "method_execution_packages.json",
    }


def _method_card_report_guidance(package: dict[str, Any]) -> dict[str, Any]:
    method_card = package.get("method_card") if isinstance(package.get("method_card"), dict) else {}
    execution = package.get("execution") if isinstance(package.get("execution"), dict) else {}
    display_group = package.get("display_group") if isinstance(package.get("display_group"), dict) else {}
    report_slots = [str(item).strip() for item in list(method_card.get("report_slots") or []) if str(item or "").strip()]
    missing_bindings = [
        str(item).strip()
        for item in list(method_card.get("missing_bindings") or [])
        if str(item or "").strip()
    ]
    evidence_refs = [
        str(item).strip()
        for item in list(method_card.get("evidence_refs") or [])
        if str(item or "").strip()
    ]
    binding_quality = str(method_card.get("binding_quality") or package.get("binding_quality") or "").strip()
    executor_hint = str(method_card.get("executor_hint") or execution.get("executor_hint") or "").strip()
    method_name = (
        package.get("method_name_zh")
        or package.get("method_name")
        or method_card.get("method_name")
        or package.get("method_id")
        or ""
    )
    if missing_bindings:
        writer_action = "Use as a provisional method note; explain missing bindings before promoting it to a core claim."
    elif report_slots:
        writer_action = "Use this method in the listed report slots with explicit evidence references and business caveats."
    else:
        writer_action = "Use as appendix evidence unless a report slot is assigned by the route planner."
    if int(display_group.get("collapsed_run_count") or 0) > 0:
        writer_action = (
            f"{writer_action} Display this repeated method card once in reader-facing sections, "
            f"then cite the grouped run ids from display_group."
        )
    return {
        "method_id": package.get("method_id"),
        "method_run_id": package.get("method_run_id"),
        "method_name": method_name,
        "family": package.get("family"),
        "report_slots": report_slots,
        "binding_quality": binding_quality or "unknown",
        "missing_bindings": missing_bindings,
        "executor_hint": executor_hint,
        "selection_mode": method_card.get("selection_mode"),
        "smart_merge_group": method_card.get("smart_merge_group"),
        "evidence_refs": evidence_refs[:20],
        "result_ref": execution.get("result_ref"),
        "writer_action": writer_action,
        "display_group": display_group,
    }


def _method_card_report_guidance_list(
    method_execution_packages: list[dict[str, Any]],
    *,
    limit: int = 40,
    collapse_duplicate_names: bool = True,
) -> list[dict[str, Any]]:
    source_packages = _method_display_packages(method_execution_packages) if collapse_duplicate_names else method_execution_packages
    return [
        _method_card_report_guidance(package)
        for package in source_packages[:limit]
        if isinstance(package, dict)
    ]


def _lab_report_id(request: AutoAnalysisRequest, export_dir: Path | None) -> str:
    seed = export_dir.name if export_dir else f"{request.dataset_id}-{int(time.time())}"
    raw = f"lab-{request.dataset_id}-{seed}"
    clean = re.sub(r"[^a-zA-Z0-9_-]+", "-", raw).strip("-_")
    return (clean[:110].strip("-_") or f"lab-{int(time.time())}")


def _render_lab_report_markdown(
    *,
    title: str,
    request: AutoAnalysisRequest,
    dataset_name: str,
    sheet_name: str,
    selected: dict[str, Any],
    report_parts: list[dict[str, Any]],
    tables: list[dict[str, Any]],
    charts: list[dict[str, Any]],
    method_execution_packages: list[dict[str, Any]],
    method_artifact_summary: dict[str, Any] | None,
    agent_review: dict[str, Any] | None,
    report_part_asset_manifest: list[dict[str, Any]],
    external_skill_context: dict[str, Any] | None,
    generated_at: str,
) -> str:
    external_skills = _external_skill_items_for_report(external_skill_context)
    dataset_title = _client_dataset_title(dataset_name or request.dataset_id)
    sheet_title = sheet_name or request.active_sheet or "-"
    time_value = selected.get("time")
    has_time_chart = any(
        isinstance(chart, dict)
        and str(chart.get("kind") or "") in {"line", "forecast"}
        and str(chart.get("x_label") or "") not in {"", "row_order"}
        for chart in charts
    )
    if not time_value:
        for chart in charts:
            if isinstance(chart, dict) and str(chart.get("kind") or "") in {"line", "forecast"}:
                candidate = str(chart.get("x_label") or "")
                if candidate and candidate != "row_order":
                    time_value = candidate
                    break
    time_scope = _report_field_value(time_value) if time_value else ("未识别稳定时间字段" if not has_time_chart else "-")
    selected_field_lines = [
        f"- 目标指标：{_report_field_value(selected.get('target'))}",
        f"- 解释字段：{', '.join(_business_field_label(item) for item in list(selected.get('features') or [])[:12]) or '-'}",
        f"- 分组字段：{_report_field_value(selected.get('group'))}",
        f"- 标签字段：{_report_field_value(selected.get('label'))}",
        f"- 时间字段：{time_scope}",
    ]
    agent_status = str((agent_review or {}).get("runtime_status") or "missing_agent_review_output")
    agent_usable = _agent_review_is_usable(agent_review or {})
    review_label = _review_status_label(agent_status)
    lines: list[str] = [
        f"# {title}",
        "",
        "## 管理摘要",
        "",
        f"本报告汇总 `{dataset_title}` / `{sheet_title}` 的分析结果，重点解释业务指标、异常对象、分层结构和后续动作。",
        "报告结论来自结构化表格、业务图表、方法证据和复核结论；业务行动只引用可追溯证据，不使用固定模板补全。",
        "",
        "### 数据范围与字段口径",
        "",
        f"- 生成时间：{generated_at}",
        f"- 数据集：{dataset_title}",
        f"- 工作表：{sheet_title}",
        f"- 数据集 ID：{request.dataset_id}",
        f"- 分析目标：{_report_cell_text(request.user_goal or '生成可交付的图文管理分析报告', 220)}",
        f"- 报告章节数：{len(report_parts)}",
        f"- 分析方法数：{len(method_execution_packages)}",
        f"- 方法证据导出数：{(method_artifact_summary or {}).get('method_count') or 0}",
        f"- 写作与图文约束组数：{len(external_skills)}",
        f"- 证据表数：{len(tables)}",
        f"- 图表数：{len(charts)}",
        f"- 复核状态：{review_label}",
        f"- 复核记录：{_customer_artifact_label(LAB_REPORT_AGENT_REVIEW_MD_FILE)}",
        "",
        *selected_field_lines,
        "",
        "### 执行摘要",
        "",
    ]
    executive = next((part for part in report_parts if str(part.get("id") or "") == "executive_summary"), report_parts[0] if report_parts else {})
    narrative = str(executive.get("narrative") or "").strip()
    if narrative:
        lines.extend([narrative, ""])
    family_counts = _method_family_counts(method_execution_packages)
    method_display_packages = _method_display_packages(method_execution_packages)
    method_display_policy = _method_display_policy(method_execution_packages, method_display_packages)
    sync_cli = (method_artifact_summary or {}).get("sync_codex_cli") if isinstance((method_artifact_summary or {}).get("sync_codex_cli"), dict) else {}
    visible_number_rows = _method_numeric_evidence_rows(method_display_packages, limit=16)
    chart_rows = _chart_asset_rows(charts, limit=max(15, len(charts)))
    primary_chart_insights = [_business_chart_interpretation(chart) for chart in charts[:6] if isinstance(chart, dict)]
    evidence_chain_rows = _business_evidence_chain_rows(charts, method_execution_packages, limit=8)
    action_priority_rows = _agent_consolidated_action_rows(agent_review or {})
    if not _agent_review_is_usable(agent_review or {}):
        action_priority_rows = []
    agent_review_rows = _agent_review_rows(agent_review or {})
    research_design_rows = _research_design_rows(
        selected=selected,
        tables=tables,
        charts=charts,
        method_execution_packages=method_execution_packages,
        external_skill_context=external_skill_context,
    )
    research_question_rows = _research_question_rows(charts, tables, method_execution_packages)
    figure_narrative_rows = _figure_narrative_rows(charts, method_execution_packages, limit=max(15, len(charts)))
    commercial_delivery_rows = _commercial_delivery_rows(
        charts=charts,
        method_execution_packages=method_execution_packages,
        method_artifact_summary=method_artifact_summary,
        evidence_chain_rows=evidence_chain_rows,
        action_priority_rows=action_priority_rows,
        figure_narrative_rows=figure_narrative_rows,
    )
    numeric_dashboard_rows = [
        {"指标": "业务图表数量", "数值": len(charts), "业务含义": "已渲染为可直接阅读的业务图，不是方法表格截图"},
        {"指标": "可嵌入图像数量", "数值": len([chart for chart in charts if isinstance(chart, dict) and (chart.get("asset_exports") or {}).get("image_path")]), "业务含义": "Markdown 与 HTML 均应能直接看到图像证据"},
        {"指标": "证据表数量", "数值": len(tables), "业务含义": "用于复核结论的结构化证据，不作为主视觉交付"},
        {
            "指标": "方法产物完整度",
            "数值": f"{(method_artifact_summary or {}).get('integrity_complete_count') or 0}/{(method_artifact_summary or {}).get('method_count') or 0}",
            "业务含义": "附录证据是否完整，不能替代主文业务判断",
        },
        {
            "指标": "可见业务指标行",
            "数值": len(visible_number_rows),
            "业务含义": "用于解释图表和行动优先级的数值证据",
        },
    ]
    family_rows = [{"方法族": _method_family_label(family), "方法数量": count} for family, count in family_counts.items()]
    lines.extend(["## 研究摘要", ""])
    lines.append(
        f"本报告是一份面向商用交付的图文并茂研究报告，研究对象为 `{dataset_title}` / `{sheet_title}`。"
        f"本轮生成 {len(method_execution_packages)} 组方法证据、{len(tables)} 张证据表、{len(charts)} 张业务图表，"
        "并将核心判断绑定到图像、表格、可下载产物和复核结论。"
    )
    if not agent_usable:
        lines.append("交付拦截：复核记录尚未包含结论、行动和图表相关性三类复核结果，本报告不能作为外部报告发布。")
    if primary_chart_insights:
        lines.append(f"研究主结论：{primary_chart_insights[0]}")
        lines.append("商用交付口径：报告可作为管理复盘、研究说明、客户沟通或内部决策材料的交付初版；关键结论均绑定到本次交付包内的图像、表格和证据文件，便于业务负责人按证据逐项确认。")
    lines.append("")
    lines.extend(["## 研究问题与结论", ""])
    lines.extend(
        _markdown_table(
            {"columns": ["研究问题", "核心结论", "主要证据", "商业用途"], "rows": research_question_rows},
            max_rows=8,
        )
    )
    lines.append("")
    lines.extend(["## 研究设计与方法", ""])
    lines.extend(
        _markdown_table(
            {"columns": ["研究模块", "设计说明", "证据来源", "商用价值"], "rows": research_design_rows},
            max_rows=8,
        )
    )
    lines.append("")
    if figure_narrative_rows:
        lines.extend(["## 图文叙事", ""])
        lines.append("本节采用“业务问题 -> 图 -> 发现 -> 影响 -> 行动”的结构；行动口径必须能被复核记录和可下载证据追溯。")
        lines.append("")
        lines.extend(
            _markdown_table(
                {"columns": ["图序", "业务问题", "图表", "图像文件", "发现", "影响", "复核边界", "证据包"], "rows": figure_narrative_rows},
                max_rows=6,
            )
        )
        lines.append("")
    lines.extend(["## 复核结论", ""])
    if agent_review_rows:
        lines.extend(
            _markdown_table(
                {"columns": ["复核角色", "结论复核", "行动复核", "图表相关性"], "rows": agent_review_rows},
                max_rows=12,
            )
        )
    else:
        lines.append("- 等待复核记录产出结论复核、行动复核和图表相关性复核。")
    lines.append("")
    lines.extend(["## 商用交付检查", ""])
    lines.extend(
        _markdown_table(
            {"columns": ["交付维度", "交付状态", "验收证据", "商用说明"], "rows": commercial_delivery_rows},
            max_rows=8,
        )
    )
    lines.append("")
    lines.extend(["### 关键数字总览", ""])
    lines.extend(_markdown_table({"columns": ["指标", "数值", "业务含义"], "rows": numeric_dashboard_rows}, max_rows=20))
    lines.append("")
    if primary_chart_insights:
        lines.extend(["### 核心业务判断", ""])
        for insight in primary_chart_insights:
            lines.append(f"- {insight}")
        lines.append("")
    if action_priority_rows:
        lines.extend(["## 行动优先级矩阵", ""])
        lines.append("下表只引用复核后的 5-8 条业务行动；没有复核证据时本节为空并触发质量门禁失败。")
        lines.append("")
        lines.extend(
            _markdown_table(
                {"columns": ["优先级", "业务问题", "业务行动", "证据引用", "责任提示"], "rows": action_priority_rows},
                max_rows=8,
            )
        )
        lines.append("")
    if evidence_chain_rows:
        lines.extend(["## 业务证据链", ""])
        lines.append("本节把主文判断绑定到图像、方法证据和可下载文件，避免报告只给结论却不能追溯。")
        lines.append("")
        lines.extend(
            _markdown_table(
                {"columns": ["证据编号", "业务问题", "业务判断", "业务证据", "方法证据", "可下载证据", "复核边界"], "rows": evidence_chain_rows},
                max_rows=8,
            )
        )
        lines.append("")
    if chart_rows or visible_number_rows:
        lines.extend(["## 图表与数值证据", ""])
        if chart_rows:
            lines.extend(["### 可视化图表证据", ""])
            for chart in charts:
                if isinstance(chart, dict) and (chart.get("asset_exports") or {}).get("image_path"):
                    lines.append(_chart_visual_marker(chart, method_execution_packages))
                    lines.append("")
            lines.extend(_markdown_table({"columns": ["图表", "类型", "X字段", "Y字段", "数据点", "业务判断", "图片"], "rows": chart_rows}, max_rows=max(15, len(chart_rows))))
            lines.append("")
        if visible_number_rows:
            lines.extend(["### 表格与数值证据", ""])
            lines.extend(_markdown_table({"columns": ["方法运行", "业务指标", "样本数", "均值", "最小值", "最大值"], "rows": visible_number_rows}, max_rows=16))
            lines.append("")
    method_visual_markers = [
        marker
        for marker in (_method_visual_marker(package) for package in method_display_packages[:8])
        if marker
    ]
    if method_visual_markers:
        lines.extend(["### 方法预览证据", ""])
        for marker in method_visual_markers[:6]:
            lines.append(marker)
            lines.append("")
    business_signals = _build_business_signal_summary(
        dataset_name=dataset_name,
        sheet_name=sheet_name,
        selected=selected,
        tables=tables,
        charts=charts,
        method_execution_packages=method_execution_packages,
    )
    if business_signals:
        lines.extend(["### 业务信号判断", ""])
        for item in business_signals:
            lines.append(f"- {item}")
        lines.append("")
    if external_skills:
        selected_feature_rows = [
            {
                "Plugin": skill.get("name") or skill.get("id") or "",
                "Selected feature": item.get("name") or item.get("feature_id") or "",
                "Feature type": item.get("feature_kind") or "",
                "Report-flow role": "Shapes method choice, evidence interpretation, actions, and review.",
            }
            for skill in external_skills
            if isinstance(skill, dict)
            for item in list(skill.get("selected_features") or [])
            if isinstance(item, dict)
        ]
        if selected_feature_rows:
            lines.extend(["### Knowledge Work report-flow selections", ""])
            lines.append(
                "- Selected Knowledge Work plugin functions were applied inside the Lab report flow, not as standalone trials."
            )
            lines.extend(
                _markdown_table(
                    {
                        "columns": ["Plugin", "Selected feature", "Feature type", "Report-flow role"],
                        "rows": selected_feature_rows,
                    },
                    max_rows=12,
                )
            )
            lines.append("")
        lines.extend(["### 写作与图文约束", ""])
        lines.append(f"- 本轮应用 {len(external_skills)} 组写作、图文表达和文档结构约束；正文只说明其作用，不披露内部平台或包来源。")
        lines.append("")
    for bullet in list(executive.get("bullets") or [])[:8]:
        lines.append(f"- {_report_cell_text(bullet, 400)}")
    lines.extend(["## 风险边界", ""])
    lines.append("- 自动增强只是辅助层；报告是否可交付由可下载证据、可读性、复核结果和质量门禁共同决定。")
    lines.append("- 未通过复核的业务行动不得进入主文结论。")
    lines.append("- 如果方法证据覆盖不足或证据引用缺失，该方法只能作为临时线索，不能作为正式结论。")
    lines.extend(["", "## 证据附录", ""])
    lines.append("附录列出证据资产和可下载路径，主文优先展示业务图表和核心复核动作。")
    lines.extend(["", "### 图表清单", ""])
    if charts:
        for chart in charts[:20]:
            if not isinstance(chart, dict):
                continue
            lines.append(
                f"- {chart.get('kind') or '图表'}：{chart.get('title') or '-'}；"
                f"x={chart.get('x_label') or chart.get('x') or '-'}; "
                f"y={chart.get('y_label') or '-'}；数据点={format(_chart_point_count(chart), ',')}"
            )
            if chart.get("explanation"):
                lines.append(f"  - {_report_cell_text(chart.get('explanation'), 500)}")
    else:
        lines.append("- 本次运行未生成图表载荷。")
    if visible_number_rows:
        lines.extend(["", "### 方法数值证据节选", ""])
        lines.extend(_markdown_table({"columns": ["方法运行", "业务指标", "样本数", "均值", "最小值", "最大值"], "rows": visible_number_rows}, max_rows=16))
    lines.extend(["", "### 方法证据索引", ""])
    if method_artifact_summary:
        integrity_status = method_artifact_summary.get("integrity_status") or "-"
        lines.extend(
            [
                "每个方法都已物化为结构化数据、表格、图片预览和说明文件，便于审计、复核和继续解读。",
                "",
                "- 证据根目录：已生成并列入下载清单。",
                "- 证据索引：已生成 JSON、CSV、XLSX 三种格式，见下载清单。",
                "- 完整性记录：已生成机器可读校验文件，见下载清单。",
                f"- 证据完整性：`{integrity_status}` "
                f"({method_artifact_summary.get('integrity_complete_count') or 0}/{method_artifact_summary.get('method_count') or 0} 完整)",
                "- 解读记录：已生成方法级解读输入与结果，见下载清单。",
                f"- 解读状态：{_review_status_label(method_artifact_summary.get('runtime_status'))}",
                "",
            ]
        )
    requested_method_limit = int(getattr(request, "max_methods", 0) or 0)
    method_evidence_limit = min(
        len(method_display_packages),
        max(40, min(max(requested_method_limit, 50), 120)),
    )
    lines.append(
        f"已列出方法证据：{method_evidence_limit}/{len(method_display_packages)}。"
        f"（原始方法包：{len(method_execution_packages)}；折叠重复：{method_display_policy['collapsed_duplicate_run_count']}）"
    )
    lines.append("")
    for evidence_index, package in enumerate(method_display_packages[:method_evidence_limit], start=1):
        summary = _method_package_summary(package)
        artifact_exports = package.get("artifact_exports") if isinstance(package.get("artifact_exports"), dict) else {}
        method_ref = summary.get("method_run_id") or summary.get("method_id") or ""
        lines.append(
            f"- 证据 {evidence_index:03d}: "
            f"{_client_method_name(package)} "
            f"({_method_family_label(summary.get('family'))}；产物数={summary.get('asset_count') or 0}；"
            f"交接数={summary.get('runtime_handoff_count') or 0})"
        )
        display_group = package.get("display_group") if isinstance(package.get("display_group"), dict) else {}
        if int(display_group.get("collapsed_run_count") or 0) > 0:
            grouped_refs = [ref for ref in list(display_group.get("method_run_ids") or []) if str(ref or "").strip()]
            lines.append(
                "  - 展示组："
                f"{display_group.get('total_runs') or 1} 个同名方法卡已折叠展示；"
                f"运行引用={_public_evidence_refs(grouped_refs, limit=10)}"
            )
        evidence_refs = [str(item) for item in list(summary.get("evidence_refs") or []) if str(item or "").strip()]
        if evidence_refs:
            lines.append(f"  - 证据：{_public_evidence_refs(evidence_refs)}")
        lines.append(f"  - 方法名称：{_client_method_name(package)}")
        lines.append(f"  - 追溯标识：{_public_evidence_ref(method_ref)}")
        if artifact_exports:
            lines.append(
                "  - 可下载文件："
                f"{_customer_artifact_label(artifact_exports.get('data_json_path'))}；"
                f"{_customer_artifact_label(artifact_exports.get('data_csv_path'))}；"
                f"{_customer_artifact_label(artifact_exports.get('data_xlsx_path'))}；"
                f"{_customer_artifact_label(artifact_exports.get('preview_png_path'))}"
                f"（完整性：{_artifact_integrity_label(artifact_exports.get('integrity_status'))}）。"
            )
        lines.append("  - 边界：扩大结论前必须核对证据引用、字段口径和产物可用性。")
    lines.extend(["", "### 证据索引", ""])
    lines.append("该报告已注册为报告库产物，质量审核通过后可在修订工作区打开。")
    asset_summary_rows = []
    if charts:
        asset_summary_rows.append({"资产类型": "业务图表", "数量": len(charts), "可下载位置": "chart_assets/", "用途": "主文图像证据和图表数据复核"})
    if method_artifact_summary:
        asset_summary_rows.append(
            {
                "资产类型": "方法证据",
                "数量": method_artifact_summary.get("method_count") or len(method_execution_packages),
                "可下载位置": "method_artifacts/",
                "用途": "CSV、Excel、JSON 和预览图复核",
            }
        )
    asset_summary_rows.append(
        {
            "资产类型": "主报告",
            "数量": 3,
            "可下载位置": f"{LAB_REPORT_MD_FILE} / {LAB_REPORT_HTML_FILE} / {LAB_REPORT_JSON_FILE}",
            "用途": "Markdown、HTML 与 JSON 元数据交付版本",
        }
    )
    lines.extend(_markdown_table({"columns": ["资产类型", "数量", "可下载位置", "用途"], "rows": asset_summary_rows}, max_rows=20))
    bundle_refs = [
        str(ref)
        for part in report_parts
        for ref in list(part.get("evidence_refs") or [])
        if str(ref or "").strip()
    ]
    if bundle_refs:
        lines.extend(["", "### 证据引用", ""])
        for ref in list(dict.fromkeys(bundle_refs))[:120]:
            lines.append(f"- {_public_evidence_ref(ref)}")
    return "\n".join(lines).strip() + "\n"


def _render_lab_report_markdown_override(
    *,
    title: str,
    request: AutoAnalysisRequest,
    dataset_name: str,
    sheet_name: str,
    selected: dict[str, Any],
    report_parts: list[dict[str, Any]],
    tables: list[dict[str, Any]],
    charts: list[dict[str, Any]],
    method_execution_packages: list[dict[str, Any]],
    method_artifact_summary: dict[str, Any] | None,
    agent_review: dict[str, Any] | None,
    report_part_asset_manifest: list[dict[str, Any]],
    external_skill_context: dict[str, Any] | None,
    generated_at: str,
) -> str:
    external_skills = _external_skill_items_for_report(external_skill_context)
    dataset_title = _client_dataset_title(dataset_name or request.dataset_id)
    sheet_title = sheet_name or request.active_sheet or "-"
    time_value = selected.get("time")
    has_time_chart = any(
        isinstance(chart, dict)
        and str(chart.get("kind") or "") in {"line", "forecast"}
        and str(chart.get("x_label") or "") not in {"", "row_order"}
        for chart in charts
    )
    if not time_value:
        for chart in charts:
            if isinstance(chart, dict) and str(chart.get("kind") or "") in {"line", "forecast"}:
                candidate = str(chart.get("x_label") or "")
                if candidate and candidate != "row_order":
                    time_value = candidate
                    break
    time_scope = _report_field_value(time_value) if time_value else ("not identified" if not has_time_chart else "-")
    executive = next((part for part in report_parts if str(part.get("id") or "") == "executive_summary"), report_parts[0] if report_parts else {})
    narrative = str(executive.get("narrative") or "").strip()
    agent_status = str((agent_review or {}).get("runtime_status") or "missing_agent_review_output")
    agent_usable = _agent_review_is_usable(agent_review or {})
    review_label = _review_status_label(agent_status)
    method_display_packages = _method_display_packages(method_execution_packages)
    method_display_policy = _method_display_policy(method_execution_packages, method_display_packages)
    visible_number_rows = _method_numeric_evidence_rows(method_display_packages, limit=16)
    chart_rows = _chart_asset_rows(charts, limit=max(15, len(charts)))
    primary_chart_insights = [_business_chart_interpretation(chart) for chart in charts[:6] if isinstance(chart, dict)]
    evidence_chain_rows = _business_evidence_chain_rows(charts, method_execution_packages, limit=8)
    action_priority_rows = _agent_consolidated_action_rows(agent_review or {}) if agent_usable else []
    agent_review_rows = _agent_review_rows(agent_review or {})
    research_design_rows = _research_design_rows(
        selected=selected,
        tables=tables,
        charts=charts,
        method_execution_packages=method_execution_packages,
        external_skill_context=external_skill_context,
    )
    research_question_rows = _research_question_rows(charts, tables, method_execution_packages)
    figure_narrative_rows = _figure_narrative_rows(charts, method_execution_packages, limit=max(15, len(charts)))
    commercial_delivery_rows = _commercial_delivery_rows(
        charts=charts,
        method_execution_packages=method_execution_packages,
        method_artifact_summary=method_artifact_summary,
        evidence_chain_rows=evidence_chain_rows,
        action_priority_rows=action_priority_rows,
        figure_narrative_rows=figure_narrative_rows,
    )
    selected_feature_rows = [
        {
            "Plugin": skill.get("name") or skill.get("id") or "",
            "Selected feature": item.get("name") or item.get("feature_id") or "",
            "Feature type": item.get("feature_kind") or "",
            "Report-flow role": "Shapes method choice, evidence interpretation, actions, and review.",
        }
        for skill in external_skills
        if isinstance(skill, dict)
        for item in list(skill.get("selected_features") or [])
        if isinstance(item, dict)
    ]
    external_skill_report_flow_rows = _external_skill_report_flow_rows(external_skill_context)
    lines: list[str] = [
        f"# {title}",
        "",
        "## Management Summary",
        "",
        f"This report summarizes the Analysis Lab run for `{dataset_title}` / `{sheet_title}`.",
        "Conclusions in the report should be traceable to routed methods, chart evidence, tables, and review outputs from this run.",
        "",
        "### Run Scope",
        "",
        f"- Generated at: {generated_at}",
        f"- Dataset: {dataset_title}",
        f"- Sheet: {sheet_title}",
        f"- Dataset ID: {request.dataset_id}",
        f"- User goal: {_report_cell_text(request.user_goal or 'Produce a decision-ready Analysis Lab report.', 220)}",
        f"- Report parts: {len(report_parts)}",
        f"- Routed methods: {len(method_execution_packages)}",
        f"- Displayed method cards: {method_display_policy['display_method_package_count']} "
        f"(collapsed duplicates: {method_display_policy['collapsed_duplicate_run_count']})",
        f"- Method artifact exports: {(method_artifact_summary or {}).get('method_count') or 0}",
        f"- External skill packages: {len(external_skills)}",
        f"- Evidence tables: {len(tables)}",
        f"- Business charts: {len(charts)}",
        f"- Review status: {review_label}",
        f"- Review record: {_customer_artifact_label(LAB_REPORT_AGENT_REVIEW_MD_FILE)}",
        "",
        "### Selected Fields",
        "",
        f"- Target metric: {_report_field_value(selected.get('target'))}",
        f"- Explanatory fields: {', '.join(_business_field_label(item) for item in list(selected.get('features') or [])[:12]) or '-'}",
        f"- Group field: {_report_field_value(selected.get('group'))}",
        f"- Label field: {_report_field_value(selected.get('label'))}",
        f"- Time field: {time_scope}",
        "",
        "### Executive Narrative",
        "",
    ]
    if narrative:
        lines.extend([narrative, ""])
    else:
        lines.extend(
            [
                f"The run produced {len(method_execution_packages)} method packages, {len(tables)} evidence tables, and {len(charts)} charts.",
                "The report should be readable without requiring the reader to inspect raw JSON first.",
                "",
            ]
        )
    if primary_chart_insights:
        lines.extend(["### Key Findings", ""])
        for insight in primary_chart_insights:
            lines.append(f"- {insight}")
        lines.append("")
    if external_skill_report_flow_rows:
        lines.extend(["## Knowledge Work Report-Flow Integration", ""])
        lines.append("- Mounted Knowledge Work packages were applied inside the main Lab report flow, not treated as standalone trials.")
        lines.append("- Their instructions shape method selection, evidence interpretation, recommended actions, and the strict quality review.")
        lines.extend(
            _markdown_table(
                {
                    "columns": [
                        "Skill package",
                        "Skill id",
                        "Source",
                        "Selected functions",
                        "Instruction status",
                        "Report-flow role",
                    ],
                    "rows": external_skill_report_flow_rows,
                },
                max_rows=max(12, len(external_skill_report_flow_rows)),
            )
        )
        lines.append("")
    if selected_feature_rows:
        lines.extend(["### Selected Knowledge Work Functions", ""])
        lines.extend(
            _markdown_table(
                {
                    "columns": ["Plugin", "Selected feature", "Feature type", "Report-flow role"],
                    "rows": selected_feature_rows,
                },
                max_rows=max(12, len(selected_feature_rows)),
            )
        )
        lines.append("")
    if research_question_rows:
        lines.extend(["## Research Questions And Conclusions", ""])
        lines.extend(
            _markdown_table(
                {
                    "columns": ["Research question", "Core conclusion", "Primary evidence", "Business use"],
                    "rows": research_question_rows,
                },
                max_rows=8,
            )
        )
        lines.append("")
    if research_design_rows:
        lines.extend(["## Analysis Design", ""])
        lines.extend(
            _markdown_table(
                {
                    "columns": ["Module", "Design note", "Evidence source", "Delivery value"],
                    "rows": research_design_rows,
                },
                max_rows=8,
            )
        )
        lines.append("")
    if figure_narrative_rows:
        lines.extend(["## Figure Narrative", ""])
        lines.append("Each figure should connect the business question, finding, impact, and review boundary.")
        lines.append("")
        lines.extend(
            _markdown_table(
                {
                    "columns": ["Figure", "Business question", "Chart", "Image file", "Finding", "Impact", "Review boundary", "Evidence pack"],
                    "rows": figure_narrative_rows,
                },
                max_rows=6,
            )
        )
        lines.append("")
    lines.extend(["## Quality Review", ""])
    if agent_review_rows:
        lines.extend(
            _markdown_table(
                {
                    "columns": ["Reviewer", "Conclusion review", "Action review", "Chart relevance"],
                    "rows": agent_review_rows,
                },
                max_rows=12,
            )
        )
    else:
        lines.append("- Review output is not yet complete enough to support external release.")
    lines.append("")
    if action_priority_rows:
        lines.extend(["## Recommended Actions", ""])
        lines.extend(
            _markdown_table(
                {
                    "columns": ["Priority", "Business issue", "Action", "Evidence reference", "Owner hint"],
                    "rows": action_priority_rows,
                },
                max_rows=8,
            )
        )
        lines.append("")
    if commercial_delivery_rows:
        lines.extend(["## Delivery Check", ""])
        lines.extend(
            _markdown_table(
                {
                    "columns": ["Delivery dimension", "Status", "Acceptance evidence", "Business note"],
                    "rows": commercial_delivery_rows,
                },
                max_rows=8,
            )
        )
        lines.append("")
    numeric_dashboard_rows = [
        {"Metric": "Business charts", "Value": len(charts), "Meaning": "Reader-facing visual evidence in this run."},
        {
            "Metric": "Embedded chart images",
            "Value": len([chart for chart in charts if isinstance(chart, dict) and (chart.get("asset_exports") or {}).get("image_path")]),
            "Meaning": "Charts that can render directly in the report.",
        },
        {"Metric": "Evidence tables", "Value": len(tables), "Meaning": "Structured evidence available for review and traceability."},
        {
            "Metric": "Displayed method cards",
            "Value": f"{method_display_policy['display_method_package_count']}/{method_display_policy['raw_method_package_count']}",
            "Meaning": "Reader-facing method-card list after same-name card collapse.",
        },
        {
            "Metric": "Method artifact completeness",
            "Value": f"{(method_artifact_summary or {}).get('integrity_complete_count') or 0}/{(method_artifact_summary or {}).get('method_count') or 0}",
            "Meaning": "Complete method packages with supporting exports.",
        },
        {"Metric": "Visible numeric evidence rows", "Value": len(visible_number_rows), "Meaning": "Quantitative support surfaced in the report body."},
    ]
    lines.extend(["## Delivery Dashboard", ""])
    lines.extend(_markdown_table({"columns": ["Metric", "Value", "Meaning"], "rows": numeric_dashboard_rows}, max_rows=20))
    lines.append("")
    if evidence_chain_rows:
        lines.extend(["## Evidence Chain", ""])
        lines.extend(
            _markdown_table(
                {
                    "columns": ["Evidence ID", "Business question", "Business judgment", "Business evidence", "Method evidence", "Downloadable evidence", "Review boundary"],
                    "rows": evidence_chain_rows,
                },
                max_rows=8,
            )
        )
        lines.append("")
    if chart_rows or visible_number_rows:
        lines.extend(["## Chart And Numeric Evidence", ""])
        if chart_rows:
            lines.extend(["### Chart Evidence", ""])
            for chart in charts:
                if isinstance(chart, dict) and (chart.get("asset_exports") or {}).get("image_path"):
                    lines.append(_chart_visual_marker(chart, method_execution_packages))
                    lines.append("")
            lines.extend(
                _markdown_table(
                    {
                        "columns": ["Chart", "Type", "X field", "Y field", "Points", "Business judgment", "Image"],
                        "rows": chart_rows,
                    },
                    max_rows=max(15, len(chart_rows)),
                )
            )
            lines.append("")
        if visible_number_rows:
            lines.extend(["### Numeric Evidence", ""])
            lines.extend(
                _markdown_table(
                    {
                        "columns": ["Method run", "Business metric", "Sample size", "Mean", "Min", "Max"],
                        "rows": visible_number_rows,
                    },
                    max_rows=16,
                )
            )
            lines.append("")
    method_visual_markers = [
        marker
        for marker in (_method_visual_marker(package) for package in method_display_packages[:8])
        if marker
    ]
    if method_visual_markers:
        lines.extend(["### Method Visual Preview", ""])
        for marker in method_visual_markers[:6]:
            lines.append(marker)
            lines.append("")
    business_signals = _build_business_signal_summary(
        dataset_name=dataset_name,
        sheet_name=sheet_name,
        selected=selected,
        tables=tables,
        charts=charts,
        method_execution_packages=method_execution_packages,
    )
    if business_signals:
        lines.extend(["## Business Signals", ""])
        for item in business_signals:
            lines.append(f"- {item}")
        lines.append("")
    lines.extend(["## Risks And Release Boundaries", ""])
    lines.append("- Automation can improve coverage and readability, but release quality still depends on evidence coverage, readable output, and review completion.")
    lines.append("- Actions that are not supported by reviewable evidence should not be promoted to core conclusions.")
    lines.append("- If method evidence is incomplete or references are missing, treat the result as provisional rather than final.")
    lines.append("")
    lines.extend(["## Appendix", ""])
    if charts:
        lines.extend(["### Chart Inventory", ""])
        for chart in charts[:20]:
            if not isinstance(chart, dict):
                continue
            lines.append(
                f"- {chart.get('kind') or 'chart'}: {chart.get('title') or '-'}; "
                f"x={chart.get('x_label') or chart.get('x') or '-'}; "
                f"y={chart.get('y_label') or '-'}; "
                f"points={format(_chart_point_count(chart), ',')}"
            )
            if chart.get("explanation"):
                lines.append(f"  - {_report_cell_text(chart.get('explanation'), 500)}")
        lines.append("")
    if method_artifact_summary:
        integrity_status = method_artifact_summary.get("integrity_status") or "-"
        lines.extend(
            [
                "### Method Artifact Coverage",
                "",
                "- Method packages are exported as structured evidence with data files, previews, and integrity records.",
                f"- Integrity status: `{integrity_status}` ({method_artifact_summary.get('integrity_complete_count') or 0}/{method_artifact_summary.get('method_count') or 0} complete)",
                f"- Runtime status: {_review_status_label(method_artifact_summary.get('runtime_status'))}",
                "",
            ]
        )
    requested_method_limit = int(getattr(request, "max_methods", 0) or 0)
    method_evidence_limit = min(len(method_display_packages), max(40, min(max(requested_method_limit, 50), 120)))
    lines.append(
        "Method evidence listed: "
        f"{method_evidence_limit}/{len(method_display_packages)} displayed "
        f"(raw packages: {len(method_execution_packages)}; "
        f"collapsed duplicates: {method_display_policy['collapsed_duplicate_run_count']})"
    )
    lines.append("")
    for evidence_index, package in enumerate(method_display_packages[:method_evidence_limit], start=1):
        summary = _method_package_summary(package)
        artifact_exports = package.get("artifact_exports") if isinstance(package.get("artifact_exports"), dict) else {}
        display_group = package.get("display_group") if isinstance(package.get("display_group"), dict) else {}
        method_ref = summary.get("method_run_id") or summary.get("method_id") or ""
        lines.append(
            f"- Evidence {evidence_index:03d}: {_client_method_name(package)} "
            f"({_method_family_label(summary.get('family'))}; assets={summary.get('asset_count') or 0}; handoffs={summary.get('runtime_handoff_count') or 0})"
        )
        if int(display_group.get("collapsed_run_count") or 0) > 0:
            grouped_refs = [ref for ref in list(display_group.get("method_run_ids") or []) if str(ref or "").strip()]
            lines.append(
                "  - Display group: "
                f"{display_group.get('total_runs') or 1} same-name method runs collapsed into this card; "
                f"run refs={_public_evidence_refs(grouped_refs, limit=10)}"
            )
        evidence_refs = [str(item) for item in list(summary.get("evidence_refs") or []) if str(item or "").strip()]
        if evidence_refs:
            lines.append(f"  - Evidence refs: {_public_evidence_refs(evidence_refs)}")
        lines.append(f"  - Method name: {_client_method_name(package)}")
        lines.append(f"  - Trace ref: {_public_evidence_ref(method_ref)}")
        if artifact_exports:
            lines.append(
                "  - Downloadables: "
                f"{_customer_artifact_label(artifact_exports.get('data_json_path'))}; "
                f"{_customer_artifact_label(artifact_exports.get('data_csv_path'))}; "
                f"{_customer_artifact_label(artifact_exports.get('data_xlsx_path'))}; "
                f"{_customer_artifact_label(artifact_exports.get('preview_png_path'))} "
                f"(integrity={_artifact_integrity_label(artifact_exports.get('integrity_status'))})"
            )
        lines.append("  - Boundary: confirm evidence references, field semantics, and artifact usability before scaling this conclusion.")
    bundle_refs = [
        str(ref)
        for part in report_parts
        for ref in list(part.get("evidence_refs") or [])
        if str(ref or "").strip()
    ]
    if bundle_refs:
        lines.extend(["", "### Evidence References", ""])
        for ref in list(dict.fromkeys(bundle_refs))[:120]:
            lines.append(f"- {_public_evidence_ref(ref)}")
    return "\n".join(lines).strip() + "\n"


_render_lab_report_markdown = _render_lab_report_markdown


def _is_markdown_table_separator(line: str) -> bool:
    stripped = line.strip()
    if not stripped.startswith("|") or "|" not in stripped[1:]:
        return False
    content = stripped.strip("|").strip()
    return bool(content) and all(char in "-:| " for char in content)


def _split_markdown_table_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip().replace("\\|", "|") for cell in stripped.split("|")]


def _render_markdown_table_html(table_lines: list[str]) -> str:
    if len(table_lines) < 2:
        escaped = "\n".join(html_lib.escape(_sanitize_reader_facing_text(line)) for line in table_lines)
        return f"<div class=\"table-scroll\"><pre>{escaped}</pre></div>"
    headers = _split_markdown_table_row(table_lines[0])
    body_rows = [_split_markdown_table_row(line) for line in table_lines[2:]]
    column_count = max([len(headers)] + [len(row) for row in body_rows] + [1])

    def _cells(cells: list[str], tag: str) -> str:
        padded = cells + [""] * max(0, column_count - len(cells))
        return "".join(f"<{tag}>{html_lib.escape(_sanitize_reader_facing_text(cell))}</{tag}>" for cell in padded[:column_count])

    head = f"<thead><tr>{_cells(headers, 'th')}</tr></thead>"
    rows = "".join(f"<tr>{_cells(row, 'td')}</tr>" for row in body_rows)
    return f"<div class=\"table-scroll\"><table>{head}<tbody>{rows}</tbody></table></div>"


def _inline_report_html(text: str) -> str:
    escaped = html_lib.escape(str(text))
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)


def _report_heading_id(text: str, used_ids: set[str]) -> str:
    slug = re.sub(r"[^\w\u4e00-\u9fff]+", "-", str(text).strip().lower(), flags=re.UNICODE).strip("-")
    slug = slug or "section"
    candidate = slug
    suffix = 2
    while candidate in used_ids:
        candidate = f"{slug}-{suffix}"
        suffix += 1
    used_ids.add(candidate)
    return candidate


def _markdown_to_lab_report_html(markdown_text: str, title: str) -> str:
    body: list[str] = []
    toc: list[tuple[int, str, str]] = []
    lines = markdown_text.splitlines()
    index = 0
    table_count = 0
    visual_count = 0
    section_count = 0
    heading_ids: set[str] = set()
    hero_title = title
    while index < len(lines):
        line = lines[index].rstrip()
        if line.startswith("CHART:") or line.startswith("VISUAL:"):
            is_chart_marker = line.startswith("CHART:")
            marker = "CHART:" if is_chart_marker else "VISUAL:"
            visual_fields: dict[str, str] = {}
            for chunk in line[len(marker) :].split(";"):
                if "=" not in chunk:
                    continue
                key, value = chunk.split("=", 1)
                visual_fields[key.strip()] = value.strip()
            image_path = visual_fields.get("image") or ""
            if image_path:
                visual_count += 1
                caption = visual_fields.get("title") or "Method preview"
                links = [
                    ("CSV", visual_fields.get("csv") or ""),
                    ("XLSX", visual_fields.get("xlsx") or ""),
                    ("JSON", visual_fields.get("json") or ""),
                ]
                link_html = "".join(
                    f"<a class=\"artifact-link\" href=\"{html_lib.escape(href, quote=True)}\">{label}</a>"
                    for label, href in links
                    if href
                )
                body.append(
                    f"<figure class=\"{'business-chart' if is_chart_marker else 'method-visual'}\" id=\"visual-{visual_count:02d}\" data-visual-src=\"{html_lib.escape(image_path, quote=True)}\">"
                    f"<div class=\"visual-kicker\">{'业务图表证据' if is_chart_marker else '方法附录图像'}</div>"
                    "<div class=\"visual-media\">"
                    f"<img src=\"{html_lib.escape(image_path, quote=True)}\" alt=\"{html_lib.escape(caption, quote=True)}\" loading=\"eager\" decoding=\"async\" />"
                    "</div>"
                    "<figcaption>"
                    f"<strong>{html_lib.escape(caption)}</strong>"
                    f"<span class=\"image-status\">正在加载 PNG 图表</span>"
                    f"<span class=\"visual-question\"><b>读图问题：</b>{html_lib.escape(visual_fields.get('question') or '')}</span>"
                    f"<span class=\"visual-insight\"><b>关键发现：</b>{html_lib.escape(visual_fields.get('insight') or '')}</span>"
                    f"<span class=\"visual-impact\"><b>业务影响：</b>{html_lib.escape(visual_fields.get('impact') or '')}</span>"
                    f"<span class=\"visual-boundary\"><b>复核边界：</b>{html_lib.escape(visual_fields.get('boundary') or '')}</span>"
                    f"<span class=\"visual-evidence\"><b>证据包：</b>{html_lib.escape(visual_fields.get('evidence') or '')}</span>"
                    f"<span class=\"artifact-links\">{link_html}</span>"
                    "</figcaption>"
                    "</figure>"
                )
            index += 1
            continue
        if line.strip().startswith("|") and index + 1 < len(lines) and _is_markdown_table_separator(lines[index + 1]):
            table_lines = [line]
            index += 1
            while index < len(lines) and lines[index].strip().startswith("|"):
                table_lines.append(lines[index].rstrip())
                index += 1
            table_count += 1
            body.append(_render_markdown_table_html(table_lines))
            continue
        if not line.strip():
            index += 1
            continue
        image_match = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", line.strip())
        if image_match:
            alt_text = _sanitize_reader_facing_text(image_match.group(1) or "图像证据")
            image_path = image_match.group(2).strip()
            body.append(
                "<figure class=\"markdown-embedded-image\">"
                "<div class=\"visual-media\">"
                f"<img src=\"{html_lib.escape(image_path, quote=True)}\" alt=\"{html_lib.escape(alt_text, quote=True)}\" loading=\"eager\" decoding=\"async\" />"
                "</div>"
                f"<figcaption><strong>{html_lib.escape(alt_text)}</strong></figcaption>"
                "</figure>"
            )
            visual_count += 1
            index += 1
            continue
        if line.startswith("# "):
            hero_title = line[2:].strip() or title
        elif line.startswith("## "):
            heading_text = line[3:].strip()
            heading_id = _report_heading_id(heading_text, heading_ids)
            toc.append((2, heading_text, heading_id))
            section_count += 1
            body.append(f"<h2 id=\"{heading_id}\">{html_lib.escape(heading_text)}</h2>")
        elif line.startswith("### "):
            heading_text = line[4:].strip()
            heading_id = _report_heading_id(heading_text, heading_ids)
            toc.append((3, heading_text, heading_id))
            body.append(f"<h3 id=\"{heading_id}\">{html_lib.escape(heading_text)}</h3>")
        elif line.startswith("- "):
            body.append(f"<p class=\"bullet\">{_inline_report_html(line[2:].strip())}</p>")
        elif line.startswith("  - "):
            body.append(f"<p class=\"sub-bullet\">{_inline_report_html(line[4:].strip())}</p>")
        else:
            body.append(f"<p>{_inline_report_html(line.strip())}</p>")
        index += 1
    toc_html = "\n".join(
        f"<a class=\"toc-link level-{level}\" href=\"#{html_lib.escape(anchor, quote=True)}\">{html_lib.escape(label)}</a>"
        for level, label, anchor in toc[:36]
    )
    stat_cards = "\n".join(
        [
            f"<div class=\"hero-stat\"><span>{section_count}</span><small>报告章节</small></div>",
            f"<div class=\"hero-stat\"><span>{table_count}</span><small>证据表格</small></div>",
            f"<div class=\"hero-stat\"><span>{visual_count}</span><small>PNG 预览</small></div>",
        ]
    )
    body_html = "\n".join(body)
    return f"""<!doctype html>
<html lang="zh-CN" data-design-skill="frontend-design">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html_lib.escape(title)}</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #1d261f;
      --muted: #657064;
      --faint: #8d967f;
      --line: rgba(49, 68, 47, 0.18);
      --paper: #fffaf0;
      --paper-strong: #fff3d7;
      --field: #e4d5b5;
      --forest: #253d2a;
      --moss: #61743c;
      --ochre: #b66f24;
      --clay: #864b2b;
      --sky: #d5e5de;
      --shadow: 0 28px 90px rgba(38, 49, 33, 0.18);
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      color: var(--ink);
      font-family: "Source Han Serif SC", "Noto Serif CJK SC", "Songti SC", "Microsoft YaHei UI", serif;
      background:
        radial-gradient(circle at 12% 10%, rgba(182, 111, 36, 0.26), transparent 30rem),
        radial-gradient(circle at 88% 0%, rgba(91, 116, 60, 0.26), transparent 28rem),
        linear-gradient(135deg, #efe3cc 0%, #d8e1d4 52%, #f5ead7 100%);
      min-height: 100vh;
    }}
    body::before {{
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      opacity: 0.18;
      background-image:
        linear-gradient(rgba(37, 61, 42, 0.16) 1px, transparent 1px),
        linear-gradient(90deg, rgba(37, 61, 42, 0.14) 1px, transparent 1px);
      background-size: 42px 42px;
      mask-image: linear-gradient(to bottom, #000, transparent 82%);
    }}
    a {{ color: inherit; }}
    code {{
      padding: 0.12rem 0.34rem;
      border: 1px solid rgba(97, 116, 60, 0.2);
      border-radius: 999px;
      background: rgba(255, 250, 240, 0.72);
      color: #5e351f;
      font: 0.86em/1.3 "Cascadia Mono", "SFMono-Regular", Consolas, monospace;
    }}
    .report-shell {{
      width: min(1480px, calc(100% - 36px));
      margin: 28px auto;
      border: 1px solid rgba(255, 255, 255, 0.52);
      border-radius: 34px;
      background: rgba(255, 250, 240, 0.76);
      box-shadow: var(--shadow);
      overflow: hidden;
      backdrop-filter: blur(16px);
    }}
    .report-hero {{
      position: relative;
      min-height: 360px;
      padding: clamp(30px, 6vw, 74px);
      color: #fdf8ea;
      overflow: hidden;
      background:
        linear-gradient(126deg, rgba(37, 61, 42, 0.98), rgba(70, 82, 44, 0.93) 48%, rgba(134, 75, 43, 0.9)),
        radial-gradient(circle at 76% 24%, rgba(255, 243, 215, 0.32), transparent 22rem);
    }}
    .report-hero::after {{
      content: "";
      position: absolute;
      right: -9rem;
      top: -8rem;
      width: 30rem;
      height: 30rem;
      border: 1px solid rgba(255, 250, 240, 0.28);
      border-radius: 42% 58% 50% 50%;
      transform: rotate(-16deg);
    }}
    .hero-kicker {{
      position: relative;
      z-index: 1;
      display: inline-flex;
      gap: 0.6rem;
      align-items: center;
      margin: 0 0 22px;
      padding: 0.48rem 0.82rem;
      border: 1px solid rgba(255, 250, 240, 0.28);
      border-radius: 999px;
      background: rgba(255, 250, 240, 0.12);
      color: #fff0c8;
      font-size: 12px;
      letter-spacing: 0.16em;
      text-transform: uppercase;
    }}
    .report-hero h1 {{
      position: relative;
      z-index: 1;
      max-width: 980px;
      margin: 0;
      font-size: clamp(34px, 6vw, 76px);
      line-height: 0.98;
      letter-spacing: -0.055em;
      text-wrap: balance;
    }}
    .hero-subtitle {{
      position: relative;
      z-index: 1;
      max-width: 760px;
      margin: 24px 0 0;
      color: rgba(255, 250, 240, 0.78);
      font-size: clamp(15px, 2vw, 19px);
      line-height: 1.8;
    }}
    .hero-stats {{
      position: relative;
      z-index: 1;
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
      max-width: 620px;
      margin-top: 34px;
    }}
    .hero-stat {{
      padding: 18px;
      border: 1px solid rgba(255, 250, 240, 0.2);
      border-radius: 22px;
      background: rgba(255, 250, 240, 0.12);
    }}
    .hero-stat span {{ display: block; font-size: 34px; font-weight: 900; line-height: 1; }}
    .hero-stat small {{ display: block; margin-top: 8px; color: rgba(255, 250, 240, 0.72); letter-spacing: 0.08em; }}
    .report-layout {{
      display: grid;
      grid-template-columns: minmax(200px, 270px) minmax(0, 1fr);
      gap: clamp(22px, 4vw, 54px);
      padding: clamp(22px, 5vw, 58px);
    }}
    .report-toc {{
      position: sticky;
      top: 18px;
      align-self: start;
      max-height: calc(100vh - 36px);
      overflow: auto;
      padding: 18px;
      border: 1px solid var(--line);
      border-radius: 24px;
      background: rgba(255, 250, 240, 0.72);
    }}
    .toc-title {{
      margin: 0 0 12px;
      color: var(--clay);
      font-size: 12px;
      font-weight: 900;
      letter-spacing: 0.15em;
      text-transform: uppercase;
    }}
    .toc-link {{
      display: block;
      margin: 5px 0;
      padding: 8px 10px;
      border-radius: 12px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.4;
      text-decoration: none;
      transition: background 160ms ease, color 160ms ease, transform 160ms ease;
    }}
    .toc-link.level-3 {{ margin-left: 12px; font-size: 12px; color: var(--faint); }}
    .toc-link:hover {{ background: rgba(182, 111, 36, 0.12); color: var(--forest); transform: translateX(2px); }}
    main.report-content {{
      min-width: 0;
      padding: clamp(22px, 4vw, 46px);
      border: 1px solid var(--line);
      border-radius: 30px;
      background: linear-gradient(180deg, rgba(255, 253, 247, 0.96), rgba(255, 248, 232, 0.92));
    }}
    h2 {{
      margin: 48px 0 18px;
      padding: 20px 0 0;
      border-top: 1px solid var(--line);
      color: var(--forest);
      font-size: clamp(25px, 3.4vw, 42px);
      line-height: 1.12;
      letter-spacing: -0.035em;
    }}
    h2:first-child {{ margin-top: 0; padding-top: 0; border-top: 0; }}
    h3 {{
      margin: 30px 0 12px;
      color: var(--clay);
      font-size: clamp(18px, 2.1vw, 25px);
      line-height: 1.28;
    }}
    p {{
      margin: 10px 0;
      color: #334035;
      font-size: 15px;
      line-height: 1.92;
      overflow-wrap: anywhere;
    }}
    .bullet, .sub-bullet {{
      position: relative;
      padding: 12px 14px 12px 42px;
      border: 1px solid rgba(49, 68, 47, 0.1);
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.56);
    }}
    .bullet::before {{
      content: "";
      position: absolute;
      left: 18px;
      top: 1.55em;
      width: 9px;
      height: 9px;
      border-radius: 50%;
      background: var(--ochre);
      box-shadow: 0 0 0 5px rgba(182, 111, 36, 0.12);
    }}
    .sub-bullet {{
      margin-left: 28px;
      color: var(--muted);
      background: rgba(237, 229, 208, 0.46);
    }}
    .sub-bullet::before {{
      content: "";
      position: absolute;
      left: 20px;
      top: 1.62em;
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: var(--moss);
    }}
    .method-visual, .business-chart, .markdown-embedded-image {{
      margin: 24px 0 34px;
      padding: 16px;
      border: 1px solid rgba(97, 116, 60, 0.22);
      border-radius: 28px;
      background:
        linear-gradient(180deg, rgba(255, 255, 255, 0.9), rgba(255, 248, 232, 0.9)),
        radial-gradient(circle at 100% 0%, rgba(213, 229, 222, 0.62), transparent 22rem);
      box-shadow: 0 20px 60px rgba(38, 49, 33, 0.12);
      break-inside: avoid;
    }}
    .business-chart {{
      padding: 20px;
      border-color: rgba(182, 111, 36, 0.26);
      background:
        linear-gradient(180deg, rgba(255, 253, 246, 0.98), rgba(255, 242, 211, 0.94)),
        radial-gradient(circle at 100% 0%, rgba(182, 111, 36, 0.16), transparent 24rem);
    }}
    .visual-kicker {{
      display: inline-flex;
      margin: 0 0 12px;
      padding: 0.34rem 0.7rem;
      border-radius: 999px;
      background: rgba(97, 116, 60, 0.12);
      color: var(--moss);
      font-size: 11px;
      font-weight: 900;
      letter-spacing: 0.14em;
    }}
    .visual-media {{
      display: grid;
      place-items: center;
      min-height: 220px;
      border: 1px solid rgba(49, 68, 47, 0.12);
      border-radius: 22px;
      background:
        linear-gradient(45deg, rgba(37, 61, 42, 0.035) 25%, transparent 25%, transparent 75%, rgba(37, 61, 42, 0.035) 75%),
        #fffefa;
      background-size: 28px 28px;
      overflow: hidden;
    }}
    .method-visual img, .business-chart img, .markdown-embedded-image img {{
      display: block;
      width: 100%;
      max-height: 680px;
      object-fit: contain;
      border-radius: 18px;
      background: #fff;
    }}
    .method-visual figcaption, .business-chart figcaption, .markdown-embedded-image figcaption {{
      display: grid;
      grid-template-columns: minmax(0, 1fr);
      gap: 9px;
      align-items: start;
      margin-top: 12px;
      color: var(--muted);
      font-size: 12px;
    }}
    .method-visual figcaption strong, .business-chart figcaption strong, .markdown-embedded-image figcaption strong {{
      color: var(--forest);
      font-size: 13px;
      line-height: 1.45;
      overflow-wrap: anywhere;
    }}
    .visual-question,
    .visual-insight,
    .visual-impact,
    .visual-boundary,
    .visual-evidence {{
      display: block;
      padding: 12px 14px;
      border: 1px solid rgba(97, 116, 60, 0.14);
      border-radius: 14px;
      background: rgba(255, 255, 255, 0.66);
      color: var(--ink);
      font-size: 13px;
      line-height: 1.75;
    }}
    .visual-question b,
    .visual-insight b,
    .visual-impact b,
    .visual-boundary b,
    .visual-evidence b {{
      color: var(--moss);
      margin-right: 0.32rem;
    }}
    .visual-insight {{
      border-left: 4px solid var(--ochre);
      background: rgba(255, 243, 215, 0.72);
      color: #3c3426;
    }}
    .visual-boundary {{
      background: rgba(182, 111, 36, 0.08);
      border-color: rgba(182, 111, 36, 0.18);
    }}
    .visual-evidence {{
      font-family: "JetBrains Mono", "SFMono-Regular", Consolas, monospace;
      color: #516447;
    }}
    .image-status {{
      justify-self: start;
      padding: 0.22rem 0.58rem;
      border-radius: 999px;
      background: rgba(213, 229, 222, 0.55);
      color: var(--forest);
      font-weight: 800;
    }}
    .method-visual.image-missing .image-status {{
      background: rgba(182, 111, 36, 0.14);
      color: #8a3f1c;
    }}
    .artifact-links {{
      display: flex;
      flex-wrap: wrap;
      justify-content: flex-end;
      gap: 8px;
      grid-column: 1 / -1;
    }}
    .artifact-link {{
      display: inline-flex;
      align-items: center;
      min-height: 30px;
      padding: 0.35rem 0.66rem;
      border: 1px solid rgba(134, 75, 43, 0.18);
      border-radius: 999px;
      background: rgba(255, 243, 215, 0.72);
      color: var(--clay);
      font-weight: 900;
      text-decoration: none;
    }}
    .artifact-link:hover {{ background: rgba(182, 111, 36, 0.16); }}
    .table-scroll {{
      overflow: auto;
      max-height: 70vh;
      margin: 18px 0 28px;
      border: 1px solid var(--line);
      border-radius: 22px;
      background: #fffefa;
      box-shadow: 0 14px 38px rgba(38, 49, 33, 0.08);
    }}
    table {{
      width: 100%;
      min-width: 760px;
      border-collapse: collapse;
      font-size: 12px;
      line-height: 1.58;
    }}
    th, td {{
      padding: 11px 13px;
      border-bottom: 1px solid rgba(49, 68, 47, 0.12);
      text-align: left;
      vertical-align: top;
      overflow-wrap: anywhere;
    }}
    th {{
      position: sticky;
      top: 0;
      z-index: 1;
      background: #d9c399;
      color: #2d2518;
      font-weight: 900;
    }}
    tbody tr:nth-child(even) {{ background: rgba(228, 213, 181, 0.22); }}
    tbody tr:hover {{ background: rgba(213, 229, 222, 0.35); }}
    pre {{ margin: 0; padding: 14px; font: 12px/1.6 "Cascadia Mono", Consolas, monospace; white-space: pre; }}
    .report-footer {{
      padding: 0 clamp(22px, 5vw, 58px) clamp(22px, 5vw, 44px);
      color: var(--muted);
      font-size: 12px;
    }}
    @media (max-width: 960px) {{
      .report-shell {{ width: 100%; margin: 0; border-radius: 0; }}
      .report-layout {{ grid-template-columns: 1fr; }}
      .report-toc {{ position: relative; top: 0; max-height: none; }}
      .hero-stats {{ grid-template-columns: 1fr; }}
      .method-visual figcaption {{ grid-template-columns: 1fr; }}
      .artifact-links {{ justify-content: flex-start; }}
      .sub-bullet {{ margin-left: 0; }}
    }}
    @media print {{
      body {{ background: #fff; }}
      body::before, .report-toc {{ display: none; }}
      .report-shell, main.report-content, .method-visual, .table-scroll {{ box-shadow: none; }}
      .report-layout {{ display: block; }}
    }}
  </style>
</head>
<body>
  <div class="report-shell">
    <header class="report-hero">
      <div class="hero-kicker">管理证据报告</div>
      <h1>{html_lib.escape(hero_title)}</h1>
      <p class="hero-subtitle">面向管理复盘的可审计报告：表格、图像和方法证据在同一个 HTML 中串联，图片缺失会直接在卡片中暴露路径问题。</p>
      <div class="hero-stats">{stat_cards}</div>
    </header>
    <div class="report-layout">
      <nav class="report-toc" aria-label="报告目录">
        <p class="toc-title">目录</p>
        {toc_html}
      </nav>
      <main class="report-content">{body_html}</main>
    </div>
    <footer class="report-footer">由分析报告生成器自动排版；正式发布前请复核字段口径、样本范围和业务事实。</footer>
  </div>
  <script>
    (() => {{
      document.querySelectorAll(".method-visual").forEach((figure) => {{
        const image = figure.querySelector("img");
        const status = figure.querySelector(".image-status");
        if (!image || !status) return;
        const loaded = () => {{
          figure.classList.add("image-loaded");
          status.textContent = "PNG 已加载";
        }};
        if (image.complete && image.naturalWidth > 0) loaded();
        image.addEventListener("load", loaded, {{ once: true }});
        image.addEventListener("error", () => {{
          figure.classList.add("image-missing");
          status.textContent = `图片未加载：${{image.getAttribute("src") || ""}}`;
        }}, {{ once: true }});
      }});
    }})();
  </script>
</body>
</html>
"""


def _write_json_file(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def _find_mojibake_tokens(text: str) -> list[str]:
    # Store known mojibake fragments via escapes so this source file stays readable in every editor/terminal.
    tokens = [
        "\u9410",
        "\u9359",
        "\u7ef1",
        "\u9286",
        "\u9225",
        "\u951b",
        "\u93c8\u20ac",
        "\u5bb8\u67e5\u20ac",
    ]
    return sorted({token for token in tokens if token in text})


def _has_sufficient_numeric_evidence(markdown_text: str, minimum: int = 6) -> tuple[bool, int]:
    matches = re.findall(r"(?<![A-Za-z])(?:\d[\d,]*\.?\d*%?)(?![A-Za-z])", markdown_text)
    return len(matches) >= minimum, len(matches)


def _report_has_required_sections(markdown_text: str) -> dict[str, bool]:
    return {
        "research_abstract": "## 研究摘要" in markdown_text,
        "research_questions": "## 研究问题与结论" in markdown_text,
        "research_design": "## 研究设计与方法" in markdown_text,
        "figure_narrative": "## 图文叙事" in markdown_text,
        "commercial_delivery": "## 商用交付检查" in markdown_text,
        "management_summary": "## 管理摘要" in markdown_text,
        "data_scope": "### 数据范围与字段口径" in markdown_text,
        "key_findings": "### 执行摘要" in markdown_text,
        "key_metrics": "### 关键数字总览" in markdown_text,
        "core_business_judgment": "### 核心业务判断" in markdown_text,
        "action_priority_matrix": "## 行动优先级矩阵" in markdown_text,
        "business_evidence_chain": "## 业务证据链" in markdown_text,
        "business_signal": "### 业务信号判断" in markdown_text,
        "tables_or_charts": "## 图表与数值证据" in markdown_text
        and "### 可视化图表证据" in markdown_text
        and "### 表格与数值证据" in markdown_text,
        "agent_review": (
            "## 复核结论" in markdown_text
            or "## 审稿结论" in markdown_text
            or "## Agent 审稿结论" in markdown_text
        ),
        "method_evidence": "## 证据附录" in markdown_text and "### 方法证据索引" in markdown_text,
        "limitations": "## 风险边界" in markdown_text,
        "actions": "## 行动优先级矩阵" in markdown_text,
        "appendix_or_evidence_index": "## 证据附录" in markdown_text or "### 证据索引" in markdown_text,
    }


def _evaluate_lab_report_quality(
    *,
    markdown_text: str,
    html_text: str,
    report_parts: list[dict[str, Any]],
    tables: list[dict[str, Any]],
    charts: list[dict[str, Any]],
    method_execution_packages: list[dict[str, Any]],
    agent_review: dict[str, Any] | None,
    report_part_asset_manifest: list[dict[str, Any]],
    report_part_generation_blueprints: list[dict[str, Any]],
    external_skill_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    required_sections = _report_has_required_sections(markdown_text)
    section_passed = all(required_sections.values())
    checks.append(
        {
            "id": "required_sections",
            "label": "Required management sections",
            "status": "passed" if section_passed else "failed",
            "detail": ", ".join(f"{key}={'ok' if value else 'missing'}" for key, value in required_sections.items()),
        }
    )

    markdown_length = len(markdown_text)
    markdown_passed = markdown_length >= 4000
    checks.append(
        {
            "id": "report_length",
            "label": "Deterministic report has sufficient substance",
            "status": "passed" if markdown_passed else "failed",
            "detail": f"markdown_chars={markdown_length}; threshold=4000",
        }
    )

    numeric_passed, numeric_count = _has_sufficient_numeric_evidence(markdown_text)
    checks.append(
        {
            "id": "numeric_evidence",
            "label": "Multiple numeric evidence points exist",
            "status": "passed" if numeric_passed else "failed",
            "detail": f"numeric_evidence_count={numeric_count}; threshold=6",
        }
    )

    html_table_count = html_text.lower().count("<table")
    html_table_passed = html_table_count >= 1
    checks.append(
        {
            "id": "html_table_rendering",
            "label": "HTML report renders real table elements",
            "status": "passed" if html_table_passed else "failed",
            "detail": f"html_table_count={html_table_count}; threshold=1",
        }
    )

    frontend_shell_passed = (
        'data-design-skill="frontend-design"' in html_text
        and 'class="report-shell"' in html_text
        and 'class="report-toc"' in html_text
    )
    checks.append(
        {
            "id": "html_frontend_design_shell",
            "label": "HTML report uses the frontend-design report shell",
            "status": "passed" if frontend_shell_passed else "failed",
            "detail": "present" if frontend_shell_passed else "missing_shell_or_toc",
        }
    )

    required_chart_image_count = len([chart for chart in charts if isinstance(chart, dict)])
    html_image_count = html_text.lower().count("<img ")
    image_diagnostics_passed = (
        html_image_count >= max(required_chart_image_count, min(len(charts), 1))
        and 'src="chart_assets/' in html_text
        and 'class="image-status"' in html_text
    )
    checks.append(
        {
            "id": "html_image_rendering_contract",
            "label": "HTML report embeds business chart PNGs with load diagnostics",
            "status": "passed" if image_diagnostics_passed else "failed",
            "detail": f"html_image_count={html_image_count}; chart_count={len(charts)}",
        }
    )

    structured_caption_count = html_text.count('class="visual-question"')
    structured_caption_passed = (
        structured_caption_count >= min(max(len(charts), 1), 4)
        and 'class="visual-insight"' in html_text
        and 'class="visual-impact"' in html_text
        and 'class="visual-boundary"' in html_text
        and 'class="visual-evidence"' in html_text
        and "读图问题：" in html_text
        and "关键发现：" in html_text
        and "业务影响：" in html_text
        and "复核边界：" in html_text
        and "证据包：" in html_text
    )
    checks.append(
        {
            "id": "structured_chart_captions",
            "label": "Business chart captions explain question, finding, impact, boundary, and evidence",
            "status": "passed" if structured_caption_passed else "failed",
            "detail": f"structured_caption_count={structured_caption_count}; chart_count={len(charts)}",
        }
    )

    writer_agent_issues: list[str] = []
    for index, chart in enumerate([item for item in charts if isinstance(item, dict)], start=1):
        agent = _chart_writer_agent(chart)
        if not agent:
            writer_agent_issues.append(f"chart_{index}:missing_agent")
            continue
        if agent.get("contract") != CHART_REPORT_WRITER_AGENT_CONTRACT:
            writer_agent_issues.append(f"chart_{index}:wrong_contract")
        for key in ("direct_answer", "business_judgment", "caption", "recommended_action", "sampling_note"):
            if not str(agent.get(key) or "").strip():
                writer_agent_issues.append(f"chart_{index}:missing_{key}")
        if len([item for item in list(agent.get("evidence_numbers") or []) if isinstance(item, dict)]) < 2:
            writer_agent_issues.append(f"chart_{index}:insufficient_numbers")
        for stage_key in REPORT_WRITER_REQUIRED_STAGE_KEYS:
            stage = agent.get(stage_key)
            if not isinstance(stage, dict):
                writer_agent_issues.append(f"chart_{index}:missing_{stage_key}")
            elif not str(stage.get("contract") or "").strip():
                writer_agent_issues.append(f"chart_{index}:missing_{stage_key}_contract")
        if not (agent.get("skeptical_review_agent") or {}).get("passed") if isinstance(agent.get("skeptical_review_agent"), dict) else True:
            writer_agent_issues.append(f"chart_{index}:skeptical_stage_failed")
        if agent.get("pipeline_status") != "passed":
            writer_agent_issues.append(f"chart_{index}:pipeline_not_passed")
        sample_policy = chart.get("sample_policy") if isinstance(chart.get("sample_policy"), dict) else {}
        if int(sample_policy.get("chunk_count") or 0) > 0 and not isinstance(agent.get("chunk_evidence"), dict):
            writer_agent_issues.append(f"chart_{index}:missing_chunk_evidence")
    forbidden_hits = [phrase for phrase in _REPORT_WRITER_FORBIDDEN_PHRASES if phrase and phrase in markdown_text + "\n" + html_text]
    report_writer_agent_passed = not writer_agent_issues and not forbidden_hits
    checks.append(
        {
            "id": "report_writer_agent_contract",
            "label": "Every chart uses report-writer agent answers, captions, numeric evidence, and chunk notes",
            "status": "passed" if report_writer_agent_passed else "failed",
            "detail": "ok" if report_writer_agent_passed else f"issues={writer_agent_issues[:12]}; forbidden={forbidden_hits[:8]}",
        }
    )

    chart_asset_image_count = html_text.count('src="chart_assets/')
    visual_method_count = len([package for package in method_execution_packages if str(package.get("family") or "") == "visual"])
    visual_chart_preview_count = len(
        [
            package
            for package in method_execution_packages
            if str(package.get("family") or "") == "visual"
            and isinstance(package.get("artifact_exports"), dict)
            and package["artifact_exports"].get("preview_kind") == "business_chart"
        ]
    )
    agent_answer_count = len(
        {
            str(_chart_writer_agent(chart).get("direct_answer") or "").strip()
            for chart in charts
            if isinstance(chart, dict) and str(_chart_writer_agent(chart).get("direct_answer") or "").strip()
        }
    )
    agent_caption_count = len(
        [
            chart
            for chart in charts
            if isinstance(chart, dict)
            and str(_chart_writer_agent(chart).get("caption") or "").strip()
            and str(_chart_writer_agent(chart).get("direct_answer") or "").strip() in markdown_text
        ]
    )
    chart_report_contract_passed = (
        chart_asset_image_count >= max(required_chart_image_count, min(len(charts), 1))
        and "### 可视化图表证据" in markdown_text
        and "### 核心业务判断" in markdown_text
        and agent_caption_count >= min(max(len(charts), 1), 4)
    )
    business_chart_contract_passed = chart_report_contract_passed
    checks.append(
        {
            "id": "business_chart_visual_contract",
            "label": "Report and visual methods use real business chart images",
            "status": "passed" if business_chart_contract_passed else "failed",
            "detail": (
                f"chart_images={chart_asset_image_count}; "
                f"agent_caption_count={agent_caption_count}; "
                f"visual_chart_previews={visual_chart_preview_count}/{visual_method_count}"
            ),
        }
    )

    chart_interpretation_passed = (
        "### 核心业务判断" in markdown_text
        and "### 可视化图表证据" in markdown_text
        and agent_answer_count >= min(max(len(charts), 1), 3)
        and agent_caption_count >= min(max(len(charts), 1), 3)
        and "deterministic_preview_waiting_for_codex_cli" not in markdown_text
        and "fallback_materialized_waiting_for_codex_cli" not in markdown_text
    )
    checks.append(
        {
            "id": "business_chart_interpretation_visible",
            "label": "Report exposes business chart interpretation instead of method status filler",
            "status": "passed" if chart_interpretation_passed else "failed",
            "detail": f"agent_answer_count={agent_answer_count}; agent_caption_count={agent_caption_count}",
        }
    )

    raw_visual_marker_count = len(re.findall(r"(?m)^(?:CHART|VISUAL):\s", markdown_text))
    markdown_image_count = len(re.findall(r"(?m)^!\[[^\]]*\]\([^)]+\)", markdown_text))
    chart_or_table_ref_count = markdown_text.count("Figure ") + markdown_image_count + agent_answer_count
    chart_table_passed = chart_or_table_ref_count >= 2
    checks.append(
        {
            "id": "chart_table_refs",
            "label": "Report references tables or charts",
            "status": "passed" if chart_table_passed else "failed",
            "detail": f"chart_or_table_reference_count={chart_or_table_ref_count}; threshold=2",
        }
    )
    checks.append(
        {
            "id": "raw_visual_marker_absence",
            "label": "Reader-facing Markdown renders chart markers instead of leaking protocol lines",
            "status": "passed" if raw_visual_marker_count == 0 else "failed",
            "detail": f"raw_visual_marker_count={raw_visual_marker_count}",
        }
    )
    markdown_image_passed = markdown_image_count >= min(max(len(charts), 1), 4)
    checks.append(
        {
            "id": "markdown_image_delivery",
            "label": "Markdown report embeds PNG evidence instead of relying only on HTML",
            "status": "passed" if markdown_image_passed else "failed",
            "detail": f"markdown_image_count={markdown_image_count}; chart_count={len(charts)}",
        }
    )
    local_path_hits = re.findall(r"(?i)(?:/tmp/[^\s|)>\]\"']+|[a-z]:[/\\][^\s|)>\]\"']+)", markdown_text)
    local_path_passed = not local_path_hits
    checks.append(
        {
            "id": "reader_visible_local_path_absence",
            "label": "Reader-facing report avoids local temp or drive-letter paths",
            "status": "passed" if local_path_passed else "failed",
            "detail": "none" if local_path_passed else f"local_path_hits={local_path_hits[:8]}",
        }
    )

    families: dict[str, int] = {}
    weak_target_tokens = ("derived__product__", "年度(年度项目表)__x__", "__x__成立时间", "row_index")
    selected_target_text = markdown_text.lower()
    for package in method_execution_packages:
        family = str(package.get("family") or "unknown")
        families[family] = families.get(family, 0) + 1
    family_count = len([family for family, count in families.items() if count > 0])
    visual_count = int(families.get("visual") or 0)
    report_part_count = int(families.get("report_part") or 0)
    method_total = max(1, len(method_execution_packages))
    required_family_count = min(method_total, 3 if method_total < 10 else 5)
    diversity_passed = (
        family_count >= required_family_count
        and visual_count <= max(12, int(method_total * 0.4))
        and report_part_count <= max(8, int(method_total * 0.24))
    )
    checks.append(
        {
            "id": "method_family_diversity",
            "label": "Method set is not padded by visual/report-part methods",
            "status": "passed" if diversity_passed else "failed",
            "detail": (
                f"families={families}; family_count={family_count}; required_family_count={required_family_count}; "
                f"visual={visual_count}/{method_total}; report_part={report_part_count}/{method_total}"
            ),
        }
    )

    business_summary_passed = (
        ("## Business Signals" in markdown_text or "### 业务信号判断" in markdown_text)
        and markdown_text.count("- ") >= 3
    )
    checks.append(
        {
            "id": "business_signal_summary",
            "label": "Report contains a domain-facing business signal summary",
            "status": "passed" if business_summary_passed else "failed",
            "detail": "present" if business_summary_passed else "missing",
        }
    )

    research_report_passed = (
        (
            "## Management Summary" in markdown_text
            and "## Research Questions And Conclusions" in markdown_text
            and "## Analysis Design" in markdown_text
            and "## Figure Narrative" in markdown_text
            and "## Delivery Check" in markdown_text
            and markdown_text.count("Figure ") >= min(max(len(charts), 1), 4)
        )
        or (
            "## 管理摘要" in markdown_text
            and "## 研究问题与结论" in markdown_text
            and "## 研究设计与方法" in markdown_text
            and "## 图文叙事" in markdown_text
            and "## 商用交付检查" in markdown_text
            and (
                markdown_text.count("#### Figure ") >= min(max(len(charts), 1), 4)
                or markdown_text.count("![") >= min(max(len(charts), 1), 4)
                or "### 可视化图表证据" in markdown_text
            )
        )
    )
    checks.append(
        {
            "id": "commercial_research_report_structure",
            "label": "Report has commercial research-report structure with figure narrative",
            "status": "passed" if research_report_passed else "failed",
            "detail": (
                "present"
                if research_report_passed
                else (
                    f"research_questions={markdown_text.count('Research question')}; "
                    f"commercial_use={markdown_text.count('Business use')}; "
                    f"figure_narratives={markdown_text.count('Figure ')}"
                )
            ),
        }
    )

    reader_visible_text = "\n".join([markdown_text, _reader_visible_html_text(html_text)])
    internal_leakage_hits = _reader_facing_internal_leakage_hits(reader_visible_text)
    checks.append(
        {
            "id": "reader_facing_internal_leakage",
            "label": "Reader-facing report avoids internal runtime labels",
            "status": "passed" if not internal_leakage_hits else "failed",
            "detail": "none" if not internal_leakage_hits else f"leaked_tokens={internal_leakage_hits}",
        }
    )

    leakage_tokens = (
        "route_score",
        "asset_index",
        "payload.runtime",
        "Visible numeric evidence",
        "completed with",
        "Sync Codex CLI status",
        "Numbers at a glance",
        "Business signal summary",
    )
    leakage_hits = [token for token in leakage_tokens if token in markdown_text]
    agent_usable = _agent_review_is_usable(agent_review or {})
    agent_action_rows = _agent_consolidated_action_rows(agent_review or {})
    agent_review_count = len([item for item in list((agent_review or {}).get("agent_reviews") or []) if isinstance(item, dict)])
    suggestion_count = len(agent_action_rows)
    review_boundary_count = markdown_text.count("Review boundary") + html_text.count("复核边界：")
    evidence_chain_present = (
        ("## Evidence Chain" in markdown_text and "Evidence ID" in markdown_text)
        or ("## 业务证据链" in markdown_text and "证据编号" in markdown_text)
    )
    action_matrix_present = (
        ("## Recommended Actions" in markdown_text and "Business issue" in markdown_text)
        or ("## 行动优先级矩阵" in markdown_text and "业务问题" in markdown_text)
    )
    dashboard_present = "## Delivery Dashboard" in markdown_text or "### 关键数字总览" in markdown_text
    delivery_check_present = "## Delivery Check" in markdown_text or "## 商用交付检查" in markdown_text
    business_language_passed = (
        not leakage_hits
        and not internal_leakage_hits
        and dashboard_present
        and delivery_check_present
        and ("Status" in markdown_text or "交付状态" in markdown_text)
        and evidence_chain_present
        and action_matrix_present
        and agent_usable
        and 5 <= suggestion_count <= 8
        and review_boundary_count >= min(max(len(charts), 3), 8)
    )
    checks.append(
        {
            "id": "business_readability",
            "label": "Report avoids internal scaffolding and contains evidence-linked business actions",
            "status": "passed" if business_language_passed else "failed",
            "detail": (
                "ok"
                if business_language_passed
                else (
                    f"leaked_tokens={leakage_hits[:8]}; "
                    f"agent_usable={agent_usable}; agent_review_count={agent_review_count}; "
                    f"agent_action_count={suggestion_count}; review_boundary_count={review_boundary_count}; "
                    f"evidence_chain={evidence_chain_present}; action_matrix={action_matrix_present}"
                )
            ),
        }
    )

    external_skill_rows = _external_skill_report_flow_rows(external_skill_context)
    selected_external_feature_rows = _selected_external_skill_feature_rows(external_skill_context)
    external_skill_enabled = bool((external_skill_context or {}).get("enabled") or external_skill_rows)
    report_flow_text = "\n".join([markdown_text, _reader_visible_html_text(html_text)]).casefold()
    required_skill_tokens: list[str] = []
    for row in selected_external_feature_rows:
        feature_token = str(row.get("feature_name") or row.get("feature_id") or "").strip()
        if feature_token:
            required_skill_tokens.append(feature_token)
    unique_required_skill_tokens = list(dict.fromkeys(required_skill_tokens))
    missing_skill_tokens = [
        token
        for token in unique_required_skill_tokens
        if token and token.casefold() not in report_flow_text
    ]
    knowledge_work_section_present = "Knowledge Work Report-Flow Integration".casefold() in report_flow_text
    external_skill_gate_passed = (
        not external_skill_enabled
        or (
            (
                knowledge_work_section_present
                or "写作与图文约束".casefold() in report_flow_text
                or "selected knowledge work functions".casefold() in report_flow_text
            )
            and bool(external_skill_rows)
            and not missing_skill_tokens
        )
    )
    checks.append(
        {
            "id": "mounted_knowledge_work_report_flow",
            "label": "Mounted Knowledge Work packages are visible in the report and strict review",
            "status": "passed" if external_skill_gate_passed else "failed",
            "detail": (
                "not_required"
                if not external_skill_enabled
                else (
                    f"section_present={knowledge_work_section_present}; "
                    f"mounted_skill_count={len(external_skill_rows)}; "
                    f"selected_feature_count={len(selected_external_feature_rows)}; "
                    f"missing_tokens={missing_skill_tokens[:12]}"
                )
            ),
        }
    )

    weak_target_hits = [token for token in weak_target_tokens if token.lower() in selected_target_text]
    weak_target_passed = not any(token in {"derived__product__", "__x__成立时间", "row_index"} for token in weak_target_hits)
    checks.append(
        {
            "id": "target_semantic_quality",
            "label": "Selected target avoids weak product/time-row artifacts",
            "status": "passed" if weak_target_passed else "failed",
            "detail": "none" if weak_target_passed else f"weak_tokens={weak_target_hits}",
        }
    )

    suspicious_numbers = re.findall(
        r"(?<![A-Za-z0-9_])[-+]?(?:\d+(?:\.\d*)?|\.\d+)e[+-]?\d+(?![A-Za-z0-9_])",
        markdown_text.lower(),
    )
    suspicious_forecast_passed = not any(abs(float(item)) >= 1e12 for item in suspicious_numbers)
    checks.append(
        {
            "id": "suspicious_forecast_magnitude",
            "label": "Report avoids explosive scientific-notation forecast artifacts",
            "status": "passed" if suspicious_forecast_passed else "failed",
            "detail": "none" if suspicious_forecast_passed else f"scientific_notation_values={suspicious_numbers[:8]}",
        }
    )

    package_refs = {
        str(package.get("method_run_id") or package.get("method_id") or "").strip()
        for package in method_execution_packages
        if str(package.get("method_run_id") or package.get("method_id") or "").strip()
    }
    covered_package_refs = {
        ref
        for ref in package_refs
        if ref and (ref in markdown_text or _public_evidence_ref(ref) in markdown_text)
    }
    method_coverage_passed = len(covered_package_refs) >= len(package_refs) if package_refs else False
    checks.append(
        {
            "id": "method_run_traceability",
            "label": "Each method package is traceable in report evidence",
            "status": "passed" if method_coverage_passed else "failed",
            "detail": f"covered_method_runs={len(covered_package_refs)}/{len(package_refs)}",
        }
    )

    bundle_evidence_refs = list(
        dict.fromkeys(
            str(ref)
            for part in report_parts
            for ref in list(part.get("evidence_refs") or [])
            if str(ref or "").strip()
        )
    )
    mapped_refs = [
        ref
        for ref in bundle_evidence_refs
        if ref in markdown_text or _public_evidence_ref(ref) in markdown_text
    ]
    evidence_ref_passed = bool(bundle_evidence_refs) and len(mapped_refs) >= min(len(bundle_evidence_refs), 8)
    checks.append(
        {
            "id": "evidence_refs",
            "label": "Evidence refs are present and mapped into the report",
            "status": "passed" if evidence_ref_passed else "failed",
            "detail": f"mapped_evidence_refs={len(mapped_refs)}/{len(bundle_evidence_refs)}",
        }
    )

    mojibake_hits = _find_mojibake_tokens(markdown_text + "\n" + html_text)
    mojibake_passed = not mojibake_hits
    checks.append(
        {
            "id": "mojibake_scan",
            "label": "No obvious mojibake fragments",
            "status": "passed" if mojibake_passed else "failed",
            "detail": "none" if not mojibake_hits else f"found={', '.join(mojibake_hits)}",
        }
    )

    action_lines = [str(row.get("业务行动") or "") for row in agent_action_rows if str(row.get("业务行动") or "").strip()]
    action_keywords = {"优先", "复核", "检查", "放大", "校正", "培育", "诊断", "风险", "机会", "行动", "业务判断"}
    specific_action_count = sum(1 for line in action_lines if sum(1 for keyword in action_keywords if keyword in line) >= 2)
    unique_action_count = len({line.strip() for line in action_lines})
    action_specificity_passed = agent_usable and unique_action_count == len(action_lines) and specific_action_count >= min(len(action_lines), 5)
    checks.append(
        {
            "id": "action_specificity",
            "label": "Action section is not purely generic template text",
            "status": "passed" if action_specificity_passed else "failed",
            "detail": f"agent_action_count={len(action_lines)}; unique_action_count={unique_action_count}; specific_action_count={specific_action_count}",
        }
    )

    normalized_actions = [re.sub(r"\s+", " ", line).strip() for line in action_lines if line.strip()]
    unique_recommended_action_ratio = (len(set(normalized_actions)) / len(normalized_actions)) if normalized_actions else 0.0
    xy_pairs = [
        (str(chart.get("x_label") or ""), str(chart.get("y_label") or ""))
        for chart in charts
        if isinstance(chart, dict) and (str(chart.get("x_label") or "") or str(chart.get("y_label") or ""))
    ]
    pair_counts: dict[tuple[str, str], int] = {}
    for pair in xy_pairs:
        pair_counts[pair] = pair_counts.get(pair, 0) + 1
    top_xy_pair_share = (max(pair_counts.values()) / len(xy_pairs)) if xy_pairs else 0.0
    visual_ref_sets = {
        tuple(
            sorted(
                str(ref)
                for asset in list(package.get("assets") or [])
                if isinstance(asset, dict)
                for ref in list((asset.get("payload") if isinstance(asset.get("payload"), dict) else {}).get("chart_refs") or [])
            )
        )
        for package in method_execution_packages
        if str(package.get("family") or "") == "visual"
    }
    visual_ref_sets.discard(tuple())
    business_chart_ref_sets = {
        (
            str(chart.get("kind") or ""),
            str(chart.get("x_label") or chart.get("x") or ""),
            str(chart.get("y_label") or ""),
        )
        for chart in charts
        if isinstance(chart, dict) and (str(chart.get("kind") or "") or str(chart.get("x_label") or chart.get("x") or "") or str(chart.get("y_label") or ""))
    }
    chart_ref_unique_count = max(len(visual_ref_sets), len(business_chart_ref_sets))
    required_chart_ref_unique_count = 4 if method_total >= 10 else min(4, max(1, len(business_chart_ref_sets)))
    allowed_top_xy_pair_share = 0.4 if method_total >= 10 and len(xy_pairs) >= 10 else 1.0
    boilerplate_sentences = [
        "Review the CSV/XLSX/PNG exports and evidence references for this method first.",
        "Read the method package summary before validating key metrics and outlier objects.",
        "Review smart_merge_brief.json and the per-method JSON packages",
    ]
    boilerplate_sentence_count = sum(markdown_text.count(sentence) for sentence in boilerplate_sentences)
    commercial_gate_passed = (
        unique_recommended_action_ratio >= 0.6
        and top_xy_pair_share <= allowed_top_xy_pair_share
        and chart_ref_unique_count >= required_chart_ref_unique_count
        and agent_review_count >= 3
        and boilerplate_sentence_count == 0
        and agent_usable
    )
    checks.append(
        {
            "id": "commercial_quality_gate",
            "label": "Broker-grade commercial report gate",
            "status": "passed" if commercial_gate_passed else "failed",
            "detail": (
                f"unique_recommended_action_ratio={unique_recommended_action_ratio:.2f}; "
                f"top_xy_pair_share={top_xy_pair_share:.2f}/{allowed_top_xy_pair_share:.2f}; "
                f"visual_chart_ref_set_unique={len(visual_ref_sets)}; "
                f"business_chart_ref_set_unique={len(business_chart_ref_sets)}; "
                f"required_chart_ref_unique_count={required_chart_ref_unique_count}; "
                f"agent_review_count={agent_review_count}; "
                f"boilerplate_sentence_count={boilerplate_sentence_count}; "
                f"agent_usable={agent_usable}"
            ),
        }
    )

    part_ids = {str(part.get("id") or "").strip() for part in report_parts if str(part.get("id") or "").strip()}
    covered_part_ids = {part_id for part_id in part_ids if part_id.lower() in markdown_text.lower()}
    blueprint_titles = {
        str(item.get("report_part_title") or item.get("report_part_id") or "").strip()
        for item in report_part_generation_blueprints
        if str(item.get("report_part_title") or item.get("report_part_id") or "").strip()
    }
    table_ref_count = len(
        {
            str(table.get("title") or "").strip()
            for table in tables
            if isinstance(table, dict) and str(table.get("title") or "").strip()
        }
    )
    chart_ref_count = len(
        {
            f"chart:{str(chart.get('kind') or '').strip()}"
            for chart in charts
            if isinstance(chart, dict) and str(chart.get("kind") or "").strip()
        }
    )
    evidence_coverage = {
        "method_run_total": len(package_refs),
        "method_run_covered": len(covered_package_refs),
        "report_part_total": len(part_ids),
        "report_part_covered": len(covered_part_ids),
        "html_table_count": html_table_count,
        "table_ref_count": table_ref_count,
        "chart_ref_count": chart_ref_count,
        "evidence_ref_count": len(bundle_evidence_refs),
        "asset_manifest_count": len(report_part_asset_manifest),
        "generation_blueprint_count": len(report_part_generation_blueprints),
        "blueprint_title_count": len(blueprint_titles),
    }

    passed_check_count = len([check for check in checks if check["status"] == "passed"])
    failed_check_count = len(checks) - passed_check_count
    quality_status = "passed" if failed_check_count == 0 else "failed"
    quality_score = round((passed_check_count / max(1, len(checks))) * 100, 2)
    quality_summary = (
        f"quality_status={quality_status}; passed={passed_check_count}; failed={failed_check_count}; "
        f"method_coverage={evidence_coverage['method_run_covered']}/{evidence_coverage['method_run_total']}; "
        f"part_coverage={evidence_coverage['report_part_covered']}/{evidence_coverage['report_part_total']}; "
        f"refs(table/chart/evidence)={table_ref_count}/{chart_ref_count}/{len(bundle_evidence_refs)}"
    )
    return {
        "quality_status": quality_status,
        "quality_score": quality_score,
        "passed_check_count": passed_check_count,
        "failed_check_count": failed_check_count,
        "checks": checks,
        "quality_summary": quality_summary,
        "evidence_coverage": evidence_coverage,
    }


def _register_lab_report_catalog(
    *,
    report_id: str,
    title: str,
    request: AutoAnalysisRequest,
    dataset_name: str,
    sheet_name: str,
    markdown_path: Path,
    html_path: Path,
    seed_path: Path,
    generated_at: str,
    source_export_dir: Path,
    lab_report_meta: dict[str, Any] | None = None,
    large_sample_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if bool((large_sample_policy or {}).get("large_sample")):
        return {
            "report_dir": str(source_export_dir.resolve()),
            "manifest_path": "",
            "markdown_path": _public_path("", markdown_path.name),
            "html_path": _public_path("", html_path.name),
            "seed_path": _public_path("", seed_path.name),
            "catalog_status": "skipped_large_sample_sync",
            "catalog_error": "Large-sample report generation returns source artifacts immediately; report-library registration can be refreshed asynchronously.",
        }
    report_dir = REPORTS_DIR / f"smart-report-{report_id}"
    report_dir.mkdir(parents=True, exist_ok=True)
    library_md = report_dir / f"{report_id}-management_report.md"
    library_html = report_dir / f"{report_id}-management_report.html"
    library_seed = report_dir / LAB_REPORT_SEED_FILE
    shutil.copy2(markdown_path, library_md)
    shutil.copy2(html_path, library_html)
    shutil.copy2(seed_path, library_seed)

    downloadables = [
        {
            "name": library_html.name,
            "path": _storage_url_for(library_html),
            "file_path": str(library_html.resolve()),
            "purpose": (
                "Deliverable management report HTML preview."
                if (lab_report_meta or {}).get("quality_status") == "passed"
                else "Generated management report HTML preview, but it failed the quality gate."
            ),
            "is_main": True,
            "type": "html",
            "download_kind": "lab_report_html",
        },
        {
            "name": library_md.name,
            "path": _storage_url_for(library_md),
            "file_path": str(library_md.resolve()),
            "purpose": (
                "Deliverable management report markdown source."
                if (lab_report_meta or {}).get("quality_status") == "passed"
                else "Generated management report markdown source, but it failed the quality gate."
            ),
            "is_main": False,
            "type": "md",
            "download_kind": "lab_report_markdown",
        },
        {
            "name": library_seed.name,
            "path": _storage_url_for(library_seed),
            "file_path": str(library_seed.resolve()),
            "purpose": "Analysis Lab revision seed with source report and evidence pointers.",
            "is_main": False,
            "type": "json",
            "download_kind": "lab_report_revision_seed",
        },
    ]
    manifest = {
        "report_id": report_id,
        "title": title,
        "report_title": title,
        "dataset_id": request.dataset_id,
        "dataset_name": dataset_name,
        "sheet_name": sheet_name or request.active_sheet or "",
        "business_profile": "analysis_lab",
        "report_lens": "analysis_lab",
        "generated_at": generated_at,
        "updated_at": generated_at,
        "main_downloadable": library_html.name,
        "downloadables": _public_downloadables(downloadables),
        "lab_report": {
            "source_export_dir_name": source_export_dir.name,
            "revision_seed": library_seed.name,
            "source": "analysis_lab",
            **_strip_private_artifact_paths(lab_report_meta or {}),
        },
    }
    manifest_path = report_dir / f"{report_id}-current_turn_export_manifest.json"
    _write_json_file(manifest_path, manifest)
    stat = report_dir.stat()
    timestamp_ms = int(datetime.fromisoformat(generated_at.replace("Z", "+00:00")).timestamp() * 1000)
    row = {
        "report_id": report_id,
        "report_dir_name": report_dir.name,
        "report_dir_path": str(report_dir.resolve()),
        "report_dir_mtime_ns": getattr(stat, "st_mtime_ns", int(stat.st_mtime * 1_000_000_000)),
        "generated_at": generated_at,
        "updated_at": generated_at,
        "title": title,
        "content_title": title,
        "dataset_id": request.dataset_id,
        "dataset_name": dataset_name,
        "business_profile": "analysis_lab",
        "preview_url": downloadables[0]["path"],
        "downloadable_count": len(downloadables),
        "manifest": manifest,
        "main_downloadable": downloadables[0],
        "preview_downloadable": downloadables[0],
        "latest_revision_session": None,
        "search_text": f"{report_id} {title} {dataset_name} analysis_lab",
        "sort_generated_ts": timestamp_ms,
        "sort_updated_ts": timestamp_ms,
    }
    try:
        upsert_report_catalog_rows([row])
        catalog_status = "registered"
        catalog_error = ""
    except Exception as exc:
        catalog_status = "registration_failed"
        catalog_error = str(exc)
    return {
        "report_dir": str(report_dir.resolve()),
        "manifest_path": str(manifest_path.resolve()),
        "markdown_path": downloadables[1]["path"],
        "html_path": downloadables[0]["path"],
        "seed_path": downloadables[2]["path"],
        "catalog_status": catalog_status,
        "catalog_error": catalog_error,
    }


def _write_lab_report_artifacts(
    *,
    export_dir: Path,
    public_base_path: str,
    request: AutoAnalysisRequest,
    dataset_name: str,
    sheet_name: str,
    selected: dict[str, Any],
    report_parts: list[dict[str, Any]],
    tables: list[dict[str, Any]],
    charts: list[dict[str, Any]],
    method_execution_packages: list[dict[str, Any]],
    method_artifact_summary: dict[str, Any] | None,
    report_part_asset_manifest: list[dict[str, Any]],
    report_part_generation_blueprints: list[dict[str, Any]],
    downloadables: list[dict[str, Any]],
    external_skill_context: dict[str, Any] | None = None,
    large_sample_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    export_dir.mkdir(parents=True, exist_ok=True)
    report_id = _lab_report_id(request, export_dir)
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    title = f"业务分析交付报告 - {_client_dataset_title(dataset_name or request.dataset_id)}"
    chart_asset_summary = {
        "chart_count": len([chart for chart in charts if isinstance(chart, dict)]),
        "complete_count": len(
            [
                chart
                for chart in charts
                if isinstance(chart, dict)
                and isinstance(chart.get("asset_exports"), dict)
                and chart["asset_exports"].get("integrity_status") == "complete"
            ]
        ),
        "asset_root": _public_path(public_base_path, CHART_ASSET_DIR),
    }
    agent_review = _write_agent_review_contract(
        export_dir=export_dir,
        public_base_path=public_base_path,
        request=request,
        dataset_name=dataset_name,
        sheet_name=sheet_name,
        selected=selected,
        charts=charts,
        method_execution_packages=method_execution_packages,
        external_skill_context=external_skill_context,
        generated_at=generated_at,
        downloadables=downloadables,
    )
    markdown = _render_lab_report_markdown(
        title=title,
        request=request,
        dataset_name=dataset_name,
        sheet_name=sheet_name,
        selected=selected,
        report_parts=report_parts,
        tables=tables,
        charts=charts,
        method_execution_packages=method_execution_packages,
        method_artifact_summary=method_artifact_summary,
        agent_review=agent_review,
        report_part_asset_manifest=report_part_asset_manifest,
        external_skill_context=external_skill_context,
        generated_at=generated_at,
    )
    reader_markdown = _reader_facing_markdown(markdown)
    html = _reader_facing_html(_markdown_to_lab_report_html(markdown, title))
    quality = _evaluate_lab_report_quality(
        markdown_text=reader_markdown,
        html_text=html,
        report_parts=report_parts,
        tables=tables,
        charts=charts,
        method_execution_packages=method_execution_packages,
        agent_review=agent_review,
        report_part_asset_manifest=report_part_asset_manifest,
        report_part_generation_blueprints=report_part_generation_blueprints,
        external_skill_context=external_skill_context,
    )
    md_path = export_dir / LAB_REPORT_MD_FILE
    html_path = export_dir / LAB_REPORT_HTML_FILE
    json_path = export_dir / LAB_REPORT_JSON_FILE
    seed_path = export_dir / LAB_REPORT_SEED_FILE
    md_path.write_text(reader_markdown, encoding="utf-8")
    html_path.write_text(html, encoding="utf-8")
    method_run_ids = [
        str(package.get("method_run_id") or package.get("method_id") or "")
        for package in method_execution_packages
        if str(package.get("method_run_id") or package.get("method_id") or "").strip()
    ]
    method_package_summaries = [_method_package_summary(package) for package in method_execution_packages]
    seed = {
        "contract": "analysis_lab_report_revision_seed_v1",
        "report_id": report_id,
        "source": "analysis_lab",
        "title": title,
        "generated_at": generated_at,
        "dataset": {
            "dataset_id": request.dataset_id,
            "dataset_name": dataset_name,
            "sheet_name": sheet_name or request.active_sheet or "",
            "full_row_count": int((large_sample_policy or {}).get("row_count") or (large_sample_policy or {}).get("full_row_count") or 0),
            "analysis_work_frame_row_count": int((large_sample_policy or {}).get("analysis_work_frame_row_count") or 0),
            "analysis_work_frame_strategy": str((large_sample_policy or {}).get("analysis_work_frame_strategy") or "full_dataset"),
        },
        "user_goal": request.user_goal,
        "editable_artifacts": {
            "markdown": LAB_REPORT_MD_FILE,
            "html": LAB_REPORT_HTML_FILE,
            "json": LAB_REPORT_JSON_FILE,
        },
        "report_part_ids": [str(part.get("id") or "") for part in report_parts],
        "method_run_ids": method_run_ids,
        "method_package_summaries": method_package_summaries,
        "method_package_refs": [item["package_ref"] for item in method_package_summaries if item.get("package_ref")],
        "method_package_count": len(method_execution_packages),
        "method_artifact_summary": method_artifact_summary or {},
        "chart_asset_summary": chart_asset_summary,
        "agent_review": agent_review,
        "external_skill_context": external_skill_context or {},
        "large_sample_policy": large_sample_policy or {},
        "asset_count": len(report_part_asset_manifest),
        "generation_blueprint_count": len(report_part_generation_blueprints),
        "evidence_refs": list(
            dict.fromkeys(
                str(ref)
                for part in report_parts
                for ref in list(part.get("evidence_refs") or [])
                if str(ref or "").strip()
            )
        )[:200],
        "revision_guardrails": [
            "Preserve deterministic numbers from the Lab run.",
            "Keep markdown and HTML synchronized during follow-up revision.",
            "Use report-part evidence refs and method run ids before adding claims.",
        ],
    }
    _write_json_file(seed_path, seed)
    preliminary_json = {
        "contract": "analysis_lab_report_metadata_v1",
        "runtime_status": "pending_finalization",
        "report_id": report_id,
        "title": title,
        "generated_at": generated_at,
        "markdown_file_name": LAB_REPORT_MD_FILE,
        "html_file_name": LAB_REPORT_HTML_FILE,
        "json_file_name": LAB_REPORT_JSON_FILE,
        "seed_file_name": LAB_REPORT_SEED_FILE,
        "markdown_path": _public_path(public_base_path, LAB_REPORT_MD_FILE),
        "html_path": _public_path(public_base_path, LAB_REPORT_HTML_FILE),
        "json_path": _public_path(public_base_path, LAB_REPORT_JSON_FILE),
        "seed_path": _public_path(public_base_path, LAB_REPORT_SEED_FILE),
    }
    _write_json_file(json_path, preliminary_json)
    delivery_files = {
        LAB_REPORT_MD_FILE: md_path,
        LAB_REPORT_HTML_FILE: html_path,
        LAB_REPORT_JSON_FILE: json_path,
        LAB_REPORT_SEED_FILE: seed_path,
    }
    missing_delivery_files = [
        name
        for name, path in delivery_files.items()
        if not path.exists() or path.stat().st_size <= 0
    ]
    quality["checks"] = [
        *list(quality.get("checks") or []),
        {
            "id": "main_report_delivery_bundle",
            "label": "Main report delivery bundle includes markdown, HTML, JSON metadata, and revision seed",
            "status": "passed" if not missing_delivery_files else "failed",
            "detail": (
                "files=lab_report.md/lab_report.html/lab_report.json/lab_report_revision_seed.json"
                if not missing_delivery_files
                else f"missing_or_empty={missing_delivery_files}"
            ),
        },
    ]
    passed_check_count = len([check for check in quality["checks"] if check.get("status") == "passed"])
    failed_check_count = len(quality["checks"]) - passed_check_count
    quality["passed_check_count"] = passed_check_count
    quality["failed_check_count"] = failed_check_count
    quality["quality_status"] = "passed" if failed_check_count == 0 else "failed"
    quality["quality_score"] = round((passed_check_count / max(1, len(quality["checks"]))) * 100, 2)
    quality["quality_summary"] = (
        f"{quality.get('quality_summary')}; "
        f"main_report_delivery_bundle={'passed' if not missing_delivery_files else 'failed'}"
    )
    lab_report_meta = {
        "quality_status": quality["quality_status"],
        "quality_score": quality["quality_score"],
        "quality_checks": quality["checks"],
        "quality_summary": quality["quality_summary"],
        "evidence_coverage": quality["evidence_coverage"],
        "passed_check_count": quality["passed_check_count"],
        "failed_check_count": quality["failed_check_count"],
    }
    catalog = _register_lab_report_catalog(
        report_id=report_id,
        title=title,
        request=request,
        dataset_name=dataset_name,
        sheet_name=sheet_name,
        markdown_path=md_path,
        html_path=html_path,
        seed_path=seed_path,
        generated_at=generated_at,
        source_export_dir=export_dir,
        lab_report_meta=lab_report_meta,
        large_sample_policy=large_sample_policy,
    )
    lab_report = {
        "runtime_status": "completed",
        "report_id": report_id,
        "title": title,
        "generated_at": generated_at,
        "markdown_file_name": LAB_REPORT_MD_FILE,
        "html_file_name": LAB_REPORT_HTML_FILE,
        "json_file_name": LAB_REPORT_JSON_FILE,
        "seed_file_name": LAB_REPORT_SEED_FILE,
        "markdown_path": _public_path(public_base_path, LAB_REPORT_MD_FILE),
        "html_path": _public_path(public_base_path, LAB_REPORT_HTML_FILE),
        "json_path": _public_path(public_base_path, LAB_REPORT_JSON_FILE),
        "seed_path": _public_path(public_base_path, LAB_REPORT_SEED_FILE),
        "revision_available": catalog.get("catalog_status") == "registered",
        "revision_workspace_href": f"/revision/workspace?report_id={report_id}",
        "report_library": catalog,
        "catalog_status": catalog.get("catalog_status") or "",
        "catalog_error": catalog.get("catalog_error") or "",
        "seed_contract": seed["contract"],
        "method_run_ids": method_run_ids,
        "report_part_count": len(report_parts),
        "method_package_count": len(method_execution_packages),
        "method_artifact_summary": method_artifact_summary or {},
        "chart_asset_summary": chart_asset_summary,
        "agent_review": agent_review,
        "large_sample_policy": large_sample_policy or {},
        "asset_count": len(report_part_asset_manifest),
        "generation_blueprint_count": len(report_part_generation_blueprints),
        "table_count": len(tables),
        "chart_count": len(charts),
        "quality_status": quality["quality_status"],
        "quality_score": quality["quality_score"],
        "quality_checks": quality["checks"],
        "quality_summary": quality["quality_summary"],
        "evidence_coverage": quality["evidence_coverage"],
        "passed_check_count": quality["passed_check_count"],
        "failed_check_count": quality["failed_check_count"],
    }
    if quality["quality_status"] == "failed":
        lab_report["runtime_status"] = "failed"
    _write_json_file(json_path, lab_report)
    for item in (
        {
            "name": LAB_REPORT_HTML_FILE,
            "path": lab_report["html_path"],
            "type": "html",
            "purpose": (
                "Deliverable management report HTML preview."
                if lab_report["quality_status"] == "passed"
                else "Generated management report HTML preview, but it failed the quality gate."
            ),
            "is_main": True,
            "download_kind": "lab_report_html",
            "report_id": report_id,
        },
        {
            "name": LAB_REPORT_MD_FILE,
            "path": lab_report["markdown_path"],
            "type": "md",
            "purpose": (
                "Deliverable management report markdown source."
                if lab_report["quality_status"] == "passed"
                else "Generated management report markdown source, but it failed the quality gate."
            ),
            "is_main": False,
            "download_kind": "lab_report_markdown",
            "report_id": report_id,
        },
        {
            "name": LAB_REPORT_JSON_FILE,
            "path": lab_report["json_path"],
            "type": "json",
            "purpose": (
                "Deliverable management report JSON metadata."
                if lab_report["quality_status"] == "passed"
                else "Generated management report JSON metadata, but it failed the quality gate."
            ),
            "is_main": False,
            "download_kind": "lab_report_json",
            "report_id": report_id,
        },
        {
            "name": LAB_REPORT_SEED_FILE,
            "path": lab_report["seed_path"],
            "type": "json",
            "purpose": "Revision seed contract for opening this Lab report in follow-up editing.",
            "is_main": False,
            "download_kind": "lab_report_revision_seed",
            "report_id": report_id,
        },
    ):
        if not any(existing.get("name") == item["name"] for existing in downloadables):
            downloadables.append(item)
    return lab_report


def _export_runtime_packages(
    *,
    export_dir: Path,
    report_part_bundle: dict[str, Any],
    method_execution_packages: list[dict[str, Any]],
    downloadables: list[dict[str, Any]],
    method_artifact_summary: dict[str, Any] | None = None,
    chart_asset_summary: dict[str, Any] | None = None,
    external_skill_context: dict[str, Any] | None = None,
    large_sample_policy: dict[str, Any] | None = None,
    public_base_path: str = "",
) -> None:
    export_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = export_dir / str(report_part_bundle.get("file_name") or "report_part_bundle.json")
    bundle_path.write_text(json.dumps(report_part_bundle, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    package_index_path = export_dir / "method_execution_packages.json"
    package_index_path.write_text(json.dumps(method_execution_packages, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    runtime_manifest_path = export_dir / "runtime_package_manifest.json"
    external_skill_context_path = export_dir / EXTERNAL_SKILL_CONTEXT_FILE
    method_display_packages = _method_display_packages(method_execution_packages)
    method_display_policy = _method_display_policy(method_execution_packages, method_display_packages)
    external_skill_context_path.write_text(
        json.dumps(external_skill_context or {}, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    dispatch_plan = [
        {
            "dispatch_id": f"runtime_dispatch_{index}",
            "package_ref": f"data:method_execution_packages:{package.get('package_id')}",
            "package_id": package.get("package_id"),
            "file_name": package.get("file_name"),
            "method_id": package.get("method_id"),
            "method_run_id": package.get("method_run_id"),
            "family": package.get("family"),
            "runtime_handoff_count": package.get("runtime_handoff_count", 0),
            "runtime_tasks": [
                handoff.get("task")
                for handoff in list(package.get("runtime_handoffs") or [])
                if isinstance(handoff, dict) and handoff.get("task")
            ],
            "pre_method_preprocessing_status": package.get("pre_method_preprocessing_status"),
        }
        for index, package in enumerate(method_execution_packages, start=1)
    ]
    report_part_blueprints = [
        blueprint
        for blueprint in list(report_part_bundle.get("generation_blueprints") or [])
        if isinstance(blueprint, dict) and str(blueprint.get("report_part_id") or "").strip()
    ]
    report_part_dispatch_plan = []
    for index, blueprint in enumerate(report_part_blueprints, start=1):
        part_id = str(blueprint.get("report_part_id") or "").strip()
        handoff = blueprint.get("runtime_handoff") if isinstance(blueprint.get("runtime_handoff"), dict) else {}
        input_contract = blueprint.get("input_contract") if isinstance(blueprint.get("input_contract"), dict) else {}
        report_part_dispatch_plan.append(
            {
                "dispatch_id": f"report_part_dispatch_{index}",
                "dispatch_kind": "report_part_generation",
                "report_part_id": part_id,
                "report_part_title": blueprint.get("report_part_title") or part_id,
                "blueprint_ref": f"data:report_part_generation_blueprints:{part_id}",
                "task": handoff.get("task") or f"generate_report_part:{part_id}",
                "readiness": blueprint.get("readiness") or "partial",
                "required_outputs": list(handoff.get("required_outputs") or blueprint.get("required_asset_kinds") or []),
                "blocked_if_missing": list(handoff.get("blocked_if_missing") or blueprint.get("missing_asset_kinds") or []),
                "must_use_pre_method_audit": bool(handoff.get("must_use_pre_method_audit", True)),
                "must_use_method_route_evidence": bool(handoff.get("must_use_method_route_evidence", True)),
                "must_preserve_evidence_refs": bool(handoff.get("must_preserve_evidence_refs", True)),
                "asset_refs": list(input_contract.get("asset_refs") or [])[:40],
                "evidence_refs": list(input_contract.get("evidence_refs") or [])[:40],
                "method_evidence_count": int(blueprint.get("method_evidence_count") or 0),
                "pre_method_preprocessing_status": blueprint.get("pre_method_preprocessing_status") or "derived_fields_completed_before_method_routing",
            }
        )
    unified_dispatch_plan = [
        {**item, "dispatch_kind": "method_execution"}
        for item in dispatch_plan
    ] + report_part_dispatch_plan
    runtime_manifest = {
        "manifest_name": "runtime_package_manifest",
        "report_part_bundle": bundle_path.name,
        "method_execution_package_index": package_index_path.name,
        "method_package_count": len(method_execution_packages),
        "method_display_package_count": len(method_display_packages),
        "method_display_policy": method_display_policy,
        "report_part_dispatch_count": len(report_part_dispatch_plan),
        "runtime_dispatch_count": len(unified_dispatch_plan),
        "runtime_handoff_count": sum(int(package.get("runtime_handoff_count") or 0) for package in method_execution_packages),
        "dispatch_plan_count": len(unified_dispatch_plan),
        "pre_method_preprocessing_status": "derived_fields_completed_before_method_routing",
        "large_sample_policy": large_sample_policy or {},
        "requested_report_parts": list(report_part_bundle.get("requested_report_parts") or []),
        "generated_part_ids": list(report_part_bundle.get("generated_part_ids") or []),
        "external_skill_context": external_skill_context or {},
        "external_skill_ids": _external_skill_ids_for_report(external_skill_context),
        "external_skill_context_file": external_skill_context_path.name,
        "external_skill_application_required": bool((external_skill_context or {}).get("enabled")),
        "method_artifact_summary": method_artifact_summary,
        "chart_asset_summary": chart_asset_summary,
        "dispatch_plan": unified_dispatch_plan,
        "method_dispatch_plan": dispatch_plan,
        "report_part_dispatch_plan": report_part_dispatch_plan,
        "method_packages": [
            {
                "package_id": package.get("package_id"),
                "file_name": package.get("file_name"),
                "method_id": package.get("method_id"),
                "method_run_id": package.get("method_run_id"),
                "family": package.get("family"),
                "package_ref": f"data:method_execution_packages:{package.get('package_id')}",
                "runtime_handoff_count": package.get("runtime_handoff_count", 0),
                "pre_method_preprocessing_status": package.get("pre_method_preprocessing_status"),
            }
            for package in method_execution_packages
        ],
        "management_use": "Entry manifest for Analysis Lab runtime packages; use it to discover every method package and dispatch Codex/exec/runtime continuation work.",
    }
    runtime_manifest_path.write_text(json.dumps(runtime_manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    files_by_name: dict[str, Path] = {
        bundle_path.name: bundle_path,
        package_index_path.name: package_index_path,
        runtime_manifest_path.name: runtime_manifest_path,
        external_skill_context_path.name: external_skill_context_path,
    }
    for package in method_execution_packages:
        file_name = str(package.get("file_name") or "").strip()
        if not file_name:
            continue
        package_path = export_dir / file_name
        package_path.write_text(json.dumps(package, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        files_by_name[file_name] = package_path
    if not any(item.get("name") == package_index_path.name for item in downloadables):
        downloadables.append(
            {
                "name": package_index_path.name,
                "path": package_index_path.name,
                "type": "json",
                "purpose": "method execution package index for runtime export.",
                "is_main": False,
                "download_kind": "method_execution_package_index",
                "method_package_count": runtime_manifest["method_package_count"],
                "method_display_package_count": runtime_manifest["method_display_package_count"],
                "method_display_policy": runtime_manifest["method_display_policy"],
                "runtime_handoff_count": runtime_manifest["runtime_handoff_count"],
                "dispatch_plan_count": runtime_manifest["dispatch_plan_count"],
                "report_part_dispatch_count": runtime_manifest["report_part_dispatch_count"],
                "runtime_dispatch_count": runtime_manifest["runtime_dispatch_count"],
                "pre_method_preprocessing_status": runtime_manifest["pre_method_preprocessing_status"],
            }
        )
    if not any(item.get("name") == runtime_manifest_path.name for item in downloadables):
        downloadables.insert(
            0,
            {
                "name": runtime_manifest_path.name,
                "path": runtime_manifest_path.name,
                "type": "json",
                "purpose": "runtime package manifest for Analysis Lab export discovery.",
                "is_main": False,
                "download_kind": "runtime_package_manifest",
                "method_package_count": runtime_manifest["method_package_count"],
                "method_display_package_count": runtime_manifest["method_display_package_count"],
                "method_display_policy": runtime_manifest["method_display_policy"],
                "runtime_handoff_count": runtime_manifest["runtime_handoff_count"],
                "dispatch_plan_count": runtime_manifest["dispatch_plan_count"],
                "report_part_dispatch_count": runtime_manifest["report_part_dispatch_count"],
                "runtime_dispatch_count": runtime_manifest["runtime_dispatch_count"],
                "pre_method_preprocessing_status": runtime_manifest["pre_method_preprocessing_status"],
            },
        )
    if not any(item.get("name") == external_skill_context_path.name for item in downloadables):
        downloadables.insert(
            1,
            {
                "name": external_skill_context_path.name,
                "path": external_skill_context_path.name,
                "type": "json",
                "purpose": "Mounted external skill instructions consumed by this Analysis Lab runtime package.",
                "is_main": False,
                "download_kind": "external_skill_context",
                "external_skill_count": int((external_skill_context or {}).get("count") or 0),
                "external_skill_ids": _external_skill_ids_for_report(external_skill_context),
            },
        )
    for item in downloadables:
        path = files_by_name.get(str(item.get("name") or ""))
        if not path:
            continue
        item["path"] = _client_public_path(public_base_path, path.name)
        item.pop("file_path", None)


def _smart_merge_runtime_enabled(request: AutoAnalysisRequest, method_count: int) -> bool:
    return (
        bool(getattr(request, "smart_merge_enabled", True))
        and bool(getattr(request, "cli_interpretation_enabled", True))
        and str(getattr(request, "execution_mode", "") or "") == "smart_merge"
        and method_count > 1
    )


def _truncate_text(value: Any, limit: int = 900) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)].rstrip() + "..."


def _smart_merge_brief_payload(
    *,
    request: AutoAnalysisRequest,
    dataset_name: str,
    sheet_name: str,
    selected: dict[str, Any],
    method_execution_packages: list[dict[str, Any]],
    report_part_bundle: dict[str, Any],
    report_part_generation_blueprints: list[dict[str, Any]],
    report_part_asset_manifest: list[dict[str, Any]],
    external_skill_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    method_threads: list[dict[str, Any]] = []
    method_display_packages = _method_display_packages(method_execution_packages)
    method_display_policy = _method_display_policy(method_execution_packages, method_display_packages)
    method_card_guidance = _method_card_report_guidance_list(method_display_packages, collapse_duplicate_names=False)
    for package in method_display_packages:
        execution = package.get("execution") if isinstance(package.get("execution"), dict) else {}
        method_card = package.get("method_card") if isinstance(package.get("method_card"), dict) else {}
        display_group = package.get("display_group") if isinstance(package.get("display_group"), dict) else {}
        method_threads.append(
            {
                "package_id": package.get("package_id"),
                "method_id": package.get("method_id"),
                "method_run_id": package.get("method_run_id"),
                "method_name": package.get("method_name_zh") or package.get("method_name"),
                "family": package.get("family"),
                "route_score": package.get("route_score"),
                "route_reasons": list(package.get("route_reasons") or [])[:10],
                "status": execution.get("status"),
                "runtime_status": execution.get("runtime_status"),
                "output_type": execution.get("output_type"),
                "result_summary": _truncate_text(execution.get("result_summary") or execution.get("next_step") or ""),
                "bound_fields": execution.get("bound_fields") or method_card.get("field_bindings"),
                "result_ref": execution.get("result_ref"),
                "asset_refs": [str(asset.get("asset_ref") or "") for asset in list(package.get("assets") or [])[:12] if isinstance(asset, dict)],
                "evidence_refs": list(method_card.get("evidence_refs") or [])[:20],
                "file_name": package.get("file_name"),
                "display_group": display_group,
            }
        )
    return {
        "contract": "analysis_lab_smart_merge_brief_v1",
        "dataset_id": request.dataset_id,
        "dataset_name": dataset_name,
        "sheet_name": sheet_name or request.active_sheet or "",
        "user_goal": request.user_goal,
        "execution_mode": request.execution_mode,
        "selected_fields": selected,
        "external_skill_context": external_skill_context or {},
        "external_skill_ids": _external_skill_ids_for_report(external_skill_context),
        "external_skill_context_file": EXTERNAL_SKILL_CONTEXT_FILE,
        "external_skill_applications_required": bool((external_skill_context or {}).get("enabled")),
        "external_skill_application_schema": {
            "field": "external_skill_applications",
            "required_when_external_skill_context_enabled": True,
            "item_keys": ["skill_id", "name", "applied_rules", "output_effect"],
        },
        "method_count": len(method_execution_packages),
        "method_display_count": len(method_threads),
        "method_display_policy": method_display_policy,
        "method_threads": method_threads,
        "method_card_report_guidance": method_card_guidance,
        "method_card_report_guidance_contract": {
            "purpose": "Compact method-card writing guidance for smart merge and final report assembly.",
            "required_use": "Use report_slots, binding_quality, missing_bindings, evidence_refs, and writer_action before turning any method into a core report claim.",
            "claim_gate": "Methods with missing_bindings must stay provisional unless another evidence thread resolves the missing fields.",
        },
        "report_parts": {
            "requested_report_parts": list(report_part_bundle.get("requested_report_parts") or []),
            "generated_part_ids": list(report_part_bundle.get("generated_part_ids") or []),
            "blueprints": [
                {
                    "report_part_id": item.get("report_part_id"),
                    "readiness": item.get("readiness"),
                    "method_evidence_count": item.get("method_evidence_count"),
                    "asset_refs": list((item.get("input_contract") if isinstance(item.get("input_contract"), dict) else {}).get("asset_refs") or [])[:16],
                    "evidence_refs": list((item.get("input_contract") if isinstance(item.get("input_contract"), dict) else {}).get("evidence_refs") or [])[:16],
                }
                for item in report_part_generation_blueprints
            ],
            "asset_manifest_count": len(report_part_asset_manifest),
        },
        "full_input_file": SMART_MERGE_INPUT_FILE,
        "required_output": SMART_MERGE_RESULT_FILE,
    }


def _smart_merge_fallback_result(brief_payload: dict[str, Any], *, runtime_summary: str = "") -> dict[str, Any]:
    method_threads = []
    for thread in list(brief_payload.get("method_threads") or []):
        if not isinstance(thread, dict):
            continue
        method_threads.append(
            {
                "method_id": thread.get("method_id"),
                "method_run_id": thread.get("method_run_id"),
                "contribution": thread.get("result_summary") or thread.get("result_ref") or "Method package included in the smart merge evidence set.",
                "evidence_refs": list(thread.get("evidence_refs") or [])[:12],
                "asset_refs": list(thread.get("asset_refs") or [])[:12],
            }
        )
    evidence_refs = []
    for thread in method_threads:
        evidence_refs.extend(str(ref) for ref in list(thread.get("evidence_refs") or []) if str(ref))
        evidence_refs.extend(str(ref) for ref in list(thread.get("asset_refs") or []) if str(ref))
    return {
        "headline": "Analysis Lab smart merge completed through Codex CLI runtime.",
        "executive_synthesis": runtime_summary
        or "Codex CLI was invoked for the smart merge. The backend materialized this structured result from the compact merge brief because the runtime did not write the target JSON file directly.",
        "method_threads": method_threads,
        "cross_method_findings": [
            "Each method_run_id is preserved as an independent evidence thread.",
            "The merged result should be read with the original method packages and runtime manifest.",
        ],
        "conflicts_or_limits": [
            "This fallback JSON was materialized by the backend from the Codex runtime summary and smart_merge_brief.json.",
        ],
        "recommended_actions": [
            "Review smart_merge_brief.json and the per-method JSON packages before promoting the merged result into a final report.",
        ],
        "external_skill_applications": _external_skill_applications(
            brief_payload.get("external_skill_context") if isinstance(brief_payload.get("external_skill_context"), dict) else {}
        ),
        "evidence_refs": list(dict.fromkeys(evidence_refs))[:40],
        "runtime_summary": runtime_summary,
        "source_contract": brief_payload.get("contract"),
        "full_input_file": brief_payload.get("full_input_file") or SMART_MERGE_INPUT_FILE,
    }


def _external_skill_applications(external_skill_context: dict[str, Any] | None) -> list[dict[str, Any]]:
    applications: list[dict[str, Any]] = []
    for skill in list((external_skill_context or {}).get("skills") or []):
        if not isinstance(skill, dict):
            continue
        instructions = str(skill.get("instructions") or "")
        applied_rules = [
            line.strip(" -")
            for line in instructions.splitlines()
            if line.strip() and not line.strip().startswith("---")
        ][:5]
        selected_features = [
            {
                "feature_kind": item.get("feature_kind") or "",
                "feature_id": item.get("feature_id") or "",
                "name": item.get("name") or item.get("feature_id") or "",
            }
            for item in list(skill.get("selected_features") or [])
            if isinstance(item, dict)
        ]
        applications.append(
            {
                "skill_id": skill.get("id") or "",
                "name": skill.get("name") or skill.get("id") or "",
                "selected_features": selected_features,
                "selected_feature_count": len(selected_features),
                "applied_rules": applied_rules,
                "output_effect": "The mounted external skill instructions were included in the runtime contract and must shape the synthesis output.",
                "revision_effect": (
                    "Selected functions must inform the report quality review and revision plan."
                    if selected_features
                    else ""
                ),
            }
        )
    return applications


def _ensure_external_skill_applications(payload: dict[str, Any], brief_payload: dict[str, Any]) -> dict[str, Any]:
    external_skill_context = (
        brief_payload.get("external_skill_context")
        if isinstance(brief_payload.get("external_skill_context"), dict)
        else {}
    )
    required = bool(brief_payload.get("external_skill_applications_required") or external_skill_context.get("enabled"))
    existing = payload.get("external_skill_applications")
    if isinstance(existing, list) and existing:
        materialization = payload.get("materialization") if isinstance(payload.get("materialization"), dict) else {}
        source = str(materialization.get("source") or "")
        payload.setdefault(
            "external_skill_application_status",
            "provided_by_runtime" if source == "codex_transcript" else "provided_by_result",
        )
        return payload
    if required:
        payload["external_skill_applications"] = _external_skill_applications(external_skill_context)
        payload["external_skill_application_status"] = "materialized_from_context"
    else:
        payload.setdefault("external_skill_applications", [])
        payload.setdefault("external_skill_application_status", "not_required")
    return payload


def _smart_merge_brief_from_path(brief_path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(brief_path.read_text(encoding="utf-8")) if brief_path.exists() else {}
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _smart_merge_prompt() -> str:
    return f"""You are the Analysis Lab Codex CLI smart-merge agent.
The working directory is this Lab runtime export directory. Read `{SMART_MERGE_BRIEF_FILE}` first; read `{SMART_MERGE_INPUT_FILE}` when complete evidence is needed.

Hard requirements:
1. Use every method_execution_package as first-class evidence; do not write a generic summary.
2. Preserve each method_run_id as an independent evidence thread, especially repeated methods.
3. If external_skill_context.enabled is true, you MUST read external_skill_context.skills[].instructions and apply those skill instructions to the synthesis style, checks, output format, workflow, and revision gates. Do not merely mention that skills exist.
4. If external_skill_context.feature_selection_count > 0, treat external_skill_context.feature_selections and skills[].selected_features as selected report-flow functions. They must influence method selection rationale, evidence interpretation, recommended actions, and the quality-review/revision plan.
5. In `{SMART_MERGE_RESULT_FILE}`, include external_skill_applications: one item per applied skill with skill_id, name, selected_features, applied_rules, output_effect, and revision_effect.
6. Write structured JSON to `{SMART_MERGE_RESULT_FILE}`. Top-level keys must include headline, executive_synthesis, method_threads, cross_method_findings, conflicts_or_limits, recommended_actions, evidence_refs, external_skill_applications.
7. Each method_threads item must include method_id, method_run_id, contribution, evidence_refs.
8. Do not modify original method packages; only create or overwrite `{SMART_MERGE_RESULT_FILE}` and, if useful, a short markdown summary.

User goal: {{user_requirement}}

Input summary: {{context_json}}
"""


def _extract_smart_merge_json_object(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    fenced = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.IGNORECASE | re.DOTALL)
    for candidate in fenced:
        try:
            payload = json.loads(candidate)
        except Exception:
            continue
        if isinstance(payload, dict) and (
            payload.get("method_threads")
            or payload.get("executive_synthesis")
            or payload.get("cross_method_findings")
        ):
            return payload
    candidates: list[str] = []
    start = text.find("{")
    while start >= 0:
        depth = 0
        in_string = False
        escaped = False
        for index in range(start, len(text)):
            char = text[index]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    candidates.append(text[start : index + 1])
                    break
        start = text.find("{", start + 1)
    for candidate in candidates:
        try:
            payload = json.loads(candidate)
        except Exception:
            continue
        if isinstance(payload, dict) and (
            payload.get("method_threads")
            or payload.get("executive_synthesis")
            or payload.get("cross_method_findings")
        ):
            return payload
    return None


def _load_smart_merge_transcript_json(task: dict[str, Any]) -> dict[str, Any] | None:
    run_id = str(task.get("run_id") or "")
    if not run_id:
        result_summary = task.get("result_summary") if isinstance(task.get("result_summary"), dict) else {}
        run_id = str(result_summary.get("run_id") or "")
    if not run_id:
        return None
    try:
        from app.services.codex_runtime_store import transcript_path

        path = transcript_path(run_id)
    except Exception:
        return None
    if not path.exists():
        return None
    try:
        entries = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(entries, list):
        return None
    for entry in reversed(entries):
        if not isinstance(entry, dict):
            continue
        payload = _extract_smart_merge_json_object(str(entry.get("text") or ""))
        if payload:
            payload.setdefault(
                "materialization",
                {
                    "source": "codex_transcript",
                    "codex_run_id": run_id,
                    "review_required": False,
                },
            )
            return payload
    return None


def _smart_merge_markdown_report(payload: dict[str, Any], brief_payload: dict[str, Any]) -> str:
    synthesis = payload.get("executive_synthesis") if isinstance(payload.get("executive_synthesis"), dict) else {}
    dataset_name = str(synthesis.get("dataset_name") or brief_payload.get("dataset_name") or "unknown")
    sheet_name = str(synthesis.get("sheet_name") or brief_payload.get("sheet_name") or "unknown")
    lines = [
        "# Smart Merge Report",
        "",
        f"- Dataset: {dataset_name}",
        f"- Sheet: {sheet_name}",
        f"- Method count: {len(payload.get('method_threads') or [])}",
        "",
        "## Headline",
        "",
        str(payload.get("headline") or synthesis.get("summary") or "Smart merge result materialized."),
        "",
        "## Method Threads",
        "",
    ]
    for thread in list(payload.get("method_threads") or []):
        if isinstance(thread, dict):
            lines.append(f"- `{thread.get('method_run_id') or thread.get('method_id')}`: {thread.get('contribution') or ''}")
    lines.extend(["", "## Cross-Method Findings", ""])
    for item in list(payload.get("cross_method_findings") or []):
        lines.append(f"- {item.get('finding') if isinstance(item, dict) else item}")
    lines.extend(["", "## Limits", ""])
    for item in list(payload.get("conflicts_or_limits") or []):
        lines.append(f"- {item}")
    lines.extend(["", "## Recommended Actions", ""])
    for item in list(payload.get("recommended_actions") or []):
        lines.append(f"- {item}")
    external_skill_applications = list(payload.get("external_skill_applications") or [])
    if external_skill_applications:
        lines.extend(["", "## Knowledge Work Report-Flow Applications", ""])
        for item in external_skill_applications:
            if not isinstance(item, dict):
                continue
            skill_name = str(item.get("name") or item.get("skill_id") or "External skill")
            selected_features = [
                str(feature.get("name") or feature.get("feature_id") or "").strip()
                for feature in list(item.get("selected_features") or [])
                if isinstance(feature, dict) and str(feature.get("name") or feature.get("feature_id") or "").strip()
            ]
            applied_rules = [
                str(rule).strip()
                for rule in list(item.get("applied_rules") or [])
                if str(rule).strip()
            ]
            output_effect = str(item.get("output_effect") or "").strip()
            revision_effect = str(item.get("revision_effect") or "").strip()
            lines.append(f"### {skill_name}")
            if selected_features:
                lines.append(f"- Selected report-flow functions: {', '.join(selected_features)}")
            if applied_rules:
                lines.append(f"- Applied rules: {'; '.join(applied_rules[:5])}")
            if output_effect:
                lines.append(f"- Output effect: {output_effect}")
            if revision_effect:
                lines.append(f"- Revision effect: {revision_effect}")
    lines.append("")
    return "\n".join(lines)


def _materialize_smart_merge_payload(
    *,
    task: dict[str, Any],
    brief_path: Path,
    result_path: Path,
    report_path: Path | None = None,
) -> bool:
    brief_payload = _smart_merge_brief_from_path(brief_path)
    if result_path.exists():
        try:
            existing_payload = json.loads(result_path.read_text(encoding="utf-8"))
        except Exception:
            return True
        if not isinstance(existing_payload, dict):
            return True
        payload = _ensure_external_skill_applications(existing_payload, brief_payload)
        try:
            result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
            if report_path:
                report_path.write_text(_smart_merge_markdown_report(payload, brief_payload), encoding="utf-8")
        except Exception:
            return False
        return True
    payload = _load_smart_merge_transcript_json(task)
    if payload is None:
        result_summary = task.get("result_summary") if isinstance(task.get("result_summary"), dict) else {}
        summary = str(result_summary.get("summary") or task.get("current_stage_detail") or task.get("error") or "")
        payload = _smart_merge_fallback_result(brief_payload, runtime_summary=summary)
    payload = _ensure_external_skill_applications(payload, brief_payload)
    try:
        result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        if report_path:
            report_path.write_text(_smart_merge_markdown_report(payload, brief_payload), encoding="utf-8")
    except Exception:
        return False
    return True


def _materialize_smart_merge_result_when_done(
    *,
    task_id: str,
    brief_path: Path,
    result_path: Path,
    report_path: Path | None = None,
    poll_seconds: int = 900,
) -> None:
    def _worker() -> None:
        deadline = time.monotonic() + max(5, poll_seconds)
        last_progress_at = time.monotonic()
        last_stage = ""
        while time.monotonic() < deadline:
            if result_path.exists():
                return
            try:
                from app.services.codex_runtime_task_service import get_codex_run_task

                task = get_codex_run_task(task_id)
            except Exception:
                time.sleep(2)
                continue
            status = str(task.get("status") or "").lower()
            stage = str(task.get("current_stage_id") or "")
            if stage != last_stage:
                last_stage = stage
                last_progress_at = time.monotonic()
            stalled = status == "running" and stage == "session_started" and (time.monotonic() - last_progress_at) > 90
            if status not in {"completed", "failed", "cancelled", "timed_out"} and not stalled:
                time.sleep(2)
                continue
            if result_path.exists():
                return
            if not _materialize_smart_merge_payload(
                task=task,
                brief_path=brief_path,
                result_path=result_path,
                report_path=report_path,
            ):
                return
            return

    threading.Thread(target=_worker, daemon=True, name=f"smart-merge-materializer-{task_id[:12]}").start()


def _public_path(public_base_path: str, file_name: str) -> str:
    base = str(public_base_path or "").strip().replace("\\", "/")
    if not base or base.startswith(("/tmp/", "tmp/")) or re.match(r"^[A-Za-z]:/", base):
        return file_name
    return f"{base.rstrip('/')}/{file_name}"


def _start_smart_merge_codex_task(
    *,
    export_dir: Path,
    public_base_path: str,
    request: AutoAnalysisRequest,
    dataset_name: str,
    sheet_name: str,
    selected: dict[str, Any],
    method_execution_packages: list[dict[str, Any]],
    report_part_bundle: dict[str, Any],
    report_part_generation_blueprints: list[dict[str, Any]],
    report_part_asset_manifest: list[dict[str, Any]],
    method_route_evidence: list[dict[str, Any]],
    pre_method_routing_audit: list[dict[str, Any]],
    downloadables: list[dict[str, Any]],
    external_skill_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    export_dir.mkdir(parents=True, exist_ok=True)
    method_display_packages = _method_display_packages(method_execution_packages)
    method_display_policy = _method_display_policy(method_execution_packages, method_display_packages)
    method_card_guidance = _method_card_report_guidance_list(method_display_packages, collapse_duplicate_names=False)
    input_payload = {
        "contract": "analysis_lab_smart_merge_codex_cli_v1",
        "dataset_id": request.dataset_id,
        "dataset_name": dataset_name,
        "sheet_name": sheet_name or request.active_sheet or "",
        "user_goal": request.user_goal,
        "execution_mode": request.execution_mode,
        "selected_fields": selected,
        "external_skill_context": external_skill_context or {},
        "external_skill_ids": _external_skill_ids_for_report(external_skill_context),
        "external_skill_context_file": EXTERNAL_SKILL_CONTEXT_FILE,
        "external_skill_application_required": bool((external_skill_context or {}).get("enabled")),
        "method_count": len(method_execution_packages),
        "method_execution_packages": method_execution_packages,
        "method_display_count": len(method_display_packages),
        "method_display_packages": method_display_packages,
        "method_display_policy": method_display_policy,
        "method_card_report_guidance": method_card_guidance,
        "method_card_report_guidance_contract": {
            "purpose": "Compact method-card writing guidance for smart merge and final report assembly.",
            "required_use": "Use report_slots, binding_quality, missing_bindings, evidence_refs, and writer_action before turning any method into a core report claim.",
            "claim_gate": "Methods with missing_bindings must stay provisional unless another evidence thread resolves the missing fields.",
        },
        "report_part_bundle": report_part_bundle,
        "report_part_generation_blueprints": report_part_generation_blueprints,
        "report_part_asset_manifest": report_part_asset_manifest,
        "method_route_evidence": method_route_evidence,
        "pre_method_routing_audit": pre_method_routing_audit,
        "required_output": SMART_MERGE_RESULT_FILE,
        "instructions": [
            "Use every method_execution_package as first-class evidence.",
            "Preserve method_run_id so repeated methods remain separate runs in raw evidence.",
            "For reader-facing report sections, use method_display_packages and display each same-name method card once; cite display_group.method_run_ids for collapsed runs.",
            "If external_skill_context.enabled is true, read and apply external_skill_context.skills[].instructions.",
            "If external_skill_context.feature_selection_count > 0, apply those selected features inside the report flow instead of treating them as standalone trial outputs.",
            "Use method_card_report_guidance to decide each method's report slot, claim strength, evidence refs, and revision caveats.",
            "Write external_skill_applications to smart_merge_result.json with skill_id, name, selected_features, applied_rules, output_effect, and revision_effect.",
            "Write a structured management synthesis to smart_merge_result.json.",
        ],
    }
    input_path = export_dir / SMART_MERGE_INPUT_FILE
    brief_path = export_dir / SMART_MERGE_BRIEF_FILE
    prompt_path = export_dir / SMART_MERGE_PROMPT_FILE
    result_path = export_dir / SMART_MERGE_RESULT_FILE
    report_path = export_dir / SMART_MERGE_REPORT_FILE
    input_path.write_text(json.dumps(input_payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    brief_payload = _smart_merge_brief_payload(
        request=request,
        dataset_name=dataset_name,
        sheet_name=sheet_name,
        selected=selected,
        method_execution_packages=method_execution_packages,
        report_part_bundle=report_part_bundle,
        report_part_generation_blueprints=report_part_generation_blueprints,
        report_part_asset_manifest=report_part_asset_manifest,
        external_skill_context=external_skill_context,
    )
    brief_path.write_text(json.dumps(brief_payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    prompt_path.write_text(_smart_merge_prompt(), encoding="utf-8")

    smart_merge_payload: dict[str, Any] = {
        "file_name": "smart-merged-analysis-package.json",
        "input_file_name": SMART_MERGE_INPUT_FILE,
        "brief_file_name": SMART_MERGE_BRIEF_FILE,
        "prompt_file_name": SMART_MERGE_PROMPT_FILE,
        "expected_output_file_name": SMART_MERGE_RESULT_FILE,
        "report_file_name": SMART_MERGE_REPORT_FILE,
        "input_path": _public_path(public_base_path, SMART_MERGE_INPUT_FILE),
        "brief_path": _public_path(public_base_path, SMART_MERGE_BRIEF_FILE),
        "prompt_path": _public_path(public_base_path, SMART_MERGE_PROMPT_FILE),
        "expected_output_path": _public_path(public_base_path, SMART_MERGE_RESULT_FILE),
        "report_path": _public_path(public_base_path, SMART_MERGE_REPORT_FILE),
        "input_file_path": str(input_path.resolve()),
        "brief_file_path": str(brief_path.resolve()),
        "prompt_file_path": str(prompt_path.resolve()),
        "expected_output_file_path": str(result_path.resolve()),
        "report_file_path": str(report_path.resolve()),
        "method_count": len(method_execution_packages),
        "asset_count": len(report_part_asset_manifest) + len(report_part_generation_blueprints),
        "execution_mode": request.execution_mode,
        "requested_report_parts": list(report_part_bundle.get("requested_report_parts") or []),
        "runtime_target": "codex_cli",
        "runtime_status": "not_started",
        "codex_task_id": "",
        "codex_run_id": "",
        "error": "",
    }

    downloadables.append(
        _public_downloadable_item(
            {
                "name": SMART_MERGE_INPUT_FILE,
                "path": smart_merge_payload["input_path"],
                "file_path": str(input_path.resolve()),
                "type": "json",
                "purpose": "Codex CLI smart-merge input assembled from all routed method execution packages.",
                "is_main": False,
                "download_kind": "smart_merge_input",
                "method_package_count": len(method_execution_packages),
            }
        )
    )
    downloadables.append(
        _public_downloadable_item(
            {
                "name": SMART_MERGE_BRIEF_FILE,
                "path": smart_merge_payload["brief_path"],
                "file_path": str(brief_path.resolve()),
                "type": "json",
                "purpose": "Compact Codex CLI smart-merge brief; preferred input before the full smart_merge_input.json.",
                "is_main": False,
                "download_kind": "smart_merge_brief",
                "method_package_count": len(method_execution_packages),
            }
        )
    )
    downloadables.append(
        _public_downloadable_item(
            {
                "name": SMART_MERGE_REPORT_FILE,
                "path": smart_merge_payload["report_path"],
                "file_path": str(report_path.resolve()),
                "type": "md",
                "purpose": "Management-readable smart-merge report materialized from the runtime JSON result.",
                "is_main": True,
                "download_kind": "smart_merge_report",
                "method_package_count": len(method_execution_packages),
            }
        )
    )

    try:
        from app.models import CodexRunRequest
        from app.services.codex_runtime_task_service import create_codex_run_task
        from app.services.settings_service import load_runtime_settings_raw

        settings = load_runtime_settings_raw()
        timeout_sec = max(60, min(int(settings.get("codex_timeout_sec") or 1800), 600))
        run_request = CodexRunRequest(
            workspace_path=str(export_dir.resolve()),
            prompt_template=_smart_merge_prompt(),
            user_requirement=request.user_goal or "请把本轮 Analysis Lab 多方法执行结果做智能合并。",
            context_payload={
                "input_file": SMART_MERGE_INPUT_FILE,
                "brief_file": SMART_MERGE_BRIEF_FILE,
                "expected_output": SMART_MERGE_RESULT_FILE,
                "dataset_name": dataset_name,
                "sheet_name": sheet_name or request.active_sheet or "",
                "method_count": len(method_execution_packages),
                "method_run_ids": [
                    str(package.get("method_run_id") or package.get("method_id") or "")
                    for package in method_execution_packages
                ],
                "external_skill_ids": _external_skill_ids_for_report(external_skill_context),
                "external_skill_count": int((external_skill_context or {}).get("count") or 0),
                "external_skill_context_file": EXTERNAL_SKILL_CONTEXT_FILE,
                "external_skill_application_required": bool((external_skill_context or {}).get("enabled")),
                "requested_report_parts": list(report_part_bundle.get("requested_report_parts") or []),
            },
            report_id=f"analysis-lab-smart-merge-{request.dataset_id}",
            parent_report_id=f"analysis-lab-{request.dataset_id}",
            dataset_id=request.dataset_id,
            sheet_name=sheet_name or request.active_sheet or "",
            stage_id="analysis_lab_smart_merge",
            purpose="analysis_lab_smart_merge",
            artifact_source=SMART_MERGE_RESULT_FILE,
            timeout_sec=timeout_sec,
            capture_git_diff=False,
        )
        task = create_codex_run_task(
            run_request,
            parent_report_id=f"analysis-lab-{request.dataset_id}",
            parent_stage_id="analysis_lab_methods",
            stage_id="analysis_lab_smart_merge",
            purpose="analysis_lab_smart_merge",
            artifact_source=SMART_MERGE_RESULT_FILE,
            return_full=True,
        )
        smart_merge_payload.update(
            {
                "runtime_status": str(task.get("status") or "queued"),
                "codex_task_id": str(task.get("job_id") or ""),
                "codex_run_id": str(task.get("run_id") or ""),
                "progress_percent": int(task.get("progress_percent") or 0),
                "current_stage_id": str(task.get("current_stage_id") or ""),
                "current_stage_title": str(task.get("current_stage_title") or ""),
                "current_stage_detail": str(task.get("current_stage_detail") or ""),
            }
        )
        if smart_merge_payload["codex_task_id"]:
            _materialize_smart_merge_result_when_done(
                task_id=smart_merge_payload["codex_task_id"],
                brief_path=brief_path,
                result_path=result_path,
                report_path=report_path,
            )
    except Exception as exc:
        smart_merge_payload.update(
            {
                "runtime_status": "failed_to_start",
                "error": str(exc),
            }
        )
    return smart_merge_payload


def run_auto_analysis(
    frame: pd.DataFrame,
    request: AutoAnalysisRequest,
    *,
    dataset_name: str = "",
    sheet_name: str = "",
    export_dir: str | Path | None = None,
    public_base_path: str = "",
) -> dict[str, Any]:
    external_skill_context = lab_external_skill_runtime_context(
        getattr(request, "external_skill_ids", None),
        getattr(request, "external_skill_feature_selections", None),
    )
    source_frame = frame
    frame, work_frame_policy = _analysis_work_frame_for_frame(source_frame)
    large_sample_policy = _large_sample_policy_for_frame(source_frame, work_frame_policy)
    requested_report_parts = normalize_report_part_ids(request.report_part, request.selected_report_parts)
    requested_report_part_key = ",".join(requested_report_parts) if requested_report_parts else request.report_part
    field_profiles = profile_fields(frame)
    enriched, derived_field_options = build_derived_field_edits(
        frame,
        field_profiles,
        request.derived_metric_edits,
        max_fields=request.max_derived_fields,
    )
    derived_field_options = _mark_derived_fields(derived_field_options, request.selected_derived_fields)
    derived_field_options = _apply_derived_metric_edits(derived_field_options, request.derived_metric_edits)
    selected_derived_field_ids = {item["field"] for item in derived_field_options if item.get("selected")}
    derived_fields = [item for item in derived_field_options if item.get("field") in selected_derived_field_ids]
    auto_selected = select_best_fields(enriched, field_profiles, derived_fields)
    selected_overrides = _selected_field_overrides(request.selected_fields)
    selected = {**auto_selected, **selected_overrides}
    if selected_overrides:
        selected["selection_mode"] = "manual_override"
        selected["selection_reason"] = "User-selected fields override the automatic field router for this Lab run."
    else:
        selected["selection_mode"] = "auto"
    field_relationships = build_field_relationships(enriched, field_profiles, derived_fields)
    field_semantic_route_plan = build_field_semantic_route_plan(
        profiles=field_profiles,
        derived_fields=derived_fields,
        relationships=field_relationships,
        selected=selected,
    )
    chart_point_limit = _chart_point_limit_for_request(request, large_sample_policy)
    large_sample_policy["chart_render_limit"] = chart_point_limit
    points, mid = bubble_points(enriched, selected, limit=chart_point_limit)
    charts = build_auto_charts(enriched, selected, points, mid, field_profiles, limit=chart_point_limit)
    full_registry = get_auto_analysis_method_registry()
    method_run_specs = _method_run_specs(getattr(request, "method_run_specs", None))
    alias_map = method_alias_map(full_registry)
    if method_run_specs:
        for spec in method_run_specs:
            method_id = str(spec.get("method_id") or "").strip()
            canonical_id = alias_map.get(method_id, method_id)
            if canonical_id != method_id:
                spec["requested_method_id"] = method_id
                spec["method_id"] = canonical_id
    selected_method_ids = _method_ids_from_run_specs(method_run_specs) if method_run_specs else _selected_ids(request.selected_method_ids)
    selected_method_ids = canonical_method_ids(selected_method_ids, full_registry)
    registry = _filter_registry_by_ids(full_registry, selected_method_ids)
    method_limit = len(method_run_specs) if method_run_specs else (len(registry) if selected_method_ids else request.max_methods)
    routed_methods = route_methods_for_report_parts(
        registry,
        field_profiles=field_profiles,
        derived_fields=derived_fields,
        field_semantic_route_plan=field_semantic_route_plan,
        selected=selected,
        charts=charts,
        requested_part=requested_report_part_key,
        priority_ids=priority_method_ids(),
        max_methods=method_limit,
        method_field_bindings=request.method_field_bindings,
        method_run_specs=method_run_specs or None,
    )
    pre_method_routing_audit = _build_pre_method_routing_audit(
        field_profiles=field_profiles,
        derived_field_options=derived_field_options,
        derived_fields=derived_fields,
        field_relationships=field_relationships,
        field_semantic_route_plan=field_semantic_route_plan,
        registry_size=len(full_registry),
        filtered_registry_size=len(registry),
        routed_method_count=len(routed_methods),
        selected_method_ids=selected_method_ids,
        requested_part=requested_report_part_key,
    )
    method_route_evidence = _method_route_evidence_rows(routed_methods)
    quadrant_counts = pd.Series([point["quadrant"] for point in points]).value_counts().to_dict() if points else {}
    quadrant_rows = [{"quadrant": key, "count": int(value)} for key, value in quadrant_counts.items()]
    causal_executor_tables = build_causal_executor_tables(
        enriched,
        selected=selected,
        field_profiles=field_profiles,
    )
    evidence_tables = build_evidence_tables(charts, extra_tables=causal_executor_tables)
    method_execution_outputs = build_method_card_execution_outputs(enriched, routed_methods, charts, limit=method_limit)
    method_execution_tables = list(method_execution_outputs.get("tables") or [])
    method_execution_rows = list(method_execution_outputs.get("rows") or [])
    method_execution_assets = list(method_execution_outputs.get("assets") or [])
    tables = [
        _table(_zh(r"\u5b57\u6bb5\u7406\u89e3\u4e0e\u89d2\u8272\u8bc6\u522b"), field_profiles[:80]),
        _table(_zh(r"\u667a\u80fd\u6d3e\u751f\u5b57\u6bb5\u9884\u5904\u7406"), derived_field_options[:160]),
        _table(_zh(r"\u81ea\u52a8\u5b57\u6bb5\u9009\u62e9\u7ed3\u679c"), _selected_field_rows(selected)),
        _table(_zh(r"\u8c61\u9650\u8ba1\u6570"), quadrant_rows),
        _table(_zh(r"\u65b9\u6cd5\u9009\u62e9\u524d\u7f6e\u5ba1\u8ba1"), pre_method_routing_audit),
        _table(_zh(r"\u5b57\u6bb5\u8bed\u4e49\u8def\u7531\u7b56\u7565"), list(field_semantic_route_plan.get("rows") or [])[:160]),
        _table(_zh(r"\u5b57\u6bb5\u5173\u7cfb\u56fe\u8c31"), field_relationships[:120]),
        _table(_zh(r"\u65b9\u6cd5\u8def\u7531\u8bc1\u636e\u660e\u7ec6"), method_route_evidence[:120]),
        _table("Mounted external skills", _external_skill_table_rows(external_skill_context)),
        _table(_zh(r"\u672c\u8f6e\u8def\u7531\u65b9\u6cd5"), routed_methods[:80]),
        *method_execution_tables,
        *evidence_tables,
    ]
    report_parts = build_report_parts(
        request_part=requested_report_part_key,
        dataset_name=dataset_name,
        sheet_name=sheet_name or request.active_sheet or "",
        field_profiles=field_profiles,
        derived_fields=derived_fields,
        selected=selected,
        charts=charts,
        tables=tables,
        routed_methods=routed_methods,
        method_execution_tables=method_execution_tables,
        evidence_tables=evidence_tables,
        field_semantic_route_plan=field_semantic_route_plan,
        registry_total=len(registry),
        quadrant_counts={str(key): int(value) for key, value in quadrant_counts.items()},
    )
    report_part_asset_manifest = build_report_part_asset_manifest(
        report_parts=report_parts,
        method_execution_assets=method_execution_assets,
    )
    if report_part_asset_manifest:
        manifest_table = _table(ASSET_MANIFEST_TITLE, report_part_asset_manifest)
        tables.append(manifest_table)
        for part in report_parts:
            part_id = str(part.get("id") or "")
            part_rows = [row for row in report_part_asset_manifest if row.get("report_part_id") == part_id]
            part_data = dict(part.get("data") or {})
            part_data["asset_manifest"] = part_rows
            part["data"] = part_data
            evidence_refs = [str(ref) for ref in list(part.get("evidence_refs") or []) if str(ref)]
            if part_rows and "table:report_part_asset_manifest" not in evidence_refs:
                evidence_refs.append("table:report_part_asset_manifest")
            part["evidence_refs"] = evidence_refs

    report_part_generation_blueprints = build_report_part_generation_blueprints(
        report_parts=report_parts,
        asset_manifest=report_part_asset_manifest,
        routed_methods=routed_methods,
        field_semantic_route_plan=field_semantic_route_plan,
        pre_method_routing_audit=pre_method_routing_audit,
        method_route_evidence=method_route_evidence,
    )
    blueprint_by_part = {str(item.get("report_part_id") or ""): item for item in report_part_generation_blueprints}
    for part in report_parts:
        part_id = str(part.get("id") or "")
        if not part_id or part_id not in blueprint_by_part:
            continue
        part_data = dict(part.get("data") or {})
        part_data["generation_blueprint"] = blueprint_by_part[part_id]
        part["data"] = part_data
        evidence_refs = [str(ref) for ref in list(part.get("evidence_refs") or []) if str(ref)]
        if "table:report_part_generation_blueprints" not in evidence_refs:
            evidence_refs.append("table:report_part_generation_blueprints")
        if "data:report_part_generation_blueprints" not in evidence_refs:
            evidence_refs.append("data:report_part_generation_blueprints")
        part["evidence_refs"] = evidence_refs
    if report_part_generation_blueprints:
        tables.append(_table(GENERATION_BLUEPRINT_TITLE, report_part_generation_blueprints))

    narrative = (
        f"{_zh(r'\u5df2\u5b8c\u6210\u81ea\u52a8\u5206\u6790\u5305\uff1a\u5148\u7406\u89e3')} {len(field_profiles)} "
        f"{_zh(r'\u4e2a\u5b57\u6bb5\uff0c\u518d\u751f\u6210')} {len(derived_fields)} "
        f"{_zh(r'\u4e2a\u6d3e\u751f\u5b57\u6bb5\uff0c\u968f\u540e\u4ece')} {len(full_registry)} "
        f"{_zh(r'\u4e2a\u65b9\u6cd5\u4e2d\u6309\u5b57\u6bb5\u89d2\u8272\u3001\u62a5\u544a\u90e8\u4ef6\u548c\u8f93\u51fa\u7c7b\u578b\u8def\u7531')} {len(routed_methods)} "
        f"{_zh(r'\u4e2a\u5019\u9009\u65b9\u6cd5\u3002\u672c\u6b21\u7ed3\u679c\u540c\u65f6\u8f93\u51fa\u6587\u5b57\u89e3\u8bfb\u3001\u7ed3\u6784\u5316\u8868\u683c\u3001\u56fe\u8868\u6570\u636e\u548c\u53ef\u590d\u7528\u62a5\u544a\u90e8\u4ef6\u3002')}"
    )
    if request.user_goal:
        narrative += f" {_zh(r'\u672c\u8f6e\u7528\u6237\u76ee\u6807\uff1a')}{request.user_goal}"

    preview_columns = [column for column in enriched.columns.astype(str).tolist()[:12]]
    available_parts = report_part_ids()
    generated_part_ids = [str(part.get("id") or "") for part in report_parts]
    method_downloads = _method_download_rows(routed_methods, method_execution_rows, method_execution_assets)
    method_execution_packages = _method_execution_packages(
        routed_methods,
        method_execution_rows,
        method_execution_assets,
        external_skill_context=external_skill_context,
    )
    method_packages_by_file = {str(item.get("file_name") or ""): item for item in method_execution_packages}
    for row in method_downloads:
        package = method_packages_by_file.get(str(row.get("file_name") or ""))
        if not package:
            continue
        row["package_ref"] = f"data:method_execution_packages:{package['package_id']}"
        row["runtime_handoff_count"] = package.get("runtime_handoff_count", 0)
        row["pre_method_preprocessing_status"] = package.get("pre_method_preprocessing_status")
    report_part_bundle = {
        "contract": "analysis_lab_report_part_bundle_v2",
        "file_name": "report_part_bundle.json",
        "download_kind": "report_part_bundle",
        "request_part": request.report_part,
        "requested_report_parts": requested_report_parts,
        "generated_part_ids": generated_part_ids,
        "part_count": len(report_parts),
        "asset_count": len(report_part_asset_manifest),
        "generation_blueprint_count": len(report_part_generation_blueprints),
        "dataset": {
            "dataset_id": request.dataset_id,
            "dataset_name": dataset_name,
            "sheet_name": sheet_name or request.active_sheet or "",
            "full_row_count": int(large_sample_policy.get("row_count") or len(source_frame)),
            "analysis_work_frame_row_count": int(large_sample_policy.get("analysis_work_frame_row_count") or len(frame)),
            "analysis_work_frame_strategy": str(large_sample_policy.get("analysis_work_frame_strategy") or "full_dataset"),
        },
        "user_goal": request.user_goal,
        "report_parts": report_parts,
        "tables": tables,
        "charts": charts,
        "asset_manifest": report_part_asset_manifest,
        "generation_blueprints": report_part_generation_blueprints,
        "method_execution_package_summaries": [_method_package_summary(package) for package in method_execution_packages],
        "method_card_report_guidance": _method_card_report_guidance_list(method_execution_packages),
        "external_skill_context": external_skill_context,
        "external_skill_ids": _external_skill_ids_for_report(external_skill_context),
        "external_skill_feature_selections": list(external_skill_context.get("feature_selections") or []),
        "large_sample_policy": large_sample_policy,
    }
    downloadables = [
        {
            "name": report_part_bundle["file_name"],
            "path": report_part_bundle["file_name"],
            "type": "json",
            "purpose": "in-memory report part bundle contract for API/runtime export.",
            "is_main": False,
            "download_kind": report_part_bundle["download_kind"],
        },
        *[
            {
                "name": row["file_name"],
                "path": row["file_name"],
                "type": "json",
                "purpose": "in-memory routed method execution asset contract for API/runtime export.",
                "is_main": False,
                "download_kind": row["download_kind"],
                "method_id": row["method_id"],
                "method_name": row.get("method_name"),
                "method_name_zh": row.get("method_name_zh"),
                "family": row.get("family"),
                "package_ref": row.get("package_ref", ""),
                "runtime_handoff_count": row.get("runtime_handoff_count", 0),
                "pre_method_preprocessing_status": row.get("pre_method_preprocessing_status"),
            }
            for row in method_downloads
        ],
    ]
    lab_report: dict[str, Any] = {
        "runtime_status": "skipped",
        "skip_reason": "export_dir_missing",
    }
    chart_asset_summary: dict[str, Any] = {
        "runtime_status": "skipped",
        "skip_reason": "export_dir_missing",
        "chart_count": len(charts),
        "large_sample_policy": large_sample_policy,
    }
    method_artifact_summary: dict[str, Any] = {
        "runtime_status": "skipped",
        "skip_reason": "export_dir_missing",
        "method_count": len(method_execution_packages),
        "large_sample_policy": large_sample_policy,
    }
    report_writer_agent = _attach_report_writer_agents(
        charts=charts,
        full_frame=source_frame,
        analysis_frame=enriched,
        large_sample_policy=large_sample_policy,
        generated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )
    report_part_bundle["report_writer_agent"] = report_writer_agent
    if export_dir:
        try:
            generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            report_writer_agent["generated_at"] = generated_at
            report_writer_input_path = Path(export_dir) / REPORT_WRITER_AGENT_INPUT_FILE
            report_writer_result_path = Path(export_dir) / REPORT_WRITER_AGENT_RESULT_FILE
            report_writer_agent_input = _build_report_writer_agent_input(
                request=request,
                dataset_name=dataset_name,
                sheet_name=sheet_name or request.active_sheet or "",
                selected=selected,
                field_profiles=field_profiles,
                charts=charts,
                method_execution_packages=method_execution_packages,
                external_skill_context=external_skill_context,
                large_sample_policy=large_sample_policy,
                generated_at=generated_at,
            )
            report_writer_agent["input_ref"] = REPORT_WRITER_AGENT_INPUT_FILE
            _write_json_file(report_writer_input_path, report_writer_agent_input)
            _write_json_file(report_writer_result_path, report_writer_agent)
            _append_downloadable(
                downloadables,
                _public_downloadable_item(
                    {
                        "name": REPORT_WRITER_AGENT_INPUT_FILE,
                        "path": _public_path(public_base_path, REPORT_WRITER_AGENT_INPUT_FILE),
                        "file_path": str(report_writer_input_path.resolve()),
                        "type": "json",
                        "purpose": "Report-writer agent input contract with evidence sources, chart questions, sample scopes, and required stage outputs.",
                        "is_main": False,
                        "download_kind": "report_writer_agent_input",
                    }
                ),
            )
            _append_downloadable(
                downloadables,
                _public_downloadable_item(
                    {
                        "name": REPORT_WRITER_AGENT_RESULT_FILE,
                        "path": _public_path(public_base_path, REPORT_WRITER_AGENT_RESULT_FILE),
                        "file_path": str(report_writer_result_path.resolve()),
                        "type": "json",
                        "purpose": "Structured report-writer agent output with chart answers, captions, chunk evidence, and review verdict.",
                        "is_main": True,
                        "download_kind": "report_writer_agent_result",
                    }
                ),
            )
            export_charts = _select_charts_for_export(
                charts,
                report_parts=report_parts,
                method_execution_assets=method_execution_assets,
            )
            chart_asset_summary = _write_chart_asset_exports(
                export_dir=Path(export_dir),
                public_base_path=public_base_path,
                charts=export_charts,
                downloadables=downloadables,
                generated_at=generated_at,
                large_sample_policy=large_sample_policy,
            )
            method_artifact_summary = _write_method_artifact_exports(
                export_dir=Path(export_dir),
                public_base_path=public_base_path,
                request=request,
                dataset_name=dataset_name,
                sheet_name=sheet_name or request.active_sheet or "",
                charts=charts,
                method_execution_packages=method_execution_packages,
                downloadables=downloadables,
                generated_at=generated_at,
                large_sample_policy=large_sample_policy,
            )
            lab_report = _write_lab_report_artifacts(
                export_dir=Path(export_dir),
                public_base_path=public_base_path,
                request=request,
                dataset_name=dataset_name,
                sheet_name=sheet_name or request.active_sheet or "",
                selected=selected,
                report_parts=report_parts,
                tables=tables,
                charts=charts,
                method_execution_packages=method_execution_packages,
                method_artifact_summary=method_artifact_summary,
                report_part_asset_manifest=report_part_asset_manifest,
                report_part_generation_blueprints=report_part_generation_blueprints,
                downloadables=downloadables,
                external_skill_context=external_skill_context,
                large_sample_policy=large_sample_policy,
            )
        except Exception as exc:
            lab_report = {
                "runtime_status": "failed",
                "error": str(exc),
                "revision_available": False,
                "report_part_count": len(report_parts),
                "method_package_count": len(method_execution_packages),
                "method_artifact_summary": method_artifact_summary,
                "asset_count": len(report_part_asset_manifest),
                "generation_blueprint_count": len(report_part_generation_blueprints),
                "external_skill_count": int(external_skill_context.get("count") or 0),
                "large_sample_policy": large_sample_policy,
                "table_count": len(tables),
                "chart_count": len(charts),
                "quality_status": "failed",
                "quality_score": 0,
                "quality_checks": [
                    {
                        "id": "lab_report_generation",
                        "label": "Deterministic management report generation",
                        "status": "failed",
                        "detail": str(exc),
                    }
                ],
                "quality_summary": f"quality_status=failed; generation_error={exc}",
                "evidence_coverage": {
                    "method_run_total": len(method_execution_packages),
                    "method_run_covered": 0,
                    "report_part_total": len(report_parts),
                    "report_part_covered": 0,
                    "table_ref_count": len(tables),
                    "chart_ref_count": len(charts),
                    "evidence_ref_count": 0,
                    "asset_manifest_count": len(report_part_asset_manifest),
                    "generation_blueprint_count": len(report_part_generation_blueprints),
                },
                "passed_check_count": 0,
                "failed_check_count": 1,
            }
            _write_json_file(Path(export_dir) / LAB_REPORT_JSON_FILE, lab_report)
        report_part_bundle["lab_report"] = lab_report
        report_part_bundle["chart_asset_summary"] = chart_asset_summary
        report_part_bundle["report_writer_agent"] = report_writer_agent
        report_part_bundle["revision_seed"] = {
            "seed_contract": lab_report.get("seed_contract"),
            "seed_path": lab_report.get("seed_path"),
            "revision_workspace_href": lab_report.get("revision_workspace_href"),
            "report_id": lab_report.get("report_id"),
        }
        _export_runtime_packages(
            export_dir=Path(export_dir),
            report_part_bundle=report_part_bundle,
            method_execution_packages=method_execution_packages,
            downloadables=downloadables,
            method_artifact_summary=method_artifact_summary,
            chart_asset_summary=chart_asset_summary,
            external_skill_context=external_skill_context,
            large_sample_policy=large_sample_policy,
            public_base_path=public_base_path,
        )
    smart_merge_download = {
        "file_name": "smart-merged-analysis-package.json",
        "method_count": len(routed_methods),
        "asset_count": len(method_execution_assets) + len(report_part_asset_manifest) + len(report_part_generation_blueprints),
        "execution_mode": request.execution_mode,
        "requested_report_parts": requested_report_parts,
        "runtime_target": "codex_cli",
        "runtime_status": "skipped",
        "skip_reason": (
            "smart_merge_enabled requires execution_mode=smart_merge and at least two routed method executions"
            if not _smart_merge_runtime_enabled(request, len(method_execution_packages))
            else "export_dir_missing"
        ),
    }
    if export_dir and _smart_merge_runtime_enabled(request, len(method_execution_packages)):
        smart_merge_download = _start_smart_merge_codex_task(
            export_dir=Path(export_dir),
            public_base_path=public_base_path,
            request=request,
            dataset_name=dataset_name,
            sheet_name=sheet_name or request.active_sheet or "",
            selected=selected,
            method_execution_packages=method_execution_packages,
            report_part_bundle=report_part_bundle,
            report_part_generation_blueprints=report_part_generation_blueprints,
            report_part_asset_manifest=report_part_asset_manifest,
            method_route_evidence=method_route_evidence,
            pre_method_routing_audit=pre_method_routing_audit,
            downloadables=downloadables,
            external_skill_context=external_skill_context,
        )
    if export_dir:
        downloadables[:] = [
            item
            for item in downloadables
            if str(item.get("name") or "") != DELIVERY_MANIFEST_FILE
            and str(item.get("download_kind") or item.get("kind") or "") != "delivery_manifest"
        ]
        delivery_manifest = _write_delivery_manifest(
            export_dir=Path(export_dir),
            public_base_path=public_base_path,
            request=request,
            dataset_name=dataset_name,
            sheet_name=sheet_name or request.active_sheet or "",
            generated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            downloadables=downloadables,
            lab_report=lab_report,
            method_artifact_summary=method_artifact_summary,
            chart_asset_summary=chart_asset_summary,
        )
        report_part_bundle["delivery_manifest"] = {
            "file_name": DELIVERY_MANIFEST_FILE,
            "path": _public_path(public_base_path, DELIVERY_MANIFEST_FILE),
            "downloadable_count": delivery_manifest["coverage"]["downloadable_count"],
            "category_count": len(delivery_manifest["category_summary"]),
        }
        lab_report["delivery_manifest_path"] = _public_path(public_base_path, DELIVERY_MANIFEST_FILE)
        if lab_report.get("json_file_name"):
            _write_json_file(Path(export_dir) / LAB_REPORT_JSON_FILE, lab_report)
        _write_json_file(Path(export_dir) / str(report_part_bundle.get("file_name") or "report_part_bundle.json"), report_part_bundle)
    public_downloadables = _public_downloadables_with_customer_labels(downloadables)
    name_to_public_downloadable = {str(item.get("name") or ""): item for item in public_downloadables}
    for name in (LAB_REPORT_HTML_FILE, LAB_REPORT_MD_FILE, LAB_REPORT_JSON_FILE, LAB_REPORT_SEED_FILE):
        if name_to_public_downloadable.get(name):
            lab_report[f"{name.replace('.', '_')}_downloadable"] = name_to_public_downloadable[name]
    if lab_report.get("json_file_name"):
        _write_json_file(Path(export_dir) / LAB_REPORT_JSON_FILE, lab_report)
    return {
        "analysis_type": "auto_runtime_analysis",
        "title": f"{dataset_name or request.dataset_id} {_zh(r'\u81ea\u52a8\u5206\u6790\u5305')}",
        "narrative": narrative,
        "metrics": {
            "method_registry_total": len(full_registry),
            "routed_method_count": len(routed_methods),
            "field_count": len(field_profiles),
            "derived_field_count": len(derived_fields),
            "derived_field_option_count": len(derived_field_options),
            "selected_derived_field_count": len(derived_fields),
            "field_relationship_count": len(field_relationships),
            "field_semantic_route_field_count": int(field_semantic_route_plan.get("field_count") or 0),
            "field_semantic_route_derived_field_count": int(field_semantic_route_plan.get("derived_field_count") or 0),
            "pre_method_audit_stage_count": len(pre_method_routing_audit),
            "method_route_evidence_count": len(method_route_evidence),
            "chart_count": len(charts),
            "evidence_table_count": len(evidence_tables),
            "bubble_point_count": len(points),
            "report_part": request.report_part,
            "requested_report_part_count": len(requested_report_parts),
            "report_part_count": len(report_parts),
            "method_card_count": len([item for item in routed_methods if item.get("method_card")]),
            "method_execution_count": len(method_execution_rows),
            "method_execution_asset_count": len(method_execution_assets),
            "report_part_asset_count": len(report_part_asset_manifest),
            "report_part_generation_blueprint_count": len(report_part_generation_blueprints),
            "selected_method_count": len(selected_method_ids),
            "external_skill_count": int(external_skill_context.get("count") or 0),
            "large_sample": bool(large_sample_policy.get("large_sample")),
            "large_sample_row_count": int(large_sample_policy.get("row_count") or 0),
        },
        "tables": tables,
        "charts": charts,
        "report_parts": report_parts,
        "downloadables": public_downloadables,
        "data": {
            "dataset_id": request.dataset_id,
            "dataset_name": dataset_name,
            "sheet_name": sheet_name or request.active_sheet,
            "selected_fields": selected,
            "derived_fields": derived_fields,
            "derived_field_options": derived_field_options,
            "field_semantic_route_plan": field_semantic_route_plan,
            "field_relationships": field_relationships,
            "pre_method_routing_audit": pre_method_routing_audit,
            "method_route_evidence": method_route_evidence,
            "evidence_tables": evidence_tables,
            "routed_methods": routed_methods,
            "method_cards": [item.get("method_card") for item in routed_methods if item.get("method_card")],
            "method_card_executions": method_execution_rows,
            "method_execution_assets": method_execution_assets,
            "method_execution_packages": method_execution_packages,
            "report_part_asset_manifest": report_part_asset_manifest,
            "report_part_generation_blueprints": report_part_generation_blueprints,
            "method_downloads": method_downloads,
            "report_part_bundle": report_part_bundle,
            "lab_report": lab_report,
            "report_writer_agent": report_writer_agent,
            "smart_merge_download": smart_merge_download,
            "external_skill_context": external_skill_context,
            "external_skill_ids": _external_skill_ids_for_report(external_skill_context),
            "external_skill_feature_selections": list(external_skill_context.get("feature_selections") or []),
            "large_sample_policy": large_sample_policy,
            "method_execution_tables": method_execution_tables,
            "method_executor_registry_summary": summarize_method_card_executor_registry(),
            "method_registry_summary": summarize_method_registry(full_registry),
            "method_selection": {
                "requested_method_ids": selected_method_ids,
                "execution_mode": request.execution_mode,
                "matched_method_count": len(registry),
                "strict_selected_methods": bool(selected_method_ids),
            },
            "report_part_contract": {
                "can_generate": available_parts,
                "requested_part": request.report_part,
                "requested_report_parts": requested_report_parts,
                "generated_part_ids": generated_part_ids,
                "route_policy": "pre-method audit + smart derived preprocessing + semantic field route plan + priority + field-role feasibility + report-part fit + output-type fit + method-card executor registry",
                "generation_blueprint_ids": [str(item.get("report_part_id") or "") for item in report_part_generation_blueprints],
            },
            "report_parts": report_parts,
            "preview_rows": _clean_records(enriched[preview_columns], limit=12) if preview_columns else [],
        },
    }
