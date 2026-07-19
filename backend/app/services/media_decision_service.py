from __future__ import annotations

import math
import re
from typing import Any

import numpy as np
import pandas as pd


ESTIMATE_TOKENS = ("预估", "预计", "计划", "目标", "estimate", "estimated", "forecast", "plan", "planned", "target")
ACTUAL_TOKENS = ("监测", "实际", "实绩", "actual", "observed", "monitor", "measured", "served", "delivery", "delivered")
SPEND_TOKENS = ("花费", "消耗", "成本", "费用", "预算", "spend", "cost", "budget")

TRADING_MODE_KEYWORDS = {
    "程序化PD池": ("pd池", "程序化pd", "程序化"),
    "PDB": ("pdb",),
    "PMP": ("pmp",),
    "保量": ("保量",),
    "直采": ("直采",),
}

AD_FORMAT_KEYWORDS = {
    "开屏": ("开屏", "开机"),
    "全屏闪屏": ("闪屏",),
    "前贴片": ("前贴片",),
    "暂停页": ("暂停",),
    "信息流": ("信息流",),
    "Banner": ("banner",),
    "视频首焦": ("视频首焦",),
    "品牌头条": ("品牌头条",),
}

PLATFORM_HINTS = ("bilibili", "优酷", "芒果", "快手", "抖音", "微博", "腾讯", "小红书")


def _semantic_role_columns(program_bundle: dict[str, Any], role: str) -> list[str]:
    role_summary = program_bundle.get("semantic_mapping", {}).get("role_summary", {})
    return [str(item.get("column")) for item in role_summary.get(role, []) if item.get("column")]


def _column_token_score(column_name: str, include: tuple[str, ...] = (), exclude: tuple[str, ...] = ()) -> int:
    normalized = str(column_name).strip().lower()
    score = 0
    for token in include:
        if token and token.lower() in normalized:
            score += 3
    for token in exclude:
        if token and token.lower() in normalized:
            score -= 4
    return score


def _pick_role_column(columns: list[str], *, include: tuple[str, ...] = (), exclude: tuple[str, ...] = ()) -> str | None:
    if not columns:
        return None
    ranked = sorted(
        columns,
        key=lambda column: (_column_token_score(column, include=include, exclude=exclude), -len(str(column)), str(column)),
        reverse=True,
    )
    if include and _column_token_score(ranked[0], include=include, exclude=exclude) <= 0:
        return None
    return ranked[0]


def _metric_columns(program_bundle: dict[str, Any]) -> dict[str, str | None]:
    reach_columns = _semantic_role_columns(program_bundle, "reach")
    interaction_columns = _semantic_role_columns(program_bundle, "interaction")
    spend_columns = _semantic_role_columns(program_bundle, "spend")
    return {
        "estimated_reach": _pick_role_column(reach_columns, include=ESTIMATE_TOKENS, exclude=ACTUAL_TOKENS),
        "actual_reach": _pick_role_column(reach_columns, include=ACTUAL_TOKENS, exclude=ESTIMATE_TOKENS) or _pick_role_column(reach_columns, exclude=ESTIMATE_TOKENS),
        "estimated_interaction": _pick_role_column(interaction_columns, include=ESTIMATE_TOKENS, exclude=ACTUAL_TOKENS),
        "actual_interaction": _pick_role_column(interaction_columns, include=ACTUAL_TOKENS, exclude=ESTIMATE_TOKENS) or _pick_role_column(interaction_columns, exclude=ESTIMATE_TOKENS),
        "spend": _pick_role_column(spend_columns, include=SPEND_TOKENS) or (spend_columns[0] if spend_columns else None),
        "date": (_semantic_role_columns(program_bundle, "time") or [None])[0],
        "media": (_semantic_role_columns(program_bundle, "media") or [None])[0],
        "device": (_semantic_role_columns(program_bundle, "device") or [None])[0],
        "placement": (_semantic_role_columns(program_bundle, "placement") or [None])[0],
    }


def _to_numeric(frame: pd.DataFrame, column: str | None) -> pd.Series:
    if not column or column not in frame.columns:
        return pd.Series(dtype="float64")
    return pd.to_numeric(frame[column], errors="coerce")


def _safe_ratio(numerator: float | int | None, denominator: float | int | None) -> float | None:
    if numerator is None or denominator in {None, 0}:
        return None
    try:
        denominator_value = float(denominator)
        if denominator_value == 0:
            return None
        return float(numerator) / denominator_value
    except Exception:
        return None


def _format_confidence(value: float) -> str:
    if value >= 0.75:
        return "high"
    if value >= 0.45:
        return "medium"
    return "low"


def _time_grain(date_series: pd.Series) -> str:
    if date_series.empty:
        return "unknown"
    normalized = date_series.dt.normalize().dropna().sort_values().unique()
    if len(normalized) <= 1:
        return "single_day"
    normalized_series = pd.Series(pd.to_datetime(normalized))
    if normalized_series.dt.day.nunique() > 1:
        return "daily"
    diffs = np.diff(normalized).astype("timedelta64[D]").astype(int)
    median_gap = float(np.median(diffs)) if len(diffs) else 0.0
    if median_gap <= 1.5:
        return "daily"
    if median_gap <= 8:
        return "weekly"
    if normalized_series.dt.day.isin([1]).all():
        return "monthly"
    return "monthly"


