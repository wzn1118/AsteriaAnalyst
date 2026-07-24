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

### 分析方法（注册族：`关联分析`；56 张；可运行 27 张）

| 卡片 ID | 中文方法名称 | 原始英文概念 | 中文输出形式 | 字段角色 | 状态 | 来源 |
| --- | --- | --- | --- | --- | --- | --- |
| `association_correlation` | 关联分析・相关性 | 相关性 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `association_distance` | 关联分析・距离 | 距离 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `association_mutual_information` | 关联分析・分析方法 | 互信息 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `association_network` | 关联分析・网络 | 关系网络 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `association_partial` | 关联分析・偏相关 | 偏相关 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `canonical_correlation_data` | 典型相关分析 | Canonical Correlation | 结构化数据 | multi numeric、multi numeric | 目录条目 | 统计目录 |
| `canonical_correlation_table` | 典型相关分析 | Canonical Correlation | 表格 | multi numeric、multi numeric | 目录条目 | 统计目录 |
| `canonical_correlation_text` | 典型相关分析 | Canonical Correlation | 文字解读 | multi numeric、multi numeric | 目录条目 | 统计目录 |
| `cooccurrence_network_analysis_data` | 共现网络分析 | Co-occurrence Network Analysis | 结构化数据 | 字段组 | 目录条目 | 统计目录 |
| `cooccurrence_network_analysis_table` | 共现网络分析 | Co-occurrence Network Analysis | 表格 | 字段组 | 目录条目 | 统计目录 |
| `cooccurrence_network_analysis_text` | 共现网络分析 | Co-occurrence Network Analysis | 文字解读 | 字段组 | 目录条目 | 统计目录 |
| `correlation_chart` | 相关矩阵分析 | Correlation Matrix | 图表 | multi numeric | 可运行 | 统计目录 |
| `correlation_data` | 相关矩阵分析 | Correlation Matrix | 结构化数据 | multi numeric | 可运行 | 统计目录 |
| `correlation_image_spec` | 相关矩阵分析 | Correlation Matrix | 图片规格 | multi numeric | 可运行 | 统计目录 |
| `correlation_report_section` | 相关矩阵分析 | Correlation Matrix | 报告段落 | multi numeric | 可运行 | 统计目录 |
| `correlation_table` | 相关矩阵分析 | Correlation Matrix | 表格 | multi numeric | 可运行 | 统计目录 |
| `correlation_text` | 相关矩阵分析 | Correlation Matrix | 文字解读 | multi numeric | 可运行 | 统计目录 |
| `distance_correlation_data` | 距离相关分析 | Distance Correlation | 结构化数据 | 数值字段、数值字段 | 可运行 | 统计目录 |
| `distance_correlation_table` | 距离相关分析 | Distance Correlation | 表格 | 数值字段、数值字段 | 可运行 | 统计目录 |
| `distance_correlation_text` | 距离相关分析 | Distance Correlation | 文字解读 | 数值字段、数值字段 | 可运行 | 统计目录 |
| `eta_squared_data` | Eta 平方效应量 | Eta Squared | 结构化数据 | 分类字段、数值字段 | 可运行 | 统计目录 |
| `eta_squared_table` | Eta 平方效应量 | Eta Squared | 表格 | 分类字段、数值字段 | 可运行 | 统计目录 |
| `eta_squared_text` | Eta 平方效应量 | Eta Squared | 文字解读 | 分类字段、数值字段 | 可运行 | 统计目录 |
| `intraclass_correlation_data` | 组内相关系数 | Intraclass Correlation | 结构化数据 | 数值字段、分组 | 目录条目 | 统计目录 |
| `intraclass_correlation_table` | 组内相关系数 | Intraclass Correlation | 表格 | 数值字段、分组 | 目录条目 | 统计目录 |
| `intraclass_correlation_text` | 组内相关系数 | Intraclass Correlation | 文字解读 | 数值字段、分组 | 目录条目 | 统计目录 |
| `kendall_tau_data` | 肯德尔秩相关系数 | Kendall Tau | 结构化数据 | 数值字段、数值字段 | 可运行 | 统计目录 |
| `kendall_tau_table` | 肯德尔秩相关系数 | Kendall Tau | 表格 | 数值字段、数值字段 | 可运行 | 统计目录 |
| `kendall_tau_text` | 肯德尔秩相关系数 | Kendall Tau | 文字解读 | 数值字段、数值字段 | 可运行 | 统计目录 |
| `moran_i_spatial_autocorrelation_data` | 莫兰 I 空间自相关 | Moran's I Spatial Autocorrelation | 结构化数据 | 对象级、数值字段 | 目录条目 | 统计目录 |
| `moran_i_spatial_autocorrelation_table` | 莫兰 I 空间自相关 | Moran's I Spatial Autocorrelation | 表格 | 对象级、数值字段 | 目录条目 | 统计目录 |
| `moran_i_spatial_autocorrelation_text` | 莫兰 I 空间自相关 | Moran's I Spatial Autocorrelation | 文字解读 | 对象级、数值字段 | 目录条目 | 统计目录 |
| `mutual_information_data` | 互信息分析 | Mutual Information | 结构化数据 | numeric or categorical、numeric or categorical | 目录条目 | 统计目录 |
| `mutual_information_table` | 互信息分析 | Mutual Information | 表格 | numeric or categorical、numeric or categorical | 目录条目 | 统计目录 |
| `mutual_information_text` | 互信息分析 | Mutual Information | 文字解读 | numeric or categorical、numeric or categorical | 目录条目 | 统计目录 |
| `nearest_neighbor_spatial_search_data` | 最近邻空间搜索 | Nearest-neighbor Spatial Search | 结构化数据 | 对象级 | 目录条目 | 统计目录 |
| `nearest_neighbor_spatial_search_table` | 最近邻空间搜索 | Nearest-neighbor Spatial Search | 表格 | 对象级 | 目录条目 | 统计目录 |
| `nearest_neighbor_spatial_search_text` | 最近邻空间搜索 | Nearest-neighbor Spatial Search | 文字解读 | 对象级 | 目录条目 | 统计目录 |
| `network_assortativity_data` | 网络同配性 | Network Assortativity | 结构化数据 | 对象级、分组 | 目录条目 | 统计目录 |
| `network_assortativity_table` | 网络同配性 | Network Assortativity | 表格 | 对象级、分组 | 目录条目 | 统计目录 |
| `network_assortativity_text` | 网络同配性 | Network Assortativity | 文字解读 | 对象级、分组 | 目录条目 | 统计目录 |
| `partial_correlation_data` | 偏相关分析 | Partial Correlation | 结构化数据 | 数值字段、数值字段、covariate | 可运行 | 统计目录 |
| `partial_correlation_table` | 偏相关分析 | Partial Correlation | 表格 | 数值字段、数值字段、covariate | 可运行 | 统计目录 |
| `partial_correlation_text` | 偏相关分析 | Partial Correlation | 文字解读 | 数值字段、数值字段、covariate | 可运行 | 统计目录 |
| `pearson_correlation_data` | 皮尔逊相关分析 | Pearson Correlation | 结构化数据 | 数值字段、数值字段 | 可运行 | 统计目录 |
| `pearson_correlation_table` | 皮尔逊相关分析 | Pearson Correlation | 表格 | 数值字段、数值字段 | 可运行 | 统计目录 |
| `pearson_correlation_text` | 皮尔逊相关分析 | Pearson Correlation | 文字解读 | 数值字段、数值字段 | 可运行 | 统计目录 |
| `point_biserial_data` | 点二列相关分析 | Point-Biserial Correlation | 结构化数据 | 数值字段、binary | 可运行 | 统计目录 |
| `point_biserial_table` | 点二列相关分析 | Point-Biserial Correlation | 表格 | 数值字段、binary | 可运行 | 统计目录 |
| `point_biserial_text` | 点二列相关分析 | Point-Biserial Correlation | 文字解读 | 数值字段、binary | 可运行 | 统计目录 |
| `spearman_correlation_data` | 斯皮尔曼秩相关分析 | Spearman Correlation | 结构化数据 | 数值字段、数值字段 | 可运行 | 统计目录 |
| `spearman_correlation_table` | 斯皮尔曼秩相关分析 | Spearman Correlation | 表格 | 数值字段、数值字段 | 可运行 | 统计目录 |
| `spearman_correlation_text` | 斯皮尔曼秩相关分析 | Spearman Correlation | 文字解读 | 数值字段、数值字段 | 可运行 | 统计目录 |
| `text_embedding_similarity_data` | 文本嵌入相似度分析 | Text Embedding Similarity | 结构化数据 | 字段对 | 目录条目 | 统计目录 |
| `text_embedding_similarity_table` | 文本嵌入相似度分析 | Text Embedding Similarity | 表格 | 字段对 | 目录条目 | 统计目录 |
| `text_embedding_similarity_text` | 文本嵌入相似度分析 | Text Embedding Similarity | 文字解读 | 字段对 | 目录条目 | 统计目录 |

### 分析方法（注册族：`分布假设`；54 张；可运行 36 张）

| 卡片 ID | 中文方法名称 | 原始英文概念 | 中文输出形式 | 字段角色 | 状态 | 来源 |
| --- | --- | --- | --- | --- | --- | --- |
| `anderson_darling_data` | 安德森-达林检验 | Anderson-Darling Test | 结构化数据 | 数值字段 | 可运行 | 统计目录 |
| `anderson_darling_table` | 安德森-达林检验 | Anderson-Darling Test | 表格 | 数值字段 | 可运行 | 统计目录 |
| `anderson_darling_text` | 安德森-达林检验 | Anderson-Darling Test | 文字解读 | 数值字段 | 可运行 | 统计目录 |
| `bartlett_data` | 巴特利特方差齐性检验 | Bartlett Test | 结构化数据 | 数值字段、分类字段 | 可运行 | 统计目录 |
| `bartlett_table` | 巴特利特方差齐性检验 | Bartlett Test | 表格 | 数值字段、分类字段 | 可运行 | 统计目录 |
| `bartlett_text` | 巴特利特方差齐性检验 | Bartlett Test | 文字解读 | 数值字段、分类字段 | 可运行 | 统计目录 |
| `box_m_test_data` | Box M 协方差矩阵检验 | Box's M Test | 结构化数据 | multi numeric、分类字段 | 目录条目 | 统计目录 |
| `box_m_test_table` | Box M 协方差矩阵检验 | Box's M Test | 表格 | multi numeric、分类字段 | 目录条目 | 统计目录 |
| `box_m_test_text` | Box M 协方差矩阵检验 | Box's M Test | 文字解读 | multi numeric、分类字段 | 目录条目 | 统计目录 |
| `breusch_pagan_data` | 布鲁施-帕甘异方差检验 | Breusch-Pagan Test | 结构化数据 | 数值字段、数值字段 | 可运行 | 统计目录 |
| `breusch_pagan_table` | 布鲁施-帕甘异方差检验 | Breusch-Pagan Test | 表格 | 数值字段、数值字段 | 可运行 | 统计目录 |
| `breusch_pagan_text` | 布鲁施-帕甘异方差检验 | Breusch-Pagan Test | 文字解读 | 数值字段、数值字段 | 可运行 | 统计目录 |
| `brown_forsythe_data` | 布朗-福赛斯方差齐性检验 | Brown-Forsythe Test | 结构化数据 | 数值字段、分类字段 | 可运行 | 统计目录 |
| `brown_forsythe_table` | 布朗-福赛斯方差齐性检验 | Brown-Forsythe Test | 表格 | 数值字段、分类字段 | 可运行 | 统计目录 |
| `brown_forsythe_text` | 布朗-福赛斯方差齐性检验 | Brown-Forsythe Test | 文字解读 | 数值字段、分类字段 | 可运行 | 统计目录 |
| `dagostino_k2_data` | 达戈斯蒂诺 K 平方检验 | D'Agostino K^2 Test | 结构化数据 | 数值字段 | 可运行 | 统计目录 |
| `dagostino_k2_table` | 达戈斯蒂诺 K 平方检验 | D'Agostino K^2 Test | 表格 | 数值字段 | 可运行 | 统计目录 |
| `dagostino_k2_text` | 达戈斯蒂诺 K 平方检验 | D'Agostino K^2 Test | 文字解读 | 数值字段 | 可运行 | 统计目录 |
| `durbin_watson_data` | 德宾-沃森残差自相关检验 | Durbin-Watson | 结构化数据 | 数值字段、数值字段 | 可运行 | 统计目录 |
| `durbin_watson_table` | 德宾-沃森残差自相关检验 | Durbin-Watson | 表格 | 数值字段、数值字段 | 可运行 | 统计目录 |
| `durbin_watson_text` | 德宾-沃森残差自相关检验 | Durbin-Watson | 文字解读 | 数值字段、数值字段 | 可运行 | 统计目录 |
| `jarque_bera_data` | 雅克-贝拉检验 | Jarque-Bera Test | 结构化数据 | 数值字段 | 可运行 | 统计目录 |
| `jarque_bera_table` | 雅克-贝拉检验 | Jarque-Bera Test | 表格 | 数值字段 | 可运行 | 统计目录 |
| `jarque_bera_text` | 雅克-贝拉检验 | Jarque-Bera Test | 文字解读 | 数值字段 | 可运行 | 统计目录 |
| `kolmogorov_smirnov_1samp_data` | 单样本柯尔莫哥洛夫-斯米尔诺夫检验 | One-sample KS Test | 结构化数据 | 数值字段 | 可运行 | 统计目录 |
| `kolmogorov_smirnov_1samp_table` | 单样本柯尔莫哥洛夫-斯米尔诺夫检验 | One-sample KS Test | 表格 | 数值字段 | 可运行 | 统计目录 |
| `kolmogorov_smirnov_1samp_text` | 单样本柯尔莫哥洛夫-斯米尔诺夫检验 | One-sample KS Test | 文字解读 | 数值字段 | 可运行 | 统计目录 |
| `levene_data` | 列文方差齐性检验 | Levene Test | 结构化数据 | 数值字段、分类字段 | 可运行 | 统计目录 |
| `levene_table` | 列文方差齐性检验 | Levene Test | 表格 | 数值字段、分类字段 | 可运行 | 统计目录 |
| `levene_text` | 列文方差齐性检验 | Levene Test | 文字解读 | 数值字段、分类字段 | 可运行 | 统计目录 |
| `mauchly_sphericity_data` | 莫赫利球形性检验 | Mauchly Sphericity Test | 结构化数据 | 数值字段、within subject factor | 目录条目 | 统计目录 |
| `mauchly_sphericity_table` | 莫赫利球形性检验 | Mauchly Sphericity Test | 表格 | 数值字段、within subject factor | 目录条目 | 统计目录 |
| `mauchly_sphericity_text` | 莫赫利球形性检验 | Mauchly Sphericity Test | 文字解读 | 数值字段、within subject factor | 目录条目 | 统计目录 |
| `normality_data` | 正态性检验 | Normality Test | 结构化数据 | 数值字段 | 可运行 | 统计目录 |
| `normality_table` | 正态性检验 | Normality Test | 表格 | 数值字段 | 可运行 | 统计目录 |
| `normality_text` | 正态性检验 | Normality Test | 文字解读 | 数值字段 | 可运行 | 统计目录 |
| `overdispersion_diagnostic_data` | 过度离散诊断 | Overdispersion Diagnostic | 结构化数据 | count | 目录条目 | 统计目录 |
| `overdispersion_diagnostic_table` | 过度离散诊断 | Overdispersion Diagnostic | 表格 | count | 目录条目 | 统计目录 |
| `overdispersion_diagnostic_text` | 过度离散诊断 | Overdispersion Diagnostic | 文字解读 | count | 目录条目 | 统计目录 |
| `qq_diagnostic_review_data` | Q-Q 图诊断评审 | Q-Q Diagnostic Review | 结构化数据 | 数值字段 | 目录条目 | 统计目录 |
| `qq_diagnostic_review_table` | Q-Q 图诊断评审 | Q-Q Diagnostic Review | 表格 | 数值字段 | 目录条目 | 统计目录 |
| `qq_diagnostic_review_text` | Q-Q 图诊断评审 | Q-Q Diagnostic Review | 文字解读 | 数值字段 | 目录条目 | 统计目录 |
| `shapiro_wilk_data` | 夏皮罗-威尔克检验 | Shapiro-Wilk Test | 结构化数据 | 数值字段 | 可运行 | 统计目录 |
| `shapiro_wilk_table` | 夏皮罗-威尔克检验 | Shapiro-Wilk Test | 表格 | 数值字段 | 可运行 | 统计目录 |
| `shapiro_wilk_text` | 夏皮罗-威尔克检验 | Shapiro-Wilk Test | 文字解读 | 数值字段 | 可运行 | 统计目录 |
| `skewness_kurtosis_profile_data` | 偏度与峰度画像 | Skewness / Kurtosis Profile | 结构化数据 | 数值字段 | 目录条目 | 统计目录 |
| `skewness_kurtosis_profile_table` | 偏度与峰度画像 | Skewness / Kurtosis Profile | 表格 | 数值字段 | 目录条目 | 统计目录 |
| `skewness_kurtosis_profile_text` | 偏度与峰度画像 | Skewness / Kurtosis Profile | 文字解读 | 数值字段 | 目录条目 | 统计目录 |
| `white_test_data` | 怀特异方差检验 | White Test | 结构化数据 | 数值字段、数值字段 | 可运行 | 统计目录 |
| `white_test_table` | 怀特异方差检验 | White Test | 表格 | 数值字段、数值字段 | 可运行 | 统计目录 |
| `white_test_text` | 怀特异方差检验 | White Test | 文字解读 | 数值字段、数值字段 | 可运行 | 统计目录 |
| `zero_inflation_diagnostic_data` | 零膨胀诊断 | Zero-inflation Diagnostic | 结构化数据 | 数值字段 | 目录条目 | 统计目录 |
| `zero_inflation_diagnostic_table` | 零膨胀诊断 | Zero-inflation Diagnostic | 表格 | 数值字段 | 目录条目 | 统计目录 |
| `zero_inflation_diagnostic_text` | 零膨胀诊断 | Zero-inflation Diagnostic | 文字解读 | 数值字段 | 目录条目 | 统计目录 |

### 分析方法（注册族：`分类关联`；39 张；可运行 30 张）

| 卡片 ID | 中文方法名称 | 原始英文概念 | 中文输出形式 | 字段角色 | 状态 | 来源 |
| --- | --- | --- | --- | --- | --- | --- |
| `chi_square_data` | 卡方检验 | Chi-square Test | 结构化数据 | 分类字段、分类字段 | 可运行 | 统计目录 |
| `chi_square_table` | 卡方检验 | Chi-square Test | 表格 | 分类字段、分类字段 | 可运行 | 统计目录 |
| `chi_square_text` | 卡方检验 | Chi-square Test | 文字解读 | 分类字段、分类字段 | 可运行 | 统计目录 |
| `cmh_test_data` | 科克伦-曼特尔-亨泽尔检验 | Cochran-Mantel-Haenszel Test | 结构化数据 | 分类字段、分类字段、strata | 可运行 | 统计目录 |
| `cmh_test_table` | 科克伦-曼特尔-亨泽尔检验 | Cochran-Mantel-Haenszel Test | 表格 | 分类字段、分类字段、strata | 可运行 | 统计目录 |
| `cmh_test_text` | 科克伦-曼特尔-亨泽尔检验 | Cochran-Mantel-Haenszel Test | 文字解读 | 分类字段、分类字段、strata | 可运行 | 统计目录 |
| `cochran_q_data` | 科克伦 Q 检验 | Cochran Q Test | 结构化数据 | binary、within subject factor | 可运行 | 统计目录 |
| `cochran_q_table` | 科克伦 Q 检验 | Cochran Q Test | 表格 | binary、within subject factor | 可运行 | 统计目录 |
| `cochran_q_text` | 科克伦 Q 检验 | Cochran Q Test | 文字解读 | binary、within subject factor | 可运行 | 统计目录 |
| `cohens_kappa_data` | 科恩卡帕系数 | Cohen's Kappa | 结构化数据 | 分类字段、paired | 可运行 | 统计目录 |
| `cohens_kappa_table` | 科恩卡帕系数 | Cohen's Kappa | 表格 | 分类字段、paired | 可运行 | 统计目录 |
| `cohens_kappa_text` | 科恩卡帕系数 | Cohen's Kappa | 文字解读 | 分类字段、paired | 可运行 | 统计目录 |
| `cramers_v_data` | 克拉默 V 关联系数 | Cramer's V | 结构化数据 | 分类字段、分类字段 | 可运行 | 统计目录 |
| `cramers_v_table` | 克拉默 V 关联系数 | Cramer's V | 表格 | 分类字段、分类字段 | 可运行 | 统计目录 |
| `cramers_v_text` | 克拉默 V 关联系数 | Cramer's V | 文字解读 | 分类字段、分类字段 | 可运行 | 统计目录 |
| `fisher_exact_data` | 费舍尔精确检验 | Fisher Exact Test | 结构化数据 | 分类字段、分类字段 | 可运行 | 统计目录 |
| `fisher_exact_table` | 费舍尔精确检验 | Fisher Exact Test | 表格 | 分类字段、分类字段 | 可运行 | 统计目录 |
| `fisher_exact_text` | 费舍尔精确检验 | Fisher Exact Test | 文字解读 | 分类字段、分类字段 | 可运行 | 统计目录 |
| `goodman_kruskal_lambda_data` | 古德曼-克鲁斯卡尔拉姆达系数 | Goodman-Kruskal Lambda | 结构化数据 | 分类字段、分类字段 | 可运行 | 统计目录 |
| `goodman_kruskal_lambda_table` | 古德曼-克鲁斯卡尔拉姆达系数 | Goodman-Kruskal Lambda | 表格 | 分类字段、分类字段 | 可运行 | 统计目录 |
| `goodman_kruskal_lambda_text` | 古德曼-克鲁斯卡尔拉姆达系数 | Goodman-Kruskal Lambda | 文字解读 | 分类字段、分类字段 | 可运行 | 统计目录 |
| `mcnemar_data` | 麦克内马尔检验 | McNemar Test | 结构化数据 | binary、paired | 可运行 | 统计目录 |
| `mcnemar_table` | 麦克内马尔检验 | McNemar Test | 表格 | binary、paired | 可运行 | 统计目录 |
| `mcnemar_text` | 麦克内马尔检验 | McNemar Test | 文字解读 | binary、paired | 可运行 | 统计目录 |
| `odds_ratio_data` | 优势比 | Odds Ratio | 结构化数据 | binary、binary | 目录条目 | 统计目录 |
| `odds_ratio_table` | 优势比 | Odds Ratio | 表格 | binary、binary | 目录条目 | 统计目录 |
| `odds_ratio_text` | 优势比 | Odds Ratio | 文字解读 | binary、binary | 目录条目 | 统计目录 |
| `phi_coefficient_data` | 菲系数 | Phi Coefficient | 结构化数据 | binary、binary | 可运行 | 统计目录 |
| `phi_coefficient_table` | 菲系数 | Phi Coefficient | 表格 | binary、binary | 可运行 | 统计目录 |
| `phi_coefficient_text` | 菲系数 | Phi Coefficient | 文字解读 | binary、binary | 可运行 | 统计目录 |
| `relative_risk_data` | 相对风险 | Relative Risk | 结构化数据 | binary、binary | 目录条目 | 统计目录 |
| `relative_risk_table` | 相对风险 | Relative Risk | 表格 | binary、binary | 目录条目 | 统计目录 |
| `relative_risk_text` | 相对风险 | Relative Risk | 文字解读 | binary、binary | 目录条目 | 统计目录 |
| `risk_difference_data` | 风险差 | Risk Difference | 结构化数据 | binary、binary | 目录条目 | 统计目录 |
| `risk_difference_table` | 风险差 | Risk Difference | 表格 | binary、binary | 目录条目 | 统计目录 |
| `risk_difference_text` | 风险差 | Risk Difference | 文字解读 | binary、binary | 目录条目 | 统计目录 |
| `theils_u_data` | 泰尔 U 关联系数 | Theil's U | 结构化数据 | 分类字段、分类字段 | 可运行 | 统计目录 |
| `theils_u_table` | 泰尔 U 关联系数 | Theil's U | 表格 | 分类字段、分类字段 | 可运行 | 统计目录 |
| `theils_u_text` | 泰尔 U 关联系数 | Theil's U | 文字解读 | 分类字段、分类字段 | 可运行 | 统计目录 |

### 分析方法（注册族：`可视化`；2685 张；可运行 0 张）

| 卡片 ID | 中文方法名称 | 原始英文概念 | 中文输出形式 | 字段角色 | 状态 | 来源 |
| --- | --- | --- | --- | --- | --- | --- |
| `visual_alluvial` | 可视化分析・可视化・河流图 | 河流图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_area` | 可视化分析・可视化・面积图 | 面积图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_bar` | 可视化分析・可视化・条形图 | 条形图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_beeswarm` | 可视化分析・可视化・蜂群图 | 蜂群图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_boxplot` | 可视化分析・可视化・箱线图 | 箱线图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_bubble` | 可视化分析・可视化・气泡图 | 气泡图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_bullet` | 可视化分析・可视化・子弹图 | 子弹图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_bump_chart` | 可视化分析・可视化 | 排名趋势图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_calendar_heatmap` | 可视化分析・可视化・日历・热力矩阵 | 日历热力图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_candlestick` | 可视化分析・可视化・蜁烛图 | 蜁烛图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_chord` | 可视化分析・可视化・弦图 | 弦图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_choropleth` | 可视化分析・可视化・分级着色地图 | 分级着色地图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_cohort_matrix` | 可视化分析・可视化・队列 | 队列矩阵 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_column` | 可视化分析・可视化・柱状图 | 柱状图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_contour` | 可视化分析・可视化・等高线图 | 等高线图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_control_chart` | 可视化分析・可视化・控制 | 控制图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_density` | 可视化分析・可视化・密度图 | 密度图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_ecdf` | 可视化分析・可视化・经验分布图 | 经验分布图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_flow_map` | 可视化分析・可视化 | 流向地图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_funnel` | 可视化分析・可视化・漏斗 | 漏斗图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_gauge` | 可视化分析・可视化・仪表盘 | 仪表盘 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_geo_map` | 可视化分析・可视化 | 地理地图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_heatmap` | 可视化分析・可视化・热力矩阵 | 热力矩阵 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_hexbin` | 可视化分析・可视化・六边形密度图 | 六边形密度图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_histogram` | 可视化分析・可视化・直方图 | 直方图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_line` | 可视化分析・可视化・折线图 | 折线图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_marimekko` | 可视化分析・可视化・马赛克图 | 马赛克图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_network` | 可视化分析・可视化・网络 | 关系网络 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_pairplot` | 可视化分析・可视化・成对散点矩阵 | 成对散点矩阵 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_parallel_coordinates` | 可视化分析・可视化 | 平行坐标图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_qqplot` | 可视化分析・可视化・正态 Q-Q 图 | 正态 Q-Q 图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_quadrant` | 可视化分析・可视化・象限图 | 象限图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_radar` | 可视化分析・可视化・雷达图 | 雷达图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_sankey` | 可视化分析・可视化・桑基图 | 桑基图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_scatter` | 可视化分析・可视化・散点图 | 散点图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_slopegraph` | 可视化分析・可视化・坡度图 | 坡度图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_small_multiple` | 可视化分析・可视化 | 小多图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_sparkline` | 可视化分析・可视化・迷你趋势线 | 迷你趋势线 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_stacked_area` | 可视化分析・可视化・面积图 | 堆积面积图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_stat_agreement_reliability_annotated_reference_view` | 可视化分析・可视化・统计 | Agreement reliability - Annotated reference view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_agreement_reliability_boxen_interval` | 可视化分析・可视化・统计 | Agreement reliability - Boxen interval plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_agreement_reliability_comparative_lollipop` | 可视化分析・可视化・统计 | Agreement reliability - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_agreement_reliability_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_agreement_reliability_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Agreement reliability - Diagnostic panel | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_agreement_reliability_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_agreement_reliability_flow_transition_map` | 可视化分析・可视化・统计 | Agreement reliability - Flow transition map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_agreement_reliability_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_agreement_reliability_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_agreement_reliability_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_agreement_reliability_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_agreement_reliability_mosaic_tile_view` | 可视化分析・可视化・统计 | Agreement reliability - Mosaic tile view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_agreement_reliability_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_agreement_reliability_qq_reference_plot` | 可视化分析・可视化・统计 | Agreement reliability - Q-Q reference plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_agreement_reliability_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_agreement_reliability_raincloud_view` | 可视化分析・可视化・统计 | Agreement reliability - Raincloud view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_agreement_reliability_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_agreement_reliability_residual_annotation_map` | 可视化分析・可视化・统计 | Agreement reliability - Residual annotation map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_agreement_reliability_slope_change_view` | 可视化分析・可视化・统计 | Agreement reliability - Slope change view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_agreement_reliability_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_agreement_reliability_stratified_dotplot` | 可视化分析・可视化・统计 | Agreement reliability - Stratified dot plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_agreement_reliability_threshold_band` | 可视化分析・可视化・统计 | Agreement reliability - Threshold band | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_agreement_reliability_uncertainty_ribbon` | 可视化分析・可视化・统计 | Agreement reliability - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_agreement_reliability_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_assignment_flow_annotated_reference_view` | 可视化分析・可视化・统计 | Assignment flow - Annotated reference view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_assignment_flow_boxen_interval` | 可视化分析・可视化・统计 | Assignment flow - Boxen interval plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_assignment_flow_comparative_lollipop` | 可视化分析・可视化・统计 | Assignment flow - Comparative lollipop plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_assignment_flow_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_assignment_flow_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Assignment flow - Diagnostic panel | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_assignment_flow_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_assignment_flow_flow_transition_map` | 可视化分析・可视化・统计 | Assignment flow - Flow transition map | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_assignment_flow_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_assignment_flow_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_assignment_flow_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_assignment_flow_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 流向地图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_assignment_flow_mosaic_tile_view` | 可视化分析・可视化・统计 | Assignment flow - Mosaic tile view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_assignment_flow_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_assignment_flow_qq_reference_plot` | 可视化分析・可视化・统计 | Assignment flow - Q-Q reference plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_assignment_flow_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_assignment_flow_raincloud_view` | 可视化分析・可视化・统计 | Assignment flow - Raincloud view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_assignment_flow_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_assignment_flow_residual_annotation_map` | 可视化分析・可视化・统计 | Assignment flow - Residual annotation map | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_assignment_flow_slope_change_view` | 可视化分析・可视化・统计 | Assignment flow - Slope change view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_assignment_flow_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_assignment_flow_stratified_dotplot` | 可视化分析・可视化・统计 | Assignment flow - Stratified dot plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_assignment_flow_threshold_band` | 可视化分析・可视化・统计 | Assignment flow - Threshold band | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_assignment_flow_uncertainty_ribbon` | 可视化分析・可视化・统计 | Assignment flow - Uncertainty ribbon | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_assignment_flow_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_autocorrelation_pattern_annotated_reference_view` | 可视化分析・可视化・统计 | Autocorrelation pattern - Annotated reference view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_autocorrelation_pattern_boxen_interval` | 可视化分析・可视化・统计 | Autocorrelation pattern - Boxen interval plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_autocorrelation_pattern_comparative_lollipop` | 可视化分析・可视化・统计 | Autocorrelation pattern - Comparative lollipop plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_autocorrelation_pattern_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_autocorrelation_pattern_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Autocorrelation pattern - Diagnostic panel | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_autocorrelation_pattern_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_autocorrelation_pattern_flow_transition_map` | 可视化分析・可视化・统计 | Autocorrelation pattern - Flow transition map | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_autocorrelation_pattern_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_autocorrelation_pattern_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_autocorrelation_pattern_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_autocorrelation_pattern_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_autocorrelation_pattern_mosaic_tile_view` | 可视化分析・可视化・统计 | Autocorrelation pattern - Mosaic tile view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_autocorrelation_pattern_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_autocorrelation_pattern_qq_reference_plot` | 可视化分析・可视化・统计 | Autocorrelation pattern - Q-Q reference plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_autocorrelation_pattern_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_autocorrelation_pattern_raincloud_view` | 可视化分析・可视化・统计 | Autocorrelation pattern - Raincloud view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_autocorrelation_pattern_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_autocorrelation_pattern_residual_annotation_map` | 可视化分析・可视化・统计 | Autocorrelation pattern - Residual annotation map | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_autocorrelation_pattern_slope_change_view` | 可视化分析・可视化・统计 | Autocorrelation pattern - Slope change view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_autocorrelation_pattern_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_autocorrelation_pattern_stratified_dotplot` | 可视化分析・可视化・统计 | Autocorrelation pattern - Stratified dot plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_autocorrelation_pattern_threshold_band` | 可视化分析・可视化・统计 | Autocorrelation pattern - Threshold band | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_autocorrelation_pattern_uncertainty_ribbon` | 可视化分析・可视化・统计 | Autocorrelation pattern - Uncertainty ribbon | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_autocorrelation_pattern_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_baseline_covariate_balance_annotated_reference_view` | 可视化分析・可视化・统计・基线 | Baseline covariate balance - Annotated reference view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_baseline_covariate_balance_boxen_interval` | 可视化分析・可视化・统计・基线 | Baseline covariate balance - Boxen interval plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_baseline_covariate_balance_comparative_lollipop` | 可视化分析・可视化・统计・基线 | Baseline covariate balance - Comparative lollipop plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_baseline_covariate_balance_density_ridge` | 可视化分析・可视化・统计・基线・密度图 | 密度图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_baseline_covariate_balance_diagnostic_panel` | 可视化分析・可视化・统计・基线・诊断・面板 | Baseline covariate balance - Diagnostic panel | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_baseline_covariate_balance_ecdf_step_view` | 可视化分析・可视化・统计・基线・经验分布图 | 经验分布图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_baseline_covariate_balance_flow_transition_map` | 可视化分析・可视化・统计・基线 | Baseline covariate balance - Flow transition map | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_baseline_covariate_balance_forest_interval_plot` | 可视化分析・可视化・统计・基线・随机森林 | 随机森林 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_baseline_covariate_balance_heatmap_matrix` | 可视化分析・可视化・统计・基线・热力矩阵 | 热力矩阵 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_baseline_covariate_balance_histogram_facets` | 可视化分析・可视化・统计・基线・直方图 | 直方图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_baseline_covariate_balance_map_choropleth_layer` | 可视化分析・可视化・统计・基线・分级着色地图 | 分级着色地图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_baseline_covariate_balance_mosaic_tile_view` | 可视化分析・可视化・统计・基线 | Baseline covariate balance - Mosaic tile view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_baseline_covariate_balance_network_node_link` | 可视化分析・可视化・统计・基线・网络 | 关系网络 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_baseline_covariate_balance_qq_reference_plot` | 可视化分析・可视化・统计・基线 | Baseline covariate balance - Q-Q reference plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_baseline_covariate_balance_quantile_band` | 可视化分析・可视化・统计・基线・分位数 | 分位数 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_baseline_covariate_balance_raincloud_view` | 可视化分析・可视化・统计・基线 | Baseline covariate balance - Raincloud view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_baseline_covariate_balance_rank_interval_plot` | 可视化分析・可视化・统计・基线・排名 | 排名 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_baseline_covariate_balance_residual_annotation_map` | 可视化分析・可视化・统计・基线 | Baseline covariate balance - Residual annotation map | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_baseline_covariate_balance_slope_change_view` | 可视化分析・可视化・统计・基线 | Baseline covariate balance - Slope change view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_baseline_covariate_balance_small_multiple_grid` | 可视化分析・可视化・统计・基线 | 小多图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_baseline_covariate_balance_stratified_dotplot` | 可视化分析・可视化・统计・基线 | Baseline covariate balance - Stratified dot plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_baseline_covariate_balance_threshold_band` | 可视化分析・可视化・统计・基线 | Baseline covariate balance - Threshold band | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_baseline_covariate_balance_uncertainty_ribbon` | 可视化分析・可视化・统计・基线 | Baseline covariate balance - Uncertainty ribbon | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_baseline_covariate_balance_violin_summary` | 可视化分析・可视化・统计・基线・小提琴图・概览 | 小提琴图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_block_design_balance_annotated_reference_view` | 可视化分析・可视化・统计 | Block design balance - Annotated reference view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_block_design_balance_boxen_interval` | 可视化分析・可视化・统计 | Block design balance - Boxen interval plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_block_design_balance_comparative_lollipop` | 可视化分析・可视化・统计 | Block design balance - Comparative lollipop plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_block_design_balance_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_block_design_balance_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Block design balance - Diagnostic panel | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_block_design_balance_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_block_design_balance_flow_transition_map` | 可视化分析・可视化・统计 | Block design balance - Flow transition map | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_block_design_balance_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_block_design_balance_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_block_design_balance_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_block_design_balance_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_block_design_balance_mosaic_tile_view` | 可视化分析・可视化・统计 | Block design balance - Mosaic tile view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_block_design_balance_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_block_design_balance_qq_reference_plot` | 可视化分析・可视化・统计 | Block design balance - Q-Q reference plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_block_design_balance_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_block_design_balance_raincloud_view` | 可视化分析・可视化・统计 | Block design balance - Raincloud view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_block_design_balance_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_block_design_balance_residual_annotation_map` | 可视化分析・可视化・统计 | Block design balance - Residual annotation map | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_block_design_balance_slope_change_view` | 可视化分析・可视化・统计 | Block design balance - Slope change view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_block_design_balance_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_block_design_balance_stratified_dotplot` | 可视化分析・可视化・统计 | Block design balance - Stratified dot plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_block_design_balance_threshold_band` | 可视化分析・可视化・统计 | Block design balance - Threshold band | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_block_design_balance_uncertainty_ribbon` | 可视化分析・可视化・统计 | Block design balance - Uncertainty ribbon | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_block_design_balance_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_annotated_reference_view` | 可视化分析・可视化・统计 | Calibration diagnostic - Annotated reference view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_boxen_interval` | 可视化分析・可视化・统计 | Calibration diagnostic - Boxen interval plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_by_group_annotated_reference_view` | 可视化分析・可视化・统计 | Calibration by group - Annotated reference view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_by_group_boxen_interval` | 可视化分析・可视化・统计 | Calibration by group - Boxen interval plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_by_group_comparative_lollipop` | 可视化分析・可视化・统计 | Calibration by group - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_by_group_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_by_group_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Calibration by group - Diagnostic panel | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_by_group_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_by_group_flow_transition_map` | 可视化分析・可视化・统计 | Calibration by group - Flow transition map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_by_group_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_by_group_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_by_group_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_by_group_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_by_group_mosaic_tile_view` | 可视化分析・可视化・统计 | Calibration by group - Mosaic tile view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_by_group_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_by_group_qq_reference_plot` | 可视化分析・可视化・统计 | Calibration by group - Q-Q reference plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_by_group_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_by_group_raincloud_view` | 可视化分析・可视化・统计 | Calibration by group - Raincloud view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_by_group_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_by_group_residual_annotation_map` | 可视化分析・可视化・统计 | Calibration by group - Residual annotation map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_by_group_slope_change_view` | 可视化分析・可视化・统计 | Calibration by group - Slope change view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_by_group_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_by_group_stratified_dotplot` | 可视化分析・可视化・统计 | Calibration by group - Stratified dot plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_by_group_threshold_band` | 可视化分析・可视化・统计 | Calibration by group - Threshold band | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_by_group_uncertainty_ribbon` | 可视化分析・可视化・统计 | Calibration by group - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_by_group_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_comparative_lollipop` | 可视化分析・可视化・统计 | Calibration diagnostic - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Calibration diagnostic - Diagnostic panel | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_flow_transition_map` | 可视化分析・可视化・统计 | Calibration diagnostic - Flow transition map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_mosaic_tile_view` | 可视化分析・可视化・统计 | Calibration diagnostic - Mosaic tile view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_qq_reference_plot` | 可视化分析・可视化・统计 | Calibration diagnostic - Q-Q reference plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_raincloud_view` | 可视化分析・可视化・统计 | Calibration diagnostic - Raincloud view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_residual_annotation_map` | 可视化分析・可视化・统计 | Calibration diagnostic - Residual annotation map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_slope_change_view` | 可视化分析・可视化・统计 | Calibration diagnostic - Slope change view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_stratified_dotplot` | 可视化分析・可视化・统计 | Calibration diagnostic - Stratified dot plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_threshold_band` | 可视化分析・可视化・统计 | Calibration diagnostic - Threshold band | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_uncertainty_ribbon` | 可视化分析・可视化・统计 | Calibration diagnostic - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_calibration_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_categorical_composition_annotated_reference_view` | 可视化分析・可视化・统计 | Categorical composition - Annotated reference view | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_categorical_composition_boxen_interval` | 可视化分析・可视化・统计 | Categorical composition - Boxen interval plot | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_categorical_composition_comparative_lollipop` | 可视化分析・可视化・统计 | Categorical composition - Comparative lollipop plot | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_categorical_composition_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_categorical_composition_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Categorical composition - Diagnostic panel | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_categorical_composition_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_categorical_composition_flow_transition_map` | 可视化分析・可视化・统计 | Categorical composition - Flow transition map | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_categorical_composition_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_categorical_composition_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_categorical_composition_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_categorical_composition_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_categorical_composition_mosaic_tile_view` | 可视化分析・可视化・统计 | Categorical composition - Mosaic tile view | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_categorical_composition_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_categorical_composition_qq_reference_plot` | 可视化分析・可视化・统计 | Categorical composition - Q-Q reference plot | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_categorical_composition_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_categorical_composition_raincloud_view` | 可视化分析・可视化・统计 | Categorical composition - Raincloud view | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_categorical_composition_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_categorical_composition_residual_annotation_map` | 可视化分析・可视化・统计 | Categorical composition - Residual annotation map | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_categorical_composition_slope_change_view` | 可视化分析・可视化・统计 | Categorical composition - Slope change view | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_categorical_composition_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_categorical_composition_stratified_dotplot` | 可视化分析・可视化・统计 | Categorical composition - Stratified dot plot | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_categorical_composition_threshold_band` | 可视化分析・可视化・统计 | Categorical composition - Threshold band | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_categorical_composition_uncertainty_ribbon` | 可视化分析・可视化・统计 | Categorical composition - Uncertainty ribbon | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_categorical_composition_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_causal_balance_annotated_reference_view` | 可视化分析・可视化・统计・因果 | Causal balance - Annotated reference view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_causal_balance_boxen_interval` | 可视化分析・可视化・统计・因果 | Causal balance - Boxen interval plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_causal_balance_comparative_lollipop` | 可视化分析・可视化・统计・因果 | Causal balance - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_causal_balance_density_ridge` | 可视化分析・可视化・统计・因果・密度图 | 密度图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_causal_balance_diagnostic_panel` | 可视化分析・可视化・统计・因果・诊断・面板 | Causal balance - Diagnostic panel | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_causal_balance_ecdf_step_view` | 可视化分析・可视化・统计・因果・经验分布图 | 经验分布图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_causal_balance_flow_transition_map` | 可视化分析・可视化・统计・因果 | Causal balance - Flow transition map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_causal_balance_forest_interval_plot` | 可视化分析・可视化・统计・因果・随机森林 | 随机森林 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_causal_balance_heatmap_matrix` | 可视化分析・可视化・统计・因果・热力矩阵 | 热力矩阵 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_causal_balance_histogram_facets` | 可视化分析・可视化・统计・因果・直方图 | 直方图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_causal_balance_map_choropleth_layer` | 可视化分析・可视化・统计・因果・分级着色地图 | 分级着色地图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_causal_balance_mosaic_tile_view` | 可视化分析・可视化・统计・因果 | Causal balance - Mosaic tile view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_causal_balance_network_node_link` | 可视化分析・可视化・统计・因果・网络 | 关系网络 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_causal_balance_qq_reference_plot` | 可视化分析・可视化・统计・因果 | Causal balance - Q-Q reference plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_causal_balance_quantile_band` | 可视化分析・可视化・统计・因果・分位数 | 分位数 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_causal_balance_raincloud_view` | 可视化分析・可视化・统计・因果 | Causal balance - Raincloud view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_causal_balance_rank_interval_plot` | 可视化分析・可视化・统计・因果・排名 | 排名 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_causal_balance_residual_annotation_map` | 可视化分析・可视化・统计・因果 | Causal balance - Residual annotation map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_causal_balance_slope_change_view` | 可视化分析・可视化・统计・因果 | Causal balance - Slope change view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_causal_balance_small_multiple_grid` | 可视化分析・可视化・统计・因果 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_causal_balance_stratified_dotplot` | 可视化分析・可视化・统计・因果 | Causal balance - Stratified dot plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_causal_balance_threshold_band` | 可视化分析・可视化・统计・因果 | Causal balance - Threshold band | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_causal_balance_uncertainty_ribbon` | 可视化分析・可视化・统计・因果 | Causal balance - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_causal_balance_violin_summary` | 可视化分析・可视化・统计・因果・小提琴图・概览 | 小提琴图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_change_point_annotated_reference_view` | 可视化分析・可视化・统计 | 拐点 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_change_point_boxen_interval` | 可视化分析・可视化・统计 | 拐点 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_change_point_comparative_lollipop` | 可视化分析・可视化・统计 | 拐点 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_change_point_density_ridge` | 可视化分析・可视化・统计・密度图 | 拐点 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_change_point_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | 拐点 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_change_point_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 拐点 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_change_point_flow_transition_map` | 可视化分析・可视化・统计 | 拐点 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_change_point_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 拐点 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_change_point_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 拐点 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_change_point_histogram_facets` | 可视化分析・可视化・统计・直方图 | 拐点 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_change_point_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 拐点 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_change_point_mosaic_tile_view` | 可视化分析・可视化・统计 | 拐点 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_change_point_network_node_link` | 可视化分析・可视化・统计・网络 | 拐点 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_change_point_qq_reference_plot` | 可视化分析・可视化・统计 | 拐点 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_change_point_quantile_band` | 可视化分析・可视化・统计・分位数 | 拐点 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_change_point_raincloud_view` | 可视化分析・可视化・统计 | 拐点 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_change_point_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 拐点 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_change_point_residual_annotation_map` | 可视化分析・可视化・统计 | 拐点 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_change_point_slope_change_view` | 可视化分析・可视化・统计 | 拐点 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_change_point_small_multiple_grid` | 可视化分析・可视化・统计 | 拐点 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_change_point_stratified_dotplot` | 可视化分析・可视化・统计 | 拐点 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_change_point_threshold_band` | 可视化分析・可视化・统计 | 拐点 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_change_point_uncertainty_ribbon` | 可视化分析・可视化・统计 | 拐点 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_change_point_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 拐点 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_classifier_threshold_annotated_reference_view` | 可视化分析・可视化・统计 | Classifier threshold - Annotated reference view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classifier_threshold_boxen_interval` | 可视化分析・可视化・统计 | Classifier threshold - Boxen interval plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classifier_threshold_comparative_lollipop` | 可视化分析・可视化・统计 | Classifier threshold - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classifier_threshold_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classifier_threshold_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Classifier threshold - Diagnostic panel | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classifier_threshold_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classifier_threshold_flow_transition_map` | 可视化分析・可视化・统计 | Classifier threshold - Flow transition map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classifier_threshold_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classifier_threshold_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classifier_threshold_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classifier_threshold_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classifier_threshold_mosaic_tile_view` | 可视化分析・可视化・统计 | Classifier threshold - Mosaic tile view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classifier_threshold_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classifier_threshold_qq_reference_plot` | 可视化分析・可视化・统计 | Classifier threshold - Q-Q reference plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classifier_threshold_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classifier_threshold_raincloud_view` | 可视化分析・可视化・统计 | Classifier threshold - Raincloud view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classifier_threshold_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classifier_threshold_residual_annotation_map` | 可视化分析・可视化・统计 | Classifier threshold - Residual annotation map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classifier_threshold_slope_change_view` | 可视化分析・可视化・统计 | Classifier threshold - Slope change view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classifier_threshold_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classifier_threshold_stratified_dotplot` | 可视化分析・可视化・统计 | Classifier threshold - Stratified dot plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classifier_threshold_threshold_band` | 可视化分析・可视化・统计 | Classifier threshold - Threshold band | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classifier_threshold_uncertainty_ribbon` | 可视化分析・可视化・统计 | Classifier threshold - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classifier_threshold_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classroom_fairness_annotated_reference_view` | 可视化分析・可视化・统计 | Classroom fairness - Annotated reference view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classroom_fairness_boxen_interval` | 可视化分析・可视化・统计 | Classroom fairness - Boxen interval plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classroom_fairness_comparative_lollipop` | 可视化分析・可视化・统计 | Classroom fairness - Comparative lollipop plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classroom_fairness_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classroom_fairness_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Classroom fairness - Diagnostic panel | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classroom_fairness_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classroom_fairness_flow_transition_map` | 可视化分析・可视化・统计 | Classroom fairness - Flow transition map | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classroom_fairness_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classroom_fairness_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classroom_fairness_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classroom_fairness_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classroom_fairness_mosaic_tile_view` | 可视化分析・可视化・统计 | Classroom fairness - Mosaic tile view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classroom_fairness_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classroom_fairness_qq_reference_plot` | 可视化分析・可视化・统计 | Classroom fairness - Q-Q reference plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classroom_fairness_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classroom_fairness_raincloud_view` | 可视化分析・可视化・统计 | Classroom fairness - Raincloud view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classroom_fairness_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classroom_fairness_residual_annotation_map` | 可视化分析・可视化・统计 | Classroom fairness - Residual annotation map | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classroom_fairness_slope_change_view` | 可视化分析・可视化・统计 | Classroom fairness - Slope change view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classroom_fairness_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classroom_fairness_stratified_dotplot` | 可视化分析・可视化・统计 | Classroom fairness - Stratified dot plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classroom_fairness_threshold_band` | 可视化分析・可视化・统计 | Classroom fairness - Threshold band | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classroom_fairness_uncertainty_ribbon` | 可视化分析・可视化・统计 | Classroom fairness - Uncertainty ribbon | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_classroom_fairness_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_clinical_endpoint_annotated_reference_view` | 可视化分析・可视化・统计 | Clinical endpoint - Annotated reference view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_clinical_endpoint_boxen_interval` | 可视化分析・可视化・统计 | Clinical endpoint - Boxen interval plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_clinical_endpoint_comparative_lollipop` | 可视化分析・可视化・统计 | Clinical endpoint - Comparative lollipop plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_clinical_endpoint_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_clinical_endpoint_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Clinical endpoint - Diagnostic panel | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_clinical_endpoint_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_clinical_endpoint_flow_transition_map` | 可视化分析・可视化・统计 | Clinical endpoint - Flow transition map | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_clinical_endpoint_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_clinical_endpoint_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_clinical_endpoint_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_clinical_endpoint_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_clinical_endpoint_mosaic_tile_view` | 可视化分析・可视化・统计 | Clinical endpoint - Mosaic tile view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_clinical_endpoint_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_clinical_endpoint_qq_reference_plot` | 可视化分析・可视化・统计 | Clinical endpoint - Q-Q reference plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_clinical_endpoint_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_clinical_endpoint_raincloud_view` | 可视化分析・可视化・统计 | Clinical endpoint - Raincloud view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_clinical_endpoint_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_clinical_endpoint_residual_annotation_map` | 可视化分析・可视化・统计 | Clinical endpoint - Residual annotation map | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_clinical_endpoint_slope_change_view` | 可视化分析・可视化・统计 | Clinical endpoint - Slope change view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_clinical_endpoint_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_clinical_endpoint_stratified_dotplot` | 可视化分析・可视化・统计 | Clinical endpoint - Stratified dot plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_clinical_endpoint_threshold_band` | 可视化分析・可视化・统计 | Clinical endpoint - Threshold band | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_clinical_endpoint_uncertainty_ribbon` | 可视化分析・可视化・统计 | Clinical endpoint - Uncertainty ribbon | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_clinical_endpoint_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_cluster_structure_annotated_reference_view` | 可视化分析・可视化・统计・聚类 | Cluster structure - Annotated reference view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_cluster_structure_boxen_interval` | 可视化分析・可视化・统计・聚类 | Cluster structure - Boxen interval plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_cluster_structure_comparative_lollipop` | 可视化分析・可视化・统计・聚类 | Cluster structure - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_cluster_structure_density_ridge` | 可视化分析・可视化・统计・聚类・密度图 | 密度图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_cluster_structure_diagnostic_panel` | 可视化分析・可视化・统计・聚类・诊断・面板 | Cluster structure - Diagnostic panel | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_cluster_structure_ecdf_step_view` | 可视化分析・可视化・统计・聚类・经验分布图 | 经验分布图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_cluster_structure_flow_transition_map` | 可视化分析・可视化・统计・聚类 | Cluster structure - Flow transition map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_cluster_structure_forest_interval_plot` | 可视化分析・可视化・统计・聚类・随机森林 | 随机森林 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_cluster_structure_heatmap_matrix` | 可视化分析・可视化・统计・聚类・热力矩阵 | 热力矩阵 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_cluster_structure_histogram_facets` | 可视化分析・可视化・统计・聚类・直方图 | 直方图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_cluster_structure_map_choropleth_layer` | 可视化分析・可视化・统计・聚类・分级着色地图 | 分级着色地图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_cluster_structure_mosaic_tile_view` | 可视化分析・可视化・统计・聚类 | Cluster structure - Mosaic tile view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_cluster_structure_network_node_link` | 可视化分析・可视化・统计・聚类・网络 | 关系网络 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_cluster_structure_qq_reference_plot` | 可视化分析・可视化・统计・聚类 | Cluster structure - Q-Q reference plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_cluster_structure_quantile_band` | 可视化分析・可视化・统计・聚类・分位数 | 分位数 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_cluster_structure_raincloud_view` | 可视化分析・可视化・统计・聚类 | Cluster structure - Raincloud view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_cluster_structure_rank_interval_plot` | 可视化分析・可视化・统计・聚类・排名 | 排名 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_cluster_structure_residual_annotation_map` | 可视化分析・可视化・统计・聚类 | Cluster structure - Residual annotation map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_cluster_structure_slope_change_view` | 可视化分析・可视化・统计・聚类 | Cluster structure - Slope change view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_cluster_structure_small_multiple_grid` | 可视化分析・可视化・统计・聚类 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_cluster_structure_stratified_dotplot` | 可视化分析・可视化・统计・聚类 | Cluster structure - Stratified dot plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_cluster_structure_threshold_band` | 可视化分析・可视化・统计・聚类 | Cluster structure - Threshold band | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_cluster_structure_uncertainty_ribbon` | 可视化分析・可视化・统计・聚类 | Cluster structure - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_cluster_structure_violin_summary` | 可视化分析・可视化・统计・聚类・小提琴图・概览 | 小提琴图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_community_structure_annotated_reference_view` | 可视化分析・可视化・统计 | Community structure - Annotated reference view | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_community_structure_boxen_interval` | 可视化分析・可视化・统计 | Community structure - Boxen interval plot | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_community_structure_comparative_lollipop` | 可视化分析・可视化・统计 | Community structure - Comparative lollipop plot | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_community_structure_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_community_structure_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Community structure - Diagnostic panel | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_community_structure_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_community_structure_flow_transition_map` | 可视化分析・可视化・统计 | Community structure - Flow transition map | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_community_structure_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_community_structure_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_community_structure_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_community_structure_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_community_structure_mosaic_tile_view` | 可视化分析・可视化・统计 | Community structure - Mosaic tile view | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_community_structure_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_community_structure_qq_reference_plot` | 可视化分析・可视化・统计 | Community structure - Q-Q reference plot | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_community_structure_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_community_structure_raincloud_view` | 可视化分析・可视化・统计 | Community structure - Raincloud view | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_community_structure_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_community_structure_residual_annotation_map` | 可视化分析・可视化・统计 | Community structure - Residual annotation map | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_community_structure_slope_change_view` | 可视化分析・可视化・统计 | Community structure - Slope change view | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_community_structure_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_community_structure_stratified_dotplot` | 可视化分析・可视化・统计 | Community structure - Stratified dot plot | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_community_structure_threshold_band` | 可视化分析・可视化・统计 | Community structure - Threshold band | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_community_structure_uncertainty_ribbon` | 可视化分析・可视化・统计 | Community structure - Uncertainty ribbon | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_community_structure_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_confusion_error_profile_annotated_reference_view` | 可视化分析・可视化・统计・误差・画像 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_confusion_error_profile_boxen_interval` | 可视化分析・可视化・统计・误差・画像 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_confusion_error_profile_comparative_lollipop` | 可视化分析・可视化・统计・误差・画像 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_confusion_error_profile_density_ridge` | 可视化分析・可视化・统计・误差・画像・密度图 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_confusion_error_profile_diagnostic_panel` | 可视化分析・可视化・统计・误差・画像・诊断・面板 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_confusion_error_profile_ecdf_step_view` | 可视化分析・可视化・统计・误差・画像・经验分布图 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_confusion_error_profile_flow_transition_map` | 可视化分析・可视化・统计・误差・画像 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_confusion_error_profile_forest_interval_plot` | 可视化分析・可视化・统计・误差・画像・随机森林 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_confusion_error_profile_heatmap_matrix` | 可视化分析・可视化・统计・误差・画像・热力矩阵 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_confusion_error_profile_histogram_facets` | 可视化分析・可视化・统计・误差・画像・直方图 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_confusion_error_profile_map_choropleth_layer` | 可视化分析・可视化・统计・误差・画像・分级着色地图 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_confusion_error_profile_mosaic_tile_view` | 可视化分析・可视化・统计・误差・画像 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_confusion_error_profile_network_node_link` | 可视化分析・可视化・统计・误差・画像・网络 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_confusion_error_profile_qq_reference_plot` | 可视化分析・可视化・统计・误差・画像 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_confusion_error_profile_quantile_band` | 可视化分析・可视化・统计・误差・画像・分位数 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_confusion_error_profile_raincloud_view` | 可视化分析・可视化・统计・误差・画像 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_confusion_error_profile_rank_interval_plot` | 可视化分析・可视化・统计・误差・画像・排名 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_confusion_error_profile_residual_annotation_map` | 可视化分析・可视化・统计・误差・画像 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_confusion_error_profile_slope_change_view` | 可视化分析・可视化・统计・误差・画像 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_confusion_error_profile_small_multiple_grid` | 可视化分析・可视化・统计・误差・画像 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_confusion_error_profile_stratified_dotplot` | 可视化分析・可视化・统计・误差・画像 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_confusion_error_profile_threshold_band` | 可视化分析・可视化・统计・误差・画像 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_confusion_error_profile_uncertainty_ribbon` | 可视化分析・可视化・统计・误差・画像 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_confusion_error_profile_violin_summary` | 可视化分析・可视化・统计・误差・画像・小提琴图・概览 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_contingency_structure_annotated_reference_view` | 可视化分析・可视化・统计 | Contingency structure - Annotated reference view | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_contingency_structure_boxen_interval` | 可视化分析・可视化・统计 | Contingency structure - Boxen interval plot | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_contingency_structure_comparative_lollipop` | 可视化分析・可视化・统计 | Contingency structure - Comparative lollipop plot | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_contingency_structure_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_contingency_structure_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Contingency structure - Diagnostic panel | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_contingency_structure_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_contingency_structure_flow_transition_map` | 可视化分析・可视化・统计 | Contingency structure - Flow transition map | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_contingency_structure_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_contingency_structure_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_contingency_structure_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_contingency_structure_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_contingency_structure_mosaic_tile_view` | 可视化分析・可视化・统计 | Contingency structure - Mosaic tile view | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_contingency_structure_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_contingency_structure_qq_reference_plot` | 可视化分析・可视化・统计 | Contingency structure - Q-Q reference plot | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_contingency_structure_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_contingency_structure_raincloud_view` | 可视化分析・可视化・统计 | Contingency structure - Raincloud view | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_contingency_structure_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_contingency_structure_residual_annotation_map` | 可视化分析・可视化・统计 | Contingency structure - Residual annotation map | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_contingency_structure_slope_change_view` | 可视化分析・可视化・统计 | Contingency structure - Slope change view | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_contingency_structure_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_contingency_structure_stratified_dotplot` | 可视化分析・可视化・统计 | Contingency structure - Stratified dot plot | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_contingency_structure_threshold_band` | 可视化分析・可视化・统计 | Contingency structure - Threshold band | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_contingency_structure_uncertainty_ribbon` | 可视化分析・可视化・统计 | Contingency structure - Uncertainty ribbon | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_contingency_structure_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_correlation_structure_annotated_reference_view` | 可视化分析・可视化・统计・相关性 | 相关性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_correlation_structure_boxen_interval` | 可视化分析・可视化・统计・相关性 | 相关性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_correlation_structure_comparative_lollipop` | 可视化分析・可视化・统计・相关性 | 相关性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_correlation_structure_density_ridge` | 可视化分析・可视化・统计・相关性・密度图 | 相关性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_correlation_structure_diagnostic_panel` | 可视化分析・可视化・统计・相关性・诊断・面板 | 相关性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_correlation_structure_ecdf_step_view` | 可视化分析・可视化・统计・相关性・经验分布图 | 相关性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_correlation_structure_flow_transition_map` | 可视化分析・可视化・统计・相关性 | 相关性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_correlation_structure_forest_interval_plot` | 可视化分析・可视化・统计・相关性・随机森林 | 相关性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_correlation_structure_heatmap_matrix` | 可视化分析・可视化・统计・相关性・热力矩阵 | 相关性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_correlation_structure_histogram_facets` | 可视化分析・可视化・统计・相关性・直方图 | 相关性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_correlation_structure_map_choropleth_layer` | 可视化分析・可视化・统计・相关性・分级着色地图 | 相关性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_correlation_structure_mosaic_tile_view` | 可视化分析・可视化・统计・相关性 | 相关性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_correlation_structure_network_node_link` | 可视化分析・可视化・统计・相关性・网络 | 相关性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_correlation_structure_qq_reference_plot` | 可视化分析・可视化・统计・相关性 | 相关性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_correlation_structure_quantile_band` | 可视化分析・可视化・统计・相关性・分位数 | 相关性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_correlation_structure_raincloud_view` | 可视化分析・可视化・统计・相关性 | 相关性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_correlation_structure_rank_interval_plot` | 可视化分析・可视化・统计・相关性・排名 | 相关性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_correlation_structure_residual_annotation_map` | 可视化分析・可视化・统计・相关性 | 相关性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_correlation_structure_slope_change_view` | 可视化分析・可视化・统计・相关性 | 相关性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_correlation_structure_small_multiple_grid` | 可视化分析・可视化・统计・相关性 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_correlation_structure_stratified_dotplot` | 可视化分析・可视化・统计・相关性 | 相关性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_correlation_structure_threshold_band` | 可视化分析・可视化・统计・相关性 | 相关性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_correlation_structure_uncertainty_ribbon` | 可视化分析・可视化・统计・相关性 | 相关性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_correlation_structure_violin_summary` | 可视化分析・可视化・统计・相关性・小提琴图・概览 | 相关性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_counterfactual_contrast_annotated_reference_view` | 可视化分析・可视化・统计 | Counterfactual contrast - Annotated reference view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_counterfactual_contrast_boxen_interval` | 可视化分析・可视化・统计 | Counterfactual contrast - Boxen interval plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_counterfactual_contrast_comparative_lollipop` | 可视化分析・可视化・统计 | Counterfactual contrast - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_counterfactual_contrast_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_counterfactual_contrast_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Counterfactual contrast - Diagnostic panel | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_counterfactual_contrast_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_counterfactual_contrast_flow_transition_map` | 可视化分析・可视化・统计 | Counterfactual contrast - Flow transition map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_counterfactual_contrast_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_counterfactual_contrast_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_counterfactual_contrast_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_counterfactual_contrast_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_counterfactual_contrast_mosaic_tile_view` | 可视化分析・可视化・统计 | Counterfactual contrast - Mosaic tile view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_counterfactual_contrast_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_counterfactual_contrast_qq_reference_plot` | 可视化分析・可视化・统计 | Counterfactual contrast - Q-Q reference plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_counterfactual_contrast_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_counterfactual_contrast_raincloud_view` | 可视化分析・可视化・统计 | Counterfactual contrast - Raincloud view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_counterfactual_contrast_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_counterfactual_contrast_residual_annotation_map` | 可视化分析・可视化・统计 | Counterfactual contrast - Residual annotation map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_counterfactual_contrast_slope_change_view` | 可视化分析・可视化・统计 | Counterfactual contrast - Slope change view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_counterfactual_contrast_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_counterfactual_contrast_stratified_dotplot` | 可视化分析・可视化・统计 | Counterfactual contrast - Stratified dot plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_counterfactual_contrast_threshold_band` | 可视化分析・可视化・统计 | Counterfactual contrast - Threshold band | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_counterfactual_contrast_uncertainty_ribbon` | 可视化分析・可视化・统计 | Counterfactual contrast - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_counterfactual_contrast_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_quality_annotated_reference_view` | 可视化分析・可视化・统计・数据・质量 | Data quality profile - Annotated reference view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_quality_boxen_interval` | 可视化分析・可视化・统计・数据・质量 | Data quality profile - Boxen interval plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_quality_comparative_lollipop` | 可视化分析・可视化・统计・数据・质量 | Data quality profile - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_quality_density_ridge` | 可视化分析・可视化・统计・数据・质量・密度图 | 密度图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_quality_diagnostic_panel` | 可视化分析・可视化・统计・数据・质量・诊断・面板 | Data quality profile - Diagnostic panel | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_quality_ecdf_step_view` | 可视化分析・可视化・统计・数据・质量・经验分布图 | 经验分布图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_quality_flow_transition_map` | 可视化分析・可视化・统计・数据・质量 | Data quality profile - Flow transition map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_quality_forest_interval_plot` | 可视化分析・可视化・统计・数据・质量・随机森林 | 随机森林 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_quality_heatmap_matrix` | 可视化分析・可视化・统计・数据・质量・热力矩阵 | 热力矩阵 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_quality_histogram_facets` | 可视化分析・可视化・统计・数据・质量・直方图 | 直方图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_quality_map_choropleth_layer` | 可视化分析・可视化・统计・数据・质量・分级着色地图 | 分级着色地图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_quality_mosaic_tile_view` | 可视化分析・可视化・统计・数据・质量 | Data quality profile - Mosaic tile view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_quality_network_node_link` | 可视化分析・可视化・统计・数据・质量・网络 | 关系网络 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_quality_qq_reference_plot` | 可视化分析・可视化・统计・数据・质量 | Data quality profile - Q-Q reference plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_quality_quantile_band` | 可视化分析・可视化・统计・数据・质量・分位数 | 分位数 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_quality_raincloud_view` | 可视化分析・可视化・统计・数据・质量 | Data quality profile - Raincloud view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_quality_rank_interval_plot` | 可视化分析・可视化・统计・数据・质量・排名 | 排名 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_quality_residual_annotation_map` | 可视化分析・可视化・统计・数据・质量 | Data quality profile - Residual annotation map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_quality_slope_change_view` | 可视化分析・可视化・统计・数据・质量 | Data quality profile - Slope change view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_quality_small_multiple_grid` | 可视化分析・可视化・统计・数据・质量 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_quality_stratified_dotplot` | 可视化分析・可视化・统计・数据・质量 | Data quality profile - Stratified dot plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_quality_threshold_band` | 可视化分析・可视化・统计・数据・质量 | Data quality profile - Threshold band | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_quality_uncertainty_ribbon` | 可视化分析・可视化・统计・数据・质量 | Data quality profile - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_quality_violin_summary` | 可视化分析・可视化・统计・数据・质量・小提琴图・概览 | 小提琴图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_validation_rules_annotated_reference_view` | 可视化分析・可视化・统计・数据・校验 | Data validation rules - Annotated reference view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_validation_rules_boxen_interval` | 可视化分析・可视化・统计・数据・校验 | Data validation rules - Boxen interval plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_validation_rules_comparative_lollipop` | 可视化分析・可视化・统计・数据・校验 | Data validation rules - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_validation_rules_density_ridge` | 可视化分析・可视化・统计・数据・校验・密度图 | 密度图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_validation_rules_diagnostic_panel` | 可视化分析・可视化・统计・数据・校验・诊断・面板 | Data validation rules - Diagnostic panel | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_validation_rules_ecdf_step_view` | 可视化分析・可视化・统计・数据・校验・经验分布图 | 经验分布图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_validation_rules_flow_transition_map` | 可视化分析・可视化・统计・数据・校验 | Data validation rules - Flow transition map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_validation_rules_forest_interval_plot` | 可视化分析・可视化・统计・数据・校验・随机森林 | 随机森林 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_validation_rules_heatmap_matrix` | 可视化分析・可视化・统计・数据・校验・热力矩阵 | 热力矩阵 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_validation_rules_histogram_facets` | 可视化分析・可视化・统计・数据・校验・直方图 | 直方图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_validation_rules_map_choropleth_layer` | 可视化分析・可视化・统计・数据・校验・分级着色地图 | 分级着色地图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_validation_rules_mosaic_tile_view` | 可视化分析・可视化・统计・数据・校验 | Data validation rules - Mosaic tile view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_validation_rules_network_node_link` | 可视化分析・可视化・统计・数据・校验・网络 | 关系网络 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_validation_rules_qq_reference_plot` | 可视化分析・可视化・统计・数据・校验 | Data validation rules - Q-Q reference plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_validation_rules_quantile_band` | 可视化分析・可视化・统计・数据・校验・分位数 | 分位数 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_validation_rules_raincloud_view` | 可视化分析・可视化・统计・数据・校验 | Data validation rules - Raincloud view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_validation_rules_rank_interval_plot` | 可视化分析・可视化・统计・数据・校验・排名 | 排名 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_validation_rules_residual_annotation_map` | 可视化分析・可视化・统计・数据・校验 | Data validation rules - Residual annotation map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_validation_rules_slope_change_view` | 可视化分析・可视化・统计・数据・校验 | Data validation rules - Slope change view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_validation_rules_small_multiple_grid` | 可视化分析・可视化・统计・数据・校验 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_validation_rules_stratified_dotplot` | 可视化分析・可视化・统计・数据・校验 | Data validation rules - Stratified dot plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_validation_rules_threshold_band` | 可视化分析・可视化・统计・数据・校验 | Data validation rules - Threshold band | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_validation_rules_uncertainty_ribbon` | 可视化分析・可视化・统计・数据・校验 | Data validation rules - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_data_validation_rules_violin_summary` | 可视化分析・可视化・统计・数据・校验・小提琴图・概览 | 小提琴图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_defect_classification_annotated_reference_view` | 可视化分析・可视化・统计 | Defect classification - Annotated reference view | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_defect_classification_boxen_interval` | 可视化分析・可视化・统计 | Defect classification - Boxen interval plot | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_defect_classification_comparative_lollipop` | 可视化分析・可视化・统计 | Defect classification - Comparative lollipop plot | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_defect_classification_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_defect_classification_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Defect classification - Diagnostic panel | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_defect_classification_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_defect_classification_flow_transition_map` | 可视化分析・可视化・统计 | Defect classification - Flow transition map | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_defect_classification_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_defect_classification_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_defect_classification_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_defect_classification_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_defect_classification_mosaic_tile_view` | 可视化分析・可视化・统计 | Defect classification - Mosaic tile view | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_defect_classification_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_defect_classification_qq_reference_plot` | 可视化分析・可视化・统计 | Defect classification - Q-Q reference plot | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_defect_classification_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_defect_classification_raincloud_view` | 可视化分析・可视化・统计 | Defect classification - Raincloud view | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_defect_classification_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_defect_classification_residual_annotation_map` | 可视化分析・可视化・统计 | Defect classification - Residual annotation map | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_defect_classification_slope_change_view` | 可视化分析・可视化・统计 | Defect classification - Slope change view | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_defect_classification_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_defect_classification_stratified_dotplot` | 可视化分析・可视化・统计 | Defect classification - Stratified dot plot | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_defect_classification_threshold_band` | 可视化分析・可视化・统计 | Defect classification - Threshold band | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_defect_classification_uncertainty_ribbon` | 可视化分析・可视化・统计 | Defect classification - Uncertainty ribbon | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_defect_classification_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_dimension_reduction_annotated_reference_view` | 可视化分析・可视化・统计 | Dimension reduction - Annotated reference view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_dimension_reduction_boxen_interval` | 可视化分析・可视化・统计 | Dimension reduction - Boxen interval plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_dimension_reduction_comparative_lollipop` | 可视化分析・可视化・统计 | Dimension reduction - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_dimension_reduction_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_dimension_reduction_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Dimension reduction - Diagnostic panel | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_dimension_reduction_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_dimension_reduction_flow_transition_map` | 可视化分析・可视化・统计 | Dimension reduction - Flow transition map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_dimension_reduction_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_dimension_reduction_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_dimension_reduction_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_dimension_reduction_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_dimension_reduction_mosaic_tile_view` | 可视化分析・可视化・统计 | Dimension reduction - Mosaic tile view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_dimension_reduction_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_dimension_reduction_qq_reference_plot` | 可视化分析・可视化・统计 | Dimension reduction - Q-Q reference plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_dimension_reduction_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_dimension_reduction_raincloud_view` | 可视化分析・可视化・统计 | Dimension reduction - Raincloud view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_dimension_reduction_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_dimension_reduction_residual_annotation_map` | 可视化分析・可视化・统计 | Dimension reduction - Residual annotation map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_dimension_reduction_slope_change_view` | 可视化分析・可视化・统计 | Dimension reduction - Slope change view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_dimension_reduction_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_dimension_reduction_stratified_dotplot` | 可视化分析・可视化・统计 | Dimension reduction - Stratified dot plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_dimension_reduction_threshold_band` | 可视化分析・可视化・统计 | Dimension reduction - Threshold band | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_dimension_reduction_uncertainty_ribbon` | 可视化分析・可视化・统计 | Dimension reduction - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_dimension_reduction_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_discontinuity_window_annotated_reference_view` | 可视化分析・可视化・统计 | Discontinuity window - Annotated reference view | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_discontinuity_window_boxen_interval` | 可视化分析・可视化・统计 | Discontinuity window - Boxen interval plot | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_discontinuity_window_comparative_lollipop` | 可视化分析・可视化・统计 | Discontinuity window - Comparative lollipop plot | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_discontinuity_window_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_discontinuity_window_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Discontinuity window - Diagnostic panel | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_discontinuity_window_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_discontinuity_window_flow_transition_map` | 可视化分析・可视化・统计 | Discontinuity window - Flow transition map | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_discontinuity_window_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_discontinuity_window_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_discontinuity_window_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_discontinuity_window_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_discontinuity_window_mosaic_tile_view` | 可视化分析・可视化・统计 | Discontinuity window - Mosaic tile view | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_discontinuity_window_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_discontinuity_window_qq_reference_plot` | 可视化分析・可视化・统计 | Discontinuity window - Q-Q reference plot | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_discontinuity_window_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_discontinuity_window_raincloud_view` | 可视化分析・可视化・统计 | Discontinuity window - Raincloud view | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_discontinuity_window_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_discontinuity_window_residual_annotation_map` | 可视化分析・可视化・统计 | Discontinuity window - Residual annotation map | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_discontinuity_window_slope_change_view` | 可视化分析・可视化・统计 | Discontinuity window - Slope change view | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_discontinuity_window_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_discontinuity_window_stratified_dotplot` | 可视化分析・可视化・统计 | Discontinuity window - Stratified dot plot | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_discontinuity_window_threshold_band` | 可视化分析・可视化・统计 | Discontinuity window - Threshold band | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_discontinuity_window_uncertainty_ribbon` | 可视化分析・可视化・统计 | Discontinuity window - Uncertainty ribbon | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_discontinuity_window_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_comparison_annotated_reference_view` | 可视化分析・可视化・统计・分布 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_comparison_boxen_interval` | 可视化分析・可视化・统计・分布 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_comparison_comparative_lollipop` | 可视化分析・可视化・统计・分布 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_comparison_density_ridge` | 可视化分析・可视化・统计・分布・密度图 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_comparison_diagnostic_panel` | 可视化分析・可视化・统计・分布・诊断・面板 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_comparison_ecdf_step_view` | 可视化分析・可视化・统计・分布・经验分布图 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_comparison_flow_transition_map` | 可视化分析・可视化・统计・分布 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_comparison_forest_interval_plot` | 可视化分析・可视化・统计・分布・随机森林 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_comparison_heatmap_matrix` | 可视化分析・可视化・统计・分布・热力矩阵 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_comparison_histogram_facets` | 可视化分析・可视化・统计・分布・直方图 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_comparison_map_choropleth_layer` | 可视化分析・可视化・统计・分布・分级着色地图 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_comparison_mosaic_tile_view` | 可视化分析・可视化・统计・分布 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_comparison_network_node_link` | 可视化分析・可视化・统计・分布・网络 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_comparison_qq_reference_plot` | 可视化分析・可视化・统计・分布 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_comparison_quantile_band` | 可视化分析・可视化・统计・分布・分位数 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_comparison_raincloud_view` | 可视化分析・可视化・统计・分布 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_comparison_rank_interval_plot` | 可视化分析・可视化・统计・分布・排名 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_comparison_residual_annotation_map` | 可视化分析・可视化・统计・分布 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_comparison_slope_change_view` | 可视化分析・可视化・统计・分布 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_comparison_small_multiple_grid` | 可视化分析・可视化・统计・分布 | 小多图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_comparison_stratified_dotplot` | 可视化分析・可视化・统计・分布 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_comparison_threshold_band` | 可视化分析・可视化・统计・分布 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_comparison_uncertainty_ribbon` | 可视化分析・可视化・统计・分布 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_comparison_violin_summary` | 可视化分析・可视化・统计・分布・小提琴图・概览 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_shape_annotated_reference_view` | 可视化分析・可视化・统计・分布 | 分布 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_shape_boxen_interval` | 可视化分析・可视化・统计・分布 | 分布 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_shape_comparative_lollipop` | 可视化分析・可视化・统计・分布 | 分布 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_shape_density_ridge` | 可视化分析・可视化・统计・分布・密度图 | 分布 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_shape_diagnostic_panel` | 可视化分析・可视化・统计・分布・诊断・面板 | 分布 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_shape_ecdf_step_view` | 可视化分析・可视化・统计・分布・经验分布图 | 分布 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_shape_flow_transition_map` | 可视化分析・可视化・统计・分布 | 分布 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_shape_forest_interval_plot` | 可视化分析・可视化・统计・分布・随机森林 | 分布 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_shape_heatmap_matrix` | 可视化分析・可视化・统计・分布・热力矩阵 | 分布 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_shape_histogram_facets` | 可视化分析・可视化・统计・分布・直方图 | 分布 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_shape_map_choropleth_layer` | 可视化分析・可视化・统计・分布・分级着色地图 | 分布 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_shape_mosaic_tile_view` | 可视化分析・可视化・统计・分布 | 分布 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_shape_network_node_link` | 可视化分析・可视化・统计・分布・网络 | 分布 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_shape_qq_reference_plot` | 可视化分析・可视化・统计・分布 | 分布 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_shape_quantile_band` | 可视化分析・可视化・统计・分布・分位数 | 分布 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_shape_raincloud_view` | 可视化分析・可视化・统计・分布 | 分布 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_shape_rank_interval_plot` | 可视化分析・可视化・统计・分布・排名 | 分布 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_shape_residual_annotation_map` | 可视化分析・可视化・统计・分布 | 分布 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_shape_slope_change_view` | 可视化分析・可视化・统计・分布 | 分布 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_shape_small_multiple_grid` | 可视化分析・可视化・统计・分布 | 小多图 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_shape_stratified_dotplot` | 可视化分析・可视化・统计・分布 | 分布 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_shape_threshold_band` | 可视化分析・可视化・统计・分布 | 分布 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_shape_uncertainty_ribbon` | 可视化分析・可视化・统计・分布 | 分布 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_distribution_shape_violin_summary` | 可视化分析・可视化・统计・分布・小提琴图・概览 | 分布 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_dose_response_annotated_reference_view` | 可视化分析・可视化・统计 | Dose response - Annotated reference view | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_dose_response_boxen_interval` | 可视化分析・可视化・统计 | Dose response - Boxen interval plot | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_dose_response_comparative_lollipop` | 可视化分析・可视化・统计 | Dose response - Comparative lollipop plot | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_dose_response_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_dose_response_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Dose response - Diagnostic panel | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_dose_response_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_dose_response_flow_transition_map` | 可视化分析・可视化・统计 | Dose response - Flow transition map | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_dose_response_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_dose_response_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_dose_response_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_dose_response_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_dose_response_mosaic_tile_view` | 可视化分析・可视化・统计 | Dose response - Mosaic tile view | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_dose_response_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_dose_response_qq_reference_plot` | 可视化分析・可视化・统计 | Dose response - Q-Q reference plot | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_dose_response_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_dose_response_raincloud_view` | 可视化分析・可视化・统计 | Dose response - Raincloud view | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_dose_response_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_dose_response_residual_annotation_map` | 可视化分析・可视化・统计 | Dose response - Residual annotation map | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_dose_response_slope_change_view` | 可视化分析・可视化・统计 | Dose response - Slope change view | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_dose_response_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_dose_response_stratified_dotplot` | 可视化分析・可视化・统计 | Dose response - Stratified dot plot | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_dose_response_threshold_band` | 可视化分析・可视化・统计 | Dose response - Threshold band | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_dose_response_uncertainty_ribbon` | 可视化分析・可视化・统计 | Dose response - Uncertainty ribbon | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_dose_response_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_duplicate_record_structure_annotated_reference_view` | 可视化分析・可视化・统计 | Duplicate record structure - Annotated reference view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_duplicate_record_structure_boxen_interval` | 可视化分析・可视化・统计 | Duplicate record structure - Boxen interval plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_duplicate_record_structure_comparative_lollipop` | 可视化分析・可视化・统计 | Duplicate record structure - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_duplicate_record_structure_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_duplicate_record_structure_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Duplicate record structure - Diagnostic panel | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_duplicate_record_structure_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_duplicate_record_structure_flow_transition_map` | 可视化分析・可视化・统计 | Duplicate record structure - Flow transition map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_duplicate_record_structure_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_duplicate_record_structure_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_duplicate_record_structure_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_duplicate_record_structure_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_duplicate_record_structure_mosaic_tile_view` | 可视化分析・可视化・统计 | Duplicate record structure - Mosaic tile view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_duplicate_record_structure_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_duplicate_record_structure_qq_reference_plot` | 可视化分析・可视化・统计 | Duplicate record structure - Q-Q reference plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_duplicate_record_structure_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_duplicate_record_structure_raincloud_view` | 可视化分析・可视化・统计 | Duplicate record structure - Raincloud view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_duplicate_record_structure_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_duplicate_record_structure_residual_annotation_map` | 可视化分析・可视化・统计 | Duplicate record structure - Residual annotation map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_duplicate_record_structure_slope_change_view` | 可视化分析・可视化・统计 | Duplicate record structure - Slope change view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_duplicate_record_structure_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_duplicate_record_structure_stratified_dotplot` | 可视化分析・可视化・统计 | Duplicate record structure - Stratified dot plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_duplicate_record_structure_threshold_band` | 可视化分析・可视化・统计 | Duplicate record structure - Threshold band | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_duplicate_record_structure_uncertainty_ribbon` | 可视化分析・可视化・统计 | Duplicate record structure - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_duplicate_record_structure_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_categorical_overview_annotated_reference_view` | 可视化分析・可视化・统计 | EDA categorical overview - Annotated reference view | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_categorical_overview_boxen_interval` | 可视化分析・可视化・统计 | EDA categorical overview - Boxen interval plot | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_categorical_overview_comparative_lollipop` | 可视化分析・可视化・统计 | EDA categorical overview - Comparative lollipop plot | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_categorical_overview_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_categorical_overview_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | EDA categorical overview - Diagnostic panel | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_categorical_overview_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_categorical_overview_flow_transition_map` | 可视化分析・可视化・统计 | EDA categorical overview - Flow transition map | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_categorical_overview_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_categorical_overview_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_categorical_overview_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_categorical_overview_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_categorical_overview_mosaic_tile_view` | 可视化分析・可视化・统计 | EDA categorical overview - Mosaic tile view | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_categorical_overview_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_categorical_overview_qq_reference_plot` | 可视化分析・可视化・统计 | EDA categorical overview - Q-Q reference plot | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_categorical_overview_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_categorical_overview_raincloud_view` | 可视化分析・可视化・统计 | EDA categorical overview - Raincloud view | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_categorical_overview_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_categorical_overview_residual_annotation_map` | 可视化分析・可视化・统计 | EDA categorical overview - Residual annotation map | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_categorical_overview_slope_change_view` | 可视化分析・可视化・统计 | EDA categorical overview - Slope change view | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_categorical_overview_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_categorical_overview_stratified_dotplot` | 可视化分析・可视化・统计 | EDA categorical overview - Stratified dot plot | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_categorical_overview_threshold_band` | 可视化分析・可视化・统计 | EDA categorical overview - Threshold band | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_categorical_overview_uncertainty_ribbon` | 可视化分析・可视化・统计 | EDA categorical overview - Uncertainty ribbon | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_categorical_overview_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_numeric_overview_annotated_reference_view` | 可视化分析・可视化・统计 | EDA numeric overview - Annotated reference view | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_numeric_overview_boxen_interval` | 可视化分析・可视化・统计 | EDA numeric overview - Boxen interval plot | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_numeric_overview_comparative_lollipop` | 可视化分析・可视化・统计 | EDA numeric overview - Comparative lollipop plot | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_numeric_overview_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_numeric_overview_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | EDA numeric overview - Diagnostic panel | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_numeric_overview_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_numeric_overview_flow_transition_map` | 可视化分析・可视化・统计 | EDA numeric overview - Flow transition map | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_numeric_overview_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_numeric_overview_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_numeric_overview_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_numeric_overview_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_numeric_overview_mosaic_tile_view` | 可视化分析・可视化・统计 | EDA numeric overview - Mosaic tile view | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_numeric_overview_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_numeric_overview_qq_reference_plot` | 可视化分析・可视化・统计 | EDA numeric overview - Q-Q reference plot | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_numeric_overview_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_numeric_overview_raincloud_view` | 可视化分析・可视化・统计 | EDA numeric overview - Raincloud view | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_numeric_overview_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_numeric_overview_residual_annotation_map` | 可视化分析・可视化・统计 | EDA numeric overview - Residual annotation map | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_numeric_overview_slope_change_view` | 可视化分析・可视化・统计 | EDA numeric overview - Slope change view | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_numeric_overview_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_numeric_overview_stratified_dotplot` | 可视化分析・可视化・统计 | EDA numeric overview - Stratified dot plot | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_numeric_overview_threshold_band` | 可视化分析・可视化・统计 | EDA numeric overview - Threshold band | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_numeric_overview_uncertainty_ribbon` | 可视化分析・可视化・统计 | EDA numeric overview - Uncertainty ribbon | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_eda_numeric_overview_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_education_growth_annotated_reference_view` | 可视化分析・可视化・统计 | Education growth - Annotated reference view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_education_growth_boxen_interval` | 可视化分析・可视化・统计 | Education growth - Boxen interval plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_education_growth_comparative_lollipop` | 可视化分析・可视化・统计 | Education growth - Comparative lollipop plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_education_growth_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_education_growth_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Education growth - Diagnostic panel | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_education_growth_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_education_growth_flow_transition_map` | 可视化分析・可视化・统计 | Education growth - Flow transition map | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_education_growth_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_education_growth_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_education_growth_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_education_growth_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_education_growth_mosaic_tile_view` | 可视化分析・可视化・统计 | Education growth - Mosaic tile view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_education_growth_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_education_growth_qq_reference_plot` | 可视化分析・可视化・统计 | Education growth - Q-Q reference plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_education_growth_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_education_growth_raincloud_view` | 可视化分析・可视化・统计 | Education growth - Raincloud view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_education_growth_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_education_growth_residual_annotation_map` | 可视化分析・可视化・统计 | Education growth - Residual annotation map | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_education_growth_slope_change_view` | 可视化分析・可视化・统计 | Education growth - Slope change view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_education_growth_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_education_growth_stratified_dotplot` | 可视化分析・可视化・统计 | Education growth - Stratified dot plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_education_growth_threshold_band` | 可视化分析・可视化・统计 | Education growth - Threshold band | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_education_growth_uncertainty_ribbon` | 可视化分析・可视化・统计 | Education growth - Uncertainty ribbon | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_education_growth_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_effect_size_annotated_reference_view` | 可视化分析・可视化・统计・效应 | Effect size view - Annotated reference view | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_effect_size_boxen_interval` | 可视化分析・可视化・统计・效应 | Effect size view - Boxen interval plot | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_effect_size_comparative_lollipop` | 可视化分析・可视化・统计・效应 | Effect size view - Comparative lollipop plot | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_effect_size_density_ridge` | 可视化分析・可视化・统计・效应・密度图 | 密度图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_effect_size_diagnostic_panel` | 可视化分析・可视化・统计・效应・诊断・面板 | Effect size view - Diagnostic panel | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_effect_size_ecdf_step_view` | 可视化分析・可视化・统计・效应・经验分布图 | 经验分布图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_effect_size_flow_transition_map` | 可视化分析・可视化・统计・效应 | Effect size view - Flow transition map | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_effect_size_forest_interval_plot` | 可视化分析・可视化・统计・效应・随机森林 | 随机森林 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_effect_size_heatmap_matrix` | 可视化分析・可视化・统计・效应・热力矩阵 | 热力矩阵 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_effect_size_histogram_facets` | 可视化分析・可视化・统计・效应・直方图 | 直方图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_effect_size_map_choropleth_layer` | 可视化分析・可视化・统计・效应・分级着色地图 | 分级着色地图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_effect_size_mosaic_tile_view` | 可视化分析・可视化・统计・效应 | Effect size view - Mosaic tile view | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_effect_size_network_node_link` | 可视化分析・可视化・统计・效应・网络 | 关系网络 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_effect_size_qq_reference_plot` | 可视化分析・可视化・统计・效应 | Effect size view - Q-Q reference plot | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_effect_size_quantile_band` | 可视化分析・可视化・统计・效应・分位数 | 分位数 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_effect_size_raincloud_view` | 可视化分析・可视化・统计・效应 | Effect size view - Raincloud view | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_effect_size_rank_interval_plot` | 可视化分析・可视化・统计・效应・排名 | 排名 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_effect_size_residual_annotation_map` | 可视化分析・可视化・统计・效应 | Effect size view - Residual annotation map | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_effect_size_slope_change_view` | 可视化分析・可视化・统计・效应 | Effect size view - Slope change view | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_effect_size_small_multiple_grid` | 可视化分析・可视化・统计・效应 | 小多图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_effect_size_stratified_dotplot` | 可视化分析・可视化・统计・效应 | Effect size view - Stratified dot plot | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_effect_size_threshold_band` | 可视化分析・可视化・统计・效应 | Effect size view - Threshold band | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_effect_size_uncertainty_ribbon` | 可视化分析・可视化・统计・效应 | Effect size view - Uncertainty ribbon | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_effect_size_violin_summary` | 可视化分析・可视化・统计・效应・小提琴图・概览 | 小提琴图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_environmental_exposure_annotated_reference_view` | 可视化分析・可视化・统计 | Environmental exposure - Annotated reference view | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_environmental_exposure_boxen_interval` | 可视化分析・可视化・统计 | Environmental exposure - Boxen interval plot | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_environmental_exposure_comparative_lollipop` | 可视化分析・可视化・统计 | Environmental exposure - Comparative lollipop plot | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_environmental_exposure_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_environmental_exposure_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Environmental exposure - Diagnostic panel | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_environmental_exposure_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_environmental_exposure_flow_transition_map` | 可视化分析・可视化・统计 | Environmental exposure - Flow transition map | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_environmental_exposure_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_environmental_exposure_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_environmental_exposure_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_environmental_exposure_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_environmental_exposure_mosaic_tile_view` | 可视化分析・可视化・统计 | Environmental exposure - Mosaic tile view | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_environmental_exposure_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_environmental_exposure_qq_reference_plot` | 可视化分析・可视化・统计 | Environmental exposure - Q-Q reference plot | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_environmental_exposure_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_environmental_exposure_raincloud_view` | 可视化分析・可视化・统计 | Environmental exposure - Raincloud view | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_environmental_exposure_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_environmental_exposure_residual_annotation_map` | 可视化分析・可视化・统计 | Environmental exposure - Residual annotation map | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_environmental_exposure_slope_change_view` | 可视化分析・可视化・统计 | Environmental exposure - Slope change view | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_environmental_exposure_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_environmental_exposure_stratified_dotplot` | 可视化分析・可视化・统计 | Environmental exposure - Stratified dot plot | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_environmental_exposure_threshold_band` | 可视化分析・可视化・统计 | Environmental exposure - Threshold band | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_environmental_exposure_uncertainty_ribbon` | 可视化分析・可视化・统计 | Environmental exposure - Uncertainty ribbon | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_environmental_exposure_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_epidemiology_cluster_annotated_reference_view` | 可视化分析・可视化・统计・聚类 | Epidemiology cluster - Annotated reference view | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_epidemiology_cluster_boxen_interval` | 可视化分析・可视化・统计・聚类 | Epidemiology cluster - Boxen interval plot | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_epidemiology_cluster_comparative_lollipop` | 可视化分析・可视化・统计・聚类 | Epidemiology cluster - Comparative lollipop plot | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_epidemiology_cluster_density_ridge` | 可视化分析・可视化・统计・聚类・密度图 | 密度图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_epidemiology_cluster_diagnostic_panel` | 可视化分析・可视化・统计・聚类・诊断・面板 | Epidemiology cluster - Diagnostic panel | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_epidemiology_cluster_ecdf_step_view` | 可视化分析・可视化・统计・聚类・经验分布图 | 经验分布图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_epidemiology_cluster_flow_transition_map` | 可视化分析・可视化・统计・聚类 | Epidemiology cluster - Flow transition map | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_epidemiology_cluster_forest_interval_plot` | 可视化分析・可视化・统计・聚类・随机森林 | 随机森林 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_epidemiology_cluster_heatmap_matrix` | 可视化分析・可视化・统计・聚类・热力矩阵 | 热力矩阵 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_epidemiology_cluster_histogram_facets` | 可视化分析・可视化・统计・聚类・直方图 | 直方图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_epidemiology_cluster_map_choropleth_layer` | 可视化分析・可视化・统计・聚类・分级着色地图 | 分级着色地图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_epidemiology_cluster_mosaic_tile_view` | 可视化分析・可视化・统计・聚类 | Epidemiology cluster - Mosaic tile view | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_epidemiology_cluster_network_node_link` | 可视化分析・可视化・统计・聚类・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_epidemiology_cluster_qq_reference_plot` | 可视化分析・可视化・统计・聚类 | Epidemiology cluster - Q-Q reference plot | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_epidemiology_cluster_quantile_band` | 可视化分析・可视化・统计・聚类・分位数 | 分位数 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_epidemiology_cluster_raincloud_view` | 可视化分析・可视化・统计・聚类 | Epidemiology cluster - Raincloud view | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_epidemiology_cluster_rank_interval_plot` | 可视化分析・可视化・统计・聚类・排名 | 排名 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_epidemiology_cluster_residual_annotation_map` | 可视化分析・可视化・统计・聚类 | Epidemiology cluster - Residual annotation map | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_epidemiology_cluster_slope_change_view` | 可视化分析・可视化・统计・聚类 | Epidemiology cluster - Slope change view | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_epidemiology_cluster_small_multiple_grid` | 可视化分析・可视化・统计・聚类 | 小多图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_epidemiology_cluster_stratified_dotplot` | 可视化分析・可视化・统计・聚类 | Epidemiology cluster - Stratified dot plot | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_epidemiology_cluster_threshold_band` | 可视化分析・可视化・统计・聚类 | Epidemiology cluster - Threshold band | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_epidemiology_cluster_uncertainty_ribbon` | 可视化分析・可视化・统计・聚类 | Epidemiology cluster - Uncertainty ribbon | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_epidemiology_cluster_violin_summary` | 可视化分析・可视化・统计・聚类・小提琴图・概览 | 小提琴图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_power_annotated_reference_view` | 可视化分析・可视化・统计・实验 | Experiment power - Annotated reference view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_power_boxen_interval` | 可视化分析・可视化・统计・实验 | Experiment power - Boxen interval plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_power_comparative_lollipop` | 可视化分析・可视化・统计・实验 | Experiment power - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_power_density_ridge` | 可视化分析・可视化・统计・实验・密度图 | 密度图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_power_diagnostic_panel` | 可视化分析・可视化・统计・实验・诊断・面板 | Experiment power - Diagnostic panel | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_power_ecdf_step_view` | 可视化分析・可视化・统计・实验・经验分布图 | 经验分布图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_power_flow_transition_map` | 可视化分析・可视化・统计・实验 | Experiment power - Flow transition map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_power_forest_interval_plot` | 可视化分析・可视化・统计・实验・随机森林 | 随机森林 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_power_heatmap_matrix` | 可视化分析・可视化・统计・实验・热力矩阵 | 热力矩阵 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_power_histogram_facets` | 可视化分析・可视化・统计・实验・直方图 | 直方图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_power_map_choropleth_layer` | 可视化分析・可视化・统计・实验・分级着色地图 | 分级着色地图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_power_mosaic_tile_view` | 可视化分析・可视化・统计・实验 | Experiment power - Mosaic tile view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_power_network_node_link` | 可视化分析・可视化・统计・实验・网络 | 关系网络 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_power_qq_reference_plot` | 可视化分析・可视化・统计・实验 | Experiment power - Q-Q reference plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_power_quantile_band` | 可视化分析・可视化・统计・实验・分位数 | 分位数 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_power_raincloud_view` | 可视化分析・可视化・统计・实验 | Experiment power - Raincloud view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_power_rank_interval_plot` | 可视化分析・可视化・统计・实验・排名 | 排名 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_power_residual_annotation_map` | 可视化分析・可视化・统计・实验 | Experiment power - Residual annotation map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_power_slope_change_view` | 可视化分析・可视化・统计・实验 | Experiment power - Slope change view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_power_small_multiple_grid` | 可视化分析・可视化・统计・实验 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_power_stratified_dotplot` | 可视化分析・可视化・统计・实验 | Experiment power - Stratified dot plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_power_threshold_band` | 可视化分析・可视化・统计・实验 | Experiment power - Threshold band | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_power_uncertainty_ribbon` | 可视化分析・可视化・统计・实验 | Experiment power - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_power_violin_summary` | 可视化分析・可视化・统计・实验・小提琴图・概览 | 小提琴图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_response_annotated_reference_view` | 可视化分析・可视化・统计・实验 | Experiment response - Annotated reference view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_response_boxen_interval` | 可视化分析・可视化・统计・实验 | Experiment response - Boxen interval plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_response_comparative_lollipop` | 可视化分析・可视化・统计・实验 | Experiment response - Comparative lollipop plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_response_density_ridge` | 可视化分析・可视化・统计・实验・密度图 | 密度图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_response_diagnostic_panel` | 可视化分析・可视化・统计・实验・诊断・面板 | Experiment response - Diagnostic panel | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_response_ecdf_step_view` | 可视化分析・可视化・统计・实验・经验分布图 | 经验分布图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_response_flow_transition_map` | 可视化分析・可视化・统计・实验 | Experiment response - Flow transition map | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_response_forest_interval_plot` | 可视化分析・可视化・统计・实验・随机森林 | 随机森林 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_response_heatmap_matrix` | 可视化分析・可视化・统计・实验・热力矩阵 | 热力矩阵 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_response_histogram_facets` | 可视化分析・可视化・统计・实验・直方图 | 直方图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_response_map_choropleth_layer` | 可视化分析・可视化・统计・实验・分级着色地图 | 分级着色地图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_response_mosaic_tile_view` | 可视化分析・可视化・统计・实验 | Experiment response - Mosaic tile view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_response_network_node_link` | 可视化分析・可视化・统计・实验・网络 | 关系网络 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_response_qq_reference_plot` | 可视化分析・可视化・统计・实验 | Experiment response - Q-Q reference plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_response_quantile_band` | 可视化分析・可视化・统计・实验・分位数 | 分位数 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_response_raincloud_view` | 可视化分析・可视化・统计・实验 | Experiment response - Raincloud view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_response_rank_interval_plot` | 可视化分析・可视化・统计・实验・排名 | 排名 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_response_residual_annotation_map` | 可视化分析・可视化・统计・实验 | Experiment response - Residual annotation map | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_response_slope_change_view` | 可视化分析・可视化・统计・实验 | Experiment response - Slope change view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_response_small_multiple_grid` | 可视化分析・可视化・统计・实验 | 小多图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_response_stratified_dotplot` | 可视化分析・可视化・统计・实验 | Experiment response - Stratified dot plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_response_threshold_band` | 可视化分析・可视化・统计・实验 | Experiment response - Threshold band | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_response_uncertainty_ribbon` | 可视化分析・可视化・统计・实验 | Experiment response - Uncertainty ribbon | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_experiment_response_violin_summary` | 可视化分析・可视化・统计・实验・小提琴图・概览 | 小提琴图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factor_loading_annotated_reference_view` | 可视化分析・可视化・统计 | Factor loading pattern - Annotated reference view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factor_loading_boxen_interval` | 可视化分析・可视化・统计 | Factor loading pattern - Boxen interval plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factor_loading_comparative_lollipop` | 可视化分析・可视化・统计 | Factor loading pattern - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factor_loading_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factor_loading_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Factor loading pattern - Diagnostic panel | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factor_loading_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factor_loading_flow_transition_map` | 可视化分析・可视化・统计 | Factor loading pattern - Flow transition map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factor_loading_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factor_loading_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factor_loading_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factor_loading_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factor_loading_mosaic_tile_view` | 可视化分析・可视化・统计 | Factor loading pattern - Mosaic tile view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factor_loading_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factor_loading_qq_reference_plot` | 可视化分析・可视化・统计 | Factor loading pattern - Q-Q reference plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factor_loading_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factor_loading_raincloud_view` | 可视化分析・可视化・统计 | Factor loading pattern - Raincloud view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factor_loading_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factor_loading_residual_annotation_map` | 可视化分析・可视化・统计 | Factor loading pattern - Residual annotation map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factor_loading_slope_change_view` | 可视化分析・可视化・统计 | Factor loading pattern - Slope change view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factor_loading_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factor_loading_stratified_dotplot` | 可视化分析・可视化・统计 | Factor loading pattern - Stratified dot plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factor_loading_threshold_band` | 可视化分析・可视化・统计 | Factor loading pattern - Threshold band | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factor_loading_uncertainty_ribbon` | 可视化分析・可视化・统计 | Factor loading pattern - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factor_loading_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factorial_response_annotated_reference_view` | 可视化分析・可视化・统计 | Factorial response - Annotated reference view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factorial_response_boxen_interval` | 可视化分析・可视化・统计 | Factorial response - Boxen interval plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factorial_response_comparative_lollipop` | 可视化分析・可视化・统计 | Factorial response - Comparative lollipop plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factorial_response_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factorial_response_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Factorial response - Diagnostic panel | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factorial_response_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factorial_response_flow_transition_map` | 可视化分析・可视化・统计 | Factorial response - Flow transition map | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factorial_response_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factorial_response_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factorial_response_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factorial_response_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factorial_response_mosaic_tile_view` | 可视化分析・可视化・统计 | Factorial response - Mosaic tile view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factorial_response_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factorial_response_qq_reference_plot` | 可视化分析・可视化・统计 | Factorial response - Q-Q reference plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factorial_response_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factorial_response_raincloud_view` | 可视化分析・可视化・统计 | Factorial response - Raincloud view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factorial_response_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factorial_response_residual_annotation_map` | 可视化分析・可视化・统计 | Factorial response - Residual annotation map | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factorial_response_slope_change_view` | 可视化分析・可视化・统计 | Factorial response - Slope change view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factorial_response_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factorial_response_stratified_dotplot` | 可视化分析・可视化・统计 | Factorial response - Stratified dot plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factorial_response_threshold_band` | 可视化分析・可视化・统计 | Factorial response - Threshold band | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factorial_response_uncertainty_ribbon` | 可视化分析・可视化・统计 | Factorial response - Uncertainty ribbon | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_factorial_response_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_contribution_annotated_reference_view` | 可视化分析・可视化・统计・特征 | Feature contribution - Annotated reference view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_contribution_boxen_interval` | 可视化分析・可视化・统计・特征 | Feature contribution - Boxen interval plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_contribution_comparative_lollipop` | 可视化分析・可视化・统计・特征 | Feature contribution - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_contribution_density_ridge` | 可视化分析・可视化・统计・特征・密度图 | 密度图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_contribution_diagnostic_panel` | 可视化分析・可视化・统计・特征・诊断・面板 | Feature contribution - Diagnostic panel | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_contribution_ecdf_step_view` | 可视化分析・可视化・统计・特征・经验分布图 | 经验分布图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_contribution_flow_transition_map` | 可视化分析・可视化・统计・特征 | Feature contribution - Flow transition map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_contribution_forest_interval_plot` | 可视化分析・可视化・统计・特征・随机森林 | 随机森林 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_contribution_heatmap_matrix` | 可视化分析・可视化・统计・特征・热力矩阵 | 热力矩阵 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_contribution_histogram_facets` | 可视化分析・可视化・统计・特征・直方图 | 直方图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_contribution_map_choropleth_layer` | 可视化分析・可视化・统计・特征・分级着色地图 | 分级着色地图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_contribution_mosaic_tile_view` | 可视化分析・可视化・统计・特征 | Feature contribution - Mosaic tile view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_contribution_network_node_link` | 可视化分析・可视化・统计・特征・网络 | 关系网络 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_contribution_qq_reference_plot` | 可视化分析・可视化・统计・特征 | Feature contribution - Q-Q reference plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_contribution_quantile_band` | 可视化分析・可视化・统计・特征・分位数 | 分位数 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_contribution_raincloud_view` | 可视化分析・可视化・统计・特征 | Feature contribution - Raincloud view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_contribution_rank_interval_plot` | 可视化分析・可视化・统计・特征・排名 | 排名 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_contribution_residual_annotation_map` | 可视化分析・可视化・统计・特征 | Feature contribution - Residual annotation map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_contribution_slope_change_view` | 可视化分析・可视化・统计・特征 | Feature contribution - Slope change view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_contribution_small_multiple_grid` | 可视化分析・可视化・统计・特征 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_contribution_stratified_dotplot` | 可视化分析・可视化・统计・特征 | Feature contribution - Stratified dot plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_contribution_threshold_band` | 可视化分析・可视化・统计・特征 | Feature contribution - Threshold band | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_contribution_uncertainty_ribbon` | 可视化分析・可视化・统计・特征 | Feature contribution - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_contribution_violin_summary` | 可视化分析・可视化・统计・特征・小提琴图・概览 | 小提琴图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_importance_annotated_reference_view` | 可视化分析・可视化・统计・特征・重要性 | 重要性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_importance_boxen_interval` | 可视化分析・可视化・统计・特征・重要性 | 重要性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_importance_comparative_lollipop` | 可视化分析・可视化・统计・特征・重要性 | 重要性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_importance_density_ridge` | 可视化分析・可视化・统计・特征・重要性・密度图 | 重要性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_importance_diagnostic_panel` | 可视化分析・可视化・统计・特征・重要性・诊断・面板 | 重要性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_importance_ecdf_step_view` | 可视化分析・可视化・统计・特征・重要性・经验分布图 | 重要性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_importance_flow_transition_map` | 可视化分析・可视化・统计・特征・重要性 | 重要性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_importance_forest_interval_plot` | 可视化分析・可视化・统计・特征・重要性・随机森林 | 重要性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_importance_heatmap_matrix` | 可视化分析・可视化・统计・特征・重要性・热力矩阵 | 重要性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_importance_histogram_facets` | 可视化分析・可视化・统计・特征・重要性・直方图 | 重要性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_importance_map_choropleth_layer` | 可视化分析・可视化・统计・特征・重要性・分级着色地图 | 重要性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_importance_mosaic_tile_view` | 可视化分析・可视化・统计・特征・重要性 | 重要性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_importance_network_node_link` | 可视化分析・可视化・统计・特征・重要性・网络 | 重要性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_importance_qq_reference_plot` | 可视化分析・可视化・统计・特征・重要性 | 重要性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_importance_quantile_band` | 可视化分析・可视化・统计・特征・重要性・分位数 | 重要性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_importance_raincloud_view` | 可视化分析・可视化・统计・特征・重要性 | 重要性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_importance_rank_interval_plot` | 可视化分析・可视化・统计・特征・重要性・排名 | 重要性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_importance_residual_annotation_map` | 可视化分析・可视化・统计・特征・重要性 | 重要性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_importance_slope_change_view` | 可视化分析・可视化・统计・特征・重要性 | 重要性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_importance_small_multiple_grid` | 可视化分析・可视化・统计・特征・重要性 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_importance_stratified_dotplot` | 可视化分析・可视化・统计・特征・重要性 | 重要性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_importance_threshold_band` | 可视化分析・可视化・统计・特征・重要性 | 重要性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_importance_uncertainty_ribbon` | 可视化分析・可视化・统计・特征・重要性 | 重要性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_feature_importance_violin_summary` | 可视化分析・可视化・统计・特征・重要性・小提琴图・概览 | 重要性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_forecast_uncertainty_annotated_reference_view` | 可视化分析・可视化・统计・预测 | 预测 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_forecast_uncertainty_boxen_interval` | 可视化分析・可视化・统计・预测 | 预测 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_forecast_uncertainty_comparative_lollipop` | 可视化分析・可视化・统计・预测 | 预测 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_forecast_uncertainty_density_ridge` | 可视化分析・可视化・统计・预测・密度图 | 预测 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_forecast_uncertainty_diagnostic_panel` | 可视化分析・可视化・统计・预测・诊断・面板 | 预测 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_forecast_uncertainty_ecdf_step_view` | 可视化分析・可视化・统计・预测・经验分布图 | 预测 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_forecast_uncertainty_flow_transition_map` | 可视化分析・可视化・统计・预测 | 预测 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_forecast_uncertainty_forest_interval_plot` | 可视化分析・可视化・统计・预测・随机森林 | 预测 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_forecast_uncertainty_heatmap_matrix` | 可视化分析・可视化・统计・预测・热力矩阵 | 预测 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_forecast_uncertainty_histogram_facets` | 可视化分析・可视化・统计・预测・直方图 | 预测 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_forecast_uncertainty_map_choropleth_layer` | 可视化分析・可视化・统计・预测・分级着色地图 | 预测 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_forecast_uncertainty_mosaic_tile_view` | 可视化分析・可视化・统计・预测 | 预测 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_forecast_uncertainty_network_node_link` | 可视化分析・可视化・统计・预测・网络 | 预测 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_forecast_uncertainty_qq_reference_plot` | 可视化分析・可视化・统计・预测 | 预测 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_forecast_uncertainty_quantile_band` | 可视化分析・可视化・统计・预测・分位数 | 预测 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_forecast_uncertainty_raincloud_view` | 可视化分析・可视化・统计・预测 | 预测 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_forecast_uncertainty_rank_interval_plot` | 可视化分析・可视化・统计・预测・排名 | 预测 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_forecast_uncertainty_residual_annotation_map` | 可视化分析・可视化・统计・预测 | 预测 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_forecast_uncertainty_slope_change_view` | 可视化分析・可视化・统计・预测 | 预测 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_forecast_uncertainty_small_multiple_grid` | 可视化分析・可视化・统计・预测 | 小多图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_forecast_uncertainty_stratified_dotplot` | 可视化分析・可视化・统计・预测 | 预测 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_forecast_uncertainty_threshold_band` | 可视化分析・可视化・统计・预测 | 预测 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_forecast_uncertainty_uncertainty_ribbon` | 可视化分析・可视化・统计・预测 | 预测 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_forecast_uncertainty_violin_summary` | 可视化分析・可视化・统计・预测・小提琴图・概览 | 预测 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_balance_annotated_reference_view` | 可视化分析・可视化・统计 | Group balance diagnostic - Annotated reference view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_balance_boxen_interval` | 可视化分析・可视化・统计 | Group balance diagnostic - Boxen interval plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_balance_comparative_lollipop` | 可视化分析・可视化・统计 | Group balance diagnostic - Comparative lollipop plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_balance_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_balance_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Group balance diagnostic - Diagnostic panel | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_balance_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_balance_flow_transition_map` | 可视化分析・可视化・统计 | Group balance diagnostic - Flow transition map | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_balance_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_balance_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_balance_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_balance_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_balance_mosaic_tile_view` | 可视化分析・可视化・统计 | Group balance diagnostic - Mosaic tile view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_balance_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_balance_qq_reference_plot` | 可视化分析・可视化・统计 | Group balance diagnostic - Q-Q reference plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_balance_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_balance_raincloud_view` | 可视化分析・可视化・统计 | Group balance diagnostic - Raincloud view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_balance_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_balance_residual_annotation_map` | 可视化分析・可视化・统计 | Group balance diagnostic - Residual annotation map | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_balance_slope_change_view` | 可视化分析・可视化・统计 | Group balance diagnostic - Slope change view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_balance_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_balance_stratified_dotplot` | 可视化分析・可视化・统计 | Group balance diagnostic - Stratified dot plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_balance_threshold_band` | 可视化分析・可视化・统计 | Group balance diagnostic - Threshold band | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_balance_uncertainty_ribbon` | 可视化分析・可视化・统计 | Group balance diagnostic - Uncertainty ribbon | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_balance_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_difference_annotated_reference_view` | 可视化分析・可视化・统计 | Group difference evidence - Annotated reference view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_difference_boxen_interval` | 可视化分析・可视化・统计 | Group difference evidence - Boxen interval plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_difference_comparative_lollipop` | 可视化分析・可视化・统计 | Group difference evidence - Comparative lollipop plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_difference_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_difference_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Group difference evidence - Diagnostic panel | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_difference_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_difference_flow_transition_map` | 可视化分析・可视化・统计 | Group difference evidence - Flow transition map | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_difference_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_difference_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_difference_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_difference_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_difference_mosaic_tile_view` | 可视化分析・可视化・统计 | Group difference evidence - Mosaic tile view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_difference_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_difference_qq_reference_plot` | 可视化分析・可视化・统计 | Group difference evidence - Q-Q reference plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_difference_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_difference_raincloud_view` | 可视化分析・可视化・统计 | Group difference evidence - Raincloud view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_difference_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_difference_residual_annotation_map` | 可视化分析・可视化・统计 | Group difference evidence - Residual annotation map | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_difference_slope_change_view` | 可视化分析・可视化・统计 | Group difference evidence - Slope change view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_difference_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_difference_stratified_dotplot` | 可视化分析・可视化・统计 | Group difference evidence - Stratified dot plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_difference_threshold_band` | 可视化分析・可视化・统计 | Group difference evidence - Threshold band | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_difference_uncertainty_ribbon` | 可视化分析・可视化・统计 | Group difference evidence - Uncertainty ribbon | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_group_difference_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_hazard_comparison_annotated_reference_view` | 可视化分析・可视化・统计 | Hazard comparison - Annotated reference view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_hazard_comparison_boxen_interval` | 可视化分析・可视化・统计 | Hazard comparison - Boxen interval plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_hazard_comparison_comparative_lollipop` | 可视化分析・可视化・统计 | Hazard comparison - Comparative lollipop plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_hazard_comparison_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_hazard_comparison_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Hazard comparison - Diagnostic panel | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_hazard_comparison_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_hazard_comparison_flow_transition_map` | 可视化分析・可视化・统计 | Hazard comparison - Flow transition map | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_hazard_comparison_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_hazard_comparison_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_hazard_comparison_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_hazard_comparison_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_hazard_comparison_mosaic_tile_view` | 可视化分析・可视化・统计 | Hazard comparison - Mosaic tile view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_hazard_comparison_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_hazard_comparison_qq_reference_plot` | 可视化分析・可视化・统计 | Hazard comparison - Q-Q reference plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_hazard_comparison_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_hazard_comparison_raincloud_view` | 可视化分析・可视化・统计 | Hazard comparison - Raincloud view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_hazard_comparison_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_hazard_comparison_residual_annotation_map` | 可视化分析・可视化・统计 | Hazard comparison - Residual annotation map | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_hazard_comparison_slope_change_view` | 可视化分析・可视化・统计 | Hazard comparison - Slope change view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_hazard_comparison_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_hazard_comparison_stratified_dotplot` | 可视化分析・可视化・统计 | Hazard comparison - Stratified dot plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_hazard_comparison_threshold_band` | 可视化分析・可视化・统计 | Hazard comparison - Threshold band | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_hazard_comparison_uncertainty_ribbon` | 可视化分析・可视化・统计 | Hazard comparison - Uncertainty ribbon | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_hazard_comparison_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_heteroscedasticity_pattern_annotated_reference_view` | 可视化分析・可视化・统计 | Heteroscedasticity pattern - Annotated reference view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_heteroscedasticity_pattern_boxen_interval` | 可视化分析・可视化・统计 | Heteroscedasticity pattern - Boxen interval plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_heteroscedasticity_pattern_comparative_lollipop` | 可视化分析・可视化・统计 | Heteroscedasticity pattern - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_heteroscedasticity_pattern_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_heteroscedasticity_pattern_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Heteroscedasticity pattern - Diagnostic panel | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_heteroscedasticity_pattern_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_heteroscedasticity_pattern_flow_transition_map` | 可视化分析・可视化・统计 | Heteroscedasticity pattern - Flow transition map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_heteroscedasticity_pattern_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_heteroscedasticity_pattern_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_heteroscedasticity_pattern_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_heteroscedasticity_pattern_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_heteroscedasticity_pattern_mosaic_tile_view` | 可视化分析・可视化・统计 | Heteroscedasticity pattern - Mosaic tile view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_heteroscedasticity_pattern_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_heteroscedasticity_pattern_qq_reference_plot` | 可视化分析・可视化・统计 | Heteroscedasticity pattern - Q-Q reference plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_heteroscedasticity_pattern_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_heteroscedasticity_pattern_raincloud_view` | 可视化分析・可视化・统计 | Heteroscedasticity pattern - Raincloud view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_heteroscedasticity_pattern_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_heteroscedasticity_pattern_residual_annotation_map` | 可视化分析・可视化・统计 | Heteroscedasticity pattern - Residual annotation map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_heteroscedasticity_pattern_slope_change_view` | 可视化分析・可视化・统计 | Heteroscedasticity pattern - Slope change view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_heteroscedasticity_pattern_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_heteroscedasticity_pattern_stratified_dotplot` | 可视化分析・可视化・统计 | Heteroscedasticity pattern - Stratified dot plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_heteroscedasticity_pattern_threshold_band` | 可视化分析・可视化・统计 | Heteroscedasticity pattern - Threshold band | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_heteroscedasticity_pattern_uncertainty_ribbon` | 可视化分析・可视化・统计 | Heteroscedasticity pattern - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_heteroscedasticity_pattern_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_instrument_strength_annotated_reference_view` | 可视化分析・可视化・统计 | Instrument strength - Annotated reference view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_instrument_strength_boxen_interval` | 可视化分析・可视化・统计 | Instrument strength - Boxen interval plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_instrument_strength_comparative_lollipop` | 可视化分析・可视化・统计 | Instrument strength - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_instrument_strength_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_instrument_strength_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Instrument strength - Diagnostic panel | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_instrument_strength_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_instrument_strength_flow_transition_map` | 可视化分析・可视化・统计 | Instrument strength - Flow transition map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_instrument_strength_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_instrument_strength_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_instrument_strength_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_instrument_strength_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_instrument_strength_mosaic_tile_view` | 可视化分析・可视化・统计 | Instrument strength - Mosaic tile view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_instrument_strength_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_instrument_strength_qq_reference_plot` | 可视化分析・可视化・统计 | Instrument strength - Q-Q reference plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_instrument_strength_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_instrument_strength_raincloud_view` | 可视化分析・可视化・统计 | Instrument strength - Raincloud view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_instrument_strength_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_instrument_strength_residual_annotation_map` | 可视化分析・可视化・统计 | Instrument strength - Residual annotation map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_instrument_strength_slope_change_view` | 可视化分析・可视化・统计 | Instrument strength - Slope change view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_instrument_strength_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_instrument_strength_stratified_dotplot` | 可视化分析・可视化・统计 | Instrument strength - Stratified dot plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_instrument_strength_threshold_band` | 可视化分析・可视化・统计 | Instrument strength - Threshold band | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_instrument_strength_uncertainty_ribbon` | 可视化分析・可视化・统计 | Instrument strength - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_instrument_strength_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_inter_rater_agreement_annotated_reference_view` | 可视化分析・可视化・统计 | Inter-rater agreement - Annotated reference view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_inter_rater_agreement_boxen_interval` | 可视化分析・可视化・统计 | Inter-rater agreement - Boxen interval plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_inter_rater_agreement_comparative_lollipop` | 可视化分析・可视化・统计 | Inter-rater agreement - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_inter_rater_agreement_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_inter_rater_agreement_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Inter-rater agreement - Diagnostic panel | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_inter_rater_agreement_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_inter_rater_agreement_flow_transition_map` | 可视化分析・可视化・统计 | Inter-rater agreement - Flow transition map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_inter_rater_agreement_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_inter_rater_agreement_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_inter_rater_agreement_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_inter_rater_agreement_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_inter_rater_agreement_mosaic_tile_view` | 可视化分析・可视化・统计 | Inter-rater agreement - Mosaic tile view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_inter_rater_agreement_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_inter_rater_agreement_qq_reference_plot` | 可视化分析・可视化・统计 | Inter-rater agreement - Q-Q reference plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_inter_rater_agreement_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_inter_rater_agreement_raincloud_view` | 可视化分析・可视化・统计 | Inter-rater agreement - Raincloud view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_inter_rater_agreement_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_inter_rater_agreement_residual_annotation_map` | 可视化分析・可视化・统计 | Inter-rater agreement - Residual annotation map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_inter_rater_agreement_slope_change_view` | 可视化分析・可视化・统计 | Inter-rater agreement - Slope change view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_inter_rater_agreement_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_inter_rater_agreement_stratified_dotplot` | 可视化分析・可视化・统计 | Inter-rater agreement - Stratified dot plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_inter_rater_agreement_threshold_band` | 可视化分析・可视化・统计 | Inter-rater agreement - Threshold band | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_inter_rater_agreement_uncertainty_ribbon` | 可视化分析・可视化・统计 | Inter-rater agreement - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_inter_rater_agreement_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_interaction_effect_annotated_reference_view` | 可视化分析・可视化・统计・效应 | Interaction effect - Annotated reference view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_interaction_effect_boxen_interval` | 可视化分析・可视化・统计・效应 | Interaction effect - Boxen interval plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_interaction_effect_comparative_lollipop` | 可视化分析・可视化・统计・效应 | Interaction effect - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_interaction_effect_density_ridge` | 可视化分析・可视化・统计・效应・密度图 | 密度图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_interaction_effect_diagnostic_panel` | 可视化分析・可视化・统计・效应・诊断・面板 | Interaction effect - Diagnostic panel | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_interaction_effect_ecdf_step_view` | 可视化分析・可视化・统计・效应・经验分布图 | 经验分布图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_interaction_effect_flow_transition_map` | 可视化分析・可视化・统计・效应 | Interaction effect - Flow transition map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_interaction_effect_forest_interval_plot` | 可视化分析・可视化・统计・效应・随机森林 | 随机森林 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_interaction_effect_heatmap_matrix` | 可视化分析・可视化・统计・效应・热力矩阵 | 热力矩阵 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_interaction_effect_histogram_facets` | 可视化分析・可视化・统计・效应・直方图 | 直方图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_interaction_effect_map_choropleth_layer` | 可视化分析・可视化・统计・效应・分级着色地图 | 分级着色地图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_interaction_effect_mosaic_tile_view` | 可视化分析・可视化・统计・效应 | Interaction effect - Mosaic tile view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_interaction_effect_network_node_link` | 可视化分析・可视化・统计・效应・网络 | 关系网络 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_interaction_effect_qq_reference_plot` | 可视化分析・可视化・统计・效应 | Interaction effect - Q-Q reference plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_interaction_effect_quantile_band` | 可视化分析・可视化・统计・效应・分位数 | 分位数 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_interaction_effect_raincloud_view` | 可视化分析・可视化・统计・效应 | Interaction effect - Raincloud view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_interaction_effect_rank_interval_plot` | 可视化分析・可视化・统计・效应・排名 | 排名 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_interaction_effect_residual_annotation_map` | 可视化分析・可视化・统计・效应 | Interaction effect - Residual annotation map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_interaction_effect_slope_change_view` | 可视化分析・可视化・统计・效应 | Interaction effect - Slope change view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_interaction_effect_small_multiple_grid` | 可视化分析・可视化・统计・效应 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_interaction_effect_stratified_dotplot` | 可视化分析・可视化・统计・效应 | Interaction effect - Stratified dot plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_interaction_effect_threshold_band` | 可视化分析・可视化・统计・效应 | Interaction effect - Threshold band | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_interaction_effect_uncertainty_ribbon` | 可视化分析・可视化・统计・效应 | Interaction effect - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_interaction_effect_violin_summary` | 可视化分析・可视化・统计・效应・小提琴图・概览 | 小提琴图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_inventory_process_variation_annotated_reference_view` | 可视化分析・可视化・统计 | Inventory process variation - Annotated reference view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_inventory_process_variation_boxen_interval` | 可视化分析・可视化・统计 | Inventory process variation - Boxen interval plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_inventory_process_variation_comparative_lollipop` | 可视化分析・可视化・统计 | Inventory process variation - Comparative lollipop plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_inventory_process_variation_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_inventory_process_variation_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Inventory process variation - Diagnostic panel | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_inventory_process_variation_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_inventory_process_variation_flow_transition_map` | 可视化分析・可视化・统计 | Inventory process variation - Flow transition map | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_inventory_process_variation_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_inventory_process_variation_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_inventory_process_variation_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_inventory_process_variation_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_inventory_process_variation_mosaic_tile_view` | 可视化分析・可视化・统计 | Inventory process variation - Mosaic tile view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_inventory_process_variation_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_inventory_process_variation_qq_reference_plot` | 可视化分析・可视化・统计 | Inventory process variation - Q-Q reference plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_inventory_process_variation_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_inventory_process_variation_raincloud_view` | 可视化分析・可视化・统计 | Inventory process variation - Raincloud view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_inventory_process_variation_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_inventory_process_variation_residual_annotation_map` | 可视化分析・可视化・统计 | Inventory process variation - Residual annotation map | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_inventory_process_variation_slope_change_view` | 可视化分析・可视化・统计 | Inventory process variation - Slope change view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_inventory_process_variation_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_inventory_process_variation_stratified_dotplot` | 可视化分析・可视化・统计 | Inventory process variation - Stratified dot plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_inventory_process_variation_threshold_band` | 可视化分析・可视化・统计 | Inventory process variation - Threshold band | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_inventory_process_variation_uncertainty_ribbon` | 可视化分析・可视化・统计 | Inventory process variation - Uncertainty ribbon | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_inventory_process_variation_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_item_response_pattern_annotated_reference_view` | 可视化分析・可视化・统计 | Item response pattern - Annotated reference view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_item_response_pattern_boxen_interval` | 可视化分析・可视化・统计 | Item response pattern - Boxen interval plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_item_response_pattern_comparative_lollipop` | 可视化分析・可视化・统计 | Item response pattern - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_item_response_pattern_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_item_response_pattern_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Item response pattern - Diagnostic panel | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_item_response_pattern_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_item_response_pattern_flow_transition_map` | 可视化分析・可视化・统计 | Item response pattern - Flow transition map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_item_response_pattern_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_item_response_pattern_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_item_response_pattern_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_item_response_pattern_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_item_response_pattern_mosaic_tile_view` | 可视化分析・可视化・统计 | Item response pattern - Mosaic tile view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_item_response_pattern_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_item_response_pattern_qq_reference_plot` | 可视化分析・可视化・统计 | Item response pattern - Q-Q reference plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_item_response_pattern_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_item_response_pattern_raincloud_view` | 可视化分析・可视化・统计 | Item response pattern - Raincloud view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_item_response_pattern_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_item_response_pattern_residual_annotation_map` | 可视化分析・可视化・统计 | Item response pattern - Residual annotation map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_item_response_pattern_slope_change_view` | 可视化分析・可视化・统计 | Item response pattern - Slope change view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_item_response_pattern_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_item_response_pattern_stratified_dotplot` | 可视化分析・可视化・统计 | Item response pattern - Stratified dot plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_item_response_pattern_threshold_band` | 可视化分析・可视化・统计 | Item response pattern - Threshold band | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_item_response_pattern_uncertainty_ribbon` | 可视化分析・可视化・统计 | Item response pattern - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_item_response_pattern_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_lab_measurement_qc_annotated_reference_view` | 可视化分析・可视化・统计 | Laboratory measurement QC - Annotated reference view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_lab_measurement_qc_boxen_interval` | 可视化分析・可视化・统计 | Laboratory measurement QC - Boxen interval plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_lab_measurement_qc_comparative_lollipop` | 可视化分析・可视化・统计 | Laboratory measurement QC - Comparative lollipop plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_lab_measurement_qc_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_lab_measurement_qc_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Laboratory measurement QC - Diagnostic panel | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_lab_measurement_qc_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_lab_measurement_qc_flow_transition_map` | 可视化分析・可视化・统计 | Laboratory measurement QC - Flow transition map | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_lab_measurement_qc_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_lab_measurement_qc_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_lab_measurement_qc_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_lab_measurement_qc_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_lab_measurement_qc_mosaic_tile_view` | 可视化分析・可视化・统计 | Laboratory measurement QC - Mosaic tile view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_lab_measurement_qc_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_lab_measurement_qc_qq_reference_plot` | 可视化分析・可视化・统计 | Laboratory measurement QC - Q-Q reference plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_lab_measurement_qc_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_lab_measurement_qc_raincloud_view` | 可视化分析・可视化・统计 | Laboratory measurement QC - Raincloud view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_lab_measurement_qc_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_lab_measurement_qc_residual_annotation_map` | 可视化分析・可视化・统计 | Laboratory measurement QC - Residual annotation map | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_lab_measurement_qc_slope_change_view` | 可视化分析・可视化・统计 | Laboratory measurement QC - Slope change view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_lab_measurement_qc_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_lab_measurement_qc_stratified_dotplot` | 可视化分析・可视化・统计 | Laboratory measurement QC - Stratified dot plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_lab_measurement_qc_threshold_band` | 可视化分析・可视化・统计 | Laboratory measurement QC - Threshold band | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_lab_measurement_qc_uncertainty_ribbon` | 可视化分析・可视化・统计 | Laboratory measurement QC - Uncertainty ribbon | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_lab_measurement_qc_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_latent_construct_annotated_reference_view` | 可视化分析・可视化・统计 | Latent construct - Annotated reference view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_latent_construct_boxen_interval` | 可视化分析・可视化・统计 | Latent construct - Boxen interval plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_latent_construct_comparative_lollipop` | 可视化分析・可视化・统计 | Latent construct - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_latent_construct_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_latent_construct_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Latent construct - Diagnostic panel | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_latent_construct_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_latent_construct_flow_transition_map` | 可视化分析・可视化・统计 | Latent construct - Flow transition map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_latent_construct_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_latent_construct_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_latent_construct_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_latent_construct_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_latent_construct_mosaic_tile_view` | 可视化分析・可视化・统计 | Latent construct - Mosaic tile view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_latent_construct_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_latent_construct_qq_reference_plot` | 可视化分析・可视化・统计 | Latent construct - Q-Q reference plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_latent_construct_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_latent_construct_raincloud_view` | 可视化分析・可视化・统计 | Latent construct - Raincloud view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_latent_construct_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_latent_construct_residual_annotation_map` | 可视化分析・可视化・统计 | Latent construct - Residual annotation map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_latent_construct_slope_change_view` | 可视化分析・可视化・统计 | Latent construct - Slope change view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_latent_construct_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_latent_construct_stratified_dotplot` | 可视化分析・可视化・统计 | Latent construct - Stratified dot plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_latent_construct_threshold_band` | 可视化分析・可视化・统计 | Latent construct - Threshold band | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_latent_construct_uncertainty_ribbon` | 可视化分析・可视化・统计 | Latent construct - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_latent_construct_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_leverage_structure_annotated_reference_view` | 可视化分析・可视化・统计 | Leverage structure - Annotated reference view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_leverage_structure_boxen_interval` | 可视化分析・可视化・统计 | Leverage structure - Boxen interval plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_leverage_structure_comparative_lollipop` | 可视化分析・可视化・统计 | Leverage structure - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_leverage_structure_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_leverage_structure_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Leverage structure - Diagnostic panel | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_leverage_structure_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_leverage_structure_flow_transition_map` | 可视化分析・可视化・统计 | Leverage structure - Flow transition map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_leverage_structure_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_leverage_structure_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_leverage_structure_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_leverage_structure_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_leverage_structure_mosaic_tile_view` | 可视化分析・可视化・统计 | Leverage structure - Mosaic tile view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_leverage_structure_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_leverage_structure_qq_reference_plot` | 可视化分析・可视化・统计 | Leverage structure - Q-Q reference plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_leverage_structure_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_leverage_structure_raincloud_view` | 可视化分析・可视化・统计 | Leverage structure - Raincloud view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_leverage_structure_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_leverage_structure_residual_annotation_map` | 可视化分析・可视化・统计 | Leverage structure - Residual annotation map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_leverage_structure_slope_change_view` | 可视化分析・可视化・统计 | Leverage structure - Slope change view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_leverage_structure_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_leverage_structure_stratified_dotplot` | 可视化分析・可视化・统计 | Leverage structure - Stratified dot plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_leverage_structure_threshold_band` | 可视化分析・可视化・统计 | Leverage structure - Threshold band | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_leverage_structure_uncertainty_ribbon` | 可视化分析・可视化・统计 | Leverage structure - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_leverage_structure_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_longitudinal_trajectory_annotated_reference_view` | 可视化分析・可视化・统计 | Longitudinal trajectory - Annotated reference view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_longitudinal_trajectory_boxen_interval` | 可视化分析・可视化・统计 | Longitudinal trajectory - Boxen interval plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_longitudinal_trajectory_comparative_lollipop` | 可视化分析・可视化・统计 | Longitudinal trajectory - Comparative lollipop plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_longitudinal_trajectory_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_longitudinal_trajectory_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Longitudinal trajectory - Diagnostic panel | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_longitudinal_trajectory_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_longitudinal_trajectory_flow_transition_map` | 可视化分析・可视化・统计 | Longitudinal trajectory - Flow transition map | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_longitudinal_trajectory_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_longitudinal_trajectory_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_longitudinal_trajectory_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_longitudinal_trajectory_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_longitudinal_trajectory_mosaic_tile_view` | 可视化分析・可视化・统计 | Longitudinal trajectory - Mosaic tile view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_longitudinal_trajectory_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_longitudinal_trajectory_qq_reference_plot` | 可视化分析・可视化・统计 | Longitudinal trajectory - Q-Q reference plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_longitudinal_trajectory_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_longitudinal_trajectory_raincloud_view` | 可视化分析・可视化・统计 | Longitudinal trajectory - Raincloud view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_longitudinal_trajectory_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_longitudinal_trajectory_residual_annotation_map` | 可视化分析・可视化・统计 | Longitudinal trajectory - Residual annotation map | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_longitudinal_trajectory_slope_change_view` | 可视化分析・可视化・统计 | Longitudinal trajectory - Slope change view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_longitudinal_trajectory_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_longitudinal_trajectory_stratified_dotplot` | 可视化分析・可视化・统计 | Longitudinal trajectory - Stratified dot plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_longitudinal_trajectory_threshold_band` | 可视化分析・可视化・统计 | Longitudinal trajectory - Threshold band | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_longitudinal_trajectory_uncertainty_ribbon` | 可视化分析・可视化・统计 | Longitudinal trajectory - Uncertainty ribbon | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_longitudinal_trajectory_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_manifold_structure_annotated_reference_view` | 可视化分析・可视化・统计 | Manifold structure - Annotated reference view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_manifold_structure_boxen_interval` | 可视化分析・可视化・统计 | Manifold structure - Boxen interval plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_manifold_structure_comparative_lollipop` | 可视化分析・可视化・统计 | Manifold structure - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_manifold_structure_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_manifold_structure_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Manifold structure - Diagnostic panel | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_manifold_structure_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_manifold_structure_flow_transition_map` | 可视化分析・可视化・统计 | Manifold structure - Flow transition map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_manifold_structure_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_manifold_structure_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_manifold_structure_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_manifold_structure_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_manifold_structure_mosaic_tile_view` | 可视化分析・可视化・统计 | Manifold structure - Mosaic tile view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_manifold_structure_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_manifold_structure_qq_reference_plot` | 可视化分析・可视化・统计 | Manifold structure - Q-Q reference plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_manifold_structure_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_manifold_structure_raincloud_view` | 可视化分析・可视化・统计 | Manifold structure - Raincloud view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_manifold_structure_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_manifold_structure_residual_annotation_map` | 可视化分析・可视化・统计 | Manifold structure - Residual annotation map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_manifold_structure_slope_change_view` | 可视化分析・可视化・统计 | Manifold structure - Slope change view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_manifold_structure_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_manifold_structure_stratified_dotplot` | 可视化分析・可视化・统计 | Manifold structure - Stratified dot plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_manifold_structure_threshold_band` | 可视化分析・可视化・统计 | Manifold structure - Threshold band | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_manifold_structure_uncertainty_ribbon` | 可视化分析・可视化・统计 | Manifold structure - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_manifold_structure_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_manufacturing_process_stability_annotated_reference_view` | 可视化分析・可视化・统计 | Manufacturing process stability - Annotated reference view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_manufacturing_process_stability_boxen_interval` | 可视化分析・可视化・统计 | Manufacturing process stability - Boxen interval plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_manufacturing_process_stability_comparative_lollipop` | 可视化分析・可视化・统计 | Manufacturing process stability - Comparative lollipop plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_manufacturing_process_stability_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_manufacturing_process_stability_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Manufacturing process stability - Diagnostic panel | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_manufacturing_process_stability_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_manufacturing_process_stability_flow_transition_map` | 可视化分析・可视化・统计 | Manufacturing process stability - Flow transition map | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_manufacturing_process_stability_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_manufacturing_process_stability_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_manufacturing_process_stability_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_manufacturing_process_stability_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_manufacturing_process_stability_mosaic_tile_view` | 可视化分析・可视化・统计 | Manufacturing process stability - Mosaic tile view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_manufacturing_process_stability_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_manufacturing_process_stability_qq_reference_plot` | 可视化分析・可视化・统计 | Manufacturing process stability - Q-Q reference plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_manufacturing_process_stability_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_manufacturing_process_stability_raincloud_view` | 可视化分析・可视化・统计 | Manufacturing process stability - Raincloud view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_manufacturing_process_stability_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_manufacturing_process_stability_residual_annotation_map` | 可视化分析・可视化・统计 | Manufacturing process stability - Residual annotation map | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_manufacturing_process_stability_slope_change_view` | 可视化分析・可视化・统计 | Manufacturing process stability - Slope change view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_manufacturing_process_stability_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_manufacturing_process_stability_stratified_dotplot` | 可视化分析・可视化・统计 | Manufacturing process stability - Stratified dot plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_manufacturing_process_stability_threshold_band` | 可视化分析・可视化・统计 | Manufacturing process stability - Threshold band | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_manufacturing_process_stability_uncertainty_ribbon` | 可视化分析・可视化・统计 | Manufacturing process stability - Uncertainty ribbon | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_manufacturing_process_stability_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_measurement_error_annotated_reference_view` | 可视化分析・可视化・统计・误差 | Measurement error - Annotated reference view | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_measurement_error_boxen_interval` | 可视化分析・可视化・统计・误差 | Measurement error - Boxen interval plot | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_measurement_error_comparative_lollipop` | 可视化分析・可视化・统计・误差 | Measurement error - Comparative lollipop plot | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_measurement_error_density_ridge` | 可视化分析・可视化・统计・误差・密度图 | 密度图 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_measurement_error_diagnostic_panel` | 可视化分析・可视化・统计・误差・诊断・面板 | Measurement error - Diagnostic panel | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_measurement_error_ecdf_step_view` | 可视化分析・可视化・统计・误差・经验分布图 | 经验分布图 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_measurement_error_flow_transition_map` | 可视化分析・可视化・统计・误差 | Measurement error - Flow transition map | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_measurement_error_forest_interval_plot` | 可视化分析・可视化・统计・误差・随机森林 | 随机森林 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_measurement_error_heatmap_matrix` | 可视化分析・可视化・统计・误差・热力矩阵 | 热力矩阵 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_measurement_error_histogram_facets` | 可视化分析・可视化・统计・误差・直方图 | 直方图 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_measurement_error_map_choropleth_layer` | 可视化分析・可视化・统计・误差・分级着色地图 | 分级着色地图 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_measurement_error_mosaic_tile_view` | 可视化分析・可视化・统计・误差 | Measurement error - Mosaic tile view | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_measurement_error_network_node_link` | 可视化分析・可视化・统计・误差・网络 | 关系网络 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_measurement_error_qq_reference_plot` | 可视化分析・可视化・统计・误差 | Measurement error - Q-Q reference plot | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_measurement_error_quantile_band` | 可视化分析・可视化・统计・误差・分位数 | 分位数 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_measurement_error_raincloud_view` | 可视化分析・可视化・统计・误差 | Measurement error - Raincloud view | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_measurement_error_rank_interval_plot` | 可视化分析・可视化・统计・误差・排名 | 排名 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_measurement_error_residual_annotation_map` | 可视化分析・可视化・统计・误差 | Measurement error - Residual annotation map | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_measurement_error_slope_change_view` | 可视化分析・可视化・统计・误差 | Measurement error - Slope change view | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_measurement_error_small_multiple_grid` | 可视化分析・可视化・统计・误差 | 小多图 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_measurement_error_stratified_dotplot` | 可视化分析・可视化・统计・误差 | Measurement error - Stratified dot plot | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_measurement_error_threshold_band` | 可视化分析・可视化・统计・误差 | Measurement error - Threshold band | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_measurement_error_uncertainty_ribbon` | 可视化分析・可视化・统计・误差 | Measurement error - Uncertainty ribbon | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_measurement_error_violin_summary` | 可视化分析・可视化・统计・误差・小提琴图・概览 | 小提琴图 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_mediation_path_annotated_reference_view` | 可视化分析・可视化・统计 | Mediation path - Annotated reference view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_mediation_path_boxen_interval` | 可视化分析・可视化・统计 | Mediation path - Boxen interval plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_mediation_path_comparative_lollipop` | 可视化分析・可视化・统计 | Mediation path - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_mediation_path_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_mediation_path_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Mediation path - Diagnostic panel | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_mediation_path_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_mediation_path_flow_transition_map` | 可视化分析・可视化・统计 | Mediation path - Flow transition map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_mediation_path_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_mediation_path_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_mediation_path_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_mediation_path_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_mediation_path_mosaic_tile_view` | 可视化分析・可视化・统计 | Mediation path - Mosaic tile view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_mediation_path_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_mediation_path_qq_reference_plot` | 可视化分析・可视化・统计 | Mediation path - Q-Q reference plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_mediation_path_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_mediation_path_raincloud_view` | 可视化分析・可视化・统计 | Mediation path - Raincloud view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_mediation_path_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_mediation_path_residual_annotation_map` | 可视化分析・可视化・统计 | Mediation path - Residual annotation map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_mediation_path_slope_change_view` | 可视化分析・可视化・统计 | Mediation path - Slope change view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_mediation_path_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_mediation_path_stratified_dotplot` | 可视化分析・可视化・统计 | Mediation path - Stratified dot plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_mediation_path_threshold_band` | 可视化分析・可视化・统计 | Mediation path - Threshold band | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_mediation_path_uncertainty_ribbon` | 可视化分析・可视化・统计 | Mediation path - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_mediation_path_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_missingness_pattern_annotated_reference_view` | 可视化分析・可视化・统计・缺失情况 | 缺失情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_missingness_pattern_boxen_interval` | 可视化分析・可视化・统计・缺失情况 | 缺失情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_missingness_pattern_comparative_lollipop` | 可视化分析・可视化・统计・缺失情况 | 缺失情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_missingness_pattern_density_ridge` | 可视化分析・可视化・统计・缺失情况・密度图 | 缺失情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_missingness_pattern_diagnostic_panel` | 可视化分析・可视化・统计・缺失情况・诊断・面板 | 缺失情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_missingness_pattern_ecdf_step_view` | 可视化分析・可视化・统计・缺失情况・经验分布图 | 缺失情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_missingness_pattern_flow_transition_map` | 可视化分析・可视化・统计・缺失情况 | 缺失情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_missingness_pattern_forest_interval_plot` | 可视化分析・可视化・统计・缺失情况・随机森林 | 缺失情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_missingness_pattern_heatmap_matrix` | 可视化分析・可视化・统计・缺失情况・热力矩阵 | 缺失情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_missingness_pattern_histogram_facets` | 可视化分析・可视化・统计・缺失情况・直方图 | 缺失情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_missingness_pattern_map_choropleth_layer` | 可视化分析・可视化・统计・缺失情况・分级着色地图 | 缺失情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_missingness_pattern_mosaic_tile_view` | 可视化分析・可视化・统计・缺失情况 | 缺失情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_missingness_pattern_network_node_link` | 可视化分析・可视化・统计・缺失情况・网络 | 缺失情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_missingness_pattern_qq_reference_plot` | 可视化分析・可视化・统计・缺失情况 | 缺失情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_missingness_pattern_quantile_band` | 可视化分析・可视化・统计・缺失情况・分位数 | 缺失情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_missingness_pattern_raincloud_view` | 可视化分析・可视化・统计・缺失情况 | 缺失情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_missingness_pattern_rank_interval_plot` | 可视化分析・可视化・统计・缺失情况・排名 | 缺失情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_missingness_pattern_residual_annotation_map` | 可视化分析・可视化・统计・缺失情况 | 缺失情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_missingness_pattern_slope_change_view` | 可视化分析・可视化・统计・缺失情况 | 缺失情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_missingness_pattern_small_multiple_grid` | 可视化分析・可视化・统计・缺失情况 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_missingness_pattern_stratified_dotplot` | 可视化分析・可视化・统计・缺失情况 | 缺失情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_missingness_pattern_threshold_band` | 可视化分析・可视化・统计・缺失情况 | 缺失情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_missingness_pattern_uncertainty_ribbon` | 可视化分析・可视化・统计・缺失情况 | 缺失情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_missingness_pattern_violin_summary` | 可视化分析・可视化・统计・缺失情况・小提琴图・概览 | 缺失情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_mobility_flow_annotated_reference_view` | 可视化分析・可视化・统计 | Mobility flow - Annotated reference view | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_mobility_flow_boxen_interval` | 可视化分析・可视化・统计 | Mobility flow - Boxen interval plot | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_mobility_flow_comparative_lollipop` | 可视化分析・可视化・统计 | Mobility flow - Comparative lollipop plot | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_mobility_flow_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_mobility_flow_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Mobility flow - Diagnostic panel | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_mobility_flow_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_mobility_flow_flow_transition_map` | 可视化分析・可视化・统计 | Mobility flow - Flow transition map | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_mobility_flow_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_mobility_flow_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_mobility_flow_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_mobility_flow_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 流向地图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_mobility_flow_mosaic_tile_view` | 可视化分析・可视化・统计 | Mobility flow - Mosaic tile view | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_mobility_flow_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_mobility_flow_qq_reference_plot` | 可视化分析・可视化・统计 | Mobility flow - Q-Q reference plot | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_mobility_flow_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_mobility_flow_raincloud_view` | 可视化分析・可视化・统计 | Mobility flow - Raincloud view | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_mobility_flow_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_mobility_flow_residual_annotation_map` | 可视化分析・可视化・统计 | Mobility flow - Residual annotation map | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_mobility_flow_slope_change_view` | 可视化分析・可视化・统计 | Mobility flow - Slope change view | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_mobility_flow_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_mobility_flow_stratified_dotplot` | 可视化分析・可视化・统计 | Mobility flow - Stratified dot plot | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_mobility_flow_threshold_band` | 可视化分析・可视化・统计 | Mobility flow - Threshold band | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_mobility_flow_uncertainty_ribbon` | 可视化分析・可视化・统计 | Mobility flow - Uncertainty ribbon | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_mobility_flow_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_model_fit_annotated_reference_view` | 可视化分析・可视化・统计・模型 | Model fit diagnostic - Annotated reference view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_model_fit_boxen_interval` | 可视化分析・可视化・统计・模型 | Model fit diagnostic - Boxen interval plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_model_fit_comparative_lollipop` | 可视化分析・可视化・统计・模型 | Model fit diagnostic - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_model_fit_density_ridge` | 可视化分析・可视化・统计・模型・密度图 | 密度图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_model_fit_diagnostic_panel` | 可视化分析・可视化・统计・模型・诊断・面板 | Model fit diagnostic - Diagnostic panel | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_model_fit_ecdf_step_view` | 可视化分析・可视化・统计・模型・经验分布图 | 经验分布图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_model_fit_flow_transition_map` | 可视化分析・可视化・统计・模型 | Model fit diagnostic - Flow transition map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_model_fit_forest_interval_plot` | 可视化分析・可视化・统计・模型・随机森林 | 随机森林 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_model_fit_heatmap_matrix` | 可视化分析・可视化・统计・模型・热力矩阵 | 热力矩阵 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_model_fit_histogram_facets` | 可视化分析・可视化・统计・模型・直方图 | 直方图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_model_fit_map_choropleth_layer` | 可视化分析・可视化・统计・模型・分级着色地图 | 分级着色地图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_model_fit_mosaic_tile_view` | 可视化分析・可视化・统计・模型 | Model fit diagnostic - Mosaic tile view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_model_fit_network_node_link` | 可视化分析・可视化・统计・模型・网络 | 关系网络 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_model_fit_qq_reference_plot` | 可视化分析・可视化・统计・模型 | Model fit diagnostic - Q-Q reference plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_model_fit_quantile_band` | 可视化分析・可视化・统计・模型・分位数 | 分位数 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_model_fit_raincloud_view` | 可视化分析・可视化・统计・模型 | Model fit diagnostic - Raincloud view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_model_fit_rank_interval_plot` | 可视化分析・可视化・统计・模型・排名 | 排名 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_model_fit_residual_annotation_map` | 可视化分析・可视化・统计・模型 | Model fit diagnostic - Residual annotation map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_model_fit_slope_change_view` | 可视化分析・可视化・统计・模型 | Model fit diagnostic - Slope change view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_model_fit_small_multiple_grid` | 可视化分析・可视化・统计・模型 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_model_fit_stratified_dotplot` | 可视化分析・可视化・统计・模型 | Model fit diagnostic - Stratified dot plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_model_fit_threshold_band` | 可视化分析・可视化・统计・模型 | Model fit diagnostic - Threshold band | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_model_fit_uncertainty_ribbon` | 可视化分析・可视化・统计・模型 | Model fit diagnostic - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_model_fit_violin_summary` | 可视化分析・可视化・统计・模型・小提琴图・概览 | 小提琴图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_multivariate_projection_annotated_reference_view` | 可视化分析・可视化・统计 | Multivariate projection - Annotated reference view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_multivariate_projection_boxen_interval` | 可视化分析・可视化・统计 | Multivariate projection - Boxen interval plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_multivariate_projection_comparative_lollipop` | 可视化分析・可视化・统计 | Multivariate projection - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_multivariate_projection_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_multivariate_projection_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Multivariate projection - Diagnostic panel | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_multivariate_projection_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_multivariate_projection_flow_transition_map` | 可视化分析・可视化・统计 | Multivariate projection - Flow transition map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_multivariate_projection_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_multivariate_projection_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_multivariate_projection_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_multivariate_projection_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_multivariate_projection_mosaic_tile_view` | 可视化分析・可视化・统计 | Multivariate projection - Mosaic tile view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_multivariate_projection_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_multivariate_projection_qq_reference_plot` | 可视化分析・可视化・统计 | Multivariate projection - Q-Q reference plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_multivariate_projection_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_multivariate_projection_raincloud_view` | 可视化分析・可视化・统计 | Multivariate projection - Raincloud view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_multivariate_projection_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_multivariate_projection_residual_annotation_map` | 可视化分析・可视化・统计 | Multivariate projection - Residual annotation map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_multivariate_projection_slope_change_view` | 可视化分析・可视化・统计 | Multivariate projection - Slope change view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_multivariate_projection_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_multivariate_projection_stratified_dotplot` | 可视化分析・可视化・统计 | Multivariate projection - Stratified dot plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_multivariate_projection_threshold_band` | 可视化分析・可视化・统计 | Multivariate projection - Threshold band | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_multivariate_projection_uncertainty_ribbon` | 可视化分析・可视化・统计 | Multivariate projection - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_multivariate_projection_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_bridge_annotated_reference_view` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_bridge_boxen_interval` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_bridge_comparative_lollipop` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_bridge_density_ridge` | 可视化分析・可视化・统计・网络・密度图 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_bridge_diagnostic_panel` | 可视化分析・可视化・统计・网络・诊断・面板 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_bridge_ecdf_step_view` | 可视化分析・可视化・统计・网络・经验分布图 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_bridge_flow_transition_map` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_bridge_forest_interval_plot` | 可视化分析・可视化・统计・网络・随机森林 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_bridge_heatmap_matrix` | 可视化分析・可视化・统计・网络・热力矩阵 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_bridge_histogram_facets` | 可视化分析・可视化・统计・网络・直方图 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_bridge_map_choropleth_layer` | 可视化分析・可视化・统计・网络・分级着色地图 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_bridge_mosaic_tile_view` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_bridge_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_bridge_qq_reference_plot` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_bridge_quantile_band` | 可视化分析・可视化・统计・网络・分位数 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_bridge_raincloud_view` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_bridge_rank_interval_plot` | 可视化分析・可视化・统计・网络・排名 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_bridge_residual_annotation_map` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_bridge_slope_change_view` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_bridge_small_multiple_grid` | 可视化分析・可视化・统计・网络 | 小多图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_bridge_stratified_dotplot` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_bridge_threshold_band` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_bridge_uncertainty_ribbon` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_bridge_violin_summary` | 可视化分析・可视化・统计・网络・小提琴图・概览 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_centrality_annotated_reference_view` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_centrality_boxen_interval` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_centrality_comparative_lollipop` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_centrality_density_ridge` | 可视化分析・可视化・统计・网络・密度图 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_centrality_diagnostic_panel` | 可视化分析・可视化・统计・网络・诊断・面板 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_centrality_ecdf_step_view` | 可视化分析・可视化・统计・网络・经验分布图 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_centrality_flow_transition_map` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_centrality_forest_interval_plot` | 可视化分析・可视化・统计・网络・随机森林 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_centrality_heatmap_matrix` | 可视化分析・可视化・统计・网络・热力矩阵 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_centrality_histogram_facets` | 可视化分析・可视化・统计・网络・直方图 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_centrality_map_choropleth_layer` | 可视化分析・可视化・统计・网络・分级着色地图 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_centrality_mosaic_tile_view` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_centrality_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_centrality_qq_reference_plot` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_centrality_quantile_band` | 可视化分析・可视化・统计・网络・分位数 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_centrality_raincloud_view` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_centrality_rank_interval_plot` | 可视化分析・可视化・统计・网络・排名 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_centrality_residual_annotation_map` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_centrality_slope_change_view` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_centrality_small_multiple_grid` | 可视化分析・可视化・统计・网络 | 小多图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_centrality_stratified_dotplot` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_centrality_threshold_band` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_centrality_uncertainty_ribbon` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_centrality_violin_summary` | 可视化分析・可视化・统计・网络・小提琴图・概览 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_diffusion_annotated_reference_view` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_diffusion_boxen_interval` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_diffusion_comparative_lollipop` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_diffusion_density_ridge` | 可视化分析・可视化・统计・网络・密度图 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_diffusion_diagnostic_panel` | 可视化分析・可视化・统计・网络・诊断・面板 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_diffusion_ecdf_step_view` | 可视化分析・可视化・统计・网络・经验分布图 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_diffusion_flow_transition_map` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_diffusion_forest_interval_plot` | 可视化分析・可视化・统计・网络・随机森林 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_diffusion_heatmap_matrix` | 可视化分析・可视化・统计・网络・热力矩阵 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_diffusion_histogram_facets` | 可视化分析・可视化・统计・网络・直方图 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_diffusion_map_choropleth_layer` | 可视化分析・可视化・统计・网络・分级着色地图 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_diffusion_mosaic_tile_view` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_diffusion_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_diffusion_qq_reference_plot` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_diffusion_quantile_band` | 可视化分析・可视化・统计・网络・分位数 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_diffusion_raincloud_view` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_diffusion_rank_interval_plot` | 可视化分析・可视化・统计・网络・排名 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_diffusion_residual_annotation_map` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_diffusion_slope_change_view` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_diffusion_small_multiple_grid` | 可视化分析・可视化・统计・网络 | 小多图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_diffusion_stratified_dotplot` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_diffusion_threshold_band` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_diffusion_uncertainty_ribbon` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_network_diffusion_violin_summary` | 可视化分析・可视化・统计・网络・小提琴图・概览 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_fit_shape_annotated_reference_view` | 可视化分析・可视化・统计 | Nonlinear fit shape - Annotated reference view | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_fit_shape_boxen_interval` | 可视化分析・可视化・统计 | Nonlinear fit shape - Boxen interval plot | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_fit_shape_comparative_lollipop` | 可视化分析・可视化・统计 | Nonlinear fit shape - Comparative lollipop plot | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_fit_shape_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_fit_shape_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Nonlinear fit shape - Diagnostic panel | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_fit_shape_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_fit_shape_flow_transition_map` | 可视化分析・可视化・统计 | Nonlinear fit shape - Flow transition map | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_fit_shape_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_fit_shape_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_fit_shape_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_fit_shape_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_fit_shape_mosaic_tile_view` | 可视化分析・可视化・统计 | Nonlinear fit shape - Mosaic tile view | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_fit_shape_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_fit_shape_qq_reference_plot` | 可视化分析・可视化・统计 | Nonlinear fit shape - Q-Q reference plot | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_fit_shape_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_fit_shape_raincloud_view` | 可视化分析・可视化・统计 | Nonlinear fit shape - Raincloud view | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_fit_shape_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_fit_shape_residual_annotation_map` | 可视化分析・可视化・统计 | Nonlinear fit shape - Residual annotation map | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_fit_shape_slope_change_view` | 可视化分析・可视化・统计 | Nonlinear fit shape - Slope change view | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_fit_shape_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_fit_shape_stratified_dotplot` | 可视化分析・可视化・统计 | Nonlinear fit shape - Stratified dot plot | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_fit_shape_threshold_band` | 可视化分析・可视化・统计 | Nonlinear fit shape - Threshold band | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_fit_shape_uncertainty_ribbon` | 可视化分析・可视化・统计 | Nonlinear fit shape - Uncertainty ribbon | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_fit_shape_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_relationship_annotated_reference_view` | 可视化分析・可视化・统计 | Nonlinear relationship - Annotated reference view | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_relationship_boxen_interval` | 可视化分析・可视化・统计 | Nonlinear relationship - Boxen interval plot | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_relationship_comparative_lollipop` | 可视化分析・可视化・统计 | Nonlinear relationship - Comparative lollipop plot | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_relationship_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_relationship_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Nonlinear relationship - Diagnostic panel | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_relationship_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_relationship_flow_transition_map` | 可视化分析・可视化・统计 | Nonlinear relationship - Flow transition map | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_relationship_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_relationship_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_relationship_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_relationship_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_relationship_mosaic_tile_view` | 可视化分析・可视化・统计 | Nonlinear relationship - Mosaic tile view | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_relationship_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_relationship_qq_reference_plot` | 可视化分析・可视化・统计 | Nonlinear relationship - Q-Q reference plot | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_relationship_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_relationship_raincloud_view` | 可视化分析・可视化・统计 | Nonlinear relationship - Raincloud view | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_relationship_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_relationship_residual_annotation_map` | 可视化分析・可视化・统计 | Nonlinear relationship - Residual annotation map | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_relationship_slope_change_view` | 可视化分析・可视化・统计 | Nonlinear relationship - Slope change view | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_relationship_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_relationship_stratified_dotplot` | 可视化分析・可视化・统计 | Nonlinear relationship - Stratified dot plot | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_relationship_threshold_band` | 可视化分析・可视化・统计 | Nonlinear relationship - Threshold band | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_relationship_uncertainty_ribbon` | 可视化分析・可视化・统计 | Nonlinear relationship - Uncertainty ribbon | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonlinear_relationship_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonresponse_pattern_annotated_reference_view` | 可视化分析・可视化・统计 | Nonresponse pattern - Annotated reference view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonresponse_pattern_boxen_interval` | 可视化分析・可视化・统计 | Nonresponse pattern - Boxen interval plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonresponse_pattern_comparative_lollipop` | 可视化分析・可视化・统计 | Nonresponse pattern - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonresponse_pattern_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonresponse_pattern_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Nonresponse pattern - Diagnostic panel | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonresponse_pattern_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonresponse_pattern_flow_transition_map` | 可视化分析・可视化・统计 | Nonresponse pattern - Flow transition map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonresponse_pattern_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonresponse_pattern_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonresponse_pattern_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonresponse_pattern_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonresponse_pattern_mosaic_tile_view` | 可视化分析・可视化・统计 | Nonresponse pattern - Mosaic tile view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonresponse_pattern_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonresponse_pattern_qq_reference_plot` | 可视化分析・可视化・统计 | Nonresponse pattern - Q-Q reference plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonresponse_pattern_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonresponse_pattern_raincloud_view` | 可视化分析・可视化・统计 | Nonresponse pattern - Raincloud view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonresponse_pattern_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonresponse_pattern_residual_annotation_map` | 可视化分析・可视化・统计 | Nonresponse pattern - Residual annotation map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonresponse_pattern_slope_change_view` | 可视化分析・可视化・统计 | Nonresponse pattern - Slope change view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonresponse_pattern_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonresponse_pattern_stratified_dotplot` | 可视化分析・可视化・统计 | Nonresponse pattern - Stratified dot plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonresponse_pattern_threshold_band` | 可视化分析・可视化・统计 | Nonresponse pattern - Threshold band | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonresponse_pattern_uncertainty_ribbon` | 可视化分析・可视化・统计 | Nonresponse pattern - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_nonresponse_pattern_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_operations_capacity_annotated_reference_view` | 可视化分析・可视化・统计 | Operations capacity - Annotated reference view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_operations_capacity_boxen_interval` | 可视化分析・可视化・统计 | Operations capacity - Boxen interval plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_operations_capacity_comparative_lollipop` | 可视化分析・可视化・统计 | Operations capacity - Comparative lollipop plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_operations_capacity_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_operations_capacity_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Operations capacity - Diagnostic panel | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_operations_capacity_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_operations_capacity_flow_transition_map` | 可视化分析・可视化・统计 | Operations capacity - Flow transition map | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_operations_capacity_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_operations_capacity_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_operations_capacity_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_operations_capacity_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_operations_capacity_mosaic_tile_view` | 可视化分析・可视化・统计 | Operations capacity - Mosaic tile view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_operations_capacity_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_operations_capacity_qq_reference_plot` | 可视化分析・可视化・统计 | Operations capacity - Q-Q reference plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_operations_capacity_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_operations_capacity_raincloud_view` | 可视化分析・可视化・统计 | Operations capacity - Raincloud view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_operations_capacity_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_operations_capacity_residual_annotation_map` | 可视化分析・可视化・统计 | Operations capacity - Residual annotation map | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_operations_capacity_slope_change_view` | 可视化分析・可视化・统计 | Operations capacity - Slope change view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_operations_capacity_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_operations_capacity_stratified_dotplot` | 可视化分析・可视化・统计 | Operations capacity - Stratified dot plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_operations_capacity_threshold_band` | 可视化分析・可视化・统计 | Operations capacity - Threshold band | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_operations_capacity_uncertainty_ribbon` | 可视化分析・可视化・统计 | Operations capacity - Uncertainty ribbon | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_operations_capacity_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_ordinal_response_annotated_reference_view` | 可视化分析・可视化・统计 | Ordinal response profile - Annotated reference view | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_ordinal_response_boxen_interval` | 可视化分析・可视化・统计 | Ordinal response profile - Boxen interval plot | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_ordinal_response_comparative_lollipop` | 可视化分析・可视化・统计 | Ordinal response profile - Comparative lollipop plot | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_ordinal_response_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_ordinal_response_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Ordinal response profile - Diagnostic panel | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_ordinal_response_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_ordinal_response_flow_transition_map` | 可视化分析・可视化・统计 | Ordinal response profile - Flow transition map | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_ordinal_response_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_ordinal_response_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_ordinal_response_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_ordinal_response_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_ordinal_response_mosaic_tile_view` | 可视化分析・可视化・统计 | Ordinal response profile - Mosaic tile view | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_ordinal_response_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_ordinal_response_qq_reference_plot` | 可视化分析・可视化・统计 | Ordinal response profile - Q-Q reference plot | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_ordinal_response_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_ordinal_response_raincloud_view` | 可视化分析・可视化・统计 | Ordinal response profile - Raincloud view | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_ordinal_response_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_ordinal_response_residual_annotation_map` | 可视化分析・可视化・统计 | Ordinal response profile - Residual annotation map | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_ordinal_response_slope_change_view` | 可视化分析・可视化・统计 | Ordinal response profile - Slope change view | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_ordinal_response_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_ordinal_response_stratified_dotplot` | 可视化分析・可视化・统计 | Ordinal response profile - Stratified dot plot | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_ordinal_response_threshold_band` | 可视化分析・可视化・统计 | Ordinal response profile - Threshold band | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_ordinal_response_uncertainty_ribbon` | 可视化分析・可视化・统计 | Ordinal response profile - Uncertainty ribbon | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_ordinal_response_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 分类字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_outlier_influence_annotated_reference_view` | 可视化分析・可视化・统计・离群值 | Outlier influence - Annotated reference view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_outlier_influence_boxen_interval` | 可视化分析・可视化・统计・离群值 | Outlier influence - Boxen interval plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_outlier_influence_comparative_lollipop` | 可视化分析・可视化・统计・离群值 | Outlier influence - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_outlier_influence_density_ridge` | 可视化分析・可视化・统计・离群值・密度图 | 密度图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_outlier_influence_diagnostic_panel` | 可视化分析・可视化・统计・离群值・诊断・面板 | Outlier influence - Diagnostic panel | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_outlier_influence_ecdf_step_view` | 可视化分析・可视化・统计・离群值・经验分布图 | 经验分布图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_outlier_influence_flow_transition_map` | 可视化分析・可视化・统计・离群值 | Outlier influence - Flow transition map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_outlier_influence_forest_interval_plot` | 可视化分析・可视化・统计・离群值・随机森林 | 随机森林 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_outlier_influence_heatmap_matrix` | 可视化分析・可视化・统计・离群值・热力矩阵 | 热力矩阵 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_outlier_influence_histogram_facets` | 可视化分析・可视化・统计・离群值・直方图 | 直方图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_outlier_influence_map_choropleth_layer` | 可视化分析・可视化・统计・离群值・分级着色地图 | 分级着色地图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_outlier_influence_mosaic_tile_view` | 可视化分析・可视化・统计・离群值 | Outlier influence - Mosaic tile view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_outlier_influence_network_node_link` | 可视化分析・可视化・统计・离群值・网络 | 关系网络 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_outlier_influence_qq_reference_plot` | 可视化分析・可视化・统计・离群值 | Outlier influence - Q-Q reference plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_outlier_influence_quantile_band` | 可视化分析・可视化・统计・离群值・分位数 | 分位数 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_outlier_influence_raincloud_view` | 可视化分析・可视化・统计・离群值 | Outlier influence - Raincloud view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_outlier_influence_rank_interval_plot` | 可视化分析・可视化・统计・离群值・排名 | 排名 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_outlier_influence_residual_annotation_map` | 可视化分析・可视化・统计・离群值 | Outlier influence - Residual annotation map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_outlier_influence_slope_change_view` | 可视化分析・可视化・统计・离群值 | Outlier influence - Slope change view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_outlier_influence_small_multiple_grid` | 可视化分析・可视化・统计・离群值 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_outlier_influence_stratified_dotplot` | 可视化分析・可视化・统计・离群值 | Outlier influence - Stratified dot plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_outlier_influence_threshold_band` | 可视化分析・可视化・统计・离群值 | Outlier influence - Threshold band | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_outlier_influence_uncertainty_ribbon` | 可视化分析・可视化・统计・离群值 | Outlier influence - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_outlier_influence_violin_summary` | 可视化分析・可视化・统计・离群值・小提琴图・概览 | 小提琴图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_paired_change_annotated_reference_view` | 可视化分析・可视化・统计 | Paired change - Annotated reference view | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_paired_change_boxen_interval` | 可视化分析・可视化・统计 | Paired change - Boxen interval plot | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_paired_change_comparative_lollipop` | 可视化分析・可视化・统计 | Paired change - Comparative lollipop plot | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_paired_change_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_paired_change_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Paired change - Diagnostic panel | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_paired_change_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_paired_change_flow_transition_map` | 可视化分析・可视化・统计 | Paired change - Flow transition map | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_paired_change_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_paired_change_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_paired_change_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_paired_change_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_paired_change_mosaic_tile_view` | 可视化分析・可视化・统计 | Paired change - Mosaic tile view | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_paired_change_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_paired_change_qq_reference_plot` | 可视化分析・可视化・统计 | Paired change - Q-Q reference plot | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_paired_change_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_paired_change_raincloud_view` | 可视化分析・可视化・统计 | Paired change - Raincloud view | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_paired_change_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_paired_change_residual_annotation_map` | 可视化分析・可视化・统计 | Paired change - Residual annotation map | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_paired_change_slope_change_view` | 可视化分析・可视化・统计 | Paired change - Slope change view | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_paired_change_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_paired_change_stratified_dotplot` | 可视化分析・可视化・统计 | Paired change - Stratified dot plot | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_paired_change_threshold_band` | 可视化分析・可视化・统计 | Paired change - Threshold band | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_paired_change_uncertainty_ribbon` | 可视化分析・可视化・统计 | Paired change - Uncertainty ribbon | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_paired_change_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_partial_association_annotated_reference_view` | 可视化分析・可视化・统计・偏相关 | 偏相关 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_partial_association_boxen_interval` | 可视化分析・可视化・统计・偏相关 | 偏相关 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_partial_association_comparative_lollipop` | 可视化分析・可视化・统计・偏相关 | 偏相关 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_partial_association_density_ridge` | 可视化分析・可视化・统计・偏相关・密度图 | 偏相关 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_partial_association_diagnostic_panel` | 可视化分析・可视化・统计・偏相关・诊断・面板 | 偏相关 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_partial_association_ecdf_step_view` | 可视化分析・可视化・统计・偏相关・经验分布图 | 偏相关 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_partial_association_flow_transition_map` | 可视化分析・可视化・统计・偏相关 | 偏相关 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_partial_association_forest_interval_plot` | 可视化分析・可视化・统计・偏相关・随机森林 | 偏相关 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_partial_association_heatmap_matrix` | 可视化分析・可视化・统计・偏相关・热力矩阵 | 偏相关 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_partial_association_histogram_facets` | 可视化分析・可视化・统计・偏相关・直方图 | 偏相关 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_partial_association_map_choropleth_layer` | 可视化分析・可视化・统计・偏相关・分级着色地图 | 偏相关 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_partial_association_mosaic_tile_view` | 可视化分析・可视化・统计・偏相关 | 偏相关 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_partial_association_network_node_link` | 可视化分析・可视化・统计・偏相关・网络 | 偏相关 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_partial_association_qq_reference_plot` | 可视化分析・可视化・统计・偏相关 | 偏相关 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_partial_association_quantile_band` | 可视化分析・可视化・统计・偏相关・分位数 | 偏相关 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_partial_association_raincloud_view` | 可视化分析・可视化・统计・偏相关 | 偏相关 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_partial_association_rank_interval_plot` | 可视化分析・可视化・统计・偏相关・排名 | 偏相关 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_partial_association_residual_annotation_map` | 可视化分析・可视化・统计・偏相关 | 偏相关 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_partial_association_slope_change_view` | 可视化分析・可视化・统计・偏相关 | 偏相关 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_partial_association_small_multiple_grid` | 可视化分析・可视化・统计・偏相关 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_partial_association_stratified_dotplot` | 可视化分析・可视化・统计・偏相关 | 偏相关 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_partial_association_threshold_band` | 可视化分析・可视化・统计・偏相关 | 偏相关 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_partial_association_uncertainty_ribbon` | 可视化分析・可视化・统计・偏相关 | 偏相关 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_partial_association_violin_summary` | 可视化分析・可视化・统计・偏相关・小提琴图・概览 | 偏相关 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_patient_trajectory_annotated_reference_view` | 可视化分析・可视化・统计 | Patient trajectory - Annotated reference view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_patient_trajectory_boxen_interval` | 可视化分析・可视化・统计 | Patient trajectory - Boxen interval plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_patient_trajectory_comparative_lollipop` | 可视化分析・可视化・统计 | Patient trajectory - Comparative lollipop plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_patient_trajectory_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_patient_trajectory_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Patient trajectory - Diagnostic panel | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_patient_trajectory_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_patient_trajectory_flow_transition_map` | 可视化分析・可视化・统计 | Patient trajectory - Flow transition map | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_patient_trajectory_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_patient_trajectory_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_patient_trajectory_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_patient_trajectory_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_patient_trajectory_mosaic_tile_view` | 可视化分析・可视化・统计 | Patient trajectory - Mosaic tile view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_patient_trajectory_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_patient_trajectory_qq_reference_plot` | 可视化分析・可视化・统计 | Patient trajectory - Q-Q reference plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_patient_trajectory_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_patient_trajectory_raincloud_view` | 可视化分析・可视化・统计 | Patient trajectory - Raincloud view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_patient_trajectory_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_patient_trajectory_residual_annotation_map` | 可视化分析・可视化・统计 | Patient trajectory - Residual annotation map | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_patient_trajectory_slope_change_view` | 可视化分析・可视化・统计 | Patient trajectory - Slope change view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_patient_trajectory_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_patient_trajectory_stratified_dotplot` | 可视化分析・可视化・统计 | Patient trajectory - Stratified dot plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_patient_trajectory_threshold_band` | 可视化分析・可视化・统计 | Patient trajectory - Threshold band | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_patient_trajectory_uncertainty_ribbon` | 可视化分析・可视化・统计 | Patient trajectory - Uncertainty ribbon | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_patient_trajectory_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_error_annotated_reference_view` | 可视化分析・可视化・统计・误差 | Prediction error - Annotated reference view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_error_boxen_interval` | 可视化分析・可视化・统计・误差 | Prediction error - Boxen interval plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_error_comparative_lollipop` | 可视化分析・可视化・统计・误差 | Prediction error - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_error_density_ridge` | 可视化分析・可视化・统计・误差・密度图 | 密度图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_error_diagnostic_panel` | 可视化分析・可视化・统计・误差・诊断・面板 | Prediction error - Diagnostic panel | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_error_ecdf_step_view` | 可视化分析・可视化・统计・误差・经验分布图 | 经验分布图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_error_flow_transition_map` | 可视化分析・可视化・统计・误差 | Prediction error - Flow transition map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_error_forest_interval_plot` | 可视化分析・可视化・统计・误差・随机森林 | 随机森林 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_error_heatmap_matrix` | 可视化分析・可视化・统计・误差・热力矩阵 | 热力矩阵 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_error_histogram_facets` | 可视化分析・可视化・统计・误差・直方图 | 直方图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_error_map_choropleth_layer` | 可视化分析・可视化・统计・误差・分级着色地图 | 分级着色地图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_error_mosaic_tile_view` | 可视化分析・可视化・统计・误差 | Prediction error - Mosaic tile view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_error_network_node_link` | 可视化分析・可视化・统计・误差・网络 | 关系网络 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_error_qq_reference_plot` | 可视化分析・可视化・统计・误差 | Prediction error - Q-Q reference plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_error_quantile_band` | 可视化分析・可视化・统计・误差・分位数 | 分位数 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_error_raincloud_view` | 可视化分析・可视化・统计・误差 | Prediction error - Raincloud view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_error_rank_interval_plot` | 可视化分析・可视化・统计・误差・排名 | 排名 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_error_residual_annotation_map` | 可视化分析・可视化・统计・误差 | Prediction error - Residual annotation map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_error_slope_change_view` | 可视化分析・可视化・统计・误差 | Prediction error - Slope change view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_error_small_multiple_grid` | 可视化分析・可视化・统计・误差 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_error_stratified_dotplot` | 可视化分析・可视化・统计・误差 | Prediction error - Stratified dot plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_error_threshold_band` | 可视化分析・可视化・统计・误差 | Prediction error - Threshold band | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_error_uncertainty_ribbon` | 可视化分析・可视化・统计・误差 | Prediction error - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_error_violin_summary` | 可视化分析・可视化・统计・误差・小提琴图・概览 | 小提琴图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_interval_annotated_reference_view` | 可视化分析・可视化・统计 | Prediction interval - Annotated reference view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_interval_boxen_interval` | 可视化分析・可视化・统计 | Prediction interval - Boxen interval plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_interval_comparative_lollipop` | 可视化分析・可视化・统计 | Prediction interval - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_interval_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_interval_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Prediction interval - Diagnostic panel | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_interval_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_interval_flow_transition_map` | 可视化分析・可视化・统计 | Prediction interval - Flow transition map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_interval_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_interval_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_interval_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_interval_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_interval_mosaic_tile_view` | 可视化分析・可视化・统计 | Prediction interval - Mosaic tile view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_interval_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_interval_qq_reference_plot` | 可视化分析・可视化・统计 | Prediction interval - Q-Q reference plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_interval_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_interval_raincloud_view` | 可视化分析・可视化・统计 | Prediction interval - Raincloud view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_interval_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_interval_residual_annotation_map` | 可视化分析・可视化・统计 | Prediction interval - Residual annotation map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_interval_slope_change_view` | 可视化分析・可视化・统计 | Prediction interval - Slope change view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_interval_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_interval_stratified_dotplot` | 可视化分析・可视化・统计 | Prediction interval - Stratified dot plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_interval_threshold_band` | 可视化分析・可视化・统计 | Prediction interval - Threshold band | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_interval_uncertainty_ribbon` | 可视化分析・可视化・统计 | Prediction interval - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_prediction_interval_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_principal_component_variance_annotated_reference_view` | 可视化分析・可视化・统计・方差 | 方差 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_principal_component_variance_boxen_interval` | 可视化分析・可视化・统计・方差 | 方差 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_principal_component_variance_comparative_lollipop` | 可视化分析・可视化・统计・方差 | 方差 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_principal_component_variance_density_ridge` | 可视化分析・可视化・统计・方差・密度图 | 方差 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_principal_component_variance_diagnostic_panel` | 可视化分析・可视化・统计・方差・诊断・面板 | 方差 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_principal_component_variance_ecdf_step_view` | 可视化分析・可视化・统计・方差・经验分布图 | 方差 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_principal_component_variance_flow_transition_map` | 可视化分析・可视化・统计・方差 | 方差 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_principal_component_variance_forest_interval_plot` | 可视化分析・可视化・统计・方差・随机森林 | 方差 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_principal_component_variance_heatmap_matrix` | 可视化分析・可视化・统计・方差・热力矩阵 | 方差 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_principal_component_variance_histogram_facets` | 可视化分析・可视化・统计・方差・直方图 | 方差 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_principal_component_variance_map_choropleth_layer` | 可视化分析・可视化・统计・方差・分级着色地图 | 方差 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_principal_component_variance_mosaic_tile_view` | 可视化分析・可视化・统计・方差 | 方差 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_principal_component_variance_network_node_link` | 可视化分析・可视化・统计・方差・网络 | 方差 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_principal_component_variance_qq_reference_plot` | 可视化分析・可视化・统计・方差 | 方差 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_principal_component_variance_quantile_band` | 可视化分析・可视化・统计・方差・分位数 | 方差 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_principal_component_variance_raincloud_view` | 可视化分析・可视化・统计・方差 | 方差 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_principal_component_variance_rank_interval_plot` | 可视化分析・可视化・统计・方差・排名 | 方差 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_principal_component_variance_residual_annotation_map` | 可视化分析・可视化・统计・方差 | 方差 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_principal_component_variance_slope_change_view` | 可视化分析・可视化・统计・方差 | 方差 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_principal_component_variance_small_multiple_grid` | 可视化分析・可视化・统计・方差 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_principal_component_variance_stratified_dotplot` | 可视化分析・可视化・统计・方差 | 方差 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_principal_component_variance_threshold_band` | 可视化分析・可视化・统计・方差 | 方差 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_principal_component_variance_uncertainty_ribbon` | 可视化分析・可视化・统计・方差 | 方差 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_principal_component_variance_violin_summary` | 可视化分析・可视化・统计・方差・小提琴图・概览 | 方差 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_propensity_overlap_annotated_reference_view` | 可视化分析・可视化・统计 | Propensity overlap - Annotated reference view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_propensity_overlap_boxen_interval` | 可视化分析・可视化・统计 | Propensity overlap - Boxen interval plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_propensity_overlap_comparative_lollipop` | 可视化分析・可视化・统计 | Propensity overlap - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_propensity_overlap_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_propensity_overlap_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Propensity overlap - Diagnostic panel | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_propensity_overlap_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_propensity_overlap_flow_transition_map` | 可视化分析・可视化・统计 | Propensity overlap - Flow transition map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_propensity_overlap_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_propensity_overlap_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_propensity_overlap_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_propensity_overlap_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_propensity_overlap_mosaic_tile_view` | 可视化分析・可视化・统计 | Propensity overlap - Mosaic tile view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_propensity_overlap_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_propensity_overlap_qq_reference_plot` | 可视化分析・可视化・统计 | Propensity overlap - Q-Q reference plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_propensity_overlap_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_propensity_overlap_raincloud_view` | 可视化分析・可视化・统计 | Propensity overlap - Raincloud view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_propensity_overlap_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_propensity_overlap_residual_annotation_map` | 可视化分析・可视化・统计 | Propensity overlap - Residual annotation map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_propensity_overlap_slope_change_view` | 可视化分析・可视化・统计 | Propensity overlap - Slope change view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_propensity_overlap_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_propensity_overlap_stratified_dotplot` | 可视化分析・可视化・统计 | Propensity overlap - Stratified dot plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_propensity_overlap_threshold_band` | 可视化分析・可视化・统计 | Propensity overlap - Threshold band | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_propensity_overlap_uncertainty_ribbon` | 可视化分析・可视化・统计 | Propensity overlap - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_propensity_overlap_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_public_health_incidence_annotated_reference_view` | 可视化分析・可视化・统计・健康度 | Public health incidence - Annotated reference view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_public_health_incidence_boxen_interval` | 可视化分析・可视化・统计・健康度 | Public health incidence - Boxen interval plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_public_health_incidence_comparative_lollipop` | 可视化分析・可视化・统计・健康度 | Public health incidence - Comparative lollipop plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_public_health_incidence_density_ridge` | 可视化分析・可视化・统计・健康度・密度图 | 密度图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_public_health_incidence_diagnostic_panel` | 可视化分析・可视化・统计・健康度・诊断・面板 | Public health incidence - Diagnostic panel | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_public_health_incidence_ecdf_step_view` | 可视化分析・可视化・统计・健康度・经验分布图 | 经验分布图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_public_health_incidence_flow_transition_map` | 可视化分析・可视化・统计・健康度 | Public health incidence - Flow transition map | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_public_health_incidence_forest_interval_plot` | 可视化分析・可视化・统计・健康度・随机森林 | 随机森林 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_public_health_incidence_heatmap_matrix` | 可视化分析・可视化・统计・健康度・热力矩阵 | 热力矩阵 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_public_health_incidence_histogram_facets` | 可视化分析・可视化・统计・健康度・直方图 | 直方图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_public_health_incidence_map_choropleth_layer` | 可视化分析・可视化・统计・健康度・分级着色地图 | 分级着色地图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_public_health_incidence_mosaic_tile_view` | 可视化分析・可视化・统计・健康度 | Public health incidence - Mosaic tile view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_public_health_incidence_network_node_link` | 可视化分析・可视化・统计・健康度・网络 | 关系网络 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_public_health_incidence_qq_reference_plot` | 可视化分析・可视化・统计・健康度 | Public health incidence - Q-Q reference plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_public_health_incidence_quantile_band` | 可视化分析・可视化・统计・健康度・分位数 | 分位数 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_public_health_incidence_raincloud_view` | 可视化分析・可视化・统计・健康度 | Public health incidence - Raincloud view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_public_health_incidence_rank_interval_plot` | 可视化分析・可视化・统计・健康度・排名 | 排名 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_public_health_incidence_residual_annotation_map` | 可视化分析・可视化・统计・健康度 | Public health incidence - Residual annotation map | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_public_health_incidence_slope_change_view` | 可视化分析・可视化・统计・健康度 | Public health incidence - Slope change view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_public_health_incidence_small_multiple_grid` | 可视化分析・可视化・统计・健康度 | 小多图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_public_health_incidence_stratified_dotplot` | 可视化分析・可视化・统计・健康度 | Public health incidence - Stratified dot plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_public_health_incidence_threshold_band` | 可视化分析・可视化・统计・健康度 | Public health incidence - Threshold band | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_public_health_incidence_uncertainty_ribbon` | 可视化分析・可视化・统计・健康度 | Public health incidence - Uncertainty ribbon | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_public_health_incidence_violin_summary` | 可视化分析・可视化・统计・健康度・小提琴图・概览 | 小提琴图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_quality_control_annotated_reference_view` | 可视化分析・可视化・统计・质量・控制 | Quality control - Annotated reference view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_quality_control_boxen_interval` | 可视化分析・可视化・统计・质量・控制 | Quality control - Boxen interval plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_quality_control_comparative_lollipop` | 可视化分析・可视化・统计・质量・控制 | Quality control - Comparative lollipop plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_quality_control_density_ridge` | 可视化分析・可视化・统计・质量・控制・密度图 | 密度图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_quality_control_diagnostic_panel` | 可视化分析・可视化・统计・质量・控制・诊断・面板 | Quality control - Diagnostic panel | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_quality_control_ecdf_step_view` | 可视化分析・可视化・统计・质量・控制・经验分布图 | 经验分布图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_quality_control_flow_transition_map` | 可视化分析・可视化・统计・质量・控制 | Quality control - Flow transition map | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_quality_control_forest_interval_plot` | 可视化分析・可视化・统计・质量・控制・随机森林 | 随机森林 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_quality_control_heatmap_matrix` | 可视化分析・可视化・统计・质量・控制・热力矩阵 | 热力矩阵 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_quality_control_histogram_facets` | 可视化分析・可视化・统计・质量・控制・直方图 | 直方图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_quality_control_map_choropleth_layer` | 可视化分析・可视化・统计・质量・控制・分级着色地图 | 分级着色地图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_quality_control_mosaic_tile_view` | 可视化分析・可视化・统计・质量・控制 | Quality control - Mosaic tile view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_quality_control_network_node_link` | 可视化分析・可视化・统计・质量・控制・网络 | 关系网络 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_quality_control_qq_reference_plot` | 可视化分析・可视化・统计・质量・控制 | Quality control - Q-Q reference plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_quality_control_quantile_band` | 可视化分析・可视化・统计・质量・控制・分位数 | 分位数 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_quality_control_raincloud_view` | 可视化分析・可视化・统计・质量・控制 | Quality control - Raincloud view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_quality_control_rank_interval_plot` | 可视化分析・可视化・统计・质量・控制・排名 | 排名 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_quality_control_residual_annotation_map` | 可视化分析・可视化・统计・质量・控制 | Quality control - Residual annotation map | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_quality_control_slope_change_view` | 可视化分析・可视化・统计・质量・控制 | Quality control - Slope change view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_quality_control_small_multiple_grid` | 可视化分析・可视化・统计・质量・控制 | 小多图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_quality_control_stratified_dotplot` | 可视化分析・可视化・统计・质量・控制 | Quality control - Stratified dot plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_quality_control_threshold_band` | 可视化分析・可视化・统计・质量・控制 | Quality control - Threshold band | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_quality_control_uncertainty_ribbon` | 可视化分析・可视化・统计・质量・控制 | Quality control - Uncertainty ribbon | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_quality_control_violin_summary` | 可视化分析・可视化・统计・质量・控制・小提琴图・概览 | 小提琴图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_questionnaire_item_quality_annotated_reference_view` | 可视化分析・可视化・统计・质量 | Questionnaire item quality - Annotated reference view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_questionnaire_item_quality_boxen_interval` | 可视化分析・可视化・统计・质量 | Questionnaire item quality - Boxen interval plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_questionnaire_item_quality_comparative_lollipop` | 可视化分析・可视化・统计・质量 | Questionnaire item quality - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_questionnaire_item_quality_density_ridge` | 可视化分析・可视化・统计・质量・密度图 | 密度图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_questionnaire_item_quality_diagnostic_panel` | 可视化分析・可视化・统计・质量・诊断・面板 | Questionnaire item quality - Diagnostic panel | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_questionnaire_item_quality_ecdf_step_view` | 可视化分析・可视化・统计・质量・经验分布图 | 经验分布图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_questionnaire_item_quality_flow_transition_map` | 可视化分析・可视化・统计・质量 | Questionnaire item quality - Flow transition map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_questionnaire_item_quality_forest_interval_plot` | 可视化分析・可视化・统计・质量・随机森林 | 随机森林 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_questionnaire_item_quality_heatmap_matrix` | 可视化分析・可视化・统计・质量・热力矩阵 | 热力矩阵 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_questionnaire_item_quality_histogram_facets` | 可视化分析・可视化・统计・质量・直方图 | 直方图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_questionnaire_item_quality_map_choropleth_layer` | 可视化分析・可视化・统计・质量・分级着色地图 | 分级着色地图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_questionnaire_item_quality_mosaic_tile_view` | 可视化分析・可视化・统计・质量 | Questionnaire item quality - Mosaic tile view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_questionnaire_item_quality_network_node_link` | 可视化分析・可视化・统计・质量・网络 | 关系网络 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_questionnaire_item_quality_qq_reference_plot` | 可视化分析・可视化・统计・质量 | Questionnaire item quality - Q-Q reference plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_questionnaire_item_quality_quantile_band` | 可视化分析・可视化・统计・质量・分位数 | 分位数 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_questionnaire_item_quality_raincloud_view` | 可视化分析・可视化・统计・质量 | Questionnaire item quality - Raincloud view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_questionnaire_item_quality_rank_interval_plot` | 可视化分析・可视化・统计・质量・排名 | 排名 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_questionnaire_item_quality_residual_annotation_map` | 可视化分析・可视化・统计・质量 | Questionnaire item quality - Residual annotation map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_questionnaire_item_quality_slope_change_view` | 可视化分析・可视化・统计・质量 | Questionnaire item quality - Slope change view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_questionnaire_item_quality_small_multiple_grid` | 可视化分析・可视化・统计・质量 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_questionnaire_item_quality_stratified_dotplot` | 可视化分析・可视化・统计・质量 | Questionnaire item quality - Stratified dot plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_questionnaire_item_quality_threshold_band` | 可视化分析・可视化・统计・质量 | Questionnaire item quality - Threshold band | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_questionnaire_item_quality_uncertainty_ribbon` | 可视化分析・可视化・统计・质量 | Questionnaire item quality - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_questionnaire_item_quality_violin_summary` | 可视化分析・可视化・统计・质量・小提琴图・概览 | 小提琴图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_randomization_check_annotated_reference_view` | 可视化分析・可视化・统计 | Randomization check - Annotated reference view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_randomization_check_boxen_interval` | 可视化分析・可视化・统计 | Randomization check - Boxen interval plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_randomization_check_comparative_lollipop` | 可视化分析・可视化・统计 | Randomization check - Comparative lollipop plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_randomization_check_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_randomization_check_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Randomization check - Diagnostic panel | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_randomization_check_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_randomization_check_flow_transition_map` | 可视化分析・可视化・统计 | Randomization check - Flow transition map | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_randomization_check_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_randomization_check_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_randomization_check_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_randomization_check_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_randomization_check_mosaic_tile_view` | 可视化分析・可视化・统计 | Randomization check - Mosaic tile view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_randomization_check_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_randomization_check_qq_reference_plot` | 可视化分析・可视化・统计 | Randomization check - Q-Q reference plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_randomization_check_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_randomization_check_raincloud_view` | 可视化分析・可视化・统计 | Randomization check - Raincloud view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_randomization_check_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_randomization_check_residual_annotation_map` | 可视化分析・可视化・统计 | Randomization check - Residual annotation map | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_randomization_check_slope_change_view` | 可视化分析・可视化・统计 | Randomization check - Slope change view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_randomization_check_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_randomization_check_stratified_dotplot` | 可视化分析・可视化・统计 | Randomization check - Stratified dot plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_randomization_check_threshold_band` | 可视化分析・可视化・统计 | Randomization check - Threshold band | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_randomization_check_uncertainty_ribbon` | 可视化分析・可视化・统计 | Randomization check - Uncertainty ribbon | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_randomization_check_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_regional_inequality_annotated_reference_view` | 可视化分析・可视化・统计 | Regional inequality - Annotated reference view | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_regional_inequality_boxen_interval` | 可视化分析・可视化・统计 | Regional inequality - Boxen interval plot | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_regional_inequality_comparative_lollipop` | 可视化分析・可视化・统计 | Regional inequality - Comparative lollipop plot | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_regional_inequality_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_regional_inequality_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Regional inequality - Diagnostic panel | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_regional_inequality_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_regional_inequality_flow_transition_map` | 可视化分析・可视化・统计 | Regional inequality - Flow transition map | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_regional_inequality_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_regional_inequality_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_regional_inequality_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_regional_inequality_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_regional_inequality_mosaic_tile_view` | 可视化分析・可视化・统计 | Regional inequality - Mosaic tile view | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_regional_inequality_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_regional_inequality_qq_reference_plot` | 可视化分析・可视化・统计 | Regional inequality - Q-Q reference plot | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_regional_inequality_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_regional_inequality_raincloud_view` | 可视化分析・可视化・统计 | Regional inequality - Raincloud view | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_regional_inequality_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_regional_inequality_residual_annotation_map` | 可视化分析・可视化・统计 | Regional inequality - Residual annotation map | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_regional_inequality_slope_change_view` | 可视化分析・可视化・统计 | Regional inequality - Slope change view | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_regional_inequality_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_regional_inequality_stratified_dotplot` | 可视化分析・可视化・统计 | Regional inequality - Stratified dot plot | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_regional_inequality_threshold_band` | 可视化分析・可视化・统计 | Regional inequality - Threshold band | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_regional_inequality_uncertainty_ribbon` | 可视化分析・可视化・统计 | Regional inequality - Uncertainty ribbon | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_regional_inequality_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_regularization_path_annotated_reference_view` | 可视化分析・可视化・统计 | Regularization path - Annotated reference view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_regularization_path_boxen_interval` | 可视化分析・可视化・统计 | Regularization path - Boxen interval plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_regularization_path_comparative_lollipop` | 可视化分析・可视化・统计 | Regularization path - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_regularization_path_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_regularization_path_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Regularization path - Diagnostic panel | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_regularization_path_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_regularization_path_flow_transition_map` | 可视化分析・可视化・统计 | Regularization path - Flow transition map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_regularization_path_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_regularization_path_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_regularization_path_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_regularization_path_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_regularization_path_mosaic_tile_view` | 可视化分析・可视化・统计 | Regularization path - Mosaic tile view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_regularization_path_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_regularization_path_qq_reference_plot` | 可视化分析・可视化・统计 | Regularization path - Q-Q reference plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_regularization_path_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_regularization_path_raincloud_view` | 可视化分析・可视化・统计 | Regularization path - Raincloud view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_regularization_path_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_regularization_path_residual_annotation_map` | 可视化分析・可视化・统计 | Regularization path - Residual annotation map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_regularization_path_slope_change_view` | 可视化分析・可视化・统计 | Regularization path - Slope change view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_regularization_path_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_regularization_path_stratified_dotplot` | 可视化分析・可视化・统计 | Regularization path - Stratified dot plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_regularization_path_threshold_band` | 可视化分析・可视化・统计 | Regularization path - Threshold band | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_regularization_path_uncertainty_ribbon` | 可视化分析・可视化・统计 | Regularization path - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_regularization_path_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_relationship_strength_annotated_reference_view` | 可视化分析・可视化・统计 | Relationship strength - Annotated reference view | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_relationship_strength_boxen_interval` | 可视化分析・可视化・统计 | Relationship strength - Boxen interval plot | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_relationship_strength_comparative_lollipop` | 可视化分析・可视化・统计 | Relationship strength - Comparative lollipop plot | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_relationship_strength_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_relationship_strength_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Relationship strength - Diagnostic panel | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_relationship_strength_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_relationship_strength_flow_transition_map` | 可视化分析・可视化・统计 | Relationship strength - Flow transition map | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_relationship_strength_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_relationship_strength_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_relationship_strength_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_relationship_strength_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_relationship_strength_mosaic_tile_view` | 可视化分析・可视化・统计 | Relationship strength - Mosaic tile view | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_relationship_strength_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_relationship_strength_qq_reference_plot` | 可视化分析・可视化・统计 | Relationship strength - Q-Q reference plot | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_relationship_strength_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_relationship_strength_raincloud_view` | 可视化分析・可视化・统计 | Relationship strength - Raincloud view | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_relationship_strength_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_relationship_strength_residual_annotation_map` | 可视化分析・可视化・统计 | Relationship strength - Residual annotation map | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_relationship_strength_slope_change_view` | 可视化分析・可视化・统计 | Relationship strength - Slope change view | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_relationship_strength_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_relationship_strength_stratified_dotplot` | 可视化分析・可视化・统计 | Relationship strength - Stratified dot plot | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_relationship_strength_threshold_band` | 可视化分析・可视化・统计 | Relationship strength - Threshold band | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_relationship_strength_uncertainty_ribbon` | 可视化分析・可视化・统计 | Relationship strength - Uncertainty ribbon | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_relationship_strength_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 字段对 | 规划条目 | 统计可视化目录 |
| `visual_stat_reliability_scale_annotated_reference_view` | 可视化分析・可视化・统计 | Reliability scale - Annotated reference view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_reliability_scale_boxen_interval` | 可视化分析・可视化・统计 | Reliability scale - Boxen interval plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_reliability_scale_comparative_lollipop` | 可视化分析・可视化・统计 | Reliability scale - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_reliability_scale_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_reliability_scale_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Reliability scale - Diagnostic panel | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_reliability_scale_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_reliability_scale_flow_transition_map` | 可视化分析・可视化・统计 | Reliability scale - Flow transition map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_reliability_scale_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_reliability_scale_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_reliability_scale_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_reliability_scale_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_reliability_scale_mosaic_tile_view` | 可视化分析・可视化・统计 | Reliability scale - Mosaic tile view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_reliability_scale_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_reliability_scale_qq_reference_plot` | 可视化分析・可视化・统计 | Reliability scale - Q-Q reference plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_reliability_scale_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_reliability_scale_raincloud_view` | 可视化分析・可视化・统计 | Reliability scale - Raincloud view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_reliability_scale_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_reliability_scale_residual_annotation_map` | 可视化分析・可视化・统计 | Reliability scale - Residual annotation map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_reliability_scale_slope_change_view` | 可视化分析・可视化・统计 | Reliability scale - Slope change view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_reliability_scale_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_reliability_scale_stratified_dotplot` | 可视化分析・可视化・统计 | Reliability scale - Stratified dot plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_reliability_scale_threshold_band` | 可视化分析・可视化・统计 | Reliability scale - Threshold band | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_reliability_scale_uncertainty_ribbon` | 可视化分析・可视化・统计 | Reliability scale - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_reliability_scale_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_residual_pattern_annotated_reference_view` | 可视化分析・可视化・统计 | Residual pattern - Annotated reference view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_residual_pattern_boxen_interval` | 可视化分析・可视化・统计 | Residual pattern - Boxen interval plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_residual_pattern_comparative_lollipop` | 可视化分析・可视化・统计 | Residual pattern - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_residual_pattern_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_residual_pattern_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Residual pattern - Diagnostic panel | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_residual_pattern_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_residual_pattern_flow_transition_map` | 可视化分析・可视化・统计 | Residual pattern - Flow transition map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_residual_pattern_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_residual_pattern_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_residual_pattern_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_residual_pattern_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_residual_pattern_mosaic_tile_view` | 可视化分析・可视化・统计 | Residual pattern - Mosaic tile view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_residual_pattern_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_residual_pattern_qq_reference_plot` | 可视化分析・可视化・统计 | Residual pattern - Q-Q reference plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_residual_pattern_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_residual_pattern_raincloud_view` | 可视化分析・可视化・统计 | Residual pattern - Raincloud view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_residual_pattern_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_residual_pattern_residual_annotation_map` | 可视化分析・可视化・统计 | Residual pattern - Residual annotation map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_residual_pattern_slope_change_view` | 可视化分析・可视化・统计 | Residual pattern - Slope change view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_residual_pattern_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_residual_pattern_stratified_dotplot` | 可视化分析・可视化・统计 | Residual pattern - Stratified dot plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_residual_pattern_threshold_band` | 可视化分析・可视化・统计 | Residual pattern - Threshold band | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_residual_pattern_uncertainty_ribbon` | 可视化分析・可视化・统计 | Residual pattern - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_residual_pattern_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_robust_summary_annotated_reference_view` | 可视化分析・可视化・统计・稳健・概览 | 稳健 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_robust_summary_boxen_interval` | 可视化分析・可视化・统计・稳健・概览 | 稳健 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_robust_summary_comparative_lollipop` | 可视化分析・可视化・统计・稳健・概览 | 稳健 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_robust_summary_density_ridge` | 可视化分析・可视化・统计・稳健・概览・密度图 | 稳健 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_robust_summary_diagnostic_panel` | 可视化分析・可视化・统计・稳健・概览・诊断・面板 | 稳健 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_robust_summary_ecdf_step_view` | 可视化分析・可视化・统计・稳健・概览・经验分布图 | 稳健 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_robust_summary_flow_transition_map` | 可视化分析・可视化・统计・稳健・概览 | 稳健 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_robust_summary_forest_interval_plot` | 可视化分析・可视化・统计・稳健・概览・随机森林 | 稳健 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_robust_summary_heatmap_matrix` | 可视化分析・可视化・统计・稳健・概览・热力矩阵 | 稳健 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_robust_summary_histogram_facets` | 可视化分析・可视化・统计・稳健・概览・直方图 | 稳健 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_robust_summary_map_choropleth_layer` | 可视化分析・可视化・统计・稳健・概览・分级着色地图 | 稳健 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_robust_summary_mosaic_tile_view` | 可视化分析・可视化・统计・稳健・概览 | 稳健 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_robust_summary_network_node_link` | 可视化分析・可视化・统计・稳健・概览・网络 | 稳健 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_robust_summary_qq_reference_plot` | 可视化分析・可视化・统计・稳健・概览 | 稳健 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_robust_summary_quantile_band` | 可视化分析・可视化・统计・稳健・概览・分位数 | 稳健 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_robust_summary_raincloud_view` | 可视化分析・可视化・统计・稳健・概览 | 稳健 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_robust_summary_rank_interval_plot` | 可视化分析・可视化・统计・稳健・概览・排名 | 稳健 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_robust_summary_residual_annotation_map` | 可视化分析・可视化・统计・稳健・概览 | 稳健 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_robust_summary_slope_change_view` | 可视化分析・可视化・统计・稳健・概览 | 稳健 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_robust_summary_small_multiple_grid` | 可视化分析・可视化・统计・稳健・概览 | 小多图 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_robust_summary_stratified_dotplot` | 可视化分析・可视化・统计・稳健・概览 | 稳健 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_robust_summary_threshold_band` | 可视化分析・可视化・统计・稳健・概览 | 稳健 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_robust_summary_uncertainty_ribbon` | 可视化分析・可视化・统计・稳健・概览 | 稳健 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_robust_summary_violin_summary` | 可视化分析・可视化・统计・稳健・概览・小提琴图 | 稳健 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_coverage_annotated_reference_view` | 可视化分析・可视化・统计・覆盖情况 | 覆盖情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_coverage_boxen_interval` | 可视化分析・可视化・统计・覆盖情况 | 覆盖情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_coverage_comparative_lollipop` | 可视化分析・可视化・统计・覆盖情况 | 覆盖情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_coverage_density_ridge` | 可视化分析・可视化・统计・覆盖情况・密度图 | 覆盖情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_coverage_diagnostic_panel` | 可视化分析・可视化・统计・覆盖情况・诊断・面板 | 覆盖情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_coverage_ecdf_step_view` | 可视化分析・可视化・统计・覆盖情况・经验分布图 | 覆盖情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_coverage_flow_transition_map` | 可视化分析・可视化・统计・覆盖情况 | 覆盖情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_coverage_forest_interval_plot` | 可视化分析・可视化・统计・覆盖情况・随机森林 | 覆盖情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_coverage_heatmap_matrix` | 可视化分析・可视化・统计・覆盖情况・热力矩阵 | 覆盖情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_coverage_histogram_facets` | 可视化分析・可视化・统计・覆盖情况・直方图 | 覆盖情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_coverage_map_choropleth_layer` | 可视化分析・可视化・统计・覆盖情况・分级着色地图 | 覆盖情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_coverage_mosaic_tile_view` | 可视化分析・可视化・统计・覆盖情况 | 覆盖情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_coverage_network_node_link` | 可视化分析・可视化・统计・覆盖情况・网络 | 覆盖情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_coverage_qq_reference_plot` | 可视化分析・可视化・统计・覆盖情况 | 覆盖情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_coverage_quantile_band` | 可视化分析・可视化・统计・覆盖情况・分位数 | 覆盖情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_coverage_raincloud_view` | 可视化分析・可视化・统计・覆盖情况 | 覆盖情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_coverage_rank_interval_plot` | 可视化分析・可视化・统计・覆盖情况・排名 | 覆盖情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_coverage_residual_annotation_map` | 可视化分析・可视化・统计・覆盖情况 | 覆盖情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_coverage_slope_change_view` | 可视化分析・可视化・统计・覆盖情况 | 覆盖情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_coverage_small_multiple_grid` | 可视化分析・可视化・统计・覆盖情况 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_coverage_stratified_dotplot` | 可视化分析・可视化・统计・覆盖情况 | 覆盖情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_coverage_threshold_band` | 可视化分析・可视化・统计・覆盖情况 | 覆盖情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_coverage_uncertainty_ribbon` | 可视化分析・可视化・统计・覆盖情况 | 覆盖情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_coverage_violin_summary` | 可视化分析・可视化・统计・覆盖情况・小提琴图・概览 | 覆盖情况 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_weight_effect_annotated_reference_view` | 可视化分析・可视化・统计・效应 | Sample weight effect - Annotated reference view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_weight_effect_boxen_interval` | 可视化分析・可视化・统计・效应 | Sample weight effect - Boxen interval plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_weight_effect_comparative_lollipop` | 可视化分析・可视化・统计・效应 | Sample weight effect - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_weight_effect_density_ridge` | 可视化分析・可视化・统计・效应・密度图 | 密度图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_weight_effect_diagnostic_panel` | 可视化分析・可视化・统计・效应・诊断・面板 | Sample weight effect - Diagnostic panel | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_weight_effect_ecdf_step_view` | 可视化分析・可视化・统计・效应・经验分布图 | 经验分布图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_weight_effect_flow_transition_map` | 可视化分析・可视化・统计・效应 | Sample weight effect - Flow transition map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_weight_effect_forest_interval_plot` | 可视化分析・可视化・统计・效应・随机森林 | 随机森林 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_weight_effect_heatmap_matrix` | 可视化分析・可视化・统计・效应・热力矩阵 | 热力矩阵 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_weight_effect_histogram_facets` | 可视化分析・可视化・统计・效应・直方图 | 直方图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_weight_effect_map_choropleth_layer` | 可视化分析・可视化・统计・效应・分级着色地图 | 分级着色地图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_weight_effect_mosaic_tile_view` | 可视化分析・可视化・统计・效应 | Sample weight effect - Mosaic tile view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_weight_effect_network_node_link` | 可视化分析・可视化・统计・效应・网络 | 关系网络 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_weight_effect_qq_reference_plot` | 可视化分析・可视化・统计・效应 | Sample weight effect - Q-Q reference plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_weight_effect_quantile_band` | 可视化分析・可视化・统计・效应・分位数 | 分位数 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_weight_effect_raincloud_view` | 可视化分析・可视化・统计・效应 | Sample weight effect - Raincloud view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_weight_effect_rank_interval_plot` | 可视化分析・可视化・统计・效应・排名 | 排名 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_weight_effect_residual_annotation_map` | 可视化分析・可视化・统计・效应 | Sample weight effect - Residual annotation map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_weight_effect_slope_change_view` | 可视化分析・可视化・统计・效应 | Sample weight effect - Slope change view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_weight_effect_small_multiple_grid` | 可视化分析・可视化・统计・效应 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_weight_effect_stratified_dotplot` | 可视化分析・可视化・统计・效应 | Sample weight effect - Stratified dot plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_weight_effect_threshold_band` | 可视化分析・可视化・统计・效应 | Sample weight effect - Threshold band | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_weight_effect_uncertainty_ribbon` | 可视化分析・可视化・统计・效应 | Sample weight effect - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sample_weight_effect_violin_summary` | 可视化分析・可视化・统计・效应・小提琴图・概览 | 小提琴图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_scale_score_profile_annotated_reference_view` | 可视化分析・可视化・统计・评分・画像 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_scale_score_profile_boxen_interval` | 可视化分析・可视化・统计・评分・画像 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_scale_score_profile_comparative_lollipop` | 可视化分析・可视化・统计・评分・画像 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_scale_score_profile_density_ridge` | 可视化分析・可视化・统计・评分・画像・密度图 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_scale_score_profile_diagnostic_panel` | 可视化分析・可视化・统计・评分・画像・诊断・面板 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_scale_score_profile_ecdf_step_view` | 可视化分析・可视化・统计・评分・画像・经验分布图 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_scale_score_profile_flow_transition_map` | 可视化分析・可视化・统计・评分・画像 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_scale_score_profile_forest_interval_plot` | 可视化分析・可视化・统计・评分・画像・随机森林 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_scale_score_profile_heatmap_matrix` | 可视化分析・可视化・统计・评分・画像・热力矩阵 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_scale_score_profile_histogram_facets` | 可视化分析・可视化・统计・评分・画像・直方图 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_scale_score_profile_map_choropleth_layer` | 可视化分析・可视化・统计・评分・画像・分级着色地图 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_scale_score_profile_mosaic_tile_view` | 可视化分析・可视化・统计・评分・画像 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_scale_score_profile_network_node_link` | 可视化分析・可视化・统计・评分・画像・网络 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_scale_score_profile_qq_reference_plot` | 可视化分析・可视化・统计・评分・画像 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_scale_score_profile_quantile_band` | 可视化分析・可视化・统计・评分・画像・分位数 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_scale_score_profile_raincloud_view` | 可视化分析・可视化・统计・评分・画像 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_scale_score_profile_rank_interval_plot` | 可视化分析・可视化・统计・评分・画像・排名 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_scale_score_profile_residual_annotation_map` | 可视化分析・可视化・统计・评分・画像 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_scale_score_profile_slope_change_view` | 可视化分析・可视化・统计・评分・画像 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_scale_score_profile_small_multiple_grid` | 可视化分析・可视化・统计・评分・画像 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_scale_score_profile_stratified_dotplot` | 可视化分析・可视化・统计・评分・画像 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_scale_score_profile_threshold_band` | 可视化分析・可视化・统计・评分・画像 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_scale_score_profile_uncertainty_ribbon` | 可视化分析・可视化・统计・评分・画像 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_scale_score_profile_violin_summary` | 可视化分析・可视化・统计・评分・画像・小提琴图・概览 | 画像 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_seasonality_pattern_annotated_reference_view` | 可视化分析・可视化・统计・季节性 | 季节性 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_seasonality_pattern_boxen_interval` | 可视化分析・可视化・统计・季节性 | 季节性 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_seasonality_pattern_comparative_lollipop` | 可视化分析・可视化・统计・季节性 | 季节性 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_seasonality_pattern_density_ridge` | 可视化分析・可视化・统计・季节性・密度图 | 季节性 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_seasonality_pattern_diagnostic_panel` | 可视化分析・可视化・统计・季节性・诊断・面板 | 季节性 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_seasonality_pattern_ecdf_step_view` | 可视化分析・可视化・统计・季节性・经验分布图 | 季节性 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_seasonality_pattern_flow_transition_map` | 可视化分析・可视化・统计・季节性 | 季节性 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_seasonality_pattern_forest_interval_plot` | 可视化分析・可视化・统计・季节性・随机森林 | 季节性 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_seasonality_pattern_heatmap_matrix` | 可视化分析・可视化・统计・季节性・热力矩阵 | 季节性 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_seasonality_pattern_histogram_facets` | 可视化分析・可视化・统计・季节性・直方图 | 季节性 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_seasonality_pattern_map_choropleth_layer` | 可视化分析・可视化・统计・季节性・分级着色地图 | 季节性 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_seasonality_pattern_mosaic_tile_view` | 可视化分析・可视化・统计・季节性 | 季节性 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_seasonality_pattern_network_node_link` | 可视化分析・可视化・统计・季节性・网络 | 季节性 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_seasonality_pattern_qq_reference_plot` | 可视化分析・可视化・统计・季节性 | 季节性 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_seasonality_pattern_quantile_band` | 可视化分析・可视化・统计・季节性・分位数 | 季节性 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_seasonality_pattern_raincloud_view` | 可视化分析・可视化・统计・季节性 | 季节性 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_seasonality_pattern_rank_interval_plot` | 可视化分析・可视化・统计・季节性・排名 | 季节性 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_seasonality_pattern_residual_annotation_map` | 可视化分析・可视化・统计・季节性 | 季节性 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_seasonality_pattern_slope_change_view` | 可视化分析・可视化・统计・季节性 | 季节性 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_seasonality_pattern_small_multiple_grid` | 可视化分析・可视化・统计・季节性 | 小多图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_seasonality_pattern_stratified_dotplot` | 可视化分析・可视化・统计・季节性 | 季节性 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_seasonality_pattern_threshold_band` | 可视化分析・可视化・统计・季节性 | 季节性 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_seasonality_pattern_uncertainty_ribbon` | 可视化分析・可视化・统计・季节性 | 季节性 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_seasonality_pattern_violin_summary` | 可视化分析・可视化・统计・季节性・小提琴图・概览 | 季节性 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_sensitivity_bounds_annotated_reference_view` | 可视化分析・可视化・统计・敏感性 | 敏感性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sensitivity_bounds_boxen_interval` | 可视化分析・可视化・统计・敏感性 | 敏感性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sensitivity_bounds_comparative_lollipop` | 可视化分析・可视化・统计・敏感性 | 敏感性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sensitivity_bounds_density_ridge` | 可视化分析・可视化・统计・敏感性・密度图 | 敏感性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sensitivity_bounds_diagnostic_panel` | 可视化分析・可视化・统计・敏感性・诊断・面板 | 敏感性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sensitivity_bounds_ecdf_step_view` | 可视化分析・可视化・统计・敏感性・经验分布图 | 敏感性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sensitivity_bounds_flow_transition_map` | 可视化分析・可视化・统计・敏感性 | 敏感性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sensitivity_bounds_forest_interval_plot` | 可视化分析・可视化・统计・敏感性・随机森林 | 敏感性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sensitivity_bounds_heatmap_matrix` | 可视化分析・可视化・统计・敏感性・热力矩阵 | 敏感性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sensitivity_bounds_histogram_facets` | 可视化分析・可视化・统计・敏感性・直方图 | 敏感性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sensitivity_bounds_map_choropleth_layer` | 可视化分析・可视化・统计・敏感性・分级着色地图 | 敏感性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sensitivity_bounds_mosaic_tile_view` | 可视化分析・可视化・统计・敏感性 | 敏感性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sensitivity_bounds_network_node_link` | 可视化分析・可视化・统计・敏感性・网络 | 敏感性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sensitivity_bounds_qq_reference_plot` | 可视化分析・可视化・统计・敏感性 | 敏感性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sensitivity_bounds_quantile_band` | 可视化分析・可视化・统计・敏感性・分位数 | 敏感性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sensitivity_bounds_raincloud_view` | 可视化分析・可视化・统计・敏感性 | 敏感性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sensitivity_bounds_rank_interval_plot` | 可视化分析・可视化・统计・敏感性・排名 | 敏感性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sensitivity_bounds_residual_annotation_map` | 可视化分析・可视化・统计・敏感性 | 敏感性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sensitivity_bounds_slope_change_view` | 可视化分析・可视化・统计・敏感性 | 敏感性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sensitivity_bounds_small_multiple_grid` | 可视化分析・可视化・统计・敏感性 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sensitivity_bounds_stratified_dotplot` | 可视化分析・可视化・统计・敏感性 | 敏感性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sensitivity_bounds_threshold_band` | 可视化分析・可视化・统计・敏感性 | 敏感性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sensitivity_bounds_uncertainty_ribbon` | 可视化分析・可视化・统计・敏感性 | 敏感性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sensitivity_bounds_violin_summary` | 可视化分析・可视化・统计・敏感性・小提琴图・概览 | 敏感性 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sentiment_distribution_annotated_reference_view` | 可视化分析・可视化・统计・分布 | 分布 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sentiment_distribution_boxen_interval` | 可视化分析・可视化・统计・分布 | 分布 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sentiment_distribution_comparative_lollipop` | 可视化分析・可视化・统计・分布 | 分布 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sentiment_distribution_density_ridge` | 可视化分析・可视化・统计・分布・密度图 | 分布 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sentiment_distribution_diagnostic_panel` | 可视化分析・可视化・统计・分布・诊断・面板 | 分布 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sentiment_distribution_ecdf_step_view` | 可视化分析・可视化・统计・分布・经验分布图 | 分布 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sentiment_distribution_flow_transition_map` | 可视化分析・可视化・统计・分布 | 分布 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sentiment_distribution_forest_interval_plot` | 可视化分析・可视化・统计・分布・随机森林 | 分布 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sentiment_distribution_heatmap_matrix` | 可视化分析・可视化・统计・分布・热力矩阵 | 分布 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sentiment_distribution_histogram_facets` | 可视化分析・可视化・统计・分布・直方图 | 分布 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sentiment_distribution_map_choropleth_layer` | 可视化分析・可视化・统计・分布・分级着色地图 | 分布 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sentiment_distribution_mosaic_tile_view` | 可视化分析・可视化・统计・分布 | 分布 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sentiment_distribution_network_node_link` | 可视化分析・可视化・统计・分布・网络 | 分布 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sentiment_distribution_qq_reference_plot` | 可视化分析・可视化・统计・分布 | 分布 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sentiment_distribution_quantile_band` | 可视化分析・可视化・统计・分布・分位数 | 分布 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sentiment_distribution_raincloud_view` | 可视化分析・可视化・统计・分布 | 分布 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sentiment_distribution_rank_interval_plot` | 可视化分析・可视化・统计・分布・排名 | 分布 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sentiment_distribution_residual_annotation_map` | 可视化分析・可视化・统计・分布 | 分布 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sentiment_distribution_slope_change_view` | 可视化分析・可视化・统计・分布 | 分布 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sentiment_distribution_small_multiple_grid` | 可视化分析・可视化・统计・分布 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sentiment_distribution_stratified_dotplot` | 可视化分析・可视化・统计・分布 | 分布 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sentiment_distribution_threshold_band` | 可视化分析・可视化・统计・分布 | 分布 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sentiment_distribution_uncertainty_ribbon` | 可视化分析・可视化・统计・分布 | 分布 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sentiment_distribution_violin_summary` | 可视化分析・可视化・统计・分布・小提琴图・概览 | 分布 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_sequential_monitoring_annotated_reference_view` | 可视化分析・可视化・统计 | Sequential monitoring - Annotated reference view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_sequential_monitoring_boxen_interval` | 可视化分析・可视化・统计 | Sequential monitoring - Boxen interval plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_sequential_monitoring_comparative_lollipop` | 可视化分析・可视化・统计 | Sequential monitoring - Comparative lollipop plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_sequential_monitoring_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_sequential_monitoring_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Sequential monitoring - Diagnostic panel | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_sequential_monitoring_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_sequential_monitoring_flow_transition_map` | 可视化分析・可视化・统计 | Sequential monitoring - Flow transition map | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_sequential_monitoring_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_sequential_monitoring_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_sequential_monitoring_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_sequential_monitoring_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_sequential_monitoring_mosaic_tile_view` | 可视化分析・可视化・统计 | Sequential monitoring - Mosaic tile view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_sequential_monitoring_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_sequential_monitoring_qq_reference_plot` | 可视化分析・可视化・统计 | Sequential monitoring - Q-Q reference plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_sequential_monitoring_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_sequential_monitoring_raincloud_view` | 可视化分析・可视化・统计 | Sequential monitoring - Raincloud view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_sequential_monitoring_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_sequential_monitoring_residual_annotation_map` | 可视化分析・可视化・统计 | Sequential monitoring - Residual annotation map | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_sequential_monitoring_slope_change_view` | 可视化分析・可视化・统计 | Sequential monitoring - Slope change view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_sequential_monitoring_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_sequential_monitoring_stratified_dotplot` | 可视化分析・可视化・统计 | Sequential monitoring - Stratified dot plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_sequential_monitoring_threshold_band` | 可视化分析・可视化・统计 | Sequential monitoring - Threshold band | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_sequential_monitoring_uncertainty_ribbon` | 可视化分析・可视化・统计 | Sequential monitoring - Uncertainty ribbon | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_sequential_monitoring_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_service_queue_pattern_annotated_reference_view` | 可视化分析・可视化・统计 | Service queue pattern - Annotated reference view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_service_queue_pattern_boxen_interval` | 可视化分析・可视化・统计 | Service queue pattern - Boxen interval plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_service_queue_pattern_comparative_lollipop` | 可视化分析・可视化・统计 | Service queue pattern - Comparative lollipop plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_service_queue_pattern_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_service_queue_pattern_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Service queue pattern - Diagnostic panel | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_service_queue_pattern_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_service_queue_pattern_flow_transition_map` | 可视化分析・可视化・统计 | Service queue pattern - Flow transition map | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_service_queue_pattern_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_service_queue_pattern_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_service_queue_pattern_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_service_queue_pattern_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_service_queue_pattern_mosaic_tile_view` | 可视化分析・可视化・统计 | Service queue pattern - Mosaic tile view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_service_queue_pattern_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_service_queue_pattern_qq_reference_plot` | 可视化分析・可视化・统计 | Service queue pattern - Q-Q reference plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_service_queue_pattern_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_service_queue_pattern_raincloud_view` | 可视化分析・可视化・统计 | Service queue pattern - Raincloud view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_service_queue_pattern_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_service_queue_pattern_residual_annotation_map` | 可视化分析・可视化・统计 | Service queue pattern - Residual annotation map | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_service_queue_pattern_slope_change_view` | 可视化分析・可视化・统计 | Service queue pattern - Slope change view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_service_queue_pattern_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_service_queue_pattern_stratified_dotplot` | 可视化分析・可视化・统计 | Service queue pattern - Stratified dot plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_service_queue_pattern_threshold_band` | 可视化分析・可视化・统计 | Service queue pattern - Threshold band | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_service_queue_pattern_uncertainty_ribbon` | 可视化分析・可视化・统计 | Service queue pattern - Uncertainty ribbon | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_service_queue_pattern_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_accessibility_annotated_reference_view` | 可视化分析・可视化・统计・空间 | Spatial accessibility - Annotated reference view | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_accessibility_boxen_interval` | 可视化分析・可视化・统计・空间 | Spatial accessibility - Boxen interval plot | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_accessibility_comparative_lollipop` | 可视化分析・可视化・统计・空间 | Spatial accessibility - Comparative lollipop plot | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_accessibility_density_ridge` | 可视化分析・可视化・统计・空间・密度图 | 密度图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_accessibility_diagnostic_panel` | 可视化分析・可视化・统计・空间・诊断・面板 | Spatial accessibility - Diagnostic panel | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_accessibility_ecdf_step_view` | 可视化分析・可视化・统计・空间・经验分布图 | 经验分布图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_accessibility_flow_transition_map` | 可视化分析・可视化・统计・空间 | Spatial accessibility - Flow transition map | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_accessibility_forest_interval_plot` | 可视化分析・可视化・统计・空间・随机森林 | 随机森林 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_accessibility_heatmap_matrix` | 可视化分析・可视化・统计・空间・热力矩阵 | 热力矩阵 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_accessibility_histogram_facets` | 可视化分析・可视化・统计・空间・直方图 | 直方图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_accessibility_map_choropleth_layer` | 可视化分析・可视化・统计・空间・分级着色地图 | 分级着色地图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_accessibility_mosaic_tile_view` | 可视化分析・可视化・统计・空间 | Spatial accessibility - Mosaic tile view | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_accessibility_network_node_link` | 可视化分析・可视化・统计・空间・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_accessibility_qq_reference_plot` | 可视化分析・可视化・统计・空间 | Spatial accessibility - Q-Q reference plot | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_accessibility_quantile_band` | 可视化分析・可视化・统计・空间・分位数 | 分位数 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_accessibility_raincloud_view` | 可视化分析・可视化・统计・空间 | Spatial accessibility - Raincloud view | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_accessibility_rank_interval_plot` | 可视化分析・可视化・统计・空间・排名 | 排名 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_accessibility_residual_annotation_map` | 可视化分析・可视化・统计・空间 | Spatial accessibility - Residual annotation map | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_accessibility_slope_change_view` | 可视化分析・可视化・统计・空间 | Spatial accessibility - Slope change view | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_accessibility_small_multiple_grid` | 可视化分析・可视化・统计・空间 | 小多图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_accessibility_stratified_dotplot` | 可视化分析・可视化・统计・空间 | Spatial accessibility - Stratified dot plot | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_accessibility_threshold_band` | 可视化分析・可视化・统计・空间 | Spatial accessibility - Threshold band | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_accessibility_uncertainty_ribbon` | 可视化分析・可视化・统计・空间 | Spatial accessibility - Uncertainty ribbon | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_accessibility_violin_summary` | 可视化分析・可视化・统计・空间・小提琴图・概览 | 小提琴图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_autocorrelation_annotated_reference_view` | 可视化分析・可视化・统计・空间 | Spatial autocorrelation - Annotated reference view | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_autocorrelation_boxen_interval` | 可视化分析・可视化・统计・空间 | Spatial autocorrelation - Boxen interval plot | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_autocorrelation_comparative_lollipop` | 可视化分析・可视化・统计・空间 | Spatial autocorrelation - Comparative lollipop plot | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_autocorrelation_density_ridge` | 可视化分析・可视化・统计・空间・密度图 | 密度图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_autocorrelation_diagnostic_panel` | 可视化分析・可视化・统计・空间・诊断・面板 | Spatial autocorrelation - Diagnostic panel | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_autocorrelation_ecdf_step_view` | 可视化分析・可视化・统计・空间・经验分布图 | 经验分布图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_autocorrelation_flow_transition_map` | 可视化分析・可视化・统计・空间 | Spatial autocorrelation - Flow transition map | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_autocorrelation_forest_interval_plot` | 可视化分析・可视化・统计・空间・随机森林 | 随机森林 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_autocorrelation_heatmap_matrix` | 可视化分析・可视化・统计・空间・热力矩阵 | 热力矩阵 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_autocorrelation_histogram_facets` | 可视化分析・可视化・统计・空间・直方图 | 直方图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_autocorrelation_map_choropleth_layer` | 可视化分析・可视化・统计・空间・分级着色地图 | 分级着色地图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_autocorrelation_mosaic_tile_view` | 可视化分析・可视化・统计・空间 | Spatial autocorrelation - Mosaic tile view | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_autocorrelation_network_node_link` | 可视化分析・可视化・统计・空间・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_autocorrelation_qq_reference_plot` | 可视化分析・可视化・统计・空间 | Spatial autocorrelation - Q-Q reference plot | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_autocorrelation_quantile_band` | 可视化分析・可视化・统计・空间・分位数 | 分位数 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_autocorrelation_raincloud_view` | 可视化分析・可视化・统计・空间 | Spatial autocorrelation - Raincloud view | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_autocorrelation_rank_interval_plot` | 可视化分析・可视化・统计・空间・排名 | 排名 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_autocorrelation_residual_annotation_map` | 可视化分析・可视化・统计・空间 | Spatial autocorrelation - Residual annotation map | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_autocorrelation_slope_change_view` | 可视化分析・可视化・统计・空间 | Spatial autocorrelation - Slope change view | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_autocorrelation_small_multiple_grid` | 可视化分析・可视化・统计・空间 | 小多图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_autocorrelation_stratified_dotplot` | 可视化分析・可视化・统计・空间 | Spatial autocorrelation - Stratified dot plot | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_autocorrelation_threshold_band` | 可视化分析・可视化・统计・空间 | Spatial autocorrelation - Threshold band | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_autocorrelation_uncertainty_ribbon` | 可视化分析・可视化・统计・空间 | Spatial autocorrelation - Uncertainty ribbon | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_autocorrelation_violin_summary` | 可视化分析・可视化・统计・空间・小提琴图・概览 | 小提琴图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_hotspot_annotated_reference_view` | 可视化分析・可视化・统计・空间 | Spatial hotspot - Annotated reference view | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_hotspot_boxen_interval` | 可视化分析・可视化・统计・空间 | Spatial hotspot - Boxen interval plot | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_hotspot_comparative_lollipop` | 可视化分析・可视化・统计・空间 | Spatial hotspot - Comparative lollipop plot | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_hotspot_density_ridge` | 可视化分析・可视化・统计・空间・密度图 | 密度图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_hotspot_diagnostic_panel` | 可视化分析・可视化・统计・空间・诊断・面板 | Spatial hotspot - Diagnostic panel | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_hotspot_ecdf_step_view` | 可视化分析・可视化・统计・空间・经验分布图 | 经验分布图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_hotspot_flow_transition_map` | 可视化分析・可视化・统计・空间 | Spatial hotspot - Flow transition map | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_hotspot_forest_interval_plot` | 可视化分析・可视化・统计・空间・随机森林 | 随机森林 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_hotspot_heatmap_matrix` | 可视化分析・可视化・统计・空间・热力矩阵 | 热力矩阵 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_hotspot_histogram_facets` | 可视化分析・可视化・统计・空间・直方图 | 直方图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_hotspot_map_choropleth_layer` | 可视化分析・可视化・统计・空间・分级着色地图 | 分级着色地图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_hotspot_mosaic_tile_view` | 可视化分析・可视化・统计・空间 | Spatial hotspot - Mosaic tile view | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_hotspot_network_node_link` | 可视化分析・可视化・统计・空间・网络 | 关系网络 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_hotspot_qq_reference_plot` | 可视化分析・可视化・统计・空间 | Spatial hotspot - Q-Q reference plot | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_hotspot_quantile_band` | 可视化分析・可视化・统计・空间・分位数 | 分位数 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_hotspot_raincloud_view` | 可视化分析・可视化・统计・空间 | Spatial hotspot - Raincloud view | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_hotspot_rank_interval_plot` | 可视化分析・可视化・统计・空间・排名 | 排名 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_hotspot_residual_annotation_map` | 可视化分析・可视化・统计・空间 | Spatial hotspot - Residual annotation map | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_hotspot_slope_change_view` | 可视化分析・可视化・统计・空间 | Spatial hotspot - Slope change view | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_hotspot_small_multiple_grid` | 可视化分析・可视化・统计・空间 | 小多图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_hotspot_stratified_dotplot` | 可视化分析・可视化・统计・空间 | Spatial hotspot - Stratified dot plot | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_hotspot_threshold_band` | 可视化分析・可视化・统计・空间 | Spatial hotspot - Threshold band | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_hotspot_uncertainty_ribbon` | 可视化分析・可视化・统计・空间 | Spatial hotspot - Uncertainty ribbon | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_spatial_hotspot_violin_summary` | 可视化分析・可视化・统计・空间・小提琴图・概览 | 小提琴图 | 图表 | 对象级 | 规划条目 | 统计可视化目录 |
| `visual_stat_student_performance_distribution_annotated_reference_view` | 可视化分析・可视化・统计・性能・分布 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_student_performance_distribution_boxen_interval` | 可视化分析・可视化・统计・性能・分布 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_student_performance_distribution_comparative_lollipop` | 可视化分析・可视化・统计・性能・分布 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_student_performance_distribution_density_ridge` | 可视化分析・可视化・统计・性能・分布・密度图 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_student_performance_distribution_diagnostic_panel` | 可视化分析・可视化・统计・性能・分布・诊断・面板 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_student_performance_distribution_ecdf_step_view` | 可视化分析・可视化・统计・性能・分布・经验分布图 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_student_performance_distribution_flow_transition_map` | 可视化分析・可视化・统计・性能・分布 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_student_performance_distribution_forest_interval_plot` | 可视化分析・可视化・统计・性能・分布・随机森林 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_student_performance_distribution_heatmap_matrix` | 可视化分析・可视化・统计・性能・分布・热力矩阵 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_student_performance_distribution_histogram_facets` | 可视化分析・可视化・统计・性能・分布・直方图 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_student_performance_distribution_map_choropleth_layer` | 可视化分析・可视化・统计・性能・分布・分级着色地图 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_student_performance_distribution_mosaic_tile_view` | 可视化分析・可视化・统计・性能・分布 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_student_performance_distribution_network_node_link` | 可视化分析・可视化・统计・性能・分布・网络 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_student_performance_distribution_qq_reference_plot` | 可视化分析・可视化・统计・性能・分布 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_student_performance_distribution_quantile_band` | 可视化分析・可视化・统计・性能・分布・分位数 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_student_performance_distribution_raincloud_view` | 可视化分析・可视化・统计・性能・分布 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_student_performance_distribution_rank_interval_plot` | 可视化分析・可视化・统计・性能・分布・排名 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_student_performance_distribution_residual_annotation_map` | 可视化分析・可视化・统计・性能・分布 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_student_performance_distribution_slope_change_view` | 可视化分析・可视化・统计・性能・分布 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_student_performance_distribution_small_multiple_grid` | 可视化分析・可视化・统计・性能・分布 | 小多图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_student_performance_distribution_stratified_dotplot` | 可视化分析・可视化・统计・性能・分布 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_student_performance_distribution_threshold_band` | 可视化分析・可视化・统计・性能・分布 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_student_performance_distribution_uncertainty_ribbon` | 可视化分析・可视化・统计・性能・分布 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_student_performance_distribution_violin_summary` | 可视化分析・可视化・统计・性能・分布・小提琴图・概览 | 分布 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_subgroup_variability_annotated_reference_view` | 可视化分析・可视化・统计 | Subgroup variability - Annotated reference view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_subgroup_variability_boxen_interval` | 可视化分析・可视化・统计 | Subgroup variability - Boxen interval plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_subgroup_variability_comparative_lollipop` | 可视化分析・可视化・统计 | Subgroup variability - Comparative lollipop plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_subgroup_variability_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_subgroup_variability_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Subgroup variability - Diagnostic panel | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_subgroup_variability_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_subgroup_variability_flow_transition_map` | 可视化分析・可视化・统计 | Subgroup variability - Flow transition map | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_subgroup_variability_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_subgroup_variability_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_subgroup_variability_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_subgroup_variability_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_subgroup_variability_mosaic_tile_view` | 可视化分析・可视化・统计 | Subgroup variability - Mosaic tile view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_subgroup_variability_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_subgroup_variability_qq_reference_plot` | 可视化分析・可视化・统计 | Subgroup variability - Q-Q reference plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_subgroup_variability_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_subgroup_variability_raincloud_view` | 可视化分析・可视化・统计 | Subgroup variability - Raincloud view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_subgroup_variability_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_subgroup_variability_residual_annotation_map` | 可视化分析・可视化・统计 | Subgroup variability - Residual annotation map | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_subgroup_variability_slope_change_view` | 可视化分析・可视化・统计 | Subgroup variability - Slope change view | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_subgroup_variability_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_subgroup_variability_stratified_dotplot` | 可视化分析・可视化・统计 | Subgroup variability - Stratified dot plot | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_subgroup_variability_threshold_band` | 可视化分析・可视化・统计 | Subgroup variability - Threshold band | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_subgroup_variability_uncertainty_ribbon` | 可视化分析・可视化・统计 | Subgroup variability - Uncertainty ribbon | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_subgroup_variability_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 分组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_response_pattern_annotated_reference_view` | 可视化分析・可视化・统计 | Survey response pattern - Annotated reference view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_response_pattern_boxen_interval` | 可视化分析・可视化・统计 | Survey response pattern - Boxen interval plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_response_pattern_comparative_lollipop` | 可视化分析・可视化・统计 | Survey response pattern - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_response_pattern_density_ridge` | 可视化分析・可视化・统计・密度图 | 密度图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_response_pattern_diagnostic_panel` | 可视化分析・可视化・统计・诊断・面板 | Survey response pattern - Diagnostic panel | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_response_pattern_ecdf_step_view` | 可视化分析・可视化・统计・经验分布图 | 经验分布图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_response_pattern_flow_transition_map` | 可视化分析・可视化・统计 | Survey response pattern - Flow transition map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_response_pattern_forest_interval_plot` | 可视化分析・可视化・统计・随机森林 | 随机森林 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_response_pattern_heatmap_matrix` | 可视化分析・可视化・统计・热力矩阵 | 热力矩阵 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_response_pattern_histogram_facets` | 可视化分析・可视化・统计・直方图 | 直方图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_response_pattern_map_choropleth_layer` | 可视化分析・可视化・统计・分级着色地图 | 分级着色地图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_response_pattern_mosaic_tile_view` | 可视化分析・可视化・统计 | Survey response pattern - Mosaic tile view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_response_pattern_network_node_link` | 可视化分析・可视化・统计・网络 | 关系网络 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_response_pattern_qq_reference_plot` | 可视化分析・可视化・统计 | Survey response pattern - Q-Q reference plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_response_pattern_quantile_band` | 可视化分析・可视化・统计・分位数 | 分位数 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_response_pattern_raincloud_view` | 可视化分析・可视化・统计 | Survey response pattern - Raincloud view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_response_pattern_rank_interval_plot` | 可视化分析・可视化・统计・排名 | 排名 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_response_pattern_residual_annotation_map` | 可视化分析・可视化・统计 | Survey response pattern - Residual annotation map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_response_pattern_slope_change_view` | 可视化分析・可视化・统计 | Survey response pattern - Slope change view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_response_pattern_small_multiple_grid` | 可视化分析・可视化・统计 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_response_pattern_stratified_dotplot` | 可视化分析・可视化・统计 | Survey response pattern - Stratified dot plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_response_pattern_threshold_band` | 可视化分析・可视化・统计 | Survey response pattern - Threshold band | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_response_pattern_uncertainty_ribbon` | 可视化分析・可视化・统计 | Survey response pattern - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_response_pattern_violin_summary` | 可视化分析・可视化・统计・小提琴图・概览 | 小提琴图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_weighting_annotated_reference_view` | 可视化分析・可视化・统计・加权 | Survey weighting - Annotated reference view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_weighting_boxen_interval` | 可视化分析・可视化・统计・加权 | Survey weighting - Boxen interval plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_weighting_comparative_lollipop` | 可视化分析・可视化・统计・加权 | Survey weighting - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_weighting_density_ridge` | 可视化分析・可视化・统计・加权・密度图 | 密度图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_weighting_diagnostic_panel` | 可视化分析・可视化・统计・加权・诊断・面板 | Survey weighting - Diagnostic panel | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_weighting_ecdf_step_view` | 可视化分析・可视化・统计・加权・经验分布图 | 经验分布图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_weighting_flow_transition_map` | 可视化分析・可视化・统计・加权 | Survey weighting - Flow transition map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_weighting_forest_interval_plot` | 可视化分析・可视化・统计・加权・随机森林 | 随机森林 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_weighting_heatmap_matrix` | 可视化分析・可视化・统计・加权・热力矩阵 | 热力矩阵 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_weighting_histogram_facets` | 可视化分析・可视化・统计・加权・直方图 | 直方图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_weighting_map_choropleth_layer` | 可视化分析・可视化・统计・加权・分级着色地图 | 分级着色地图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_weighting_mosaic_tile_view` | 可视化分析・可视化・统计・加权 | Survey weighting - Mosaic tile view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_weighting_network_node_link` | 可视化分析・可视化・统计・加权・网络 | 关系网络 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_weighting_qq_reference_plot` | 可视化分析・可视化・统计・加权 | Survey weighting - Q-Q reference plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_weighting_quantile_band` | 可视化分析・可视化・统计・加权・分位数 | 分位数 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_weighting_raincloud_view` | 可视化分析・可视化・统计・加权 | Survey weighting - Raincloud view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_weighting_rank_interval_plot` | 可视化分析・可视化・统计・加权・排名 | 排名 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_weighting_residual_annotation_map` | 可视化分析・可视化・统计・加权 | Survey weighting - Residual annotation map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_weighting_slope_change_view` | 可视化分析・可视化・统计・加权 | Survey weighting - Slope change view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_weighting_small_multiple_grid` | 可视化分析・可视化・统计・加权 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_weighting_stratified_dotplot` | 可视化分析・可视化・统计・加权 | Survey weighting - Stratified dot plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_weighting_threshold_band` | 可视化分析・可视化・统计・加权 | Survey weighting - Threshold band | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_weighting_uncertainty_ribbon` | 可视化分析・可视化・统计・加权 | Survey weighting - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survey_weighting_violin_summary` | 可视化分析・可视化・统计・加权・小提琴图・概览 | 小提琴图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_curve_annotated_reference_view` | 可视化分析・可视化・统计・生存 | Survival curve - Annotated reference view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_curve_boxen_interval` | 可视化分析・可视化・统计・生存 | Survival curve - Boxen interval plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_curve_comparative_lollipop` | 可视化分析・可视化・统计・生存 | Survival curve - Comparative lollipop plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_curve_density_ridge` | 可视化分析・可视化・统计・生存・密度图 | 密度图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_curve_diagnostic_panel` | 可视化分析・可视化・统计・生存・诊断・面板 | Survival curve - Diagnostic panel | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_curve_ecdf_step_view` | 可视化分析・可视化・统计・生存・经验分布图 | 经验分布图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_curve_flow_transition_map` | 可视化分析・可视化・统计・生存 | Survival curve - Flow transition map | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_curve_forest_interval_plot` | 可视化分析・可视化・统计・生存・随机森林 | 随机森林 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_curve_heatmap_matrix` | 可视化分析・可视化・统计・生存・热力矩阵 | 热力矩阵 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_curve_histogram_facets` | 可视化分析・可视化・统计・生存・直方图 | 直方图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_curve_map_choropleth_layer` | 可视化分析・可视化・统计・生存・分级着色地图 | 分级着色地图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_curve_mosaic_tile_view` | 可视化分析・可视化・统计・生存 | Survival curve - Mosaic tile view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_curve_network_node_link` | 可视化分析・可视化・统计・生存・网络 | 关系网络 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_curve_qq_reference_plot` | 可视化分析・可视化・统计・生存 | Survival curve - Q-Q reference plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_curve_quantile_band` | 可视化分析・可视化・统计・生存・分位数 | 分位数 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_curve_raincloud_view` | 可视化分析・可视化・统计・生存 | Survival curve - Raincloud view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_curve_rank_interval_plot` | 可视化分析・可视化・统计・生存・排名 | 排名 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_curve_residual_annotation_map` | 可视化分析・可视化・统计・生存 | Survival curve - Residual annotation map | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_curve_slope_change_view` | 可视化分析・可视化・统计・生存 | Survival curve - Slope change view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_curve_small_multiple_grid` | 可视化分析・可视化・统计・生存 | 小多图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_curve_stratified_dotplot` | 可视化分析・可视化・统计・生存 | Survival curve - Stratified dot plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_curve_threshold_band` | 可视化分析・可视化・统计・生存 | Survival curve - Threshold band | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_curve_uncertainty_ribbon` | 可视化分析・可视化・统计・生存 | Survival curve - Uncertainty ribbon | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_curve_violin_summary` | 可视化分析・可视化・统计・生存・小提琴图・概览 | 小提琴图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_strata_annotated_reference_view` | 可视化分析・可视化・统计・生存 | Survival strata - Annotated reference view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_strata_boxen_interval` | 可视化分析・可视化・统计・生存 | Survival strata - Boxen interval plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_strata_comparative_lollipop` | 可视化分析・可视化・统计・生存 | Survival strata - Comparative lollipop plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_strata_density_ridge` | 可视化分析・可视化・统计・生存・密度图 | 密度图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_strata_diagnostic_panel` | 可视化分析・可视化・统计・生存・诊断・面板 | Survival strata - Diagnostic panel | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_strata_ecdf_step_view` | 可视化分析・可视化・统计・生存・经验分布图 | 经验分布图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_strata_flow_transition_map` | 可视化分析・可视化・统计・生存 | Survival strata - Flow transition map | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_strata_forest_interval_plot` | 可视化分析・可视化・统计・生存・随机森林 | 随机森林 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_strata_heatmap_matrix` | 可视化分析・可视化・统计・生存・热力矩阵 | 热力矩阵 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_strata_histogram_facets` | 可视化分析・可视化・统计・生存・直方图 | 直方图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_strata_map_choropleth_layer` | 可视化分析・可视化・统计・生存・分级着色地图 | 分级着色地图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_strata_mosaic_tile_view` | 可视化分析・可视化・统计・生存 | Survival strata - Mosaic tile view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_strata_network_node_link` | 可视化分析・可视化・统计・生存・网络 | 关系网络 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_strata_qq_reference_plot` | 可视化分析・可视化・统计・生存 | Survival strata - Q-Q reference plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_strata_quantile_band` | 可视化分析・可视化・统计・生存・分位数 | 分位数 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_strata_raincloud_view` | 可视化分析・可视化・统计・生存 | Survival strata - Raincloud view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_strata_rank_interval_plot` | 可视化分析・可视化・统计・生存・排名 | 排名 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_strata_residual_annotation_map` | 可视化分析・可视化・统计・生存 | Survival strata - Residual annotation map | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_strata_slope_change_view` | 可视化分析・可视化・统计・生存 | Survival strata - Slope change view | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_strata_small_multiple_grid` | 可视化分析・可视化・统计・生存 | 小多图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_strata_stratified_dotplot` | 可视化分析・可视化・统计・生存 | Survival strata - Stratified dot plot | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_strata_threshold_band` | 可视化分析・可视化・统计・生存 | Survival strata - Threshold band | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_strata_uncertainty_ribbon` | 可视化分析・可视化・统计・生存 | Survival strata - Uncertainty ribbon | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_survival_strata_violin_summary` | 可视化分析・可视化・统计・生存・小提琴图・概览 | 小提琴图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_tail_outlier_annotated_reference_view` | 可视化分析・可视化・统计・离群值 | Tail and outlier structure - Annotated reference view | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_tail_outlier_boxen_interval` | 可视化分析・可视化・统计・离群值 | Tail and outlier structure - Boxen interval plot | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_tail_outlier_comparative_lollipop` | 可视化分析・可视化・统计・离群值 | Tail and outlier structure - Comparative lollipop plot | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_tail_outlier_density_ridge` | 可视化分析・可视化・统计・离群值・密度图 | 密度图 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_tail_outlier_diagnostic_panel` | 可视化分析・可视化・统计・离群值・诊断・面板 | Tail and outlier structure - Diagnostic panel | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_tail_outlier_ecdf_step_view` | 可视化分析・可视化・统计・离群值・经验分布图 | 经验分布图 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_tail_outlier_flow_transition_map` | 可视化分析・可视化・统计・离群值 | Tail and outlier structure - Flow transition map | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_tail_outlier_forest_interval_plot` | 可视化分析・可视化・统计・离群值・随机森林 | 随机森林 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_tail_outlier_heatmap_matrix` | 可视化分析・可视化・统计・离群值・热力矩阵 | 热力矩阵 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_tail_outlier_histogram_facets` | 可视化分析・可视化・统计・离群值・直方图 | 直方图 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_tail_outlier_map_choropleth_layer` | 可视化分析・可视化・统计・离群值・分级着色地图 | 分级着色地图 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_tail_outlier_mosaic_tile_view` | 可视化分析・可视化・统计・离群值 | Tail and outlier structure - Mosaic tile view | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_tail_outlier_network_node_link` | 可视化分析・可视化・统计・离群值・网络 | 关系网络 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_tail_outlier_qq_reference_plot` | 可视化分析・可视化・统计・离群值 | Tail and outlier structure - Q-Q reference plot | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_tail_outlier_quantile_band` | 可视化分析・可视化・统计・离群值・分位数 | 分位数 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_tail_outlier_raincloud_view` | 可视化分析・可视化・统计・离群值 | Tail and outlier structure - Raincloud view | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_tail_outlier_rank_interval_plot` | 可视化分析・可视化・统计・离群值・排名 | 排名 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_tail_outlier_residual_annotation_map` | 可视化分析・可视化・统计・离群值 | Tail and outlier structure - Residual annotation map | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_tail_outlier_slope_change_view` | 可视化分析・可视化・统计・离群值 | Tail and outlier structure - Slope change view | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_tail_outlier_small_multiple_grid` | 可视化分析・可视化・统计・离群值 | 小多图 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_tail_outlier_stratified_dotplot` | 可视化分析・可视化・统计・离群值 | Tail and outlier structure - Stratified dot plot | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_tail_outlier_threshold_band` | 可视化分析・可视化・统计・离群值 | Tail and outlier structure - Threshold band | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_tail_outlier_uncertainty_ribbon` | 可视化分析・可视化・统计・离群值 | Tail and outlier structure - Uncertainty ribbon | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_tail_outlier_violin_summary` | 可视化分析・可视化・统计・离群值・小提琴图・概览 | 小提琴图 | 图表 | 单字段 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_frequency_annotated_reference_view` | 可视化分析・可视化・统计・文本 | Text frequency - Annotated reference view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_frequency_boxen_interval` | 可视化分析・可视化・统计・文本 | Text frequency - Boxen interval plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_frequency_comparative_lollipop` | 可视化分析・可视化・统计・文本 | Text frequency - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_frequency_density_ridge` | 可视化分析・可视化・统计・文本・密度图 | 密度图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_frequency_diagnostic_panel` | 可视化分析・可视化・统计・文本・诊断・面板 | Text frequency - Diagnostic panel | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_frequency_ecdf_step_view` | 可视化分析・可视化・统计・文本・经验分布图 | 经验分布图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_frequency_flow_transition_map` | 可视化分析・可视化・统计・文本 | Text frequency - Flow transition map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_frequency_forest_interval_plot` | 可视化分析・可视化・统计・文本・随机森林 | 随机森林 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_frequency_heatmap_matrix` | 可视化分析・可视化・统计・文本・热力矩阵 | 热力矩阵 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_frequency_histogram_facets` | 可视化分析・可视化・统计・文本・直方图 | 直方图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_frequency_map_choropleth_layer` | 可视化分析・可视化・统计・文本・分级着色地图 | 分级着色地图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_frequency_mosaic_tile_view` | 可视化分析・可视化・统计・文本 | Text frequency - Mosaic tile view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_frequency_network_node_link` | 可视化分析・可视化・统计・文本・网络 | 关系网络 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_frequency_qq_reference_plot` | 可视化分析・可视化・统计・文本 | Text frequency - Q-Q reference plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_frequency_quantile_band` | 可视化分析・可视化・统计・文本・分位数 | 分位数 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_frequency_raincloud_view` | 可视化分析・可视化・统计・文本 | Text frequency - Raincloud view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_frequency_rank_interval_plot` | 可视化分析・可视化・统计・文本・排名 | 排名 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_frequency_residual_annotation_map` | 可视化分析・可视化・统计・文本 | Text frequency - Residual annotation map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_frequency_slope_change_view` | 可视化分析・可视化・统计・文本 | Text frequency - Slope change view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_frequency_small_multiple_grid` | 可视化分析・可视化・统计・文本 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_frequency_stratified_dotplot` | 可视化分析・可视化・统计・文本 | Text frequency - Stratified dot plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_frequency_threshold_band` | 可视化分析・可视化・统计・文本 | Text frequency - Threshold band | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_frequency_uncertainty_ribbon` | 可视化分析・可视化・统计・文本 | Text frequency - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_frequency_violin_summary` | 可视化分析・可视化・统计・文本・小提琴图・概览 | 小提琴图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_topic_annotated_reference_view` | 可视化分析・可视化・统计・文本・主题 | Text topic structure - Annotated reference view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_topic_boxen_interval` | 可视化分析・可视化・统计・文本・主题 | Text topic structure - Boxen interval plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_topic_comparative_lollipop` | 可视化分析・可视化・统计・文本・主题 | Text topic structure - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_topic_density_ridge` | 可视化分析・可视化・统计・文本・主题・密度图 | 密度图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_topic_diagnostic_panel` | 可视化分析・可视化・统计・文本・主题・诊断・面板 | Text topic structure - Diagnostic panel | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_topic_ecdf_step_view` | 可视化分析・可视化・统计・文本・主题・经验分布图 | 经验分布图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_topic_flow_transition_map` | 可视化分析・可视化・统计・文本・主题 | Text topic structure - Flow transition map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_topic_forest_interval_plot` | 可视化分析・可视化・统计・文本・主题・随机森林 | 随机森林 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_topic_heatmap_matrix` | 可视化分析・可视化・统计・文本・主题・热力矩阵 | 热力矩阵 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_topic_histogram_facets` | 可视化分析・可视化・统计・文本・主题・直方图 | 直方图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_topic_map_choropleth_layer` | 可视化分析・可视化・统计・文本・主题・分级着色地图 | 分级着色地图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_topic_mosaic_tile_view` | 可视化分析・可视化・统计・文本・主题 | Text topic structure - Mosaic tile view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_topic_network_node_link` | 可视化分析・可视化・统计・文本・主题・网络 | 关系网络 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_topic_qq_reference_plot` | 可视化分析・可视化・统计・文本・主题 | Text topic structure - Q-Q reference plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_topic_quantile_band` | 可视化分析・可视化・统计・文本・主题・分位数 | 分位数 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_topic_raincloud_view` | 可视化分析・可视化・统计・文本・主题 | Text topic structure - Raincloud view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_topic_rank_interval_plot` | 可视化分析・可视化・统计・文本・主题・排名 | 排名 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_topic_residual_annotation_map` | 可视化分析・可视化・统计・文本・主题 | Text topic structure - Residual annotation map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_topic_slope_change_view` | 可视化分析・可视化・统计・文本・主题 | Text topic structure - Slope change view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_topic_small_multiple_grid` | 可视化分析・可视化・统计・文本・主题 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_topic_stratified_dotplot` | 可视化分析・可视化・统计・文本・主题 | Text topic structure - Stratified dot plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_topic_threshold_band` | 可视化分析・可视化・统计・文本・主题 | Text topic structure - Threshold band | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_topic_uncertainty_ribbon` | 可视化分析・可视化・统计・文本・主题 | Text topic structure - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_text_topic_violin_summary` | 可视化分析・可视化・统计・文本・主题・小提琴图・概览 | 小提琴图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_time_trend_annotated_reference_view` | 可视化分析・可视化・统计・时间・趋势 | 趋势 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_time_trend_boxen_interval` | 可视化分析・可视化・统计・时间・趋势 | 趋势 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_time_trend_comparative_lollipop` | 可视化分析・可视化・统计・时间・趋势 | 趋势 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_time_trend_density_ridge` | 可视化分析・可视化・统计・时间・趋势・密度图 | 趋势 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_time_trend_diagnostic_panel` | 可视化分析・可视化・统计・时间・趋势・诊断・面板 | 趋势 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_time_trend_ecdf_step_view` | 可视化分析・可视化・统计・时间・趋势・经验分布图 | 趋势 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_time_trend_flow_transition_map` | 可视化分析・可视化・统计・时间・趋势 | 趋势 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_time_trend_forest_interval_plot` | 可视化分析・可视化・统计・时间・趋势・随机森林 | 趋势 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_time_trend_heatmap_matrix` | 可视化分析・可视化・统计・时间・趋势・热力矩阵 | 趋势 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_time_trend_histogram_facets` | 可视化分析・可视化・统计・时间・趋势・直方图 | 趋势 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_time_trend_map_choropleth_layer` | 可视化分析・可视化・统计・时间・趋势・分级着色地图 | 趋势 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_time_trend_mosaic_tile_view` | 可视化分析・可视化・统计・时间・趋势 | 趋势 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_time_trend_network_node_link` | 可视化分析・可视化・统计・时间・趋势・网络 | 趋势 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_time_trend_qq_reference_plot` | 可视化分析・可视化・统计・时间・趋势 | 趋势 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_time_trend_quantile_band` | 可视化分析・可视化・统计・时间・趋势・分位数 | 趋势 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_time_trend_raincloud_view` | 可视化分析・可视化・统计・时间・趋势 | 趋势 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_time_trend_rank_interval_plot` | 可视化分析・可视化・统计・时间・趋势・排名 | 趋势 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_time_trend_residual_annotation_map` | 可视化分析・可视化・统计・时间・趋势 | 趋势 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_time_trend_slope_change_view` | 可视化分析・可视化・统计・时间・趋势 | 趋势 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_time_trend_small_multiple_grid` | 可视化分析・可视化・统计・时间・趋势 | 小多图 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_time_trend_stratified_dotplot` | 可视化分析・可视化・统计・时间・趋势 | 趋势 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_time_trend_threshold_band` | 可视化分析・可视化・统计・时间・趋势 | 趋势 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_time_trend_uncertainty_ribbon` | 可视化分析・可视化・统计・时间・趋势 | 趋势 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_time_trend_violin_summary` | 可视化分析・可视化・统计・时间・趋势・小提琴图・概览 | 趋势 | 图表 | 时间窗口 | 规划条目 | 统计可视化目录 |
| `visual_stat_treatment_effect_annotated_reference_view` | 可视化分析・可视化・统计・处理・效应 | Treatment effect heterogeneity - Annotated reference view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_treatment_effect_boxen_interval` | 可视化分析・可视化・统计・处理・效应 | Treatment effect heterogeneity - Boxen interval plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_treatment_effect_comparative_lollipop` | 可视化分析・可视化・统计・处理・效应 | Treatment effect heterogeneity - Comparative lollipop plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_treatment_effect_density_ridge` | 可视化分析・可视化・统计・处理・效应・密度图 | 密度图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_treatment_effect_diagnostic_panel` | 可视化分析・可视化・统计・处理・效应・诊断・面板 | Treatment effect heterogeneity - Diagnostic panel | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_treatment_effect_ecdf_step_view` | 可视化分析・可视化・统计・处理・效应・经验分布图 | 经验分布图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_treatment_effect_flow_transition_map` | 可视化分析・可视化・统计・处理・效应 | Treatment effect heterogeneity - Flow transition map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_treatment_effect_forest_interval_plot` | 可视化分析・可视化・统计・处理・效应・随机森林 | 随机森林 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_treatment_effect_heatmap_matrix` | 可视化分析・可视化・统计・处理・效应・热力矩阵 | 热力矩阵 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_treatment_effect_histogram_facets` | 可视化分析・可视化・统计・处理・效应・直方图 | 直方图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_treatment_effect_map_choropleth_layer` | 可视化分析・可视化・统计・处理・效应・分级着色地图 | 分级着色地图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_treatment_effect_mosaic_tile_view` | 可视化分析・可视化・统计・处理・效应 | Treatment effect heterogeneity - Mosaic tile view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_treatment_effect_network_node_link` | 可视化分析・可视化・统计・处理・效应・网络 | 关系网络 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_treatment_effect_qq_reference_plot` | 可视化分析・可视化・统计・处理・效应 | Treatment effect heterogeneity - Q-Q reference plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_treatment_effect_quantile_band` | 可视化分析・可视化・统计・处理・效应・分位数 | 分位数 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_treatment_effect_raincloud_view` | 可视化分析・可视化・统计・处理・效应 | Treatment effect heterogeneity - Raincloud view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_treatment_effect_rank_interval_plot` | 可视化分析・可视化・统计・处理・效应・排名 | 排名 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_treatment_effect_residual_annotation_map` | 可视化分析・可视化・统计・处理・效应 | Treatment effect heterogeneity - Residual annotation map | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_treatment_effect_slope_change_view` | 可视化分析・可视化・统计・处理・效应 | Treatment effect heterogeneity - Slope change view | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_treatment_effect_small_multiple_grid` | 可视化分析・可视化・统计・处理・效应 | 小多图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_treatment_effect_stratified_dotplot` | 可视化分析・可视化・统计・处理・效应 | Treatment effect heterogeneity - Stratified dot plot | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_treatment_effect_threshold_band` | 可视化分析・可视化・统计・处理・效应 | Treatment effect heterogeneity - Threshold band | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_treatment_effect_uncertainty_ribbon` | 可视化分析・可视化・统计・处理・效应 | Treatment effect heterogeneity - Uncertainty ribbon | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_stat_treatment_effect_violin_summary` | 可视化分析・可视化・统计・处理・效应・小提琴图・概览 | 小提琴图 | 图表 | 字段组 | 规划条目 | 统计可视化目录 |
| `visual_streamgraph` | 可视化分析・可视化・流形图 | 流形图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_strip` | 可视化分析・可视化・条带散点图 | 条带散点图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_sunburst` | 可视化分析・可视化・旭日图 | 旭日图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_treemap` | 可视化分析・可视化・树图 | 树图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_violin` | 可视化分析・可视化・小提琴图 | 小提琴图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `visual_waterfall` | 可视化分析・可视化・瀑布图 | 瀑布图 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |

### 分析方法（注册族：`回归建模`；6 张；可运行 0 张）

| 卡片 ID | 中文方法名称 | 原始英文概念 | 中文输出形式 | 字段角色 | 状态 | 来源 |
| --- | --- | --- | --- | --- | --- | --- |
| `regression_linear` | 分析方法・回归・线性 | 线性 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `regression_logistic` | 分析方法・回归・逻辑 | 逻辑 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `regression_poisson` | 分析方法・回归・泊松 | 泊松 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `regression_quantile` | 分析方法・回归・分位数 | 分位数 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `regression_regularized` | 分析方法・回归・正则化 | 正则化 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `regression_robust` | 分析方法・回归・稳健 | 稳健 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |

### 分析方法（注册族：`因果探查`；47 张；可运行 0 张）

| 卡片 ID | 中文方法名称 | 原始英文概念 | 中文输出形式 | 字段角色 | 状态 | 来源 |
| --- | --- | --- | --- | --- | --- | --- |
| `causal_did` | 因果探查・因果・双重差分 | 双重差分 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `causal_forest_data` | 因果森林 | Causal Forest | 结构化数据 | group、outcome、features | 目录条目 | 统计目录 |
| `causal_forest_table` | 因果森林 | Causal Forest | 表格 | group、outcome、features | 目录条目 | 统计目录 |
| `causal_forest_text` | 因果森林 | Causal Forest | 文字解读 | group、outcome、features | 目录条目 | 统计目录 |
| `causal_matching` | 因果探查・因果・匹配 | 匹配 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `causal_sensitivity` | 因果探查・因果・敏感性 | 敏感性 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `causal_synthetic_control` | 因果探查・因果・控制 | 合成控制 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `causal_uplift` | 因果探查・因果・增量 | 增量 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `dag_assumption_review_data` | 因果图假设评审 | DAG Assumption Review | 结构化数据 | target、features | 目录条目 | 统计目录 |
| `dag_assumption_review_table` | 因果图假设评审 | DAG Assumption Review | 表格 | target、features | 目录条目 | 统计目录 |
| `dag_assumption_review_text` | 因果图假设评审 | DAG Assumption Review | 文字解读 | target、features | 目录条目 | 统计目录 |
| `double_machine_learning_data` | 双重机器学习 | Double Machine Learning | 结构化数据 | group、outcome、features | 目录条目 | 统计目录 |
| `double_machine_learning_table` | 双重机器学习 | Double Machine Learning | 表格 | group、outcome、features | 目录条目 | 统计目录 |
| `double_machine_learning_text` | 双重机器学习 | Double Machine Learning | 文字解读 | group、outcome、features | 目录条目 | 统计目录 |
| `doubly_robust_estimation_data` | 双重稳健估计 | Doubly Robust Estimation | 结构化数据 | group、outcome、features | 目录条目 | 统计目录 |
| `doubly_robust_estimation_table` | 双重稳健估计 | Doubly Robust Estimation | 表格 | group、outcome、features | 目录条目 | 统计目录 |
| `doubly_robust_estimation_text` | 双重稳健估计 | Doubly Robust Estimation | 文字解读 | group、outcome、features | 目录条目 | 统计目录 |
| `heterogeneous_treatment_effects_data` | 异质性处理效应 | Heterogeneous Treatment Effects | 结构化数据 | group、outcome、features | 目录条目 | 统计目录 |
| `heterogeneous_treatment_effects_table` | 异质性处理效应 | Heterogeneous Treatment Effects | 表格 | group、outcome、features | 目录条目 | 统计目录 |
| `heterogeneous_treatment_effects_text` | 异质性处理效应 | Heterogeneous Treatment Effects | 文字解读 | group、outcome、features | 目录条目 | 统计目录 |
| `instrumental_variables_data` | 工具变量法 | Instrumental Variables | 结构化数据 | target、features | 目录条目 | 统计目录 |
| `instrumental_variables_table` | 工具变量法 | Instrumental Variables | 表格 | target、features | 目录条目 | 统计目录 |
| `instrumental_variables_text` | 工具变量法 | Instrumental Variables | 文字解读 | target、features | 目录条目 | 统计目录 |
| `inverse_probability_weighting_data` | 逆概率加权 | Inverse Probability Weighting | 结构化数据 | group、outcome、features | 目录条目 | 统计目录 |
| `inverse_probability_weighting_table` | 逆概率加权 | Inverse Probability Weighting | 表格 | group、outcome、features | 目录条目 | 统计目录 |
| `inverse_probability_weighting_text` | 逆概率加权 | Inverse Probability Weighting | 文字解读 | group、outcome、features | 目录条目 | 统计目录 |
| `negative_control_exposure_data` | 负向对照暴露 | Negative Control Exposure | 结构化数据 | target、features | 目录条目 | 统计目录 |
| `negative_control_exposure_table` | 负向对照暴露 | Negative Control Exposure | 表格 | target、features | 目录条目 | 统计目录 |
| `negative_control_exposure_text` | 负向对照暴露 | Negative Control Exposure | 文字解读 | target、features | 目录条目 | 统计目录 |
| `negative_control_outcome_data` | 负向对照结果 | Negative Control Outcome | 结构化数据 | target、features | 目录条目 | 统计目录 |
| `negative_control_outcome_table` | 负向对照结果 | Negative Control Outcome | 表格 | target、features | 目录条目 | 统计目录 |
| `negative_control_outcome_text` | 负向对照结果 | Negative Control Outcome | 文字解读 | target、features | 目录条目 | 统计目录 |
| `placebo_test_data` | 安慰剂检验 | Placebo Test | 结构化数据 | target、features | 目录条目 | 统计目录 |
| `placebo_test_table` | 安慰剂检验 | Placebo Test | 表格 | target、features | 目录条目 | 统计目录 |
| `placebo_test_text` | 安慰剂检验 | Placebo Test | 文字解读 | target、features | 目录条目 | 统计目录 |
| `propensity_score_matching_data` | 倾向得分匹配 | Propensity Score Matching | 结构化数据 | group、outcome、features | 目录条目 | 统计目录 |
| `propensity_score_matching_table` | 倾向得分匹配 | Propensity Score Matching | 表格 | group、outcome、features | 目录条目 | 统计目录 |
| `propensity_score_matching_text` | 倾向得分匹配 | Propensity Score Matching | 文字解读 | group、outcome、features | 目录条目 | 统计目录 |
| `regression_discontinuity_data` | 回归不连续设计 | Regression Discontinuity | 结构化数据 | target、features | 目录条目 | 统计目录 |
| `regression_discontinuity_table` | 回归不连续设计 | Regression Discontinuity | 表格 | target、features | 目录条目 | 统计目录 |
| `regression_discontinuity_text` | 回归不连续设计 | Regression Discontinuity | 文字解读 | target、features | 目录条目 | 统计目录 |
| `spillover_interference_audit_data` | 溢出与干扰审计 | Spillover / Interference Audit | 结构化数据 | group、outcome、features | 目录条目 | 统计目录 |
| `spillover_interference_audit_table` | 溢出与干扰审计 | Spillover / Interference Audit | 表格 | group、outcome、features | 目录条目 | 统计目录 |
| `spillover_interference_audit_text` | 溢出与干扰审计 | Spillover / Interference Audit | 文字解读 | group、outcome、features | 目录条目 | 统计目录 |
| `unobserved_confounding_sensitivity_data` | 未观测混杂敏感性分析 | Unobserved Confounding Sensitivity | 结构化数据 | target、features | 目录条目 | 统计目录 |
| `unobserved_confounding_sensitivity_table` | 未观测混杂敏感性分析 | Unobserved Confounding Sensitivity | 表格 | target、features | 目录条目 | 统计目录 |
| `unobserved_confounding_sensitivity_text` | 未观测混杂敏感性分析 | Unobserved Confounding Sensitivity | 文字解读 | target、features | 目录条目 | 统计目录 |

### 分析方法（注册族：`均值检验`；39 张；可运行 30 张）

| 卡片 ID | 中文方法名称 | 原始英文概念 | 中文输出形式 | 字段角色 | 状态 | 来源 |
| --- | --- | --- | --- | --- | --- | --- |
| `ancova_data` | 协方差分析 | ANCOVA | 结构化数据 | 数值字段、分类字段、数值字段 | 可运行 | 统计目录 |
| `ancova_table` | 协方差分析 | ANCOVA | 表格 | 数值字段、分类字段、数值字段 | 可运行 | 统计目录 |
| `ancova_text` | 协方差分析 | ANCOVA | 文字解读 | 数值字段、分类字段、数值字段 | 可运行 | 统计目录 |
| `anova_data` | 单因素方差分析 | One-way ANOVA | 结构化数据 | 数值字段、分类字段 | 可运行 | 统计目录 |
| `anova_table` | 单因素方差分析 | One-way ANOVA | 表格 | 数值字段、分类字段 | 可运行 | 统计目录 |
| `anova_text` | 单因素方差分析 | One-way ANOVA | 文字解读 | 数值字段、分类字段 | 可运行 | 统计目录 |
| `equivalence_test_tost_data` | 双单侧等效性检验 | TOST Equivalence Test | 结构化数据 | 数值字段、binary group | 目录条目 | 统计目录 |
| `equivalence_test_tost_table` | 双单侧等效性检验 | TOST Equivalence Test | 表格 | 数值字段、binary group | 目录条目 | 统计目录 |
| `equivalence_test_tost_text` | 双单侧等效性检验 | TOST Equivalence Test | 文字解读 | 数值字段、binary group | 目录条目 | 统计目录 |
| `hotelling_t2_data` | 霍特林 T 平方检验 | Hotelling T^2 | 结构化数据 | multi numeric、binary group | 目录条目 | 统计目录 |
| `hotelling_t2_table` | 霍特林 T 平方检验 | Hotelling T^2 | 表格 | multi numeric、binary group | 目录条目 | 统计目录 |
| `hotelling_t2_text` | 霍特林 T 平方检验 | Hotelling T^2 | 文字解读 | multi numeric、binary group | 目录条目 | 统计目录 |
| `manova_data` | 多元方差分析 | MANOVA | 结构化数据 | multi numeric、分类字段 | 目录条目 | 统计目录 |
| `manova_table` | 多元方差分析 | MANOVA | 表格 | multi numeric、分类字段 | 目录条目 | 统计目录 |
| `manova_text` | 多元方差分析 | MANOVA | 文字解读 | multi numeric、分类字段 | 目录条目 | 统计目录 |
| `one_sample_ttest_data` | 单样本 T 检验 | One-sample T-test | 结构化数据 | 数值字段 | 可运行 | 统计目录 |
| `one_sample_ttest_table` | 单样本 T 检验 | One-sample T-test | 表格 | 数值字段 | 可运行 | 统计目录 |
| `one_sample_ttest_text` | 单样本 T 检验 | One-sample T-test | 文字解读 | 数值字段 | 可运行 | 统计目录 |
| `paired_ttest_data` | 配对样本 T 检验 | Paired T-test | 结构化数据 | 数值字段、paired | 可运行 | 统计目录 |
| `paired_ttest_table` | 配对样本 T 检验 | Paired T-test | 表格 | 数值字段、paired | 可运行 | 统计目录 |
| `paired_ttest_text` | 配对样本 T 检验 | Paired T-test | 文字解读 | 数值字段、paired | 可运行 | 统计目录 |
| `repeated_measures_anova_data` | 重复测量方差分析 | Repeated Measures ANOVA | 结构化数据 | 数值字段、within subject factor | 可运行 | 统计目录 |
| `repeated_measures_anova_table` | 重复测量方差分析 | Repeated Measures ANOVA | 表格 | 数值字段、within subject factor | 可运行 | 统计目录 |
| `repeated_measures_anova_text` | 重复测量方差分析 | Repeated Measures ANOVA | 文字解读 | 数值字段、within subject factor | 可运行 | 统计目录 |
| `ttest_data` | 韦尔奇双样本 T 检验 | Welch Two-sample T-test | 结构化数据 | 数值字段、binary group | 可运行 | 统计目录 |
| `ttest_table` | 韦尔奇双样本 T 检验 | Welch Two-sample T-test | 表格 | 数值字段、binary group | 可运行 | 统计目录 |
| `ttest_text` | 韦尔奇双样本 T 检验 | Welch Two-sample T-test | 文字解读 | 数值字段、binary group | 可运行 | 统计目录 |
| `tukey_hsd_data` | 图基显著性差异事后检验 | Tukey HSD | 结构化数据 | 数值字段、分类字段 | 可运行 | 统计目录 |
| `tukey_hsd_table` | 图基显著性差异事后检验 | Tukey HSD | 表格 | 数值字段、分类字段 | 可运行 | 统计目录 |
| `tukey_hsd_text` | 图基显著性差异事后检验 | Tukey HSD | 文字解读 | 数值字段、分类字段 | 可运行 | 统计目录 |
| `two_way_anova_data` | 双因素方差分析 | Two-way ANOVA | 结构化数据 | 数值字段、分类字段、分类字段 | 可运行 | 统计目录 |
| `two_way_anova_table` | 双因素方差分析 | Two-way ANOVA | 表格 | 数值字段、分类字段、分类字段 | 可运行 | 统计目录 |
| `two_way_anova_text` | 双因素方差分析 | Two-way ANOVA | 文字解读 | 数值字段、分类字段、分类字段 | 可运行 | 统计目录 |
| `welch_anova_data` | 韦尔奇方差分析 | Welch ANOVA | 结构化数据 | 数值字段、分类字段 | 可运行 | 统计目录 |
| `welch_anova_table` | 韦尔奇方差分析 | Welch ANOVA | 表格 | 数值字段、分类字段 | 可运行 | 统计目录 |
| `welch_anova_text` | 韦尔奇方差分析 | Welch ANOVA | 文字解读 | 数值字段、分类字段 | 可运行 | 统计目录 |
| `z_test_mean_data` | 均值 Z 检验 | Z-test for Mean | 结构化数据 | 数值字段 | 可运行 | 统计目录 |
| `z_test_mean_table` | 均值 Z 检验 | Z-test for Mean | 表格 | 数值字段 | 可运行 | 统计目录 |
| `z_test_mean_text` | 均值 Z 检验 | Z-test for Mean | 文字解读 | 数值字段 | 可运行 | 统计目录 |

### 分析方法（注册族：`多变量分析`；114 张；可运行 12 张）

| 卡片 ID | 中文方法名称 | 原始英文概念 | 中文输出形式 | 字段角色 | 状态 | 来源 |
| --- | --- | --- | --- | --- | --- | --- |
| `bertopic_clustering_chart` | BERTopic 主题聚类 | BERTopic Clustering | 图表 | 字段组 | 目录条目 | 统计目录 |
| `bertopic_clustering_data` | BERTopic 主题聚类 | BERTopic Clustering | 结构化数据 | 字段组 | 目录条目 | 统计目录 |
| `bertopic_clustering_image_spec` | BERTopic 主题聚类 | BERTopic Clustering | 图片规格 | 字段组 | 目录条目 | 统计目录 |
| `bertopic_clustering_report_section` | BERTopic 主题聚类 | BERTopic Clustering | 报告段落 | 字段组 | 目录条目 | 统计目录 |
| `bertopic_clustering_table` | BERTopic 主题聚类 | BERTopic Clustering | 表格 | 字段组 | 目录条目 | 统计目录 |
| `bertopic_clustering_text` | BERTopic 主题聚类 | BERTopic Clustering | 文字解读 | 字段组 | 目录条目 | 统计目录 |
| `bipartite_network_projection_data` | 二部网络投影 | Bipartite Network Projection | 结构化数据 | 对象级 | 目录条目 | 统计目录 |
| `bipartite_network_projection_table` | 二部网络投影 | Bipartite Network Projection | 表格 | 对象级 | 目录条目 | 统计目录 |
| `bipartite_network_projection_text` | 二部网络投影 | Bipartite Network Projection | 文字解读 | 对象级 | 目录条目 | 统计目录 |
| `cluster_stability_data` | 聚类稳定性分析 | Cluster Stability Analysis | 结构化数据 | multi numeric | 目录条目 | 统计目录 |
| `cluster_stability_table` | 聚类稳定性分析 | Cluster Stability Analysis | 表格 | multi numeric | 目录条目 | 统计目录 |
| `cluster_stability_text` | 聚类稳定性分析 | Cluster Stability Analysis | 文字解读 | multi numeric | 目录条目 | 统计目录 |
| `community_detection_louvain_data` | Louvain 社区发现 | Louvain Community Detection | 结构化数据 | 对象级 | 目录条目 | 统计目录 |
| `community_detection_louvain_table` | Louvain 社区发现 | Louvain Community Detection | 表格 | 对象级 | 目录条目 | 统计目录 |
| `community_detection_louvain_text` | Louvain 社区发现 | Louvain Community Detection | 文字解读 | 对象级 | 目录条目 | 统计目录 |
| `confirmatory_factor_analysis_data` | 验证性因子分析 | Confirmatory Factor Analysis | 结构化数据 | multi numeric | 目录条目 | 统计目录 |
| `confirmatory_factor_analysis_table` | 验证性因子分析 | Confirmatory Factor Analysis | 表格 | multi numeric | 目录条目 | 统计目录 |
| `confirmatory_factor_analysis_text` | 验证性因子分析 | Confirmatory Factor Analysis | 文字解读 | multi numeric | 目录条目 | 统计目录 |
| `correspondence_analysis_chart` | 对应分析 | Correspondence Analysis | 图表 | 分类字段、分类字段 | 目录条目 | 统计目录 |
| `correspondence_analysis_data` | 对应分析 | Correspondence Analysis | 结构化数据 | 分类字段、分类字段 | 目录条目 | 统计目录 |
| `correspondence_analysis_image_spec` | 对应分析 | Correspondence Analysis | 图片规格 | 分类字段、分类字段 | 目录条目 | 统计目录 |
| `correspondence_analysis_report_section` | 对应分析 | Correspondence Analysis | 报告段落 | 分类字段、分类字段 | 目录条目 | 统计目录 |
| `correspondence_analysis_table` | 对应分析 | Correspondence Analysis | 表格 | 分类字段、分类字段 | 目录条目 | 统计目录 |
| `correspondence_analysis_text` | 对应分析 | Correspondence Analysis | 文字解读 | 分类字段、分类字段 | 目录条目 | 统计目录 |
| `dbscan_chart` | 基于密度的空间聚类 | DBSCAN | 图表 | multi numeric | 目录条目 | 统计目录 |
| `dbscan_data` | 基于密度的空间聚类 | DBSCAN | 结构化数据 | multi numeric | 目录条目 | 统计目录 |
| `dbscan_image_spec` | 基于密度的空间聚类 | DBSCAN | 图片规格 | multi numeric | 目录条目 | 统计目录 |
| `dbscan_report_section` | 基于密度的空间聚类 | DBSCAN | 报告段落 | multi numeric | 目录条目 | 统计目录 |
| `dbscan_table` | 基于密度的空间聚类 | DBSCAN | 表格 | multi numeric | 目录条目 | 统计目录 |
| `dbscan_text` | 基于密度的空间聚类 | DBSCAN | 文字解读 | multi numeric | 目录条目 | 统计目录 |
| `discriminant_analysis_lda_data` | 线性判别分析 | Linear Discriminant Analysis | 结构化数据 | multi numeric、分类字段 | 目录条目 | 统计目录 |
| `discriminant_analysis_lda_table` | 线性判别分析 | Linear Discriminant Analysis | 表格 | multi numeric、分类字段 | 目录条目 | 统计目录 |
| `discriminant_analysis_lda_text` | 线性判别分析 | Linear Discriminant Analysis | 文字解读 | multi numeric、分类字段 | 目录条目 | 统计目录 |
| `discriminant_analysis_qda_data` | 二次判别分析 | Quadratic Discriminant Analysis | 结构化数据 | multi numeric、分类字段 | 目录条目 | 统计目录 |
| `discriminant_analysis_qda_table` | 二次判别分析 | Quadratic Discriminant Analysis | 表格 | multi numeric、分类字段 | 目录条目 | 统计目录 |
| `discriminant_analysis_qda_text` | 二次判别分析 | Quadratic Discriminant Analysis | 文字解读 | multi numeric、分类字段 | 目录条目 | 统计目录 |
| `elbow_method_data` | 肘部法则 | Elbow Method | 结构化数据 | multi numeric | 目录条目 | 统计目录 |
| `elbow_method_table` | 肘部法则 | Elbow Method | 表格 | multi numeric | 目录条目 | 统计目录 |
| `elbow_method_text` | 肘部法则 | Elbow Method | 文字解读 | multi numeric | 目录条目 | 统计目录 |
| `factor_analysis_chart` | 因子分析 | Factor Analysis | 图表 | multi numeric | 目录条目 | 统计目录 |
| `factor_analysis_data` | 因子分析 | Factor Analysis | 结构化数据 | multi numeric | 目录条目 | 统计目录 |
| `factor_analysis_image_spec` | 因子分析 | Factor Analysis | 图片规格 | multi numeric | 目录条目 | 统计目录 |
| `factor_analysis_report_section` | 因子分析 | Factor Analysis | 报告段落 | multi numeric | 目录条目 | 统计目录 |
| `factor_analysis_table` | 因子分析 | Factor Analysis | 表格 | multi numeric | 目录条目 | 统计目录 |
| `factor_analysis_text` | 因子分析 | Factor Analysis | 文字解读 | multi numeric | 目录条目 | 统计目录 |
| `gaussian_mixture_chart` | 高斯混合模型 | Gaussian Mixture Model | 图表 | multi numeric | 目录条目 | 统计目录 |
| `gaussian_mixture_data` | 高斯混合模型 | Gaussian Mixture Model | 结构化数据 | multi numeric | 目录条目 | 统计目录 |
| `gaussian_mixture_image_spec` | 高斯混合模型 | Gaussian Mixture Model | 图片规格 | multi numeric | 目录条目 | 统计目录 |
| `gaussian_mixture_report_section` | 高斯混合模型 | Gaussian Mixture Model | 报告段落 | multi numeric | 目录条目 | 统计目录 |
| `gaussian_mixture_table` | 高斯混合模型 | Gaussian Mixture Model | 表格 | multi numeric | 目录条目 | 统计目录 |
| `gaussian_mixture_text` | 高斯混合模型 | Gaussian Mixture Model | 文字解读 | multi numeric | 目录条目 | 统计目录 |
| `getis_ord_hotspot_data` | Getis-Ord 热点分析 | Getis-Ord Hotspot Analysis | 结构化数据 | 对象级、数值字段 | 目录条目 | 统计目录 |
| `getis_ord_hotspot_table` | Getis-Ord 热点分析 | Getis-Ord Hotspot Analysis | 表格 | 对象级、数值字段 | 目录条目 | 统计目录 |
| `getis_ord_hotspot_text` | Getis-Ord 热点分析 | Getis-Ord Hotspot Analysis | 文字解读 | 对象级、数值字段 | 目录条目 | 统计目录 |
| `hierarchical_clustering_chart` | 层次聚类 | Hierarchical Clustering | 图表 | multi numeric | 目录条目 | 统计目录 |
| `hierarchical_clustering_data` | 层次聚类 | Hierarchical Clustering | 结构化数据 | multi numeric | 目录条目 | 统计目录 |
| `hierarchical_clustering_image_spec` | 层次聚类 | Hierarchical Clustering | 图片规格 | multi numeric | 目录条目 | 统计目录 |
| `hierarchical_clustering_report_section` | 层次聚类 | Hierarchical Clustering | 报告段落 | multi numeric | 目录条目 | 统计目录 |
| `hierarchical_clustering_table` | 层次聚类 | Hierarchical Clustering | 表格 | multi numeric | 目录条目 | 统计目录 |
| `hierarchical_clustering_text` | 层次聚类 | Hierarchical Clustering | 文字解读 | multi numeric | 目录条目 | 统计目录 |
| `ica_data` | 独立成分分析 | Independent Component Analysis | 结构化数据 | multi numeric | 目录条目 | 统计目录 |
| `ica_table` | 独立成分分析 | Independent Component Analysis | 表格 | multi numeric | 目录条目 | 统计目录 |
| `ica_text` | 独立成分分析 | Independent Component Analysis | 文字解读 | multi numeric | 目录条目 | 统计目录 |
| `kmeans_chart` | K 均值聚类 | KMeans Clustering | 图表 | multi numeric | 可运行 | 统计目录 |
| `kmeans_data` | K 均值聚类 | KMeans Clustering | 结构化数据 | multi numeric | 可运行 | 统计目录 |
| `kmeans_image_spec` | K 均值聚类 | KMeans Clustering | 图片规格 | multi numeric | 可运行 | 统计目录 |
| `kmeans_report_section` | K 均值聚类 | KMeans Clustering | 报告段落 | multi numeric | 可运行 | 统计目录 |
| `kmeans_table` | K 均值聚类 | KMeans Clustering | 表格 | multi numeric | 可运行 | 统计目录 |
| `kmeans_text` | K 均值聚类 | KMeans Clustering | 文字解读 | multi numeric | 可运行 | 统计目录 |
| `latent_class_analysis_data` | 潜在类别分析 | Latent Class Analysis | 结构化数据 | multi categorical | 目录条目 | 统计目录 |
| `latent_class_analysis_table` | 潜在类别分析 | Latent Class Analysis | 表格 | multi categorical | 目录条目 | 统计目录 |
| `latent_class_analysis_text` | 潜在类别分析 | Latent Class Analysis | 文字解读 | multi categorical | 目录条目 | 统计目录 |
| `multivariate_control_chart_chart` | 多变量控制图 | Multivariate Control Chart | 图表 | multi numeric | 目录条目 | 统计目录 |
| `multivariate_control_chart_data` | 多变量控制图 | Multivariate Control Chart | 结构化数据 | multi numeric | 目录条目 | 统计目录 |
| `multivariate_control_chart_image_spec` | 多变量控制图 | Multivariate Control Chart | 图片规格 | multi numeric | 目录条目 | 统计目录 |
| `multivariate_control_chart_report_section` | 多变量控制图 | Multivariate Control Chart | 报告段落 | multi numeric | 目录条目 | 统计目录 |
| `multivariate_control_chart_table` | 多变量控制图 | Multivariate Control Chart | 表格 | multi numeric | 目录条目 | 统计目录 |
| `multivariate_control_chart_text` | 多变量控制图 | Multivariate Control Chart | 文字解读 | multi numeric | 目录条目 | 统计目录 |
| `named_entity_extraction_profile_data` | 命名实体提取画像 | Named Entity Extraction Profile | 结构化数据 | 字段组 | 目录条目 | 统计目录 |
| `named_entity_extraction_profile_table` | 命名实体提取画像 | Named Entity Extraction Profile | 表格 | 字段组 | 目录条目 | 统计目录 |
| `named_entity_extraction_profile_text` | 命名实体提取画像 | Named Entity Extraction Profile | 文字解读 | 字段组 | 目录条目 | 统计目录 |
| `network_betweenness_centrality_data` | 网络介数中心性 | Network Betweenness Centrality | 结构化数据 | 对象级 | 目录条目 | 统计目录 |
| `network_betweenness_centrality_table` | 网络介数中心性 | Network Betweenness Centrality | 表格 | 对象级 | 目录条目 | 统计目录 |
| `network_betweenness_centrality_text` | 网络介数中心性 | Network Betweenness Centrality | 文字解读 | 对象级 | 目录条目 | 统计目录 |
| `network_degree_centrality_data` | 网络度中心性 | Network Degree Centrality | 结构化数据 | 对象级 | 目录条目 | 统计目录 |
| `network_degree_centrality_table` | 网络度中心性 | Network Degree Centrality | 表格 | 对象级 | 目录条目 | 统计目录 |
| `network_degree_centrality_text` | 网络度中心性 | Network Degree Centrality | 文字解读 | 对象级 | 目录条目 | 统计目录 |
| `network_pagerank_data` | 网络 PageRank 分析 | Network PageRank | 结构化数据 | 对象级 | 目录条目 | 统计目录 |
| `network_pagerank_table` | 网络 PageRank 分析 | Network PageRank | 表格 | 对象级 | 目录条目 | 统计目录 |
| `network_pagerank_text` | 网络 PageRank 分析 | Network PageRank | 文字解读 | 对象级 | 目录条目 | 统计目录 |
| `pca_chart` | 主成分分析 | Principal Component Analysis | 图表 | multi numeric | 可运行 | 统计目录 |
| `pca_data` | 主成分分析 | Principal Component Analysis | 结构化数据 | multi numeric | 可运行 | 统计目录 |
| `pca_image_spec` | 主成分分析 | Principal Component Analysis | 图片规格 | multi numeric | 可运行 | 统计目录 |
| `pca_report_section` | 主成分分析 | Principal Component Analysis | 报告段落 | multi numeric | 可运行 | 统计目录 |
| `pca_table` | 主成分分析 | Principal Component Analysis | 表格 | multi numeric | 可运行 | 统计目录 |
| `pca_text` | 主成分分析 | Principal Component Analysis | 文字解读 | multi numeric | 可运行 | 统计目录 |
| `silhouette_analysis_data` | 轮廓系数分析 | Silhouette Analysis | 结构化数据 | multi numeric | 目录条目 | 统计目录 |
| `silhouette_analysis_table` | 轮廓系数分析 | Silhouette Analysis | 表格 | multi numeric | 目录条目 | 统计目录 |
| `silhouette_analysis_text` | 轮廓系数分析 | Silhouette Analysis | 文字解读 | multi numeric | 目录条目 | 统计目录 |
| `text_token_frequency_data` | 文本词元频率分析 | Text Token Frequency | 结构化数据 | 字段组 | 目录条目 | 统计目录 |
| `text_token_frequency_table` | 文本词元频率分析 | Text Token Frequency | 表格 | 字段组 | 目录条目 | 统计目录 |
| `text_token_frequency_text` | 文本词元频率分析 | Text Token Frequency | 文字解读 | 字段组 | 目录条目 | 统计目录 |
| `tfidf_feature_profile_data` | TF-IDF 特征画像 | TF-IDF Feature Profile | 结构化数据 | 字段组 | 目录条目 | 统计目录 |
| `tfidf_feature_profile_table` | TF-IDF 特征画像 | TF-IDF Feature Profile | 表格 | 字段组 | 目录条目 | 统计目录 |
| `tfidf_feature_profile_text` | TF-IDF 特征画像 | TF-IDF Feature Profile | 文字解读 | 字段组 | 目录条目 | 统计目录 |
| `topic_model_lda_data` | LDA 主题模型 | LDA Topic Model | 结构化数据 | 字段组 | 目录条目 | 统计目录 |
| `topic_model_lda_table` | LDA 主题模型 | LDA Topic Model | 表格 | 字段组 | 目录条目 | 统计目录 |
| `topic_model_lda_text` | LDA 主题模型 | LDA Topic Model | 文字解读 | 字段组 | 目录条目 | 统计目录 |
| `tsne_projection_data` | t-SNE 降维投影 | t-SNE Projection | 结构化数据 | multi numeric | 目录条目 | 统计目录 |
| `tsne_projection_table` | t-SNE 降维投影 | t-SNE Projection | 表格 | multi numeric | 目录条目 | 统计目录 |
| `tsne_projection_text` | t-SNE 降维投影 | t-SNE Projection | 文字解读 | multi numeric | 目录条目 | 统计目录 |
| `umap_projection_data` | UMAP 降维投影 | UMAP Projection | 结构化数据 | multi numeric | 目录条目 | 统计目录 |
| `umap_projection_table` | UMAP 降维投影 | UMAP Projection | 表格 | multi numeric | 目录条目 | 统计目录 |
| `umap_projection_text` | UMAP 降维投影 | UMAP Projection | 文字解读 | multi numeric | 目录条目 | 统计目录 |

### 分析方法（注册族：`实验分析`；78 张；可运行 3 张）

| 卡片 ID | 中文方法名称 | 原始英文概念 | 中文输出形式 | 字段角色 | 状态 | 来源 |
| --- | --- | --- | --- | --- | --- | --- |
| `ab_test_data` | A/B 实验检验 | A/B Test | 结构化数据 | group、numeric or binary | 可运行 | 统计目录 |
| `ab_test_table` | A/B 实验检验 | A/B Test | 表格 | group、numeric or binary | 可运行 | 统计目录 |
| `ab_test_text` | A/B 实验检验 | A/B Test | 文字解读 | group、numeric or binary | 可运行 | 统计目录 |
| `attrition_analysis_data` | 样本流失分析 | Attrition Analysis | 结构化数据 | group、numeric or binary | 目录条目 | 统计目录 |
| `attrition_analysis_table` | 样本流失分析 | Attrition Analysis | 表格 | group、numeric or binary | 目录条目 | 统计目录 |
| `attrition_analysis_text` | 样本流失分析 | Attrition Analysis | 文字解读 | group、numeric or binary | 目录条目 | 统计目录 |
| `bayesian_ab_test_data` | 贝叶斯 A/B 实验 | Bayesian A/B Test | 结构化数据 | group、numeric or binary | 目录条目 | 统计目录 |
| `bayesian_ab_test_table` | 贝叶斯 A/B 实验 | Bayesian A/B Test | 表格 | group、numeric or binary | 目录条目 | 统计目录 |
| `bayesian_ab_test_text` | 贝叶斯 A/B 实验 | Bayesian A/B Test | 文字解读 | group、numeric or binary | 目录条目 | 统计目录 |
| `bayesian_bandit_policy_data` | 贝叶斯老虎机策略 | Bayesian Bandit Policy | 结构化数据 | group、numeric or binary | 目录条目 | 统计目录 |
| `bayesian_bandit_policy_table` | 贝叶斯老虎机策略 | Bayesian Bandit Policy | 表格 | group、numeric or binary | 目录条目 | 统计目录 |
| `bayesian_bandit_policy_text` | 贝叶斯老虎机策略 | Bayesian Bandit Policy | 文字解读 | group、numeric or binary | 目录条目 | 统计目录 |
| `bucketed_ratio_metric_data` | 分桶比率指标 | Bucketed Ratio Metric | 结构化数据 | group、numeric or binary | 目录条目 | 统计目录 |
| `bucketed_ratio_metric_table` | 分桶比率指标 | Bucketed Ratio Metric | 表格 | group、numeric or binary | 目录条目 | 统计目录 |
| `bucketed_ratio_metric_text` | 分桶比率指标 | Bucketed Ratio Metric | 文字解读 | group、numeric or binary | 目录条目 | 统计目录 |
| `carryover_effect_check_data` | 残留效应检查 | Carryover Effect Check | 结构化数据 | time、group、numeric or binary | 目录条目 | 统计目录 |
| `carryover_effect_check_table` | 残留效应检查 | Carryover Effect Check | 表格 | time、group、numeric or binary | 目录条目 | 统计目录 |
| `carryover_effect_check_text` | 残留效应检查 | Carryover Effect Check | 文字解读 | time、group、numeric or binary | 目录条目 | 统计目录 |
| `cuped_adjustment_data` | CUPED 协变量调整 | CUPED Adjustment | 结构化数据 | group、outcome、features | 目录条目 | 统计目录 |
| `cuped_adjustment_table` | CUPED 协变量调整 | CUPED Adjustment | 表格 | group、outcome、features | 目录条目 | 统计目录 |
| `cuped_adjustment_text` | CUPED 协变量调整 | CUPED Adjustment | 文字解读 | group、outcome、features | 目录条目 | 统计目录 |
| `experiment_guardrail_metrics_data` | 实验护栏指标 | Experiment Guardrail Metrics | 结构化数据 | group、numeric or binary | 目录条目 | 统计目录 |
| `experiment_guardrail_metrics_table` | 实验护栏指标 | Experiment Guardrail Metrics | 表格 | group、numeric or binary | 目录条目 | 统计目录 |
| `experiment_guardrail_metrics_text` | 实验护栏指标 | Experiment Guardrail Metrics | 文字解读 | group、numeric or binary | 目录条目 | 统计目录 |
| `factorial_experiment_data` | 析因实验 | Factorial Experiment | 结构化数据 | group、outcome、features | 目录条目 | 统计目录 |
| `factorial_experiment_table` | 析因实验 | Factorial Experiment | 表格 | group、outcome、features | 目录条目 | 统计目录 |
| `factorial_experiment_text` | 析因实验 | Factorial Experiment | 文字解读 | group、outcome、features | 目录条目 | 统计目录 |
| `geo_experiment_design_data` | 地理实验设计 | Geo Experiment Design | 结构化数据 | 对象级、分组 | 目录条目 | 统计目录 |
| `geo_experiment_design_table` | 地理实验设计 | Geo Experiment Design | 表格 | 对象级、分组 | 目录条目 | 统计目录 |
| `geo_experiment_design_text` | 地理实验设计 | Geo Experiment Design | 文字解读 | 对象级、分组 | 目录条目 | 统计目录 |
| `incrementality_holdout_data` | 增量效果留出组评估 | Incrementality Holdout | 结构化数据 | group、numeric or binary | 目录条目 | 统计目录 |
| `incrementality_holdout_table` | 增量效果留出组评估 | Incrementality Holdout | 表格 | group、numeric or binary | 目录条目 | 统计目录 |
| `incrementality_holdout_text` | 增量效果留出组评估 | Incrementality Holdout | 文字解读 | group、numeric or binary | 目录条目 | 统计目录 |
| `metric_sensitivity_analysis_data` | 指标敏感性分析 | Metric Sensitivity Analysis | 结构化数据 | group、numeric or binary | 目录条目 | 统计目录 |
| `metric_sensitivity_analysis_table` | 指标敏感性分析 | Metric Sensitivity Analysis | 表格 | group、numeric or binary | 目录条目 | 统计目录 |
| `metric_sensitivity_analysis_text` | 指标敏感性分析 | Metric Sensitivity Analysis | 文字解读 | group、numeric or binary | 目录条目 | 统计目录 |
| `minimum_detectable_effect_data` | 最小可检测效应 | Minimum Detectable Effect | 结构化数据 | group、numeric or binary | 目录条目 | 统计目录 |
| `minimum_detectable_effect_table` | 最小可检测效应 | Minimum Detectable Effect | 表格 | group、numeric or binary | 目录条目 | 统计目录 |
| `minimum_detectable_effect_text` | 最小可检测效应 | Minimum Detectable Effect | 文字解读 | group、numeric or binary | 目录条目 | 统计目录 |
| `multi_arm_bandit_data` | 多臂老虎机策略 | Multi-arm Bandit | 结构化数据 | group、numeric or binary | 目录条目 | 统计目录 |
| `multi_arm_bandit_table` | 多臂老虎机策略 | Multi-arm Bandit | 表格 | group、numeric or binary | 目录条目 | 统计目录 |
| `multi_arm_bandit_text` | 多臂老虎机策略 | Multi-arm Bandit | 文字解读 | group、numeric or binary | 目录条目 | 统计目录 |
| `number_needed_to_treat_data` | 需治疗人数 | Number Needed to Treat | 结构化数据 | group、binary | 目录条目 | 统计目录 |
| `number_needed_to_treat_table` | 需治疗人数 | Number Needed to Treat | 表格 | group、binary | 目录条目 | 统计目录 |
| `number_needed_to_treat_text` | 需治疗人数 | Number Needed to Treat | 文字解读 | group、binary | 目录条目 | 统计目录 |
| `peeking_risk_audit_data` | 实验提前窥视风险审计 | Peeking Risk Audit | 结构化数据 | group、numeric or binary | 目录条目 | 统计目录 |
| `peeking_risk_audit_table` | 实验提前窥视风险审计 | Peeking Risk Audit | 表格 | group、numeric or binary | 目录条目 | 统计目录 |
| `peeking_risk_audit_text` | 实验提前窥视风险审计 | Peeking Risk Audit | 文字解读 | group、numeric or binary | 目录条目 | 统计目录 |
| `power_curve_analysis_chart` | 统计功效曲线分析 | Power Curve Analysis | 图表 | effect size | 目录条目 | 统计目录 |
| `power_curve_analysis_data` | 统计功效曲线分析 | Power Curve Analysis | 结构化数据 | effect size | 目录条目 | 统计目录 |
| `power_curve_analysis_image_spec` | 统计功效曲线分析 | Power Curve Analysis | 图片规格 | effect size | 目录条目 | 统计目录 |
| `power_curve_analysis_report_section` | 统计功效曲线分析 | Power Curve Analysis | 报告段落 | effect size | 目录条目 | 统计目录 |
| `power_curve_analysis_table` | 统计功效曲线分析 | Power Curve Analysis | 表格 | effect size | 目录条目 | 统计目录 |
| `power_curve_analysis_text` | 统计功效曲线分析 | Power Curve Analysis | 文字解读 | effect size | 目录条目 | 统计目录 |
| `sample_ratio_mismatch_data` | 样本比例失配检验 | Sample Ratio Mismatch | 结构化数据 | group、numeric or binary | 目录条目 | 统计目录 |
| `sample_ratio_mismatch_table` | 样本比例失配检验 | Sample Ratio Mismatch | 表格 | group、numeric or binary | 目录条目 | 统计目录 |
| `sample_ratio_mismatch_text` | 样本比例失配检验 | Sample Ratio Mismatch | 文字解读 | group、numeric or binary | 目录条目 | 统计目录 |
| `sample_size_power_data` | 样本量与统计功效分析 | Sample Size / Power Analysis | 结构化数据 | effect size | 目录条目 | 统计目录 |
| `sample_size_power_table` | 样本量与统计功效分析 | Sample Size / Power Analysis | 表格 | effect size | 目录条目 | 统计目录 |
| `sample_size_power_text` | 样本量与统计功效分析 | Sample Size / Power Analysis | 文字解读 | effect size | 目录条目 | 统计目录 |
| `sequential_bayesian_monitoring_data` | 序贯贝叶斯监测 | Sequential Bayesian Monitoring | 结构化数据 | group、numeric or binary | 目录条目 | 统计目录 |
| `sequential_bayesian_monitoring_table` | 序贯贝叶斯监测 | Sequential Bayesian Monitoring | 表格 | group、numeric or binary | 目录条目 | 统计目录 |
| `sequential_bayesian_monitoring_text` | 序贯贝叶斯监测 | Sequential Bayesian Monitoring | 文字解读 | group、numeric or binary | 目录条目 | 统计目录 |
| `sequential_test_data` | 序贯检验 | Sequential Test | 结构化数据 | group、numeric or binary | 目录条目 | 统计目录 |
| `sequential_test_table` | 序贯检验 | Sequential Test | 表格 | group、numeric or binary | 目录条目 | 统计目录 |
| `sequential_test_text` | 序贯检验 | Sequential Test | 文字解读 | group、numeric or binary | 目录条目 | 统计目录 |
| `stratified_randomization_data` | 分层随机化 | Stratified Randomization | 结构化数据 | group、features | 目录条目 | 统计目录 |
| `stratified_randomization_table` | 分层随机化 | Stratified Randomization | 表格 | group、features | 目录条目 | 统计目录 |
| `stratified_randomization_text` | 分层随机化 | Stratified Randomization | 文字解读 | group、features | 目录条目 | 统计目录 |
| `switchback_experiment_design_data` | 交替实验设计 | Switchback Experiment Design | 结构化数据 | time、group、numeric or binary | 目录条目 | 统计目录 |
| `switchback_experiment_design_table` | 交替实验设计 | Switchback Experiment Design | 表格 | time、group、numeric or binary | 目录条目 | 统计目录 |
| `switchback_experiment_design_text` | 交替实验设计 | Switchback Experiment Design | 文字解读 | time、group、numeric or binary | 目录条目 | 统计目录 |
| `uplift_evaluation_qini_data` | Qini 增量评估 | Qini Uplift Evaluation | 结构化数据 | group、outcome、features | 目录条目 | 统计目录 |
| `uplift_evaluation_qini_table` | Qini 增量评估 | Qini Uplift Evaluation | 表格 | group、outcome、features | 目录条目 | 统计目录 |
| `uplift_evaluation_qini_text` | Qini 增量评估 | Qini Uplift Evaluation | 文字解读 | group、outcome、features | 目录条目 | 统计目录 |
| `uplift_modeling_data` | 增量效应建模 | Uplift Modeling | 结构化数据 | group、outcome、features | 目录条目 | 统计目录 |
| `uplift_modeling_table` | 增量效应建模 | Uplift Modeling | 表格 | group、outcome、features | 目录条目 | 统计目录 |
| `uplift_modeling_text` | 增量效应建模 | Uplift Modeling | 文字解读 | group、outcome、features | 目录条目 | 统计目录 |

### 分析方法（注册族：`差异比较`；14 张；可运行 0 张）

| 卡片 ID | 中文方法名称 | 原始英文概念 | 中文输出形式 | 字段角色 | 状态 | 来源 |
| --- | --- | --- | --- | --- | --- | --- |
| `cohens_d_effect_size_data` | 科恩 d 效应量 | Cohen's d Effect Size | 结构化数据 | 数值字段、binary group | 目录条目 | 统计目录 |
| `cohens_d_effect_size_table` | 科恩 d 效应量 | Cohen's d Effect Size | 表格 | 数值字段、binary group | 目录条目 | 统计目录 |
| `cohens_d_effect_size_text` | 科恩 d 效应量 | Cohen's d Effect Size | 文字解读 | 数值字段、binary group | 目录条目 | 统计目录 |
| `comparison_mean` | 差异比较・均值 | 均值 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `comparison_median` | 差异比较・中位数 | 中位数 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `comparison_post_hoc` | 差异比较・分析方法 | 事后检验 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `comparison_proportion` | 差异比较・占比 | 占比 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `comparison_variance` | 差异比较・方差 | 方差 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `glass_delta_effect_size_data` | 格拉斯 Delta 效应量 | Glass Delta Effect Size | 结构化数据 | 数值字段、binary group | 目录条目 | 统计目录 |
| `glass_delta_effect_size_table` | 格拉斯 Delta 效应量 | Glass Delta Effect Size | 表格 | 数值字段、binary group | 目录条目 | 统计目录 |
| `glass_delta_effect_size_text` | 格拉斯 Delta 效应量 | Glass Delta Effect Size | 文字解读 | 数值字段、binary group | 目录条目 | 统计目录 |
| `hedges_g_effect_size_data` | 赫奇斯 g 效应量 | Hedges g Effect Size | 结构化数据 | 数值字段、binary group | 目录条目 | 统计目录 |
| `hedges_g_effect_size_table` | 赫奇斯 g 效应量 | Hedges g Effect Size | 表格 | 数值字段、binary group | 目录条目 | 统计目录 |
| `hedges_g_effect_size_text` | 赫奇斯 g 效应量 | Hedges g Effect Size | 文字解读 | 数值字段、binary group | 目录条目 | 统计目录 |

### 分析方法（注册族：`广义线性模型`；108 张；可运行 24 张）

| 卡片 ID | 中文方法名称 | 原始英文概念 | 中文输出形式 | 字段角色 | 状态 | 来源 |
| --- | --- | --- | --- | --- | --- | --- |
| `aic_bic_model_selection_data` | AIC/BIC 模型选择 | AIC / BIC Model Selection | 结构化数据 | target、features | 目录条目 | 统计目录 |
| `aic_bic_model_selection_table` | AIC/BIC 模型选择 | AIC / BIC Model Selection | 表格 | target、features | 目录条目 | 统计目录 |
| `aic_bic_model_selection_text` | AIC/BIC 模型选择 | AIC / BIC Model Selection | 文字解读 | target、features | 目录条目 | 统计目录 |
| `beta_regression_data` | 贝塔回归 | Beta Regression | 结构化数据 | proportion、multi numeric | 目录条目 | 统计目录 |
| `beta_regression_table` | 贝塔回归 | Beta Regression | 表格 | proportion、multi numeric | 目录条目 | 统计目录 |
| `beta_regression_text` | 贝塔回归 | Beta Regression | 文字解读 | proportion、multi numeric | 目录条目 | 统计目录 |
| `cluster_robust_standard_errors_data` | 聚类稳健标准误 | Cluster-robust Standard Errors | 结构化数据 | target、features、分组 | 目录条目 | 统计目录 |
| `cluster_robust_standard_errors_table` | 聚类稳健标准误 | Cluster-robust Standard Errors | 表格 | target、features、分组 | 目录条目 | 统计目录 |
| `cluster_robust_standard_errors_text` | 聚类稳健标准误 | Cluster-robust Standard Errors | 文字解读 | target、features、分组 | 目录条目 | 统计目录 |
| `cooks_distance_data` | 库克距离 | Cook's Distance | 结构化数据 | target、features | 目录条目 | 统计目录 |
| `cooks_distance_table` | 库克距离 | Cook's Distance | 表格 | target、features | 目录条目 | 统计目录 |
| `cooks_distance_text` | 库克距离 | Cook's Distance | 文字解读 | target、features | 目录条目 | 统计目录 |
| `cross_validated_regression_data` | 交叉验证回归 | Cross-validated Regression | 结构化数据 | target、features | 目录条目 | 统计目录 |
| `cross_validated_regression_table` | 交叉验证回归 | Cross-validated Regression | 表格 | target、features | 目录条目 | 统计目录 |
| `cross_validated_regression_text` | 交叉验证回归 | Cross-validated Regression | 文字解读 | target、features | 目录条目 | 统计目录 |
| `elastic_net_data` | 弹性网络回归 | Elastic Net | 结构化数据 | 数值字段、multi numeric | 可运行 | 统计目录 |
| `elastic_net_table` | 弹性网络回归 | Elastic Net | 表格 | 数值字段、multi numeric | 可运行 | 统计目录 |
| `elastic_net_text` | 弹性网络回归 | Elastic Net | 文字解读 | 数值字段、multi numeric | 可运行 | 统计目录 |
| `gamma_glm_data` | 伽马广义线性模型 | Gamma GLM | 结构化数据 | positive numeric、multi numeric | 目录条目 | 统计目录 |
| `gamma_glm_table` | 伽马广义线性模型 | Gamma GLM | 表格 | positive numeric、multi numeric | 目录条目 | 统计目录 |
| `gamma_glm_text` | 伽马广义线性模型 | Gamma GLM | 文字解读 | positive numeric、multi numeric | 目录条目 | 统计目录 |
| `generalized_additive_model_data` | 广义加性模型 | Generalized Additive Model | 结构化数据 | target、features | 目录条目 | 统计目录 |
| `generalized_additive_model_table` | 广义加性模型 | Generalized Additive Model | 表格 | target、features | 目录条目 | 统计目录 |
| `generalized_additive_model_text` | 广义加性模型 | Generalized Additive Model | 文字解读 | target、features | 目录条目 | 统计目录 |
| `geographically_weighted_regression_data` | 地理加权回归 | Geographically Weighted Regression | 结构化数据 | target、features、对象级 | 目录条目 | 统计目录 |
| `geographically_weighted_regression_table` | 地理加权回归 | Geographically Weighted Regression | 表格 | target、features、对象级 | 目录条目 | 统计目录 |
| `geographically_weighted_regression_text` | 地理加权回归 | Geographically Weighted Regression | 文字解读 | target、features、对象级 | 目录条目 | 统计目录 |
| `glm_binomial_data` | 二项广义线性模型 | Binomial GLM | 结构化数据 | binary、multi numeric | 目录条目 | 统计目录 |
| `glm_binomial_table` | 二项广义线性模型 | Binomial GLM | 表格 | binary、multi numeric | 目录条目 | 统计目录 |
| `glm_binomial_text` | 二项广义线性模型 | Binomial GLM | 文字解读 | binary、multi numeric | 目录条目 | 统计目录 |
| `heteroskedasticity_robust_se_data` | 异方差稳健标准误 | Heteroskedasticity-robust Standard Errors | 结构化数据 | target、features | 目录条目 | 统计目录 |
| `heteroskedasticity_robust_se_table` | 异方差稳健标准误 | Heteroskedasticity-robust Standard Errors | 表格 | target、features | 目录条目 | 统计目录 |
| `heteroskedasticity_robust_se_text` | 异方差稳健标准误 | Heteroskedasticity-robust Standard Errors | 文字解读 | target、features | 目录条目 | 统计目录 |
| `influence_diagnostics_data` | 影响点诊断 | Influence Diagnostics | 结构化数据 | target、features | 目录条目 | 统计目录 |
| `influence_diagnostics_table` | 影响点诊断 | Influence Diagnostics | 表格 | target、features | 目录条目 | 统计目录 |
| `influence_diagnostics_text` | 影响点诊断 | Influence Diagnostics | 文字解读 | target、features | 目录条目 | 统计目录 |
| `interaction_feature_screen_data` | 交互特征筛选 | Interaction Feature Screen | 结构化数据 | target、features | 目录条目 | 统计目录 |
| `interaction_feature_screen_table` | 交互特征筛选 | Interaction Feature Screen | 表格 | target、features | 目录条目 | 统计目录 |
| `interaction_feature_screen_text` | 交互特征筛选 | Interaction Feature Screen | 文字解读 | target、features | 目录条目 | 统计目录 |
| `lasso_regression_data` | 套索回归 | Lasso Regression | 结构化数据 | 数值字段、multi numeric | 可运行 | 统计目录 |
| `lasso_regression_table` | 套索回归 | Lasso Regression | 表格 | 数值字段、multi numeric | 可运行 | 统计目录 |
| `lasso_regression_text` | 套索回归 | Lasso Regression | 文字解读 | 数值字段、multi numeric | 可运行 | 统计目录 |
| `logit_data` | 逻辑回归 | Logistic Regression | 结构化数据 | binary、multi numeric | 可运行 | 统计目录 |
| `logit_table` | 逻辑回归 | Logistic Regression | 表格 | binary、multi numeric | 可运行 | 统计目录 |
| `logit_text` | 逻辑回归 | Logistic Regression | 文字解读 | binary、multi numeric | 可运行 | 统计目录 |
| `model_specification_curve_chart` | 模型设定曲线分析 | Specification Curve Analysis | 图表 | target、features | 目录条目 | 统计目录 |
| `model_specification_curve_data` | 模型设定曲线分析 | Specification Curve Analysis | 结构化数据 | target、features | 目录条目 | 统计目录 |
| `model_specification_curve_image_spec` | 模型设定曲线分析 | Specification Curve Analysis | 图片规格 | target、features | 目录条目 | 统计目录 |
| `model_specification_curve_report_section` | 模型设定曲线分析 | Specification Curve Analysis | 报告段落 | target、features | 目录条目 | 统计目录 |
| `model_specification_curve_table` | 模型设定曲线分析 | Specification Curve Analysis | 表格 | target、features | 目录条目 | 统计目录 |
| `model_specification_curve_text` | 模型设定曲线分析 | Specification Curve Analysis | 文字解读 | target、features | 目录条目 | 统计目录 |
| `multinomial_logit_data` | 多项逻辑回归 | Multinomial Logit | 结构化数据 | multi class、multi numeric | 目录条目 | 统计目录 |
| `multinomial_logit_table` | 多项逻辑回归 | Multinomial Logit | 表格 | multi class、multi numeric | 目录条目 | 统计目录 |
| `multinomial_logit_text` | 多项逻辑回归 | Multinomial Logit | 文字解读 | multi class、multi numeric | 目录条目 | 统计目录 |
| `negative_binomial_data` | 负二项回归 | Negative Binomial Regression | 结构化数据 | count、multi numeric | 目录条目 | 统计目录 |
| `negative_binomial_table` | 负二项回归 | Negative Binomial Regression | 表格 | count、multi numeric | 目录条目 | 统计目录 |
| `negative_binomial_text` | 负二项回归 | Negative Binomial Regression | 文字解读 | count、multi numeric | 目录条目 | 统计目录 |
| `ols_data` | 普通最小二乘回归 | OLS Regression | 结构化数据 | 数值字段、multi numeric | 可运行 | 统计目录 |
| `ols_table` | 普通最小二乘回归 | OLS Regression | 表格 | 数值字段、multi numeric | 可运行 | 统计目录 |
| `ols_text` | 普通最小二乘回归 | OLS Regression | 文字解读 | 数值字段、multi numeric | 可运行 | 统计目录 |
| `ordinal_logit_data` | 有序逻辑回归 | Ordinal Logistic Regression | 结构化数据 | ordered category、multi numeric | 目录条目 | 统计目录 |
| `ordinal_logit_table` | 有序逻辑回归 | Ordinal Logistic Regression | 表格 | ordered category、multi numeric | 目录条目 | 统计目录 |
| `ordinal_logit_text` | 有序逻辑回归 | Ordinal Logistic Regression | 文字解读 | ordered category、multi numeric | 目录条目 | 统计目录 |
| `piecewise_regression_data` | 分段回归 | Piecewise Regression | 结构化数据 | target、features | 目录条目 | 统计目录 |
| `piecewise_regression_table` | 分段回归 | Piecewise Regression | 表格 | target、features | 目录条目 | 统计目录 |
| `piecewise_regression_text` | 分段回归 | Piecewise Regression | 文字解读 | target、features | 目录条目 | 统计目录 |
| `poisson_glm_data` | 泊松广义线性模型 | Poisson GLM | 结构化数据 | count、multi numeric | 可运行 | 统计目录 |
| `poisson_glm_table` | 泊松广义线性模型 | Poisson GLM | 表格 | count、multi numeric | 可运行 | 统计目录 |
| `poisson_glm_text` | 泊松广义线性模型 | Poisson GLM | 文字解读 | count、multi numeric | 可运行 | 统计目录 |
| `prediction_interval_data` | 预测区间 | Prediction Interval | 结构化数据 | target、features | 目录条目 | 统计目录 |
| `prediction_interval_table` | 预测区间 | Prediction Interval | 表格 | target、features | 目录条目 | 统计目录 |
| `prediction_interval_text` | 预测区间 | Prediction Interval | 文字解读 | target、features | 目录条目 | 统计目录 |
| `probit_regression_data` | 概率单位回归 | Probit Regression | 结构化数据 | binary、multi numeric | 目录条目 | 统计目录 |
| `probit_regression_table` | 概率单位回归 | Probit Regression | 表格 | binary、multi numeric | 目录条目 | 统计目录 |
| `probit_regression_text` | 概率单位回归 | Probit Regression | 文字解读 | binary、multi numeric | 目录条目 | 统计目录 |
| `quantile_regression_data` | 分位数回归 | Quantile Regression | 结构化数据 | 数值字段、multi numeric | 可运行 | 统计目录 |
| `quantile_regression_table` | 分位数回归 | Quantile Regression | 表格 | 数值字段、multi numeric | 可运行 | 统计目录 |
| `quantile_regression_text` | 分位数回归 | Quantile Regression | 文字解读 | 数值字段、multi numeric | 可运行 | 统计目录 |
| `residual_diagnostic_panel_data` | 残差诊断面板 | Residual Diagnostic Panel | 结构化数据 | target、features | 目录条目 | 统计目录 |
| `residual_diagnostic_panel_table` | 残差诊断面板 | Residual Diagnostic Panel | 表格 | target、features | 目录条目 | 统计目录 |
| `residual_diagnostic_panel_text` | 残差诊断面板 | Residual Diagnostic Panel | 文字解读 | target、features | 目录条目 | 统计目录 |
| `ridge_regression_data` | 岭回归 | Ridge Regression | 结构化数据 | 数值字段、multi numeric | 可运行 | 统计目录 |
| `ridge_regression_table` | 岭回归 | Ridge Regression | 表格 | 数值字段、multi numeric | 可运行 | 统计目录 |
| `ridge_regression_text` | 岭回归 | Ridge Regression | 文字解读 | 数值字段、multi numeric | 可运行 | 统计目录 |
| `robust_regression_data` | 稳健回归 | Robust Regression | 结构化数据 | 数值字段、multi numeric | 可运行 | 统计目录 |
| `robust_regression_table` | 稳健回归 | Robust Regression | 表格 | 数值字段、multi numeric | 可运行 | 统计目录 |
| `robust_regression_text` | 稳健回归 | Robust Regression | 文字解读 | 数值字段、multi numeric | 可运行 | 统计目录 |
| `spatial_error_model_data` | 空间误差模型 | Spatial Error Model | 结构化数据 | target、features、对象级 | 目录条目 | 统计目录 |
| `spatial_error_model_table` | 空间误差模型 | Spatial Error Model | 表格 | target、features、对象级 | 目录条目 | 统计目录 |
| `spatial_error_model_text` | 空间误差模型 | Spatial Error Model | 文字解读 | target、features、对象级 | 目录条目 | 统计目录 |
| `spatial_lag_model_data` | 空间滞后模型 | Spatial Lag Model | 结构化数据 | target、features、对象级 | 目录条目 | 统计目录 |
| `spatial_lag_model_table` | 空间滞后模型 | Spatial Lag Model | 表格 | target、features、对象级 | 目录条目 | 统计目录 |
| `spatial_lag_model_text` | 空间滞后模型 | Spatial Lag Model | 文字解读 | target、features、对象级 | 目录条目 | 统计目录 |
| `spline_regression_chart` | 样条回归 | Spline Regression | 图表 | target、features | 目录条目 | 统计目录 |
| `spline_regression_data` | 样条回归 | Spline Regression | 结构化数据 | target、features | 目录条目 | 统计目录 |
| `spline_regression_image_spec` | 样条回归 | Spline Regression | 图片规格 | target、features | 目录条目 | 统计目录 |
| `spline_regression_report_section` | 样条回归 | Spline Regression | 报告段落 | target、features | 目录条目 | 统计目录 |
| `spline_regression_table` | 样条回归 | Spline Regression | 表格 | target、features | 目录条目 | 统计目录 |
| `spline_regression_text` | 样条回归 | Spline Regression | 文字解读 | target、features | 目录条目 | 统计目录 |
| `stepwise_model_comparison_data` | 逐步模型比较 | Stepwise Model Comparison | 结构化数据 | target、features | 目录条目 | 统计目录 |
| `stepwise_model_comparison_table` | 逐步模型比较 | Stepwise Model Comparison | 表格 | target、features | 目录条目 | 统计目录 |
| `stepwise_model_comparison_text` | 逐步模型比较 | Stepwise Model Comparison | 文字解读 | target、features | 目录条目 | 统计目录 |
| `vif_multicollinearity_data` | 方差膨胀因子共线性诊断 | VIF Multicollinearity Diagnostic | 结构化数据 | target、features | 目录条目 | 统计目录 |
| `vif_multicollinearity_table` | 方差膨胀因子共线性诊断 | VIF Multicollinearity Diagnostic | 表格 | target、features | 目录条目 | 统计目录 |
| `vif_multicollinearity_text` | 方差膨胀因子共线性诊断 | VIF Multicollinearity Diagnostic | 文字解读 | target、features | 目录条目 | 统计目录 |
| `zero_inflated_poisson_data` | 零膨胀泊松模型 | Zero-inflated Poisson | 结构化数据 | count、multi numeric | 目录条目 | 统计目录 |
| `zero_inflated_poisson_table` | 零膨胀泊松模型 | Zero-inflated Poisson | 表格 | count、multi numeric | 目录条目 | 统计目录 |
| `zero_inflated_poisson_text` | 零膨胀泊松模型 | Zero-inflated Poisson | 文字解读 | count、multi numeric | 目录条目 | 统计目录 |

### 分析方法（注册族：`心理测量`；24 张；可运行 0 张）

| 卡片 ID | 中文方法名称 | 原始英文概念 | 中文输出形式 | 字段角色 | 状态 | 来源 |
| --- | --- | --- | --- | --- | --- | --- |
| `item_response_theory_data` | 项目反应理论 | Item Response Theory | 结构化数据 | item response | 目录条目 | 统计目录 |
| `item_response_theory_table` | 项目反应理论 | Item Response Theory | 表格 | item response | 目录条目 | 统计目录 |
| `item_response_theory_text` | 项目反应理论 | Item Response Theory | 文字解读 | item response | 目录条目 | 统计目录 |
| `latent_growth_model_data` | 潜在增长模型 | Latent Growth Model | 结构化数据 | repeated measure | 目录条目 | 统计目录 |
| `latent_growth_model_table` | 潜在增长模型 | Latent Growth Model | 表格 | repeated measure | 目录条目 | 统计目录 |
| `latent_growth_model_text` | 潜在增长模型 | Latent Growth Model | 文字解读 | repeated measure | 目录条目 | 统计目录 |
| `measurement_invariance_data` | 测量等值性检验 | Measurement Invariance | 结构化数据 | multi group scale | 目录条目 | 统计目录 |
| `measurement_invariance_table` | 测量等值性检验 | Measurement Invariance | 表格 | multi group scale | 目录条目 | 统计目录 |
| `measurement_invariance_text` | 测量等值性检验 | Measurement Invariance | 文字解读 | multi group scale | 目录条目 | 统计目录 |
| `mediation_analysis_data` | 中介效应分析 | Mediation Analysis | 结构化数据 | x、m、y | 目录条目 | 统计目录 |
| `mediation_analysis_table` | 中介效应分析 | Mediation Analysis | 表格 | x、m、y | 目录条目 | 统计目录 |
| `mediation_analysis_text` | 中介效应分析 | Mediation Analysis | 文字解读 | x、m、y | 目录条目 | 统计目录 |
| `moderation_analysis_data` | 调节效应分析 | Moderation Analysis | 结构化数据 | x、moderator、y | 目录条目 | 统计目录 |
| `moderation_analysis_table` | 调节效应分析 | Moderation Analysis | 表格 | x、moderator、y | 目录条目 | 统计目录 |
| `moderation_analysis_text` | 调节效应分析 | Moderation Analysis | 文字解读 | x、moderator、y | 目录条目 | 统计目录 |
| `reliability_cronbach_alpha_data` | 克朗巴赫阿尔法信度 | Cronbach Alpha | 结构化数据 | multi item scale | 目录条目 | 统计目录 |
| `reliability_cronbach_alpha_table` | 克朗巴赫阿尔法信度 | Cronbach Alpha | 表格 | multi item scale | 目录条目 | 统计目录 |
| `reliability_cronbach_alpha_text` | 克朗巴赫阿尔法信度 | Cronbach Alpha | 文字解读 | multi item scale | 目录条目 | 统计目录 |
| `sem_data` | 结构方程模型 | Structural Equation Modeling | 结构化数据 | multi numeric、latent | 目录条目 | 统计目录 |
| `sem_table` | 结构方程模型 | Structural Equation Modeling | 表格 | multi numeric、latent | 目录条目 | 统计目录 |
| `sem_text` | 结构方程模型 | Structural Equation Modeling | 文字解读 | multi numeric、latent | 目录条目 | 统计目录 |
| `split_half_reliability_data` | 折半信度 | Split-half Reliability | 结构化数据 | multi item scale | 目录条目 | 统计目录 |
| `split_half_reliability_table` | 折半信度 | Split-half Reliability | 表格 | multi item scale | 目录条目 | 统计目录 |
| `split_half_reliability_text` | 折半信度 | Split-half Reliability | 文字解读 | multi item scale | 目录条目 | 统计目录 |

### 分析方法（注册族：`报告部件`；14 张；可运行 0 张）

| 卡片 ID | 中文方法名称 | 原始英文概念 | 中文输出形式 | 字段角色 | 状态 | 来源 |
| --- | --- | --- | --- | --- | --- | --- |
| `explainable_dashboard_narrative_chart` | 可解释仪表盘叙述 | Explainable Dashboard Narrative | 图表 | 全数据集 | 目录条目 | 统计目录 |
| `explainable_dashboard_narrative_data` | 可解释仪表盘叙述 | Explainable Dashboard Narrative | 结构化数据 | 全数据集 | 目录条目 | 统计目录 |
| `explainable_dashboard_narrative_image_spec` | 可解释仪表盘叙述 | Explainable Dashboard Narrative | 图片规格 | 全数据集 | 目录条目 | 统计目录 |
| `explainable_dashboard_narrative_report_section` | 可解释仪表盘叙述 | Explainable Dashboard Narrative | 报告段落 | 全数据集 | 目录条目 | 统计目录 |
| `explainable_dashboard_narrative_table` | 可解释仪表盘叙述 | Explainable Dashboard Narrative | 表格 | 全数据集 | 目录条目 | 统计目录 |
| `explainable_dashboard_narrative_text` | 可解释仪表盘叙述 | Explainable Dashboard Narrative | 文字解读 | 全数据集 | 目录条目 | 统计目录 |
| `report_part_action_plan` | 报告部件・分析方法 | 行动建议 | 报告段落 | 全数据集 | 规划条目 | 自动分析规格目录 |
| `report_part_appendix` | 报告部件・附录 | 分析附录 | 报告段落 | 全数据集 | 规划条目 | 自动分析规格目录 |
| `report_part_chapter` | 报告部件・章节 | 分析章节 | 报告段落 | 全数据集 | 规划条目 | 自动分析规格目录 |
| `report_part_evidence_index` | 报告部件・分析方法 | 证据索引 | 报告段落 | 全数据集 | 规划条目 | 自动分析规格目录 |
| `report_part_executive_summary` | 报告部件・概览 | 管理摘要 | 报告段落 | 全数据集 | 规划条目 | 自动分析规格目录 |
| `report_part_field_glossary` | 报告部件・分析方法 | 字段解释 | 报告段落 | 全数据集 | 规划条目 | 自动分析规格目录 |
| `report_part_method_note` | 报告部件・分析方法 | 方法说明 | 报告段落 | 全数据集 | 规划条目 | 自动分析规格目录 |
| `report_part_visual_gallery` | 报告部件・可视化 | 图组解读 | 报告段落 | 全数据集 | 规划条目 | 自动分析规格目录 |

### 分析方法（注册族：`描述统计`；210 张；可运行 36 张）

| 卡片 ID | 中文方法名称 | 原始英文概念 | 中文输出形式 | 字段角色 | 状态 | 来源 |
| --- | --- | --- | --- | --- | --- | --- |
| `areal_interpolation_data` | 区域插值 | Areal Interpolation | 结构化数据 | 对象级、数值字段 | 目录条目 | 统计目录 |
| `areal_interpolation_table` | 区域插值 | Areal Interpolation | 表格 | 对象级、数值字段 | 目录条目 | 统计目录 |
| `areal_interpolation_text` | 区域插值 | Areal Interpolation | 文字解读 | 对象级、数值字段 | 目录条目 | 统计目录 |
| `boxcox_transformation_data` | Box-Cox 变换 | Box-Cox Transformation | 结构化数据 | 数值字段 | 目录条目 | 统计目录 |
| `boxcox_transformation_table` | Box-Cox 变换 | Box-Cox Transformation | 表格 | 数值字段 | 目录条目 | 统计目录 |
| `boxcox_transformation_text` | Box-Cox 变换 | Box-Cox Transformation | 文字解读 | 数值字段 | 目录条目 | 统计目录 |
| `business_rule_validation_data` | 业务规则校验 | Business Rule Validation | 结构化数据 | 字段组 | 目录条目 | 统计目录 |
| `business_rule_validation_table` | 业务规则校验 | Business Rule Validation | 表格 | 字段组 | 目录条目 | 统计目录 |
| `business_rule_validation_text` | 业务规则校验 | Business Rule Validation | 文字解读 | 字段组 | 目录条目 | 统计目录 |
| `cluster_sampling_design_data` | 整群抽样设计 | Cluster Sampling Design | 结构化数据 | 对象级、分组 | 目录条目 | 统计目录 |
| `cluster_sampling_design_table` | 整群抽样设计 | Cluster Sampling Design | 表格 | 对象级、分组 | 目录条目 | 统计目录 |
| `cluster_sampling_design_text` | 整群抽样设计 | Cluster Sampling Design | 文字解读 | 对象级、分组 | 目录条目 | 统计目录 |
| `cohort_summary_chart` | 队列汇总 | Cohort Summary | 图表 | time、分类字段、数值字段 | 目录条目 | 统计目录 |
| `cohort_summary_data` | 队列汇总 | Cohort Summary | 结构化数据 | time、分类字段、数值字段 | 目录条目 | 统计目录 |
| `cohort_summary_image_spec` | 队列汇总 | Cohort Summary | 图片规格 | time、分类字段、数值字段 | 目录条目 | 统计目录 |
| `cohort_summary_report_section` | 队列汇总 | Cohort Summary | 报告段落 | time、分类字段、数值字段 | 目录条目 | 统计目录 |
| `cohort_summary_table` | 队列汇总 | Cohort Summary | 表格 | time、分类字段、数值字段 | 目录条目 | 统计目录 |
| `cohort_summary_text` | 队列汇总 | Cohort Summary | 文字解读 | time、分类字段、数值字段 | 目录条目 | 统计目录 |
| `completeness_sla_monitor_data` | 数据完整性服务等级监控 | Completeness SLA Monitor | 结构化数据 | 全数据集 | 目录条目 | 统计目录 |
| `completeness_sla_monitor_table` | 数据完整性服务等级监控 | Completeness SLA Monitor | 表格 | 全数据集 | 目录条目 | 统计目录 |
| `completeness_sla_monitor_text` | 数据完整性服务等级监控 | Completeness SLA Monitor | 文字解读 | 全数据集 | 目录条目 | 统计目录 |
| `consent_coverage_audit_data` | 同意范围审计 | Consent Coverage Audit | 结构化数据 | 字段组 | 目录条目 | 统计目录 |
| `consent_coverage_audit_table` | 同意范围审计 | Consent Coverage Audit | 表格 | 字段组 | 目录条目 | 统计目录 |
| `consent_coverage_audit_text` | 同意范围审计 | Consent Coverage Audit | 文字解读 | 字段组 | 目录条目 | 统计目录 |
| `cross_tabulation_data` | 交叉列联表 | Cross Tabulation | 结构化数据 | 分类字段、分类字段 | 可运行 | 统计目录 |
| `cross_tabulation_table` | 交叉列联表 | Cross Tabulation | 表格 | 分类字段、分类字段 | 可运行 | 统计目录 |
| `cross_tabulation_text` | 交叉列联表 | Cross Tabulation | 文字解读 | 分类字段、分类字段 | 可运行 | 统计目录 |
| `data_contract_validation_data` | 数据契约校验 | Data Contract Validation | 结构化数据 | 全数据集 | 目录条目 | 统计目录 |
| `data_contract_validation_table` | 数据契约校验 | Data Contract Validation | 表格 | 全数据集 | 目录条目 | 统计目录 |
| `data_contract_validation_text` | 数据契约校验 | Data Contract Validation | 文字解读 | 全数据集 | 目录条目 | 统计目录 |
| `data_minimization_audit_data` | 数据最小化审计 | Data Minimization Audit | 结构化数据 | 字段组 | 目录条目 | 统计目录 |
| `data_minimization_audit_table` | 数据最小化审计 | Data Minimization Audit | 表格 | 字段组 | 目录条目 | 统计目录 |
| `data_minimization_audit_text` | 数据最小化审计 | Data Minimization Audit | 文字解读 | 字段组 | 目录条目 | 统计目录 |
| `data_quality_scorecard_data` | 数据质量评分卡 | Data Quality Scorecard | 结构化数据 | 全数据集 | 目录条目 | 统计目录 |
| `data_quality_scorecard_table` | 数据质量评分卡 | Data Quality Scorecard | 表格 | 全数据集 | 目录条目 | 统计目录 |
| `data_quality_scorecard_text` | 数据质量评分卡 | Data Quality Scorecard | 文字解读 | 全数据集 | 目录条目 | 统计目录 |
| `data_type_validation_data` | 数据类型校验 | Data Type Validation | 结构化数据 | 字段组 | 目录条目 | 统计目录 |
| `data_type_validation_table` | 数据类型校验 | Data Type Validation | 表格 | 字段组 | 目录条目 | 统计目录 |
| `data_type_validation_text` | 数据类型校验 | Data Type Validation | 文字解读 | 字段组 | 目录条目 | 统计目录 |
| `datasheet_for_dataset_data` | 数据集说明书 | Datasheet for Dataset | 结构化数据 | 全数据集 | 目录条目 | 统计目录 |
| `datasheet_for_dataset_table` | 数据集说明书 | Datasheet for Dataset | 表格 | 全数据集 | 目录条目 | 统计目录 |
| `datasheet_for_dataset_text` | 数据集说明书 | Datasheet for Dataset | 文字解读 | 全数据集 | 目录条目 | 统计目录 |
| `denominator_integrity_check_data` | 分母完整性检查 | Denominator Integrity Check | 结构化数据 | 字段对、分组 | 目录条目 | 统计目录 |
| `denominator_integrity_check_table` | 分母完整性检查 | Denominator Integrity Check | 表格 | 字段对、分组 | 目录条目 | 统计目录 |
| `denominator_integrity_check_text` | 分母完整性检查 | Denominator Integrity Check | 文字解读 | 字段对、分组 | 目录条目 | 统计目录 |
| `descriptive_coverage` | 描述统计・覆盖情况 | 覆盖情况 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `descriptive_distribution` | 描述统计・分布 | 分布 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `descriptive_missingness` | 描述统计・缺失情况 | 缺失情况 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `descriptive_profile` | 描述统计・画像 | 画像 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `descriptive_rank` | 描述统计・排名 | 排名 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `descriptive_segment` | 描述统计・分层 | 分层 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `descriptive_summary_data` | 描述性统计摘要 | Descriptive Summary | 结构化数据 | 数值字段 | 可运行 | 统计目录 |
| `descriptive_summary_table` | 描述性统计摘要 | Descriptive Summary | 表格 | 数值字段 | 可运行 | 统计目录 |
| `descriptive_summary_text` | 描述性统计摘要 | Descriptive Summary | 文字解读 | 数值字段 | 可运行 | 统计目录 |
| `duplicate_record_audit_data` | 重复记录审计 | Duplicate Record Audit | 结构化数据 | 字段组 | 目录条目 | 统计目录 |
| `duplicate_record_audit_table` | 重复记录审计 | Duplicate Record Audit | 表格 | 字段组 | 目录条目 | 统计目录 |
| `duplicate_record_audit_text` | 重复记录审计 | Duplicate Record Audit | 文字解读 | 字段组 | 目录条目 | 统计目录 |
| `ego_network_profile_data` | 自我中心网络画像 | Ego Network Profile | 结构化数据 | 对象级 | 目录条目 | 统计目录 |
| `ego_network_profile_table` | 自我中心网络画像 | Ego Network Profile | 表格 | 对象级 | 目录条目 | 统计目录 |
| `ego_network_profile_text` | 自我中心网络画像 | Ego Network Profile | 文字解读 | 对象级 | 目录条目 | 统计目录 |
| `feature_binning_strategy_data` | 特征分箱策略 | Feature Binning Strategy | 结构化数据 | 数值字段 | 目录条目 | 统计目录 |
| `feature_binning_strategy_table` | 特征分箱策略 | Feature Binning Strategy | 表格 | 数值字段 | 目录条目 | 统计目录 |
| `feature_binning_strategy_text` | 特征分箱策略 | Feature Binning Strategy | 文字解读 | 数值字段 | 目录条目 | 统计目录 |
| `frequency_table_data` | 频数表 | Frequency Table | 结构化数据 | 分类字段 | 可运行 | 统计目录 |
| `frequency_table_table` | 频数表 | Frequency Table | 表格 | 分类字段 | 可运行 | 统计目录 |
| `frequency_table_text` | 频数表 | Frequency Table | 文字解读 | 分类字段 | 可运行 | 统计目录 |
| `funnel_step_conversion_data` | 漏斗步骤转化分析 | Funnel Step Conversion | 结构化数据 | 分类字段、数值字段 | 目录条目 | 统计目录 |
| `funnel_step_conversion_table` | 漏斗步骤转化分析 | Funnel Step Conversion | 表格 | 分类字段、数值字段 | 目录条目 | 统计目录 |
| `funnel_step_conversion_text` | 漏斗步骤转化分析 | Funnel Step Conversion | 文字解读 | 分类字段、数值字段 | 目录条目 | 统计目录 |
| `geohash_grid_aggregation_chart` | 地理哈希网格汇总 | Geohash Grid Aggregation | 图表 | 对象级、数值字段 | 目录条目 | 统计目录 |
| `geohash_grid_aggregation_data` | 地理哈希网格汇总 | Geohash Grid Aggregation | 结构化数据 | 对象级、数值字段 | 目录条目 | 统计目录 |
| `geohash_grid_aggregation_image_spec` | 地理哈希网格汇总 | Geohash Grid Aggregation | 图片规格 | 对象级、数值字段 | 目录条目 | 统计目录 |
| `geohash_grid_aggregation_report_section` | 地理哈希网格汇总 | Geohash Grid Aggregation | 报告段落 | 对象级、数值字段 | 目录条目 | 统计目录 |
| `geohash_grid_aggregation_table` | 地理哈希网格汇总 | Geohash Grid Aggregation | 表格 | 对象级、数值字段 | 目录条目 | 统计目录 |
| `geohash_grid_aggregation_text` | 地理哈希网格汇总 | Geohash Grid Aggregation | 文字解读 | 对象级、数值字段 | 目录条目 | 统计目录 |
| `gini_coefficient_data` | 基尼系数 | Gini Coefficient | 结构化数据 | 数值字段 | 可运行 | 统计目录 |
| `gini_coefficient_table` | 基尼系数 | Gini Coefficient | 表格 | 数值字段 | 可运行 | 统计目录 |
| `gini_coefficient_text` | 基尼系数 | Gini Coefficient | 文字解读 | 数值字段 | 可运行 | 统计目录 |
| `high_cardinality_profile_data` | 高基数特征画像 | High-cardinality Profile | 结构化数据 | 分类字段 | 目录条目 | 统计目录 |
| `high_cardinality_profile_table` | 高基数特征画像 | High-cardinality Profile | 表格 | 分类字段 | 目录条目 | 统计目录 |
| `high_cardinality_profile_text` | 高基数特征画像 | High-cardinality Profile | 文字解读 | 分类字段 | 目录条目 | 统计目录 |
| `imputation_strategy_plan_data` | 缺失值填补策略规划 | Imputation Strategy Plan | 结构化数据 | 字段组 | 目录条目 | 统计目录 |
| `imputation_strategy_plan_table` | 缺失值填补策略规划 | Imputation Strategy Plan | 表格 | 字段组 | 目录条目 | 统计目录 |
| `imputation_strategy_plan_text` | 缺失值填补策略规划 | Imputation Strategy Plan | 文字解读 | 字段组 | 目录条目 | 统计目录 |
| `keyword_in_context_review_data` | 关键词上下文评审 | Keyword-in-context Review | 结构化数据 | 字段组 | 目录条目 | 统计目录 |
| `keyword_in_context_review_table` | 关键词上下文评审 | Keyword-in-context Review | 表格 | 字段组 | 目录条目 | 统计目录 |
| `keyword_in_context_review_text` | 关键词上下文评审 | Keyword-in-context Review | 文字解读 | 字段组 | 目录条目 | 统计目录 |
| `lorenz_curve_chart` | 洛伦兹曲线 | Lorenz Curve | 图表 | 数值字段 | 目录条目 | 统计目录 |
| `lorenz_curve_data` | 洛伦兹曲线 | Lorenz Curve | 结构化数据 | 数值字段 | 目录条目 | 统计目录 |
| `lorenz_curve_image_spec` | 洛伦兹曲线 | Lorenz Curve | 图片规格 | 数值字段 | 目录条目 | 统计目录 |
| `lorenz_curve_report_section` | 洛伦兹曲线 | Lorenz Curve | 报告段落 | 数值字段 | 目录条目 | 统计目录 |
| `lorenz_curve_table` | 洛伦兹曲线 | Lorenz Curve | 表格 | 数值字段 | 目录条目 | 统计目录 |
| `lorenz_curve_text` | 洛伦兹曲线 | Lorenz Curve | 文字解读 | 数值字段 | 目录条目 | 统计目录 |
| `measurement_error_audit_data` | 测量误差审计 | Measurement Error Audit | 结构化数据 | 字段组 | 目录条目 | 统计目录 |
| `measurement_error_audit_table` | 测量误差审计 | Measurement Error Audit | 表格 | 字段组 | 目录条目 | 统计目录 |
| `measurement_error_audit_text` | 测量误差审计 | Measurement Error Audit | 文字解读 | 字段组 | 目录条目 | 统计目录 |
| `missingness_heatmap_audit_chart` | 缺失值热力审计 | Missingness Heatmap Audit | 图表 | 字段组 | 目录条目 | 统计目录 |
| `missingness_heatmap_audit_data` | 缺失值热力审计 | Missingness Heatmap Audit | 结构化数据 | 字段组 | 目录条目 | 统计目录 |
| `missingness_heatmap_audit_image_spec` | 缺失值热力审计 | Missingness Heatmap Audit | 图片规格 | 字段组 | 目录条目 | 统计目录 |
| `missingness_heatmap_audit_report_section` | 缺失值热力审计 | Missingness Heatmap Audit | 报告段落 | 字段组 | 目录条目 | 统计目录 |
| `missingness_heatmap_audit_table` | 缺失值热力审计 | Missingness Heatmap Audit | 表格 | 字段组 | 目录条目 | 统计目录 |
| `missingness_heatmap_audit_text` | 缺失值热力审计 | Missingness Heatmap Audit | 文字解读 | 字段组 | 目录条目 | 统计目录 |
| `missingness_mechanism_diagnostic_data` | 缺失机制诊断 | Missingness Mechanism Diagnostic | 结构化数据 | 字段组 | 目录条目 | 统计目录 |
| `missingness_mechanism_diagnostic_table` | 缺失机制诊断 | Missingness Mechanism Diagnostic | 表格 | 字段组 | 目录条目 | 统计目录 |
| `missingness_mechanism_diagnostic_text` | 缺失机制诊断 | Missingness Mechanism Diagnostic | 文字解读 | 字段组 | 目录条目 | 统计目录 |
| `nonresponse_bias_analysis_data` | 无应答偏差分析 | Nonresponse Bias Analysis | 结构化数据 | 字段组、分组 | 目录条目 | 统计目录 |
| `nonresponse_bias_analysis_table` | 无应答偏差分析 | Nonresponse Bias Analysis | 表格 | 字段组、分组 | 目录条目 | 统计目录 |
| `nonresponse_bias_analysis_text` | 无应答偏差分析 | Nonresponse Bias Analysis | 文字解读 | 字段组、分组 | 目录条目 | 统计目录 |
| `north_star_metric_audit_data` | 北极星指标审计 | North-star Metric Audit | 结构化数据 | 字段组 | 目录条目 | 统计目录 |
| `north_star_metric_audit_table` | 北极星指标审计 | North-star Metric Audit | 表格 | 字段组 | 目录条目 | 统计目录 |
| `north_star_metric_audit_text` | 北极星指标审计 | North-star Metric Audit | 文字解读 | 字段组 | 目录条目 | 统计目录 |
| `outlier_screening_iqr_data` | 四分位距异常值筛查 | IQR Outlier Screening | 结构化数据 | 数值字段 | 目录条目 | 统计目录 |
| `outlier_screening_iqr_table` | 四分位距异常值筛查 | IQR Outlier Screening | 表格 | 数值字段 | 目录条目 | 统计目录 |
| `outlier_screening_iqr_text` | 四分位距异常值筛查 | IQR Outlier Screening | 文字解读 | 数值字段 | 目录条目 | 统计目录 |
| `pareto_analysis_chart` | 帕累托分析 | Pareto Analysis | 图表 | 分类字段、数值字段 | 可运行 | 统计目录 |
| `pareto_analysis_data` | 帕累托分析 | Pareto Analysis | 结构化数据 | 分类字段、数值字段 | 可运行 | 统计目录 |
| `pareto_analysis_image_spec` | 帕累托分析 | Pareto Analysis | 图片规格 | 分类字段、数值字段 | 可运行 | 统计目录 |
| `pareto_analysis_report_section` | 帕累托分析 | Pareto Analysis | 报告段落 | 分类字段、数值字段 | 可运行 | 统计目录 |
| `pareto_analysis_table` | 帕累托分析 | Pareto Analysis | 表格 | 分类字段、数值字段 | 可运行 | 统计目录 |
| `pareto_analysis_text` | 帕累托分析 | Pareto Analysis | 文字解读 | 分类字段、数值字段 | 可运行 | 统计目录 |
| `pii_detection_profile_data` | 个人敏感信息检测画像 | PII Detection Profile | 结构化数据 | 字段组 | 目录条目 | 统计目录 |
| `pii_detection_profile_table` | 个人敏感信息检测画像 | PII Detection Profile | 表格 | 字段组 | 目录条目 | 统计目录 |
| `pii_detection_profile_text` | 个人敏感信息检测画像 | PII Detection Profile | 文字解读 | 字段组 | 目录条目 | 统计目录 |
| `pivot_summary_data` | 透视汇总 | Pivot Summary | 结构化数据 | 分类字段、数值字段 | 可运行 | 统计目录 |
| `pivot_summary_table` | 透视汇总 | Pivot Summary | 表格 | 分类字段、数值字段 | 可运行 | 统计目录 |
| `pivot_summary_text` | 透视汇总 | Pivot Summary | 文字解读 | 分类字段、数值字段 | 可运行 | 统计目录 |
| `post_stratification_weighting_data` | 后分层加权 | Post-stratification Weighting | 结构化数据 | 字段组、分组 | 目录条目 | 统计目录 |
| `post_stratification_weighting_table` | 后分层加权 | Post-stratification Weighting | 表格 | 字段组、分组 | 目录条目 | 统计目录 |
| `post_stratification_weighting_text` | 后分层加权 | Post-stratification Weighting | 文字解读 | 字段组、分组 | 目录条目 | 统计目录 |
| `privacy_k_anonymity_data` | K 匿名隐私检查 | k-anonymity Privacy Check | 结构化数据 | 字段组 | 目录条目 | 统计目录 |
| `privacy_k_anonymity_table` | K 匿名隐私检查 | k-anonymity Privacy Check | 表格 | 字段组 | 目录条目 | 统计目录 |
| `privacy_k_anonymity_text` | K 匿名隐私检查 | k-anonymity Privacy Check | 文字解读 | 字段组 | 目录条目 | 统计目录 |
| `privacy_l_diversity_data` | L 多样性隐私检查 | l-diversity Privacy Check | 结构化数据 | 字段组 | 目录条目 | 统计目录 |
| `privacy_l_diversity_table` | L 多样性隐私检查 | l-diversity Privacy Check | 表格 | 字段组 | 目录条目 | 统计目录 |
| `privacy_l_diversity_text` | L 多样性隐私检查 | l-diversity Privacy Check | 文字解读 | 字段组 | 目录条目 | 统计目录 |
| `quantile_profile_data` | 分位数画像 | Quantile Profile | 结构化数据 | 数值字段 | 可运行 | 统计目录 |
| `quantile_profile_table` | 分位数画像 | Quantile Profile | 表格 | 数值字段 | 可运行 | 统计目录 |
| `quantile_profile_text` | 分位数画像 | Quantile Profile | 文字解读 | 数值字段 | 可运行 | 统计目录 |
| `raking_weighting_data` | 迭代比例拟合加权 | Raking Weighting | 结构化数据 | 字段组、分组 | 目录条目 | 统计目录 |
| `raking_weighting_table` | 迭代比例拟合加权 | Raking Weighting | 表格 | 字段组、分组 | 目录条目 | 统计目录 |
| `raking_weighting_text` | 迭代比例拟合加权 | Raking Weighting | 文字解读 | 字段组、分组 | 目录条目 | 统计目录 |
| `range_constraint_validation_data` | 范围约束校验 | Range Constraint Validation | 结构化数据 | 字段组 | 目录条目 | 统计目录 |
| `range_constraint_validation_table` | 范围约束校验 | Range Constraint Validation | 表格 | 字段组 | 目录条目 | 统计目录 |
| `range_constraint_validation_text` | 范围约束校验 | Range Constraint Validation | 文字解读 | 字段组 | 目录条目 | 统计目录 |
| `rare_category_consolidation_data` | 稀有类别合并 | Rare Category Consolidation | 结构化数据 | 分类字段 | 目录条目 | 统计目录 |
| `rare_category_consolidation_table` | 稀有类别合并 | Rare Category Consolidation | 表格 | 分类字段 | 目录条目 | 统计目录 |
| `rare_category_consolidation_text` | 稀有类别合并 | Rare Category Consolidation | 文字解读 | 分类字段 | 目录条目 | 统计目录 |
| `referential_integrity_check_data` | 引用完整性检查 | Referential Integrity Check | 结构化数据 | 字段组 | 目录条目 | 统计目录 |
| `referential_integrity_check_table` | 引用完整性检查 | Referential Integrity Check | 表格 | 字段组 | 目录条目 | 统计目录 |
| `referential_integrity_check_text` | 引用完整性检查 | Referential Integrity Check | 文字解读 | 字段组 | 目录条目 | 统计目录 |
| `retention_policy_audit_data` | 数据保留策略审计 | Retention Policy Audit | 结构化数据 | time、字段组 | 目录条目 | 统计目录 |
| `retention_policy_audit_table` | 数据保留策略审计 | Retention Policy Audit | 表格 | time、字段组 | 目录条目 | 统计目录 |
| `retention_policy_audit_text` | 数据保留策略审计 | Retention Policy Audit | 文字解读 | time、字段组 | 目录条目 | 统计目录 |
| `robust_zscore_outlier_data` | 稳健 Z 分数异常值筛查 | Robust Z-score Outlier Screening | 结构化数据 | 数值字段 | 目录条目 | 统计目录 |
| `robust_zscore_outlier_table` | 稳健 Z 分数异常值筛查 | Robust Z-score Outlier Screening | 表格 | 数值字段 | 目录条目 | 统计目录 |
| `robust_zscore_outlier_text` | 稳健 Z 分数异常值筛查 | Robust Z-score Outlier Screening | 文字解读 | 数值字段 | 目录条目 | 统计目录 |
| `root_cause_data_quality_data` | 数据质量根因分析 | Data Quality Root Cause Analysis | 结构化数据 | 全数据集 | 目录条目 | 统计目录 |
| `root_cause_data_quality_table` | 数据质量根因分析 | Data Quality Root Cause Analysis | 表格 | 全数据集 | 目录条目 | 统计目录 |
| `root_cause_data_quality_text` | 数据质量根因分析 | Data Quality Root Cause Analysis | 文字解读 | 全数据集 | 目录条目 | 统计目录 |
| `sampling_bias_audit_data` | 抽样偏差审计 | Sampling Bias Audit | 结构化数据 | 字段组、分组 | 目录条目 | 统计目录 |
| `sampling_bias_audit_table` | 抽样偏差审计 | Sampling Bias Audit | 表格 | 字段组、分组 | 目录条目 | 统计目录 |
| `sampling_bias_audit_text` | 抽样偏差审计 | Sampling Bias Audit | 文字解读 | 字段组、分组 | 目录条目 | 统计目录 |
| `schema_drift_detection_data` | 模式漂移检测 | Schema Drift Detection | 结构化数据 | 全数据集 | 目录条目 | 统计目录 |
| `schema_drift_detection_table` | 模式漂移检测 | Schema Drift Detection | 表格 | 全数据集 | 目录条目 | 统计目录 |
| `schema_drift_detection_text` | 模式漂移检测 | Schema Drift Detection | 文字解读 | 全数据集 | 目录条目 | 统计目录 |
| `segmented_kpi_breakdown_chart` | 分层关键指标拆解 | Segmented KPI Breakdown | 图表 | 分类字段、数值字段 | 可运行 | 统计目录 |
| `segmented_kpi_breakdown_data` | 分层关键指标拆解 | Segmented KPI Breakdown | 结构化数据 | 分类字段、数值字段 | 可运行 | 统计目录 |
| `segmented_kpi_breakdown_image_spec` | 分层关键指标拆解 | Segmented KPI Breakdown | 图片规格 | 分类字段、数值字段 | 可运行 | 统计目录 |
| `segmented_kpi_breakdown_report_section` | 分层关键指标拆解 | Segmented KPI Breakdown | 报告段落 | 分类字段、数值字段 | 可运行 | 统计目录 |
| `segmented_kpi_breakdown_table` | 分层关键指标拆解 | Segmented KPI Breakdown | 表格 | 分类字段、数值字段 | 可运行 | 统计目录 |
| `segmented_kpi_breakdown_text` | 分层关键指标拆解 | Segmented KPI Breakdown | 文字解读 | 分类字段、数值字段 | 可运行 | 统计目录 |
| `semantic_deduplication_data` | 语义去重 | Semantic Deduplication | 结构化数据 | 字段组 | 目录条目 | 统计目录 |
| `semantic_deduplication_table` | 语义去重 | Semantic Deduplication | 表格 | 字段组 | 目录条目 | 统计目录 |
| `semantic_deduplication_text` | 语义去重 | Semantic Deduplication | 文字解读 | 字段组 | 目录条目 | 统计目录 |
| `small_area_estimation_data` | 小域估计 | Small Area Estimation | 结构化数据 | 对象级、分组 | 目录条目 | 统计目录 |
| `small_area_estimation_table` | 小域估计 | Small Area Estimation | 表格 | 对象级、分组 | 目录条目 | 统计目录 |
| `small_area_estimation_text` | 小域估计 | Small Area Estimation | 文字解读 | 对象级、分组 | 目录条目 | 统计目录 |
| `spatial_join_audit_data` | 空间连接审计 | Spatial Join Audit | 结构化数据 | 对象级 | 目录条目 | 统计目录 |
| `spatial_join_audit_table` | 空间连接审计 | Spatial Join Audit | 表格 | 对象级 | 目录条目 | 统计目录 |
| `spatial_join_audit_text` | 空间连接审计 | Spatial Join Audit | 文字解读 | 对象级 | 目录条目 | 统计目录 |
| `standardization_scaling_data` | 标准化与缩放 | Standardization / Scaling | 结构化数据 | 字段组 | 目录条目 | 统计目录 |
| `standardization_scaling_table` | 标准化与缩放 | Standardization / Scaling | 表格 | 字段组 | 目录条目 | 统计目录 |
| `standardization_scaling_text` | 标准化与缩放 | Standardization / Scaling | 文字解读 | 字段组 | 目录条目 | 统计目录 |
| `stratified_sampling_design_data` | 分层抽样设计 | Stratified Sampling Design | 结构化数据 | 分组、字段组 | 目录条目 | 统计目录 |
| `stratified_sampling_design_table` | 分层抽样设计 | Stratified Sampling Design | 表格 | 分组、字段组 | 目录条目 | 统计目录 |
| `stratified_sampling_design_text` | 分层抽样设计 | Stratified Sampling Design | 文字解读 | 分组、字段组 | 目录条目 | 统计目录 |
| `survey_design_effect_chart` | 调查设计效应 | Survey Design Effect | 图表 | 字段组、分组 | 目录条目 | 统计目录 |
| `survey_design_effect_data` | 调查设计效应 | Survey Design Effect | 结构化数据 | 字段组、分组 | 目录条目 | 统计目录 |
| `survey_design_effect_image_spec` | 调查设计效应 | Survey Design Effect | 图片规格 | 字段组、分组 | 目录条目 | 统计目录 |
| `survey_design_effect_report_section` | 调查设计效应 | Survey Design Effect | 报告段落 | 字段组、分组 | 目录条目 | 统计目录 |
| `survey_design_effect_table` | 调查设计效应 | Survey Design Effect | 表格 | 字段组、分组 | 目录条目 | 统计目录 |
| `survey_design_effect_text` | 调查设计效应 | Survey Design Effect | 文字解读 | 字段组、分组 | 目录条目 | 统计目录 |
| `synthetic_data_quality_audit_data` | 合成数据质量审计 | Synthetic Data Quality Audit | 结构化数据 | 全数据集 | 目录条目 | 统计目录 |
| `synthetic_data_quality_audit_table` | 合成数据质量审计 | Synthetic Data Quality Audit | 表格 | 全数据集 | 目录条目 | 统计目录 |
| `synthetic_data_quality_audit_text` | 合成数据质量审计 | Synthetic Data Quality Audit | 文字解读 | 全数据集 | 目录条目 | 统计目录 |
| `trimmed_mean_data` | 截尾均值 | Trimmed Mean | 结构化数据 | 数值字段 | 可运行 | 统计目录 |
| `trimmed_mean_table` | 截尾均值 | Trimmed Mean | 表格 | 数值字段 | 可运行 | 统计目录 |
| `trimmed_mean_text` | 截尾均值 | Trimmed Mean | 文字解读 | 数值字段 | 可运行 | 统计目录 |
| `uniqueness_constraint_check_data` | 唯一性约束检查 | Uniqueness Constraint Check | 结构化数据 | 字段组 | 目录条目 | 统计目录 |
| `uniqueness_constraint_check_table` | 唯一性约束检查 | Uniqueness Constraint Check | 表格 | 字段组 | 目录条目 | 统计目录 |
| `uniqueness_constraint_check_text` | 唯一性约束检查 | Uniqueness Constraint Check | 文字解读 | 字段组 | 目录条目 | 统计目录 |
| `winsorization_strategy_data` | 缩尾处理策略 | Winsorization Strategy | 结构化数据 | 数值字段 | 目录条目 | 统计目录 |
| `winsorization_strategy_table` | 缩尾处理策略 | Winsorization Strategy | 表格 | 数值字段 | 目录条目 | 统计目录 |
| `winsorization_strategy_text` | 缩尾处理策略 | Winsorization Strategy | 文字解读 | 数值字段 | 目录条目 | 统计目录 |
| `winsorized_summary_data` | 缩尾统计摘要 | Winsorized Summary | 结构化数据 | 数值字段 | 可运行 | 统计目录 |
| `winsorized_summary_table` | 缩尾统计摘要 | Winsorized Summary | 表格 | 数值字段 | 可运行 | 统计目录 |
| `winsorized_summary_text` | 缩尾统计摘要 | Winsorized Summary | 文字解读 | 数值字段 | 可运行 | 统计目录 |
| `yeo_johnson_transformation_data` | Yeo-Johnson 变换 | Yeo-Johnson Transformation | 结构化数据 | 数值字段 | 目录条目 | 统计目录 |
| `yeo_johnson_transformation_table` | Yeo-Johnson 变换 | Yeo-Johnson Transformation | 表格 | 数值字段 | 目录条目 | 统计目录 |
| `yeo_johnson_transformation_text` | Yeo-Johnson 变换 | Yeo-Johnson Transformation | 文字解读 | 数值字段 | 目录条目 | 统计目录 |

### 分析方法（注册族：`时间序列`；198 张；可运行 30 张）

| 卡片 ID | 中文方法名称 | 原始英文概念 | 中文输出形式 | 字段角色 | 状态 | 来源 |
| --- | --- | --- | --- | --- | --- | --- |
| `adf_test_chart` | 扩展迪基-富勒平稳性检验 | Augmented Dickey-Fuller Test | 图表 | time、数值字段 | 可运行 | 统计目录 |
| `adf_test_data` | 扩展迪基-富勒平稳性检验 | Augmented Dickey-Fuller Test | 结构化数据 | time、数值字段 | 可运行 | 统计目录 |
| `adf_test_image_spec` | 扩展迪基-富勒平稳性检验 | Augmented Dickey-Fuller Test | 图片规格 | time、数值字段 | 可运行 | 统计目录 |
| `adf_test_report_section` | 扩展迪基-富勒平稳性检验 | Augmented Dickey-Fuller Test | 报告段落 | time、数值字段 | 可运行 | 统计目录 |
| `adf_test_table` | 扩展迪基-富勒平稳性检验 | Augmented Dickey-Fuller Test | 表格 | time、数值字段 | 可运行 | 统计目录 |
| `adf_test_text` | 扩展迪基-富勒平稳性检验 | Augmented Dickey-Fuller Test | 文字解读 | time、数值字段 | 可运行 | 统计目录 |
| `alert_threshold_backtest_chart` | 告警阈值回测 | Alert Threshold Backtest | 图表 | time、数值字段 | 目录条目 | 统计目录 |
| `alert_threshold_backtest_data` | 告警阈值回测 | Alert Threshold Backtest | 结构化数据 | time、数值字段 | 目录条目 | 统计目录 |
| `alert_threshold_backtest_image_spec` | 告警阈值回测 | Alert Threshold Backtest | 图片规格 | time、数值字段 | 目录条目 | 统计目录 |
| `alert_threshold_backtest_report_section` | 告警阈值回测 | Alert Threshold Backtest | 报告段落 | time、数值字段 | 目录条目 | 统计目录 |
| `alert_threshold_backtest_table` | 告警阈值回测 | Alert Threshold Backtest | 表格 | time、数值字段 | 目录条目 | 统计目录 |
| `alert_threshold_backtest_text` | 告警阈值回测 | Alert Threshold Backtest | 文字解读 | time、数值字段 | 目录条目 | 统计目录 |
| `arima_chart` | 自回归积分滑动平均模型 | ARIMA | 图表 | time、数值字段 | 目录条目 | 统计目录 |
| `arima_data` | 自回归积分滑动平均模型 | ARIMA | 结构化数据 | time、数值字段 | 目录条目 | 统计目录 |
| `arima_image_spec` | 自回归积分滑动平均模型 | ARIMA | 图片规格 | time、数值字段 | 目录条目 | 统计目录 |
| `arima_report_section` | 自回归积分滑动平均模型 | ARIMA | 报告段落 | time、数值字段 | 目录条目 | 统计目录 |
| `arima_table` | 自回归积分滑动平均模型 | ARIMA | 表格 | time、数值字段 | 目录条目 | 统计目录 |
| `arima_text` | 自回归积分滑动平均模型 | ARIMA | 文字解读 | time、数值字段 | 目录条目 | 统计目录 |
| `autocorrelation_chart` | 自相关分析 | Autocorrelation Analysis | 图表 | time、数值字段 | 可运行 | 统计目录 |
| `autocorrelation_data` | 自相关分析 | Autocorrelation Analysis | 结构化数据 | time、数值字段 | 可运行 | 统计目录 |
| `autocorrelation_image_spec` | 自相关分析 | Autocorrelation Analysis | 图片规格 | time、数值字段 | 可运行 | 统计目录 |
| `autocorrelation_report_section` | 自相关分析 | Autocorrelation Analysis | 报告段落 | time、数值字段 | 可运行 | 统计目录 |
| `autocorrelation_table` | 自相关分析 | Autocorrelation Analysis | 表格 | time、数值字段 | 可运行 | 统计目录 |
| `autocorrelation_text` | 自相关分析 | Autocorrelation Analysis | 文字解读 | time、数值字段 | 可运行 | 统计目录 |
| `control_chart_rule_set_chart` | 控制图规则集 | Control Chart Rule Set | 图表 | time、数值字段 | 目录条目 | 统计目录 |
| `control_chart_rule_set_data` | 控制图规则集 | Control Chart Rule Set | 结构化数据 | time、数值字段 | 目录条目 | 统计目录 |
| `control_chart_rule_set_image_spec` | 控制图规则集 | Control Chart Rule Set | 图片规格 | time、数值字段 | 目录条目 | 统计目录 |
| `control_chart_rule_set_report_section` | 控制图规则集 | Control Chart Rule Set | 报告段落 | time、数值字段 | 目录条目 | 统计目录 |
| `control_chart_rule_set_table` | 控制图规则集 | Control Chart Rule Set | 表格 | time、数值字段 | 目录条目 | 统计目录 |
| `control_chart_rule_set_text` | 控制图规则集 | Control Chart Rule Set | 文字解读 | time、数值字段 | 目录条目 | 统计目录 |
| `cross_correlation_lag_chart` | 交叉相关滞后分析 | Cross-correlation Lag Analysis | 图表 | time、数值字段、数值字段 | 目录条目 | 统计目录 |
| `cross_correlation_lag_data` | 交叉相关滞后分析 | Cross-correlation Lag Analysis | 结构化数据 | time、数值字段、数值字段 | 目录条目 | 统计目录 |
| `cross_correlation_lag_image_spec` | 交叉相关滞后分析 | Cross-correlation Lag Analysis | 图片规格 | time、数值字段、数值字段 | 目录条目 | 统计目录 |
| `cross_correlation_lag_report_section` | 交叉相关滞后分析 | Cross-correlation Lag Analysis | 报告段落 | time、数值字段、数值字段 | 目录条目 | 统计目录 |
| `cross_correlation_lag_table` | 交叉相关滞后分析 | Cross-correlation Lag Analysis | 表格 | time、数值字段、数值字段 | 目录条目 | 统计目录 |
| `cross_correlation_lag_text` | 交叉相关滞后分析 | Cross-correlation Lag Analysis | 文字解读 | time、数值字段、数值字段 | 目录条目 | 统计目录 |
| `dynamic_regression_chart` | 动态回归 | Dynamic Regression | 图表 | time、数值字段、features | 目录条目 | 统计目录 |
| `dynamic_regression_data` | 动态回归 | Dynamic Regression | 结构化数据 | time、数值字段、features | 目录条目 | 统计目录 |
| `dynamic_regression_image_spec` | 动态回归 | Dynamic Regression | 图片规格 | time、数值字段、features | 目录条目 | 统计目录 |
| `dynamic_regression_report_section` | 动态回归 | Dynamic Regression | 报告段落 | time、数值字段、features | 目录条目 | 统计目录 |
| `dynamic_regression_table` | 动态回归 | Dynamic Regression | 表格 | time、数值字段、features | 目录条目 | 统计目录 |
| `dynamic_regression_text` | 动态回归 | Dynamic Regression | 文字解读 | time、数值字段、features | 目录条目 | 统计目录 |
| `forecast_backtesting_chart` | 预测回测 | Forecast Backtesting | 图表 | time、数值字段 | 目录条目 | 统计目录 |
| `forecast_backtesting_data` | 预测回测 | Forecast Backtesting | 结构化数据 | time、数值字段 | 目录条目 | 统计目录 |
| `forecast_backtesting_image_spec` | 预测回测 | Forecast Backtesting | 图片规格 | time、数值字段 | 目录条目 | 统计目录 |
| `forecast_backtesting_report_section` | 预测回测 | Forecast Backtesting | 报告段落 | time、数值字段 | 目录条目 | 统计目录 |
| `forecast_backtesting_table` | 预测回测 | Forecast Backtesting | 表格 | time、数值字段 | 目录条目 | 统计目录 |
| `forecast_backtesting_text` | 预测回测 | Forecast Backtesting | 文字解读 | time、数值字段 | 目录条目 | 统计目录 |
| `forecast_residual_diagnostics_chart` | 预测残差诊断 | Forecast Residual Diagnostics | 图表 | time、数值字段 | 目录条目 | 统计目录 |
| `forecast_residual_diagnostics_data` | 预测残差诊断 | Forecast Residual Diagnostics | 结构化数据 | time、数值字段 | 目录条目 | 统计目录 |
| `forecast_residual_diagnostics_image_spec` | 预测残差诊断 | Forecast Residual Diagnostics | 图片规格 | time、数值字段 | 目录条目 | 统计目录 |
| `forecast_residual_diagnostics_report_section` | 预测残差诊断 | Forecast Residual Diagnostics | 报告段落 | time、数值字段 | 目录条目 | 统计目录 |
| `forecast_residual_diagnostics_table` | 预测残差诊断 | Forecast Residual Diagnostics | 表格 | time、数值字段 | 目录条目 | 统计目录 |
| `forecast_residual_diagnostics_text` | 预测残差诊断 | Forecast Residual Diagnostics | 文字解读 | time、数值字段 | 目录条目 | 统计目录 |
| `freshness_sla_monitor_chart` | 数据新鲜度服务等级监控 | Freshness SLA Monitor | 图表 | time、全数据集 | 目录条目 | 统计目录 |
| `freshness_sla_monitor_data` | 数据新鲜度服务等级监控 | Freshness SLA Monitor | 结构化数据 | time、全数据集 | 目录条目 | 统计目录 |
| `freshness_sla_monitor_image_spec` | 数据新鲜度服务等级监控 | Freshness SLA Monitor | 图片规格 | time、全数据集 | 目录条目 | 统计目录 |
| `freshness_sla_monitor_report_section` | 数据新鲜度服务等级监控 | Freshness SLA Monitor | 报告段落 | time、全数据集 | 目录条目 | 统计目录 |
| `freshness_sla_monitor_table` | 数据新鲜度服务等级监控 | Freshness SLA Monitor | 表格 | time、全数据集 | 目录条目 | 统计目录 |
| `freshness_sla_monitor_text` | 数据新鲜度服务等级监控 | Freshness SLA Monitor | 文字解读 | time、全数据集 | 目录条目 | 统计目录 |
| `granger_causality_chart` | 格兰杰因果检验 | Granger Causality Test | 图表 | time、数值字段、数值字段 | 目录条目 | 统计目录 |
| `granger_causality_data` | 格兰杰因果检验 | Granger Causality Test | 结构化数据 | time、数值字段、数值字段 | 目录条目 | 统计目录 |
| `granger_causality_image_spec` | 格兰杰因果检验 | Granger Causality Test | 图片规格 | time、数值字段、数值字段 | 目录条目 | 统计目录 |
| `granger_causality_report_section` | 格兰杰因果检验 | Granger Causality Test | 报告段落 | time、数值字段、数值字段 | 目录条目 | 统计目录 |
| `granger_causality_table` | 格兰杰因果检验 | Granger Causality Test | 表格 | time、数值字段、数值字段 | 目录条目 | 统计目录 |
| `granger_causality_text` | 格兰杰因果检验 | Granger Causality Test | 文字解读 | time、数值字段、数值字段 | 目录条目 | 统计目录 |
| `hidden_markov_model_chart` | 隐马尔可夫模型 | Hidden Markov Model | 图表 | time、数值字段 | 目录条目 | 统计目录 |
| `hidden_markov_model_data` | 隐马尔可夫模型 | Hidden Markov Model | 结构化数据 | time、数值字段 | 目录条目 | 统计目录 |
| `hidden_markov_model_image_spec` | 隐马尔可夫模型 | Hidden Markov Model | 图片规格 | time、数值字段 | 目录条目 | 统计目录 |
| `hidden_markov_model_report_section` | 隐马尔可夫模型 | Hidden Markov Model | 报告段落 | time、数值字段 | 目录条目 | 统计目录 |
| `hidden_markov_model_table` | 隐马尔可夫模型 | Hidden Markov Model | 表格 | time、数值字段 | 目录条目 | 统计目录 |
| `hidden_markov_model_text` | 隐马尔可夫模型 | Hidden Markov Model | 文字解读 | time、数值字段 | 目录条目 | 统计目录 |
| `holt_winters_chart` | 霍尔特-温特斯指数平滑 | Holt-Winters | 图表 | time、数值字段 | 目录条目 | 统计目录 |
| `holt_winters_data` | 霍尔特-温特斯指数平滑 | Holt-Winters | 结构化数据 | time、数值字段 | 目录条目 | 统计目录 |
| `holt_winters_image_spec` | 霍尔特-温特斯指数平滑 | Holt-Winters | 图片规格 | time、数值字段 | 目录条目 | 统计目录 |
| `holt_winters_report_section` | 霍尔特-温特斯指数平滑 | Holt-Winters | 报告段落 | time、数值字段 | 目录条目 | 统计目录 |
| `holt_winters_table` | 霍尔特-温特斯指数平滑 | Holt-Winters | 表格 | time、数值字段 | 目录条目 | 统计目录 |
| `holt_winters_text` | 霍尔特-温特斯指数平滑 | Holt-Winters | 文字解读 | time、数值字段 | 目录条目 | 统计目录 |
| `kpss_test_chart` | KPSS 平稳性检验 | KPSS Test | 图表 | time、数值字段 | 目录条目 | 统计目录 |
| `kpss_test_data` | KPSS 平稳性检验 | KPSS Test | 结构化数据 | time、数值字段 | 目录条目 | 统计目录 |
| `kpss_test_image_spec` | KPSS 平稳性检验 | KPSS Test | 图片规格 | time、数值字段 | 目录条目 | 统计目录 |
| `kpss_test_report_section` | KPSS 平稳性检验 | KPSS Test | 报告段落 | time、数值字段 | 目录条目 | 统计目录 |
| `kpss_test_table` | KPSS 平稳性检验 | KPSS Test | 表格 | time、数值字段 | 目录条目 | 统计目录 |
| `kpss_test_text` | KPSS 平稳性检验 | KPSS Test | 文字解读 | time、数值字段 | 目录条目 | 统计目录 |
| `ljung_box_chart` | 隆-博克斯白噪声检验 | Ljung-Box Test | 图表 | time、数值字段 | 可运行 | 统计目录 |
| `ljung_box_data` | 隆-博克斯白噪声检验 | Ljung-Box Test | 结构化数据 | time、数值字段 | 可运行 | 统计目录 |
| `ljung_box_image_spec` | 隆-博克斯白噪声检验 | Ljung-Box Test | 图片规格 | time、数值字段 | 可运行 | 统计目录 |
| `ljung_box_report_section` | 隆-博克斯白噪声检验 | Ljung-Box Test | 报告段落 | time、数值字段 | 可运行 | 统计目录 |
| `ljung_box_table` | 隆-博克斯白噪声检验 | Ljung-Box Test | 表格 | time、数值字段 | 可运行 | 统计目录 |
| `ljung_box_text` | 隆-博克斯白噪声检验 | Ljung-Box Test | 文字解读 | time、数值字段 | 可运行 | 统计目录 |
| `longitudinal_cohort_retention_chart` | 纵向队列留存分析 | Longitudinal Cohort Retention | 图表 | time、分类字段、数值字段 | 目录条目 | 统计目录 |
| `longitudinal_cohort_retention_data` | 纵向队列留存分析 | Longitudinal Cohort Retention | 结构化数据 | time、分类字段、数值字段 | 目录条目 | 统计目录 |
| `longitudinal_cohort_retention_image_spec` | 纵向队列留存分析 | Longitudinal Cohort Retention | 图片规格 | time、分类字段、数值字段 | 目录条目 | 统计目录 |
| `longitudinal_cohort_retention_report_section` | 纵向队列留存分析 | Longitudinal Cohort Retention | 报告段落 | time、分类字段、数值字段 | 目录条目 | 统计目录 |
| `longitudinal_cohort_retention_table` | 纵向队列留存分析 | Longitudinal Cohort Retention | 表格 | time、分类字段、数值字段 | 目录条目 | 统计目录 |
| `longitudinal_cohort_retention_text` | 纵向队列留存分析 | Longitudinal Cohort Retention | 文字解读 | time、分类字段、数值字段 | 目录条目 | 统计目录 |
| `markov_chain_analysis_chart` | 马尔可夫链分析 | Markov Chain Analysis | 图表 | time、分类字段 | 目录条目 | 统计目录 |
| `markov_chain_analysis_data` | 马尔可夫链分析 | Markov Chain Analysis | 结构化数据 | time、分类字段 | 目录条目 | 统计目录 |
| `markov_chain_analysis_image_spec` | 马尔可夫链分析 | Markov Chain Analysis | 图片规格 | time、分类字段 | 目录条目 | 统计目录 |
| `markov_chain_analysis_report_section` | 马尔可夫链分析 | Markov Chain Analysis | 报告段落 | time、分类字段 | 目录条目 | 统计目录 |
| `markov_chain_analysis_table` | 马尔可夫链分析 | Markov Chain Analysis | 表格 | time、分类字段 | 目录条目 | 统计目录 |
| `markov_chain_analysis_text` | 马尔可夫链分析 | Markov Chain Analysis | 文字解读 | time、分类字段 | 目录条目 | 统计目录 |
| `metric_anomaly_root_cause_chart` | 指标异常根因分析 | Metric Anomaly Root Cause | 图表 | time、数值字段、features | 目录条目 | 统计目录 |
| `metric_anomaly_root_cause_data` | 指标异常根因分析 | Metric Anomaly Root Cause | 结构化数据 | time、数值字段、features | 目录条目 | 统计目录 |
| `metric_anomaly_root_cause_image_spec` | 指标异常根因分析 | Metric Anomaly Root Cause | 图片规格 | time、数值字段、features | 目录条目 | 统计目录 |
| `metric_anomaly_root_cause_report_section` | 指标异常根因分析 | Metric Anomaly Root Cause | 报告段落 | time、数值字段、features | 目录条目 | 统计目录 |
| `metric_anomaly_root_cause_table` | 指标异常根因分析 | Metric Anomaly Root Cause | 表格 | time、数值字段、features | 目录条目 | 统计目录 |
| `metric_anomaly_root_cause_text` | 指标异常根因分析 | Metric Anomaly Root Cause | 文字解读 | time、数值字段、features | 目录条目 | 统计目录 |
| `metric_definition_drift_chart` | 指标定义漂移 | Metric Definition Drift | 图表 | time、数值字段 | 目录条目 | 统计目录 |
| `metric_definition_drift_data` | 指标定义漂移 | Metric Definition Drift | 结构化数据 | time、数值字段 | 目录条目 | 统计目录 |
| `metric_definition_drift_image_spec` | 指标定义漂移 | Metric Definition Drift | 图片规格 | time、数值字段 | 目录条目 | 统计目录 |
| `metric_definition_drift_report_section` | 指标定义漂移 | Metric Definition Drift | 报告段落 | time、数值字段 | 目录条目 | 统计目录 |
| `metric_definition_drift_table` | 指标定义漂移 | Metric Definition Drift | 表格 | time、数值字段 | 目录条目 | 统计目录 |
| `metric_definition_drift_text` | 指标定义漂移 | Metric Definition Drift | 文字解读 | time、数值字段 | 目录条目 | 统计目录 |
| `moving_average_chart` | 移动平均 | Moving Average | 图表 | time、数值字段 | 可运行 | 统计目录 |
| `moving_average_data` | 移动平均 | Moving Average | 结构化数据 | time、数值字段 | 可运行 | 统计目录 |
| `moving_average_image_spec` | 移动平均 | Moving Average | 图片规格 | time、数值字段 | 可运行 | 统计目录 |
| `moving_average_report_section` | 移动平均 | Moving Average | 报告段落 | time、数值字段 | 可运行 | 统计目录 |
| `moving_average_table` | 移动平均 | Moving Average | 表格 | time、数值字段 | 可运行 | 统计目录 |
| `moving_average_text` | 移动平均 | Moving Average | 文字解读 | time、数值字段 | 可运行 | 统计目录 |
| `newey_west_standard_errors_chart` | 纽维-韦斯特标准误 | Newey-West Standard Errors | 图表 | time、数值字段、features | 目录条目 | 统计目录 |
| `newey_west_standard_errors_data` | 纽维-韦斯特标准误 | Newey-West Standard Errors | 结构化数据 | time、数值字段、features | 目录条目 | 统计目录 |
| `newey_west_standard_errors_image_spec` | 纽维-韦斯特标准误 | Newey-West Standard Errors | 图片规格 | time、数值字段、features | 目录条目 | 统计目录 |
| `newey_west_standard_errors_report_section` | 纽维-韦斯特标准误 | Newey-West Standard Errors | 报告段落 | time、数值字段、features | 目录条目 | 统计目录 |
| `newey_west_standard_errors_table` | 纽维-韦斯特标准误 | Newey-West Standard Errors | 表格 | time、数值字段、features | 目录条目 | 统计目录 |
| `newey_west_standard_errors_text` | 纽维-韦斯特标准误 | Newey-West Standard Errors | 文字解读 | time、数值字段、features | 目录条目 | 统计目录 |
| `partial_autocorrelation_chart` | 偏自相关分析 | Partial Autocorrelation | 图表 | time、数值字段 | 可运行 | 统计目录 |
| `partial_autocorrelation_data` | 偏自相关分析 | Partial Autocorrelation | 结构化数据 | time、数值字段 | 可运行 | 统计目录 |
| `partial_autocorrelation_image_spec` | 偏自相关分析 | Partial Autocorrelation | 图片规格 | time、数值字段 | 可运行 | 统计目录 |
| `partial_autocorrelation_report_section` | 偏自相关分析 | Partial Autocorrelation | 报告段落 | time、数值字段 | 可运行 | 统计目录 |
| `partial_autocorrelation_table` | 偏自相关分析 | Partial Autocorrelation | 表格 | time、数值字段 | 可运行 | 统计目录 |
| `partial_autocorrelation_text` | 偏自相关分析 | Partial Autocorrelation | 文字解读 | time、数值字段 | 可运行 | 统计目录 |
| `path_sequence_mining_chart` | 路径序列挖掘 | Path Sequence Mining | 图表 | time、分类字段 | 目录条目 | 统计目录 |
| `path_sequence_mining_data` | 路径序列挖掘 | Path Sequence Mining | 结构化数据 | time、分类字段 | 目录条目 | 统计目录 |
| `path_sequence_mining_image_spec` | 路径序列挖掘 | Path Sequence Mining | 图片规格 | time、分类字段 | 目录条目 | 统计目录 |
| `path_sequence_mining_report_section` | 路径序列挖掘 | Path Sequence Mining | 报告段落 | time、分类字段 | 目录条目 | 统计目录 |
| `path_sequence_mining_table` | 路径序列挖掘 | Path Sequence Mining | 表格 | time、分类字段 | 目录条目 | 统计目录 |
| `path_sequence_mining_text` | 路径序列挖掘 | Path Sequence Mining | 文字解读 | time、分类字段 | 目录条目 | 统计目录 |
| `prophet_style_trend_chart` | Prophet 风格趋势模型 | Prophet-style Trend Model | 图表 | time、数值字段 | 目录条目 | 统计目录 |
| `prophet_style_trend_data` | Prophet 风格趋势模型 | Prophet-style Trend Model | 结构化数据 | time、数值字段 | 目录条目 | 统计目录 |
| `prophet_style_trend_image_spec` | Prophet 风格趋势模型 | Prophet-style Trend Model | 图片规格 | time、数值字段 | 目录条目 | 统计目录 |
| `prophet_style_trend_report_section` | Prophet 风格趋势模型 | Prophet-style Trend Model | 报告段落 | time、数值字段 | 目录条目 | 统计目录 |
| `prophet_style_trend_table` | Prophet 风格趋势模型 | Prophet-style Trend Model | 表格 | time、数值字段 | 目录条目 | 统计目录 |
| `prophet_style_trend_text` | Prophet 风格趋势模型 | Prophet-style Trend Model | 文字解读 | time、数值字段 | 目录条目 | 统计目录 |
| `quantile_forecast_chart` | 分位数预测 | Quantile Forecast | 图表 | time、数值字段 | 目录条目 | 统计目录 |
| `quantile_forecast_data` | 分位数预测 | Quantile Forecast | 结构化数据 | time、数值字段 | 目录条目 | 统计目录 |
| `quantile_forecast_image_spec` | 分位数预测 | Quantile Forecast | 图片规格 | time、数值字段 | 目录条目 | 统计目录 |
| `quantile_forecast_report_section` | 分位数预测 | Quantile Forecast | 报告段落 | time、数值字段 | 目录条目 | 统计目录 |
| `quantile_forecast_table` | 分位数预测 | Quantile Forecast | 表格 | time、数值字段 | 目录条目 | 统计目录 |
| `quantile_forecast_text` | 分位数预测 | Quantile Forecast | 文字解读 | time、数值字段 | 目录条目 | 统计目录 |
| `rolling_correlation_chart` | 滚动相关分析 | Rolling Correlation | 图表 | time、数值字段、数值字段 | 目录条目 | 统计目录 |
| `rolling_correlation_data` | 滚动相关分析 | Rolling Correlation | 结构化数据 | time、数值字段、数值字段 | 目录条目 | 统计目录 |
| `rolling_correlation_image_spec` | 滚动相关分析 | Rolling Correlation | 图片规格 | time、数值字段、数值字段 | 目录条目 | 统计目录 |
| `rolling_correlation_report_section` | 滚动相关分析 | Rolling Correlation | 报告段落 | time、数值字段、数值字段 | 目录条目 | 统计目录 |
| `rolling_correlation_table` | 滚动相关分析 | Rolling Correlation | 表格 | time、数值字段、数值字段 | 目录条目 | 统计目录 |
| `rolling_correlation_text` | 滚动相关分析 | Rolling Correlation | 文字解读 | time、数值字段、数值字段 | 目录条目 | 统计目录 |
| `sarima_chart` | 季节性自回归积分滑动平均模型 | SARIMA | 图表 | time、数值字段 | 目录条目 | 统计目录 |
| `sarima_data` | 季节性自回归积分滑动平均模型 | SARIMA | 结构化数据 | time、数值字段 | 目录条目 | 统计目录 |
| `sarima_image_spec` | 季节性自回归积分滑动平均模型 | SARIMA | 图片规格 | time、数值字段 | 目录条目 | 统计目录 |
| `sarima_report_section` | 季节性自回归积分滑动平均模型 | SARIMA | 报告段落 | time、数值字段 | 目录条目 | 统计目录 |
| `sarima_table` | 季节性自回归积分滑动平均模型 | SARIMA | 表格 | time、数值字段 | 目录条目 | 统计目录 |
| `sarima_text` | 季节性自回归积分滑动平均模型 | SARIMA | 文字解读 | time、数值字段 | 目录条目 | 统计目录 |
| `seasonal_baseline_anomaly_chart` | 季节性基线异常检测 | Seasonal Baseline Anomaly | 图表 | time、数值字段 | 目录条目 | 统计目录 |
| `seasonal_baseline_anomaly_data` | 季节性基线异常检测 | Seasonal Baseline Anomaly | 结构化数据 | time、数值字段 | 目录条目 | 统计目录 |
| `seasonal_baseline_anomaly_image_spec` | 季节性基线异常检测 | Seasonal Baseline Anomaly | 图片规格 | time、数值字段 | 目录条目 | 统计目录 |
| `seasonal_baseline_anomaly_report_section` | 季节性基线异常检测 | Seasonal Baseline Anomaly | 报告段落 | time、数值字段 | 目录条目 | 统计目录 |
| `seasonal_baseline_anomaly_table` | 季节性基线异常检测 | Seasonal Baseline Anomaly | 表格 | time、数值字段 | 目录条目 | 统计目录 |
| `seasonal_baseline_anomaly_text` | 季节性基线异常检测 | Seasonal Baseline Anomaly | 文字解读 | time、数值字段 | 目录条目 | 统计目录 |
| `seasonal_decomposition_chart` | 季节性分解 | Seasonal Decomposition | 图表 | time、数值字段 | 目录条目 | 统计目录 |
| `seasonal_decomposition_data` | 季节性分解 | Seasonal Decomposition | 结构化数据 | time、数值字段 | 目录条目 | 统计目录 |
| `seasonal_decomposition_image_spec` | 季节性分解 | Seasonal Decomposition | 图片规格 | time、数值字段 | 目录条目 | 统计目录 |
| `seasonal_decomposition_report_section` | 季节性分解 | Seasonal Decomposition | 报告段落 | time、数值字段 | 目录条目 | 统计目录 |
| `seasonal_decomposition_table` | 季节性分解 | Seasonal Decomposition | 表格 | time、数值字段 | 目录条目 | 统计目录 |
| `seasonal_decomposition_text` | 季节性分解 | Seasonal Decomposition | 文字解读 | time、数值字段 | 目录条目 | 统计目录 |
| `spatiotemporal_cluster_detection_chart` | 时空聚类检测 | Spatiotemporal Cluster Detection | 图表 | time、对象级、数值字段 | 目录条目 | 统计目录 |
| `spatiotemporal_cluster_detection_data` | 时空聚类检测 | Spatiotemporal Cluster Detection | 结构化数据 | time、对象级、数值字段 | 目录条目 | 统计目录 |
| `spatiotemporal_cluster_detection_image_spec` | 时空聚类检测 | Spatiotemporal Cluster Detection | 图片规格 | time、对象级、数值字段 | 目录条目 | 统计目录 |
| `spatiotemporal_cluster_detection_report_section` | 时空聚类检测 | Spatiotemporal Cluster Detection | 报告段落 | time、对象级、数值字段 | 目录条目 | 统计目录 |
| `spatiotemporal_cluster_detection_table` | 时空聚类检测 | Spatiotemporal Cluster Detection | 表格 | time、对象级、数值字段 | 目录条目 | 统计目录 |
| `spatiotemporal_cluster_detection_text` | 时空聚类检测 | Spatiotemporal Cluster Detection | 文字解读 | time、对象级、数值字段 | 目录条目 | 统计目录 |
| `state_transition_matrix_chart` | 状态转移矩阵 | State Transition Matrix | 图表 | time、分类字段 | 目录条目 | 统计目录 |
| `state_transition_matrix_data` | 状态转移矩阵 | State Transition Matrix | 结构化数据 | time、分类字段 | 目录条目 | 统计目录 |
| `state_transition_matrix_image_spec` | 状态转移矩阵 | State Transition Matrix | 图片规格 | time、分类字段 | 目录条目 | 统计目录 |
| `state_transition_matrix_report_section` | 状态转移矩阵 | State Transition Matrix | 报告段落 | time、分类字段 | 目录条目 | 统计目录 |
| `state_transition_matrix_table` | 状态转移矩阵 | State Transition Matrix | 表格 | time、分类字段 | 目录条目 | 统计目录 |
| `state_transition_matrix_text` | 状态转移矩阵 | State Transition Matrix | 文字解读 | time、分类字段 | 目录条目 | 统计目录 |
| `stl_decomposition_chart` | STL 季节趋势分解 | STL Decomposition | 图表 | time、数值字段 | 目录条目 | 统计目录 |
| `stl_decomposition_data` | STL 季节趋势分解 | STL Decomposition | 结构化数据 | time、数值字段 | 目录条目 | 统计目录 |
| `stl_decomposition_image_spec` | STL 季节趋势分解 | STL Decomposition | 图片规格 | time、数值字段 | 目录条目 | 统计目录 |
| `stl_decomposition_report_section` | STL 季节趋势分解 | STL Decomposition | 报告段落 | time、数值字段 | 目录条目 | 统计目录 |
| `stl_decomposition_table` | STL 季节趋势分解 | STL Decomposition | 表格 | time、数值字段 | 目录条目 | 统计目录 |
| `stl_decomposition_text` | STL 季节趋势分解 | STL Decomposition | 文字解读 | time、数值字段 | 目录条目 | 统计目录 |
| `time_series_calendar` | 时间序列・时间・序列・日历 | 日历 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `time_series_change_point` | 时间序列・时间・序列 | 拐点 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `time_series_forecast` | 时间序列・时间・序列・预测 | 预测 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `time_series_lag` | 时间序列・时间・序列・滞后 | 滞后 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `time_series_seasonality` | 时间序列・时间・序列・季节性 | 季节性 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `time_series_trend` | 时间序列・时间・序列・趋势 | 趋势 | 图表 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |

### 分析方法（注册族：`机器学习`；120 张；可运行 9 张）

| 卡片 ID | 中文方法名称 | 原始英文概念 | 中文输出形式 | 字段角色 | 状态 | 来源 |
| --- | --- | --- | --- | --- | --- | --- |
| `anomaly_detection_isolation_forest_data` | 孤立森林异常检测 | Isolation Forest Anomaly Detection | 结构化数据 | 字段组 | 目录条目 | 统计目录 |
| `anomaly_detection_isolation_forest_table` | 孤立森林异常检测 | Isolation Forest Anomaly Detection | 表格 | 字段组 | 目录条目 | 统计目录 |
| `anomaly_detection_isolation_forest_text` | 孤立森林异常检测 | Isolation Forest Anomaly Detection | 文字解读 | 字段组 | 目录条目 | 统计目录 |
| `anomaly_detection_local_outlier_factor_data` | 局部离群因子异常检测 | Local Outlier Factor | 结构化数据 | 字段组 | 目录条目 | 统计目录 |
| `anomaly_detection_local_outlier_factor_table` | 局部离群因子异常检测 | Local Outlier Factor | 表格 | 字段组 | 目录条目 | 统计目录 |
| `anomaly_detection_local_outlier_factor_text` | 局部离群因子异常检测 | Local Outlier Factor | 文字解读 | 字段组 | 目录条目 | 统计目录 |
| `champion_challenger_evaluation_data` | 冠军-挑战者模型评估 | Champion / Challenger Evaluation | 结构化数据 | target、features | 目录条目 | 统计目录 |
| `champion_challenger_evaluation_table` | 冠军-挑战者模型评估 | Champion / Challenger Evaluation | 表格 | target、features | 目录条目 | 统计目录 |
| `champion_challenger_evaluation_text` | 冠军-挑战者模型评估 | Champion / Challenger Evaluation | 文字解读 | target、features | 目录条目 | 统计目录 |
| `concept_drift_detection_data` | 概念漂移检测 | Concept Drift Detection | 结构化数据 | target、features、时间窗口 | 目录条目 | 统计目录 |
| `concept_drift_detection_table` | 概念漂移检测 | Concept Drift Detection | 表格 | target、features、时间窗口 | 目录条目 | 统计目录 |
| `concept_drift_detection_text` | 概念漂移检测 | Concept Drift Detection | 文字解读 | target、features、时间窗口 | 目录条目 | 统计目录 |
| `conformal_prediction_data` | 保序预测 | Conformal Prediction | 结构化数据 | target、features | 目录条目 | 统计目录 |
| `conformal_prediction_table` | 保序预测 | Conformal Prediction | 表格 | target、features | 目录条目 | 统计目录 |
| `conformal_prediction_text` | 保序预测 | Conformal Prediction | 文字解读 | target、features | 目录条目 | 统计目录 |
| `confusion_matrix_review_chart` | 混淆矩阵评审 | Confusion Matrix Review | 图表 | binary、features | 目录条目 | 统计目录 |
| `confusion_matrix_review_data` | 混淆矩阵评审 | Confusion Matrix Review | 结构化数据 | binary、features | 目录条目 | 统计目录 |
| `confusion_matrix_review_image_spec` | 混淆矩阵评审 | Confusion Matrix Review | 图片规格 | binary、features | 目录条目 | 统计目录 |
| `confusion_matrix_review_report_section` | 混淆矩阵评审 | Confusion Matrix Review | 报告段落 | binary、features | 目录条目 | 统计目录 |
| `confusion_matrix_review_table` | 混淆矩阵评审 | Confusion Matrix Review | 表格 | binary、features | 目录条目 | 统计目录 |
| `confusion_matrix_review_text` | 混淆矩阵评审 | Confusion Matrix Review | 文字解读 | binary、features | 目录条目 | 统计目录 |
| `cost_sensitive_evaluation_data` | 成本敏感评估 | Cost-sensitive Evaluation | 结构化数据 | target、features | 目录条目 | 统计目录 |
| `cost_sensitive_evaluation_table` | 成本敏感评估 | Cost-sensitive Evaluation | 表格 | target、features | 目录条目 | 统计目录 |
| `cost_sensitive_evaluation_text` | 成本敏感评估 | Cost-sensitive Evaluation | 文字解读 | target、features | 目录条目 | 统计目录 |
| `cross_validation_data` | 交叉验证 | Cross-validation | 结构化数据 | target、features | 目录条目 | 统计目录 |
| `cross_validation_table` | 交叉验证 | Cross-validation | 表格 | target、features | 目录条目 | 统计目录 |
| `cross_validation_text` | 交叉验证 | Cross-validation | 文字解读 | target、features | 目录条目 | 统计目录 |
| `data_drift_dashboard_data` | 数据漂移仪表盘 | Data Drift Dashboard | 结构化数据 | 字段组、时间窗口 | 目录条目 | 统计目录 |
| `data_drift_dashboard_table` | 数据漂移仪表盘 | Data Drift Dashboard | 表格 | 字段组、时间窗口 | 目录条目 | 统计目录 |
| `data_drift_dashboard_text` | 数据漂移仪表盘 | Data Drift Dashboard | 文字解读 | 字段组、时间窗口 | 目录条目 | 统计目录 |
| `data_leakage_audit_data` | 数据泄漏审计 | Data Leakage Audit | 结构化数据 | target、features | 目录条目 | 统计目录 |
| `data_leakage_audit_table` | 数据泄漏审计 | Data Leakage Audit | 表格 | target、features | 目录条目 | 统计目录 |
| `data_leakage_audit_text` | 数据泄漏审计 | Data Leakage Audit | 文字解读 | target、features | 目录条目 | 统计目录 |
| `deep_learning_data` | 深度学习网络 | Deep Learning Network | 结构化数据 | numeric or binary、multi numeric | 可运行 | 统计目录 |
| `deep_learning_table` | 深度学习网络 | Deep Learning Network | 表格 | numeric or binary、multi numeric | 可运行 | 统计目录 |
| `deep_learning_text` | 深度学习网络 | Deep Learning Network | 文字解读 | numeric or binary、multi numeric | 可运行 | 统计目录 |
| `fairness_proxy_variable_audit_data` | 公平性代理变量审计 | Fairness Proxy Variable Audit | 结构化数据 | target、features、分组 | 目录条目 | 统计目录 |
| `fairness_proxy_variable_audit_table` | 公平性代理变量审计 | Fairness Proxy Variable Audit | 表格 | target、features、分组 | 目录条目 | 统计目录 |
| `fairness_proxy_variable_audit_text` | 公平性代理变量审计 | Fairness Proxy Variable Audit | 文字解读 | target、features、分组 | 目录条目 | 统计目录 |
| `fairness_slice_audit_data` | 公平性切片审计 | Fairness Slice Audit | 结构化数据 | target、features、分组 | 目录条目 | 统计目录 |
| `fairness_slice_audit_table` | 公平性切片审计 | Fairness Slice Audit | 表格 | target、features、分组 | 目录条目 | 统计目录 |
| `fairness_slice_audit_text` | 公平性切片审计 | Fairness Slice Audit | 文字解读 | target、features、分组 | 目录条目 | 统计目录 |
| `feature_privacy_risk_rank_data` | 特征隐私风险排序 | Feature Privacy Risk Rank | 结构化数据 | features | 目录条目 | 统计目录 |
| `feature_privacy_risk_rank_table` | 特征隐私风险排序 | Feature Privacy Risk Rank | 表格 | features | 目录条目 | 统计目录 |
| `feature_privacy_risk_rank_text` | 特征隐私风险排序 | Feature Privacy Risk Rank | 文字解读 | features | 目录条目 | 统计目录 |
| `graph_anomaly_detection_data` | 图异常检测 | Graph Anomaly Detection | 结构化数据 | 对象级 | 目录条目 | 统计目录 |
| `graph_anomaly_detection_table` | 图异常检测 | Graph Anomaly Detection | 表格 | 对象级 | 目录条目 | 统计目录 |
| `graph_anomaly_detection_text` | 图异常检测 | Graph Anomaly Detection | 文字解读 | 对象级 | 目录条目 | 统计目录 |
| `learning_curve_chart` | 学习曲线分析 | Learning Curve | 图表 | target、features | 目录条目 | 统计目录 |
| `learning_curve_data` | 学习曲线分析 | Learning Curve | 结构化数据 | target、features | 目录条目 | 统计目录 |
| `learning_curve_image_spec` | 学习曲线分析 | Learning Curve | 图片规格 | target、features | 目录条目 | 统计目录 |
| `learning_curve_report_section` | 学习曲线分析 | Learning Curve | 报告段落 | target、features | 目录条目 | 统计目录 |
| `learning_curve_table` | 学习曲线分析 | Learning Curve | 表格 | target、features | 目录条目 | 统计目录 |
| `learning_curve_text` | 学习曲线分析 | Learning Curve | 文字解读 | target、features | 目录条目 | 统计目录 |
| `link_prediction_baseline_data` | 链接预测基线 | Link Prediction Baseline | 结构化数据 | 对象级 | 目录条目 | 统计目录 |
| `link_prediction_baseline_table` | 链接预测基线 | Link Prediction Baseline | 表格 | 对象级 | 目录条目 | 统计目录 |
| `link_prediction_baseline_text` | 链接预测基线 | Link Prediction Baseline | 文字解读 | 对象级 | 目录条目 | 统计目录 |
| `machine_learning_boosting` | 机器学习・机器・提升模型 | 提升模型 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `machine_learning_forest` | 机器学习・机器・随机森林 | 随机森林 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `machine_learning_importance` | 机器学习・机器・重要性 | 重要性 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `machine_learning_neighbors` | 机器学习・机器・近邻 | 近邻 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `machine_learning_neural` | 机器学习・机器・神经网络 | 神经网络 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `machine_learning_tree` | 机器学习・机器・决策树 | 决策树 | 文字解读 | 单字段、字段对、字段组、分组、时间窗口、对象级、全数据集、派生指标 | 规划条目 | 自动分析规格目录 |
| `model_calibration_data` | 模型校准 | Model Calibration | 结构化数据 | binary、features | 目录条目 | 统计目录 |
| `model_calibration_table` | 模型校准 | Model Calibration | 表格 | binary、features | 目录条目 | 统计目录 |
| `model_calibration_text` | 模型校准 | Model Calibration | 文字解读 | binary、features | 目录条目 | 统计目录 |
| `model_card_documentation_data` | 模型卡文档 | Model Card Documentation | 结构化数据 | target、features | 目录条目 | 统计目录 |
| `model_card_documentation_table` | 模型卡文档 | Model Card Documentation | 表格 | target、features | 目录条目 | 统计目录 |
| `model_card_documentation_text` | 模型卡文档 | Model Card Documentation | 文字解读 | target、features | 目录条目 | 统计目录 |
| `model_performance_monitor_data` | 模型性能监控 | Model Performance Monitor | 结构化数据 | target、features、时间窗口 | 目录条目 | 统计目录 |
| `model_performance_monitor_table` | 模型性能监控 | Model Performance Monitor | 表格 | target、features、时间窗口 | 目录条目 | 统计目录 |
| `model_performance_monitor_text` | 模型性能监控 | Model Performance Monitor | 文字解读 | target、features、时间窗口 | 目录条目 | 统计目录 |
| `model_retraining_trigger_data` | 模型再训练触发器 | Model Retraining Trigger | 结构化数据 | target、features、时间窗口 | 目录条目 | 统计目录 |
| `model_retraining_trigger_table` | 模型再训练触发器 | Model Retraining Trigger | 表格 | target、features、时间窗口 | 目录条目 | 统计目录 |
| `model_retraining_trigger_text` | 模型再训练触发器 | Model Retraining Trigger | 文字解读 | target、features、时间窗口 | 目录条目 | 统计目录 |
| `nested_cross_validation_data` | 嵌套交叉验证 | Nested Cross-validation | 结构化数据 | target、features | 目录条目 | 统计目录 |
| `nested_cross_validation_table` | 嵌套交叉验证 | Nested Cross-validation | 表格 | target、features | 目录条目 | 统计目录 |
| `nested_cross_validation_text` | 嵌套交叉验证 | Nested Cross-validation | 文字解读 | target、features | 目录条目 | 统计目录 |
| `neural_network_data` | 神经网络 | Neural Network | 结构化数据 | numeric or binary、multi numeric | 可运行 | 统计目录 |
| `neural_network_table` | 神经网络 | Neural Network | 表格 | numeric or binary、multi numeric | 可运行 | 统计目录 |
| `neural_network_text` | 神经网络 | Neural Network | 文字解读 | numeric or binary、multi numeric | 可运行 | 统计目录 |
| `one_hot_encoding_plan_data` | 独热编码规划 | One-hot Encoding Plan | 结构化数据 | features | 目录条目 | 统计目录 |
| `one_hot_encoding_plan_table` | 独热编码规划 | One-hot Encoding Plan | 表格 | features | 目录条目 | 统计目录 |
| `one_hot_encoding_plan_text` | 独热编码规划 | One-hot Encoding Plan | 文字解读 | features | 目录条目 | 统计目录 |
| `online_offline_metric_gap_data` | 线上线下指标差距分析 | Online / Offline Metric Gap | 结构化数据 | target、features、时间窗口 | 目录条目 | 统计目录 |
| `online_offline_metric_gap_table` | 线上线下指标差距分析 | Online / Offline Metric Gap | 表格 | target、features、时间窗口 | 目录条目 | 统计目录 |
| `online_offline_metric_gap_text` | 线上线下指标差距分析 | Online / Offline Metric Gap | 文字解读 | target、features、时间窗口 | 目录条目 | 统计目录 |
| `permutation_importance_review_data` | 置换重要性评审 | Permutation Importance Review | 结构化数据 | target、features | 目录条目 | 统计目录 |
| `permutation_importance_review_table` | 置换重要性评审 | Permutation Importance Review | 表格 | target、features | 目录条目 | 统计目录 |
| `permutation_importance_review_text` | 置换重要性评审 | Permutation Importance Review | 文字解读 | target、features | 目录条目 | 统计目录 |
| `population_stability_index_data` | 总体稳定性指数 | Population Stability Index | 结构化数据 | 字段组、时间窗口 | 目录条目 | 统计目录 |
| `population_stability_index_table` | 总体稳定性指数 | Population Stability Index | 表格 | 字段组、时间窗口 | 目录条目 | 统计目录 |
| `population_stability_index_text` | 总体稳定性指数 | Population Stability Index | 文字解读 | 字段组、时间窗口 | 目录条目 | 统计目录 |
| `precision_recall_analysis_data` | 精确率-召回率分析 | Precision / Recall Analysis | 结构化数据 | binary、features | 目录条目 | 统计目录 |
| `precision_recall_analysis_table` | 精确率-召回率分析 | Precision / Recall Analysis | 表格 | binary、features | 目录条目 | 统计目录 |
| `precision_recall_analysis_text` | 精确率-召回率分析 | Precision / Recall Analysis | 文字解读 | binary、features | 目录条目 | 统计目录 |
| `random_forest_data` | 随机森林 | Random Forest | 结构化数据 | numeric or binary、multi numeric | 可运行 | 统计目录 |
| `random_forest_table` | 随机森林 | Random Forest | 表格 | numeric or binary、multi numeric | 可运行 | 统计目录 |
| `random_forest_text` | 随机森林 | Random Forest | 文字解读 | numeric or binary、multi numeric | 可运行 | 统计目录 |
| `roc_auc_analysis_data` | ROC-AUC 分析 | ROC AUC Analysis | 结构化数据 | binary、features | 目录条目 | 统计目录 |
| `roc_auc_analysis_table` | ROC-AUC 分析 | ROC AUC Analysis | 表格 | binary、features | 目录条目 | 统计目录 |
| `roc_auc_analysis_text` | ROC-AUC 分析 | ROC AUC Analysis | 文字解读 | binary、features | 目录条目 | 统计目录 |
| `sentiment_classifier_audit_data` | 情感分类器审计 | Sentiment Classifier Audit | 结构化数据 | target、features | 目录条目 | 统计目录 |
| `sentiment_classifier_audit_table` | 情感分类器审计 | Sentiment Classifier Audit | 表格 | target、features | 目录条目 | 统计目录 |
| `sentiment_classifier_audit_text` | 情感分类器审计 | Sentiment Classifier Audit | 文字解读 | target、features | 目录条目 | 统计目录 |
| `shap_explanation_data` | SHAP 模型解释 | SHAP Explanation | 结构化数据 | target、features | 目录条目 | 统计目录 |
| `shap_explanation_table` | SHAP 模型解释 | SHAP Explanation | 表格 | target、features | 目录条目 | 统计目录 |
| `shap_explanation_text` | SHAP 模型解释 | SHAP Explanation | 文字解读 | target、features | 目录条目 | 统计目录 |
| `target_encoding_audit_data` | 目标编码审计 | Target Encoding Audit | 结构化数据 | target、features | 目录条目 | 统计目录 |
| `target_encoding_audit_table` | 目标编码审计 | Target Encoding Audit | 表格 | target、features | 目录条目 | 统计目录 |
| `target_encoding_audit_text` | 目标编码审计 | Target Encoding Audit | 文字解读 | target、features | 目录条目 | 统计目录 |
| `text_label_quality_audit_data` | 文本标注质量审计 | Text Label Quality Audit | 结构化数据 | target、features | 目录条目 | 统计目录 |
| `text_label_quality_audit_table` | 文本标注质量审计 | Text Label Quality Audit | 表格 | target、features | 目录条目 | 统计目录 |
| `text_label_quality_audit_text` | 文本标注质量审计 | Text Label Quality Audit | 文字解读 | target、features | 目录条目 | 统计目录 |
| `threshold_optimization_data` | 决策阈值优化 | Decision Threshold Optimization | 结构化数据 | binary、features | 目录条目 | 统计目录 |
| `threshold_optimization_table` | 决策阈值优化 | Decision Threshold Optimization | 表格 | binary、features | 目录条目 | 统计目录 |
| `threshold_optimization_text` | 决策阈值优化 | Decision Threshold Optimization | 文字解读 | binary、features | 目录条目 | 统计目录 |
| `train_test_split_audit_data` | 训练集与测试集切分审计 | Train / Test Split Audit | 结构化数据 | target、features | 目录条目 | 统计目录 |
| `train_test_split_audit_table` | 训练集与测试集切分审计 | Train / Test Split Audit | 表格 | target、features | 目录条目 | 统计目录 |
| `train_test_split_audit_text` | 训练集与测试集切分审计 | Train / Test Split Audit | 文字解读 | target、features | 目录条目 | 统计目录 |

### 分析方法（注册族：`生存分析`；78 张；可运行 0 张）

| 卡片 ID | 中文方法名称 | 原始英文概念 | 中文输出形式 | 字段角色 | 状态 | 来源 |
| --- | --- | --- | --- | --- | --- | --- |
| `accelerated_failure_time_chart` | 加速失效时间模型 | Accelerated Failure Time Model | 图表 | time to event、features | 目录条目 | 统计目录 |
| `accelerated_failure_time_data` | 加速失效时间模型 | Accelerated Failure Time Model | 结构化数据 | time to event、features | 目录条目 | 统计目录 |
| `accelerated_failure_time_image_spec` | 加速失效时间模型 | Accelerated Failure Time Model | 图片规格 | time to event、features | 目录条目 | 统计目录 |
| `accelerated_failure_time_report_section` | 加速失效时间模型 | Accelerated Failure Time Model | 报告段落 | time to event、features | 目录条目 | 统计目录 |
| `accelerated_failure_time_table` | 加速失效时间模型 | Accelerated Failure Time Model | 表格 | time to event、features | 目录条目 | 统计目录 |
| `accelerated_failure_time_text` | 加速失效时间模型 | Accelerated Failure Time Model | 文字解读 | time to event、features | 目录条目 | 统计目录 |
| `competing_event_retention_chart` | 竞争事件留存分析 | Competing Event Retention | 图表 | time to event、event type | 目录条目 | 统计目录 |
| `competing_event_retention_data` | 竞争事件留存分析 | Competing Event Retention | 结构化数据 | time to event、event type | 目录条目 | 统计目录 |
| `competing_event_retention_image_spec` | 竞争事件留存分析 | Competing Event Retention | 图片规格 | time to event、event type | 目录条目 | 统计目录 |
| `competing_event_retention_report_section` | 竞争事件留存分析 | Competing Event Retention | 报告段落 | time to event、event type | 目录条目 | 统计目录 |
| `competing_event_retention_table` | 竞争事件留存分析 | Competing Event Retention | 表格 | time to event、event type | 目录条目 | 统计目录 |
| `competing_event_retention_text` | 竞争事件留存分析 | Competing Event Retention | 文字解读 | time to event、event type | 目录条目 | 统计目录 |
| `competing_risks_chart` | 竞争风险模型 | Competing Risks Model | 图表 | time to event、event type | 目录条目 | 统计目录 |
| `competing_risks_data` | 竞争风险模型 | Competing Risks Model | 结构化数据 | time to event、event type | 目录条目 | 统计目录 |
| `competing_risks_image_spec` | 竞争风险模型 | Competing Risks Model | 图片规格 | time to event、event type | 目录条目 | 统计目录 |
| `competing_risks_report_section` | 竞争风险模型 | Competing Risks Model | 报告段落 | time to event、event type | 目录条目 | 统计目录 |
| `competing_risks_table` | 竞争风险模型 | Competing Risks Model | 表格 | time to event、event type | 目录条目 | 统计目录 |
| `competing_risks_text` | 竞争风险模型 | Competing Risks Model | 文字解读 | time to event、event type | 目录条目 | 统计目录 |
| `cox_ph_chart` | Cox 比例风险模型 | Cox Proportional Hazards | 图表 | time to event、features | 目录条目 | 统计目录 |
| `cox_ph_data` | Cox 比例风险模型 | Cox Proportional Hazards | 结构化数据 | time to event、features | 目录条目 | 统计目录 |
| `cox_ph_image_spec` | Cox 比例风险模型 | Cox Proportional Hazards | 图片规格 | time to event、features | 目录条目 | 统计目录 |
| `cox_ph_report_section` | Cox 比例风险模型 | Cox Proportional Hazards | 报告段落 | time to event、features | 目录条目 | 统计目录 |
| `cox_ph_table` | Cox 比例风险模型 | Cox Proportional Hazards | 表格 | time to event、features | 目录条目 | 统计目录 |
| `cox_ph_text` | Cox 比例风险模型 | Cox Proportional Hazards | 文字解读 | time to event、features | 目录条目 | 统计目录 |
| `cumulative_incidence_curve_chart` | 累积发生率曲线 | Cumulative Incidence Curve | 图表 | time to event、event type | 目录条目 | 统计目录 |
| `cumulative_incidence_curve_data` | 累积发生率曲线 | Cumulative Incidence Curve | 结构化数据 | time to event、event type | 目录条目 | 统计目录 |
| `cumulative_incidence_curve_image_spec` | 累积发生率曲线 | Cumulative Incidence Curve | 图片规格 | time to event、event type | 目录条目 | 统计目录 |
| `cumulative_incidence_curve_report_section` | 累积发生率曲线 | Cumulative Incidence Curve | 报告段落 | time to event、event type | 目录条目 | 统计目录 |
| `cumulative_incidence_curve_table` | 累积发生率曲线 | Cumulative Incidence Curve | 表格 | time to event、event type | 目录条目 | 统计目录 |
| `cumulative_incidence_curve_text` | 累积发生率曲线 | Cumulative Incidence Curve | 文字解读 | time to event、event type | 目录条目 | 统计目录 |
| `kaplan_meier_chart` | 卡普兰-迈耶生存估计 | Kaplan-Meier Estimator | 图表 | time to event | 目录条目 | 统计目录 |
| `kaplan_meier_data` | 卡普兰-迈耶生存估计 | Kaplan-Meier Estimator | 结构化数据 | time to event | 目录条目 | 统计目录 |
| `kaplan_meier_image_spec` | 卡普兰-迈耶生存估计 | Kaplan-Meier Estimator | 图片规格 | time to event | 目录条目 | 统计目录 |
| `kaplan_meier_report_section` | 卡普兰-迈耶生存估计 | Kaplan-Meier Estimator | 报告段落 | time to event | 目录条目 | 统计目录 |
| `kaplan_meier_table` | 卡普兰-迈耶生存估计 | Kaplan-Meier Estimator | 表格 | time to event | 目录条目 | 统计目录 |
| `kaplan_meier_text` | 卡普兰-迈耶生存估计 | Kaplan-Meier Estimator | 文字解读 | time to event | 目录条目 | 统计目录 |
| `log_rank_test_chart` | 对数秩生存曲线检验 | Log-rank Test | 图表 | time to event、group | 目录条目 | 统计目录 |
| `log_rank_test_data` | 对数秩生存曲线检验 | Log-rank Test | 结构化数据 | time to event、group | 目录条目 | 统计目录 |
| `log_rank_test_image_spec` | 对数秩生存曲线检验 | Log-rank Test | 图片规格 | time to event、group | 目录条目 | 统计目录 |
| `log_rank_test_report_section` | 对数秩生存曲线检验 | Log-rank Test | 报告段落 | time to event、group | 目录条目 | 统计目录 |
| `log_rank_test_table` | 对数秩生存曲线检验 | Log-rank Test | 表格 | time to event、group | 目录条目 | 统计目录 |
| `log_rank_test_text` | 对数秩生存曲线检验 | Log-rank Test | 文字解读 | time to event、group | 目录条目 | 统计目录 |
| `multi_state_survival_model_chart` | 多状态生存模型 | Multi-state Survival Model | 图表 | time to event、event type | 目录条目 | 统计目录 |
| `multi_state_survival_model_data` | 多状态生存模型 | Multi-state Survival Model | 结构化数据 | time to event、event type | 目录条目 | 统计目录 |
| `multi_state_survival_model_image_spec` | 多状态生存模型 | Multi-state Survival Model | 图片规格 | time to event、event type | 目录条目 | 统计目录 |
| `multi_state_survival_model_report_section` | 多状态生存模型 | Multi-state Survival Model | 报告段落 | time to event、event type | 目录条目 | 统计目录 |
| `multi_state_survival_model_table` | 多状态生存模型 | Multi-state Survival Model | 表格 | time to event、event type | 目录条目 | 统计目录 |
| `multi_state_survival_model_text` | 多状态生存模型 | Multi-state Survival Model | 文字解读 | time to event、event type | 目录条目 | 统计目录 |
| `nelson_aalen_chart` | 纳尔逊-阿伦累积风险估计 | Nelson-Aalen Estimator | 图表 | time to event | 目录条目 | 统计目录 |
| `nelson_aalen_data` | 纳尔逊-阿伦累积风险估计 | Nelson-Aalen Estimator | 结构化数据 | time to event | 目录条目 | 统计目录 |
| `nelson_aalen_image_spec` | 纳尔逊-阿伦累积风险估计 | Nelson-Aalen Estimator | 图片规格 | time to event | 目录条目 | 统计目录 |
| `nelson_aalen_report_section` | 纳尔逊-阿伦累积风险估计 | Nelson-Aalen Estimator | 报告段落 | time to event | 目录条目 | 统计目录 |
| `nelson_aalen_table` | 纳尔逊-阿伦累积风险估计 | Nelson-Aalen Estimator | 表格 | time to event | 目录条目 | 统计目录 |
| `nelson_aalen_text` | 纳尔逊-阿伦累积风险估计 | Nelson-Aalen Estimator | 文字解读 | time to event | 目录条目 | 统计目录 |
| `proportional_hazards_check_chart` | 比例风险假设检验 | Proportional Hazards Check | 图表 | time to event、features | 目录条目 | 统计目录 |
| `proportional_hazards_check_data` | 比例风险假设检验 | Proportional Hazards Check | 结构化数据 | time to event、features | 目录条目 | 统计目录 |
| `proportional_hazards_check_image_spec` | 比例风险假设检验 | Proportional Hazards Check | 图片规格 | time to event、features | 目录条目 | 统计目录 |
| `proportional_hazards_check_report_section` | 比例风险假设检验 | Proportional Hazards Check | 报告段落 | time to event、features | 目录条目 | 统计目录 |
| `proportional_hazards_check_table` | 比例风险假设检验 | Proportional Hazards Check | 表格 | time to event、features | 目录条目 | 统计目录 |
| `proportional_hazards_check_text` | 比例风险假设检验 | Proportional Hazards Check | 文字解读 | time to event、features | 目录条目 | 统计目录 |
| `survival_censoring_audit_chart` | 生存删失审计 | Survival Censoring Audit | 图表 | time to event、group | 目录条目 | 统计目录 |
| `survival_censoring_audit_data` | 生存删失审计 | Survival Censoring Audit | 结构化数据 | time to event、group | 目录条目 | 统计目录 |
| `survival_censoring_audit_image_spec` | 生存删失审计 | Survival Censoring Audit | 图片规格 | time to event、group | 目录条目 | 统计目录 |
| `survival_censoring_audit_report_section` | 生存删失审计 | Survival Censoring Audit | 报告段落 | time to event、group | 目录条目 | 统计目录 |
| `survival_censoring_audit_table` | 生存删失审计 | Survival Censoring Audit | 表格 | time to event、group | 目录条目 | 统计目录 |
| `survival_censoring_audit_text` | 生存删失审计 | Survival Censoring Audit | 文字解读 | time to event、group | 目录条目 | 统计目录 |
| `survival_retention_model_chart` | 生存留存模型 | Survival Retention Model | 图表 | time to event、features | 目录条目 | 统计目录 |
| `survival_retention_model_data` | 生存留存模型 | Survival Retention Model | 结构化数据 | time to event、features | 目录条目 | 统计目录 |
| `survival_retention_model_image_spec` | 生存留存模型 | Survival Retention Model | 图片规格 | time to event、features | 目录条目 | 统计目录 |
| `survival_retention_model_report_section` | 生存留存模型 | Survival Retention Model | 报告段落 | time to event、features | 目录条目 | 统计目录 |
| `survival_retention_model_table` | 生存留存模型 | Survival Retention Model | 表格 | time to event、features | 目录条目 | 统计目录 |
| `survival_retention_model_text` | 生存留存模型 | Survival Retention Model | 文字解读 | time to event、features | 目录条目 | 统计目录 |
| `time_dependent_covariates_chart` | 时变协变量 | Time-dependent Covariates | 图表 | time to event、features | 目录条目 | 统计目录 |
| `time_dependent_covariates_data` | 时变协变量 | Time-dependent Covariates | 结构化数据 | time to event、features | 目录条目 | 统计目录 |
| `time_dependent_covariates_image_spec` | 时变协变量 | Time-dependent Covariates | 图片规格 | time to event、features | 目录条目 | 统计目录 |
| `time_dependent_covariates_report_section` | 时变协变量 | Time-dependent Covariates | 报告段落 | time to event、features | 目录条目 | 统计目录 |
| `time_dependent_covariates_table` | 时变协变量 | Time-dependent Covariates | 表格 | time to event、features | 目录条目 | 统计目录 |
| `time_dependent_covariates_text` | 时变协变量 | Time-dependent Covariates | 文字解读 | time to event、features | 目录条目 | 统计目录 |

### 分析方法（注册族：`统计方法`；54 张；可运行 0 张）

| 卡片 ID | 中文方法名称 | 原始英文概念 | 中文输出形式 | 字段角色 | 状态 | 来源 |
| --- | --- | --- | --- | --- | --- | --- |
| `analysis_lineage_map_data` | 分析血缘图谱 | Analysis Lineage Map | 结构化数据 | 全数据集 | 目录条目 | 统计目录 |
| `analysis_lineage_map_table` | 分析血缘图谱 | Analysis Lineage Map | 表格 | 全数据集 | 目录条目 | 统计目录 |
| `analysis_lineage_map_text` | 分析血缘图谱 | Analysis Lineage Map | 文字解读 | 全数据集 | 目录条目 | 统计目录 |
| `bayes_factor_model_comparison_data` | 贝叶斯因子模型比较 | Bayes Factor Model Comparison | 结构化数据 | target、features | 目录条目 | 统计目录 |
| `bayes_factor_model_comparison_table` | 贝叶斯因子模型比较 | Bayes Factor Model Comparison | 表格 | target、features | 目录条目 | 统计目录 |
| `bayes_factor_model_comparison_text` | 贝叶斯因子模型比较 | Bayes Factor Model Comparison | 文字解读 | target、features | 目录条目 | 统计目录 |
| `bayesian_credible_effect_data` | 贝叶斯可信效应 | Bayesian Credible Effect | 结构化数据 | target、features | 目录条目 | 统计目录 |
| `bayesian_credible_effect_table` | 贝叶斯可信效应 | Bayesian Credible Effect | 表格 | target、features | 目录条目 | 统计目录 |
| `bayesian_credible_effect_text` | 贝叶斯可信效应 | Bayesian Credible Effect | 文字解读 | target、features | 目录条目 | 统计目录 |
| `bayesian_interval_summary_data` | 贝叶斯区间摘要 | Bayesian Interval Summary | 结构化数据 | 数值字段 | 目录条目 | 统计目录 |
| `bayesian_interval_summary_table` | 贝叶斯区间摘要 | Bayesian Interval Summary | 表格 | 数值字段 | 目录条目 | 统计目录 |
| `bayesian_interval_summary_text` | 贝叶斯区间摘要 | Bayesian Interval Summary | 文字解读 | 数值字段 | 目录条目 | 统计目录 |
| `bayesian_posterior_predictive_check_data` | 贝叶斯后验预测检验 | Bayesian Posterior Predictive Check | 结构化数据 | target、features | 目录条目 | 统计目录 |
| `bayesian_posterior_predictive_check_table` | 贝叶斯后验预测检验 | Bayesian Posterior Predictive Check | 表格 | target、features | 目录条目 | 统计目录 |
| `bayesian_posterior_predictive_check_text` | 贝叶斯后验预测检验 | Bayesian Posterior Predictive Check | 文字解读 | target、features | 目录条目 | 统计目录 |
| `bayesian_prior_predictive_check_data` | 贝叶斯先验预测检验 | Bayesian Prior Predictive Check | 结构化数据 | target、features | 目录条目 | 统计目录 |
| `bayesian_prior_predictive_check_table` | 贝叶斯先验预测检验 | Bayesian Prior Predictive Check | 表格 | target、features | 目录条目 | 统计目录 |
| `bayesian_prior_predictive_check_text` | 贝叶斯先验预测检验 | Bayesian Prior Predictive Check | 文字解读 | target、features | 目录条目 | 统计目录 |
| `confidence_interval_summary_data` | 置信区间摘要 | Confidence Interval Summary | 结构化数据 | 数值字段 | 目录条目 | 统计目录 |
| `confidence_interval_summary_table` | 置信区间摘要 | Confidence Interval Summary | 表格 | 数值字段 | 目录条目 | 统计目录 |
| `confidence_interval_summary_text` | 置信区间摘要 | Confidence Interval Summary | 文字解读 | 数值字段 | 目录条目 | 统计目录 |
| `differential_privacy_budget_data` | 差分隐私预算 | Differential Privacy Budget | 结构化数据 | 全数据集 | 目录条目 | 统计目录 |
| `differential_privacy_budget_table` | 差分隐私预算 | Differential Privacy Budget | 表格 | 全数据集 | 目录条目 | 统计目录 |
| `differential_privacy_budget_text` | 差分隐私预算 | Differential Privacy Budget | 文字解读 | 全数据集 | 目录条目 | 统计目录 |
| `empirical_bayes_shrinkage_data` | 经验贝叶斯收缩 | Empirical Bayes Shrinkage | 结构化数据 | 数值字段、分组 | 目录条目 | 统计目录 |
| `empirical_bayes_shrinkage_table` | 经验贝叶斯收缩 | Empirical Bayes Shrinkage | 表格 | 数值字段、分组 | 目录条目 | 统计目录 |
| `empirical_bayes_shrinkage_text` | 经验贝叶斯收缩 | Empirical Bayes Shrinkage | 文字解读 | 数值字段、分组 | 目录条目 | 统计目录 |
| `false_discovery_rate_data` | 错误发现率控制 | False Discovery Rate Control | 结构化数据 | 字段组 | 目录条目 | 统计目录 |
| `false_discovery_rate_table` | 错误发现率控制 | False Discovery Rate Control | 表格 | 字段组 | 目录条目 | 统计目录 |
| `false_discovery_rate_text` | 错误发现率控制 | False Discovery Rate Control | 文字解读 | 字段组 | 目录条目 | 统计目录 |
| `finite_population_correction_data` | 有限总体校正 | Finite Population Correction | 结构化数据 | 数值字段 | 目录条目 | 统计目录 |
| `finite_population_correction_table` | 有限总体校正 | Finite Population Correction | 表格 | 数值字段 | 目录条目 | 统计目录 |
| `finite_population_correction_text` | 有限总体校正 | Finite Population Correction | 文字解读 | 数值字段 | 目录条目 | 统计目录 |
| `margin_of_error_data` | 误差范围 | Margin of Error | 结构化数据 | 数值字段 | 目录条目 | 统计目录 |
| `margin_of_error_table` | 误差范围 | Margin of Error | 表格 | 数值字段 | 目录条目 | 统计目录 |
| `margin_of_error_text` | 误差范围 | Margin of Error | 文字解读 | 数值字段 | 目录条目 | 统计目录 |
| `multiple_testing_correction_data` | 多重检验校正 | Multiple Testing Correction | 结构化数据 | 字段组 | 目录条目 | 统计目录 |
| `multiple_testing_correction_table` | 多重检验校正 | Multiple Testing Correction | 表格 | 字段组 | 目录条目 | 统计目录 |
| `multiple_testing_correction_text` | 多重检验校正 | Multiple Testing Correction | 文字解读 | 字段组 | 目录条目 | 统计目录 |
| `ratio_metric_delta_method_data` | 比率指标 Delta 法 | Ratio Metric Delta Method | 结构化数据 | 字段对 | 目录条目 | 统计目录 |
| `ratio_metric_delta_method_table` | 比率指标 Delta 法 | Ratio Metric Delta Method | 表格 | 字段对 | 目录条目 | 统计目录 |
| `ratio_metric_delta_method_text` | 比率指标 Delta 法 | Ratio Metric Delta Method | 文字解读 | 字段对 | 目录条目 | 统计目录 |
| `reproducibility_audit_data` | 可复现性审计 | Reproducibility Audit | 结构化数据 | 全数据集 | 目录条目 | 统计目录 |
| `reproducibility_audit_table` | 可复现性审计 | Reproducibility Audit | 表格 | 全数据集 | 目录条目 | 统计目录 |
| `reproducibility_audit_text` | 可复现性审计 | Reproducibility Audit | 文字解读 | 全数据集 | 目录条目 | 统计目录 |
| `robustness_grid_data` | 稳健性网格分析 | Robustness Grid | 结构化数据 | 字段组 | 目录条目 | 统计目录 |
| `robustness_grid_table` | 稳健性网格分析 | Robustness Grid | 表格 | 字段组 | 目录条目 | 统计目录 |
| `robustness_grid_text` | 稳健性网格分析 | Robustness Grid | 文字解读 | 字段组 | 目录条目 | 统计目录 |
| `sensitivity_to_missing_data_data` | 缺失数据敏感性分析 | Sensitivity to Missing Data | 结构化数据 | 字段组 | 目录条目 | 统计目录 |
| `sensitivity_to_missing_data_table` | 缺失数据敏感性分析 | Sensitivity to Missing Data | 表格 | 字段组 | 目录条目 | 统计目录 |
| `sensitivity_to_missing_data_text` | 缺失数据敏感性分析 | Sensitivity to Missing Data | 文字解读 | 字段组 | 目录条目 | 统计目录 |
| `sensitivity_to_outliers_data` | 异常值敏感性分析 | Sensitivity to Outliers | 结构化数据 | 字段组 | 目录条目 | 统计目录 |
| `sensitivity_to_outliers_table` | 异常值敏感性分析 | Sensitivity to Outliers | 表格 | 字段组 | 目录条目 | 统计目录 |
| `sensitivity_to_outliers_text` | 异常值敏感性分析 | Sensitivity to Outliers | 文字解读 | 字段组 | 目录条目 | 统计目录 |

### 分析方法（注册族：`非参数检验`；42 张；可运行 36 张）

| 卡片 ID | 中文方法名称 | 原始英文概念 | 中文输出形式 | 字段角色 | 状态 | 来源 |
| --- | --- | --- | --- | --- | --- | --- |
| `bootstrap_ci_data` | 自助法置信区间 | Bootstrap CI | 结构化数据 | 数值字段 | 可运行 | 统计目录 |
| `bootstrap_ci_table` | 自助法置信区间 | Bootstrap CI | 表格 | 数值字段 | 可运行 | 统计目录 |
| `bootstrap_ci_text` | 自助法置信区间 | Bootstrap CI | 文字解读 | 数值字段 | 可运行 | 统计目录 |
| `cliffs_delta_effect_size_data` | 克利夫 Delta 效应量 | Cliff's Delta Effect Size | 结构化数据 | 数值字段、binary group | 目录条目 | 统计目录 |
| `cliffs_delta_effect_size_table` | 克利夫 Delta 效应量 | Cliff's Delta Effect Size | 表格 | 数值字段、binary group | 目录条目 | 统计目录 |
| `cliffs_delta_effect_size_text` | 克利夫 Delta 效应量 | Cliff's Delta Effect Size | 文字解读 | 数值字段、binary group | 目录条目 | 统计目录 |
| `fligner_killeen_data` | 弗林纳-基林方差齐性检验 | Fligner-Killeen Test | 结构化数据 | 数值字段、分类字段 | 可运行 | 统计目录 |
| `fligner_killeen_table` | 弗林纳-基林方差齐性检验 | Fligner-Killeen Test | 表格 | 数值字段、分类字段 | 可运行 | 统计目录 |
| `fligner_killeen_text` | 弗林纳-基林方差齐性检验 | Fligner-Killeen Test | 文字解读 | 数值字段、分类字段 | 可运行 | 统计目录 |
| `friedman_data` | 弗里德曼检验 | Friedman Test | 结构化数据 | 数值字段、within subject factor | 可运行 | 统计目录 |
| `friedman_table` | 弗里德曼检验 | Friedman Test | 表格 | 数值字段、within subject factor | 可运行 | 统计目录 |
| `friedman_text` | 弗里德曼检验 | Friedman Test | 文字解读 | 数值字段、within subject factor | 可运行 | 统计目录 |
| `kruskal_data` | 克鲁斯卡尔-沃利斯检验 | Kruskal-Wallis Test | 结构化数据 | 数值字段、分类字段 | 可运行 | 统计目录 |
| `kruskal_table` | 克鲁斯卡尔-沃利斯检验 | Kruskal-Wallis Test | 表格 | 数值字段、分类字段 | 可运行 | 统计目录 |
| `kruskal_text` | 克鲁斯卡尔-沃利斯检验 | Kruskal-Wallis Test | 文字解读 | 数值字段、分类字段 | 可运行 | 统计目录 |
| `ks_two_sample_data` | 双样本柯尔莫哥洛夫-斯米尔诺夫检验 | Two-sample KS Test | 结构化数据 | 数值字段、binary group | 可运行 | 统计目录 |
| `ks_two_sample_table` | 双样本柯尔莫哥洛夫-斯米尔诺夫检验 | Two-sample KS Test | 表格 | 数值字段、binary group | 可运行 | 统计目录 |
| `ks_two_sample_text` | 双样本柯尔莫哥洛夫-斯米尔诺夫检验 | Two-sample KS Test | 文字解读 | 数值字段、binary group | 可运行 | 统计目录 |
| `mann_whitney_data` | 曼-惠特尼 U 检验 | Mann-Whitney U Test | 结构化数据 | 数值字段、binary group | 可运行 | 统计目录 |
| `mann_whitney_table` | 曼-惠特尼 U 检验 | Mann-Whitney U Test | 表格 | 数值字段、binary group | 可运行 | 统计目录 |
| `mann_whitney_text` | 曼-惠特尼 U 检验 | Mann-Whitney U Test | 文字解读 | 数值字段、binary group | 可运行 | 统计目录 |
| `median_test_data` | 中位数检验 | Median Test | 结构化数据 | 数值字段、分类字段 | 可运行 | 统计目录 |
| `median_test_table` | 中位数检验 | Median Test | 表格 | 数值字段、分类字段 | 可运行 | 统计目录 |
| `median_test_text` | 中位数检验 | Median Test | 文字解读 | 数值字段、分类字段 | 可运行 | 统计目录 |
| `mood_median_data` | 穆德中位数检验 | Mood Median Test | 结构化数据 | 数值字段、分类字段 | 可运行 | 统计目录 |
| `mood_median_table` | 穆德中位数检验 | Mood Median Test | 表格 | 数值字段、分类字段 | 可运行 | 统计目录 |
| `mood_median_text` | 穆德中位数检验 | Mood Median Test | 文字解读 | 数值字段、分类字段 | 可运行 | 统计目录 |
| `permutation_test_data` | 置换检验 | Permutation Test | 结构化数据 | 数值字段、分类字段 | 可运行 | 统计目录 |
| `permutation_test_table` | 置换检验 | Permutation Test | 表格 | 数值字段、分类字段 | 可运行 | 统计目录 |
| `permutation_test_text` | 置换检验 | Permutation Test | 文字解读 | 数值字段、分类字段 | 可运行 | 统计目录 |
| `rank_biserial_correlation_data` | 秩二列相关系数 | Rank-biserial Correlation | 结构化数据 | 数值字段、binary group | 目录条目 | 统计目录 |
| `rank_biserial_correlation_table` | 秩二列相关系数 | Rank-biserial Correlation | 表格 | 数值字段、binary group | 目录条目 | 统计目录 |
| `rank_biserial_correlation_text` | 秩二列相关系数 | Rank-biserial Correlation | 文字解读 | 数值字段、binary group | 目录条目 | 统计目录 |
| `runs_test_data` | 游程检验 | Runs Test | 结构化数据 | ordered | 可运行 | 统计目录 |
| `runs_test_table` | 游程检验 | Runs Test | 表格 | ordered | 可运行 | 统计目录 |
| `runs_test_text` | 游程检验 | Runs Test | 文字解读 | ordered | 可运行 | 统计目录 |
| `sign_test_data` | 符号检验 | Sign Test | 结构化数据 | 数值字段、paired | 可运行 | 统计目录 |
| `sign_test_table` | 符号检验 | Sign Test | 表格 | 数值字段、paired | 可运行 | 统计目录 |
| `sign_test_text` | 符号检验 | Sign Test | 文字解读 | 数值字段、paired | 可运行 | 统计目录 |
| `wilcoxon_signed_rank_data` | 威尔科克森符号秩检验 | Wilcoxon Signed-rank Test | 结构化数据 | 数值字段、paired | 可运行 | 统计目录 |
| `wilcoxon_signed_rank_table` | 威尔科克森符号秩检验 | Wilcoxon Signed-rank Test | 表格 | 数值字段、paired | 可运行 | 统计目录 |
| `wilcoxon_signed_rank_text` | 威尔科克森符号秩检验 | Wilcoxon Signed-rank Test | 文字解读 | 数值字段、paired | 可运行 | 统计目录 |

### 分析方法（注册族：`面板因果`；48 张；可运行 0 张）

| 卡片 ID | 中文方法名称 | 原始英文概念 | 中文输出形式 | 字段角色 | 状态 | 来源 |
| --- | --- | --- | --- | --- | --- | --- |
| `bayesian_hierarchical_model_data` | 贝叶斯层级模型 | Bayesian Hierarchical Model | 结构化数据 | grouped numeric | 目录条目 | 统计目录 |
| `bayesian_hierarchical_model_table` | 贝叶斯层级模型 | Bayesian Hierarchical Model | 表格 | grouped numeric | 目录条目 | 统计目录 |
| `bayesian_hierarchical_model_text` | 贝叶斯层级模型 | Bayesian Hierarchical Model | 文字解读 | grouped numeric | 目录条目 | 统计目录 |
| `did_data` | 双重差分法 | Difference-in-Differences | 结构化数据 | time、group、数值字段 | 目录条目 | 统计目录 |
| `did_table` | 双重差分法 | Difference-in-Differences | 表格 | time、group、数值字段 | 目录条目 | 统计目录 |
| `did_text` | 双重差分法 | Difference-in-Differences | 文字解读 | time、group、数值字段 | 目录条目 | 统计目录 |
| `event_study_design_chart` | 事件研究设计 | Event Study Design | 图表 | time、group、数值字段 | 目录条目 | 统计目录 |
| `event_study_design_data` | 事件研究设计 | Event Study Design | 结构化数据 | time、group、数值字段 | 目录条目 | 统计目录 |
| `event_study_design_image_spec` | 事件研究设计 | Event Study Design | 图片规格 | time、group、数值字段 | 目录条目 | 统计目录 |
| `event_study_design_report_section` | 事件研究设计 | Event Study Design | 报告段落 | time、group、数值字段 | 目录条目 | 统计目录 |
| `event_study_design_table` | 事件研究设计 | Event Study Design | 表格 | time、group、数值字段 | 目录条目 | 统计目录 |
| `event_study_design_text` | 事件研究设计 | Event Study Design | 文字解读 | time、group、数值字段 | 目录条目 | 统计目录 |
| `gee_data` | 广义估计方程 | Generalized Estimating Equations | 结构化数据 | grouped numeric | 目录条目 | 统计目录 |
| `gee_table` | 广义估计方程 | Generalized Estimating Equations | 表格 | grouped numeric | 目录条目 | 统计目录 |
| `gee_text` | 广义估计方程 | Generalized Estimating Equations | 文字解读 | grouped numeric | 目录条目 | 统计目录 |
| `interrupted_time_series_data` | 中断时间序列分析 | Interrupted Time Series | 结构化数据 | time、数值字段 | 目录条目 | 统计目录 |
| `interrupted_time_series_table` | 中断时间序列分析 | Interrupted Time Series | 表格 | time、数值字段 | 目录条目 | 统计目录 |
| `interrupted_time_series_text` | 中断时间序列分析 | Interrupted Time Series | 文字解读 | time、数值字段 | 目录条目 | 统计目录 |
| `mixed_effects_model_data` | 混合效应模型 | Mixed Effects Model | 结构化数据 | grouped numeric | 目录条目 | 统计目录 |
| `mixed_effects_model_table` | 混合效应模型 | Mixed Effects Model | 表格 | grouped numeric | 目录条目 | 统计目录 |
| `mixed_effects_model_text` | 混合效应模型 | Mixed Effects Model | 文字解读 | grouped numeric | 目录条目 | 统计目录 |
| `mixed_effects_random_intercepts_data` | 混合效应随机截距模型 | Mixed Effects Random Intercepts | 结构化数据 | grouped numeric | 目录条目 | 统计目录 |
| `mixed_effects_random_intercepts_table` | 混合效应随机截距模型 | Mixed Effects Random Intercepts | 表格 | grouped numeric | 目录条目 | 统计目录 |
| `mixed_effects_random_intercepts_text` | 混合效应随机截距模型 | Mixed Effects Random Intercepts | 文字解读 | grouped numeric | 目录条目 | 统计目录 |
| `mixed_effects_random_slopes_data` | 混合效应随机斜率模型 | Mixed Effects Random Slopes | 结构化数据 | grouped numeric | 目录条目 | 统计目录 |
| `mixed_effects_random_slopes_table` | 混合效应随机斜率模型 | Mixed Effects Random Slopes | 表格 | grouped numeric | 目录条目 | 统计目录 |
| `mixed_effects_random_slopes_text` | 混合效应随机斜率模型 | Mixed Effects Random Slopes | 文字解读 | grouped numeric | 目录条目 | 统计目录 |
| `multilevel_poststratification_data` | 多层回归与后分层 | Multilevel Regression and Poststratification | 结构化数据 | grouped numeric | 目录条目 | 统计目录 |
| `multilevel_poststratification_table` | 多层回归与后分层 | Multilevel Regression and Poststratification | 表格 | grouped numeric | 目录条目 | 统计目录 |
| `multilevel_poststratification_text` | 多层回归与后分层 | Multilevel Regression and Poststratification | 文字解读 | grouped numeric | 目录条目 | 统计目录 |
| `panel_fixed_effects_data` | 面板固定效应模型 | Panel Fixed Effects | 结构化数据 | panel、数值字段 | 目录条目 | 统计目录 |
| `panel_fixed_effects_table` | 面板固定效应模型 | Panel Fixed Effects | 表格 | panel、数值字段 | 目录条目 | 统计目录 |
| `panel_fixed_effects_text` | 面板固定效应模型 | Panel Fixed Effects | 文字解读 | panel、数值字段 | 目录条目 | 统计目录 |
| `panel_random_effects_data` | 面板随机效应模型 | Panel Random Effects | 结构化数据 | panel、数值字段 | 目录条目 | 统计目录 |
| `panel_random_effects_table` | 面板随机效应模型 | Panel Random Effects | 表格 | panel、数值字段 | 目录条目 | 统计目录 |
| `panel_random_effects_text` | 面板随机效应模型 | Panel Random Effects | 文字解读 | panel、数值字段 | 目录条目 | 统计目录 |
| `parallel_trends_diagnostic_chart` | 平行趋势诊断 | Parallel Trends Diagnostic | 图表 | time、group、数值字段 | 目录条目 | 统计目录 |
| `parallel_trends_diagnostic_data` | 平行趋势诊断 | Parallel Trends Diagnostic | 结构化数据 | time、group、数值字段 | 目录条目 | 统计目录 |
| `parallel_trends_diagnostic_image_spec` | 平行趋势诊断 | Parallel Trends Diagnostic | 图片规格 | time、group、数值字段 | 目录条目 | 统计目录 |
| `parallel_trends_diagnostic_report_section` | 平行趋势诊断 | Parallel Trends Diagnostic | 报告段落 | time、group、数值字段 | 目录条目 | 统计目录 |
| `parallel_trends_diagnostic_table` | 平行趋势诊断 | Parallel Trends Diagnostic | 表格 | time、group、数值字段 | 目录条目 | 统计目录 |
| `parallel_trends_diagnostic_text` | 平行趋势诊断 | Parallel Trends Diagnostic | 文字解读 | time、group、数值字段 | 目录条目 | 统计目录 |
| `synthetic_control_data` | 合成控制法 | Synthetic Control | 结构化数据 | time、panel | 目录条目 | 统计目录 |
| `synthetic_control_table` | 合成控制法 | Synthetic Control | 表格 | time、panel | 目录条目 | 统计目录 |
| `synthetic_control_text` | 合成控制法 | Synthetic Control | 文字解读 | time、panel | 目录条目 | 统计目录 |
| `synthetic_difference_in_differences_data` | 合成双重差分法 | Synthetic Difference-in-Differences | 结构化数据 | time、panel | 目录条目 | 统计目录 |
| `synthetic_difference_in_differences_table` | 合成双重差分法 | Synthetic Difference-in-Differences | 表格 | time、panel | 目录条目 | 统计目录 |
| `synthetic_difference_in_differences_text` | 合成双重差分法 | Synthetic Difference-in-Differences | 文字解读 | time、panel | 目录条目 | 统计目录 |
