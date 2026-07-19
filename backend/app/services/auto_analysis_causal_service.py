from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _zh(value: str) -> str:
    return value.encode("ascii").decode("unicode_escape")


def _table(title: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    columns: list[str] = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    return {"title": title, "columns": columns, "rows": rows}


def _safe_number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(number):
        return None
    return number


def _series_column(frame: pd.DataFrame, column: str) -> pd.Series:
    if not column or column not in frame.columns:
        return pd.Series(index=frame.index, dtype="object")
    values = frame.loc[:, column]
    if isinstance(values, pd.DataFrame):
        return values.iloc[:, 0]
    return values


def _numeric_column(frame: pd.DataFrame, column: str) -> pd.Series:
    if not column or column not in frame.columns:
        return pd.Series(index=frame.index, dtype="float64")
    return pd.to_numeric(_series_column(frame, column), errors="coerce")


def _time_column(frame: pd.DataFrame, field_profiles: list[dict[str, Any]]) -> str:
    for profile in field_profiles:
        column = str(profile.get("column") or "")
        if column not in frame.columns:
            continue
        tags = {str(item) for item in list(profile.get("semantic_tags") or [])}
        if profile.get("role") == "time" or "time" in tags:
            parsed = pd.to_datetime(_series_column(frame, column), errors="coerce")
            if parsed.notna().mean() >= 0.5:
                return column
    return ""


def _candidate_drivers(frame: pd.DataFrame, selected: dict[str, Any], target: str, limit: int) -> list[str]:
    bubble = selected.get("bubble") or {}
    ordered = [
        *(selected.get("features") or []),
        bubble.get("x"),
        bubble.get("y"),
        bubble.get("size"),
    ]
    drivers: list[str] = []
    for item in ordered:
        column = str(item or "")
        if not column or column == target or column in drivers or column not in frame.columns:
            continue
        values = _numeric_column(frame, column)
        if values.notna().sum() >= 4 and values.nunique(dropna=True) >= 2:
            drivers.append(column)
        if len(drivers) >= limit:
            break
    return drivers


def _lag1_correlation(frame: pd.DataFrame, driver: str, outcome: str, time_col: str) -> tuple[float | None, int]:
    clean = pd.DataFrame({"driver": _numeric_column(frame, driver), "outcome": _numeric_column(frame, outcome)})
    if time_col and time_col in frame.columns:
        clean["time"] = pd.to_datetime(_series_column(frame, time_col), errors="coerce")
        clean = clean.dropna(subset=["time"]).sort_values("time")
    clean = clean.dropna(subset=["driver", "outcome"])
    if len(clean) < 4:
        return None, int(len(clean))
    lagged = clean["driver"].shift(1)
    aligned = pd.DataFrame({"driver_lag1": lagged, "outcome": clean["outcome"]}).dropna()
    if len(aligned) < 3 or aligned["driver_lag1"].std(ddof=0) == 0 or aligned["outcome"].std(ddof=0) == 0:
        return None, int(len(aligned))
    value = _safe_number(aligned["driver_lag1"].corr(aligned["outcome"]))
    return (round(value, 4) if value is not None else None), int(len(aligned))


def _effect_estimate(treated: pd.Series, control: pd.Series) -> float:
    return float(treated.mean()) - float(control.mean())


def _seed_for(*parts: str) -> int:
    seed = 0
    for part in parts:
        for char in str(part):
            seed = (seed * 131 + ord(char)) % (2**32 - 1)
    return seed or 17


def _bootstrap_ci(treated: pd.Series, control: pd.Series, *, seed: int, iterations: int = 80) -> tuple[float | None, float | None, int]:
    treated_values = treated.to_numpy(dtype=float)
    control_values = control.to_numpy(dtype=float)
    if len(treated_values) < 2 or len(control_values) < 2:
        return None, None, 0
    rng = np.random.default_rng(seed)
    estimates: list[float] = []
    for _ in range(iterations):
        treated_sample = rng.choice(treated_values, size=len(treated_values), replace=True)
        control_sample = rng.choice(control_values, size=len(control_values), replace=True)
        estimates.append(float(treated_sample.mean() - control_sample.mean()))
    low, high = np.percentile(np.asarray(estimates, dtype=float), [2.5, 97.5])
    return round(float(low), 4), round(float(high), 4), iterations


def _stratified_effect(frame: pd.DataFrame, *, driver: str, outcome: str, group_col: str, threshold: float) -> tuple[float | None, int, int]:
    if not group_col or group_col not in frame.columns or group_col in {driver, outcome}:
        return None, 0, 0
    clean = pd.DataFrame(
        {
            "driver": _numeric_column(frame, driver),
            "outcome": _numeric_column(frame, outcome),
            "group": _series_column(frame, group_col).astype(str),
        }
    ).dropna()
    if len(clean) < 4 or clean["group"].nunique(dropna=True) > 24:
        return None, 0, 0
    weighted_effect = 0.0
    covered = 0
    strata = 0
    for _, group_frame in clean.groupby("group", dropna=True):
        treated = group_frame[group_frame["driver"] >= threshold]["outcome"]
        control = group_frame[group_frame["driver"] < threshold]["outcome"]
        if treated.empty or control.empty:
            continue
        weight = len(group_frame)
        weighted_effect += _effect_estimate(treated, control) * weight
        covered += weight
        strata += 1
    if not covered:
        return None, 0, 0
    return round(weighted_effect / covered, 4), strata, covered


def _executor_quality(*, standardized: float, ci_low: float | None, ci_high: float | None, stratified_effect: float | None) -> str:
    ci_excludes_zero = ci_low is not None and ci_high is not None and (ci_low > 0 or ci_high < 0)
    if ci_excludes_zero and abs(standardized) >= 0.35 and stratified_effect is not None:
        return "strong_directional_screen"
    if ci_excludes_zero or abs(standardized) >= 0.25:
        return "directional_screen"
    return "weak_or_uncertain_screen"


def _comparison_row(frame: pd.DataFrame, *, driver: str, outcome: str, time_col: str, group_col: str, index: int) -> dict[str, Any] | None:
    driver_values = _numeric_column(frame, driver)
    outcome_values = _numeric_column(frame, outcome)
    clean = pd.DataFrame({"driver": driver_values, "outcome": outcome_values}).dropna()
    if len(clean) < 4 or clean["driver"].nunique(dropna=True) < 2:
        return None
    threshold = float(clean["driver"].median())
    treated = clean[clean["driver"] >= threshold]["outcome"]
    control = clean[clean["driver"] < threshold]["outcome"]
    if treated.empty or control.empty:
        return None
    treated_mean = float(treated.mean())
    control_mean = float(control.mean())
    effect = _effect_estimate(treated, control)
    pooled_std = float(clean["outcome"].std(ddof=0) or 0.0)
    standardized = effect / pooled_std if pooled_std else 0.0
    relative_lift = effect / abs(control_mean) if control_mean else None
    lag1_corr, lag_n = _lag1_correlation(frame, driver, outcome, time_col)
    ci_low, ci_high, bootstrap_iterations = _bootstrap_ci(treated, control, seed=_seed_for(driver, outcome))
    ci_excludes_zero = bool(ci_low is not None and ci_high is not None and (ci_low > 0 or ci_high < 0))
    stratified_effect, strata_count, stratified_n = _stratified_effect(frame, driver=driver, outcome=outcome, group_col=group_col, threshold=threshold)
    quality = _executor_quality(standardized=standardized, ci_low=ci_low, ci_high=ci_high, stratified_effect=stratified_effect)
    sample_score = min(20.0, len(clean) / 5.0)
    effect_score = min(30.0, abs(standardized) * 20.0)
    lag_score = min(15.0, abs(lag1_corr or 0.0) * 15.0)
    ci_score = 10.0 if ci_excludes_zero else 0.0
    control_score = 5.0 if stratified_effect is not None else 0.0
    priority_score = min(100.0, 25.0 + sample_score + effect_score + lag_score + ci_score + control_score)
    return {
        "executor_id": f"causal_light_executor_{index}",
        "driver": driver,
        "outcome": outcome,
        "design": "median_split_difference_in_means",
        "source_ref": "data:derived_enriched_frame",
        "sample_size": int(len(clean)),
        "treated_n": int(len(treated)),
        "control_n": int(len(control)),
        "driver_threshold": round(threshold, 4),
        "treated_mean": round(treated_mean, 4),
        "control_mean": round(control_mean, 4),
        "effect_estimate": round(effect, 4),
        "standardized_effect": round(standardized, 4),
        "stratified_effect_estimate": stratified_effect,
        "strata_count": strata_count,
        "stratified_observation_count": stratified_n,
        "relative_lift": round(relative_lift, 4) if relative_lift is not None else None,
        "bootstrap_ci_low": ci_low,
        "bootstrap_ci_high": ci_high,
        "bootstrap_iterations": bootstrap_iterations,
        "ci_excludes_zero": ci_excludes_zero,
        "lag1_correlation": lag1_corr,
        "lag_observation_count": lag_n,
        "group_control_hint": group_col or "no_group_field_selected",
        "executor_quality": quality,
        "priority_score": round(priority_score, 2),
        "caveat": "observational_screen_not_causal_claim",
        "next_step": "rerun with explicit treatment timing, controls, and segment holdout before making a causal claim",
    }


def build_causal_executor_tables(
    frame: pd.DataFrame,
    *,
    selected: dict[str, Any],
    field_profiles: list[dict[str, Any]],
    max_rows: int = 6,
) -> list[dict[str, Any]]:
    target = str(selected.get("target") or "")
    if not target or target not in frame.columns:
        return []
    if _numeric_column(frame, target).notna().sum() < 4:
        return []
    time_col = _time_column(frame, field_profiles)
    group_col = str(selected.get("group") or "")
    rows: list[dict[str, Any]] = []
    for index, driver in enumerate(_candidate_drivers(frame, selected, target, max_rows), start=1):
        row = _comparison_row(frame, driver=driver, outcome=target, time_col=time_col, group_col=group_col, index=index)
        if row:
            rows.append(row)
    rows.sort(key=lambda item: float(item.get("priority_score") or 0.0), reverse=True)
    if not rows:
        return []
    return [_table(_zh(r"\u56e0\u679c\u8f7b\u91cf\u6267\u884c\u7ed3\u679c"), rows[:max_rows])]
