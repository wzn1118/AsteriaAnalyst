from __future__ import annotations

from collections.abc import Callable
import hashlib
from typing import Any

import numpy as np
import pandas as pd

from app.models import StatisticRequest
from app.services.analysis_service import SUPPORTED_ANALYSIS_TYPES, run_statistical_analysis


def _zh(value: str) -> str:
    return value.encode("ascii").decode("unicode_escape")


EXECUTION_TABLE_TITLE = _zh(r"\u65b9\u6cd5\u5361\u6267\u884c\u7ed3\u679c")
ASSET_TABLE_TITLE = _zh(r"\u65b9\u6cd5\u5361\u6267\u884c\u8d44\u4ea7")
STATISTICAL_OUTPUT_VARIANTS = ("text", "table", "data", "chart", "image_spec", "report_section")


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _safe_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(number):
        return None
    return round(number, 6)


def _series(frame: pd.DataFrame, column: str) -> pd.Series:
    value = frame.loc[:, column]
    if isinstance(value, pd.DataFrame):
        return value.iloc[:, 0]
    return value


def _list_text(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [_clean_text(item) for item in values if _clean_text(item)]


def _binding_fields(bindings: dict[str, Any]) -> list[str]:
    fields: list[str] = []
    for value in bindings.values():
        if isinstance(value, list):
            fields.extend(_list_text(value))
        elif isinstance(value, str):
            fields.append(value)
    return [field for field in dict.fromkeys(fields) if field and field != "all_rows"]


def _existing_fields(frame: pd.DataFrame, bindings: dict[str, Any]) -> list[str]:
    columns = set(frame.columns.astype(str).tolist())
    return [field for field in _binding_fields(bindings) if field in columns]


def _statistical_analysis_type(card: dict[str, Any]) -> str:
    candidates = [
        _clean_text(card.get("analysis_type")),
        _clean_text(card.get("base_method_id")),
        _clean_text(card.get("method_id")),
    ]
    method_id = _clean_text(card.get("method_id"))
    for suffix in STATISTICAL_OUTPUT_VARIANTS:
        if method_id.endswith(f"_{suffix}"):
            candidates.append(method_id[: -(len(suffix) + 1)])
    for candidate in candidates:
        if candidate in SUPPORTED_ANALYSIS_TYPES:
            return candidate
    return ""


def _first_existing(frame: pd.DataFrame, values: list[Any]) -> str:
    columns = set(frame.columns.astype(str).tolist())
    for value in values:
        text = _clean_text(value)
        if text in columns:
            return text
    return ""


def _int_option(options: dict[str, Any], key: str, default: int, *, minimum: int, maximum: int) -> int:
    try:
        value = int(options.get(key))
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(maximum, value))


def _float_option(options: dict[str, Any], key: str, default: float, *, minimum: float, maximum: float) -> float:
    try:
        value = float(options.get(key))
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(maximum, value))


def _choice_option(options: dict[str, Any], key: str, default: str, allowed: set[str]) -> str:
    value = _clean_text(options.get(key)) or default
    return value if value in allowed else default


def _statistical_request_from_card(frame: pd.DataFrame, card: dict[str, Any]) -> StatisticRequest | None:
    analysis_type = _statistical_analysis_type(card)
    if not analysis_type:
        return None
    bindings = dict(card.get("field_bindings") or {})
    options = dict(card.get("statistical_options") or {}) if isinstance(card.get("statistical_options"), dict) else {}
    existing = _existing_fields(frame, bindings)
    numeric = _numeric_fields(frame, existing or frame.columns.astype(str).tolist(), limit=8)
    target = _first_existing(frame, [bindings.get("target"), bindings.get("field"), bindings.get("y"), numeric[0] if numeric else ""])
    group_column = _first_existing(frame, [bindings.get("group"), bindings.get("time"), bindings.get("category"), bindings.get("dimension"), bindings.get("x")])
    raw_features = bindings.get("features") if isinstance(bindings.get("features"), list) else []
    raw_feature_fields = _list_text(raw_features)
    for alias in ["paired", "strata", "segment", "rater", "reviewer"]:
        alias_field = _clean_text(bindings.get(alias))
        if alias_field:
            raw_feature_fields.append(alias_field)
    features = _numeric_fields(frame, _list_text(raw_features), limit=8)
    if not features:
        features = [field for field in numeric if field != target][:8]
    if analysis_type == "correlation":
        features = _numeric_fields(frame, list(dict.fromkeys([*features, *numeric])), limit=8)
    if analysis_type == "partial_correlation" and len(features) < 2:
        features = [field for field in numeric if field != target][:8]
    if analysis_type in {"pca", "kmeans", "repeated_measures_anova", "friedman"} and len(features) < 2:
        features = list(dict.fromkeys(numeric))[:8]
    if analysis_type in {
        "ols",
        "ridge_regression",
        "lasso_regression",
        "elastic_net",
        "robust_regression",
        "quantile_regression",
        "breusch_pagan",
        "white_test",
        "durbin_watson",
        "logit",
        "poisson_glm",
        "random_forest",
        "neural_network",
        "deep_learning",
    }:
        features = [field for field in dict.fromkeys(features) if field != target][:8]
    if analysis_type in {"mcnemar", "cochran_q", "cohens_kappa"}:
        categorical_features = [
            field
            for field in dict.fromkeys([*raw_feature_fields, *existing])
            if field in frame.columns and field != target
        ]
        features = categorical_features[:8]
    if analysis_type == "cmh_test":
        categorical_features = [
            field
            for field in dict.fromkeys([*raw_feature_fields, *existing])
            if field in frame.columns and field not in {target, group_column}
        ]
        features = categorical_features[:8]
    if analysis_type == "two_way_anova":
        factor_features = [
            field
            for field in dict.fromkeys([*raw_feature_fields, *existing])
            if field in frame.columns and field not in {target, group_column}
        ]
        features = factor_features[:8]
    if analysis_type == "ancova" and not features:
        features = [field for field in numeric if field != target][:8]
    return StatisticRequest(
        dataset_id="analysis_lab_method_card",
        analysis_type=analysis_type,  # type: ignore[arg-type]
        target=target or None,
        features=features,
        group_column=group_column or None,
        group_a=_clean_text(options.get("group_a")) or None,
        group_b=_clean_text(options.get("group_b")) or None,
        components=_int_option(options, "components", 2, minimum=1, maximum=12),
        clusters=_int_option(options, "clusters", 3, minimum=2, maximum=12),
        window=_int_option(options, "window", 3, minimum=2, maximum=90),
        lag=_int_option(options, "lag", 12, minimum=1, maximum=120),
        regularization_strength=_float_option(options, "regularization_strength", 1.0, minimum=0.0001, maximum=100.0),
        l1_ratio=_float_option(options, "l1_ratio", 0.5, minimum=0.0, maximum=1.0),
        quantile=_float_option(options, "quantile", 0.5, minimum=0.05, maximum=0.95),
        bootstrap_iterations=_int_option(options, "bootstrap_iterations", 1000, minimum=100, maximum=10000),
        metric_type=_choice_option(options, "metric_type", "auto", {"auto", "continuous", "binary"}),  # type: ignore[arg-type]
        alpha=_float_option(options, "alpha", 0.05, minimum=0.0001, maximum=0.2),
        hypothesis=_choice_option(options, "hypothesis", "two-sided", {"two-sided", "larger", "smaller"}),  # type: ignore[arg-type]
        test_value=_float_option(options, "test_value", 0.0, minimum=-1_000_000_000, maximum=1_000_000_000),
        population_std=_float_option(options, "population_std", 0.0, minimum=0.0, maximum=1_000_000_000) or None,
        success_value=options.get("success_value") if options.get("success_value") not in ("", None) else None,
    )


