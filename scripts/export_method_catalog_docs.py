"""Export the public Chinese method catalog from Asteria's backend registries.

Run from the repository root:
    backend\\.venv\\Scripts\\python.exe scripts\\export_method_catalog_docs.py
"""

from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
DOCS_DIR = ROOT / "docs"

sys.path.insert(0, str(BACKEND_DIR))

from app.services.auto_analysis_registry_service import (  # noqa: E402
    METHOD_LABELS,
    auto_analysis_method_catalog,
)
from app.services.statistical_catalog import get_catalog_summary, get_statistical_catalog  # noqa: E402


FAMILY_LABELS = {
    "association": "关联分析",
    "categorical_association": "分类关联",
    "causal": "因果探查",
    "causal_panel": "面板因果",
    "comparison": "差异比较",
    "descriptive": "描述统计",
    "distribution_assumption": "分布假设",
    "experimentation": "实验分析",
    "machine_learning": "机器学习",
    "mean_tests": "均值检验",
    "multivariate": "多变量分析",
    "nonparametric": "非参数检验",
    "psychometrics": "心理测量",
    "regression_glm": "广义线性模型",
    "report_part": "报告部件",
    "statistical": "统计推断与稳健性",
    "survival": "生存分析",
    "time_series": "时间序列",
}

ROLE_LABELS = {
    "binary": "二元字段",
    "binary_group": "二元分组",
    "categorical": "分类字段",
    "categorical_pair": "两个分类字段",
    "count": "计数字段",
    "covariate": "协变量",
    "effect_size": "效应量",
    "event_type": "事件类型",
    "features": "特征字段",
    "group": "分组字段",
    "grouped": "分组结构",
    "grouped_numeric": "分组数值结构",
    "multi_categorical": "多分类字段",
    "multi_class": "多分类目标",
    "multi_item_scale": "多题项量表",
    "multi_numeric": "多个数值字段",
    "numeric": "数值字段",
    "numeric_or_binary": "数值或二元目标",
    "numeric_or_categorical": "数值或分类字段",
    "ordered": "有序字段",
    "ordered_category": "有序分类目标",
    "outcome": "结果字段",
    "paired": "配对标识",
    "panel": "面板标识",
    "positive_numeric": "正值数值字段",
    "proportion": "比例字段",
    "strata": "分层字段",
    "target": "目标字段",
    "time": "时间字段",
    "time_to_event": "生存时长",
    "within_subject_factor": "受试内因子",
    "x": "自变量",
    "y": "因变量",
    "m": "中介变量",
    "moderator": "调节变量",
    "latent": "潜变量",
    "repeated_measure": "重复测量结构",
    "multi_group_scale": "多组量表",
}

STATUS_LABELS = {
    "live": "可运行",
    "catalog": "目录条目",
    "planned": "规划条目",
}

