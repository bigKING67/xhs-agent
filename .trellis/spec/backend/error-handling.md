# Error Handling

> How errors are handled in this project.

---

## Overview

xiaohongshu-cli 使用**分层异常体系 + 自动重试 + 冷却机制**，处理网络错误、API 错误、验证码等场景。

**核心原则**：
1. **自定义异常优先** — 7 个 domain-specific 异常类
2. **错误码映射** — 不同错误类型映射到稳定的 error code（用于结构化输出）
3. **自动冷却** — 验证码触发时自动等待（5→10→20→30秒）
4. **指数退避** — 网络/API 错误时自动重试
5. **速率限制** — 所有请求前自动插入延迟（Gaussian 分布 + 5% 长暂停）

---

## 异常体系

### 异常类定义

所有异常继承自 `XhsApiError`（基类）。位置: `xhs_cli/exceptions.py`

#### 1. **NeedVerifyError** — 验证码触发
```python
raise NeedVerifyError(verify_type="sms", verify_uuid="abc-123")
```

**触发条件**：
- HTTP 状态码 461 或 471（验证码 API 响应）

**属性**：
- `verify_type: str` — 验证码类型（如 "sms", "geetest" 等）
- `verify_uuid: str` — 验证码 UUID（用于 Web 端验证）

**处理流程**：
```
第1次触发 → 等待 5秒 → request_delay 加倍 → 抛出异常
第2次触发 → 等待 10秒 → request_delay 继续增大
第3次触发 → 等待 20秒
第4次+   → 等待 30秒（上限）
```

冷却公式: `cooldown = min(30, 5 * (2 ** (verify_count - 1)))`

**推荐处理**：
```python
from xhs_cli.exceptions import NeedVerifyError

try:
    results = client.search("keyword")
except NeedVerifyError as e:
    print(f"Captcha required: {e.verify_type}")
    print(f"Complete at: https://www.xiaohongshu.com/")
    print(f"UUID: {e.verify_uuid}")
    # 客户端自动冷却，稍后重试即可
```

---

#### 2. **SessionExpiredError** — 登录过期
```python
raise SessionExpiredError()
```

**触发条件**：
- API 返回错误码 `-100`（小红书 API 的标准过期码）

**属性**：
- `code: int` = `-100`
- 包含恢复指令的完整错误信息

**原因**：
- Cookie 过期（默认 7 天）
- Cookie 被服务器撤销
- 用户在其他设备登录导致会话冲突

**推荐处理**：
```python
from xhs_cli.exceptions import SessionExpiredError

try:
    results = client.search("keyword")
except SessionExpiredError:
    print("Session expired. Please re-login with: xhs login")
    # 用户必须重新运行 xhs login 刷新 Cookie
```

**自动恢复机制**（在 `cookies.py` 中）：
```
1. 每次 API 调用前检查 Cookie TTL
2. 如果距过期 < 24 小时，尝试从浏览器刷新
3. 浏览器刷新失败时，警告用户但继续使用旧 Cookie
4. 如果 API 返回 -100，清除本地 Cookie 并提示重新登录
```

---

#### 3. **IpBlockedError** — IP 被限制
```python
raise IpBlockedError()
```

**触发条件**：
- API 返回错误码 `300012`（小红书 IP 限制响应）

**原因**：
- IP 地址被检测为机器人
- 短时间内发送过多请求
- IP 所在地被小红书限制

**推荐处理**：
```python
from xhs_cli.exceptions import IpBlockedError

try:
    results = client.search("keyword")
except IpBlockedError:
    print("IP blocked by XHS. Options:")
    print("  1. Try a different network (mobile hotspot, VPN)")
    print("  2. Wait a few hours")
    print("  3. Use a different IP address")
    # 不应该自动重试，等待是最好的方式
```

---

#### 4. **SignatureError** — 签名校验失败
```python
raise SignatureError()
```

**触发条件**：
- API 返回错误码 `300015`（签名验证失败）

**原因**：
- 签名库 `xhshow` 过期（小红书改变了签名算法）
- Cookie 与签名不一致（跨会话使用旧 Cookie）
- 系统时间与小红书服务器时间相差过大（>5分钟）

**推荐处理**：
```python
from xhs_cli.exceptions import SignatureError

try:
    results = client.search("keyword")
except SignatureError:
    print("Signature verification failed. Options:")
    print("  1. Check system time (should be accurate to within 5 minutes)")
    print("  2. Update xhshow library: uv sync")
    print("  3. Re-login: xhs login")
    # 通常需要更新依赖或刷新 Cookie
```

---

#### 5. **NoCookieError** — 无有效 Cookie
```python
raise NoCookieError(source="auto", details="...")
```

