# Asteria Analyst 发布与运维指南

本指南定义公开 GitHub 发布前的可复现检查、Windows 便携包构建、Release 资产验收和回滚原则。它不允许把“本地文件夹能启动”或“某个提交已 push”表述为“公开 Release 已经可用”。

## 1. 发布对象与完成定义

| 对象 | 面向谁 | 成立条件 |
| --- | --- | --- |
| 源码提交 | 开发者和审阅者 | 变更已提交、已 push，CI/本地检查结果明确。 |
| GitHub 标签 | 版本定位 | 标签指向已验证的不可变提交。 |
| GitHub Release | 终端用户 | 已实际创建 Release，说明、版本、资产和校验和与标签一致。 |
| Windows 便携包 | Windows 本机使用者 | ZIP 可完整解压、可在干净环境启动、健康检查与核心工作流通过。 |
| 正式 `management_report.pdf` | 报告交付使用者 | 同时满足 AI trace、schema、确定性计算、证据校验、质量门禁和分数不低于 90。 |

不要把本地报告工作区中的“发布”与 GitHub Release 混为一谈，也不要把 GitHub Release 与正式管理报告的业务发布门禁混为一谈。

## 2. 发布前总检查

在仓库根目录执行：

```powershell
git status --short
git diff --check
```

`git status --short` 应只显示本次计划发布的代码、文档或构建定义变更。以下内容不得进入提交或 Release 资产：

- `.env`、API Key、Token、密码、私有 Base URL；
- 客户数据、上传文件、生成报告、修订会话、附件、日志、缓存、运行状态；
- 机器用户目录、内部域名、真实绝对路径或未授权的作品集材料；
- 未获授权的第三方二进制、数据或图片；
- 临时 ZIP、构建目录或历史备份目录。

发布前还要核对：

1. README、文档中心、模块/功能参考、API、配置、安全和发布文档互相链接有效；
2. 页面、路由、配置变量和便携包文件名与当前代码一致；
3. 当前版本的已知限制已写入 Release 说明，尤其是“仅本机回环单用户使用”；
4. 若尚未选择许可证，Release 文案不应暗示已经开放复制、再分发或商用权利；
5. 若要接受安全报告，仓库所有者已配置并验证私密报告渠道。

## 3. 必做验证

### 3.1 后端与前端

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m pytest

