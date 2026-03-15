# XHS Agent - 小红书数据采集、分析、策略生成平台

## 📋 概述

XHS Agent 是一个完整的小红书内容策略生成平台，包含三个核心环节：

```
采集数据 → 分析洞察 → 生成策略
```

### 功能模块

- **采集管道** (`pipelines/collection/`) — 采集笔记、达人、评论数据
- **分析管道** (`pipelines/analysis/`) — 分析笔记表现、用户情感、趋势
- **策略生成** (`strategy/`) — 基于分析结果生成最优种草方案
- **数据存储** (`storage/`) — JSON / SQLite 数据持久化
- **集成层** (`integrations/`) — 与 xiaohongshu-cli、ohmyxhs 集成

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- xiaohongshu-cli（用于 API 调用）
- 小红书有效的 Cookie

### 安装依赖

```bash
# 确保 xiaohongshu-cli 已安装
cd ../xiaohongshu-cli
uv sync

# 回到 xhs-agent
cd ../xhs-agent
uv sync
```

本项目使用 `pyproject.toml` + `uv.lock` 固定依赖版本，推荐统一使用 `uv sync` / `uv run ...`。

### 基础使用

#### 1️⃣ 采集笔记

```python
import asyncio
from xhs_agent.pipelines.collection import NoteAggregator

async def main():
    aggregator = NoteAggregator()
    try:
        notes = await aggregator.collect_async(
            keywords=['护肤', '眼膜']
        )
        print(f"采集了 {len(notes)} 条笔记")
        for note in notes[:3]:
            print(f"  - {note.title} ({note.likes} 赞)")
    finally:
        await aggregator.close()

asyncio.run(main())
```

#### 2️⃣ 采集笔记和评论

```python
from xhs_agent.pipelines.collection import BatchCollector

async def main():
    collector = BatchCollector()
    try:
        result = await collector.collect_notes_with_comments(
            keywords=['护肤']
        )
        print(f"采集了 {len(result)} 条笔记及其评论")
    finally:
        collector.print_summary()

asyncio.run(main())
```

#### 3️⃣ 完整的端到端采集

```python
async def main():
    collector = BatchCollector()
    try:
        result = await collector.collect_all(
            keywords=['护肤', '眼膜'],
            celebrity_ids=['user_1', 'user_2']
        )

        print(f"采集统计:")
        print(f"  - 笔记数: {result['summary']['total_notes']}")
        print(f"  - 达人数: {result['summary']['total_celebrities']}")
    finally:
        collector.print_summary()

asyncio.run(main())
```

---

## 📂 项目结构

```
xhs-agent/
├── types.py                           # 数据类型定义（Pydantic 模型）
├── config.py                          # 配置管理
├── __init__.py                        # 包导出
├── examples.py                        # 使用示例
├── README.md                          # 本文件
│
├── pipelines/
│   ├── collection/                    # 采集管道
│   │   ├── __init__.py
│   │   ├── base.py                    # 基类和接口
│   │   ├── notes.py                   # 笔记采集器
│   │   ├── celebrity.py               # 达人采集器
│   │   ├── comments.py                # 评论采集器
│   │   └── batchers.py                # 批量采集协调
│   │
│   └── analysis/                      # 分析管道（待实现）
│       ├── __init__.py
│       ├── performance.py             # 笔记表现分析
│       ├── sentiment.py               # 情感分析
│       └── trends.py                  # 趋势分析
│
├── storage/                           # 存储层（待实现）
│   ├── base.py                        # 存储接口
│   ├── json_store.py                  # JSON 存储
│   └── sqlite_store.py                # SQLite 存储
│
├── strategy/                          # 策略生成（待实现）
│   ├── generator.py                   # 策略生成器
│   └── optimizer.py                   # 策略优化
│
└── integrations/                      # 第三方集成（待实现）
    ├── xhs_api.py                     # xiaohongshu-cli 包装
    ├── ohmyxhs_caller.py              # ohmyxhs 调用
    └── llm_fallback.py                # LLM 降级方案
```

---

## 🔧 核心 API

### 数据模型

#### NoteData - 笔记
```python
from xhs_agent.types import NoteData

note = NoteData(
    note_id="note_123",
    title="护肤新手必看",
    content="今天分享一下...",
    author_id="user_123",
    likes=1000,
    comments_count=100,
    ...
)
```

#### CelebData - 达人
```python
from xhs_agent.types import CelebData

celeb = CelebData(
    celeb_id="user_123",
    name="小红书达人",
    followers=100000,
    interaction_rate=0.05,
    content_styles=["tutorial", "story"],
    ...
)
```

#### NoteWithComments - 完整笔记
```python
from xhs_agent.types import NoteWithComments

note_with_comments = NoteWithComments(
    note=note,
    comments=[comment1, comment2, ...],
    author_data=celeb
)
```

### 采集器接口

#### NoteAggregator - 笔记采集
```python
aggregator = NoteAggregator(config)

# 按关键词搜索
notes = await aggregator.collect_async(
    keywords=['护肤', '眼膜'],
    sort='popular',
    max_results=100
)

# 采集单个笔记
note = await aggregator.collect_single('note_123')

# 批量采集
notes = await aggregator.collect_batch_async(
    ['note_1', 'note_2', 'note_3']
)
```

