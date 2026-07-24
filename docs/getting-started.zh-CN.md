# Asteria Analyst 使用入门

本文面向首次运行 Asteria Analyst 的用户，说明从数据到 Analysis Lab 结果、正式报告和修订版本的完整操作路径。

## 1. 启动服务

在仓库根目录分别启动后端和前端：

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

```powershell
cd frontend
$env:NEXT_PUBLIC_API_BASE_URL = "http://127.0.0.1:8000"
npm run dev
```

打开 `http://127.0.0.1:3000`。后端健康检查位于 `http://127.0.0.1:8000/health`。

## 2. 导入与检查数据

1. 打开 `/analysis` 或 `/lab`，导入 CSV、XLSX 等数据文件。
2. 在数据集选择器中确认数据集、工作表、行数和字段数量。
3. 在 Lab 的“数据资产蓝图”查看工作表清单、数据质量分、复杂度、关联关系、提醒项和建议分析路径。
4. 按业务含义确认数值字段、分类字段、时间字段、目标字段与分组字段。

字段角色决定方法卡可用的绑定槽位。统计目录中的“所需字段角色”列给出了每种方法的配置条件，详见 [统计方法完整目录](statistical_methods_zh.md)。

## 3. 在 Analysis Lab 运行统计方法

1. 打开 `/lab`，选择数据集与工作表。
2. 从方法目录选择目标方法；Lab 会显示每张卡的用途、字段角色、输出形态与运行控制项。
3. 将字段绑定到目标指标、特征字段、分组字段、时间字段或方法要求的其他角色。
4. 选择运行方式：字段绑定、全表运行或重点对象运行。
5. 执行方法卡，查看文字解读、表格、结构化数据与图表产物。
6. 保留有价值的运行实例，将产物用于报告部件或后续分析。

### 方法卡输出

| 输出 | 用途 |
| --- | --- |
| 文字解读 | 展示方法结论、方向、差异、异常与管理含义。 |
| 表格 | 展示样本量、统计量、检验量、分组结果与中间证据。 |
| 结构化数据 | 提供 JSON、CSV、XLSX 等可复用结果。 |
| 图表与图像规格 | 为趋势、分布、关联、分群等结果提供可视化交付。 |

Lab 完整方法卡索引见 [Analysis Lab 方法卡索引](lab_method_inventory_zh.md)。该索引列出全部卡片 ID、方法概念、输出形态、字段角色、状态与注册来源。

## 4. 使用数据资产蓝图

数据资产蓝图会根据当前数据集生成以下信息：

- 工作表及字段结构；
- 数据质量、缺失、复杂度与风险提醒；
- 可识别的表间关系；
- 推荐分析路径和方法集合；
- 可直接带入 Lab 的方法选择。

推荐路径用于缩短首次选型时间。运行前仍应检查数据口径、样本边界、字段单位与业务解释范围。

## 5. 使用外部 Skill 与 Agent 团队

Lab 支持挂载外部 Skill 和报告 Agent 团队包：

1. 在 Skill 面板查看已发现、已挂载和可试跑的能力。
2. 运行试跑后，使用“用于下一次 Lab 运行”将推荐的数据、字段、方法和报告部件带入工作区。
3. 在 Agent 团队面板选择团队任务，启动后通过“团队任务中心”查看进度、产物和运行状态。
4. 对已完成或中断的任务可在任务中心刷新、取消或重试。

团队任务记录通过 `/api/lab/report-agent-teams/runs` 保存，可用于复盘分析任务的配置与产物。

## 6. 生成正式管理报告

正式报告从 `/analysis` 发起，遵循固定的 AI 与确定性计算链路：

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

报告会保留字段语义、业务路由、指标规划、确定性计算和证据校验 Trace。`FormalPDFReleaseGate` 在质量分达到 `90` 后放行正式 PDF。

## 7. 修订、审阅与发布

1. 在 `/revision` 选择已生成报告，创建修订任务。
2. 在 `/revision/workspace` 添加批注、查看文件变更、跟踪执行状态与审阅内容。
3. 确认修订结果后发布版本，保留版本记录与交付资产。

## 8. 开发验证

```powershell
cd backend
python -m pytest

cd ..\frontend
npm run build
```

统计方法或 Lab 卡片发生变更时，重新导出公开目录：

```powershell
backend\.venv\Scripts\python.exe scripts\export_method_catalog_docs.py
```
