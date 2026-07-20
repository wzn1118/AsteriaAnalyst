# 本地扩展指南：Skill、Report Agent Team 与 Codex Runtime

> 适用入口：Analysis Lab <code>/lab</code>、报告修订工作区 <code>/revision/workspace</code>，以及本机 Runtime API。基础数据导入、受控统计和 Analysis Lab 不需要开启本页所述扩展。

Skill、Report Agent Team 和 Codex Runtime 是项目已经提供的本机扩展能力，不是“预告功能”。它们默认关闭的原因是这些能力会读取本机文件、保存运行工件，或调用本机 Codex CLI；关闭不表示功能不存在。公开版把它们设计为由可信本机管理员主动启用、审阅来源、选择最小工作区后使用，而不是把高权限能力自动开放给任何浏览器访问者。

本指南说明每项能力的入口、输入、操作步骤、可见结果、配置条件和失败处理。需要逐页查看基础分析结果时，配合阅读 [逐页结果说明](page-results.zh-CN.md)；需要查看完整 HTTP 契约时，阅读 [API 参考](api-reference.zh-CN.md)。

## 1. 先区分六个概念

| 名称 | 在哪里使用 | 解决什么问题 | 主要输入 | 用户会得到什么 | 不等于什么 |
| --- | --- | --- | --- | --- | --- |
| 内置已挂载 Skill | <code>/lab</code> 与 <code>GET /api/skills/mounted</code> | 查看项目随附或本机 Codex 环境中已经可识别的技能说明 | 已存在的 <code>SKILL.md</code> | 技能名称、来源、挂载状态与说明元数据 | 不会自动安装第三方包或执行技能中的任意命令 |
| 外部 Lab Skill | <code>/lab</code> 的本地扩展区域 | 导入经审阅的技能/插件包，并把其受限说明带入 Lab 分析上下文 | GitHub 仓库 URL 或本机目录 | 已安装包、挂载状态、内嵌 Skill/命令/MCP 元数据 | 不是通用的插件执行器，也不会自动启动包内命令或 MCP 服务 |
| Feature Trial | <code>/lab</code> 的技能功能试验 | 用真实数据评估一个已导入功能是否适合当前任务 | 数据集、工作表、插件、功能、用户目标 | 就绪度、原因、推荐动作、建议的 Lab 参数和 JSON/CSV/Markdown 工件 | 不是任意第三方命令的直接执行 |
| Report Agent Team | <code>/lab</code> 的团队区域 | 把一组本地 Markdown 角色说明交给 Codex 任务使用 | 团队目录、已选数据集、可选报告/工作表、需求 | 团队清单、挂载状态、任务 ID、任务状态和受控工作区 | 不等于修订中心的报告 Agent Session，也不自动生成正式 PDF |
| Report Agent Session | <code>/revision/workspace</code> | 围绕一份已有报告持续修改、查看事件、差异、附件和批注 | 已有报告、会话消息、附件和批注 | 会话事件、文件、差异和本地版本发布状态 | 不等于从 Lab 导入的团队配置 |
| Codex Runtime / Pipeline | 本机 Runtime API、修订工作区和团队任务 | 解析本机 Codex CLI，运行任务、查询日志、取消任务或执行多阶段管线 | 受限工作区、提示词/上下文、CLI 与本机配置 | 健康检查、运行 ID、状态、日志、摘要、文件变化、差异、工件或错误 | 不是托管云服务，也不是绕过工作区限制的系统命令入口 |

### 两种 Agent 的实际区别

| 对比项 | Report Agent Team | Report Agent Session |
| --- | --- | --- |
| 创建位置 | Analysis Lab 的“本地报告 Agent Team”区域 | 修订工作区中针对已有报告创建 |
| 组织方式 | 本地目录中的团队描述和多个角色 Markdown 文件 | 一份报告下的消息、事件、附件、批注和差异 |
| 主要目标 | 为一次受控 Codex 任务提供团队角色与任务上下文 | 对已有报告进行审阅、续改和版本管理 |
| 可见结果 | 团队数量、挂载数、任务 ID/状态、工作区路径与任务结果 | 会话状态、事件流、文件、批注、差异和发布版本 |
| 与正式 <code>management_report.pdf</code> 的关系 | 只能提供辅助任务结果，不能自行放行正式 PDF | 修订和本地发布也不能解除正式报告门禁 |

