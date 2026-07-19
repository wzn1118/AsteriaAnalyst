from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _normalize(value: Any) -> str:
    return "".join(ch for ch in _safe_text(value).lower() if ch.isalnum() or "\u4e00" <= ch <= "\u9fff")


def _resolve_column(frame: pd.DataFrame, value: Any) -> str | None:
    text = _safe_text(value)
    if not text:
        return None
    if text in frame.columns:
        return text
    normalized = _normalize(text)
    for column in frame.columns.astype(str):
        if _normalize(column) == normalized:
            return column
    return None


def _numeric(frame: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(frame[column], errors="coerce")


def _source_columns(frame: pd.DataFrame, spec: dict[str, Any]) -> list[str]:
    values = list(spec.get("source_columns") or spec.get("columns") or [])
    resolved: list[str] = []
    for value in values:
        column = _resolve_column(frame, value)
        if column and column not in resolved:
            resolved.append(column)
    return resolved


def _selected_values(spec: dict[str, Any]) -> list[str]:
    return [_safe_text(value).lower() for value in spec.get("selected_values") or [] if _safe_text(value)]


def _count_selected(frame: pd.DataFrame, columns: list[str], spec: dict[str, Any]) -> pd.Series:
    selected = _selected_values(spec)
    result = pd.Series(0, index=frame.index, dtype="float64")
    for column in columns:
        text = frame[column].fillna("").astype(str).str.lower()
        if selected:
            result = result + text.apply(lambda value: 1 if any(item in value for item in selected) else 0)
        else:
            result = result + text.apply(lambda value: 1 if value.strip() else 0)
    return result


def _weighted_score(frame: pd.DataFrame, columns: list[str], spec: dict[str, Any]) -> pd.Series:
    weights_raw = spec.get("weights") or {}
    weights: dict[str, float] = {}
    if isinstance(weights_raw, dict):
        for key, value in weights_raw.items():
            column = _resolve_column(frame, key)
            if not column:
                continue
            try:
                weights[column] = float(value)
            except Exception:
                continue
    if not weights:
        weights = {column: 1.0 for column in columns}
    numerator = pd.Series(0.0, index=frame.index)
    denominator = pd.Series(0.0, index=frame.index)
    for column in columns:
        series = _numeric(frame, column)
        weight = weights.get(column, 1.0)
        valid = series.notna()
        numerator = numerator + series.fillna(0.0) * weight
        denominator = denominator + valid.astype(float) * abs(weight)
    return numerator / denominator.replace({0.0: pd.NA})


def _ratio_metric(frame: pd.DataFrame, spec: dict[str, Any]) -> tuple[pd.Series, list[str], str]:
    numerator_cols = [
        column
        for column in (_resolve_column(frame, value) for value in spec.get("numerator_columns") or [])
        if column
    ]
    denominator_cols = [
        column
        for column in (_resolve_column(frame, value) for value in spec.get("denominator_columns") or [])
        if column
    ]
    if not numerator_cols or not denominator_cols:
        columns = _source_columns(frame, spec)
        if len(columns) >= 2:
            numerator_cols = [columns[0]]
            denominator_cols = [columns[1]]
    if not numerator_cols or not denominator_cols:
        raise ValueError("ratio metric requires numerator_columns and denominator_columns")
    numerator = sum((_numeric(frame, column).fillna(0.0) for column in numerator_cols), pd.Series(0.0, index=frame.index))
    denominator = sum((_numeric(frame, column).fillna(0.0) for column in denominator_cols), pd.Series(0.0, index=frame.index))
    return numerator / denominator.replace({0.0: pd.NA}), [*numerator_cols, *denominator_cols], f"sum({'+'.join(numerator_cols)}) / sum({'+'.join(denominator_cols)})"


def _execute_metric(frame: pd.DataFrame, spec: dict[str, Any]) -> tuple[pd.Series, list[str], str]:
    columns = _source_columns(frame, spec)
    metric_type = _safe_text(spec.get("metric_type") or spec.get("type") or spec.get("aggregation")).lower()
    aggregation = _safe_text(spec.get("aggregation") or "").lower()
    metric_id = _safe_text(spec.get("metric_id") or spec.get("name")).lower()
    if metric_type == "ratio" or aggregation == "ratio":
        return _ratio_metric(frame, spec)
    if not columns:
        raise ValueError("no source columns resolved")
    if metric_type in {"count_selected", "strategy_count", "channel_count"} or aggregation in {"count_selected", "count_non_empty"} or metric_id.endswith("_count"):
        return _count_selected(frame, columns, spec), columns, f"count_selected({', '.join(columns)})"
    if metric_type in {"weighted_score", "composite_score"} or aggregation in {"weighted_mean", "mean", "average"}:
        return _weighted_score(frame, columns, spec), columns, f"weighted_mean({', '.join(columns)})"
    if aggregation == "sum" or metric_type in {"sum_score", "score_sum"}:
        numeric_frame = pd.DataFrame({column: _numeric(frame, column) for column in columns})
        return numeric_frame.sum(axis=1, min_count=1), columns, f"sum({', '.join(columns)})"
    numeric_frame = pd.DataFrame({column: _numeric(frame, column) for column in columns})
    return numeric_frame.mean(axis=1, skipna=True), columns, f"mean({', '.join(columns)})"


def _read_specs(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(payload, dict):
        metrics = payload.get("custom_metrics") or payload.get("metrics") or []
    elif isinstance(payload, list):
        metrics = payload
    else:
        metrics = []
    return [dict(item) for item in metrics if isinstance(item, dict)]


def execute_custom_metric_specs(
    *,
    workspace_path: str | Path,
    source_dataset_path: str | Path,
    specs_path: str | Path,
) -> dict[str, Any]:
    workspace = Path(workspace_path).expanduser().resolve()
    source_path = Path(source_dataset_path).expanduser().resolve()
    specs_file = Path(specs_path).expanduser().resolve()
    workspace.mkdir(parents=True, exist_ok=True)

    values_path = workspace / "custom_metric_values.csv"
    dataset_path = workspace / "custom_metrics_dataset.csv"
    log_path = workspace / "custom_metric_log.csv"
    json_path = workspace / "03_custom_metric_execution.json"
    md_path = workspace / "03_custom_metric_execution.md"

    if not source_path.exists():
        raise FileNotFoundError(f"source dataset not found: {source_path}")
    if not specs_file.exists():
        raise FileNotFoundError(f"custom metric specs not found: {specs_file}")

    frame = pd.read_csv(source_path, encoding="utf-8-sig")
    specs = _read_specs(specs_file)
    enriched = frame.copy()
    value_rows: list[dict[str, Any]] = []
    log_rows: list[dict[str, Any]] = []

    for index, spec in enumerate(specs, 1):
        metric_id = _safe_text(spec.get("metric_id") or spec.get("name") or f"custom_metric_{index:02d}")
        metric_name = _safe_text(spec.get("metric_name") or spec.get("name") or metric_id)
        if not metric_id:
            continue
        try:
            series, resolved_columns, formula = _execute_metric(enriched, spec)
            enriched[metric_id] = series
            valid = pd.to_numeric(series, errors="coerce").dropna()
            status = "completed" if not valid.empty else "skipped"
            reason = "" if not valid.empty else "metric produced no numeric values"
            value_rows.append(
                {
                    "metric_id": metric_id,
                    "metric_name": metric_name,
                    "metric_type": _safe_text(spec.get("metric_type") or spec.get("type") or spec.get("aggregation")),
                    "source_columns": ";".join(resolved_columns),
                    "formula": _safe_text(spec.get("formula") or formula),
                    "valid_n": int(valid.shape[0]),
                    "mean": float(valid.mean()) if not valid.empty else "",
                    "median": float(valid.median()) if not valid.empty else "",
                    "min": float(valid.min()) if not valid.empty else "",
                    "max": float(valid.max()) if not valid.empty else "",
                    "status": status,
                    "reason": reason,
                }
            )
            log_rows.append(
                {
                    "metric_id": metric_id,
                    "status": status,
                    "reason": reason,
                    "source_columns": ";".join(resolved_columns),
                }
            )
        except Exception as exc:
            log_rows.append(
                {
                    "metric_id": metric_id,
                    "status": "error",
                    "reason": str(exc),
                    "source_columns": ";".join(_source_columns(enriched, spec)),
                }
            )

    pd.DataFrame(value_rows).to_csv(values_path, index=False, encoding="utf-8-sig")
    pd.DataFrame(log_rows).to_csv(log_path, index=False, encoding="utf-8-sig")
    enriched.to_csv(dataset_path, index=False, encoding="utf-8-sig")

    completed = [row for row in log_rows if row.get("status") == "completed"]
    payload = {
        "source_dataset_path": str(source_path),
        "specs_path": str(specs_file),
        "custom_metric_count": len(specs),
        "completed_metric_count": len(completed),
        "value_table_path": str(values_path.resolve()),
        "enhanced_dataset_path": str(dataset_path.resolve()),
        "log_path": str(log_path.resolve()),
        "metrics": value_rows,
        "log": log_rows,
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(
        "\n".join(
            [
                "# custom metric execution",
                "",
                f"- source dataset: `{source_path.name}`",
                f"- custom metric specs: `{specs_file.name}`",
                f"- metric specs: {len(specs)}",
                f"- completed metrics: {len(completed)}",
                f"- enhanced dataset: `{dataset_path.name}`",
                f"- values table: `{values_path.name}`",
                f"- execution log: `{log_path.name}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return payload
