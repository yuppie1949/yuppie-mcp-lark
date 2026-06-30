"""消息域 mixin — 飞书 IM 消息发送"""

from __future__ import annotations

from typing import Any

from .base import _LarkMixinProtocol


class MessagesMixin:
    """消息域方法（混入 _LarkBase 子类使用）"""

    async def send_message(
        self: _LarkMixinProtocol,
        receive_id: str,
        msg_type: str,
        content: str,
        *,
        receive_id_type: str = "open_id",
        uuid: str | None = None,
    ) -> dict[str, Any]:
        """发送消息给单个用户/群
        文档: https://open.feishu.cn/document/server-docs/im-v1/message/create
        发送消息内容结构: https://open.feishu.cn/document/server-docs/im-v1/message-content-description/create_json
        """
        body: dict[str, Any] = {
            "receive_id": receive_id,
            "msg_type": msg_type,
            "content": content,
        }
        if uuid is not None:
            body["uuid"] = uuid
        return await self._request(
            "POST",
            "/open-apis/im/v1/messages",
            params={"receive_id_type": receive_id_type},
            json_data=body,
        )

    async def send_messages(
        self: _LarkMixinProtocol,
        receive_ids: list[str],
        msg_type: str,
        content: str,
        *,
        receive_id_type: str = "open_id",
        uuid: str | None = None,
    ) -> list[dict[str, Any]]:
        """批量发送消息，返回 [{receive_id, message_id, error?}] 列表"""
        results: list[dict[str, Any]] = []
        for uid in receive_ids:
            try:
                data = await self.send_message(
                    uid, msg_type, content, receive_id_type=receive_id_type, uuid=uuid
                )
                results.append({"receive_id": uid, "message_id": data.get("message_id", "")})
            except Exception as e:
                results.append({"receive_id": uid, "message_id": "", "error": str(e)})
        return results
