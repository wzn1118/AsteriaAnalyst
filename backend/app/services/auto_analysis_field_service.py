from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from app.services.auto_analysis_registry_service import load_auto_analysis_specs


def _zh(value: str) -> str:
    return value.encode("ascii").decode("unicode_escape")


DERIVED_RECIPE_LABELS = {
    "zscore": _zh(r"\u6807\u51c6\u5316\u5206\u6570"),
    "percentile_rank": _zh(r"\u767e\u5206\u4f4d\u6392\u540d"),
    "ratio": _zh(r"\u6bd4\u503c\u6307\u6807"),
    "difference": _zh(r"\u5dee\u503c\u6307\u6807"),
    "share": _zh(r"\u5360\u6bd4\u6307\u6807"),
    "product": _zh(r"\u4e58\u79ef\u6307\u6807"),
    "mean_index": _zh(r"\u5747\u503c\u6307\u6570"),
    "log1p": _zh(r"\u5bf9\u6570\u6307\u6807"),
    "calendar_month": _zh(r"\u6708\u4efd\u6307\u6807"),
    "calendar_dayofweek": _zh(r"\u661f\u671f\u6307\u6807"),
}


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def semantic_tags(column: str) -> list[str]:
    specs = load_auto_analysis_specs()
    mapping = specs.get("semantic_tags") if isinstance(specs.get("semantic_tags"), dict) else {}
    lower = column.lower()
    tags: list[str] = []
    for tag, tokens in mapping.items():
        if any(str(token).lower() in lower for token in list(tokens or [])):
            tags.append(str(tag))
    return tags


def profile_fields(frame: pd.DataFrame) -> list[dict[str, Any]]:
    row_count = max(int(len(frame)), 1)
    profiles: list[dict[str, Any]] = []
    for column in frame.columns.astype(str).tolist():
        series = frame[column]
        tags = semantic_tags(column)
        numeric = pd.to_numeric(series, errors="coerce")
        numeric_ratio = float(numeric.notna().mean())
        is_numeric = bool(pd.api.types.is_numeric_dtype(series) or numeric_ratio >= 0.8)
        is_datetime = bool(pd.api.types.is_datetime64_any_dtype(series))
        if not is_datetime and not is_numeric and "time" in tags:
            parsed_date = pd.to_datetime(series, errors="coerce")
            is_datetime = bool(parsed_date.notna().mean() >= 0.8)
        unique_count = int(series.nunique(dropna=True))
        missing_ratio = float(series.isna().sum() / row_count)
        role = "measure" if is_numeric else "time" if is_datetime else "dimension"
        if unique_count >= row_count * 0.8 and not is_numeric:
            role = "entity"
        profiles.append(
            {
                "column": column,
                "role": role,
                "dtype": str(series.dtype),
                "missing_ratio": round(missing_ratio, 4),
                "unique_count": unique_count,
                "numeric_ratio": round(numeric_ratio, 4),
                "semantic_tags": tags,
                "analysis_use": "target/metric" if role == "measure" else "split/filter/label",
            }
        )
    return profiles


def _enabled_recipe_ids() -> set[str]:
    specs = load_auto_analysis_specs()
    return {
        str(item.get("id") or "")
        for item in list(specs.get("derivation_recipes") or [])
        if isinstance(item, dict) and str(item.get("id") or "").strip()
    }


def _recipe_use(recipe_id: str) -> str:
    specs = load_auto_analysis_specs()
    for item in list(specs.get("derivation_recipes") or []):
        if isinstance(item, dict) and item.get("id") == recipe_id:
            return str(item.get("use") or "")
    return ""


def _derived_record(recipe_id: str, field: str, formula: str, source_fields: list[str]) -> dict[str, Any]:
    label = DERIVED_RECIPE_LABELS.get(recipe_id, recipe_id)
    sources = _zh(r"\u3001").join(source_fields)
    return {
        "field": field,
        "display_name": f"{label}\uff1a{sources}",
        "display_name_zh": f"{label}\uff1a{sources}",
        "recipe_id": recipe_id,
        "recipe_label": label,
        "formula": formula,
        "source_fields": source_fields,
        "source_fields_zh": sources,
        "use": _recipe_use(recipe_id),
    }


