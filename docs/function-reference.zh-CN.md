# Asteria Analyst 功能逐项参考

> 本文提供公开仓库的细粒度功能参考，逐项说明页面、用户操作、后端职责、输入、处理、输出和使用条件。需要独立安装、显式启用或通过正式质量门禁的能力均有状态标记。

[项目首页](../README.md) | [全部可用功能目录](feature-catalog.zh-CN.md) | [模块与功能手册](module-guide.zh-CN.md) | [快速开始](getting-started.zh-CN.md) | [详细用户指南](user-guide.zh-CN.md) | [正式报告可信机制](report-integrity.zh-CN.md)

> 想按“入口、输入、动作、结果和条件”核对发布能力，可先阅读 [全部可用功能目录](feature-catalog.zh-CN.md)。本文聚焦页面操作、API 和服务职责的细粒度参考。

## 0. 阅读方式与使用状态

### 0.1 本文中的状态标记

| 标记 | 含义 | 用户应如何理解 |
| --- | --- | --- |
| 默认可用 | 随当前本地应用启动即可使用的基本能力 | 仍会受文件格式、数据质量和浏览器环境影响 |
| 条件可用 | 需要合适的数据、选择对应方法或完成局部配置 | 数据、方法和配置共同决定适配范围 |
| 正式受控 | 可进入正式管理报告流程，但必须通过强制链与质量门禁 | 发布资格由完整验证流程确定 |
| 可选配置 | 需要用户自行提供运行时、模型服务或环境变量 | 配置完成后可用；未配置时显示明确状态 |
| 实验性 | 面向本地管理员的扩展或探索能力 | 默认关闭，不作为便携版的基础承诺 |

### 0.2 页面、功能和服务模块的层级

- **页面**是用户访问的工作区，例如 `/analysis` 或 `/revision`。
- **功能**是用户能够执行的动作，例如上传数据、运行统计、创建报告任务、添加批注。
- **服务模块**是实现该动作的后端职责，例如 `DatasetService`、`AnalysisService`、`ReportAgentSessionService`。
- 一次点击可能同时经过多个服务模块。正式报告由完整链路与门禁共同判定，页面和接口按各自职责呈现阶段状态。

### 0.3 当前公开版的基本承诺

1. 默认形态是 Windows 本地单用户分析工作台，服务面向本机回环地址使用。
2. 基本流程是“导入数据 -> 检查画像 -> 选择分析或报告路径 -> 审阅证据与资产 -> 处理修订”。
3. 方法目录用于检索和路由，可执行性由当前环境、数据与参数确认。
4. 修订工作区发布本地报告版本；项目发布到 GitHub 和报告上传公网使用各自的发布流程。
5. 项目公开可见范围与软件许可分别维护；仓库当前的许可证状态见项目首页。

### 0.4 按任务快速定位

| 要完成的任务 | 优先阅读 | 主要结果 |
| --- | --- | --- |
| 导入数据、选择工作表、补充业务材料 | 第 3 节 | 数据集、画像和任务上下文 |
| 配置字段、方法和运行参数 | 第 5、6、9 节 | 字段角色、方法运行与证据资产 |
| 创建并审阅报告 | 第 7、8 节 | 任务状态、报告资产和正式 PDF 质量结果 |
| 修订已有报告 | 第 11 节 | 会话、差异、批注、附件和本地版本 |
| 启用本地运行时或扩展 | 第 12 节 | 配置状态、任务记录和运行工件 |

## 1. 页面与工作区总表

| 路由 | 页面/组件职责 | 用户可完成的主要动作 | 主要产物 | 使用条件 |
| --- | --- | --- | --- | --- |
| `/` | 首页与智能报告入口 | 选择数据、补充业务目标、进入分析或报告流程 | 数据与任务上下文 | 正式发布进入完整报告门禁 |
| `/analysis` | Smart Report Studio 正式分析工作台 | 上传/选择数据、查看画像、运行受控分析、创建报告任务、查看结果 | 统计结果、图表、报告任务、报告资产 | 正式 PDF 仍需通过强制发布链 |
| `/lab` | Analysis Lab 方法实验台 | 处理字段、定义派生指标、选方法、建方法卡、执行实验、查看 PDCA | 实验运行、证据表、图表、方法卡、资产清单 | 正式交付需经过正式发布链 |
| `/lab/method-guide` | 方法指南 | 按问题、变量和方法类别理解可选方法 | 方法说明与选择线索 | 结合业务判断与统计审阅使用 |
| `/revision` | 报告修订入口 | 浏览、搜索和选择已有报告，进入修订场景 | 已有报告与会话入口 | 报告必须先存在于本地目录 |
| `/revision/workspace` | 报告修订工作区 | 创建会话、发送修改要求、查看事件、差异、附件和批注，发布本地版本 | 修订会话、差异、附件、批注、本地发布版本 | 高级会话能力按本地运行时授权启用 |

## 2. 启动、健康检查与第一次进入

### 2.1 Windows 便携版

**入口**：下载 Release 中的 Windows 便携版，按 [快速开始](getting-started.zh-CN.md) 启动。

**启动后应看到的结果**：

1. 本地服务进程启动，浏览器打开应用页面或可访问本地地址。
2. 访问 `/health` 能得到服务健康状态。
3. 首页、`/analysis`、`/lab`、`/revision` 页面可以打开，表明 Web 应用已启动；外部运行时由各自配置状态决定。

**需要独立配置的能力**：R、外部 AI 提供方、Codex Runtime、外部 Skill、报告 Agent Team，以及公网多用户部署。相应配置完成后按运行状态启用。

### 2.2 源码版

**入口**：按 [快速开始](getting-started.zh-CN.md) 安装前后端依赖并启动本地服务。

**基础检查接口**：

| 接口 | 用途 | 何时使用 |
| --- | --- | --- |
| `GET /health` | 检查后端是否存活 | 浏览器打不开、启动脚本似乎无响应时 |
| `GET /api/manifest` | 读取前端/服务端公开运行信息 | 排查当前启动的是哪一套本地服务时 |
| `GET /api/runtime-settings` | 查看不含密钥的运行时配置状态 | 确认可选运行时是否已启用时 |

**常见判断**：可选按钮状态反映相应扩展或外部运行时的配置情况；核心数据分析流程按其独立状态运行。

## 3. 数据接入与数据目录

后端职责：`DatasetService`、`DatasetCatalogService`、`HistoricalReportService`、`BusinessBackgroundService`。

### 3.1 导入结构化数据集

**解决的问题**：将本地表格或数据文件建立为可选择、可审阅、可复用的数据集，供后续分析任务持续调用。

**入口**：首页、`/analysis`、`/lab` 中的数据选择或上传区域。

**接受的主要格式**：

| 格式 | 常见用途 | 导入后行为 |
| --- | --- | --- |
| CSV | 单表导出、业务明细、系统下载文件 | 解析列、样本、类型和缺失情况 |
| TSV | 制表符分隔数据 | 按分隔符解析为表格数据 |
| Excel `.xlsx` | 多工作表经营台账、调查表、汇总表 | 识别工作表并保留表级上下文 |
| Excel `.xls` | 旧版 Excel 文件 | 转换为 `.xlsx` 后进入分析流程 |
| Stata `.dta` | 统计研究与调查数据 | 读取为可分析的数据表 |

分析数据接收范围包含 CSV、TSV、`.xlsx` 和 `.dta`。旧版 `.xls` 转换为 `.xlsx` 后，可按相同方式上传并进行多工作表分析。

**核心操作**：

1. 选择一个本地文件。
2. 上传后，系统创建数据集记录并生成初步数据画像。
3. 如果是多工作表 Excel，选择要作为当前分析对象的工作表。
4. 检查行列数量、字段名称、类型、缺失、样本行和推荐图表。
5. 在分析、Lab 或报告任务中复用该数据集，减少相同文件的重复上传。

**直接输出**：数据集标识、文件和工作表元信息、字段摘要、样本、质量提示、当前活动工作表。

**对应接口**：

| 操作 | 接口 | 输入 | 返回或后续效果 |
| --- | --- | --- | --- |
| 列出数据集 | `GET /api/datasets` | 无 | 可选择的数据集目录 |
| 上传数据集 | `POST /api/datasets/upload` | 文件和上传元信息 | 新数据集与初步画像 |
| 读取数据集 | `GET /api/datasets/{dataset_id}` | 数据集标识 | 详情、字段和活动表信息 |
| 切换工作表 | `POST /api/datasets/{dataset_id}/sheet` | 目标工作表名称或标识 | 更新活动表并刷新表级上下文 |
| 读取工作流摘要 | `GET /api/datasets/{dataset_id}/workflow` | 数据集标识 | 数据到分析/报告的可用工作流信息 |

