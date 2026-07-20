# 便携版 Codex Runtime（中文说明）

> 英文技术说明：[Portable Codex Runtime](portable_codex_runtime.md)。本文件说明公开便携包如何发现可选的本机 Codex Runtime，以及为什么它默认不启用。

## 用途与边界

Codex Runtime 仅服务于明确启用后的本机辅助工作流，例如报告修订工作台所需的本机 `codex app-server` 能力。它不是 Asteria Analyst 的基础分析前提：没有 Codex、没有 AI 密钥时，基础的本地文件导入与分析仍应可以使用。

公开 Windows 便携包不会把高权限 Runtime 默认暴露给浏览器或网络。任何启用都必须发生在使用者受控的本机环境中，并遵守 [配置参考](configuration-reference.zh-CN.md) 与 [安全与部署说明](security-deployment.zh-CN.md)。

## 发现顺序

启动时，系统按以下顺序查找 Codex CLI：

1. 显式设置的 `ASTERIA_CODEX_CLI_PATH`，或已保存的 `codex_cli_path`。
2. 项目/便携包随附位置：
   - `runtime/codex/bin/codex.exe`
   - `runtime/codex/bin/codex.cmd`
   - `workspace/runtime/codex/bin/codex.exe`
   - `backend/tools/codex/bin/codex.exe`
   - `tools/codex/bin/codex.exe`
   - `vendor/codex/bin/codex.exe`
3. 已安装的 Codex Desktop 默认位置：`%LOCALAPPDATA%\OpenAI\Codex\bin\codex.exe`。
4. npm/PATH 候选：`%APPDATA%\npm\codex.cmd`，最后是 `codex`。

对于离线便携包，发布者如决定随包提供 Codex，应将可信的可执行文件放在 `runtime/codex/bin/`。不能把未核验的下载文件、用户工作区里的同名程序或网络共享路径自动当作受信任 Runtime。

## 启用条件

Runtime 相关 HTTP 功能默认关闭。启用前需要同时确认：

1. `ASTERIA_CODEX_RUNTIME_ENABLED=1`：允许应用解析和使用本机 Codex Runtime。
2. `ASTERIA_ENABLE_CODEX_RUNTIME_API=1`：允许受控的 Runtime API 路径。
3. Codex CLI 可执行、版本可识别，且 `codex app-server` 可用。
4. 工作区根目录、超时和检索设置符合本机数据边界。

需要无沙箱执行时，还必须显式设置 `ASTERIA_ALLOW_UNSANDBOXED_CODEX_RUNTIME=1`。这会扩大本机代码执行风险，公开发布的默认配置不应启用它。

完整变量说明见 [配置参考](configuration-reference.zh-CN.md) 中的“Codex Runtime”章节。

## 健康检查与故障定位

当 Runtime 功能已按上文配置后，可使用：

```text
GET /api/runtime/codex-health
```

该检查用于说明候选路径、实际解析到的二进制、版本与 `codex app-server` 可用性。它不应被视为把任意 Runtime 暴露给网页的开关。

常见处理顺序：

1. 先确认基础分析功能可正常启动，避免把 Runtime 问题误判为整个应用无法使用。
2. 检查环境变量是在启动 Asteria 的同一个终端/桌面会话中设置，而不是只写在其他用户或其他 shell 会话中。
3. 设置绝对路径 `ASTERIA_CODEX_CLI_PATH`，避免 PATH 顺序或同名程序造成歧义。
4. 检查工作区路径与数据目录，确保它们不包含不应交给 Runtime 读取的客户数据或密钥。
5. 使用健康检查查看解析结果；缺失 Runtime 时，界面应报告不可用状态，不能伪造“已排队”或“已完成”的结果。

## 发布者核验清单

- 便携包内未包含用户密钥、个人登录状态、聊天记录、工作区数据或未授权二进制。
- `runtime/codex/bin/` 如存在，只包含发布者明确核验并在发布说明中列出的文件。
- 默认 `ASTERIA_CODEX_RUNTIME_ENABLED`、`ASTERIA_ENABLE_CODEX_RUNTIME_API` 和 `ASTERIA_ALLOW_UNSANDBOXED_CODEX_RUNTIME` 均为关闭。
- 使用不带 Runtime 的干净 Windows 环境验证基础本地分析仍可启动。
- 使用带 Runtime 的隔离测试环境验证健康检查、超时、失败信息和关闭开关均符合预期。

这项能力是可选的本机扩展，不是托管服务承诺，也不改变项目“本机、回环地址、单用户优先”的默认部署边界。
