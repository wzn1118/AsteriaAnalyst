from __future__ import annotations

import csv
import html
import json
import math
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd

from app.models import CodexRunRequest
from app.models import SmartReportRequest
from app.services.codex_service import (
    _fallback_r_workflow_author_v2,
    codex_generate_r_workflow,
    codex_infer_r_workflow_semantics,
    codex_interpret_r_results,
)
from app.services.codex_runtime_task_service import create_codex_run_task, get_codex_run_task
from app.services.codex_runtime_service import run_headless_codex
from app.services.path_service import REPORTS_DIR, bundled_rscript_candidates
from app.services.report_design_spec_service import build_report_design_spec
from app.services.settings_service import load_runtime_settings_raw


R_WORKFLOW_OUTPUT_SPECS: dict[str, dict[str, Any]] = {
    "cleaned_dataset.csv": {"title": "清洗后数据", "purpose": "R 清洗后数据。", "type": "csv", "preview_limit": 160},
    "summary_stats.csv": {"title": "数值摘要结果", "purpose": "R 数值摘要结果。", "type": "csv", "preview_limit": 200},
    "quantile_profile.csv": {"title": "分位数轮廓", "purpose": "R 分位数画像结果。", "type": "csv", "preview_limit": 200},
    "anomaly_summary.csv": {"title": "异常值摘要", "purpose": "R 异常值/IQR 摘要。", "type": "csv", "preview_limit": 200},
    "zero_ratio_summary.csv": {"title": "零值占比摘要", "purpose": "R 零值占比结果。", "type": "csv", "preview_limit": 200},
    "coefficient_variation.csv": {"title": "波动系数摘要", "purpose": "R 变异系数结果。", "type": "csv", "preview_limit": 200},
    "skew_kurtosis_summary.csv": {"title": "偏度峰度摘要", "purpose": "R 分布形态摘要。", "type": "csv", "preview_limit": 200},
    "missing_profile.csv": {"title": "缺失值画像", "purpose": "R 缺失值画像。", "type": "csv", "preview_limit": 200},
    "duplicate_profile.csv": {"title": "重复值画像", "purpose": "R 重复值画像。", "type": "csv", "preview_limit": 200},
    "correlation_matrix.csv": {"title": "相关矩阵结果", "purpose": "R 相关矩阵结果。", "type": "csv", "preview_limit": 200},
    "correlation_pairs.csv": {"title": "高相关对摘要", "purpose": "R 高相关指标对摘要。", "type": "csv", "preview_limit": 200},
    "covariance_matrix.csv": {"title": "协方差矩阵结果", "purpose": "R 协方差矩阵结果。", "type": "csv", "preview_limit": 200},
    "pca_variance.csv": {"title": "PCA 方差解释", "purpose": "R 主成分方差解释。", "type": "csv", "preview_limit": 200},
    "pca_loadings.csv": {"title": "PCA 载荷结果", "purpose": "R 主成分载荷结果。", "type": "csv", "preview_limit": 200},
    "pca_scores.csv": {"title": "PCA 得分结果", "purpose": "R 主成分得分结果。", "type": "csv", "preview_limit": 200},
    "kmeans_clusters.csv": {"title": "KMeans 聚类结果", "purpose": "R 聚类分群结果。", "type": "csv", "preview_limit": 200},
    "cluster_profile.csv": {"title": "聚类画像", "purpose": "R 聚类画像结果。", "type": "csv", "preview_limit": 200},
    "top_categories.csv": {"title": "类别结构结果", "purpose": "R 类别结构结果。", "type": "csv", "preview_limit": 200},
    "category_share_summary.csv": {"title": "类别占比摘要", "purpose": "R 类别占比与累计占比。", "type": "csv", "preview_limit": 200},
    "category_metric_summary.csv": {"title": "类别指标摘要", "purpose": "R 类别指标聚合结果。", "type": "csv", "preview_limit": 200},
    "category_price_band_summary.csv": {"title": "类别价格带摘要", "purpose": "R 类别价格带摘要。", "type": "csv", "preview_limit": 200},
    "budget_variance_summary.csv": {"title": "预算偏差摘要", "purpose": "R 预算 vs 实际偏差分层结果。", "type": "csv", "preview_limit": 240},
    "temporal_trend.csv": {"title": "时间趋势结果", "purpose": "R 时间趋势结果。", "type": "csv", "preview_limit": 200},
    "temporal_growth.csv": {"title": "时间增长结果", "purpose": "R 时间增长率结果。", "type": "csv", "preview_limit": 200},
    "temporal_moving_average.csv": {"title": "时间移动平均", "purpose": "R 时间移动平均结果。", "type": "csv", "preview_limit": 200},
    "temporal_period_profile.csv": {"title": "周期画像", "purpose": "R 周期画像结果。", "type": "csv", "preview_limit": 200},
    "funnel_metrics.csv": {"title": "漏斗总量结果", "purpose": "R 漏斗总量结果。", "type": "csv", "preview_limit": 200},
    "funnel_conversion_summary.csv": {"title": "漏斗转化摘要", "purpose": "R 漏斗转化摘要。", "type": "csv", "preview_limit": 200},
    "top_items.csv": {"title": "头部商品摘要", "purpose": "R 头部商品摘要。", "type": "csv", "preview_limit": 200},
    "item_metric_summary.csv": {"title": "商品指标摘要", "purpose": "R 商品指标摘要。", "type": "csv", "preview_limit": 200},
    "item_daily_summary.csv": {"title": "商品日级摘要", "purpose": "R 商品日级摘要。", "type": "csv", "preview_limit": 200},
    "outlier_records.csv": {"title": "异常样本明细", "purpose": "R 异常样本明细。", "type": "csv", "preview_limit": 200},
    "correlation_pairs_with_pvalues.csv": {"title": "相关系数与 p 值", "purpose": "相关系数及显著性 p 值。", "type": "csv", "preview_limit": 400},
    "anova_results.csv": {"title": "ANOVA 组间检验", "purpose": "ANOVA 组间检验结果，含 eta²。", "type": "csv", "preview_limit": 400},
    "eta_squared_results.csv": {"title": "eta² 效应量", "purpose": "ANOVA 对应 eta² 效应量。", "type": "csv", "preview_limit": 400},
    "kruskal_results.csv": {"title": "Kruskal-Wallis 检验", "purpose": "Kruskal-Wallis 非参数组间检验结果。", "type": "csv", "preview_limit": 400},
    "tukey_hsd_results.csv": {"title": "Tukey HSD 事后比较", "purpose": "Tukey HSD 组间事后比较。", "type": "csv", "preview_limit": 500},
    "chi_square_tests.csv": {"title": "卡方检验", "purpose": "分类变量独立性卡方检验，含 Cramer's V。", "type": "csv", "preview_limit": 500},
    "cramers_v_results.csv": {"title": "Cramer's V 效应量", "purpose": "卡方检验对应 Cramer's V 效应量。", "type": "csv", "preview_limit": 500},
    "cronbach_alpha.csv": {"title": "Cronbach's alpha", "purpose": "自动识别 Likert 题项后的信度系数。", "type": "csv", "preview_limit": 120},
    "method_log.csv": {"title": "方法执行日志", "purpose": "R 方法执行日志。", "type": "csv", "preview_limit": 400},
    "numeric_distribution.png": {"title": "数值分布图", "purpose": "R 数值分布图。", "type": "png"},
    "numeric_boxplot.png": {"title": "数值箱线图", "purpose": "R 数值箱线图。", "type": "png"},
    "numeric_density.png": {"title": "数值密度图", "purpose": "R 数值密度图。", "type": "png"},
    "correlation_heatmap.png": {"title": "相关热力图", "purpose": "R 相关热力图。", "type": "png"},
    "numeric_scatter_plot.png": {"title": "数值散点图", "purpose": "R 数值散点图。", "type": "png"},
    "category_mix.png": {"title": "类别结构图", "purpose": "R 类别结构图。", "type": "png"},
    "category_metric_plot.png": {"title": "类别指标图", "purpose": "R 类别指标图。", "type": "png"},
    "category_pareto.png": {"title": "类别帕累托图", "purpose": "R 类别帕累托图。", "type": "png"},
    "temporal_trend.png": {"title": "时间趋势图", "purpose": "R 时间趋势图。", "type": "png"},
    "temporal_growth.png": {"title": "时间增长图", "purpose": "R 时间增长图。", "type": "png"},
    "temporal_period_plot.png": {"title": "周期画像图", "purpose": "R 周期画像图。", "type": "png"},
    "funnel_overview.png": {"title": "漏斗总览图", "purpose": "R 漏斗总览图。", "type": "png"},
    "top_items_plot.png": {"title": "头部商品图", "purpose": "R 头部商品图。", "type": "png"},
    "01_clean_prepare-stdout.log": {"title": "清洗脚本标准输出", "purpose": "R 清洗脚本标准输出。", "type": "log"},
    "01_clean_prepare-stderr.log": {"title": "清洗脚本错误输出", "purpose": "R 清洗脚本错误输出。", "type": "log"},
    "02_analysis_visualize-stdout.log": {"title": "分析脚本标准输出", "purpose": "R 分析脚本标准输出。", "type": "log"},
    "02_analysis_visualize-stderr.log": {"title": "分析脚本错误输出", "purpose": "R 分析脚本错误输出。", "type": "log"},
}

R_WORKFLOW_OUTPUT_SPECS["pca_axis_summary.csv"] = {
    "title": "PCA 涓昏酱涓氬姟鎽樿",
    "purpose": "R 主轴业务摘要。",
    "type": "csv",
    "preview_limit": 120,
}
R_WORKFLOW_OUTPUT_SPECS["cluster_member_detail.csv"] = {
    "title": "鑱氱被鎴愬憳鏄庣粏",
    "purpose": "R 聚类成员明细。",
    "type": "csv",
    "preview_limit": 240,
}

R_WORKFLOW_OUTPUT_SPECS.update(
    {
        "spearman_correlation_pairs.csv": {
            "title": "Spearman correlation",
            "purpose": "Spearman rank correlation with p values.",
            "type": "csv",
            "preview_limit": 400,
        },
        "kendall_correlation_pairs.csv": {
            "title": "Kendall correlation",
            "purpose": "Kendall rank correlation with p values.",
            "type": "csv",
            "preview_limit": 400,
        },
        "p_value_adjustment_summary.csv": {
            "title": "P-value adjustment summary",
            "purpose": "BH/FDR and Bonferroni correction across available p-value outputs.",
            "type": "csv",
            "preview_limit": 600,
        },
        "normality_diagnostics.csv": {
            "title": "Normality diagnostics",
            "purpose": "Distribution diagnostics for numeric columns.",
            "type": "csv",
            "preview_limit": 300,
        },
        "variance_homogeneity_tests.csv": {
            "title": "Variance homogeneity tests",
            "purpose": "Levene and Brown-Forsythe tests for grouped numeric comparisons.",
            "type": "csv",
            "preview_limit": 500,
        },
        "welch_anova_results.csv": {
            "title": "Welch ANOVA",
            "purpose": "Welch ANOVA for grouped numeric comparisons when variance equality is uncertain.",
            "type": "csv",
            "preview_limit": 500,
        },
        "dunn_posthoc_results.csv": {
            "title": "Dunn posthoc",
            "purpose": "Dunn-style pairwise posthoc comparisons after significant Kruskal-Wallis tests.",
            "type": "csv",
            "preview_limit": 600,
        },
        "chi_square_residuals.csv": {
            "title": "Chi-square residuals",
            "purpose": "Standardized residuals for chi-square contingency tables.",
            "type": "csv",
            "preview_limit": 600,
        },
        "confidence_intervals.csv": {
            "title": "Confidence intervals",
            "purpose": "95% confidence intervals for numeric means and binary proportions.",
            "type": "csv",
            "preview_limit": 300,
        },
        "missingness_diagnostics.csv": {
            "title": "Missingness diagnostics",
            "purpose": "Column-level missingness diagnostics.",
            "type": "csv",
            "preview_limit": 300,
        },
        "low_information_columns.csv": {
            "title": "Low-information columns",
            "purpose": "Constant, near-zero variance, and high-duplicate column diagnostics.",
            "type": "csv",
            "preview_limit": 300,
        },
        "outlier_influence_summary.csv": {
            "title": "Outlier influence summary",
            "purpose": "IQR/MAD outlier diagnostics and mean-sensitivity summary for numeric columns.",
            "type": "csv",
            "preview_limit": 300,
        },
        "generic_missingness_bar.png": {
            "title": "Generic missingness bar chart",
            "purpose": "Non-questionnaire generic chart showing fields with the highest missingness.",
            "type": "png",
        },
        "generic_correlation_bubble.csv": {
            "title": "Generic correlation bubble data",
            "purpose": "Non-questionnaire generic top numeric correlation pairs for bubble visualization.",
            "type": "csv",
            "preview_limit": 400,
        },
        "generic_correlation_bubble.png": {
            "title": "Generic correlation bubble chart",
            "purpose": "Non-questionnaire generic bubble chart for the strongest numeric relationships.",
            "type": "png",
        },
        "generic_category_metric_heatmap.csv": {
            "title": "Generic category metric heatmap data",
            "purpose": "Non-questionnaire generic category-by-metric mean and lift data.",
            "type": "csv",
            "preview_limit": 500,
        },
        "generic_category_metric_heatmap.png": {
            "title": "Generic category metric heatmap",
            "purpose": "Non-questionnaire generic heatmap comparing category levels across numeric metrics.",
            "type": "png",
        },
        "generic_outlier_influence_bubble.csv": {
            "title": "Generic outlier influence bubble data",
            "purpose": "Non-questionnaire generic outlier rate and mean-shift bubble data.",
            "type": "csv",
            "preview_limit": 300,
        },
        "generic_outlier_influence_bubble.png": {
            "title": "Generic outlier influence bubble chart",
            "purpose": "Non-questionnaire generic bubble chart for outlier rate versus mean influence.",
            "type": "png",
        },
        "generic_time_trend_grid.csv": {
            "title": "Generic time trend grid data",
            "purpose": "Non-questionnaire generic normalized trend data for top numeric metrics.",
            "type": "csv",
            "preview_limit": 500,
        },
        "generic_time_trend_grid.png": {
            "title": "Generic time trend grid",
            "purpose": "Non-questionnaire generic small-multiple trend chart for time series metrics.",
            "type": "png",
        },
        "generic_numeric_distribution_grid.csv": {
            "title": "Generic numeric distribution grid data",
            "purpose": "Non-questionnaire generic numeric distribution bins for top metrics.",
            "type": "csv",
            "preview_limit": 500,
        },
        "generic_numeric_distribution_grid.png": {
            "title": "Generic numeric distribution grid",
            "purpose": "Non-questionnaire generic histogram small multiples for top numeric metrics.",
            "type": "png",
        },
        "generic_cumulative_contribution_curve.csv": {
            "title": "Generic cumulative contribution curve data",
            "purpose": "Non-questionnaire generic Pareto-style cumulative contribution data.",
            "type": "csv",
            "preview_limit": 500,
        },
        "generic_cumulative_contribution_curve.png": {
            "title": "Generic cumulative contribution curve",
            "purpose": "Non-questionnaire generic Pareto-style cumulative contribution chart.",
            "type": "png",
        },
        "generic_segment_bubble.csv": {
            "title": "Generic segment bubble data",
            "purpose": "Non-questionnaire generic segment share versus metric lift bubble data.",
            "type": "csv",
            "preview_limit": 500,
        },
        "generic_segment_bubble.png": {
            "title": "Generic segment bubble chart",
            "purpose": "Non-questionnaire generic bubble chart for segment size and metric over-index.",
            "type": "png",
        },
        "generic_top_bottom_performer.csv": {
            "title": "Generic top bottom performer data",
            "purpose": "Non-questionnaire generic top and bottom category levels by a selected metric.",
            "type": "csv",
            "preview_limit": 500,
        },
        "generic_top_bottom_performer.png": {
            "title": "Generic top bottom performer chart",
            "purpose": "Non-questionnaire generic diverging bar chart for top and bottom category performers.",
            "type": "png",
        },
        "generic_key_metric_scatter_bubble.csv": {
            "title": "Generic key metric scatter bubble data",
            "purpose": "Non-questionnaire generic row-level scatter bubble data for key metric relationships.",
            "type": "csv",
            "preview_limit": 500,
        },
        "generic_key_metric_scatter_bubble.png": {
            "title": "Generic key metric scatter bubble chart",
            "purpose": "Non-questionnaire generic scatter bubble chart for key metric relationships.",
            "type": "png",
        },
        "chart_visual_style.csv": {
            "title": "Chart visual style",
            "purpose": "Frontend/request-driven chart color style used by deterministic R workflow visuals.",
            "type": "csv",
            "preview_limit": 40,
        },
        "chart_visual_style.json": {
            "title": "Chart visual style JSON",
            "purpose": "Traceable chart color palette resolved from frontend visual input.",
            "type": "json",
            "preview_limit": 40,
        },
    }
)

R_WORKFLOW_OUTPUT_SPECS.update(
    {
        "survey_field_map.csv": {
            "title": "Survey field map",
            "purpose": "Questionnaire-only short labels and field roles for readable visuals.",
            "type": "csv",
            "preview_limit": 300,
        },
        "survey_multi_select_rates.csv": {
            "title": "Survey multi-select rates",
            "purpose": "Questionnaire-only option selection rates for 0/1 multi-select fields.",
            "type": "csv",
            "preview_limit": 300,
        },
        "survey_likert_summary.csv": {
            "title": "Survey Likert summary",
            "purpose": "Questionnaire-only Likert means, confidence intervals, and sentiment rates.",
            "type": "csv",
            "preview_limit": 300,
        },
        "survey_likert_distribution.csv": {
            "title": "Survey Likert distribution",
            "purpose": "Questionnaire-only response distribution by Likert item.",
            "type": "csv",
            "preview_limit": 500,
        },
        "survey_multi_select_cooccurrence.csv": {
            "title": "Survey multi-select co-occurrence",
            "purpose": "Questionnaire-only pairwise co-selection rates and lift for multi-select options.",
            "type": "csv",
            "preview_limit": 500,
        },
        "survey_likert_correlation.csv": {
            "title": "Survey Likert correlation",
            "purpose": "Questionnaire-only rank correlation between Likert items.",
            "type": "csv",
            "preview_limit": 500,
        },
        "survey_segment_likert_means.csv": {
            "title": "Survey segment Likert means",
            "purpose": "Questionnaire-only segment-level Likert means for audience comparison.",
            "type": "csv",
            "preview_limit": 500,
        },
        "survey_segment_distribution.csv": {
            "title": "Survey segment distribution",
            "purpose": "Questionnaire-only respondent mix across detected segment dimensions.",
            "type": "csv",
            "preview_limit": 500,
        },
        "survey_segment_multi_select_rates.csv": {
            "title": "Survey segment multi-select rates",
            "purpose": "Questionnaire-only multi-select option rates by respondent segment.",
            "type": "csv",
            "preview_limit": 500,
        },
        "survey_likert_sentiment_balance.csv": {
            "title": "Survey Likert sentiment balance",
            "purpose": "Questionnaire-only positive, neutral, negative, and net-positive rates by Likert item.",
            "type": "csv",
            "preview_limit": 500,
        },
        "survey_multi_select_portfolio.csv": {
            "title": "Survey multi-select portfolio",
            "purpose": "Questionnaire-only option reach versus co-selection lift portfolio.",
            "type": "csv",
            "preview_limit": 500,
        },
        "survey_segment_multi_select_bubble.csv": {
            "title": "Survey segment multi-select bubble data",
            "purpose": "Questionnaire-only segment-by-option bubble data with selection-rate deltas.",
            "type": "csv",
            "preview_limit": 500,
        },
        "survey_segment_likert_bubble.csv": {
            "title": "Survey segment Likert bubble data",
            "purpose": "Questionnaire-only segment-by-Likert bubble data with mean deltas.",
            "type": "csv",
            "preview_limit": 500,
        },
        "survey_multi_select_rates.png": {
            "title": "Survey multi-select rates chart",
            "purpose": "Questionnaire-only readable multi-select option rate chart.",
            "type": "png",
        },
        "survey_likert_mean_ci.png": {
            "title": "Survey Likert mean CI chart",
            "purpose": "Questionnaire-only Likert mean and 95% CI chart.",
            "type": "png",
        },
        "survey_likert_distribution.png": {
            "title": "Survey Likert distribution chart",
            "purpose": "Questionnaire-only stacked Likert distribution chart.",
            "type": "png",
        },
        "survey_multi_select_cooccurrence.png": {
            "title": "Survey multi-select co-occurrence heatmap",
            "purpose": "Questionnaire-only heatmap showing which multi-select options are selected together.",
            "type": "png",
        },
        "survey_likert_correlation_heatmap.png": {
            "title": "Survey Likert correlation heatmap",
            "purpose": "Questionnaire-only heatmap showing relationship structure between Likert items.",
            "type": "png",
        },
        "survey_segment_likert_heatmap.png": {
            "title": "Survey segment Likert heatmap",
            "purpose": "Questionnaire-only heatmap comparing Likert means across detected audience segments.",
            "type": "png",
        },
        "survey_segment_distribution.png": {
            "title": "Survey segment distribution chart",
            "purpose": "Questionnaire-only readable respondent mix chart.",
            "type": "png",
        },
        "survey_segment_multi_select_heatmap.png": {
            "title": "Survey segment multi-select heatmap",
            "purpose": "Questionnaire-only heatmap comparing option selection rates by segment.",
            "type": "png",
        },
        "survey_likert_sentiment_balance.png": {
            "title": "Survey Likert sentiment balance chart",
            "purpose": "Questionnaire-only net positive and negative sentiment chart.",
            "type": "png",
        },
        "survey_multi_select_portfolio.png": {
            "title": "Survey multi-select portfolio chart",
            "purpose": "Questionnaire-only option reach versus co-selection lift chart.",
            "type": "png",
        },
        "survey_segment_multi_select_bubble.png": {
            "title": "Survey segment multi-select bubble chart",
            "purpose": "Questionnaire-only bubble chart comparing segment option preference gaps.",
            "type": "png",
        },
        "survey_segment_likert_bubble.png": {
            "title": "Survey segment Likert bubble chart",
            "purpose": "Questionnaire-only bubble chart comparing segment Likert mean gaps.",
            "type": "png",
        },
    }
)


R_WORKFLOW_METHOD_SPECS: dict[str, dict[str, str]] = {
    "summary_stats": {"title": "数值摘要", "what": "看整体规模、均值、中位数和波动水平。", "use": "判断核心指标的常态水平和波动基线。"},
    "quantile_profile": {"title": "分位数轮廓", "what": "看 5/25/75/95 分位数。", "use": "判断分布是否偏斜，以及头尾是否拉开。"},
    "anomaly_summary": {"title": "异常值摘要", "what": "看 IQR 异常边界和异常占比。", "use": "判断总量和均值是否被少数异常点拉动。"},
    "zero_ratio_summary": {"title": "零值占比", "what": "看零值和低活跃记录比例。", "use": "判断数据是否存在大量无效、未成交或空转样本。"},
    "coefficient_variation": {"title": "变异系数", "what": "看标准差相对均值的比例。", "use": "判断指标稳定性，区分稳定盘和高波动盘。"},
    "skew_kurtosis_summary": {"title": "偏度峰度", "what": "看分布的偏斜程度和厚尾程度。", "use": "判断是否适合只看均值，还是必须强调分位数。"},
    "missing_profile": {"title": "缺失值画像", "what": "看列级缺失数和缺失率。", "use": "判断哪些字段可直接用于解释，哪些必须降权。"},
    "duplicate_profile": {"title": "重复值画像", "what": "看重复记录规模。", "use": "判断总量是否可能被重复行虚增。"},
    "correlation_matrix": {"title": "相关矩阵", "what": "看指标之间的整体相关关系。", "use": "识别是否有重复口径或强联动指标链。"},
    "correlation_pairs": {"title": "高相关指标对", "what": "筛最强相关的指标组合。", "use": "用于构建关键监控链，不重复讲同一件事。"},
    "correlation_pairs_with_pvalues": {"title": "相关系数与 p 值", "what": "看指标相关系数是否达到统计显著。", "use": "区分强相关中的稳定关系和样本噪声。"},
    "covariance_matrix": {"title": "协方差矩阵", "what": "看指标同向/反向波动幅度。", "use": "补充相关矩阵，辅助理解量纲下的联动强弱。"},
    "anova_results": {"title": "ANOVA 组间检验", "what": "看不同类别组之间的数值均值是否显著不同。", "use": "判断某个分层是否值得作为业务拆盘维度。"},
    "eta_squared_results": {"title": "eta² 效应量", "what": "看分组因素解释了多少数值差异。", "use": "避免只看 p 值，把显著性和实际影响大小分开。"},
    "kruskal_results": {"title": "Kruskal-Wallis 检验", "what": "看非正态或等级数据下组间分布是否不同。", "use": "为问卷等级题和偏态指标提供更稳健的组间检验。"},
    "tukey_hsd_results": {"title": "Tukey HSD 事后比较", "what": "看 ANOVA 后具体哪两组差异显著。", "use": "把整体差异进一步落到具体组别动作。"},
    "chi_square_tests": {"title": "卡方检验", "what": "看两个分类变量是否独立。", "use": "判断性别、年龄、渠道、偏好等分类结构是否存在绑定关系。"},
    "cramers_v_results": {"title": "Cramer's V", "what": "看分类变量关联强度。", "use": "补足卡方检验的效应量，避免只看显著性。"},
    "cronbach_alpha": {"title": "Cronbach's alpha", "what": "看自动识别的 Likert 题项是否具备内部一致性。", "use": "判断量表题是否适合合成或共同解释。"},
    "pca_variance": {"title": "PCA 方差解释", "what": "看主成分解释了多少信息。", "use": "判断数据是否可以压成少数主轴。"},
    "pca_loadings": {"title": "PCA 载荷", "what": "看各指标对主成分的贡献。", "use": "判断主轴背后到底是销量、价格还是成本在驱动。"},
    "pca_scores": {"title": "PCA 得分", "what": "看样本在主成分空间的分布。", "use": "识别是否存在明显分群或异类样本。"},
    "kmeans_clusters": {"title": "KMeans 聚类", "what": "把样本按行为特征分群。", "use": "判断是否存在多类经营模式，不能只看整体均值。"},
    "cluster_profile": {"title": "聚类画像", "what": "看每个簇的均值特征。", "use": "给管理层解释各簇分别代表什么样的对象。"},
    "category_mix": {"title": "类别结构", "what": "看头部类别和结构集中度。", "use": "判断资源或销量是不是过度集中。"},
    "category_share_summary": {"title": "类别占比与累计占比", "what": "看头部类别的累计贡献。", "use": "判断是否已经进入头部集中结构。"},
    "category_metric_summary": {"title": "类别指标摘要", "what": "看每个类别对应的核心指标均值。", "use": "识别哪个类别不只是量大，而且质量更好。"},
    "category_price_band_summary": {"title": "类别价格带摘要", "what": "看类别与价格带的关系。", "use": "判断结构变化是不是由价格带切换带来的。"},
    "budget_variance_summary": {"title": "预算偏差摘要", "what": "看预算与实际在各分层维度上的偏差。", "use": "识别收入、成本偏差是普遍可控还是在某些责任中心、产品线上集中偏离。"},
    "temporal_trend": {"title": "时间趋势", "what": "看时间序列的基础趋势。", "use": "判断是在持续增长、回落还是剧烈波动。"},
    "temporal_growth": {"title": "时间增长率", "what": "看窗口间的增减幅。", "use": "区分趋势延续和短期冲高回落。"},
    "temporal_moving_average": {"title": "移动平均", "what": "看平滑后的趋势。", "use": "弱化噪音，识别真实方向。"},
    "temporal_period_profile": {"title": "周期画像", "what": "看周内/月内等周期特征。", "use": "判断节奏是不是来自周期性规律。"},
    "funnel_metrics": {"title": "漏斗总量", "what": "看流量、加购、收藏、购买各阶段总量。", "use": "识别卡点是在前链路还是后链路。"},
    "funnel_conversion_summary": {"title": "漏斗转化摘要", "what": "看阶段转化率。", "use": "判断转化损失集中在哪一步。"},
    "top_items": {"title": "头部商品摘要", "what": "看头部商品或对象的总量贡献。", "use": "识别哪些对象是真正的结构头部。"},
    "item_metric_summary": {"title": "商品指标摘要", "what": "看头部商品的指标均值或总量。", "use": "判断头部对象是量大还是效率高。"},
    "item_daily_summary": {"title": "商品日级摘要", "what": "看对象在时间维度上的表现。", "use": "判断头部对象是否稳定承接。"},
    "outlier_records": {"title": "异常样本明细", "what": "看被识别出的异常记录。", "use": "给业务复盘具体样本，而不是只报比例。"},
    "numeric_distribution_plot": {"title": "数值分布图", "what": "可视化数值分布。", "use": "辅助判断偏态、长尾和多峰结构。"},
    "numeric_boxplot": {"title": "数值箱线图", "what": "可视化各指标箱线结构。", "use": "看中位数、分散度和异常值。"},
    "numeric_density_plot": {"title": "数值密度图", "what": "看平滑分布形态。", "use": "辅助识别多峰和偏态。"},
    "correlation_heatmap": {"title": "相关热力图", "what": "可视化指标联动强弱。", "use": "帮助快速识别高相关簇。"},
    "numeric_scatter_plot": {"title": "数值散点图", "what": "看两个关键指标的联合分布。", "use": "判断是否有明显线性带、分群或异常点。"},
    "category_mix_plot": {"title": "类别结构图", "what": "可视化头部类别排名。", "use": "直观看头部集中度。"},
    "category_metric_plot": {"title": "类别指标图", "what": "可视化类别与指标的关系。", "use": "辅助判断哪些类别值得继续深挖。"},
    "category_pareto": {"title": "类别帕累托图", "what": "看累计贡献曲线。", "use": "判断是否进入 20/80 结构。"},
    "temporal_trend_plot": {"title": "时间趋势图", "what": "可视化趋势线。", "use": "辅助解释节奏变化。"},
    "temporal_growth_plot": {"title": "时间增长图", "what": "可视化增长率。", "use": "辅助判断冲高回落和转折点。"},
    "temporal_period_plot": {"title": "周期画像图", "what": "可视化周期规律。", "use": "辅助识别周内/月内节奏。"},
    "funnel_overview_plot": {"title": "漏斗图", "what": "可视化漏斗规模。", "use": "帮助直观看链路损失点。"},
    "top_items_plot": {"title": "头部商品图", "what": "可视化头部商品排名。", "use": "帮助识别头部对象集中度。"},
}

R_WORKFLOW_METHOD_SPECS.update(
    {
        "spearman_correlation_pairs": {
            "title": "Spearman correlation",
            "what": "Rank-based correlation with p values.",
            "use": "Use it when numeric fields are ordinal, skewed, or not safely linear.",
        },
        "kendall_correlation_pairs": {
            "title": "Kendall correlation",
            "what": "Rank-order association with p values.",
            "use": "Use it as a conservative relationship check for smaller or ordinal samples.",
        },
        "p_value_adjustment_summary": {
            "title": "P-value adjustment",
            "what": "BH/FDR and Bonferroni correction over available p-value results.",
            "use": "Reduce false positives when many statistical tests are run.",
        },
        "normality_diagnostics": {
            "title": "Normality diagnostics",
            "what": "Skewness, kurtosis, and normality test signals for numeric fields.",
            "use": "Decide whether parametric readings should be down-weighted.",
        },
        "variance_homogeneity_tests": {
            "title": "Variance homogeneity",
            "what": "Levene and Brown-Forsythe tests for grouped numeric comparisons.",
            "use": "Check whether standard ANOVA assumptions are reasonable.",
        },
        "welch_anova_results": {
            "title": "Welch ANOVA",
            "what": "ANOVA variant that is safer when group variances differ.",
            "use": "Keep group-difference analysis useful on messy business data.",
        },
        "dunn_posthoc_results": {
            "title": "Dunn posthoc",
            "what": "Pairwise rank comparisons after significant Kruskal-Wallis tests.",
            "use": "Locate which groups differ when the non-parametric omnibus test is significant.",
        },
        "chi_square_residuals": {
            "title": "Chi-square residuals",
            "what": "Cell-level standardized residuals for contingency tables.",
            "use": "Explain which category combinations drive a chi-square relationship.",
        },
        "confidence_intervals": {
            "title": "Confidence intervals",
            "what": "95% intervals for means and binary proportions.",
            "use": "Separate point estimates from uncertainty bands.",
        },
        "missingness_diagnostics": {
            "title": "Missingness diagnostics",
            "what": "Column-level missing counts and rates.",
            "use": "Decide which fields can be trusted and which need caution.",
        },
        "low_information_columns": {
            "title": "Low-information columns",
            "what": "Constant, near-zero variance, and high-duplicate fields.",
            "use": "Avoid over-interpreting fields that carry little analytical signal.",
        },
        "outlier_influence_summary": {
            "title": "Outlier influence",
            "what": "IQR/MAD outlier rates and mean sensitivity.",
            "use": "Flag metrics whose averages are dominated by extreme records.",
        },
        "generic_missingness_bar_plot": {
            "title": "Generic missingness bar chart",
            "what": "Show fields with the highest missingness.",
            "use": "Make data-quality gaps visible before business interpretation.",
        },
        "generic_correlation_bubble": {
            "title": "Generic correlation bubble",
            "what": "Bubble the strongest numeric relationships by absolute correlation.",
            "use": "Find linked metrics without forcing the reader through a dense matrix.",
        },
        "generic_category_metric_heatmap": {
            "title": "Generic category metric heatmap",
            "what": "Compare category levels across several numeric metrics.",
            "use": "See which segments over-index or under-index on core operating metrics.",
        },
        "generic_outlier_influence_bubble": {
            "title": "Generic outlier influence bubble",
            "what": "Plot outlier rate against how much outliers shift the mean.",
            "use": "Separate harmless outliers from metrics whose averages are unstable.",
        },
        "generic_time_trend_grid": {
            "title": "Generic time trend grid",
            "what": "Show normalized trends for several numeric metrics over time.",
            "use": "Expose growth, decline, and turning points across the main metric set.",
        },
        "generic_numeric_distribution_grid": {
            "title": "Generic numeric distribution grid",
            "what": "Show histogram small multiples for top numeric metrics.",
            "use": "Expose skew, long tails, concentration, and multi-peak operating patterns.",
        },
        "generic_cumulative_contribution_curve": {
            "title": "Generic cumulative contribution curve",
            "what": "Show how quickly a selected metric accumulates across ranked category levels.",
            "use": "Quantify whether performance is concentrated in a small head or broadly distributed.",
        },
        "generic_segment_bubble": {
            "title": "Generic segment bubble",
            "what": "Plot segment sample/share size against metric lift.",
            "use": "Prioritize segments that are both large enough and meaningfully over- or under-indexed.",
        },
        "generic_top_bottom_performer": {
            "title": "Generic top bottom performer",
            "what": "Show the strongest and weakest category levels for a selected metric.",
            "use": "Make benchmark gaps directly actionable for operations.",
        },
        "generic_key_metric_scatter_bubble": {
            "title": "Generic key metric scatter bubble",
            "what": "Plot row-level relationship between two key metrics with optional bubble sizing.",
            "use": "Reveal clusters, outliers, and non-linear tradeoffs behind aggregate correlations.",
        },
    }
)

R_WORKFLOW_METHOD_SPECS.update(
    {
        "survey_field_map": {
            "title": "Survey field map",
            "what": "Map long questionnaire fields to short labels and survey roles.",
            "use": "Keep survey charts readable without changing the original source columns.",
        },
        "survey_multi_select_rates": {
            "title": "Survey multi-select rates",
            "what": "Show selection rates for 0/1 multi-select questionnaire options.",
            "use": "Replace misleading continuous numeric charts for multi-select fields.",
        },
        "survey_likert_summary": {
            "title": "Survey Likert summary",
            "what": "Summarize Likert means, uncertainty bands, and positive/negative rates.",
            "use": "Read ordinal questionnaire items without treating them as ordinary business metrics.",
        },
        "survey_likert_distribution": {
            "title": "Survey Likert distribution",
            "what": "Show the response mix for each Likert item.",
            "use": "Reveal polarization and concentration that a single mean can hide.",
        },
        "survey_multi_select_cooccurrence": {
            "title": "Survey multi-select co-occurrence",
            "what": "Measure which binary multi-select options tend to be selected together.",
            "use": "Find bundled needs, choice clusters, and option combinations behind top-line selection rates.",
        },
        "survey_likert_correlation": {
            "title": "Survey Likert correlation",
            "what": "Measure rank associations between Likert items.",
            "use": "Find attitude structures and redundant or reinforcing questionnaire items.",
        },
        "survey_segment_likert_means": {
            "title": "Survey segment Likert means",
            "what": "Compare Likert item means by available respondent segments.",
            "use": "Locate audience groups whose attitudes or cognition differ from the overall average.",
        },
        "survey_segment_distribution": {
            "title": "Survey segment distribution",
            "what": "Show respondent composition across detected segment dimensions.",
            "use": "Avoid interpreting survey findings without knowing which audiences dominate the sample.",
        },
        "survey_segment_multi_select_rates": {
            "title": "Survey segment multi-select rates",
            "what": "Compare option selection rates across respondent segments.",
            "use": "Find which needs or choices are concentrated in specific audience groups.",
        },
        "survey_likert_sentiment_balance": {
            "title": "Survey Likert sentiment balance",
            "what": "Compare positive, neutral, negative, and net-positive rates by Likert item.",
            "use": "Separate broadly positive items from polarized or weakly supported items.",
        },
        "survey_multi_select_portfolio": {
            "title": "Survey multi-select portfolio",
            "what": "Place options by reach and co-selection lift.",
            "use": "Identify high-reach standalone options versus options that work as bundles.",
        },
        "survey_segment_multi_select_bubble": {
            "title": "Survey segment multi-select bubble",
            "what": "Bubble segment-by-option selection rates and gaps versus the overall rate.",
            "use": "Show which audience segments over-index on specific multi-select options.",
        },
        "survey_segment_likert_bubble": {
            "title": "Survey segment Likert bubble",
            "what": "Bubble segment-by-item Likert means and gaps versus the overall mean.",
            "use": "Show which segments are meaningfully above or below the overall attitude baseline.",
        },
        "survey_multi_select_rates_plot": {
            "title": "Survey multi-select rates chart",
            "what": "Readable horizontal bar chart for multi-select option rates.",
            "use": "Make questionnaire option uptake visible without overcrowded full question labels.",
        },
        "survey_likert_mean_ci_plot": {
            "title": "Survey Likert mean CI chart",
            "what": "Readable Likert mean chart with 95% confidence intervals.",
            "use": "Show which attitude items are strongest while keeping uncertainty visible.",
        },
        "survey_likert_distribution_plot": {
            "title": "Survey Likert distribution chart",
            "what": "Readable stacked chart for Likert response shares.",
            "use": "Show whether means are driven by broad agreement or polarized responses.",
        },
        "survey_multi_select_cooccurrence_plot": {
            "title": "Survey multi-select co-occurrence heatmap",
            "what": "Readable heatmap for pairwise multi-select co-selection.",
            "use": "Show which options form bundles rather than isolated preferences.",
        },
        "survey_likert_correlation_heatmap": {
            "title": "Survey Likert correlation heatmap",
            "what": "Readable heatmap for Likert item association strength.",
            "use": "Show the questionnaire's latent attitude structure.",
        },
        "survey_segment_likert_heatmap": {
            "title": "Survey segment Likert heatmap",
            "what": "Readable heatmap for segment-by-item mean differences.",
            "use": "Show where audience segmentation changes the interpretation.",
        },
        "survey_segment_distribution_plot": {
            "title": "Survey segment distribution chart",
            "what": "Readable bar chart for respondent segment composition.",
            "use": "Keep sample structure visible before drawing business conclusions.",
        },
        "survey_segment_multi_select_heatmap": {
            "title": "Survey segment multi-select heatmap",
            "what": "Readable heatmap for segment-by-option selection rates.",
            "use": "Expose audience-specific option preference differences.",
        },
        "survey_likert_sentiment_balance_plot": {
            "title": "Survey Likert sentiment balance chart",
            "what": "Readable bar chart for net-positive Likert signals.",
            "use": "Rank questionnaire items by support strength and risk.",
        },
        "survey_multi_select_portfolio_plot": {
            "title": "Survey multi-select portfolio chart",
            "what": "Readable scatter chart for option reach versus bundle lift.",
            "use": "Prioritize options by both popularity and relationship to other choices.",
        },
        "survey_segment_multi_select_bubble_plot": {
            "title": "Survey segment multi-select bubble chart",
            "what": "Readable bubble chart for segment-specific option preference gaps.",
            "use": "Quickly locate audience groups with unusually strong option demand.",
        },
        "survey_segment_likert_bubble_plot": {
            "title": "Survey segment Likert bubble chart",
            "what": "Readable bubble chart for segment-specific Likert mean gaps.",
            "use": "Quickly locate audience groups with unusually high or low attitudes.",
        },
    }
)

