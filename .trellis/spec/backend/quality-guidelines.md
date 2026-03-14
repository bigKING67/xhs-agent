# Quality Guidelines

> Code quality standards for backend development.

---

## Overview

xiaohongshu-cli 项目采用**三层质量检查** + **测试驱动**的开发模式：

1. **Ruff** — 代码风格与错误检查（自动格式化）
2. **mypy** — 静态类型检查（Python 3.10+ 特性）
3. **pytest** — 单元/集成/烟雾三层测试（80%+ 覆盖率）

**检查流程**：
```
Code → Ruff Check → mypy Check → pytest → Commit
```

所有检查都**必须通过**才能提交代码。

---

## Lint 规则 (Ruff)

### 配置信息

**位置**: `pyproject.toml`

```toml
[tool.ruff]
target-version = "py310"
line-length = 120

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP"]
```

**目标版本**: Python 3.10+（使用 f-string, match-case, type hints 等现代特性）

### 规则说明

| 规则集 | 含义 | 检查内容 |
|--------|------|---------|
| **E** | PEP 8 错误 | 缩进、空格、换行、命名 |
| **F** | Pyflakes | 未定义变量、未使用导入、重复参数 |
| **I** | isort | 导入排序与分组 |
| **B** | flake8-bugbear | 潜在 bug（空 except、可变默认参数等） |
| **UP** | pyupgrade | 过时语法（使用现代 Python） |

### 运行 Lint

```bash
# 检查所有代码
uv run ruff check xhs_cli/ tests/

# 自动格式化修复（大部分错误）
uv run ruff format xhs_cli/ tests/

# 检查特定文件
uv run ruff check xhs_cli/client.py

# 显示详细错误信息
uv run ruff check xhs_cli/ --show-fixes
```

### 常见 Ruff 错误

#### E501 — 行太长（>120 字符）
```python
# ❌ 不好: 超过 120 字符
logger.warning("This is a very long line that exceeds the 120 character limit and should be split into multiple lines")

# ✅ 好: 换行
logger.warning(
    "This is a very long line that exceeds the 120 character limit "
    "and should be split into multiple lines"
)
```

#### F401 — 未使用的导入
```python
# ❌ 不好: 导入了但没用
import time
import json  # 没有用到

def get_data():
    return {"data": "value"}

# ✅ 好: 删除未使用的导入
import json

def get_data():
    return json.dumps({"data": "value"})
```

#### B006 — 可变默认参数
```python
# ❌ 不好: 列表作为默认参数（被共享）
def add_note(notes=[]):
    notes.append("new_note")
    return notes

# ✅ 好: 使用 None 并在函数内创建
def add_note(notes=None):
    if notes is None:
        notes = []
    notes.append("new_note")
    return notes
```

#### I001 — 导入排序错误
```python
# ❌ 不好: 导入顺序混乱
from pathlib import Path
import json
import sys

from requests import get
from .client import XhsClient

# ✅ 好: 按标准库 → 第三方 → 本地 排序
import json
import sys
from pathlib import Path

import requests

from .client import XhsClient
```

---

## 类型检查 (mypy)

### 配置信息

**位置**: `pyproject.toml`

```toml
[tool.mypy]
python_version = "3.10"
ignore_missing_imports = true
check_untyped_defs = true
```

**说明**：
- `python_version = "3.10"` — 使用 Python 3.10+ 特性（union: `int | None` 而非 `Union[int, None]`）
- `ignore_missing_imports = true` — 第三方库没有类型提示时允许使用（某些老旧库没有 `py.typed`）
- `check_untyped_defs = true` — 对没有类型注解的函数参数报错

### 运行类型检查

```bash
# 检查所有代码
uv run mypy xhs_cli/

# 检查特定文件
uv run mypy xhs_cli/client.py

# 显示详细信息
uv run mypy xhs_cli/ --pretty

# 显示没有类型注解的函数
uv run mypy xhs_cli/ --untyped-calls
```

### 类型注解要求

#### 函数签名必须有类型注解

