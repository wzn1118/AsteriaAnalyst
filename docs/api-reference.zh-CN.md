# Asteria Analyst 本机 API 参考

> 适用范围：当前公开仓库 `backend/app/main.py` 注册的本机 HTTP 路由。本文件不是公网 API 承诺，也不是多租户集成规范。

## 1. 使用前必须知道的边界

- 默认启动器仅把服务绑定到 `127.0.0.1`。源码模式通常是 `http://127.0.0.1:8000`，便携版通常由同一 FastAPI 服务在 `http://127.0.0.1:8787` 提供页面和 API；端口可能变化，始终以启动日志显示的实际地址为准。
- 当前应用没有账户认证、Bearer Token 验证或对象级授权层。CORS 只约束浏览器跨域请求，**不是** 网络访问授权。
- 不要将这些路径通过反向代理、端口映射、隧道或改监听地址直接暴露到共享网络或互联网。那需要独立的身份认证、授权、对象隔离、私有下载、审计与限流设计。
- `/storage/**` 是可被本机界面引用的公开工件路径，不是通用文件 API；上传数据、私有设置和运行时目录不应放入该树。
- `CodeExecutionRequest` 虽然存在于内部模型文件，但当前公开版本没有注册 `/api/code/execute`。不要把未接入内部服务当作对外能力。

## 2. 通用约定

| 项目 | 约定 |
| --- | --- |
| 编码 | JSON 请求和响应使用 UTF-8；文件上传使用 `multipart/form-data`。 |
| 标识符 | `dataset_id`、`report_id`、`job_id`、`session_id` 等由服务端生成或返回，调用方不得自行猜测目录路径。 |
| 选择工作表 | 需要切换工作表的接口使用 `active_sheet` 或 `{"sheet_name":"..."}`。上传多工作表 Excel 后必须先确认对应工作表。 |
| 分页 | 报告目录支持 `limit`、`offset` 等查询参数；不要假定列表响应一定包含全部历史数据。 |
| 错误 | 常见 HTTP 状态为 `400`（业务输入不成立）、`403`（功能开关未开启）、`404`（标识符不存在）、`422`（FastAPI/Pydantic 校验失败）和 `500`（未处理的服务错误）。错误文本用于诊断，不应依赖其中文/英文措辞作为稳定协议。 |
| 异步任务 | 创建任务后保存 `job_id`，再轮询对应的 `GET` 路由；不要通过重复提交同一请求来判断任务是否完成。 |
| SSE | 报告修订事件流返回 `text/event-stream`。调用方应保留 `report_id` 与可选 `cursor`，并处理网络中断后的重新连接。 |

若保持 FastAPI 默认配置，本机还可访问 `/openapi.json`、`/docs` 和 `/redoc` 查看机器生成的 schema。它们是当前进程的辅助视图；发布说明和代码变更发生后，以当前 `main.py` 与 `models.py` 为准。

## 3. 功能开关总览

| API 组 | 默认可调用性 | 额外条件 | 失败时的典型结果 |
| --- | --- | --- | --- |
| 数据、统计、自动分析、报告目录 | 本机默认可用 | 数据集和请求字段有效 | `400`、`404` 或 `422`。 |
| AI 增强报告 | 可选配置 | 本机已配置可用的 AI 提供方和允许传输的数据 | 任务失败或无法通过正式报告门禁。 |
| 已挂载 Skill、Lab Skill/Trial 目录、Team 列表与 Runtime 健康检查 | 本机只读可查询 | 服务已启动；查询结果只描述当前本机状态 | 空列表、不可用 CLI 或错误信息，不会启动外部任务。 |
| Skill/Team 导入、挂载、删除，Feature Trial 与 Team Run | 默认关闭 | `ASTERIA_ENABLE_LOCAL_SKILL_INSTALLER=1`；Team Run 还需要实际可用的 Runtime | `403`，错误码通常为 `SKILL_INSTALLATION_DISABLED`。 |
| 报告智能体会话、Runtime 进程、Codex Run/流水线/学习账本 | 默认关闭 | `ASTERIA_ENABLE_CODEX_RUNTIME_API=1`，并满足 `ASTERIA_CODEX_RUNTIME_ENABLED=1`、CLI 与受限工作区条件 | `403` 或任务失败状态。 |
| 非沙箱 Codex | 默认关闭 | 除 Runtime 开关外还需 `ASTERIA_ALLOW_UNSANDBOXED_CODEX_RUNTIME=1` 与运行时确认 | 不应把它当作普通用户功能。 |

