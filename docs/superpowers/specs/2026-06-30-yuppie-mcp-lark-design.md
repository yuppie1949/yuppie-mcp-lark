# yuppie-mcp-lark 改造设计

- 日期：2026-06-30
- 状态：已确认，待实现
- 范围：将当前从 `yuppie-mcp-mssql` 复制过来的仓库，改造为对接飞书 OpenAPI 的 MCP Server `yuppie-mcp-lark`

## 1. 背景与目标

当前仓库的所有代码（`pyproject.toml`、`src/yuppie_mcp_mssql/`、`tests/`、`README.md`、`CLAUDE.md`）都是 SQL Server MCP 的实现，需要整体替换为飞书 MCP。

参考代码 `doc/lark_client.py` 是一个 612 行的飞书 OpenAPI 客户端类 `LarkClient`，包含：
- 通用能力（消息发送、多维表格搜索、电子表格读写与工作表管理）
- 业务定制方法（批次处理、列过滤等电商场景的快捷封装）

改造目标：基于 `lark_client.py` 的通用能力，构建一个对接飞书的 MCP Server，复用 mssql 项目的工程骨架（Pydantic 输入校验、async 工具、FastMCP 框架、ruff/mypy/pytest 工具链）。

## 2. 关键决策

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 工具范围 | 只做通用能力 | 业务定制方法通用性低，剔除后工具更聚焦 |
| mssql 残留处理 | 保留骨架，内容替换 | 沿用成熟的工具设计模式（Pydantic + async + markdown 输出） |
| 工具组织方式 | 按业务域重组 + Pydantic 输入 | AI 调用友好，与 mssql 项目风格一致 |
| 鉴权方式 | 仅 `tenant_access_token` | 简单，覆盖自动化/机器人场景 |
| API 域名 | 默认 `feishu.cn` + 可切换 | 一个环境变量覆盖国内/国际版 |
| 传输模式 | 仅 stdio | MCP 主流用法，YAGNI |
| LarkClient 拆分 | mixin 按业务域拆分 | 单一类对外，内部按域隔离，便于扩展 |

## 3. 整体架构

### 目录结构

```
src/yuppie_mcp_lark/
├── __init__.py
├── __main__.py
├── server.py                 # MCP 入口，注册所有工具，stdio 传输
├── utils/
│   ├── __init__.py
│   ├── config.py             # 读取 LARK_APP_ID/SECRET/BASE_URL
│   └── lark/
│       ├── __init__.py       # 暴露 LarkClient（聚合所有 mixin）
│       ├── base.py           # _LarkBase：http client、token、_request/_get/_post/_put、_index_to_letter
│       ├── messages.py       # MessagesMixin：send_message/send_messages
│       ├── bitable.py        # BitableMixin：search_records
│       └── sheets.py         # SheetsMixin：metainfo/add_sheet/delete_sheet/copy_sheet/read_range/write_range/append_data/delete_dimension/_resolve_column_letter
└── tools/
    ├── __init__.py
    ├── messages.py           # 消息域 MCP 工具
    ├── bitable.py            # 多维表格域 MCP 工具
    └── sheets.py             # 电子表格域 MCP 工具
```

### 两层职责分离

- `utils/lark/<域>.py`：底层飞书 OpenAPI 薄包装（mixin）
- `tools/<域>.py`：MCP 工具层（Pydantic 校验 → 调用 client → markdown 格式化）

### Mixin 模式说明

- `_LarkBase` 负责共享状态：httpx.AsyncClient、tenant_access_token 缓存、`_request`/`_get`/`_post`/`_put`、纯 helper `_index_to_letter`
- 各业务域 mixin（`MessagesMixin`/`BitableMixin`/`SheetsMixin`）只定义本域的方法
- 对外暴露单一类：`class LarkClient(_LarkBase, MessagesMixin, BitableMixin, SheetsMixin)`
- server.py 只需 `client = LarkClient(app_id, app_secret, base_url)` 一行

## 4. MCP 工具清单

共 10 个工具，全部为 `async def`，输入用 Pydantic `BaseModel` 校验，返回结构化 markdown。

### 消息域 `tools/messages.py`（1 个）