**前提与边界**：

- 文件读取成功后，业务口径仍需确认表头、币种、单位、时间范围、主键粒度和缺失含义。
- 大数据集的浏览器预览或图表可采用采样，以保证交互速度；后续确定性计算按方法的实际执行数据范围进行。
- 受密码保护、损坏、非结构化扫描件或复杂宏工作簿可能无法按预期解析。
- 上传数据属于本地工作区资产；公开提交前须移除真实客户数据、上传物和生成文件。
- 浏览器端负责选择文件、显示服务端返回的画像并收集用户配置；统计结论和 API 密钥管理由后端与本地环境承担。

### 3.2 多工作表与活动工作表

**解决的问题**：同一个工作簿常包含明细、维表、汇总、口径说明和多个周期。系统要求用户明确“当前分析哪一张表”，并以多表策略管理各工作表。

**用户操作**：上传 Excel 后查看工作表列表，选择活动表；必要时分别对不同表建立分析或报告策略。

**系统会做的事**：识别可读取工作表、保存表名和表级数据、刷新当前表的字段画像，并将活动表带入后续方法选择和报告编排。

**用户必须判断的事**：是否应单表分析、跨表组合，还是逐表生成子报告。系统支持 `single`、`combined`、`separate` 多表策略；共享业务主键和口径兼容性由用户确认。

### 3.3 导入历史报告

**解决的问题**：让新的分析任务能够参考旧报告的结构、结论语境或交付风格，并把旧材料纳入当前任务上下文。

**入口**：首页和分析工作区的历史材料区域。

**操作与接口**：

| 操作 | 接口 | 用途 |
| --- | --- | --- |
| 浏览历史报告 | `GET /api/historical-reports` | 选择已有历史材料 |
| 上传历史报告 | `POST /api/historical-reports/upload` | 新增本地历史报告文件 |
| 读取材料详情 | `GET /api/historical-reports/{template_id}` | 检查指定历史材料信息 |

**输出**：可关联到当前任务的历史报告记录与文件上下文。

**前端可选择的历史报告格式**：`.md`、`.txt`、`.html`、`.htm`、`.pdf`、`.docx`。文本质量、PDF 扫描状态、文档加密与文件完整性共同影响抽取和复用结果。

**使用范围**：历史报告提供上下文；当前周期结论以新数据的统计计算为依据。

### 3.4 导入业务背景材料

**解决的问题**：将业务问题、策略约束、组织背景、目标读者或专项说明纳入分析上下文。

**操作与接口**：

| 操作 | 接口 | 用途 |
| --- | --- | --- |
| 浏览业务背景 | `GET /api/business-backgrounds` | 选择已保存的背景材料 |
| 上传背景材料 | `POST /api/business-backgrounds/upload` | 新增本地背景文件 |
| 读取背景详情 | `GET /api/business-backgrounds/{context_id}` | 核对特定材料内容或元数据 |

**使用范围**：业务背景用于描述问题和路线；字段质量、口径和数据完整性由数据准备与人工审核确认。若启用外部 AI 提供方，相关上下文的发送范围由用户选定的工作流和配置决定。

**前端可选择的业务背景格式**：除常见文本、网页、PDF 和 Word 材料外，业务背景区域也可接受表格数据文件，用于提供补充语境；正式分析以选定数据集为依据。

### 3.5 数据准备完成的最低检查表

在运行统计或创建报告前，至少确认以下事项：

1. 当前工作表是否正确。
2. 一行代表什么实体或事件，是否存在重复记录。
3. 哪些字段是数值、类别、日期、标识符、分组或目标变量。
4. 缺失值、异常值、单位、币种和时间范围是否已理解。
5. 如果多表组合，连接键、粒度和汇总层级是否已确认。
6. 将业务目标写成可检验的问题，说明分析对象、目标和判断标准。

## 4. 首页与业务任务设计

前端职责：主页路由和 `HomeRouteShell` 相关工作区组件。后端支撑：数据目录、业务背景、报告策略与任务编排服务。

### 4.1 首页的用途

首页提供工作流入口，用于把“数据 + 业务问题 + 交付预期”组织为后续分析或报告任务的上下文。

### 4.2 首页可执行的典型动作

| 动作 | 用户输入 | 系统输出 | 需要用户复核的内容 |
| --- | --- | --- | --- |
| 选择或上传数据 | 数据文件、已有数据集 | 当前数据上下文与画像入口 | 表、字段、样本是否正确 |
| 补充业务目标 | 问题、范围、读者、约束 | 业务简报上下文 | 目标是否具体、可验证 |
| 关联历史材料 | 历史报告或背景文件 | 可供报告规划参考的材料 | 旧结论是否仍适用 |
| 进入正式分析 | 已准备的数据与任务 | 跳转或建立分析工作流 | 是否要先做数据质量检查 |
| 进入方法探索 | 数据与初步问题 | 跳转至 Analysis Lab | 探索结果是否需要正式复核 |

### 4.3 业务简报与交付设计

**建议填写的信息**：分析对象、时间范围、核心问题、目标读者、输出侧重点、已知限制、希望回答的决策问题。

**系统作用**：这些信息可被后续业务路线选择、报告结构设计和修订会话引用，帮助系统理解任务意图。事实证据和数值结论由数据与确定性计算提供。

**失败或不完整时的表现**：如果目标过于笼统，系统仍可能生成画像、统计或探索结果，但方法选择和报告重点会缺少约束。用户应先收窄问题，例如从“分析销售”改为“比较不同地区在指定季度的销售额、订单数和复购率，并说明异常波动”。

## 5. 数据画像、字段理解与分析路线建议

后端职责：`DatasetService`、`DatasetCatalogService`、`AutoAnalysisFieldService`、正式链中的 `DataProfileService` 与 `AIFieldSemanticMapper`。

### 5.1 数据画像

**输入**：当前数据集及活动工作表。

**系统会产出或展示**：

- 行数、列数、字段名和样本行。
- 数值、类别、日期和可能的标识字段。
- 缺失值、唯一值、基础分布与可视化建议。
- 对多工作表数据的表级指纹和可供后续选择的上下文。

**用途**：帮助用户判断数据是否能进入分析，确定候选维度、指标、分组、时间字段和目标变量。

**边界**：字段名、空值和数据类型推断是辅助信息。比如名为 `amount` 的字段可能是金额、数量或占比；名为 `date` 的字段可能是日期、文本或结算周期。必须由用户结合业务口径确认。

### 5.2 字段角色与语义映射

系统可在自动分析或正式报告流程中尝试识别字段的候选角色，例如：

| 候选角色 | 常见用途 | 用户应确认的问题 |
| --- | --- | --- |
| 标识符 | 去重、连接、多表关系 | 是否真的是唯一键，是否有脱敏或重复 |
| 时间字段 | 趋势、周期对比、时序分析 | 粒度是日、周、月还是事件时间 |
| 指标字段 | 汇总、回归、相关、KPI | 单位、币种、是否可加总 |
| 维度字段 | 分组、交叉、筛选、分层 | 类别是否稳定、是否有大量空值 |
| 目标字段 | 预测、分类、回归或实验结果 | 业务定义、观察窗口和泄漏风险 |

**自动分析字段动作**：自动分析服务可以生成字段关系、候选路线和方法建议；用户可以在 Lab 中覆盖字段角色或人工定义派生口径。

**正式报告中的特殊要求**：`AIFieldSemanticMapper` 必须在正式报告绑定前执行，并把结构化映射与可追溯工件写入流程。它负责理解和规划，不负责凭空生成数值。

### 5.3 分析路线建议

**可能的建议方向**：描述统计、分组比较、相关关系、回归模型、分类变量检验、非参数检验、聚类、时序、实验或专项业务路线。

**系统依据**：字段类型、数据规模、存在的时间或分组字段、用户目标与已选择的输出类型。

**需要人工审核的判断**：路线建议用于筛选分析方向。涉及政策、实验、价格、风险或关键经营决策时，需要有领域知识的人员审核样本选择、对照关系、混杂因素和解释范围。

## 6. 受控统计、图表、代码与证据

后端职责：`AnalysisService`、`StatisticalCatalog`、`ExecutionService`、`AutoAnalysisMethodExecutorService`、`AutoAnalysisVisualService`、`AutoAnalysisEvidenceService`。