```python
# ❌ 不好: 没有类型注解
def search(keyword):
    return client.search(keyword)

# ✅ 好: 完整的类型注解
def search(keyword: str) -> dict:
    return client.search(keyword)

# ✅ 也好: 导入类型用于复杂返回值
from typing import Any

def search(keyword: str) -> dict[str, Any]:
    return client.search(keyword)
```

#### 使用现代 Python 3.10+ 类型语法

```python
# ❌ 不好: 用 Union（过时）
from typing import Union, Optional

def handle(data: Union[str, int, None]) -> Optional[dict]:
    pass

# ✅ 好: 用 | 操作符（Python 3.10+）
def handle(data: str | int | None) -> dict | None:
    pass
```

#### 可选参数用 `| None` 表示

```python
# ❌ 不好: Optional 老语法
from typing import Optional

def get_user(user_id: Optional[str] = None) -> dict:
    pass

# ✅ 好: 用 | None
def get_user(user_id: str | None = None) -> dict:
    pass
```

#### 异常处理需要类型注解

```python
# ❌ 不好: except 没有类型指定
try:
    result = client.search("keyword")
except:  # 捕获所有异常
    print("Error")

# ✅ 好: 明确异常类型
try:
    result = client.search("keyword")
except SessionExpiredError:
    print("Session expired")
except XhsApiError as e:
    print(f"API error: {e}")
```

#### 类型别名提高可读性

```python
# ✅ 好: 定义类型别名便于重用
JsonDict = dict[str, Any]
Cookies = dict[str, str]

def get_note(note_id: str, cookies: Cookies) -> JsonDict:
    pass
```

#### 使用 `from __future__ import annotations`

```python
# ✅ 推荐: 所有文件顶部都有此导入
from __future__ import annotations

# 允许使用类本身作为类型（不需要字符串引用）
class User:
    def get_friend(self) -> User:  # 不需要 "User" 字符串
        pass
```

### 常见 mypy 错误

#### Incompatible return type

```python
# ❌ 不好: 返回类型不匹配
def get_count() -> int:
    data = {"count": "10"}  # 字符串而非整数
    return data["count"]   # mypy 错误

# ✅ 好: 转换为正确类型
def get_count() -> int:
    data = {"count": "10"}
    return int(data["count"])
```

#### Argument of type X cannot be assigned to parameter of type Y

```python
# ❌ 不好: 类型不匹配
def process(items: list[str]) -> None:
    pass

items = [1, 2, 3]  # 整数列表
process(items)     # mypy 错误

# ✅ 好: 使用正确的类型
items: list[str] = ["1", "2", "3"]
process(items)
```

---

## 测试配置 (pytest)

### 配置信息

**位置**: `pyproject.toml`

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-m 'not smoke'"
markers = ["smoke: real-API integration tests (run with: pytest -m smoke)"]
```

**说明**：
- `testpaths = ["tests"]` — 测试文件位置
- `python_files = ["test_*.py"]` — 测试文件命名规则
- `addopts = "-m 'not smoke'"` — 默认排除 smoke 测试（不运行真实 API 调用）
- `markers` — 定义测试标记（方便分类运行）

### 测试分类

| 类别 | 标记 | 文件 | 运行方式 | 依赖 |
|------|------|------|---------|------|
| **单元测试** | (无) | `test_signing.py`, `test_client.py`, 等 | `uv run pytest tests/ -m "not smoke"` | Mock/Fixtures |
| **集成测试** | (无) | `test_integration.py` | `uv run pytest tests/test_integration.py` | 真实 API（需 Cookie） |
| **烟雾测试** | `smoke` | `test_smoke.py` | `uv run pytest -m smoke` | 真实 API（需 Cookie） |

### 运行测试

```bash
# 快速测试（仅单元测试，无网络）
uv run pytest tests/ -m "not smoke"

# 完整测试（包括集成测试）
uv run pytest tests/ -v -m "not smoke"

# 烟雾测试（真实 API 调用）
uv run pytest tests/ -m smoke

# 特定测试文件
uv run pytest tests/test_signing.py -v

# 特定测试函数
uv run pytest tests/test_client.py::test_retry_logic -v

# 显示详细输出
uv run pytest tests/ -vv -s

