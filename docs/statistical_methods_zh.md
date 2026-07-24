# Asteria Analyst 统计方法与 Analysis Lab 目录

> 本文档由 `scripts/export_method_catalog_docs.py` 从后端注册表生成。变更方法后请重新执行生成器，再提交本文件。

## 目录范围

- 统计方法注册总数：`362`
- 可运行统计方法：`81`
- 目录方法：`281`
- Analysis Lab 可运行统计方法卡：`273` 张，覆盖 `81` 个可运行统计方法概念。
- 方法数据源：`backend/app/services/statistical_catalog.py`；Lab 卡片注册源：`backend/app/services/auto_analysis_registry_service.py`。

### 状态说明

| 状态 | 含义 |
| --- | --- |
| 可运行 | 已连接执行器，可在 Analysis Lab 配置字段并产生运行产物。 |
| 目录条目 | 已登记方法目标与字段契约，用于选型、路线规划与后续执行器接入。 |
| 规划条目 | 已登记在 Lab 方法空间中，用于产品路线与能力编排。 |

### 字段角色速查

| 角色 | 使用方式 |
| --- | --- |
| 数值字段 | 金额、次数、评分、时长、连续型指标。 |
| 分类字段 | 地区、渠道、产品线、客户类型等离散分组。 |
| 时间字段 | 日期、周、月、季度或有稳定排序的时间戳。 |
| 目标字段 | 待解释、预测或比较的结果变量。 |
| 特征字段 | 用于解释或预测目标字段的输入变量集合。 |
| 配对标识 / 受试内因子 | 同一对象前后测量、重复测量或匹配样本结构。 |
| 面板标识 / 分层字段 | 个体-时间面板、分层实验或多层数据结构。 |

## 结果解读与交付

| 方法族 | 优先查看的结果 | 常见交付判断 |
| --- | --- | --- |
| 描述统计 | 样本量、缺失、均值/中位数、分位数、集中度 | 识别水平、波动、长尾和头部贡献。 |
| 分布假设 | 检验统计量、p 值、残差诊断 | 选择参数检验、稳健方法或变换策略。 |
| 均值与非参数检验 | 组间差异、置信区间、p 值、效应量 | 判断差异方向、大小与业务价值。 |
| 分类关联 | 列联表、期望频数、关联强度 | 判断分类变量是否相关并量化关联强度。 |
| 关联分析 | 相关系数、方向、强度、显著性 | 区分线性、秩相关、偏相关和非线性关联。 |
| 回归与机器学习 | 系数/重要性、拟合优度、误差、诊断 | 解释驱动因素、预测表现与稳定性。 |
| 多变量与聚类 | 方差解释、载荷、簇规模、轮廓线索 | 完成降维、分群或群体结构识别。 |
| 时间序列 | 趋势、季节性、滞后、平稳性、残差 | 判断时间结构并选择预测或监控路线。 |
| 实验、因果与生存 | 处理效应、对照证据、风险率/生存率 | 形成实验决策、因果评估或留存分析结论。 |

## 全量统计方法注册表

### 描述统计（61 项；可运行 10 项）

