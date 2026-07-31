# MCP Python SDK 1.x → 2.0 迁移指南

> **适用范围**：所有基于 mcp Python SDK 1.x（`from mcp.server.fastmcp import FastMCP`）的 MCP Server 项目。
> **参照案例**：yuppie-mcp-lark（2026-07-31 完成迁移，验证报告见 `MCP_2.0_MIGRATION_VERIFICATION.md`）。
> **官方迁移文档**：https://py.sdk.modelcontextprotocol.io/v2/migration

---

## 0. 问题背景：为什么要迁移

mcp **2.0.0**（2026-07-28 发布，requires Python >=3.10）是破坏性大版本。如果你的依赖声明无上限：

```toml
mcp>=1.0.0   # ⚠️ 危险写法
```

在**干净环境**（CI、uvx runtime、新机器）重新安装时，解析器会装到 mcp 2.0，启动即崩溃：

```
ModuleNotFoundError: No module named 'mcp.server.fastmcp'
```

两个选择：

| 方案 | 说明 | 适用场景 |
|---|---|---|
| **A. 锁 1.x（临时应急）** | `mcp>=1.0.0,<2.0.0` | 立即恢复服务，无需改代码 |
| **B. 适配 2.0（推荐，长期）** | 按本指南迁移 | 一劳永逸，避免依赖长期停留在旧版本 |

---

## 1. 破坏性变化一览

| # | 1.x | 2.0 | 影响 |
|---|---|---|---|
| 1 | `mcp.server.fastmcp.FastMCP` | **移除**，替代 `MCPServer`（`from mcp.server import MCPServer` 或 `from mcp.server.mcpserver import MCPServer`） | 必须改 import |
| 2 | 构造函数 `host=...` / `port=...` | **移到 `run()`**，构造函数只剩身份与配置（name/version/instructions 等） | 必须改构造函数 + main() |
| 3 | `mcp._mcp_server.version = x` | 私有属性不存在，改用构造参数 `version=` | 必须改 |
| 4 | `mcp.settings.port = x` | `settings` 无 transport 字段（只有 debug/log_level/warn_on_duplicate_*） | 必须改 main() |
| 5 | `mcp.types` 模块 | 变为独立包 `mcp-types` 的镜像命名空间（`from mcp_types import *`），**`from mcp.types import ...` 仍可用** | import 兼容，无需改 |
| 6 | `ToolAnnotations` 字段 `readOnlyHint` 等 camelCase | 规范字段名改为 snake_case（`read_only_hint` 等）；**运行时 camelCase 仍兼容**（`populate_by_name=True`），但 **mypy 2.x 会报错** | 建议改 snake_case |
| 7 | `@mcp.tool` 不带括号（旧版允许） | **必须带括号** `@mcp.tool()`，直接传函数会抛 TypeError | 检查装饰器写法 |
| 8 | `client.list_tools()` 返回 `list[Tool]` | 返回 `ListToolsResult`（含 `.tools` 属性） | 仅影响客户端/验证脚本 |
| 9 | 依赖面 | 新增 `mcp-types`、`httpx2`、`pydantic>=2.12.0` 等 | 依赖会变多 |
| 10 | 依赖上限 | 无上限会被 3.0 再次破坏 | **必须设 `<3.0.0`** |

---

## 2. 迁移步骤（按序执行）

### 步骤 1：更新依赖（pyproject.toml）

```diff
- "mcp>=1.0.0",
+ "mcp>=2.0.0,<3.0.0",
```

> **务必设 `<3.0.0` 上限**。1.x → 2.0 的教训正是无上限导致静默拉进破坏性大版本。

### 步骤 2：改 import

```diff
-from mcp.server.fastmcp import FastMCP
-from mcp.types import ToolAnnotations
+from mcp.server.mcpserver import MCPServer
+from mcp.types import ToolAnnotations   # 2.0 中仍可导入（mcp_types 镜像）
```

### 步骤 3：改构造函数 + 版本设置

```diff
-mcp = FastMCP(
-    name="my_mcp",
-    host=os.getenv("MCP_HOST", "127.0.0.1"),   # 移除：host 移到 run()
-    instructions=("..."),
-)
-mcp._mcp_server.version = __version__          # 移除：私有属性不存在
+mcp = MCPServer(
+    name="my_mcp",
+    instructions=("..."),
+    version=__version__,                        # 改用构造参数，未设置时上报空串
+)
```

### 步骤 4：改 main() / transport 处理

```diff
 def main() -> None:
     transport = os.getenv("MCP_TRANSPORT", "stdio")
     if transport == "streamable-http":
-        mcp.settings.port = int(os.getenv("MCP_PORT", "8000"))
-        mcp.run(transport="streamable-http")
+        mcp.run(
+            transport="streamable-http",
+            host=os.getenv("MCP_HOST", "127.0.0.1"),
+            port=int(os.getenv("MCP_PORT", "8000")),
+        )
     else:
-        mcp.run()
+        mcp.run()                              # stdio 默认，无需参数；run() 仍是同步阻塞函数
```