功能开关只用于防止本机误启用高权限能力，并不替代认证或访问控制。完整配置见 [配置与安全](security-deployment.zh-CN.md)。

## 4. 系统发现与目录

| 方法与路径 | 用途 | 主要返回内容 | 注意事项 |
| --- | --- | --- | --- |
| `GET /health` | 健康检查 | `{"status":"ok"}` | 启动器用它判断后端是否可用。 |
| `GET /api/manifest` | 获取产品、集成、文件格式、分析和报告能力摘要 | manifest 对象 | 面向界面发现，不应视为永久版本契约。 |
| `GET /api/ecosystem/market` | 查看生态工具摘要 | `summary`、`tools` | 工具是否可运行仍受本机依赖和开关限制。 |
| `GET /api/skills/mounted` | 查看当前已挂载 Skill | 摘要和 `skills` | 仅表示本机已挂载状态。 |
| `GET /api/statistics/catalog` | 获取受支持统计方法目录 | 目录与分类摘要 | 方法名出现不等于对任意数据都适用。 |
| `GET /api/analysis/auto/methods` | 获取自动分析方法目录 | 方法列表 | 用于自动分析选择。 |
| `GET /api/lab/methods` | 获取 Lab 方法目录 | 带 `surface: "lab"` 的方法列表 | 用于实验室界面和方法卡。 |

## 5. 数据集、历史材料与业务背景

### 5.1 列表、详情与工作表

| 方法与路径 | 查询/请求 | 作用 |
| --- | --- | --- |
| `GET /api/datasets` | 无 | 列出本机数据集。 |
| `GET /api/datasets/{dataset_id}` | `summary` 可选 | 获取一个数据集的画像与详情。 |
| `GET /api/datasets/{dataset_id}/workflow` | 无 | 获取可用于当前数据集的工作流蓝图。 |
| `POST /api/datasets/{dataset_id}/sheet` | `SheetSelectionRequest` | 切换或确认活动工作表。 |
| `GET /api/historical-reports` | 无 | 列出导入的历史报告模板。 |
| `GET /api/historical-reports/{template_id}` | 无 | 获取一个历史报告模板。 |
| `GET /api/business-backgrounds` | 无 | 列出业务背景材料。 |
| `GET /api/business-backgrounds/{context_id}` | 无 | 获取一个业务背景材料。 |

`SheetSelectionRequest`：

```json
{
  "sheet_name": "Sheet1"
}
```

接口会检查数据集和工作表是否存在。选择工作表只决定后续分析入口的活动上下文，不会改变原始上传文件。

### 5.2 上传

| 方法与路径 | Content-Type | 表单字段 | 用途 |
| --- | --- | --- | --- |
| `POST /api/datasets/upload` | `multipart/form-data` | `file` | 上传 CSV、TSV、Excel 或 Stata 数据文件。 |
| `POST /api/historical-reports/upload` | `multipart/form-data` | `file` | 上传历史报告材料，作为上下文而非未经验证的事实来源。 |
| `POST /api/business-backgrounds/upload` | `multipart/form-data` | `file` | 上传业务背景材料。 |

调用上传接口前，确认文件不含不应进入本机工作区或外部 AI 提供方的数据。上传成功不代表该文件适合任何统计方法或可以直接支撑正式报告。

## 6. 统计、自动分析与 Analysis Lab

### 6.1 统计与自动分析