| 方法 ID | 方法 | 核心问题 | 所需字段角色 | 状态 |
| --- | --- | --- | --- | --- |
| `areal_interpolation` | Areal Interpolation | Translate measurements between incompatible geographic boundaries. | entity level、数值字段 | 目录条目 |
| `boxcox_transformation` | Box-Cox Transformation | Find a power transformation for positive numeric variables to reduce skew or stabilize variance. | 数值字段 | 目录条目 |
| `business_rule_validation` | Business Rule Validation | Validate domain rules such as totals, statuses, temporal order, and logical dependencies. | field set | 目录条目 |
| `cluster_sampling_design` | Cluster Sampling Design | Document clustered sampling units and the design effects they introduce. | entity level、分组结构 | 目录条目 |
| `cohort_summary` | Cohort Summary | 按 cohort 汇总表现 | 时间字段、分类字段、数值字段 | 目录条目 |
| `completeness_sla_monitor` | Completeness SLA Monitor | Monitor whether required fields and records meet completeness thresholds. | full dataset | 目录条目 |
| `consent_coverage_audit` | Consent Coverage Audit | Verify whether records and fields are covered by consent or allowed-use metadata. | field set | 目录条目 |
| `cross_tabulation` | Cross Tabulation | 生成列联表与交叉分布 | 分类字段、分类字段 | 可运行 |
| `data_contract_validation` | Data Contract Validation | Validate schema, allowed ranges, categorical domains, freshness, and nullability against a contract. | full dataset | 目录条目 |
| `data_minimization_audit` | Data Minimization Audit | Check whether each field is necessary for the stated analysis purpose. | field set | 目录条目 |
| `data_quality_scorecard` | Data Quality Scorecard | Summarize completeness, validity, uniqueness, consistency, timeliness, and accuracy indicators. | full dataset | 目录条目 |
| `data_type_validation` | Data Type Validation | Check whether numeric, categorical, time, identifier, and ordinal fields are typed consistently with their analysis roles. | field set | 目录条目 |
| `datasheet_for_dataset` | Datasheet for Dataset | Document dataset provenance, collection process, intended use, risks, and known gaps. | full dataset | 目录条目 |
| `denominator_integrity_check` | Denominator Integrity Check | Verify that rates and ratios use consistent denominators across groups and time. | field pair、分组结构 | 目录条目 |
| `descriptive_summary` | Descriptive Summary | 描述均值、中位数、标准差、分位数 | 数值字段 | 可运行 |
| `duplicate_record_audit` | Duplicate Record Audit | Detect exact and near-duplicate records before calculating rates, totals, or model training samples. | field set | 目录条目 |
| `ego_network_profile` | Ego Network Profile | Summarize local neighborhoods around selected entities. | entity level | 目录条目 |
| `feature_binning_strategy` | Feature Binning Strategy | Convert continuous variables into meaningful bins for stability, interpretability, or nonlinear modeling. | 数值字段 | 目录条目 |
| `frequency_table` | Frequency Table | 描述分类频数与占比 | 分类字段 | 可运行 |
| `funnel_step_conversion` | Funnel Step Conversion | Measure transition rates and drop-off between ordered process or journey steps. | 分类字段、数值字段 | 目录条目 |
| `geohash_grid_aggregation` | Geohash Grid Aggregation | Aggregate events into consistent spatial grid cells for density and trend analysis. | entity level、数值字段 | 目录条目 |
| `gini_coefficient` | Gini Coefficient | Gini Coefficient（基尼系数）用 0 到 1 的系数衡量数值分布的集中程度和长尾不均衡；数值越高，表示少数对象贡献越集中。适合收入、销售额、采购金额、客户贡献等贡献结构分析。 | 数值字段 | 可运行 |
| `high_cardinality_profile` | High-cardinality Profile | Diagnose categorical fields with many levels, sparse counts, or unstable long tails. | 分类字段 | 目录条目 |
| `imputation_strategy_plan` | Imputation Strategy Plan | Compare deletion, simple imputation, model-based imputation, and multiple imputation as an auditable data-preparation plan. | field set | 目录条目 |
| `keyword_in_context_review` | Keyword-in-context Review | Inspect how important terms appear in surrounding text before drawing thematic conclusions. | field set | 目录条目 |
| `lorenz_curve` | Lorenz Curve | Lorenz Curve（洛伦兹曲线）按数值从低到高展示累计对象占比与累计指标贡献之间的偏离，用来直观看长尾结构、集中贡献和分布不均衡。 | 数值字段 | 目录条目 |
| `measurement_error_audit` | Measurement Error Audit | Identify impossible values, rounding artifacts, inconsistent units, and likely data-entry errors. | field set | 目录条目 |
| `missingness_heatmap_audit` | Missingness Heatmap Audit | Map missing values across rows and fields to find systematic gaps, block missingness, and collection failures. | field set | 目录条目 |
| `missingness_mechanism_diagnostic` | Missingness Mechanism Diagnostic | Classify missing-data patterns as likely MCAR, MAR, or MNAR before choosing deletion or imputation. | field set | 目录条目 |
| `nonresponse_bias_analysis` | Nonresponse Bias Analysis | Assess whether missing respondents or records differ systematically from observed cases. | field set、分组结构 | 目录条目 |
| `north_star_metric_audit` | North-star Metric Audit | Check whether a primary metric is sensitive, stable, interpretable, and resistant to gaming. | field set | 目录条目 |
| `outlier_screening_iqr` | IQR Outlier Screening | Use interquartile fences to flag extreme numeric observations without assuming normality. | 数值字段 | 目录条目 |
| `pareto_analysis` | Pareto Analysis | 识别头部贡献结构 | 分类字段、数值字段 | 可运行 |
| `pii_detection_profile` | PII Detection Profile | Detect personally identifiable information in fields before sharing or modeling. | field set | 目录条目 |
| `pivot_summary` | Pivot Summary | 按维度汇总指标 | 分类字段、数值字段 | 可运行 |
| `post_stratification_weighting` | Post-stratification Weighting | Adjust sample weights to match known population margins across key strata. | field set、分组结构 | 目录条目 |
| `privacy_k_anonymity` | k-anonymity Privacy Check | Assess whether quasi-identifier groups contain enough records to reduce re-identification risk. | field set | 目录条目 |
| `privacy_l_diversity` | l-diversity Privacy Check | Check whether sensitive values remain diverse within anonymized groups. | field set | 目录条目 |
| `quantile_profile` | Quantile Profile | 分析分位数分布结构 | 数值字段 | 可运行 |
| `raking_weighting` | Raking Weighting | Iteratively calibrate survey weights to multiple population margins. | field set、分组结构 | 目录条目 |
| `range_constraint_validation` | Range Constraint Validation | Detect values outside allowed numeric, date, or categorical ranges. | field set | 目录条目 |
| `rare_category_consolidation` | Rare Category Consolidation | Pool sparse categories to improve stability, privacy, and model robustness. | 分类字段 | 目录条目 |
| `referential_integrity_check` | Referential Integrity Check | Check whether foreign-key-like relationships are complete and consistent. | field set | 目录条目 |
| `retention_policy_audit` | Retention Policy Audit | Check whether data age, deletion requirements, and retention rules are respected. | 时间字段、field set | 目录条目 |
| `robust_zscore_outlier` | Robust Z-score Outlier Screening | Use median and MAD-based standardized distance to detect extreme values under skewed distributions. | 数值字段 | 目录条目 |
| `root_cause_data_quality` | Data Quality Root Cause Analysis | Trace quality failures to source systems, transformations, owners, or workflow stages. | full dataset | 目录条目 |
| `sampling_bias_audit` | Sampling Bias Audit | Compare observed sample composition with the target population or intended analysis frame. | field set、分组结构 | 目录条目 |
| `schema_drift_detection` | Schema Drift Detection | Detect added, removed, renamed, or retyped fields across dataset versions. | full dataset | 目录条目 |
| `segmented_kpi_breakdown` | Segmented KPI Breakdown | 分组输出关键指标对比 | 分类字段、数值字段 | 可运行 |
| `semantic_deduplication` | Semantic Deduplication | Find near-duplicate records or documents using semantic similarity rather than exact matching. | field set | 目录条目 |
| `small_area_estimation` | Small Area Estimation | Estimate subgroup or geographic values when direct samples are sparse. | entity level、分组结构 | 目录条目 |
| `spatial_join_audit` | Spatial Join Audit | Verify geographic joins, boundary matching, coordinate systems, and aggregation units. | entity level | 目录条目 |
| `standardization_scaling` | Standardization / Scaling | Prepare numeric features with z-score, robust, min-max, or domain-specific scaling. | field set | 目录条目 |
| `stratified_sampling_design` | Stratified Sampling Design | Plan samples by strata so important groups are represented before estimation or modeling. | 分组结构、field set | 目录条目 |
| `survey_design_effect` | Survey Design Effect | Estimate how weighting, clustering, or stratification changes effective sample size and uncertainty. | field set、分组结构 | 目录条目 |
| `synthetic_data_quality_audit` | Synthetic Data Quality Audit | Compare synthetic data utility, privacy risk, distribution fit, and relationship preservation. | full dataset | 目录条目 |
| `trimmed_mean` | Trimmed Mean | 在异常值存在时估计稳健均值 | 数值字段 | 可运行 |
| `uniqueness_constraint_check` | Uniqueness Constraint Check | Verify primary keys, composite keys, and uniqueness expectations. | field set | 目录条目 |
| `winsorization_strategy` | Winsorization Strategy | Cap extreme values using transparent thresholds while preserving record counts. | 数值字段 | 目录条目 |
| `winsorized_summary` | Winsorized Summary | 削尾后描述分布 | 数值字段 | 可运行 |
| `yeo_johnson_transformation` | Yeo-Johnson Transformation | Transform numeric variables that may include zero or negative values. | 数值字段 | 目录条目 |

### 分布假设（18 项；可运行 12 项）

| 方法 ID | 方法 | 核心问题 | 所需字段角色 | 状态 |
| --- | --- | --- | --- | --- |
| `anderson_darling` | Anderson-Darling Test | 尾部更敏感的分布拟合检验 | 数值字段 | 可运行 |
| `bartlett` | Bartlett Test | 正态假设下检验方差齐性 | 数值字段、分类字段 | 可运行 |
| `box_m_test` | Box's M Test | Assess equality of covariance matrices before multivariate group comparison. | 多个数值字段、分类字段 | 目录条目 |
| `breusch_pagan` | Breusch-Pagan Test | 检验回归异方差性 | 数值字段、数值字段 | 可运行 |
| `brown_forsythe` | Brown-Forsythe Test | 更稳健的方差齐性检验 | 数值字段、分类字段 | 可运行 |
| `dagostino_k2` | D'Agostino K^2 Test | 联合偏度峰度做正态性检验 | 数值字段 | 可运行 |
| `durbin_watson` | Durbin-Watson | 检验残差自相关 | 数值字段、数值字段 | 可运行 |
| `jarque_bera` | Jarque-Bera Test | 根据偏度与峰度检验正态性 | 数值字段 | 可运行 |
| `kolmogorov_smirnov_1samp` | One-sample KS Test | 检验样本与理论分布的一致性 | 数值字段 | 可运行 |
| `levene` | Levene Test | 检验多组方差齐性 | 数值字段、分类字段 | 可运行 |
| `mauchly_sphericity` | Mauchly Sphericity Test | Check sphericity for repeated-measures ANOVA and decide whether correction is needed. | 数值字段、受试内因子 | 目录条目 |
| `normality` | Normality Test | 检验分布是否接近正态 | 数值字段 | 可运行 |
| `overdispersion_diagnostic` | Overdispersion Diagnostic | Check whether count variance exceeds mean and ordinary Poisson assumptions are too narrow. | 计数字段 | 目录条目 |
| `qq_diagnostic_review` | Q-Q Diagnostic Review | Compare empirical quantiles with a reference distribution to inspect shape deviations. | 数值字段 | 目录条目 |
| `shapiro_wilk` | Shapiro-Wilk Test | 小样本正态性检验 | 数值字段 | 可运行 |
| `skewness_kurtosis_profile` | Skewness / Kurtosis Profile | Summarize asymmetry and tail heaviness to guide transformation, robust tests, or nonparametric methods. | 数值字段 | 目录条目 |
| `white_test` | White Test | 广义异方差检验 | 数值字段、数值字段 | 可运行 |
| `zero_inflation_diagnostic` | Zero-inflation Diagnostic | Detect excessive zeros before choosing count, hurdle, or zero-inflated models. | 数值字段 | 目录条目 |

