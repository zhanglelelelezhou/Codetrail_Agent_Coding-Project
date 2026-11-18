# CodeTrail 改造记录

## 继承的教程能力

以下模块来自原始 ZIP，不能作为本次新增工作：Agent 工具循环、Textual TUI、多 Provider 客户端、上下文压缩、会话与记忆、MCP、权限规则、子 Agent、团队协作、Git Worktree、Hook、流式 JSON 输出和远程模式。

源码来源和原始哈希见 [NOTICE](../NOTICE.md) 与 [原始文件清单](source-manifest.json)。

## 本次改造

| 改动 | 用户可以观察到的结果 | 主要位置 |
| --- | --- | --- |
| 项目标识迁移 | 使用 `codetrail` 命令、Python 包和 `.codetrail` 配置目录 | `pyproject.toml`、`codetrail/`、`tests/` |
| 首次配置初始化 | `--init` 生成配置模板，已有文件不会被覆盖 | `codetrail/onboarding.py` |
| 离线配置诊断 | `--doctor` 检查配置、凭据、Git 与 MCP 命令，支持 JSON | `codetrail/onboarding.py` |
| 环境变量修复 | Provider 解析 `${ENV_VAR}`；缺失变量给出明确错误 | `codetrail/config.py` |
| 指定配置文件 | `--config PATH` 选择独立配置，用于隔离项目与排错 | `codetrail/__main__.py` |
| 统一版本 | CLI、TUI、`/status` 读取同一版本来源 | `codetrail/__init__.py` |
| 测试与技术文档 | 新增功能测试、CI、架构说明和验证记录 | `tests/`、`.github/`、`docs/` |
| Windows 测试修复 | 多步工具调用测试使用临时目录，避免硬编码 `/tmp` | `tests/test_agent.py` |

原文件中的来源署名保留；已清理与项目功能无关的推广注释，第三方技能内容未修改。

## 后续可选方向（尚未实现）

1. **运行记录与预算**：将已有 Usage / Tool 事件写入 SQLite，展示每轮 token、耗时和失败工具；预算达到上限时终止任务。
2. **离线评测集**：使用固定的模拟模型响应，验证读文件、编辑、权限拒绝和工具失败恢复；输出可复现报告。
3. **配置分层重构**：保留“未设置”和“显式 false / default”的区别，解决现有部分覆盖逻辑无法关闭上一层开关的问题。

功能清单随实现进度更新，性能指标由实际测量获得。
