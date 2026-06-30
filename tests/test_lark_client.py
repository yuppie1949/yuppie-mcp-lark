"""LarkClient 底层客户端测试（仅测纯函数，不测网络调用）"""

import pytest

from yuppie_mcp_lark.utils.lark.base import _LarkBase


@pytest.mark.parametrize(
    "index,expected",
    [
        (0, "A"),
        (1, "B"),
        (25, "Z"),
        (26, "AA"),
        (27, "AB"),
        (51, "AZ"),
        (52, "BA"),
        (701, "ZZ"),
        (702, "AAA"),
    ],
)
def test_index_to_letter(index: int, expected: str) -> None:
    assert _LarkBase._index_to_letter(index) == expected


def test_base_init_strips_trailing_slash() -> None:
    base = _LarkBase("id", "secret", base_url="https://open.feishu.cn/")
    assert base.base_url == "https://open.feishu.cn"


def test_lark_client_aggregates_all_mixins() -> None:
    """LarkClient 实例应具备所有 mixin 方法"""
    from yuppie_mcp_lark.utils.lark import LarkClient

    client = LarkClient("id", "secret")
    # 消息域
    assert callable(getattr(client, "send_message", None))
    assert callable(getattr(client, "send_messages", None))
    # 多维表格域
    assert callable(getattr(client, "search_records", None))
    # 电子表格域
    assert callable(getattr(client, "get_metainfo", None))
    assert callable(getattr(client, "add_sheet", None))
    assert callable(getattr(client, "delete_sheet", None))
    assert callable(getattr(client, "copy_sheet", None))
    assert callable(getattr(client, "read_range", None))
    assert callable(getattr(client, "write_range", None))
    assert callable(getattr(client, "append_data", None))
    assert callable(getattr(client, "delete_dimension", None))
    # 基类方法
    assert callable(getattr(client, "close", None))


def test_lark_client_accepts_base_url() -> None:
    from yuppie_mcp_lark.utils.lark import LarkClient

    client = LarkClient("id", "secret", base_url="https://open.larksuite.com/")
    assert client.base_url == "https://open.larksuite.com"
