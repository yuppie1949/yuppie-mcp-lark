"""WebhookMixin 请求级测试（httpx.MockTransport 拦截，不联网）

验证：card/text 两种消息体、签名注入（与官方算法独立复算对比）、
code!=0 抛错、非 JSON 响应抛错、请求体 >20KB 抛出清晰错误。
"""

import base64
import hashlib
import hmac
import json
from collections.abc import Callable

import httpx
import pytest
from yuppie_lark import LarkClient

Handler = Callable[[httpx.Request], httpx.Response]

WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/test"


def _make_client(handler: Handler) -> LarkClient:
    client = LarkClient("app_id", "app_secret")
    client._http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return client


def _gen_sign(timestamp: str, secret: str) -> str:
    """独立复算官方 gen_sign，用于验证库内 _sign"""
    string_to_sign = f"{timestamp}\n{secret}"
    digest = hmac.new(string_to_sign.encode("utf-8"), digestmod=hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


def _ok_handler(captured: dict) -> Handler:
    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["url"] = str(request.url)
        captured["headers"] = dict(request.headers)
        captured["json"] = json.loads(request.read())
        return httpx.Response(200, json={"code": 0, "data": {}, "msg": "success"})

    return handler


@pytest.mark.asyncio
async def test_send_webhook_card_body_and_no_secret() -> None:
    captured: dict = {}
    client = _make_client(_ok_handler(captured))
    card = {"header": {"title": {"tag": "plain_text", "content": "通知"}}, "elements": []}

    await client.send_webhook_card(WEBHOOK_URL, card)

    assert captured["method"] == "POST"
    assert captured["url"] == WEBHOOK_URL
    assert captured["headers"]["content-type"] == "application/json"
    assert captured["json"]["msg_type"] == "interactive"
    assert captured["json"]["card"] == card
    assert "timestamp" not in captured["json"]
    assert "sign" not in captured["json"]
    await client.close()


@pytest.mark.asyncio
async def test_send_webhook_card_with_secret_signs_payload() -> None:
    captured: dict = {}
    client = _make_client(_ok_handler(captured))
    secret = "sec-demo"
    card = {"elements": [{"tag": "div", "content": "hello"}]}

    await client.send_webhook_card(WEBHOOK_URL, card, secret=secret)

    ts = captured["json"]["timestamp"]
    assert captured["json"]["sign"] == _gen_sign(ts, secret)
    assert captured["json"]["card"] == card
    await client.close()


@pytest.mark.asyncio
async def test_send_webhook_text_builds_text_body() -> None:
    captured: dict = {}
    client = _make_client(_ok_handler(captured))

    await client.send_webhook_text(WEBHOOK_URL, "新更新提醒", secret="s")

    assert captured["json"]["msg_type"] == "text"
    assert captured["json"]["content"] == {"text": "新更新提醒"}
    assert "timestamp" in captured["json"]
    await client.close()


@pytest.mark.asyncio
async def test_send_webhook_raises_on_nonzero_code() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"code": 9499, "msg": "Bad Request", "data": {}})

    client = _make_client(handler)
    with pytest.raises(Exception, match=r"code=9499.*Bad Request"):
        await client.send_webhook_card(WEBHOOK_URL, {})
    await client.close()


@pytest.mark.asyncio
async def test_send_webhook_raises_on_non_json_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(502, text="<html>Bad Gateway</html>")

    client = _make_client(handler)
    with pytest.raises(Exception, match=r"响应非 JSON"):
        await client.send_webhook_card(WEBHOOK_URL, {})
    await client.close()


@pytest.mark.asyncio
async def test_send_webhook_card_rejects_body_over_20kb() -> None:
    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover
        raise AssertionError("不应发出请求")

    client = _make_client(handler)
    big_content = "x" * (21 * 1024)
    with pytest.raises(Exception, match="20KB"):
        await client.send_webhook_card(WEBHOOK_URL, {"elements": [{"content": big_content}]})
    await client.close()