def _parse_filename_range(filename: str, actual_year: int | None) -> dict[str, Any]:
    text = str(filename)
    patterns = [
        re.compile(r"(?P<year>\d{4})[.\-_/]?(?P<start_month>\d{1,2})[.\-_/]?(?P<start_day>\d{1,2})\s*[-~至]\s*(?P<end_month>\d{1,2})[.\-_/]?(?P<end_day>\d{1,2})"),
        re.compile(r"(?<!\d)(?P<start_month>\d{2})(?P<start_day>\d{2})\s*[-~至]\s*(?P<end_month>\d{2})(?P<end_day>\d{2})(?!\d)"),
    ]
    for pattern in patterns:
        match = pattern.search(text)
        if not match:
            continue
        parts = match.groupdict()
        year = int(parts.get("year") or actual_year or pd.Timestamp.utcnow().year)
        try:
            start = pd.Timestamp(year=year, month=int(parts["start_month"]), day=int(parts["start_day"]))
            end = pd.Timestamp(year=year, month=int(parts["end_month"]), day=int(parts["end_day"]))
            return {"start": start, "end": end, "matched_text": match.group(0)}
        except Exception:
            continue
    return {"start": None, "end": None, "matched_text": ""}


def analyze_data_scope(frame: pd.DataFrame, filename: str, program_bundle: dict[str, Any]) -> dict[str, Any]:
    columns = _metric_columns(program_bundle)
    date_column = columns["date"]
    date_series = pd.to_datetime(frame[date_column], errors="coerce") if date_column and date_column in frame.columns else pd.Series(dtype="datetime64[ns]")
    valid_dates = date_series.dropna()
    date_min = valid_dates.min() if not valid_dates.empty else None
    date_max = valid_dates.max() if not valid_dates.empty else None
    parsed_range = _parse_filename_range(filename, int(date_max.year) if date_max is not None else None)
    duplicate_count = int(frame.duplicated().sum())
    grain = _time_grain(valid_dates)
    filename_conflict = False
    if parsed_range["start"] is not None and date_min is not None and date_max is not None:
        filename_conflict = bool(date_min.normalize() < parsed_range["start"].normalize() or date_max.normalize() > parsed_range["end"].normalize())
    coverage_days = int(valid_dates.dt.normalize().nunique()) if not valid_dates.empty else 0
    return {
        "date_column": date_column,
        "date_min": date_min,
        "date_max": date_max,
        "valid_sample_count": int(valid_dates.shape[0]),
        "time_grain": grain,
        "empty_date_count": int(date_series.isna().sum()) if not date_series.empty else int(len(frame)),
        "duplicate_record_count": duplicate_count,
        "coverage_days": coverage_days,
        "filename_range_start": parsed_range["start"],
        "filename_range_end": parsed_range["end"],
        "filename_range_text": parsed_range["matched_text"],
        "filename_conflict": filename_conflict,
    }


def _row_metric_distribution(numerator: pd.Series, denominator: pd.Series) -> dict[str, float | None]:
    valid = numerator.notna() & denominator.notna() & (denominator != 0)
    if valid.sum() == 0:
        return {"row_mean": None, "median": None, "p25": None, "p75": None, "std": None, "outlier_ratio": None}
    values = numerator[valid] / denominator[valid]
    q1 = float(values.quantile(0.25))
    q3 = float(values.quantile(0.75))
    iqr = q3 - q1
    if iqr == 0:
        outlier_ratio = 0.0
    else:
        mask = (values < (q1 - 1.5 * iqr)) | (values > (q3 + 1.5 * iqr))
        outlier_ratio = float(mask.mean())
    return {
        "row_mean": float(values.mean()),
        "median": float(values.median()),
        "p25": float(values.quantile(0.25)),
        "p75": float(values.quantile(0.75)),
        "std": float(values.std(ddof=0)),
        "outlier_ratio": outlier_ratio,
    }


def compute_weighted_metrics(frame: pd.DataFrame, program_bundle: dict[str, Any]) -> dict[str, Any]:
    columns = _metric_columns(program_bundle)
    estimated_reach = _to_numeric(frame, columns["estimated_reach"])
    actual_reach = _to_numeric(frame, columns["actual_reach"])
    estimated_interaction = _to_numeric(frame, columns["estimated_interaction"])
    actual_interaction = _to_numeric(frame, columns["actual_interaction"])
    spend = _to_numeric(frame, columns["spend"])

    overall = {
        "total_estimated_reach": float(estimated_reach.sum()) if not estimated_reach.empty else None,
        "total_actual_reach": float(actual_reach.sum()) if not actual_reach.empty else None,
        "total_estimated_interaction": float(estimated_interaction.sum()) if not estimated_interaction.empty else None,
        "total_actual_interaction": float(actual_interaction.sum()) if not actual_interaction.empty else None,
        "total_spend": float(spend.sum()) if not spend.empty else None,
        "weighted_ctr": _safe_ratio(float(actual_interaction.sum()) if not actual_interaction.empty else None, float(actual_reach.sum()) if not actual_reach.empty else None),
        "weighted_exposure_delivery": _safe_ratio(float(actual_reach.sum()) if not actual_reach.empty else None, float(estimated_reach.sum()) if not estimated_reach.empty else None),
        "weighted_click_delivery": _safe_ratio(float(actual_interaction.sum()) if not actual_interaction.empty else None, float(estimated_interaction.sum()) if not estimated_interaction.empty else None),
        "weighted_cpm": _safe_ratio(float(spend.sum() * 1000) if not spend.empty else None, float(actual_reach.sum()) if not actual_reach.empty else None),
        "weighted_cpc": _safe_ratio(float(spend.sum()) if not spend.empty else None, float(actual_interaction.sum()) if not actual_interaction.empty else None),
    }
    distributions = {
        "ctr": _row_metric_distribution(actual_interaction, actual_reach),
        "exposure_delivery": _row_metric_distribution(actual_reach, estimated_reach),
        "click_delivery": _row_metric_distribution(actual_interaction, estimated_interaction),
    }
    click_delivery = overall["weighted_click_delivery"]
    click_risk = click_delivery is not None and (click_delivery > 1.8 or click_delivery < 0.5)
    exposure_delivery = overall["weighted_exposure_delivery"]
    exposure_risk = exposure_delivery is not None and (exposure_delivery > 1.2 or exposure_delivery < 0.8)
    return {
        "columns": columns,
        "overall": overall,
        "distributions": distributions,
        "click_risk": click_risk,
        "exposure_risk": exposure_risk,
    }


