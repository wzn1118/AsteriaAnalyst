from __future__ import annotations

import ast
import csv
import json
import math
import re
import warnings
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


SUPPORTED_METRIC_CHART_FAMILIES = {
    "contribution_pareto",
    "top_n_bar",
    "abc_stacked",
    "efficiency_heatmap",
    "grouped_bar",
    "funnel",
    "cost_conversion_quadrant",
    "risk_bubble",
    "top_bottom_risk_ranking",
    "time_trend_grid",
    "line_trend",
    "growth_slope",
    "pulse_chart",
    "custom_top_bottom",
    "custom_trend",
    "custom_mix",
    "custom_correlation_matrix",
    "confidence_matrix",
    "direct_derived_proxy_split",
    "semantic_coverage_map",
}

_DEFAULT_MAIN_REPORT_TARGET_MIN = 12
_DEFAULT_MAIN_REPORT_TARGET_MAX = 16
_DEFAULT_APPENDIX_LIMIT = 32

GENERIC_VISUAL_BAND_INDEX_JSON_NAME = "generic_visual_band_index.json"
GENERIC_VISUAL_BAND_INDEX_CSV_NAME = "generic_visual_band_index.csv"
GENERIC_BUBBLE_COVERAGE_MANIFEST_NAME = "generic_bubble_coverage_manifest.json"
GENERIC_VISUAL_ROUTE_CONTRACT_JSON_NAME = "generic_visual_route_contract.json"
GENERIC_VISUAL_ROUTE_CONTRACT_MD_NAME = "generic_visual_route_contract.md"

_DIMENSION_PATTERNS: dict[str, list[str]] = {
    "category": ["category", "cate", "品类", "类目", "分类"],
    "product": ["product", "item", "goods", "商品", "货品", "title"],
    "sku": ["sku", "spu", "stockcode", "product_id", "item_id", "鍟嗗搧id", "璐у彿"],
    "seller": ["seller", "shop", "store", "merchant", "卖家", "店铺", "商家"],
    "supplier_proxy": ["supplier", "vendor", "seller", "供应商", "卖家", "merchant"],
    "region": ["region", "province", "state", "city", "area", "district", "省", "市", "区域", "地区"],
    "route": ["route", "sellerstate", "customerstate", "sellercity", "customercity", "璺敱", "璺緞"],
    "time": ["date", "day", "week", "month", "period", "timestamp", "日期", "时间", "周", "月"],
    "channel": ["channel", "source", "campaign", "placement", "media", "渠道", "来源", "投放", "媒体"],
    "audience": ["audience", "segment", "customer", "user", "用户", "客群", "客户", "人群"],
}

_METRIC_PRIORITY_RULES: tuple[tuple[str, int], ...] = (
    ("contribution", 95),
    ("share", 90),
    ("abc", 90),
    ("trend", 88),
    ("change", 86),
    ("conversion", 84),
    ("ctr", 82),
    ("cvr", 82),
    ("cpa", 82),
    ("cpc", 80),
    ("cpm", 78),
    ("inventory", 78),
    ("margin", 76),
    ("rate", 74),
    ("ratio", 72),
    ("confidence", 52),
    ("coverage", 48),
)


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _safe_float(value: Any) -> float | None:
    try:
        numeric = float(value)
    except Exception:
        return None
    if math.isnan(numeric) or math.isinf(numeric):
        return None
    return numeric


def _normalize_token(value: Any) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", _safe_text(value).lower())


def _slug(value: Any, *, limit: int = 48) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", _safe_text(value).lower()).strip("_")
    return (slug[:limit].strip("_") or "metric").lower()


def _read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists() or not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _read_csv_rows(path: Path, *, limit: int = 0) -> list[dict[str, Any]]:
    if not path.exists() or not path.is_file():
        return []
    try:
        frame = pd.read_csv(path, encoding="utf-8-sig")
    except Exception:
        try:
            frame = pd.read_csv(path, encoding="utf-8")
        except Exception:
            return []
    if limit and len(frame) > limit:
        frame = frame.head(limit)
    return frame.to_dict(orient="records")


def _parse_list_like(value: Any) -> list[str]:
    if isinstance(value, list):
        return [_safe_text(item) for item in value if _safe_text(item)]
    text = _safe_text(value)
    if not text:
        return []
    try:
        parsed = ast.literal_eval(text)
    except Exception:
        parsed = None
    if isinstance(parsed, (list, tuple, set)):
        return [_safe_text(item) for item in parsed if _safe_text(item)]
    return [text]


def _detect_dimensions(frame: pd.DataFrame) -> dict[str, list[str]]:
    columns = [str(column) for column in frame.columns.astype(str).tolist()]
    detected: dict[str, list[str]] = {key: [] for key in _DIMENSION_PATTERNS}
    for column in columns:
        token = _normalize_token(column)
        for scope, patterns in _DIMENSION_PATTERNS.items():
            if any(pattern in token for pattern in patterns):
                detected[scope].append(column)
    if detected["route"]:
        detected["route"] = list(dict.fromkeys(detected["route"]))
    if not detected["route"]:
        seller_state = next((item for item in detected["region"] if "seller" in _normalize_token(item) and "state" in _normalize_token(item)), "")
        customer_state = next((item for item in detected["region"] if "customer" in _normalize_token(item) and "state" in _normalize_token(item)), "")
        if seller_state and customer_state:
            detected["route"] = [seller_state, customer_state]
    for key, values in list(detected.items()):
        detected[key] = list(dict.fromkeys(values))[:12]
    return detected


def _choose_object_scope(metric_id: str, metric_name: str, source_columns: list[str], dimensions: dict[str, list[str]]) -> str:
    joined = " ".join([metric_id, metric_name, *source_columns]).lower()
    if "route" in joined and dimensions.get("route"):
        return "route"
    if any(token in joined for token in ("seller", "supplier", "vendor", "卖家", "供应商")) and (dimensions.get("seller") or dimensions.get("supplier_proxy")):
        return "supplier_proxy"
    if any(token in joined for token in ("sku", "spu", "stockcode")) and dimensions.get("sku"):
        return "sku"
    if any(token in joined for token in ("product", "item", "goods", "鍟嗗搧")) and dimensions.get("product"):
        return "product"
    if any(token in joined for token in ("category", "cate", "鍝佺被", "绫荤洰")) and dimensions.get("category"):
        return "category"
    if any(token in joined for token in ("region", "state", "city", "province", "鍖哄煙", "鍦板尯")) and dimensions.get("region"):
        return "region"
    if any(token in joined for token in ("time", "trend", "period", "date", "day", "week", "month", "pulse", "鏃ユ湡", "鏃堕棿")) and dimensions.get("time"):
        return "time"
    for scope in ("category", "product", "sku", "seller", "region", "channel", "audience"):
        if dimensions.get(scope):
            return scope
    return "overall"


def _groupable_dimensions_for_scope(scope: str, dimensions: dict[str, list[str]]) -> list[str]:
    if scope == "route":
        return list(dimensions.get("route") or [])
    if scope == "supplier_proxy":
        return [*(dimensions.get("seller") or []), *(dimensions.get("supplier_proxy") or [])][:8]
    return list(dimensions.get(scope) or [])[:8]


def _aggregation_hint(metric_id: str, metric_name: str, formula: str, source_kind: str) -> str:
    joined = " ".join([metric_id, metric_name, formula]).lower()
    if source_kind == "semantic_metric":
        return "confidence"
    if source_kind == "custom_metric":
        return "custom"
    if any(token in joined for token in ("contribution", "share", "abc")):
        return "contribution"
    if any(token in joined for token in ("trend", "change", "pulse", "time", "date", "week", "month")):
        return "trend"
    if any(token in joined for token in ("rate", "ratio", "ctr", "cvr", "cpc", "cpm", "cpa", "margin")):
        return "ratio"
    return "level"


def _preferred_chart_families(metric_id: str, metric_name: str, formula: str, source_kind: str, time_capable: bool) -> list[str]:
    joined = " ".join([metric_id, metric_name, formula]).lower()
    families: list[str] = []
    if source_kind == "semantic_metric":
        families.extend(["confidence_matrix", "direct_derived_proxy_split", "semantic_coverage_map"])
    if source_kind == "custom_metric":
        families.extend(["custom_top_bottom", "custom_trend", "custom_mix", "custom_correlation_matrix"])
    if any(token in joined for token in ("contribution", "share", "abc", "top_object", "pareto")):
        families.extend(["contribution_pareto", "top_n_bar", "abc_stacked"])
    if any(token in joined for token in ("rate", "ratio", "ctr", "cvr", "cpc", "cpm", "cpa", "margin", "inventory", "activation", "progress")):
        families.extend(["efficiency_heatmap", "grouped_bar", "cost_conversion_quadrant"])
    if source_kind == "proxy_metric" or any(token in joined for token in ("risk", "proxy", "late", "delay", "refund", "quality")):
        families.extend(["risk_bubble", "top_bottom_risk_ranking"])
    if time_capable or any(token in joined for token in ("trend", "change", "pulse", "time", "date", "week", "month")):
        families.extend(["time_trend_grid", "line_trend", "growth_slope", "pulse_chart"])
    ordered = []
    seen: set[str] = set()
    for family in families:
        if family in SUPPORTED_METRIC_CHART_FAMILIES and family not in seen:
            seen.add(family)
            ordered.append(family)
    return ordered[:8]


def _business_priority(metric_id: str, metric_name: str, business_meaning: str, source_kind: str) -> int:
    joined = " ".join([metric_id, metric_name, business_meaning]).lower()
    for token, score in _METRIC_PRIORITY_RULES:
        if token in joined:
            return score
    base = {
        "derived_metric": 70,
        "custom_metric": 74,
        "proxy_metric": 64,
        "semantic_metric": 42,
    }
    return base.get(source_kind, 50)


def _main_report_candidate(source_kind: str, evidence_level: str, confidence: str, priority: int) -> bool:
    if source_kind == "semantic_metric":
        return False
    if evidence_level.startswith("A_"):
        return True
    if confidence.lower() == "high" and priority >= 72:
        return True
    return priority >= 84


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return path


