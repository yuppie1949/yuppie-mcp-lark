# yuppie-mcp-lark 迁移到 mcp 2.0 — 验证报告

> 日期：2026-07-31
> 状态：✅ 迁移完成，所有检查全绿

## 1. 背景

项目原声明依赖 `mcp>=1.0.0`（无上限）。mcp 2.0.0（2026-07-28 发布）是破坏性大版本，移除了
`mcp.server.fastmcp.FastMCP`，替代品为 `MCPServer`。在干净环境（如 obot 的 uvx runtime）重新安装时，
解析器会装到 mcp 2.0，导致 `from mcp.server.fastmcp import FastMCP` 抛
`ModuleNotFoundError` 崩溃。

本次迁移：适配 mcp 2.0，并将依赖上限锁定为 `<3.0.0` 防止未来再次被大版本无声破坏。

## 2. 版本与环境

| 项目 | 版本 |
|---|---|
| Python | 3.13.11（requires >=3.10） |
| uv | 0.9.16 |
| **mcp** | **2.0.0** |
| mcp-types | 2.0.0（mcp 2.0 新拆出的独立类型包） |
| httpx | 0.28.1 |
| httpx2 | 2.9.1（mcp 2.0 新增依赖，与 httpx 共存不冲突） |
| pydantic | 2.13.4 |
| ruff | 0.15.16 |
| mypy | 2.1.0 |

## 3. 改动清单

| 文件 | 改动 |
|---|---|
| `pyproject.toml` | 依赖 `mcp>=1.0.0` → `mcp>=2.0.0,<3.0.0` |
| `src/yuppie_mcp_lark/server.py` | `FastMCP` → `MCPServer`；构造函数去 `host`、改用 `version=__version__`；`main()` 将 host/port 传给 `run()`；48 处 `ToolAnnotations` 字段 camelCase → snake_case；import 排序 |
| `uv.lock` | `uv lock` 重解析，mcp 2.0.0 + 新增传递依赖 |
| `CLAUDE.md` | 架构描述同步（FastMCP → MCPServer，工具数 29 → 48） |
| `tools/*`、`utils/lark/*` | 清理既有 mypy / ruff 债务（见第 5 节），ruff format 统一格式 |

**全仓库仅 `server.py` 一个文件 import mcp 库**，业务层（`tools/`、`utils/lark/`）与 mcp 完全解耦，这是迁移成本低的原因。

## 4. 验证结果

### 4.1 依赖版本

```bash
$ uv run python -c "from importlib.metadata import version; print(version('mcp'))"
2.0.0
```

### 4.2 模块导入（无需 LARK 凭证）

```bash
$ uv run python -c "from yuppie_mcp_lark.server import mcp; print(type(mcp).__name__)"
MCPServer
```

### 4.3 48 个工具注册 + 协议握手

通过 mcp 2.0 进程内 Client 做 `tools/list` 协议握手：

```bash
$ uv run python -c "... async with Client(mcp) as client: tools = (await client.list_tools()).tools; print(len(tools))"
工具总数: 48
```

48 个工具名与迁移前完全一致：`message_send`、`drive_*`、`bitable_*`、`sheets_*`、`quick_*`。
`ToolAnnotations` 各字段（title/readOnlyHint 等）在 2.0 中正确填充——2.0 用 snake_case 字段名 +
camelCase alias（`populate_by_name=True`），迁移后统一为 snake_case。

### 4.4 streamable-http 冒烟

启动服务（绑定 127.0.0.1:8137）并发送 `initialize` 请求：

```bash
$ MCP_TRANSPORT=streamable-http MCP_PORT=8137 MCP_HOST=127.0.0.1 uv run yuppie-mcp-lark &
$ curl -s -X POST http://127.0.0.1:8137/mcp \
    -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
    -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"smoke","version":"0"}}}'
```

返回（摘录）：

