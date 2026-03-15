"""
集成层 (Integrations)。

负责与第三方服务的集成：
- xiaohongshu-cli API 包装
- ohmyxhs SKILL 调用
- LLM 降级方案
"""

from .xhs_port import XhsPort
from .xhs_cli_adapter import XhsCliAdapter
from .xhs_factory import (
    DEFAULT_XHS_BACKEND,
    XHS_BACKEND_ENV,
    create_xhs_cli_port,
    create_xhs_port,
    register_xhs_backend,
    get_registered_xhs_backends,
)

__all__ = [
    "XhsPort",
    "XhsCliAdapter",
    "DEFAULT_XHS_BACKEND",
    "XHS_BACKEND_ENV",
    "create_xhs_cli_port",
    "create_xhs_port",
    "register_xhs_backend",
    "get_registered_xhs_backends",
]