### 均值检验（13 项；可运行 10 项）

| 方法 ID | 方法 | 核心问题 | 所需字段角色 | 状态 |
| --- | --- | --- | --- | --- |
| `ancova` | ANCOVA | 控制协变量后比较组间均值 | 数值字段、分类字段、数值字段 | 可运行 |
| `anova` | One-way ANOVA | 比较多组均值差异 | 数值字段、分类字段 | 可运行 |
| `equivalence_test_tost` | TOST Equivalence Test | 检验两组是否统计等效 | 数值字段、二元分组 | 目录条目 |
| `hotelling_t2` | Hotelling T^2 | 多变量均值比较 | 多个数值字段、二元分组 | 目录条目 |
| `manova` | MANOVA | 多因变量组间差异检验 | 多个数值字段、分类字段 | 目录条目 |
| `one_sample_ttest` | One-sample T-test | 比较样本均值与理论值 | 数值字段 | 可运行 |
| `paired_ttest` | Paired T-test | 比较配对样本均值差异 | 数值字段、配对标识 | 可运行 |
| `repeated_measures_anova` | Repeated Measures ANOVA | 分析重复测量差异 | 数值字段、受试内因子 | 可运行 |
| `ttest` | Welch Two-sample T-test | 比较两组均值差异 | 数值字段、二元分组 | 可运行 |
| `tukey_hsd` | Tukey HSD | ANOVA 之后进行多重比较 | 数值字段、分类字段 | 可运行 |
| `two_way_anova` | Two-way ANOVA | 分析两个因子及交互作用 | 数值字段、分类字段、分类字段 | 可运行 |
| `welch_anova` | Welch ANOVA | 方差不齐时的多组均值检验 | 数值字段、分类字段 | 可运行 |
| `z_test_mean` | Z-test for Mean | 大样本均值检验 | 数值字段 | 可运行 |

### 非参数检验（14 项；可运行 12 项）

| 方法 ID | 方法 | 核心问题 | 所需字段角色 | 状态 |
| --- | --- | --- | --- | --- |
| `bootstrap_ci` | Bootstrap CI | 用重抽样估计区间 | 数值字段 | 可运行 |
| `cliffs_delta_effect_size` | Cliff's Delta Effect Size | Report ordinal dominance between two groups without relying on means or normality. | 数值字段、二元分组 | 目录条目 |
| `fligner_killeen` | Fligner-Killeen Test | 稳健的方差齐性检验 | 数值字段、分类字段 | 可运行 |
| `friedman` | Friedman Test | 重复测量的非参数比较 | 数值字段、受试内因子 | 可运行 |
| `kruskal` | Kruskal-Wallis Test | 多组中位数/秩和比较 | 数值字段、分类字段 | 可运行 |
| `ks_two_sample` | Two-sample KS Test | 比较两组完整分布差异 | 数值字段、二元分组 | 可运行 |
| `mann_whitney` | Mann-Whitney U Test | 两组秩和比较 | 数值字段、二元分组 | 可运行 |
| `median_test` | Median Test | 比较组间中位数是否一致 | 数值字段、分类字段 | 可运行 |
| `mood_median` | Mood Median Test | 检验多组中位数差异 | 数值字段、分类字段 | 可运行 |
| `permutation_test` | Permutation Test | 用重排法检验组间差异 | 数值字段、分类字段 | 可运行 |
| `rank_biserial_correlation` | Rank-biserial Correlation | Turn rank-based group differences into an interpretable effect-size measure. | 数值字段、二元分组 | 目录条目 |
| `runs_test` | Runs Test | 检验序列随机性 | 有序字段 | 可运行 |
| `sign_test` | Sign Test | 基于方向的稳健配对检验 | 数值字段、配对标识 | 可运行 |
| `wilcoxon_signed_rank` | Wilcoxon Signed-rank Test | 配对样本秩和检验 | 数值字段、配对标识 | 可运行 |

### 分类关联（13 项；可运行 10 项）

| 方法 ID | 方法 | 核心问题 | 所需字段角色 | 状态 |
| --- | --- | --- | --- | --- |
| `chi_square` | Chi-square Test | 检验两个分类变量独立性 | 分类字段、分类字段 | 可运行 |
| `cmh_test` | Cochran-Mantel-Haenszel Test | 控制分层后的列联分析 | 分类字段、分类字段、分层字段 | 可运行 |
| `cochran_q` | Cochran Q Test | 三个及以上相关二元样本比较 | 二元字段、受试内因子 | 可运行 |
| `cohens_kappa` | Cohen's Kappa | 评估两位评定者一致性 | 分类字段、配对标识 | 可运行 |
| `cramers_v` | Cramer's V | 分类变量关联强度 | 分类字段、分类字段 | 可运行 |
| `fisher_exact` | Fisher Exact Test | 2x2 列联精确检验 | 分类字段、分类字段 | 可运行 |
| `goodman_kruskal_lambda` | Goodman-Kruskal Lambda | 分类变量预测改进度 | 分类字段、分类字段 | 可运行 |
| `mcnemar` | McNemar Test | 配对二元结果变化检验 | 二元字段、配对标识 | 可运行 |
| `odds_ratio` | Odds Ratio | Estimate how exposure changes the odds of a binary outcome. | 二元字段、二元字段 | 目录条目 |
| `phi_coefficient` | Phi Coefficient | 2x2 列联关联强度 | 二元字段、二元字段 | 可运行 |
| `relative_risk` | Relative Risk | Compare event probability across exposed and unexposed groups. | 二元字段、二元字段 | 目录条目 |
| `risk_difference` | Risk Difference | Measure absolute event-rate lift or reduction between two groups. | 二元字段、二元字段 | 目录条目 |
| `theils_u` | Theil's U | 不对称分类关联度 | 分类字段、分类字段 | 可运行 |

### 关联分析（16 项；可运行 8 项）

| 方法 ID | 方法 | 核心问题 | 所需字段角色 | 状态 |
| --- | --- | --- | --- | --- |
| `canonical_correlation` | Canonical Correlation | 两组变量的线性关联 | 多个数值字段、多个数值字段 | 目录条目 |
| `cooccurrence_network_analysis` | Co-occurrence Network Analysis | Map items, terms, or entities that appear together more often than expected. | field set | 目录条目 |
| `correlation` | Correlation Matrix | 快速扫描数值变量联动关系 | 多个数值字段 | 可运行 |
| `distance_correlation` | Distance Correlation | 捕捉非线性关联 | 数值字段、数值字段 | 可运行 |
| `eta_squared` | Eta Squared | 分类到连续的解释强度 | 分类字段、数值字段 | 可运行 |
| `intraclass_correlation` | Intraclass Correlation | 组内一致性估计 | 数值字段、分组结构 | 目录条目 |
| `kendall_tau` | Kendall Tau | 稳健秩相关分析 | 数值字段、数值字段 | 可运行 |
| `moran_i_spatial_autocorrelation` | Moran's I Spatial Autocorrelation | Measure whether nearby geographic units have similar values. | entity level、数值字段 | 目录条目 |
| `mutual_information` | Mutual Information | 信息论视角的变量依赖度 | 数值或分类字段、数值或分类字段 | 目录条目 |
| `nearest_neighbor_spatial_search` | Nearest-neighbor Spatial Search | Find closest spatial entities and distance-based relationships. | entity level | 目录条目 |
| `network_assortativity` | Network Assortativity | Measure whether nodes connect preferentially to similar nodes. | entity level、分组结构 | 目录条目 |
| `partial_correlation` | Partial Correlation | 控制协变量后的相关 | 数值字段、数值字段、协变量 | 可运行 |
| `pearson_correlation` | Pearson Correlation | 线性相关分析 | 数值字段、数值字段 | 可运行 |
| `point_biserial` | Point-Biserial Correlation | 连续与二元变量相关 | 数值字段、二元字段 | 可运行 |
| `spearman_correlation` | Spearman Correlation | 秩相关分析 | 数值字段、数值字段 | 可运行 |
| `text_embedding_similarity` | Text Embedding Similarity | Measure semantic similarity between documents, labels, or comments using embedding distance. | field pair | 目录条目 |

