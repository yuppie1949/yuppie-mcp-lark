"""多维表格域 MCP 工具"""

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


# ── 记录管理 ──


class CreateRecordInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    app_token: str = Field(..., min_length=1, description="多维表格 app_token")
    table_id: str = Field(..., min_length=1, description="数据表 table_id")
    fields: dict[str, Any] = Field(..., description="记录字段数据，如 {\"字段名\": \"字段值\"}")


class UpdateRecordInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    app_token: str = Field(..., min_length=1, description="多维表格 app_token")
    table_id: str = Field(..., min_length=1, description="数据表 table_id")
    record_id: str = Field(..., min_length=1, description="记录 ID")
    fields: dict[str, Any] = Field(..., description="记录字段数据")


class DeleteRecordInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    app_token: str = Field(..., min_length=1, description="多维表格 app_token")
    table_id: str = Field(..., min_length=1, description="数据表 table_id")
    record_id: str = Field(..., min_length=1, description="记录 ID")


class SearchRecordsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    app_token: str = Field(..., min_length=1, description="多维表格 app_token")
    table_id: str = Field(..., min_length=1, description="数据表 table_id")
    view_id: str | None = Field(None, description="视图 ID")
    field_names: list[str] | None = Field(None, description="指定返回字段名列表")
    sort: dict[str, Any] | None = Field(None, description="排序规则，如 {field_name, desc}")
    filter: dict[str, Any] | None = Field(None, description="过滤条件")
    page_token: str | None = Field(None, description="分页 token")
    page_size: int | None = Field(None, ge=1, le=500, description="分页大小")
    automatic_fields: bool | None = Field(None, description="是否返回自动计算字段")
    user_id_type: str | None = Field(None, description="用户 ID 类型：open_id / user_id / union_id")


class BatchCreateRecordsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    app_token: str = Field(..., min_length=1, description="多维表格 app_token")
    table_id: str = Field(..., min_length=1, description="数据表 table_id")
    records: list[dict[str, Any]] = Field(
        ..., description="记录列表，每条含 fields 字段，最多 1000 条"
    )


class BatchUpdateRecordsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    app_token: str = Field(..., min_length=1, description="多维表格 app_token")
    table_id: str = Field(..., min_length=1, description="数据表 table_id")
    records: list[dict[str, Any]] = Field(
        ..., description="记录列表，每条含 record_id 和 fields，最多 1000 条"
    )


class BatchGetRecordsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    app_token: str = Field(..., min_length=1, description="多维表格 app_token")
    table_id: str = Field(..., min_length=1, description="数据表 table_id")
    record_ids: list[str] = Field(
        ..., min_length=1, max_length=100, description="记录 ID 列表，最多 100 条"
    )
    user_id_type: str | None = Field(None, description="用户 ID 类型：open_id / user_id / union_id")
    with_shared_url: bool | None = Field(None, description="是否返回分享链接")
    automatic_fields: bool | None = Field(None, description="是否返回自动计算字段")


class BatchDeleteRecordsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    app_token: str = Field(..., min_length=1, description="多维表格 app_token")
    table_id: str = Field(..., min_length=1, description="数据表 table_id")
    record_ids: list[str] = Field(
        ..., min_length=1, max_length=500, description="记录 ID 列表，最多 500 条"
    )


# ── 应用/表格管理 ──


class CreateAppInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(..., min_length=1, max_length=255, description="多维表格名称")
    folder_token: str | None = Field(None, description="文件夹 token")
    time_zone: str | None = Field(None, description="文档时区")


class CopyAppInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    app_token: str = Field(..., min_length=1, description="要复制的多维表格 app_token")
    name: str | None = Field(None, description="新表格名称")
    folder_token: str | None = Field(None, description="目标文件夹 token")
    without_content: bool | None = Field(None, description="是否仅复制结构（不复制内容）")
    time_zone: str | None = Field(None, description="文档时区")


class CreateTableInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    app_token: str = Field(..., min_length=1, description="多维表格 app_token")
    table: dict[str, Any] = Field(..., description="数据表定义，含 name、fields 等")


class DeleteTableInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    app_token: str = Field(..., min_length=1, description="多维表格 app_token")
    table_id: str = Field(..., min_length=1, description="要删除的数据表 ID")


# ── 工具函数 ──


async def create_record(args: CreateRecordInput) -> str:
    try:
        client = _get_client()
        record = await client.create_record(args.app_token, args.table_id, args.fields)
    except Exception as e:
        return f"❌ 创建记录失败：{e}"
    return (
        f"✅ 创建记录成功\n\n"
        f"- **record_id**: `{record.get('record_id', '')}`\n"
        f"- **fields**: `{record.get('fields', {})}`"
    )


async def update_record(args: UpdateRecordInput) -> str:
    try:
        client = _get_client()
        record = await client.update_record(
            args.app_token, args.table_id, args.record_id, args.fields
        )
    except Exception as e:
        return f"❌ 更新记录失败：{e}"
    return (
        f"✅ 更新记录成功\n\n"
        f"- **record_id**: `{record.get('record_id', '')}`\n"
        f"- **fields**: `{record.get('fields', {})}`"
    )


async def delete_record(args: DeleteRecordInput) -> str:
    try:
        client = _get_client()
        await client.delete_record(args.app_token, args.table_id, args.record_id)
    except Exception as e:
        return f"❌ 删除记录失败：{e}"
    return f"✅ 已删除记录 `{args.record_id}`"