| 方法与路径 | 请求模型 | 用途 |
| --- | --- | --- |
| `POST /api/statistics/run` | `StatisticRequest` | 执行受支持的统计或模型方法。 |
| `POST /api/analysis/auto` | `AutoAnalysisRequest` | 根据数据、目标和字段选择执行自动分析。 |
| `POST /api/lab/run` | `AutoAnalysisRequest` | 在 Analysis Lab 表面执行自动分析并生成实验资产。 |

`StatisticRequest` 的核心字段：

| 字段 | 含义 |
| --- | --- |
| `dataset_id` | 必填，目标数据集。 |
| `analysis_type` | 必填，统计方法标识；有效取值以当前 `models.py` 和统计目录为准。 |
| `active_sheet` | 多工作表文件的活动工作表。 |
| `target`、`features` | 因变量、特征或分析字段。 |
| `group_column`、`group_a`、`group_b` | 分组字段与两组比较的取值；仅在对应方法需要时填写。 |
| 方法参数 | 与方法相关，例如显著性、模型、随机种子或图表选项。 |

`AutoAnalysisRequest` 的核心字段：`dataset_id`、`active_sheet`、`user_goal`、`report_part`、字段绑定、方法选择、派生字段选择、Skill 选择与合并模式。它适合生成可审阅的分析建议和结构化结果，但不能绕过正式报告的 AI trace、确定性计算、证据校验和质量门禁。

### 6.2 Lab 方法资产与 PDCA

| 方法与路径 | 请求/参数 | 作用 |
| --- | --- | --- |
| `POST /api/lab/method-cards` | `LabMethodCardSaveRequest` | 保存由基础方法、名称、描述、字段和来源方法组成的方法卡。 |
| `GET /api/lab/pdca/status` | 无 | 查询 Lab 的 PDCA 状态。 |
| `POST /api/lab/pdca/run` | 无 | 手动触发一个 PDCA 周期。 |

方法卡和 Lab 结果用于探索、对比、复核和复用方法配置。它们不是正式管理报告发布资格的替代物。

### 6.3 外部 Skill 与功能试验

以下只读目录可以用于展示当前本机状态，不会安装或执行外部内容：

| 方法与路径 | 请求 | 作用 |
| --- | --- | --- |
| `GET /api/skills/mounted` | 无 | 列出当前已挂载 Skill 的摘要。 |
| `GET /api/lab/skills` | 无 | 列出本机导入/挂载的实验室 Skill。 |
| `GET /api/lab/feature-trials/catalog` | 无 | 获取已导入包可声明的受控功能试验目录。 |

以下管理和试验路径需要本机显式启用 `ASTERIA_ENABLE_LOCAL_SKILL_INSTALLER=1`：

| 方法与路径 | 请求 | 作用与主要返回 |
| --- | --- | --- |
| `POST /api/lab/skills/install` | `source_url`、可选 `ref`、`mount` | 从 GitHub 仓库安装；返回包/插件元数据与挂载状态。 |
| `POST /api/lab/skills/import-local` | `local_path`、`mount` | 从包含 `SKILL.md` 或插件清单的本机目录导入；返回导入条目。 |
| `POST /api/lab/skills/{skill_id}/mount` | 无 | 把 Skill 加入后续 Lab 的外部 Skill 上下文。 |
| `POST /api/lab/skills/{skill_id}/unmount` | 无 | 从后续 Lab 上下文移除 Skill，保留本机条目。 |
| `DELETE /api/lab/skills/{skill_id}` | 无 | 删除本机条目；调用前应确认没有任务依赖它。 |
| `POST /api/lab/feature-trials/run` | `dataset_id`、可选 `active_sheet`、`plugin_id`、`feature_kind`、`feature_id`、`user_goal` | 返回 `analysis_lab_feature_trial_v1`、`trial_id`、基线画像、就绪度/原因、推荐动作、建议的 Lab 载荷和工件链接。 |

