# Analysis Lab 方法卡索引

> 本文档由 `scripts/export_method_catalog_docs.py` 生成，记录当前 Lab 注册表中的全部方法卡。

## 运行状态

- 方法卡总数：`4028`
- 可运行：`273`
- 目录条目：`1023`
- 规划条目：`2732`
- API：`GET /api/lab/methods?compact=true`；全量字段可通过 `compact=false` 获取。

## 使用约定

每张方法卡保存方法身份、字段角色、可选运行模式与产物合约。`live` 卡可在 Lab 中绑定数据集字段并运行；卡片产物按方法契约输出 JSON、CSV、XLSX、Markdown，部分方法额外提供图表、SVG、HTML 或图像规格。

## 全量方法卡

### 关联分析（56 张；可运行 27 张）

| 卡片 ID | 方法概念 | 输出形态 | 字段角色 | 状态 | 来源 |
| --- | --- | --- | --- | --- | --- |
| `association_correlation` | 相关性 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `association_distance` | 距离 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `association_mutual_information` | 互信息 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `association_network` | 关系网络 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `association_partial` | 偏相关 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `canonical_correlation_data` | Canonical Correlation | 结构化数据 | multi numeric、multi numeric | 目录条目 | statistical_catalog |
| `canonical_correlation_table` | Canonical Correlation | 表格 | multi numeric、multi numeric | 目录条目 | statistical_catalog |
| `canonical_correlation_text` | Canonical Correlation | 文字解读 | multi numeric、multi numeric | 目录条目 | statistical_catalog |
| `cooccurrence_network_analysis_data` | Co-occurrence Network Analysis | 结构化数据 | 字段组 | 目录条目 | statistical_catalog |
| `cooccurrence_network_analysis_table` | Co-occurrence Network Analysis | 表格 | 字段组 | 目录条目 | statistical_catalog |
| `cooccurrence_network_analysis_text` | Co-occurrence Network Analysis | 文字解读 | 字段组 | 目录条目 | statistical_catalog |
| `correlation_chart` | Correlation Matrix | 图表 | multi numeric | 可运行 | statistical_catalog |
| `correlation_data` | Correlation Matrix | 结构化数据 | multi numeric | 可运行 | statistical_catalog |
| `correlation_image_spec` | Correlation Matrix | 图片规格 | multi numeric | 可运行 | statistical_catalog |
| `correlation_report_section` | Correlation Matrix | 报告段落 | multi numeric | 可运行 | statistical_catalog |
| `correlation_table` | Correlation Matrix | 表格 | multi numeric | 可运行 | statistical_catalog |
| `correlation_text` | Correlation Matrix | 文字解读 | multi numeric | 可运行 | statistical_catalog |
| `distance_correlation_data` | Distance Correlation | 结构化数据 | 数值字段、数值字段 | 可运行 | statistical_catalog |
| `distance_correlation_table` | Distance Correlation | 表格 | 数值字段、数值字段 | 可运行 | statistical_catalog |
| `distance_correlation_text` | Distance Correlation | 文字解读 | 数值字段、数值字段 | 可运行 | statistical_catalog |
| `eta_squared_data` | Eta Squared | 结构化数据 | 分类字段、数值字段 | 可运行 | statistical_catalog |
| `eta_squared_table` | Eta Squared | 表格 | 分类字段、数值字段 | 可运行 | statistical_catalog |
| `eta_squared_text` | Eta Squared | 文字解读 | 分类字段、数值字段 | 可运行 | statistical_catalog |
| `intraclass_correlation_data` | Intraclass Correlation | 结构化数据 | 数值字段、分组 | 目录条目 | statistical_catalog |
| `intraclass_correlation_table` | Intraclass Correlation | 表格 | 数值字段、分组 | 目录条目 | statistical_catalog |
| `intraclass_correlation_text` | Intraclass Correlation | 文字解读 | 数值字段、分组 | 目录条目 | statistical_catalog |
| `kendall_tau_data` | Kendall Tau | 结构化数据 | 数值字段、数值字段 | 可运行 | statistical_catalog |
| `kendall_tau_table` | Kendall Tau | 表格 | 数值字段、数值字段 | 可运行 | statistical_catalog |
| `kendall_tau_text` | Kendall Tau | 文字解读 | 数值字段、数值字段 | 可运行 | statistical_catalog |
| `moran_i_spatial_autocorrelation_data` | Moran's I Spatial Autocorrelation | 结构化数据 | 对象级、数值字段 | 目录条目 | statistical_catalog |
| `moran_i_spatial_autocorrelation_table` | Moran's I Spatial Autocorrelation | 表格 | 对象级、数值字段 | 目录条目 | statistical_catalog |
| `moran_i_spatial_autocorrelation_text` | Moran's I Spatial Autocorrelation | 文字解读 | 对象级、数值字段 | 目录条目 | statistical_catalog |
| `mutual_information_data` | Mutual Information | 结构化数据 | numeric or categorical、numeric or categorical | 目录条目 | statistical_catalog |
| `mutual_information_table` | Mutual Information | 表格 | numeric or categorical、numeric or categorical | 目录条目 | statistical_catalog |
| `mutual_information_text` | Mutual Information | 文字解读 | numeric or categorical、numeric or categorical | 目录条目 | statistical_catalog |
| `nearest_neighbor_spatial_search_data` | Nearest-neighbor Spatial Search | 结构化数据 | 对象级 | 目录条目 | statistical_catalog |
| `nearest_neighbor_spatial_search_table` | Nearest-neighbor Spatial Search | 表格 | 对象级 | 目录条目 | statistical_catalog |
| `nearest_neighbor_spatial_search_text` | Nearest-neighbor Spatial Search | 文字解读 | 对象级 | 目录条目 | statistical_catalog |
| `network_assortativity_data` | Network Assortativity | 结构化数据 | 对象级、分组 | 目录条目 | statistical_catalog |
| `network_assortativity_table` | Network Assortativity | 表格 | 对象级、分组 | 目录条目 | statistical_catalog |
| `network_assortativity_text` | Network Assortativity | 文字解读 | 对象级、分组 | 目录条目 | statistical_catalog |
| `partial_correlation_data` | Partial Correlation | 结构化数据 | 数值字段、数值字段、covariate | 可运行 | statistical_catalog |
| `partial_correlation_table` | Partial Correlation | 表格 | 数值字段、数值字段、covariate | 可运行 | statistical_catalog |
| `partial_correlation_text` | Partial Correlation | 文字解读 | 数值字段、数值字段、covariate | 可运行 | statistical_catalog |
| `pearson_correlation_data` | Pearson Correlation | 结构化数据 | 数值字段、数值字段 | 可运行 | statistical_catalog |
| `pearson_correlation_table` | Pearson Correlation | 表格 | 数值字段、数值字段 | 可运行 | statistical_catalog |
| `pearson_correlation_text` | Pearson Correlation | 文字解读 | 数值字段、数值字段 | 可运行 | statistical_catalog |
| `point_biserial_data` | Point-Biserial Correlation | 结构化数据 | 数值字段、binary | 可运行 | statistical_catalog |
| `point_biserial_table` | Point-Biserial Correlation | 表格 | 数值字段、binary | 可运行 | statistical_catalog |
| `point_biserial_text` | Point-Biserial Correlation | 文字解读 | 数值字段、binary | 可运行 | statistical_catalog |
| `spearman_correlation_data` | Spearman Correlation | 结构化数据 | 数值字段、数值字段 | 可运行 | statistical_catalog |
| `spearman_correlation_table` | Spearman Correlation | 表格 | 数值字段、数值字段 | 可运行 | statistical_catalog |
| `spearman_correlation_text` | Spearman Correlation | 文字解读 | 数值字段、数值字段 | 可运行 | statistical_catalog |
| `text_embedding_similarity_data` | Text Embedding Similarity | 结构化数据 | 字段对 | 目录条目 | statistical_catalog |
| `text_embedding_similarity_table` | Text Embedding Similarity | 表格 | 字段对 | 目录条目 | statistical_catalog |
| `text_embedding_similarity_text` | Text Embedding Similarity | 文字解读 | 字段对 | 目录条目 | statistical_catalog |

### 分布假设（54 张；可运行 36 张）

| 卡片 ID | 方法概念 | 输出形态 | 字段角色 | 状态 | 来源 |
| --- | --- | --- | --- | --- | --- |
| `anderson_darling_data` | Anderson-Darling Test | 结构化数据 | 数值字段 | 可运行 | statistical_catalog |
| `anderson_darling_table` | Anderson-Darling Test | 表格 | 数值字段 | 可运行 | statistical_catalog |
| `anderson_darling_text` | Anderson-Darling Test | 文字解读 | 数值字段 | 可运行 | statistical_catalog |
| `bartlett_data` | Bartlett Test | 结构化数据 | 数值字段、分类字段 | 可运行 | statistical_catalog |
| `bartlett_table` | Bartlett Test | 表格 | 数值字段、分类字段 | 可运行 | statistical_catalog |
| `bartlett_text` | Bartlett Test | 文字解读 | 数值字段、分类字段 | 可运行 | statistical_catalog |
| `box_m_test_data` | Box's M Test | 结构化数据 | multi numeric、分类字段 | 目录条目 | statistical_catalog |
| `box_m_test_table` | Box's M Test | 表格 | multi numeric、分类字段 | 目录条目 | statistical_catalog |
| `box_m_test_text` | Box's M Test | 文字解读 | multi numeric、分类字段 | 目录条目 | statistical_catalog |
| `breusch_pagan_data` | Breusch-Pagan Test | 结构化数据 | 数值字段、数值字段 | 可运行 | statistical_catalog |
| `breusch_pagan_table` | Breusch-Pagan Test | 表格 | 数值字段、数值字段 | 可运行 | statistical_catalog |
| `breusch_pagan_text` | Breusch-Pagan Test | 文字解读 | 数值字段、数值字段 | 可运行 | statistical_catalog |
| `brown_forsythe_data` | Brown-Forsythe Test | 结构化数据 | 数值字段、分类字段 | 可运行 | statistical_catalog |
| `brown_forsythe_table` | Brown-Forsythe Test | 表格 | 数值字段、分类字段 | 可运行 | statistical_catalog |
| `brown_forsythe_text` | Brown-Forsythe Test | 文字解读 | 数值字段、分类字段 | 可运行 | statistical_catalog |
| `dagostino_k2_data` | D'Agostino K^2 Test | 结构化数据 | 数值字段 | 可运行 | statistical_catalog |
| `dagostino_k2_table` | D'Agostino K^2 Test | 表格 | 数值字段 | 可运行 | statistical_catalog |
| `dagostino_k2_text` | D'Agostino K^2 Test | 文字解读 | 数值字段 | 可运行 | statistical_catalog |
| `durbin_watson_data` | Durbin-Watson | 结构化数据 | 数值字段、数值字段 | 可运行 | statistical_catalog |
| `durbin_watson_table` | Durbin-Watson | 表格 | 数值字段、数值字段 | 可运行 | statistical_catalog |
| `durbin_watson_text` | Durbin-Watson | 文字解读 | 数值字段、数值字段 | 可运行 | statistical_catalog |
| `jarque_bera_data` | Jarque-Bera Test | 结构化数据 | 数值字段 | 可运行 | statistical_catalog |
| `jarque_bera_table` | Jarque-Bera Test | 表格 | 数值字段 | 可运行 | statistical_catalog |
| `jarque_bera_text` | Jarque-Bera Test | 文字解读 | 数值字段 | 可运行 | statistical_catalog |
| `kolmogorov_smirnov_1samp_data` | One-sample KS Test | 结构化数据 | 数值字段 | 可运行 | statistical_catalog |
| `kolmogorov_smirnov_1samp_table` | One-sample KS Test | 表格 | 数值字段 | 可运行 | statistical_catalog |
| `kolmogorov_smirnov_1samp_text` | One-sample KS Test | 文字解读 | 数值字段 | 可运行 | statistical_catalog |
| `levene_data` | Levene Test | 结构化数据 | 数值字段、分类字段 | 可运行 | statistical_catalog |
| `levene_table` | Levene Test | 表格 | 数值字段、分类字段 | 可运行 | statistical_catalog |
| `levene_text` | Levene Test | 文字解读 | 数值字段、分类字段 | 可运行 | statistical_catalog |
| `mauchly_sphericity_data` | Mauchly Sphericity Test | 结构化数据 | 数值字段、within subject factor | 目录条目 | statistical_catalog |
| `mauchly_sphericity_table` | Mauchly Sphericity Test | 表格 | 数值字段、within subject factor | 目录条目 | statistical_catalog |
| `mauchly_sphericity_text` | Mauchly Sphericity Test | 文字解读 | 数值字段、within subject factor | 目录条目 | statistical_catalog |
| `normality_data` | Normality Test | 结构化数据 | 数值字段 | 可运行 | statistical_catalog |
| `normality_table` | Normality Test | 表格 | 数值字段 | 可运行 | statistical_catalog |
| `normality_text` | Normality Test | 文字解读 | 数值字段 | 可运行 | statistical_catalog |
| `overdispersion_diagnostic_data` | Overdispersion Diagnostic | 结构化数据 | count | 目录条目 | statistical_catalog |
| `overdispersion_diagnostic_table` | Overdispersion Diagnostic | 表格 | count | 目录条目 | statistical_catalog |
| `overdispersion_diagnostic_text` | Overdispersion Diagnostic | 文字解读 | count | 目录条目 | statistical_catalog |
| `qq_diagnostic_review_data` | Q-Q Diagnostic Review | 结构化数据 | 数值字段 | 目录条目 | statistical_catalog |
| `qq_diagnostic_review_table` | Q-Q Diagnostic Review | 表格 | 数值字段 | 目录条目 | statistical_catalog |
| `qq_diagnostic_review_text` | Q-Q Diagnostic Review | 文字解读 | 数值字段 | 目录条目 | statistical_catalog |
| `shapiro_wilk_data` | Shapiro-Wilk Test | 结构化数据 | 数值字段 | 可运行 | statistical_catalog |
| `shapiro_wilk_table` | Shapiro-Wilk Test | 表格 | 数值字段 | 可运行 | statistical_catalog |
| `shapiro_wilk_text` | Shapiro-Wilk Test | 文字解读 | 数值字段 | 可运行 | statistical_catalog |
| `skewness_kurtosis_profile_data` | Skewness / Kurtosis Profile | 结构化数据 | 数值字段 | 目录条目 | statistical_catalog |
| `skewness_kurtosis_profile_table` | Skewness / Kurtosis Profile | 表格 | 数值字段 | 目录条目 | statistical_catalog |
| `skewness_kurtosis_profile_text` | Skewness / Kurtosis Profile | 文字解读 | 数值字段 | 目录条目 | statistical_catalog |
| `white_test_data` | White Test | 结构化数据 | 数值字段、数值字段 | 可运行 | statistical_catalog |
| `white_test_table` | White Test | 表格 | 数值字段、数值字段 | 可运行 | statistical_catalog |
| `white_test_text` | White Test | 文字解读 | 数值字段、数值字段 | 可运行 | statistical_catalog |
| `zero_inflation_diagnostic_data` | Zero-inflation Diagnostic | 结构化数据 | 数值字段 | 目录条目 | statistical_catalog |
| `zero_inflation_diagnostic_table` | Zero-inflation Diagnostic | 表格 | 数值字段 | 目录条目 | statistical_catalog |
| `zero_inflation_diagnostic_text` | Zero-inflation Diagnostic | 文字解读 | 数值字段 | 目录条目 | statistical_catalog |

### 分类关联（39 张；可运行 30 张）

| 卡片 ID | 方法概念 | 输出形态 | 字段角色 | 状态 | 来源 |
| --- | --- | --- | --- | --- | --- |
| `chi_square_data` | Chi-square Test | 结构化数据 | 分类字段、分类字段 | 可运行 | statistical_catalog |
| `chi_square_table` | Chi-square Test | 表格 | 分类字段、分类字段 | 可运行 | statistical_catalog |
| `chi_square_text` | Chi-square Test | 文字解读 | 分类字段、分类字段 | 可运行 | statistical_catalog |
| `cmh_test_data` | Cochran-Mantel-Haenszel Test | 结构化数据 | 分类字段、分类字段、strata | 可运行 | statistical_catalog |
| `cmh_test_table` | Cochran-Mantel-Haenszel Test | 表格 | 分类字段、分类字段、strata | 可运行 | statistical_catalog |
| `cmh_test_text` | Cochran-Mantel-Haenszel Test | 文字解读 | 分类字段、分类字段、strata | 可运行 | statistical_catalog |
| `cochran_q_data` | Cochran Q Test | 结构化数据 | binary、within subject factor | 可运行 | statistical_catalog |
| `cochran_q_table` | Cochran Q Test | 表格 | binary、within subject factor | 可运行 | statistical_catalog |
| `cochran_q_text` | Cochran Q Test | 文字解读 | binary、within subject factor | 可运行 | statistical_catalog |
| `cohens_kappa_data` | Cohen's Kappa | 结构化数据 | 分类字段、paired | 可运行 | statistical_catalog |
| `cohens_kappa_table` | Cohen's Kappa | 表格 | 分类字段、paired | 可运行 | statistical_catalog |
| `cohens_kappa_text` | Cohen's Kappa | 文字解读 | 分类字段、paired | 可运行 | statistical_catalog |
| `cramers_v_data` | Cramer's V | 结构化数据 | 分类字段、分类字段 | 可运行 | statistical_catalog |
| `cramers_v_table` | Cramer's V | 表格 | 分类字段、分类字段 | 可运行 | statistical_catalog |
| `cramers_v_text` | Cramer's V | 文字解读 | 分类字段、分类字段 | 可运行 | statistical_catalog |
| `fisher_exact_data` | Fisher Exact Test | 结构化数据 | 分类字段、分类字段 | 可运行 | statistical_catalog |
| `fisher_exact_table` | Fisher Exact Test | 表格 | 分类字段、分类字段 | 可运行 | statistical_catalog |
| `fisher_exact_text` | Fisher Exact Test | 文字解读 | 分类字段、分类字段 | 可运行 | statistical_catalog |
| `goodman_kruskal_lambda_data` | Goodman-Kruskal Lambda | 结构化数据 | 分类字段、分类字段 | 可运行 | statistical_catalog |
| `goodman_kruskal_lambda_table` | Goodman-Kruskal Lambda | 表格 | 分类字段、分类字段 | 可运行 | statistical_catalog |
| `goodman_kruskal_lambda_text` | Goodman-Kruskal Lambda | 文字解读 | 分类字段、分类字段 | 可运行 | statistical_catalog |
| `mcnemar_data` | McNemar Test | 结构化数据 | binary、paired | 可运行 | statistical_catalog |
| `mcnemar_table` | McNemar Test | 表格 | binary、paired | 可运行 | statistical_catalog |
| `mcnemar_text` | McNemar Test | 文字解读 | binary、paired | 可运行 | statistical_catalog |
| `odds_ratio_data` | Odds Ratio | 结构化数据 | binary、binary | 目录条目 | statistical_catalog |
| `odds_ratio_table` | Odds Ratio | 表格 | binary、binary | 目录条目 | statistical_catalog |
| `odds_ratio_text` | Odds Ratio | 文字解读 | binary、binary | 目录条目 | statistical_catalog |
| `phi_coefficient_data` | Phi Coefficient | 结构化数据 | binary、binary | 可运行 | statistical_catalog |
| `phi_coefficient_table` | Phi Coefficient | 表格 | binary、binary | 可运行 | statistical_catalog |
| `phi_coefficient_text` | Phi Coefficient | 文字解读 | binary、binary | 可运行 | statistical_catalog |
| `relative_risk_data` | Relative Risk | 结构化数据 | binary、binary | 目录条目 | statistical_catalog |
| `relative_risk_table` | Relative Risk | 表格 | binary、binary | 目录条目 | statistical_catalog |
| `relative_risk_text` | Relative Risk | 文字解读 | binary、binary | 目录条目 | statistical_catalog |
| `risk_difference_data` | Risk Difference | 结构化数据 | binary、binary | 目录条目 | statistical_catalog |
| `risk_difference_table` | Risk Difference | 表格 | binary、binary | 目录条目 | statistical_catalog |
| `risk_difference_text` | Risk Difference | 文字解读 | binary、binary | 目录条目 | statistical_catalog |
| `theils_u_data` | Theil's U | 结构化数据 | 分类字段、分类字段 | 可运行 | statistical_catalog |
| `theils_u_table` | Theil's U | 表格 | 分类字段、分类字段 | 可运行 | statistical_catalog |
| `theils_u_text` | Theil's U | 文字解读 | 分类字段、分类字段 | 可运行 | statistical_catalog |

### 可视化（2685 张；可运行 0 张）

| 卡片 ID | 方法概念 | 输出形态 | 字段角色 | 状态 | 来源 |
| --- | --- | --- | --- | --- | --- |
| `visual_alluvial` | 河流图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_area` | 面积图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_bar` | 条形图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_beeswarm` | 蜂群图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_boxplot` | 箱线图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_bubble` | 气泡图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_bullet` | 子弹图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_bump_chart` | 排名趋势图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_calendar_heatmap` | 日历热力图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_candlestick` | 蜁烛图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_chord` | 弦图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_choropleth` | 分级着色地图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_cohort_matrix` | 队列矩阵 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_column` | 柱状图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_contour` | 等高线图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_control_chart` | 控制图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_density` | 密度图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_ecdf` | 经验分布图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_flow_map` | 流向地图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_funnel` | 漏斗图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_gauge` | 仪表盘 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_geo_map` | 地理地图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_heatmap` | 热力矩阵 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_hexbin` | 六边形密度图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_histogram` | 直方图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_line` | 折线图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_marimekko` | 马赛克图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_network` | 关系网络 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_pairplot` | 成对散点矩阵 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_parallel_coordinates` | 平行坐标图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_qqplot` | 正态 Q-Q 图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_quadrant` | 象限图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_radar` | 雷达图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_sankey` | 桑基图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_scatter` | 散点图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_slopegraph` | 坡度图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_small_multiple` | 小多图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_sparkline` | 迷你趋势线 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_stacked_area` | 堆积面积图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_stat_agreement_reliability_annotated_reference_view` | Agreement reliability - Annotated reference view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_agreement_reliability_boxen_interval` | Agreement reliability - Boxen interval plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_agreement_reliability_comparative_lollipop` | Agreement reliability - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_agreement_reliability_density_ridge` | 密度图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_agreement_reliability_diagnostic_panel` | Agreement reliability - Diagnostic panel | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_agreement_reliability_ecdf_step_view` | 经验分布图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_agreement_reliability_flow_transition_map` | Agreement reliability - Flow transition map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_agreement_reliability_forest_interval_plot` | 随机森林 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_agreement_reliability_heatmap_matrix` | 热力矩阵 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_agreement_reliability_histogram_facets` | 直方图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_agreement_reliability_map_choropleth_layer` | 分级着色地图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_agreement_reliability_mosaic_tile_view` | Agreement reliability - Mosaic tile view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_agreement_reliability_network_node_link` | 关系网络 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_agreement_reliability_qq_reference_plot` | Agreement reliability - Q-Q reference plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_agreement_reliability_quantile_band` | 分位数 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_agreement_reliability_raincloud_view` | Agreement reliability - Raincloud view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_agreement_reliability_rank_interval_plot` | 排名 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_agreement_reliability_residual_annotation_map` | Agreement reliability - Residual annotation map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_agreement_reliability_slope_change_view` | Agreement reliability - Slope change view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_agreement_reliability_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_agreement_reliability_stratified_dotplot` | Agreement reliability - Stratified dot plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_agreement_reliability_threshold_band` | Agreement reliability - Threshold band | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_agreement_reliability_uncertainty_ribbon` | Agreement reliability - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_agreement_reliability_violin_summary` | 小提琴图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_assignment_flow_annotated_reference_view` | Assignment flow - Annotated reference view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_assignment_flow_boxen_interval` | Assignment flow - Boxen interval plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_assignment_flow_comparative_lollipop` | Assignment flow - Comparative lollipop plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_assignment_flow_density_ridge` | 密度图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_assignment_flow_diagnostic_panel` | Assignment flow - Diagnostic panel | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_assignment_flow_ecdf_step_view` | 经验分布图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_assignment_flow_flow_transition_map` | Assignment flow - Flow transition map | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_assignment_flow_forest_interval_plot` | 随机森林 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_assignment_flow_heatmap_matrix` | 热力矩阵 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_assignment_flow_histogram_facets` | 直方图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_assignment_flow_map_choropleth_layer` | 流向地图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_assignment_flow_mosaic_tile_view` | Assignment flow - Mosaic tile view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_assignment_flow_network_node_link` | 关系网络 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_assignment_flow_qq_reference_plot` | Assignment flow - Q-Q reference plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_assignment_flow_quantile_band` | 分位数 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_assignment_flow_raincloud_view` | Assignment flow - Raincloud view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_assignment_flow_rank_interval_plot` | 排名 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_assignment_flow_residual_annotation_map` | Assignment flow - Residual annotation map | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_assignment_flow_slope_change_view` | Assignment flow - Slope change view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_assignment_flow_small_multiple_grid` | 小多图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_assignment_flow_stratified_dotplot` | Assignment flow - Stratified dot plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_assignment_flow_threshold_band` | Assignment flow - Threshold band | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_assignment_flow_uncertainty_ribbon` | Assignment flow - Uncertainty ribbon | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_assignment_flow_violin_summary` | 小提琴图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_autocorrelation_pattern_annotated_reference_view` | Autocorrelation pattern - Annotated reference view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_autocorrelation_pattern_boxen_interval` | Autocorrelation pattern - Boxen interval plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_autocorrelation_pattern_comparative_lollipop` | Autocorrelation pattern - Comparative lollipop plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_autocorrelation_pattern_density_ridge` | 密度图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_autocorrelation_pattern_diagnostic_panel` | Autocorrelation pattern - Diagnostic panel | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_autocorrelation_pattern_ecdf_step_view` | 经验分布图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_autocorrelation_pattern_flow_transition_map` | Autocorrelation pattern - Flow transition map | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_autocorrelation_pattern_forest_interval_plot` | 随机森林 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_autocorrelation_pattern_heatmap_matrix` | 热力矩阵 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_autocorrelation_pattern_histogram_facets` | 直方图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_autocorrelation_pattern_map_choropleth_layer` | 分级着色地图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_autocorrelation_pattern_mosaic_tile_view` | Autocorrelation pattern - Mosaic tile view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_autocorrelation_pattern_network_node_link` | 关系网络 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_autocorrelation_pattern_qq_reference_plot` | Autocorrelation pattern - Q-Q reference plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_autocorrelation_pattern_quantile_band` | 分位数 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_autocorrelation_pattern_raincloud_view` | Autocorrelation pattern - Raincloud view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_autocorrelation_pattern_rank_interval_plot` | 排名 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_autocorrelation_pattern_residual_annotation_map` | Autocorrelation pattern - Residual annotation map | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_autocorrelation_pattern_slope_change_view` | Autocorrelation pattern - Slope change view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_autocorrelation_pattern_small_multiple_grid` | 小多图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_autocorrelation_pattern_stratified_dotplot` | Autocorrelation pattern - Stratified dot plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_autocorrelation_pattern_threshold_band` | Autocorrelation pattern - Threshold band | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_autocorrelation_pattern_uncertainty_ribbon` | Autocorrelation pattern - Uncertainty ribbon | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_autocorrelation_pattern_violin_summary` | 小提琴图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_baseline_covariate_balance_annotated_reference_view` | Baseline covariate balance - Annotated reference view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_baseline_covariate_balance_boxen_interval` | Baseline covariate balance - Boxen interval plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_baseline_covariate_balance_comparative_lollipop` | Baseline covariate balance - Comparative lollipop plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_baseline_covariate_balance_density_ridge` | 密度图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_baseline_covariate_balance_diagnostic_panel` | Baseline covariate balance - Diagnostic panel | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_baseline_covariate_balance_ecdf_step_view` | 经验分布图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_baseline_covariate_balance_flow_transition_map` | Baseline covariate balance - Flow transition map | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_baseline_covariate_balance_forest_interval_plot` | 随机森林 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_baseline_covariate_balance_heatmap_matrix` | 热力矩阵 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_baseline_covariate_balance_histogram_facets` | 直方图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_baseline_covariate_balance_map_choropleth_layer` | 分级着色地图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_baseline_covariate_balance_mosaic_tile_view` | Baseline covariate balance - Mosaic tile view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_baseline_covariate_balance_network_node_link` | 关系网络 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_baseline_covariate_balance_qq_reference_plot` | Baseline covariate balance - Q-Q reference plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_baseline_covariate_balance_quantile_band` | 分位数 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_baseline_covariate_balance_raincloud_view` | Baseline covariate balance - Raincloud view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_baseline_covariate_balance_rank_interval_plot` | 排名 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_baseline_covariate_balance_residual_annotation_map` | Baseline covariate balance - Residual annotation map | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_baseline_covariate_balance_slope_change_view` | Baseline covariate balance - Slope change view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_baseline_covariate_balance_small_multiple_grid` | 小多图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_baseline_covariate_balance_stratified_dotplot` | Baseline covariate balance - Stratified dot plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_baseline_covariate_balance_threshold_band` | Baseline covariate balance - Threshold band | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_baseline_covariate_balance_uncertainty_ribbon` | Baseline covariate balance - Uncertainty ribbon | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_baseline_covariate_balance_violin_summary` | 小提琴图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_block_design_balance_annotated_reference_view` | Block design balance - Annotated reference view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_block_design_balance_boxen_interval` | Block design balance - Boxen interval plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_block_design_balance_comparative_lollipop` | Block design balance - Comparative lollipop plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_block_design_balance_density_ridge` | 密度图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_block_design_balance_diagnostic_panel` | Block design balance - Diagnostic panel | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_block_design_balance_ecdf_step_view` | 经验分布图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_block_design_balance_flow_transition_map` | Block design balance - Flow transition map | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_block_design_balance_forest_interval_plot` | 随机森林 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_block_design_balance_heatmap_matrix` | 热力矩阵 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_block_design_balance_histogram_facets` | 直方图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_block_design_balance_map_choropleth_layer` | 分级着色地图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_block_design_balance_mosaic_tile_view` | Block design balance - Mosaic tile view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_block_design_balance_network_node_link` | 关系网络 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_block_design_balance_qq_reference_plot` | Block design balance - Q-Q reference plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_block_design_balance_quantile_band` | 分位数 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_block_design_balance_raincloud_view` | Block design balance - Raincloud view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_block_design_balance_rank_interval_plot` | 排名 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_block_design_balance_residual_annotation_map` | Block design balance - Residual annotation map | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_block_design_balance_slope_change_view` | Block design balance - Slope change view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_block_design_balance_small_multiple_grid` | 小多图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_block_design_balance_stratified_dotplot` | Block design balance - Stratified dot plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_block_design_balance_threshold_band` | Block design balance - Threshold band | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_block_design_balance_uncertainty_ribbon` | Block design balance - Uncertainty ribbon | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_block_design_balance_violin_summary` | 小提琴图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_annotated_reference_view` | Calibration diagnostic - Annotated reference view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_boxen_interval` | Calibration diagnostic - Boxen interval plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_by_group_annotated_reference_view` | Calibration by group - Annotated reference view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_by_group_boxen_interval` | Calibration by group - Boxen interval plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_by_group_comparative_lollipop` | Calibration by group - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_by_group_density_ridge` | 密度图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_by_group_diagnostic_panel` | Calibration by group - Diagnostic panel | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_by_group_ecdf_step_view` | 经验分布图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_by_group_flow_transition_map` | Calibration by group - Flow transition map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_by_group_forest_interval_plot` | 随机森林 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_by_group_heatmap_matrix` | 热力矩阵 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_by_group_histogram_facets` | 直方图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_by_group_map_choropleth_layer` | 分级着色地图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_by_group_mosaic_tile_view` | Calibration by group - Mosaic tile view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_by_group_network_node_link` | 关系网络 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_by_group_qq_reference_plot` | Calibration by group - Q-Q reference plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_by_group_quantile_band` | 分位数 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_by_group_raincloud_view` | Calibration by group - Raincloud view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_by_group_rank_interval_plot` | 排名 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_by_group_residual_annotation_map` | Calibration by group - Residual annotation map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_by_group_slope_change_view` | Calibration by group - Slope change view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_by_group_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_by_group_stratified_dotplot` | Calibration by group - Stratified dot plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_by_group_threshold_band` | Calibration by group - Threshold band | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_by_group_uncertainty_ribbon` | Calibration by group - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_by_group_violin_summary` | 小提琴图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_comparative_lollipop` | Calibration diagnostic - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_density_ridge` | 密度图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_diagnostic_panel` | Calibration diagnostic - Diagnostic panel | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_ecdf_step_view` | 经验分布图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_flow_transition_map` | Calibration diagnostic - Flow transition map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_forest_interval_plot` | 随机森林 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_heatmap_matrix` | 热力矩阵 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_histogram_facets` | 直方图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_map_choropleth_layer` | 分级着色地图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_mosaic_tile_view` | Calibration diagnostic - Mosaic tile view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_network_node_link` | 关系网络 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_qq_reference_plot` | Calibration diagnostic - Q-Q reference plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_quantile_band` | 分位数 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_raincloud_view` | Calibration diagnostic - Raincloud view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_rank_interval_plot` | 排名 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_residual_annotation_map` | Calibration diagnostic - Residual annotation map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_slope_change_view` | Calibration diagnostic - Slope change view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_stratified_dotplot` | Calibration diagnostic - Stratified dot plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_threshold_band` | Calibration diagnostic - Threshold band | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_uncertainty_ribbon` | Calibration diagnostic - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_calibration_violin_summary` | 小提琴图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_categorical_composition_annotated_reference_view` | Categorical composition - Annotated reference view | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_categorical_composition_boxen_interval` | Categorical composition - Boxen interval plot | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_categorical_composition_comparative_lollipop` | Categorical composition - Comparative lollipop plot | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_categorical_composition_density_ridge` | 密度图 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_categorical_composition_diagnostic_panel` | Categorical composition - Diagnostic panel | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_categorical_composition_ecdf_step_view` | 经验分布图 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_categorical_composition_flow_transition_map` | Categorical composition - Flow transition map | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_categorical_composition_forest_interval_plot` | 随机森林 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_categorical_composition_heatmap_matrix` | 热力矩阵 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_categorical_composition_histogram_facets` | 直方图 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_categorical_composition_map_choropleth_layer` | 分级着色地图 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_categorical_composition_mosaic_tile_view` | Categorical composition - Mosaic tile view | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_categorical_composition_network_node_link` | 关系网络 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_categorical_composition_qq_reference_plot` | Categorical composition - Q-Q reference plot | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_categorical_composition_quantile_band` | 分位数 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_categorical_composition_raincloud_view` | Categorical composition - Raincloud view | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_categorical_composition_rank_interval_plot` | 排名 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_categorical_composition_residual_annotation_map` | Categorical composition - Residual annotation map | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_categorical_composition_slope_change_view` | Categorical composition - Slope change view | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_categorical_composition_small_multiple_grid` | 小多图 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_categorical_composition_stratified_dotplot` | Categorical composition - Stratified dot plot | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_categorical_composition_threshold_band` | Categorical composition - Threshold band | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_categorical_composition_uncertainty_ribbon` | Categorical composition - Uncertainty ribbon | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_categorical_composition_violin_summary` | 小提琴图 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_causal_balance_annotated_reference_view` | Causal balance - Annotated reference view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_causal_balance_boxen_interval` | Causal balance - Boxen interval plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_causal_balance_comparative_lollipop` | Causal balance - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_causal_balance_density_ridge` | 密度图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_causal_balance_diagnostic_panel` | Causal balance - Diagnostic panel | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_causal_balance_ecdf_step_view` | 经验分布图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_causal_balance_flow_transition_map` | Causal balance - Flow transition map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_causal_balance_forest_interval_plot` | 随机森林 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_causal_balance_heatmap_matrix` | 热力矩阵 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_causal_balance_histogram_facets` | 直方图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_causal_balance_map_choropleth_layer` | 分级着色地图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_causal_balance_mosaic_tile_view` | Causal balance - Mosaic tile view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_causal_balance_network_node_link` | 关系网络 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_causal_balance_qq_reference_plot` | Causal balance - Q-Q reference plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_causal_balance_quantile_band` | 分位数 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_causal_balance_raincloud_view` | Causal balance - Raincloud view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_causal_balance_rank_interval_plot` | 排名 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_causal_balance_residual_annotation_map` | Causal balance - Residual annotation map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_causal_balance_slope_change_view` | Causal balance - Slope change view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_causal_balance_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_causal_balance_stratified_dotplot` | Causal balance - Stratified dot plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_causal_balance_threshold_band` | Causal balance - Threshold band | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_causal_balance_uncertainty_ribbon` | Causal balance - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_causal_balance_violin_summary` | 小提琴图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_change_point_annotated_reference_view` | 拐点 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_change_point_boxen_interval` | 拐点 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_change_point_comparative_lollipop` | 拐点 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_change_point_density_ridge` | 拐点 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_change_point_diagnostic_panel` | 拐点 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_change_point_ecdf_step_view` | 拐点 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_change_point_flow_transition_map` | 拐点 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_change_point_forest_interval_plot` | 拐点 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_change_point_heatmap_matrix` | 拐点 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_change_point_histogram_facets` | 拐点 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_change_point_map_choropleth_layer` | 拐点 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_change_point_mosaic_tile_view` | 拐点 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_change_point_network_node_link` | 拐点 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_change_point_qq_reference_plot` | 拐点 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_change_point_quantile_band` | 拐点 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_change_point_raincloud_view` | 拐点 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_change_point_rank_interval_plot` | 拐点 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_change_point_residual_annotation_map` | 拐点 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_change_point_slope_change_view` | 拐点 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_change_point_small_multiple_grid` | 拐点 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_change_point_stratified_dotplot` | 拐点 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_change_point_threshold_band` | 拐点 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_change_point_uncertainty_ribbon` | 拐点 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_change_point_violin_summary` | 拐点 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classifier_threshold_annotated_reference_view` | Classifier threshold - Annotated reference view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classifier_threshold_boxen_interval` | Classifier threshold - Boxen interval plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classifier_threshold_comparative_lollipop` | Classifier threshold - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classifier_threshold_density_ridge` | 密度图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classifier_threshold_diagnostic_panel` | Classifier threshold - Diagnostic panel | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classifier_threshold_ecdf_step_view` | 经验分布图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classifier_threshold_flow_transition_map` | Classifier threshold - Flow transition map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classifier_threshold_forest_interval_plot` | 随机森林 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classifier_threshold_heatmap_matrix` | 热力矩阵 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classifier_threshold_histogram_facets` | 直方图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classifier_threshold_map_choropleth_layer` | 分级着色地图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classifier_threshold_mosaic_tile_view` | Classifier threshold - Mosaic tile view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classifier_threshold_network_node_link` | 关系网络 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classifier_threshold_qq_reference_plot` | Classifier threshold - Q-Q reference plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classifier_threshold_quantile_band` | 分位数 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classifier_threshold_raincloud_view` | Classifier threshold - Raincloud view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classifier_threshold_rank_interval_plot` | 排名 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classifier_threshold_residual_annotation_map` | Classifier threshold - Residual annotation map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classifier_threshold_slope_change_view` | Classifier threshold - Slope change view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classifier_threshold_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classifier_threshold_stratified_dotplot` | Classifier threshold - Stratified dot plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classifier_threshold_threshold_band` | Classifier threshold - Threshold band | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classifier_threshold_uncertainty_ribbon` | Classifier threshold - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classifier_threshold_violin_summary` | 小提琴图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classroom_fairness_annotated_reference_view` | Classroom fairness - Annotated reference view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classroom_fairness_boxen_interval` | Classroom fairness - Boxen interval plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classroom_fairness_comparative_lollipop` | Classroom fairness - Comparative lollipop plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classroom_fairness_density_ridge` | 密度图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classroom_fairness_diagnostic_panel` | Classroom fairness - Diagnostic panel | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classroom_fairness_ecdf_step_view` | 经验分布图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classroom_fairness_flow_transition_map` | Classroom fairness - Flow transition map | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classroom_fairness_forest_interval_plot` | 随机森林 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classroom_fairness_heatmap_matrix` | 热力矩阵 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classroom_fairness_histogram_facets` | 直方图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classroom_fairness_map_choropleth_layer` | 分级着色地图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classroom_fairness_mosaic_tile_view` | Classroom fairness - Mosaic tile view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classroom_fairness_network_node_link` | 关系网络 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classroom_fairness_qq_reference_plot` | Classroom fairness - Q-Q reference plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classroom_fairness_quantile_band` | 分位数 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classroom_fairness_raincloud_view` | Classroom fairness - Raincloud view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classroom_fairness_rank_interval_plot` | 排名 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classroom_fairness_residual_annotation_map` | Classroom fairness - Residual annotation map | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classroom_fairness_slope_change_view` | Classroom fairness - Slope change view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classroom_fairness_small_multiple_grid` | 小多图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classroom_fairness_stratified_dotplot` | Classroom fairness - Stratified dot plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classroom_fairness_threshold_band` | Classroom fairness - Threshold band | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classroom_fairness_uncertainty_ribbon` | Classroom fairness - Uncertainty ribbon | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_classroom_fairness_violin_summary` | 小提琴图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_clinical_endpoint_annotated_reference_view` | Clinical endpoint - Annotated reference view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_clinical_endpoint_boxen_interval` | Clinical endpoint - Boxen interval plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_clinical_endpoint_comparative_lollipop` | Clinical endpoint - Comparative lollipop plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_clinical_endpoint_density_ridge` | 密度图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_clinical_endpoint_diagnostic_panel` | Clinical endpoint - Diagnostic panel | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_clinical_endpoint_ecdf_step_view` | 经验分布图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_clinical_endpoint_flow_transition_map` | Clinical endpoint - Flow transition map | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_clinical_endpoint_forest_interval_plot` | 随机森林 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_clinical_endpoint_heatmap_matrix` | 热力矩阵 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_clinical_endpoint_histogram_facets` | 直方图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_clinical_endpoint_map_choropleth_layer` | 分级着色地图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_clinical_endpoint_mosaic_tile_view` | Clinical endpoint - Mosaic tile view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_clinical_endpoint_network_node_link` | 关系网络 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_clinical_endpoint_qq_reference_plot` | Clinical endpoint - Q-Q reference plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_clinical_endpoint_quantile_band` | 分位数 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_clinical_endpoint_raincloud_view` | Clinical endpoint - Raincloud view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_clinical_endpoint_rank_interval_plot` | 排名 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_clinical_endpoint_residual_annotation_map` | Clinical endpoint - Residual annotation map | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_clinical_endpoint_slope_change_view` | Clinical endpoint - Slope change view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_clinical_endpoint_small_multiple_grid` | 小多图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_clinical_endpoint_stratified_dotplot` | Clinical endpoint - Stratified dot plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_clinical_endpoint_threshold_band` | Clinical endpoint - Threshold band | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_clinical_endpoint_uncertainty_ribbon` | Clinical endpoint - Uncertainty ribbon | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_clinical_endpoint_violin_summary` | 小提琴图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_cluster_structure_annotated_reference_view` | Cluster structure - Annotated reference view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_cluster_structure_boxen_interval` | Cluster structure - Boxen interval plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_cluster_structure_comparative_lollipop` | Cluster structure - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_cluster_structure_density_ridge` | 密度图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_cluster_structure_diagnostic_panel` | Cluster structure - Diagnostic panel | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_cluster_structure_ecdf_step_view` | 经验分布图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_cluster_structure_flow_transition_map` | Cluster structure - Flow transition map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_cluster_structure_forest_interval_plot` | 随机森林 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_cluster_structure_heatmap_matrix` | 热力矩阵 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_cluster_structure_histogram_facets` | 直方图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_cluster_structure_map_choropleth_layer` | 分级着色地图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_cluster_structure_mosaic_tile_view` | Cluster structure - Mosaic tile view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_cluster_structure_network_node_link` | 关系网络 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_cluster_structure_qq_reference_plot` | Cluster structure - Q-Q reference plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_cluster_structure_quantile_band` | 分位数 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_cluster_structure_raincloud_view` | Cluster structure - Raincloud view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_cluster_structure_rank_interval_plot` | 排名 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_cluster_structure_residual_annotation_map` | Cluster structure - Residual annotation map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_cluster_structure_slope_change_view` | Cluster structure - Slope change view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_cluster_structure_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_cluster_structure_stratified_dotplot` | Cluster structure - Stratified dot plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_cluster_structure_threshold_band` | Cluster structure - Threshold band | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_cluster_structure_uncertainty_ribbon` | Cluster structure - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_cluster_structure_violin_summary` | 小提琴图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_community_structure_annotated_reference_view` | Community structure - Annotated reference view | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_community_structure_boxen_interval` | Community structure - Boxen interval plot | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_community_structure_comparative_lollipop` | Community structure - Comparative lollipop plot | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_community_structure_density_ridge` | 密度图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_community_structure_diagnostic_panel` | Community structure - Diagnostic panel | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_community_structure_ecdf_step_view` | 经验分布图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_community_structure_flow_transition_map` | Community structure - Flow transition map | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_community_structure_forest_interval_plot` | 随机森林 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_community_structure_heatmap_matrix` | 热力矩阵 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_community_structure_histogram_facets` | 直方图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_community_structure_map_choropleth_layer` | 分级着色地图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_community_structure_mosaic_tile_view` | Community structure - Mosaic tile view | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_community_structure_network_node_link` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_community_structure_qq_reference_plot` | Community structure - Q-Q reference plot | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_community_structure_quantile_band` | 分位数 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_community_structure_raincloud_view` | Community structure - Raincloud view | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_community_structure_rank_interval_plot` | 排名 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_community_structure_residual_annotation_map` | Community structure - Residual annotation map | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_community_structure_slope_change_view` | Community structure - Slope change view | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_community_structure_small_multiple_grid` | 小多图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_community_structure_stratified_dotplot` | Community structure - Stratified dot plot | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_community_structure_threshold_band` | Community structure - Threshold band | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_community_structure_uncertainty_ribbon` | Community structure - Uncertainty ribbon | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_community_structure_violin_summary` | 小提琴图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_confusion_error_profile_annotated_reference_view` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_confusion_error_profile_boxen_interval` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_confusion_error_profile_comparative_lollipop` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_confusion_error_profile_density_ridge` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_confusion_error_profile_diagnostic_panel` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_confusion_error_profile_ecdf_step_view` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_confusion_error_profile_flow_transition_map` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_confusion_error_profile_forest_interval_plot` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_confusion_error_profile_heatmap_matrix` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_confusion_error_profile_histogram_facets` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_confusion_error_profile_map_choropleth_layer` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_confusion_error_profile_mosaic_tile_view` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_confusion_error_profile_network_node_link` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_confusion_error_profile_qq_reference_plot` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_confusion_error_profile_quantile_band` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_confusion_error_profile_raincloud_view` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_confusion_error_profile_rank_interval_plot` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_confusion_error_profile_residual_annotation_map` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_confusion_error_profile_slope_change_view` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_confusion_error_profile_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_confusion_error_profile_stratified_dotplot` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_confusion_error_profile_threshold_band` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_confusion_error_profile_uncertainty_ribbon` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_confusion_error_profile_violin_summary` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_contingency_structure_annotated_reference_view` | Contingency structure - Annotated reference view | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_contingency_structure_boxen_interval` | Contingency structure - Boxen interval plot | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_contingency_structure_comparative_lollipop` | Contingency structure - Comparative lollipop plot | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_contingency_structure_density_ridge` | 密度图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_contingency_structure_diagnostic_panel` | Contingency structure - Diagnostic panel | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_contingency_structure_ecdf_step_view` | 经验分布图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_contingency_structure_flow_transition_map` | Contingency structure - Flow transition map | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_contingency_structure_forest_interval_plot` | 随机森林 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_contingency_structure_heatmap_matrix` | 热力矩阵 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_contingency_structure_histogram_facets` | 直方图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_contingency_structure_map_choropleth_layer` | 分级着色地图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_contingency_structure_mosaic_tile_view` | Contingency structure - Mosaic tile view | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_contingency_structure_network_node_link` | 关系网络 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_contingency_structure_qq_reference_plot` | Contingency structure - Q-Q reference plot | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_contingency_structure_quantile_band` | 分位数 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_contingency_structure_raincloud_view` | Contingency structure - Raincloud view | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_contingency_structure_rank_interval_plot` | 排名 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_contingency_structure_residual_annotation_map` | Contingency structure - Residual annotation map | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_contingency_structure_slope_change_view` | Contingency structure - Slope change view | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_contingency_structure_small_multiple_grid` | 小多图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_contingency_structure_stratified_dotplot` | Contingency structure - Stratified dot plot | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_contingency_structure_threshold_band` | Contingency structure - Threshold band | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_contingency_structure_uncertainty_ribbon` | Contingency structure - Uncertainty ribbon | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_contingency_structure_violin_summary` | 小提琴图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_correlation_structure_annotated_reference_view` | 相关性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_correlation_structure_boxen_interval` | 相关性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_correlation_structure_comparative_lollipop` | 相关性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_correlation_structure_density_ridge` | 相关性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_correlation_structure_diagnostic_panel` | 相关性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_correlation_structure_ecdf_step_view` | 相关性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_correlation_structure_flow_transition_map` | 相关性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_correlation_structure_forest_interval_plot` | 相关性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_correlation_structure_heatmap_matrix` | 相关性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_correlation_structure_histogram_facets` | 相关性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_correlation_structure_map_choropleth_layer` | 相关性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_correlation_structure_mosaic_tile_view` | 相关性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_correlation_structure_network_node_link` | 相关性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_correlation_structure_qq_reference_plot` | 相关性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_correlation_structure_quantile_band` | 相关性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_correlation_structure_raincloud_view` | 相关性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_correlation_structure_rank_interval_plot` | 相关性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_correlation_structure_residual_annotation_map` | 相关性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_correlation_structure_slope_change_view` | 相关性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_correlation_structure_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_correlation_structure_stratified_dotplot` | 相关性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_correlation_structure_threshold_band` | 相关性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_correlation_structure_uncertainty_ribbon` | 相关性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_correlation_structure_violin_summary` | 相关性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_counterfactual_contrast_annotated_reference_view` | Counterfactual contrast - Annotated reference view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_counterfactual_contrast_boxen_interval` | Counterfactual contrast - Boxen interval plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_counterfactual_contrast_comparative_lollipop` | Counterfactual contrast - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_counterfactual_contrast_density_ridge` | 密度图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_counterfactual_contrast_diagnostic_panel` | Counterfactual contrast - Diagnostic panel | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_counterfactual_contrast_ecdf_step_view` | 经验分布图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_counterfactual_contrast_flow_transition_map` | Counterfactual contrast - Flow transition map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_counterfactual_contrast_forest_interval_plot` | 随机森林 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_counterfactual_contrast_heatmap_matrix` | 热力矩阵 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_counterfactual_contrast_histogram_facets` | 直方图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_counterfactual_contrast_map_choropleth_layer` | 分级着色地图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_counterfactual_contrast_mosaic_tile_view` | Counterfactual contrast - Mosaic tile view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_counterfactual_contrast_network_node_link` | 关系网络 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_counterfactual_contrast_qq_reference_plot` | Counterfactual contrast - Q-Q reference plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_counterfactual_contrast_quantile_band` | 分位数 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_counterfactual_contrast_raincloud_view` | Counterfactual contrast - Raincloud view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_counterfactual_contrast_rank_interval_plot` | 排名 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_counterfactual_contrast_residual_annotation_map` | Counterfactual contrast - Residual annotation map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_counterfactual_contrast_slope_change_view` | Counterfactual contrast - Slope change view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_counterfactual_contrast_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_counterfactual_contrast_stratified_dotplot` | Counterfactual contrast - Stratified dot plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_counterfactual_contrast_threshold_band` | Counterfactual contrast - Threshold band | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_counterfactual_contrast_uncertainty_ribbon` | Counterfactual contrast - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_counterfactual_contrast_violin_summary` | 小提琴图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_quality_annotated_reference_view` | Data quality profile - Annotated reference view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_quality_boxen_interval` | Data quality profile - Boxen interval plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_quality_comparative_lollipop` | Data quality profile - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_quality_density_ridge` | 密度图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_quality_diagnostic_panel` | Data quality profile - Diagnostic panel | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_quality_ecdf_step_view` | 经验分布图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_quality_flow_transition_map` | Data quality profile - Flow transition map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_quality_forest_interval_plot` | 随机森林 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_quality_heatmap_matrix` | 热力矩阵 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_quality_histogram_facets` | 直方图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_quality_map_choropleth_layer` | 分级着色地图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_quality_mosaic_tile_view` | Data quality profile - Mosaic tile view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_quality_network_node_link` | 关系网络 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_quality_qq_reference_plot` | Data quality profile - Q-Q reference plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_quality_quantile_band` | 分位数 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_quality_raincloud_view` | Data quality profile - Raincloud view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_quality_rank_interval_plot` | 排名 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_quality_residual_annotation_map` | Data quality profile - Residual annotation map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_quality_slope_change_view` | Data quality profile - Slope change view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_quality_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_quality_stratified_dotplot` | Data quality profile - Stratified dot plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_quality_threshold_band` | Data quality profile - Threshold band | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_quality_uncertainty_ribbon` | Data quality profile - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_quality_violin_summary` | 小提琴图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_validation_rules_annotated_reference_view` | Data validation rules - Annotated reference view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_validation_rules_boxen_interval` | Data validation rules - Boxen interval plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_validation_rules_comparative_lollipop` | Data validation rules - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_validation_rules_density_ridge` | 密度图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_validation_rules_diagnostic_panel` | Data validation rules - Diagnostic panel | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_validation_rules_ecdf_step_view` | 经验分布图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_validation_rules_flow_transition_map` | Data validation rules - Flow transition map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_validation_rules_forest_interval_plot` | 随机森林 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_validation_rules_heatmap_matrix` | 热力矩阵 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_validation_rules_histogram_facets` | 直方图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_validation_rules_map_choropleth_layer` | 分级着色地图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_validation_rules_mosaic_tile_view` | Data validation rules - Mosaic tile view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_validation_rules_network_node_link` | 关系网络 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_validation_rules_qq_reference_plot` | Data validation rules - Q-Q reference plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_validation_rules_quantile_band` | 分位数 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_validation_rules_raincloud_view` | Data validation rules - Raincloud view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_validation_rules_rank_interval_plot` | 排名 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_validation_rules_residual_annotation_map` | Data validation rules - Residual annotation map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_validation_rules_slope_change_view` | Data validation rules - Slope change view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_validation_rules_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_validation_rules_stratified_dotplot` | Data validation rules - Stratified dot plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_validation_rules_threshold_band` | Data validation rules - Threshold band | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_validation_rules_uncertainty_ribbon` | Data validation rules - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_data_validation_rules_violin_summary` | 小提琴图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_defect_classification_annotated_reference_view` | Defect classification - Annotated reference view | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_defect_classification_boxen_interval` | Defect classification - Boxen interval plot | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_defect_classification_comparative_lollipop` | Defect classification - Comparative lollipop plot | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_defect_classification_density_ridge` | 密度图 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_defect_classification_diagnostic_panel` | Defect classification - Diagnostic panel | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_defect_classification_ecdf_step_view` | 经验分布图 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_defect_classification_flow_transition_map` | Defect classification - Flow transition map | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_defect_classification_forest_interval_plot` | 随机森林 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_defect_classification_heatmap_matrix` | 热力矩阵 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_defect_classification_histogram_facets` | 直方图 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_defect_classification_map_choropleth_layer` | 分级着色地图 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_defect_classification_mosaic_tile_view` | Defect classification - Mosaic tile view | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_defect_classification_network_node_link` | 关系网络 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_defect_classification_qq_reference_plot` | Defect classification - Q-Q reference plot | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_defect_classification_quantile_band` | 分位数 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_defect_classification_raincloud_view` | Defect classification - Raincloud view | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_defect_classification_rank_interval_plot` | 排名 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_defect_classification_residual_annotation_map` | Defect classification - Residual annotation map | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_defect_classification_slope_change_view` | Defect classification - Slope change view | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_defect_classification_small_multiple_grid` | 小多图 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_defect_classification_stratified_dotplot` | Defect classification - Stratified dot plot | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_defect_classification_threshold_band` | Defect classification - Threshold band | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_defect_classification_uncertainty_ribbon` | Defect classification - Uncertainty ribbon | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_defect_classification_violin_summary` | 小提琴图 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dimension_reduction_annotated_reference_view` | Dimension reduction - Annotated reference view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dimension_reduction_boxen_interval` | Dimension reduction - Boxen interval plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dimension_reduction_comparative_lollipop` | Dimension reduction - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dimension_reduction_density_ridge` | 密度图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dimension_reduction_diagnostic_panel` | Dimension reduction - Diagnostic panel | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dimension_reduction_ecdf_step_view` | 经验分布图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dimension_reduction_flow_transition_map` | Dimension reduction - Flow transition map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dimension_reduction_forest_interval_plot` | 随机森林 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dimension_reduction_heatmap_matrix` | 热力矩阵 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dimension_reduction_histogram_facets` | 直方图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dimension_reduction_map_choropleth_layer` | 分级着色地图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dimension_reduction_mosaic_tile_view` | Dimension reduction - Mosaic tile view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dimension_reduction_network_node_link` | 关系网络 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dimension_reduction_qq_reference_plot` | Dimension reduction - Q-Q reference plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dimension_reduction_quantile_band` | 分位数 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dimension_reduction_raincloud_view` | Dimension reduction - Raincloud view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dimension_reduction_rank_interval_plot` | 排名 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dimension_reduction_residual_annotation_map` | Dimension reduction - Residual annotation map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dimension_reduction_slope_change_view` | Dimension reduction - Slope change view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dimension_reduction_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dimension_reduction_stratified_dotplot` | Dimension reduction - Stratified dot plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dimension_reduction_threshold_band` | Dimension reduction - Threshold band | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dimension_reduction_uncertainty_ribbon` | Dimension reduction - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dimension_reduction_violin_summary` | 小提琴图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_discontinuity_window_annotated_reference_view` | Discontinuity window - Annotated reference view | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_discontinuity_window_boxen_interval` | Discontinuity window - Boxen interval plot | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_discontinuity_window_comparative_lollipop` | Discontinuity window - Comparative lollipop plot | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_discontinuity_window_density_ridge` | 密度图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_discontinuity_window_diagnostic_panel` | Discontinuity window - Diagnostic panel | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_discontinuity_window_ecdf_step_view` | 经验分布图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_discontinuity_window_flow_transition_map` | Discontinuity window - Flow transition map | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_discontinuity_window_forest_interval_plot` | 随机森林 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_discontinuity_window_heatmap_matrix` | 热力矩阵 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_discontinuity_window_histogram_facets` | 直方图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_discontinuity_window_map_choropleth_layer` | 分级着色地图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_discontinuity_window_mosaic_tile_view` | Discontinuity window - Mosaic tile view | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_discontinuity_window_network_node_link` | 关系网络 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_discontinuity_window_qq_reference_plot` | Discontinuity window - Q-Q reference plot | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_discontinuity_window_quantile_band` | 分位数 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_discontinuity_window_raincloud_view` | Discontinuity window - Raincloud view | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_discontinuity_window_rank_interval_plot` | 排名 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_discontinuity_window_residual_annotation_map` | Discontinuity window - Residual annotation map | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_discontinuity_window_slope_change_view` | Discontinuity window - Slope change view | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_discontinuity_window_small_multiple_grid` | 小多图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_discontinuity_window_stratified_dotplot` | Discontinuity window - Stratified dot plot | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_discontinuity_window_threshold_band` | Discontinuity window - Threshold band | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_discontinuity_window_uncertainty_ribbon` | Discontinuity window - Uncertainty ribbon | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_discontinuity_window_violin_summary` | 小提琴图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_comparison_annotated_reference_view` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_comparison_boxen_interval` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_comparison_comparative_lollipop` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_comparison_density_ridge` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_comparison_diagnostic_panel` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_comparison_ecdf_step_view` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_comparison_flow_transition_map` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_comparison_forest_interval_plot` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_comparison_heatmap_matrix` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_comparison_histogram_facets` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_comparison_map_choropleth_layer` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_comparison_mosaic_tile_view` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_comparison_network_node_link` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_comparison_qq_reference_plot` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_comparison_quantile_band` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_comparison_raincloud_view` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_comparison_rank_interval_plot` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_comparison_residual_annotation_map` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_comparison_slope_change_view` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_comparison_small_multiple_grid` | 小多图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_comparison_stratified_dotplot` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_comparison_threshold_band` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_comparison_uncertainty_ribbon` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_comparison_violin_summary` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_shape_annotated_reference_view` | 分布 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_shape_boxen_interval` | 分布 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_shape_comparative_lollipop` | 分布 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_shape_density_ridge` | 分布 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_shape_diagnostic_panel` | 分布 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_shape_ecdf_step_view` | 分布 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_shape_flow_transition_map` | 分布 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_shape_forest_interval_plot` | 分布 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_shape_heatmap_matrix` | 分布 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_shape_histogram_facets` | 分布 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_shape_map_choropleth_layer` | 分布 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_shape_mosaic_tile_view` | 分布 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_shape_network_node_link` | 分布 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_shape_qq_reference_plot` | 分布 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_shape_quantile_band` | 分布 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_shape_raincloud_view` | 分布 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_shape_rank_interval_plot` | 分布 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_shape_residual_annotation_map` | 分布 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_shape_slope_change_view` | 分布 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_shape_small_multiple_grid` | 小多图 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_shape_stratified_dotplot` | 分布 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_shape_threshold_band` | 分布 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_shape_uncertainty_ribbon` | 分布 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_distribution_shape_violin_summary` | 分布 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dose_response_annotated_reference_view` | Dose response - Annotated reference view | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dose_response_boxen_interval` | Dose response - Boxen interval plot | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dose_response_comparative_lollipop` | Dose response - Comparative lollipop plot | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dose_response_density_ridge` | 密度图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dose_response_diagnostic_panel` | Dose response - Diagnostic panel | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dose_response_ecdf_step_view` | 经验分布图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dose_response_flow_transition_map` | Dose response - Flow transition map | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dose_response_forest_interval_plot` | 随机森林 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dose_response_heatmap_matrix` | 热力矩阵 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dose_response_histogram_facets` | 直方图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dose_response_map_choropleth_layer` | 分级着色地图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dose_response_mosaic_tile_view` | Dose response - Mosaic tile view | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dose_response_network_node_link` | 关系网络 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dose_response_qq_reference_plot` | Dose response - Q-Q reference plot | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dose_response_quantile_band` | 分位数 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dose_response_raincloud_view` | Dose response - Raincloud view | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dose_response_rank_interval_plot` | 排名 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dose_response_residual_annotation_map` | Dose response - Residual annotation map | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dose_response_slope_change_view` | Dose response - Slope change view | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dose_response_small_multiple_grid` | 小多图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dose_response_stratified_dotplot` | Dose response - Stratified dot plot | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dose_response_threshold_band` | Dose response - Threshold band | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dose_response_uncertainty_ribbon` | Dose response - Uncertainty ribbon | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_dose_response_violin_summary` | 小提琴图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_duplicate_record_structure_annotated_reference_view` | Duplicate record structure - Annotated reference view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_duplicate_record_structure_boxen_interval` | Duplicate record structure - Boxen interval plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_duplicate_record_structure_comparative_lollipop` | Duplicate record structure - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_duplicate_record_structure_density_ridge` | 密度图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_duplicate_record_structure_diagnostic_panel` | Duplicate record structure - Diagnostic panel | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_duplicate_record_structure_ecdf_step_view` | 经验分布图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_duplicate_record_structure_flow_transition_map` | Duplicate record structure - Flow transition map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_duplicate_record_structure_forest_interval_plot` | 随机森林 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_duplicate_record_structure_heatmap_matrix` | 热力矩阵 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_duplicate_record_structure_histogram_facets` | 直方图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_duplicate_record_structure_map_choropleth_layer` | 分级着色地图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_duplicate_record_structure_mosaic_tile_view` | Duplicate record structure - Mosaic tile view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_duplicate_record_structure_network_node_link` | 关系网络 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_duplicate_record_structure_qq_reference_plot` | Duplicate record structure - Q-Q reference plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_duplicate_record_structure_quantile_band` | 分位数 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_duplicate_record_structure_raincloud_view` | Duplicate record structure - Raincloud view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_duplicate_record_structure_rank_interval_plot` | 排名 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_duplicate_record_structure_residual_annotation_map` | Duplicate record structure - Residual annotation map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_duplicate_record_structure_slope_change_view` | Duplicate record structure - Slope change view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_duplicate_record_structure_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_duplicate_record_structure_stratified_dotplot` | Duplicate record structure - Stratified dot plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_duplicate_record_structure_threshold_band` | Duplicate record structure - Threshold band | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_duplicate_record_structure_uncertainty_ribbon` | Duplicate record structure - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_duplicate_record_structure_violin_summary` | 小提琴图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_categorical_overview_annotated_reference_view` | EDA categorical overview - Annotated reference view | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_categorical_overview_boxen_interval` | EDA categorical overview - Boxen interval plot | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_categorical_overview_comparative_lollipop` | EDA categorical overview - Comparative lollipop plot | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_categorical_overview_density_ridge` | 密度图 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_categorical_overview_diagnostic_panel` | EDA categorical overview - Diagnostic panel | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_categorical_overview_ecdf_step_view` | 经验分布图 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_categorical_overview_flow_transition_map` | EDA categorical overview - Flow transition map | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_categorical_overview_forest_interval_plot` | 随机森林 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_categorical_overview_heatmap_matrix` | 热力矩阵 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_categorical_overview_histogram_facets` | 直方图 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_categorical_overview_map_choropleth_layer` | 分级着色地图 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_categorical_overview_mosaic_tile_view` | EDA categorical overview - Mosaic tile view | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_categorical_overview_network_node_link` | 关系网络 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_categorical_overview_qq_reference_plot` | EDA categorical overview - Q-Q reference plot | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_categorical_overview_quantile_band` | 分位数 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_categorical_overview_raincloud_view` | EDA categorical overview - Raincloud view | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_categorical_overview_rank_interval_plot` | 排名 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_categorical_overview_residual_annotation_map` | EDA categorical overview - Residual annotation map | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_categorical_overview_slope_change_view` | EDA categorical overview - Slope change view | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_categorical_overview_small_multiple_grid` | 小多图 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_categorical_overview_stratified_dotplot` | EDA categorical overview - Stratified dot plot | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_categorical_overview_threshold_band` | EDA categorical overview - Threshold band | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_categorical_overview_uncertainty_ribbon` | EDA categorical overview - Uncertainty ribbon | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_categorical_overview_violin_summary` | 小提琴图 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_numeric_overview_annotated_reference_view` | EDA numeric overview - Annotated reference view | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_numeric_overview_boxen_interval` | EDA numeric overview - Boxen interval plot | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_numeric_overview_comparative_lollipop` | EDA numeric overview - Comparative lollipop plot | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_numeric_overview_density_ridge` | 密度图 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_numeric_overview_diagnostic_panel` | EDA numeric overview - Diagnostic panel | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_numeric_overview_ecdf_step_view` | 经验分布图 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_numeric_overview_flow_transition_map` | EDA numeric overview - Flow transition map | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_numeric_overview_forest_interval_plot` | 随机森林 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_numeric_overview_heatmap_matrix` | 热力矩阵 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_numeric_overview_histogram_facets` | 直方图 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_numeric_overview_map_choropleth_layer` | 分级着色地图 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_numeric_overview_mosaic_tile_view` | EDA numeric overview - Mosaic tile view | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_numeric_overview_network_node_link` | 关系网络 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_numeric_overview_qq_reference_plot` | EDA numeric overview - Q-Q reference plot | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_numeric_overview_quantile_band` | 分位数 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_numeric_overview_raincloud_view` | EDA numeric overview - Raincloud view | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_numeric_overview_rank_interval_plot` | 排名 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_numeric_overview_residual_annotation_map` | EDA numeric overview - Residual annotation map | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_numeric_overview_slope_change_view` | EDA numeric overview - Slope change view | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_numeric_overview_small_multiple_grid` | 小多图 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_numeric_overview_stratified_dotplot` | EDA numeric overview - Stratified dot plot | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_numeric_overview_threshold_band` | EDA numeric overview - Threshold band | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_numeric_overview_uncertainty_ribbon` | EDA numeric overview - Uncertainty ribbon | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_eda_numeric_overview_violin_summary` | 小提琴图 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_education_growth_annotated_reference_view` | Education growth - Annotated reference view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_education_growth_boxen_interval` | Education growth - Boxen interval plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_education_growth_comparative_lollipop` | Education growth - Comparative lollipop plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_education_growth_density_ridge` | 密度图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_education_growth_diagnostic_panel` | Education growth - Diagnostic panel | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_education_growth_ecdf_step_view` | 经验分布图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_education_growth_flow_transition_map` | Education growth - Flow transition map | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_education_growth_forest_interval_plot` | 随机森林 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_education_growth_heatmap_matrix` | 热力矩阵 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_education_growth_histogram_facets` | 直方图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_education_growth_map_choropleth_layer` | 分级着色地图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_education_growth_mosaic_tile_view` | Education growth - Mosaic tile view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_education_growth_network_node_link` | 关系网络 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_education_growth_qq_reference_plot` | Education growth - Q-Q reference plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_education_growth_quantile_band` | 分位数 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_education_growth_raincloud_view` | Education growth - Raincloud view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_education_growth_rank_interval_plot` | 排名 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_education_growth_residual_annotation_map` | Education growth - Residual annotation map | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_education_growth_slope_change_view` | Education growth - Slope change view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_education_growth_small_multiple_grid` | 小多图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_education_growth_stratified_dotplot` | Education growth - Stratified dot plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_education_growth_threshold_band` | Education growth - Threshold band | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_education_growth_uncertainty_ribbon` | Education growth - Uncertainty ribbon | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_education_growth_violin_summary` | 小提琴图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_effect_size_annotated_reference_view` | Effect size view - Annotated reference view | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_effect_size_boxen_interval` | Effect size view - Boxen interval plot | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_effect_size_comparative_lollipop` | Effect size view - Comparative lollipop plot | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_effect_size_density_ridge` | 密度图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_effect_size_diagnostic_panel` | Effect size view - Diagnostic panel | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_effect_size_ecdf_step_view` | 经验分布图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_effect_size_flow_transition_map` | Effect size view - Flow transition map | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_effect_size_forest_interval_plot` | 随机森林 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_effect_size_heatmap_matrix` | 热力矩阵 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_effect_size_histogram_facets` | 直方图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_effect_size_map_choropleth_layer` | 分级着色地图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_effect_size_mosaic_tile_view` | Effect size view - Mosaic tile view | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_effect_size_network_node_link` | 关系网络 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_effect_size_qq_reference_plot` | Effect size view - Q-Q reference plot | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_effect_size_quantile_band` | 分位数 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_effect_size_raincloud_view` | Effect size view - Raincloud view | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_effect_size_rank_interval_plot` | 排名 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_effect_size_residual_annotation_map` | Effect size view - Residual annotation map | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_effect_size_slope_change_view` | Effect size view - Slope change view | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_effect_size_small_multiple_grid` | 小多图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_effect_size_stratified_dotplot` | Effect size view - Stratified dot plot | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_effect_size_threshold_band` | Effect size view - Threshold band | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_effect_size_uncertainty_ribbon` | Effect size view - Uncertainty ribbon | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_effect_size_violin_summary` | 小提琴图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_environmental_exposure_annotated_reference_view` | Environmental exposure - Annotated reference view | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_environmental_exposure_boxen_interval` | Environmental exposure - Boxen interval plot | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_environmental_exposure_comparative_lollipop` | Environmental exposure - Comparative lollipop plot | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_environmental_exposure_density_ridge` | 密度图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_environmental_exposure_diagnostic_panel` | Environmental exposure - Diagnostic panel | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_environmental_exposure_ecdf_step_view` | 经验分布图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_environmental_exposure_flow_transition_map` | Environmental exposure - Flow transition map | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_environmental_exposure_forest_interval_plot` | 随机森林 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_environmental_exposure_heatmap_matrix` | 热力矩阵 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_environmental_exposure_histogram_facets` | 直方图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_environmental_exposure_map_choropleth_layer` | 分级着色地图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_environmental_exposure_mosaic_tile_view` | Environmental exposure - Mosaic tile view | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_environmental_exposure_network_node_link` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_environmental_exposure_qq_reference_plot` | Environmental exposure - Q-Q reference plot | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_environmental_exposure_quantile_band` | 分位数 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_environmental_exposure_raincloud_view` | Environmental exposure - Raincloud view | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_environmental_exposure_rank_interval_plot` | 排名 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_environmental_exposure_residual_annotation_map` | Environmental exposure - Residual annotation map | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_environmental_exposure_slope_change_view` | Environmental exposure - Slope change view | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_environmental_exposure_small_multiple_grid` | 小多图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_environmental_exposure_stratified_dotplot` | Environmental exposure - Stratified dot plot | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_environmental_exposure_threshold_band` | Environmental exposure - Threshold band | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_environmental_exposure_uncertainty_ribbon` | Environmental exposure - Uncertainty ribbon | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_environmental_exposure_violin_summary` | 小提琴图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_epidemiology_cluster_annotated_reference_view` | Epidemiology cluster - Annotated reference view | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_epidemiology_cluster_boxen_interval` | Epidemiology cluster - Boxen interval plot | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_epidemiology_cluster_comparative_lollipop` | Epidemiology cluster - Comparative lollipop plot | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_epidemiology_cluster_density_ridge` | 密度图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_epidemiology_cluster_diagnostic_panel` | Epidemiology cluster - Diagnostic panel | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_epidemiology_cluster_ecdf_step_view` | 经验分布图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_epidemiology_cluster_flow_transition_map` | Epidemiology cluster - Flow transition map | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_epidemiology_cluster_forest_interval_plot` | 随机森林 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_epidemiology_cluster_heatmap_matrix` | 热力矩阵 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_epidemiology_cluster_histogram_facets` | 直方图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_epidemiology_cluster_map_choropleth_layer` | 分级着色地图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_epidemiology_cluster_mosaic_tile_view` | Epidemiology cluster - Mosaic tile view | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_epidemiology_cluster_network_node_link` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_epidemiology_cluster_qq_reference_plot` | Epidemiology cluster - Q-Q reference plot | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_epidemiology_cluster_quantile_band` | 分位数 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_epidemiology_cluster_raincloud_view` | Epidemiology cluster - Raincloud view | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_epidemiology_cluster_rank_interval_plot` | 排名 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_epidemiology_cluster_residual_annotation_map` | Epidemiology cluster - Residual annotation map | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_epidemiology_cluster_slope_change_view` | Epidemiology cluster - Slope change view | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_epidemiology_cluster_small_multiple_grid` | 小多图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_epidemiology_cluster_stratified_dotplot` | Epidemiology cluster - Stratified dot plot | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_epidemiology_cluster_threshold_band` | Epidemiology cluster - Threshold band | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_epidemiology_cluster_uncertainty_ribbon` | Epidemiology cluster - Uncertainty ribbon | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_epidemiology_cluster_violin_summary` | 小提琴图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_power_annotated_reference_view` | Experiment power - Annotated reference view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_power_boxen_interval` | Experiment power - Boxen interval plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_power_comparative_lollipop` | Experiment power - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_power_density_ridge` | 密度图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_power_diagnostic_panel` | Experiment power - Diagnostic panel | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_power_ecdf_step_view` | 经验分布图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_power_flow_transition_map` | Experiment power - Flow transition map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_power_forest_interval_plot` | 随机森林 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_power_heatmap_matrix` | 热力矩阵 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_power_histogram_facets` | 直方图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_power_map_choropleth_layer` | 分级着色地图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_power_mosaic_tile_view` | Experiment power - Mosaic tile view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_power_network_node_link` | 关系网络 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_power_qq_reference_plot` | Experiment power - Q-Q reference plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_power_quantile_band` | 分位数 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_power_raincloud_view` | Experiment power - Raincloud view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_power_rank_interval_plot` | 排名 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_power_residual_annotation_map` | Experiment power - Residual annotation map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_power_slope_change_view` | Experiment power - Slope change view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_power_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_power_stratified_dotplot` | Experiment power - Stratified dot plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_power_threshold_band` | Experiment power - Threshold band | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_power_uncertainty_ribbon` | Experiment power - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_power_violin_summary` | 小提琴图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_response_annotated_reference_view` | Experiment response - Annotated reference view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_response_boxen_interval` | Experiment response - Boxen interval plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_response_comparative_lollipop` | Experiment response - Comparative lollipop plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_response_density_ridge` | 密度图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_response_diagnostic_panel` | Experiment response - Diagnostic panel | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_response_ecdf_step_view` | 经验分布图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_response_flow_transition_map` | Experiment response - Flow transition map | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_response_forest_interval_plot` | 随机森林 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_response_heatmap_matrix` | 热力矩阵 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_response_histogram_facets` | 直方图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_response_map_choropleth_layer` | 分级着色地图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_response_mosaic_tile_view` | Experiment response - Mosaic tile view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_response_network_node_link` | 关系网络 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_response_qq_reference_plot` | Experiment response - Q-Q reference plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_response_quantile_band` | 分位数 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_response_raincloud_view` | Experiment response - Raincloud view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_response_rank_interval_plot` | 排名 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_response_residual_annotation_map` | Experiment response - Residual annotation map | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_response_slope_change_view` | Experiment response - Slope change view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_response_small_multiple_grid` | 小多图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_response_stratified_dotplot` | Experiment response - Stratified dot plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_response_threshold_band` | Experiment response - Threshold band | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_response_uncertainty_ribbon` | Experiment response - Uncertainty ribbon | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_experiment_response_violin_summary` | 小提琴图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factor_loading_annotated_reference_view` | Factor loading pattern - Annotated reference view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factor_loading_boxen_interval` | Factor loading pattern - Boxen interval plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factor_loading_comparative_lollipop` | Factor loading pattern - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factor_loading_density_ridge` | 密度图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factor_loading_diagnostic_panel` | Factor loading pattern - Diagnostic panel | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factor_loading_ecdf_step_view` | 经验分布图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factor_loading_flow_transition_map` | Factor loading pattern - Flow transition map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factor_loading_forest_interval_plot` | 随机森林 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factor_loading_heatmap_matrix` | 热力矩阵 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factor_loading_histogram_facets` | 直方图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factor_loading_map_choropleth_layer` | 分级着色地图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factor_loading_mosaic_tile_view` | Factor loading pattern - Mosaic tile view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factor_loading_network_node_link` | 关系网络 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factor_loading_qq_reference_plot` | Factor loading pattern - Q-Q reference plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factor_loading_quantile_band` | 分位数 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factor_loading_raincloud_view` | Factor loading pattern - Raincloud view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factor_loading_rank_interval_plot` | 排名 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factor_loading_residual_annotation_map` | Factor loading pattern - Residual annotation map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factor_loading_slope_change_view` | Factor loading pattern - Slope change view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factor_loading_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factor_loading_stratified_dotplot` | Factor loading pattern - Stratified dot plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factor_loading_threshold_band` | Factor loading pattern - Threshold band | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factor_loading_uncertainty_ribbon` | Factor loading pattern - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factor_loading_violin_summary` | 小提琴图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factorial_response_annotated_reference_view` | Factorial response - Annotated reference view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factorial_response_boxen_interval` | Factorial response - Boxen interval plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factorial_response_comparative_lollipop` | Factorial response - Comparative lollipop plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factorial_response_density_ridge` | 密度图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factorial_response_diagnostic_panel` | Factorial response - Diagnostic panel | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factorial_response_ecdf_step_view` | 经验分布图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factorial_response_flow_transition_map` | Factorial response - Flow transition map | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factorial_response_forest_interval_plot` | 随机森林 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factorial_response_heatmap_matrix` | 热力矩阵 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factorial_response_histogram_facets` | 直方图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factorial_response_map_choropleth_layer` | 分级着色地图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factorial_response_mosaic_tile_view` | Factorial response - Mosaic tile view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factorial_response_network_node_link` | 关系网络 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factorial_response_qq_reference_plot` | Factorial response - Q-Q reference plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factorial_response_quantile_band` | 分位数 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factorial_response_raincloud_view` | Factorial response - Raincloud view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factorial_response_rank_interval_plot` | 排名 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factorial_response_residual_annotation_map` | Factorial response - Residual annotation map | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factorial_response_slope_change_view` | Factorial response - Slope change view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factorial_response_small_multiple_grid` | 小多图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factorial_response_stratified_dotplot` | Factorial response - Stratified dot plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factorial_response_threshold_band` | Factorial response - Threshold band | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factorial_response_uncertainty_ribbon` | Factorial response - Uncertainty ribbon | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_factorial_response_violin_summary` | 小提琴图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_contribution_annotated_reference_view` | Feature contribution - Annotated reference view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_contribution_boxen_interval` | Feature contribution - Boxen interval plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_contribution_comparative_lollipop` | Feature contribution - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_contribution_density_ridge` | 密度图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_contribution_diagnostic_panel` | Feature contribution - Diagnostic panel | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_contribution_ecdf_step_view` | 经验分布图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_contribution_flow_transition_map` | Feature contribution - Flow transition map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_contribution_forest_interval_plot` | 随机森林 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_contribution_heatmap_matrix` | 热力矩阵 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_contribution_histogram_facets` | 直方图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_contribution_map_choropleth_layer` | 分级着色地图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_contribution_mosaic_tile_view` | Feature contribution - Mosaic tile view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_contribution_network_node_link` | 关系网络 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_contribution_qq_reference_plot` | Feature contribution - Q-Q reference plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_contribution_quantile_band` | 分位数 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_contribution_raincloud_view` | Feature contribution - Raincloud view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_contribution_rank_interval_plot` | 排名 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_contribution_residual_annotation_map` | Feature contribution - Residual annotation map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_contribution_slope_change_view` | Feature contribution - Slope change view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_contribution_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_contribution_stratified_dotplot` | Feature contribution - Stratified dot plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_contribution_threshold_band` | Feature contribution - Threshold band | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_contribution_uncertainty_ribbon` | Feature contribution - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_contribution_violin_summary` | 小提琴图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_importance_annotated_reference_view` | 重要性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_importance_boxen_interval` | 重要性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_importance_comparative_lollipop` | 重要性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_importance_density_ridge` | 重要性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_importance_diagnostic_panel` | 重要性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_importance_ecdf_step_view` | 重要性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_importance_flow_transition_map` | 重要性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_importance_forest_interval_plot` | 重要性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_importance_heatmap_matrix` | 重要性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_importance_histogram_facets` | 重要性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_importance_map_choropleth_layer` | 重要性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_importance_mosaic_tile_view` | 重要性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_importance_network_node_link` | 重要性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_importance_qq_reference_plot` | 重要性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_importance_quantile_band` | 重要性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_importance_raincloud_view` | 重要性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_importance_rank_interval_plot` | 重要性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_importance_residual_annotation_map` | 重要性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_importance_slope_change_view` | 重要性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_importance_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_importance_stratified_dotplot` | 重要性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_importance_threshold_band` | 重要性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_importance_uncertainty_ribbon` | 重要性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_feature_importance_violin_summary` | 重要性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_forecast_uncertainty_annotated_reference_view` | 预测 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_forecast_uncertainty_boxen_interval` | 预测 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_forecast_uncertainty_comparative_lollipop` | 预测 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_forecast_uncertainty_density_ridge` | 预测 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_forecast_uncertainty_diagnostic_panel` | 预测 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_forecast_uncertainty_ecdf_step_view` | 预测 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_forecast_uncertainty_flow_transition_map` | 预测 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_forecast_uncertainty_forest_interval_plot` | 预测 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_forecast_uncertainty_heatmap_matrix` | 预测 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_forecast_uncertainty_histogram_facets` | 预测 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_forecast_uncertainty_map_choropleth_layer` | 预测 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_forecast_uncertainty_mosaic_tile_view` | 预测 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_forecast_uncertainty_network_node_link` | 预测 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_forecast_uncertainty_qq_reference_plot` | 预测 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_forecast_uncertainty_quantile_band` | 预测 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_forecast_uncertainty_raincloud_view` | 预测 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_forecast_uncertainty_rank_interval_plot` | 预测 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_forecast_uncertainty_residual_annotation_map` | 预测 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_forecast_uncertainty_slope_change_view` | 预测 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_forecast_uncertainty_small_multiple_grid` | 小多图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_forecast_uncertainty_stratified_dotplot` | 预测 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_forecast_uncertainty_threshold_band` | 预测 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_forecast_uncertainty_uncertainty_ribbon` | 预测 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_forecast_uncertainty_violin_summary` | 预测 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_balance_annotated_reference_view` | Group balance diagnostic - Annotated reference view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_balance_boxen_interval` | Group balance diagnostic - Boxen interval plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_balance_comparative_lollipop` | Group balance diagnostic - Comparative lollipop plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_balance_density_ridge` | 密度图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_balance_diagnostic_panel` | Group balance diagnostic - Diagnostic panel | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_balance_ecdf_step_view` | 经验分布图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_balance_flow_transition_map` | Group balance diagnostic - Flow transition map | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_balance_forest_interval_plot` | 随机森林 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_balance_heatmap_matrix` | 热力矩阵 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_balance_histogram_facets` | 直方图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_balance_map_choropleth_layer` | 分级着色地图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_balance_mosaic_tile_view` | Group balance diagnostic - Mosaic tile view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_balance_network_node_link` | 关系网络 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_balance_qq_reference_plot` | Group balance diagnostic - Q-Q reference plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_balance_quantile_band` | 分位数 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_balance_raincloud_view` | Group balance diagnostic - Raincloud view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_balance_rank_interval_plot` | 排名 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_balance_residual_annotation_map` | Group balance diagnostic - Residual annotation map | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_balance_slope_change_view` | Group balance diagnostic - Slope change view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_balance_small_multiple_grid` | 小多图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_balance_stratified_dotplot` | Group balance diagnostic - Stratified dot plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_balance_threshold_band` | Group balance diagnostic - Threshold band | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_balance_uncertainty_ribbon` | Group balance diagnostic - Uncertainty ribbon | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_balance_violin_summary` | 小提琴图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_difference_annotated_reference_view` | Group difference evidence - Annotated reference view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_difference_boxen_interval` | Group difference evidence - Boxen interval plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_difference_comparative_lollipop` | Group difference evidence - Comparative lollipop plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_difference_density_ridge` | 密度图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_difference_diagnostic_panel` | Group difference evidence - Diagnostic panel | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_difference_ecdf_step_view` | 经验分布图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_difference_flow_transition_map` | Group difference evidence - Flow transition map | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_difference_forest_interval_plot` | 随机森林 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_difference_heatmap_matrix` | 热力矩阵 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_difference_histogram_facets` | 直方图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_difference_map_choropleth_layer` | 分级着色地图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_difference_mosaic_tile_view` | Group difference evidence - Mosaic tile view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_difference_network_node_link` | 关系网络 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_difference_qq_reference_plot` | Group difference evidence - Q-Q reference plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_difference_quantile_band` | 分位数 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_difference_raincloud_view` | Group difference evidence - Raincloud view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_difference_rank_interval_plot` | 排名 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_difference_residual_annotation_map` | Group difference evidence - Residual annotation map | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_difference_slope_change_view` | Group difference evidence - Slope change view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_difference_small_multiple_grid` | 小多图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_difference_stratified_dotplot` | Group difference evidence - Stratified dot plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_difference_threshold_band` | Group difference evidence - Threshold band | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_difference_uncertainty_ribbon` | Group difference evidence - Uncertainty ribbon | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_group_difference_violin_summary` | 小提琴图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_hazard_comparison_annotated_reference_view` | Hazard comparison - Annotated reference view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_hazard_comparison_boxen_interval` | Hazard comparison - Boxen interval plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_hazard_comparison_comparative_lollipop` | Hazard comparison - Comparative lollipop plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_hazard_comparison_density_ridge` | 密度图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_hazard_comparison_diagnostic_panel` | Hazard comparison - Diagnostic panel | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_hazard_comparison_ecdf_step_view` | 经验分布图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_hazard_comparison_flow_transition_map` | Hazard comparison - Flow transition map | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_hazard_comparison_forest_interval_plot` | 随机森林 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_hazard_comparison_heatmap_matrix` | 热力矩阵 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_hazard_comparison_histogram_facets` | 直方图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_hazard_comparison_map_choropleth_layer` | 分级着色地图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_hazard_comparison_mosaic_tile_view` | Hazard comparison - Mosaic tile view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_hazard_comparison_network_node_link` | 关系网络 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_hazard_comparison_qq_reference_plot` | Hazard comparison - Q-Q reference plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_hazard_comparison_quantile_band` | 分位数 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_hazard_comparison_raincloud_view` | Hazard comparison - Raincloud view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_hazard_comparison_rank_interval_plot` | 排名 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_hazard_comparison_residual_annotation_map` | Hazard comparison - Residual annotation map | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_hazard_comparison_slope_change_view` | Hazard comparison - Slope change view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_hazard_comparison_small_multiple_grid` | 小多图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_hazard_comparison_stratified_dotplot` | Hazard comparison - Stratified dot plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_hazard_comparison_threshold_band` | Hazard comparison - Threshold band | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_hazard_comparison_uncertainty_ribbon` | Hazard comparison - Uncertainty ribbon | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_hazard_comparison_violin_summary` | 小提琴图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_heteroscedasticity_pattern_annotated_reference_view` | Heteroscedasticity pattern - Annotated reference view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_heteroscedasticity_pattern_boxen_interval` | Heteroscedasticity pattern - Boxen interval plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_heteroscedasticity_pattern_comparative_lollipop` | Heteroscedasticity pattern - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_heteroscedasticity_pattern_density_ridge` | 密度图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_heteroscedasticity_pattern_diagnostic_panel` | Heteroscedasticity pattern - Diagnostic panel | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_heteroscedasticity_pattern_ecdf_step_view` | 经验分布图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_heteroscedasticity_pattern_flow_transition_map` | Heteroscedasticity pattern - Flow transition map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_heteroscedasticity_pattern_forest_interval_plot` | 随机森林 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_heteroscedasticity_pattern_heatmap_matrix` | 热力矩阵 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_heteroscedasticity_pattern_histogram_facets` | 直方图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_heteroscedasticity_pattern_map_choropleth_layer` | 分级着色地图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_heteroscedasticity_pattern_mosaic_tile_view` | Heteroscedasticity pattern - Mosaic tile view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_heteroscedasticity_pattern_network_node_link` | 关系网络 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_heteroscedasticity_pattern_qq_reference_plot` | Heteroscedasticity pattern - Q-Q reference plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_heteroscedasticity_pattern_quantile_band` | 分位数 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_heteroscedasticity_pattern_raincloud_view` | Heteroscedasticity pattern - Raincloud view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_heteroscedasticity_pattern_rank_interval_plot` | 排名 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_heteroscedasticity_pattern_residual_annotation_map` | Heteroscedasticity pattern - Residual annotation map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_heteroscedasticity_pattern_slope_change_view` | Heteroscedasticity pattern - Slope change view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_heteroscedasticity_pattern_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_heteroscedasticity_pattern_stratified_dotplot` | Heteroscedasticity pattern - Stratified dot plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_heteroscedasticity_pattern_threshold_band` | Heteroscedasticity pattern - Threshold band | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_heteroscedasticity_pattern_uncertainty_ribbon` | Heteroscedasticity pattern - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_heteroscedasticity_pattern_violin_summary` | 小提琴图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_instrument_strength_annotated_reference_view` | Instrument strength - Annotated reference view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_instrument_strength_boxen_interval` | Instrument strength - Boxen interval plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_instrument_strength_comparative_lollipop` | Instrument strength - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_instrument_strength_density_ridge` | 密度图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_instrument_strength_diagnostic_panel` | Instrument strength - Diagnostic panel | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_instrument_strength_ecdf_step_view` | 经验分布图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_instrument_strength_flow_transition_map` | Instrument strength - Flow transition map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_instrument_strength_forest_interval_plot` | 随机森林 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_instrument_strength_heatmap_matrix` | 热力矩阵 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_instrument_strength_histogram_facets` | 直方图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_instrument_strength_map_choropleth_layer` | 分级着色地图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_instrument_strength_mosaic_tile_view` | Instrument strength - Mosaic tile view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_instrument_strength_network_node_link` | 关系网络 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_instrument_strength_qq_reference_plot` | Instrument strength - Q-Q reference plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_instrument_strength_quantile_band` | 分位数 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_instrument_strength_raincloud_view` | Instrument strength - Raincloud view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_instrument_strength_rank_interval_plot` | 排名 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_instrument_strength_residual_annotation_map` | Instrument strength - Residual annotation map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_instrument_strength_slope_change_view` | Instrument strength - Slope change view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_instrument_strength_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_instrument_strength_stratified_dotplot` | Instrument strength - Stratified dot plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_instrument_strength_threshold_band` | Instrument strength - Threshold band | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_instrument_strength_uncertainty_ribbon` | Instrument strength - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_instrument_strength_violin_summary` | 小提琴图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inter_rater_agreement_annotated_reference_view` | Inter-rater agreement - Annotated reference view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inter_rater_agreement_boxen_interval` | Inter-rater agreement - Boxen interval plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inter_rater_agreement_comparative_lollipop` | Inter-rater agreement - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inter_rater_agreement_density_ridge` | 密度图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inter_rater_agreement_diagnostic_panel` | Inter-rater agreement - Diagnostic panel | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inter_rater_agreement_ecdf_step_view` | 经验分布图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inter_rater_agreement_flow_transition_map` | Inter-rater agreement - Flow transition map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inter_rater_agreement_forest_interval_plot` | 随机森林 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inter_rater_agreement_heatmap_matrix` | 热力矩阵 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inter_rater_agreement_histogram_facets` | 直方图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inter_rater_agreement_map_choropleth_layer` | 分级着色地图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inter_rater_agreement_mosaic_tile_view` | Inter-rater agreement - Mosaic tile view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inter_rater_agreement_network_node_link` | 关系网络 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inter_rater_agreement_qq_reference_plot` | Inter-rater agreement - Q-Q reference plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inter_rater_agreement_quantile_band` | 分位数 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inter_rater_agreement_raincloud_view` | Inter-rater agreement - Raincloud view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inter_rater_agreement_rank_interval_plot` | 排名 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inter_rater_agreement_residual_annotation_map` | Inter-rater agreement - Residual annotation map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inter_rater_agreement_slope_change_view` | Inter-rater agreement - Slope change view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inter_rater_agreement_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inter_rater_agreement_stratified_dotplot` | Inter-rater agreement - Stratified dot plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inter_rater_agreement_threshold_band` | Inter-rater agreement - Threshold band | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inter_rater_agreement_uncertainty_ribbon` | Inter-rater agreement - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inter_rater_agreement_violin_summary` | 小提琴图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_interaction_effect_annotated_reference_view` | Interaction effect - Annotated reference view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_interaction_effect_boxen_interval` | Interaction effect - Boxen interval plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_interaction_effect_comparative_lollipop` | Interaction effect - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_interaction_effect_density_ridge` | 密度图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_interaction_effect_diagnostic_panel` | Interaction effect - Diagnostic panel | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_interaction_effect_ecdf_step_view` | 经验分布图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_interaction_effect_flow_transition_map` | Interaction effect - Flow transition map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_interaction_effect_forest_interval_plot` | 随机森林 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_interaction_effect_heatmap_matrix` | 热力矩阵 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_interaction_effect_histogram_facets` | 直方图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_interaction_effect_map_choropleth_layer` | 分级着色地图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_interaction_effect_mosaic_tile_view` | Interaction effect - Mosaic tile view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_interaction_effect_network_node_link` | 关系网络 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_interaction_effect_qq_reference_plot` | Interaction effect - Q-Q reference plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_interaction_effect_quantile_band` | 分位数 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_interaction_effect_raincloud_view` | Interaction effect - Raincloud view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_interaction_effect_rank_interval_plot` | 排名 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_interaction_effect_residual_annotation_map` | Interaction effect - Residual annotation map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_interaction_effect_slope_change_view` | Interaction effect - Slope change view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_interaction_effect_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_interaction_effect_stratified_dotplot` | Interaction effect - Stratified dot plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_interaction_effect_threshold_band` | Interaction effect - Threshold band | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_interaction_effect_uncertainty_ribbon` | Interaction effect - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_interaction_effect_violin_summary` | 小提琴图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inventory_process_variation_annotated_reference_view` | Inventory process variation - Annotated reference view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inventory_process_variation_boxen_interval` | Inventory process variation - Boxen interval plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inventory_process_variation_comparative_lollipop` | Inventory process variation - Comparative lollipop plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inventory_process_variation_density_ridge` | 密度图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inventory_process_variation_diagnostic_panel` | Inventory process variation - Diagnostic panel | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inventory_process_variation_ecdf_step_view` | 经验分布图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inventory_process_variation_flow_transition_map` | Inventory process variation - Flow transition map | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inventory_process_variation_forest_interval_plot` | 随机森林 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inventory_process_variation_heatmap_matrix` | 热力矩阵 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inventory_process_variation_histogram_facets` | 直方图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inventory_process_variation_map_choropleth_layer` | 分级着色地图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inventory_process_variation_mosaic_tile_view` | Inventory process variation - Mosaic tile view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inventory_process_variation_network_node_link` | 关系网络 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inventory_process_variation_qq_reference_plot` | Inventory process variation - Q-Q reference plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inventory_process_variation_quantile_band` | 分位数 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inventory_process_variation_raincloud_view` | Inventory process variation - Raincloud view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inventory_process_variation_rank_interval_plot` | 排名 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inventory_process_variation_residual_annotation_map` | Inventory process variation - Residual annotation map | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inventory_process_variation_slope_change_view` | Inventory process variation - Slope change view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inventory_process_variation_small_multiple_grid` | 小多图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inventory_process_variation_stratified_dotplot` | Inventory process variation - Stratified dot plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inventory_process_variation_threshold_band` | Inventory process variation - Threshold band | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inventory_process_variation_uncertainty_ribbon` | Inventory process variation - Uncertainty ribbon | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_inventory_process_variation_violin_summary` | 小提琴图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_item_response_pattern_annotated_reference_view` | Item response pattern - Annotated reference view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_item_response_pattern_boxen_interval` | Item response pattern - Boxen interval plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_item_response_pattern_comparative_lollipop` | Item response pattern - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_item_response_pattern_density_ridge` | 密度图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_item_response_pattern_diagnostic_panel` | Item response pattern - Diagnostic panel | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_item_response_pattern_ecdf_step_view` | 经验分布图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_item_response_pattern_flow_transition_map` | Item response pattern - Flow transition map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_item_response_pattern_forest_interval_plot` | 随机森林 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_item_response_pattern_heatmap_matrix` | 热力矩阵 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_item_response_pattern_histogram_facets` | 直方图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_item_response_pattern_map_choropleth_layer` | 分级着色地图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_item_response_pattern_mosaic_tile_view` | Item response pattern - Mosaic tile view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_item_response_pattern_network_node_link` | 关系网络 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_item_response_pattern_qq_reference_plot` | Item response pattern - Q-Q reference plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_item_response_pattern_quantile_band` | 分位数 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_item_response_pattern_raincloud_view` | Item response pattern - Raincloud view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_item_response_pattern_rank_interval_plot` | 排名 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_item_response_pattern_residual_annotation_map` | Item response pattern - Residual annotation map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_item_response_pattern_slope_change_view` | Item response pattern - Slope change view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_item_response_pattern_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_item_response_pattern_stratified_dotplot` | Item response pattern - Stratified dot plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_item_response_pattern_threshold_band` | Item response pattern - Threshold band | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_item_response_pattern_uncertainty_ribbon` | Item response pattern - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_item_response_pattern_violin_summary` | 小提琴图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_lab_measurement_qc_annotated_reference_view` | Laboratory measurement QC - Annotated reference view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_lab_measurement_qc_boxen_interval` | Laboratory measurement QC - Boxen interval plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_lab_measurement_qc_comparative_lollipop` | Laboratory measurement QC - Comparative lollipop plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_lab_measurement_qc_density_ridge` | 密度图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_lab_measurement_qc_diagnostic_panel` | Laboratory measurement QC - Diagnostic panel | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_lab_measurement_qc_ecdf_step_view` | 经验分布图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_lab_measurement_qc_flow_transition_map` | Laboratory measurement QC - Flow transition map | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_lab_measurement_qc_forest_interval_plot` | 随机森林 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_lab_measurement_qc_heatmap_matrix` | 热力矩阵 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_lab_measurement_qc_histogram_facets` | 直方图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_lab_measurement_qc_map_choropleth_layer` | 分级着色地图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_lab_measurement_qc_mosaic_tile_view` | Laboratory measurement QC - Mosaic tile view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_lab_measurement_qc_network_node_link` | 关系网络 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_lab_measurement_qc_qq_reference_plot` | Laboratory measurement QC - Q-Q reference plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_lab_measurement_qc_quantile_band` | 分位数 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_lab_measurement_qc_raincloud_view` | Laboratory measurement QC - Raincloud view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_lab_measurement_qc_rank_interval_plot` | 排名 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_lab_measurement_qc_residual_annotation_map` | Laboratory measurement QC - Residual annotation map | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_lab_measurement_qc_slope_change_view` | Laboratory measurement QC - Slope change view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_lab_measurement_qc_small_multiple_grid` | 小多图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_lab_measurement_qc_stratified_dotplot` | Laboratory measurement QC - Stratified dot plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_lab_measurement_qc_threshold_band` | Laboratory measurement QC - Threshold band | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_lab_measurement_qc_uncertainty_ribbon` | Laboratory measurement QC - Uncertainty ribbon | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_lab_measurement_qc_violin_summary` | 小提琴图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_latent_construct_annotated_reference_view` | Latent construct - Annotated reference view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_latent_construct_boxen_interval` | Latent construct - Boxen interval plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_latent_construct_comparative_lollipop` | Latent construct - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_latent_construct_density_ridge` | 密度图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_latent_construct_diagnostic_panel` | Latent construct - Diagnostic panel | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_latent_construct_ecdf_step_view` | 经验分布图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_latent_construct_flow_transition_map` | Latent construct - Flow transition map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_latent_construct_forest_interval_plot` | 随机森林 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_latent_construct_heatmap_matrix` | 热力矩阵 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_latent_construct_histogram_facets` | 直方图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_latent_construct_map_choropleth_layer` | 分级着色地图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_latent_construct_mosaic_tile_view` | Latent construct - Mosaic tile view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_latent_construct_network_node_link` | 关系网络 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_latent_construct_qq_reference_plot` | Latent construct - Q-Q reference plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_latent_construct_quantile_band` | 分位数 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_latent_construct_raincloud_view` | Latent construct - Raincloud view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_latent_construct_rank_interval_plot` | 排名 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_latent_construct_residual_annotation_map` | Latent construct - Residual annotation map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_latent_construct_slope_change_view` | Latent construct - Slope change view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_latent_construct_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_latent_construct_stratified_dotplot` | Latent construct - Stratified dot plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_latent_construct_threshold_band` | Latent construct - Threshold band | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_latent_construct_uncertainty_ribbon` | Latent construct - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_latent_construct_violin_summary` | 小提琴图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_leverage_structure_annotated_reference_view` | Leverage structure - Annotated reference view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_leverage_structure_boxen_interval` | Leverage structure - Boxen interval plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_leverage_structure_comparative_lollipop` | Leverage structure - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_leverage_structure_density_ridge` | 密度图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_leverage_structure_diagnostic_panel` | Leverage structure - Diagnostic panel | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_leverage_structure_ecdf_step_view` | 经验分布图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_leverage_structure_flow_transition_map` | Leverage structure - Flow transition map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_leverage_structure_forest_interval_plot` | 随机森林 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_leverage_structure_heatmap_matrix` | 热力矩阵 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_leverage_structure_histogram_facets` | 直方图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_leverage_structure_map_choropleth_layer` | 分级着色地图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_leverage_structure_mosaic_tile_view` | Leverage structure - Mosaic tile view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_leverage_structure_network_node_link` | 关系网络 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_leverage_structure_qq_reference_plot` | Leverage structure - Q-Q reference plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_leverage_structure_quantile_band` | 分位数 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_leverage_structure_raincloud_view` | Leverage structure - Raincloud view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_leverage_structure_rank_interval_plot` | 排名 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_leverage_structure_residual_annotation_map` | Leverage structure - Residual annotation map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_leverage_structure_slope_change_view` | Leverage structure - Slope change view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_leverage_structure_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_leverage_structure_stratified_dotplot` | Leverage structure - Stratified dot plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_leverage_structure_threshold_band` | Leverage structure - Threshold band | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_leverage_structure_uncertainty_ribbon` | Leverage structure - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_leverage_structure_violin_summary` | 小提琴图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_longitudinal_trajectory_annotated_reference_view` | Longitudinal trajectory - Annotated reference view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_longitudinal_trajectory_boxen_interval` | Longitudinal trajectory - Boxen interval plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_longitudinal_trajectory_comparative_lollipop` | Longitudinal trajectory - Comparative lollipop plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_longitudinal_trajectory_density_ridge` | 密度图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_longitudinal_trajectory_diagnostic_panel` | Longitudinal trajectory - Diagnostic panel | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_longitudinal_trajectory_ecdf_step_view` | 经验分布图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_longitudinal_trajectory_flow_transition_map` | Longitudinal trajectory - Flow transition map | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_longitudinal_trajectory_forest_interval_plot` | 随机森林 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_longitudinal_trajectory_heatmap_matrix` | 热力矩阵 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_longitudinal_trajectory_histogram_facets` | 直方图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_longitudinal_trajectory_map_choropleth_layer` | 分级着色地图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_longitudinal_trajectory_mosaic_tile_view` | Longitudinal trajectory - Mosaic tile view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_longitudinal_trajectory_network_node_link` | 关系网络 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_longitudinal_trajectory_qq_reference_plot` | Longitudinal trajectory - Q-Q reference plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_longitudinal_trajectory_quantile_band` | 分位数 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_longitudinal_trajectory_raincloud_view` | Longitudinal trajectory - Raincloud view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_longitudinal_trajectory_rank_interval_plot` | 排名 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_longitudinal_trajectory_residual_annotation_map` | Longitudinal trajectory - Residual annotation map | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_longitudinal_trajectory_slope_change_view` | Longitudinal trajectory - Slope change view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_longitudinal_trajectory_small_multiple_grid` | 小多图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_longitudinal_trajectory_stratified_dotplot` | Longitudinal trajectory - Stratified dot plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_longitudinal_trajectory_threshold_band` | Longitudinal trajectory - Threshold band | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_longitudinal_trajectory_uncertainty_ribbon` | Longitudinal trajectory - Uncertainty ribbon | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_longitudinal_trajectory_violin_summary` | 小提琴图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manifold_structure_annotated_reference_view` | Manifold structure - Annotated reference view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manifold_structure_boxen_interval` | Manifold structure - Boxen interval plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manifold_structure_comparative_lollipop` | Manifold structure - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manifold_structure_density_ridge` | 密度图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manifold_structure_diagnostic_panel` | Manifold structure - Diagnostic panel | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manifold_structure_ecdf_step_view` | 经验分布图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manifold_structure_flow_transition_map` | Manifold structure - Flow transition map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manifold_structure_forest_interval_plot` | 随机森林 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manifold_structure_heatmap_matrix` | 热力矩阵 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manifold_structure_histogram_facets` | 直方图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manifold_structure_map_choropleth_layer` | 分级着色地图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manifold_structure_mosaic_tile_view` | Manifold structure - Mosaic tile view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manifold_structure_network_node_link` | 关系网络 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manifold_structure_qq_reference_plot` | Manifold structure - Q-Q reference plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manifold_structure_quantile_band` | 分位数 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manifold_structure_raincloud_view` | Manifold structure - Raincloud view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manifold_structure_rank_interval_plot` | 排名 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manifold_structure_residual_annotation_map` | Manifold structure - Residual annotation map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manifold_structure_slope_change_view` | Manifold structure - Slope change view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manifold_structure_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manifold_structure_stratified_dotplot` | Manifold structure - Stratified dot plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manifold_structure_threshold_band` | Manifold structure - Threshold band | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manifold_structure_uncertainty_ribbon` | Manifold structure - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manifold_structure_violin_summary` | 小提琴图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manufacturing_process_stability_annotated_reference_view` | Manufacturing process stability - Annotated reference view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manufacturing_process_stability_boxen_interval` | Manufacturing process stability - Boxen interval plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manufacturing_process_stability_comparative_lollipop` | Manufacturing process stability - Comparative lollipop plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manufacturing_process_stability_density_ridge` | 密度图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manufacturing_process_stability_diagnostic_panel` | Manufacturing process stability - Diagnostic panel | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manufacturing_process_stability_ecdf_step_view` | 经验分布图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manufacturing_process_stability_flow_transition_map` | Manufacturing process stability - Flow transition map | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manufacturing_process_stability_forest_interval_plot` | 随机森林 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manufacturing_process_stability_heatmap_matrix` | 热力矩阵 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manufacturing_process_stability_histogram_facets` | 直方图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manufacturing_process_stability_map_choropleth_layer` | 分级着色地图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manufacturing_process_stability_mosaic_tile_view` | Manufacturing process stability - Mosaic tile view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manufacturing_process_stability_network_node_link` | 关系网络 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manufacturing_process_stability_qq_reference_plot` | Manufacturing process stability - Q-Q reference plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manufacturing_process_stability_quantile_band` | 分位数 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manufacturing_process_stability_raincloud_view` | Manufacturing process stability - Raincloud view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manufacturing_process_stability_rank_interval_plot` | 排名 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manufacturing_process_stability_residual_annotation_map` | Manufacturing process stability - Residual annotation map | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manufacturing_process_stability_slope_change_view` | Manufacturing process stability - Slope change view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manufacturing_process_stability_small_multiple_grid` | 小多图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manufacturing_process_stability_stratified_dotplot` | Manufacturing process stability - Stratified dot plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manufacturing_process_stability_threshold_band` | Manufacturing process stability - Threshold band | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manufacturing_process_stability_uncertainty_ribbon` | Manufacturing process stability - Uncertainty ribbon | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_manufacturing_process_stability_violin_summary` | 小提琴图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_measurement_error_annotated_reference_view` | Measurement error - Annotated reference view | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_measurement_error_boxen_interval` | Measurement error - Boxen interval plot | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_measurement_error_comparative_lollipop` | Measurement error - Comparative lollipop plot | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_measurement_error_density_ridge` | 密度图 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_measurement_error_diagnostic_panel` | Measurement error - Diagnostic panel | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_measurement_error_ecdf_step_view` | 经验分布图 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_measurement_error_flow_transition_map` | Measurement error - Flow transition map | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_measurement_error_forest_interval_plot` | 随机森林 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_measurement_error_heatmap_matrix` | 热力矩阵 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_measurement_error_histogram_facets` | 直方图 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_measurement_error_map_choropleth_layer` | 分级着色地图 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_measurement_error_mosaic_tile_view` | Measurement error - Mosaic tile view | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_measurement_error_network_node_link` | 关系网络 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_measurement_error_qq_reference_plot` | Measurement error - Q-Q reference plot | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_measurement_error_quantile_band` | 分位数 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_measurement_error_raincloud_view` | Measurement error - Raincloud view | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_measurement_error_rank_interval_plot` | 排名 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_measurement_error_residual_annotation_map` | Measurement error - Residual annotation map | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_measurement_error_slope_change_view` | Measurement error - Slope change view | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_measurement_error_small_multiple_grid` | 小多图 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_measurement_error_stratified_dotplot` | Measurement error - Stratified dot plot | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_measurement_error_threshold_band` | Measurement error - Threshold band | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_measurement_error_uncertainty_ribbon` | Measurement error - Uncertainty ribbon | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_measurement_error_violin_summary` | 小提琴图 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mediation_path_annotated_reference_view` | Mediation path - Annotated reference view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mediation_path_boxen_interval` | Mediation path - Boxen interval plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mediation_path_comparative_lollipop` | Mediation path - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mediation_path_density_ridge` | 密度图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mediation_path_diagnostic_panel` | Mediation path - Diagnostic panel | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mediation_path_ecdf_step_view` | 经验分布图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mediation_path_flow_transition_map` | Mediation path - Flow transition map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mediation_path_forest_interval_plot` | 随机森林 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mediation_path_heatmap_matrix` | 热力矩阵 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mediation_path_histogram_facets` | 直方图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mediation_path_map_choropleth_layer` | 分级着色地图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mediation_path_mosaic_tile_view` | Mediation path - Mosaic tile view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mediation_path_network_node_link` | 关系网络 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mediation_path_qq_reference_plot` | Mediation path - Q-Q reference plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mediation_path_quantile_band` | 分位数 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mediation_path_raincloud_view` | Mediation path - Raincloud view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mediation_path_rank_interval_plot` | 排名 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mediation_path_residual_annotation_map` | Mediation path - Residual annotation map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mediation_path_slope_change_view` | Mediation path - Slope change view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mediation_path_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mediation_path_stratified_dotplot` | Mediation path - Stratified dot plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mediation_path_threshold_band` | Mediation path - Threshold band | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mediation_path_uncertainty_ribbon` | Mediation path - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mediation_path_violin_summary` | 小提琴图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_missingness_pattern_annotated_reference_view` | 缺失情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_missingness_pattern_boxen_interval` | 缺失情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_missingness_pattern_comparative_lollipop` | 缺失情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_missingness_pattern_density_ridge` | 缺失情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_missingness_pattern_diagnostic_panel` | 缺失情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_missingness_pattern_ecdf_step_view` | 缺失情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_missingness_pattern_flow_transition_map` | 缺失情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_missingness_pattern_forest_interval_plot` | 缺失情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_missingness_pattern_heatmap_matrix` | 缺失情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_missingness_pattern_histogram_facets` | 缺失情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_missingness_pattern_map_choropleth_layer` | 缺失情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_missingness_pattern_mosaic_tile_view` | 缺失情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_missingness_pattern_network_node_link` | 缺失情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_missingness_pattern_qq_reference_plot` | 缺失情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_missingness_pattern_quantile_band` | 缺失情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_missingness_pattern_raincloud_view` | 缺失情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_missingness_pattern_rank_interval_plot` | 缺失情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_missingness_pattern_residual_annotation_map` | 缺失情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_missingness_pattern_slope_change_view` | 缺失情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_missingness_pattern_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_missingness_pattern_stratified_dotplot` | 缺失情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_missingness_pattern_threshold_band` | 缺失情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_missingness_pattern_uncertainty_ribbon` | 缺失情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_missingness_pattern_violin_summary` | 缺失情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mobility_flow_annotated_reference_view` | Mobility flow - Annotated reference view | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mobility_flow_boxen_interval` | Mobility flow - Boxen interval plot | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mobility_flow_comparative_lollipop` | Mobility flow - Comparative lollipop plot | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mobility_flow_density_ridge` | 密度图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mobility_flow_diagnostic_panel` | Mobility flow - Diagnostic panel | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mobility_flow_ecdf_step_view` | 经验分布图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mobility_flow_flow_transition_map` | Mobility flow - Flow transition map | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mobility_flow_forest_interval_plot` | 随机森林 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mobility_flow_heatmap_matrix` | 热力矩阵 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mobility_flow_histogram_facets` | 直方图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mobility_flow_map_choropleth_layer` | 流向地图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mobility_flow_mosaic_tile_view` | Mobility flow - Mosaic tile view | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mobility_flow_network_node_link` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mobility_flow_qq_reference_plot` | Mobility flow - Q-Q reference plot | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mobility_flow_quantile_band` | 分位数 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mobility_flow_raincloud_view` | Mobility flow - Raincloud view | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mobility_flow_rank_interval_plot` | 排名 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mobility_flow_residual_annotation_map` | Mobility flow - Residual annotation map | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mobility_flow_slope_change_view` | Mobility flow - Slope change view | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mobility_flow_small_multiple_grid` | 小多图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mobility_flow_stratified_dotplot` | Mobility flow - Stratified dot plot | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mobility_flow_threshold_band` | Mobility flow - Threshold band | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mobility_flow_uncertainty_ribbon` | Mobility flow - Uncertainty ribbon | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_mobility_flow_violin_summary` | 小提琴图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_model_fit_annotated_reference_view` | Model fit diagnostic - Annotated reference view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_model_fit_boxen_interval` | Model fit diagnostic - Boxen interval plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_model_fit_comparative_lollipop` | Model fit diagnostic - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_model_fit_density_ridge` | 密度图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_model_fit_diagnostic_panel` | Model fit diagnostic - Diagnostic panel | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_model_fit_ecdf_step_view` | 经验分布图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_model_fit_flow_transition_map` | Model fit diagnostic - Flow transition map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_model_fit_forest_interval_plot` | 随机森林 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_model_fit_heatmap_matrix` | 热力矩阵 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_model_fit_histogram_facets` | 直方图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_model_fit_map_choropleth_layer` | 分级着色地图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_model_fit_mosaic_tile_view` | Model fit diagnostic - Mosaic tile view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_model_fit_network_node_link` | 关系网络 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_model_fit_qq_reference_plot` | Model fit diagnostic - Q-Q reference plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_model_fit_quantile_band` | 分位数 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_model_fit_raincloud_view` | Model fit diagnostic - Raincloud view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_model_fit_rank_interval_plot` | 排名 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_model_fit_residual_annotation_map` | Model fit diagnostic - Residual annotation map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_model_fit_slope_change_view` | Model fit diagnostic - Slope change view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_model_fit_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_model_fit_stratified_dotplot` | Model fit diagnostic - Stratified dot plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_model_fit_threshold_band` | Model fit diagnostic - Threshold band | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_model_fit_uncertainty_ribbon` | Model fit diagnostic - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_model_fit_violin_summary` | 小提琴图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_multivariate_projection_annotated_reference_view` | Multivariate projection - Annotated reference view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_multivariate_projection_boxen_interval` | Multivariate projection - Boxen interval plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_multivariate_projection_comparative_lollipop` | Multivariate projection - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_multivariate_projection_density_ridge` | 密度图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_multivariate_projection_diagnostic_panel` | Multivariate projection - Diagnostic panel | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_multivariate_projection_ecdf_step_view` | 经验分布图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_multivariate_projection_flow_transition_map` | Multivariate projection - Flow transition map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_multivariate_projection_forest_interval_plot` | 随机森林 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_multivariate_projection_heatmap_matrix` | 热力矩阵 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_multivariate_projection_histogram_facets` | 直方图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_multivariate_projection_map_choropleth_layer` | 分级着色地图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_multivariate_projection_mosaic_tile_view` | Multivariate projection - Mosaic tile view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_multivariate_projection_network_node_link` | 关系网络 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_multivariate_projection_qq_reference_plot` | Multivariate projection - Q-Q reference plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_multivariate_projection_quantile_band` | 分位数 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_multivariate_projection_raincloud_view` | Multivariate projection - Raincloud view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_multivariate_projection_rank_interval_plot` | 排名 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_multivariate_projection_residual_annotation_map` | Multivariate projection - Residual annotation map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_multivariate_projection_slope_change_view` | Multivariate projection - Slope change view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_multivariate_projection_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_multivariate_projection_stratified_dotplot` | Multivariate projection - Stratified dot plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_multivariate_projection_threshold_band` | Multivariate projection - Threshold band | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_multivariate_projection_uncertainty_ribbon` | Multivariate projection - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_multivariate_projection_violin_summary` | 小提琴图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_bridge_annotated_reference_view` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_bridge_boxen_interval` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_bridge_comparative_lollipop` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_bridge_density_ridge` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_bridge_diagnostic_panel` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_bridge_ecdf_step_view` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_bridge_flow_transition_map` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_bridge_forest_interval_plot` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_bridge_heatmap_matrix` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_bridge_histogram_facets` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_bridge_map_choropleth_layer` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_bridge_mosaic_tile_view` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_bridge_network_node_link` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_bridge_qq_reference_plot` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_bridge_quantile_band` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_bridge_raincloud_view` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_bridge_rank_interval_plot` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_bridge_residual_annotation_map` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_bridge_slope_change_view` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_bridge_small_multiple_grid` | 小多图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_bridge_stratified_dotplot` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_bridge_threshold_band` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_bridge_uncertainty_ribbon` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_bridge_violin_summary` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_centrality_annotated_reference_view` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_centrality_boxen_interval` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_centrality_comparative_lollipop` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_centrality_density_ridge` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_centrality_diagnostic_panel` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_centrality_ecdf_step_view` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_centrality_flow_transition_map` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_centrality_forest_interval_plot` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_centrality_heatmap_matrix` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_centrality_histogram_facets` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_centrality_map_choropleth_layer` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_centrality_mosaic_tile_view` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_centrality_network_node_link` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_centrality_qq_reference_plot` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_centrality_quantile_band` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_centrality_raincloud_view` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_centrality_rank_interval_plot` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_centrality_residual_annotation_map` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_centrality_slope_change_view` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_centrality_small_multiple_grid` | 小多图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_centrality_stratified_dotplot` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_centrality_threshold_band` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_centrality_uncertainty_ribbon` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_centrality_violin_summary` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_diffusion_annotated_reference_view` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_diffusion_boxen_interval` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_diffusion_comparative_lollipop` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_diffusion_density_ridge` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_diffusion_diagnostic_panel` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_diffusion_ecdf_step_view` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_diffusion_flow_transition_map` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_diffusion_forest_interval_plot` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_diffusion_heatmap_matrix` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_diffusion_histogram_facets` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_diffusion_map_choropleth_layer` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_diffusion_mosaic_tile_view` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_diffusion_network_node_link` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_diffusion_qq_reference_plot` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_diffusion_quantile_band` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_diffusion_raincloud_view` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_diffusion_rank_interval_plot` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_diffusion_residual_annotation_map` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_diffusion_slope_change_view` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_diffusion_small_multiple_grid` | 小多图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_diffusion_stratified_dotplot` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_diffusion_threshold_band` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_diffusion_uncertainty_ribbon` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_network_diffusion_violin_summary` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_fit_shape_annotated_reference_view` | Nonlinear fit shape - Annotated reference view | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_fit_shape_boxen_interval` | Nonlinear fit shape - Boxen interval plot | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_fit_shape_comparative_lollipop` | Nonlinear fit shape - Comparative lollipop plot | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_fit_shape_density_ridge` | 密度图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_fit_shape_diagnostic_panel` | Nonlinear fit shape - Diagnostic panel | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_fit_shape_ecdf_step_view` | 经验分布图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_fit_shape_flow_transition_map` | Nonlinear fit shape - Flow transition map | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_fit_shape_forest_interval_plot` | 随机森林 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_fit_shape_heatmap_matrix` | 热力矩阵 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_fit_shape_histogram_facets` | 直方图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_fit_shape_map_choropleth_layer` | 分级着色地图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_fit_shape_mosaic_tile_view` | Nonlinear fit shape - Mosaic tile view | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_fit_shape_network_node_link` | 关系网络 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_fit_shape_qq_reference_plot` | Nonlinear fit shape - Q-Q reference plot | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_fit_shape_quantile_band` | 分位数 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_fit_shape_raincloud_view` | Nonlinear fit shape - Raincloud view | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_fit_shape_rank_interval_plot` | 排名 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_fit_shape_residual_annotation_map` | Nonlinear fit shape - Residual annotation map | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_fit_shape_slope_change_view` | Nonlinear fit shape - Slope change view | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_fit_shape_small_multiple_grid` | 小多图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_fit_shape_stratified_dotplot` | Nonlinear fit shape - Stratified dot plot | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_fit_shape_threshold_band` | Nonlinear fit shape - Threshold band | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_fit_shape_uncertainty_ribbon` | Nonlinear fit shape - Uncertainty ribbon | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_fit_shape_violin_summary` | 小提琴图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_relationship_annotated_reference_view` | Nonlinear relationship - Annotated reference view | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_relationship_boxen_interval` | Nonlinear relationship - Boxen interval plot | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_relationship_comparative_lollipop` | Nonlinear relationship - Comparative lollipop plot | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_relationship_density_ridge` | 密度图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_relationship_diagnostic_panel` | Nonlinear relationship - Diagnostic panel | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_relationship_ecdf_step_view` | 经验分布图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_relationship_flow_transition_map` | Nonlinear relationship - Flow transition map | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_relationship_forest_interval_plot` | 随机森林 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_relationship_heatmap_matrix` | 热力矩阵 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_relationship_histogram_facets` | 直方图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_relationship_map_choropleth_layer` | 分级着色地图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_relationship_mosaic_tile_view` | Nonlinear relationship - Mosaic tile view | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_relationship_network_node_link` | 关系网络 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_relationship_qq_reference_plot` | Nonlinear relationship - Q-Q reference plot | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_relationship_quantile_band` | 分位数 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_relationship_raincloud_view` | Nonlinear relationship - Raincloud view | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_relationship_rank_interval_plot` | 排名 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_relationship_residual_annotation_map` | Nonlinear relationship - Residual annotation map | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_relationship_slope_change_view` | Nonlinear relationship - Slope change view | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_relationship_small_multiple_grid` | 小多图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_relationship_stratified_dotplot` | Nonlinear relationship - Stratified dot plot | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_relationship_threshold_band` | Nonlinear relationship - Threshold band | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_relationship_uncertainty_ribbon` | Nonlinear relationship - Uncertainty ribbon | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonlinear_relationship_violin_summary` | 小提琴图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonresponse_pattern_annotated_reference_view` | Nonresponse pattern - Annotated reference view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonresponse_pattern_boxen_interval` | Nonresponse pattern - Boxen interval plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonresponse_pattern_comparative_lollipop` | Nonresponse pattern - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonresponse_pattern_density_ridge` | 密度图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonresponse_pattern_diagnostic_panel` | Nonresponse pattern - Diagnostic panel | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonresponse_pattern_ecdf_step_view` | 经验分布图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonresponse_pattern_flow_transition_map` | Nonresponse pattern - Flow transition map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonresponse_pattern_forest_interval_plot` | 随机森林 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonresponse_pattern_heatmap_matrix` | 热力矩阵 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonresponse_pattern_histogram_facets` | 直方图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonresponse_pattern_map_choropleth_layer` | 分级着色地图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonresponse_pattern_mosaic_tile_view` | Nonresponse pattern - Mosaic tile view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonresponse_pattern_network_node_link` | 关系网络 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonresponse_pattern_qq_reference_plot` | Nonresponse pattern - Q-Q reference plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonresponse_pattern_quantile_band` | 分位数 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonresponse_pattern_raincloud_view` | Nonresponse pattern - Raincloud view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonresponse_pattern_rank_interval_plot` | 排名 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonresponse_pattern_residual_annotation_map` | Nonresponse pattern - Residual annotation map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonresponse_pattern_slope_change_view` | Nonresponse pattern - Slope change view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonresponse_pattern_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonresponse_pattern_stratified_dotplot` | Nonresponse pattern - Stratified dot plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonresponse_pattern_threshold_band` | Nonresponse pattern - Threshold band | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonresponse_pattern_uncertainty_ribbon` | Nonresponse pattern - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_nonresponse_pattern_violin_summary` | 小提琴图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_operations_capacity_annotated_reference_view` | Operations capacity - Annotated reference view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_operations_capacity_boxen_interval` | Operations capacity - Boxen interval plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_operations_capacity_comparative_lollipop` | Operations capacity - Comparative lollipop plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_operations_capacity_density_ridge` | 密度图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_operations_capacity_diagnostic_panel` | Operations capacity - Diagnostic panel | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_operations_capacity_ecdf_step_view` | 经验分布图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_operations_capacity_flow_transition_map` | Operations capacity - Flow transition map | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_operations_capacity_forest_interval_plot` | 随机森林 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_operations_capacity_heatmap_matrix` | 热力矩阵 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_operations_capacity_histogram_facets` | 直方图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_operations_capacity_map_choropleth_layer` | 分级着色地图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_operations_capacity_mosaic_tile_view` | Operations capacity - Mosaic tile view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_operations_capacity_network_node_link` | 关系网络 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_operations_capacity_qq_reference_plot` | Operations capacity - Q-Q reference plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_operations_capacity_quantile_band` | 分位数 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_operations_capacity_raincloud_view` | Operations capacity - Raincloud view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_operations_capacity_rank_interval_plot` | 排名 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_operations_capacity_residual_annotation_map` | Operations capacity - Residual annotation map | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_operations_capacity_slope_change_view` | Operations capacity - Slope change view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_operations_capacity_small_multiple_grid` | 小多图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_operations_capacity_stratified_dotplot` | Operations capacity - Stratified dot plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_operations_capacity_threshold_band` | Operations capacity - Threshold band | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_operations_capacity_uncertainty_ribbon` | Operations capacity - Uncertainty ribbon | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_operations_capacity_violin_summary` | 小提琴图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_ordinal_response_annotated_reference_view` | Ordinal response profile - Annotated reference view | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_ordinal_response_boxen_interval` | Ordinal response profile - Boxen interval plot | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_ordinal_response_comparative_lollipop` | Ordinal response profile - Comparative lollipop plot | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_ordinal_response_density_ridge` | 密度图 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_ordinal_response_diagnostic_panel` | Ordinal response profile - Diagnostic panel | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_ordinal_response_ecdf_step_view` | 经验分布图 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_ordinal_response_flow_transition_map` | Ordinal response profile - Flow transition map | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_ordinal_response_forest_interval_plot` | 随机森林 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_ordinal_response_heatmap_matrix` | 热力矩阵 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_ordinal_response_histogram_facets` | 直方图 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_ordinal_response_map_choropleth_layer` | 分级着色地图 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_ordinal_response_mosaic_tile_view` | Ordinal response profile - Mosaic tile view | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_ordinal_response_network_node_link` | 关系网络 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_ordinal_response_qq_reference_plot` | Ordinal response profile - Q-Q reference plot | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_ordinal_response_quantile_band` | 分位数 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_ordinal_response_raincloud_view` | Ordinal response profile - Raincloud view | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_ordinal_response_rank_interval_plot` | 排名 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_ordinal_response_residual_annotation_map` | Ordinal response profile - Residual annotation map | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_ordinal_response_slope_change_view` | Ordinal response profile - Slope change view | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_ordinal_response_small_multiple_grid` | 小多图 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_ordinal_response_stratified_dotplot` | Ordinal response profile - Stratified dot plot | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_ordinal_response_threshold_band` | Ordinal response profile - Threshold band | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_ordinal_response_uncertainty_ribbon` | Ordinal response profile - Uncertainty ribbon | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_ordinal_response_violin_summary` | 小提琴图 | 图表 | 分类字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_outlier_influence_annotated_reference_view` | Outlier influence - Annotated reference view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_outlier_influence_boxen_interval` | Outlier influence - Boxen interval plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_outlier_influence_comparative_lollipop` | Outlier influence - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_outlier_influence_density_ridge` | 密度图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_outlier_influence_diagnostic_panel` | Outlier influence - Diagnostic panel | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_outlier_influence_ecdf_step_view` | 经验分布图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_outlier_influence_flow_transition_map` | Outlier influence - Flow transition map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_outlier_influence_forest_interval_plot` | 随机森林 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_outlier_influence_heatmap_matrix` | 热力矩阵 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_outlier_influence_histogram_facets` | 直方图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_outlier_influence_map_choropleth_layer` | 分级着色地图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_outlier_influence_mosaic_tile_view` | Outlier influence - Mosaic tile view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_outlier_influence_network_node_link` | 关系网络 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_outlier_influence_qq_reference_plot` | Outlier influence - Q-Q reference plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_outlier_influence_quantile_band` | 分位数 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_outlier_influence_raincloud_view` | Outlier influence - Raincloud view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_outlier_influence_rank_interval_plot` | 排名 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_outlier_influence_residual_annotation_map` | Outlier influence - Residual annotation map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_outlier_influence_slope_change_view` | Outlier influence - Slope change view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_outlier_influence_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_outlier_influence_stratified_dotplot` | Outlier influence - Stratified dot plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_outlier_influence_threshold_band` | Outlier influence - Threshold band | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_outlier_influence_uncertainty_ribbon` | Outlier influence - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_outlier_influence_violin_summary` | 小提琴图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_paired_change_annotated_reference_view` | Paired change - Annotated reference view | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_paired_change_boxen_interval` | Paired change - Boxen interval plot | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_paired_change_comparative_lollipop` | Paired change - Comparative lollipop plot | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_paired_change_density_ridge` | 密度图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_paired_change_diagnostic_panel` | Paired change - Diagnostic panel | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_paired_change_ecdf_step_view` | 经验分布图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_paired_change_flow_transition_map` | Paired change - Flow transition map | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_paired_change_forest_interval_plot` | 随机森林 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_paired_change_heatmap_matrix` | 热力矩阵 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_paired_change_histogram_facets` | 直方图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_paired_change_map_choropleth_layer` | 分级着色地图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_paired_change_mosaic_tile_view` | Paired change - Mosaic tile view | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_paired_change_network_node_link` | 关系网络 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_paired_change_qq_reference_plot` | Paired change - Q-Q reference plot | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_paired_change_quantile_band` | 分位数 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_paired_change_raincloud_view` | Paired change - Raincloud view | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_paired_change_rank_interval_plot` | 排名 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_paired_change_residual_annotation_map` | Paired change - Residual annotation map | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_paired_change_slope_change_view` | Paired change - Slope change view | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_paired_change_small_multiple_grid` | 小多图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_paired_change_stratified_dotplot` | Paired change - Stratified dot plot | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_paired_change_threshold_band` | Paired change - Threshold band | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_paired_change_uncertainty_ribbon` | Paired change - Uncertainty ribbon | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_paired_change_violin_summary` | 小提琴图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_partial_association_annotated_reference_view` | 偏相关 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_partial_association_boxen_interval` | 偏相关 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_partial_association_comparative_lollipop` | 偏相关 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_partial_association_density_ridge` | 偏相关 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_partial_association_diagnostic_panel` | 偏相关 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_partial_association_ecdf_step_view` | 偏相关 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_partial_association_flow_transition_map` | 偏相关 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_partial_association_forest_interval_plot` | 偏相关 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_partial_association_heatmap_matrix` | 偏相关 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_partial_association_histogram_facets` | 偏相关 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_partial_association_map_choropleth_layer` | 偏相关 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_partial_association_mosaic_tile_view` | 偏相关 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_partial_association_network_node_link` | 偏相关 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_partial_association_qq_reference_plot` | 偏相关 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_partial_association_quantile_band` | 偏相关 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_partial_association_raincloud_view` | 偏相关 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_partial_association_rank_interval_plot` | 偏相关 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_partial_association_residual_annotation_map` | 偏相关 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_partial_association_slope_change_view` | 偏相关 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_partial_association_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_partial_association_stratified_dotplot` | 偏相关 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_partial_association_threshold_band` | 偏相关 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_partial_association_uncertainty_ribbon` | 偏相关 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_partial_association_violin_summary` | 偏相关 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_patient_trajectory_annotated_reference_view` | Patient trajectory - Annotated reference view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_patient_trajectory_boxen_interval` | Patient trajectory - Boxen interval plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_patient_trajectory_comparative_lollipop` | Patient trajectory - Comparative lollipop plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_patient_trajectory_density_ridge` | 密度图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_patient_trajectory_diagnostic_panel` | Patient trajectory - Diagnostic panel | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_patient_trajectory_ecdf_step_view` | 经验分布图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_patient_trajectory_flow_transition_map` | Patient trajectory - Flow transition map | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_patient_trajectory_forest_interval_plot` | 随机森林 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_patient_trajectory_heatmap_matrix` | 热力矩阵 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_patient_trajectory_histogram_facets` | 直方图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_patient_trajectory_map_choropleth_layer` | 分级着色地图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_patient_trajectory_mosaic_tile_view` | Patient trajectory - Mosaic tile view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_patient_trajectory_network_node_link` | 关系网络 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_patient_trajectory_qq_reference_plot` | Patient trajectory - Q-Q reference plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_patient_trajectory_quantile_band` | 分位数 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_patient_trajectory_raincloud_view` | Patient trajectory - Raincloud view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_patient_trajectory_rank_interval_plot` | 排名 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_patient_trajectory_residual_annotation_map` | Patient trajectory - Residual annotation map | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_patient_trajectory_slope_change_view` | Patient trajectory - Slope change view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_patient_trajectory_small_multiple_grid` | 小多图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_patient_trajectory_stratified_dotplot` | Patient trajectory - Stratified dot plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_patient_trajectory_threshold_band` | Patient trajectory - Threshold band | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_patient_trajectory_uncertainty_ribbon` | Patient trajectory - Uncertainty ribbon | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_patient_trajectory_violin_summary` | 小提琴图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_error_annotated_reference_view` | Prediction error - Annotated reference view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_error_boxen_interval` | Prediction error - Boxen interval plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_error_comparative_lollipop` | Prediction error - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_error_density_ridge` | 密度图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_error_diagnostic_panel` | Prediction error - Diagnostic panel | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_error_ecdf_step_view` | 经验分布图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_error_flow_transition_map` | Prediction error - Flow transition map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_error_forest_interval_plot` | 随机森林 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_error_heatmap_matrix` | 热力矩阵 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_error_histogram_facets` | 直方图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_error_map_choropleth_layer` | 分级着色地图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_error_mosaic_tile_view` | Prediction error - Mosaic tile view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_error_network_node_link` | 关系网络 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_error_qq_reference_plot` | Prediction error - Q-Q reference plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_error_quantile_band` | 分位数 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_error_raincloud_view` | Prediction error - Raincloud view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_error_rank_interval_plot` | 排名 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_error_residual_annotation_map` | Prediction error - Residual annotation map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_error_slope_change_view` | Prediction error - Slope change view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_error_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_error_stratified_dotplot` | Prediction error - Stratified dot plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_error_threshold_band` | Prediction error - Threshold band | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_error_uncertainty_ribbon` | Prediction error - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_error_violin_summary` | 小提琴图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_interval_annotated_reference_view` | Prediction interval - Annotated reference view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_interval_boxen_interval` | Prediction interval - Boxen interval plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_interval_comparative_lollipop` | Prediction interval - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_interval_density_ridge` | 密度图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_interval_diagnostic_panel` | Prediction interval - Diagnostic panel | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_interval_ecdf_step_view` | 经验分布图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_interval_flow_transition_map` | Prediction interval - Flow transition map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_interval_forest_interval_plot` | 随机森林 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_interval_heatmap_matrix` | 热力矩阵 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_interval_histogram_facets` | 直方图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_interval_map_choropleth_layer` | 分级着色地图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_interval_mosaic_tile_view` | Prediction interval - Mosaic tile view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_interval_network_node_link` | 关系网络 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_interval_qq_reference_plot` | Prediction interval - Q-Q reference plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_interval_quantile_band` | 分位数 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_interval_raincloud_view` | Prediction interval - Raincloud view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_interval_rank_interval_plot` | 排名 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_interval_residual_annotation_map` | Prediction interval - Residual annotation map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_interval_slope_change_view` | Prediction interval - Slope change view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_interval_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_interval_stratified_dotplot` | Prediction interval - Stratified dot plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_interval_threshold_band` | Prediction interval - Threshold band | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_interval_uncertainty_ribbon` | Prediction interval - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_prediction_interval_violin_summary` | 小提琴图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_principal_component_variance_annotated_reference_view` | 方差 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_principal_component_variance_boxen_interval` | 方差 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_principal_component_variance_comparative_lollipop` | 方差 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_principal_component_variance_density_ridge` | 方差 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_principal_component_variance_diagnostic_panel` | 方差 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_principal_component_variance_ecdf_step_view` | 方差 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_principal_component_variance_flow_transition_map` | 方差 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_principal_component_variance_forest_interval_plot` | 方差 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_principal_component_variance_heatmap_matrix` | 方差 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_principal_component_variance_histogram_facets` | 方差 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_principal_component_variance_map_choropleth_layer` | 方差 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_principal_component_variance_mosaic_tile_view` | 方差 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_principal_component_variance_network_node_link` | 方差 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_principal_component_variance_qq_reference_plot` | 方差 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_principal_component_variance_quantile_band` | 方差 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_principal_component_variance_raincloud_view` | 方差 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_principal_component_variance_rank_interval_plot` | 方差 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_principal_component_variance_residual_annotation_map` | 方差 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_principal_component_variance_slope_change_view` | 方差 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_principal_component_variance_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_principal_component_variance_stratified_dotplot` | 方差 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_principal_component_variance_threshold_band` | 方差 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_principal_component_variance_uncertainty_ribbon` | 方差 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_principal_component_variance_violin_summary` | 方差 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_propensity_overlap_annotated_reference_view` | Propensity overlap - Annotated reference view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_propensity_overlap_boxen_interval` | Propensity overlap - Boxen interval plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_propensity_overlap_comparative_lollipop` | Propensity overlap - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_propensity_overlap_density_ridge` | 密度图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_propensity_overlap_diagnostic_panel` | Propensity overlap - Diagnostic panel | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_propensity_overlap_ecdf_step_view` | 经验分布图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_propensity_overlap_flow_transition_map` | Propensity overlap - Flow transition map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_propensity_overlap_forest_interval_plot` | 随机森林 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_propensity_overlap_heatmap_matrix` | 热力矩阵 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_propensity_overlap_histogram_facets` | 直方图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_propensity_overlap_map_choropleth_layer` | 分级着色地图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_propensity_overlap_mosaic_tile_view` | Propensity overlap - Mosaic tile view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_propensity_overlap_network_node_link` | 关系网络 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_propensity_overlap_qq_reference_plot` | Propensity overlap - Q-Q reference plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_propensity_overlap_quantile_band` | 分位数 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_propensity_overlap_raincloud_view` | Propensity overlap - Raincloud view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_propensity_overlap_rank_interval_plot` | 排名 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_propensity_overlap_residual_annotation_map` | Propensity overlap - Residual annotation map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_propensity_overlap_slope_change_view` | Propensity overlap - Slope change view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_propensity_overlap_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_propensity_overlap_stratified_dotplot` | Propensity overlap - Stratified dot plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_propensity_overlap_threshold_band` | Propensity overlap - Threshold band | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_propensity_overlap_uncertainty_ribbon` | Propensity overlap - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_propensity_overlap_violin_summary` | 小提琴图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_public_health_incidence_annotated_reference_view` | Public health incidence - Annotated reference view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_public_health_incidence_boxen_interval` | Public health incidence - Boxen interval plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_public_health_incidence_comparative_lollipop` | Public health incidence - Comparative lollipop plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_public_health_incidence_density_ridge` | 密度图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_public_health_incidence_diagnostic_panel` | Public health incidence - Diagnostic panel | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_public_health_incidence_ecdf_step_view` | 经验分布图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_public_health_incidence_flow_transition_map` | Public health incidence - Flow transition map | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_public_health_incidence_forest_interval_plot` | 随机森林 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_public_health_incidence_heatmap_matrix` | 热力矩阵 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_public_health_incidence_histogram_facets` | 直方图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_public_health_incidence_map_choropleth_layer` | 分级着色地图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_public_health_incidence_mosaic_tile_view` | Public health incidence - Mosaic tile view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_public_health_incidence_network_node_link` | 关系网络 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_public_health_incidence_qq_reference_plot` | Public health incidence - Q-Q reference plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_public_health_incidence_quantile_band` | 分位数 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_public_health_incidence_raincloud_view` | Public health incidence - Raincloud view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_public_health_incidence_rank_interval_plot` | 排名 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_public_health_incidence_residual_annotation_map` | Public health incidence - Residual annotation map | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_public_health_incidence_slope_change_view` | Public health incidence - Slope change view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_public_health_incidence_small_multiple_grid` | 小多图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_public_health_incidence_stratified_dotplot` | Public health incidence - Stratified dot plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_public_health_incidence_threshold_band` | Public health incidence - Threshold band | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_public_health_incidence_uncertainty_ribbon` | Public health incidence - Uncertainty ribbon | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_public_health_incidence_violin_summary` | 小提琴图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_quality_control_annotated_reference_view` | Quality control - Annotated reference view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_quality_control_boxen_interval` | Quality control - Boxen interval plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_quality_control_comparative_lollipop` | Quality control - Comparative lollipop plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_quality_control_density_ridge` | 密度图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_quality_control_diagnostic_panel` | Quality control - Diagnostic panel | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_quality_control_ecdf_step_view` | 经验分布图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_quality_control_flow_transition_map` | Quality control - Flow transition map | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_quality_control_forest_interval_plot` | 随机森林 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_quality_control_heatmap_matrix` | 热力矩阵 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_quality_control_histogram_facets` | 直方图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_quality_control_map_choropleth_layer` | 分级着色地图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_quality_control_mosaic_tile_view` | Quality control - Mosaic tile view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_quality_control_network_node_link` | 关系网络 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_quality_control_qq_reference_plot` | Quality control - Q-Q reference plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_quality_control_quantile_band` | 分位数 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_quality_control_raincloud_view` | Quality control - Raincloud view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_quality_control_rank_interval_plot` | 排名 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_quality_control_residual_annotation_map` | Quality control - Residual annotation map | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_quality_control_slope_change_view` | Quality control - Slope change view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_quality_control_small_multiple_grid` | 小多图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_quality_control_stratified_dotplot` | Quality control - Stratified dot plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_quality_control_threshold_band` | Quality control - Threshold band | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_quality_control_uncertainty_ribbon` | Quality control - Uncertainty ribbon | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_quality_control_violin_summary` | 小提琴图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_questionnaire_item_quality_annotated_reference_view` | Questionnaire item quality - Annotated reference view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_questionnaire_item_quality_boxen_interval` | Questionnaire item quality - Boxen interval plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_questionnaire_item_quality_comparative_lollipop` | Questionnaire item quality - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_questionnaire_item_quality_density_ridge` | 密度图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_questionnaire_item_quality_diagnostic_panel` | Questionnaire item quality - Diagnostic panel | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_questionnaire_item_quality_ecdf_step_view` | 经验分布图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_questionnaire_item_quality_flow_transition_map` | Questionnaire item quality - Flow transition map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_questionnaire_item_quality_forest_interval_plot` | 随机森林 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_questionnaire_item_quality_heatmap_matrix` | 热力矩阵 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_questionnaire_item_quality_histogram_facets` | 直方图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_questionnaire_item_quality_map_choropleth_layer` | 分级着色地图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_questionnaire_item_quality_mosaic_tile_view` | Questionnaire item quality - Mosaic tile view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_questionnaire_item_quality_network_node_link` | 关系网络 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_questionnaire_item_quality_qq_reference_plot` | Questionnaire item quality - Q-Q reference plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_questionnaire_item_quality_quantile_band` | 分位数 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_questionnaire_item_quality_raincloud_view` | Questionnaire item quality - Raincloud view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_questionnaire_item_quality_rank_interval_plot` | 排名 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_questionnaire_item_quality_residual_annotation_map` | Questionnaire item quality - Residual annotation map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_questionnaire_item_quality_slope_change_view` | Questionnaire item quality - Slope change view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_questionnaire_item_quality_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_questionnaire_item_quality_stratified_dotplot` | Questionnaire item quality - Stratified dot plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_questionnaire_item_quality_threshold_band` | Questionnaire item quality - Threshold band | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_questionnaire_item_quality_uncertainty_ribbon` | Questionnaire item quality - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_questionnaire_item_quality_violin_summary` | 小提琴图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_randomization_check_annotated_reference_view` | Randomization check - Annotated reference view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_randomization_check_boxen_interval` | Randomization check - Boxen interval plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_randomization_check_comparative_lollipop` | Randomization check - Comparative lollipop plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_randomization_check_density_ridge` | 密度图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_randomization_check_diagnostic_panel` | Randomization check - Diagnostic panel | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_randomization_check_ecdf_step_view` | 经验分布图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_randomization_check_flow_transition_map` | Randomization check - Flow transition map | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_randomization_check_forest_interval_plot` | 随机森林 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_randomization_check_heatmap_matrix` | 热力矩阵 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_randomization_check_histogram_facets` | 直方图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_randomization_check_map_choropleth_layer` | 分级着色地图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_randomization_check_mosaic_tile_view` | Randomization check - Mosaic tile view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_randomization_check_network_node_link` | 关系网络 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_randomization_check_qq_reference_plot` | Randomization check - Q-Q reference plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_randomization_check_quantile_band` | 分位数 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_randomization_check_raincloud_view` | Randomization check - Raincloud view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_randomization_check_rank_interval_plot` | 排名 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_randomization_check_residual_annotation_map` | Randomization check - Residual annotation map | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_randomization_check_slope_change_view` | Randomization check - Slope change view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_randomization_check_small_multiple_grid` | 小多图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_randomization_check_stratified_dotplot` | Randomization check - Stratified dot plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_randomization_check_threshold_band` | Randomization check - Threshold band | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_randomization_check_uncertainty_ribbon` | Randomization check - Uncertainty ribbon | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_randomization_check_violin_summary` | 小提琴图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regional_inequality_annotated_reference_view` | Regional inequality - Annotated reference view | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regional_inequality_boxen_interval` | Regional inequality - Boxen interval plot | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regional_inequality_comparative_lollipop` | Regional inequality - Comparative lollipop plot | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regional_inequality_density_ridge` | 密度图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regional_inequality_diagnostic_panel` | Regional inequality - Diagnostic panel | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regional_inequality_ecdf_step_view` | 经验分布图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regional_inequality_flow_transition_map` | Regional inequality - Flow transition map | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regional_inequality_forest_interval_plot` | 随机森林 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regional_inequality_heatmap_matrix` | 热力矩阵 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regional_inequality_histogram_facets` | 直方图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regional_inequality_map_choropleth_layer` | 分级着色地图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regional_inequality_mosaic_tile_view` | Regional inequality - Mosaic tile view | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regional_inequality_network_node_link` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regional_inequality_qq_reference_plot` | Regional inequality - Q-Q reference plot | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regional_inequality_quantile_band` | 分位数 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regional_inequality_raincloud_view` | Regional inequality - Raincloud view | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regional_inequality_rank_interval_plot` | 排名 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regional_inequality_residual_annotation_map` | Regional inequality - Residual annotation map | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regional_inequality_slope_change_view` | Regional inequality - Slope change view | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regional_inequality_small_multiple_grid` | 小多图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regional_inequality_stratified_dotplot` | Regional inequality - Stratified dot plot | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regional_inequality_threshold_band` | Regional inequality - Threshold band | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regional_inequality_uncertainty_ribbon` | Regional inequality - Uncertainty ribbon | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regional_inequality_violin_summary` | 小提琴图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regularization_path_annotated_reference_view` | Regularization path - Annotated reference view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regularization_path_boxen_interval` | Regularization path - Boxen interval plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regularization_path_comparative_lollipop` | Regularization path - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regularization_path_density_ridge` | 密度图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regularization_path_diagnostic_panel` | Regularization path - Diagnostic panel | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regularization_path_ecdf_step_view` | 经验分布图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regularization_path_flow_transition_map` | Regularization path - Flow transition map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regularization_path_forest_interval_plot` | 随机森林 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regularization_path_heatmap_matrix` | 热力矩阵 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regularization_path_histogram_facets` | 直方图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regularization_path_map_choropleth_layer` | 分级着色地图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regularization_path_mosaic_tile_view` | Regularization path - Mosaic tile view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regularization_path_network_node_link` | 关系网络 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regularization_path_qq_reference_plot` | Regularization path - Q-Q reference plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regularization_path_quantile_band` | 分位数 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regularization_path_raincloud_view` | Regularization path - Raincloud view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regularization_path_rank_interval_plot` | 排名 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regularization_path_residual_annotation_map` | Regularization path - Residual annotation map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regularization_path_slope_change_view` | Regularization path - Slope change view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regularization_path_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regularization_path_stratified_dotplot` | Regularization path - Stratified dot plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regularization_path_threshold_band` | Regularization path - Threshold band | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regularization_path_uncertainty_ribbon` | Regularization path - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_regularization_path_violin_summary` | 小提琴图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_relationship_strength_annotated_reference_view` | Relationship strength - Annotated reference view | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_relationship_strength_boxen_interval` | Relationship strength - Boxen interval plot | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_relationship_strength_comparative_lollipop` | Relationship strength - Comparative lollipop plot | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_relationship_strength_density_ridge` | 密度图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_relationship_strength_diagnostic_panel` | Relationship strength - Diagnostic panel | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_relationship_strength_ecdf_step_view` | 经验分布图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_relationship_strength_flow_transition_map` | Relationship strength - Flow transition map | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_relationship_strength_forest_interval_plot` | 随机森林 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_relationship_strength_heatmap_matrix` | 热力矩阵 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_relationship_strength_histogram_facets` | 直方图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_relationship_strength_map_choropleth_layer` | 分级着色地图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_relationship_strength_mosaic_tile_view` | Relationship strength - Mosaic tile view | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_relationship_strength_network_node_link` | 关系网络 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_relationship_strength_qq_reference_plot` | Relationship strength - Q-Q reference plot | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_relationship_strength_quantile_band` | 分位数 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_relationship_strength_raincloud_view` | Relationship strength - Raincloud view | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_relationship_strength_rank_interval_plot` | 排名 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_relationship_strength_residual_annotation_map` | Relationship strength - Residual annotation map | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_relationship_strength_slope_change_view` | Relationship strength - Slope change view | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_relationship_strength_small_multiple_grid` | 小多图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_relationship_strength_stratified_dotplot` | Relationship strength - Stratified dot plot | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_relationship_strength_threshold_band` | Relationship strength - Threshold band | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_relationship_strength_uncertainty_ribbon` | Relationship strength - Uncertainty ribbon | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_relationship_strength_violin_summary` | 小提琴图 | 图表 | 字段对 | 规划条目 | statistical_visual_catalog |
| `visual_stat_reliability_scale_annotated_reference_view` | Reliability scale - Annotated reference view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_reliability_scale_boxen_interval` | Reliability scale - Boxen interval plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_reliability_scale_comparative_lollipop` | Reliability scale - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_reliability_scale_density_ridge` | 密度图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_reliability_scale_diagnostic_panel` | Reliability scale - Diagnostic panel | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_reliability_scale_ecdf_step_view` | 经验分布图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_reliability_scale_flow_transition_map` | Reliability scale - Flow transition map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_reliability_scale_forest_interval_plot` | 随机森林 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_reliability_scale_heatmap_matrix` | 热力矩阵 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_reliability_scale_histogram_facets` | 直方图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_reliability_scale_map_choropleth_layer` | 分级着色地图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_reliability_scale_mosaic_tile_view` | Reliability scale - Mosaic tile view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_reliability_scale_network_node_link` | 关系网络 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_reliability_scale_qq_reference_plot` | Reliability scale - Q-Q reference plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_reliability_scale_quantile_band` | 分位数 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_reliability_scale_raincloud_view` | Reliability scale - Raincloud view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_reliability_scale_rank_interval_plot` | 排名 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_reliability_scale_residual_annotation_map` | Reliability scale - Residual annotation map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_reliability_scale_slope_change_view` | Reliability scale - Slope change view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_reliability_scale_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_reliability_scale_stratified_dotplot` | Reliability scale - Stratified dot plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_reliability_scale_threshold_band` | Reliability scale - Threshold band | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_reliability_scale_uncertainty_ribbon` | Reliability scale - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_reliability_scale_violin_summary` | 小提琴图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_residual_pattern_annotated_reference_view` | Residual pattern - Annotated reference view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_residual_pattern_boxen_interval` | Residual pattern - Boxen interval plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_residual_pattern_comparative_lollipop` | Residual pattern - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_residual_pattern_density_ridge` | 密度图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_residual_pattern_diagnostic_panel` | Residual pattern - Diagnostic panel | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_residual_pattern_ecdf_step_view` | 经验分布图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_residual_pattern_flow_transition_map` | Residual pattern - Flow transition map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_residual_pattern_forest_interval_plot` | 随机森林 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_residual_pattern_heatmap_matrix` | 热力矩阵 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_residual_pattern_histogram_facets` | 直方图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_residual_pattern_map_choropleth_layer` | 分级着色地图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_residual_pattern_mosaic_tile_view` | Residual pattern - Mosaic tile view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_residual_pattern_network_node_link` | 关系网络 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_residual_pattern_qq_reference_plot` | Residual pattern - Q-Q reference plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_residual_pattern_quantile_band` | 分位数 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_residual_pattern_raincloud_view` | Residual pattern - Raincloud view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_residual_pattern_rank_interval_plot` | 排名 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_residual_pattern_residual_annotation_map` | Residual pattern - Residual annotation map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_residual_pattern_slope_change_view` | Residual pattern - Slope change view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_residual_pattern_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_residual_pattern_stratified_dotplot` | Residual pattern - Stratified dot plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_residual_pattern_threshold_band` | Residual pattern - Threshold band | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_residual_pattern_uncertainty_ribbon` | Residual pattern - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_residual_pattern_violin_summary` | 小提琴图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_robust_summary_annotated_reference_view` | 稳健 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_robust_summary_boxen_interval` | 稳健 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_robust_summary_comparative_lollipop` | 稳健 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_robust_summary_density_ridge` | 稳健 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_robust_summary_diagnostic_panel` | 稳健 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_robust_summary_ecdf_step_view` | 稳健 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_robust_summary_flow_transition_map` | 稳健 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_robust_summary_forest_interval_plot` | 稳健 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_robust_summary_heatmap_matrix` | 稳健 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_robust_summary_histogram_facets` | 稳健 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_robust_summary_map_choropleth_layer` | 稳健 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_robust_summary_mosaic_tile_view` | 稳健 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_robust_summary_network_node_link` | 稳健 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_robust_summary_qq_reference_plot` | 稳健 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_robust_summary_quantile_band` | 稳健 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_robust_summary_raincloud_view` | 稳健 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_robust_summary_rank_interval_plot` | 稳健 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_robust_summary_residual_annotation_map` | 稳健 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_robust_summary_slope_change_view` | 稳健 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_robust_summary_small_multiple_grid` | 小多图 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_robust_summary_stratified_dotplot` | 稳健 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_robust_summary_threshold_band` | 稳健 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_robust_summary_uncertainty_ribbon` | 稳健 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_robust_summary_violin_summary` | 稳健 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_coverage_annotated_reference_view` | 覆盖情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_coverage_boxen_interval` | 覆盖情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_coverage_comparative_lollipop` | 覆盖情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_coverage_density_ridge` | 覆盖情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_coverage_diagnostic_panel` | 覆盖情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_coverage_ecdf_step_view` | 覆盖情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_coverage_flow_transition_map` | 覆盖情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_coverage_forest_interval_plot` | 覆盖情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_coverage_heatmap_matrix` | 覆盖情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_coverage_histogram_facets` | 覆盖情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_coverage_map_choropleth_layer` | 覆盖情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_coverage_mosaic_tile_view` | 覆盖情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_coverage_network_node_link` | 覆盖情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_coverage_qq_reference_plot` | 覆盖情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_coverage_quantile_band` | 覆盖情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_coverage_raincloud_view` | 覆盖情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_coverage_rank_interval_plot` | 覆盖情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_coverage_residual_annotation_map` | 覆盖情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_coverage_slope_change_view` | 覆盖情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_coverage_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_coverage_stratified_dotplot` | 覆盖情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_coverage_threshold_band` | 覆盖情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_coverage_uncertainty_ribbon` | 覆盖情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_coverage_violin_summary` | 覆盖情况 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_weight_effect_annotated_reference_view` | Sample weight effect - Annotated reference view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_weight_effect_boxen_interval` | Sample weight effect - Boxen interval plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_weight_effect_comparative_lollipop` | Sample weight effect - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_weight_effect_density_ridge` | 密度图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_weight_effect_diagnostic_panel` | Sample weight effect - Diagnostic panel | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_weight_effect_ecdf_step_view` | 经验分布图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_weight_effect_flow_transition_map` | Sample weight effect - Flow transition map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_weight_effect_forest_interval_plot` | 随机森林 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_weight_effect_heatmap_matrix` | 热力矩阵 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_weight_effect_histogram_facets` | 直方图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_weight_effect_map_choropleth_layer` | 分级着色地图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_weight_effect_mosaic_tile_view` | Sample weight effect - Mosaic tile view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_weight_effect_network_node_link` | 关系网络 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_weight_effect_qq_reference_plot` | Sample weight effect - Q-Q reference plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_weight_effect_quantile_band` | 分位数 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_weight_effect_raincloud_view` | Sample weight effect - Raincloud view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_weight_effect_rank_interval_plot` | 排名 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_weight_effect_residual_annotation_map` | Sample weight effect - Residual annotation map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_weight_effect_slope_change_view` | Sample weight effect - Slope change view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_weight_effect_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_weight_effect_stratified_dotplot` | Sample weight effect - Stratified dot plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_weight_effect_threshold_band` | Sample weight effect - Threshold band | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_weight_effect_uncertainty_ribbon` | Sample weight effect - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sample_weight_effect_violin_summary` | 小提琴图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_scale_score_profile_annotated_reference_view` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_scale_score_profile_boxen_interval` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_scale_score_profile_comparative_lollipop` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_scale_score_profile_density_ridge` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_scale_score_profile_diagnostic_panel` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_scale_score_profile_ecdf_step_view` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_scale_score_profile_flow_transition_map` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_scale_score_profile_forest_interval_plot` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_scale_score_profile_heatmap_matrix` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_scale_score_profile_histogram_facets` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_scale_score_profile_map_choropleth_layer` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_scale_score_profile_mosaic_tile_view` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_scale_score_profile_network_node_link` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_scale_score_profile_qq_reference_plot` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_scale_score_profile_quantile_band` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_scale_score_profile_raincloud_view` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_scale_score_profile_rank_interval_plot` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_scale_score_profile_residual_annotation_map` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_scale_score_profile_slope_change_view` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_scale_score_profile_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_scale_score_profile_stratified_dotplot` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_scale_score_profile_threshold_band` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_scale_score_profile_uncertainty_ribbon` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_scale_score_profile_violin_summary` | 画像 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_seasonality_pattern_annotated_reference_view` | 季节性 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_seasonality_pattern_boxen_interval` | 季节性 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_seasonality_pattern_comparative_lollipop` | 季节性 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_seasonality_pattern_density_ridge` | 季节性 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_seasonality_pattern_diagnostic_panel` | 季节性 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_seasonality_pattern_ecdf_step_view` | 季节性 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_seasonality_pattern_flow_transition_map` | 季节性 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_seasonality_pattern_forest_interval_plot` | 季节性 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_seasonality_pattern_heatmap_matrix` | 季节性 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_seasonality_pattern_histogram_facets` | 季节性 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_seasonality_pattern_map_choropleth_layer` | 季节性 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_seasonality_pattern_mosaic_tile_view` | 季节性 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_seasonality_pattern_network_node_link` | 季节性 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_seasonality_pattern_qq_reference_plot` | 季节性 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_seasonality_pattern_quantile_band` | 季节性 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_seasonality_pattern_raincloud_view` | 季节性 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_seasonality_pattern_rank_interval_plot` | 季节性 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_seasonality_pattern_residual_annotation_map` | 季节性 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_seasonality_pattern_slope_change_view` | 季节性 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_seasonality_pattern_small_multiple_grid` | 小多图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_seasonality_pattern_stratified_dotplot` | 季节性 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_seasonality_pattern_threshold_band` | 季节性 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_seasonality_pattern_uncertainty_ribbon` | 季节性 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_seasonality_pattern_violin_summary` | 季节性 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sensitivity_bounds_annotated_reference_view` | 敏感性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sensitivity_bounds_boxen_interval` | 敏感性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sensitivity_bounds_comparative_lollipop` | 敏感性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sensitivity_bounds_density_ridge` | 敏感性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sensitivity_bounds_diagnostic_panel` | 敏感性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sensitivity_bounds_ecdf_step_view` | 敏感性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sensitivity_bounds_flow_transition_map` | 敏感性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sensitivity_bounds_forest_interval_plot` | 敏感性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sensitivity_bounds_heatmap_matrix` | 敏感性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sensitivity_bounds_histogram_facets` | 敏感性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sensitivity_bounds_map_choropleth_layer` | 敏感性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sensitivity_bounds_mosaic_tile_view` | 敏感性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sensitivity_bounds_network_node_link` | 敏感性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sensitivity_bounds_qq_reference_plot` | 敏感性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sensitivity_bounds_quantile_band` | 敏感性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sensitivity_bounds_raincloud_view` | 敏感性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sensitivity_bounds_rank_interval_plot` | 敏感性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sensitivity_bounds_residual_annotation_map` | 敏感性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sensitivity_bounds_slope_change_view` | 敏感性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sensitivity_bounds_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sensitivity_bounds_stratified_dotplot` | 敏感性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sensitivity_bounds_threshold_band` | 敏感性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sensitivity_bounds_uncertainty_ribbon` | 敏感性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sensitivity_bounds_violin_summary` | 敏感性 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sentiment_distribution_annotated_reference_view` | 分布 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sentiment_distribution_boxen_interval` | 分布 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sentiment_distribution_comparative_lollipop` | 分布 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sentiment_distribution_density_ridge` | 分布 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sentiment_distribution_diagnostic_panel` | 分布 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sentiment_distribution_ecdf_step_view` | 分布 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sentiment_distribution_flow_transition_map` | 分布 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sentiment_distribution_forest_interval_plot` | 分布 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sentiment_distribution_heatmap_matrix` | 分布 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sentiment_distribution_histogram_facets` | 分布 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sentiment_distribution_map_choropleth_layer` | 分布 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sentiment_distribution_mosaic_tile_view` | 分布 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sentiment_distribution_network_node_link` | 分布 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sentiment_distribution_qq_reference_plot` | 分布 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sentiment_distribution_quantile_band` | 分布 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sentiment_distribution_raincloud_view` | 分布 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sentiment_distribution_rank_interval_plot` | 分布 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sentiment_distribution_residual_annotation_map` | 分布 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sentiment_distribution_slope_change_view` | 分布 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sentiment_distribution_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sentiment_distribution_stratified_dotplot` | 分布 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sentiment_distribution_threshold_band` | 分布 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sentiment_distribution_uncertainty_ribbon` | 分布 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sentiment_distribution_violin_summary` | 分布 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sequential_monitoring_annotated_reference_view` | Sequential monitoring - Annotated reference view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sequential_monitoring_boxen_interval` | Sequential monitoring - Boxen interval plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sequential_monitoring_comparative_lollipop` | Sequential monitoring - Comparative lollipop plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sequential_monitoring_density_ridge` | 密度图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sequential_monitoring_diagnostic_panel` | Sequential monitoring - Diagnostic panel | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sequential_monitoring_ecdf_step_view` | 经验分布图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sequential_monitoring_flow_transition_map` | Sequential monitoring - Flow transition map | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sequential_monitoring_forest_interval_plot` | 随机森林 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sequential_monitoring_heatmap_matrix` | 热力矩阵 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sequential_monitoring_histogram_facets` | 直方图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sequential_monitoring_map_choropleth_layer` | 分级着色地图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sequential_monitoring_mosaic_tile_view` | Sequential monitoring - Mosaic tile view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sequential_monitoring_network_node_link` | 关系网络 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sequential_monitoring_qq_reference_plot` | Sequential monitoring - Q-Q reference plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sequential_monitoring_quantile_band` | 分位数 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sequential_monitoring_raincloud_view` | Sequential monitoring - Raincloud view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sequential_monitoring_rank_interval_plot` | 排名 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sequential_monitoring_residual_annotation_map` | Sequential monitoring - Residual annotation map | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sequential_monitoring_slope_change_view` | Sequential monitoring - Slope change view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sequential_monitoring_small_multiple_grid` | 小多图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sequential_monitoring_stratified_dotplot` | Sequential monitoring - Stratified dot plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sequential_monitoring_threshold_band` | Sequential monitoring - Threshold band | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sequential_monitoring_uncertainty_ribbon` | Sequential monitoring - Uncertainty ribbon | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_sequential_monitoring_violin_summary` | 小提琴图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_service_queue_pattern_annotated_reference_view` | Service queue pattern - Annotated reference view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_service_queue_pattern_boxen_interval` | Service queue pattern - Boxen interval plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_service_queue_pattern_comparative_lollipop` | Service queue pattern - Comparative lollipop plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_service_queue_pattern_density_ridge` | 密度图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_service_queue_pattern_diagnostic_panel` | Service queue pattern - Diagnostic panel | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_service_queue_pattern_ecdf_step_view` | 经验分布图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_service_queue_pattern_flow_transition_map` | Service queue pattern - Flow transition map | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_service_queue_pattern_forest_interval_plot` | 随机森林 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_service_queue_pattern_heatmap_matrix` | 热力矩阵 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_service_queue_pattern_histogram_facets` | 直方图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_service_queue_pattern_map_choropleth_layer` | 分级着色地图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_service_queue_pattern_mosaic_tile_view` | Service queue pattern - Mosaic tile view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_service_queue_pattern_network_node_link` | 关系网络 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_service_queue_pattern_qq_reference_plot` | Service queue pattern - Q-Q reference plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_service_queue_pattern_quantile_band` | 分位数 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_service_queue_pattern_raincloud_view` | Service queue pattern - Raincloud view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_service_queue_pattern_rank_interval_plot` | 排名 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_service_queue_pattern_residual_annotation_map` | Service queue pattern - Residual annotation map | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_service_queue_pattern_slope_change_view` | Service queue pattern - Slope change view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_service_queue_pattern_small_multiple_grid` | 小多图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_service_queue_pattern_stratified_dotplot` | Service queue pattern - Stratified dot plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_service_queue_pattern_threshold_band` | Service queue pattern - Threshold band | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_service_queue_pattern_uncertainty_ribbon` | Service queue pattern - Uncertainty ribbon | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_service_queue_pattern_violin_summary` | 小提琴图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_accessibility_annotated_reference_view` | Spatial accessibility - Annotated reference view | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_accessibility_boxen_interval` | Spatial accessibility - Boxen interval plot | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_accessibility_comparative_lollipop` | Spatial accessibility - Comparative lollipop plot | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_accessibility_density_ridge` | 密度图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_accessibility_diagnostic_panel` | Spatial accessibility - Diagnostic panel | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_accessibility_ecdf_step_view` | 经验分布图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_accessibility_flow_transition_map` | Spatial accessibility - Flow transition map | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_accessibility_forest_interval_plot` | 随机森林 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_accessibility_heatmap_matrix` | 热力矩阵 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_accessibility_histogram_facets` | 直方图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_accessibility_map_choropleth_layer` | 分级着色地图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_accessibility_mosaic_tile_view` | Spatial accessibility - Mosaic tile view | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_accessibility_network_node_link` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_accessibility_qq_reference_plot` | Spatial accessibility - Q-Q reference plot | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_accessibility_quantile_band` | 分位数 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_accessibility_raincloud_view` | Spatial accessibility - Raincloud view | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_accessibility_rank_interval_plot` | 排名 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_accessibility_residual_annotation_map` | Spatial accessibility - Residual annotation map | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_accessibility_slope_change_view` | Spatial accessibility - Slope change view | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_accessibility_small_multiple_grid` | 小多图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_accessibility_stratified_dotplot` | Spatial accessibility - Stratified dot plot | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_accessibility_threshold_band` | Spatial accessibility - Threshold band | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_accessibility_uncertainty_ribbon` | Spatial accessibility - Uncertainty ribbon | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_accessibility_violin_summary` | 小提琴图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_autocorrelation_annotated_reference_view` | Spatial autocorrelation - Annotated reference view | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_autocorrelation_boxen_interval` | Spatial autocorrelation - Boxen interval plot | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_autocorrelation_comparative_lollipop` | Spatial autocorrelation - Comparative lollipop plot | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_autocorrelation_density_ridge` | 密度图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_autocorrelation_diagnostic_panel` | Spatial autocorrelation - Diagnostic panel | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_autocorrelation_ecdf_step_view` | 经验分布图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_autocorrelation_flow_transition_map` | Spatial autocorrelation - Flow transition map | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_autocorrelation_forest_interval_plot` | 随机森林 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_autocorrelation_heatmap_matrix` | 热力矩阵 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_autocorrelation_histogram_facets` | 直方图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_autocorrelation_map_choropleth_layer` | 分级着色地图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_autocorrelation_mosaic_tile_view` | Spatial autocorrelation - Mosaic tile view | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_autocorrelation_network_node_link` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_autocorrelation_qq_reference_plot` | Spatial autocorrelation - Q-Q reference plot | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_autocorrelation_quantile_band` | 分位数 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_autocorrelation_raincloud_view` | Spatial autocorrelation - Raincloud view | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_autocorrelation_rank_interval_plot` | 排名 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_autocorrelation_residual_annotation_map` | Spatial autocorrelation - Residual annotation map | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_autocorrelation_slope_change_view` | Spatial autocorrelation - Slope change view | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_autocorrelation_small_multiple_grid` | 小多图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_autocorrelation_stratified_dotplot` | Spatial autocorrelation - Stratified dot plot | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_autocorrelation_threshold_band` | Spatial autocorrelation - Threshold band | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_autocorrelation_uncertainty_ribbon` | Spatial autocorrelation - Uncertainty ribbon | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_autocorrelation_violin_summary` | 小提琴图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_hotspot_annotated_reference_view` | Spatial hotspot - Annotated reference view | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_hotspot_boxen_interval` | Spatial hotspot - Boxen interval plot | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_hotspot_comparative_lollipop` | Spatial hotspot - Comparative lollipop plot | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_hotspot_density_ridge` | 密度图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_hotspot_diagnostic_panel` | Spatial hotspot - Diagnostic panel | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_hotspot_ecdf_step_view` | 经验分布图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_hotspot_flow_transition_map` | Spatial hotspot - Flow transition map | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_hotspot_forest_interval_plot` | 随机森林 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_hotspot_heatmap_matrix` | 热力矩阵 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_hotspot_histogram_facets` | 直方图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_hotspot_map_choropleth_layer` | 分级着色地图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_hotspot_mosaic_tile_view` | Spatial hotspot - Mosaic tile view | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_hotspot_network_node_link` | 关系网络 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_hotspot_qq_reference_plot` | Spatial hotspot - Q-Q reference plot | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_hotspot_quantile_band` | 分位数 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_hotspot_raincloud_view` | Spatial hotspot - Raincloud view | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_hotspot_rank_interval_plot` | 排名 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_hotspot_residual_annotation_map` | Spatial hotspot - Residual annotation map | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_hotspot_slope_change_view` | Spatial hotspot - Slope change view | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_hotspot_small_multiple_grid` | 小多图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_hotspot_stratified_dotplot` | Spatial hotspot - Stratified dot plot | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_hotspot_threshold_band` | Spatial hotspot - Threshold band | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_hotspot_uncertainty_ribbon` | Spatial hotspot - Uncertainty ribbon | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_spatial_hotspot_violin_summary` | 小提琴图 | 图表 | 对象级 | 规划条目 | statistical_visual_catalog |
| `visual_stat_student_performance_distribution_annotated_reference_view` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_student_performance_distribution_boxen_interval` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_student_performance_distribution_comparative_lollipop` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_student_performance_distribution_density_ridge` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_student_performance_distribution_diagnostic_panel` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_student_performance_distribution_ecdf_step_view` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_student_performance_distribution_flow_transition_map` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_student_performance_distribution_forest_interval_plot` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_student_performance_distribution_heatmap_matrix` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_student_performance_distribution_histogram_facets` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_student_performance_distribution_map_choropleth_layer` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_student_performance_distribution_mosaic_tile_view` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_student_performance_distribution_network_node_link` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_student_performance_distribution_qq_reference_plot` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_student_performance_distribution_quantile_band` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_student_performance_distribution_raincloud_view` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_student_performance_distribution_rank_interval_plot` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_student_performance_distribution_residual_annotation_map` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_student_performance_distribution_slope_change_view` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_student_performance_distribution_small_multiple_grid` | 小多图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_student_performance_distribution_stratified_dotplot` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_student_performance_distribution_threshold_band` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_student_performance_distribution_uncertainty_ribbon` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_student_performance_distribution_violin_summary` | 分布 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_subgroup_variability_annotated_reference_view` | Subgroup variability - Annotated reference view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_subgroup_variability_boxen_interval` | Subgroup variability - Boxen interval plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_subgroup_variability_comparative_lollipop` | Subgroup variability - Comparative lollipop plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_subgroup_variability_density_ridge` | 密度图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_subgroup_variability_diagnostic_panel` | Subgroup variability - Diagnostic panel | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_subgroup_variability_ecdf_step_view` | 经验分布图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_subgroup_variability_flow_transition_map` | Subgroup variability - Flow transition map | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_subgroup_variability_forest_interval_plot` | 随机森林 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_subgroup_variability_heatmap_matrix` | 热力矩阵 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_subgroup_variability_histogram_facets` | 直方图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_subgroup_variability_map_choropleth_layer` | 分级着色地图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_subgroup_variability_mosaic_tile_view` | Subgroup variability - Mosaic tile view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_subgroup_variability_network_node_link` | 关系网络 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_subgroup_variability_qq_reference_plot` | Subgroup variability - Q-Q reference plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_subgroup_variability_quantile_band` | 分位数 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_subgroup_variability_raincloud_view` | Subgroup variability - Raincloud view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_subgroup_variability_rank_interval_plot` | 排名 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_subgroup_variability_residual_annotation_map` | Subgroup variability - Residual annotation map | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_subgroup_variability_slope_change_view` | Subgroup variability - Slope change view | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_subgroup_variability_small_multiple_grid` | 小多图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_subgroup_variability_stratified_dotplot` | Subgroup variability - Stratified dot plot | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_subgroup_variability_threshold_band` | Subgroup variability - Threshold band | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_subgroup_variability_uncertainty_ribbon` | Subgroup variability - Uncertainty ribbon | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_subgroup_variability_violin_summary` | 小提琴图 | 图表 | 分组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_response_pattern_annotated_reference_view` | Survey response pattern - Annotated reference view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_response_pattern_boxen_interval` | Survey response pattern - Boxen interval plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_response_pattern_comparative_lollipop` | Survey response pattern - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_response_pattern_density_ridge` | 密度图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_response_pattern_diagnostic_panel` | Survey response pattern - Diagnostic panel | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_response_pattern_ecdf_step_view` | 经验分布图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_response_pattern_flow_transition_map` | Survey response pattern - Flow transition map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_response_pattern_forest_interval_plot` | 随机森林 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_response_pattern_heatmap_matrix` | 热力矩阵 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_response_pattern_histogram_facets` | 直方图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_response_pattern_map_choropleth_layer` | 分级着色地图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_response_pattern_mosaic_tile_view` | Survey response pattern - Mosaic tile view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_response_pattern_network_node_link` | 关系网络 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_response_pattern_qq_reference_plot` | Survey response pattern - Q-Q reference plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_response_pattern_quantile_band` | 分位数 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_response_pattern_raincloud_view` | Survey response pattern - Raincloud view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_response_pattern_rank_interval_plot` | 排名 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_response_pattern_residual_annotation_map` | Survey response pattern - Residual annotation map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_response_pattern_slope_change_view` | Survey response pattern - Slope change view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_response_pattern_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_response_pattern_stratified_dotplot` | Survey response pattern - Stratified dot plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_response_pattern_threshold_band` | Survey response pattern - Threshold band | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_response_pattern_uncertainty_ribbon` | Survey response pattern - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_response_pattern_violin_summary` | 小提琴图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_weighting_annotated_reference_view` | Survey weighting - Annotated reference view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_weighting_boxen_interval` | Survey weighting - Boxen interval plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_weighting_comparative_lollipop` | Survey weighting - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_weighting_density_ridge` | 密度图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_weighting_diagnostic_panel` | Survey weighting - Diagnostic panel | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_weighting_ecdf_step_view` | 经验分布图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_weighting_flow_transition_map` | Survey weighting - Flow transition map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_weighting_forest_interval_plot` | 随机森林 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_weighting_heatmap_matrix` | 热力矩阵 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_weighting_histogram_facets` | 直方图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_weighting_map_choropleth_layer` | 分级着色地图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_weighting_mosaic_tile_view` | Survey weighting - Mosaic tile view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_weighting_network_node_link` | 关系网络 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_weighting_qq_reference_plot` | Survey weighting - Q-Q reference plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_weighting_quantile_band` | 分位数 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_weighting_raincloud_view` | Survey weighting - Raincloud view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_weighting_rank_interval_plot` | 排名 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_weighting_residual_annotation_map` | Survey weighting - Residual annotation map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_weighting_slope_change_view` | Survey weighting - Slope change view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_weighting_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_weighting_stratified_dotplot` | Survey weighting - Stratified dot plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_weighting_threshold_band` | Survey weighting - Threshold band | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_weighting_uncertainty_ribbon` | Survey weighting - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survey_weighting_violin_summary` | 小提琴图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_curve_annotated_reference_view` | Survival curve - Annotated reference view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_curve_boxen_interval` | Survival curve - Boxen interval plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_curve_comparative_lollipop` | Survival curve - Comparative lollipop plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_curve_density_ridge` | 密度图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_curve_diagnostic_panel` | Survival curve - Diagnostic panel | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_curve_ecdf_step_view` | 经验分布图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_curve_flow_transition_map` | Survival curve - Flow transition map | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_curve_forest_interval_plot` | 随机森林 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_curve_heatmap_matrix` | 热力矩阵 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_curve_histogram_facets` | 直方图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_curve_map_choropleth_layer` | 分级着色地图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_curve_mosaic_tile_view` | Survival curve - Mosaic tile view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_curve_network_node_link` | 关系网络 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_curve_qq_reference_plot` | Survival curve - Q-Q reference plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_curve_quantile_band` | 分位数 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_curve_raincloud_view` | Survival curve - Raincloud view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_curve_rank_interval_plot` | 排名 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_curve_residual_annotation_map` | Survival curve - Residual annotation map | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_curve_slope_change_view` | Survival curve - Slope change view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_curve_small_multiple_grid` | 小多图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_curve_stratified_dotplot` | Survival curve - Stratified dot plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_curve_threshold_band` | Survival curve - Threshold band | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_curve_uncertainty_ribbon` | Survival curve - Uncertainty ribbon | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_curve_violin_summary` | 小提琴图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_strata_annotated_reference_view` | Survival strata - Annotated reference view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_strata_boxen_interval` | Survival strata - Boxen interval plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_strata_comparative_lollipop` | Survival strata - Comparative lollipop plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_strata_density_ridge` | 密度图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_strata_diagnostic_panel` | Survival strata - Diagnostic panel | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_strata_ecdf_step_view` | 经验分布图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_strata_flow_transition_map` | Survival strata - Flow transition map | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_strata_forest_interval_plot` | 随机森林 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_strata_heatmap_matrix` | 热力矩阵 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_strata_histogram_facets` | 直方图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_strata_map_choropleth_layer` | 分级着色地图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_strata_mosaic_tile_view` | Survival strata - Mosaic tile view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_strata_network_node_link` | 关系网络 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_strata_qq_reference_plot` | Survival strata - Q-Q reference plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_strata_quantile_band` | 分位数 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_strata_raincloud_view` | Survival strata - Raincloud view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_strata_rank_interval_plot` | 排名 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_strata_residual_annotation_map` | Survival strata - Residual annotation map | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_strata_slope_change_view` | Survival strata - Slope change view | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_strata_small_multiple_grid` | 小多图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_strata_stratified_dotplot` | Survival strata - Stratified dot plot | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_strata_threshold_band` | Survival strata - Threshold band | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_strata_uncertainty_ribbon` | Survival strata - Uncertainty ribbon | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_survival_strata_violin_summary` | 小提琴图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_tail_outlier_annotated_reference_view` | Tail and outlier structure - Annotated reference view | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_tail_outlier_boxen_interval` | Tail and outlier structure - Boxen interval plot | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_tail_outlier_comparative_lollipop` | Tail and outlier structure - Comparative lollipop plot | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_tail_outlier_density_ridge` | 密度图 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_tail_outlier_diagnostic_panel` | Tail and outlier structure - Diagnostic panel | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_tail_outlier_ecdf_step_view` | 经验分布图 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_tail_outlier_flow_transition_map` | Tail and outlier structure - Flow transition map | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_tail_outlier_forest_interval_plot` | 随机森林 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_tail_outlier_heatmap_matrix` | 热力矩阵 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_tail_outlier_histogram_facets` | 直方图 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_tail_outlier_map_choropleth_layer` | 分级着色地图 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_tail_outlier_mosaic_tile_view` | Tail and outlier structure - Mosaic tile view | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_tail_outlier_network_node_link` | 关系网络 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_tail_outlier_qq_reference_plot` | Tail and outlier structure - Q-Q reference plot | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_tail_outlier_quantile_band` | 分位数 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_tail_outlier_raincloud_view` | Tail and outlier structure - Raincloud view | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_tail_outlier_rank_interval_plot` | 排名 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_tail_outlier_residual_annotation_map` | Tail and outlier structure - Residual annotation map | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_tail_outlier_slope_change_view` | Tail and outlier structure - Slope change view | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_tail_outlier_small_multiple_grid` | 小多图 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_tail_outlier_stratified_dotplot` | Tail and outlier structure - Stratified dot plot | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_tail_outlier_threshold_band` | Tail and outlier structure - Threshold band | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_tail_outlier_uncertainty_ribbon` | Tail and outlier structure - Uncertainty ribbon | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_tail_outlier_violin_summary` | 小提琴图 | 图表 | 单字段 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_frequency_annotated_reference_view` | Text frequency - Annotated reference view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_frequency_boxen_interval` | Text frequency - Boxen interval plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_frequency_comparative_lollipop` | Text frequency - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_frequency_density_ridge` | 密度图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_frequency_diagnostic_panel` | Text frequency - Diagnostic panel | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_frequency_ecdf_step_view` | 经验分布图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_frequency_flow_transition_map` | Text frequency - Flow transition map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_frequency_forest_interval_plot` | 随机森林 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_frequency_heatmap_matrix` | 热力矩阵 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_frequency_histogram_facets` | 直方图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_frequency_map_choropleth_layer` | 分级着色地图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_frequency_mosaic_tile_view` | Text frequency - Mosaic tile view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_frequency_network_node_link` | 关系网络 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_frequency_qq_reference_plot` | Text frequency - Q-Q reference plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_frequency_quantile_band` | 分位数 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_frequency_raincloud_view` | Text frequency - Raincloud view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_frequency_rank_interval_plot` | 排名 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_frequency_residual_annotation_map` | Text frequency - Residual annotation map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_frequency_slope_change_view` | Text frequency - Slope change view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_frequency_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_frequency_stratified_dotplot` | Text frequency - Stratified dot plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_frequency_threshold_band` | Text frequency - Threshold band | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_frequency_uncertainty_ribbon` | Text frequency - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_frequency_violin_summary` | 小提琴图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_topic_annotated_reference_view` | Text topic structure - Annotated reference view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_topic_boxen_interval` | Text topic structure - Boxen interval plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_topic_comparative_lollipop` | Text topic structure - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_topic_density_ridge` | 密度图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_topic_diagnostic_panel` | Text topic structure - Diagnostic panel | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_topic_ecdf_step_view` | 经验分布图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_topic_flow_transition_map` | Text topic structure - Flow transition map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_topic_forest_interval_plot` | 随机森林 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_topic_heatmap_matrix` | 热力矩阵 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_topic_histogram_facets` | 直方图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_topic_map_choropleth_layer` | 分级着色地图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_topic_mosaic_tile_view` | Text topic structure - Mosaic tile view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_topic_network_node_link` | 关系网络 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_topic_qq_reference_plot` | Text topic structure - Q-Q reference plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_topic_quantile_band` | 分位数 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_topic_raincloud_view` | Text topic structure - Raincloud view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_topic_rank_interval_plot` | 排名 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_topic_residual_annotation_map` | Text topic structure - Residual annotation map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_topic_slope_change_view` | Text topic structure - Slope change view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_topic_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_topic_stratified_dotplot` | Text topic structure - Stratified dot plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_topic_threshold_band` | Text topic structure - Threshold band | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_topic_uncertainty_ribbon` | Text topic structure - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_text_topic_violin_summary` | 小提琴图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_time_trend_annotated_reference_view` | 趋势 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_time_trend_boxen_interval` | 趋势 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_time_trend_comparative_lollipop` | 趋势 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_time_trend_density_ridge` | 趋势 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_time_trend_diagnostic_panel` | 趋势 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_time_trend_ecdf_step_view` | 趋势 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_time_trend_flow_transition_map` | 趋势 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_time_trend_forest_interval_plot` | 趋势 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_time_trend_heatmap_matrix` | 趋势 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_time_trend_histogram_facets` | 趋势 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_time_trend_map_choropleth_layer` | 趋势 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_time_trend_mosaic_tile_view` | 趋势 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_time_trend_network_node_link` | 趋势 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_time_trend_qq_reference_plot` | 趋势 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_time_trend_quantile_band` | 趋势 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_time_trend_raincloud_view` | 趋势 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_time_trend_rank_interval_plot` | 趋势 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_time_trend_residual_annotation_map` | 趋势 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_time_trend_slope_change_view` | 趋势 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_time_trend_small_multiple_grid` | 小多图 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_time_trend_stratified_dotplot` | 趋势 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_time_trend_threshold_band` | 趋势 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_time_trend_uncertainty_ribbon` | 趋势 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_time_trend_violin_summary` | 趋势 | 图表 | 时间窗口 | 规划条目 | statistical_visual_catalog |
| `visual_stat_treatment_effect_annotated_reference_view` | Treatment effect heterogeneity - Annotated reference view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_treatment_effect_boxen_interval` | Treatment effect heterogeneity - Boxen interval plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_treatment_effect_comparative_lollipop` | Treatment effect heterogeneity - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_treatment_effect_density_ridge` | 密度图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_treatment_effect_diagnostic_panel` | Treatment effect heterogeneity - Diagnostic panel | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_treatment_effect_ecdf_step_view` | 经验分布图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_treatment_effect_flow_transition_map` | Treatment effect heterogeneity - Flow transition map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_treatment_effect_forest_interval_plot` | 随机森林 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_treatment_effect_heatmap_matrix` | 热力矩阵 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_treatment_effect_histogram_facets` | 直方图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_treatment_effect_map_choropleth_layer` | 分级着色地图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_treatment_effect_mosaic_tile_view` | Treatment effect heterogeneity - Mosaic tile view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_treatment_effect_network_node_link` | 关系网络 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_treatment_effect_qq_reference_plot` | Treatment effect heterogeneity - Q-Q reference plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_treatment_effect_quantile_band` | 分位数 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_treatment_effect_raincloud_view` | Treatment effect heterogeneity - Raincloud view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_treatment_effect_rank_interval_plot` | 排名 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_treatment_effect_residual_annotation_map` | Treatment effect heterogeneity - Residual annotation map | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_treatment_effect_slope_change_view` | Treatment effect heterogeneity - Slope change view | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_treatment_effect_small_multiple_grid` | 小多图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_treatment_effect_stratified_dotplot` | Treatment effect heterogeneity - Stratified dot plot | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_treatment_effect_threshold_band` | Treatment effect heterogeneity - Threshold band | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_treatment_effect_uncertainty_ribbon` | Treatment effect heterogeneity - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_stat_treatment_effect_violin_summary` | 小提琴图 | 图表 | 字段组 | 规划条目 | statistical_visual_catalog |
| `visual_streamgraph` | 流形图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_strip` | 条带散点图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_sunburst` | 旭日图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_treemap` | 树图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_violin` | 小提琴图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `visual_waterfall` | 瀑布图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |

### 回归建模（6 张；可运行 0 张）

| 卡片 ID | 方法概念 | 输出形态 | 字段角色 | 状态 | 来源 |
| --- | --- | --- | --- | --- | --- |
| `regression_linear` | 线性 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `regression_logistic` | 逻辑 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `regression_poisson` | 泊松 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `regression_quantile` | 分位数 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `regression_regularized` | 正则化 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `regression_robust` | 稳健 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |

### 因果探查（47 张；可运行 0 张）

| 卡片 ID | 方法概念 | 输出形态 | 字段角色 | 状态 | 来源 |
| --- | --- | --- | --- | --- | --- |
| `causal_did` | 双重差分 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `causal_forest_data` | Causal Forest | 结构化数据 | group、outcome、features | 目录条目 | statistical_catalog |
| `causal_forest_table` | Causal Forest | 表格 | group、outcome、features | 目录条目 | statistical_catalog |
| `causal_forest_text` | Causal Forest | 文字解读 | group、outcome、features | 目录条目 | statistical_catalog |
| `causal_matching` | 匹配 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `causal_sensitivity` | 敏感性 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `causal_synthetic_control` | 合成控制 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `causal_uplift` | 增量 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `dag_assumption_review_data` | DAG Assumption Review | 结构化数据 | target、features | 目录条目 | statistical_catalog |
| `dag_assumption_review_table` | DAG Assumption Review | 表格 | target、features | 目录条目 | statistical_catalog |
| `dag_assumption_review_text` | DAG Assumption Review | 文字解读 | target、features | 目录条目 | statistical_catalog |
| `double_machine_learning_data` | Double Machine Learning | 结构化数据 | group、outcome、features | 目录条目 | statistical_catalog |
| `double_machine_learning_table` | Double Machine Learning | 表格 | group、outcome、features | 目录条目 | statistical_catalog |
| `double_machine_learning_text` | Double Machine Learning | 文字解读 | group、outcome、features | 目录条目 | statistical_catalog |
| `doubly_robust_estimation_data` | Doubly Robust Estimation | 结构化数据 | group、outcome、features | 目录条目 | statistical_catalog |
| `doubly_robust_estimation_table` | Doubly Robust Estimation | 表格 | group、outcome、features | 目录条目 | statistical_catalog |
| `doubly_robust_estimation_text` | Doubly Robust Estimation | 文字解读 | group、outcome、features | 目录条目 | statistical_catalog |
| `heterogeneous_treatment_effects_data` | Heterogeneous Treatment Effects | 结构化数据 | group、outcome、features | 目录条目 | statistical_catalog |
| `heterogeneous_treatment_effects_table` | Heterogeneous Treatment Effects | 表格 | group、outcome、features | 目录条目 | statistical_catalog |
| `heterogeneous_treatment_effects_text` | Heterogeneous Treatment Effects | 文字解读 | group、outcome、features | 目录条目 | statistical_catalog |
| `instrumental_variables_data` | Instrumental Variables | 结构化数据 | target、features | 目录条目 | statistical_catalog |
| `instrumental_variables_table` | Instrumental Variables | 表格 | target、features | 目录条目 | statistical_catalog |
| `instrumental_variables_text` | Instrumental Variables | 文字解读 | target、features | 目录条目 | statistical_catalog |
| `inverse_probability_weighting_data` | Inverse Probability Weighting | 结构化数据 | group、outcome、features | 目录条目 | statistical_catalog |
| `inverse_probability_weighting_table` | Inverse Probability Weighting | 表格 | group、outcome、features | 目录条目 | statistical_catalog |
| `inverse_probability_weighting_text` | Inverse Probability Weighting | 文字解读 | group、outcome、features | 目录条目 | statistical_catalog |
| `negative_control_exposure_data` | Negative Control Exposure | 结构化数据 | target、features | 目录条目 | statistical_catalog |
| `negative_control_exposure_table` | Negative Control Exposure | 表格 | target、features | 目录条目 | statistical_catalog |
| `negative_control_exposure_text` | Negative Control Exposure | 文字解读 | target、features | 目录条目 | statistical_catalog |
| `negative_control_outcome_data` | Negative Control Outcome | 结构化数据 | target、features | 目录条目 | statistical_catalog |
| `negative_control_outcome_table` | Negative Control Outcome | 表格 | target、features | 目录条目 | statistical_catalog |
| `negative_control_outcome_text` | Negative Control Outcome | 文字解读 | target、features | 目录条目 | statistical_catalog |
| `placebo_test_data` | Placebo Test | 结构化数据 | target、features | 目录条目 | statistical_catalog |
| `placebo_test_table` | Placebo Test | 表格 | target、features | 目录条目 | statistical_catalog |
| `placebo_test_text` | Placebo Test | 文字解读 | target、features | 目录条目 | statistical_catalog |
| `propensity_score_matching_data` | Propensity Score Matching | 结构化数据 | group、outcome、features | 目录条目 | statistical_catalog |
| `propensity_score_matching_table` | Propensity Score Matching | 表格 | group、outcome、features | 目录条目 | statistical_catalog |
| `propensity_score_matching_text` | Propensity Score Matching | 文字解读 | group、outcome、features | 目录条目 | statistical_catalog |
| `regression_discontinuity_data` | Regression Discontinuity | 结构化数据 | target、features | 目录条目 | statistical_catalog |
| `regression_discontinuity_table` | Regression Discontinuity | 表格 | target、features | 目录条目 | statistical_catalog |
| `regression_discontinuity_text` | Regression Discontinuity | 文字解读 | target、features | 目录条目 | statistical_catalog |
| `spillover_interference_audit_data` | Spillover / Interference Audit | 结构化数据 | group、outcome、features | 目录条目 | statistical_catalog |
| `spillover_interference_audit_table` | Spillover / Interference Audit | 表格 | group、outcome、features | 目录条目 | statistical_catalog |
| `spillover_interference_audit_text` | Spillover / Interference Audit | 文字解读 | group、outcome、features | 目录条目 | statistical_catalog |
| `unobserved_confounding_sensitivity_data` | Unobserved Confounding Sensitivity | 结构化数据 | target、features | 目录条目 | statistical_catalog |
| `unobserved_confounding_sensitivity_table` | Unobserved Confounding Sensitivity | 表格 | target、features | 目录条目 | statistical_catalog |
| `unobserved_confounding_sensitivity_text` | Unobserved Confounding Sensitivity | 文字解读 | target、features | 目录条目 | statistical_catalog |

### 均值检验（39 张；可运行 30 张）

| 卡片 ID | 方法概念 | 输出形态 | 字段角色 | 状态 | 来源 |
| --- | --- | --- | --- | --- | --- |
| `ancova_data` | ANCOVA | 结构化数据 | 数值字段、分类字段、数值字段 | 可运行 | statistical_catalog |
| `ancova_table` | ANCOVA | 表格 | 数值字段、分类字段、数值字段 | 可运行 | statistical_catalog |
| `ancova_text` | ANCOVA | 文字解读 | 数值字段、分类字段、数值字段 | 可运行 | statistical_catalog |
| `anova_data` | One-way ANOVA | 结构化数据 | 数值字段、分类字段 | 可运行 | statistical_catalog |
| `anova_table` | One-way ANOVA | 表格 | 数值字段、分类字段 | 可运行 | statistical_catalog |
| `anova_text` | One-way ANOVA | 文字解读 | 数值字段、分类字段 | 可运行 | statistical_catalog |
| `equivalence_test_tost_data` | TOST Equivalence Test | 结构化数据 | 数值字段、binary group | 目录条目 | statistical_catalog |
| `equivalence_test_tost_table` | TOST Equivalence Test | 表格 | 数值字段、binary group | 目录条目 | statistical_catalog |
| `equivalence_test_tost_text` | TOST Equivalence Test | 文字解读 | 数值字段、binary group | 目录条目 | statistical_catalog |
| `hotelling_t2_data` | Hotelling T^2 | 结构化数据 | multi numeric、binary group | 目录条目 | statistical_catalog |
| `hotelling_t2_table` | Hotelling T^2 | 表格 | multi numeric、binary group | 目录条目 | statistical_catalog |
| `hotelling_t2_text` | Hotelling T^2 | 文字解读 | multi numeric、binary group | 目录条目 | statistical_catalog |
| `manova_data` | MANOVA | 结构化数据 | multi numeric、分类字段 | 目录条目 | statistical_catalog |
| `manova_table` | MANOVA | 表格 | multi numeric、分类字段 | 目录条目 | statistical_catalog |
| `manova_text` | MANOVA | 文字解读 | multi numeric、分类字段 | 目录条目 | statistical_catalog |
| `one_sample_ttest_data` | One-sample T-test | 结构化数据 | 数值字段 | 可运行 | statistical_catalog |
| `one_sample_ttest_table` | One-sample T-test | 表格 | 数值字段 | 可运行 | statistical_catalog |
| `one_sample_ttest_text` | One-sample T-test | 文字解读 | 数值字段 | 可运行 | statistical_catalog |
| `paired_ttest_data` | Paired T-test | 结构化数据 | 数值字段、paired | 可运行 | statistical_catalog |
| `paired_ttest_table` | Paired T-test | 表格 | 数值字段、paired | 可运行 | statistical_catalog |
| `paired_ttest_text` | Paired T-test | 文字解读 | 数值字段、paired | 可运行 | statistical_catalog |
| `repeated_measures_anova_data` | Repeated Measures ANOVA | 结构化数据 | 数值字段、within subject factor | 可运行 | statistical_catalog |
| `repeated_measures_anova_table` | Repeated Measures ANOVA | 表格 | 数值字段、within subject factor | 可运行 | statistical_catalog |
| `repeated_measures_anova_text` | Repeated Measures ANOVA | 文字解读 | 数值字段、within subject factor | 可运行 | statistical_catalog |
| `ttest_data` | Welch Two-sample T-test | 结构化数据 | 数值字段、binary group | 可运行 | statistical_catalog |
| `ttest_table` | Welch Two-sample T-test | 表格 | 数值字段、binary group | 可运行 | statistical_catalog |
| `ttest_text` | Welch Two-sample T-test | 文字解读 | 数值字段、binary group | 可运行 | statistical_catalog |
| `tukey_hsd_data` | Tukey HSD | 结构化数据 | 数值字段、分类字段 | 可运行 | statistical_catalog |
| `tukey_hsd_table` | Tukey HSD | 表格 | 数值字段、分类字段 | 可运行 | statistical_catalog |
| `tukey_hsd_text` | Tukey HSD | 文字解读 | 数值字段、分类字段 | 可运行 | statistical_catalog |
| `two_way_anova_data` | Two-way ANOVA | 结构化数据 | 数值字段、分类字段、分类字段 | 可运行 | statistical_catalog |
| `two_way_anova_table` | Two-way ANOVA | 表格 | 数值字段、分类字段、分类字段 | 可运行 | statistical_catalog |
| `two_way_anova_text` | Two-way ANOVA | 文字解读 | 数值字段、分类字段、分类字段 | 可运行 | statistical_catalog |
| `welch_anova_data` | Welch ANOVA | 结构化数据 | 数值字段、分类字段 | 可运行 | statistical_catalog |
| `welch_anova_table` | Welch ANOVA | 表格 | 数值字段、分类字段 | 可运行 | statistical_catalog |
| `welch_anova_text` | Welch ANOVA | 文字解读 | 数值字段、分类字段 | 可运行 | statistical_catalog |
| `z_test_mean_data` | Z-test for Mean | 结构化数据 | 数值字段 | 可运行 | statistical_catalog |
| `z_test_mean_table` | Z-test for Mean | 表格 | 数值字段 | 可运行 | statistical_catalog |
| `z_test_mean_text` | Z-test for Mean | 文字解读 | 数值字段 | 可运行 | statistical_catalog |

### 多变量分析（114 张；可运行 12 张）

| 卡片 ID | 方法概念 | 输出形态 | 字段角色 | 状态 | 来源 |
| --- | --- | --- | --- | --- | --- |
| `bertopic_clustering_chart` | BERTopic Clustering | 图表 | 字段组 | 目录条目 | statistical_catalog |
| `bertopic_clustering_data` | BERTopic Clustering | 结构化数据 | 字段组 | 目录条目 | statistical_catalog |
| `bertopic_clustering_image_spec` | BERTopic Clustering | 图片规格 | 字段组 | 目录条目 | statistical_catalog |
| `bertopic_clustering_report_section` | BERTopic Clustering | 报告段落 | 字段组 | 目录条目 | statistical_catalog |
| `bertopic_clustering_table` | BERTopic Clustering | 表格 | 字段组 | 目录条目 | statistical_catalog |
| `bertopic_clustering_text` | BERTopic Clustering | 文字解读 | 字段组 | 目录条目 | statistical_catalog |
| `bipartite_network_projection_data` | Bipartite Network Projection | 结构化数据 | 对象级 | 目录条目 | statistical_catalog |
| `bipartite_network_projection_table` | Bipartite Network Projection | 表格 | 对象级 | 目录条目 | statistical_catalog |
| `bipartite_network_projection_text` | Bipartite Network Projection | 文字解读 | 对象级 | 目录条目 | statistical_catalog |
| `cluster_stability_data` | Cluster Stability Analysis | 结构化数据 | multi numeric | 目录条目 | statistical_catalog |
| `cluster_stability_table` | Cluster Stability Analysis | 表格 | multi numeric | 目录条目 | statistical_catalog |
| `cluster_stability_text` | Cluster Stability Analysis | 文字解读 | multi numeric | 目录条目 | statistical_catalog |
| `community_detection_louvain_data` | Louvain Community Detection | 结构化数据 | 对象级 | 目录条目 | statistical_catalog |
| `community_detection_louvain_table` | Louvain Community Detection | 表格 | 对象级 | 目录条目 | statistical_catalog |
| `community_detection_louvain_text` | Louvain Community Detection | 文字解读 | 对象级 | 目录条目 | statistical_catalog |
| `confirmatory_factor_analysis_data` | Confirmatory Factor Analysis | 结构化数据 | multi numeric | 目录条目 | statistical_catalog |
| `confirmatory_factor_analysis_table` | Confirmatory Factor Analysis | 表格 | multi numeric | 目录条目 | statistical_catalog |
| `confirmatory_factor_analysis_text` | Confirmatory Factor Analysis | 文字解读 | multi numeric | 目录条目 | statistical_catalog |
| `correspondence_analysis_chart` | Correspondence Analysis | 图表 | 分类字段、分类字段 | 目录条目 | statistical_catalog |
| `correspondence_analysis_data` | Correspondence Analysis | 结构化数据 | 分类字段、分类字段 | 目录条目 | statistical_catalog |
| `correspondence_analysis_image_spec` | Correspondence Analysis | 图片规格 | 分类字段、分类字段 | 目录条目 | statistical_catalog |
| `correspondence_analysis_report_section` | Correspondence Analysis | 报告段落 | 分类字段、分类字段 | 目录条目 | statistical_catalog |
| `correspondence_analysis_table` | Correspondence Analysis | 表格 | 分类字段、分类字段 | 目录条目 | statistical_catalog |
| `correspondence_analysis_text` | Correspondence Analysis | 文字解读 | 分类字段、分类字段 | 目录条目 | statistical_catalog |
| `dbscan_chart` | DBSCAN | 图表 | multi numeric | 目录条目 | statistical_catalog |
| `dbscan_data` | DBSCAN | 结构化数据 | multi numeric | 目录条目 | statistical_catalog |
| `dbscan_image_spec` | DBSCAN | 图片规格 | multi numeric | 目录条目 | statistical_catalog |
| `dbscan_report_section` | DBSCAN | 报告段落 | multi numeric | 目录条目 | statistical_catalog |
| `dbscan_table` | DBSCAN | 表格 | multi numeric | 目录条目 | statistical_catalog |
| `dbscan_text` | DBSCAN | 文字解读 | multi numeric | 目录条目 | statistical_catalog |
| `discriminant_analysis_lda_data` | Linear Discriminant Analysis | 结构化数据 | multi numeric、分类字段 | 目录条目 | statistical_catalog |
| `discriminant_analysis_lda_table` | Linear Discriminant Analysis | 表格 | multi numeric、分类字段 | 目录条目 | statistical_catalog |
| `discriminant_analysis_lda_text` | Linear Discriminant Analysis | 文字解读 | multi numeric、分类字段 | 目录条目 | statistical_catalog |
| `discriminant_analysis_qda_data` | Quadratic Discriminant Analysis | 结构化数据 | multi numeric、分类字段 | 目录条目 | statistical_catalog |
| `discriminant_analysis_qda_table` | Quadratic Discriminant Analysis | 表格 | multi numeric、分类字段 | 目录条目 | statistical_catalog |
| `discriminant_analysis_qda_text` | Quadratic Discriminant Analysis | 文字解读 | multi numeric、分类字段 | 目录条目 | statistical_catalog |
| `elbow_method_data` | Elbow Method | 结构化数据 | multi numeric | 目录条目 | statistical_catalog |
| `elbow_method_table` | Elbow Method | 表格 | multi numeric | 目录条目 | statistical_catalog |
| `elbow_method_text` | Elbow Method | 文字解读 | multi numeric | 目录条目 | statistical_catalog |
| `factor_analysis_chart` | Factor Analysis | 图表 | multi numeric | 目录条目 | statistical_catalog |
| `factor_analysis_data` | Factor Analysis | 结构化数据 | multi numeric | 目录条目 | statistical_catalog |
| `factor_analysis_image_spec` | Factor Analysis | 图片规格 | multi numeric | 目录条目 | statistical_catalog |
| `factor_analysis_report_section` | Factor Analysis | 报告段落 | multi numeric | 目录条目 | statistical_catalog |
| `factor_analysis_table` | Factor Analysis | 表格 | multi numeric | 目录条目 | statistical_catalog |
| `factor_analysis_text` | Factor Analysis | 文字解读 | multi numeric | 目录条目 | statistical_catalog |
| `gaussian_mixture_chart` | Gaussian Mixture Model | 图表 | multi numeric | 目录条目 | statistical_catalog |
| `gaussian_mixture_data` | Gaussian Mixture Model | 结构化数据 | multi numeric | 目录条目 | statistical_catalog |
| `gaussian_mixture_image_spec` | Gaussian Mixture Model | 图片规格 | multi numeric | 目录条目 | statistical_catalog |
| `gaussian_mixture_report_section` | Gaussian Mixture Model | 报告段落 | multi numeric | 目录条目 | statistical_catalog |
| `gaussian_mixture_table` | Gaussian Mixture Model | 表格 | multi numeric | 目录条目 | statistical_catalog |
| `gaussian_mixture_text` | Gaussian Mixture Model | 文字解读 | multi numeric | 目录条目 | statistical_catalog |
| `getis_ord_hotspot_data` | Getis-Ord Hotspot Analysis | 结构化数据 | 对象级、数值字段 | 目录条目 | statistical_catalog |
| `getis_ord_hotspot_table` | Getis-Ord Hotspot Analysis | 表格 | 对象级、数值字段 | 目录条目 | statistical_catalog |
| `getis_ord_hotspot_text` | Getis-Ord Hotspot Analysis | 文字解读 | 对象级、数值字段 | 目录条目 | statistical_catalog |
| `hierarchical_clustering_chart` | Hierarchical Clustering | 图表 | multi numeric | 目录条目 | statistical_catalog |
| `hierarchical_clustering_data` | Hierarchical Clustering | 结构化数据 | multi numeric | 目录条目 | statistical_catalog |
| `hierarchical_clustering_image_spec` | Hierarchical Clustering | 图片规格 | multi numeric | 目录条目 | statistical_catalog |
| `hierarchical_clustering_report_section` | Hierarchical Clustering | 报告段落 | multi numeric | 目录条目 | statistical_catalog |
| `hierarchical_clustering_table` | Hierarchical Clustering | 表格 | multi numeric | 目录条目 | statistical_catalog |
| `hierarchical_clustering_text` | Hierarchical Clustering | 文字解读 | multi numeric | 目录条目 | statistical_catalog |
| `ica_data` | Independent Component Analysis | 结构化数据 | multi numeric | 目录条目 | statistical_catalog |
| `ica_table` | Independent Component Analysis | 表格 | multi numeric | 目录条目 | statistical_catalog |
| `ica_text` | Independent Component Analysis | 文字解读 | multi numeric | 目录条目 | statistical_catalog |
| `kmeans_chart` | KMeans Clustering | 图表 | multi numeric | 可运行 | statistical_catalog |
| `kmeans_data` | KMeans Clustering | 结构化数据 | multi numeric | 可运行 | statistical_catalog |
| `kmeans_image_spec` | KMeans Clustering | 图片规格 | multi numeric | 可运行 | statistical_catalog |
| `kmeans_report_section` | KMeans Clustering | 报告段落 | multi numeric | 可运行 | statistical_catalog |
| `kmeans_table` | KMeans Clustering | 表格 | multi numeric | 可运行 | statistical_catalog |
| `kmeans_text` | KMeans Clustering | 文字解读 | multi numeric | 可运行 | statistical_catalog |
| `latent_class_analysis_data` | Latent Class Analysis | 结构化数据 | multi categorical | 目录条目 | statistical_catalog |
| `latent_class_analysis_table` | Latent Class Analysis | 表格 | multi categorical | 目录条目 | statistical_catalog |
| `latent_class_analysis_text` | Latent Class Analysis | 文字解读 | multi categorical | 目录条目 | statistical_catalog |
| `multivariate_control_chart_chart` | Multivariate Control Chart | 图表 | multi numeric | 目录条目 | statistical_catalog |
| `multivariate_control_chart_data` | Multivariate Control Chart | 结构化数据 | multi numeric | 目录条目 | statistical_catalog |
| `multivariate_control_chart_image_spec` | Multivariate Control Chart | 图片规格 | multi numeric | 目录条目 | statistical_catalog |
| `multivariate_control_chart_report_section` | Multivariate Control Chart | 报告段落 | multi numeric | 目录条目 | statistical_catalog |
| `multivariate_control_chart_table` | Multivariate Control Chart | 表格 | multi numeric | 目录条目 | statistical_catalog |
| `multivariate_control_chart_text` | Multivariate Control Chart | 文字解读 | multi numeric | 目录条目 | statistical_catalog |
| `named_entity_extraction_profile_data` | Named Entity Extraction Profile | 结构化数据 | 字段组 | 目录条目 | statistical_catalog |
| `named_entity_extraction_profile_table` | Named Entity Extraction Profile | 表格 | 字段组 | 目录条目 | statistical_catalog |
| `named_entity_extraction_profile_text` | Named Entity Extraction Profile | 文字解读 | 字段组 | 目录条目 | statistical_catalog |
| `network_betweenness_centrality_data` | Network Betweenness Centrality | 结构化数据 | 对象级 | 目录条目 | statistical_catalog |
| `network_betweenness_centrality_table` | Network Betweenness Centrality | 表格 | 对象级 | 目录条目 | statistical_catalog |
| `network_betweenness_centrality_text` | Network Betweenness Centrality | 文字解读 | 对象级 | 目录条目 | statistical_catalog |
| `network_degree_centrality_data` | Network Degree Centrality | 结构化数据 | 对象级 | 目录条目 | statistical_catalog |
| `network_degree_centrality_table` | Network Degree Centrality | 表格 | 对象级 | 目录条目 | statistical_catalog |
| `network_degree_centrality_text` | Network Degree Centrality | 文字解读 | 对象级 | 目录条目 | statistical_catalog |
| `network_pagerank_data` | Network PageRank | 结构化数据 | 对象级 | 目录条目 | statistical_catalog |
| `network_pagerank_table` | Network PageRank | 表格 | 对象级 | 目录条目 | statistical_catalog |
| `network_pagerank_text` | Network PageRank | 文字解读 | 对象级 | 目录条目 | statistical_catalog |
| `pca_chart` | Principal Component Analysis | 图表 | multi numeric | 可运行 | statistical_catalog |
| `pca_data` | Principal Component Analysis | 结构化数据 | multi numeric | 可运行 | statistical_catalog |
| `pca_image_spec` | Principal Component Analysis | 图片规格 | multi numeric | 可运行 | statistical_catalog |
| `pca_report_section` | Principal Component Analysis | 报告段落 | multi numeric | 可运行 | statistical_catalog |
| `pca_table` | Principal Component Analysis | 表格 | multi numeric | 可运行 | statistical_catalog |
| `pca_text` | Principal Component Analysis | 文字解读 | multi numeric | 可运行 | statistical_catalog |
| `silhouette_analysis_data` | Silhouette Analysis | 结构化数据 | multi numeric | 目录条目 | statistical_catalog |
| `silhouette_analysis_table` | Silhouette Analysis | 表格 | multi numeric | 目录条目 | statistical_catalog |
| `silhouette_analysis_text` | Silhouette Analysis | 文字解读 | multi numeric | 目录条目 | statistical_catalog |
| `text_token_frequency_data` | Text Token Frequency | 结构化数据 | 字段组 | 目录条目 | statistical_catalog |
| `text_token_frequency_table` | Text Token Frequency | 表格 | 字段组 | 目录条目 | statistical_catalog |
| `text_token_frequency_text` | Text Token Frequency | 文字解读 | 字段组 | 目录条目 | statistical_catalog |
| `tfidf_feature_profile_data` | TF-IDF Feature Profile | 结构化数据 | 字段组 | 目录条目 | statistical_catalog |
| `tfidf_feature_profile_table` | TF-IDF Feature Profile | 表格 | 字段组 | 目录条目 | statistical_catalog |
| `tfidf_feature_profile_text` | TF-IDF Feature Profile | 文字解读 | 字段组 | 目录条目 | statistical_catalog |
| `topic_model_lda_data` | LDA Topic Model | 结构化数据 | 字段组 | 目录条目 | statistical_catalog |
| `topic_model_lda_table` | LDA Topic Model | 表格 | 字段组 | 目录条目 | statistical_catalog |
| `topic_model_lda_text` | LDA Topic Model | 文字解读 | 字段组 | 目录条目 | statistical_catalog |
| `tsne_projection_data` | t-SNE Projection | 结构化数据 | multi numeric | 目录条目 | statistical_catalog |
| `tsne_projection_table` | t-SNE Projection | 表格 | multi numeric | 目录条目 | statistical_catalog |
| `tsne_projection_text` | t-SNE Projection | 文字解读 | multi numeric | 目录条目 | statistical_catalog |
| `umap_projection_data` | UMAP Projection | 结构化数据 | multi numeric | 目录条目 | statistical_catalog |
| `umap_projection_table` | UMAP Projection | 表格 | multi numeric | 目录条目 | statistical_catalog |
| `umap_projection_text` | UMAP Projection | 文字解读 | multi numeric | 目录条目 | statistical_catalog |

### 实验分析（78 张；可运行 3 张）

| 卡片 ID | 方法概念 | 输出形态 | 字段角色 | 状态 | 来源 |
| --- | --- | --- | --- | --- | --- |
| `ab_test_data` | A/B Test | 结构化数据 | group、numeric or binary | 可运行 | statistical_catalog |
| `ab_test_table` | A/B Test | 表格 | group、numeric or binary | 可运行 | statistical_catalog |
| `ab_test_text` | A/B Test | 文字解读 | group、numeric or binary | 可运行 | statistical_catalog |
| `attrition_analysis_data` | Attrition Analysis | 结构化数据 | group、numeric or binary | 目录条目 | statistical_catalog |
| `attrition_analysis_table` | Attrition Analysis | 表格 | group、numeric or binary | 目录条目 | statistical_catalog |
| `attrition_analysis_text` | Attrition Analysis | 文字解读 | group、numeric or binary | 目录条目 | statistical_catalog |
| `bayesian_ab_test_data` | Bayesian A/B Test | 结构化数据 | group、numeric or binary | 目录条目 | statistical_catalog |
| `bayesian_ab_test_table` | Bayesian A/B Test | 表格 | group、numeric or binary | 目录条目 | statistical_catalog |
| `bayesian_ab_test_text` | Bayesian A/B Test | 文字解读 | group、numeric or binary | 目录条目 | statistical_catalog |
| `bayesian_bandit_policy_data` | Bayesian Bandit Policy | 结构化数据 | group、numeric or binary | 目录条目 | statistical_catalog |
| `bayesian_bandit_policy_table` | Bayesian Bandit Policy | 表格 | group、numeric or binary | 目录条目 | statistical_catalog |
| `bayesian_bandit_policy_text` | Bayesian Bandit Policy | 文字解读 | group、numeric or binary | 目录条目 | statistical_catalog |
| `bucketed_ratio_metric_data` | Bucketed Ratio Metric | 结构化数据 | group、numeric or binary | 目录条目 | statistical_catalog |
| `bucketed_ratio_metric_table` | Bucketed Ratio Metric | 表格 | group、numeric or binary | 目录条目 | statistical_catalog |
| `bucketed_ratio_metric_text` | Bucketed Ratio Metric | 文字解读 | group、numeric or binary | 目录条目 | statistical_catalog |
| `carryover_effect_check_data` | Carryover Effect Check | 结构化数据 | time、group、numeric or binary | 目录条目 | statistical_catalog |
| `carryover_effect_check_table` | Carryover Effect Check | 表格 | time、group、numeric or binary | 目录条目 | statistical_catalog |
| `carryover_effect_check_text` | Carryover Effect Check | 文字解读 | time、group、numeric or binary | 目录条目 | statistical_catalog |
| `cuped_adjustment_data` | CUPED Adjustment | 结构化数据 | group、outcome、features | 目录条目 | statistical_catalog |
| `cuped_adjustment_table` | CUPED Adjustment | 表格 | group、outcome、features | 目录条目 | statistical_catalog |
| `cuped_adjustment_text` | CUPED Adjustment | 文字解读 | group、outcome、features | 目录条目 | statistical_catalog |
| `experiment_guardrail_metrics_data` | Experiment Guardrail Metrics | 结构化数据 | group、numeric or binary | 目录条目 | statistical_catalog |
| `experiment_guardrail_metrics_table` | Experiment Guardrail Metrics | 表格 | group、numeric or binary | 目录条目 | statistical_catalog |
| `experiment_guardrail_metrics_text` | Experiment Guardrail Metrics | 文字解读 | group、numeric or binary | 目录条目 | statistical_catalog |
| `factorial_experiment_data` | Factorial Experiment | 结构化数据 | group、outcome、features | 目录条目 | statistical_catalog |
| `factorial_experiment_table` | Factorial Experiment | 表格 | group、outcome、features | 目录条目 | statistical_catalog |
| `factorial_experiment_text` | Factorial Experiment | 文字解读 | group、outcome、features | 目录条目 | statistical_catalog |
| `geo_experiment_design_data` | Geo Experiment Design | 结构化数据 | 对象级、分组 | 目录条目 | statistical_catalog |
| `geo_experiment_design_table` | Geo Experiment Design | 表格 | 对象级、分组 | 目录条目 | statistical_catalog |
| `geo_experiment_design_text` | Geo Experiment Design | 文字解读 | 对象级、分组 | 目录条目 | statistical_catalog |
| `incrementality_holdout_data` | Incrementality Holdout | 结构化数据 | group、numeric or binary | 目录条目 | statistical_catalog |
| `incrementality_holdout_table` | Incrementality Holdout | 表格 | group、numeric or binary | 目录条目 | statistical_catalog |
| `incrementality_holdout_text` | Incrementality Holdout | 文字解读 | group、numeric or binary | 目录条目 | statistical_catalog |
| `metric_sensitivity_analysis_data` | Metric Sensitivity Analysis | 结构化数据 | group、numeric or binary | 目录条目 | statistical_catalog |
| `metric_sensitivity_analysis_table` | Metric Sensitivity Analysis | 表格 | group、numeric or binary | 目录条目 | statistical_catalog |
| `metric_sensitivity_analysis_text` | Metric Sensitivity Analysis | 文字解读 | group、numeric or binary | 目录条目 | statistical_catalog |
| `minimum_detectable_effect_data` | Minimum Detectable Effect | 结构化数据 | group、numeric or binary | 目录条目 | statistical_catalog |
| `minimum_detectable_effect_table` | Minimum Detectable Effect | 表格 | group、numeric or binary | 目录条目 | statistical_catalog |
| `minimum_detectable_effect_text` | Minimum Detectable Effect | 文字解读 | group、numeric or binary | 目录条目 | statistical_catalog |
| `multi_arm_bandit_data` | Multi-arm Bandit | 结构化数据 | group、numeric or binary | 目录条目 | statistical_catalog |
| `multi_arm_bandit_table` | Multi-arm Bandit | 表格 | group、numeric or binary | 目录条目 | statistical_catalog |
| `multi_arm_bandit_text` | Multi-arm Bandit | 文字解读 | group、numeric or binary | 目录条目 | statistical_catalog |
| `number_needed_to_treat_data` | Number Needed to Treat | 结构化数据 | group、binary | 目录条目 | statistical_catalog |
| `number_needed_to_treat_table` | Number Needed to Treat | 表格 | group、binary | 目录条目 | statistical_catalog |
| `number_needed_to_treat_text` | Number Needed to Treat | 文字解读 | group、binary | 目录条目 | statistical_catalog |
| `peeking_risk_audit_data` | Peeking Risk Audit | 结构化数据 | group、numeric or binary | 目录条目 | statistical_catalog |
| `peeking_risk_audit_table` | Peeking Risk Audit | 表格 | group、numeric or binary | 目录条目 | statistical_catalog |
| `peeking_risk_audit_text` | Peeking Risk Audit | 文字解读 | group、numeric or binary | 目录条目 | statistical_catalog |
| `power_curve_analysis_chart` | Power Curve Analysis | 图表 | effect size | 目录条目 | statistical_catalog |
| `power_curve_analysis_data` | Power Curve Analysis | 结构化数据 | effect size | 目录条目 | statistical_catalog |
| `power_curve_analysis_image_spec` | Power Curve Analysis | 图片规格 | effect size | 目录条目 | statistical_catalog |
| `power_curve_analysis_report_section` | Power Curve Analysis | 报告段落 | effect size | 目录条目 | statistical_catalog |
| `power_curve_analysis_table` | Power Curve Analysis | 表格 | effect size | 目录条目 | statistical_catalog |
| `power_curve_analysis_text` | Power Curve Analysis | 文字解读 | effect size | 目录条目 | statistical_catalog |
| `sample_ratio_mismatch_data` | Sample Ratio Mismatch | 结构化数据 | group、numeric or binary | 目录条目 | statistical_catalog |
| `sample_ratio_mismatch_table` | Sample Ratio Mismatch | 表格 | group、numeric or binary | 目录条目 | statistical_catalog |
| `sample_ratio_mismatch_text` | Sample Ratio Mismatch | 文字解读 | group、numeric or binary | 目录条目 | statistical_catalog |
| `sample_size_power_data` | Sample Size / Power Analysis | 结构化数据 | effect size | 目录条目 | statistical_catalog |
| `sample_size_power_table` | Sample Size / Power Analysis | 表格 | effect size | 目录条目 | statistical_catalog |
| `sample_size_power_text` | Sample Size / Power Analysis | 文字解读 | effect size | 目录条目 | statistical_catalog |
| `sequential_bayesian_monitoring_data` | Sequential Bayesian Monitoring | 结构化数据 | group、numeric or binary | 目录条目 | statistical_catalog |
| `sequential_bayesian_monitoring_table` | Sequential Bayesian Monitoring | 表格 | group、numeric or binary | 目录条目 | statistical_catalog |
| `sequential_bayesian_monitoring_text` | Sequential Bayesian Monitoring | 文字解读 | group、numeric or binary | 目录条目 | statistical_catalog |
| `sequential_test_data` | Sequential Test | 结构化数据 | group、numeric or binary | 目录条目 | statistical_catalog |
| `sequential_test_table` | Sequential Test | 表格 | group、numeric or binary | 目录条目 | statistical_catalog |
| `sequential_test_text` | Sequential Test | 文字解读 | group、numeric or binary | 目录条目 | statistical_catalog |
| `stratified_randomization_data` | Stratified Randomization | 结构化数据 | group、features | 目录条目 | statistical_catalog |
| `stratified_randomization_table` | Stratified Randomization | 表格 | group、features | 目录条目 | statistical_catalog |
| `stratified_randomization_text` | Stratified Randomization | 文字解读 | group、features | 目录条目 | statistical_catalog |
| `switchback_experiment_design_data` | Switchback Experiment Design | 结构化数据 | time、group、numeric or binary | 目录条目 | statistical_catalog |
| `switchback_experiment_design_table` | Switchback Experiment Design | 表格 | time、group、numeric or binary | 目录条目 | statistical_catalog |
| `switchback_experiment_design_text` | Switchback Experiment Design | 文字解读 | time、group、numeric or binary | 目录条目 | statistical_catalog |
| `uplift_evaluation_qini_data` | Qini Uplift Evaluation | 结构化数据 | group、outcome、features | 目录条目 | statistical_catalog |
| `uplift_evaluation_qini_table` | Qini Uplift Evaluation | 表格 | group、outcome、features | 目录条目 | statistical_catalog |
| `uplift_evaluation_qini_text` | Qini Uplift Evaluation | 文字解读 | group、outcome、features | 目录条目 | statistical_catalog |
| `uplift_modeling_data` | Uplift Modeling | 结构化数据 | group、outcome、features | 目录条目 | statistical_catalog |
| `uplift_modeling_table` | Uplift Modeling | 表格 | group、outcome、features | 目录条目 | statistical_catalog |
| `uplift_modeling_text` | Uplift Modeling | 文字解读 | group、outcome、features | 目录条目 | statistical_catalog |

### 差异比较（14 张；可运行 0 张）

| 卡片 ID | 方法概念 | 输出形态 | 字段角色 | 状态 | 来源 |
| --- | --- | --- | --- | --- | --- |
| `cohens_d_effect_size_data` | Cohen's d Effect Size | 结构化数据 | 数值字段、binary group | 目录条目 | statistical_catalog |
| `cohens_d_effect_size_table` | Cohen's d Effect Size | 表格 | 数值字段、binary group | 目录条目 | statistical_catalog |
| `cohens_d_effect_size_text` | Cohen's d Effect Size | 文字解读 | 数值字段、binary group | 目录条目 | statistical_catalog |
| `comparison_mean` | 均值 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `comparison_median` | 中位数 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `comparison_post_hoc` | 事后检验 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `comparison_proportion` | 占比 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `comparison_variance` | 方差 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `glass_delta_effect_size_data` | Glass Delta Effect Size | 结构化数据 | 数值字段、binary group | 目录条目 | statistical_catalog |
| `glass_delta_effect_size_table` | Glass Delta Effect Size | 表格 | 数值字段、binary group | 目录条目 | statistical_catalog |
| `glass_delta_effect_size_text` | Glass Delta Effect Size | 文字解读 | 数值字段、binary group | 目录条目 | statistical_catalog |
| `hedges_g_effect_size_data` | Hedges g Effect Size | 结构化数据 | 数值字段、binary group | 目录条目 | statistical_catalog |
| `hedges_g_effect_size_table` | Hedges g Effect Size | 表格 | 数值字段、binary group | 目录条目 | statistical_catalog |
| `hedges_g_effect_size_text` | Hedges g Effect Size | 文字解读 | 数值字段、binary group | 目录条目 | statistical_catalog |

### 广义线性模型（108 张；可运行 24 张）

| 卡片 ID | 方法概念 | 输出形态 | 字段角色 | 状态 | 来源 |
| --- | --- | --- | --- | --- | --- |
| `aic_bic_model_selection_data` | AIC / BIC Model Selection | 结构化数据 | target、features | 目录条目 | statistical_catalog |
| `aic_bic_model_selection_table` | AIC / BIC Model Selection | 表格 | target、features | 目录条目 | statistical_catalog |
| `aic_bic_model_selection_text` | AIC / BIC Model Selection | 文字解读 | target、features | 目录条目 | statistical_catalog |
| `beta_regression_data` | Beta Regression | 结构化数据 | proportion、multi numeric | 目录条目 | statistical_catalog |
| `beta_regression_table` | Beta Regression | 表格 | proportion、multi numeric | 目录条目 | statistical_catalog |
| `beta_regression_text` | Beta Regression | 文字解读 | proportion、multi numeric | 目录条目 | statistical_catalog |
| `cluster_robust_standard_errors_data` | Cluster-robust Standard Errors | 结构化数据 | target、features、分组 | 目录条目 | statistical_catalog |
| `cluster_robust_standard_errors_table` | Cluster-robust Standard Errors | 表格 | target、features、分组 | 目录条目 | statistical_catalog |
| `cluster_robust_standard_errors_text` | Cluster-robust Standard Errors | 文字解读 | target、features、分组 | 目录条目 | statistical_catalog |
| `cooks_distance_data` | Cook's Distance | 结构化数据 | target、features | 目录条目 | statistical_catalog |
| `cooks_distance_table` | Cook's Distance | 表格 | target、features | 目录条目 | statistical_catalog |
| `cooks_distance_text` | Cook's Distance | 文字解读 | target、features | 目录条目 | statistical_catalog |
| `cross_validated_regression_data` | Cross-validated Regression | 结构化数据 | target、features | 目录条目 | statistical_catalog |
| `cross_validated_regression_table` | Cross-validated Regression | 表格 | target、features | 目录条目 | statistical_catalog |
| `cross_validated_regression_text` | Cross-validated Regression | 文字解读 | target、features | 目录条目 | statistical_catalog |
| `elastic_net_data` | Elastic Net | 结构化数据 | 数值字段、multi numeric | 可运行 | statistical_catalog |
| `elastic_net_table` | Elastic Net | 表格 | 数值字段、multi numeric | 可运行 | statistical_catalog |
| `elastic_net_text` | Elastic Net | 文字解读 | 数值字段、multi numeric | 可运行 | statistical_catalog |
| `gamma_glm_data` | Gamma GLM | 结构化数据 | positive numeric、multi numeric | 目录条目 | statistical_catalog |
| `gamma_glm_table` | Gamma GLM | 表格 | positive numeric、multi numeric | 目录条目 | statistical_catalog |
| `gamma_glm_text` | Gamma GLM | 文字解读 | positive numeric、multi numeric | 目录条目 | statistical_catalog |
| `generalized_additive_model_data` | Generalized Additive Model | 结构化数据 | target、features | 目录条目 | statistical_catalog |
| `generalized_additive_model_table` | Generalized Additive Model | 表格 | target、features | 目录条目 | statistical_catalog |
| `generalized_additive_model_text` | Generalized Additive Model | 文字解读 | target、features | 目录条目 | statistical_catalog |
| `geographically_weighted_regression_data` | Geographically Weighted Regression | 结构化数据 | target、features、对象级 | 目录条目 | statistical_catalog |
| `geographically_weighted_regression_table` | Geographically Weighted Regression | 表格 | target、features、对象级 | 目录条目 | statistical_catalog |
| `geographically_weighted_regression_text` | Geographically Weighted Regression | 文字解读 | target、features、对象级 | 目录条目 | statistical_catalog |
| `glm_binomial_data` | Binomial GLM | 结构化数据 | binary、multi numeric | 目录条目 | statistical_catalog |
| `glm_binomial_table` | Binomial GLM | 表格 | binary、multi numeric | 目录条目 | statistical_catalog |
| `glm_binomial_text` | Binomial GLM | 文字解读 | binary、multi numeric | 目录条目 | statistical_catalog |
| `heteroskedasticity_robust_se_data` | Heteroskedasticity-robust Standard Errors | 结构化数据 | target、features | 目录条目 | statistical_catalog |
| `heteroskedasticity_robust_se_table` | Heteroskedasticity-robust Standard Errors | 表格 | target、features | 目录条目 | statistical_catalog |
| `heteroskedasticity_robust_se_text` | Heteroskedasticity-robust Standard Errors | 文字解读 | target、features | 目录条目 | statistical_catalog |
| `influence_diagnostics_data` | Influence Diagnostics | 结构化数据 | target、features | 目录条目 | statistical_catalog |
| `influence_diagnostics_table` | Influence Diagnostics | 表格 | target、features | 目录条目 | statistical_catalog |
| `influence_diagnostics_text` | Influence Diagnostics | 文字解读 | target、features | 目录条目 | statistical_catalog |
| `interaction_feature_screen_data` | Interaction Feature Screen | 结构化数据 | target、features | 目录条目 | statistical_catalog |
| `interaction_feature_screen_table` | Interaction Feature Screen | 表格 | target、features | 目录条目 | statistical_catalog |
| `interaction_feature_screen_text` | Interaction Feature Screen | 文字解读 | target、features | 目录条目 | statistical_catalog |
| `lasso_regression_data` | Lasso Regression | 结构化数据 | 数值字段、multi numeric | 可运行 | statistical_catalog |
| `lasso_regression_table` | Lasso Regression | 表格 | 数值字段、multi numeric | 可运行 | statistical_catalog |
| `lasso_regression_text` | Lasso Regression | 文字解读 | 数值字段、multi numeric | 可运行 | statistical_catalog |
| `logit_data` | Logistic Regression | 结构化数据 | binary、multi numeric | 可运行 | statistical_catalog |
| `logit_table` | Logistic Regression | 表格 | binary、multi numeric | 可运行 | statistical_catalog |
| `logit_text` | Logistic Regression | 文字解读 | binary、multi numeric | 可运行 | statistical_catalog |
| `model_specification_curve_chart` | Specification Curve Analysis | 图表 | target、features | 目录条目 | statistical_catalog |
| `model_specification_curve_data` | Specification Curve Analysis | 结构化数据 | target、features | 目录条目 | statistical_catalog |
| `model_specification_curve_image_spec` | Specification Curve Analysis | 图片规格 | target、features | 目录条目 | statistical_catalog |
| `model_specification_curve_report_section` | Specification Curve Analysis | 报告段落 | target、features | 目录条目 | statistical_catalog |
| `model_specification_curve_table` | Specification Curve Analysis | 表格 | target、features | 目录条目 | statistical_catalog |
| `model_specification_curve_text` | Specification Curve Analysis | 文字解读 | target、features | 目录条目 | statistical_catalog |
| `multinomial_logit_data` | Multinomial Logit | 结构化数据 | multi class、multi numeric | 目录条目 | statistical_catalog |
| `multinomial_logit_table` | Multinomial Logit | 表格 | multi class、multi numeric | 目录条目 | statistical_catalog |
| `multinomial_logit_text` | Multinomial Logit | 文字解读 | multi class、multi numeric | 目录条目 | statistical_catalog |
| `negative_binomial_data` | Negative Binomial Regression | 结构化数据 | count、multi numeric | 目录条目 | statistical_catalog |
| `negative_binomial_table` | Negative Binomial Regression | 表格 | count、multi numeric | 目录条目 | statistical_catalog |
| `negative_binomial_text` | Negative Binomial Regression | 文字解读 | count、multi numeric | 目录条目 | statistical_catalog |
| `ols_data` | OLS Regression | 结构化数据 | 数值字段、multi numeric | 可运行 | statistical_catalog |
| `ols_table` | OLS Regression | 表格 | 数值字段、multi numeric | 可运行 | statistical_catalog |
| `ols_text` | OLS Regression | 文字解读 | 数值字段、multi numeric | 可运行 | statistical_catalog |
| `ordinal_logit_data` | Ordinal Logistic Regression | 结构化数据 | ordered category、multi numeric | 目录条目 | statistical_catalog |
| `ordinal_logit_table` | Ordinal Logistic Regression | 表格 | ordered category、multi numeric | 目录条目 | statistical_catalog |
| `ordinal_logit_text` | Ordinal Logistic Regression | 文字解读 | ordered category、multi numeric | 目录条目 | statistical_catalog |
| `piecewise_regression_data` | Piecewise Regression | 结构化数据 | target、features | 目录条目 | statistical_catalog |
| `piecewise_regression_table` | Piecewise Regression | 表格 | target、features | 目录条目 | statistical_catalog |
| `piecewise_regression_text` | Piecewise Regression | 文字解读 | target、features | 目录条目 | statistical_catalog |
| `poisson_glm_data` | Poisson GLM | 结构化数据 | count、multi numeric | 可运行 | statistical_catalog |
| `poisson_glm_table` | Poisson GLM | 表格 | count、multi numeric | 可运行 | statistical_catalog |
| `poisson_glm_text` | Poisson GLM | 文字解读 | count、multi numeric | 可运行 | statistical_catalog |
| `prediction_interval_data` | Prediction Interval | 结构化数据 | target、features | 目录条目 | statistical_catalog |
| `prediction_interval_table` | Prediction Interval | 表格 | target、features | 目录条目 | statistical_catalog |
| `prediction_interval_text` | Prediction Interval | 文字解读 | target、features | 目录条目 | statistical_catalog |
| `probit_regression_data` | Probit Regression | 结构化数据 | binary、multi numeric | 目录条目 | statistical_catalog |
| `probit_regression_table` | Probit Regression | 表格 | binary、multi numeric | 目录条目 | statistical_catalog |
| `probit_regression_text` | Probit Regression | 文字解读 | binary、multi numeric | 目录条目 | statistical_catalog |
| `quantile_regression_data` | Quantile Regression | 结构化数据 | 数值字段、multi numeric | 可运行 | statistical_catalog |
| `quantile_regression_table` | Quantile Regression | 表格 | 数值字段、multi numeric | 可运行 | statistical_catalog |
| `quantile_regression_text` | Quantile Regression | 文字解读 | 数值字段、multi numeric | 可运行 | statistical_catalog |
| `residual_diagnostic_panel_data` | Residual Diagnostic Panel | 结构化数据 | target、features | 目录条目 | statistical_catalog |
| `residual_diagnostic_panel_table` | Residual Diagnostic Panel | 表格 | target、features | 目录条目 | statistical_catalog |
| `residual_diagnostic_panel_text` | Residual Diagnostic Panel | 文字解读 | target、features | 目录条目 | statistical_catalog |
| `ridge_regression_data` | Ridge Regression | 结构化数据 | 数值字段、multi numeric | 可运行 | statistical_catalog |
| `ridge_regression_table` | Ridge Regression | 表格 | 数值字段、multi numeric | 可运行 | statistical_catalog |
| `ridge_regression_text` | Ridge Regression | 文字解读 | 数值字段、multi numeric | 可运行 | statistical_catalog |
| `robust_regression_data` | Robust Regression | 结构化数据 | 数值字段、multi numeric | 可运行 | statistical_catalog |
| `robust_regression_table` | Robust Regression | 表格 | 数值字段、multi numeric | 可运行 | statistical_catalog |
| `robust_regression_text` | Robust Regression | 文字解读 | 数值字段、multi numeric | 可运行 | statistical_catalog |
| `spatial_error_model_data` | Spatial Error Model | 结构化数据 | target、features、对象级 | 目录条目 | statistical_catalog |
| `spatial_error_model_table` | Spatial Error Model | 表格 | target、features、对象级 | 目录条目 | statistical_catalog |
| `spatial_error_model_text` | Spatial Error Model | 文字解读 | target、features、对象级 | 目录条目 | statistical_catalog |
| `spatial_lag_model_data` | Spatial Lag Model | 结构化数据 | target、features、对象级 | 目录条目 | statistical_catalog |
| `spatial_lag_model_table` | Spatial Lag Model | 表格 | target、features、对象级 | 目录条目 | statistical_catalog |
| `spatial_lag_model_text` | Spatial Lag Model | 文字解读 | target、features、对象级 | 目录条目 | statistical_catalog |
| `spline_regression_chart` | Spline Regression | 图表 | target、features | 目录条目 | statistical_catalog |
| `spline_regression_data` | Spline Regression | 结构化数据 | target、features | 目录条目 | statistical_catalog |
| `spline_regression_image_spec` | Spline Regression | 图片规格 | target、features | 目录条目 | statistical_catalog |
| `spline_regression_report_section` | Spline Regression | 报告段落 | target、features | 目录条目 | statistical_catalog |
| `spline_regression_table` | Spline Regression | 表格 | target、features | 目录条目 | statistical_catalog |
| `spline_regression_text` | Spline Regression | 文字解读 | target、features | 目录条目 | statistical_catalog |
| `stepwise_model_comparison_data` | Stepwise Model Comparison | 结构化数据 | target、features | 目录条目 | statistical_catalog |
| `stepwise_model_comparison_table` | Stepwise Model Comparison | 表格 | target、features | 目录条目 | statistical_catalog |
| `stepwise_model_comparison_text` | Stepwise Model Comparison | 文字解读 | target、features | 目录条目 | statistical_catalog |
| `vif_multicollinearity_data` | VIF Multicollinearity Diagnostic | 结构化数据 | target、features | 目录条目 | statistical_catalog |
| `vif_multicollinearity_table` | VIF Multicollinearity Diagnostic | 表格 | target、features | 目录条目 | statistical_catalog |
| `vif_multicollinearity_text` | VIF Multicollinearity Diagnostic | 文字解读 | target、features | 目录条目 | statistical_catalog |
| `zero_inflated_poisson_data` | Zero-inflated Poisson | 结构化数据 | count、multi numeric | 目录条目 | statistical_catalog |
| `zero_inflated_poisson_table` | Zero-inflated Poisson | 表格 | count、multi numeric | 目录条目 | statistical_catalog |
| `zero_inflated_poisson_text` | Zero-inflated Poisson | 文字解读 | count、multi numeric | 目录条目 | statistical_catalog |

### 心理测量（24 张；可运行 0 张）

| 卡片 ID | 方法概念 | 输出形态 | 字段角色 | 状态 | 来源 |
| --- | --- | --- | --- | --- | --- |
| `item_response_theory_data` | Item Response Theory | 结构化数据 | item response | 目录条目 | statistical_catalog |
| `item_response_theory_table` | Item Response Theory | 表格 | item response | 目录条目 | statistical_catalog |
| `item_response_theory_text` | Item Response Theory | 文字解读 | item response | 目录条目 | statistical_catalog |
| `latent_growth_model_data` | Latent Growth Model | 结构化数据 | repeated measure | 目录条目 | statistical_catalog |
| `latent_growth_model_table` | Latent Growth Model | 表格 | repeated measure | 目录条目 | statistical_catalog |
| `latent_growth_model_text` | Latent Growth Model | 文字解读 | repeated measure | 目录条目 | statistical_catalog |
| `measurement_invariance_data` | Measurement Invariance | 结构化数据 | multi group scale | 目录条目 | statistical_catalog |
| `measurement_invariance_table` | Measurement Invariance | 表格 | multi group scale | 目录条目 | statistical_catalog |
| `measurement_invariance_text` | Measurement Invariance | 文字解读 | multi group scale | 目录条目 | statistical_catalog |
| `mediation_analysis_data` | Mediation Analysis | 结构化数据 | x、m、y | 目录条目 | statistical_catalog |
| `mediation_analysis_table` | Mediation Analysis | 表格 | x、m、y | 目录条目 | statistical_catalog |
| `mediation_analysis_text` | Mediation Analysis | 文字解读 | x、m、y | 目录条目 | statistical_catalog |
| `moderation_analysis_data` | Moderation Analysis | 结构化数据 | x、moderator、y | 目录条目 | statistical_catalog |
| `moderation_analysis_table` | Moderation Analysis | 表格 | x、moderator、y | 目录条目 | statistical_catalog |
| `moderation_analysis_text` | Moderation Analysis | 文字解读 | x、moderator、y | 目录条目 | statistical_catalog |
| `reliability_cronbach_alpha_data` | Cronbach Alpha | 结构化数据 | multi item scale | 目录条目 | statistical_catalog |
| `reliability_cronbach_alpha_table` | Cronbach Alpha | 表格 | multi item scale | 目录条目 | statistical_catalog |
| `reliability_cronbach_alpha_text` | Cronbach Alpha | 文字解读 | multi item scale | 目录条目 | statistical_catalog |
| `sem_data` | Structural Equation Modeling | 结构化数据 | multi numeric、latent | 目录条目 | statistical_catalog |
| `sem_table` | Structural Equation Modeling | 表格 | multi numeric、latent | 目录条目 | statistical_catalog |
| `sem_text` | Structural Equation Modeling | 文字解读 | multi numeric、latent | 目录条目 | statistical_catalog |
| `split_half_reliability_data` | Split-half Reliability | 结构化数据 | multi item scale | 目录条目 | statistical_catalog |
| `split_half_reliability_table` | Split-half Reliability | 表格 | multi item scale | 目录条目 | statistical_catalog |
| `split_half_reliability_text` | Split-half Reliability | 文字解读 | multi item scale | 目录条目 | statistical_catalog |

### 报告部件（14 张；可运行 0 张）

| 卡片 ID | 方法概念 | 输出形态 | 字段角色 | 状态 | 来源 |
| --- | --- | --- | --- | --- | --- |
| `explainable_dashboard_narrative_chart` | Explainable Dashboard Narrative | 图表 | 全数据集 | 目录条目 | statistical_catalog |
| `explainable_dashboard_narrative_data` | Explainable Dashboard Narrative | 结构化数据 | 全数据集 | 目录条目 | statistical_catalog |
| `explainable_dashboard_narrative_image_spec` | Explainable Dashboard Narrative | 图片规格 | 全数据集 | 目录条目 | statistical_catalog |
| `explainable_dashboard_narrative_report_section` | Explainable Dashboard Narrative | 报告段落 | 全数据集 | 目录条目 | statistical_catalog |
| `explainable_dashboard_narrative_table` | Explainable Dashboard Narrative | 表格 | 全数据集 | 目录条目 | statistical_catalog |
| `explainable_dashboard_narrative_text` | Explainable Dashboard Narrative | 文字解读 | 全数据集 | 目录条目 | statistical_catalog |
| `report_part_action_plan` | 行动建议 | 报告段落 | 全数据集 | 规划条目 | auto_analysis_specs |
| `report_part_appendix` | 分析附录 | 报告段落 | 全数据集 | 规划条目 | auto_analysis_specs |
| `report_part_chapter` | 分析章节 | 报告段落 | 全数据集 | 规划条目 | auto_analysis_specs |
| `report_part_evidence_index` | 证据索引 | 报告段落 | 全数据集 | 规划条目 | auto_analysis_specs |
| `report_part_executive_summary` | 管理摘要 | 报告段落 | 全数据集 | 规划条目 | auto_analysis_specs |
| `report_part_field_glossary` | 字段解释 | 报告段落 | 全数据集 | 规划条目 | auto_analysis_specs |
| `report_part_method_note` | 方法说明 | 报告段落 | 全数据集 | 规划条目 | auto_analysis_specs |
| `report_part_visual_gallery` | 图组解读 | 报告段落 | 全数据集 | 规划条目 | auto_analysis_specs |

### 描述统计（210 张；可运行 36 张）

| 卡片 ID | 方法概念 | 输出形态 | 字段角色 | 状态 | 来源 |
| --- | --- | --- | --- | --- | --- |
| `areal_interpolation_data` | Areal Interpolation | 结构化数据 | 对象级、数值字段 | 目录条目 | statistical_catalog |
| `areal_interpolation_table` | Areal Interpolation | 表格 | 对象级、数值字段 | 目录条目 | statistical_catalog |
| `areal_interpolation_text` | Areal Interpolation | 文字解读 | 对象级、数值字段 | 目录条目 | statistical_catalog |
| `boxcox_transformation_data` | Box-Cox Transformation | 结构化数据 | 数值字段 | 目录条目 | statistical_catalog |
| `boxcox_transformation_table` | Box-Cox Transformation | 表格 | 数值字段 | 目录条目 | statistical_catalog |
| `boxcox_transformation_text` | Box-Cox Transformation | 文字解读 | 数值字段 | 目录条目 | statistical_catalog |
| `business_rule_validation_data` | Business Rule Validation | 结构化数据 | 字段组 | 目录条目 | statistical_catalog |
| `business_rule_validation_table` | Business Rule Validation | 表格 | 字段组 | 目录条目 | statistical_catalog |
| `business_rule_validation_text` | Business Rule Validation | 文字解读 | 字段组 | 目录条目 | statistical_catalog |
| `cluster_sampling_design_data` | Cluster Sampling Design | 结构化数据 | 对象级、分组 | 目录条目 | statistical_catalog |
| `cluster_sampling_design_table` | Cluster Sampling Design | 表格 | 对象级、分组 | 目录条目 | statistical_catalog |
| `cluster_sampling_design_text` | Cluster Sampling Design | 文字解读 | 对象级、分组 | 目录条目 | statistical_catalog |
| `cohort_summary_chart` | Cohort Summary | 图表 | time、分类字段、数值字段 | 目录条目 | statistical_catalog |
| `cohort_summary_data` | Cohort Summary | 结构化数据 | time、分类字段、数值字段 | 目录条目 | statistical_catalog |
| `cohort_summary_image_spec` | Cohort Summary | 图片规格 | time、分类字段、数值字段 | 目录条目 | statistical_catalog |
| `cohort_summary_report_section` | Cohort Summary | 报告段落 | time、分类字段、数值字段 | 目录条目 | statistical_catalog |
| `cohort_summary_table` | Cohort Summary | 表格 | time、分类字段、数值字段 | 目录条目 | statistical_catalog |
| `cohort_summary_text` | Cohort Summary | 文字解读 | time、分类字段、数值字段 | 目录条目 | statistical_catalog |
| `completeness_sla_monitor_data` | Completeness SLA Monitor | 结构化数据 | 全数据集 | 目录条目 | statistical_catalog |
| `completeness_sla_monitor_table` | Completeness SLA Monitor | 表格 | 全数据集 | 目录条目 | statistical_catalog |
| `completeness_sla_monitor_text` | Completeness SLA Monitor | 文字解读 | 全数据集 | 目录条目 | statistical_catalog |
| `consent_coverage_audit_data` | Consent Coverage Audit | 结构化数据 | 字段组 | 目录条目 | statistical_catalog |
| `consent_coverage_audit_table` | Consent Coverage Audit | 表格 | 字段组 | 目录条目 | statistical_catalog |
| `consent_coverage_audit_text` | Consent Coverage Audit | 文字解读 | 字段组 | 目录条目 | statistical_catalog |
| `cross_tabulation_data` | Cross Tabulation | 结构化数据 | 分类字段、分类字段 | 可运行 | statistical_catalog |
| `cross_tabulation_table` | Cross Tabulation | 表格 | 分类字段、分类字段 | 可运行 | statistical_catalog |
| `cross_tabulation_text` | Cross Tabulation | 文字解读 | 分类字段、分类字段 | 可运行 | statistical_catalog |
| `data_contract_validation_data` | Data Contract Validation | 结构化数据 | 全数据集 | 目录条目 | statistical_catalog |
| `data_contract_validation_table` | Data Contract Validation | 表格 | 全数据集 | 目录条目 | statistical_catalog |
| `data_contract_validation_text` | Data Contract Validation | 文字解读 | 全数据集 | 目录条目 | statistical_catalog |
| `data_minimization_audit_data` | Data Minimization Audit | 结构化数据 | 字段组 | 目录条目 | statistical_catalog |
| `data_minimization_audit_table` | Data Minimization Audit | 表格 | 字段组 | 目录条目 | statistical_catalog |
| `data_minimization_audit_text` | Data Minimization Audit | 文字解读 | 字段组 | 目录条目 | statistical_catalog |
| `data_quality_scorecard_data` | Data Quality Scorecard | 结构化数据 | 全数据集 | 目录条目 | statistical_catalog |
| `data_quality_scorecard_table` | Data Quality Scorecard | 表格 | 全数据集 | 目录条目 | statistical_catalog |
| `data_quality_scorecard_text` | Data Quality Scorecard | 文字解读 | 全数据集 | 目录条目 | statistical_catalog |
| `data_type_validation_data` | Data Type Validation | 结构化数据 | 字段组 | 目录条目 | statistical_catalog |
| `data_type_validation_table` | Data Type Validation | 表格 | 字段组 | 目录条目 | statistical_catalog |
| `data_type_validation_text` | Data Type Validation | 文字解读 | 字段组 | 目录条目 | statistical_catalog |
| `datasheet_for_dataset_data` | Datasheet for Dataset | 结构化数据 | 全数据集 | 目录条目 | statistical_catalog |
| `datasheet_for_dataset_table` | Datasheet for Dataset | 表格 | 全数据集 | 目录条目 | statistical_catalog |
| `datasheet_for_dataset_text` | Datasheet for Dataset | 文字解读 | 全数据集 | 目录条目 | statistical_catalog |
| `denominator_integrity_check_data` | Denominator Integrity Check | 结构化数据 | 字段对、分组 | 目录条目 | statistical_catalog |
| `denominator_integrity_check_table` | Denominator Integrity Check | 表格 | 字段对、分组 | 目录条目 | statistical_catalog |
| `denominator_integrity_check_text` | Denominator Integrity Check | 文字解读 | 字段对、分组 | 目录条目 | statistical_catalog |
| `descriptive_coverage` | 覆盖情况 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `descriptive_distribution` | 分布 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `descriptive_missingness` | 缺失情况 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `descriptive_profile` | 画像 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `descriptive_rank` | 排名 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `descriptive_segment` | 分层 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `descriptive_summary_data` | Descriptive Summary | 结构化数据 | 数值字段 | 可运行 | statistical_catalog |
| `descriptive_summary_table` | Descriptive Summary | 表格 | 数值字段 | 可运行 | statistical_catalog |
| `descriptive_summary_text` | Descriptive Summary | 文字解读 | 数值字段 | 可运行 | statistical_catalog |
| `duplicate_record_audit_data` | Duplicate Record Audit | 结构化数据 | 字段组 | 目录条目 | statistical_catalog |
| `duplicate_record_audit_table` | Duplicate Record Audit | 表格 | 字段组 | 目录条目 | statistical_catalog |
| `duplicate_record_audit_text` | Duplicate Record Audit | 文字解读 | 字段组 | 目录条目 | statistical_catalog |
| `ego_network_profile_data` | Ego Network Profile | 结构化数据 | 对象级 | 目录条目 | statistical_catalog |
| `ego_network_profile_table` | Ego Network Profile | 表格 | 对象级 | 目录条目 | statistical_catalog |
| `ego_network_profile_text` | Ego Network Profile | 文字解读 | 对象级 | 目录条目 | statistical_catalog |
| `feature_binning_strategy_data` | Feature Binning Strategy | 结构化数据 | 数值字段 | 目录条目 | statistical_catalog |
| `feature_binning_strategy_table` | Feature Binning Strategy | 表格 | 数值字段 | 目录条目 | statistical_catalog |
| `feature_binning_strategy_text` | Feature Binning Strategy | 文字解读 | 数值字段 | 目录条目 | statistical_catalog |
| `frequency_table_data` | Frequency Table | 结构化数据 | 分类字段 | 可运行 | statistical_catalog |
| `frequency_table_table` | Frequency Table | 表格 | 分类字段 | 可运行 | statistical_catalog |
| `frequency_table_text` | Frequency Table | 文字解读 | 分类字段 | 可运行 | statistical_catalog |
| `funnel_step_conversion_data` | Funnel Step Conversion | 结构化数据 | 分类字段、数值字段 | 目录条目 | statistical_catalog |
| `funnel_step_conversion_table` | Funnel Step Conversion | 表格 | 分类字段、数值字段 | 目录条目 | statistical_catalog |
| `funnel_step_conversion_text` | Funnel Step Conversion | 文字解读 | 分类字段、数值字段 | 目录条目 | statistical_catalog |
| `geohash_grid_aggregation_chart` | Geohash Grid Aggregation | 图表 | 对象级、数值字段 | 目录条目 | statistical_catalog |
| `geohash_grid_aggregation_data` | Geohash Grid Aggregation | 结构化数据 | 对象级、数值字段 | 目录条目 | statistical_catalog |
| `geohash_grid_aggregation_image_spec` | Geohash Grid Aggregation | 图片规格 | 对象级、数值字段 | 目录条目 | statistical_catalog |
| `geohash_grid_aggregation_report_section` | Geohash Grid Aggregation | 报告段落 | 对象级、数值字段 | 目录条目 | statistical_catalog |
| `geohash_grid_aggregation_table` | Geohash Grid Aggregation | 表格 | 对象级、数值字段 | 目录条目 | statistical_catalog |
| `geohash_grid_aggregation_text` | Geohash Grid Aggregation | 文字解读 | 对象级、数值字段 | 目录条目 | statistical_catalog |
| `gini_coefficient_data` | Gini Coefficient | 结构化数据 | 数值字段 | 可运行 | statistical_catalog |
| `gini_coefficient_table` | Gini Coefficient | 表格 | 数值字段 | 可运行 | statistical_catalog |
| `gini_coefficient_text` | Gini Coefficient | 文字解读 | 数值字段 | 可运行 | statistical_catalog |
| `high_cardinality_profile_data` | High-cardinality Profile | 结构化数据 | 分类字段 | 目录条目 | statistical_catalog |
| `high_cardinality_profile_table` | High-cardinality Profile | 表格 | 分类字段 | 目录条目 | statistical_catalog |
| `high_cardinality_profile_text` | High-cardinality Profile | 文字解读 | 分类字段 | 目录条目 | statistical_catalog |
| `imputation_strategy_plan_data` | Imputation Strategy Plan | 结构化数据 | 字段组 | 目录条目 | statistical_catalog |
| `imputation_strategy_plan_table` | Imputation Strategy Plan | 表格 | 字段组 | 目录条目 | statistical_catalog |
| `imputation_strategy_plan_text` | Imputation Strategy Plan | 文字解读 | 字段组 | 目录条目 | statistical_catalog |
| `keyword_in_context_review_data` | Keyword-in-context Review | 结构化数据 | 字段组 | 目录条目 | statistical_catalog |
| `keyword_in_context_review_table` | Keyword-in-context Review | 表格 | 字段组 | 目录条目 | statistical_catalog |
| `keyword_in_context_review_text` | Keyword-in-context Review | 文字解读 | 字段组 | 目录条目 | statistical_catalog |
| `lorenz_curve_chart` | Lorenz Curve | 图表 | 数值字段 | 目录条目 | statistical_catalog |
| `lorenz_curve_data` | Lorenz Curve | 结构化数据 | 数值字段 | 目录条目 | statistical_catalog |
| `lorenz_curve_image_spec` | Lorenz Curve | 图片规格 | 数值字段 | 目录条目 | statistical_catalog |
| `lorenz_curve_report_section` | Lorenz Curve | 报告段落 | 数值字段 | 目录条目 | statistical_catalog |
| `lorenz_curve_table` | Lorenz Curve | 表格 | 数值字段 | 目录条目 | statistical_catalog |
| `lorenz_curve_text` | Lorenz Curve | 文字解读 | 数值字段 | 目录条目 | statistical_catalog |
| `measurement_error_audit_data` | Measurement Error Audit | 结构化数据 | 字段组 | 目录条目 | statistical_catalog |
| `measurement_error_audit_table` | Measurement Error Audit | 表格 | 字段组 | 目录条目 | statistical_catalog |
| `measurement_error_audit_text` | Measurement Error Audit | 文字解读 | 字段组 | 目录条目 | statistical_catalog |
| `missingness_heatmap_audit_chart` | Missingness Heatmap Audit | 图表 | 字段组 | 目录条目 | statistical_catalog |
| `missingness_heatmap_audit_data` | Missingness Heatmap Audit | 结构化数据 | 字段组 | 目录条目 | statistical_catalog |
| `missingness_heatmap_audit_image_spec` | Missingness Heatmap Audit | 图片规格 | 字段组 | 目录条目 | statistical_catalog |
| `missingness_heatmap_audit_report_section` | Missingness Heatmap Audit | 报告段落 | 字段组 | 目录条目 | statistical_catalog |
| `missingness_heatmap_audit_table` | Missingness Heatmap Audit | 表格 | 字段组 | 目录条目 | statistical_catalog |
| `missingness_heatmap_audit_text` | Missingness Heatmap Audit | 文字解读 | 字段组 | 目录条目 | statistical_catalog |
| `missingness_mechanism_diagnostic_data` | Missingness Mechanism Diagnostic | 结构化数据 | 字段组 | 目录条目 | statistical_catalog |
| `missingness_mechanism_diagnostic_table` | Missingness Mechanism Diagnostic | 表格 | 字段组 | 目录条目 | statistical_catalog |
| `missingness_mechanism_diagnostic_text` | Missingness Mechanism Diagnostic | 文字解读 | 字段组 | 目录条目 | statistical_catalog |
| `nonresponse_bias_analysis_data` | Nonresponse Bias Analysis | 结构化数据 | 字段组、分组 | 目录条目 | statistical_catalog |
| `nonresponse_bias_analysis_table` | Nonresponse Bias Analysis | 表格 | 字段组、分组 | 目录条目 | statistical_catalog |
| `nonresponse_bias_analysis_text` | Nonresponse Bias Analysis | 文字解读 | 字段组、分组 | 目录条目 | statistical_catalog |
| `north_star_metric_audit_data` | North-star Metric Audit | 结构化数据 | 字段组 | 目录条目 | statistical_catalog |
| `north_star_metric_audit_table` | North-star Metric Audit | 表格 | 字段组 | 目录条目 | statistical_catalog |
| `north_star_metric_audit_text` | North-star Metric Audit | 文字解读 | 字段组 | 目录条目 | statistical_catalog |
| `outlier_screening_iqr_data` | IQR Outlier Screening | 结构化数据 | 数值字段 | 目录条目 | statistical_catalog |
| `outlier_screening_iqr_table` | IQR Outlier Screening | 表格 | 数值字段 | 目录条目 | statistical_catalog |
| `outlier_screening_iqr_text` | IQR Outlier Screening | 文字解读 | 数值字段 | 目录条目 | statistical_catalog |
| `pareto_analysis_chart` | Pareto Analysis | 图表 | 分类字段、数值字段 | 可运行 | statistical_catalog |
| `pareto_analysis_data` | Pareto Analysis | 结构化数据 | 分类字段、数值字段 | 可运行 | statistical_catalog |
| `pareto_analysis_image_spec` | Pareto Analysis | 图片规格 | 分类字段、数值字段 | 可运行 | statistical_catalog |
| `pareto_analysis_report_section` | Pareto Analysis | 报告段落 | 分类字段、数值字段 | 可运行 | statistical_catalog |
| `pareto_analysis_table` | Pareto Analysis | 表格 | 分类字段、数值字段 | 可运行 | statistical_catalog |
| `pareto_analysis_text` | Pareto Analysis | 文字解读 | 分类字段、数值字段 | 可运行 | statistical_catalog |
| `pii_detection_profile_data` | PII Detection Profile | 结构化数据 | 字段组 | 目录条目 | statistical_catalog |
| `pii_detection_profile_table` | PII Detection Profile | 表格 | 字段组 | 目录条目 | statistical_catalog |
| `pii_detection_profile_text` | PII Detection Profile | 文字解读 | 字段组 | 目录条目 | statistical_catalog |
| `pivot_summary_data` | Pivot Summary | 结构化数据 | 分类字段、数值字段 | 可运行 | statistical_catalog |
| `pivot_summary_table` | Pivot Summary | 表格 | 分类字段、数值字段 | 可运行 | statistical_catalog |
| `pivot_summary_text` | Pivot Summary | 文字解读 | 分类字段、数值字段 | 可运行 | statistical_catalog |
| `post_stratification_weighting_data` | Post-stratification Weighting | 结构化数据 | 字段组、分组 | 目录条目 | statistical_catalog |
| `post_stratification_weighting_table` | Post-stratification Weighting | 表格 | 字段组、分组 | 目录条目 | statistical_catalog |
| `post_stratification_weighting_text` | Post-stratification Weighting | 文字解读 | 字段组、分组 | 目录条目 | statistical_catalog |
| `privacy_k_anonymity_data` | k-anonymity Privacy Check | 结构化数据 | 字段组 | 目录条目 | statistical_catalog |
| `privacy_k_anonymity_table` | k-anonymity Privacy Check | 表格 | 字段组 | 目录条目 | statistical_catalog |
| `privacy_k_anonymity_text` | k-anonymity Privacy Check | 文字解读 | 字段组 | 目录条目 | statistical_catalog |
| `privacy_l_diversity_data` | l-diversity Privacy Check | 结构化数据 | 字段组 | 目录条目 | statistical_catalog |
| `privacy_l_diversity_table` | l-diversity Privacy Check | 表格 | 字段组 | 目录条目 | statistical_catalog |
| `privacy_l_diversity_text` | l-diversity Privacy Check | 文字解读 | 字段组 | 目录条目 | statistical_catalog |
| `quantile_profile_data` | Quantile Profile | 结构化数据 | 数值字段 | 可运行 | statistical_catalog |
| `quantile_profile_table` | Quantile Profile | 表格 | 数值字段 | 可运行 | statistical_catalog |
| `quantile_profile_text` | Quantile Profile | 文字解读 | 数值字段 | 可运行 | statistical_catalog |
| `raking_weighting_data` | Raking Weighting | 结构化数据 | 字段组、分组 | 目录条目 | statistical_catalog |
| `raking_weighting_table` | Raking Weighting | 表格 | 字段组、分组 | 目录条目 | statistical_catalog |
| `raking_weighting_text` | Raking Weighting | 文字解读 | 字段组、分组 | 目录条目 | statistical_catalog |
| `range_constraint_validation_data` | Range Constraint Validation | 结构化数据 | 字段组 | 目录条目 | statistical_catalog |
| `range_constraint_validation_table` | Range Constraint Validation | 表格 | 字段组 | 目录条目 | statistical_catalog |
| `range_constraint_validation_text` | Range Constraint Validation | 文字解读 | 字段组 | 目录条目 | statistical_catalog |
| `rare_category_consolidation_data` | Rare Category Consolidation | 结构化数据 | 分类字段 | 目录条目 | statistical_catalog |
| `rare_category_consolidation_table` | Rare Category Consolidation | 表格 | 分类字段 | 目录条目 | statistical_catalog |
| `rare_category_consolidation_text` | Rare Category Consolidation | 文字解读 | 分类字段 | 目录条目 | statistical_catalog |
| `referential_integrity_check_data` | Referential Integrity Check | 结构化数据 | 字段组 | 目录条目 | statistical_catalog |
| `referential_integrity_check_table` | Referential Integrity Check | 表格 | 字段组 | 目录条目 | statistical_catalog |
| `referential_integrity_check_text` | Referential Integrity Check | 文字解读 | 字段组 | 目录条目 | statistical_catalog |
| `retention_policy_audit_data` | Retention Policy Audit | 结构化数据 | time、字段组 | 目录条目 | statistical_catalog |
| `retention_policy_audit_table` | Retention Policy Audit | 表格 | time、字段组 | 目录条目 | statistical_catalog |
| `retention_policy_audit_text` | Retention Policy Audit | 文字解读 | time、字段组 | 目录条目 | statistical_catalog |
| `robust_zscore_outlier_data` | Robust Z-score Outlier Screening | 结构化数据 | 数值字段 | 目录条目 | statistical_catalog |
| `robust_zscore_outlier_table` | Robust Z-score Outlier Screening | 表格 | 数值字段 | 目录条目 | statistical_catalog |
| `robust_zscore_outlier_text` | Robust Z-score Outlier Screening | 文字解读 | 数值字段 | 目录条目 | statistical_catalog |
| `root_cause_data_quality_data` | Data Quality Root Cause Analysis | 结构化数据 | 全数据集 | 目录条目 | statistical_catalog |
| `root_cause_data_quality_table` | Data Quality Root Cause Analysis | 表格 | 全数据集 | 目录条目 | statistical_catalog |
| `root_cause_data_quality_text` | Data Quality Root Cause Analysis | 文字解读 | 全数据集 | 目录条目 | statistical_catalog |
| `sampling_bias_audit_data` | Sampling Bias Audit | 结构化数据 | 字段组、分组 | 目录条目 | statistical_catalog |
| `sampling_bias_audit_table` | Sampling Bias Audit | 表格 | 字段组、分组 | 目录条目 | statistical_catalog |
| `sampling_bias_audit_text` | Sampling Bias Audit | 文字解读 | 字段组、分组 | 目录条目 | statistical_catalog |
| `schema_drift_detection_data` | Schema Drift Detection | 结构化数据 | 全数据集 | 目录条目 | statistical_catalog |
| `schema_drift_detection_table` | Schema Drift Detection | 表格 | 全数据集 | 目录条目 | statistical_catalog |
| `schema_drift_detection_text` | Schema Drift Detection | 文字解读 | 全数据集 | 目录条目 | statistical_catalog |
| `segmented_kpi_breakdown_chart` | Segmented KPI Breakdown | 图表 | 分类字段、数值字段 | 可运行 | statistical_catalog |
| `segmented_kpi_breakdown_data` | Segmented KPI Breakdown | 结构化数据 | 分类字段、数值字段 | 可运行 | statistical_catalog |
| `segmented_kpi_breakdown_image_spec` | Segmented KPI Breakdown | 图片规格 | 分类字段、数值字段 | 可运行 | statistical_catalog |
| `segmented_kpi_breakdown_report_section` | Segmented KPI Breakdown | 报告段落 | 分类字段、数值字段 | 可运行 | statistical_catalog |
| `segmented_kpi_breakdown_table` | Segmented KPI Breakdown | 表格 | 分类字段、数值字段 | 可运行 | statistical_catalog |
| `segmented_kpi_breakdown_text` | Segmented KPI Breakdown | 文字解读 | 分类字段、数值字段 | 可运行 | statistical_catalog |
| `semantic_deduplication_data` | Semantic Deduplication | 结构化数据 | 字段组 | 目录条目 | statistical_catalog |
| `semantic_deduplication_table` | Semantic Deduplication | 表格 | 字段组 | 目录条目 | statistical_catalog |
| `semantic_deduplication_text` | Semantic Deduplication | 文字解读 | 字段组 | 目录条目 | statistical_catalog |
| `small_area_estimation_data` | Small Area Estimation | 结构化数据 | 对象级、分组 | 目录条目 | statistical_catalog |
| `small_area_estimation_table` | Small Area Estimation | 表格 | 对象级、分组 | 目录条目 | statistical_catalog |
| `small_area_estimation_text` | Small Area Estimation | 文字解读 | 对象级、分组 | 目录条目 | statistical_catalog |
| `spatial_join_audit_data` | Spatial Join Audit | 结构化数据 | 对象级 | 目录条目 | statistical_catalog |
| `spatial_join_audit_table` | Spatial Join Audit | 表格 | 对象级 | 目录条目 | statistical_catalog |
| `spatial_join_audit_text` | Spatial Join Audit | 文字解读 | 对象级 | 目录条目 | statistical_catalog |
| `standardization_scaling_data` | Standardization / Scaling | 结构化数据 | 字段组 | 目录条目 | statistical_catalog |
| `standardization_scaling_table` | Standardization / Scaling | 表格 | 字段组 | 目录条目 | statistical_catalog |
| `standardization_scaling_text` | Standardization / Scaling | 文字解读 | 字段组 | 目录条目 | statistical_catalog |
| `stratified_sampling_design_data` | Stratified Sampling Design | 结构化数据 | 分组、字段组 | 目录条目 | statistical_catalog |
| `stratified_sampling_design_table` | Stratified Sampling Design | 表格 | 分组、字段组 | 目录条目 | statistical_catalog |
| `stratified_sampling_design_text` | Stratified Sampling Design | 文字解读 | 分组、字段组 | 目录条目 | statistical_catalog |
| `survey_design_effect_chart` | Survey Design Effect | 图表 | 字段组、分组 | 目录条目 | statistical_catalog |
| `survey_design_effect_data` | Survey Design Effect | 结构化数据 | 字段组、分组 | 目录条目 | statistical_catalog |
| `survey_design_effect_image_spec` | Survey Design Effect | 图片规格 | 字段组、分组 | 目录条目 | statistical_catalog |
| `survey_design_effect_report_section` | Survey Design Effect | 报告段落 | 字段组、分组 | 目录条目 | statistical_catalog |
| `survey_design_effect_table` | Survey Design Effect | 表格 | 字段组、分组 | 目录条目 | statistical_catalog |
| `survey_design_effect_text` | Survey Design Effect | 文字解读 | 字段组、分组 | 目录条目 | statistical_catalog |
| `synthetic_data_quality_audit_data` | Synthetic Data Quality Audit | 结构化数据 | 全数据集 | 目录条目 | statistical_catalog |
| `synthetic_data_quality_audit_table` | Synthetic Data Quality Audit | 表格 | 全数据集 | 目录条目 | statistical_catalog |
| `synthetic_data_quality_audit_text` | Synthetic Data Quality Audit | 文字解读 | 全数据集 | 目录条目 | statistical_catalog |
| `trimmed_mean_data` | Trimmed Mean | 结构化数据 | 数值字段 | 可运行 | statistical_catalog |
| `trimmed_mean_table` | Trimmed Mean | 表格 | 数值字段 | 可运行 | statistical_catalog |
| `trimmed_mean_text` | Trimmed Mean | 文字解读 | 数值字段 | 可运行 | statistical_catalog |
| `uniqueness_constraint_check_data` | Uniqueness Constraint Check | 结构化数据 | 字段组 | 目录条目 | statistical_catalog |
| `uniqueness_constraint_check_table` | Uniqueness Constraint Check | 表格 | 字段组 | 目录条目 | statistical_catalog |
| `uniqueness_constraint_check_text` | Uniqueness Constraint Check | 文字解读 | 字段组 | 目录条目 | statistical_catalog |
| `winsorization_strategy_data` | Winsorization Strategy | 结构化数据 | 数值字段 | 目录条目 | statistical_catalog |
| `winsorization_strategy_table` | Winsorization Strategy | 表格 | 数值字段 | 目录条目 | statistical_catalog |
| `winsorization_strategy_text` | Winsorization Strategy | 文字解读 | 数值字段 | 目录条目 | statistical_catalog |
| `winsorized_summary_data` | Winsorized Summary | 结构化数据 | 数值字段 | 可运行 | statistical_catalog |
| `winsorized_summary_table` | Winsorized Summary | 表格 | 数值字段 | 可运行 | statistical_catalog |
| `winsorized_summary_text` | Winsorized Summary | 文字解读 | 数值字段 | 可运行 | statistical_catalog |
| `yeo_johnson_transformation_data` | Yeo-Johnson Transformation | 结构化数据 | 数值字段 | 目录条目 | statistical_catalog |
| `yeo_johnson_transformation_table` | Yeo-Johnson Transformation | 表格 | 数值字段 | 目录条目 | statistical_catalog |
| `yeo_johnson_transformation_text` | Yeo-Johnson Transformation | 文字解读 | 数值字段 | 目录条目 | statistical_catalog |

### 时间序列（198 张；可运行 30 张）

| 卡片 ID | 方法概念 | 输出形态 | 字段角色 | 状态 | 来源 |
| --- | --- | --- | --- | --- | --- |
| `adf_test_chart` | Augmented Dickey-Fuller Test | 图表 | time、数值字段 | 可运行 | statistical_catalog |
| `adf_test_data` | Augmented Dickey-Fuller Test | 结构化数据 | time、数值字段 | 可运行 | statistical_catalog |
| `adf_test_image_spec` | Augmented Dickey-Fuller Test | 图片规格 | time、数值字段 | 可运行 | statistical_catalog |
| `adf_test_report_section` | Augmented Dickey-Fuller Test | 报告段落 | time、数值字段 | 可运行 | statistical_catalog |
| `adf_test_table` | Augmented Dickey-Fuller Test | 表格 | time、数值字段 | 可运行 | statistical_catalog |
| `adf_test_text` | Augmented Dickey-Fuller Test | 文字解读 | time、数值字段 | 可运行 | statistical_catalog |
| `alert_threshold_backtest_chart` | Alert Threshold Backtest | 图表 | time、数值字段 | 目录条目 | statistical_catalog |
| `alert_threshold_backtest_data` | Alert Threshold Backtest | 结构化数据 | time、数值字段 | 目录条目 | statistical_catalog |
| `alert_threshold_backtest_image_spec` | Alert Threshold Backtest | 图片规格 | time、数值字段 | 目录条目 | statistical_catalog |
| `alert_threshold_backtest_report_section` | Alert Threshold Backtest | 报告段落 | time、数值字段 | 目录条目 | statistical_catalog |
| `alert_threshold_backtest_table` | Alert Threshold Backtest | 表格 | time、数值字段 | 目录条目 | statistical_catalog |
| `alert_threshold_backtest_text` | Alert Threshold Backtest | 文字解读 | time、数值字段 | 目录条目 | statistical_catalog |
| `arima_chart` | ARIMA | 图表 | time、数值字段 | 目录条目 | statistical_catalog |
| `arima_data` | ARIMA | 结构化数据 | time、数值字段 | 目录条目 | statistical_catalog |
| `arima_image_spec` | ARIMA | 图片规格 | time、数值字段 | 目录条目 | statistical_catalog |
| `arima_report_section` | ARIMA | 报告段落 | time、数值字段 | 目录条目 | statistical_catalog |
| `arima_table` | ARIMA | 表格 | time、数值字段 | 目录条目 | statistical_catalog |
| `arima_text` | ARIMA | 文字解读 | time、数值字段 | 目录条目 | statistical_catalog |
| `autocorrelation_chart` | Autocorrelation Analysis | 图表 | time、数值字段 | 可运行 | statistical_catalog |
| `autocorrelation_data` | Autocorrelation Analysis | 结构化数据 | time、数值字段 | 可运行 | statistical_catalog |
| `autocorrelation_image_spec` | Autocorrelation Analysis | 图片规格 | time、数值字段 | 可运行 | statistical_catalog |
| `autocorrelation_report_section` | Autocorrelation Analysis | 报告段落 | time、数值字段 | 可运行 | statistical_catalog |
| `autocorrelation_table` | Autocorrelation Analysis | 表格 | time、数值字段 | 可运行 | statistical_catalog |
| `autocorrelation_text` | Autocorrelation Analysis | 文字解读 | time、数值字段 | 可运行 | statistical_catalog |
| `control_chart_rule_set_chart` | Control Chart Rule Set | 图表 | time、数值字段 | 目录条目 | statistical_catalog |
| `control_chart_rule_set_data` | Control Chart Rule Set | 结构化数据 | time、数值字段 | 目录条目 | statistical_catalog |
| `control_chart_rule_set_image_spec` | Control Chart Rule Set | 图片规格 | time、数值字段 | 目录条目 | statistical_catalog |
| `control_chart_rule_set_report_section` | Control Chart Rule Set | 报告段落 | time、数值字段 | 目录条目 | statistical_catalog |
| `control_chart_rule_set_table` | Control Chart Rule Set | 表格 | time、数值字段 | 目录条目 | statistical_catalog |
| `control_chart_rule_set_text` | Control Chart Rule Set | 文字解读 | time、数值字段 | 目录条目 | statistical_catalog |
| `cross_correlation_lag_chart` | Cross-correlation Lag Analysis | 图表 | time、数值字段、数值字段 | 目录条目 | statistical_catalog |
| `cross_correlation_lag_data` | Cross-correlation Lag Analysis | 结构化数据 | time、数值字段、数值字段 | 目录条目 | statistical_catalog |
| `cross_correlation_lag_image_spec` | Cross-correlation Lag Analysis | 图片规格 | time、数值字段、数值字段 | 目录条目 | statistical_catalog |
| `cross_correlation_lag_report_section` | Cross-correlation Lag Analysis | 报告段落 | time、数值字段、数值字段 | 目录条目 | statistical_catalog |
| `cross_correlation_lag_table` | Cross-correlation Lag Analysis | 表格 | time、数值字段、数值字段 | 目录条目 | statistical_catalog |
| `cross_correlation_lag_text` | Cross-correlation Lag Analysis | 文字解读 | time、数值字段、数值字段 | 目录条目 | statistical_catalog |
| `dynamic_regression_chart` | Dynamic Regression | 图表 | time、数值字段、features | 目录条目 | statistical_catalog |
| `dynamic_regression_data` | Dynamic Regression | 结构化数据 | time、数值字段、features | 目录条目 | statistical_catalog |
| `dynamic_regression_image_spec` | Dynamic Regression | 图片规格 | time、数值字段、features | 目录条目 | statistical_catalog |
| `dynamic_regression_report_section` | Dynamic Regression | 报告段落 | time、数值字段、features | 目录条目 | statistical_catalog |
| `dynamic_regression_table` | Dynamic Regression | 表格 | time、数值字段、features | 目录条目 | statistical_catalog |
| `dynamic_regression_text` | Dynamic Regression | 文字解读 | time、数值字段、features | 目录条目 | statistical_catalog |
| `forecast_backtesting_chart` | Forecast Backtesting | 图表 | time、数值字段 | 目录条目 | statistical_catalog |
| `forecast_backtesting_data` | Forecast Backtesting | 结构化数据 | time、数值字段 | 目录条目 | statistical_catalog |
| `forecast_backtesting_image_spec` | Forecast Backtesting | 图片规格 | time、数值字段 | 目录条目 | statistical_catalog |
| `forecast_backtesting_report_section` | Forecast Backtesting | 报告段落 | time、数值字段 | 目录条目 | statistical_catalog |
| `forecast_backtesting_table` | Forecast Backtesting | 表格 | time、数值字段 | 目录条目 | statistical_catalog |
| `forecast_backtesting_text` | Forecast Backtesting | 文字解读 | time、数值字段 | 目录条目 | statistical_catalog |
| `forecast_residual_diagnostics_chart` | Forecast Residual Diagnostics | 图表 | time、数值字段 | 目录条目 | statistical_catalog |
| `forecast_residual_diagnostics_data` | Forecast Residual Diagnostics | 结构化数据 | time、数值字段 | 目录条目 | statistical_catalog |
| `forecast_residual_diagnostics_image_spec` | Forecast Residual Diagnostics | 图片规格 | time、数值字段 | 目录条目 | statistical_catalog |
| `forecast_residual_diagnostics_report_section` | Forecast Residual Diagnostics | 报告段落 | time、数值字段 | 目录条目 | statistical_catalog |
| `forecast_residual_diagnostics_table` | Forecast Residual Diagnostics | 表格 | time、数值字段 | 目录条目 | statistical_catalog |
| `forecast_residual_diagnostics_text` | Forecast Residual Diagnostics | 文字解读 | time、数值字段 | 目录条目 | statistical_catalog |
| `freshness_sla_monitor_chart` | Freshness SLA Monitor | 图表 | time、全数据集 | 目录条目 | statistical_catalog |
| `freshness_sla_monitor_data` | Freshness SLA Monitor | 结构化数据 | time、全数据集 | 目录条目 | statistical_catalog |
| `freshness_sla_monitor_image_spec` | Freshness SLA Monitor | 图片规格 | time、全数据集 | 目录条目 | statistical_catalog |
| `freshness_sla_monitor_report_section` | Freshness SLA Monitor | 报告段落 | time、全数据集 | 目录条目 | statistical_catalog |
| `freshness_sla_monitor_table` | Freshness SLA Monitor | 表格 | time、全数据集 | 目录条目 | statistical_catalog |
| `freshness_sla_monitor_text` | Freshness SLA Monitor | 文字解读 | time、全数据集 | 目录条目 | statistical_catalog |
| `granger_causality_chart` | Granger Causality Test | 图表 | time、数值字段、数值字段 | 目录条目 | statistical_catalog |
| `granger_causality_data` | Granger Causality Test | 结构化数据 | time、数值字段、数值字段 | 目录条目 | statistical_catalog |
| `granger_causality_image_spec` | Granger Causality Test | 图片规格 | time、数值字段、数值字段 | 目录条目 | statistical_catalog |
| `granger_causality_report_section` | Granger Causality Test | 报告段落 | time、数值字段、数值字段 | 目录条目 | statistical_catalog |
| `granger_causality_table` | Granger Causality Test | 表格 | time、数值字段、数值字段 | 目录条目 | statistical_catalog |
| `granger_causality_text` | Granger Causality Test | 文字解读 | time、数值字段、数值字段 | 目录条目 | statistical_catalog |
| `hidden_markov_model_chart` | Hidden Markov Model | 图表 | time、数值字段 | 目录条目 | statistical_catalog |
| `hidden_markov_model_data` | Hidden Markov Model | 结构化数据 | time、数值字段 | 目录条目 | statistical_catalog |
| `hidden_markov_model_image_spec` | Hidden Markov Model | 图片规格 | time、数值字段 | 目录条目 | statistical_catalog |
| `hidden_markov_model_report_section` | Hidden Markov Model | 报告段落 | time、数值字段 | 目录条目 | statistical_catalog |
| `hidden_markov_model_table` | Hidden Markov Model | 表格 | time、数值字段 | 目录条目 | statistical_catalog |
| `hidden_markov_model_text` | Hidden Markov Model | 文字解读 | time、数值字段 | 目录条目 | statistical_catalog |
| `holt_winters_chart` | Holt-Winters | 图表 | time、数值字段 | 目录条目 | statistical_catalog |
| `holt_winters_data` | Holt-Winters | 结构化数据 | time、数值字段 | 目录条目 | statistical_catalog |
| `holt_winters_image_spec` | Holt-Winters | 图片规格 | time、数值字段 | 目录条目 | statistical_catalog |
| `holt_winters_report_section` | Holt-Winters | 报告段落 | time、数值字段 | 目录条目 | statistical_catalog |
| `holt_winters_table` | Holt-Winters | 表格 | time、数值字段 | 目录条目 | statistical_catalog |
| `holt_winters_text` | Holt-Winters | 文字解读 | time、数值字段 | 目录条目 | statistical_catalog |
| `kpss_test_chart` | KPSS Test | 图表 | time、数值字段 | 目录条目 | statistical_catalog |
| `kpss_test_data` | KPSS Test | 结构化数据 | time、数值字段 | 目录条目 | statistical_catalog |
| `kpss_test_image_spec` | KPSS Test | 图片规格 | time、数值字段 | 目录条目 | statistical_catalog |
| `kpss_test_report_section` | KPSS Test | 报告段落 | time、数值字段 | 目录条目 | statistical_catalog |
| `kpss_test_table` | KPSS Test | 表格 | time、数值字段 | 目录条目 | statistical_catalog |
| `kpss_test_text` | KPSS Test | 文字解读 | time、数值字段 | 目录条目 | statistical_catalog |
| `ljung_box_chart` | Ljung-Box Test | 图表 | time、数值字段 | 可运行 | statistical_catalog |
| `ljung_box_data` | Ljung-Box Test | 结构化数据 | time、数值字段 | 可运行 | statistical_catalog |
| `ljung_box_image_spec` | Ljung-Box Test | 图片规格 | time、数值字段 | 可运行 | statistical_catalog |
| `ljung_box_report_section` | Ljung-Box Test | 报告段落 | time、数值字段 | 可运行 | statistical_catalog |
| `ljung_box_table` | Ljung-Box Test | 表格 | time、数值字段 | 可运行 | statistical_catalog |
| `ljung_box_text` | Ljung-Box Test | 文字解读 | time、数值字段 | 可运行 | statistical_catalog |
| `longitudinal_cohort_retention_chart` | Longitudinal Cohort Retention | 图表 | time、分类字段、数值字段 | 目录条目 | statistical_catalog |
| `longitudinal_cohort_retention_data` | Longitudinal Cohort Retention | 结构化数据 | time、分类字段、数值字段 | 目录条目 | statistical_catalog |
| `longitudinal_cohort_retention_image_spec` | Longitudinal Cohort Retention | 图片规格 | time、分类字段、数值字段 | 目录条目 | statistical_catalog |
| `longitudinal_cohort_retention_report_section` | Longitudinal Cohort Retention | 报告段落 | time、分类字段、数值字段 | 目录条目 | statistical_catalog |
| `longitudinal_cohort_retention_table` | Longitudinal Cohort Retention | 表格 | time、分类字段、数值字段 | 目录条目 | statistical_catalog |
| `longitudinal_cohort_retention_text` | Longitudinal Cohort Retention | 文字解读 | time、分类字段、数值字段 | 目录条目 | statistical_catalog |
| `markov_chain_analysis_chart` | Markov Chain Analysis | 图表 | time、分类字段 | 目录条目 | statistical_catalog |
| `markov_chain_analysis_data` | Markov Chain Analysis | 结构化数据 | time、分类字段 | 目录条目 | statistical_catalog |
| `markov_chain_analysis_image_spec` | Markov Chain Analysis | 图片规格 | time、分类字段 | 目录条目 | statistical_catalog |
| `markov_chain_analysis_report_section` | Markov Chain Analysis | 报告段落 | time、分类字段 | 目录条目 | statistical_catalog |
| `markov_chain_analysis_table` | Markov Chain Analysis | 表格 | time、分类字段 | 目录条目 | statistical_catalog |
| `markov_chain_analysis_text` | Markov Chain Analysis | 文字解读 | time、分类字段 | 目录条目 | statistical_catalog |
| `metric_anomaly_root_cause_chart` | Metric Anomaly Root Cause | 图表 | time、数值字段、features | 目录条目 | statistical_catalog |
| `metric_anomaly_root_cause_data` | Metric Anomaly Root Cause | 结构化数据 | time、数值字段、features | 目录条目 | statistical_catalog |
| `metric_anomaly_root_cause_image_spec` | Metric Anomaly Root Cause | 图片规格 | time、数值字段、features | 目录条目 | statistical_catalog |
| `metric_anomaly_root_cause_report_section` | Metric Anomaly Root Cause | 报告段落 | time、数值字段、features | 目录条目 | statistical_catalog |
| `metric_anomaly_root_cause_table` | Metric Anomaly Root Cause | 表格 | time、数值字段、features | 目录条目 | statistical_catalog |
| `metric_anomaly_root_cause_text` | Metric Anomaly Root Cause | 文字解读 | time、数值字段、features | 目录条目 | statistical_catalog |
| `metric_definition_drift_chart` | Metric Definition Drift | 图表 | time、数值字段 | 目录条目 | statistical_catalog |
| `metric_definition_drift_data` | Metric Definition Drift | 结构化数据 | time、数值字段 | 目录条目 | statistical_catalog |
| `metric_definition_drift_image_spec` | Metric Definition Drift | 图片规格 | time、数值字段 | 目录条目 | statistical_catalog |
| `metric_definition_drift_report_section` | Metric Definition Drift | 报告段落 | time、数值字段 | 目录条目 | statistical_catalog |
| `metric_definition_drift_table` | Metric Definition Drift | 表格 | time、数值字段 | 目录条目 | statistical_catalog |
| `metric_definition_drift_text` | Metric Definition Drift | 文字解读 | time、数值字段 | 目录条目 | statistical_catalog |
| `moving_average_chart` | Moving Average | 图表 | time、数值字段 | 可运行 | statistical_catalog |
| `moving_average_data` | Moving Average | 结构化数据 | time、数值字段 | 可运行 | statistical_catalog |
| `moving_average_image_spec` | Moving Average | 图片规格 | time、数值字段 | 可运行 | statistical_catalog |
| `moving_average_report_section` | Moving Average | 报告段落 | time、数值字段 | 可运行 | statistical_catalog |
| `moving_average_table` | Moving Average | 表格 | time、数值字段 | 可运行 | statistical_catalog |
| `moving_average_text` | Moving Average | 文字解读 | time、数值字段 | 可运行 | statistical_catalog |
| `newey_west_standard_errors_chart` | Newey-West Standard Errors | 图表 | time、数值字段、features | 目录条目 | statistical_catalog |
| `newey_west_standard_errors_data` | Newey-West Standard Errors | 结构化数据 | time、数值字段、features | 目录条目 | statistical_catalog |
| `newey_west_standard_errors_image_spec` | Newey-West Standard Errors | 图片规格 | time、数值字段、features | 目录条目 | statistical_catalog |
| `newey_west_standard_errors_report_section` | Newey-West Standard Errors | 报告段落 | time、数值字段、features | 目录条目 | statistical_catalog |
| `newey_west_standard_errors_table` | Newey-West Standard Errors | 表格 | time、数值字段、features | 目录条目 | statistical_catalog |
| `newey_west_standard_errors_text` | Newey-West Standard Errors | 文字解读 | time、数值字段、features | 目录条目 | statistical_catalog |
| `partial_autocorrelation_chart` | Partial Autocorrelation | 图表 | time、数值字段 | 可运行 | statistical_catalog |
| `partial_autocorrelation_data` | Partial Autocorrelation | 结构化数据 | time、数值字段 | 可运行 | statistical_catalog |
| `partial_autocorrelation_image_spec` | Partial Autocorrelation | 图片规格 | time、数值字段 | 可运行 | statistical_catalog |
| `partial_autocorrelation_report_section` | Partial Autocorrelation | 报告段落 | time、数值字段 | 可运行 | statistical_catalog |
| `partial_autocorrelation_table` | Partial Autocorrelation | 表格 | time、数值字段 | 可运行 | statistical_catalog |
| `partial_autocorrelation_text` | Partial Autocorrelation | 文字解读 | time、数值字段 | 可运行 | statistical_catalog |
| `path_sequence_mining_chart` | Path Sequence Mining | 图表 | time、分类字段 | 目录条目 | statistical_catalog |
| `path_sequence_mining_data` | Path Sequence Mining | 结构化数据 | time、分类字段 | 目录条目 | statistical_catalog |
| `path_sequence_mining_image_spec` | Path Sequence Mining | 图片规格 | time、分类字段 | 目录条目 | statistical_catalog |
| `path_sequence_mining_report_section` | Path Sequence Mining | 报告段落 | time、分类字段 | 目录条目 | statistical_catalog |
| `path_sequence_mining_table` | Path Sequence Mining | 表格 | time、分类字段 | 目录条目 | statistical_catalog |
| `path_sequence_mining_text` | Path Sequence Mining | 文字解读 | time、分类字段 | 目录条目 | statistical_catalog |
| `prophet_style_trend_chart` | Prophet-style Trend Model | 图表 | time、数值字段 | 目录条目 | statistical_catalog |
| `prophet_style_trend_data` | Prophet-style Trend Model | 结构化数据 | time、数值字段 | 目录条目 | statistical_catalog |
| `prophet_style_trend_image_spec` | Prophet-style Trend Model | 图片规格 | time、数值字段 | 目录条目 | statistical_catalog |
| `prophet_style_trend_report_section` | Prophet-style Trend Model | 报告段落 | time、数值字段 | 目录条目 | statistical_catalog |
| `prophet_style_trend_table` | Prophet-style Trend Model | 表格 | time、数值字段 | 目录条目 | statistical_catalog |
| `prophet_style_trend_text` | Prophet-style Trend Model | 文字解读 | time、数值字段 | 目录条目 | statistical_catalog |
| `quantile_forecast_chart` | Quantile Forecast | 图表 | time、数值字段 | 目录条目 | statistical_catalog |
| `quantile_forecast_data` | Quantile Forecast | 结构化数据 | time、数值字段 | 目录条目 | statistical_catalog |
| `quantile_forecast_image_spec` | Quantile Forecast | 图片规格 | time、数值字段 | 目录条目 | statistical_catalog |
| `quantile_forecast_report_section` | Quantile Forecast | 报告段落 | time、数值字段 | 目录条目 | statistical_catalog |
| `quantile_forecast_table` | Quantile Forecast | 表格 | time、数值字段 | 目录条目 | statistical_catalog |
| `quantile_forecast_text` | Quantile Forecast | 文字解读 | time、数值字段 | 目录条目 | statistical_catalog |
| `rolling_correlation_chart` | Rolling Correlation | 图表 | time、数值字段、数值字段 | 目录条目 | statistical_catalog |
| `rolling_correlation_data` | Rolling Correlation | 结构化数据 | time、数值字段、数值字段 | 目录条目 | statistical_catalog |
| `rolling_correlation_image_spec` | Rolling Correlation | 图片规格 | time、数值字段、数值字段 | 目录条目 | statistical_catalog |
| `rolling_correlation_report_section` | Rolling Correlation | 报告段落 | time、数值字段、数值字段 | 目录条目 | statistical_catalog |
| `rolling_correlation_table` | Rolling Correlation | 表格 | time、数值字段、数值字段 | 目录条目 | statistical_catalog |
| `rolling_correlation_text` | Rolling Correlation | 文字解读 | time、数值字段、数值字段 | 目录条目 | statistical_catalog |
| `sarima_chart` | SARIMA | 图表 | time、数值字段 | 目录条目 | statistical_catalog |
| `sarima_data` | SARIMA | 结构化数据 | time、数值字段 | 目录条目 | statistical_catalog |
| `sarima_image_spec` | SARIMA | 图片规格 | time、数值字段 | 目录条目 | statistical_catalog |
| `sarima_report_section` | SARIMA | 报告段落 | time、数值字段 | 目录条目 | statistical_catalog |
| `sarima_table` | SARIMA | 表格 | time、数值字段 | 目录条目 | statistical_catalog |
| `sarima_text` | SARIMA | 文字解读 | time、数值字段 | 目录条目 | statistical_catalog |
| `seasonal_baseline_anomaly_chart` | Seasonal Baseline Anomaly | 图表 | time、数值字段 | 目录条目 | statistical_catalog |
| `seasonal_baseline_anomaly_data` | Seasonal Baseline Anomaly | 结构化数据 | time、数值字段 | 目录条目 | statistical_catalog |
| `seasonal_baseline_anomaly_image_spec` | Seasonal Baseline Anomaly | 图片规格 | time、数值字段 | 目录条目 | statistical_catalog |
| `seasonal_baseline_anomaly_report_section` | Seasonal Baseline Anomaly | 报告段落 | time、数值字段 | 目录条目 | statistical_catalog |
| `seasonal_baseline_anomaly_table` | Seasonal Baseline Anomaly | 表格 | time、数值字段 | 目录条目 | statistical_catalog |
| `seasonal_baseline_anomaly_text` | Seasonal Baseline Anomaly | 文字解读 | time、数值字段 | 目录条目 | statistical_catalog |
| `seasonal_decomposition_chart` | Seasonal Decomposition | 图表 | time、数值字段 | 目录条目 | statistical_catalog |
| `seasonal_decomposition_data` | Seasonal Decomposition | 结构化数据 | time、数值字段 | 目录条目 | statistical_catalog |
| `seasonal_decomposition_image_spec` | Seasonal Decomposition | 图片规格 | time、数值字段 | 目录条目 | statistical_catalog |
| `seasonal_decomposition_report_section` | Seasonal Decomposition | 报告段落 | time、数值字段 | 目录条目 | statistical_catalog |
| `seasonal_decomposition_table` | Seasonal Decomposition | 表格 | time、数值字段 | 目录条目 | statistical_catalog |
| `seasonal_decomposition_text` | Seasonal Decomposition | 文字解读 | time、数值字段 | 目录条目 | statistical_catalog |
| `spatiotemporal_cluster_detection_chart` | Spatiotemporal Cluster Detection | 图表 | time、对象级、数值字段 | 目录条目 | statistical_catalog |
| `spatiotemporal_cluster_detection_data` | Spatiotemporal Cluster Detection | 结构化数据 | time、对象级、数值字段 | 目录条目 | statistical_catalog |
| `spatiotemporal_cluster_detection_image_spec` | Spatiotemporal Cluster Detection | 图片规格 | time、对象级、数值字段 | 目录条目 | statistical_catalog |
| `spatiotemporal_cluster_detection_report_section` | Spatiotemporal Cluster Detection | 报告段落 | time、对象级、数值字段 | 目录条目 | statistical_catalog |
| `spatiotemporal_cluster_detection_table` | Spatiotemporal Cluster Detection | 表格 | time、对象级、数值字段 | 目录条目 | statistical_catalog |
| `spatiotemporal_cluster_detection_text` | Spatiotemporal Cluster Detection | 文字解读 | time、对象级、数值字段 | 目录条目 | statistical_catalog |
| `state_transition_matrix_chart` | State Transition Matrix | 图表 | time、分类字段 | 目录条目 | statistical_catalog |
| `state_transition_matrix_data` | State Transition Matrix | 结构化数据 | time、分类字段 | 目录条目 | statistical_catalog |
| `state_transition_matrix_image_spec` | State Transition Matrix | 图片规格 | time、分类字段 | 目录条目 | statistical_catalog |
| `state_transition_matrix_report_section` | State Transition Matrix | 报告段落 | time、分类字段 | 目录条目 | statistical_catalog |
| `state_transition_matrix_table` | State Transition Matrix | 表格 | time、分类字段 | 目录条目 | statistical_catalog |
| `state_transition_matrix_text` | State Transition Matrix | 文字解读 | time、分类字段 | 目录条目 | statistical_catalog |
| `stl_decomposition_chart` | STL Decomposition | 图表 | time、数值字段 | 目录条目 | statistical_catalog |
| `stl_decomposition_data` | STL Decomposition | 结构化数据 | time、数值字段 | 目录条目 | statistical_catalog |
| `stl_decomposition_image_spec` | STL Decomposition | 图片规格 | time、数值字段 | 目录条目 | statistical_catalog |
| `stl_decomposition_report_section` | STL Decomposition | 报告段落 | time、数值字段 | 目录条目 | statistical_catalog |
| `stl_decomposition_table` | STL Decomposition | 表格 | time、数值字段 | 目录条目 | statistical_catalog |
| `stl_decomposition_text` | STL Decomposition | 文字解读 | time、数值字段 | 目录条目 | statistical_catalog |
| `time_series_calendar` | 日历 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `time_series_change_point` | 拐点 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `time_series_forecast` | 预测 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `time_series_lag` | 滞后 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `time_series_seasonality` | 季节性 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `time_series_trend` | 趋势 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |

### 机器学习（120 张；可运行 9 张）

| 卡片 ID | 方法概念 | 输出形态 | 字段角色 | 状态 | 来源 |
| --- | --- | --- | --- | --- | --- |
| `anomaly_detection_isolation_forest_data` | Isolation Forest Anomaly Detection | 结构化数据 | 字段组 | 目录条目 | statistical_catalog |
| `anomaly_detection_isolation_forest_table` | Isolation Forest Anomaly Detection | 表格 | 字段组 | 目录条目 | statistical_catalog |
| `anomaly_detection_isolation_forest_text` | Isolation Forest Anomaly Detection | 文字解读 | 字段组 | 目录条目 | statistical_catalog |
| `anomaly_detection_local_outlier_factor_data` | Local Outlier Factor | 结构化数据 | 字段组 | 目录条目 | statistical_catalog |
| `anomaly_detection_local_outlier_factor_table` | Local Outlier Factor | 表格 | 字段组 | 目录条目 | statistical_catalog |
| `anomaly_detection_local_outlier_factor_text` | Local Outlier Factor | 文字解读 | 字段组 | 目录条目 | statistical_catalog |
| `champion_challenger_evaluation_data` | Champion / Challenger Evaluation | 结构化数据 | target、features | 目录条目 | statistical_catalog |
| `champion_challenger_evaluation_table` | Champion / Challenger Evaluation | 表格 | target、features | 目录条目 | statistical_catalog |
| `champion_challenger_evaluation_text` | Champion / Challenger Evaluation | 文字解读 | target、features | 目录条目 | statistical_catalog |
| `concept_drift_detection_data` | Concept Drift Detection | 结构化数据 | target、features、时间窗口 | 目录条目 | statistical_catalog |
| `concept_drift_detection_table` | Concept Drift Detection | 表格 | target、features、时间窗口 | 目录条目 | statistical_catalog |
| `concept_drift_detection_text` | Concept Drift Detection | 文字解读 | target、features、时间窗口 | 目录条目 | statistical_catalog |
| `conformal_prediction_data` | Conformal Prediction | 结构化数据 | target、features | 目录条目 | statistical_catalog |
| `conformal_prediction_table` | Conformal Prediction | 表格 | target、features | 目录条目 | statistical_catalog |
| `conformal_prediction_text` | Conformal Prediction | 文字解读 | target、features | 目录条目 | statistical_catalog |
| `confusion_matrix_review_chart` | Confusion Matrix Review | 图表 | binary、features | 目录条目 | statistical_catalog |
| `confusion_matrix_review_data` | Confusion Matrix Review | 结构化数据 | binary、features | 目录条目 | statistical_catalog |
| `confusion_matrix_review_image_spec` | Confusion Matrix Review | 图片规格 | binary、features | 目录条目 | statistical_catalog |
| `confusion_matrix_review_report_section` | Confusion Matrix Review | 报告段落 | binary、features | 目录条目 | statistical_catalog |
| `confusion_matrix_review_table` | Confusion Matrix Review | 表格 | binary、features | 目录条目 | statistical_catalog |
| `confusion_matrix_review_text` | Confusion Matrix Review | 文字解读 | binary、features | 目录条目 | statistical_catalog |
| `cost_sensitive_evaluation_data` | Cost-sensitive Evaluation | 结构化数据 | target、features | 目录条目 | statistical_catalog |
| `cost_sensitive_evaluation_table` | Cost-sensitive Evaluation | 表格 | target、features | 目录条目 | statistical_catalog |
| `cost_sensitive_evaluation_text` | Cost-sensitive Evaluation | 文字解读 | target、features | 目录条目 | statistical_catalog |
| `cross_validation_data` | Cross-validation | 结构化数据 | target、features | 目录条目 | statistical_catalog |
| `cross_validation_table` | Cross-validation | 表格 | target、features | 目录条目 | statistical_catalog |
| `cross_validation_text` | Cross-validation | 文字解读 | target、features | 目录条目 | statistical_catalog |
| `data_drift_dashboard_data` | Data Drift Dashboard | 结构化数据 | 字段组、时间窗口 | 目录条目 | statistical_catalog |
| `data_drift_dashboard_table` | Data Drift Dashboard | 表格 | 字段组、时间窗口 | 目录条目 | statistical_catalog |
| `data_drift_dashboard_text` | Data Drift Dashboard | 文字解读 | 字段组、时间窗口 | 目录条目 | statistical_catalog |
| `data_leakage_audit_data` | Data Leakage Audit | 结构化数据 | target、features | 目录条目 | statistical_catalog |
| `data_leakage_audit_table` | Data Leakage Audit | 表格 | target、features | 目录条目 | statistical_catalog |
| `data_leakage_audit_text` | Data Leakage Audit | 文字解读 | target、features | 目录条目 | statistical_catalog |
| `deep_learning_data` | Deep Learning Network | 结构化数据 | numeric or binary、multi numeric | 可运行 | statistical_catalog |
| `deep_learning_table` | Deep Learning Network | 表格 | numeric or binary、multi numeric | 可运行 | statistical_catalog |
| `deep_learning_text` | Deep Learning Network | 文字解读 | numeric or binary、multi numeric | 可运行 | statistical_catalog |
| `fairness_proxy_variable_audit_data` | Fairness Proxy Variable Audit | 结构化数据 | target、features、分组 | 目录条目 | statistical_catalog |
| `fairness_proxy_variable_audit_table` | Fairness Proxy Variable Audit | 表格 | target、features、分组 | 目录条目 | statistical_catalog |
| `fairness_proxy_variable_audit_text` | Fairness Proxy Variable Audit | 文字解读 | target、features、分组 | 目录条目 | statistical_catalog |
| `fairness_slice_audit_data` | Fairness Slice Audit | 结构化数据 | target、features、分组 | 目录条目 | statistical_catalog |
| `fairness_slice_audit_table` | Fairness Slice Audit | 表格 | target、features、分组 | 目录条目 | statistical_catalog |
| `fairness_slice_audit_text` | Fairness Slice Audit | 文字解读 | target、features、分组 | 目录条目 | statistical_catalog |
| `feature_privacy_risk_rank_data` | Feature Privacy Risk Rank | 结构化数据 | features | 目录条目 | statistical_catalog |
| `feature_privacy_risk_rank_table` | Feature Privacy Risk Rank | 表格 | features | 目录条目 | statistical_catalog |
| `feature_privacy_risk_rank_text` | Feature Privacy Risk Rank | 文字解读 | features | 目录条目 | statistical_catalog |
| `graph_anomaly_detection_data` | Graph Anomaly Detection | 结构化数据 | 对象级 | 目录条目 | statistical_catalog |
| `graph_anomaly_detection_table` | Graph Anomaly Detection | 表格 | 对象级 | 目录条目 | statistical_catalog |
| `graph_anomaly_detection_text` | Graph Anomaly Detection | 文字解读 | 对象级 | 目录条目 | statistical_catalog |
| `learning_curve_chart` | Learning Curve | 图表 | target、features | 目录条目 | statistical_catalog |
| `learning_curve_data` | Learning Curve | 结构化数据 | target、features | 目录条目 | statistical_catalog |
| `learning_curve_image_spec` | Learning Curve | 图片规格 | target、features | 目录条目 | statistical_catalog |
| `learning_curve_report_section` | Learning Curve | 报告段落 | target、features | 目录条目 | statistical_catalog |
| `learning_curve_table` | Learning Curve | 表格 | target、features | 目录条目 | statistical_catalog |
| `learning_curve_text` | Learning Curve | 文字解读 | target、features | 目录条目 | statistical_catalog |
| `link_prediction_baseline_data` | Link Prediction Baseline | 结构化数据 | 对象级 | 目录条目 | statistical_catalog |
| `link_prediction_baseline_table` | Link Prediction Baseline | 表格 | 对象级 | 目录条目 | statistical_catalog |
| `link_prediction_baseline_text` | Link Prediction Baseline | 文字解读 | 对象级 | 目录条目 | statistical_catalog |
| `machine_learning_boosting` | 提升模型 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `machine_learning_forest` | 随机森林 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `machine_learning_importance` | 重要性 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `machine_learning_neighbors` | 近邻 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `machine_learning_neural` | 神经网络 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `machine_learning_tree` | 决策树 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | auto_analysis_specs |
| `model_calibration_data` | Model Calibration | 结构化数据 | binary、features | 目录条目 | statistical_catalog |
| `model_calibration_table` | Model Calibration | 表格 | binary、features | 目录条目 | statistical_catalog |
| `model_calibration_text` | Model Calibration | 文字解读 | binary、features | 目录条目 | statistical_catalog |
| `model_card_documentation_data` | Model Card Documentation | 结构化数据 | target、features | 目录条目 | statistical_catalog |
| `model_card_documentation_table` | Model Card Documentation | 表格 | target、features | 目录条目 | statistical_catalog |
| `model_card_documentation_text` | Model Card Documentation | 文字解读 | target、features | 目录条目 | statistical_catalog |
| `model_performance_monitor_data` | Model Performance Monitor | 结构化数据 | target、features、时间窗口 | 目录条目 | statistical_catalog |
| `model_performance_monitor_table` | Model Performance Monitor | 表格 | target、features、时间窗口 | 目录条目 | statistical_catalog |
| `model_performance_monitor_text` | Model Performance Monitor | 文字解读 | target、features、时间窗口 | 目录条目 | statistical_catalog |
| `model_retraining_trigger_data` | Model Retraining Trigger | 结构化数据 | target、features、时间窗口 | 目录条目 | statistical_catalog |
| `model_retraining_trigger_table` | Model Retraining Trigger | 表格 | target、features、时间窗口 | 目录条目 | statistical_catalog |
| `model_retraining_trigger_text` | Model Retraining Trigger | 文字解读 | target、features、时间窗口 | 目录条目 | statistical_catalog |
| `nested_cross_validation_data` | Nested Cross-validation | 结构化数据 | target、features | 目录条目 | statistical_catalog |
| `nested_cross_validation_table` | Nested Cross-validation | 表格 | target、features | 目录条目 | statistical_catalog |
| `nested_cross_validation_text` | Nested Cross-validation | 文字解读 | target、features | 目录条目 | statistical_catalog |
| `neural_network_data` | Neural Network | 结构化数据 | numeric or binary、multi numeric | 可运行 | statistical_catalog |
| `neural_network_table` | Neural Network | 表格 | numeric or binary、multi numeric | 可运行 | statistical_catalog |
| `neural_network_text` | Neural Network | 文字解读 | numeric or binary、multi numeric | 可运行 | statistical_catalog |
| `one_hot_encoding_plan_data` | One-hot Encoding Plan | 结构化数据 | features | 目录条目 | statistical_catalog |
| `one_hot_encoding_plan_table` | One-hot Encoding Plan | 表格 | features | 目录条目 | statistical_catalog |
| `one_hot_encoding_plan_text` | One-hot Encoding Plan | 文字解读 | features | 目录条目 | statistical_catalog |
| `online_offline_metric_gap_data` | Online / Offline Metric Gap | 结构化数据 | target、features、时间窗口 | 目录条目 | statistical_catalog |
| `online_offline_metric_gap_table` | Online / Offline Metric Gap | 表格 | target、features、时间窗口 | 目录条目 | statistical_catalog |
| `online_offline_metric_gap_text` | Online / Offline Metric Gap | 文字解读 | target、features、时间窗口 | 目录条目 | statistical_catalog |
| `permutation_importance_review_data` | Permutation Importance Review | 结构化数据 | target、features | 目录条目 | statistical_catalog |
| `permutation_importance_review_table` | Permutation Importance Review | 表格 | target、features | 目录条目 | statistical_catalog |
| `permutation_importance_review_text` | Permutation Importance Review | 文字解读 | target、features | 目录条目 | statistical_catalog |
| `population_stability_index_data` | Population Stability Index | 结构化数据 | 字段组、时间窗口 | 目录条目 | statistical_catalog |
| `population_stability_index_table` | Population Stability Index | 表格 | 字段组、时间窗口 | 目录条目 | statistical_catalog |
| `population_stability_index_text` | Population Stability Index | 文字解读 | 字段组、时间窗口 | 目录条目 | statistical_catalog |
| `precision_recall_analysis_data` | Precision / Recall Analysis | 结构化数据 | binary、features | 目录条目 | statistical_catalog |
| `precision_recall_analysis_table` | Precision / Recall Analysis | 表格 | binary、features | 目录条目 | statistical_catalog |
| `precision_recall_analysis_text` | Precision / Recall Analysis | 文字解读 | binary、features | 目录条目 | statistical_catalog |
| `random_forest_data` | Random Forest | 结构化数据 | numeric or binary、multi numeric | 可运行 | statistical_catalog |
| `random_forest_table` | Random Forest | 表格 | numeric or binary、multi numeric | 可运行 | statistical_catalog |
| `random_forest_text` | Random Forest | 文字解读 | numeric or binary、multi numeric | 可运行 | statistical_catalog |
| `roc_auc_analysis_data` | ROC AUC Analysis | 结构化数据 | binary、features | 目录条目 | statistical_catalog |
| `roc_auc_analysis_table` | ROC AUC Analysis | 表格 | binary、features | 目录条目 | statistical_catalog |
| `roc_auc_analysis_text` | ROC AUC Analysis | 文字解读 | binary、features | 目录条目 | statistical_catalog |
| `sentiment_classifier_audit_data` | Sentiment Classifier Audit | 结构化数据 | target、features | 目录条目 | statistical_catalog |
| `sentiment_classifier_audit_table` | Sentiment Classifier Audit | 表格 | target、features | 目录条目 | statistical_catalog |
| `sentiment_classifier_audit_text` | Sentiment Classifier Audit | 文字解读 | target、features | 目录条目 | statistical_catalog |
| `shap_explanation_data` | SHAP Explanation | 结构化数据 | target、features | 目录条目 | statistical_catalog |
| `shap_explanation_table` | SHAP Explanation | 表格 | target、features | 目录条目 | statistical_catalog |
| `shap_explanation_text` | SHAP Explanation | 文字解读 | target、features | 目录条目 | statistical_catalog |
| `target_encoding_audit_data` | Target Encoding Audit | 结构化数据 | target、features | 目录条目 | statistical_catalog |
| `target_encoding_audit_table` | Target Encoding Audit | 表格 | target、features | 目录条目 | statistical_catalog |
| `target_encoding_audit_text` | Target Encoding Audit | 文字解读 | target、features | 目录条目 | statistical_catalog |
| `text_label_quality_audit_data` | Text Label Quality Audit | 结构化数据 | target、features | 目录条目 | statistical_catalog |
| `text_label_quality_audit_table` | Text Label Quality Audit | 表格 | target、features | 目录条目 | statistical_catalog |
| `text_label_quality_audit_text` | Text Label Quality Audit | 文字解读 | target、features | 目录条目 | statistical_catalog |
| `threshold_optimization_data` | Decision Threshold Optimization | 结构化数据 | binary、features | 目录条目 | statistical_catalog |
| `threshold_optimization_table` | Decision Threshold Optimization | 表格 | binary、features | 目录条目 | statistical_catalog |
| `threshold_optimization_text` | Decision Threshold Optimization | 文字解读 | binary、features | 目录条目 | statistical_catalog |
| `train_test_split_audit_data` | Train / Test Split Audit | 结构化数据 | target、features | 目录条目 | statistical_catalog |
| `train_test_split_audit_table` | Train / Test Split Audit | 表格 | target、features | 目录条目 | statistical_catalog |
| `train_test_split_audit_text` | Train / Test Split Audit | 文字解读 | target、features | 目录条目 | statistical_catalog |

### 生存分析（78 张；可运行 0 张）

| 卡片 ID | 方法概念 | 输出形态 | 字段角色 | 状态 | 来源 |
| --- | --- | --- | --- | --- | --- |
| `accelerated_failure_time_chart` | Accelerated Failure Time Model | 图表 | time to event、features | 目录条目 | statistical_catalog |
| `accelerated_failure_time_data` | Accelerated Failure Time Model | 结构化数据 | time to event、features | 目录条目 | statistical_catalog |
| `accelerated_failure_time_image_spec` | Accelerated Failure Time Model | 图片规格 | time to event、features | 目录条目 | statistical_catalog |
| `accelerated_failure_time_report_section` | Accelerated Failure Time Model | 报告段落 | time to event、features | 目录条目 | statistical_catalog |
| `accelerated_failure_time_table` | Accelerated Failure Time Model | 表格 | time to event、features | 目录条目 | statistical_catalog |
| `accelerated_failure_time_text` | Accelerated Failure Time Model | 文字解读 | time to event、features | 目录条目 | statistical_catalog |
| `competing_event_retention_chart` | Competing Event Retention | 图表 | time to event、event type | 目录条目 | statistical_catalog |
| `competing_event_retention_data` | Competing Event Retention | 结构化数据 | time to event、event type | 目录条目 | statistical_catalog |
| `competing_event_retention_image_spec` | Competing Event Retention | 图片规格 | time to event、event type | 目录条目 | statistical_catalog |
| `competing_event_retention_report_section` | Competing Event Retention | 报告段落 | time to event、event type | 目录条目 | statistical_catalog |
| `competing_event_retention_table` | Competing Event Retention | 表格 | time to event、event type | 目录条目 | statistical_catalog |
| `competing_event_retention_text` | Competing Event Retention | 文字解读 | time to event、event type | 目录条目 | statistical_catalog |
| `competing_risks_chart` | Competing Risks Model | 图表 | time to event、event type | 目录条目 | statistical_catalog |
| `competing_risks_data` | Competing Risks Model | 结构化数据 | time to event、event type | 目录条目 | statistical_catalog |
| `competing_risks_image_spec` | Competing Risks Model | 图片规格 | time to event、event type | 目录条目 | statistical_catalog |
| `competing_risks_report_section` | Competing Risks Model | 报告段落 | time to event、event type | 目录条目 | statistical_catalog |
| `competing_risks_table` | Competing Risks Model | 表格 | time to event、event type | 目录条目 | statistical_catalog |
| `competing_risks_text` | Competing Risks Model | 文字解读 | time to event、event type | 目录条目 | statistical_catalog |
| `cox_ph_chart` | Cox Proportional Hazards | 图表 | time to event、features | 目录条目 | statistical_catalog |
| `cox_ph_data` | Cox Proportional Hazards | 结构化数据 | time to event、features | 目录条目 | statistical_catalog |
| `cox_ph_image_spec` | Cox Proportional Hazards | 图片规格 | time to event、features | 目录条目 | statistical_catalog |
| `cox_ph_report_section` | Cox Proportional Hazards | 报告段落 | time to event、features | 目录条目 | statistical_catalog |
| `cox_ph_table` | Cox Proportional Hazards | 表格 | time to event、features | 目录条目 | statistical_catalog |
| `cox_ph_text` | Cox Proportional Hazards | 文字解读 | time to event、features | 目录条目 | statistical_catalog |
| `cumulative_incidence_curve_chart` | Cumulative Incidence Curve | 图表 | time to event、event type | 目录条目 | statistical_catalog |
| `cumulative_incidence_curve_data` | Cumulative Incidence Curve | 结构化数据 | time to event、event type | 目录条目 | statistical_catalog |
| `cumulative_incidence_curve_image_spec` | Cumulative Incidence Curve | 图片规格 | time to event、event type | 目录条目 | statistical_catalog |
| `cumulative_incidence_curve_report_section` | Cumulative Incidence Curve | 报告段落 | time to event、event type | 目录条目 | statistical_catalog |
| `cumulative_incidence_curve_table` | Cumulative Incidence Curve | 表格 | time to event、event type | 目录条目 | statistical_catalog |
| `cumulative_incidence_curve_text` | Cumulative Incidence Curve | 文字解读 | time to event、event type | 目录条目 | statistical_catalog |
| `kaplan_meier_chart` | Kaplan-Meier Estimator | 图表 | time to event | 目录条目 | statistical_catalog |
| `kaplan_meier_data` | Kaplan-Meier Estimator | 结构化数据 | time to event | 目录条目 | statistical_catalog |
| `kaplan_meier_image_spec` | Kaplan-Meier Estimator | 图片规格 | time to event | 目录条目 | statistical_catalog |
| `kaplan_meier_report_section` | Kaplan-Meier Estimator | 报告段落 | time to event | 目录条目 | statistical_catalog |
| `kaplan_meier_table` | Kaplan-Meier Estimator | 表格 | time to event | 目录条目 | statistical_catalog |
| `kaplan_meier_text` | Kaplan-Meier Estimator | 文字解读 | time to event | 目录条目 | statistical_catalog |
| `log_rank_test_chart` | Log-rank Test | 图表 | time to event、group | 目录条目 | statistical_catalog |
| `log_rank_test_data` | Log-rank Test | 结构化数据 | time to event、group | 目录条目 | statistical_catalog |
| `log_rank_test_image_spec` | Log-rank Test | 图片规格 | time to event、group | 目录条目 | statistical_catalog |
| `log_rank_test_report_section` | Log-rank Test | 报告段落 | time to event、group | 目录条目 | statistical_catalog |
| `log_rank_test_table` | Log-rank Test | 表格 | time to event、group | 目录条目 | statistical_catalog |
| `log_rank_test_text` | Log-rank Test | 文字解读 | time to event、group | 目录条目 | statistical_catalog |
| `multi_state_survival_model_chart` | Multi-state Survival Model | 图表 | time to event、event type | 目录条目 | statistical_catalog |
| `multi_state_survival_model_data` | Multi-state Survival Model | 结构化数据 | time to event、event type | 目录条目 | statistical_catalog |
| `multi_state_survival_model_image_spec` | Multi-state Survival Model | 图片规格 | time to event、event type | 目录条目 | statistical_catalog |
| `multi_state_survival_model_report_section` | Multi-state Survival Model | 报告段落 | time to event、event type | 目录条目 | statistical_catalog |
| `multi_state_survival_model_table` | Multi-state Survival Model | 表格 | time to event、event type | 目录条目 | statistical_catalog |
| `multi_state_survival_model_text` | Multi-state Survival Model | 文字解读 | time to event、event type | 目录条目 | statistical_catalog |
| `nelson_aalen_chart` | Nelson-Aalen Estimator | 图表 | time to event | 目录条目 | statistical_catalog |
| `nelson_aalen_data` | Nelson-Aalen Estimator | 结构化数据 | time to event | 目录条目 | statistical_catalog |
| `nelson_aalen_image_spec` | Nelson-Aalen Estimator | 图片规格 | time to event | 目录条目 | statistical_catalog |
| `nelson_aalen_report_section` | Nelson-Aalen Estimator | 报告段落 | time to event | 目录条目 | statistical_catalog |
| `nelson_aalen_table` | Nelson-Aalen Estimator | 表格 | time to event | 目录条目 | statistical_catalog |
| `nelson_aalen_text` | Nelson-Aalen Estimator | 文字解读 | time to event | 目录条目 | statistical_catalog |
| `proportional_hazards_check_chart` | Proportional Hazards Check | 图表 | time to event、features | 目录条目 | statistical_catalog |
| `proportional_hazards_check_data` | Proportional Hazards Check | 结构化数据 | time to event、features | 目录条目 | statistical_catalog |
| `proportional_hazards_check_image_spec` | Proportional Hazards Check | 图片规格 | time to event、features | 目录条目 | statistical_catalog |
| `proportional_hazards_check_report_section` | Proportional Hazards Check | 报告段落 | time to event、features | 目录条目 | statistical_catalog |
| `proportional_hazards_check_table` | Proportional Hazards Check | 表格 | time to event、features | 目录条目 | statistical_catalog |
| `proportional_hazards_check_text` | Proportional Hazards Check | 文字解读 | time to event、features | 目录条目 | statistical_catalog |
| `survival_censoring_audit_chart` | Survival Censoring Audit | 图表 | time to event、group | 目录条目 | statistical_catalog |
| `survival_censoring_audit_data` | Survival Censoring Audit | 结构化数据 | time to event、group | 目录条目 | statistical_catalog |
| `survival_censoring_audit_image_spec` | Survival Censoring Audit | 图片规格 | time to event、group | 目录条目 | statistical_catalog |
| `survival_censoring_audit_report_section` | Survival Censoring Audit | 报告段落 | time to event、group | 目录条目 | statistical_catalog |
| `survival_censoring_audit_table` | Survival Censoring Audit | 表格 | time to event、group | 目录条目 | statistical_catalog |
| `survival_censoring_audit_text` | Survival Censoring Audit | 文字解读 | time to event、group | 目录条目 | statistical_catalog |
| `survival_retention_model_chart` | Survival Retention Model | 图表 | time to event、features | 目录条目 | statistical_catalog |
| `survival_retention_model_data` | Survival Retention Model | 结构化数据 | time to event、features | 目录条目 | statistical_catalog |
| `survival_retention_model_image_spec` | Survival Retention Model | 图片规格 | time to event、features | 目录条目 | statistical_catalog |
| `survival_retention_model_report_section` | Survival Retention Model | 报告段落 | time to event、features | 目录条目 | statistical_catalog |
| `survival_retention_model_table` | Survival Retention Model | 表格 | time to event、features | 目录条目 | statistical_catalog |
| `survival_retention_model_text` | Survival Retention Model | 文字解读 | time to event、features | 目录条目 | statistical_catalog |
| `time_dependent_covariates_chart` | Time-dependent Covariates | 图表 | time to event、features | 目录条目 | statistical_catalog |
| `time_dependent_covariates_data` | Time-dependent Covariates | 结构化数据 | time to event、features | 目录条目 | statistical_catalog |
| `time_dependent_covariates_image_spec` | Time-dependent Covariates | 图片规格 | time to event、features | 目录条目 | statistical_catalog |
| `time_dependent_covariates_report_section` | Time-dependent Covariates | 报告段落 | time to event、features | 目录条目 | statistical_catalog |
| `time_dependent_covariates_table` | Time-dependent Covariates | 表格 | time to event、features | 目录条目 | statistical_catalog |
| `time_dependent_covariates_text` | Time-dependent Covariates | 文字解读 | time to event、features | 目录条目 | statistical_catalog |

### 统计方法（54 张；可运行 0 张）

| 卡片 ID | 方法概念 | 输出形态 | 字段角色 | 状态 | 来源 |
| --- | --- | --- | --- | --- | --- |
| `analysis_lineage_map_data` | Analysis Lineage Map | 结构化数据 | 全数据集 | 目录条目 | statistical_catalog |
| `analysis_lineage_map_table` | Analysis Lineage Map | 表格 | 全数据集 | 目录条目 | statistical_catalog |
| `analysis_lineage_map_text` | Analysis Lineage Map | 文字解读 | 全数据集 | 目录条目 | statistical_catalog |
| `bayes_factor_model_comparison_data` | Bayes Factor Model Comparison | 结构化数据 | target、features | 目录条目 | statistical_catalog |
| `bayes_factor_model_comparison_table` | Bayes Factor Model Comparison | 表格 | target、features | 目录条目 | statistical_catalog |
| `bayes_factor_model_comparison_text` | Bayes Factor Model Comparison | 文字解读 | target、features | 目录条目 | statistical_catalog |
| `bayesian_credible_effect_data` | Bayesian Credible Effect | 结构化数据 | target、features | 目录条目 | statistical_catalog |
| `bayesian_credible_effect_table` | Bayesian Credible Effect | 表格 | target、features | 目录条目 | statistical_catalog |
| `bayesian_credible_effect_text` | Bayesian Credible Effect | 文字解读 | target、features | 目录条目 | statistical_catalog |
| `bayesian_interval_summary_data` | Bayesian Interval Summary | 结构化数据 | 数值字段 | 目录条目 | statistical_catalog |
| `bayesian_interval_summary_table` | Bayesian Interval Summary | 表格 | 数值字段 | 目录条目 | statistical_catalog |
| `bayesian_interval_summary_text` | Bayesian Interval Summary | 文字解读 | 数值字段 | 目录条目 | statistical_catalog |
| `bayesian_posterior_predictive_check_data` | Bayesian Posterior Predictive Check | 结构化数据 | target、features | 目录条目 | statistical_catalog |
| `bayesian_posterior_predictive_check_table` | Bayesian Posterior Predictive Check | 表格 | target、features | 目录条目 | statistical_catalog |
| `bayesian_posterior_predictive_check_text` | Bayesian Posterior Predictive Check | 文字解读 | target、features | 目录条目 | statistical_catalog |
| `bayesian_prior_predictive_check_data` | Bayesian Prior Predictive Check | 结构化数据 | target、features | 目录条目 | statistical_catalog |
| `bayesian_prior_predictive_check_table` | Bayesian Prior Predictive Check | 表格 | target、features | 目录条目 | statistical_catalog |
| `bayesian_prior_predictive_check_text` | Bayesian Prior Predictive Check | 文字解读 | target、features | 目录条目 | statistical_catalog |
| `confidence_interval_summary_data` | Confidence Interval Summary | 结构化数据 | 数值字段 | 目录条目 | statistical_catalog |
| `confidence_interval_summary_table` | Confidence Interval Summary | 表格 | 数值字段 | 目录条目 | statistical_catalog |
| `confidence_interval_summary_text` | Confidence Interval Summary | 文字解读 | 数值字段 | 目录条目 | statistical_catalog |
| `differential_privacy_budget_data` | Differential Privacy Budget | 结构化数据 | 全数据集 | 目录条目 | statistical_catalog |
| `differential_privacy_budget_table` | Differential Privacy Budget | 表格 | 全数据集 | 目录条目 | statistical_catalog |
| `differential_privacy_budget_text` | Differential Privacy Budget | 文字解读 | 全数据集 | 目录条目 | statistical_catalog |
| `empirical_bayes_shrinkage_data` | Empirical Bayes Shrinkage | 结构化数据 | 数值字段、分组 | 目录条目 | statistical_catalog |
| `empirical_bayes_shrinkage_table` | Empirical Bayes Shrinkage | 表格 | 数值字段、分组 | 目录条目 | statistical_catalog |
| `empirical_bayes_shrinkage_text` | Empirical Bayes Shrinkage | 文字解读 | 数值字段、分组 | 目录条目 | statistical_catalog |
| `false_discovery_rate_data` | False Discovery Rate Control | 结构化数据 | 字段组 | 目录条目 | statistical_catalog |
| `false_discovery_rate_table` | False Discovery Rate Control | 表格 | 字段组 | 目录条目 | statistical_catalog |
| `false_discovery_rate_text` | False Discovery Rate Control | 文字解读 | 字段组 | 目录条目 | statistical_catalog |
| `finite_population_correction_data` | Finite Population Correction | 结构化数据 | 数值字段 | 目录条目 | statistical_catalog |
| `finite_population_correction_table` | Finite Population Correction | 表格 | 数值字段 | 目录条目 | statistical_catalog |
| `finite_population_correction_text` | Finite Population Correction | 文字解读 | 数值字段 | 目录条目 | statistical_catalog |
| `margin_of_error_data` | Margin of Error | 结构化数据 | 数值字段 | 目录条目 | statistical_catalog |
| `margin_of_error_table` | Margin of Error | 表格 | 数值字段 | 目录条目 | statistical_catalog |
| `margin_of_error_text` | Margin of Error | 文字解读 | 数值字段 | 目录条目 | statistical_catalog |
| `multiple_testing_correction_data` | Multiple Testing Correction | 结构化数据 | 字段组 | 目录条目 | statistical_catalog |
| `multiple_testing_correction_table` | Multiple Testing Correction | 表格 | 字段组 | 目录条目 | statistical_catalog |
| `multiple_testing_correction_text` | Multiple Testing Correction | 文字解读 | 字段组 | 目录条目 | statistical_catalog |
| `ratio_metric_delta_method_data` | Ratio Metric Delta Method | 结构化数据 | 字段对 | 目录条目 | statistical_catalog |
| `ratio_metric_delta_method_table` | Ratio Metric Delta Method | 表格 | 字段对 | 目录条目 | statistical_catalog |
| `ratio_metric_delta_method_text` | Ratio Metric Delta Method | 文字解读 | 字段对 | 目录条目 | statistical_catalog |
| `reproducibility_audit_data` | Reproducibility Audit | 结构化数据 | 全数据集 | 目录条目 | statistical_catalog |
| `reproducibility_audit_table` | Reproducibility Audit | 表格 | 全数据集 | 目录条目 | statistical_catalog |
| `reproducibility_audit_text` | Reproducibility Audit | 文字解读 | 全数据集 | 目录条目 | statistical_catalog |
| `robustness_grid_data` | Robustness Grid | 结构化数据 | 字段组 | 目录条目 | statistical_catalog |
| `robustness_grid_table` | Robustness Grid | 表格 | 字段组 | 目录条目 | statistical_catalog |
| `robustness_grid_text` | Robustness Grid | 文字解读 | 字段组 | 目录条目 | statistical_catalog |
| `sensitivity_to_missing_data_data` | Sensitivity to Missing Data | 结构化数据 | 字段组 | 目录条目 | statistical_catalog |
| `sensitivity_to_missing_data_table` | Sensitivity to Missing Data | 表格 | 字段组 | 目录条目 | statistical_catalog |
| `sensitivity_to_missing_data_text` | Sensitivity to Missing Data | 文字解读 | 字段组 | 目录条目 | statistical_catalog |
| `sensitivity_to_outliers_data` | Sensitivity to Outliers | 结构化数据 | 字段组 | 目录条目 | statistical_catalog |
| `sensitivity_to_outliers_table` | Sensitivity to Outliers | 表格 | 字段组 | 目录条目 | statistical_catalog |
| `sensitivity_to_outliers_text` | Sensitivity to Outliers | 文字解读 | 字段组 | 目录条目 | statistical_catalog |

### 非参数检验（42 张；可运行 36 张）

| 卡片 ID | 方法概念 | 输出形态 | 字段角色 | 状态 | 来源 |
| --- | --- | --- | --- | --- | --- |
| `bootstrap_ci_data` | Bootstrap CI | 结构化数据 | 数值字段 | 可运行 | statistical_catalog |
| `bootstrap_ci_table` | Bootstrap CI | 表格 | 数值字段 | 可运行 | statistical_catalog |
| `bootstrap_ci_text` | Bootstrap CI | 文字解读 | 数值字段 | 可运行 | statistical_catalog |
| `cliffs_delta_effect_size_data` | Cliff's Delta Effect Size | 结构化数据 | 数值字段、binary group | 目录条目 | statistical_catalog |
| `cliffs_delta_effect_size_table` | Cliff's Delta Effect Size | 表格 | 数值字段、binary group | 目录条目 | statistical_catalog |
| `cliffs_delta_effect_size_text` | Cliff's Delta Effect Size | 文字解读 | 数值字段、binary group | 目录条目 | statistical_catalog |
| `fligner_killeen_data` | Fligner-Killeen Test | 结构化数据 | 数值字段、分类字段 | 可运行 | statistical_catalog |
| `fligner_killeen_table` | Fligner-Killeen Test | 表格 | 数值字段、分类字段 | 可运行 | statistical_catalog |
| `fligner_killeen_text` | Fligner-Killeen Test | 文字解读 | 数值字段、分类字段 | 可运行 | statistical_catalog |
| `friedman_data` | Friedman Test | 结构化数据 | 数值字段、within subject factor | 可运行 | statistical_catalog |
| `friedman_table` | Friedman Test | 表格 | 数值字段、within subject factor | 可运行 | statistical_catalog |
| `friedman_text` | Friedman Test | 文字解读 | 数值字段、within subject factor | 可运行 | statistical_catalog |
| `kruskal_data` | Kruskal-Wallis Test | 结构化数据 | 数值字段、分类字段 | 可运行 | statistical_catalog |
| `kruskal_table` | Kruskal-Wallis Test | 表格 | 数值字段、分类字段 | 可运行 | statistical_catalog |
| `kruskal_text` | Kruskal-Wallis Test | 文字解读 | 数值字段、分类字段 | 可运行 | statistical_catalog |
| `ks_two_sample_data` | Two-sample KS Test | 结构化数据 | 数值字段、binary group | 可运行 | statistical_catalog |
| `ks_two_sample_table` | Two-sample KS Test | 表格 | 数值字段、binary group | 可运行 | statistical_catalog |
| `ks_two_sample_text` | Two-sample KS Test | 文字解读 | 数值字段、binary group | 可运行 | statistical_catalog |
| `mann_whitney_data` | Mann-Whitney U Test | 结构化数据 | 数值字段、binary group | 可运行 | statistical_catalog |
| `mann_whitney_table` | Mann-Whitney U Test | 表格 | 数值字段、binary group | 可运行 | statistical_catalog |
| `mann_whitney_text` | Mann-Whitney U Test | 文字解读 | 数值字段、binary group | 可运行 | statistical_catalog |
| `median_test_data` | Median Test | 结构化数据 | 数值字段、分类字段 | 可运行 | statistical_catalog |
| `median_test_table` | Median Test | 表格 | 数值字段、分类字段 | 可运行 | statistical_catalog |
| `median_test_text` | Median Test | 文字解读 | 数值字段、分类字段 | 可运行 | statistical_catalog |
| `mood_median_data` | Mood Median Test | 结构化数据 | 数值字段、分类字段 | 可运行 | statistical_catalog |
| `mood_median_table` | Mood Median Test | 表格 | 数值字段、分类字段 | 可运行 | statistical_catalog |
| `mood_median_text` | Mood Median Test | 文字解读 | 数值字段、分类字段 | 可运行 | statistical_catalog |
| `permutation_test_data` | Permutation Test | 结构化数据 | 数值字段、分类字段 | 可运行 | statistical_catalog |
| `permutation_test_table` | Permutation Test | 表格 | 数值字段、分类字段 | 可运行 | statistical_catalog |
| `permutation_test_text` | Permutation Test | 文字解读 | 数值字段、分类字段 | 可运行 | statistical_catalog |
| `rank_biserial_correlation_data` | Rank-biserial Correlation | 结构化数据 | 数值字段、binary group | 目录条目 | statistical_catalog |
| `rank_biserial_correlation_table` | Rank-biserial Correlation | 表格 | 数值字段、binary group | 目录条目 | statistical_catalog |
| `rank_biserial_correlation_text` | Rank-biserial Correlation | 文字解读 | 数值字段、binary group | 目录条目 | statistical_catalog |
| `runs_test_data` | Runs Test | 结构化数据 | ordered | 可运行 | statistical_catalog |
| `runs_test_table` | Runs Test | 表格 | ordered | 可运行 | statistical_catalog |
| `runs_test_text` | Runs Test | 文字解读 | ordered | 可运行 | statistical_catalog |
| `sign_test_data` | Sign Test | 结构化数据 | 数值字段、paired | 可运行 | statistical_catalog |
| `sign_test_table` | Sign Test | 表格 | 数值字段、paired | 可运行 | statistical_catalog |
| `sign_test_text` | Sign Test | 文字解读 | 数值字段、paired | 可运行 | statistical_catalog |
| `wilcoxon_signed_rank_data` | Wilcoxon Signed-rank Test | 结构化数据 | 数值字段、paired | 可运行 | statistical_catalog |
| `wilcoxon_signed_rank_table` | Wilcoxon Signed-rank Test | 表格 | 数值字段、paired | 可运行 | statistical_catalog |
| `wilcoxon_signed_rank_text` | Wilcoxon Signed-rank Test | 文字解读 | 数值字段、paired | 可运行 | statistical_catalog |

### 面板因果（48 张；可运行 0 张）

| 卡片 ID | 方法概念 | 输出形态 | 字段角色 | 状态 | 来源 |
| --- | --- | --- | --- | --- | --- |
| `bayesian_hierarchical_model_data` | Bayesian Hierarchical Model | 结构化数据 | grouped numeric | 目录条目 | statistical_catalog |
| `bayesian_hierarchical_model_table` | Bayesian Hierarchical Model | 表格 | grouped numeric | 目录条目 | statistical_catalog |
| `bayesian_hierarchical_model_text` | Bayesian Hierarchical Model | 文字解读 | grouped numeric | 目录条目 | statistical_catalog |
| `did_data` | Difference-in-Differences | 结构化数据 | time、group、数值字段 | 目录条目 | statistical_catalog |
| `did_table` | Difference-in-Differences | 表格 | time、group、数值字段 | 目录条目 | statistical_catalog |
| `did_text` | Difference-in-Differences | 文字解读 | time、group、数值字段 | 目录条目 | statistical_catalog |
| `event_study_design_chart` | Event Study Design | 图表 | time、group、数值字段 | 目录条目 | statistical_catalog |
| `event_study_design_data` | Event Study Design | 结构化数据 | time、group、数值字段 | 目录条目 | statistical_catalog |
| `event_study_design_image_spec` | Event Study Design | 图片规格 | time、group、数值字段 | 目录条目 | statistical_catalog |
| `event_study_design_report_section` | Event Study Design | 报告段落 | time、group、数值字段 | 目录条目 | statistical_catalog |
| `event_study_design_table` | Event Study Design | 表格 | time、group、数值字段 | 目录条目 | statistical_catalog |
| `event_study_design_text` | Event Study Design | 文字解读 | time、group、数值字段 | 目录条目 | statistical_catalog |
| `gee_data` | Generalized Estimating Equations | 结构化数据 | grouped numeric | 目录条目 | statistical_catalog |
| `gee_table` | Generalized Estimating Equations | 表格 | grouped numeric | 目录条目 | statistical_catalog |
| `gee_text` | Generalized Estimating Equations | 文字解读 | grouped numeric | 目录条目 | statistical_catalog |
| `interrupted_time_series_data` | Interrupted Time Series | 结构化数据 | time、数值字段 | 目录条目 | statistical_catalog |
| `interrupted_time_series_table` | Interrupted Time Series | 表格 | time、数值字段 | 目录条目 | statistical_catalog |
| `interrupted_time_series_text` | Interrupted Time Series | 文字解读 | time、数值字段 | 目录条目 | statistical_catalog |
| `mixed_effects_model_data` | Mixed Effects Model | 结构化数据 | grouped numeric | 目录条目 | statistical_catalog |
| `mixed_effects_model_table` | Mixed Effects Model | 表格 | grouped numeric | 目录条目 | statistical_catalog |
| `mixed_effects_model_text` | Mixed Effects Model | 文字解读 | grouped numeric | 目录条目 | statistical_catalog |
| `mixed_effects_random_intercepts_data` | Mixed Effects Random Intercepts | 结构化数据 | grouped numeric | 目录条目 | statistical_catalog |
| `mixed_effects_random_intercepts_table` | Mixed Effects Random Intercepts | 表格 | grouped numeric | 目录条目 | statistical_catalog |
| `mixed_effects_random_intercepts_text` | Mixed Effects Random Intercepts | 文字解读 | grouped numeric | 目录条目 | statistical_catalog |
| `mixed_effects_random_slopes_data` | Mixed Effects Random Slopes | 结构化数据 | grouped numeric | 目录条目 | statistical_catalog |
| `mixed_effects_random_slopes_table` | Mixed Effects Random Slopes | 表格 | grouped numeric | 目录条目 | statistical_catalog |
| `mixed_effects_random_slopes_text` | Mixed Effects Random Slopes | 文字解读 | grouped numeric | 目录条目 | statistical_catalog |
| `multilevel_poststratification_data` | Multilevel Regression and Poststratification | 结构化数据 | grouped numeric | 目录条目 | statistical_catalog |
| `multilevel_poststratification_table` | Multilevel Regression and Poststratification | 表格 | grouped numeric | 目录条目 | statistical_catalog |
| `multilevel_poststratification_text` | Multilevel Regression and Poststratification | 文字解读 | grouped numeric | 目录条目 | statistical_catalog |
| `panel_fixed_effects_data` | Panel Fixed Effects | 结构化数据 | panel、数值字段 | 目录条目 | statistical_catalog |
| `panel_fixed_effects_table` | Panel Fixed Effects | 表格 | panel、数值字段 | 目录条目 | statistical_catalog |
| `panel_fixed_effects_text` | Panel Fixed Effects | 文字解读 | panel、数值字段 | 目录条目 | statistical_catalog |
| `panel_random_effects_data` | Panel Random Effects | 结构化数据 | panel、数值字段 | 目录条目 | statistical_catalog |
| `panel_random_effects_table` | Panel Random Effects | 表格 | panel、数值字段 | 目录条目 | statistical_catalog |
| `panel_random_effects_text` | Panel Random Effects | 文字解读 | panel、数值字段 | 目录条目 | statistical_catalog |
| `parallel_trends_diagnostic_chart` | Parallel Trends Diagnostic | 图表 | time、group、数值字段 | 目录条目 | statistical_catalog |
| `parallel_trends_diagnostic_data` | Parallel Trends Diagnostic | 结构化数据 | time、group、数值字段 | 目录条目 | statistical_catalog |
| `parallel_trends_diagnostic_image_spec` | Parallel Trends Diagnostic | 图片规格 | time、group、数值字段 | 目录条目 | statistical_catalog |
| `parallel_trends_diagnostic_report_section` | Parallel Trends Diagnostic | 报告段落 | time、group、数值字段 | 目录条目 | statistical_catalog |
| `parallel_trends_diagnostic_table` | Parallel Trends Diagnostic | 表格 | time、group、数值字段 | 目录条目 | statistical_catalog |
| `parallel_trends_diagnostic_text` | Parallel Trends Diagnostic | 文字解读 | time、group、数值字段 | 目录条目 | statistical_catalog |
| `synthetic_control_data` | Synthetic Control | 结构化数据 | time、panel | 目录条目 | statistical_catalog |
| `synthetic_control_table` | Synthetic Control | 表格 | time、panel | 目录条目 | statistical_catalog |
| `synthetic_control_text` | Synthetic Control | 文字解读 | time、panel | 目录条目 | statistical_catalog |
| `synthetic_difference_in_differences_data` | Synthetic Difference-in-Differences | 结构化数据 | time、panel | 目录条目 | statistical_catalog |
| `synthetic_difference_in_differences_table` | Synthetic Difference-in-Differences | 表格 | time、panel | 目录条目 | statistical_catalog |
| `synthetic_difference_in_differences_text` | Synthetic Difference-in-Differences | 文字解读 | time、panel | 目录条目 | statistical_catalog |
