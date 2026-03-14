# 📋 实施计划：xiaohongshu-cli 批量笔记获取功能

**版本**：v1.0
**创建时间**：2026-03-13 23:26:29
**任务类型**：全栈（后端 API 层 + CLI 层）
**优先级**：高（用户明确需求，涉及 OpenXhs 集成）

---

## 一、任务目标

### 核心需求
将 xiaohongshu-cli 从单笔记查询扩展为批量笔记数据获取，支持：
- **输入**：包含笔记链接/ID 的表格（CSV/JSON/Excel）
- **处理**：批量抓取笔记数据，失败自动重试，可中断恢复
- **输出**：结构化数据，便于 OpenXhs 内容策略分析

### 验收标准
- ✅ 支持 CSV/JSON 两种输入格式（Excel 可选）
- ✅ 单笔记失败不影响全局，返回详细错误
- ✅ 输出 YAML/JSON envelope 格式（与单条命令一致）
- ✅ 支持断点恢复（通过 checkpoint 文件）
- ✅ 与现有风控机制兼容（串行处理，自适应冷却）
- ✅ OpenXhs 协议对接（预留导入接口）

---

## 二、技术方案

### 推荐方案：A - 串行批处理 + Checkpoint 恢复

**原因**：
- 与现有风控机制最兼容
- 风险最低，故障排查最简单
- 改动集中，侵入性最小

**架构图**：
```
输入文件 (CSV/JSON)
    ↓
[InputLoader] - 规范化解析（统一为 note_id + xsec_token）
    ↓
[BatchRunner] - 串行执行（复用 client.get_note_detail）
    ├─ 错误分级（验证码/会话过期/IP限制）
    ├─ 自动冷却与重试
    └─ Checkpoint 保存进度（可中断恢复）
    ↓
[OutputFormatter] - 结构化输出
    ├─ Summary: {total, success, failed, skipped}
    ├─ Items: [{ref, status, normalized_data, error, raw}]
    └─ Errors: [聚合错误]
    ↓
[OpenXhsAdapter] - 协议转换
    └─ 生成 OpenXhs ingest 格式 (JSON)
    ↓
结果输出 (YAML/JSON) 或文件持久化 (JSONL)
```

---

## 三、实施步骤

### Step 1：定义输入/输出规范（2 小时）

**新增命令**：
```bash
xhs read-batch --input <path> [--output <path>] [--format json|yaml]
               [--continue-on-error] [--checkpoint <path>] [--unsafe-concurrency]
```

**参数说明**：
| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `--input` | 必需 | 输入文件路径 | `notes.csv` |
| `--output` | 可选 | 输出文件路径（不填则 stdout） | `result.jsonl` |
| `--format` | 可选 | 输出格式 | `json` / `yaml`（默认 `yaml`） |
| `--continue-on-error` | 可选 | 单条失败是否继续 | 默认 `true` |
| `--checkpoint` | 可选 | 断点恢复文件 | `batch_001.checkpoint` |
| `--unsafe-concurrency` | 可选 | 启用 2-3 并发（测试用） | — |

**输入格式**：

CSV 示例（`notes.csv`）：
```csv
note_url,creator_id,note_id
https://www.xiaohongshu.com/explore/xxx?xsec_token=yyy,5f2e123,xxx
https://www.xiaohongshu.com/explore/zzz,5f2e456,zzz
```

JSON 示例（`notes.json`）：
```json
{
  "notes": [
    {"url": "https://...", "note_id": "xxx", "creator_id": "5f2e123"},
    {"note_id": "zzz", "creator_id": "5f2e456"}
  ]
}
```

**输出格式**（YAML 示例）：
```yaml
ok: true
schema_version: "1"
data:
  job:
    input_file: notes.csv
    total: 100
    success: 95
    failed: 3
    skipped: 2
    duration_seconds: 145.23
  items:
    - index: 0
      input: "https://..."
      status: success
      note_id: xxx
      creator_id: 5f2e123
      normalized:
        title: "..."
        content: "..."
        metrics: {liked_count: 1000, comment_count: 50}
      raw: {...}
    - index: 1
      input: "https://..."
      status: failed
      error:
        code: verification_required
        message: "Captcha required"
        retriable: true
  errors:
    - index: 1
      code: verification_required
      count: 1
    - index: 50
      code: ip_blocked
      count: 2
  openxhs_sink: "result.openxhs.jsonl"  # 可选：导出给 OpenXhs 的记录文件
```

