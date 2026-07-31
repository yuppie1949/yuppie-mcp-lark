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

- **`server.py`**: MCP Server 入口，MCPServer 注册 48 个工具
- **`utils/config.py`**: `LarkConfig` 数据类，`from_env()` 读取并校验 `LARK_APP_ID`/`LARK_APP_SECRET`/`LARK_BASE_URL`，自动加载 `.env`
- **`utils/lark/`**: 飞书客户端（mixin 模式）
  - `base.py` — `_LarkBase`：httpx client、tenant_access_token 自动刷新、`_request`/`_get`/`_post`/`_put`、`_index_to_letter`、90217 限流重试；`_LarkMixinProtocol`：mixin 自引用协议
  - `messages.py` — `MessagesMixin`：消息发送
  - `bitable.py` — `BitableMixin`：多维表格记录增删改查、批量操作、应用/表格管理
  - `bitable_quick.py` — `QuickBitableMixin`：多维表格编排型快捷操作（清空数据）
  - `sheets.py` — `SheetsMixin`：通用电子表格操作 + 列查找辅助（`find_sheet_ids`、`_resolve_column_letter`、`_ensure_column`、`_get_sheet_dimensions`）
  - `sheets_quick.py` — `QuickSheetsMixin`：电子表格快捷业务操作（过滤列、批次索引、批量更新等）
  - `__init__.py` — `LarkClient(_LarkBase, MessagesMixin, BitableMixin, QuickBitableMixin, SheetsMixin, QuickSheetsMixin)` 聚合
- **`tools/`**: MCP 工具层（按域分），每个模块持模块级 client 单例，首次调用时懒加载
  - `bitable.py` — 多维表格 MCP 工具
  - `bitable_quick.py` — 多维表格快捷工具
  - `messages.py` — 消息工具
  - `sheets.py` — 电子表格工具
  - `sheets_quick.py` — 电子表格快捷工具
  - 每个工具函数：Pydantic `BaseModel`（`ConfigDict(str_strip_whitespace=True, extra="forbid")`）+ `async def` 实现 + markdown 输出 + try/except 友好错误

### 客户端懒加载

`_get_client()` 首次调用时从环境变量读取配置并构造 `LarkClient`，后续重用。各个 tools 模块各自独立懒加载。

### 传输模式

仅支持 stdio（MCP 主流用法）。可通过 `MCP_TRANSPORT=streamable-http` 环境变量切换为 HTTP 模式。

### API 分层

飞书 OpenAPI 路径前缀统一为 `/open-apis/`，mixin 通过 `self: _LarkMixinProtocol` 类型注解让 mypy 支持跨 mixin 方法调用（MRO 解析）。

## 代码规范

- 使用 `ruff`（line-length = 100，select = E/F/I/W）和 `mypy`（strict = true）
- 异步函数 `async def`，底层 httpx 调用本身即异步
- 所有工具参数通过 Pydantic BaseModel 校验
- 工具返回 markdown 字符串；失败时返回 `❌ ...失败：{异常}`
- 方法命名：通用 API 薄包装用原始名，快捷业务操作前缀 `quick_sheets_` / `quick_bitable_`
- Mixin 中直接返回 `data.get(...)` 的行需要加 `# type: ignore[no-any-return]`；返回字典字面量的不需要

## 添加新工具

1. 在 `utils/lark/<域>.py` 的 mixin 上加飞书 API 薄包装方法（async，参数用 keyword-only）
2. 如果新方法是**编排型**（组合多个 API），放在对应的 `*_quick.py` mixin 中
3. 在 `tools/<域>.py` 加 `*Input(BaseModel)` + async 工具函数 + 模块级 `_get_client`
   - Input 类必须设 `model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")`
4. 在 `server.py` 中：
   - import 新的 Input 类
   - 用 `@mcp.tool(name=..., annotations=ToolAnnotations(...))` 注册
   - 参数用 `Annotated[type, Field(...)]` 声明
5. 在 `tests/test_tools.py` 加 BaseModel 校验测试（required fields、defaults、边界值）
6. 如果新增 mixin 模块，在 `utils/lark/__init__.py` 的 `LarkClient` 继承链中加入