### 6.1 方法目录与实际执行的区别

项目内置统计方法目录，用于检索、说明和路由方法。目录覆盖约 362 项统计方法和相关概念；执行条件由当前数据、依赖和运行时共同决定。

运行前系统会根据数据类型、选择的变量、方法参数和当前环境决定是否能够执行。界面显示的推荐方法也应先查看其前提条件。

### 6.2 可选的分析类别

| 类别 | 代表功能 | 常见输入 | 主要输出 | 解释边界 |
| --- | --- | --- | --- | --- |
| 描述与分布 | 描述统计、频数、分位数、截尾均值、Winsorize、基尼、帕累托 | 数值或类别字段 | 统计表、分布摘要、排序结果 | 呈现样本分布和排序；成因解释需结合业务与研究设计 |
| 分组与交叉 | 交叉表、透视表、分群 KPI | 维度、指标、分组字段 | 分组汇总、结构占比、对比表 | 必须确认分组口径与样本规模 |
| 相关与关系 | Pearson、Spearman、Kendall、偏相关、距离相关、点二列、Eta squared | 两个或多个适配字段 | 系数、显著性、关系摘要 | 呈现变量关系；因果结论需要研究设计与审阅 |
| 回归与广义模型 | OLS、岭、Lasso、Elastic Net、稳健回归、分位数回归、Logit、Poisson | 目标变量和解释变量 | 系数、拟合、诊断 | 需检查模型设定、共线性和外推风险 |
| 模型诊断 | Breusch-Pagan、White、Durbin-Watson 等 | 已拟合模型或对应字段 | 假设检验和诊断信息 | 诊断结果需结合模型目的解释 |
| 组间检验 | t 检验、配对检验、Z 检验、A/B、ANOVA、ANCOVA、Welch ANOVA、事后比较 | 数值指标、分组、配对或协变量 | 差异、区间、显著性 | 需确认独立性、正态性、方差和实验设计 |
| 分类变量检验 | 卡方、Fisher、McNemar、Cochran Q、CMH、Cramer’s V、Kappa | 类别字段或配对类别 | 列联表、关联强度、显著性 | 小样本与稀疏单元格可能限制方法 |
| 非参数与重采样 | Mann-Whitney、Wilcoxon、Kruskal-Wallis、Friedman、置换、Bootstrap | 不满足参数前提或排序数据 | 检验结果、区间、重采样摘要 | 仍需结合研究设计和多重比较 |
| 探索与预测 | PCA、K-Means、随机森林、基础神经网络 | 多指标数据、特征和目标 | 成分、分群、特征关系、预测摘要 | 用于分析与试验；生产使用需另行验证 |
| 时序与稳定性 | 移动平均、ACF/PACF、Ljung-Box、ADF | 连续时间序列 | 趋势、滞后、平稳性提示 | 需确认时间顺序、缺口和结构变更 |

### 6.3 运行一次受控统计分析

**入口**：`/analysis` 的分析区域，或由 Lab 的方法执行流程调用。

**标准步骤**：

1. 打开统计方法目录，理解要解决的问题与方法前提。
2. 选择当前数据集/工作表。
3. 指定变量、分组字段、目标字段或时间字段。
4. 填写方法需要的参数，例如显著性水平、是否配对、分类/回归目标或筛选条件。
5. 提交运行，阅读执行状态和结果表。
6. 审核结果是否与数据口径、样本限制和业务问题一致，再决定是否引用到报告。

**接口**：`GET /api/statistics/catalog` 获取目录；`POST /api/statistics/run` 提交受控分析。

**Smart Report Studio 中的直接统计选项**：前端可以为相关性、OLS 回归、随机森林、K-means 聚类、PCA 和正态性检验等请求收集目标字段、特征字段和分组字段。为了避免不合理的大型请求，前端对一次请求选择的特征字段限制为最多 8 个；这只是交互层的保护，不替代模型本身的样本量、共线性、解释性和验证要求。

**常见输出**：数值表、分组表、模型摘要、诊断信息、可视化规格、计算证据、可下载或可绑定的分析资产。

**何时应停止并回到数据准备**：变量类型明显错误、样本量不足、分组几乎为空、指标单位未知、时间排序不可靠、模型报出不可估计或结果与常识严重冲突但没有找到原因。

### 6.4 图表与代码产物

系统可以根据数据和方法生成图表建议、图表资产或对应的计算/展示产物。图表与底层统计表、计算证据共同支持趋势、构成、差异和关系的解读。

**用户复核重点**：图标题、单位、筛选条件、时间范围、轴刻度、异常值处理、分组顺序，以及图表是否只展示了样本或经过汇总的数据。

### 6.5 自动分析

**接口**：`GET /api/analysis/auto/methods` 获取候选方法；`POST /api/analysis/auto` 启动自动分析路线。

**会做什么**：结合字段类型、候选角色、用户目标和输出偏好，提出字段关系、派生指标建议、方法建议、图表、证据表、计算表和报告部件候选项。

**受控处理范围**：系统将相关性作为关系描述，业务口径由使用者确认；正式报告由 AI 强制链和确定性数值执行完成。

## 7. 智能报告、任务编排与报告资产

后端职责：`OrchestrationService`、`ReportService`、`ReportCoordinatorService`、`ReportTaskService`、`JobGraphService`、`ReportCatalogIndexService`、`ReportDesignSpecService`。

### 7.1 智能报告任务的输入

创建报告前应准备：当前数据集和工作表、业务目标、可选历史报告或背景材料、多表策略、需要的分析或交付类型。

### 7.1.1 Smart Report Studio 的逐项配置

| 配置区 | 用户可以提供什么 | 服务端如何使用 | 使用边界 |
| --- | --- | --- | --- |
| 数据源与工作表 | 已上传数据集、新文件、活动工作表、多表模式 | 建立报告的数据范围与表策略 | 系统已自动确认跨表连接关系 |
| 分析需求 | 待解决问题、分析诉求、核心目的、目标读者、预期结果、关键约束 | 作为业务路线与报告结构的上下文 | 这些文字本身就是数据证据 |
| 历史报告与背景 | 样例报告、业务背景资料 | 参考表达风格、业务语境和历史材料 | 自动复制旧报告或沿用旧结论 |
| 高级交付选项 | R 工作流、行业研究、增强交付管线、完整表格、通用业务运行时、交付目标、图表配色和视觉要求 | 向服务端请求对应的可选路线 | 所有本地部署均已具备这些依赖 |
| 任务状态 | 提交异步任务后查看阶段、进度、错误和结果 | 反映后台作业的实际状态 | 页面刷新即意味着任务完成 |

高级交付选项是对服务端能力的请求。可用性取决于安装的依赖、运行时权限、数据适配度和当前配置；便携版基础能力以默认可用范围为准。

### 7.2 同步报告与异步作业

| 模式 | 接口 | 适合场景 | 用户应查看 |
| --- | --- | --- | --- |
| 同步提交 | `POST /api/datasets/{dataset_id}/smart-report` | 小型或需要立即等待结果的任务 | 直接返回的任务/报告结果 |
| 异步提交 | `POST /api/datasets/{dataset_id}/smart-report-jobs` | 多表、耗时或需后台跟踪的任务 | 作业标识和状态 |
| 查询作业 | `GET /api/report-jobs/{job_id}` | 追踪异步任务 | 排队、执行、成功、失败及相关信息 |

**输出范围**：任务可生成报告正文、统计表、图表、数据附件、JSON 证据、Markdown、HTML、PDF 或其子集。实际资产由数据、路径、运行状态和质量门禁决定，任务按结果清单返回可用格式。

### 7.3 多表策略

| 策略 | 含义 | 适用前提 | 风险 |
| --- | --- | --- | --- |
| `single` | 以一个活动表为中心生成分析/报告 | 业务问题可由单表回答 | 容易遗漏应参照的维表或历史表 |
| `combined` | 组合多个表的上下文 | 表之间有已确认的可组合逻辑 | 连接键、粒度或时间口径不一致会误导结果 |
| `separate` | 分表生成子分析或子报告，再由总控任务组织 | 各表有独立价值或缺少可靠合并条件 | 需要人工审阅跨表结论是否一致 |

### 7.4 报告目录与资产

| 功能 | 接口 | 用途 |
| --- | --- | --- |
| 列出报告 | `GET /api/reports` | 浏览已经生成或可修订的报告 |
| 读取报告详情 | `GET /api/reports/{report_id}` | 查看一个报告的元数据、资产和状态 |
| 报告任务状态 | `GET /api/report-jobs/{job_id}` | 追踪后台任务状态 |

