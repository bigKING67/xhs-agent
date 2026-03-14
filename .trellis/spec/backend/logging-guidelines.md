# Logging Guidelines

> How logging is done in this project.

---

## Overview

xiaohongshu-cli 使用**标准 Python `logging` 模块**，分为 4 个日志级别：

- **DEBUG** — 详细的诊断信息（用于开发调试）
- **INFO** — 重要的业务事件（API 备用、流程切换）
- **WARNING** — 可恢复的问题（验证码、重试、超时）
- **ERROR** — 严重问题，程序可能无法继续

**启用 DEBUG 日志**：
```bash
xhs --verbose search "keyword"  # -v 或 --verbose flag
```

---

## 日志库与初始化

### 使用标准库 `logging`

```python
import logging

logger = logging.getLogger(__name__)  # 使用模块名作为 logger 名称
```

**规则**：
- 每个模块顶部都应有 `logger = logging.getLogger(__name__)`
- 不要创建全局 logger，使用 `__name__` 让 logger 具有模块层级
- 不要 hardcode logger 名称

**为什么**：
- `logging.getLogger(__name__)` 返回以模块名命名的 logger（如 `xhs_cli.client`）
- 支持按模块设置日志级别（如只看 `xhs_cli.client` 的日志）
- 便于调试和日志统计

### CLI 中启用详细日志

**位置**: `xhs_cli/cli.py`

```python
@click.group()
@click.option('-v', '--verbose', is_flag=True, help='Enable DEBUG logging')
def cli(verbose):
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
```

---

## 日志级别与使用场景

### DEBUG — 诊断信息（最详细）

**何时使用**：
- 函数入口和参数值
- HTTP 请求/响应细节
- 缓存操作（读取、写入、命中）
- 内部状态变化
- 多步骤流程的中间结果

**特点**：
- 只有在 `--verbose` 时才输出
- 可以包含大量数据（URL、响应体等）
- 用于开发调试

**示例**：

```python
# client.py
logger.debug("GET %s", url)  # 请求 URL
logger.debug("Rate-limit delay: %.2fs", sleep_time)  # 延迟时间
logger.debug("Response headers: %s", resp.headers)  # 响应头

# cookies.py
logger.debug("Loaded saved cookies from %s", cookie_path)  # 缓存读取
logger.debug("Cached xsec_token for note %s", note_id)  # Token 缓存
logger.debug("Cookie extraction subprocess failed: %s", result.stderr)  # 进程错误
```

**格式规范**：
```python
# ✅ 好: 使用百分号格式化，便于日志系统过滤
logger.debug("Processing note %s with delay %.2fs", note_id, delay)

# ❌ 不好: f-string（日志系统无法灵活处理）
logger.debug(f"Processing note {note_id} with delay {delay:.2f}s")

# ❌ 不好: 直接字符串拼接
logger.debug("Processing note " + str(note_id))
```

---

### INFO — 重要业务事件

**何时使用**：
- API 调用的决策点（使用备用方案、切换 API）
- Cookie/Token 的管理操作（刷新、过期）
- 登录流程的关键步骤
- 一次性操作（如首次初始化）

**特点**：
- 总是输出（除非日志级别调到 WARNING）
- 简洁，只记录决策和结果
- 用于运营监控和审计

**示例**：

```python
# cookies.py
logger.info(
    "Cookies older than %d days, attempting browser refresh",
    COOKIE_TTL_DAYS,
)  # Cookie 过期时尝试刷新

# client_mixins.py
logger.info("Feed API failed (%s), falling back to HTML", exc)  # 使用备用方案

# qr_login.py
logger.info("Browser-assisted QR login unavailable, falling back to HTTP flow: %s", exc)
```

**何时不用 INFO**：
- 每个请求的细节（用 DEBUG）
- 临时变量值（用 DEBUG）
- 经常发生的事件（用 DEBUG）

---

### WARNING — 可恢复的异常情况

**何时使用**：
- 重试（HTTP 错误、网络超时）
- 验证码触发与冷却
- 性能问题（请求超时、缓存失败）
- API 返回异常状态码但能继续

