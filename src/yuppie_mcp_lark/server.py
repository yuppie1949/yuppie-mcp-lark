"""飞书 MCP Server 主入口"""

import os
from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .tools import bitable, messages, sheets
from .tools.bitable import SearchRecordsInput
from .tools.messages import SendMessageInput
from .tools.sheets import (
    AddSheetInput,
    AppendDataInput,
    CopySheetInput,
    DeleteDimensionInput,
    DeleteSheetInput,
    GetMetainfoInput,
    ReadRangeInput,
    WriteRangeInput,
)

mcp = FastMCP("lark_mcp")


@mcp.tool(
    name="lark_send_message",
    annotations=ToolAnnotations(
        title="发送飞书消息",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_send_message(
    receive_id: Annotated[str, Field(description="接收者 ID", min_length=1)],
    content: Annotated[str, Field(description="消息内容 JSON 字符串", min_length=1)],
    msg_type: Annotated[str, Field(description="消息类型，默认 text")] = "text",
    receive_id_type: Annotated[
        str,
        Field(description="ID 类型：open_id / user_id / union_id / chat_id"),
    ] = "open_id",
) -> str:
    """发送消息给单个用户或群。

    content 是 JSON 字符串，例如 text 类型消息：'{"text":"你好"}'。
    """
    return await messages.send_message(
        SendMessageInput(
            receive_id=receive_id,
            msg_type=msg_type,
            content=content,
            receive_id_type=receive_id_type,
        )
    )


@mcp.tool(
    name="lark_search_records",
    annotations=ToolAnnotations(
        title="搜索多维表格记录",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def tool_search_records(
    app_token: Annotated[str, Field(description="多维表格 app_token", min_length=1)],
    table_id: Annotated[str, Field(description="数据表 table_id", min_length=1)],
    view_id: Annotated[str | None, Field(description="视图 ID")] = None,
    field_names: Annotated[list[str] | None, Field(description="指定返回字段名列表")] = None,
    sort: Annotated[dict[str, Any] | None, Field(description="排序规则")] = None,
    filter: Annotated[dict[str, Any] | None, Field(description="过滤条件")] = None,
    page_token: Annotated[str | None, Field(description="分页 token")] = None,
    page_size: Annotated[int | None, Field(description="分页大小（1-500）", ge=1, le=500)] = None,
    automatic_fields: Annotated[bool | None, Field(description="是否返回自动计算字段")] = None,
    user_id_type: Annotated[
        str | None,
        Field(description="用户 ID 类型：open_id / user_id / union_id"),
    ] = None,
) -> str:
    """搜索多维表格记录，返回 markdown 表格。支持分页、排序、过滤。"""
    return await bitable.search_records(
        SearchRecordsInput(
            app_token=app_token,
            table_id=table_id,
            view_id=view_id,
            field_names=field_names,
            sort=sort,
            filter=filter,
            page_token=page_token,
            page_size=page_size,
            automatic_fields=automatic_fields,
            user_id_type=user_id_type,
        )
    )


@mcp.tool(
    name="lark_get_spreadsheet_metainfo",
    annotations=ToolAnnotations(
        title="获取电子表格元信息",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def tool_get_metainfo(
    spreadsheet_token: Annotated[
        str, Field(description="电子表格 token", min_length=1)
    ],
) -> str:
    """获取电子表格元信息，含工作表列表（标题、sheetId、行数、列数）。"""
    return await sheets.get_metainfo(GetMetainfoInput(spreadsheet_token=spreadsheet_token))


@mcp.tool(
    name="lark_add_sheet",
    annotations=ToolAnnotations(
        title="添加工作表",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_add_sheet(
    spreadsheet_token: Annotated[
        str, Field(description="电子表格 token", min_length=1)
    ],
    title: Annotated[str, Field(description="新工作表标题", min_length=1)],
) -> str:
    """添加工作表，返回新 sheetId。"""
    return await sheets.add_sheet(
        AddSheetInput(spreadsheet_token=spreadsheet_token, title=title)
    )


@mcp.tool(
    name="lark_delete_sheet",
    annotations=ToolAnnotations(
        title="删除工作表",
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_delete_sheet(
    spreadsheet_token: Annotated[
        str, Field(description="电子表格 token", min_length=1)
    ],
    sheet_id: Annotated[str, Field(description="工作表 ID", min_length=1)],
) -> str:
    """删除指定工作表。"""
    return await sheets.delete_sheet(
        DeleteSheetInput(spreadsheet_token=spreadsheet_token, sheet_id=sheet_id)
    )


@mcp.tool(
    name="lark_copy_sheet",
    annotations=ToolAnnotations(
        title="复制工作表",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_copy_sheet(
    spreadsheet_token: Annotated[
        str, Field(description="电子表格 token", min_length=1)
    ],
    source_sheet_id: Annotated[str, Field(description="源工作表 ID", min_length=1)],
    title: Annotated[str, Field(description="新工作表标题", min_length=1)],
) -> str:
    """复制工作表，返回新 sheetId。"""
    return await sheets.copy_sheet(
        CopySheetInput(
            spreadsheet_token=spreadsheet_token,
            source_sheet_id=source_sheet_id,
            title=title,
        )
    )


@mcp.tool(
    name="lark_read_range",
    annotations=ToolAnnotations(
        title="读取电子表格范围",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def tool_read_range(
    spreadsheet_token: Annotated[
        str, Field(description="电子表格 token", min_length=1)
    ],
    range_str: Annotated[
        str, Field(description="范围，如 Sheet1!A1:C10", min_length=1)
    ],
) -> str:
    """读取单个范围数据，返回 markdown 表格（超过 10 行仅预览前 10 行）。"""
    return await sheets.read_range(
        ReadRangeInput(spreadsheet_token=spreadsheet_token, range_str=range_str)
    )


@mcp.tool(
    name="lark_write_range",
    annotations=ToolAnnotations(
        title="写入电子表格范围",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_write_range(
    spreadsheet_token: Annotated[
        str, Field(description="电子表格 token", min_length=1)
    ],
    range_str: Annotated[str, Field(description="范围", min_length=1)],
    values: Annotated[list[list[Any]], Field(description="二维数组")],
) -> str:
    """向单个范围写入数据（≤5000 行、100 列）。"""
    return await sheets.write_range(
        WriteRangeInput(
            spreadsheet_token=spreadsheet_token,
            range_str=range_str,
            values=values,
        )
    )


@mcp.tool(
    name="lark_append_data",
    annotations=ToolAnnotations(
        title="追加电子表格数据",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_append_data(
    spreadsheet_token: Annotated[
        str, Field(description="电子表格 token", min_length=1)
    ],
    sheet_id: Annotated[str, Field(description="工作表 ID", min_length=1)],
    values: Annotated[list[list[Any]], Field(description="二维数组")],
) -> str:
    """追加数据到工作表（自动找空白位置写入）。"""
    return await sheets.append_data(
        AppendDataInput(
            spreadsheet_token=spreadsheet_token,
            sheet_id=sheet_id,
            values=values,
        )
    )


@mcp.tool(
    name="lark_delete_dimension",
    annotations=ToolAnnotations(
        title="删除电子表格行列",
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_delete_dimension(
    spreadsheet_token: Annotated[
        str, Field(description="电子表格 token", min_length=1)
    ],
    sheet_id: Annotated[str, Field(description="工作表 ID", min_length=1)],
    start_index: Annotated[int, Field(description="起始索引（1-based 含）", ge=1)],
    end_index: Annotated[int, Field(description="结束索引（1-based 含）", ge=1)],
    major_dimension: Annotated[
        str, Field(description="COLUMNS 或 ROWS，默认 COLUMNS")
    ] = "COLUMNS",
) -> str:
    """删除行或列（1-based 含首尾，单次最多 5000 行/列）。"""
    return await sheets.delete_dimension(
        DeleteDimensionInput(
            spreadsheet_token=spreadsheet_token,
            sheet_id=sheet_id,
            major_dimension=major_dimension,
            start_index=start_index,
            end_index=end_index,
        )
    )


def main() -> None:
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    if transport == "streamable-http":
        mcp.settings.port = int(os.getenv("MCP_PORT", "8000"))
        mcp.run(transport="streamable-http")
    else:
        mcp.run()


if __name__ == "__main__":
    main()