**用户应先审阅后交付**：检查报告覆盖的数据范围、分析方法、图表、数值证据、结论措辞、附件和质量状态；正式管理报告需通过完整 AI 链路与质量门禁。

## 8. 正式管理报告的 AI 强制链与 PDF 门禁

正式 `management_report.pdf` 需满足以下必要条件：

```text
raw data
-> DataProfileService
-> AIFieldSemanticMapper
-> AIBusinessContextRouter
-> AIMetricDerivationPlanner
-> DeterministicMetricExecutor
-> EvidenceValidator
-> ReportBindingLayer
-> FormalPDFReleaseGate
-> management_report.pdf
```

### 8.1 每一层的职责、输入和产物

| 层 | 主要输入 | 负责的事情 | 需要保留的结果 | 职责边界 |
| --- | --- | --- | --- | --- |
| `DataProfileService` | 原始数据、工作表上下文 | 建立字段、质量、规模和结构画像 | 数据画像 | 直接编造业务结论 |
| `AIFieldSemanticMapper` | 画像、字段名、样本、用户上下文 | 生成结构化字段语义和角色映射 | 可追溯 AI 映射工件 | 直接定稿数值 |
| `AIBusinessContextRouter` | 字段语义、目标、背景 | 选择业务分析路线和报告重点 | 业务路由工件 | 绕过字段语义直接绑定报告 |
| `AIMetricDerivationPlanner` | 语义、路由、数据结构 | 规划指标定义、输入和计算路径 | 指标规划工件 | 计算或杜撰最终数值 |
| `DeterministicMetricExecutor` | 已验证指标计划、原始数据 | 用确定性代码执行计算 | 可复算数值和计算证据 | 由 LLM 输出数值定稿 |
| `EvidenceValidator` | 数值、证据、结构化工件 | 校验输入、绑定和证据完整性 | 验证状态与错误信息 | 忽略缺失或矛盾证据 |
| `ReportBindingLayer` | 已验证结果 | 把可信字段理解、数值、图表和文字绑定到报告 | 绑定后的报告内容 | 在渲染阶段理解字段或改写口径 |
| `FormalPDFReleaseGate` | 报告、质量分、追踪工件 | 决定是否允许正式发布 | 通过/拒绝记录 | 放行未达标的正式 PDF |

### 8.2 必须满足的门禁

1. `AIFieldSemanticMapper`、`AIBusinessContextRouter`、`AIMetricDerivationPlanner` 都必须在正式报告绑定前完成。
2. AI 输出必须通过模式校验并持久化可追溯工件。
3. 所有正式数值必须由确定性执行器计算；LLM 输出提供文字与结构化建议。
4. 缺失 AI 追踪、模式无效、证据不完整或任意强制步骤被绕过时，只能生成 `debug_report`，不得发布正式 `management_report.pdf`。
5. 最终质量分低于 `90` 时，禁止正式 PDF 发布。
6. PDF 渲染器呈现已绑定和验证的内容；字段理解、业务路由和指标推导由前序链路负责。

### 8.3 用户看到正式报告状态时应如何理解

| 状态或现象 | 正确理解 | 下一步 |
| --- | --- | --- |
| 有调试报告或中间文件 | 说明流程有可检查产物 | 作为流程检查材料使用；正式管理报告需通过完整门禁 |
| AI 追踪缺失 | 正式链不完整 | 回到任务/配置/数据上下文排查 |
| Schema 校验失败 | AI 工件未满足下游可靠使用条件 | 修复输入、提示或服务配置后重新执行 |
| 数值证据缺失 | 需补充证据以形成可复核结论 | 检查指标计划、数据和确定性执行器 |
| 质量分低于 90 | 正式发布被拒绝 | 审阅质量问题，改善内容和证据后重试 |
| 正式门禁通过 | 可以生成合格的正式报告 | 仍需业务责任人做最终交付审核 |

## 9. Analysis Lab 方法实验台

前端职责：`AnalysisWorkspaceShell`。后端职责：`AutoAnalysisService`、`AutoAnalysisFieldService`、`AutoAnalysisMethodExecutorService`、`AutoAnalysisVisualService`、`AutoAnalysisEvidenceService`、`AnalysisLabPdcaService`。

### 9.1 Lab 的定位

Lab 是探索、比较、配置和复用方法的工作区。它适合在正式报告前理解数据、试验合理的方法组合、建立方法卡和审阅证据。正式报告持续遵循完整发布约束。

### 9.2 数据准备与字段角色

**用户操作**：选择/上传数据，查看字段画像，为字段指定或覆盖角色，选择当前分析目标。

**结果**：形成可传给方法路由、派生指标、图表和执行器的字段配置。

**Lab 可配置的常见字段角色**：

| 字段角色 | 用于什么 | 常见例子 | 配错时的风险 |
| --- | --- | --- | --- |
| 目标 | 被解释、预测或比较的结果 | 销售额、是否转化、满意度 | 模型结论回答错问题 |
| 特征 | 解释、预测或分群的输入 | 渠道、价格、活跃度 | 可能引入泄漏或共线性 |
| 分组 | 比较不同人群、地区或渠道 | 区域、品类、实验组 | 分组口径与样本量失真 |
| 标签 | 展示或识别对象 | 商品名、客户名、门店名 | 可把展示文本误作分析变量 |
| 时间 | 排序、趋势、时序分析 | 日期、周、月份 | 时间粒度或顺序错误 |
| 气泡图 X/Y/大小 | 多变量可视化 | 规模、增长率、利润 | 视觉关系被误读为因果 |
| 象限 X/Y/对象 | 经营象限定位 | 价值、增长、商品/客户 | 阈值和象限解释缺少业务依据 |

同一字段可能对应不同角色。字段绑定应以业务定义、字段类型和数据粒度为依据。

**边界**：人工覆盖必须有业务依据；把标识符当指标、把文本当连续数值或把汇总表与明细表混用，会使后续方法即使成功运行也不可靠。

### 9.3 派生指标定义

**解决的问题**：原始表中不一定直接存在需要的经营指标，例如转化率、客单价、周期同比、结构占比或单位成本。

**合理流程**：定义指标名称 -> 指定输入字段 -> 明确公式、筛选范围、时间窗口和单位 -> 保存为可执行/可审阅的计划 -> 运行并检查数值。

**正式路径要求**：对于会进入正式报告的指标，AI 可以帮助规划公式和输入，但实际数值仍需由 `DeterministicMetricExecutor` 计算并写入证据。

### 9.4 方法目录

**接口**：`GET /api/lab/methods`。

**用途**：按问题类型、变量角色、输出目标和方法类别浏览方法。目录帮助选择，不替代统计方法的前提检查。

**用户应比较的维度**：方法想回答的问题、需要的变量类型、样本量和独立性要求、结果是否可解释、是否需要图表/表格/模型诊断、能否进入所需报告部件。

**Lab 目录的主要分类**：描述统计、关联分析、分类关联、比较、分布与假设、参数与非参数检验、回归与广义线性模型、机器学习、多变量分析、时间序列、因果与面板、存活分析、实验设计、心理测量、可视化和报告部件。默认目录面向非金融统计与数据分析方法；实际可运行状态以当前运行时目录和字段绑定检查为准。

### 9.5 方法卡

**接口**：`POST /api/lab/method-cards`。

**用途**：把一个可复用的分析设计保存为方法卡，包括方法、字段角色、参数、期望输出、报告部件或执行约束。

**好处**：同类分析可复用同一配置，复核人能看到“为什么选这个方法、使用哪些字段、按什么参数运行”。

**使用范围**：方法卡保存分析设计。更换数据后需重新检查数据质量和方法前提。

### 9.6 运行实验与查看证据

**接口**：`POST /api/lab/run`。

**输入**：数据集、字段配置、方法或方法卡、参数、输出偏好。

**可能输出**：运行状态、统计表、图表、计算表、证据表、报告部件候选项、资产清单和错误信息。

**四种运行方式**：自动运行、单方法运行、批量运行、报告试运行。运行前页面会显示就绪、部分就绪或阻塞原因；目录中的方法需结合当前环境配置确定可执行性。

**结果画布可帮助审阅的内容**：统计表、图表、方法解释、字段审计、清洗与派生过程、运行状态、原始结果包，以及可能生成的清单、索引、方法包、读者版汇总、报告部件和下载链接。