STATISTICAL_METHOD_NAME_ZH = {
    "descriptive_summary": "描述性统计摘要",
    "frequency_table": "频数表",
    "cross_tabulation": "交叉列联表",
    "pivot_summary": "透视汇总",
    "quantile_profile": "分位数画像",
    "trimmed_mean": "截尾均值",
    "winsorized_summary": "缩尾统计摘要",
    "gini_coefficient": "基尼系数",
    "lorenz_curve": "洛伦兹曲线",
    "pareto_analysis": "帕累托分析",
    "cohort_summary": "队列汇总",
    "segmented_kpi_breakdown": "分层关键指标拆解",
    "normality": "正态性检验",
    "shapiro_wilk": "夏皮罗-威尔克检验",
    "dagostino_k2": "达戈斯蒂诺 K 平方检验",
    "jarque_bera": "雅克-贝拉检验",
    "kolmogorov_smirnov_1samp": "单样本柯尔莫哥洛夫-斯米尔诺夫检验",
    "anderson_darling": "安德森-达林检验",
    "levene": "列文方差齐性检验",
    "bartlett": "巴特利特方差齐性检验",
    "brown_forsythe": "布朗-福赛斯方差齐性检验",
    "breusch_pagan": "布鲁施-帕甘异方差检验",
    "white_test": "怀特异方差检验",
    "durbin_watson": "德宾-沃森残差自相关检验",
    "ttest": "韦尔奇双样本 T 检验",
    "paired_ttest": "配对样本 T 检验",
    "one_sample_ttest": "单样本 T 检验",
    "z_test_mean": "均值 Z 检验",
    "anova": "单因素方差分析",
    "welch_anova": "韦尔奇方差分析",
    "two_way_anova": "双因素方差分析",
    "repeated_measures_anova": "重复测量方差分析",
    "ancova": "协方差分析",
    "manova": "多元方差分析",
    "hotelling_t2": "霍特林 T 平方检验",
    "equivalence_test_tost": "双单侧等效性检验",
    "tukey_hsd": "图基显著性差异事后检验",
    "mann_whitney": "曼-惠特尼 U 检验",
    "wilcoxon_signed_rank": "威尔科克森符号秩检验",
    "sign_test": "符号检验",
    "kruskal": "克鲁斯卡尔-沃利斯检验",
    "friedman": "弗里德曼检验",
    "mood_median": "穆德中位数检验",
    "ks_two_sample": "双样本柯尔莫哥洛夫-斯米尔诺夫检验",
    "runs_test": "游程检验",
    "median_test": "中位数检验",
    "fligner_killeen": "弗林纳-基林方差齐性检验",
    "permutation_test": "置换检验",
    "bootstrap_ci": "自助法置信区间",
    "chi_square": "卡方检验",
    "fisher_exact": "费舍尔精确检验",
    "mcnemar": "麦克内马尔检验",
    "cochran_q": "科克伦 Q 检验",
    "cmh_test": "科克伦-曼特尔-亨泽尔检验",
    "cramers_v": "克拉默 V 关联系数",
    "phi_coefficient": "菲系数",
    "theils_u": "泰尔 U 关联系数",
    "goodman_kruskal_lambda": "古德曼-克鲁斯卡尔拉姆达系数",
    "cohens_kappa": "科恩卡帕系数",
    "pearson_correlation": "皮尔逊相关分析",
    "correlation": "相关矩阵分析",
    "spearman_correlation": "斯皮尔曼秩相关分析",
    "kendall_tau": "肯德尔秩相关系数",
    "partial_correlation": "偏相关分析",
    "distance_correlation": "距离相关分析",
    "point_biserial": "点二列相关分析",
    "eta_squared": "Eta 平方效应量",
    "intraclass_correlation": "组内相关系数",
    "canonical_correlation": "典型相关分析",
    "mutual_information": "互信息分析",
    "ols": "普通最小二乘回归",
    "ridge_regression": "岭回归",
    "lasso_regression": "套索回归",
    "elastic_net": "弹性网络回归",
    "logit": "逻辑回归",
    "random_forest": "随机森林",
    "neural_network": "神经网络",
    "deep_learning": "深度学习网络",
    "probit_regression": "概率单位回归",
    "multinomial_logit": "多项逻辑回归",
    "ordinal_logit": "有序逻辑回归",
    "poisson_glm": "泊松广义线性模型",
    "negative_binomial": "负二项回归",
    "gamma_glm": "伽马广义线性模型",
    "beta_regression": "贝塔回归",
    "quantile_regression": "分位数回归",
    "robust_regression": "稳健回归",
    "glm_binomial": "二项广义线性模型",
    "zero_inflated_poisson": "零膨胀泊松模型",
    "pca": "主成分分析",
    "factor_analysis": "因子分析",
    "confirmatory_factor_analysis": "验证性因子分析",
    "ica": "独立成分分析",
    "kmeans": "K 均值聚类",
    "hierarchical_clustering": "层次聚类",
    "dbscan": "基于密度的空间聚类",
    "gaussian_mixture": "高斯混合模型",
    "latent_class_analysis": "潜在类别分析",
    "discriminant_analysis_lda": "线性判别分析",
    "discriminant_analysis_qda": "二次判别分析",
    "correspondence_analysis": "对应分析",
    "moving_average": "移动平均",
    "seasonal_decomposition": "季节性分解",
    "autocorrelation": "自相关分析",
    "partial_autocorrelation": "偏自相关分析",
    "ljung_box": "隆-博克斯白噪声检验",
    "adf_test": "扩展迪基-富勒平稳性检验",
    "kpss_test": "KPSS 平稳性检验",
    "granger_causality": "格兰杰因果检验",
    "arima": "自回归积分滑动平均模型",
    "sarima": "季节性自回归积分滑动平均模型",
    "holt_winters": "霍尔特-温特斯指数平滑",
    "prophet_style_trend": "Prophet 风格趋势模型",
    "ab_test": "A/B 实验检验",
    "sample_size_power": "样本量与统计功效分析",
    "sequential_test": "序贯检验",
    "bayesian_ab_test": "贝叶斯 A/B 实验",
    "uplift_modeling": "增量效应建模",
    "did": "双重差分法",
    "synthetic_control": "合成控制法",
    "interrupted_time_series": "中断时间序列分析",
    "panel_fixed_effects": "面板固定效应模型",
    "panel_random_effects": "面板随机效应模型",
    "mixed_effects_model": "混合效应模型",
    "gee": "广义估计方程",
    "kaplan_meier": "卡普兰-迈耶生存估计",
    "log_rank_test": "对数秩生存曲线检验",
    "cox_ph": "Cox 比例风险模型",
    "accelerated_failure_time": "加速失效时间模型",
    "competing_risks": "竞争风险模型",
    "nelson_aalen": "纳尔逊-阿伦累积风险估计",
    "reliability_cronbach_alpha": "克朗巴赫阿尔法信度",
    "split_half_reliability": "折半信度",
    "item_response_theory": "项目反应理论",
    "sem": "结构方程模型",
    "mediation_analysis": "中介效应分析",
    "moderation_analysis": "调节效应分析",
    "latent_growth_model": "潜在增长模型",
    "measurement_invariance": "测量等值性检验",
    "missingness_mechanism_diagnostic": "缺失机制诊断",
    "missingness_heatmap_audit": "缺失值热力审计",
    "imputation_strategy_plan": "缺失值填补策略规划",
    "outlier_screening_iqr": "四分位距异常值筛查",
    "robust_zscore_outlier": "稳健 Z 分数异常值筛查",
    "duplicate_record_audit": "重复记录审计",
    "data_type_validation": "数据类型校验",
    "measurement_error_audit": "测量误差审计",
    "sampling_bias_audit": "抽样偏差审计",
    "data_leakage_audit": "数据泄漏审计",
    "cohens_d_effect_size": "科恩 d 效应量",
    "hedges_g_effect_size": "赫奇斯 g 效应量",
    "glass_delta_effect_size": "格拉斯 Delta 效应量",
    "cliffs_delta_effect_size": "克利夫 Delta 效应量",
    "rank_biserial_correlation": "秩二列相关系数",
    "odds_ratio": "优势比",
    "relative_risk": "相对风险",
    "risk_difference": "风险差",
    "number_needed_to_treat": "需治疗人数",
    "confidence_interval_summary": "置信区间摘要",
    "multiple_testing_correction": "多重检验校正",
    "false_discovery_rate": "错误发现率控制",
    "bayesian_interval_summary": "贝叶斯区间摘要",
    "mauchly_sphericity": "莫赫利球形性检验",
    "box_m_test": "Box M 协方差矩阵检验",
    "vif_multicollinearity": "方差膨胀因子共线性诊断",
    "influence_diagnostics": "影响点诊断",
    "cooks_distance": "库克距离",
    "residual_diagnostic_panel": "残差诊断面板",
    "aic_bic_model_selection": "AIC/BIC 模型选择",
    "stepwise_model_comparison": "逐步模型比较",
    "cross_validated_regression": "交叉验证回归",
    "train_test_split_audit": "训练集与测试集切分审计",
    "cross_validation": "交叉验证",
    "nested_cross_validation": "嵌套交叉验证",
    "learning_curve": "学习曲线分析",
    "roc_auc_analysis": "ROC-AUC 分析",
    "precision_recall_analysis": "精确率-召回率分析",
    "confusion_matrix_review": "混淆矩阵评审",
    "threshold_optimization": "决策阈值优化",
    "model_calibration": "模型校准",
    "permutation_importance_review": "置换重要性评审",
    "shap_explanation": "SHAP 模型解释",
    "fairness_slice_audit": "公平性切片审计",
    "silhouette_analysis": "轮廓系数分析",
    "elbow_method": "肘部法则",
    "cluster_stability": "聚类稳定性分析",
    "umap_projection": "UMAP 降维投影",
    "tsne_projection": "t-SNE 降维投影",
    "dag_assumption_review": "因果图假设评审",
    "propensity_score_matching": "倾向得分匹配",
    "inverse_probability_weighting": "逆概率加权",
    "doubly_robust_estimation": "双重稳健估计",
    "instrumental_variables": "工具变量法",
    "regression_discontinuity": "回归不连续设计",
    "placebo_test": "安慰剂检验",
    "unobserved_confounding_sensitivity": "未观测混杂敏感性分析",
    "rolling_correlation": "滚动相关分析",
    "cross_correlation_lag": "交叉相关滞后分析",
    "stl_decomposition": "STL 季节趋势分解",
    "forecast_backtesting": "预测回测",
    "forecast_residual_diagnostics": "预测残差诊断",
    "dynamic_regression": "动态回归",
    "sample_ratio_mismatch": "样本比例失配检验",
    "experiment_guardrail_metrics": "实验护栏指标",
    "peeking_risk_audit": "实验提前窥视风险审计",
    "cuped_adjustment": "CUPED 协变量调整",
    "stratified_randomization": "分层随机化",
    "factorial_experiment": "析因实验",
    "multi_arm_bandit": "多臂老虎机策略",
    "stratified_sampling_design": "分层抽样设计",
    "cluster_sampling_design": "整群抽样设计",
    "survey_design_effect": "调查设计效应",
    "post_stratification_weighting": "后分层加权",
    "raking_weighting": "迭代比例拟合加权",
    "nonresponse_bias_analysis": "无应答偏差分析",
    "margin_of_error": "误差范围",
    "finite_population_correction": "有限总体校正",
    "power_curve_analysis": "统计功效曲线分析",
    "minimum_detectable_effect": "最小可检测效应",
    "metric_sensitivity_analysis": "指标敏感性分析",
    "north_star_metric_audit": "北极星指标审计",
    "metric_definition_drift": "指标定义漂移",
    "denominator_integrity_check": "分母完整性检查",
    "ratio_metric_delta_method": "比率指标 Delta 法",
    "bucketed_ratio_metric": "分桶比率指标",
    "zero_inflation_diagnostic": "零膨胀诊断",
    "overdispersion_diagnostic": "过度离散诊断",
    "skewness_kurtosis_profile": "偏度与峰度画像",
    "qq_diagnostic_review": "Q-Q 图诊断评审",
    "boxcox_transformation": "Box-Cox 变换",
    "yeo_johnson_transformation": "Yeo-Johnson 变换",
    "standardization_scaling": "标准化与缩放",
    "winsorization_strategy": "缩尾处理策略",
    "feature_binning_strategy": "特征分箱策略",
    "target_encoding_audit": "目标编码审计",
    "one_hot_encoding_plan": "独热编码规划",
    "rare_category_consolidation": "稀有类别合并",
    "high_cardinality_profile": "高基数特征画像",
    "interaction_feature_screen": "交互特征筛选",
    "spline_regression": "样条回归",
    "generalized_additive_model": "广义加性模型",
    "piecewise_regression": "分段回归",
    "mixed_effects_random_intercepts": "混合效应随机截距模型",
    "mixed_effects_random_slopes": "混合效应随机斜率模型",
    "cluster_robust_standard_errors": "聚类稳健标准误",
    "heteroskedasticity_robust_se": "异方差稳健标准误",
    "newey_west_standard_errors": "纽维-韦斯特标准误",
    "model_specification_curve": "模型设定曲线分析",
    "robustness_grid": "稳健性网格分析",
    "sensitivity_to_outliers": "异常值敏感性分析",
    "sensitivity_to_missing_data": "缺失数据敏感性分析",
    "negative_control_outcome": "负向对照结果",
    "negative_control_exposure": "负向对照暴露",
    "event_study_design": "事件研究设计",
    "parallel_trends_diagnostic": "平行趋势诊断",
    "spillover_interference_audit": "溢出与干扰审计",
    "attrition_analysis": "样本流失分析",
    "carryover_effect_check": "残留效应检查",
    "switchback_experiment_design": "交替实验设计",
    "geo_experiment_design": "地理实验设计",
    "synthetic_difference_in_differences": "合成双重差分法",
    "double_machine_learning": "双重机器学习",
    "causal_forest": "因果森林",
    "heterogeneous_treatment_effects": "异质性处理效应",
    "survival_censoring_audit": "生存删失审计",
    "proportional_hazards_check": "比例风险假设检验",
    "time_dependent_covariates": "时变协变量",
    "cumulative_incidence_curve": "累积发生率曲线",
    "state_transition_matrix": "状态转移矩阵",
    "markov_chain_analysis": "马尔可夫链分析",
    "hidden_markov_model": "隐马尔可夫模型",
    "anomaly_detection_isolation_forest": "孤立森林异常检测",
    "anomaly_detection_local_outlier_factor": "局部离群因子异常检测",
    "population_stability_index": "总体稳定性指数",
    "concept_drift_detection": "概念漂移检测",
    "data_drift_dashboard": "数据漂移仪表盘",
    "prediction_interval": "预测区间",
    "quantile_forecast": "分位数预测",
    "conformal_prediction": "保序预测",
    "model_card_documentation": "模型卡文档",
    "datasheet_for_dataset": "数据集说明书",
    "reproducibility_audit": "可复现性审计",
    "analysis_lineage_map": "分析血缘图谱",
    "bayesian_prior_predictive_check": "贝叶斯先验预测检验",
    "bayesian_posterior_predictive_check": "贝叶斯后验预测检验",
    "bayesian_hierarchical_model": "贝叶斯层级模型",
    "bayesian_credible_effect": "贝叶斯可信效应",
    "bayes_factor_model_comparison": "贝叶斯因子模型比较",
    "empirical_bayes_shrinkage": "经验贝叶斯收缩",
    "small_area_estimation": "小域估计",
    "multilevel_poststratification": "多层回归与后分层",
    "sequential_bayesian_monitoring": "序贯贝叶斯监测",
    "bayesian_bandit_policy": "贝叶斯老虎机策略",
    "text_token_frequency": "文本词元频率分析",
    "tfidf_feature_profile": "TF-IDF 特征画像",
    "topic_model_lda": "LDA 主题模型",
    "bertopic_clustering": "BERTopic 主题聚类",
    "text_embedding_similarity": "文本嵌入相似度分析",
    "sentiment_classifier_audit": "情感分类器审计",
    "keyword_in_context_review": "关键词上下文评审",
    "named_entity_extraction_profile": "命名实体提取画像",
    "text_label_quality_audit": "文本标注质量审计",
    "semantic_deduplication": "语义去重",
    "network_degree_centrality": "网络度中心性",
    "network_betweenness_centrality": "网络介数中心性",
    "network_pagerank": "网络 PageRank 分析",
    "community_detection_louvain": "Louvain 社区发现",
    "bipartite_network_projection": "二部网络投影",
    "cooccurrence_network_analysis": "共现网络分析",
    "network_assortativity": "网络同配性",
    "link_prediction_baseline": "链接预测基线",
    "ego_network_profile": "自我中心网络画像",
    "graph_anomaly_detection": "图异常检测",
    "spatial_join_audit": "空间连接审计",
    "moran_i_spatial_autocorrelation": "莫兰 I 空间自相关",
    "getis_ord_hotspot": "Getis-Ord 热点分析",
    "spatial_lag_model": "空间滞后模型",
    "spatial_error_model": "空间误差模型",
    "geographically_weighted_regression": "地理加权回归",
    "spatiotemporal_cluster_detection": "时空聚类检测",
    "areal_interpolation": "区域插值",
    "nearest_neighbor_spatial_search": "最近邻空间搜索",
    "geohash_grid_aggregation": "地理哈希网格汇总",
    "privacy_k_anonymity": "K 匿名隐私检查",
    "privacy_l_diversity": "L 多样性隐私检查",
    "differential_privacy_budget": "差分隐私预算",
    "synthetic_data_quality_audit": "合成数据质量审计",
    "pii_detection_profile": "个人敏感信息检测画像",
    "data_minimization_audit": "数据最小化审计",
    "consent_coverage_audit": "同意范围审计",
    "retention_policy_audit": "数据保留策略审计",
    "feature_privacy_risk_rank": "特征隐私风险排序",
    "fairness_proxy_variable_audit": "公平性代理变量审计",
    "data_contract_validation": "数据契约校验",
    "schema_drift_detection": "模式漂移检测",
    "freshness_sla_monitor": "数据新鲜度服务等级监控",
    "completeness_sla_monitor": "数据完整性服务等级监控",
    "uniqueness_constraint_check": "唯一性约束检查",
    "referential_integrity_check": "引用完整性检查",
    "range_constraint_validation": "范围约束校验",
    "business_rule_validation": "业务规则校验",
    "data_quality_scorecard": "数据质量评分卡",
    "root_cause_data_quality": "数据质量根因分析",
    "metric_anomaly_root_cause": "指标异常根因分析",
    "alert_threshold_backtest": "告警阈值回测",
    "seasonal_baseline_anomaly": "季节性基线异常检测",
    "control_chart_rule_set": "控制图规则集",
    "multivariate_control_chart": "多变量控制图",
    "model_performance_monitor": "模型性能监控",
    "model_retraining_trigger": "模型再训练触发器",
    "champion_challenger_evaluation": "冠军-挑战者模型评估",
    "online_offline_metric_gap": "线上线下指标差距分析",
    "cost_sensitive_evaluation": "成本敏感评估",
    "uplift_evaluation_qini": "Qini 增量评估",
    "incrementality_holdout": "增量效果留出组评估",
    "longitudinal_cohort_retention": "纵向队列留存分析",
    "funnel_step_conversion": "漏斗步骤转化分析",
    "path_sequence_mining": "路径序列挖掘",
    "survival_retention_model": "生存留存模型",
    "competing_event_retention": "竞争事件留存分析",
    "multi_state_survival_model": "多状态生存模型",
    "explainable_dashboard_narrative": "可解释仪表盘叙述",
}