**特点**：
- 表示有问题但程序可以继续
- 可能需要用户注意，但不是致命错误
- 用于问题诊断和告警

**示例**：

```python
# client.py - 重试
logger.warning(
    "HTTP %d from %s, retrying in %.1fs (attempt %d/%d)",
    resp.status_code, url[:80], wait, attempt + 1, self._max_retries,
)

# client.py - 验证码
logger.warning(
    "Captcha triggered (count=%d), cooling down %.0fs before raising",
    self._verify_count, cooldown,
)

# client.py - 网络错误
logger.warning(
    "Network error: %s, retrying in %.1fs (attempt %d/%d)",
    exc, wait, attempt + 1, self._max_retries,
)
```

**何时不用 WARNING**：
- 一切正常的事件（用 INFO 或 DEBUG）
- 用户输入错误（这是 Exception，用 ERROR）
- 临时调试信息（用 DEBUG）

---

### ERROR — 严重错误（最严重）

**何时使用**：
- 函数无法继续执行，必须抛出异常
- 数据校验失败（无法恢复）
- 系统配置错误
- 内部逻辑错误（代码 bug）

**特点**：
- 表示程序流被中断
- 通常伴随 Exception 抛出
- 用于问题告警和日志监控

**当前项目状态**：
- 代码中很少有 ERROR 级日志
- 大多数错误通过异常处理而非日志
- 建议保留给真正的内部错误

**建议用法**：

```python
# ✅ 推荐: 记录异常并抛出
try:
    data = json.loads(response_text)
except json.JSONDecodeError as e:
    logger.error("Failed to parse JSON response: %s", e)
    raise XhsApiError("Invalid API response") from e

# ✅ 推荐: 记录配置错误
if not config_dir.exists():
    logger.error("Config directory does not exist: %s", config_dir)
    raise SystemError(f"Config directory not found: {config_dir}")
```

**何时不用 ERROR**：
- 预期的异常（如 SessionExpiredError）— 不记录，通过异常处理
- 用户错误（输入验证失败）— 输出到 CLI，不记录
- API 返回业务错误（如"笔记不存在"）— 通过异常处理，不记录

---

## 日志格式

### 默认格式（Python logging 默认）

```
DEBUG:xhs_cli.client:GET https://edith.xiaohongshu.com/api/note/feed
WARNING:xhs_cli.client:Captcha triggered (count=1), cooling down 5s before raising
INFO:xhs_cli.cookies:Cookies older than 7 days, attempting browser refresh
```

**组成**：
```
<LEVEL>:<logger_name>:<message>
```

### 自定义格式（如果配置）

xiaohongshu-cli 当前使用默认格式，不做自定义。如需扩展，遵循规则：

```python
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
```

---

## 日志内容规范

### ✅ 应该记录什么

#### 1. 请求相关信息
```python
# ✅ 好: URL（不含敏感参数）
logger.debug("GET %s", url)

# ❌ 不好: 完整 URL 可能含 token
logger.debug("GET %s", full_url_with_token)
```

#### 2. 重试和冷却
```python
# ✅ 好: 清晰的重试信息
logger.warning("HTTP %d, retrying in %.1fs (attempt %d/%d)", status, wait, attempt, max_retries)
```

#### 3. 缓存命中/未命中
```python
# ✅ 好: 缓存操作
logger.debug("Loaded saved cookies from %s", cookie_path)
logger.debug("Cached xsec_token for note %s", note_id)
```

#### 4. API 备用和降级
```python
# ✅ 好: 记录降级决策
logger.info("Feed API failed (%s), falling back to HTML", exc)
```

#### 5. Cookie 和认证
```python
# ✅ 好: Cookie 生命周期事件
logger.info("Cookies older than 7 days, attempting browser refresh")
logger.debug("Cookie extraction timed out")
```

---

### ❌ 不应该记录什么

