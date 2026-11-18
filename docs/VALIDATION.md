# 验证记录

验证日期：2026-11-18（Asia/Shanghai）。本地环境：Windows、Python 3.13.3、uv 0.13.9。

## 实际结果

| 检查 | 结果 |
| --- | --- |
| 新增功能测试 | 35 项通过，覆盖 CLI、初始化、诊断、凭据解析与 TUI 配置错误 |
| 完整测试 | **620 passed, 3 skipped**，约 41 秒 |
| TUI 启动 | 演示 Provider 下成功启动，未发送模型请求；截图见 `images/terminal.svg` |
| 分发构建 | `uv build --offline` 成功生成 sdist 与 wheel |
| 资源检查 | 配置模板、TUI 样式与内置 Agent 定义随包分发 |
| 运行数据隔离 | 分发内容不包含 `.venv`、`.codetrail`、`.mewcode` 或缓存目录 |
| 依赖变更 | 保留原锁文件中 54 个第三方包的版本，更新本项目元数据 |
| 来源保留 | 167 个原始 Python 文件保留来源署名，清理了与项目功能无关的推广注释 |

三个跳过项分别是：真实 API 测试未设置 `CODETRAIL_TEST_API_KEY`、Windows 没有测试所需的 `rm`、符号链接测试没有找到合适的系统文件。

原始 ZIP 首轮运行结果为 583 passed、3 skipped、2 failed；其中一项由运行目录不正确引起，切换项目根目录后通过；另一项使用硬编码 `/tmp`，已改为 pytest 的临时目录。原有可执行测试共 585 项，本次新增 35 项，不把继承测试算作新增工作。

## 复现命令

在项目根目录执行：

```powershell
uv sync --locked
uv run pytest -q -rs
uv run pytest tests/test_provider_credentials.py tests/test_onboarding.py tests/test_cli.py -q
uv run codetrail --version
uv build
```

诊断使用演示 Key 即可验证本地解析与退出码。演示 Key 无法用于真实模型请求，测试不会证明远程认证有效。

## 尚未验证

- GitHub Actions 矩阵已配置，本次没有上传触发云端执行。
- Python 3.11、Linux 和 macOS 未在本机运行；不能据此宣称全平台验证完成。
- 真实模型对话、第三方 MCP、远程浏览器接入和多进程队友未进行端到端验证。
- 没有真实用户量、生产部署或性能提升数据。
- 课程源码的公开分发许可仍需核实，见 [NOTICE](../NOTICE.md)。
