"""电子表格快捷业务操作 MCP 工具"""

from __future__ import annotations

import time
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ..utils.config import LarkConfig
from ..utils.lark import LarkClient

_client: LarkClient | None = None


def _get_client() -> LarkClient:
    global _client
    if _client is None:
        config = LarkConfig.from_env()
        _client = LarkClient(config.app_id, config.app_secret, config.base_url)
    return _client


class FilterSheetColumnsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_token: str = Field(..., min_length=1, description="电子表格 token")
    sheet_id: str = Field(..., min_length=1, description="工作表 ID")
    keep_columns: list[str] = Field(
        ..., min_length=1, description="要保留的列名列表，其余列将被删除"
    )
    data_start: int = Field(2, ge=1, description="数据起始行号（1-based），默认 2")


class SetBatchIndexInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_token: str = Field(..., min_length=1, description="电子表格 token")
    sheet_id: str = Field(..., min_length=1, description="工作表 ID")
    batch_column: str = Field("f_batch_index", description="批次列名，默认 f_batch_index")
    batch_size: int = Field(10, ge=1, le=1000, description="每批行数，默认 10")
    data_start: int = Field(2, ge=1, description="数据起始行号（1-based），默认 2")


class SetHeaderListInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_token: str = Field(..., min_length=1, description="电子表格 token")
    sheet_id: str = Field(..., min_length=1, description="工作表 ID")
    header_list: list[str] = Field(..., min_length=1, description="新表头列表")
    keep_columns: int | None = Field(
        None, ge=0, description="保留的原始列数，新表头从该位置后开始写入。不指定则从 A 列写入"
    )
    data_start: int = Field(2, ge=1, description="数据起始行号，header=data_start-1，默认 2")


class GetColumnLastValueInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_token: str = Field(..., min_length=1, description="电子表格 token")
    sheet_id: str = Field(..., min_length=1, description="工作表 ID")
    column_name: str = Field(..., min_length=1, description="列名，将在表头中查找其位置")
    data_start: int = Field(2, ge=1, description="数据起始行（1-based），默认 2")


class GetRowsByBatchInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_token: str = Field(..., min_length=1, description="电子表格 token")
    sheet_id: str = Field(..., min_length=1, description="工作表 ID")
    batch_id: int = Field(..., ge=1, description="批次号，从 1 开始")
    batch_size: int = Field(..., ge=1, le=5000, description="每批行数")
    data_start: int = Field(2, ge=1, description="数据起始行（1-based），默认 2")


class BatchUpdateInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_token: str = Field(..., min_length=1, description="电子表格 token")
    sheet_id: str = Field(..., min_length=1, description="工作表 ID")
    update_data: list[dict[str, Any]] = Field(
        ...,
        description='更新数据。每个 dict 含 row_number 和要更新的列',
    )
    columns: list[str] | None = Field(
        None,
        description='要写入的列名列表。为 None 时从第一条数据自动推导',
    )
    data_start: int = Field(2, ge=1, description="数据起始行（1-based），默认 2")


class BatchAppendInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_token: str = Field(..., min_length=1, description="电子表格 token")
    sheet_id: str = Field(..., min_length=1, description="工作表 ID")
    data: list[dict[str, Any]] = Field(..., description="要追加的数据，每行一个 dict，key 为列名")
    batch_size: int = Field(500, ge=1, le=5000, description="每批追加行数")
    batch_interval: int = Field(2, ge=0, le=30, description="每批追加间隔秒数，默认 2")
    data_start: int = Field(2, ge=1, description="数据起始行（1-based），默认 2")
    overwrite_start: int | bool | None = Field(
        None, description="True 从 data_start 覆写，int 从指定行覆写，None 使用 append 自动寻址",
    )


class SyncFromFileInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_token: str = Field(..., min_length=1, description="电子表格 token")
    sheet_id: str = Field(..., min_length=1, description="工作表 ID")
    file_path: str = Field(..., min_length=1, description="本地 CSV 文件路径")
    batch_size: int = Field(5000, ge=1, le=5000, description="每批写入行数，默认 5000")
    data_start: int = Field(2, ge=1, description="数据起始行（1-based），默认 2")


class ClearSheetInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_token: str = Field(..., min_length=1, description="电子表格 token")
    sheet_id: str = Field(..., min_length=1, description="工作表 ID")
    keep_header: bool = Field(True, description="是否保留首行表头，默认 true")
    data_start: int = Field(2, ge=1, description="数据起始行号，keep_header 时保留前一行（header）")


class ClearSheetContentInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_token: str = Field(..., min_length=1, description="电子表格 token")
    sheet_id: str = Field(..., min_length=1, description="工作表 ID")
    keep_header: bool = Field(True, description="是否保留首行表头，默认 true")
    data_start: int = Field(2, ge=1, description="数据起始行号，keep_header 时保留前一行（header）")
    before_column: str | None = Field(
        None, description='指定列字母（如 "F"），只清空该列之前的所有列。不指定则清空全部列',
    )

class SetRowHeightInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_token: str = Field(..., min_length=1, description="电子表格 token")
    sheet_id: str = Field(..., min_length=1, description="工作表 ID")
    height: int = Field(..., ge=1, description="行高（点，1/72 英寸）")
    start_row: int = Field(2, ge=1, description="起始行号，默认 2（跳过表头）")
    end_row: int | None = Field(None, description="结束行号，不传则到最后一行")


async def quick_sheets_filter_columns(args: FilterSheetColumnsInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        sheet_id = await client.quick_sheets_filter_columns(
            args.spreadsheet_token, args.sheet_id, args.keep_columns,
            data_start=args.data_start,
        )
        _elapsed = time.time() - _t0
        return (
            "✅ 列过滤完成\n\n"
            f"- **耗时**: `{_elapsed:.1f}s`"
            f"- **保留列数**: `{len(args.keep_columns)}`\n"
            f"- **sheetId**: `{sheet_id}`\n"
        )
    except Exception as e:
        return f"❌ 列过滤失败：{e}"


async def quick_sheets_set_batch_index(args: SetBatchIndexInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        await client.quick_sheets_set_batch_index(
            args.spreadsheet_token,
            args.sheet_id,
            batch_column=args.batch_column,
            batch_size=args.batch_size,
            data_start=args.data_start,
        )
        _elapsed = time.time() - _t0
        return (
            "✅ 批次索引已设置\n\n"
            f"- **耗时**: `{_elapsed:.1f}s`"
            f"- **batch_column**: `{args.batch_column}`\n"
            f"- **batch_size**: `{args.batch_size}`\n"
        )
    except Exception as e:
        return f"❌ 设置批次索引失败：{e}"


async def quick_sheets_set_header_list(args: SetHeaderListInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        await client.quick_sheets_set_header_list(
            args.spreadsheet_token,
            args.sheet_id,
            args.header_list,
            keep_columns=args.keep_columns,
            data_start=args.data_start,
        )
        _elapsed = time.time() - _t0
        return (
            f"✅ 表头已写入\n\n- **列数**: `{len(args.header_list)}`\n- **耗时**: `{_elapsed:.1f}s`"
        )
    except Exception as e:
        return f"❌ 写入表头失败：{e}"


async def quick_sheets_get_column_last_value(args: GetColumnLastValueInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        result = await client.quick_sheets_get_last_value(
            args.spreadsheet_token, args.sheet_id, args.column_name,
            data_start=args.data_start,
        )
        _elapsed = time.time() - _t0
        return (
            f"查询完成\n\n"
            f"- **耗时**: `{_elapsed:.1f}s`"
            f"- **列**: `{args.column_name}`\n"
            f"- **最后一个非空值**: `{result['value']}`\n"
            f"- **行号**: `{result['row_number']}`\n"
        )
    except Exception as e:
        return f"❌ 查询失败：{e}"


async def quick_sheets_get_rows_by_batch(args: GetRowsByBatchInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        rows = await client.quick_sheets_get_rows_by_batch(
            args.spreadsheet_token, args.sheet_id, args.batch_id, args.batch_size,
            data_start=args.data_start,
        )
        _elapsed = time.time() - _t0
    except Exception as e:
        return f"❌ 读取失败：{e}"
    if not rows:
        return f"查询完成\n\n- **行数**: `0`\n- **耗时**: `{_elapsed:.1f}s`"
    keys = ["row_number"] + [k for k in rows[0].keys() if k is not None and k != "row_number"]
    header = "| " + " | ".join(keys) + " |"
    sep = "| " + " | ".join("---" for _ in keys) + " |"
    body = "\n".join("| " + " | ".join(str(r.get(k, "")) for k in keys) + " |" for r in rows)
    return (
        f"查询完成\n\n"
        f"- **耗时**: `{_elapsed:.1f}s`\n\n"
        f"- **行数**: `{len(rows)}`\n"
        f"{header}\n{sep}\n{body}"
    )


async def quick_sheets_batch_update(args: BatchUpdateInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        if not args.update_data:
            return "✅ 批量更新完成\n\n- **更新行数**: `0`"
        await client.quick_sheets_batch_update(
            args.spreadsheet_token,
            args.sheet_id,
            args.update_data,
            columns=args.columns,
            data_start=args.data_start,
        )
        _elapsed = time.time() - _t0
        return (
            "✅ 批量更新完成\n\n"
            f"- **耗时**: `{_elapsed:.1f}s`"
            f"- **更新行数**: `{len(args.update_data)}`\n"
        )
    except Exception as e:
        return f"❌ 批量更新失败：{e}"


async def quick_sheets_batch_append(args: BatchAppendInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        await client.quick_sheets_batch_append(
            args.spreadsheet_token,
            args.sheet_id,
            args.data,
            batch_size=args.batch_size,
            batch_interval=args.batch_interval,
            data_start=args.data_start,
            overwrite_start=args.overwrite_start,
        )
        _elapsed = time.time() - _t0
        return (
            f"✅ 批量追加完成\n\n- **追加行数**: `{len(args.data)}`\n- **耗时**: `{_elapsed:.1f}s`"
        )
    except Exception as e:
        return f"❌ 批量追加失败：{e}"


async def quick_sheets_sync_from_file(args: SyncFromFileInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        await client.quick_sheets_sync_from_file(
            args.spreadsheet_token,
            args.sheet_id,
            args.file_path,
            batch_size=args.batch_size,
            data_start=args.data_start,
        )
        _elapsed = time.time() - _t0
        return (
            f"✅ 从文件同步完成\n\n"
            f"- **耗时**: `{_elapsed:.1f}s`"
            f"- **文件**: `{args.file_path}`\n"
        )
    except Exception as e:
        return f"❌ 从文件同步失败：{e}"


async def quick_sheets_clear_content(args: ClearSheetContentInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        info = await client.quick_sheets_clear_content(
            args.spreadsheet_token,
            args.sheet_id,
            keep_header=args.keep_header,
            data_start=args.data_start,
            before_column=args.before_column,
        )
        _elapsed = time.time() - _t0
        col_label = f"**清空列数**: `{info['col_count']}`\n" if info["col_count"] else ""
        return (
            "✅ 工作表内容已清空\n\n"
            f"- **耗时**: `{_elapsed:.1f}s`"
            f"{col_label}"
            f"- **清空行数**: `{info['row_count']}`\n"
        )
    except Exception as e:
        return f"❌ 清空工作表内容失败：{e}"


async def quick_sheets_clear_sheet(args: ClearSheetInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        await client.quick_sheets_clear_sheet(
            args.spreadsheet_token,
            args.sheet_id,
            keep_header=args.keep_header,
            data_start=args.data_start,
        )
        _elapsed = time.time() - _t0
        return f"✅ 工作表已清空\n\n- **耗时**: `{_elapsed:.1f}s`"
    except Exception as e:
        return f"❌ 清空工作表失败：{e}"


class QuickWriteImageInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_token: str = Field(..., min_length=1, description="电子表格 token")
    range: str = Field(..., min_length=1, description='单元格范围，如 "sheetId!A1:A1"')
    image_source: str = Field(
        ..., min_length=1,
        description="图片来源：网络 URL（http/https）、本地文件路径、或 base64 字符串",
    )
    name: str | None = Field(None, description='图片文件名（含后缀），不传则从 image_source 自动提取')


async def quick_sheets_write_image(args: QuickWriteImageInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        result = await client.quick_sheets_write_image(
            args.spreadsheet_token, args.range, args.image_source, args.name
        )
        _elapsed = time.time() - _t0
    except Exception as e:
        return f"❌ 写入图片失败：{e}"
    return (
        f"✅ 图片已写入\n\n"
        f"- **range**: `{result.get('updateRange', '')}`\n"
        f"- **耗时**: `{_elapsed:.1f}s`"
    )

async def quick_sheets_set_row_height(args: SetRowHeightInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        result = await client.quick_sheets_set_row_height(
            args.spreadsheet_token,
            args.sheet_id,
            args.height,
            start_row=args.start_row,
            end_row=args.end_row,
        )
        _elapsed = time.time() - _t0
    except Exception as e:
        return f"❌ 设置行高失败：{e}"
    return (
        f"✅ 行高已设置\n\n"
        f"- **耗时**: `{_elapsed:.1f}s`"
        f"- **行高**: `{args.height}pt`\n"
        f"- **行数**: `{result['updated_rows']}`\n"
        f"- **批次数**: `{result['batch_count']}`\n"
    )
