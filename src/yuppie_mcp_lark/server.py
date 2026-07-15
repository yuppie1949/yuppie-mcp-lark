"""飞书 MCP Server 主入口"""

import os
from typing import Annotated, Any, Literal

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from . import __version__
from .tools import bitable, bitable_quick, drive, messages, sheets, sheets_quick
from .tools.bitable import (
    BatchCreateRecordsInput,
    BatchDeleteRecordsInput,
    BatchGetRecordsInput,
    BatchUpdateRecordsInput,
    CopyAppInput,
    CreateAppInput,
    CreateRecordInput,
    CreateTableInput,
    DeleteRecordInput,
    DeleteTableInput,
    SearchRecordsInput,
    UpdateRecordInput,
)
from .tools.bitable_quick import BitableClearInput
from .tools.drive import CheckTaskInput, CopyFileInput, CreateFolderInput, DeleteFileInput, ListFilesInput, UploadFileInput
from .tools.messages import SendMessageInput
from .tools.sheets import (
    AddSheetInput,
    AppendDataInput,
    CopySheetInput,
    CreateSpreadsheetInput,
    DeleteDimensionInput,
    DeleteSheetInput,
    GetMetainfoInput,
    ReadRangeInput,
    ReadRangesInput,
    StylesBatchUpdateInput,
    UpdateDimensionInput,
    WriteImageInput,
    WriteRangeInput,
)
from .tools.sheets_quick import (
    BatchAppendInput,
    BatchUpdateInput,
    ClearSheetContentInput,
    ClearSheetInput,
    FilterSheetColumnsInput,
    GetColumnLastValueInput,
    GetRowsByBatchInput,
    QuickWriteImageInput,
    SetBatchIndexInput,
    SetColumnStyleInput,
    SetRowHeightInput,
    SetHeaderListInput,
    SyncFromFileInput,
)

mcp = FastMCP(
    name="lark_mcp",
    host=os.getenv("MCP_HOST", "127.0.0.1"),
    instructions=(
        "飞书开放平台工具集：发送消息（文本/富文本/卡片/文件等）、操作多维表格"
        "（搜索/创建/更新/删除记录，批量操作，应用和表格管理）、读写电子表格数据、"
        "管理工作表（新增/复制/删除/清空）、批量数据处理（追加/更新/按批次读写/从 CSV 同步）。"
    ),
)
mcp._mcp_server.version = __version__