#### `lark_send_message`
发送消息给单个用户/群。

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `receive_id` | str | 是 | - | 接收者 ID |
| `msg_type` | str | 否 | `"text"` | 消息类型 |
| `content` | str | 是 | - | JSON 字符串（如 `'{"text":"hello"}'`） |
| `receive_id_type` | str | 否 | `"open_id"` | ID 类型 |

> 批量发送不单独做工具，AI 可循环调用 `lark_send_message`。

### 多维表格域 `tools/bitable.py`（1 个）

#### `lark_search_records`
搜索多维表格记录，返回 `{items, has_more, page_token, total}`。

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `app_token` | str | 是 | - | 多维表格 app_token |
| `table_id` | str | 是 | - | 数据表 table_id |
| `view_id` | str | 否 | - | 视图 ID |
| `field_names` | list[str] | 否 | - | 指定返回字段名 |
| `sort` | dict | 否 | - | 排序规则 |
| `filter` | dict | 否 | - | 过滤条件 |
| `page_token` | str | 否 | - | 分页 token |
| `page_size` | int | 否 | - | 分页大小 |
| `automatic_fields` | bool | 否 | - | 是否返回自动计算字段 |
| `user_id_type` | str | 否 | - | 用户 ID 类型 |

### 电子表格域 `tools/sheets.py`（8 个）

#### `lark_get_spreadsheet_metainfo`
获取表格元信息（含工作表列表）。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `spreadsheet_token` | str | 是 | 电子表格 token |

#### `lark_add_sheet`
添加工作表，返回 sheetId。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `spreadsheet_token` | str | 是 | 电子表格 token |
| `title` | str | 是 | 新工作表标题 |

#### `lark_delete_sheet`
删除工作表。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `spreadsheet_token` | str | 是 | 电子表格 token |
| `sheet_id` | str | 是 | 工作表 ID |

#### `lark_copy_sheet`
复制工作表，返回新 sheetId。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `spreadsheet_token` | str | 是 | 电子表格 token |
| `source_sheet_id` | str | 是 | 源工作表 ID |
| `title` | str | 是 | 新工作表标题 |

#### `lark_read_range`
读取单个范围数据。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `spreadsheet_token` | str | 是 | 电子表格 token |
| `range_str` | str | 是 | 范围（如 `Sheet1!A1:C10`） |

#### `lark_write_range`
写入单个范围（≤5000 行、100 列）。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `spreadsheet_token` | str | 是 | 电子表格 token |
| `range_str` | str | 是 | 范围 |
| `values` | list[list] | 是 | 二维数组 |

#### `lark_append_data`
追加数据到工作表。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `spreadsheet_token` | str | 是 | 电子表格 token |
| `sheet_id` | str | 是 | 工作表 ID |
| `values` | list[list] | 是 | 二维数组 |

#### `lark_delete_dimension`
删除行/列（1-based 含首尾）。

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `spreadsheet_token` | str | 是 | - | 电子表格 token |
| `sheet_id` | str | 是 | - | 工作表 ID |
| `major_dimension` | str | 否 | `"COLUMNS"` | `COLUMNS` 或 `ROWS` |
| `start_index` | int | 是 | - | 起始索引（1-based 含） |
| `end_index` | int | 是 | - | 结束索引（1-based 含） |

## 5. 鉴权与配置

### 环境变量

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `LARK_APP_ID` | 是 | - | 飞书应用 App ID |
| `LARK_APP_SECRET` | 是 | - | 飞书应用 App Secret |
| `LARK_BASE_URL` | 否 | `https://open.feishu.cn` | 国际版设为 `https://open.larksuite.com` |

### `utils/config.py` 职责

- 集中读取上述环境变量
- 启动时校验 `LARK_APP_ID`/`LARK_APP_SECRET` 必填，缺失则抛清晰错误并退出
- 提供 `LarkConfig` 数据类（dataclass）

### Token 管理（在 `_LarkBase` 里）

- `tenant_access_token` 自动获取，缓存到内存
- 过期前 60 秒自动刷新（`time.time() < expire_at - 60`）
- `asyncio.Lock` 防止并发触发多次刷新
- httpx 客户端用 `httpx.AsyncClient(timeout=120)`，整个进程共享一个实例

### server.py 启动流程