**触发条件**：
- `xhs login` 时未找到 `a1` cookie（登录标志）
- 所有支持的浏览器中都找不到 cookie

**属性**：
- `source: str` — 浏览器名称（"auto" 表示尝试全部浏览器）
- `details: str` — 额外诊断信息

**错误信息包含完整的故障排查步骤**：
1. 打开浏览器访问 xiaohongshu.com
2. 确保已登录
3. 运行 `xhs login --cookie-source <browser>`

**推荐处理**：
```python
from xhs_cli.exceptions import NoCookieError

try:
    cookies = get_cookies()
except NoCookieError as e:
    print(str(e))  # 异常消息已包含完整指导
    # 用户需要手动在浏览器中登录后重试
```

---

#### 6. **UnsupportedOperationError** — API 不再支持
```python
raise UnsupportedOperationError("Direct message API has been removed by XHS")
```

**触发条件**：
- 小红书更新了 API，某个端点不再存在或改变了返回格式
- CLI 功能调用了已弃用的 API

**原因**：
- 小红书平台更新
- 逆向工程的 API 合约变更
- 官方禁用了某些功能

**推荐处理**：
```python
from xhs_cli.exceptions import UnsupportedOperationError

try:
    result = client.some_operation()
except UnsupportedOperationError as e:
    print(f"Feature no longer supported: {e}")
    print("Please check https://github.com/jackwener/xiaohongshu-cli/issues")
    # 需要项目维护者更新
```

---

#### 7. **XhsApiError** — 通用 API 错误（基类）
```python
raise XhsApiError(
    "API error: server returned invalid response",
    code=500,
    response={"error": "..."}
)
```

**用途**：
- 捕获所有其他 API 错误
- 无法分类的响应错误
- 未定义的错误码

**属性**：
- `message: str` — 错误消息
- `code: int | str | None` — API 错误码
- `response: dict | None` — 完整 API 响应

**触发条件**：
- API 返回 `success: false`（小红书 API 的标准失败格式）
- 任何 JSON 解析失败

---

### 异常处理流程图

```
HTTP Request
    ↓
[Rate Limit Delay]  ← Gaussian 延迟 + 5% 长暂停
    ↓
[Retry Loop] (最多 3 次)
    ├─ HTTP 429/5xx → 指数退避 (2^attempt + random[0,1])
    ├─ Network Error → 指数退避
    └─ Success → 继续处理响应
    ↓
[Response Handler]
    ├─ HTTP 461/471 (验证码)
    │  └─ verify_count += 1
    │  └─ cooldown = min(30, 5 * 2^(verify_count-1))
    │  └─ sleep(cooldown)
    │  └─ request_delay *= 2  ← 之后所有请求都会延迟加倍
    │  └─ raise NeedVerifyError
    │
    ├─ success: true → 返回 data
    │
    └─ success: false
       ├─ code -100 → raise SessionExpiredError
       ├─ code 300012 → raise IpBlockedError
       ├─ code 300015 → raise SignatureError
       └─ other → raise XhsApiError
```

---

## 错误码映射

位置: `xhs_cli/error_codes.py`

**转换表** — 异常类型 → 结构化错误码（用于 CLI 输出）：

| 异常类型 | 错误码 | 含义 | HTTP 状态 |
|---------|--------|------|----------|
| `NoCookieError` | `not_authenticated` | 未登录 | N/A |
| `SessionExpiredError` | `not_authenticated` | 登录过期 | -100 |
| `NeedVerifyError` | `verification_required` | 需要验证码 | 461/471 |
| `IpBlockedError` | `ip_blocked` | IP 被限制 | 300012 |
| `SignatureError` | `signature_error` | 签名失败 | 300015 |
| `UnsupportedOperationError` | `unsupported_operation` | 不支持 | N/A |
| `XhsApiError` (其他) | `api_error` | 通用 API 错误 | 其他 |

**转换函数**：
```python
from xhs_cli.error_codes import error_code_for_exception

try:
    result = client.search("keyword")
except Exception as e:
    code = error_code_for_exception(e)
    # code 现在是稳定的、易于序列化的标识符
```

**CLI 输出示例**：
```yaml
ok: false
schema_version: "1"
error:
  code: verification_required
  message: "Captcha required: type=sms, uuid=abc-123"
```

---

## 重试与恢复机制

### 1. HTTP 错误重试（指数退避）

**触发条件**：
- HTTP 状态码 429 (Too Many Requests)
- HTTP 状态码 5xx (Server Error: 500, 502, 503, 504)
- 网络超时或连接错误

