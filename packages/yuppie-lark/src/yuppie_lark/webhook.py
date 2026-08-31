"""Webhook 域 mixin — 飞书自定义机器人（群机器人 webhook）消息推送

与 MessagesMixin（tenant_access_token 应用通道）相互独立：webhook 无需应用鉴权、
无法指定接收人，通过 HMAC-SHA256 签名（timestamp\\nsecret）校验来源，只能发送、
不能更新/撤回。接口参考 docs/lark-custom-bot-webhook.md。
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any

from .base import _LarkMixinProtocol

_MAX_WEBHOOK_BODY_BYTES = 20 * 1024


class WebhookMixin:
    """自定义机器人 webhook 方法（混入 _LarkBase 子类使用）"""

    @staticmethod
    def _sign(timestamp: str, secret: str) -> str:
        """飞书 webhook 签名：`timestamp + "\\n" + secret` → HmacSHA256 → Base64。"""
        string_to_sign = f"{timestamp}\n{secret}"
        digest = hmac.new(string_to_sign.encode("utf-8"), digestmod=hashlib.sha256).digest()
        return base64.b64encode(digest).decode("utf-8")

    async def _send_webhook(
        self: _LarkMixinProtocol,
        url: str,
        body: dict[str, Any],
        *,
        secret: str | None = None,
        timeout: float = 30,
    ) -> dict[str, Any]:
        """POST 到指定 webhook 地址，可选签名注入，校验 code==0。

        限制：单请求体 ≤ 20KB；webhook 仅单向发送，无更新/撤回能力。
        官方文档：https://open.feishu.cn/document/client-docs/bot-v3/add-custom-bot?lang=zh-CN#756b882f
        """
        if secret:
            ts = str(int(time.time()))
            body = {**body, "timestamp": ts, "sign": self._sign(ts, secret)}
        payload = json.dumps(body, ensure_ascii=False)
        if len(payload.encode("utf-8")) > _MAX_WEBHOOK_BODY_BYTES:
            raise Exception("[webhook] 请求体超过 20KB，飞书自定义机器人限制单消息 ≤ 20KB")
        resp = await self._get_http().post(
            url,
            content=payload,
            headers={"Content-Type": "application/json"},
            timeout=timeout,
        )
        try:
            data = resp.json()
        except json.JSONDecodeError as e:
            body_text = resp.text[:200]
            raise Exception(
                f"[webhook] 响应非 JSON（HTTP {resp.status_code}）: {e}。原始响应: {body_text}"
            ) from e
        if data.get("code") != 0:
            raise Exception(f"[webhook] 发送失败(code={data.get('code')}): {data.get('msg', '')}")
        return data.get("data", {})  # type: ignore[no-any-return]

    async def send_webhook_card(
        self: _LarkMixinProtocol,
        url: str,
        card: dict[str, Any],
        *,
        secret: str | None = None,
        timeout: float = 30,
    ) -> dict[str, Any]:
        """发送卡片消息（msg_type=interactive + 顶层 card 结构体）"""
        return await self._send_webhook(
            url,
            {"msg_type": "interactive", "card": card},
            secret=secret,
            timeout=timeout,
        )

    async def send_webhook_text(
        self: _LarkMixinProtocol,
        url: str,
        content: str,
        *,
        secret: str | None = None,
        timeout: float = 30,
    ) -> dict[str, Any]:
        """发送文本消息（msg_type=text）"""
        return await self._send_webhook(
            url,
            {"msg_type": "text", "content": {"text": content}},
            secret=secret,
            timeout=timeout,
        )