#### 1. **Cookie 值、Token、用户凭证**
```python
# ❌ 禁止: 记录完整 Cookie
logger.debug("Cookies: %s", cookies)

# ❌ 禁止: 记录 Token
logger.debug("xsec_token: %s", token)

# ✅ 好: 只记录 key 或长度
logger.debug("Loaded %d cookies", len(cookies))
logger.debug("Cached xsec_token for note %s", note_id)  # note_id 是公开的
```

#### 2. **用户数据和笔记内容**
```python
# ❌ 禁止: 记录笔记完整内容
logger.debug("Note data: %s", note_data)

# ✅ 好: 只记录 metadata
logger.debug("Processing note %s (title_length=%d)", note_id, len(title))
```

#### 3. **完整 API 响应体**
```python
# ❌ 禁止: 记录完整响应
logger.debug("API response: %s", response_text)

# ✅ 好: 只记录关键信息
logger.debug("API returned %d notes", len(notes))
```

#### 4. **个人身份信息 (PII)**
```python
# ❌ 禁止: 记录用户名、手机号、邮箱
logger.debug("User logged in: %s", user_email)

# ✅ 好: 只记录用户 ID
logger.debug("User %s logged in", user_id)
```

#### 5. **系统敏感信息**
```python
# ❌ 禁止: 记录完整路径、配置值
logger.debug("Config file: /Users/myname/.xiaohongshu-cli/cookies.json")

# ✅ 好: 只记录相对路径或变量名
logger.debug("Config loaded from %s", config_dir / "cookies.json")
```

---

## 常见日志模式

### 模式 1: 函数入口与返回

```python
# DEBUG 级别记录入口和参数
def search(keyword: str, page: int = 1) -> dict:
    logger.debug("search() called with keyword=%r, page=%d", keyword, page)

    try:
        result = client.search(keyword, page=page)
        logger.debug("search() returned %d results", len(result.get("notes", [])))
        return result
    except XhsApiError as e:
        logger.warning("Search failed: %s", e)
        raise
```

### 模式 2: 重试循环

```python
for attempt in range(max_retries):
    try:
        resp = self._http.request(method, url, **kwargs)
        if resp.status_code in (429, 500, 502, 503, 504):
            wait = (2 ** attempt) + random.uniform(0, 1)
            logger.warning(
                "HTTP %d from %s, retrying in %.1fs (attempt %d/%d)",
                resp.status_code, url[:80], wait, attempt + 1, max_retries,
            )
            time.sleep(wait)
            continue
        return resp
    except (httpx.TimeoutException, httpx.NetworkError) as exc:
        wait = (2 ** attempt) + random.uniform(0, 1)
        logger.warning(
            "Network error: %s, retrying in %.1fs (attempt %d/%d)",
            exc, wait, attempt + 1, max_retries,
        )
        time.sleep(wait)
```

### 模式 3: 流程切换（降级）

```python
try:
    # 主路径
    result = client.get_feed()
    logger.debug("Feed API succeeded")
    return result
except XhsApiError as e:
    # 备用路径
    logger.info("Feed API failed (%s), falling back to HTML", e)
    result = client.get_feed_via_html()
    return result
```

### 模式 4: 缓存操作

```python
def get_cached_token(note_id: str) -> str | None:
    token = _load_from_cache(note_id)

    if token:
        logger.debug("Token cache hit for note %s", note_id)
        return token
    else:
        logger.debug("Token cache miss for note %s", note_id)
        return None

def cache_token(note_id: str, token: str) -> None:
    _save_to_cache(note_id, token)
    logger.debug("Cached xsec_token for note %s", note_id)
```

### 模式 5: 认证和权限

```python
def get_cookies() -> dict[str, str]:
    try:
        cookies = _load_from_file()
        if _is_expired(cookies):
            logger.info("Cookies expired, attempting browser refresh")
            cookies = _refresh_from_browser()
            logger.info("Cookies refreshed successfully")
        else:
            logger.debug("Using cached cookies")
        return cookies
    except NoCookieError as e:
        logger.warning("No valid cookies found: %s", e)
        raise
```

