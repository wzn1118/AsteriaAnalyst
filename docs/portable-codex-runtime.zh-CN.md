# 便携版 Codex Runtime（中文说明）

> 英文技术说明：[Portable Codex Runtime](portable_codex_runtime.md)。本文件说明公开便携包如何发现可选的本机 Codex Runtime，以及启用所需的本机条件。

## 用途与边界

Codex Runtime 为明确启用后的本机辅助工作流提供能力，例如报告修订工作台所需的本机 `codex app-server`。基础本地文件导入与分析可独立运行，Runtime 和 AI 密钥用于扩展工作流。

公开 Windows 便携包将高权限 Runtime 保持为本机受控扩展。启用操作在使用者管理的本机环境中完成，并遵守 [配置参考](configuration-reference.zh-CN.md) 与 [安全与部署说明](security-deployment.zh-CN.md)。Lab 中的 Skill、Feature Trial 和 Report Agent Team 复用该 Runtime；各入口需要相应的本机开关和输入条件，详见 [本地扩展指南](local-extensions.zh-CN.md)。

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

对于离线便携包，发布者将已核验的 Codex 可执行文件放在 `runtime/codex/bin/`。Runtime 信任来源限于已核验的随包文件、显式路径或本机已安装的受控 CLI。

## 启用条件

Runtime 相关 HTTP 功能在以下条件同时满足后开放：

1. `ASTERIA_CODEX_RUNTIME_ENABLED=1`：允许应用解析和使用本机 Codex Runtime。
2. `ASTERIA_ENABLE_CODEX_RUNTIME_API=1`：允许受控的 Runtime API 路径。
3. Codex CLI 可执行、版本可识别，且 `codex app-server` 可用。
4. 工作区根目录、超时和检索设置符合本机数据边界。

无沙箱执行需显式设置 `ASTERIA_ALLOW_UNSANDBOXED_CODEX_RUNTIME=1`。公开便携包将该开关保持关闭，由本机管理员在受控工作区内按需设置。

完整变量说明见 [配置参考](configuration-reference.zh-CN.md) 中的“Codex Runtime”章节。

## 健康检查与故障定位

当 Runtime 功能已按上文配置后，可使用：

```text
GET /api/runtime/codex-health
```

该检查显示候选路径、实际解析到的二进制、版本与 `codex app-server` 可用性。网页端通过这条接口读取诊断状态；Runtime 启动继续由本机环境变量和受控工作区决定。

常见处理顺序：

1. 先确认基础分析功能可正常启动，再定位 Runtime 配置。
2. 在启动 Asteria 的同一个终端或桌面会话中设置环境变量。
3. 设置绝对路径 `ASTERIA_CODEX_CLI_PATH`，固定 CLI 解析来源。
4. 检查工作区路径与数据目录，明确 Runtime 可读取的项目文件和数据范围。
5. 使用健康检查查看解析结果；Runtime 状态、作业队列和完成事件均以服务端诊断结果呈现。

## 发布者核验清单

- 便携包只收录启动所需运行时、公开代码、文档和经核验的二进制。
- `runtime/codex/bin/` 如存在，只包含发布者明确核验并在发布说明中列出的文件。
- 默认 `ASTERIA_CODEX_RUNTIME_ENABLED`、`ASTERIA_ENABLE_CODEX_RUNTIME_API` 和 `ASTERIA_ALLOW_UNSANDBOXED_CODEX_RUNTIME` 均为关闭。
- 在未配置 Runtime 的干净 Windows 环境验证基础本地分析启动。
- 使用带 Runtime 的隔离测试环境验证健康检查、超时、失败信息和关闭开关均符合预期。

这项能力作为可选本机扩展运行；项目默认部署保持本机、回环地址和单用户优先的边界。
