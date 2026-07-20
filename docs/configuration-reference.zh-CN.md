# Asteria Analyst 配置参考

本文件列出当前公开版本中面向使用者、开发者或本机管理员的配置契约。它区分稳定的日常配置、便携版启动设置和高权限扩展设置；不会把仅供内部实验或测试使用的环境变量承诺为长期公共接口。

所有示例都应写入本机 `.env` 或进程环境，**不要**提交 `.env`、真实 API Key、私有 URL、客户数据或包含这些内容的日志。以仓库根目录的 `.env.example` 为起点：

```powershell
Copy-Item .env.example .env
```

源码启动器会读取根目录的可选 `.env`。便携版使用者通常不需要配置 AI 或 Runtime；只有明确需要相关能力时才在本机环境中设置变量。

## 1. 配置优先级与存放位置

| 层级 | 位置 | 适用场景 | 注意事项 |
| --- | --- | --- | --- |
| 进程环境变量 | 当前 PowerShell、启动脚本或系统环境 | 临时测试、便携版启动参数 | 关闭窗口后可能失效；不要把密钥回显到终端。 |
| 根目录 `.env` | 源码工作区 | 本机开发/日常源码启动 | 已忽略，不应上传。 |
| 私有 `settings.json` | 源码模式 `workspace/storage/`；便携模式 `%APPDATA%\AsteriaAnalyst` 或 `ASTERIA_DATA_DIR` | 本机持久化运行偏好 | 不应进入 `/storage` 或 Git。 |
| `.env.example` | 仓库根目录 | 无密钥模板和文档来源 | 不能填入真实值后提交。 |

运行设置服务会优先读取环境变量和持久化偏好，但有安全例外：Codex Runtime 和 Runtime API 每次启动都由环境开关重新决定，持久化设置不能在新版本启动后自动重新开启高权限执行。

## 2. AI 提供方配置

| 变量 | 默认值 | 作用 | 风险与注意事项 |
| --- | --- | --- | --- |
| `OPENAI_API_KEY` | 空 | 为 AI 辅助字段语义、业务路由、报告或修订提供凭据。 | 仅保存在本机私有环境；响应接口只应显示掩码，不应把原值交给浏览器。 |
| `OPENAI_BASE_URL` | 空 | 指向兼容的模型提供方或中继地址。空值表示使用默认 OpenAI Responses API 端点。 | 先确认该提供方被授权处理相应数据、地区、保留和审计要求。 |
| `OPENAI_MODEL` | `gpt-5.4` | 选择模型名称。 | 可用性取决于提供方；修改模型不改变正式报告必须经过确定性计算的规则。 |
| `OPENAI_REASONING_EFFORT` | `xhigh` | 设置 AI 推理强度偏好。 | 提高强度可能改变耗时/费用，不保证数值或报告会自动通过门禁。 |

基础 CSV/Excel 查看和本地统计不要求 API Key。启用 AI 后，相关字段上下文、业务背景、报告上下文或上传的工作簿/PDF 可能发送给已配置提供方；使用前应先脱敏并确认数据授权。

## 3. 本机网络与前端地址

| 变量 | 默认值 | 作用 | 使用边界 |
| --- | --- | --- | --- |
| `ASTERIA_CORS_ALLOW_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | 指定允许的浏览器 Origin，逗号分隔。 | CORS 不是认证机制；不要用它替代公网访问控制。 |
| `ASTERIA_CORS_ALLOW_ORIGIN_REGEX` | 匹配 `localhost`/`127.0.0.1` 与任意端口的本机正则 | 补充 Origin 匹配规则。 | 放宽到公网域名不会使应用变成安全的共享服务。 |
| `NEXT_PUBLIC_API_BASE_URL` | `http://127.0.0.1:8000` | 前端构建时使用的 API 基地址。 | `NEXT_PUBLIC_` 表示值可能出现在浏览器构建产物中，绝不可放入密钥。 |
| `NEXT_PUBLIC_API_SAME_ORIGIN` | 构建便携静态导出时由脚本临时设置 | 让导出前端通过同源 API 工作。 | 由 `scripts/build_portable.ps1` 管理，普通源码使用者无需设置。 |

默认启动器故意只绑定回环地址。不要仅通过修改 CORS、端口转发或反向代理把 API 公开到互联网。

## 4. 桌面启动变量与 Windows 便携包行为

以下变量由 `backend/run_desktop.py` 支持，适用于源码模式或由受控运维脚本自行启动的场景。

| 变量 | 源码启动默认值 | 作用 | 便携包中的实际行为 |
| --- | --- | --- | --- |
| `ASTERIA_HOST` | `127.0.0.1` | 后端监听地址。 | 公开便携包按回环地址健康检查和打开页面；不要通过预设此变量把它改成局域网/公网地址。需要其他监听策略时，应为受控部署单独设计。 |
| `ASTERIA_PORT` | `8787` | 源码/自定义启动器的后端端口。 | 生成的 `start-asteria.ps1` 会从 `8787` 到 `8817` 选择可用端口，并覆盖启动前已有的值。用户不能靠预设此变量固定便携包端口。 |
| `ASTERIA_LAUNCH_PATH` | `/revision` | 源码桌面启动器要打开的本机页面路径。 | 生成的便携启动器固定为 `/analysis` 并覆盖启动前已有的值。 |
| `ASTERIA_OPEN_BROWSER` | `1` | `0`、`false`、`no` 或 `off` 时禁止源码桌面启动器自动打开浏览器。 | 生成的便携启动器将后端自动开浏览器关闭，待健康检查通过后由启动脚本打开 `/analysis`；预设此变量不能改变该行为。 |
| `ASTERIA_DATA_DIR` | 由路径服务决定；冻结/便携模式通常为 `%APPDATA%\AsteriaAnalyst` | 覆盖用户数据目录。 | 生成的便携启动器固定使用 `%APPDATA%\AsteriaAnalyst`，以避免把用户数据写入解压目录或 Git 仓库。 |