### 广义线性模型（34 项；可运行 8 项）

| 方法 ID | 方法 | 核心问题 | 所需字段角色 | 状态 |
| --- | --- | --- | --- | --- |
| `aic_bic_model_selection` | AIC / BIC Model Selection | Compare candidate models using penalized likelihood criteria. | 目标字段、特征字段 | 目录条目 |
| `beta_regression` | Beta Regression | 比例型结果建模 | 比例字段、多个数值字段 | 目录条目 |
| `cluster_robust_standard_errors` | Cluster-robust Standard Errors | Adjust uncertainty when observations are correlated within groups or entities. | 目标字段、特征字段、分组结构 | 目录条目 |
| `cooks_distance` | Cook's Distance | Rank observations by their influence on model estimates. | 目标字段、特征字段 | 目录条目 |
| `cross_validated_regression` | Cross-validated Regression | Estimate out-of-sample regression error with held-out folds instead of in-sample fit only. | 目标字段、特征字段 | 目录条目 |
| `elastic_net` | Elastic Net | 兼顾 Ridge 与 Lasso | 数值字段、多个数值字段 | 可运行 |
| `gamma_glm` | Gamma GLM | 正偏连续结果建模 | 正值数值字段、多个数值字段 | 目录条目 |
| `generalized_additive_model` | Generalized Additive Model | Estimate nonlinear additive effects with smooth functions for each predictor. | 目标字段、特征字段 | 目录条目 |
| `geographically_weighted_regression` | Geographically Weighted Regression | Estimate location-varying regression relationships across space. | 目标字段、特征字段、entity level | 目录条目 |
| `glm_binomial` | Binomial GLM | 用 GLM 方式做二元建模 | 二元字段、多个数值字段 | 目录条目 |
| `heteroskedasticity_robust_se` | Heteroskedasticity-robust Standard Errors | Use robust uncertainty estimates when residual variance is not constant. | 目标字段、特征字段 | 目录条目 |
| `influence_diagnostics` | Influence Diagnostics | Identify observations with high leverage, large residuals, or outsized influence on fitted models. | 目标字段、特征字段 | 目录条目 |
| `interaction_feature_screen` | Interaction Feature Screen | Identify candidate interaction terms between predictors before model expansion. | 目标字段、特征字段 | 目录条目 |
| `lasso_regression` | Lasso Regression | 变量选择与稀疏建模 | 数值字段、多个数值字段 | 可运行 |
| `logit` | Logistic Regression | 二分类概率建模 | 二元字段、多个数值字段 | 可运行 |
| `model_specification_curve` | Specification Curve Analysis | Compare conclusions across many defensible model specifications. | 目标字段、特征字段 | 目录条目 |
| `multinomial_logit` | Multinomial Logit | 多分类离散选择建模 | 多分类目标、多个数值字段 | 目录条目 |
| `negative_binomial` | Negative Binomial Regression | 过度离散计数建模 | 计数字段、多个数值字段 | 目录条目 |
| `ols` | OLS Regression | 线性回归解释连续结果 | 数值字段、多个数值字段 | 可运行 |
| `ordinal_logit` | Ordinal Logistic Regression | 有序分类建模 | 有序分类目标、多个数值字段 | 目录条目 |
| `piecewise_regression` | Piecewise Regression | Fit different linear slopes across threshold regions or regimes. | 目标字段、特征字段 | 目录条目 |
| `poisson_glm` | Poisson GLM | 计数结果建模 | 计数字段、多个数值字段 | 可运行 |
| `prediction_interval` | Prediction Interval | Estimate the likely range for individual future observations rather than only mean uncertainty. | 目标字段、特征字段 | 目录条目 |
| `probit_regression` | Probit Regression | 二分类潜变量建模 | 二元字段、多个数值字段 | 目录条目 |
| `quantile_regression` | Quantile Regression | 关注不同分位点的影响 | 数值字段、多个数值字段 | 可运行 |
| `residual_diagnostic_panel` | Residual Diagnostic Panel | Inspect residual shape, fitted-vs-observed patterns, heteroscedasticity, and nonlinearity after model fitting. | 目标字段、特征字段 | 目录条目 |
| `ridge_regression` | Ridge Regression | 缓解多重共线性 | 数值字段、多个数值字段 | 可运行 |
| `robust_regression` | Robust Regression | 减小异常值影响 | 数值字段、多个数值字段 | 可运行 |
| `spatial_error_model` | Spatial Error Model | Account for spatially correlated omitted factors in regression residuals. | 目标字段、特征字段、entity level | 目录条目 |
| `spatial_lag_model` | Spatial Lag Model | Model outcomes influenced by neighboring-unit outcomes. | 目标字段、特征字段、entity level | 目录条目 |
| `spline_regression` | Spline Regression | Model smooth nonlinear relationships while preserving interpretable fitted curves. | 目标字段、特征字段 | 目录条目 |
| `stepwise_model_comparison` | Stepwise Model Comparison | Compare nested or staged model specifications while documenting selection risk. | 目标字段、特征字段 | 目录条目 |
| `vif_multicollinearity` | VIF Multicollinearity Diagnostic | Detect predictors whose shared variance may destabilize regression coefficients. | 目标字段、特征字段 | 目录条目 |
| `zero_inflated_poisson` | Zero-inflated Poisson | 零膨胀计数建模 | 计数字段、多个数值字段 | 目录条目 |

### 机器学习（36 项；可运行 3 项）

