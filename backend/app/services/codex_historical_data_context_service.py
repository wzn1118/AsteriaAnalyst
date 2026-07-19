from __future__ import annotations

import json
import math
import re
import warnings
from pathlib import Path
from typing import Any

from app.services.business_analysis_package_service import build_business_analysis_package


def _pd() -> Any:
    import pandas as pd

    return pd


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


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
    date_tokens = (
        "date",
        "time",
        "day",
        "month",
        "year",
        "\u65e5\u671f",
        "\u65f6\u95f4",
        "\u65e5",
        "\u6708",
        "\u5e74",
    )
    try:
        if not pd.api.types.is_datetime64_any_dtype(series) and not any(token in lower for token in date_tokens):
            return None
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            return pd.to_datetime(series, errors="coerce")
    except Exception:
        return None


def write_historical_data_snapshot(workspace: Path, frame: Any | None) -> str:
    """Persist a bounded current-data snapshot for historical-style data-context stages."""
    pd = _pd()
    snapshot_path = workspace / "historical_data_snapshot.csv"
    data = _coerce_frame(frame)
    if data.empty:
        pd.DataFrame().to_csv(snapshot_path, index=False, encoding="utf-8-sig")
        return str(snapshot_path.resolve())
    data = data.copy()
    if len(data) > 5000:
        data = data.head(5000)
    data.to_csv(snapshot_path, index=False, encoding="utf-8-sig")
    return str(snapshot_path.resolve())


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
                "name": name,
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
                "name": name,
                "non_null": non_null,
                "unique_count": unique_count,
                "missing_count": int(series.isna().sum()),
                "dimension_type": "date" if date_ratio >= 0.7 else ("numeric_bucket" if is_numeric else "categorical"),
                "priority": priority,
                "top_values": [
                    {"label": str(index), "count": int(value)}
                    for index, value in series.fillna("缺失").astype(str).value_counts().head(8).items()
                ],
            }
        )
    output.sort(key=lambda item: (int(item.get("priority") or 0), int(item.get("non_null") or 0)), reverse=True)
    return output


def _date_columns(frame: Any) -> list[dict[str, Any]]:
    pd = _pd()
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
                "name": name,
                "non_null": non_null,
                "min": str(parsed.min().date()) if non_null else "",
                "max": str(parsed.max().date()) if non_null else "",
                "month_count": int(parsed.dt.to_period("M").nunique()) if non_null else 0,
            }
        )
    return output[:4]


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
    if series.min() >= 0 and series.max() <= 1:
        return "rate"
    return "numeric"


def _infer_aggregation(name: str, series: Any) -> str:
    metric_type = _infer_metric_type(name, series)
    if metric_type in {"amount", "count"}:
        return "sum"
    return "mean"


def _metric_value(series: Any, aggregation: str) -> float:
    cleaned = series.dropna()
    if cleaned.empty:
        return 0.0
    if aggregation == "sum":
        return _safe_float(cleaned.sum())
    if aggregation == "median":
        return _safe_float(cleaned.median())
    return _safe_float(cleaned.mean())


def _dimension_metric_cube(frame: Any, metrics: list[dict[str, Any]], dimensions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pd = _pd()
    cube: list[dict[str, Any]] = []
    for dimension in dimensions[:10]:
        dim_name = str(dimension.get("name") or "")
        if dim_name not in frame.columns:
            continue
        work = frame.copy()
        work[dim_name] = work[dim_name].fillna("缺失").astype(str)
        for metric in metrics[:12]:
            metric_name = str(metric.get("name") or "")
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
                        "dimension_value": str(value),
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
                        "dimension": dim_name,
                        "metric": metric_name,
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
        top = rows[:3]
        bottom = list(reversed(rows[-3:])) if len(rows) > 3 else rows[-1:]
        output.append(
            {
                "dimension": item.get("dimension"),
                "metric": item.get("metric"),
                "aggregation": item.get("aggregation"),
                "top": top,
                "bottom": bottom,
            }
        )
    return output[:60]


def _pairwise_relationships(frame: Any, metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pd = _pd()
    names = [str(item.get("name")) for item in metrics[:16] if str(item.get("name") or "") in frame.columns]
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
                    "left": left,
                    "right": right,
                    "correlation": value,
                    "abs_correlation": abs(value),
                    "relationship_type": "positive" if value >= 0 else "negative",
                }
            )
    relationships.sort(key=lambda item: _safe_float(item.get("abs_correlation")), reverse=True)
    return relationships[:40]