def _numeric_fields(frame: pd.DataFrame, fields: list[str], *, limit: int = 8) -> list[str]:
    result: list[str] = []
    for field in fields:
        if field not in frame.columns:
            continue
        values = pd.to_numeric(frame[field], errors="coerce")
        if values.notna().sum() >= 2:
            result.append(field)
        if len(result) >= limit:
            break
    return result


def _columns_from_rows(rows: list[dict[str, Any]]) -> list[str]:
    columns: list[str] = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    return columns


def _format_number(value: Any) -> float | None:
    number = _safe_float(value)
    return round(number, 6) if number is not None else None


def _field_profile_rows(frame: pd.DataFrame, fields: list[str], *, limit: int = 12) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for field in fields[:limit]:
        if field not in frame.columns:
            continue
        series = _series(frame, field)
        non_null = int(series.notna().sum())
        row: dict[str, Any] = {
            "字段": field,
            "样本数": non_null,
            "缺失数": int(series.isna().sum()),
            "缺失率": round(float(series.isna().mean()), 6),
        }
        numeric = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
        if not numeric.empty:
            row.update(
                {
                    "字段类型": "numeric",
                    "均值": _format_number(numeric.mean()),
                    "中位数": _format_number(numeric.median()),
                    "最小值": _format_number(numeric.min()),
                    "最大值": _format_number(numeric.max()),
                    "标准差": _format_number(numeric.std(ddof=0)),
                }
            )
        else:
            top = series.dropna().astype(str).value_counts().head(3)
            row.update(
                {
                    "字段类型": "category",
                    "唯一值数": int(series.dropna().astype(str).nunique()),
                    "Top取值": "；".join(f"{index}={count}" for index, count in top.items()),
                }
            )
        rows.append(row)
    return rows


def _group_summary_rows(frame: pd.DataFrame, group_field: str, numeric_fields: list[str], *, limit: int = 12) -> list[dict[str, Any]]:
    if not group_field or group_field not in frame.columns or not numeric_fields:
        return []
    metric = next((field for field in numeric_fields if field in frame.columns), "")
    if not metric:
        return []
    working = frame[[group_field, metric]].copy()
    working[metric] = pd.to_numeric(working[metric], errors="coerce")
    working = working.dropna(subset=[group_field, metric])
    if working.empty:
        return []
    grouped = (
        working.groupby(group_field, dropna=False)[metric]
        .agg(["count", "mean", "sum", "min", "max"])
        .sort_values("sum", ascending=False)
        .head(limit)
    )
    return [
        {
            "分组字段": group_field,
            "分组": str(index),
            "指标": metric,
            "样本数": int(row["count"]),
            "均值": _format_number(row["mean"]),
            "合计": _format_number(row["sum"]),
            "最小值": _format_number(row["min"]),
            "最大值": _format_number(row["max"]),
        }
        for index, row in grouped.iterrows()
    ]


