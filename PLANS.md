# PLANS.md

本文件用于复杂任务的统一规划，目标是减少返工并提高可验证性。

## 何时需要写计划
- 预计改动跨多个目录或模块。
- 需求存在歧义，容易出现错误实现。
- 需要分阶段交付（例如先改 CLI，再改 pipeline，再补测试）。

## 任务计划模板

复制以下模板并填写：

```markdown
## Task: <任务名>

### Goal
- <要达成的行为变化>

### Context
- 相关路径: <file/dir>
- 相关现象/报错: <error/log/command>

### Constraints
- 架构约束: <如接口兼容、模块边界>
- 安全约束: <如不落地密钥、输入校验>
- 运行约束: <如仅修改某子项目>

### Done when
- [ ] 功能行为满足预期
- [ ] 相关测试通过
- [ ] 无明显回归
- [ ] 交付包含变更摘要、验证结果、风险说明

### Plan
1. [ ] 信息收集与最小复现
2. [ ] 最小可行改动
3. [ ] 补充/更新测试
4. [ ] 本地验证与回归检查
5. [ ] 输出交付与风险说明

### Verification Commands
- <command 1>
- <command 2>
- <command 3>

### Notes
- 决策: <关键取舍>
- 风险: <潜在影响>
- 回退: <失败时如何回滚>
```

## 使用约定
- 复杂任务开始前先创建一个 `Task` 区块。
- 执行过程中勾选 `Plan` 与 `Done when`。
- 完成后补齐 `Verification Commands` 的执行结果。

---

## Task: xiaohongshu-cli ASR API 接入（暂停）

### Goal
- 在现有 `xhs script --asr` 基础上新增云端 ASR Provider（计划优先 Qwen3-ASR），支持更高识别准确率与可控成本。

### Context
- 相关路径: `xiaohongshu-cli/xhs_cli/asr_transcriber.py`, `xiaohongshu-cli/xhs_cli/commands/reading.py`
- 当前状态:
  - 本地链路已可用：视频 -> 音频 -> Whisper -> `plain/timecode/srt`
  - 已支持 `--srt` 输出
  - 待办：云端 API provider 抽象与接入

### Constraints
- 架构约束: 保持 `xhs script` 命令向后兼容，默认本地模式不变
- 安全约束: API Key 必须走环境变量，不写入源码
- 运行约束: 仅改动 `xiaohongshu-cli` 子项目

### Done when
- [ ] 支持 `--asr-provider local|qwen3`
- [ ] 支持 `QWEN3_ASR_API_KEY` 环境变量读取
- [ ] provider 失败时有可观测错误，不静默降级
- [ ] 补齐 provider 相关单测与 CLI 参数测试

### Plan
1. [x] 本地 ASR 和 SRT 输出打通（当前已完成）
2. [ ] 设计 provider 接口（统一返回 `text/segments/srt`）
3. [ ] 接入 Qwen3-ASR API
4. [ ] 增加配置参数与帮助文档
5. [ ] 回归测试与错误处理验证

### Notes
- 状态: `Paused`（等待购买并提供 Qwen3-ASR API）
- 恢复条件: 提供可用 API Key 与接口文档