def _write_csv(path: Path, rows: list[dict[str, Any]], headers: list[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({header: row.get(header, "") for header in headers})
    return path


def _frame_column_type(frame: pd.DataFrame, column: str) -> str:
    if frame.empty or column not in frame.columns:
        token = _normalize_token(column)
        if any(marker in token for marker in ("date", "time", "timestamp", "day", "month", "week")):
            return "datetime"
        return "unknown"
    series = frame[column]
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    token = _normalize_token(column)
    if any(marker in token for marker in ("date", "time", "timestamp", "day", "month", "week")):
        return "datetime"
    sample_values = series.dropna().astype(str).head(30).tolist()
    if not any(re.search(r"\d{4}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4}", value) for value in sample_values):
        return "categorical"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        converted = pd.to_datetime(pd.Series(sample_values), errors="coerce")
    if len(converted) and converted.notna().mean() >= 0.75:
        return "datetime"
    return "categorical"


def _resolve_metric_source_columns(entry: dict[str, Any], frame: pd.DataFrame) -> list[str]:
    raw_columns = [str(item).strip() for item in list(entry.get("source_columns") or []) if str(item).strip()]
    if frame.empty:
        return raw_columns
    normalized_to_actual = {_normalize_token(column): str(column) for column in frame.columns.astype(str).tolist()}
    resolved: list[str] = []
    for column in raw_columns:
        actual = normalized_to_actual.get(_normalize_token(column), column)
        if actual and actual not in resolved:
            resolved.append(actual)
    formula_token = _normalize_token(entry.get("formula") or "")
    for column in frame.columns.astype(str).tolist():
        token = _normalize_token(column)
        if token and token in formula_token and str(column) not in resolved:
            resolved.append(str(column))
    return resolved[:12]


def _metric_joined_text(entry: dict[str, Any]) -> str:
    return " ".join(
        [
            _safe_text(entry.get("metric_id")),
            _safe_text(entry.get("metric_name")),
            _safe_text(entry.get("formula")),
            _safe_text(entry.get("business_meaning")),
        ]
    ).lower()


def _infer_time_basis(entry: dict[str, Any], frame: pd.DataFrame) -> str:
    source_columns = _resolve_metric_source_columns(entry, frame)
    time_columns = [column for column in source_columns if _frame_column_type(frame, column) == "datetime"]
    if time_columns:
        return time_columns[0]
    joined = _metric_joined_text(entry)
    for column in frame.columns.astype(str).tolist() if not frame.empty else []:
        token = _normalize_token(column)
        if token and token in _normalize_token(joined) and _frame_column_type(frame, str(column)) == "datetime":
            return str(column)
    return "none"


def _formula_divides_by_time_column(entry: dict[str, Any], frame: pd.DataFrame) -> bool:
    formula = _safe_text(entry.get("formula")).lower()
    if "/" not in formula:
        return False
    source_columns = _resolve_metric_source_columns(entry, frame)
    denominator_parts = formula.split("/")[1:]
    normalized_denominators = [_normalize_token(part[:120]) for part in denominator_parts]
    for column in source_columns:
        if _frame_column_type(frame, column) != "datetime":
            continue
        token = _normalize_token(column)
        for denominator in normalized_denominators:
            if not token or token not in denominator:
                continue
            if any(aggregator in denominator for aggregator in ("sum", "mean", "avg", "count", "first", "last", "min", "max")):
                continue
            return True
    return False


def _infer_unit_basis(entry: dict[str, Any]) -> str:
    joined = _metric_joined_text(entry)
    if any(token in joined for token in ("share", "rate", "ratio", "percent", "conversion", "ctr", "cvr", "margin")):
        return "ratio"
    if any(token in joined for token in ("revenue", "amount", "gmv", "sales", "freight", "cost", "price", "spend")):
        return "currency"
    if any(token in joined for token in ("count", "quantity", "orders", "users", "customers", "items")):
        return "count"
    if any(token in joined for token in ("score", "rating", "review", "quality")):
        return "score"
    if str(entry.get("metric_source_kind") or "") == "proxy_metric":
        return "proxy_score"
    return "unknown"


def _infer_denominator_basis(entry: dict[str, Any], frame: pd.DataFrame) -> str:
    joined = _metric_joined_text(entry)
    formula = _safe_text(entry.get("formula")).lower()
    source_columns = _resolve_metric_source_columns(entry, frame)
    if "/" not in formula and "ratio" not in joined and "share" not in joined and "rate" not in joined:
        return "none"
    if _formula_divides_by_time_column(entry, frame):
        return "timestamp_denominator_invalid"
    if any(token in joined for token in ("trend", "change", "pulse", "time", "date", "week", "month")):
        return "period_aggregated_value"
    if any(token in formula for token in ("sum(revenue)", "sum(amount)", "total_revenue", "gmv")):
        return "total_revenue"
    if any(token in joined for token in ("conversion", "ctr", "cvr")):
        return "eligible_event_count"
    if any(token in joined for token in ("order", "row")):
        return "row_or_order_count"
    if any(token in joined for token in ("score", "review", "quality")) and "/" in formula:
        return "score_denominator"
    return "ratio_denominator_unspecified"


def _normalize_time_trend_semantic_basis(item: dict[str, Any]) -> dict[str, Any]:
    metric_ids = " ".join(str(value or "") for value in list(item.get("metric_ids") or []))
    marker = " ".join(
        str(item.get(key) or "")
        for key in (
            "figure_id",
            "name",
            "relative_path",
            "title",
            "chart_family",
            "chart_type",
            "metric_id",
        )
    )
    joined = f"{metric_ids} {marker}".lower()
    if any(
        token in joined
        for token in (
            "overall_trend_change",
            "line_trend",
            "time_trend_grid",
            "growth_slope",
            "pulse_chart",
            "trend",
            "time_",
        )
    ):
        normalized = dict(item)
        normalized["denominator_basis"] = "period_aggregated_value"
        if str(normalized.get("time_basis") or "").strip().lower() in {"", "none", "unknown"}:
            normalized["time_basis"] = "period_time_field"
        return normalized
    return item


def _infer_proxy_direction(entry: dict[str, Any]) -> str:
    if str(entry.get("metric_source_kind") or "") != "proxy_metric":
        return "not_proxy"
    joined = _metric_joined_text(entry)
    if any(token in joined for token in ("quality", "review", "score", "rating")):
        return "quality_strength_proxy"
    if any(token in joined for token in ("delay", "late", "refund", "risk", "defect", "complaint")):
        return "risk_proxy"
    if any(token in joined for token in ("coverage", "confidence", "semantic")):
        return "coverage_confidence_proxy"
    return "proxy_direction_unspecified"


def _semantic_contract_entry(entry: dict[str, Any], frame: pd.DataFrame) -> dict[str, Any]:
    metric_id = _safe_text(entry.get("metric_id"))
    metric_name = _safe_text(entry.get("metric_name") or metric_id)
    source_kind = _safe_text(entry.get("metric_source_kind"))
    source_columns = _resolve_metric_source_columns(entry, frame)
    source_column_types = {column: _frame_column_type(frame, column) for column in source_columns}
    joined = _metric_joined_text(entry)
    formula = _safe_text(entry.get("formula"))
    denominator_basis = _infer_denominator_basis(entry, frame)
    unit_basis = _infer_unit_basis(entry)
    time_basis = _infer_time_basis(entry, frame)
    proxy_direction = _infer_proxy_direction(entry)
    invalid_reasons: list[str] = []
    warning_reasons: list[str] = []

    normalized_joined = _normalize_token(joined)
    if denominator_basis == "timestamp_denominator_invalid":
        invalid_reasons.append("formula_divides_by_datetime_or_timestamp")
    if "cpa" in normalized_joined or re.search(r"cost[_\s-]*per[_\s-]*acquisition|acquisition", joined):
        has_action_denominator = any(
            token in joined
            for token in ("conversion", "acquisition", "signup", "register", "lead", "newcustomer", "order_count", "orders")
        )
        if not has_action_denominator or denominator_basis == "timestamp_denominator_invalid":
            invalid_reasons.append("cpa_label_without_valid_acquisition_or_conversion_denominator")
    if "cpm" in normalized_joined or re.search(r"cost[_\s-]*per[_\s-]*mille|impression", joined):
        source_tokens = [
            _normalize_token(token)
            for token in [
                *source_columns,
                *re.split(r"[^A-Za-z0-9_\u4e00-\u9fff]+", formula),
            ]
            if _normalize_token(token)
        ]
        exact_impression_tokens = {"impression", "impressions", "exposure", "exposures", "views", "display"}
        embedded_impression_markers = ("impression", "exposure", "pageview", "adview", "viewcount", "display")
        has_impression_denominator = any(
            token in exact_impression_tokens or any(marker in token for marker in embedded_impression_markers)
            for token in source_tokens
        )
        if not has_impression_denominator:
            invalid_reasons.append("cpm_label_without_impression_or_exposure_denominator")
    if source_kind == "proxy_metric" and proxy_direction == "proxy_direction_unspecified":
        warning_reasons.append("proxy_direction_not_declared")

    if invalid_reasons:
        formula_validity = "invalid_semantics"
    elif source_kind == "proxy_metric":
        formula_validity = "proxy_only"
    elif warning_reasons:
        formula_validity = "needs_review"
    else:
        formula_validity = "valid"

    allowed_claims = [
        "Use this metric only with its declared unit, denominator, and time basis.",
        "Use visual evidence as ranking or comparison support when the chart data contains concrete values.",
    ]
    forbidden_claims = [
        "Do not infer causality from this metric alone.",
        "Do not change the denominator, unit, or time basis in reader-facing text.",
    ]
    if formula_validity == "invalid_semantics":
        allowed_claims = [
            "Use only in appendix or audit notes as an invalid / needs-rewording derived metric.",
            "If retained visually, rename it away from unsupported business acronyms and explain the corrected basis.",
        ]
        forbidden_claims.extend(
            [
                "Do not use this metric as a main-report hero figure.",
                "Do not support management recommendations with this metric until the formula is corrected.",
            ]
        )
    elif source_kind == "proxy_metric":
        allowed_claims.extend(
            [
                f"State explicitly that this is a {proxy_direction} and use it for prioritization, not direct measurement.",
            ]
        )
        forbidden_claims.extend(
            [
                "Do not call a proxy metric a direct measured KPI.",
                "Do not label high-score quality proxy charts as risk unless lower values define the risk direction.",
            ]
        )
    if time_basis and time_basis != "none":
        forbidden_claims.append(f"Do not rename `{time_basis}` trends as a different date basis such as order date or delivery date.")
    if denominator_basis:
        forbidden_claims.append(f"Do not present chart shares using a different denominator than `{denominator_basis}`.")

    return {
        "metric_source_kind": source_kind,
        "metric_id": metric_id,
        "metric_name": metric_name,
        "formula": formula,
        "formula_validity": formula_validity,
        "formula_invalid_reasons": invalid_reasons,
        "semantic_warnings": warning_reasons,
        "source_columns": source_columns,
        "source_column_types": source_column_types,
        "unit_basis": unit_basis,
        "denominator_basis": denominator_basis,
        "time_basis": time_basis,
        "allowed_claims": allowed_claims,
        "forbidden_claims": forbidden_claims,
        "proxy_direction": proxy_direction,
        "metric_semantic_status": formula_validity,
    }


def _build_metric_semantic_contract_payload(
    *,
    workspace: Path,
    registry_payload: dict[str, Any],
    frame: pd.DataFrame,
    business_profile: str = "",
) -> dict[str, Any]:
    entries = [
        _semantic_contract_entry(item, frame)
        for item in list(registry_payload.get("entries") or [])
        if isinstance(item, dict)
    ]
    invalid_count = sum(1 for item in entries if item.get("formula_validity") == "invalid_semantics")
    proxy_count = sum(1 for item in entries if item.get("formula_validity") == "proxy_only")
    return {
        "contract_version": 1,
        "business_profile": _safe_text(business_profile) or _safe_text(registry_payload.get("business_profile")) or "",
        "workspace_path": str(workspace.resolve()),
        "dataset_path": registry_payload.get("dataset_path", ""),
        "metric_count": len(entries),
        "invalid_semantics_count": invalid_count,
        "proxy_only_count": proxy_count,
        "entries": entries,
        "global_rules": {
            "denominator_basis": "Reader-facing shares/rates must name the denominator used by the figure or metric.",
            "unit_basis": "Currency, count, ratio, score, and proxy units must not be mixed in a single claim.",
            "time_basis": "A trend may only be named with the actual date column used to compute it.",
            "proxy_direction": "Proxy metrics can guide prioritization, but the direction must be named before risk or quality claims.",
        },
    }


def build_metric_semantic_contract(
    *,
    workspace_path: str | Path,
    registry_payload: dict[str, Any] | None = None,
    business_profile: str = "",
) -> dict[str, Any]:
    """Write the deterministic semantic contract that governs metric claims."""
    workspace = Path(workspace_path).expanduser().resolve()
    if registry_payload is None:
        registry_payload = _read_json_if_exists(workspace / "metric_visual_registry.json")
    dataset_path = workspace / "custom_metrics_dataset.csv"
    if not dataset_path.exists():
        dataset_path = workspace / "source_dataset.csv"
    frame = pd.read_csv(dataset_path, encoding="utf-8-sig") if dataset_path.exists() else pd.DataFrame()
    payload = _build_metric_semantic_contract_payload(
        workspace=workspace,
        registry_payload=registry_payload or {},
        frame=frame,
        business_profile=business_profile,
    )
    json_path = _write_json(workspace / "metric_semantic_contract.json", payload)
    payload["json_path"] = str(json_path.resolve())
    return payload


def _candidate_metric_roots(workspace: Path) -> list[Path]:
    roots: list[Path] = []
    seen: set[str] = set()

    def add(path: Path) -> None:
        key = str(path.resolve()).lower()
        if key in seen:
            return
        seen.add(key)
        roots.append(path)

    add(workspace)
    current = workspace
    for parent in workspace.parents:
        current = parent
        if current.name.startswith("smart-report-"):
            add(current)
            break
    return roots


def _find_existing_metric_outputs(workspace: Path) -> dict[str, Path]:
    roots = _candidate_metric_roots(workspace)

    def candidate_paths(*relative_parts: str) -> list[Path]:
        paths: list[Path] = []
        for root in roots:
            paths.append(root.joinpath(*relative_parts))
        return paths

    candidates = {
        "universal_metric_mining_result": [
            *candidate_paths("metric_mining", "universal_metric_mining_result.json"),
            *candidate_paths("outputs", "metric_mining", "universal_metric_mining_result.json"),
            *candidate_paths("universal_metric_mining_result.json"),
        ],
        "derived_metrics_table": [
            *candidate_paths("metric_mining", "derived_metrics_table.csv"),
            *candidate_paths("outputs", "metric_mining", "derived_metrics_table.csv"),
            *candidate_paths("derived_metrics_table.csv"),
            *candidate_paths("procurement_sales_derived_metrics.csv"),
        ],
        "proxy_metrics_table": [
            *candidate_paths("metric_mining", "proxy_metrics_table.csv"),
            *candidate_paths("outputs", "metric_mining", "proxy_metrics_table.csv"),
            *candidate_paths("proxy_metrics_table.csv"),
        ],
        "semantic_metric_result": [
            *candidate_paths("metric_mining", "semantic_metric_result.json"),
            *candidate_paths("outputs", "metric_mining", "semantic_metric_result.json"),
            *candidate_paths("semantic_metric_result.json"),
        ],
        "custom_metric_execution": [
            *candidate_paths("03_custom_metric_execution.json"),
        ],
        "custom_metric_values": [
            *candidate_paths("custom_metric_values.csv"),
        ],
        "custom_metrics_dataset": [
            *candidate_paths("custom_metrics_dataset.csv"),
        ],
        "generic_derived_metric_discovery": [
            *candidate_paths("generic_derived_metric_discovery.json"),
        ],
        "generic_derived_metric_values": [
            *candidate_paths("generic_derived_metric_values.csv"),
        ],
        "generic_derived_metric_diagnostics": [
            *candidate_paths("generic_derived_metric_execution_diagnostics.json"),
        ],
    }
    resolved: dict[str, Path] = {}
    for key, paths in candidates.items():
        for path in paths:
            if path.exists() and path.is_file():
                resolved[key] = path
                break
    return resolved


def build_metric_visual_registry(
    *,
    workspace_path: str | Path,
    business_profile: str = "",
) -> dict[str, Any]:
    workspace = Path(workspace_path).expanduser().resolve()
    dataset_path = workspace / "custom_metrics_dataset.csv"
    if not dataset_path.exists():
        dataset_path = workspace / "source_dataset.csv"

    frame = pd.read_csv(dataset_path, encoding="utf-8-sig") if dataset_path.exists() else pd.DataFrame()
    dimensions = _detect_dimensions(frame) if not frame.empty else {key: [] for key in _DIMENSION_PATTERNS}
    existing_outputs = _find_existing_metric_outputs(workspace)

    universal_payload = _read_json_if_exists(existing_outputs.get("universal_metric_mining_result", Path()))
    semantic_payload = _read_json_if_exists(existing_outputs.get("semantic_metric_result", Path()))
    custom_payload = _read_json_if_exists(existing_outputs.get("custom_metric_execution", Path()))
    generic_derived_rows = _read_csv_rows(existing_outputs.get("generic_derived_metric_values", Path()))
    generic_derived_diagnostics = _read_json_if_exists(existing_outputs.get("generic_derived_metric_diagnostics", Path()))
    generic_derived_diagnostics_by_id = {
        _safe_text(item.get("metric_id")): item
        for item in list(generic_derived_diagnostics.get("diagnostics") or [])
        if isinstance(item, dict) and _safe_text(item.get("metric_id"))
    }

    profile = _safe_text(business_profile) or _safe_text(universal_payload.get("business_profile")) or "generic_long_business_report"
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add_entry(payload: dict[str, Any]) -> None:
        metric_id = _safe_text(payload.get("metric_id"))
        source_kind = _safe_text(payload.get("metric_source_kind"))
        if not metric_id or not source_kind:
            return
        marker = f"{source_kind}::{metric_id}"
        if marker in seen:
            return
        seen.add(marker)
        entries.append(payload)

    for source_kind, group_name in (("derived_metric", "derived_metrics"), ("proxy_metric", "proxy_metrics")):
        for row in list(universal_payload.get(group_name) or []):
            if not isinstance(row, dict):
                continue
            metric_id = _safe_text(row.get("metric_id"))
            metric_name = _safe_text(row.get("metric_name") or metric_id)
            formula = _safe_text(row.get("formula"))
            source_columns = _parse_list_like(row.get("source_columns"))
            scope = _choose_object_scope(metric_id, metric_name, source_columns, dimensions)
            groupable = _groupable_dimensions_for_scope(scope, dimensions)
            time_capable = bool(dimensions.get("time"))
            priority = _business_priority(metric_id, metric_name, _safe_text(row.get("business_meaning")), source_kind)
            confidence = _safe_text(row.get("confidence") or "medium")
            evidence_level = _safe_text(row.get("evidence_level") or "")
            add_entry(
                {
                    "metric_source_kind": source_kind,
                    "metric_id": metric_id,
                    "metric_name": metric_name,
                    "business_profile": profile,
                    "formula": formula,
                    "evidence_level": evidence_level,
                    "confidence": confidence,
                    "business_meaning": _safe_text(row.get("business_meaning") or row.get("note") or ""),
                    "object_scope": scope,
                    "groupable_dimensions": groupable,
                    "time_capable": time_capable,
                    "chartability": True,
                    "preferred_chart_families": _preferred_chart_families(metric_id, metric_name, formula, source_kind, time_capable),
                    "default_reader_tier": "main_report" if _main_report_candidate(source_kind, evidence_level, confidence, priority) else "appendix",
                    "main_report_candidate": _main_report_candidate(source_kind, evidence_level, confidence, priority),
                    "business_priority": priority,
                    "metric_kind": _safe_text(row.get("metric_kind") or source_kind),
                    "value": row.get("value", ""),
                    "source_columns": source_columns,
                    "aggregation_hint": _aggregation_hint(metric_id, metric_name, formula, source_kind),
                }
            )

    for row in list(semantic_payload.get("results") or []):
        if not isinstance(row, dict):
            continue
        status = _safe_text(row.get("status"))
        if status not in {"calculated", "proxy_calculated"}:
            continue
        metric_id = _safe_text(row.get("metric_id") or row.get("metric_name_cn"))
        metric_name = _safe_text(row.get("metric_name_cn") or row.get("metric_name") or metric_id)
        formula = _safe_text(row.get("formula") or row.get("calculation_method"))
        source_columns = _parse_list_like(row.get("source_fields"))
        scope = _choose_object_scope(metric_id, metric_name, source_columns, dimensions)
        priority = _business_priority(metric_id, metric_name, _safe_text(row.get("caveat") or ""), "semantic_metric")
        confidence = _safe_text(row.get("confidence") or "medium")
        evidence_level = _safe_text(row.get("evidence_level") or "")
        add_entry(
            {
                "metric_source_kind": "semantic_metric",
                "metric_id": metric_id,
                "metric_name": metric_name,
                "business_profile": profile,
                "formula": formula,
                "evidence_level": evidence_level,
                "confidence": confidence,
                "business_meaning": _safe_text(row.get("caveat") or row.get("unsupported_reason") or "Semantic metric confidence signal."),
                "object_scope": scope,
                "groupable_dimensions": _groupable_dimensions_for_scope(scope, dimensions),
                "time_capable": bool(dimensions.get("time")),
                "chartability": True,
                "preferred_chart_families": _preferred_chart_families(metric_id, metric_name, formula, "semantic_metric", bool(dimensions.get("time"))),
                "default_reader_tier": "appendix",
                "main_report_candidate": False,
                "business_priority": priority,
                "metric_kind": "semantic_metric",
                "value": row.get("value", ""),
                "source_columns": source_columns,
                "aggregation_hint": "confidence",
                "status": status,
            }
        )

    for row in generic_derived_rows:
        if not isinstance(row, dict):
            continue
        status = _safe_text(row.get("status"))
        if status != "completed":
            continue
        metric_id = _safe_text(row.get("metric_id"))
        metric_name = _safe_text(row.get("metric_name") or row.get("指标中文名") or metric_id)
        diagnostic = dict(generic_derived_diagnostics_by_id.get(metric_id) or {})
        source_columns = _parse_list_like(row.get("source_fields") or row.get("source_metrics"))
        formula = _safe_text(row.get("formula"))
        scope = _choose_object_scope(metric_id, metric_name, source_columns, dimensions)
        priority = max(
            _business_priority(metric_id, metric_name, formula, "derived_metric"),
            82 if _safe_text(row.get("recommended_visual_use")) else 74,
        )
        add_entry(
            {
                "metric_source_kind": "derived_metric",
                "metric_id": metric_id,
                "metric_name": metric_name,
                "business_profile": profile,
                "formula": formula,
                "evidence_level": "A_RUNTIME_CLI_DERIVED",
                "confidence": "high",
                "business_meaning": _safe_text(row.get("business_meaning") or ""),
                "diagnostic_use": _safe_text(row.get("diagnostic_use") or diagnostic.get("diagnostic_use")),
                "object_scope": scope,
                "groupable_dimensions": _groupable_dimensions_for_scope(scope, dimensions),
                "time_capable": bool(dimensions.get("time")),
                "chartability": True,
                "preferred_chart_families": _preferred_chart_families(metric_id, metric_name, formula, "derived_metric", bool(dimensions.get("time"))),
                "default_reader_tier": "main_report" if priority >= 74 else "appendix",
                "main_report_candidate": priority >= 74,
                "business_priority": priority,
                "metric_kind": "runtime_cli_derived_metric",
                "value": row.get("mean", ""),
                "source_columns": source_columns,
                "aggregation_hint": _aggregation_hint(metric_id, metric_name, formula, "derived_metric"),
                "unit_basis": _safe_text(row.get("unit")),
                "directionality": _safe_text(row.get("directionality")),
                "recommended_visual_use": _safe_text(row.get("recommended_visual_use")),
                "execution_diagnostics": {
                    "coverage_ratio": diagnostic.get("coverage_ratio", row.get("coverage_ratio", "")),
                    "valid_n": diagnostic.get("valid_n", row.get("valid_n", "")),
                    "denominator_zero_count": diagnostic.get("denominator_zero_count", ""),
                    "denominator_nonzero_ratio": diagnostic.get("denominator_nonzero_ratio", ""),
                    "overlap_count": diagnostic.get("overlap_count", row.get("overlap_count", "")),
                    "overlap_ratio": diagnostic.get("overlap_ratio", row.get("overlap_ratio", "")),
                },
            }
        )

    for row in list(custom_payload.get("metrics") or []):
        if not isinstance(row, dict):
            continue
        status = _safe_text(row.get("status"))
        if status != "completed":
            continue
        metric_id = _safe_text(row.get("metric_id"))
        metric_name = _safe_text(row.get("metric_name") or metric_id)
        source_columns = _parse_list_like(row.get("source_columns"))
        formula = _safe_text(row.get("formula"))
        scope = _choose_object_scope(metric_id, metric_name, source_columns, dimensions)
        priority = _business_priority(metric_id, metric_name, formula, "custom_metric")
        add_entry(
            {
                "metric_source_kind": "custom_metric",
                "metric_id": metric_id,
                "metric_name": metric_name,
                "business_profile": profile,
                "formula": formula,
                "evidence_level": "A_DIRECT",
                "confidence": "high",
                "business_meaning": f"Custom metric `{metric_id}` rendered from deterministic custom metric execution.",
                "object_scope": scope,
                "groupable_dimensions": _groupable_dimensions_for_scope(scope, dimensions),
                "time_capable": bool(dimensions.get("time")),
                "chartability": True,
                "preferred_chart_families": _preferred_chart_families(metric_id, metric_name, formula, "custom_metric", bool(dimensions.get("time"))),
                "default_reader_tier": "main_report" if priority >= 74 else "appendix",
                "main_report_candidate": priority >= 74,
                "business_priority": priority,
                "metric_kind": "custom_metric",
                "value": row.get("mean", ""),
                "source_columns": source_columns,
                "aggregation_hint": "custom",
            }
        )

    registry_payload = {
        "registry_version": 1,
        "business_profile": profile,
        "dataset_path": str(dataset_path.resolve()) if dataset_path.exists() else "",
        "metric_output_paths": {key: str(path.resolve()) for key, path in existing_outputs.items()},
        "available_dimensions": dimensions,
        "supported_chart_families": sorted(SUPPORTED_METRIC_CHART_FAMILIES),
        "entry_count": len(entries),
        "entries": sorted(entries, key=lambda item: (-int(item.get("business_priority") or 0), str(item.get("metric_id") or ""))),
    }
    semantic_contract_payload = _build_metric_semantic_contract_payload(
        workspace=workspace,
        registry_payload=registry_payload,
        frame=frame,
        business_profile=profile,
    )
    semantic_index = {
        f"{item.get('metric_source_kind')}::{item.get('metric_id')}": item
        for item in list(semantic_contract_payload.get("entries") or [])
        if isinstance(item, dict)
    }
    for item in registry_payload["entries"]:
        semantic_item = semantic_index.get(f"{item.get('metric_source_kind')}::{item.get('metric_id')}") or {}
        for key in (
            "formula_validity",
            "formula_invalid_reasons",
            "semantic_warnings",
            "unit_basis",
            "denominator_basis",
            "time_basis",
            "allowed_claims",
            "forbidden_claims",
            "proxy_direction",
            "metric_semantic_status",
            "source_column_types",
        ):
            if key in semantic_item:
                item[key] = semantic_item.get(key)
        if str(item.get("formula_validity") or "") == "invalid_semantics":
            item["default_reader_tier"] = "appendix"
            item["main_report_candidate"] = False
            item["chartability"] = False
            item["preferred_chart_families"] = []
    semantic_contract_payload = _build_metric_semantic_contract_payload(
        workspace=workspace,
        registry_payload=registry_payload,
        frame=frame,
        business_profile=profile,
    )
    json_path = _write_json(workspace / "metric_visual_registry.json", registry_payload)
    contract_json_path = _write_json(workspace / "metric_semantic_contract.json", semantic_contract_payload)
    csv_rows = []
    for item in registry_payload["entries"]:
        csv_rows.append(
            {
                "metric_source_kind": item.get("metric_source_kind"),
                "metric_id": item.get("metric_id"),
                "metric_name": item.get("metric_name"),
                "business_profile": item.get("business_profile"),
                "object_scope": item.get("object_scope"),
                "groupable_dimensions": ";".join(item.get("groupable_dimensions") or []),
                "time_capable": item.get("time_capable"),
                "chartability": item.get("chartability"),
                "preferred_chart_families": ";".join(item.get("preferred_chart_families") or []),
                "default_reader_tier": item.get("default_reader_tier"),
                "main_report_candidate": item.get("main_report_candidate"),
                "business_priority": item.get("business_priority"),
                "evidence_level": item.get("evidence_level"),
                "confidence": item.get("confidence"),
                "formula": item.get("formula"),
                "formula_validity": item.get("formula_validity"),
                "unit_basis": item.get("unit_basis"),
                "denominator_basis": item.get("denominator_basis"),
                "time_basis": item.get("time_basis"),
                "proxy_direction": item.get("proxy_direction"),
            }
        )
    csv_path = _write_csv(
        workspace / "metric_visual_registry.csv",
        csv_rows,
        [
            "metric_source_kind",
            "metric_id",
            "metric_name",
            "business_profile",
            "object_scope",
            "groupable_dimensions",
            "time_capable",
            "chartability",
            "preferred_chart_families",
            "default_reader_tier",
            "main_report_candidate",
            "business_priority",
            "evidence_level",
            "confidence",
            "formula",
            "formula_validity",
            "unit_basis",
            "denominator_basis",
            "time_basis",
            "proxy_direction",
        ],
    )
    registry_payload["json_path"] = str(json_path.resolve())
    registry_payload["csv_path"] = str(csv_path.resolve())
    registry_payload["semantic_contract_path"] = str(contract_json_path.resolve())
    registry_payload["semantic_contract_summary"] = {
        "metric_count": semantic_contract_payload.get("metric_count", 0),
        "invalid_semantics_count": semantic_contract_payload.get("invalid_semantics_count", 0),
        "proxy_only_count": semantic_contract_payload.get("proxy_only_count", 0),
    }
    return registry_payload


def _choose_existing_main_candidates(image_assets: list[dict[str, Any]]) -> list[str]:
    preferred = []
    for asset in image_assets:
        figure_id = _safe_text(asset.get("figure_id") or asset.get("name") or asset.get("relative_path"))
        chart_type = _safe_text(asset.get("chart_type"))
        if "missingness" in figure_id.lower():
            continue
        if figure_id and figure_id not in preferred:
            preferred.append(figure_id)
        if len(preferred) >= 8:
            break
    return preferred


def _build_default_render_specs(registry_payload: dict[str, Any]) -> list[dict[str, Any]]:
    entries = [
        item
        for item in list(registry_payload.get("entries") or [])
        if isinstance(item, dict)
        and item.get("chartability")
        and str(item.get("formula_validity") or item.get("metric_semantic_status") or "") != "invalid_semantics"
    ]
    specs: list[dict[str, Any]] = []

    def section_anchor(entry: dict[str, Any]) -> str:
        scope = str(entry.get("object_scope") or "overall")
        metric_name = str(entry.get("metric_name") or entry.get("metric_id") or "metric")
        return f"{scope}::{metric_name}"

    def add_spec(entry: dict[str, Any], chart_family: str, reader_tier: str) -> None:
        metric_ids = [str(item).strip() for item in list(entry.get("metric_ids") or []) if str(item).strip()]
        if not metric_ids:
            metric_ids = [str(entry.get("metric_id") or "").strip()]
        metric_source_kind = str(entry.get("metric_source_kind") or "")
        metric_id = str(entry.get("metric_id") or "")
        semantic_status = str(entry.get("formula_validity") or entry.get("metric_semantic_status") or "unknown")
        if semantic_status == "invalid_semantics":
            return
        if reader_tier == "appendix":
            figure_role = "appendix"
        elif chart_family in {"contribution_pareto", "pulse_chart", "efficiency_heatmap", "risk_bubble", "custom_mix"}:
            figure_role = "hero"
        elif chart_family in {"abc_stacked", "line_trend", "grouped_bar", "top_bottom_risk_ranking", "custom_top_bottom"}:
            figure_role = "support"
        else:
            figure_role = "extension"
        specs.append(
            {
                "figure_id": f"metric_{metric_source_kind}_{chart_family}_{_slug(metric_ids[0])}.png",
                "metric_source_kind": metric_source_kind,
                "metric_ids": metric_ids,
                "chart_family": chart_family,
                "reader_tier": reader_tier,
                "figure_role": figure_role,
                "page_priority": int(entry.get("business_priority") or 0),
                "object_scope": str(entry.get("object_scope") or "overall"),
                "title": f"{entry.get('metric_name') or entry.get('metric_id')} / {chart_family}",
                "business_priority": int(entry.get("business_priority") or 0),
                "reason": f"Auto-generated from {entry.get('metric_source_kind')} `{entry.get('metric_id')}`.",
                "section_anchor": section_anchor(entry),
                "business_reason": f"Fallback chart for `{metric_id}` to keep a minimal business-facing metric evidence layer.",
                "evidence_reason": f"`{metric_id}` is available in the metric registry and matches chart family `{chart_family}`.",
                "proxy_disclaimer_required": metric_source_kind == "proxy_metric",
                "denominator_basis": entry.get("denominator_basis") or "unknown",
                "unit_basis": entry.get("unit_basis") or "unknown",
                "time_basis": entry.get("time_basis") or "none",
                "metric_semantic_status": semantic_status,
                "proxy_direction": entry.get("proxy_direction") or "not_proxy",
                "allowed_reader_claim": "; ".join(list(entry.get("allowed_claims") or [])[:2]),
                "cannot_say": list(entry.get("forbidden_claims") or [])[:4],
                "claim_strength": "blocked" if semantic_status == "invalid_semantics" else ("proxy" if metric_source_kind == "proxy_metric" else "metric_supported"),
            }
        )

    for entry in entries:
        families = list(entry.get("preferred_chart_families") or [])
        reader_tier = str(entry.get("default_reader_tier") or "appendix")
        for family in families[:2]:
            if family in {"custom_mix", "custom_correlation_matrix"} and not entry.get("groupable_dimensions"):
                continue
            add_spec(entry, family, reader_tier)

    # Add global semantic coverage charts once.
    if any(str(item.get("metric_source_kind") or "") == "semantic_metric" for item in entries):
        specs.append(
            {
                "figure_id": "metric_semantic_confidence_matrix.png",
                "metric_source_kind": "semantic_metric",
                "metric_ids": [str(item.get("metric_id") or "") for item in entries if str(item.get("metric_source_kind") or "") == "semantic_metric"][:16],
                "chart_family": "confidence_matrix",
                "reader_tier": "appendix",
                "figure_role": "appendix",
                "page_priority": 420,
                "object_scope": "overall",
                "title": "Semantic metric confidence matrix",
                "business_priority": 42,
                "reason": "Semantic metric confidence matrix.",
                "section_anchor": "appendix::semantic_metric_confidence",
                "business_reason": "Fallback appendix chart for semantic-metric confidence review.",
                "evidence_reason": "Semantic metric confidence should be visible when semantic metrics exist.",
                "proxy_disclaimer_required": False,
                "denominator_basis": "none",
                "unit_basis": "confidence_score",
                "time_basis": "none",
                "metric_semantic_status": "valid",
                "proxy_direction": "not_proxy",
                "allowed_reader_claim": "Use as semantic confidence / coverage disclosure.",
                "cannot_say": ["Do not use semantic confidence charts as direct business KPI proof."],
                "claim_strength": "semantic_context",
            }
        )
    if entries:
        specs.append(
            {
                "figure_id": "metric_direct_derived_proxy_split.png",
                "metric_source_kind": "semantic_metric",
                "metric_ids": [],
                "chart_family": "direct_derived_proxy_split",
                "reader_tier": "appendix",
                "figure_role": "appendix",
                "page_priority": 400,
                "object_scope": "overall",
                "title": "Direct / derived / proxy metric split",
                "business_priority": 40,
                "reason": "Metric source-kind coverage split.",
                "section_anchor": "appendix::metric_source_split",
                "business_reason": "Fallback appendix chart for metric-source coverage transparency.",
                "evidence_reason": "The report should still disclose the mix of direct, derived, and proxy metrics.",
                "proxy_disclaimer_required": False,
                "denominator_basis": "metric_registry_count",
                "unit_basis": "count",
                "time_basis": "none",
                "metric_semantic_status": "valid",
                "proxy_direction": "not_proxy",
                "allowed_reader_claim": "Use as metric-source mix disclosure.",
                "cannot_say": ["Do not treat source-kind split as operational performance."],
                "claim_strength": "semantic_context",
            }
        )

    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for spec in specs:
        figure_id = str(spec.get("figure_id") or "")
        if not figure_id or figure_id in seen:
            continue
        seen.add(figure_id)
        deduped.append(spec)
    return deduped[:24]


def build_metric_chart_plan_fallback(
    *,
    registry_payload: dict[str, Any],
    visual_asset_index_payload: dict[str, Any],
) -> dict[str, Any]:
    image_assets = [item for item in list(visual_asset_index_payload.get("image_assets") or []) if isinstance(item, dict)]
    existing_main = _choose_existing_main_candidates(image_assets)[:4]
    render_specs = _build_default_render_specs(registry_payload)
    main_figures = list(existing_main)
    support_figures: list[str] = []
    appendix_figures: list[str] = []
    reuse_existing_figures: list[dict[str, Any]] = []

    for figure_id in existing_main:
        reuse_existing_figures.append(
            {
                "figure_id": figure_id,
                "reader_tier": "main_report",
                "reason": "Existing deterministic visual retained for main report coverage.",
                "section_anchor": "auto::existing_main_figure",
                "figure_role": "hero" if len(reuse_existing_figures) < 2 else "support",
            }
        )
    selected_render_specs: list[dict[str, Any]] = []
    fallback_main_target = 8
    fallback_appendix_target = 8
    for spec in render_specs:
        figure_id = str(spec.get("figure_id") or "")
        if not figure_id:
            continue
        if str(spec.get("reader_tier") or "") == "main_report" and len(main_figures) < fallback_main_target:
            main_figures.append(figure_id)
            if str(spec.get("figure_role") or "") in {"support", "extension"}:
                support_figures.append(figure_id)
            selected_render_specs.append(spec)
            continue
        if len(appendix_figures) < fallback_appendix_target:
            appendix_figures.append(figure_id)
            selected_render_specs.append(spec)
    appendix_overflow: list[str] = []

    entry_index = {str(item.get("metric_id") or ""): item for item in list(registry_payload.get("entries") or []) if isinstance(item, dict)}
    rendered_metric_ids = {metric_id for spec in selected_render_specs for metric_id in list(spec.get("metric_ids") or [])}
    skipped_metrics = []
    for metric_id, item in entry_index.items():
        if metric_id in rendered_metric_ids:
            continue
        skipped_metrics.append(
            {
                "metric_id": metric_id,
                "reason": "Not selected into the first metric-chart pack after priority sorting.",
                "metric_source_kind": item.get("metric_source_kind"),
            }
        )

    return {
        "main_report_figures": main_figures[:fallback_main_target],
        "support_figures": support_figures[:fallback_main_target],
        "appendix_figures": appendix_figures,
        "render_specs": selected_render_specs,
        "reuse_existing_figures": reuse_existing_figures,
        "skipped_metrics": skipped_metrics[:40],
        "appendix_overflow_figures": appendix_overflow,
        "plan_governance": "fallback_minimum",
    }


def _ratio_series(frame: pd.DataFrame, numerator: str, denominator: str, *, multiplier: float = 1.0) -> pd.Series:
    numerator_series = pd.to_numeric(frame[numerator], errors="coerce")
    denominator_series = pd.to_numeric(frame[denominator], errors="coerce")
    valid = numerator_series.notna() & denominator_series.notna() & (denominator_series != 0)
    series = pd.Series(np.nan, index=frame.index, dtype="float64")
    series.loc[valid] = numerator_series.loc[valid] * multiplier / denominator_series.loc[valid]
    return series


def _preferred_numeric_source_column(frame: pd.DataFrame, source_columns: list[str], *, exclude: set[str] | None = None) -> str:
    exclude = exclude or set()
    ranked: list[tuple[int, int, str]] = []
    for index, column in enumerate(source_columns):
        if column not in frame.columns or column in exclude:
            continue
        numeric = pd.to_numeric(frame[column], errors="coerce")
        valid_count = int(numeric.notna().sum())
        if valid_count <= 0:
            continue
        token = _normalize_token(column)
        priority = 50
        if any(key in token for key in ("revenue", "sales", "gmv", "amount", "value", "freight", "cost", "price", "margin", "quantity", "score")):
            priority = 90
        elif any(key in token for key in ("day", "delay", "late", "rate", "ratio", "count")):
            priority = 72
        ranked.append((priority, valid_count, column))
    if not ranked:
        return ""
    ranked.sort(key=lambda item: (-item[0], -item[1], source_columns.index(item[2]) if item[2] in source_columns else 999))
    return ranked[0][2]


def _series_for_metric(frame: pd.DataFrame, entry: dict[str, Any]) -> pd.Series:
    metric_id = _safe_text(entry.get("metric_id"))
    if metric_id and metric_id in frame.columns:
        return pd.to_numeric(frame[metric_id], errors="coerce")
    source_columns = [column for column in list(entry.get("source_columns") or []) if column in frame.columns]
    formula = _safe_text(entry.get("formula"))
    aggregation_hint = _safe_text(entry.get("aggregation_hint"))
    if aggregation_hint == "ratio" and len(source_columns) >= 2:
        multiplier = 1000.0 if "1000" in formula else 1.0
        ratio_series = _ratio_series(frame, source_columns[0], source_columns[1], multiplier=multiplier)
        if int(ratio_series.notna().sum()) > 0:
            return ratio_series
    if aggregation_hint in {"contribution", "trend", "level", "ratio"} and source_columns:
        numeric_column = _preferred_numeric_source_column(frame, source_columns)
        if numeric_column:
            return pd.to_numeric(frame[numeric_column], errors="coerce")
    if source_columns:
        return pd.to_numeric(frame[source_columns[0]], errors="coerce")
    return pd.Series(np.nan, index=frame.index, dtype="float64")


def _find_group_column(frame: pd.DataFrame, scope: str, preferred_columns: list[str]) -> str:
    for column in preferred_columns:
        if column in frame.columns:
            return column
    if scope == "route":
        seller_state = next((column for column in frame.columns.astype(str) if "seller" in _normalize_token(column) and "state" in _normalize_token(column)), "")
        customer_state = next((column for column in frame.columns.astype(str) if "customer" in _normalize_token(column) and "state" in _normalize_token(column)), "")
        if seller_state and customer_state:
            return "__route__"
    return preferred_columns[0] if preferred_columns and preferred_columns[0] in frame.columns else ""


def _route_series(frame: pd.DataFrame) -> pd.Series:
    seller_state = next((column for column in frame.columns.astype(str) if "seller" in _normalize_token(column) and "state" in _normalize_token(column)), "")
    customer_state = next((column for column in frame.columns.astype(str) if "customer" in _normalize_token(column) and "state" in _normalize_token(column)), "")
    if not seller_state or not customer_state:
        return pd.Series(["overall"] * len(frame), index=frame.index)
    return frame[seller_state].astype(str) + "->" + frame[customer_state].astype(str)


def _chart_style_payload(workspace: Path) -> dict[str, Any]:
    payload = _read_json_if_exists(workspace / "source_visual_assets" / "chart_visual_style.json")
    colors = list(payload.get("palette_colors") or [])
    if not colors:
        colors = ["#163A63", "#C8A44D", "#7F93B2", "#D9C27A", "#4B5563", "#A8B5C7"]
    return {
        "background": "#FFFFFF",
        "grid": "#D6DCE5",
        "text": "#1F2937",
        "colors": colors,
    }


def _configure_plot_style(workspace: Path) -> dict[str, Any]:
    style = _chart_style_payload(workspace)
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["axes.facecolor"] = style["background"]
    plt.rcParams["figure.facecolor"] = style["background"]
    return style


def _write_render_csv(path: Path, rows: list[dict[str, Any]]) -> Path:
    headers = list(dict.fromkeys(key for row in rows for key in row.keys()))
    if not headers:
        headers = ["note"]
        rows = [{"note": "no_rows"}]
    return _write_csv(path, rows, headers)


def _render_contribution_pareto(frame: pd.DataFrame, spec: dict[str, Any], entry: dict[str, Any], output_png: Path, output_csv: Path, workspace: Path) -> dict[str, Any] | None:
    style = _configure_plot_style(workspace)
    group_col = _find_group_column(frame, str(entry.get("object_scope") or ""), list(entry.get("groupable_dimensions") or []))
    if group_col == "__route__":
        groups = _route_series(frame)
    elif group_col:
        groups = frame[group_col].astype(str)
    else:
        return None
    value_series = _series_for_metric(frame, entry)
    data = pd.DataFrame({"group": groups, "value": value_series}).dropna()
    if data.empty or float(data["value"].sum()) == 0:
        return None
    grouped = data.groupby("group", as_index=False)["value"].sum().sort_values("value", ascending=False).head(12)
    total = float(grouped["value"].sum())
    grouped["contribution_share"] = grouped["value"] / total
    grouped["cumulative_share"] = grouped["contribution_share"].cumsum()
    grouped["rank"] = range(1, len(grouped) + 1)
    _write_render_csv(output_csv, grouped.to_dict(orient="records"))

    fig, ax1 = plt.subplots(figsize=(10.6, 6.0))
    positions = np.arange(len(grouped))
    ax1.bar(positions, grouped["value"], color=style["colors"][0], alpha=0.9)
    ax1.set_ylabel("Value")
    ax1.set_xticks(positions)
    ax1.set_xticklabels([str(item) for item in grouped["group"]], rotation=35, ha="right")
    ax1.grid(axis="y", color=style["grid"], alpha=0.5)
    ax2 = ax1.twinx()
    ax2.plot(positions, grouped["cumulative_share"], color=style["colors"][1], marker="o", linewidth=2.2)
    ax2.set_ylabel("Cumulative share")
    ax2.set_ylim(0, 1.05)
    fig.suptitle(_safe_text(spec.get("title") or "Contribution Pareto"))
    fig.tight_layout()
    fig.savefig(output_png, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return {"row_count": int(len(grouped))}


def _render_top_n_bar(frame: pd.DataFrame, spec: dict[str, Any], entry: dict[str, Any], output_png: Path, output_csv: Path, workspace: Path) -> dict[str, Any] | None:
    style = _configure_plot_style(workspace)
    group_col = _find_group_column(frame, str(entry.get("object_scope") or ""), list(entry.get("groupable_dimensions") or []))
    if group_col == "__route__":
        groups = _route_series(frame)
    elif group_col:
        groups = frame[group_col].astype(str)
    else:
        return None
    value_series = _series_for_metric(frame, entry)
    data = pd.DataFrame({"group": groups, "value": value_series}).dropna()
    if data.empty:
        return None
    reducer = "sum" if _safe_text(entry.get("aggregation_hint")) == "contribution" else "mean"
    grouped = data.groupby("group", as_index=False)["value"].agg(reducer).sort_values("value", ascending=False).head(10)
    _write_render_csv(output_csv, grouped.to_dict(orient="records"))
    fig, ax = plt.subplots(figsize=(10.2, 5.8))
    ax.barh(grouped["group"], grouped["value"], color=style["colors"][0])
    ax.invert_yaxis()
    ax.grid(axis="x", color=style["grid"], alpha=0.5)
    ax.set_xlabel("Metric value")
    fig.suptitle(_safe_text(spec.get("title") or "Top-N metric comparison"))
    fig.tight_layout()
    fig.savefig(output_png, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return {"row_count": int(len(grouped))}


def _render_abc_stacked(frame: pd.DataFrame, spec: dict[str, Any], entry: dict[str, Any], output_png: Path, output_csv: Path, workspace: Path) -> dict[str, Any] | None:
    style = _configure_plot_style(workspace)
    group_col = _find_group_column(frame, str(entry.get("object_scope") or ""), list(entry.get("groupable_dimensions") or []))
    if group_col == "__route__":
        groups = _route_series(frame)
    elif group_col:
        groups = frame[group_col].astype(str)
    else:
        return None
    value_series = _series_for_metric(frame, entry)
    data = pd.DataFrame({"group": groups, "value": value_series}).dropna()
    if data.empty or float(data["value"].sum()) == 0:
        return None
    grouped = data.groupby("group", as_index=False)["value"].sum().sort_values("value", ascending=False).head(16)
    grouped["share"] = grouped["value"] / float(grouped["value"].sum())
    grouped["cum"] = grouped["share"].cumsum()
    grouped["abc_class"] = grouped["cum"].apply(lambda value: "A" if value <= 0.8 else ("B" if value <= 0.95 else "C"))
    summary = grouped.groupby("abc_class", as_index=False)["share"].sum()
    _write_render_csv(output_csv, grouped.to_dict(orient="records"))
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    ax.bar(summary["abc_class"], summary["share"], color=style["colors"][: len(summary)])
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Share")
    fig.suptitle(_safe_text(spec.get("title") or "ABC mix"))
    fig.tight_layout()
    fig.savefig(output_png, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return {"row_count": int(len(grouped))}


def _render_efficiency_heatmap(frame: pd.DataFrame, spec: dict[str, Any], entries: list[dict[str, Any]], output_png: Path, output_csv: Path, workspace: Path) -> dict[str, Any] | None:
    style = _configure_plot_style(workspace)
    dimension = ""
    for entry in entries:
        dims = list(entry.get("groupable_dimensions") or [])
        if dims:
            dimension = dims[0]
            break
    if not dimension or dimension not in frame.columns:
        return None
    dimension_values = frame[dimension].astype(str)
    size_order = dimension_values.value_counts().head(8).index.tolist()
    rows: list[dict[str, Any]] = []
    matrix: list[list[float]] = []
    labels: list[str] = []
    metric_labels: list[str] = []
    for entry in entries[:6]:
        metric_series = _series_for_metric(frame, entry)
        metric_name = _safe_text(entry.get("metric_name") or entry.get("metric_id"))
        metric_labels.append(metric_name[:28])
        metric_row: list[float] = []
        for level in size_order:
            mask = dimension_values == level
            values = metric_series.loc[mask].dropna()
            mean_value = float(values.mean()) if not values.empty else np.nan
            metric_row.append(mean_value)
            rows.append(
                {
                    "dimension": dimension,
                    "segment": level,
                    "metric_id": entry.get("metric_id"),
                    "metric_name": metric_name,
                    "mean_value": mean_value,
                }
            )
        matrix.append(metric_row)
    if not rows:
        return None
    _write_render_csv(output_csv, rows)
    labels = size_order
    arr = np.array(matrix, dtype=float)
    fig, ax = plt.subplots(figsize=(11.0, 5.8))
    im = ax.imshow(arr, aspect="auto", cmap="Blues")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=35, ha="right")
    ax.set_yticks(range(len(metric_labels)))
    ax.set_yticklabels(metric_labels)
    fig.colorbar(im, ax=ax, fraction=0.03, pad=0.03)
    fig.suptitle(_safe_text(spec.get("title") or "Metric efficiency heatmap"))
    fig.tight_layout()
    fig.savefig(output_png, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return {"row_count": int(len(rows))}


def _render_risk_bubble(frame: pd.DataFrame, spec: dict[str, Any], entries: list[dict[str, Any]], output_png: Path, output_csv: Path, workspace: Path) -> dict[str, Any] | None:
    style = _configure_plot_style(workspace)
    entry = entries[0] if entries else {}
    group_col = _find_group_column(frame, str(entry.get("object_scope") or ""), list(entry.get("groupable_dimensions") or []))
    if group_col == "__route__":
        groups = _route_series(frame)
    elif group_col:
        groups = frame[group_col].astype(str)
    else:
        return None
    size_series = pd.to_numeric(frame[next((col for col in frame.columns if _normalize_token(col) in {"revenue", "sales", "gmv", "amount"}), frame.columns[0])], errors="coerce")
    rows: list[dict[str, Any]] = []
    for entry in entries[:3]:
        series = _series_for_metric(frame, entry)
        data = pd.DataFrame({"group": groups, "value": series, "size": size_series}).dropna(subset=["value"])
        if data.empty:
            continue
        grouped = data.groupby("group", as_index=False).agg(value=("value", "mean"), size=("size", "sum")).sort_values("size", ascending=False).head(12)
        for row in grouped.to_dict(orient="records"):
            rows.append(
                {
                    "group": row["group"],
                    "metric_id": entry.get("metric_id"),
                    "value": row["value"],
                    "size": row["size"],
                }
            )
    if not rows:
        return None
    render_frame = pd.DataFrame(rows).sort_values("size", ascending=False).head(18)
    _write_render_csv(output_csv, render_frame.to_dict(orient="records"))
    fig, ax = plt.subplots(figsize=(10.6, 6.2))
    size_scale = np.clip(render_frame["size"].astype(float).to_numpy(), a_min=1.0, a_max=None)
    scatter = ax.scatter(
        range(len(render_frame)),
        render_frame["value"].astype(float).to_numpy(),
        s=np.sqrt(size_scale) * 20,
        c=np.arange(len(render_frame)),
        cmap="Blues",
        alpha=0.75,
        edgecolors=style["colors"][1],
        linewidths=0.8,
    )
    ax.set_xticks(range(len(render_frame)))
    ax.set_xticklabels(render_frame["group"], rotation=40, ha="right")
    ax.set_ylabel("Risk proxy value")
    ax.grid(axis="y", color=style["grid"], alpha=0.5)
    fig.colorbar(scatter, ax=ax, fraction=0.03, pad=0.03)
    fig.suptitle(_safe_text(spec.get("title") or "Risk proxy bubble"))
    fig.tight_layout()
    fig.savefig(output_png, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return {"row_count": int(len(render_frame))}


def _render_time_trend(frame: pd.DataFrame, spec: dict[str, Any], entries: list[dict[str, Any]], output_png: Path, output_csv: Path, workspace: Path, *, grid: bool) -> dict[str, Any] | None:
    style = _configure_plot_style(workspace)
    time_columns = _detect_dimensions(frame).get("time") or []
    time_column = time_columns[0] if time_columns else ""
    if not time_column or time_column not in frame.columns:
        return None
    parsed = pd.to_datetime(frame[time_column], errors="coerce")
    if int(parsed.notna().sum()) < 4:
        return None
    if int(parsed.notna().sum()) > 45:
        periods = parsed.dt.to_period("M").dt.to_timestamp()
    else:
        periods = parsed.dt.to_period("D").dt.to_timestamp()
    rows: list[dict[str, Any]] = []
    series_payloads: list[tuple[str, pd.DataFrame]] = []
    for entry in entries[:6]:
        series = _series_for_metric(frame, entry)
        data = pd.DataFrame({"period": periods, "value": series}).dropna()
        if len(data) < 3:
            continue
        grouped = data.groupby("period", as_index=False)["value"].mean().sort_values("period")
        label = _safe_text(entry.get("metric_name") or entry.get("metric_id"))
        for row in grouped.to_dict(orient="records"):
            rows.append({"metric_id": entry.get("metric_id"), "metric_name": label, "period": row["period"].strftime("%Y-%m-%d"), "value": row["value"]})
        series_payloads.append((label, grouped))
    if not rows:
        return None
    _write_render_csv(output_csv, rows)
    if grid:
        fig, axes = plt.subplots(len(series_payloads), 1, figsize=(10.6, max(4.8, len(series_payloads) * 2.2)), sharex=True)
        if not isinstance(axes, np.ndarray):
            axes = np.array([axes])
        for index, (label, grouped) in enumerate(series_payloads):
            ax = axes[index]
            ax.plot(grouped["period"], grouped["value"], color=style["colors"][index % len(style["colors"])], linewidth=2.2)
            ax.set_title(label, fontsize=10, loc="left")
            ax.grid(axis="y", color=style["grid"], alpha=0.5)
        fig.suptitle(_safe_text(spec.get("title") or "Metric trend grid"))
        fig.tight_layout()
    else:
        fig, ax = plt.subplots(figsize=(10.6, 5.6))
        for index, (label, grouped) in enumerate(series_payloads):
            ax.plot(grouped["period"], grouped["value"], label=label, color=style["colors"][index % len(style["colors"])], linewidth=2.0)
        ax.grid(axis="y", color=style["grid"], alpha=0.5)
        ax.legend(loc="best", fontsize=8)
        fig.suptitle(_safe_text(spec.get("title") or "Metric trend"))
        fig.tight_layout()
    fig.savefig(output_png, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return {"row_count": int(len(rows))}


def _render_confidence_matrix(registry_payload: dict[str, Any], output_png: Path, output_csv: Path, workspace: Path) -> dict[str, Any] | None:
    entries = [item for item in list(registry_payload.get("entries") or []) if isinstance(item, dict) and str(item.get("metric_source_kind") or "") == "semantic_metric"]
    if not entries:
        return None
    rows = []
    confidence_order = {"low": 1, "medium": 2, "high": 3}
    evidence_order = {"C_PROXY": 1, "B_DERIVED": 2, "A_DIRECT": 3}
    for item in entries[:20]:
        rows.append(
            {
                "metric_id": item.get("metric_id"),
                "metric_name": item.get("metric_name"),
                "confidence_score": confidence_order.get(str(item.get("confidence") or "").lower(), 0),
                "evidence_score": evidence_order.get(str(item.get("evidence_level") or ""), 0),
            }
        )
    _write_render_csv(output_csv, rows)
    style = _configure_plot_style(workspace)
    arr = np.array([[row["confidence_score"], row["evidence_score"]] for row in rows], dtype=float)
    fig, ax = plt.subplots(figsize=(6.8, max(4.0, len(rows) * 0.35)))
    im = ax.imshow(arr, aspect="auto", cmap="Blues")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["confidence", "evidence"])
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([str(row["metric_name"])[:26] for row in rows], fontsize=8)
    fig.colorbar(im, ax=ax, fraction=0.03, pad=0.03)
    fig.suptitle("Semantic confidence matrix")
    fig.tight_layout()
    fig.savefig(output_png, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return {"row_count": int(len(rows))}


def _render_source_kind_split(registry_payload: dict[str, Any], output_png: Path, output_csv: Path, workspace: Path) -> dict[str, Any] | None:
    entries = [item for item in list(registry_payload.get("entries") or []) if isinstance(item, dict)]
    if not entries:
        return None
    counts: dict[str, int] = {}
    for item in entries:
        key = str(item.get("metric_source_kind") or "unknown")
        counts[key] = counts.get(key, 0) + 1
    rows = [{"metric_source_kind": key, "count": value} for key, value in sorted(counts.items())]
    _write_render_csv(output_csv, rows)
    style = _configure_plot_style(workspace)
    fig, ax = plt.subplots(figsize=(7.0, 4.8))
    ax.bar([row["metric_source_kind"] for row in rows], [row["count"] for row in rows], color=style["colors"][: len(rows)])
    ax.grid(axis="y", color=style["grid"], alpha=0.5)
    fig.suptitle("Metric source-kind split")
    fig.tight_layout()
    fig.savefig(output_png, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return {"row_count": int(len(rows))}


def _render_custom_mix(frame: pd.DataFrame, spec: dict[str, Any], entries: list[dict[str, Any]], output_png: Path, output_csv: Path, workspace: Path) -> dict[str, Any] | None:
    if not entries:
        return None
    group_col = ""
    for entry in entries:
        dims = list(entry.get("groupable_dimensions") or [])
        if dims:
            group_col = dims[0]
            break
    if not group_col or group_col not in frame.columns:
        return None
    rows: list[dict[str, Any]] = []
    for entry in entries[:3]:
        metric_id = str(entry.get("metric_id") or "")
        if metric_id not in frame.columns:
            continue
        series = pd.to_numeric(frame[metric_id], errors="coerce")
        grouped = pd.DataFrame({"group": frame[group_col].astype(str), "value": series}).dropna()
        if grouped.empty:
            continue
        summary = grouped.groupby("group", as_index=False)["value"].mean().sort_values("value", ascending=False).head(8)
        for row in summary.to_dict(orient="records"):
            rows.append({"group": row["group"], "metric_id": metric_id, "value": row["value"]})
    if not rows:
        return None
    render_frame = pd.DataFrame(rows)
    _write_render_csv(output_csv, render_frame.to_dict(orient="records"))
    style = _configure_plot_style(workspace)
    pivot = render_frame.pivot_table(index="group", columns="metric_id", values="value", aggfunc="mean").fillna(0.0)
    pivot = pivot.head(8)
    fig, ax = plt.subplots(figsize=(10.4, 5.8))
    bottom = np.zeros(len(pivot))
    positions = np.arange(len(pivot.index))
    for index, column in enumerate(pivot.columns):
        values = pivot[column].to_numpy(dtype=float)
        ax.bar(positions, values, bottom=bottom, color=style["colors"][index % len(style["colors"])], label=str(column))
        bottom += values
    ax.legend(loc="best", fontsize=8)
    ax.set_xticks(positions)
    ax.set_xticklabels([str(item) for item in pivot.index], rotation=35, ha="right")
    fig.suptitle(_safe_text(spec.get("title") or "Custom metric mix"))
    fig.tight_layout()
    fig.savefig(output_png, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return {"row_count": int(len(render_frame))}


def _render_metric_spec(
    *,
    workspace: Path,
    frame: pd.DataFrame,
    registry_payload: dict[str, Any],
    spec: dict[str, Any],
    registry_index: dict[str, dict[str, Any]],
    output_png: Path,
    output_csv: Path,
) -> dict[str, Any] | None:
    chart_family = str(spec.get("chart_family") or "")
    metric_ids = [str(item).strip() for item in list(spec.get("metric_ids") or []) if str(item).strip()]
    entries = [registry_index[item] for item in metric_ids if item in registry_index]
    entry = entries[0] if entries else {}
    if chart_family == "contribution_pareto":
        return _render_contribution_pareto(frame, spec, entry, output_png, output_csv, workspace)
    if chart_family == "top_n_bar":
        return _render_top_n_bar(frame, spec, entry, output_png, output_csv, workspace)
    if chart_family == "grouped_bar":
        return _render_top_n_bar(frame, spec, entry, output_png, output_csv, workspace)
    if chart_family == "abc_stacked":
        return _render_abc_stacked(frame, spec, entry, output_png, output_csv, workspace)
    if chart_family == "efficiency_heatmap":
        return _render_efficiency_heatmap(frame, spec, entries or [entry], output_png, output_csv, workspace)
    if chart_family in {"risk_bubble", "top_bottom_risk_ranking"}:
        return _render_risk_bubble(frame, spec, entries or [entry], output_png, output_csv, workspace)
    if chart_family == "time_trend_grid":
        return _render_time_trend(frame, spec, entries or [entry], output_png, output_csv, workspace, grid=True)
    if chart_family in {"line_trend", "growth_slope", "pulse_chart"}:
        return _render_time_trend(frame, spec, entries or [entry], output_png, output_csv, workspace, grid=False)
    if chart_family == "confidence_matrix":
        return _render_confidence_matrix(registry_payload, output_png, output_csv, workspace)
    if chart_family in {"direct_derived_proxy_split", "semantic_coverage_map"}:
        return _render_source_kind_split(registry_payload, output_png, output_csv, workspace)
    if chart_family in {"custom_top_bottom", "custom_trend"}:
        if chart_family == "custom_top_bottom":
            return _render_top_n_bar(frame, spec, entry, output_png, output_csv, workspace)
        return _render_time_trend(frame, spec, entries or [entry], output_png, output_csv, workspace, grid=False)
    if chart_family in {"custom_mix", "custom_correlation_matrix"}:
        return _render_custom_mix(frame, spec, entries, output_png, output_csv, workspace)
    return None


def _metric_asset_entry(
    *,
    workspace: Path,
    png_path: Path,
    csv_path: Path,
    spec: dict[str, Any],
) -> dict[str, Any]:
    relative_png = png_path.relative_to(workspace).as_posix()
    relative_csv = csv_path.relative_to(workspace).as_posix()
    chart_family = str(spec.get("chart_family") or "")
    metric_ids = [str(item).strip() for item in list(spec.get("metric_ids") or []) if str(item).strip()]
    metric_source_kind = str(spec.get("metric_source_kind") or "")
    evidence_numbers: list[str] = []
    comparison_points: list[str] = []
    segment_names: list[str] = []
    try:
        csv_frame = pd.read_csv(csv_path, encoding="utf-8-sig")
    except Exception:
        csv_frame = pd.DataFrame()
    if not csv_frame.empty:
        candidate_label_columns = [col for col in csv_frame.columns if str(col) in {"group", "segment", "period", "metric_name", "metric_id", "abc_class"}]
        numeric_columns = [
            col for col in csv_frame.columns
            if pd.api.types.is_numeric_dtype(csv_frame[col]) or pd.to_numeric(csv_frame[col], errors="coerce").notna().any()
        ]
        if candidate_label_columns:
            label_col = candidate_label_columns[0]
            segment_names = [str(value) for value in csv_frame[label_col].dropna().astype(str).head(6).tolist()]
        for _, row in csv_frame.head(5).iterrows():
            label_parts = []
            for col in candidate_label_columns[:2]:
                value = str(row.get(col, "") or "").strip()
                if value:
                    label_parts.append(value)
            numeric_parts = []
            for col in numeric_columns[:3]:
                value = pd.to_numeric(pd.Series([row.get(col)]), errors="coerce").iloc[0]
                if pd.notna(value):
                    numeric_parts.append(f"{col} {float(value):.2f}" if abs(float(value)) < 1000 else f"{col} {float(value):,.2f}")
            if numeric_parts:
                line = " / ".join([*label_parts, *numeric_parts]) if label_parts else ", ".join(numeric_parts)
                evidence_numbers.append(line)
                comparison_points.append(line)
    top_signals = [
        _safe_text(spec.get("business_reason") or f"{metric_source_kind} chart planned for {chart_family}."),
        _safe_text(spec.get("evidence_reason") or ""),
    ]
    top_signals = [item for item in top_signals if item]
    insight_input = {
        "chart_subject": _safe_text(spec.get("title") or png_path.stem),
        "segment_names": segment_names,
        "metric_names": metric_ids[:6],
        "top_signals": top_signals,
        "comparison_points": comparison_points,
        "outliers_or_extremes": [],
        "evidence_numbers": evidence_numbers,
        "chart_type": chart_family,
        "section_anchor": _safe_text(spec.get("section_anchor") or ""),
        "proxy_disclaimer_required": bool(spec.get("proxy_disclaimer_required", False)),
        "denominator_basis": _safe_text(spec.get("denominator_basis") or "unknown"),
        "unit_basis": _safe_text(spec.get("unit_basis") or "unknown"),
        "time_basis": _safe_text(spec.get("time_basis") or "none"),
        "metric_semantic_status": _safe_text(spec.get("metric_semantic_status") or "unknown"),
        "claim_strength": _safe_text(spec.get("claim_strength") or ""),
        "allowed_reader_claim": _safe_text(spec.get("allowed_reader_claim") or ""),
        "cannot_say": list(spec.get("cannot_say") or []),
        "proxy_direction": _safe_text(spec.get("proxy_direction") or "not_proxy"),
    }
    return {
        "name": png_path.name,
        "relative_path": relative_png,
        "absolute_path": str(png_path.resolve()),
        "title": _safe_text(spec.get("title") or png_path.stem),
        "purpose": _safe_text(spec.get("reason") or "Metric-derived chart."),
        "type": "png",
        "bytes": int(png_path.stat().st_size),
        "figure_id": png_path.name,
        "chart_type": chart_family,
        "data_source_files": [csv_path.name],
        "metric_source_kind": metric_source_kind,
        "metric_ids": metric_ids,
        "object_scope": _safe_text(spec.get("object_scope") or "overall"),
        "business_priority": int(spec.get("business_priority") or 0),
        "reader_tier": _safe_text(spec.get("reader_tier") or "appendix"),
        "section_anchor": _safe_text(spec.get("section_anchor") or ""),
        "business_reason": _safe_text(spec.get("business_reason") or spec.get("reason") or ""),
        "evidence_reason": _safe_text(spec.get("evidence_reason") or spec.get("reason") or ""),
        "proxy_disclaimer_required": bool(spec.get("proxy_disclaimer_required", False)),
        "figure_role": _safe_text(spec.get("figure_role") or ("hero" if str(spec.get("reader_tier") or "") == "main_report" else "appendix")),
        "page_priority": int(spec.get("page_priority") or spec.get("business_priority") or 999),
        "denominator_basis": _safe_text(spec.get("denominator_basis") or "unknown"),
        "unit_basis": _safe_text(spec.get("unit_basis") or "unknown"),
        "time_basis": _safe_text(spec.get("time_basis") or "none"),
        "metric_semantic_status": _safe_text(spec.get("metric_semantic_status") or "unknown"),
        "claim_strength": _safe_text(spec.get("claim_strength") or ""),
        "allowed_reader_claim": _safe_text(spec.get("allowed_reader_claim") or ""),
        "cannot_say": list(spec.get("cannot_say") or []),
        "proxy_direction": _safe_text(spec.get("proxy_direction") or "not_proxy"),
        "render_origin": "metric_chart_render",
        "chart_family": chart_family,
        "render_metadata": {
            "name": png_path.name,
            "relative_path": relative_png,
            "title": _safe_text(spec.get("title") or png_path.stem),
            "purpose": _safe_text(spec.get("reason") or "Metric-derived chart."),
            "chart_type": chart_family,
            "data_source_files": [csv_path.name],
        },
        "insight_input": insight_input,
        "interpretation_notes": list(insight_input.get("top_signals") or []),
    }


def _resolve_chart_plan_figure_paths(plan_values: list[Any], image_by_id: dict[str, dict[str, Any]]) -> list[str]:
    resolved: list[str] = []
    seen: set[str] = set()
    for item in plan_values:
        if isinstance(item, dict):
            candidate = str(item.get("relative_path") or item.get("figure_id") or "").strip()
        else:
            candidate = str(item or "").strip()
        if not candidate:
            continue
        normalized = _safe_text(candidate)
        target = image_by_id.get(normalized)
        if not target:
            continue
        relative_path = str(target.get("relative_path") or "").strip()
        if not relative_path or relative_path in seen:
            continue
        seen.add(relative_path)
        resolved.append(relative_path)
    return resolved


def _apply_chart_plan_to_index(
    *,
    workspace: Path,
    plan_payload: dict[str, Any],
    render_entries: list[dict[str, Any]],
    invalid_metric_ids: set[str] | None = None,
) -> dict[str, Any]:
    index_path = workspace / "source_visual_assets_index.json"
    payload = _read_json_if_exists(index_path)
    invalid_metric_ids = {str(item).strip() for item in (invalid_metric_ids or set()) if str(item).strip()}

    def has_invalid_metric(value: Any) -> bool:
        if not invalid_metric_ids:
            return False
        if isinstance(value, dict):
            metric_ids = {str(item).strip() for item in list(value.get("metric_ids") or []) if str(item).strip()}
            marker = " ".join(
                str(value.get(key) or "")
                for key in ("figure_id", "name", "relative_path", "absolute_path", "purpose", "title")
            )
        else:
            metric_ids = set()
            marker = str(value or "")
        return bool(metric_ids & invalid_metric_ids) or any(metric_id in marker for metric_id in invalid_metric_ids)

    image_assets = [
        item
        for item in list(payload.get("image_assets") or [])
        if isinstance(item, dict) and not has_invalid_metric(item)
    ]
    csv_assets = [
        item
        for item in list(payload.get("csv_assets") or [])
        if isinstance(item, dict) and not has_invalid_metric(item)
    ]

    image_by_id = {
        _safe_text(item.get("figure_id") or item.get("name") or item.get("relative_path")): dict(item)
        for item in image_assets
    }

    main_set = {
        _safe_text(item if isinstance(item, str) else item.get("figure_id") or item.get("relative_path"))
        for item in list(plan_payload.get("main_report_figures") or [])
    }
    appendix_set = {
        _safe_text(item if isinstance(item, str) else item.get("figure_id") or item.get("relative_path"))
        for item in list(plan_payload.get("appendix_figures") or [])
    }
    for item in list(plan_payload.get("reuse_existing_figures") or []):
        if not isinstance(item, dict):
            continue
        figure_id = _safe_text(item.get("figure_id"))
        target = image_by_id.get(figure_id)
        if not target:
            continue
        target["reader_tier"] = _safe_text(item.get("reader_tier") or target.get("reader_tier") or "appendix")
        target["render_origin"] = target.get("render_origin") or "generic_visual"
        target["metric_source_kind"] = target.get("metric_source_kind") or "generic_visual"
        target["metric_ids"] = list(target.get("metric_ids") or [])
        target["object_scope"] = target.get("object_scope") or "overall"
        target["business_priority"] = int(target.get("business_priority") or 0)
        target["chart_family"] = target.get("chart_family") or _safe_text(target.get("chart_type") or "")
        target["denominator_basis"] = target.get("denominator_basis") or "unknown"
        target["unit_basis"] = target.get("unit_basis") or "unknown"
        target["time_basis"] = target.get("time_basis") or "none"
        target["metric_semantic_status"] = target.get("metric_semantic_status") or "unknown"
        target["claim_strength"] = target.get("claim_strength") or ""
        target["allowed_reader_claim"] = target.get("allowed_reader_claim") or ""
        target["cannot_say"] = list(target.get("cannot_say") or [])
        target["proxy_direction"] = target.get("proxy_direction") or "not_proxy"
        target = _normalize_time_trend_semantic_basis(target)
        image_by_id[figure_id] = target

    for entry in render_entries:
        if has_invalid_metric(entry):
            continue
        figure_id = _safe_text(entry.get("figure_id") or entry.get("name") or entry.get("relative_path"))
        if figure_id:
            image_by_id[figure_id] = _normalize_time_trend_semantic_basis(dict(entry))
        csv_name = _visual_csv_asset_from_image(entry)
        if csv_name:
            csv_assets.append(csv_name)

    updated_images = []
    for figure_id, item in image_by_id.items():
        if has_invalid_metric(item) or has_invalid_metric(figure_id):
            continue
        if figure_id in main_set:
            item["reader_tier"] = "main_report"
        elif figure_id in appendix_set:
            item["reader_tier"] = "appendix"
        else:
            item["reader_tier"] = _safe_text(item.get("reader_tier") or "appendix")
        item["metric_source_kind"] = item.get("metric_source_kind") or "generic_visual"
        item["metric_ids"] = list(item.get("metric_ids") or [])
        item["object_scope"] = item.get("object_scope") or "overall"
        item["render_origin"] = item.get("render_origin") or "generic_visual"
        item["chart_family"] = item.get("chart_family") or _safe_text(item.get("chart_type") or "")
        item["business_priority"] = int(item.get("business_priority") or 0)
        item["denominator_basis"] = item.get("denominator_basis") or "unknown"
        item["unit_basis"] = item.get("unit_basis") or "unknown"
        item["time_basis"] = item.get("time_basis") or "none"
        item["metric_semantic_status"] = item.get("metric_semantic_status") or "unknown"
        item["claim_strength"] = item.get("claim_strength") or ""
        item["allowed_reader_claim"] = item.get("allowed_reader_claim") or ""
        item["cannot_say"] = list(item.get("cannot_say") or [])
        item["proxy_direction"] = item.get("proxy_direction") or "not_proxy"
        item = _normalize_time_trend_semantic_basis(item)
        updated_images.append(item)

    updated_images.sort(
        key=lambda item: (
            0 if str(item.get("reader_tier") or "") == "main_report" else 1,
            -int(item.get("business_priority") or 0),
            str(item.get("name") or ""),
        )
    )

    deduped_csv: list[dict[str, Any]] = []
    seen_csv: set[str] = set()
    for item in csv_assets:
        if not isinstance(item, dict):
            continue
        marker = _safe_text(item.get("name") or item.get("relative_path"))
        if not marker or marker in seen_csv:
            continue
        seen_csv.add(marker)
        deduped_csv.append(item)

    payload["image_assets"] = updated_images
    payload["csv_assets"] = deduped_csv[:160]
    payload["image_count"] = len(updated_images)
    payload["csv_count"] = len(deduped_csv)
    payload["recommended_main_report_figures"] = _resolve_chart_plan_figure_paths(
        list(plan_payload.get("main_report_figures") or []),
        image_by_id,
    )[:_DEFAULT_MAIN_REPORT_TARGET_MAX]
    payload["recommended_support_figures"] = _resolve_chart_plan_figure_paths(
        list(plan_payload.get("support_figures") or []),
        image_by_id,
    )[:_DEFAULT_MAIN_REPORT_TARGET_MAX]
    payload["recommended_appendix_figures"] = _resolve_chart_plan_figure_paths(
        list(plan_payload.get("appendix_figures") or []),
        image_by_id,
    )[:_DEFAULT_APPENDIX_LIMIT]
    payload["recommended_figure_slots"] = payload["recommended_main_report_figures"][:8]
    _write_json(index_path, payload)
    return payload


def _visual_csv_asset_from_image(image_entry: dict[str, Any]) -> dict[str, Any] | None:
    render_metadata = dict(image_entry.get("render_metadata") or {})
    files = list(render_metadata.get("data_source_files") or [])
    if not files:
        return None
    relative_dir = str(Path(str(image_entry.get("relative_path") or "")).parent).replace("\\", "/")
    file_name = str(files[0] or "").strip()
    if not file_name:
        return None
    absolute_path = Path(str(image_entry.get("absolute_path") or "")).parent / file_name
    if not absolute_path.exists():
        return None
    return {
        "name": file_name,
        "relative_path": f"{relative_dir}/{file_name}" if relative_dir and relative_dir != "." else file_name,
        "absolute_path": str(absolute_path.resolve()),
        "title": f"{image_entry.get('title') or absolute_path.stem} data",
        "purpose": f"Deterministic data source for {image_entry.get('name') or file_name}.",
        "type": absolute_path.suffix.lstrip(".").lower(),
        "bytes": int(absolute_path.stat().st_size),
    }


def _metric_render_skip_reason(
    *,
    frame: pd.DataFrame,
    spec: dict[str, Any],
    entries: list[dict[str, Any]],
) -> str:
    chart_family = str(spec.get("chart_family") or "").strip()
    supported = SUPPORTED_METRIC_CHART_FAMILIES | {"grouped_bar"}
    if chart_family not in supported:
        return "unsupported_chart_family"
    if chart_family in {"confidence_matrix", "semantic_coverage_map", "direct_derived_proxy_split"}:
        if not entries and chart_family != "direct_derived_proxy_split":
            return "unsupported_chart_family"
        return "missing_numeric_source"
    entry = entries[0] if entries else {}
    scope = str(spec.get("object_scope") or entry.get("object_scope") or "overall")
    preferred_columns = list(entry.get("groupable_dimensions") or [])
    if chart_family in {
        "contribution_pareto",
        "top_n_bar",
        "abc_stacked",
        "grouped_bar",
        "risk_bubble",
        "top_bottom_risk_ranking",
        "custom_mix",
        "custom_correlation_matrix",
        "custom_top_bottom",
    }:
        group_col = _find_group_column(frame, scope, preferred_columns)
        if not group_col and scope != "overall":
            return "missing_group_dimension"
        groups = _route_series(frame) if group_col == "__route__" else (frame[group_col].astype(str) if group_col else pd.Series(["overall"] * len(frame), index=frame.index))
        if int(groups.dropna().nunique()) < 2 and chart_family in {"contribution_pareto", "top_n_bar", "abc_stacked", "grouped_bar"}:
            return "insufficient_category_count"
    if chart_family in {"time_trend_grid", "line_trend", "growth_slope", "pulse_chart", "custom_trend"}:
        time_columns = _detect_dimensions(frame).get("time") or []
        time_column = time_columns[0] if time_columns else ""
        if not time_column or time_column not in frame.columns:
            return "insufficient_time_points"
        parsed = pd.to_datetime(frame[time_column], errors="coerce")
        if int(parsed.notna().sum()) < 4:
            return "insufficient_time_points"
    if entries:
        non_empty = False
        for item in entries:
            series = _series_for_metric(frame, item)
            if int(series.notna().sum()) > 0:
                non_empty = True
                break
        if not non_empty:
            return "proxy_not_stable_enough" if any(str(item.get("metric_source_kind") or "") == "proxy_metric" for item in entries) else "missing_numeric_source"
    return "missing_numeric_source"


def render_metric_visual_assets(
    *,
    workspace_path: str | Path,
    plan_payload: dict[str, Any],
) -> dict[str, Any]:
    workspace = Path(workspace_path).expanduser().resolve()
    registry_payload = build_metric_visual_registry(workspace_path=workspace)
    registry_index = {
        str(item.get("metric_id") or ""): item
        for item in list(registry_payload.get("entries") or [])
        if isinstance(item, dict)
    }
    invalid_metric_ids = {
        str(item.get("metric_id") or "").strip()
        for item in list(registry_payload.get("entries") or [])
        if isinstance(item, dict)
        and str(item.get("formula_validity") or item.get("metric_semantic_status") or "") == "invalid_semantics"
        and str(item.get("metric_id") or "").strip()
    }
    visual_dir = workspace / "source_visual_assets"
    visual_dir.mkdir(parents=True, exist_ok=True)
    dataset_path = workspace / "custom_metrics_dataset.csv"
    if not dataset_path.exists():
        dataset_path = workspace / "source_dataset.csv"
    frame = pd.read_csv(dataset_path, encoding="utf-8-sig") if dataset_path.exists() else pd.DataFrame()

    render_specs = [spec for spec in list(plan_payload.get("render_specs") or []) if isinstance(spec, dict)]

    rendered_figures: list[dict[str, Any]] = []
    render_rows: list[dict[str, Any]] = []
    for spec in render_specs:
        spec = _normalize_time_trend_semantic_basis(dict(spec))
        figure_id = _safe_text(spec.get("figure_id"))
        if not figure_id:
            continue
        png_path = visual_dir / figure_id
        csv_name = figure_id.replace(".png", ".csv")
        csv_path = visual_dir / csv_name
        metric_ids = [str(item).strip() for item in list(spec.get("metric_ids") or []) if str(item).strip()]
        entries = [registry_index[item] for item in metric_ids if item in registry_index]
        if invalid_metric_ids & set(metric_ids) or str(spec.get("metric_semantic_status") or "") == "invalid_semantics":
            render_rows.append(
                {
                    "figure_id": figure_id,
                    "chart_family": spec.get("chart_family"),
                    "status": "skipped",
                    "reason": "invalid_semantics_blocked_by_metric_semantic_contract",
                    "reader_tier": spec.get("reader_tier"),
                    "metric_ids": ";".join(metric_ids),
                    "metric_semantic_status": "invalid_semantics",
                    "denominator_basis": spec.get("denominator_basis"),
                    "unit_basis": spec.get("unit_basis"),
                    "time_basis": spec.get("time_basis"),
                }
            )
            continue
        result = _render_metric_spec(
            workspace=workspace,
            frame=frame,
            registry_payload=registry_payload,
            spec=spec,
            registry_index=registry_index,
            output_png=png_path,
            output_csv=csv_path,
        )
        if result is None or not png_path.exists():
            render_rows.append(
                {
                    "figure_id": figure_id,
                    "chart_family": spec.get("chart_family"),
                    "status": "skipped",
                "reason": _metric_render_skip_reason(frame=frame, spec=spec, entries=entries),
                "reader_tier": spec.get("reader_tier"),
                "metric_ids": ";".join(metric_ids),
                "metric_semantic_status": spec.get("metric_semantic_status"),
                "denominator_basis": spec.get("denominator_basis"),
                "unit_basis": spec.get("unit_basis"),
                "time_basis": spec.get("time_basis"),
            }
        )
            continue
        rendered_entry = _metric_asset_entry(workspace=workspace, png_path=png_path, csv_path=csv_path, spec=spec)
        rendered_figures.append(rendered_entry)
        render_rows.append(
            {
                "figure_id": figure_id,
                "chart_family": spec.get("chart_family"),
                "status": "completed",
                "row_count": result.get("row_count", 0),
                "reader_tier": spec.get("reader_tier"),
                "metric_ids": ";".join(spec.get("metric_ids") or []),
                "section_anchor": spec.get("section_anchor"),
                "proxy_disclaimer_required": bool(spec.get("proxy_disclaimer_required", False)),
                "figure_role": spec.get("figure_role"),
                "page_priority": spec.get("page_priority"),
                "metric_semantic_status": spec.get("metric_semantic_status"),
                "denominator_basis": spec.get("denominator_basis"),
                "unit_basis": spec.get("unit_basis"),
                "time_basis": spec.get("time_basis"),
                "proxy_direction": spec.get("proxy_direction"),
            }
        )

    visual_index_payload = _apply_chart_plan_to_index(
        workspace=workspace,
        plan_payload=plan_payload,
        render_entries=rendered_figures,
        invalid_metric_ids=invalid_metric_ids,
    )

    render_log = {
        "registry_entry_count": int(registry_payload.get("entry_count") or 0),
        "semantic_contract_path": str((workspace / "metric_semantic_contract.json").resolve()) if (workspace / "metric_semantic_contract.json").exists() else "",
        "requested_render_spec_count": len(render_specs),
        "rendered_figure_count": len(rendered_figures),
        "render_rows": render_rows,
        "plan_governance": str(plan_payload.get("plan_governance") or ""),
        "recommended_main_report_figures": visual_index_payload.get("recommended_main_report_figures") or [],
        "recommended_support_figures": visual_index_payload.get("recommended_support_figures") or [],
        "recommended_appendix_figures": visual_index_payload.get("recommended_appendix_figures") or [],
    }
    _write_json(workspace / "05b_metric_chart_render_log.json", render_log)
    return render_log


def _read_csv_frame(path: Path) -> pd.DataFrame:
    if not path.exists() or not path.is_file():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except Exception:
        try:
            return pd.read_csv(path, encoding="utf-8")
        except Exception:
            return pd.DataFrame()


def _safe_json_list(text: Any) -> list[dict[str, Any]]:
    raw = _safe_text(text)
    if not raw:
        return []
    try:
        payload = json.loads(raw)
    except Exception:
        try:
            payload = ast.literal_eval(raw)
        except Exception:
            return []
    if not isinstance(payload, list):
        return []
    return [item for item in payload if isinstance(item, dict)]


def _coerce_float_series(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(dtype="float64")
    return pd.to_numeric(frame[column], errors="coerce")


def _metric_range_text(frame: pd.DataFrame, columns: list[str]) -> str:
    parts: list[str] = []
    for column in columns:
        if column not in frame.columns:
            continue
        series = _coerce_float_series(frame, column).dropna()
        if series.empty:
            continue
        minimum = float(series.min())
        maximum = float(series.max())
        if 0 <= minimum <= 1 and 0 <= maximum <= 1 and (
            "rate" in _normalize_token(column)
            or "share" in _normalize_token(column)
            or "delta" in _normalize_token(column)
        ):
            parts.append(f"{column} {minimum:.1%}-{maximum:.1%}")
        else:
            parts.append(f"{column} {minimum:.2f}-{maximum:.2f}")
    return "；".join(parts)


def _object_list_text(values: list[str]) -> str:
    cleaned = [item for item in [_safe_text(value) for value in values] if item]
    return "；".join(cleaned)


def _candidate_object_column(frame: pd.DataFrame) -> str:
    ordered = [
        "瀵硅薄",
        "object_label",
        "object_name",
        "group",
        "segment",
        "segment_level",
        "option",
        "option_short",
        "likert_item",
        "likert_short",
    ]
    for column in ordered:
        if column in frame.columns:
            return column
    for column in frame.columns.astype(str).tolist():
        token = _normalize_token(column)
        if any(marker in token for marker in ("group", "segment", "option", "likert", "audience", "channel", "category", "band")):
            return column
    return str(frame.columns[0]) if len(frame.columns) else ""


def _generic_chart_key(asset: dict[str, Any], frame: pd.DataFrame) -> str:
    name = _safe_text(asset.get("name") or asset.get("figure_id") or "").lower()
    chart_type = _safe_text(asset.get("chart_type") or asset.get("chart_family") or "").lower()
    columns = {str(column) for column in frame.columns.astype(str).tolist()}
    if "heatmap" in chart_type or "heatmap" in name:
        return ""
    if "segment_likert_bubble" in name or {"segment_level", "likert_short", "mean", "delta_vs_overall"}.issubset(columns):
        return "segment_likert_bubble"
    if "segment_multi_select_bubble" in name or {"segment_level", "option_short", "selected_rate"}.issubset(columns):
        return "segment_multi_select_bubble"
    if "portfolio" in name or ("scatter" in chart_type and {"selected_rate", "mean_lift_vs_independent"}.issubset(columns)):
        return "portfolio_scatter"
    if "risk_bubble" in chart_type or "outlier" in name or {"group", "value", "size"}.issubset(columns):
        return "risk_bubble"
    if "quadrant" in chart_type or "quadrant" in name or {"x_value", "y_value"}.issubset(columns):
        return "quadrant"
    if "custom_top_bottom" in chart_type or "custom_top_bottom" in name:
        return "custom_top_bottom"
    if "bubble" in chart_type or "bubble" in name:
        return "generic_bubble"
    if "scatter" in chart_type or "scatter" in name:
        return "generic_scatter"
    return ""


def _generic_chart_business_question(chart_key: str, title: str) -> str:
    mapping = {
        "segment_likert_bubble": "哪些分群在关键态度项上形成稳定差异，哪些分群需要优先解释或修复？",
        "segment_multi_select_bubble": "哪些分群对选项或动作的偏好更强，适合作为优先对象？",
        "portfolio_scatter": "哪些对象同时具备较高偏好和较强组合增益，哪些对象只适合观察？",
        "risk_bubble": "哪些对象影响大且风险高，需要优先复核或收缩？",
        "quadrant": "这张象限气泡图如何把对象分成不同解释含义的分区？",
        "custom_top_bottom": "哪些对象应优先放大，哪些对象应进入修复或观察序列？",
        "generic_bubble": "这张气泡图里哪些对象最值得优先解释，哪些对象只适合观察？",
        "generic_scatter": "这张散点图里哪些对象具备优先级，哪些对象需要谨慎处理？",
    }
    return mapping.get(chart_key, f"{title} 回答哪些对象值得优先解释、修复或观察？")


def _generic_band_policy(chart_key: str) -> tuple[dict[str, str], str, str]:
    if chart_key == "segment_likert_bubble":
        return (
            {
                "high_positive": "高认同经营池",
                "high_interest": "高兴趣待解释池",
                "negative": "低认同修复池",
                "neutral": "低影响观察池",
            },
            "内容负责人",
            "本周内容例会",
        )
    if chart_key in {"segment_multi_select_bubble", "portfolio_scatter"}:
        return (
            {
                "high_positive": "高偏好优先动作池",
                "high_interest": "高偏好待匹配池",
                "negative": "低偏好谨慎池",
                "neutral": "低影响观察池",
            },
            "增长运营负责人",
            "本周增长复盘",
        )
    if chart_key == "risk_bubble":
        return (
            {
                "critical": "高影响异常池",
                "review": "高波动复核池",
                "negative": "一般异常池",
                "neutral": "低影响观察池",
            },
            "运营负责人",
            "T+3 复核",
        )
    if chart_key == "quadrant":
        return (
            {
                "expand": "强信号承接池",
                "optimize": "高潜力提效池",
                "validate": "低风险验证池",
                "shrink": "压力收缩复核池",
            },
            "经营负责人",
            "本周经营例会",
        )
    if chart_key == "custom_top_bottom":
        return (
            {
                "high_positive": "优先放大对象",
                "negative": "关键修复对象",
                "neutral": "中性观察对象",
            },
            "业务负责人",
            "T+7 复盘",
        )
    return (
        {
            "high_positive": "优先解释对象",
            "negative": "谨慎处理对象",
            "neutral": "观察对象",
        },
        "分析负责人",
        "T+7 复盘",
    )


def _generic_band_action(chart_key: str, band_name: str) -> str:
    action_map = {
        "高认同经营池": "保留当前节奏，并继续复核承接内容。",
        "高兴趣待解释池": "保留兴趣入口，补充解释层和配套内容。",
        "低认同修复池": "优先修复表达、承接或定位问题，暂缓放量。",
        "低影响观察池": "保留观察，不占用主资源。",
        "高偏好优先动作池": "进入优先动作包，优先配置资源。",
        "高偏好待匹配池": "偏好高但承接未闭环，先补匹配方案。",
        "低偏好谨慎池": "保持低优先级，小规模验证即可。",
        "高影响异常池": "先做止损或复核，不继续放大。",
        "高波动复核池": "复核原因后再决定放大或收缩。",
        "一般异常池": "纳入问题池，按影响排序处理。",
        "优先放大对象": "作为优先解释对象，保留主资源位。",
        "关键修复对象": "先修复短板，再决定是否继续投入。",
        "中性观察对象": "暂不加码，保留低成本观察。",
        "优先解释对象": "保留优先解释资格，并持续复核表现。",
        "谨慎处理对象": "先控制投入，再判断是否退出。",
        "观察对象": "暂不升级动作，进入观察序列。",
    }
    return action_map.get(band_name, f"围绕“{band_name}”执行对应解释或处理动作。")


def _quadrant_labels_from_source(
    *,
    route_candidate: dict[str, Any] | None = None,
    asset: dict[str, Any] | None = None,
    x_metric_name: str = "",
    y_metric_name: str = "",
) -> dict[str, str]:
    for source in [
        route_candidate.get("quadrant_labels") if isinstance(route_candidate, dict) else None,
        asset.get("quadrant_labels") if isinstance(asset, dict) else None,
        (asset.get("render_metadata") or {}).get("quadrant_labels") if isinstance((asset or {}).get("render_metadata"), dict) else None,
    ]:
        if isinstance(source, dict):
            labels = {key: _safe_text(source.get(key)) for key in ["top_right", "top_left", "bottom_left", "bottom_right"]}
            if all(labels.values()) and len(set(labels.values())) == 4:
                return labels
    raise ValueError("generic quadrant labels must come from CLI route contract or asset metadata; backend high/low label synthesis is forbidden.")


def _normalize_generic_point_csv(
    *,
    csv_path: Path,
    asset: dict[str, Any],
    route_candidate: dict[str, Any] | None = None,
) -> pd.DataFrame:
    frame = _read_csv_frame(csv_path)
    if frame.empty:
        return frame
    columns = {str(column) for column in frame.columns.astype(str).tolist()}
    chart_token = f"{asset.get('chart_type', '')} {asset.get('chart_family', '')} {asset.get('name', '')}".lower()
    is_object_chart = (
        {"x_value", "y_value"}.issubset(columns)
        or any(token in chart_token for token in ("quadrant_bubble", "bubble", "scatter", "portfolio", "risk"))
    )
    if not is_object_chart:
        return frame
    normalized = frame.copy()
    if "图中序号" not in normalized.columns:
        normalized.insert(0, "图中序号", [f"B{index + 1:02d}" for index in range(len(normalized))])
    else:
        normalized["图中序号"] = [value if re.fullmatch(r"B\d{2,}", _safe_text(value)) else f"B{index + 1:02d}" for index, value in enumerate(normalized["图中序号"].tolist())]
    if "对象" not in normalized.columns:
        object_column = _candidate_object_column(normalized)
        if object_column == "图中序号":
            object_column = ""
        normalized.insert(1, "对象", normalized[object_column].astype(str) if object_column and object_column in normalized.columns else normalized["图中序号"].astype(str))
    if "对象维度" not in normalized.columns:
        object_dimension = _safe_text((route_candidate or {}).get("object_dimension") or asset.get("object_scope") or asset.get("title") or "对象")
        normalized.insert(2, "对象维度", object_dimension)
    if {"x_value", "y_value"}.issubset(set(normalized.columns.astype(str).tolist())) and "象限" not in normalized.columns:
        x_series = pd.to_numeric(normalized["x_value"], errors="coerce")
        y_series = pd.to_numeric(normalized["y_value"], errors="coerce")
        x_mid = float(np.nanmedian(x_series.to_numpy(dtype=float)))
        y_mid = float(np.nanmedian(y_series.to_numpy(dtype=float)))
        x_name = _safe_text(normalized["x_metric_name"].dropna().iloc[0]) if "x_metric_name" in normalized.columns and not normalized["x_metric_name"].dropna().empty else _safe_text((route_candidate or {}).get("x_metric_name"))
        y_name = _safe_text(normalized["y_metric_name"].dropna().iloc[0]) if "y_metric_name" in normalized.columns and not normalized["y_metric_name"].dropna().empty else _safe_text((route_candidate or {}).get("y_metric_name"))
        labels = _quadrant_labels_from_source(route_candidate=route_candidate, asset=asset, x_metric_name=x_name, y_metric_name=y_name)

        def row_label(row: pd.Series) -> str:
            x_value = float(pd.to_numeric(pd.Series([row.get("x_value")]), errors="coerce").fillna(0.0).iloc[0])
            y_value = float(pd.to_numeric(pd.Series([row.get("y_value")]), errors="coerce").fillna(0.0).iloc[0])
            if y_value >= y_mid and x_value >= x_mid:
                return labels["top_right"]
            if y_value >= y_mid and x_value < x_mid:
                return labels["top_left"]
            if y_value < y_mid and x_value < x_mid:
                return labels["bottom_left"]
            return labels["bottom_right"]

        normalized["象限"] = normalized.apply(row_label, axis=1)
    if "边界标签" not in normalized.columns:
        normalized["边界标签"] = ""
    first_columns = ["图中序号", "对象", "对象维度"]
    ordered_columns = first_columns + [column for column in normalized.columns.astype(str).tolist() if column not in first_columns]
    normalized = normalized.loc[:, ordered_columns]
    _write_csv(csv_path, normalized.to_dict(orient="records"), ordered_columns)
    return normalized


def _generic_object_label(row: pd.Series, chart_key: str) -> str:
    if chart_key == "segment_likert_bubble":
        return " 脳 ".join(
            [
                _safe_text(row.get("segment_level") or row.get("segment_short")),
                _safe_text(row.get("likert_short") or row.get("likert_item")),
            ]
        ).strip(" 脳")
    if chart_key == "segment_multi_select_bubble":
        return " 脳 ".join(
            [
                _safe_text(row.get("segment_level") or row.get("segment_short")),
                _safe_text(row.get("option_short") or row.get("option")),
            ]
        ).strip(" 脳")
    if chart_key == "portfolio_scatter":
        return _safe_text(row.get("option_short") or row.get("option") or row.get("group"))
    return _safe_text(row.get("瀵硅薄") or row.get(_candidate_object_column(pd.DataFrame([row]))) or row.get("group") or row.get("object_name"))


def _generic_band_frame(frame: pd.DataFrame, chart_key: str) -> tuple[pd.DataFrame, str]:
    band_frame = frame.copy()
    label_column = "__object_label__"
    band_frame[label_column] = band_frame.apply(lambda row: _generic_object_label(row, chart_key), axis=1)
    if "象限" in band_frame.columns:
        band_frame["band_name"] = band_frame["象限"].astype(str).replace({"": "未分配象限"})
        band_frame["owner"] = "经营负责人"
        band_frame["checkpoint"] = "下一次经营复盘"
        return band_frame, label_column
    labels, default_owner, default_checkpoint = _generic_band_policy(chart_key)
    if chart_key == "segment_likert_bubble":
        delta = _coerce_float_series(band_frame, "delta_vs_overall")
        mean_series = _coerce_float_series(band_frame, "mean")
        overall = _coerce_float_series(band_frame, "overall_mean")
        positive_threshold = max(float(delta.quantile(0.75)) if delta.notna().any() else 0.0, 0.05)
        negative_threshold = min(float(delta.quantile(0.25)) if delta.notna().any() else 0.0, -0.05)
        conditions = [
            delta >= positive_threshold,
            (delta >= 0) & (mean_series < overall),
            delta <= negative_threshold,
        ]
        band_values = [
            labels["high_positive"],
            labels["high_interest"],
            labels["negative"],
        ]
        band_frame["band_name"] = np.select(conditions, band_values, default=labels["neutral"])
    elif chart_key in {"segment_multi_select_bubble", "portfolio_scatter"}:
        rate_column = "selected_rate" if "selected_rate" in band_frame.columns else "mean_co_selected_rate"
        lift_column = "mean_lift_vs_independent" if "mean_lift_vs_independent" in band_frame.columns else "delta_vs_overall"
        rates = _coerce_float_series(band_frame, rate_column)
        lifts = _coerce_float_series(band_frame, lift_column)
        rate_threshold = float(rates.median()) if rates.notna().any() else 0.0
        lift_threshold = float(lifts.median()) if lifts.notna().any() else 0.0
        conditions = [
            (rates >= rate_threshold) & (lifts >= lift_threshold),
            (rates >= rate_threshold) & (lifts < lift_threshold),
            (rates < rate_threshold) & (lifts >= lift_threshold),
        ]
        band_values = [
            labels["high_positive"],
            labels["high_interest"],
            labels["negative"],
        ]
        band_frame["band_name"] = np.select(conditions, band_values, default=labels["neutral"])
    elif chart_key == "risk_bubble":
        value_series = _coerce_float_series(band_frame, "value")
        size_series = _coerce_float_series(band_frame, "size")
        value_threshold = float(value_series.quantile(0.75)) if value_series.notna().any() else 0.0
        size_threshold = float(size_series.quantile(0.75)) if size_series.notna().any() else 0.0
        conditions = [
            (value_series >= value_threshold) & (size_series >= size_threshold),
            (value_series >= value_threshold) | (size_series >= size_threshold),
            value_series > float(value_series.median()) if value_series.notna().any() else False,
        ]
        band_values = [
            labels["critical"],
            labels["review"],
            labels["negative"],
        ]
        band_frame["band_name"] = np.select(conditions, band_values, default=labels["neutral"])
    elif chart_key == "quadrant":
        x_series = _coerce_float_series(band_frame, "x_value")
        y_series = _coerce_float_series(band_frame, "y_value")
        x_threshold = float(x_series.median()) if x_series.notna().any() else 0.0
        y_threshold = float(y_series.median()) if y_series.notna().any() else 0.0
        conditions = [
            (x_series >= x_threshold) & (y_series >= y_threshold),
            (x_series < x_threshold) & (y_series >= y_threshold),
            (x_series < x_threshold) & (y_series < y_threshold),
        ]
        band_values = [
            labels["expand"],
            labels["optimize"],
            labels["validate"],
        ]
        band_frame["band_name"] = np.select(conditions, band_values, default=labels["shrink"])
    elif chart_key == "custom_top_bottom":
        value_series = _coerce_float_series(band_frame, "value")
        high_threshold = float(value_series.quantile(0.67)) if value_series.notna().any() else 0.0
        low_threshold = float(value_series.quantile(0.33)) if value_series.notna().any() else 0.0
        conditions = [
            value_series >= high_threshold,
            value_series <= low_threshold,
        ]
        band_values = [
            labels["high_positive"],
            labels["negative"],
        ]
        band_frame["band_name"] = np.select(conditions, band_values, default=labels["neutral"])
    else:
        score_column = next((column for column in ["y_value", "value", "mean", "selected_rate"] if column in band_frame.columns), "")
        score_series = _coerce_float_series(band_frame, score_column) if score_column else pd.Series(dtype="float64")
        high_threshold = float(score_series.quantile(0.67)) if score_series.notna().any() else 0.0
        low_threshold = float(score_series.quantile(0.33)) if score_series.notna().any() else 0.0
        conditions = [
            score_series >= high_threshold,
            score_series <= low_threshold,
        ]
        band_values = [labels["high_positive"], labels["negative"]]
        band_frame["band_name"] = np.select(conditions, band_values, default=labels["neutral"])
    band_frame["owner"] = default_owner
    band_frame["checkpoint"] = default_checkpoint
    return band_frame, label_column


def _generic_band_rows_for_chart(
    *,
    asset: dict[str, Any],
    frame: pd.DataFrame,
    source_csv_name: str,
    report_lens: str = "",
    smart_lens_payload: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    chart_key = _generic_chart_key(asset, frame)
    if not chart_key:
        return []
    band_frame, label_column = _generic_band_frame(frame, chart_key)
    title = _safe_text(asset.get("title") or asset.get("name"))
    chart_id = _safe_text(asset.get("figure_id") or asset.get("name"))
    chart_type = _safe_text(asset.get("chart_type") or asset.get("chart_family"))
    relevant_numeric_columns = [
        column
        for column in [
            "mean",
            "delta_vs_overall",
            "selected_rate",
            "mean_lift_vs_independent",
            "value",
            "size",
            "x_value",
            "y_value",
            "size_value",
            "n",
        ]
        if column in band_frame.columns
    ]
    lens = "business_management" if _safe_text(report_lens) == "business_management" else "smart_lens"
    smart_lens_payload = smart_lens_payload or {}
    smart_lens_name = _safe_text(smart_lens_payload.get("lens_name"))
    smart_flow = "；".join(
        _safe_text(item.get("step") if isinstance(item, dict) else item)
        for item in list(smart_lens_payload.get("narrative_flow") or [])[:3]
        if _safe_text(item.get("step") if isinstance(item, dict) else item)
    )
    chart_question = (
        _generic_chart_business_question(chart_key, title)
        if lens == "business_management"
        else f"{smart_lens_name or '本次智能镜头'}下，{title or chart_id} 用来解释哪些对象分区、指标差异和证据边界最关键？"
    )
    rows: list[dict[str, Any]] = []
    for band_name, subset in band_frame.groupby("band_name", dropna=False):
        subset = subset.copy()
        object_labels = [value for value in subset[label_column].astype(str).tolist() if _safe_text(value)]
        if not object_labels:
            continue
        representative = object_labels[:4]
        point_ids = [value for value in subset.get("图中序号", pd.Series(dtype="object")).astype(str).tolist() if _safe_text(value)] if "图中序号" in subset.columns else []
        representative_point_ids = point_ids[:4]
        source_table_set = _object_list_text(
            list(dict.fromkeys(str(value) for value in subset.get("source_table_set", pd.Series(dtype="object")).dropna().tolist()))
        ) if "source_table_set" in subset.columns else ""
        join_context = _safe_text(subset.get("join_context", pd.Series(dtype="object")).dropna().iloc[0]) if "join_context" in subset.columns and not subset.get("join_context", pd.Series(dtype="object")).dropna().empty else ""
        analysis_interpretation = (
            f"按“{smart_lens_name or '本次智能镜头'}”阅读，“{band_name}”是对象位置与指标组合形成的分区；{smart_flow or '需要结合图中序号、派生指标和数值边界解释'}。"
            if lens != "business_management"
            else ""
        )
        follow_up_question = (
            "这些对象的分区差异是否由样本量、缺失值、极端值或分组结构驱动？"
            if lens != "business_management"
            else ""
        )
        validation_note = (
            "结合图中序号映射表复核该分区全部对象、字段和值，再形成解释边界。"
            if lens != "business_management"
            else ""
        )
        rows.append(
            {
                "chart_id": chart_id,
                "chart_title": title,
                "chart_family": chart_key,
                "chart_type": chart_type,
                "business_question": chart_question,
                "analysis_question": chart_question,
                "smart_lens_name": smart_lens_name,
                "band_name": str(band_name),
                "object_count": int(len(object_labels)),
                "object_list": _object_list_text(object_labels),
                "representative_objects": _object_list_text(representative),
                "representative_point_ids": _object_list_text(representative_point_ids),
                "metric_range": _metric_range_text(subset, relevant_numeric_columns),
                "analysis_interpretation": analysis_interpretation,
                "follow_up_question": follow_up_question,
                "validation_note": validation_note,
                "management_action": _generic_band_action(chart_key, str(band_name)) if lens == "business_management" else "",
                "owner": _safe_text(subset["owner"].iloc[0]) if lens == "business_management" and "owner" in subset.columns and not subset.empty else "",
                "checkpoint": _safe_text(subset["checkpoint"].iloc[0]) if lens == "business_management" and "checkpoint" in subset.columns and not subset.empty else "",
                "source_csv": source_csv_name,
                "source_table_set": source_table_set,
                "join_context": join_context,
                "required_bubble": bool("bubble" in chart_key or "scatter" in chart_key or chart_key == "quadrant"),
                "source_row_count": int(frame.shape[0]),
            }
        )
    return rows


def build_generic_bubble_coverage_manifest(
    *,
    workspace_path: str | Path,
    business_profile: str = "",
    report_lens: str = "",
) -> dict[str, Any]:
    workspace = Path(workspace_path).expanduser().resolve()
    index_payload = _read_json_if_exists(workspace / "source_visual_assets_index.json")
    route_payload = _read_json_if_exists(workspace / GENERIC_VISUAL_ROUTE_CONTRACT_JSON_NAME)
    lens = _safe_text(report_lens or route_payload.get("report_lens") or "smart_lens")
    if lens != "business_management":
        lens = "smart_lens"
    profile = _safe_text(business_profile) or ("generic_long_business_report" if lens == "business_management" else "generic_long_smart_lens_report")
    route_index = {
        _safe_text(item.get("figure_id") or f"{_safe_text(item.get('candidate_id'))}.png"): item
        for item in list(route_payload.get("visual_candidates") or [])
        if isinstance(item, dict)
    }
    image_assets = [item for item in list(index_payload.get("image_assets") or []) if isinstance(item, dict)]
    csv_assets = [item for item in list(index_payload.get("csv_assets") or []) if isinstance(item, dict)]
    charts: list[dict[str, Any]] = []
    seen_chart_ids: set[str] = set()
    for asset in image_assets:
        figure_id = _safe_text(asset.get("figure_id") or asset.get("name"))
        chart_type = _safe_text(asset.get("chart_type") or asset.get("chart_family"))
        csv_name = ""
        files = list((asset.get("data_source_files") or []))
        if files:
            csv_name = _safe_text(files[0])
        csv_path = workspace / "source_visual_assets" / csv_name if csv_name else Path()
        frame = _read_csv_frame(csv_path) if csv_name else pd.DataFrame()
        chart_key = _generic_chart_key(asset, frame)
        if not chart_key:
            continue
        route_candidate = route_index.get(figure_id) or route_index.get(f"{Path(figure_id).stem}.png")
        visual_token = f"{figure_id} {chart_type}".lower()
        required_bubble = bool(route_candidate.get("required_bubble")) if isinstance(route_candidate, dict) else any(marker in visual_token for marker in ("bubble", "scatter", "portfolio", "risk", "quadrant"))
        allowed_forms = ["heatmap"]
        if required_bubble or "quadrant" in visual_token or "bubble" in visual_token or "scatter" in visual_token or "portfolio" in visual_token:
            allowed_forms = ["quadrant_bubble"]
        elif chart_key == "custom_top_bottom":
            allowed_forms = ["top_bottom"]
        charts.append(
            {
                "chart_id": figure_id,
                "chart_title": _safe_text(asset.get("title") or figure_id),
                "chart_family": chart_key,
                "chart_type": chart_type,
                "relative_path": _safe_text(asset.get("relative_path") or ""),
                "source_csv": csv_name,
                "required_bubble": required_bubble,
                "main_report_candidate": bool(route_candidate.get("main_report_candidate")) if isinstance(route_candidate, dict) else False,
                "allowed_visual_forms": allowed_forms,
                "object_scope": _safe_text(asset.get("object_scope") or "overall"),
                "source_row_count": int(frame.shape[0]),
                "plottable_row_count": int((pd.to_numeric(frame.get("x_value"), errors="coerce").notna() & pd.to_numeric(frame.get("y_value"), errors="coerce").notna()).sum()) if {"x_value", "y_value"}.issubset(set(frame.columns.astype(str).tolist())) else 0,
                "unplottable_row_count": int(frame.shape[0] - ((pd.to_numeric(frame.get("x_value"), errors="coerce").notna() & pd.to_numeric(frame.get("y_value"), errors="coerce").notna()).sum())) if {"x_value", "y_value"}.issubset(set(frame.columns.astype(str).tolist())) else 0,
                "figure_group_id": _safe_text((route_candidate or {}).get("figure_group_id") or (route_candidate or {}).get("candidate_id") or figure_id),
                "coverage_explanation": _safe_text((route_candidate or {}).get("coverage_explanation") or (route_candidate or {}).get("join_context") or ""),
                "reason": (
                    "This chart has row-level object points and must stay reader-facing as a numbered quadrant bubble."
                    if required_bubble
                    else "This chart stays non-bubble but still participates in object-band indexing."
                ),
                "business_profile": profile,
                "report_lens": lens,
            }
        )
        seen_chart_ids.add(figure_id)
    for asset in csv_assets:
        csv_name = _safe_text(asset.get("name") or "")
        if not csv_name:
            continue
        implied_chart_id = f"{Path(csv_name).stem}.png"
        if implied_chart_id in seen_chart_ids:
            continue
        csv_path = workspace / "source_visual_assets" / csv_name
        frame = _read_csv_frame(csv_path)
        if frame.empty:
            continue
        columns = {str(column) for column in frame.columns.astype(str).tolist()}
        token = f"{csv_name} {' '.join(columns)}".lower()
        has_xy_size = {"x_value", "y_value", "size_value"}.issubset(columns) or {"x_metric", "y_metric", "size_metric"}.issubset(columns)
        looks_like_bubble = any(marker in token for marker in ("bubble", "scatter", "portfolio", "outlier", "risk")) or has_xy_size
        if not looks_like_bubble:
            continue
        charts.append(
            {
                "chart_id": implied_chart_id,
                "chart_title": _safe_text(asset.get("title") or implied_chart_id),
                "chart_family": _generic_chart_key({"name": implied_chart_id, "chart_type": "bubble"}, frame) or "generic_bubble",
                "chart_type": "quadrant_bubble",
                "relative_path": f"source_visual_assets/{implied_chart_id}",
                "source_csv": csv_name,
                "required_bubble": True,
                "main_report_candidate": bool((route_index.get(implied_chart_id) or {}).get("main_report_candidate")),
                "allowed_visual_forms": ["quadrant_bubble"],
                "object_scope": "overall",
                "source_row_count": int(frame.shape[0]),
                "plottable_row_count": int((pd.to_numeric(frame.get("x_value"), errors="coerce").notna() & pd.to_numeric(frame.get("y_value"), errors="coerce").notna()).sum()) if {"x_value", "y_value"}.issubset(set(frame.columns.astype(str).tolist())) else 0,
                "unplottable_row_count": int(frame.shape[0] - ((pd.to_numeric(frame.get("x_value"), errors="coerce").notna() & pd.to_numeric(frame.get("y_value"), errors="coerce").notna()).sum())) if {"x_value", "y_value"}.issubset(set(frame.columns.astype(str).tolist())) else 0,
                "figure_group_id": implied_chart_id,
                "coverage_explanation": _safe_text((route_index.get(implied_chart_id) or {}).get("coverage_explanation") or ""),
                "reason": "This CSV has x/y/size-like object rows and therefore requires a reader-facing numbered quadrant bubble.",
                "business_profile": profile,
                "report_lens": lens,
            }
        )
        seen_chart_ids.add(implied_chart_id)
    for figure_id, route_candidate in route_index.items():
        if figure_id in seen_chart_ids:
            continue
        charts.append(
            {
                "chart_id": figure_id,
                "chart_title": _safe_text(route_candidate.get("object_dimension") or route_candidate.get("candidate_id") or figure_id),
                "chart_family": _safe_text(route_candidate.get("chart_form") or ""),
                "chart_type": _safe_text(route_candidate.get("chart_form") or ""),
                "relative_path": f"source_visual_assets/{figure_id}",
                "source_csv": "",
                "required_bubble": bool(route_candidate.get("required_bubble")),
                "main_report_candidate": bool(route_candidate.get("main_report_candidate")),
                "allowed_visual_forms": [str(route_candidate.get("chart_form") or "")],
                "object_scope": _safe_text(route_candidate.get("object_dimension") or "overall"),
                "source_row_count": 0,
                "plottable_row_count": 0,
                "unplottable_row_count": 0,
                "figure_group_id": _safe_text(route_candidate.get("figure_group_id") or route_candidate.get("candidate_id") or figure_id),
                "coverage_explanation": _safe_text(route_candidate.get("coverage_explanation") or route_candidate.get("join_context") or ""),
                "reason": "Required by generic visual route contract but not yet rendered into source_visual_assets.",
                "business_profile": profile,
                "report_lens": lens,
            }
        )
    payload = {
        "version": "generic_bubble_coverage_manifest_v1",
        "source": "deterministic_generic_visual_bubble_coverage",
        "business_profile": profile,
        "report_lens": lens,
        "chart_count": len(charts),
        "charts": charts,
    }
    _write_json(workspace / GENERIC_BUBBLE_COVERAGE_MANIFEST_NAME, payload)
    return payload


def build_generic_visual_band_index(
    *,
    workspace_path: str | Path,
    business_profile: str = "",
    report_lens: str = "",
) -> dict[str, Any]:
    workspace = Path(workspace_path).expanduser().resolve()
    index_payload = _read_json_if_exists(workspace / "source_visual_assets_index.json")
    route_payload = _read_json_if_exists(workspace / GENERIC_VISUAL_ROUTE_CONTRACT_JSON_NAME)
    lens = _safe_text(report_lens or route_payload.get("report_lens") or "smart_lens")
    if lens != "business_management":
        lens = "smart_lens"
    profile = _safe_text(business_profile) or ("generic_long_business_report" if lens == "business_management" else "generic_long_smart_lens_report")
    smart_lens_payload = _read_json_if_exists(workspace / "generic_smart_lens_contract.json")
    route_index = {
        _safe_text(item.get("figure_id") or f"{_safe_text(item.get('candidate_id'))}.png"): item
        for item in list(route_payload.get("visual_candidates") or [])
        if isinstance(item, dict)
    }
    image_assets = [item for item in list(index_payload.get("image_assets") or []) if isinstance(item, dict)]
    charts: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    for asset in image_assets:
        files = list((asset.get("data_source_files") or []))
        if not files:
            continue
        csv_name = _safe_text(files[0])
        if not csv_name:
            continue
        csv_path = workspace / "source_visual_assets" / csv_name
        chart_id = _safe_text(asset.get("figure_id") or asset.get("name"))
        route_candidate = route_index.get(chart_id) or route_index.get(f"{Path(chart_id).stem}.png")
        frame = _normalize_generic_point_csv(
            csv_path=csv_path,
            asset=asset,
            route_candidate=route_candidate if isinstance(route_candidate, dict) else None,
        )
        if frame.empty:
            continue
        chart_rows = _generic_band_rows_for_chart(
            asset=asset,
            frame=frame,
            source_csv_name=csv_name,
            report_lens=lens,
            smart_lens_payload=smart_lens_payload,
        )
        if not chart_rows:
            continue
        charts.append(
            {
                "chart_id": chart_id,
                "chart_title": _safe_text(asset.get("title") or chart_id),
                "chart_family": _safe_text(chart_rows[0].get("chart_family")),
                "chart_type": _safe_text(asset.get("chart_type") or asset.get("chart_family")),
                "source_csv": csv_name,
                "band_count": len(chart_rows),
                "source_row_count": int(frame.shape[0]),
                "plottable_row_count": int((frame.get("plot_status", pd.Series(dtype="object")).astype(str) == "plottable").sum()) if "plot_status" in frame.columns else int(frame.shape[0]),
                "unplottable_row_count": int((frame.get("plot_status", pd.Series(dtype="object")).astype(str) != "plottable").sum()) if "plot_status" in frame.columns else 0,
                "object_universe_count": int(_read_json_if_exists(workspace / "generic_object_universe.json").get("object_count") or 0) if (workspace / "generic_object_universe.json").exists() else 0,
                "figure_group_id": _safe_text((route_candidate or {}).get("figure_group_id") or (route_candidate or {}).get("candidate_id") or chart_id),
                "coverage_explanation": _safe_text((route_candidate or {}).get("coverage_explanation") or (route_candidate or {}).get("join_context") or ""),
                "business_question": _safe_text(chart_rows[0].get("business_question")),
                "analysis_question": _safe_text(chart_rows[0].get("analysis_question")),
                "smart_lens_name": _safe_text(chart_rows[0].get("smart_lens_name")),
                "object_scope": _safe_text(asset.get("object_scope") or "overall"),
                "source_table_set": _safe_text(chart_rows[0].get("source_table_set")),
                "join_context": _safe_text(chart_rows[0].get("join_context")),
                "report_lens": lens,
            }
        )
        rows.extend(chart_rows)
    payload = {
        "version": "generic_visual_band_index_v1",
        "source": "deterministic_generic_visual_band_index",
        "business_profile": profile,
        "report_lens": lens,
        "chart_count": len(charts),
        "row_count": len(rows),
        "object_universe_count": int(_read_json_if_exists(workspace / "generic_object_universe.json").get("object_count") or 0) if (workspace / "generic_object_universe.json").exists() else 0,
        "charts": charts,
        "rows": rows,
    }
    _write_json(workspace / GENERIC_VISUAL_BAND_INDEX_JSON_NAME, payload)
    _write_csv(
        workspace / GENERIC_VISUAL_BAND_INDEX_CSV_NAME,
        rows,
        [
            "chart_id",
            "chart_title",
            "chart_family",
            "chart_type",
            "business_question",
            "analysis_question",
            "smart_lens_name",
            "band_name",
            "object_count",
            "object_list",
            "representative_objects",
            "representative_point_ids",
            "metric_range",
            "analysis_interpretation",
            "follow_up_question",
            "validation_note",
            "management_action",
            "owner",
            "checkpoint",
            "source_csv",
            "source_table_set",
            "join_context",
            "required_bubble",
            "source_row_count",
            "plottable_row_count",
            "unplottable_row_count",
            "object_universe_count",
            "figure_group_id",
            "coverage_explanation",
        ],
    )
    return payload


def _normalize_route_field_name(value: Any) -> str:
    text = _safe_text(value)
    text = re.sub(r"^sheet_\d+_[a-z0-9]+__", "", text, flags=re.I)
    text = re.sub(r"[锛?][^锛?]*[锛?]", "", text)
    text = re.sub(r"\s+", "", text)
    return text


def _metric_role_payload(*, metric_id: str, metric_name: str, operation: str, formula: str = "") -> dict[str, str]:
    token = _normalize_token(" ".join([metric_id, metric_name, operation, formula]))
    if operation in {"row_count", "nunique"} or any(key in token for key in ("数量", "count", "记录数", "次数", "projectcount", "fundcount", "项目数量", "基金会数量", "理事会")):
        return {"role_family": "count_metrics", "role_subtype": "count"}
    if operation == "ratio" or any(key in token for key in ("姣旂巼", "鍗犳瘮", "rate", "ratio", "share")):
        return {"role_family": "ratio_metrics", "role_subtype": "ratio"}
    if any(key in token for key in ("鏀跺叆", "revenue", "sales", "donation", "鎹愯禒", "income")):
        return {"role_family": "scale_metrics", "role_subtype": "income"}
    if any(key in token for key in ("鏀嚭", "expense", "cost", "spend", "鍏泭浜嬩笟")):
        return {"role_family": "scale_metrics", "role_subtype": "expense"}
    if any(key in token for key in ("退货", "折扣", "库存", "履约", "delivery", "days", "return", "discount", "inventory")):
        return {"role_family": "risk_or_efficiency_metrics", "role_subtype": "risk_efficiency"}
    if any(key in token for key in ("满意", "评分", "score", "lifetime", "价值", "value", "quality", "mean", "median")):
        return {"role_family": "quality_or_value_metrics", "role_subtype": "quality_value"}
    if any(key in token for key in ("骞村害", "year", "month", "week", "time", "trend")):
        return {"role_family": "time_dimensions", "role_subtype": "time"}
    return {"role_family": "scale_metrics", "role_subtype": "generic_scale"}


def _route_dimension_kind(groups: dict[str, Any]) -> tuple[str, str]:
    normalized = [_normalize_route_field_name(key) for key in groups.keys()]
    if any("统一信用代码" in key or "基金会名称" in key for key in normalized):
        return "fund", "基金会"
    if any("服务领域" in key for key in normalized):
        return "service_domain", "服务领域"
    if any("基金会类型" in key for key in normalized):
        return "fund_type", "基金会类型"
    if any("注册地省份" in key or "省份" in key for key in normalized):
        return "registration_province", "注册地省份"
    if any("项目地点" in key for key in normalized):
        return "project_location", "项目地点"
    if any("项目名称" in key for key in normalized):
        return "project_name", "项目名称"
    if any("channel" in key for key in normalized):
        return "channel", "渠道"
    if any("region" in key for key in normalized):
        return "region", "区域"
    if any("customersegment" in key or "客户分层" in key for key in normalized):
        return "customer_segment", "客户分层"
    if any("category" in key or "品类" in key for key in normalized):
        return "category", "品类"
    if normalized:
        return normalized[0], normalized[0]
    return "overall", "整体"


def _route_object_identity(groups: dict[str, Any], fallback_group: str) -> dict[str, Any]:
    normalized_groups = {_normalize_route_field_name(key): value for key, value in groups.items()}
    dimension_kind, dimension_label = _route_dimension_kind(groups)
    code = next((str(value) for key, value in normalized_groups.items() if "统一信用代码" in key and _safe_text(value)), "")
    fund_name = next((str(value) for key, value in normalized_groups.items() if "基金会名称" in key and _safe_text(value)), "")
    year = next((str(value) for key, value in normalized_groups.items() if "年度" in key and _safe_text(value)), "")
    if dimension_kind == "fund":
        object_key = code or fund_name or fallback_group
        object_label = fund_name or fallback_group or code
        if year:
            object_key = f"{object_key} | {year}"
            object_label = f"{object_label} | {year}"
        key_fields = [field for field in ["基金会名称", "统一信用代码", "年度"] if any(field in key for key in normalized_groups)]
    else:
        primary_key = next(iter(normalized_groups.keys()), dimension_label)
        primary_value = next(iter(normalized_groups.values()), fallback_group)
        object_key = _safe_text(primary_value) or fallback_group
        object_label = _safe_text(primary_value) or fallback_group
        key_fields = [primary_key]
    return {
        "dimension_kind": dimension_kind,
        "dimension_label": dimension_label,
        "object_key": object_key,
        "object_label": object_label,
        "key_fields": key_fields,
        "normalized_groups": normalized_groups,
    }


def _append_unique_label(target: list[str], value: str) -> None:
    text = _safe_text(value)
    if text and text not in target:
        target.append(text)


def _route_metric_summary_frame(records: list[dict[str, Any]]) -> pd.DataFrame:
    frame = pd.DataFrame(records)
    if frame.empty:
        return frame
    frame = frame.dropna(subset=["value"])
    frame = frame.loc[frame["object_key"].astype(str).str.strip().ne("")]
    return frame


def _metric_priority_score(metric_name: str, role_subtype: str) -> int:
    token = _normalize_token(metric_name)
    if role_subtype == "income":
        if any(key in token for key in ("捐赠收入", "donation")):
            return 92
        if any(key in token for key in ("年度收入", "本年度收入", "收入合计", "totalincome")):
            return 100
        if any(key in token for key in ("项目收入", "projectincome")):
            return 90
        return 80
    if role_subtype == "expense":
        if any(key in token for key in ("年度总支出", "本年度总支出", "总支出", "totalexpense")):
            return 100
        if any(key in token for key in ("项目支出", "projectexpense")):
            return 92
        return 82
    if role_subtype == "count":
        if any(key in token for key in ("项目数量", "projectcount")):
            return 100
        if any(key in token for key in ("基金会数量", "fundcount")):
            return 88
        return 78
    if role_subtype == "ratio":
        return 74
    if role_subtype == "risk_efficiency":
        return 72
    if role_subtype == "quality_value":
        return 70
    return 60


def _multi_table_route_metric_index(workspace: Path) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], dict[str, pd.DataFrame]]:
    relationship_payload = _read_json_if_exists(workspace / "02_relationship_model.json")
    metric_frame = _read_csv_frame(workspace / "cross_table_metric_values.csv")
    derived_frame = _read_csv_frame(workspace / "generic_derived_metric_values.csv")
    metric_rows = [row for row in metric_frame.to_dict(orient="records") if _safe_text(row.get("status")) == "completed"]
    derived_rows = [row for row in derived_frame.to_dict(orient="records") if _safe_text(row.get("status")) == "completed"]
    metric_rows.extend(derived_rows)
    records: list[dict[str, Any]] = []
    metric_maps: dict[str, pd.DataFrame] = {}
    for row in metric_rows:
        detail_rows = _safe_json_list(row.get("detail_rows_json"))
        if not detail_rows:
            continue
        role = _metric_role_payload(
            metric_id=_safe_text(row.get("metric_id")),
            metric_name=_safe_text(row.get("metric_name")),
            operation=_safe_text(row.get("operation")),
            formula=_safe_text(row.get("formula")),
        )
        processed_rows: list[dict[str, Any]] = []
        for item in detail_rows:
            groups = dict(item.get("groups") or {})
            identity = _route_object_identity(groups, _safe_text(item.get("group")))
            value = _safe_float(item.get("value"))
            if value is None:
                continue
            processed_rows.append(
                {
                    "metric_id": _safe_text(row.get("metric_id")),
                    "metric_name": _safe_text(row.get("metric_name")),
                    "table_id": _safe_text(row.get("table_id")),
                    "operation": _safe_text(row.get("operation")),
                    "formula": _safe_text(row.get("formula")),
                    "reason": _safe_text(row.get("reason")),
                    "value": value,
                    "n": int(_safe_float(item.get("n")) or 0),
                    "group": _safe_text(item.get("group")),
                    "groups": groups,
                    **identity,
                    **role,
                }
            )
        metric_df = _route_metric_summary_frame(processed_rows)
        if metric_df.empty or int(metric_df["object_key"].nunique()) < 3:
            continue
        metric_maps[_safe_text(row.get("metric_id"))] = metric_df
        sample = metric_df.iloc[0].to_dict()
        records.append(
            {
                "metric_id": _safe_text(row.get("metric_id")),
                "metric_name": _safe_text(row.get("metric_name")),
                "table_id": _safe_text(row.get("table_id")),
                "operation": _safe_text(row.get("operation")),
                "formula": _safe_text(row.get("formula")),
                "reason": _safe_text(row.get("reason")),
                "dimension_kind": _safe_text(sample.get("dimension_kind")),
                "dimension_label": _safe_text(sample.get("dimension_label")),
                "key_fields": list(sample.get("key_fields") or []),
                "role_family": _safe_text(sample.get("role_family")),
                "role_subtype": _safe_text(sample.get("role_subtype")),
                "priority_score": _metric_priority_score(_safe_text(row.get("metric_name")), _safe_text(sample.get("role_subtype"))),
                "object_count": int(metric_df["object_key"].nunique()),
            }
        )
    return relationship_payload, metric_rows, records, metric_maps


def build_generic_visual_route_contract(
    *,
    workspace_path: str | Path,
    business_profile: str = "",
) -> dict[str, Any]:
    raise RuntimeError(
        "generic_visual_route_contract must be produced by the Codex runtime "
        "visual_route_decision stage; backend code may validate and render it, "
        "but must not synthesize visual candidates."
    )


def _cross_table_detail_records(metric_frame: pd.DataFrame) -> list[dict[str, Any]]:
    def normalize_group_key(key: str) -> str:
        return re.sub(r"^sheet_\d+_[a-z0-9]+__", "", _safe_text(key), flags=re.I)

    records: list[dict[str, Any]] = []
    for row in metric_frame.to_dict(orient="records"):
        if _safe_text(row.get("status")) != "completed":
            continue
        detail_rows = _safe_json_list(row.get("detail_rows_json"))
        if not detail_rows:
            continue
        for item in detail_rows:
            raw_groups = dict(item.get("groups") or {})
            groups = {normalize_group_key(key): value for key, value in raw_groups.items()}
            records.append(
                {
                    "metric_id": _safe_text(row.get("metric_id")),
                    "metric_name": _safe_text(row.get("metric_name")),
                    "table_id": _safe_text(row.get("table_id")),
                    "operation": _safe_text(row.get("operation")),
                    "formula": _safe_text(row.get("formula")),
                    "reason": _safe_text(row.get("reason")),
                    "group": _safe_text(item.get("group")),
                    "groups": groups,
                    "group_signature": " | ".join(sorted(groups.keys())) if groups else "group",
                    "n": int(_safe_float(item.get("n")) or 0),
                    "value": _safe_float(item.get("value")),
                }
            )
    return records


def _cross_table_bubble_candidates(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_signature: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        by_signature.setdefault(str(record.get("group_signature") or "group"), []).append(record)
    candidates: list[dict[str, Any]] = []
    for signature, signature_records in by_signature.items():
        metric_groups: dict[str, list[dict[str, Any]]] = {}
        for record in signature_records:
            metric_groups.setdefault(str(record.get("metric_id") or ""), []).append(record)
        if len(metric_groups) < 2:
            continue
        normalized: dict[str, pd.DataFrame] = {}
        for metric_id, rows in metric_groups.items():
            frame = pd.DataFrame(rows)
            if frame.empty or frame["group"].nunique() < 3:
                continue
            normalized[metric_id] = frame
        if len(normalized) < 2:
            continue

        def choose_metric(predicate: Any, *, exclude: set[str] | None = None) -> str:
            exclude = exclude or set()
            ranked: list[tuple[int, str]] = []
            for metric_id, frame in normalized.items():
                if metric_id in exclude:
                    continue
                sample = frame.iloc[0].to_dict()
                metric_name = _safe_text(sample.get("metric_name"))
                operation = _safe_text(sample.get("operation"))
                score = predicate(metric_name, operation)
                if score > 0:
                    ranked.append((score, metric_id))
            ranked.sort(reverse=True)
            return ranked[0][1] if ranked else ""

        size_metric = choose_metric(
            lambda name, operation: 100
            if operation in {"sum", "row_count", "nunique"}
            or any(token in _normalize_token(name) for token in ("sales", "revenue", "amount", "count", "order", "customer", "product", "订单", "销售", "收入", "数量"))
            else 0
        )
        y_metric = choose_metric(
            lambda name, operation: 100
            if any(token in _normalize_token(name) for token in ("margin", "satisfaction", "lifetime", "value", "sales", "revenue", "score", "毛利", "满意", "价值", "销售", "收入", "评分"))
            else (80 if operation in {"ratio", "mean", "sum"} else 0),
            exclude={size_metric} if size_metric else set(),
        )
        x_metric = choose_metric(
            lambda name, operation: 100
            if any(token in _normalize_token(name) for token in ("return", "discount", "inventory", "delivery", "days", "rate", "cost", "退货", "折扣", "库存", "履约", "天数", "成本", "率"))
            else (70 if operation in {"ratio", "mean"} else 0),
            exclude={item for item in [size_metric, y_metric] if item},
        )
        if not y_metric:
            continue
        if not x_metric:
            x_metric = choose_metric(lambda _name, operation: 60 if operation in {"ratio", "mean", "sum"} else 0, exclude={item for item in [size_metric, y_metric] if item})
        if not x_metric:
            continue
        if not size_metric:
            size_metric = choose_metric(lambda _name, operation: 40 if operation in {"row_count", "nunique", "sum"} else 0, exclude={item for item in [x_metric, y_metric] if item})
        if not size_metric:
            size_metric = y_metric

        x_frame = normalized[x_metric][["group", "value", "n", "groups", "reason", "formula", "table_id", "metric_name"]].rename(
            columns={"value": "x_value", "n": "x_n", "metric_name": "x_metric_name"}
        )
        y_frame = normalized[y_metric][["group", "value", "n", "metric_name"]].rename(
            columns={"value": "y_value", "n": "y_n", "metric_name": "y_metric_name"}
        )
        size_frame = normalized[size_metric][["group", "value", "n", "metric_name"]].rename(
            columns={"value": "size_value", "n": "size_n", "metric_name": "size_metric_name"}
        )
        merged = x_frame.merge(y_frame, on=["group"], how="inner").merge(size_frame, on=["group"], how="left")
        if merged.empty:
            continue
        merged["n"] = (
            pd.to_numeric(merged.get("x_n"), errors="coerce")
            .fillna(pd.to_numeric(merged.get("y_n"), errors="coerce"))
            .fillna(pd.to_numeric(merged.get("size_n"), errors="coerce"))
            .fillna(0)
        )
        merged["size_value"] = pd.to_numeric(merged["size_value"], errors="coerce").fillna(pd.to_numeric(merged["n"], errors="coerce")).fillna(1.0)
        x_missing = pd.to_numeric(merged.get("x_value"), errors="coerce").isna()
        y_missing = pd.to_numeric(merged.get("y_value"), errors="coerce").isna()
        merged["plot_status"] = np.where(~x_missing & ~y_missing, "plottable", "missing_coordinates")
        merged["missing_coordinate_reason"] = np.select(
            [x_missing & y_missing, x_missing, y_missing],
            ["missing_x_and_y", "missing_x", "missing_y"],
            default="",
        )
        if merged.shape[0] < 3:
            continue
        groups = dict(merged.iloc[0].get("groups") or {})
        source_table_set = sorted({str(item.get("table_id") or "") for item in signature_records if _safe_text(item.get("table_id"))})
        candidates.append(
            {
                "signature": signature,
                "groups": groups,
                "source_table_set": source_table_set,
                "join_context": _safe_text(merged.iloc[0].get("reason") or merged.iloc[0].get("formula")),
                "frame": merged.sort_values("size_value", ascending=False).reset_index(drop=True),
            }
        )
    candidates.sort(key=lambda item: (-len(item.get("source_table_set") or []), -int(item["frame"].shape[0]), str(item.get("signature") or "")))
    return candidates[:4]


def _cross_table_chart_title(groups: dict[str, Any], frame: pd.DataFrame) -> str:
    label_map = {
        "channel": "渠道",
        "region": "区域",
        "customer_segment": "客户分层",
        "city_tier": "城市层级",
        "price_band_q4": "价格带",
        "strategic_priority": "战略优先级",
        "product_id": "商品对象",
        "sheet_02_customers__customer_segment": "客户分层",
        "sheet_02_customers__acquisition_channel": "获客来源",
        "sheet_03_products__category": "品类",
        "sheet_03_products__brand": "品牌",
        "sheet_03_products__strategic_priority": "战略优先级",
    }
    signature = " × ".join(label_map.get(key, key) for key in groups.keys()) if groups else "跨表对象"
    x_name = _safe_text(frame.iloc[0].get("x_metric_name"))
    y_name = _safe_text(frame.iloc[0].get("y_metric_name"))
    size_name = _safe_text(frame.iloc[0].get("size_metric_name"))
    return f"{signature}：{y_name} × {x_name} × {size_name} 气泡图"


def _seed_multi_table_visual_assets(
    *,
    workspace_path: str | Path,
    business_profile: str = "multi_table_generic_long_cli_pipeline",
) -> dict[str, Any]:
    workspace = Path(workspace_path).expanduser().resolve()
    metric_values_path = workspace / "cross_table_metric_values.csv"
    single_table_values_path = workspace / "custom_metrics_dataset.csv"
    visual_dir = workspace / "source_visual_assets"
    visual_dir.mkdir(parents=True, exist_ok=True)
    metric_frame = _read_csv_frame(metric_values_path)
    single_table_metric_frame = pd.DataFrame()
    if metric_frame.empty:
        single_table_metric_frame = _read_csv_frame(single_table_values_path)
    single_table_mode = bool(metric_frame.empty and not single_table_metric_frame.empty)
    image_assets: list[dict[str, Any]] = []
    csv_assets: list[dict[str, Any]] = []
    if metric_frame.empty and single_table_metric_frame.empty:
        payload = {
            "asset_dir": str(visual_dir.resolve()),
            "image_count": 0,
            "csv_count": 0,
            "image_assets": [],
            "csv_assets": [],
            "recommended_figure_slots": [],
            "recommended_main_report_figures": [],
            "recommended_appendix_figures": [],
            "seed_source": "cross_table_metric_values",
        }
        _write_json(workspace / "source_visual_assets_index.json", payload)
        return payload

    style = _configure_plot_style(workspace)
    route_payload = _read_json_if_exists(workspace / GENERIC_VISUAL_ROUTE_CONTRACT_JSON_NAME)
    route_candidates = [
        item
        for item in list(route_payload.get("visual_candidates") or [])
        if isinstance(item, dict) and str(item.get("chart_form") or "") == "quadrant_bubble"
    ]
    object_universe_frame = _read_csv_frame(workspace / "generic_object_universe.csv")
    if not object_universe_frame.empty and "object_key" in object_universe_frame.columns:
        object_universe_frame["object_key"] = object_universe_frame["object_key"].astype(str)
    else:
        object_universe_frame = pd.DataFrame()

    def should_use_object_universe(*frames: pd.DataFrame) -> bool:
        if object_universe_frame.empty or "object_key" not in object_universe_frame.columns:
            return False
        universe_keys = set(object_universe_frame["object_key"].astype(str).tolist())
        if not universe_keys:
            return False
        candidate_keys: set[str] = set()
        for item in frames:
            if item is None or item.empty or "object_key" not in item.columns:
                continue
            candidate_keys.update(item["object_key"].astype(str).tolist())
        overlap = len(universe_keys & candidate_keys)
        return overlap >= max(3, int(len(universe_keys) * 0.5))

    def align_metric_frame_to_object_universe(frame: pd.DataFrame) -> pd.DataFrame:
        if frame is None or frame.empty or "object_key" not in frame.columns:
            return frame
        if object_universe_frame.empty or "object_key" not in object_universe_frame.columns:
            return frame
        work = frame.copy()
        universe_keys = set(object_universe_frame["object_key"].astype(str).tolist())
        current_keys = set(work["object_key"].astype(str).tolist())
        if len(universe_keys & current_keys) >= max(3, int(len(universe_keys) * 0.5)):
            return work

        map_columns = ["object_key"]
        for column in ("object_label", "id_value", "label_value", "time_value", "object_index", "missing_detail_reason"):
            if column in object_universe_frame.columns and column not in map_columns:
                map_columns.append(column)
        universe_map = object_universe_frame[map_columns].copy()

        def apply_mapping(left_key: str, right_key: str) -> pd.DataFrame:
            if right_key not in universe_map.columns:
                return work
            mapping = universe_map.dropna(subset=[right_key]).copy()
            mapping[right_key] = mapping[right_key].astype(str)
            if mapping[right_key].duplicated().any():
                return work
            keyed = work.copy()
            keyed[left_key] = keyed[left_key].astype(str)
            merged_map = keyed.merge(
                mapping.rename(
                    columns={
                        "object_key": "__universe_object_key",
                        "object_label": "__universe_object_label",
                    }
                ),
                left_on=left_key,
                right_on=right_key,
                how="left",
            )
            hit = merged_map["__universe_object_key"].fillna("").astype(str).str.strip().ne("")
            if int(hit.sum()) < max(3, int(len(work) * 0.5)):
                return work
            for column in work.columns:
                if column not in merged_map.columns:
                    merged_map[column] = work[column].values
            merged_map["source_object_key"] = merged_map[left_key]
            merged_map["object_key"] = merged_map["__universe_object_key"].where(hit, merged_map["object_key"])
            if "object_label" in merged_map.columns:
                merged_map["object_label"] = (
                    merged_map["__universe_object_label"].where(
                        hit & merged_map["__universe_object_label"].fillna("").astype(str).str.strip().ne(""),
                        merged_map["object_label"],
                    )
                )
            keep_columns = list(dict.fromkeys([*work.columns, "source_object_key"]))
            return merged_map[keep_columns].copy()

        if "id_value" in universe_map.columns:
            work = apply_mapping("object_key", "id_value")
            current_keys = set(work["object_key"].astype(str).tolist())
            if len(universe_keys & current_keys) >= max(3, int(len(universe_keys) * 0.5)):
                return work
        if "label_value" in universe_map.columns and "object_label" in work.columns:
            work = apply_mapping("object_label", "label_value")
        return work

    def fill_missing_metric_values(merged: pd.DataFrame, value_column: str, operation_column: str) -> pd.Series:
        values = pd.to_numeric(merged.get(value_column), errors="coerce")
        operations = merged.get(operation_column, pd.Series("", index=merged.index)).fillna("").astype(str).str.lower()
        zero_safe = operations.isin({"sum", "row_count", "count", "count_rows", "nunique", "count_distinct"})
        missing_detail = (
            merged.get("missing_detail_reason", pd.Series("", index=merged.index))
            .fillna("")
            .astype(str)
            .str.strip()
            .ne("")
        )
        return values.mask(values.isna() & (zero_safe | missing_detail), 0)

    def frame_from_route_candidate(candidate: dict[str, Any]) -> pd.DataFrame:
        object_fields = [
            _safe_text(field)
            for field in list(candidate.get("object_key_fields") or [])
            if _safe_text(field)
        ]
        if not object_fields and _safe_text(candidate.get("object_dimension")):
            object_fields = [_safe_text(candidate.get("object_dimension"))]
        x_metric_id = _safe_text(candidate.get("x_metric_id"))
        y_metric_id = _safe_text(candidate.get("y_metric_id"))
        size_metric_id = _safe_text(candidate.get("size_metric_id"))
        if single_table_mode:
            if not object_fields or x_metric_id not in single_table_metric_frame.columns or y_metric_id not in single_table_metric_frame.columns:
                return pd.DataFrame()
            missing_object_fields = [field for field in object_fields if field not in single_table_metric_frame.columns]
            if missing_object_fields:
                return pd.DataFrame()
            work = single_table_metric_frame[object_fields + [x_metric_id, y_metric_id] + ([size_metric_id] if size_metric_id in single_table_metric_frame.columns else [])].copy()
            work[x_metric_id] = pd.to_numeric(work[x_metric_id], errors="coerce")
            work[y_metric_id] = pd.to_numeric(work[y_metric_id], errors="coerce")
            if size_metric_id in work.columns:
                work[size_metric_id] = pd.to_numeric(work[size_metric_id], errors="coerce")
            work = work.dropna(subset=[x_metric_id, y_metric_id])
            if work.empty:
                return pd.DataFrame()
            rows: list[dict[str, Any]] = []
            grouped = work.groupby(object_fields, dropna=False)
            size_mode = _safe_text(candidate.get("size_mode"))
            size_is_share = any(
                marker in f"{size_metric_id} {_safe_text(candidate.get('size_metric_name'))}".lower()
                for marker in ["share", "contribution", "鍗犳瘮", "浠介"]
            )
            for object_key, group_frame in grouped:
                key_values = object_key if isinstance(object_key, tuple) else (object_key,)
                label_parts = [str(value) if str(value).strip() else "缂哄け" for value in key_values]
                object_label = " / ".join(label_parts)
                if size_mode == "uniform_size" or not size_metric_id or size_metric_id not in group_frame.columns:
                    size_value = float(len(group_frame))
                else:
                    size_series = pd.to_numeric(group_frame[size_metric_id], errors="coerce")
                    size_value = float(size_series.sum(skipna=True) if size_is_share else size_series.mean(skipna=True))
                rows.append(
                    {
                        "object_key": object_label,
                        "object_label": object_label,
                        "x_value": float(pd.to_numeric(group_frame[x_metric_id], errors="coerce").mean(skipna=True)),
                        "y_value": float(pd.to_numeric(group_frame[y_metric_id], errors="coerce").mean(skipna=True)),
                        "size_value": size_value,
                        "n": int(len(group_frame)),
                        "group": object_label,
                        "x_metric_name": _safe_text(candidate.get("x_metric_name")) or x_metric_id,
                        "y_metric_name": _safe_text(candidate.get("y_metric_name")) or y_metric_id,
                        "size_metric_name": _safe_text(candidate.get("size_metric_name")) or size_metric_id,
                        "source_table_set": "custom_metrics_dataset",
                        "join_context": "single_table_groupby:" + " / ".join(object_fields),
                    }
                )
            result = pd.DataFrame(rows)
            x_missing = pd.to_numeric(result.get("x_value"), errors="coerce").isna()
            y_missing = pd.to_numeric(result.get("y_value"), errors="coerce").isna()
            result["plot_status"] = np.where(~x_missing & ~y_missing, "plottable", "missing_coordinates")
            result["missing_coordinate_reason"] = np.select(
                [x_missing & y_missing, x_missing, y_missing],
                ["missing_x_and_y", "missing_x", "missing_y"],
                default="",
            )
            return result.copy()
        role_payloads = _multi_table_route_metric_index(workspace)[3]
        x_frame = role_payloads.get(x_metric_id, pd.DataFrame()).copy()
        y_frame = role_payloads.get(y_metric_id, pd.DataFrame()).copy()
        if x_frame.empty or y_frame.empty:
            return pd.DataFrame()
        x_frame = align_metric_frame_to_object_universe(x_frame)
        y_frame = align_metric_frame_to_object_universe(y_frame)
        x_frame = x_frame[["object_key", "object_label", "value", "n", "table_id", "reason", "formula", "operation"]].rename(
            columns={"value": "x_value", "n": "x_n", "operation": "x_operation"}
        )
        y_frame = y_frame[["object_key", "object_label", "value", "n", "operation"]].rename(
            columns={"value": "y_value", "n": "y_n", "operation": "y_operation"}
        )
        use_universe = should_use_object_universe(x_frame, y_frame)
        if use_universe:
            base_columns = ["object_key", "object_label"]
            if "object_index" in object_universe_frame.columns:
                base_columns.append("object_index")
            if "missing_detail_reason" in object_universe_frame.columns:
                base_columns.append("missing_detail_reason")
            base = object_universe_frame[base_columns].drop_duplicates(subset=["object_key"]).rename(columns={"object_label": "universe_object_label"})
            merged = base.merge(x_frame, on=["object_key"], how="left").merge(y_frame, on=["object_key"], how="left", suffixes=("_x", "_y"))
        else:
            merged = x_frame.merge(y_frame, on=["object_key"], how="inner", suffixes=("_x", "_y"))
        if merged.empty:
            return pd.DataFrame()
        if size_metric_id:
            size_frame = role_payloads.get(size_metric_id, pd.DataFrame()).copy()
            size_frame = align_metric_frame_to_object_universe(size_frame)
            if not size_frame.empty:
                size_frame = size_frame[["object_key", "object_label", "value", "n", "operation"]].rename(
                    columns={"value": "size_value", "n": "size_n", "operation": "size_operation"}
                )
                merged = merged.merge(size_frame, on=["object_key"], how="left")
        if use_universe:
            merged["x_value"] = fill_missing_metric_values(merged, "x_value", "x_operation")
            merged["y_value"] = fill_missing_metric_values(merged, "y_value", "y_operation")
            if "size_value" in merged.columns:
                merged["size_value"] = fill_missing_metric_values(merged, "size_value", "size_operation")
        merged["object_label"] = (
            merged.get("universe_object_label", pd.Series(dtype="object")).fillna("").astype(str)
            .where(
                merged.get("universe_object_label", pd.Series(dtype="object")).fillna("").astype(str).str.len() > 0,
                merged.get("object_label_x", pd.Series(dtype="object")).fillna("").astype(str),
            )
        )
        merged["object_label"] = (
            merged["object_label"].fillna("").astype(str)
            .where(
                merged["object_label"].fillna("").astype(str).str.len() >= merged.get("object_label_y", pd.Series(dtype="object")).fillna("").astype(str).str.len(),
                merged.get("object_label_y", pd.Series(dtype="object")).fillna("").astype(str),
            )
        )
        if not use_universe:
            merged["object_label"] = (
            merged.get("object_label_x", pd.Series(dtype="object")).fillna("")
            .astype(str)
            .where(merged.get("object_label_x", pd.Series(dtype="object")).fillna("").astype(str).str.len() >= merged.get("object_label_y", pd.Series(dtype="object")).fillna("").astype(str).str.len(),
                   merged.get("object_label_y", pd.Series(dtype="object")).fillna("").astype(str))
            )
        merged["n"] = (
            pd.to_numeric(merged.get("x_n"), errors="coerce")
            .fillna(pd.to_numeric(merged.get("y_n"), errors="coerce"))
            .fillna(pd.to_numeric(merged.get("size_n"), errors="coerce"))
            .fillna(0)
        )
        if "size_value" in merged.columns:
            size_series = pd.to_numeric(merged["size_value"], errors="coerce")
        else:
            size_series = pd.Series(np.nan, index=merged.index, dtype="float64")
        merged["size_value"] = size_series.fillna(pd.to_numeric(merged["n"], errors="coerce")).fillna(1.0)
        merged["group"] = merged["object_label"]
        merged["x_metric_name"] = _safe_text(candidate.get("x_metric_name"))
        merged["y_metric_name"] = _safe_text(candidate.get("y_metric_name"))
        merged["size_metric_name"] = _safe_text(candidate.get("size_metric_name"))
        merged["source_table_set"] = ";".join(str(value) for value in (candidate.get("source_table_set") or []) if str(value).strip())
        merged["join_context"] = _safe_text(candidate.get("join_context"))
        x_missing = pd.to_numeric(merged.get("x_value"), errors="coerce").isna()
        y_missing = pd.to_numeric(merged.get("y_value"), errors="coerce").isna()
        merged["plot_status"] = np.where(~x_missing & ~y_missing, "plottable", "missing_coordinates")
        merged["missing_coordinate_reason"] = np.select(
            [x_missing & y_missing, x_missing, y_missing],
            ["missing_x_and_y", "missing_x", "missing_y"],
            default="",
        )
        if use_universe:
            return merged.copy()
        return merged.loc[merged["plot_status"] == "plottable"].copy()

    route_render_candidates: list[dict[str, Any]] = []
    for candidate in route_candidates:
        candidate_frame = frame_from_route_candidate(candidate)
        if candidate_frame.empty or int(candidate_frame["object_key"].nunique()) < 3:
            continue
        if "object_index" in candidate_frame.columns:
            candidate_frame = candidate_frame.sort_values("object_index", kind="stable")
        else:
            candidate_frame = candidate_frame.sort_values("size_value", ascending=False, kind="stable")
        route_render_candidates.append(
            {
                "signature": _safe_text(candidate.get("candidate_id")),
                "groups": {str(field): str(field) for field in (list(candidate.get("object_key_fields") or []) or [_safe_text(candidate.get("object_dimension"))]) if str(field).strip()},
                "source_table_set": list(candidate.get("source_table_set") or []),
                "join_context": _safe_text(candidate.get("join_context")),
                "title": _safe_text(candidate.get("object_dimension_name")) or _safe_text(candidate.get("object_dimension")),
                "frame": candidate_frame.reset_index(drop=True),
                "candidate_id": _safe_text(candidate.get("candidate_id")),
                "figure_id": _safe_text(candidate.get("figure_id")),
                "chart_form": _safe_text(candidate.get("chart_form")),
                "quadrant_labels": candidate.get("quadrant_labels"),
                "boundary_labels": candidate.get("boundary_labels"),
            }
        )
    candidates = route_render_candidates
    for index, candidate in enumerate(candidates, start=1):
        frame = candidate["frame"]
        groups = dict(candidate.get("groups") or {})
        title = _safe_text(candidate.get("title")) or _cross_table_chart_title(groups, frame)
        slug = _slug(candidate.get("signature") or f"multi_table_{index}", limit=32)
        figure_id = _safe_text(candidate.get("figure_id"))
        candidate_id = _safe_text(candidate.get("candidate_id"))
        if figure_id:
            png_name = figure_id if figure_id.lower().endswith(".png") else f"{figure_id}.png"
        elif candidate_id:
            png_name = f"{candidate_id}.png"
        else:
            png_name = f"cross_table_{slug}_bubble_{index:02d}.png"
        csv_name = f"{Path(png_name).stem}.csv"
        png_path = visual_dir / png_name
        csv_path = visual_dir / csv_name
        chart_form = _safe_text(candidate.get("chart_form") or "quadrant_bubble")
        quadrant_labels = candidate.get("quadrant_labels") if isinstance(candidate.get("quadrant_labels"), dict) else {}
        if not quadrant_labels or not all(_safe_text(quadrant_labels.get(key)) for key in ["top_right", "top_left", "bottom_left", "bottom_right"]):
            raise ValueError(f"route candidate `{candidate.get('candidate_id')}` missing CLI-generated quadrant_labels.")
        quadrant_labels = {
            "top_right": _safe_text(quadrant_labels.get("top_right")),
            "top_left": _safe_text(quadrant_labels.get("top_left")),
            "bottom_left": _safe_text(quadrant_labels.get("bottom_left")),
            "bottom_right": _safe_text(quadrant_labels.get("bottom_right")),
        }
        raw_boundary_labels = candidate.get("boundary_labels")
        if isinstance(raw_boundary_labels, dict):
            boundary_label_values = list(raw_boundary_labels.values())
        else:
            boundary_label_values = list(raw_boundary_labels or [])
        boundary_labels = [str(item).strip() for item in boundary_label_values if str(item).strip()]
        x_numeric = pd.to_numeric(frame["x_value"], errors="coerce")
        y_numeric = pd.to_numeric(frame["y_value"], errors="coerce")
        if x_numeric.dropna().empty or y_numeric.dropna().empty:
            x_mid = 0.0
            y_mid = 0.0
        else:
            x_mid = float(np.nanmedian(x_numeric.to_numpy(dtype=float)))
            y_mid = float(np.nanmedian(y_numeric.to_numpy(dtype=float)))

        def quadrant_for_values(x_value: float, y_value: float) -> str:
            if y_value >= y_mid and x_value >= x_mid:
                return quadrant_labels["top_right"]
            if y_value >= y_mid and x_value < x_mid:
                return quadrant_labels["top_left"]
            if y_value < y_mid and x_value < x_mid:
                return quadrant_labels["bottom_left"]
            return quadrant_labels["bottom_right"]

        def boundary_for_values(x_value: float, y_value: float) -> str:
            if not boundary_labels:
                return ""
            x_span = max(float(np.nanmax(x_numeric) - np.nanmin(x_numeric)), 1.0)
            y_span = max(float(np.nanmax(y_numeric) - np.nanmin(y_numeric)), 1.0)
            near_x = abs(x_value - x_mid) <= x_span * 0.05
            near_y = abs(y_value - y_mid) <= y_span * 0.05
            return boundary_labels[0] if near_x or near_y else ""

        frame = frame.copy().reset_index(drop=True)
        if "object_index" in frame.columns:
            frame["object_index"] = pd.to_numeric(frame["object_index"], errors="coerce")
        frame["_point_id"] = [
            f"B{int(row['object_index']):02d}" if "object_index" in frame.columns and pd.notna(row.get("object_index")) else f"B{point_index + 1:02d}"
            for point_index, (_, row) in enumerate(frame.iterrows())
        ]
        frame["_quadrant"] = [
            "未定位对象" if str(row.get("plot_status") or "").strip() != "plottable" else quadrant_for_values(float(_safe_float(row.get("x_value")) or 0.0), float(_safe_float(row.get("y_value")) or 0.0))
            for _, row in frame.iterrows()
        ]
        frame["_boundary_label"] = [
            "" if str(row.get("plot_status") or "").strip() != "plottable" else boundary_for_values(float(_safe_float(row.get("x_value")) or 0.0), float(_safe_float(row.get("y_value")) or 0.0))
            for _, row in frame.iterrows()
        ]
        plot_frame = frame.loc[frame["plot_status"] == "plottable"].copy()
        if plot_frame.empty:
            plot_frame = frame.copy()

        export_rows = []
        for point_index, row in frame.iterrows():
            point_id = _safe_text(row.get("_point_id")) or f"B{point_index + 1:02d}"
            x_value = _safe_float(row.get("x_value"))
            y_value = _safe_float(row.get("y_value"))
            size_value = _safe_float(row.get("size_value"))
            x_float = float(x_value or 0.0)
            y_float = float(y_value or 0.0)
            export_rows.append(
                {
                    "图中序号": point_id,
                    "对象": _safe_text(row.get("group")),
                    "对象维度": title,
                    "x_metric_name": _safe_text(row.get("x_metric_name")),
                    "y_metric_name": _safe_text(row.get("y_metric_name")),
                    "size_metric_name": _safe_text(row.get("size_metric_name")),
                    "x_value": x_value,
                    "y_value": y_value,
                    "size_value": size_value,
                    "象限": _safe_text(row.get("_quadrant")) or "未定位对象",
                    "边界标签": _safe_text(row.get("_boundary_label")),
                    "n": int(_safe_float(row.get("n")) or 0),
                    "source_table_set": ";".join(str(value) for value in (candidate.get("source_table_set") or []) if str(value).strip()),
                    "join_context": _safe_text(candidate.get("join_context")),
                    "group_fields": ";".join(groups.keys()),
                    "chart_form": chart_form,
                    "missing_detail_reason": _safe_text(row.get("missing_detail_reason")),
                    "plot_status": _safe_text(row.get("plot_status")),
                    "missing_coordinate_reason": _safe_text(row.get("missing_coordinate_reason")),
                }
            )
        _write_csv(
            csv_path,
            export_rows,
            [
                "图中序号",
                "对象",
                "对象维度",
                "x_metric_name",
                "y_metric_name",
                "size_metric_name",
                "x_value",
                "y_value",
                "size_value",
                "象限",
                "边界标签",
                "n",
                "source_table_set",
                "join_context",
                "group_fields",
                "chart_form",
                "missing_detail_reason",
                "plot_status",
                "missing_coordinate_reason",
            ],
        )
        sizes = np.clip(pd.to_numeric(plot_frame["size_value"], errors="coerce").fillna(1.0).to_numpy(dtype=float), a_min=1.0, a_max=None)
        x_values = pd.to_numeric(plot_frame["x_value"], errors="coerce").to_numpy(dtype=float)
        y_values = pd.to_numeric(plot_frame["y_value"], errors="coerce").to_numpy(dtype=float)
        if np.isnan(x_values).all() or np.isnan(y_values).all():
            x_min = y_min = 0.0
            x_max = y_max = 1.0
        else:
            x_min, x_max = float(np.nanmin(x_values)), float(np.nanmax(x_values))
            y_min, y_max = float(np.nanmin(y_values)), float(np.nanmax(y_values))
        x_pad = (x_max - x_min) * 0.04 if x_max > x_min else 1.0
        y_pad = (y_max - y_min) * 0.04 if y_max > y_min else 1.0
        muted_color = style["colors"][4] if len(style.get("colors") or []) > 4 else style["text"]

        def annotate_points(axis: Any, subset: pd.DataFrame) -> None:
            for local_index, (_, row) in enumerate(subset.iterrows()):
                offset_x = 7 if local_index % 2 == 0 else -18
                offset_y = 7 if local_index % 3 else -12
                axis.annotate(
                    _safe_text(row.get("_point_id")) or f"B{local_index + 1:02d}",
                    (float(row.get("x_value") or 0.0), float(row.get("y_value") or 0.0)),
                    textcoords="offset points",
                    xytext=(offset_x, offset_y),
                    fontsize=6.5 if len(subset) > 45 else 8,
                    color=style["text"],
                    arrowprops={"arrowstyle": "-", "color": style["grid"], "linewidth": 0.4, "alpha": 0.65},
                )

        if len(plot_frame) > 120:
            fig, axes = plt.subplots(2, 2, figsize=(14.2, 10.2), sharex=True, sharey=True)
            quadrant_order = [
                (quadrant_labels["top_left"], axes[0][0]),
                (quadrant_labels["top_right"], axes[0][1]),
                (quadrant_labels["bottom_left"], axes[1][0]),
                (quadrant_labels["bottom_right"], axes[1][1]),
            ]
            for quadrant_name, axis in quadrant_order:
                subset = plot_frame.loc[plot_frame["_quadrant"] == quadrant_name].copy()
                subset_sizes = np.clip(pd.to_numeric(subset.get("size_value", pd.Series(dtype="float64")), errors="coerce").fillna(1.0).to_numpy(dtype=float), a_min=1.0, a_max=None)
                if not subset.empty:
                    axis.scatter(
                        pd.to_numeric(subset["x_value"], errors="coerce"),
                        pd.to_numeric(subset["y_value"], errors="coerce"),
                        s=np.sqrt(subset_sizes) * 16,
                        c=np.arange(len(subset)),
                        cmap="Blues",
                        alpha=0.78,
                        edgecolors=style["colors"][1],
                        linewidths=0.85,
                    )
                    annotate_points(axis, subset)
                axis.set_title(f"{quadrant_name} ({len(subset)})", fontsize=10, color=muted_color)
                axis.set_xlabel(_safe_text(frame.iloc[0].get("x_metric_name")))
                axis.set_ylabel(_safe_text(frame.iloc[0].get("y_metric_name")))
                axis.grid(color=style["grid"], alpha=0.45)
                axis.axvline(x_mid, color=style["colors"][1], linestyle="--", linewidth=0.9)
                axis.axhline(y_mid, color=style["colors"][1], linestyle="--", linewidth=0.9)
        else:
            fig, ax = plt.subplots(figsize=(10.2, 6.1))
            scatter = ax.scatter(
                x_values,
                y_values,
                s=np.sqrt(sizes) * 18,
                c=np.arange(len(frame)),
                cmap="Blues",
                alpha=0.78,
                edgecolors=style["colors"][1],
                linewidths=0.9,
            )
            annotate_points(ax, plot_frame)
            ax.set_xlabel(_safe_text(frame.iloc[0].get("x_metric_name")))
            ax.set_ylabel(_safe_text(frame.iloc[0].get("y_metric_name")))
            ax.grid(color=style["grid"], alpha=0.5)
            ax.axvline(x_mid, color=style["colors"][1], linestyle="--", linewidth=1.1)
            ax.axhline(y_mid, color=style["colors"][1], linestyle="--", linewidth=1.1)
            ax.text(x_max - x_pad, y_max - y_pad, quadrant_labels["top_right"], ha="right", va="top", fontsize=8, color=muted_color)
            ax.text(x_min + x_pad, y_max - y_pad, quadrant_labels["top_left"], ha="left", va="top", fontsize=8, color=muted_color)
            ax.text(x_min + x_pad, y_min + y_pad, quadrant_labels["bottom_left"], ha="left", va="bottom", fontsize=8, color=muted_color)
            ax.text(x_max - x_pad, y_min + y_pad, quadrant_labels["bottom_right"], ha="right", va="bottom", fontsize=8, color=muted_color)
            fig.colorbar(scatter, ax=ax, fraction=0.03, pad=0.03)
        fig.suptitle(title)
        fig.tight_layout()
        fig.savefig(png_path, dpi=180, bbox_inches="tight")
        plt.close(fig)
        relative_png = png_path.relative_to(workspace).as_posix()
        relative_csv = csv_path.relative_to(workspace).as_posix()
        image_assets.append(
            {
                "name": png_name,
                "relative_path": relative_png,
                "absolute_path": str(png_path.resolve()),
                "title": title,
                "purpose": "Cross-table quadrant bubble rendered from the CLI visual route contract.",
                "type": "png",
                "bytes": int(png_path.stat().st_size),
                "figure_id": png_name,
                "chart_type": "quadrant_bubble",
                "data_source_files": [csv_name],
                "metric_source_kind": "cross_table_metric",
                "metric_ids": [
                    _safe_text(frame.iloc[0].get("x_metric_name")),
                    _safe_text(frame.iloc[0].get("y_metric_name")),
                    _safe_text(frame.iloc[0].get("size_metric_name")),
                ],
                "object_scope": "cross_table_group",
                "business_priority": max(70, 86 - index * 3),
                "reader_tier": "main_report" if index <= 2 else "appendix",
                "render_origin": "cross_table_metric_seed",
                "chart_family": "quadrant_bubble",
                "source_row_count": int(frame.shape[0]),
                "plottable_row_count": int(plot_frame.shape[0]),
                "unplottable_row_count": int(max(0, frame.shape[0] - plot_frame.shape[0])),
                "object_universe_count": int(object_universe_frame.shape[0]) if not object_universe_frame.empty else int(frame.shape[0]),
                "figure_group_id": f"{slug}::quadrant_bubble",
                "coverage_explanation": (
                    f"图源 CSV 覆盖 {int(frame.shape[0])} 个对象；"
                    f"其中 {int(plot_frame.shape[0])} 个坐标可绘，"
                    f"{int(max(0, frame.shape[0] - plot_frame.shape[0]))} 个保留在映射表并标注缺坐标原因。"
                ),
                "quadrant_labels": quadrant_labels,
                "boundary_labels": boundary_labels,
                "source_table_set": list(candidate.get("source_table_set") or []),
                "join_context": _safe_text(candidate.get("join_context")),
                "render_metadata": {
                    "name": png_name,
                    "relative_path": relative_png,
                    "title": title,
                    "purpose": "Cross-table quadrant bubble rendered from the CLI visual route contract.",
                    "chart_type": "quadrant_bubble",
                    "data_source_files": [csv_name],
                    "source_row_count": int(frame.shape[0]),
                    "plottable_row_count": int(plot_frame.shape[0]),
                    "unplottable_row_count": int(max(0, frame.shape[0] - plot_frame.shape[0])),
                    "object_universe_count": int(object_universe_frame.shape[0]) if not object_universe_frame.empty else int(frame.shape[0]),
                    "figure_group_id": f"{slug}::quadrant_bubble",
                    "quadrant_labels": quadrant_labels,
                    "boundary_labels": boundary_labels,
                },
                "insight_input": {
                    "chart_subject": title,
                    "segment_names": [str(value) for value in frame["group"].head(6).tolist()],
                    "metric_names": [
                        _safe_text(frame.iloc[0].get("x_metric_name")),
                        _safe_text(frame.iloc[0].get("y_metric_name")),
                        _safe_text(frame.iloc[0].get("size_metric_name")),
                    ],
                    "top_signals": [
                        "Cross-table grouped objects are compared through a CLI-routed quadrant bubble chart.",
                        _safe_text(candidate.get("join_context")),
                    ],
                    "comparison_points": [
                        f"{_safe_text(row.get('group'))} / x {float(row.get('x_value') or 0.0):.2f} / y {float(row.get('y_value') or 0.0):.2f} / size {float(row.get('size_value') or 0.0):.2f}"
                        for _, row in frame.head(6).iterrows()
                    ],
                    "outliers_or_extremes": [],
                    "evidence_numbers": [
                        f"{_safe_text(row.get('group'))} / x {float(row.get('x_value') or 0.0):.2f} / y {float(row.get('y_value') or 0.0):.2f} / size {float(row.get('size_value') or 0.0):.2f}"
                        for _, row in frame.head(6).iterrows()
                    ],
                    "chart_type": "quadrant_bubble",
                    "section_anchor": f"cross_table::{slug}",
                    "proxy_disclaimer_required": False,
                    "denominator_basis": "group_level",
                    "unit_basis": "mixed_metric_bubble",
                    "time_basis": "current_period",
                    "metric_semantic_status": "valid",
                    "claim_strength": "direct",
                    "allowed_reader_claim": "This cross-table bubble chart may support grouped comparison and operating priority claims.",
                    "cannot_say": ["Do not treat one bubble as causal proof without the underlying join context."],
                    "proxy_direction": "not_proxy",
                },
                "interpretation_notes": [
                    "Cross-table grouped objects are compared through a CLI-routed quadrant bubble chart.",
                    _safe_text(candidate.get("join_context")),
                ],
            }
        )
        csv_assets.append(
            {
                "name": csv_name,
                "relative_path": relative_csv,
                "absolute_path": str(csv_path.resolve()),
                "title": f"{title} data",
                "purpose": "Data source for the CLI-routed cross-table quadrant bubble.",
                "type": "csv",
                "bytes": int(csv_path.stat().st_size),
                "source_row_count": int(frame.shape[0]),
                "plottable_row_count": int(plot_frame.shape[0]),
                "unplottable_row_count": int(max(0, frame.shape[0] - plot_frame.shape[0])),
                "object_universe_count": int(object_universe_frame.shape[0]) if not object_universe_frame.empty else int(frame.shape[0]),
                "figure_group_id": f"{slug}::quadrant_bubble",
            }
        )
    payload = {
        "asset_dir": str(visual_dir.resolve()),
        "image_count": len(image_assets),
        "csv_count": len(csv_assets),
        "image_assets": image_assets,
        "csv_assets": csv_assets,
        "recommended_figure_slots": [item["relative_path"] for item in image_assets[:4]],
        "recommended_main_report_figures": [item["relative_path"] for item in image_assets if item.get("reader_tier") == "main_report"],
        "recommended_appendix_figures": [item["relative_path"] for item in image_assets if item.get("reader_tier") == "appendix"],
        "seed_source": "custom_metrics_dataset" if single_table_mode else "cross_table_metric_values",
        "business_profile": business_profile,
    }
    _write_json(workspace / "source_visual_assets_index.json", payload)
    return payload