**建议操作顺序**：

1. 先运行一项方法，确认字段与结果是否合理。
2. 再按目标组织多个方法或报告部件。
3. 审阅每个方法的前提、参数、样本范围和证据。
4. 需要正式交付时，带着已审阅的设计进入正式报告链，由发布门禁评估交付资格。

### 9.7 PDCA 状态与周期改进

| 操作 | 接口 | 作用 |
| --- | --- | --- |
| 查看状态 | `GET /api/lab/pdca/status` | 读取当前计划、执行、检查、改进行为的状态 |
| 运行周期 | `POST /api/lab/pdca/run` | 触发或记录一次 Lab 的 PDCA 改进周期 |

**使用范围**：PDCA 用于管理探索与改进过程；统计结论、正式证据和质量门禁由相应流程完成。

## 10. 方法指南

**入口**：`/lab/method-guide`，前端可由 `MethodGuideModal` 等组件展示。

**用途**：帮助用户从业务问题、变量类型、目标输出和方法类别出发理解可选分析路径。

**典型问题到方法的映射**：

| 想回答的问题 | 常见方法方向 | 必须先确认 |
| --- | --- | --- |
| 当前水平和结构如何 | 描述统计、频数、透视、帕累托 | 指标单位、分组层级 |
| 两组或多组是否不同 | t 检验、ANOVA、非参数检验 | 分组、独立性、分布前提 |
| 两个变量是否有关 | 相关、列联表、关联强度 | 变量类型、异常值、因果边界 |
| 哪些因素与结果相关 | 回归、广义模型、特征分析 | 目标定义、混杂、样本设计 |
| 如何识别客户/商品群体 | 聚类、降维、分群 KPI | 特征尺度、群体可解释性 |
| 是否存在趋势/周期/异常 | 时序、移动平均、ACF/PACF | 时间顺序、缺失周期、结构变化 |

**使用范围**：方法指南提供方法选择线索。领域专家、统计专业审阅、实验设计和合规审核应参与相应决策；复杂问题需结合这些审核完成。

## 11. 报告修订、差异、附件与批注

前端职责：`RevisionModeShell`、`RevisionWorkspaceShell`、`ReportRevisionWorkbench`、预览面板、批注层与运行时活动面板。后端职责：`ReportAgentSessionService`。

### 11.1 找到已有报告

**入口**：`/revision`。

**基础动作**：浏览报告目录、搜索或打开报告，查看报告详情和已有资产。

**可用的筛选思路**：按关键词、数据集、业务画像、更新时间或生成时间缩小报告范围。运行时不可用时，修订入口提供只读浏览；报告文件状态以报告元数据和读取结果为准。

**接口**：`GET /api/reports`、`GET /api/reports/{report_id}`。

### 11.2 创建或恢复修订会话

| 操作 | 接口 | 输入 | 输出 |
| --- | --- | --- | --- |
| 创建修订会话 | `POST /api/reports/{report_id}/agent-sessions` | 报告标识与会话上下文 | 会话标识和初始状态 |
| 读取会话 | `GET /api/reports/{report_id}/agent-sessions/{session_id}` | 报告和会话标识 | 会话详情和状态 |
| 发送修改要求 | `POST /api/report-agent-sessions/{session_id}/messages` | 用户消息、修改意图 | 新事件和处理结果 |
| 取消会话 | `POST /api/report-agent-sessions/{session_id}/cancel` | 会话标识 | 取消状态 |

**适合提出的修改要求**：补充某段说明、调整标题层级、检查图表口径、替换附件、解释某个结论的证据来源、修正明确的表达错误。

**工作区定位方式**：`/revision/workspace?report_id=...&session_id=...` 使用报告 ID 和会话 ID 打开指定上下文。页面会显示当前原生 Codex 回合、任务状态、尝试次数、处理范围、验证结果、禁止修改项和错误信息；执行中可补充指导、取消或在满足条件时续跑。

**修订范围**：修订会话用于管理有依据的内容调整。涉及数值、正式结论或指标定义的修改必须回到可追溯数据和正式门禁。

### 11.3 事件、实时流和产物

| 功能 | 接口 | 用途 |
| --- | --- | --- |
| 读取事件记录 | `GET /api/report-agent-sessions/{session_id}/events` | 查看会话发生过什么 |
| 订阅实时事件 | `GET /api/report-agent-sessions/{session_id}/events/stream` | 持续接收执行进度或会话事件 |
| 查看生成文件 | `GET /api/report-agent-sessions/{session_id}/files` | 浏览会话相关产物 |
| 查看差异 | `GET /api/report-agent-sessions/{session_id}/diff` | 比较修订前后内容 |

**用户复核重点**：事件是否显示执行失败、差异是否覆盖预期段落、生成文件是否对应当前会话、修改后是否影响原有数值或证据。

**实时更新策略**：前端优先使用 SSE 事件流更新修订进度；连接不可用时会使用轮询回退。两种机制传达服务端状态，正式报告验证以发布门禁结果为准。

### 11.4 附件与批注

| 操作 | 接口 | 作用 | 注意事项 |
| --- | --- | --- | --- |
| 列出附件 | `GET /api/report-agent-sessions/{session_id}/attachments` | 查看会话资料 | 检查附件来源和敏感性 |
| 上传附件 | `POST /api/report-agent-sessions/{session_id}/attachments` | 添加修订依据或材料 | 上传前移除客户和个人敏感资料 |
| 删除附件 | `DELETE /api/report-agent-sessions/{session_id}/attachments/{attachment_id}` | 移除不再需要的资料 | 删除前确认当前任务仍具备完整证据 |
| 列出批注 | `GET /api/report-agent-sessions/{session_id}/annotations` | 浏览批注意见 | 批注需能定位到可复核位置 |
| 新增批注 | `POST /api/report-agent-sessions/{session_id}/annotations` | 对内容或页面区域提出修改意见 | 说明预期改动和理由 |
| 删除批注 | `DELETE /api/report-agent-sessions/{session_id}/annotations/{annotation_id}` | 清理已处理意见 | 删除后核对相关修订是否已完成 |

**附件格式与用途**：修订工作区可上传 `.csv`、`.tsv`、`.xlsx`、`.xls`、`.md`、`.txt`、`.pdf`、`.json` 作为补充证据。附件进入修订上下文；图表数值由后端确定性流程渲染，修订界面保留原报告数字。

**PDF 预览与批注动作**：预览支持翻页、适配页面或宽度、缩放，以及画笔、矩形、高亮和橡皮擦批注。批注按文件和页面坐标保存，适合作为后续修订的定位说明；事实与数值通过数据和验证流程确认。

### 11.5 发布修订后的本地报告版本

**接口**：`POST /api/report-agent-sessions/{session_id}/publish`。

**含义**：把当前会话经处理的版本发布到本地报告工作区的版本流中。

**发布前条件**：前端仅在 `canPublish` 条件满足时提供可发布状态，例如存在可用预览、没有运行中的回合，并满足已有验证要求。发布动作持续受 `canPublish` 校验约束；用户可检查会话事件和验证状态，处理未满足条件后再发布。

**发布范围**：系统内修订发布创建本地报告版本。GitHub、公开 Release 和网站部署使用独立流程；正式管理报告继续遵循证据与质量门禁。

## 12. 可选运行时与本地扩展

这类能力扩展本地工作流，需经本机配置后使用。

### 12.1 AI 提供方配置

**作用**：为需要 AI 结构化理解、业务路由、指标规划或其他可选智能能力的流程提供兼容模型服务配置。

**用户责任**：在本地 `.env` 或运行时配置中保存端点、模型与密钥；禁止把 `.env`、密钥、真实提示上下文或日志提交到 GitHub。

**数据边界**：如果选择外部模型服务，字段、业务背景、报告上下文和用户上传材料可能会依该工作流发送给所选提供方。本机数据边界以所选工作流的传输范围为准。

### 12.2 R 工作流

后端职责：`RWorkflowService`、`RArtifactIntelligenceService`。

| 功能 | 接口 | 用途 | 前提 |
| --- | --- | --- | --- |
| R 智能工作流 | `POST /api/reports/{report_id}/r-intelligence-flow` | 进行 R 数据准备、统计、可视化和工件关联 | 本机存在可用 R/Rscript，路径配置正确 |

**可能输出**：CSV、XLSX、Markdown、HTML、PDF 或 R 工件索引，具体取决于工作流。

**配置状态**：系统以配置状态决定可用路径。未配置时，接口或界面会明确报错或显示不可用，并保留实际配置状态。

