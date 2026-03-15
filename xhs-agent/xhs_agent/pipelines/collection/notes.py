"""
笔记采集模块。

负责采集小红书笔记数据：
- 搜索笔记
- 获取笔记详情
- 采集笔记互动数据
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, List, Optional

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
            from xhs_cli.cookies import get_cookies
            from xhs_cli.client import XhsClient

            logger.info("Initializing XHS API client...")
            _browser, cookies = get_cookies()
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

                notes = search_result.get("items", [])
                logger.info(
                    "Found %d notes for keyword: %s",
                    len(notes),
                    keyword,
                )

                # 转换为 NoteData 格式
                note_data_list: list[NoteData] = []
                for note in notes:
                    try:
                        note_data_list.append(
                            self._convert_to_note_data(note, source_keyword=keyword)
                        )
                    except Exception as exc:
                        logger.debug("Skip malformed note payload: %s", exc)
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
        # xhs_cli 客户端是同步接口，这里做轻量分页封装。
        try:
            items: list[dict[str, Any]] = []
            page = 1
            remaining = max(limit, 1)

            while remaining > 0:
                page_size = min(20, remaining)
                result = self._xhs_client.search_notes(
                    keyword=keyword,
                    sort=sort,
                    page=page,
                    page_size=page_size,
                )
                page_items = result.get("items", []) if isinstance(result, dict) else []
                if not isinstance(page_items, list) or not page_items:
                    break
                items.extend([item for item in page_items if isinstance(item, dict)])
                remaining -= len(page_items)
                if remaining <= 0:
                    break
                has_more_raw = result.get("has_more") if isinstance(result, dict) else None
                if has_more_raw is True:
                    page += 1
                    continue
                if has_more_raw is False:
                    break
                if len(page_items) < page_size:
                    break
                page += 1

            return {"items": items}
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
            result = self._xhs_client.get_note_detail(note_id)
            if not isinstance(result, dict):
                return None
            items = result.get("items")
            if isinstance(items, list) and items:
                first = items[0]
                if isinstance(first, dict):
                    note_card = first.get("note_card")
                    if isinstance(note_card, dict):
                        return note_card
                    return first
            return result
        except Exception as e:
            logger.error("Get note detail API error: %s", str(e))
            raise

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
            if not raw:
                return datetime.now(timezone.utc)
            if raw.isdigit():
                return NoteAggregator._parse_datetime(int(raw))
            try:
                return datetime.fromisoformat(raw.replace("Z", "+00:00"))
            except ValueError:
                return datetime.now(timezone.utc)

        return datetime.now(timezone.utc)

    @staticmethod
    def _normalize_note_type(raw_type: Any) -> str:
        normalized = str(raw_type or "").lower()
        if normalized in {"video", "image", "carousel"}:
            return normalized
        if normalized in {"normal", "note"}:
            return "image"
        return "image"

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
        # 兼容 search/items、feed/items、html fallback 等多种结构。
        note_info = api_response.get("note_card", api_response)
        if not isinstance(note_info, dict):
            note_info = {}

        user_info = note_info.get("user", {})
        if not isinstance(user_info, dict):
            user_info = {}

        interact_info = note_info.get("interact_info", {})
        if not isinstance(interact_info, dict):
            interact_info = {}

        note_id = str(
            note_info.get("note_id")
            or note_info.get("id")
            or api_response.get("note_id")
            or ""
        ).strip()
        title = str(
            note_info.get("title")
            or note_info.get("display_title")
            or note_info.get("desc")
            or note_id
        ).strip()
        content = str(note_info.get("content") or note_info.get("desc") or "").strip()

        raw_images = note_info.get("image_list") or note_info.get("images") or []
        image_urls: list[str] = []
        if isinstance(raw_images, list):
            for image in raw_images:
                if isinstance(image, str):
                    image_urls.append(image)
                    continue
                if not isinstance(image, dict):
                    continue
                info_list = image.get("info_list_v2")
                info_list_url = ""
                if (
                    isinstance(info_list, list)
                    and info_list
                    and isinstance(info_list[0], dict)
                ):
                    info_list_url = str(info_list[0].get("url", "")).strip()
                image_url = (
                    image.get("url_default")
                    or image.get("url")
                    or image.get("url_pre")
                    or info_list_url
                )
                if isinstance(image_url, str) and image_url:
                    image_urls.append(image_url)

        published_at_raw = (
            note_info.get("published_at")
            or note_info.get("publish_time")
            or note_info.get("time")
            or note_info.get("create_time")
        )

        return NoteData(
            note_id=note_id,
            title=title,
            content=content,
            author_id=str(
                note_info.get("author_id")
                or user_info.get("user_id")
                or user_info.get("userid")
                or ""
            ).strip(),
            author_name=str(
                note_info.get("author_name")
                or user_info.get("nickname")
                or user_info.get("name")
                or ""
            ).strip(),
            note_type=self._normalize_note_type(
                note_info.get("note_type") or note_info.get("type")
            ),
            images=image_urls,
            topics=[
                str(item)
                for item in (note_info.get("topics") or [])
                if isinstance(item, (str, int))
            ],
            mentioned_products=[
                str(item)
                for item in (note_info.get("mentioned_products") or [])
                if isinstance(item, (str, int))
            ],
            likes=self._safe_int(
                interact_info.get("liked_count")
                or interact_info.get("likes")
            ),
            comments_count=self._safe_int(
                interact_info.get("comment_count")
                or interact_info.get("comments")
            ),
            shares=self._safe_int(
                interact_info.get("share_count")
                or interact_info.get("shares")
            ),
            collects=self._safe_int(
                interact_info.get("collected_count")
                or interact_info.get("collects")
            ),
            reposts=self._safe_int(
                interact_info.get("repost_count")
                or interact_info.get("reposts")
            ),
            published_at=self._parse_datetime(published_at_raw),
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