def _association_rows(pairs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pair in pairs[:12]:
        corr = _format_number(pair.get("correlation"))
        direction = "正相关" if (corr or 0) >= 0 else "负相关"
        strength = abs(float(corr or 0.0))
        rows.append(
            {
                "变量1": pair.get("x"),
                "变量2": pair.get("y"),
                "相关系数": corr,
                "方向": direction,
                "强度判断": "强" if strength >= 0.7 else "中" if strength >= 0.4 else "弱",
            }
        )
    return rows


def _model_candidate_rows(frame: pd.DataFrame, fields: list[str], *, limit: int = 12) -> list[dict[str, Any]]:
    numeric = _numeric_fields(frame, fields, limit=limit)
    if len(numeric) < 2:
        return _field_profile_rows(frame, fields, limit=limit)
    target = numeric[0]
    target_values = pd.to_numeric(_series(frame, target), errors="coerce")
    rows: list[dict[str, Any]] = []
    for feature in numeric[1:limit]:
        feature_values = pd.to_numeric(_series(frame, feature), errors="coerce")
        clean = pd.DataFrame({"target": target_values, "feature": feature_values}).dropna()
        if len(clean) < 2:
            continue
        corr = _format_number(clean["feature"].corr(clean["target"]))
        variance = float(clean["feature"].var(ddof=0) or 0.0)
        slope = _format_number(clean["feature"].cov(clean["target"]) / variance) if variance else None
        rows.append(
            {
                "目标指标": target,
                "候选解释变量": feature,
                "样本数": int(len(clean)),
                "相关系数": corr,
                "单变量斜率": slope,
                "目标均值": _format_number(clean["target"].mean()),
                "变量均值": _format_number(clean["feature"].mean()),
            }
        )
    return rows or _field_profile_rows(frame, numeric, limit=limit)


def _causal_screen_rows(frame: pd.DataFrame, fields: list[str], *, limit: int = 8) -> list[dict[str, Any]]:
    numeric = _numeric_fields(frame, fields, limit=limit)
    if len(numeric) < 2:
        return _field_profile_rows(frame, fields, limit=limit)
    target = numeric[0]
    target_values = pd.to_numeric(_series(frame, target), errors="coerce")
    rows: list[dict[str, Any]] = []
    for driver in numeric[1:limit]:
        driver_values = pd.to_numeric(_series(frame, driver), errors="coerce")
        clean = pd.DataFrame({"target": target_values, "driver": driver_values}).dropna()
        if len(clean) < 4:
            continue
        median = clean["driver"].median()
        high = clean.loc[clean["driver"] >= median, "target"]
        low = clean.loc[clean["driver"] < median, "target"]
        if high.empty or low.empty:
            continue
        rows.append(
            {
                "目标指标": target,
                "候选驱动": driver,
                "切分方式": "按驱动中位数分组",
                "高组样本数": int(len(high)),
                "低组样本数": int(len(low)),
                "高组目标均值": _format_number(high.mean()),
                "低组目标均值": _format_number(low.mean()),
                "均值差": _format_number(high.mean() - low.mean()),
            }
        )
    return rows or _field_profile_rows(frame, numeric, limit=limit)


def _chart_result_rows(charts: list[dict[str, Any]], refs: list[str], *, limit: int = 12) -> list[dict[str, Any]]:
    requested = {ref.split(":", 1)[1] for ref in refs if ":" in ref}
    rows: list[dict[str, Any]] = []
    for chart in charts:
        kind = str(chart.get("kind") or "")
        if requested and kind not in requested:
            continue
        point_count = 0
        for key in ("points", "x", "labels", "actual", "forecast", "matrix"):
            value = chart.get(key)
            if isinstance(value, list):
                point_count = len(value)
                break
        row = {
            "图表引用": f"chart:{kind}",
            "图表类型": kind,
            "标题": chart.get("title") or "",
            "X字段": chart.get("x_label") or chart.get("x") or "",
            "Y字段": chart.get("y_label") or "",
            "数据点数": point_count,
            "业务解读": _business_chart_interpretation(chart),
        }
        if kind == "heatmap":
            labels = list(chart.get("labels") or [])
            row["指标数量"] = len(labels)
        elif kind == "cluster-scatter":
            row["分群数量"] = len(list(chart.get("cluster_summary") or []))
        elif kind == "anomaly-scatter":
            points = list(chart.get("points") or [])
            row["异常点数"] = sum(1 for point in points if isinstance(point, dict) and point.get("is_anomaly"))
        rows.append(row)
        if len(rows) >= limit:
            break
    return rows


def _chart_point_count(chart: dict[str, Any]) -> int:
    for key in ("points", "x", "labels", "actual", "forecast", "matrix"):
        value = chart.get(key)
        if isinstance(value, list):
            return len(value)
    return 0


def _format_business_number(value: Any) -> str:
    number = _safe_float(value)
    if number is None:
        return _clean_text(value) or "-"
    if abs(number) >= 10000:
        return f"{number / 10000:.1f}万"
    if abs(number) >= 1000:
        return f"{number:,.0f}"
    return f"{number:.3g}"


def _business_chart_interpretation(chart: dict[str, Any]) -> str:
    kind = _clean_text(chart.get("kind"))
    x_label = _clean_text(chart.get("x_label"))
    y_label = _clean_text(chart.get("y_label"))
    points = list(chart.get("points") or []) if isinstance(chart.get("points"), list) else []
    if kind in {"bubble", "quadrant"} and points:
        counts: dict[str, int] = {}
        for point in points:
            if isinstance(point, dict):
                quadrant = _clean_text(point.get("quadrant")) or "unknown"
                counts[quadrant] = counts.get(quadrant, 0) + 1
        high_high = counts.get("high_high", 0)
        high_low = counts.get("high_low", 0)
        low_high = counts.get("low_high", 0)
        low_low = counts.get("low_low", 0)
        sorted_points = sorted(
            [point for point in points if isinstance(point, dict)],
            key=lambda point: float(abs(_safe_float(point.get("size")) or 0.0)),
            reverse=True,
        )
        top = sorted_points[0] if sorted_points else {}
        action = (
            "优先复核低收入高支出对象的资金缺口和项目效率"
            if low_high >= max(high_high, high_low, low_low)
            else "优先放大高收入高支出对象的成熟项目打法"
            if high_high >= max(high_low, low_high, low_low)
            else "优先核对高支出低回报对象的预算配置"
        )
        return (
            f"{x_label or 'X指标'} 与 {y_label or 'Y指标'} 形成四象限分化："
            f"高高{high_high}、高低{high_low}、低高{low_high}、低低{low_low}。"
            f"最大气泡是 {top.get('name') or '-'}，规模约 {_format_business_number(top.get('size'))}。"
            f"业务判断：{action}，不要把它当作图表说明。"
        )
    if kind == "histogram":
        labels = list(chart.get("x") or [])
        counts = list(chart.get("y") or [])
        if labels and counts:
            max_index = int(np.argmax(np.asarray(counts, dtype=float)))
            total = sum(float(item or 0) for item in counts) or 1.0
            share = float(counts[max_index] or 0) / total
            return (
                f"{x_label or '核心指标'} 的分布集中在 {labels[max_index]} 区间，占比 {share:.1%}。"
                "业务判断：如果高值区间样本很少，应单独做重点项目/异常项目复核，不能只看平均值。"
            )
    if kind == "heatmap":
        labels = list(chart.get("labels") or [])
        matrix = list(chart.get("matrix") or [])
        best: tuple[str, str, float] | None = None
        for row_index, row in enumerate(matrix):
            if not isinstance(row, list):
                continue
            for col_index, value in enumerate(row):
                if row_index >= col_index:
                    continue
                number = _safe_float(value)
                if number is None:
                    continue
                if best is None or abs(number) > abs(best[2]):
                    best = (_clean_text(labels[row_index]) if row_index < len(labels) else "-", _clean_text(labels[col_index]) if col_index < len(labels) else "-", number)
        if best:
            return f"{best[0]} 与 {best[1]} 的相关系数约 {best[2]:.2f}。业务判断：强相关只能作为驱动线索，下一步要核对业务机制和字段口径。"
    if kind == "cluster-scatter":
        summary = [item for item in list(chart.get("cluster_summary") or []) if isinstance(item, dict)]
        if summary:
            largest = max(summary, key=lambda item: int(item.get("count") or 0))
            return (
                f"分群结果中 cluster={largest.get('cluster')} 覆盖 {largest.get('count')} 个对象，"
                f"平均{x_label or 'X'}={_format_business_number(largest.get('x_mean'))}，平均{y_label or 'Y'}={_format_business_number(largest.get('y_mean'))}。"
                "业务判断：先为主群体制定标准动作，再对少数高规模群体单列策略。"
            )
    if kind == "anomaly-scatter":
        anomaly_count = sum(1 for point in points if isinstance(point, dict) and point.get("is_anomaly"))
        return f"异常筛查识别 {anomaly_count} 个高偏离对象。业务判断：这些对象应进入风险、机会和数据质量三类复核清单，而不是合并进总体均值。"
    if kind in {"scatter", "cluster-scatter"} and points:
        return f"{x_label or 'X指标'} 与 {y_label or 'Y指标'} 有 {_chart_point_count(chart)} 个可视点。业务判断：先看离群点和高值聚集区，再决定是否做分层运营。"
    return _clean_text(chart.get("explanation")) or "该图表用于支持业务判断，需结合字段口径和样本范围解读。"


def _chart_refs(card: dict[str, Any]) -> list[str]:
    refs = [ref for ref in _list_text(card.get("evidence_refs")) if ref.startswith("chart:")]
    if not refs:
        return []
    method_text = " ".join(
        [
            _clean_text(card.get("method_id")),
            _clean_text(card.get("method_run_id")),
            _clean_text(card.get("method_name")),
            _clean_text(card.get("method_name_zh")),
            _clean_text(card.get("executor_hint")),
        ]
    ).lower()
    bound_text = " ".join(str(value or "") for value in dict(card.get("field_bindings") or {}).values()).lower()
    intent_text = f"{method_text} {bound_text}"
    preference_rules: list[tuple[tuple[str, ...], list[str]]] = [
        (("bubble", "气泡"), ["chart:bubble", "chart:quadrant", "chart:bar-region"]),
        (("quadrant", "象限"), ["chart:quadrant", "chart:bubble", "chart:bar-service"]),
        (("scatter", "散点", "association", "相关"), ["chart:scatter", "chart:heatmap", "chart:bar-organization"]),
        (("histogram", "distribution", "分布", "violin", "小提琴"), ["chart:histogram", "chart:bar-service", "chart:bar-region"]),
        (("heatmap", "corr", "相关矩阵"), ["chart:heatmap", "chart:scatter", "chart:bar-organization"]),
        (("cluster", "clustering", "分群"), ["chart:cluster-scatter", "chart:bar-organization", "chart:bar-service"]),
        (("anomaly", "outlier", "异常"), ["chart:anomaly-scatter", "chart:scatter", "chart:bar-region"]),
        (("time", "forecast", "trend", "年度", "year"), ["chart:line", "chart:forecast", "chart:bar-year"]),
        (("region", "地区", "地域", "省", "市"), ["chart:bar-region", "chart:bubble", "chart:anomaly-scatter"]),
        (("service", "服务", "领域"), ["chart:bar-service", "chart:quadrant", "chart:histogram"]),
        (("foundation", "基金会", "组织", "画像", "类型"), ["chart:bar-organization", "chart:cluster-scatter", "chart:heatmap"]),
    ]
    selected: list[str] = []
    ref_set = set(refs)
    for tokens, candidates in preference_rules:
        if not any(token in intent_text for token in tokens):
            continue
        for candidate in candidates:
            if candidate in ref_set and candidate not in selected:
                selected.append(candidate)
        if selected:
            break
    if not selected:
        digest = hashlib.sha1(intent_text.encode("utf-8", errors="ignore")).hexdigest()
        start = int(digest[:4], 16) % len(refs)
        selected = [refs[(start + offset) % len(refs)] for offset in range(min(3, len(refs)))]
    start = 0
    if selected:
        try:
            start = (refs.index(selected[-1]) + 1) % len(refs)
        except ValueError:
            start = int(hashlib.sha1(intent_text.encode("utf-8", errors="ignore")).hexdigest()[:4], 16) % len(refs)
    for offset in range(len(refs)):
        ref = refs[(start + offset) % len(refs)]
        if ref not in selected and len(selected) < 3:
            selected.append(ref)
    return selected[:3]


def _make_asset(card: dict[str, Any], *, asset_type: str, asset_ref: str, payload: dict[str, Any]) -> dict[str, Any]:
    enriched_payload = dict(payload)
    semantic_contract = card.get("runtime_field_selection_contract") if isinstance(card.get("runtime_field_selection_contract"), dict) else {}
    semantic_routes = list(card.get("semantic_field_routes") or []) if isinstance(card.get("semantic_field_routes"), list) else []
    semantic_refs = _list_text(card.get("semantic_route_refs"))
    cli_interpretation = _clean_text(card.get("cli_interpretation"))
    enriched_payload.setdefault("runtime_field_selection_contract", semantic_contract)
    enriched_payload.setdefault("semantic_field_routes", semantic_routes)
    enriched_payload.setdefault("semantic_route_refs", semantic_refs)
    enriched_payload.setdefault("cli_interpretation_enabled", bool(card.get("cli_interpretation_enabled", True)))
    enriched_payload.setdefault("cli_interpretation", cli_interpretation)
    return {
        "asset_type": asset_type,
        "asset_ref": asset_ref,
        "method_id": _clean_text(card.get("method_id")),
        "method_run_id": _clean_text(card.get("method_run_id") or card.get("method_id")),
        "executor_hint": _clean_text(card.get("executor_hint")),
        "report_slots": _list_text(card.get("report_slots")),
        "evidence_refs": _list_text(card.get("evidence_refs")),
        "semantic_route_refs": semantic_refs,
        "cli_interpretation_enabled": bool(card.get("cli_interpretation_enabled", True)),
        "cli_interpretation": cli_interpretation,
        "payload": enriched_payload,
    }


def _runtime_handoff_for_asset(card: dict[str, Any], asset: dict[str, Any], *, status: str, output_type: str) -> dict[str, Any]:
    semantic_contract = card.get("runtime_field_selection_contract") if isinstance(card.get("runtime_field_selection_contract"), dict) else {}
    bindings = dict(card.get("field_bindings") or {})
    object_selection = card.get("object_selection") if isinstance(card.get("object_selection"), dict) else {}
    runtime_status = "runtime_handoff_ready" if status in {"ready", "partial"} else "runtime_blocked"
    return {
        "target": "codex_cli_exec_runtime",
        "task": f"execute_method_asset:{_clean_text(asset.get('method_run_id') or asset.get('method_id') or card.get('method_id'))}",
        "status": runtime_status,
        "local_preparation_status": status,
        "runtime_required": True,
        "runtime_executor": "codex_cli",
        "runtime_job_id": "",
        "runtime_manifest_path": "",
        "runtime_error": "",
        "executor_hint": _clean_text(asset.get("executor_hint") or card.get("executor_hint")),
        "asset_type": _clean_text(asset.get("asset_type")),
        "asset_ref": _clean_text(asset.get("asset_ref")),
        "expected_output_type": output_type,
        "allowed_outputs": ["text", "table", "structured_data", "chart", "image_spec", "report_section"],
        "selection_mode": _clean_text(card.get("selection_mode")) or "fields",
        "object_selection": object_selection,
        "smart_merge_group": _clean_text(card.get("smart_merge_group")),
        "field_bindings": bindings,
        "bound_fields": _binding_fields(bindings),
        "report_slots": _list_text(card.get("report_slots")),
        "evidence_refs": _list_text(card.get("evidence_refs")),
        "semantic_route_refs": _list_text(card.get("semantic_route_refs")),
        "cli_interpretation_enabled": bool(card.get("cli_interpretation_enabled", True)),
        "cli_interpretation": _clean_text(card.get("cli_interpretation")),
        "pre_method_preprocessing_status": _clean_text(semantic_contract.get("pre_method_preprocessing_status"))
        or "derived_fields_completed_before_method_routing",
        "must_use_field_semantics": True,
        "must_preserve_evidence_refs": True,
    }


def _base_result(card: dict[str, Any], *, output_type: str, status: str = "ready") -> dict[str, Any]:
    slots = _list_text(card.get("report_slots"))
    return {
        "status": status,
        "runtime_status": "runtime_handoff_ready" if status in {"ready", "partial"} else "runtime_blocked",
        "runtime_required": True,
        "runtime_executor": "codex_cli",
        "runtime_job_id": "",
        "runtime_manifest_path": "",
        "runtime_error": "",
        "output_type": output_type,
        "result_ref": f"{output_type}:{slots[0]}" if slots else output_type,
        "result_summary": "",
        "next_step": "attach result to requested report slot",
    }


def _execute_chart_asset_builder(frame: pd.DataFrame, card: dict[str, Any], charts: list[dict[str, Any]]) -> dict[str, Any]:
    result = _base_result(card, output_type="chart_asset")
    refs = _chart_refs(card)
    result["result_ref"] = refs[0] if refs else "chart:pending"
    result["status"] = "ready" if refs or charts else "partial"
    result["result_summary"] = f"linked {len(refs) or min(len(charts), 1)} chart asset reference(s) for visual report assembly"
    result["next_step"] = "render chart asset with management interpretation"
    result_rows = _chart_result_rows(charts, refs)
    result["result_rows"] = result_rows
    result["result_columns"] = _columns_from_rows(result_rows)
    requested = {ref.split(":", 1)[1] for ref in refs if ":" in ref}
    linked_charts = [
        chart
        for chart in charts
        if isinstance(chart, dict) and (not requested or _clean_text(chart.get("kind")) in requested)
    ]
    result["asset"] = _make_asset(
        card,
        asset_type="chart_asset",
        asset_ref=result["result_ref"],
        payload={
            "chart_refs": refs,
            "available_chart_count": len(charts),
            "linked_charts": linked_charts[:12],
            "business_interpretations": [
                {
                    "chart_ref": f"chart:{_clean_text(chart.get('kind'))}",
                    "title": chart.get("title") or "",
                    "business_interpretation": _business_chart_interpretation(chart),
                }
                for chart in linked_charts[:12]
            ],
        },
    )
    return result


def _execute_report_section_writer(frame: pd.DataFrame, card: dict[str, Any], charts: list[dict[str, Any]]) -> dict[str, Any]:
    result = _base_result(card, output_type="report_section")
    slots = _list_text(card.get("report_slots"))
    evidence_refs = _list_text(card.get("evidence_refs"))
    result["result_ref"] = f"report_part:{slots[0]}" if slots else "report_part:auto"
    result["result_summary"] = f"section contract ready with {len(evidence_refs)} evidence reference(s)"
    result["next_step"] = "generate narrative, bullets, tables and evidence index for the slot"
    result_rows = [
        {
            "报告槽位": slot or "auto",
            "证据引用数": len(evidence_refs),
            "前5个证据": "；".join(evidence_refs[:5]),
            "产出类型": "report_section",
            "下一步": result["next_step"],
        }
        for slot in (slots or ["auto"])
    ]
    result["result_rows"] = result_rows
    result["result_columns"] = _columns_from_rows(result_rows)
    result["asset"] = _make_asset(card, asset_type="report_section_contract", asset_ref=result["result_ref"], payload={"slots": slots, "evidence_refs": evidence_refs})
    return result


def _execute_association_executor(frame: pd.DataFrame, card: dict[str, Any], charts: list[dict[str, Any]]) -> dict[str, Any]:
    bindings = dict(card.get("field_bindings") or {})
    x = _clean_text(bindings.get("x") or bindings.get("target"))
    features = bindings.get("features") if isinstance(bindings.get("features"), list) else []
    y = _clean_text(bindings.get("y") or (features[0] if features else ""))
    result = _base_result(card, output_type="data")
    if not x or not y or x not in frame.columns or y not in frame.columns:
        result.update({"status": "partial", "result_ref": "association:pending", "result_summary": "association fields are not fully bound"})
        result["asset"] = _make_asset(card, asset_type="association_scan", asset_ref="association:pending", payload={"fields": [], "top_pairs": []})
        return result
    numeric = _numeric_fields(frame, _existing_fields(frame, bindings), limit=8)
    if x not in numeric:
        numeric.insert(0, x)
    if y not in numeric:
        numeric.append(y)
    numeric = _numeric_fields(frame, list(dict.fromkeys(numeric)), limit=8)
    pairs: list[dict[str, Any]] = []
    for left_index, left in enumerate(numeric):
        for right in numeric[left_index + 1:]:
            corr = pd.to_numeric(frame[left], errors="coerce").corr(pd.to_numeric(frame[right], errors="coerce"))
            value = _safe_float(corr)
            if value is None:
                continue
            pairs.append({"x": left, "y": right, "correlation": value, "abs_correlation": abs(value)})
    pairs.sort(key=lambda item: float(item["abs_correlation"]), reverse=True)
    value = pairs[0]["correlation"] if pairs else None
    result["result_ref"] = f"association:{x}:{y}"
    result["result_summary"] = f"top_association={pairs[0]['x']}~{pairs[0]['y']} corr={value}" if value is not None and pairs else f"association({x},{y}) requires more numeric coverage"
    result["next_step"] = "promote strong relationships into explanation or model sections"
    result_rows = _association_rows(pairs)
    result["result_rows"] = result_rows
    result["result_columns"] = _columns_from_rows(result_rows)
    result["asset"] = _make_asset(card, asset_type="association_scan", asset_ref=result["result_ref"], payload={"fields": numeric, "top_pairs": pairs[:10]})
    return result


def _execute_time_series_diagnostic_executor(frame: pd.DataFrame, card: dict[str, Any], charts: list[dict[str, Any]]) -> dict[str, Any]:
    bindings = dict(card.get("field_bindings") or {})
    result = _base_result(card, output_type="table")
    time_field = _clean_text(bindings.get("time"))
    target = _clean_text(bindings.get("target") or bindings.get("derived_metric"))
    result["status"] = "ready" if time_field or _chart_refs(card) else "partial"
    result["result_ref"] = "table:time_series_diagnostics"
    target_values = pd.to_numeric(frame[target], errors="coerce") if target in frame.columns else pd.Series(dtype=float)
    non_null = int(target_values.notna().sum())
    first_value = _safe_float(target_values.dropna().iloc[0]) if non_null else None
    last_value = _safe_float(target_values.dropna().iloc[-1]) if non_null else None
    change = _safe_float((last_value or 0) - (first_value or 0)) if first_value is not None and last_value is not None else None
    result["result_summary"] = f"time diagnostic bound to time={time_field or 'inferred'}, target={target or 'inferred'}, change={change}"
    result["next_step"] = "use trend, lag and forecast evidence in chapter or action plan"
    result_rows = [
        {
            "时间字段": time_field or "未识别",
            "目标指标": target or "未识别",
            "有效样本数": non_null,
            "首个值": first_value,
            "末个值": last_value,
            "变化量": change,
            "判断": "上升" if (change or 0) > 0 else "下降" if (change or 0) < 0 else "平稳或证据不足",
        }
    ]
    result["result_rows"] = result_rows
    result["result_columns"] = _columns_from_rows(result_rows)
    result["asset"] = _make_asset(card, asset_type="time_series_summary", asset_ref=result["result_ref"], payload={"time_field": time_field, "target": target, "non_null": non_null, "first": first_value, "last": last_value, "change": change, "chart_refs": _chart_refs(card)})
    return result


def _execute_causal_screen_executor(frame: pd.DataFrame, card: dict[str, Any], charts: list[dict[str, Any]]) -> dict[str, Any]:
    bindings = dict(card.get("field_bindings") or {})
    fields = _existing_fields(frame, bindings)
    result = _base_result(card, output_type="table")
    result["result_ref"] = "table:causal_light_executor_results"
    result["result_summary"] = "causal screen uses derived-field candidates, stratified effect and bootstrap confidence interval evidence"
    result["next_step"] = "rerun with explicit treatment timing and controls before claiming causality"
    result_rows = _causal_screen_rows(frame, fields)
    result["result_rows"] = result_rows
    result["result_columns"] = _columns_from_rows(result_rows)
    result["asset"] = _make_asset(card, asset_type="causal_screen_reference", asset_ref=result["result_ref"], payload={"required_followup": "explicit treatment timing and controls", "evidence_refs": _list_text(card.get("evidence_refs"))})
    return result


def _execute_profile_table_executor(frame: pd.DataFrame, card: dict[str, Any], charts: list[dict[str, Any]]) -> dict[str, Any]:
    bindings = dict(card.get("field_bindings") or {})
    fields = _existing_fields(frame, bindings)
    field = fields[0] if fields else ""
    result = _base_result(card, output_type="table")
    result["result_ref"] = f"profile:{field}" if field else "profile:dataset"
    result_rows = _field_profile_rows(frame, fields or frame.columns.astype(str).tolist(), limit=12)
    result["result_rows"] = result_rows
    result["result_columns"] = _columns_from_rows(result_rows)
    if field:
        non_null = int(frame[field].notna().sum())
        result["result_summary"] = f"profile ready for {field}: non_null={non_null}, rows={len(frame)}"
        result["asset"] = _make_asset(card, asset_type="profile_summary", asset_ref=result["result_ref"], payload={"field": field, "non_null": non_null, "rows": len(frame)})
    else:
        result["status"] = "partial"
        result["result_summary"] = "profile table needs at least one bound field"
        result["asset"] = _make_asset(card, asset_type="profile_summary", asset_ref=result["result_ref"], payload={"field": "", "non_null": 0, "rows": len(frame)})
    result["next_step"] = "attach profile table to appendix or field glossary"
    return result


def _execute_runtime_model_executor(frame: pd.DataFrame, card: dict[str, Any], charts: list[dict[str, Any]]) -> dict[str, Any]:
    bindings = dict(card.get("field_bindings") or {})
    fields = _existing_fields(frame, bindings)
    result = _base_result(card, output_type="data")
    result["status"] = "ready" if len(fields) >= 2 else "partial"
    result["result_ref"] = "model:runtime_candidate"
    result["result_summary"] = f"model executor candidate with {len(fields)} bound field(s)"
    result["next_step"] = "dispatch to Codex/runtime model executor when stronger modeling is requested"
    result_rows = _model_candidate_rows(frame, fields)
    result["result_rows"] = result_rows
    result["result_columns"] = _columns_from_rows(result_rows)
    result["asset"] = _make_asset(card, asset_type="runtime_model_candidate", asset_ref=result["result_ref"], payload={"fields": fields, "field_count": len(fields)})
    return result


def _execute_table_builder(frame: pd.DataFrame, card: dict[str, Any], charts: list[dict[str, Any]]) -> dict[str, Any]:
    bindings = dict(card.get("field_bindings") or {})
    fields = _existing_fields(frame, bindings)
    numeric = _numeric_fields(frame, fields, limit=8)
    group_field = _clean_text(bindings.get("group") or bindings.get("category") or bindings.get("dimension"))
    result = _base_result(card, output_type="table")
    result["result_ref"] = "table:method_card_output"
    result["result_summary"] = f"table builder ready with binding_quality={_clean_text(card.get('binding_quality')) or 'unknown'}"
    result_rows = _group_summary_rows(frame, group_field, numeric) or _field_profile_rows(frame, fields or frame.columns.astype(str).tolist(), limit=12)
    result["result_rows"] = result_rows
    result["result_columns"] = _columns_from_rows(result_rows)
    result["asset"] = _make_asset(card, asset_type="table_contract", asset_ref=result["result_ref"], payload={"binding_quality": _clean_text(card.get("binding_quality"))})
    return result


def _execute_runtime_explainer(frame: pd.DataFrame, card: dict[str, Any], charts: list[dict[str, Any]]) -> dict[str, Any]:
    bindings = dict(card.get("field_bindings") or {})
    fields = _existing_fields(frame, bindings)
    result = _base_result(card, output_type="text")
    result["result_ref"] = "text:method_explanation"
    result["result_summary"] = "runtime explainer can turn bound fields and evidence refs into narrative"
    result_rows = _field_profile_rows(frame, fields, limit=8)
    result["result_rows"] = result_rows
    result["result_columns"] = _columns_from_rows(result_rows)
    result["asset"] = _make_asset(card, asset_type="text_contract", asset_ref=result["result_ref"], payload={"evidence_refs": _list_text(card.get("evidence_refs"))})
    return result


def _statistical_metric_rows(metrics: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, value in metrics.items():
        if isinstance(value, (dict, list)):
            display_value = str(value)
        else:
            display_value = _format_number(value) if isinstance(value, (int, float, np.generic)) else value
        rows.append({"metric": key, "value": display_value})
    return rows


def _execute_statistical_analysis_executor(frame: pd.DataFrame, card: dict[str, Any], charts: list[dict[str, Any]]) -> dict[str, Any]:
    request = _statistical_request_from_card(frame, card)
    analysis_type = request.analysis_type if request else _statistical_analysis_type(card)
    output_type = (_list_text(card.get("output_types")) or ["data"])[0]
    result = _base_result(card, output_type=output_type)
    result["result_ref"] = f"statistical:{analysis_type or 'pending'}:{output_type}"
    if request is None:
        result.update(
            {
                "status": "partial",
                "runtime_status": "runtime_blocked",
                "result_summary": "statistical method card is not mapped to a live analysis type",
                "next_step": "choose a live statistical catalog card or save a card with a supported base method",
                "result_rows": [],
                "result_columns": [],
            }
        )
        result["asset"] = _make_asset(card, asset_type="statistical_result", asset_ref=result["result_ref"], payload={"analysis_type": analysis_type, "status": "partial"})
        return result
    try:
        stats_result = run_statistical_analysis(frame, request)
    except Exception as exc:
        result.update(
            {
                "status": "partial",
                "runtime_status": "runtime_blocked",
                "result_summary": f"{analysis_type} could not run from current bindings: {exc}",
                "next_step": "edit the method card bindings, target, features or group fields and rerun",
                "result_rows": [],
                "result_columns": [],
            }
        )
        result["asset"] = _make_asset(
            card,
            asset_type="statistical_result",
            asset_ref=result["result_ref"],
            payload={
                "analysis_type": analysis_type,
                "status": "partial",
                "error": str(exc),
                "request": request.model_dump(),
            },
        )
        return result
    tables = list(stats_result.get("tables") or []) if isinstance(stats_result.get("tables"), list) else []
    metrics = dict(stats_result.get("metrics") or {}) if isinstance(stats_result.get("metrics"), dict) else {}
    first_table = next((table for table in tables if isinstance(table, dict) and isinstance(table.get("rows"), list)), {})
    metric_rows = _statistical_metric_rows(metrics)
    table_rows = list(first_table.get("rows") or [])[:40] if isinstance(first_table, dict) else []
    result_rows = table_rows or metric_rows
    result["runtime_status"] = "local_statistical_execution_completed"
    result["result_summary"] = _clean_text(stats_result.get("narrative")) or f"{analysis_type} completed"
    result["next_step"] = "attach statistical metrics, tables and chart payload to the report evidence chain"
    result["result_rows"] = result_rows
    result["result_columns"] = _columns_from_rows(result_rows)
    result["asset"] = _make_asset(
        card,
        asset_type="statistical_result",
        asset_ref=result["result_ref"],
        payload={
            "analysis_type": analysis_type,
            "title": stats_result.get("title"),
            "narrative": stats_result.get("narrative"),
            "metrics": metrics,
            "metric_rows": metric_rows,
            "tables": tables,
            "chart": stats_result.get("chart"),
            "request": request.model_dump(),
        },
    )
    return result


Executor = Callable[[pd.DataFrame, dict[str, Any], list[dict[str, Any]]], dict[str, Any]]


EXECUTOR_REGISTRY: dict[str, Executor] = {
    "chart_asset_builder": _execute_chart_asset_builder,
    "report_section_writer": _execute_report_section_writer,
    "association_executor": _execute_association_executor,
    "time_series_diagnostic_executor": _execute_time_series_diagnostic_executor,
    "causal_screen_executor": _execute_causal_screen_executor,
    "profile_table_executor": _execute_profile_table_executor,
    "runtime_model_executor": _execute_runtime_model_executor,
    "table_builder": _execute_table_builder,
    "runtime_explainer": _execute_runtime_explainer,
    "statistical_analysis_executor": _execute_statistical_analysis_executor,
}


def summarize_method_card_executor_registry() -> dict[str, Any]:
    return {"total_executors": len(EXECUTOR_REGISTRY), "executor_hints": sorted(EXECUTOR_REGISTRY)}


def _execution_artifacts(frame: pd.DataFrame, routed_methods: list[dict[str, Any]], charts: list[dict[str, Any]], *, limit: int = 80) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    assets: list[dict[str, Any]] = []
    for index, method in enumerate(routed_methods[:limit], start=1):
        card = dict(method.get("method_card") or {})
        hint = _clean_text(card.get("executor_hint") or method.get("executor_hint")) or "runtime_explainer"
        executor = EXECUTOR_REGISTRY.get(hint, _execute_runtime_explainer)
        result = executor(frame, card, charts)
        bindings = dict(card.get("field_bindings") or {})
        execution_id = f"method_exec_{index}"
        method_id = _clean_text(method.get("id") or card.get("method_id"))
        method_run_id = _clean_text(method.get("method_run_id") or card.get("method_run_id") or method_id)
        asset = dict(result.get("asset") or _make_asset(card, asset_type="execution_contract", asset_ref=result.get("result_ref", ""), payload={}))
        asset["execution_id"] = execution_id
        asset["method_id"] = method_id
        asset["method_run_id"] = method_run_id
        asset["executor_hint"] = hint
        asset["status"] = result.get("status", "ready")
        asset["runtime_status"] = result.get("runtime_status", "runtime_handoff_ready")
        asset["selection_mode"] = _clean_text(card.get("selection_mode")) or "fields"
        asset["smart_merge_group"] = _clean_text(card.get("smart_merge_group"))
        asset["cli_interpretation_enabled"] = bool(card.get("cli_interpretation_enabled", True))
        asset["cli_interpretation"] = _clean_text(card.get("cli_interpretation"))
        asset["runtime_handoff"] = _runtime_handoff_for_asset(
            card,
            asset,
            status=_clean_text(result.get("status")) or "ready",
            output_type=_clean_text(result.get("output_type")) or "data",
        )
        assets.append(asset)
        rows.append(
            {
                "execution_id": execution_id,
                "method_id": method_id,
                "method_run_id": method_run_id,
                "executor_hint": hint,
                "status": result.get("status", "ready"),
                "runtime_status": result.get("runtime_status", "runtime_handoff_ready"),
                "output_type": result.get("output_type", "data"),
                "selection_mode": _clean_text(card.get("selection_mode")) or "fields",
                "smart_merge_group": _clean_text(card.get("smart_merge_group")),
                "binding_quality": _clean_text(card.get("binding_quality")),
                "bound_fields": ", ".join(_binding_fields(bindings)),
                "semantic_route_refs": ", ".join(_list_text(card.get("semantic_route_refs"))[:8]),
                "report_slots": ", ".join(_list_text(card.get("report_slots"))),
                "evidence_refs": ", ".join(_list_text(card.get("evidence_refs"))[:8]),
                "result_ref": result.get("result_ref", ""),
                "asset_type": asset.get("asset_type", ""),
                "asset_ref": asset.get("asset_ref", ""),
                "runtime_handoff_task": (asset.get("runtime_handoff") or {}).get("task", ""),
                "cli_interpretation_enabled": bool(card.get("cli_interpretation_enabled", True)),
                "cli_interpretation": _clean_text(card.get("cli_interpretation")),
                "result_summary": result.get("result_summary", ""),
                "next_step": result.get("next_step", ""),
                "result_row_count": len(list(result.get("result_rows") or [])),
                "result_columns": ", ".join(str(column) for column in list(result.get("result_columns") or [])[:20]),
                "result_rows": list(result.get("result_rows") or [])[:80],
            }
        )
    return rows, assets


def execute_method_cards(frame: pd.DataFrame, routed_methods: list[dict[str, Any]], charts: list[dict[str, Any]], *, limit: int = 80) -> list[dict[str, Any]]:
    rows, _assets = _execution_artifacts(frame, routed_methods, charts, limit=limit)
    return rows


def execute_method_card_assets(frame: pd.DataFrame, routed_methods: list[dict[str, Any]], charts: list[dict[str, Any]], *, limit: int = 80) -> list[dict[str, Any]]:
    _rows, assets = _execution_artifacts(frame, routed_methods, charts, limit=limit)
    return assets


def _asset_rows(assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for asset in assets:
        payload = asset.get("payload") if isinstance(asset.get("payload"), dict) else {}
        rows.append(
            {
                "execution_id": asset.get("execution_id"),
                "method_id": asset.get("method_id"),
                "method_run_id": asset.get("method_run_id"),
                "executor_hint": asset.get("executor_hint"),
                "status": asset.get("status"),
                "runtime_status": asset.get("runtime_status"),
                "selection_mode": asset.get("selection_mode"),
                "smart_merge_group": asset.get("smart_merge_group"),
                "cli_interpretation_enabled": asset.get("cli_interpretation_enabled"),
                "asset_type": asset.get("asset_type"),
                "asset_ref": asset.get("asset_ref"),
                "runtime_handoff_task": (asset.get("runtime_handoff") or {}).get("task", ""),
                "payload_keys": ", ".join(sorted(payload.keys())),
                "report_slots": ", ".join(_list_text(asset.get("report_slots"))),
            }
        )
    return rows


def build_method_card_execution_outputs(frame: pd.DataFrame, routed_methods: list[dict[str, Any]], charts: list[dict[str, Any]], *, limit: int = 80) -> dict[str, Any]:
    rows, assets = _execution_artifacts(frame, routed_methods, charts, limit=limit)
    execution_columns = [
        "execution_id",
        "method_id",
        "method_run_id",
        "executor_hint",
        "status",
        "runtime_status",
        "output_type",
        "selection_mode",
        "smart_merge_group",
        "binding_quality",
        "bound_fields",
        "semantic_route_refs",
        "report_slots",
        "evidence_refs",
        "result_ref",
        "asset_type",
        "asset_ref",
        "runtime_handoff_task",
        "cli_interpretation_enabled",
        "cli_interpretation",
        "result_summary",
        "next_step",
    ]
    asset_columns = ["execution_id", "method_id", "method_run_id", "executor_hint", "status", "runtime_status", "selection_mode", "smart_merge_group", "cli_interpretation_enabled", "asset_type", "asset_ref", "runtime_handoff_task", "payload_keys", "report_slots"]
    tables: list[dict[str, Any]] = []
    if rows:
        tables.append({"title": EXECUTION_TABLE_TITLE, "columns": execution_columns, "rows": rows})
    asset_table_rows = _asset_rows(assets)
    if asset_table_rows:
        tables.append({"title": ASSET_TABLE_TITLE, "columns": asset_columns, "rows": asset_table_rows})
    return {"tables": tables, "rows": rows, "assets": assets}


def build_method_card_execution_tables(frame: pd.DataFrame, routed_methods: list[dict[str, Any]], charts: list[dict[str, Any]], *, limit: int = 80) -> list[dict[str, Any]]:
    return list(build_method_card_execution_outputs(frame, routed_methods, charts, limit=limit).get("tables") or [])
