"""
笔记表现分析模块。

分析笔记的互动数据，计算表现指标：
- 互动率
- 热度评分
- 传播力评分
- 转化潜力
"""

from __future__ import annotations

import logging
from typing import Optional
from datetime import datetime, timedelta

from xhs_agent.types import NoteWithComments, PerformanceMetrics
from .base import PerformanceAnalyzer, AnalysisLogger

logger = logging.getLogger(__name__)


class NotePerformanceAnalyzer(PerformanceAnalyzer):
    """
    笔记表现分析器的具体实现。

    计算笔记的各项表现指标，用于判断内容的有效性。

    使用方式:
        analyzer = NotePerformanceAnalyzer()
        metrics = analyzer.analyze(note_with_comments)
        print(f"Heat Score: {metrics.heat_score}")
    """

    def __init__(
        self,
        heat_weights: Optional[dict] = None,
        virality_weights: Optional[dict] = None,
        conversion_weights: Optional[dict] = None,
    ):
        """
        初始化笔记表现分析器。

        Args:
            heat_weights: 热度评分权重
                {
                    "likes": 0.4,
                    "comments": 0.35,
                    "shares": 0.25,
                }
            virality_weights: 传播力评分权重
                {
                    "shares": 0.5,
                    "reposts": 0.3,
                    "comments": 0.2,
                }
            conversion_weights: 转化潜力权重
        """
        super().__init__(heat_weights)

        self.virality_weights = virality_weights or {
            "shares": 0.5,
            "reposts": 0.3,
            "comments": 0.2,
        }

        self.conversion_weights = conversion_weights or {
            "comments_with_purchase_signals": 0.4,
            "comments_with_positive_sentiment": 0.3,
            "engagement_rate": 0.3,
        }

    def analyze(self, data: NoteWithComments) -> PerformanceMetrics:
        """
        分析单个笔记的表现。

        Args:
            data: 包含评论的笔记

        Returns:
            笔记表现指标
        """
        try:
            note = data.note

            # 1. 计算基础互动数据
            engagement_count = (
                note.likes + note.comments_count + note.collects
            )
            engagement_rate = self._estimate_engagement_rate(
                engagement_count,
                note.followers_estimate if hasattr(note, "followers_estimate") else 10000,
            )

            # 2. 计算热度评分
            heat_score = self._calculate_heat_score(
                likes=note.likes,
                comments=note.comments_count,
                shares=note.shares,
            )

            # 3. 计算传播力评分
            virality_score = self._calculate_virality_score(
                shares=note.shares,
                reposts=note.reposts,
                comments=note.comments_count,
            )

            # 4. 计算转化潜力
            conversion_potential = self._calculate_conversion_potential(
                engagement_rate=engagement_rate,
                comments=data.comments,
            )

            # 5. 计算发布至今天数
            days_since = self._calculate_days_since_publish(note.published_at)

            # 6. 估算峰值互动时间
            peak_hour = self._estimate_peak_hour(data.comments)

            return PerformanceMetrics(
                note_id=note.note_id,
                engagement_rate=engagement_rate,
                engagement_count=engagement_count,
                heat_score=heat_score,
                virality_score=virality_score,
                conversion_potential=conversion_potential,
                peak_engagement_hour=peak_hour,
                days_since_publish=days_since,
            )

        except Exception as e:
            logger.error("Failed to analyze note %s: %s", data.note.note_id, str(e))
            raise

    def batch_analyze(
        self,
        data_list: list[NoteWithComments],
    ) -> list[PerformanceMetrics]:
        """
        批量分析笔记表现。

        Args:
            data_list: 笔记列表

        Returns:
            表现指标列表
        """
        logger.info("Analyzing performance for %d notes", len(data_list))

        results = []
        logger_obj = AnalysisLogger()

        for data in data_list:
            try:
                metrics = self.analyze(data)
                results.append(metrics)
                logger_obj.record_success(data.note.note_id)
            except Exception as e:
                logger.error(
                    "Failed to analyze note %s: %s",
                    data.note.note_id,
                    str(e),
                )
                logger_obj.record_failure(data.note.note_id, str(e))

        logger_obj.print_summary()
        return results

    def _estimate_engagement_rate(
        self,
        engagement_count: int,
        estimated_impressions: int,
    ) -> float:
        """
        估算互动率。

        小红书的真实曝光数难以获取，这里用一个启发式估计。

        Args:
            engagement_count: 互动总数（赞+评+收）
            estimated_impressions: 估算曝光数

        Returns:
            互动率（0-1）
        """
        if estimated_impressions <= 0:
            return 0.0

        engagement_rate = engagement_count / estimated_impressions
        return min(engagement_rate, 1.0)  # 上限 100%

    def _calculate_heat_score(
        self,
        likes: int,
        comments: int,
        shares: int,
    ) -> float:
        """
        计算热度评分（0-100）。

        热度反映笔记的当前人气程度。

        Args:
            likes: 赞数
            comments: 评论数
            shares: 分享数

        Returns:
            热度评分（0-100）
        """
        # 归一化（使用对数刻度，处理数值差异）
        normalized_likes = (
            10 * (1 + likes / max(likes, 1)) ** 0.5
        )  # 0-10
        normalized_comments = (
            10 * (1 + comments / max(comments, 1)) ** 0.5
        )  # 0-10
        normalized_shares = (
            10 * (1 + shares / max(shares, 1)) ** 0.5
        )  # 0-10

        # 加权求和
        heat_score = (
            normalized_likes * self.heat_weights.get("likes", 0.4)
            + normalized_comments * self.heat_weights.get("comments", 0.35)
            + normalized_shares * self.heat_weights.get("shares", 0.25)
        )

        return min(heat_score, 100.0)  # 上限 100

    def _calculate_virality_score(
        self,
        shares: int,
        reposts: int,
        comments: int,
    ) -> float:
        """
        计算传播力评分（0-100）。

        传播力反映笔记被分享、转发的倾向。

        Args:
            shares: 分享数
            reposts: 转发数
            comments: 评论数

        Returns:
            传播力评分（0-100）
        """
        # 归一化
        normalized_shares = 20 * (shares / max(shares, 1)) ** 0.5
        normalized_reposts = 20 * (reposts / max(reposts, 1)) ** 0.5
        normalized_comments = 10 * (comments / max(comments, 1)) ** 0.5

        # 加权求和
        virality_score = (
            normalized_shares * self.virality_weights.get("shares", 0.5)
            + normalized_reposts * self.virality_weights.get("reposts", 0.3)
            + normalized_comments * self.virality_weights.get("comments", 0.2)
        )

        return min(virality_score, 100.0)

    def _calculate_conversion_potential(
        self,
        engagement_rate: float,
        comments: list,
    ) -> float:
        """
        计算转化潜力（0-100）。

        转化潜力反映笔记可能产生购买的可能性。

        这个指标需要情感分析的支持，这里提供简化版本。

        Args:
            engagement_rate: 互动率
            comments: 评论列表

        Returns:
            转化潜力评分（0-100）
        """
        # 评论数越多，潜力越大
        comment_score = min(len(comments) / 100 * 100, 50)  # 最多 50 分

        # 互动率越高，潜力越大
        engagement_score = engagement_rate * 100 * 0.5  # 最多 50 分

        conversion_potential = comment_score + engagement_score

        return min(conversion_potential, 100.0)

    def _calculate_days_since_publish(self, published_at: str) -> int:
        """
        计算笔记发布至今的天数。

        Args:
            published_at: 发布时间（ISO 格式字符串）

        Returns:
            天数
        """
        try:
            if isinstance(published_at, str):
                pub_time = datetime.fromisoformat(
                    published_at.replace("Z", "+00:00")
                )
            else:
                pub_time = published_at

            days = (datetime.now() - pub_time).days
            return max(days, 0)

        except (ValueError, AttributeError, TypeError):
            logger.warning("Failed to parse published_at: %s", published_at)
            return 0

    def _estimate_peak_hour(self, comments: list) -> int | None:
        """
        估算笔记互动的峰值时间（小时）。

        基于评论的发布时间分布。

        Args:
            comments: 评论列表

        Returns:
            峰值小时（0-23）或 None
        """
        if not comments:
            return None

        try:
            # 统计评论按小时的分布
            hour_counts = {}

            for comment in comments:
                try:
                    if isinstance(comment.published_at, str):
                        cmt_time = datetime.fromisoformat(
                            comment.published_at.replace("Z", "+00:00")
                        )
                    else:
                        cmt_time = comment.published_at

                    hour = cmt_time.hour
                    hour_counts[hour] = hour_counts.get(hour, 0) + 1

                except (ValueError, AttributeError, TypeError):
                    continue

            if not hour_counts:
                return None

            # 找到最多评论的小时
            peak_hour = max(hour_counts, key=hour_counts.get)
            return peak_hour

        except Exception as e:
            logger.warning("Failed to estimate peak hour: %s", str(e))
            return None


# 便利函数
def analyze_note_performance(
    note_with_comments: NoteWithComments,
) -> PerformanceMetrics:
    """
    快速分析单个笔记的表现。

    Args:
        note_with_comments: 包含评论的笔记

    Returns:
        表现指标

    示例:
        metrics = analyze_note_performance(note_with_comments)
        print(f"热度: {metrics.heat_score}")
    """
    analyzer = NotePerformanceAnalyzer()
    return analyzer.analyze(note_with_comments)


def analyze_notes_performance(
    notes_with_comments: list[NoteWithComments],
) -> list[PerformanceMetrics]:
    """
    快速批量分析笔记表现。

    Args:
        notes_with_comments: 包含评论的笔记列表

    Returns:
        表现指标列表
    """
    analyzer = NotePerformanceAnalyzer()
    return analyzer.batch_analyze(notes_with_comments)
