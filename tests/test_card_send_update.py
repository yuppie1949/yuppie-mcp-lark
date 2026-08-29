"""send_card / update_card 请求级测试（httpx.MockTransport 拦截，不联网）

验证：POST /im/v1/messages 发卡片（msg_type=interactive、content 为卡片 JSON）、
PATCH /im/v1/messages/{message_id} 原地更新（content + msg_type）。
"""

from collections.abc import Callable

import httpx
import pytest
from yuppie_lark import LarkClient

TOKEN_RESP = {
    "code": 0,
    "tenant_access_token": "t-test-token",
    "expire": 7200,
}

Handler = Callable[[httpx.Request], httpx.Response]


def _make_client(handler: Handler) -> LarkClient:
    client = LarkClient("app_id", "app_secret")
    client._http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return client


def _handler(request: httpx.Request) -> httpx.Response:
    import json

    if "tenant_access_token" in request.url.path:
        return httpx.Response(200, json=TOKEN_RESP)
    if request.url.path == "/open-apis/im/v1/messages":
        body = request.read().decode()
        assert request.method == "POST"
        assert request.url.params["receive_id_type"] == "chat_id"

        data = json.loads(body)
        assert data["msg_type"] == "interactive"
        card = json.loads(data["content"])
        assert card["header"]["title"]["content"] == "冒烟进度"
        return httpx.Response(
            200,
            json={"code": 0, "data": {"message_id": "om_mock123"}},
        )
    if "/open-apis/im/v1/messages/" in request.url.path:
        body = request.read().decode()
        assert request.method == "PATCH"
        data = json.loads(body)
        assert data["msg_type"] == "interactive"
        card = json.loads(data["content"])
        assert card["elements"][0]["text"]["content"] == "**更新后**"
        return httpx.Response(200, json={"code": 0, "data": {}})
    return httpx.Response(200, json={"code": 0, "data": {}})


@pytest.mark.asyncio
async def test_send_card_posts_interactive_with_card_json() -> None:
    client = _make_client(_handler)
    card = {
        "header": {"title": {"tag": "plain_text", "content": "冒烟进度"}, "template": "blue"},
        "elements": [{"tag": "div", "text": {"tag": "lark_md", "content": "**步骤 1**"}}],
    }
    data = await client.send_card("oc_chat123", card)
    assert data["message_id"] == "om_mock123"
    await client.close()


@pytest.mark.asyncio
async def test_send_card_uses_open_id_when_specified() -> None:
    calls: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if "tenant_access_token" in request.url.path:
            return httpx.Response(200, json=TOKEN_RESP)
        calls["receive_id_type"] = request.url.params.get("receive_id_type", "")
        return httpx.Response(
            200,
            json={"code": 0, "data": {"message_id": "om_x"}},
        )

    client = _make_client(handler)
    await client.send_card("ou_user123", {"elements": []}, receive_id_type="open_id")
    assert calls["receive_id_type"] == "open_id"
    await client.close()


@pytest.mark.asyncio
async def test_update_card_patches_message() -> None:
    client = _make_client(_handler)
    card = {
        "elements": [{"tag": "div", "text": {"tag": "lark_md", "content": "**更新后**"}}],
    }
    await client.update_card("om_x100", card)
    await client.close()


@pytest.mark.asyncio
async def test_update_message_defaults_to_interactive() -> None:
    observed: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if "tenant_access_token" in request.url.path:
            return httpx.Response(200, json=TOKEN_RESP)
        import json

        observed["method"] = request.method
        observed["url"] = str(request.url)
        observed["body"] = json.loads(request.read())
        return httpx.Response(200, json={"code": 0, "data": {}})

    client = _make_client(handler)
    await client.update_message("om_x200", '{"text":"hi"}')
    assert observed["method"] == "PATCH"
    assert observed["url"] == "https://open.feishu.cn/open-apis/im/v1/messages/om_x200"
    assert observed["body"] == {"content": '{"text":"hi"}', "msg_type": "interactive"}
    await client.close()