Set-Location ..\frontend
npm ci
npm run lint
npm run verify:method-guide
npm run build
```

项目 CI 在 Ubuntu 上运行后端 pytest，以及前端 `lint`、`verify:method-guide`、生产构建和高危生产依赖审计。发布验证还覆盖 Windows 启动器、便携 ZIP、浏览器和本机权限边界。

### 3.2 源码启动器冒烟

在支持的 Windows 环境中：

1. 运行 `start-asteria.cmd`；
2. 记录启动器打印的实际前端地址和健康地址；
3. 访问 `<实际后端地址>/health`，确认返回 `{"status":"ok"}`；
4. 在 `/analysis` 上传 `examples/revenue-smoke.csv` 或其他无敏感样本；
5. 选择正确工作表，查看数据画像，运行一个基础统计或 Lab 方法；
6. 确认生成的表格、图表或工件可被本机页面访问；
7. 检查 `logs/launcher/`，确认没有把密钥或真实数据写入将被公开的日志。

没有实际完成上述步骤时，Release 说明应写“未验证”或“受环境阻塞”，不得写成“已通过”。

### 3.3 正式报告变更的额外验证

只要发布包含报告生成、AI 编排、指标、证据或 PDF 变更，除常规测试外，还必须核对：

- `AIFieldSemanticMapper`、`AIBusinessContextRouter`、`AIMetricDerivationPlanner` 都在报告绑定前运行并保存 trace；
- AI 输出已经过 schema 验证；
- 正式数值由确定性执行器计算；
- `EvidenceValidator` 已验证证据；
- `FormalPDFReleaseGate` 明确放行，且最终质量分不少于 `90`；
- 任一条件不满足时只能产生 `debug_report`，不能发布正式 `management_report.pdf`。

## 4. 构建 Windows 便携包

便携包脚本位于 `scripts/build_portable.ps1`，它构建前端静态导出、复制后端与运行时、检查可携带 Python 依赖，并生成启动器和 ZIP。构建前应关闭正在使用该便携目录的 Asteria 进程，保留足够磁盘空间，并在没有敏感运行数据的工作区中操作。

标准构建：

```powershell
PowerShell -ExecutionPolicy Bypass -File .\scripts\build_portable.ps1
```

调试构建可使用脚本已提供的参数：

```powershell
PowerShell -ExecutionPolicy Bypass -File .\scripts\build_portable.ps1 -SkipFrontendExport -SkipZip
```

只有在前端导出已由同一提交成功生成、且明确只需要检查目录结果时才使用跳过参数。正式 Release 必须重新构建完整 ZIP，不能复用来源不明的旧文件。

默认产物位于：

```text
workspace\release\AsteriaAnalyst-portable\
workspace\release\AsteriaAnalyst-portable.zip
```

目录构建完成后，继续执行以下 ZIP 发布验收。

## 5. 便携包验收

### 5.1 资产清单

解压到一个全新的可写目录，检查至少存在：

```text
start-asteria.bat
start-asteria.ps1
USER-GUIDE.txt
使用指南.zh-CN.md
backend\run_desktop.py
runtime\python\python.exe
```

若构建选择了 R 运行时，相关 `runtime\R-*` 目录也应与 Release 说明一致。不要把 `.env`、`workspace/storage`、用户数据目录或本机缓存打入 ZIP。

### 5.2 校验和

为 ZIP 生成 SHA-256，并同时上传文本校验文件或在 Release 说明中提供完整值：

```powershell
Get-FileHash .\workspace\release\AsteriaAnalyst-portable.zip -Algorithm SHA256
```

下载者应使用同一命令核对文件名和哈希。校验和确认下载文件与发布文件一致；功能测试和安全审计作为独立发布检查执行。

### 5.3 干净环境冒烟

1. 在没有该项目源码的 Windows 用户目录中完整解压 ZIP；
2. 不在压缩包预览器、只读目录、桌面同步公共目录或 `Program Files` 中直接运行；
3. 双击 `start-asteria.bat`；
4. 等待浏览器打开，或访问启动脚本显示的本机 `/analysis` 地址；
5. 检查 `<实际地址>/health` 返回 `{"status":"ok"}`；
6. 上传无敏感样本，确认数据画像、一个基础分析和报告/工件浏览至少可用；
7. 关闭浏览器后再打开启动器，确认它不会无故启动重复服务；
8. 检查 `backend\desktop-start.err.log` 是否包含启动错误。

便携包默认验收覆盖基础本地分析。Release 明确声明运行时、开关、数据边界和测试结果后，再将 AI、Codex Runtime、外部 Skill 和非沙箱能力纳入对应验收。

## 6. 创建 GitHub Release

建议按以下顺序进行：

1. 确认目标提交已 push，CI 结果可查；
2. 创建指向该提交的新版本标签；不要把新文档或修复宣称为已存在旧标签的内容；
3. 创建同名 GitHub Release；
4. 上传与该标签同一次构建得到的 `AsteriaAnalyst-portable.zip` 和 SHA-256 校验信息；
5. 在 Release 说明中写明版本、目标提交、支持平台、启动方法、已验证项、未验证项、已知限制和升级/回滚说明；
6. 从 Release 页面重新下载一次资产，按 5.3 完成最终冒烟。

Release 说明最少应包含：

```text
版本：vX.Y.Z
目标提交：<commit SHA>
平台：Windows 本机单用户、仅 127.0.0.1
资产：AsteriaAnalyst-portable.zip
校验：SHA-256 <hash>
已验证：<具体命令与冒烟结果>
限制：不支持公网/多用户托管；AI 与高权限 Runtime 默认关闭
升级：备份 %APPDATA%\AsteriaAnalyst 后使用新目录解压运行
```

不要写“永久可用”“完全安全”“AI 自动保证正确”或“已支持公网多用户”之类无法验证的承诺。

## 7. 回滚与问题处理

GitHub Release 一旦被用户下载，不应通过偷偷替换同名资产来掩盖问题。出现严重问题时：

1. 先在 Release 说明中标明受影响版本、风险和停止使用建议；
2. 保留可追溯的标签和校验和，不篡改历史证据；
3. 用修复提交构建新资产，生成新版本/新标签/新校验和；
4. 在新 Release 中说明升级和回滚路径；
5. 若问题涉及密钥、真实数据或漏洞细节，转入私密安全处理，不在公开 Release Notes 暴露敏感材料。

用户升级前应备份 `%APPDATA%\AsteriaAnalyst`，并将新包解压到新目录。只有验证新版本能启动、数据可访问且关键流程可用后，才删除旧包或旧备份。

## 8. 发布记录与文档同步

每个 Release 都应更新或检查：

- `README.md` 的下载链接与文档索引；
- `docs/README.md` 的技术入口；
- 本次变更涉及的 API、配置、架构、安全、便携包和用户文档；
- Release 说明、标签、ZIP 名称和 SHA-256 是否一致；
- 发布后 GitHub 页面能否打开 README、中文文档和下载资产。

对于历史标签，文档仅描述该标签实际包含的内容。后续补齐的中文文档或便携包指南通过新的提交、标签和 Release 发布。
