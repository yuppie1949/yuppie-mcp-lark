"""飞书 MCP Server 主入口"""

import os
from typing import Annotated, Any, Literal

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from . import __version__
from .tools import bitable, messages, sheets, sheets_quick
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
from .tools.sheets_quick import (
    SyncFromFileInput,
    BatchAppendInput,
    BatchUpdateInput,
    ClearSheetContentInput,
    ClearSheetInput,
    FilterSheetColumnsInput,
    GetColumnLastValueInput,
    GetRowsByBatchInput,
    SetBatchIndexInput,
    SetHeaderListInput,
)

mcp = FastMCP("lark_mcp")
mcp._mcp_server.version = __version__


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
    content: Annotated[
        str,
        Field(
            description="消息内容 JSON 字符串，文本≤150KB，卡片/富文本≤30KB",
            min_length=1,
            max_length=30000,
        ),
    ],
    msg_type: Annotated[
        Literal[
            "text",
            "post",
            "image",
            "file",
            "audio",
            "media",
            "interactive",
        ],
        Field(description="消息类型，默认 text"),
    ] = "text",
    receive_id_type: Annotated[
        str,
        Field(description="ID 类型：open_id / user_id / union_id / chat_id"),
    ] = "open_id",
    uuid: Annotated[
        str | None,
        Field(description="去重序列号，相同 uuid 在 1 小时内至多发送一条消息", max_length=50),
    ] = None,
) -> str:
    """发送消息给单个用户或群。

    content 是 JSON 字符串，不同 msg_type 的 content 格式：

    1. text（文本）:
       {"text":"你好"}

    2. interactive（卡片，支持 markdown、at 等）:
       {"elements":[{"tag":"markdown","content":"普通文本\\n\\n<at id=\\"all\\"></at>"}]}

    3. post（富文本）:
       {"zh_cn":{"title":"标题","content":[[{"tag":"text","text":"内容"}]]}}

    4. image（图片）:
       {"image_key":"img_xxxxx"}
    """
    return await messages.send_message(
        SendMessageInput(
            receive_id=receive_id,
            msg_type=msg_type,
            content=content,
            receive_id_type=receive_id_type,
            uuid=uuid,
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
    spreadsheet_token: Annotated[str, Field(description="电子表格 token", min_length=1)],
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
    spreadsheet_token: Annotated[str, Field(description="电子表格 token", min_length=1)],
    title: Annotated[str, Field(description="新工作表标题", min_length=1)],
) -> str:
    """添加工作表，返回新 sheetId。"""
    return await sheets.add_sheet(AddSheetInput(spreadsheet_token=spreadsheet_token, title=title))


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
    spreadsheet_token: Annotated[str, Field(description="电子表格 token", min_length=1)],
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
    spreadsheet_token: Annotated[str, Field(description="电子表格 token", min_length=1)],
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
    spreadsheet_token: Annotated[str, Field(description="电子表格 token", min_length=1)],
    range_str: Annotated[str, Field(description="范围，如 {sheetId}!A1:C10", min_length=1)],
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
    spreadsheet_token: Annotated[str, Field(description="电子表格 token", min_length=1)],
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
    spreadsheet_token: Annotated[str, Field(description="电子表格 token", min_length=1)],
    sheet_id: Annotated[str, Field(description="工作表 ID", min_length=1)],
    values: Annotated[list[list[Any]], Field(description="二维数组")],
    data_start: Annotated[int, Field(description="数据起始行（1-based），默认 2", ge=1)] = 2,
) -> str:
    """追加数据到工作表（自动找空白位置写入）。"""
    return await sheets.append_data(
        AppendDataInput(
            spreadsheet_token=spreadsheet_token,
            sheet_id=sheet_id,
            values=values,
            data_start=data_start,
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
    spreadsheet_token: Annotated[str, Field(description="电子表格 token", min_length=1)],
    sheet_id: Annotated[str, Field(description="工作表 ID", min_length=1)],
    start_index: Annotated[int, Field(description="起始索引（1-based 含）", ge=1)],
    end_index: Annotated[int, Field(description="结束索引（1-based 含）", ge=1)],
    major_dimension: Annotated[str, Field(description="COLUMNS 或 ROWS，默认 COLUMNS")] = "COLUMNS",
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


@mcp.tool(
    name="lark_quick_filter_sheet_columns",
    annotations=ToolAnnotations(
        title="过滤工作表列",
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_quick_sheets_filter_columns(
    spreadsheet_token: Annotated[str, Field(description="电子表格 token", min_length=1)],
    sheet_id: Annotated[str, Field(description="工作表 ID", min_length=1)],
    keep_columns: Annotated[
        list[str], Field(description="要保留的列名列表，其余列将被删除", min_length=1)
    ],
    data_start: Annotated[int, Field(description="数据起始行（1-based），默认 2", ge=1)] = 2,
) -> str:
    """只保留指定列，删除其余列（包括空白列）。"""
    return await sheets_quick.quick_sheets_filter_columns(
        FilterSheetColumnsInput(
            spreadsheet_token=spreadsheet_token,
            sheet_id=sheet_id,
            keep_columns=keep_columns,
            data_start=data_start,
        )
    )

@mcp.tool(
    name="lark_quick_set_batch_index",
    annotations=ToolAnnotations(
        title="设置批次索引",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_quick_sheets_set_batch_index(
    spreadsheet_token: Annotated[str, Field(description="电子表格 token", min_length=1)],
    sheet_id: Annotated[str, Field(description="工作表 ID", min_length=1)],
    batch_column: Annotated[
        str, Field(description="批次列名，默认 f_batch_index")
    ] = "f_batch_index",
    batch_size: Annotated[int, Field(description="每批行数，默认 10", ge=1, le=1000)] = 10,
    data_start: Annotated[int, Field(description="数据起始行（1-based），默认 2", ge=1)] = 2,
) -> str:
    """按列设置批次索引，将数据按 batch_size 分组并写入批次号。"""
    return await sheets_quick.quick_sheets_set_batch_index(
        SetBatchIndexInput(
            spreadsheet_token=spreadsheet_token,
            sheet_id=sheet_id,
            batch_column=batch_column,
            batch_size=batch_size,
            data_start=data_start,
        )
    )


@mcp.tool(
    name="lark_quick_set_header_list",
    annotations=ToolAnnotations(
        title="写入新表头",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_quick_sheets_set_header_list(
    spreadsheet_token: Annotated[str, Field(description="电子表格 token", min_length=1)],
    sheet_id: Annotated[str, Field(description="工作表 ID", min_length=1)],
    header_list: Annotated[list[str], Field(description="新表头列表", min_length=1)],
    keep_columns: Annotated[
        int | None, Field(description="保留的原始列数，不指定则从 A 列写入", ge=0)
    ] = None,
    data_start: Annotated[int, Field(description="表头所在行=data_start-1，默认 2", ge=1)] = 2,
) -> str:
    """从指定位置写入新表头。"""
    return await sheets_quick.quick_sheets_set_header_list(
        SetHeaderListInput(
            spreadsheet_token=spreadsheet_token,
            sheet_id=sheet_id,
            header_list=header_list,
            keep_columns=keep_columns,
            data_start=data_start,
        )
    )


@mcp.tool(
    name="lark_quick_get_column_last_value",
    annotations=ToolAnnotations(
        title="获取列最后一个数值",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def tool_quick_sheets_get_column_last_value(
    spreadsheet_token: Annotated[str, Field(description="电子表格 token", min_length=1)],
    sheet_id: Annotated[str, Field(description="工作表 ID", min_length=1)],
    column_name: Annotated[str, Field(description="列名，将在表头中查找其位置", min_length=1)],
    data_start: Annotated[int, Field(description="数据起始行（1-based），默认 2", ge=1)] = 2,
) -> str:
    """获取指定列中最后一个数值（跳过表头），用于确定最大批次等场景。"""
    return await sheets_quick.quick_sheets_get_column_last_value(
        GetColumnLastValueInput(
            spreadsheet_token=spreadsheet_token,
            sheet_id=sheet_id,
            column_name=column_name,
            data_start=data_start,
        )
    )


@mcp.tool(
    name="lark_quick_get_rows_by_batch",
    annotations=ToolAnnotations(
        title="按批次读取行",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def tool_quick_sheets_get_rows_by_batch(
    spreadsheet_token: Annotated[str, Field(description="电子表格 token", min_length=1)],
    sheet_id: Annotated[str, Field(description="工作表 ID", min_length=1)],
    batch_id: Annotated[int, Field(description="批次号，从 1 开始", ge=1)],
    batch_size: Annotated[int, Field(description="每批行数", ge=1, le=5000)],
    data_start: Annotated[int, Field(description="数据起始行（1-based），默认 2", ge=1)] = 2,
) -> str:
    """按批次范围读取行数据，返回 markdown 表格。"""
    return await sheets_quick.quick_sheets_get_rows_by_batch(
        GetRowsByBatchInput(
            spreadsheet_token=spreadsheet_token,
            sheet_id=sheet_id,
            batch_id=batch_id,
            batch_size=batch_size,
            data_start=data_start,
        )
    )


@mcp.tool(
    name="lark_quick_batch_update",
    annotations=ToolAnnotations(
        title="批量更新行数据",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_quick_sheets_batch_update(
    spreadsheet_token: Annotated[str, Field(description="电子表格 token", min_length=1)],
    sheet_id: Annotated[str, Field(description="工作表 ID", min_length=1)],
    update_data: Annotated[
        list[dict[str, Any]],
        Field(description="更新数据，每行一个 dict，含 row_number 和要更新的列"),
    ],
    columns: Annotated[
        list[str] | None,
        Field(description="要写入的列名列表，不传则从第一条数据自动推导"),
    ] = None,
    data_start: Annotated[int, Field(description="数据起始行（1-based），默认 2", ge=1)] = 2,
) -> str:
    """批量更新多行，一次请求更新所有指定列。"""
    return await sheets_quick.quick_sheets_batch_update(
        BatchUpdateInput(
            spreadsheet_token=spreadsheet_token,
            sheet_id=sheet_id,
            update_data=update_data,
            columns=columns,
            data_start=data_start,
        )
    )


@mcp.tool(
    name="lark_quick_batch_append",
    annotations=ToolAnnotations(
        title="批量追加行数据",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_quick_sheets_batch_append(
    spreadsheet_token: Annotated[str, Field(description="电子表格 token", min_length=1)],
    sheet_id: Annotated[str, Field(description="工作表 ID", min_length=1)],
    data: Annotated[list[dict[str, Any]], Field(description="要追加的数据，每行一个 dict")],
    batch_size: Annotated[int, Field(description="每批追加行数，默认 500", ge=1, le=5000)] = 500,
    batch_interval: Annotated[int, Field(description="每批追加间隔秒数，默认 2", ge=0, le=30)] = 2,
    data_start: Annotated[int, Field(description="数据起始行（1-based），默认 2", ge=1)] = 2,
    overwrite_start: Annotated[
        int | bool | None, Field(description="True 从 data_start 覆写，int 从指定行覆写，None 使用 append 寻址")
    ] = None,
) -> str:
    """批量追加行到工作表，自动分片并带间隔。指定 overwrite_start 则从该行覆盖写入。"""
    return await sheets_quick.quick_sheets_batch_append(
        BatchAppendInput(
            spreadsheet_token=spreadsheet_token,
            sheet_id=sheet_id,
            data=data,
            batch_size=batch_size,
            batch_interval=batch_interval,
            data_start=data_start,
            overwrite_start=overwrite_start,
        )
    )


@mcp.tool(
    name="lark_quick_sync_from_file",
    annotations=ToolAnnotations(
        title="从 CSV 文件同步数据到工作表",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_quick_sheets_sync_from_file(
    spreadsheet_token: Annotated[str, Field(description="电子表格 token", min_length=1)],
    sheet_id: Annotated[str, Field(description="工作表 ID", min_length=1)],
    file_path: Annotated[str, Field(description="本地 CSV 文件路径")],
    batch_size: Annotated[int, Field(description="每批写入行数，默认 5000", ge=1, le=5000)] = 5000,
    data_start: Annotated[int, Field(description="数据起始行（1-based），默认 2", ge=1)] = 2,
) -> str:
    """从本地 CSV 文件同步数据到工作表。CSV 第一行为表头，默认从 data_start 行开始覆盖写入。"""
    return await sheets_quick.quick_sheets_sync_from_file(
        SyncFromFileInput(
            spreadsheet_token=spreadsheet_token,
            sheet_id=sheet_id,
            file_path=file_path,
            batch_size=batch_size,
            data_start=data_start,
        )
    )


@mcp.tool(
    name="lark_quick_clear_sheet_content",
    annotations=ToolAnnotations(
        title="清空工作表内容（不移除行）",
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_quick_sheets_clear_sheet_content(
    spreadsheet_token: Annotated[str, Field(description="电子表格 token", min_length=1)],
    sheet_id: Annotated[str, Field(description="工作表 ID", min_length=1)],
    keep_header: Annotated[bool, Field(description="是否保留首行表头，默认 true")] = True,
    data_start: Annotated[int, Field(description="数据起始行号，默认 2", ge=1)] = 2,
    before_column: Annotated[str | None, Field(description='指定列字母（如 "F"），只清空该列之前的所有列。不指定则清空全部列')] = None,
) -> str:
    """清空工作表数据内容（不移除行）。指定 before_column 则只清空该列之前的所有列。"""
    return await sheets_quick.quick_sheets_clear_sheet_content(
        ClearSheetContentInput(
            spreadsheet_token=spreadsheet_token,
            sheet_id=sheet_id,
            keep_header=keep_header,
            data_start=data_start,
            before_column=before_column,
        )
    )


@mcp.tool(
    name="lark_quick_clear_sheet",
    annotations=ToolAnnotations(
        title="清空工作表数据（删除行）",
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_quick_sheets_clear_sheet(
    spreadsheet_token: Annotated[str, Field(description="电子表格 token", min_length=1)],
    sheet_id: Annotated[str, Field(description="工作表 ID", min_length=1)],
    keep_header: Annotated[bool, Field(description="是否保留首行表头，默认 true")] = True,
    data_start: Annotated[int, Field(description="数据起始行号，默认 2", ge=1)] = 2,
) -> str:
    """清空工作表数据（删除行），默认保留首行表头。"""
    return await sheets_quick.quick_sheets_clear_sheet(
        ClearSheetInput(
            spreadsheet_token=spreadsheet_token,
            sheet_id=sheet_id,
            keep_header=keep_header,
            data_start=data_start,
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
