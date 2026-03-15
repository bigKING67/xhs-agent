"""
分析管道 (Analysis Pipeline)。

负责分析采集到的数据：
- 笔记表现分析（互动率、热度、传播力）
- 评论情感分析（正负面、话题提取）
- 趋势分析（热词、风格转变）
- 信号提取（用于策略生成）
"""

from .base import BaseAnalyzer, PerformanceAnalyzer, SentimentAnalyzer, AnalysisLogger
from .performance import NotePerformanceAnalyzer, analyze_note_performance, analyze_notes_performance
from .sentiment import CommentSentimentAnalyzer, analyze_comment_sentiment, analyze_comments_sentiment
from .trends import TrendAnalyzer, analyze_market_trends
from .orchestrator import AnalysisOrchestrator, generate_strategy_signals

__all__ = [
    # Base classes
    "BaseAnalyzer",
    "PerformanceAnalyzer",
    "SentimentAnalyzer",
    "AnalysisLogger",

    # Performance analyzer
    "NotePerformanceAnalyzer",
    "analyze_note_performance",
    "analyze_notes_performance",

    # Sentiment analyzer
    "CommentSentimentAnalyzer",
    "analyze_comment_sentiment",
    "analyze_comments_sentiment",

    # Trend analyzer
    "TrendAnalyzer",
    "analyze_market_trends",

    # Orchestrator
    "AnalysisOrchestrator",
    "generate_strategy_signals",
]
