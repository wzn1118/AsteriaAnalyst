# Asteria Analyst | 企业数据分析、统计实验与管理报告工作台

[![CI](https://github.com/wzn1118/AsteriaAnalyst/actions/workflows/ci.yml/badge.svg)](https://github.com/wzn1118/AsteriaAnalyst/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/wzn1118/AsteriaAnalyst?display_name=tag&label=release)](https://github.com/wzn1118/AsteriaAnalyst/releases/latest)
[![Platform](https://img.shields.io/badge/platform-Windows%20local-0f766e)](#快速开始)
[![Language](https://img.shields.io/badge/docs-中文-2563eb)](docs/README.md)

> 面向经营分析、统计建模、数据质量核验与正式管理报告交付的本地工作台。Asteria Analyst 将数据接入、字段语义理解、分析方案、确定性计算、证据校验、报告生成、协作修订和版本发布连成一条可追溯的数据分析流程。

<img src="docs/assets/asteria-method-guide-preview.png" alt="Asteria Analyst 方法指南、字段绑定与数据分析流程预览" width="100%" />

## 快速开始

### 使用 Windows 便携发布包

1. 在 [GitHub Releases](https://github.com/wzn1118/AsteriaAnalyst/releases/latest) 下载 `AsteriaAnalyst-portable.zip`。
2. 解压到本机目录后双击 `start-asteria.bat`。
3. 启动器会打开本地分析界面；数据、运行产物和报告均保留在本机。

便携版自带运行时，无需预先配置 Python 或 Node.js。完整步骤、校验方式和常见问题见 [便携版用户指南](docs/portable-user-guide.zh-CN.md)。

### 从源码启动

适合开发、二次集成和参与贡献。准备 Windows、Python 3.11 与 Node.js 20+ 后执行：

```powershell
git clone https://github.com/wzn1118/AsteriaAnalyst.git
cd AsteriaAnalyst
PowerShell -ExecutionPolicy Bypass -File .\open-asteria-ui.ps1
```

默认入口为 `http://127.0.0.1:3000/analysis`，服务健康检查为 `http://127.0.0.1:8000/health`。启动参数、端口处理和排障步骤见 [快速开始](docs/getting-started.zh-CN.md) 与 [开发指南](docs/development-guide.zh-CN.md)。

## 产品地图

Asteria Analyst 覆盖从原始业务文件到可复核交付资产的完整工作流。每个页面都对应明确的输入、操作与结果。

| 页面与入口 | 适用工作 | 核心操作 | 主要结果 |
| --- | --- | --- | --- |
| `/` 项目首页 | 查看项目状态和本机配置 | 浏览导航、检查服务状态、配置本地 AI Provider | 运行状态和可进入的工作流 |
| `/analysis` 正式分析 | 经营分析与正式管理报告 | 导入数据、配置分析目标、运行分析、预览报告 | 数据画像、业务指标、证据和报告候选内容 |
| `/lab` Analysis Lab | 统计实验、方法比较与数据资产分析 | 绑定字段、运行方法卡、读取产物、加载数据资产蓝图 | JSON、CSV、XLSX、Markdown、图表和运行记录 |
| `/lab/method-guide` 方法指南 | 学习方法选择和字段配置 | 选择对象、绑定字段、运行样例、解释结果 | 可复用的方法配置与结果解读路径 |
| `/revision` 修订中心 | 管理报告修订与版本任务 | 查询报告、创建修订、追踪任务 | 修订任务、报告库和版本状态 |
| `/revision/workspace` 修订工作区 | 对已有报告持续审阅 | 添加批注与附件、查看事件与差异、发布本地版本 | 审阅上下文、文件差异和版本记录 |

逐项的前置条件、可执行动作、返回结果与接口入口见 [完整功能目录](docs/feature-catalog.zh-CN.md)、[模块使用指南](docs/module-guide.zh-CN.md) 和 [逐页结果说明](docs/page-results.zh-CN.md)。

## 能解决哪些问题

- **经营与管理分析**：将销售、客户、渠道、库存、成本、预算或运营表格转化为可审阅的指标、图表、解释和管理报告材料。
- **统计研究与数据验证**：围绕差异、关联、预测、分群、实验与时间序列问题选择方法，保留字段角色、参数、运行状态和结果文件。
- **数据质量与口径治理**：识别字段类型、缺失值、异常值、重复项和时间连续性，沉淀数据字典与质量证据。
- **报告审阅与迭代交付**：针对既有报告管理批注、附件、事件、差异和本地版本，形成持续可追踪的修订记录。
- **团队方法复用**：将已审阅的 Skill、功能试验、报告 Agent 团队与本机 Codex Runtime 纳入受控任务上下文，减少重复配置成本。

## Analysis Lab 与统计方法

统计目录由后端注册表导出，当前公开版收录 **362 条注册统计方法**，其中 **81 条可运行方法**；Analysis Lab 将可运行方法按输入与输出形态展开为 **4,028 张方法卡**，其中 **273 张可运行卡片**对应 81 个可运行方法概念。

| 方法族 | 可用于回答的问题 | 示例能力 |
| --- | --- | --- |
| 描述统计与汇总 | 数据分布、分组差异、关键指标处于什么水平 | 描述汇总、频数表、列联表、透视汇总、分位数、帕累托、分组 KPI |
| 分布与诊断 | 数据或模型是否满足后续分析条件 | 正态性、方差齐性、异方差、残差自相关、ADF、ACF/PACF |
| 差异与假设检验 | 两组或多组指标差异是否稳定 | t 检验、Z 检验、ANOVA、ANCOVA、Tukey HSD、重复测量分析 |
| 非参数与重采样 | 小样本、偏态或等级数据如何比较 | Mann-Whitney、Wilcoxon、Kruskal-Wallis、Friedman、置换检验、Bootstrap |
| 分类与关联 | 变量之间是否存在关联、关系强度如何 | 卡方、Fisher、McNemar、Cramer's V、Kappa、Pearson、Spearman、Kendall |
| 回归、机器学习与多变量 | 哪些变量驱动结果，如何预测或分群 | OLS、Ridge、Lasso、Elastic Net、Logistic、Poisson、随机森林、神经网络、PCA、KMeans |
| 时间与实验 | 指标是否存在趋势、序列相关或实验差异 | 移动平均、Ljung-Box、ADF、A/B Test |

每张 Lab 方法卡都描述方法 ID、字段角色、输入约束、输出形态、运行状态和来源。运行时可选字段绑定、全表运行或重点对象运行；产物可包含 JSON、CSV、XLSX、Markdown、图表、SVG、HTML 或图像规格。

- [统计方法完整目录：中文方法名称、用途、字段角色与运行状态](docs/statistical_methods_zh.md)
- [Analysis Lab 方法卡索引：4,028 张卡片的输入、输出与来源](docs/lab_method_inventory_zh.md)
- [统计方法使用场景：按业务问题寻找合适方法](docs/statistical_methods_zh.md#使用场景与方法选择)
- [方法编辑器教程：对象、字段、实例与结果解释](docs/getting-started.zh-CN.md)

## 正式管理报告：从数据到发布的受控链路

正式 `management_report.pdf` 遵循项目内置的强制处理链：

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

这条链路分别承担数据画像、字段语义映射、业务场景路由、指标派生规划、确定性数值计算、证据验证、报告绑定与发布门控。AI 输出需要留下追溯工件并通过结构校验；数值由确定性执行器计算；缺少必要追溯信息或质量未达到发布要求时，正式报告不会进入发布流程。

[AI 强制链架构说明](docs/architecture_ai_mandatory_chain.zh-CN.md) 与 [报告完整性规则](docs/report-integrity.zh-CN.md) 说明了阶段职责、工件、校验点和发布要求。

## Skill、Feature Trial、Report Agent Team 与 Codex Runtime

Analysis Lab 提供面向本机工作流的扩展层，用于将可复用方法、功能适配性检查和团队角色协作纳入数据分析过程。

| 能力 | 在哪里使用 | 完成后得到的内容 |
| --- | --- | --- |
| Skill | `/lab` 的本地扩展区域 | 已识别或已挂载 Skill 的来源、状态、说明及其受限上下文记录 |
| Feature Trial | `/lab` 的功能试验目录 | `trial_id`、就绪度、原因、字段评分、推荐动作、建议参数与试验工件 |
| Report Agent Team | `/lab` 的团队区域 | 团队与角色摘要、受控工作区、任务 ID、运行状态、日志、摘要或文件差异 |
| Report Agent Session | `/revision/workspace` | 面向已有报告的消息、附件、批注、事件、文件和版本状态 |
| Codex Runtime / Pipeline | Runtime API、Lab 团队任务与修订工作区 | 健康检查、运行 ID、任务状态、日志、摘要、工件与管线记录 |

外部 Skill 与团队包以本机导入的元数据和受限上下文参与工作流。Feature Trial 使用真实数据画像评估功能与字段适配性，并生成可下载的 JSON、CSV 与 Markdown 工件。Report Agent Team 在受控工作区创建任务；Report Agent Session 聚焦既有报告的持续修订。

配置项、来源审阅、导入结构、运行条件、产物与故障排查见 [本地扩展指南](docs/local-extensions.zh-CN.md) 和 [配置参考](docs/configuration-reference.zh-CN.md)。

## 数据、产物与交付

| 环节 | 输入 | 系统处理 | 可查看或下载的结果 |
| --- | --- | --- | --- |
| 数据接入 | CSV、XLSX 等本机文件与工作表 | 文件检查、数据画像、字段推断 | 数据集信息、工作表、字段摘要、质量发现 |
| 方法执行 | 数据集、字段绑定、参数与对象范围 | 运行统计方法或数据资产步骤 | `run_id`、状态、表格、图表、JSON、CSV、XLSX、Markdown |
| 数据资产蓝图 | 业务对象、字段、指标与场景描述 | 定义数据资产与可执行分析配置 | 蓝图、字段角色、指标配置、关联方法 |
| 正式分析 | 分析目标与业务数据 | 语义理解、指标规划、确定性计算、证据验证 | 可追溯的分析结果与报告候选材料 |
| 修订发布 | 已有报告、批注、附件与变更需求 | 任务编排、审阅、差异记录和版本管理 | 版本状态、事件、差异、附件与本地发布记录 |

API 输入输出与结果文件字段见 [API 参考](docs/api-reference.zh-CN.md)，页面级结果说明见 [逐页结果说明](docs/page-results.zh-CN.md)。

## 技术架构

| 层级 | 主要技术 | 职责 |
| --- | --- | --- |
| Web 客户端 | Next.js 16、React 19、TypeScript | 分析工作台、Lab、方法指南、修订与本机设置界面 |
| 服务端 | FastAPI、Pydantic | 数据集、分析、报告、修订、Skill、Trial、Team 与 Runtime API |
| 数据与计算 | Pandas、DuckDB、Statsmodels、scikit-learn | 数据处理、统计计算、机器学习与确定性指标执行 |
| 文件与报告 | OpenPyXL、python-docx、pypdf、ReportLab | 表格、文档、PDF、图表与交付工件处理 |
| 发布与质量 | GitHub Actions、pytest、npm scripts、便携包构建 | 自动测试、前端构建、Windows 便携包冒烟验证与标签发布 |

系统架构、服务边界与关键模块关系见 [架构说明](docs/architecture.zh-CN.md)。

## 中文文档导航

| 主题 | 文档 |
| --- | --- |
| 项目全景、模块和场景 | [公开项目介绍](docs/public-project-introduction.zh-CN.md) |
| 每项可用功能的入口、准备、动作与结果 | [功能目录](docs/feature-catalog.zh-CN.md) |
| 页面操作和结果展示 | [逐页结果说明](docs/page-results.zh-CN.md) |
| 模块职责与协作关系 | [模块使用指南](docs/module-guide.zh-CN.md) |
| 数据分析与报告工作流 | [用户指南](docs/user-guide.zh-CN.md) |
| 统计方法目录、状态与使用场景 | [统计方法完整目录](docs/statistical_methods_zh.md) |
| Lab 方法卡、输入输出与来源 | [Analysis Lab 方法卡索引](docs/lab_method_inventory_zh.md) |
| 从安装到第一次分析 | [快速开始](docs/getting-started.zh-CN.md) |
| 本地 AI、R、Skill、Agent 团队与 Runtime | [本地扩展指南](docs/local-extensions.zh-CN.md) |
| API、请求和返回结构 | [API 参考](docs/api-reference.zh-CN.md) |
| 配置项和环境变量 | [配置参考](docs/configuration-reference.zh-CN.md) |
| AI 强制链与报告发布 | [架构说明](docs/architecture_ai_mandatory_chain.zh-CN.md) |
| 便携版、发布、校验与回滚 | [发布运维指南](docs/release-operations.zh-CN.md) |
| 数据和部署边界 | [安全与部署说明](docs/security-deployment.zh-CN.md) |

完整文档目录见 [docs/README.md](docs/README.md)。

## 持续集成与发布

GitHub Actions 在 `main`、标签和 Pull Request 上运行后端测试、前端 lint、方法指南校验、前端构建、依赖审计和 Windows 便携包冒烟测试。发布标签会构建并上传 `AsteriaAnalyst-portable.zip`，供 Windows 本机用户下载使用。

| 面向使用者 | 面向贡献者 |
| --- | --- |
| 下载 Release、解压、运行 `start-asteria.bat` | Fork 项目、创建分支、提交 PR，并在本机运行测试与构建 |
| 按 [便携版用户指南](docs/portable-user-guide.zh-CN.md) 校验 SHA-256 与启动状态 | 按 [开发指南](docs/development-guide.zh-CN.md) 配置环境、执行 `pytest` 与 `npm run build` |

发布前检查、发布资产、回滚与维护步骤见 [发布运维指南](docs/release-operations.zh-CN.md)。

## 贡献与反馈

欢迎通过 Issue 和 Pull Request 提交缺陷、文档修订、方法目录建议、数据分析场景和集成建议。提交前请阅读 [开发指南](docs/development-guide.zh-CN.md)，并为涉及分析或报告链路的修改补充相应验证。

与数据、依赖、部署和本机运行相关的注意事项见 [安全与部署说明](docs/security-deployment.zh-CN.md)。
