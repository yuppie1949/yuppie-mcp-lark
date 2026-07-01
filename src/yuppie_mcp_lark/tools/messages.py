"""消息域 MCP 工具"""

from __future__ import annotations

from typing import Literal

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


class SendMessageInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    receive_id: str = Field(..., min_length=1, description="接收者 ID")
    msg_type: Literal[
        "text",
        "post",
        "image",
        "file",
        "audio",
        "media",
        "interactive",
    ] = Field("text", description="消息类型，默认 text")
    content: str = Field(
        ...,
        min_length=1,
        max_length=30000,
        description="消息内容 JSON 字符串，文本≤150KB，卡片/富文本≤30KB",
    )
    receive_id_type: str = Field(
        "open_id", description="ID 类型：open_id / user_id / union_id / chat_id"
    )
    uuid: str | None = Field(
        None,
        max_length=50,
        description="去重序列号，相同 uuid 在 1 小时内至多发送一条消息",
    )


async def send_message(args: SendMessageInput) -> str:
    try:
        client = _get_client()
        data = await client.send_message(
            args.receive_id,
            args.msg_type,
            args.content,
            receive_id_type=args.receive_id_type,
            uuid=args.uuid,
        )
        return (
            "✅ 发送成功\n\n"
            f"- **message_id**: `{data.get('message_id', '')}`\n"
            f"- **receive_id**: `{args.receive_id}`\n"
            f"- **msg_type**: `{args.msg_type}`"
        )
    except Exception as e:
        return f"❌ 发送失败：{e}"