## 2. 入口与启用条件

### 2.1 页面入口

1. 启动本机服务后打开 <code>/lab</code>。
2. 先选择或上传数据集。Feature Trial 和 Team Run 都需要真实数据集上下文。
3. 在 Lab 的本地扩展区域查看 Skill、功能试验目录和 Report Agent Team。
4. 需要围绕已经生成的报告修改时，进入 <code>/revision/workspace</code>，不要把修订会话误当成 Team Run。

列表和目录接口可以用来展示当前状态；安装、导入、挂载、删除、功能试验和团队启动则需要相应开关。页面出现空列表不表示功能不存在，通常表示尚未导入任何外部包或团队。

### 2.2 操作条件矩阵

| 操作 | 必需条件 | 结果 |
| --- | --- | --- |
| 查看内置已挂载 Skill | 服务已启动 | 返回现有 Skill 的元数据；不会安装新内容 |
| 查看 Lab Skill、试验目录或 Agent Team 列表 | 服务已启动 | 显示已导入条目和可用试验目录；空列表是合法初始状态 |
| 安装、导入、挂载、取消挂载或删除 Skill | <code>ASTERIA_ENABLE_LOCAL_SKILL_INSTALLER=1</code> | 可以管理本机扩展条目 |
| 运行 Feature Trial | 上述开关、已选数据集、有效的插件/功能选择 | 生成一次试验结论及工件 |
| 导入、挂载、取消挂载或删除 Team | <code>ASTERIA_ENABLE_LOCAL_SKILL_INSTALLER=1</code> | 可以管理团队目录 |
| 启动 Team Run | 已挂载团队、已选数据集、<code>ASTERIA_ENABLE_LOCAL_SKILL_INSTALLER=1</code>，且 Runtime 可实际运行 | 创建任务并返回工作区路径和任务状态 |
| 使用通用 Codex Run、任务、日志、取消、管线和学习账本 API | <code>ASTERIA_CODEX_RUNTIME_ENABLED=1</code>、<code>ASTERIA_ENABLE_CODEX_RUNTIME_API=1</code>、可用 CLI 与受限工作区 | 可运行、查看和管理本机 Codex 任务 |

Team Run 的 HTTP 入口以本地扩展安装器开关作为第一层条件；但任务真正执行时仍需要可用的 Codex Runtime、CLI 和受限工作区。因此，想完整使用 Team Run 时，应同时完成 Runtime 配置。<code>ASTERIA_ENABLE_CODEX_RUNTIME_API=1</code> 是通用运行时任务、日志、取消和管线 API 的开关，也建议在完整本机扩展环境中一并开启。

### 2.3 推荐的本机配置

在受信任的本机工作区创建或更新私有 <code>.env</code> 后重启服务：

    ASTERIA_ENABLE_LOCAL_SKILL_INSTALLER=1
    ASTERIA_CODEX_RUNTIME_ENABLED=1
    ASTERIA_ENABLE_CODEX_RUNTIME_API=1
    ASTERIA_CODEX_WORKSPACE_ROOT=C:\AsteriaWorkspaces
    ASTERIA_CODEX_CLI_PATH=codex

<code>ASTERIA_CODEX_WORKSPACE_ROOT</code> 应指向最小必要的专用目录，而不是磁盘根目录、包含其他客户资料的目录或包含密钥的个人目录。普通使用不需要设置 <code>ASTERIA_ALLOW_UNSANDBOXED_CODEX_RUNTIME</code>；本指南不会把非沙箱执行作为常规安装步骤。

重启后先检查：

1. <code>GET /api/runtime/codex-health</code> 是否能识别 CLI、候选路径和版本。
2. <code>GET /api/runtime-settings</code> 是否显示脱敏后的开关和工作区摘要。
3. 回到 <code>/lab</code>，确认扩展区不再显示“安装器未启用”的阻断状态。