| 方法 ID | 方法 | 核心问题 | 所需字段角色 | 状态 |
| --- | --- | --- | --- | --- |
| `anomaly_detection_isolation_forest` | Isolation Forest Anomaly Detection | Detect unusual observations in multivariate data using isolation-based scoring. | field set | 目录条目 |
| `anomaly_detection_local_outlier_factor` | Local Outlier Factor | Find observations that are locally sparse compared with their nearest neighbors. | field set | 目录条目 |
| `champion_challenger_evaluation` | Champion / Challenger Evaluation | Compare incumbent and candidate models under consistent metrics and traffic splits. | 目标字段、特征字段 | 目录条目 |
| `concept_drift_detection` | Concept Drift Detection | Detect changes in the relationship between predictors and outcomes over time. | 目标字段、特征字段、time window | 目录条目 |
| `conformal_prediction` | Conformal Prediction | Build distribution-free prediction sets with finite-sample coverage guarantees. | 目标字段、特征字段 | 目录条目 |
| `confusion_matrix_review` | Confusion Matrix Review | Translate classification errors into false positives, false negatives, and operational tradeoffs. | 二元字段、特征字段 | 目录条目 |
| `cost_sensitive_evaluation` | Cost-sensitive Evaluation | Evaluate predictions with asymmetric false-positive and false-negative costs. | 目标字段、特征字段 | 目录条目 |
| `cross_validation` | Cross-validation | Estimate generalization performance across repeated training and validation folds. | 目标字段、特征字段 | 目录条目 |
| `data_drift_dashboard` | Data Drift Dashboard | Track distribution shifts in features, labels, predictions, and residuals. | field set、time window | 目录条目 |
| `data_leakage_audit` | Data Leakage Audit | Flag predictors that may encode future information, target proxies, or post-outcome operational states. | 目标字段、特征字段 | 目录条目 |
| `deep_learning` | Deep Learning Network | 用更深的神经网络拟合复杂非线性结构 | 数值或二元目标、多个数值字段 | 可运行 |
| `fairness_proxy_variable_audit` | Fairness Proxy Variable Audit | Detect features that may proxy protected classes or sensitive attributes. | 目标字段、特征字段、分组结构 | 目录条目 |
| `fairness_slice_audit` | Fairness Slice Audit | Compare model errors, calibration, or decision rates across protected or operationally important groups. | 目标字段、特征字段、分组结构 | 目录条目 |
| `feature_privacy_risk_rank` | Feature Privacy Risk Rank | Rank predictors by re-identification, sensitivity, proxy, and governance risk. | 特征字段 | 目录条目 |
| `graph_anomaly_detection` | Graph Anomaly Detection | Detect unusual nodes, edges, or subgraphs in relationship data. | entity level | 目录条目 |
| `learning_curve` | Learning Curve | Show whether model performance is limited by sample size, bias, or variance. | 目标字段、特征字段 | 目录条目 |
| `link_prediction_baseline` | Link Prediction Baseline | Score likely missing or future edges in a graph using structural features. | entity level | 目录条目 |
| `model_calibration` | Model Calibration | Check whether predicted probabilities match observed outcome frequencies. | 二元字段、特征字段 | 目录条目 |
| `model_card_documentation` | Model Card Documentation | Document model purpose, data, metrics, limitations, and responsible-use boundaries. | 目标字段、特征字段 | 目录条目 |
| `model_performance_monitor` | Model Performance Monitor | Track model accuracy, calibration, lift, drift, and subgroup performance after deployment. | 目标字段、特征字段、time window | 目录条目 |
| `model_retraining_trigger` | Model Retraining Trigger | Define rules for retraining based on drift, performance decay, or data coverage changes. | 目标字段、特征字段、time window | 目录条目 |
| `nested_cross_validation` | Nested Cross-validation | Separate hyperparameter selection from unbiased model-performance estimation. | 目标字段、特征字段 | 目录条目 |
| `neural_network` | Neural Network | 做非线性模式拟合与预测 | 数值或二元目标、多个数值字段 | 可运行 |
| `one_hot_encoding_plan` | One-hot Encoding Plan | Represent categorical variables for modeling while tracking rare levels and reference categories. | 特征字段 | 目录条目 |
| `online_offline_metric_gap` | Online / Offline Metric Gap | Compare offline validation metrics with live production outcomes. | 目标字段、特征字段、time window | 目录条目 |
| `permutation_importance_review` | Permutation Importance Review | Rank features by measuring performance loss after shuffling each predictor. | 目标字段、特征字段 | 目录条目 |
| `population_stability_index` | Population Stability Index | Measure feature or score distribution drift between baseline and current populations. | field set、time window | 目录条目 |
| `precision_recall_analysis` | Precision / Recall Analysis | Evaluate classifier performance when the positive class is rare or costly. | 二元字段、特征字段 | 目录条目 |
| `random_forest` | Random Forest | 做非线性预测并输出特征重要性 | 数值或二元目标、多个数值字段 | 可运行 |
| `roc_auc_analysis` | ROC AUC Analysis | Evaluate binary classifier ranking quality across thresholds. | 二元字段、特征字段 | 目录条目 |
| `sentiment_classifier_audit` | Sentiment Classifier Audit | Evaluate sentiment labels, uncertainty, drift, and subgroup errors in text classification. | 目标字段、特征字段 | 目录条目 |
| `shap_explanation` | SHAP Explanation | Explain model predictions using additive feature contribution summaries. | 目标字段、特征字段 | 目录条目 |
| `target_encoding_audit` | Target Encoding Audit | Encode high-cardinality categories while preventing target leakage and overfitting. | 目标字段、特征字段 | 目录条目 |
| `text_label_quality_audit` | Text Label Quality Audit | Check annotation consistency, class balance, disagreement, and ambiguous examples in labeled text. | 目标字段、特征字段 | 目录条目 |
| `threshold_optimization` | Decision Threshold Optimization | Choose classification thresholds based on cost, recall, precision, or business capacity. | 二元字段、特征字段 | 目录条目 |
| `train_test_split_audit` | Train / Test Split Audit | Verify split strategy, leakage boundaries, stratification, and time ordering before evaluating a model. | 目标字段、特征字段 | 目录条目 |

### 多变量分析（29 项；可运行 2 项）

| 方法 ID | 方法 | 核心问题 | 所需字段角色 | 状态 |
| --- | --- | --- | --- | --- |
| `bertopic_clustering` | BERTopic Clustering | Cluster text embeddings into interpretable topics with representative terms. | field set | 目录条目 |
| `bipartite_network_projection` | Bipartite Network Projection | Project two-mode relationships into one-mode similarity or co-occurrence networks. | entity level | 目录条目 |
| `cluster_stability` | Cluster Stability Analysis | Test whether discovered groups persist under resampling, feature changes, or random initialization. | 多个数值字段 | 目录条目 |
| `community_detection_louvain` | Louvain Community Detection | Detect modular groups in a network by optimizing community structure. | entity level | 目录条目 |
| `confirmatory_factor_analysis` | Confirmatory Factor Analysis | 验证预设潜变量结构 | 多个数值字段 | 目录条目 |
| `correspondence_analysis` | Correspondence Analysis | 列联表降维与可视化 | 分类字段、分类字段 | 目录条目 |
| `dbscan` | DBSCAN | 密度聚类与噪声识别 | 多个数值字段 | 目录条目 |
| `discriminant_analysis_lda` | Linear Discriminant Analysis | 监督降维与分类 | 多个数值字段、分类字段 | 目录条目 |
| `discriminant_analysis_qda` | Quadratic Discriminant Analysis | 非线性边界判别 | 多个数值字段、分类字段 | 目录条目 |
| `elbow_method` | Elbow Method | Compare cluster counts by tracking within-cluster compactness across candidate k values. | 多个数值字段 | 目录条目 |
| `factor_analysis` | Factor Analysis | 提取潜在因子结构 | 多个数值字段 | 目录条目 |
| `gaussian_mixture` | Gaussian Mixture Model | 软分群与混合分布建模 | 多个数值字段 | 目录条目 |
| `getis_ord_hotspot` | Getis-Ord Hotspot Analysis | Identify local clusters of unusually high or low values. | entity level、数值字段 | 目录条目 |
| `hierarchical_clustering` | Hierarchical Clustering | 层次聚类树状划分 | 多个数值字段 | 目录条目 |
| `ica` | Independent Component Analysis | 提取独立源信号 | 多个数值字段 | 目录条目 |
| `kmeans` | KMeans Clustering | 基于均值的无监督分群 | 多个数值字段 | 可运行 |
| `latent_class_analysis` | Latent Class Analysis | 分类数据潜在类别建模 | 多分类字段 | 目录条目 |
| `multivariate_control_chart` | Multivariate Control Chart | Monitor several correlated process metrics at once for unusual joint movement. | 多个数值字段 | 目录条目 |
| `named_entity_extraction_profile` | Named Entity Extraction Profile | Extract people, organizations, locations, products, and other entities from text fields. | field set | 目录条目 |
| `network_betweenness_centrality` | Network Betweenness Centrality | Identify bridge nodes that lie on many shortest paths between others. | entity level | 目录条目 |
| `network_degree_centrality` | Network Degree Centrality | Rank nodes by direct connection count in a relationship graph. | entity level | 目录条目 |
| `network_pagerank` | Network PageRank | Rank node influence using recursive incoming relationship strength. | entity level | 目录条目 |
| `pca` | Principal Component Analysis | 降维与方差解释 | 多个数值字段 | 可运行 |
| `silhouette_analysis` | Silhouette Analysis | Assess cluster separation and cohesion after unsupervised segmentation. | 多个数值字段 | 目录条目 |
| `text_token_frequency` | Text Token Frequency | Summarize common terms, phrases, and sparse text signals for document collections. | field set | 目录条目 |
| `tfidf_feature_profile` | TF-IDF Feature Profile | Represent text by weighted terms that emphasize distinctive vocabulary. | field set | 目录条目 |
| `topic_model_lda` | LDA Topic Model | Discover latent topics and document-topic mixtures in text corpora. | field set | 目录条目 |
| `tsne_projection` | t-SNE Projection | Visualize local neighborhood structure in high-dimensional observations. | 多个数值字段 | 目录条目 |
| `umap_projection` | UMAP Projection | Create a nonlinear low-dimensional view of high-dimensional structure for exploration. | 多个数值字段 | 目录条目 |

