# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this repository.

## 项目概述

`yuppie-mcp-lark` 是一个 MCP (Model Context Protocol) Server，让 AI 助手通过 MCP 协议操作飞书（Lark / Feishu）。基于飞书 OpenAPI（`tenant_access_token` 鉴权），覆盖消息、多维表格、电子表格三大业务域。

## 开发命令

```bash
# 安装开发依赖
uv pip install -e ".[dev]"

# 运行测试
uv run pytest -v

# 代码检查
ruff check src/
ruff format --check src/

# 类型检查
mypy src/

# 本地运行 MCP Server（stdio 模式）
LARK_APP_ID=cli_xxx LARK_APP_SECRET=xxx uv run yuppie-mcp-lark
```

## 架构设计

### 核心模块

- **`server.py`**: MCP Server 入口，FastMCP 注册 17 个工具
- **`utils/config.py`**: `LarkConfig` 数据类，`from_env()` 读取并校验 `LARK_APP_ID`/`LARK_APP_SECRET`/`LARK_BASE_URL`，自动加载 `.env`
- **`utils/lark/`**: 飞书客户端（mixin 模式）
  - `base.py` — `_LarkBase`：httpx client、tenant_access_token 自动刷新、`_request`/`_get`/`_post`/`_put`、`_index_to_letter`、90217 限流重试
  - `messages.py` — `MessagesMixin`：消息发送
  - `bitable.py` — `BitableMixin`：多维表格记录搜索
  - `sheets.py` — `SheetsMixin`：通用电子表格操作 + 列查找辅助（`find_sheet_ids`、`_resolve_column_letter`、`_ensure_column`、`_get_sheet_dimensions`）
  - `sheets_quick.py` — `QuickSheetsMixin`：电子表格快捷业务操作（过滤列、批次索引、批量更新等）
  - `__init__.py` — `LarkClient(_LarkBase, MessagesMixin, BitableMixin, SheetsMixin, QuickSheetsMixin)` 聚合
- **`tools/`**: MCP 工具层（按域分），每个模块持模块级 client 单例，首次调用时懒加载
  - 每个工具：Pydantic `BaseModel`（`str_strip_whitespace` + `extra="forbid"`）+ `async def` 实现 + markdown 输出 + try/except 友好错误

### 客户端懒加载

`_get_client()` 首次调用时从环境变量读取配置并构造 `LarkClient`，后续重用。三个 tools 模块各自独立懒加载。

### 传输模式

仅支持 stdio（MCP 主流用法）。`server.py` 直接 `mcp.run()`。

## 代码规范

- 使用 `ruff`（line-length = 100）和 `mypy`（strict = true）
- 异步函数 `async def`，底层 httpx 调用本身即异步
- 所有工具参数通过 Pydantic BaseModel 校验
- 工具返回 markdown 字符串；失败时返回 `❌ ...失败：{异常}`
- 方法命名：通用 API 薄包装用原始名，快捷业务操作前缀 `quick_sheets_`

## 添加新工具

1. 在 `utils/lark/<域>.py` 的 mixin 上加飞书 API 薄包装方法
2. 在 `tools/<域>.py` 加 BaseModel + async 实现 + 模块级 `_get_client`
3. 在 `server.py` 用 `@mcp.tool(name=..., annotations=ToolAnnotations(...))` 注册，参数用 `Annotated[type, Field(...)]`
4. 在 `tests/test_tools.py` 加 BaseModel 校验测试