def _safe_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [_clean_text(item) for item in value if _clean_text(item)]
    if isinstance(value, str):
        return [_clean_text(part) for part in value.split(",") if _clean_text(part)]
    return []


def _numeric_signal(values: pd.Series) -> tuple[int, float]:
    numeric = pd.to_numeric(values, errors="coerce").dropna()
    if len(numeric) < 2:
        return 0, 0.0
    return int(numeric.nunique(dropna=True)), float(numeric.std(skipna=True) or 0.0)


def _is_usable_numeric_series(values: pd.Series) -> bool:
    unique_count, std = _numeric_signal(values)
    return unique_count >= 2 and std > 0


def _is_time_like_name(column: str) -> bool:
    text = column.lower()
    return any(token in text for token in ["年度", "年份", "年(", "date", "time", "year", "成立时间"])


def _is_identifier_like_name(column: str) -> bool:
    text = column.lower()
    return any(token in text for token in ["代码", "编号", "id", "uuid", "信用代码"])


def _normalize_formula(formula: str, source_fields: list[str]) -> str:
    formula_text = _clean_text(formula)
    if formula_text:
        return formula_text
    if len(source_fields) >= 2:
        return f"{source_fields[0]} / {source_fields[1]}"
    if len(source_fields) == 1:
        return f"{source_fields[0]} (derived)"
    return "derived_field"