### 时间序列（32 项；可运行 5 项）

| 方法 ID | 方法 | 核心问题 | 所需字段角色 | 状态 |
| --- | --- | --- | --- | --- |
| `adf_test` | Augmented Dickey-Fuller Test | 检验单位根与平稳性 | 时间字段、数值字段 | 可运行 |
| `alert_threshold_backtest` | Alert Threshold Backtest | Evaluate false positives, missed events, and stability for monitoring thresholds. | 时间字段、数值字段 | 目录条目 |
| `arima` | ARIMA | 经典单变量时间序列建模 | 时间字段、数值字段 | 目录条目 |
| `autocorrelation` | Autocorrelation Analysis | 度量滞后相关结构 | 时间字段、数值字段 | 可运行 |
| `control_chart_rule_set` | Control Chart Rule Set | Apply process-control rules for shifts, runs, trends, and out-of-control variation. | 时间字段、数值字段 | 目录条目 |
| `cross_correlation_lag` | Cross-correlation Lag Analysis | Find whether one series leads or lags another across candidate offsets. | 时间字段、数值字段、数值字段 | 目录条目 |
| `dynamic_regression` | Dynamic Regression | Model a time-series outcome with lagged or time-varying predictors. | 时间字段、数值字段、特征字段 | 目录条目 |
| `forecast_backtesting` | Forecast Backtesting | Evaluate forecast accuracy with rolling-origin or holdout-window validation. | 时间字段、数值字段 | 目录条目 |
| `forecast_residual_diagnostics` | Forecast Residual Diagnostics | Inspect forecast errors for bias, autocorrelation, changing variance, and missed seasonality. | 时间字段、数值字段 | 目录条目 |
| `freshness_sla_monitor` | Freshness SLA Monitor | Track whether data arrives within expected freshness windows. | 时间字段、full dataset | 目录条目 |
| `granger_causality` | Granger Causality Test | 检验时间序列预测因果 | 时间字段、数值字段、数值字段 | 目录条目 |
| `hidden_markov_model` | Hidden Markov Model | Infer latent regimes from observed sequential signals. | 时间字段、数值字段 | 目录条目 |
| `holt_winters` | Holt-Winters | 指数平滑预测 | 时间字段、数值字段 | 目录条目 |
| `kpss_test` | KPSS Test | 检验趋势平稳性 | 时间字段、数值字段 | 目录条目 |
| `ljung_box` | Ljung-Box Test | 检验残差白噪声性 | 时间字段、数值字段 | 可运行 |
| `longitudinal_cohort_retention` | Longitudinal Cohort Retention | Track cohort survival, repeat behavior, or retention over aligned age periods. | 时间字段、分类字段、数值字段 | 目录条目 |
| `markov_chain_analysis` | Markov Chain Analysis | Model transition probabilities between states and forecast next-state behavior. | 时间字段、分类字段 | 目录条目 |
| `metric_anomaly_root_cause` | Metric Anomaly Root Cause | Break down metric anomalies by segment, source, timing, and contributing drivers. | 时间字段、数值字段、特征字段 | 目录条目 |
| `metric_definition_drift` | Metric Definition Drift | Detect changes in metric construction, source systems, or inclusion rules over time. | 时间字段、数值字段 | 目录条目 |
| `moving_average` | Moving Average | 平滑时间波动 | 时间字段、数值字段 | 可运行 |
| `newey_west_standard_errors` | Newey-West Standard Errors | Adjust regression standard errors for autocorrelation and heteroskedasticity in ordered data. | 时间字段、数值字段、特征字段 | 目录条目 |
| `partial_autocorrelation` | Partial Autocorrelation | 识别独立滞后项 | 时间字段、数值字段 | 可运行 |
| `path_sequence_mining` | Path Sequence Mining | Discover common event sequences, transitions, and drop-off patterns. | 时间字段、分类字段 | 目录条目 |
| `prophet_style_trend` | Prophet-style Trend Model | 趋势+季节性建模 | 时间字段、数值字段 | 目录条目 |
| `quantile_forecast` | Quantile Forecast | Forecast multiple quantiles to represent uncertainty and tail risk. | 时间字段、数值字段 | 目录条目 |
| `rolling_correlation` | Rolling Correlation | Track changing association between two series across moving windows. | 时间字段、数值字段、数值字段 | 目录条目 |
| `sarima` | SARIMA | 季节性时间序列建模 | 时间字段、数值字段 | 目录条目 |
| `seasonal_baseline_anomaly` | Seasonal Baseline Anomaly | Detect anomalies relative to weekday, monthly, or seasonal expected baselines. | 时间字段、数值字段 | 目录条目 |
| `seasonal_decomposition` | Seasonal Decomposition | 拆解趋势、季节性与残差 | 时间字段、数值字段 | 目录条目 |
| `spatiotemporal_cluster_detection` | Spatiotemporal Cluster Detection | Find clusters that are localized in both geography and time. | 时间字段、entity level、数值字段 | 目录条目 |
| `state_transition_matrix` | State Transition Matrix | Summarize movement between discrete states across time or process steps. | 时间字段、分类字段 | 目录条目 |
| `stl_decomposition` | STL Decomposition | Separate a time series into trend, seasonal, and remainder components using robust local smoothing. | 时间字段、数值字段 | 目录条目 |

### 实验分析（25 项；可运行 1 项）

