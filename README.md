# xhs-agent

一个面向小红书数据的工程化项目，目标是把「采集 -> 分析 -> 策略生成」串成可复用的流程。

当前仓库包含：

- `xhs-agent/`：核心 Python 包（数据采集、分析、存储、策略生成）
- `xiaohongshu-cli/`：用于小红书交互与数据读取的 CLI 代码区（以子模块方式管理）
- `.trellis/`：任务流、规范和协作元数据

## 核心能力

- 批量采集笔记、评论、达人信息
- 对采集结果做结构化分析（趋势、情绪、表现等）
- 生成可执行的内容策略输出
- 提供测试与模块化目录，方便二次扩展

## 快速开始

```bash
cd xhs-agent
uv sync
uv run pytest -v
```

依赖与版本通过 `xhs-agent/pyproject.toml` + `xhs-agent/uv.lock` 统一管理，`uv sync` 可一键复现环境。

## 同步上游 xiaohongshu-cli

本仓库将 `xiaohongshu-cli/` 作为子模块管理。更新上游推荐流程：

```bash
# 1) 拉取根仓库代码后初始化子模块
git submodule update --init --recursive

# 2) 进入子模块并同步上游 main
cd xiaohongshu-cli
git checkout main
git pull --ff-only origin main

# 3) 回到根仓库，提交子模块指针变更（如果你要固定到新版本）
cd ..
git add xiaohongshu-cli
git commit -m "chore: bump xiaohongshu-cli submodule"
```

说明：

- 仅在你执行 `git add xiaohongshu-cli` 并提交时，根仓库才会记录新的子模块提交指针。
- 子模块更新不会自动改动 `xhs-agent` 源码；是否兼容由 `xhs-agent` 测试结果决定。

## 致谢

本项目在工程实现中参考并借鉴了以下开源项目（属于二次开发/扩展场景）：

- [jackwener/xiaohongshu-cli](https://github.com/jackwener/xiaohongshu-cli)

感谢原作者与社区贡献。