def _window_key(date_series: pd.Series, grain: str) -> pd.Series:
    if grain == "daily":
        return date_series.dt.strftime("%Y-%m-%d")
    if grain == "weekly":
        return date_series.dt.to_period("W").astype(str)
    return date_series.dt.to_period("M").astype(str)


def _combo_frame(frame: pd.DataFrame, columns: dict[str, str | None]) -> pd.DataFrame:
    group_columns = [column for column in [columns["media"], columns["device"], columns["placement"]] if column and column in frame.columns]
    actual_reach = columns["actual_reach"]
    if len(group_columns) < 2 or not actual_reach:
        return pd.DataFrame()
    selected_columns = list(dict.fromkeys(group_columns + [column for column in columns.values() if column and column in frame.columns]))
    working = frame[selected_columns].copy()
    for key in ("estimated_reach", "actual_reach", "estimated_interaction", "actual_interaction", "spend"):
        column = columns[key]
        if column and column in working.columns:
            working[column] = pd.to_numeric(working[column], errors="coerce")
    working = working.dropna(subset=[actual_reach])
    if working.empty:
        return pd.DataFrame()
    agg_map = {actual_reach: "sum"}
    for key in ("estimated_reach", "estimated_interaction", "actual_interaction", "spend"):
        column = columns[key]
        if column and column in working.columns:
            agg_map[column] = "sum"
    grouped = working.groupby(group_columns, dropna=False).agg(agg_map).reset_index()
    grouped["combo"] = grouped[group_columns].fillna("Unknown").astype(str).agg(" / ".join, axis=1)
    total = float(grouped[actual_reach].sum())
    grouped["reach_share"] = np.where(total > 0, grouped[actual_reach] / total, np.nan)
    if columns["actual_interaction"] and columns["actual_interaction"] in grouped.columns:
        grouped["ctr"] = np.where(grouped[actual_reach] > 0, grouped[columns["actual_interaction"]] / grouped[actual_reach], np.nan)
    if columns["estimated_reach"] and columns["estimated_reach"] in grouped.columns:
        grouped["exposure_delivery"] = np.where(grouped[columns["estimated_reach"]] > 0, grouped[actual_reach] / grouped[columns["estimated_reach"]], np.nan)
        grouped["absolute_exposure_gap"] = grouped[actual_reach] - grouped[columns["estimated_reach"]]
    if columns["actual_interaction"] and columns["estimated_interaction"] and columns["actual_interaction"] in grouped.columns and columns["estimated_interaction"] in grouped.columns:
        grouped["click_delivery"] = np.where(grouped[columns["estimated_interaction"]] > 0, grouped[columns["actual_interaction"]] / grouped[columns["estimated_interaction"]], np.nan)
    return grouped.sort_values(actual_reach, ascending=False)