def _action_candidates(top_bottom: list[dict[str, Any]], relationships: list[dict[str, Any]]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for item in top_bottom[:24]:
        dimension = str(item.get("dimension") or "")
        metric = str(item.get("metric") or "")
        top = list(item.get("top") or [])
        bottom = list(item.get("bottom") or [])
        if top:
            leader = top[0]
            actions.append(
                {
                    "action_type": "scale_leader",
                    "dimension": dimension,
                    "metric": metric,
                    "segment": leader.get("dimension_value"),
                    "evidence": leader,
                    "recommendation": f"优先复盘并复制 `{dimension}` 中 `{leader.get('dimension_value')}` 在 `{metric}` 上的领先做法。",
                }
            )
        if bottom:
            laggard = bottom[0]
            actions.append(
                {
                    "action_type": "repair_laggard",
                    "dimension": dimension,
                    "metric": metric,
                    "segment": laggard.get("dimension_value"),
                    "evidence": laggard,
                    "recommendation": f"将 `{dimension}` 中 `{laggard.get('dimension_value')}` 纳入修复清单，先定位 `{metric}` 落后的可控原因。",
                }
            )
    for rel in relationships[:12]:
        actions.append(
            {
                "action_type": "relationship_probe",
                "dimension": "",
                "metric": f"{rel.get('left')} x {rel.get('right')}",
                "segment": "",
                "evidence": rel,
                "recommendation": f"围绕 `{rel.get('left')}` 与 `{rel.get('right')}` 的强相关关系设计联动动作或拆解共同驱动因素。",
            }
        )
    return actions[:48]


def _scatter_points_for_pair(frame: Any, x_metric: str, y_metric: str, label_column: str = "") -> list[dict[str, Any]]:
    pd = _pd()
    if frame.empty or x_metric not in frame.columns or y_metric not in frame.columns:
        return []
    work = frame[[column for column in [x_metric, y_metric, label_column] if column and column in frame.columns]].copy()
    work[x_metric] = pd.to_numeric(work[x_metric], errors="coerce")
    work[y_metric] = pd.to_numeric(work[y_metric], errors="coerce")
    work = work.dropna(subset=[x_metric, y_metric]).head(120)
    points: list[dict[str, Any]] = []
    for index, row in work.iterrows():
        label = str(row.get(label_column) or f"row_{index}") if label_column else f"row_{index}"
        points.append(
            {
                "label": label[:80],
                "x": _safe_float(row.get(x_metric)),
                "y": _safe_float(row.get(y_metric)),
            }
        )
    return points


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
            "title": f"{first.get('dimension')} x {first.get('metric')} 贡献结构",
            "x": [row.get("dimension_value") for row in rows],
            "y": [row.get("value") for row in rows],
            "insight_input": first,
        }
        for index, item in enumerate(cube[1:8], start=1):
            rows = list(item.get("rows") or [])[:12]
            bundle["extra_categories"].append(
                {
                    "id": f"category_{index:02d}_{_safe_id(item.get('dimension'))}_{_safe_id(item.get('metric'))}",
                    "title": f"{item.get('dimension')} x {item.get('metric')} 结构对比",
                    "x": [row.get("dimension_value") for row in rows],
                    "y": [row.get("value") for row in rows],
                    "insight_input": item,
                }
            )
    if metrics:
        first_metric = metrics[0]
        bundle["distribution"] = {
            "title": f"{first_metric.get('name')} 分布",
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
        for index, metric in enumerate(metrics[1:6], start=1):
            bundle["extra_distributions"].append(
                {
                    "id": f"distribution_{index:02d}_{_safe_id(metric.get('name'))}",
                    "title": f"{metric.get('name')} 分布",
                    "x": ["最小值", "下四分位", "中位数", "上四分位", "最大值"],
                    "y": [metric.get("min"), metric.get("q25"), metric.get("median"), metric.get("q75"), metric.get("max")],
                    "insight_input": metric,
                }
            )
    if len(metrics) >= 2 and relationships:
        labels = [str(item.get("name")) for item in metrics[:8]]
        index = {name: idx for idx, name in enumerate(labels)}
        matrix = [[1.0 if i == j else 0.0 for j in labels] for i in labels]
        for rel in relationships:
            left = str(rel.get("left"))
            right = str(rel.get("right"))
            if left in index and right in index:
                i = index[left]
                j = index[right]
                matrix[i][j] = matrix[j][i] = _safe_float(rel.get("correlation"))
        bundle["correlation"] = {
            "title": "核心指标相关关系",
            "labels": labels,
            "matrix": matrix,
            "insight_input": {"relationships": relationships[:20]},
        }
    if len(metrics) >= 2:
        label_column = str((dimensions[0] if dimensions else {}).get("name") or "")
        points = _scatter_points_for_pair(
            frame,
            str(metrics[0].get("name") or ""),
            str(metrics[1].get("name") or ""),
            label_column,
        )
        bundle["scatter"] = {
            "title": f"{metrics[0].get('name')} vs {metrics[1].get('name')}",
            "x_label": metrics[0].get("name"),
            "y_label": metrics[1].get("name"),
            "points": points,
            "insight_input": {"x_metric": metrics[0], "y_metric": metrics[1]},
        }
        for index, rel in enumerate(relationships[:5], start=1):
            left = str(rel.get("left") or "")
            right = str(rel.get("right") or "")
            if not left or not right or left == str(metrics[0].get("name")) and right == str(metrics[1].get("name")):
                continue
            rel_points = _scatter_points_for_pair(frame, left, right, label_column)
            if len(rel_points) < 6:
                continue
            bundle["extra_scatters"].append(
                {
                    "id": f"scatter_{index:02d}_{_safe_id(left)}_{_safe_id(right)}",
                    "title": f"{left} vs {right}",
                    "x_label": left,
                    "y_label": right,
                    "points": rel_points,
                    "insight_input": {"relationship": rel, "label_dimension": label_column},
                }
            )
    return bundle


def _build_support_tables(metrics: list[dict[str, Any]], dimensions: list[dict[str, Any]], cube: list[dict[str, Any]], top_bottom: list[dict[str, Any]], relationships: list[dict[str, Any]], actions: list[dict[str, Any]], column_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    ranking_tables: list[dict[str, Any]] = []
    seen_dimensions: set[str] = set()
    for item in cube:
        dimension = str(item.get("dimension") or "")
        if not dimension or dimension in seen_dimensions:
            continue
        seen_dimensions.add(dimension)
        ranking_tables.append({"dimension": dimension, "metric": item.get("metric"), "rows": list(item.get("rows") or [])[:12]})
    return {
        "kpi_snapshot": [
            {
                "metric": metric.get("name"),
                "metric_type": metric.get("metric_type"),
                "aggregation": metric.get("aggregation"),
                "value": metric.get("sum") if metric.get("aggregation") == "sum" else metric.get("mean"),
                "non_null": metric.get("non_null"),
            }
            for metric in metrics[:16]
        ],
        "ranking_tables": ranking_tables[:12],
        "correlation_focus": relationships[:20],
        "glossary_rows": [
            {
                "column": item.get("name"),
                "dtype": item.get("dtype") or item.get("metric_type") or item.get("dimension_type"),
                "missing_ratio": item.get("missing_ratio"),
                "unique_count": item.get("unique_count"),
                "top_values": " / ".join(str(v.get("label")) for v in list(item.get("top_values") or [])[:4] if isinstance(v, dict)),
            }
            for item in (list(column_summaries or [])[:24] + dimensions[:12])
            if isinstance(item, dict)
        ],
        "dimension_matrix": [
            {
                "dimension": item.get("dimension"),
                "metric": item.get("metric"),
                "top_segment": (list(item.get("top") or [{}])[0]).get("dimension_value"),
                "top_value": (list(item.get("top") or [{}])[0]).get("value"),
                "bottom_segment": (list(item.get("bottom") or [{}])[0]).get("dimension_value"),
                "bottom_value": (list(item.get("bottom") or [{}])[0]).get("value"),
            }
            for item in top_bottom[:24]
        ],
        "priority_action_table": actions[:24],
        "appendix_detail_rows": [
            {
                "dimension": item.get("dimension"),
                "metric": item.get("metric"),
                "segment": row.get("dimension_value"),
                "rank": row.get("rank"),
                "n": row.get("n"),
                "value": row.get("value"),
                "lift_vs_overall": row.get("lift_vs_overall"),
            }
            for item in cube[:12]
            for row in list(item.get("rows") or [])[:6]
        ],
        "top_bottom_segments": top_bottom[:40],
        "action_candidates": actions[:40],
    }


def build_historical_data_context_pack(
    *,
    workspace: Path,
    data_snapshot_path: Path,
    current_report_context_path: Path | None = None,
    column_summaries: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Create deterministic data evidence artifacts for historical-style CLI pipelines."""
    return build_business_analysis_package(
        workspace=workspace,
        data_snapshot_path=data_snapshot_path,
        current_report_context_path=current_report_context_path,
        column_summaries=column_summaries,
    )