# 覆盖率报告
uv run pytest tests/ -m "not smoke" --cov=xhs_cli --cov-report=html
```

### 测试覆盖率要求

**最低要求**: 80% 代码覆盖率

**检查覆盖率**：
```bash
uv run pytest tests/ -m "not smoke" --cov=xhs_cli --cov-report=term-missing
```

**覆盖率不足时**：
- 确保所有关键路径都有测试（异常处理、边界情况）
- 无法 100% 覆盖的代码（如 `sys.exit()`）可用 `# pragma: no cover`
- 对于可选的依赖，可排除其覆盖率检查

### 测试代码规范

#### 测试函数命名

```python
# ✅ 好: 清晰的命名
def test_search_returns_notes_list():
    """搜索应返回笔记列表。"""
    pass

def test_search_with_empty_results():
    """搜索无结果时应返回空列表。"""
    pass

def test_search_raises_on_session_expired():
    """搜索时 Session 过期应抛出异常。"""
    pass

# ❌ 不好: 名字含糊
def test_search():
    pass

def test_1():
    pass
```

#### Fixture 使用

```python
# conftest.py
import pytest
from xhs_cli.cookies import Cookies

@pytest.fixture
def mock_cookies():
    """返回测试 Cookie。"""
    return {"a1": "test_value"}

@pytest.fixture
def client(mock_cookies):
    """返回客户端实例。"""
    from xhs_cli.client import XhsClient
    return XhsClient(mock_cookies)

# test_client.py
def test_search(client):
    """使用 Fixture 中的客户端。"""
    result = client.search("test")
    assert isinstance(result, dict)
```

#### Mock 与 Patch

```python
# ❌ 不好: 调用真实 API
def test_search():
    client = XhsClient(real_cookies)
    result = client.search("keyword")  # 真实网络请求
    assert result

# ✅ 好: Mock 网络请求
from unittest.mock import patch, MagicMock

def test_search():
    mock_response = {"success": True, "data": {"notes": []}}

    with patch.object(XhsClient, '_request_with_retry') as mock_req:
        mock_req.return_value = MagicMock(status_code=200, text=json.dumps(mock_response))

        client = XhsClient({"a1": "test"})
        result = client.search("keyword")
        assert result == []
```

---

## 禁止模式

### ❌ 1. 硬编码 API Host

```python
# ❌ 禁止: 硬编码 Host
response = requests.post("https://edith.xiaohongshu.com/api/v1/note/feed", json=data)

# ✅ 使用常量
from .constants import EDITH_HOST

response = requests.post(f"{EDITH_HOST}/api/v1/note/feed", json=data)
```

**原因**: API Host 可能变更，硬编码会导致难以维护和跨多个文件修改

---

### ❌ 2. 直接修改 `_request_delay`

```python
# ❌ 禁止: 绕过反检测机制
client._request_delay = 0  # 去掉延迟
client._verify_count = 0   # 重置验证码计数

# ✅ 正确方式: 让客户端自动处理
try:
    result = client.search("keyword")
except NeedVerifyError:
    # 客户端已自动冷却
    pass
```

**原因**: 破坏反检测机制，更容易被检测为机器人，导致 IP 限制或验证码

---

### ❌ 3. 忘记处理异常

```python
# ❌ 禁止: 吞掉异常
try:
    result = client.search("keyword")
except:
    pass  # 错误被隐藏

# ✅ 至少记录异常
import logging

logger = logging.getLogger(__name__)

try:
    result = client.search("keyword")
except XhsApiError as e:
    logger.error("Search failed: %s", e)
    raise
```

**原因**: 无法调试，用户看不到实际错误

---

### ❌ 4. Cookie 直接从内存读取（无 TTL 检查）

```python
# ❌ 禁止: 不检查 Cookie 过期
def search(keyword):
    cookies = load_cookies_from_file()  # 可能已过期
    client = XhsClient(cookies)
    return client.search(keyword)

# ✅ 使用 get_cookies() 自动处理 TTL
from .cookies import get_cookies

def search(keyword):
    cookies = get_cookies()  # 自动检查 TTL 并刷新
    client = XhsClient(cookies)
    return client.search(keyword)
```

