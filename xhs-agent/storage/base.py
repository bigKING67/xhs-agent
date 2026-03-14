"""
存储层的基类和接口定义。

支持多种存储后端（JSON、SQLite 等）。
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional, List, Dict
from pathlib import Path
from datetime import datetime

from xhs_agent.types import (
    NoteData,
    NoteWithComments,
    CelebData,
    PerformanceMetrics,
    SentimentReport,
    StrategySignals,
    XhsStrategyPlan,
)

logger = logging.getLogger(__name__)


class BaseStorage(ABC):
    """
    存储层基类。

    所有存储后端都继承此类，实现对数据的增删改查。
    """

    def __init__(self, backend_name: str):
        """初始化存储层"""
        self.backend_name = backend_name
        logger.info(f"Storage backend initialized: {backend_name}")

    # =========================================================================
    # 采集数据存储
    # =========================================================================

    @abstractmethod
    def save_note(self, note: NoteData) -> bool:
        """保存单个笔记"""
        raise NotImplementedError

    @abstractmethod
    def save_notes(self, notes: List[NoteData]) -> int:
        """批量保存笔记，返回保存数"""
        raise NotImplementedError

    @abstractmethod
    def save_note_with_comments(
        self,
        note_with_comments: NoteWithComments,
    ) -> bool:
        """保存笔记及其评论"""
        raise NotImplementedError

    @abstractmethod
    def save_celebrity(self, celebrity: CelebData) -> bool:
        """保存达人数据"""
        raise NotImplementedError

    @abstractmethod
    def save_celebrities(self, celebrities: List[CelebData]) -> int:
        """批量保存达人数据"""
        raise NotImplementedError

    @abstractmethod
    def get_note(self, note_id: str) -> Optional[NoteData]:
        """获取单个笔记"""
        raise NotImplementedError

    @abstractmethod
    def get_notes(self, keyword: str) -> List[NoteData]:
        """按关键词获取笔记"""
        raise NotImplementedError

    @abstractmethod
    def get_celebrity(self, celeb_id: str) -> Optional[CelebData]:
        """获取达人数据"""
        raise NotImplementedError

    # =========================================================================
    # 分析结果存储
    # =========================================================================

    @abstractmethod
    def save_performance_metrics(self, metrics: PerformanceMetrics) -> bool:
        """保存笔记表现指标"""
        raise NotImplementedError

    @abstractmethod
    def save_sentiment_report(self, report: SentimentReport) -> bool:
        """保存情感分析报告"""
        raise NotImplementedError

    @abstractmethod
    def save_strategy_signals(self, signals: StrategySignals) -> bool:
        """保存策略信号"""
        raise NotImplementedError

    @abstractmethod
    def get_performance_metrics(self, note_id: str) -> Optional[PerformanceMetrics]:
        """获取笔记表现指标"""
        raise NotImplementedError

    @abstractmethod
    def get_sentiment_report(self, note_id: str) -> Optional[SentimentReport]:
        """获取情感分析报告"""
        raise NotImplementedError

    @abstractmethod
    def get_strategy_signals(self, note_id: str) -> Optional[StrategySignals]:
        """获取策略信号"""
        raise NotImplementedError

    # =========================================================================
    # 策略结果存储
    # =========================================================================

    @abstractmethod
    def save_strategy_plan(self, plan: XhsStrategyPlan) -> bool:
        """保存生成的策略方案"""
        raise NotImplementedError

    @abstractmethod
    def get_strategy_plan(self, product_name: str, celebrity: str) -> Optional[XhsStrategyPlan]:
        """获取策略方案"""
        raise NotImplementedError

    @abstractmethod
    def list_strategy_plans(self, product_name: str) -> List[XhsStrategyPlan]:
        """列出某产品的所有策略方案"""
        raise NotImplementedError

    # =========================================================================
    # 通用操作
    # =========================================================================

    @abstractmethod
    def clear(self) -> bool:
        """清空所有数据"""
        raise NotImplementedError

    @abstractmethod
    def get_stats(self) -> Dict[str, int]:
        """获取存储统计信息"""
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(backend={self.backend_name})"


class StorageManager:
    """
    存储管理器。

    负责创建和管理存储后端实例。
    """

    def __init__(self, backend_type: str = "json", backend_config: Optional[dict] = None):
        """
        初始化存储管理器。

        Args:
            backend_type: 后端类型 ("json", "sqlite")
            backend_config: 后端配置字典
        """
        self.backend_type = backend_type
        self.backend_config = backend_config or {}
        self._storage: Optional[BaseStorage] = None

    def get_storage(self) -> BaseStorage:
        """获取存储实例"""
        if self._storage is None:
            self._storage = self._create_storage()
        return self._storage

    def _create_storage(self) -> BaseStorage:
        """创建存储实例"""
        if self.backend_type == "json":
            from .json_store import JSONStorage
            return JSONStorage(**self.backend_config)
        elif self.backend_type == "sqlite":
            from .sqlite_store import SQLiteStorage
            return SQLiteStorage(**self.backend_config)
        else:
            raise ValueError(f"Unknown storage backend: {self.backend_type}")

    def close(self):
        """关闭存储连接"""
        if self._storage:
            if hasattr(self._storage, 'close'):
                self._storage.close()
            self._storage = None


class StorageContext:
    """
    存储上下文（Context Manager）。

    用于自动管理存储生命周期。

    使用方式:
        with StorageContext("json", {"path": "data/"}) as storage:
            storage.save_note(note)
    """

    def __init__(self, backend_type: str = "json", backend_config: Optional[dict] = None):
        self.manager = StorageManager(backend_type, backend_config)
        self.storage = None

    def __enter__(self) -> BaseStorage:
        self.storage = self.manager.get_storage()
        return self.storage

    def __exit__(self, *args):
        self.manager.close()
