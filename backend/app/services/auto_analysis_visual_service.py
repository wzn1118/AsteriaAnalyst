from __future__ import annotations

import hashlib
from typing import Any

import numpy as np
import pandas as pd


def _zh(value: str) -> str:
    return value.encode("ascii").decode("unicode_escape")


def _safe_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(number):
        return None
    return number


def _series(frame: pd.DataFrame, column: str) -> pd.Series:
    value = frame.loc[:, column]
    if isinstance(value, pd.DataFrame):
        return value.iloc[:, 0]
    return value


def _format_axis_number(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if not np.isfinite(number):
        return str(value)
    if abs(number) >= 1000:
        return f"{number:,.0f}"
    if abs(number) >= 1:
        return f"{number:,.2f}".rstrip("0").rstrip(".")
    formatted = f"{number:.4f}".rstrip("0").rstrip(".")
    return formatted or "0"


def _frame_for_columns(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    data: dict[str, pd.Series] = {}
    for column in columns:
        if column and column in frame.columns and column not in data:
            data[column] = _series(frame, column)
    return pd.DataFrame(data, index=frame.index)


def _representative_frame(frame: pd.DataFrame, limit: int) -> pd.DataFrame:
    limit = max(1, int(limit or 1))
    if len(frame) <= limit:
        return frame.copy()
    positions = np.linspace(0, len(frame) - 1, limit, dtype=int)
    return frame.iloc[pd.Index(positions).drop_duplicates()].copy()


def _numeric_columns(enriched: pd.DataFrame, selected: dict[str, Any], limit: int = 8) -> list[str]:
    preferred = [
        selected.get("target"),
        *(selected.get("features") or []),
        (selected.get("bubble") or {}).get("x"),
        (selected.get("bubble") or {}).get("y"),
        (selected.get("bubble") or {}).get("size"),
    ]
    columns: list[str] = []
    for column in [str(item or "") for item in preferred]:
        if column and column in enriched.columns and column not in columns:
            if pd.to_numeric(_series(enriched, column), errors="coerce").notna().mean() >= 0.5:
                columns.append(column)
    for column in enriched.columns.astype(str).tolist():
        if len(columns) >= limit:
            break
        if column in columns:
            continue
        if pd.to_numeric(_series(enriched, column), errors="coerce").notna().mean() >= 0.8:
            columns.append(column)
    return columns[:limit]


def _column_score(column: str, *, semantic: str = "") -> int:
    text = f"{column} {semantic}".lower()
    score = 0
    for token, weight in (
        ("支出", 120),
        ("收入", 115),
        ("年度", 100),
        ("year", 100),
        ("地区", 95),
        ("地域", 95),
        ("省", 75),
        ("市", 70),
        ("服务", 90),
        ("领域", 90),
        ("基金会", 85),
        ("组织", 80),
        ("类型", 80),
        ("画像", 78),
        ("异常", 76),
        ("风险", 74),
        ("项目", 65),
    ):
        if token in text:
            score += weight
    return score


def _categorical_columns(enriched: pd.DataFrame, selected: dict[str, Any], field_profiles: list[dict[str, Any]], limit: int = 8) -> list[str]:
    preferred = [
        selected.get("group"),
        selected.get("label"),
        (selected.get("bubble") or {}).get("color"),
        *(selected.get("features") or []),
    ]
    profile_roles = {
        str(profile.get("column") or ""): " ".join(
            [str(profile.get("role") or ""), *[str(item) for item in list(profile.get("semantic_tags") or [])]]
        )
        for profile in field_profiles
        if str(profile.get("column") or "")
    }
    candidates: list[tuple[int, str]] = []
    seen: set[str] = set()
    ordered = [str(item or "") for item in preferred] + enriched.columns.astype(str).tolist()
    for column in ordered:
        if not column or column in seen or column not in enriched.columns:
            continue
        seen.add(column)
        series = _series(enriched, column).dropna().astype(str).str.strip()
        series = series[series != ""]
        if series.empty:
            continue
        unique_count = int(series.nunique(dropna=True))
        if unique_count < 2 or unique_count > max(80, int(len(series) * 0.7)):
            continue
        numeric_ratio = pd.to_numeric(series, errors="coerce").notna().mean()
        if numeric_ratio >= 0.85:
            continue
        score = _column_score(column, semantic=profile_roles.get(column, ""))
        candidates.append((score, column))
    candidates.sort(key=lambda item: (-item[0], item[1]))
    return [column for _, column in candidates[:limit]]


def _chart_question(kind: str, x_label: str = "", y_label: str = "", group_label: str = "") -> str:
    x_text = x_label or "核心指标"
    y_text = y_label or "对比指标"
    group_text = group_label or "分组"
    if kind in {"bubble", "quadrant"}:
        return f"{x_text} 与 {y_text} 的高低组合如何定位预算效率、投入产出和优先复核对象？"
    if kind == "scatter" or kind.startswith("scatter-"):
        return f"{x_text} 与 {y_text} 是否存在异常偏离或高值聚集，需要按基金会/年度/领域拆分复核？"
    if kind == "histogram":
        return f"{x_text} 的分布是否长尾，是否需要为极端项目设定单独复核阈值？"
    if kind == "heatmap":
        return "哪些数值字段存在强联动，可能影响收入、支出、组织规模或效率判断？"
    if kind == "line":
        return f"{x_text} 随时间变化是否出现阶段性波动，是否需要结合年度项目周期复核？"
    if kind == "forecast":
        return f"{x_text} 的趋势外推是否提示预算、收入或项目规模的方向性风险？"
    if kind == "cluster-scatter":
        return f"对象画像在 {x_text} 与 {y_text} 上是否形成可运营的分层群体？"
    if kind == "anomaly-scatter":
        return f"哪些对象在 {x_text} 与 {y_text} 组合上显著偏离整体，应进入异常清单？"
    if kind == "bar" or kind.startswith("bar-"):
        return f"{group_text} 维度下，{x_text} 的集中度和资源倾斜是否需要管理动作？"
    return "这张图回答哪个业务问题，以及下一步如何复核？"


def _with_business_question(chart: dict[str, Any] | None, question: str | None = None) -> dict[str, Any] | None:
    if not chart:
        return None
    chart["business_question"] = question or _chart_question(
        str(chart.get("kind") or ""),
        str(chart.get("x_label") or ""),
        str(chart.get("y_label") or ""),
        str(chart.get("group_label") or ""),
    )
    return chart


def _time_column(enriched: pd.DataFrame, field_profiles: list[dict[str, Any]]) -> str:
    for profile in field_profiles:
        column = str(profile.get("column") or "")
        if column not in enriched.columns:
            continue
        if profile.get("role") == "time" or "time" in list(profile.get("semantic_tags") or []):
            parsed = pd.to_datetime(_series(enriched, column), errors="coerce")
            if parsed.notna().mean() >= 0.5 and int(parsed.dropna().nunique()) >= 4:
                return column
    return ""


def _scatter_chart_for_pair(
    enriched: pd.DataFrame,
    x_col: str,
    y_col: str,
    *,
    kind: str = "scatter",
    title: str | None = None,
    limit: int = 160,
) -> dict[str, Any] | None:
    if not x_col or not y_col or x_col == y_col or x_col not in enriched.columns or y_col not in enriched.columns:
        return None
    clean = _frame_for_columns(enriched, [x_col, y_col])
    clean[x_col] = pd.to_numeric(clean[x_col], errors="coerce")
    clean[y_col] = pd.to_numeric(clean[y_col], errors="coerce")
    clean = _representative_frame(clean.dropna(), limit)
    points = [
        [float(row[x_col]), float(row[y_col])]
        for _, row in clean.iterrows()
        if _safe_float(row[x_col]) is not None and _safe_float(row[y_col]) is not None
    ]
    if not points:
        return None
    return _with_business_question(
        {
            "kind": kind,
            "title": title or _zh(r"\u6563\u70b9\u56fe\uff1a\u591a\u89c6\u89d2\u6307\u6807\u5173\u7cfb"),
            "x_label": x_col,
            "y_label": y_col,
            "points": points,
            "explanation": _zh(r"\u7528\u4e8e\u4ece\u4e0d\u540c\u4e1a\u52a1\u95ee\u9898\u89c6\u89d2\u68c0\u67e5\u6307\u6807\u5173\u7cfb\u3001\u9ad8\u503c\u805a\u96c6\u548c\u5f02\u5e38\u504f\u79bb\u3002"),
        }
    )


def bubble_points(enriched: pd.DataFrame, selected: dict[str, Any], limit: int = 160) -> tuple[list[dict[str, Any]], dict[str, float]]:
    spec = selected.get("bubble") or {}
    x_col = str(spec.get("x") or "")
    y_col = str(spec.get("y") or "")
    size_col = str(spec.get("size") or "")
    color_col = str(spec.get("color") or "")
    label_col = str(spec.get("label") or "")
    columns = [column for column in [x_col, y_col, size_col, color_col, label_col] if column and column in enriched.columns]
    if not x_col or not y_col or not columns:
        return [], {"x_mid": 0.0, "y_mid": 0.0}
    clean = _frame_for_columns(enriched, columns)
    clean[x_col] = pd.to_numeric(clean[x_col], errors="coerce")
    clean[y_col] = pd.to_numeric(clean[y_col], errors="coerce")
    if size_col:
        clean[size_col] = pd.to_numeric(clean[size_col], errors="coerce")
    clean = _representative_frame(clean.dropna(subset=[x_col, y_col]), limit)
    x_mid = float(clean[x_col].median()) if not clean.empty else 0.0
    y_mid = float(clean[y_col].median()) if not clean.empty else 0.0
    points: list[dict[str, Any]] = []
    for index, row in clean.iterrows():
        x_value = _safe_float(row.get(x_col))
        y_value = _safe_float(row.get(y_col))
        size_value = abs(_safe_float(row.get(size_col)) or 1.0) if size_col else 1.0
        if x_value is None or y_value is None:
            continue
        quadrant = "high_high" if x_value >= x_mid and y_value >= y_mid else "high_low" if x_value >= x_mid else "low_high" if y_value >= y_mid else "low_low"
        points.append(
            {
                "name": str(row.get(label_col) if label_col else index),
                "x": x_value,
                "y": y_value,
                "size": size_value,
                "category": str(row.get(color_col) if color_col else ""),
                "quadrant": quadrant,
            }
        )
    return points, {"x_mid": x_mid, "y_mid": y_mid}


def _scatter_chart(enriched: pd.DataFrame, numeric: list[str], limit: int) -> dict[str, Any] | None:
    if len(numeric) < 2:
        return None
    x_col, y_col = numeric[0], numeric[1]
    clean = _frame_for_columns(enriched, [x_col, y_col])
    clean[x_col] = pd.to_numeric(clean[x_col], errors="coerce")
    clean[y_col] = pd.to_numeric(clean[y_col], errors="coerce")
    clean = _representative_frame(clean.dropna(), limit)
    points = [
        [float(row[x_col]), float(row[y_col])]
        for _, row in clean.iterrows()
        if _safe_float(row[x_col]) is not None and _safe_float(row[y_col]) is not None
    ]
    if not points:
        return None
    return _with_business_question({
        "kind": "scatter",
        "title": _zh(r"\u6563\u70b9\u56fe\uff1a\u6838\u5fc3\u6307\u6807\u5173\u7cfb"),
        "x_label": x_col,
        "y_label": y_col,
        "points": points,
        "explanation": _zh(r"\u7528\u4e8e\u89c2\u5bdf\u4e24\u4e2a\u6307\u6807\u4e4b\u95f4\u662f\u5426\u5b58\u5728\u7ebf\u6027\u5173\u7cfb\u3001\u79bb\u7fa4\u70b9\u6216\u5206\u5c42\u7ed3\u6784\u3002"),
    })


def _histogram_chart(enriched: pd.DataFrame, numeric: list[str]) -> dict[str, Any] | None:
    if not numeric:
        return None
    column = numeric[0]
    values = pd.to_numeric(_series(enriched, column), errors="coerce").dropna()
    if values.empty:
        return None
    unique_count = int(values.nunique(dropna=True))
    bins = max(3, min(12, unique_count, len(values)))
    counts, edges = np.histogram(values, bins=bins)
    labels = [
        f"{_format_axis_number(edges[index])} 至 {_format_axis_number(edges[index + 1])}"
        for index in range(len(edges) - 1)
    ]
    return _with_business_question({
        "kind": "histogram",
        "title": _zh(r"\u5206\u5e03\u56fe\uff1a\u6838\u5fc3\u6307\u6807\u96c6\u4e2d\u5ea6"),
        "x": labels,
        "y": [int(item) for item in counts.tolist()],
        "x_label": column,
        "explanation": _zh(r"\u7528\u4e8e\u5224\u65ad\u6307\u6807\u662f\u5426\u96c6\u4e2d\u3001\u957f\u5c3e\u6216\u5b58\u5728\u5f02\u5e38\u9ad8\u503c\u3002"),
    })


def _correlation_heatmap(enriched: pd.DataFrame, numeric: list[str]) -> dict[str, Any] | None:
    columns = numeric[:6]
    if len(columns) < 2:
        return None
    numeric_frame = _frame_for_columns(enriched, columns).apply(pd.to_numeric, errors="coerce")
    corr = numeric_frame.corr(numeric_only=True).fillna(0.0).round(4)
    if corr.empty:
        return None
    return _with_business_question({
        "kind": "heatmap",
        "title": _zh(r"\u76f8\u5173\u77e9\u9635\uff1a\u6570\u503c\u5b57\u6bb5\u8054\u52a8"),
        "labels": [str(item) for item in corr.columns.tolist()],
        "matrix": [[float(value) for value in row] for row in corr.to_numpy().tolist()],
        "explanation": _zh(r"\u7528\u4e8e\u5feb\u901f\u53d1\u73b0\u5f3a\u76f8\u5173\u5b57\u6bb5\u3001\u5197\u4f59\u6307\u6807\u548c\u53ef\u80fd\u7684\u9a71\u52a8\u5173\u7cfb\u3002"),
    })


def _time_series_chart(enriched: pd.DataFrame, field_profiles: list[dict[str, Any]], numeric: list[str]) -> dict[str, Any] | None:
    time_col = _time_column(enriched, field_profiles)
    target_col = numeric[0] if numeric else ""
    if not time_col or not target_col:
        return _sequence_line_chart(enriched, numeric)
    frame = _frame_for_columns(enriched, [time_col, target_col])
    frame[time_col] = pd.to_datetime(frame[time_col], errors="coerce", utc=True).dt.tz_localize(None)
    frame[target_col] = pd.to_numeric(frame[target_col], errors="coerce")
    frame = frame.dropna()
    if frame.empty or not pd.api.types.is_datetime64_any_dtype(frame[time_col]):
        return None
    grouped = frame.groupby(frame[time_col].dt.to_period("D"))[target_col].mean().sort_index()
    grouped = _representative_frame(grouped.to_frame("value"), 360).iloc[:, 0]
    if grouped.empty:
        return None
    return _with_business_question({
        "kind": "line",
        "title": _zh(r"\u65f6\u95f4\u5e8f\u5217\uff1a\u6838\u5fc3\u6307\u6807\u8d8b\u52bf"),
        "x": [str(index) for index in grouped.index.tolist()],
        "y": [float(value) for value in grouped.tolist()],
        "x_label": time_col,
        "y_label": target_col,
        "explanation": _zh(r"\u7528\u4e8e\u89c2\u5bdf\u6307\u6807\u968f\u65f6\u95f4\u7684\u8d8b\u52bf\u3001\u6ce2\u52a8\u548c\u9636\u6bb5\u6027\u53d8\u5316\u3002"),
    })


def _sequence_line_chart(enriched: pd.DataFrame, numeric: list[str]) -> dict[str, Any] | None:
    target_col = numeric[0] if numeric else ""
    if not target_col or target_col not in enriched.columns:
        return None
    values = _representative_frame(pd.to_numeric(_series(enriched, target_col), errors="coerce").dropna().to_frame("value"), 360).iloc[:, 0]
    if len(values) < 2:
        return None
    return _with_business_question({
        "kind": "line",
        "title": _zh(r"\u5e8f\u5217\u8d8b\u52bf\uff1a\u6838\u5fc3\u6307\u6807\u987a\u5e8f\u53d8\u5316"),
        "x": [str(index + 1) for index in range(len(values))],
        "y": [float(value) for value in values.tolist()],
        "x_label": "row_order",
        "y_label": target_col,
        "explanation": _zh(r"\u672a\u68c0\u6d4b\u5230\u7a33\u5b9a\u65f6\u95f4\u8f74\u65f6\uff0c\u4ee5\u884c\u987a\u5e8f\u5c55\u793a\u6307\u6807\u8d8b\u52bf\uff0c\u7528\u4e8e\u53d1\u73b0\u6ce2\u52a8\u548c\u9636\u6bb5\u6027\u7ebf\u7d22\u3002"),
    })


def _forecast_chart(enriched: pd.DataFrame, field_profiles: list[dict[str, Any]], numeric: list[str]) -> dict[str, Any] | None:
    target_col = numeric[0] if numeric else ""
    if not target_col:
        return None
    time_col = _time_column(enriched, field_profiles)
    if not time_col:
        return _sequence_forecast_chart(enriched, numeric)
    columns = [target_col, time_col]
    frame = _frame_for_columns(enriched, columns)
    frame[target_col] = pd.to_numeric(frame[target_col], errors="coerce")
    frame[time_col] = pd.to_datetime(frame[time_col], errors="coerce", utc=True).dt.tz_localize(None)
    frame = frame.dropna(subset=[target_col, time_col]).sort_values(time_col)
    if not pd.api.types.is_datetime64_any_dtype(frame[time_col]):
        return None
    series = frame.groupby(frame[time_col].dt.to_period("D"))[target_col].mean().sort_index()
    labels = [str(index) for index in series.index.tolist()]
    x_label = time_col
    if len(series) < 4 or int(series.nunique(dropna=True)) < 3:
        return None
    history = series.tail(80).astype(float).reset_index(drop=True)
    if float(history.std(skipna=True) or 0.0) <= 0:
        return None
    steps = min(6, max(3, len(history) // 4))
    x = np.arange(len(history), dtype=float)
    slope, intercept = np.polyfit(x, history.to_numpy(dtype=float), 1)
    future_x = np.arange(len(history), len(history) + steps, dtype=float)
    fitted = (slope * x + intercept).tolist()
    future = (slope * future_x + intercept).tolist()
    baseline = float(np.nanmedian(np.abs(history.to_numpy(dtype=float)))) or 1.0
    max_reasonable = baseline * 10_000.0
    if any(abs(float(value)) > max_reasonable for value in future if np.isfinite(value)):
        return None
    future_labels = [f"forecast_{index + 1}" for index in range(steps)]
    return _with_business_question({
        "kind": "forecast",
        "title": _zh(r"\u9884\u6d4b\u56fe\uff1a\u6838\u5fc3\u6307\u6807\u8d8b\u52bf\u5916\u63a8"),
        "x": [*labels[-len(history) :], *future_labels],
        "actual": [float(value) for value in history.tolist()] + [None] * steps,
        "forecast": [float(value) for value in fitted] + [float(value) for value in future],
        "x_label": x_label,
        "y_label": target_col,
        "explanation": _zh(r"\u7528\u7ebf\u6027\u8d8b\u52bf\u5916\u63a8\u751f\u6210\u8f7b\u91cf\u9884\u6d4b\uff0c\u7528\u4e8e\u5224\u65ad\u672a\u6765\u51e0\u4e2a\u5468\u671f\u7684\u65b9\u5411\u6027\u98ce\u9669\u3002"),
    })


def _sequence_forecast_chart(enriched: pd.DataFrame, numeric: list[str]) -> dict[str, Any] | None:
    target_col = numeric[0] if numeric else ""
    if not target_col or target_col not in enriched.columns:
        return None
    values = _representative_frame(pd.to_numeric(_series(enriched, target_col), errors="coerce").dropna().to_frame("value"), 360).iloc[:, 0].astype(float)
    if len(values) < 4 or int(values.nunique(dropna=True)) < 3:
        return None
    history = values.reset_index(drop=True)
    if float(history.std(skipna=True) or 0.0) <= 0:
        return None
    steps = min(6, max(3, len(history) // 2))
    x = np.arange(len(history), dtype=float)
    slope, intercept = np.polyfit(x, history.to_numpy(dtype=float), 1)
    future_x = np.arange(len(history), len(history) + steps, dtype=float)
    fitted = (slope * x + intercept).tolist()
    future = (slope * future_x + intercept).tolist()
    return _with_business_question({
        "kind": "forecast",
        "title": _zh(r"\u8f7b\u91cf\u9884\u6d4b\uff1a\u884c\u987a\u5e8f\u8d8b\u52bf\u5916\u63a8"),
        "x": [str(index + 1) for index in range(len(history))] + [f"forecast_{index + 1}" for index in range(steps)],
        "actual": [float(value) for value in history.tolist()] + [None] * steps,
        "forecast": [float(value) for value in fitted] + [float(value) for value in future],
        "x_label": "row_order",
        "y_label": target_col,
        "explanation": _zh(r"\u5728\u65e0\u660e\u786e\u65f6\u95f4\u8f74\u65f6\u4ec5\u505a\u8f7b\u91cf\u65b9\u5411\u5916\u63a8\uff0c\u7528\u4e8e\u63d0\u793a\u9700\u8981\u4eba\u5de5\u590d\u6838\u7684\u98ce\u9669\u8d8b\u52bf\u3002"),
    })


def _cluster_scatter_chart(enriched: pd.DataFrame, numeric: list[str], limit: int) -> dict[str, Any] | None:
    if len(numeric) < 2:
        return None
    x_col, y_col = numeric[0], numeric[1]
    clean = _frame_for_columns(enriched, [x_col, y_col])
    clean[x_col] = pd.to_numeric(clean[x_col], errors="coerce")
    clean[y_col] = pd.to_numeric(clean[y_col], errors="coerce")
    clean = _representative_frame(clean.dropna(), limit)
    if len(clean) < 4:
        return None
    raw = clean[[x_col, y_col]].to_numpy(dtype=float)
    mean = raw.mean(axis=0)
    std = raw.std(axis=0)
    std[std == 0] = 1.0
    values = (raw - mean) / std
    k = min(4, max(2, int(round(np.sqrt(len(values) / 2)))))
    seed_indices = np.linspace(0, len(values) - 1, k).round().astype(int)
    centers = values[seed_indices].copy()
    labels = np.zeros(len(values), dtype=int)
    for _ in range(12):
        distances = ((values[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
        labels = distances.argmin(axis=1)
        next_centers = centers.copy()
        for cluster_id in range(k):
            members = values[labels == cluster_id]
            if len(members):
                next_centers[cluster_id] = members.mean(axis=0)
        if np.allclose(next_centers, centers):
            break
        centers = next_centers
    summary = [
        {
            "cluster": int(cluster_id),
            "count": int((labels == cluster_id).sum()),
            "x_mean": float(raw[labels == cluster_id, 0].mean()) if (labels == cluster_id).any() else 0.0,
            "y_mean": float(raw[labels == cluster_id, 1].mean()) if (labels == cluster_id).any() else 0.0,
        }
        for cluster_id in range(k)
    ]
    return _with_business_question({
        "kind": "cluster-scatter",
        "title": _zh(r"\u5206\u7fa4\u56fe\uff1a\u5bf9\u8c61\u7ed3\u6784\u5206\u5c42"),
        "x_label": x_col,
        "y_label": y_col,
        "points": [[float(row[0]), float(row[1]), int(label)] for row, label in zip(raw, labels, strict=False)],
        "cluster_summary": summary,
        "explanation": _zh(r"\u7528\u8f7b\u91cf KMeans \u5c06\u5bf9\u8c61\u5206\u6210\u82e5\u5e72\u7ed3\u6784\u76f8\u8fd1\u7684\u7fa4\u7ec4\uff0c\u7528\u4e8e\u8bc6\u522b\u4e0d\u540c\u8fd0\u8425\u6253\u6cd5\u3002"),
    })


def _anomaly_scatter_chart(enriched: pd.DataFrame, numeric: list[str], limit: int) -> dict[str, Any] | None:
    columns = numeric[:6]
    if len(columns) < 2:
        return None
    frame = _representative_frame(_frame_for_columns(enriched, columns).apply(pd.to_numeric, errors="coerce").dropna(), limit)
    if len(frame) < 4:
        return None
    values = frame.to_numpy(dtype=float)
    mean = values.mean(axis=0)
    std = values.std(axis=0)
    std[std == 0] = 1.0
    zscores = (values - mean) / std
    scores = np.sqrt((zscores**2).mean(axis=1))
    threshold = max(2.0, float(np.quantile(scores, 0.9)))
    anomaly_count = int((scores >= threshold).sum())
    if anomaly_count == 0:
        threshold = float(np.quantile(scores, 0.8))
    x_col, y_col = columns[0], columns[1]
    points = []
    for index, (_, row) in enumerate(frame.iterrows()):
        score = float(scores[index])
        points.append(
            {
                "name": str(row.name),
                "x": float(row[x_col]),
                "y": float(row[y_col]),
                "score": score,
                "is_anomaly": bool(score >= threshold),
            }
        )
    return _with_business_question({
        "kind": "anomaly-scatter",
        "title": _zh(r"\u5f02\u5e38\u56fe\uff1a\u9ad8\u504f\u79bb\u5bf9\u8c61\u8bc6\u522b"),
        "x_label": x_col,
        "y_label": y_col,
        "points": points,
        "threshold": threshold,
        "explanation": _zh(r"\u7528\u591a\u6307\u6807\u6807\u51c6\u5206\u8bc6\u522b\u504f\u79bb\u6574\u4f53\u7ed3\u6784\u7684\u5bf9\u8c61\uff0c\u4f18\u5148\u8fdb\u5165\u98ce\u9669\u3001\u673a\u4f1a\u6216\u6570\u636e\u8d28\u91cf\u590d\u6838\u3002"),
    })


def _bar_chart_for_category(enriched: pd.DataFrame, group_col: str, value_col: str, *, limit: int = 12) -> dict[str, Any] | None:
    if not group_col or not value_col or group_col not in enriched.columns or value_col not in enriched.columns:
        return None
    frame = _frame_for_columns(enriched, [group_col, value_col])
    frame[group_col] = frame[group_col].astype(str).str.strip()
    frame[value_col] = pd.to_numeric(frame[value_col], errors="coerce")
    frame = frame.dropna(subset=[group_col, value_col])
    frame = frame[frame[group_col] != ""]
    if frame.empty:
        return None
    grouped = frame.groupby(group_col)[value_col].sum().sort_values(ascending=False).head(limit)
    if grouped.empty or int(grouped.shape[0]) < 2:
        return None
    title = _zh(r"\u5206\u7ec4\u6761\u5f62\u56fe\uff1a\u4e1a\u52a1\u7ef4\u5ea6\u8d44\u6e90\u96c6\u4e2d")
    kind = "bar-category"
    group_score = _column_score(group_col)
    if any(token in group_col for token in ("地区", "地域", "省", "市")):
        title = "地区视角：资源投向集中度"
        kind = "bar-region"
    elif "服务" in group_col or "领域" in group_col:
        title = "服务领域视角：项目组合集中度"
        kind = "bar-service"
    elif "年度" in group_col or "year" in group_col.lower():
        title = "年度视角：项目规模变化"
        kind = "bar-year"
    elif "基金会" in group_col or "组织" in group_col or "类型" in group_col:
        title = "组织画像视角：基金会类型差异"
        kind = "bar-organization"
    elif group_score:
        title = f"{group_col}视角：{value_col}集中度"
        kind = f"bar-category-{hashlib.sha1(group_col.encode('utf-8', errors='ignore')).hexdigest()[:8]}"
    return _with_business_question(
        {
            "kind": kind,
            "title": title,
            "x": [str(index) for index in grouped.index.tolist()],
            "y": [float(value) for value in grouped.tolist()],
            "x_label": group_col,
            "y_label": value_col,
            "group_label": group_col,
            "explanation": "按业务分组汇总核心指标，用于识别资源集中、结构倾斜和需要优先复核的客群或项目组合。",
        }
    )


def _pair_candidates(numeric: list[str]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for left_index, left in enumerate(numeric):
        for right in numeric[left_index + 1 :]:
            if left != right:
                pairs.append((left, right))
    pairs.sort(key=lambda pair: -(_column_score(pair[0]) + _column_score(pair[1])))
    return pairs


def build_auto_charts(
    enriched: pd.DataFrame,
    selected: dict[str, Any],
    points: list[dict[str, Any]],
    mid: dict[str, float],
    field_profiles: list[dict[str, Any]],
    limit: int = 160,
) -> list[dict[str, Any]]:
    bubble = selected.get("bubble") or {}
    quadrant = selected.get("quadrant") or {}
    charts: list[dict[str, Any]] = []
    if points:
        charts.extend([
            _with_business_question({
            "kind": "bubble",
            "title": _zh(r"\u5168\u91cf\u6c14\u6ce1\u56fe\uff1a\u81ea\u52a8\u5b57\u6bb5\u7ec4\u5408"),
            "x_label": str(bubble.get("x") or ""),
            "y_label": str(bubble.get("y") or ""),
            "size_label": str(bubble.get("size") or ""),
            "color_label": str(bubble.get("color") or ""),
            "points": points,
            "explanation": _zh(r"\u6bcf\u4e2a\u70b9\u4ee3\u8868\u4e00\u6761\u8bb0\u5f55\uff1b\u4f4d\u7f6e\u770b\u4e24\u9879\u6838\u5fc3\u6307\u6807\uff0c\u6c14\u6ce1\u5927\u5c0f\u770b\u5f3a\u5ea6\uff0c\u989c\u8272\u770b\u5206\u7ec4\u3002"),
            }),
            _with_business_question({
            "kind": "quadrant",
            "title": _zh(r"\u8c61\u9650\u56fe\uff1a\u9ad8\u4f4e\u7ec4\u5408\u4e0e\u884c\u52a8\u4f18\u5148\u7ea7"),
            "x_label": str(quadrant.get("x") or ""),
            "y_label": str(quadrant.get("y") or ""),
            "x_mid": mid["x_mid"],
            "y_mid": mid["y_mid"],
            "points": points,
            "quadrant_labels": {
                "high_high": _zh(r"\u4f18\u5148\u653e\u5927"),
                "high_low": _zh(r"\u6548\u7387\u6821\u6b63"),
                "low_high": _zh(r"\u6f5c\u529b\u57f9\u80b2"),
                "low_low": _zh(r"\u4f4e\u4f18\u5148\u7ea7/\u9700\u8bca\u65ad"),
            },
            "explanation": _zh(r"\u7528\u4e2d\u4f4d\u6570\u5207\u5206\u56db\u8c61\u9650\uff0c\u628a\u5bf9\u8c61\u5206\u6210\u653e\u5927\u3001\u4fee\u6b63\u3001\u57f9\u80b2\u548c\u8bca\u65ad\u56db\u7c7b\u3002"),
            }),
        ])
    numeric = _numeric_columns(enriched, selected, limit=12)
    categorical = _categorical_columns(enriched, selected, field_profiles, limit=8)
    pair_candidates = _pair_candidates(numeric)
    alternative_pair_charts: list[dict[str, Any] | None] = []
    used_pairs: set[tuple[str, str]] = set()
    for left, right in pair_candidates:
        pair_key = (left, right)
        if pair_key in used_pairs:
            continue
        used_pairs.add(pair_key)
        title = "多视角散点图：预算效率与组织画像"
        if any(token in f"{left}{right}" for token in ("收入", "支出")):
            title = "收支效率视角：高支出低收入识别"
        elif any(token in f"{left}{right}" for token in ("年度", "year")):
            title = "年度变化视角：项目指标波动"
        alt_kind = f"scatter-business-{len(alternative_pair_charts) + 1}"
        alternative_pair_charts.append(_scatter_chart_for_pair(enriched, left, right, kind=alt_kind, title=title, limit=limit))
        if len(alternative_pair_charts) >= 4:
            break
    grouped_charts: list[dict[str, Any] | None] = []
    value_candidates = numeric[:4] if numeric else []
    for category in categorical:
        value = value_candidates[0] if value_candidates else ""
        for candidate_value in value_candidates:
            if candidate_value != category:
                value = candidate_value
                break
        grouped_charts.append(_bar_chart_for_category(enriched, category, value))
        if len(grouped_charts) >= 5:
            break
    for candidate in [
        _scatter_chart(enriched, numeric, limit),
        _histogram_chart(enriched, numeric),
        _correlation_heatmap(enriched, numeric),
        _time_series_chart(enriched, field_profiles, numeric),
        _forecast_chart(enriched, field_profiles, numeric),
        _cluster_scatter_chart(enriched, numeric, limit),
        _anomaly_scatter_chart(enriched, numeric, limit),
        *alternative_pair_charts,
        *grouped_charts,
    ]:
        if candidate:
            charts.append(candidate)
    unique: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for chart in charts:
        key = (str(chart.get("kind") or ""), str(chart.get("x_label") or ""), str(chart.get("y_label") or ""))
        if key in seen:
            continue
        seen.add(key)
        unique.append(chart)
    return unique