**原因**: `get_cookies()` 包含完整的 TTL 检查和浏览器刷新逻辑

---

### ❌ 5. 同步调用异步函数

```python
# ❌ 禁止: 同步代码调用异步函数
def search(keyword):
    result = client.search(keyword)  # 但如果改成异步了呢？
    return result

# ✅ 如果 API 是异步，使用 asyncio.run()
import asyncio

def search(keyword):
    result = asyncio.run(client.search(keyword))
    return result
```

**原因**: 可能导致运行时错误或死锁

---

### ❌ 6. 直接访问私有属性

```python
# ❌ 禁止: 访问私有属性（下划线开头）
def get_verify_count():
    return client._verify_count  # 私有属性，不保证稳定

# ✅ 使用公开方法或属性
# 如果需要暴露，添加公开方法
def get_verify_count():
    # 使用公开 API，或请求项目维护者添加公开方法
    pass
```

**原因**: 私有属性可能随时改变，依赖它会破坏代码

---

### ❌ 7. 没有类型注解的函数

```python
# ❌ 禁止: 缺少类型注解
def normalize_data(data):
    return {"processed": data}

# ✅ 完整类型注解
def normalize_data(data: dict[str, Any]) -> dict[str, Any]:
    return {"processed": data}
```

**原因**: 难以调试，IDE 无法提供代码补全和错误检查

---

### ❌ 8. 日志用 print() 或 f-string

```python
# ❌ 禁止: 用 print
print(f"Processing note {note_id}")

# ✅ 使用 logger
import logging

logger = logging.getLogger(__name__)
logger.info("Processing note %s", note_id)
```

**原因**: logger 支持日志级别、格式化、重定向等功能，更可控

---

### ❌ 9. 返回 raw dict，不进行规范化

```python
# ❌ 禁止: 直接返回 API 响应
def search(keyword):
    return client.search(keyword)  # raw API 数据

# ✅ 规范化数据
from .formatter_normalizers import normalize_search_results

def search(keyword):
    raw_result = client.search(keyword)
    return normalize_search_results(raw_result)
```

**原因**: 不同 API 端点的数据格式不一致，规范化确保 CLI 输出统一

---

### ❌ 10. 忘记关闭资源（HTTP 连接）

```python
# ❌ 禁止: 不关闭客户端
client = XhsClient(cookies)
result = client.search("keyword")
# 连接泄漏

# ✅ 使用 context manager
with XhsClient(cookies) as client:
    result = client.search("keyword")
# 自动关闭

# 或显式关闭
client = XhsClient(cookies)
try:
    result = client.search("keyword")
finally:
    client.close()
```

**原因**: TCP 连接限制，长期运行会导致"too many open files"错误

---

## 必须的模式

### ✅ 1. 所有文件顶部有 `from __future__ import annotations`

```python
# ✅ 强制
from __future__ import annotations

# 允许使用类本身作为类型
class XhsClient:
    def get_note(self) -> XhsClient | None:
        pass
```

---

### ✅ 2. 结构化错误输出（命令层）

```python
# ✅ 强制
from .formatter import success_payload, error_payload, maybe_print_structured
from .error_codes import error_code_for_exception

try:
    result = client.search("keyword")
    maybe_print_structured(success_payload(result))
except XhsApiError as e:
    error_code = error_code_for_exception(e)
    maybe_print_structured(
        error_payload(error_code, str(e)),
        as_json=as_json,
        as_yaml=as_yaml
    )
```

---

### ✅ 3. 使用 logger 记录重要信息

```python
# ✅ 强制
import logging

logger = logging.getLogger(__name__)

logger.debug("Request details: %s", request)
logger.info("Searching for: %s", keyword)
logger.warning("Captcha triggered, cooling down")
logger.error("API error: %s", e)
```

---

### ✅ 4. 数据规范化

```python
# ✅ 强制: 命令层必须规范化数据
from .formatter_normalizers import normalize_note

def read_command(note_id):
    raw = client.get_note_feed(note_id)
    normalized = normalize_note(raw)
    output_context(normalized)
```

---

### ✅ 5. 异常处理的上下游

