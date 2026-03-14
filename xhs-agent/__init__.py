"""
XHS Agent - 小红书数据采集、分析、策略生成完整平台。

主要功能：
1. 采集 (Pipelines) - 从小红书采集笔记、达人、评论数据
2. 分析 (Analysis) - 分析笔记表现、用户情感、内容趋势
3. 生成 (Strategy) - 基于分析结果生成最优种草策略
4. 存储 (Storage) - 数据持久化（JSON / SQLite）
5. 集成 (Integrations) - 与 xiaohongshu-cli 和 ohmyxhs SKILL 集成

快速开始:

    # 采集笔记和评论
    from xhs_agent.pipelines.collection import BatchCollector

    async def main():
        collector = BatchCollector()
        result = await collector.collect_notes_with_comments(
            keywords=['护肤', '眼膜']
        )
        print(f"采集了 {len(result)} 条笔记")

    import asyncio
    asyncio.run(main())

    # 或者使用同步接口
    from xhs_agent.pipelines.collection.base import SyncCollectorAdapter
    from xhs_agent.pipelines.collection import NoteAggregator

    note_collector = NoteAggregator()
    sync_collector = SyncCollectorAdapter(note_collector)
    notes = sync_collector.collect(['note_1', 'note_2'])
"""

from xhs_agent.types import (
    # 枚举
    ContentStyle,
    SentimentType,
    PriceLevel,
    ProductCategory,
    EmotionType,
    NoteType,

    # 基础实体
    CelebData,
    NoteData,
    Comment,

    # 富化数据
    NoteWithComments,

    # 分析结果
    PerformanceMetrics,
    SentimentReport,
    StrategySignals,

    # 产品信息
    ProductInfo,

    # 输出
    XhsStrategyPlan,

    # 配置
    CollectionConfig,
    CollectionResult,
)

from xhs_agent.pipelines.collection import (
    BaseCollector,
    CelebAggregator,
    NoteAggregator,
    CommentAggregator,
    BatchCollector,
)

from xhs_agent.pipelines.analysis import (
    NotePerformanceAnalyzer,
    CommentSentimentAnalyzer,
    TrendAnalyzer,
    AnalysisOrchestrator,
)

from xhs_agent.storage import (
    BaseStorage,
    StorageManager,
    StorageContext,
    JSONStorage,
)

from xhs_agent.strategy import (
    StrategyGenerator,
    generate_strategy_plan,
)

from xhs_agent.core import (
    XHSAgentOrchestrator,
    run_xhs_agent,
)

__version__ = "0.1.0"

__all__ = [
    # Types
    "ContentStyle",
    "SentimentType",
    "PriceLevel",
    "ProductCategory",
    "EmotionType",
    "NoteType",

    # Entities
    "CelebData",
    "NoteData",
    "Comment",
    "NoteWithComments",

    # Analysis
    "PerformanceMetrics",
    "SentimentReport",
    "StrategySignals",

    # Product & Output
    "ProductInfo",
    "XhsStrategyPlan",

    # Config
    "CollectionConfig",
    "CollectionResult",

    # Collectors
    "BaseCollector",
    "CelebAggregator",
    "NoteAggregator",
    "CommentAggregator",
    "BatchCollector",

    # Analyzers
    "NotePerformanceAnalyzer",
    "CommentSentimentAnalyzer",
    "TrendAnalyzer",
    "AnalysisOrchestrator",

    # Storage
    "BaseStorage",
    "StorageManager",
    "StorageContext",
    "JSONStorage",

    # Strategy
    "StrategyGenerator",
    "generate_strategy_plan",

    # Core
    "XHSAgentOrchestrator",
    "run_xhs_agent",
]
