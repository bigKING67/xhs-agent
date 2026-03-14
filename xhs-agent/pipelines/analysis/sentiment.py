"""
评论情感分析模块。

分析笔记的评论数据，提取：
- 情感分布（正面、中立、负面比例）
- 用户核心痛点
- 最有效的情绪触发
- 购买驱动力
"""

from __future__ import annotations

import logging
import re
from typing import Optional
from collections import Counter

from xhs_agent.types import NoteWithComments, SentimentReport, Comment
from .base import SentimentAnalyzer, AnalysisLogger

logger = logging.getLogger(__name__)


class CommentSentimentAnalyzer(SentimentAnalyzer):
    """
    评论情感分析器的具体实现。

    使用关键词匹配和启发式规则分析评论情感。

    注意：这是一个简化版本，实际应该用 NLP 模型（如 BERT）进行更精准的情感分类。

    使用方式:
        analyzer = CommentSentimentAnalyzer()
        sentiment = analyzer.analyze(note_with_comments)
        print(f"正面比例: {sentiment.positive_ratio}")
    """

    def __init__(
        self,
        positive_keywords: Optional[list[str]] = None,
        negative_keywords: Optional[list[str]] = None,
        purchase_signal_keywords: Optional[list[str]] = None,
    ):
        """
        初始化情感分析器。

        Args:
            positive_keywords: 正面词汇列表
            negative_keywords: 负面词汇列表
            purchase_signal_keywords: 购买信号词汇列表
        """
        super().__init__(
            positive_keywords or [
                "好用", "效果好", "真的有效", "推荐", "已回购",
                "爱上", "必买", "安利", "太棒了", "改善",
                "满意", "值得", "正品", "品质好", "信任",
            ],
            negative_keywords or [
                "不好用", "没效果", "浪费钱", "坑", "差评",
                "不推荐", "退货", "假货", "骗人", "垃圾",
                "烂", "太差", "失望", "后悔", "不值得",
            ],
            purchase_signal_keywords or [
                "回购", "已下单", "已拍", "囤货", "收藏",
                "分享给", "安利", "转发", "预购", "等快递",
                "已到货", "必须买", "必回购", "强烈推荐",
            ],
        )

    def analyze(self, data: NoteWithComments) -> SentimentReport:
        """
        分析笔记评论的情感。

        Args:
            data: 包含评论的笔记

        Returns:
            情感分析报告
        """
        try:
            comments = data.comments
            if not comments:
                return self._create_empty_sentiment_report(data.note.note_id)

            # 1. 分类评论情感
            sentiments = []
            for comment in comments:
                sentiment = self._classify_comment_sentiment(comment.content)
                sentiments.append(sentiment)

            # 2. 计算情感分布
            positive_count = sentiments.count("positive")
            negative_count = sentiments.count("negative")
            neutral_count = sentiments.count("neutral")
            total = len(comments)

            positive_ratio = positive_count / total if total > 0 else 0
            negative_ratio = negative_count / total if total > 0 else 0
            neutral_ratio = neutral_count / total if total > 0 else 0

            # 3. 提取痛点和话题
            pain_points = self._extract_pain_points(comments)
            purchase_drivers = self._extract_purchase_drivers(comments)

            # 4. 推断用户情绪
            user_emotions = self._infer_emotions(
                comments,
                positive_ratio,
                pain_points,
            )

            # 5. 提取关键话题
            key_topics = self._extract_topics(comments)

            # 6. 计算总体情感评分
            overall_score = (
                positive_ratio * 1.0 +
                neutral_ratio * 0.5 +
                negative_ratio * 0.0
            ) / (positive_ratio + neutral_ratio + negative_ratio or 1)

            return SentimentReport(
                note_id=data.note.note_id,
                total_comments=total,
                positive_ratio=positive_ratio,
                neutral_ratio=neutral_ratio,
                negative_ratio=negative_ratio,
                top_pain_points=pain_points[:5],  # 前 5 个
                top_emotions=user_emotions[:3],  # 前 3 个
                purchase_drivers=purchase_drivers[:5],  # 前 5 个
                key_topics=key_topics,
                overall_sentiment_score=overall_score,
            )

        except Exception as e:
            logger.error("Failed to analyze sentiment for note %s: %s",
                         data.note.note_id, str(e))
            raise

    def batch_analyze(
        self,
        data_list: list[NoteWithComments],
    ) -> list[SentimentReport]:
        """
        批量分析笔记评论情感。

        Args:
            data_list: 笔记列表

        Returns:
            情感分析报告列表
        """
        logger.info("Analyzing sentiment for %d notes", len(data_list))

        results = []
        logger_obj = AnalysisLogger()

        for data in data_list:
            try:
                report = self.analyze(data)
                results.append(report)
                logger_obj.record_success(data.note.note_id)
            except Exception as e:
                logger.error("Failed to analyze sentiment for note %s: %s",
                             data.note.note_id, str(e))
                logger_obj.record_failure(data.note.note_id, str(e))

        logger_obj.print_summary()
        return results

    def _classify_comment_sentiment(self, content: str) -> str:
        """
        分类单个评论的情感。

        使用关键词匹配的启发式方法。

        Args:
            content: 评论内容

        Returns:
            情感类型 ("positive", "negative", "neutral")
        """
        if not content:
            return "neutral"

        content_lower = content.lower()

        # 计算正面和负面关键词的出现次数
        positive_count = sum(
            1 for keyword in self.positive_keywords
            if keyword in content_lower
        )
        negative_count = sum(
            1 for keyword in self.negative_keywords
            if keyword in content_lower
        )

        # 根据出现次数判断情感
        if positive_count > negative_count and positive_count > 0:
            return "positive"
        elif negative_count > positive_count and negative_count > 0:
            return "negative"
        else:
            return "neutral"

    def _extract_pain_points(self, comments: list[Comment]) -> list[str]:
        """
        从评论中提取用户的核心痛点。

        使用关键词和名词短语提取。

        Args:
            comments: 评论列表

        Returns:
            痛点列表（按频率排序）
        """
        pain_point_keywords = [
            "黑眼圈", "细纹", "法令纹", "眼袋", "浮肿",
            "干纹", "暗沉", "毛孔", "油腻", "长痘",
            "敏感", "泛红", "痘印", "色斑", "皱纹",
            "衰老", "松弛", "暗沉", "缺水", "脱皮",
        ]

        pain_points = {}

        for comment in comments:
            content_lower = comment.content.lower()
            for keyword in pain_point_keywords:
                if keyword in content_lower:
                    pain_points[keyword] = pain_points.get(keyword, 0) + 1

        # 按频率排序
        sorted_points = sorted(
            pain_points.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        return [point for point, _ in sorted_points]

    def _extract_purchase_drivers(self, comments: list[Comment]) -> list[str]:
        """
        从评论中提取购买驱动力因素。

        按照用户的购买原因排序。

        Args:
            comments: 评论列表

        Returns:
            购买驱动力列表（按强度排序）
        """
        drivers = {
            "真实有效": 0,  # "确实有效"、"真的管用"
            "快速见效": 0,  # "一周"、"几天"
            "性价比高": 0,  # "便宜"、"划算"
            "好用易用": 0,  # "方便"、"简单"
            "安全可靠": 0,  # "安心"、"放心"、"正品"
        }

        for comment in comments:
            content = comment.content

            # "真实有效"
            if any(w in content for w in ["确实", "真的", "真的有效", "确实管用"]):
                drivers["真实有效"] += 1

            # "快速见效"
            if any(w in content for w in ["一周", "几天", "立竿见影", "很快"]):
                drivers["快速见效"] += 1

            # "性价比高"
            if any(w in content for w in ["划算", "便宜", "值得", "实惠"]):
                drivers["性价比高"] += 1

            # "好用易用"
            if any(w in content for w in ["方便", "简单", "好用", "容易"]):
                drivers["好用易用"] += 1

            # "安全可靠"
            if any(w in content for w in ["安心", "放心", "正品", "信任", "放心买"]):
                drivers["安全可靠"] += 1

        # 按强度排序
        sorted_drivers = sorted(
            drivers.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        return [driver for driver, _ in sorted_drivers if driver]

    def _infer_emotions(
        self,
        comments: list[Comment],
        positive_ratio: float,
        pain_points: list[str],
    ) -> list[str]:
        """
        推断用户的关键情绪。

        基于评论内容、情感分布和痛点。

        Args:
            comments: 评论列表
            positive_ratio: 正面比例
            pain_points: 用户痛点

        Returns:
            情绪类型列表（按强度排序）
        """
        emotions = {
            "获得感": 0,  # "买对了"、"赚到"、"值得"
            "安心感": 0,  # "放心"、"安心"、"有保障"
            "自信感": 0,  # "自信"、"变美"、"绽放"
            "共鸣感": 0,  # "原来不是我一个人"、"终于"
            "掌控感": 0,  # "我可以"、"自己可以解决"
        }

        for comment in comments:
            content = comment.content

            # 获得感
            if any(w in content for w in ["买对了", "赚到", "太值得", "还要回购"]):
                emotions["获得感"] += 3
            elif any(w in content for w in ["值得", "推荐", "满意"]):
                emotions["获得感"] += 1

            # 安心感
            if any(w in content for w in ["放心", "安心", "可以放心", "有保障"]):
                emotions["安心感"] += 3
            elif positive_ratio > 0.7:
                emotions["安心感"] += 1

            # 自信感
            if any(w in content for w in ["自信", "变美", "绽放", "魅力", "气质"]):
                emotions["自信感"] += 3
            elif any(w in content for w in ["改善", "提升", "变好"]):
                emotions["自信感"] += 1

            # 共鸣感
            if any(w in content for w in ["终于", "原来", "是不是", "我也是", "同感"]):
                emotions["共鸣感"] += 2
            if pain_points:  # 有共同痛点
                emotions["共鸣感"] += 1

            # 掌控感
            if any(w in content for w in ["可以", "能够", "自己", "学会", "解决"]):
                emotions["掌控感"] += 2

        # 按强度排序
        sorted_emotions = sorted(
            emotions.items(),
            key=lambda x: x[1],
            reverse=True,
        )

        return [
            emotion for emotion, score in sorted_emotions
            if score > 0
        ]

    def _extract_topics(self, comments: list[Comment]) -> dict[str, int]:
        """
        从评论中提取热点话题。

        使用频率统计。

        Args:
            comments: 评论列表

        Returns:
            话题及其提及次数
        """
        topics = {}

        # 关键话题词汇
        topic_keywords = [
            ("补水", ["补水", "保湿", "滋润"]),
            ("保护", ["保护", "防护", "屏障"]),
            ("淡化", ["淡化", "改善", "减少", "消退"]),
            ("提亮", ["提亮", "明亮", "光泽", "闪耀"]),
            ("修复", ["修复", "恢复", "再生"]),
            ("舒适", ["舒适", "不刺激", "温和"]),
            ("吸收", ["吸收", "好吸收", "不油腻"]),
            ("坚持", ["坚持", "长期", "持续"]),
        ]

        for topic_name, keywords in topic_keywords:
            count = 0
            for comment in comments:
                content_lower = comment.content.lower()
                if any(kw in content_lower for kw in keywords):
                    count += 1
            if count > 0:
                topics[topic_name] = count

        # 按频率排序
        return dict(
            sorted(topics.items(), key=lambda x: x[1], reverse=True)
        )

    def _create_empty_sentiment_report(self, note_id: str) -> SentimentReport:
        """创建空评论的默认情感报告"""
        return SentimentReport(
            note_id=note_id,
            total_comments=0,
            positive_ratio=0.0,
            neutral_ratio=0.0,
            negative_ratio=0.0,
            top_pain_points=[],
            top_emotions=[],
            purchase_drivers=[],
            key_topics={},
            overall_sentiment_score=0.5,
        )


# 便利函数
def analyze_comment_sentiment(
    note_with_comments: NoteWithComments,
) -> SentimentReport:
    """
    快速分析笔记的评论情感。

    Args:
        note_with_comments: 包含评论的笔记

    Returns:
        情感分析报告

    示例:
        report = analyze_comment_sentiment(note_with_comments)
        print(f"正面比例: {report.positive_ratio:.2%}")
    """
    analyzer = CommentSentimentAnalyzer()
    return analyzer.analyze(note_with_comments)


def analyze_comments_sentiment(
    notes_with_comments: list[NoteWithComments],
) -> list[SentimentReport]:
    """
    快速批量分析评论情感。

    Args:
        notes_with_comments: 包含评论的笔记列表

    Returns:
        情感分析报告列表
    """
    analyzer = CommentSentimentAnalyzer()
    return analyzer.batch_analyze(notes_with_comments)
