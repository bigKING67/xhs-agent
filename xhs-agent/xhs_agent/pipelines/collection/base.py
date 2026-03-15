"""
采集管道的基类和接口定义。
"""

from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional
from datetime import datetime

from xhs_agent.types import CollectionResult, CollectionConfig

logger = logging.getLogger(__name__)

T = TypeVar("T")  # 泛型，表示采集的数据类型


class BaseCollector(ABC, Generic[T]):
    """
    采集器基类。

    所有采集器都继承此类，实现：
    - 数据采集逻辑
    - 错误处理和重试
    - 速率限制
    - 日志记录
    """

    def __init__(self, config: Optional[CollectionConfig] = None):
        """
        初始化采集器。

        Args:
            config: 采集配置。如果为 None，使用默认配置。
        """
        self.config = config or CollectionConfig()
        self.session = None  # 将在子类中初始化（HTTP session 或类似）

    async def collect_async(self, *args, **kwargs) -> List[T]:
        """
        异步采集数据（主接口）。

        所有子类都应实现此方法。
        """
        raise NotImplementedError("Subclass must implement collect_async()")

    async def collect_batch_async(
        self, items: List[str], *args, **kwargs
    ) -> List[T]:
        """
        异步批量采集（带并发控制）。

        Args:
            items: 要采集的项目列表（如笔记 ID、用户 ID 等）
            *args, **kwargs: 传给 collect_async 的参数

        Returns:
            采集的数据列表

        使用信号量控制并发数，避免过多并发请求导致限流。
        """
        semaphore = asyncio.Semaphore(self.config.concurrent_requests)

        async def bounded_collect(item: str) -> Optional[T]:
            async with semaphore:
                try:
                    await self._apply_rate_limit()
                    result = await self._collect_with_retry(item, *args, **kwargs)
                    return result
                except Exception as e:
                    logger.warning(
                        "Failed to collect item %s: %s (will skip)",
                        item,
                        str(e),
                    )
                    return None

        results = await asyncio.gather(
            *[bounded_collect(item) for item in items],
            return_exceptions=False
        )

        # 过滤掉 None（失败的采集）
        return [r for r in results if r is not None]

    async def _collect_with_retry(
        self, item: str, *args, **kwargs
    ) -> Optional[T]:
        """
        带重试逻辑的采集（私有方法）。

        Args:
            item: 单个项目标识符
            *args, **kwargs: 传给 collect_single 的参数

        Returns:
            采集的数据，或失败时返回 None
        """
        last_exception = None

        for attempt in range(1, self.config.retry_attempts + 1):
            try:
                logger.debug(
                    "Collecting item %s (attempt %d/%d)",
                    item,
                    attempt,
                    self.config.retry_attempts,
                )
                result = await self.collect_single(item, *args, **kwargs)
                logger.debug("Successfully collected item %s", item)
                return result

            except Exception as e:
                last_exception = e
                if attempt < self.config.retry_attempts:
                    wait_time = min(2 ** (attempt - 1), 30)  # 指数退避，最多 30 秒
                    logger.warning(
                        "Failed to collect item %s (attempt %d/%d), "
                        "retrying in %.1fs: %s",
                        item,
                        attempt,
                        self.config.retry_attempts,
                        wait_time,
                        str(e),
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(
                        "Failed to collect item %s after %d attempts: %s",
                        item,
                        self.config.retry_attempts,
                        str(e),
                    )

        return None

    @abstractmethod
    async def collect_single(self, item: str, *args, **kwargs) -> T:
        """
        采集单个项目（抽象方法，子类实现）。

        Args:
            item: 项目标识符（如笔记 ID、用户 ID）
            *args, **kwargs: 额外参数

        Returns:
            采集到的数据对象
        """
        raise NotImplementedError("Subclass must implement collect_single()")

    async def _apply_rate_limit(self) -> None:
        """
        应用速率限制（避免请求过于频繁）。
        """
        if self.config.rate_limit_delay > 0:
            await asyncio.sleep(self.config.rate_limit_delay)

    async def close(self) -> None:
        """
        关闭采集器（清理资源）。

        子类应实现此方法关闭 HTTP session 等资源。
        """
        pass

    def __enter__(self):
        """Context manager 支持（同步）"""
        return self

    def __exit__(self, *args):
        """Context manager 清理"""
        # 同步上下文中无法调用异步方法，仅用于同步代码
        pass

    async def __aenter__(self):
        """异步 Context manager 支持"""
        return self

    async def __aexit__(self, *args):
        """异步 Context manager 清理"""
        await self.close()


class SyncCollectorAdapter:
    """
    将异步采集器适配为同步接口。

    用于在同步代码中调用异步采集器。

    示例:
        collector = SyncCollectorAdapter(async_collector)
        results = collector.collect(['note_1', 'note_2'])
    """

    def __init__(self, async_collector: BaseCollector):
        self.collector = async_collector

    def collect(self, items: List[str], *args, **kwargs) -> List:
        """同步采集接口"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.collector.collect_batch_async(items, *args, **kwargs)
            )
        finally:
            loop.close()

    def close(self) -> None:
        """关闭采集器"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.collector.close())
        finally:
            loop.close()


class CollectionLogger:
    """
    采集过程的日志和统计。
    """

    def __init__(self):
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.total_items: int = 0
        self.success_count: int = 0
        self.failed_count: int = 0
        self.errors: List[str] = []

    def start(self):
        """记录开始时间"""
        self.start_time = datetime.now()
        logger.info("Collection started at %s", self.start_time)

    def finish(self):
        """记录结束时间"""
        self.end_time = datetime.now()
        logger.info("Collection finished at %s", self.end_time)

    def record_success(self, item: str):
        """记录成功的采集"""
        self.success_count += 1
        logger.debug("Collected successfully: %s", item)

    def record_failure(self, item: str, error: str):
        """记录失败的采集"""
        self.failed_count += 1
        self.errors.append(f"{item}: {error}")
        logger.warning("Failed to collect %s: %s", item, error)

    def get_result(self) -> CollectionResult:
        """生成采集结果"""
        duration = (
            (self.end_time - self.start_time).total_seconds()
            if self.end_time and self.start_time
            else 0.0
        )

        return CollectionResult(
            success=self.failed_count == 0,
            items_collected=self.success_count,
            items_failed=self.failed_count,
            error_message=(
                f"Failed items: {len(self.errors)}" if self.errors else None
            ),
            duration_seconds=duration,
            timestamp=self.end_time or datetime.now(),
        )

    def print_summary(self):
        """打印总结信息"""
        result = self.get_result()
        logger.info(
            "Collection Summary: %d succeeded, %d failed, %.1f seconds",
            result.items_collected,
            result.items_failed,
            result.duration_seconds,
        )

        if self.errors and len(self.errors) <= 10:
            for error in self.errors:
                logger.warning("  Error: %s", error)
