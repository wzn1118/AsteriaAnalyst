# 正式报告可信机制

本文件解释 Asteria Analyst 如何区分“生成结果”和“允许正式发布”。它面向报告负责人、业务审阅者、分析师和贡献者，并与项目中的 [AI 强制发布链](architecture_ai_mandatory_chain.md) 配套使用。

## 探索结果与正式报告采用不同发布标准

| 输出类型 | 目的 | 是否可作为正式管理材料 |
| --- | --- | --- |
| Analysis Lab 结果 | 探索方法、比较结果、发现问题、生成方法级资产 | 用于探索和复核；正式发布需进入完整发布链。 |
| `debug_report` | 诊断任务、检查不完整输入或质量问题 | 用于定位问题和继续复核。 |
| `management_report.pdf` | 经过受控链路和质量门的正式管理报告 | 全部发布条件齐备后，由门禁放行。 |

正式发布以证据、trace、schema、确定性计算和门禁结果为准。页面预览和模型生成文字用于审阅与辅助判断。

## 强制发布链

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

### 各阶段的发布职责

| 阶段 | 输入 | 主要输出 | 发布价值 |
| --- | --- | --- | --- |
| DataProfileService | 原始数据 | 字段、类型、缺失、候选对象和工作表结构 | 为粒度和字段确认提供统一画像 |
| AIFieldSemanticMapper | 数据画像 | 字段语义映射和 trace | 形成可审计的字段业务含义 |
| AIBusinessContextRouter | 语义与业务背景 | 业务路由和 trace | 将数据置于匹配的行业和报告框架 |
| AIMetricDerivationPlanner | 路由和字段 | 指标规划和 trace | 明确直接、推导、代理和待验证指标 |
| DeterministicMetricExecutor | 已验证规划与数据 | 实际数值计算结果 | 提供可复算的最终数值来源 |
| EvidenceValidator | 计算结果与 AI 输出 | 证据和 schema 校验状态 | 将有效证据和结构送入报告绑定 |
| ReportBindingLayer | 已验证解释、指标和证据 | 可渲染的报告绑定结构 | 将已验证事实装配为报告模型 |
| FormalPDFReleaseGate | 全部链路状态 | 放行或拦截决定 | 依据完整发布条件给出交付结论 |

## AI 的职责与正式发布条件

AI 在以下阶段提供支持：

- 理解字段名称和候选业务角色；
- 根据业务背景选择分析框架；
- 规划哪些指标是直接、推导、代理、假设或暂不支持的；
- 组织已经验证的表达和报告结构。

正式发布中的 AI 输出满足以下条件：

- 最终数值由确定性执行器产生；
- 事实性解释具有数据支持和可验证证据；
- 正式发布前提供 trace 和 schema 校验结果；
- PDF 渲染阶段消费已完成的字段理解、业务路由和指标规划结果。

正式数值必须由 `DeterministicMetricExecutor` 或等价的确定性执行路径产生。

## 正式发布条件

正式 `management_report.pdf` 在以下条件齐备后由门禁释放：

- AIFieldSemanticMapper、AIBusinessContextRouter 和 AIMetricDerivationPlanner 均已执行；
- 三个 AI 阶段都有持久化 trace；
- AI 输出通过 schema 验证；
- 所有正式数值来自确定性执行；
- 证据校验通过；
- ReportBindingLayer 只消费已经理解、验证和绑定的内容；
- FormalPDFReleaseGate 放行；
- 最终质量分数不低于 `90`。

门禁遇到缺失或校验失败时输出诊断结论：

- 使用 `debug_report` 定位数据、口径、规划、证据或质量问题；
- 完成修复后重新运行完整链路；
- 正式报告以门禁放行记录、trace、schema、确定性计算和证据校验为依据。

## 用户如何审阅可信性

在把结果作为正式材料发送前，报告负责人应检查：

1. **数据范围**：数据集、工作表、时间范围、行粒度和单位是否正确。
2. **字段解释**：关键字段的业务含义是否经过业务方确认。
3. **指标口径**：哪些是直接指标、哪些是推导指标、哪些只是待验证假设。
4. **计算证据**：数值、筛选条件、分组和图表是否能互相对应。
5. **trace 和 schema**：AI 辅助步骤是否具有有效的可追踪输出。
6. **发布状态**：正式发布门禁和最终质量状态是否明确通过。
7. **表达边界**：相关性、样本观察和业务推测是否被错误表述为因果或保证。

## Analysis Lab 与正式报告的关系

Analysis Lab 很重要，但它的目标是学习、试验和复核方法。你可以在 Lab 中：

- 比较适合的数据处理或统计方法；
- 查看方法级表格、图表和结构化资产；
- 发现异常、数据质量问题或值得继续验证的假设；
- 将已验证的方法结果带入下一轮业务讨论。

Lab 结果进入正式管理报告时，完整强制链路和质量门持续生效。

## 常见问题

### “图表和摘要生成后，还需要哪些发布验证？”

图表和摘要展示任务生成的可见结果。正式发布还验证字段理解、数值可靠性、证据完整性和发布质量。

### “AI 已经解释了数据，为什么还要计算？”

字段解释和业务规划属于语义问题；最终数值属于计算问题。前者可以使用 AI 辅助，后者必须可重复、可核查地执行。

### “质量分低于 90，可以先发后改吗？”

质量分低于阈值的结果用于诊断和改进；正式 `management_report.pdf` 的质量分须达到发布阈值。

### “能否手动修改 PDF 后当作正式版本？”

任何影响数值、结论、证据或发布状态的修改均通过受控工作流重新验证，并重新生成 trace、证据和质量门结果。

## 贡献者约束

贡献者通过以下规则维护发布链：

- 正式报告使用完整的 `raw data -> ... -> management_report.pdf` 链路；
- 字段理解、业务路由和指标规划在渲染前完成；
- 完整 AI trace、证据、schema 和门禁结果进入正式发布决策；
- LLM 提供解释、规划和归类，确定性执行器写入最终数值。

修改报告链路后，应运行后端测试和前端构建，并阅读 [AGENTS.md](../AGENTS.md) 与 [AI 强制发布链](architecture_ai_mandatory_chain.md)。
