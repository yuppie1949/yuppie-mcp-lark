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