Feature Trial 会写入 `trial.json`、`field_scores.csv` 和 `trial_report.md`。当前实现把受审阅的 Skill 说明/元数据写入 Lab 上下文；它不是通用第三方命令或 MCP 自动执行器。本机目录导入、远程安装和试验执行都可能扩大本机执行面，只在受信任单机环境中使用，并在导入前审阅来源。完整操作见 [本地扩展指南](local-extensions.zh-CN.md)。

### 6.4 报告 Agent Team

团队列表是只读状态接口；导入、挂载、卸载、删除和运行均需要 `ASTERIA_ENABLE_LOCAL_SKILL_INSTALLER=1`：

| 方法与路径 | 请求 | 作用与主要返回 |
| --- | --- | --- |
| `GET /api/lab/report-agent-teams` | 无 | 列出本机团队。 |
| `POST /api/lab/report-agent-teams/import-local` | `local_path`、`mount` | 从至少含一个 Agent Markdown 的本机目录导入团队。 |
| `POST /api/lab/report-agent-teams/{team_id}/mount` | 无 | 挂载团队。 |
| `POST /api/lab/report-agent-teams/{team_id}/unmount` | 无 | 卸载团队。 |
| `DELETE /api/lab/report-agent-teams/{team_id}` | 无 | 删除团队。 |
| `POST /api/lab/report-agent-teams/run` | `report_id`、`dataset_id`、`sheet_name`、`workspace_path`、`user_requirement`、`team_ids` | 将已挂载团队角色写入受控工作区并创建 Codex 任务；返回团队上下文、工作区路径和任务对象。 |

Team Run 的首层接口检查是安装器开关，但其后台任务仍需可用 Codex Runtime、CLI、认证与受限工作区；不满足这些条件时任务可能排队后失败。当前服务端将多个角色 Markdown 和协调提示交给单个受控 Codex 任务，并非后端保证的并行多智能体编排。Team 结果不自动生成或发布正式 `management_report.pdf`。使用者必须明确它们只适合可信本机管理员场景。

## 7. 智能报告、任务与报告目录

| 方法与路径 | 请求/参数 | 作用 |
| --- | --- | --- |
| `POST /api/datasets/{dataset_id}/smart-report` | `SmartReportRequest` | 同步生成智能报告结果。 |
| `POST /api/datasets/{dataset_id}/smart-report-jobs` | `SmartReportRequest` | 创建异步智能报告任务。 |
| `GET /api/report-jobs/{job_id}` | 无 | 轮询报告任务状态。不存在时返回 `404`。 |
| `GET /api/reports` | `limit`、`offset`、`q`、`dataset_id`、`business_profile`、`sort_by`、`refresh_index` | 分页检索报告目录。 |
| `GET /api/reports/{report_id}` | 无 | 获取单份报告详情和可用工件。 |

`SmartReportRequest` 的主要维度：

| 维度 | 相关字段 | 说明 |
| --- | --- | --- |
| 数据范围 | `sheet_name`、`selected_sheets`、`multi_table_mode` | 多表模式为 `single`、`merge`、`separate` 或 `combined`。 |
| 业务意图 | 业务画像、目标受众、用户需求、报告部分 | 让生成围绕问题而非只围绕字段。 |
| 输出 | 报告风格、语言、视觉偏好、交付目标 | 影响呈现，不可把样式当证据。 |
| 补充上下文 | 历史报告和业务背景 | 提供参考，不应替代原始数据和验证。 |
| 高级路线 | R 或高级运行时选项 | 受本机依赖、设置和相应安全边界限制。 |

同步接口适合较短、可交互的任务；耗时任务优先使用 jobs 接口并查询 `job_id`。不论采用哪一种，返回了文件或预览都不自动代表正式 `management_report.pdf` 已获放行。

## 8. 报告修订智能体工作台

除创建会话外，下列会话接口均要求在查询参数中携带 `report_id`，以避免跨报告混淆会话状态。