```
读 config → 校验 → 实例化 LarkClient(app_id, app_secret, base_url)
→ 注册 10 个工具 → mcp.run()（stdio 模式）
```

## 6. 错误处理与重试

### `LarkClient` 层（`_LarkBase._request`）

- **限流重试**：飞书返回 `code == 90217`（too many request）时，自动重试最多 3 次，退避 `1.5s → 3s → 4.5s`
- **API 错误**：`code != 0` 抛 `Exception(f"[{method} {path}] 失败(code={code}): {msg}")`，包含方法、路径、错误码、消息
- **token 获取失败**：抛 `Exception(f"获取 tenant_access_token 失败: {msg}")`
- **网络异常**：httpx 的 `RequestError` 直接向上抛（不吞）

### MCP 工具层（`tools/*.py`）

- **Pydantic 校验失败** → FastMCP 自动返回参数错误
- **LarkClient 抛异常** → 工具函数内 `try/except`，捕获后返回结构化 markdown 错误（含 `code`、`msg`、`path`），让 AI 能理解失败原因
- **非 LarkClient 抛出的异常** 向上抛，由 MCP 框架处理

### `LarkClient.close()`

提供 `await client.close()` 方法释放 httpx 连接。stdio 模式下进程退出时不强求显式调用。

## 7. 测试策略

**原则**：只测纯函数和输入校验，不 mock 飞书 API（mock 网络收益低、维护成本高；真实 API 测试需要凭据，CI 不友好）。

### 测试文件

| 文件 | 测试内容 |
|------|---------|
| `tests/test_lark_client.py` | `_LarkBase._index_to_letter`（0→A, 25→Z, 26→AA, 701→ZZ）、`LarkClient` 类继承结构（mixin 方法可见） |
| `tests/test_config.py` | `LarkConfig` 必填字段缺失时抛错、默认值正确（`base_url` 默认 `https://open.feishu.cn`） |
| `tests/test_tools.py` | 各工具 Pydantic 输入校验：必填缺失报错、默认值正确（`msg_type="text"`、`receive_id_type="open_id"`、`major_dimension="COLUMNS"`） |

### 不测的部分

- 飞书 API 真实调用（需要凭据）
- token 并发刷新逻辑（涉及 `asyncio.Lock` 和时间，复杂度高、收益低）
- httpx 网络错误重试（需要 mock httpx，YAGNI）

### 运行方式

```bash
uv run pytest -v
```

沿用 mssql 项目的 `pytest-asyncio` + `asyncio_mode = "auto"` 配置。

## 8. 迁移清单

### 删除

- `src/yuppie_mcp_mssql/`（整个目录）
- `tests/test_sql_guard.py`、`tests/test_export.py`
- `doc/lark_client.py`（迁移到 `src/yuppie_mcp_lark/utils/lark/` 后删除原件）

### 新增

- `src/yuppie_mcp_lark/`（整个包结构，见第 3 节）
- `tests/test_lark_client.py`、`tests/test_config.py`、`tests/test_tools.py`

### 修改

- `pyproject.toml`：包名改 `yuppie-mcp-lark`，入口 `yuppie-mcp-lark = "yuppie_mcp_lark.server:main"`，依赖改为 `mcp`、`httpx`、`pydantic`，移除 `python-tds`，URL 改为 `yuppie-mcp-lark` 仓库地址
- `README.md`：整体重写为飞书 MCP 文档
- `CLAUDE.md`：项目概述、命令、架构描述改为 lark 版本
- `.env.example`：改为 `LARK_APP_ID`/`LARK_APP_SECRET`/`LARK_BASE_URL`
- `scripts/publish.sh`：包名引用改为 `yuppie-mcp-lark`

## 9. 非目标（YAGNI）

明确不做的事：

- 不支持 `user_access_token`（OAuth 流程）
- 不支持 `streamable-http` 传输模式
- 不暴露 `lark_client.py` 的业务定制方法（`set_column_batch_index`、`get_rows_by_batch`、`batch_update_by_batch`、`filter_sheet_columns`、`set_header_list`、`get_last_value`、`batch_append`、`find_sheet_id*`）
- 不做 `output_format` 参数（默认 markdown，未来按需再加）
- 不做 `lark_send_messages` 批量工具（AI 循环调用即可）
