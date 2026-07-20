# Asteria Analyst 开发与质量指南

本指南面向在源码仓库中开发、测试、审阅和提交变更的贡献者，并与 [CONTRIBUTING.md](../CONTRIBUTING.md) 共同定义仓库规则。报告相关变更持续遵循 AI 强制发布链。

## 1. 开发环境

| 依赖 | 最低要求 | 用途 |
| --- | --- | --- |
| Python | 3.11+ | FastAPI、数据处理、统计、PDF 与测试。CI 当前使用 Python 3.13 进行后端验证。 |
| Node.js | 20.9+ | Next.js 前端开发、构建、lint。CI 当前使用 Node.js 22。 |
| npm | 随 Node.js | 依据锁文件安装前端依赖。 |
| PowerShell | Windows 推荐 | 启动器、便携版构建和本机检查。 |
| R（可选） | 与本机工作流匹配 | 仅在使用 R 智能流时需要；可用捆绑 R 运行时或显式路径。 |
| Codex CLI（可选） | 受信任的本机安装 | 仅在显式启用 Runtime 时需要。 |

先确认版本：

```powershell
python --version
node --version
npm --version
```

## 2. 仓库地图

| 路径 | 职责 | 修改时必须注意 |
| --- | --- | --- |
| `start-asteria.cmd` / `start-asteria.ps1` | 源码版一键启动、依赖检查、端口和日志。 | 保持回环绑定、实际端口输出和不误杀无关进程的策略。 |
| `frontend/` | Next.js 页面、组件、客户端调用和构建配置。 | 浏览器包使用可公开的客户端配置；密钥和后端私有路径由服务端保存。 |
| `backend/app/main.py` | 已注册 HTTP 路由、静态工件和前端回退入口。 | 路由变更必须同步更新 API 文档与测试。 |
| `backend/app/models.py` | Pydantic 请求模型。 | 路由公开状态由路由层和安全策略定义；新增执行入口前完成独立评审。 |
| `backend/app/services/` | 数据、分析、AI、报告、修订和 Runtime 逻辑。 | 维护数据/证据边界；渲染层消费已绑定内容，字段理解和正式数值计算由服务层完成。 |
| `backend/tests/` | 单元、集成和发布默认值验证。 | 安全回归应覆盖默认关闭和公开路由面。 |
| `docs/` | 用户与技术文档。 | 保持路由、配置、启动方式和发布说明与代码一致。 |
| `scripts/` | 实验、检查和便携版构建。 | 实验脚本标注为实验用途；稳定产品功能提供独立入口和文档。 |

## 3. 启动方式

### 推荐：源码版一键启动

在仓库根目录双击：

```text
start-asteria.cmd
```

启动器会读取可选 `.env`、检查 Python 与 Node.js、准备 `backend/.venv`、安装依赖、构建前端、启动绑定到 `127.0.0.1` 的服务，并在 `logs/launcher/` 写入日志。它会打印实际前端地址和后端健康地址；端口以启动输出为准。

### 手动调试：后端与前端分开启动

手动方式适用于需要单独观察进程、端口和日志归属的调试场景：

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

另开一个终端：

```powershell
Set-Location frontend
npm ci
npm run dev
```

手动启动后，前端 API 基地址与实际后端保持一致。`NEXT_PUBLIC_API_BASE_URL` 使用可公开的地址；协作与公网访问通过带认证、授权和网络隔离的独立部署方案提供。

## 4. 日常质量检查

后端在 `backend` 目录执行，前端在 `frontend` 目录执行：

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m pytest

