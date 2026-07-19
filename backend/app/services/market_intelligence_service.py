from __future__ import annotations

import re
from typing import Any

import numpy as np
import pandas as pd


MARKET_ECOSYSTEM = [
    {
        "track": "Tableau-like",
        "tool": "Apache Superset",
        "repo": "https://github.com/apache/superset",
        "github_stars": "72.4k",
        "verified_on": "2026-04-14",
        "role": "interactive BI dashboards, semantic metrics, embedded analytics",
    },
    {
        "track": "Tableau-like",
        "tool": "Metabase",
        "repo": "https://github.com/metabase/metabase",
        "github_stars": "46.8k",
        "verified_on": "2026-04-14",
        "role": "self-serve dashboards, query builder, business-facing exploration",
    },
    {
        "track": "Stata-like",
        "tool": "statsmodels",
        "repo": "https://github.com/statsmodels/statsmodels",
        "github_stars": "11.4k",
        "verified_on": "2026-04-14",
        "role": "econometrics, inference, regression diagnostics, GLM",
    },
    {
        "track": "Stata-like",
        "tool": "linearmodels",
        "repo": "https://github.com/bashtage/linearmodels",
        "github_stars": "1.0k",
        "verified_on": "2026-04-14",
        "role": "panel data, instrumental variables, asset pricing style models",
    },
    {
        "track": "R-like",
        "tool": "Shiny",
        "repo": "https://github.com/rstudio/shiny",
        "github_stars": "5.6k",
        "verified_on": "2026-04-14",
        "role": "interactive analytical apps and narrative exploration",
    },
    {
        "track": "R-like",
        "tool": "ggplot2",
        "repo": "https://github.com/tidyverse/ggplot2",
        "github_stars": "6.9k",
        "verified_on": "2026-04-14",
        "role": "grammar-of-graphics style visualization and chart composition",
    },
    {
        "track": "R-like",
        "tool": "plotly.py",
        "repo": "https://github.com/plotly/plotly.py",
        "github_stars": "18.4k",
        "verified_on": "2026-04-14",
        "role": "interactive charts and dashboard-ready visual outputs",
    },
    {
        "track": "Market data",
        "tool": "yfinance",
        "repo": "https://github.com/ranaroussi/yfinance",
        "github_stars": "22.9k",
        "verified_on": "2026-04-14",
        "role": "market data ingestion for listed assets and benchmark context",
    },
    {
        "track": "Market forecast",
        "tool": "Prophet",
        "repo": "https://github.com/facebook/prophet",
        "github_stars": "20.1k",
        "verified_on": "2026-04-14",
        "role": "trend and seasonality forecasting for business or market signals",
    },
]

MARKET_DIMENSION_KEYWORDS = [
    "brand",
    "company",
    "vendor",
    "merchant",
    "seller",
    "competitor",
    "industry",
    "sector",
    "category",
    "channel",
    "region",
    "country",
    "province",
    "city",
    "market",
    "segment",
    "product",
    "screen_name",
    "account",
    "creator",
    "author",
    "campaign",
    "source",
    "品牌",
    "渠道",
    "地区",
    "区域",
    "品类",
]

MARKET_METRIC_KEYWORDS = [
    "sales",
    "revenue",
    "gmv",
    "amount",
    "orders",
    "volume",
    "users",
    "customers",
    "views",
    "impressions",
    "likes",
    "replies",
    "retweets",
    "bookmarks",
    "spend",
    "cost",
    "profit",
    "margin",
    "price",
    "qty",
    "quantity",
    "count",
    "新增",
    "流失",
    "净流入",
    "销量",
    "收入",
    "销售",
]

MARKET_REQUEST_KEYWORDS = [
    "market",
    "market analysis",
    "go-to-market",
    "competition",
    "competitor",
    "share",
    "segment",
    "industry",
    "品牌",
    "市场",
    "竞品",
    "竞争",
    "份额",
    "渠道",
    "行业",
    "用户增长",
    "商业分析",
]

NAME_DIMENSION_HINTS = [
    "name",
    "title",
    "product",
    "item",
    "goods",
    "sku",
    "spu",
    "brand",
    "category",
    "名称",
    "标题",
    "商品",
    "品类",
    "品牌",
]

FUNCTION_KEYWORDS = [
    "止痒",
    "驱蚊",
    "冰凉",
    "清凉",
    "杀虫",
    "防虫",
    "防蚊",
    "灭蚊",
    "保湿",
    "补水",
    "修护",
    "去屑",
    "清洁",
    "控油",
    "美白",
]

CATEGORY_KEYWORDS = [
    "花露水",
    "驱蚊液",
    "喷雾",
    "气雾剂",
    "木条",
    "蚊香液",
    "电蚊拍",
    "套装",
    "洗发水",
    "沐浴露",
    "牙膏",
    "面膜",
    "精华",
    "乳液",
]


