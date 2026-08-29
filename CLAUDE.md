# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this repository.

## 项目概述

`yuppie-mcp-lark` 仓库拆分为双包（uv workspace）：

- **`yuppie-lark`**（`packages/yuppie-lark/`）：飞书 OpenAPI 客户端纯库（`tenant_access_token` 鉴权），覆盖消息、多维表格、电子表格、云文档（Drive）四大业务域。**无 MCP、无 pydantic 依赖**，PyPI 分发，可单独 `pip install yuppie-lark`
- **`yuppie-mcp-lark`**（`packages/yuppie-mcp-lark/`）：MCP Server 壳包，deps 声明 `yuppie-lark>=0.1.0`，PyPI 分发

## 开发命令

```bash
# 安装开发依赖（workspace 全包）
uv sync --all-packages --all-extras

# 运行测试
uv run pytest -v

# 代码检查
uv run ruff check packages/ tests/
uv run ruff format --check packages/

# 类型检查
uv run mypy packages/*/src

# 本地运行 MCP Server（stdio 模式）
LARK_APP_ID=cli_xxx LARK_APP_SECRET=xxx uv run yuppie-mcp-lark
```

## 架构设计

### 目录结构

```
packages/
├── yuppie-lark/src/yuppie_lark/     # 库包（客户端纯库，无 mcp）
│   ├── __init__.py                  # LarkClient mixin 聚合 + LarkConfig re-export
│   ├── config.py                    # LarkConfig 数据类
│   ├── base.py                      # _LarkBase：httpx client、token 刷新、_request、90217 限流重试
│   ├── messages.py                  # MessagesMixin：消息发送 + 卡片发送/更新（send_card/update_card）
│   ├── bitable.py                   # BitableMixin：多维表格记录增删改查、批量操作
│   ├── bitable_quick.py             # QuickBitableMixin：多维表格编排型快捷操作
│   ├── drive.py                     # DriveMixin：云文档/文件夹管理
│   ├── sheets.py                    # SheetsMixin：通用电子表格操作
│   └── sheets_quick.py              # QuickSheetsMixin：电子表格快捷业务操作
└── yuppie-mcp-lark/src/yuppie_mcp_lark/   # 壳包（MCP 工具层）
    ├── __init__.py                  # __version__
    ├── server.py                    # 唯一 import mcp 的文件，MCPServer 注册 50 个工具
    ├── __main__.py
    └── tools/                       # MCP 工具层（按域分），模块级 client 单例懒加载
```

### 客户端懒加载

`tools/` 各模块持有模块级 `LarkClient` 单例，首次调用时从环境变量读取配置并构造，后续重用。

### 传输模式

仅支持 stdio（MCP 主流用法）。可通过 `MCP_TRANSPORT=streamable-http` 环境变量切换为 HTTP 模式。

### API 分层

库包 mixin 通过 `self: _LarkMixinProtocol` 类型注解让 mypy 支持跨 mixin 方法调用（MRO 解析）；tools 层经壳包 `yuppie_mcp_lark` 依赖的 `yuppie_lark` 导入客户端。

## 代码规范

- 使用 `ruff`（line-length = 100，select = E/F/I/W）和 `mypy`（strict = true）
- 异步函数 `async def`，底层 httpx 调用本身即异步
- 所有 MCP 工具参数通过 Pydantic BaseModel 校验（仅壳包 tools 层用 pydantic）
- 工具返回 markdown 字符串；失败时返回 `❌ ...失败：{异常}`
- 方法命名：通用 API 薄包装用原始名，快捷业务操作前缀 `quick_sheets_` / `quick_bitable_`
- Mixin 中直接返回 `data.get(...)` 的行需要加 `# type: ignore[no-any-return]`；返回字典字面量的不需要

## 添加新工具

1. 在库包 `packages/yuppie-lark/src/yuppie_lark/<域>.py` 的 mixin 上加飞书 API 薄包装方法（async，参数用 keyword-only）
2. 如果新方法是**编排型**（组合多个 API），放在对应的 `*_quick.py` mixin 中
3. 在壳包 `packages/yuppie-mcp-lark/src/yuppie_mcp_lark/tools/<域>.py` 加 `*Input(BaseModel)` + async 工具函数 + 模块级 `_get_client`
   - Input 类必须设 `model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")`
4. 在壳包 `server.py` 中：
   - import 新的 Input 类
   - 用 `@mcp.tool(name=..., annotations=ToolAnnotations(...))` 注册
   - 参数用 `Annotated[type, Field(...)]` 声明
5. 在 `tests/test_tools.py` 加 BaseModel 校验测试（required fields、defaults、边界值）
6. 如果新增 mixin 模块，在库包 `__init__.py` 的 `LarkClient` 继承链中加入