### 12.3 Codex Runtime

后端职责：`CodexRuntimeService`、`CodexRuntimeTaskService`、`CodexRuntimePipelineService`、`CodexCliResolverService`、运行时进程与学习账本服务。

**启用条件**：健康检查可用于发现本机 CLI；真正创建或管理 Runtime 任务需要 `ASTERIA_ENABLE_CODEX_RUNTIME_API=1`，实际执行还必须满足 `ASTERIA_CODEX_RUNTIME_ENABLED=1`、可用 CLI、认证与受限工作区。默认关闭。

| 功能 | 接口 | 用途 |
| --- | --- | --- |
| 健康检查 | `GET /api/runtime/codex-health` | 检查本机 Codex CLI 与受控运行时状态 |
| 直接任务 | `POST /api/codex-runs` | 创建本地运行任务 |
| 异步任务 | `POST /api/codex-run-jobs` | 创建可查询的后台任务 |
| 查询任务 | `GET /api/codex-run-jobs/{job_id}` | 读取后台任务状态 |
| 查询运行 | `GET /api/codex-runs/{run_id}` | 读取一次运行详情 |
| 查看日志 | `GET /api/codex-runs/{run_id}/log` | 查看运行日志 |
| 取消运行 | `POST /api/codex-runs/{run_id}/cancel` | 终止一次运行 |
| 取消任务 | `POST /api/codex-run-jobs/{job_id}/cancel` | 终止后台任务 |

**安全边界**：它运行于高权限本机扩展范围。公网 API 部署需要独立的认证、隔离与网关设计；启用前审阅本地代码执行边界。

### 12.4 运行中进程管理

| 功能 | 接口 | 用途 |
| --- | --- | --- |
| 列出进程 | `GET /api/runtime/processes` | 查看受控运行时进程 |
| 取消进程 | `POST /api/runtime/processes/{kind}/{process_id}/cancel` | 请求取消某类进程 |
| 恢复进程 | `POST /api/runtime/processes/{kind}/{process_id}/resume` | 恢复允许继续的进程 |

**边界**：进程管理是本地运维工具，操作前应确认目标任务、文件和数据范围，避免在报告生成或文件写入中途造成不完整产物。

### 12.5 本地 Skill、实验特性和报告 Agent Team

**可查看的内容**：`GET /api/skills/mounted`、`GET /api/lab/skills`、`GET /api/lab/feature-trials/catalog` 和 `GET /api/lab/report-agent-teams` 用于展示当前本机状态。它们不安装包、不启动试验也不创建 Runtime 任务；空列表表示尚未导入，不表示功能不存在。

**管理与执行条件**：安装、导入、挂载、卸载、删除、Feature Trial 和 Team Run 需要 `ASTERIA_ENABLE_LOCAL_SKILL_INSTALLER=1`。Team Run 还必须有至少一个已挂载团队、选定数据集、可运行 Codex Runtime、CLI 和受限工作区。

| 类别 | 接口组 | 能做什么 | 可见结果与边界 |
| --- | --- | --- | --- |
| 已挂载 Skill | `GET /api/skills/mounted`、`GET /api/lab/skills` | 查看项目/本机可识别的 Skill 与外部包 | 来源、挂载状态、内嵌 Skill/命令/MCP 元数据；包内容按受控流程执行 |
| 安装/导入 Skill | `POST /api/lab/skills/install`、`POST /api/lab/skills/import-local` | 从 GitHub URL 或本机目录建立 Skill 条目 | 仅导入经审阅来源；包必须含 `SKILL.md` 或插件清单 |
| 挂载/卸载/删除 Skill | `POST /api/lab/skills/{skill_id}/mount`、`unmount`、`DELETE` | 管理 Skill 是否进入后续 Lab 上下文 | 挂载信息会形成 `external_skill_context.json`；声明命令或 MCP 配置须经受控流程显式执行 |
| Feature Trial | `GET /api/lab/feature-trials/catalog`、`POST /api/lab/feature-trials/run` | 用真实数据评估插件功能适配性 | 产生 `trial_id`、就绪度/原因、推荐动作、建议载荷和 JSON/CSV/Markdown 工件；执行范围限定为数据适配性评估 |
| Report Agent Team | `GET /api/lab/report-agent-teams`、导入、挂载、卸载、运行、删除接口 | 管理用户自有的本地团队 Markdown，并创建一项 Codex 任务 | 返回团队/挂载状态、任务 ID、状态和工作区路径；后端将角色说明交给单个受控 Codex 任务，调度状态以任务结果为准 |

**与修订 Agent 的区别**：Lab 中的 Report Agent Team 面向新任务的角色与数据上下文；修订工作区的 Report Agent Session 面向已有报告的消息、事件、附件、批注、差异和本地版本。两者均受正式 `management_report.pdf` 发布门禁约束。完整步骤和错误处理见 [本地扩展指南](local-extensions.zh-CN.md)。

### 12.6 Codex 管线与学习账本

| 功能 | 接口 | 用途 |
| --- | --- | --- |
| 学习账本列表 | `GET /api/runtime-learning-ledger` | 查看本地运行的记录摘要 |
| 单条账本 | `GET /api/runtime-learning-ledger/{entry_id}` | 查看指定记录 |
| 创建管线任务 | `POST /api/codex-pipeline-jobs` | 提交多阶段本地管线 |
| 查询管线 | `GET /api/codex-pipeline-jobs/{job_id}` | 查看管线状态 |
| 取消管线 | `POST /api/codex-pipeline-jobs/{job_id}/cancel` | 终止管线 |
| 重试阶段 | `POST /api/codex-pipeline-jobs/{job_id}/retry-stage` | 重试指定阶段 |
| 登记报告输出 | `POST /api/codex-pipeline-jobs/{job_id}/register-report-output` | 将允许的输出登记到任务中 |

**边界**：这些接口用于受控的本地扩展工作，不替代 Asteria 正式报告的强制链和质量门禁。

## 13. 专项业务分析路线

专项路线由 `BusinessProfileRouter` 和对应服务模块根据数据特征、业务目标与配置选择。路线命中由数据和业务路由决定，行业模板以条件能力提供。

| 路线分组 | 代表服务模块 | 可处理的方向 | 使用前提 |
| --- | --- | --- | --- |
| 电商商品与经营 | `EcommerceProductOperationsService`、电商 PDF/行动路线渲染器 | 商品、交易、经营指标、行动建议 | 字段与口径要能支持商品/交易分析 |
| 互联网运营 | `InternetOperationsAnalysisModules`、`InternetOpsProfileService`、管理简报与行动路线模块 | 渠道、留存、运营表现、内容或增长指标 | 数据必须有足够运营事件或周期信息 |
| 采购与销售 | `ProcurementSalesProfileService`、指标挖掘、关系与渲染模块 | 采购、销售、供应与经营关系 | 要确认采购和销售表的粒度及连接逻辑 |
| 通用深度经营 | `GenericLongBusinessProfileService`、深度挖掘、派生指标发现模块 | 非特定行业的长周期经营分析 | 仍需由用户确认指标口径和业务目标 |
| 市场、媒体与管理会计 | `MarketIntelligenceService`、`MediaDecisionService`、`ManagementAccountingKnowledgeService` | 市场信息、媒体决策、管理会计知识支持 | 需要匹配的业务上下文和数据字段 |
| 独立行业研究 | 行业研究链、编排、引用与 PDF 校验模块 | 行业研究类路线 | 应明确资料来源、引用与报告质量要求 |

**使用范围**：专项路由根据数据特征、业务目标和配置形成候选路径；行业模板命中及结论由数据、业务规则和人工审核共同确认。

## 14. 后端职责模块地图

以下表格面向想理解项目结构的使用者和开发者，列出主要职责模块。普通用户可通过页面完成常用工作流。