@mcp.tool(
    name="message_send",
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
    name="drive_copy_file",
    annotations=ToolAnnotations(
        title="复制云文件",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_copy_file(
    file_token: Annotated[str, Field(description="源文件 token", min_length=1)],
    name: Annotated[str, Field(description="新文件名称", min_length=1)],
    folder_token: Annotated[str, Field(description="目标文件夹 token", min_length=1)],
    file_type: Annotated[str, Field(description="源文件类型：file/doc/sheet/bitable/docx")],
    user_id_type: Annotated[str | None, Field(description="用户 ID 类型")] = None,
) -> str:
    """复制文件到指定文件夹。"""
    return await drive.copy_file(
        CopyFileInput(
            file_token=file_token, name=name, folder_token=folder_token,
            file_type=file_type, user_id_type=user_id_type,
        )
    )


@mcp.tool(
    name="drive_delete_file",
    annotations=ToolAnnotations(
        title="删除云文件或文件夹",
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_delete_file(
    file_token: Annotated[str, Field(description="文件或文件夹 token", min_length=1)],
    file_type: Annotated[str, Field(description="文件类型：file/doc/sheet/bitable/docx/folder")],
) -> str:
    """删除云空间内的文件或文件夹（进入回收站）。"""
    return await drive.delete_file(
        DeleteFileInput(file_token=file_token, file_type=file_type)
    )


@mcp.tool(
    name="drive_check_task",
    annotations=ToolAnnotations(
        title="查询异步任务状态",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def tool_check_task(
    task_id: Annotated[str, Field(description="异步任务 ID", min_length=1)],
) -> str:
    """查询异步任务状态（删除/移动文件夹）。"""
    return await drive.check_task(CheckTaskInput(task_id=task_id))


@mcp.tool(
    name="drive_upload_file",
    annotations=ToolAnnotations(
        title="上传文件到云空间",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_upload_file(
    file_path: Annotated[str, Field(description="本地文件路径", min_length=1)],
    parent_node: Annotated[str, Field(description="目标文件夹 token", min_length=1)],
    file_name: Annotated[str | None, Field(description="文件名，不传则从 file_path 提取")] = None,
    checksum: Annotated[str | None, Field(description="文件的 Adler-32 校验和")] = None,
) -> str:
    """上传文件到云空间指定文件夹（最大 20 MB）。"""
    return await drive.upload_file(
        UploadFileInput(
            file_path=file_path, parent_node=parent_node,
            file_name=file_name, checksum=checksum,
        )
    )


@mcp.tool(
    name="drive_list_files",
    annotations=ToolAnnotations(
        title="获取文件夹文件清单",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def tool_list_files(
    folder_token: Annotated[str | None, Field(description="文件夹 token，不传则获取根目录")] = None,
    page_size: Annotated[int | None, Field(description="每页数量，最大 200", ge=1, le=200)] = None,
    page_token: Annotated[str | None, Field(description="分页 token")] = None,
    order_by: Annotated[str | None, Field(description="排序：EditedTime / CreatedTime")] = None,
    direction: Annotated[str | None, Field(description="排序方向：ASC / DESC")] = None,
    user_id_type: Annotated[str | None, Field(description="用户 ID 类型：open_id / union_id / user_id")] = None,
) -> str:
    """获取文件夹中的文件清单，支持分页。"""
    return await drive.list_files(
        ListFilesInput(
            folder_token=folder_token, page_size=page_size,
            page_token=page_token, order_by=order_by,
            direction=direction, user_id_type=user_id_type,
        )
    )


@mcp.tool(
    name="drive_create_folder",
    annotations=ToolAnnotations(
        title="创建文件夹",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_create_folder(
    name: Annotated[str, Field(description="文件夹名称", min_length=1)],
    folder_token: Annotated[str, Field(description="父文件夹 token", min_length=1)],
) -> str:
    """在云空间中创建一个空文件夹。"""
    return await drive.create_folder(
        CreateFolderInput(name=name, folder_token=folder_token)
    )


@mcp.tool(
    name="bitable_search_records",
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
    name="bitable_create_record",
    annotations=ToolAnnotations(
        title="创建多维表格记录",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_create_record(
    app_token: Annotated[str, Field(description="多维表格 app_token", min_length=1)],
    table_id: Annotated[str, Field(description="数据表 table_id", min_length=1)],
    fields: Annotated[dict[str, Any], Field(description='记录字段数据，如 {"字段名": "字段值"}')],
) -> str:
    """创建一条多维表格记录。"""
    return await bitable.create_record(
        CreateRecordInput(app_token=app_token, table_id=table_id, fields=fields)
    )


@mcp.tool(
    name="bitable_update_record",
    annotations=ToolAnnotations(
        title="更新多维表格记录",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_update_record(
    app_token: Annotated[str, Field(description="多维表格 app_token", min_length=1)],
    table_id: Annotated[str, Field(description="数据表 table_id", min_length=1)],
    record_id: Annotated[str, Field(description="记录 ID", min_length=1)],
    fields: Annotated[dict[str, Any], Field(description="记录字段数据")],
) -> str:
    """更新一条多维表格记录。"""
    return await bitable.update_record(
        UpdateRecordInput(
            app_token=app_token, table_id=table_id, record_id=record_id, fields=fields
        )
    )


@mcp.tool(
    name="bitable_delete_record",
    annotations=ToolAnnotations(
        title="删除多维表格记录",
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_delete_record(
    app_token: Annotated[str, Field(description="多维表格 app_token", min_length=1)],
    table_id: Annotated[str, Field(description="数据表 table_id", min_length=1)],
    record_id: Annotated[str, Field(description="记录 ID", min_length=1)],
) -> str:
    """删除一条多维表格记录。"""
    return await bitable.delete_record(
        DeleteRecordInput(app_token=app_token, table_id=table_id, record_id=record_id)
    )


@mcp.tool(
    name="bitable_batch_create_records",
    annotations=ToolAnnotations(
        title="批量创建多维表格记录",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_batch_create_records(
    app_token: Annotated[str, Field(description="多维表格 app_token", min_length=1)],
    table_id: Annotated[str, Field(description="数据表 table_id", min_length=1)],
    records: Annotated[
        list[dict[str, Any]],
        Field(description="记录列表，每条含 fields 字段，最多 500 条"),
    ],
) -> str:
    """批量创建多维表格记录（最多 500 条）。"""
    return await bitable.batch_create_records(
        BatchCreateRecordsInput(app_token=app_token, table_id=table_id, records=records)
    )


@mcp.tool(
    name="bitable_batch_update_records",
    annotations=ToolAnnotations(
        title="批量更新多维表格记录",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_batch_update_records(
    app_token: Annotated[str, Field(description="多维表格 app_token", min_length=1)],
    table_id: Annotated[str, Field(description="数据表 table_id", min_length=1)],
    records: Annotated[
        list[dict[str, Any]],
        Field(description="记录列表，每条含 record_id 和 fields，最多 500 条"),
    ],
) -> str:
    """批量更新多维表格记录（最多 500 条）。"""
    return await bitable.batch_update_records(
        BatchUpdateRecordsInput(app_token=app_token, table_id=table_id, records=records)
    )


@mcp.tool(
    name="bitable_batch_get_records",
    annotations=ToolAnnotations(
        title="批量获取多维表格记录",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def tool_batch_get_records(
    app_token: Annotated[str, Field(description="多维表格 app_token", min_length=1)],
    table_id: Annotated[str, Field(description="数据表 table_id", min_length=1)],
    record_ids: Annotated[
        list[str],
        Field(description="记录 ID 列表，最多 100 条", min_length=1),
    ],
    user_id_type: Annotated[
        str | None, Field(description="用户 ID 类型：open_id / user_id / union_id")
    ] = None,
    with_shared_url: Annotated[bool | None, Field(description="是否返回分享链接")] = None,
    automatic_fields: Annotated[bool | None, Field(description="是否返回自动计算字段")] = None,
) -> str:
    """批量获取多维表格记录（最多 100 条）。"""
    return await bitable.batch_get_records(
        BatchGetRecordsInput(
            app_token=app_token,
            table_id=table_id,
            record_ids=record_ids,
            user_id_type=user_id_type,
            with_shared_url=with_shared_url,
            automatic_fields=automatic_fields,
        )
    )


@mcp.tool(
    name="bitable_batch_delete_records",
    annotations=ToolAnnotations(
        title="批量删除多维表格记录",
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_batch_delete_records(
    app_token: Annotated[str, Field(description="多维表格 app_token", min_length=1)],
    table_id: Annotated[str, Field(description="数据表 table_id", min_length=1)],
    record_ids: Annotated[
        list[str],
        Field(description="记录 ID 列表，最多 500 条", min_length=1),
    ],
) -> str:
    """批量删除多维表格记录（最多 500 条）。"""
    return await bitable.batch_delete_records(
        BatchDeleteRecordsInput(app_token=app_token, table_id=table_id, record_ids=record_ids)
    )


@mcp.tool(
    name="bitable_create_app",
    annotations=ToolAnnotations(
        title="创建多维表格",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_create_app(
    name: Annotated[str, Field(description="多维表格名称", min_length=1)],
    folder_token: Annotated[str | None, Field(description="文件夹 token")] = None,
    time_zone: Annotated[str | None, Field(description="文档时区")] = None,
) -> str:
    """在指定文件夹中创建一个新的多维表格应用。"""
    return await bitable.create_app(
        CreateAppInput(name=name, folder_token=folder_token, time_zone=time_zone)
    )


@mcp.tool(
    name="bitable_copy_app",
    annotations=ToolAnnotations(
        title="复制多维表格",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_copy_app(
    app_token: Annotated[str, Field(description="要复制的多维表格 app_token", min_length=1)],
    name: Annotated[str | None, Field(description="新表格名称")] = None,
    folder_token: Annotated[str | None, Field(description="目标文件夹 token")] = None,
    without_content: Annotated[
        bool | None, Field(description="是否仅复制结构（不复制内容）")
    ] = None,
    time_zone: Annotated[str | None, Field(description="文档时区")] = None,
) -> str:
    """复制多维表格，可以指定名称、目标文件夹等。"""
    return await bitable.copy_app(
        CopyAppInput(
            app_token=app_token,
            name=name,
            folder_token=folder_token,
            without_content=without_content,
            time_zone=time_zone,
        )
    )


@mcp.tool(
    name="bitable_create_table",
    annotations=ToolAnnotations(
        title="创建多维表格数据表",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_create_table(
    app_token: Annotated[str, Field(description="多维表格 app_token", min_length=1)],
    table: Annotated[
        dict[str, Any],
        Field(description="数据表定义，含 name（必填）、default_view_name、fields 等"),
    ],
) -> str:
    """在指定多维表格中创建新的数据表。"""
    return await bitable.create_table(
        CreateTableInput(app_token=app_token, table=table)
    )


@mcp.tool(
    name="bitable_delete_table",
    annotations=ToolAnnotations(
        title="删除多维表格数据表",
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_delete_table(
    app_token: Annotated[str, Field(description="多维表格 app_token", min_length=1)],
    table_id: Annotated[str, Field(description="要删除的数据表 ID", min_length=1)],
) -> str:
    """删除多维表格中的指定数据表（至少保留一张表）。"""
    return await bitable.delete_table(
        DeleteTableInput(app_token=app_token, table_id=table_id)
    )


@mcp.tool(
    name="quick_bitable_clear",
    annotations=ToolAnnotations(
        title="清空多维表格数据",
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_quick_bitable_clear(
    app_token: Annotated[str, Field(description="多维表格 app_token", min_length=1)],
    table_id: Annotated[str, Field(description="数据表 table_id", min_length=1)],
    filter: Annotated[
        dict[str, Any] | None, Field(description="筛选条件，只删除符合条件的数据")
    ] = None,
    sort: Annotated[
        list[dict[str, Any]] | None, Field(description="排序条件")
    ] = None,
) -> str:
    """分页获取所有记录并批量删除，支持筛选条件。"""
    return await bitable_quick.quick_bitable_clear(
        BitableClearInput(
            app_token=app_token,
            table_id=table_id,
            filter=filter,
            sort=sort,
        )
    )


@mcp.tool(
    name="sheets_get_metainfo",
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
    name="sheets_add_sheet",
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
    name="sheets_delete_sheet",
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
    name="sheets_copy_sheet",
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
    name="sheets_create_spreadsheet",
    annotations=ToolAnnotations(
        title="创建电子表格",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_create_spreadsheet(
    title: Annotated[str, Field(description="电子表格标题", min_length=1)],
    folder_token: Annotated[str | None, Field(description="文件夹 token")] = None,
) -> str:
    """创建一个新的电子表格。"""
    return await sheets.create_spreadsheet(
        CreateSpreadsheetInput(title=title, folder_token=folder_token)
    )


@mcp.tool(
    name="sheets_get_spreadsheet",
    annotations=ToolAnnotations(
        title="获取电子表格信息",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def tool_get_spreadsheet(
    spreadsheet_token: Annotated[str, Field(description="电子表格 token", min_length=1)],
) -> str:
    """获取电子表格的基本信息。"""
    return await sheets.get_spreadsheet(
        GetMetainfoInput(spreadsheet_token=spreadsheet_token)
    )


@mcp.tool(
    name="sheets_query_sheets",
    annotations=ToolAnnotations(
        title="查询所有工作表",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def tool_query_sheets(
    spreadsheet_token: Annotated[str, Field(description="电子表格 token", min_length=1)],
) -> str:
    """查询电子表格中的所有工作表。"""
    return await sheets.query_sheets(
        GetMetainfoInput(spreadsheet_token=spreadsheet_token)
    )


@mcp.tool(
    name="sheets_read_range",
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
    name="sheets_read_ranges",
    annotations=ToolAnnotations(
        title="读取多个范围数据",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def tool_read_ranges(
    spreadsheet_token: Annotated[str, Field(description="电子表格 token", min_length=1)],
    ranges: Annotated[str, Field(description='多个范围，逗号分隔，如 "sheetId1!A2:B6,sheetId2!B1:C8"', min_length=1)],
    value_render_option: Annotated[
        str | None, Field(description="值渲染选项：ToString / Formula / FormattedValue / UnformattedValue")
    ] = None,
    date_time_render_option: Annotated[
        str | None, Field(description="日期时间渲染选项：FormattedString")
    ] = None,
    user_id_type: Annotated[
        str | None, Field(description="用户 ID 类型：open_id / union_id")
    ] = None,
) -> str:
    """读取多个范围数据，每个范围以 markdown 表格呈现。"""
    return await sheets.read_ranges(
        ReadRangesInput(
            spreadsheet_token=spreadsheet_token,
            ranges=ranges,
            value_render_option=value_render_option,
            date_time_render_option=date_time_render_option,
            user_id_type=user_id_type,
        )
    )


@mcp.tool(
    name="sheets_write_image",
    annotations=ToolAnnotations(
        title="写入电子表格图片",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_write_image(
    spreadsheet_token: Annotated[str, Field(description="电子表格 token", min_length=1)],
    range: Annotated[str, Field(description='单元格范围，如 "sheetId!A1:A1"', min_length=1)],
    image_base64: Annotated[str, Field(description="图片 base64 编码内容", min_length=1)],
    name: Annotated[str, Field(description='图片文件名，含后缀，如 "test.png"', min_length=1)],
) -> str:
    """向指定单元格写入图片，支持 PNG/JPEG/GIF/BMP 等格式。"""
    return await sheets.write_image(
        WriteImageInput(
            spreadsheet_token=spreadsheet_token,
            range=range,
            image_base64=image_base64,
            name=name,
        )
    )


@mcp.tool(
    name="sheets_write_range",
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
    name="sheets_append_data",
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
    name="sheets_delete_dimension",
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
    name="sheets_update_dimension",
    annotations=ToolAnnotations(
        title="更新行列属性",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def tool_update_dimension(
    spreadsheet_token: Annotated[str, Field(description="电子表格 token", min_length=1)],
    sheet_id: Annotated[str, Field(description="工作表 ID", min_length=1)],
    start_index: Annotated[int, Field(description="起始位置（1-based 含）", ge=1)],
    end_index: Annotated[int, Field(description="结束位置（1-based 含）", ge=1)],
    major_dimension: Annotated[str, Field(description="维度：ROWS（行）或 COLUMNS（列）")] = "ROWS",
    fixed_size: Annotated[int | None, Field(description="行高或列宽（像素）")] = None,
    visible: Annotated[bool | None, Field(description="是否显示行或列")] = None,
) -> str:
    """更新行列属性（行高/列宽/显示隐藏），单次最多 5000 行/列。"""
    return await sheets.update_dimension(
        UpdateDimensionInput(
            spreadsheet_token=spreadsheet_token,
            sheet_id=sheet_id,
            major_dimension=major_dimension,
            start_index=start_index,
            end_index=end_index,
            fixed_size=fixed_size,
            visible=visible,
        )
    )


@mcp.tool(
    name="sheets_styles_batch_update",
    annotations=ToolAnnotations(
        title="批量设置单元格样式",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_styles_batch_update(
    spreadsheet_token: Annotated[str, Field(description="电子表格 token", min_length=1)],
    data: Annotated[
        list[dict[str, Any]],
        Field(description='样式数据，每项含 ranges（范围列表）和 style（样式对象）'),
    ],
) -> str:
    """批量设置单元格样式，单次最多 50000 个单元格。"""
    return await sheets.styles_batch_update(
        StylesBatchUpdateInput(spreadsheet_token=spreadsheet_token, data=data)
    )


@mcp.tool(
    name="quick_sheets_filter_columns",
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
    name="quick_sheets_set_batch_index",
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
    name="quick_sheets_set_header_list",
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
    name="quick_sheets_get_column_last_value",
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
    name="quick_sheets_get_rows_by_batch",
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
    name="quick_sheets_batch_update",
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
    name="quick_sheets_batch_append",
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
    name="quick_sheets_sync_from_file",
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
    name="quick_sheets_clear_content",
    annotations=ToolAnnotations(
        title="清空工作表内容（不移除行）",
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_quick_sheets_clear_content(
    spreadsheet_token: Annotated[str, Field(description="电子表格 token", min_length=1)],
    sheet_id: Annotated[str, Field(description="工作表 ID", min_length=1)],
    keep_header: Annotated[bool, Field(description="是否保留首行表头，默认 true")] = True,
    data_start: Annotated[int, Field(description="数据起始行号，默认 2", ge=1)] = 2,
    before_column: Annotated[str | None, Field(description='指定列字母（如 "F"），只清空该列之前的所有列。不指定则清空全部列')] = None,
) -> str:
    """清空工作表数据内容（不移除行）。指定 before_column 则只清空该列之前的所有列。"""
    return await sheets_quick.quick_sheets_clear_content(
        ClearSheetContentInput(
            spreadsheet_token=spreadsheet_token,
            sheet_id=sheet_id,
            keep_header=keep_header,
            data_start=data_start,
            before_column=before_column,
        )
    )


@mcp.tool(
    name="quick_sheets_set_row_height",
    annotations=ToolAnnotations(
        title="设置工作表的行高",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def tool_quick_sheets_set_row_height(
    spreadsheet_token: Annotated[str, Field(description="电子表格 token", min_length=1)],
    sheet_id: Annotated[str, Field(description="工作表 ID", min_length=1)],
    height: Annotated[int, Field(description="行高（点，1/72 英寸）", ge=1)],
    start_row: Annotated[int, Field(description="起始行号，默认 2（跳过表头）", ge=1)] = 2,
    end_row: Annotated[int | None, Field(description="结束行号，不传则到最后一行")] = None,
) -> str:
    """设置工作表的行高（自动分批，支持指定范围）。"""
    return await sheets_quick.quick_sheets_set_row_height(
        SetRowHeightInput(
            spreadsheet_token=spreadsheet_token,
            sheet_id=sheet_id,
            height=height,
            start_row=start_row,
            end_row=end_row,
        )
    )


@mcp.tool(
    name="quick_sheets_set_column_style",
    annotations=ToolAnnotations(
        title="批量设置列样式",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_quick_sheets_set_column_style(
    spreadsheet_token: Annotated[str, Field(description="电子表格 token", min_length=1)],
    sheet_id: Annotated[str, Field(description="工作表 ID", min_length=1)],
    style: Annotated[dict[str, Any], Field(description="样式配置，传给 styles_batch_update 的 style 对象")],
    columns: Annotated[
        list[str] | None, Field(description='指定列字母列表，如 ["A", "C"]。不传则全部列')
    ] = None,
    start_row: Annotated[int, Field(description="起始行号，默认 2（跳过表头）", ge=1)] = 2,
    end_row: Annotated[int | None, Field(description="结束行号，不传则到最后一行")] = None,
) -> str:
    """批量设置列样式（自动分批），支持单列、多列或全部列。"""
    return await sheets_quick.quick_sheets_set_column_style(
        SetColumnStyleInput(
            spreadsheet_token=spreadsheet_token,
            sheet_id=sheet_id,
            style=style,
            columns=columns,
            start_row=start_row,
            end_row=end_row,
        )
    )


@mcp.tool(
    name="quick_sheets_clear_sheet",
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


@mcp.tool(
    name="quick_sheets_write_image",
    annotations=ToolAnnotations(
        title="快捷写入电子表格图片",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_quick_sheets_write_image(
    spreadsheet_token: Annotated[str, Field(description="电子表格 token", min_length=1)],
    range: Annotated[str, Field(description='单元格范围，如 "sheetId!A1:A1"', min_length=1)],
    image_source: Annotated[
        str,
        Field(
            description="图片来源：网络 URL（http/https）、本地文件路径、或 base64 字符串",
            min_length=1,
        ),
    ],
    name: Annotated[
        str | None, Field(description='图片文件名（含后缀），不传则自动从 image_source 提取')
    ] = None,
) -> str:
    """向单元格写入图片，支持网络图片、本地文件、base64 三种来源。"""
    return await sheets_quick.quick_sheets_write_image(
        QuickWriteImageInput(
            spreadsheet_token=spreadsheet_token,
            range=range,
            image_source=image_source,
            name=name,
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