---

### Step 2：新增输入加载器模块（3 小时）

**文件**：`xiaohongshu-cli/xhs_cli/input_loader.py`

```python
# 伪代码
from typing import TypedDict, List, Union
from pathlib import Path
import csv
import json

class RawRow(TypedDict):
    """原始行数据"""
    row_index: int
    values: dict

class ResolvedRef(TypedDict):
    """解析后的笔记引用"""
    note_id: str
    xsec_token: str
    xsec_source: str
    creator_id: str | None

def load_csv(path: Path) -> List[RawRow]:
    """解析 CSV 文件"""
    rows = []
    with open(path, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            rows.append(RawRow(row_index=idx, values=row))
    return rows

def load_json(path: Path) -> List[RawRow]:
    """解析 JSON 文件（支持 list 和 dict.notes）"""
    with open(path) as f:
        data = json.load(f)

    if isinstance(data, list):
        items = data
    elif isinstance(data, dict) and 'notes' in data:
        items = data['notes']
    else:
        raise ValueError("JSON 必须是 list 或 {notes: [...]}")

    return [RawRow(row_index=idx, values=item) for idx, item in enumerate(items)]

def resolve_row(row: RawRow, idx: int) -> Union[ResolvedRef, tuple[int, str]]:
    """
    解析行，返回 ResolvedRef 或 (idx, error_msg)
    """
    values = row['values']
    text = None

    # 优先级：url > note_url > note_id > id
    for key in ['url', 'note_url', 'note_id', 'id']:
        if values.get(key):
            text = values[key].strip()
            break

    if not text:
        return (idx, "No note_id or URL found in row")

    try:
        note_id, token, source = parse_note_reference(text)
        creator_id = values.get('creator_id') or values.get('user_id')
        return ResolvedRef(
            note_id=note_id,
            xsec_token=token or "",
            xsec_source=source or "pc_feed",
            creator_id=creator_id,
        )
    except Exception as e:
        return (idx, str(e))

def load_inputs(path: str) -> tuple[List[ResolvedRef], List[tuple[int, str]]]:
    """
    加载输入文件，返回 (成功列表, 失败列表)
    """
    p = Path(path)
    if p.suffix.lower() == '.csv':
        raw_rows = load_csv(p)
    elif p.suffix.lower() == '.json':
        raw_rows = load_json(p)
    else:
        raise ValueError(f"Unsupported format: {p.suffix}")

    success = []
    errors = []
    seen_ids = set()

    for raw_row in raw_rows:
        result = resolve_row(raw_row, raw_row['row_index'])
        if isinstance(result, tuple):
            # 错误
            errors.append(result)
        else:
            # 去重
            if result['note_id'] not in seen_ids:
                success.append(result)
                seen_ids.add(result['note_id'])
            else:
                errors.append((raw_row['row_index'], "Duplicate note_id"))

    return success, errors
```

**关键设计**：
- 支持多种列名（`url`, `note_url`, `note_id`, `id`）
- 自动去重
- 列表化错误报告

---

### Step 3：新增批处理执行器模块（5 小时）

**文件**：`xiaohongshu-cli/xhs_cli/batch_runner.py`

