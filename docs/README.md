# Asteria Analyst 文档中心

本目录是 Asteria Analyst 的公开技术文档入口。它把“如何使用”与“如何开发、配置、发布和审计”分开说明，避免把实验功能、默认功能和正式交付资格混为一谈。

项目当前面向 **Windows 本机、回环地址、单用户** 工作流。公开 GitHub 仓库和公开 Release 不代表系统已经成为可直接暴露到公网的多用户服务；相关边界见 [安全与部署说明](security-deployment.zh-CN.md)。

## 先按角色选文档

| 你要完成的事 | 首选文档 | 什么时候继续读 |
| --- | --- | --- |
| 第一次启动并完成一次本地分析 | [快速开始](getting-started.zh-CN.md) | 需要完整操作顺序时读 [用户指南](user-guide.zh-CN.md) |
| 查找某个页面、按钮、产物或业务模块 | [模块与功能手册](module-guide.zh-CN.md) | 需要逐项输入、输出、接口和限制时读 [功能逐项参考](function-reference.zh-CN.md)；需要判断每个页面完成后实际得到什么时读 [逐页结果说明](page-results.zh-CN.md) |
| 理解数据、AI、计算、证据和 PDF 为什么要分层 | [系统架构](architecture.zh-CN.md) | 正式报告负责人还必须读 [正式报告可置信机制](report-integrity.zh-CN.md) |
| 调用本机 API、排查前后端联调 | [API 参考](api-reference.zh-CN.md) | 需要字段结构时对照 `backend/app/models.py` 和本机 OpenAPI |
| 配置 AI 提供方、CORS、Codex Runtime 或数据目录 | [配置参考](configuration-reference.zh-CN.md) | 涉及密钥、网络暴露或公开部署边界时继续读 [安全与部署说明](security-deployment.zh-CN.md) |
| 修改代码、添加功能或提交 Pull Request | [开发与质量指南](development-guide.zh-CN.md) | 涉及报告生成时还必须遵守 [AI 强制发布链（中文）](architecture_ai_mandatory_chain.zh-CN.md) |
| 构建 Windows 便携包、发布 GitHub Release、回滚发布 | [发布与运维指南](release-operations.zh-CN.md) | 使用便携包时读 [便携版离线指南](portable-user-guide.zh-CN.md) |

## 文档覆盖图

| 文档 | 解决的问题 | 权威来源 |
| --- | --- | --- |
| [公开项目介绍](public-project-introduction.zh-CN.md) | 项目定位、适用场景、公开仓库边界 | `README.md`、`SECURITY.md` |
| [模块与功能手册](module-guide.zh-CN.md) | 前端工作区、后端服务、数据和报告模块 | 前端路由、`backend/app/services/` |
| [功能逐项参考](function-reference.zh-CN.md) | 页面操作、接口入口、产物和限制 | 页面实现、`backend/app/main.py` |
| [逐页结果说明](page-results.zh-CN.md) | 六个实际页面的完成结果、空态、失败边界与下一步 | 前端路由、页面组件与接口返回状态 |
| [系统架构](architecture.zh-CN.md) | 分层、数据流、存储边界、正式报告链 | `backend/app/main.py`、服务层、`path_service.py` |
| [AI 强制发布链（中文）](architecture_ai_mandatory_chain.zh-CN.md) | 正式 `management_report.pdf` 的不可绕过技术契约 | `AGENTS.md`、报告服务与发布门禁 |
| [API 参考](api-reference.zh-CN.md) | 当前注册的 HTTP 路由、请求体、状态和错误 | `backend/app/main.py`、`backend/app/models.py` |
| [配置参考](configuration-reference.zh-CN.md) | 环境变量、启动器差异、AI/R/Codex Runtime 与数据目录 | `.env.example`、`run_desktop.py`、`settings_service.py` |
| [安全与部署说明](security-deployment.zh-CN.md) | 密钥、公开仓库、网络暴露、可选 Runtime 和部署红线 | `SECURITY.md`、部署边界与安全测试 |
| [开发与质量指南](development-guide.zh-CN.md) | 本地开发、测试、代码变更和文档维护 | `CONTRIBUTING.md`、`AGENTS.md`、项目脚本 |
| [发布与运维指南](release-operations.zh-CN.md) | 源码/便携包构建、Release 验收、回滚 | `scripts/build_portable.ps1`、GitHub Actions |
| [便携版离线指南](portable-user-guide.zh-CN.md) | ZIP 解压后的启动、数据位置、升级和排障 | 便携包启动脚本、`run_desktop.py` |
| [便携版 Codex Runtime（中文）](portable-codex-runtime.zh-CN.md) | 可选 Runtime 的发现、开关、健康检查与发布边界 | Runtime 服务、`.env.example` |

## 阅读约定

为避免“看见功能名就以为一定可用”，文档采用以下状态词：

| 状态 | 含义 |
| --- | --- |
| **默认可用** | 在支持的平台上启动本机服务后可使用，不需要 AI 密钥或高权限开关。 |
| **可选配置** | 需要使用者在本机配置 AI 提供方、R 环境或其他依赖。 |
| **默认关闭** | 需要本机管理员设置明确的环境变量后才开放；不应为方便而在共享环境中开启。 |
| **受发布门禁约束** | 即使界面显示结果，也不等同于可以发布正式 `management_report.pdf`。 |
| **未承诺能力** | 代码目录、方法目录或内部模型中可能存在名称，但当前公开版本没有把它作为受支持功能发布。 |

## 正式报告的不可绕过规则

正式 `management_report.pdf` 只能经过下面的链路：

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

AI 用于字段语义、业务路由和指标规划，不能最终确定数字。缺少 AI trace、schema 校验、确定性计算、证据校验或门禁通过结果时，系统最多应生成用于诊断的 `debug_report`；最终质量分低于 `90` 时同样不得发布正式 PDF。完整解释见 [正式报告可置信机制](report-integrity.zh-CN.md) 和 [AI 强制发布链（中文）](architecture_ai_mandatory_chain.zh-CN.md)。

## 文档维护规则

代码变更必须同步维护相应文档，尤其是以下情况：

1. 在 `backend/app/main.py` 新增、删除或改动 HTTP 路由时，更新 [API 参考](api-reference.zh-CN.md)。
2. 修改 `backend/app/models.py` 的请求模型、`.env.example` 的配置项或启动器时，更新 API、配置和启动相关文档。
3. 修改报告生成链路、证据规则或质量阈值时，同时更新 `AGENTS.md`、[AI 强制发布链（中文）](architecture_ai_mandatory_chain.zh-CN.md) 和 [正式报告可置信机制](report-integrity.zh-CN.md)。
4. 修改 `scripts/build_portable.ps1`、便携包结构或 Release 流程时，更新 [发布与运维指南](release-operations.zh-CN.md) 及 [便携版离线指南](portable-user-guide.zh-CN.md)。
5. 文档中的安全承诺必须能在当前代码或配置中验证。不要把“本机默认值”写成“生产级公网安全”。

源码是最终事实来源。若文档与当前代码不一致，应先停止对外承诺，核对 `main.py`、请求模型、启动脚本和自动化测试后再修订文档或实现。