FAMILY_ORDER = [
    "descriptive",
    "distribution_assumption",
    "mean_tests",
    "nonparametric",
    "categorical_association",
    "association",
    "regression_glm",
    "machine_learning",
    "multivariate",
    "time_series",
    "experimentation",
    "causal",
    "causal_panel",
    "survival",
    "psychometrics",
    "statistical",
    "comparison",
    "report_part",
]


def escape_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ").strip()


def role_labels(roles: list[str]) -> str:
    return "、".join(ROLE_LABELS.get(role, role.replace("_", " ")) for role in roles)


def family_label(family: str) -> str:
    return FAMILY_LABELS.get(family, family.replace("_", " "))


def status_label(status: str) -> str:
    return STATUS_LABELS.get(status, status)


LAB_FAMILY_LABELS = {
    **FAMILY_LABELS,
    "visual": "可视化分析",
    "financial_visual": "金融可视化",
    "quality": "数据质量",
    "privacy": "数据隐私",
    "network": "网络分析",
    "spatial": "空间分析",
    "text": "文本分析",
}

LAB_TOKEN_LABELS = {
    **METHOD_LABELS,
    "ab": "A/B 实验",
    "adf": "单位根",
    "alert": "告警",
    "anomaly": "异常",
    "analysis": "分析",
    "audit": "审计",
    "auto": "自动化",
    "backtest": "回测",
    "bandit": "老虎机策略",
    "baseline": "基线",
    "bayes": "贝叶斯",
    "bayesian": "贝叶斯",
    "binning": "分箱",
    "causal": "因果",
    "censoring": "删失",
    "cluster": "聚类",
    "cohort": "队列",
    "completeness": "完整性",
    "confounding": "混杂",
    "control": "控制",
    "conversion": "转化",
    "correlation": "相关性",
    "data": "数据",
    "deduplication": "去重",
    "diagnostic": "诊断",
    "drift": "漂移",
    "effect": "效应",
    "embedding": "嵌入",
    "error": "误差",
    "event": "事件",
    "experiment": "实验",
    "explainable": "可解释",
    "feature": "特征",
    "finance": "金融",
    "forecasting": "预测",
    "funnel": "漏斗",
    "geographic": "地理",
    "graph": "图网络",
    "guardrail": "护栏",
    "health": "健康度",
    "impact": "影响",
    "inference": "推断",
    "integrity": "完整性",
    "kpi": "关键指标",
    "lag": "滞后",
    "lineage": "血缘",
    "machine": "机器",
    "market": "市场",
    "metric": "指标",
    "model": "模型",
    "monitor": "监控",
    "network": "网络",
    "outlier": "离群值",
    "panel": "面板",
    "performance": "性能",
    "privacy": "隐私",
    "quality": "质量",
    "ranking": "排序",
    "regression": "回归",
    "retention": "留存",
    "risk": "风险",
    "sampling": "抽样",
    "score": "评分",
    "series": "序列",
    "spatial": "空间",
    "stat": "统计",
    "statistical": "统计",
    "survival": "生存",
    "text": "文本",
    "time": "时间",
    "topic": "主题",
    "treatment": "处理",
    "validation": "校验",
    "visual": "可视化",
    "weighting": "加权",
}