```json
{"id":1,"result":{"capabilities":{"tools":{...}},
  "instructions":"飞书开放平台工具集：...",
  "protocolVersion":"2025-03-26",
  "serverInfo":{"name":"lark_mcp","version":"0.1.10"}}}
```

`serverInfo.version` 通过构造参数 `version=__version__` 正确上报（迁移前依赖 `mcp._mcp_server.version` 私有属性，2.0 已移除）。

### 4.5 静态检查与测试

| 检查 | 命令 | 结果 |
|---|---|---|
| 单元测试 | `uv run pytest -q` | **89 passed** |
| 代码检查 | `uv run ruff check src/` | **All checks passed** |
| 格式检查 | `uv run ruff format --check src/` | **20 files already formatted** |
| 类型检查 | `uv run mypy src/` | **Success: no issues found in 20 source files** |

## 5. 清理过程中修复的问题

以下均为**迁移前已存在**的债务（经 git stash 基线比对确认），由新版本工具（mypy 2.1.0 / ruff 0.15.16）暴露：

| # | 文件 | 问题 | 修复 |
|---|---|---|---|
| 1 | `utils/lark/sheets_quick.py` | 5 处把 `read_range` 返回值（dict）当 list 用（`headers[0]`、`data[i]`），**运行时必崩 KeyError**（真实 bug） | 改为 `.get("values", [])` |
| 2 | `utils/lark/bitable.py`、`tools/bitable.py`、`server.py`、`utils/lark/base.py` | `search_records` 的 `sort` 类型标注为 `dict`，但飞书实际格式是 `list[dict]`（`[{field_name, desc}]`） | 统一改为 `list[dict[str, Any]] | None` |
| 3 | `utils/lark/base.py` | `_LarkMixinProtocol.quick_sheets_batch_append` 签名缺 `overwrite_start` 参数 | 补齐参数 |
| 4 | `utils/lark/sheets_quick.py` | 过时的 `# type: ignore[comparison-overlap]`（mypy 2.x 不再报该错误） | 删除 |
| 5 | `server.py` | 48 处 `ToolAnnotations(readOnlyHint=...)` camelCase，mypy 2.x 识别 snake_case 规范字段名 | 改为 `read_only_hint` 等 snake_case |
| 6 | `tools/*`、`utils/lark/*` | 15 处 E501 超长行、3 处 F541/W292（ruff --fix） | 手动拆行 / 自动修复 |
| 7 | 9 个文件 | ruff format 风格不统一（既有格式债务） | `ruff format src/` 统一 |

## 6. ⚠️ 接口变化（下游需知晓）

`bitable_search_records` 工具的 `sort` 入参 schema 从 **object 变为 array**：

```json
// 迁移前：object
{"sort": {"field_name": "id", "desc": true}}

// 迁移后：array（符合飞书 API 实际格式）
{"sort": [{"field_name": "id", "desc": true}]}
```

MCP 客户端看到的 schema：`sort: {anyOf: [{type: array, items: {type: object}}, {type: null}]}`。
下游若按旧格式传参，需改为数组形式。

## 7. 结论

- ✅ mcp 2.0.0 适配完成，48 个工具全部正常注册，行为与迁移前一致（工具返回 `str` 自动判定 unstructured）
- ✅ 依赖上限 `mcp>=2.0.0,<3.0.0`，防止未来 3.0 再次破坏
- ✅ 测试 / ruff / ruff format / mypy 全绿
- ✅ 顺带修复 1 个真实运行时 bug（sheets_quick 的 read_range 误用）和 1 处类型标注错误
- ⚠️ 唯一接口变化：`bitable_search_records.sort` 入参 schema object → array

## 8. 建议

- Review 本次 git diff 后提交；发布建议 bump 到 `0.2.0`（破坏性依赖升级），走现有 `scripts/publish.sh`。
- 其他 yuppie 系包（如 `yuppie-mcp-alibabacloud-fnf`）建议同步检查依赖上限，避免同类问题。