def _window_presence(frame: pd.DataFrame, columns: dict[str, str | None], grain: str) -> pd.DataFrame:
    date_column = columns["date"]
    actual_reach = columns["actual_reach"]
    if not date_column or date_column not in frame.columns or not actual_reach:
        return pd.DataFrame()
    group_columns = [column for column in [columns["media"], columns["device"], columns["placement"]] if column and column in frame.columns]
    if len(group_columns) < 2:
        return pd.DataFrame()
    selected_columns = list(dict.fromkeys(group_columns + [date_column, actual_reach, columns["actual_interaction"], columns["estimated_reach"], columns["estimated_interaction"]]))
    working = frame[[column for column in selected_columns if column]].copy()
    working[date_column] = pd.to_datetime(working[date_column], errors="coerce")
    working[actual_reach] = pd.to_numeric(working[actual_reach], errors="coerce")
    if columns["actual_interaction"] and columns["actual_interaction"] in working.columns:
        working[columns["actual_interaction"]] = pd.to_numeric(working[columns["actual_interaction"]], errors="coerce")
    if columns["estimated_reach"] and columns["estimated_reach"] in working.columns:
        working[columns["estimated_reach"]] = pd.to_numeric(working[columns["estimated_reach"]], errors="coerce")
    if columns["estimated_interaction"] and columns["estimated_interaction"] in working.columns:
        working[columns["estimated_interaction"]] = pd.to_numeric(working[columns["estimated_interaction"]], errors="coerce")
    working = working.dropna(subset=[date_column, actual_reach])
    if working.empty:
        return pd.DataFrame()
    working["window"] = _window_key(working[date_column], grain)
    agg_map = {actual_reach: "sum"}
    if columns["actual_interaction"] and columns["actual_interaction"] in working.columns:
        agg_map[columns["actual_interaction"]] = "sum"
    if columns["estimated_reach"] and columns["estimated_reach"] in working.columns:
        agg_map[columns["estimated_reach"]] = "sum"
    if columns["estimated_interaction"] and columns["estimated_interaction"] in working.columns:
        agg_map[columns["estimated_interaction"]] = "sum"
    grouped = working.groupby(group_columns + ["window"], dropna=False).agg(agg_map).reset_index()
    grouped["combo"] = grouped[group_columns].fillna("Unknown").astype(str).agg(" / ".join, axis=1)
    if columns["actual_interaction"] and columns["actual_interaction"] in grouped.columns:
        grouped["ctr"] = np.where(grouped[actual_reach] > 0, grouped[columns["actual_interaction"]] / grouped[actual_reach], np.nan)
    if columns["estimated_reach"] and columns["estimated_reach"] in grouped.columns:
        grouped["exposure_delivery"] = np.where(grouped[columns["estimated_reach"]] > 0, grouped[actual_reach] / grouped[columns["estimated_reach"]], np.nan)
    return grouped


def _stability_rows(frame: pd.DataFrame, columns: dict[str, str | None], grain: str, benchmarks: dict[str, float | None]) -> list[dict[str, Any]]:
    window_frame = _window_presence(frame, columns, grain)
    if window_frame.empty:
        return []
    reach_column = columns["actual_reach"]
    rows: list[dict[str, Any]] = []
    total_windows = int(window_frame["window"].nunique())
    for combo, group in window_frame.groupby("combo"):
        reach_series = group[reach_column]
        total_reach = float(reach_series.sum())
        top_window_share = float(reach_series.max() / total_reach) if total_reach else 0.0
        mean_value = float(reach_series.mean()) if len(reach_series) else 0.0
        reach_cv = float(reach_series.std(ddof=0) / mean_value) if mean_value else math.inf
        presence = int(group["window"].nunique())
        avg_ctr = float(group["ctr"].mean()) if "ctr" in group and group["ctr"].notna().any() else None
        avg_delivery = float(group["exposure_delivery"].mean()) if "exposure_delivery" in group and group["exposure_delivery"].notna().any() else None
        high_efficiency = avg_ctr is not None and benchmarks.get("high_efficiency_threshold") is not None and avg_ctr >= float(benchmarks["high_efficiency_threshold"])
        stable = presence >= 2 and top_window_share <= 0.6 and reach_cv <= 1.0
        if high_efficiency and stable:
            label = "高效率且稳定"
        elif high_efficiency:
            label = "高效率但低稳定性"
        elif total_reach >= float(benchmarks.get("high_scale_threshold") or 0) and reach_cv > 1.0:
            label = "规模大但波动高"
        elif total_reach >= float(benchmarks.get("high_scale_threshold") or 0):
            label = "规模大且相对稳定"
        else:
            label = "样本较小或波动未定"
        rows.append(
            {
                "combo": combo,
                "windows_present": presence,
                "window_coverage": float(presence / max(total_windows, 1)),
                "top_window_share": top_window_share,
                "reach_cv": reach_cv if math.isfinite(reach_cv) else None,
                "avg_ctr": avg_ctr,
                "avg_exposure_delivery": avg_delivery,
                "stability_label": label,
                "stable": stable,
            }
        )
    rows.sort(key=lambda row: (row["stable"], row["window_coverage"]), reverse=True)
    return rows


def build_bias_review(frame: pd.DataFrame, program_bundle: dict[str, Any]) -> dict[str, Any]:
    columns = _metric_columns(program_bundle)
    combo_frame = _combo_frame(frame, columns)
    if combo_frame.empty or "absolute_exposure_gap" not in combo_frame:
        return {"rows": [], "over_delivery": [], "under_delivery": [], "top_contributor": None}
    total_absolute_gap = float(combo_frame["absolute_exposure_gap"].abs().sum()) or 1.0
    combo_frame = combo_frame.copy()
    combo_frame["gap_direction"] = np.where(combo_frame["absolute_exposure_gap"] >= 0, "超投放", "欠投放")
    combo_frame["weighted_gap_contribution"] = combo_frame["absolute_exposure_gap"].abs() / total_absolute_gap
    rows = [
        {
            "对象": str(row["combo"]),
            "方向": str(row["gap_direction"]),
            "绝对偏差量": float(row["absolute_exposure_gap"]),
            "相对偏差率": float(row["exposure_delivery"] - 1) if pd.notna(row.get("exposure_delivery")) else None,
            "加权偏差贡献": float(row["weighted_gap_contribution"]),
        }
        for _, row in combo_frame.sort_values("weighted_gap_contribution", ascending=False).head(12).iterrows()
    ]
    return {
        "rows": rows,
        "over_delivery": [row for row in rows if row["方向"] == "超投放"][:6],
        "under_delivery": [row for row in rows if row["方向"] == "欠投放"][:6],
        "top_contributor": rows[0] if rows else None,
    }


