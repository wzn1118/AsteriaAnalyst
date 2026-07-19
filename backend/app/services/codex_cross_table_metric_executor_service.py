from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _as_list(value: Any) -> list[Any]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return value
    return [value]


def _ref_column_name(value: Any) -> str:
    if isinstance(value, dict):
        for key in ("column_name", "column", "field", "source_column", "name"):
            text = _safe_text(value.get(key))
            if text:
                return text
        return ""
    return _safe_text(value)


def _ref_table_id(value: Any) -> str:
    if isinstance(value, dict):
        for key in ("table_id", "table", "source_table"):
            text = _safe_text(value.get(key))
            if text:
                return text
    return ""


def _normalize(value: Any) -> str:
    return "".join(ch for ch in _safe_text(value).lower() if ch.isalnum() or "\u4e00" <= ch <= "\u9fff")


def _json_safe(value: Any) -> Any:
    if pd.isna(value):
        return ""
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return value


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _read_specs(path: Path) -> list[dict[str, Any]]:
    payload = _load_json(path)
    specs = payload.get("metric_specs") or payload.get("cross_table_metrics") or payload.get("metrics") or []
    return [dict(item) for item in specs if isinstance(item, dict)]


def _discover_table_paths(workspace: Path) -> dict[str, Path]:
    tables_dir = workspace / "tables"
    discovered: dict[str, Path] = {}
    if not tables_dir.exists():
        return discovered
    for table_dir in sorted(item for item in tables_dir.iterdir() if item.is_dir()):
        table_path = table_dir / "source_table.csv"
        sample_path = table_dir / "source_sample.csv"
        if table_path.exists():
            discovered[table_dir.name] = table_path
        elif sample_path.exists():
            discovered[table_dir.name] = sample_path
    return discovered


def _resolve_table(table_paths: dict[str, Path], value: Any) -> tuple[str, Path] | None:
    text = _safe_text(value)
    if not text:
        return None
    if text in table_paths:
        return text, table_paths[text]
    normalized = _normalize(text)
    for table_id, path in table_paths.items():
        if _normalize(table_id) == normalized:
            return table_id, path
    return None


def _resolve_column(frame: pd.DataFrame, value: Any) -> str | None:
    text = _ref_column_name(value)
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


def _metric_id(spec: dict[str, Any], index: int) -> str:
    return _safe_text(spec.get("metric_id") or spec.get("name") or f"cross_table_metric_{index:02d}")


def _operation(spec: dict[str, Any]) -> str:
    return _safe_text(spec.get("operation") or spec.get("aggregation") or spec.get("metric_type")).lower()


def _aggregate_value(
    frame: pd.DataFrame,
    *,
    operation: str,
    value_column: str | None = None,
    numerator_column: str | None = None,
    denominator_column: str | None = None,
    numerator_operation: str = "sum",
    denominator_operation: str = "sum",
) -> tuple[Any, str]:
    if operation in {"", "row_count", "count_rows", "count"}:
        return int(frame.shape[0]), "row_count"
    if operation in {"nunique", "count_distinct"}:
        if not value_column:
            return "", "count_distinct requires value_column"
        return int(frame[value_column].nunique(dropna=True)), f"nunique({value_column})"
    if operation == "ratio":
        if not numerator_column or not denominator_column:
            return "", "ratio requires numerator_column and denominator_column"
        numerator_series = _numeric(frame, numerator_column)
        numerator_value = numerator_series.sum() if numerator_operation in {"", "sum"} else numerator_series.mean()
        denominator_op = denominator_operation or "sum"
        if denominator_op in {"row_count", "count_rows", "count"}:
            denominator_value = frame.shape[0]
        else:
            denominator_series = _numeric(frame, denominator_column)
            denominator_value = denominator_series.sum() if denominator_op == "sum" else denominator_series.mean()
        if not denominator_value:
            return "", "ratio denominator is zero"
        return float(numerator_value / denominator_value), f"{numerator_operation or 'sum'}({numerator_column}) / {denominator_op}({denominator_column})"
    if operation in {"sum", "mean", "average", "median", "min", "max"}:
        if not value_column:
            return "", f"{operation} requires value_column"
        numeric = _numeric(frame, value_column).dropna()
        if numeric.empty:
            return "", f"{value_column} has no numeric values"
        if operation == "sum":
            return float(numeric.sum()), f"sum({value_column})"
        if operation in {"mean", "average"}:
            return float(numeric.mean()), f"mean({value_column})"
        if operation == "median":
            return float(numeric.median()), f"median({value_column})"
        if operation == "min":
            return float(numeric.min()), f"min({value_column})"
        return float(numeric.max()), f"max({value_column})"
    return "", f"unsupported safe operation: {operation}"


