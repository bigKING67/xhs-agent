"""
批量采集协调模块。

负责协调多个采集器的批量采集任务：
- 搜索笔记 → 采集评论 → 采集达人信息
- 处理采集中的错误和重试
- 生成采集统计和报告
"""

from __future__ import annotations

import logging
import asyncio
from typing import List, Optional
from datetime import datetime

from xhs_agent.types import (
    NoteData,
    NoteWithComments,
    CelebData,
    CollectionConfig,
    CollectionResult,
)
from .base import CollectionLogger
from .notes import NoteAggregator
from .comments import CommentAggregator
from .celebrity import CelebAggregator

logger = logging.getLogger(__name__)


class BatchCollector:
    """
    批量采集协调器。

    协调多个采集器的联动操作，执行完整的数据采集流程：
    1. 搜索笔记
    2. 采集笔记评论
    3. 采集达人信息
    4. 统计和报告

    使用方式:
        batch_collector = BatchCollector()
        result = await batch_collector.collect_all(
            keywords=['护肤', '眼膜'],
            celebrity_ids=['user_1', 'user_2']
        )
    """

    def __init__(self, config: Optional[CollectionConfig] = None):
        self.config = config or CollectionConfig()
        self.logger = CollectionLogger()

        # 初始化各个采集器
        self.note_aggregator = NoteAggregator(config)
        self.comment_aggregator = CommentAggregator(config)
        self.celeb_aggregator = CelebAggregator(config)

    async def collect_all(
        self,
        keywords: List[str],
        celebrity_ids: Optional[List[str]] = None,
    ) -> dict:
        """
        执行完整的数据采集流程。

        Args:
            keywords: 搜索关键词列表
            celebrity_ids: 达人 ID 列表（可选）

        Returns:
            采集结果字典
        """
        self.logger.start()

        try:
            # Phase 1: 采集笔记
            logger.info("Phase 1: Collecting notes by keywords...")
            notes = await self.note_aggregator.collect_async(keywords=keywords)
            logger.info("Phase 1 completed: %d notes collected", len(notes))

            # Phase 2: 采集笔记评论
            logger.info("Phase 2: Collecting comments for notes...")
            notes_with_comments = await self._collect_comments_for_notes(notes)
            logger.info(
                "Phase 2 completed: %d notes with comments",
                len(notes_with_comments),
            )

            # Phase 3: 采集达人信息
            if celebrity_ids:
                logger.info("Phase 3: Collecting celebrity data...")
                celebs = await self.celeb_aggregator.collect_batch_async(
                    celebrity_ids
                )
                logger.info("Phase 3 completed: %d celebrities collected", len(celebs))
            else:
                celebs = []
                logger.info("Phase 3 skipped (no celebrity IDs provided)")

            # 汇总结果
            result = {
                "notes": notes,
                "notes_with_comments": notes_with_comments,
                "celebrities": celebs,
                "collection_time": datetime.now(),
                "summary": {
                    "total_notes": len(notes),
                    "total_notes_with_comments": len(notes_with_comments),
                    "total_celebrities": len(celebs),
                },
            }

            self.logger.finish()
            return result

        except Exception as e:
            logger.error("Collection failed: %s", str(e))
            self.logger.finish()
            raise

        finally:
            await self.close()

    async def _collect_comments_for_notes(
        self,
        notes: List[NoteData],
    ) -> List[NoteWithComments]:
        """
        为多个笔记采集评论（并发）。

        Args:
            notes: 笔记列表

        Returns:
            包含评论的笔记列表
        """
        tasks = [
            self.comment_aggregator.collect_note_with_comments(note)
            for note in notes
        ]

        # 并发采集评论，但限制并发数
        semaphore = asyncio.Semaphore(self.config.concurrent_requests)

        async def bounded_collect(note, task):
            async with semaphore:
                try:
                    result = await task
                    logger.debug(
                        "Collected %d comments for note %s",
                        len(result.comments),
                        note.note_id,
                    )
                    return result
                except Exception as e:
                    logger.warning(
                        "Failed to collect comments for note %s: %s",
                        note.note_id,
                        str(e),
                    )
                    # 返回只有笔记、没有评论的对象
                    return NoteWithComments(note=note, comments=[])

        results = await asyncio.gather(
            *[bounded_collect(note, task) for note, task in zip(notes, tasks)]
        )

        return results

    async def collect_notes_only(
        self,
        keywords: List[str],
    ) -> List[NoteData]:
        """
        仅采集笔记（不采集评论和达人）。

        Args:
            keywords: 搜索关键词列表

        Returns:
            笔记列表
        """
        self.logger.start()

        try:
            notes = await self.note_aggregator.collect_async(keywords=keywords)
            self.logger.finish()
            return notes
        except Exception as e:
            logger.error("Collection failed: %s", str(e))
            self.logger.finish()
            raise
        finally:
            await self.close()

    async def collect_notes_with_comments(
        self,
        keywords: List[str],
    ) -> List[NoteWithComments]:
        """
        采集笔记和评论（不采集达人）。

        Args:
            keywords: 搜索关键词列表

        Returns:
            包含评论的笔记列表
        """
        self.logger.start()

        try:
            # 采集笔记
            notes = await self.note_aggregator.collect_async(keywords=keywords)

            # 采集评论
            notes_with_comments = await self._collect_comments_for_notes(notes)

            self.logger.finish()
            return notes_with_comments

        except Exception as e:
            logger.error("Collection failed: %s", str(e))
            self.logger.finish()
            raise
        finally:
            await self.close()

    async def collect_celebrities(
        self,
        celebrity_ids: List[str],
    ) -> List[CelebData]:
        """
        仅采集达人数据。

        Args:
            celebrity_ids: 达人 ID 列表

        Returns:
            达人列表
        """
        self.logger.start()

        try:
            celebs = await self.celeb_aggregator.collect_batch_async(celebrity_ids)
            self.logger.finish()
            return celebs
        except Exception as e:
            logger.error("Collection failed: %s", str(e))
            self.logger.finish()
            raise
        finally:
            await self.close()

    async def close(self) -> None:
        """关闭所有采集器"""
        logger.info("Closing all collectors...")

        await asyncio.gather(
            self.note_aggregator.close(),
            self.comment_aggregator.close(),
            self.celeb_aggregator.close(),
            return_exceptions=True,
        )

        logger.info("All collectors closed")

    def print_summary(self):
        """打印采集总结"""
        self.logger.print_summary()


# 便利函数
async def collect_comprehensive(
    keywords: List[str],
    celebrity_ids: Optional[List[str]] = None,
    config: Optional[CollectionConfig] = None,
) -> dict:
    """
    执行完整的采集流程（一站式函数）。

    Args:
        keywords: 搜索关键词列表
        celebrity_ids: 达人 ID 列表（可选）
        config: 采集配置

    Returns:
        采集结果字典，包含：
        - notes: 笔记列表
        - notes_with_comments: 包含评论的笔记列表
        - celebrities: 达人列表
        - summary: 统计信息

    示例:
        result = await collect_comprehensive(
            keywords=['护肤', '眼膜'],
            celebrity_ids=['user_1', 'user_2']
        )
        print(f"Collected {result['summary']['total_notes']} notes")
    """
    collector = BatchCollector(config)
    try:
        return await collector.collect_all(
            keywords=keywords,
            celebrity_ids=celebrity_ids,
        )
    finally:
        collector.print_summary()
