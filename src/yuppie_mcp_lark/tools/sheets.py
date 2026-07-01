"""电子表格域 MCP 工具"""

from __future__ import annotations

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


class DeleteDimensionInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_token: str = Field(..., min_length=1, description="电子表格 token")
    sheet_id: str = Field(..., min_length=1, description="工作表 ID")
    major_dimension: str = Field("COLUMNS", description="COLUMNS 或 ROWS，默认 COLUMNS")
    start_index: int = Field(..., ge=1, description="起始索引（1-based 含）")
    end_index: int = Field(..., ge=1, description="结束索引（1-based 含）")


async def get_metainfo(args: GetMetainfoInput) -> str:
    try:
        client = _get_client()
        data = await client.get_metainfo(args.spreadsheet_token)
    except Exception as e:
        return f"❌ 获取元信息失败：{e}"
    sheets = data.get("sheets", [])
    lines = [f"标题: **{data.get('title', '')}**", ""]
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
        client = _get_client()
        sheet_id = await client.add_sheet(args.spreadsheet_token, args.title)
        return f"✅ 工作表已创建\n\n- **title**: `{args.title}`\n- **sheetId**: `{sheet_id}`"
    except Exception as e:
        return f"❌ 创建工作表失败：{e}"


async def delete_sheet(args: DeleteSheetInput) -> str:
    try:
        client = _get_client()
        await client.delete_sheet(args.spreadsheet_token, args.sheet_id)
        return f"✅ 工作表已删除\n\n- **sheetId**: `{args.sheet_id}`"
    except Exception as e:
        return f"❌ 删除工作表失败：{e}"


async def copy_sheet(args: CopySheetInput) -> str:
    try:
        client = _get_client()
        sheet_id = await client.copy_sheet(args.spreadsheet_token, args.source_sheet_id, args.title)
        return (
            f"✅ 工作表已复制\n\n"
            f"- **source_sheet_id**: `{args.source_sheet_id}`\n"
            f"- **new_sheetId**: `{sheet_id}`"
        )
    except Exception as e:
        return f"❌ 复制工作表失败：{e}"


async def read_range(args: ReadRangeInput) -> str:
    try:
        client = _get_client()
        data = await client.read_range(args.spreadsheet_token, args.range_str)
    except Exception as e:
        return f"❌ 读取失败：{e}"
    if not data:
        return "范围为空"
    rows = len(data)
    cols = max(len(r) for r in data)
    preview_rows = data[:10]
    header = "| " + " | ".join(f"col{i}" for i in range(cols)) + " |"
    sep = "| " + " | ".join("---" for _ in range(cols)) + " |"
    body = "\n".join(
        "| " + " | ".join(str(r[i]) if i < len(r) else "" for i in range(cols)) + " |"
        for r in preview_rows
    )
    truncated = f"\n\n> 共 {rows} 行，仅显示前 10 行" if rows > 10 else ""
    return f"读取完成（{rows} 行 × {cols} 列）\n\n{header}\n{sep}\n{body}{truncated}"


async def write_range(args: WriteRangeInput) -> str:
    try:
        client = _get_client()
        await client.write_range(args.spreadsheet_token, args.range_str, args.values)
        rows = len(args.values)
        return f"✅ 写入完成\n\n- **range**: `{args.range_str}`\n- **rows**: `{rows}`"
    except Exception as e:
        return f"❌ 写入失败：{e}"


async def append_data(args: AppendDataInput) -> str:
    try:
        client = _get_client()
        await client.append_data(args.spreadsheet_token, args.sheet_id, args.values)
        rows = len(args.values)
        return f"✅ 追加完成\n\n- **sheet_id**: `{args.sheet_id}`\n- **rows**: `{rows}`"
    except Exception as e:
        return f"❌ 追加失败：{e}"


# ── 业务批量工具 ──


async def delete_dimension(args: DeleteDimensionInput) -> str:
    try:
        client = _get_client()
        await client.delete_dimension(
            args.spreadsheet_token,
            args.sheet_id,
            major_dimension=args.major_dimension,
            start_index=args.start_index,
            end_index=args.end_index,
        )
        return (
            f"✅ 删除完成\n\n"
            f"- **dimension**: `{args.major_dimension}`\n"
            f"- **range**: `{args.start_index}` 到 `{args.end_index}`（1-based 含首尾）"
        )
    except Exception as e:
        return f"❌ 删除失败：{e}"