| 模块组 | 代表服务 | 负责什么 | 与用户功能的关系 |
| --- | --- | --- | --- |
| 数据与目录 | `dataset_service.py`、`dataset_catalog_service.py` | 文件解析、工作表、画像、目录 | 支撑上传、选表和数据概览 |
| 上下文材料 | `historical_report_service.py`、`business_background_service.py` | 保存和读取历史报告、业务背景 | 支撑任务设计和修订语境 |
| 基础统计 | `analysis_service.py`、`statistical_catalog.py` | 方法目录和受控统计执行 | 支撑分析页与 Lab 的统计结果 |
| 自动分析 | `auto_analysis_service.py`、字段/方法/图表/证据子服务 | 字段路线、方法建议、图表、证据和报告部件 | 支撑自动分析与 Lab 探索 |
| 派生指标 | `derived_metric_usage_contract_service.py`、`derived_metric_family_execution_service.py` | 定义、约束和执行派生指标 | 支撑可复核 KPI 和指标计划 |
| 报告编排 | `orchestration_service.py`、`report_service.py`、`report_coordinator_service.py`、`job_graph_service.py` | 决定报告路径、管理任务和多表策略 | 支撑智能报告和后台作业 |
| 报告设计与资产 | `report_design_spec_service.py`、`report_catalog_index_service.py`、`report_task_service.py` | 组织报告结构、资产目录和任务 | 支撑报告浏览与交付物 |
| 正式 AI 链 | `ai_mandatory/` 下字段、路由、计划、执行、Schema、追踪模块 | 保证正式报告的理解、计算和追溯顺序 | 正式 PDF 的必要条件 |
| 证据与质量 | `evidence_digest_service.py`、质量门禁和各路线 render guard | 校验证据、约束渲染与质量 | 防止未验证内容进入正式交付 |
| 修订会话 | `report_agent_session_service.py` | 会话、消息、事件、文件、差异、附件和批注 | 支撑修订工作区 |
| R 扩展 | `r_workflow_service.py`、`r_artifact_intelligence_service.py` | 调用本机 R 和关联 R 工件 | 仅在 R 配置正确时使用 |
| Codex 扩展 | `codex_runtime_*.py`、CLI 解析与任务服务 | 本地 Codex 任务、日志、管线、账本 | 默认关闭的高权限扩展 |
| 本地扩展管理 | `skill_mount_service.py`、Lab Skill/Trial/Team 服务 | 管理技能、实验特性和团队 | 默认关闭的管理员功能 |
| 行业路线 | 电商、互联网、采购销售、通用经营、行业研究相关服务 | 为匹配场景提供路线专用处理 | 由数据与业务路由决定是否命中 |

## 15. API 参考与调用边界

### 15.1 适用范围

`backend/app/main.py` 统一提供这些接口，主要服务本地前端和本地工作流。部署时应保持本机或受控网络访问范围；公网 SaaS 所需的多租户认证、配额、审计隔离和网关能力不在当前发布范围内。

### 15.2 系统、数据与分析接口

| 方法 | 路径 | 功能 | 输入要点 | 输出/状态 |
| --- | --- | --- | --- | --- |
| GET | `/health` | 健康检查 | 无 | 服务状态 |
| GET | `/api/manifest` | 读取运行清单 | 无 | 公开运行信息 |
| GET | `/api/runtime-settings` | 读取运行时设置状态 | 无 | 不含密钥的配置状态 |
| GET | `/api/datasets` | 列出数据集 | 无 | 数据集目录 |
| POST | `/api/datasets/upload` | 上传数据文件 | 文件与元信息 | 数据集、画像、工作表信息 |
| GET | `/api/datasets/{dataset_id}` | 读取数据集详情 | 数据集标识 | 数据与字段上下文 |
| POST | `/api/datasets/{dataset_id}/sheet` | 切换活动工作表 | 目标工作表 | 更新后的表上下文 |
| GET | `/api/datasets/{dataset_id}/workflow` | 读取工作流摘要 | 数据集标识 | 可用路线和任务上下文 |
| GET | `/api/historical-reports` | 列出历史报告 | 无 | 历史材料目录 |
| POST | `/api/historical-reports/upload` | 上传历史报告 | 文件 | 新材料记录 |
| GET | `/api/historical-reports/{template_id}` | 读取历史报告 | 材料标识 | 材料详情 |
| GET | `/api/business-backgrounds` | 列出业务背景 | 无 | 背景材料目录 |
| POST | `/api/business-backgrounds/upload` | 上传业务背景 | 文件 | 新背景记录 |
| GET | `/api/business-backgrounds/{context_id}` | 读取背景详情 | 背景标识 | 背景内容/元信息 |
| GET | `/api/statistics/catalog` | 获取统计目录 | 无 | 方法、前提和分组信息 |
| POST | `/api/statistics/run` | 运行受控统计 | 数据集、字段、方法、参数 | 结果、证据或错误 |
| GET | `/api/analysis/auto/methods` | 获取自动分析候选方法 | 数据/目标上下文 | 方法建议 |
| POST | `/api/analysis/auto` | 执行自动分析 | 数据、目标、输出偏好 | 路线、表、图、证据候选项 |

### 15.3 Lab、报告与修订接口

| 方法 | 路径 | 功能 | 输入要点 | 输出/状态 |
| --- | --- | --- | --- | --- |
| GET | `/api/lab/methods` | 获取 Lab 方法目录 | 无或筛选条件 | 方法信息 |
| POST | `/api/lab/method-cards` | 保存方法卡 | 方法、字段角色、参数 | 方法卡记录 |
| GET | `/api/lab/pdca/status` | 获取 PDCA 状态 | 无或工作区上下文 | 当前周期状态 |
| POST | `/api/lab/pdca/run` | 运行 PDCA 周期 | 工作区/计划上下文 | 更新后的周期结果 |
| POST | `/api/lab/run` | 运行 Lab 分析 | 数据、方法、字段、参数 | 运行结果、资产或错误 |
| POST | `/api/datasets/{dataset_id}/smart-report` | 同步创建报告 | 目标、上下文、策略 | 直接任务/报告结果 |
| POST | `/api/datasets/{dataset_id}/smart-report-jobs` | 异步创建报告作业 | 同上 | 作业标识 |
| GET | `/api/report-jobs/{job_id}` | 查询作业 | 作业标识 | 作业状态和详情 |
| GET | `/api/reports` | 列出报告 | 无或查询条件 | 报告目录 |
| GET | `/api/reports/{report_id}` | 读取报告详情 | 报告标识 | 资产、元数据、状态 |
| POST | `/api/reports/{report_id}/agent-sessions` | 创建修订会话 | 报告和会话上下文 | 会话标识 |
| GET | `/api/reports/{report_id}/agent-sessions/{session_id}` | 读取会话 | 报告和会话标识 | 会话详情 |
| POST | `/api/report-agent-sessions/{session_id}/messages` | 提交修改消息 | 修改要求 | 会话事件/结果 |
| GET | `/api/report-agent-sessions/{session_id}/events` | 读取事件 | 会话标识 | 事件历史 |
| POST | `/api/report-agent-sessions/{session_id}/cancel` | 取消会话 | 会话标识 | 取消状态 |
| GET | `/api/report-agent-sessions/{session_id}/files` | 读取会话文件 | 会话标识 | 文件清单 |
| GET | `/api/report-agent-sessions/{session_id}/diff` | 读取差异 | 会话标识 | 修订差异 |
| GET | `/api/report-agent-sessions/{session_id}/attachments` | 列出附件 | 会话标识 | 附件清单 |
| POST | `/api/report-agent-sessions/{session_id}/attachments` | 上传附件 | 文件与关联信息 | 附件记录 |
| DELETE | `/api/report-agent-sessions/{session_id}/attachments/{attachment_id}` | 删除附件 | 会话和附件标识 | 删除状态 |
| GET | `/api/report-agent-sessions/{session_id}/annotations` | 列出批注 | 会话标识 | 批注清单 |
| POST | `/api/report-agent-sessions/{session_id}/annotations` | 新增批注 | 位置、内容、上下文 | 批注记录 |
| DELETE | `/api/report-agent-sessions/{session_id}/annotations/{annotation_id}` | 删除批注 | 会话和批注标识 | 删除状态 |
| GET | `/api/report-agent-sessions/{session_id}/events/stream` | 订阅事件流 | 会话标识 | 持续事件流 |
| POST | `/api/report-agent-sessions/{session_id}/publish` | 发布本地修订版本 | 会话标识 | 本地发布状态 |

### 15.4 扩展与管理员接口

