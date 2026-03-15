"""
xhs_cli 适配器实现。

该文件是 xhs-agent 中唯一直接依赖 xhs_cli API 的位置。
"""

from __future__ import annotations

from typing import Any

from .xhs_port import XhsPort


class XhsCliAdapter(XhsPort):
    """将 xhs_cli 客户端适配为 XhsPort 协议。"""

    def __init__(self, client: Any):
        self._client = client

    def search_notes(
        self,
        keyword: str,
        sort: str,
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        return self._client.search_notes(
            keyword=keyword,
            sort=sort,
            page=page,
            page_size=page_size,
        )

    def get_note_detail(self, note_id: str) -> dict[str, Any]:
        return self._client.get_note_detail(note_id)

    def get_user_info(self, user_id: str) -> dict[str, Any]:
        return self._client.get_user_info(user_id)

    def get_user_notes(self, user_id: str, cursor: str = "") -> dict[str, Any]:
        return self._client.get_user_notes(user_id, cursor=cursor)

    def get_all_comments(self, note_id: str, max_pages: int = 20) -> dict[str, Any]:
        return self._client.get_all_comments(note_id, max_pages=max_pages)

    def close(self) -> None:
        self._client.close()
