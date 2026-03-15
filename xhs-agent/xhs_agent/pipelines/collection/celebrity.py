"""
达人采集模块。

负责采集小红书达人数据：
- 达人基本信息（粉丝、互动率等）
- 达人内容风格
- 达人历史笔记统计
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional, List

from xhs_agent.integrations import XhsPort, create_xhs_port
from xhs_agent.types import (
    CelebData,
    ContentStyle,
    PriceLevel,
    CollectionConfig,
)
from .base import BaseCollector

logger = logging.getLogger(__name__)


class CelebAggregator(BaseCollector[CelebData]):
    """
    达人采集器。

    负责采集达人数据：
    - 达人基本信息（粉丝数、昵称、简介等）
    - 达人互动统计（平均点赞、评论、分享）
    - 达人内容风格分析
    - 达人发布频率

    使用方式:
        aggregator = CelebAggregator(config)
        async with aggregator:
            celebs = await aggregator.collect_batch_async(['user_1', 'user_2'])
    """

    def __init__(
        self,
        config: Optional[CollectionConfig] = None,
        xhs_port: Optional[XhsPort] = None,
    ):
        super().__init__(config)
        self._xhs = xhs_port

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
            logger.info("Initializing XHS API client for celeb aggregator...")
            self._xhs = create_xhs_port()
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

    async def collect_single(
        self,
        celeb_id: str,
        *args,
        **kwargs
    ) -> Optional[CelebData]:
        """
        采集单个达人的信息。

        Args:
            celeb_id: 达人用户 ID

        Returns:
            达人数据对象
        """
        await self._ensure_xhs()

        try:
            logger.debug("Fetching celeb data for: %s", celeb_id)

            # 获取达人基本信息
            user_info = await self._get_user_info(celeb_id)
            if not user_info:
                logger.warning("User not found: %s", celeb_id)
                return None

            # 获取达人发布的笔记（用于统计）
            notes = await self._get_user_notes(celeb_id, limit=50)

            # 计算达人的统计信息
            celeb_stats = self._calculate_celeb_stats(user_info, notes)

            logger.debug("Successfully fetched celeb: %s", celeb_id)
            return celeb_stats

        except Exception as e:
            logger.error("Failed to fetch celeb %s: %s", celeb_id, str(e))
            raise

    async def _get_user_info(self, user_id: str) -> Optional[dict]:
        """
        获取用户基本信息。

        Args:
            user_id: 用户 ID

        Returns:
            用户信息字典
        """
        try:
            client = await self._ensure_xhs()
            # 调用 xiaohongshu-cli 的用户端点
            result = client.get_user_info(user_id)
            return result
        except Exception as e:
            logger.error("Get user info API error: %s", str(e))
            raise

    async def _get_user_notes(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[dict]:
        """
        获取用户发布的笔记列表。

        Args:
            user_id: 用户 ID
            limit: 最多获取多少条笔记

        Returns:
            笔记列表
        """
        try:
            client = await self._ensure_xhs()
            notes: list[dict] = []
            cursor = ""
            while len(notes) < limit:
                result = client.get_user_notes(user_id, cursor=cursor)
                page_notes = []
                if isinstance(result, dict):
                    page_notes = (
                        result.get("notes")
                        or result.get("note_list")
                        or result.get("items")
                        or []
                    )
                if not isinstance(page_notes, list) or not page_notes:
                    break
                notes.extend([item for item in page_notes if isinstance(item, dict)])
                if len(notes) >= limit:
                    break
                has_more = bool(result.get("has_more")) if isinstance(result, dict) else False
                next_cursor = str(result.get("cursor", "")).strip() if isinstance(result, dict) else ""
                if not has_more or not next_cursor:
                    break
                cursor = next_cursor
            return notes[:limit]
        except Exception as e:
            logger.error("Get user notes API error: %s", str(e))
            return []

    @staticmethod
    def _safe_int(value) -> int:
        try:
            return int(str(value).strip())
        except (TypeError, ValueError):
            return 0

    def _calculate_celeb_stats(
        self,
        user_info: dict,
        notes: List[dict],
    ) -> CelebData:
        """
        从原始数据计算达人统计信息。

        Args:
            user_info: 用户基本信息
            notes: 用户的笔记列表

        Returns:
            标准化的 CelebData 对象
        """
        # 提取基本信息
        user_info_detail = user_info.get("user_info", user_info)
        if not isinstance(user_info_detail, dict):
            user_info_detail = {}

        basic_info = user_info_detail.get("basic_info", {})
        if isinstance(basic_info, dict):
            user_info_detail = {**basic_info, **user_info_detail}

        followers = self._safe_int(
            user_info_detail.get("followers")
            or user_info_detail.get("fans")
            or user_info_detail.get("follower_count")
        )

        # 计算互动统计
        if notes:
            avg_likes = sum(
                self._safe_int(
                    (n.get("note_card", n) or {}).get("interact_info", {}).get("liked_count")
                    or (n.get("note_card", n) or {}).get("interact_info", {}).get("likes")
                )
                for n in notes
            ) / len(notes)
            avg_comments = sum(
                self._safe_int(
                    (n.get("note_card", n) or {}).get("interact_info", {}).get("comment_count")
                    or (n.get("note_card", n) or {}).get("interact_info", {}).get("comments")
                )
                for n in notes
            ) / len(notes)
            avg_shares = sum(
                self._safe_int(
                    (n.get("note_card", n) or {}).get("interact_info", {}).get("share_count")
                    or (n.get("note_card", n) or {}).get("interact_info", {}).get("shares")
                )
                for n in notes
            ) / len(notes)
        else:
            avg_likes = avg_comments = avg_shares = 0

        # 估算互动率
        # 小红书平均曝光数难以直接获取，这里用一个启发式估计
        estimated_engagement_rate = (
            (avg_likes + avg_comments + avg_shares)
            / max(followers, 1)
            * 100  # 百分比
        )

        # 分析内容风格（基于笔记数据，实际需要更复杂的分析）
        content_styles = self._infer_content_styles(notes)

        # 计算发布频率
        days_span = self._calculate_days_span(notes)
        avg_notes_per_week = (
            (len(notes) / days_span * 7)
            if days_span > 0
            else 0
        )

        # 估算价格档位（基于粉丝数的启发式）
        price_tier = self._estimate_price_tier(followers)

        return CelebData(
            celeb_id=str(
                user_info_detail.get("user_id")
                or user_info_detail.get("userid")
                or ""
            ).strip(),
            name=str(
                user_info_detail.get("nickname")
                or user_info_detail.get("name")
                or ""
            ).strip(),
            avatar_url=str(
                user_info_detail.get("avatar")
                or user_info_detail.get("image")
                or ""
            ).strip() or None,
            followers=followers,
            interaction_rate=estimated_engagement_rate,
            avg_likes_per_note=avg_likes,
            avg_comments_per_note=avg_comments,
            avg_shares_per_note=avg_shares,
            content_styles=content_styles,
            avg_notes_per_week=int(avg_notes_per_week),
            target_audience=user_info_detail.get("description", ""),
            price_tier=price_tier,
            bio=user_info_detail.get("signature", ""),
            data_collected_at=datetime.now(),
        )

    def _infer_content_styles(self, notes: List[dict]) -> List[ContentStyle]:
        """
        根据笔记内容推断达人的内容风格。

        这是一个简化版实现，实际应该用 NLP 分析。

        Args:
            notes: 笔记列表

        Returns:
            推断的内容风格列表
        """
        # 简单启发式：根据笔记类型和关键词
        styles = set()

        for note in notes:
            note_card = note.get("note_card", note) if isinstance(note, dict) else {}
            if not isinstance(note_card, dict):
                continue
            content = str(note_card.get("content") or note_card.get("desc") or "").lower()
            title = str(note_card.get("title") or note_card.get("display_title") or "").lower()

            # 检查是否含有教程特征
            if any(
                word in content or word in title
                for word in ["教程", "步骤", "怎么", "如何", "指南"]
            ):
                styles.add(ContentStyle.TUTORIAL)

            # 检查是否含有故事特征
            if any(
                word in content or word in title
                for word in ["我的", "分享", "经历", "故事", "日常"]
            ):
                styles.add(ContentStyle.STORY)

            # 检查是否含有文艺特征
            if any(
                word in content or word in title
                for word in ["文艺", "美学", "设计", "品味", "生活方式"]
            ):
                styles.add(ContentStyle.ARTISTIC)

        # 如果没有推断出特定风格，使用默认值
        if not styles:
            styles.add(ContentStyle.DAILY_LIFE)

        return list(styles)

    def _calculate_days_span(self, notes: List[dict]) -> int:
        """
        计算笔记发布的时间跨度（天数）。

        Args:
            notes: 笔记列表

        Returns:
            时间跨度（天数）
        """
        if not notes:
            return 0

        # 提取发布时间
        published_times = []
        for note in notes:
            note_card = note.get("note_card", note) if isinstance(note, dict) else {}
            if not isinstance(note_card, dict):
                continue
            published_at = (
                note_card.get("published_at")
                or note_card.get("publish_time")
                or note_card.get("time")
                or note_card.get("create_time")
            )
            if isinstance(published_at, (int, float)):
                ts = float(published_at)
                if ts > 1_000_000_000_000:
                    ts /= 1000.0
                published_times.append(datetime.fromtimestamp(ts, tz=timezone.utc))
                continue
            if isinstance(published_at, str):
                if published_at.strip().isdigit():
                    ts = float(published_at.strip())
                    if ts > 1_000_000_000_000:
                        ts /= 1000.0
                    published_times.append(datetime.fromtimestamp(ts, tz=timezone.utc))
                    continue
                try:
                    published_times.append(
                        datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                    )
                except (ValueError, AttributeError):
                    continue

        if not published_times:
            return 0

        # 计算最早和最晚的发布时间
        min_time = min(published_times)
        max_time = max(published_times)

        span = (max_time - min_time).days
        return max(span, 1)  # 至少 1 天

    def _estimate_price_tier(self, followers: int) -> PriceLevel:
        """
        根据粉丝数估算达人的价格档位。

        启发式规则（这些数字可以根据实际情况调整）：
        - < 10 万: 平价
        - 10-100 万: 中档
        - > 100 万: 高档

        Args:
            followers: 粉丝数

        Returns:
            价格档位
        """
        if followers < 100000:
            return PriceLevel.BUDGET
        elif followers < 1000000:
            return PriceLevel.MID_RANGE
        else:
            return PriceLevel.PREMIUM

    async def close(self) -> None:
        """关闭采集器"""
        if self._xhs:
            try:
                self._xhs.close()
                logger.info("XHS API client closed")
            except Exception as e:
                logger.error("Error closing XHS API client: %s", str(e))


# 便利函数
async def collect_celebs_by_ids(
    celeb_ids: List[str],
    config: Optional[CollectionConfig] = None,
) -> List[CelebData]:
    """
    快速采集多个达人的信息。

    Args:
        celeb_ids: 达人 ID 列表
        config: 采集配置

    Returns:
        采集到的达人列表

    示例:
        celebs = await collect_celebs_by_ids(['user_1', 'user_2'])
    """
    aggregator = CelebAggregator(config)
    try:
        return await aggregator.collect_batch_async(celeb_ids)
    finally:
        await aggregator.close()
