# AI 强制发布链（中文技术契约）

> 英文原始规范：[AI Mandatory Chain Architecture](architecture_ai_mandatory_chain.md)。本文件面向中文使用者、开发者和审计人员说明同一套不可绕过的正式报告发布规则；两份文件的要求必须保持一致。

## 1. 适用范围与术语

本契约只约束正式的 `management_report.pdf`。普通页面预览、分析草稿和 `debug_report` 保持各自的探索或诊断用途，满足全部发布条件后方可形成正式管理报告。

- **正式报告**：通过全部发布门禁、可对外交付的 `management_report.pdf`。
- **调试报告**：用于开发、诊断或人工复核的 `debug_report`；正式发布资格由完整发布链和门禁结果决定。
- **AI trace**：AI 字段语义、业务路由和指标规划阶段留下的可审计持久化记录。
- **确定性计算**：同一组合法输入在同一规则下可重复验证的数值计算；最终数值由确定性执行器产生。
- **绑定层**：把经验证的语义、指标和证据组织为渲染器可消费的报告数据结构，字段理解和业务路由在绑定前完成。

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

顺序是发布条件的一部分。正式管理报告始终从完整链路获得数据、语义、指标、证据和门禁结论。

## 3. 各阶段职责、输入与输出

### 3.1 DataProfileService

**输入**：原始上传数据、工作表信息和可读取的结构元数据。

**输出**：字段清单、类型、缺失情况、候选对象、工作表概览等结构化画像。

**发布作用**：为字段语义、业务路由和指标规划提供结构化输入。

### 3.2 AIFieldSemanticMapper

**输入**：数据画像与受控上下文。

**输出**：结构化字段语义映射及其 trace。

**强制要求**：正式发布前必须执行；输出必须在进入下游前通过约束的 schema 校验。文本解释不足以作为可发布依据。

### 3.3 AIBusinessContextRouter

**输入**：已校验的字段语义、数据画像和受控业务上下文。

**输出**：业务画像、适用的分析/报告链路和 trace。

**强制要求**：该阶段必须执行。字段名相似、规则默认值和前端选择均须形成可审计的路由结果。

### 3.4 AIMetricDerivationPlanner

**输入**：经路由的业务上下文、字段语义和数据画像。

**输出**：指标派生计划，明确哪些指标为直接指标、派生指标、代理指标、假设或不受支持项，并保存 trace。

**发布作用**：规划器输出计算方法和证据需求；最终数值由确定性执行器生成。

### 3.5 DeterministicMetricExecutor

**输入**：schema 有效的指标计划、原始数据和受控计算规则。

**输出**：可复算的最终数值、计算输入和执行结果。

**强制要求**：正式报告中出现的所有数值均必须来自此阶段或同等的确定性执行器。LLM 输出用于解释、规划或归类；最终数字来源为确定性执行器。

### 3.6 EvidenceValidator

**输入**：AI 输出、确定性指标结果、来源字段和证据绑定信息。

**输出**：校验结论与阻断原因。它检查 schema、计算输入、证据关联和不受支持声明是否成立。

**发布作用**：完整、有效且受支持的证据进入正式发布；缺失或畸形证据由门禁记录阻断原因。

### 3.7 ReportBindingLayer

**输入**：经验证的语义、路由、指标、证据和报告结构。

**输出**：供 HTML/PDF 渲染器消费的已绑定报告模型。

**发布作用**：该层将已验证内容绑定为报告模型；字段角色、业务路由、指标设计和数值计算在绑定前完成。

### 3.8 FormalPDFReleaseGate

**输入**：整条链的完成状态、trace、schema 校验、确定性执行、证据校验和质量结果。

**输出**：允许正式发布或给出阻断原因。

**硬门槛**：最终质量分达到 `90`，并且全部必经步骤和验证结果齐备时，门禁放行 `management_report.pdf`。

## 4. 正式发布规则

1. `AIFieldSemanticMapper`、`AIBusinessContextRouter` 和 `AIMetricDerivationPlanner` 均为正式发布必经阶段。
2. 每个 AI 阶段必须写入可追溯的持久化 trace，且输出在下游使用前通过 schema 校验。
3. `DeterministicMetricExecutor` 写入最终数值；LLM 输出用于解释、规划和归类。
4. `EvidenceValidator` 必须验证计算输入、证据绑定和 AI 输出的可用性。
5. PDF/HTML 渲染器消费已绑定内容；字段理解、业务路由、指标规划和证据校验在渲染前完成。
6. [report_service.py](../backend/app/services/report_service.py) 通过完整强制链生成正式报告。
7. `debug_report` 用于 trace 缺失或诊断场景；正式 `management_report.pdf` 以完整 trace 和门禁放行为依据。

## 5. 不形成正式报告的路径

- `raw data -> renderer -> management_report.pdf`
- 确定性计算后直接生成正式 PDF，缺少 AI 语义、路由和指标规划。
- AI 文本直接生成正式 PDF，缺少确定性计算。
- 渲染阶段依据字段名重新推断业务含义或补写指标。
- 诊断产物以正式报告名称或正式报告入口交付。
- 质量分、trace、schema 或证据条件未齐备时的正式 PDF。

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

当任一项缺失时，发布门禁输出“正式报告不可发布”。正式发布以可验证证据为依据，说明文字提供业务上下文。

## 7. 代码和文档变更要求

- 修改报告服务、AI 编排、指标执行、证据校验、绑定层或 PDF 渲染前，先阅读根目录 [AGENTS.md](../AGENTS.md)。
- 新增或变更阶段时，同时更新本文件、英文原始规范、[正式报告可置信机制](report-integrity.zh-CN.md) 和自动化测试。
- 新增诊断路径时，明确产物为调试输出，并由测试验证 `FormalPDFReleaseGate` 的持续生效。
- 对外文档将页面预览、调试输出和正式报告分别标注其用途与发布状态。

本契约定义公开版正式报告的可信边界；产品体验、文档和实现共同维持这些发布条件。