**重试配置**：
```python
# client.py - _request_with_retry()
for attempt in range(self._max_retries):  # 最多 3 次
    try:
        resp = self._http.request(...)
        if resp.status_code in (429, 500, 502, 503, 504):
            wait = (2 ** attempt) + random.uniform(0, 1)
            # attempt=0 → wait=1-2秒
            # attempt=1 → wait=2-3秒
            # attempt=2 → wait=4-5秒
            time.sleep(wait)
            continue
        return resp
    except (httpx.TimeoutException, httpx.NetworkError):
        # 同样的指数退避
        wait = (2 ** attempt) + random.uniform(0, 1)
        time.sleep(wait)
```

**不重试的情况**：
- 4xx 错误（客户端错误，重试无益）
- 验证码触发（需要人工干预）
- 签名失败（需要更新签名库）

---

### 2. 验证码冷却（自适应延迟）

**机制**：
- 首次触发: 冷却 5 秒
- 第二次触发: 冷却 10 秒
- 第三次触发: 冷却 20 秒
- 第四次及以后: 冷却 30 秒（上限）

**副作用**：
- 验证码触发后，`request_delay` 永久翻倍
- 所有后续请求都会使用加倍延迟（直到进程重启）

**代码**：
```python
# client.py - _handle_response()
if resp.status_code in (461, 471):
    self._verify_count += 1
    cooldown = min(30, 5 * (2 ** (self._verify_count - 1)))
    logger.warning("Captcha triggered, cooling down %.0fs", cooldown)
    self._request_delay = max(self._request_delay, self._base_request_delay * 2)
    time.sleep(cooldown)
    raise NeedVerifyError(...)
```

---

### 3. 速率限制延迟（反检测）

**目的**：
- 模拟人类浏览行为
- 避免被识别为机器人
- 规避频率限制

**延迟策略**：
```python
# client.py - _rate_limit_delay()
base_delay = self._request_delay  # 默认 1.0 秒

# 95% 请求: 正态分布延迟
jitter = max(0, random.gauss(0.3, 0.15))  # μ=0.3, σ=0.15
sleep_time = base_delay - elapsed + jitter

# 5% 请求: 额外长暂停
if random.random() < 0.05:
    jitter += random.uniform(2.0, 5.0)  # 追加 2-5 秒
    sleep_time += jitter
```

**效果**：
- 95% 请求: ~1.15秒（带高斯抖动）
- 5% 请求: ~3-6秒（长暂停，模拟用户阅读）

**可配置**：
```python
# 创建客户端时指定延迟
client = XhsClient(cookies, request_delay=0.5)  # 更快
client = XhsClient(cookies, request_delay=0)    # 无延迟（不推荐）
```

---

### 4. Cookie 过期恢复

**自动刷新流程** (在 `cookies.py` 中)：
```
每次 API 调用前:
  1. 检查 cookie.json TTL
  2. 如果 TTL - now < 24小时:
     ├─ 尝试从浏览器提取新 Cookie
     ├─ 成功 → 更新 cookies.json
     └─ 失败 → 警告用户但继续使用旧 Cookie
```

**强制刷新触发**：
- API 返回错误码 -100 (SessionExpiredError)
- 清除本地 `~/.xiaohongshu-cli/cookies.json`
- 提示用户: "Please re-login with: xhs login"

**手动刷新**：
```bash
xhs login  # 重新提取 Cookie
```

---

## API 错误响应格式

### 成功响应
```yaml
ok: true
schema_version: "1"
data:
  # 具体数据（取决于命令）
  notes:
    - id: "..."
      title: "..."
  user:
    id: "..."
    name: "..."
```

### 错误响应（标准格式）
```yaml
ok: false
schema_version: "1"
error:
  code: "error_code"       # 稳定的错误码（见错误码映射表）
  message: "Human readable message"
```

### 错误响应示例

**验证码触发**：
```yaml
ok: false
schema_version: "1"
error:
  code: verification_required
  message: "Captcha required: type=sms, uuid=abc-123-def"
```

**登录过期**：
```yaml
ok: false
schema_version: "1"
error:
  code: not_authenticated
  message: "Session expired — please re-login with: xhs login"
```

**IP 被限制**：
```yaml
ok: false
schema_version: "1"
error:
  code: ip_blocked
  message: "IP blocked by XHS — try a different network"
```

---

## 常见错误处理模式

### 模式 1: 简单错误处理（在 CLI 命令中）

```python
# commands/reading.py
from xhs_cli.exceptions import XhsApiError
from xhs_cli.error_codes import error_code_for_exception

@click.command()
def search(keyword):
    try:
        client = get_client()
        results = client.search(keyword)
        # 处理结果...
    except XhsApiError as e:
        error_code = error_code_for_exception(e)
        output_context(
            {"ok": False, "error": {"code": error_code, "message": str(e)}}
        )
```

### 模式 2: 区分不同错误并采取行动

