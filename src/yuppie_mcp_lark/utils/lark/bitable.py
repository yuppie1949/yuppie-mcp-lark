"""多维表格域 mixin — 飞书 Bitable 记录搜索"""

from __future__ import annotations

from typing import Any

from .base import _LarkMixinProtocol


class BitableMixin:
    """多维表格域方法（混入 _LarkBase 子类使用）"""

    async def search_records(
        self: _LarkMixinProtocol,
        app_token: str,
        table_id: str,
        *,
        view_id: str | None = None,
        field_names: list[str] | None = None,
        sort: dict[str, Any] | None = None,
        filter: dict[str, Any] | None = None,
        page_token: str | None = None,
        page_size: int | None = None,
        automatic_fields: bool | None = None,
        user_id_type: str | None = None,
    ) -> dict[str, Any]:
        """搜索多维表格记录，返回 {items, has_more, page_token, total}

        文档: https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-record/search
        """
        params: dict[str, Any] = {}
        if user_id_type:
            params["user_id_type"] = user_id_type
        if page_token:
            params["page_token"] = page_token
        if page_size is not None:
            params["page_size"] = page_size

        body: dict[str, Any] = {}
        if view_id:
            body["view_id"] = view_id
        if field_names:
            body["field_names"] = field_names
        if sort:
            body["sort"] = sort
        if filter:
            body["filter"] = filter
        if automatic_fields is not None:
            body["automatic_fields"] = automatic_fields

        data = await self._request(
            "POST",
            f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/search",
            params=params or None,
            json_data=body,
        )
        return {
            "items": data.get("items", []),
            "has_more": data.get("has_more", False),
            "page_token": data.get("page_token", ""),
            "total": data.get("total", 0),
        }