def get_market_ecosystem_catalog() -> list[dict[str, str]]:
    return [dict(item) for item in MARKET_ECOSYSTEM]


def get_market_ecosystem_summary() -> dict[str, Any]:
    tracks = sorted({item["track"] for item in MARKET_ECOSYSTEM})
    return {
        "total_tools": len(MARKET_ECOSYSTEM),
        "tracks": tracks,
        "verified_on": "2026-04-14",
    }


def _requested_market_mode(request_text: str) -> bool:
    text = request_text.lower()
    return any(token in text for token in MARKET_REQUEST_KEYWORDS)


def _choose_market_dimension(
    frame: pd.DataFrame,
    categorical_cols: list[str],
    temporal_cols: list[str],
    numeric_cols: list[str],
) -> str | None:
    candidates: list[tuple[int, int, float, str]] = []
    row_count = max(len(frame), 1)
    upper_cardinality = min(120, max(10, int(row_count * 0.35)))

    for column in frame.columns.astype(str).tolist():
        if column in temporal_cols or column in numeric_cols:
            continue
        series = frame[column].dropna().astype(str)
        if series.empty:
            continue
        cardinality = int(series.nunique())
        if cardinality < 2 or cardinality > upper_cardinality:
            continue
        top_share = float(series.value_counts(normalize=True).iloc[0])
        lower = column.lower()
        score = 0
        if column in categorical_cols:
            score += 2
        if any(token in lower for token in MARKET_DIMENSION_KEYWORDS):
            score += 5
        if cardinality <= 20:
            score += 2
        if top_share < 0.95:
            score += 1
        if score > 0:
            candidates.append((score, -cardinality, top_share, column))

    if not candidates:
        return None
    candidates.sort(key=lambda item: (-item[0], item[1], item[2], item[3]))
    return candidates[0][3]


def _choose_market_metric(frame: pd.DataFrame, numeric_cols: list[str]) -> str | None:
    candidates: list[tuple[int, float, str]] = []
    for column in numeric_cols:
        series = pd.to_numeric(frame[column], errors="coerce").dropna()
        if series.empty:
            continue
        lower = column.lower()
        score = 0
        if any(token in lower for token in MARKET_METRIC_KEYWORDS):
            score += 5
        if (series >= 0).mean() >= 0.95:
            score += 1
        variability = float(series.std()) if len(series) > 1 else 0.0
        score += 1 if variability > 0 else 0
        score += 1 if series.nunique() >= min(20, len(series)) else 0
        candidates.append((score, variability, column))

    if not candidates:
        return None
    candidates.sort(key=lambda item: (-item[0], -item[1], item[2]))
    return candidates[0][2]


def _choose_market_time_column(temporal_cols: list[str]) -> str | None:
    if not temporal_cols:
        return None
    preferred = sorted(
        temporal_cols,
        key=lambda column: (
            0 if any(token in column.lower() for token in ["date", "time", "month", "week", "day"]) else 1,
            column,
        ),
    )
    return preferred[0]


def _best_name_column(frame: pd.DataFrame) -> str | None:
    candidates: list[tuple[int, float, str]] = []
    for column in frame.columns.astype(str).tolist():
        series = frame[column]
        if pd.api.types.is_numeric_dtype(series):
            continue
        clean = series.dropna().astype(str)
        if clean.empty:
            continue
        score = 0
        lower = column.lower()
        if any(token in lower for token in NAME_DIMENSION_HINTS):
            score += 6
        unique_ratio = float(clean.nunique()) / max(len(clean), 1)
        if unique_ratio >= 0.4:
            score += 2
        avg_length = float(clean.map(len).mean())
        if 3 <= avg_length <= 40:
            score += 1
        if score > 0:
            candidates.append((score, -avg_length, column))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (-item[0], item[1], item[2]))
    return candidates[0][2]


def _extract_brand_token(text: str) -> str | None:
    normalized = re.sub(r"[^\w\u4e00-\u9fff]+", " ", str(text)).strip()
    if not normalized:
        return None
    match = re.match(r"^([A-Za-z]+|[\u4e00-\u9fff]{2,4})", normalized)
    return match.group(1) if match else None


def _extract_category_token(text: str) -> str | None:
    raw = str(text)
    for keyword in CATEGORY_KEYWORDS:
        if keyword in raw:
            return keyword
    matches = re.findall(r"[\u4e00-\u9fff]{2,6}", raw)
    return matches[-1] if matches else None


def _extract_function_token(text: str) -> str | None:
    raw = str(text)
    hits = [keyword for keyword in FUNCTION_KEYWORDS if keyword in raw]
    return "/".join(hits[:2]) if hits else None