```python
from xhs_cli.exceptions import (
    SessionExpiredError, NeedVerifyError, IpBlockedError
)

try:
    results = client.search("keyword")
except SessionExpiredError:
    # 提示重新登录
    click.echo("Please re-login: xhs login")
except NeedVerifyError as e:
    # 记录验证码信息
    click.echo(f"Captcha required: {e.verify_type}")
except IpBlockedError:
    # 建议切换网络
    click.echo("Try a different network")
except XhsApiError as e:
    # 通用错误处理
    click.echo(f"Error: {e}")
```

### 模式 3: 重试（对于临时故障）

```python
import time
from xhs_cli.exceptions import XhsApiError

def search_with_retry(keyword, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            return client.search(keyword)
        except (TimeoutError, ConnectionError) as e:
            if attempt < max_attempts - 1:
                wait = (2 ** attempt)
                click.echo(f"Retry in {wait}s...")
                time.sleep(wait)
            else:
                raise
```

---

## 常见错误与调试

### ❌ 错误做法

#### 1. 吞掉异常（catch all without re-raising）
```python
# ❌ 不好: 错误被隐藏
try:
    result = client.search("keyword")
except Exception:
    print("Something went wrong")
    return None
```

**问题**: 用户无法看到具体错误，无法调试

**改进**:
```python
# ✅ 好: 记录并重新抛出
try:
    result = client.search("keyword")
except XhsApiError as e:
    logger.error("Search failed: %s", e)
    raise  # 或者返回具体的错误信息
```

---

#### 2. 不处理不同的异常类型
```python
# ❌ 不好: 所有错误同样处理
try:
    result = client.search("keyword")
except XhsApiError:
    print("Error occurred")
```

**问题**: 验证码、登录过期、IP 限制需要不同的恢复策略

**改进**:
```python
# ✅ 好: 根据异常类型采取不同行动
try:
    result = client.search("keyword")
except SessionExpiredError:
    click.echo("Session expired. Re-login with: xhs login")
except IpBlockedError:
    click.echo("IP blocked. Try different network")
except NeedVerifyError:
    click.echo(f"Captcha required. UUID: {e.verify_uuid}")
```

---

#### 3. 绕过验证码冷却（手动减少延迟）
```python
# ❌ 不好: 绕过反检测
client._request_delay = 0
client._verify_count = 0  # 重置计数

# 立即重试 → 触发更多验证码
```

**问题**: 破坏反检测机制，更容易被限制

**改进**:
```python
# ✅ 好: 让客户端自动处理
try:
    result = client.search("keyword")
except NeedVerifyError:
    # 客户端已自动冷却并增加延迟
    # 只需等待用户完成验证后重试
    pass
```

---

#### 4. 假设 API 总是返回期望的字段
```python
# ❌ 不好: KeyError 会导致程序崩溃
result = client.search("keyword")
note_id = result["notes"][0]["id"]  # 如果列表为空会报错
```

**问题**: 空结果、API 变更时程序崩溃

**改进**:
```python
# ✅ 好: 防御性编程
result = client.search("keyword")
notes = result.get("notes", [])
if notes:
    note_id = notes[0].get("id")
else:
    click.echo("No results found")
```

---

## 日志指导

### 适当的日志级别

```python
import logging

logger = logging.getLogger(__name__)

# DEBUG - 详细信息，用于诊断
logger.debug("Signature headers: %s", sign_headers)

# INFO - 常规信息，用于追踪流程
logger.info("Searching for: %s", keyword)

# WARNING - 注意但不是错误
logger.warning("Captcha triggered, cooling down %.0fs", cooldown)

# ERROR - 错误但程序继续
logger.error("API returned error: %s", response)

# CRITICAL - 严重错误，程序可能无法继续
logger.critical("Signature verification failed, aborting")
```

**启用 DEBUG 日志**：
```bash
xhs --verbose search "keyword"  # -v flag 启用 DEBUG
```

---

## 总结

| 场景 | 异常类型 | 用户操作 | 恢复方式 |
|------|---------|---------|---------|
| 需要验证码 | `NeedVerifyError` | 打开浏览器完成验证 | 客户端自动冷却 + 重试 |
| Cookie 过期 | `SessionExpiredError` | 运行 `xhs login` | 手动刷新 Cookie |
| IP 被限制 | `IpBlockedError` | 切换网络或等待 | 无自动恢复，需人工干预 |
| 签名失败 | `SignatureError` | 更新依赖或重新登录 | 更新 xhshow 库 |
| 无 Cookie | `NoCookieError` | 在浏览器中登录后重试 | 运行 `xhs login` |
| 网络错误 | `XhsApiError` (TimeoutError/NetworkError) | 重试或检查网络 | 自动重试（指数退避） |
| API 变更 | `UnsupportedOperationError` | 检查更新 | 等待项目维护者修复 |