def analyze_window_change(frame: pd.DataFrame, program_bundle: dict[str, Any], scope: dict[str, Any]) -> dict[str, Any]:
    columns = _metric_columns(program_bundle)
    date_column = columns["date"]
    actual_reach = columns["actual_reach"]
    if not date_column or not actual_reach:
        return {"rows": [], "low_confidence": True, "summary": []}
    working = frame.copy()
    working[date_column] = pd.to_datetime(working[date_column], errors="coerce")
    working[actual_reach] = pd.to_numeric(working[actual_reach], errors="coerce")
    working = working.dropna(subset=[date_column, actual_reach])
    if working.empty:
        return {"rows": [], "low_confidence": True, "summary": []}
    grain = "daily" if scope["time_grain"] in {"daily", "single_day"} else scope["time_grain"]
    working["window"] = _window_key(working[date_column], grain)
    windows = sorted(working["window"].dropna().unique())
    if len(windows) < 2:
        return {"rows": [], "low_confidence": True, "summary": []}
    current_window, previous_window = windows[-1], windows[-2]
    group_candidates = [column for column in [columns["media"], columns["device"], columns["placement"]] if column and column in working.columns]
    if not group_candidates:
        return {"rows": [], "low_confidence": True, "summary": []}
    working["driver"] = working[group_candidates].fillna("Unknown").astype(str).agg(" / ".join, axis=1)
    grouped = working.groupby(["window", "driver"], dropna=False)[actual_reach].sum().reset_index()
    current = grouped[grouped["window"] == current_window].set_index("driver")[actual_reach]
    previous = grouped[grouped["window"] == previous_window].set_index("driver")[actual_reach]
    all_drivers = current.index.union(previous.index)
    total_change = float(current.sum() - previous.sum())
    contribution_base = abs(total_change) if abs(total_change) > 0 else float((current - previous).abs().sum()) or 1.0
    change_rows: list[dict[str, Any]] = []
    for driver in all_drivers:
        current_value = float(current.get(driver, 0.0))
        previous_value = float(previous.get(driver, 0.0))
        delta = current_value - previous_value
        change_rows.append(
            {
                "对象": str(driver),
                "上一窗口": previous_value,
                "最新窗口": current_value,
                "变化量": delta,
                "贡献占比": abs(delta) / contribution_base,
            }
        )
    change_rows.sort(key=lambda row: abs(row["变化量"]), reverse=True)
    top_share = sum(row["贡献占比"] for row in change_rows[:3])
    missing_drivers = [row["对象"] for row in change_rows if row["上一窗口"] > 0 and row["最新窗口"] == 0][:5]
    previous_counts = working.groupby("window").size().sort_index()
    latest_window_count = int(working[working["window"] == current_window].shape[0])
    latest_window_incomplete = latest_window_count < 0.5 * float(previous_counts.iloc[:-1].median()) if len(previous_counts) > 2 else False
    low_confidence = bool(scope["filename_conflict"] or latest_window_incomplete)
    summary = [f"最新窗口 `{current_window}` 相对上一窗口 `{previous_window}` 的变化主要由前 3 个组合贡献了 {top_share:.1%}。"]
    if missing_drivers:
        summary.append(f"上一窗口有投放、最新窗口直接归零的组合包括 {', '.join(missing_drivers[:3])}，这更像排期断档或窗口不完整。")
    if latest_window_incomplete:
        summary.append("最新窗口记录量明显低于此前窗口，中断或监测延迟的可能性较高，因此异常结论降为低置信。")
    return {
        "current_window": current_window,
        "previous_window": previous_window,
        "rows": change_rows[:12],
        "low_confidence": low_confidence,
        "latest_window_incomplete": latest_window_incomplete,
        "summary": summary,
    }


def _extract_token(text: str, keywords: dict[str, tuple[str, ...]]) -> str | None:
    lowered = text.lower()
    for label, tokens in keywords.items():
        if any(token in lowered for token in tokens):
            return label
    return None


