"""
存储层 (Storage Layer)。

负责数据的持久化存储：
- JSON 文件存储
- SQLite 数据库存储（待实现）
"""

from .base import BaseStorage, StorageManager, StorageContext
from .json_store import JSONStorage

__all__ = [
    "BaseStorage",
    "StorageManager",
    "StorageContext",
    "JSONStorage",
]