def _group_values(
    frame: pd.DataFrame,
    group_columns: list[str],
    value_column: str | None,
    operation: str,
    *,
    numerator_column: str | None = None,
    denominator_column: str | None = None,
    numerator_operation: str = "sum",
    denominator_operation: str = "sum",
) -> list[dict[str, Any]]:
    grouped = frame.groupby(group_columns[0] if len(group_columns) == 1 else group_columns, dropna=False)
    rows: list[dict[str, Any]] = []
    for group_value, group_frame in grouped:
        if not isinstance(group_value, tuple):
            group_value = (group_value,)
        row: dict[str, Any] = {
            "group": " | ".join(str(item) for item in group_value),
            "groups": {column: group_value[idx] for idx, column in enumerate(group_columns)},
            "n": int(group_frame.shape[0]),
        }
        value, formula = _aggregate_value(
            group_frame,
            operation=operation,
            value_column=value_column,
            numerator_column=numerator_column,
            denominator_column=denominator_column,
            numerator_operation=numerator_operation,
            denominator_operation=denominator_operation,
        )
        row["value"] = value
        row["formula"] = formula
        rows.append(row)
    rows.sort(key=lambda item: float(item.get("value") or item.get("n") or 0), reverse=True)
    return rows


def _preview_rows(rows: list[dict[str, Any]], *, limit: int = 12) -> list[dict[str, Any]]:
    return rows[: max(0, limit)]


def _column_token(column: Any) -> str:
    return _normalize(column)


def _looks_like_id_column(column: Any) -> bool:
    token = _column_token(column)
    return any(marker in token for marker in ("id", "code", "编号", "编码", "代码", "统一", "信用"))


def _looks_like_time_column(column: Any) -> bool:
    token = _column_token(column)
    return any(marker in token for marker in ("年度", "年份", "年", "year", "date", "日期", "time", "period"))


def _looks_like_label_column(column: Any) -> bool:
    token = _column_token(column)
    if any(marker in token for marker in ("简介", "描述", "说明", "description", "remark", "memo")):
        return False
    return any(marker in token for marker in ("名称", "姓名", "name", "title", "label"))


