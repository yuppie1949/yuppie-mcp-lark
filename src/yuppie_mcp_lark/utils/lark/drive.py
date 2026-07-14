"""云文档域 mixin — 飞书 Drive 文件操作"""

from __future__ import annotations

from typing import Any

from .base import _LarkMixinProtocol


class DriveMixin:
    """云文档域方法（混入 _LarkBase 子类使用）"""

    async def copy_file(
        self: _LarkMixinProtocol,
        file_token: str,
        name: str,
        folder_token: str,
        file_type: str,
        *,
        user_id_type: str | None = None,
    ) -> dict[str, Any]:
        """复制文件到指定文件夹
        使用限制
            该接口调用频率上限为 5 QPS，10000 次/天。否则会返回 1061045 错误码，可通过稍后重试解决。

        文档: https://open.feishu.cn/document/server-docs/docs/drive-v1/file/copy
        """
        body: dict[str, Any] = {
            "name": name,
            "folder_token": folder_token,
            "type": file_type,
        }
        params: dict[str, Any] = {}
        if user_id_type:
            params["user_id_type"] = user_id_type

        return await self._request(
            "POST",
            f"/open-apis/drive/v1/files/{file_token}/copy",
            params=params,
            json_data=body,
        )

    async def delete_file(
        self: _LarkMixinProtocol,
        file_token: str,
        file_type: str,
    ) -> dict[str, Any]:
        """删除文件或文件夹
        使用限制
            该接口不支持并发调用，且调用频率上限为 5 QPS，10000 次/天。否则会返回 1061045 错误码，可通过稍后重试解决。
        返回
            删除文件：{"data":{}}
            删除文件夹：{"data":{"task_id":"xxx"}}
        文档: https://open.feishu.cn/document/server-docs/docs/drive-v1/file/delete
        """
        return await self._request(
            "DELETE",
            f"/open-apis/drive/v1/files/{file_token}",
            params={"type": file_type},
        )

    async def check_task(
        self: _LarkMixinProtocol,
        task_id: str,
    ) -> dict[str, Any]:
        """查询异步任务状态（删除/移动文件夹）

        文档: https://open.feishu.cn/document/server-docs/docs/drive-v1/file/task_check
        """
        return await self._get(
            "/open-apis/drive/v1/files/task_check",
            params={"task_id": task_id},
        )

    async def upload_file(
        self: _LarkMixinProtocol,
        file_path: str,
        parent_node: str,
        *,
        file_name: str | None = None,
        checksum: str | None = None,
    ) -> dict[str, Any]:
        """上传文件到云空间指定文件夹（最大 20 MB）

        使用限制
            文件大小不得超过 20 MB，且不可上传空文件。
            该接口调用频率上限为 5 QPS，10000 次/天。否则会返回 1061045 错误码，可通过稍后重试解决。

        文档: https://open.feishu.cn/document/server-docs/docs/drive-v1/file/upload_all
        """
        import os

        resolved = os.path.abspath(file_path)
        file_size = os.path.getsize(resolved)
        if file_size > 20 * 1024 * 1024:
            raise Exception(f"文件超过 20 MB 限制（{file_size} bytes），请使用分片上传")
        if file_size == 0:
            raise Exception("文件为空，不允许上传")
        name = file_name or os.path.basename(resolved)
        form_data: dict[str, Any] = {
            "file_name": name,
            "parent_type": "explorer",
            "parent_node": parent_node,
            "size": str(file_size),
        }
        if checksum:
            form_data["checksum"] = checksum

        with open(resolved, "rb") as f:
            files = {"file": (name, f, "application/octet-stream")}
            return await self._upload(
                "POST",
                "/open-apis/drive/v1/files/upload_all",
                data=form_data,
                files=files,
            )

    async def list_files(
        self: _LarkMixinProtocol,
        *,
        folder_token: str | None = None,
        page_size: int | None = None,
        page_token: str | None = None,
        order_by: str | None = None,
        direction: str | None = None,
        user_id_type: str | None = None,
    ) -> dict[str, Any]:
        """获取文件夹中的文件清单

        文档: https://open.feishu.cn/document/server-docs/docs/drive-v1/file/list
        """
        params: dict[str, Any] = {}
        if folder_token:
            params["folder_token"] = folder_token
        if page_size is not None:
            params["page_size"] = page_size
        if page_token:
            params["page_token"] = page_token
        if order_by:
            params["order_by"] = order_by
        if direction:
            params["direction"] = direction
        if user_id_type:
            params["user_id_type"] = user_id_type

        return await self._get("/open-apis/drive/v1/files", params=params)
