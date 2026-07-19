from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd


SUPPORTED_FORMULA_FAMILIES = {
    "ratio",
    "contribution",
    "concentration",
    "late_fulfillment",
    "freight_efficiency",
    "rating_risk",
    "route_risk",
    "time_trend",
    "top_bottom_object",
}


FAMILY_CHINESE_LABELS = {
    "ratio": "比率指标",
    "contribution": "贡献度指标",
    "concentration": "集中度指标",
    "late_fulfillment": "迟发履约指标",
    "freight_efficiency": "运费效率指标",
    "rating_risk": "低评分风险指标",
    "route_risk": "路线风险指标",
    "time_trend": "时间趋势指标",
    "top_bottom_object": "对象差异指标",
}

METRIC_CHINESE_OVERRIDES = {
    "gmv_per_order": "单均成交额",
    "gmv_per_order_planned": "单均成交额",
    "category_gmv_contribution": "类目成交额贡献度",
    "category_gmv_contribution_planned": "类目成交额贡献度",
    "category_gmv_concentration": "类目成交额集中度",
    "seller_gmv_contribution_planned": "卖家成交额贡献度",
    "sku_gmv_contribution_planned": "SKU成交额贡献度",
    "seller_gmv_concentration_planned": "卖家成交额集中度",
    "low_rating_risk": "低评分风险率",
    "low_rating_risk_planned": "低评分风险率",
    "freight_to_gmv": "运费成交额占比",
    "freight_to_gmv_planned": "运费成交额占比",
    "freight_to_revenue_planned": "运费收入占比",
    "late_fulfillment_rate_planned": "延迟履约率",
    "route_delay_risk_planned": "路线延迟风险",
    "route_freight_risk_planned": "路线运费风险",
    "gmv_time_trend_planned": "成交额时间趋势变化率",
    "seller_top_bottom_gap_planned": "卖家头尾差异",
    "category_top_bottom_gap_planned": "类目头尾差异",
}


def _slug(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9_]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "metric"


def _contains_cjk(value: Any) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", str(value or "")))


def _reader_metric_name(metric_id: str, metric_name: Any, family: str) -> str:
    text = str(metric_name or "").strip()
    if _contains_cjk(text):
        return text
    metric_key = _slug(metric_id)
    if metric_key in METRIC_CHINESE_OVERRIDES:
        return METRIC_CHINESE_OVERRIDES[metric_key]
    family_label = FAMILY_CHINESE_LABELS.get(_slug(family), "派生指标")
    return f"{family_label}（{metric_key}）"


def _reader_business_meaning(metric_id: str, business_meaning: Any, family: str) -> str:
    text = str(business_meaning or "").strip()
    if _contains_cjk(text):
        return text
    metric_name = _reader_metric_name(metric_id, "", family)
    return f"{metric_name}用于补充判断电商经营效率、风险或结构变化。"


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        if text.startswith("[") and text.endswith("]"):
            try:
                parsed = json.loads(text.replace("'", '"'))
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            except Exception:
                pass
        return [part.strip() for part in re.split(r"[,/;|]", text) if part.strip()]
    return [str(value).strip()] if str(value).strip() else []


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]], *, columns: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def _load_source_frame(workspace: Path) -> pd.DataFrame:
    source_path = workspace / "source_dataset.csv"
    if not source_path.is_file():
        raise ValueError(f"derived metric family execution source dataset not found: {source_path}")
    frame = pd.read_csv(source_path, encoding="utf-8-sig")
    frame.columns = [str(column) for column in frame.columns]
    return frame


def _specs_from_plan(plan: dict[str, Any]) -> list[dict[str, Any]]:
    specs = plan.get("metric_specs_draft")
    if not isinstance(specs, list):
        specs = []
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(specs, start=1):
        if not isinstance(item, dict):
            continue
        metric_id = _slug(item.get("metric_id") or item.get("id") or item.get("metric_name") or f"planned_metric_{index:02d}")
        family = _slug(item.get("formula_family") or item.get("metric_family") or item.get("family") or item.get("metric_type"))
        normalized.append({**item, "metric_id": metric_id, "formula_family": family})
    return normalized


def _column_from_spec(spec: dict[str, Any], *names: str) -> str:
    for name in names:
        value = str(spec.get(name) or "").strip()
        if value:
            return value
    columns = _as_list(spec.get("source_columns"))
    if columns:
        return columns[0]
    return ""