#### CelebAggregator - 达人采集
```python
aggregator = CelebAggregator(config)

# 批量采集达人
celebs = await aggregator.collect_batch_async(
    ['user_1', 'user_2', 'user_3']
)
```

#### CommentAggregator - 评论采集
```python
aggregator = CommentAggregator(config)

# 采集笔记的评论
comments = await aggregator.collect_async(note_id='note_123')

# 采集笔记及其评论
note_with_comments = await aggregator.collect_note_with_comments(note)
```

#### BatchCollector - 批量协调
```python
collector = BatchCollector()

# 完整流程
result = await collector.collect_all(
    keywords=['护肤'],
    celebrity_ids=['user_1', 'user_2']
)

# 或分步操作
notes = await collector.collect_notes_only(keywords=['护肤'])
notes_with_comments = await collector.collect_notes_with_comments(keywords=['护肤'])
celebs = await collector.collect_celebrities(celebrity_ids=['user_1'])
```

---

## ⚙️ 配置管理

### 采集配置

```python
from xhs_agent.types import CollectionConfig

config = CollectionConfig(
    # 并发设置
    concurrent_requests=5,        # 并发请求数
    request_timeout=30,           # 请求超时（秒）
    retry_attempts=3,             # 重试次数
    rate_limit_delay=1.0,         # 请求间隔延迟（秒）

    # 采集限制
    max_notes_per_search=100,     # 每个搜索最多采集笔记数
    max_comments_per_note=200,    # 每个笔记最多采集评论数

    # 存储设置
    storage_backend='json',       # 存储后端
    storage_path='data/',         # 存储路径
)

aggregator = NoteAggregator(config)
```

### 全局配置

在 `config.py` 中配置：

```python
# 路径
DATA_DIR = Path("data/")
LOG_DIR = Path("logs/")

# 采集配置
DEFAULT_COLLECTION_CONFIG = CollectionConfig(...)

# 分析权重
HEAT_SCORE_WEIGHTS = {
    "likes": 0.4,
    "comments": 0.35,
    "shares": 0.25,
}

# 关键词列表
POSITIVE_KEYWORDS = ["好用", "效果好", ...]
NEGATIVE_KEYWORDS = ["不好用", "没效果", ...]
PURCHASE_SIGNAL_KEYWORDS = ["回购", "已下单", ...]
```

---

## 📊 数据流

### 单个笔记采集流程

```
搜索笔记 (NoteAggregator)
    ↓
获取笔记详情
    ↓
提取互动数据
    ↓
转换为 NoteData
    ↓
存储 / 返回
```

### 完整采集流程

```
搜索笔记 (NoteAggregator)
    ↓
批量获取评论 (CommentAggregator)
    ↓
批量获取达人信息 (CelebAggregator)
    ↓
汇总结果
    ↓
保存数据库
```

---

## 🔄 异步 / 同步

### 异步使用（推荐）

```python
import asyncio

async def main():
    aggregator = NoteAggregator()
    try:
        notes = await aggregator.collect_async(keywords=['护肤'])
    finally:
        await aggregator.close()

asyncio.run(main())
```

### 同步使用

```python
from xhs_agent.pipelines.collection.base import SyncCollectorAdapter

aggregator = NoteAggregator()
sync_collector = SyncCollectorAdapter(aggregator)
notes = sync_collector.collect(['note_1', 'note_2'])
sync_collector.close()
```

---

## 🐛 错误处理

采集器内置了重试机制：

```python
# 自动重试：
# - 网络错误：指数退避重试
# - API 错误：使用配置中的 retry_attempts
# - 单个失败不会中断整个采集

# 获取采集结果
result = await collector.collect_batch_async(['note_1', 'note_2', 'bad_note'])
# result 会包含成功采集的项目，失败的会被跳过
```

---

## 📝 日志

采集过程会输出详细日志：

```
INFO:xhs_agent.pipelines.collection.notes:Searching notes for keyword: 护肤 (max: 100)
DEBUG:xhs_agent.pipelines.collection.notes:Fetching note details for: note_123
INFO:xhs_agent.pipelines.collection.base:Collection started at 2026-03-14 10:00:00
...
INFO:xhs_agent.pipelines.collection.base:Collection Summary: 95 succeeded, 5 failed, 45.3 seconds
```

调整日志级别：

```python
import logging

logging.basicConfig(level=logging.DEBUG)  # 详细日志
```

---

## 🚦 下一步（待实现）

### Phase 2: 分析管道
- [ ] 笔记表现指标计算 (`PerformanceMetrics`)
- [ ] 评论情感分析 (`SentimentReport`)
- [ ] 趋势识别 (`TrendAnalysis`)

### Phase 3: 策略生成
- [ ] 调用 ohmyxhs SKILL
- [ ] 基于分析结果优化策略
- [ ] 生成最终的种草方案

### Phase 4: 数据存储
- [ ] JSON 文件存储
- [ ] SQLite 数据库支持
- [ ] 数据查询接口

### Phase 5: 完整集成
- [ ] CLI 工具
- [ ] Web API
- [ ] 数据可视化仪表板

---

## 📚 示例

详见 `examples.py` 获取更多使用示例：

```bash
uv run examples.py
```

---

## 🤝 贡献

欢迎提交 Issue 和 PR！

---

## 📄 许可证

Apache 2.0

---

## 📞 联系

有任何问题或建议，请提交 Issue。
