"""
XHS 集成端口定义。

采集器只依赖本文件中的协议，不直接依赖 xhs_cli 的具体实现。
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class XhsPort(Protocol):
    """小红书数据访问端口协议。"""

    def search_notes(
        self,
        keyword: str,
        sort: str,
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        """搜索笔记。"""
        ...

    def get_note_detail(self, note_id: str) -> dict[str, Any]:
        """获取笔记详情。"""
        ...

    def get_user_info(self, user_id: str) -> dict[str, Any]:
        """获取用户基础信息。"""
        ...

    def get_user_notes(self, user_id: str, cursor: str = "") -> dict[str, Any]:
        """分页获取用户笔记。"""
        ...

    def get_all_comments(self, note_id: str, max_pages: int = 20) -> dict[str, Any]:
        """分页获取笔记评论。"""
        ...

    def close(self) -> None:
        """关闭底层连接。"""
        ...