配置变量的默认值、数据边界和便携版差异见 [配置参考](configuration-reference.zh-CN.md) 与 [便携版 Codex Runtime 说明](portable-codex-runtime.zh-CN.md)。

## 3. Skill：从审阅到进入 Lab 上下文

### 3.1 可以导入什么

外部 Lab Skill 支持两类来源：

| 来源 | 合法形式 | 何时使用 | 导入前必须检查 |
| --- | --- | --- | --- |
| 远程 GitHub 仓库 | <code>https://github.com/所有者/仓库</code>，API 可附加 <code>ref</code> | 需要固定到可审阅的公开仓库版本 | 仓库所有者、提交/标签、许可证、依赖、网络行为和数据读取范围 |
| 本机目录 | 包含 <code>SKILL.md</code> 或 <code>.claude-plugin/plugin.json</code> 的目录 | 团队已在本机准备好经过审阅的包 | 所有文件、脚本引用、命令声明、MCP 配置和相对路径 |

一个插件包可以携带内嵌 Skill、命令和 MCP 连接器的元数据。Asteria 会把这些内容作为可审阅的包信息和受限 Lab 上下文的一部分；它不会因为包中出现命令或 MCP 配置就自动执行它们。不要把导入动作理解为对第三方代码的信任或自动运行许可。

### 3.2 完整操作流程

1. 在 <code>/lab</code> 打开本地扩展区域，先确认当前服务运行在可信本机。
2. 选择“从 GitHub 安装”或“从本机目录导入”。远程来源填写完整 GitHub URL；本地来源选择已经审阅的目录。
3. 安装/导入后核对包名称、来源、插件信息、内嵌 Skill 数量、命令/MCP 元数据和挂载状态。
4. 仅在需要将该包的信息用于当前 Lab 分析时执行“挂载”。取消挂载会把它从后续 Lab 上下文中移除，但保留本机条目供以后复用。
5. 在数据集和功能均已选择时运行 Feature Trial，或在 Lab 分析中选择该功能并继续受控分析。
6. 不再使用时先取消挂载；确认没有任务依赖后再删除条目。

### 3.3 挂载后产生什么

挂载的 Skill 不会替代数据画像、字段角色、方法选择或确定性计算。它会以受大小和数量限制的说明/元数据形式进入 Lab 外部 Skill 上下文，生成 <code>analysis_lab_external_skill_context_v2</code> 结构，并与本次分析输出一起保存 <code>external_skill_context.json</code>。

使用者在界面上可看到：

- 已安装和已挂载数量；
- 插件名称、来源、内嵌 Skill、命令和 MCP 连接器的摘要；
- 可选择的功能条目；
- 本次 Lab 分析是否引用了已选功能；
- 后端返回的分析结果、文件和下载入口（仅当本次运行实际产生这些资产时）。

这项能力的意义是让经过审阅的技能说明参与分析规划和上下文组织，而不是让扩展内容替代数据证据或绕过正式报告的必经链。

## 4. Feature Trial：先做适配性评估，再决定是否进入分析

### 4.1 需要填写的内容

一次试验使用以下信息：

| 字段 | 含义 |
| --- | --- |
| <code>dataset_id</code> | 必填，待评估的数据集 |
| <code>active_sheet</code> | 可选，多工作表文件中要使用的工作表 |
| <code>plugin_id</code> | 选定的外部插件 |
| <code>feature_kind</code> | 功能类别：<code>command</code> 或 <code>embedded_skill</code> |
| <code>feature_id</code> | 插件内选定功能的标识 |
| <code>user_goal</code> | 希望该功能帮助解决的业务或分析目标 |

Feature Trial 先读取实际数据画像和字段条件，计算该功能对当前数据的就绪度和建议，而不是直接把外部命令作为通用执行载荷运行。

### 4.2 成功后得到的结果

每次成功试验返回 <code>analysis_lab_feature_trial_v1</code>，并在 <code>/storage/lab_feature_trials/&lt;trial_id&gt;/</code> 下保存工件：