```python
# 伪代码
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import time
import json
from pathlib import Path
from datetime import datetime

@dataclass
class BatchCheckpoint:
    """断点文件"""
    job_id: str
    processed: set = field(default_factory=set)  # 已处理的 note_id
    failed: Dict[str, Dict] = field(default_factory=dict)
    last_error: Optional[Dict] = None

    def save(self, path: Path):
        with open(path, 'w') as f:
            json.dump({
                'job_id': self.job_id,
                'processed': list(self.processed),
                'failed': self.failed,
                'last_error': self.last_error,
            }, f, indent=2)

    @staticmethod
    def load(path: Path) -> 'BatchCheckpoint':
        with open(path) as f:
            data = json.load(f)
        cp = BatchCheckpoint(job_id=data['job_id'])
        cp.processed = set(data['processed'])
        cp.failed = data['failed']
        cp.last_error = data['last_error']
        return cp

@dataclass
class BatchItem:
    """批处理单条结果"""
    index: int
    ref: Dict  # ResolvedRef
    status: str  # success / failed / skipped
    error: Optional[Dict] = None
    raw: Optional[Dict] = None
    normalized: Optional[Dict] = None

class BatchRunner:
    def __init__(self, client, checkpoint_path=None):
        self.client = client
        self.checkpoint = checkpoint_path
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0,
        }
        self.items: List[BatchItem] = []
        self.global_errors: Dict[str, int] = {}
        self.start_time = None

    def run(self, refs: List[Dict], continue_on_error=True) -> Dict:
        """
        执行批处理
        """
        self.start_time = time.time()
        self.stats['total'] = len(refs)

        cp = None
        if self.checkpoint and self.checkpoint.exists():
            cp = BatchCheckpoint.load(self.checkpoint)
            logger.info(f"Resuming from checkpoint: {cp.processed}")

        for idx, ref in enumerate(refs):
            if cp and ref['note_id'] in cp.processed:
                self.stats['skipped'] += 1
                continue

            item = self._fetch_one(idx, ref)
            self.items.append(item)

            if item.status == 'success':
                self.stats['success'] += 1
            elif item.status == 'failed':
                self.stats['failed'] += 1
                if not continue_on_error:
                    break

            # 保存 checkpoint
            if cp:
                cp.processed.add(ref['note_id'])
                cp.save(self.checkpoint)

        return self._build_result()

    def _fetch_one(self, idx: int, ref: Dict) -> BatchItem:
        """
        抓取单条笔记
        """
        item = BatchItem(index=idx, ref=ref, status='pending')

        try:
            # 调用 client.get_note_detail
            raw = self.client.get_note_detail(
                ref['note_id'],
                xsec_token=ref.get('xsec_token', ''),
                xsec_source=ref.get('xsec_source', 'pc_feed'),
            )

            item.status = 'success'
            item.raw = raw
            item.normalized = normalize_note_payload(raw)

        except NeedVerifyError as e:
            # 需要验证码，暂停
            logger.error(f"Captcha required for {ref['note_id']}")
            item.status = 'failed'
            item.error = {
                'code': 'verification_required',
                'message': 'User intervention required',
                'retriable': True,
            }
            self.global_errors.setdefault('verification_required', 0)
            self.global_errors['verification_required'] += 1
            # 暂停批处理
            self._pause_for_manual_verify()

        except SessionExpiredError as e:
            # 会话过期，刷新 client
            logger.warning(f"Session expired, refreshing...")
            item.status = 'failed'
            item.error = {
                'code': 'session_expired',
                'message': 'Re-login required',
                'retriable': True,
            }
            # 尝试刷新 client
            self._refresh_client()
            # 当前条重试一次
            try:
                raw = self.client.get_note_detail(...)
                item.status = 'success'
                item.raw = raw
                item.normalized = normalize_note_payload(raw)
            except:
                self.global_errors.setdefault('session_expired', 0)
                self.global_errors['session_expired'] += 1

        except IpBlockedError as e:
            logger.error(f"IP blocked for {ref['note_id']}")
            item.status = 'failed'
            item.error = {
                'code': 'ip_blocked',
                'message': 'IP blocked, consider switching network',
                'retriable': True,
            }
            self.global_errors.setdefault('ip_blocked', 0)
            self.global_errors['ip_blocked'] += 1
            # 致命错误，停止批处理
            raise RuntimeError("IP blocked, cannot continue")

        except XhsApiError as e:
            # API 错误，记录但继续
            logger.warning(f"API error for {ref['note_id']}: {e}")
            item.status = 'failed'
            item.error = {
                'code': 'api_error',
                'message': str(e),
                'retriable': False,
            }
            self.global_errors.setdefault('api_error', 0)
            self.global_errors['api_error'] += 1

        except Exception as e:
            # 未分类错误
            logger.exception(f"Unexpected error for {ref['note_id']}")
            item.status = 'failed'
            item.error = {
                'code': 'unknown_error',
                'message': str(e),
                'retriable': False,
            }
            self.global_errors.setdefault('unknown_error', 0)
            self.global_errors['unknown_error'] += 1

        return item

    def _pause_for_manual_verify(self):
        """暂停，等待用户手动完成验证码"""
        logger.info("Pausing for manual verification...")
        # 可选：打开浏览器提示用户
        logger.info("Please complete the CAPTCHA in browser and press Enter to continue...")
        input()

    def _refresh_client(self):
        """刷新客户端（重新加载 Cookie）"""
        logger.info("Refreshing client session...")
        # 这里需要与 CLI 层协调如何刷新
        # 暂时假设可以调用 get_cookies 重新获取
        try:
            cookies = get_cookies()
            self.client = XhsClient(cookies)
        except Exception as e:
            logger.error(f"Failed to refresh client: {e}")

    def _build_result(self) -> Dict:
        """构建最终结果"""
        duration = time.time() - self.start_time
        return {
            'job': {
                'total': self.stats['total'],
                'success': self.stats['success'],
                'failed': self.stats['failed'],
                'skipped': self.stats['skipped'],
                'duration_seconds': round(duration, 2),
            },
            'items': [
                {
                    'index': item.index,
                    'input': f"{item.ref.get('note_id')} (creator: {item.ref.get('creator_id', 'unknown')})",
                    'status': item.status,
                    'note_id': item.ref.get('note_id'),
                    'creator_id': item.ref.get('creator_id'),
                    'error': item.error,
                    'normalized': item.normalized,
                    'raw': item.raw,
                }
                for item in self.items
            ],
            'errors': [
                {'code': code, 'count': count}
                for code, count in self.global_errors.items()
            ],
        }
```