| 方法 ID | 方法 | 核心问题 | 所需字段角色 | 状态 |
| --- | --- | --- | --- | --- |
| `ab_test` | A/B Test | 对比实验组与控制组效果 | 分组字段、数值或二元目标 | 可运行 |
| `attrition_analysis` | Attrition Analysis | Check whether dropout, churn, or missing follow-up differs by treatment group. | 分组字段、数值或二元目标 | 目录条目 |
| `bayesian_ab_test` | Bayesian A/B Test | 贝叶斯实验比较 | 分组字段、数值或二元目标 | 目录条目 |
| `bayesian_bandit_policy` | Bayesian Bandit Policy | Allocate traffic using posterior uncertainty, exploration, and exploitation tradeoffs. | 分组字段、数值或二元目标 | 目录条目 |
| `bucketed_ratio_metric` | Bucketed Ratio Metric | Evaluate ratio metrics by aggregating observations into independent buckets. | 分组字段、数值或二元目标 | 目录条目 |
| `carryover_effect_check` | Carryover Effect Check | Detect whether earlier treatment exposure contaminates later measurement windows. | 时间字段、分组字段、数值或二元目标 | 目录条目 |
| `cuped_adjustment` | CUPED Adjustment | Use pre-experiment covariates to reduce variance in randomized experiment estimates. | 分组字段、结果字段、特征字段 | 目录条目 |
| `experiment_guardrail_metrics` | Experiment Guardrail Metrics | Track secondary safety metrics before accepting an experiment winner. | 分组字段、数值或二元目标 | 目录条目 |
| `factorial_experiment` | Factorial Experiment | Estimate main effects and interactions across multiple experimental factors. | 分组字段、结果字段、特征字段 | 目录条目 |
| `geo_experiment_design` | Geo Experiment Design | Plan geographically assigned experiments with spillover, balance, and measurement constraints. | entity level、分组结构 | 目录条目 |
| `incrementality_holdout` | Incrementality Holdout | Reserve a holdout group to estimate incremental impact of campaigns or interventions. | 分组字段、数值或二元目标 | 目录条目 |
| `metric_sensitivity_analysis` | Metric Sensitivity Analysis | Compare candidate outcome metrics by variance, skew, responsiveness, and business relevance. | 分组字段、数值或二元目标 | 目录条目 |
| `minimum_detectable_effect` | Minimum Detectable Effect | Estimate the smallest effect an experiment can reliably detect with available sample size. | 分组字段、数值或二元目标 | 目录条目 |
| `multi_arm_bandit` | Multi-arm Bandit | Adapt traffic allocation while balancing learning and reward. | 分组字段、数值或二元目标 | 目录条目 |
| `number_needed_to_treat` | Number Needed to Treat | Translate absolute effect into the number of treated units needed for one additional desired outcome. | 分组字段、二元字段 | 目录条目 |
| `peeking_risk_audit` | Peeking Risk Audit | Document repeated looks, optional stopping, and inflated false-positive risk. | 分组字段、数值或二元目标 | 目录条目 |
| `power_curve_analysis` | Power Curve Analysis | Show how detectable effect changes across sample sizes, alpha levels, and variance assumptions. | 效应量 | 目录条目 |
| `sample_ratio_mismatch` | Sample Ratio Mismatch | Detect assignment imbalance that may indicate instrumentation or randomization failures. | 分组字段、数值或二元目标 | 目录条目 |
| `sample_size_power` | Sample Size / Power Analysis | 估算实验所需样本量 | 效应量 | 目录条目 |
| `sequential_bayesian_monitoring` | Sequential Bayesian Monitoring | Monitor accumulating experimental evidence using posterior probabilities and decision thresholds. | 分组字段、数值或二元目标 | 目录条目 |
| `sequential_test` | Sequential Test | 逐步监控实验结果 | 分组字段、数值或二元目标 | 目录条目 |
| `stratified_randomization` | Stratified Randomization | Plan or audit randomized assignment within important strata. | 分组字段、特征字段 | 目录条目 |
| `switchback_experiment_design` | Switchback Experiment Design | Plan experiments that alternate treatment over time for marketplace, logistics, or operational systems. | 时间字段、分组字段、数值或二元目标 | 目录条目 |
| `uplift_evaluation_qini` | Qini Uplift Evaluation | Evaluate targeting models by incremental gain across ranked treatment scores. | 分组字段、结果字段、特征字段 | 目录条目 |
| `uplift_modeling` | Uplift Modeling | 识别处理效应异质性 | 分组字段、结果字段、特征字段 | 目录条目 |

### 因果探查（14 项；可运行 0 项）

| 方法 ID | 方法 | 核心问题 | 所需字段角色 | 状态 |
| --- | --- | --- | --- | --- |
| `causal_forest` | Causal Forest | Estimate heterogeneous treatment effects with tree-based causal modeling. | 分组字段、结果字段、特征字段 | 目录条目 |
| `dag_assumption_review` | DAG Assumption Review | Document causal assumptions, confounders, mediators, colliders, and adjustment sets before estimation. | 目标字段、特征字段 | 目录条目 |
| `double_machine_learning` | Double Machine Learning | Use nuisance models and orthogonalization to estimate causal effects with many controls. | 分组字段、结果字段、特征字段 | 目录条目 |
| `doubly_robust_estimation` | Doubly Robust Estimation | Combine outcome modeling and propensity weighting for treatment-effect estimation. | 分组字段、结果字段、特征字段 | 目录条目 |
| `heterogeneous_treatment_effects` | Heterogeneous Treatment Effects | Find segments where treatment impact differs meaningfully. | 分组字段、结果字段、特征字段 | 目录条目 |
| `instrumental_variables` | Instrumental Variables | Estimate causal effects using external variation when ordinary regression is confounded. | 目标字段、特征字段 | 目录条目 |
| `inverse_probability_weighting` | Inverse Probability Weighting | Reweight observations to estimate treatment effects under observed-confounder adjustment. | 分组字段、结果字段、特征字段 | 目录条目 |
| `negative_control_exposure` | Negative Control Exposure | Use an exposure that should not affect the outcome to reveal confounding or measurement artifacts. | 目标字段、特征字段 | 目录条目 |
| `negative_control_outcome` | Negative Control Outcome | Use an outcome that should not be affected to detect hidden bias in a causal design. | 目标字段、特征字段 | 目录条目 |
| `placebo_test` | Placebo Test | Check whether a causal design detects effects where no true effect should exist. | 目标字段、特征字段 | 目录条目 |
| `propensity_score_matching` | Propensity Score Matching | Match treated and comparison units using estimated treatment propensity. | 分组字段、结果字段、特征字段 | 目录条目 |
| `regression_discontinuity` | Regression Discontinuity | Estimate local causal effects around an assignment threshold. | 目标字段、特征字段 | 目录条目 |
| `spillover_interference_audit` | Spillover / Interference Audit | Assess whether treatment assigned to one unit may affect other units and violate independence. | 分组字段、结果字段、特征字段 | 目录条目 |
| `unobserved_confounding_sensitivity` | Unobserved Confounding Sensitivity | Assess how strong hidden confounding would need to be to overturn a causal conclusion. | 目标字段、特征字段 | 目录条目 |

### 面板因果（14 项；可运行 0 项）

| 方法 ID | 方法 | 核心问题 | 所需字段角色 | 状态 |
| --- | --- | --- | --- | --- |
| `bayesian_hierarchical_model` | Bayesian Hierarchical Model | Pool information across groups while allowing group-specific uncertainty and shrinkage. | 分组数值结构 | 目录条目 |
| `did` | Difference-in-Differences | 前后变化差异因果估计 | 时间字段、分组字段、数值字段 | 目录条目 |
| `event_study_design` | Event Study Design | Estimate pre-trends and post-event dynamics around treatment or policy timing. | 时间字段、分组字段、数值字段 | 目录条目 |
| `gee` | Generalized Estimating Equations | 相关样本广义线性建模 | 分组数值结构 | 目录条目 |
| `interrupted_time_series` | Interrupted Time Series | 评估政策/事件冲击 | 时间字段、数值字段 | 目录条目 |
| `mixed_effects_model` | Mixed Effects Model | 处理层级和重复测量结构 | 分组数值结构 | 目录条目 |
| `mixed_effects_random_intercepts` | Mixed Effects Random Intercepts | Model grouped observations with cluster-specific baselines. | 分组数值结构 | 目录条目 |
| `mixed_effects_random_slopes` | Mixed Effects Random Slopes | Allow predictor effects to vary across groups, sites, users, or repeated-measure units. | 分组数值结构 | 目录条目 |
| `multilevel_poststratification` | Multilevel Regression and Poststratification | Combine multilevel models with population margins to estimate representative subgroup outcomes. | 分组数值结构 | 目录条目 |
| `panel_fixed_effects` | Panel Fixed Effects | 控制个体不变异质性 | 面板标识、数值字段 | 目录条目 |
| `panel_random_effects` | Panel Random Effects | 随机效应面板建模 | 面板标识、数值字段 | 目录条目 |
| `parallel_trends_diagnostic` | Parallel Trends Diagnostic | Check whether treated and control groups followed similar pre-treatment trends. | 时间字段、分组字段、数值字段 | 目录条目 |
| `synthetic_control` | Synthetic Control | 构造合成对照组 | 时间字段、面板标识 | 目录条目 |
| `synthetic_difference_in_differences` | Synthetic Difference-in-Differences | Combine weighting and difference-in-differences for panel treatment evaluation. | 时间字段、面板标识 | 目录条目 |

