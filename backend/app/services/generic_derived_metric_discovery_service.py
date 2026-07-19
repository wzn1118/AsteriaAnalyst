from __future__ import annotations

import ast
import json
import math
import re
from pathlib import Path
from typing import Any

import pandas as pd


DISCOVERY_MD_NAME = "generic_derived_metric_discovery.md"
DISCOVERY_JSON_NAME = "generic_derived_metric_discovery.json"
CANDIDATES_CSV_NAME = "generic_derived_metric_candidates.csv"
VALUES_CSV_NAME = "generic_derived_metric_values.csv"
DIAGNOSTICS_JSON_NAME = "generic_derived_metric_execution_diagnostics.json"
OBJECT_UNIVERSE_JSON_NAME = "generic_object_universe.json"
OBJECT_UNIVERSE_CSV_NAME = "generic_object_universe.csv"

_SAFE_FORMULA_FAMILIES = {
    "ratio",
    "rate",
    "share",
    "conversion",
    "efficiency",
    "density",
    "value",
    "quality",
    "risk",
    "difference",
    "gap",
    "sum",
    "mean",
    "average",
    "index",
    "normalized",
    "scale_normalized",
    "contribution_share",
    "relative_gap",
    "percent_change",
    "inverse",
    "per_unit",
    "z_score",
    "standardized",
    "percentile_rank",
    "rank_percentile",
    "composite_score",
    "weighted_score",
    "time_delta",
    "period_delta",
    "delta_over_time",
}


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _normalize(value: Any) -> str:
    return "".join(ch for ch in _safe_text(value).lower() if ch.isalnum() or "\u4e00" <= ch <= "\u9fff")


def _looks_like_id_key(value: Any) -> bool:
    token = _normalize(value)
    return any(marker in token for marker in ("id", "code", "编号", "编码", "代码", "统一", "信用"))


def _looks_like_time_key(value: Any) -> bool:
    token = _normalize(value)
    return any(marker in token for marker in ("年度", "年份", "年", "year", "date", "日期", "time", "period"))


def _looks_like_label_key(value: Any) -> bool:
    token = _normalize(value)
    if any(marker in token for marker in ("简介", "描述", "说明", "description", "remark", "memo")):
        return False
    return any(marker in token for marker in ("名称", "姓名", "name", "title", "label"))


def _semantic_object_identity(groups: dict[str, Any], fallback_group: str) -> tuple[str, str]:
    id_value = ""
    label_value = ""
    time_value = ""
    for key, value in groups.items():
        text = _safe_text(value)
        if not text:
            continue
        if not id_value and _looks_like_id_key(key):
            id_value = text
        elif not label_value and _looks_like_label_key(key):
            label_value = text
        elif not time_value and _looks_like_time_key(key):
            time_value = text
    object_key_parts = [id_value or label_value or _safe_text(fallback_group)]
    if time_value:
        object_key_parts.append(time_value)
    object_key = " | ".join(part for part in object_key_parts if part)
    object_label = label_value or _safe_text(fallback_group) or object_key
    if time_value and time_value not in object_label:
        object_label = f"{object_label} | {time_value}"
    return object_key, object_label


def _slug(value: Any, *, fallback: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "_", _safe_text(value).lower()).strip("_")
    return text or fallback


def _safe_float(value: Any) -> float | None:
    try:
        numeric = float(value)
    except Exception:
        return None
    if math.isnan(numeric) or math.isinf(numeric):
        return None
    return numeric


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must contain a JSON object.")
    return payload


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists() or not path.is_file():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except Exception:
        return pd.read_csv(path, encoding="utf-8")


def _parse_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [_safe_text(item) for item in value if _safe_text(item)]
    if isinstance(value, tuple):
        return [_safe_text(item) for item in value if _safe_text(item)]
    text = _safe_text(value)
    if not text:
        return []
    if ";" in text:
        return [_safe_text(item) for item in text.split(";") if _safe_text(item)]
    if "," in text:
        return [_safe_text(item) for item in text.split(",") if _safe_text(item)]
    try:
        parsed = ast.literal_eval(text)
    except Exception:
        parsed = None
    if isinstance(parsed, (list, tuple, set)):
        return [_safe_text(item) for item in parsed if _safe_text(item)]
    return [text]


def _resolve_column(frame: pd.DataFrame, value: Any) -> str | None:
    text = _safe_text(value)
    if not text:
        return None
    if text in frame.columns:
        return text
    normalized = _normalize(text)
    for column in frame.columns.astype(str):
        if _normalize(column) == normalized:
            return str(column)
    return None


