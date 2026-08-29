# yuppie-lark

飞书（Lark / Feishu）OpenAPI 客户端库，基于 `tenant_access_token` 鉴权，覆盖消息、多维表格、电子表格、云文档（Drive）四大业务域。异步（httpx），无 MCP 依赖。

## 安装

```bash
pip install yuppie-lark
```

## 快速开始

```python
import asyncio

from yuppie_lark import LarkClient, LarkConfig

async def main() -> None:
    client = LarkClient(LarkConfig.from_env())  # 读取 LARK_APP_ID / LARK_APP_SECRET / LARK_BASE_URL
    resp = await client.send_message(
        receive_id_type="open_id",
        receive_id="ou_xxx",
        msg_type="text",
        content='{"text": "hello"}',
    )
    print(resp)

asyncio.run(main())
```

环境变量：

- `LARK_APP_ID`（必填）
- `LARK_APP_SECRET`（必填）
- `LARK_BASE_URL`（可选，默认 `https://open.feishu.cn`）

## 能力域

| Mixin | 能力 |
|-------|------|
| `MessagesMixin` | 消息发送 |
| `BitableMixin` / `QuickBitableMixin` | 多维表格记录增删改查、批量操作、应用/表格管理 |
| `SheetsMixin` / `QuickSheetsMixin` | 电子表格读写、格式、批量操作 |
| `DriveMixin` | 云文档/文件夹管理、上传下载 |

详细 API 见各模块 docstring。

## 相关

本包是 `yuppie-mcp-lark`（MCP Server 壳包）的底层客户端库。若要用 MCP 方式操作飞书，请安装：

```bash
pip install yuppie-mcp-lark
```