**关键设计**：
- Checkpoint 恢复：中断后可接着处理
- 错误分级：验证码（停止）、会话过期（刷新）、API 错误（继续）
- 统一到单条逻辑，复用现有风控机制

---

### Step 4：新增 OpenXhs 适配层（2 小时）

**文件**：`xiaohongshu-cli/xhs_cli/openxhs_adapter.py`

```python
# 伪代码
from typing import List, Dict, Any
from datetime import datetime
import json

def adapt_for_openxhs(items: List[Dict]) -> List[Dict]:
    """
    将批处理结果转换为 OpenXhs ingest 格式
    """
    records = []
    for item in items:
        if item['status'] != 'success':
            continue  # 仅导出成功的记录

        record = {
            'platform': 'xiaohongshu',
            'source': 'xiaohongshu-cli/read-batch',
            'note_id': item['note_id'],
            'creator_id': item.get('creator_id'),
            'fetched_at': datetime.utcnow().isoformat() + 'Z',

            # 标准化的笔记内容
            'content': {
                'title': item['normalized'].get('title'),
                'body': item['normalized'].get('desc'),
                'tags': item['normalized'].get('tags', []),
                'image_count': item['normalized'].get('image_count', 0),
            },

            # 互动指标
            'metrics': {
                'liked_count': item['normalized'].get('liked_count', 0),
                'comment_count': item['normalized'].get('comment_count', 0),
                'collected_count': item['normalized'].get('collected_count', 0),
                'share_count': item['normalized'].get('share_count', 0),
            },

            # 原始数据备份
            'raw': item.get('raw'),
        }
        records.append(record)

    return records

def save_openxhs_jsonl(records: List[Dict], output_path: str):
    """
    以 JSONL 格式导出给 OpenXhs
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
```

---

### Step 5：新增 CLI 命令（2 小时）

**文件**：`xiaohongshu-cli/xhs_cli/commands/batch.py`（新文件）

```python
# 伪代码
import click
from pathlib import Path

@click.command('read-batch')
@click.argument('input_path', type=click.Path(exists=True))
@click.option('--output', type=click.Path(), help='Output file path (JSONL format)')
@click.option('--format', type=click.Choice(['json', 'yaml']), default='yaml', help='Output format')
@click.option('--continue-on-error', is_flag=True, default=True, help='Continue on fetch errors')
@click.option('--checkpoint', type=click.Path(), help='Checkpoint file for resumable runs')
@click.option('--unsafe-concurrency', is_flag=True, help='[EXPERIMENTAL] Enable 2-3 concurrent workers')
@click.pass_context
def read_batch(ctx, input_path, output, format, continue_on_error, checkpoint, unsafe_concurrency):
    """
    Fetch notes in batch from CSV/JSON file.

    Example:
        xhs read-batch notes.csv --output result.yaml
        xhs read-batch notes.json --checkpoint batch_001.ckpt --continue-on-error
    """

    # Step 1: 加载输入
    try:
        refs, input_errors = load_inputs(input_path)
        if input_errors:
            for idx, err_msg in input_errors:
                logger.warning(f"Row {idx}: {err_msg}")
        if not refs:
            raise UsageError("No valid notes found in input")
    except Exception as e:
        raise UsageError(f"Failed to load input: {e}")

    # Step 2: 执行批处理
    try:
        client = ctx.obj['client']  # 从 CLI 上下文获取
        runner = BatchRunner(client, checkpoint_path=Path(checkpoint) if checkpoint else None)
        result = runner.run(refs, continue_on_error=continue_on_error)
    except Exception as e:
        raise ClickException(f"Batch processing failed: {e}")

    # Step 3: 构建输出
    # 包装成 envelope
    envelope = {
        'ok': result['job']['failed'] == 0,
        'schema_version': '1',
        'data': result,
    }

    # 如果成功，附加 OpenXhs 导出信息
    if output:
        openxhs_records = adapt_for_openxhs(result['items'])
        openxhs_path = Path(output).with_suffix('.openxhs.jsonl')
        save_openxhs_jsonl(openxhs_records, str(openxhs_path))
        envelope['data']['openxhs_sink'] = str(openxhs_path)

    # Step 4: 输出结果
    if output:
        # 写入文件（JSONL 或包装后的 YAML）
        with open(output, 'w', encoding='utf-8') as f:
            if format == 'json':
                json.dump(envelope, f, ensure_ascii=False, indent=2)
            else:
                import yaml
                yaml.dump(envelope, f, allow_unicode=True)
        logger.info(f"Results saved to {output}")
    else:
        # 输出到 stdout
        maybe_print_structured(envelope, format=format, as_json=(format == 'json'), as_yaml=(format == 'yaml'))

    # Step 5: 返回码
    exit_code = 0 if envelope['ok'] else 1
    ctx.exit(exit_code)
```

