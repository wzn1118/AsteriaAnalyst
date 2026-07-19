from __future__ import annotations

import json
import math
import re
import warnings
from pathlib import Path
from typing import Any

from app.services.codex_historical_localization_service import (
    localize_historical_key,
    localize_historical_record,
    localize_historical_text,
)


def _pd() -> Any:
    import pandas as pd

    return pd


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        number = float(value)
        if math.isnan(number) or math.isinf(number):
            return default
        return number
    except Exception:
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _safe_id(value: Any, *, fallback: str = "item") -> str:
    text = re.sub(r"[^a-zA-Z0-9_\-\u4e00-\u9fff]+", "_", str(value or "").strip()).strip("_")
    return text[:80] or fallback


def _coerce_frame(frame: Any | None = None, *, csv_path: Path | None = None) -> Any:
    pd = _pd()
    if frame is not None and hasattr(frame, "columns"):
        return frame.copy()
    if csv_path and csv_path.exists():
        return pd.read_csv(csv_path, encoding="utf-8-sig")
    return pd.DataFrame()


def _parse_dates_if_likely(series: Any, column_name: str) -> Any | None:
    pd = _pd()
    lower = str(column_name or "").lower()
    date_tokens = ("date", "time", "day", "month", "year", "日期", "时间", "日", "月", "年")
    try:
        if not pd.api.types.is_datetime64_any_dtype(series) and not any(token in lower for token in date_tokens):
            return None
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            return pd.to_datetime(series, errors="coerce")
    except Exception:
        return None


def _label_entry(raw_key: str) -> dict[str, str]:
    return {
        "raw_key": raw_key,
        "localized_label": localize_historical_key(raw_key, fallback=raw_key),
    }


def _metric_value(series: Any, aggregation: str) -> float:
    cleaned = series.dropna()
    if cleaned.empty:
        return 0.0
    if aggregation == "sum":
        return _safe_float(cleaned.sum())
    if aggregation == "median":
        return _safe_float(cleaned.median())
    return _safe_float(cleaned.mean())


def _infer_metric_type(name: str, series: Any) -> str:
    lower = name.lower()
    if any(token in lower for token in ("rate", "ratio", "率", "占比", "转化", "留存", "复购", "完成率")):
        return "rate"
    if any(token in lower for token in ("amount", "revenue", "sales", "gmv", "cost", "price", "金额", "收入", "销售", "费用", "成本", "客单", "毛利")):
        return "amount"
    if any(token in lower for token in ("count", "num", "qty", "orders", "users", "次数", "数量", "人数", "订单", "件数")):
        return "count"
    if any(token in lower for token in ("score", "nps", "rating", "满意", "评分", "得分", "指数")):
        return "score"
    if any(token in lower for token in ("day", "hour", "time", "duration", "天", "小时", "时长")):
        return "duration"
    if not series.empty and series.min() >= 0 and series.max() <= 1:
        return "rate"
    return "numeric"


def _infer_aggregation(name: str, series: Any) -> str:
    metric_type = _infer_metric_type(name, series)
    return "sum" if metric_type in {"amount", "count"} else "mean"


def _numeric_columns(frame: Any) -> list[dict[str, Any]]:
    pd = _pd()
    output: list[dict[str, Any]] = []
    for column in frame.columns:
        name = str(column)
        series = pd.to_numeric(frame[column], errors="coerce")
        non_null = int(series.notna().sum())
        if non_null < max(3, int(len(frame) * 0.35)):
            continue
        original_non_null = int(frame[column].notna().sum()) or 1
        if non_null / original_non_null < 0.65:
            continue
        cleaned = series.dropna()
        if cleaned.nunique(dropna=True) < 2:
            continue
        output.append(
            {
                "raw_key": name,
                "localized_label": localize_historical_key(name, fallback=name),
                "non_null": non_null,
                "unique_count": int(cleaned.nunique(dropna=True)),
                "metric_type": _infer_metric_type(name, cleaned),
                "aggregation": _infer_aggregation(name, cleaned),
                "sum": _safe_float(cleaned.sum()),
                "mean": _safe_float(cleaned.mean()),
                "median": _safe_float(cleaned.median()),
                "min": _safe_float(cleaned.min()),
                "max": _safe_float(cleaned.max()),
                "std": _safe_float(cleaned.std()),
                "q25": _safe_float(cleaned.quantile(0.25)),
                "q75": _safe_float(cleaned.quantile(0.75)),
            }
        )
    return output


def _resolve_context_path(raw_path: Any, *, workspace: Path, context_path: Path | None) -> Path | None:
    text = str(raw_path or "").strip()
    if not text:
        return None
    path = Path(text).expanduser()
    candidates = [path]
    if not path.is_absolute():
        candidates = [workspace / path]
        if context_path is not None:
            candidates.append(context_path.parent / path)
            candidates.append(context_path.parent.parent / path)
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except Exception:
            resolved = candidate
        if resolved.exists():
            return resolved
    return None


def _looks_like_derived_metric(item: dict[str, Any], *, source_hint: str = "") -> bool:
    haystack = " ".join(
        str(value or "").lower()
        for value in [
            source_hint,
            item.get("metric_kind"),
            item.get("metric_type"),
            item.get("type"),
            item.get("source"),
            item.get("formula"),
            item.get("derivation_rule"),
            item.get("status"),
        ]
    )
    return any(token in haystack for token in ("derived", "custom", "formula", "ratio", "composite", "weighted", "派生", "衍生"))


def _normalize_derived_metric(item: dict[str, Any], *, source_hint: str = "") -> dict[str, Any] | None:
    metric_id = str(
        item.get("metric_id")
        or item.get("raw_key")
        or item.get("metric")
        or item.get("metric_name")
        or item.get("name")
        or ""
    ).strip()
    if not metric_id:
        return None
    metric_name = str(item.get("metric_name") or item.get("localized_label") or item.get("name") or metric_id).strip()
    formula = str(item.get("formula") or item.get("derivation_rule") or item.get("calculation") or "").strip()
    source_columns = item.get("source_columns") or item.get("available_fields") or item.get("columns") or []
    if isinstance(source_columns, str):
        source_columns = [part.strip() for part in re.split(r"[;,，、]+", source_columns) if part.strip()]
    if not isinstance(source_columns, list):
        source_columns = []
    row = {
        "raw_key": metric_id,
        "localized_label": localize_historical_key(metric_name, fallback=metric_name),
        "metric_type": str(item.get("metric_type") or item.get("type") or "derived").strip() or "derived",
        "aggregation": str(item.get("aggregation") or "derived").strip() or "derived",
        "metric_kind": "derived_metric",
        "is_derived": True,
        "formula": formula,
        "source_columns": [str(value) for value in source_columns if str(value).strip()][:12],
        "business_meaning": str(item.get("business_meaning") or item.get("business_value") or item.get("purpose") or item.get("description") or "").strip(),
        "derivation_source": source_hint,
        "derivation_status": str(item.get("status") or item.get("execution_status") or "planned").strip() or "planned",
    }
    for key in ("non_null", "valid_n"):
        if item.get(key) not in (None, ""):
            row["non_null"] = _safe_int(item.get(key))
            break
    for key in ("sum", "mean", "median", "min", "max", "std", "q25", "q75"):
        if item.get(key) not in (None, ""):
            row[key] = _safe_float(item.get(key))
    return row