async def search_records(args: SearchRecordsInput) -> str:
    try:
        client = _get_client()
        data = await client.search_records(
            args.app_token,
            args.table_id,
            view_id=args.view_id,
            field_names=args.field_names,
            sort=args.sort,
            filter=args.filter,
            page_token=args.page_token,
            page_size=args.page_size,
            automatic_fields=args.automatic_fields,
            user_id_type=args.user_id_type,
        )
    except Exception as e:
        return f"❌ 搜索失败：{e}"

    items = data.get("items", [])
    total = data.get("total", 0)
    has_more = data.get("has_more", False)
    page_token = data.get("page_token", "")
    if not items:
        return "查询完成，无匹配记录"

    keys = list(items[0].keys())
    header = "| " + " | ".join(keys) + " |"
    sep = "| " + " | ".join("---" for _ in keys) + " |"
    body = "\n".join("| " + " | ".join(str(item.get(k, "")) for k in keys) + " |" for item in items)
    more_hint = f"\n\n> 还有更多数据，page_token=`{page_token}`" if has_more else ""
    return f"查询完成，共 {total} 条记录\n\n{header}\n{sep}\n{body}{more_hint}"


async def batch_create_records(args: BatchCreateRecordsInput) -> str:
    try:
        client = _get_client()
        result = await client.batch_create_records(args.app_token, args.table_id, args.records)
    except Exception as e:
        return f"❌ 批量创建记录失败：{e}"
    records = result.get("records", [])
    return f"✅ 批量创建记录成功，共 {len(records)} 条"


async def batch_update_records(args: BatchUpdateRecordsInput) -> str:
    try:
        client = _get_client()
        result = await client.batch_update_records(args.app_token, args.table_id, args.records)
    except Exception as e:
        return f"❌ 批量更新记录失败：{e}"
    records = result.get("records", [])
    return f"✅ 批量更新记录成功，共 {len(records)} 条"


async def batch_get_records(args: BatchGetRecordsInput) -> str:
    try:
        client = _get_client()
        result = await client.batch_get_records(
            args.app_token,
            args.table_id,
            args.record_ids,
            user_id_type=args.user_id_type,
            with_shared_url=args.with_shared_url,
            automatic_fields=args.automatic_fields,
        )
    except Exception as e:
        return f"❌ 批量获取记录失败：{e}"
    records = result.get("records", [])
    if not records:
        return "未找到记录"
    keys = list(records[0].get("fields", {}).keys())
    header = "| record_id | " + " | ".join(keys) + " |"
    sep = "| --- | " + " | ".join("---" for _ in keys) + " |"
    body = "\n".join(
        "| " + r.get("record_id", "")
        + " | " + " | ".join(str(r.get("fields", {}).get(k, "")) for k in keys)
        + " |"
        for r in records
    )
    return f"共 {len(records)} 条记录\n\n{header}\n{sep}\n{body}"


async def batch_delete_records(args: BatchDeleteRecordsInput) -> str:
    try:
        client = _get_client()
        await client.batch_delete_records(args.app_token, args.table_id, args.record_ids)
    except Exception as e:
        return f"❌ 批量删除记录失败：{e}"
    return f"✅ 已批量删除 {len(args.record_ids)} 条记录"


async def create_app(args: CreateAppInput) -> str:
    try:
        client = _get_client()
        app = await client.create_app(
            args.name, folder_token=args.folder_token, time_zone=args.time_zone
        )
    except Exception as e:
        return f"❌ 创建多维表格失败：{e}"
    return (
        f"✅ 创建多维表格成功\n\n"
        f"- **app_token**: `{app.get('app_token', '')}`\n"
        f"- **name**: {app.get('name', '')}\n"
        f"- **url**: {app.get('url', '')}\n"
        f"- **default_table_id**: `{app.get('default_table_id', '')}`"
    )


async def copy_app(args: CopyAppInput) -> str:
    try:
        client = _get_client()
        app = await client.copy_app(
            args.app_token,
            name=args.name,
            folder_token=args.folder_token,
            without_content=args.without_content,
            time_zone=args.time_zone,
        )
    except Exception as e:
        return f"❌ 复制多维表格失败：{e}"
    return (
        f"✅ 复制多维表格成功\n\n"
        f"- **app_token**: `{app.get('app_token', '')}`\n"
        f"- **name**: {app.get('name', '')}\n"
        f"- **url**: {app.get('url', '')}"
    )


async def create_table(args: CreateTableInput) -> str:
    try:
        client = _get_client()
        result = await client.create_table(args.app_token, args.table)
    except Exception as e:
        return f"❌ 创建数据表失败：{e}"
    return (
        f"✅ 创建数据表成功\n\n"
        f"- **table_id**: `{result.get('table_id', '')}`\n"
        f"- **default_view_id**: `{result.get('default_view_id', '')}`\n"
        f"- **field_id_list**: `{result.get('field_id_list', [])}`"
    )


async def delete_table(args: DeleteTableInput) -> str:
    try:
        client = _get_client()
        await client.delete_table(args.app_token, args.table_id)
    except Exception as e:
        return f"❌ 删除数据表失败：{e}"
    return f"✅ 已删除数据表 `{args.table_id}`"