Set-Location ..\frontend
npm ci
npm run lint
npm run verify:method-guide
npm run build
```

`CONTRIBUTING.md` 将这些检查列为 Pull Request 前的最低要求。若全量后端测试耗时过长，应先运行与修改相关的聚焦测试以便定位问题，但在提交或发布前必须如实报告全量测试是否完成、通过、失败或受环境阻塞。

GitHub Actions 的 `ci.yml` 当前验证后端 pytest、前端 lint、方法指南校验、生产构建和高危生产依赖审计。它不替代 Windows 便携包构建、实际浏览器冒烟和 Release 资产检查。

## 5. 正式报告链的开发约束

修改任何报告生成、数据映射、AI 编排、指标、证据、PDF 或报表绑定代码前，先阅读根目录 `AGENTS.md`、[AI 强制发布链（中文）](architecture_ai_mandatory_chain.zh-CN.md) 和 [正式报告可置信机制](report-integrity.zh-CN.md)。以下约束在每次改动中持续满足：

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

- `AIFieldSemanticMapper`、`AIBusinessContextRouter` 与 `AIMetricDerivationPlanner` 必须在正式报告绑定前执行并保留 trace。
- AI 输出必须通过 schema 校验；正式数值由确定性执行器产生。
- PDF 渲染器消费已完成字段理解、业务路由和指标计算的绑定结果。
- `debug_report` 服务于 trace、schema、证据或门禁诊断；正式 PDF 使用完整发布链的放行结果。
- 质量分低于 `90` 必须阻断正式 `management_report.pdf`。

禁止新增 `raw data -> renderer -> management_report.pdf` 快捷路径；此类变更属于发布阻断问题。

## 6. API、模型与前端联调规则

1. 在 `backend/app/main.py` 注册新路由前，判断它是否需要认证、对象授权或仅限本机管理员开关。
2. 新增请求模型后，在注册路由和安全策略明确后，将其列入 [API 参考](api-reference.zh-CN.md)。
3. 文件上传、报告、附件和 `/storage` 工件必须保持私有数据与公开工件子树的边界。
4. Runtime、Skill、Agent Team 和非沙箱执行必须默认关闭，并有聚焦测试验证其 HTTP 路由或行为不会被意外暴露。
5. 前端错误处理覆盖任务轮询、`403` 功能关闭、`404` 资源缺失和 `422` 请求校验失败；界面依据状态码和结构化字段呈现状态。
6. 所有可见文案、接口字段和文档与当前实现同步；计划中的方法目录项目标注为规划内容。

## 7. 文档与测试同步矩阵

| 变更类型 | 必须同步的文档 | 推荐验证 |
| --- | --- | --- |
| 路由、请求模型、响应结构 | `docs/api-reference.zh-CN.md`、功能逐项参考 | OpenAPI/本机调用、相关后端测试。 |
| 页面、工作区、按钮或导出 | 模块手册、功能逐项参考、用户指南 | `npm run lint`、`npm run build`、浏览器冒烟。 |
| `.env.example`、启动器、路径或端口 | 配置参考、快速开始、便携版指南 | 启动器/便携版实际启动和 `/health`。 |
| 报告/AI 链 | AI 强制链、报告可置信机制、架构文档 | 后端测试、前端构建、发布门禁验证。 |
| 便携包/Release 结构 | 发布与运维指南、离线指南 | ZIP 清单、SHA-256、干净机器冒烟。 |
| 安全默认值 | 安全与部署、API 参考、`SECURITY.md` | 公开路由与默认开关的安全回归。 |

## 8. 提交前检查单

1. `git status` 中是否没有真实数据、报告、日志、缓存、密钥或 `.env`？
2. 是否运行了与修改风险相称的后端测试和前端检查？
3. 是否没有改变默认回环监听、私有存储或高权限 Runtime 的安全边界？
4. 是否更新了相关中文文档和英文政策/贡献说明？
5. 报告链变更是否仍满足 trace、schema、确定性计算、证据和质量门禁？
6. 是否清楚区分“已验证”和“尚未运行/环境阻塞”的检查结果？

## 9. 排障入口

| 现象 | 首先检查 |
| --- | --- |
| 启动失败 | `logs/launcher/` 中前后端日志、Python/Node.js 版本、端口占用。 |
| 页面无法访问 API | `/health`、实际启动端口、`NEXT_PUBLIC_API_BASE_URL`、浏览器控制台。 |
| AI 功能不可用 | 本机环境变量、数据授权、提供方可达性和 `/api/runtime-settings` 掩码摘要。 |
| Runtime 返回 `403` | `ASTERIA_ENABLE_CODEX_RUNTIME_API` 或本机 Skill 安装开关是否明确启用。 |
| 正式 PDF 被阻断 | AI trace、schema、确定性数值、证据、质量分与 `FormalPDFReleaseGate` 结果。 |

发布流程请继续阅读 [发布与运维指南](release-operations.zh-CN.md)。