def parse_placement_field(frame: pd.DataFrame, program_bundle: dict[str, Any]) -> dict[str, Any]:
    placement_column = (_semantic_role_columns(program_bundle, "placement") or [None])[0]
    if not placement_column or placement_column not in frame.columns:
        return {"placement_column": None, "confidence": "low", "rows": [], "summary": []}
    values = frame[placement_column].dropna().astype(str)
    if values.empty:
        return {"placement_column": placement_column, "confidence": "low", "rows": [], "summary": []}
    parsed_rows: list[dict[str, Any]] = []
    extracted_scores: list[int] = []
    for raw in values.head(80):
        platform_tag = next((hint for hint in PLATFORM_HINTS if hint.lower() in raw.lower()), "")
        trading_mode = _extract_token(raw, TRADING_MODE_KEYWORDS) or ""
        ad_format = _extract_token(raw, AD_FORMAT_KEYWORDS) or ""
        bracket_tags = re.findall(r"[【\[](.*?)[】\]]", raw)
        primary_tokens = [token.strip() for token in re.split(r"[/\-]", raw) if token.strip()]
        product_line = ""
        for token in primary_tokens[:4]:
            lowered = token.lower()
            if trading_mode and trading_mode.lower() in lowered:
                continue
            if ad_format and ad_format.lower() in lowered:
                continue
            if any(hint.lower() in lowered for hint in PLATFORM_HINTS):
                continue
            if not product_line:
                product_line = token
                break
        resource_tag = bracket_tags[0] if bracket_tags else ""
        extracted = int(bool(product_line)) + int(bool(ad_format)) + int(bool(trading_mode)) + int(bool(resource_tag)) + int(bool(platform_tag))
        extracted_scores.append(extracted)
        parsed_rows.append(
            {
                "原始点位": raw,
                "产品线": product_line or "Unknown",
                "广告形态": ad_format or "Unknown",
                "交易模式": trading_mode or "Unknown",
                "资源包标签": resource_tag or "Unknown",
                "平台附加标签": platform_tag or "Unknown",
            }
        )
    average_score = float(np.mean(extracted_scores)) if extracted_scores else 0.0
    confidence = _format_confidence(min(1.0, average_score / 4.0))
    summary = []
    if confidence != "low":
        top_formats = pd.Series([row["广告形态"] for row in parsed_rows if row["广告形态"] != "Unknown"]).value_counts().head(3)
        top_modes = pd.Series([row["交易模式"] for row in parsed_rows if row["交易模式"] != "Unknown"]).value_counts().head(3)
        if not top_formats.empty:
            summary.append(f"广告形态主要集中在 {', '.join(top_formats.index.tolist())}。")
        if not top_modes.empty:
            summary.append(f"采买方式主要集中在 {', '.join(top_modes.index.tolist())}。")
    else:
        summary.append("点位字段仍然混有多重语义，字段标准化不足，相关洞察仅供参考。")
    return {
        "placement_column": placement_column,
        "confidence": confidence,
        "rows": parsed_rows[:12],
        "summary": summary,
    }