def _numeric(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        raise KeyError(column)
    return pd.to_numeric(frame[column], errors="coerce")


def _non_empty_count(frame: pd.DataFrame, column: str) -> float:
    if column not in frame.columns:
        raise KeyError(column)
    series = frame[column]
    return float(series.notna().sum())


def _distinct_non_empty_count(frame: pd.DataFrame, column: str) -> float:
    if column not in frame.columns:
        raise KeyError(column)
    series = frame[column].dropna().astype(str).str.strip()
    if series.empty:
        return 0.0
    return float(series[series != ""].nunique())


def _boolean_indicator(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        raise KeyError(column)
    numeric = pd.to_numeric(frame[column], errors="coerce")
    if numeric.notna().any():
        return (numeric > 0).astype(float).where(numeric.notna())
    series = frame[column].fillna("").astype(str).str.strip().str.lower()
    mapping = {
        "1": 1.0,
        "0": 0.0,
        "true": 1.0,
        "false": 0.0,
        "yes": 1.0,
        "no": 0.0,
        "y": 1.0,
        "n": 0.0,
        "late": 1.0,
        "on_time": 0.0,
    }
    return series.map(mapping)


def _value_series(frame: pd.DataFrame, column: str) -> pd.Series:
    numeric = pd.to_numeric(frame[column], errors="coerce")
    if numeric.notna().any():
        return numeric
    boolean = _boolean_indicator(frame, column)
    if boolean.notna().any():
        return boolean
    return numeric


def _resolve_denominator_value(
    frame: pd.DataFrame,
    *,
    denominator_column: str,
    denominator_mode: str,
    fallback_column: str,
) -> tuple[float, str, list[str]]:
    mode = _slug(denominator_mode or "sum")
    target_column = denominator_column or fallback_column
    if mode == "sum":
        if not target_column:
            raise ValueError("sum denominator requires denominator_column")
        return float(_numeric(frame, target_column).sum()), f"sum({target_column})", [target_column]
    if mode == "row_count":
        count_column = target_column or fallback_column
        if not count_column:
            return float(len(frame.index)), "row_count()", []
        return _non_empty_count(frame, count_column), f"count_non_null({count_column})", [count_column]
    if mode == "distinct_count":
        if not target_column:
            raise ValueError("distinct_count denominator requires denominator_column")
        return _distinct_non_empty_count(frame, target_column), f"count_distinct({target_column})", [target_column]
    raise ValueError(f"unsupported denominator_mode:{denominator_mode}")


def _safe_divide(numerator: float, denominator: float) -> float:
    if abs(float(denominator or 0)) <= 1e-12:
        raise ZeroDivisionError("denominator is zero")
    return float(numerator) / float(denominator)


def _execute_ratio(frame: pd.DataFrame, spec: dict[str, Any]) -> tuple[float, str, list[str]]:
    numerator_column = _column_from_spec(spec, "numerator_column", "numerator")
    denominator_column = str(spec.get("denominator_column") or spec.get("denominator") or "").strip()
    if not denominator_column:
        source_columns = _as_list(spec.get("source_columns"))
        denominator_column = source_columns[1] if len(source_columns) > 1 else ""
    if not numerator_column or not denominator_column:
        raise ValueError("ratio requires numerator_column and denominator_column")
    numerator = _numeric(frame, numerator_column).sum()
    denominator, denominator_expr, denominator_sources = _resolve_denominator_value(
        frame,
        denominator_column=denominator_column,
        denominator_mode=str(spec.get("denominator_mode") or "sum"),
        fallback_column=numerator_column,
    )
    value = _safe_divide(float(numerator), float(denominator))
    return value, f"sum({numerator_column}) / {denominator_expr}", [numerator_column, *denominator_sources]


def _execute_contribution(frame: pd.DataFrame, spec: dict[str, Any]) -> tuple[float, str, list[str]]:
    dimension_column = str(spec.get("dimension_column") or spec.get("object_column") or "").strip()
    value_column = str(spec.get("value_column") or spec.get("amount_column") or "").strip()
    source_columns = _as_list(spec.get("source_columns"))
    if not dimension_column and source_columns:
        dimension_column = source_columns[0]
    if not value_column and len(source_columns) > 1:
        value_column = source_columns[1]
    if not dimension_column or not value_column:
        raise ValueError("contribution requires dimension_column and value_column")
    values = _numeric(frame, value_column)
    grouped = pd.DataFrame({"dimension": frame[dimension_column].fillna("UNKNOWN").astype(str), "value": values})
    grouped = grouped.groupby("dimension", dropna=False)["value"].sum().sort_values(ascending=False)
    value = _safe_divide(float(grouped.head(int(spec.get("top_n") or 1)).sum()), float(grouped.sum()))
    return value, f"top{int(spec.get('top_n') or 1)}(sum({value_column}) by {dimension_column}) / sum({value_column})", [dimension_column, value_column]


def _execute_concentration(frame: pd.DataFrame, spec: dict[str, Any]) -> tuple[float, str, list[str]]:
    dimension_column = str(spec.get("dimension_column") or spec.get("object_column") or "").strip()
    value_column = str(spec.get("value_column") or spec.get("amount_column") or "").strip()
    source_columns = _as_list(spec.get("source_columns"))
    if not dimension_column and source_columns:
        dimension_column = source_columns[0]
    if not value_column and len(source_columns) > 1:
        value_column = source_columns[1]
    if not dimension_column or not value_column:
        raise ValueError("concentration requires dimension_column and value_column")
    values = _numeric(frame, value_column)
    grouped = pd.DataFrame({"dimension": frame[dimension_column].fillna("UNKNOWN").astype(str), "value": values})
    shares = grouped.groupby("dimension", dropna=False)["value"].sum()
    shares = shares / shares.sum()
    value = float((shares * shares).sum())
    return value, f"HHI(sum({value_column}) by {dimension_column})", [dimension_column, value_column]


def _execute_late_fulfillment(frame: pd.DataFrame, spec: dict[str, Any]) -> tuple[float, str, list[str]]:
    late_flag_column = str(spec.get("late_flag_column") or spec.get("is_late_column") or "").strip()
    if late_flag_column:
        late_flags = _boolean_indicator(frame, late_flag_column)
        if late_flags.notna().any():
            return float(late_flags.mean()), f"share({late_flag_column} is true)", [late_flag_column]
    delay_column = str(spec.get("delay_days_column") or spec.get("delay_column") or "").strip()
    threshold = float(spec.get("late_threshold_days") or spec.get("threshold") or 0)
    if delay_column:
        delay = _numeric(frame, delay_column)
        return float((delay > threshold).mean()), f"share({delay_column} > {threshold})", [delay_column]
    start_column = str(spec.get("start_date_column") or "").strip()
    end_column = str(spec.get("end_date_column") or "").strip()
    threshold = float(spec.get("late_threshold_days") or 7)
    if not start_column or not end_column:
        raise ValueError("late_fulfillment requires delay_days_column or start/end date columns")
    start = pd.to_datetime(frame[start_column], errors="coerce")
    end = pd.to_datetime(frame[end_column], errors="coerce")
    delay = (end - start).dt.days
    return float((delay > threshold).mean()), f"share(({end_column} - {start_column}) > {threshold} days)", [start_column, end_column]


def _execute_freight_efficiency(frame: pd.DataFrame, spec: dict[str, Any]) -> tuple[float, str, list[str]]:
    freight_column = str(spec.get("freight_column") or spec.get("cost_column") or "").strip()
    denominator_column = str(spec.get("denominator_column") or spec.get("gmv_column") or spec.get("weight_column") or "").strip()
    if not freight_column or not denominator_column:
        source_columns = _as_list(spec.get("source_columns"))
        freight_column = freight_column or (source_columns[0] if source_columns else "")
        denominator_column = denominator_column or (source_columns[1] if len(source_columns) > 1 else "")
    if not freight_column or not denominator_column:
        raise ValueError("freight_efficiency requires freight_column and denominator_column")
    denominator, denominator_expr, denominator_sources = _resolve_denominator_value(
        frame,
        denominator_column=denominator_column,
        denominator_mode=str(spec.get("denominator_mode") or "sum"),
        fallback_column=freight_column,
    )
    value = _safe_divide(float(_numeric(frame, freight_column).sum()), float(denominator))
    return value, f"sum({freight_column}) / {denominator_expr}", [freight_column, *denominator_sources]


def _execute_rating_risk(frame: pd.DataFrame, spec: dict[str, Any]) -> tuple[float, str, list[str]]:
    rating_column = str(spec.get("rating_column") or "").strip()
    if not rating_column:
        rating_column = _column_from_spec(spec, "value_column")
    threshold = float(spec.get("low_rating_threshold") or spec.get("threshold") or 3)
    rating = _numeric(frame, rating_column)
    value = float((rating <= threshold).mean())
    return value, f"share({rating_column} <= {threshold})", [rating_column]


def _execute_route_risk(frame: pd.DataFrame, spec: dict[str, Any]) -> tuple[float, str, list[str]]:
    origin_column = str(spec.get("origin_column") or spec.get("left_column") or "").strip()
    destination_column = str(spec.get("destination_column") or spec.get("right_column") or "").strip()
    value_column = str(spec.get("value_column") or spec.get("risk_column") or "").strip()
    if not origin_column or not destination_column or not value_column:
        raise ValueError("route_risk requires origin_column, destination_column, and value_column")
    values = _value_series(frame, value_column)
    route = frame[origin_column].fillna("UNKNOWN").astype(str) + "->" + frame[destination_column].fillna("UNKNOWN").astype(str)
    grouped = pd.DataFrame({"route": route, "value": values}).groupby("route", dropna=False)["value"].mean()
    return float(grouped.max()), f"max(mean({value_column}) by {origin_column}->{destination_column})", [origin_column, destination_column, value_column]


def _execute_time_trend(frame: pd.DataFrame, spec: dict[str, Any]) -> tuple[float, str, list[str]]:
    time_column = str(spec.get("time_column") or "").strip()
    value_column = str(spec.get("value_column") or spec.get("amount_column") or "").strip()
    if not time_column or not value_column:
        raise ValueError("time_trend requires time_column and value_column")
    time_values = pd.to_datetime(frame[time_column], errors="coerce")
    working = pd.DataFrame({"time": time_values, "value": _numeric(frame, value_column)}).dropna()
    if working.empty:
        raise ValueError("time_trend has no valid time/value rows")
    working["period"] = working["time"].dt.to_period(str(spec.get("time_grain") or "M")).astype(str)
    grouped = working.groupby("period")["value"].sum().sort_index()
    if len(grouped) < 2:
        raise ValueError("time_trend requires at least two periods")
    value = _safe_divide(float(grouped.iloc[-1] - grouped.iloc[0]), float(grouped.iloc[0]))
    return value, f"last(sum({value_column}) by {time_column}) / first(...) - 1", [time_column, value_column]


def _execute_top_bottom_object(frame: pd.DataFrame, spec: dict[str, Any]) -> tuple[float, str, list[str]]:
    dimension_column = str(spec.get("dimension_column") or spec.get("object_column") or "").strip()
    value_column = str(spec.get("value_column") or spec.get("amount_column") or "").strip()
    if not dimension_column or not value_column:
        raise ValueError("top_bottom_object requires dimension_column and value_column")
    grouped = pd.DataFrame(
        {"dimension": frame[dimension_column].fillna("UNKNOWN").astype(str), "value": _numeric(frame, value_column)}
    ).groupby("dimension", dropna=False)["value"].sum()
    if grouped.empty:
        raise ValueError("top_bottom_object has no valid object rows")
    value = float(grouped.max() - grouped.min())
    return value, f"max(sum({value_column}) by {dimension_column}) - min(...)", [dimension_column, value_column]


EXECUTORS = {
    "ratio": _execute_ratio,
    "contribution": _execute_contribution,
    "concentration": _execute_concentration,
    "late_fulfillment": _execute_late_fulfillment,
    "freight_efficiency": _execute_freight_efficiency,
    "rating_risk": _execute_rating_risk,
    "route_risk": _execute_route_risk,
    "time_trend": _execute_time_trend,
    "top_bottom_object": _execute_top_bottom_object,
}


def _metric_row(spec: dict[str, Any], *, value: float, formula: str, source_columns: list[str]) -> dict[str, Any]:
    family = str(spec.get("formula_family") or "").strip()
    metric_kind = str(spec.get("metric_kind") or "derived_metric").strip()
    if family in {"rating_risk"} or str(spec.get("proxy_only") or "").lower() == "true":
        metric_kind = "proxy_metric"
    metric_id = _slug(spec.get("metric_id"))
    return {
        "business_profile": "ecommerce_product_operations_report",
        "metric_id": metric_id,
        "metric_name": _reader_metric_name(metric_id, spec.get("metric_name"), family),
        "source_columns": json.dumps(source_columns, ensure_ascii=False),
        "formula": str(spec.get("formula") or formula).strip(),
        "value": round(float(value), 6),
        "evidence_level": str(spec.get("evidence_level") or ("C_PROXY" if metric_kind == "proxy_metric" else "B_DERIVED")).strip(),
        "confidence": str(spec.get("confidence") or "medium").strip().lower(),
        "metric_kind": metric_kind,
        "business_meaning": _reader_business_meaning(metric_id, spec.get("business_meaning") or spec.get("business_question"), family),
        "note": str(spec.get("note") or "由 Codex 规划并由后端确定性执行得到。").strip(),
    }


def execute_derived_metric_family_specs(workspace: Path | str) -> dict[str, Any]:
    """Execute CLI-planned ecommerce derived metric families with a deterministic whitelist."""
    workspace = Path(workspace)
    plan_path = workspace / "01c_derived_metric_family_plan.json"
    plan = _read_json(plan_path)
    frame = _load_source_frame(workspace)

    derived_rows: list[dict[str, Any]] = []
    proxy_rows: list[dict[str, Any]] = []
    unsupported_rows: list[dict[str, Any]] = []
    log_rows: list[dict[str, Any]] = []

    for spec in _specs_from_plan(plan):
        metric_id = _slug(spec.get("metric_id"))
        family = _slug(spec.get("formula_family"))
        executor = EXECUTORS.get(family)
        if family not in SUPPORTED_FORMULA_FAMILIES or executor is None:
            reason = f"unsupported_formula_family:{family}"
            unsupported_rows.append(
                {
                    "business_profile": "ecommerce_product_operations_report",
                    "metric_id": metric_id,
                    "metric_name": _reader_metric_name(metric_id, spec.get("metric_name"), family),
                    "required_fields": json.dumps(_as_list(spec.get("source_columns")), ensure_ascii=False),
                    "missing_fields": "",
                    "reason": reason,
                    "metric_kind": "unsupported_metric",
                }
            )
            log_rows.append({"metric_id": metric_id, "formula_family": family, "status": "unsupported", "reason": reason})
            continue
        try:
            value, formula, source_columns = executor(frame, spec)
            row = _metric_row(spec, value=value, formula=formula, source_columns=source_columns)
            if str(row.get("metric_kind") or "") == "proxy_metric":
                proxy_rows.append(row)
            else:
                derived_rows.append(row)
            log_rows.append({"metric_id": metric_id, "formula_family": family, "status": "completed", "reason": ""})
        except KeyError as exc:
            missing = str(exc).strip("'")
            unsupported_rows.append(
                {
                    "business_profile": "ecommerce_product_operations_report",
                    "metric_id": metric_id,
                    "metric_name": _reader_metric_name(metric_id, spec.get("metric_name"), family),
                    "required_fields": json.dumps(_as_list(spec.get("source_columns")), ensure_ascii=False),
                    "missing_fields": missing,
                    "reason": "missing_required_field",
                    "metric_kind": "unsupported_metric",
                }
            )
            log_rows.append({"metric_id": metric_id, "formula_family": family, "status": "unsupported", "reason": f"missing field {missing}"})
        except Exception as exc:
            unsupported_rows.append(
                {
                    "business_profile": "ecommerce_product_operations_report",
                    "metric_id": metric_id,
                    "metric_name": _reader_metric_name(metric_id, spec.get("metric_name"), family),
                    "required_fields": json.dumps(_as_list(spec.get("source_columns")), ensure_ascii=False),
                    "missing_fields": "",
                    "reason": str(exc),
                    "metric_kind": "unsupported_metric",
                }
            )
            log_rows.append({"metric_id": metric_id, "formula_family": family, "status": "unsupported", "reason": str(exc)})

    derived_path = workspace / "01c_derived_metrics_table.csv"
    proxy_path = workspace / "01c_proxy_metrics_table.csv"
    unsupported_path = workspace / "01c_unsupported_metrics_table.csv"
    log_path = workspace / "01c_derived_metric_execution_log.csv"
    summary_path = workspace / "01c_derived_metric_family_execution.json"

    metric_columns = [
        "business_profile",
        "metric_id",
        "metric_name",
        "source_columns",
        "formula",
        "value",
        "evidence_level",
        "confidence",
        "metric_kind",
        "business_meaning",
        "note",
    ]
    unsupported_columns = [
        "business_profile",
        "metric_id",
        "metric_name",
        "required_fields",
        "missing_fields",
        "reason",
        "metric_kind",
    ]
    log_columns = ["metric_id", "formula_family", "status", "reason"]

    _write_csv(derived_path, derived_rows, columns=metric_columns)
    _write_csv(proxy_path, proxy_rows, columns=metric_columns)
    _write_csv(unsupported_path, unsupported_rows, columns=unsupported_columns)
    _write_csv(log_path, log_rows, columns=log_columns)
    payload = {
        "derived_metric_family_count": len(_specs_from_plan(plan)),
        "derived_metric_family_executed_count": len(derived_rows) + len(proxy_rows),
        "derived_metric_family_unsupported_count": len(unsupported_rows),
        "derived_metrics_table_path": derived_path.name,
        "proxy_metrics_table_path": proxy_path.name,
        "unsupported_metrics_table_path": unsupported_path.name,
        "execution_log_path": log_path.name,
        "supported_formula_families": sorted(SUPPORTED_FORMULA_FAMILIES),
    }
    _write_json(summary_path, payload)
    return payload
