"""
笔记采集模块。

负责采集小红书笔记数据：
- 搜索笔记
- 获取笔记详情
- 采集笔记互动数据
"""

from __future__ import annotations

import logging
from typing import Optional, List

from xhs_agent.types import NoteData, CollectionConfig
from .base import BaseCollector

logger = logging.getLogger(__name__)


class NoteAggregator(BaseCollector[NoteData]):
    """
    笔记采集器。

    负责采集笔记数据：
    - 通过关键词搜索笔记
    - 获取笔记详情
    - 采集笔记的互动数据（赞、评论、收藏等）

    使用方式:
        # 异步方式
        aggregator = NoteAggregator(config)
        async with aggregator:
            notes = await aggregator.collect_async(
                keywords=['护肤', '眼膜'],
                max_results=100
            )

        # 同步方式
        from xhs_agent.pipelines.collection.base import SyncCollectorAdapter
        sync_agg = SyncCollectorAdapter(aggregator)
        notes = sync_agg.collect(['note_1', 'note_2'])
    """

    def __init__(self, config: Optional[CollectionConfig] = None):
        super().__init__(config)
        self._xhs_client = None  # 将在初始化时连接 xiaohongshu-cli

    async def init_xhs_client(self):
        """
        初始化小红书 API 客户端。

        这将导入 xiaohongshu-cli 并创建客户端实例。
        """
        try:
            from xiaohongshu_cli.cookies import get_cookies
            from xiaohongshu_cli.client import XhsClient

            logger.info("Initializing XHS API client...")
            cookies = get_cookies()
            self._xhs_client = XhsClient(cookies)
            logger.info("XHS API client initialized successfully")
        except ImportError:
            logger.error("xiaohongshu-cli not found. Please install it first.")
            raise
        except Exception as e:
            logger.error("Failed to initialize XHS API client: %s", str(e))
            raise

    async def collect_async(
        self,
        keywords: List[str],
        sort: str = "general",
        max_results: Optional[int] = None,
    ) -> List[NoteData]:
        """
        按关键词搜索并采集笔记。

        Args:
            keywords: 搜索关键词列表
            sort: 排序方式 ('general', 'popular', 'latest')
            max_results: 最多采集多少条笔记（默认使用配置中的 max_notes_per_search）

        Returns:
            采集到的笔记列表
        """
        if not self._xhs_client:
            await self.init_xhs_client()

        if max_results is None:
            max_results = self.config.max_notes_per_search

        all_notes = []

        for keyword in keywords:
            logger.info(
                "Searching notes for keyword: %s (max: %d)",
                keyword,
                max_results,
            )

            try:
                # 调用小红书 API 搜索笔记
                search_result = await self._search_notes(
                    keyword=keyword,
                    sort=sort,
                    limit=max_results,
                )

                notes = search_result.get("notes", [])
                logger.info(
                    "Found %d notes for keyword: %s",
                    len(notes),
                    keyword,
                )

                # 转换为 NoteData 格式
                note_data_list = [
                    self._convert_to_note_data(note, source_keyword=keyword)
                    for note in notes
                ]
                all_notes.extend(note_data_list)

            except Exception as e:
                logger.error(
                    "Failed to search notes for keyword %s: %s",
                    keyword,
                    str(e),
                )
                continue

        logger.info("Total notes collected: %d", len(all_notes))
        return all_notes

    async def collect_single(
        self, note_id: str, *args, **kwargs
    ) -> Optional[NoteData]:
        """
        采集单个笔记的详情。

        Args:
            note_id: 笔记 ID
            *args, **kwargs: 额外参数

        Returns:
            笔记数据，或失败时返回 None
        """
        if not self._xhs_client:
            await self.init_xhs_client()

        try:
            logger.debug("Fetching note details for: %s", note_id)

            # 调用小红书 API 获取笔记详情
            note_data = await self._get_note_detail(note_id)

            if note_data:
                logger.debug("Successfully fetched note: %s", note_id)
                return self._convert_to_note_data(note_data)
            else:
                logger.warning("Note not found: %s", note_id)
                return None

        except Exception as e:
            logger.error(
                "Failed to fetch note %s: %s",
                note_id,
                str(e),
            )
            raise

    async def _search_notes(
        self,
        keyword: str,
        sort: str = "general",
        limit: int = 100,
    ) -> dict:
        """
        调用小红书 API 搜索笔记。

        Args:
            keyword: 搜索关键词
            sort: 排序方式
            limit: 最多返回多少条

        Returns:
            搜索结果字典
        """
        # 这是对 xiaohongshu-cli.search() 的包装
        # 实际调用时需要正确处理 async/sync 问题
        try:
            result = self._xhs_client.search(
                keyword=keyword,
                sort=sort,
                page=1,
            )
            return result
        except Exception as e:
            logger.error("Search API error: %s", str(e))
            raise

    async def _get_note_detail(self, note_id: str) -> Optional[dict]:
        """
        调用小红书 API 获取笔记详情。

        Args:
            note_id: 笔记 ID

        Returns:
            笔记详情字典
        """
        try:
            result = self._xhs_client.get_note_feed(note_id)
            return result
        except Exception as e:
            logger.error("Get note detail API error: %s", str(e))
            raise

    def _convert_to_note_data(
        self,
        api_response: dict,
        source_keyword: Optional[str] = None,
    ) -> NoteData:
        """
        将 API 响应转换为 NoteData 对象。

        Args:
            api_response: 小红书 API 返回的笔记数据
            source_keyword: 笔记来自哪个搜索关键词

        Returns:
            标准化的 NoteData 对象
        """
        # 从 API 响应中提取字段
        note_info = api_response.get("note_info", api_response)

        return NoteData(
            note_id=note_info.get("note_id", ""),
            title=note_info.get("title", ""),
            content=note_info.get("content", ""),
            author_id=note_info.get("author_id", ""),
            author_name=note_info.get("author_name", ""),
            note_type=note_info.get("note_type", "image"),
            images=note_info.get("image_list", []),
            topics=note_info.get("interact_info", {}).get("topics", []),
            mentioned_products=note_info.get("mentioned_products", []),
            likes=note_info.get("interact_info", {}).get("likes", 0),
            comments_count=note_info.get("interact_info", {})
            .get("comments", 0),
            shares=note_info.get("interact_info", {}).get("shares", 0),
            collects=note_info.get("interact_info", {}).get("collects", 0),
            reposts=note_info.get("interact_info", {}).get("reposts", 0),
            published_at=note_info.get("published_at", ""),
            source_search_keyword=source_keyword,
        )

    async def close(self) -> None:
        """关闭采集器，释放资源"""
        if self._xhs_client:
            try:
                self._xhs_client.close()
                logger.info("XHS API client closed")
            except Exception as e:
                logger.error("Error closing XHS API client: %s", str(e))


# 便利函数：快速采集笔记
async def collect_notes_by_keywords(
    keywords: List[str],
    config: Optional[CollectionConfig] = None,
) -> List[NoteData]:
    """
    快速采集笔记。

    Args:
        keywords: 搜索关键词列表
        config: 采集配置

    Returns:
        采集到的笔记列表

    示例:
        notes = await collect_notes_by_keywords(['护肤', '眼膜'])
    """
    aggregator = NoteAggregator(config)
    try:
        return await aggregator.collect_async(keywords=keywords)
    finally:
        await aggregator.close()