| 方法 | 路径 | 功能 | 默认状态 |
| --- | --- | --- | --- |
| GET | `/api/ecosystem/market` | 查看生态市场信息 | 受本地配置影响 |
| GET | `/api/skills/mounted` | 查看挂载 Skill | 默认不含安装能力 |
| GET | `/api/lab/skills` | 列出 Lab Skill | 本机只读状态；不安装或执行 |
| POST | `/api/lab/skills/install` | 安装 Skill | 默认关闭 |
| POST | `/api/lab/skills/import-local` | 导入本地 Skill | 默认关闭 |
| POST | `/api/lab/skills/{skill_id}/mount` | 挂载 Skill | 默认关闭 |
| POST | `/api/lab/skills/{skill_id}/unmount` | 卸载 Skill | 默认关闭 |
| DELETE | `/api/lab/skills/{skill_id}` | 删除 Skill | 默认关闭 |
| GET | `/api/lab/feature-trials/catalog` | 查看实验特性 | 本机只读目录；实验性 |
| POST | `/api/lab/feature-trials/run` | 运行实验特性 | 默认关闭，需安装器开关 |
| GET | `/api/lab/report-agent-teams` | 查看团队配置 | 本机只读状态 |
| POST | `/api/lab/report-agent-teams/import-local` | 导入本地团队 | 默认关闭 |
| POST | `/api/lab/report-agent-teams/{team_id}/mount` | 挂载团队 | 默认关闭 |
| POST | `/api/lab/report-agent-teams/{team_id}/unmount` | 卸载团队 | 默认关闭 |
| POST | `/api/lab/report-agent-teams/run` | 运行团队 | 默认关闭 |
| DELETE | `/api/lab/report-agent-teams/{team_id}` | 删除团队 | 默认关闭 |
| GET | `/api/runtime/codex-health` | 检查 Codex Runtime | 本机只读检查；不执行任务 |
| GET/POST | `/api/codex-runs`、`/api/codex-run-jobs` | 管理本地 Codex 运行/任务 | 同上 |
| GET | `/api/runtime/processes` | 查看运行时进程 | 受运行时状态影响 |
| POST | `/api/runtime/processes/{kind}/{process_id}/cancel`、`resume` | 取消或恢复进程 | 受运行时状态影响 |
| POST | `/api/reports/{report_id}/r-intelligence-flow` | 运行 R 工作流 | 需本机 R/Rscript |
| GET | `/api/runtime-learning-ledger`、`/{entry_id}` | 查看本地学习账本 | Codex 扩展可用时 |
| GET/POST | `/api/codex-pipeline-jobs` 及子路径 | 管理 Codex 管线 | Codex 扩展可用时 |

## 16. 前端组件职责地图

| 前端模块 | 负责的用户体验 | 不负责的事情 |
| --- | --- | --- |
| `SmartReportStudio` / `/analysis` | 正式分析、报告任务、结果与资产浏览 | 绕过后端正式质量门禁 |
| `AnalysisWorkspaceShell` / `/lab` | 数据准备、方法探索、字段配置、方法卡、运行结果 | 将探索输出自动升格为正式报告 |
| `MethodGuideModal` / `/lab/method-guide` | 方法信息、选择提示与学习路径 | 代替统计专业判断 |
| `DatasetPicker` | 选择与切换数据集 | 纠正数据口径或实际业务含义 |
| `ChartPanel` | 展示图表和相关资产 | 替代数值证据、隐藏筛选条件 |
| `CodeEditorPanel` | 承载受控编辑/代码相关界面 | 无限制执行任意不可信代码 |
| `RevisionModeShell` / `/revision` | 报告目录与修订入口 | 直接公开发布到 GitHub |
| `RevisionWorkspaceShell` / `ReportRevisionWorkbench` | 会话、消息、差异、附件、批注和发布协作 | 修改事实或数值而不留证据 |
| `ReportPreviewPane` / `AnnotationLayer` | 报告预览与位置化批注 | 判定正式质量门禁是否通过 |
| `RuntimeSettingsPanel` / 运行时面板 | 显示本地运行时状态和活动 | 自动安装或授权高权限扩展 |

## 17. 功能可用性矩阵与故障判断

| 功能 | 默认状态 | 成功信号 | 常见不可用原因 | 应做什么 |
| --- | --- | --- | --- | --- |
| 数据上传 | 默认可用 | 数据集出现，画像可读 | 文件损坏、格式不支持、内容无表格结构 | 转换格式、检查表头与文件完整性 |
| 工作表切换 | 条件可用 | 活动表和画像更新 | 单表文件、工作表无法解析 | 选择可读工作表或转换 Excel |
| 统计运行 | 条件可用 | 返回结果、表或明确错误 | 方法前提不符、变量选择错误、样本不足 | 回到画像和方法前提 |
| 自动分析 | 条件可用 | 获得路线/方法/图表/证据候选项 | 数据字段不明确、目标过于笼统 | 明确字段角色与业务目标 |
| 智能报告 | 默认可提交，产物条件可得 | 任务/作业状态可查询 | 数据或上下文不完整、运行错误 | 查看作业状态和错误信息 |
| 正式 PDF | 正式受控 | 门禁通过并生成正式文件 | AI trace、Schema、证据或质量分不合格 | 修复阻断项后重新运行 |
| Lab 运行 | 条件可用 | 产生实验结果与资产 | 方法配置/数据类型不匹配 | 从单一方法开始复核 |
| 修订基础浏览 | 默认可用 | 可见已有报告 | 本地没有报告资产 | 先完成报告任务或导入工作区资产 |
| 高级修订会话 | 条件可用 | 会话、事件和差异可读 | 运行时配置或会话执行失败 | 检查会话状态与本地配置 |
| R 工作流 | 可选配置 | R 工件/流程成功 | R/Rscript 缺失或路径错误 | 安装并配置 R |
| Codex Runtime | 默认关闭 | 健康检查通过、任务可运行 | 未设置启用变量或 CLI 不可用 | 仅在理解风险后显式启用 |
| Skill/Team 扩展 | 默认关闭 | 可列出或挂载受信任配置 | 本地扩展安装器未启用 | 管理员审阅后再启用 |

## 18. 四条推荐操作路径

### 18.1 基础本地分析

1. 启动应用并确认 `/health` 正常。
2. 上传 CSV、TSV、XLSX 或 DTA。
3. 选择活动表，检查字段、样本、缺失、单位和时间。
4. 写清业务问题和分析范围。
5. 运行一个适配的受控统计方法，先审阅表和证据。
6. 再按需要进入报告任务，检查资产与结论。

### 18.2 正式管理报告

1. 完成数据准备、业务目标和必要上下文。
2. 提交智能报告任务并观察作业状态。
3. 确认强制链的字段语义、业务路由、指标规划、确定性计算和证据校验都留下可追溯记录。
4. 确认最终质量分至少为 90。
5. 只有 `FormalPDFReleaseGate` 放行后，才将 `management_report.pdf` 作为正式交付物。

### 18.3 方法探索与复用

1. 进入 `/lab`，确认数据和字段角色。
2. 明确一个可检验问题，选择适配方法。
3. 建立方法卡，保存字段、参数和输出预期。
4. 先小范围运行，检查每项结果与方法前提。
5. 需要正式交付时，把经审阅的设计带回正式报告流程。

### 18.4 修订已有报告

1. 在 `/revision` 找到目标报告。
2. 在 `/revision/workspace` 创建或恢复会话。
3. 用可定位、可验证的语言提交修改要求，必要时上传依据或添加批注。
4. 查看事件、文件和差异，确认改动覆盖了目标。
5. 对数值、指标和正式结论的变更，重新核对数据、证据和质量门禁。
6. 发布的是本地报告版本；GitHub 发布需单独操作。

## 19. 隐私、安全与公开发布边界

1. 当前接口没有为公网多用户服务设计认证、权限隔离和租户边界；只应在本机回环地址或经过独立安全设计的受控环境中使用。
2. `.env`、API 密钥、上传数据、生成报告、运行日志、缓存、工作会话和客户资料不得提交到公开仓库。
3. `/storage` 或其他本地工件目录可能暴露生成资产；发布前要检查是否残留个人、客户、商业或受版权保护材料。
4. 开启外部 AI、R、Codex、Skill 或 Team 前，必须理解数据将流向哪里、运行什么代码、谁能访问本地文件。
5. 公开仓库目前没有 `LICENSE`。复制、修改、再分发或商用前需取得适用授权。

## 20. 相关文档

- [项目首页与发布入口](../README.md)
- [模块与功能手册](module-guide.zh-CN.md)
- [逐页结果说明](page-results.zh-CN.md)
- [公开项目介绍](public-project-introduction.zh-CN.md)
- [快速开始](getting-started.zh-CN.md)
- [详细用户指南](user-guide.zh-CN.md)
- [正式报告可信机制](report-integrity.zh-CN.md)
- [AI 强制发布链架构](architecture_ai_mandatory_chain.md)
- [部署边界](deployment-boundaries.md)
- [安全策略](../SECURITY.md)
