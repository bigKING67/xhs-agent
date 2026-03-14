"""
XHS Agent 使用示例。

演示如何使用采集管道采集笔记、达人、评论数据。
"""

import asyncio
import logging
from typing import List

from xhs_agent.types import (
    NoteData,
    CelebData,
    CollectionConfig,
)
from xhs_agent.pipelines.collection import (
    BatchCollector,
    NoteAggregator,
    CelebAggregator,
    CommentAggregator,
)
from xhs_agent.pipelines.collection.base import SyncCollectorAdapter

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# =============================================================================
# 示例 1: 基础笔记采集（异步）
# =============================================================================

async def example_1_collect_notes_async():
    """
    异步采集笔记。

    这是最基础的用法，演示如何搜索笔记。
    """
    logger.info("Example 1: Collecting notes (async)")

    aggregator = NoteAggregator()
    try:
        notes = await aggregator.collect_async(
            keywords=["护肤", "眼膜"],
        )
        logger.info(f"Collected {len(notes)} notes")
        for note in notes[:3]:
            logger.info(f"  - {note.title} ({note.likes} likes)")
    finally:
        await aggregator.close()


# =============================================================================
# 示例 2: 笔记采集（同步）
# =============================================================================

def example_2_collect_notes_sync():
    """
    同步采集笔记。

    如果你在同步代码中工作，可以使用 SyncCollectorAdapter 来适配。
    """
    logger.info("Example 2: Collecting notes (sync)")

    aggregator = NoteAggregator()
    sync_collector = SyncCollectorAdapter(aggregator)

    try:
        notes = sync_collector.collect(["note_1", "note_2", "note_3"])
        logger.info(f"Collected {len(notes)} notes")
    finally:
        sync_collector.close()


# =============================================================================
# 示例 3: 采集笔记和评论
# =============================================================================

async def example_3_collect_notes_with_comments():
    """
    采集笔记及其评论。

    这个示例演示如何同时获取笔记和其所有评论。
    """
    logger.info("Example 3: Collecting notes with comments")

    batch_collector = BatchCollector()
    try:
        result = await batch_collector.collect_notes_with_comments(
            keywords=["护肤"],
        )

        logger.info(f"Collected {len(result)} notes with comments")
        for note_item in result[:2]:
            logger.info(
                f"  - {note_item.note.title} "
                f"({len(note_item.comments)} comments)"
            )

    finally:
        batch_collector.print_summary()


# =============================================================================
# 示例 4: 采集达人信息
# =============================================================================

async def example_4_collect_celebrities():
    """
    采集达人信息。

    包括粉丝数、互动率、内容风格等。
    """
    logger.info("Example 4: Collecting celebrity data")

    aggregator = CelebAggregator()
    try:
        celebs = await aggregator.collect_batch_async([
            "user_123",
            "user_456",
            "user_789",
        ])

        logger.info(f"Collected {len(celebs)} celebrities")
        for celeb in celebs:
            logger.info(
                f"  - {celeb.name} ({celeb.followers} followers, "
                f"{celeb.interaction_rate:.2f}% engagement)"
            )

    finally:
        await aggregator.close()


# =============================================================================
# 示例 5: 完整的端到端采集
# =============================================================================

async def example_5_complete_collection():
    """
    执行完整的采集流程。

    采集笔记 → 评论 → 达人信息，所有操作协调进行。
    """
    logger.info("Example 5: Complete collection pipeline")

    collector = BatchCollector()
    try:
        result = await collector.collect_all(
            keywords=["护肤", "眼膜"],
            celebrity_ids=["user_1", "user_2"],
        )

        logger.info("Collection completed!")
        logger.info(f"  - Notes: {result['summary']['total_notes']}")
        logger.info(
            f"  - Notes with comments: "
            f"{result['summary']['total_notes_with_comments']}"
        )
        logger.info(f"  - Celebrities: {result['summary']['total_celebrities']}")

        return result

    finally:
        collector.print_summary()