R_WORKFLOW_METHOD_SPECS["pca_axis_summary"] = {
    "title": "PCA 涓昏酱涓氬姟鎽樿",
    "what": "把主成分翻译成业务主轴。",
    "use": "帮助理解主轴代表的是规模、履约、成本还是结构差异。",
}
R_WORKFLOW_METHOD_SPECS["cluster_member_detail"] = {
    "title": "鑱氱被鎴愬憳鏄庣粏",
    "what": "看每个簇里具体有哪些成员。",
    "use": "把聚类结果落到具体对象明细，支持复核和后续运营动作。",
}


def _resolve_rscript_path() -> str | None:
    settings = load_runtime_settings_raw()
    configured = str(settings.get("rscript_path") or "").strip()
    if configured and Path(configured).exists():
        return configured
    for candidate in bundled_rscript_candidates():
        if candidate.exists():
            return str(candidate.resolve())
    discovered = shutil.which("Rscript")
    return discovered


def _csv_ready_frame(frame: pd.DataFrame) -> pd.DataFrame:
    export_frame = frame.copy()
    for column in export_frame.columns:
        if pd.api.types.is_datetime64_any_dtype(export_frame[column]):
            export_frame[column] = export_frame[column].dt.strftime("%Y-%m-%d %H:%M:%S")
    return export_frame.where(pd.notnull(export_frame), None)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_csv_artifact(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows, columns=columns)
    frame.to_csv(path, index=False, encoding="utf-8-sig")


def _numeric_series_for_inference(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def _rw_significance_label(p_value: Any, q_value: Any, n: Any) -> str:
    n_value = int(n or 0)
    if n_value < 8:
        return "样本不足"
    p = _safe_float(p_value)
    q = _safe_float(q_value)
    if p is not None and q is not None and p < 0.05 and q < 0.05:
        return "显著"
    if (p is not None and p < 0.10) or (q is not None and q < 0.10):
        return "边缘显著"
    return "不显著"


def _rw_pearson_payload(left_series: pd.Series, right_series: pd.Series) -> dict[str, Any] | None:
    pair = pd.DataFrame({"left": left_series, "right": right_series}).dropna()
    n = int(len(pair))
    if n < 8 or int(pair["left"].nunique()) < 2 or int(pair["right"].nunique()) < 2:
        return None
    corr_value = pair["left"].corr(pair["right"], method="pearson")
    if pd.isna(corr_value):
        return None
    r_value = max(min(float(corr_value), 0.999999999), -0.999999999)
    p_value: float | None = None
    try:
        from scipy import stats  # type: ignore

        _r, scipy_p = stats.pearsonr(pair["left"].to_numpy(), pair["right"].to_numpy())
        p_value = float(scipy_p)
    except Exception:
        if n > 2 and abs(r_value) < 1:
            t_value = abs(r_value) * math.sqrt((n - 2) / max(1e-12, 1 - r_value * r_value))
            p_value = float(math.erfc(t_value / math.sqrt(2)))
    ci_low: float | None = None
    ci_high: float | None = None
    if n > 3 and abs(r_value) < 1:
        fisher_z = math.atanh(r_value)
        se = 1 / math.sqrt(n - 3)
        ci_low = math.tanh(fisher_z - 1.96 * se)
        ci_high = math.tanh(fisher_z + 1.96 * se)
    return {
        "n": n,
        "pearson_r": r_value,
        "correlation": r_value,
        "abs_correlation": abs(r_value),
        "p_value": p_value,
        "ci95_low": ci_low,
        "ci95_high": ci_high,
    }


def _rw_add_bh_q_values(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    indexed = [(idx, _safe_float(row.get("p_value"))) for idx, row in enumerate(rows) if _safe_float(row.get("p_value")) is not None]
    m = len(indexed)
    if not m:
        for row in rows:
            row["q_value_bh"] = None
            row["significance_label"] = _rw_significance_label(row.get("p_value"), None, row.get("n"))
        return rows
    ordered = sorted(indexed, key=lambda item: item[1] if item[1] is not None else 1.0)
    q_by_index: dict[int, float] = {}
    running = 1.0
    for rank_from_end, (idx, p_value) in enumerate(reversed(ordered), start=1):
        rank = m - rank_from_end + 1
        p = float(p_value) if p_value is not None else 1.0
        q = min(running, p * m / rank)
        running = q
        q_by_index[idx] = min(q, 1.0)
    for idx, row in enumerate(rows):
        row["q_value_bh"] = q_by_index.get(idx)
        row["significance_label"] = _rw_significance_label(row.get("p_value"), row.get("q_value_bh"), row.get("n"))
    return rows


def _categorical_series_for_inference(series: pd.Series) -> pd.Series:
    text = series.astype("string").str.strip()
    text = text.mask(text.isin(["", "nan", "None", "<NA>"]))
    return text


def _infer_inference_numeric_columns(frame: pd.DataFrame) -> list[str]:
    selected: list[str] = []
    for column in frame.columns.astype(str).tolist():
        numeric = _numeric_series_for_inference(frame[column])
        if int(numeric.notna().sum()) < 3:
            continue
        if int(numeric.dropna().nunique()) <= 1:
            continue
        selected.append(column)
    return selected


def _infer_inference_categorical_columns(frame: pd.DataFrame) -> list[str]:
    selected: list[str] = []
    row_count = max(len(frame), 1)
    max_cardinality = max(8, min(30, int(row_count * 0.35)))
    for column in frame.columns.astype(str).tolist():
        values = _categorical_series_for_inference(frame[column]).dropna()
        unique_count = int(values.nunique())
        if unique_count < 2 or unique_count > max_cardinality:
            continue
        selected.append(column)
    return selected


def _valid_grouped_numeric_values(
    frame: pd.DataFrame,
    *,
    group_column: str,
    target_column: str,
    min_group_size: int = 2,
) -> tuple[pd.DataFrame, list[pd.Series]]:
    group = _categorical_series_for_inference(frame[group_column])
    target = _numeric_series_for_inference(frame[target_column])
    valid = pd.DataFrame({"group": group, "value": target}).dropna()
    if valid.empty:
        return valid, []
    groups: list[pd.Series] = []
    for _group_name, group_frame in valid.groupby("group", dropna=True):
        values = group_frame["value"].dropna()
        if len(values) >= min_group_size and int(values.nunique()) > 1:
            groups.append(values)
    return valid, groups


def _append_method_log_rows(workflow_dir: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    method_log_path = workflow_dir / "method_log.csv"
    existing = pd.DataFrame(columns=["method", "output", "status", "note"])
    if method_log_path.exists():
        try:
            existing = pd.read_csv(method_log_path, encoding="utf-8-sig")
        except Exception:
            existing = pd.DataFrame(columns=["method", "output", "status", "note"])
    appended = pd.concat([existing, pd.DataFrame(rows)], ignore_index=True)
    appended = appended.drop_duplicates(subset=["method", "output"], keep="last")
    appended.to_csv(method_log_path, index=False, encoding="utf-8-sig")


def _r_workflow_numeric_columns(
    frame: pd.DataFrame,
    column_role_registry: dict[str, Any],
    *,
    limit: int = 24,
) -> list[str]:
    selected: list[str] = []
    for column in list(column_role_registry.get("numeric_method_columns") or []):
        if column in frame.columns and column not in selected:
            selected.append(column)
    for column in _infer_inference_numeric_columns(frame):
        if column not in selected:
            selected.append(column)
    return selected[:limit]


def _r_workflow_categorical_columns(
    frame: pd.DataFrame,
    column_role_registry: dict[str, Any],
    *,
    limit: int = 24,
) -> list[str]:
    selected: list[str] = []
    for column in list(column_role_registry.get("category_dimension_columns") or []):
        if column in frame.columns and column not in selected:
            selected.append(column)
    for column in _infer_inference_categorical_columns(frame):
        if column not in selected:
            selected.append(column)
    return selected[:limit]


SURVEY_VISUAL_IMAGE_ORDER = [
    "survey_multi_select_rates.png",
    "survey_multi_select_cooccurrence.png",
    "survey_multi_select_portfolio.png",
    "survey_segment_distribution.png",
    "survey_segment_multi_select_heatmap.png",
    "survey_segment_multi_select_bubble.png",
    "survey_likert_mean_ci.png",
    "survey_likert_sentiment_balance.png",
    "survey_likert_distribution.png",
    "survey_likert_correlation_heatmap.png",
    "survey_segment_likert_heatmap.png",
    "survey_segment_likert_bubble.png",
]

SURVEY_UNSUITABLE_GENERIC_IMAGES = {
    "numeric_boxplot.png",
    "numeric_density.png",
    "numeric_scatter_plot.png",
    "category_metric_plot.png",
}

GENERIC_VISUAL_IMAGE_ORDER = [
    "generic_missingness_bar.png",
    "generic_correlation_bubble.png",
    "generic_category_metric_heatmap.png",
    "generic_segment_bubble.png",
    "generic_top_bottom_performer.png",
    "generic_cumulative_contribution_curve.png",
    "generic_key_metric_scatter_bubble.png",
    "generic_numeric_distribution_grid.png",
    "generic_outlier_influence_bubble.png",
    "generic_time_trend_grid.png",
]


def _looks_like_questionnaire_field(column_name: str) -> bool:
    text = str(column_name or "").strip()
    if not text:
        return False
    return bool(
        re.search(r"^\s*\d+[\.\、]", text)
        or re.search(r"问卷|您的|你|您|请选择|以下哪些|多选|单选|满意|同意|认同|评分|态度|意愿|兴趣|可能|是否", text)
    )


def _is_binary_option_series(series: pd.Series) -> bool:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if len(numeric) < 10:
        return False
    unique_values = {float(value) for value in numeric.unique().tolist()}
    return bool(unique_values) and unique_values.issubset({0.0, 1.0}) and len(unique_values) >= 2


def _is_likert_series(series: pd.Series) -> bool:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if len(numeric) < 20 or int(numeric.nunique()) < 3:
        return False
    rounded = numeric.round()
    if not bool((numeric - rounded).abs().le(1e-9).all()):
        return False
    values = {int(value) for value in rounded.unique().tolist()}
    return values.issubset(set(range(1, 6))) or values.issubset(set(range(1, 8)))


def _survey_short_labels(columns: list[str]) -> dict[str, str]:
    labels: dict[str, str] = {}
    used: dict[str, int] = {}
    for index, column in enumerate(columns, start=1):
        text = str(column or "").strip()
        question_match = re.match(r"\s*(\d+)[\.\、]", text)
        if question_match:
            label = f"Q{question_match.group(1)}"
            option_match = re.search(r"\s-\s*([A-Za-z])[\.\、]?", text)
            if option_match:
                label = f"{label}-{option_match.group(1).upper()}"
        else:
            label = f"S{index}"
        count = used.get(label, 0) + 1
        used[label] = count
        labels[text] = label if count == 1 else f"{label}.{count}"
    return labels


def _detect_questionnaire_columns(frame: pd.DataFrame) -> dict[str, Any]:
    columns = [str(column) for column in frame.columns]
    question_like = [column for column in columns if _looks_like_questionnaire_field(column)]
    binary_options = [
        column
        for column in question_like
        if column in frame.columns and _is_binary_option_series(frame[column])
    ]
    likert_items = [
        column
        for column in question_like
        if column in frame.columns and _is_likert_series(frame[column])
    ]
    categorical_dimensions: list[str] = []
    for column in columns:
        if column not in frame.columns or column in binary_options or column in likert_items:
            continue
        text = str(column)
        values = _categorical_series_for_inference(frame[column]).dropna()
        unique_count = int(values.nunique())
        if unique_count < 2 or unique_count > 20:
            continue
        if _looks_like_questionnaire_field(text) or re.search(r"性别|年龄|年级|地区|职业|收入|学历|城市", text):
            categorical_dimensions.append(column)

    is_questionnaire = (
        len(question_like) >= 4
        and (len(binary_options) + len(likert_items)) >= 4
        and (len(binary_options) >= 2 or len(likert_items) >= 3)
    )
    labels = _survey_short_labels([*binary_options, *likert_items, *categorical_dimensions])
    return {
        "is_questionnaire": is_questionnaire,
        "question_like_columns": question_like,
        "binary_options": binary_options,
        "likert_items": likert_items,
        "categorical_dimensions": categorical_dimensions[:8],
        "short_labels": labels,
    }


def _configure_matplotlib_for_chinese(plt: Any) -> None:
    try:
        from matplotlib import font_manager

        for font_path in [
            Path(r"C:\Windows\Fonts\Noto Sans SC.ttf"),
            Path(r"C:\Windows\Fonts\NotoSansSC-Regular.ttf"),
            Path(r"C:\Windows\Fonts\msyh.ttc"),
            Path(r"C:\Windows\Fonts\simhei.ttf"),
            Path(r"C:\Windows\Fonts\simsun.ttc"),
        ]:
            if font_path.exists():
                font_manager.fontManager.addfont(str(font_path))
                prop = font_manager.FontProperties(fname=str(font_path))
                plt.rcParams["font.family"] = prop.get_name()
                break
        plt.rcParams["axes.unicode_minus"] = False
    except Exception:
        pass


def _plot_survey_multi_select_rates(path: Path, rows: list[dict[str, Any]]) -> bool:
    if not rows:
        return False
    try:
        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt

        _configure_matplotlib_for_chinese(plt)
        ordered = sorted(rows, key=lambda row: float(row.get("selected_rate") or 0), reverse=True)[:20]
        labels = [str(row.get("short_label") or "") for row in ordered]
        values = [float(row.get("selected_rate") or 0) * 100 for row in ordered]
        fig_height = max(4.8, 0.34 * len(ordered) + 1.2)
        fig, ax = plt.subplots(figsize=(10.5, fig_height))
        ax.barh(labels[::-1], values[::-1], color="#1f6f8b")
        ax.set_xlim(0, max(100, max(values) * 1.12))
        ax.set_xlabel("选择率 (%)")
        ax.set_title("问卷多选项选择率")
        for index, value in enumerate(values[::-1]):
            ax.text(value + 1, index, f"{value:.1f}%", va="center", fontsize=9)
        ax.grid(axis="x", alpha=0.18)
        fig.tight_layout()
        fig.savefig(path, dpi=180)
        plt.close(fig)
        return True
    except Exception:
        return False


def _plot_survey_likert_mean_ci(path: Path, rows: list[dict[str, Any]]) -> bool:
    if not rows:
        return False
    try:
        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt

        _configure_matplotlib_for_chinese(plt)
        ordered = sorted(rows, key=lambda row: float(row.get("mean") or 0), reverse=True)[:16]
        labels = [str(row.get("short_label") or "") for row in ordered]
        means = [float(row.get("mean") or 0) for row in ordered]
        lows = [float(row.get("ci_low") or row.get("mean") or 0) for row in ordered]
        highs = [float(row.get("ci_high") or row.get("mean") or 0) for row in ordered]
        xerr = [[max(mean - low, 0) for mean, low in zip(means, lows)], [max(high - mean, 0) for mean, high in zip(means, highs)]]
        fig_height = max(4.8, 0.36 * len(ordered) + 1.2)
        fig, ax = plt.subplots(figsize=(10.5, fig_height))
        y_pos = list(range(len(ordered)))
        ax.errorbar(means[::-1], y_pos, xerr=[xerr[0][::-1], xerr[1][::-1]], fmt="o", color="#0f2a44", ecolor="#7aa5c7", capsize=4)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels[::-1])
        max_scale = max(float(row.get("scale_max") or 5) for row in ordered)
        ax.set_xlim(0.8, max_scale + 0.2)
        ax.set_xlabel("均值及 95% CI")
        ax.set_title("Likert 题项均值与置信区间")
        ax.grid(axis="x", alpha=0.2)
        fig.tight_layout()
        fig.savefig(path, dpi=180)
        plt.close(fig)
        return True
    except Exception:
        return False


def _plot_survey_likert_distribution(path: Path, rows: list[dict[str, Any]]) -> bool:
    if not rows:
        return False
    try:
        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt

        _configure_matplotlib_for_chinese(plt)
        labels = list(dict.fromkeys(str(row.get("short_label") or "") for row in rows if str(row.get("short_label") or "")))[:12]
        response_values = sorted({int(float(row.get("response_value") or 0)) for row in rows if str(row.get("response_value") or "").strip()})
        if not labels or not response_values:
            return False
        rate_map = {
            (str(row.get("short_label") or ""), int(float(row.get("response_value") or 0))): float(row.get("rate") or 0) * 100
            for row in rows
        }
        fig_height = max(4.8, 0.36 * len(labels) + 1.4)
        fig, ax = plt.subplots(figsize=(10.8, fig_height))
        left = [0.0] * len(labels)
        colors = ["#9e2f2f", "#d77a61", "#e7d8a8", "#8fbf9f", "#1f7a5b", "#155c7a", "#083d5a"]
        for idx, response_value in enumerate(response_values):
            values = [rate_map.get((label, response_value), 0.0) for label in labels]
            ax.barh(labels, values, left=left, color=colors[idx % len(colors)], label=str(response_value))
            left = [base + value for base, value in zip(left, values)]
        ax.set_xlim(0, 100)
        ax.set_xlabel("回答占比 (%)")
        ax.set_title("Likert 回答分布")
        ax.legend(title="选项", ncol=min(len(response_values), 7), loc="lower center", bbox_to_anchor=(0.5, -0.22))
        ax.grid(axis="x", alpha=0.15)
        fig.tight_layout()
        fig.savefig(path, dpi=180)
        plt.close(fig)
        return True
    except Exception:
        return False


def _plot_survey_multi_select_cooccurrence(path: Path, rows: list[dict[str, Any]]) -> bool:
    if not rows:
        return False
    try:
        import numpy as np
        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt

        _configure_matplotlib_for_chinese(plt)
        labels = sorted(
            {
                str(row.get("option_a_short") or "")
                for row in rows
                if str(row.get("option_a_short") or "").strip()
            }
            | {
                str(row.get("option_b_short") or "")
                for row in rows
                if str(row.get("option_b_short") or "").strip()
            }
        )[:14]
        if len(labels) < 2:
            return False
        index = {label: offset for offset, label in enumerate(labels)}
        matrix = np.zeros((len(labels), len(labels)), dtype=float)
        for row in rows:
            left = str(row.get("option_a_short") or "")
            right = str(row.get("option_b_short") or "")
            if left in index and right in index:
                value = float(row.get("co_selected_rate") or 0) * 100
                matrix[index[left], index[right]] = value
                matrix[index[right], index[left]] = value
        fig_size = max(6.8, 0.48 * len(labels) + 3.2)
        fig, ax = plt.subplots(figsize=(fig_size, fig_size))
        im = ax.imshow(matrix, cmap="Blues", vmin=0, vmax=max(float(matrix.max()), 1.0))
        ax.set_xticks(range(len(labels)))
        ax.set_yticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.set_yticklabels(labels)
        ax.set_title("Multi-select co-selection rate (%)")
        for row_index in range(len(labels)):
            for col_index in range(len(labels)):
                if row_index != col_index and matrix[row_index, col_index] >= 1:
                    ax.text(col_index, row_index, f"{matrix[row_index, col_index]:.0f}", ha="center", va="center", fontsize=7)
        fig.colorbar(im, ax=ax, shrink=0.78)
        fig.tight_layout()
        fig.savefig(path, dpi=180)
        plt.close(fig)
        return True
    except Exception:
        return False


def _plot_survey_likert_correlation_heatmap(path: Path, rows: list[dict[str, Any]]) -> bool:
    if not rows:
        return False
    try:
        import numpy as np
        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt

        _configure_matplotlib_for_chinese(plt)
        labels = sorted(
            {
                str(row.get("item_a_short") or "")
                for row in rows
                if str(row.get("item_a_short") or "").strip()
            }
            | {
                str(row.get("item_b_short") or "")
                for row in rows
                if str(row.get("item_b_short") or "").strip()
            }
        )[:14]
        if len(labels) < 2:
            return False
        index = {label: offset for offset, label in enumerate(labels)}
        matrix = np.eye(len(labels), dtype=float)
        for row in rows:
            left = str(row.get("item_a_short") or "")
            right = str(row.get("item_b_short") or "")
            if left in index and right in index:
                value = float(row.get("spearman_corr") or 0)
                matrix[index[left], index[right]] = value
                matrix[index[right], index[left]] = value
        fig_size = max(6.8, 0.48 * len(labels) + 3.2)
        fig, ax = plt.subplots(figsize=(fig_size, fig_size))
        im = ax.imshow(matrix, cmap="RdBu_r", vmin=-1, vmax=1)
        ax.set_xticks(range(len(labels)))
        ax.set_yticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.set_yticklabels(labels)
        ax.set_title("Likert item Spearman correlation")
        for row_index in range(len(labels)):
            for col_index in range(len(labels)):
                value = matrix[row_index, col_index]
                if abs(value) >= 0.3 or row_index == col_index:
                    ax.text(col_index, row_index, f"{value:.2f}", ha="center", va="center", fontsize=7)
        fig.colorbar(im, ax=ax, shrink=0.78)
        fig.tight_layout()
        fig.savefig(path, dpi=180)
        plt.close(fig)
        return True
    except Exception:
        return False


def _plot_survey_segment_likert_heatmap(path: Path, rows: list[dict[str, Any]]) -> bool:
    if not rows:
        return False
    try:
        import numpy as np
        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt

        _configure_matplotlib_for_chinese(plt)
        dimension_order: list[str] = []
        for row in rows:
            dimension = str(row.get("segment_short") or row.get("segment_column") or "")
            if dimension and dimension not in dimension_order:
                dimension_order.append(dimension)
        if not dimension_order:
            return False
        selected_dimension = max(
            dimension_order,
            key=lambda dimension: sum(1 for row in rows if str(row.get("segment_short") or row.get("segment_column") or "") == dimension),
        )
        selected_rows = [
            row
            for row in rows
            if str(row.get("segment_short") or row.get("segment_column") or "") == selected_dimension
        ]
        levels = list(dict.fromkeys(str(row.get("segment_level") or "") for row in selected_rows if str(row.get("segment_level") or "")))[:10]
        items = list(dict.fromkeys(str(row.get("likert_short") or "") for row in selected_rows if str(row.get("likert_short") or "")))[:14]
        if len(levels) < 2 or len(items) < 2:
            return False
        matrix = np.full((len(levels), len(items)), np.nan, dtype=float)
        level_index = {label: offset for offset, label in enumerate(levels)}
        item_index = {label: offset for offset, label in enumerate(items)}
        for row in selected_rows:
            level = str(row.get("segment_level") or "")
            item = str(row.get("likert_short") or "")
            if level in level_index and item in item_index:
                matrix[level_index[level], item_index[item]] = float(row.get("mean") or np.nan)
        fig_width = max(8.0, 0.45 * len(items) + 4.0)
        fig_height = max(4.8, 0.42 * len(levels) + 2.2)
        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        finite_values = matrix[np.isfinite(matrix)]
        vmin = min(float(finite_values.min()), 1.0) if finite_values.size else 1.0
        vmax = max(float(finite_values.max()), 5.0) if finite_values.size else 5.0
        im = ax.imshow(matrix, cmap="YlGnBu", vmin=vmin, vmax=vmax)
        ax.set_xticks(range(len(items)))
        ax.set_yticks(range(len(levels)))
        ax.set_xticklabels(items, rotation=45, ha="right")
        ax.set_yticklabels(levels)
        ax.set_title(f"Segment Likert means: {selected_dimension}")
        for row_index in range(len(levels)):
            for col_index in range(len(items)):
                value = matrix[row_index, col_index]
                if np.isfinite(value):
                    ax.text(col_index, row_index, f"{value:.1f}", ha="center", va="center", fontsize=7)
        fig.colorbar(im, ax=ax, shrink=0.8)
        fig.tight_layout()
        fig.savefig(path, dpi=180)
        plt.close(fig)
        return True
    except Exception:
        return False


def _plot_survey_segment_distribution(path: Path, rows: list[dict[str, Any]]) -> bool:
    if not rows:
        return False
    try:
        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt

        _configure_matplotlib_for_chinese(plt)
        dimensions = list(dict.fromkeys(str(row.get("segment_short") or row.get("segment_column") or "") for row in rows))
        if not dimensions:
            return False
        selected_dimension = max(
            dimensions,
            key=lambda dimension: sum(1 for row in rows if str(row.get("segment_short") or row.get("segment_column") or "") == dimension),
        )
        selected_rows = [
            row
            for row in rows
            if str(row.get("segment_short") or row.get("segment_column") or "") == selected_dimension
        ][:12]
        if not selected_rows:
            return False
        labels = [str(row.get("segment_level") or "") for row in selected_rows]
        values = [float(row.get("rate") or 0) * 100 for row in selected_rows]
        fig_height = max(4.8, 0.36 * len(labels) + 1.4)
        fig, ax = plt.subplots(figsize=(10.5, fig_height))
        ax.barh(labels[::-1], values[::-1], color="#315c8c")
        ax.set_xlim(0, max(100, max(values) * 1.12))
        ax.set_xlabel("Share (%)")
        ax.set_title(f"Respondent mix: {selected_dimension}")
        for index, value in enumerate(values[::-1]):
            ax.text(value + 1, index, f"{value:.1f}%", va="center", fontsize=9)
        ax.grid(axis="x", alpha=0.18)
        fig.tight_layout()
        fig.savefig(path, dpi=180)
        plt.close(fig)
        return True
    except Exception:
        return False


def _plot_survey_segment_multi_select_heatmap(path: Path, rows: list[dict[str, Any]]) -> bool:
    if not rows:
        return False
    try:
        import numpy as np
        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt

        _configure_matplotlib_for_chinese(plt)
        dimensions = list(dict.fromkeys(str(row.get("segment_short") or row.get("segment_column") or "") for row in rows))
        if not dimensions:
            return False
        selected_dimension = max(
            dimensions,
            key=lambda dimension: sum(1 for row in rows if str(row.get("segment_short") or row.get("segment_column") or "") == dimension),
        )
        selected_rows = [
            row
            for row in rows
            if str(row.get("segment_short") or row.get("segment_column") or "") == selected_dimension
        ]
        levels = list(dict.fromkeys(str(row.get("segment_level") or "") for row in selected_rows if str(row.get("segment_level") or "")))[:10]
        options = list(dict.fromkeys(str(row.get("option_short") or "") for row in selected_rows if str(row.get("option_short") or "")))[:14]
        if len(levels) < 2 or len(options) < 2:
            return False
        matrix = np.full((len(levels), len(options)), np.nan, dtype=float)
        level_index = {label: offset for offset, label in enumerate(levels)}
        option_index = {label: offset for offset, label in enumerate(options)}
        for row in selected_rows:
            level = str(row.get("segment_level") or "")
            option = str(row.get("option_short") or "")
            if level in level_index and option in option_index:
                matrix[level_index[level], option_index[option]] = float(row.get("selected_rate") or np.nan) * 100
        fig_width = max(8.5, 0.48 * len(options) + 4.0)
        fig_height = max(4.8, 0.42 * len(levels) + 2.2)
        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        im = ax.imshow(matrix, cmap="YlGnBu", vmin=0, vmax=100)
        ax.set_xticks(range(len(options)))
        ax.set_yticks(range(len(levels)))
        ax.set_xticklabels(options, rotation=45, ha="right")
        ax.set_yticklabels(levels)
        ax.set_title(f"Segment option rates: {selected_dimension}")
        for row_index in range(len(levels)):
            for col_index in range(len(options)):
                value = matrix[row_index, col_index]
                if np.isfinite(value):
                    ax.text(col_index, row_index, f"{value:.0f}", ha="center", va="center", fontsize=7)
        fig.colorbar(im, ax=ax, shrink=0.8)
        fig.tight_layout()
        fig.savefig(path, dpi=180)
        plt.close(fig)
        return True
    except Exception:
        return False


def _plot_survey_likert_sentiment_balance(path: Path, rows: list[dict[str, Any]]) -> bool:
    if not rows:
        return False
    try:
        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt

        _configure_matplotlib_for_chinese(plt)
        ordered = sorted(rows, key=lambda row: float(row.get("net_positive_rate") or 0), reverse=True)[:18]
        labels = [str(row.get("short_label") or "") for row in ordered]
        positive = [float(row.get("positive_rate") or 0) * 100 for row in ordered]
        negative = [-float(row.get("negative_rate") or 0) * 100 for row in ordered]
        fig_height = max(4.8, 0.34 * len(labels) + 1.4)
        fig, ax = plt.subplots(figsize=(10.8, fig_height))
        y_pos = list(range(len(labels)))
        ax.barh(y_pos, negative[::-1], color="#c7624f", label="Negative")
        ax.barh(y_pos, positive[::-1], color="#1f7a5b", label="Positive")
        ax.axvline(0, color="#1f2937", linewidth=0.8)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels[::-1])
        ax.set_xlabel("Response share (%)")
        ax.set_title("Likert positive vs negative balance")
        ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.22), ncol=2)
        ax.grid(axis="x", alpha=0.16)
        fig.tight_layout()
        fig.savefig(path, dpi=180)
        plt.close(fig)
        return True
    except Exception:
        return False


def _plot_survey_multi_select_portfolio(path: Path, rows: list[dict[str, Any]]) -> bool:
    if not rows:
        return False
    try:
        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt

        _configure_matplotlib_for_chinese(plt)
        ordered = sorted(rows, key=lambda row: float(row.get("selected_rate") or 0), reverse=True)[:18]
        x_values = [float(row.get("selected_rate") or 0) * 100 for row in ordered]
        y_values = [float(row.get("mean_lift_vs_independent") or 0) for row in ordered]
        sizes = [max(float(row.get("co_pair_count") or 1), 1) * 22 for row in ordered]
        labels = [str(row.get("option_short") or "") for row in ordered]
        fig, ax = plt.subplots(figsize=(10.5, 6.4))
        ax.scatter(x_values, y_values, s=sizes, color="#1f6f8b", alpha=0.72, edgecolor="#0f2a44", linewidth=0.7)
        if x_values:
            ax.axvline(sum(x_values) / len(x_values), color="#64748b", linestyle="--", linewidth=0.9)
        ax.axhline(1.0, color="#64748b", linestyle="--", linewidth=0.9)
        for label, x_value, y_value in zip(labels, x_values, y_values):
            ax.text(x_value + 0.6, y_value + 0.015, label, fontsize=8)
        ax.set_xlabel("Selection rate (%)")
        ax.set_ylabel("Mean co-selection lift")
        ax.set_title("Multi-select option portfolio")
        ax.grid(alpha=0.18)
        fig.tight_layout()
        fig.savefig(path, dpi=180)
        plt.close(fig)
        return True
    except Exception:
        return False


def _plot_survey_segment_multi_select_bubble(path: Path, rows: list[dict[str, Any]]) -> bool:
    if not rows:
        return False
    try:
        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt

        _configure_matplotlib_for_chinese(plt)
        dimensions = list(dict.fromkeys(str(row.get("segment_short") or "") for row in rows if str(row.get("segment_short") or "")))
        if not dimensions:
            return False
        selected_dimension = max(
            dimensions,
            key=lambda dimension: sum(1 for row in rows if str(row.get("segment_short") or "") == dimension),
        )
        selected_rows = [row for row in rows if str(row.get("segment_short") or "") == selected_dimension]
        levels = list(dict.fromkeys(str(row.get("segment_level") or "") for row in selected_rows if str(row.get("segment_level") or "")))[:10]
        options = list(dict.fromkeys(str(row.get("option_short") or "") for row in selected_rows if str(row.get("option_short") or "")))[:14]
        if len(levels) < 2 or len(options) < 2:
            return False
        level_index = {label: offset for offset, label in enumerate(levels)}
        option_index = {label: offset for offset, label in enumerate(options)}
        x_values: list[int] = []
        y_values: list[int] = []
        sizes: list[float] = []
        colors: list[float] = []
        for row in selected_rows:
            level = str(row.get("segment_level") or "")
            option = str(row.get("option_short") or "")
            if level not in level_index or option not in option_index:
                continue
            selected_rate = float(row.get("selected_rate") or 0)
            delta = float(row.get("delta_vs_overall") or 0)
            x_values.append(option_index[option])
            y_values.append(level_index[level])
            sizes.append(max(selected_rate * 900, 18))
            colors.append(delta * 100)
        if not x_values:
            return False
        fig_width = max(9.0, 0.5 * len(options) + 4.0)
        fig_height = max(5.0, 0.44 * len(levels) + 2.4)
        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        max_abs_delta = max(max(abs(value) for value in colors), 1.0)
        scatter = ax.scatter(x_values, y_values, s=sizes, c=colors, cmap="RdBu_r", vmin=-max_abs_delta, vmax=max_abs_delta, alpha=0.76, edgecolor="#1f2937", linewidth=0.5)
        ax.set_xticks(range(len(options)))
        ax.set_yticks(range(len(levels)))
        ax.set_xticklabels(options, rotation=45, ha="right")
        ax.set_yticklabels(levels)
        ax.set_title(f"Segment option bubble: {selected_dimension}")
        ax.set_xlabel("Multi-select option")
        ax.set_ylabel("Segment")
        ax.grid(alpha=0.16)
        cbar = fig.colorbar(scatter, ax=ax, shrink=0.82)
        cbar.set_label("Delta vs overall (pp)")
        fig.tight_layout()
        fig.savefig(path, dpi=180)
        plt.close(fig)
        return True
    except Exception:
        return False


def _plot_survey_segment_likert_bubble(path: Path, rows: list[dict[str, Any]]) -> bool:
    if not rows:
        return False
    try:
        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt

        _configure_matplotlib_for_chinese(plt)
        dimensions = list(dict.fromkeys(str(row.get("segment_short") or "") for row in rows if str(row.get("segment_short") or "")))
        if not dimensions:
            return False
        selected_dimension = max(
            dimensions,
            key=lambda dimension: sum(1 for row in rows if str(row.get("segment_short") or "") == dimension),
        )
        selected_rows = [row for row in rows if str(row.get("segment_short") or "") == selected_dimension]
        levels = list(dict.fromkeys(str(row.get("segment_level") or "") for row in selected_rows if str(row.get("segment_level") or "")))[:10]
        items = list(dict.fromkeys(str(row.get("likert_short") or "") for row in selected_rows if str(row.get("likert_short") or "")))[:14]
        if len(levels) < 2 or len(items) < 2:
            return False
        level_index = {label: offset for offset, label in enumerate(levels)}
        item_index = {label: offset for offset, label in enumerate(items)}
        x_values: list[int] = []
        y_values: list[int] = []
        sizes: list[float] = []
        colors: list[float] = []
        for row in selected_rows:
            level = str(row.get("segment_level") or "")
            item = str(row.get("likert_short") or "")
            if level not in level_index or item not in item_index:
                continue
            delta = float(row.get("delta_vs_overall") or 0)
            n_value = float(row.get("n") or 1)
            x_values.append(item_index[item])
            y_values.append(level_index[level])
            sizes.append(max(abs(delta) * 950 + min(n_value, 80) * 2.2, 24))
            colors.append(delta)
        if not x_values:
            return False
        fig_width = max(9.0, 0.5 * len(items) + 4.0)
        fig_height = max(5.0, 0.44 * len(levels) + 2.4)
        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        max_abs_delta = max(max(abs(value) for value in colors), 0.25)
        scatter = ax.scatter(x_values, y_values, s=sizes, c=colors, cmap="RdBu_r", vmin=-max_abs_delta, vmax=max_abs_delta, alpha=0.76, edgecolor="#1f2937", linewidth=0.5)
        ax.set_xticks(range(len(items)))
        ax.set_yticks(range(len(levels)))
        ax.set_xticklabels(items, rotation=45, ha="right")
        ax.set_yticklabels(levels)
        ax.set_title(f"Segment Likert bubble: {selected_dimension}")
        ax.set_xlabel("Likert item")
        ax.set_ylabel("Segment")
        ax.grid(alpha=0.16)
        cbar = fig.colorbar(scatter, ax=ax, shrink=0.82)
        cbar.set_label("Delta vs overall mean")
        fig.tight_layout()
        fig.savefig(path, dpi=180)
        plt.close(fig)
        return True
    except Exception:
        return False


def _generic_chart_label(value: Any, *, limit: int = 28) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[: max(limit - 1, 1)].rstrip() + "…"


