"""
XHS 端口工厂。

负责创建默认的 xhs_cli 适配器实例，并支持可配置后端选择。
"""

from __future__ import annotations

import importlib
import os
from typing import Callable

from .xhs_cli_adapter import XhsCliAdapter
from .xhs_port import XhsPort

DEFAULT_XHS_BACKEND = "xhs_cli"
XHS_BACKEND_ENV = "XHS_AGENT_XHS_BACKEND"


def create_xhs_cli_port() -> XhsPort:
    """创建 xhs_cli 后端端口。"""
    from xhs_cli.cookies import get_cookies
    from xhs_cli.client import XhsClient

    _browser, cookies = get_cookies()
    client = XhsClient(cookies)
    return XhsCliAdapter(client)


_BACKEND_FACTORIES: dict[str, Callable[[], XhsPort]] = {
    DEFAULT_XHS_BACKEND: create_xhs_cli_port,
}


def register_xhs_backend(name: str, factory: Callable[[], XhsPort]) -> None:
    """注册自定义后端工厂。"""
    backend_name = str(name).strip().lower()
    if not backend_name:
        raise ValueError("Backend name cannot be empty")
    if not callable(factory):
        raise TypeError("Backend factory must be callable")
    _BACKEND_FACTORIES[backend_name] = factory


def get_registered_xhs_backends() -> tuple[str, ...]:
    """返回已注册后端列表。"""
    return tuple(sorted(_BACKEND_FACTORIES))


def _load_python_factory(factory_path: str) -> Callable[[], XhsPort]:
    raw = str(factory_path).strip()
    if ":" not in raw:
        raise ValueError(
            "Invalid python factory path. Expected format: module:function"
        )
    module_name, attr_name = raw.split(":", 1)
    module_name = module_name.strip()
    attr_name = attr_name.strip()
    if not module_name or not attr_name:
        raise ValueError(
            "Invalid python factory path. Expected format: module:function"
        )
    module = importlib.import_module(module_name)
    factory = getattr(module, attr_name, None)
    if factory is None:
        raise AttributeError(
            f"Factory '{attr_name}' not found in module '{module_name}'"
        )
    if not callable(factory):
        raise TypeError(
            f"Factory '{module_name}:{attr_name}' is not callable"
        )
    return factory


def create_xhs_port(backend: str | None = None) -> XhsPort:
    """
    创建 XHS 访问端口。

    backend 解析顺序：
    1. 函数参数 backend
    2. 环境变量 XHS_AGENT_XHS_BACKEND
    3. 默认值 xhs_cli

    支持值：
    - 已注册后端名（如 xhs_cli）
    - python:module:function（动态加载自定义工厂）
    """
    selected = (
        backend
        or os.getenv(XHS_BACKEND_ENV, DEFAULT_XHS_BACKEND)
    )
    selected = str(selected).strip()
    if not selected:
        selected = DEFAULT_XHS_BACKEND

    normalized = selected.lower()
    factory = _BACKEND_FACTORIES.get(normalized)
    if factory is not None:
        return factory()

    if normalized.startswith("python:"):
        dynamic_factory = _load_python_factory(selected.split(":", 1)[1])
        return dynamic_factory()

    available = ", ".join(get_registered_xhs_backends())
    raise ValueError(
        f"Unknown XHS backend '{selected}'. "
        f"Available backends: {available}. "
        "Or use python:module:function."
    )
