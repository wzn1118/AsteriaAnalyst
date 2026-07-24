# Asteria Analyst

Asteria Analyst 是面向业务分析、统计建模与管理报告交付的本地分析工作台。项目将数据接入、字段理解、分析方案、确定性计算、证据校验、报告生成、审阅修订与版本发布串成可追溯流程。

## 统计方法与 Analysis Lab

GitHub 中的统计方法说明以当前后端注册表为准，包含方法状态、字段角色、核心问题、Lab 卡片与运行产物。

| 目录 | 内容 | 当前规模 |
| --- | --- | ---: |
| [统计方法完整目录](docs/statistical_methods_zh.md) | 每个统计方法的 ID、用途、字段角色和可运行状态 | 362 条注册方法，81 条可运行方法 |
| [Analysis Lab 方法卡索引](docs/lab_method_inventory_zh.md) | Lab 中所有卡片的 ID、方法概念、输出形态、字段角色、状态和来源 | 4,028 张方法卡 |
| [方法编辑器教程](docs/getting-started.zh-CN.md) | 从对象、字段、实例到结果解释的操作步骤 | 面向首次运行 |

可运行统计方法在 Lab 中按输出形态展开为独立卡片，可使用字段绑定、全表运行或重点对象运行模式。方法卡会保留运行配置与产物合约；默认产物包含 JSON、CSV、XLSX、Markdown，图表型方法还可提供图表、SVG、HTML 或图像规格。

### 可运行方法覆盖范围

- **描述统计**：描述汇总、频数表、列联表、透视汇总、分位数、截尾与缩尾统计、基尼系数、帕累托、分组 KPI。
- **分布与假设诊断**：正态性、Shapiro-Wilk、D'Agostino K²、Jarque-Bera、KS、Anderson-Darling、方差齐性、异方差与残差自相关。
- **差异检验**：Welch t 检验、配对 t 检验、单样本 t 检验、Z 检验、单因素/双因素/重复测量 ANOVA、ANCOVA、Welch ANOVA、Tukey HSD。
- **非参数检验**：Mann-Whitney、Wilcoxon、符号检验、Kruskal-Wallis、Friedman、中位数检验、置换检验与 Bootstrap 置信区间。
- **分类与关联**：卡方、Fisher、McNemar、Cochran Q、CMH、Cramer's V、Phi、Theil's U、Kappa、Pearson、Spearman、Kendall、偏相关、距离相关。
- **回归、机器学习与多变量**：OLS、Ridge、Lasso、Elastic Net、Logistic、Poisson、分位数和稳健回归；随机森林、神经网络、深度网络；PCA 与 KMeans。
- **时间与实验**：移动平均、ACF/PACF、Ljung-Box、ADF；A/B Test。

完整 ID、用途、输入字段和状态请以 [统计方法完整目录](docs/statistical_methods_zh.md) 为准。

## 产品模块

| 页面 | 路径 | 用途 |
| --- | --- | --- |
| 首页 | `/` | 项目导航、运行状态与本地 AI Provider 设置。 |
| 正式分析 | `/analysis` | 数据导入、分析目标配置、正式分析运行与报告预览。 |
| Analysis Lab | `/lab` | 选择统计方法、配置字段、运行方法卡、查看产物、加载数据资产蓝图、调用外部 Skill 与 Agent 团队。 |
| 方法指南 | `/lab/method-guide` | 方法选择、字段绑定、运行实例与结果解释教程。 |
| 修订中心 | `/revision` | 查询报告库、创建修订任务并管理交付版本。 |
| 修订工作区 | `/revision/workspace` | 标注报告、审阅文件改动、跟踪 AI 执行并发布版本。 |

## 分析与报告链路

正式管理报告遵循以下固定链路：

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

AI 负责字段语义、业务路由与分析规划；数值计算由确定性执行器完成。每个正式报告保留 AI Trace、结构化校验结果、计算证据与发布门禁结果。质量分数达到 `90` 后，`FormalPDFReleaseGate` 才会放行正式 PDF。

## 技术结构

```text
backend/    FastAPI API、分析编排、统计执行、证据校验、报告与修订服务
frontend/   Next.js 产品界面、分析工作区、Analysis Lab 与报告修订界面
docs/       架构说明、统计目录、Lab 索引、工作流与产品文档
scripts/    验证、打包与方法目录导出脚本
skills/     可挂载的分析与报告能力定义
winui/      Windows 本地客户端与打包配置
```

核心依赖包括 Next.js、React、FastAPI、Pandas、DuckDB、statsmodels、scikit-learn、ECharts、SheetJS 与 Monaco Editor。

## 本地启动

环境建议：Python 3.11+、Node.js 20+。

### 1. 启动后端

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

健康检查：`http://127.0.0.1:8000/health`

### 2. 启动前端

```powershell
cd frontend
npm ci
$env:NEXT_PUBLIC_API_BASE_URL = "http://127.0.0.1:8000"
npm run dev
```

打开 `http://127.0.0.1:3000`，Analysis Lab 位于 `http://127.0.0.1:3000/lab`。

## API 入口

| API | 用途 |
| --- | --- |
| `GET /health` | 后端存活检查。 |
| `GET /api/statistics/catalog` | 统计方法注册表与统计摘要。 |
| `GET /api/lab/methods?compact=true` | Analysis Lab 方法卡目录。 |
| `GET /api/lab/skills` | 可挂载外部 Skill。 |
| `GET /api/lab/report-agent-teams` | Agent 团队包目录。 |
| `GET /api/lab/report-agent-teams/runs` | Agent 团队运行记录。 |

## 更新公开方法文档

新增、调整统计方法或 Lab 卡片后，在仓库根目录执行：

```powershell
backend\.venv\Scripts\python.exe scripts\export_method_catalog_docs.py
```

该命令会同步更新：

- `docs/statistical_methods_zh.md`
- `docs/lab_method_inventory_zh.md`

## 验证

```powershell
cd backend
python -m pytest

cd ..\frontend
npm run build
```

更多架构说明见 [AI 强制发布链路](docs/architecture_ai_mandatory_chain.md)、[产品概览](docs/product_overview_zh.md) 与 [GitHub 发布说明](docs/github-market-stack.md)。