def _derived_dimension_candidates(frame: pd.DataFrame) -> dict[str, pd.Series]:
    name_column = _best_name_column(frame)
    if not name_column:
        return {}
    source = frame[name_column].fillna("").astype(str)
    derived: dict[str, pd.Series] = {
        "derived_brand": source.map(_extract_brand_token),
        "derived_function": source.map(_extract_function_token),
        "derived_category": source.map(_extract_category_token),
    }
    result: dict[str, pd.Series] = {}
    for key, series in derived.items():
        usable = series.fillna("Unknown")
        unique = int(usable.nunique())
        if 2 <= unique <= 20:
            result[key] = usable
    return result


def _segment_share_rows(frame: pd.DataFrame, dimension_column: str, metric_column: str) -> dict[str, Any]:
    working = frame[[dimension_column, metric_column]].copy()
    working[dimension_column] = working[dimension_column].fillna("Missing").astype(str)
    working[metric_column] = pd.to_numeric(working[metric_column], errors="coerce")
    working = working.dropna()
    if working.empty:
        return {"rows": [], "hhi": None, "top3_share": None, "pareto_count": None}

    grouped = working.groupby(dimension_column, dropna=False)[metric_column].sum().sort_values(ascending=False)
    total = float(grouped.sum())
    if total <= 0:
        return {"rows": [], "hhi": None, "top3_share": None, "pareto_count": None}

    shares = grouped / total
    cumulative = shares.cumsum()
    rows = [
        {
            "segment": str(index),
            "metric": round(float(value), 4),
            "share": round(float(shares.loc[index]), 4),
            "cumulative_share": round(float(cumulative.loc[index]), 4),
        }
        for index, value in grouped.head(10).items()
    ]
    hhi = float((shares.pow(2).sum()) * 10000)
    pareto_count = int((cumulative <= 0.8).sum() + 1)
    return {
        "rows": rows,
        "hhi": round(hhi, 1),
        "top3_share": round(float(shares.head(3).sum()), 4),
        "pareto_count": pareto_count,
    }


def _trend_rows(frame: pd.DataFrame, time_column: str, metric_column: str) -> list[dict[str, Any]]:
    working = frame[[time_column, metric_column]].copy()
    working[time_column] = pd.to_datetime(working[time_column], errors="coerce")
    working[metric_column] = pd.to_numeric(working[metric_column], errors="coerce")
    working = working.dropna()
    if working.empty:
        return []
    grouped = (
        working.assign(period=working[time_column].dt.to_period("M").astype(str))
        .groupby("period")[metric_column]
        .sum()
        .reset_index()
        .tail(12)
    )
    return [{"period": str(row["period"]), "metric": round(float(row[metric_column]), 4)} for _, row in grouped.iterrows()]


def _opportunity_rows(
    frame: pd.DataFrame,
    dimension_column: str,
    metric_column: str,
    time_column: str,
) -> list[dict[str, Any]]:
    working = frame[[dimension_column, metric_column, time_column]].copy()
    working[dimension_column] = working[dimension_column].fillna("Missing").astype(str)
    working[metric_column] = pd.to_numeric(working[metric_column], errors="coerce")
    working[time_column] = pd.to_datetime(working[time_column], errors="coerce")
    working = working.dropna()
    if working.empty:
        return []

    grouped = (
        working.assign(period=working[time_column].dt.to_period("M").astype(str))
        .groupby([dimension_column, "period"])[metric_column]
        .sum()
        .reset_index()
    )
    periods = sorted(grouped["period"].unique().tolist())
    if len(periods) < 2:
        return []

    current_period = periods[-1]
    previous_period = periods[-2]
    pivot = grouped.pivot_table(
        index=dimension_column,
        columns="period",
        values=metric_column,
        aggfunc="sum",
        fill_value=0,
    )
    current = pivot[current_period] if current_period in pivot else pd.Series(dtype="float64")
    previous = pivot[previous_period] if previous_period in pivot else pd.Series(dtype="float64")
    current_total = float(current.sum())
    if current_total <= 0:
        return []

    rows: list[dict[str, Any]] = []
    for segment, current_value in current.sort_values(ascending=False).head(12).items():
        previous_value = float(previous.get(segment, 0.0))
        growth_rate = round((float(current_value) - previous_value) / previous_value, 4) if previous_value > 0 else None
        rows.append(
            {
                "segment": str(segment),
                "current_period": current_period,
                "previous_period": previous_period,
                "current_metric": round(float(current_value), 4),
                "previous_metric": round(previous_value, 4),
                "share": round(float(current_value) / current_total, 4),
                "growth_rate": growth_rate,
            }
        )

    rows.sort(
        key=lambda row: (
            -row["share"],
            -(row["growth_rate"] if row["growth_rate"] is not None else -9.0),
            row["segment"],
        )
    )
    return rows[:8]


