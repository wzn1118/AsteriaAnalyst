from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

from .schemas import AIFieldSemanticMappingResult, AIMetricDerivationPlan, AIMetricPlanItem


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _normalize(value: Any) -> str:
    return "".join(ch for ch in _safe_text(value).lower() if ch.isalnum() or "\u4e00" <= ch <= "\u9fff")


def _metric_dir(output_dir: str | Path) -> Path:
    path = Path(output_dir) / "outputs" / "metric_mining"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _json_default(value: Any) -> Any:
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    return value


def _write_json(path: Path, payload: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    return str(path.resolve())


def _role_aliases(canonical_concept: str, business_role: str) -> set[str]:
    aliases: set[str] = set()
    concept = _normalize(canonical_concept)
    role = _normalize(business_role)
    if any(token in concept for token in ["userid", "uid"]):
        aliases.update({"user_key", "object_key"})
    if any(token in concept for token in ["orderid"]):
        aliases.update({"order_key", "object_key"})
    if any(token in concept for token in ["skuid"]):
        aliases.update({"sku_key", "product_key", "object_key"})
    if any(token in concept for token in ["productid"]):
        aliases.update({"product_key", "object_key"})
    if "category" in concept:
        aliases.update({"category_key", "object_key"})
    if "supplierid" in concept:
        aliases.update({"supplier_key", "object_key"})
    if "sellerid" in concept:
        aliases.update({"seller_key", "object_key"})
    if "channel" in concept:
        aliases.update({"channel_key", "object_key"})
    if "campaign" in concept:
        aliases.update({"campaign_key", "object_key"})
    if "content" in concept:
        aliases.update({"content_key", "object_key"})
    if "sessionid" in concept:
        aliases.update({"session_key", "object_key"})
    if concept == "date":
        aliases.add("time_key")
    if concept in {"revenue", "gmv"} or "amount" in concept:
        aliases.add("amount_field")
        aliases.add("numeric_measure")
    if concept == "cost":
        aliases.add("cost_field")
        aliases.add("numeric_measure")
    if concept == "price":
        aliases.add("price_field")
        aliases.add("numeric_measure")
    if concept == "quantity":
        aliases.add("quantity_field")
        aliases.add("numeric_measure")
    if concept in {"inventory", "stock"}:
        aliases.add("inventory_field")
        aliases.add("numeric_measure")
    if concept == "rating":
        aliases.add("rating_field")
        aliases.add("numeric_measure")
    if concept == "reviewscore":
        aliases.add("review_score_field")
        aliases.add("numeric_measure")
    if concept == "commenttext":
        aliases.add("text_feedback_field")
    if concept == "impression":
        aliases.add("impression_field")
        aliases.add("numeric_measure")
    if concept == "click":
        aliases.add("click_field")
        aliases.add("numeric_measure")
    if concept == "conversion":
        aliases.add("conversion_field")
        aliases.add("numeric_measure")
    if concept == "eventtype":
        aliases.add("event_field")

    if "time" in role:
        aliases.add("time_key")
    if "user" in role:
        aliases.update({"user_key", "object_key"})
    if "order" in role:
        aliases.update({"order_key", "object_key"})
    if "sku" in role:
        aliases.update({"sku_key", "product_key", "object_key"})
    if "product" in role:
        aliases.update({"product_key", "object_key"})
    if "category" in role:
        aliases.update({"category_key", "object_key"})
    if "supplier" in role:
        aliases.update({"supplier_key", "object_key"})
    if "seller" in role:
        aliases.update({"seller_key", "object_key"})
    if "channel" in role:
        aliases.update({"channel_key", "object_key"})
    if "campaign" in role:
        aliases.update({"campaign_key", "object_key"})
    if "content" in role:
        aliases.update({"content_key", "object_key"})
    if "session" in role:
        aliases.update({"session_key", "object_key"})
    if "amount" in role or "revenue" in role:
        aliases.add("amount_field")
    if "quantity" in role or "count" in role:
        aliases.add("quantity_field")
    if "cost" in role:
        aliases.add("cost_field")
    if "price" in role:
        aliases.add("price_field")
    if "inventory" in role or "stock" in role:
        aliases.add("inventory_field")
    if "rating" in role:
        aliases.add("rating_field")
    if "review" in role and "score" in role:
        aliases.add("review_score_field")
    if "text" in role or "comment" in role or "feedback" in role:
        aliases.add("text_feedback_field")
    if "impression" in role:
        aliases.add("impression_field")
    if "click" in role:
        aliases.add("click_field")
    if "conversion" in role:
        aliases.add("conversion_field")
    if "event" in role:
        aliases.add("event_field")
    if "step" in role or "order" in role:
        aliases.add("step_key")
    return aliases


def _available_role_map(mapping_result: AIFieldSemanticMappingResult) -> dict[str, list[str]]:
    role_map: dict[str, list[str]] = {}
    for mapping in mapping_result.field_mappings:
        for alias in _role_aliases(mapping.canonical_concept, mapping.business_role):
            role_map.setdefault(alias, [])
            if mapping.field_name not in role_map[alias]:
                role_map[alias].append(mapping.field_name)
        for key in {_safe_text(mapping.canonical_concept), _safe_text(mapping.business_role)}:
            role_map.setdefault(key, [])
            if mapping.field_name not in role_map[key]:
                role_map[key].append(mapping.field_name)
    return role_map


def _first_field(role_map: dict[str, list[str]], role: str) -> str | None:
    values = role_map.get(role) or []
    return values[0] if values else None


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


def _role_field(frame: pd.DataFrame, role_map: dict[str, list[str]], *roles: str) -> str | None:
    for role in roles:
        for candidate in role_map.get(role) or []:
            resolved = _resolve_column(frame, candidate)
            if resolved:
                return resolved
    return None


def _matched_fields(frame: pd.DataFrame, item: AIMetricPlanItem) -> list[str]:
    fields: list[str] = []
    for field in item.matched_fields:
        resolved = _resolve_column(frame, field)
        if resolved and resolved not in fields:
            fields.append(resolved)
    return fields


def _is_numeric_field(frame: pd.DataFrame, column: str | None) -> bool:
    if not column or column not in frame.columns:
        return False
    return _numeric_series(frame, column).notna().any()


_SUM_RE = re.compile(r"\bsum\s*\(\s*([^)]+?)\s*\)", re.IGNORECASE)
_AVG_RE = re.compile(r"\bavg\s*\(\s*([^)]+?)\s*\)", re.IGNORECASE)
_COUNT_RE = re.compile(r"\bcount\s*\(\s*([^)]+?)\s*\)", re.IGNORECASE)
_COUNT_DISTINCT_RE = re.compile(r"\bcount\s*\(\s*distinct\s+([^)]+?)\s*\)", re.IGNORECASE)
_GROUP_BY_RE = re.compile(r"\bgroup\s+by\s+(.+?)(?:;|$)", re.IGNORECASE)
_BY_RE = re.compile(r"\bby\s+(.+?)(?:/|;|$)", re.IGNORECASE)


def _formula_sum_field(frame: pd.DataFrame, item: AIMetricPlanItem) -> str | None:
    for match in _SUM_RE.finditer(item.formula_or_logic or ""):
        candidate = _resolve_column(frame, match.group(1).strip(" `\"'"))
        if candidate and _is_numeric_field(frame, candidate):
            return candidate
    return None


def _formula_sum_fields(frame: pd.DataFrame, item: AIMetricPlanItem) -> list[str]:
    fields: list[str] = []
    for match in _SUM_RE.finditer(item.formula_or_logic or ""):
        candidate = _resolve_column(frame, match.group(1).strip(" `\"'"))
        if candidate and candidate not in fields:
            fields.append(candidate)
    return fields


def _formula_avg_field(frame: pd.DataFrame, item: AIMetricPlanItem) -> str | None:
    for match in _AVG_RE.finditer(item.formula_or_logic or ""):
        candidate = _resolve_column(frame, match.group(1).strip(" `\"'"))
        if candidate:
            return candidate
    return None


def _formula_count_field(frame: pd.DataFrame, item: AIMetricPlanItem) -> str | None:
    for match in _COUNT_RE.finditer(item.formula_or_logic or ""):
        raw = match.group(1).strip(" `\"'")
        if raw.lower().startswith("distinct "):
            raw = raw[9:].strip()
        candidate = _resolve_column(frame, raw)
        if candidate:
            return candidate
    return None


def _formula_distinct_field(frame: pd.DataFrame, item: AIMetricPlanItem) -> str | None:
    for match in _COUNT_DISTINCT_RE.finditer(item.formula_or_logic or ""):
        candidate = _resolve_column(frame, match.group(1).strip(" `\"'"))
        if candidate:
            return candidate
    return None


def _formula_group_fields(frame: pd.DataFrame, item: AIMetricPlanItem) -> list[str]:
    formula = item.formula_or_logic or ""
    match = _GROUP_BY_RE.search(formula) or _BY_RE.search(formula)
    if not match:
        return []
    fields: list[str] = []
    raw = match.group(1)
    for part in re.split(r",|\band\b|/|\+", raw, flags=re.IGNORECASE):
        candidate = _resolve_column(frame, part.strip(" `\"'"))
        if candidate and candidate not in fields:
            fields.append(candidate)
    return fields


def _measure_field(frame: pd.DataFrame, item: AIMetricPlanItem, role_map: dict[str, list[str]]) -> str | None:
    formula_field = _formula_sum_field(frame, item)
    if formula_field:
        return formula_field
    role_field = _role_field(
        frame,
        role_map,
        "amount_field",
        "quantity_field",
        "impression_field",
        "click_field",
        "conversion_field",
        "cost_field",
        "price_field",
        "inventory_field",
        "rating_field",
        "review_score_field",
        "numeric_measure",
    )
    if role_field:
        return role_field
    for field in _matched_fields(frame, item):
        if _is_numeric_field(frame, field):
            return field
    return None


def _dimension_field(frame: pd.DataFrame, item: AIMetricPlanItem, role_map: dict[str, list[str]]) -> str | None:
    formula_fields = _formula_group_fields(frame, item)
    if formula_fields:
        return formula_fields[0]
    grain_col = _resolve_column(frame, item.grain)
    if grain_col:
        return grain_col
    role_field = _role_field(
        frame,
        role_map,
        "channel_key",
        "campaign_key",
        "content_key",
        "category_key",
        "sku_key",
        "product_key",
        "supplier_key",
        "seller_key",
        "event_field",
        "object_key",
    )
    if role_field:
        return role_field
    for field in _matched_fields(frame, item):
        if not _is_numeric_field(frame, field):
            return field
    return None


def _time_field(frame: pd.DataFrame, item: AIMetricPlanItem, role_map: dict[str, list[str]]) -> str | None:
    for field in _formula_group_fields(frame, item):
        if _time_series(frame, field).notna().any():
            return field
    return _role_field(frame, role_map, "time_key")


def _numeric_series(frame: pd.DataFrame, column: str | None) -> pd.Series:
    if not column or column not in frame.columns:
        return pd.Series(dtype="float64")
    return pd.to_numeric(frame[column], errors="coerce")


def _time_series(frame: pd.DataFrame, column: str | None) -> pd.Series:
    if not column or column not in frame.columns:
        return pd.Series(dtype="datetime64[ns]")
    return pd.to_datetime(frame[column], errors="coerce")


def _ratio(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    valid = numerator.notna() & denominator.notna() & (denominator != 0)
    out = pd.Series(dtype="float64", index=denominator.index)
    out.loc[valid] = numerator.loc[valid] / denominator.loc[valid]
    return out.dropna()


def _string_series(frame: pd.DataFrame, column: str | None) -> pd.Series:
    if not column or column not in frame.columns:
        return pd.Series(dtype="object")
    return frame[column].astype(str)


def _format_value(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 6)
    if isinstance(value, pd.Series):
        return value.to_dict()
    return value


def _calculated_status(item: AIMetricPlanItem) -> str:
    return "proxy_calculated" if item.metric_type == "proxy" or item.evidence_level == "C_PROXY" else "calculated"


def _base_result(item: AIMetricPlanItem) -> dict[str, Any]:
    return {
        "metric_id": item.metric_id,
        "metric_name_cn": item.metric_name_cn,
        "value": None,
        "grain": item.grain,
        "source_fields": list(item.matched_fields),
        "formula": item.formula_or_logic,
        "calculation_method": "",
        "evidence_level": item.evidence_level,
        "confidence": item.confidence,
        "caveat": item.caveat,
        "unsupported_reason": "",
        "status": "unavailable",
    }


def _result_unavailable(item: AIMetricPlanItem, reason: str) -> dict[str, Any]:
    result = _base_result(item)
    result["unsupported_reason"] = reason
    result["status"] = "unavailable"
    return result


def _result_failed(item: AIMetricPlanItem, reason: str) -> dict[str, Any]:
    result = _base_result(item)
    result["unsupported_reason"] = reason
    result["status"] = "failed"
    return result


def _grouped_distinct_users(frame: pd.DataFrame, time_col: str, user_col: str, freq: str) -> list[dict[str, Any]]:
    time_series = _time_series(frame, time_col)
    users = _string_series(frame, user_col)
    data = pd.DataFrame({"time": time_series, "user": users}).dropna()
    if data.empty:
        return []
    if freq == "day":
        key = data["time"].dt.strftime("%Y-%m-%d")
    elif freq == "week":
        key = data["time"].dt.to_period("W").astype(str)
    else:
        key = data["time"].dt.to_period("M").astype(str)
    grouped = data.assign(period=key).groupby("period")["user"].nunique().sort_index()
    return [{"period": period, "value": int(value)} for period, value in grouped.items()]


def _cohort_retention(frame: pd.DataFrame, time_col: str, user_col: str, window_days: int) -> list[dict[str, Any]]:
    times = _time_series(frame, time_col)
    users = _string_series(frame, user_col)
    data = pd.DataFrame({"time": times, "user": users}).dropna()
    if data.empty:
        return []
    data["date"] = data["time"].dt.normalize()
    first_seen = data.groupby("user")["date"].min().rename("cohort_date")
    joined = data.merge(first_seen, left_on="user", right_index=True, how="left")
    joined["delta_days"] = (joined["date"] - joined["cohort_date"]).dt.days
    cohort_users = first_seen.reset_index().groupby("cohort_date")["user"].nunique()
    retained = joined[joined["delta_days"] == window_days].groupby("cohort_date")["user"].nunique()
    rows: list[dict[str, Any]] = []
    for cohort_date, cohort_size in cohort_users.items():
        retained_users = int(retained.get(cohort_date, 0))
        rows.append(
            {
                "cohort_date": cohort_date.strftime("%Y-%m-%d"),
                "cohort_users": int(cohort_size),
                "retained_users": retained_users,
                "retention_rate": round(retained_users / cohort_size, 6) if cohort_size else None,
            }
        )
    return rows


def _first_seen(frame: pd.DataFrame, time_col: str, user_col: str) -> list[dict[str, Any]]:
    times = _time_series(frame, time_col)
    users = _string_series(frame, user_col)
    data = pd.DataFrame({"time": times, "user": users}).dropna()
    if data.empty:
        return []
    first_seen = data.groupby("user")["time"].min().sort_values()
    return [{"user_id": user, "first_seen": value.isoformat()} for user, value in first_seen.head(200).items()]


def _ctr(frame: pd.DataFrame, impression_col: str, click_col: str) -> float | None:
    ratio = _ratio(_numeric_series(frame, click_col), _numeric_series(frame, impression_col))
    return float(ratio.mean()) if not ratio.empty else None


def _cvr(frame: pd.DataFrame, numerator_col: str, denominator_col: str) -> float | None:
    ratio = _ratio(_numeric_series(frame, numerator_col), _numeric_series(frame, denominator_col))
    return float(ratio.mean()) if not ratio.empty else None


def _sum_metric(frame: pd.DataFrame, column: str) -> float | None:
    series = _numeric_series(frame, column).dropna()
    return float(series.sum()) if not series.empty else None


def _mean_metric(frame: pd.DataFrame, column: str) -> float | None:
    numeric = _numeric_series(frame, column).dropna()
    if not numeric.empty:
        return float(numeric.mean())
    text = _string_series(frame, column).replace("", pd.NA).dropna()
    if not text.empty:
        return float(text.size)
    return None


def _distinct_count_or_rowcount(frame: pd.DataFrame, order_col: str | None) -> tuple[int | None, str]:
    if order_col and order_col in frame.columns:
        series = _string_series(frame, order_col).replace("", pd.NA).dropna()
        return (int(series.nunique()) if not series.empty else None, "distinct_order_id")
    return (int(len(frame)) if len(frame) else None, "row_count_fallback")


def _group_contribution(frame: pd.DataFrame, object_col: str, amount_col: str) -> list[dict[str, Any]]:
    data = pd.DataFrame({"object": _string_series(frame, object_col), "amount": _numeric_series(frame, amount_col)}).dropna()
    if data.empty or data["amount"].sum() == 0:
        return []
    grouped = data.groupby("object")["amount"].sum().sort_values(ascending=False)
    total = float(grouped.sum())
    return [
        {
            "object_id": obj,
            "value": round(float(value), 6),
            "contribution": round(float(value) / total, 6),
        }
        for obj, value in grouped.items()
    ]


def _group_sum(frame: pd.DataFrame, dimension_col: str, measure_col: str) -> list[dict[str, Any]]:
    data = pd.DataFrame(
        {
            "dimension": _string_series(frame, dimension_col).replace("", pd.NA),
            "value": _numeric_series(frame, measure_col),
        }
    ).dropna()
    if data.empty:
        return []
    grouped = data.groupby("dimension")["value"].sum().sort_values(ascending=False)
    return [
        {"dimension": str(dimension), "value": round(float(value), 6)}
        for dimension, value in grouped.items()
    ]


def _group_share(frame: pd.DataFrame, dimension_col: str, measure_col: str) -> list[dict[str, Any]]:
    rows = _group_sum(frame, dimension_col, measure_col)
    total = sum(float(row["value"] or 0) for row in rows)
    if not rows or total == 0:
        return []
    return [
        {
            **row,
            "share": round(float(row["value"]) / total, 6),
        }
        for row in rows
    ]


def _time_sum(frame: pd.DataFrame, time_col: str, measure_col: str, freq: str = "day") -> list[dict[str, Any]]:
    times = _time_series(frame, time_col)
    values = _numeric_series(frame, measure_col)
    data = pd.DataFrame({"time": times, "value": values}).dropna()
    if data.empty:
        return []
    if freq == "month":
        period = data["time"].dt.to_period("M").astype(str)
    elif freq == "week":
        period = data["time"].dt.to_period("W").astype(str)
    else:
        period = data["time"].dt.strftime("%Y-%m-%d")
    grouped = data.assign(period=period).groupby("period")["value"].sum().sort_index()
    return [{"period": str(period_key), "value": round(float(value), 6)} for period_key, value in grouped.items()]


def _distinct_users_by_dimension(frame: pd.DataFrame, dimension_col: str, user_col: str) -> list[dict[str, Any]]:
    data = pd.DataFrame(
        {
            "dimension": _string_series(frame, dimension_col).replace("", pd.NA),
            "user": _string_series(frame, user_col).replace("", pd.NA),
        }
    ).dropna()
    if data.empty:
        return []
    grouped = data.groupby("dimension")["user"].nunique().sort_values(ascending=False)
    return [{"dimension": str(dimension), "value": int(value)} for dimension, value in grouped.items()]


def _returning_users(frame: pd.DataFrame, time_col: str, user_col: str) -> dict[str, Any] | None:
    times = _time_series(frame, time_col)
    users = _string_series(frame, user_col).replace("", pd.NA)
    data = pd.DataFrame({"time": times, "user": users}).dropna()
    if data.empty:
        return None
    data["date"] = data["time"].dt.normalize()
    active_days = data.groupby("user")["date"].nunique()
    returning = active_days[active_days > 1]
    total_users = int(active_days.size)
    returning_users = int(returning.size)
    return {
        "total_users": total_users,
        "returning_users": returning_users,
        "returning_rate": round(returning_users / total_users, 6) if total_users else None,
    }


def _gross_profit(frame: pd.DataFrame, revenue_col: str, cost_col: str) -> float | None:
    revenue = _numeric_series(frame, revenue_col)
    cost = _numeric_series(frame, cost_col)
    valid = revenue.notna() & cost.notna()
    if not valid.any():
        return None
    return float((revenue[valid] - cost[valid]).sum())


def _gross_margin(frame: pd.DataFrame, revenue_col: str, cost_col: str) -> float | None:
    revenue = _numeric_series(frame, revenue_col)
    cost = _numeric_series(frame, cost_col)
    valid = revenue.notna() & cost.notna() & (revenue != 0)
    if not valid.any():
        return None
    margin = (revenue[valid] - cost[valid]) / revenue[valid]
    return float(margin.mean()) if not margin.empty else None


def _asp(frame: pd.DataFrame, revenue_col: str | None, quantity_col: str | None, price_col: str | None) -> tuple[float | None, str]:
    if revenue_col and quantity_col:
        ratio = _ratio(_numeric_series(frame, revenue_col), _numeric_series(frame, quantity_col))
        if not ratio.empty:
            return float(ratio.mean()), "revenue_over_quantity"
    if price_col:
        series = _numeric_series(frame, price_col).dropna()
        if not series.empty:
            return float(series.mean()), "price_average"
    return None, ""


def _inventory_velocity_proxy(frame: pd.DataFrame, inventory_col: str | None, sales_velocity_col: str | None) -> float | None:
    if not inventory_col or not sales_velocity_col:
        return None
    ratio = _ratio(_numeric_series(frame, inventory_col), _numeric_series(frame, sales_velocity_col))
    return float(ratio.mean()) if not ratio.empty else None


def _sell_through_proxy(frame: pd.DataFrame, quantity_col: str | None, inventory_col: str | None) -> float | None:
    if not quantity_col or not inventory_col:
        return None
    ratio = _ratio(_numeric_series(frame, quantity_col), _numeric_series(frame, inventory_col))
    return float(ratio.mean()) if not ratio.empty else None


def _low_rating_rate(frame: pd.DataFrame, rating_col: str) -> float | None:
    ratings = _numeric_series(frame, rating_col).dropna()
    if ratings.empty:
        return None
    return float((ratings <= 2).mean())


def _nonnull_coverage(frame: pd.DataFrame, column: str) -> float | None:
    if column not in frame.columns:
        return None
    series = frame[column]
    denominator = int(len(series))
    if denominator == 0:
        return None
    if pd.api.types.is_numeric_dtype(series):
        numerator = int(series.notna().sum())
    else:
        numerator = int(series.astype("object").notna().sum())
    return round(numerator / denominator, 6)


def _sum_count_ratio(frame: pd.DataFrame, numerator_col: str, denominator_col: str) -> float | None:
    numerator = _numeric_series(frame, numerator_col)
    denominator = _numeric_series(frame, denominator_col)
    valid = numerator.notna() & denominator.notna()
    if not valid.any():
        return None
    denominator_count = int(valid.sum())
    if denominator_count == 0:
        return None
    return float(numerator[valid].sum() / denominator_count)


def _sum_sum_ratio(frame: pd.DataFrame, numerator_col: str, denominator_col: str) -> float | None:
    numerator = _numeric_series(frame, numerator_col).dropna()
    denominator = _numeric_series(frame, denominator_col).dropna()
    if numerator.empty or denominator.empty:
        return None
    denominator_sum = float(denominator.sum())
    if denominator_sum == 0:
        return None
    return float(numerator.sum() / denominator_sum)


def _sum_difference(frame: pd.DataFrame, left_col: str, right_col: str) -> float | None:
    left = _numeric_series(frame, left_col)
    right = _numeric_series(frame, right_col)
    valid = left.notna() & right.notna()
    if not valid.any():
        return None
    return float((left[valid] - right[valid]).sum())


def _difference_over_sum(frame: pd.DataFrame, left_col: str, right_col: str, denominator_col: str) -> float | None:
    left = _numeric_series(frame, left_col)
    right = _numeric_series(frame, right_col)
    denominator = _numeric_series(frame, denominator_col)
    valid = left.notna() & right.notna() & denominator.notna()
    if not valid.any():
        return None
    denominator_sum = float(denominator[valid].sum())
    if denominator_sum == 0:
        return None
    return float((left[valid] - right[valid]).sum() / denominator_sum)


def _complement_rate(frame: pd.DataFrame, indicator_col: str) -> float | None:
    indicator = _numeric_series(frame, indicator_col).dropna()
    if indicator.empty:
        return None
    return float((1 - indicator).mean())


def _categorical_rate(frame: pd.DataFrame, column: str, expected_value: str) -> float | None:
    series = _string_series(frame, column).replace("", pd.NA).dropna()
    if series.empty:
        return None
    normalized_expected = _normalize(expected_value)
    matched = series.map(lambda value: _normalize(value) == normalized_expected)
    return float(matched.mean()) if not matched.empty else None


def _average_time_delta_days(frame: pd.DataFrame, start_col: str, end_col: str) -> float | None:
    start = _time_series(frame, start_col)
    end = _time_series(frame, end_col)
    valid = start.notna() & end.notna()
    if not valid.any():
        return None
    delta = (end[valid] - start[valid]).dt.total_seconds() / 86400
    delta = delta.dropna()
    return float(delta.mean()) if not delta.empty else None


def _orderable_step_field(role_map: dict[str, list[str]]) -> str | None:
    for candidate in role_map.get("step_key", []):
        key = _normalize(candidate)
        if any(token in key for token in ["step", "order", "sequence", "rank"]):
            return candidate
    return None


def _funnel(frame: pd.DataFrame, user_col: str, event_col: str, step_col: str | None) -> list[dict[str, Any]]:
    users = _string_series(frame, user_col)
    if step_col and step_col in frame.columns:
        step_values = _numeric_series(frame, step_col)
        event_values = _string_series(frame, event_col)
        data = pd.DataFrame({"user": users, "event": event_values, "step": step_values}).dropna()
        if data.empty:
            return []
        grouped = data.groupby(["step", "event"])["user"].nunique().reset_index().sort_values("step")
        return [
            {"step": int(row["step"]), "event": row["event"], "users": int(row["user"])}
            for _, row in grouped.iterrows()
        ]
    return []


def _choose_handler(item: AIMetricPlanItem) -> str:
    formula = item.formula_or_logic or ""
    text = _normalize(" ".join([item.metric_id, item.metric_name_cn, item.metric_name_en, item.metric_family, item.grain, formula]))
    if "dau" in text:
        return "dau"
    if "wau" in text:
        return "wau"
    if "mau" in text:
        return "mau"
    if "activeuser" in text or "活跃用户" in item.metric_name_cn:
        return "active_users"
    if "returninguser" in text or "returningbehavior" in text or "returning" in text:
        return "returning_users"
    if "firstseen" in text or "cohort" in text and "retention" not in text:
        return "first_seen"
    if "d1" in text and "retention" in text:
        return "retention_d1"
    if "d7" in text and "retention" in text:
        return "retention_d7"
    if "funnel" in text:
        return "funnel"
    if "ctr" in text:
        return "ctr"
    if "cvr" in text or ("conversion" in text and "click" in text):
        return "cvr"
    if "grossprofit" in text:
        return "gross_profit"
    if "grossmargin" in text:
        return "gross_margin"
    if "aov" in text or "averageordervalue" in text or "客单价" in item.metric_name_cn:
        return "aov"
    if "ordercount" in text or "订单数" in item.metric_name_cn:
        return "order_count"
    if "asp" in text or "sellingprice" in text or "售价" in item.metric_name_cn:
        return "asp"
    if "inventoryturnover" in text or "inventoryvelocity" in text:
        return "inventory_velocity"
    if "sellthrough" in text:
        return "sell_through"
    if "rating" in text or "reviewrisk" in text or "lowrating" in text:
        return "review_risk"
    has_group_sum_formula = (_GROUP_BY_RE.search(formula) or _BY_RE.search(formula)) and _SUM_RE.search(formula)
    if ("share" in text or "占比" in item.metric_name_cn) and has_group_sum_formula:
        return "generic_group_share"
    if has_group_sum_formula:
        if any(token in text for token in ["daily", "weekly", "monthly", "trend", "每日", "每周", "每月", "趋势"]):
            return "generic_time_sum"
        return "generic_group_sum"
    if _COUNT_DISTINCT_RE.search(formula):
        return "generic_distinct_count"
    if ".notna()" in formula.lower():
        return "nonnull_coverage"
    if "where" in formula.lower() and "count(" in formula.lower() and "/" in formula:
        return "categorical_rate"
    if "sum(1 -" in formula.lower() and "/ count(" in formula.lower():
        return "complement_rate"
    if "sum(" in formula.lower() and "/ count(" in formula.lower():
        return "sum_count_ratio"
    if formula.lower().count("sum(") >= 2 and "/ sum(" in formula.lower() and "- sum(" in formula.lower():
        return "difference_over_sum"
    if formula.lower().count("sum(") >= 2 and "/ sum(" in formula.lower():
        return "sum_sum_ratio"
    if formula.lower().count("sum(") >= 2 and "- sum(" in formula.lower():
        return "sum_difference"
    if _AVG_RE.search(formula) and ".dt.total_seconds()" in formula.lower():
        return "time_delta_avg"
    if _AVG_RE.search(formula):
        return "generic_avg"
    if _SUM_RE.search(formula):
        return "generic_sum"
    if "contribution" in text or "ranking" in text or "concentration" in text or "share" in text:
        return "contribution"
    if "gmv" in text or "revenue" in text or "sales" in text and item.metric_family == "scale_metric":
        return "sum_amount"
    return ""


def execute_metric_plan(
    *,
    output_dir: str | Path,
    dataframe: pd.DataFrame,
    semantic_mapping_result: AIFieldSemanticMappingResult,
    metric_plan: AIMetricDerivationPlan | dict[str, Any],
) -> dict[str, Any]:
    plan = metric_plan if isinstance(metric_plan, AIMetricDerivationPlan) else AIMetricDerivationPlan.model_validate(metric_plan)
    role_map = _available_role_map(semantic_mapping_result)
    field_names = set(dataframe.columns.astype(str))
    result_rows: list[dict[str, Any]] = []
    log_rows: list[dict[str, Any]] = []

    for item in plan.metric_plans:
        base = _base_result(item)
        base["source_fields"] = list(dict.fromkeys(item.matched_fields))

        if item.metric_type == "unavailable":
            result = _result_unavailable(item, item.reason or "metric marked unavailable by planner")
        elif item.metric_type == "diagnostic":
            result = _result_unavailable(item, item.reason or "diagnostic only")
        else:
            missing_runtime_fields = [field for field in item.matched_fields if field not in field_names]
            if missing_runtime_fields:
                result = _result_failed(item, f"runtime missing fields: {missing_runtime_fields}")
            else:
                try:
                    handler = _choose_handler(item)
                    if handler == "dau":
                        user_col = _first_field(role_map, "user_key")
                        time_col = _first_field(role_map, "time_key")
                        if user_col and time_col:
                            value = _grouped_distinct_users(dataframe, time_col, user_col, "day")
                            result = {**base, "value": value, "calculation_method": "distinct users by day", "status": "calculated"}
                        else:
                            result = _result_unavailable(item, "date + user_id required")
                    elif handler == "wau":
                        user_col = _first_field(role_map, "user_key")
                        time_col = _first_field(role_map, "time_key")
                        if user_col and time_col:
                            value = _grouped_distinct_users(dataframe, time_col, user_col, "week")
                            result = {**base, "value": value, "calculation_method": "distinct users by week", "status": "calculated"}
                        else:
                            result = _result_unavailable(item, "date + user_id required")
                    elif handler == "mau":
                        user_col = _first_field(role_map, "user_key")
                        time_col = _first_field(role_map, "time_key")
                        if user_col and time_col:
                            value = _grouped_distinct_users(dataframe, time_col, user_col, "month")
                            result = {**base, "value": value, "calculation_method": "distinct users by month", "status": "calculated"}
                        else:
                            result = _result_unavailable(item, "date + user_id required")
                    elif handler == "active_users":
                        user_col = _role_field(dataframe, role_map, "user_key")
                        time_col = _time_field(dataframe, item, role_map)
                        dimension_col = _dimension_field(dataframe, item, role_map)
                        if user_col and time_col and (not dimension_col or dimension_col == time_col):
                            value = _grouped_distinct_users(dataframe, time_col, user_col, "day")
                            result = {**base, "value": value, "calculation_method": f"count_distinct({user_col}) by day({time_col})", "status": _calculated_status(item)}
                        elif user_col and dimension_col:
                            value = _distinct_users_by_dimension(dataframe, dimension_col, user_col)
                            result = {**base, "value": value, "calculation_method": f"count_distinct({user_col}) by {dimension_col}", "status": _calculated_status(item)}
                        else:
                            result = _result_unavailable(item, "user_id + date or dimension required")
                    elif handler == "returning_users":
                        user_col = _role_field(dataframe, role_map, "user_key")
                        time_col = _time_field(dataframe, item, role_map)
                        if user_col and time_col:
                            value = _returning_users(dataframe, time_col, user_col)
                            result = {**base, "value": value, "calculation_method": f"users with distinct active dates > 1 using {user_col}/{time_col}", "status": _calculated_status(item)}
                            if value is None:
                                result["status"] = "unavailable"
                                result["unsupported_reason"] = "empty user/date data"
                        else:
                            result = _result_unavailable(item, "date + user_id required")
                    elif handler == "first_seen":
                        user_col = _first_field(role_map, "user_key")
                        time_col = _first_field(role_map, "time_key")
                        if user_col and time_col:
                            value = _first_seen(dataframe, time_col, user_col)
                            result = {**base, "value": value, "calculation_method": "first seen cohort", "status": "calculated"}
                        else:
                            result = _result_unavailable(item, "date + user_id required")
                    elif handler == "retention_d1":
                        user_col = _first_field(role_map, "user_key")
                        time_col = _first_field(role_map, "time_key")
                        if user_col and time_col:
                            value = _cohort_retention(dataframe, time_col, user_col, 1)
                            result = {**base, "value": value, "calculation_method": "cohort D1 retention", "status": "calculated"}
                        else:
                            result = _result_unavailable(item, "date + user_id required")
                    elif handler == "retention_d7":
                        user_col = _first_field(role_map, "user_key")
                        time_col = _first_field(role_map, "time_key")
                        if user_col and time_col:
                            value = _cohort_retention(dataframe, time_col, user_col, 7)
                            status = "calculated" if value else "unavailable"
                            result = {**base, "value": value, "calculation_method": "cohort D7 retention", "status": status}
                            if not value:
                                result["unsupported_reason"] = "insufficient time window or empty cohort result"
                        else:
                            result = _result_unavailable(item, "date + user_id required")
                    elif handler == "funnel":
                        user_col = _first_field(role_map, "user_key")
                        event_col = _first_field(role_map, "event_field")
                        step_col = _orderable_step_field(role_map)
                        if user_col and event_col and step_col:
                            value = _funnel(dataframe, user_col, event_col, step_col)
                            result = {**base, "value": value, "calculation_method": "ordered funnel distinct users", "status": "calculated"}
                        else:
                            result = _result_unavailable(item, "orderable step field required for funnel")
                    elif handler == "ctr":
                        impression_col = _first_field(role_map, "impression_field")
                        click_col = _first_field(role_map, "click_field")
                        if impression_col and click_col:
                            value = _ctr(dataframe, impression_col, click_col)
                            result = {**base, "value": _format_value(value), "calculation_method": "click / impression", "status": "calculated"}
                        else:
                            result = _result_unavailable(item, "click + impression required")
                    elif handler == "cvr":
                        click_col = _first_field(role_map, "click_field")
                        conversion_col = _first_field(role_map, "conversion_field")
                        visit_col = _first_field(role_map, "impression_field")
                        denominator = click_col or visit_col
                        if conversion_col and denominator:
                            value = _cvr(dataframe, conversion_col, denominator)
                            result = {**base, "value": _format_value(value), "calculation_method": f"{conversion_col} / {denominator}", "status": "calculated"}
                        else:
                            result = _result_unavailable(item, "conversion + click/visit required")
                    elif handler == "sum_amount":
                        amount_col = _first_field(role_map, "amount_field")
                        if amount_col:
                            value = _sum_metric(dataframe, amount_col)
                            result = {**base, "value": _format_value(value), "calculation_method": f"sum({amount_col})", "status": "calculated"}
                        else:
                            result = _result_unavailable(item, "amount field required")
                    elif handler == "order_count":
                        order_col = _first_field(role_map, "order_key")
                        value, method = _distinct_count_or_rowcount(dataframe, order_col)
                        status = "calculated" if order_col else "proxy_calculated"
                        result = {**base, "value": value, "calculation_method": method, "status": status}
                        if not order_col:
                            result["caveat"] = (result["caveat"] + " row count fallback used for order_count").strip()
                    elif handler == "aov":
                        amount_col = _first_field(role_map, "amount_field")
                        order_col = _first_field(role_map, "order_key")
                        order_count, method = _distinct_count_or_rowcount(dataframe, order_col)
                        if amount_col and order_count:
                            value = _sum_metric(dataframe, amount_col)
                            result = {
                                **base,
                                "value": _format_value((value or 0) / order_count),
                                "calculation_method": f"sum({amount_col}) / {method}",
                                "status": "calculated" if order_col else "proxy_calculated",
                            }
                            if not order_col:
                                result["caveat"] = (result["caveat"] + " row count fallback used for order_count").strip()
                        else:
                            result = _result_unavailable(item, "amount + order key or row count required")
                    elif handler == "gross_profit":
                        revenue_col = _first_field(role_map, "amount_field")
                        cost_col = _first_field(role_map, "cost_field")
                        if revenue_col and cost_col:
                            value = _gross_profit(dataframe, revenue_col, cost_col)
                            result = {**base, "value": _format_value(value), "calculation_method": f"{revenue_col} - {cost_col}", "status": "calculated"}
                        else:
                            result = _result_unavailable(item, "revenue + cost required")
                    elif handler == "gross_margin":
                        revenue_col = _first_field(role_map, "amount_field")
                        cost_col = _first_field(role_map, "cost_field")
                        if revenue_col and cost_col:
                            value = _gross_margin(dataframe, revenue_col, cost_col)
                            result = {**base, "value": _format_value(value), "calculation_method": f"({revenue_col} - {cost_col}) / {revenue_col}", "status": "calculated"}
                        else:
                            result = _result_unavailable(item, "revenue + cost required")
                    elif handler == "asp":
                        amount_col = _first_field(role_map, "amount_field")
                        quantity_col = _first_field(role_map, "quantity_field")
                        price_col = _first_field(role_map, "price_field")
                        value, method = _asp(dataframe, amount_col, quantity_col, price_col)
                        if method:
                            result = {**base, "value": _format_value(value), "calculation_method": method, "status": "calculated"}
                        else:
                            result = _result_unavailable(item, "amount + quantity or price required")
                    elif handler == "inventory_velocity":
                        inventory_col = _first_field(role_map, "inventory_field")
                        quantity_col = _first_field(role_map, "quantity_field")
                        if inventory_col and quantity_col:
                            value = _inventory_velocity_proxy(dataframe, inventory_col, quantity_col)
                            result = {**base, "value": _format_value(value), "calculation_method": f"{inventory_col} / {quantity_col}", "status": "proxy_calculated"}
                        else:
                            result = _result_unavailable(item, "inventory + quantity required")
                    elif handler == "sell_through":
                        inventory_col = _first_field(role_map, "inventory_field")
                        quantity_col = _first_field(role_map, "quantity_field")
                        if inventory_col and quantity_col:
                            value = _sell_through_proxy(dataframe, quantity_col, inventory_col)
                            result = {**base, "value": _format_value(value), "calculation_method": f"{quantity_col} / {inventory_col}", "status": "proxy_calculated"}
                        else:
                            result = _result_unavailable(item, "quantity + inventory required")
                    elif handler == "review_risk":
                        rating_col = _first_field(role_map, "rating_field") or _first_field(role_map, "review_score_field")
                        if rating_col:
                            value = _low_rating_rate(dataframe, rating_col)
                            result = {**base, "value": _format_value(value), "calculation_method": f"mean({rating_col} <= 2)", "status": "proxy_calculated"}
                        else:
                            result = _result_unavailable(item, "rating/review_score required")
                    elif handler == "generic_distinct_count":
                        distinct_col = _formula_distinct_field(dataframe, item) or _formula_count_field(dataframe, item)
                        if distinct_col:
                            distinct_series = _string_series(dataframe, distinct_col).replace("", pd.NA).dropna()
                            value = int(distinct_series.nunique()) if not distinct_series.empty else None
                            result = {**base, "value": value, "calculation_method": f"count_distinct({distinct_col})", "status": _calculated_status(item)}
                            result["source_fields"] = list(dict.fromkeys([*base.get("source_fields", []), distinct_col]))
                        else:
                            result = _result_unavailable(item, "COUNT(DISTINCT field) requires resolvable field")
                    elif handler == "generic_avg":
                        avg_col = _formula_avg_field(dataframe, item) or _measure_field(dataframe, item, role_map)
                        if avg_col:
                            value = _mean_metric(dataframe, avg_col)
                            result = {**base, "value": _format_value(value), "calculation_method": f"avg({avg_col})", "status": _calculated_status(item)}
                            result["source_fields"] = list(dict.fromkeys([*base.get("source_fields", []), avg_col]))
                        else:
                            result = _result_unavailable(item, "AVG field required")
                    elif handler == "nonnull_coverage":
                        count_col = _formula_count_field(dataframe, item) or (_matched_fields(dataframe, item)[0] if _matched_fields(dataframe, item) else None)
                        if count_col:
                            value = _nonnull_coverage(dataframe, count_col)
                            result = {**base, "value": _format_value(value), "calculation_method": f"count_nonnull({count_col}) / count({count_col})", "status": _calculated_status(item)}
                            result["source_fields"] = list(dict.fromkeys([*base.get("source_fields", []), count_col]))
                        else:
                            result = _result_unavailable(item, "COUNT(field where field.notna()) / COUNT(field) requires field")
                    elif handler == "categorical_rate":
                        text_fields = _matched_fields(dataframe, item)
                        category_col = next((field for field in text_fields if not _is_numeric_field(dataframe, field)), None)
                        expected_match = re.search(r"==\s*['\"]([^'\"]+)['\"]", item.formula_or_logic or "")
                        expected_value = expected_match.group(1) if expected_match else ""
                        if category_col and expected_value:
                            value = _categorical_rate(dataframe, category_col, expected_value)
                            result = {**base, "value": _format_value(value), "calculation_method": f"mean({category_col} == {expected_value})", "status": _calculated_status(item)}
                            result["source_fields"] = list(dict.fromkeys([*base.get("source_fields", []), category_col]))
                        else:
                            result = _result_unavailable(item, "COUNT(field where field == value) / COUNT(field) requires categorical field and value")
                    elif handler == "complement_rate":
                        indicator_col = _formula_count_field(dataframe, item) or _formula_sum_field(dataframe, item) or _measure_field(dataframe, item, role_map)
                        if indicator_col:
                            value = _complement_rate(dataframe, indicator_col)
                            result = {**base, "value": _format_value(value), "calculation_method": f"mean(1 - {indicator_col})", "status": _calculated_status(item)}
                            result["source_fields"] = list(dict.fromkeys([*base.get("source_fields", []), indicator_col]))
                        else:
                            result = _result_unavailable(item, "SUM(1 - indicator) / COUNT(indicator) requires indicator field")
                    elif handler == "sum_count_ratio":
                        numerator_col = _formula_sum_field(dataframe, item)
                        denominator_col = _formula_count_field(dataframe, item) or numerator_col
                        if numerator_col and denominator_col:
                            value = _sum_count_ratio(dataframe, numerator_col, denominator_col)
                            result = {**base, "value": _format_value(value), "calculation_method": f"sum({numerator_col}) / count({denominator_col})", "status": _calculated_status(item)}
                            result["source_fields"] = list(dict.fromkeys([*base.get("source_fields", []), numerator_col, denominator_col]))
                        else:
                            result = _result_unavailable(item, "SUM(field) / COUNT(field) requires resolvable fields")
                    elif handler == "sum_sum_ratio":
                        sum_fields = _formula_sum_fields(dataframe, item)
                        if len(sum_fields) >= 2:
                            value = _sum_sum_ratio(dataframe, sum_fields[0], sum_fields[1])
                            result = {**base, "value": _format_value(value), "calculation_method": f"sum({sum_fields[0]}) / sum({sum_fields[1]})", "status": _calculated_status(item)}
                            result["source_fields"] = list(dict.fromkeys([*base.get("source_fields", []), *sum_fields[:2]]))
                        else:
                            result = _result_unavailable(item, "SUM(field) / SUM(field) requires two numeric fields")
                    elif handler == "sum_difference":
                        sum_fields = _formula_sum_fields(dataframe, item)
                        if len(sum_fields) >= 2:
                            value = _sum_difference(dataframe, sum_fields[0], sum_fields[1])
                            result = {**base, "value": _format_value(value), "calculation_method": f"sum({sum_fields[0]}) - sum({sum_fields[1]})", "status": _calculated_status(item)}
                            result["source_fields"] = list(dict.fromkeys([*base.get("source_fields", []), *sum_fields[:2]]))
                        else:
                            result = _result_unavailable(item, "SUM(field) - SUM(field) requires two numeric fields")
                    elif handler == "difference_over_sum":
                        sum_fields = _formula_sum_fields(dataframe, item)
                        if len(sum_fields) >= 3:
                            value = _difference_over_sum(dataframe, sum_fields[0], sum_fields[1], sum_fields[2])
                            result = {**base, "value": _format_value(value), "calculation_method": f"(sum({sum_fields[0]}) - sum({sum_fields[1]})) / sum({sum_fields[2]})", "status": _calculated_status(item)}
                            result["source_fields"] = list(dict.fromkeys([*base.get("source_fields", []), *sum_fields[:3]]))
                        elif len(sum_fields) == 2:
                            value = _difference_over_sum(dataframe, sum_fields[0], sum_fields[1], sum_fields[0])
                            result = {**base, "value": _format_value(value), "calculation_method": f"(sum({sum_fields[0]}) - sum({sum_fields[1]})) / sum({sum_fields[0]})", "status": _calculated_status(item)}
                            result["source_fields"] = list(dict.fromkeys([*base.get("source_fields", []), *sum_fields[:2]]))
                        else:
                            result = _result_unavailable(item, "difference-over-sum requires two or three numeric fields")
                    elif handler == "time_delta_avg":
                        matched = _matched_fields(dataframe, item)
                        time_fields = [field for field in matched if _time_series(dataframe, field).notna().any()]
                        if len(time_fields) >= 2:
                            value = _average_time_delta_days(dataframe, time_fields[0], time_fields[1])
                            result = {**base, "value": _format_value(value), "calculation_method": f"avg(({time_fields[1]} - {time_fields[0]}).days)", "status": _calculated_status(item)}
                            result["source_fields"] = list(dict.fromkeys([*base.get("source_fields", []), *time_fields[:2]]))
                        else:
                            result = _result_unavailable(item, "AVG(end_time - start_time) requires two datetime fields")
                    elif handler == "generic_sum":
                        measure_col = _measure_field(dataframe, item, role_map)
                        if measure_col:
                            value = _sum_metric(dataframe, measure_col)
                            result = {**base, "value": _format_value(value), "calculation_method": f"sum({measure_col})", "status": _calculated_status(item)}
                            result["source_fields"] = list(dict.fromkeys([*base.get("source_fields", []), measure_col]))
                        else:
                            result = _result_unavailable(item, "numeric SUM field required")
                    elif handler == "generic_group_sum":
                        dimension_col = _dimension_field(dataframe, item, role_map)
                        measure_col = _measure_field(dataframe, item, role_map)
                        if dimension_col and measure_col:
                            value = _group_sum(dataframe, dimension_col, measure_col)
                            result = {**base, "value": value, "calculation_method": f"groupby({dimension_col}).sum({measure_col})", "status": _calculated_status(item)}
                            result["source_fields"] = list(dict.fromkeys([*base.get("source_fields", []), dimension_col, measure_col]))
                        else:
                            result = _result_unavailable(item, "GROUP BY dimension + SUM numeric field required")
                    elif handler == "generic_group_share":
                        dimension_col = _dimension_field(dataframe, item, role_map)
                        measure_col = _measure_field(dataframe, item, role_map)
                        if dimension_col and measure_col:
                            value = _group_share(dataframe, dimension_col, measure_col)
                            result = {**base, "value": value, "calculation_method": f"groupby({dimension_col}).sum({measure_col}) / sum({measure_col})", "status": _calculated_status(item)}
                            result["source_fields"] = list(dict.fromkeys([*base.get("source_fields", []), dimension_col, measure_col]))
                        else:
                            result = _result_unavailable(item, "GROUP BY dimension + SUM numeric field required")
                    elif handler == "generic_time_sum":
                        time_col = _time_field(dataframe, item, role_map)
                        measure_col = _measure_field(dataframe, item, role_map)
                        if time_col and measure_col:
                            value = _time_sum(dataframe, time_col, measure_col)
                            result = {**base, "value": value, "calculation_method": f"groupby(day({time_col})).sum({measure_col})", "status": _calculated_status(item)}
                            result["source_fields"] = list(dict.fromkeys([*base.get("source_fields", []), time_col, measure_col]))
                        else:
                            result = _result_unavailable(item, "time field + SUM numeric field required")
                    elif handler == "contribution":
                        object_col = _dimension_field(dataframe, item, role_map) or _first_field(role_map, "object_key")
                        amount_col = _measure_field(dataframe, item, role_map) or _first_field(role_map, "amount_field")
                        if object_col and amount_col:
                            value = _group_contribution(dataframe, object_col, amount_col)
                            result = {**base, "value": value, "calculation_method": f"groupby({object_col}).sum({amount_col}) with contribution", "status": "calculated"}
                        else:
                            result = _result_unavailable(item, "object + amount required")
                    else:
                        result = _result_unavailable(item, "no deterministic handler matched metric plan")
                except Exception as exc:
                    result = _result_failed(item, str(exc))

        result_rows.append(result)
        log_rows.append(
            {
                "metric_id": item.metric_id,
                "metric_name_cn": item.metric_name_cn,
                "status": result["status"],
                "source_fields": " / ".join(result.get("source_fields") or []),
                "formula": result.get("formula", ""),
                "calculation_method": result.get("calculation_method", ""),
                "evidence_level": result.get("evidence_level", ""),
                "confidence": result.get("confidence", ""),
                "caveat": result.get("caveat", ""),
                "unsupported_reason": result.get("unsupported_reason", ""),
            }
        )

    metric_dir = _metric_dir(output_dir)
    result_payload = {
        "trace_id": plan.trace_id,
        "provider": plan.provider,
        "model": plan.model,
        "results": result_rows,
        "summary": {
            "calculated_count": sum(1 for row in result_rows if row["status"] == "calculated"),
            "proxy_calculated_count": sum(1 for row in result_rows if row["status"] == "proxy_calculated"),
            "unavailable_count": sum(1 for row in result_rows if row["status"] == "unavailable"),
            "failed_count": sum(1 for row in result_rows if row["status"] == "failed"),
        },
    }
    _write_json(metric_dir / "semantic_metric_result.json", result_payload)

    log_path = metric_dir / "metric_derivation_log.csv"
    with log_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "metric_id",
                "metric_name_cn",
                "status",
                "source_fields",
                "formula",
                "calculation_method",
                "evidence_level",
                "confidence",
                "caveat",
                "unsupported_reason",
            ],
        )
        writer.writeheader()
        writer.writerows(log_rows)

    return {
        "semantic_metric_result_path": str((metric_dir / "semantic_metric_result.json").resolve()),
        "metric_derivation_log_path": str(log_path.resolve()),
        "result_payload": result_payload,
        "log_rows": log_rows,
    }


__all__ = ["execute_metric_plan"]