---

### Step 6：集成到 CLI 主入口（1 小时）

**文件**：`xiaohongshu-cli/xhs_cli/cli.py` （修改）

```python
# 在主 cli group 中注册新命令
from .commands.batch import read_batch

@click.group(...)
def cli(...):
    ...

cli.add_command(read_batch)  # 注册 xhs read-batch
```

---

### Step 7：测试与验证（4 小时）

**新增测试文件**：`tests/test_batch_reader.py`

```python
# 伪代码
import pytest
from pathlib import Path
from xhs_cli.input_loader import load_inputs, resolve_row
from xhs_cli.batch_runner import BatchRunner
from xhs_cli.openxhs_adapter import adapt_for_openxhs

def test_load_csv():
    """测试 CSV 加载"""
    csv_path = Path("tests/fixtures/notes_sample.csv")
    refs, errors = load_inputs(str(csv_path))
    assert len(refs) > 0
    assert all(r['note_id'] for r in refs)

def test_load_json():
    """测试 JSON 加载"""
    json_path = Path("tests/fixtures/notes_sample.json")
    refs, errors = load_inputs(str(json_path))
    assert len(refs) > 0

def test_batch_runner_checkpoint(mock_client):
    """测试 checkpoint 恢复"""
    refs = [...]
    runner = BatchRunner(mock_client, checkpoint_path=Path("test.ckpt"))

    # 第一轮：处理前 5 个
    result_1 = runner.run(refs[:5])
    assert result_1['job']['success'] > 0

    # 模拟中断，加载 checkpoint
    runner_2 = BatchRunner(mock_client, checkpoint_path=Path("test.ckpt"))
    result_2 = runner_2.run(refs[5:])
    # 断点恢复的项不应重复处理

def test_openxhs_adapter():
    """测试 OpenXhs 导出"""
    items = [...]
    records = adapt_for_openxhs(items)
    assert all(r['platform'] == 'xiaohongshu' for r in records)
```

**测试数据**：创建 `tests/fixtures/` 目录，包含示例 CSV 和 JSON

---

## 四、关键文件修改清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `xhs_cli/input_loader.py` | **创建** | CSV/JSON/Excel 解析 |
| `xhs_cli/batch_runner.py` | **创建** | 批处理执行引擎 + Checkpoint |
| `xhs_cli/openxhs_adapter.py` | **创建** | OpenXhs 协议转换 |
| `xhs_cli/commands/batch.py` | **创建** | CLI 命令入口 |
| `xhs_cli/cli.py` | **修改** | 注册 `read-batch` 命令 |
| `xhs_cli/formatter_normalizers.py` | **修改** | 统一 API/HTML note 结构（重点） |
| `tests/test_batch_reader.py` | **创建** | 批处理测试套件 |
| `tests/fixtures/` | **创建** | 测试数据（CSV/JSON 示例） |

---

## 五、与 OpenXhs 的集成协议

### 数据流
```
xiaohongshu-cli (read-batch)
    ↓ 导出 JSONL
OpenXhs (ingest service)
    ↓ 处理数据
ohmyxhs (内容策略)
    ↓ 生成种草笔记
```

