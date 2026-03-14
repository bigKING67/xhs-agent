# Directory Structure

> How backend code is organized in this project.

---

## Overview

xiaohongshu-cli 采用**分层 + 功能域分组**的架构：

- **传输层** (`client.py`, `client_mixins.py`, `signing.py`) — HTTP 传输、请求签名、反检测
- **会话层** (`cookies.py`, `qr_login.py`) — Cookie 管理、登录流程
- **命令层** (`commands/`) — CLI 命令实现，按功能域分 6 个子模块
- **工具层** (`formatter*.py`, `exceptions.py`, `html_parser.py`, 等) — 通用工具、格式化、错误处理

**设计原则**：
1. **单一职责** — 每个文件承担一个清晰的角色
2. **功能域隔离** — 命令按功能域分开（Auth/Reading/Interaction/Creator/Social/Notification）
3. **Mixin 模式** — 客户端功能通过 6 个 Mixin 按功能域组织
4. **工具集中** — 通用工具集中在根目录（`formatter*.py`, `exceptions.py`, 等）

---

## Directory Layout

```
xiaohongshu-cli/
├── xhs_cli/                          # 源代码包
│   ├── __init__.py                   # 包导出（导出 XhsClient）
│   ├── __main__.py                   # python -m xhs_cli 入口
│   │
│   # 传输层 — HTTP 客户端与签名
│   ├── client.py                     # XhsClient 主类（~200 行）
│   ├── client_mixins.py              # 6 个 Mixin（~600 行）
│   │   ├── ReadingEndpointsMixin     # 搜索、阅读端点
│   │   ├── InteractionEndpointsMixin # 互动端点
│   │   ├── CreatorEndpointsMixin     # 创作端点
│   │   ├── SocialEndpointsMixin      # 社交端点
│   │   ├── NotificationEndpointsMixin# 通知端点
│   │   └── AuthEndpointsMixin        # 认证端点
│   ├── signing.py                    # 主 API 签名（x-s, x-s-common, x-t）
│   ├── creator_signing.py            # 创作 API AES-128-CBC 签名
│   │
│   # 会话层 — Cookie 与登录管理
│   ├── cookies.py                    # Cookie 提取、TTL、缓存管理（~450 行）
│   ├── qr_login.py                   # 二维码登录流程（~500 行）
│   │
│   # CLI 入口
│   ├── cli.py                        # Click CLI 主程序与全局选项（~150 行）
│   │
│   # 命令层 — CLI 命令实现
│   ├── commands/
│   │   ├── __init__.py               # 命令组导出
│   │   ├── _common.py                # 共享的 CLI 工具函数（~200 行）
│   │   │   ├── output_context()      # 处理 --json/--yaml 输出
│   │   │   ├── get_xsec_token()      # 从缓存或交互获取 xsec_token
│   │   │   └── ensure_authenticated()# 检查登录状态
│   │   ├── auth.py                   # 认证命令（~200 行）
│   │   │   ├── login                 # 登录（Cookie 提取或 QR）
│   │   │   ├── status                # 检查登录状态
│   │   │   ├── logout                # 清除 Cookie
│   │   │   └── whoami                # 获取当前用户信息
│   │   ├── reading.py                # 搜索与阅读命令（~500 行）
│   │   │   ├── search                # 关键词搜索
│   │   │   ├── search_user           # 搜索用户
│   │   │   ├── topics                # 搜索话题
│   │   │   ├── feed                  # 推荐 Feed
│   │   │   ├── hot                   # 热门笔记
│   │   │   ├── read                  # 读取笔记详情
│   │   │   ├── comments              # 获取评论列表
│   │   │   ├── sub_comments          # 获取评论回复
│   │   │   ├── user                  # 获取用户主页
│   │   │   └── user_posts            # 获取用户笔记列表
│   │   ├── interactions.py           # 互动命令（~300 行）
│   │   │   ├── like                  # 点赞 / 取消点赞
│   │   │   ├── favorite              # 收藏 / 取消收藏
│   │   │   ├── comment               # 发表评论
│   │   │   ├── reply                 # 回复评论
│   │   │   └── delete_comment        # 删除评论
│   │   ├── creator.py                # 创作命令（~250 行）
│   │   │   ├── post                  # 发布图文笔记
│   │   │   ├── my_notes              # 我的笔记列表
│   │   │   └── delete                # 删除笔记
│   │   ├── social.py                 # 社交命令（~150 行）
│   │   │   ├── follow                # 关注用户
│   │   │   ├── unfollow              # 取消关注
│   │   │   └── favorites             # 我的收藏
│   │   ├── notifications.py          # 通知命令（~150 行）
│   │   │   ├── unread                # 获取未读数
│   │   │   └── notifications         # 获取通知列表
│   │   └── batch.py                  # 批量操作命令（~200 行）
│   │
│   # 工具层 — 通用工具与格式化
│   ├── constants.py                  # 常量定义（API Host, User-Agent, 等）
│   ├── exceptions.py                 # 异常类定义（7 个自定义异常）
│   ├── error_codes.py                # 错误码映射表（XHS API 错误 → 易读信息）
│   ├── formatter.py                  # 格式化导出入口（Re-export）
│   ├── formatter_utils.py            # 格式化基础工具（~200 行）
│   │   ├── console                   # Rich Console 实例
│   │   ├── success_payload()         # 生成成功响应信封
│   │   └── error_payload()           # 生成错误响应信封
│   ├── formatter_normalizers.py      # 数据规范化（~250 行）
│   │   ├── normalize_note()          # 笔记数据规范化
│   │   ├── normalize_user()          # 用户数据规范化
│   │   └── normalize_comment()       # 评论数据规范化
│   ├── formatter_renderers.py        # Rich 渲染函数（~400 行）
│   │   ├── render_note()             # 渲染单个笔记
│   │   ├── render_search_results()   # 渲染搜索结果表格
│   │   ├── render_comments()         # 渲染评论树
│   │   └── render_user_profile()     # 渲染用户主页
│   ├── html_parser.py                # HTML 解析器（~80 行）
│   │   └── parse_note_detail()       # 从 HTML 提取笔记详情
│   ├── note_refs.py                  # 笔记引用管理（~80 行）
│   │   └── NoteRef 类                # 笔记 ID/URL 解析与转换
│   ├── command_normalizers.py        # 命令级数据规范化（~70 行）
│   │   └── normalize_search_params()  # 规范化搜索参数
│   ├── input_loader.py               # 输入加载器（~200 行）
│   │   ├── load_images()             # 加载与验证图片
│   │   └── load_csv()                # 加载 CSV 批量数据
│   ├── openxhs_adapter.py            # OpenXHS 适配器（~150 行）
│   │   └── XhsApiClient 包装         # 实验性适配器
│   ├── batch_runner.py               # 批量运行器（~350 行）
│   │   ├── BatchRunner 类            # 管理批量任务队列
│   │   └── execute_batch()           # 执行批量操作
│   └── py.typed                      # PEP 561 标记（类型提示）
│
├── tests/                            # 测试套件
│   ├── conftest.py                   # pytest 配置与 fixtures
│   ├── test_signing.py               # 签名算法测试
│   ├── test_client.py                # 客户端测试
│   ├── test_cookies.py               # Cookie 管理测试
│   ├── test_formatter.py             # 格式化测试
│   ├── test_cli.py                   # CLI 命令测试
│   ├── test_anti_detection.py        # 反检测测试
│   ├── test_creator_signing.py       # 创作签名测试
│   ├── test_qr_login.py              # QR 登录测试
│   ├── test_integration.py           # 集成测试（需 Cookie）
│   └── test_smoke.py                 # 烟雾测试（真实 API）
│
├── pyproject.toml                    # 项目配置、依赖、工具设置
├── uv.lock                           # 依赖锁文件
├── README.md                         # 完整使用指南
├── SCHEMA.md                         # 输出数据结构定义
├── SKILL.md                          # AI Agent 快速上手
├── CLAUDE.md                         # 深度架构文档
└── .gitignore                        # Git 忽略规则
```