> `run()` 签名：`run(transport="stdio"/"sse"/"streamable-http", **kwargs)`，HTTP 模式的 host/port/路径通过 kwargs 传。默认路径为 `/mcp`。

### 步骤 5：`ToolAnnotations` 字段改 snake_case（48 处机械替换）

2.0 规范字段名是 snake_case。运行时 camelCase 也接受，但 mypy 2.x 会报 `Unexpected keyword argument "readOnlyHint" ... did you mean "read_only_hint"?`，所以直接改成 snake_case：

```diff
 ToolAnnotations(
     title="发送消息",
-    readOnlyHint=False,
-    destructiveHint=False,
-    idempotentHint=False,
-    openWorldHint=True,
+    read_only_hint=False,
+    destructive_hint=False,
+    idempotent_hint=False,
+    open_world_hint=True,
 )
```

> 每个工具的 `@mcp.tool(name=..., annotations=ToolAnnotations(...))` **装饰器参数本身不变**（name/annotations/title/description 均保留），只改 ToolAnnotations 内的字段名。

### 步骤 6：重新解析依赖并安装

```bash
uv lock && uv sync --extra dev
uv run python -c "from importlib.metadata import version; print(version('mcp'))"   # 期望 2.0.0
```

> 2.0 会引入新的传递依赖（mcp-types、httpx2、pydantic>=2.12 等），`uv lock` 自动处理。注意 `httpx2` 与项目自带的 `httpx` 是不同包，共存不冲突。

### 步骤 7：全量验证（见第 4 节）

---

## 3. 常见坑点

1. **`mcp.settings.port` / `mcp._mcp_server` 直接用会崩** —— 前者 `Settings` 无 port 字段抛错，后者属性不存在，必须同时改掉（步骤 3、4）。
2. **ToolAnnotations camelCase 运行时 OK、mypy 报错** —— 建议统一改 snake_case，别和 mypy 较劲。
3. **`structured_output` 自动检测** —— 返回 `str` 的工具自动判定为 unstructured，行为与 1.x 一致，无需显式传 `structured_output=False`。
4. **`mcp.types` 仍是合法 import** —— 2.0 中它是 `mcp_types` 独立包的完整镜像；若 mypy 对通配镜像解析有疑问，可改 `from mcp_types import ToolAnnotations`（`mcp_types` 是 mcp 2.0 直接依赖）。
5. **pydantic 会被提升到 >=2.12.0** —— 项目若用 `BaseModel`/`Field`/`ConfigDict`，2.x 下稳定；若有特殊 pydantic 用法需回归测试。
6. **`@mcp.tool()` 必须带括号** —— 检查所有装饰器都写了括号。
7. **`mypy`/`ruff` 升级可能暴露既有债务** —— `uv sync` 会装最新 mypy/ruff，旧代码里隐藏的类型/格式问题可能一次性浮现（yuppie-mcp-lark 迁移时顺带修复了 20+ 处既有问题），建议迁移时一并清理。

---

## 4. 验证清单（全部通过才算完成）

```bash
# 1) 依赖版本
uv run python -c "from importlib.metadata import version; print(version('mcp'))"
#    → 2.0.0

# 2) 模块可导入（无需业务凭证，客户端懒加载）
uv run python -c "from your_pkg.server import mcp; print(type(mcp).__name__)"
#    → MCPServer

# 3) 枚举所有工具（进程内 Client，无需凭证）
uv run python -c "
import asyncio
from mcp import Client
from your_pkg.server import mcp
async def main():
    async with Client(mcp) as client:
        result = await client.list_tools()
        print('工具数:', len(result.tools))   # 注意 2.0 返回 ListToolsResult，取 .tools
        for t in result.tools: print(t.name)
asyncio.run(main())
"
#    → 工具数与迁移前一致

# 4) 静态检查 + 测试
uv run pytest -q
uv run ruff check src/
uv run ruff format --check src/
uv run mypy src/

# 5) streamable-http 冒烟（验证 run() 的 host/port 生效 + serverInfo.version 上报）
MCP_TRANSPORT=streamable-http MCP_PORT=8000 uv run your-mcp-server &
curl -s -X POST http://127.0.0.1:8000/mcp \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"smoke","version":"0"}}}'
#    → 响应里 serverInfo.version 应为你的 __version__，非空串
```

---

## 5. 参考

- 官方 v2 API 文档：https://py.sdk.modelcontextprotocol.io/v2
- 官方迁移说明：https://py.sdk.modelcontextprotocol.io/v2/migration
- 实迁移案例（含踩坑与修复明细）：`MCP_2.0_MIGRATION_VERIFICATION.md`
