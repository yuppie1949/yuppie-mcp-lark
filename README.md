# yuppie-mcp-lark

飞书（Lark / Feishu）MCP Server — 让 AI 助手通过 MCP 协议操作飞书消息、多维表格、电子表格。

## 特性

- **消息**：发送单聊/群聊消息（文本、富文本、卡片、图片等）
- **多维表格**：记录增删改查、批量操作、应用/数据表管理
- **电子表格**：元信息查询、工作表增删复制、范围读写、追加数据、删除行列
- **快捷操作**：列过滤、批次索引、批量更新/追加、按批次读取、从 CSV 同步、清空多维表格
- **鉴权**：基于飞书应用 `tenant_access_token`，自动刷新
- **部署**：仅 stdio，本地 AI 助手友好

## 快速开始

### Claude Code

在 `.mcp.json` 中添加（`--refresh` 强制拉取 PyPI 最新版，忽略本地缓存）：

```json
{
  "mcpServers": {
    "lark": {
      "type": "stdio",
      "command": "uvx",
      "args": ["--refresh", "yuppie-mcp-lark"],
      "env": {
        "LARK_APP_ID": "cli_xxx",
        "LARK_APP_SECRET": "xxx"
      }
    }
  }
}
```

### Cursor

在 `~/.cursor/mcp.json` 中添加同上配置。

### Cherry Studio / Claude Desktop / OpenCode

参照上方 env 字段，按各自 MCP 配置格式填入即可。

## 环境变量

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `LARK_APP_ID` | 是 | - | 飞书应用 App ID |
| `LARK_APP_SECRET` | 是 | - | 飞书应用 App Secret |
| `LARK_BASE_URL` | 否 | `https://open.feishu.cn` | 国际版设为 `https://open.larksuite.com` |

## 可用工具（共 50 个）

### 消息

| 工具 | 说明 |
|------|------|
| `message_send` | 发送消息（支持 text/post/image/interactive 等） |
| `card_send` | 发送卡片消息（interactive，card 传卡片 schema 对象） |
| `card_update` | 原地更新已发送的卡片（PATCH） |

### 云文档

| 工具 | 说明 |
|------|------|
| `drive_copy_file` | 复制文件到指定文件夹 |
| `drive_delete_file` | 删除文件或文件夹 |
| `drive_check_task` | 查询异步任务状态 |
| `drive_upload_file` | 上传文件到云空间（最大 20 MB） |
| `drive_list_files` | 获取文件夹中的文件清单 |
| `drive_create_folder` | 创建文件夹 |

### 多维表格

| 工具 | 说明 |
|------|------|
| `bitable_search_records` | 搜索记录（支持分页、排序、过滤） |
| `bitable_create_record` | 创建记录 |
| `bitable_update_record` | 更新记录 |
| `bitable_delete_record` | 删除记录 |
| `bitable_batch_create_records` | 批量创建记录（最多 500 条） |
| `bitable_batch_update_records` | 批量更新记录（最多 500 条） |
| `bitable_batch_get_records` | 批量获取记录（最多 100 条） |
| `bitable_batch_delete_records` | 批量删除记录（最多 500 条） |
| `bitable_create_app` | 创建多维表格应用 |
| `bitable_copy_app` | 复制多维表格应用 |
| `bitable_create_table` | 新建数据表 |
| `bitable_delete_table` | 删除数据表 |

### 多维表格快捷操作

| 工具 | 说明 |
|------|------|
| `quick_bitable_clear` | 清空多维表格数据（分页批量删除，支持筛选） |

### 电子表格通用

| 工具 | 说明 |
|------|------|
| `sheets_get_metainfo` | 获取电子表格元信息 |
| `sheets_get_spreadsheet` | 获取电子表格 v3 信息 |
| `sheets_query_sheets` | 查询所有工作表 |
| `sheets_add_sheet` | 添加工作表 |
| `sheets_delete_sheet` | 删除工作表 |
| `sheets_copy_sheet` | 复制工作表 |
| `sheets_create_spreadsheet` | 创建电子表格 |
| `sheets_read_range` | 读取单范围数据 |
| `sheets_read_ranges` | 读取多范围数据 |
| `sheets_write_range` | 写入范围数据 |
| `sheets_write_image` | 向单元格写入图片 |
| `sheets_append_data` | 追加数据 |
| `sheets_delete_dimension` | 删除行列 |
| `sheets_update_dimension` | 更新行列属性（行高/列宽/显示隐藏） |
| `sheets_styles_batch_update` | 批量设置单元格样式 |

### 电子表格快捷操作

| 工具 | 说明 |
|------|------|
| `quick_sheets_filter_columns` | 只保留指定列，删除其余列 |
| `quick_sheets_set_batch_index` | 按列设置批次索引 |
| `quick_sheets_set_header_list` | 写入新表头 |
| `quick_sheets_get_column_last_value` | 获取列最后一个非空值 |
| `quick_sheets_get_rows_by_batch` | 按批次读取行 |
| `quick_sheets_batch_update` | 批量更新行 |
| `quick_sheets_batch_append` | 批量追加行 |
| `quick_sheets_sync_from_file` | 从 CSV 文件同步数据 |
| `quick_sheets_clear_content` | 清空工作表内容（不移除行） |
| `quick_sheets_clear_sheet` | 清空工作表数据（删除行） |
| `quick_sheets_write_image` | 向单元格写入图片（网络/本地/base64） |
| `quick_sheets_set_row_height` | 设置工作表的行高（自动分批） |
| `quick_sheets_set_column_style` | 批量设置列样式（自动分批） |

## 测试与调试

```bash
uv pip install -e ".[dev]"
uv run pytest -v
```

使用 MCP Inspector 调试（需先在 `.env` 配置 `LARK_APP_ID` / `LARK_APP_SECRET`）：

```bash
npx @modelcontextprotocol/inspector uv run yuppie-mcp-lark
```

## 作为库使用

本仓库拆分为双包：`yuppie-mcp-lark`（MCP 壳包，本 README）+ `yuppie-lark`（飞书客户端纯库，无 MCP 依赖）。若只想在代码里调用飞书客户端而不引入 MCP：

```bash
pip install yuppie-lark
```

```python
import asyncio
from yuppie_lark import LarkClient, LarkConfig

async def main() -> None:
    client = LarkClient(LarkConfig.from_env())
    resp = await client.send_message(
        receive_id="ou_xxx", msg_type="text", content='{"text": "hello"}'
    )
    print(resp)

asyncio.run(main())
```

## License

MIT