def build_derived_field_edits(
    frame: pd.DataFrame,
    profiles: list[dict[str, Any]],
    edits: list[dict[str, Any]] | None = None,
    max_fields: int = 64,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    base_frame, base_records = build_derived_fields(frame, profiles, max_fields=max_fields)
    if not edits:
        return base_frame, base_records

    enriched = base_frame.copy()
    records = list(base_records)
    known_fields = {str(item.get("field") or "") for item in records if str(item.get("field") or "").strip()}
    for edit in edits:
        if not isinstance(edit, dict):
            continue
        field = _clean_text(edit.get("field") or edit.get("name") or edit.get("metric_name") or edit.get("display_name"))
        if not field:
            continue
        display_name = _clean_text(edit.get("display_name") or edit.get("display_name_zh") or edit.get("metric_name_cn") or edit.get("name_zh") or edit.get("name"))
        formula = _normalize_formula(
            _clean_text(edit.get("formula") or edit.get("formula_or_logic") or edit.get("calculation_method")),
            _safe_list(edit.get("source_fields") or edit.get("sources") or edit.get("fields")),
        )
        source_fields = _safe_list(edit.get("source_fields") or edit.get("sources") or edit.get("fields"))
        source_fields = [item for item in source_fields if item in enriched.columns]
        recipe_id = _clean_text(edit.get("recipe_id") or edit.get("recipe") or edit.get("calculation_method")) or "custom"
        if field in enriched.columns:
            existing = enriched[field]
            if not display_name:
                display_name = field
            enriched[field] = existing
        else:
            values = None
            if len(source_fields) >= 2 and source_fields[0] in enriched.columns and source_fields[1] in enriched.columns:
                left = pd.to_numeric(enriched[source_fields[0]], errors="coerce")
                right = pd.to_numeric(enriched[source_fields[1]], errors="coerce").replace(0, np.nan)
                if "/" in formula or "ratio" in recipe_id.lower():
                    values = left / right
                elif "-" in formula or "difference" in recipe_id.lower():
                    values = left - right
            elif len(source_fields) == 1 and source_fields[0] in enriched.columns:
                values = pd.to_numeric(enriched[source_fields[0]], errors="coerce")
            if values is not None:
                enriched[field] = values
            else:
                enriched[field] = np.nan
        record = {
            "field": field,
            "display_name": display_name or field,
            "display_name_zh": display_name or field,
            "recipe_id": recipe_id,
            "recipe_label": _clean_text(edit.get("recipe_label") or edit.get("formula_label") or display_name or recipe_id),
            "formula": formula,
            "source_fields": source_fields,
            "source_fields_zh": "、".join(source_fields),
            "use": _clean_text(edit.get("use") or edit.get("management_use") or "custom derived metric"),
            "manual_rename": bool(_clean_text(edit.get("manual_rename"))),
            "custom": True,
        }
        if field in known_fields:
            records = [item for item in records if str(item.get("field") or "") != field]
        records.append(record)
    return enriched, records[: max_fields + min(len(edits), 32)]


def _safe_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(number):
        return None
    return round(number, 6)


def _series(enriched: pd.DataFrame, column: str) -> pd.Series | None:
    if column not in enriched.columns:
        return None
    value = enriched[column]
    if isinstance(value, pd.DataFrame):
        return None
    return value


def _relationship_record(
    *,
    left_field: str,
    right_field: str,
    relationship_type: str,
    strength: float | None,
    direction: str,
    evidence: str,
    interpretation: str,
    recommended_use: str,
) -> dict[str, Any]:
    return {
        "left_field": left_field,
        "right_field": right_field,
        "relationship_type": relationship_type,
        "strength": strength,
        "direction": direction,
        "evidence": evidence,
        "management_interpretation": interpretation,
        "recommended_use": recommended_use,
    }


def build_derived_fields(frame: pd.DataFrame, profiles: list[dict[str, Any]], max_fields: int = 64) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    enriched = frame.copy()
    recipe_ids = _enabled_recipe_ids()
    def _missing_ratio(item: dict[str, Any]) -> float:
        value = item.get("missing_ratio")
        return 1.0 if value is None else float(value)

    numeric_columns = [
        item["column"]
        for item in profiles
        if item.get("role") == "measure"
        and _missing_ratio(item) < 0.8
        and not _is_identifier_like_name(str(item.get("column") or ""))
        and str(item.get("column") or "") in enriched.columns
        and _is_usable_numeric_series(enriched[str(item.get("column") or "")])
    ]
    records: list[dict[str, Any]] = []

    for column in numeric_columns[:16]:
        values = pd.to_numeric(enriched[column], errors="coerce")
        if "zscore" in recipe_ids:
            std = float(values.std(skipna=True) or 0.0)
            if std > 0:
                new_col = f"derived__zscore__{column}"
                enriched[new_col] = (values - float(values.mean(skipna=True))) / std
                records.append(_derived_record("zscore", new_col, f"zscore({column})", [column]))
        if "percentile_rank" in recipe_ids:
            rank_col = f"derived__pct_rank__{column}"
            enriched[rank_col] = values.rank(pct=True)
            records.append(_derived_record("percentile_rank", rank_col, f"percentile_rank({column})", [column]))
        mean_value = float(values.mean(skipna=True) or 0.0)
        if mean_value:
            index_col = f"derived__mean_index__{column}"
            enriched[index_col] = values / mean_value
            records.append(_derived_record("mean_index", index_col, f"{column} / mean({column})", [column]))
        if float(values.min(skipna=True) or 0.0) >= 0:
            log_col = f"derived__log1p__{column}"
            enriched[log_col] = np.log1p(values)
            records.append(_derived_record("log1p", log_col, f"log1p({column})", [column]))
        if len(records) >= max_fields:
            return enriched, records[:max_fields]

    pair_columns = numeric_columns[:10]
    for left_index, left in enumerate(pair_columns):
        for right_index, right in enumerate(pair_columns):
            if left == right or len(records) >= max_fields:
                continue
            left_values = pd.to_numeric(enriched[left], errors="coerce")
            right_values = pd.to_numeric(enriched[right], errors="coerce")
            if "ratio" in recipe_ids:
                ratio_col = f"derived__ratio__{left}__to__{right}"
                enriched[ratio_col] = left_values / right_values.replace(0, np.nan)
                records.append(_derived_record("ratio", ratio_col, f"{left} / {right}", [left, right]))
            if "difference" in recipe_ids:
                diff_col = f"derived__diff__{left}__minus__{right}"
                enriched[diff_col] = left_values - right_values
                records.append(_derived_record("difference", diff_col, f"{left} - {right}", [left, right]))
            if left_index < right_index:
                denom = (left_values + right_values).replace(0, np.nan)
                share_col = f"derived__share__{left}__of__{left}__plus__{right}"
                enriched[share_col] = left_values / denom
                records.append(_derived_record("share", share_col, f"{left} / ({left} + {right})", [left, right]))
                if not (_is_time_like_name(left) or _is_time_like_name(right)):
                    product_col = f"derived__product__{left}__x__{right}"
                    enriched[product_col] = left_values * right_values
                    records.append(_derived_record("product", product_col, f"{left} * {right}", [left, right]))

    for profile in profiles:
        if len(records) >= max_fields:
            break
        column = str(profile.get("column") or "")
        if not column or column not in enriched.columns:
            continue
        if profile.get("role") != "time" and "time" not in profile.get("semantic_tags", []):
            continue
        dt = pd.to_datetime(enriched[column], errors="coerce")
        if dt.notna().mean() < 0.5:
            continue
        if "calendar_month" in recipe_ids:
            month_col = f"derived__month__{column}"
            enriched[month_col] = dt.dt.to_period("M").astype(str)
            records.append(_derived_record("calendar_month", month_col, f"month({column})", [column]))
        if "calendar_dayofweek" in recipe_ids:
            dow_col = f"derived__dayofweek__{column}"
            enriched[dow_col] = dt.dt.dayofweek
            records.append(_derived_record("calendar_dayofweek", dow_col, f"dayofweek({column})", [column]))

    return enriched, records[:max_fields]


def build_field_relationships(
    enriched: pd.DataFrame,
    profiles: list[dict[str, Any]],
    derived_fields: list[dict[str, Any]],
    max_relationships: int = 120,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    profile_by_column = {str(item.get("column") or ""): item for item in profiles}
    numeric_columns = [
        str(item.get("column") or "")
        for item in profiles
        if item.get("role") == "measure" and str(item.get("column") or "") in enriched.columns
    ][:14]
    derived_numeric = [
        str(item.get("field") or "")
        for item in derived_fields
        if str(item.get("field") or "") in enriched.columns
    ][:10]

    for item in derived_fields[: max_relationships // 3]:
        field = str(item.get("field") or "")
        sources = [str(source) for source in list(item.get("source_fields") or []) if str(source)]
        if not field or not sources:
            continue
        records.append(
            _relationship_record(
                left_field=field,
                right_field=", ".join(sources),
                relationship_type="derived_from",
                strength=1.0,
                direction="lineage",
                evidence=str(item.get("formula") or field),
                interpretation=f"{item.get('display_name_zh') or field} {_zh(r'\u6765\u81ea\u539f\u59cb\u5b57\u6bb5\u8ba1\u7b97\uff0c\u53ef\u7528\u4e8e\u76f8\u5bf9\u8868\u73b0\u3001\u6548\u7387\u6216\u5dee\u5f02\u89e3\u8bfb\u3002')}",
                recommended_use=str(item.get("use") or "derived metric analysis"),
            )
        )

    relationship_candidates: list[dict[str, Any]] = []
    numeric_for_pairs = [*numeric_columns, *derived_numeric]
    for left_index, left in enumerate(numeric_for_pairs[:16]):
        left_series = _series(enriched, left)
        if left_series is None:
            continue
        left_values = pd.to_numeric(left_series, errors="coerce")
        for right in numeric_for_pairs[left_index + 1 : 16]:
            right_series = _series(enriched, right)
            if right_series is None:
                continue
            right_values = pd.to_numeric(right_series, errors="coerce")
            valid = left_values.notna() & right_values.notna()
            if int(valid.sum()) < 3:
                continue
            corr = _safe_float(left_values[valid].corr(right_values[valid]))
            if corr is None:
                continue
            relationship_candidates.append(
                _relationship_record(
                    left_field=left,
                    right_field=right,
                    relationship_type="numeric_correlation",
                    strength=abs(corr),
                    direction="positive" if corr >= 0 else "negative",
                    evidence=f"pearson={corr}",
                    interpretation=_zh(r"\u4e24\u4e2a\u6570\u503c\u6307\u6807\u5728\u5f53\u524d\u6837\u672c\u4e2d\u5448\u73b0\u540c\u5411\u6216\u53cd\u5411\u53d8\u52a8\uff0c\u9002\u5408\u8fdb\u5165\u9a71\u52a8\u89e3\u91ca\u3001\u6307\u6807\u5197\u4f59\u5224\u65ad\u6216\u6a21\u578b\u7279\u5f81\u5019\u9009\u3002"),
                    recommended_use="driver scan / redundancy check / model feature candidate",
                )
            )

    dimension_columns = [
        str(item.get("column") or "")
        for item in profiles
        if item.get("role") in {"dimension", "entity"} and 1 < int(item.get("unique_count") or 0) <= 30
    ][:5]
    for dimension in dimension_columns:
        dimension_series = _series(enriched, dimension)
        if dimension_series is None:
            continue
        for measure in numeric_columns[:8]:
            measure_series = _series(enriched, measure)
            if measure_series is None:
                continue
            values = pd.to_numeric(measure_series, errors="coerce")
            grouped = values.groupby(dimension_series).mean().dropna()
            if len(grouped) < 2:
                continue
            spread = float(grouped.max() - grouped.min())
            scale = float(values.std(skipna=True) or 0.0) or 1.0
            strength = _safe_float(min(abs(spread / scale), 10.0) / 10.0)
            relationship_candidates.append(
                _relationship_record(
                    left_field=dimension,
                    right_field=measure,
                    relationship_type="segment_lift",
                    strength=strength,
                    direction="group_difference",
                    evidence=f"mean_spread={round(spread, 6)}; groups={len(grouped)}",
                    interpretation=_zh(r"\u7ef4\u5ea6\u5206\u7ec4\u4e4b\u95f4\u7684\u6307\u6807\u5747\u503c\u6709\u53ef\u89c1\u5dee\u5f02\uff0c\u9002\u5408\u751f\u6210\u5206\u5c42\u89e3\u8bfb\u3001\u5bf9\u6bd4\u8868\u548c\u884c\u52a8\u4f18\u5148\u7ea7\u3002"),
                    recommended_use="segment comparison / action prioritization",
                )
            )

    time_columns = [
        str(item.get("column") or "")
        for item in profiles
        if item.get("role") == "time" and str(item.get("column") or "") in enriched.columns
    ][:2]
    for time_column in time_columns:
        time_series = _series(enriched, time_column)
        if time_series is None:
            continue
        parsed = pd.to_datetime(time_series, errors="coerce")
        order = parsed.rank(method="dense")
        for measure in numeric_columns[:8]:
            measure_series = _series(enriched, measure)
            if measure_series is None:
                continue
            values = pd.to_numeric(measure_series, errors="coerce")
            valid = order.notna() & values.notna()
            if int(valid.sum()) < 3:
                continue
            corr = _safe_float(order[valid].corr(values[valid]))
            if corr is None:
                continue
            relationship_candidates.append(
                _relationship_record(
                    left_field=time_column,
                    right_field=measure,
                    relationship_type="time_trend",
                    strength=abs(corr),
                    direction="upward" if corr >= 0 else "downward",
                    evidence=f"time_rank_corr={corr}",
                    interpretation=_zh(r"\u65f6\u95f4\u987a\u5e8f\u4e0e\u6307\u6807\u53d8\u52a8\u5b58\u5728\u65b9\u5411\u6027\u5173\u7cfb\uff0c\u9002\u5408\u8fdb\u5165\u8d8b\u52bf\u3001\u9884\u6d4b\u548c\u5f02\u5e38\u65f6\u70b9\u89e3\u8bfb\u3002"),
                    recommended_use="time series chapter / forecast / anomaly timing",
                )
            )

    relationship_candidates.sort(key=lambda item: float(item.get("strength") or 0.0), reverse=True)
    for item in relationship_candidates:
        if len(records) >= max_relationships:
            break
        records.append(item)

    for record in records:
        left_profile = profile_by_column.get(str(record.get("left_field") or ""), {})
        right_profile = profile_by_column.get(str(record.get("right_field") or ""), {})
        record["left_role"] = left_profile.get("role") or ("derived" if str(record.get("left_field") or "").startswith("derived__") else "")
        record["right_role"] = right_profile.get("role") or ""
        record["left_semantic_tags"] = list(left_profile.get("semantic_tags") or [])
        record["right_semantic_tags"] = list(right_profile.get("semantic_tags") or [])
    return records[:max_relationships]


def _field_business_meaning(profile: dict[str, Any], derived_by_field: dict[str, dict[str, Any]]) -> str:
    column = str(profile.get("column") or "")
    role = str(profile.get("role") or "")
    tags = {str(tag) for tag in list(profile.get("semantic_tags") or [])}
    if column in derived_by_field:
        recipe = str(derived_by_field[column].get("recipe_label") or derived_by_field[column].get("recipe_id") or "derived")
        sources = str(derived_by_field[column].get("source_fields_zh") or ", ".join(derived_by_field[column].get("source_fields") or []))
        return f"{recipe} derived from {sources}; use it as a normalized, relative, gap, calendar, or efficiency signal."
    if "time" in tags or role == "time":
        return "Time/order field for trend, lag, seasonality, forecast, and before/after narrative routing."
    if "entity" in tags or role == "entity":
        return "Business object identifier or label for bubble, anomaly, drilldown, and evidence-index rows."
    if {"revenue", "profit"} & tags:
        return "Outcome/value metric suitable as target, size, quadrant axis, and executive KPI evidence."
    if {"cost"} & tags:
        return "Cost or investment metric suitable for efficiency, margin, variance, and action-priority analysis."
    if {"quantity", "rate", "quality"} & tags:
        return "Operational metric suitable for distribution, segmentation, threshold, and driver analysis."
    if role == "measure":
        return "Continuous measure suitable for target selection, feature screening, relationships, and visual axes."
    if role == "dimension":
        return "Categorical dimension suitable for grouping, filtering, comparison, color, and chapter segmentation."
    return "General field retained for profiling, glossary, appendix, and evidence-index traceability."


def _analysis_roles_for_profile(profile: dict[str, Any], selected: dict[str, Any], is_derived: bool) -> list[str]:
    column = str(profile.get("column") or "")
    role = str(profile.get("role") or "")
    roles: list[str] = []
    if column == selected.get("target"):
        roles.append("target")
    if column in list(selected.get("features") or []):
        roles.append("feature")
    if column == selected.get("group"):
        roles.append("group")
    if column == selected.get("label"):
        roles.append("label")
    for chart_role, value in dict(selected.get("bubble") or {}).items():
        if column == value:
            roles.append(f"bubble_{chart_role}")
    for chart_role, value in dict(selected.get("quadrant") or {}).items():
        if column == value:
            roles.append(f"quadrant_{chart_role}")
    if is_derived:
        roles.append("derived_metric")
    if role == "time":
        roles.append("time_window")
    if role in {"dimension", "entity"}:
        roles.extend(["segment", "filter"])
    if role == "measure":
        roles.extend(["measure", "model_candidate"])
    return list(dict.fromkeys(roles)) or ["profile_only"]


def _method_families_for_roles(profile: dict[str, Any], analysis_roles: list[str]) -> list[str]:
    role = str(profile.get("role") or "")
    families: list[str] = ["descriptive", "report_part"]
    if role == "measure" or "derived_metric" in analysis_roles:
        families.extend(["association", "comparison", "regression", "machine_learning", "visual"])
    if role in {"dimension", "entity"} or {"group", "segment", "filter"} & set(analysis_roles):
        families.extend(["comparison", "categorical_association", "visual"])
    if role == "time" or "time_window" in analysis_roles:
        families.extend(["time_series", "causal", "visual"])
    if {"target", "feature", "model_candidate"} & set(analysis_roles):
        families.extend(["regression", "machine_learning", "causal"])
    return list(dict.fromkeys(families))


def _report_parts_for_roles(analysis_roles: list[str], method_families: list[str]) -> list[str]:
    parts = ["field_glossary", "appendix", "evidence_index"]
    role_set = set(analysis_roles)
    family_set = set(method_families)
    if {"target", "group", "bubble_x", "bubble_y", "bubble_size", "quadrant_x", "quadrant_y"} & role_set:
        parts.extend(["executive_summary", "chapter", "visual_gallery"])
    if {"regression", "machine_learning", "causal", "time_series"} & family_set:
        parts.extend(["method_note", "action_plan"])
    if "derived_metric" in role_set:
        parts.extend(["chapter", "method_note"])
    return list(dict.fromkeys(parts))


def _relationship_refs_for_field(field: str, relationships: list[dict[str, Any]], limit: int = 6) -> list[str]:
    refs: list[str] = []
    for relationship in relationships:
        left = str(relationship.get("left_field") or "")
        right = str(relationship.get("right_field") or "")
        if field != left and field not in [part.strip() for part in right.split(",")]:
            continue
        rel_type = str(relationship.get("relationship_type") or "relationship")
        other = right if field == left else left
        refs.append(f"{rel_type}:{field}->{other}")
        if len(refs) >= limit:
            break
    return refs


def build_field_semantic_route_plan(
    *,
    profiles: list[dict[str, Any]],
    derived_fields: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
    selected: dict[str, Any],
    max_rows: int = 160,
) -> dict[str, Any]:
    """Build the field-level routing contract consumed by report-part generators.

    This runs after smart derived-field preprocessing and before/alongside method
    routing, so every downstream method card can explain why fields were chosen.
    """
    derived_by_field = {str(item.get("field") or ""): item for item in derived_fields if str(item.get("field") or "")}
    profile_by_column = {str(item.get("column") or ""): dict(item) for item in profiles if str(item.get("column") or "")}
    for derived in derived_fields:
        field = str(derived.get("field") or "")
        if field and field not in profile_by_column:
            profile_by_column[field] = {
                "column": field,
                "role": "measure",
                "dtype": "derived",
                "missing_ratio": "",
                "unique_count": "",
                "numeric_ratio": "",
                "semantic_tags": ["derived"],
                "analysis_use": "derived metric analysis",
            }

    rows: list[dict[str, Any]] = []
    for field, profile in profile_by_column.items():
        is_derived = field in derived_by_field
        analysis_roles = _analysis_roles_for_profile(profile, selected, is_derived)
        method_families = _method_families_for_roles(profile, analysis_roles)
        report_parts = _report_parts_for_roles(analysis_roles, method_families)
        relationship_refs = _relationship_refs_for_field(field, relationships)
        rows.append(
            {
                "field": field,
                "source": "derived_field" if is_derived else "original_field",
                "semantic_role": profile.get("role") or ("measure" if is_derived else ""),
                "semantic_tags": ", ".join(str(tag) for tag in list(profile.get("semantic_tags") or [])),
                "business_meaning": _field_business_meaning(profile, derived_by_field),
                "analysis_roles": ", ".join(analysis_roles),
                "compatible_method_families": ", ".join(method_families),
                "recommended_report_parts": ", ".join(report_parts),
                "relationship_refs": ", ".join(relationship_refs),
                "relationship_count": len(relationship_refs),
                "derived_from": ", ".join(str(item) for item in list(derived_by_field.get(field, {}).get("source_fields") or [])),
                "management_use": "Use this row to bind fields into method cards, chart specs, report sections, appendix tables, and evidence refs.",
            }
        )

    def _priority(row: dict[str, Any]) -> tuple[int, int, str]:
        role_text = str(row.get("analysis_roles") or "")
        source_score = 2 if row.get("source") == "derived_field" else 1
        role_score = sum(token in role_text for token in ["target", "feature", "bubble", "quadrant", "group", "time_window"])
        return (int(role_score), source_score, str(row.get("field") or ""))

    rows.sort(key=_priority, reverse=True)
    role_counts: dict[str, int] = {}
    source_counts: dict[str, int] = {}
    report_part_counts: dict[str, int] = {}
    for row in rows:
        source = str(row.get("source") or "unknown")
        source_counts[source] = source_counts.get(source, 0) + 1
        for role in [item.strip() for item in str(row.get("analysis_roles") or "").split(",") if item.strip()]:
            role_counts[role] = role_counts.get(role, 0) + 1
        for part in [item.strip() for item in str(row.get("recommended_report_parts") or "").split(",") if item.strip()]:
            report_part_counts[part] = report_part_counts.get(part, 0) + 1
    return {
        "status": "ready",
        "pre_method_preprocessing_status": "derived_fields_completed_before_method_routing",
        "field_count": len(rows),
        "derived_field_count": source_counts.get("derived_field", 0),
        "relationship_linked_field_count": sum(1 for row in rows if int(row.get("relationship_count") or 0) > 0),
        "role_counts": dict(sorted(role_counts.items())),
        "source_counts": dict(sorted(source_counts.items())),
        "report_part_counts": dict(sorted(report_part_counts.items())),
        "rows": rows[:max_rows],
    }


def select_best_fields(enriched: pd.DataFrame, profiles: list[dict[str, Any]], derived_fields: list[dict[str, Any]]) -> dict[str, Any]:
    base_numeric = [item["column"] for item in profiles if item.get("role") == "measure"]
    derived_numeric = [item["field"] for item in derived_fields if item["field"] in enriched.columns and pd.api.types.is_numeric_dtype(enriched[item["field"]])]
    numeric = [column for column in [*base_numeric, *derived_numeric] if column in enriched.columns]
    profile_by_column = {str(item.get("column") or ""): item for item in profiles}
    derived_by_field = {str(item.get("field") or ""): item for item in derived_fields}

    def _business_metric_bonus(column: str) -> float:
        text = column.lower()
        bonus = 0.0
        for token in ["收入", "支出", "捐赠", "公益", "项目收入", "项目支出", "total", "revenue", "expense", "donation"]:
            if token in text:
                bonus += 10.0
        if _is_identifier_like_name(column):
            bonus -= 80.0
        if _is_time_like_name(column):
            bonus -= 35.0
        return bonus

    def _derived_penalty(column: str) -> float:
        record = derived_by_field.get(column)
        if not record:
            return 0.0
        recipe = str(record.get("recipe_id") or "")
        sources = [str(item) for item in list(record.get("source_fields") or [])]
        penalty = 14.0
        if recipe == "product":
            penalty += 90.0
        elif recipe in {"zscore", "percentile_rank", "mean_index", "log1p"}:
            penalty += 18.0
        elif recipe in {"ratio", "share", "difference"}:
            penalty -= 4.0
        if any(_is_time_like_name(source) for source in sources):
            penalty += 35.0
        return penalty

    numeric_scores: list[tuple[float, str]] = []
    for column in numeric:
        values = pd.to_numeric(enriched[column], errors="coerce")
        unique_count, std = _numeric_signal(values)
        valid_ratio = float(values.notna().mean())
        if unique_count < 2 or std <= 0 or valid_ratio < 0.5:
            continue
        profile = profile_by_column.get(column) or {}
        original_bonus = 30.0 if column in profile_by_column else 0.0
        unique_bonus = min(20.0, float(np.log1p(unique_count)) * 4.0)
        spread_bonus = min(25.0, float(np.log1p(abs(std))) * 2.5)
        score = original_bonus + unique_bonus + spread_bonus + valid_ratio * 20.0 + _business_metric_bonus(column) - _derived_penalty(column)
        if int(profile.get("unique_count") or unique_count) <= 1:
            score -= 100.0
        numeric_scores.append((score, column))
    numeric_scores.sort(reverse=True)
    selected_numeric = [column for _, column in numeric_scores[:6]]

    dimension_candidates = [
        item["column"]
        for item in profiles
        if item.get("role") in {"dimension", "entity", "time"} and 1 < int(item.get("unique_count") or 0) <= max(80, len(enriched) // 2)
    ]
    label_candidates = [item["column"] for item in profiles if item.get("role") in {"dimension", "entity"}]

    def _dimension_score(column: str) -> float:
        text = column.lower()
        profile = profile_by_column.get(column) or {}
        unique_count = int(profile.get("unique_count") or 0)
        score = 100.0 - min(80.0, abs(unique_count - 12) * 1.5)
        for token in ["服务领域", "注册地", "省份", "地区", "基金会类型", "项目地点", "管理机关", "category", "region", "segment"]:
            if token in text:
                score += 35.0
        if "基金会名称" in column:
            score -= 20.0
        if _is_identifier_like_name(column):
            score -= 80.0
        return score

    dimension_candidates.sort(key=_dimension_score, reverse=True)

    def _label_score(column: str) -> float:
        score = 0.0
        if "基金会名称" in column:
            score += 100.0
        if "项目名称" in column:
            score += 80.0
        if _is_identifier_like_name(column):
            score -= 80.0
        return score

    label_candidates.sort(key=_label_score, reverse=True)

    x = selected_numeric[0] if selected_numeric else ""
    y = selected_numeric[1] if len(selected_numeric) > 1 else x
    size = selected_numeric[2] if len(selected_numeric) > 2 else x
    color = dimension_candidates[0] if dimension_candidates else ""
    label = label_candidates[0] if label_candidates else ""
    return {
        "target": selected_numeric[0] if selected_numeric else "",
        "features": selected_numeric[1:6],
        "group": color,
        "label": label,
        "bubble": {"x": x, "y": y, "size": size, "color": color, "label": label},
        "quadrant": {"x": x, "y": y, "label": label, "group": color},
        "selection_reason": "Fields are ranked by completeness, variance, semantic role, and suitability for chart/report output.",
    }