def _identity_columns(frame: pd.DataFrame) -> dict[str, str]:
    columns = [str(column) for column in frame.columns]
    id_columns = [column for column in columns if _looks_like_id_column(column)]
    label_columns = [column for column in columns if _looks_like_label_column(column)]
    time_columns = [column for column in columns if _looks_like_time_column(column)]

    def column_score(column: str, *, prefer_unique: bool = True) -> tuple[float, int]:
        series = frame[column].dropna().astype(str)
        unique_count = int(series.nunique())
        ratio = unique_count / max(len(series), 1)
        avg_len = float(series.str.len().mean() or 0)
        uniqueness_score = 1.0 - abs(0.95 - ratio) if prefer_unique else 1.0 - abs(0.35 - ratio)
        long_text_penalty = 0.35 if avg_len > 80 else 0.0
        return (uniqueness_score - long_text_penalty, unique_count)

    id_column = ""
    if id_columns:
        id_column = sorted(id_columns, key=lambda col: column_score(col), reverse=True)[0]

    label_column = ""
    if label_columns:
        # Avoid row-level free-text names when a stable id exists; prefer labels that
        # repeat at the same object grain as the id column.
        if id_column:
            id_unique = max(int(frame[id_column].dropna().astype(str).nunique()), 1)
            label_columns = sorted(
                label_columns,
                key=lambda col: (
                    -abs(int(frame[col].dropna().astype(str).nunique()) - id_unique),
                    -float(frame[col].dropna().astype(str).str.len().mean() or 0),
                ),
            )
        else:
            label_columns = sorted(label_columns, key=lambda col: column_score(col), reverse=True)
        label_column = label_columns[0]

    time_column = ""
    if time_columns:
        time_column = sorted(
            time_columns,
            key=lambda col: (
                int(frame[col].dropna().astype(str).nunique()),
                -len(str(col)),
            ),
        )[0]
    return {"id_column": id_column, "label_column": label_column, "time_column": time_column}


def _object_key_from_row(row: pd.Series, identity: dict[str, str]) -> str:
    parts: list[str] = []
    id_column = identity.get("id_column") or ""
    label_column = identity.get("label_column") or ""
    time_column = identity.get("time_column") or ""
    if id_column:
        parts.append(_safe_text(row.get(id_column)))
    elif label_column:
        parts.append(_safe_text(row.get(label_column)))
    if time_column:
        parts.append(_safe_text(row.get(time_column)))
    if not any(parts):
        parts = [_safe_text(value) for value in row.tolist()[:3]]
    return " | ".join(part for part in parts if part)


def _object_label_from_row(row: pd.Series, identity: dict[str, str], fallback_key: str) -> str:
    label_column = identity.get("label_column") or ""
    time_column = identity.get("time_column") or ""
    label = _safe_text(row.get(label_column)) if label_column else fallback_key
    time_value = _safe_text(row.get(time_column)) if time_column else ""
    if time_value and time_value not in label:
        return f"{label} | {time_value}"
    return label or fallback_key


def _object_rows(frame: pd.DataFrame, identity: dict[str, str], *, table_id: str) -> list[dict[str, Any]]:
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    for _, source_row in frame.iterrows():
        object_key = _object_key_from_row(source_row, identity)
        if not object_key or object_key in seen:
            continue
        seen.add(object_key)
        rows.append(
            {
                "object_key": object_key,
                "object_label": _object_label_from_row(source_row, identity, object_key),
                "table_id": table_id,
                "id_value": _safe_text(source_row.get(identity.get("id_column") or "")),
                "label_value": _safe_text(source_row.get(identity.get("label_column") or "")),
                "time_value": _safe_text(source_row.get(identity.get("time_column") or "")),
            }
        )
    return rows


def _table_identity_score(frame: pd.DataFrame, identity: dict[str, str]) -> tuple[int, int, int, int]:
    rows = _object_rows(frame, identity, table_id="")
    has_id = 1 if identity.get("id_column") else 0
    has_label = 1 if identity.get("label_column") else 0
    # Prefer object-level tables over event/detail tables: enough objects, fewer
    # duplicate source rows per object, and stable id/label columns.
    duplicate_penalty = int(frame.shape[0] / max(len(rows), 1))
    return (has_id, has_label, len(rows), -duplicate_penalty)


