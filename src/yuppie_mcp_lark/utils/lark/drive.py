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