| 结果 | 用途 |
| --- | --- |
| <code>trial_id</code>、数据集、插件与功能信息 | 唯一标识本次试验，便于回查 |
| 基线数据画像 | 显示用于判断的实际数据规模、字段与样本信息 |
| 就绪度评分与原因 | 说明为什么适合、部分适合或不适合当前数据 |
| 重点字段与推荐动作 | 帮助修正字段绑定、数据准备或分析目标 |
| 建议的 Lab 运行参数 | 把试验结论转成可继续审阅的 Lab 输入 |
| <code>trial.json</code> | 结构化试验结果 |
| <code>field_scores.csv</code> | 字段适配度明细 |
| <code>trial_report.md</code> | 便于人工阅读的试验摘要 |

试验结果的正确用途是决定“是否值得把该功能加入后续 Lab 分析”，不是把评分、建议或 Markdown 摘要当作正式管理结论。

## 5. Report Agent Team：把团队角色放进受控 Codex 工作区

### 5.1 团队目录最低要求

导入的 Team 必须是本机目录，且至少能找到一份 Agent Markdown 说明。推荐结构：

    my-report-team/
      team.json
      agents/
        evidence-reviewer.md
        structure-planner.md
        delivery-checker.md

也可以在团队根目录使用 <code>team.md</code> 或 <code>agents.md</code>。可选 <code>team.json</code> 用于声明团队名称、描述和角色摘要；<code>agents/</code> 下的 Markdown 文件描述各角色的任务边界。系统会限制可导入的文件与角色数量，以防止不受控制地把大量本机内容写入任务工作区。

当前公开仓库不随包提供可直接运行的 Team 示例，因此初次打开 Team 列表时为空是正常结果。使用者应导入自己已审阅的本机角色定义，而不是把该区域理解成远程托管的预置团队市场。

团队 Markdown 应写清每个角色可阅读的上下文、预期输出、禁止事项和交接方式。不要把密钥、客户数据、无关工作区路径或“忽略所有约束”的指令写进角色说明。

### 5.2 完整操作流程

1. 在 <code>/lab</code> 的 Report Agent Team 区域选择本机团队目录并导入。
2. 检查团队名称、发现的角色、来源目录和当前挂载状态。
3. 挂载要参与本次任务的团队；未挂载团队不会被写入任务上下文。
4. 选择真实数据集，可选填写工作表、关联报告、用户需求和受限工作区。
5. 确认 Codex Runtime 健康检查通过，再点击运行团队。
6. 页面会显示团队数量、已挂载数、任务 ID、任务状态和返回的工作区路径；根据任务状态继续查看 Runtime 结果、日志或错误。

### 5.3 运行时会写入什么

Team Run 会在受控工作区中创建任务目录。默认位置类似：

    reports/smart-report-<report_id>/lab_agent_team_workspace/
      .codex/lab-report-agent-team.json
      .codex/agents/<team>--<agent>.md
      AGENTS.md

系统把已挂载团队的摘要、角色说明和本次数据/报告上下文写入上述受控任务区域，再创建一个阶段为 <code>lab_report_agent_team</code> 的 Codex 任务。成功、失败或取消后，任务结果可能包含运行 ID、状态、摘要、修改文件、差异链接、transcript 链接和错误信息；这些字段是否出现取决于实际 Runtime 是否完成执行。

Team Run 不承诺一定修改报告，也不会自动把任何文件注册成正式管理报告。运行结果应先在工作区、任务摘要、差异和数据证据中复核。

## 6. Codex Runtime：健康检查、任务和管线

### 6.1 Runtime 能做什么

启用后，Runtime 可提供以下本机辅助能力：

| 能力 | 典型接口/结果 |
| --- | --- |
| 健康检查 | <code>GET /api/runtime/codex-health</code> 返回 CLI 候选、解析路径、版本和错误 |
| 单次运行或异步任务 | 创建 Codex run/job，获得 <code>run_id</code> 或 <code>job_id</code>、状态和摘要 |
| 日志与取消 | 查看运行日志、取消运行、取消任务，避免继续占用本机资源 |
| 运行时进程管理 | 列出、取消或恢复受控运行时进程 |
| 多阶段管线 | 创建、查询、取消、重试阶段或登记允许的报告输出 |
| 学习账本 | 查询本机运行记录和单条详情，便于复盘已发生的任务 |

