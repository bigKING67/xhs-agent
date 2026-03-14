"""
评论采集模块。

负责采集小红书笔记的评论数据：
- 获取笔记的评论列表
- 采集评论的基本信息和互动数据
- 采集评论的回复
"""

from __future__ import annotations

import logging
from typing import Optional, List

from xhs_agent.types import Comment, CollectionConfig, NoteWithComments, NoteData
from .base import BaseCollector

logger = logging.getLogger(__name__)


class CommentAggregator(BaseCollector[Comment]):
    """
    评论采集器。

    负责采集评论数据：
    - 获取笔记的评论列表
    - 获取评论的回复
    - 采集评论的互动信息

    使用方式:
        aggregator = CommentAggregator(config)
        async with aggregator:
            comments = await aggregator.collect_async(note_id='note_123')
    """

    def __init__(self, config: Optional[CollectionConfig] = None):
        super().__init__(config)
        self._xhs_client = None

    async def init_xhs_client(self):
        """初始化小红书 API 客户端"""
        try:
            from xiaohongshu_cli.cookies import get_cookies
            from xiaohongshu_cli.client import XhsClient

            logger.info("Initializing XHS API client for comment aggregator...")
            cookies = get_cookies()
            self._xhs_client = XhsClient(cookies)
            logger.info("XHS API client initialized successfully")
        except ImportError:
            logger.error("xiaohongshu-cli not found")
            raise
        except Exception as e:
            logger.error("Failed to initialize XHS API client: %s", str(e))
            raise

    async def collect_async(
        self,
        note_id: str,
        max_comments: Optional[int] = None,
    ) -> List[Comment]:
        """
        采集笔记的所有评论。

        Args:
            note_id: 笔记 ID
            max_comments: 最多采集多少条评论

        Returns:
            评论列表
        """
        if not self._xhs_client:
            await self.init_xhs_client()

        if max_comments is None:
            max_comments = self.config.max_comments_per_note

        logger.info(
            "Fetching comments for note %s (max: %d)",
            note_id,
            max_comments,
        )

        try:
            # 获取评论列表
            comments = await self._get_note_comments(
                note_id=note_id,
                limit=max_comments,
            )

            logger.info(
                "Fetched %d comments for note %s",
                len(comments),
                note_id,
            )

            # 转换为 Comment 对象
            comment_objects = [
                self._convert_to_comment(cmt, note_id)
                for cmt in comments
            ]

            return comment_objects

        except Exception as e:
            logger.error(
                "Failed to fetch comments for note %s: %s",
                note_id,
                str(e),
            )
            raise

    async def collect_single(
        self,
        comment_id: str,
        *args,
        **kwargs
    ) -> Optional[Comment]:
        """
        采集单个评论的详情。

        Args:
            comment_id: 评论 ID

        Returns:
            评论数据对象
        """
        if not self._xhs_client:
            await self.init_xhs_client()

        try:
            logger.debug("Fetching comment: %s", comment_id)

            # 获取评论详情
            comment_data = await self._get_comment_detail(comment_id)
            if comment_data:
                logger.debug("Successfully fetched comment: %s", comment_id)
                note_id = comment_data.get("note_id", "")
                return self._convert_to_comment(comment_data, note_id)
            else:
                logger.warning("Comment not found: %s", comment_id)
                return None

        except Exception as e:
            logger.error("Failed to fetch comment %s: %s", comment_id, str(e))
            raise

    async def collect_note_with_comments(
        self,
        note: NoteData,
        max_comments: Optional[int] = None,
    ) -> NoteWithComments:
        """
        采集笔记及其所有评论。

        Args:
            note: 笔记数据对象
            max_comments: 最多采集多少条评论

        Returns:
            包含评论的完整笔记数据
        """
        comments = await self.collect_async(
            note_id=note.note_id,
            max_comments=max_comments,
        )

        return NoteWithComments(
            note=note,
            comments=comments,
            author_data=None,  # 可以稍后填充
        )

    async def _get_note_comments(
        self,
        note_id: str,
        limit: int = 200,
    ) -> List[dict]:
        """
        获取笔记的评论列表。

        Args:
            note_id: 笔记 ID
            limit: 最多获取多少条评论

        Returns:
            评论列表
        """
        try:
            result = self._xhs_client.get_note_comments(note_id, limit=limit)
            return result.get("comments", [])
        except Exception as e:
            logger.error("Get note comments API error: %s", str(e))
            raise

    async def _get_comment_detail(self, comment_id: str) -> Optional[dict]:
        """
        获取单个评论的详情。

        Args:
            comment_id: 评论 ID

        Returns:
            评论详情字典
        """
        try:
            result = self._xhs_client.get_comment_detail(comment_id)
            return result
        except Exception as e:
            logger.error("Get comment detail API error: %s", str(e))
            raise

    def _convert_to_comment(
        self,
        api_response: dict,
        note_id: str,
    ) -> Comment:
        """
        将 API 响应转换为 Comment 对象。

        Args:
            api_response: 小红书 API 返回的评论数据
            note_id: 所属笔记 ID

        Returns:
            标准化的 Comment 对象
        """
        return Comment(
            comment_id=api_response.get("comment_id", ""),
            note_id=note_id,
            author_id=api_response.get("author_id", ""),
            author_name=api_response.get("author_name", ""),
            content=api_response.get("content", ""),
            likes=api_response.get("likes", 0),
            replies_count=api_response.get("replies_count", 0),
            is_reply=api_response.get("is_reply", False),
            parent_comment_id=api_response.get("parent_comment_id"),
            published_at=api_response.get("published_at", ""),
        )

    async def close(self) -> None:
        """关闭采集器"""
        if self._xhs_client:
            try:
                self._xhs_client.close()
                logger.info("XHS API client closed")
            except Exception as e:
                logger.error("Error closing XHS API client: %s", str(e))


# 便利函数
async def collect_note_with_comments(
    note: NoteData,
    config: Optional[CollectionConfig] = None,
) -> NoteWithComments:
    """
    快速采集笔记及其评论。

    Args:
        note: 笔记对象
        config: 采集配置

    Returns:
        包含评论的完整笔记

    示例:
        note_with_cmts = await collect_note_with_comments(note)
    """
    aggregator = CommentAggregator(config)
    try:
        return await aggregator.collect_note_with_comments(note)
    finally:
        await aggregator.close()
