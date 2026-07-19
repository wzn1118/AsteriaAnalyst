from __future__ import annotations

from typing import Any

import numpy as np


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


def _table(title: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    columns: list[str] = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    return {"title": title, "columns": columns, "rows": rows}


def _forecast_rows(chart: dict[str, Any]) -> list[dict[str, Any]]:
    actual = [_safe_float(item) for item in list(chart.get("actual") or [])]
    forecast = [_safe_float(item) for item in list(chart.get("forecast") or [])]
    actual_values = [item for item in actual if item is not None]
    forecast_tail = [item for item in forecast[len(actual_values) :] if item is not None]
    if not actual_values or not forecast_tail:
        return []
    last_actual = actual_values[-1]
    final_forecast = forecast_tail[-1]
    delta = final_forecast - last_actual
    pct_delta = delta / abs(last_actual) if last_actual else None
    direction = _zh(r"\u4e0a\u884c") if delta > 0 else _zh(r"\u4e0b\u884c") if delta < 0 else _zh(r"\u5e73\u7a33")
    return [
        {
            "target": chart.get("y_label"),
            "horizon": len(forecast_tail),
            "last_actual": round(last_actual, 4),
            "final_forecast": round(final_forecast, 4),
            "delta": round(delta, 4),
            "pct_delta": round(pct_delta, 4) if pct_delta is not None else None,
            "direction": direction,
        }
    ]


def _cluster_rows(chart: dict[str, Any]) -> list[dict[str, Any]]:
    summary = list(chart.get("cluster_summary") or [])
    total = sum(int(item.get("count") or 0) for item in summary) or 1
    rows: list[dict[str, Any]] = []
    for item in summary:
        count = int(item.get("count") or 0)
        rows.append(
            {
                "cluster": int(item.get("cluster") or 0),
                "count": count,
                "share": round(count / total, 4),
                "x_mean": round(float(item.get("x_mean") or 0.0), 4),
                "y_mean": round(float(item.get("y_mean") or 0.0), 4),
            }
        )
    return rows


def _anomaly_rows(chart: dict[str, Any], limit: int = 10) -> list[dict[str, Any]]:
    threshold = _safe_float(chart.get("threshold"))
    points = sorted(list(chart.get("points") or []), key=lambda item: float(item.get("score") or 0.0), reverse=True)
    rows: list[dict[str, Any]] = []
    for point in points[:limit]:
        rows.append(
            {
                "name": point.get("name"),
                "x": round(float(point.get("x") or 0.0), 4),
                "y": round(float(point.get("y") or 0.0), 4),
                "score": round(float(point.get("score") or 0.0), 4),
                "threshold": round(threshold, 4) if threshold is not None else None,
                "is_anomaly": bool(point.get("is_anomaly")),
            }
        )
    return rows


def _numeric_values(values: Any) -> list[float]:
    numbers: list[float] = []
    for item in list(values or []):
        number = _safe_float(item)
        if number is not None:
            numbers.append(number)
    return numbers


def _top_correlation_pairs(chart: dict[str, Any], limit: int = 5) -> list[dict[str, Any]]:
    labels = [str(item) for item in list(chart.get("labels") or [])]
    matrix = list(chart.get("matrix") or [])
    pairs: list[dict[str, Any]] = []
    for left_index, left_label in enumerate(labels):
        for right_index, right_label in enumerate(labels):
            if right_index <= left_index:
                continue
            try:
                value = float(matrix[left_index][right_index])
            except (IndexError, TypeError, ValueError):
                continue
            if not np.isfinite(value):
                continue
            pairs.append(
                {
                    "driver": right_label,
                    "target": left_label,
                    "strength": round(value, 4),
                    "abs_strength": abs(value),
                    "direction": "positive" if value >= 0 else "negative",
                }
            )
    pairs.sort(key=lambda item: float(item["abs_strength"]), reverse=True)
    return pairs[:limit]


def _driver_hypothesis_rows(charts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for chart in charts:
        if chart.get("kind") == "heatmap":
            for index, pair in enumerate(_top_correlation_pairs(chart), start=1):
                rows.append(
                    {
                        "hypothesis_id": f"driver_corr_{index}",
                        "hypothesis": f"{pair['driver']} may move with {pair['target']}",
                        "evidence": "correlation_heatmap",
                        "driver": pair["driver"],
                        "target": pair["target"],
                        "strength": pair["strength"],
                        "direction": pair["direction"],
                        "confidence": "medium" if pair["abs_strength"] >= 0.6 else "low",
                        "caveat": "correlation_not_causation",
                    }
                )
        elif chart.get("kind") == "forecast":
            rows.extend(
                {
                    "hypothesis_id": "driver_forecast_trend",
                    "hypothesis": f"{chart.get('y_label')} has directional momentum",
                    "evidence": "forecast",
                    "driver": chart.get("x_label"),
                    "target": chart.get("y_label"),
                    "strength": None,
                    "direction": "trend",
                    "confidence": "low",
                    "caveat": "linear_extrapolation_only",
                }
                for _ in [0]
            )
        elif chart.get("kind") == "cluster-scatter":
            rows.append(
                {
                    "hypothesis_id": "driver_segment_structure",
                    "hypothesis": "segments may require differentiated actions",
                    "evidence": "cluster_profile",
                    "driver": chart.get("x_label"),
                    "target": chart.get("y_label"),
                    "strength": len(chart.get("cluster_summary") or []),
                    "direction": "segment_difference",
                    "confidence": "medium",
                    "caveat": "lightweight_kmeans",
                }
            )
    return rows[:10]


def _direction_label(delta: float) -> str:
    if delta > 0:
        return _zh(r"\u4e0a\u884c")
    if delta < 0:
        return _zh(r"\u4e0b\u884c")
    return _zh(r"\u5e73\u7a33")


def _time_series_diagnostic_rows(charts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for chart in charts:
        kind = str(chart.get("kind") or "")
        if kind == "line":
            values = _numeric_values(chart.get("y"))
            if len(values) < 2:
                continue
            diffs = np.diff(np.asarray(values, dtype=float))
            baseline = abs(values[0]) if values[0] else 1.0
            mean_abs = float(np.mean(np.abs(values))) or 1.0
            delta = values[-1] - values[0]
            rows.append(
                {
                    "source_ref": "chart:time_series",
                    "target": chart.get("y_label"),
                    "signal_type": "historical_trend",
                    "observation_count": len(values),
                    "horizon": 0,
                    "start_value": round(values[0], 4),
                    "end_value": round(values[-1], 4),
                    "net_change": round(delta, 4),
                    "pct_change": round(delta / baseline, 4),
                    "volatility_index": round(float(np.std(diffs)) / mean_abs, 4) if len(diffs) else 0.0,
                    "trend_direction": _direction_label(delta),
                    "recommended_method": "trend_change_point_seasonality_scan",
                    "next_step": "check seasonality, change points, and lagged drivers before setting action cadence",
                }
            )
        elif kind == "forecast":
            actual = _numeric_values(chart.get("actual"))
            forecast = [_safe_float(item) for item in list(chart.get("forecast") or [])]
            forecast_tail = [item for item in forecast[len(actual) :] if item is not None]
            if not actual or not forecast_tail:
                continue
            last_actual = actual[-1]
            final_forecast = forecast_tail[-1]
            baseline = abs(last_actual) if last_actual else 1.0
            delta = final_forecast - last_actual
            rows.append(
                {
                    "source_ref": "chart:forecast",
                    "target": chart.get("y_label"),
                    "signal_type": "forecast_projection",
                    "observation_count": len(actual),
                    "horizon": len(forecast_tail),
                    "start_value": round(last_actual, 4),
                    "end_value": round(final_forecast, 4),
                    "net_change": round(delta, 4),
                    "pct_change": round(delta / baseline, 4),
                    "volatility_index": None,
                    "trend_direction": _direction_label(delta),
                    "recommended_method": "forecast_backtest_and_scenario_band",
                    "next_step": "backtest the projection and compare scenarios before committing resources",
                }
            )
    return rows[:6]


def _causal_candidate_rows(charts: list[dict[str, Any]], evidence_tables: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    driver_table = next((table for table in evidence_tables if table.get("title") == _zh(r"\u9a71\u52a8\u5047\u8bbe")), None)
    has_time_signal = any(table.get("title") == _zh(r"\u65f6\u95f4\u5e8f\u5217\u8bca\u65ad") and table.get("rows") for table in evidence_tables)
    has_segment_signal = any(chart.get("kind") == "cluster-scatter" for chart in charts)
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(list((driver_table or {}).get("rows") or [])[:limit], start=1):
        strength = _safe_float(item.get("strength"))
        readiness = 35.0
        if strength is not None:
            readiness += min(35.0, abs(strength) * 35.0)
        if has_time_signal:
            readiness += 15.0
        if has_segment_signal:
            readiness += 10.0
        design = "lagged_regression_with_controls" if has_time_signal else "controlled_comparison_or_matching"
        if item.get("evidence") == "cluster_profile":
            design = "segment_controlled_comparison"
        rows.append(
            {
                "candidate_id": f"causal_candidate_{index}",
                "driver": item.get("driver"),
                "outcome": item.get("target"),
                "hypothesis_source": item.get("evidence"),
                "signal_strength": item.get("strength"),
                "readiness_score": round(min(100.0, readiness), 2),
                "recommended_design": design,
                "control_hint": "control for segment, time, and high-correlation covariates",
                "minimum_data_needed": "outcome, driver, time/order, segment, and confounder fields",
                "caveat": "hypothesis_only_not_causal_claim",
                "next_step": "promote this candidate to a causal method executor when controls and temporal ordering are available",
            }
        )
    if not rows and has_time_signal:
        rows.append(
            {
                "candidate_id": "causal_candidate_time_trend",
                "driver": "time_or_period",
                "outcome": "selected_target",
                "hypothesis_source": "time_series_diagnostic",
                "signal_strength": None,
                "readiness_score": 50.0,
                "recommended_design": "interrupted_time_series_or_change_point_review",
                "control_hint": "compare pre/post windows and seasonality controls",
                "minimum_data_needed": "time, outcome, intervention/event marker",
                "caveat": "requires event timing before causal interpretation",
                "next_step": "ask the runtime for intervention dates or known business events",
            }
        )
    rows.sort(key=lambda item: float(item.get("readiness_score") or 0.0), reverse=True)
    return rows[:limit]


def _priority_label(score: float) -> str:
    if score >= 75:
        return _zh(r"\u9ad8")
    if score >= 45:
        return _zh(r"\u4e2d")
    return _zh(r"\u4f4e")


def _action_priority_rows(evidence_tables: list[dict[str, Any]], charts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    forecast = next((table for table in evidence_tables if table.get("title") == _zh(r"\u9884\u6d4b\u98ce\u9669\u6458\u8981")), None)
    if forecast and forecast.get("rows"):
        item = forecast["rows"][0]
        pct_delta = abs(float(item.get("pct_delta") or 0.0))
        score = min(100.0, 35.0 + pct_delta * 250.0)
        rows.append(
            {
                "action": "review_forecast_risk",
                "evidence": "forecast_risk_summary",
                "source_ref": "table:forecast_risk_summary",
                "priority_score": round(score, 2),
                "priority": _priority_label(score),
                "why": f"direction={item.get('direction')}, pct_delta={item.get('pct_delta')}",
                "score_reason": "35 + 250 * abs(pct_delta)",
                "recommended_owner": "business_owner",
                "next_step": "compare directional forecast risk with pipeline, capacity, and recent actuals",
            }
        )
    cluster = next((table for table in evidence_tables if table.get("title") == _zh(r"\u5206\u7fa4\u753b\u50cf")), None)
    if cluster and cluster.get("rows"):
        largest = max(cluster["rows"], key=lambda item: float(item.get("share") or 0.0))
        score = min(100.0, 30.0 + float(largest.get("share") or 0.0) * 100.0)
        rows.append(
            {
                "action": f"design_segment_playbook_cluster_{largest.get('cluster')}",
                "evidence": "cluster_profile",
                "source_ref": "table:cluster_profile",
                "priority_score": round(score, 2),
                "priority": _priority_label(score),
                "why": f"share={largest.get('share')}, x_mean={largest.get('x_mean')}, y_mean={largest.get('y_mean')}",
                "score_reason": "30 + 100 * largest_cluster_share",
                "recommended_owner": "operations_or_growth_owner",
                "next_step": "draft a differentiated playbook for the largest segment and validate it on a holdout slice",
            }
        )
    anomaly = next((table for table in evidence_tables if table.get("title") == _zh(r"\u5f02\u5e38 Top-N")), None)
    if anomaly and anomaly.get("rows"):
        top = anomaly["rows"][0]
        threshold = float(top.get("threshold") or 1.0) or 1.0
        score = min(100.0, 30.0 + float(top.get("score") or 0.0) / threshold * 50.0)
        rows.append(
            {
                "action": "investigate_top_anomalies",
                "evidence": "anomaly_top_n",
                "source_ref": "table:anomaly_top_n",
                "priority_score": round(score, 2),
                "priority": _priority_label(score),
                "why": f"top={top.get('name')}, score={top.get('score')}, threshold={top.get('threshold')}",
                "score_reason": "30 + 50 * top_score / threshold",
                "recommended_owner": "risk_or_data_quality_owner",
                "next_step": "triage top anomalies into opportunity, risk event, or data quality issue",
            }
        )
    heatmap = next((chart for chart in charts if chart.get("kind") == "heatmap"), None)
    if heatmap:
        pairs = _top_correlation_pairs(heatmap, limit=1)
        if pairs:
            pair = pairs[0]
            score = min(100.0, 25.0 + pair["abs_strength"] * 75.0)
            rows.append(
                {
                    "action": f"validate_driver_{pair['driver']}_to_{pair['target']}",
                    "evidence": "driver_hypothesis",
                    "source_ref": "chart:correlation_heatmap",
                    "priority_score": round(score, 2),
                    "priority": _priority_label(score),
                    "why": f"correlation={pair['strength']}, caveat=correlation_not_causation",
                    "score_reason": "25 + 75 * abs(correlation)",
                    "recommended_owner": "analytics_lead",
                    "next_step": "check whether the driver relationship survives controls, lags, or segment splits",
                }
            )
    time_series = next((table for table in evidence_tables if table.get("title") == _zh(r"\u65f6\u95f4\u5e8f\u5217\u8bca\u65ad")), None)
    if time_series and time_series.get("rows"):
        item = time_series["rows"][0]
        pct_change = abs(float(item.get("pct_change") or 0.0))
        volatility = abs(float(item.get("volatility_index") or 0.0))
        score = min(100.0, 35.0 + pct_change * 150.0 + volatility * 200.0)
        rows.append(
            {
                "action": "run_time_series_backtest_or_change_point_review",
                "evidence": "time_series_diagnostic",
                "source_ref": "table:time_series_diagnostics",
                "priority_score": round(score, 2),
                "priority": _priority_label(score),
                "why": f"direction={item.get('trend_direction')}, pct_change={item.get('pct_change')}, volatility={item.get('volatility_index')}",
                "score_reason": "35 + 150 * abs(pct_change) + 200 * volatility_index",
                "recommended_owner": "analytics_lead",
                "next_step": item.get("next_step"),
            }
        )
    causal = next((table for table in evidence_tables if table.get("title") == _zh(r"\u56e0\u679c\u5019\u9009\u8def\u5f84")), None)
    if causal and causal.get("rows"):
        top = max(causal["rows"], key=lambda item: float(item.get("readiness_score") or 0.0))
        score = min(100.0, 30.0 + float(top.get("readiness_score") or 0.0) * 0.7)
        rows.append(
            {
                "action": f"validate_{top.get('candidate_id')}",
                "evidence": "causal_candidate_path",
                "source_ref": "table:causal_candidate_paths",
                "priority_score": round(score, 2),
                "priority": _priority_label(score),
                "why": f"driver={top.get('driver')}, outcome={top.get('outcome')}, readiness={top.get('readiness_score')}",
                "score_reason": "30 + 0.7 * causal_readiness_score",
                "recommended_owner": "analytics_lead",
                "next_step": top.get("next_step"),
            }
        )
    causal_executor = next((table for table in evidence_tables if table.get("title") == _zh(r"\u56e0\u679c\u8f7b\u91cf\u6267\u884c\u7ed3\u679c")), None)
    if causal_executor and causal_executor.get("rows"):
        top = max(causal_executor["rows"], key=lambda item: float(item.get("priority_score") or 0.0))
        score = min(100.0, 35.0 + float(top.get("priority_score") or 0.0) * 0.65)
        rows.append(
            {
                "action": f"review_causal_light_executor_{top.get('driver')}_to_{top.get('outcome')}",
                "evidence": "causal_light_executor",
                "source_ref": "table:causal_light_executor_results",
                "priority_score": round(score, 2),
                "priority": _priority_label(score),
                "why": f"effect={top.get('effect_estimate')}, standardized={top.get('standardized_effect')}, ci=[{top.get('bootstrap_ci_low')}, {top.get('bootstrap_ci_high')}], quality={top.get('executor_quality')}",
                "score_reason": "35 + 0.65 * executor_priority_score",
                "recommended_owner": "analytics_lead",
                "next_step": top.get("next_step"),
            }
        )
    rows.sort(key=lambda item: float(item.get("priority_score") or 0.0), reverse=True)
    return rows


def build_evidence_tables(charts: list[dict[str, Any]], extra_tables: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    tables: list[dict[str, Any]] = []
    for chart in charts:
        kind = str(chart.get("kind") or "")
        if kind == "forecast":
            rows = _forecast_rows(chart)
            if rows:
                tables.append(_table(_zh(r"\u9884\u6d4b\u98ce\u9669\u6458\u8981"), rows))
        elif kind == "cluster-scatter":
            rows = _cluster_rows(chart)
            if rows:
                tables.append(_table(_zh(r"\u5206\u7fa4\u753b\u50cf"), rows))
        elif kind == "anomaly-scatter":
            rows = _anomaly_rows(chart)
            if rows:
                tables.append(_table(_zh(r"\u5f02\u5e38 Top-N"), rows))
    driver_rows = _driver_hypothesis_rows(charts)
    if driver_rows:
        tables.append(_table(_zh(r"\u9a71\u52a8\u5047\u8bbe"), driver_rows))
    time_series_rows = _time_series_diagnostic_rows(charts)
    if time_series_rows:
        tables.append(_table(_zh(r"\u65f6\u95f4\u5e8f\u5217\u8bca\u65ad"), time_series_rows))
    causal_rows = _causal_candidate_rows(charts, tables)
    if causal_rows:
        tables.append(_table(_zh(r"\u56e0\u679c\u5019\u9009\u8def\u5f84"), causal_rows))
    tables.extend(extra_tables or [])
    priority_rows = _action_priority_rows(tables, charts)
    if priority_rows:
        tables.append(_table(_zh(r"\u884c\u52a8\u4f18\u5148\u7ea7\u8bc4\u5206"), priority_rows))
    return tables