R_WORKFLOW_CHART_STYLE_PRESETS: dict[str, dict[str, Any]] = {
    "cn_editorial_ink": {
        "preset": "cn_editorial_ink",
        "primary": "#17191c",
        "secondary": "#214a4f",
        "accent": "#8f2f31",
        "positive": "#2f6b55",
        "negative": "#8f2f31",
        "neutral": "#7b6d61",
        "edge": "#17191c",
        "grid": "#c8c3b8",
        "diverging_cmap": "RdBu_r",
        "sequential_cmap": "GnBu",
        "category_cmap": "Dark2",
        "category_colors": ["#17191c", "#214a4f", "#8f2f31", "#b08a57", "#5f737b", "#7b6d61"],
    },
    "navy_white_premium": {
        "preset": "navy_white_premium",
        "primary": "#0f2a44",
        "secondary": "#1f6f8b",
        "accent": "#d8a24a",
        "positive": "#1f7a5b",
        "negative": "#b4532a",
        "neutral": "#64748b",
        "edge": "#1f2937",
        "grid": "#64748b",
        "diverging_cmap": "RdBu_r",
        "sequential_cmap": "Blues",
        "category_cmap": "tab20",
        "category_colors": ["#0f2a44", "#1f6f8b", "#d8a24a", "#7aa5c7", "#64748b"],
    },
    "navy_gold_boardroom": {
        "preset": "navy_gold_boardroom",
        "primary": "#052b5f",
        "secondary": "#0f4c81",
        "accent": "#f2c14e",
        "positive": "#2a9d8f",
        "negative": "#c2410c",
        "neutral": "#64748b",
        "edge": "#0b1220",
        "grid": "#94a3b8",
        "diverging_cmap": "RdBu_r",
        "sequential_cmap": "Blues",
        "category_cmap": "tab20",
        "category_colors": ["#052b5f", "#0f4c81", "#f2c14e", "#2a9d8f", "#c2410c", "#94a3b8"],
    },
    "ink_blue_slate": {
        "preset": "ink_blue_slate",
        "primary": "#111827",
        "secondary": "#1d4ed8",
        "accent": "#38bdf8",
        "positive": "#0f766e",
        "negative": "#be123c",
        "neutral": "#64748b",
        "edge": "#020617",
        "grid": "#94a3b8",
        "diverging_cmap": "coolwarm",
        "sequential_cmap": "PuBu",
        "category_cmap": "tab20",
        "category_colors": ["#111827", "#1d4ed8", "#38bdf8", "#0f766e", "#be123c", "#64748b"],
    },
    "black_white_editorial": {
        "preset": "black_white_editorial",
        "primary": "#111827",
        "secondary": "#4b5563",
        "accent": "#9ca3af",
        "positive": "#374151",
        "negative": "#6b7280",
        "neutral": "#71717a",
        "edge": "#111827",
        "grid": "#9ca3af",
        "diverging_cmap": "Greys",
        "sequential_cmap": "Greys",
        "category_cmap": "Greys",
        "category_colors": ["#111827", "#374151", "#6b7280", "#9ca3af", "#d1d5db"],
    },
    "emerald_business": {
        "preset": "emerald_business",
        "primary": "#064e3b",
        "secondary": "#0f766e",
        "accent": "#a3e635",
        "positive": "#15803d",
        "negative": "#b91c1c",
        "neutral": "#64748b",
        "edge": "#052e2b",
        "grid": "#94a3b8",
        "diverging_cmap": "BrBG",
        "sequential_cmap": "YlGnBu",
        "category_cmap": "viridis",
        "category_colors": ["#064e3b", "#0f766e", "#14b8a6", "#a3e635", "#f59e0b", "#64748b"],
    },
    "emerald_teal_growth": {
        "preset": "emerald_teal_growth",
        "primary": "#064e3b",
        "secondary": "#0f766e",
        "accent": "#5eead4",
        "positive": "#16a34a",
        "negative": "#dc2626",
        "neutral": "#64748b",
        "edge": "#052e2b",
        "grid": "#99f6e4",
        "diverging_cmap": "BrBG",
        "sequential_cmap": "YlGnBu",
        "category_cmap": "viridis",
        "category_colors": ["#064e3b", "#0f766e", "#14b8a6", "#5eead4", "#84cc16", "#64748b"],
    },
    "amber_editorial": {
        "preset": "amber_editorial",
        "primary": "#7c2d12",
        "secondary": "#c2410c",
        "accent": "#f59e0b",
        "positive": "#166534",
        "negative": "#b91c1c",
        "neutral": "#78716c",
        "edge": "#292524",
        "grid": "#a8a29e",
        "diverging_cmap": "PuOr_r",
        "sequential_cmap": "YlOrBr",
        "category_cmap": "tab20c",
        "category_colors": ["#7c2d12", "#c2410c", "#f59e0b", "#facc15", "#166534", "#78716c"],
    },
    "amber_copper_retail": {
        "preset": "amber_copper_retail",
        "primary": "#7c2d12",
        "secondary": "#b45309",
        "accent": "#f59e0b",
        "positive": "#15803d",
        "negative": "#b91c1c",
        "neutral": "#78716c",
        "edge": "#292524",
        "grid": "#d6d3d1",
        "diverging_cmap": "PuOr_r",
        "sequential_cmap": "YlOrBr",
        "category_cmap": "tab20c",
        "category_colors": ["#7c2d12", "#b45309", "#f59e0b", "#facc15", "#15803d", "#78716c"],
    },
    "burgundy_luxury": {
        "preset": "burgundy_luxury",
        "primary": "#4c0519",
        "secondary": "#9f1239",
        "accent": "#d4af37",
        "positive": "#166534",
        "negative": "#9f1239",
        "neutral": "#64748b",
        "edge": "#1f2937",
        "grid": "#94a3b8",
        "diverging_cmap": "Spectral",
        "sequential_cmap": "Reds",
        "category_cmap": "tab20b",
        "category_colors": ["#4c0519", "#9f1239", "#d4af37", "#f8e7a2", "#166534", "#64748b"],
    },
    "cobalt_cyan_saas": {
        "preset": "cobalt_cyan_saas",
        "primary": "#1e3a8a",
        "secondary": "#2563eb",
        "accent": "#06b6d4",
        "positive": "#10b981",
        "negative": "#f97316",
        "neutral": "#64748b",
        "edge": "#172554",
        "grid": "#bfdbfe",
        "diverging_cmap": "RdYlBu",
        "sequential_cmap": "winter",
        "category_cmap": "tab20",
        "category_colors": ["#1e3a8a", "#2563eb", "#06b6d4", "#10b981", "#f97316", "#64748b"],
    },
    "graphite_mint_finance": {
        "preset": "graphite_mint_finance",
        "primary": "#1f2937",
        "secondary": "#475569",
        "accent": "#2dd4bf",
        "positive": "#059669",
        "negative": "#e11d48",
        "neutral": "#94a3b8",
        "edge": "#020617",
        "grid": "#cbd5e1",
        "diverging_cmap": "PiYG",
        "sequential_cmap": "GnBu",
        "category_cmap": "Dark2",
        "category_colors": ["#1f2937", "#475569", "#2dd4bf", "#059669", "#e11d48", "#94a3b8"],
    },
    "terracotta_sand_consumer": {
        "preset": "terracotta_sand_consumer",
        "primary": "#7c2d12",
        "secondary": "#c65d3b",
        "accent": "#f4d35e",
        "positive": "#2a9d8f",
        "negative": "#bc4749",
        "neutral": "#9a8c7a",
        "edge": "#292524",
        "grid": "#e7d8c9",
        "diverging_cmap": "Spectral",
        "sequential_cmap": "YlOrBr",
        "category_cmap": "tab20c",
        "category_colors": ["#7c2d12", "#c65d3b", "#f4d35e", "#2a9d8f", "#bc4749", "#9a8c7a"],
    },
    "indigo_rose_media": {
        "preset": "indigo_rose_media",
        "primary": "#312e81",
        "secondary": "#4f46e5",
        "accent": "#f472b6",
        "positive": "#22c55e",
        "negative": "#fb7185",
        "neutral": "#64748b",
        "edge": "#1e1b4b",
        "grid": "#c7d2fe",
        "diverging_cmap": "coolwarm",
        "sequential_cmap": "Purples",
        "category_cmap": "tab20",
        "category_colors": ["#312e81", "#4f46e5", "#f472b6", "#22c55e", "#fb7185", "#64748b"],
    },
    "forest_lime_ops": {
        "preset": "forest_lime_ops",
        "primary": "#14532d",
        "secondary": "#166534",
        "accent": "#84cc16",
        "positive": "#22c55e",
        "negative": "#ea580c",
        "neutral": "#64748b",
        "edge": "#052e16",
        "grid": "#bbf7d0",
        "diverging_cmap": "BrBG",
        "sequential_cmap": "Greens",
        "category_cmap": "viridis",
        "category_colors": ["#14532d", "#166534", "#84cc16", "#22c55e", "#ea580c", "#64748b"],
    },
    "steel_violet_product": {
        "preset": "steel_violet_product",
        "primary": "#334155",
        "secondary": "#7c3aed",
        "accent": "#a78bfa",
        "positive": "#14b8a6",
        "negative": "#f43f5e",
        "neutral": "#94a3b8",
        "edge": "#0f172a",
        "grid": "#cbd5e1",
        "diverging_cmap": "PRGn",
        "sequential_cmap": "BuPu",
        "category_cmap": "tab20",
        "category_colors": ["#334155", "#7c3aed", "#a78bfa", "#14b8a6", "#f43f5e", "#94a3b8"],
    },
}


def _copy_chart_style(name: str) -> dict[str, Any]:
    return dict(R_WORKFLOW_CHART_STYLE_PRESETS.get(name) or R_WORKFLOW_CHART_STYLE_PRESETS["cn_editorial_ink"])


def _normalize_hex_color(value: str) -> str:
    text = str(value or "").strip()
    match = re.fullmatch(r"#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})", text)
    if not match:
        return ""
    body = match.group(1)
    if len(body) == 3:
        body = "".join(char * 2 for char in body)
    return f"#{body.lower()}"


def _request_style_value(request: SmartReportRequest | dict[str, Any] | None, key: str) -> Any:
    if request is None:
        return ""
    if isinstance(request, dict):
        return request.get(key, "")
    return getattr(request, key, "")


def _coerce_hex_color_list(value: Any) -> list[str]:
    if isinstance(value, dict):
        raw_items = list(value.values())
    elif isinstance(value, (list, tuple, set)):
        raw_items = list(value)
    else:
        raw_items = re.findall(r"#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?", str(value or ""))
    colors: list[str] = []
    for item in raw_items:
        normalized = _normalize_hex_color(str(item))
        if normalized and normalized not in colors:
            colors.append(normalized)
    return colors


def _resolve_r_workflow_chart_style(request: SmartReportRequest | dict[str, Any] | None) -> dict[str, Any]:
    """Resolve deterministic chart colors from frontend visual input and intent output."""

    design_spec = build_report_design_spec(request=request)
    preset = str(
        _request_style_value(request, "chart_palette_preset")
        or design_spec.get("chart_palette_preset")
        or _request_style_value(request, "premium_style_preset")
        or ""
    ).strip()
    visual_text = " ".join(
        str(_request_style_value(request, key) or "")
        for key in [
            "visual_style_text",
            "user_requirement",
            "problem_to_solve",
            "core_purpose",
            "expected_result",
            "key_constraints",
        ]
    ).strip()
    lowered = visual_text.lower()
    if "中文" in visual_text or "内参" in visual_text or "cn_editorial" in lowered or "finance editorial" in lowered:
        style = _copy_chart_style("cn_editorial_ink")
    elif "黑白" in visual_text or "black_white" in lowered or "editorial" in lowered or "monochrome" in lowered:
        style = _copy_chart_style("black_white_editorial")
    elif "绿色" in visual_text or "绿" in visual_text or "emerald" in lowered or "teal" in lowered:
        style = _copy_chart_style("emerald_business")
    elif "橙" in visual_text or "amber" in lowered or "orange" in lowered:
        style = _copy_chart_style("amber_editorial")
    elif "酒红" in visual_text or "红金" in visual_text or "burgundy" in lowered or "maroon" in lowered:
        style = _copy_chart_style("burgundy_luxury")
    elif preset in R_WORKFLOW_CHART_STYLE_PRESETS:
        style = _copy_chart_style(preset)
    else:
        style = _copy_chart_style("cn_editorial_ink")

    palette_hex_colors = _coerce_hex_color_list(design_spec.get("chart_palette_colors") or _request_style_value(request, "chart_palette_colors"))
    if preset in R_WORKFLOW_CHART_STYLE_PRESETS:
        style = _copy_chart_style(preset)
    hex_colors = palette_hex_colors or _coerce_hex_color_list(visual_text)
    if hex_colors:
        style["primary"] = hex_colors[0]
    if len(hex_colors) == 2:
        style["secondary"] = hex_colors[0]
        style["accent"] = hex_colors[1]
    elif len(hex_colors) > 2:
        for key, color in zip(["secondary", "accent", "positive", "negative"], hex_colors[1:5]):
            style[key] = color
    if hex_colors:
        style["category_colors"] = hex_colors[:12]
    style["source_preset"] = preset or style.get("preset", "cn_editorial_ink")
    style["source_visual_text"] = visual_text[:800]
    style["hex_override_count"] = len(hex_colors)
    return style


def _chart_style_value(chart_style: dict[str, Any] | None, key: str, fallback: str) -> str:
    value = str((chart_style or {}).get(key) or "").strip()
    if key.endswith("cmap"):
        return value or fallback
    return _normalize_hex_color(value) or fallback


def _chart_style_palette(chart_style: dict[str, Any] | None) -> list[str]:
    return _coerce_hex_color_list((chart_style or {}).get("category_colors"))


def _write_chart_visual_style_artifacts(workflow_dir: Path, chart_style: dict[str, Any]) -> None:
    safe_style = {str(key): value for key, value in chart_style.items()}
    _write_text(
        workflow_dir / "chart_visual_style.json",
        json.dumps(safe_style, ensure_ascii=False, indent=2, default=str),
    )
    _write_csv_artifact(
        workflow_dir / "chart_visual_style.csv",
        [
            {
                "field": str(key),
                "value": json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else str(value),
            }
            for key, value in safe_style.items()
        ],
        ["field", "value"],
    )


def _plot_generic_missingness_bar(path: Path, rows: list[dict[str, Any]], chart_style: dict[str, Any] | None = None) -> bool:
    rows = [row for row in rows if float(row.get("missing_rate") or 0) > 0]
    if not rows:
        return False
    try:
        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt

        _configure_matplotlib_for_chinese(plt)
        accent = _chart_style_value(chart_style, "accent", "#8f5f2a")
        ordered = sorted(rows, key=lambda row: float(row.get("missing_rate") or 0), reverse=True)[:18]
        labels = [_generic_chart_label(row.get("column")) for row in ordered]
        values = [float(row.get("missing_rate") or 0) * 100 for row in ordered]
        fig_height = max(4.8, 0.34 * len(labels) + 1.2)
        fig, ax = plt.subplots(figsize=(10.8, fig_height))
        ax.barh(labels[::-1], values[::-1], color=accent)
        ax.set_xlim(0, max(100, max(values) * 1.1))
        ax.set_xlabel("Missing rate (%)")
        ax.set_title("Missingness profile")
        for index, value in enumerate(values[::-1]):
            ax.text(value + 1, index, f"{value:.1f}%", va="center", fontsize=9)
        ax.grid(axis="x", alpha=0.18)
        fig.tight_layout()
        fig.savefig(path, dpi=180)
        plt.close(fig)
        return True
    except Exception:
        return False


def _plot_generic_correlation_bubble(path: Path, rows: list[dict[str, Any]], chart_style: dict[str, Any] | None = None) -> bool:
    if not rows:
        return False
    try:
        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt

        _configure_matplotlib_for_chinese(plt)
        diverging_cmap = _chart_style_value(chart_style, "diverging_cmap", "RdBu_r")
        edge = _chart_style_value(chart_style, "edge", "#1f2937")
        neutral = _chart_style_value(chart_style, "neutral", "#64748b")
        ordered = sorted(rows, key=lambda row: float(row.get("abs_correlation") or 0), reverse=True)[:18]
        labels = [
            f"{_generic_chart_label(row.get('left'), limit=16)} × {_generic_chart_label(row.get('right'), limit=16)}"
            for row in ordered
        ]
        y_values = list(range(len(ordered)))
        x_values = [float(row.get("correlation") or 0) for row in ordered]
        sizes = [max(float(row.get("abs_correlation") or 0) * 900, 28) for row in ordered]
        colors = x_values
        fig_height = max(5.2, 0.38 * len(labels) + 1.8)
        fig, ax = plt.subplots(figsize=(10.8, fig_height))
        scatter = ax.scatter(
            x_values,
            y_values,
            s=sizes,
            c=colors,
            cmap=diverging_cmap,
            vmin=-1,
            vmax=1,
            alpha=0.78,
            edgecolor=edge,
            linewidth=0.5,
        )
        ax.axvline(0, color=neutral, linewidth=0.8)
        ax.set_yticks(y_values)
        ax.set_yticklabels(labels)
        ax.set_xlim(-1.05, 1.05)
        ax.set_xlabel("Pearson correlation")
        ax.set_title("Top numeric relationships")
        ax.grid(axis="x", alpha=0.18)
        cbar = fig.colorbar(scatter, ax=ax, shrink=0.78)
        cbar.set_label("Correlation")
        fig.tight_layout()
        fig.savefig(path, dpi=180)
        plt.close(fig)
        return True
    except Exception:
        return False


def _plot_generic_category_metric_heatmap(path: Path, rows: list[dict[str, Any]], chart_style: dict[str, Any] | None = None) -> bool:
    if not rows:
        return False
    try:
        import numpy as np
        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt

        _configure_matplotlib_for_chinese(plt)
        diverging_cmap = _chart_style_value(chart_style, "diverging_cmap", "RdBu_r")
        category_columns = list(dict.fromkeys(str(row.get("category_column") or "") for row in rows))
        if not category_columns:
            return False
        selected_category = max(
            category_columns,
            key=lambda category: sum(1 for row in rows if str(row.get("category_column") or "") == category),
        )
        selected_rows = [row for row in rows if str(row.get("category_column") or "") == selected_category]
        levels = list(dict.fromkeys(str(row.get("category_level") or "") for row in selected_rows if str(row.get("category_level") or "")))[:12]
        metrics = list(dict.fromkeys(str(row.get("metric") or "") for row in selected_rows if str(row.get("metric") or "")))[:10]
        if len(levels) < 2 or len(metrics) < 1:
            return False
        matrix = np.full((len(levels), len(metrics)), np.nan, dtype=float)
        level_index = {label: offset for offset, label in enumerate(levels)}
        metric_index = {label: offset for offset, label in enumerate(metrics)}
        for row in selected_rows:
            level = str(row.get("category_level") or "")
            metric = str(row.get("metric") or "")
            if level in level_index and metric in metric_index:
                matrix[level_index[level], metric_index[metric]] = float(row.get("lift_vs_overall") or 0) * 100
        finite_values = matrix[np.isfinite(matrix)]
        max_abs = max(float(np.max(np.abs(finite_values))), 1.0) if finite_values.size else 1.0
        fig_width = max(9.0, 0.48 * len(metrics) + 4.0)
        fig_height = max(5.0, 0.42 * len(levels) + 2.2)
        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        im = ax.imshow(matrix, cmap=diverging_cmap, vmin=-max_abs, vmax=max_abs)
        ax.set_xticks(range(len(metrics)))
        ax.set_yticks(range(len(levels)))
        ax.set_xticklabels([_generic_chart_label(metric, limit=16) for metric in metrics], rotation=45, ha="right")
        ax.set_yticklabels([_generic_chart_label(level, limit=22) for level in levels])
        ax.set_title(f"Category metric lift: {_generic_chart_label(selected_category, limit=36)}")
        for row_index in range(len(levels)):
            for col_index in range(len(metrics)):
                value = matrix[row_index, col_index]
                if np.isfinite(value):
                    ax.text(col_index, row_index, f"{value:+.0f}", ha="center", va="center", fontsize=7)
        cbar = fig.colorbar(im, ax=ax, shrink=0.82)
        cbar.set_label("Lift vs overall (%)")
        fig.tight_layout()
        fig.savefig(path, dpi=180)
        plt.close(fig)
        return True
    except Exception:
        return False


def _plot_generic_outlier_influence_bubble(path: Path, rows: list[dict[str, Any]], chart_style: dict[str, Any] | None = None) -> bool:
    if not rows:
        return False
    try:
        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt

        _configure_matplotlib_for_chinese(plt)
        negative = _chart_style_value(chart_style, "negative", "#b4532a")
        edge = _chart_style_value(chart_style, "edge", "#1f2937")
        neutral = _chart_style_value(chart_style, "neutral", "#64748b")
        ordered = sorted(
            rows,
            key=lambda row: (float(row.get("iqr_outlier_rate") or 0), float(row.get("mean_relative_shift") or 0)),
            reverse=True,
        )[:24]
        x_values = [float(row.get("iqr_outlier_rate") or 0) * 100 for row in ordered]
        y_values = [float(row.get("mean_relative_shift") or 0) * 100 for row in ordered]
        sizes = [max(float(row.get("n") or 1) ** 0.5 * 20, 32) for row in ordered]
        labels = [_generic_chart_label(row.get("column"), limit=18) for row in ordered]
        fig, ax = plt.subplots(figsize=(10.8, 6.4))
        ax.scatter(x_values, y_values, s=sizes, color=negative, alpha=0.68, edgecolor=edge, linewidth=0.5)
        ax.axhline(10, color=neutral, linestyle="--", linewidth=0.9)
        for label, x_value, y_value in zip(labels, x_values, y_values):
            if x_value >= 1 or y_value >= 2:
                ax.text(x_value + 0.2, y_value + 0.2, label, fontsize=8)
        ax.set_xlabel("IQR outlier rate (%)")
        ax.set_ylabel("Mean shift after removing outliers (%)")
        ax.set_title("Outlier influence bubble")
        ax.grid(alpha=0.18)
        fig.tight_layout()
        fig.savefig(path, dpi=180)
        plt.close(fig)
        return True
    except Exception:
        return False