LAB_OUTPUT_LABELS = {
    "chart": "图表",
    "data": "数据结果",
    "image": "图像",
    "image_spec": "图像规格",
    "json": "JSON 结果",
    "markdown": "Markdown 文档",
    "report_section": "报告章节",
    "svg": "SVG 图形",
    "table": "数据表",
    "text": "文字解读",
    "xlsx": "Excel 工作簿",
}

LAB_SOURCE_LABELS = {
    "statistical_catalog": "统计目录",
    "statistical_visual_catalog": "统计可视化目录",
    "financial_visual_catalog": "金融可视化目录",
    "auto_analysis_specs": "自动分析规格目录",
    "learned_methods": "已学习方法",
}


def has_cjk(value: object) -> bool:
    return any("\u4e00" <= character <= "\u9fff" for character in str(value))


def statistical_name_zh(entry: dict[str, object]) -> str:
    method_id = str(entry["id"])
    try:
        return STATISTICAL_METHOD_NAME_ZH[method_id]
    except KeyError as exc:
        raise ValueError(f"Missing Chinese statistical method name: {method_id}") from exc


def lab_family_label(family: str) -> str:
    if has_cjk(family):
        return family
    return LAB_FAMILY_LABELS.get(family, "分析方法")


def _localized_identifier(value: str) -> str:
    tokens = [token for token in re.split(r"[^a-z0-9]+", value.lower()) if token]
    labels = [LAB_TOKEN_LABELS[token] for token in tokens if token in LAB_TOKEN_LABELS]
    unique_labels = list(dict.fromkeys(labels))
    return "・".join(unique_labels) if unique_labels else "分析方法"


