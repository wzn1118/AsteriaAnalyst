from __future__ import annotations

import importlib
from typing import Any

import numpy as np
import pandas as pd

from app.models import StatisticRequest


class _LazyImport:
    def __init__(self, module_name: str, attr_name: str | None = None):
        self._module_name = module_name
        self._attr_name = attr_name
        self._resolved: Any | None = None

    def _resolve(self) -> Any:
        if self._resolved is None:
            module = importlib.import_module(self._module_name)
            self._resolved = getattr(module, self._attr_name) if self._attr_name else module
        return self._resolved

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self._resolve()(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._resolve(), name)


stats = _LazyImport("scipy.stats")
KMeans = _LazyImport("sklearn.cluster", "KMeans")
PCA = _LazyImport("sklearn.decomposition", "PCA")
RandomForestClassifier = _LazyImport("sklearn.ensemble", "RandomForestClassifier")
RandomForestRegressor = _LazyImport("sklearn.ensemble", "RandomForestRegressor")
permutation_importance = _LazyImport("sklearn.inspection", "permutation_importance")
ElasticNet = _LazyImport("sklearn.linear_model", "ElasticNet")
Lasso = _LazyImport("sklearn.linear_model", "Lasso")
Ridge = _LazyImport("sklearn.linear_model", "Ridge")
accuracy_score = _LazyImport("sklearn.metrics", "accuracy_score")
f1_score = _LazyImport("sklearn.metrics", "f1_score")
mean_absolute_error = _LazyImport("sklearn.metrics", "mean_absolute_error")
mean_squared_error = _LazyImport("sklearn.metrics", "mean_squared_error")
precision_score = _LazyImport("sklearn.metrics", "precision_score")
r2_score = _LazyImport("sklearn.metrics", "r2_score")
recall_score = _LazyImport("sklearn.metrics", "recall_score")
roc_auc_score = _LazyImport("sklearn.metrics", "roc_auc_score")
silhouette_score = _LazyImport("sklearn.metrics", "silhouette_score")
train_test_split = _LazyImport("sklearn.model_selection", "train_test_split")
MLPClassifier = _LazyImport("sklearn.neural_network", "MLPClassifier")
MLPRegressor = _LazyImport("sklearn.neural_network", "MLPRegressor")
StandardScaler = _LazyImport("sklearn.preprocessing", "StandardScaler")


def _statsmodels_api():
    import statsmodels.api as sm

    return sm


def _statsmodels_ols():
    from statsmodels.formula.api import ols

    return ols


def _statsmodels_diagnostic():
    from statsmodels.stats.diagnostic import acorr_ljungbox, het_breuschpagan, het_white

    return acorr_ljungbox, het_breuschpagan, het_white


def _statsmodels_pairwise_tukeyhsd():
    from statsmodels.stats.multicomp import pairwise_tukeyhsd

    return pairwise_tukeyhsd


def _statsmodels_power():
    from statsmodels.stats.power import NormalIndPower, TTestIndPower

    return NormalIndPower, TTestIndPower


def _statsmodels_proportion():
    from statsmodels.stats.proportion import confint_proportions_2indep, proportion_effectsize, proportions_ztest

    return confint_proportions_2indep, proportion_effectsize, proportions_ztest


def _statsmodels_durbin_watson():
    from statsmodels.stats.stattools import durbin_watson

    return durbin_watson


def _statsmodels_tsa():
    from statsmodels.tsa.stattools import acf, adfuller, pacf

    return acf, adfuller, pacf


SUPPORTED_ANALYSIS_TYPES = (
    "correlation",
    "pearson_correlation",
    "spearman_correlation",
    "kendall_tau",
    "partial_correlation",
    "distance_correlation",
    "point_biserial",
    "eta_squared",
    "descriptive_summary",
    "frequency_table",
    "cross_tabulation",
    "pivot_summary",
    "quantile_profile",
    "trimmed_mean",
    "winsorized_summary",
    "gini_coefficient",
    "pareto_analysis",
    "segmented_kpi_breakdown",
    "ols",
    "ridge_regression",
    "lasso_regression",
    "elastic_net",
    "robust_regression",
    "quantile_regression",
    "anova",
    "two_way_anova",
    "ancova",
    "logit",
    "random_forest",
    "neural_network",
    "deep_learning",
    "pca",
    "kmeans",
    "ttest",
    "paired_ttest",
    "one_sample_ttest",
    "z_test_mean",
    "ab_test",
    "repeated_measures_anova",
    "chi_square",
    "fisher_exact",
    "mcnemar",
    "cochran_q",
    "cmh_test",
    "cramers_v",
    "phi_coefficient",
    "theils_u",
    "goodman_kruskal_lambda",
    "cohens_kappa",
    "mann_whitney",
    "wilcoxon_signed_rank",
    "sign_test",
    "kruskal",
    "friedman",
    "mood_median",
    "ks_two_sample",
    "runs_test",
    "median_test",
    "fligner_killeen",
    "permutation_test",
    "bootstrap_ci",
    "poisson_glm",
    "normality",
    "shapiro_wilk",
    "dagostino_k2",
    "jarque_bera",
    "kolmogorov_smirnov_1samp",
    "anderson_darling",
    "breusch_pagan",
    "white_test",
    "durbin_watson",
    "moving_average",
    "autocorrelation",
    "partial_autocorrelation",
    "ljung_box",
    "adf_test",
    "tukey_hsd",
    "levene",
    "brown_forsythe",
    "bartlett",
    "welch_anova",
)


def metric(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, np.generic):
        return value.item()
    if pd.isna(value):
        return None
    return value


def quote(column_name: str) -> str:
    escaped = column_name.replace('"', '\\"')
    return f'Q("{escaped}")'


def _numeric_frame(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    numeric = frame[columns].apply(pd.to_numeric, errors="coerce")
    return numeric.dropna()


def _records(frame: pd.DataFrame, limit: int = 18) -> list[dict[str, Any]]:
    if frame.empty:
        return []
    preview = frame.head(limit).copy().where(pd.notnull(frame.head(limit)), None)
    return [
        {str(key): metric(value) for key, value in row.items()}
        for row in preview.to_dict(orient="records")
    ]


def _table(title: str, frame: pd.DataFrame) -> dict[str, Any]:
    return {
        "title": title,
        "columns": frame.columns.astype(str).tolist(),
        "rows": _records(frame),
    }


def _best_label_column(frame: pd.DataFrame, exclude: set[str] | None = None) -> str | None:
    exclude = exclude or set()
    candidates: list[tuple[int, int, float, str]] = []
    for column in frame.columns.astype(str).tolist():
        if column in exclude:
            continue
        series = frame[column]
        if pd.api.types.is_numeric_dtype(series):
            continue
        clean = series.dropna().astype(str)
        if clean.empty:
            continue
        unique = int(clean.nunique())
        if unique < 2:
            continue
        lower = column.lower()
        score = 0
        if any(
            token in lower
            for token in [
                "name",
                "title",
                "label",
                "product",
                "item",
                "sku",
                "spu",
                "brand",
                "category",
                "名称",
                "标题",
                "商品",
                "品牌",
                "品类",
            ]
        ):
            score += 6
        if unique <= min(200, max(len(frame), 1)):
            score += 2
        avg_len = float(clean.map(len).mean())
        if 2 <= avg_len <= 40:
            score += 2
        top_share = float(clean.value_counts(normalize=True).iloc[0])
        if top_share < 0.7:
            score += 1
        if score > 0:
            candidates.append((score, -unique, top_share, column))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (-item[0], item[1], item[2], item[3]))
    return candidates[0][3]


def _decision_note(result: dict[str, Any]) -> str | None:
    analysis_type = str(result.get("analysis_type", "") or "")
    metrics = result.get("metrics", {}) or {}
    p_value = metrics.get("p_value")
    decision = metrics.get("decision")

    def first_metric(*keys: str) -> Any:
        for key in keys:
            value = metrics.get(key)
            if value is not None:
                return value
        return None

    if analysis_type == "correlation":
        left = metrics.get("strongest_left")
        right = metrics.get("strongest_right")
        if left and right:
            return f"Decision cue: use {left} and {right} as a first-pass feature-screening pair, but do not treat correlation as causal evidence."

    if analysis_type in {"pearson_correlation", "spearman_correlation", "kendall_tau", "partial_correlation", "distance_correlation", "point_biserial", "eta_squared"}:
        strength = first_metric("correlation", "eta_squared")
        if isinstance(strength, (int, float)):
            if abs(float(strength)) >= 0.5 or (analysis_type == "eta_squared" and float(strength) >= 0.14):
                return "Decision cue: the effect is large enough to feature as a driver-screening signal, but it still needs causal or business validation."
            if abs(float(strength)) >= 0.3 or (analysis_type == "eta_squared" and float(strength) >= 0.06):
                return "Decision cue: the effect is moderate, so use it to prioritize follow-up comparisons rather than as a final decision rule."
        return "Decision cue: the association is weak or exploratory, so avoid making it a headline without corroborating evidence."

    if analysis_type in {"descriptive_summary", "frequency_table", "cross_tabulation", "pivot_summary", "segmented_kpi_breakdown"}:
        if analysis_type in {"frequency_table", "cross_tabulation"}:
            top_share = metrics.get("top_share") or metrics.get("largest_cell_share")
            if isinstance(top_share, (int, float)) and float(top_share) >= 0.5:
                return "Decision cue: the distribution is concentrated enough to call out dominant categories before deeper modeling."
        if analysis_type in {"pivot_summary", "segmented_kpi_breakdown"}:
            ratio = metrics.get("max_min_mean_ratio") or metrics.get("top_bottom_mean_ratio")
            if isinstance(ratio, (int, float)) and float(ratio) >= 1.5:
                return "Decision cue: segment-level KPI contrast is large enough to prioritize management follow-up by group."
        return "Decision cue: use this descriptive table as baseline evidence before escalating into hypothesis tests or model-based claims."

    if analysis_type in {"quantile_profile", "trimmed_mean", "winsorized_summary"}:
        tail_ratio = metrics.get("tail_to_median_ratio") or metrics.get("winsorized_mean_shift_pct") or metrics.get("trimmed_mean_shift_pct")
        if isinstance(tail_ratio, (int, float)) and abs(float(tail_ratio)) >= 0.15:
            return "Decision cue: the distribution has enough tail pressure to report robust summaries alongside the raw mean before making operational comparisons."
        return "Decision cue: the robust and raw summaries are close enough to use the ordinary center as a readable baseline, while still showing tail checks."

    if analysis_type == "gini_coefficient":
        gini = metrics.get("gini")
        if isinstance(gini, (int, float)) and float(gini) >= 0.45:
            return "Decision cue: contribution is concentrated, so prioritize head-item governance, risk checks, and resource allocation by contribution tier."
        return "Decision cue: contribution concentration is not extreme, so avoid over-focusing only on the head without checking mid-tail opportunities."

    if analysis_type == "pareto_analysis":
        top_share = metrics.get("top_20_share")
        if isinstance(top_share, (int, float)) and float(top_share) >= 0.8:
            return "Decision cue: the top segment explains most contribution, so report head accounts/items separately and manage long-tail coverage as a second layer."
        return "Decision cue: contribution is more distributed than a strict Pareto pattern, so balance head optimization with broader portfolio review."

    if analysis_type in {"cramers_v", "phi_coefficient", "theils_u", "goodman_kruskal_lambda"}:
        strength = first_metric("cramers_v", "phi", "theils_u", "lambda")
        if isinstance(strength, (int, float)):
            if abs(float(strength)) >= 0.3:
                return "Decision cue: the categorical association is strong enough to prioritize combination-level drill-downs, but it is still not causal evidence."
            return "Decision cue: the categorical association is measurable but modest, so use it as a segmentation hint rather than a standalone decision rule."
        return "Decision cue: treat this categorical association as descriptive evidence and pair it with business context before operationalizing it."

    if analysis_type in {"mcnemar", "cochran_q", "cmh_test"}:
        if decision == "significant" or (isinstance(p_value, (int, float)) and p_value < 0.05):
            return "Decision cue: the categorical shift remains statistically meaningful, so use it to prioritize paired or stratified follow-up checks."
        if isinstance(p_value, (int, float)):
            return "Decision cue: the categorical shift evidence is limited, so report it as a boundary check rather than a main operational claim."

    if analysis_type == "cohens_kappa":
        kappa = metrics.get("kappa")
        if isinstance(kappa, (int, float)):
            if float(kappa) >= 0.6:
                return "Decision cue: agreement is strong enough to support consistent labeling, while still requiring adjudication for high-risk cases."
            if float(kappa) >= 0.4:
                return "Decision cue: agreement is usable but not definitive, so sample disagreements before relying on this label process."
        return "Decision cue: agreement is weak or unavailable, so treat labels as a process-quality risk before using them for downstream decisions."

    if analysis_type in {"ttest", "paired_ttest", "one_sample_ttest", "z_test_mean", "anova", "two_way_anova", "ancova", "welch_anova", "mann_whitney", "wilcoxon_signed_rank", "sign_test", "kruskal", "median_test", "chi_square", "fisher_exact", "tukey_hsd"}:
        if decision == "significant" or (isinstance(p_value, (int, float)) and p_value < 0.05):
            return "Decision cue: the group difference is statistically meaningful enough to justify a follow-up drill-down or post-hoc comparison."
        if isinstance(p_value, (int, float)):
            return "Decision cue: the evidence for a stable group difference is limited, so avoid over-committing without more signal."

    if analysis_type in {"repeated_measures_anova", "friedman"}:
        if decision == "significant" or (isinstance(p_value, (int, float)) and p_value < 0.05):
            return "Decision cue: the within-subject condition effect is meaningful enough to inspect pairwise condition changes and repeated-measure drivers."
        if isinstance(p_value, (int, float)):
            return "Decision cue: repeated-measure differences are limited, so avoid treating condition order as a confirmed driver without more evidence."

    if analysis_type in {"mood_median", "ks_two_sample", "permutation_test"}:
        if decision == "significant" or (isinstance(p_value, (int, float)) and p_value < 0.05):
            return "Decision cue: this robust distribution check supports a real group difference, so use it as a safeguard when parametric assumptions are weak."
        if isinstance(p_value, (int, float)):
            return "Decision cue: the robust test does not show a strong group difference, so keep the result as a boundary condition rather than a headline claim."

    if analysis_type == "bootstrap_ci":
        ci_low = metrics.get("ci_low")
        ci_high = metrics.get("ci_high")
        if isinstance(ci_low, (int, float)) and isinstance(ci_high, (int, float)) and float(ci_low) <= 0 <= float(ci_high):
            return "Decision cue: the bootstrap interval crosses zero, so avoid presenting the average as a reliable positive or negative effect."
        return "Decision cue: the bootstrap interval is away from zero, so report the interval alongside the point estimate as uncertainty evidence."

    if analysis_type == "runs_test":
        if decision == "non_random_sequence" or (isinstance(p_value, (int, float)) and p_value < 0.05):
            return "Decision cue: ordering looks non-random, so inspect time, process, or batching effects before treating rows as exchangeable."
        if isinstance(p_value, (int, float)):
            return "Decision cue: no strong run-pattern signal was detected, but pair this with trend or autocorrelation checks when row order matters."

    if analysis_type in {"levene", "brown_forsythe", "bartlett", "fligner_killeen"}:
        if decision == "variance_heterogeneous" or (isinstance(p_value, (int, float)) and p_value < 0.05):
            return "Decision cue: variance looks uneven, so prefer Welch ANOVA, robust standard errors, or a nonparametric route before making a group-comparison claim."
        if isinstance(p_value, (int, float)):
            return "Decision cue: variance equality is not strongly contradicted, but still pair this with normality and sample-size checks before using equal-variance methods."

    if analysis_type in {"ols", "logit", "poisson_glm"}:
        return "Decision cue: prioritize the strongest stable coefficients as driver-analysis candidates, and keep low-signal terms out of the main story."

    if analysis_type in {"ridge_regression", "lasso_regression", "elastic_net"}:
        strongest_term = metrics.get("strongest_term")
        nonzero = metrics.get("nonzero_terms")
        if strongest_term:
            return f"Decision cue: {strongest_term} remains the strongest regularized driver; use regularization to separate stable signal from multicollinearity noise."
        if isinstance(nonzero, (int, float)) and int(nonzero) == 0:
            return "Decision cue: regularization shrank all feature signals heavily, so avoid presenting a driver story without more evidence or weaker penalty."
        return "Decision cue: compare regularized coefficients with OLS before naming durable drivers in the management report."

    if analysis_type == "robust_regression":
        strongest_term = metrics.get("strongest_term")
        return f"Decision cue: robust regression reduces outlier leverage; treat {strongest_term or 'the stable non-outlier terms'} as safer driver candidates than raw OLS spikes."

    if analysis_type == "quantile_regression":
        quantile_value = metrics.get("quantile")
        if isinstance(quantile_value, (int, float)) and float(quantile_value) != 0.5:
            return "Decision cue: effects differ at this target quantile, so tailor actions to the low-tail or high-tail segment rather than only the average case."
        return "Decision cue: median effects are robust to tails; compare them with OLS before claiming an average-only driver."

    if analysis_type in {"breusch_pagan", "white_test"}:
        if decision == "heteroskedastic" or (isinstance(p_value, (int, float)) and p_value < 0.05):
            return "Decision cue: residual variance is uneven, so pair regression findings with robust standard errors or a transformation before reporting coefficient confidence."
        if isinstance(p_value, (int, float)):
            return "Decision cue: this diagnostic does not strongly contradict homoskedasticity, but keep residual plots and outlier checks in the evidence chain."

    if analysis_type == "durbin_watson":
        statistic = metrics.get("durbin_watson_statistic")
        if isinstance(statistic, (int, float)) and (float(statistic) < 1.5 or float(statistic) > 2.5):
            return "Decision cue: residual autocorrelation may distort standard errors, so validate the regression with time-aware or autocorrelation-robust methods."
        return "Decision cue: residual autocorrelation is not prominent by this diagnostic, so ordinary regression summaries are more defensible."

    if analysis_type in {"random_forest", "neural_network", "deep_learning"}:
        return "Decision cue: prioritize the most important features as first-pass driver candidates, but validate them with business context before turning them into strategy."

    if analysis_type == "pca":
        return "Decision cue: use the top-loading variables to name the latent dimensions before operationalizing them in a dashboard or model."

    if analysis_type == "kmeans":
        silhouette = metrics.get("silhouette")
        if isinstance(silhouette, (int, float)):
            if silhouette >= 0.35:
                return "Decision cue: the segments are separated enough to support a first clustering-based segmentation pass."
            return "Decision cue: the segments are still soft, so treat clustering as exploratory rather than a final segmentation schema."
        return "Decision cue: use cluster size and center contrast to decide whether segmentation is worth operationalizing."

    if analysis_type == "normality":
        if isinstance(p_value, (int, float)) and p_value < 0.05:
            return "Decision cue: normality looks weak, so prefer robust or nonparametric methods in the next step."
        if isinstance(p_value, (int, float)):
            return "Decision cue: normality is not strongly contradicted, so parametric methods remain plausible."

    if analysis_type in {"shapiro_wilk", "dagostino_k2", "jarque_bera", "kolmogorov_smirnov_1samp", "anderson_darling"}:
        if decision == "reject_normality" or (isinstance(p_value, (int, float)) and p_value < 0.05):
            return "Decision cue: distribution diagnostics raise normality concerns, so prefer robust, transformed, or nonparametric follow-up before making parametric claims."
        if decision == "fail_to_reject_normality" or isinstance(p_value, (int, float)):
            return "Decision cue: this diagnostic does not strongly contradict normality, but still pair it with sample-size, outlier, and visual checks."
        return "Decision cue: use this distribution diagnostic as assumption evidence rather than as a business conclusion by itself."

    if analysis_type == "moving_average":
        trend_direction = metrics.get("trend_direction")
        if trend_direction == "up":
            return "Decision cue: the smoothed trend is rising, so separate sustained growth from short-term spikes before committing resources."
        if trend_direction == "down":
            return "Decision cue: the smoothed trend is falling, so prioritize root-cause checks and intervention timing before extrapolating the decline."
        return "Decision cue: the smoothed trend is relatively flat, so focus the report on volatility, segments, or external events rather than headline trend."

    if analysis_type in {"autocorrelation", "partial_autocorrelation"}:
        strongest_lag = metrics.get("strongest_lag")
        strongest_value = metrics.get("strongest_correlation")
        if isinstance(strongest_lag, (int, float)) and isinstance(strongest_value, (int, float)) and abs(float(strongest_value)) >= 0.3:
            return f"Decision cue: lag {int(strongest_lag)} carries meaningful serial signal, so time-aware features or lagged comparisons should enter the next model."
        return "Decision cue: serial signal is modest, so avoid overclaiming seasonality or lag effects without a stronger business calendar explanation."

    if analysis_type == "ljung_box":
        if decision == "serial_correlation" or (isinstance(p_value, (int, float)) and p_value < 0.05):
            return "Decision cue: the series is not white noise, so trend, lag, or seasonality structure should be modeled before treating observations as independent."
        if isinstance(p_value, (int, float)):
            return "Decision cue: white-noise behavior is not strongly contradicted at the tested lags, so simple monitoring may be acceptable for this metric."

    if analysis_type == "adf_test":
        if decision == "stationary" or (isinstance(p_value, (int, float)) and p_value < 0.05):
            return "Decision cue: stationarity is plausible, so level-based monitoring and autoregressive summaries are more defensible."
        if isinstance(p_value, (int, float)):
            return "Decision cue: unit-root risk remains, so difference the metric or model trend before making forecast or control-chart claims."

    if analysis_type == "ab_test":
        if decision == "significant" or (isinstance(p_value, (int, float)) and p_value < 0.05):
            return "Decision cue: the lift is strong enough to consider rollout prioritization, subject to effect size and business cost."
        return "Decision cue: hold off on rollout and treat this as directional until more evidence accumulates."

    return None


def _enhance_result_narrative(result: dict[str, Any]) -> dict[str, Any]:
    narrative = str(result.get("narrative", "") or "").strip()
    note = _decision_note(result)
    if note and note not in narrative:
        result["narrative"] = f"{narrative} {note}".strip()
    return result


def _relative_change(baseline: float, candidate: float) -> float | None:
    if baseline == 0:
        return None
    return float((candidate - baseline) / abs(baseline))


def _scipy_alternative(hypothesis: str) -> str:
    mapping = {
        "two-sided": "two-sided",
        "larger": "greater",
        "smaller": "less",
    }
    return mapping.get(hypothesis, "two-sided")


def _confidence_level(alpha: float) -> float:
    return round((1 - alpha) * 100, 2)


def _two_group_frame(frame: pd.DataFrame, request: StatisticRequest) -> tuple[pd.DataFrame, str, str]:
    if not request.target or not request.group_column:
        raise ValueError("This analysis requires both a target column and a group column.")

    clean = frame[[request.target, request.group_column]].copy().dropna()
    if clean.empty:
        raise ValueError("No complete observations remain after removing nulls.")

    clean[request.group_column] = clean[request.group_column].astype(str)
    available = clean[request.group_column].unique().tolist()
    if len(available) < 2:
        raise ValueError("At least two groups are required.")

    group_a = request.group_a or available[0]
    group_b = request.group_b or available[1]
    selected = clean.loc[clean[request.group_column].isin([group_a, group_b])].copy()
    if selected[request.group_column].nunique() != 2:
        raise ValueError("Both comparison groups must be present in the dataset.")
    return selected, group_a, group_b


def _paired_numeric_frame(frame: pd.DataFrame, request: StatisticRequest, *, test_name: str) -> tuple[pd.DataFrame, str, str]:
    if not request.target:
        raise ValueError(f"{test_name} requires a target column.")
    paired_feature = next((feature for feature in request.features if feature != request.target), None)
    if not paired_feature:
        raise ValueError(f"{test_name} requires a second numeric field in features.")
    clean = frame[[request.target, paired_feature]].apply(pd.to_numeric, errors="coerce").dropna()
    if len(clean) < 2:
        raise ValueError(f"{test_name} needs at least two complete paired observations.")
    return clean, request.target, paired_feature


def _repeated_numeric_frame(frame: pd.DataFrame, request: StatisticRequest, *, test_name: str) -> tuple[pd.DataFrame, list[str]]:
    target_columns = [request.target] if request.target else []
    columns = list(dict.fromkeys([*target_columns, *request.features]))
    if len(columns) < 3:
        raise ValueError(f"{test_name} requires at least three repeated numeric columns.")
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{test_name} fields are missing from the dataset: {', '.join(missing)}.")
    clean = frame[columns].apply(pd.to_numeric, errors="coerce").dropna()
    if len(clean) < 3:
        raise ValueError(f"{test_name} needs at least three complete subjects.")
    varying = [column for column in columns if clean[column].nunique(dropna=True) > 1]
    if len(varying) < 2:
        raise ValueError(f"{test_name} requires variation in at least two repeated columns.")
    return clean, columns


def _paired_categorical_frame(
    frame: pd.DataFrame,
    request: StatisticRequest,
    *,
    test_name: str,
    feature_error: str = "a second categorical field in features",
) -> tuple[pd.DataFrame, str, str]:
    if not request.target:
        raise ValueError(f"{test_name} requires a target column.")
    paired_feature = next((feature for feature in request.features if feature != request.target), None)
    if not paired_feature:
        raise ValueError(f"{test_name} requires {feature_error}.")
    clean = _categorical_frame(frame, [request.target, paired_feature])
    if len(clean) < 2:
        raise ValueError(f"{test_name} needs at least two complete paired observations.")
    return clean, request.target, paired_feature


def _binary_category_labels(series: pd.Series, *, column: str) -> list[str]:
    clean = series.dropna()
    if clean.empty:
        raise ValueError(f"{column} contains no usable observations.")
    labels = sorted(clean.astype(str).unique().tolist(), key=str)
    if len(labels) != 2:
        raise ValueError(f"{column} must contain exactly two binary categories.")
    return labels


def _binary_indicator_series(series: pd.Series, *, column: str) -> tuple[pd.Series, str]:
    clean = series.dropna()
    if clean.empty:
        raise ValueError(f"{column} contains no usable observations.")
    if pd.api.types.is_bool_dtype(clean):
        return clean.astype(int), "True"
    numeric = pd.to_numeric(clean, errors="coerce")
    if numeric.notna().all():
        unique_values = sorted(pd.Series(numeric).dropna().unique().tolist())
        if set(unique_values).issubset({0.0, 1.0}) and unique_values:
            return numeric.astype(int), "1"
    labels = _binary_category_labels(clean, column=column)
    positive_label = labels[-1]
    return clean.astype(str).map({labels[0]: 0, positive_label: 1}).astype(int), positive_label


def _kappa_strength_label(value: float | None) -> str:
    if value is None or not np.isfinite(value):
        return "not_available"
    if value >= 0.81:
        return "almost_perfect"
    if value >= 0.61:
        return "substantial"
    if value >= 0.41:
        return "moderate"
    if value >= 0.21:
        return "fair"
    if value >= 0.01:
        return "slight"
    return "poor"


def _binary_metric_series(series: pd.Series, success_value: str | int | float | bool | None) -> tuple[pd.Series, str]:
    clean = series.dropna()
    if clean.empty:
        raise ValueError("Binary metric column contains no usable observations.")

    if pd.api.types.is_bool_dtype(clean):
        return clean.astype(int), "boolean metric"

    numeric = pd.to_numeric(clean, errors="coerce")
    if numeric.notna().all():
        unique_values = sorted(pd.Series(numeric).dropna().unique().tolist())
        if set(unique_values).issubset({0.0, 1.0}):
            return numeric.astype(int), "0/1 metric"
        if success_value is None and len(unique_values) == 2:
            inferred_success = unique_values[-1]
            return numeric.eq(inferred_success).astype(int), f"inferred success value {inferred_success}"
        if success_value is not None:
            success_numeric = float(success_value)
            return numeric.eq(success_numeric).astype(int), f"success value {success_numeric}"

    if success_value is not None:
        return clean.astype(str).eq(str(success_value)).astype(int), f"success value {success_value}"

    raise ValueError(
        "Binary A/B tests need a boolean/0-1 metric, or an explicit success_value for categorical outcomes."
    )