def build_parsed_dimension_reviews(
    frame: pd.DataFrame,
    program_bundle: dict[str, Any],
    placement_parse: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    placement_column = placement_parse.get("placement_column")
    rows = placement_parse.get("rows") or []
    if not placement_column or not rows or placement_column not in frame.columns:
        return {"product_line": [], "ad_format": [], "trading_mode": [], "platform_tag": []}

    parsed_lookup = {str(row["原始点位"]): row for row in rows}
    columns = _metric_columns(program_bundle)
    actual_reach = columns["actual_reach"]
    actual_interaction = columns["actual_interaction"]
    estimated_reach = columns["estimated_reach"]
    if not actual_reach:
        return {"product_line": [], "ad_format": [], "trading_mode": [], "platform_tag": []}

    working = frame.copy()
    working["_placement_raw"] = working[placement_column].astype(str)
    working["_product_line"] = working["_placement_raw"].map(lambda value: parsed_lookup.get(value, {}).get("产品线", "Unknown"))
    working["_ad_format"] = working["_placement_raw"].map(lambda value: parsed_lookup.get(value, {}).get("广告形态", "Unknown"))
    working["_trading_mode"] = working["_placement_raw"].map(lambda value: parsed_lookup.get(value, {}).get("交易模式", "Unknown"))
    working["_platform_tag"] = working["_placement_raw"].map(lambda value: parsed_lookup.get(value, {}).get("平台附加标签", "Unknown"))

    for column in [actual_reach, actual_interaction, estimated_reach]:
        if column and column in working.columns:
            working[column] = pd.to_numeric(working[column], errors="coerce")
    working = working.dropna(subset=[actual_reach])
    if working.empty:
        return {"product_line": [], "ad_format": [], "trading_mode": [], "platform_tag": []}

    def summarize(group_column: str) -> list[dict[str, Any]]:
        grouped = (
            working.groupby(group_column, dropna=False)[[column for column in [actual_reach, actual_interaction, estimated_reach] if column]]
            .sum()
            .reset_index()
            .rename(columns={group_column: "segment"})
        )
        total_reach = float(grouped[actual_reach].sum()) or 1.0
        grouped["reach_share"] = grouped[actual_reach] / total_reach
        if actual_interaction and actual_interaction in grouped.columns:
            grouped["ctr"] = np.where(grouped[actual_reach] > 0, grouped[actual_interaction] / grouped[actual_reach], np.nan)
        if estimated_reach and estimated_reach in grouped.columns:
            grouped["delivery_rate"] = np.where(grouped[estimated_reach] > 0, grouped[actual_reach] / grouped[estimated_reach], np.nan)
        grouped = grouped[grouped["segment"].notna() & (grouped["segment"] != "Unknown")]
        grouped = grouped.sort_values(actual_reach, ascending=False)
        result = []
        for _, row in grouped.head(8).iterrows():
            result.append(
                {
                    "segment": str(row["segment"]),
                    "reach": float(row[actual_reach]),
                    "reach_share": float(row["reach_share"]),
                    "ctr": float(row["ctr"]) if "ctr" in row and pd.notna(row.get("ctr")) else None,
                    "delivery_rate": float(row["delivery_rate"]) if "delivery_rate" in row and pd.notna(row.get("delivery_rate")) else None,
                }
            )
        return result

    return {
        "product_line": summarize("_product_line"),
        "ad_format": summarize("_ad_format"),
        "trading_mode": summarize("_trading_mode"),
        "platform_tag": summarize("_platform_tag"),
    }


def infer_media_measurement_mode(placement_parse: dict[str, Any], program_bundle: dict[str, Any]) -> dict[str, Any]:
    rows = placement_parse.get("rows") or []
    conversion_columns = _semantic_role_columns(program_bundle, "conversion")
    revenue_columns = _semantic_role_columns(program_bundle, "revenue")
    display_like_count = 0
    for row in rows:
        trading_mode = str(row.get("交易模式", ""))
        ad_format = str(row.get("广告形态", ""))
        if trading_mode in {"程序化PD池", "PDB", "PMP", "保量"} or ad_format in {"开屏", "全屏闪屏", "前贴片", "暂停页", "Banner", "品牌头条"}:
            display_like_count += 1
    display_ratio = display_like_count / max(len(rows), 1) if rows else 0.0
    is_cpm_delivery = display_ratio >= 0.4 and not conversion_columns and not revenue_columns
    if is_cpm_delivery:
        return {
            "mode": "cpm_delivery",
            "confidence": _format_confidence(min(1.0, display_ratio + 0.2)),
            "reason": "点位结构以品牌曝光/资源位采买形态为主，且当前缺少后链路转化或收入字段，因此决策应按 CPM/曝光型采买处理。",
        }
    return {
        "mode": "mixed_or_traffic",
        "confidence": "medium",
        "reason": "当前数据同时包含曝光与点击信号，且未形成明确 CPM 采买单一口径，因此仍保留效率与完成率并行判断。",
    }


def build_media_decision_context(frame: pd.DataFrame, program_bundle: dict[str, Any], filename: str) -> dict[str, Any]:
    scope = analyze_data_scope(frame, filename, program_bundle)
    metrics = compute_weighted_metrics(frame, program_bundle)
    columns = metrics["columns"]
    combo_frame = _combo_frame(frame, columns)

    weighted_ctr = metrics["overall"]["weighted_ctr"] or 0.0
    high_scale_threshold = float(combo_frame[columns["actual_reach"]].quantile(0.6)) if not combo_frame.empty and columns["actual_reach"] else 0.0
    if not combo_frame.empty and "ctr" in combo_frame and combo_frame["ctr"].notna().any():
        high_efficiency_threshold = max(weighted_ctr * 1.2, float(combo_frame["ctr"].quantile(0.75)))
        low_efficiency_threshold = min(weighted_ctr * 0.8, float(combo_frame["ctr"].quantile(0.25)))
    else:
        high_efficiency_threshold = weighted_ctr * 1.2
        low_efficiency_threshold = weighted_ctr * 0.8
    benchmarks = {
        "high_scale_threshold": high_scale_threshold,
        "high_efficiency_threshold": high_efficiency_threshold,
        "low_efficiency_threshold": low_efficiency_threshold,
    }
    stability_rows = _stability_rows(frame, columns, scope["time_grain"], benchmarks)
    stability_map = {row["combo"]: row for row in stability_rows}
    window_change = analyze_window_change(frame, program_bundle, scope)
    placement_parse = parse_placement_field(frame, program_bundle)
    measurement_mode = infer_media_measurement_mode(placement_parse, program_bundle)
    bias_review = build_bias_review(frame, program_bundle)
    parsed_dimension_reviews = build_parsed_dimension_reviews(frame, program_bundle, placement_parse)

    actions: list[dict[str, Any]] = []
    priority_actions: list[str] = []
    high_risk_warnings: list[str] = []
    if scope["filename_conflict"]:
        high_risk_warnings.append("数据范围警示：文件名时间范围与工作表真实日期范围不一致，趋势类结论自动降级。")
    if metrics["click_risk"] and measurement_mode["mode"] != "cpm_delivery":
        high_risk_warnings.append("点击口径高风险：点击兑现偏离健康区间，点击类结果仅作辅助参考，不作为放量结论的核心证据。")
    elif metrics["click_risk"] and measurement_mode["mode"] == "cpm_delivery":
        high_risk_warnings.append("当前采买模式识别为 CPM/曝光型，点击兑现偏差只作辅助提醒，不参与动作主判断。")
    if metrics["exposure_risk"]:
        high_risk_warnings.append("曝光兑现异常：预估与监测的曝光口径存在明显偏离，需要优先复核口径与执行节奏。")
    if window_change.get("latest_window_incomplete"):
        high_risk_warnings.append("最新窗口疑似不完整：最新窗口记录量显著低于此前窗口，异常结论仅作低置信观察。")
    if measurement_mode["mode"] == "cpm_delivery":
        high_risk_warnings.append("采买模式识别为 CPM/曝光型：动作判断优先看完成率和稳定性，CTR 仅作辅助观察。")

    if not combo_frame.empty:
        for _, row in combo_frame.iterrows():
            combo = str(row["combo"])
            reach_value = float(row[columns["actual_reach"]]) if columns["actual_reach"] else 0.0
            scale_high = reach_value >= high_scale_threshold
            scale_medium = reach_value >= (high_scale_threshold * 0.6 if high_scale_threshold else 0)
            efficiency = float(row["ctr"]) if "ctr" in row and pd.notna(row["ctr"]) else None
            delivery = float(row["exposure_delivery"]) if "exposure_delivery" in row and pd.notna(row["exposure_delivery"]) else None
            click_delivery = float(row["click_delivery"]) if "click_delivery" in row and pd.notna(row["click_delivery"]) else None
            stability = stability_map.get(combo, {})
            stable = bool(stability.get("stable"))
            high_efficiency = efficiency is not None and efficiency >= high_efficiency_threshold and not metrics["click_risk"]
            low_efficiency = efficiency is not None and efficiency <= low_efficiency_threshold
            healthy_delivery = delivery is not None and 0.9 <= delivery <= 1.15
            exposure_risk = delivery is not None and (delivery > 1.2 or delivery < 0.8)
            click_risk = click_delivery is not None and (click_delivery > 1.8 or click_delivery < 0.5)
            risk_notes: list[str] = []
            evidence_dimensions: list[str] = []
            if scale_high:
                evidence_dimensions.append("规模")
            elif not scale_medium:
                risk_notes.append("规模偏小")
            if measurement_mode["mode"] != "cpm_delivery":
                if high_efficiency:
                    evidence_dimensions.append("效率")
                elif low_efficiency:
                    risk_notes.append("效率偏弱")
            if healthy_delivery:
                evidence_dimensions.append("兑现")
            elif exposure_risk:
                risk_notes.append("兑现异常")
            if stable:
                evidence_dimensions.append("稳定性")
            else:
                risk_notes.append("稳定性不足")
            if scope["filename_conflict"] or window_change.get("latest_window_incomplete") or exposure_risk or (click_risk and measurement_mode["mode"] != "cpm_delivery") or (metrics["click_risk"] and measurement_mode["mode"] != "cpm_delivery"):
                risk_notes.append("数据风险")

            action = None
            if exposure_risk or (click_risk and measurement_mode["mode"] != "cpm_delivery") or scope["filename_conflict"] or window_change.get("latest_window_incomplete"):
                action = "优先排查"
            elif measurement_mode["mode"] == "cpm_delivery" and scale_high and healthy_delivery and stable and "数据风险" not in risk_notes:
                action = "优先放量验证"
            elif measurement_mode["mode"] == "cpm_delivery" and healthy_delivery and (not scale_high or not stable):
                action = "观察培养"
            elif measurement_mode["mode"] == "cpm_delivery" and scale_high and delivery is not None and delivery < 0.9 and stable:
                action = "降噪收缩"
            elif scale_high and high_efficiency and healthy_delivery and stable and "数据风险" not in risk_notes:
                action = "优先放量验证"
            elif high_efficiency and healthy_delivery and (not scale_high or not stable):
                action = "观察培养"
            elif scale_high and low_efficiency and stable and not exposure_risk:
                action = "降噪收缩"
            if not action:
                continue

            stability_label = stability.get("stability_label", "稳定性待判断")
            actions.append(
                {
                    "对象": combo,
                    "动作": action,
                    "证据维度": evidence_dimensions,
                    "风险维度": risk_notes,
                    "证据链": " / ".join(evidence_dimensions + risk_notes) or "待补证据",
                    "触达占比": float(row["reach_share"]) if pd.notna(row.get("reach_share")) else None,
                    "互动效率": efficiency,
                    "曝光兑现": delivery,
                    "点击兑现": click_delivery,
                    "稳定性标签": stability_label,
                }
            )
        priority_map = {"优先排查": 0, "优先放量验证": 1, "观察培养": 2, "降噪收缩": 3}
        actions.sort(key=lambda item: (priority_map.get(item["动作"], 9), -(item["触达占比"] or 0)))
        for item in actions[:3]:
            priority_actions.append(f"{item['动作']}：`{item['对象']}`，证据来自 {item['证据链']}。")

    overall_judgment = "当前投放整体可用于执行复盘，但放量判断必须同时依赖规模、效率、兑现和稳定性。"
    if high_risk_warnings:
        overall_judgment = "当前投放可以做复盘，但存在高风险口径或时间边界问题，强结论和放量动作需要降级处理。"
    elif actions and actions[0]["动作"] == "优先放量验证":
        overall_judgment = "当前投放已出现可验证放量对象，但仍应先在稳定窗口内做放量验证，再进入资源迁移。"

    return {
        "scope": scope,
        "metrics": metrics,
        "role_summary": (program_bundle.get("semantic_mapping") or {}).get("role_summary", {}),
        "placement_parse": placement_parse,
        "parsed_dimension_reviews": parsed_dimension_reviews,
        "combo_rows": [
            {
                "对象": str(row["combo"]),
                "触达占比": float(row["reach_share"]) if pd.notna(row.get("reach_share")) else None,
                "互动效率": float(row["ctr"]) if "ctr" in row and pd.notna(row.get("ctr")) else None,
                "曝光完成率": float(row["exposure_delivery"]) if "exposure_delivery" in row and pd.notna(row.get("exposure_delivery")) else None,
                "点击兑现": float(row["click_delivery"]) if "click_delivery" in row and pd.notna(row.get("click_delivery")) else None,
            }
            for _, row in combo_frame.head(30).iterrows()
        ] if not combo_frame.empty else [],
        "measurement_mode": measurement_mode,
        "bias_review": bias_review,
        "window_change": window_change,
        "stability_rows": stability_rows,
        "actions": actions,
        "priority_actions": priority_actions,
        "high_risk_warnings": high_risk_warnings,
        "overall_judgment": overall_judgment,
        "metric_columns": columns,
    }
