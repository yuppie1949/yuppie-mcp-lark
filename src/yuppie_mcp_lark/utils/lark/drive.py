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