def _categorical_frame(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    clean = frame[columns].copy().dropna()
    for column in columns:
        clean[column] = clean[column].astype(str)
    return clean


def _contingency_table(frame: pd.DataFrame, left: str, right: str) -> pd.DataFrame:
    clean = _categorical_frame(frame, [left, right])
    if clean.empty:
        raise ValueError("No complete observations remain for the requested categorical test.")
    table = pd.crosstab(clean[left], clean[right])
    if table.empty:
        raise ValueError("Could not build a valid contingency table.")
    return table


def _categorical_association_table(frame: pd.DataFrame, request: StatisticRequest, *, test_name: str) -> pd.DataFrame:
    if not request.target or not request.group_column:
        raise ValueError(f"{test_name} requires two categorical columns: target and group_column.")
    table = _contingency_table(frame, request.group_column, request.target)
    if table.shape[0] < 2 or table.shape[1] < 2:
        raise ValueError(f"{test_name} requires at least two categories in each selected column.")
    return table


def _contingency_records(table: pd.DataFrame, *, left_label: str, right_label: str) -> list[dict[str, Any]]:
    return [
        {
            left_label: str(row_label),
            right_label: str(col_label),
            "count": int(table.loc[row_label, col_label]),
        }
        for row_label in table.index
        for col_label in table.columns
    ]


def _contingency_table_view(table: pd.DataFrame, index_name: str) -> pd.DataFrame:
    frame = table.reset_index()
    frame = frame.rename(columns={frame.columns[0]: index_name})
    return frame


def _association_strength_label(value: float | None) -> str:
    if value is None or not np.isfinite(value):
        return "not_available"
    magnitude = abs(float(value))
    if magnitude >= 0.5:
        return "strong"
    if magnitude >= 0.3:
        return "moderate"
    if magnitude >= 0.1:
        return "weak"
    return "very_weak"


def _entropy_from_counts(counts: np.ndarray | list[float]) -> float:
    values = np.asarray(counts, dtype=float)
    total = float(values.sum())
    if total <= 0:
        return 0.0
    probabilities = values[values > 0] / total
    return float(-np.sum(probabilities * np.log2(probabilities)))


def _theils_u_from_contingency(table: pd.DataFrame) -> tuple[float, float, float]:
    observed = table.to_numpy(dtype=float)
    n = float(observed.sum())
    outcome_entropy = _entropy_from_counts(observed.sum(axis=0))
    predictor_weights = observed.sum(axis=1) / n
    conditional_entropy = float(
        sum(
            weight * _entropy_from_counts(observed[row_index, :])
            for row_index, weight in enumerate(predictor_weights)
            if weight > 0
        )
    )
    if outcome_entropy <= 0:
        raise ValueError("Theil's U requires at least two outcome categories with non-zero counts.")
    theils_u = max(0.0, min(1.0, (outcome_entropy - conditional_entropy) / outcome_entropy))
    return float(theils_u), float(outcome_entropy), float(conditional_entropy)


def _lambda_from_contingency(table: pd.DataFrame) -> tuple[float, float, float]:
    observed = table.to_numpy(dtype=float)
    n = float(observed.sum())
    errors_without_predictor = n - float(observed.sum(axis=0).max())
    errors_with_predictor = float(sum(row.sum() - row.max() for row in observed))
    if errors_without_predictor <= 0:
        raise ValueError("Goodman-Kruskal Lambda requires at least two outcome categories with non-zero counts.")
    lambda_value = max(0.0, min(1.0, (errors_without_predictor - errors_with_predictor) / errors_without_predictor))
    return float(lambda_value), float(errors_without_predictor), float(errors_with_predictor)


def _auto_supervised_target(frame: pd.DataFrame) -> str:
    numeric_candidates = frame.select_dtypes(include=["number", "bool"]).columns.astype(str).tolist()
    if not numeric_candidates:
        raise ValueError("当前数据中没有可用于监督学习的目标字段。")
    return numeric_candidates[0]


def _infer_metric_type(series: pd.Series, requested: str) -> str:
    if requested in {"continuous", "binary"}:
        return requested
    clean = series.dropna()
    if clean.empty:
        raise ValueError("目标字段没有可用样本。")
    if pd.api.types.is_bool_dtype(clean):
        return "binary"
    numeric = pd.to_numeric(clean, errors="coerce")
    if numeric.notna().all():
        unique_values = sorted(pd.Series(numeric).dropna().unique().tolist())
        if set(unique_values).issubset({0.0, 1.0}) or len(unique_values) == 2:
            return "binary"
        return "continuous"
    if clean.astype(str).nunique() == 2:
        return "binary"
    return "continuous"


def _normalize_supervised_feature_frame(features: pd.DataFrame) -> pd.DataFrame:
    normalized = features.copy()
    for column in normalized.columns:
        series = normalized[column]
        if pd.api.types.is_datetime64_any_dtype(series):
            normalized[column] = series.astype("int64") / 1_000_000_000
            continue
        if pd.api.types.is_datetime64tz_dtype(series):
            normalized[column] = series.dt.tz_convert("UTC").astype("int64") / 1_000_000_000
            continue
        if series.dtype == object:
            parsed = pd.to_datetime(series, errors="coerce", utc=True)
            if parsed.notna().mean() >= 0.8:
                normalized[column] = parsed.astype("int64") / 1_000_000_000
    return normalized


def _prepare_supervised_learning_frame(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    target = request.target or _auto_supervised_target(frame)
    if target not in frame.columns:
        raise ValueError(f"目标字段 `{target}` 不存在。")

    features = request.features or [column for column in frame.columns.astype(str).tolist() if column != target][:8]
    features = [column for column in features if column in frame.columns and column != target]
    if len(features) < 2:
        raise ValueError("监督学习至少需要两个特征字段。")

    working = frame[[target, *features]].copy().dropna()
    if len(working) < 30:
        raise ValueError("监督学习需要至少 30 条完整样本。")

    metric_type = _infer_metric_type(working[target], request.metric_type)
    feature_frame = _normalize_supervised_feature_frame(working[features])
    x_raw = pd.get_dummies(feature_frame, dummy_na=False)
    if x_raw.shape[1] < 2:
        raise ValueError("特征展开后维度不足，无法稳定训练模型。")

    if metric_type == "binary":
        target_series = working[target]
        if pd.api.types.is_bool_dtype(target_series):
            y = target_series.astype(int)
            target_labels = ["0", "1"]
        else:
            numeric = pd.to_numeric(target_series, errors="coerce")
            if numeric.notna().all():
                unique_values = sorted(pd.Series(numeric).dropna().unique().tolist())
                if len(unique_values) != 2:
                    raise ValueError("二分类目标必须恰好有两个类别。")
                positive = unique_values[-1]
                y = numeric.eq(positive).astype(int)
                target_labels = [str(unique_values[0]), str(unique_values[1])]
            else:
                categories = target_series.astype(str)
                uniques = sorted(categories.unique().tolist())
                if len(uniques) != 2:
                    raise ValueError("二分类目标必须恰好有两个类别。")
                positive = uniques[-1]
                y = categories.eq(positive).astype(int)
                target_labels = uniques
    else:
        y = pd.to_numeric(working[target], errors="coerce")
        if y.isna().any():
            raise ValueError("连续目标字段无法稳定转成数值。")
        target_labels = []

    stratify = y if metric_type == "binary" and int(pd.Series(y).value_counts().min()) >= 2 else None
    x_train, x_test, y_train, y_test = train_test_split(
        x_raw,
        y,
        test_size=0.25,
        random_state=42,
        stratify=stratify,
    )
    return {
        "target": target,
        "features": features,
        "metric_type": metric_type,
        "x_raw": x_raw,
        "x_train": x_train,
        "x_test": x_test,
        "y_train": y_train,
        "y_test": y_test,
        "target_labels": target_labels,
    }


def _feature_importance_rows(feature_names: list[str], scores: np.ndarray | list[float], limit: int = 12) -> pd.DataFrame:
    table = pd.DataFrame({"feature": feature_names, "importance": scores})
    table = table.sort_values("importance", ascending=False).head(limit).reset_index(drop=True)
    return table.round(5)


def _supervised_metric_table(metrics: dict[str, Any]) -> pd.DataFrame:
    rows = [{"metric": key, "value": value} for key, value in metrics.items()]
    return pd.DataFrame(rows)


def run_statistical_analysis(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    if request.analysis_type == "correlation":
        return _enhance_result_narrative(run_correlation(frame, request))
    if request.analysis_type == "pearson_correlation":
        return _enhance_result_narrative(run_bivariate_correlation(frame, request, method="pearson"))
    if request.analysis_type == "spearman_correlation":
        return _enhance_result_narrative(run_bivariate_correlation(frame, request, method="spearman"))
    if request.analysis_type == "kendall_tau":
        return _enhance_result_narrative(run_bivariate_correlation(frame, request, method="kendall"))
    if request.analysis_type == "partial_correlation":
        return _enhance_result_narrative(run_partial_correlation(frame, request))
    if request.analysis_type == "distance_correlation":
        return _enhance_result_narrative(run_distance_correlation(frame, request))
    if request.analysis_type == "point_biserial":
        return _enhance_result_narrative(run_point_biserial(frame, request))
    if request.analysis_type == "eta_squared":
        return _enhance_result_narrative(run_eta_squared(frame, request))
    if request.analysis_type == "descriptive_summary":
        return _enhance_result_narrative(run_descriptive_summary(frame, request))
    if request.analysis_type == "frequency_table":
        return _enhance_result_narrative(run_frequency_table(frame, request))
    if request.analysis_type == "cross_tabulation":
        return _enhance_result_narrative(run_cross_tabulation(frame, request))
    if request.analysis_type == "pivot_summary":
        return _enhance_result_narrative(run_pivot_summary(frame, request))
    if request.analysis_type == "quantile_profile":
        return _enhance_result_narrative(run_quantile_profile(frame, request))
    if request.analysis_type == "trimmed_mean":
        return _enhance_result_narrative(run_trimmed_mean(frame, request))
    if request.analysis_type == "winsorized_summary":
        return _enhance_result_narrative(run_winsorized_summary(frame, request))
    if request.analysis_type == "gini_coefficient":
        return _enhance_result_narrative(run_gini_coefficient(frame, request))
    if request.analysis_type == "pareto_analysis":
        return _enhance_result_narrative(run_pareto_analysis(frame, request))
    if request.analysis_type == "segmented_kpi_breakdown":
        return _enhance_result_narrative(run_segmented_kpi_breakdown(frame, request))
    if request.analysis_type == "ols":
        return _enhance_result_narrative(run_ols(frame, request))
    if request.analysis_type == "ridge_regression":
        return _enhance_result_narrative(run_regularized_regression(frame, request, method="ridge"))
    if request.analysis_type == "lasso_regression":
        return _enhance_result_narrative(run_regularized_regression(frame, request, method="lasso"))
    if request.analysis_type == "elastic_net":
        return _enhance_result_narrative(run_regularized_regression(frame, request, method="elastic_net"))
    if request.analysis_type == "robust_regression":
        return _enhance_result_narrative(run_robust_regression(frame, request))
    if request.analysis_type == "quantile_regression":
        return _enhance_result_narrative(run_quantile_regression(frame, request))
    if request.analysis_type == "breusch_pagan":
        return _enhance_result_narrative(run_breusch_pagan(frame, request))
    if request.analysis_type == "white_test":
        return _enhance_result_narrative(run_white_test(frame, request))
    if request.analysis_type == "durbin_watson":
        return _enhance_result_narrative(run_durbin_watson(frame, request))
    if request.analysis_type == "anova":
        return _enhance_result_narrative(run_anova(frame, request))
    if request.analysis_type == "two_way_anova":
        return _enhance_result_narrative(run_two_way_anova(frame, request))
    if request.analysis_type == "ancova":
        return _enhance_result_narrative(run_ancova(frame, request))
    if request.analysis_type == "logit":
        return _enhance_result_narrative(run_logit(frame, request))
    if request.analysis_type == "random_forest":
        return _enhance_result_narrative(run_random_forest(frame, request))
    if request.analysis_type == "neural_network":
        return _enhance_result_narrative(run_neural_network(frame, request))
    if request.analysis_type == "deep_learning":
        return _enhance_result_narrative(run_deep_learning(frame, request))
    if request.analysis_type == "pca":
        return _enhance_result_narrative(run_pca(frame, request))
    if request.analysis_type == "kmeans":
        return _enhance_result_narrative(run_kmeans(frame, request))
    if request.analysis_type == "ttest":
        return _enhance_result_narrative(run_ttest(frame, request))
    if request.analysis_type == "paired_ttest":
        return _enhance_result_narrative(run_paired_ttest(frame, request))
    if request.analysis_type == "one_sample_ttest":
        return _enhance_result_narrative(run_one_sample_ttest(frame, request))
    if request.analysis_type == "z_test_mean":
        return _enhance_result_narrative(run_z_test_mean(frame, request))
    if request.analysis_type == "ab_test":
        return _enhance_result_narrative(run_ab_test(frame, request))
    if request.analysis_type == "repeated_measures_anova":
        return _enhance_result_narrative(run_repeated_measures_anova(frame, request))
    if request.analysis_type == "chi_square":
        return _enhance_result_narrative(run_chi_square(frame, request))
    if request.analysis_type == "fisher_exact":
        return _enhance_result_narrative(run_fisher_exact(frame, request))
    if request.analysis_type == "mcnemar":
        return _enhance_result_narrative(run_mcnemar(frame, request))
    if request.analysis_type == "cochran_q":
        return _enhance_result_narrative(run_cochran_q(frame, request))
    if request.analysis_type == "cmh_test":
        return _enhance_result_narrative(run_cmh_test(frame, request))
    if request.analysis_type == "cramers_v":
        return _enhance_result_narrative(run_cramers_v(frame, request))
    if request.analysis_type == "phi_coefficient":
        return _enhance_result_narrative(run_phi_coefficient(frame, request))
    if request.analysis_type == "theils_u":
        return _enhance_result_narrative(run_theils_u(frame, request))
    if request.analysis_type == "goodman_kruskal_lambda":
        return _enhance_result_narrative(run_goodman_kruskal_lambda(frame, request))
    if request.analysis_type == "cohens_kappa":
        return _enhance_result_narrative(run_cohens_kappa(frame, request))
    if request.analysis_type == "mann_whitney":
        return _enhance_result_narrative(run_mann_whitney(frame, request))
    if request.analysis_type == "wilcoxon_signed_rank":
        return _enhance_result_narrative(run_wilcoxon_signed_rank(frame, request))
    if request.analysis_type == "sign_test":
        return _enhance_result_narrative(run_sign_test(frame, request))
    if request.analysis_type == "kruskal":
        return _enhance_result_narrative(run_kruskal(frame, request))
    if request.analysis_type == "friedman":
        return _enhance_result_narrative(run_friedman(frame, request))
    if request.analysis_type == "mood_median":
        return _enhance_result_narrative(run_mood_median(frame, request))
    if request.analysis_type == "ks_two_sample":
        return _enhance_result_narrative(run_ks_two_sample(frame, request))
    if request.analysis_type == "runs_test":
        return _enhance_result_narrative(run_runs_test(frame, request))
    if request.analysis_type == "median_test":
        return _enhance_result_narrative(run_median_test(frame, request))
    if request.analysis_type == "fligner_killeen":
        return _enhance_result_narrative(run_fligner_killeen(frame, request))
    if request.analysis_type == "permutation_test":
        return _enhance_result_narrative(run_permutation_test(frame, request))
    if request.analysis_type == "bootstrap_ci":
        return _enhance_result_narrative(run_bootstrap_ci(frame, request))
    if request.analysis_type == "poisson_glm":
        return _enhance_result_narrative(run_poisson_glm(frame, request))
    if request.analysis_type == "normality":
        return _enhance_result_narrative(run_normality(frame, request))
    if request.analysis_type == "shapiro_wilk":
        return _enhance_result_narrative(run_shapiro_wilk(frame, request))
    if request.analysis_type == "dagostino_k2":
        return _enhance_result_narrative(run_dagostino_k2(frame, request))
    if request.analysis_type == "jarque_bera":
        return _enhance_result_narrative(run_jarque_bera(frame, request))
    if request.analysis_type == "kolmogorov_smirnov_1samp":
        return _enhance_result_narrative(run_kolmogorov_smirnov_1samp(frame, request))
    if request.analysis_type == "anderson_darling":
        return _enhance_result_narrative(run_anderson_darling(frame, request))
    if request.analysis_type == "moving_average":
        return _enhance_result_narrative(run_moving_average(frame, request))
    if request.analysis_type == "autocorrelation":
        return _enhance_result_narrative(run_autocorrelation(frame, request))
    if request.analysis_type == "partial_autocorrelation":
        return _enhance_result_narrative(run_partial_autocorrelation(frame, request))
    if request.analysis_type == "ljung_box":
        return _enhance_result_narrative(run_ljung_box(frame, request))
    if request.analysis_type == "adf_test":
        return _enhance_result_narrative(run_adf_test(frame, request))
    if request.analysis_type == "tukey_hsd":
        return _enhance_result_narrative(run_tukey_hsd(frame, request))
    if request.analysis_type == "levene":
        return _enhance_result_narrative(run_variance_homogeneity(frame, request, method="levene"))
    if request.analysis_type == "brown_forsythe":
        return _enhance_result_narrative(run_variance_homogeneity(frame, request, method="brown_forsythe"))
    if request.analysis_type == "bartlett":
        return _enhance_result_narrative(run_variance_homogeneity(frame, request, method="bartlett"))
    if request.analysis_type == "welch_anova":
        return _enhance_result_narrative(run_welch_anova(frame, request))
    raise ValueError(f"Unsupported analysis type: {request.analysis_type}")


def run_correlation(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    columns = request.features or frame.select_dtypes(include=["number", "bool"]).columns[:8].tolist()
    if len(columns) < 2:
        raise ValueError("Correlation analysis needs at least two numeric columns.")

    numeric = _numeric_frame(frame, columns)
    corr = numeric.corr().round(4)
    absolute_values = corr.where(~np.eye(len(corr), dtype=bool)).abs().stack()
    strongest = float(absolute_values.max()) if not absolute_values.empty else 0.0
    pair_rows: list[dict[str, Any]] = []
    for left_index, left in enumerate(corr.columns):
        for right in corr.columns[left_index + 1 :]:
            pair_frame = numeric[[left, right]].dropna()
            value = float(corr.loc[left, right])
            p_value: float | None = None
            sample_size = int(pair_frame.shape[0])
            if sample_size >= 3:
                try:
                    _, p_raw = stats.pearsonr(pair_frame[left], pair_frame[right])
                    p_value = float(p_raw)
                except Exception:
                    p_value = None
            pair_rows.append(
                {
                    "left": str(left),
                    "right": str(right),
                    "correlation": value,
                    "abs_correlation": abs(value),
                    "p_value": p_value,
                    "sample_size": sample_size,
                    "direction": "positive" if value >= 0 else "negative",
                }
            )
    pair_rows.sort(key=lambda row: row["abs_correlation"], reverse=True)
    strongest_pair = pair_rows[0] if pair_rows else None
    strength_band = (
        "strong"
        if strongest >= 0.7
        else "moderate"
        if strongest >= 0.4
        else "weak"
    )

    return {
        "analysis_type": "correlation",
        "title": "Correlation Matrix",
        "narrative": (
            f"The strongest pair is {strongest_pair['left']} vs {strongest_pair['right']} "
            f"with correlation {strongest_pair['correlation']:.3f} "
            f"({'p-value ' + format(strongest_pair['p_value'], '.4g') + ', ' if strongest_pair['p_value'] is not None else ''}{strength_band}, {strongest_pair['direction']}). "
            f"Use the top-ranked pairs as feature-screening candidates, but treat correlation as association rather than causation."
            if strongest_pair
            else "No usable pairwise correlation was identified."
        ),
        "metrics": {
            "column_count": len(columns),
            "strongest_correlation": strongest,
            "strongest_left": strongest_pair["left"] if strongest_pair else None,
            "strongest_right": strongest_pair["right"] if strongest_pair else None,
            "strongest_p_value": strongest_pair["p_value"] if strongest_pair else None,
            "strongest_sample_size": strongest_pair["sample_size"] if strongest_pair else None,
            "strength_band": strength_band if strongest_pair else None,
        },
        "tables": [
            _table("Top correlation pairs", pd.DataFrame(pair_rows[:12]).round(5)),
            _table("Correlation coefficients", corr.reset_index().rename(columns={"index": "column"})),
        ],
        "chart": {
            "kind": "heatmap",
            "title": "Pairwise correlation heatmap",
            "labels": corr.columns.tolist(),
            "matrix": corr.to_numpy().tolist(),
        },
    }


def _bivariate_numeric_frame(frame: pd.DataFrame, request: StatisticRequest, *, method_name: str) -> tuple[pd.DataFrame, str, str]:
    if not request.target:
        raise ValueError(f"{method_name} requires a numeric target column.")
    feature = next((item for item in request.features if item and item != request.target), None)
    if not feature:
        raise ValueError(f"{method_name} requires a second numeric field in features.")
    clean = frame[[request.target, feature]].apply(pd.to_numeric, errors="coerce").dropna()
    if len(clean) < 3:
        raise ValueError(f"{method_name} requires at least three complete numeric pairs.")
    if float(clean[request.target].std(ddof=1)) == 0.0 or float(clean[feature].std(ddof=1)) == 0.0:
        raise ValueError(f"{method_name} requires non-constant numeric fields.")
    return clean, request.target, feature


def _correlation_strength(value: float) -> str:
    magnitude = abs(float(value))
    if magnitude >= 0.7:
        return "strong"
    if magnitude >= 0.4:
        return "moderate"
    if magnitude >= 0.2:
        return "weak"
    return "very_weak"


def run_bivariate_correlation(frame: pd.DataFrame, request: StatisticRequest, *, method: str) -> dict[str, Any]:
    labels = {
        "pearson": ("pearson_correlation", "Pearson Correlation", stats.pearsonr, "pearson_r"),
        "spearman": ("spearman_correlation", "Spearman Correlation", stats.spearmanr, "spearman_rho"),
        "kendall": ("kendall_tau", "Kendall Tau", stats.kendalltau, "kendall_tau"),
    }
    analysis_type, title, runner, statistic_key = labels[method]
    clean, target, feature = _bivariate_numeric_frame(frame, request, method_name=title)
    statistic, p_value = runner(clean[target], clean[feature])
    value = float(statistic)
    rows = pd.DataFrame(
        {
            "metric": [statistic_key, "p_value", "sample_size", "target_mean", "feature_mean"],
            "value": [value, float(p_value), int(len(clean)), float(clean[target].mean()), float(clean[feature].mean())],
        }
    ).round(6)
    return {
        "analysis_type": analysis_type,
        "title": title,
        "narrative": f"{title} between {target} and {feature} is {value:.4f} with p-value {float(p_value):.4g}.",
        "metrics": {
            statistic_key: value,
            "correlation": value,
            "abs_correlation": abs(value),
            "p_value": float(p_value),
            "sample_size": int(len(clean)),
            "strength": _correlation_strength(value),
            "direction": "positive" if value >= 0 else "negative",
        },
        "tables": [_table(f"{title} summary", rows)],
        "chart": {
            "kind": "scatter",
            "title": f"{target} vs {feature}",
            "x": clean[feature].head(200).tolist(),
            "y": clean[target].head(200).tolist(),
        },
    }


def _residualize_against_covariates(y: pd.Series, covariates: pd.DataFrame) -> np.ndarray:
    sm = _statsmodels_api()
    design = sm.add_constant(covariates.astype(float), has_constant="add")
    model = sm.OLS(y.astype(float), design).fit()
    return np.asarray(model.resid, dtype=float)


def _distance_correlation(x: np.ndarray, y: np.ndarray) -> float:
    x_values = np.asarray(x, dtype=float).reshape(-1, 1)
    y_values = np.asarray(y, dtype=float).reshape(-1, 1)
    x_dist = np.abs(x_values - x_values.T)
    y_dist = np.abs(y_values - y_values.T)
    x_centered = x_dist - x_dist.mean(axis=0) - x_dist.mean(axis=1)[:, None] + x_dist.mean()
    y_centered = y_dist - y_dist.mean(axis=0) - y_dist.mean(axis=1)[:, None] + y_dist.mean()
    dcov2 = float(np.mean(x_centered * y_centered))
    dvar_x = float(np.mean(x_centered * x_centered))
    dvar_y = float(np.mean(y_centered * y_centered))
    denominator = np.sqrt(max(dvar_x * dvar_y, 0.0))
    if denominator <= 0:
        raise ValueError("Distance correlation requires non-constant numeric fields.")
    return float(np.sqrt(max(dcov2, 0.0) / denominator))


def run_partial_correlation(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    clean, target, feature = _bivariate_numeric_frame(frame, request, method_name="Partial correlation")
    covariates = [item for item in request.features if item not in {target, feature} and item in frame.columns]
    if not covariates and request.group_column and request.group_column not in {target, feature}:
        covariates = [request.group_column]
    if not covariates:
        raise ValueError("Partial correlation requires at least one numeric covariate in features or group_column.")
    columns = [target, feature, *covariates]
    clean = frame[columns].apply(pd.to_numeric, errors="coerce").dropna()
    if len(clean) <= len(covariates) + 3:
        raise ValueError("Partial correlation needs more complete rows than covariates.")
    if float(clean[target].std(ddof=1)) == 0.0 or float(clean[feature].std(ddof=1)) == 0.0:
        raise ValueError("Partial correlation requires non-constant numeric target and feature fields.")
    usable_covariates = [column for column in covariates if float(clean[column].std(ddof=1)) > 0.0]
    if not usable_covariates:
        raise ValueError("Partial correlation requires at least one non-constant numeric covariate.")
    target_resid = _residualize_against_covariates(clean[target], clean[usable_covariates])
    feature_resid = _residualize_against_covariates(clean[feature], clean[usable_covariates])
    statistic, p_value = stats.pearsonr(target_resid, feature_resid)
    value = float(statistic)
    rows = pd.DataFrame(
        {
            "metric": ["partial_correlation", "p_value", "sample_size", "covariate_count"],
            "value": [value, float(p_value), int(len(clean)), int(len(usable_covariates))],
        }
    ).round(6)
    covariate_rows = pd.DataFrame(
        {
            "covariate": usable_covariates,
            "mean": [float(clean[column].mean()) for column in usable_covariates],
            "std": [float(clean[column].std(ddof=1)) for column in usable_covariates],
        }
    ).round(6)

    return {
        "analysis_type": "partial_correlation",
        "title": "Partial Correlation",
        "narrative": (
            f"Partial correlation between {target} and {feature}, controlling for {', '.join(usable_covariates)}, "
            f"is {value:.4f} with p-value {float(p_value):.4g}."
        ),
        "metrics": {
            "partial_correlation": value,
            "correlation": value,
            "abs_correlation": abs(value),
            "p_value": float(p_value),
            "sample_size": int(len(clean)),
            "covariate_count": int(len(usable_covariates)),
            "covariates": usable_covariates,
            "strength": _correlation_strength(value),
            "direction": "positive" if value >= 0 else "negative",
        },
        "tables": [
            _table("Partial correlation summary", rows),
            _table("Controlled covariates", covariate_rows),
        ],
        "chart": {
            "kind": "scatter",
            "title": f"Residualized {target} vs {feature}",
            "x": feature_resid[:200].tolist(),
            "y": target_resid[:200].tolist(),
        },
    }


def run_distance_correlation(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    clean, target, feature = _bivariate_numeric_frame(frame, request, method_name="Distance correlation")
    x_values = clean[feature].to_numpy(dtype=float)
    y_values = clean[target].to_numpy(dtype=float)
    value = _distance_correlation(x_values, y_values)
    iterations = max(100, min(int(request.bootstrap_iterations or 499), 5000))
    rng = np.random.default_rng(42)
    extreme = 0
    for _ in range(iterations):
        permuted = rng.permutation(y_values)
        permuted_value = _distance_correlation(x_values, permuted)
        extreme += int(permuted_value >= value)
    p_value = float((extreme + 1) / (iterations + 1))
    rows = pd.DataFrame(
        {
            "metric": ["distance_correlation", "permutation_p_value", "sample_size", "permutations"],
            "value": [value, p_value, int(len(clean)), iterations],
        }
    ).round(6)

    return {
        "analysis_type": "distance_correlation",
        "title": "Distance Correlation",
        "narrative": (
            f"Distance correlation between {target} and {feature} is {value:.4f}; "
            f"permutation p-value {p_value:.4g} over {iterations} shuffles."
        ),
        "metrics": {
            "distance_correlation": value,
            "correlation": value,
            "abs_correlation": abs(value),
            "p_value": p_value,
            "sample_size": int(len(clean)),
            "permutations": int(iterations),
            "strength": _correlation_strength(value),
            "direction": "nonlinear_or_general_association",
        },
        "tables": [_table("Distance correlation summary", rows)],
        "chart": {
            "kind": "scatter",
            "title": f"{target} vs {feature}",
            "x": clean[feature].head(200).tolist(),
            "y": clean[target].head(200).tolist(),
        },
    }


def run_point_biserial(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    if not request.target or not request.group_column:
        raise ValueError("Point-biserial correlation requires a numeric target and binary grouping column.")
    clean = frame[[request.target, request.group_column]].copy().dropna()
    clean[request.target] = pd.to_numeric(clean[request.target], errors="coerce")
    clean = clean.dropna()
    groups = clean[request.group_column].astype(str)
    labels = sorted(groups.unique().tolist())
    if len(labels) != 2:
        raise ValueError("Point-biserial correlation requires exactly two group categories.")
    if float(clean[request.target].std(ddof=1)) == 0.0:
        raise ValueError("Point-biserial correlation requires a non-constant numeric target.")
    coded = groups.eq(labels[1]).astype(int)
    statistic, p_value = stats.pointbiserialr(coded, clean[request.target])
    group_summary = (
        clean.assign(group=groups)
        .groupby("group")[request.target]
        .agg(["count", "mean", "median", "std"])
        .reset_index()
        .round(6)
    )
    value = float(statistic)
    return {
        "analysis_type": "point_biserial",
        "title": "Point-Biserial Correlation",
        "narrative": f"Point-biserial correlation between {request.group_column} and {request.target} is {value:.4f}; p-value {float(p_value):.4g}.",
        "metrics": {
            "point_biserial_r": value,
            "correlation": value,
            "abs_correlation": abs(value),
            "p_value": float(p_value),
            "sample_size": int(len(clean)),
            "negative_label": labels[0],
            "positive_label": labels[1],
            "strength": _correlation_strength(value),
            "direction": "positive" if value >= 0 else "negative",
        },
        "tables": [_table("Group numeric summary", group_summary)],
        "chart": {
            "kind": "bar",
            "title": f"{request.target} mean by {request.group_column}",
            "x": group_summary["group"].astype(str).tolist(),
            "y": group_summary["mean"].tolist(),
        },
    }


def run_eta_squared(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    if not request.target or not request.group_column:
        raise ValueError("Eta squared requires a numeric target and categorical grouping column.")
    clean = frame[[request.target, request.group_column]].copy().dropna()
    clean[request.target] = pd.to_numeric(clean[request.target], errors="coerce")
    clean = clean.dropna()
    if clean[request.group_column].nunique() < 2:
        raise ValueError("Eta squared requires at least two groups.")
    if float(clean[request.target].std(ddof=1)) == 0.0:
        raise ValueError("Eta squared requires a non-constant numeric target.")
    grand_mean = float(clean[request.target].mean())
    group_summary = (
        clean.groupby(request.group_column)[request.target]
        .agg(["count", "mean", "median", "std"])
        .reset_index()
        .rename(columns={request.group_column: "group"})
        .round(6)
    )
    ss_between = float(
        sum(
            len(subset) * (float(subset[request.target].mean()) - grand_mean) ** 2
            for _, subset in clean.groupby(request.group_column)
        )
    )
    ss_total = float(((clean[request.target] - grand_mean) ** 2).sum())
    if ss_total <= 0:
        raise ValueError("Eta squared requires positive total variance.")
    eta_squared = ss_between / ss_total
    dof_between = int(clean[request.group_column].nunique() - 1)
    dof_within = int(len(clean) - clean[request.group_column].nunique())
    samples = [subset[request.target].to_numpy(dtype=float) for _, subset in clean.groupby(request.group_column)]
    f_statistic, p_value = stats.f_oneway(*samples)
    return {
        "analysis_type": "eta_squared",
        "title": "Eta Squared Effect Size",
        "narrative": f"{request.group_column} explains {eta_squared:.2%} of variance in {request.target}; ANOVA p-value {float(p_value):.4g}.",
        "metrics": {
            "eta_squared": float(eta_squared),
            "p_value": float(p_value),
            "f_statistic": float(f_statistic),
            "sample_size": int(len(clean)),
            "groups": int(clean[request.group_column].nunique()),
            "ss_between": ss_between,
            "ss_total": ss_total,
            "degrees_between": dof_between,
            "degrees_within": dof_within,
        },
        "tables": [_table("Group effect summary", group_summary)],
        "chart": {
            "kind": "bar",
            "title": f"{request.target} mean by {request.group_column}",
            "x": group_summary["group"].astype(str).tolist(),
            "y": group_summary["mean"].tolist(),
        },
    }


def _categorical_series_for_summary(frame: pd.DataFrame, request: StatisticRequest, *, method_name: str) -> tuple[pd.Series, str]:
    field = request.target or request.group_column or (request.features[0] if request.features else None)
    if not field:
        raise ValueError(f"{method_name} requires a categorical field.")
    series = frame[field].dropna().astype(str)
    if series.empty:
        raise ValueError(f"{method_name} requires at least one non-null category.")
    return series, field


def _second_categorical_field(frame: pd.DataFrame, first: str, request: StatisticRequest) -> str | None:
    candidates = [request.target, request.group_column, *request.features]
    for candidate in candidates:
        if candidate and candidate != first and candidate in frame.columns:
            return candidate
    for column in frame.columns.astype(str).tolist():
        if column == first:
            continue
        clean = frame[column].dropna()
        if clean.empty:
            continue
        if not pd.api.types.is_numeric_dtype(clean) or clean.nunique() <= min(50, max(2, len(clean) // 2)):
            return column
    return None


def _group_numeric_summary(clean: pd.DataFrame, group_column: str, target: str) -> pd.DataFrame:
    return (
        clean.groupby(group_column)[target]
        .agg(["count", "sum", "mean", "median", "std", "min", "max"])
        .reset_index()
        .rename(columns={group_column: "group"})
        .sort_values("sum", ascending=False)
        .round(6)
    )


def run_descriptive_summary(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    series, target = _descriptive_series(frame, request, method_name="Descriptive summary")
    summary = _distribution_summary_table(series)
    mean = float(series.mean())
    median = float(series.median())
    std = float(series.std())
    return {
        "analysis_type": "descriptive_summary",
        "title": "Descriptive Summary",
        "narrative": f"{target} has {len(series)} numeric observations; mean={mean:.4f}, median={median:.4f}, std={std:.4f}.",
        "metrics": {
            "sample_size": int(len(series)),
            "mean": mean,
            "median": median,
            "std": std,
            "min": float(series.min()),
            "max": float(series.max()),
        },
        "tables": [_table("Descriptive summary", summary)],
        "chart": _distribution_chart(target, series),
    }


def run_frequency_table(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    series, field = _categorical_series_for_summary(frame, request, method_name="Frequency table")
    counts = series.value_counts(dropna=False)
    total = int(counts.sum())
    rows = pd.DataFrame(
        {
            "category": counts.index.astype(str),
            "count": counts.astype(int).values,
            "share": (counts / total).values,
            "cumulative_share": (counts / total).cumsum().values,
        }
    ).round(6)
    top_share = float(rows["share"].iloc[0]) if not rows.empty else 0.0
    return {
        "analysis_type": "frequency_table",
        "title": "Frequency Table",
        "narrative": f"{field} has {len(counts)} categories; top category {rows['category'].iloc[0]} accounts for {top_share:.2%}.",
        "metrics": {
            "sample_size": total,
            "category_count": int(len(counts)),
            "top_category": str(rows["category"].iloc[0]) if not rows.empty else None,
            "top_share": top_share,
        },
        "tables": [_table("Frequency table", rows)],
        "chart": {
            "kind": "bar",
            "title": f"{field} frequency",
            "x": rows["category"].head(20).tolist(),
            "y": rows["count"].head(20).tolist(),
        },
    }


def run_cross_tabulation(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    left = request.group_column or request.target
    if not left:
        raise ValueError("Cross tabulation requires at least one categorical field.")
    right = _second_categorical_field(frame, left, request)
    if not right:
        raise ValueError("Cross tabulation requires a second categorical field.")
    table = _categorical_association_table(
        frame,
        StatisticRequest(dataset_id=request.dataset_id, analysis_type="chi_square", target=right, group_column=left),
        test_name="Cross tabulation",
    )
    total = float(table.to_numpy().sum())
    row_totals = table.sum(axis=1)
    column_totals = table.sum(axis=0)
    largest_cell = float(table.to_numpy().max())
    largest_cell_share = largest_cell / total if total else 0.0
    flat_rows = _contingency_records(table, left_label=left, right_label=right)
    share_rows = pd.DataFrame(
        [
            {**row, "share": row["count"] / total if total else 0.0}
            for row in flat_rows
        ]
    ).round(6)
    return {
        "analysis_type": "cross_tabulation",
        "title": "Cross Tabulation",
        "narrative": f"Cross tabulation of {left} by {right} covers {int(total)} complete observations across {table.shape[0]}x{table.shape[1]} cells.",
        "metrics": {
            "sample_size": int(total),
            "row_categories": int(table.shape[0]),
            "column_categories": int(table.shape[1]),
            "largest_cell_share": largest_cell_share,
            "largest_row_share": float(row_totals.max() / total),
            "largest_column_share": float(column_totals.max() / total),
        },
        "tables": [
            _table("Cross tabulation", _contingency_table_view(table, left)),
            _table("Cell shares", share_rows),
        ],
        "chart": {
            "kind": "bar",
            "title": f"{left} by {right} cell counts",
            "x": [f"{row[left]} / {row[right]}" for row in flat_rows[:24]],
            "y": [row["count"] for row in flat_rows[:24]],
        },
    }


def run_pivot_summary(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    if not request.target or not request.group_column:
        raise ValueError("Pivot summary requires a numeric target and grouping column.")
    clean = frame[[request.target, request.group_column]].copy().dropna()
    clean[request.target] = pd.to_numeric(clean[request.target], errors="coerce")
    clean = clean.dropna()
    if clean.empty:
        raise ValueError("Pivot summary requires complete numeric observations.")
    summary = _group_numeric_summary(clean, request.group_column, request.target)
    max_mean = float(summary["mean"].max())
    min_mean = float(summary["mean"].min())
    max_min_mean_ratio = None if min_mean == 0 else float(max_mean / abs(min_mean))
    return {
        "analysis_type": "pivot_summary",
        "title": "Pivot Summary",
        "narrative": f"{request.target} summarized across {len(summary)} {request.group_column} groups; top group by sum is {summary['group'].iloc[0]}.",
        "metrics": {
            "sample_size": int(len(clean)),
            "groups": int(len(summary)),
            "top_group": str(summary["group"].iloc[0]),
            "top_group_share": float(summary["sum"].iloc[0] / summary["sum"].sum()) if summary["sum"].sum() else None,
            "max_min_mean_ratio": max_min_mean_ratio,
        },
        "tables": [_table("Pivot summary", summary)],
        "chart": {
            "kind": "bar",
            "title": f"{request.target} sum by {request.group_column}",
            "x": summary["group"].head(20).astype(str).tolist(),
            "y": summary["sum"].head(20).tolist(),
        },
    }


def _descriptive_series(frame: pd.DataFrame, request: StatisticRequest, *, method_name: str, allow_negative: bool = True) -> tuple[pd.Series, str]:
    target = request.target or (request.features[0] if request.features else None)
    if not target:
        raise ValueError(f"{method_name} requires a target numeric column.")
    series = pd.to_numeric(frame[target], errors="coerce").dropna()
    if len(series) < 2:
        raise ValueError(f"{method_name} requires at least two numeric observations.")
    if not allow_negative and (series < 0).any():
        raise ValueError(f"{method_name} requires non-negative contribution values.")
    return series, target


def _safe_pct_change(baseline: float, candidate: float) -> float | None:
    if baseline == 0:
        return None
    return float((candidate - baseline) / abs(baseline))


def _gini_from_values(values: np.ndarray) -> float:
    clean = np.asarray(values, dtype=float)
    clean = clean[np.isfinite(clean)]
    if clean.size == 0:
        raise ValueError("Gini coefficient requires numeric observations.")
    if (clean < 0).any():
        raise ValueError("Gini coefficient requires non-negative values.")
    total = float(clean.sum())
    if total <= 0:
        raise ValueError("Gini coefficient requires a positive total contribution.")
    sorted_values = np.sort(clean)
    n = sorted_values.size
    index = np.arange(1, n + 1, dtype=float)
    return float((2 * np.sum(index * sorted_values)) / (n * total) - (n + 1) / n)


def run_quantile_profile(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    series, target = _descriptive_series(frame, request, method_name="Quantile profile")
    quantile_levels = [0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99]
    quantiles = series.quantile(quantile_levels)
    rows = pd.DataFrame(
        {
            "quantile": [f"p{int(level * 100):02d}" for level in quantile_levels],
            "value": [float(quantiles.loc[level]) for level in quantile_levels],
        }
    ).round(6)
    median = float(quantiles.loc[0.5])
    p95 = float(quantiles.loc[0.95])
    p05 = float(quantiles.loc[0.05])
    tail_to_median_ratio = None if median == 0 else float((p95 - p05) / abs(median))
    summary = pd.DataFrame(
        {
            "metric": ["count", "mean", "std", "median", "p05", "p95", "tail_to_median_ratio"],
            "value": [int(len(series)), float(series.mean()), float(series.std()), median, p05, p95, tail_to_median_ratio],
        }
    ).round(6)
    return {
        "analysis_type": "quantile_profile",
        "title": "Quantile Profile",
        "narrative": f"{target} median is {median:.4f}; p05-p95 span is {p05:.4f} to {p95:.4f}.",
        "metrics": {
            "sample_size": int(len(series)),
            "median": median,
            "p05": p05,
            "p95": p95,
            "tail_to_median_ratio": tail_to_median_ratio,
        },
        "tables": [_table("Quantile profile", rows), _table("Quantile summary", summary)],
        "chart": {
            "kind": "bar",
            "title": f"{target} quantiles",
            "x": rows["quantile"].tolist(),
            "y": rows["value"].tolist(),
        },
    }


def run_trimmed_mean(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    series, target = _descriptive_series(frame, request, method_name="Trimmed mean")
    trim_proportion = 0.1
    raw_mean = float(series.mean())
    trimmed_mean_value = float(stats.trim_mean(series.to_numpy(), proportiontocut=trim_proportion))
    median = float(series.median())
    shift_pct = _safe_pct_change(raw_mean, trimmed_mean_value)
    trim_count_each_tail = int(np.floor(len(series) * trim_proportion))
    kept_count = int(len(series) - (2 * trim_count_each_tail))
    summary = pd.DataFrame(
        {
            "metric": ["raw_mean", "trimmed_mean", "median", "trim_each_tail", "kept_count", "trimmed_mean_shift_pct"],
            "value": [raw_mean, trimmed_mean_value, median, trim_count_each_tail, kept_count, shift_pct],
        }
    ).round(6)
    return {
        "analysis_type": "trimmed_mean",
        "title": "Trimmed Mean",
        "narrative": f"{target} raw mean is {raw_mean:.4f}; 10% trimmed mean is {trimmed_mean_value:.4f}.",
        "metrics": {
            "raw_mean": raw_mean,
            "trimmed_mean": trimmed_mean_value,
            "median": median,
            "trim_proportion_each_tail": trim_proportion,
            "trim_count_each_tail": trim_count_each_tail,
            "kept_count": kept_count,
            "trimmed_mean_shift_pct": shift_pct,
            "sample_size": int(len(series)),
        },
        "tables": [_table("Trimmed mean summary", summary)],
        "chart": {
            "kind": "bar",
            "title": f"{target} raw vs robust center",
            "x": ["raw_mean", "trimmed_mean", "median"],
            "y": [raw_mean, trimmed_mean_value, median],
        },
    }


def run_winsorized_summary(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    series, target = _descriptive_series(frame, request, method_name="Winsorized summary")
    lower_cap = float(series.quantile(0.05))
    upper_cap = float(series.quantile(0.95))
    winsorized = series.clip(lower=lower_cap, upper=upper_cap)
    raw_mean = float(series.mean())
    winsorized_mean = float(winsorized.mean())
    shift_pct = _safe_pct_change(raw_mean, winsorized_mean)
    clipped_low = int((series < lower_cap).sum())
    clipped_high = int((series > upper_cap).sum())
    raw_std = float(series.std())
    winsorized_std = float(winsorized.std())
    summary = pd.DataFrame(
        {
            "metric": ["raw_mean", "winsorized_mean", "raw_std", "winsorized_std", "lower_cap", "upper_cap", "clipped_low", "clipped_high", "winsorized_mean_shift_pct"],
            "value": [raw_mean, winsorized_mean, raw_std, winsorized_std, lower_cap, upper_cap, clipped_low, clipped_high, shift_pct],
        }
    ).round(6)
    return {
        "analysis_type": "winsorized_summary",
        "title": "Winsorized Summary",
        "narrative": f"{target} winsorized mean is {winsorized_mean:.4f} after capping p05={lower_cap:.4f} and p95={upper_cap:.4f}.",
        "metrics": {
            "raw_mean": raw_mean,
            "winsorized_mean": winsorized_mean,
            "raw_std": raw_std,
            "winsorized_std": winsorized_std,
            "lower_cap": lower_cap,
            "upper_cap": upper_cap,
            "clipped_low": clipped_low,
            "clipped_high": clipped_high,
            "winsorized_mean_shift_pct": shift_pct,
            "sample_size": int(len(series)),
        },
        "tables": [_table("Winsorized summary", summary)],
        "chart": {
            "kind": "bar",
            "title": f"{target} raw vs winsorized center",
            "x": ["raw_mean", "winsorized_mean", "raw_std", "winsorized_std"],
            "y": [raw_mean, winsorized_mean, raw_std, winsorized_std],
        },
    }


def run_gini_coefficient(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    series, target = _descriptive_series(frame, request, method_name="Gini coefficient", allow_negative=False)
    values = series.to_numpy(dtype=float)
    gini = _gini_from_values(values)
    sorted_desc = np.sort(values)[::-1]
    total = float(sorted_desc.sum())
    top_10_count = max(1, int(np.ceil(len(sorted_desc) * 0.1)))
    top_20_count = max(1, int(np.ceil(len(sorted_desc) * 0.2)))
    top_10_share = float(sorted_desc[:top_10_count].sum() / total)
    top_20_share = float(sorted_desc[:top_20_count].sum() / total)
    sorted_asc = np.sort(values)
    lorenz_points = pd.DataFrame(
        {
            "population_share": np.linspace(0, 1, len(sorted_asc) + 1),
            "contribution_share": np.concatenate([[0.0], np.cumsum(sorted_asc) / total]),
        }
    ).round(6)
    summary = pd.DataFrame(
        {
            "metric": ["gini", "top_10_share", "top_20_share", "total_contribution", "sample_size"],
            "value": [gini, top_10_share, top_20_share, total, int(len(series))],
        }
    ).round(6)
    return {
        "analysis_type": "gini_coefficient",
        "title": "Gini Coefficient",
        "narrative": f"{target} Gini coefficient is {gini:.4f}; top 20% share is {top_20_share:.2%}.",
        "metrics": {
            "gini": gini,
            "top_10_share": top_10_share,
            "top_20_share": top_20_share,
            "total_contribution": total,
            "sample_size": int(len(series)),
        },
        "tables": [_table("Gini summary", summary), _table("Lorenz curve points", lorenz_points)],
        "chart": {
            "kind": "bar",
            "title": f"{target} concentration shares",
            "x": ["top_10_share", "top_20_share", "remaining_80_share"],
            "y": [top_10_share, top_20_share, 1 - top_20_share],
        },
    }


def run_pareto_analysis(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    if not request.target or not request.group_column:
        raise ValueError("Pareto analysis requires a numeric target and grouping column.")
    clean = frame[[request.target, request.group_column]].copy().dropna()
    clean[request.target] = pd.to_numeric(clean[request.target], errors="coerce")
    clean = clean.dropna()
    if clean.empty:
        raise ValueError("Pareto analysis requires complete numeric contribution observations.")
    if (clean[request.target] < 0).any():
        raise ValueError("Pareto analysis requires non-negative contribution values.")
    grouped = (
        clean.groupby(request.group_column, dropna=False)[request.target]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={request.group_column: "group", request.target: "contribution"})
    )
    total = float(grouped["contribution"].sum())
    if total <= 0:
        raise ValueError("Pareto analysis requires a positive total contribution.")
    grouped["share"] = grouped["contribution"] / total
    grouped["cumulative_share"] = grouped["share"].cumsum()
    grouped["rank"] = range(1, len(grouped) + 1)
    grouped["group"] = grouped["group"].astype(str)
    top_20_count = max(1, int(np.ceil(len(grouped) * 0.2)))
    top_20_share = float(grouped.head(top_20_count)["share"].sum())
    groups_to_80 = int((grouped["cumulative_share"] < 0.8).sum() + 1)
    rows = grouped[["rank", "group", "contribution", "share", "cumulative_share"]].round(6)
    return {
        "analysis_type": "pareto_analysis",
        "title": "Pareto Contribution Analysis",
        "narrative": f"Top {top_20_count} of {len(grouped)} {request.group_column} groups contribute {top_20_share:.2%} of {request.target}.",
        "metrics": {
            "groups": int(len(grouped)),
            "total_contribution": total,
            "top_20_group_count": top_20_count,
            "top_20_share": top_20_share,
            "groups_to_80pct": groups_to_80,
            "sample_size": int(len(clean)),
        },
        "tables": [_table("Pareto contribution table", rows)],
        "chart": {
            "kind": "bar",
            "title": f"{request.target} contribution by {request.group_column}",
            "x": rows["group"].head(20).tolist(),
            "y": rows["contribution"].head(20).tolist(),
            "details": rows.head(20).to_dict(orient="records"),
        },
    }


def run_segmented_kpi_breakdown(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    if not request.target or not request.group_column:
        raise ValueError("Segmented KPI breakdown requires a numeric target and grouping column.")
    clean = frame[[request.target, request.group_column]].copy().dropna()
    clean[request.target] = pd.to_numeric(clean[request.target], errors="coerce")
    clean = clean.dropna()
    if clean.empty:
        raise ValueError("Segmented KPI breakdown requires complete numeric observations.")
    summary = _group_numeric_summary(clean, request.group_column, request.target)
    total_sum = float(summary["sum"].sum())
    summary["sum_share"] = summary["sum"] / total_sum if total_sum else 0.0
    summary["mean_rank"] = summary["mean"].rank(ascending=False, method="dense").astype(int)
    summary = summary.sort_values(["mean_rank", "sum"], ascending=[True, False]).round(6)
    top_mean = float(summary["mean"].iloc[0])
    bottom_mean = float(summary["mean"].iloc[-1])
    top_bottom_mean_ratio = None if bottom_mean == 0 else float(top_mean / abs(bottom_mean))
    return {
        "analysis_type": "segmented_kpi_breakdown",
        "title": "Segmented KPI Breakdown",
        "narrative": f"{request.target} KPI differs across {len(summary)} {request.group_column} groups; top mean group is {summary['group'].iloc[0]}.",
        "metrics": {
            "sample_size": int(len(clean)),
            "groups": int(len(summary)),
            "top_mean_group": str(summary["group"].iloc[0]),
            "top_mean": top_mean,
            "bottom_mean": bottom_mean,
            "top_bottom_mean_ratio": top_bottom_mean_ratio,
            "total_sum": total_sum,
        },
        "tables": [_table("Segmented KPI breakdown", summary)],
        "chart": {
            "kind": "bar",
            "title": f"{request.target} mean by {request.group_column}",
            "x": summary["group"].head(20).astype(str).tolist(),
            "y": summary["mean"].head(20).tolist(),
        },
    }


def run_ols(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    if not request.target or len(request.features) < 1:
        raise ValueError("OLS requires one numeric target and at least one feature.")
    sm = _statsmodels_api()

    clean = frame[[request.target, *request.features]].apply(pd.to_numeric, errors="coerce").dropna()
    if len(clean) < max(10, len(request.features) + 2):
        raise ValueError("Not enough complete rows to fit an OLS model.")

    y = clean[request.target]
    x = sm.add_constant(clean[request.features], has_constant="add")
    model = sm.OLS(y, x).fit()
    ci = model.conf_int()
    coefficients = pd.DataFrame(
        {
            "term": model.params.index.astype(str),
            "coefficient": model.params.values,
            "std_error": model.bse.values,
            "t_value": model.tvalues.values,
            "p_value": model.pvalues.values,
            "ci_low": ci[0].values,
            "ci_high": ci[1].values,
        }
    ).round(5)

    feature_terms = coefficients[coefficients["term"] != "const"]
    strongest_term = (
        feature_terms.assign(abs_coefficient=feature_terms["coefficient"].abs())
        .sort_values("abs_coefficient", ascending=False)
        .iloc[0]
        if not feature_terms.empty
        else None
    )
    return {
        "analysis_type": "ols",
        "title": "OLS Regression",
        "narrative": (
            f"Adjusted R^2 is {model.rsquared_adj:.3f} using {len(clean)} complete observations. "
            f"The strongest coefficient by magnitude is {strongest_term['term']} ({strongest_term['coefficient']:.4f}); "
            f"use statistically reliable terms as the first driver-analysis candidates."
            if strongest_term is not None
            else f"Adjusted R^2 is {model.rsquared_adj:.3f}, using {len(clean)} complete observations."
        ),
        "metrics": {
            "observations": int(model.nobs),
            "r_squared": float(model.rsquared),
            "adjusted_r_squared": float(model.rsquared_adj),
            "aic": float(model.aic),
            "bic": float(model.bic),
            "f_statistic": float(model.fvalue) if model.fvalue is not None else None,
            "f_p_value": float(model.f_pvalue) if model.f_pvalue is not None else None,
            "strongest_term": str(strongest_term["term"]) if strongest_term is not None else None,
        },
        "tables": [_table("Coefficient table", coefficients)],
        "chart": {
            "kind": "bar",
            "title": "Feature coefficients",
            "x": feature_terms["term"].tolist(),
            "y": feature_terms["coefficient"].round(5).tolist(),
        },
    }


def _regression_clean_frame(frame: pd.DataFrame, request: StatisticRequest, *, method_name: str, min_rows: int = 10) -> tuple[pd.DataFrame, str, list[str]]:
    if not request.target or len(request.features) < 1:
        raise ValueError(f"{method_name} requires one numeric target and at least one numeric feature.")
    features = [field for field in dict.fromkeys(request.features) if field != request.target]
    if not features:
        raise ValueError(f"{method_name} requires at least one numeric feature that is different from the target.")
    clean = frame[[request.target, *features]].apply(pd.to_numeric, errors="coerce").dropna()
    required_rows = max(min_rows, len(features) + 3)
    if len(clean) < required_rows:
        raise ValueError(f"Not enough complete rows for {method_name}; at least {required_rows} are required.")
    if float(clean[request.target].std(ddof=1)) == 0.0:
        raise ValueError(f"{method_name} requires a non-constant numeric target.")
    constant_features = [field for field in features if float(clean[field].std(ddof=1)) == 0.0]
    if constant_features:
        raise ValueError(f"{method_name} requires non-constant numeric features; constant fields: {', '.join(constant_features)}.")
    return clean, request.target, features


def _regularized_regression_model(method: str, request: StatisticRequest) -> tuple[str, Any]:
    alpha = max(0.0001, min(float(request.regularization_strength or 1.0), 100.0))
    if method == "ridge":
        return "ridge_regression", Ridge(alpha=alpha, random_state=42)
    if method == "lasso":
        return "lasso_regression", Lasso(alpha=alpha, random_state=42, max_iter=20000)
    l1_ratio = max(0.0, min(float(request.l1_ratio or 0.5), 1.0))
    return "elastic_net", ElasticNet(alpha=alpha, l1_ratio=l1_ratio, random_state=42, max_iter=20000)


def run_regularized_regression(frame: pd.DataFrame, request: StatisticRequest, *, method: str) -> dict[str, Any]:
    clean, target, features = _regression_clean_frame(frame, request, method_name=method.replace("_", " ").title(), min_rows=12)
    analysis_type, model = _regularized_regression_model(method, request)
    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(clean[features])
    y = clean[target].to_numpy(dtype=float)
    model.fit(x_scaled, y)
    predictions = model.predict(x_scaled)
    coefficients = pd.DataFrame(
        {
            "term": features,
            "standardized_coefficient": model.coef_,
            "abs_standardized_coefficient": np.abs(model.coef_),
        }
    ).sort_values("abs_standardized_coefficient", ascending=False).round(6)
    strongest = coefficients.iloc[0] if not coefficients.empty else None
    residuals = y - predictions
    r_squared = r2_score(y, predictions)
    rmse = float(np.sqrt(mean_squared_error(y, predictions)))
    mae = float(mean_absolute_error(y, predictions))
    alpha = max(0.0001, min(float(request.regularization_strength or 1.0), 100.0))
    metrics = {
        "sample_size": int(len(clean)),
        "feature_count": int(len(features)),
        "regularization_strength": alpha,
        "r_squared": float(r_squared),
        "rmse": rmse,
        "mae": mae,
        "intercept": float(model.intercept_),
        "strongest_term": str(strongest["term"]) if strongest is not None else None,
        "nonzero_terms": int((np.abs(model.coef_) > 1e-8).sum()),
    }
    if analysis_type == "elastic_net":
        metrics["l1_ratio"] = max(0.0, min(float(request.l1_ratio or 0.5), 1.0))
    residual_table = pd.DataFrame(
        {
            "metric": ["residual_mean", "residual_std", "prediction_mean", "target_mean"],
            "value": [
                float(np.mean(residuals)),
                float(np.std(residuals, ddof=1)),
                float(np.mean(predictions)),
                float(np.mean(y)),
            ],
        }
    ).round(6)
    title = {
        "ridge_regression": "Ridge Regression",
        "lasso_regression": "Lasso Regression",
        "elastic_net": "Elastic Net Regression",
    }[analysis_type]
    return {
        "analysis_type": analysis_type,
        "title": title,
        "narrative": (
            f"{title} fitted {len(features)} standardized feature(s) for {target} with alpha={alpha:g}; "
            f"in-sample R^2 is {r_squared:.3f} and strongest regularized term is {metrics['strongest_term']}."
        ),
        "metrics": metrics,
        "tables": [
            _table("Regularized coefficient table", coefficients),
            _table("Regularized fit summary", residual_table),
        ],
        "chart": {
            "kind": "bar",
            "title": f"{title} standardized coefficients",
            "x": coefficients["term"].tolist(),
            "y": coefficients["standardized_coefficient"].tolist(),
        },
    }


def _model_coefficient_table(model: Any) -> pd.DataFrame:
    ci = model.conf_int()
    return pd.DataFrame(
        {
            "term": model.params.index.astype(str),
            "coefficient": model.params.values,
            "std_error": model.bse.values,
            "z_or_t_value": model.tvalues.values,
            "p_value": model.pvalues.values,
            "ci_low": ci[0].values,
            "ci_high": ci[1].values,
        }
    ).round(6)


def run_robust_regression(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    clean, target, features = _regression_clean_frame(frame, request, method_name="Robust Regression", min_rows=12)
    sm = _statsmodels_api()
    y = clean[target]
    x = sm.add_constant(clean[features], has_constant="add")
    model = sm.RLM(y, x, M=sm.robust.norms.HuberT()).fit()
    coefficients = _model_coefficient_table(model)
    feature_terms = coefficients[coefficients["term"] != "const"]
    strongest = (
        feature_terms.assign(abs_coefficient=feature_terms["coefficient"].abs())
        .sort_values("abs_coefficient", ascending=False)
        .iloc[0]
        if not feature_terms.empty
        else None
    )
    residuals = y.to_numpy(dtype=float) - model.fittedvalues
    robust_objective = float(np.sum(np.square(residuals)))
    return {
        "analysis_type": "robust_regression",
        "title": "Robust Regression",
        "narrative": (
            f"Robust regression fitted {len(features)} feature(s) for {target} using Huber weighting; "
            f"strongest robust coefficient is {strongest['term']} ({strongest['coefficient']:.4f})."
            if strongest is not None
            else f"Robust regression fitted {len(features)} feature(s) for {target} using Huber weighting."
        ),
        "metrics": {
            "sample_size": int(len(clean)),
            "feature_count": int(len(features)),
            "scale": float(model.scale),
            "robust_objective": robust_objective,
            "strongest_term": str(strongest["term"]) if strongest is not None else None,
            "residual_std": float(np.std(residuals, ddof=1)),
        },
        "tables": [_table("Robust coefficient table", coefficients)],
        "chart": {
            "kind": "bar",
            "title": "Robust feature coefficients",
            "x": feature_terms["term"].tolist(),
            "y": feature_terms["coefficient"].tolist(),
        },
    }


def run_quantile_regression(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    clean, target, features = _regression_clean_frame(frame, request, method_name="Quantile Regression", min_rows=14)
    sm = _statsmodels_api()
    quantile_value = max(0.05, min(float(request.quantile or 0.5), 0.95))
    y = clean[target]
    x = sm.add_constant(clean[features], has_constant="add")
    model = sm.QuantReg(y, x).fit(q=quantile_value)
    coefficients = _model_coefficient_table(model)
    feature_terms = coefficients[coefficients["term"] != "const"]
    strongest = (
        feature_terms.assign(abs_coefficient=feature_terms["coefficient"].abs())
        .sort_values("abs_coefficient", ascending=False)
        .iloc[0]
        if not feature_terms.empty
        else None
    )
    predictions = model.predict(x)
    pseudo_r2 = getattr(model, "prsquared", None)
    return {
        "analysis_type": "quantile_regression",
        "title": "Quantile Regression",
        "narrative": (
            f"Quantile regression fitted q={quantile_value:.2f} for {target}; "
            f"strongest quantile coefficient is {strongest['term']} ({strongest['coefficient']:.4f})."
            if strongest is not None
            else f"Quantile regression fitted q={quantile_value:.2f} for {target}."
        ),
        "metrics": {
            "sample_size": int(len(clean)),
            "feature_count": int(len(features)),
            "quantile": quantile_value,
            "pseudo_r_squared": float(pseudo_r2) if pseudo_r2 is not None else None,
            "mae": float(mean_absolute_error(y, predictions)),
            "strongest_term": str(strongest["term"]) if strongest is not None else None,
        },
        "tables": [_table("Quantile coefficient table", coefficients)],
        "chart": {
            "kind": "bar",
            "title": f"Quantile q={quantile_value:.2f} coefficients",
            "x": feature_terms["term"].tolist(),
            "y": feature_terms["coefficient"].tolist(),
        },
    }


def _fit_ols_residual_diagnostic(
    frame: pd.DataFrame,
    request: StatisticRequest,
    *,
    method_name: str,
    min_rows: int = 12,
) -> tuple[pd.DataFrame, Any, list[str]]:
    if not request.target or len(request.features) < 1:
        raise ValueError(f"{method_name} requires one numeric target and at least one numeric feature.")

    features = [field for field in dict.fromkeys(request.features) if field != request.target]
    if not features:
        raise ValueError(f"{method_name} requires at least one numeric feature that is different from the target.")

    clean = frame[[request.target, *features]].apply(pd.to_numeric, errors="coerce").dropna()
    required_rows = max(min_rows, len(features) + 5)
    if len(clean) < required_rows:
        raise ValueError(f"Not enough complete rows for {method_name}; at least {required_rows} are required.")

    if float(clean[request.target].std(ddof=1)) == 0.0:
        raise ValueError(f"{method_name} requires a non-constant numeric target.")
    constant_features = [field for field in features if float(clean[field].std(ddof=1)) == 0.0]
    if constant_features:
        raise ValueError(f"{method_name} requires non-constant numeric features; constant fields: {', '.join(constant_features)}.")
    sm = _statsmodels_api()

    y = clean[request.target]
    x = sm.add_constant(clean[features], has_constant="add")
    model = sm.OLS(y, x).fit()
    return clean, model, features


def _regression_diagnostic_chart(model: Any, *, title: str, mode: str = "fitted") -> dict[str, Any]:
    residuals = pd.Series(model.resid).head(200)
    if mode == "sequence":
        return {
            "kind": "scatter",
            "title": title,
            "x": list(range(1, len(residuals) + 1)),
            "y": residuals.round(6).tolist(),
        }
    return {
        "kind": "scatter",
        "title": title,
        "x": pd.Series(model.fittedvalues).head(200).round(6).tolist(),
        "y": residuals.round(6).tolist(),
    }


def run_breusch_pagan(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    clean, model, features = _fit_ols_residual_diagnostic(frame, request, method_name="Breusch-Pagan Test")
    _acorr_ljungbox, het_breuschpagan, _het_white = _statsmodels_diagnostic()
    lm_statistic, lm_p_value, f_statistic, f_p_value = het_breuschpagan(model.resid, model.model.exog)
    p_value = float(f_p_value)
    decision = "heteroskedastic" if p_value < request.alpha else "not_heteroskedastic"
    summary = pd.DataFrame(
        {
            "metric": ["lm_statistic", "lm_p_value", "f_statistic", "f_p_value", "sample_size", "feature_count"],
            "value": [
                float(lm_statistic),
                float(lm_p_value),
                float(f_statistic),
                p_value,
                int(len(clean)),
                int(len(features)),
            ],
        }
    ).round(6)
    feature_summary = (
        clean[features]
        .agg(["mean", "std", "min", "max"])
        .T.reset_index()
        .rename(columns={"index": "feature"})
        .round(6)
    )
    return {
        "analysis_type": "breusch_pagan",
        "title": "Breusch-Pagan Test",
        "narrative": (
            f"Breusch-Pagan residual variance diagnostic on {request.target} uses {len(clean)} complete observations "
            f"and {len(features)} feature(s); F p-value is {p_value:.4g}, so the result is {decision} at alpha={request.alpha}."
        ),
        "metrics": {
            "sample_size": int(len(clean)),
            "feature_count": int(len(features)),
            "lm_statistic": float(lm_statistic),
            "lm_p_value": float(lm_p_value),
            "f_statistic": float(f_statistic),
            "f_p_value": p_value,
            "p_value": p_value,
            "decision": decision,
        },
        "tables": [
            _table("Breusch-Pagan diagnostic", summary),
            _table("Regression feature summary", feature_summary),
        ],
        "chart": _regression_diagnostic_chart(model, title="Fitted values vs residuals"),
    }


def run_white_test(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    clean, model, features = _fit_ols_residual_diagnostic(frame, request, method_name="White Test", min_rows=14)
    _acorr_ljungbox, _het_breuschpagan, het_white = _statsmodels_diagnostic()
    lm_statistic, lm_p_value, f_statistic, f_p_value = het_white(model.resid, model.model.exog)
    p_value = float(f_p_value)
    decision = "heteroskedastic" if p_value < request.alpha else "not_heteroskedastic"
    summary = pd.DataFrame(
        {
            "metric": ["lm_statistic", "lm_p_value", "f_statistic", "f_p_value", "sample_size", "feature_count"],
            "value": [
                float(lm_statistic),
                float(lm_p_value),
                float(f_statistic),
                p_value,
                int(len(clean)),
                int(len(features)),
            ],
        }
    ).round(6)
    return {
        "analysis_type": "white_test",
        "title": "White Test",
        "narrative": (
            f"White residual variance diagnostic on {request.target} uses {len(clean)} complete observations "
            f"and checks nonlinear variance structure; F p-value is {p_value:.4g}, so the result is {decision} at alpha={request.alpha}."
        ),
        "metrics": {
            "sample_size": int(len(clean)),
            "feature_count": int(len(features)),
            "lm_statistic": float(lm_statistic),
            "lm_p_value": float(lm_p_value),
            "f_statistic": float(f_statistic),
            "f_p_value": p_value,
            "p_value": p_value,
            "decision": decision,
        },
        "tables": [_table("White test diagnostic", summary)],
        "chart": _regression_diagnostic_chart(model, title="Fitted values vs residuals"),
    }


def run_durbin_watson(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    clean, model, features = _fit_ols_residual_diagnostic(frame, request, method_name="Durbin-Watson Test")
    durbin_watson = _statsmodels_durbin_watson()
    statistic = float(durbin_watson(model.resid))
    if statistic < 1.5:
        decision = "positive_autocorrelation_risk"
    elif statistic > 2.5:
        decision = "negative_autocorrelation_risk"
    else:
        decision = "low_autocorrelation_risk"
    summary = pd.DataFrame(
        {
            "metric": ["durbin_watson_statistic", "sample_size", "feature_count", "residual_mean", "residual_std"],
            "value": [
                statistic,
                int(len(clean)),
                int(len(features)),
                float(pd.Series(model.resid).mean()),
                float(pd.Series(model.resid).std(ddof=1)),
            ],
        }
    ).round(6)
    return {
        "analysis_type": "durbin_watson",
        "title": "Durbin-Watson Test",
        "narrative": (
            f"Durbin-Watson residual autocorrelation diagnostic on {request.target} is {statistic:.4f} "
            f"using {len(clean)} complete observations; classification is {decision}."
        ),
        "metrics": {
            "sample_size": int(len(clean)),
            "feature_count": int(len(features)),
            "durbin_watson_statistic": statistic,
            "decision": decision,
        },
        "tables": [_table("Durbin-Watson diagnostic", summary)],
        "chart": _regression_diagnostic_chart(model, title="Residual sequence", mode="sequence"),
    }


def run_anova(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    if not request.target or not request.group_column:
        raise ValueError("ANOVA requires a numeric target and a grouping column.")
    sm = _statsmodels_api()
    ols = _statsmodels_ols()

    clean = frame[[request.target, request.group_column]].copy()
    clean[request.target] = pd.to_numeric(clean[request.target], errors="coerce")
    clean = clean.dropna()
    if clean[request.group_column].nunique() < 2:
        raise ValueError("ANOVA needs at least two groups.")

    model = ols(
        f'{quote(request.target)} ~ C({quote(request.group_column)})',
        data=clean,
    ).fit()
    anova_table = sm.stats.anova_lm(model, typ=2).reset_index().rename(columns={"index": "term"}).round(5)
    group_means = (
        clean.groupby(request.group_column)[request.target]
        .agg(["count", "mean", "std"])
        .reset_index()
        .rename(columns={request.group_column: "group"})
        .round(5)
    )
    effect = anova_table.loc[0, "sum_sq"] / anova_table["sum_sq"].sum() if "sum_sq" in anova_table else None
    f_statistic = float(anova_table.loc[0, "F"]) if "F" in anova_table else None
    p_value = float(anova_table.loc[0, "PR(>F)"]) if "PR(>F)" in anova_table else None
    top_group = group_means.sort_values("mean", ascending=False).iloc[0]
    bottom_group = group_means.sort_values("mean", ascending=True).iloc[0]
    decision = "significant" if p_value is not None and p_value < 0.05 else "not_significant"

    return {
        "analysis_type": "anova",
        "title": "One-way ANOVA",
        "narrative": (
            f"Mean {request.target} differs across {request.group_column} with F={f_statistic:.3f}, p-value {p_value:.4g}, "
            f"and effect share {effect:.3f}. The highest-mean group is {top_group['group']} and the lowest is {bottom_group['group']}; "
            f"{'post-hoc comparison is recommended' if decision == 'significant' else 'the group effect looks limited'}."
            if effect is not None and f_statistic is not None and p_value is not None
            else "ANOVA completed."
        ),
        "metrics": {
            "groups": int(clean[request.group_column].nunique()),
            "observations": int(len(clean)),
            "effect_share": float(effect) if effect is not None else None,
            "f_statistic": f_statistic,
            "p_value": p_value,
            "decision": decision,
        },
        "tables": [
            _table("ANOVA table", anova_table),
            _table("Group means", group_means),
        ],
        "chart": {
            "kind": "bar",
            "title": "Group means",
            "x": group_means["group"].astype(str).tolist(),
            "y": group_means["mean"].tolist(),
        },
    }


def _anova_effect_rows(anova_table: pd.DataFrame) -> pd.DataFrame:
    rows = anova_table.copy()
    sum_sq_total = float(rows["sum_sq"].sum()) if "sum_sq" in rows else 0.0
    if sum_sq_total > 0:
        rows["effect_share"] = rows["sum_sq"].astype(float) / sum_sq_total
    else:
        rows["effect_share"] = None
    return rows.round(6)


def _first_feature(request: StatisticRequest, *, excluding: set[str], error: str) -> str:
    feature = next((item for item in request.features if item and item not in excluding), None)
    if not feature:
        raise ValueError(error)
    return feature


def run_two_way_anova(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    if not request.target or not request.group_column:
        raise ValueError("Two-way ANOVA requires a numeric target and a primary grouping column.")
    factor_b = _first_feature(
        request,
        excluding={request.target, request.group_column},
        error="Two-way ANOVA requires a second categorical factor in features.",
    )
    clean = frame[[request.target, request.group_column, factor_b]].copy()
    clean[request.target] = pd.to_numeric(clean[request.target], errors="coerce")
    clean = clean.dropna()
    if clean[request.group_column].nunique() < 2 or clean[factor_b].nunique() < 2:
        raise ValueError("Two-way ANOVA requires at least two levels in each factor.")
    if len(clean) < 8:
        raise ValueError("Two-way ANOVA requires at least eight complete observations.")
    cell_counts = clean.groupby([request.group_column, factor_b]).size()
    if (cell_counts < 2).any():
        raise ValueError("Two-way ANOVA requires at least two observations in every observed factor cell.")
    sm = _statsmodels_api()
    ols = _statsmodels_ols()

    formula = f'{quote(request.target)} ~ C({quote(request.group_column)}) * C({quote(factor_b)})'
    model = ols(formula, data=clean).fit()
    anova_table = sm.stats.anova_lm(model, typ=2).reset_index().rename(columns={"index": "term"})
    anova_table = _anova_effect_rows(anova_table)
    p_values = {
        str(row["term"]): float(row["PR(>F)"])
        for row in anova_table.to_dict(orient="records")
        if row.get("PR(>F)") is not None and not pd.isna(row.get("PR(>F)"))
    }
    interaction_term = next((term for term in p_values if ":" in term), "")
    primary_p = p_values.get(f"C({quote(request.group_column)})")
    secondary_p = p_values.get(f"C({quote(factor_b)})")
    interaction_p = p_values.get(interaction_term) if interaction_term else None
    p_candidates = [value for value in [primary_p, secondary_p, interaction_p] if value is not None]
    p_value = min(p_candidates) if p_candidates else None
    decision = "significant" if p_value is not None and p_value < request.alpha else "not_significant"
    cell_summary = (
        clean.groupby([request.group_column, factor_b])[request.target]
        .agg(["count", "mean", "std"])
        .reset_index()
        .rename(columns={request.group_column: "factor_a", factor_b: "factor_b"})
        .round(6)
    )
    top_cell = cell_summary.sort_values("mean", ascending=False).iloc[0]

    return {
        "analysis_type": "two_way_anova",
        "title": "Two-way ANOVA",
        "narrative": (
            f"Two-way ANOVA tests {request.group_column}, {factor_b}, and their interaction for {request.target}; "
            f"minimum term p-value is {p_value:.4g}. Highest mean cell is {top_cell['factor_a']} / {top_cell['factor_b']}."
            if p_value is not None
            else "Two-way ANOVA completed."
        ),
        "metrics": {
            "observations": int(len(clean)),
            "factor_a": request.group_column,
            "factor_b": factor_b,
            "factor_a_levels": int(clean[request.group_column].nunique()),
            "factor_b_levels": int(clean[factor_b].nunique()),
            "p_value": p_value,
            "factor_a_p_value": primary_p,
            "factor_b_p_value": secondary_p,
            "interaction_p_value": interaction_p,
            "decision": decision,
            "alpha": float(request.alpha),
        },
        "tables": [
            _table("Two-way ANOVA table", anova_table),
            _table("Factor cell means", cell_summary),
        ],
        "chart": {
            "kind": "bar",
            "title": f"{request.target} mean by {request.group_column} and {factor_b}",
            "x": [f"{row['factor_a']} / {row['factor_b']}" for row in cell_summary.to_dict(orient="records")],
            "y": cell_summary["mean"].tolist(),
        },
    }


def run_ancova(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    if not request.target or not request.group_column:
        raise ValueError("ANCOVA requires a numeric target and a grouping column.")
    covariate = _first_feature(
        request,
        excluding={request.target, request.group_column},
        error="ANCOVA requires a numeric covariate in features.",
    )
    clean = frame[[request.target, request.group_column, covariate]].copy()
    clean[request.target] = pd.to_numeric(clean[request.target], errors="coerce")
    clean[covariate] = pd.to_numeric(clean[covariate], errors="coerce")
    clean = clean.dropna()
    if clean[request.group_column].nunique() < 2:
        raise ValueError("ANCOVA requires at least two groups.")
    if float(clean[covariate].std(ddof=1)) == 0.0:
        raise ValueError("ANCOVA requires a non-constant numeric covariate.")
    if len(clean) < 8:
        raise ValueError("ANCOVA requires at least eight complete observations.")
    sm = _statsmodels_api()
    ols = _statsmodels_ols()

    formula = f'{quote(request.target)} ~ C({quote(request.group_column)}) + {quote(covariate)}'
    model = ols(formula, data=clean).fit()
    anova_table = sm.stats.anova_lm(model, typ=2).reset_index().rename(columns={"index": "term"})
    anova_table = _anova_effect_rows(anova_table)
    group_term = f"C({quote(request.group_column)})"
    covariate_term = quote(covariate)
    term_rows = {str(row["term"]): row for row in anova_table.to_dict(orient="records")}
    group_p = float(term_rows[group_term]["PR(>F)"]) if group_term in term_rows and not pd.isna(term_rows[group_term].get("PR(>F)")) else None
    covariate_p = float(term_rows[covariate_term]["PR(>F)"]) if covariate_term in term_rows and not pd.isna(term_rows[covariate_term].get("PR(>F)")) else None
    decision = "significant" if group_p is not None and group_p < request.alpha else "not_significant"
    covariate_mean = float(clean[covariate].mean())
    groups = sorted(clean[request.group_column].astype(str).unique().tolist())
    adjusted_rows = []
    for group in groups:
        prediction_frame = pd.DataFrame({request.group_column: [group], covariate: [covariate_mean]})
        adjusted_mean = float(model.predict(prediction_frame).iloc[0])
        observed_subset = clean.loc[clean[request.group_column].astype(str) == group, request.target]
        adjusted_rows.append(
            {
                "group": group,
                "observed_count": int(len(observed_subset)),
                "observed_mean": float(observed_subset.mean()),
                "adjusted_mean_at_covariate_mean": adjusted_mean,
            }
        )
    adjusted_summary = pd.DataFrame(adjusted_rows).round(6)

    return {
        "analysis_type": "ancova",
        "title": "ANCOVA",
        "narrative": (
            f"ANCOVA compares {request.target} across {request.group_column} while controlling for {covariate}; "
            f"group p-value is {group_p:.4g} and covariate p-value is {covariate_p:.4g}."
            if group_p is not None and covariate_p is not None
            else "ANCOVA completed."
        ),
        "metrics": {
            "observations": int(len(clean)),
            "groups": int(clean[request.group_column].nunique()),
            "covariate": covariate,
            "group_p_value": group_p,
            "covariate_p_value": covariate_p,
            "p_value": group_p,
            "alpha": float(request.alpha),
            "decision": decision,
        },
        "tables": [
            _table("ANCOVA table", anova_table),
            _table("Adjusted group means", adjusted_summary),
        ],
        "chart": {
            "kind": "bar",
            "title": f"Adjusted {request.target} mean by {request.group_column}",
            "x": adjusted_summary["group"].astype(str).tolist(),
            "y": adjusted_summary["adjusted_mean_at_covariate_mean"].tolist(),
        },
    }


def _grouped_numeric_samples(frame: pd.DataFrame, request: StatisticRequest, *, minimum_per_group: int = 2) -> tuple[pd.DataFrame, list[str], list[np.ndarray], pd.DataFrame]:
    if not request.target or not request.group_column:
        raise ValueError("This test requires a numeric target and grouping column.")
    clean = frame[[request.target, request.group_column]].copy()
    clean[request.target] = pd.to_numeric(clean[request.target], errors="coerce")
    clean = clean.dropna()
    labels: list[str] = []
    samples: list[np.ndarray] = []
    for label, subset in clean.groupby(request.group_column):
        values = subset[request.target].dropna().to_numpy(dtype=float)
        if len(values) >= minimum_per_group:
            labels.append(str(label))
            samples.append(values)
    if len(samples) < 2:
        raise ValueError("At least two groups with usable observations are required.")
    summary = (
        clean.loc[clean[request.group_column].astype(str).isin(labels)]
        .groupby(request.group_column)[request.target]
        .agg(["count", "mean", "median", "std", "var"])
        .reset_index()
        .rename(columns={request.group_column: "group"})
        .round(5)
    )
    return clean, labels, samples, summary


def run_variance_homogeneity(frame: pd.DataFrame, request: StatisticRequest, *, method: str) -> dict[str, Any]:
    clean, labels, samples, summary = _grouped_numeric_samples(frame, request)
    if method == "bartlett":
        statistic, p_value = stats.bartlett(*samples)
        title = "Bartlett Test"
        center = "mean-normality-sensitive"
    else:
        center = "median" if method == "brown_forsythe" else "mean"
        statistic, p_value = stats.levene(*samples, center=center)
        title = "Brown-Forsythe Test" if method == "brown_forsythe" else "Levene Test"
    decision = "variance_heterogeneous" if p_value < request.alpha else "variance_not_rejected"
    variance_ratio = float(max(np.var(sample, ddof=1) for sample in samples) / max(min(np.var(sample, ddof=1) for sample in samples), 1e-12))
    return {
        "analysis_type": method,
        "title": title,
        "narrative": (
            f"{title} returned p-value {p_value:.4g} across {len(samples)} groups. "
            f"{'Variance heterogeneity is strong enough to prefer Welch/nonparametric follow-up.' if decision == 'variance_heterogeneous' else 'Equal-variance methods remain plausible, subject to normality and sample-size checks.'}"
        ),
        "metrics": {
            "statistic": float(statistic),
            "p_value": float(p_value),
            "alpha": float(request.alpha),
            "decision": decision,
            "groups": len(samples),
            "observations": int(len(clean)),
            "center": center,
            "max_min_variance_ratio": variance_ratio,
        },
        "tables": [_table("Group variance summary", summary)],
        "chart": {
            "kind": "bar",
            "title": f"{request.target} variance by group",
            "x": summary["group"].astype(str).tolist(),
            "y": summary["var"].fillna(0).tolist(),
        },
    }


def run_welch_anova(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    clean, labels, samples, summary = _grouped_numeric_samples(frame, request)
    counts = np.asarray([len(sample) for sample in samples], dtype=float)
    means = np.asarray([float(np.mean(sample)) for sample in samples], dtype=float)
    variances = np.asarray([float(np.var(sample, ddof=1)) for sample in samples], dtype=float)
    if np.any(variances <= 0):
        raise ValueError("Welch ANOVA requires non-zero within-group variance.")
    weights = counts / variances
    weight_sum = float(weights.sum())
    weighted_mean = float(np.sum(weights * means) / weight_sum)
    groups = len(samples)
    numerator = float(np.sum(weights * (means - weighted_mean) ** 2) / max(groups - 1, 1))
    adjustment = 1 + (2 * (groups - 2) / (groups**2 - 1)) * float(np.sum(((1 - (weights / weight_sum)) ** 2) / (counts - 1)))
    f_statistic = numerator / adjustment
    df_num = float(groups - 1)
    df_den = float((groups**2 - 1) / (3 * np.sum(((1 - (weights / weight_sum)) ** 2) / (counts - 1))))
    p_value = float(stats.f.sf(f_statistic, df_num, df_den))
    decision = "significant" if p_value < request.alpha else "not_significant"
    top_group = summary.sort_values("mean", ascending=False).iloc[0]
    bottom_group = summary.sort_values("mean", ascending=True).iloc[0]
    return {
        "analysis_type": "welch_anova",
        "title": "Welch ANOVA",
        "narrative": (
            f"Welch ANOVA found F={f_statistic:.3f}, p-value {p_value:.4g}, df=({df_num:.1f}, {df_den:.1f}). "
            f"The highest-mean group is {top_group['group']} and the lowest is {bottom_group['group']}; "
            f"{'follow with post-hoc contrasts for unequal variances.' if decision == 'significant' else 'group mean evidence is limited under unequal-variance correction.'}"
        ),
        "metrics": {
            "f_statistic": f_statistic,
            "p_value": p_value,
            "alpha": float(request.alpha),
            "df_num": df_num,
            "df_den": df_den,
            "groups": groups,
            "observations": int(len(clean)),
            "decision": decision,
        },
        "tables": [_table("Welch group summary", summary)],
        "chart": {
            "kind": "bar",
            "title": f"{request.target} mean by group",
            "x": summary["group"].astype(str).tolist(),
            "y": summary["mean"].tolist(),
        },
    }


def run_logit(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    if not request.target or len(request.features) < 1:
        raise ValueError("Logit requires a binary target and at least one feature.")
    sm = _statsmodels_api()

    clean = frame[[request.target, *request.features]].copy().dropna()
    if not pd.api.types.is_numeric_dtype(clean[request.target]):
        target_codes, uniques = pd.factorize(clean[request.target].astype(str))
        if len(uniques) != 2:
            raise ValueError("Target must contain exactly two classes.")
        clean[request.target] = target_codes

    clean[request.features] = clean[request.features].apply(pd.to_numeric, errors="coerce")
    clean = clean.dropna()
    if clean[request.target].nunique() != 2:
        raise ValueError("Target must contain exactly two classes.")

    y = clean[request.target]
    x = sm.add_constant(clean[request.features], has_constant="add")
    model = sm.Logit(y, x).fit(disp=False)
    odds_ratios = np.exp(model.params)
    coefficient_table = pd.DataFrame(
        {
            "term": model.params.index.astype(str),
            "coefficient": model.params.values,
            "odds_ratio": odds_ratios.values,
            "std_error": model.bse.values,
            "z_value": model.tvalues.values,
            "p_value": model.pvalues.values,
        }
    ).round(5)
    feature_terms = coefficient_table[coefficient_table["term"] != "const"]
    strongest_term = (
        feature_terms.assign(distance_from_one=(feature_terms["odds_ratio"] - 1).abs())
        .sort_values("distance_from_one", ascending=False)
        .iloc[0]
        if not feature_terms.empty
        else None
    )

    return {
        "analysis_type": "logit",
        "title": "Logistic Regression",
        "narrative": (
            f"McFadden pseudo R^2 is {model.prsquared:.3f}. "
            f"The strongest odds-ratio signal is {strongest_term['term']} ({strongest_term['odds_ratio']:.3f}); "
            f"prioritize this feature when explaining the probability shift."
            if strongest_term is not None
            else f"McFadden pseudo R^2 is {model.prsquared:.3f}."
        ),
        "metrics": {
            "observations": int(model.nobs),
            "pseudo_r_squared": float(model.prsquared),
            "log_likelihood": float(model.llf),
            "strongest_term": str(strongest_term["term"]) if strongest_term is not None else None,
        },
        "tables": [_table("Logit coefficients", coefficient_table)],
        "chart": {
            "kind": "bar",
            "title": "Odds ratios",
            "x": feature_terms["term"].tolist(),
            "y": feature_terms["odds_ratio"].tolist(),
        },
    }


def run_pca(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    feature_columns = request.features or frame.select_dtypes(include=["number", "bool"]).columns[:6].tolist()
    if len(feature_columns) < 2:
        raise ValueError("PCA requires at least two numeric columns.")

    clean = _numeric_frame(frame, feature_columns)
    if len(clean) < 3:
        raise ValueError("Not enough complete rows for PCA.")

    scaled = StandardScaler().fit_transform(clean)
    components = max(2, min(request.components, len(feature_columns)))
    pca = PCA(n_components=components, random_state=42)
    transformed = pca.fit_transform(scaled)
    loadings = pd.DataFrame(
        pca.components_.T,
        index=feature_columns,
        columns=[f"PC{i + 1}" for i in range(components)],
    ).reset_index().rename(columns={"index": "feature"}).round(5)
    top_pc1 = loadings.assign(abs_pc1=loadings["PC1"].abs()).sort_values("abs_pc1", ascending=False).head(2)
    top_features = ", ".join(top_pc1["feature"].astype(str).tolist())

    return {
        "analysis_type": "pca",
        "title": "Principal Component Analysis",
        "narrative": (
            f"The first two components explain {pca.explained_variance_ratio_[:2].sum():.3f} of variance. "
            f"PC1 is driven most strongly by {top_features}."
        ),
        "metrics": {
            "observations": int(len(clean)),
            "components": int(components),
            "variance_pc1": float(pca.explained_variance_ratio_[0]),
            "variance_pc2": float(pca.explained_variance_ratio_[1]) if components > 1 else None,
        },
        "tables": [
            _table(
                "Explained variance",
                pd.DataFrame(
                    {
                        "component": [f"PC{i + 1}" for i in range(components)],
                        "explained_variance_ratio": pca.explained_variance_ratio_,
                    }
                ).round(5),
            ),
            _table("Feature loadings", loadings),
        ],
        "chart": {
            "kind": "scatter",
            "title": "PCA projection",
            "x_label": "PC1",
            "y_label": "PC2",
            "points": transformed[:160, :2].round(5).tolist(),
        },
    }


def run_kmeans(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    feature_columns = request.features or frame.select_dtypes(include=["number", "bool"]).columns[:5].tolist()
    if len(feature_columns) < 2:
        raise ValueError("KMeans requires at least two numeric columns.")

    clean = _numeric_frame(frame, feature_columns)
    clusters = max(2, min(request.clusters, 8))
    if len(clean) < max(clusters + 1, 10):
        raise ValueError("Not enough complete rows for clustering.")

    scaled = StandardScaler().fit_transform(clean)
    model = KMeans(n_clusters=clusters, n_init="auto", random_state=42)
    labels = model.fit_predict(scaled)
    projection = PCA(n_components=2, random_state=42).fit_transform(scaled)
    cluster_sizes = pd.Series(labels).value_counts().sort_index().reset_index()
    cluster_sizes.columns = ["cluster", "count"]
    centers = pd.DataFrame(model.cluster_centers_, columns=feature_columns).reset_index().rename(columns={"index": "cluster"}).round(5)
    label_column = _best_label_column(frame.loc[clean.index], exclude=set(feature_columns))
    cluster_members_rows: list[dict[str, Any]] = []
    if label_column:
        labelled = frame.loc[clean.index, [label_column]].copy()
        labelled["_cluster"] = labels
        distances = np.linalg.norm(scaled - model.cluster_centers_[labels], axis=1)
        labelled["_distance"] = distances
        for cluster_id in range(clusters):
            subset = labelled.loc[labelled["_cluster"] == cluster_id].sort_values("_distance").head(8)
            for rank, (_, row) in enumerate(subset.iterrows(), start=1):
                cluster_members_rows.append(
                    {
                        "cluster": int(cluster_id),
                        "rank": rank,
                        "member": str(row[label_column]),
                    }
                )

    largest_cluster = int(cluster_sizes["count"].max()) if not cluster_sizes.empty else 0
    largest_share = float(largest_cluster / len(clean)) if len(clean) else 0.0
    metrics = {
        "observations": int(len(clean)),
        "clusters": int(clusters),
        "inertia": float(model.inertia_),
        "largest_cluster_share": largest_share,
    }
    if len(clean) > clusters:
        metrics["silhouette"] = float(silhouette_score(scaled, labels))
    if label_column:
        metrics["member_label_column"] = label_column

    return {
        "analysis_type": "kmeans",
        "title": "KMeans Clustering",
        "narrative": (
            f"Clustering completed with {clusters} segments. "
            f"The largest cluster holds {largest_share:.1%} of usable rows"
            + (
                f", and silhouette is {metrics['silhouette']:.3f}."
                if "silhouette" in metrics
                else "."
            )
        ),
        "metrics": metrics,
        "tables": [
            _table("Cluster sizes", cluster_sizes),
            _table("Scaled cluster centers", centers),
            {
                "title": "Cluster members",
                "columns": ["cluster", "rank", "member"],
                "rows": cluster_members_rows,
            }
            if cluster_members_rows
            else {
                "title": "Cluster members",
                "columns": [],
                "rows": [],
            },
        ],
        "chart": {
            "kind": "cluster-scatter",
            "title": "Cluster map",
            "x_label": "PC1",
            "y_label": "PC2",
            "points": [
                [round(float(point[0]), 5), round(float(point[1]), 5), int(label)]
                for point, label in zip(projection[:220], labels[:220], strict=False)
            ],
        },
    }


def run_ttest(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    if not request.target or not request.group_column:
        raise ValueError("T-test requires a numeric target and a group column.")

    clean = frame[[request.target, request.group_column]].copy()
    clean[request.target] = pd.to_numeric(clean[request.target], errors="coerce")
    clean = clean.dropna()
    groups = clean[request.group_column].astype(str)
    available = groups.unique().tolist()
    if len(available) < 2:
        raise ValueError("T-test needs at least two groups.")

    group_a = request.group_a or available[0]
    group_b = request.group_b or available[1]
    sample_a = clean.loc[groups == group_a, request.target]
    sample_b = clean.loc[groups == group_b, request.target]
    if len(sample_a) < 2 or len(sample_b) < 2:
        raise ValueError("Each group needs at least two observations.")

    alpha = min(max(float(request.alpha), 0.0001), 0.2)
    alternative = _scipy_alternative(request.hypothesis)
    stat, p_value = stats.ttest_ind(sample_a, sample_b, equal_var=False, alternative=alternative)
    mean_difference = float(sample_a.mean() - sample_b.mean())
    var_a = float(sample_a.var(ddof=1))
    var_b = float(sample_b.var(ddof=1))
    se = float(np.sqrt((var_a / len(sample_a)) + (var_b / len(sample_b))))
    numerator = ((var_a / len(sample_a)) + (var_b / len(sample_b))) ** 2
    denominator = (
        ((var_a / len(sample_a)) ** 2) / max(len(sample_a) - 1, 1)
        + ((var_b / len(sample_b)) ** 2) / max(len(sample_b) - 1, 1)
    )
    degrees_of_freedom = float(numerator / denominator) if denominator > 0 else float(len(sample_a) + len(sample_b) - 2)
    critical = float(stats.t.ppf(1 - (alpha / 2), degrees_of_freedom))
    ci_low = float(mean_difference - (critical * se))
    ci_high = float(mean_difference + (critical * se))
    pooled_variance = (((len(sample_a) - 1) * var_a) + ((len(sample_b) - 1) * var_b)) / max(len(sample_a) + len(sample_b) - 2, 1)
    pooled_std = float(np.sqrt(pooled_variance)) if pooled_variance > 0 else None
    effect_size = float(mean_difference / pooled_std) if pooled_std not in (None, 0) else None
    decision = "significant" if p_value < alpha else "not_significant"
    table = pd.DataFrame(
        {
            "group": [group_a, group_b],
            "count": [len(sample_a), len(sample_b)],
            "mean": [sample_a.mean(), sample_b.mean()],
            "std": [sample_a.std(), sample_b.std()],
        }
    ).round(5)

    return {
        "analysis_type": "ttest",
        "title": "Welch Two-sample T-test",
        "narrative": (
            f"{group_a} vs {group_b} differs by {mean_difference:.4f} on {request.target} with p-value {p_value:.4g}, "
            f"{_confidence_level(alpha)}% CI [{ci_low:.4f}, {ci_high:.4f}], and effect size {effect_size:.3f}."
            if effect_size is not None
            else f"{group_a} vs {group_b} differs by {mean_difference:.4f} on {request.target} with p-value {p_value:.4g}."
        ),
        "metrics": {
            "t_statistic": float(stat),
            "p_value": float(p_value),
            "mean_difference": mean_difference,
            "ci_low": ci_low,
            "ci_high": ci_high,
            "effect_size": effect_size,
            "decision": decision,
            "alpha": alpha,
            "hypothesis": request.hypothesis,
            "group_a": group_a,
            "group_b": group_b,
        },
        "tables": [_table("Group statistics", table)],
        "chart": {
            "kind": "bar",
            "title": "Group means",
            "x": [group_a, group_b],
            "y": [float(sample_a.mean()), float(sample_b.mean())],
        },
    }


def run_one_sample_ttest(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    target = request.target or (request.features[0] if request.features else None)
    if not target:
        raise ValueError("One-sample t-test requires a numeric target column.")

    sample = pd.to_numeric(frame[target], errors="coerce").dropna()
    if len(sample) < 2:
        raise ValueError("One-sample t-test needs at least two numeric observations.")

    alpha = min(max(float(request.alpha), 0.0001), 0.2)
    test_value = float(request.test_value)
    alternative = _scipy_alternative(request.hypothesis)
    stat, p_value = stats.ttest_1samp(sample, popmean=test_value, alternative=alternative)
    mean_value = float(sample.mean())
    mean_difference = float(mean_value - test_value)
    std_value = float(sample.std(ddof=1))
    se = float(std_value / np.sqrt(len(sample)))
    df = float(len(sample) - 1)
    critical = float(stats.t.ppf(1 - (alpha / 2), df))
    ci_low = float(mean_difference - (critical * se))
    ci_high = float(mean_difference + (critical * se))
    effect_size = float(mean_difference / std_value) if std_value > 0 else None
    decision = "significant" if p_value < alpha else "not_significant"
    summary = pd.DataFrame(
        {
            "metric": ["sample_size", "sample_mean", "test_value", "mean_difference", "std", "std_error"],
            "value": [int(len(sample)), mean_value, test_value, mean_difference, std_value, se],
        }
    ).round(5)
    comparison = pd.DataFrame(
        {
            "target": [target],
            "t_statistic": [float(stat)],
            "p_value": [float(p_value)],
            "ci_low": [ci_low],
            "ci_high": [ci_high],
            "decision": [decision],
        }
    ).round(5)

    return {
        "analysis_type": "one_sample_ttest",
        "title": "One-sample T-test",
        "narrative": (
            f"{target} has mean {mean_value:.4f} versus test value {test_value:.4f}; "
            f"mean difference is {mean_difference:.4f} with p-value {p_value:.4g}. "
            f"Use this to decide whether the observed level is materially away from the benchmark."
        ),
        "metrics": {
            "sample_size": int(len(sample)),
            "mean": mean_value,
            "test_value": test_value,
            "mean_difference": mean_difference,
            "std": std_value,
            "std_error": se,
            "t_statistic": float(stat),
            "p_value": float(p_value),
            "ci_low": ci_low,
            "ci_high": ci_high,
            "effect_size": effect_size,
            "df": df,
            "alpha": alpha,
            "hypothesis": request.hypothesis,
            "decision": decision,
        },
        "tables": [
            _table("One-sample summary", summary),
            _table("One-sample test result", comparison),
        ],
        "chart": {
            "kind": "bar",
            "title": f"{target} mean vs test value",
            "x": ["sample_mean", "test_value"],
            "y": [mean_value, test_value],
        },
    }


def run_paired_ttest(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    clean, target, paired_feature = _paired_numeric_frame(frame, request, test_name="Paired t-test")
    alpha = min(max(float(request.alpha), 0.0001), 0.2)
    alternative = _scipy_alternative(request.hypothesis)
    left = clean[target]
    right = clean[paired_feature]
    differences = left - right
    stat, p_value = stats.ttest_rel(left, right, alternative=alternative)
    mean_difference = float(differences.mean())
    std_difference = float(differences.std(ddof=1))
    se = float(std_difference / np.sqrt(len(differences)))
    df = float(len(differences) - 1)
    critical = float(stats.t.ppf(1 - (alpha / 2), df))
    ci_low = float(mean_difference - (critical * se))
    ci_high = float(mean_difference + (critical * se))
    effect_size = float(mean_difference / std_difference) if std_difference > 0 else None
    decision = "significant" if p_value < alpha else "not_significant"
    summary = pd.DataFrame(
        {
            "field": [request.target, paired_feature, "paired_difference"],
            "count": [len(left), len(right), len(differences)],
            "mean": [float(left.mean()), float(right.mean()), mean_difference],
            "std": [float(left.std(ddof=1)), float(right.std(ddof=1)), std_difference],
        }
    ).round(5)
    comparison = pd.DataFrame(
        {
            "comparison": [f"{target} - {paired_feature}"],
            "mean_difference": [mean_difference],
            "t_statistic": [float(stat)],
            "p_value": [float(p_value)],
            "ci_low": [ci_low],
            "ci_high": [ci_high],
            "decision": [decision],
        }
    ).round(5)

    return {
        "analysis_type": "paired_ttest",
        "title": "Paired T-test",
        "narrative": (
            f"Paired difference {target} - {paired_feature} averages {mean_difference:.4f} "
            f"with p-value {p_value:.4g}. This isolates within-pair change rather than independent group contrast."
        ),
        "metrics": {
            "pairs": int(len(clean)),
            "left_field": target,
            "right_field": paired_feature,
            "mean_difference": mean_difference,
            "std_difference": std_difference,
            "std_error": se,
            "t_statistic": float(stat),
            "p_value": float(p_value),
            "ci_low": ci_low,
            "ci_high": ci_high,
            "effect_size": effect_size,
            "df": df,
            "alpha": alpha,
            "hypothesis": request.hypothesis,
            "decision": decision,
        },
        "tables": [
            _table("Paired field summary", summary),
            _table("Paired test result", comparison),
        ],
        "chart": {
            "kind": "bar",
            "title": "Paired means",
            "x": [target, paired_feature, "difference"],
            "y": [float(left.mean()), float(right.mean()), mean_difference],
        },
    }


def run_z_test_mean(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    target = request.target or (request.features[0] if request.features else None)
    if not target:
        raise ValueError("Z-test for mean requires a numeric target column.")

    sample = pd.to_numeric(frame[target], errors="coerce").dropna()
    if len(sample) < 30:
        raise ValueError("Z-test for mean needs at least 30 numeric observations.")

    alpha = min(max(float(request.alpha), 0.0001), 0.2)
    test_value = float(request.test_value)
    std_value = float(request.population_std) if request.population_std and request.population_std > 0 else float(sample.std(ddof=1))
    if std_value <= 0:
        raise ValueError("Z-test for mean requires non-zero standard deviation.")
    mean_value = float(sample.mean())
    mean_difference = float(mean_value - test_value)
    se = float(std_value / np.sqrt(len(sample)))
    z_stat = float(mean_difference / se)
    if request.hypothesis == "larger":
        p_value = float(stats.norm.sf(z_stat))
    elif request.hypothesis == "smaller":
        p_value = float(stats.norm.cdf(z_stat))
    else:
        p_value = float(2 * stats.norm.sf(abs(z_stat)))
    critical = float(stats.norm.ppf(1 - (alpha / 2)))
    ci_low = float(mean_difference - (critical * se))
    ci_high = float(mean_difference + (critical * se))
    effect_size = float(mean_difference / std_value)
    decision = "significant" if p_value < alpha else "not_significant"
    summary = pd.DataFrame(
        {
            "metric": ["sample_size", "sample_mean", "test_value", "mean_difference", "std_used", "std_error"],
            "value": [int(len(sample)), mean_value, test_value, mean_difference, std_value, se],
        }
    ).round(5)
    comparison = pd.DataFrame(
        {
            "target": [target],
            "z_statistic": [z_stat],
            "p_value": [p_value],
            "ci_low": [ci_low],
            "ci_high": [ci_high],
            "decision": [decision],
        }
    ).round(5)

    return {
        "analysis_type": "z_test_mean",
        "title": "Z-test for Mean",
        "narrative": (
            f"{target} has large-sample mean {mean_value:.4f} versus test value {test_value:.4f}; "
            f"z={z_stat:.3f}, p-value {p_value:.4g}. Use this when sample size is large and the standard error assumption is acceptable."
        ),
        "metrics": {
            "sample_size": int(len(sample)),
            "mean": mean_value,
            "test_value": test_value,
            "mean_difference": mean_difference,
            "std_used": std_value,
            "std_error": se,
            "z_statistic": z_stat,
            "p_value": p_value,
            "ci_low": ci_low,
            "ci_high": ci_high,
            "effect_size": effect_size,
            "alpha": alpha,
            "hypothesis": request.hypothesis,
            "population_std_supplied": bool(request.population_std and request.population_std > 0),
            "decision": decision,
        },
        "tables": [
            _table("Z-test summary", summary),
            _table("Z-test result", comparison),
        ],
        "chart": {
            "kind": "bar",
            "title": f"{target} mean vs test value",
            "x": ["sample_mean", "test_value"],
            "y": [mean_value, test_value],
        },
    }


def run_ab_test(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    selected, control_group, treatment_group = _two_group_frame(frame, request)
    alpha = min(max(float(request.alpha), 0.0001), 0.2)

    inferred_metric_type = request.metric_type
    if inferred_metric_type == "auto":
        try:
            _binary_metric_series(selected[request.target], request.success_value)
            inferred_metric_type = "binary"
        except ValueError:
            inferred_metric_type = "continuous"

    if inferred_metric_type == "binary":
        binary_metric, encoding_note = _binary_metric_series(
            selected[request.target],
            request.success_value,
        )
        clean = selected.loc[binary_metric.index].copy()
        clean[request.target] = binary_metric.astype(int)

        control = clean.loc[clean[request.group_column] == control_group, request.target]
        treatment = clean.loc[clean[request.group_column] == treatment_group, request.target]
        if len(control) < 2 or len(treatment) < 2:
            raise ValueError("Binary A/B test needs at least two observations in each variant.")

        control_successes = int(control.sum())
        treatment_successes = int(treatment.sum())
        control_rate = float(control.mean())
        treatment_rate = float(treatment.mean())
        uplift = float(treatment_rate - control_rate)
        relative_uplift = _relative_change(control_rate, treatment_rate)

        z_stat, p_value = proportions_ztest(
            count=[treatment_successes, control_successes],
            nobs=[len(treatment), len(control)],
            alternative=request.hypothesis,
        )
        ci_low, ci_high = confint_proportions_2indep(
            treatment_successes,
            len(treatment),
            control_successes,
            len(control),
            compare="diff",
            method="newcomb",
            alpha=alpha,
        )

        risk_ratio = float(treatment_rate / control_rate) if control_rate > 0 else None
        control_failures = len(control) - control_successes
        treatment_failures = len(treatment) - treatment_successes
        odds_ratio = None
        if control_successes > 0 and treatment_successes > 0 and control_failures > 0 and treatment_failures > 0:
            odds_ratio = float(
                (treatment_successes / treatment_failures)
                / (control_successes / control_failures)
            )

        effect_size = float(proportion_effectsize(treatment_rate, control_rate))
        try:
            observed_power = float(
                NormalIndPower().power(
                    effect_size=abs(effect_size),
                    nobs1=len(treatment),
                    ratio=len(control) / len(treatment),
                    alpha=alpha,
                    alternative=request.hypothesis,
                )
            )
            if not np.isfinite(observed_power):
                observed_power = None
        except Exception:
            observed_power = None

        group_stats = pd.DataFrame(
            {
                "group": [control_group, treatment_group],
                "sample_size": [len(control), len(treatment)],
                "successes": [control_successes, treatment_successes],
                "conversion_rate": [control_rate, treatment_rate],
            }
        ).round(5)
        comparison = pd.DataFrame(
            {
                "comparison": [f"{treatment_group} vs {control_group}"],
                "metric_type": ["binary"],
                "absolute_uplift": [uplift],
                "relative_uplift": [relative_uplift],
                "z_statistic": [float(z_stat)],
                "p_value": [float(p_value)],
                "ci_low": [float(ci_low)],
                "ci_high": [float(ci_high)],
                "risk_ratio": [risk_ratio],
                "odds_ratio": [odds_ratio],
                "decision": ["significant" if p_value < alpha else "not_significant"],
                "encoding_note": [encoding_note],
            }
        ).round(5)

        return {
            "analysis_type": "ab_test",
            "title": "A/B Test",
            "narrative": (
                f"Treatment {treatment_group} changed {request.target} by {uplift:.4f} "
                f"({relative_uplift * 100:.2f}% relative uplift) "
                f"with p-value {p_value:.4g}."
                if relative_uplift is not None
                else f"Treatment {treatment_group} changed {request.target} by {uplift:.4f} with p-value {p_value:.4g}."
            ),
            "metrics": {
                "metric_type": "binary",
                "control_group": control_group,
                "treatment_group": treatment_group,
                "control_sample_size": int(len(control)),
                "treatment_sample_size": int(len(treatment)),
                "control_rate": control_rate,
                "treatment_rate": treatment_rate,
                "absolute_uplift": uplift,
                "relative_uplift": relative_uplift,
                "z_statistic": float(z_stat),
                "p_value": float(p_value),
                "ci_low": float(ci_low),
                "ci_high": float(ci_high),
                "risk_ratio": risk_ratio,
                "odds_ratio": odds_ratio,
                "effect_size": effect_size,
                "observed_power": observed_power,
                "decision": "significant" if p_value < alpha else "not_significant",
                "alpha": alpha,
                "hypothesis": request.hypothesis,
            },
            "tables": [
                _table("Variant performance", group_stats),
                _table("A/B comparison", comparison),
            ],
            "chart": {
                "kind": "bar",
                "title": f"{request.target} conversion rate",
                "x": [control_group, treatment_group],
                "y": [control_rate, treatment_rate],
            },
        }

    clean = selected.copy()
    clean[request.target] = pd.to_numeric(clean[request.target], errors="coerce")
    clean = clean.dropna()
    control = clean.loc[clean[request.group_column] == control_group, request.target]
    treatment = clean.loc[clean[request.group_column] == treatment_group, request.target]
    if len(control) < 2 or len(treatment) < 2:
        raise ValueError("Continuous A/B test needs at least two observations in each variant.")

    control_mean = float(control.mean())
    treatment_mean = float(treatment.mean())
    uplift = float(treatment_mean - control_mean)
    relative_uplift = _relative_change(control_mean, treatment_mean)
    t_stat, p_value = stats.ttest_ind(
        treatment,
        control,
        equal_var=False,
        alternative=_scipy_alternative(request.hypothesis),
    )

    control_var = float(control.var(ddof=1))
    treatment_var = float(treatment.var(ddof=1))
    standard_error = float(np.sqrt((treatment_var / len(treatment)) + (control_var / len(control))))
    numerator = ((treatment_var / len(treatment)) + (control_var / len(control))) ** 2
    denominator = (
        ((treatment_var / len(treatment)) ** 2) / max(len(treatment) - 1, 1)
        + ((control_var / len(control)) ** 2) / max(len(control) - 1, 1)
    )
    degrees_of_freedom = float(numerator / denominator) if denominator > 0 else float(len(treatment) + len(control) - 2)
    t_critical = float(stats.t.ppf(1 - (alpha / 2), degrees_of_freedom))
    ci_low = float(uplift - (t_critical * standard_error))
    ci_high = float(uplift + (t_critical * standard_error))

    pooled_variance = (
        (((len(treatment) - 1) * treatment_var) + ((len(control) - 1) * control_var))
        / max(len(treatment) + len(control) - 2, 1)
    )
    pooled_std = float(np.sqrt(pooled_variance)) if pooled_variance > 0 else None
    effect_size = float(uplift / pooled_std) if pooled_std not in (None, 0) else None

    try:
        observed_power = (
            float(
                TTestIndPower().power(
                    effect_size=abs(effect_size),
                    nobs1=len(treatment),
                    ratio=len(control) / len(treatment),
                    alpha=alpha,
                    alternative=request.hypothesis,
                )
            )
            if effect_size is not None
            else None
        )
        if (
            observed_power is not None
            and not np.isfinite(observed_power)
            and effect_size is not None
            and request.hypothesis == "two-sided"
        ):
            observed_power = float(
                TTestIndPower().power(
                    effect_size=abs(effect_size),
                    nobs1=len(treatment),
                    ratio=len(control) / len(treatment),
                    alpha=alpha / 2,
                    alternative="larger",
                )
            )
        if observed_power is not None and not np.isfinite(observed_power):
            observed_power = None
    except Exception:
        observed_power = None

    group_stats = pd.DataFrame(
        {
            "group": [control_group, treatment_group],
            "sample_size": [len(control), len(treatment)],
            "mean": [control_mean, treatment_mean],
            "std": [float(control.std(ddof=1)), float(treatment.std(ddof=1))],
        }
    ).round(5)
    comparison = pd.DataFrame(
        {
            "comparison": [f"{treatment_group} vs {control_group}"],
            "metric_type": ["continuous"],
            "absolute_uplift": [uplift],
            "relative_uplift": [relative_uplift],
            "t_statistic": [float(t_stat)],
            "p_value": [float(p_value)],
            "ci_low": [ci_low],
            "ci_high": [ci_high],
            "effect_size": [effect_size],
            "decision": ["significant" if p_value < alpha else "not_significant"],
        }
    ).round(5)

    narrative = (
        f"Treatment {treatment_group} changed the mean of {request.target} by {uplift:.4f} "
        f"({relative_uplift * 100:.2f}% relative uplift) with p-value {p_value:.4g}."
        if relative_uplift is not None
        else f"Treatment {treatment_group} changed the mean of {request.target} by {uplift:.4f} with p-value {p_value:.4g}."
    )

    return {
        "analysis_type": "ab_test",
        "title": "A/B Test",
        "narrative": narrative,
        "metrics": {
            "metric_type": "continuous",
            "control_group": control_group,
            "treatment_group": treatment_group,
            "control_sample_size": int(len(control)),
            "treatment_sample_size": int(len(treatment)),
            "control_mean": control_mean,
            "treatment_mean": treatment_mean,
            "absolute_uplift": uplift,
            "relative_uplift": relative_uplift,
            "t_statistic": float(t_stat),
            "p_value": float(p_value),
            "ci_low": ci_low,
            "ci_high": ci_high,
            "effect_size": effect_size,
            "observed_power": observed_power,
            "decision": "significant" if p_value < alpha else "not_significant",
            "alpha": alpha,
            "hypothesis": request.hypothesis,
        },
        "tables": [
            _table("Variant performance", group_stats),
            _table("A/B comparison", comparison),
        ],
        "chart": {
            "kind": "bar",
            "title": f"{request.target} mean by variant",
            "x": [control_group, treatment_group],
            "y": [control_mean, treatment_mean],
        },
    }


def run_repeated_measures_anova(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    clean, columns = _repeated_numeric_frame(frame, request, test_name="Repeated measures ANOVA")
    values = clean[columns].to_numpy(dtype=float)
    subject_count, condition_count = values.shape
    grand_mean = float(values.mean())
    condition_means = values.mean(axis=0)
    subject_means = values.mean(axis=1)
    ss_total = float(np.square(values - grand_mean).sum())
    ss_conditions = float(subject_count * np.square(condition_means - grand_mean).sum())
    ss_subjects = float(condition_count * np.square(subject_means - grand_mean).sum())
    ss_error = float(ss_total - ss_conditions - ss_subjects)
    df_conditions = condition_count - 1
    df_subjects = subject_count - 1
    df_error = df_conditions * df_subjects
    if df_error <= 0 or ss_error <= 0:
        raise ValueError("Repeated measures ANOVA requires residual variation across subjects and conditions.")
    ms_conditions = ss_conditions / df_conditions
    ms_error = ss_error / df_error
    f_statistic = float(ms_conditions / ms_error)
    p_value = float(stats.f.sf(f_statistic, df_conditions, df_error))
    partial_eta_squared = float(ss_conditions / max(ss_conditions + ss_error, 1e-12))
    alpha = min(max(float(request.alpha), 0.0001), 0.2)
    decision = "significant" if p_value < alpha else "not_significant"
    condition_summary = pd.DataFrame(
        {
            "condition": columns,
            "mean": condition_means,
            "median": np.median(values, axis=0),
            "std": np.std(values, axis=0, ddof=1),
            "min": np.min(values, axis=0),
            "max": np.max(values, axis=0),
        }
    ).round(6)
    anova_table = pd.DataFrame(
        {
            "source": ["condition", "subject", "error", "total"],
            "sum_sq": [ss_conditions, ss_subjects, ss_error, ss_total],
            "df": [df_conditions, df_subjects, df_error, subject_count * condition_count - 1],
            "mean_sq": [ms_conditions, ss_subjects / df_subjects if df_subjects else None, ms_error, None],
            "f_statistic": [f_statistic, None, None, None],
            "p_value": [p_value, None, None, None],
        }
    ).round(6)

    return {
        "analysis_type": "repeated_measures_anova",
        "title": "Repeated Measures ANOVA",
        "narrative": (
            f"Repeated measures ANOVA compares {condition_count} within-subject numeric conditions across "
            f"{subject_count} complete subjects; F={f_statistic:.4f}, p-value {p_value:.4g}."
        ),
        "metrics": {
            "sample_size": int(subject_count),
            "condition_count": int(condition_count),
            "f_statistic": f_statistic,
            "p_value": p_value,
            "df_condition": int(df_conditions),
            "df_error": int(df_error),
            "partial_eta_squared": partial_eta_squared,
            "alpha": alpha,
            "decision": decision,
        },
        "tables": [
            _table("Repeated measures ANOVA table", anova_table),
            _table("Repeated condition summary", condition_summary),
        ],
        "chart": {
            "kind": "bar",
            "title": "Repeated condition means",
            "x": condition_summary["condition"].tolist(),
            "y": condition_summary["mean"].tolist(),
        },
    }


def run_chi_square(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    if not request.target or not request.group_column:
        raise ValueError("Chi-square requires two categorical columns: target and group_column.")

    table = _contingency_table(frame, request.group_column, request.target)
    chi2, p_value, dof, expected = stats.chi2_contingency(table)
    n = float(table.to_numpy().sum())
    min_dim = min(table.shape) - 1
    cramers_v = float(np.sqrt((chi2 / n) / max(min_dim, 1))) if n > 0 else None

    expected_frame = pd.DataFrame(expected, index=table.index, columns=table.columns).round(4)
    flat_rows = [
        {
            "group": str(row_label),
            "category": str(col_label),
            "count": int(table.loc[row_label, col_label]),
        }
        for row_label in table.index
        for col_label in table.columns
    ]

    return {
        "analysis_type": "chi_square",
        "title": "Chi-square Test of Independence",
        "narrative": f"The association between {request.group_column} and {request.target} has p-value {p_value:.4g}.",
        "metrics": {
            "chi2_statistic": float(chi2),
            "p_value": float(p_value),
            "degrees_of_freedom": int(dof),
            "cramers_v": cramers_v,
            "sample_size": int(n),
        },
        "tables": [
            _table("Observed contingency table", table.reset_index().rename(columns={table.index.name or "index": request.group_column})),
            _table("Expected contingency table", expected_frame.reset_index().rename(columns={expected_frame.index.name or "index": request.group_column})),
        ],
        "chart": {
            "kind": "bar",
            "title": f"{request.target} counts by {request.group_column}",
            "x": [f"{row['group']} / {row['category']}" for row in flat_rows[:24]],
            "y": [row["count"] for row in flat_rows[:24]],
        },
    }


def run_fisher_exact(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    if not request.target or not request.group_column:
        raise ValueError("Fisher exact test requires two categorical columns.")

    table = _contingency_table(frame, request.group_column, request.target)
    if table.shape != (2, 2):
        raise ValueError("Fisher exact test requires a 2x2 contingency table.")

    odds_ratio, p_value = stats.fisher_exact(table.to_numpy(), alternative=_scipy_alternative(request.hypothesis))
    rows = [
        {
            request.group_column: str(row_label),
            **{str(col_label): int(table.loc[row_label, col_label]) for col_label in table.columns},
        }
        for row_label in table.index
    ]

    return {
        "analysis_type": "fisher_exact",
        "title": "Fisher Exact Test",
        "narrative": f"The 2x2 exact test returned p-value {p_value:.4g} with odds ratio {odds_ratio:.4f}.",
        "metrics": {
            "odds_ratio": float(odds_ratio),
            "p_value": float(p_value),
            "sample_size": int(table.to_numpy().sum()),
        },
        "tables": [
            {
                "title": "2x2 contingency table",
                "columns": list(rows[0].keys()) if rows else [],
                "rows": rows,
            }
        ],
        "chart": {
            "kind": "bar",
            "title": "2x2 cell counts",
            "x": [f"{row_label} / {col_label}" for row_label in table.index for col_label in table.columns],
            "y": [int(table.loc[row_label, col_label]) for row_label in table.index for col_label in table.columns],
        },
    }


def run_mcnemar(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    clean, target, paired_feature = _paired_categorical_frame(
        frame,
        request,
        test_name="McNemar test",
        feature_error="one paired binary feature",
    )
    target_labels = _binary_category_labels(clean[target], column=target)
    paired_labels = _binary_category_labels(clean[paired_feature], column=paired_feature)
    if set(target_labels) != set(paired_labels):
        raise ValueError("McNemar test requires both paired binary columns to share the same two categories.")
    labels = sorted(target_labels, key=str)
    table = pd.crosstab(clean[paired_feature], clean[target]).reindex(index=labels, columns=labels, fill_value=0)
    b = int(table.loc[labels[0], labels[1]])
    c = int(table.loc[labels[1], labels[0]])
    discordant = b + c
    if discordant == 0:
        statistic = 0.0
        p_value = 1.0
    else:
        statistic = float((max(abs(b - c) - 1, 0) ** 2) / discordant)
        p_value = float(stats.binomtest(min(b, c), discordant, 0.5, alternative=_scipy_alternative(request.hypothesis)).pvalue)
    decision = "significant" if p_value < request.alpha else "not_significant"
    summary = pd.DataFrame(
        {
            "metric": ["pairs", "discordant_pairs", f"{paired_feature}_{labels[0]}_to_{target}_{labels[1]}", f"{paired_feature}_{labels[1]}_to_{target}_{labels[0]}", "p_value"],
            "value": [int(len(clean)), discordant, b, c, p_value],
        }
    ).round(6)

    return {
        "analysis_type": "mcnemar",
        "title": "McNemar Paired Binary Change Test",
        "narrative": (
            f"McNemar test compares paired binary columns {paired_feature} and {target}; "
            f"discordant counts are {b} versus {c}, exact p-value {p_value:.4g}."
        ),
        "metrics": {
            "sample_size": int(len(clean)),
            "discordant_pairs": discordant,
            "discordant_forward": b,
            "discordant_reverse": c,
            "chi_square_statistic": statistic,
            "p_value": p_value,
            "alpha": float(request.alpha),
            "hypothesis": request.hypothesis,
            "decision": decision,
        },
        "tables": [
            _table("McNemar paired transition summary", summary),
            _table("Paired binary transition table", _contingency_table_view(table, paired_feature)),
        ],
        "chart": {
            "kind": "bar",
            "title": "McNemar discordant pair counts",
            "x": [f"{paired_feature}:{labels[0]} -> {target}:{labels[1]}", f"{paired_feature}:{labels[1]} -> {target}:{labels[0]}"],
            "y": [b, c],
        },
    }


def run_cochran_q(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    if not request.target:
        raise ValueError("Cochran Q test requires a target binary column.")
    columns = list(dict.fromkeys([request.target, *[feature for feature in request.features if feature != request.target]]))
    if len(columns) < 3:
        raise ValueError("Cochran Q test requires at least three related binary columns.")
    clean = frame[columns].copy().dropna()
    if len(clean) < 2:
        raise ValueError("Cochran Q test needs at least two complete related observations.")

    positive_labels: dict[str, str] = {}
    binary_columns: dict[str, pd.Series] = {}
    for column in columns:
        indicator, positive_label = _binary_indicator_series(clean[column], column=column)
        binary_columns[column] = indicator
        positive_labels[column] = positive_label
    binary = pd.DataFrame(binary_columns, index=clean.index).astype(int)
    values = binary.to_numpy(dtype=float)
    k = values.shape[1]
    col_sums = values.sum(axis=0)
    row_sums = values.sum(axis=1)
    denominator = float(k * row_sums.sum() - np.square(row_sums).sum())
    if denominator <= 0:
        raise ValueError("Cochran Q test requires variation across related binary columns.")
    statistic = float((k - 1) * (k * np.square(col_sums).sum() - (col_sums.sum() ** 2)) / denominator)
    degrees_of_freedom = k - 1
    p_value = float(stats.chi2.sf(statistic, degrees_of_freedom))
    decision = "significant" if p_value < request.alpha else "not_significant"
    condition_summary = pd.DataFrame(
        {
            "condition": columns,
            "positive_label": [positive_labels[column] for column in columns],
            "positive_count": [int(col_sums[index]) for index in range(k)],
            "positive_rate": [float(col_sums[index] / len(binary)) for index in range(k)],
        }
    ).round(6)
    test_summary = pd.DataFrame(
        {
            "metric": ["conditions", "complete_subjects", "q_statistic", "degrees_of_freedom", "p_value"],
            "value": [k, int(len(binary)), statistic, degrees_of_freedom, p_value],
        }
    ).round(6)

    return {
        "analysis_type": "cochran_q",
        "title": "Cochran Q Related Binary Samples Test",
        "narrative": (
            f"Cochran Q compares {k} related binary columns across {len(binary)} complete rows; "
            f"Q={statistic:.4f}, p-value {p_value:.4g}."
        ),
        "metrics": {
            "sample_size": int(len(binary)),
            "condition_count": int(k),
            "q_statistic": statistic,
            "degrees_of_freedom": int(degrees_of_freedom),
            "p_value": p_value,
            "alpha": float(request.alpha),
            "decision": decision,
        },
        "tables": [
            _table("Cochran Q test summary", test_summary),
            _table("Related binary condition summary", condition_summary),
        ],
        "chart": {
            "kind": "bar",
            "title": "Positive rate by related condition",
            "x": condition_summary["condition"].tolist(),
            "y": condition_summary["positive_rate"].tolist(),
        },
    }


def run_cmh_test(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    if not request.target or not request.group_column:
        raise ValueError("CMH test requires target and group categorical columns.")
    strata_column = next((feature for feature in request.features if feature not in {request.target, request.group_column}), None)
    if not strata_column:
        raise ValueError("CMH test requires a stratification column in features.")
    clean = _categorical_frame(frame, [request.group_column, request.target, strata_column])
    if clean.empty:
        raise ValueError("No complete observations remain for the CMH test.")
    group_labels = sorted(clean[request.group_column].unique().tolist(), key=str)
    target_labels = sorted(clean[request.target].unique().tolist(), key=str)
    if len(group_labels) != 2 or len(target_labels) != 2:
        raise ValueError("CMH test requires 2x2 tables within strata.")

    stratum_rows: list[dict[str, Any]] = []
    numerator = 0.0
    variance_sum = 0.0
    common_or_numerator = 0.0
    common_or_denominator = 0.0
    total_n = 0
    for stratum, group in clean.groupby(strata_column, sort=True):
        table = pd.crosstab(group[request.group_column], group[request.target]).reindex(index=group_labels, columns=target_labels, fill_value=0)
        values = table.to_numpy(dtype=float)
        a, b, c, d = values.ravel()
        n = float(values.sum())
        if n <= 1:
            continue
        row1 = a + b
        row2 = c + d
        col1 = a + c
        col2 = b + d
        expected_a = row1 * col1 / n
        variance_a = (row1 * row2 * col1 * col2) / ((n**2) * (n - 1))
        numerator += a - expected_a
        variance_sum += variance_a
        common_or_numerator += (a * d) / n
        common_or_denominator += (b * c) / n
        total_n += int(n)
        stratum_rows.append(
            {
                strata_column: str(stratum),
                "sample_size": int(n),
                f"{group_labels[0]}_{target_labels[0]}": int(a),
                f"{group_labels[0]}_{target_labels[1]}": int(b),
                f"{group_labels[1]}_{target_labels[0]}": int(c),
                f"{group_labels[1]}_{target_labels[1]}": int(d),
                "stratum_odds_ratio": None if b * c == 0 else float((a * d) / (b * c)),
            }
        )
    if not stratum_rows or variance_sum <= 0:
        raise ValueError("CMH test requires at least one informative 2x2 stratum.")

    statistic = float((max(abs(numerator) - 0.5, 0) ** 2) / variance_sum)
    p_value = float(stats.chi2.sf(statistic, 1))
    common_odds_ratio = None if common_or_denominator <= 0 else float(common_or_numerator / common_or_denominator)
    decision = "significant" if p_value < request.alpha else "not_significant"
    summary = pd.DataFrame(
        {
            "metric": ["strata", "sample_size", "cmh_statistic", "p_value", "common_odds_ratio"],
            "value": [len(stratum_rows), total_n, statistic, p_value, common_odds_ratio],
        }
    ).round(6)
    stratum_frame = pd.DataFrame(stratum_rows).round(6)

    return {
        "analysis_type": "cmh_test",
        "title": "Cochran-Mantel-Haenszel Stratified 2x2 Test",
        "narrative": (
            f"CMH test compares {request.group_column} and {request.target} while controlling for {strata_column}; "
            f"statistic={statistic:.4f}, p-value {p_value:.4g}."
        ),
        "metrics": {
            "sample_size": int(total_n),
            "strata_count": int(len(stratum_rows)),
            "cmh_statistic": statistic,
            "p_value": p_value,
            "common_odds_ratio": common_odds_ratio,
            "degrees_of_freedom": 1,
            "alpha": float(request.alpha),
            "decision": decision,
        },
        "tables": [
            _table("CMH test summary", summary),
            _table("Stratified 2x2 tables", stratum_frame),
        ],
        "chart": {
            "kind": "bar",
            "title": "Stratum-specific odds ratios",
            "x": stratum_frame[strata_column].astype(str).tolist(),
            "y": [row["stratum_odds_ratio"] if row["stratum_odds_ratio"] is not None else 0 for row in stratum_rows],
        },
    }


def run_cramers_v(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    table = _categorical_association_table(frame, request, test_name="Cramer's V")
    chi2, p_value, dof, expected = stats.chi2_contingency(table, correction=False)
    n = float(table.to_numpy().sum())
    rows, columns = table.shape
    raw_denominator = max(min(rows - 1, columns - 1), 1)
    cramers_v = float(np.sqrt((chi2 / n) / raw_denominator)) if n > 0 else None

    corrected_v = None
    if n > 1:
        phi2 = chi2 / n
        phi2_corr = max(0.0, phi2 - ((columns - 1) * (rows - 1)) / (n - 1))
        rows_corr = rows - ((rows - 1) ** 2) / (n - 1)
        columns_corr = columns - ((columns - 1) ** 2) / (n - 1)
        corrected_denominator = min(columns_corr - 1, rows_corr - 1)
        if corrected_denominator > 0:
            corrected_v = float(np.sqrt(phi2_corr / corrected_denominator))

    expected_frame = pd.DataFrame(expected, index=table.index, columns=table.columns).round(4)
    flat_rows = _contingency_records(table, left_label=request.group_column, right_label=request.target)
    summary = pd.DataFrame(
        {
            "metric": ["cramers_v", "bias_corrected_cramers_v", "chi_square", "p_value", "degrees_of_freedom", "sample_size"],
            "value": [cramers_v, corrected_v, float(chi2), float(p_value), int(dof), int(n)],
        }
    ).round(6)

    return {
        "analysis_type": "cramers_v",
        "title": "Cramer's V Categorical Association Strength",
        "narrative": f"Cramer's V between {request.group_column} and {request.target} is {cramers_v:.4f}; p-value {p_value:.4g}.",
        "metrics": {
            "cramers_v": cramers_v,
            "bias_corrected_cramers_v": corrected_v,
            "strength": _association_strength_label(cramers_v),
            "chi2_statistic": float(chi2),
            "p_value": float(p_value),
            "degrees_of_freedom": int(dof),
            "sample_size": int(n),
            "decision": "significant" if p_value < request.alpha else "not_significant",
            "alpha": float(request.alpha),
        },
        "tables": [
            _table("Cramer's V summary", summary),
            _table("Observed contingency table", _contingency_table_view(table, request.group_column)),
            _table("Expected contingency table", _contingency_table_view(expected_frame, request.group_column)),
        ],
        "chart": {
            "kind": "bar",
            "title": f"{request.target} counts by {request.group_column}",
            "x": [f"{row[request.group_column]} / {row[request.target]}" for row in flat_rows[:24]],
            "y": [row["count"] for row in flat_rows[:24]],
        },
    }


def run_phi_coefficient(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    table = _categorical_association_table(frame, request, test_name="Phi coefficient")
    if table.shape != (2, 2):
        raise ValueError("Phi coefficient requires a 2x2 contingency table.")

    values = table.to_numpy(dtype=float)
    a, b, c, d = values.ravel()
    denominator = float(np.sqrt((a + b) * (c + d) * (a + c) * (b + d)))
    if denominator <= 0:
        raise ValueError("Phi coefficient requires non-empty row and column margins.")
    phi = float(((a * d) - (b * c)) / denominator)
    chi2, p_value, dof, expected = stats.chi2_contingency(table, correction=False)
    expected_frame = pd.DataFrame(expected, index=table.index, columns=table.columns).round(4)
    flat_rows = _contingency_records(table, left_label=request.group_column, right_label=request.target)
    odds_ratio = None if b * c == 0 else float((a * d) / (b * c))
    summary = pd.DataFrame(
        {
            "metric": ["phi", "absolute_phi", "chi_square", "p_value", "odds_ratio", "sample_size"],
            "value": [phi, abs(phi), float(chi2), float(p_value), odds_ratio, int(values.sum())],
        }
    ).round(6)

    return {
        "analysis_type": "phi_coefficient",
        "title": "Phi Coefficient for 2x2 Association",
        "narrative": f"Phi coefficient between {request.group_column} and {request.target} is {phi:.4f}; p-value {p_value:.4g}.",
        "metrics": {
            "phi": phi,
            "absolute_phi": abs(phi),
            "strength": _association_strength_label(phi),
            "chi2_statistic": float(chi2),
            "p_value": float(p_value),
            "degrees_of_freedom": int(dof),
            "odds_ratio": odds_ratio,
            "sample_size": int(values.sum()),
            "decision": "significant" if p_value < request.alpha else "not_significant",
            "alpha": float(request.alpha),
        },
        "tables": [
            _table("Phi coefficient summary", summary),
            _table("Observed 2x2 table", _contingency_table_view(table, request.group_column)),
            _table("Expected 2x2 table", _contingency_table_view(expected_frame, request.group_column)),
        ],
        "chart": {
            "kind": "bar",
            "title": "2x2 cell counts",
            "x": [f"{row[request.group_column]} / {row[request.target]}" for row in flat_rows],
            "y": [row["count"] for row in flat_rows],
        },
    }


def run_theils_u(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    table = _categorical_association_table(frame, request, test_name="Theil's U")
    forward_u, outcome_entropy, conditional_entropy = _theils_u_from_contingency(table)
    reverse_u, predictor_entropy, reverse_conditional_entropy = _theils_u_from_contingency(table.T)
    flat_rows = _contingency_records(table, left_label=request.group_column, right_label=request.target)
    summary = pd.DataFrame(
        {
            "direction": [
                f"{request.target} given {request.group_column}",
                f"{request.group_column} given {request.target}",
            ],
            "theils_u": [forward_u, reverse_u],
            "entropy": [outcome_entropy, predictor_entropy],
            "conditional_entropy": [conditional_entropy, reverse_conditional_entropy],
            "strength": [_association_strength_label(forward_u), _association_strength_label(reverse_u)],
        }
    ).round(6)

    return {
        "analysis_type": "theils_u",
        "title": "Theil's U Directional Categorical Association",
        "narrative": f"Knowing {request.group_column} reduces uncertainty in {request.target} by {forward_u:.2%}; reverse direction is {reverse_u:.2%}.",
        "metrics": {
            "theils_u": forward_u,
            "reverse_theils_u": reverse_u,
            "outcome_entropy": outcome_entropy,
            "conditional_entropy": conditional_entropy,
            "strength": _association_strength_label(forward_u),
            "sample_size": int(table.to_numpy().sum()),
            "decision": "directional_association" if forward_u >= 0.1 else "weak_directional_association",
        },
        "tables": [
            _table("Theil's U directional summary", summary),
            _table("Observed contingency table", _contingency_table_view(table, request.group_column)),
        ],
        "chart": {
            "kind": "bar",
            "title": "Directional uncertainty reduction",
            "x": [f"{request.target}|{request.group_column}", f"{request.group_column}|{request.target}"],
            "y": [forward_u, reverse_u],
            "details": flat_rows[:24],
        },
    }


def run_goodman_kruskal_lambda(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    table = _categorical_association_table(frame, request, test_name="Goodman-Kruskal Lambda")
    forward_lambda, errors_without, errors_with = _lambda_from_contingency(table)
    reverse_lambda, reverse_errors_without, reverse_errors_with = _lambda_from_contingency(table.T)
    summary = pd.DataFrame(
        {
            "direction": [
                f"{request.target} predicted by {request.group_column}",
                f"{request.group_column} predicted by {request.target}",
            ],
            "lambda": [forward_lambda, reverse_lambda],
            "errors_without_predictor": [errors_without, reverse_errors_without],
            "errors_with_predictor": [errors_with, reverse_errors_with],
            "strength": [_association_strength_label(forward_lambda), _association_strength_label(reverse_lambda)],
        }
    ).round(6)
    flat_rows = _contingency_records(table, left_label=request.group_column, right_label=request.target)

    return {
        "analysis_type": "goodman_kruskal_lambda",
        "title": "Goodman-Kruskal Lambda Predictive Association",
        "narrative": f"{request.group_column} reduces classification error for {request.target} by {forward_lambda:.2%}; reverse direction is {reverse_lambda:.2%}.",
        "metrics": {
            "lambda": forward_lambda,
            "reverse_lambda": reverse_lambda,
            "errors_without_predictor": errors_without,
            "errors_with_predictor": errors_with,
            "strength": _association_strength_label(forward_lambda),
            "sample_size": int(table.to_numpy().sum()),
            "decision": "predictive_association" if forward_lambda >= 0.1 else "weak_predictive_association",
        },
        "tables": [
            _table("Goodman-Kruskal Lambda summary", summary),
            _table("Observed contingency table", _contingency_table_view(table, request.group_column)),
        ],
        "chart": {
            "kind": "bar",
            "title": "Directional prediction error reduction",
            "x": [f"{request.target}|{request.group_column}", f"{request.group_column}|{request.target}"],
            "y": [forward_lambda, reverse_lambda],
            "details": flat_rows[:24],
        },
    }


def run_cohens_kappa(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    clean, target, paired_feature = _paired_categorical_frame(
        frame,
        request,
        test_name="Cohen's Kappa",
        feature_error="two categorical rating columns",
    )
    labels = sorted(set(clean[target].unique().tolist()) | set(clean[paired_feature].unique().tolist()), key=str)
    if len(labels) < 2:
        raise ValueError("Cohen's Kappa requires at least two rating categories.")
    table = pd.crosstab(clean[paired_feature], clean[target]).reindex(index=labels, columns=labels, fill_value=0)
    values = table.to_numpy(dtype=float)
    n = float(values.sum())
    if n <= 0:
        raise ValueError("Cohen's Kappa requires complete paired ratings.")
    observed_agreement = float(np.trace(values) / n)
    row_marginals = values.sum(axis=1)
    col_marginals = values.sum(axis=0)
    expected_agreement = float(np.dot(row_marginals, col_marginals) / (n**2))
    denominator = 1 - expected_agreement
    kappa = None if denominator <= 0 else float((observed_agreement - expected_agreement) / denominator)
    if kappa is None:
        z_statistic = None
        p_value = None
    else:
        standard_error = float(np.sqrt(max(observed_agreement * (1 - observed_agreement), 0) / max(n * (denominator**2), 1e-12)))
        if standard_error <= 0:
            z_statistic = None
            p_value = None
        else:
            z_statistic = float(kappa / standard_error)
            p_value = float(2 * stats.norm.sf(abs(z_statistic)))
    summary = pd.DataFrame(
        {
            "metric": ["pairs", "observed_agreement", "expected_agreement", "kappa", "p_value"],
            "value": [int(n), observed_agreement, expected_agreement, kappa, p_value],
        }
    ).round(6)
    label_summary = pd.DataFrame(
        {
            "rating_category": labels,
            f"{paired_feature}_count": [int(row_marginals[index]) for index in range(len(labels))],
            f"{target}_count": [int(col_marginals[index]) for index in range(len(labels))],
        }
    )

    return {
        "analysis_type": "cohens_kappa",
        "title": "Cohen's Kappa Inter-rater Agreement",
        "narrative": (
            f"Cohen's Kappa compares categorical ratings in {paired_feature} and {target}; "
            f"observed agreement is {observed_agreement:.2%}, kappa is {kappa if kappa is not None else 0:.4f}."
        ),
        "metrics": {
            "sample_size": int(n),
            "observed_agreement": observed_agreement,
            "expected_agreement": expected_agreement,
            "kappa": kappa,
            "z_statistic": z_statistic,
            "p_value": p_value,
            "strength": _kappa_strength_label(kappa),
            "decision": "substantial_agreement" if kappa is not None and kappa >= 0.61 else "limited_agreement",
        },
        "tables": [
            _table("Cohen's Kappa summary", summary),
            _table("Agreement matrix", _contingency_table_view(table, paired_feature)),
            _table("Rating marginal counts", label_summary),
        ],
        "chart": {
            "kind": "bar",
            "title": "Observed vs expected agreement",
            "x": ["observed_agreement", "expected_agreement"],
            "y": [observed_agreement, expected_agreement],
        },
    }


def run_mann_whitney(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    selected, group_a, group_b = _two_group_frame(frame, request)
    selected[request.target] = pd.to_numeric(selected[request.target], errors="coerce")
    selected = selected.dropna()
    sample_a = selected.loc[selected[request.group_column] == group_a, request.target]
    sample_b = selected.loc[selected[request.group_column] == group_b, request.target]
    if len(sample_a) < 2 or len(sample_b) < 2:
        raise ValueError("Mann-Whitney requires at least two observations per group.")

    statistic, p_value = stats.mannwhitneyu(sample_a, sample_b, alternative=_scipy_alternative(request.hypothesis))
    rank_biserial = 1 - (2 * statistic) / (len(sample_a) * len(sample_b))
    table = pd.DataFrame(
        {
            "group": [group_a, group_b],
            "count": [len(sample_a), len(sample_b)],
            "median": [sample_a.median(), sample_b.median()],
            "mean_rank_proxy": [sample_a.rank().mean(), sample_b.rank().mean()],
        }
    ).round(5)

    return {
        "analysis_type": "mann_whitney",
        "title": "Mann-Whitney U Test",
        "narrative": f"The nonparametric difference test returned p-value {p_value:.4g}.",
        "metrics": {
            "u_statistic": float(statistic),
            "p_value": float(p_value),
            "rank_biserial": float(rank_biserial),
            "sample_a_size": int(len(sample_a)),
            "sample_b_size": int(len(sample_b)),
        },
        "tables": [_table("Group distribution summary", table)],
        "chart": {
            "kind": "bar",
            "title": f"{request.target} median by group",
            "x": [group_a, group_b],
            "y": [float(sample_a.median()), float(sample_b.median())],
        },
    }


def run_wilcoxon_signed_rank(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    clean, target, paired_feature = _paired_numeric_frame(frame, request, test_name="Wilcoxon signed-rank test")
    alpha = min(max(float(request.alpha), 0.0001), 0.2)
    differences = clean[target] - clean[paired_feature]
    non_zero = differences[differences != 0]
    if len(non_zero) < 1:
        raise ValueError("Wilcoxon signed-rank test needs at least one non-zero paired difference.")

    statistic, p_value = stats.wilcoxon(non_zero, alternative=_scipy_alternative(request.hypothesis), zero_method="wilcox")
    median_difference = float(non_zero.median())
    positive_pairs = int((non_zero > 0).sum())
    negative_pairs = int((non_zero < 0).sum())
    rank_sum = float(stats.rankdata(abs(non_zero)).sum())
    signed_rank_effect = float((positive_pairs - negative_pairs) / len(non_zero))
    decision = "significant" if p_value < alpha else "not_significant"
    summary = pd.DataFrame(
        {
            "metric": ["pairs", "non_zero_pairs", "median_difference", "positive_pairs", "negative_pairs", "zero_pairs"],
            "value": [int(len(clean)), int(len(non_zero)), median_difference, positive_pairs, negative_pairs, int((differences == 0).sum())],
        }
    ).round(5)
    comparison = pd.DataFrame(
        {
            "comparison": [f"{target} - {paired_feature}"],
            "wilcoxon_statistic": [float(statistic)],
            "p_value": [float(p_value)],
            "rank_sum": [rank_sum],
            "signed_rank_effect": [signed_rank_effect],
            "decision": [decision],
        }
    ).round(5)

    return {
        "analysis_type": "wilcoxon_signed_rank",
        "title": "Wilcoxon Signed-rank Test",
        "narrative": (
            f"Wilcoxon signed-rank test compares paired {target} and {paired_feature}; "
            f"median paired difference is {median_difference:.4f}, p-value {p_value:.4g}."
        ),
        "metrics": {
            "pairs": int(len(clean)),
            "non_zero_pairs": int(len(non_zero)),
            "wilcoxon_statistic": float(statistic),
            "p_value": float(p_value),
            "median_difference": median_difference,
            "positive_pairs": positive_pairs,
            "negative_pairs": negative_pairs,
            "signed_rank_effect": signed_rank_effect,
            "alpha": alpha,
            "hypothesis": request.hypothesis,
            "decision": decision,
        },
        "tables": [
            _table("Wilcoxon paired summary", summary),
            _table("Wilcoxon test result", comparison),
        ],
        "chart": {
            "kind": "bar",
            "title": "Paired direction counts",
            "x": ["positive", "negative", "zero"],
            "y": [positive_pairs, negative_pairs, int((differences == 0).sum())],
        },
    }


def run_sign_test(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    clean, target, paired_feature = _paired_numeric_frame(frame, request, test_name="Sign test")
    alpha = min(max(float(request.alpha), 0.0001), 0.2)
    differences = clean[target] - clean[paired_feature]
    non_zero = differences[differences != 0]
    if len(non_zero) < 1:
        raise ValueError("Sign test needs at least one non-zero paired difference.")

    positive_pairs = int((non_zero > 0).sum())
    negative_pairs = int((non_zero < 0).sum())
    nobs = positive_pairs + negative_pairs
    if request.hypothesis == "larger":
        p_value = float(stats.binomtest(positive_pairs, nobs, 0.5, alternative="greater").pvalue)
    elif request.hypothesis == "smaller":
        p_value = float(stats.binomtest(positive_pairs, nobs, 0.5, alternative="less").pvalue)
    else:
        p_value = float(stats.binomtest(positive_pairs, nobs, 0.5, alternative="two-sided").pvalue)
    median_difference = float(non_zero.median())
    direction_balance = float((positive_pairs - negative_pairs) / nobs)
    decision = "significant" if p_value < alpha else "not_significant"
    summary = pd.DataFrame(
        {
            "direction": ["positive", "negative", "zero"],
            "count": [positive_pairs, negative_pairs, int((differences == 0).sum())],
        }
    )
    comparison = pd.DataFrame(
        {
            "comparison": [f"{target} - {paired_feature}"],
            "positive_pairs": [positive_pairs],
            "negative_pairs": [negative_pairs],
            "p_value": [p_value],
            "direction_balance": [direction_balance],
            "decision": [decision],
        }
    ).round(5)

    return {
        "analysis_type": "sign_test",
        "title": "Sign Test",
        "narrative": (
            f"Sign test found {positive_pairs} positive and {negative_pairs} negative paired differences "
            f"for {target} - {paired_feature}, p-value {p_value:.4g}."
        ),
        "metrics": {
            "pairs": int(len(clean)),
            "non_zero_pairs": nobs,
            "positive_pairs": positive_pairs,
            "negative_pairs": negative_pairs,
            "median_difference": median_difference,
            "direction_balance": direction_balance,
            "p_value": p_value,
            "alpha": alpha,
            "hypothesis": request.hypothesis,
            "decision": decision,
        },
        "tables": [
            _table("Sign direction counts", summary),
            _table("Sign test result", comparison),
        ],
        "chart": {
            "kind": "bar",
            "title": "Sign test direction counts",
            "x": summary["direction"].tolist(),
            "y": summary["count"].tolist(),
        },
    }


def run_kruskal(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    if not request.target or not request.group_column:
        raise ValueError("Kruskal-Wallis requires a numeric target and grouping column.")

    clean = frame[[request.target, request.group_column]].copy()
    clean[request.target] = pd.to_numeric(clean[request.target], errors="coerce")
    clean = clean.dropna()
    groups = []
    labels = []
    for label, subset in clean.groupby(request.group_column):
        if len(subset) >= 2:
            labels.append(str(label))
            groups.append(subset[request.target].to_numpy())
    if len(groups) < 2:
        raise ValueError("Kruskal-Wallis needs at least two groups with usable observations.")

    statistic, p_value = stats.kruskal(*groups)
    summary = (
        clean.groupby(request.group_column)[request.target]
        .agg(["count", "median", "mean"])
        .reset_index()
        .rename(columns={request.group_column: "group"})
        .round(5)
    )

    return {
        "analysis_type": "kruskal",
        "title": "Kruskal-Wallis Test",
        "narrative": f"The nonparametric multi-group test returned p-value {p_value:.4g}.",
        "metrics": {
            "h_statistic": float(statistic),
            "p_value": float(p_value),
            "groups": len(groups),
            "sample_size": int(len(clean)),
        },
        "tables": [_table("Group median summary", summary)],
        "chart": {
            "kind": "bar",
            "title": f"{request.target} median by group",
            "x": summary["group"].astype(str).tolist(),
            "y": summary["median"].tolist(),
        },
    }


def run_friedman(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    clean, columns = _repeated_numeric_frame(frame, request, test_name="Friedman test")
    alpha = min(max(float(request.alpha), 0.0001), 0.2)
    samples = [clean[column].to_numpy(dtype=float) for column in columns]
    statistic, p_value = stats.friedmanchisquare(*samples)
    condition_count = len(columns)
    subject_count = len(clean)
    kendalls_w = float(statistic / (subject_count * (condition_count - 1))) if subject_count > 0 and condition_count > 1 else None
    decision = "significant" if p_value < alpha else "not_significant"
    condition_summary = pd.DataFrame(
        {
            "condition": columns,
            "mean": [float(clean[column].mean()) for column in columns],
            "median": [float(clean[column].median()) for column in columns],
            "mean_rank": pd.DataFrame(
                stats.rankdata(clean[columns].to_numpy(dtype=float), axis=1),
                columns=columns,
            ).mean(axis=0).tolist(),
        }
    ).round(6)
    result_rows = pd.DataFrame(
        {
            "metric": ["friedman_chi_square", "p_value", "conditions", "complete_subjects", "kendalls_w"],
            "value": [float(statistic), float(p_value), condition_count, subject_count, kendalls_w],
        }
    ).round(6)

    return {
        "analysis_type": "friedman",
        "title": "Friedman Repeated Measures Test",
        "narrative": (
            f"Friedman test compares {condition_count} related numeric conditions across {subject_count} complete subjects; "
            f"chi-square={statistic:.4f}, p-value {p_value:.4g}."
        ),
        "metrics": {
            "sample_size": int(subject_count),
            "condition_count": int(condition_count),
            "friedman_chi_square": float(statistic),
            "p_value": float(p_value),
            "kendalls_w": kendalls_w,
            "alpha": alpha,
            "decision": decision,
        },
        "tables": [
            _table("Friedman test result", result_rows),
            _table("Repeated condition rank summary", condition_summary),
        ],
        "chart": {
            "kind": "bar",
            "title": "Repeated condition median",
            "x": condition_summary["condition"].tolist(),
            "y": condition_summary["median"].tolist(),
        },
    }


def run_mood_median(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    clean, _labels, samples, summary = _grouped_numeric_samples(frame, request)
    alpha = min(max(float(request.alpha), 0.0001), 0.2)
    statistic, p_value, grand_median, contingency = stats.median_test(*samples)
    decision = "significant" if p_value < alpha else "not_significant"
    contingency_frame = pd.DataFrame(
        contingency,
        index=["above_grand_median", "at_or_below_grand_median"],
        columns=summary["group"].astype(str).tolist(),
    ).reset_index(names="side")
    result_rows = pd.DataFrame(
        {
            "metric": ["chi_square", "p_value", "grand_median", "groups", "observations"],
            "value": [float(statistic), float(p_value), float(grand_median), int(len(samples)), int(len(clean))],
        }
    ).round(6)
    return {
        "analysis_type": "mood_median",
        "title": "Mood Median Test",
        "narrative": f"Mood median test compares group medians around grand median {grand_median:.4f}; p-value {p_value:.4g}.",
        "metrics": {
            "chi_square": float(statistic),
            "p_value": float(p_value),
            "grand_median": float(grand_median),
            "groups": int(len(samples)),
            "sample_size": int(len(clean)),
            "alpha": alpha,
            "decision": decision,
        },
        "tables": [
            _table("Mood median contingency", contingency_frame),
            _table("Mood median result", result_rows),
            _table("Group median summary", summary),
        ],
        "chart": {
            "kind": "bar",
            "title": f"{request.target} median by group",
            "x": summary["group"].astype(str).tolist(),
            "y": summary["median"].tolist(),
        },
    }


def run_ks_two_sample(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    selected, group_a, group_b = _two_group_frame(frame, request)
    selected[request.target] = pd.to_numeric(selected[request.target], errors="coerce")
    selected = selected.dropna()
    sample_a = selected.loc[selected[request.group_column] == group_a, request.target]
    sample_b = selected.loc[selected[request.group_column] == group_b, request.target]
    if len(sample_a) < 2 or len(sample_b) < 2:
        raise ValueError("Two-sample KS test requires at least two observations per group.")
    alpha = min(max(float(request.alpha), 0.0001), 0.2)
    statistic, p_value = stats.ks_2samp(sample_a, sample_b, alternative=_scipy_alternative(request.hypothesis), method="auto")
    decision = "significant" if p_value < alpha else "not_significant"
    summary = pd.DataFrame(
        {
            "group": [group_a, group_b],
            "count": [len(sample_a), len(sample_b)],
            "mean": [sample_a.mean(), sample_b.mean()],
            "median": [sample_a.median(), sample_b.median()],
            "p10": [sample_a.quantile(0.1), sample_b.quantile(0.1)],
            "p90": [sample_a.quantile(0.9), sample_b.quantile(0.9)],
        }
    ).round(6)
    return {
        "analysis_type": "ks_two_sample",
        "title": "Two-sample Kolmogorov-Smirnov Test",
        "narrative": f"Two-sample KS test compares the full {request.target} distribution between {group_a} and {group_b}; p-value {p_value:.4g}.",
        "metrics": {
            "ks_statistic": float(statistic),
            "p_value": float(p_value),
            "sample_a_size": int(len(sample_a)),
            "sample_b_size": int(len(sample_b)),
            "alpha": alpha,
            "hypothesis": request.hypothesis,
            "decision": decision,
        },
        "tables": [_table("Two-sample distribution summary", summary)],
        "chart": {
            "kind": "bar",
            "title": f"{request.target} median by group",
            "x": [group_a, group_b],
            "y": [float(sample_a.median()), float(sample_b.median())],
        },
    }


def run_runs_test(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    target = request.target or (request.features[0] if request.features else None)
    if not target:
        raise ValueError("Runs test requires a numeric target column.")
    if request.group_column:
        clean = frame[[request.group_column, target]].copy()
        clean[target] = pd.to_numeric(clean[target], errors="coerce")
        order = pd.to_datetime(clean[request.group_column], errors="coerce")
        if order.notna().any():
            clean["_order"] = order
        else:
            clean["_order"] = pd.to_numeric(clean[request.group_column], errors="coerce")
        clean = clean.dropna(subset=[target, "_order"]).sort_values("_order")
    else:
        clean = frame[[target]].copy()
        clean[target] = pd.to_numeric(clean[target], errors="coerce")
        clean = clean.dropna()
    if len(clean) < 10:
        raise ValueError("Runs test requires at least 10 ordered numeric observations.")
    median = float(clean[target].median())
    signs = np.where(clean[target].to_numpy(dtype=float) > median, 1, 0)
    if signs.min() == signs.max():
        raise ValueError("Runs test requires observations on both sides of the median.")
    runs = int(1 + np.sum(signs[1:] != signs[:-1]))
    n_high = int(signs.sum())
    n_low = int(len(signs) - n_high)
    expected_runs = float(1 + (2 * n_high * n_low) / (n_high + n_low))
    variance_runs = float((2 * n_high * n_low * (2 * n_high * n_low - n_high - n_low)) / (((n_high + n_low) ** 2) * (n_high + n_low - 1)))
    z_score = float((runs - expected_runs) / np.sqrt(variance_runs))
    p_value = float(2 * stats.norm.sf(abs(z_score)))
    alpha = min(max(float(request.alpha), 0.0001), 0.2)
    decision = "non_random_sequence" if p_value < alpha else "randomness_not_rejected"
    rows = pd.DataFrame(
        {
            "metric": ["runs", "expected_runs", "z_score", "p_value", "above_median", "at_or_below_median"],
            "value": [runs, expected_runs, z_score, p_value, n_high, n_low],
        }
    ).round(6)
    return {
        "analysis_type": "runs_test",
        "title": "Runs Test",
        "narrative": f"Runs test checks whether ordered {target} values randomly alternate around median {median:.4f}; p-value {p_value:.4g}.",
        "metrics": {
            "sample_size": int(len(clean)),
            "median": median,
            "runs": runs,
            "expected_runs": expected_runs,
            "z_score": z_score,
            "p_value": p_value,
            "alpha": alpha,
            "decision": decision,
        },
        "tables": [_table("Runs test result", rows)],
        "chart": {
            "kind": "bar",
            "title": "Runs test side counts",
            "x": ["above_median", "at_or_below_median"],
            "y": [n_high, n_low],
        },
    }


def run_median_test(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    clean, _labels, samples, summary = _grouped_numeric_samples(frame, request)
    alpha = min(max(float(request.alpha), 0.0001), 0.2)
    statistic, p_value, grand_median, contingency = stats.median_test(*samples)
    decision = "significant" if p_value < alpha else "not_significant"
    contingency_frame = pd.DataFrame(
        contingency,
        index=["above_grand_median", "at_or_below_grand_median"],
        columns=summary["group"].astype(str).tolist(),
    ).reset_index(names="side")
    comparison = pd.DataFrame(
        {
            "metric": ["chi_square", "p_value", "grand_median", "groups", "observations"],
            "value": [float(statistic), float(p_value), float(grand_median), int(len(samples)), int(len(clean))],
        }
    ).round(5)

    return {
        "analysis_type": "median_test",
        "title": "Median Test",
        "narrative": (
            f"Median test compares group medians around grand median {grand_median:.4f}; "
            f"p-value {p_value:.4g} across {len(samples)} groups."
        ),
        "metrics": {
            "chi_square": float(statistic),
            "p_value": float(p_value),
            "grand_median": float(grand_median),
            "groups": int(len(samples)),
            "observations": int(len(clean)),
            "alpha": alpha,
            "decision": decision,
        },
        "tables": [
            _table("Median test contingency", contingency_frame),
            _table("Median test result", comparison),
            _table("Group median summary", summary),
        ],
        "chart": {
            "kind": "bar",
            "title": f"{request.target} median by group",
            "x": summary["group"].astype(str).tolist(),
            "y": summary["median"].tolist(),
        },
    }


def run_fligner_killeen(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    clean, _labels, samples, summary = _grouped_numeric_samples(frame, request)
    alpha = min(max(float(request.alpha), 0.0001), 0.2)
    statistic, p_value = stats.fligner(*samples)
    decision = "variance_heterogeneous" if p_value < alpha else "variance_not_rejected"
    variance_values = [float(np.var(sample, ddof=1)) for sample in samples]
    variance_ratio = float(max(variance_values) / max(min(variance_values), 1e-12))
    comparison = pd.DataFrame(
        {
            "metric": ["fligner_killeen_statistic", "p_value", "groups", "observations", "max_min_variance_ratio"],
            "value": [float(statistic), float(p_value), int(len(samples)), int(len(clean)), variance_ratio],
        }
    ).round(5)

    return {
        "analysis_type": "fligner_killeen",
        "title": "Fligner-Killeen Test",
        "narrative": (
            f"Fligner-Killeen robust variance test returned p-value {p_value:.4g} across {len(samples)} groups. "
            f"{'Variance heterogeneity is strong; prefer robust or nonparametric follow-up.' if decision == 'variance_heterogeneous' else 'Variance heterogeneity is not strongly contradicted by this robust test.'}"
        ),
        "metrics": {
            "statistic": float(statistic),
            "p_value": float(p_value),
            "alpha": alpha,
            "decision": decision,
            "groups": int(len(samples)),
            "observations": int(len(clean)),
            "max_min_variance_ratio": variance_ratio,
            "center": "median-rank-robust",
        },
        "tables": [
            _table("Fligner-Killeen result", comparison),
            _table("Group variance summary", summary),
        ],
        "chart": {
            "kind": "bar",
            "title": f"{request.target} variance by group",
            "x": summary["group"].astype(str).tolist(),
            "y": summary["var"].fillna(0).tolist(),
        },
    }


def run_permutation_test(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    selected, group_a, group_b = _two_group_frame(frame, request)
    selected[request.target] = pd.to_numeric(selected[request.target], errors="coerce")
    selected = selected.dropna()
    sample_a = selected.loc[selected[request.group_column] == group_a, request.target].to_numpy(dtype=float)
    sample_b = selected.loc[selected[request.group_column] == group_b, request.target].to_numpy(dtype=float)
    if len(sample_a) < 2 or len(sample_b) < 2:
        raise ValueError("Permutation test requires at least two observations per group.")
    iterations = max(100, min(int(request.bootstrap_iterations or 1000), 10000))
    rng = np.random.default_rng(42)
    observed_diff = float(np.mean(sample_b) - np.mean(sample_a))
    pooled = np.concatenate([sample_a, sample_b])
    extreme = 0
    permuted_diffs: list[float] = []
    for _ in range(iterations):
        shuffled = rng.permutation(pooled)
        perm_a = shuffled[: len(sample_a)]
        perm_b = shuffled[len(sample_a) :]
        diff = float(np.mean(perm_b) - np.mean(perm_a))
        permuted_diffs.append(diff)
        if request.hypothesis == "larger":
            extreme += int(diff >= observed_diff)
        elif request.hypothesis == "smaller":
            extreme += int(diff <= observed_diff)
        else:
            extreme += int(abs(diff) >= abs(observed_diff))
    p_value = float((extreme + 1) / (iterations + 1))
    alpha = min(max(float(request.alpha), 0.0001), 0.2)
    decision = "significant" if p_value < alpha else "not_significant"
    summary = pd.DataFrame(
        {
            "group": [group_a, group_b],
            "count": [len(sample_a), len(sample_b)],
            "mean": [float(np.mean(sample_a)), float(np.mean(sample_b))],
            "median": [float(np.median(sample_a)), float(np.median(sample_b))],
        }
    ).round(6)
    result_rows = pd.DataFrame(
        {
            "metric": ["observed_mean_difference_b_minus_a", "p_value", "iterations", "permutation_diff_p05", "permutation_diff_p95"],
            "value": [
                observed_diff,
                p_value,
                iterations,
                float(np.quantile(permuted_diffs, 0.05)),
                float(np.quantile(permuted_diffs, 0.95)),
            ],
        }
    ).round(6)
    return {
        "analysis_type": "permutation_test",
        "title": "Permutation Test",
        "narrative": f"Permutation test estimates the group mean-difference null for {request.target}; observed B-A difference is {observed_diff:.4f}, p-value {p_value:.4g}.",
        "metrics": {
            "sample_a_size": int(len(sample_a)),
            "sample_b_size": int(len(sample_b)),
            "observed_mean_difference": observed_diff,
            "p_value": p_value,
            "iterations": int(iterations),
            "alpha": alpha,
            "hypothesis": request.hypothesis,
            "decision": decision,
        },
        "tables": [
            _table("Permutation group summary", summary),
            _table("Permutation test result", result_rows),
        ],
        "chart": {
            "kind": "bar",
            "title": f"{request.target} mean by group",
            "x": [group_a, group_b],
            "y": [float(np.mean(sample_a)), float(np.mean(sample_b))],
        },
    }


def run_bootstrap_ci(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    target = request.target or (request.features[0] if request.features else None)
    if not target:
        raise ValueError("Bootstrap CI requires a numeric target column.")
    series = pd.to_numeric(frame[target], errors="coerce").dropna()
    if len(series) < 5:
        raise ValueError("Bootstrap CI requires at least 5 numeric observations.")
    if float(series.std(ddof=1)) == 0.0:
        raise ValueError("Bootstrap CI requires non-constant numeric observations.")
    iterations = max(100, min(int(request.bootstrap_iterations or 1000), 10000))
    alpha = min(max(float(request.alpha), 0.0001), 0.2)
    rng = np.random.default_rng(42)
    values = series.to_numpy(dtype=float)
    sample_size = len(values)
    bootstrap_means = np.empty(iterations, dtype=float)
    for index in range(iterations):
        bootstrap_means[index] = float(np.mean(rng.choice(values, size=sample_size, replace=True)))
    ci_low = float(np.quantile(bootstrap_means, alpha / 2))
    ci_high = float(np.quantile(bootstrap_means, 1 - alpha / 2))
    mean_value = float(np.mean(values))
    median_value = float(np.median(values))
    rows = pd.DataFrame(
        {
            "metric": ["mean", "median", "ci_low", "ci_high", "iterations", "alpha"],
            "value": [mean_value, median_value, ci_low, ci_high, iterations, alpha],
        }
    ).round(6)
    return {
        "analysis_type": "bootstrap_ci",
        "title": "Bootstrap Confidence Interval",
        "narrative": f"Bootstrap CI for mean {target} is [{ci_low:.4f}, {ci_high:.4f}] using {iterations} resamples.",
        "metrics": {
            "sample_size": int(sample_size),
            "mean": mean_value,
            "median": median_value,
            "ci_low": ci_low,
            "ci_high": ci_high,
            "iterations": int(iterations),
            "alpha": alpha,
        },
        "tables": [_table("Bootstrap CI summary", rows)],
        "chart": {
            "kind": "bar",
            "title": f"{target} bootstrap mean interval",
            "x": ["ci_low", "mean", "ci_high"],
            "y": [ci_low, mean_value, ci_high],
        },
    }


def run_poisson_glm(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    if not request.target or len(request.features) < 1:
        raise ValueError("Poisson GLM requires a count target and at least one feature.")
    sm = _statsmodels_api()

    clean = frame[[request.target, *request.features]].copy()
    clean[request.target] = pd.to_numeric(clean[request.target], errors="coerce")
    clean[request.features] = clean[request.features].apply(pd.to_numeric, errors="coerce")
    clean = clean.dropna()
    if (clean[request.target] < 0).any():
        raise ValueError("Poisson GLM target must be non-negative.")
    if len(clean) < max(20, len(request.features) + 5):
        raise ValueError("Not enough complete rows to fit a Poisson GLM.")

    y = clean[request.target]
    x = sm.add_constant(clean[request.features], has_constant="add")
    model = sm.GLM(y, x, family=sm.families.Poisson()).fit()
    coefficients = pd.DataFrame(
        {
            "term": model.params.index.astype(str),
            "coefficient": model.params.values,
            "rate_ratio": np.exp(model.params.values),
            "std_error": model.bse.values,
            "z_value": model.tvalues.values,
            "p_value": model.pvalues.values,
        }
    ).round(5)
    feature_terms = coefficients[coefficients["term"] != "const"]

    return {
        "analysis_type": "poisson_glm",
        "title": "Poisson GLM",
        "narrative": f"The count model converged with pseudo R^2-style deviance improvement captured by deviance {model.deviance:.3f}.",
        "metrics": {
            "observations": int(model.nobs),
            "deviance": float(model.deviance),
            "pearson_chi2": float(model.pearson_chi2),
            "aic": float(model.aic),
            "bic": float(model.bic_llf),
        },
        "tables": [_table("Poisson coefficient table", coefficients)],
        "chart": {
            "kind": "bar",
            "title": "Poisson rate ratios",
            "x": feature_terms["term"].tolist(),
            "y": feature_terms["rate_ratio"].tolist(),
        },
    }


def _classification_result_metrics(y_test: pd.Series, predictions: np.ndarray, probabilities: np.ndarray | None = None) -> dict[str, Any]:
    metrics = {
        "sample_size": int(len(y_test)),
        "accuracy": float(accuracy_score(y_test, predictions)),
        "precision": float(precision_score(y_test, predictions, zero_division=0)),
        "recall": float(recall_score(y_test, predictions, zero_division=0)),
        "f1": float(f1_score(y_test, predictions, zero_division=0)),
    }
    if probabilities is not None:
        try:
            metrics["roc_auc"] = float(roc_auc_score(y_test, probabilities))
        except Exception:
            metrics["roc_auc"] = None
    return metrics


def _regression_result_metrics(y_test: pd.Series, predictions: np.ndarray) -> dict[str, Any]:
    mse = float(mean_squared_error(y_test, predictions))
    return {
        "sample_size": int(len(y_test)),
        "mae": float(mean_absolute_error(y_test, predictions)),
        "rmse": float(np.sqrt(mse)),
        "r_squared": float(r2_score(y_test, predictions)),
        "mean_actual": float(pd.Series(y_test).mean()),
        "mean_prediction": float(pd.Series(predictions).mean()),
    }


def run_random_forest(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    prepared = _prepare_supervised_learning_frame(frame, request)
    metric_type = prepared["metric_type"]
    if metric_type == "binary":
        model = RandomForestClassifier(n_estimators=300, random_state=42, class_weight="balanced")
        model.fit(prepared["x_train"], prepared["y_train"])
        predictions = model.predict(prepared["x_test"])
        probabilities = model.predict_proba(prepared["x_test"])[:, 1] if hasattr(model, "predict_proba") else None
        metrics = _classification_result_metrics(prepared["y_test"], predictions, probabilities)
        permutation = permutation_importance(model, prepared["x_test"], prepared["y_test"], n_repeats=5, random_state=42, scoring="f1")
        importance_table = _feature_importance_rows(prepared["x_test"].columns.astype(str).tolist(), model.feature_importances_)
        permutation_table = _feature_importance_rows(prepared["x_test"].columns.astype(str).tolist(), permutation.importances_mean)
        top_features = "、".join(importance_table["feature"].head(3).tolist())
        narrative = (
            f"随机森林已完成二分类建模，测试集准确率 {metrics['accuracy']:.3f}、F1 {metrics['f1']:.3f}"
            + (f"、AUC {metrics['roc_auc']:.3f}" if metrics.get("roc_auc") is not None else "")
            + f"。当前最重要的特征是 {top_features}。业务上应优先把这些变量当成第一批风险或机会驱动因素去复盘。"
        )
        chart = {
            "kind": "bar",
            "title": "随机森林特征重要性",
            "x": importance_table["feature"].tolist(),
            "y": importance_table["importance"].tolist(),
        }
    else:
        model = RandomForestRegressor(n_estimators=300, random_state=42)
        model.fit(prepared["x_train"], prepared["y_train"])
        predictions = model.predict(prepared["x_test"])
        metrics = _regression_result_metrics(prepared["y_test"], predictions)
        permutation = permutation_importance(model, prepared["x_test"], prepared["y_test"], n_repeats=5, random_state=42, scoring="r2")
        importance_table = _feature_importance_rows(prepared["x_test"].columns.astype(str).tolist(), model.feature_importances_)
        permutation_table = _feature_importance_rows(prepared["x_test"].columns.astype(str).tolist(), permutation.importances_mean)
        top_features = "、".join(importance_table["feature"].head(3).tolist())
        narrative = (
            f"随机森林已完成连续目标建模，测试集 R² {metrics['r_squared']:.3f}、RMSE {metrics['rmse']:.3f}、MAE {metrics['mae']:.3f}。"
            f"当前最重要的特征是 {top_features}。业务上应优先检查这些变量对应的结构、流程或资源差异。"
        )
        chart = {
            "kind": "bar",
            "title": "随机森林特征重要性",
            "x": importance_table["feature"].tolist(),
            "y": importance_table["importance"].tolist(),
        }

    metrics["target"] = prepared["target"]
    metrics["feature_count"] = int(prepared["x_train"].shape[1])
    return {
        "analysis_type": "random_forest",
        "title": "随机森林模型",
        "narrative": narrative,
        "metrics": metrics,
        "tables": [
            _table("模型评估指标", _supervised_metric_table(metrics)),
            _table("随机森林特征重要性", importance_table),
            _table("置换重要性", permutation_table),
        ],
        "chart": chart,
    }


def _run_mlp_model(frame: pd.DataFrame, request: StatisticRequest, hidden_layers: tuple[int, ...], analysis_type: str, title: str) -> dict[str, Any]:
    prepared = _prepare_supervised_learning_frame(frame, request)
    scaler = StandardScaler()
    x_train = scaler.fit_transform(prepared["x_train"])
    x_test = scaler.transform(prepared["x_test"])
    metric_type = prepared["metric_type"]
    if metric_type == "binary":
        model = MLPClassifier(hidden_layer_sizes=hidden_layers, max_iter=500, random_state=42, early_stopping=True)
        model.fit(x_train, prepared["y_train"])
        predictions = model.predict(x_test)
        probabilities = model.predict_proba(x_test)[:, 1] if hasattr(model, "predict_proba") else None
        metrics = _classification_result_metrics(prepared["y_test"], predictions, probabilities)
        permutation = permutation_importance(model, x_test, prepared["y_test"], n_repeats=5, random_state=42, scoring="f1")
        importance_table = _feature_importance_rows(prepared["x_test"].columns.astype(str).tolist(), permutation.importances_mean)
        top_features = "、".join(importance_table["feature"].head(3).tolist())
        relation_phrase = "更复杂的非线性关系" if analysis_type == "deep_learning" else "非线性关系"
        narrative = (
            f"{title}已完成二分类建模，测试集准确率 {metrics['accuracy']:.3f}、F1 {metrics['f1']:.3f}"
            + (f"、AUC {metrics['roc_auc']:.3f}" if metrics.get("roc_auc") is not None else "")
            + f"。模型更擅长捕捉{relation_phrase}，当前最敏感的特征是 {top_features}。业务上可把这些变量作为重点联动因素继续复盘。"
        )
    else:
        model = MLPRegressor(hidden_layer_sizes=hidden_layers, max_iter=600, random_state=42, early_stopping=True)
        model.fit(x_train, prepared["y_train"])
        predictions = model.predict(x_test)
        metrics = _regression_result_metrics(prepared["y_test"], predictions)
        permutation = permutation_importance(model, x_test, prepared["y_test"], n_repeats=5, random_state=42, scoring="r2")
        importance_table = _feature_importance_rows(prepared["x_test"].columns.astype(str).tolist(), permutation.importances_mean)
        top_features = "、".join(importance_table["feature"].head(3).tolist())
        relation_phrase = "更复杂的深层非线性结构" if analysis_type == "deep_learning" else "一定非线性拟合空间"
        narrative = (
            f"{title}已完成连续目标建模，测试集 R² {metrics['r_squared']:.3f}、RMSE {metrics['rmse']:.3f}、MAE {metrics['mae']:.3f}。"
            f"模型更擅长捕捉{relation_phrase}，当前最敏感的特征是 {top_features}。业务上应优先检查这些因素是否同时驱动规模和效率变化。"
        )
    metrics["target"] = prepared["target"]
    metrics["feature_count"] = int(prepared["x_train"].shape[1])
    metrics["hidden_layers"] = " x ".join(str(item) for item in hidden_layers)
    return {
        "analysis_type": analysis_type,
        "title": title,
        "narrative": narrative,
        "metrics": metrics,
        "tables": [
            _table("模型评估指标", _supervised_metric_table(metrics)),
            _table("置换重要性", importance_table),
        ],
        "chart": {
            "kind": "bar",
            "title": f"{title}特征敏感度",
            "x": importance_table["feature"].tolist(),
            "y": importance_table["importance"].tolist(),
        },
    }


def run_neural_network(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    return _run_mlp_model(
        frame,
        request,
        hidden_layers=(64, 32),
        analysis_type="neural_network",
        title="神经网络模型",
    )


def run_deep_learning(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    return _run_mlp_model(
        frame,
        request,
        hidden_layers=(128, 64, 32),
        analysis_type="deep_learning",
        title="深度学习网络",
    )


def run_normality(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    target = request.target or (request.features[0] if request.features else None)
    if not target:
        raise ValueError("Normality test requires a target column or first feature.")

    series = pd.to_numeric(frame[target], errors="coerce").dropna()
    if len(series) < 8:
        raise ValueError("Normality testing requires at least 8 numeric observations.")

    if len(series) <= 5000:
        stat_name = "shapiro_w"
        statistic, p_value = stats.shapiro(series)
    else:
        stat_name = "dagostino_k2"
        statistic, p_value = stats.normaltest(series)

    skewness = float(stats.skew(series))
    kurtosis = float(stats.kurtosis(series))
    summary = pd.DataFrame(
        {
            "metric": ["count", "mean", "std", "skewness", "kurtosis"],
            "value": [
                int(len(series)),
                float(series.mean()),
                float(series.std()),
                skewness,
                kurtosis,
            ],
        }
    ).round(5)

    return {
        "analysis_type": "normality",
        "title": "Normality Test",
        "narrative": f"The {stat_name} test returned p-value {p_value:.4g}; lower values imply stronger evidence against normality.",
        "metrics": {
            stat_name: float(statistic),
            "p_value": float(p_value),
            "skewness": skewness,
            "kurtosis": kurtosis,
            "sample_size": int(len(series)),
        },
        "tables": [_table("Distribution summary", summary)],
        "chart": {
            "kind": "bar",
            "title": f"{target} moments",
            "x": ["mean", "std", "skewness", "kurtosis"],
            "y": [float(series.mean()), float(series.std()), skewness, kurtosis],
        },
    }


def _distribution_series(frame: pd.DataFrame, request: StatisticRequest, *, test_name: str, min_observations: int) -> tuple[pd.Series, str]:
    target = request.target or (request.features[0] if request.features else None)
    if not target:
        raise ValueError(f"{test_name} requires a target column or first feature.")
    series = pd.to_numeric(frame[target], errors="coerce").dropna()
    if len(series) < min_observations:
        raise ValueError(f"{test_name} requires at least {min_observations} numeric observations.")
    if float(series.std(ddof=1)) == 0.0:
        raise ValueError(f"{test_name} requires non-constant numeric observations.")
    return series, target


def _distribution_summary_table(series: pd.Series) -> pd.DataFrame:
    quantiles = series.quantile([0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99])
    return pd.DataFrame(
        {
            "metric": [
                "count",
                "mean",
                "std",
                "skewness",
                "kurtosis",
                "min",
                "p01",
                "p05",
                "p25",
                "median",
                "p75",
                "p95",
                "p99",
                "max",
            ],
            "value": [
                int(len(series)),
                float(series.mean()),
                float(series.std()),
                float(stats.skew(series)),
                float(stats.kurtosis(series)),
                float(series.min()),
                float(quantiles.loc[0.01]),
                float(quantiles.loc[0.05]),
                float(quantiles.loc[0.25]),
                float(quantiles.loc[0.5]),
                float(quantiles.loc[0.75]),
                float(quantiles.loc[0.95]),
                float(quantiles.loc[0.99]),
                float(series.max()),
            ],
        }
    ).round(6)


def _distribution_chart(target: str, series: pd.Series) -> dict[str, Any]:
    quantiles = series.quantile([0.05, 0.25, 0.5, 0.75, 0.95])
    return {
        "kind": "bar",
        "title": f"{target} distribution checkpoints",
        "x": ["p05", "p25", "median", "p75", "p95"],
        "y": [float(quantiles.loc[q]) for q in [0.05, 0.25, 0.5, 0.75, 0.95]],
    }


def _normality_result(
    *,
    analysis_type: str,
    title: str,
    test_label: str,
    target: str,
    series: pd.Series,
    statistic_key: str,
    statistic: float,
    p_value: float,
    alpha: float,
    extra_metrics: dict[str, Any] | None = None,
    extra_tables: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    decision = "reject_normality" if p_value < alpha else "fail_to_reject_normality"
    metrics = {
        statistic_key: float(statistic),
        "p_value": float(p_value),
        "sample_size": int(len(series)),
        "skewness": float(stats.skew(series)),
        "kurtosis": float(stats.kurtosis(series)),
        "alpha": float(alpha),
        "decision": decision,
    }
    if extra_metrics:
        metrics.update(extra_metrics)
    tables = [_table("Distribution summary", _distribution_summary_table(series))]
    if extra_tables:
        tables.extend(extra_tables)
    return {
        "analysis_type": analysis_type,
        "title": title,
        "narrative": f"{test_label} returned p-value {p_value:.4g} for {target}; lower values imply stronger evidence against normality.",
        "metrics": metrics,
        "tables": tables,
        "chart": _distribution_chart(target, series),
    }


def run_shapiro_wilk(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    series, target = _distribution_series(frame, request, test_name="Shapiro-Wilk", min_observations=3)
    original_sample_size = len(series)
    sampled_for_test = original_sample_size > 5000
    if sampled_for_test:
        series = series.sample(n=5000, random_state=17)
    statistic, p_value = stats.shapiro(series)
    return _normality_result(
        analysis_type="shapiro_wilk",
        title="Shapiro-Wilk Normality Test",
        test_label="Shapiro-Wilk",
        target=target,
        series=series,
        statistic_key="shapiro_w",
        statistic=float(statistic),
        p_value=float(p_value),
        alpha=request.alpha,
        extra_metrics={"sampled_for_test": sampled_for_test, "original_sample_size": int(original_sample_size)},
    )


def run_dagostino_k2(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    series, target = _distribution_series(frame, request, test_name="D'Agostino K^2", min_observations=8)
    statistic, p_value = stats.normaltest(series)
    return _normality_result(
        analysis_type="dagostino_k2",
        title="D'Agostino K^2 Normality Test",
        test_label="D'Agostino K^2",
        target=target,
        series=series,
        statistic_key="k2_statistic",
        statistic=float(statistic),
        p_value=float(p_value),
        alpha=request.alpha,
    )


def run_jarque_bera(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    series, target = _distribution_series(frame, request, test_name="Jarque-Bera", min_observations=3)
    statistic, p_value = stats.jarque_bera(series)
    return _normality_result(
        analysis_type="jarque_bera",
        title="Jarque-Bera Normality Test",
        test_label="Jarque-Bera",
        target=target,
        series=series,
        statistic_key="jarque_bera_statistic",
        statistic=float(statistic),
        p_value=float(p_value),
        alpha=request.alpha,
    )


def run_kolmogorov_smirnov_1samp(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    series, target = _distribution_series(frame, request, test_name="One-sample Kolmogorov-Smirnov", min_observations=5)
    standardized = (series - series.mean()) / series.std(ddof=1)
    statistic, p_value = stats.kstest(standardized.to_numpy(), "norm")
    return _normality_result(
        analysis_type="kolmogorov_smirnov_1samp",
        title="One-sample Kolmogorov-Smirnov Normality Check",
        test_label="One-sample KS against fitted normal",
        target=target,
        series=series,
        statistic_key="ks_statistic",
        statistic=float(statistic),
        p_value=float(p_value),
        alpha=request.alpha,
        extra_metrics={
            "reference_distribution": "normal",
            "estimated_mean": float(series.mean()),
            "estimated_std": float(series.std(ddof=1)),
            "parameter_estimation_note": "p-value is approximate because normal parameters are estimated from the sample.",
        },
    )


def run_anderson_darling(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    series, target = _distribution_series(frame, request, test_name="Anderson-Darling", min_observations=5)
    result = stats.anderson(series.to_numpy(), dist="norm", method="interpolate")
    p_value = float(result.pvalue)
    decision = "reject_normality" if p_value < request.alpha else "fail_to_reject_normality"
    test_rows = pd.DataFrame(
        {
            "metric": ["anderson_darling_statistic", "p_value", "alpha"],
            "value": [float(result.statistic), p_value, float(request.alpha)],
        }
    ).round(6)
    summary = _distribution_summary_table(series)
    return {
        "analysis_type": "anderson_darling",
        "title": "Anderson-Darling Normality Test",
        "narrative": f"Anderson-Darling returned p-value {p_value:.4g} for {target}; lower values imply stronger tail-sensitive evidence against normality.",
        "metrics": {
            "anderson_darling_statistic": float(result.statistic),
            "p_value": p_value,
            "p_value_method": "interpolate",
            "sample_size": int(len(series)),
            "skewness": float(stats.skew(series)),
            "kurtosis": float(stats.kurtosis(series)),
            "alpha": float(request.alpha),
            "decision": decision,
        },
        "tables": [
            _table("Distribution summary", summary),
            _table("Anderson-Darling p-value summary", test_rows),
        ],
        "chart": _distribution_chart(target, series),
    }


def _time_series_frame(frame: pd.DataFrame, request: StatisticRequest, *, test_name: str, min_observations: int) -> tuple[pd.DataFrame, str, str]:
    target = request.target or (request.features[0] if request.features else None)
    time_field = request.group_column
    if not target:
        raise ValueError(f"{test_name} requires a numeric target column.")
    if not time_field:
        raise ValueError(f"{test_name} requires a time field bound as group_column/time.")

    clean = frame[[time_field, target]].copy()
    clean[target] = pd.to_numeric(clean[target], errors="coerce")
    parsed_time = pd.to_datetime(clean[time_field], errors="coerce")
    if parsed_time.notna().sum() >= max(2, int(len(clean.dropna(subset=[target])) * 0.6)):
        clean["_analysis_time_sort"] = parsed_time
        clean["_analysis_time_label"] = parsed_time.dt.strftime("%Y-%m-%d")
    else:
        numeric_time = pd.to_numeric(clean[time_field], errors="coerce")
        clean["_analysis_time_sort"] = numeric_time if numeric_time.notna().any() else clean[time_field].astype(str)
        clean["_analysis_time_label"] = clean[time_field].astype(str)
    clean = clean.dropna(subset=[target, "_analysis_time_sort"]).sort_values("_analysis_time_sort").reset_index(drop=True)
    if len(clean) < min_observations:
        raise ValueError(f"{test_name} requires at least {min_observations} complete ordered observations.")
    if float(clean[target].std(ddof=1)) == 0.0:
        raise ValueError(f"{test_name} requires non-constant numeric observations.")
    return clean, target, time_field


def _safe_lag(requested_lag: int, sample_size: int, *, minimum: int = 1, maximum: int | None = None) -> int:
    cap = maximum if maximum is not None else max(minimum, sample_size // 2)
    return max(minimum, min(int(requested_lag), cap))


def _time_series_chart(clean: pd.DataFrame, target: str, *, y_column: str | None = None, title: str) -> dict[str, Any]:
    y_field = y_column or target
    return {
        "kind": "scatter",
        "title": title,
        "x": clean["_analysis_time_label"].head(240).astype(str).tolist(),
        "y": clean[y_field].head(240).round(6).tolist(),
    }


def run_moving_average(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    clean, target, time_field = _time_series_frame(frame, request, test_name="Moving Average", min_observations=4)
    window = max(2, min(int(request.window or 3), max(2, len(clean) // 2)))
    clean = clean.copy()
    clean["moving_average"] = clean[target].rolling(window=window, min_periods=1).mean()
    clean["residual_to_smooth"] = clean[target] - clean["moving_average"]
    first_smooth = float(clean["moving_average"].iloc[0])
    last_smooth = float(clean["moving_average"].iloc[-1])
    trend_change = last_smooth - first_smooth
    trend_direction = "up" if trend_change > 0 else "down" if trend_change < 0 else "flat"
    rows = clean[["_analysis_time_label", target, "moving_average", "residual_to_smooth"]].rename(columns={"_analysis_time_label": time_field}).tail(40).round(6)
    return {
        "analysis_type": "moving_average",
        "title": "Moving Average Trend",
        "narrative": f"Moving average for {target} over {time_field} uses window={window}; smoothed trend moves {trend_direction} by {trend_change:.4f}.",
        "metrics": {
            "sample_size": int(len(clean)),
            "window": int(window),
            "first_smoothed_value": first_smooth,
            "last_smoothed_value": last_smooth,
            "trend_change": float(trend_change),
            "trend_direction": trend_direction,
        },
        "tables": [_table("Moving average tail", rows)],
        "chart": _time_series_chart(clean, target, y_column="moving_average", title=f"{target} moving average"),
    }


def run_autocorrelation(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    clean, target, time_field = _time_series_frame(frame, request, test_name="Autocorrelation", min_observations=8)
    lag_count = _safe_lag(request.lag or 12, len(clean), maximum=max(1, len(clean) // 2))
    values = clean[target].to_numpy(dtype=float)
    acf, _adfuller, _pacf = _statsmodels_tsa()
    acf_values = acf(values, nlags=lag_count, fft=False)
    lag_rows = pd.DataFrame({"lag": list(range(len(acf_values))), "autocorrelation": acf_values}).round(6)
    nonzero = lag_rows[lag_rows["lag"] > 0]
    strongest = nonzero.iloc[nonzero["autocorrelation"].abs().argmax()]
    return {
        "analysis_type": "autocorrelation",
        "title": "Autocorrelation Analysis",
        "narrative": f"Autocorrelation for {target} over {time_field} checked {lag_count} lag(s); strongest lag is {int(strongest['lag'])} with correlation {float(strongest['autocorrelation']):.4f}.",
        "metrics": {
            "sample_size": int(len(clean)),
            "lag_count": int(lag_count),
            "strongest_lag": int(strongest["lag"]),
            "strongest_correlation": float(strongest["autocorrelation"]),
        },
        "tables": [_table("Autocorrelation by lag", lag_rows)],
        "chart": {
            "kind": "bar",
            "title": f"{target} autocorrelation by lag",
            "x": lag_rows["lag"].astype(str).tolist(),
            "y": lag_rows["autocorrelation"].tolist(),
        },
    }


def run_partial_autocorrelation(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    clean, target, time_field = _time_series_frame(frame, request, test_name="Partial Autocorrelation", min_observations=10)
    lag_count = _safe_lag(request.lag or 8, len(clean), maximum=max(1, len(clean) // 3))
    values = clean[target].to_numpy(dtype=float)
    _acf, _adfuller, pacf = _statsmodels_tsa()
    pacf_values = pacf(values, nlags=lag_count, method="yw")
    lag_rows = pd.DataFrame({"lag": list(range(len(pacf_values))), "partial_autocorrelation": pacf_values}).round(6)
    nonzero = lag_rows[lag_rows["lag"] > 0]
    strongest = nonzero.iloc[nonzero["partial_autocorrelation"].abs().argmax()]
    return {
        "analysis_type": "partial_autocorrelation",
        "title": "Partial Autocorrelation Analysis",
        "narrative": f"Partial autocorrelation for {target} over {time_field} checked {lag_count} lag(s); strongest independent lag is {int(strongest['lag'])}.",
        "metrics": {
            "sample_size": int(len(clean)),
            "lag_count": int(lag_count),
            "strongest_lag": int(strongest["lag"]),
            "strongest_correlation": float(strongest["partial_autocorrelation"]),
        },
        "tables": [_table("Partial autocorrelation by lag", lag_rows)],
        "chart": {
            "kind": "bar",
            "title": f"{target} partial autocorrelation by lag",
            "x": lag_rows["lag"].astype(str).tolist(),
            "y": lag_rows["partial_autocorrelation"].tolist(),
        },
    }


def run_ljung_box(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    clean, target, time_field = _time_series_frame(frame, request, test_name="Ljung-Box", min_observations=10)
    lag_count = _safe_lag(request.lag or 10, len(clean), maximum=max(1, min(20, len(clean) // 2)))
    acorr_ljungbox, _het_breuschpagan, _het_white = _statsmodels_diagnostic()
    result = acorr_ljungbox(clean[target].to_numpy(dtype=float), lags=[lag_count], return_df=True)
    statistic = float(result["lb_stat"].iloc[0])
    p_value = float(result["lb_pvalue"].iloc[0])
    decision = "serial_correlation" if p_value < request.alpha else "white_noise_not_rejected"
    rows = result.reset_index().rename(columns={"index": "lag", "lb_stat": "ljung_box_statistic", "lb_pvalue": "p_value"}).round(6)
    return {
        "analysis_type": "ljung_box",
        "title": "Ljung-Box White Noise Test",
        "narrative": f"Ljung-Box test for {target} over {time_field} at lag {lag_count} returned p-value {p_value:.4g}.",
        "metrics": {
            "sample_size": int(len(clean)),
            "lag": int(lag_count),
            "ljung_box_statistic": statistic,
            "p_value": p_value,
            "alpha": float(request.alpha),
            "decision": decision,
        },
        "tables": [_table("Ljung-Box test", rows)],
        "chart": _time_series_chart(clean, target, title=f"{target} ordered series"),
    }


def run_adf_test(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    clean, target, time_field = _time_series_frame(frame, request, test_name="ADF Test", min_observations=12)
    _acf, adfuller, _pacf = _statsmodels_tsa()
    statistic, p_value, used_lag, observations, critical_values, _icbest = adfuller(clean[target].to_numpy(dtype=float), autolag="AIC")
    decision = "stationary" if float(p_value) < request.alpha else "unit_root_not_rejected"
    critical_rows = pd.DataFrame(
        [{"threshold": key, "critical_value": value} for key, value in critical_values.items()]
    ).round(6)
    summary_rows = pd.DataFrame(
        {
            "metric": ["adf_statistic", "p_value", "used_lag", "observations", "alpha"],
            "value": [float(statistic), float(p_value), int(used_lag), int(observations), float(request.alpha)],
        }
    ).round(6)
    return {
        "analysis_type": "adf_test",
        "title": "Augmented Dickey-Fuller Stationarity Test",
        "narrative": f"ADF test for {target} over {time_field} returned p-value {float(p_value):.4g}; decision is {decision}.",
        "metrics": {
            "sample_size": int(len(clean)),
            "adf_statistic": float(statistic),
            "p_value": float(p_value),
            "used_lag": int(used_lag),
            "observations": int(observations),
            "alpha": float(request.alpha),
            "decision": decision,
        },
        "tables": [
            _table("ADF test summary", summary_rows),
            _table("ADF critical values", critical_rows),
        ],
        "chart": _time_series_chart(clean, target, title=f"{target} ordered series"),
    }


def run_tukey_hsd(frame: pd.DataFrame, request: StatisticRequest) -> dict[str, Any]:
    if not request.target or not request.group_column:
        raise ValueError("Tukey HSD requires a numeric target and grouping column.")

    clean = frame[[request.target, request.group_column]].copy()
    clean[request.target] = pd.to_numeric(clean[request.target], errors="coerce")
    clean = clean.dropna()
    if clean[request.group_column].nunique() < 2:
        raise ValueError("Tukey HSD needs at least two groups.")

    tukey = pairwise_tukeyhsd(
        endog=clean[request.target].to_numpy(),
        groups=clean[request.group_column].astype(str).to_numpy(),
        alpha=request.alpha,
    )
    table = pd.DataFrame(
        tukey.summary().data[1:],
        columns=tukey.summary().data[0],
    )
    for column in ["meandiff", "p-adj", "lower", "upper"]:
        if column in table.columns:
            table[column] = pd.to_numeric(table[column], errors="coerce")
    comparison_rows = table.round(5)
    significant_count = int(comparison_rows["reject"].astype(str).eq("True").sum()) if "reject" in comparison_rows.columns else 0

    return {
        "analysis_type": "tukey_hsd",
        "title": "Tukey HSD Post-hoc Test",
        "narrative": f"Tukey post-hoc comparisons found {significant_count} significant pairwise differences.",
        "metrics": {
            "comparisons": int(len(comparison_rows)),
            "significant_pairs": significant_count,
            "alpha": float(request.alpha),
        },
        "tables": [
            {
                "title": "Pairwise Tukey HSD comparisons",
                "columns": comparison_rows.columns.astype(str).tolist(),
                "rows": comparison_rows.to_dict(orient="records"),
            }
        ],
        "chart": {
            "kind": "bar",
            "title": "Pairwise mean differences",
            "x": [
                f"{row['group1']} vs {row['group2']}"
                for _, row in comparison_rows.head(12).iterrows()
            ],
            "y": [float(row["meandiff"]) for _, row in comparison_rows.head(12).iterrows()],
        },
    }