### 生存分析（13 项；可运行 0 项）

| 方法 ID | 方法 | 核心问题 | 所需字段角色 | 状态 |
| --- | --- | --- | --- | --- |
| `accelerated_failure_time` | Accelerated Failure Time Model | 建模事件发生速度 | 生存时长、特征字段 | 目录条目 |
| `competing_event_retention` | Competing Event Retention | Analyze retention when multiple mutually exclusive event types can occur. | 生存时长、事件类型 | 目录条目 |
| `competing_risks` | Competing Risks Model | 多事件类型生存分析 | 生存时长、事件类型 | 目录条目 |
| `cox_ph` | Cox Proportional Hazards | 生存风险回归 | 生存时长、特征字段 | 目录条目 |
| `cumulative_incidence_curve` | Cumulative Incidence Curve | Estimate event probability over time when competing risks may exist. | 生存时长、事件类型 | 目录条目 |
| `kaplan_meier` | Kaplan-Meier Estimator | 估计生存曲线 | 生存时长 | 目录条目 |
| `log_rank_test` | Log-rank Test | 比较两组生存曲线 | 生存时长、分组字段 | 目录条目 |
| `multi_state_survival_model` | Multi-state Survival Model | Model transitions among states over time with censoring and event histories. | 生存时长、事件类型 | 目录条目 |
| `nelson_aalen` | Nelson-Aalen Estimator | 累积风险估计 | 生存时长 | 目录条目 |
| `proportional_hazards_check` | Proportional Hazards Check | Assess whether Cox model hazard-ratio assumptions are plausible over follow-up time. | 生存时长、特征字段 | 目录条目 |
| `survival_censoring_audit` | Survival Censoring Audit | Inspect censoring patterns before survival-curve or hazard modeling. | 生存时长、分组字段 | 目录条目 |
| `survival_retention_model` | Survival Retention Model | Model time to churn, repeat use, failure, or reactivation with censoring-aware methods. | 生存时长、特征字段 | 目录条目 |
| `time_dependent_covariates` | Time-dependent Covariates | Model survival outcomes when predictors change during follow-up. | 生存时长、特征字段 | 目录条目 |

### 心理测量（8 项；可运行 0 项）

| 方法 ID | 方法 | 核心问题 | 所需字段角色 | 状态 |
| --- | --- | --- | --- | --- |
| `item_response_theory` | Item Response Theory | 题项反应建模 | item response | 目录条目 |
| `latent_growth_model` | Latent Growth Model | 建模潜在成长轨迹 | 重复测量结构 | 目录条目 |
| `measurement_invariance` | Measurement Invariance | 检验量表跨组可比性 | 多组量表 | 目录条目 |
| `mediation_analysis` | Mediation Analysis | 检验中介路径 | 自变量、中介变量、因变量 | 目录条目 |
| `moderation_analysis` | Moderation Analysis | 检验调节效应 | 自变量、调节变量、因变量 | 目录条目 |
| `reliability_cronbach_alpha` | Cronbach Alpha | 量表内部一致性 | 多题项量表 | 目录条目 |
| `sem` | Structural Equation Modeling | 结构方程模型 | 多个数值字段、潜变量 | 目录条目 |
| `split_half_reliability` | Split-half Reliability | 半分信度 | 多题项量表 | 目录条目 |

### 统计推断与稳健性（18 项；可运行 0 项）

| 方法 ID | 方法 | 核心问题 | 所需字段角色 | 状态 |
| --- | --- | --- | --- | --- |
| `analysis_lineage_map` | Analysis Lineage Map | Trace how raw fields, derived metrics, methods, and report claims connect. | full dataset | 目录条目 |
| `bayes_factor_model_comparison` | Bayes Factor Model Comparison | Compare evidence for competing hypotheses or models on a Bayesian evidence scale. | 目标字段、特征字段 | 目录条目 |
| `bayesian_credible_effect` | Bayesian Credible Effect | Report probability that an effect exceeds a practical threshold using posterior draws. | 目标字段、特征字段 | 目录条目 |
| `bayesian_interval_summary` | Bayesian Interval Summary | Describe posterior uncertainty with credible intervals and probability statements. | 数值字段 | 目录条目 |
| `bayesian_posterior_predictive_check` | Bayesian Posterior Predictive Check | Compare observed data with simulations from the fitted posterior model. | 目标字段、特征字段 | 目录条目 |
| `bayesian_prior_predictive_check` | Bayesian Prior Predictive Check | Simulate from priors to verify that assumptions generate plausible data before observing outcomes. | 目标字段、特征字段 | 目录条目 |
| `confidence_interval_summary` | Confidence Interval Summary | Summarize uncertainty intervals around means, proportions, effects, or model estimates. | 数值字段 | 目录条目 |
| `differential_privacy_budget` | Differential Privacy Budget | Plan epsilon, delta, query sensitivity, and composition for privacy-preserving releases. | full dataset | 目录条目 |
| `empirical_bayes_shrinkage` | Empirical Bayes Shrinkage | Stabilize noisy group estimates by shrinking them toward a shared prior distribution. | 数值字段、分组结构 | 目录条目 |
| `false_discovery_rate` | False Discovery Rate Control | Control expected false discoveries when screening many hypotheses or features. | field set | 目录条目 |
| `finite_population_correction` | Finite Population Correction | Adjust uncertainty estimates when sampling without replacement from a small finite population. | 数值字段 | 目录条目 |
| `margin_of_error` | Margin of Error | Translate sample size and variability into an interpretable uncertainty range. | 数值字段 | 目录条目 |
| `multiple_testing_correction` | Multiple Testing Correction | Adjust inference when many comparisons are made in the same analysis run. | field set | 目录条目 |
| `ratio_metric_delta_method` | Ratio Metric Delta Method | Approximate uncertainty for ratio metrics such as conversion rate, revenue per user, or defect rate. | field pair | 目录条目 |
| `reproducibility_audit` | Reproducibility Audit | Check whether data, code, parameters, random seeds, and outputs can be rerun consistently. | full dataset | 目录条目 |
| `robustness_grid` | Robustness Grid | Summarize how conclusions change across alternative filters, transformations, models, and assumptions. | field set | 目录条目 |
| `sensitivity_to_missing_data` | Sensitivity to Missing Data | Compare conclusions under complete-case, imputed, and missingness-aware analyses. | field set | 目录条目 |
| `sensitivity_to_outliers` | Sensitivity to Outliers | Compare results before and after outlier exclusion, winsorization, or robust estimation. | field set | 目录条目 |

### 差异比较（3 项；可运行 0 项）

| 方法 ID | 方法 | 核心问题 | 所需字段角色 | 状态 |
| --- | --- | --- | --- | --- |
| `cohens_d_effect_size` | Cohen's d Effect Size | Quantify standardized mean difference so a report can separate practical magnitude from p-value significance. | 数值字段、二元分组 | 目录条目 |
| `glass_delta_effect_size` | Glass Delta Effect Size | Measure mean difference using the control group's standard deviation when group variances differ. | 数值字段、二元分组 | 目录条目 |
| `hedges_g_effect_size` | Hedges g Effect Size | Estimate standardized mean difference with small-sample correction. | 数值字段、二元分组 | 目录条目 |

### 报告部件（1 项；可运行 0 项）

| 方法 ID | 方法 | 核心问题 | 所需字段角色 | 状态 |
| --- | --- | --- | --- | --- |
| `explainable_dashboard_narrative` | Explainable Dashboard Narrative | Turn metrics, diagnostics, and method outputs into a transparent dashboard explanation section. | full dataset | 目录条目 |
