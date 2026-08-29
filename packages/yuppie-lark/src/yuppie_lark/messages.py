"""消息域 mixin — 飞书 IM 消息发送"""

from __future__ import annotations

import json
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

    async def send_card(
        self: _LarkMixinProtocol,
        receive_id: str,
        card: dict[str, Any],
        *,
        receive_id_type: str = "chat_id",
        uuid: str | None = None,
    ) -> dict[str, Any]:
        """发送卡片消息。card 为卡片 schema dict，内部 json.dumps 转 content。
        默认 receive_id_type=chat_id（进度卡片发群），单聊传 open_id。
        """
        return await self.send_message(
            receive_id,
            "interactive",
            json.dumps(card, ensure_ascii=False),
            receive_id_type=receive_id_type,
            uuid=uuid,
        )

    async def update_message(
        self: _LarkMixinProtocol,
        message_id: str,
        content: str,
        *,
        msg_type: str = "interactive",
    ) -> dict[str, Any]:
        """更新消息（原地 PATCH）
        文档: https://open.feishu.cn/document/server-docs/im-v1/message/update
        """
        return await self._request(
            "PATCH",
            f"/open-apis/im/v1/messages/{message_id}",
            json_data={"content": content, "msg_type": msg_type},
        )

    async def update_card(
        self: _LarkMixinProtocol,
        message_id: str,
        card: dict[str, Any],
    ) -> dict[str, Any]:
        """原地更新卡片消息。card 为新的卡片 schema dict。"""
        return await self.update_message(
            message_id,
            json.dumps(card, ensure_ascii=False),
        )
