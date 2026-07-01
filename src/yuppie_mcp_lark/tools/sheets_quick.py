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


class SetBatchIndexInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_token: str = Field(..., min_length=1, description="电子表格 token")
    sheet_id: str = Field(..., min_length=1, description="工作表 ID")
    batch_column: str = Field("f_batch_index", description="批次列名，默认 f_batch_index")
    batch_size: int = Field(10, ge=1, le=1000, description="每批行数，默认 10")


class SetHeaderListInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_token: str = Field(..., min_length=1, description="电子表格 token")
    sheet_id: str = Field(..., min_length=1, description="工作表 ID")
    header_list: list[str] = Field(..., min_length=1, description="新表头列表")
    keep_columns: int | None = Field(
        None, ge=0, description="保留的原始列数，新表头从该位置后开始写入。不指定则从 A 列写入"
    )


class GetColumnLastValueInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_token: str = Field(..., min_length=1, description="电子表格 token")
    sheet_id: str = Field(..., min_length=1, description="工作表 ID")
    column_name: str = Field(..., min_length=1, description="列名，将在表头中查找其位置")


class GetRowsByBatchInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_token: str = Field(..., min_length=1, description="电子表格 token")
    sheet_id: str = Field(..., min_length=1, description="工作表 ID")
    batch_id: int = Field(..., ge=1, description="批次号，从 1 开始")
    batch_size: int = Field(..., ge=1, le=5000, description="每批行数")


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


class BatchAppendInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_token: str = Field(..., min_length=1, description="电子表格 token")
    sheet_id: str = Field(..., min_length=1, description="工作表 ID")
    data: list[dict[str, Any]] = Field(..., description="要追加的数据，每行一个 dict，key 为列名")
    batch_size: int = Field(500, ge=1, le=5000, description="每批追加行数")
    batch_interval: int = Field(2, ge=0, le=30, description="每批追加间隔秒数，默认 2")


class BatchAppendFromFileInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_token: str = Field(..., min_length=1, description="电子表格 token")
    sheet_id: str = Field(..., min_length=1, description="工作表 ID")
    file_path: str = Field(..., min_length=1, description="本地 CSV 文件路径")
    batch_size: int = Field(5000, ge=1, le=5000, description="每批写入行数，默认 5000")


async def quick_sheets_filter_columns(args: FilterSheetColumnsInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        sheet_id = await client.quick_sheets_filter_columns(
            args.spreadsheet_token, args.sheet_id, args.keep_columns
        )
        _elapsed = time.time() - _t0
        return (
            "✅ 列过滤完成\n\n"
            f"- **保留列数**: `{len(args.keep_columns)}`\n"
            f"- **sheetId**: `{sheet_id}`\n"
            f"- **耗时**: `{_elapsed:.1f}s`"
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
        )
        _elapsed = time.time() - _t0
        return (
            "✅ 批次索引已设置\n\n"
            f"- **batch_column**: `{args.batch_column}`\n"
            f"- **batch_size**: `{args.batch_size}`\n"
            f"- **耗时**: `{_elapsed:.1f}s`"
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
            args.spreadsheet_token, args.sheet_id, args.column_name
        )
        _elapsed = time.time() - _t0
        return (
            f"查询完成\n\n"
            f"- **列**: `{args.column_name}`\n"
            f"- **最后一个非空值**: `{result['value']}`\n"
            f"- **行号**: `{result['row_number']}`\n"
            f"- **耗时**: `{_elapsed:.1f}s`"
        )
    except Exception as e:
        return f"❌ 查询失败：{e}"


async def quick_sheets_get_rows_by_batch(args: GetRowsByBatchInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        rows = await client.quick_sheets_get_rows_by_batch(
            args.spreadsheet_token, args.sheet_id, args.batch_id, args.batch_size
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
        f"- **行数**: `{len(rows)}`\n"
        f"- **耗时**: `{_elapsed:.1f}s`\n\n"
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
        )
        _elapsed = time.time() - _t0
        return (
            "✅ 批量更新完成\n\n"
            f"- **更新行数**: `{len(args.update_data)}`\n"
            f"- **耗时**: `{_elapsed:.1f}s`"
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
        )
        _elapsed = time.time() - _t0
        return (
            f"✅ 批量追加完成\n\n- **追加行数**: `{len(args.data)}`\n- **耗时**: `{_elapsed:.1f}s`"
        )
    except Exception as e:
        return f"❌ 批量追加失败：{e}"


async def quick_sheets_batch_append_from_file(args: BatchAppendFromFileInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        await client.quick_sheets_batch_append_from_file(
            args.spreadsheet_token,
            args.sheet_id,
            args.file_path,
            batch_size=args.batch_size,
        )
        _elapsed = time.time() - _t0
        return (
            f"✅ 从文件追加完成\n\n"
            f"- **文件**: `{args.file_path}`\n"
            f"- **耗时**: `{_elapsed:.1f}s`"
        )
    except Exception as e:
        return f"❌ 从文件追加失败：{e}"
