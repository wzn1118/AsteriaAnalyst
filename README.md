# Asteria Analyst

> 本地优先的数据分析与报告交付工作台：从一份结构化数据和一个业务问题，走到可审阅的分析证据、报告资产与修订版本。

[下载 Windows 便携版](https://github.com/wzn1118/AsteriaAnalyst/releases/latest) | [完整模块手册](docs/module-guide.zh-CN.md) | [功能逐项参考](docs/function-reference.zh-CN.md) | [快速开始](docs/getting-started.zh-CN.md) | [详细用户指南](docs/user-guide.zh-CN.md)

## 项目定位

Asteria Analyst 面向经营分析、运营复盘、研究统计和咨询交付场景。它不是一个只根据提示词生成结论的写作工具，而是把数据、业务问题、受控分析、证据、报告和后续修改组织成一条本地可追溯的工作流。

一个典型任务从 CSV、Excel、TSV 或 Stata 数据开始：先确认工作表、行粒度、字段类型、缺失、单位与时间范围；再定义业务问题、目标读者和约束；随后选择受控统计分析或 Analysis Lab 方法实验；最后审阅表格、图表、计算证据与报告资产。需要正式管理报告时，系统还会执行强制 AI 审计链、确定性数值计算、证据校验和 PDF 发布门禁。

| 面向角色 | 主要问题 | Asteria Analyst 提供的能力 |
| --- | --- | --- |
| 经营或运营负责人 | 如何把周期性业务问题变成可讨论的决策材料 | 业务简报、受控分析路径、报告资产与审阅状态 |
| 数据分析师或研究人员 | 如何理解字段、选择方法并保留验证依据 | 数据画像、统计分析、Analysis Lab、方法卡和结果工件 |
| 报告或交付负责人 | 如何处理修改而不丢失上下文和证据 | 修订会话、批注、附件、文件差异和本地版本发布 |
| 工程、治理或审计伙伴 | 如何确认结论来自哪里 | 确定性计算、证据绑定、trace 工件、manifest 和公开边界 |

## 从数据到交付

<pre>
数据、工作表与业务问题
  -> 数据画像与字段语义
  -> 业务路由、指标与方法规划
  -> 受控统计或确定性计算
  -> 证据表、图表与报告部件
  -> 质量检查与下载资产
  -> 批注、修订和版本发布
</pre>

这条路径的重点是可复核性：模型可以帮助理解字段、整理业务上下文和规划指标，但正式数值不能由语言模型编造或定稿。图表、表格、方法结果和报告文本应能回到相应的数据与计算证据。

## 六个工作区

| 工作区 | 路由 | 主要用途 | 使用者会看到什么 |
| --- | --- | --- | --- |
| 首页 | <code>/</code> | 直接开始智能报告任务 | 上传或选择数据、填写需求与背景、生成和下载结果 |
| 正式分析 | <code>/analysis</code> | 受控数据导入、快速统计和智能报告 | 工作表选择、数据画像、业务简报、任务进度、报告资产 |
| Analysis Lab | <code>/lab</code> | 方法探索、比较和可复用分析证据 | 字段角色、派生口径、方法目录、运行实例、方法卡和结果 |
| 方法指南 | <code>/lab/method-guide</code> | 学习如何选择和配置方法 | 重点对象、字段绑定、运行实例、建模输入字段的操作说明 |
| 修订中心 | <code>/revision</code> | 查找既有报告并开始后续工作 | 报告列表、筛选、排序和历史修订会话 |
| 修订工作区 | <code>/revision/workspace</code> | 审阅、批注、比较和发布本地修订版 | HTML/PDF 预览、批注层、事件流、差异、附件和版本状态 |

各工作区的完整功能、对应后端模块和启用条件见 [模块与功能手册](docs/module-guide.zh-CN.md)。

## 能力状态与边界

公开项目把能力明确分为四类，避免用户因按钮或目录而误以为所有能力都无需配置即可运行：

| 状态 | 能力 | 使用条件 |
| --- | --- | --- |
| 默认可用 | 本地数据导入、数据画像、受控统计、智能报告界面、Analysis Lab、方法指南、报告浏览 | 启动本机前后端即可使用；具体分析结果取决于数据质量和方法适配性 |
| 可选配置 | AI 辅助字段语义、业务路由、指标规划、报告与修订增强 | 使用者在本地 <code>.env</code> 中配置兼容的 AI 提供方，并承担相应的数据合规责任 |
| 默认关闭 | Codex Runtime、外部 Skill、本地报告 Agent Team、非沙箱本地执行、Codex 搜索 | 仅可信本机的管理员在明确授权后通过服务端环境变量启用 |
| 受发布门禁约束 | 正式 <code>management_report.pdf</code> | 必须完成 AI trace、schema 校验、确定性数值、证据校验和质量门禁；最终分数低于 90 不得发布 |

公共版不会在浏览器中要求或保存 API Key，也不把任意 Python/R 脚本执行作为普通用户功能。运行时密钥和执行策略由本地服务端配置管理。

## 功能概览

### 1. 数据导入、工作簿与数据画像

- 支持 CSV、TSV、Excel（<code>.xlsx</code>）和 Stata（<code>.dta</code>）数据；前端导入界面也接受 <code>.xls</code>。
- 识别 Excel 多工作表、合并单元格、稀疏或多行表头，并允许切换分析工作表。
- 返回行列规模、数值/类别/日期字段、缺失值、字段摘要、样本行与可视化建议。
- 大数据集的浏览器预览和图表采用采样控制响应速度；完整数据仍可用于后续计算。
- 历史报告和业务背景材料可作为分析上下文，但不会替代原始数据或成为未经验证的事实来源。

### 2. 受控统计分析

- 描述统计、频数、交叉表、透视表、分位数、截尾处理、基尼、帕累托和 KPI。
- 相关与关系分析，如 Pearson、Spearman、Kendall、偏相关、距离相关和分类关联。
- 回归与广义线性模型，如 OLS、岭回归、Lasso、Elastic Net、稳健/分位数回归、Logit、Poisson 及部分诊断。
- 组间比较、A/B 测试、方差分析、分类检验、非参数检验、Bootstrap 和置换检验。
- PCA、K-Means、随机森林、基础神经网络、正态性和部分时间序列方法。

方法目录可用于检索与路由，但目录中出现的方法名称不等于当前发布版的每一项都已经实现为可执行引擎。统计结果必须结合样本量、数据类型、方法假设与业务口径解释，相关或模型结果本身不等于因果结论。

### 3. 智能报告工作台

- 导入数据后选择一个或多个工作表，并按单表、合并、分别或组合方式组织多表分析。
- 填写报告要回答的问题、目标读者、核心用途、期望结果和关键约束，让交付围绕业务问题而非单纯字段摘要。
- 可选运行相关矩阵、OLS、随机森林、K-Means、PCA、正态性检验等受控快速统计。
- 可选择报告深度、视觉风格、视觉说明、交付目标和全文表格偏好。
- 提交任务后查看进度、结构化章节、关键指标、图表、表格和可下载资产；实际产物由数据、路线和执行结果决定。

### 4. Analysis Lab 方法实验台

- 通过数据准备、字段画像、字段角色和派生指标口径组织分析实验。
- 按目标、分组、标签、时间、特征、重点对象和图形字段配置运行输入。
- 搜索和筛选方法目录，建立独立运行实例，避免不同对象或不同字段配置互相覆盖。
- 支持合并运行、单方法独立运行、批量独立运行，以及进入正式报告链路的试跑对照。
- 结果可呈现分析摘要、指标、图表、表格、文本、方法前置审计与可重跑的报告部件蓝图（若该结果提供）。

Analysis Lab 用于探索、验证和方法比较，不能绕过正式管理报告的发布门禁。

### 5. 报告修订与版本工作区

- 在报告库中按关键词、数据集或业务画像筛选既有报告，并创建或恢复修订会话。
- 通过自由修改意见或快捷修改任务发起续改，使用事件流和轮询显示进度。
- 在 HTML/PDF 之间切换预览，支持刷新、新窗口查看、缩放、翻页、整页和适宽模式。
- 支持浏览、画笔、矩形、高亮和橡皮批注；可将批注和修改说明作为修订指令。
- 查看产物、附件、批注、文件差异和已发布本地版本；必要时查看任务、CLI 管线、Codex 回合和恢复信息。

修订工作区中的“发布”仅指本地报告版本的发布，不等同于 GitHub 发布或互联网部署，也不会解除正式报告的 AI 强制链与质量门禁。

### 6. 专项路线与本地扩展

项目包含按数据和业务路由选择的电商经营、互联网运营、采购销售、通用深度经营、市场情报、媒体决策、管理会计和独立行业研究等专项服务。它们是可命中的专项路线，不表示任何数据集都会自动进入某一行业模板。

R 工作流、Codex Runtime、外部 Skill、实验特性和本地报告 Agent Team 也位于项目中，但并非便携版的默认保证能力。R 需要本机可用的 <code>Rscript</code>；Codex 和本地扩展默认关闭，只能在可信本地环境中由管理员显式启用。

## 正式管理报告的可信机制

正式 <code>management_report.pdf</code> 必须完整通过以下链路：

<pre>
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
</pre>

- <code>AIFieldSemanticMapper</code>、<code>AIBusinessContextRouter</code> 和 <code>AIMetricDerivationPlanner</code> 必须在正式报告绑定前执行，并写入可追溯工件。
- AI 输出必须通过 schema 校验；AI 用于结构化理解和规划，不生成最终数值。
- <code>DeterministicMetricExecutor</code> 负责实际数值计算；<code>EvidenceValidator</code> 校验输入、计算和绑定证据。
- 缺少或无效的 AI trace 时，最多只能生成 <code>debug_report</code> 用于诊断，禁止发布正式 <code>management_report.pdf</code>。
- 最终质量分低于 90 时，同样禁止正式 PDF 发布。

更多细节见 [正式报告可信机制](docs/report-integrity.zh-CN.md)、[AI 强制发布链（中文）](docs/architecture_ai_mandatory_chain.zh-CN.md) 与 [英文原始规范](docs/architecture_ai_mandatory_chain.md)。

## 快速开始

### Windows 便携版

1. 从 [GitHub Releases](https://github.com/wzn1118/AsteriaAnalyst/releases/latest) 下载 <code>AsteriaAnalyst-portable.zip</code>。
2. 完整解压到可写目录，不要在压缩包预览器中直接运行。
3. 双击解压目录中的 <code>start-asteria.bat</code>。
4. 等待启动窗口显示实际本地地址并自动打开工作区。

便携版面向 Windows 本机单用户使用，不是公网托管服务。

### 源码版

前置条件：Python 3.11+、Node.js 20.9+，且首次启动可以连接依赖源。

1. 克隆或解压本仓库。
2. 在仓库根目录双击 <code>start-asteria.cmd</code>。
3. 启动器会检查后端与前端、准备依赖、启动仅绑定 <code>127.0.0.1</code> 的服务、打开 <code>/analysis</code>，并在 <code>logs/launcher/</code> 写入日志。
4. 默认前端地址为 <code>http://127.0.0.1:3000/analysis</code>，后端健康检查为 <code>http://127.0.0.1:8000/health</code>。若端口已占用，启动器会选择附近可用端口并打印实际地址。

基础本地分析不要求 API Key。需要 AI 辅助功能时，从 <code>.env.example</code> 创建本地 <code>.env</code> 并填写自己的兼容提供方配置；绝不要把 <code>.env</code>、密钥、真实数据或生成报告提交到 GitHub。

完整的首次启动、配置和排障说明见 [快速开始](docs/getting-started.zh-CN.md)。

## 推荐使用流程

1. **先核对数据**：上传小型、非敏感样本或 <code>examples/revenue-smoke.csv</code>，确认行粒度、字段、缺失、单位和时间范围。
2. **说明业务问题**：写清希望解释、比较或决策的事项，以及报告读者和约束。
3. **选择正确工作区**：需要探索和比较方法时使用 Lab；需要受控报告路径时使用正式分析；已有报告要续改时进入修订中心。
4. **先审阅证据再读摘要**：依次检查方法/计算结果、表格与图表、文字总结和下载资产。
5. **确认交付等级**：只有全部门禁通过的 <code>management_report.pdf</code> 才是正式管理报告；其他结果是探索性、调试性或修订性材料。

## 数据、隐私与公开边界

- 基础 CSV/Excel 工作可以在本机完成，不要求外部模型提供方。
- 若主动启用 AI 辅助报告或修订，相关字段上下文、报告上下文或上传的工作簿/PDF 可能发送给本地配置的 OpenAI-compatible 提供方。请先脱敏，并遵循数据授权、合同和组织政策。
- 默认部署仅适合回环地址的单用户使用。当前项目没有面向公网多用户的身份认证、租户隔离和生产托管承诺；不要直接暴露到公共网络或共享网络。
- <code>/storage</code> 可提供本地生成工件。公开截图、Issue、演示和提交前都应检查是否含有客户、个人、商业或运行时敏感信息。

非本机部署前，请先阅读 [部署边界](docs/deployment-boundaries.md) 与 [安全策略](SECURITY.md)。

## 文档索引

- [中文技术文档中心](docs/README.md)
- [系统架构](docs/architecture.zh-CN.md)
- [API 参考](docs/api-reference.zh-CN.md)
- [配置参考](docs/configuration-reference.zh-CN.md)
- [开发与质量指南](docs/development-guide.zh-CN.md)
- [安全与部署说明](docs/security-deployment.zh-CN.md)
- [发布与运维指南](docs/release-operations.zh-CN.md)
- [Windows 便携版离线指南](docs/portable-user-guide.zh-CN.md)
- [便携版 Codex Runtime（中文）](docs/portable-codex-runtime.zh-CN.md)
- [完整模块与功能手册](docs/module-guide.zh-CN.md)
- [功能逐项参考：页面、操作、接口、产物与边界](docs/function-reference.zh-CN.md)
- [逐页结果说明：完成后看到什么、得到什么、下一步做什么](docs/page-results.zh-CN.md)
- [公开项目介绍](docs/public-project-introduction.zh-CN.md)
- [快速开始](docs/getting-started.zh-CN.md)
- [详细用户指南](docs/user-guide.zh-CN.md)
- [正式报告可信机制](docs/report-integrity.zh-CN.md)
- [AI 强制发布链（中文）](docs/architecture_ai_mandatory_chain.zh-CN.md)（[English](docs/architecture_ai_mandatory_chain.md)）
- [贡献指南](CONTRIBUTING.md)
- [安全策略](SECURITY.md)

## 公开仓库范围与许可证

本仓库公开源码、测试、启动脚本、示例和技术文档；不应包含客户资料、上传数据、生成报告、运行会话、日志、缓存、凭据和私有作品集材料。

仓库公开可见不等于已授予复制、修改、再分发或商用许可。目前尚未选择开源许可证；在所有者添加 <code>LICENSE</code> 前，请不要把项目当作已获开源授权的软件。