---

## 模块组织原则

### 1. 传输层 (Transport)

**文件**: `client.py`, `client_mixins.py`, `signing.py`, `creator_signing.py`

**职责**:
- HTTP 请求构建与发送
- 请求签名（x-s, x-s-common, x-t）
- 自动重试与速率限制
- 反检测（Gaussian 延迟、浏览器指纹）

**新增 API 端点时**:
1. 在相应的 Mixin 中添加方法（如 `ReadingEndpointsMixin` 中添加搜索方法）
2. 使用 `self._post_async()` 或 `self._get_async()` 发送请求
3. 返回 raw dict（不规范化）
4. 签名自动处理，无需显式调用

**示例**:
```python
# 在 ReadingEndpointsMixin 中
async def search(self, keyword: str, page: int = 1) -> dict:
    """搜索笔记。"""
    payload = {"keyword": keyword, "page": page}
    return await self._post_async(
        "/note/feed",
        json=payload
    )
```

### 2. 会话层 (Session)

**文件**: `cookies.py`, `qr_login.py`

**职责**:
- Cookie 提取（浏览器自动检测）
- TTL 管理（7 天有效期）
- xsec_token 缓存
- 二维码登录流程

**关键函数**:
- `get_cookies()` — 获取有效 Cookie（自动处理 TTL 与刷新）
- `save_cookies(cookies)` — 保存 Cookie + TTL
- `cache_note_context(note_id, xsec_token)` — 缓存笔记上下文
- `login_with_qrcode()` — 二维码登录

### 3. 命令层 (Commands)

**目录**: `commands/`

**职责**:
- 解析 CLI 参数
- 调用客户端 API
- 规范化数据
- 格式化输出

**按功能域分组**（6 个文件）:

| 文件 | 命令数 | 代表命令 |
|------|--------|----------|
| `auth.py` | 4 | login, status, logout, whoami |
| `reading.py` | 10 | search, read, comments, feed, hot, topics, ... |
| `interactions.py` | 5 | like, favorite, comment, reply, delete-comment |
| `creator.py` | 3 | post, my-notes, delete |
| `social.py` | 3 | follow, unfollow, favorites |
| `notifications.py` | 2 | unread, notifications |
| `batch.py` | 1 | batch |

**新增命令时**:
1. 在对应的 `commands/*.py` 中添加函数
2. 使用 `@click.command()` 装饰
3. 在 `cli.py` 中 `add_command()` 注册
4. 通过 `_common.output_context()` 输出（自动处理 --json/--yaml）

**示例**:
```python
# 在 commands/reading.py 中
@click.command()
@click.argument('keyword')
@click.option('--sort', default='general')
def search(keyword, sort):
    """搜索笔记。"""
    client = get_client()  # 从 _common 导入
    results = client.search(keyword, sort=sort)

    normalized = normalize_search_results(results)
    output_context(normalized, as_json, as_yaml)
```

### 4. 工具层 (Utils)

**文件**: `formatter*.py`, `exceptions.py`, `html_parser.py`, `note_refs.py`, 等

**子模块**:

#### 异常处理 (`exceptions.py`, `error_codes.py`)
- 定义 7 个自定义异常类
- 映射 API 错误码到人类可读的消息
- 用于客户端与命令层的错误处理

#### 格式化 (`formatter*.py`)
- **formatter_utils.py** — 基础工具（console, payload 生成）
- **formatter_normalizers.py** — 数据规范化（笔记、用户、评论等）
- **formatter_renderers.py** — Rich 渲染（表格、树、彩色输出）
- **formatter.py** — 统一导出入口

**信封模式**（所有输出）:
```yaml
ok: true                      # 或 false
schema_version: "1"
data:                         # 具体内容
  notes: [...]
error: (仅当 ok=false)
  code: "error_code"
  message: "..."
```

#### 其他工具
- **html_parser.py** — 从 HTML 提取笔记详情（内部使用）
- **note_refs.py** — 笔记 ID/URL 解析（将 URL 转换为 ID）
- **constants.py** — API Host、User-Agent、错误码等常量
- **command_normalizers.py** — 命令级参数规范化
- **input_loader.py** — 加载图片、CSV 等输入文件
- **batch_runner.py** — 批量任务队列管理

---

## 命名规范

### 文件命名
- **包结构**: 小写 + 下划线（`xhs_cli`, `client_mixins`, `formatter_normalizers`）
- **Mixin 类**: `*EndpointsMixin` 模式（`ReadingEndpointsMixin`）
- **工具模块**: 功能名 + 后缀（`formatter_utils`, `formatter_renderers`）

### 类命名
- **主类**: `XhsClient`（驼峰式首字母大写）
- **异常类**: `*Error` 后缀（`NeedVerifyError`, `SessionExpiredError`）
- **Mixin**: `*EndpointsMixin`（明确表示 API 端点集合）

### 函数命名
- **CLI 命令**: 小写 + 下划线（`search`, `my_notes`, `delete_comment`）
- **内部方法**: 小写 + 下划线（`_post_async`, `_apply_delay`）
- **格式化函数**: `render_*` 或 `normalize_*`（明确意图）

---

## 常见操作指南

### 添加新的 API 端点

1. **在对应 Mixin 中定义方法**
   ```python
   # client_mixins.py - ReadingEndpointsMixin
   async def search(self, keyword: str) -> dict:
       return await self._post_async("/note/feed", json={"keyword": keyword})
   ```

2. **在命令层调用**
   ```python
   # commands/reading.py
   @click.command()
   def search(keyword):
       client = XhsClient(cookies)
       results = client.search(keyword)
       output_context(normalize_search_results(results))
   ```

### 处理新的错误情况

1. **定义异常**（如需要）
   ```python
   # exceptions.py
   class CustomError(XhsApiError):
       """自定义错误。"""
       pass
   ```

2. **在 client.py 中捕获并抛出**
   ```python
   if response.status_code == 12345:
       raise CustomError("Error message")
   ```

3. **在 error_codes.py 中映射**
   ```python
   ERROR_CODE_MAP = {
       12345: ("custom_error", "用户友好的错误信息")
   }
   ```

### 添加新的格式化类型

1. **在 formatter_normalizers.py 中添加规范化函数**
   ```python
   def normalize_new_data(data: dict) -> dict:
       return {"field": data.get("field")}
   ```

2. **在 formatter_renderers.py 中添加渲染函数**
   ```python
   def render_new_data(data: dict):
       # 使用 console 输出
       console.print(data)
   ```

---

## 相关文档

- **代码实现细节**: 见各文件的 docstring
- **数据结构**: `SCHEMA.md`
- **API 端点清单**: `README.md` 或 `CLAUDE.md`
- **测试对应关系**: 见 `tests/` 目录文件

