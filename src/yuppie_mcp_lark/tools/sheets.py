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

class ReadRangesInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_token: str = Field(..., min_length=1, description="电子表格 token")
    ranges: str = Field(..., min_length=1, description='多个范围，逗号分隔，如 "sheetId1!A2:B6,sheetId2!B1:C8"')
    value_render_option: str | None = Field(None, description='值渲染选项：ToString / Formula / FormattedValue / UnformattedValue')
    date_time_render_option: str | None = Field(None, description='日期时间渲染选项：FormattedString')
    user_id_type: str | None = Field(None, description='用户 ID 类型：open_id / union_id')


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

class UpdateDimensionInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_token: str = Field(..., min_length=1, description="电子表格 token")
    sheet_id: str = Field(..., min_length=1, description="工作表 ID")
    major_dimension: str = Field("ROWS", description="维度：ROWS（行）或 COLUMNS（列）")
    start_index: int = Field(..., ge=1, description="起始位置（1-based 含）")
    end_index: int = Field(..., ge=1, description="结束位置（1-based 含）")
    fixed_size: int | None = Field(None, description="行高或列宽（像素）")
    visible: bool | None = Field(None, description="是否显示行或列")

class WriteImageInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_token: str = Field(..., min_length=1, description="电子表格 token")
    range: str = Field(..., min_length=1, description='单元格范围，如 "sheetId!A1:A1"')
    image_base64: str = Field(..., min_length=1, description="图片 base64 编码内容")
    name: str = Field(..., min_length=1, description='图片文件名，含后缀，如 "test.png"')

class StylesBatchUpdateInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_token: str = Field(..., min_length=1, description="电子表格 token")
    data: list[dict[str, Any]] = Field(
        ...,
        description='样式数据数组，每项含 ranges（范围列表）和 style（样式对象）',
    )

class CreateSpreadsheetInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: str = Field(..., min_length=1, description="电子表格标题")
    folder_token: str | None = Field(None, description="文件夹 token")


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
            f"- **耗时**: `{_elapsed:.1f}s`\n"
            f"- **title**: `{args.title}`\n"
            f"- **sheetId**: `{sheet_id}`\n"
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
        vr = await client.read_range(args.spreadsheet_token, args.range_str)
        _elapsed = time.time() - _t0
    except Exception as e:
        return f"❌ 读取失败：{e}"
    values = vr.get("values", [])
    if not values:
        return f"查询完成\n\n- **行数**: `0`\n- **耗时**: `{_elapsed:.1f}s`"
    rows = len(values)
    cols = max(len(r) for r in values)
    header = "| " + " | ".join(f"col{i}" for i in range(cols)) + " |"
    sep = "| " + " | ".join("---" for _ in range(cols)) + " |"
    body = "\n".join(
        "| " + " | ".join(str(r[i]) if i < len(r) else "" for i in range(cols)) + " |"
        for r in values
    )
    return (
        f"查询完成\n\n"
        f"- **行数**: `{rows}`\n- **耗时**: `{_elapsed:.1f}s`\n\n"
        f"{header}\n{sep}\n{body}"
    )