---

## 日志调试技巧

### 查看特定模块的日志

```bash
# 只显示 client 模块的日志
xhs --verbose search "keyword" 2>&1 | grep "xhs_cli.client"

# 只显示 DEBUG 及以上的日志
xhs --verbose search "keyword" 2>&1 | grep "DEBUG"
```

### 在本地调试时启用详细日志

```python
import logging

# 在脚本顶部设置
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 现在所有日志都会输出
client.search("keyword")
```

### 过滤特定日志

```bash
# 只看警告和错误
xhs search "keyword" 2>&1 | grep -E "WARNING|ERROR"

# 排除某些模块的日志
xhs --verbose search "keyword" 2>&1 | grep -v "browser_cookie3"
```

---

## 常见错误与改进

### ❌ 错误做法

#### 1. 使用 print() 而非 logger
```python
# ❌ 不好
print(f"Processing note {note_id}")

# ✅ 好
logger.debug("Processing note %s", note_id)
```

**原因**: print() 无法控制日志级别、格式化、重定向等

#### 2. 在异常处理中忘记记录
```python
# ❌ 不好
try:
    result = client.search("keyword")
except XhsApiError:
    return None  # 错误被吞掉了

# ✅ 好
try:
    result = client.search("keyword")
except XhsApiError as e:
    logger.warning("Search failed: %s", e)
    return None
```

**原因**: 无法调试，用户看不到实际错误

#### 3. 记录太多敏感数据
```python
# ❌ 不好
logger.debug("Full response: %s", response_dict)  # 可能含 token

# ✅ 好
logger.debug("Response contains %d items", len(response_dict.get("items", [])))
```

**原因**: 日志可能被存储、分析、分享，敏感数据泄露风险

#### 4. 使用 f-string 而非参数化格式
```python
# ❌ 不好: 日志系统无法处理
logger.debug(f"User {user_id} performed action {action}")

# ✅ 好: 日志系统可以解析和过滤
logger.debug("User %s performed action %s", user_id, action)
```

**原因**: 日志系统可以基于字段进行统计和搜索

#### 5. 记录完整异常堆栈
```python
# ❌ 不好: 冗余
logger.error("Error: %s", traceback.format_exc())

# ✅ 好: 使用 exc_info 参数
logger.error("Operation failed", exc_info=True)
```

**原因**: 不需要手动格式化，logging 会自动处理

---

## 日志最佳实践总结

| 场景 | 级别 | 例子 |
|------|------|------|
| 程序启动、初始化 | INFO | "Initializing client" |
| API 调用、URL 请求 | DEBUG | "GET /api/note/feed" |
| 缓存命中/未命中 | DEBUG | "Cache hit for note X" |
| 重试、备用方案 | WARNING | "HTTP 500, retrying" |
| Cookie 过期、刷新 | INFO | "Cookies expired, refreshing" |
| 验证码触发 | WARNING | "Captcha triggered, cooling down" |
| 异常（可恢复） | WARNING | "API error, using fallback" |
| 异常（不可恢复） | ERROR | "Config file not found" |

---

## 运营与监控

### 日志监控指标

**收集这些**：
- WARNING 及以上的日志（问题告警）
- "Captcha triggered" — 频繁验证码表示可能被检测
- "Cookies expired" — Cookie 寿命监控
- 重试次数分布 — 网络稳定性指标

**监控告警**：
```bash
# 告警: 出现 ERROR 级日志
if grep -q "ERROR" logs/xhs_cli.log; then
    send_alert("XHS CLI error detected")
fi

# 告警: 验证码频繁触发
error_count=$(grep -c "Captcha triggered" logs/xhs_cli.log | tail -1)
if [ $error_count -gt 10 ]; then
    send_alert("Too many captchas: $error_count")
fi
```

### 日志轮转

建议配置日志轮转避免日志文件过大：

```python
import logging.handlers

handler = logging.handlers.RotatingFileHandler(
    'xhs_cli.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
logging.getLogger().addHandler(handler)
```