def _collect_derived_metric_rows(value: Any, *, source_hint: str = "") -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if isinstance(value, dict):
        if _looks_like_derived_metric(value, source_hint=source_hint):
            normalized = _normalize_derived_metric(value, source_hint=source_hint)
            if normalized:
                rows.append(normalized)
        for key, nested in value.items():
            key_text = str(key)
            key_lower = key_text.lower()
            if (
                key_text in {"derived_metrics", "analysis_program_derived_metrics", "custom_metrics", "metric_plans", "metrics"}
                or "derived" in key_lower
                or "custom_metric" in key_lower
                or "\u6d3e\u751f" in key_text
                or "\u884d\u751f" in key_text
                or "\u81ea\u5b9a\u4e49" in key_text
            ):
                rows.extend(_collect_derived_metric_rows(nested, source_hint=key_text or source_hint))
            elif isinstance(nested, (dict, list)):
                rows.extend(_collect_derived_metric_rows(nested, source_hint=source_hint))
    elif isinstance(value, list):
        for item in value:
            rows.extend(_collect_derived_metric_rows(item, source_hint=source_hint))
    return rows


def _load_derived_metric_rows_from_path(path: Path, *, source_hint: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists() or not path.is_file():
        return rows
    suffix = path.suffix.lower()
    try:
        if suffix == ".json":
            payload = _read_json(path)
            rows.extend(_collect_derived_metric_rows(payload, source_hint=source_hint or path.name))
        elif suffix == ".csv":
            pd = _pd()
            frame = pd.read_csv(path, encoding="utf-8-sig")
            for item in frame.head(200).to_dict(orient="records"):
                if isinstance(item, dict):
                    normalized = _normalize_derived_metric(item, source_hint=source_hint or path.name)
                    if normalized:
                        rows.append(normalized)
    except Exception:
        return rows
    return rows


def _external_derived_metrics(
    *,
    context_payload: dict[str, Any],
    workspace: Path,
    context_path: Path | None,
) -> list[dict[str, Any]]:
    rows = _collect_derived_metric_rows(context_payload, source_hint="current_report_context")
    candidate_paths: list[Any] = []

    def _walk_paths(value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                key_text = str(key).lower()
                if any(token in key_text for token in ("derived", "custom_metric", "metric_derivation")) and str(item or "").strip():
                    candidate_paths.append(item)
                elif any(token in str(key) for token in ("\u6d3e\u751f", "\u884d\u751f", "\u81ea\u5b9a\u4e49")) and str(item or "").strip():
                    candidate_paths.append(item)
                _walk_paths(item)
        elif isinstance(value, list):
            for item in value:
                _walk_paths(item)

    _walk_paths(context_payload)
    default_candidates = [
        workspace / "derived_metrics_table.csv",
        workspace / "custom_metric_values.csv",
        workspace / "03_custom_metric_execution.json",
        workspace / "metric_derivation_plan.json",
        workspace / "derived_metric_execution_review.json",
    ]
    for raw in candidate_paths:
        path = _resolve_context_path(raw, workspace=workspace, context_path=context_path)
        if path:
            rows.extend(_load_derived_metric_rows_from_path(path, source_hint=path.name))
    for path in default_candidates:
        rows.extend(_load_derived_metric_rows_from_path(path, source_hint=path.name))

    deduped: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = str(row.get("raw_key") or "").strip()
        if not key:
            continue
        previous = deduped.get(key, {})
        deduped[key] = {**previous, **row}
    return list(deduped.values())


def _merge_derived_metrics(metrics: list[dict[str, Any]], derived_metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for item in metrics:
        raw_key = str(item.get("raw_key") or "").strip()
        if raw_key:
            merged[raw_key] = {**item, "metric_kind": item.get("metric_kind") or "direct_metric", "is_derived": bool(item.get("is_derived"))}
    for item in derived_metrics:
        raw_key = str(item.get("raw_key") or "").strip()
        if not raw_key:
            continue
        if raw_key in merged:
            merged[raw_key] = {**merged[raw_key], **item, "is_derived": True, "metric_kind": "derived_metric"}
        else:
            merged[raw_key] = dict(item)
    return list(merged.values())


def _dimension_columns(frame: Any, numeric_names: set[str]) -> list[dict[str, Any]]:
    pd = _pd()
    output: list[dict[str, Any]] = []
    priority_tokens = (
        "category",
        "品类",
        "类目",
        "segment",
        "客群",
        "人群",
        "channel",
        "渠道",
        "platform",
        "平台",
        "region",
        "区域",
        "省",
        "市",
        "brand",
        "品牌",
        "product",
        "商品",
        "sku",
        "campaign",
        "活动",
        "media",
        "媒体",
        "format",
        "业态",
        "customer",
        "store",
        "门店",
        "supplier",
        "供方",
        "vendor",
    )
    for column in frame.columns:
        name = str(column)
        series = frame[column]
        non_null = int(series.notna().sum())
        if non_null < 3:
            continue
        unique_count = int(series.nunique(dropna=True))
        if unique_count < 2 or unique_count > min(80, max(12, int(len(frame) * 0.45))):
            continue
        is_numeric = name in numeric_names
        parsed_date = _parse_dates_if_likely(series, name)
        date_ratio = float(parsed_date.notna().sum()) / max(1, non_null) if parsed_date is not None else 0.0
        if is_numeric and unique_count > 8 and date_ratio < 0.7:
            continue
        priority = 2 if any(token.lower() in name.lower() for token in priority_tokens) else 1
        output.append(
            {
                "raw_key": name,
                "localized_label": localize_historical_key(name, fallback=name),
                "non_null": non_null,
                "unique_count": unique_count,
                "missing_count": int(series.isna().sum()),
                "dimension_type": "date" if date_ratio >= 0.7 else ("numeric_bucket" if is_numeric else "categorical"),
                "priority": priority,
                "top_values": [
                    {
                        "raw_key": str(index),
                        "localized_label": localize_historical_text(index, fallback=str(index)),
                        "count": int(value),
                    }
                    for index, value in series.fillna("缺失").astype(str).value_counts().head(8).items()
                ],
            }
        )
    output.sort(key=lambda item: (int(item.get("priority") or 0), int(item.get("non_null") or 0)), reverse=True)
    return output


def _date_columns(frame: Any) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for column in frame.columns:
        name = str(column)
        parsed = _parse_dates_if_likely(frame[column], name)
        if parsed is None:
            continue
        non_null = int(parsed.notna().sum())
        if non_null < max(5, int(len(frame) * 0.35)):
            continue
        output.append(
            {
                "raw_key": name,
                "localized_label": localize_historical_key(name, fallback=name),
                "non_null": non_null,
                "min": str(parsed.min().date()) if non_null else "",
                "max": str(parsed.max().date()) if non_null else "",
                "month_count": int(parsed.dt.to_period("M").nunique()) if non_null else 0,
            }
        )
    return output[:4]


def _table_profiles(data_frames: dict[str, Any]) -> list[dict[str, Any]]:
    pd = _pd()
    profiles: list[dict[str, Any]] = []
    object_tokens = ("channel", "category", "region", "customer", "product", "sku", "campaign", "store", "supplier")
    for table_id, frame in data_frames.items():
        if frame is None or not hasattr(frame, "columns"):
            continue
        working = frame.copy()
        row_count = int(len(working))
        candidate_keys: list[str] = []
        for column in working.columns:
            series = working[column]
            non_null = int(series.notna().sum())
            if non_null <= 1:
                continue
            unique_count = int(series.nunique(dropna=True))
            if unique_count >= max(2, int(row_count * 0.98)) and non_null >= max(2, int(row_count * 0.95)):
                candidate_keys.append(str(column))
            if len(candidate_keys) >= 6:
                break
        date_ranges: list[dict[str, Any]] = []
        for column in working.columns:
            parsed = _parse_dates_if_likely(working[column], str(column))
            if parsed is None:
                continue
            valid = parsed.dropna()
            if valid.empty:
                continue
            date_ranges.append(
                {
                    "raw_key": str(column),
                    "localized_label": localize_historical_key(column, fallback=str(column)),
                    "min": str(valid.min().date()),
                    "max": str(valid.max().date()),
                }
            )
            if len(date_ranges) >= 3:
                break
        business_objects = [
            {
                "raw_key": str(column),
                "localized_label": localize_historical_key(column, fallback=str(column)),
            }
            for column in working.columns
            if any(token in str(column).lower() for token in object_tokens)
        ][:8]
        profiles.append(
            {
                "table_id": table_id,
                "table_label": localize_historical_text(table_id, fallback=table_id),
                "row_count": row_count,
                "column_count": int(len(working.columns)),
                "candidate_keys": [_label_entry(name) for name in candidate_keys],
                "date_ranges": date_ranges,
                "main_business_objects": business_objects,
            }
        )
    return profiles


def _select_primary_frame(data_frames: dict[str, Any], data_frame: Any | None, csv_path: Path | None) -> tuple[str, Any]:
    if data_frame is not None and hasattr(data_frame, "columns"):
        return "primary_frame", data_frame.copy()
    ranked = []
    for table_id, frame in data_frames.items():
        if frame is not None and hasattr(frame, "columns"):
            ranked.append((int(len(frame)), table_id, frame))
    if ranked:
        ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return str(ranked[0][1]), ranked[0][2].copy()
    return "snapshot", _coerce_frame(csv_path=csv_path)


def _dimension_metric_cube(frame: Any, metrics: list[dict[str, Any]], dimensions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pd = _pd()
    cube: list[dict[str, Any]] = []
    for dimension in dimensions[:10]:
        dim_name = str(dimension.get("raw_key") or "")
        if dim_name not in frame.columns:
            continue
        work = frame.copy()
        work[dim_name] = work[dim_name].fillna("缺失").astype(str)
        for metric in metrics[:12]:
            metric_name = str(metric.get("raw_key") or "")
            if metric_name not in frame.columns:
                continue
            aggregation = str(metric.get("aggregation") or "mean")
            numeric = pd.to_numeric(work[metric_name], errors="coerce")
            work_metric = work.assign(__metric=numeric)
            overall = _metric_value(numeric, aggregation)
            grouped = work_metric.groupby(dim_name, dropna=False)
            rows: list[dict[str, Any]] = []
            for value, group in grouped:
                valid = group["__metric"].dropna()
                n = int(valid.shape[0])
                if n <= 0:
                    continue
                reading = _metric_value(valid, aggregation)
                share = reading / overall if aggregation == "sum" and overall else None
                lift = (reading / overall - 1.0) if overall else 0.0
                rows.append(
                    {
                        "dimension_value_raw": str(value),
                        "dimension_value_label": localize_historical_text(value, fallback=str(value)),
                        "n": n,
                        "value": reading,
                        "share_of_total": round(share, 6) if share is not None else None,
                        "share_semantics": "contribution_share" if share is not None else "not_applicable_for_mean_or_rate",
                        "lift_vs_overall": round(lift, 6),
                    }
                )
            rows.sort(key=lambda item: _safe_float(item.get("value")), reverse=True)
            for rank, row in enumerate(rows, start=1):
                row["rank"] = rank
            if len(rows) >= 2:
                cube.append(
                    {
                        "dimension_raw_key": dim_name,
                        "dimension_localized_label": localize_historical_key(dim_name, fallback=dim_name),
                        "metric_raw_key": metric_name,
                        "metric_localized_label": localize_historical_key(metric_name, fallback=metric_name),
                        "metric_type": metric.get("metric_type"),
                        "aggregation": aggregation,
                        "overall_value": overall,
                        "segment_count": len(rows),
                        "rows": rows[:20],
                    }
                )
    return cube


def _top_bottom_segments(cube: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for item in cube:
        rows = list(item.get("rows") or [])
        if not rows:
            continue
        output.append(
            {
                "dimension_raw_key": item.get("dimension_raw_key"),
                "dimension_localized_label": item.get("dimension_localized_label"),
                "metric_raw_key": item.get("metric_raw_key"),
                "metric_localized_label": item.get("metric_localized_label"),
                "top": rows[:3],
                "bottom": list(reversed(rows[-3:])) if len(rows) > 3 else rows[-1:],
            }
        )
    return output[:60]


def _pairwise_relationships(frame: Any, metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pd = _pd()
    names = [str(item.get("raw_key")) for item in metrics[:16] if str(item.get("raw_key") or "") in frame.columns]
    if len(names) < 2:
        return []
    numeric = frame[names].apply(pd.to_numeric, errors="coerce")
    corr = numeric.corr(method="pearson")
    relationships: list[dict[str, Any]] = []
    for left_index, left in enumerate(names):
        for right in names[left_index + 1 :]:
            value = _safe_float(corr.loc[left, right], default=0.0)
            if not value:
                continue
            relationships.append(
                {
                    "left_raw_key": left,
                    "left_localized_label": localize_historical_key(left, fallback=left),
                    "right_raw_key": right,
                    "right_localized_label": localize_historical_key(right, fallback=right),
                    "correlation": value,
                    "abs_correlation": abs(value),
                    "relationship_type": "positive" if value >= 0 else "negative",
                    "management_hint": (
                        "适合纳入同一张经营看板协同观察。"
                        if abs(value) >= 0.45
                        else "可作为辅助关系观察，不宜单独驱动决策。"
                    ),
                }
            )
    relationships.sort(key=lambda item: _safe_float(item.get("abs_correlation")), reverse=True)
    return relationships[:40]


def _missingness_diagnostics(frame: Any) -> list[dict[str, Any]]:
    if frame is None or not hasattr(frame, "columns") or frame.empty:
        return []
    row_count = int(len(frame))
    diagnostics: list[dict[str, Any]] = []
    for column in frame.columns:
        series = frame[column]
        missing_count = int(series.isna().sum())
        missing_ratio = missing_count / max(1, row_count)
        if missing_count <= 0 and row_count > 0:
            continue
        diagnostics.append(
            {
                "raw_key": str(column),
                "localized_label": localize_historical_key(column, fallback=str(column)),
                "missing_count": missing_count,
                "missing_ratio": round(missing_ratio, 6),
                "non_null_count": int(series.notna().sum()),
                "severity": "high" if missing_ratio >= 0.25 else ("medium" if missing_ratio >= 0.08 else "low"),
                "management_use": (
                    "优先检查该字段是否影响关键判断或分层动作。"
                    if missing_ratio >= 0.08
                    else "作为字段质量背景信息，不单独驱动结论。"
                ),
            }
        )
    diagnostics.sort(key=lambda item: _safe_float(item.get("missing_ratio")), reverse=True)
    return diagnostics[:40]


def _outlier_influence_summary(frame: Any, metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pd = _pd()
    if frame is None or not hasattr(frame, "columns") or frame.empty:
        return []
    output: list[dict[str, Any]] = []
    for metric in metrics[:20]:
        raw_key = str(metric.get("raw_key") or "")
        if raw_key not in frame.columns:
            continue
        values = pd.to_numeric(frame[raw_key], errors="coerce").dropna()
        if len(values) < 8:
            continue
        q1 = values.quantile(0.25)
        q3 = values.quantile(0.75)
        iqr = q3 - q1
        if not iqr:
            continue
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        mask = (values < lower) | (values > upper)
        outlier_count = int(mask.sum())
        if outlier_count <= 0:
            continue
        clean_values = values[~mask]
        full_mean = _safe_float(values.mean())
        clean_mean = _safe_float(clean_values.mean(), full_mean)
        shift_ratio = abs(full_mean - clean_mean) / max(abs(clean_mean), 1e-9)
        output.append(
            {
                "metric_raw_key": raw_key,
                "metric_localized_label": localize_historical_key(raw_key, fallback=raw_key),
                "method": "iqr_1_5",
                "n": int(len(values)),
                "outlier_count": outlier_count,
                "outlier_ratio": round(outlier_count / max(1, len(values)), 6),
                "lower_bound": _safe_float(lower),
                "upper_bound": _safe_float(upper),
                "mean_with_outliers": full_mean,
                "mean_without_outliers": clean_mean,
                "mean_shift_ratio": round(shift_ratio, 6),
                "severity": "high" if shift_ratio >= 0.2 else ("medium" if shift_ratio >= 0.08 else "low"),
                "management_use": "报告解释该指标时需要区分头部异常对象与常规经营水平。",
            }
        )
    output.sort(key=lambda item: (_safe_float(item.get("severity") == "high"), _safe_float(item.get("mean_shift_ratio"))), reverse=True)
    return output[:40]


def _time_trend_slices(frame: Any, metrics: list[dict[str, Any]], dates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pd = _pd()
    if frame is None or not hasattr(frame, "columns") or frame.empty or not dates:
        return []
    date_key = str(dates[0].get("raw_key") or "")
    if date_key not in frame.columns:
        return []
    parsed = _parse_dates_if_likely(frame[date_key], date_key)
    if parsed is None or int(parsed.notna().sum()) < 6:
        return []
    output: list[dict[str, Any]] = []
    base = frame.copy()
    base["__period"] = parsed.dt.to_period("M").astype(str)
    for metric in metrics[:10]:
        metric_key = str(metric.get("raw_key") or "")
        if metric_key not in base.columns:
            continue
        work = base[["__period", metric_key]].copy()
        work[metric_key] = pd.to_numeric(work[metric_key], errors="coerce")
        work = work.dropna(subset=["__period", metric_key])
        if work["__period"].nunique() < 2:
            continue
        aggregation = str(metric.get("aggregation") or "mean")
        grouped = work.groupby("__period")[metric_key]
        series = grouped.sum() if aggregation == "sum" else grouped.mean()
        series = series.sort_index()
        if len(series) < 2:
            continue
        first = _safe_float(series.iloc[0])
        last = _safe_float(series.iloc[-1])
        absolute_change = last - first
        growth_rate = absolute_change / abs(first) if first else 0.0
        values = [
            {"period": str(period), "value": _safe_float(value)}
            for period, value in series.tail(12).items()
        ]
        output.append(
            {
                "date_raw_key": date_key,
                "date_localized_label": localize_historical_key(date_key, fallback=date_key),
                "metric_raw_key": metric_key,
                "metric_localized_label": localize_historical_key(metric_key, fallback=metric_key),
                "aggregation": aggregation,
                "period_grain": "month",
                "period_count": int(len(series)),
                "first_period": str(series.index[0]),
                "last_period": str(series.index[-1]),
                "first_value": first,
                "last_value": last,
                "absolute_change": _safe_float(absolute_change),
                "growth_rate": round(growth_rate, 6),
                "direction": "up" if absolute_change > 0 else ("down" if absolute_change < 0 else "flat"),
                "volatility": _safe_float(series.std()),
                "series": values,
                "management_use": "用于生成趋势页、当前期变化解释和节奏判断。",
            }
        )
    output.sort(key=lambda item: abs(_safe_float(item.get("growth_rate"))), reverse=True)
    return output[:20]


def _concentration_diagnostics(cube: list[dict[str, Any]]) -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    for item in cube[:80]:
        rows = list(item.get("rows") or [])
        if len(rows) < 3:
            continue
        if item.get("aggregation") != "sum":
            continue
        share_rows = [
            row for row in rows
            if row.get("share_semantics") == "contribution_share" and row.get("share_of_total") is not None
        ]
        if len(share_rows) < 3:
            continue
        shares = [_safe_float(row.get("share_of_total")) for row in share_rows]
        top1_share = shares[0] if shares else 0.0
        top3_share = sum(shares[:3])
        hhi = sum(share * share for share in shares if share > 0)
        values = [_safe_float(row.get("value")) for row in rows]
        gap = values[0] - values[-1] if values else 0.0
        diagnostics.append(
            {
                "dimension_raw_key": item.get("dimension_raw_key"),
                "dimension_localized_label": item.get("dimension_localized_label"),
                "metric_raw_key": item.get("metric_raw_key"),
                "metric_localized_label": item.get("metric_localized_label"),
                "aggregation": item.get("aggregation"),
                "segment_count": len(rows),
                "top1_share": round(top1_share, 6),
                "top3_share": round(top3_share, 6),
                "hhi": round(hhi, 6),
                "leader_laggard_gap": _safe_float(gap),
                "concentration_level": (
                    "high" if top3_share >= 0.65 or hhi >= 0.22 else ("medium" if top3_share >= 0.45 or hhi >= 0.12 else "low")
                ),
                "management_use": "用于判断资源是否过度集中、是否需要扩展第二梯队或修复尾部对象。",
            }
        )
    diagnostics.sort(
        key=lambda item: (_safe_float(item.get("top3_share")), _safe_float(item.get("hhi"))),
        reverse=True,
    )
    return diagnostics[:50]


def _priority_zone(share: float | None, lift: float) -> str:
    if share is None:
        return "均值/率值观察区"
    if share >= 0.12 and lift >= 0.12:
        return "头部放量区"
    if share >= 0.08 and lift < 0:
        return "规模修复区"
    if share < 0.05 and lift >= 0.18:
        return "价值培育区"
    return "观察区"


def _cross_dimension_priority_tables(frame: Any, metrics: list[dict[str, Any]], dimensions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pd = _pd()
    tables: list[dict[str, Any]] = []
    dimension_names = [str(item.get("raw_key") or "") for item in dimensions[:6] if str(item.get("raw_key") or "") in frame.columns]
    metric_specs = [item for item in metrics[:4] if str(item.get("raw_key") or "") in frame.columns]
    for left_index, dimension_a in enumerate(dimension_names):
        for dimension_b in dimension_names[left_index + 1 :]:
            for metric in metric_specs:
                metric_name = str(metric.get("raw_key") or "")
                if metric_name in {dimension_a, dimension_b}:
                    continue
                aggregation = str(metric.get("aggregation") or "mean")
                work = frame[[dimension_a, dimension_b, metric_name]].copy()
                work[dimension_a] = work[dimension_a].fillna("缺失").astype(str)
                work[dimension_b] = work[dimension_b].fillna("缺失").astype(str)
                work["__metric"] = pd.to_numeric(work[metric_name], errors="coerce")
                work = work.dropna(subset=["__metric"])
                if work.empty:
                    continue
                grouped = work.groupby([dimension_a, dimension_b], dropna=False)["__metric"]
                rows_frame = grouped.sum().reset_index(name="value") if aggregation == "sum" else grouped.mean().reset_index(name="value")
                rows_frame["n"] = work.groupby([dimension_a, dimension_b], dropna=False).size().reset_index(name="n")["n"]
                rows_frame = rows_frame.sort_values("value", ascending=False).head(20)
                if rows_frame.empty:
                    continue
                overall = _safe_float(work["__metric"].sum() if aggregation == "sum" else work["__metric"].mean(), default=0.0)
                rows: list[dict[str, Any]] = []
                for rank, (_, row) in enumerate(rows_frame.iterrows(), start=1):
                    value = _safe_float(row["value"])
                    share = value / overall if aggregation == "sum" and overall else None
                    lift = (value / overall - 1.0) if overall else 0.0
                    rows.append(
                        {
                            "dimension_a": dimension_a,
                            "dimension_a_label": localize_historical_key(dimension_a, fallback=dimension_a),
                            "dimension_a_value_raw": str(row[dimension_a]),
                            "dimension_a_value_label": localize_historical_text(row[dimension_a], fallback=str(row[dimension_a])),
                            "dimension_b": dimension_b,
                            "dimension_b_label": localize_historical_key(dimension_b, fallback=dimension_b),
                            "dimension_b_value_raw": str(row[dimension_b]),
                            "dimension_b_value_label": localize_historical_text(row[dimension_b], fallback=str(row[dimension_b])),
                            "metric": metric_name,
                            "metric_label": localize_historical_key(metric_name, fallback=metric_name),
                            "value": value,
                            "share_of_total": round(share, 6) if share is not None else None,
                            "share_semantics": "contribution_share" if share is not None else "not_applicable_for_mean_or_rate",
                            "lift_vs_overall": round(lift, 6),
                            "priority_zone": _priority_zone(share, lift),
                            "n": int(row["n"]),
                            "rank": rank,
                        }
                    )
                tables.append(
                    {
                        "table_id": _safe_id(f"{dimension_a}_{dimension_b}_{metric_name}", fallback="cross_dimension"),
                        "dimension_a": dimension_a,
                        "dimension_a_label": localize_historical_key(dimension_a, fallback=dimension_a),
                        "dimension_b": dimension_b,
                        "dimension_b_label": localize_historical_key(dimension_b, fallback=dimension_b),
                        "metric": metric_name,
                        "metric_label": localize_historical_key(metric_name, fallback=metric_name),
                        "aggregation": aggregation,
                        "overall_value": overall,
                        "rows": rows[:12],
                    }
                )
    return tables[:24]


def _segment_scorecards(cube: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scorecards: list[dict[str, Any]] = []
    for item in cube[:24]:
        rows = list(item.get("rows") or [])[:4]
        for row in rows:
            scorecards.append(
                {
                    "scorecard_id": _safe_id(
                        f"{item.get('dimension_raw_key')}_{row.get('dimension_value_raw')}_{item.get('metric_raw_key')}",
                        fallback="scorecard",
                    ),
                    "dimension_raw_key": item.get("dimension_raw_key"),
                    "dimension_localized_label": item.get("dimension_localized_label"),
                    "segment_raw_value": row.get("dimension_value_raw"),
                    "segment_localized_label": row.get("dimension_value_label"),
                    "metric_raw_key": item.get("metric_raw_key"),
                    "metric_localized_label": item.get("metric_localized_label"),
                    "value": row.get("value"),
                    "share_of_total": row.get("share_of_total"),
                    "share_semantics": row.get("share_semantics"),
                    "lift_vs_overall": row.get("lift_vs_overall"),
                    "rank": row.get("rank"),
                    "management_signal": (
                        "头部高价值分层，适合放量保护。"
                        if int(row.get("rank") or 99) <= 2
                        else "中尾部分层，适合观察或修复。"
                    ),
                }
            )
    return scorecards[:60]


def _action_candidates(
    top_bottom: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
    cross_tables: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for item in top_bottom[:24]:
        dimension_label = str(item.get("dimension_localized_label") or "")
        metric_label = str(item.get("metric_localized_label") or "")
        top = list(item.get("top") or [])
        bottom = list(item.get("bottom") or [])
        if top:
            leader = top[0]
            actions.append(
                {
                    "candidate_id": _safe_id(f"leader_{dimension_label}_{metric_label}_{leader.get('dimension_value_raw')}", fallback="leader"),
                    "priority": "high",
                    "action_type": "scale_leader",
                    "object_label": f"{dimension_label} / {leader.get('dimension_value_label')}",
                    "evidence_source": "historical_top_bottom_segments.json",
                    "recommendation": f"优先复制 `{dimension_label}` 中 `{leader.get('dimension_value_label')}` 在 `{metric_label}` 上的领先做法。",
                }
            )
        if bottom:
            laggard = bottom[0]
            actions.append(
                {
                    "candidate_id": _safe_id(f"repair_{dimension_label}_{metric_label}_{laggard.get('dimension_value_raw')}", fallback="repair"),
                    "priority": "medium",
                    "action_type": "repair_laggard",
                    "object_label": f"{dimension_label} / {laggard.get('dimension_value_label')}",
                    "evidence_source": "historical_top_bottom_segments.json",
                    "recommendation": f"将 `{dimension_label}` 中 `{laggard.get('dimension_value_label')}` 纳入修复清单，先定位 `{metric_label}` 落后的可控原因。",
                }
            )
    for rel in relationships[:10]:
        actions.append(
            {
                "candidate_id": _safe_id(f"relationship_{rel.get('left_raw_key')}_{rel.get('right_raw_key')}", fallback="relationship"),
                "priority": "medium",
                "action_type": "relationship_probe",
                "object_label": f"{rel.get('left_localized_label')} x {rel.get('right_localized_label')}",
                "evidence_source": "historical_pairwise_relationships.json",
                "recommendation": f"围绕 `{rel.get('left_localized_label')}` 与 `{rel.get('right_localized_label')}` 的强联动关系设计协同动作或拆解共同驱动因素。",
            }
        )
    for table in cross_tables[:8]:
        rows = list(table.get("rows") or [])
        if not rows:
            continue
        row = rows[0]
        actions.append(
            {
                "candidate_id": _safe_id(f"cross_{table.get('table_id')}_{row.get('rank')}", fallback="cross"),
                "priority": "high" if row.get("priority_zone") in {"头部放量区", "价值培育区"} else "medium",
                "action_type": "cross_dimension_priority",
                "object_label": f"{row.get('dimension_a_value_label')} x {row.get('dimension_b_value_label')}",
                "evidence_source": "historical_cross_dimension_priority_tables.json",
                "recommendation": f"把 `{row.get('dimension_a_value_label')} x {row.get('dimension_b_value_label')}` 作为 `{row.get('priority_zone')}` 对象，围绕 `{row.get('metric_label')}` 安排分层动作。",
            }
        )
    return actions[:64]


def _build_chart_bundle(
    frame: Any,
    metrics: list[dict[str, Any]],
    dimensions: list[dict[str, Any]],
    cube: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
) -> dict[str, Any]:
    bundle: dict[str, Any] = {"extra_categories": [], "extra_distributions": [], "extra_scatters": []}
    if cube:
        first = cube[0]
        rows = list(first.get("rows") or [])[:12]
        bundle["category"] = {
            "kind": "bar",
            "title": f"{first.get('dimension_localized_label')} x {first.get('metric_localized_label')} 贡献结构",
            "x": [row.get("dimension_value_label") for row in rows],
            "y": [row.get("value") for row in rows],
            "insight_input": first,
        }
    if metrics:
        first_metric = metrics[0]
        bundle["distribution"] = {
            "kind": "histogram",
            "title": f"{first_metric.get('localized_label')} 分布",
            "x": ["最小值", "下四分位", "中位数", "上四分位", "最大值"],
            "y": [
                first_metric.get("min"),
                first_metric.get("q25"),
                first_metric.get("median"),
                first_metric.get("q75"),
                first_metric.get("max"),
            ],
            "insight_input": first_metric,
        }
    if len(metrics) >= 2 and relationships:
        labels = [str(item.get("localized_label")) for item in metrics[:8]]
        raw_names = [str(item.get("raw_key")) for item in metrics[:8]]
        index = {name: idx for idx, name in enumerate(raw_names)}
        matrix = [[1.0 if left_name == right_name else 0.0 for right_name in raw_names] for left_name in raw_names]
        for rel in relationships:
            left = str(rel.get("left_raw_key"))
            right = str(rel.get("right_raw_key"))
            if left in index and right in index:
                i = index[left]
                j = index[right]
                matrix[i][j] = matrix[j][i] = _safe_float(rel.get("correlation"))
        bundle["correlation"] = {
            "kind": "heatmap",
            "title": "经营驱动因素相关图",
            "labels": labels,
            "matrix": matrix,
            "insight_input": {"relationships": relationships[:20]},
        }
    if len(metrics) >= 2:
        label_column = str((dimensions[0] if dimensions else {}).get("raw_key") or "")
        x_metric = str(metrics[0].get("raw_key") or "")
        y_metric = str(metrics[1].get("raw_key") or "")
        points = []
        if x_metric in frame.columns and y_metric in frame.columns:
            pd = _pd()
            work = frame[[column for column in [x_metric, y_metric, label_column] if column and column in frame.columns]].copy()
            work[x_metric] = pd.to_numeric(work[x_metric], errors="coerce")
            work[y_metric] = pd.to_numeric(work[y_metric], errors="coerce")
            work = work.dropna(subset=[x_metric, y_metric]).head(120)
            for index_value, row in work.iterrows():
                label = str(row.get(label_column) or f"row_{index_value}") if label_column else f"row_{index_value}"
                points.append({"label": localize_historical_text(label, fallback=label), "x": _safe_float(row.get(x_metric)), "y": _safe_float(row.get(y_metric))})
        bundle["scatter"] = {
            "kind": "scatter",
            "title": f"{metrics[0].get('localized_label')} vs {metrics[1].get('localized_label')}",
            "x_label": metrics[0].get("localized_label"),
            "y_label": metrics[1].get("localized_label"),
            "points": points,
            "insight_input": {"x_metric": metrics[0], "y_metric": metrics[1]},
        }
    return bundle


def _build_support_tables(
    metrics: list[dict[str, Any]],
    cube: list[dict[str, Any]],
    top_bottom: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
    actions: list[dict[str, Any]],
    cross_tables: list[dict[str, Any]],
    table_profiles: list[dict[str, Any]],
    missingness: list[dict[str, Any]] | None = None,
    outliers: list[dict[str, Any]] | None = None,
    trends: list[dict[str, Any]] | None = None,
    concentration: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    missingness = list(missingness or [])
    outliers = list(outliers or [])
    trends = list(trends or [])
    concentration = list(concentration or [])
    ranking_tables: list[dict[str, Any]] = []
    seen_dimensions: set[str] = set()
    for item in cube:
        dimension = str(item.get("dimension_localized_label") or "")
        raw_dimension = str(item.get("dimension_raw_key") or "")
        if not raw_dimension or raw_dimension in seen_dimensions:
            continue
        seen_dimensions.add(raw_dimension)
        ranking_tables.append(
            {
                "dimension": dimension,
                "dimension_raw_key": raw_dimension,
                "metric": item.get("metric_localized_label"),
                "metric_raw_key": item.get("metric_raw_key"),
                "rows": [
                    {
                        dimension: row.get("dimension_value_label"),
                        "value": row.get("value"),
                        "row_count": row.get("n"),
                        "share_of_total": row.get("share_of_total"),
                        "share_semantics": row.get("share_semantics"),
                        "lift_vs_overall": row.get("lift_vs_overall"),
                        "rank": row.get("rank"),
                    }
                    for row in list(item.get("rows") or [])[:12]
                ],
            }
        )
    glossary_rows = []
    for item in metrics[:20]:
        glossary_rows.append(
            {
                "column": item.get("localized_label"),
                "raw_key": item.get("raw_key"),
                "dtype": item.get("metric_type"),
                "metric_kind": item.get("metric_kind") or "direct_metric",
                "is_derived": bool(item.get("is_derived") or item.get("metric_kind") == "derived_metric"),
                "formula": item.get("formula"),
                "unique_count": item.get("unique_count"),
                "top_values": "",
            }
        )
    derived_metric_rows = [
        {
            "metric": item.get("localized_label"),
            "metric_raw_key": item.get("raw_key"),
            "metric_type": item.get("metric_type"),
            "aggregation": item.get("aggregation"),
            "formula": item.get("formula"),
            "source_columns": " / ".join(str(value) for value in list(item.get("source_columns") or [])[:6]),
            "business_meaning": item.get("business_meaning"),
            "derivation_status": item.get("derivation_status"),
            "value": item.get("sum") if item.get("aggregation") == "sum" else item.get("mean"),
            "non_null": item.get("non_null"),
        }
        for item in metrics
        if item.get("is_derived") or item.get("metric_kind") == "derived_metric"
    ]
    for item in table_profiles[:8]:
        glossary_rows.append(
            {
                "column": item.get("table_label"),
                "raw_key": item.get("table_id"),
                "dtype": "table",
                "unique_count": item.get("column_count"),
                "top_values": " / ".join(entry.get("localized_label") for entry in item.get("main_business_objects", [])[:4]),
            }
        )
    return {
        "kpi_snapshot": [
            {
                "metric": metric.get("localized_label"),
                "metric_raw_key": metric.get("raw_key"),
                "aggregation": metric.get("aggregation"),
                "metric_kind": metric.get("metric_kind") or "direct_metric",
                "is_derived": bool(metric.get("is_derived") or metric.get("metric_kind") == "derived_metric"),
                "formula": metric.get("formula"),
                "value": metric.get("sum") if metric.get("aggregation") == "sum" else metric.get("mean"),
                "non_null": metric.get("non_null"),
            }
            for metric in metrics[:16]
        ],
        "derived_metric_rows": derived_metric_rows[:24],
        "ranking_tables": ranking_tables[:12],
        "correlation_focus": [
            {
                "left": item.get("left_localized_label"),
                "right": item.get("right_localized_label"),
                "correlation": item.get("correlation"),
                "abs_correlation": item.get("abs_correlation"),
            }
            for item in relationships[:12]
        ],
        "glossary_rows": glossary_rows,
        "dimension_matrix": [
            {
                "dimension": item.get("dimension_localized_label"),
                "metric": item.get("metric_localized_label"),
                "top_segment": (list(item.get("top") or [{}])[0]).get("dimension_value_label"),
                "top_value": (list(item.get("top") or [{}])[0]).get("value"),
                "bottom_segment": (list(item.get("bottom") or [{}])[0]).get("dimension_value_label"),
                "bottom_value": (list(item.get("bottom") or [{}])[0]).get("value"),
            }
            for item in top_bottom[:24]
        ],
        "priority_action_table": [
            {
                "priority_zone": item.get("priority"),
                "current_signal": item.get("object_label"),
                "management_question": item.get("recommendation"),
                "action_lens": item.get("action_type"),
            }
            for item in actions[:24]
        ],
        "appendix_detail_rows": [
            {
                "dimension_a": row.get("dimension_a_label"),
                "dimension_a_segment": row.get("dimension_a_value_label"),
                "dimension_b": row.get("dimension_b_label"),
                "dimension_b_segment": row.get("dimension_b_value_label"),
                "metric": row.get("metric_label"),
                "value": row.get("value"),
                "priority_zone": row.get("priority_zone"),
                "rank": row.get("rank"),
            }
            for table in cross_tables[:10]
            for row in list(table.get("rows") or [])[:4]
        ],
        "top_bottom_segments": top_bottom[:40],
        "action_candidates": actions[:40],
        "cross_dimension_priority_tables": cross_tables[:20],
        "segment_scorecards": _segment_scorecards(cube)[:40],
        "missingness_diagnostics": missingness[:24],
        "outlier_influence_summary": outliers[:24],
        "time_trend_slices": trends[:16],
        "concentration_diagnostics": concentration[:24],
    }


def _localized_label_map(
    metrics: list[dict[str, Any]],
    dimensions: list[dict[str, Any]],
    table_profiles: list[dict[str, Any]],
) -> list[dict[str, str]]:
    rows = {}
    for entry in table_profiles:
        rows[str(entry.get("table_id") or "")] = _label_entry(str(entry.get("table_id") or ""))
        for key in entry.get("candidate_keys", []):
            if isinstance(key, dict):
                rows[str(key.get("raw_key") or "")] = dict(key)
        for obj in entry.get("main_business_objects", []):
            if isinstance(obj, dict):
                rows[str(obj.get("raw_key") or "")] = dict(obj)
    for entry in metrics + dimensions:
        raw_key = str(entry.get("raw_key") or "")
        if raw_key:
            rows[raw_key] = _label_entry(raw_key)
    return [value for key, value in sorted(rows.items(), key=lambda item: item[0]) if key]


def build_business_analysis_package(
    *,
    workspace: Path,
    data_frames: dict[str, Any] | None = None,
    data_frame: Any | None = None,
    data_snapshot_path: Path | None = None,
    current_report_context_path: Path | None = None,
    column_summaries: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a deterministic multi-table business analysis package for high-grade deck pipelines."""
    data_frames = {str(key): value for key, value in dict(data_frames or {}).items() if value is not None}
    primary_table_id, frame = _select_primary_frame(data_frames, data_frame, data_snapshot_path)
    if not data_frames and primary_table_id not in data_frames and frame is not None and hasattr(frame, "columns"):
        data_frames[primary_table_id] = frame

    context_payload = _read_json(current_report_context_path) if current_report_context_path and current_report_context_path.exists() else {}
    derived_metrics = _external_derived_metrics(
        context_payload=context_payload,
        workspace=workspace,
        context_path=current_report_context_path,
    )
    row_count = int(len(frame))
    metrics = _merge_derived_metrics(_numeric_columns(frame), derived_metrics)
    dimensions = _dimension_columns(frame, {str(item.get("raw_key")) for item in metrics})
    dates = _date_columns(frame)
    cube = _dimension_metric_cube(frame, metrics, dimensions) if not frame.empty else []
    top_bottom = _top_bottom_segments(cube)
    relationships = _pairwise_relationships(frame, metrics) if not frame.empty else []
    cross_tables = _cross_dimension_priority_tables(frame, metrics, dimensions) if not frame.empty else []
    scorecards = _segment_scorecards(cube)
    missingness = _missingness_diagnostics(frame) if not frame.empty else []
    outliers = _outlier_influence_summary(frame, metrics) if not frame.empty else []
    trends = _time_trend_slices(frame, metrics, dates) if not frame.empty else []
    concentration = _concentration_diagnostics(cube)
    actions = _action_candidates(top_bottom, relationships, cross_tables)
    table_profiles = _table_profiles(data_frames)
    chart_bundle = _build_chart_bundle(frame, metrics, dimensions, cube, relationships)
    if trends:
        chart_bundle["time_trends"] = trends[:8]
    if concentration:
        chart_bundle["concentration_diagnostics"] = concentration[:12]
    support_tables = _build_support_tables(
        metrics,
        cube,
        top_bottom,
        relationships,
        actions,
        cross_tables,
        table_profiles,
        missingness=missingness,
        outliers=outliers,
        trends=trends,
        concentration=concentration,
    )
    localized_label_map = _localized_label_map(metrics, dimensions, table_profiles)

    data_profile = {
        "primary_table_id": primary_table_id,
        "primary_table_label": localize_historical_text(primary_table_id, fallback=primary_table_id),
        "row_count": row_count,
        "column_count": int(len(frame.columns)),
        "table_count": len(table_profiles),
        "metric_count": len(metrics),
        "derived_metric_count": len([item for item in metrics if item.get("is_derived") or item.get("metric_kind") == "derived_metric"]),
        "dimension_count": len(dimensions),
        "date_column_count": len(dates),
        "candidate_primary_keys": [_label_entry(item.get("raw_key")) for table in table_profiles for item in table.get("candidate_keys", [])][:12],
        "tables": table_profiles,
        "main_business_objects": [
            entry for table in table_profiles for entry in table.get("main_business_objects", [])
        ][:16],
        "date_ranges": dates,
        "field_coverage": [
            {
                "raw_key": str(column),
                "localized_label": localize_historical_key(column, fallback=str(column)),
                "missing_count": int(frame[column].isna().sum()) if column in frame.columns else 0,
                "missing_ratio": round(float(frame[column].isna().mean()), 6) if column in frame.columns and row_count else 0,
            }
            for column in frame.columns
        ],
    }
    metric_inventory = {"metrics": metrics}
    derived_metric_inventory = {
        "derived_metric_count": len([item for item in metrics if item.get("is_derived") or item.get("metric_kind") == "derived_metric"]),
        "metrics": [item for item in metrics if item.get("is_derived") or item.get("metric_kind") == "derived_metric"],
    }
    dimension_metric_cube = {"cube": cube}
    cross_dimension_priority = {"tables": cross_tables}
    pairwise_relationships = {"relationships": relationships}
    segment_scorecards = {"scorecards": scorecards}
    action_candidates = {"actions": actions}
    top_bottom_payload = {"segments": top_bottom}
    missingness_payload = {"diagnostics": missingness}
    outlier_payload = {"outliers": outliers}
    time_trend_payload = {"trends": trends}
    concentration_payload = {"diagnostics": concentration}

    paths = {
        "data_profile": workspace / "historical_data_profile.json",
        "metric_inventory": workspace / "historical_metric_inventory.json",
        "derived_metric_inventory": workspace / "historical_derived_metric_inventory.json",
        "dimension_metric_cube": workspace / "historical_dimension_metric_cube.json",
        "cross_dimension_priority_tables": workspace / "historical_cross_dimension_priority_tables.json",
        "pairwise_relationships": workspace / "historical_pairwise_relationships.json",
        "segment_scorecards": workspace / "historical_segment_scorecards.json",
        "action_candidates": workspace / "historical_action_candidates.json",
        "top_bottom_segments": workspace / "historical_top_bottom_segments.json",
        "missingness_diagnostics": workspace / "historical_missingness_diagnostics.json",
        "outlier_influence_summary": workspace / "historical_outlier_influence_summary.json",
        "time_trend_slices": workspace / "historical_time_trend_slices.json",
        "concentration_diagnostics": workspace / "historical_concentration_diagnostics.json",
        "chart_bundle": workspace / "historical_chart_bundle.json",
        "support_tables": workspace / "historical_support_tables.json",
    }
    _write_json(paths["data_profile"], data_profile)
    _write_json(paths["metric_inventory"], metric_inventory)
    _write_json(paths["derived_metric_inventory"], derived_metric_inventory)
    _write_json(paths["dimension_metric_cube"], dimension_metric_cube)
    _write_json(paths["cross_dimension_priority_tables"], cross_dimension_priority)
    _write_json(paths["pairwise_relationships"], pairwise_relationships)
    _write_json(paths["segment_scorecards"], segment_scorecards)
    _write_json(paths["action_candidates"], action_candidates)
    _write_json(paths["top_bottom_segments"], top_bottom_payload)
    _write_json(paths["missingness_diagnostics"], missingness_payload)
    _write_json(paths["outlier_influence_summary"], outlier_payload)
    _write_json(paths["time_trend_slices"], time_trend_payload)
    _write_json(paths["concentration_diagnostics"], concentration_payload)
    _write_json(paths["chart_bundle"], chart_bundle)
    _write_json(paths["support_tables"], support_tables)

    manifest = {
        "primary_table_id": primary_table_id,
        "row_count": row_count,
        "table_count": len(table_profiles),
        "metric_count": len(metrics),
        "derived_metric_count": len(derived_metric_inventory["metrics"]),
        "dimension_count": len(dimensions),
        "cube_count": len(cube),
        "cross_dimension_table_count": len(cross_tables),
        "segment_scorecard_count": len(scorecards),
        "relationship_count": len(relationships),
        "action_candidate_count": len(actions),
        "missingness_issue_count": len(missingness),
        "outlier_metric_count": len(outliers),
        "time_trend_count": len(trends),
        "concentration_signal_count": len(concentration),
        "localized_label_map": localized_label_map,
        "asset_ready_views": {
            "chart_bundle": {"path": paths["chart_bundle"].name, "view_type": "chart_bundle"},
            "support_tables": {"path": paths["support_tables"].name, "view_type": "support_tables"},
            "derived_metric_inventory": {"path": paths["derived_metric_inventory"].name, "view_type": "derived_metrics"},
            "cross_dimension_priority_tables": {"path": paths["cross_dimension_priority_tables"].name, "view_type": "cross_dimension"},
            "segment_scorecards": {"path": paths["segment_scorecards"].name, "view_type": "scorecards"},
            "dimension_metric_cube": {"path": paths["dimension_metric_cube"].name, "view_type": "cube"},
            "top_bottom_segments": {"path": paths["top_bottom_segments"].name, "view_type": "top_bottom"},
            "pairwise_relationships": {"path": paths["pairwise_relationships"].name, "view_type": "relationships"},
            "action_candidates": {"path": paths["action_candidates"].name, "view_type": "actions"},
            "missingness_diagnostics": {"path": paths["missingness_diagnostics"].name, "view_type": "data_quality"},
            "outlier_influence_summary": {"path": paths["outlier_influence_summary"].name, "view_type": "outlier_influence"},
            "time_trend_slices": {"path": paths["time_trend_slices"].name, "view_type": "time_trend"},
            "concentration_diagnostics": {"path": paths["concentration_diagnostics"].name, "view_type": "concentration"},
        },
        "source_artifacts": {key: str(path.resolve()) for key, path in paths.items()},
    }
    manifest_path = workspace / "historical_data_asset_manifest.json"
    _write_json(manifest_path, manifest)

    if current_report_context_path and current_report_context_path.exists():
        try:
            context = json.loads(current_report_context_path.read_text(encoding="utf-8-sig"))
        except Exception:
            context = {}
        if isinstance(context, dict):
            context["chart_bundle"] = chart_bundle
            context["support_tables"] = support_tables
            context["analysis_package_context"] = {
                "manifest_path": manifest_path.name,
                "data_profile_path": paths["data_profile"].name,
                "metric_inventory_path": paths["metric_inventory"].name,
                "derived_metric_inventory_path": paths["derived_metric_inventory"].name,
                "dimension_metric_cube_path": paths["dimension_metric_cube"].name,
                "cross_dimension_priority_tables_path": paths["cross_dimension_priority_tables"].name,
                "pairwise_relationships_path": paths["pairwise_relationships"].name,
                "segment_scorecards_path": paths["segment_scorecards"].name,
                "action_candidates_path": paths["action_candidates"].name,
                "missingness_diagnostics_path": paths["missingness_diagnostics"].name,
                "outlier_influence_summary_path": paths["outlier_influence_summary"].name,
                "time_trend_slices_path": paths["time_trend_slices"].name,
                "concentration_diagnostics_path": paths["concentration_diagnostics"].name,
                "localized_label_map_count": len(localized_label_map),
                "metric_count": len(metrics),
                "derived_metric_count": len(derived_metric_inventory["metrics"]),
                "dimension_count": len(dimensions),
                "table_count": len(table_profiles),
                "time_trend_count": len(trends),
                "outlier_metric_count": len(outliers),
                "concentration_signal_count": len(concentration),
            }
            _write_json(current_report_context_path, context)

    return {
        "manifest_path": str(manifest_path.resolve()),
        "manifest": manifest,
        "data_profile": data_profile,
        "metric_inventory": metric_inventory,
        "derived_metric_inventory": derived_metric_inventory,
        "dimension_metric_cube": dimension_metric_cube,
        "cross_dimension_priority_tables": cross_dimension_priority,
        "pairwise_relationships": pairwise_relationships,
        "segment_scorecards": segment_scorecards,
        "action_candidates": action_candidates,
        "top_bottom_segments": top_bottom_payload,
        "missingness_diagnostics": missingness_payload,
        "outlier_influence_summary": outlier_payload,
        "time_trend_slices": time_trend_payload,
        "concentration_diagnostics": concentration_payload,
        "chart_bundle": chart_bundle,
        "support_tables": support_tables,
    }
