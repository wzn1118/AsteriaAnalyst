# AI 强制发布链（中文技术契约）

> 英文原始规范：[AI Mandatory Chain Architecture](architecture_ai_mandatory_chain.md)。本文件面向中文使用者、开发者和审计人员说明同一套不可绕过的正式报告发布规则；两份文件的要求必须保持一致。

## 1. 适用范围与术语

本契约只约束正式的 `management_report.pdf`。它不把普通页面预览、分析草稿或 `debug_report` 自动升级为正式管理报告。

- **正式报告**：通过全部发布门禁、可对外交付的 `management_report.pdf`。
- **调试报告**：用于开发、诊断或人工复核的 `debug_report`；它不具备正式发布资格。
- **AI trace**：AI 字段语义、业务路由和指标规划阶段留下的可审计持久化记录。
- **确定性计算**：同一组合法输入在同一规则下可重复验证的数值计算；最终数值不得由 LLM 编造。
- **绑定层**：把经验证的语义、指标和证据组织为渲染器可消费的报告数据结构，而不是在渲染时重新理解数据。

## 2. 唯一允许的正式发布链

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

顺序是发布条件的一部分。任何从原始数据、页面状态、LLM 文本或渲染器直接跳到 `management_report.pdf` 的实现，均不符合本项目的正式发布规则。

## 3. 各阶段职责、输入与输出

### 3.1 DataProfileService

**输入**：原始上传数据、工作表信息和可读取的结构元数据。

**输出**：字段清单、类型、缺失情况、候选对象、工作表概览等结构化画像。

**边界**：它可以描述数据结构，但不能单独确定业务语义，也不能代替后续 AI 语义、业务路由或指标规划。

### 3.2 AIFieldSemanticMapper

**输入**：数据画像与受控上下文。

**输出**：结构化字段语义映射及其 trace。

**强制要求**：正式发布前必须执行；输出必须在进入下游前通过约束的 schema 校验。文本解释不足以作为可发布依据。

### 3.3 AIBusinessContextRouter

**输入**：已校验的字段语义、数据画像和受控业务上下文。

**输出**：业务画像、适用的分析/报告链路和 trace。

**强制要求**：不得跳过。字段名相似、规则默认值或前端选择均不能替代该阶段的可审计路由结果。

### 3.4 AIMetricDerivationPlanner

**输入**：经路由的业务上下文、字段语义和数据画像。

**输出**：指标派生计划，明确哪些指标为直接指标、派生指标、代理指标、假设或不受支持项，并保存 trace。

**边界**：规划器可以提出计算方法和证据需求，但不能产生最终数值，更不能用语言模型猜测缺失数字。

### 3.5 DeterministicMetricExecutor

**输入**：schema 有效的指标计划、原始数据和受控计算规则。

**输出**：可复算的最终数值、计算输入和执行结果。

**强制要求**：正式报告中出现的所有数值均必须来自此阶段或同等的确定性执行器。LLM 输出只能解释、规划或归类，不能作为最终数字来源。

### 3.6 EvidenceValidator

**输入**：AI 输出、确定性指标结果、来源字段和证据绑定信息。

**输出**：校验结论与阻断原因。它检查 schema、计算输入、证据关联和不受支持声明是否成立。

**边界**：发现缺失、畸形或不受支持证据时必须阻断正式发布，不能通过静默默认值补齐。

### 3.7 ReportBindingLayer

**输入**：经验证的语义、路由、指标、证据和报告结构。

**输出**：供 HTML/PDF 渲染器消费的已绑定报告模型。

**边界**：该层负责绑定，不负责重新推断字段角色、路由业务、设计指标或修改数值。

### 3.8 FormalPDFReleaseGate

**输入**：整条链的完成状态、trace、schema 校验、确定性执行、证据校验和质量结果。

**输出**：允许正式发布或给出阻断原因。

**硬门槛**：最终质量分必须 `>= 90`；低于 `90`、任何必经步骤缺失或验证失败时，均不得释放 `management_report.pdf`。

## 4. 不可绕过的规则

1. `AIFieldSemanticMapper`、`AIBusinessContextRouter` 和 `AIMetricDerivationPlanner` 均为正式发布必经阶段。
2. 每个 AI 阶段必须写入可追溯的持久化 trace，且输出在下游使用前通过 schema 校验。
3. 最终数值必须由 `DeterministicMetricExecutor` 执行；LLM 不得编造、补全或最终裁定数字。
4. `EvidenceValidator` 必须验证计算输入、证据绑定和 AI 输出的可用性。
5. PDF/HTML 渲染器只能忠实渲染已绑定内容，不得承担字段理解、业务路由、指标规划或证据修复。
6. [report_service.py](../backend/app/services/report_service.py) 不得以任何快捷路径绕过这条链。
7. 缺失 AI trace 时，系统最多可以产出 `debug_report`，绝不能产出正式 `management_report.pdf`。

## 5. 明确禁止的实现方式

- `raw data -> renderer -> management_report.pdf`
- 只做确定性计算、跳过 AI 语义/路由/规划后直接发布
- 只使用 AI 文本、没有确定性计算后直接发布
- 在渲染器中根据字段名猜测业务含义或补写指标
- 出错后静默降级，却仍把产物命名或暴露为正式报告
- 质量分不足、trace 丢失、schema 无效或证据不足时继续放行

## 6. 审计与验收清单

发布前，审计者至少应能定位以下证据：

| 检查项 | 必须存在的证据 |
| --- | --- |
| 数据画像 | 字段、类型、缺失情况和工作表概览 |
| 语义映射 | 结构化映射、schema 校验结果和 trace |
| 业务路由 | 路由结论、输入依据和 trace |
| 指标规划 | 指标类别、计算计划、限制声明和 trace |
| 最终数值 | 可复算的确定性执行记录 |
| 证据有效性 | EvidenceValidator 的通过/阻断结果 |
| 报告绑定 | 报告模型只引用经过验证的内容 |
| 发布结论 | FormalPDFReleaseGate 的允许/拒绝结果与质量分 |

当任一项无法提供时，正确结论是“正式报告不可发布”，而不是以说明文字替代证据。

## 7. 代码和文档变更要求

- 修改报告服务、AI 编排、指标执行、证据校验、绑定层或 PDF 渲染前，先阅读根目录 [AGENTS.md](../AGENTS.md)。
- 新增或变更阶段时，同时更新本文件、英文原始规范、[正式报告可置信机制](report-integrity.zh-CN.md) 和自动化测试。
- 新增降级路径时，必须明确其产物只能是调试输出，且测试证明它无法绕过 `FormalPDFReleaseGate`。
- 对外文档不得把“页面能预览”描述成“正式报告已可发布”。

本契约是公开版的安全与可信边界之一；任何与它冲突的产品便利性要求，都不能放宽正式报告发布条件。