```python
# ✅ 强制: 客户端层抛出异常，命令层捕获并输出
# xhs_cli/client.py
class XhsClient:
    def search(self, keyword):
        if error:
            raise NeedVerifyError(...)  # 抛出异常

# xhs_cli/commands/reading.py
@click.command()
def search(keyword):
    try:
        result = client.search(keyword)
    except NeedVerifyError as e:
        output_context(error_payload("verification_required", str(e)))
```

---

## 代码审查清单

### 提交前检查

- [ ] **Lint 通过** — `uv run ruff check xhs_cli/ tests/` 零错误
- [ ] **格式化通过** — 运行 `uv run ruff format xhs_cli/` 确保格式一致
- [ ] **类型检查通过** — `uv run mypy xhs_cli/` 零错误
- [ ] **测试通过** — `uv run pytest tests/ -m "not smoke"` 全部 PASS
- [ ] **覆盖率达标** — 新增代码覆盖率 ≥ 80%

### 代码审查要点

- [ ] **异常处理** — 有异常处理，且使用具体异常类型而非 `Exception`
- [ ] **类型注解** — 所有函数参数和返回值都有类型注解
- [ ] **日志** — 关键操作都有 logger 记录（不用 print）
- [ ] **文档** — 公开 API 有 docstring（至少一句话描述）
- [ ] **测试** — 新增功能有对应的单元测试
- [ ] **资源管理** — HTTP 连接、文件等都正确关闭（context manager 或 try-finally）
- [ ] **命名** — 变量名清晰，不用单字母（除了循环变量）
- [ ] **无硬编码** — API Host、常量等都用 `constants.py` 中定义的值
- [ ] **数据规范化** — 命令层对 API 响应进行规范化
- [ ] **结构化输出** — CLI 命令输出使用 YAML/JSON 信封格式

### 常见代码审查注释

| 问题 | 改进方案 |
|------|---------|
| "This function is too long" | 拆分为多个小函数，每个函数单一职责 |
| "Missing type hints" | 添加函数参数和返回值的类型注解 |
| "This logic is duplicated" | 提取为通用函数（见 formatter_normalizers.py） |
| "No error handling" | 添加 try-except 并区分异常类型 |
| "Missing tests" | 添加单元测试覆盖新增代码 |
| "Hardcoded value" | 移到 constants.py |
| "Using print()" | 改用 logger 或 click.echo() |

---

## 完整检查流程

### 开发完成后

```bash
# 1. 自动格式化
uv run ruff format xhs_cli/ tests/

# 2. Lint 检查
uv run ruff check xhs_cli/ tests/

# 3. 类型检查
uv run mypy xhs_cli/

# 4. 运行测试
uv run pytest tests/ -m "not smoke" -v

# 5. 检查覆盖率
uv run pytest tests/ -m "not smoke" --cov=xhs_cli --cov-report=term-missing

# 所有通过后，提交
git add xhs_cli/ tests/
git commit -m "feat(module): description"
```

### 完整检查脚本

```bash
#!/bin/bash
set -e  # 任何命令失败都中止

echo "🔍 Running Ruff format..."
uv run ruff format xhs_cli/ tests/

echo "✅ Ruff format complete"
echo ""

echo "🔍 Running Ruff check..."
uv run ruff check xhs_cli/ tests/

echo "✅ Ruff check complete"
echo ""

echo "🔍 Running mypy..."
uv run mypy xhs_cli/

echo "✅ mypy check complete"
echo ""

echo "🔍 Running pytest..."
uv run pytest tests/ -m "not smoke" -v

echo "✅ All tests passed"
echo ""

echo "✨ All checks passed!"
```

保存为 `.pre-commit-hook` 或在 CI/CD 中使用。

---

## 总结表

| 检查工具 | 命令 | 失败时 | 修复 |
|---------|------|--------|------|
| **Ruff** | `ruff check` | E/F/I/B/UP 错误 | `ruff format` |
| **mypy** | `mypy xhs_cli/` | 类型不匹配 | 手动添加类型注解 |
| **pytest** | `pytest tests/` | 测试失败 | 修复代码或测试 |
| **Coverage** | `--cov=xhs_cli` | 覆盖率 <80% | 添加单元测试 |