当 CLI 不可用、工作区不在允许根目录内、认证不可用、任务超时或用户取消任务时，系统应返回失败、取消或错误状态，而不是把任务显示成已完成。

### 6.2 正确的排障顺序

1. 先验证基础分析能启动，避免把 Runtime 故障误判为整个项目不可用。
2. 用 <code>/api/runtime/codex-health</code> 检查 CLI 路径、版本和可用性。
3. 确认 <code>ASTERIA_CODEX_WORKSPACE_ROOT</code> 指向专用、可写且最小化的目录。
4. 确认当前启动服务的同一会话读取到了 Runtime 与 API 开关。
5. 用一个非敏感、小范围任务验证创建、状态查询、日志和取消。
6. 再把 Runtime 用于 Team Run、报告修订或管线；不要把错误任务反复提交为“已完成”。

## 7. 状态、错误与下一步

| 现象 | 常见原因 | 应采取的动作 |
| --- | --- | --- |
| 看到 Skill/Team 列表但不能导入、挂载或运行 | 本地扩展安装器未启用 | 在可信本机设置 <code>ASTERIA_ENABLE_LOCAL_SKILL_INSTALLER=1</code>，重启后重试 |
| 返回 <code>403</code> 和 <code>SKILL_INSTALLATION_DISABLED</code> | 管理类扩展操作被默认保护 | 不要绕过服务端；检查启动环境是否真的包含该开关 |
| Feature Trial 无法启动 | 未选择数据集、功能 ID 无效或包未正确导入 | 先选择数据集，刷新功能目录并核对插件/功能 |
| 团队可以导入但无法运行 | 未挂载团队、未选数据集或 Runtime 条件不足 | 挂载团队，选择数据集，检查 CLI、工作区和 Runtime 健康状态 |
| Runtime 健康检查显示 CLI 不可用 | <code>codex</code> 不在 PATH，或路径/版本不正确 | 设置受信任的 <code>ASTERIA_CODEX_CLI_PATH</code>，重启并重新检查 |
| 任务排队后失败、超时或取消 | 工作区约束、认证、CLI、输入内容或任务本身失败 | 阅读任务状态、错误、日志和工作区差异；修正原因后以新任务重试 |
| 包中显示命令/MCP 元数据 | 外部包包含可声明的功能 | 审阅元数据；当前导入/试验流程不会自动运行任意声明 |

## 8. 与正式报告发布门禁的关系

Skill、Feature Trial、Report Agent Team、Report Agent Session 和 Codex Runtime 都可以帮助组织工作、产生辅助材料或维护任务上下文，但它们都不能跳过正式 <code>management_report.pdf</code> 的强制链：

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

正式 PDF 必须保留 AI trace，确保 AI 输出通过 schema 校验，由确定性执行器计算数值，通过证据校验和发布门禁，且最终质量分不低于 <code>90</code>。缺少任一步时最多只能得到调试性或探索性结果，不能把 Trial 文件、团队工作区文件、运行时日志或修订版本描述为正式管理报告。

## 9. 相关文档

- [配置参考](configuration-reference.zh-CN.md)：变量、默认值和便携版差异。
- [API 参考](api-reference.zh-CN.md)：Skill、Trial、Team、Runtime 的请求和返回字段。
- [模块与功能手册](module-guide.zh-CN.md)：系统模块与入口。
- [功能逐项参考](function-reference.zh-CN.md)：页面操作、接口、产物与边界。
- [逐页结果说明](page-results.zh-CN.md)：在 <code>/lab</code> 与修订工作区完成后应看到什么。
- [便携版 Codex Runtime（中文）](portable-codex-runtime.zh-CN.md)：CLI 发现、健康检查与便携版发布边界。
- [正式报告可信机制](report-integrity.zh-CN.md)：正式 PDF 的证据与质量规则。