# =============================================================================
# 示例 6: 自定义采集配置
# =============================================================================

async def example_6_custom_config():
    """
    使用自定义配置进行采集。

    演示如何调整并发、超时、重试等参数。
    """
    logger.info("Example 6: Collecting with custom config")

    config = CollectionConfig(
        concurrent_requests=10,  # 增加并发
        request_timeout=60,  # 增加超时时间
        retry_attempts=5,  # 增加重试次数
        rate_limit_delay=0.5,  # 减少延迟
        max_notes_per_search=200,  # 每个搜索采集更多笔记
        max_comments_per_note=500,  # 每个笔记采集更多评论
    )

    aggregator = NoteAggregator(config)
    try:
        notes = await aggregator.collect_async(keywords=["护肤"])
        logger.info(f"Collected {len(notes)} notes with custom config")
    finally:
        await aggregator.close()


# =============================================================================
# 示例 7: 错误处理和重试
# =============================================================================

async def example_7_error_handling():
    """
    演示错误处理和重试机制。

    采集过程中可能失败，但采集器会自动重试。
    """
    logger.info("Example 7: Error handling and retry")

    config = CollectionConfig(
        retry_attempts=3,  # 最多重试 3 次
        rate_limit_delay=1.0,
    )

    aggregator = NoteAggregator(config)
    try:
        # 采集时如果出现错误，会自动重试
        # 单个项目失败不会中断整个采集过程
        notes = await aggregator.collect_batch_async(
            ["note_1", "note_2", "invalid_note"],
        )
        logger.info(
            f"Collected {len(notes)} notes "
            f"(some items may have failed)"
        )
    finally:
        await aggregator.close()


# =============================================================================
# 示例 8: 批量采集并保存结果
# =============================================================================

async def example_8_batch_collection_with_save():
    """
    批量采集并保存结果到文件。

    这演示了采集后如何处理数据（保存、处理等）。
    """
    logger.info("Example 8: Batch collection with saving")

    collector = BatchCollector()
    try:
        result = await collector.collect_notes_with_comments(
            keywords=["护肤"],
        )

        logger.info(f"Collected {len(result)} notes")

        # 这里可以将结果保存到文件
        import json
        from pathlib import Path

        output_file = Path("data/collection/sample_notes.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # 转换为字典格式（便于 JSON 序列化）
        data = {
            "notes": [
                {
                    "note_id": item.note.note_id,
                    "title": item.note.title,
                    "likes": item.note.likes,
                    "comments_count": len(item.comments),
                }
                for item in result
            ]
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Results saved to {output_file}")

    finally:
        collector.print_summary()


# =============================================================================
# 主函数
# =============================================================================

async def main():
    """运行所有示例"""
    print("\n" + "=" * 80)
    print("XHS Agent 采集管道示例")
    print("=" * 80 + "\n")

    # 注意：以下示例需要正确配置 xiaohongshu-cli 和 Cookie
    # 如果未配置，示例会因为 API 错误而失败

    examples = [
        ("基础笔记采集（异步）", example_1_collect_notes_async),
        ("笔记采集（同步）", example_2_collect_notes_sync),
        ("采集笔记和评论", example_3_collect_notes_with_comments),
        ("采集达人信息", example_4_collect_celebrities),
        ("完整的端到端采集", example_5_complete_collection),
        ("自定义采集配置", example_6_custom_config),
        ("错误处理和重试", example_7_error_handling),
        ("批量采集并保存", example_8_batch_collection_with_save),
    ]

    for idx, (title, example_func) in enumerate(examples, 1):
        print(f"\n{idx}. {title}")
        print("-" * 80)

        try:
            if asyncio.iscoroutinefunction(example_func):
                await example_func()
            else:
                example_func()
            print("✓ 示例完成")
        except Exception as e:
            print(f"✗ 示例失败: {e}")

        print()


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())