def _plot_generic_time_trend_grid(path: Path, rows: list[dict[str, Any]], chart_style: dict[str, Any] | None = None) -> bool:
    if not rows:
        return False
    try:
        import math
        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt

        _configure_matplotlib_for_chinese(plt)
        secondary = _chart_style_value(chart_style, "secondary", "#1f6f8b")
        neutral = _chart_style_value(chart_style, "neutral", "#64748b")
        metrics = list(dict.fromkeys(str(row.get("metric") or "") for row in rows if str(row.get("metric") or "")))[:6]
        if not metrics:
            return False
        cols = 2 if len(metrics) > 1 else 1
        rows_count = int(math.ceil(len(metrics) / cols))
        fig, axes = plt.subplots(rows_count, cols, figsize=(11.5, max(3.2 * rows_count, 4.2)), squeeze=False)
        for index, metric in enumerate(metrics):
            ax = axes[index // cols][index % cols]
            metric_rows = [row for row in rows if str(row.get("metric") or "") == metric]
            metric_rows = sorted(metric_rows, key=lambda row: str(row.get("period") or ""))
            x_values = list(range(len(metric_rows)))
            y_values = [float(row.get("indexed_value") or 0) for row in metric_rows]
            labels = [str(row.get("period") or "") for row in metric_rows]
            ax.plot(x_values, y_values, color=secondary, linewidth=1.8, marker="o", markersize=3)
            ax.axhline(100, color=neutral, linestyle="--", linewidth=0.8)
            ax.set_title(_generic_chart_label(metric, limit=34))
            ax.set_ylabel("Index = 100 at start")
            if len(labels) <= 8:
                ax.set_xticks(x_values)
                ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
            else:
                step = max(int(len(labels) / 6), 1)
                ticks = x_values[::step]
                ax.set_xticks(ticks)
                ax.set_xticklabels([labels[tick] for tick in ticks], rotation=45, ha="right", fontsize=8)
            ax.grid(alpha=0.18)
        for empty_index in range(len(metrics), rows_count * cols):
            axes[empty_index // cols][empty_index % cols].axis("off")
        fig.tight_layout()
        fig.savefig(path, dpi=180)
        plt.close(fig)
        return True
    except Exception:
        return False


def _plot_generic_numeric_distribution_grid(path: Path, rows: list[dict[str, Any]], chart_style: dict[str, Any] | None = None) -> bool:
    if not rows:
        return False
    try:
        import math
        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt

        _configure_matplotlib_for_chinese(plt)
        primary = _chart_style_value(chart_style, "primary", "#315c8c")
        metrics = list(dict.fromkeys(str(row.get("metric") or "") for row in rows if str(row.get("metric") or "")))[:6]
        if not metrics:
            return False
        cols = 2 if len(metrics) > 1 else 1
        rows_count = int(math.ceil(len(metrics) / cols))
        fig, axes = plt.subplots(rows_count, cols, figsize=(11.5, max(3.1 * rows_count, 4.2)), squeeze=False)
        for index, metric in enumerate(metrics):
            ax = axes[index // cols][index % cols]
            metric_rows = [
                row
                for row in rows
                if str(row.get("metric") or "") == metric
            ]
            metric_rows = sorted(metric_rows, key=lambda row: float(row.get("bin_left") or 0))
            centers = [
                (float(row.get("bin_left") or 0) + float(row.get("bin_right") or 0)) / 2
                for row in metric_rows
            ]
            counts = [float(row.get("count") or 0) for row in metric_rows]
            widths = [
                max(float(row.get("bin_right") or 0) - float(row.get("bin_left") or 0), 1e-9)
                for row in metric_rows
            ]
            ax.bar(centers, counts, width=widths, color=primary, alpha=0.82, align="center")
            ax.set_title(_generic_chart_label(metric, limit=34))
            ax.set_ylabel("Count")
            ax.grid(axis="y", alpha=0.18)
        for empty_index in range(len(metrics), rows_count * cols):
            axes[empty_index // cols][empty_index % cols].axis("off")
        fig.tight_layout()
        fig.savefig(path, dpi=180)
        plt.close(fig)
        return True
    except Exception:
        return False


def _plot_generic_cumulative_contribution_curve(path: Path, rows: list[dict[str, Any]], chart_style: dict[str, Any] | None = None) -> bool:
    if not rows:
        return False
    try:
        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt

        _configure_matplotlib_for_chinese(plt)
        secondary = _chart_style_value(chart_style, "secondary", "#1f6f8b")
        accent = _chart_style_value(chart_style, "accent", "#b4532a")
        ordered = sorted(rows, key=lambda row: int(float(row.get("rank") or 0)))
        if len(ordered) < 2:
            return False
        ranks = [int(float(row.get("rank") or 0)) for row in ordered]
        cumulative = [float(row.get("cumulative_share") or 0) * 100 for row in ordered]
        labels = [_generic_chart_label(row.get("category_level"), limit=16) for row in ordered]
        fig, ax = plt.subplots(figsize=(10.8, 5.8))
        ax.plot(ranks, cumulative, color=secondary, linewidth=2.0, marker="o", markersize=4)
        ax.axhline(80, color=accent, linestyle="--", linewidth=1.0)
        ax.set_ylim(0, 105)
        ax.set_xlabel("Ranked category levels")
        ax.set_ylabel("Cumulative contribution (%)")
        title_category = ordered[0].get("category_column", "")
        title_metric = ordered[0].get("metric", "")
        ax.set_title(f"Cumulative contribution: {_generic_chart_label(title_category, limit=24)} / {_generic_chart_label(title_metric, limit=24)}")
        tick_step = max(int(len(ranks) / 8), 1)
        shown_ticks = ranks[::tick_step]
        ax.set_xticks(shown_ticks)
        ax.set_xticklabels([labels[index - 1] for index in shown_ticks if 0 <= index - 1 < len(labels)], rotation=45, ha="right")
        ax.grid(alpha=0.18)
        fig.tight_layout()
        fig.savefig(path, dpi=180)
        plt.close(fig)
        return True
    except Exception:
        return False


def _plot_generic_segment_bubble(path: Path, rows: list[dict[str, Any]], chart_style: dict[str, Any] | None = None) -> bool:
    if not rows:
        return False
    try:
        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt

        _configure_matplotlib_for_chinese(plt)
        diverging_cmap = _chart_style_value(chart_style, "diverging_cmap", "RdBu_r")
        edge = _chart_style_value(chart_style, "edge", "#1f2937")
        neutral = _chart_style_value(chart_style, "neutral", "#64748b")
        ordered = sorted(rows, key=lambda row: abs(float(row.get("lift_vs_overall") or 0)), reverse=True)[:24]
        if not ordered:
            return False
        x_values = [float(row.get("category_share") or 0) * 100 for row in ordered]
        y_values = [float(row.get("lift_vs_overall") or 0) * 100 for row in ordered]
        sizes = [max(float(row.get("n") or 1) ** 0.5 * 24, 32) for row in ordered]
        labels = [_generic_chart_label(row.get("category_level"), limit=18) for row in ordered]
        fig, ax = plt.subplots(figsize=(10.8, 6.3))
        scatter = ax.scatter(
            x_values,
            y_values,
            s=sizes,
            c=y_values,
            cmap=diverging_cmap,
            alpha=0.72,
            edgecolor=edge,
            linewidth=0.5,
        )
        ax.axhline(0, color=neutral, linestyle="--", linewidth=0.9)
        for label, x_value, y_value in zip(labels, x_values, y_values):
            if abs(y_value) >= 5 or x_value >= 10:
                ax.text(x_value + 0.25, y_value + 0.25, label, fontsize=8)
        ax.set_xlabel("Segment share (%)")
        ax.set_ylabel("Metric lift vs overall (%)")
        title_category = ordered[0].get("category_column", "")
        title_metric = ordered[0].get("metric", "")
        ax.set_title(f"Segment bubble: {_generic_chart_label(title_category, limit=24)} / {_generic_chart_label(title_metric, limit=24)}")
        ax.grid(alpha=0.18)
        cbar = fig.colorbar(scatter, ax=ax, shrink=0.82)
        cbar.set_label("Lift vs overall (%)")
        fig.tight_layout()
        fig.savefig(path, dpi=180)
        plt.close(fig)
        return True
    except Exception:
        return False


def _plot_generic_top_bottom_performer(path: Path, rows: list[dict[str, Any]], chart_style: dict[str, Any] | None = None) -> bool:
    if not rows:
        return False
    try:
        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt

        _configure_matplotlib_for_chinese(plt)
        positive = _chart_style_value(chart_style, "positive", "#b4532a")
        negative = _chart_style_value(chart_style, "negative", "#2f6f9f")
        edge = _chart_style_value(chart_style, "edge", "#1f2937")
        ordered = sorted(rows, key=lambda row: float(row.get("lift_vs_overall") or 0))
        labels = [_generic_chart_label(row.get("category_level"), limit=26) for row in ordered]
        values = [float(row.get("lift_vs_overall") or 0) * 100 for row in ordered]
        colors = [negative if value < 0 else positive for value in values]
        fig_height = max(5.0, 0.36 * len(labels) + 1.4)
        fig, ax = plt.subplots(figsize=(10.8, fig_height))
        y_pos = list(range(len(labels)))
        ax.barh(y_pos, values, color=colors, alpha=0.86)
        ax.axvline(0, color=edge, linewidth=0.8)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels)
        title_category = ordered[0].get("category_column", "")
        title_metric = ordered[0].get("metric", "")
        ax.set_title(f"Top / bottom performers: {_generic_chart_label(title_category, limit=24)} / {_generic_chart_label(title_metric, limit=24)}")
        ax.set_xlabel("Lift vs overall (%)")
        ax.grid(axis="x", alpha=0.18)
        for index, value in enumerate(values):
            ax.text(value + (0.5 if value >= 0 else -0.5), index, f"{value:+.1f}%", va="center", ha="left" if value >= 0 else "right", fontsize=8)
        fig.tight_layout()
        fig.savefig(path, dpi=180)
        plt.close(fig)
        return True
    except Exception:
        return False


def _plot_generic_key_metric_scatter_bubble(path: Path, rows: list[dict[str, Any]], chart_style: dict[str, Any] | None = None) -> bool:
    if not rows:
        return False
    try:
        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt

        _configure_matplotlib_for_chinese(plt)
        category_cmap = _chart_style_value(chart_style, "category_cmap", "tab20")
        category_palette = _chart_style_palette(chart_style)
        edge = _chart_style_value(chart_style, "edge", "#1f2937")
        neutral = _chart_style_value(chart_style, "neutral", "#475569")
        x_values = [float(row.get("x_value") or 0) for row in rows]
        y_values = [float(row.get("y_value") or 0) for row in rows]
        raw_sizes = [max(float(row.get("size_value") or 1), 0.0) for row in rows]
        min_size = min(raw_sizes) if raw_sizes else 0.0
        max_size = max(raw_sizes) if raw_sizes else 0.0
        if max_size > min_size:
            sizes = [42 + (value - min_size) / (max_size - min_size) * 720 for value in raw_sizes]
        else:
            sizes = [140 for _value in raw_sizes]
        categories = [str(row.get("category_level") or "") for row in rows]
        category_order = list(dict.fromkeys(categories))[:12]
        color_map = {category: index for index, category in enumerate(category_order)}
        colors = [color_map.get(category, 0) for category in categories]
        point_colors = [
            category_palette[color_map.get(category, 0) % len(category_palette)]
            for category in categories
        ] if category_palette else []
        fig, ax = plt.subplots(figsize=(10.6, 6.5))
        if point_colors:
            scatter = ax.scatter(
                x_values,
                y_values,
                s=sizes,
                c=point_colors,
                alpha=0.56,
                edgecolor=edge,
                linewidth=0.4,
            )
        else:
            scatter = ax.scatter(
                x_values,
                y_values,
                s=sizes,
                c=colors,
                cmap=category_cmap,
                alpha=0.56,
                edgecolor=edge,
                linewidth=0.4,
            )
        x_metric = rows[0].get("x_metric", "x")
        y_metric = rows[0].get("y_metric", "y")
        size_metric = rows[0].get("size_metric", "size")
        ax.set_xlabel(str(x_metric))
        ax.set_ylabel(str(y_metric))
        ax.set_title(f"Key metric scatter bubble: {_generic_chart_label(x_metric, limit=22)} × {_generic_chart_label(y_metric, limit=22)}")
        ax.grid(alpha=0.18)
        if category_order and any(category_order):
            handles = []
            for category in category_order[:8]:
                marker_color = (
                    category_palette[color_map[category] % len(category_palette)]
                    if category_palette
                    else scatter.cmap(scatter.norm(color_map[category]))
                )
                handles.append(
                    plt.Line2D([0], [0], marker="o", color="w", label=_generic_chart_label(category, limit=16), markerfacecolor=marker_color, markersize=7)
                )
            ax.legend(handles=handles, title="Category", loc="best", fontsize=8)
        ax.text(0.99, 0.02, f"Bubble size: {_generic_chart_label(size_metric, limit=24)}", transform=ax.transAxes, ha="right", va="bottom", fontsize=8, color=neutral)
        fig.tight_layout()
        fig.savefig(path, dpi=180)
        plt.close(fig)
        return True
    except Exception:
        return False


def _write_generic_visualization_artifacts(
    *,
    workflow_dir: Path,
    frame: pd.DataFrame,
    column_role_registry: dict[str, Any],
    request: SmartReportRequest | dict[str, Any] | None = None,
) -> None:
    """Add richer generic business visuals only when data is not questionnaire-like."""

    if bool(_detect_questionnaire_columns(frame).get("is_questionnaire")):
        return

    chart_style = _resolve_r_workflow_chart_style(request)
    _write_chart_visual_style_artifacts(workflow_dir, chart_style)
    method_rows: list[dict[str, Any]] = []
    method_rows.append(
        {
            "method": "chart_visual_style",
            "output": "chart_visual_style.json",
            "status": True,
            "note": f"completed:{chart_style.get('preset') or chart_style.get('source_preset')}",
        }
    )
    temporal_columns = _dedupe_ordered(
        list(column_role_registry.get("temporal_columns") or []) + _infer_r_temporal_columns(frame)
    )
    temporal_column_set = set(temporal_columns)
    numeric_columns = [
        column
        for column in _r_workflow_numeric_columns(frame, column_role_registry, limit=18)
        if column not in temporal_column_set
        and not pd.api.types.is_datetime64_any_dtype(frame[column])
        and not _is_id_like_column(column)
    ][:14]
    categorical_columns = _r_workflow_categorical_columns(frame, column_role_registry, limit=8)

    try:
        row_count = int(len(frame))
        missing_rows: list[dict[str, Any]] = []
        for column in frame.columns.astype(str).tolist():
            series = frame[column]
            text_series = series.astype("string")
            blank_count = int(text_series.str.strip().isin(["", "nan", "None", "<NA>"]).sum())
            missing_count = int(series.isna().sum() + blank_count)
            missing_rows.append(
                {
                    "column": column,
                    "row_count": row_count,
                    "missing_count": min(missing_count, row_count),
                    "missing_rate": min(missing_count, row_count) / max(row_count, 1),
                }
            )
        missing_plot_ok = _plot_generic_missingness_bar(workflow_dir / "generic_missingness_bar.png", missing_rows, chart_style)
        method_rows.append(
            {
                "method": "generic_missingness_bar_plot",
                "output": "generic_missingness_bar.png",
                "status": missing_plot_ok,
                "note": "completed:missingness bar chart" if missing_plot_ok else "skipped_no_missing_values",
            }
        )

        correlation_rows: list[dict[str, Any]] = []
        for left_index, left_column in enumerate(numeric_columns):
            left_series = _numeric_series_for_inference(frame[left_column])
            for right_column in numeric_columns[left_index + 1 :]:
                right_series = _numeric_series_for_inference(frame[right_column])
                payload = _rw_pearson_payload(left_series, right_series)
                if not payload:
                    continue
                correlation_rows.append(
                    {
                        "left": left_column,
                        "right": right_column,
                        **payload,
                    }
                )
        correlation_rows = _rw_add_bh_q_values(correlation_rows)
        correlation_rows = sorted(correlation_rows, key=lambda row: float(row.get("abs_correlation") or 0), reverse=True)[:60]
        _write_csv_artifact(
            workflow_dir / "generic_correlation_bubble.csv",
            correlation_rows,
            ["left", "right", "n", "pearson_r", "correlation", "abs_correlation", "p_value", "q_value_bh", "significance_label", "ci95_low", "ci95_high"],
        )
        corr_plot_ok = _plot_generic_correlation_bubble(workflow_dir / "generic_correlation_bubble.png", correlation_rows, chart_style)
        method_rows.append(
            {
                "method": "generic_correlation_bubble",
                "output": "generic_correlation_bubble.png",
                "status": corr_plot_ok,
                "note": f"completed:{len(correlation_rows)} correlation pairs" if corr_plot_ok else "skipped_insufficient_numeric_pairs",
            }
        )

        distribution_rows: list[dict[str, Any]] = []
        for metric in numeric_columns[:6]:
            values = _numeric_series_for_inference(frame[metric]).dropna()
            if len(values) < 5 or int(values.nunique()) < 2:
                continue
            bin_count = max(5, min(24, int(len(values) ** 0.5)))
            try:
                bins = pd.cut(values, bins=bin_count, duplicates="drop")
            except Exception:
                continue
            counts = bins.value_counts().sort_index()
            for interval, count in counts.items():
                distribution_rows.append(
                    {
                        "metric": metric,
                        "bin_left": float(interval.left),
                        "bin_right": float(interval.right),
                        "count": int(count),
                    }
                )
        _write_csv_artifact(
            workflow_dir / "generic_numeric_distribution_grid.csv",
            distribution_rows,
            ["metric", "bin_left", "bin_right", "count"],
        )
        distribution_plot_ok = _plot_generic_numeric_distribution_grid(
            workflow_dir / "generic_numeric_distribution_grid.png",
            distribution_rows,
            chart_style,
        )
        method_rows.append(
            {
                "method": "generic_numeric_distribution_grid",
                "output": "generic_numeric_distribution_grid.png",
                "status": distribution_plot_ok,
                "note": f"completed:{len(distribution_rows)} distribution bins" if distribution_plot_ok else "skipped_no_eligible_numeric_distributions",
            }
        )

        category_metric_rows: list[dict[str, Any]] = []
        for category_column in categorical_columns[:4]:
            values = _categorical_series_for_inference(frame[category_column]).dropna()
            level_counts = values.value_counts().head(12)
            if len(level_counts) < 2:
                continue
            for metric in numeric_columns[:10]:
                numeric = _numeric_series_for_inference(frame[metric])
                overall = float(numeric.dropna().mean()) if int(numeric.notna().sum()) else 0.0
                for level, count in level_counts.items():
                    mask = _categorical_series_for_inference(frame[category_column]) == str(level)
                    metric_values = numeric.loc[mask].dropna()
                    if len(metric_values) < 2:
                        continue
                    mean_value = float(metric_values.mean())
                    category_metric_rows.append(
                        {
                            "category_column": category_column,
                            "category_level": str(level),
                            "metric": metric,
                            "n": int(len(metric_values)),
                            "mean": mean_value,
                            "overall_mean": overall,
                            "lift_vs_overall": (mean_value / overall - 1) if overall else 0,
                            "category_share": int(count) / max(len(values), 1),
                        }
                    )
            if category_metric_rows:
                break
        _write_csv_artifact(
            workflow_dir / "generic_category_metric_heatmap.csv",
            category_metric_rows,
            ["category_column", "category_level", "metric", "n", "mean", "overall_mean", "lift_vs_overall", "category_share"],
        )
        cat_heatmap_ok = _plot_generic_category_metric_heatmap(
            workflow_dir / "generic_category_metric_heatmap.png",
            category_metric_rows,
            chart_style,
        )
        method_rows.append(
            {
                "method": "generic_category_metric_heatmap",
                "output": "generic_category_metric_heatmap.png",
                "status": cat_heatmap_ok,
                "note": f"completed:{len(category_metric_rows)} category metric cells" if cat_heatmap_ok else "skipped_no_eligible_category_metric_grid",
            }
        )

        selected_category_column = ""
        selected_metric = ""
        if category_metric_rows:
            metric_scores: dict[str, float] = {}
            for row in category_metric_rows:
                metric = str(row.get("metric") or "")
                metric_scores[metric] = metric_scores.get(metric, 0.0) + abs(float(row.get("lift_vs_overall") or 0))
            selected_metric = max(metric_scores, key=metric_scores.get) if metric_scores else str(category_metric_rows[0].get("metric") or "")
            selected_category_column = str(category_metric_rows[0].get("category_column") or "")

        segment_rows = [
            row
            for row in category_metric_rows
            if str(row.get("category_column") or "") == selected_category_column
            and str(row.get("metric") or "") == selected_metric
        ]
        _write_csv_artifact(
            workflow_dir / "generic_segment_bubble.csv",
            segment_rows,
            ["category_column", "category_level", "metric", "n", "mean", "overall_mean", "lift_vs_overall", "category_share"],
        )
        segment_plot_ok = _plot_generic_segment_bubble(workflow_dir / "generic_segment_bubble.png", segment_rows, chart_style)
        method_rows.append(
            {
                "method": "generic_segment_bubble",
                "output": "generic_segment_bubble.png",
                "status": segment_plot_ok,
                "note": f"completed:{len(segment_rows)} segment bubbles" if segment_plot_ok else "skipped_no_eligible_segment_bubble",
            }
        )

        top_bottom_rows: list[dict[str, Any]] = []
        if segment_rows:
            ordered_segment_rows = sorted(segment_rows, key=lambda row: float(row.get("lift_vs_overall") or 0))
            combined_rows = ordered_segment_rows[:6] + ordered_segment_rows[-6:]
            seen_levels: set[str] = set()
            for row in combined_rows:
                level = str(row.get("category_level") or "")
                key = f"{row.get('category_column')}::{level}::{row.get('metric')}"
                if key in seen_levels:
                    continue
                seen_levels.add(key)
                top_bottom_rows.append(dict(row))
        _write_csv_artifact(
            workflow_dir / "generic_top_bottom_performer.csv",
            top_bottom_rows,
            ["category_column", "category_level", "metric", "n", "mean", "overall_mean", "lift_vs_overall", "category_share"],
        )
        top_bottom_plot_ok = _plot_generic_top_bottom_performer(
            workflow_dir / "generic_top_bottom_performer.png",
            top_bottom_rows,
            chart_style,
        )
        method_rows.append(
            {
                "method": "generic_top_bottom_performer",
                "output": "generic_top_bottom_performer.png",
                "status": top_bottom_plot_ok,
                "note": f"completed:{len(top_bottom_rows)} performer rows" if top_bottom_plot_ok else "skipped_no_eligible_top_bottom_performers",
            }
        )

        contribution_rows: list[dict[str, Any]] = []
        if selected_category_column and selected_metric:
            metric_values = _numeric_series_for_inference(frame[selected_metric])
            categories = _categorical_series_for_inference(frame[selected_category_column])
            grouped = (
                pd.DataFrame({"category": categories, "value": metric_values})
                .dropna()
                .groupby("category", as_index=False)["value"]
                .sum()
                .sort_values("value", ascending=False)
            )
            grouped = grouped[grouped["value"] > 0].head(30)
            total_value = float(grouped["value"].sum()) if len(grouped) else 0.0
            cumulative = 0.0
            if total_value > 0:
                for rank, row in enumerate(grouped.to_dict(orient="records"), start=1):
                    value = float(row.get("value") or 0)
                    contribution = value / total_value
                    cumulative += contribution
                    contribution_rows.append(
                        {
                            "category_column": selected_category_column,
                            "category_level": str(row.get("category") or ""),
                            "metric": selected_metric,
                            "rank": rank,
                            "value": value,
                            "contribution_share": contribution,
                            "cumulative_share": cumulative,
                        }
                    )
        _write_csv_artifact(
            workflow_dir / "generic_cumulative_contribution_curve.csv",
            contribution_rows,
            ["category_column", "category_level", "metric", "rank", "value", "contribution_share", "cumulative_share"],
        )
        contribution_plot_ok = _plot_generic_cumulative_contribution_curve(
            workflow_dir / "generic_cumulative_contribution_curve.png",
            contribution_rows,
            chart_style,
        )
        method_rows.append(
            {
                "method": "generic_cumulative_contribution_curve",
                "output": "generic_cumulative_contribution_curve.png",
                "status": contribution_plot_ok,
                "note": f"completed:{len(contribution_rows)} ranked contribution rows" if contribution_plot_ok else "skipped_no_eligible_contribution_curve",
            }
        )

        scatter_rows: list[dict[str, Any]] = []
        if correlation_rows:
            strongest_pair = correlation_rows[0]
            x_metric = str(strongest_pair.get("left") or "")
            y_metric = str(strongest_pair.get("right") or "")
            size_metric = next((column for column in numeric_columns if column not in {x_metric, y_metric}), "")
            category_column = selected_category_column or (categorical_columns[0] if categorical_columns else "")
            scatter_frame = pd.DataFrame(
                {
                    "x_value": _numeric_series_for_inference(frame[x_metric]) if x_metric in frame.columns else pd.Series(dtype=float),
                    "y_value": _numeric_series_for_inference(frame[y_metric]) if y_metric in frame.columns else pd.Series(dtype=float),
                    "size_value": _numeric_series_for_inference(frame[size_metric]) if size_metric in frame.columns else pd.Series([1] * len(frame)),
                    "category_level": _categorical_series_for_inference(frame[category_column]) if category_column in frame.columns else pd.Series([""] * len(frame)),
                }
            ).dropna(subset=["x_value", "y_value"])
            if len(scatter_frame) > 500:
                scatter_frame = scatter_frame.sample(n=500, random_state=7)
            for row in scatter_frame.to_dict(orient="records"):
                scatter_rows.append(
                    {
                        "x_metric": x_metric,
                        "y_metric": y_metric,
                        "size_metric": size_metric or "row_count",
                        "category_column": category_column,
                        "category_level": str(row.get("category_level") or ""),
                        "x_value": float(row.get("x_value") or 0),
                        "y_value": float(row.get("y_value") or 0),
                        "size_value": float(row.get("size_value") or 1),
                    }
                )
        _write_csv_artifact(
            workflow_dir / "generic_key_metric_scatter_bubble.csv",
            scatter_rows,
            ["x_metric", "y_metric", "size_metric", "category_column", "category_level", "x_value", "y_value", "size_value"],
        )
        scatter_plot_ok = _plot_generic_key_metric_scatter_bubble(
            workflow_dir / "generic_key_metric_scatter_bubble.png",
            scatter_rows,
            chart_style,
        )
        method_rows.append(
            {
                "method": "generic_key_metric_scatter_bubble",
                "output": "generic_key_metric_scatter_bubble.png",
                "status": scatter_plot_ok,
                "note": f"completed:{len(scatter_rows)} scatter rows" if scatter_plot_ok else "skipped_no_eligible_scatter_bubble",
            }
        )

        outlier_rows: list[dict[str, Any]] = []
        outlier_path = workflow_dir / "outlier_influence_summary.csv"
        if outlier_path.exists():
            try:
                outlier_frame = pd.read_csv(outlier_path, encoding="utf-8-sig")
                for row in outlier_frame.to_dict(orient="records"):
                    outlier_rows.append(
                        {
                            "column": row.get("column", ""),
                            "n": row.get("n", 0),
                            "iqr_outlier_rate": row.get("iqr_outlier_rate", 0),
                            "mean_relative_shift": row.get("mean_relative_shift", 0),
                            "influence_flag": row.get("influence_flag", False),
                        }
                    )
            except Exception:
                outlier_rows = []
        _write_csv_artifact(
            workflow_dir / "generic_outlier_influence_bubble.csv",
            outlier_rows,
            ["column", "n", "iqr_outlier_rate", "mean_relative_shift", "influence_flag"],
        )
        outlier_plot_ok = _plot_generic_outlier_influence_bubble(
            workflow_dir / "generic_outlier_influence_bubble.png",
            outlier_rows,
            chart_style,
        )
        method_rows.append(
            {
                "method": "generic_outlier_influence_bubble",
                "output": "generic_outlier_influence_bubble.png",
                "status": outlier_plot_ok,
                "note": f"completed:{len(outlier_rows)} outlier rows" if outlier_plot_ok else "skipped_no_outlier_influence_rows",
            }
        )

        trend_rows: list[dict[str, Any]] = []
        if temporal_columns and numeric_columns:
            time_column = temporal_columns[0]
            parsed_time = pd.to_datetime(frame[time_column], errors="coerce")
            valid_time_count = int(parsed_time.notna().sum())
            if valid_time_count >= 4:
                time_frame = pd.DataFrame({"period": parsed_time})
                if valid_time_count > 45:
                    time_frame["period"] = time_frame["period"].dt.to_period("M").dt.to_timestamp()
                for metric in numeric_columns[:6]:
                    metric_values = _numeric_series_for_inference(frame[metric])
                    grouped = (
                        pd.DataFrame({"period": time_frame["period"], "value": metric_values})
                        .dropna()
                        .groupby("period", as_index=False)["value"]
                        .mean()
                        .sort_values("period")
                    )
                    if len(grouped) < 3:
                        continue
                    base = float(grouped["value"].iloc[0])
                    for _, row in grouped.iterrows():
                        value = float(row["value"])
                        indexed_value = value / base * 100 if base else value
                        trend_rows.append(
                            {
                                "time_column": time_column,
                                "period": pd.Timestamp(row["period"]).strftime("%Y-%m-%d"),
                                "metric": metric,
                                "value": value,
                                "indexed_value": indexed_value,
                            }
                        )
        _write_csv_artifact(
            workflow_dir / "generic_time_trend_grid.csv",
            trend_rows,
            ["time_column", "period", "metric", "value", "indexed_value"],
        )
        trend_plot_ok = _plot_generic_time_trend_grid(workflow_dir / "generic_time_trend_grid.png", trend_rows, chart_style)
        method_rows.append(
            {
                "method": "generic_time_trend_grid",
                "output": "generic_time_trend_grid.png",
                "status": trend_plot_ok,
                "note": f"completed:{len(trend_rows)} trend rows" if trend_plot_ok else "skipped_no_eligible_time_series",
            }
        )
    except Exception as exc:
        method_rows.append(
            {
                "method": "generic_visualization_enhancements",
                "output": "generic_*",
                "status": False,
                "note": f"error:{exc}",
            }
        )
    finally:
        _append_method_log_rows(workflow_dir, method_rows)


def _write_questionnaire_visualization_artifacts(
    *,
    workflow_dir: Path,
    frame: pd.DataFrame,
    column_role_registry: dict[str, Any],
) -> None:
    """Add questionnaire-only readable visuals without changing generic R outputs."""

    _ = column_role_registry
    profile = _detect_questionnaire_columns(frame)
    if not bool(profile.get("is_questionnaire")):
        return

    labels: dict[str, str] = dict(profile.get("short_labels") or {})
    binary_options: list[str] = list(profile.get("binary_options") or [])
    likert_items: list[str] = list(profile.get("likert_items") or [])
    categorical_dimensions: list[str] = list(profile.get("categorical_dimensions") or [])
    method_rows: list[dict[str, Any]] = []

    try:
        field_rows: list[dict[str, Any]] = []
        for role, columns in [
            ("multi_select_option", binary_options),
            ("likert_item", likert_items),
            ("categorical_dimension", categorical_dimensions),
        ]:
            for column in columns:
                series = frame[column] if column in frame.columns else pd.Series(dtype=object)
                usable = int(series.notna().sum())
                unique_values = int(series.dropna().nunique())
                field_rows.append(
                    {
                        "short_label": labels.get(column, column),
                        "full_column": column,
                        "survey_role": role,
                        "usable_n": usable,
                        "unique_values": unique_values,
                    }
                )
        _write_csv_artifact(
            workflow_dir / "survey_field_map.csv",
            field_rows,
            ["short_label", "full_column", "survey_role", "usable_n", "unique_values"],
        )
        method_rows.append(
            {
                "method": "survey_field_map",
                "output": "survey_field_map.csv",
                "status": True,
                "note": f"completed:{len(field_rows)} questionnaire fields mapped",
            }
        )

        multi_rows: list[dict[str, Any]] = []
        for column in binary_options:
            series = pd.to_numeric(frame[column], errors="coerce")
            base_n = int(series.notna().sum())
            selected_count = int((series == 1).sum())
            multi_rows.append(
                {
                    "short_label": labels.get(column, column),
                    "full_column": column,
                    "base_n": base_n,
                    "selected_count": selected_count,
                    "selected_rate": selected_count / base_n if base_n else 0,
                }
            )
        _write_csv_artifact(
            workflow_dir / "survey_multi_select_rates.csv",
            multi_rows,
            ["short_label", "full_column", "base_n", "selected_count", "selected_rate"],
        )
        multi_plot_ok = _plot_survey_multi_select_rates(workflow_dir / "survey_multi_select_rates.png", multi_rows)
        method_rows.extend(
            [
                {
                    "method": "survey_multi_select_rates",
                    "output": "survey_multi_select_rates.csv",
                    "status": bool(multi_rows),
                    "note": f"completed:{len(multi_rows)} multi-select options" if multi_rows else "skipped_no_multi_select_options",
                },
                {
                    "method": "survey_multi_select_rates_plot",
                    "output": "survey_multi_select_rates.png",
                    "status": multi_plot_ok,
                    "note": "completed:readable questionnaire multi-select chart" if multi_plot_ok else "skipped_plot_unavailable",
                },
            ]
        )

        likert_rows: list[dict[str, Any]] = []
        distribution_rows: list[dict[str, Any]] = []
        for column in likert_items:
            series = pd.to_numeric(frame[column], errors="coerce").dropna()
            if series.empty:
                continue
            scale_max = int(series.max()) if int(series.max()) <= 7 else 5
            n = int(len(series))
            mean = float(series.mean())
            sd = float(series.std(ddof=1)) if n > 1 else 0.0
            ci_margin = 1.96 * sd / (n ** 0.5) if n > 1 else 0.0
            likert_rows.append(
                {
                    "short_label": labels.get(column, column),
                    "full_column": column,
                    "n": n,
                    "scale_min": int(series.min()),
                    "scale_max": scale_max,
                    "mean": mean,
                    "median": float(series.median()),
                    "sd": sd,
                    "ci_low": mean - ci_margin,
                    "ci_high": mean + ci_margin,
                    "positive_rate": float((series >= max(scale_max - 1, 4)).mean()),
                    "neutral_rate": float((series == 3).mean()) if scale_max == 5 else float((series == round((scale_max + 1) / 2)).mean()),
                    "negative_rate": float((series <= 2).mean()),
                }
            )
            counts = series.round().astype(int).value_counts().sort_index()
            for response_value in range(1, scale_max + 1):
                count = int(counts.get(response_value, 0))
                distribution_rows.append(
                    {
                        "short_label": labels.get(column, column),
                        "full_column": column,
                        "response_value": response_value,
                        "count": count,
                        "rate": count / n if n else 0,
                    }
                )
        _write_csv_artifact(
            workflow_dir / "survey_likert_summary.csv",
            likert_rows,
            [
                "short_label",
                "full_column",
                "n",
                "scale_min",
                "scale_max",
                "mean",
                "median",
                "sd",
                "ci_low",
                "ci_high",
                "positive_rate",
                "neutral_rate",
                "negative_rate",
            ],
        )
        _write_csv_artifact(
            workflow_dir / "survey_likert_distribution.csv",
            distribution_rows,
            ["short_label", "full_column", "response_value", "count", "rate"],
        )
        mean_plot_ok = _plot_survey_likert_mean_ci(workflow_dir / "survey_likert_mean_ci.png", likert_rows)
        dist_plot_ok = _plot_survey_likert_distribution(workflow_dir / "survey_likert_distribution.png", distribution_rows)

        cooccurrence_rows: list[dict[str, Any]] = []
        co_columns = binary_options[:20]
        for left_index in range(len(co_columns)):
            left_column = co_columns[left_index]
            left_series = pd.to_numeric(frame[left_column], errors="coerce")
            for right_column in co_columns[left_index + 1 :]:
                right_series = pd.to_numeric(frame[right_column], errors="coerce")
                valid = left_series.notna() & right_series.notna()
                base_n = int(valid.sum())
                if base_n < 10:
                    continue
                left_rate = float((left_series[valid] == 1).mean())
                right_rate = float((right_series[valid] == 1).mean())
                co_selected_rate = float(((left_series[valid] == 1) & (right_series[valid] == 1)).mean())
                expected_rate = left_rate * right_rate
                cooccurrence_rows.append(
                    {
                        "option_a_short": labels.get(left_column, left_column),
                        "option_b_short": labels.get(right_column, right_column),
                        "option_a": left_column,
                        "option_b": right_column,
                        "base_n": base_n,
                        "option_a_rate": left_rate,
                        "option_b_rate": right_rate,
                        "co_selected_rate": co_selected_rate,
                        "lift_vs_independent": co_selected_rate / expected_rate if expected_rate > 0 else "",
                    }
                )
        _write_csv_artifact(
            workflow_dir / "survey_multi_select_cooccurrence.csv",
            cooccurrence_rows,
            [
                "option_a_short",
                "option_b_short",
                "option_a",
                "option_b",
                "base_n",
                "option_a_rate",
                "option_b_rate",
                "co_selected_rate",
                "lift_vs_independent",
            ],
        )
        cooccurrence_plot_ok = _plot_survey_multi_select_cooccurrence(
            workflow_dir / "survey_multi_select_cooccurrence.png",
            cooccurrence_rows,
        )

        portfolio_rows: list[dict[str, Any]] = []
        co_by_option: dict[str, list[dict[str, Any]]] = {}
        for row in cooccurrence_rows:
            co_by_option.setdefault(str(row.get("option_a_short") or ""), []).append(row)
            co_by_option.setdefault(str(row.get("option_b_short") or ""), []).append(row)
        for row in multi_rows:
            option_short = str(row.get("short_label") or "")
            pairs = co_by_option.get(option_short, [])
            lift_values = [
                float(pair.get("lift_vs_independent"))
                for pair in pairs
                if str(pair.get("lift_vs_independent") or "").strip()
            ]
            co_values = [float(pair.get("co_selected_rate") or 0) for pair in pairs]
            portfolio_rows.append(
                {
                    "option_short": option_short,
                    "option": row.get("full_column", ""),
                    "selected_rate": row.get("selected_rate", 0),
                    "selected_count": row.get("selected_count", 0),
                    "base_n": row.get("base_n", 0),
                    "co_pair_count": len(pairs),
                    "mean_co_selected_rate": sum(co_values) / len(co_values) if co_values else "",
                    "mean_lift_vs_independent": sum(lift_values) / len(lift_values) if lift_values else "",
                }
            )
        _write_csv_artifact(
            workflow_dir / "survey_multi_select_portfolio.csv",
            portfolio_rows,
            [
                "option_short",
                "option",
                "selected_rate",
                "selected_count",
                "base_n",
                "co_pair_count",
                "mean_co_selected_rate",
                "mean_lift_vs_independent",
            ],
        )
        portfolio_plot_ok = _plot_survey_multi_select_portfolio(
            workflow_dir / "survey_multi_select_portfolio.png",
            portfolio_rows,
        )

        likert_correlation_rows: list[dict[str, Any]] = []
        corr_columns = likert_items[:20]
        for left_index in range(len(corr_columns)):
            left_column = corr_columns[left_index]
            left_series = pd.to_numeric(frame[left_column], errors="coerce")
            for right_column in corr_columns[left_index + 1 :]:
                right_series = pd.to_numeric(frame[right_column], errors="coerce")
                pair = pd.DataFrame({"left": left_series, "right": right_series}).dropna()
                if len(pair) < 10 or int(pair["left"].nunique()) < 2 or int(pair["right"].nunique()) < 2:
                    continue
                corr_value = pair["left"].corr(pair["right"], method="spearman")
                if pd.isna(corr_value):
                    continue
                likert_correlation_rows.append(
                    {
                        "item_a_short": labels.get(left_column, left_column),
                        "item_b_short": labels.get(right_column, right_column),
                        "item_a": left_column,
                        "item_b": right_column,
                        "n": int(len(pair)),
                        "spearman_corr": float(corr_value),
                        "abs_correlation": abs(float(corr_value)),
                    }
                )
        _write_csv_artifact(
            workflow_dir / "survey_likert_correlation.csv",
            likert_correlation_rows,
            ["item_a_short", "item_b_short", "item_a", "item_b", "n", "spearman_corr", "abs_correlation"],
        )
        likert_corr_plot_ok = _plot_survey_likert_correlation_heatmap(
            workflow_dir / "survey_likert_correlation_heatmap.png",
            likert_correlation_rows,
        )

        sentiment_rows: list[dict[str, Any]] = []
        for row in likert_rows:
            positive_rate = float(row.get("positive_rate") or 0)
            neutral_rate = float(row.get("neutral_rate") or 0)
            negative_rate = float(row.get("negative_rate") or 0)
            sentiment_rows.append(
                {
                    "short_label": row.get("short_label", ""),
                    "full_column": row.get("full_column", ""),
                    "n": row.get("n", 0),
                    "positive_rate": positive_rate,
                    "neutral_rate": neutral_rate,
                    "negative_rate": negative_rate,
                    "net_positive_rate": positive_rate - negative_rate,
                    "polarization_rate": positive_rate + negative_rate,
                }
            )
        _write_csv_artifact(
            workflow_dir / "survey_likert_sentiment_balance.csv",
            sentiment_rows,
            [
                "short_label",
                "full_column",
                "n",
                "positive_rate",
                "neutral_rate",
                "negative_rate",
                "net_positive_rate",
                "polarization_rate",
            ],
        )
        sentiment_plot_ok = _plot_survey_likert_sentiment_balance(
            workflow_dir / "survey_likert_sentiment_balance.png",
            sentiment_rows,
        )

        segment_distribution_rows: list[dict[str, Any]] = []
        for dimension in categorical_dimensions[:6]:
            if dimension not in frame.columns:
                continue
            values = _categorical_series_for_inference(frame[dimension]).astype("string").dropna()
            total = int(len(values))
            if total <= 0:
                continue
            for level, count in values.value_counts().head(12).items():
                segment_distribution_rows.append(
                    {
                        "segment_short": labels.get(dimension, dimension),
                        "segment_column": dimension,
                        "segment_level": str(level),
                        "count": int(count),
                        "rate": int(count) / total,
                        "base_n": total,
                    }
                )
        _write_csv_artifact(
            workflow_dir / "survey_segment_distribution.csv",
            segment_distribution_rows,
            ["segment_short", "segment_column", "segment_level", "count", "rate", "base_n"],
        )
        segment_distribution_plot_ok = _plot_survey_segment_distribution(
            workflow_dir / "survey_segment_distribution.png",
            segment_distribution_rows,
        )

        segment_multi_select_rows: list[dict[str, Any]] = []
        for dimension in categorical_dimensions[:3]:
            if dimension not in frame.columns:
                continue
            dimension_series = _categorical_series_for_inference(frame[dimension]).astype("string")
            level_counts = dimension_series.dropna().value_counts().head(10)
            for level, level_n in level_counts.items():
                if int(level_n) < 5:
                    continue
                mask = dimension_series == str(level)
                for column in binary_options[:16]:
                    values = pd.to_numeric(frame.loc[mask, column], errors="coerce").dropna()
                    if len(values) < 5:
                        continue
                    selected_count = int((values == 1).sum())
                    segment_multi_select_rows.append(
                        {
                            "segment_short": labels.get(dimension, dimension),
                            "segment_column": dimension,
                            "segment_level": str(level),
                            "option_short": labels.get(column, column),
                            "option": column,
                            "base_n": int(len(values)),
                            "selected_count": selected_count,
                            "selected_rate": selected_count / len(values) if len(values) else 0,
                        }
                    )
        _write_csv_artifact(
            workflow_dir / "survey_segment_multi_select_rates.csv",
            segment_multi_select_rows,
            [
                "segment_short",
                "segment_column",
                "segment_level",
                "option_short",
                "option",
                "base_n",
                "selected_count",
                "selected_rate",
            ],
        )
        segment_multi_select_plot_ok = _plot_survey_segment_multi_select_heatmap(
            workflow_dir / "survey_segment_multi_select_heatmap.png",
            segment_multi_select_rows,
        )
        overall_option_rates = {
            str(row.get("short_label") or ""): float(row.get("selected_rate") or 0)
            for row in multi_rows
        }
        segment_multi_select_bubble_rows: list[dict[str, Any]] = []
        for row in segment_multi_select_rows:
            option_short = str(row.get("option_short") or "")
            selected_rate = float(row.get("selected_rate") or 0)
            overall_rate = overall_option_rates.get(option_short, 0.0)
            segment_multi_select_bubble_rows.append(
                {
                    "segment_short": row.get("segment_short", ""),
                    "segment_column": row.get("segment_column", ""),
                    "segment_level": row.get("segment_level", ""),
                    "option_short": option_short,
                    "option": row.get("option", ""),
                    "base_n": row.get("base_n", 0),
                    "selected_rate": selected_rate,
                    "overall_selected_rate": overall_rate,
                    "delta_vs_overall": selected_rate - overall_rate,
                }
            )
        _write_csv_artifact(
            workflow_dir / "survey_segment_multi_select_bubble.csv",
            segment_multi_select_bubble_rows,
            [
                "segment_short",
                "segment_column",
                "segment_level",
                "option_short",
                "option",
                "base_n",
                "selected_rate",
                "overall_selected_rate",
                "delta_vs_overall",
            ],
        )
        segment_multi_select_bubble_ok = _plot_survey_segment_multi_select_bubble(
            workflow_dir / "survey_segment_multi_select_bubble.png",
            segment_multi_select_bubble_rows,
        )

        segment_likert_rows: list[dict[str, Any]] = []
        for dimension in categorical_dimensions[:3]:
            if dimension not in frame.columns:
                continue
            dimension_series = _categorical_series_for_inference(frame[dimension]).astype("string")
            level_counts = dimension_series.dropna().value_counts().head(10)
            for level, level_n in level_counts.items():
                if int(level_n) < 5:
                    continue
                mask = dimension_series == str(level)
                for column in likert_items[:16]:
                    values = pd.to_numeric(frame.loc[mask, column], errors="coerce").dropna()
                    if len(values) < 3:
                        continue
                    segment_likert_rows.append(
                        {
                            "segment_short": labels.get(dimension, dimension),
                            "segment_column": dimension,
                            "segment_level": str(level),
                            "likert_short": labels.get(column, column),
                            "likert_item": column,
                            "n": int(len(values)),
                            "mean": float(values.mean()),
                            "median": float(values.median()),
                        }
                    )
        _write_csv_artifact(
            workflow_dir / "survey_segment_likert_means.csv",
            segment_likert_rows,
            ["segment_short", "segment_column", "segment_level", "likert_short", "likert_item", "n", "mean", "median"],
        )
        segment_heatmap_ok = _plot_survey_segment_likert_heatmap(
            workflow_dir / "survey_segment_likert_heatmap.png",
            segment_likert_rows,
        )
        overall_likert_means = {
            str(row.get("short_label") or ""): float(row.get("mean") or 0)
            for row in likert_rows
        }
        segment_likert_bubble_rows: list[dict[str, Any]] = []
        for row in segment_likert_rows:
            likert_short = str(row.get("likert_short") or "")
            mean_value = float(row.get("mean") or 0)
            overall_mean = overall_likert_means.get(likert_short, 0.0)
            segment_likert_bubble_rows.append(
                {
                    "segment_short": row.get("segment_short", ""),
                    "segment_column": row.get("segment_column", ""),
                    "segment_level": row.get("segment_level", ""),
                    "likert_short": likert_short,
                    "likert_item": row.get("likert_item", ""),
                    "n": row.get("n", 0),
                    "mean": mean_value,
                    "overall_mean": overall_mean,
                    "delta_vs_overall": mean_value - overall_mean,
                }
            )
        _write_csv_artifact(
            workflow_dir / "survey_segment_likert_bubble.csv",
            segment_likert_bubble_rows,
            [
                "segment_short",
                "segment_column",
                "segment_level",
                "likert_short",
                "likert_item",
                "n",
                "mean",
                "overall_mean",
                "delta_vs_overall",
            ],
        )
        segment_likert_bubble_ok = _plot_survey_segment_likert_bubble(
            workflow_dir / "survey_segment_likert_bubble.png",
            segment_likert_bubble_rows,
        )
        method_rows.extend(
            [
                {
                    "method": "survey_likert_summary",
                    "output": "survey_likert_summary.csv",
                    "status": bool(likert_rows),
                    "note": f"completed:{len(likert_rows)} Likert items" if likert_rows else "skipped_no_likert_items",
                },
                {
                    "method": "survey_likert_distribution",
                    "output": "survey_likert_distribution.csv",
                    "status": bool(distribution_rows),
                    "note": f"completed:{len(distribution_rows)} response cells" if distribution_rows else "skipped_no_likert_distribution",
                },
                {
                    "method": "survey_likert_mean_ci_plot",
                    "output": "survey_likert_mean_ci.png",
                    "status": mean_plot_ok,
                    "note": "completed:Likert mean CI chart" if mean_plot_ok else "skipped_plot_unavailable",
                },
                {
                    "method": "survey_likert_distribution_plot",
                    "output": "survey_likert_distribution.png",
                    "status": dist_plot_ok,
                    "note": "completed:Likert distribution chart" if dist_plot_ok else "skipped_plot_unavailable",
                },
                {
                    "method": "survey_multi_select_cooccurrence",
                    "output": "survey_multi_select_cooccurrence.csv",
                    "status": bool(cooccurrence_rows),
                    "note": f"completed:{len(cooccurrence_rows)} option pairs" if cooccurrence_rows else "skipped_insufficient_multi_select_pairs",
                },
                {
                    "method": "survey_multi_select_cooccurrence_plot",
                    "output": "survey_multi_select_cooccurrence.png",
                    "status": cooccurrence_plot_ok,
                    "note": "completed:multi-select co-occurrence heatmap" if cooccurrence_plot_ok else "skipped_plot_unavailable",
                },
                {
                    "method": "survey_multi_select_portfolio",
                    "output": "survey_multi_select_portfolio.csv",
                    "status": bool(portfolio_rows),
                    "note": f"completed:{len(portfolio_rows)} multi-select options" if portfolio_rows else "skipped_no_multi_select_options",
                },
                {
                    "method": "survey_multi_select_portfolio_plot",
                    "output": "survey_multi_select_portfolio.png",
                    "status": portfolio_plot_ok,
                    "note": "completed:multi-select portfolio chart" if portfolio_plot_ok else "skipped_plot_unavailable",
                },
                {
                    "method": "survey_likert_correlation",
                    "output": "survey_likert_correlation.csv",
                    "status": bool(likert_correlation_rows),
                    "note": f"completed:{len(likert_correlation_rows)} Likert item pairs" if likert_correlation_rows else "skipped_insufficient_likert_pairs",
                },
                {
                    "method": "survey_likert_correlation_heatmap",
                    "output": "survey_likert_correlation_heatmap.png",
                    "status": likert_corr_plot_ok,
                    "note": "completed:Likert correlation heatmap" if likert_corr_plot_ok else "skipped_plot_unavailable",
                },
                {
                    "method": "survey_likert_sentiment_balance",
                    "output": "survey_likert_sentiment_balance.csv",
                    "status": bool(sentiment_rows),
                    "note": f"completed:{len(sentiment_rows)} Likert sentiment rows" if sentiment_rows else "skipped_no_likert_items",
                },
                {
                    "method": "survey_likert_sentiment_balance_plot",
                    "output": "survey_likert_sentiment_balance.png",
                    "status": sentiment_plot_ok,
                    "note": "completed:Likert sentiment balance chart" if sentiment_plot_ok else "skipped_plot_unavailable",
                },
                {
                    "method": "survey_segment_distribution",
                    "output": "survey_segment_distribution.csv",
                    "status": bool(segment_distribution_rows),
                    "note": f"completed:{len(segment_distribution_rows)} segment levels" if segment_distribution_rows else "skipped_no_eligible_segments",
                },
                {
                    "method": "survey_segment_distribution_plot",
                    "output": "survey_segment_distribution.png",
                    "status": segment_distribution_plot_ok,
                    "note": "completed:segment distribution chart" if segment_distribution_plot_ok else "skipped_plot_unavailable",
                },
                {
                    "method": "survey_segment_multi_select_rates",
                    "output": "survey_segment_multi_select_rates.csv",
                    "status": bool(segment_multi_select_rows),
                    "note": f"completed:{len(segment_multi_select_rows)} segment option rates" if segment_multi_select_rows else "skipped_no_eligible_segment_options",
                },
                {
                    "method": "survey_segment_multi_select_heatmap",
                    "output": "survey_segment_multi_select_heatmap.png",
                    "status": segment_multi_select_plot_ok,
                    "note": "completed:segment multi-select heatmap" if segment_multi_select_plot_ok else "skipped_plot_unavailable",
                },
                {
                    "method": "survey_segment_multi_select_bubble",
                    "output": "survey_segment_multi_select_bubble.csv",
                    "status": bool(segment_multi_select_bubble_rows),
                    "note": f"completed:{len(segment_multi_select_bubble_rows)} segment option bubble cells" if segment_multi_select_bubble_rows else "skipped_no_eligible_segment_options",
                },
                {
                    "method": "survey_segment_multi_select_bubble_plot",
                    "output": "survey_segment_multi_select_bubble.png",
                    "status": segment_multi_select_bubble_ok,
                    "note": "completed:segment multi-select bubble chart" if segment_multi_select_bubble_ok else "skipped_plot_unavailable",
                },
                {
                    "method": "survey_segment_likert_means",
                    "output": "survey_segment_likert_means.csv",
                    "status": bool(segment_likert_rows),
                    "note": f"completed:{len(segment_likert_rows)} segment item means" if segment_likert_rows else "skipped_no_eligible_segments",
                },
                {
                    "method": "survey_segment_likert_heatmap",
                    "output": "survey_segment_likert_heatmap.png",
                    "status": segment_heatmap_ok,
                    "note": "completed:segment Likert heatmap" if segment_heatmap_ok else "skipped_plot_unavailable",
                },
                {
                    "method": "survey_segment_likert_bubble",
                    "output": "survey_segment_likert_bubble.csv",
                    "status": bool(segment_likert_bubble_rows),
                    "note": f"completed:{len(segment_likert_bubble_rows)} segment Likert bubble cells" if segment_likert_bubble_rows else "skipped_no_eligible_segment_likert_items",
                },
                {
                    "method": "survey_segment_likert_bubble_plot",
                    "output": "survey_segment_likert_bubble.png",
                    "status": segment_likert_bubble_ok,
                    "note": "completed:segment Likert bubble chart" if segment_likert_bubble_ok else "skipped_plot_unavailable",
                },
            ]
        )
    except Exception as exc:
        method_rows.append(
            {
                "method": "survey_questionnaire_visualization",
                "output": "survey_*",
                "status": False,
                "note": f"error:{exc}",
            }
        )
    finally:
        _append_method_log_rows(workflow_dir, method_rows)


def _safe_number(value: Any) -> float | str:
    try:
        numeric = float(value)
    except Exception:
        return ""
    if pd.isna(numeric):
        return ""
    return numeric


def _bh_adjust(p_values: list[float]) -> list[float]:
    if not p_values:
        return []
    indexed = sorted(enumerate(p_values), key=lambda item: item[1])
    adjusted = [1.0 for _ in p_values]
    running = 1.0
    total = len(p_values)
    for rank_from_end, (original_index, p_value) in enumerate(reversed(indexed), 1):
        rank = total - rank_from_end + 1
        running = min(running, float(p_value) * total / max(rank, 1))
        adjusted[original_index] = min(running, 1.0)
    return adjusted


def _binary_numeric_values(values: pd.Series) -> bool:
    unique_values = {float(value) for value in values.dropna().unique()}
    return bool(unique_values) and unique_values.issubset({0.0, 1.0})


def _write_generic_statistical_enhancement_artifacts(
    *,
    workflow_dir: Path,
    frame: pd.DataFrame,
    column_role_registry: dict[str, Any],
) -> None:
    """Write generic deterministic statistics with eligibility gates."""
    try:
        import numpy as np
    except Exception as exc:
        _append_method_log_rows(
            workflow_dir,
            [
                {
                    "method": "generic_statistical_enhancements",
                    "output": "generic_statistical_enhancements",
                    "status": False,
                    "note": f"skipped_missing_dependency:numpy:{exc}",
                }
            ],
        )
        return

    try:
        from scipy import stats
    except Exception:
        stats = None

    numeric_columns = _r_workflow_numeric_columns(frame, column_role_registry, limit=24)
    categorical_columns = _r_workflow_categorical_columns(frame, column_role_registry, limit=24)
    method_rows: list[dict[str, Any]] = []

    missing_rows: list[dict[str, Any]] = []
    row_count = int(len(frame))
    for column in frame.columns.astype(str).tolist():
        series = frame[column]
        text_series = series.astype("string")
        blank_count = int(text_series.str.strip().isin(["", "nan", "None", "<NA>"]).sum())
        missing_count = int(series.isna().sum() + blank_count)
        missing_count = min(missing_count, row_count)
        non_null_count = max(row_count - missing_count, 0)
        missing_rows.append(
            {
                "column": column,
                "dtype": str(series.dtype),
                "row_count": row_count,
                "missing_count": missing_count,
                "missing_rate": missing_count / max(row_count, 1),
                "non_null_count": non_null_count,
                "unique_count": int(series.dropna().nunique()),
                "blank_like_count": blank_count,
            }
        )
    _write_csv_artifact(
        workflow_dir / "missingness_diagnostics.csv",
        missing_rows,
        ["column", "dtype", "row_count", "missing_count", "missing_rate", "non_null_count", "unique_count", "blank_like_count"],
    )
    method_rows.append(
        {
            "method": "missingness_diagnostics",
            "output": "missingness_diagnostics.csv",
            "status": True,
            "note": f"completed:{len(missing_rows)} columns profiled",
        }
    )

    low_info_rows: list[dict[str, Any]] = []
    for column in frame.columns.astype(str).tolist():
        series = frame[column]
        non_null = series.dropna()
        unique_count = int(non_null.nunique())
        top_share = 0.0
        if len(non_null):
            top_share = float(non_null.astype(str).value_counts(dropna=True).iloc[0] / len(non_null))
        numeric = _numeric_series_for_inference(series)
        numeric_values = numeric.dropna()
        variance = float(numeric_values.var(ddof=1)) if len(numeric_values) >= 2 else np.nan
        unique_ratio = unique_count / max(len(non_null), 1)
        is_constant = unique_count <= 1
        near_zero_variance = bool(pd.notna(variance) and abs(variance) <= 1e-12)
        high_duplicate_share = top_share >= 0.95 and len(non_null) > 0
        low_info_rows.append(
            {
                "column": column,
                "non_null_count": int(len(non_null)),
                "unique_count": unique_count,
                "unique_ratio": unique_ratio,
                "top_value_share": top_share,
                "numeric_variance": _safe_number(variance),
                "is_constant": bool(is_constant),
                "near_zero_variance": bool(near_zero_variance),
                "high_duplicate_share": bool(high_duplicate_share),
                "low_information_flag": bool(is_constant or near_zero_variance or high_duplicate_share),
            }
        )
    _write_csv_artifact(
        workflow_dir / "low_information_columns.csv",
        low_info_rows,
        [
            "column",
            "non_null_count",
            "unique_count",
            "unique_ratio",
            "top_value_share",
            "numeric_variance",
            "is_constant",
            "near_zero_variance",
            "high_duplicate_share",
            "low_information_flag",
        ],
    )
    method_rows.append(
        {
            "method": "low_information_columns",
            "output": "low_information_columns.csv",
            "status": True,
            "note": f"completed:{len(low_info_rows)} columns profiled",
        }
    )

    outlier_rows: list[dict[str, Any]] = []
    for column in numeric_columns:
        values = _numeric_series_for_inference(frame[column]).dropna()
        if len(values) < 4:
            continue
        q1 = float(values.quantile(0.25))
        q3 = float(values.quantile(0.75))
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        iqr_mask = (values < lower) | (values > upper)
        median = float(values.median())
        mad = float((values - median).abs().median())
        if mad > 0:
            modified_z = 0.6745 * (values - median).abs() / mad
            mad_count = int((modified_z > 3.5).sum())
        else:
            mad_count = 0
        mean_all = float(values.mean())
        trimmed = values.loc[~iqr_mask]
        mean_without_iqr = float(trimmed.mean()) if len(trimmed) else np.nan
        absolute_shift = abs(mean_all - mean_without_iqr) if pd.notna(mean_without_iqr) else np.nan
        relative_shift = absolute_shift / abs(mean_all) if pd.notna(absolute_shift) and mean_all != 0 else np.nan
        outlier_rows.append(
            {
                "column": column,
                "n": int(len(values)),
                "iqr_outlier_count": int(iqr_mask.sum()),
                "iqr_outlier_rate": float(iqr_mask.mean()),
                "mad_outlier_count": mad_count,
                "q1": q1,
                "q3": q3,
                "iqr": iqr,
                "lower_bound": lower,
                "upper_bound": upper,
                "mean": mean_all,
                "mean_without_iqr_outliers": _safe_number(mean_without_iqr),
                "mean_absolute_shift": _safe_number(absolute_shift),
                "mean_relative_shift": _safe_number(relative_shift),
                "influence_flag": bool(pd.notna(relative_shift) and relative_shift >= 0.1),
            }
        )
    _write_csv_artifact(
        workflow_dir / "outlier_influence_summary.csv",
        outlier_rows,
        [
            "column",
            "n",
            "iqr_outlier_count",
            "iqr_outlier_rate",
            "mad_outlier_count",
            "q1",
            "q3",
            "iqr",
            "lower_bound",
            "upper_bound",
            "mean",
            "mean_without_iqr_outliers",
            "mean_absolute_shift",
            "mean_relative_shift",
            "influence_flag",
        ],
    )
    method_rows.append(
        {
            "method": "outlier_influence_summary",
            "output": "outlier_influence_summary.csv",
            "status": bool(outlier_rows),
            "note": f"completed:{len(outlier_rows)} numeric columns" if outlier_rows else "skipped_no_eligible_numeric_columns",
        }
    )

    ci_rows: list[dict[str, Any]] = []
    for column in numeric_columns:
        values = _numeric_series_for_inference(frame[column]).dropna()
        if len(values) >= 2:
            mean_value = float(values.mean())
            sd_value = float(values.std(ddof=1))
            if stats is not None and pd.notna(sd_value):
                t_crit = float(stats.t.ppf(0.975, len(values) - 1))
                margin = t_crit * sd_value / (len(values) ** 0.5)
                ci_low = mean_value - margin
                ci_high = mean_value + margin
            else:
                ci_low = np.nan
                ci_high = np.nan
            ci_rows.append(
                {
                    "column": column,
                    "estimate_type": "mean",
                    "n": int(len(values)),
                    "estimate": mean_value,
                    "ci_low_95": _safe_number(ci_low),
                    "ci_high_95": _safe_number(ci_high),
                    "method": "t_interval" if stats is not None else "skipped_missing_scipy",
                    "status": "computed" if stats is not None else "skipped_missing_dependency",
                }
            )
        if len(values) >= 5 and _binary_numeric_values(values):
            successes = float(values.sum())
            n = float(len(values))
            p_hat = successes / n if n else np.nan
            z = 1.959963984540054
            denominator = 1 + z**2 / n
            centre = p_hat + z**2 / (2 * n)
            margin = z * ((p_hat * (1 - p_hat) + z**2 / (4 * n)) / n) ** 0.5
            ci_rows.append(
                {
                    "column": column,
                    "estimate_type": "binary_proportion",
                    "n": int(n),
                    "estimate": p_hat,
                    "ci_low_95": (centre - margin) / denominator,
                    "ci_high_95": (centre + margin) / denominator,
                    "method": "wilson",
                    "status": "computed",
                }
            )
    _write_csv_artifact(
        workflow_dir / "confidence_intervals.csv",
        ci_rows,
        ["column", "estimate_type", "n", "estimate", "ci_low_95", "ci_high_95", "method", "status"],
    )
    method_rows.append(
        {
            "method": "confidence_intervals",
            "output": "confidence_intervals.csv",
            "status": bool(ci_rows),
            "note": f"completed:{len(ci_rows)} intervals" if ci_rows else "skipped_no_eligible_numeric_or_binary_columns",
        }
    )

    spearman_rows: list[dict[str, Any]] = []
    kendall_rows: list[dict[str, Any]] = []
    if stats is not None and len(numeric_columns) >= 2:
        for left_index, left in enumerate(numeric_columns):
            left_values = _numeric_series_for_inference(frame[left])
            for right in numeric_columns[left_index + 1 :]:
                right_values = _numeric_series_for_inference(frame[right])
                valid = pd.DataFrame({"left": left_values, "right": right_values}).dropna()
                if len(valid) < 10 or valid["left"].nunique() <= 1 or valid["right"].nunique() <= 1:
                    continue
                try:
                    rho, spearman_p = stats.spearmanr(valid["left"], valid["right"])
                    tau, kendall_p = stats.kendalltau(valid["left"], valid["right"])
                except Exception:
                    continue
                spearman_rows.append(
                    {
                        "left": left,
                        "right": right,
                        "n": int(len(valid)),
                        "rho": _safe_number(rho),
                        "p_value": _safe_number(spearman_p),
                        "abs_correlation": abs(float(rho)) if pd.notna(rho) else "",
                        "significant_0_05": bool(pd.notna(spearman_p) and spearman_p < 0.05),
                    }
                )
                kendall_rows.append(
                    {
                        "left": left,
                        "right": right,
                        "n": int(len(valid)),
                        "tau": _safe_number(tau),
                        "p_value": _safe_number(kendall_p),
                        "abs_correlation": abs(float(tau)) if pd.notna(tau) else "",
                        "significant_0_05": bool(pd.notna(kendall_p) and kendall_p < 0.05),
                    }
                )
    spearman_rows = sorted(spearman_rows, key=lambda item: float(item.get("abs_correlation") or 0), reverse=True)
    kendall_rows = sorted(kendall_rows, key=lambda item: float(item.get("abs_correlation") or 0), reverse=True)
    _write_csv_artifact(
        workflow_dir / "spearman_correlation_pairs.csv",
        spearman_rows,
        ["left", "right", "n", "rho", "p_value", "abs_correlation", "significant_0_05"],
    )
    _write_csv_artifact(
        workflow_dir / "kendall_correlation_pairs.csv",
        kendall_rows,
        ["left", "right", "n", "tau", "p_value", "abs_correlation", "significant_0_05"],
    )
    method_rows.extend(
        [
            {
                "method": "spearman_correlation_pairs",
                "output": "spearman_correlation_pairs.csv",
                "status": bool(spearman_rows),
                "note": f"completed:{len(spearman_rows)} pairs" if spearman_rows else ("skipped_missing_dependency:scipy" if stats is None else "skipped_insufficient_numeric_pairs"),
            },
            {
                "method": "kendall_correlation_pairs",
                "output": "kendall_correlation_pairs.csv",
                "status": bool(kendall_rows),
                "note": f"completed:{len(kendall_rows)} pairs" if kendall_rows else ("skipped_missing_dependency:scipy" if stats is None else "skipped_insufficient_numeric_pairs"),
            },
        ]
    )

    normality_rows: list[dict[str, Any]] = []
    for column in numeric_columns:
        values = _numeric_series_for_inference(frame[column]).dropna()
        if len(values) < 8:
            continue
        skewness = float(values.skew())
        kurtosis = float(values.kurt())
        test_name = "skew_kurtosis_only"
        statistic: float | str = ""
        p_value: float | str = ""
        if stats is not None:
            try:
                if len(values) <= 5000:
                    test_name = "shapiro"
                    statistic, p_value = stats.shapiro(values)
                elif len(values) >= 20:
                    test_name = "dagostino_k2"
                    statistic, p_value = stats.normaltest(values)
            except Exception:
                test_name = "skew_kurtosis_only"
                statistic, p_value = "", ""
        normality_rows.append(
            {
                "column": column,
                "n": int(len(values)),
                "mean": float(values.mean()),
                "sd": _safe_number(values.std(ddof=1)),
                "skewness": skewness,
                "kurtosis": kurtosis,
                "normality_test": test_name,
                "statistic": _safe_number(statistic),
                "p_value": _safe_number(p_value),
                "likely_non_normal_0_05": bool(p_value != "" and float(p_value) < 0.05),
            }
        )
    _write_csv_artifact(
        workflow_dir / "normality_diagnostics.csv",
        normality_rows,
        ["column", "n", "mean", "sd", "skewness", "kurtosis", "normality_test", "statistic", "p_value", "likely_non_normal_0_05"],
    )
    method_rows.append(
        {
            "method": "normality_diagnostics",
            "output": "normality_diagnostics.csv",
            "status": bool(normality_rows),
            "note": f"completed:{len(normality_rows)} numeric columns" if normality_rows else "skipped_no_numeric_columns_with_n_ge_8",
        }
    )

    variance_rows: list[dict[str, Any]] = []
    welch_rows: list[dict[str, Any]] = []
    dunn_rows: list[dict[str, Any]] = []
    if stats is not None:
        for group_column in categorical_columns:
            for target_column in numeric_columns:
                if group_column == target_column:
                    continue
                valid, groups = _valid_grouped_numeric_values(
                    frame,
                    group_column=group_column,
                    target_column=target_column,
                    min_group_size=3,
                )
                groups = [group.astype(float) for group in groups if len(group) >= 3]
                group_count = len(groups)
                if group_count < 2 or group_count > 20:
                    continue
                sample_n = int(sum(len(group) for group in groups))
                try:
                    levene_stat, levene_p = stats.levene(*groups, center="mean")
                except Exception:
                    levene_stat, levene_p = np.nan, np.nan
                try:
                    bf_stat, bf_p = stats.levene(*groups, center="median")
                except Exception:
                    bf_stat, bf_p = np.nan, np.nan
                variance_rows.append(
                    {
                        "group_column": group_column,
                        "target_column": target_column,
                        "n": sample_n,
                        "group_count": group_count,
                        "levene_statistic": _safe_number(levene_stat),
                        "levene_p_value": _safe_number(levene_p),
                        "brown_forsythe_statistic": _safe_number(bf_stat),
                        "brown_forsythe_p_value": _safe_number(bf_p),
                        "variance_equal_0_05": bool(pd.notna(bf_p) and bf_p >= 0.05),
                    }
                )

                means = np.array([float(group.mean()) for group in groups], dtype=float)
                variances = np.array([float(group.var(ddof=1)) for group in groups], dtype=float)
                ns = np.array([float(len(group)) for group in groups], dtype=float)
                if np.any(variances <= 0) or np.any(ns <= 1):
                    continue
                weights = ns / variances
                weight_sum = float(weights.sum())
                if weight_sum <= 0:
                    continue
                weighted_mean = float((weights * means).sum() / weight_sum)
                df_between = group_count - 1
                numerator = float((weights * (means - weighted_mean) ** 2).sum() / max(df_between, 1))
                lambda_term = float(
                    sum((1 / (ns[i] - 1)) * (1 - weights[i] / weight_sum) ** 2 for i in range(group_count))
                )
                denominator = 1 + (2 * (group_count - 2) / max(group_count**2 - 1, 1)) * lambda_term
                f_stat = numerator / denominator if denominator > 0 else np.nan
                df_within = (group_count**2 - 1) / (3 * lambda_term) if lambda_term > 0 else np.nan
                p_value = float(stats.f.sf(f_stat, df_between, df_within)) if pd.notna(f_stat) and pd.notna(df_within) else np.nan
                welch_rows.append(
                    {
                        "group_column": group_column,
                        "target_column": target_column,
                        "n": sample_n,
                        "group_count": group_count,
                        "df_between": df_between,
                        "df_within": _safe_number(df_within),
                        "f_statistic": _safe_number(f_stat),
                        "p_value": _safe_number(p_value),
                        "significant_0_05": bool(pd.notna(p_value) and p_value < 0.05),
                    }
                )

                try:
                    h_stat, kruskal_p = stats.kruskal(*groups)
                except Exception:
                    h_stat, kruskal_p = np.nan, np.nan
                if not (pd.notna(kruskal_p) and kruskal_p < 0.05):
                    continue
                grouped_values = []
                for group_name, group_frame in valid.groupby("group", dropna=True):
                    values = group_frame["value"].dropna().astype(float)
                    if len(values) >= 3 and int(values.nunique()) > 1:
                        grouped_values.append((str(group_name), values))
                if len(grouped_values) < 2:
                    continue
                all_values = pd.concat([values for _name, values in grouped_values], ignore_index=True)
                ranks = pd.Series(stats.rankdata(all_values.to_numpy()), index=all_values.index)
                rank_offset = 0
                rank_groups: list[tuple[str, pd.Series]] = []
                for group_name, values in grouped_values:
                    group_ranks = ranks.iloc[rank_offset : rank_offset + len(values)]
                    rank_groups.append((group_name, group_ranks))
                    rank_offset += len(values)
                total_n = len(all_values)
                tie_counts = pd.Series(all_values).value_counts()
                tie_correction = float((tie_counts**3 - tie_counts).sum())
                variance_base = (total_n * (total_n + 1) / 12) - (tie_correction / (12 * max(total_n - 1, 1)))
                pair_rows: list[dict[str, Any]] = []
                for left_index, (left_name, left_ranks) in enumerate(rank_groups):
                    for right_name, right_ranks in rank_groups[left_index + 1 :]:
                        denominator = (variance_base * (1 / len(left_ranks) + 1 / len(right_ranks))) ** 0.5
                        if denominator <= 0:
                            continue
                        z_stat = float((float(left_ranks.mean()) - float(right_ranks.mean())) / denominator)
                        p_pair = float(2 * stats.norm.sf(abs(z_stat)))
                        pair_rows.append(
                            {
                                "group_column": group_column,
                                "target_column": target_column,
                                "group1": left_name,
                                "group2": right_name,
                                "z_statistic": z_stat,
                                "p_value": p_pair,
                            }
                        )
                adjusted = _bh_adjust([float(row["p_value"]) for row in pair_rows])
                for row, p_adjusted in zip(pair_rows, adjusted):
                    row["p_adjust_bh"] = p_adjusted
                    row["reject_0_05"] = bool(p_adjusted < 0.05)
                    dunn_rows.append(row)
    _write_csv_artifact(
        workflow_dir / "variance_homogeneity_tests.csv",
        variance_rows,
        [
            "group_column",
            "target_column",
            "n",
            "group_count",
            "levene_statistic",
            "levene_p_value",
            "brown_forsythe_statistic",
            "brown_forsythe_p_value",
            "variance_equal_0_05",
        ],
    )
    _write_csv_artifact(
        workflow_dir / "welch_anova_results.csv",
        welch_rows,
        ["group_column", "target_column", "n", "group_count", "df_between", "df_within", "f_statistic", "p_value", "significant_0_05"],
    )
    _write_csv_artifact(
        workflow_dir / "dunn_posthoc_results.csv",
        dunn_rows,
        ["group_column", "target_column", "group1", "group2", "z_statistic", "p_value", "p_adjust_bh", "reject_0_05"],
    )
    method_rows.extend(
        [
            {
                "method": "variance_homogeneity_tests",
                "output": "variance_homogeneity_tests.csv",
                "status": bool(variance_rows),
                "note": f"completed:{len(variance_rows)} grouped comparisons" if variance_rows else ("skipped_missing_dependency:scipy" if stats is None else "skipped_no_eligible_grouped_numeric_comparisons"),
            },
            {
                "method": "welch_anova_results",
                "output": "welch_anova_results.csv",
                "status": bool(welch_rows),
                "note": f"completed:{len(welch_rows)} grouped comparisons" if welch_rows else ("skipped_missing_dependency:scipy" if stats is None else "skipped_no_eligible_grouped_numeric_comparisons"),
            },
            {
                "method": "dunn_posthoc_results",
                "output": "dunn_posthoc_results.csv",
                "status": bool(dunn_rows),
                "note": f"completed:{len(dunn_rows)} pairwise comparisons" if dunn_rows else ("skipped_missing_dependency:scipy" if stats is None else "skipped_no_significant_kruskal_pairs"),
            },
        ]
    )

    residual_rows: list[dict[str, Any]] = []
    if stats is not None:
        for left_index, left in enumerate(categorical_columns):
            for right in categorical_columns[left_index + 1 :]:
                valid = pd.DataFrame(
                    {
                        "left": _categorical_series_for_inference(frame[left]),
                        "right": _categorical_series_for_inference(frame[right]),
                    }
                ).dropna()
                if len(valid) < 5:
                    continue
                table = pd.crosstab(valid["left"], valid["right"])
                if table.shape[0] < 2 or table.shape[1] < 2:
                    continue
                try:
                    _chi2, _p_value, _dof, expected = stats.chi2_contingency(table)
                except Exception:
                    continue
                for row_index, left_level in enumerate(table.index.astype(str)):
                    for col_index, right_level in enumerate(table.columns.astype(str)):
                        expected_value = float(expected[row_index][col_index])
                        observed_value = float(table.iloc[row_index, col_index])
                        if expected_value <= 0:
                            continue
                        residual = (observed_value - expected_value) / (expected_value ** 0.5)
                        residual_rows.append(
                            {
                                "left": left,
                                "right": right,
                                "left_level": left_level,
                                "right_level": right_level,
                                "observed": observed_value,
                                "expected": expected_value,
                                "standardized_residual": residual,
                                "residual_signal": (
                                    "overrepresented" if residual >= 2 else
                                    "underrepresented" if residual <= -2 else
                                    "neutral"
                                ),
                            }
                        )
                        if len(residual_rows) >= 10000:
                            break
                    if len(residual_rows) >= 10000:
                        break
                if len(residual_rows) >= 10000:
                    break
            if len(residual_rows) >= 10000:
                break
    _write_csv_artifact(
        workflow_dir / "chi_square_residuals.csv",
        residual_rows,
        ["left", "right", "left_level", "right_level", "observed", "expected", "standardized_residual", "residual_signal"],
    )
    method_rows.append(
        {
            "method": "chi_square_residuals",
            "output": "chi_square_residuals.csv",
            "status": bool(residual_rows),
            "note": f"completed:{len(residual_rows)} residual cells" if residual_rows else ("skipped_missing_dependency:scipy" if stats is None else "skipped_no_valid_chi_square_tables"),
        }
    )

    pvalue_rows: list[dict[str, Any]] = []
    pvalue_sources = [
        ("correlation_pairs_with_pvalues.csv", "pearson_correlation", "p_value"),
        ("spearman_correlation_pairs.csv", "spearman_correlation", "p_value"),
        ("kendall_correlation_pairs.csv", "kendall_correlation", "p_value"),
        ("anova_results.csv", "anova", "p_value"),
        ("kruskal_results.csv", "kruskal", "p_value"),
        ("welch_anova_results.csv", "welch_anova", "p_value"),
        ("chi_square_tests.csv", "chi_square", "p_value"),
        ("dunn_posthoc_results.csv", "dunn_posthoc", "p_value"),
        ("tukey_hsd_results.csv", "tukey_hsd", "p_adj"),
    ]
    for source_file, method, p_column in pvalue_sources:
        path = workflow_dir / source_file
        if not path.exists():
            continue
        try:
            source_frame = pd.read_csv(path)
        except Exception:
            continue
        if p_column not in source_frame.columns:
            continue
        for index, row in source_frame.iterrows():
            raw_p = pd.to_numeric(pd.Series([row.get(p_column)]), errors="coerce").iloc[0]
            if pd.isna(raw_p):
                continue
            comparison_parts = [
                str(row.get(key) or "")
                for key in ("left", "right", "group_column", "target_column", "group1", "group2")
                if str(row.get(key) or "").strip()
            ]
            comparison_id = "|".join(comparison_parts) or f"{method}:{index}"
            pvalue_rows.append(
                {
                    "source_file": source_file,
                    "method": method,
                    "comparison_id": comparison_id,
                    "raw_p_value": float(raw_p),
                }
            )
    adjusted_bh = _bh_adjust([float(row["raw_p_value"]) for row in pvalue_rows])
    total_tests = max(len(pvalue_rows), 1)
    for row, p_bh in zip(pvalue_rows, adjusted_bh):
        bonferroni = min(float(row["raw_p_value"]) * total_tests, 1.0)
        row["p_adjust_bh"] = p_bh
        row["p_adjust_bonferroni"] = bonferroni
        row["reject_bh_0_05"] = bool(p_bh < 0.05)
        row["reject_bonferroni_0_05"] = bool(bonferroni < 0.05)
    _write_csv_artifact(
        workflow_dir / "p_value_adjustment_summary.csv",
        pvalue_rows,
        ["source_file", "method", "comparison_id", "raw_p_value", "p_adjust_bh", "p_adjust_bonferroni", "reject_bh_0_05", "reject_bonferroni_0_05"],
    )
    method_rows.append(
        {
            "method": "p_value_adjustment_summary",
            "output": "p_value_adjustment_summary.csv",
            "status": bool(pvalue_rows),
            "note": f"completed:{len(pvalue_rows)} p-values adjusted" if pvalue_rows else "skipped_no_available_p_values",
        }
    )

    _append_method_log_rows(workflow_dir, method_rows)


def _write_inferential_statistics_artifacts(
    *,
    workflow_dir: Path,
    frame: pd.DataFrame,
    column_role_registry: dict[str, Any],
) -> None:
    """Add deterministic inferential statistics outputs beside R-generated artifacts."""
    try:
        import numpy as np
        from scipy import stats
        from statsmodels.stats.multicomp import pairwise_tukeyhsd
    except Exception as exc:
        _append_method_log_rows(
            workflow_dir,
            [
                {
                    "method": "inferential_statistics",
                    "output": "inferential_statistics",
                    "status": False,
                    "note": f"推断统计依赖不可用：{exc}",
                }
            ],
        )
        return

    numeric_columns = [
        column
        for column in list(column_role_registry.get("numeric_method_columns") or [])
        if column in frame.columns
    ]
    for column in _infer_inference_numeric_columns(frame):
        if column not in numeric_columns:
            numeric_columns.append(column)
    categorical_columns = [
        column
        for column in list(column_role_registry.get("category_dimension_columns") or [])
        if column in frame.columns
    ]
    for column in _infer_inference_categorical_columns(frame):
        if column not in categorical_columns:
            categorical_columns.append(column)

    correlation_rows: list[dict[str, Any]] = []
    for left_index, left in enumerate(numeric_columns):
        left_values = _numeric_series_for_inference(frame[left])
        for right in numeric_columns[left_index + 1 :]:
            right_values = _numeric_series_for_inference(frame[right])
            valid = pd.DataFrame({"left": left_values, "right": right_values}).dropna()
            if len(valid) < 3 or valid["left"].nunique() <= 1 or valid["right"].nunique() <= 1:
                continue
            try:
                corr, p_value = stats.pearsonr(valid["left"], valid["right"])
            except Exception:
                continue
            correlation_rows.append(
                {
                    "left": left,
                    "right": right,
                    "n": int(len(valid)),
                    "correlation": float(corr),
                    "p_value": float(p_value),
                    "abs_correlation": abs(float(corr)),
                    "method": "pearson",
                    "significant_0_05": bool(p_value < 0.05),
                }
            )
    correlation_rows = sorted(correlation_rows, key=lambda item: item["abs_correlation"], reverse=True)
    _write_csv_artifact(
        workflow_dir / "correlation_pairs_with_pvalues.csv",
        correlation_rows,
        ["left", "right", "n", "correlation", "p_value", "abs_correlation", "method", "significant_0_05"],
    )

    anova_rows: list[dict[str, Any]] = []
    eta_rows: list[dict[str, Any]] = []
    kruskal_rows: list[dict[str, Any]] = []
    tukey_rows: list[dict[str, Any]] = []
    for group_column in categorical_columns:
        for target_column in numeric_columns:
            if group_column == target_column:
                continue
            valid, groups = _valid_grouped_numeric_values(
                frame,
                group_column=group_column,
                target_column=target_column,
            )
            if len(groups) < 2:
                continue
            group_sizes = [int(len(values)) for values in groups]
            group_count = len(groups)
            sample_n = int(sum(group_sizes))
            try:
                f_stat, p_value = stats.f_oneway(*groups)
            except Exception:
                f_stat, p_value = np.nan, np.nan
            all_values = valid["value"].dropna()
            grand_mean = float(all_values.mean()) if len(all_values) else np.nan
            ss_between = float(sum(len(values) * (float(values.mean()) - grand_mean) ** 2 for values in groups))
            ss_total = float(((all_values - grand_mean) ** 2).sum()) if len(all_values) else 0.0
            eta_squared = ss_between / ss_total if ss_total > 0 else np.nan
            anova_rows.append(
                {
                    "group_column": group_column,
                    "target_column": target_column,
                    "n": sample_n,
                    "group_count": group_count,
                    "df_between": group_count - 1,
                    "df_within": sample_n - group_count,
                    "f_statistic": float(f_stat) if pd.notna(f_stat) else "",
                    "p_value": float(p_value) if pd.notna(p_value) else "",
                    "eta_squared": float(eta_squared) if pd.notna(eta_squared) else "",
                    "significant_0_05": bool(pd.notna(p_value) and p_value < 0.05),
                    "group_sizes": json.dumps(group_sizes, ensure_ascii=False),
                }
            )
            eta_rows.append(
                {
                    "group_column": group_column,
                    "target_column": target_column,
                    "n": sample_n,
                    "eta_squared": float(eta_squared) if pd.notna(eta_squared) else "",
                    "effect_hint": (
                        "large" if pd.notna(eta_squared) and eta_squared >= 0.14 else
                        "medium" if pd.notna(eta_squared) and eta_squared >= 0.06 else
                        "small" if pd.notna(eta_squared) and eta_squared >= 0.01 else
                        "very_small"
                    ),
                }
            )
            try:
                h_stat, kruskal_p = stats.kruskal(*groups)
            except Exception:
                h_stat, kruskal_p = np.nan, np.nan
            kruskal_rows.append(
                {
                    "group_column": group_column,
                    "target_column": target_column,
                    "n": sample_n,
                    "group_count": group_count,
                    "h_statistic": float(h_stat) if pd.notna(h_stat) else "",
                    "p_value": float(kruskal_p) if pd.notna(kruskal_p) else "",
                    "significant_0_05": bool(pd.notna(kruskal_p) and kruskal_p < 0.05),
                    "group_sizes": json.dumps(group_sizes, ensure_ascii=False),
                }
            )
            if group_count >= 2 and sample_n > group_count and pd.notna(p_value) and p_value < 0.05:
                try:
                    tukey = pairwise_tukeyhsd(
                        endog=valid["value"].astype(float).to_numpy(),
                        groups=valid["group"].astype(str).to_numpy(),
                        alpha=0.05,
                    )
                    data = tukey.summary().data
                    for row in data[1:]:
                        record = dict(zip([str(item) for item in data[0]], row))
                        tukey_rows.append(
                            {
                                "group_column": group_column,
                                "target_column": target_column,
                                "group1": record.get("group1", ""),
                                "group2": record.get("group2", ""),
                                "mean_diff": record.get("meandiff", ""),
                                "p_adj": record.get("p-adj", ""),
                                "lower": record.get("lower", ""),
                                "upper": record.get("upper", ""),
                                "reject_0_05": record.get("reject", ""),
                            }
                        )
                except Exception:
                    continue

    _write_csv_artifact(
        workflow_dir / "anova_results.csv",
        anova_rows,
        ["group_column", "target_column", "n", "group_count", "df_between", "df_within", "f_statistic", "p_value", "eta_squared", "significant_0_05", "group_sizes"],
    )
    _write_csv_artifact(
        workflow_dir / "eta_squared_results.csv",
        eta_rows,
        ["group_column", "target_column", "n", "eta_squared", "effect_hint"],
    )
    _write_csv_artifact(
        workflow_dir / "kruskal_results.csv",
        kruskal_rows,
        ["group_column", "target_column", "n", "group_count", "h_statistic", "p_value", "significant_0_05", "group_sizes"],
    )
    _write_csv_artifact(
        workflow_dir / "tukey_hsd_results.csv",
        tukey_rows,
        ["group_column", "target_column", "group1", "group2", "mean_diff", "p_adj", "lower", "upper", "reject_0_05"],
    )

    chi_rows: list[dict[str, Any]] = []
    cramer_rows: list[dict[str, Any]] = []
    for left_index, left in enumerate(categorical_columns):
        for right in categorical_columns[left_index + 1 :]:
            valid = pd.DataFrame(
                {
                    "left": _categorical_series_for_inference(frame[left]),
                    "right": _categorical_series_for_inference(frame[right]),
                }
            ).dropna()
            if len(valid) < 5:
                continue
            table = pd.crosstab(valid["left"], valid["right"])
            if table.shape[0] < 2 or table.shape[1] < 2:
                continue
            try:
                chi2, p_value, dof, expected = stats.chi2_contingency(table)
            except Exception:
                continue
            denominator = len(valid) * max(min(table.shape[0] - 1, table.shape[1] - 1), 1)
            cramers_v = (float(chi2) / denominator) ** 0.5 if denominator > 0 else np.nan
            expected_min = float(np.min(expected)) if expected.size else np.nan
            row = {
                "left": left,
                "right": right,
                "n": int(len(valid)),
                "left_levels": int(table.shape[0]),
                "right_levels": int(table.shape[1]),
                "chi_square": float(chi2),
                "df": int(dof),
                "p_value": float(p_value),
                "cramers_v": float(cramers_v) if pd.notna(cramers_v) else "",
                "expected_min": expected_min,
                "significant_0_05": bool(p_value < 0.05),
            }
            chi_rows.append(row)
            cramer_rows.append(
                {
                    "left": left,
                    "right": right,
                    "n": int(len(valid)),
                    "cramers_v": row["cramers_v"],
                    "association_hint": (
                        "large" if pd.notna(cramers_v) and cramers_v >= 0.5 else
                        "medium" if pd.notna(cramers_v) and cramers_v >= 0.3 else
                        "small" if pd.notna(cramers_v) and cramers_v >= 0.1 else
                        "very_small"
                    ),
                }
            )
    _write_csv_artifact(
        workflow_dir / "chi_square_tests.csv",
        chi_rows,
        ["left", "right", "n", "left_levels", "right_levels", "chi_square", "df", "p_value", "cramers_v", "expected_min", "significant_0_05"],
    )
    _write_csv_artifact(
        workflow_dir / "cramers_v_results.csv",
        cramer_rows,
        ["left", "right", "n", "cramers_v", "association_hint"],
    )

    likert_columns: list[str] = []
    for column in numeric_columns:
        values = _numeric_series_for_inference(frame[column]).dropna()
        if len(values) < 5:
            continue
        unique_values = set(float(value) for value in values.unique())
        if len(unique_values) >= 3 and unique_values.issubset({1.0, 2.0, 3.0, 4.0, 5.0}):
            likert_columns.append(column)
    alpha_rows: list[dict[str, Any]] = []
    if len(likert_columns) >= 2:
        items = pd.DataFrame({column: _numeric_series_for_inference(frame[column]) for column in likert_columns}).dropna()
        if len(items) >= 5 and items.shape[1] >= 2:
            k = items.shape[1]
            item_variance_sum = float(items.var(axis=0, ddof=1).sum())
            total_variance = float(items.sum(axis=1).var(ddof=1))
            alpha = (k / (k - 1)) * (1 - item_variance_sum / total_variance) if total_variance > 0 else np.nan
            corr_matrix = items.corr()
            upper_values = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)).stack()
            alpha_rows.append(
                {
                    "scale_name": "detected_likert_1_to_5",
                    "item_count": k,
                    "n_complete": int(len(items)),
                    "cronbach_alpha": float(alpha) if pd.notna(alpha) else "",
                    "mean_inter_item_correlation": float(upper_values.mean()) if len(upper_values) else "",
                    "items": json.dumps(likert_columns, ensure_ascii=False),
                    "status": "computed",
                }
            )
    if not alpha_rows:
        alpha_rows.append(
            {
                "scale_name": "detected_likert_1_to_5",
                "item_count": len(likert_columns),
                "n_complete": 0,
                "cronbach_alpha": "",
                "mean_inter_item_correlation": "",
                "items": json.dumps(likert_columns, ensure_ascii=False),
                "status": "skipped: fewer than two usable Likert-style numeric items",
            }
        )
    _write_csv_artifact(
        workflow_dir / "cronbach_alpha.csv",
        alpha_rows,
        ["scale_name", "item_count", "n_complete", "cronbach_alpha", "mean_inter_item_correlation", "items", "status"],
    )

    _append_method_log_rows(
        workflow_dir,
        [
            {"method": "correlation_pairs_with_pvalues", "output": "correlation_pairs_with_pvalues.csv", "status": bool(correlation_rows), "note": f"已生成 {len(correlation_rows)} 组相关系数 p 值。"},
            {"method": "anova_results", "output": "anova_results.csv", "status": bool(anova_rows), "note": f"已生成 {len(anova_rows)} 组 ANOVA 检验。"},
            {"method": "eta_squared_results", "output": "eta_squared_results.csv", "status": bool(eta_rows), "note": f"已生成 {len(eta_rows)} 组 eta² 效应量。"},
            {"method": "kruskal_results", "output": "kruskal_results.csv", "status": bool(kruskal_rows), "note": f"已生成 {len(kruskal_rows)} 组 Kruskal-Wallis 检验。"},
            {"method": "tukey_hsd_results", "output": "tukey_hsd_results.csv", "status": bool(tukey_rows), "note": f"已生成 {len(tukey_rows)} 组 Tukey HSD 事后比较。"},
            {"method": "chi_square_tests", "output": "chi_square_tests.csv", "status": bool(chi_rows), "note": f"已生成 {len(chi_rows)} 组卡方检验。"},
            {"method": "cramers_v_results", "output": "cramers_v_results.csv", "status": bool(cramer_rows), "note": f"已生成 {len(cramer_rows)} 组 Cramer's V。"},
            {"method": "cronbach_alpha", "output": "cronbach_alpha.csv", "status": alpha_rows[0].get("status") == "computed", "note": "已自动识别 Likert 题项并计算 Cronbach's alpha。"},
        ],
    )


def _patch_r_csv_encoding(script: str) -> str:
    """Keep generated R scripts from mojibaking UTF-8 Chinese headers on Windows."""
    patched = str(script or "")
    replacements = {
        'read.csv(input_path, check.names = FALSE, stringsAsFactors = FALSE)': (
            'read.csv(input_path, check.names = FALSE, stringsAsFactors = FALSE, fileEncoding = "UTF-8-BOM")'
        ),
        'read.csv(file.path(workflow_dir, "cleaned_dataset.csv"), check.names = FALSE, stringsAsFactors = FALSE)': (
            'read.csv(file.path(workflow_dir, "cleaned_dataset.csv"), check.names = FALSE, stringsAsFactors = FALSE, fileEncoding = "UTF-8")'
        ),
        'write.csv(df, file.path(workflow_dir, "cleaned_dataset.csv"), row.names = FALSE, na = "")': (
            'write.csv(df, file.path(workflow_dir, "cleaned_dataset.csv"), row.names = FALSE, na = "", fileEncoding = "UTF-8")'
        ),
    }
    for source, target in replacements.items():
        patched = patched.replace(source, target)
    return patched


def _infer_r_temporal_columns(frame: pd.DataFrame) -> list[str]:
    columns = frame.columns.astype(str).tolist()
    selected: list[str] = []
    for column in columns:
        series = frame[column]
        if pd.api.types.is_datetime64_any_dtype(series):
            selected.append(column)
            continue
        lower = column.lower()
        if not any(token in lower for token in ["date", "time", "period", "day", "month", "year"]):
            continue
        sample = series.dropna().astype(str).head(500)
        if sample.empty:
            continue
        parsed = pd.to_datetime(sample, errors="coerce")
        if parsed.notna().mean() >= 0.6:
            selected.append(column)
    seen: set[str] = set()
    ordered: list[str] = []
    for column in selected:
        if column in seen:
            continue
        seen.add(column)
        ordered.append(column)
    return ordered


def _dedupe_ordered(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        ordered.append(text)
    return ordered


def _is_id_like_column(column: str) -> bool:
    lower = str(column or "").strip().lower()
    return bool(re.search(r"(^|_)(id|code|no)$|invoice|customerid|userid|sellerid|orderid", lower))


def _numeric_parse_ratio(series: pd.Series) -> float:
    sample = series.dropna().head(1000)
    if sample.empty:
        return 0.0
    parsed = pd.to_numeric(sample, errors="coerce")
    return float(parsed.notna().mean()) if len(parsed) else 0.0


_VARIANCE_BASELINE_MARKERS = (
    "预算",
    "计划",
    "目标",
    "forecast",
    "budget",
    "plan",
    "target",
    "planned",
    "expected",
    "预估",
)
_VARIANCE_ACTUAL_MARKERS = (
    "实际",
    "实绩",
    "实收",
    "实销",
    "actual",
    "observed",
    "realized",
    "monitor",
    "measured",
    "监测",
)
_VARIANCE_FAMILY_MARKERS: dict[str, tuple[str, ...]] = {
    "revenue": ("收入", "营收", "revenue", "sales", "gmv"),
    "cost": ("成本", "花费", "支出", "费用", "cost", "spend", "expense"),
    "profit": ("利润", "毛利", "净利", "profit", "margin"),
    "cashflow": ("现金流", "cash", "cashflow"),
    "inventory": ("存货", "库存", "inventory", "stock"),
    "receivable": ("应收", "应收账款", "receivable", "ar"),
    "payable": ("应付", "应付账款", "payable", "ap"),
    "asset": ("资产", "总资产", "asset"),
    "liability": ("负债", "总负债", "liability"),
    "equity": ("权益", "所有者权益", "equity"),
}


def _strip_markers(text: str, markers: tuple[str, ...]) -> str:
    cleaned = text
    for marker in markers:
        cleaned = cleaned.replace(marker, "")
    return cleaned


def _infer_variance_pairs(columns: list[str], numeric_columns: list[str]) -> list[dict[str, str]]:
    numeric_set = set(numeric_columns)
    baseline_candidates: list[dict[str, str]] = []
    actual_candidates: list[dict[str, str]] = []

    for column in columns:
        if column not in numeric_set:
            continue
        lower = str(column).lower()
        baseline = any(marker in lower for marker in _VARIANCE_BASELINE_MARKERS)
        actual = any(marker in lower for marker in _VARIANCE_ACTUAL_MARKERS)
        if not baseline and not actual:
            continue

        family = ""
        for family_name, markers in _VARIANCE_FAMILY_MARKERS.items():
            if any(marker in lower for marker in markers):
                family = family_name
                break
        if not family:
            family = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", _strip_markers(_strip_markers(lower, _VARIANCE_BASELINE_MARKERS), _VARIANCE_ACTUAL_MARKERS))

        payload = {"column": column, "family": family}
        if baseline:
            baseline_candidates.append(payload)
        if actual:
            actual_candidates.append(payload)

    pairs: list[dict[str, str]] = []
    for budget_item in baseline_candidates:
        for actual_item in actual_candidates:
            if budget_item["family"] and budget_item["family"] == actual_item["family"]:
                pairs.append(
                    {
                        "baseline_column": budget_item["column"],
                        "actual_column": actual_item["column"],
                        "family": budget_item["family"],
                    }
                )
    deduped: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in pairs:
        marker = f"{item['baseline_column']}::{item['actual_column']}"
        if marker in seen:
            continue
        seen.add(marker)
        deduped.append(item)
    return deduped


def _build_r_workflow_column_registry(frame: pd.DataFrame) -> dict[str, Any]:
    temporal_columns = _infer_r_temporal_columns(frame)
    columns = frame.columns.astype(str).tolist()
    numeric_method_columns: list[str] = []
    category_dimension_columns: list[str] = []
    object_dimension_columns: list[str] = []
    excluded_from_numeric_methods: list[dict[str, str]] = []

    object_name_tokens = ("item", "product", "sku", "spu", "brand", "supplier", "vendor", "seller", "shop", "customer")
    text_heavy_tokens = ("name", "title", "note", "comment", "remark", "description", "desc", "content", "text", "summary")

    for column in columns:
        series = frame[column]
        lower = column.lower()

        if column in temporal_columns:
            excluded_from_numeric_methods.append({"column": column, "reason": "temporal_column"})
            continue

        if _is_id_like_column(column):
            excluded_from_numeric_methods.append({"column": column, "reason": "identifier_column"})
            if any(token in lower for token in object_name_tokens):
                object_dimension_columns.append(column)
            continue

        if pd.api.types.is_numeric_dtype(series):
            usable = pd.to_numeric(series, errors="coerce")
            if usable.notna().sum() >= 3 and usable.dropna().nunique() > 1:
                numeric_method_columns.append(column)
            else:
                excluded_from_numeric_methods.append({"column": column, "reason": "insufficient_numeric_variation"})
            continue

        parse_ratio = _numeric_parse_ratio(series)
        if parse_ratio >= 0.8:
            usable = pd.to_numeric(series, errors="coerce")
            if usable.notna().sum() >= 3 and usable.dropna().nunique() > 1:
                numeric_method_columns.append(column)
            else:
                excluded_from_numeric_methods.append({"column": column, "reason": "insufficient_coerced_numeric_variation"})
            continue

        unique_count = int(series.dropna().astype(str).nunique())
        text_len = float(series.dropna().astype(str).str.len().mean()) if series.dropna().size else 0.0
        is_text_heavy = any(token in lower for token in text_heavy_tokens) or text_len > 48

        if any(token in lower for token in object_name_tokens):
            object_dimension_columns.append(column)

        if unique_count >= 2 and unique_count <= max(12, min(50, int(len(frame) * 0.6) if len(frame) else 12)) and not is_text_heavy:
            category_dimension_columns.append(column)
        else:
            excluded_from_numeric_methods.append({"column": column, "reason": "non_numeric_text_or_high_cardinality"})

    numeric_method_columns = _dedupe_ordered(numeric_method_columns)
    category_dimension_columns = _dedupe_ordered(category_dimension_columns)
    object_dimension_columns = _dedupe_ordered(object_dimension_columns)
    variance_pairs = _infer_variance_pairs(columns, numeric_method_columns)

    return {
        "temporal_columns": _dedupe_ordered(temporal_columns),
        "numeric_method_columns": numeric_method_columns,
        "category_dimension_columns": category_dimension_columns,
        "object_dimension_columns": object_dimension_columns,
        "variance_pairs": variance_pairs,
        "excluded_from_numeric_methods": excluded_from_numeric_methods,
    }


def _merge_r_workflow_semantic_registry(
    heuristic_registry: dict[str, Any],
    ai_registry: dict[str, Any] | None,
    available_columns: list[str],
) -> dict[str, Any]:
    available_set = {str(column) for column in available_columns}
    merged = dict(heuristic_registry)
    ai_registry = ai_registry or {}

    def _filter_columns(values: list[Any], fallback: list[str]) -> list[str]:
        selected = [str(value).strip() for value in values if str(value).strip() in available_set]
        return _dedupe_ordered(selected) if selected else list(fallback)

    merged["numeric_method_columns"] = _filter_columns(
        list(ai_registry.get("numeric_method_columns") or []),
        list(heuristic_registry.get("numeric_method_columns") or []),
    )
    merged["category_dimension_columns"] = _filter_columns(
        list(ai_registry.get("category_dimension_columns") or []),
        list(heuristic_registry.get("category_dimension_columns") or []),
    )
    merged["object_dimension_columns"] = _filter_columns(
        list(ai_registry.get("object_dimension_columns") or []),
        list(heuristic_registry.get("object_dimension_columns") or []),
    )
    merged["temporal_columns"] = _filter_columns(
        list(ai_registry.get("temporal_columns") or []),
        list(heuristic_registry.get("temporal_columns") or []),
    )

    numeric_set = set(merged.get("numeric_method_columns") or [])
    ai_pairs = []
    for item in ai_registry.get("variance_pairs") or []:
        baseline = str(item.get("baseline_column") or "").strip()
        actual = str(item.get("actual_column") or "").strip()
        if baseline in available_set and actual in available_set and baseline in numeric_set and actual in numeric_set:
            ai_pairs.append(
                {
                    "baseline_column": baseline,
                    "actual_column": actual,
                    "family": str(item.get("family") or "").strip(),
                    "reason": str(item.get("reason") or "").strip(),
                }
            )
    merged["variance_pairs"] = ai_pairs or list(heuristic_registry.get("variance_pairs") or [])
    merged["semantic_understanding_mode"] = "ai" if ai_pairs or ai_registry.get("live_available") else "heuristic"
    merged["semantic_understanding_runtime_state"] = str(ai_registry.get("runtime_state") or "")
    return merged


def _run_rscript(runtime_path: str, script_path: Path, args: list[str], workflow_dir: Path, *, log_prefix: str) -> None:
    process = subprocess.run(
        [runtime_path, str(script_path), *args],
        cwd=str(workflow_dir),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    _write_text(workflow_dir / f"{log_prefix}-stdout.log", process.stdout or "")
    _write_text(workflow_dir / f"{log_prefix}-stderr.log", process.stderr or "")
    if process.returncode != 0:
        raise RuntimeError(
            f"R 工作流执行失败：{process.stderr.strip() or process.stdout.strip() or f'Rscript exit {process.returncode}'}"
        )

def _looks_like_pca_cluster_runtime_failure(message: str) -> bool:
    lower = str(message or "").lower()
    return any(
        marker in lower
        for marker in (
            "prcomp.default",
            "cannot rescale a constant/zero column",
            "zero column",
            "kmeans",
            "cluster_member_detail",
            "pca_axis_summary",
            "invalid subscript type 'list'",
            "invalid subscript type \"list\"",
        )
    )


def _read_csv_rows(path: Path, limit: int = 20) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        rows: list[dict[str, Any]] = []
        for index, row in enumerate(reader):
            if index >= limit:
                break
            rows.append({str(key): value for key, value in row.items()})
        return rows


def _read_csv_rows_full(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        rows: list[dict[str, Any]] = []
        for index, row in enumerate(reader):
            if limit is not None and index >= limit:
                break
            rows.append({str(key): value for key, value in row.items()})
        return rows


def _count_csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        count = -1
        for count, _ in enumerate(reader):
            pass
    return max(count, 0)


def _read_text_content(path: Path, limit: int | None = None) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    if limit is not None and len(text) > limit:
        return text[:limit].rstrip() + "\n... [truncated]"
    return text


def _markdown_escape(value: Any) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", "<br>")


def _pretty_table_column_label(value: Any) -> str:
    text = str(value or "").strip()
    mapping = {
        "Period": "周期",
        "date": "日期",
        "column": "字段",
        "n": "样本量",
        "mean": "均值",
        "median": "中位数",
        "sd": "标准差",
        "min": "最小值",
        "max": "最大值",
        "category": "类别",
        "count": "数量",
        "value": "数值",
        "method": "方法",
        "output": "输出文件",
        "status": "状态",
        "ResponsibilityCenter": "责任中心",
        "Supplier": "供应商",
        "Category": "品类",
        "Product": "商品",
        "SKU": "SKU",
        "InvoiceNo": "发票号",
        "CustomerID": "客户ID",
        "Quantity": "销量",
        "UnitPrice": "单价",
        "Revenue": "销售额",
        "PurchaseCost": "采购成本",
        "Inventory": "库存",
        "Budget": "预算",
        "Actual": "实际值",
        "GrossProfit": "毛利",
        "ROI": "ROI",
        "page_views": "浏览量",
        "cart_count": "加购量",
        "fav_count": "收藏量",
        "buy_count": "购买量",
        "user_count": "用户数",
        "buy_rate": "购买率",
        "cart_rate": "加购率",
        "item_id": "商品ID",
        "category_id": "类目ID",
    }
    if text in mapping:
        return mapping[text]
    if text.endswith(".csv") or text.endswith(".png") or text.endswith(".R"):
        return text
    cleaned = text.replace("_", " ").strip()
    return cleaned


def _pretty_table_display_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        if value.is_integer():
            return f"{int(value):,}"
        return f"{value:,.4f}".rstrip("0").rstrip(".")
    text = str(value).strip()
    if not text:
        return ""
    try:
        numeric = float(text)
    except ValueError:
        return text
    if numeric.is_integer():
        return f"{int(numeric):,}"
    return f"{numeric:,.4f}".rstrip("0").rstrip(".")


def _build_table_markdown(title: str, rows: list[dict[str, Any]], note: str = "") -> list[str]:
    if not rows:
        return [f"### {title}", "", "_无数据_", ""]
    columns = list(rows[0].keys())
    lines = [f"### {title}", ""]
    if note.strip():
        lines.append(note.strip())
        lines.append("")
    labels = [_pretty_table_column_label(column) for column in columns]
    lines.append("| " + " | ".join(labels) + " |")
    lines.append("| " + " | ".join(["---"] * len(columns)) + " |")
    for row in rows:
        lines.append("| " + " | ".join(_markdown_escape(_pretty_table_display_value(row.get(column, ""))) for column in columns) + " |")
    lines.append("")
    return lines


def _build_code_sections(workflow_dir: Path) -> list[dict[str, str]]:
    return [
        {
            "title": filename,
            "language": "r" if filename.endswith(".R") else "text",
            "content": _read_text_content(workflow_dir / filename),
        }
        for filename in ["01_clean_prepare.R", "02_analysis_visualize.R", "run_r_workflow.R"]
        if (workflow_dir / filename).exists()
    ]


def _build_log_sections(workflow_dir: Path) -> list[dict[str, str]]:
    sections: list[dict[str, str]] = []
    for path in sorted(workflow_dir.glob("*.log")):
        spec = R_WORKFLOW_OUTPUT_SPECS.get(path.name, {})
        sections.append(
            {
                "title": str(spec.get("title") or path.name),
                "filename": path.name,
                "content": _read_text_content(path, limit=12000),
            }
        )
    return sections


def _build_image_sections(workflow_dir: Path, chart_notes: dict[str, list[str]] | None = None) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    note_map = chart_notes or {}
    image_paths = sorted(workflow_dir.glob("*.png"))
    has_survey_visuals = any(path.name in SURVEY_VISUAL_IMAGE_ORDER for path in image_paths)
    if has_survey_visuals:
        image_paths = [
            path
            for path in image_paths
            if path.name not in SURVEY_UNSUITABLE_GENERIC_IMAGES
        ]
        order_map = {name: index for index, name in enumerate(SURVEY_VISUAL_IMAGE_ORDER)}
        image_paths = sorted(image_paths, key=lambda path: (order_map.get(path.name, 99), path.name))
    else:
        order_map = {name: index for index, name in enumerate(GENERIC_VISUAL_IMAGE_ORDER)}
        image_paths = sorted(image_paths, key=lambda path: (order_map.get(path.name, 99), path.name))
    for path in image_paths:
        spec = R_WORKFLOW_OUTPUT_SPECS.get(path.name, {})
        sections.append(
            {
                "title": str(spec.get("title") or path.name),
                "path": str(path.resolve()),
                "filename": path.name,
                "notes": list(note_map.get(path.name) or []),
            }
        )
    return sections


def _csv_section_by_filename(csv_sections: list[dict[str, Any]], filename: str) -> dict[str, Any]:
    for section in csv_sections:
        if str(section.get("filename") or "") == filename:
            return section
    return {}


def _safe_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except Exception:
        return None


def _fmt_num(value: Any) -> str:
    number = _safe_float(value)
    if number is None:
        return str(value or "n/a")
    if float(number).is_integer():
        return f"{int(number):,}"
    return f"{number:,.1f}"


def _fmt_pct(value: Any) -> str:
    number = _safe_float(value)
    if number is None:
        return str(value or "n/a")
    return f"{number * 100:.1f}%"


def _top_rows(rows: list[dict[str, Any]], limit: int = 3) -> list[dict[str, Any]]:
    return rows[:limit] if rows else []


def _component_sort_key(component_name: str) -> tuple[int, str]:
    text = str(component_name or "").strip()
    match = re.fullmatch(r"PC(\d+)", text, flags=re.I)
    if match:
        return (int(match.group(1)), text)
    return (10**9, text)


def _load_cluster_count_map(workflow_dir: Path | None) -> dict[str, int]:
    if workflow_dir is None:
        return {}
    path = workflow_dir / "kmeans_clusters.csv"
    rows = _read_csv_rows_full(path)
    counts: dict[str, int] = {}
    for row in rows:
        cluster_name = str(_row_value(row, "cluster", default="")).strip()
        if not cluster_name:
            continue
        counts[cluster_name] = counts.get(cluster_name, 0) + 1
    return counts


def _load_summary_mean_map(workflow_dir: Path | None) -> dict[str, float]:
    if workflow_dir is None:
        return {}
    path = workflow_dir / "summary_stats.csv"
    rows = _read_csv_rows_full(path)
    mean_map: dict[str, float] = {}
    for row in rows:
        column_name = str(_row_value(row, "column", default="")).strip()
        mean_value = _safe_float(row.get("mean"))
        if column_name and mean_value is not None:
            mean_map[column_name] = mean_value
    return mean_map


def _fmt_multiplier(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.1f} 倍"


def _build_chart_interpretation_map(
    *,
    csv_sections: list[dict[str, Any]],
    interpretation_layer: dict[str, Any],
) -> dict[str, list[str]]:
    chart_notes: dict[str, list[str]] = {}

    summary_rows = _csv_section_by_filename(csv_sections, "summary_stats.csv").get("rows", [])
    quantile_rows = _csv_section_by_filename(csv_sections, "quantile_profile.csv").get("rows", [])
    anomaly_rows = _csv_section_by_filename(csv_sections, "anomaly_summary.csv").get("rows", [])
    skew_rows = _csv_section_by_filename(csv_sections, "skew_kurtosis_summary.csv").get("rows", [])
    corr_rows = _csv_section_by_filename(csv_sections, "correlation_pairs.csv").get("rows", [])
    category_rows = _csv_section_by_filename(csv_sections, "top_categories.csv").get("rows", [])
    category_share_rows = _csv_section_by_filename(csv_sections, "category_share_summary.csv").get("rows", [])
    category_metric_rows = _csv_section_by_filename(csv_sections, "category_metric_summary.csv").get("rows", [])
    trend_rows = _csv_section_by_filename(csv_sections, "temporal_trend.csv").get("rows", [])
    growth_rows = _csv_section_by_filename(csv_sections, "temporal_growth.csv").get("rows", [])
    profile_rows = _csv_section_by_filename(csv_sections, "temporal_period_profile.csv").get("rows", [])
    funnel_rows = _csv_section_by_filename(csv_sections, "funnel_metrics.csv").get("rows", [])
    funnel_conv_rows = _csv_section_by_filename(csv_sections, "funnel_conversion_summary.csv").get("rows", [])
    top_item_rows = _csv_section_by_filename(csv_sections, "top_items.csv").get("rows", [])
    item_metric_rows = _csv_section_by_filename(csv_sections, "item_metric_summary.csv").get("rows", [])
    survey_multi_rows = _csv_section_by_filename(csv_sections, "survey_multi_select_rates.csv").get("rows", [])
    survey_likert_rows = _csv_section_by_filename(csv_sections, "survey_likert_summary.csv").get("rows", [])
    survey_distribution_rows = _csv_section_by_filename(csv_sections, "survey_likert_distribution.csv").get("rows", [])
    survey_cooccurrence_rows = _csv_section_by_filename(csv_sections, "survey_multi_select_cooccurrence.csv").get("rows", [])
    survey_likert_corr_rows = _csv_section_by_filename(csv_sections, "survey_likert_correlation.csv").get("rows", [])
    survey_segment_rows = _csv_section_by_filename(csv_sections, "survey_segment_likert_means.csv").get("rows", [])
    survey_segment_distribution_rows = _csv_section_by_filename(csv_sections, "survey_segment_distribution.csv").get("rows", [])
    survey_segment_multi_rows = _csv_section_by_filename(csv_sections, "survey_segment_multi_select_rates.csv").get("rows", [])
    survey_sentiment_rows = _csv_section_by_filename(csv_sections, "survey_likert_sentiment_balance.csv").get("rows", [])
    survey_portfolio_rows = _csv_section_by_filename(csv_sections, "survey_multi_select_portfolio.csv").get("rows", [])
    survey_segment_multi_bubble_rows = _csv_section_by_filename(csv_sections, "survey_segment_multi_select_bubble.csv").get("rows", [])
    survey_segment_likert_bubble_rows = _csv_section_by_filename(csv_sections, "survey_segment_likert_bubble.csv").get("rows", [])
    generic_corr_bubble_rows = _csv_section_by_filename(csv_sections, "generic_correlation_bubble.csv").get("rows", [])
    generic_category_heatmap_rows = _csv_section_by_filename(csv_sections, "generic_category_metric_heatmap.csv").get("rows", [])
    generic_outlier_bubble_rows = _csv_section_by_filename(csv_sections, "generic_outlier_influence_bubble.csv").get("rows", [])
    generic_trend_rows = _csv_section_by_filename(csv_sections, "generic_time_trend_grid.csv").get("rows", [])
    generic_distribution_rows = _csv_section_by_filename(csv_sections, "generic_numeric_distribution_grid.csv").get("rows", [])
    generic_contribution_rows = _csv_section_by_filename(csv_sections, "generic_cumulative_contribution_curve.csv").get("rows", [])
    generic_segment_bubble_rows = _csv_section_by_filename(csv_sections, "generic_segment_bubble.csv").get("rows", [])
    generic_top_bottom_rows = _csv_section_by_filename(csv_sections, "generic_top_bottom_performer.csv").get("rows", [])
    generic_scatter_rows = _csv_section_by_filename(csv_sections, "generic_key_metric_scatter_bubble.csv").get("rows", [])
    missingness_rows = _csv_section_by_filename(csv_sections, "missingness_diagnostics.csv").get("rows", [])

    if missingness_rows:
        notes = []
        ordered = sorted(
            missingness_rows,
            key=lambda row: _safe_float(row.get("missing_rate")) or 0,
            reverse=True,
        )
        for row in ordered[:5]:
            if (_safe_float(row.get("missing_rate")) or 0) <= 0:
                continue
            notes.append(
                f"`{row.get('column', 'n/a')}` missing rate {_fmt_pct(row.get('missing_rate'))}, missing count {_fmt_num(row.get('missing_count'))}."
            )
        if notes:
            chart_notes["generic_missingness_bar.png"] = notes

    if generic_corr_bubble_rows:
        notes = []
        ordered = sorted(
            generic_corr_bubble_rows,
            key=lambda row: _safe_float(row.get("abs_correlation")) or 0,
            reverse=True,
        )
        for row in ordered[:5]:
            notes.append(
                f"`{row.get('left', 'n/a')}` × `{row.get('right', 'n/a')}` correlation {_fmt_num(row.get('correlation'))}, n={_fmt_num(row.get('n'))}."
            )
        chart_notes["generic_correlation_bubble.png"] = notes

    if generic_distribution_rows:
        metrics = list(dict.fromkeys(str(row.get("metric") or "") for row in generic_distribution_rows if str(row.get("metric") or "")))
        notes = [f"Distribution small multiples cover {len(metrics)} numeric metrics: {', '.join(metrics[:5])}."]
        chart_notes["generic_numeric_distribution_grid.png"] = notes

    if generic_category_heatmap_rows:
        notes = []
        ordered = sorted(
            generic_category_heatmap_rows,
            key=lambda row: abs(_safe_float(row.get("lift_vs_overall")) or 0),
            reverse=True,
        )
        for row in ordered[:5]:
            notes.append(
                f"`{row.get('category_column', 'n/a')}`={row.get('category_level', 'n/a')} on `{row.get('metric', 'n/a')}` lift {_fmt_pct(row.get('lift_vs_overall'))}."
            )
        chart_notes["generic_category_metric_heatmap.png"] = notes

    if generic_segment_bubble_rows:
        notes = []
        ordered = sorted(
            generic_segment_bubble_rows,
            key=lambda row: abs(_safe_float(row.get("lift_vs_overall")) or 0),
            reverse=True,
        )
        for row in ordered[:5]:
            notes.append(
                f"`{row.get('category_level', 'n/a')}` share {_fmt_pct(row.get('category_share'))}, `{row.get('metric', 'n/a')}` lift {_fmt_pct(row.get('lift_vs_overall'))}."
            )
        chart_notes["generic_segment_bubble.png"] = notes

    if generic_top_bottom_rows:
        notes = []
        ordered = sorted(
            generic_top_bottom_rows,
            key=lambda row: _safe_float(row.get("lift_vs_overall")) or 0,
            reverse=True,
        )
        for row in ordered[:3]:
            notes.append(
                f"Top `{row.get('category_level', 'n/a')}` lift {_fmt_pct(row.get('lift_vs_overall'))} on `{row.get('metric', 'n/a')}`."
            )
        for row in list(reversed(ordered[-2:])):
            notes.append(
                f"Bottom `{row.get('category_level', 'n/a')}` lift {_fmt_pct(row.get('lift_vs_overall'))} on `{row.get('metric', 'n/a')}`."
            )
        chart_notes["generic_top_bottom_performer.png"] = notes

    if generic_contribution_rows:
        notes = []
        for row in generic_contribution_rows[:5]:
            notes.append(
                f"Rank {row.get('rank', 'n/a')} `{row.get('category_level', 'n/a')}` contributes {_fmt_pct(row.get('contribution_share'))}; cumulative {_fmt_pct(row.get('cumulative_share'))}."
            )
        chart_notes["generic_cumulative_contribution_curve.png"] = notes

    if generic_scatter_rows:
        first = generic_scatter_rows[0]
        notes = [
            f"Scatter compares `{first.get('x_metric', 'x')}` vs `{first.get('y_metric', 'y')}` with bubble size `{first.get('size_metric', 'size')}`.",
            f"Rendered {len(generic_scatter_rows)} sampled rows for cluster/outlier reading.",
        ]
        chart_notes["generic_key_metric_scatter_bubble.png"] = notes

    if generic_outlier_bubble_rows:
        notes = []
        ordered = sorted(
            generic_outlier_bubble_rows,
            key=lambda row: (_safe_float(row.get("iqr_outlier_rate")) or 0, _safe_float(row.get("mean_relative_shift")) or 0),
            reverse=True,
        )
        for row in ordered[:5]:
            notes.append(
                f"`{row.get('column', 'n/a')}` outlier rate {_fmt_pct(row.get('iqr_outlier_rate'))}, mean shift {_fmt_pct(row.get('mean_relative_shift'))}."
            )
        chart_notes["generic_outlier_influence_bubble.png"] = notes

    if generic_trend_rows:
        notes = []
        grouped_metrics = list(dict.fromkeys(str(row.get("metric") or "") for row in generic_trend_rows if str(row.get("metric") or "")))
        for metric in grouped_metrics[:5]:
            metric_rows = [row for row in generic_trend_rows if str(row.get("metric") or "") == metric]
            if len(metric_rows) < 2:
                continue
            start = _safe_float(metric_rows[0].get("indexed_value"))
            end = _safe_float(metric_rows[-1].get("indexed_value"))
            if start is not None and end is not None:
                notes.append(f"`{metric}` indexed trend moved from {_fmt_num(start)} to {_fmt_num(end)}.")
        if notes:
            chart_notes["generic_time_trend_grid.png"] = notes

    if survey_multi_rows:
        notes = []
        ordered = sorted(
            survey_multi_rows,
            key=lambda row: _safe_float(row.get("selected_rate")) or 0,
            reverse=True,
        )
        for row in ordered[:5]:
            notes.append(
                f"`{row.get('short_label', 'n/a')}` 选择率 {_fmt_pct(row.get('selected_rate'))}，样本基数 {_fmt_num(row.get('base_n'))}。"
            )
        chart_notes["survey_multi_select_rates.png"] = notes

    if survey_likert_rows:
        notes = []
        ordered = sorted(
            survey_likert_rows,
            key=lambda row: _safe_float(row.get("mean")) or 0,
            reverse=True,
        )
        for row in ordered[:5]:
            notes.append(
                f"`{row.get('short_label', 'n/a')}` 均值 {_fmt_num(row.get('mean'))}，95% CI 为 {_fmt_num(row.get('ci_low'))}-{_fmt_num(row.get('ci_high'))}，正向率 {_fmt_pct(row.get('positive_rate'))}。"
            )
        chart_notes["survey_likert_mean_ci.png"] = notes

    if survey_distribution_rows:
        notes = []
        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in survey_distribution_rows:
            grouped.setdefault(str(row.get("short_label") or "n/a"), []).append(row)
        for label, rows in list(grouped.items())[:5]:
            top = max(rows, key=lambda row: _safe_float(row.get("rate")) or 0)
            notes.append(
                f"`{label}` 最集中回答为 {top.get('response_value', 'n/a')}，占比 {_fmt_pct(top.get('rate'))}。"
            )
        chart_notes["survey_likert_distribution.png"] = notes

    if survey_cooccurrence_rows:
        notes = []
        ordered = sorted(
            survey_cooccurrence_rows,
            key=lambda row: _safe_float(row.get("co_selected_rate")) or 0,
            reverse=True,
        )
        for row in ordered[:5]:
            notes.append(
                f"`{row.get('option_a_short', 'n/a')}` + `{row.get('option_b_short', 'n/a')}` co-selection {_fmt_pct(row.get('co_selected_rate'))}, lift {_fmt_num(row.get('lift_vs_independent'))}."
            )
        chart_notes["survey_multi_select_cooccurrence.png"] = notes

    if survey_portfolio_rows:
        notes = []
        ordered = sorted(
            survey_portfolio_rows,
            key=lambda row: _safe_float(row.get("selected_rate")) or 0,
            reverse=True,
        )
        for row in ordered[:5]:
            notes.append(
                f"`{row.get('option_short', 'n/a')}` reach {_fmt_pct(row.get('selected_rate'))}, mean co-selection lift {_fmt_num(row.get('mean_lift_vs_independent'))}."
            )
        chart_notes["survey_multi_select_portfolio.png"] = notes

    if survey_likert_corr_rows:
        notes = []
        ordered = sorted(
            survey_likert_corr_rows,
            key=lambda row: _safe_float(row.get("abs_correlation")) or 0,
            reverse=True,
        )
        for row in ordered[:5]:
            notes.append(
                f"`{row.get('item_a_short', 'n/a')}` and `{row.get('item_b_short', 'n/a')}` Spearman correlation {_fmt_num(row.get('spearman_corr'))}."
            )
        chart_notes["survey_likert_correlation_heatmap.png"] = notes

    if survey_sentiment_rows:
        notes = []
        ordered = sorted(
            survey_sentiment_rows,
            key=lambda row: _safe_float(row.get("net_positive_rate")) or 0,
            reverse=True,
        )
        for row in ordered[:5]:
            notes.append(
                f"`{row.get('short_label', 'n/a')}` net positive {_fmt_pct(row.get('net_positive_rate'))}, positive {_fmt_pct(row.get('positive_rate'))}, negative {_fmt_pct(row.get('negative_rate'))}."
            )
        chart_notes["survey_likert_sentiment_balance.png"] = notes

    if survey_segment_distribution_rows:
        notes = []
        ordered = sorted(
            survey_segment_distribution_rows,
            key=lambda row: _safe_float(row.get("rate")) or 0,
            reverse=True,
        )
        for row in ordered[:5]:
            notes.append(
                f"`{row.get('segment_short', 'n/a')}`={row.get('segment_level', 'n/a')} sample share {_fmt_pct(row.get('rate'))}, n={_fmt_num(row.get('count'))}."
            )
        chart_notes["survey_segment_distribution.png"] = notes

    if survey_segment_multi_rows:
        notes = []
        ordered = sorted(
            survey_segment_multi_rows,
            key=lambda row: _safe_float(row.get("selected_rate")) or 0,
            reverse=True,
        )
        for row in ordered[:5]:
            notes.append(
                f"`{row.get('segment_short', 'n/a')}`={row.get('segment_level', 'n/a')} selects `{row.get('option_short', 'n/a')}` at {_fmt_pct(row.get('selected_rate'))}."
            )
        chart_notes["survey_segment_multi_select_heatmap.png"] = notes

    if survey_segment_multi_bubble_rows:
        notes = []
        ordered = sorted(
            survey_segment_multi_bubble_rows,
            key=lambda row: abs(_safe_float(row.get("delta_vs_overall")) or 0),
            reverse=True,
        )
        for row in ordered[:5]:
            notes.append(
                f"`{row.get('segment_short', 'n/a')}`={row.get('segment_level', 'n/a')} on `{row.get('option_short', 'n/a')}` delta {_fmt_pct(row.get('delta_vs_overall'))} vs overall."
            )
        chart_notes["survey_segment_multi_select_bubble.png"] = notes

    if survey_segment_rows:
        notes = []
        ordered = sorted(
            survey_segment_rows,
            key=lambda row: _safe_float(row.get("mean")) or 0,
            reverse=True,
        )
        for row in ordered[:5]:
            notes.append(
                f"`{row.get('segment_short', 'n/a')}`={row.get('segment_level', 'n/a')} on `{row.get('likert_short', 'n/a')}` mean {_fmt_num(row.get('mean'))}."
            )
        chart_notes["survey_segment_likert_heatmap.png"] = notes

    if survey_segment_likert_bubble_rows:
        notes = []
        ordered = sorted(
            survey_segment_likert_bubble_rows,
            key=lambda row: abs(_safe_float(row.get("delta_vs_overall")) or 0),
            reverse=True,
        )
        for row in ordered[:5]:
            notes.append(
                f"`{row.get('segment_short', 'n/a')}`={row.get('segment_level', 'n/a')} on `{row.get('likert_short', 'n/a')}` mean delta {_fmt_num(row.get('delta_vs_overall'))}."
            )
        chart_notes["survey_segment_likert_bubble.png"] = notes

    if summary_rows:
        notes: list[str] = []
        quantile_map = {str(row.get("column") or ""): row for row in quantile_rows}
        anomaly_map = {str(row.get("column") or ""): row for row in anomaly_rows}
        for row in _top_rows(summary_rows, 3):
            column = str(row.get("column") or "n/a")
            mean_val = _safe_float(row.get("mean"))
            median_val = _safe_float(row.get("median"))
            anomaly_ratio = _safe_float((anomaly_map.get(column) or {}).get("outlier_ratio"))
            shape = "分布相对稳定"
            if mean_val is not None and median_val is not None:
                if median_val != 0 and abs(mean_val - median_val) / max(abs(median_val), 1) >= 0.2:
                    shape = "均值与中位数差距较大，说明分布偏斜"
            if anomaly_ratio is not None and anomaly_ratio >= 0.15:
                shape += f"，且异常值占比约 {_fmt_pct(anomaly_ratio)}"
            q_row = quantile_map.get(column) or {}
            notes.append(
                f"`{column}` 当前均值 {_fmt_num(row.get('mean'))}、中位数 {_fmt_num(row.get('median'))}、P25/P75 为 {_fmt_num(q_row.get('p25'))}/{_fmt_num(q_row.get('p75'))}，{shape}。"
            )
        chart_notes["numeric_distribution.png"] = notes

    if summary_rows:
        notes = []
        quantile_map = {str(row.get("column") or ""): row for row in quantile_rows}
        anomaly_map = {str(row.get("column") or ""): row for row in anomaly_rows}
        for row in _top_rows(summary_rows, 3):
            column = str(row.get("column") or "n/a")
            q_row = quantile_map.get(column) or {}
            a_row = anomaly_map.get(column) or {}
            notes.append(
                f"`{column}` 的箱体主要落在 {_fmt_num(q_row.get('p25'))} 到 {_fmt_num(q_row.get('p75'))} 之间，中位数 {_fmt_num(q_row.get('p50') or row.get('median'))}，异常值占比 {_fmt_pct(a_row.get('outlier_ratio'))}。"
            )
        chart_notes["numeric_boxplot.png"] = notes

    if skew_rows:
        notes = []
        for row in _top_rows(skew_rows, 3):
            column = str(row.get("column") or "n/a")
            skewness = _safe_float(row.get("skewness"))
            kurtosis = _safe_float(row.get("kurtosis"))
            shape = "分布较对称"
            if skewness is not None and abs(skewness) >= 0.8:
                shape = "分布明显偏斜"
            if kurtosis is not None and kurtosis >= 4:
                shape += "，且尾部较厚"
            notes.append(
                f"`{column}` 的偏度 {_fmt_num(skewness)}、峰度 {_fmt_num(kurtosis)}，说明{shape}。"
            )
        chart_notes["numeric_density.png"] = notes

    if corr_rows:
        notes = []
        for row in _top_rows(corr_rows, 3):
            left = str(row.get("left") or "n/a")
            right = str(row.get("right") or "n/a")
            corr = _safe_float(row.get("correlation"))
            direction = "同向联动" if (corr or 0) >= 0 else "反向联动"
            notes.append(f"`{left}` 与 `{right}` 的相关系数 {_fmt_num(corr)}，属于{direction}。")
        chart_notes["correlation_heatmap.png"] = notes
        chart_notes["numeric_scatter_plot.png"] = notes

    if category_rows:
        notes = []
        share_map = {(str(row.get("dimension") or ""), str(row.get("category") or "")): row for row in category_share_rows}
        for row in _top_rows(category_rows, 3):
            category = str(row.get("category") or "n/a")
            dimension = str(row.get("dimension") or "分类字段")
            share_row = share_map.get((dimension, category)) or {}
            notes.append(
                f"`{dimension}` 维度下，`{category}` 当前数量 {_fmt_num(row.get('count'))}，占比 {_fmt_pct(share_row.get('share'))}。"
            )
        chart_notes["category_mix.png"] = notes

    if category_share_rows:
        notes = []
        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in category_share_rows:
            grouped.setdefault(str(row.get("dimension") or "分类字段"), []).append(row)
        for dimension, rows in list(grouped.items())[:3]:
            top = rows[0]
            tail_index = min(2, len(rows) - 1)
            notes.append(
                f"`{dimension}` 维度下，头部类别 `{top.get('category', 'n/a')}` 当前占比 {_fmt_pct(top.get('share'))}，累计到头部第 {tail_index + 1} 类约占 {_fmt_pct((rows[tail_index] or {}).get('cumulative_share'))}。"
            )
            if len(rows) <= 2:
                notes.append(f"`{dimension}` 当前类别数过少，这张图主要看是否均衡分布，不适合强行套 20/80。")
        chart_notes["category_pareto.png"] = notes

    if category_metric_rows:
        notes = []
        for row in _top_rows(category_metric_rows, 3):
            notes.append(
                f"`{row.get('dimension', '分类字段')}` 维度下，`{row.get('category', 'n/a')}` 在当前指标上的均值约为 {_fmt_num(row.get('mean_value'))}。"
            )
        chart_notes["category_metric_plot.png"] = notes

    if trend_rows:
        notes = []
        metric_groups: dict[str, list[dict[str, Any]]] = {}
        for row in trend_rows:
            metric_groups.setdefault(str(row.get("metric") or "指标"), []).append(row)
        for metric, rows in list(metric_groups.items())[:3]:
            if len(rows) >= 2:
                first, last = rows[0], rows[-1]
                notes.append(
                    f"`{metric}` 从 `{first.get('period', 'n/a')}` 的 {_fmt_num(first.get('value'))} 变化到 `{last.get('period', 'n/a')}` 的 {_fmt_num(last.get('value'))}。"
                )
        chart_notes["temporal_trend.png"] = notes

    if growth_rows:
        notes = []
        for row in _top_rows(growth_rows, 3):
            notes.append(
                f"`{row.get('metric', 'n/a')}` 在 `{row.get('period_from', 'n/a')} → {row.get('period_to', 'n/a')}` 期间变动 {_fmt_pct(row.get('growth_rate'))}，绝对变化 {_fmt_num(row.get('delta'))}。"
            )
        chart_notes["temporal_growth.png"] = notes

    if profile_rows:
        notes = []
        metric_groups: dict[str, list[dict[str, Any]]] = {}
        for row in profile_rows:
            metric_groups.setdefault(str(row.get("metric") or "指标"), []).append(row)
        for metric, rows in list(metric_groups.items())[:3]:
            ordered = sorted(rows, key=lambda item: _safe_float(item.get("mean_value")) or 0, reverse=True)
            if ordered:
                top = ordered[0]
                notes.append(
                    f"`{metric}` 在 `{top.get('period_bucket', 'n/a')}` 的均值最高，约为 {_fmt_num(top.get('mean_value'))}。"
                )
        chart_notes["temporal_period_plot.png"] = notes

    if funnel_rows:
        notes = []
        if funnel_rows:
            first_stage = funnel_rows[0]
            last_stage = funnel_rows[-1]
            notes.append(
                f"漏斗从 `{first_stage.get('stage', 'n/a')}` 的 {_fmt_num(first_stage.get('total'))} 到 `{last_stage.get('stage', 'n/a')}` 的 {_fmt_num(last_stage.get('total'))}。"
            )
        if funnel_conv_rows:
            top_drop = min(
                funnel_conv_rows,
                key=lambda row: _safe_float(row.get("conversion_rate")) if _safe_float(row.get("conversion_rate")) is not None else 1.0,
            )
            notes.append(
                f"最弱转化环节是 `{top_drop.get('from_stage', 'n/a')} → {top_drop.get('to_stage', 'n/a')}`，转化率 {_fmt_pct(top_drop.get('conversion_rate'))}。"
            )
        chart_notes["funnel_overview.png"] = notes

    if top_item_rows:
        notes = []
        for row in _top_rows(top_item_rows, 3):
            notes.append(
                f"头部对象 `{row.get('item', row.get('item_id', 'n/a'))}` 当前总量 {_fmt_num(row.get('total_value'))}。"
            )
        if item_metric_rows:
            notes.append(
                f"头部对象均值层面最高的是 `{item_metric_rows[0].get('item', item_metric_rows[0].get('item_id', 'n/a'))}`，均值约 {_fmt_num(item_metric_rows[0].get('mean_value'))}。"
            )
        chart_notes["top_items_plot.png"] = notes

    generic_actions = [str(item).strip() for item in (interpretation_layer.get("action_recommendations") or []) if str(item).strip()]
    generic_risks = [str(item).strip() for item in (interpretation_layer.get("risk_alerts") or []) if str(item).strip()]
    for key, notes in list(chart_notes.items()):
        merged = notes[:3]
        if generic_actions:
            merged.append(f"动作建议：{generic_actions[0]}")
        elif generic_risks:
            merged.append(f"风险提醒：{generic_risks[0]}")
        chart_notes[key] = merged[:4]

    return chart_notes


def _build_csv_sections(workflow_dir: Path) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    for path in sorted(workflow_dir.glob("*.csv")):
        spec = R_WORKFLOW_OUTPUT_SPECS.get(path.name, {})
        preview_limit = int(spec.get("preview_limit") or 200)
        total_rows = _count_csv_rows(path)
        rows = _read_csv_rows_full(path, limit=preview_limit if total_rows > preview_limit else None)
        note = ""
        if total_rows > preview_limit:
            note = f"原始文件共 {total_rows} 行，PDF 内展示前 {len(rows)} 行。"
        else:
            note = f"原始文件共 {total_rows} 行，已完整展示。"
        sections.append(
            {
                "title": str(spec.get("title") or path.stem),
                "filename": path.name,
                "rows": rows,
                "note": note,
            }
        )
    return sections


def _build_output_inventory_rows(downloadables: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "输出文件": str(item.get("name") or ""),
            "类型": str(item.get("type") or ""),
            "主文件": "是" if bool(item.get("is_main")) else "否",
            "说明": str(item.get("purpose") or ""),
        }
        for item in downloadables
    ]


def _safe_workbook_sheet_name(name: str, used: set[str]) -> str:
    cleaned = re.sub(r"[\[\]\*\?/\\:]", "_", str(name or "").strip())
    cleaned = cleaned.replace("-", "_")
    cleaned = cleaned[:31] or "sheet"
    candidate = cleaned
    index = 2
    while candidate in used:
        suffix = f"_{index}"
        candidate = f"{cleaned[: max(1, 31 - len(suffix))]}{suffix}"
        index += 1
    used.add(candidate)
    return candidate


def _read_csv_frame(path: Path) -> pd.DataFrame:
    for encoding in ("utf-8-sig", "utf-8"):
        try:
            return pd.read_csv(path, encoding=encoding)
        except Exception:
            continue
    return pd.DataFrame()


def _build_column_role_rows(column_role_registry: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for role_key, role_label in [
        ("numeric_method_columns", "numeric_method"),
        ("category_dimension_columns", "category_dimension"),
        ("object_dimension_columns", "object_dimension"),
        ("temporal_columns", "temporal_column"),
    ]:
        for column in column_role_registry.get(role_key, []) or []:
            rows.append({"column": str(column), "role": role_label, "reason": ""})
    for item in column_role_registry.get("excluded_from_numeric_methods", []) or []:
        rows.append(
            {
                "column": str(item.get("column") or ""),
                "role": "excluded_from_numeric_methods",
                "reason": str(item.get("reason") or ""),
            }
        )
    return rows


def _write_r_workflow_statistics_workbook(
    *,
    workflow_dir: Path,
    report_id: str,
    dataset_name: str,
    sheet_name: str,
    runtime_path: str,
    column_role_registry: dict[str, Any],
) -> Path:
    workbook_path = workflow_dir / f"{report_id}-r-statistics-summary.xlsx"
    temp_workbook_path = workflow_dir / f".{report_id}-r-statistics-summary.tmp.xlsx"
    excluded_csv_names = {"input-data.csv", "cleaned_dataset.csv"}
    ordered_csv_paths: list[Path] = []
    for file_name in R_WORKFLOW_OUTPUT_SPECS:
        if not file_name.endswith(".csv") or file_name in excluded_csv_names:
            continue
        path = workflow_dir / file_name
        if path.exists():
            ordered_csv_paths.append(path)
    seen_paths = {str(path.resolve()) for path in ordered_csv_paths}
    for path in sorted(workflow_dir.glob("*.csv")):
        if path.name in excluded_csv_names:
            continue
        resolved = str(path.resolve())
        if resolved not in seen_paths:
            ordered_csv_paths.append(path)
            seen_paths.add(resolved)

    inventory_rows = [
        {
            "file_name": path.name,
            "title": str((R_WORKFLOW_OUTPUT_SPECS.get(path.name) or {}).get("title") or path.stem),
            "row_count": _count_csv_rows(path),
            "path": str(path.resolve()),
        }
        for path in ordered_csv_paths
    ]
    overview_rows = [
        {"field": "report_id", "value": report_id},
        {"field": "dataset_name", "value": dataset_name},
        {"field": "sheet_name", "value": sheet_name},
        {"field": "runtime_path", "value": runtime_path},
        {"field": "csv_result_count", "value": str(len(ordered_csv_paths))},
    ]
    column_role_rows = _build_column_role_rows(column_role_registry)

    used_sheet_names: set[str] = set()
    if temp_workbook_path.exists():
        try:
            temp_workbook_path.unlink()
        except Exception:
            pass
    with pd.ExcelWriter(temp_workbook_path, engine="openpyxl") as writer:
        pd.DataFrame(overview_rows).to_excel(
            writer,
            index=False,
            sheet_name=_safe_workbook_sheet_name("overview", used_sheet_names),
        )
        pd.DataFrame(inventory_rows).to_excel(
            writer,
            index=False,
            sheet_name=_safe_workbook_sheet_name("results_index", used_sheet_names),
        )
        pd.DataFrame(column_role_rows or [{"column": "", "role": "", "reason": ""}]).to_excel(
            writer,
            index=False,
            sheet_name=_safe_workbook_sheet_name("column_roles", used_sheet_names),
        )
        for path in ordered_csv_paths:
            frame = _read_csv_frame(path)
            if frame.empty and _count_csv_rows(path) == 0:
                frame = pd.DataFrame([{"note": "empty_result"}])
            frame.to_excel(
                writer,
                index=False,
                sheet_name=_safe_workbook_sheet_name(path.stem, used_sheet_names),
            )
    try:
        temp_workbook_path.replace(workbook_path)
        return workbook_path
    except PermissionError:
        fallback_path = workflow_dir / f"{report_id}-r-statistics-summary-refresh.xlsx"
        if fallback_path.exists():
            try:
                fallback_path.unlink()
            except Exception:
                fallback_path = workflow_dir / f"{report_id}-r-statistics-summary-refresh-{pd.Timestamp.utcnow().strftime('%Y%m%d%H%M%S')}.xlsx"
        temp_workbook_path.replace(fallback_path)
        return fallback_path


def _build_business_interpretation_sections(interpretation_layer: dict[str, Any]) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    for title, key in [
        ("核心指标解读", "key_metric_readings"),
        ("结构解读", "structure_readings"),
        ("趋势解读", "trend_readings"),
        ("关系解读", "relation_readings"),
        ("动作建议", "action_recommendations"),
        ("风险提醒", "risk_alerts"),
    ]:
        items = [str(item).strip() for item in (interpretation_layer.get(key) or []) if str(item).strip()]
        if items:
            sections.append({"title": title, "items": items[:6]})
    return sections


def _as_bool(value: Any) -> bool:
    return str(value or "").strip().lower() in {"true", "1", "yes", "y"}


def _row_value(row: dict[str, Any], *keys: str, default: str = "n/a") -> Any:
    for key in keys:
        if key in row and str(row.get(key, "")).strip():
            return row.get(key)
    return default


def _generic_method_row_summaries(rows: list[dict[str, Any]]) -> list[str]:
    summaries: list[str] = []
    for row in rows:
        parts = [
            f"{_pretty_table_column_label(key)}={_pretty_table_display_value(value)}"
            for key, value in row.items()
            if str(value or "").strip()
        ]
        if parts:
            summaries.append("；".join(parts[:6]))
    return summaries


def _summarize_csv_method_output(
    method_id: str,
    rows: list[dict[str, Any]],
    workflow_dir: Path | None = None,
) -> list[str]:
    if not rows:
        return []

    if method_id == "summary_stats":
        return [
            f"`{_row_value(row, 'column')}`：均值 {_fmt_num(row.get('mean'))}，中位数 {_fmt_num(row.get('median'))}，标准差 {_fmt_num(row.get('sd'))}，范围 {_fmt_num(row.get('min'))} 到 {_fmt_num(row.get('max'))}。"
            for row in rows
        ]

    if method_id == "quantile_profile":
        return [
            f"`{_row_value(row, 'column')}`：P05/P25/P50/P75/P95 分别为 {_fmt_num(row.get('p05'))} / {_fmt_num(row.get('p25'))} / {_fmt_num(row.get('p50'))} / {_fmt_num(row.get('p75'))} / {_fmt_num(row.get('p95'))}。"
            for row in rows
        ]

    if method_id == "anomaly_summary":
        return [
            f"`{_row_value(row, 'column')}`：IQR 区间 {_fmt_num(row.get('lower_bound'))} 到 {_fmt_num(row.get('upper_bound'))}，异常占比 {_fmt_pct(row.get('outlier_ratio'))}。"
            for row in rows
        ]

    if method_id == "zero_ratio_summary":
        return [
            f"`{_row_value(row, 'column')}`：零值 {_fmt_num(row.get('zero_count'))} 条，占比 {_fmt_pct(row.get('zero_ratio'))}。"
            for row in rows
        ]

    if method_id == "coefficient_variation":
        return [
            f"`{_row_value(row, 'column')}`：变异系数 {_fmt_num(_row_value(row, 'coefficient_variation', 'cv', default='n/a'))}，均值 {_fmt_num(row.get('mean'))}。"
            for row in rows
        ]

    if method_id == "skew_kurtosis_summary":
        return [
            f"`{_row_value(row, 'column')}`：偏度 {_fmt_num(row.get('skewness'))}，峰度 {_fmt_num(row.get('kurtosis'))}。"
            for row in rows
        ]

    if method_id == "missing_profile":
        return [
            f"`{_row_value(row, 'column')}`：缺失 {_fmt_num(row.get('missing_count'))} 条，缺失率 {_fmt_pct(row.get('missing_ratio'))}。"
            for row in rows
        ]

    if method_id == "duplicate_profile":
        return [
            f"`{_row_value(row, 'metric', 'column')}`：当前值 {_pretty_table_display_value(_row_value(row, 'value', default='n/a'))}。"
            for row in rows
        ]

    if method_id == "correlation_pairs":
        return [
            f"`{_row_value(row, 'left')}` 与 `{_row_value(row, 'right')}`：相关系数 {_fmt_num(row.get('correlation'))}。"
            for row in rows
        ]

    if method_id in {"correlation_matrix", "covariance_matrix"}:
        first_row = rows[0]
        field_names = [
            str(key).strip()
            for key in first_row.keys()
            if str(key).strip()
            and str(key).strip().lower() not in {"index", "row", "field", "column", "metric", "variable"}
        ]
        if field_names:
            return [f"当前矩阵覆盖字段：{'、'.join(field_names)}。"]
        return _generic_method_row_summaries(rows)

    if method_id == "pca_variance":
        component_rows: list[tuple[str, float, float]] = []
        for row in rows:
            component_name = str(_row_value(row, "component", "pc", default="")).strip()
            explained = _safe_float(_row_value(row, "explained_variance_ratio", "variance_ratio", "variance_explained", default=""))
            cumulative = _safe_float(_row_value(row, "cumulative_variance_ratio", "cumulative_ratio", "cumulative_variance", default=""))
            if component_name and explained is not None:
                component_rows.append((component_name, explained, cumulative if cumulative is not None else explained))
        component_rows.sort(key=lambda item: _component_sort_key(item[0]))
        if component_rows:
            cumulative_values = [item[2] for item in component_rows]
            one = cumulative_values[0]
            two = cumulative_values[1] if len(cumulative_values) >= 2 else cumulative_values[-1]
            three = cumulative_values[2] if len(cumulative_values) >= 3 else cumulative_values[-1]
            lead_parts = "；".join(
                [
                    f"`{name}`：解释方差 {_fmt_num(explained)}（{_fmt_pct(explained)}），累计解释 {_fmt_num(cumulative)}（{_fmt_pct(cumulative)}）"
                    for name, explained, cumulative in component_rows[:3]
                ]
            )
            if one >= 0.8:
                interpretation = "一个主轴就覆盖了大部分差异，说明这些指标很可能在重复描述同一类变化。"
            elif two >= 0.8:
                interpretation = "前两个主轴已经覆盖大部分差异，说明这批指标主要可以压缩成两个观察方向。"
            elif three >= 0.8:
                interpretation = "前三个主轴已经覆盖大部分差异，后续主轴更多是补充细节。"
            else:
                interpretation = "需要多个主轴一起看，说明样本差异不是单一方向造成的。"
            return [
                lead_parts + "。",
                f"前 1/2/3 个主成分累计解释 {_fmt_pct(one)} / {_fmt_pct(two)} / {_fmt_pct(three)}。",
                interpretation,
            ]
        return _generic_method_row_summaries(rows)

    if method_id == "pca_loadings":
        component_keys = [key for key in rows[0].keys() if re.fullmatch(r"PC\d+", str(key).strip())]
        component_keys.sort(key=_component_sort_key)
        if component_keys:
            summaries: list[str] = []
            for component in component_keys[:3]:
                weighted_fields: list[tuple[str, float]] = []
                for row in rows:
                    variable = str(_row_value(row, "column", "feature", "variable", default="")).strip()
                    loading = _safe_float(row.get(component))
                    if variable and loading is not None:
                        weighted_fields.append((variable, loading))
                weighted_fields.sort(key=lambda item: abs(item[1]), reverse=True)
                top_fields = weighted_fields[:3]
                if not top_fields:
                    continue
                lead_variable, lead_loading = top_fields[0]
                positive = [f"`{name}`" for name, value in top_fields if value >= 0]
                negative = [f"`{name}`" for name, value in top_fields if value < 0]
                if positive and negative:
                    summaries.append(
                        f"`{component}` - `{lead_variable}`：载荷 {_fmt_num(lead_loading)}。它主要把正向的 {'、'.join(positive)} 和反向的 {'、'.join(negative)} 拉开，说明这一轴更像“此消彼长”的结构差异。"
                    )
                else:
                    direction = "同向" if positive else "反向"
                    summaries.append(
                        f"`{component}` - `{lead_variable}`：载荷 {_fmt_num(lead_loading)}。它主要由 {'、'.join([f'`{name}`' for name, _ in top_fields])} {direction}驱动，说明这一轴更像综合变化轴，而不是单一字段。"
                    )
            return summaries
        return _generic_method_row_summaries(rows)

    if method_id == "pca_scores":
        component_keys = [key for key in rows[0].keys() if re.fullmatch(r"PC\d+", str(key).strip())]
        component_keys.sort(key=_component_sort_key)
        summaries: list[str] = []
        for component in component_keys[:2]:
            values = pd.to_numeric([row.get(component) for row in rows], errors="coerce")
            series = pd.Series(values).dropna()
            if series.empty:
                continue
            p10 = float(series.quantile(0.1))
            p50 = float(series.quantile(0.5))
            p90 = float(series.quantile(0.9))
            summaries.append(
                f"`{component}` 得分主要落在 {_fmt_num(p10)} 到 {_fmt_num(p90)} 之间，中位数 {_fmt_num(p50)}，全范围 {_fmt_num(series.min())} 到 {_fmt_num(series.max())}。"
            )
        if summaries:
            summaries.append("如果少数样本在主成分得分上远离主体，通常说明它们在综合规模或结构上明显不同，适合单独复核。")
            return summaries
        return _generic_method_row_summaries(rows)

    if method_id == "pca_axis_summary":
        summaries: list[str] = []
        for row in rows:
            component_name = _row_value(row, "component", default="")
            axis_summary = _row_value(row, "axis_summary", default="")
            positive = str(_row_value(row, "positive_drivers", default="")).replace("|", "、").strip()
            negative = str(_row_value(row, "negative_drivers", default="")).replace("|", "、").strip()
            explained = _fmt_pct(_row_value(row, "variance_explained", default="n/a"))
            if positive and negative:
                summaries.append(
                    f"`{component_name}`：主轴更像“{axis_summary}”，解释 {_fmt_num(_row_value(row, 'variance_explained', default='n/a'))}（{explained}）；正向由 {positive} 驱动，反向由 {negative} 拉开。"
                )
            else:
                summaries.append(
                    f"`{component_name}`：主轴更像“{axis_summary}”，解释 {_fmt_num(_row_value(row, 'variance_explained', default='n/a'))}（{explained}）。"
                )
        return summaries

    if method_id == "kmeans_clusters":
        cluster_counts: dict[str, int] = {}
        for row in rows:
            cluster_name = str(_row_value(row, "cluster", default="")).strip()
            if not cluster_name:
                continue
            cluster_counts[cluster_name] = cluster_counts.get(cluster_name, 0) + 1
        if cluster_counts:
            total = sum(cluster_counts.values())
            ordered = sorted(cluster_counts.items(), key=lambda item: item[1], reverse=True)
            summaries = [
                f"`{cluster}`：样本量 {_fmt_num(count)}，占 {_fmt_pct(count / total)}。"
                for cluster, count in ordered
            ]
            if total > 0 and ordered[0][1] / total >= 0.8 and len(ordered) > 1:
                summaries.append("分群明显头重脚轻，更像“主流盘 + 少量特殊样本”，不是几类均衡客群。")
            return summaries
        return _generic_method_row_summaries(rows)

    if method_id == "cluster_profile":
        cluster_counts = _load_cluster_count_map(workflow_dir)
        overall_mean_map = _load_summary_mean_map(workflow_dir)
        total = sum(cluster_counts.values())
        summaries: list[str] = []
        for row in rows:
            cluster_name = str(_row_value(row, "cluster", default="")).strip()
            if not cluster_name:
                continue
            metric_deltas: list[tuple[float, str, float]] = []
            for key, value in row.items():
                metric_name = str(key).strip()
                if not metric_name or metric_name.lower() in {"cluster", "index"}:
                    continue
                current_value = _safe_float(value)
                overall_value = overall_mean_map.get(metric_name)
                if current_value is None or overall_value in (None, 0):
                    continue
                ratio = current_value / overall_value
                metric_deltas.append((abs(ratio - 1), metric_name, ratio))
            metric_deltas.sort(key=lambda item: item[0], reverse=True)
            focus_parts: list[str] = []
            for _, metric_name, ratio in metric_deltas[:3]:
                if ratio >= 1.15:
                    focus_parts.append(f"`{metric_name}`偏高（约为整体 {_fmt_multiplier(ratio)}）")
                elif ratio <= 0.85:
                    focus_parts.append(f"`{metric_name}`偏低（约为整体 {_fmt_multiplier(ratio)}）")
                else:
                    focus_parts.append(f"`{metric_name}`接近整体")
            if cluster_name in cluster_counts and total > 0:
                prefix = f"`{cluster_name}`：{_fmt_num(cluster_counts[cluster_name])} 个样本，占 {_fmt_pct(cluster_counts[cluster_name] / total)}"
                share = cluster_counts[cluster_name] / total
                if share >= 0.6:
                    suffix = "，是主流群体。"
                elif share <= 0.05:
                    suffix = "，更像小众/异常群，适合单独复核。"
                else:
                    suffix = "，可以作为次级特征群体观察。"
            else:
                prefix = f"`{cluster_name}`："
                suffix = "。"
            if focus_parts:
                summaries.append(prefix + "；" + "；".join(focus_parts) + suffix)
            else:
                summaries.append(prefix + " 已生成聚类画像，可结合明细继续复核。")
        if summaries:
            return summaries
        return _generic_method_row_summaries(rows)

    if method_id == "cluster_member_detail":
        cluster_examples: dict[str, list[str]] = {}
        preferred_keys = ["item", "item_id", "SKU", "sku", "Product", "product", "OrderID", "InvoiceNo", "category", "category_id", "row_index"]
        for row in rows:
            cluster_name = str(_row_value(row, "cluster", default="")).strip()
            if not cluster_name:
                continue
            example_value = ""
            for key in preferred_keys:
                if str(row.get(key, "")).strip():
                    example_value = f"{_pretty_table_column_label(key)}={_pretty_table_display_value(row.get(key))}"
                    break
            if not example_value:
                non_cluster_keys = [key for key in row.keys() if str(key).strip().lower() not in {"cluster"} and str(row.get(key, "")).strip()]
                if non_cluster_keys:
                    key = non_cluster_keys[0]
                    example_value = f"{_pretty_table_column_label(key)}={_pretty_table_display_value(row.get(key))}"
            if example_value:
                cluster_examples.setdefault(cluster_name, [])
                if len(cluster_examples[cluster_name]) < 3:
                    cluster_examples[cluster_name].append(example_value)
        if cluster_examples:
            return [
                f"`{cluster}`：成员明细已展开，示例 {('；'.join(examples))}。"
                for cluster, examples in cluster_examples.items()
            ]
        return _generic_method_row_summaries(rows)

    if method_id == "top_categories":
        return [
            f"`{_row_value(row, 'dimension')}` 维度下，`{_row_value(row, 'category')}`：数量 {_fmt_num(_row_value(row, 'count', default='n/a'))}。"
            for row in rows
        ]

    if method_id == "category_share_summary":
        return [
            f"`{_row_value(row, 'dimension')}` 维度下，`{_row_value(row, 'category')}`：数量 {_fmt_num(_row_value(row, 'count', default='n/a'))}，占比 {_fmt_pct(_row_value(row, 'share', default='n/a'))}。"
            for row in rows
        ]

    if method_id == "category_metric_summary":
        summaries: list[str] = []
        for row in rows:
            metric_name = str(_row_value(row, "metric", default="")).strip()
            category_name = _row_value(row, "category", "price_band")
            current_value = _fmt_num(_row_value(row, "mean_value", "total_value", "value", default="n/a"))
            if metric_name:
                summaries.append(
                    f"`{_row_value(row, 'dimension')}` 维度下，`{category_name}`：指标 `{metric_name}` 当前值 {current_value}。"
                )
            else:
                summaries.append(
                    f"`{_row_value(row, 'dimension')}` 维度下，`{category_name}`：当前值 {current_value}。"
                )
        return summaries

    if method_id == "category_price_band_summary":
        return [
            f"`{_row_value(row, 'dimension')}` 维度下，`{_row_value(row, 'category')}`：指标 `{_row_value(row, 'metric', default='n/a')}` 落在分位带 `{_row_value(row, 'band', default='n/a')}` 的样本量 {_fmt_num(_row_value(row, 'count', default='n/a'))}。"
            for row in rows
        ]

    if method_id == "budget_variance_summary":
        return [
            f"`{_row_value(row, 'dimension')}` 维度下，`{_row_value(row, 'category')}`：`{_row_value(row, 'metric_pair', default='n/a')}` 预算均值 {_fmt_num(_row_value(row, 'budget_mean', default='n/a'))}，实际均值 {_fmt_num(_row_value(row, 'actual_mean', default='n/a'))}，偏差 {_fmt_num(_row_value(row, 'gap', default='n/a'))}，偏差率 {_fmt_pct(_row_value(row, 'gap_rate', default='n/a'))}。"
            for row in rows
        ]

    if method_id in {"temporal_trend", "temporal_moving_average"}:
        metric_groups: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            metric_groups.setdefault(str(_row_value(row, "metric")), []).append(row)
        return [
            f"`{metric}`：从 `{_row_value(metric_rows[0], 'period')}` 的 {_fmt_num(_row_value(metric_rows[0], 'value', 'moving_average', default='n/a'))} 变化到 `{_row_value(metric_rows[-1], 'period')}` 的 {_fmt_num(_row_value(metric_rows[-1], 'value', 'moving_average', default='n/a'))}，共 {len(metric_rows)} 个时间点。"
            for metric, metric_rows in metric_groups.items()
        ]

    if method_id == "temporal_growth":
        return [
            f"`{_row_value(row, 'metric')}`：`{_row_value(row, 'period_from')}` 到 `{_row_value(row, 'period_to')}` 增长率 {_fmt_pct(row.get('growth_rate'))}，绝对变化 {_fmt_num(row.get('delta'))}。"
            for row in rows
        ]

    if method_id == "temporal_period_profile":
        metric_groups: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            metric_groups.setdefault(str(_row_value(row, "metric")), []).append(row)
        summaries: list[str] = []
        for metric, metric_rows in metric_groups.items():
            bucket_parts = [
                f"{_row_value(row, 'period_bucket', 'bucket')}={_fmt_num(_row_value(row, 'mean_value', 'value', default='n/a'))}"
                for row in metric_rows
            ]
            summaries.append(f"`{metric}`：{'；'.join(bucket_parts)}。")
        return summaries

    if method_id == "funnel_metrics":
        return [
            f"`{_row_value(row, 'stage')}`：总量 {_fmt_num(_row_value(row, 'total', 'value', default='n/a'))}。"
            for row in rows
        ]

    if method_id == "funnel_conversion_summary":
        return [
            f"`{_row_value(row, 'from_stage')}` -> `{_row_value(row, 'to_stage')}`：转化率 {_fmt_pct(row.get('conversion_rate'))}。"
            for row in rows
        ]

    if method_id in {"top_items", "item_metric_summary"}:
        summaries: list[str] = []
        for row in rows:
            metric_name = str(_row_value(row, "metric", default="")).strip()
            item_name = _row_value(row, "item", "item_id")
            current_value = _fmt_num(_row_value(row, "total_value", "mean_value", "value", default="n/a"))
            if metric_name:
                summaries.append(f"`{item_name}`：指标 `{metric_name}` 当前值 {current_value}。")
            else:
                summaries.append(f"`{item_name}`：当前值 {current_value}。")
        return summaries

    if method_id == "item_daily_summary":
        item_groups: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            item_groups.setdefault(str(_row_value(row, "item", "item_id")), []).append(row)
        return [
            f"`{item_name}`：从 `{_row_value(item_rows[0], 'period', 'date')}` 的 {_fmt_num(_row_value(item_rows[0], 'value', 'total_value', default='n/a'))} 变化到 `{_row_value(item_rows[-1], 'period', 'date')}` 的 {_fmt_num(_row_value(item_rows[-1], 'value', 'total_value', default='n/a'))}。"
            for item_name, item_rows in item_groups.items()
        ]

    return _generic_method_row_summaries(rows)


def _summarize_method_output(workflow_dir: Path, method_id: str, output_name: str, note: str) -> list[str]:
    path = workflow_dir / output_name
    if not path.exists():
        return [note or "本次未生成对应输出。"]
    if path.suffix.lower() == ".csv":
        rows = _read_csv_rows_full(path)
        if not rows:
            return ["已生成结果文件，但当前结果为空表。"]
        summaries = _summarize_csv_method_output(method_id, rows, workflow_dir)
        return summaries or [note or f"已生成 `{output_name}`。"]
    if path.suffix.lower() == ".png":
        return [f"已生成图形 `{output_name}`，可直接用于视觉复核。"]
    if path.suffix.lower() == ".log":
        text = _read_text_content(path, limit=200).strip()
        return [text or "日志为空，说明这一段执行没有报错输出。"]
    return [note or f"已生成 `{output_name}`。"]


def _build_method_analysis_cards(workflow_dir: Path, method_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for row in method_rows:
        method_id = str(row.get("method") or "").strip()
        if not method_id:
            continue
        spec = R_WORKFLOW_METHOD_SPECS.get(method_id, {})
        output_name = str(row.get("output") or "").strip()
        status = _as_bool(row.get("status"))
        note = str(row.get("note") or "").strip()
        current_readings = _summarize_method_output(workflow_dir, method_id, output_name, note)
        cards.append(
            {
                "method_id": method_id,
                "title": str(spec.get("title") or method_id),
                "status": "已执行" if status else "未触发",
                "what": str(spec.get("what") or "用于补充结构化分析。"),
                "current_reading": " ".join(current_readings),
                "current_readings": current_readings,
                "business_use": str(spec.get("use") or "用于补充业务判断。"),
                "next_action": note or ("把这一方法的结果接入主结论，而不是只留在附件。" if status else "若业务确实需要这一视角，应补足字段后再重跑。"),
                "output_name": output_name,
            }
        )
    return cards


def _safe_r_workflow_purpose_text(*values: str) -> str:
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        question_ratio = text.count("?") / max(len(text), 1)
        if question_ratio > 0.25:
            continue
        return text
    return "R 工作流统计复核与业务解读"


def _build_interpretation_markdown(
    *,
    dataset_name: str,
    sheet_name: str,
    request: SmartReportRequest,
    runtime_path: str,
    interpretation_summary: list[str],
    interpretation_sections: list[dict[str, Any]],
    method_cards: list[dict[str, Any]],
    output_rows: list[dict[str, str]],
    csv_sections: list[dict[str, Any]],
    code_sections: list[dict[str, str]],
    image_sections: list[dict[str, Any]],
    log_sections: list[dict[str, str]],
) -> str:
    purpose_text = _safe_r_workflow_purpose_text(
        request.core_purpose,
        request.problem_to_solve,
        request.user_requirement,
    )
    lines = [
        "# R 工作流解读",
        "",
        f"- 数据集：`{dataset_name}`",
        f"- 工作表：`{sheet_name}`",
        f"- Rscript：`{runtime_path}`",
        f"- 使用目的：`{purpose_text}`",
        "",
        "## 业务解读",
        "",
        *[f"- {item}" for item in interpretation_summary[:6]],
        "",
        "## 产品说明",
        "",
        "| 输出文件 | 类型 | 主文件 | 说明 |",
        "| --- | --- | --- | --- |",
        *[
            f"| {row['输出文件']} | {row['类型']} | {row['主文件']} | {row['说明']} |"
            for row in output_rows
        ],
        "",
        "## 解读展开",
        "",
        "## 使用边界",
        "",
        "- 这份 R 解读服务于独立复核、复算和图形落地，不会替代主报告的整体业务结论。",
        "- 当前图形和统计主要使用基础 R 能力，若需要更高级可视化，可在后续补装 `ggplot2` 等包。",
        "",
    ]
    boundary_block = lines[-4:]
    lines = lines[:-4]
    if interpretation_sections:
        for section in interpretation_sections:
            lines.extend([f"### {section['title']}", ""])
            lines.extend([f"- {item}" for item in section["items"]])
            lines.append("")
    else:
        lines.extend(["_当前没有更多结构化解读。_", ""])
    lines.extend(boundary_block)
    lines.extend(["## 方法逐项解读", ""])
    for card in method_cards:
        current_readings = [
            str(item).strip()
            for item in (card.get("current_readings") or [])
            if str(item).strip()
        ] or [str(card.get("current_reading") or "").strip()]
        lines.extend(
            [
                f"### {card['title']}（{card['status']}）",
                "",
                f"- 它在看什么：{card['what']}",
                "- 当前看到什么：",
                *[f"  - {item}" for item in current_readings if item],
                f"- 业务上怎么用：{card['business_use']}",
                f"- 下一步建议：{card['next_action']}",
                "",
            ]
        )
    lines.extend(["## R 脚本正文", ""])
    for section in code_sections:
        lines.extend(
            [
                f"### {section['title']}",
                "",
                f"```{section['language']}",
                section["content"].rstrip(),
                "```",
                "",
            ]
        )

    lines.extend(["## R 结果表格", ""])
    for section in csv_sections:
        lines.extend(
            _build_table_markdown(
                f"{section['title']}（{section['filename']}）",
                section["rows"],
                section.get("note", ""),
            )
        )

    lines.extend(["## R 图形输出", ""])
    if image_sections:
        for section in image_sections:
            lines.extend(
                [
                    f"### {section['title']}",
                    "",
                    f"![{section['title']}]({section['filename']})",
                    "",
                ]
            )
            notes = [str(item).strip() for item in (section.get("notes") or []) if str(item).strip()]
            if notes:
                lines.extend(["图表解读：", ""])
                lines.extend([f"- {item}" for item in notes])
                lines.append("")
    else:
        lines.extend(["_无图形输出_", ""])

    lines.extend(["## R 日志输出", ""])
    if log_sections:
        for section in log_sections:
            lines.extend(
                [
                    f"### {section['title']}",
                    "",
                    "```text",
                    section["content"].rstrip(),
                    "```",
                    "",
                ]
            )
    else:
        lines.extend(["_无日志输出_", ""])

    return "\n".join(lines)


def _write_interpretation_html(
    *,
    dataset_name: str,
    sheet_name: str,
    runtime_path: str,
    purpose_text: str,
    interpretation_summary: list[str],
    interpretation_sections: list[dict[str, Any]],
    method_cards: list[dict[str, Any]],
    output_rows: list[dict[str, str]],
    csv_sections: list[dict[str, Any]],
    code_sections: list[dict[str, str]],
    image_sections: list[dict[str, Any]],
    log_sections: list[dict[str, str]],
    html_path: Path,
) -> None:
    summary_html = "".join(f"<li>{html.escape(item)}</li>" for item in interpretation_summary[:6])
    output_table = "".join(
        "<tr>"
        + "".join(
            f"<td>{html.escape(str(row.get(column, '')))}</td>"
            for column in ["输出文件", "类型", "主文件", "说明"]
        )
        + "</tr>"
        for row in output_rows
    )
    code_html = "".join(
        f"<section><h3>{html.escape(section['title'])}</h3><pre>{html.escape(section['content'])}</pre></section>"
        for section in code_sections
    ) or "<p>无脚本输出。</p>"
    csv_html_parts: list[str] = []
    for section in csv_sections:
        if section["rows"]:
            columns = list(section["rows"][0].keys())
            table_rows = "".join(
                "<tr>" + "".join(f"<td>{html.escape(_pretty_table_display_value(row.get(column, '')))}</td>" for column in columns) + "</tr>"
                for row in section["rows"]
            )
            table_html = (
                "<table><thead><tr>"
                + "".join(f"<th>{html.escape(_pretty_table_column_label(column))}</th>" for column in columns)
                + "</tr></thead><tbody>"
                + table_rows
                + "</tbody></table>"
            )
        else:
            table_html = "<p>无数据。</p>"
        csv_html_parts.append(
            f"<section><h3>{html.escape(section['title'])} ({html.escape(section['filename'])})</h3>"
            f"<p class=\"note\">{html.escape(section.get('note', ''))}</p>{table_html}</section>"
        )
    csv_html = "".join(csv_html_parts) or "<p>无结果表格。</p>"
    image_html = "".join(
        "<section>"
        f"<h3>{html.escape(section['title'])}</h3>"
        f"<img src=\"{html.escape(section['filename'])}\" alt=\"{html.escape(section['title'])}\" />"
        + (
            "<div class=\"chart-notes\"><h4>图表解读</h4><ul>"
            + "".join(f"<li>{html.escape(str(item))}</li>" for item in (section.get("notes") or []) if str(item).strip())
            + "</ul></div>"
            if any(str(item).strip() for item in (section.get("notes") or []))
            else ""
        )
        + "</section>"
        for section in image_sections
    ) or "<p>无图形输出。</p>"
    log_html = "".join(
        f"<section><h3>{html.escape(section['title'])}</h3><pre>{html.escape(section['content'])}</pre></section>"
        for section in log_sections
    ) or "<p>无日志输出。</p>"
    interpretation_detail_html = "".join(
        f"<section><h3>{html.escape(section['title'])}</h3><ul>"
        + "".join(f"<li>{html.escape(item)}</li>" for item in section["items"])
        + "</ul></section>"
        for section in interpretation_sections
    ) or "<p>当前没有更多结构化解读。</p>"
    method_card_html = "".join(
        "<section>"
        f"<h3>{html.escape(card['title'])}（{html.escape(card['status'])}）</h3>"
        "<ul>"
        f"<li><strong>它在看什么：</strong>{html.escape(card['what'])}</li>"
        "<li><strong>当前看到什么：</strong><ul>"
        + "".join(
            f"<li>{html.escape(str(item))}</li>"
            for item in (
                [str(entry).strip() for entry in (card.get("current_readings") or []) if str(entry).strip()]
                or [str(card.get("current_reading") or "").strip()]
            )
            if str(item).strip()
        )
        + "</ul></li>"
        f"<li><strong>业务上怎么用：</strong>{html.escape(card['business_use'])}</li>"
        f"<li><strong>下一步建议：</strong>{html.escape(card['next_action'])}</li>"
        "</ul>"
        "</section>"
        for card in method_cards
    ) or "<p>当前没有方法卡。</p>"
    html_body = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>R Workflow Interpretation</title>
  <style>
    :root {{
      --paper: #fbf8f2;
      --card: #ffffff;
      --ink: #1f2430;
      --muted: #5b6472;
      --line: #d9d3c7;
      --head: #efe6d7;
      --row: #faf7f1;
      --accent: #7b5c33;
    }}
    body {{ font-family: Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif; margin: 0; padding: 28px; background: linear-gradient(180deg, #f5efe4 0%, var(--paper) 100%); color: var(--ink); }}
    main {{ max-width: 1280px; margin: 0 auto; background: var(--card); border-radius: 24px; padding: 34px 40px; box-shadow: 0 18px 44px rgba(58, 43, 22, 0.08); }}
    h1 {{ margin: 0 0 12px; font-size: 34px; letter-spacing: 0.01em; }}
    h2 {{ margin-top: 32px; margin-bottom: 14px; font-size: 26px; border-bottom: 2px solid #eee3d1; padding-bottom: 8px; }}
    h3 {{ margin-top: 24px; margin-bottom: 10px; font-size: 20px; }}
    p, li {{ line-height: 1.8; }}
    ul {{ margin: 0; padding-left: 22px; }}
    .meta-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px 18px; margin: 18px 0 6px; }}
    .meta-card {{ background: #f8f2e8; border: 1px solid #eadfce; border-radius: 16px; padding: 12px 14px; }}
    .meta-label {{ display: block; font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; }}
    .meta-value {{ display: block; margin-top: 4px; font-size: 15px; color: var(--ink); word-break: break-word; }}
    .note {{ color: var(--muted); font-size: 13px; margin-bottom: 10px; }}
    .table-wrap {{ overflow-x: auto; border: 1px solid #e7ddcf; border-radius: 16px; box-shadow: inset 0 1px 0 rgba(255,255,255,0.6); }}
    table {{ width: 100%; border-collapse: separate; border-spacing: 0; font-size: 13px; table-layout: auto; }}
    th, td {{ border-right: 1px solid var(--line); border-bottom: 1px solid var(--line); padding: 9px 10px; text-align: left; vertical-align: top; line-height: 1.55; word-break: break-word; }}
    th:last-child, td:last-child {{ border-right: none; }}
    thead th {{ position: sticky; top: 0; background: var(--head); color: var(--ink); font-weight: 700; }}
    tbody tr:nth-child(even) td {{ background: var(--row); }}
    tbody tr:hover td {{ background: #f4ecdf; }}
    pre {{ background: #f7f6f3; border: 1px solid #e6dfd2; border-radius: 16px; padding: 16px 18px; overflow-x: auto; white-space: pre-wrap; word-break: break-word; font-size: 12px; line-height: 1.7; }}
    img {{ max-width: 100%; border: 1px solid #dfd4c2; border-radius: 16px; margin-top: 10px; background: white; padding: 8px; box-shadow: 0 8px 20px rgba(63, 46, 21, 0.06); }}
    .chart-notes {{ margin-top: 10px; background: #f8f2e8; border: 1px solid #eadfce; border-radius: 14px; padding: 12px 14px; }}
    .chart-notes h4 {{ margin: 0 0 6px; font-size: 15px; color: #5b6472; }}
    .chart-notes ul {{ margin: 0; padding-left: 18px; }}
  </style>
</head>
<body>
  <main>
    <h1>R 工作流解读</h1>
    <div class="meta-grid">
      <div class="meta-card"><span class="meta-label">数据集</span><span class="meta-value">{html.escape(dataset_name)}</span></div>
      <div class="meta-card"><span class="meta-label">工作表</span><span class="meta-value">{html.escape(sheet_name)}</span></div>
      <div class="meta-card"><span class="meta-label">Rscript</span><span class="meta-value">{html.escape(runtime_path)}</span></div>
      <div class="meta-card"><span class="meta-label">使用目的</span><span class="meta-value">{html.escape(purpose_text)}</span></div>
    </div>
    <h2>业务解读</h2>
    <ul>{summary_html}</ul>
    <h2>产品说明</h2>
    <div class="table-wrap"><table><thead><tr><th>输出文件</th><th>类型</th><th>主文件</th><th>说明</th></tr></thead><tbody>{output_table}</tbody></table></div>
    <h2>解读展开</h2>
    {interpretation_detail_html}
    <h2>方法逐项解读</h2>
    {method_card_html}
    <h2>R 脚本正文</h2>
    {code_html}
    <h2>R 结果表格</h2>
    {csv_html}
    <h2>R 图形输出</h2>
    {image_html}
    <h2>R 日志输出</h2>
    {log_html}
    <h2>使用边界</h2>
    <ul>
      <li>这份 R 解读服务于独立复核、复算和图形落地，不会替代主报告的整体业务结论。</li>
      <li>当前图形和统计主要使用基础 R 能力，若需要更高级可视化，可在后续补装 ggplot2 等包。</li>
    </ul>
  </main>
</body>
</html>"""
    _write_text(html_path, html_body)


def _write_interpretation_pdf(
    *,
    dataset_name: str,
    sheet_name: str,
    runtime_path: str,
    purpose_text: str,
    interpretation_summary: list[str],
    interpretation_sections: list[dict[str, Any]],
    method_cards: list[dict[str, Any]],
    output_rows: list[dict[str, str]],
    csv_sections: list[dict[str, Any]],
    code_sections: list[dict[str, str]],
    image_sections: list[dict[str, Any]],
    log_sections: list[dict[str, str]],
    pdf_path: Path,
) -> Path | None:
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_LEFT
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.platypus import Image as RLImage, LongTable, PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer, TableStyle
    except Exception:
        return None

    font_name = "Helvetica"
    for candidate in [r"C:\Windows\Fonts\simhei.ttf", r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simsun.ttc"]:
        if Path(candidate).exists():
            try:
                font_name = "AsteriaCN"
                pdfmetrics.registerFont(TTFont(font_name, candidate))
                break
            except Exception:
                font_name = "Helvetica"

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "RWorkflowTitle",
        parent=styles["Heading1"],
        fontName=font_name,
        fontSize=18,
        leading=24,
        textColor=colors.HexColor("#1f2430"),
        alignment=TA_LEFT,
    )
    body_style = ParagraphStyle(
        "RWorkflowBody",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=10,
        leading=15,
        textColor=colors.HexColor("#2f3742"),
    )
    table_header_style = ParagraphStyle(
        "RWorkflowTableHeader",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1f2430"),
    )
    table_body_style = ParagraphStyle(
        "RWorkflowTableBody",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#2f3742"),
    )
    code_style = ParagraphStyle(
        "RWorkflowCode",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#1f2430"),
    )
    meta_label_style = ParagraphStyle(
        "RWorkflowMetaLabel",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#7b6a57"),
    )
    meta_value_style = ParagraphStyle(
        "RWorkflowMetaValue",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#1f2430"),
    )

    page_size = landscape(A4)
    page_width, page_height = page_size
    horizontal_margin = 14 * mm
    vertical_margin = 12 * mm
    available_width = page_width - 2 * horizontal_margin

    def _estimate_table_widths(columns: list[str], rows: list[dict[str, Any]]) -> list[float]:
        if not columns:
            return []
        weights: list[float] = []
        for column in columns:
            samples = [_pretty_table_column_label(column)]
            for row in rows[:24]:
                samples.append(_pretty_table_display_value(row.get(column, "")))
            longest = max(len(text) for text in samples)
            if longest <= 8:
                weight = 1.0
            elif longest <= 18:
                weight = 1.45
            elif longest <= 32:
                weight = 1.9
            else:
                weight = 2.4
            weights.append(weight)
        total_weight = sum(weights) or 1.0
        widths = [available_width * (weight / total_weight) for weight in weights]
        min_width = 26 * mm
        adjusted = [max(min_width, width) for width in widths]
        adjusted_total = sum(adjusted)
        if adjusted_total > available_width:
            scale = available_width / adjusted_total
            adjusted = [width * scale for width in adjusted]
        return adjusted

    def append_table(title: str, rows: list[dict[str, Any]], note: str = "") -> None:
        story.append(Paragraph(title, title_style))
        if note.strip():
            story.append(Paragraph(note, body_style))
        if not rows:
            story.append(Paragraph("无数据。", body_style))
            story.append(Spacer(1, 2 * mm))
            return
        columns = list(rows[0].keys())
        visible_columns = columns[:10]
        visible_rows = rows[:24]
        if len(columns) > len(visible_columns):
            story.append(Paragraph(f"这张表原始共有 {len(columns)} 列，PDF 仅展示前 {len(visible_columns)} 列；完整结果请看 CSV 或 HTML。", body_style))
        if len(rows) > len(visible_rows):
            story.append(Paragraph(f"这张表原始共有 {len(rows)} 行，PDF 仅展示前 {len(visible_rows)} 行；完整结果请看 CSV 或 HTML。", body_style))
        local_table_data = [
            [Paragraph(html.escape(_pretty_table_column_label(column)), table_header_style) for column in visible_columns]
        ]
        for row in visible_rows:
            local_table_data.append(
                [
                    Paragraph(html.escape(_pretty_table_display_value(row.get(column, ""))), table_body_style)
                    for column in visible_columns
                ]
            )
        local_table = LongTable(local_table_data, repeatRows=1, colWidths=_estimate_table_widths(visible_columns, visible_rows))
        local_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), font_name),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EFE6D7")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1f2430")),
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D7CCBA")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAF7F1")]),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(local_table)
        story.append(Spacer(1, 3 * mm))

    story = [
        Paragraph("R 工作流解读", title_style),
        Spacer(1, 4 * mm),
    ]
    meta_rows = [
        [
            Paragraph("数据集", meta_label_style),
            Paragraph("工作表", meta_label_style),
            Paragraph("Rscript", meta_label_style),
            Paragraph("使用目的", meta_label_style),
        ],
        [
            Paragraph(html.escape(dataset_name), meta_value_style),
            Paragraph(html.escape(sheet_name), meta_value_style),
            Paragraph(html.escape(runtime_path), meta_value_style),
            Paragraph(html.escape(purpose_text), meta_value_style),
        ],
    ]
    meta_table = LongTable(meta_rows, colWidths=[available_width / 4.0] * 4)
    meta_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8F2E8")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#E6DCCB")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.extend(
        [
            meta_table,
            Spacer(1, 4 * mm),
        Spacer(1, 3 * mm),
        Paragraph("业务解读", title_style),
        ]
    )
    for item in interpretation_summary[:6]:
        story.append(Paragraph(f"- {html.escape(item)}", body_style))

    story.extend([Spacer(1, 3 * mm), Paragraph("产品说明", title_style)])
    table_data = [
        [
            Paragraph("输出文件", table_header_style),
            Paragraph("类型", table_header_style),
            Paragraph("主文件", table_header_style),
            Paragraph("说明", table_header_style),
        ]
    ]
    for row in output_rows:
        table_data.append(
            [
                Paragraph(html.escape(str(row.get("输出文件", ""))), table_body_style),
                Paragraph(html.escape(str(row.get("类型", ""))), table_body_style),
                Paragraph(html.escape(str(row.get("主文件", ""))), table_body_style),
                Paragraph(html.escape(str(row.get("说明", ""))), table_body_style),
            ]
        )
    output_table = LongTable(table_data, repeatRows=1, colWidths=_estimate_table_widths(["输出文件", "类型", "主文件", "说明"], output_rows))
    output_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EFE6D7")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1f2430")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D7CCBA")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAF7F1")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(output_table)
    story.extend([Spacer(1, 4 * mm), Paragraph("解读展开", title_style)])
    if interpretation_sections:
        for section in interpretation_sections:
            story.append(Paragraph(section["title"], title_style))
            for item in section["items"]:
                story.append(Paragraph(f"- {html.escape(item)}", body_style))
            story.append(Spacer(1, 2 * mm))
    else:
        story.append(Paragraph("当前没有更多结构化解读。", body_style))
    story.extend([Spacer(1, 4 * mm), Paragraph("方法逐项解读", title_style)])
    if method_cards:
        for card in method_cards:
            current_readings = [
                str(item).strip()
                for item in (card.get("current_readings") or [])
                if str(item).strip()
            ] or [str(card.get("current_reading") or "").strip()]
            story.append(Paragraph(f"{card['title']}（{card['status']}）", title_style))
            story.append(Paragraph(f"- 它在看什么：{html.escape(card['what'])}", body_style))
            story.append(Paragraph("- 当前看到什么：", body_style))
            for item in current_readings:
                story.append(Paragraph(f"  - {html.escape(item)}", body_style))
            story.append(Paragraph(f"- 业务上怎么用：{html.escape(card['business_use'])}", body_style))
            story.append(Paragraph(f"- 下一步建议：{html.escape(card['next_action'])}", body_style))
            story.append(Spacer(1, 2 * mm))
    else:
        story.append(Paragraph("当前没有方法卡。", body_style))
    story.extend([Spacer(1, 4 * mm), PageBreak(), Paragraph("R 脚本正文", title_style)])
    if code_sections:
        for section in code_sections:
            story.append(Paragraph(section["title"], title_style))
            story.append(Preformatted(section["content"].rstrip(), code_style))
            story.append(Spacer(1, 3 * mm))
    else:
        story.append(Paragraph("无脚本输出。", body_style))

    story.extend([PageBreak(), Paragraph("R 结果表格", title_style), Spacer(1, 2 * mm)])
    if csv_sections:
        for section in csv_sections:
            append_table(f"{section['title']}（{section['filename']}）", section["rows"], section.get("note", ""))
    else:
        story.append(Paragraph("无结果表格。", body_style))

    story.extend([PageBreak(), Paragraph("R 图形输出", title_style), Spacer(1, 2 * mm)])
    if image_sections:
        max_width = A4[0] - 30 * mm
        max_height = 160 * mm
        for section in image_sections:
            story.append(Paragraph(section["title"], title_style))
            image = RLImage(section["path"])
            scale = min(max_width / image.imageWidth, max_height / image.imageHeight, 1.0)
            image.drawWidth = image.imageWidth * scale
            image.drawHeight = image.imageHeight * scale
            story.append(image)
            notes = [str(item).strip() for item in (section.get("notes") or []) if str(item).strip()]
            if notes:
                story.append(Spacer(1, 1.5 * mm))
                story.append(Paragraph("图表解读", title_style))
                for item in notes:
                    story.append(Paragraph(f"- {html.escape(item)}", body_style))
            story.append(Spacer(1, 3 * mm))
    else:
        story.append(Paragraph("无图形输出。", body_style))

    story.extend([PageBreak(), Paragraph("R 日志输出", title_style), Spacer(1, 2 * mm)])
    if log_sections:
        for section in log_sections:
            story.append(Paragraph(section["title"], title_style))
            story.append(Preformatted(section["content"].rstrip() or "(empty)", code_style))
            story.append(Spacer(1, 3 * mm))
    else:
        story.append(Paragraph("无日志输出。", body_style))
    story.extend(
        [
            Spacer(1, 3 * mm),
            Paragraph("使用边界", title_style),
            Paragraph("- 这份 R 解读服务于独立复核、复算和图形落地，不会替代主报告的整体业务结论。", body_style),
            Paragraph("- 当前图形和统计主要使用基础 R 能力，若需要更高级可视化，可在后续补装 ggplot2 等包。", body_style),
        ]
    )

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=page_size,
        leftMargin=horizontal_margin,
        rightMargin=horizontal_margin,
        topMargin=vertical_margin,
        bottomMargin=vertical_margin,
    )
    doc.build(story)
    return pdf_path


def _report_storage_url(path: Path) -> str:
    try:
        relative = path.resolve().relative_to(REPORTS_DIR.parent.resolve()).as_posix()
    except Exception:
        return ""
    return f"/storage/{relative}"


def _build_r_workflow_codex_sidecar_prompt(
    *,
    workflow_dir: Path,
    dataset_name: str,
    sheet_name: str,
    report_lens: str,
    request: SmartReportRequest,
    interpretation_summary: list[str],
    column_role_registry: dict[str, Any],
) -> str:
    summary_text = "\n".join(f"- {item}" for item in interpretation_summary[:8]) or "- No interpretation summary available yet."
    context_payload = {
        "dataset_name": dataset_name,
        "sheet_name": sheet_name,
        "report_lens": report_lens,
        "user_requirement": request.user_requirement,
        "problem_to_solve": request.problem_to_solve,
        "target_audience": request.target_audience,
        "core_purpose": request.core_purpose,
        "expected_result": request.expected_result,
        "column_role_registry": column_role_registry,
        "interpretation_summary": interpretation_summary[:8],
    }
    return (
        "You are the Codex CLI sidecar reviewer for an R workflow directory.\n\n"
        f"Workspace: {workflow_dir}\n"
        f"Dataset: {dataset_name}\n"
        f"Sheet: {sheet_name}\n"
        f"Report lens: {report_lens}\n\n"
        "Mission:\n"
        "1. Inspect the generated R scripts, logs, CSV outputs, and interpretation artifacts.\n"
        "2. If you find obvious workflow robustness issues, you may patch local R scripts or add review artifacts.\n"
        "3. Prefer creating or updating a concise markdown note named `codex_sidecar_review.md` in this workspace.\n"
        "4. Do not invent numeric results.\n"
        "5. Do not modify any formal release flags.\n"
        "6. Do not claim deterministic execution happened if it did not.\n\n"
        "Current interpretation summary:\n"
        f"{summary_text}\n\n"
        "Structured context JSON:\n"
        f"{json.dumps(context_payload, ensure_ascii=False, indent=2)}\n\n"
        "At the end, summarize:\n"
        "- what you checked\n"
        "- what you changed\n"
        "- whether the current R workflow artifacts look usable\n"
        "- any validation or rerun gaps\n"
    )


def _codex_runtime_downloadables_from_result(result: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for key, purpose, file_type in [
        ("summary_path", "Codex CLI sidecar summary.", "md"),
        ("transcript_path", "Codex CLI sidecar transcript.", "json"),
        ("stdout_path", "Codex CLI sidecar stdout log.", "jsonl"),
        ("stderr_path", "Codex CLI sidecar stderr log.", "log"),
        ("git_diff_path", "Codex CLI sidecar git diff or patch artifact.", "patch"),
    ]:
        file_path = Path(str(result.get(key) or "")).expanduser()
        if not str(file_path):
            continue
        if not file_path.exists():
            continue
        items.append(
            {
                "name": file_path.name,
                "path": str(result.get(key.replace("_path", "_url")) or ""),
                "file_path": str(file_path.resolve()),
                "purpose": purpose,
                "is_main": False,
                "type": file_type,
            }
        )
    run_manifest = Path(str(result.get("transcript_path") or "")).expanduser().parent / "run.json"
    if run_manifest.exists():
        items.append(
            {
                "name": run_manifest.name,
                "path": _report_storage_url(run_manifest),
                "file_path": str(run_manifest.resolve()),
                "purpose": "Codex CLI sidecar run manifest.",
                "is_main": False,
                "type": "json",
            }
        )
    return items


def _workflow_sidecar_local_downloadables(workflow_dir: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for filename, purpose, file_type in [
        ("codex_sidecar_review.md", "Codex CLI sidecar local review note.", "md"),
        ("codex_sidecar_followups.md", "Codex CLI sidecar follow-up actions.", "md"),
    ]:
        path = workflow_dir / filename
        if not path.exists():
            continue
        items.append(
            {
                "name": path.name,
                "path": _report_storage_url(path),
                "file_path": str(path.resolve()),
                "purpose": purpose,
                "is_main": False,
                "type": file_type,
            }
        )
    return items


def _run_r_workflow_codex_sidecar(
    *,
    workflow_dir: Path,
    report_id: str,
    report_job_id: str,
    dataset_name: str,
    sheet_name: str,
    report_lens: str,
    request: SmartReportRequest,
    interpretation_summary: list[str],
    column_role_registry: dict[str, Any],
) -> dict[str, Any]:
    def _sync_fallback(reason: str) -> dict[str, Any]:
        prompt = _build_r_workflow_codex_sidecar_prompt(
            workflow_dir=workflow_dir,
            dataset_name=dataset_name,
            sheet_name=sheet_name,
            report_lens=report_lens,
            request=request,
            interpretation_summary=interpretation_summary,
            column_role_registry=column_role_registry,
        )
        run_request = CodexRunRequest(
            workspace_path=str(workflow_dir.resolve()),
            prompt=prompt,
            report_id=report_id,
            dataset_id="",
            sheet_name=sheet_name,
            stage_id="r_workflow_sidecar",
            purpose="r_workflow_sidecar_review",
            search=bool(settings.get("codex_search_enabled", False)),
            timeout_sec=min(int(settings.get("codex_timeout_sec", 1800) or 1800), 900),
            capture_git_diff=False,
            dangerously_bypass_approvals_and_sandbox=bool(
                settings.get("codex_dangerously_bypass_approvals_and_sandbox", False)
            ),
        )
        try:
            result = run_headless_codex(run_request)
        except Exception as exc:
            local_downloadables = _workflow_sidecar_local_downloadables(workflow_dir)
            return {
                "enabled": True,
                "status": "failed",
                "reason": f"{reason}:runtime_error",
                "task_id": "",
                "run_id": "",
                "session_id": "",
                "summary": "",
                "changed_files": [],
                "transcript_entry_count": 0,
                "downloadables": local_downloadables,
                "error": str(exc),
            }

        downloadables = _codex_runtime_downloadables_from_result(result)
        local_downloadables = _workflow_sidecar_local_downloadables(workflow_dir)
        seen_names = {str(item.get("name") or "") for item in downloadables}
        for item in local_downloadables:
            if str(item.get("name") or "") not in seen_names:
                downloadables.append(item)
        return {
            "enabled": True,
            "status": str(result.get("status") or "completed"),
            "reason": reason,
            "task_id": "",
            "run_id": str(result.get("run_id") or ""),
            "session_id": str(result.get("session_id") or ""),
            "summary": str(result.get("summary") or ""),
            "changed_files": list(result.get("changed_files") or []),
            "transcript_entry_count": int(result.get("transcript_entry_count") or 0),
            "downloadables": downloadables,
            "error": str(result.get("error") or ""),
        }

    settings = load_runtime_settings_raw()
    if not bool(settings.get("codex_runtime_enabled", False)):
        return {
            "enabled": False,
            "status": "skipped",
            "reason": "codex_runtime_disabled",
            "summary": "",
            "changed_files": [],
            "downloadables": [],
            "error": "",
        }

    prompt = _build_r_workflow_codex_sidecar_prompt(
        workflow_dir=workflow_dir,
        dataset_name=dataset_name,
        sheet_name=sheet_name,
        report_lens=report_lens,
        request=request,
        interpretation_summary=interpretation_summary,
        column_role_registry=column_role_registry,
    )
    run_request = CodexRunRequest(
        workspace_path=str(workflow_dir.resolve()),
        prompt=prompt,
        report_id=report_id,
        dataset_id="",
        sheet_name=sheet_name,
        stage_id="r_workflow_sidecar",
        purpose="r_workflow_sidecar_review",
        search=bool(settings.get("codex_search_enabled", False)),
        timeout_sec=min(int(settings.get("codex_timeout_sec", 1800) or 1800), 900),
        capture_git_diff=False,
        dangerously_bypass_approvals_and_sandbox=bool(
            settings.get("codex_dangerously_bypass_approvals_and_sandbox", False)
        ),
    )
    try:
        task = create_codex_run_task(
            run_request,
            parent_report_job_id=report_job_id,
            parent_report_id=report_id,
            parent_stage_id="r_workflow_sidecar",
            stage_id="r_workflow_sidecar",
            purpose="r_workflow_sidecar_review",
            artifact_source="codex_sidecar_review.md",
            return_full=True,
        )
        snapshot = get_codex_run_task(str(task.get("job_id") or ""))
    except Exception as exc:
        return _sync_fallback(f"task_mode_failed:{exc}")

    local_downloadables = _workflow_sidecar_local_downloadables(workflow_dir)
    downloadables = list(local_downloadables)
    task_id = str(snapshot.get("job_id") or task.get("job_id") or "")
    run_id = str(snapshot.get("run_id") or task.get("run_id") or "")
    result_summary = snapshot.get("result_summary") if isinstance(snapshot.get("result_summary"), dict) else {}
    if str(snapshot.get("status") or "").strip().lower() in {"failed", "cancelled", "timed_out"}:
        return _sync_fallback(f"task_mode_terminal:{snapshot.get('status')}")

    seen_names = {str(item.get("name") or "") for item in downloadables}
    for item in local_downloadables:
        if str(item.get("name") or "") not in seen_names:
            downloadables.append(item)

    return {
        "enabled": True,
        "status": str(snapshot.get("status") or task.get("status") or "queued"),
        "reason": "",
        "task_id": task_id,
        "run_id": run_id,
        "session_id": str(result_summary.get("session_id") or ""),
        "summary": str(result_summary.get("summary") or ""),
        "changed_files": list(result_summary.get("changed_files") or []),
        "transcript_entry_count": 0,
        "downloadables": downloadables,
        "error": str(snapshot.get("error") or ""),
    }


def run_r_workflow(
    *,
    report_dir: Path,
    report_id: str,
    report_job_id: str = "",
    dataset_name: str,
    sheet_name: str,
    frame: pd.DataFrame,
    request: SmartReportRequest,
    report_lens: str,
) -> dict[str, Any]:
    runtime_path = _resolve_rscript_path()
    if not runtime_path:
        raise RuntimeError("已勾选 R 工作流，但当前未找到 Rscript。请先在运行时配置里填写 Rscript Path。")

    workflow_dir = report_dir / "r-workflow"
    workflow_dir.mkdir(parents=True, exist_ok=True)
    input_path = workflow_dir / "input-data.csv"
    _csv_ready_frame(frame).to_csv(input_path, index=False, encoding="utf-8-sig")

    clean_script_path = workflow_dir / "01_clean_prepare.R"
    analysis_script_path = workflow_dir / "02_analysis_visualize.R"
    run_script_path = workflow_dir / "run_r_workflow.R"

    heuristic_registry = _build_r_workflow_column_registry(frame)
    ai_semantic_registry = codex_infer_r_workflow_semantics(
        {
            "dataset_name": dataset_name,
            "sheet_name": sheet_name,
            "report_lens": report_lens,
            "user_requirement": request.user_requirement,
            "problem_to_solve": request.problem_to_solve,
            "target_audience": request.target_audience,
            "core_purpose": request.core_purpose,
            "expected_result": request.expected_result,
            "visual_style": request.visual_style_text,
            "chart_palette_preset": request.chart_palette_preset,
            "chart_palette_colors": request.chart_palette_colors,
            "columns": frame.columns.astype(str).tolist()[:80],
            "sample_rows": _csv_ready_frame(frame).head(12).to_dict(orient="records"),
            "heuristic_registry": heuristic_registry,
        }
    )
    column_role_registry = _merge_r_workflow_semantic_registry(
        heuristic_registry,
        ai_semantic_registry,
        frame.columns.astype(str).tolist(),
    )
    temporal_columns = list(column_role_registry.get("temporal_columns") or [])
    r_workflow_context = {
        "dataset_name": dataset_name,
        "sheet_name": sheet_name,
        "report_lens": report_lens,
        "user_requirement": request.user_requirement,
        "problem_to_solve": request.problem_to_solve,
        "target_audience": request.target_audience,
        "core_purpose": request.core_purpose,
        "expected_result": request.expected_result,
        "visual_style": request.visual_style_text,
        "chart_palette_preset": request.chart_palette_preset,
        "chart_palette_colors": request.chart_palette_colors,
        "columns": frame.columns.astype(str).tolist()[:40],
        "numeric_columns": list(column_role_registry.get("numeric_method_columns") or [])[:20],
        "categorical_columns": list(column_role_registry.get("category_dimension_columns") or [])[:20],
        "object_columns": list(column_role_registry.get("object_dimension_columns") or [])[:20],
        "temporal_columns": temporal_columns[:12],
        "column_role_registry": column_role_registry,
        "sample_rows": _csv_ready_frame(frame).head(8).to_dict(orient="records"),
    }
    r_agent_layer = codex_generate_r_workflow(r_workflow_context)
    _write_text(clean_script_path, _patch_r_csv_encoding(str(r_agent_layer.get("clean_script") or "")))
    _write_text(analysis_script_path, _patch_r_csv_encoding(str(r_agent_layer.get("analysis_script") or "")))
    _write_text(
        run_script_path,
        "\n".join(
            [
                "args <- commandArgs(trailingOnly = TRUE)",
                'input_path <- args[1]',
                'workflow_dir <- args[2]',
                f'system2("{runtime_path.replace("\\\\", "/")}", c("{clean_script_path.name}", input_path, workflow_dir))',
                f'system2("{runtime_path.replace("\\\\", "/")}", c("{analysis_script_path.name}", workflow_dir))',
                "",
            ]
        ),
    )

    _run_rscript(runtime_path, clean_script_path, [str(input_path), str(workflow_dir)], workflow_dir, log_prefix="01_clean_prepare")
    try:
        _run_rscript(runtime_path, analysis_script_path, [str(workflow_dir)], workflow_dir, log_prefix="02_analysis_visualize")
    except RuntimeError as exc:
        if not _looks_like_pca_cluster_runtime_failure(str(exc)):
            raise
        safe_layer = _fallback_r_workflow_author_v2("runtime_recovery_after_pca_cluster_failure", r_workflow_context)
        _write_text(clean_script_path, _patch_r_csv_encoding(str(safe_layer.get("clean_script") or "")))
        _write_text(analysis_script_path, _patch_r_csv_encoding(str(safe_layer.get("analysis_script") or "")))
        _run_rscript(runtime_path, clean_script_path, [str(input_path), str(workflow_dir)], workflow_dir, log_prefix="01_clean_prepare")
        _run_rscript(runtime_path, analysis_script_path, [str(workflow_dir)], workflow_dir, log_prefix="02_analysis_visualize")
    _write_inferential_statistics_artifacts(
        workflow_dir=workflow_dir,
        frame=frame,
        column_role_registry=column_role_registry,
    )
    _write_generic_statistical_enhancement_artifacts(
        workflow_dir=workflow_dir,
        frame=frame,
        column_role_registry=column_role_registry,
    )
    _write_generic_visualization_artifacts(
        workflow_dir=workflow_dir,
        frame=frame,
        column_role_registry=column_role_registry,
        request=request,
    )
    _write_questionnaire_visualization_artifacts(
        workflow_dir=workflow_dir,
        frame=frame,
        column_role_registry=column_role_registry,
    )
    statistics_workbook_path = _write_r_workflow_statistics_workbook(
        workflow_dir=workflow_dir,
        report_id=report_id,
        dataset_name=dataset_name,
        sheet_name=sheet_name,
        runtime_path=runtime_path,
        column_role_registry=column_role_registry,
    )

    interpretation_md = workflow_dir / f"{report_id}-r-interpretation.md"
    interpretation_html = workflow_dir / f"{report_id}-r-interpretation.html"
    interpretation_pdf = workflow_dir / f"{report_id}-r-interpretation.pdf"
    relative_dir = workflow_dir.relative_to(REPORTS_DIR.parent).as_posix()

    downloadables = [
        {
            "name": interpretation_pdf.name,
            "path": f"/storage/{relative_dir}/{interpretation_pdf.name}",
            "file_path": str(interpretation_pdf.resolve()),
            "purpose": "R 工作流业务解读 PDF。",
            "is_main": True,
            "type": "pdf",
        },
        {
            "name": clean_script_path.name,
            "path": f"/storage/{relative_dir}/{clean_script_path.name}",
            "file_path": str(clean_script_path.resolve()),
            "purpose": "R 清洗脚本。",
            "is_main": False,
            "type": "r",
        },
        {
            "name": analysis_script_path.name,
            "path": f"/storage/{relative_dir}/{analysis_script_path.name}",
            "file_path": str(analysis_script_path.resolve()),
            "purpose": "R 分析与可视化脚本。",
            "is_main": False,
            "type": "r",
        },
        {
            "name": run_script_path.name,
            "path": f"/storage/{relative_dir}/{run_script_path.name}",
            "file_path": str(run_script_path.resolve()),
            "purpose": "R 一键执行入口。",
            "is_main": False,
            "type": "r",
        },
        {
            "name": input_path.name,
            "path": f"/storage/{relative_dir}/{input_path.name}",
            "file_path": str(input_path.resolve()),
            "purpose": "R 工作流输入数据抽取。",
            "is_main": False,
            "type": "csv",
        },
        {
            "name": interpretation_md.name,
            "path": f"/storage/{relative_dir}/{interpretation_md.name}",
            "file_path": str(interpretation_md.resolve()),
            "purpose": "R 工作流解读 Markdown。",
            "is_main": False,
            "type": "md",
        },
        {
            "name": interpretation_html.name,
            "path": f"/storage/{relative_dir}/{interpretation_html.name}",
            "file_path": str(interpretation_html.resolve()),
            "purpose": "R 工作流解读 HTML。",
            "is_main": False,
            "type": "html",
        },
        {
            "name": statistics_workbook_path.name,
            "path": f"/storage/{relative_dir}/{statistics_workbook_path.name}",
            "file_path": str(statistics_workbook_path.resolve()),
            "purpose": "R 工作流统计结果 Excel 总表。",
            "is_main": False,
            "type": "xlsx",
        },
    ]

    for filename, spec in R_WORKFLOW_OUTPUT_SPECS.items():
        path = workflow_dir / filename
        if not path.exists():
            continue
        downloadables.append(
            {
                "name": path.name,
                "path": f"/storage/{relative_dir}/{path.name}",
                "file_path": str(path.resolve()),
                "purpose": str(spec.get("purpose") or ""),
                "is_main": False,
                "type": str(spec.get("type") or path.suffix.lstrip(".").lower()),
            }
        )

    summary_rows = _read_csv_rows(workflow_dir / "summary_stats.csv")
    category_rows = _read_csv_rows(workflow_dir / "top_categories.csv")
    temporal_rows = _read_csv_rows(workflow_dir / "temporal_trend.csv")
    method_rows = _read_csv_rows_full(workflow_dir / "method_log.csv")
    correlation_rows = _read_csv_rows(workflow_dir / "correlation_matrix.csv")
    pca_axis_rows = _read_csv_rows(workflow_dir / "pca_axis_summary.csv")
    cluster_member_rows = _read_csv_rows(workflow_dir / "cluster_member_detail.csv")

    interpretation_layer = codex_interpret_r_results(
        {
            "dataset_name": dataset_name,
            "sheet_name": sheet_name,
            "report_lens": report_lens,
            "user_requirement": request.user_requirement,
            "problem_to_solve": request.problem_to_solve,
            "target_audience": request.target_audience,
            "core_purpose": request.core_purpose,
            "summary_rows": summary_rows[:8],
            "category_rows": category_rows[:8],
            "temporal_rows": temporal_rows[:8],
            "method_rows": method_rows[:40],
            "correlation_rows": correlation_rows[:8],
            "pca_axis_rows": pca_axis_rows[:8],
            "cluster_member_rows": cluster_member_rows[:8],
        }
    )
    interpretation_summary = [
        str(item).strip()
        for item in (interpretation_layer.get("interpretation_summary") or [])
        if str(item).strip()
    ]
    output_rows = _build_output_inventory_rows(downloadables)
    interpretation_sections = _build_business_interpretation_sections(interpretation_layer)
    method_cards = _build_method_analysis_cards(workflow_dir, method_rows)
    csv_sections = _build_csv_sections(workflow_dir)
    code_sections = _build_code_sections(workflow_dir)
    chart_notes = _build_chart_interpretation_map(csv_sections=csv_sections, interpretation_layer=interpretation_layer)
    image_sections = _build_image_sections(workflow_dir, chart_notes)
    log_sections = _build_log_sections(workflow_dir)

    markdown_text = _build_interpretation_markdown(
        dataset_name=dataset_name,
        sheet_name=sheet_name,
        request=request,
        runtime_path=runtime_path,
        interpretation_summary=interpretation_summary,
        interpretation_sections=interpretation_sections,
        method_cards=method_cards,
        output_rows=output_rows,
        csv_sections=csv_sections,
        code_sections=code_sections,
        image_sections=image_sections,
        log_sections=log_sections,
    )
    _write_text(interpretation_md, markdown_text)
    _write_interpretation_html(
        dataset_name=dataset_name,
        sheet_name=sheet_name,
        runtime_path=runtime_path,
        purpose_text=_safe_r_workflow_purpose_text(
            request.core_purpose,
            request.problem_to_solve,
            request.user_requirement,
        ),
        interpretation_summary=interpretation_summary,
        interpretation_sections=interpretation_sections,
        method_cards=method_cards,
        output_rows=output_rows,
        csv_sections=csv_sections,
        code_sections=code_sections,
        image_sections=image_sections,
        log_sections=log_sections,
        html_path=interpretation_html,
    )
    _write_interpretation_pdf(
        dataset_name=dataset_name,
        sheet_name=sheet_name,
        runtime_path=runtime_path,
        purpose_text=_safe_r_workflow_purpose_text(
            request.core_purpose,
            request.problem_to_solve,
            request.user_requirement,
        ),
        interpretation_summary=interpretation_summary,
        interpretation_sections=interpretation_sections,
        method_cards=method_cards,
        output_rows=output_rows,
        csv_sections=csv_sections,
        code_sections=code_sections,
        image_sections=image_sections,
        log_sections=log_sections,
        pdf_path=interpretation_pdf,
    )

    codex_sidecar = _run_r_workflow_codex_sidecar(
        workflow_dir=workflow_dir,
        report_id=report_id,
        report_job_id=report_job_id,
        dataset_name=dataset_name,
        sheet_name=sheet_name,
        report_lens=report_lens,
        request=request,
        interpretation_summary=interpretation_summary,
        column_role_registry=column_role_registry,
    )
    if codex_sidecar.get("downloadables"):
        seen_names = {str(item.get("name") or "") for item in downloadables}
        for item in codex_sidecar.get("downloadables", []):
            name = str(item.get("name") or "")
            if name and name not in seen_names:
                downloadables.append(item)
                seen_names.add(name)

    return {
        "enabled": True,
        "status": "completed",
        "runtime_available": True,
        "runtime_path": runtime_path,
        "workflow_dir": str(workflow_dir.resolve()),
        "interpretation_summary": interpretation_summary,
        "codex_sidecar": codex_sidecar,
        "downloadables": downloadables,
    }
