# yuppie-mcp-lark

飞书（Lark / Feishu）MCP Server — 让 AI 助手通过 MCP 协议操作飞书消息、多维表格、电子表格。

## 特性

- 消息：发送单聊/群聊消息
- 多维表格：搜索记录（支持分页、排序、过滤）
- 电子表格：元信息查询、工作表增删复制、范围读写、追加数据、删除行列
- 快捷操作：列过滤、批次索引、批量更新、批量追加、按批次读取
- 鉴权：基于飞书应用 `tenant_access_token`，自动刷新
- 部署：仅 stdio，本地 AI 助手友好

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

## 可用工具（共 17 个）

### 消息

| 工具 | 说明 |
|------|------|
| `lark_send_message` | 发送消息（支持 text/post/image/interactive 等） |

### 多维表格

| 工具 | 说明 |
|------|------|
| `lark_search_records` | 搜索记录（支持分页、排序、过滤） |

### 电子表格通用

| 工具 | 说明 |
|------|------|
| `lark_get_spreadsheet_metainfo` | 获取电子表格元信息 |
| `lark_add_sheet` | 添加工作表 |
| `lark_delete_sheet` | 删除工作表 |
| `lark_copy_sheet` | 复制工作表 |
| `lark_read_range` | 读取范围数据 |
| `lark_write_range` | 写入范围数据 |
| `lark_append_data` | 追加数据 |
| `lark_delete_dimension` | 删除行列 |

### 电子表格快捷操作

| 工具 | 说明 |
|------|------|
| `lark_quick_filter_sheet_columns` | 只保留指定列，删除其余列 |
| `lark_quick_set_batch_index` | 按列设置批次索引 |
| `lark_quick_set_header_list` | 写入新表头 |
| `lark_quick_get_column_last_value` | 获取列最后一个非空值 |
| `lark_quick_get_rows_by_batch` | 按批次读取行 |
| `lark_quick_batch_update` | 批量更新行 |
| `lark_quick_batch_append` | 批量追加行 |

## 测试与调试

```bash
uv pip install -e ".[dev]"
uv run pytest -v
```

使用 MCP Inspector 调试（需先在 `.env` 配置 `LARK_APP_ID` / `LARK_APP_SECRET`）：

```bash
npx @modelcontextprotocol/inspector uv run yuppie-mcp-lark
```

## License

MIT