### 导入格式

OpenXhs 应支持以下 JSON 格式：

```json
{
  "platform": "xiaohongshu",
  "source": "xiaohongshu-cli/read-batch",
  "note_id": "xxx",
  "creator_id": "5f2e123",
  "fetched_at": "2026-03-13T23:26:29Z",
  "content": {
    "title": "...",
    "body": "...",
    "tags": ["tag1", "tag2"],
    "image_count": 5
  },
  "metrics": {
    "liked_count": 1000,
    "comment_count": 50,
    "collected_count": 200,
    "share_count": 10
  },
  "raw": {...}  // 备份原始响应
}
```

### 导入接口（待确认）

OpenXhs 需要实现以下之一：

1. **HTTP POST 接口**
   ```
   POST /api/v1/ingest/xiaohongshu
   Content-Type: application/x-ndjson
   <JSONL 流>
   ```

2. **文件批量导入**
   ```
   /var/lib/openxhs/ingest/xiaohongshu/*.jsonl
   ```

3. **Python SDK**
   ```python
   from openxhs import IngestClient
   client = IngestClient()
   client.ingest_jsonl('result.openxhs.jsonl')
   ```

---

## 六、风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| API 限流导致批处理失败 | 串行处理，自适应冷却，支持 checkpoint 恢复 |
| 验证码阻断 | 暂停并提示用户手动完成，用户确认后继续 |
| 会话过期（长批处理） | 自动检测并刷新 Cookie，单条重试一次 |
| IP 被限制 | 记录详细错误，建议用户切换网络或等待 |
| 内存溢出（大批量） | 支持 streaming 输出（JSONL），单条处理不保留 |
| 与 OpenXhs 不兼容 | 提前对齐导入格式和接口 |

---

## 七、后续优化（Phase 2）

### 短期（1-2 周）
- [ ] 支持 Excel 输入格式
- [ ] 支持并发处理（--unsafe-concurrency）
- [ ] 详细的进度条（tqdm）

### 中期（2-4 周）
- [ ] 与 OpenXhs 接口对接测试
- [ ] 支持自定义映射规则（用户定义哪列是 note_id）
- [ ] 支持数据去重与智能合并

### 长期（1 个月以上）
- [ ] Web UI 批量上传界面
- [ ] 定时任务（cron job 批处理）
- [ ] 数据库持久化存储

---

## 八、预期工作量

| 步骤 | 时间估计 | 负责人 |
|------|----------|--------|
| Step 1：输入/输出规范 | 2h | Claude |
| Step 2：InputLoader | 3h | Claude |
| Step 3：BatchRunner | 5h | Claude |
| Step 4：OpenXhsAdapter | 2h | Claude |
| Step 5：CLI 命令 | 2h | Claude |
| Step 6：CLI 集成 | 1h | Claude |
| Step 7：测试与文档 | 4h | Claude |
| **总计** | **19h** | — |

---

## 九、交付物清单

- ✅ 4 个新 Python 模块（input_loader, batch_runner, openxhs_adapter, batch.py 命令）
- ✅ CLI 命令 `xhs read-batch` 完整实现
- ✅ 测试套件 + 示例数据
- ✅ OpenXhs 集成协议文档
- ✅ 使用示例与故障排除指南

---

## 十、SESSION_ID（供 /ccg:execute 使用）

```
CODEX_SESSION: 019ce801-b46a-7233-8d2a-90cb5ba78c75
GEMINI_SESSION: (失败 - 环境问题)
```

---

## 附录 A：使用示例

### 示例 1：基础批处理
```bash
# 从 CSV 读取笔记并输出 YAML
xhs read-batch notes.csv --output result.yaml
```

### 示例 2：支持断点恢复
```bash
# 第一次运行，设置 checkpoint
xhs read-batch notes.csv --checkpoint batch_001.ckpt --output result.yaml

# 中途中断（Ctrl+C），然后恢复
xhs read-batch notes.csv --checkpoint batch_001.ckpt --output result.yaml
```

### 示例 3：导出给 OpenXhs
```bash
# 自动生成 result.openxhs.jsonl，供 OpenXhs 导入
xhs read-batch notes.csv --output result.yaml
cat result.openxhs.jsonl | curl -X POST http://openxhs-server/api/v1/ingest -d @-
```

---

**计划完成时间**: 2026-03-13 23:26:29
**优先级**: 高
**目标交付**: 3 个工作日内完成开发 + 测试