| 方法与路径 | 请求/参数 | 作用 |
| --- | --- | --- |
| `POST /api/reports/{report_id}/agent-sessions` | `ReportAgentSessionCreateRequest` | 以可选 `title` 创建会话。 |
| `GET /api/reports/{report_id}/agent-sessions/{session_id}` | 无 | 读取会话详情。 |
| `POST /api/report-agent-sessions/{session_id}/messages` | `report_id`，`ReportAgentMessageRequest` | 提交 `message`。 |
| `GET /api/report-agent-sessions/{session_id}/events` | `report_id`、`cursor` | 拉取事件。 |
| `POST /api/report-agent-sessions/{session_id}/cancel` | `report_id` | 取消当前会话回合。 |
| `GET /api/report-agent-sessions/{session_id}/files` | `report_id` | 列出会话文件。 |
| `GET /api/report-agent-sessions/{session_id}/diff` | `report_id` | 获取当前差异。 |
| `GET /api/report-agent-sessions/{session_id}/attachments` | `report_id` | 列出附件。 |
| `POST /api/report-agent-sessions/{session_id}/attachments` | `report_id`、`multipart/form-data file` | 上传附件。 |
| `DELETE /api/report-agent-sessions/{session_id}/attachments/{attachment_id}` | `report_id` | 删除附件。 |
| `GET /api/report-agent-sessions/{session_id}/annotations` | `report_id` | 读取批注。 |
| `POST /api/report-agent-sessions/{session_id}/annotations` | `report_id`、`ReportAnnotationRequest` | 新增或更新批注。 |
| `DELETE /api/report-agent-sessions/{session_id}/annotations/{annotation_id}` | `report_id` | 删除批注。 |
| `GET /api/report-agent-sessions/{session_id}/events/stream` | `report_id`、`cursor` | 建立 SSE 事件流。 |
| `POST /api/report-agent-sessions/{session_id}/publish` | `report_id`、`ReportAgentPublishRequest` | 发布本地修订会话。 |

`ReportAnnotationRequest` 包含工件 URL、工件名称/类型、页码或坐标、形状和说明。工件 URL 必须对应当前报告可访问的本机资产；批注不应嵌入密钥、客户隐私数据或外部公网 URL 作为信任来源。

所有报告智能体会话路由目前要求 `ASTERIA_ENABLE_CODEX_RUNTIME_API=1`。这里的“发布”指本地报告修订版本，不等同于创建 GitHub Release，也不解除正式管理报告的发布门禁。

## 9. R 智能流、Runtime、Codex Run 与流水线

### 9.1 R 智能流

| 方法与路径 | 请求模型 | 作用 |
| --- | --- | --- |
| `POST /api/reports/{report_id}/r-intelligence-flow` | `RWorkflowIntelligenceRequest` | 围绕 `focus_question`、`target_audience` 和 `output_goal` 执行 R 工件智能流。 |

调用前必须确认本机 `Rscript` 可用，或便携包包含可用的 R 运行时。错误的 R 路径、缺失依赖或不匹配的数据输入会导致业务错误或运行失败。

### 9.2 Runtime 进程和 Codex Run

以下全部需要 `ASTERIA_ENABLE_CODEX_RUNTIME_API=1`：

| 方法与路径 | 请求/参数 | 作用 |
| --- | --- | --- |
| `GET /api/runtime/processes` | `report_id`、`session_id`、`scope`、`limit` | 查询受 Runtime 管理的进程。 |
| `POST /api/runtime/processes/{kind}/{process_id}/cancel` | `report_id`、可选 `session_id` | 取消一个进程。 |
| `POST /api/runtime/processes/{kind}/{process_id}/resume` | `report_id`、可选 `session_id` | 恢复一个进程。 |
| `POST /api/codex-runs` | `CodexRunRequest` | 同步或直接创建一个 Codex 运行。 |
| `POST /api/codex-run-jobs` | `CodexRunRequest` | 创建 Codex 运行任务。 |
| `GET /api/codex-run-jobs/{job_id}` | 无 | 查询 Codex 任务。 |
| `GET /api/codex-runs/{run_id}` | 无 | 查询运行详情。 |
| `GET /api/codex-runs/{run_id}/log` | `offset`、`limit_bytes` | 分段读取运行日志。 |
| `POST /api/codex-runs/{run_id}/cancel` | 无 | 取消运行。 |
| `POST /api/codex-run-jobs/{job_id}/cancel` | 无 | 取消任务。 |

