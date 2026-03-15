"""
XHS 端口工厂。

负责创建默认的 xhs_cli 适配器实例。
"""

from __future__ import annotations

from .xhs_cli_adapter import XhsCliAdapter
from .xhs_port import XhsPort


def create_xhs_port() -> XhsPort:
    """创建默认 XHS 访问端口。"""
    from xhs_cli.cookies import get_cookies
    from xhs_cli.client import XhsClient

    _browser, cookies = get_cookies()
    client = XhsClient(cookies)
    return XhsCliAdapter(client)