def _build_generic_object_universe(workspace: Path, table_frames: dict[str, pd.DataFrame]) -> dict[str, Any]:
    identities = {table_id: _identity_columns(frame) for table_id, frame in table_frames.items()}
    scored_tables = [
        (table_id, _table_identity_score(frame, identities[table_id]))
        for table_id, frame in table_frames.items()
        if not frame.empty
    ]
    scored_tables.sort(key=lambda item: item[1], reverse=True)
    primary_table_id = scored_tables[0][0] if scored_tables else ""
    if not primary_table_id:
        payload = {
            "version": "generic_object_universe_v1",
            "primary_table_id": "",
            "object_count": 0,
            "coverage": [],
            "object_key_fields": [],
            "time_fields": [],
            "rows": [],
        }
        (workspace / "generic_object_universe.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        pd.DataFrame().to_csv(workspace / "generic_object_universe.csv", index=False, encoding="utf-8-sig")
        return payload

    primary_identity = identities[primary_table_id]
    primary_rows = _object_rows(table_frames[primary_table_id], primary_identity, table_id=primary_table_id)
    primary_keys = {row["object_key"] for row in primary_rows}
    coverage: list[dict[str, Any]] = []
    table_key_sets: dict[str, set[str]] = {}
    for table_id, frame in table_frames.items():
        rows = _object_rows(frame, identities[table_id], table_id=table_id)
        keys = {row["object_key"] for row in rows}
        table_key_sets[table_id] = keys
        overlap = len(primary_keys & keys)
        coverage.append(
            {
                "table_id": table_id,
                "source_row_count": int(frame.shape[0]),
                "object_count": len(keys),
                "overlap_with_primary": overlap,
                "overlap_rate": float(overlap / max(len(primary_keys), 1)),
                "id_column": identities[table_id].get("id_column") or "",
                "label_column": identities[table_id].get("label_column") or "",
                "time_column": identities[table_id].get("time_column") or "",
            }
        )

    universe_rows: list[dict[str, Any]] = []
    for index, row in enumerate(primary_rows, start=1):
        present_tables = [table_id for table_id, keys in table_key_sets.items() if row["object_key"] in keys]
        missing_tables = [table_id for table_id in table_frames if table_id not in present_tables]
        universe_rows.append(
            {
                "object_index": index,
                "object_key": row["object_key"],
                "object_label": row["object_label"],
                "primary_table_id": primary_table_id,
                "present_tables": ";".join(present_tables),
                "missing_tables": ";".join(missing_tables),
                "missing_detail_reason": "missing from " + ";".join(missing_tables) if missing_tables else "",
                "id_value": row.get("id_value") or "",
                "label_value": row.get("label_value") or "",
                "time_value": row.get("time_value") or "",
            }
        )
    payload = {
        "version": "generic_object_universe_v1",
        "primary_table_id": primary_table_id,
        "object_count": len(universe_rows),
        "object_key_fields": [value for value in [primary_identity.get("id_column"), primary_identity.get("label_column")] if value],
        "time_fields": [primary_identity["time_column"]] if primary_identity.get("time_column") else [],
        "coverage": coverage,
        "rows": universe_rows,
        "csv_path": str((workspace / "generic_object_universe.csv").resolve()),
    }
    (workspace / "generic_object_universe.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.DataFrame(universe_rows).to_csv(workspace / "generic_object_universe.csv", index=False, encoding="utf-8-sig")
    return payload


def _load_table_frames(table_paths: dict[str, Path]) -> dict[str, pd.DataFrame]:
    frames: dict[str, pd.DataFrame] = {}
    for table_id, table_path in table_paths.items():
        try:
            frames[table_id] = pd.read_csv(table_path, encoding="utf-8-sig")
        except Exception:
            continue
    return frames


def _pick_join_key(left: pd.DataFrame, right: pd.DataFrame) -> str | None:
    common = [str(column) for column in left.columns if str(column) in set(right.columns.astype(str))]
    id_like = [column for column in common if column.lower().endswith("_id") or column.lower() == "id"]
    return (id_like or common or [None])[0]


def _resolve_ref_column(
    frame: pd.DataFrame,
    *,
    source_table_id: str,
    ref: Any,
) -> str | None:
    column_name = _ref_column_name(ref)
    table_id = _ref_table_id(ref)
    if table_id and _normalize(table_id) != _normalize(source_table_id):
        merged_column = f"{table_id}__{column_name}"
        if merged_column in frame.columns:
            return merged_column
    return _resolve_column(frame, column_name)


def _prepare_execution_frame(
    *,
    source_table_id: str,
    source_frame: pd.DataFrame,
    table_frames: dict[str, pd.DataFrame],
    spec: dict[str, Any],
) -> tuple[pd.DataFrame, list[str]]:
    frame = source_frame.copy()
    notes: list[str] = []
    refs: list[Any] = []
    refs.extend(
        [
            spec.get("value_column"),
            spec.get("numerator_column"),
            spec.get("denominator_column"),
            spec.get("time_bucket"),
        ]
    )
    refs.extend(_as_list(spec.get("group_by")))
    refs.extend(_as_list(spec.get("group_by_derived")))

    target_table_ids = [
        _ref_table_id(ref)
        for ref in refs
        if _ref_table_id(ref) and _normalize(_ref_table_id(ref)) != _normalize(source_table_id)
    ]
    for target_table_id in dict.fromkeys(target_table_ids):
        target_frame = table_frames.get(target_table_id)
        if target_frame is None:
            notes.append(f"join skipped: target table not found {target_table_id}")
            continue
        join_key = _pick_join_key(frame, target_frame)
        if not join_key:
            notes.append(f"join skipped: no deterministic common key for {target_table_id}")
            continue
        rename_map = {
            str(column): f"{target_table_id}__{column}"
            for column in target_frame.columns
            if str(column) != join_key
        }
        right = target_frame.rename(columns=rename_map)
        before_rows = frame.shape[0]
        frame = frame.merge(right, how="left", on=join_key)
        notes.append(f"joined {target_table_id} on {join_key}; rows {before_rows}->{frame.shape[0]}")

    for time_bucket in _as_list(spec.get("time_bucket")):
        time_column = _resolve_ref_column(frame, source_table_id=source_table_id, ref=time_bucket)
        if not time_column:
            continue
        grain = _safe_text(time_bucket.get("grain") if isinstance(time_bucket, dict) else "month") or "month"
        derived_name = f"{time_column}_{grain}"
        dates = pd.to_datetime(frame[time_column], errors="coerce")
        if grain == "week":
            frame[derived_name] = dates.dt.to_period("W").astype(str)
        elif grain == "day":
            frame[derived_name] = dates.dt.date.astype(str)
        else:
            frame[derived_name] = dates.dt.to_period("M").astype(str)
        notes.append(f"derived time bucket {derived_name}")

    for derived in _as_list(spec.get("group_by_derived")):
        if not isinstance(derived, dict):
            continue
        if _safe_text(derived.get("derivation_rule")) != "deterministic_quartile_band":
            continue
        base_column = _resolve_ref_column(frame, source_table_id=source_table_id, ref=derived)
        derived_name = _safe_text(derived.get("derived_name") or f"{base_column}_q4")
        if not base_column or not derived_name:
            continue
        numeric = _numeric(frame, base_column)
        try:
            frame[derived_name] = pd.qcut(numeric.rank(method="first"), q=4, labels=["Q1_low", "Q2_mid_low", "Q3_mid_high", "Q4_high"])
        except Exception:
            frame[derived_name] = pd.cut(numeric, bins=4, labels=["Q1_low", "Q2_mid_low", "Q3_mid_high", "Q4_high"])
        notes.append(f"derived quartile band {derived_name} from {base_column}")

    return frame, notes


def _execute_single_table_metric(
    *,
    table_id: str,
    frame: pd.DataFrame,
    table_frames: dict[str, pd.DataFrame],
    spec: dict[str, Any],
) -> tuple[str, Any, list[dict[str, Any]], str]:
    operation = _operation(spec)
    frame, preparation_notes = _prepare_execution_frame(
        source_table_id=table_id,
        source_frame=frame,
        table_frames=table_frames,
        spec=spec,
    )
    if operation in {"", "row_count", "count_rows"} and not spec.get("group_by") and not spec.get("time_bucket"):
        return "completed", int(frame.shape[0]), [], "row_count"

    group_columns = [
        column
        for column in (
            _resolve_ref_column(frame, source_table_id=table_id, ref=group_ref)
            for group_ref in _as_list(spec.get("group_by") or spec.get("dimension"))
        )
        if column
    ]
    for time_bucket in _as_list(spec.get("time_bucket")):
        time_column = _resolve_ref_column(frame, source_table_id=table_id, ref=time_bucket)
        grain = _safe_text(time_bucket.get("grain") if isinstance(time_bucket, dict) else "month") or "month"
        derived_name = f"{time_column}_{grain}" if time_column else ""
        if derived_name and derived_name in frame.columns:
            group_columns.append(derived_name)
    for derived in _as_list(spec.get("group_by_derived")):
        derived_name = _safe_text(derived.get("derived_name") if isinstance(derived, dict) else "")
        if derived_name and derived_name in frame.columns:
            group_columns.append(derived_name)

    value_column = _resolve_ref_column(
        frame,
        source_table_id=table_id,
        ref=spec.get("value_column") or spec.get("measure") or spec.get("source_column"),
    )
    numerator = _resolve_ref_column(frame, source_table_id=table_id, ref=spec.get("numerator_column"))
    denominator = _resolve_ref_column(frame, source_table_id=table_id, ref=spec.get("denominator_column"))
    numerator_operation = _safe_text(spec.get("numerator_operation") or "sum").lower()
    denominator_operation = _safe_text(spec.get("denominator_operation") or "sum").lower()

    if group_columns:
        detail_rows = _group_values(
            frame,
            group_columns,
            value_column,
            operation,
            numerator_column=numerator,
            denominator_column=denominator,
            numerator_operation=numerator_operation,
            denominator_operation=denominator_operation,
        )
        if not detail_rows:
            return "skipped", "", [], "groupby produced no rows"
        return "completed", "", detail_rows, "; ".join([*preparation_notes, f"groupby({', '.join(group_columns)})"]).strip("; ")

    value, formula = _aggregate_value(
        frame,
        operation=operation,
        value_column=value_column,
        numerator_column=numerator,
        denominator_column=denominator,
        numerator_operation=numerator_operation,
        denominator_operation=denominator_operation,
    )
    if value == "":
        return "skipped", "", [], formula
    return "completed", value, [], "; ".join([*preparation_notes, formula]).strip("; ")


def execute_cross_table_metric_specs(
    *,
    workspace_path: str | Path,
    specs_path: str | Path,
) -> dict[str, Any]:
    workspace = Path(workspace_path).expanduser().resolve()
    specs_file = Path(specs_path).expanduser().resolve()
    workspace.mkdir(parents=True, exist_ok=True)

    md_path = workspace / "04_cross_table_metric_execution.md"
    json_path = workspace / "04_cross_table_metric_execution.json"
    values_path = workspace / "cross_table_metric_values.csv"
    dataset_index_path = workspace / "cross_table_enhanced_dataset_index.json"
    log_path = workspace / "cross_table_metric_log.csv"
    object_universe_json_path = workspace / "generic_object_universe.json"
    object_universe_csv_path = workspace / "generic_object_universe.csv"

    if not specs_file.exists():
        raise FileNotFoundError(f"cross-table metric specs not found: {specs_file}")

    table_paths = _discover_table_paths(workspace)
    table_frames = _load_table_frames(table_paths)
    object_universe = _build_generic_object_universe(workspace, table_frames)
    specs = _read_specs(specs_file)
    value_rows: list[dict[str, Any]] = []
    log_rows: list[dict[str, Any]] = []
    dataset_index: list[dict[str, Any]] = []

    for table_id, sample_path in table_paths.items():
        dataset_index.append(
            {
                "table_id": table_id,
                "sample_path": str(sample_path.resolve()),
                "enhanced_path": "",
                "status": "source_sample_registered",
            }
        )

    for index, spec in enumerate(specs, 1):
        metric_id = _metric_id(spec, index)
        table_value = spec.get("table") or spec.get("source_table") or (spec.get("required_tables") or [""])[0]
        join_path = spec.get("join_path") or spec.get("join_paths") or spec.get("relationship")
        if join_path:
            reason = "join metrics are deferred until the relationship model is deterministically confirmed"
            log_rows.append({"metric_id": metric_id, "status": "skipped", "reason": reason, "table_id": _safe_text(table_value)})
            continue
        resolved_table = _resolve_table(table_paths, table_value)
        if not resolved_table:
            reason = f"source table not found or not specified: {_safe_text(table_value)}"
            log_rows.append({"metric_id": metric_id, "status": "skipped", "reason": reason, "table_id": _safe_text(table_value)})
            continue
        table_id, table_path = resolved_table
        try:
            frame = table_frames.get(table_id)
            if frame is None:
                frame = pd.read_csv(table_path, encoding="utf-8-sig")
            status, value, detail_rows, formula = _execute_single_table_metric(
                table_id=table_id,
                frame=frame,
                table_frames=table_frames,
                spec=spec,
            )
            value_rows.append(
                {
                    "metric_id": metric_id,
                    "metric_name": _safe_text(spec.get("metric_name") or spec.get("name") or metric_id),
                    "table_id": table_id,
                    "operation": _operation(spec),
                    "value": value,
                    "detail_rows_json": json.dumps(detail_rows, ensure_ascii=False),
                    "detail_preview_rows_json": json.dumps(_preview_rows(detail_rows), ensure_ascii=False),
                    "detail_row_count": len(detail_rows),
                    "formula": formula,
                    "status": status,
                    "reason": "" if status == "completed" else formula,
                }
            )
            log_rows.append(
                {
                    "metric_id": metric_id,
                    "status": status,
                    "reason": "" if status == "completed" else formula,
                    "table_id": table_id,
                }
            )
        except Exception as exc:
            log_rows.append({"metric_id": metric_id, "status": "error", "reason": str(exc), "table_id": table_id})

    pd.DataFrame(value_rows).to_csv(values_path, index=False, encoding="utf-8-sig")
    pd.DataFrame(log_rows).to_csv(log_path, index=False, encoding="utf-8-sig")
    dataset_index_path.write_text(json.dumps({"tables": dataset_index}, ensure_ascii=False, indent=2), encoding="utf-8")

    completed = [row for row in log_rows if row.get("status") == "completed"]
    payload = {
        "specs_path": str(specs_file),
        "metric_spec_count": len(specs),
        "completed_metric_count": len(completed),
        "value_table_path": str(values_path.resolve()),
        "enhanced_dataset_index_path": str(dataset_index_path.resolve()),
        "log_path": str(log_path.resolve()),
        "object_universe_path": str(object_universe_json_path.resolve()),
        "object_universe_csv_path": str(object_universe_csv_path.resolve()),
        "object_universe_count": int(object_universe.get("object_count") or 0),
        "values": value_rows,
        "log": log_rows,
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(
        "\n".join(
            [
                "# cross-table metric execution",
                "",
                f"- cross-table metric specs: `{specs_file.name}`",
                f"- metric specs: {len(specs)}",
                f"- completed metrics: {len(completed)}",
                f"- registered source tables: {len(table_paths)}",
                f"- values table: `{values_path.name}`",
                f"- object universe: `{object_universe_csv_path.name}` ({int(object_universe.get('object_count') or 0)} objects)",
                f"- dataset index: `{dataset_index_path.name}`",
                f"- execution log: `{log_path.name}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return payload