def build_market_intelligence(
    *,
    frame: pd.DataFrame,
    numeric_cols: list[str],
    categorical_cols: list[str],
    temporal_cols: list[str],
    request_text: str,
) -> dict[str, Any]:
    market_requested = _requested_market_mode(request_text)
    dimension_column = _choose_market_dimension(frame, categorical_cols, temporal_cols, numeric_cols)
    metric_column = _choose_market_metric(frame, numeric_cols)
    time_column = _choose_market_time_column(temporal_cols)
    derived_dimensions = _derived_dimension_candidates(frame)
    dimension_source = "explicit" if dimension_column else ""

    segment_summary = (
        _segment_share_rows(frame, dimension_column, metric_column)
        if dimension_column and metric_column
        else {"rows": [], "hhi": None, "top3_share": None, "pareto_count": None}
    )
    trend_rows = _trend_rows(frame, time_column, metric_column) if time_column and metric_column else []
    opportunity_rows = (
        _opportunity_rows(frame, dimension_column, metric_column, time_column)
        if dimension_column and metric_column and time_column
        else []
    )

    if not segment_summary["rows"] and metric_column and derived_dimensions:
        best_dimension = None
        best_summary = {"rows": [], "hhi": None, "top3_share": None, "pareto_count": None}
        best_opportunity_rows: list[dict[str, Any]] = []
        for derived_name, derived_series in derived_dimensions.items():
            working = frame.copy()
            working[derived_name] = derived_series
            summary = _segment_share_rows(working, derived_name, metric_column)
            if not summary["rows"]:
                continue
            if len(summary["rows"]) > len(best_summary["rows"]):
                best_dimension = derived_name
                best_summary = summary
                best_opportunity_rows = (
                    _opportunity_rows(working, derived_name, metric_column, time_column)
                    if time_column
                    else []
                )
        if best_dimension:
            dimension_column = best_dimension
            dimension_source = "derived"
            segment_summary = best_summary
            opportunity_rows = best_opportunity_rows

    ready = bool(dimension_column and metric_column and segment_summary["rows"])
    confidence = "low"
    if ready:
        if dimension_source == "explicit" and time_column and len(segment_summary["rows"]) >= 3:
            confidence = "high"
        elif len(segment_summary["rows"]) >= 3:
            confidence = "medium"
    readable_dimension = {
        "derived_brand": "品牌",
        "derived_function": "功效/需求",
        "derived_category": "品类",
    }.get(dimension_column, dimension_column)

    summary_bullets: list[str] = []
    if ready:
        summary_bullets.append(
            f"系统将 `{readable_dimension}` 识别为最像市场切片的维度，将 `{metric_column}` 识别为最像市场结果指标的数值列。"
        )
        if segment_summary["top3_share"] is not None:
            summary_bullets.append(
                f"头部三个细分合计占比约 {segment_summary['top3_share']:.1%}，可先判断头部集中还是长尾竞争。"
            )
        if segment_summary["hhi"] is not None:
            concentration = "高集中" if segment_summary["hhi"] >= 2500 else "中等集中" if segment_summary["hhi"] >= 1500 else "分散竞争"
            summary_bullets.append(
                f"HHI 约为 {segment_summary['hhi']:.1f}，对应的市场结构更接近 `{concentration}`。"
            )
        if opportunity_rows:
            leaders = ", ".join(row["segment"] for row in opportunity_rows[:3])
            summary_bullets.append(
                f"最近两个时间窗口下，优先值得继续看的细分包括 {leaders}。"
            )
    elif market_requested:
        summary_bullets.append("用户明显在寻找市场分析视角，但当前数据缺少足够稳定的市场维度或结果指标列。")
        summary_bullets.append("如果补充品牌/渠道/地区/品类等字段，或补充销售/曝光/订单等指标，市场分析章节会更完整。")

    return {
        "market_requested": market_requested,
        "ready": ready,
        "confidence": confidence,
        "dimension_source": dimension_source,
        "dimension_column": dimension_column,
        "metric_column": metric_column,
        "time_column": time_column,
        "segment_rows": segment_summary["rows"],
        "trend_rows": trend_rows,
        "opportunity_rows": opportunity_rows,
        "summary_bullets": summary_bullets,
        "hhi": segment_summary["hhi"],
        "top3_share": segment_summary["top3_share"],
        "pareto_count": segment_summary["pareto_count"],
        "derived_dimensions": {
            key: pd.Series(series).fillna("Unknown").value_counts().head(8).to_dict()
            for key, series in derived_dimensions.items()
        },
        "ecosystem_rows": get_market_ecosystem_catalog(),
    }
