"""多维表格域 mixin — 飞书 Bitable 操作"""

from __future__ import annotations

from typing import Any

from .base import _LarkMixinProtocol


class BitableMixin:
    """多维表格域方法（混入 _LarkBase 子类使用）"""

    async def create_record(
        self: _LarkMixinProtocol,
        app_token: str,
        table_id: str,
        fields: dict[str, Any],
    ) -> dict[str, Any]:
        """创建记录

        文档: https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-record/create
        """
        data = await self._post(
            f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records",
            json_data={"fields": fields},
        )
        return data.get("record", {})  # type: ignore[no-any-return]

    async def update_record(
        self: _LarkMixinProtocol,
        app_token: str,
        table_id: str,
        record_id: str,
        fields: dict[str, Any],
    ) -> dict[str, Any]:
        """更新记录

        文档: https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-record/update
        """
        data = await self._put(
            f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}",
            json_data={"fields": fields},
        )
        return data.get("record", {})  # type: ignore[no-any-return]

    async def delete_record(
        self: _LarkMixinProtocol,
        app_token: str,
        table_id: str,
        record_id: str,
    ) -> dict[str, Any]:
        """删除记录

        文档: https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-record/delete
        """
        await self._request(
            "DELETE",
            f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}",
        )
        return {"deleted": True}

    async def search_records(
        self: _LarkMixinProtocol,
        app_token: str,
        table_id: str,
        *,
        view_id: str | None = None,
        field_names: list[str] | None = None,
        sort: list[dict[str, Any]] | None = None,
        filter: dict[str, Any] | None = None,
        page_token: str | None = None,
        page_size: int | None = None,
        automatic_fields: bool | None = None,
        user_id_type: str | None = None,
    ) -> dict[str, Any]:
        """搜索多维表格记录，返回 {items, has_more, page_token, total}（最多 500 条）

        文档: https://open.feishu.cn/document/docs/bitable-v1/app-table-record/search
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

    async def batch_create_records(
        self: _LarkMixinProtocol,
        app_token: str,
        table_id: str,
        records: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """批量创建记录（最多 1000 条）

        文档: https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-record/batch_create
        """
        data = await self._post(
            f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create",
            json_data={"records": records},
        )
        return {"records": data.get("records", [])}

    async def batch_update_records(
        self: _LarkMixinProtocol,
        app_token: str,
        table_id: str,
        records: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """批量更新记录（最多 1000 条）

        文档: https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-record/batch_update
        """
        data = await self._post(
            f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_update",
            json_data={"records": records},
        )
        return {"records": data.get("records", [])}

    async def batch_get_records(
        self: _LarkMixinProtocol,
        app_token: str,
        table_id: str,
        record_ids: list[str],
        *,
        user_id_type: str | None = None,
        with_shared_url: bool | None = None,
        automatic_fields: bool | None = None,
    ) -> dict[str, Any]:
        """批量获取记录（最多 100 条）

        文档: https://open.feishu.cn/document/docs/bitable-v1/app-table-record/batch_get
        """
        body: dict[str, Any] = {"record_ids": record_ids}
        if user_id_type:
            body["user_id_type"] = user_id_type
        if with_shared_url is not None:
            body["with_shared_url"] = with_shared_url
        if automatic_fields is not None:
            body["automatic_fields"] = automatic_fields

        data = await self._post(
            f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_get",
            json_data=body,
        )
        return {"records": data.get("records", [])}

    async def batch_delete_records(
        self: _LarkMixinProtocol,
        app_token: str,
        table_id: str,
        record_ids: list[str],
    ) -> dict[str, Any]:
        """批量删除记录（最多 500 条）

        文档: https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-record/batch_delete
        """
        data = await self._post(
            f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_delete",
            json_data={"records": record_ids},
        )
        return {"records": data.get("records", [])}

    async def create_app(
        self: _LarkMixinProtocol,
        name: str,
        *,
        folder_token: str | None = None,
        time_zone: str | None = None,
    ) -> dict[str, Any]:
        """创建多维表格

        文档: https://open.feishu.cn/document/server-docs/docs/bitable-v1/app/create
        """
        body: dict[str, Any] = {"name": name}
        if folder_token:
            body["folder_token"] = folder_token
        if time_zone:
            body["time_zone"] = time_zone

        data = await self._post("/open-apis/bitable/v1/apps", json_data=body)
        return data.get("app", {})  # type: ignore[no-any-return]

    async def copy_app(
        self: _LarkMixinProtocol,
        app_token: str,
        *,
        name: str | None = None,
        folder_token: str | None = None,
        without_content: bool | None = None,
        time_zone: str | None = None,
    ) -> dict[str, Any]:
        """复制多维表格

        文档: https://open.feishu.cn/document/server-docs/docs/bitable-v1/app/copy
        """
        body: dict[str, Any] = {}
        if name:
            body["name"] = name
        if folder_token:
            body["folder_token"] = folder_token
        if without_content is not None:
            body["without_content"] = without_content
        if time_zone:
            body["time_zone"] = time_zone

        data = await self._post(
            f"/open-apis/bitable/v1/apps/{app_token}/copy",
            json_data=body or None,
        )
        return data.get("app", {})  # type: ignore[no-any-return]

    async def create_table(
        self: _LarkMixinProtocol,
        app_token: str,
        table: dict[str, Any],
    ) -> dict[str, Any]:
        """新增数据表

        文档: https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table/create
        """
        data = await self._post(
            f"/open-apis/bitable/v1/apps/{app_token}/tables",
            json_data={"table": table},
        )
        return {
            "table_id": data.get("table_id", ""),
            "field_id_list": data.get("field_id_list", []),
            "default_view_id": data.get("default_view_id", ""),
        }

    async def delete_table(
        self: _LarkMixinProtocol,
        app_token: str,
        table_id: str,
    ) -> dict[str, Any]:
        """删除数据表

        文档: https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table/delete
        """
        await self._request(
            "DELETE",
            f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}",
        )
        return {"deleted": True}
