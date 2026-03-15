"""
评论采集模块。

负责采集小红书笔记的评论数据：
- 获取笔记的评论列表
- 采集评论的基本信息和互动数据
- 采集评论的回复
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, List, Optional

from xhs_agent.integrations import XhsPort, create_xhs_port
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

    def __init__(
        self,
        config: Optional[CollectionConfig] = None,
        xhs_port: Optional[XhsPort] = None,
        xhs_backend: Optional[str] = None,
    ):
        super().__init__(config)
        self._xhs = xhs_port
        self._xhs_backend = xhs_backend

    @property
    def _xhs_client(self):
        """向后兼容旧测试与外部注入方式。"""
        return self._xhs

    @_xhs_client.setter
    def _xhs_client(self, value):
        self._xhs = value

    async def init_xhs_client(self):
        """初始化小红书 API 客户端"""
        if self._xhs is not None:
            return

        try:
            logger.info("Initializing XHS API client for comment aggregator...")
            self._xhs = create_xhs_port(self._xhs_backend)
            logger.info("XHS API client initialized successfully")
        except ImportError:
            logger.error("xiaohongshu-cli not found")
            raise
        except Exception as e:
            logger.error("Failed to initialize XHS API client: %s", str(e))
            raise

    async def _ensure_xhs(self) -> XhsPort:
        if self._xhs is None:
            await self.init_xhs_client()
        if self._xhs is None:
            raise RuntimeError("XHS API client is not initialized")
        return self._xhs

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
        await self._ensure_xhs()

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
        raise NotImplementedError(
            "CommentAggregator.collect_single(comment_id) is not supported by current xhs_cli APIs. "
            "Use collect_async(note_id=...) to fetch comments by note."
        )

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
            client = await self._ensure_xhs()
            max_pages = max(1, (limit + 19) // 20)
            result = client.get_all_comments(note_id, max_pages=max_pages)
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
        raise NotImplementedError(
            "Single-comment detail is not exposed by current xhs_cli APIs."
        )

    @staticmethod
    def _safe_int(value: Any) -> int:
        try:
            return int(str(value).strip())
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _parse_datetime(value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, (int, float)):
            ts = float(value)
            if ts > 1_000_000_000_000:
                ts /= 1000.0
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        if isinstance(value, str):
            raw = value.strip()
            if raw.isdigit():
                return CommentAggregator._parse_datetime(int(raw))
            try:
                return datetime.fromisoformat(raw.replace("Z", "+00:00"))
            except ValueError:
                return datetime.now(timezone.utc)
        return datetime.now(timezone.utc)

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
        user_info = api_response.get("user_info", {})
        if not isinstance(user_info, dict):
            user_info = api_response.get("user", {})
        if not isinstance(user_info, dict):
            user_info = {}

        target_comment = api_response.get("target_comment", {})
        if not isinstance(target_comment, dict):
            target_comment = {}

        return Comment(
            comment_id=str(
                api_response.get("comment_id")
                or api_response.get("id")
                or ""
            ).strip(),
            note_id=note_id,
            author_id=str(
                api_response.get("author_id")
                or user_info.get("user_id")
                or user_info.get("userid")
                or ""
            ).strip(),
            author_name=str(
                api_response.get("author_name")
                or user_info.get("nickname")
                or user_info.get("name")
                or ""
            ).strip(),
            content=str(api_response.get("content") or api_response.get("text") or "").strip(),
            likes=self._safe_int(
                api_response.get("liked_count")
                or api_response.get("likes")
            ),
            replies_count=self._safe_int(
                api_response.get("sub_comment_count")
                or api_response.get("replies_count")
            ),
            is_reply=bool(
                api_response.get("is_reply")
                or api_response.get("target_comment")
                or api_response.get("parent_comment_id")
            ),
            parent_comment_id=str(
                api_response.get("parent_comment_id")
                or target_comment.get("id")
                or ""
            ).strip() or None,
            published_at=self._parse_datetime(
                api_response.get("published_at")
                or api_response.get("create_time")
                or api_response.get("time")
            ),
        )

    async def close(self) -> None:
        """关闭采集器"""
        if self._xhs:
            try:
                self._xhs.close()
                logger.info("XHS API client closed")
            except Exception as e:
                logger.error("Error closing XHS API client: %s", str(e))


# 便利函数
async def collect_note_with_comments(
    note: NoteData,
    config: Optional[CollectionConfig] = None,
    xhs_backend: Optional[str] = None,
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
    aggregator = CommentAggregator(config, xhs_backend=xhs_backend)
    try:
        return await aggregator.collect_note_with_comments(note)
    finally:
        await aggregator.close()