def lab_method_name_zh(entry: dict[str, object]) -> str:
    candidates = [
        str(entry.get("base_method_id") or ""),
        str(entry.get("bundle_id") or ""),
        str(entry.get("parent_method_id") or ""),
        str(entry.get("id") or ""),
    ]
    for candidate in candidates:
        if candidate in STATISTICAL_METHOD_NAME_ZH:
            return STATISTICAL_METHOD_NAME_ZH[candidate]
    family = lab_family_label(str(entry.get("family") or ""))
    concept = str(entry.get("method_concept_label") or "").strip()
    if has_cjk(concept):
        return f"{family}・{concept}"
    details = _localized_identifier(next((item for item in candidates if item), ""))
    return f"{family}・{details}"


def lab_output_label_zh(value: object) -> str:
    output = str(value or "").strip()
    if has_cjk(output):
        return output
    return LAB_OUTPUT_LABELS.get(output.lower(), "分析产物")


def lab_source_label(value: object) -> str:
    source = str(value or "").strip()
    return LAB_SOURCE_LABELS.get(source, "方法目录")


def render_statistics_catalog() -> str:
    methods = get_statistical_catalog()
    summary = get_catalog_summary()
    lab_cards = auto_analysis_method_catalog(compact=True)["methods"]
    live_lab_stat_cards = [
        card
        for card in lab_cards
        if card["status"] == "live" and card["source"] == "statistical_catalog"
    ]
    live_lab_concepts = {
        str(card["base_method_id"])
        for card in live_lab_stat_cards
    }
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for method in methods:
        grouped[str(method["family"])].append(method)

    lines = [
        "# Asteria Analyst 统计方法与 Analysis Lab 目录",
        "",
        "> 本文档由 `scripts/export_method_catalog_docs.py` 从后端注册表生成。变更方法后请重新执行生成器，再提交本文件。",
        "",
        "## 目录范围",
        "",
        f"- 统计方法注册总数：`{summary['total_methods']}`",
        f"- 可运行统计方法：`{summary['live_methods']}`",
        f"- 目录方法：`{summary['catalog_methods']}`",
        (
            "- Analysis Lab 可运行统计方法卡："
            f"`{len(live_lab_stat_cards)}` 张，覆盖 "
            f"`{len(live_lab_concepts)}` 个可运行统计方法概念。"
        ),
        "- 方法数据源：`backend/app/services/statistical_catalog.py`；Lab 卡片注册源：`backend/app/services/auto_analysis_registry_service.py`。",
        "",
        "### 状态说明",
        "",
        "| 状态 | 含义 |",
        "| --- | --- |",
        "| 可运行 | 已连接执行器，可在 Analysis Lab 配置字段并产生运行产物。 |",
        "| 目录条目 | 已登记方法目标与字段契约，用于选型、路线规划与后续执行器接入。 |",
        "| 规划条目 | 已登记在 Lab 方法空间中，用于产品路线与能力编排。 |",
        "",
        "### 字段角色速查",
        "",
        "| 角色 | 使用方式 |",
        "| --- | --- |",
        "| 数值字段 | 金额、次数、评分、时长、连续型指标。 |",
        "| 分类字段 | 地区、渠道、产品线、客户类型等离散分组。 |",
        "| 时间字段 | 日期、周、月、季度或有稳定排序的时间戳。 |",
        "| 目标字段 | 待解释、预测或比较的结果变量。 |",
        "| 特征字段 | 用于解释或预测目标字段的输入变量集合。 |",
        "| 配对标识 / 受试内因子 | 同一对象前后测量、重复测量或匹配样本结构。 |",
        "| 面板标识 / 分层字段 | 个体-时间面板、分层实验或多层数据结构。 |",
        "",
        "## 结果解读与交付",
        "",
        "| 方法族 | 优先查看的结果 | 常见交付判断 |",
        "| --- | --- | --- |",
        "| 描述统计 | 样本量、缺失、均值/中位数、分位数、集中度 | 识别水平、波动、长尾和头部贡献。 |",
        "| 分布假设 | 检验统计量、p 值、残差诊断 | 选择参数检验、稳健方法或变换策略。 |",
        "| 均值与非参数检验 | 组间差异、置信区间、p 值、效应量 | 判断差异方向、大小与业务价值。 |",
        "| 分类关联 | 列联表、期望频数、关联强度 | 判断分类变量是否相关并量化关联强度。 |",
        "| 关联分析 | 相关系数、方向、强度、显著性 | 区分线性、秩相关、偏相关和非线性关联。 |",
        "| 回归与机器学习 | 系数/重要性、拟合优度、误差、诊断 | 解释驱动因素、预测表现与稳定性。 |",
        "| 多变量与聚类 | 方差解释、载荷、簇规模、轮廓线索 | 完成降维、分群或群体结构识别。 |",
        "| 时间序列 | 趋势、季节性、滞后、平稳性、残差 | 判断时间结构并选择预测或监控路线。 |",
        "| 实验、因果与生存 | 处理效应、对照证据、风险率/生存率 | 形成实验决策、因果评估或留存分析结论。 |",
        "",
        "## 使用场景与方法选择",
        "",
        "下表从业务问题出发选择首个分析路径。先确认字段角色、样本结构与方法状态，再在全量注册表中按中文名称或方法 ID 定位具体条目。涉及多个候选方法时，可将结果解读与稳健性条目作为复核路线。",
        "",
        "| 使用场景 | 典型字段与数据结构 | 建议优先查看的方法 | 预期结果与决策用途 |",
        "| --- | --- | --- | --- |",
        "| 月度经营概览 | 金额、次数、评分等数值字段；渠道、区域等分类字段 | 描述性统计摘要、频数表、分位数画像、分层关键指标拆解 | 输出规模、集中趋势、波动和结构分布，用于经营复盘与看板基线。 |",
        "| 数据入库前质量检查 | 全部字段、缺失标记、唯一标识、数据类型 | 缺失机制诊断、异常值筛查、重复记录审计、数据类型校验 | 输出质量问题清单和处理优先级，为后续分析建立可用数据集。 |",
        "| 两组人群或渠道指标比较 | 一个数值结果字段加二元分组字段 | 韦尔奇双样本 T 检验、曼-惠特尼 U 检验、效应量、置信区间摘要 | 判断两组差异方向、大小与不确定性，用于渠道、客群或方案对比。 |",
        "| 同一对象前后效果评估 | 配对标识加前后数值测量或重复测量结构 | 配对样本 T 检验、威尔科克森符号秩检验、重复测量方差分析 | 评估培训、改版、干预前后的变化幅度与稳定性。 |",
        "| 多组方案或地区表现比较 | 数值结果字段加多分类分组字段 | 单因素方差分析、韦尔奇方差分析、克鲁斯卡尔-沃利斯检验、图基事后检验 | 定位存在差异的组别，为资源分配和方案筛选提供依据。 |",
        "| 转化、满意度或偏好关联 | 两个分类字段，或有序评分字段 | 卡方检验、费舍尔精确检验、克拉默 V、斯皮尔曼秩相关分析 | 衡量分类变量关联强度，识别转化漏斗、偏好或满意度结构。 |",
        "| 指标驱动因素诊断 | 目标字段加多个数值、分类或协变量字段 | 相关矩阵分析、偏相关分析、普通最小二乘回归、逻辑回归、方差膨胀因子诊断 | 输出主要驱动因素、方向和模型诊断，用于制定经营改进动作。 |",
        "| 预测需求、销量或风险 | 历史目标字段加特征字段；可含时间字段 | 岭回归、随机森林、交叉验证、ROC-AUC 分析、模型校准 | 比较预测性能、阈值和稳定性，支持预警、排序和资源配置。 |",
        "| 客群或产品分层 | 多个数值字段、行为特征或评分指标 | 主成分分析、K 均值聚类、层次聚类、高斯混合模型、轮廓系数分析 | 输出可解释的群组结构与特征画像，支持精细化运营。 |",
        "| 销量、流量或产能预测 | 连续时间字段加数值指标，包含足够历史周期 | 趋势与季节性分解、平稳性检验、自回归积分滑动平均模型、预测回测 | 识别趋势、季节性和预测误差，服务备货、排班与预算。 |",
        "| A/B 实验与产品改版评估 | 实验分组、目标指标、样本量和实验周期 | A/B 实验检验、样本量与统计功效分析、样本比例失配检验、CUPED 协变量调整 | 判断实验差异、检测能力和分流质量，支持上线或继续实验决策。 |",
        "| 政策、活动或价格调整效果评估 | 处理组/对照组、时间字段、结果字段和协变量 | 双重差分法、事件研究设计、倾向得分匹配、合成控制法、平行趋势诊断 | 估计处理效应并检查关键假设，为政策和营销评估提供证据。 |",
        "| 留存、流失与生命周期分析 | 生存时长、事件类型、分层字段和协变量 | 卡普兰-迈耶生存估计、对数秩生存曲线检验、Cox 比例风险模型 | 输出留存曲线、风险差异和风险因素，支持召回与生命周期运营。 |",
        "| 问卷、量表和用户研究 | 多题项量表、有序评分、多组样本 | 克朗巴赫阿尔法信度、因子分析、验证性因子分析、测量等值性检验 | 验证测量质量与结构，为研究结论和量表迭代提供依据。 |",
        "| 结论复核与稳健性验证 | 已完成的主分析结果、替代样本或替代设定 | 自助法置信区间、置换检验、稳健回归、敏感性分析、多重检验校正 | 检查结论对异常值、缺失、模型设定和多次比较的敏感程度。 |",
        "",
        "## 全量统计方法注册表",
        "",
    ]

    extra_families = sorted(set(grouped) - set(FAMILY_ORDER))
    for family in [*FAMILY_ORDER, *extra_families]:
        entries = grouped.get(family)
        if not entries:
            continue
        entries.sort(key=lambda entry: str(entry["id"]))
        live = sum(entry["status"] == "live" for entry in entries)
        lines.extend(
            [
                f"### {family_label(family)}（{len(entries)} 项；可运行 {live} 项）",
                "",
                "| 方法 ID | 方法 | 核心问题 | 所需字段角色 | 状态 |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        lines[-2:] = [
            "| 方法 ID | 中文名称 | 原始英文名称 | 核心问题 | 所需字段角色 | 状态 |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for entry in entries:
            lines.append(
                "| `{id}` | {name_zh} | {name} | {goal} | {roles} | {status} |".format(
                    id=escape_cell(entry["id"]),
                    name_zh=escape_cell(statistical_name_zh(entry)),
                    name=escape_cell(entry["name"]),
                    goal=escape_cell(entry["goal"]),
                    roles=escape_cell(role_labels(list(entry["variable_types"]))),
                    status=status_label(str(entry["status"])),
                )
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_lab_inventory() -> str:
    lab_catalog = auto_analysis_method_catalog(compact=True)
    cards = list(lab_catalog["methods"])
    status_counts = Counter(str(card["status"]) for card in cards)
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for card in cards:
        grouped[str(card["family_label"])].append(card)

    lines = [
        "# Analysis Lab 方法卡索引",
        "",
        "> 本文档由 `scripts/export_method_catalog_docs.py` 生成，记录当前 Lab 注册表中的全部方法卡。",
        "",
        "## 运行状态",
        "",
        f"- 方法卡总数：`{len(cards)}`",
        f"- 可运行：`{status_counts['live']}`",
        f"- 目录条目：`{status_counts['catalog']}`",
        f"- 规划条目：`{status_counts['planned']}`",
        "- API：`GET /api/lab/methods?compact=true`；全量字段可通过 `compact=false` 获取。",
        "",
        "## 使用约定",
        "",
        "每张方法卡保存方法身份、字段角色、可选运行模式与产物合约。`live` 卡可在 Lab 中绑定数据集字段并运行；卡片产物按方法契约输出 JSON、CSV、XLSX、Markdown，部分方法额外提供图表、SVG、HTML 或图像规格。",
        "",
        "## 使用场景与操作路径",
        "",
        "先从场景找到对应的中文方法名称，再在下方按注册族和状态筛选方法卡。运行前将数据列映射到卡片列出的字段角色；运行后结合中文输出形式下载或查看产物，并保留本次分析的参数与结果。",
        "",
        "| 使用场景 | 首选方法卡方向 | 需要映射的字段角色 | 常见产物 | 操作要点 |",
        "| --- | --- | --- | --- | --- |",
        "| 数据概览与数据质量检查 | 描述统计、数据质量、缺失与异常值审计 | 数值字段、分类字段、唯一标识、时间字段 | 统计摘要、质量清单、分布图表 | 先完成字段角色映射，再将质量结论作为后续方法选择依据。 |",
        "| 经营指标分层复盘 | 描述统计、分组汇总、透视与可视化方法卡 | 数值指标、分类分组、时间字段 | 分组汇总、交叉表、图表规格 | 将区域、渠道、产品线等字段设为分组角色，比较同一指标的结构差异。 |",
        "| 两组或多组效果比较 | 均值检验、非参数检验、实验分析方法卡 | 数值结果、二元或多分类分组、配对标识 | 检验结果、效应量、置信区间、表格 | 根据是否配对、分组数量和数据分布选择对应卡片。 |",
        "| 转化漏斗与分类交叉分析 | 分类关联、列联分析方法卡 | 两个分类字段、二元结果、分层字段 | 列联表、关联强度、显著性结果 | 将渠道、活动触达、转化结果映射为分类角色，检查样本量与分层条件。 |",
        "| 驱动因素与预测建模 | 关联分析、回归建模、机器学习方法卡 | 目标字段、特征字段、协变量 | 系数或特征重要性、预测结果、诊断输出 | 先运行特征和数据质量检查，再比较不同模型卡的性能与解释结果。 |",
        "| 客群细分与结构探索 | 多变量分析、聚类、降维方法卡 | 多个数值字段、分类标签、目标字段 | 分群标签、降维坐标、结构摘要 | 统一指标口径后输入多字段，结合群组规模和特征解释命名客群。 |",
        "| 趋势监控与预测 | 时间序列方法卡 | 时间字段、数值指标、可选特征字段 | 趋势分解、预测值、残差与回测结果 | 保持时间排序和周期粒度一致，使用历史区间检查预测误差。 |",
        "| A/B 实验与干预评估 | 实验分析、因果探查方法卡 | 实验分组、结果字段、时间字段、协变量 | 效应估计、功效分析、假设检查 | 明确处理组与对照组字段，记录实验周期、样本量与指标定义。 |",
        "| 留存与流失研究 | 生存分析方法卡 | 生存时长、事件类型、分层字段、协变量 | 生存曲线、风险比、分层比较结果 | 定义事件发生规则和观察截止点，再比较不同人群的留存曲线。 |",
        "| 方法结果交付与复核 | 报告部件、可视化与统计推断方法卡 | 已生成的分析结果、指标字段、分组字段 | JSON、CSV、XLSX、Markdown、图表或图像规格 | 选择与下游交付格式匹配的卡片，保存参数、输入范围和结果文件。 |",
        "",
        "### 标准操作流程",
        "",
        "1. 在 Analysis Lab 中选择状态为“可运行”的方法卡，并阅读卡片中的字段角色与中文输出形式。",
        "2. 将数据集列映射为数值、分类、时间、目标、特征、分组或配对等角色；字段缺失时回到数据概览场景补齐。",
        "3. 填写方法参数并执行，查看返回的结构化结果、表格和图表产物。",
        "4. 按结果中的统计量、置信区间、误差、诊断或分组画像形成业务结论，并将本次输入、参数和产物一并留存。",
        "5. 对关键结论选择稳健性、敏感性或替代模型方法卡进行复核，再进入后续报告交付流程。",
        "",
        "## 全量方法卡",
        "",
    ]

    for family in sorted(grouped):
        entries = sorted(grouped[family], key=lambda entry: str(entry["id"]))
        family_status = Counter(str(entry["status"]) for entry in entries)
        lines.extend(
            [
                f"### {family}（{len(entries)} 张；可运行 {family_status['live']} 张）",
                "",
                "| 卡片 ID | 方法概念 | 输出形态 | 字段角色 | 状态 | 来源 |",
                "| --- | --- | --- | --- | --- | --- |",
            ]
        )
        lines[-4] = (
            f"### {lab_family_label(family)}（注册族：`{family}`；"
            f"{len(entries)} 张；可运行 {family_status['live']} 张）"
        )
        lines[-2:] = [
            "| 卡片 ID | 中文方法名称 | 原始英文概念 | 中文输出形式 | 字段角色 | 状态 | 来源 |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
        for entry in entries:
            lines.append(
                "| `{id}` | {method_zh} | {method} | {output} | {roles} | {status} | {source} |".format(
                    id=escape_cell(entry["id"]),
                    method_zh=escape_cell(lab_method_name_zh(entry)),
                    method=escape_cell(entry["method_concept_label"]),
                    output=escape_cell(lab_output_label_zh(entry["method_output_label"])),
                    roles=escape_cell("、".join(entry["role_labels"])),
                    status=status_label(str(entry["status"])),
                    source=escape_cell(lab_source_label(entry["source"])),
                )
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    statistics_path = DOCS_DIR / "statistical_methods_zh.md"
    lab_path = DOCS_DIR / "lab_method_inventory_zh.md"
    statistics_path.write_text(render_statistics_catalog(), encoding="utf-8", newline="\n")
    lab_path.write_text(render_lab_inventory(), encoding="utf-8", newline="\n")
    print(f"wrote {statistics_path.relative_to(ROOT)}")
    print(f"wrote {lab_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
