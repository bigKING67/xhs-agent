"""
JSON 存储后端。

使用 JSON 文件存储数据，适合快速原型和小规模数据。
"""

from __future__ import annotations

import logging
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from xhs_agent.types import (
    NoteData,
    NoteWithComments,
    CelebData,
    Comment,
    PerformanceMetrics,
    SentimentReport,
    StrategySignals,
    XhsStrategyPlan,
)
from .base import BaseStorage

logger = logging.getLogger(__name__)


class JSONStorage(BaseStorage):
    """
    JSON 文件存储后端。

    将所有数据存储为 JSON 文件。

    目录结构:
    ```
    data/
    ├── notes/
    │   └── note_{id}.json
    ├── celebrities/
    │   └── celeb_{id}.json
    ├── analysis/
    │   ├── performance_{note_id}.json
    │   ├── sentiment_{note_id}.json
    │   └── signals_{note_id}.json
    └── strategies/
        └── strategy_{product}_{celeb}.json
    ```

    使用方式:
        storage = JSONStorage(path="data/")
        storage.save_note(note)
        note = storage.get_note("note_123")
    """

    def __init__(self, path: str = "data/"):
        """初始化 JSON 存储"""
        super().__init__("json")

        self.root_path = Path(path)
        self._ensure_directories()

    def _ensure_directories(self):
        """确保所有目录存在"""
        dirs = [
            self.root_path,
            self.root_path / "notes",
            self.root_path / "celebrities",
            self.root_path / "analysis" / "performance",
            self.root_path / "analysis" / "sentiment",
            self.root_path / "analysis" / "signals",
            self.root_path / "strategies",
        ]

        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Data directories ensured at {self.root_path}")

    # =========================================================================
    # 笔记存储
    # =========================================================================

    def save_note(self, note: NoteData) -> bool:
        """保存单个笔记"""
        try:
            path = self.root_path / "notes" / f"note_{note.note_id}.json"
            data = note.model_dump(mode="json")

            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.debug(f"Saved note to {path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save note {note.note_id}: {e}")
            return False

    def save_notes(self, notes: List[NoteData]) -> int:
        """批量保存笔记"""
        saved_count = 0

        for note in notes:
            if self.save_note(note):
                saved_count += 1

        logger.info(f"Saved {saved_count}/{len(notes)} notes")
        return saved_count

    def save_note_with_comments(
        self,
        note_with_comments: NoteWithComments,
    ) -> bool:
        """保存笔记及其评论"""
        try:
            # 保存笔记
            self.save_note(note_with_comments.note)

            # 保存评论
            path = (
                self.root_path / "notes" /
                f"note_{note_with_comments.note.note_id}_comments.json"
            )

            comments_data = [
                c.model_dump(mode="json")
                for c in note_with_comments.comments
            ]

            with open(path, "w", encoding="utf-8") as f:
                json.dump(comments_data, f, ensure_ascii=False, indent=2)

            logger.debug(f"Saved {len(comments_data)} comments for note {note_with_comments.note.note_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to save note with comments: {e}")
            return False

    def get_note(self, note_id: str) -> Optional[NoteData]:
        """获取单个笔记"""
        try:
            path = self.root_path / "notes" / f"note_{note_id}.json"

            if not path.exists():
                return None

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            return NoteData(**data)

        except Exception as e:
            logger.error(f"Failed to load note {note_id}: {e}")
            return None

    def get_notes(self, keyword: str = "") -> List[NoteData]:
        """按关键词获取笔记（简单实现：返回所有笔记）"""
        notes = []
        notes_dir = self.root_path / "notes"

        try:
            for file_path in notes_dir.glob("note_*.json"):
                # 跳过评论文件
                if "_comments.json" in str(file_path):
                    continue

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    note = NoteData(**data)

                    # 如果提供了关键词，过滤
                    if keyword:
                        if keyword.lower() in note.title.lower() or \
                           keyword.lower() in note.content.lower():
                            notes.append(note)
                    else:
                        notes.append(note)

                except Exception as e:
                    logger.warning(f"Failed to load note from {file_path}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Failed to get notes: {e}")

        return notes

    # =========================================================================
    # 达人存储
    # =========================================================================

    def save_celebrity(self, celebrity: CelebData) -> bool:
        """保存达人数据"""
        try:
            path = self.root_path / "celebrities" / f"celeb_{celebrity.celeb_id}.json"
            data = celebrity.model_dump(mode="json")

            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.debug(f"Saved celebrity to {path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save celebrity {celebrity.celeb_id}: {e}")
            return False

    def save_celebrities(self, celebrities: List[CelebData]) -> int:
        """批量保存达人数据"""
        saved_count = 0

        for celeb in celebrities:
            if self.save_celebrity(celeb):
                saved_count += 1

        logger.info(f"Saved {saved_count}/{len(celebrities)} celebrities")
        return saved_count

    def get_celebrity(self, celeb_id: str) -> Optional[CelebData]:
        """获取达人数据"""
        try:
            path = self.root_path / "celebrities" / f"celeb_{celeb_id}.json"

            if not path.exists():
                return None

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            return CelebData(**data)

        except Exception as e:
            logger.error(f"Failed to load celebrity {celeb_id}: {e}")
            return None

    # =========================================================================
    # 分析结果存储
    # =========================================================================

    def save_performance_metrics(self, metrics: PerformanceMetrics) -> bool:
        """保存表现指标"""
        try:
            path = (
                self.root_path / "analysis" / "performance" /
                f"perf_{metrics.note_id}.json"
            )
            data = metrics.model_dump(mode="json")

            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            logger.error(f"Failed to save performance metrics: {e}")
            return False

    def save_sentiment_report(self, report: SentimentReport) -> bool:
        """保存情感分析报告"""
        try:
            path = (
                self.root_path / "analysis" / "sentiment" /
                f"sent_{report.note_id}.json"
            )
            data = report.model_dump(mode="json")

            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            logger.error(f"Failed to save sentiment report: {e}")
            return False

    def save_strategy_signals(self, signals: StrategySignals) -> bool:
        """保存策略信号"""
        try:
            path = (
                self.root_path / "analysis" / "signals" /
                f"signal_{signals.note_id}.json"
            )
            # 只保存信号，不保存源数据引用
            data = {
                "note_id": signals.note_id,
                "top_pain_point": signals.top_pain_point,
                "top_performing_frames": signals.top_performing_frames,
                "user_emotions": signals.user_emotions,
                "competitor_insights": signals.competitor_insights,
                "content_angle_recommendation": signals.content_angle_recommendation,
                "signal_confidence": signals.signal_confidence,
            }

            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            logger.error(f"Failed to save strategy signals: {e}")
            return False

    def get_performance_metrics(self, note_id: str) -> Optional[PerformanceMetrics]:
        """获取表现指标"""
        try:
            path = (
                self.root_path / "analysis" / "performance" /
                f"perf_{note_id}.json"
            )

            if not path.exists():
                return None

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            return PerformanceMetrics(**data)

        except Exception as e:
            logger.error(f"Failed to load performance metrics: {e}")
            return None

    def get_sentiment_report(self, note_id: str) -> Optional[SentimentReport]:
        """获取情感分析报告"""
        try:
            path = (
                self.root_path / "analysis" / "sentiment" /
                f"sent_{note_id}.json"
            )

            if not path.exists():
                return None

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            return SentimentReport(**data)

        except Exception as e:
            logger.error(f"Failed to load sentiment report: {e}")
            return None

    def get_strategy_signals(self, note_id: str) -> Optional[StrategySignals]:
        """获取策略信号"""
        try:
            path = (
                self.root_path / "analysis" / "signals" /
                f"signal_{note_id}.json"
            )

            if not path.exists():
                return None

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            return StrategySignals(**data)

        except Exception as e:
            logger.error(f"Failed to load strategy signals: {e}")
            return None

    # =========================================================================
    # 策略结果存储
    # =========================================================================

    def save_strategy_plan(self, plan: XhsStrategyPlan) -> bool:
        """保存策略方案"""
        try:
            filename = f"strategy_{plan.product_name}_{plan.target_celebrity}.json"
            path = self.root_path / "strategies" / filename
            data = plan.model_dump(mode="json")

            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"Saved strategy plan to {path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save strategy plan: {e}")
            return False

    def get_strategy_plan(
        self,
        product_name: str,
        celebrity: str,
    ) -> Optional[XhsStrategyPlan]:
        """获取策略方案"""
        try:
            filename = f"strategy_{product_name}_{celebrity}.json"
            path = self.root_path / "strategies" / filename

            if not path.exists():
                return None

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            return XhsStrategyPlan(**data)

        except Exception as e:
            logger.error(f"Failed to load strategy plan: {e}")
            return None

    def list_strategy_plans(self, product_name: str) -> List[XhsStrategyPlan]:
        """列出某产品的所有策略方案"""
        plans = []

        try:
            strategies_dir = self.root_path / "strategies"

            for file_path in strategies_dir.glob(f"strategy_{product_name}_*.json"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    plan = XhsStrategyPlan(**data)
                    plans.append(plan)
                except Exception as e:
                    logger.warning(f"Failed to load strategy from {file_path}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Failed to list strategy plans: {e}")

        return plans

    # =========================================================================
    # 通用操作
    # =========================================================================

    def clear(self) -> bool:
        """清空所有数据"""
        try:
            import shutil

            if self.root_path.exists():
                shutil.rmtree(self.root_path)
                self._ensure_directories()
                logger.info(f"Cleared all data in {self.root_path}")
                return True

            return True

        except Exception as e:
            logger.error(f"Failed to clear storage: {e}")
            return False

    def get_stats(self) -> Dict[str, int]:
        """获取存储统计信息"""
        try:
            note_files = [
                path
                for path in (self.root_path / "notes").glob("note_*.json")
                if "_comments.json" not in path.name
            ]
            stats = {
                "notes": len(note_files),
                "celebrities": len(list((self.root_path / "celebrities").glob("celeb_*.json"))),
                "performance_metrics": len(list((self.root_path / "analysis" / "performance").glob("*.json"))),
                "sentiment_reports": len(list((self.root_path / "analysis" / "sentiment").glob("*.json"))),
                "strategy_signals": len(list((self.root_path / "analysis" / "signals").glob("*.json"))),
                "strategy_plans": len(list((self.root_path / "strategies").glob("*.json"))),
            }

            return stats

        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {}