def _numeric(frame: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(frame[column], errors="coerce")


def _candidate_metric_name(candidate: dict[str, Any]) -> str:
    return _safe_text(
        candidate.get("指标中文名")
        or candidate.get("metric_name")
        or candidate.get("metric_name_cn")
        or candidate.get("name")
        or candidate.get("metric_id")
    )


def _explicit_candidate_metric_name(candidate: dict[str, Any]) -> str:
    return _safe_text(
        candidate.get("指标中文名")
        or candidate.get("metric_name_cn")
        or candidate.get("metric_name")
        or candidate.get("name")
    )


def _is_placeholder_metric_name(name: str, metric_id: str, formula_family: str) -> bool:
    text = _safe_text(name)
    normalized = _normalize(text)
    metric_id_normalized = _normalize(metric_id)
    if not text:
        return True
    if not re.search(r"[\u4e00-\u9fff]", text):
        return True
    if metric_id_normalized and normalized == metric_id_normalized and re.search(r"[a-zA-Z_]", metric_id):
        return True
    lowered = text.lower()
    placeholder_tokens = {
        "metric",
        "ratio_metric",
        "derived_metric",
        "derivedmetric",
        "kpi",
        "指标",
        "派生指标",
        "比率指标",
        "效率指标",
        "风险指标",
        "综合指标",
        "指标一",
        "指标二",
        "指标1",
        "指标2",
    }
    if lowered in placeholder_tokens or normalized in {_normalize(item) for item in placeholder_tokens}:
        return True
    if formula_family and normalized == _normalize(formula_family):
        return True
    if re.search(r"^[a-zA-Z0-9_]+$", text):
        return True
    if any(operator in text for operator in ("/", "+", "*", "÷", "=")):
        return True
    return False


def _candidate_metric_id(candidate: dict[str, Any], index: int) -> str:
    return _slug(candidate.get("metric_id") or candidate.get("name") or _candidate_metric_name(candidate), fallback=f"derived_metric_{index:02d}")


def _formula_family(candidate: dict[str, Any]) -> str:
    family = _safe_text(
        candidate.get("formula_family")
        or candidate.get("operation")
        or candidate.get("metric_type")
        or candidate.get("metric_role")
    ).lower()
    formula = _safe_text(candidate.get("formula")).lower()
    if family in _SAFE_FORMULA_FAMILIES:
        return family
    if "z_score" in formula or "z-score" in formula or "标准分" in formula:
        return "z_score"
    if "percentile" in formula or "分位" in formula or "rank" in formula:
        return "percentile_rank"
    if "relative_gap" in formula or "percent_change" in formula or "变化率" in formula or "差异率" in formula:
        return "relative_gap"
    if "inverse" in formula or "倒数" in formula:
        return "inverse"
    if "composite" in formula or "weighted" in formula or "综合分" in formula or "加权" in formula:
        return "composite_score"
    if "contribution" in formula or "贡献占比" in formula or "贡献份额" in formula:
        return "contribution_share"
    if "time_delta" in formula or "period_delta" in formula or "环比" in formula or "同比" in formula or "变化" in formula:
        return "time_delta"
    if "/" in formula or "ratio" in formula or "rate" in formula:
        return "ratio"
    if "-" in formula or "difference" in formula or "gap" in formula:
        return "difference"
    if "share" in formula or "占比" in formula:
        return "share"
    if "mean" in formula or "平均" in formula:
        return "mean"
    if "sum" in formula or "合计" in formula:
        return "sum"
    return family if family else "ratio"


def _time_column(candidate: dict[str, Any]) -> str:
    return _safe_text(candidate.get("time_column") or candidate.get("time_field") or candidate.get("period_column"))


def _object_column(candidate: dict[str, Any]) -> str:
    return _safe_text(
        candidate.get("object_column")
        or candidate.get("object_key_field")
        or candidate.get("group_column")
        or candidate.get("dimension_column")
    )


def _source_fields(candidate: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for key in (
        "source_fields",
        "source_columns",
        "fields",
        "columns",
        "numerator_columns",
        "denominator_columns",
    ):
        values.extend(_parse_list(candidate.get(key)))
    for key in ("numerator_column", "denominator_column", "value_column", "base_column"):
        text = _safe_text(candidate.get(key))
        if text:
            values.append(text)
    return list(dict.fromkeys(values))


def _source_metrics(candidate: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for key in (
        "source_metrics",
        "source_metric_ids",
        "metric_ids",
        "source_fields",
        "numerator_metric_id",
        "denominator_metric_id",
        "value_metric_id",
        "base_metric_id",
    ):
        values.extend(_parse_list(candidate.get(key)))
    return list(dict.fromkeys(values))


def _has_explicit_source_metrics(candidate: dict[str, Any]) -> bool:
    for key in (
        "source_metrics",
        "source_metric_ids",
        "metric_ids",
        "numerator_metric_id",
        "denominator_metric_id",
        "value_metric_id",
        "base_metric_id",
    ):
        if _parse_list(candidate.get(key)):
            return True
    return False


def _selected_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = payload.get("metric_candidates")
    if candidates is None:
        candidates = payload.get("derived_metric_candidates") or payload.get("derived_metrics") or []
    return [dict(item) for item in list(candidates or []) if isinstance(item, dict)]


def ensure_generic_derived_metric_discovery_markdown(markdown_path: Path, json_path: Path) -> Path:
    if markdown_path.exists() and markdown_path.is_file():
        return markdown_path
    payload = _read_json(json_path)
    candidates = _selected_candidates(payload)
    rejected = [dict(item) for item in list(payload.get("rejected_candidates") or []) if isinstance(item, dict)]
    field_roles = payload.get("field_roles") if isinstance(payload.get("field_roles"), dict) else {}
    metric_roles = payload.get("metric_role_summary") if isinstance(payload.get("metric_role_summary"), dict) else {}
    object_grains = [str(item).strip() for item in list(payload.get("object_grains") or []) if str(item).strip()]

    lines: list[str] = [
        "# Generic Derived Metric Discovery",
        "",
        f"- version: `{str(payload.get('version') or '')}`",
        f"- source: `{str(payload.get('source') or '')}`",
        f"- selected_candidate_count: `{len(candidates)}`",
        f"- rejected_candidate_count: `{len(rejected)}`",
        "",
    ]
    if field_roles:
        lines.extend(["## Field Roles", ""])
        for key, value in field_roles.items():
            text = str(value).strip()
            if text:
                lines.append(f"- `{key}`: {text}")
        lines.append("")
    if metric_roles:
        lines.extend(["## Metric Role Summary", ""])
        for key, value in metric_roles.items():
            if isinstance(value, list):
                text = ", ".join(str(item).strip() for item in value if str(item).strip())
            else:
                text = str(value).strip()
            if text:
                lines.append(f"- `{key}`: {text}")
        lines.append("")
    if object_grains:
        lines.extend(["## Object Grains", ""])
        for grain in object_grains:
            lines.append(f"- {grain}")
        lines.append("")
    if candidates:
        lines.extend(["## Selected Candidates", ""])
        for index, candidate in enumerate(candidates, 1):
            metric_id = _candidate_metric_id(candidate, index)
            metric_name = _candidate_metric_name(candidate)
            formula = _safe_text(candidate.get("formula"))
            grain = _safe_text(candidate.get("object_grain"))
            role = _safe_text(candidate.get("metric_role"))
            meaning = _safe_text(candidate.get("business_meaning"))
            diagnostic_use = _safe_text(candidate.get("diagnostic_use"))
            why_selected = _safe_text(candidate.get("why_selected"))
            lines.extend(
                [
                    f"### {index}. {metric_name}",
                    "",
                    f"- `metric_id`: `{metric_id}`",
                    f"- `formula`: `{formula}`",
                    f"- `object_grain`: `{grain}`",
                    f"- `metric_role`: `{role}`",
                    f"- `business_meaning`: {meaning}",
                    f"- `diagnostic_use`: {diagnostic_use or '-'}",
                    f"- `why_selected`: {why_selected}",
                    "",
                ]
            )
    if rejected:
        lines.extend(["## Rejected Candidates", ""])
        for index, candidate in enumerate(rejected, 1):
            metric_name = _candidate_metric_name(candidate) or _safe_text(candidate.get("metric_id")) or f"candidate_{index:02d}"
            why_rejected = _safe_text(candidate.get("why_rejected")) or "No rejection reason provided."
            lines.append(f"- {metric_name}: {why_rejected}")
        lines.append("")
    markdown_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    return markdown_path


def validate_generic_derived_metric_discovery(markdown_path: Path, json_path: Path) -> dict[str, Any]:
    if not markdown_path.exists() or not markdown_path.is_file():
        raise FileNotFoundError(f"Missing {markdown_path.name}")
    payload = _read_json(json_path)
    if str(payload.get("version") or "") not in {
        "generic_derived_metric_discovery_v1",
        "generic_derived_metric_discovery_v2",
    }:
        raise ValueError("generic_derived_metric_discovery.json must use version generic_derived_metric_discovery_v1 or v2.")
    source = str(payload.get("source") or "").lower()
    if "backend" in source or "deterministic" in source:
        raise ValueError("generic_derived_metric_discovery must be produced by runtime CLI, not backend synthesis.")
    version = str(payload.get("version") or "")
    candidates = _selected_candidates(payload)
    if not isinstance(payload.get("rejected_candidates", []), list):
        raise ValueError("generic_derived_metric_discovery rejected_candidates must be a list.")
    required_text_fields = [
        "formula",
        "object_grain",
        "metric_role",
        "unit",
        "directionality",
        "business_meaning",
        "recommended_visual_use",
        "why_selected",
    ]
    if version == "generic_derived_metric_discovery_v2":
        required_text_fields.append("diagnostic_use")
    for index, candidate in enumerate(candidates, 1):
        metric_id = _candidate_metric_id(candidate, index)
        formula_family = _formula_family(candidate)
        if not metric_id:
            raise ValueError(f"derived metric candidate {index} missing metric_id.")
        metric_name = _candidate_metric_name(candidate)
        explicit_metric_name = _explicit_candidate_metric_name(candidate)
        if not metric_name:
            raise ValueError(f"derived metric candidate {index} missing 指标中文名/metric_name.")
        if version == "generic_derived_metric_discovery_v2":
            if not explicit_metric_name:
                raise ValueError(f"derived metric candidate `{metric_id}` must provide an explicit intelligent Chinese metric name; backend metric_id fallback is forbidden.")
            if _is_placeholder_metric_name(explicit_metric_name, metric_id, formula_family):
                raise ValueError(f"derived metric candidate `{metric_id}` uses a placeholder or formula-like metric name `{explicit_metric_name}`; v2 requires data-semantic Chinese naming.")
        missing = [key for key in required_text_fields if not _safe_text(candidate.get(key))]
        if missing:
            raise ValueError(f"derived metric candidate `{metric_id}` missing: {', '.join(missing)}")
        if not _source_fields(candidate) and not _source_metrics(candidate):
            raise ValueError(f"derived metric candidate `{metric_id}` has no source_fields or source_metrics.")
        if version == "generic_derived_metric_discovery_v2" and _has_explicit_source_metrics(candidate):
            if not _safe_text(candidate.get("source_table_set")):
                raise ValueError(f"cross-table derived metric candidate `{metric_id}` missing source_table_set.")
            if not _safe_text(candidate.get("join_context")):
                raise ValueError(f"cross-table derived metric candidate `{metric_id}` missing join_context.")
        family = formula_family
        if family not in _SAFE_FORMULA_FAMILIES:
            raise ValueError(f"derived metric candidate `{metric_id}` uses unsupported formula_family `{family}`.")
        # Time-delta feasibility depends on the executed grain and available
        # group metadata. Treat a missing time key as an execution-level skip so
        # one bad exploratory candidate does not block all other derived metrics.
        if family in {"time_delta", "period_delta", "delta_over_time"} and not _time_column(candidate):
            candidate.setdefault(
                "why_rejected",
                "time-delta candidate lacks a concrete time_column/time_field at the selected object grain; backend will skip this candidate and continue executing the remaining derived metrics.",
            )
    return payload


def _detect_object_dimensions(frame: pd.DataFrame) -> list[str]:
    if frame.empty:
        return []
    object_like: list[str] = []
    for column in frame.columns.astype(str):
        series = frame[column]
        if pd.api.types.is_numeric_dtype(series):
            continue
        unique = int(series.nunique(dropna=True))
        if 2 <= unique <= max(50, int(len(frame) * 0.8)):
            object_like.append(str(column))
    return object_like[:12]


def _single_table_object_universe_count(frame: pd.DataFrame) -> int:
    object_columns = _detect_object_dimensions(frame)
    if not object_columns:
        return int(frame.shape[0])
    primary_object = object_columns[0]
    try:
        return int(frame[primary_object].nunique(dropna=True))
    except Exception:
        return int(frame.shape[0])


def _numeric_stats(series: pd.Series) -> dict[str, Any]:
    numeric = pd.to_numeric(series, errors="coerce")
    valid = numeric.dropna()
    total_n = int(numeric.shape[0])
    valid_n = int(valid.shape[0])
    stats: dict[str, Any] = {
        "total_n": total_n,
        "valid_n": valid_n,
        "null_n": int(total_n - valid_n),
        "coverage_ratio": float(valid_n / total_n) if total_n else 0.0,
        "mean": "",
        "median": "",
        "min": "",
        "max": "",
        "p05": "",
        "p95": "",
        "outlier_iqr_count": 0,
    }
    if valid.empty:
        return stats
    q1 = float(valid.quantile(0.25))
    q3 = float(valid.quantile(0.75))
    iqr = q3 - q1
    if iqr > 0:
        outliers = valid[(valid < q1 - 1.5 * iqr) | (valid > q3 + 1.5 * iqr)]
        stats["outlier_iqr_count"] = int(outliers.shape[0])
    stats.update(
        {
            "mean": float(valid.mean()),
            "median": float(valid.median()),
            "min": float(valid.min()),
            "max": float(valid.max()),
            "p05": float(valid.quantile(0.05)),
            "p95": float(valid.quantile(0.95)),
        }
    )
    return stats


def _denominator_diagnostics(denominator: pd.Series | None) -> dict[str, Any]:
    if denominator is None:
        return {
            "denominator_n": 0,
            "denominator_zero_count": 0,
            "denominator_nonzero_ratio": "",
            "denominator_null_count": 0,
        }
    numeric = pd.to_numeric(denominator, errors="coerce")
    valid = numeric.dropna()
    denominator_n = int(numeric.shape[0])
    zero_count = int((valid == 0).sum())
    nonzero_count = int((valid != 0).sum())
    return {
        "denominator_n": denominator_n,
        "denominator_zero_count": zero_count,
        "denominator_nonzero_ratio": float(nonzero_count / int(valid.shape[0])) if int(valid.shape[0]) else 0.0,
        "denominator_null_count": int(denominator_n - int(valid.shape[0])),
    }


def _min_max_normalize(series: pd.Series, *, higher_is_better: bool = True) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    valid = numeric.dropna()
    if valid.empty:
        return numeric
    span = float(valid.max() - valid.min())
    if not span:
        normalized = pd.Series(0.5, index=numeric.index, dtype="float64")
    else:
        normalized = (numeric - float(valid.min())) / span
    return normalized if higher_is_better else 1 - normalized


def _candidate_weights(candidate: dict[str, Any], columns: list[str]) -> list[float]:
    raw_weights = candidate.get("weights")
    if isinstance(raw_weights, dict):
        weights = [_safe_float(raw_weights.get(column)) for column in columns]
    else:
        weights = [_safe_float(item) for item in _parse_list(raw_weights)]
    weights = [float(value) for value in weights if value is not None]
    if len(weights) != len(columns):
        return [1.0 / len(columns)] * len(columns) if columns else []
    total = sum(abs(value) for value in weights)
    if not total:
        return [1.0 / len(columns)] * len(columns) if columns else []
    return [value / total for value in weights]


def _column_directionality(candidate: dict[str, Any], column: str) -> bool:
    direction_map = candidate.get("source_directionality")
    if isinstance(direction_map, dict):
        text = _safe_text(direction_map.get(column)).lower()
        if text:
            return text not in {"lower_is_better", "negative", "risk", "cost"}
    return _safe_text(candidate.get("directionality")).lower() not in {"lower_is_better", "negative", "risk", "cost"}


def _execute_series(frame: pd.DataFrame, candidate: dict[str, Any]) -> tuple[pd.Series, list[str], str, dict[str, Any]]:
    family = _formula_family(candidate)
    if family not in _SAFE_FORMULA_FAMILIES:
        raise ValueError(f"unsupported safe formula family: {family}")
    fields = [_resolve_column(frame, value) for value in _source_fields(candidate)]
    columns = [column for column in fields if column]
    columns = list(dict.fromkeys(columns))
    if not columns:
        raise ValueError("no source fields resolved")

    numerator_col = _resolve_column(frame, candidate.get("numerator_column"))
    denominator_col = _resolve_column(frame, candidate.get("denominator_column"))
    value_col = _resolve_column(frame, candidate.get("value_column") or candidate.get("base_column"))
    if not numerator_col and columns:
        numerator_col = columns[0]
    if not denominator_col and len(columns) >= 2:
        denominator_col = columns[1]
    if not value_col and columns:
        value_col = columns[0]

    metadata: dict[str, Any] = {
        "formula_family": family,
        "numerator_field": numerator_col or "",
        "denominator_field": denominator_col or "",
        "value_field": value_col or "",
    }

    if family in {"share", "contribution_share"} and numerator_col and not denominator_col:
        numerator = _numeric(frame, numerator_col)
        denominator_value = float(numerator.dropna().sum() or 0)
        if not denominator_value:
            raise ValueError("share derived metric denominator sum is zero")
        series = numerator / denominator_value
        metadata.update(_denominator_diagnostics(pd.Series([denominator_value] * len(frame), index=frame.index)))
        metadata["denominator_field"] = f"sum({numerator_col})"
        return series, [numerator_col], f"{numerator_col} / sum({numerator_col})", metadata
    if family in {"ratio", "rate", "share", "conversion", "efficiency", "density", "value", "quality", "risk"}:
        if not numerator_col or not denominator_col:
            raise ValueError("ratio-like derived metric requires two numeric source fields")
        numerator = _numeric(frame, numerator_col)
        denominator = _numeric(frame, denominator_col)
        series = numerator / denominator.where(denominator != 0)
        metadata.update(_denominator_diagnostics(denominator))
        return series, [numerator_col, denominator_col], f"{numerator_col} / {denominator_col}", metadata
    if family in {"relative_gap", "percent_change"}:
        if not numerator_col or not denominator_col:
            raise ValueError("relative-gap derived metric requires two numeric source fields")
        numerator = _numeric(frame, numerator_col)
        denominator = _numeric(frame, denominator_col)
        series = (numerator - denominator) / denominator.where(denominator != 0)
        metadata.update(_denominator_diagnostics(denominator))
        return series, [numerator_col, denominator_col], f"({numerator_col} - {denominator_col}) / {denominator_col}", metadata
    if family in {"difference", "gap"}:
        if not numerator_col or not denominator_col:
            raise ValueError("difference derived metric requires two numeric source fields")
        return _numeric(frame, numerator_col) - _numeric(frame, denominator_col), [numerator_col, denominator_col], f"{numerator_col} - {denominator_col}", metadata
    if family in {"inverse", "per_unit"}:
        denominator_col = denominator_col or value_col
        if not denominator_col:
            raise ValueError("inverse derived metric requires a numeric denominator/value field")
        denominator = _numeric(frame, denominator_col)
        metadata.update(_denominator_diagnostics(denominator))
        return 1 / denominator.where(denominator != 0), [denominator_col], f"1 / {denominator_col}", metadata
    if family in {"sum", "index"}:
        numeric_frame = pd.DataFrame({column: _numeric(frame, column) for column in columns})
        return numeric_frame.sum(axis=1, min_count=1), columns, " + ".join(columns), metadata
    if family in {"mean", "average"}:
        numeric_frame = pd.DataFrame({column: _numeric(frame, column) for column in columns})
        return numeric_frame.mean(axis=1, skipna=True), columns, f"mean({', '.join(columns)})", metadata
    if family in {"normalized", "scale_normalized"}:
        if not value_col:
            raise ValueError("normalized derived metric requires a numeric value field")
        values = _numeric(frame, value_col)
        denominator = float(values.dropna().mean() or 0)
        if not denominator:
            raise ValueError("normalized denominator is zero")
        metadata.update(_denominator_diagnostics(pd.Series([denominator] * len(frame), index=frame.index)))
        metadata["denominator_field"] = f"mean({value_col})"
        return values / denominator, [value_col], f"{value_col} / mean({value_col})", metadata
    if family in {"z_score", "standardized"}:
        if not value_col:
            raise ValueError("z-score derived metric requires a numeric value field")
        values = _numeric(frame, value_col)
        std = float(values.dropna().std() or 0)
        if not std:
            raise ValueError("z-score denominator std is zero")
        metadata.update(_denominator_diagnostics(pd.Series([std] * len(frame), index=frame.index)))
        metadata["denominator_field"] = f"std({value_col})"
        return (values - float(values.dropna().mean())) / std, [value_col], f"({value_col} - mean({value_col})) / std({value_col})", metadata
    if family in {"percentile_rank", "rank_percentile"}:
        if not value_col:
            raise ValueError("percentile rank derived metric requires a numeric value field")
        values = _numeric(frame, value_col)
        ascending = _safe_text(candidate.get("directionality")).lower() in {"lower_is_better", "negative", "risk", "cost"}
        return values.rank(pct=True, ascending=ascending), [value_col], f"percentile_rank({value_col})", metadata
    if family in {"composite_score", "weighted_score"}:
        if len(columns) < 2:
            raise ValueError("composite score requires at least two numeric source fields")
        weights = _candidate_weights(candidate, columns)
        parts = []
        for column in columns:
            parts.append(_min_max_normalize(_numeric(frame, column), higher_is_better=_column_directionality(candidate, column)))
        normalized_frame = pd.concat(parts, axis=1)
        series = sum(normalized_frame.iloc[:, idx] * weights[idx] for idx in range(len(weights)))
        metadata["weights"] = dict(zip(columns, weights))
        return series, columns, "weighted_score(" + ", ".join(columns) + ")", metadata
    if family in {"time_delta", "period_delta", "delta_over_time"}:
        if not value_col:
            raise ValueError("time delta derived metric requires a numeric value field")
        time_col = _resolve_column(frame, _time_column(candidate))
        if not time_col:
            raise ValueError("time delta derived metric requires a resolved time column")
        object_col = _resolve_column(frame, _object_column(candidate))
        working = frame[[column for column in [object_col, time_col, value_col] if column]].copy()
        working["_value"] = _numeric(frame, value_col)
        working["_time"] = pd.to_datetime(working[time_col], errors="coerce")
        working = working.sort_values([column for column in [object_col, "_time"] if column])
        if object_col:
            series = working.groupby(object_col, dropna=False)["_value"].diff()
        else:
            series = working["_value"].diff()
        series = series.reindex(frame.index)
        metadata["time_field"] = time_col
        metadata["object_field"] = object_col or ""
        return series, [column for column in [value_col, time_col, object_col] if column], f"delta({value_col}) over {time_col}", metadata
    raise ValueError(f"unsupported safe formula family: {family}")


def _single_table_has_derivable_metrics(frame: pd.DataFrame) -> bool:
    numeric_columns = [str(column) for column in frame.columns.astype(str) if pd.api.types.is_numeric_dtype(frame[column])]
    return bool(_detect_object_dimensions(frame) and len(numeric_columns) >= 2)


def _minimum_single_table_requirements(frame: pd.DataFrame) -> tuple[int, int]:
    if frame.empty or not _detect_object_dimensions(frame):
        return 0, 0
    numeric_count = sum(1 for column in frame.columns.astype(str) if pd.api.types.is_numeric_dtype(frame[column]))
    if numeric_count < 2:
        return 0, 0
    has_time = any(
        bool(re.search(r"(date|time|year|month|day|日期|时间|年度|月份)", str(column), flags=re.I))
        for column in frame.columns.astype(str)
    )
    if numeric_count >= 6:
        metric_min, family_min = 16, 6
    elif numeric_count >= 4:
        metric_min, family_min = 12, 5
    elif numeric_count >= 3:
        metric_min, family_min = 8, 4
    else:
        metric_min, family_min = 6, 3
    if has_time:
        metric_min = min(metric_min + 2, 18)
        family_min = min(family_min + 1, 7)
    return metric_min, family_min


def _completed_family_count(diagnostic_rows: list[dict[str, Any]]) -> int:
    return len(
        {
            _safe_text(row.get("formula_family"))
            for row in diagnostic_rows
            if _safe_text(row.get("status")) == "completed" and _safe_text(row.get("formula_family"))
        }
    )


def _write_single_table_outputs(
    workspace: Path,
    payload: dict[str, Any],
    frame: pd.DataFrame,
    *,
    allow_partial: bool = False,
) -> dict[str, Any]:
    candidates = _selected_candidates(payload)
    value_rows: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []
    diagnostic_rows: list[dict[str, Any]] = []
    enriched = frame.copy()

    for index, candidate in enumerate(candidates, 1):
        metric_id = _candidate_metric_id(candidate, index)
        metric_name = _candidate_metric_name(candidate)
        status = "skipped"
        reason = ""
        resolved_columns: list[str] = []
        formula = _safe_text(candidate.get("formula"))
        executed_formula_text = ""
        execution_metadata: dict[str, Any] = {"formula_family": _formula_family(candidate)}
        stats: dict[str, Any] = {}
        try:
            series, resolved_columns, executed_formula, execution_metadata = _execute_series(enriched, candidate)
            executed_formula_text = executed_formula
            numeric = pd.to_numeric(series, errors="coerce")
            valid = numeric.dropna()
            stats = _numeric_stats(numeric)
            if valid.empty:
                reason = "derived metric produced no numeric values"
            else:
                enriched[metric_id] = numeric
                status = "completed"
                formula = formula or executed_formula
                value_rows.append(
                    {
                        "metric_id": metric_id,
                        "metric_name": metric_name,
                        "指标中文名": metric_name,
                        "metric_role": _safe_text(candidate.get("metric_role")),
                        "formula": formula,
                        "source_fields": ";".join(resolved_columns),
                        "object_grain": _safe_text(candidate.get("object_grain")),
                        "unit": _safe_text(candidate.get("unit")),
                        "directionality": _safe_text(candidate.get("directionality")),
                        "business_meaning": _safe_text(candidate.get("business_meaning")),
                        "diagnostic_use": _safe_text(candidate.get("diagnostic_use")),
                        "recommended_visual_use": _safe_text(candidate.get("recommended_visual_use")),
                        "why_selected": _safe_text(candidate.get("why_selected")),
                        "valid_n": int(stats.get("valid_n") or 0),
                        "coverage_ratio": stats.get("coverage_ratio", ""),
                        "mean": stats.get("mean", ""),
                        "median": stats.get("median", ""),
                        "min": stats.get("min", ""),
                        "max": stats.get("max", ""),
                        "p05": stats.get("p05", ""),
                        "p95": stats.get("p95", ""),
                        "status": status,
                        "reason": "",
                    }
                )
        except Exception as exc:
            reason = str(exc)
            stats = {}
        candidate_rows.append(
            {
                "metric_id": metric_id,
                "指标中文名": metric_name,
                "formula": formula,
                "source_fields": ";".join(resolved_columns or _source_fields(candidate)),
                "object_grain": _safe_text(candidate.get("object_grain")),
                "metric_role": _safe_text(candidate.get("metric_role")),
                "unit": _safe_text(candidate.get("unit")),
                "directionality": _safe_text(candidate.get("directionality")),
                "business_meaning": _safe_text(candidate.get("business_meaning")),
                "diagnostic_use": _safe_text(candidate.get("diagnostic_use")),
                "recommended_visual_use": _safe_text(candidate.get("recommended_visual_use")),
                "why_selected": _safe_text(candidate.get("why_selected")),
                "why_rejected": _safe_text(candidate.get("why_rejected")),
                "status": status,
                "reason": reason,
            }
        )
        diagnostic_rows.append(
            {
                "metric_id": metric_id,
                "metric_name": metric_name,
                "指标中文名": metric_name,
                "status": status,
                "reason": reason,
                "formula": formula,
                "formula_family": execution_metadata.get("formula_family") or _formula_family(candidate),
                "executed_formula": executed_formula_text,
                "source_fields": ";".join(resolved_columns or _source_fields(candidate)),
                "source_metrics": "",
                "object_grain": _safe_text(candidate.get("object_grain")),
                "unit": _safe_text(candidate.get("unit")),
                "directionality": _safe_text(candidate.get("directionality")),
                "recommended_visual_use": _safe_text(candidate.get("recommended_visual_use")),
                "business_meaning": _safe_text(candidate.get("business_meaning")),
                "diagnostic_use": _safe_text(candidate.get("diagnostic_use")),
                "denominator_field": execution_metadata.get("denominator_field", ""),
                "denominator_zero_count": execution_metadata.get("denominator_zero_count", 0),
                "denominator_nonzero_ratio": execution_metadata.get("denominator_nonzero_ratio", ""),
                "denominator_null_count": execution_metadata.get("denominator_null_count", 0),
                "total_n": stats.get("total_n", int(frame.shape[0])),
                "valid_n": stats.get("valid_n", 0),
                "coverage_ratio": stats.get("coverage_ratio", 0.0),
                "null_n": stats.get("null_n", ""),
                "min": stats.get("min", ""),
                "max": stats.get("max", ""),
                "p05": stats.get("p05", ""),
                "p95": stats.get("p95", ""),
                "outlier_iqr_count": stats.get("outlier_iqr_count", 0),
                "object_count": int(frame[_detect_object_dimensions(frame)[0]].nunique(dropna=True)) if _detect_object_dimensions(frame) else "",
                "overlap_count": "",
                "overlap_ratio": "",
            }
        )

    pd.DataFrame(candidate_rows).to_csv(workspace / CANDIDATES_CSV_NAME, index=False, encoding="utf-8-sig")
    pd.DataFrame(value_rows).to_csv(workspace / VALUES_CSV_NAME, index=False, encoding="utf-8-sig")
    min_completed_metrics, min_completed_families = _minimum_single_table_requirements(frame)
    completed_family_count = _completed_family_count(diagnostic_rows)
    diagnostics_payload = {
        "version": "generic_derived_metric_execution_diagnostics_v1",
        "mode": "single_table",
        "source": "backend_safe_execution_audit",
        "execution_status": "partial" if allow_partial else "strict",
        "partial_results_allowed": bool(allow_partial),
        "candidate_count": len(candidates),
        "completed_metric_count": len(value_rows),
        "completed_formula_family_count": completed_family_count,
        "minimum_required_completed_metric_count": min_completed_metrics,
        "minimum_required_formula_family_count": min_completed_families,
        "object_universe_count": _single_table_object_universe_count(frame),
        "diagnostics": diagnostic_rows,
    }
    (workspace / DIAGNOSTICS_JSON_NAME).write_text(
        json.dumps(diagnostics_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if not enriched.empty:
        enriched.to_csv(workspace / "custom_metrics_dataset.csv", index=False, encoding="utf-8-sig")

    if _single_table_has_derivable_metrics(frame) and not value_rows and not allow_partial:
        raise ValueError("generic_derived_metric_discovery found no executable derived metrics even though object dimensions and numeric metrics exist.")
    if min_completed_metrics and len(value_rows) < min_completed_metrics and not allow_partial:
        raise ValueError(
            "generic_derived_metric_discovery under-generated executable derived metrics: "
            f"{len(value_rows)}/{min_completed_metrics}. CLI must mine a broader derived metric pool."
        )
    if min_completed_families and completed_family_count < min_completed_families and not allow_partial:
        raise ValueError(
            "generic_derived_metric_discovery lacks formula-family diversity: "
            f"{completed_family_count}/{min_completed_families} completed families."
        )
    return {
        "candidate_count": len(candidates),
        "completed_metric_count": len(value_rows),
        "values_path": str((workspace / VALUES_CSV_NAME).resolve()),
        "candidates_path": str((workspace / CANDIDATES_CSV_NAME).resolve()),
        "diagnostics_path": str((workspace / DIAGNOSTICS_JSON_NAME).resolve()),
        "metrics": value_rows,
    }


def _detail_rows_frame(row: dict[str, Any]) -> pd.DataFrame:
    raw = _safe_text(row.get("detail_rows_json"))
    if not raw:
        return pd.DataFrame()
    try:
        detail_rows = json.loads(raw)
    except Exception:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    for item in list(detail_rows or []):
        if not isinstance(item, dict):
            continue
        groups = item.get("groups") if isinstance(item.get("groups"), dict) else {}
        object_key, object_label = _semantic_object_identity(groups, _safe_text(item.get("group")))
        value = _safe_float(item.get("value"))
        if value is None:
            continue
        rows.append(
            {
                "object_key": object_key,
                "object_label": object_label or object_key,
                "groups": groups,
                "value": value,
                "n": int(_safe_float(item.get("n")) or 0),
            }
        )
    return pd.DataFrame(rows)


def _cross_table_metric_maps(workspace: Path) -> tuple[list[dict[str, Any]], dict[str, pd.DataFrame]]:
    values = _read_csv(workspace / "cross_table_metric_values.csv")
    rows = [row for row in values.to_dict(orient="records") if _safe_text(row.get("status")) == "completed"]
    index: dict[str, pd.DataFrame] = {}
    normalized_aliases: dict[str, str] = {}
    for row in rows:
        metric_id = _safe_text(row.get("metric_id"))
        metric_name = _safe_text(row.get("metric_name") or metric_id)
        detail_frame = _detail_rows_frame(row)
        if detail_frame.empty:
            continue
        detail_frame["metric_id"] = metric_id
        detail_frame["metric_name"] = metric_name
        detail_frame["table_id"] = _safe_text(row.get("table_id"))
        detail_frame["formula"] = _safe_text(row.get("formula"))
        index[metric_id] = detail_frame
        normalized_aliases[_normalize(metric_id)] = metric_id
        normalized_aliases[_normalize(metric_name)] = metric_id
    for row in rows:
        row["_normalized_aliases"] = normalized_aliases
    return rows, index


def _object_universe_frame(workspace: Path) -> pd.DataFrame:
    path = workspace / OBJECT_UNIVERSE_CSV_NAME
    if not path.exists():
        return pd.DataFrame()
    try:
        frame = pd.read_csv(path, encoding="utf-8-sig")
    except Exception:
        try:
            frame = pd.read_csv(path, encoding="utf-8")
        except Exception:
            return pd.DataFrame()
    if "object_key" not in frame.columns:
        return pd.DataFrame()
    frame["object_key"] = frame["object_key"].astype(str)
    if "object_label" not in frame.columns:
        frame["object_label"] = frame["object_key"]
    return frame.drop_duplicates(subset=["object_key"]).reset_index(drop=True)


def _metric_missing_as_zero(row: dict[str, Any] | None) -> bool:
    if not row:
        return False
    operation = _safe_text(row.get("operation")).lower()
    metric_name = _normalize(" ".join([row.get("metric_id", ""), row.get("metric_name", ""), row.get("formula", "")]))
    if operation in {"", "row_count", "count_rows", "count", "nunique", "count_distinct", "sum"}:
        return True
    return any(marker in metric_name for marker in ("数量", "次数", "金额", "收入", "支出", "count", "amount", "income", "spend", "expense"))


def _resolve_metric_id(metric_rows: list[dict[str, Any]], metric_maps: dict[str, pd.DataFrame], value: Any) -> str | None:
    text = _safe_text(value)
    if text in metric_maps:
        return text
    normalized = _normalize(text)
    aliases = metric_rows[0].get("_normalized_aliases") if metric_rows else {}
    if isinstance(aliases, dict) and normalized in aliases:
        return str(aliases[normalized])
    return None


def _candidate_metric_refs(candidate: dict[str, Any], metric_rows: list[dict[str, Any]], metric_maps: dict[str, pd.DataFrame]) -> list[str]:
    refs = _source_metrics(candidate)
    resolved: list[str] = []
    for ref in refs:
        metric_id = _resolve_metric_id(metric_rows, metric_maps, ref)
        if metric_id and metric_id not in resolved:
            resolved.append(metric_id)
    return resolved


def _compute_cross_table_detail(
    candidate: dict[str, Any],
    metric_rows: list[dict[str, Any]],
    metric_maps: dict[str, pd.DataFrame],
    object_universe: pd.DataFrame | None = None,
) -> tuple[list[dict[str, Any]], list[str], str, dict[str, Any]]:
    family = _formula_family(candidate)
    if family not in _SAFE_FORMULA_FAMILIES:
        raise ValueError(f"unsupported safe formula family: {family}")
    metric_ids = _candidate_metric_refs(candidate, metric_rows, metric_maps)
    if len(metric_ids) < 1:
        raise ValueError("no source metrics resolved")
    metric_row_by_id = {_safe_text(row.get("metric_id")): row for row in metric_rows}
    frames = []
    for idx, metric_id in enumerate(metric_ids[:4], 1):
        frame = metric_maps.get(metric_id, pd.DataFrame()).copy()
        if frame.empty:
            continue
        frame = frame.drop_duplicates(subset=["object_key"], keep="first")
        frames.append(
            frame[["object_key", "object_label", "groups", "value", "n"]].rename(
                columns={"value": f"value_{idx}", "n": f"n_{idx}"}
            )
        )
    if not frames:
        raise ValueError("source metrics have no grouped detail rows")

    universe = object_universe if object_universe is not None else pd.DataFrame()
    use_universe = False
    if not universe.empty:
        universe_keys = set(universe["object_key"].dropna().astype(str).tolist())
        for frame in frames:
            frame_keys = set(frame["object_key"].dropna().astype(str).tolist())
            if frame_keys and len(frame_keys & universe_keys) / max(len(frame_keys), 1) >= 0.5:
                use_universe = True
                break

    if use_universe:
        merged = universe[["object_key", "object_label"]].copy()
        if "missing_detail_reason" in universe.columns:
            merged["missing_detail_reason"] = universe["missing_detail_reason"]
        merged["groups"] = [{} for _ in range(len(merged))]
    else:
        merged = frames[0][["object_key", "object_label", "groups"]].copy()

    for idx, frame in enumerate(frames, 1):
        value_columns = ["object_key", f"value_{idx}", f"n_{idx}", "object_label", "groups"]
        merged = merged.merge(frame[value_columns], on=["object_key"], how="left" if use_universe else "outer", suffixes=("", f"_r{idx}"))
        label_column = f"object_label_r{idx}"
        groups_column = f"groups_r{idx}"
        if label_column in merged.columns:
            merged["object_label"] = merged["object_label"].where(merged["object_label"].astype(str).str.strip().ne(""), merged[label_column])
            merged["object_label"] = merged["object_label"].fillna(merged[label_column])
            merged = merged.drop(columns=[label_column])
        if groups_column in merged.columns:
            merged["groups"] = merged["groups"].where(
                merged["groups"].apply(lambda value: isinstance(value, dict) and bool(value)),
                merged[groups_column],
            )
            merged = merged.drop(columns=[groups_column])
    if merged.empty:
        raise ValueError("source metrics do not share a stable object grain")

    missing_flags: list[pd.Series] = []
    for idx, metric_id in enumerate(metric_ids[: len(frames)], 1):
        value_column = f"value_{idx}"
        if value_column not in merged.columns:
            continue
        missing = pd.to_numeric(merged[value_column], errors="coerce").isna()
        missing_flags.append(missing.rename(metric_id))
        if _metric_missing_as_zero(metric_row_by_id.get(metric_id)):
            merged[value_column] = pd.to_numeric(merged[value_column], errors="coerce").fillna(0.0)

    value_1 = pd.to_numeric(merged["value_1"], errors="coerce")
    value_2 = pd.to_numeric(merged["value_2"], errors="coerce") if "value_2" in merged.columns else None
    source_object_counts = [
        int(frame.get("object_key", pd.Series(dtype="object")).astype(str).nunique())
        for frame in frames
        if not frame.empty
    ]
    overlap_count = int(
        pd.concat(
            [pd.to_numeric(merged.get(f"value_{idx}"), errors="coerce").notna() for idx in range(1, len(frames) + 1)],
            axis=1,
        )
        .all(axis=1)
        .sum()
    )
    object_universe_count = int(universe["object_key"].nunique()) if use_universe and "object_key" in universe.columns else int(merged["object_key"].astype(str).nunique())
    max_source_objects = max(source_object_counts or [overlap_count])
    diagnostics = {
        "formula_family": family,
        "overlap_count": overlap_count,
        "overlap_ratio": float(overlap_count / max_source_objects) if max_source_objects else 0.0,
        "source_object_counts": source_object_counts,
        "object_universe_count": object_universe_count,
        "denominator_metric": metric_ids[1] if len(metric_ids) > 1 else "",
    }
    if family in {"share", "contribution_share"} and value_2 is None:
        denominator_value = float(value_1.dropna().sum() or 0)
        if not denominator_value:
            raise ValueError("share derived metric denominator sum is zero")
        result = value_1 / denominator_value
        executed_formula = f"{metric_ids[0]} / sum({metric_ids[0]})"
        diagnostics.update(_denominator_diagnostics(pd.Series([denominator_value] * len(merged), index=merged.index)))
        diagnostics["denominator_metric"] = f"sum({metric_ids[0]})"
    elif family in {"ratio", "rate", "share", "conversion", "efficiency", "density", "value", "quality", "risk"}:
        if value_2 is None:
            raise ValueError("ratio-like cross-table derived metric requires two source metrics")
        result = value_1 / value_2.where(value_2 != 0)
        executed_formula = f"{metric_ids[0]} / {metric_ids[1]}"
        diagnostics.update(_denominator_diagnostics(value_2))
    elif family in {"relative_gap", "percent_change"}:
        if value_2 is None:
            raise ValueError("relative-gap cross-table derived metric requires two source metrics")
        result = (value_1 - value_2) / value_2.where(value_2 != 0)
        executed_formula = f"({metric_ids[0]} - {metric_ids[1]}) / {metric_ids[1]}"
        diagnostics.update(_denominator_diagnostics(value_2))
    elif family in {"difference", "gap"}:
        if value_2 is None:
            raise ValueError("difference cross-table derived metric requires two source metrics")
        result = value_1 - value_2
        executed_formula = f"{metric_ids[0]} - {metric_ids[1]}"
    elif family in {"sum", "index"}:
        value_cols = [column for column in merged.columns if str(column).startswith("value_")]
        result = merged[value_cols].apply(pd.to_numeric, errors="coerce").sum(axis=1, min_count=1)
        executed_formula = " + ".join(metric_ids[: len(value_cols)])
    elif family in {"mean", "average"}:
        value_cols = [column for column in merged.columns if str(column).startswith("value_")]
        result = merged[value_cols].apply(pd.to_numeric, errors="coerce").mean(axis=1)
        executed_formula = f"mean({', '.join(metric_ids[: len(value_cols)])})"
    elif family in {"normalized", "scale_normalized"}:
        denominator = float(value_1.dropna().mean() or 0)
        if not denominator:
            raise ValueError("normalized denominator is zero")
        result = value_1 / denominator
        executed_formula = f"{metric_ids[0]} / mean({metric_ids[0]})"
        diagnostics.update(_denominator_diagnostics(pd.Series([denominator] * len(merged), index=merged.index)))
        diagnostics["denominator_metric"] = f"mean({metric_ids[0]})"
    elif family in {"inverse", "per_unit"}:
        result = 1 / value_1.where(value_1 != 0)
        executed_formula = f"1 / {metric_ids[0]}"
        diagnostics.update(_denominator_diagnostics(value_1))
        diagnostics["denominator_metric"] = metric_ids[0]
    elif family in {"z_score", "standardized"}:
        std = float(value_1.dropna().std() or 0)
        if not std:
            raise ValueError("z-score denominator std is zero")
        result = (value_1 - float(value_1.dropna().mean())) / std
        executed_formula = f"({metric_ids[0]} - mean({metric_ids[0]})) / std({metric_ids[0]})"
        diagnostics.update(_denominator_diagnostics(pd.Series([std] * len(merged), index=merged.index)))
        diagnostics["denominator_metric"] = f"std({metric_ids[0]})"
    elif family in {"percentile_rank", "rank_percentile"}:
        ascending = _safe_text(candidate.get("directionality")).lower() in {"lower_is_better", "negative", "risk", "cost"}
        result = value_1.rank(pct=True, ascending=ascending)
        executed_formula = f"percentile_rank({metric_ids[0]})"
    elif family in {"composite_score", "weighted_score"}:
        value_cols = [column for column in merged.columns if str(column).startswith("value_")]
        if len(value_cols) < 2:
            raise ValueError("composite cross-table derived metric requires at least two source metrics")
        weights = _candidate_weights(candidate, metric_ids[: len(value_cols)])
        parts = [
            _min_max_normalize(
                pd.to_numeric(merged[column], errors="coerce"),
                higher_is_better=_column_directionality(candidate, metric_ids[idx]),
            )
            for idx, column in enumerate(value_cols[: len(weights)])
        ]
        normalized_frame = pd.concat(parts, axis=1)
        result = sum(normalized_frame.iloc[:, idx] * weights[idx] for idx in range(len(weights)))
        executed_formula = "weighted_score(" + ", ".join(metric_ids[: len(weights)]) + ")"
        diagnostics["weights"] = dict(zip(metric_ids[: len(weights)], weights))
    elif family in {"time_delta", "period_delta", "delta_over_time"}:
        time_key = _time_column(candidate)
        if not time_key:
            raise ValueError("time delta cross-table derived metric requires time_column/time_field")
        group_records = []
        for _, row in merged.iterrows():
            groups = row.get("groups") if isinstance(row.get("groups"), dict) else {}
            if time_key not in groups:
                continue
            object_groups = {key: value for key, value in groups.items() if key != time_key}
            group_records.append(
                {
                    "_object": " | ".join(f"{key}={value}" for key, value in object_groups.items()) or _safe_text(row.get("object_label")),
                    "_time": pd.to_datetime(groups.get(time_key), errors="coerce"),
                    "_value": row.get("value_1"),
                    "_row_index": row.name,
                }
            )
        group_frame = pd.DataFrame(group_records)
        if group_frame.empty:
            raise ValueError("time delta source metrics do not contain the requested time key in groups")
        group_frame = group_frame.sort_values(["_object", "_time"])
        group_frame["_result"] = group_frame.groupby("_object", dropna=False)["_value"].diff()
        result = pd.Series(index=merged.index, dtype="float64")
        for _, row in group_frame.iterrows():
            result.loc[row["_row_index"]] = row["_result"]
        executed_formula = f"delta({metric_ids[0]}) over {time_key}"
        diagnostics["time_key"] = time_key
    else:
        raise ValueError(f"unsupported safe formula family: {family}")

    detail_rows: list[dict[str, Any]] = []
    for idx, row in merged.assign(_derived_value=result).iterrows():
        value = _safe_float(row.get("_derived_value"))
        if value is None:
            continue
        groups = row.get("groups") if isinstance(row.get("groups"), dict) else {}
        missing_metrics = [
            metric_id
            for metric_index, metric_id in enumerate(metric_ids[: len(frames)], 1)
            if pd.isna(row.get(f"value_{metric_index}"))
        ]
        detail_rows.append(
            {
                "group": _safe_text(row.get("object_label") or row.get("object_key")),
                "groups": groups or {"object_key": row.get("object_key"), "object_label": row.get("object_label")},
                "value": value,
                "n": int(_safe_float(row.get("n_1")) or 0),
                "missing_source_metrics": missing_metrics,
                "missing_detail_reason": _safe_text(row.get("missing_detail_reason")),
            }
        )
    if not detail_rows:
        raise ValueError("derived metric produced no grouped values")
    diagnostics["covered_count"] = len(detail_rows)
    diagnostics["missing_count"] = max(object_universe_count - len(detail_rows), 0)
    diagnostics["coverage_rate"] = float(len(detail_rows) / max(object_universe_count, 1))
    return detail_rows, metric_ids, executed_formula, diagnostics


def _write_cross_table_outputs(workspace: Path, payload: dict[str, Any], *, allow_partial: bool = False) -> dict[str, Any]:
    metric_rows, metric_maps = _cross_table_metric_maps(workspace)
    object_universe = _object_universe_frame(workspace)
    candidates = _selected_candidates(payload)
    value_rows: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []
    diagnostic_rows: list[dict[str, Any]] = []

    for index, candidate in enumerate(candidates, 1):
        metric_id = _candidate_metric_id(candidate, index)
        metric_name = _candidate_metric_name(candidate)
        status = "skipped"
        reason = ""
        resolved_metrics: list[str] = []
        formula = _safe_text(candidate.get("formula"))
        executed_formula_text = ""
        execution_metadata: dict[str, Any] = {"formula_family": _formula_family(candidate)}
        stats: dict[str, Any] = {}
        try:
            detail_rows, resolved_metrics, executed_formula, execution_metadata = _compute_cross_table_detail(
                candidate,
                metric_rows,
                metric_maps,
                object_universe=object_universe,
            )
            executed_formula_text = executed_formula
            status = "completed"
            formula = formula or executed_formula
            values = [_safe_float(row.get("value")) for row in detail_rows]
            numeric_values = [value for value in values if value is not None]
            stats = _numeric_stats(pd.Series(numeric_values, dtype="float64"))
            value_rows.append(
                {
                    "metric_id": metric_id,
                    "metric_name": metric_name,
                    "table_id": ";".join(_parse_list(candidate.get("source_table_set"))),
                    "operation": _formula_family(candidate),
                    "value": "",
                    "detail_rows_json": json.dumps(detail_rows, ensure_ascii=False),
                    "formula": formula,
                    "status": status,
                    "reason": "",
                    "source_metrics": ";".join(resolved_metrics),
                    "source_table_set": ";".join(_parse_list(candidate.get("source_table_set"))),
                    "join_context": _safe_text(candidate.get("join_context")),
                    "object_grain": _safe_text(candidate.get("object_grain")),
                    "metric_role": _safe_text(candidate.get("metric_role")),
                    "unit": _safe_text(candidate.get("unit")),
                    "directionality": _safe_text(candidate.get("directionality")),
                    "business_meaning": _safe_text(candidate.get("business_meaning")),
                    "diagnostic_use": _safe_text(candidate.get("diagnostic_use")),
                    "recommended_visual_use": _safe_text(candidate.get("recommended_visual_use")),
                    "valid_n": int(stats.get("valid_n") or 0),
                    "coverage_ratio": stats.get("coverage_ratio", ""),
                    "mean": stats.get("mean", ""),
                    "median": stats.get("median", ""),
                    "min": stats.get("min", ""),
                    "max": stats.get("max", ""),
                    "p05": stats.get("p05", ""),
                    "p95": stats.get("p95", ""),
                    "overlap_count": execution_metadata.get("overlap_count", ""),
                    "overlap_ratio": execution_metadata.get("overlap_ratio", ""),
                    "object_universe_count": execution_metadata.get("object_universe_count", ""),
                    "covered_count": execution_metadata.get("covered_count", ""),
                    "missing_count": execution_metadata.get("missing_count", ""),
                    "coverage_rate": execution_metadata.get("coverage_rate", ""),
                }
            )
        except Exception as exc:
            reason = str(exc)
            stats = {}
        candidate_rows.append(
            {
                "metric_id": metric_id,
                "指标中文名": metric_name,
                "formula": formula,
                "source_metrics": ";".join(resolved_metrics or _source_metrics(candidate)),
                "source_fields": ";".join(_source_fields(candidate)),
                "object_grain": _safe_text(candidate.get("object_grain")),
                "metric_role": _safe_text(candidate.get("metric_role")),
                "unit": _safe_text(candidate.get("unit")),
                "directionality": _safe_text(candidate.get("directionality")),
                "business_meaning": _safe_text(candidate.get("business_meaning")),
                "diagnostic_use": _safe_text(candidate.get("diagnostic_use")),
                "recommended_visual_use": _safe_text(candidate.get("recommended_visual_use")),
                "why_selected": _safe_text(candidate.get("why_selected")),
                "why_rejected": _safe_text(candidate.get("why_rejected")),
                "source_table_set": ";".join(_parse_list(candidate.get("source_table_set"))),
                "join_context": _safe_text(candidate.get("join_context")),
                "status": status,
                "reason": reason,
            }
        )
        diagnostic_rows.append(
            {
                "metric_id": metric_id,
                "metric_name": metric_name,
                "指标中文名": metric_name,
                "status": status,
                "reason": reason,
                "formula": formula,
                "formula_family": execution_metadata.get("formula_family") or _formula_family(candidate),
                "executed_formula": executed_formula_text,
                "source_fields": ";".join(_source_fields(candidate)),
                "source_metrics": ";".join(resolved_metrics or _source_metrics(candidate)),
                "source_table_set": ";".join(_parse_list(candidate.get("source_table_set"))),
                "join_context": _safe_text(candidate.get("join_context")),
                "object_grain": _safe_text(candidate.get("object_grain")),
                "unit": _safe_text(candidate.get("unit")),
                "directionality": _safe_text(candidate.get("directionality")),
                "recommended_visual_use": _safe_text(candidate.get("recommended_visual_use")),
                "business_meaning": _safe_text(candidate.get("business_meaning")),
                "diagnostic_use": _safe_text(candidate.get("diagnostic_use")),
                "denominator_metric": execution_metadata.get("denominator_metric", ""),
                "denominator_zero_count": execution_metadata.get("denominator_zero_count", 0),
                "denominator_nonzero_ratio": execution_metadata.get("denominator_nonzero_ratio", ""),
                "denominator_null_count": execution_metadata.get("denominator_null_count", 0),
                "total_n": stats.get("total_n", ""),
                "valid_n": stats.get("valid_n", 0),
                "coverage_ratio": stats.get("coverage_ratio", 0.0),
                "null_n": stats.get("null_n", ""),
                "min": stats.get("min", ""),
                "max": stats.get("max", ""),
                "p05": stats.get("p05", ""),
                "p95": stats.get("p95", ""),
                "outlier_iqr_count": stats.get("outlier_iqr_count", 0),
                "overlap_count": execution_metadata.get("overlap_count", ""),
                "overlap_ratio": execution_metadata.get("overlap_ratio", ""),
                "object_universe_count": execution_metadata.get("object_universe_count", ""),
                "covered_count": execution_metadata.get("covered_count", ""),
                "missing_count": execution_metadata.get("missing_count", ""),
                "coverage_rate": execution_metadata.get("coverage_rate", ""),
                "source_object_counts": execution_metadata.get("source_object_counts", []),
            }
        )

    pd.DataFrame(candidate_rows).to_csv(workspace / CANDIDATES_CSV_NAME, index=False, encoding="utf-8-sig")
    pd.DataFrame(value_rows).to_csv(workspace / VALUES_CSV_NAME, index=False, encoding="utf-8-sig")
    min_completed_metrics, min_completed_families = _minimum_cross_table_requirements(metric_maps)
    completed_family_count = _completed_family_count(diagnostic_rows)
    diagnostics_payload = {
        "version": "generic_derived_metric_execution_diagnostics_v1",
        "mode": "cross_table",
        "source": "backend_safe_execution_audit",
        "execution_status": "partial" if allow_partial else "strict",
        "partial_results_allowed": bool(allow_partial),
        "candidate_count": len(candidates),
        "completed_metric_count": len(value_rows),
        "completed_formula_family_count": completed_family_count,
        "minimum_required_completed_metric_count": min_completed_metrics,
        "minimum_required_formula_family_count": min_completed_families,
        "diagnostics": diagnostic_rows,
    }
    (workspace / DIAGNOSTICS_JSON_NAME).write_text(
        json.dumps(diagnostics_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if _cross_table_has_derivable_metrics(metric_maps) and not value_rows and not allow_partial:
        raise ValueError("cross_table_derived_metric_discovery found no executable derived metrics even though aligned object metrics exist.")
    if min_completed_metrics and len(value_rows) < min_completed_metrics and not allow_partial:
        raise ValueError(
            "cross_table_derived_metric_discovery under-generated executable derived metrics: "
            f"{len(value_rows)}/{min_completed_metrics}. CLI must mine a broader cross-table derived metric pool."
        )
    if min_completed_families and completed_family_count < min_completed_families and not allow_partial:
        raise ValueError(
            "cross_table_derived_metric_discovery lacks formula-family diversity: "
            f"{completed_family_count}/{min_completed_families} completed families."
        )
    return {
        "candidate_count": len(candidates),
        "completed_metric_count": len(value_rows),
        "values_path": str((workspace / VALUES_CSV_NAME).resolve()),
        "candidates_path": str((workspace / CANDIDATES_CSV_NAME).resolve()),
        "diagnostics_path": str((workspace / DIAGNOSTICS_JSON_NAME).resolve()),
        "metrics": value_rows,
    }


def _cross_table_has_derivable_metrics(metric_maps: dict[str, pd.DataFrame]) -> bool:
    metric_ids = list(metric_maps.keys())
    for left_idx, left_metric in enumerate(metric_ids):
        left_keys = set(metric_maps[left_metric].get("object_key", pd.Series(dtype="object")).astype(str).tolist())
        if len(left_keys) < 3:
            continue
        for right_metric in metric_ids[left_idx + 1 :]:
            right_keys = set(metric_maps[right_metric].get("object_key", pd.Series(dtype="object")).astype(str).tolist())
            if len(left_keys & right_keys) >= 3:
                return True
    return False


def _minimum_cross_table_requirements(metric_maps: dict[str, pd.DataFrame]) -> tuple[int, int]:
    if not _cross_table_has_derivable_metrics(metric_maps):
        return 0, 0
    metric_count = len(metric_maps)
    if metric_count >= 8:
        return 18, 6
    if metric_count >= 6:
        return 14, 5
    if metric_count >= 4:
        return 10, 4
    return 6, 3


def execute_generic_derived_metric_discovery(
    *,
    workspace_path: str | Path,
    mode: str,
    source_dataset_path: str | Path | None = None,
    allow_partial: bool = False,
) -> dict[str, Any]:
    workspace = Path(workspace_path).expanduser().resolve()
    json_path = workspace / DISCOVERY_JSON_NAME
    md_path = workspace / DISCOVERY_MD_NAME
    payload = validate_generic_derived_metric_discovery(md_path, json_path)
    if mode == "cross_table":
        return _write_cross_table_outputs(workspace, payload, allow_partial=allow_partial)

    source_path = Path(source_dataset_path).expanduser().resolve() if source_dataset_path else workspace / "custom_metrics_dataset.csv"
    if not source_path.exists():
        source_path = workspace / "source_dataset.csv"
    frame = _read_csv(source_path)
    if frame.empty:
        raise ValueError("generic derived metric discovery source dataset is empty or missing.")
    return _write_single_table_outputs(workspace, payload, frame, allow_partial=allow_partial)