便携 ZIP 是自管理的本机交付物，不把上述变量当作用户配置界面。它的端口、启动页、数据目录和浏览器启动流程由包内 `start-asteria.ps1` 统一控制，以保证双击启动时能使用实际可用的本机地址。需要固定端口、无浏览器模式或自定义存储路径时，应使用源码模式或专门的受控部署脚本，而不是修改公开便携包的默认行为。

## 5. R 运行时配置

| 变量 | 默认值 | 作用 | 注意事项 |
| --- | --- | --- | --- |
| `ASTERIA_RSCRIPT_PATH` | 空 | 显式指定 `Rscript` 路径。 | 仅在本机确有受信任的 R 安装时设置。 |

若没有显式路径，系统会在可用的捆绑 R 运行时中查找 `Rscript.exe`。R 工作流是可选能力；R 的存在不意味着所有报告任务都应或都会使用 R。

## 6. Codex Runtime 配置

这些变量影响高权限本机运行时。它们默认关闭或受严格限制，不能作为共享服务的授权方案。

| 变量 | 默认值 | 作用 | 使用规则 |
| --- | --- | --- | --- |
| `ASTERIA_CODEX_RUNTIME_ENABLED` | `false` | 允许 Codex Runtime 基础能力。 | 仅在受信任本机明确启用。 |
| `ASTERIA_ENABLE_CODEX_RUNTIME_API` | `false` | 允许报告智能体、Runtime 进程、Codex Run、流水线和学习账本 HTTP API。 | 启用前先确认工作区、日志和工件没有暴露给其他用户。 |
| `ASTERIA_ALLOW_UNSANDBOXED_CODEX_RUNTIME` | `false` | 允许已请求的非沙箱 Runtime 选项真正生效。 | 高风险；必须同时有运行时请求/持久偏好，单独设置它不会自动开启 Runtime。 |
| `ASTERIA_CODEX_CLI_PATH` | `codex` | 指定 Codex CLI 可执行文件。 | 使用绝对路径或受信任 PATH，避免命令劫持。 |
| `ASTERIA_CODEX_WORKSPACE_ROOT` | 源码模式默认仓库根目录；冻结模式默认空 | 限定 Codex 工作区根目录。 | 选择最小必要目录，禁止指向包含无关私密文件的磁盘根目录。 |
| `ASTERIA_CODEX_SEARCH_ENABLED` | `false` | 允许 Codex 搜索相关能力。 | 可能扩大检索数据范围，应按数据授权开启。 |
| `ASTERIA_CODEX_TIMEOUT_SEC` | `1800` | Runtime 超时秒数。 | 增大超时会增加资源占用，不等同于提高成功率。 |
| `ASTERIA_CODEX_USE_LOGIN_AUTH` | `true` | 使用本机登录认证偏好。 | 不在前端或提交记录中记录认证材料。 |
| `ASTERIA_CODEX_BYPASS_APPROVALS_AND_SANDBOX` | `false` | 请求跳过审批/沙箱的持久偏好。 | 即使为真，也必须同时有 `ASTERIA_ALLOW_UNSANDBOXED_CODEX_RUNTIME=1` 才可生效。 |

`GET /api/runtime-settings` 只公开脱敏摘要；当前公开 API 没有写入 Runtime 设置的路由。配置后重启服务，再通过本机设置摘要或 `GET /api/runtime/codex-health` 核对可用性。

## 7. 外部 Skill 与本地 Agent Team

| 变量 | 默认值 | 作用 | 风险 |
| --- | --- | --- | --- |
| `ASTERIA_ENABLE_LOCAL_SKILL_INSTALLER` | `false` | 允许本机导入、安装、挂载和运行外部 Skill 与 Report Agent Team。 | 安装或导入的内容可能扩大执行面，必须先审阅来源。 |

这个变量不提供用户身份验证。它只能用在受信任管理员控制的单机环境中，绝不应因为“有开关”就开放给不受信任浏览器用户。

## 8. 推荐的最小配置

### 仅本地分析

不需要 `.env`。直接启动即可：

```text
start-asteria.bat
```

### 本机 AI 辅助报告

```text
OPENAI_API_KEY=your-local-secret
OPENAI_MODEL=gpt-5.4
# 仅在兼容提供方需要时填写：
# OPENAI_BASE_URL=https://provider.example/v1
```

填写后不要把 `.env` 复制到附件、Issue、Release 或截图中。

### 受控便携版调试

```powershell
.\start-asteria.bat
```

启动器会自行选择并显示实际端口，随后打开 `/analysis`。若需要查看日志，请在包内的 `backend\desktop-start.out.log` 与 `backend\desktop-start.err.log` 中排查；不要假定始终使用 `8787`，也不要通过开放防火墙解决端口问题。以上仅用于本机排障，不能用于对外提供服务。

## 9. 配置变更检查单

1. 确认变量属于本文件或 `.env.example` 中公开支持的范围。
2. 密钥是否只出现在本机私有环境中，且没有进入 Git 状态、日志、截图或公开产物？
3. 启用 AI 前，是否完成数据授权和脱敏评估？
4. 启用 Runtime、Skill 或非沙箱选项前，是否确认了工作目录与导入来源？
5. 是否保持 `127.0.0.1`，没有把服务向局域网或互联网暴露？
6. 修改后是否重启服务，并检查健康接口、实际功能和启动日志？

安全与部署限制见 [安全与部署说明](security-deployment.zh-CN.md)，技术路由见 [API 参考](api-reference.zh-CN.md)。