async def read_ranges(args: ReadRangesInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        value_ranges = await client.read_ranges(
            args.spreadsheet_token,
            args.ranges,
            value_render_option=args.value_render_option,
            date_time_render_option=args.date_time_render_option,
            user_id_type=args.user_id_type,
        )
        _elapsed = time.time() - _t0
    except Exception as e:
        return f"❌ 读取失败：{e}"

    if not value_ranges:
        return "未读取到数据"

    lines = [f"✅ 读取完成（{_elapsed:.1f}s）\n"]
    for vr in value_ranges:
        range_name = vr.get("range", "?")
        values = vr.get("values", [])
        if not values:
            continue
        keys = values[0]
        section = [f"### {range_name}"]
        header = "| " + " | ".join(str(k) for k in keys) + " |"
        sep = "| " + " | ".join("---" for _ in keys) + " |"
        body = "\n".join(
            "| " + " | ".join(str(cell) for cell in row) + " |"
            for row in values[1:]
        )
        section.append(header)
        section.append(sep)
        section.append(body)
        lines.append("\n".join(section))
    return "\n\n".join(lines)


async def write_range(args: WriteRangeInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        await client.write_range(args.spreadsheet_token, args.range_str, args.values)
        _elapsed = time.time() - _t0
        rows = len(args.values)
        return (
            f"✅ 写入完成\n\n"
            f"- **耗时**: `{_elapsed:.1f}s`\n"
            f"- **range**: `{args.range_str}`\n"
            f"- **rows**: `{rows}`\n"
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
            f"- **耗时**: `{_elapsed:.1f}s`\n"
            f"- **sheet_id**: `{args.sheet_id}`\n"
            f"- **rows**: `{rows}`\n"
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
            f"- **耗时**: `{_elapsed:.1f}s`\n"
            f"- **dimension**: `{args.major_dimension}`\n"
            f"- **range**: `{args.start_index}` 到 `{args.end_index}`（1-based 含首尾）\n"
        )
    except Exception as e:
        return f"❌ 删除失败：{e}"


async def write_image(args: WriteImageInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        result = await client.write_image(
            args.spreadsheet_token, args.range, args.image_base64, args.name
        )
        _elapsed = time.time() - _t0
    except Exception as e:
        return f"❌ 写入图片失败：{e}"
    return (
        f"✅ 图片已写入\n\n"
        f"- **range**: `{result.get('updateRange', '')}`\n"
        f"- **name**: `{args.name}`\n"
        f"- **耗时**: `{_elapsed:.1f}s`"
    )

async def update_dimension(args: UpdateDimensionInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        await client.update_dimension(
            args.spreadsheet_token,
            args.sheet_id,
            major_dimension=args.major_dimension,
            start_index=args.start_index,
            end_index=args.end_index,
            fixed_size=args.fixed_size,
            visible=args.visible,
        )
        _elapsed = time.time() - _t0
    except Exception as e:
        return f"❌ 更新行列失败：{e}"
    return (
        f"✅ 行列属性已更新\n\n"
        f"- **耗时**: `{_elapsed:.1f}s`\n"
        f"- **dimension**: `{args.major_dimension}`\n"
        f"- **range**: `{args.start_index}` 到 `{args.end_index}`（1-based 含首尾）\n"
    )

async def styles_batch_update(args: StylesBatchUpdateInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        result = await client.styles_batch_update(args.spreadsheet_token, args.data)
        _elapsed = time.time() - _t0
    except Exception as e:
        return f"❌ 批量设置样式失败：{e}"
    total = result.get("totalUpdatedCells", 0)
    return (
        f"✅ 样式已更新\n\n"
        f"- **更新单元格数**: `{total}`\n"
        f"- **耗时**: `{_elapsed:.1f}s`"
    )

async def create_spreadsheet(args: CreateSpreadsheetInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        result = await client.create_spreadsheet(
            args.title, folder_token=args.folder_token
        )
        _elapsed = time.time() - _t0
    except Exception as e:
        return f"❌ 创建电子表格失败：{e}"
    data = result.get("spreadsheet", {})
    return (
        f"✅ 电子表格已创建\n\n"
        f"- **title**: `{data.get('title', '')}`\n"
        f"- **spreadsheet_token**: `{data.get('spreadsheet_token', '')}`\n"
        f"- **url**: {data.get('url', '')}\n"
        f"- **耗时**: `{_elapsed:.1f}s`"
    )


async def get_spreadsheet(args: GetMetainfoInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        data = await client.get_spreadsheet(args.spreadsheet_token)
        _elapsed = time.time() - _t0
    except Exception as e:
        return f"❌ 获取电子表格信息失败：{e}"
    sp = data.get("spreadsheet", {})
    return (
        f"✅ 查询完成\n\n"
        f"- **title**: `{sp.get('title', '')}`\n"
        f"- **spreadsheet_token**: `{sp.get('token', '')}`\n"
        f"- **url**: {sp.get('url', '')}\n"
        f"- **耗时**: `{_elapsed:.1f}s`"
    )


async def query_sheets(args: GetMetainfoInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        data = await client.query_sheets(args.spreadsheet_token)
        _elapsed = time.time() - _t0
    except Exception as e:
        return f"❌ 查询工作表失败：{e}"
    sheets = data.get("sheets", [])
    if not sheets:
        return f"未找到工作表\n- **耗时**: `{_elapsed:.1f}s`"
    lines = [f"✅ 查询完成，共 {len(sheets)} 个工作表\n"]
    lines.append(f"- **耗时**: `{_elapsed:.1f}s`")
    lines.append("| index | title | sheet_id | resource_type | hidden |")
    lines.append("| --- | --- | --- | --- | --- |")
    for s in sheets:
        lines.append(
            f"| {s.get('index', '')} | {s.get('title', '')} | {s.get('sheet_id', '')} | "
            f"{s.get('resource_type', '')} | {s.get('hidden', '')} |"
        )
    return "\n".join(lines)
