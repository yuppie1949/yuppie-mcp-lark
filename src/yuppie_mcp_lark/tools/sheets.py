"""电子表格域 MCP 工具"""

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


class GetMetainfoInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_token: str = Field(..., min_length=1, description="电子表格 token")


class AddSheetInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_token: str = Field(..., min_length=1, description="电子表格 token")
    title: str = Field(..., min_length=1, description="新工作表标题")


class DeleteSheetInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_token: str = Field(..., min_length=1, description="电子表格 token")
    sheet_id: str = Field(..., min_length=1, description="工作表 ID")


class CopySheetInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_token: str = Field(..., min_length=1, description="电子表格 token")
    source_sheet_id: str = Field(..., min_length=1, description="源工作表 ID")
    title: str = Field(..., min_length=1, description="新工作表标题")


class ReadRangeInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_token: str = Field(..., min_length=1, description="电子表格 token")
    range_str: str = Field(..., min_length=1, description="范围，如 {sheetId}!A1:C10")


class WriteRangeInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_token: str = Field(..., min_length=1, description="电子表格 token")
    range_str: str = Field(..., min_length=1, description="范围")
    values: list[list[Any]] = Field(..., description="二维数组")


class AppendDataInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_token: str = Field(..., min_length=1, description="电子表格 token")
    sheet_id: str = Field(..., min_length=1, description="工作表 ID")
    values: list[list[Any]] = Field(..., description="二维数组")
    data_start: int = Field(2, ge=1, description="数据起始行号（1-based），默认 2")


class DeleteDimensionInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_token: str = Field(..., min_length=1, description="电子表格 token")
    sheet_id: str = Field(..., min_length=1, description="工作表 ID")
    major_dimension: str = Field("COLUMNS", description="COLUMNS 或 ROWS，默认 COLUMNS")
    start_index: int = Field(..., ge=1, description="起始索引（1-based 含）")
    end_index: int = Field(..., ge=1, description="结束索引（1-based 含）")


async def get_metainfo(args: GetMetainfoInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        data = await client.get_metainfo(args.spreadsheet_token)
        _elapsed = time.time() - _t0
    except Exception as e:
        return f"❌ 获取元信息失败：{e}"
    sheets = data.get("sheets", [])
    title = data.get("title", "")
    summary = (
        f"查询完成\n\n- **标题**: {title}\n"
        f"- **工作表数**: `{len(sheets)}`\n- **耗时**: `{_elapsed:.1f}s`\n"
    )
    lines = [summary]
    lines.append("| 工作表 | sheetId | 行数 | 列数 |")
    lines.append("| --- | --- | --- | --- |")
    for s in sheets:
        lines.append(
            f"| {s.get('title', '')} | {s.get('sheetId', '')} | "
            f"{s.get('rowCount', 0)} | {s.get('columnCount', 0)} |"
        )
    return "\n".join(lines)


async def add_sheet(args: AddSheetInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        sheet_id = await client.add_sheet(args.spreadsheet_token, args.title)
        _elapsed = time.time() - _t0
        return (
            f"✅ 工作表已创建\n\n"
            f"- **title**: `{args.title}`\n"
            f"- **sheetId**: `{sheet_id}`\n"
            f"- **耗时**: `{_elapsed:.1f}s`"
        )
    except Exception as e:
        return f"❌ 创建工作表失败：{e}"


async def delete_sheet(args: DeleteSheetInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        await client.delete_sheet(args.spreadsheet_token, args.sheet_id)
        _elapsed = time.time() - _t0
        return (
            f"✅ 工作表已删除\n\n"
            f"- **sheetId**: `{args.sheet_id}`\n"
            f"- **耗时**: `{_elapsed:.1f}s`"
        )
    except Exception as e:
        return f"❌ 删除工作表失败：{e}"


async def copy_sheet(args: CopySheetInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        sheet_id = await client.copy_sheet(args.spreadsheet_token, args.source_sheet_id, args.title)
        _elapsed = time.time() - _t0
        return (
            f"✅ 工作表已复制\n\n"
            f"- **source_sheet_id**: `{args.source_sheet_id}`\n"
            f"- **new_sheetId**: `{sheet_id}`\n"
            f"- **耗时**: `{_elapsed:.1f}s`"
        )
    except Exception as e:
        return f"❌ 复制工作表失败：{e}"


async def read_range(args: ReadRangeInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        data = await client.read_range(args.spreadsheet_token, args.range_str)
        _elapsed = time.time() - _t0
    except Exception as e:
        return f"❌ 读取失败：{e}"
    if not data:
        return f"查询完成\n\n- **行数**: `0`\n- **耗时**: `{_elapsed:.1f}s`"
    rows = len(data)
    cols = max(len(r) for r in data)
    header = "| " + " | ".join(f"col{i}" for i in range(cols)) + " |"
    sep = "| " + " | ".join("---" for _ in range(cols)) + " |"
    body = "\n".join(
        "| " + " | ".join(str(r[i]) if i < len(r) else "" for i in range(cols)) + " |"
        for r in data
    )
    return (
        f"查询完成\n\n"
        f"- **行数**: `{rows}`\n- **耗时**: `{_elapsed:.1f}s`\n\n"
        f"{header}\n{sep}\n{body}"
    )


async def write_range(args: WriteRangeInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        await client.write_range(args.spreadsheet_token, args.range_str, args.values)
        _elapsed = time.time() - _t0
        rows = len(args.values)
        return (
            f"✅ 写入完成\n\n"
            f"- **range**: `{args.range_str}`\n"
            f"- **rows**: `{rows}`\n"
            f"- **耗时**: `{_elapsed:.1f}s`"
        )
    except Exception as e:
        return f"❌ 写入失败：{e}"


async def append_data(args: AppendDataInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        await client.append_data(
            args.spreadsheet_token, args.sheet_id, args.values,
            data_start=args.data_start,
        )
        _elapsed = time.time() - _t0
        rows = len(args.values)
        return (
            f"✅ 追加完成\n\n"
            f"- **sheet_id**: `{args.sheet_id}`\n"
            f"- **rows**: `{rows}`\n"
            f"- **耗时**: `{_elapsed:.1f}s`"
        )
    except Exception as e:
        return f"❌ 追加失败：{e}"


async def delete_dimension(args: DeleteDimensionInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        await client.delete_dimension(
            args.spreadsheet_token,
            args.sheet_id,
            major_dimension=args.major_dimension,
            start_index=args.start_index,
            end_index=args.end_index,
        )
        _elapsed = time.time() - _t0
        return (
            f"✅ 删除完成\n\n"
            f"- **dimension**: `{args.major_dimension}`\n"
            f"- **range**: `{args.start_index}` 到 `{args.end_index}`（1-based 含首尾）\n"
            f"- **耗时**: `{_elapsed:.1f}s`"
        )
    except Exception as e:
        return f"❌ 删除失败：{e}"