`CodexRunRequest` 至少需要 `workspace_path`，并可携带提示词、提示词模板、上下文、数据集、模型、超时和会话恢复信息。`workspace_path` 必须是管理员认可的本机工作目录；绝不应从不受信任的浏览器输入直接映射到任意机器路径。

### 9.3 学习账本与 Codex 流水线

| 方法与路径 | 请求/参数 | 作用 |
| --- | --- | --- |
| `GET /api/runtime-learning-ledger` | `limit`、`source_type`、`status` | 查询运行学习账本。 |
| `GET /api/runtime-learning-ledger/{entry_id}` | 无 | 查询账本条目详情。 |
| `POST /api/codex-pipeline-jobs` | `CodexPipelineRequest` | 创建流水线任务。 |
| `GET /api/codex-pipeline-jobs/{job_id}` | 无 | 查询流水线任务。 |
| `POST /api/codex-pipeline-jobs/{job_id}/cancel` | 无 | 取消流水线。 |
| `POST /api/codex-pipeline-jobs/{job_id}/retry-stage` | `CodexPipelineRetryRequest` | 重试指定 `stage_id`，可配置 `auto_start`。 |
| `POST /api/codex-pipeline-jobs/{job_id}/register-report-output` | 无 | 将流水线输出登记到报告任务。 |

`CodexPipelineRequest` 必须包含 `workspace_path`，并声明流水线类型、关联报告、视觉/受众/上下文和自动启动选项。账本、日志、路径和流水线产物都可能暴露本机运行信息，因此不适合作为公开网页接口。

## 10. 运行配置接口

| 方法与路径 | 作用 | 安全说明 |
| --- | --- | --- |
| `GET /api/runtime-settings` | 返回掩码 API Key、是否配置密钥、模型、Base URL、R/Codex 路径和开关摘要。 | 当前只读；即使密钥被掩码，路径和运行状态也不应暴露给不受信任用户。 |
| `GET /api/runtime/codex-health` | 返回 Codex CLI 可用性、解析路径、版本、候选路径和错误。 | 仅限本机诊断，不是公网健康检查。 |

当前公开路由没有 `POST`、`PUT` 或 `DELETE /api/runtime-settings`。不要在客户端或集成文档中承诺可以通过 HTTP 写入 API Key 或修改运行时设置。

## 11. 前端页面与静态工件

以下不是业务 API，但有助于便携版和调试：

| 路径 | 说明 |
| --- | --- |
| `/analysis`、`/lab`、`/revision`、`/revision/workspace` | 前端工作区入口，并带有尾斜杠/HEAD 兼容形式。 |
| `.../__next...__PAGE__.txt` | Next 静态导出的 RSC 兼容别名，不应被第三方集成依赖。 |
| `/storage/**` | 已选定公开工件的本机静态路径；不等于完整存储目录。 |

## 12. 集成与版本策略

当前 API 用于同仓库前端和本机工作流，尚未声明稳定的语义化公共 API 版本。外部集成应：

1. 固定到明确的 Git 提交或 Release 版本；
2. 在升级前比较 `backend/app/main.py`、`backend/app/models.py` 和本机 OpenAPI；
3. 处理 `403`、`404`、`422`、异步任务和功能开关；
4. 不读取或猜测 `/storage`、`workspace/storage`、`%APPDATA%` 下的内部文件结构；
5. 不把本机端点暴露给公网用户。

接口变动时，维护者应同时更新本文件、功能逐项参考和相应测试。
