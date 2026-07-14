"""多维表格快捷操作 MCP 工具"""

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


class BitableClearInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    app_token: str = Field(..., min_length=1, description="多维表格 app_token")
    table_id: str = Field(..., min_length=1, description="数据表 table_id")
    filter: dict[str, Any] | None = Field(None, description="筛选条件，只删除符合条件的数据")
    sort: list[dict[str, Any]] | None = Field(None, description="排序条件")


async def quick_bitable_clear(args: BitableClearInput) -> str:
    try:
        client = _get_client()
        result = await client.bitable_clear(
            args.app_token,
            args.table_id,
            filter=args.filter,
            sort=args.sort,
        )
    except Exception as e:
        return f"❌ 清空多维表格失败：{e}"

    deleted = result["totalDeleted"]
    failed = result["failedBatches"]
    total_batches = result["batchCount"]
    errors = result.get("errors", [])

    if total_batches == 0:
        return "无需删除，表中无数据"

    lines = [f"✅ 清空完成，共删除 {deleted} 条记录（{total_batches} 批）"]
    if failed > 0:
        lines.append(f"⚠️ 其中 {failed} 批失败")
        for err in errors:
            lines.append(f"  - {err}")
    return "\n".join(lines)
