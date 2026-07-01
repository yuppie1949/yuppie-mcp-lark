"""tools 层 BaseModel 输入校验测试"""

import pytest
from pydantic import ValidationError

from yuppie_mcp_lark.tools.bitable import SearchRecordsInput
from yuppie_mcp_lark.tools.messages import SendMessageInput
from yuppie_mcp_lark.tools.sheets import (
    AddSheetInput,
    AppendDataInput,
    CopySheetInput,
    DeleteDimensionInput,
    DeleteSheetInput,
    GetMetainfoInput,
    ReadRangeInput,
    WriteRangeInput,
)


# ── 消息域 ──

def test_send_message_required_fields() -> None:
    with pytest.raises(ValidationError):
        SendMessageInput()  # 缺 receive_id 和 content


def test_send_message_defaults() -> None:
    args = SendMessageInput(receive_id="ou_xxx", content='{"text":"hi"}')
    assert args.msg_type == "text"
    assert args.receive_id_type == "open_id"


def test_send_message_strips_whitespace() -> None:
    args = SendMessageInput(receive_id="  ou_xxx  ", content='{"text":"hi"}')
    assert args.receive_id == "ou_xxx"


def test_send_message_rejects_invalid_msg_type() -> None:
    with pytest.raises(ValidationError):
        SendMessageInput(receive_id="ou_xxx", content="{}", msg_type="invalid_type")


def test_send_message_accepts_uuid() -> None:
    args = SendMessageInput(
        receive_id="ou_xxx", content='{"text":"hi"}', uuid="a0d69e20-1dd1-458b-k525-dfeca4015204"
    )
    assert args.uuid == "a0d69e20-1dd1-458b-k525-dfeca4015204"


def test_send_message_forbids_extra() -> None:
    with pytest.raises(ValidationError):
        SendMessageInput(
            receive_id="ou_xxx", content="{}", extra_field="bad"
        )


# ── 多维表格域 ──

def test_search_records_required_fields() -> None:
    with pytest.raises(ValidationError):
        SearchRecordsInput()


def test_search_records_allows_only_required() -> None:
    args = SearchRecordsInput(app_token="bascn", table_id="tblxxx")
    assert args.view_id is None
    assert args.page_size is None


# ── 电子表格域 ──

def test_get_metainfo_required() -> None:
    with pytest.raises(ValidationError):
        GetMetainfoInput()


def test_add_sheet_required() -> None:
    with pytest.raises(ValidationError):
        AddSheetInput()


def test_delete_sheet_required() -> None:
    with pytest.raises(ValidationError):
        DeleteSheetInput()


def test_copy_sheet_required() -> None:
    with pytest.raises(ValidationError):
        CopySheetInput()


def test_read_range_required() -> None:
    with pytest.raises(ValidationError):
        ReadRangeInput()


def test_write_range_required() -> None:
    with pytest.raises(ValidationError):
        WriteRangeInput()


def test_append_data_required() -> None:
    with pytest.raises(ValidationError):
        AppendDataInput()


def test_delete_dimension_defaults_and_required() -> None:
    with pytest.raises(ValidationError):
        DeleteDimensionInput(spreadsheet_token="x", sheet_id="y")
    args = DeleteDimensionInput(
        spreadsheet_token="x",
        sheet_id="y",
        start_index=1,
        end_index=3,
    )
    assert args.major_dimension == "COLUMNS"


# ── 电子表格快捷操作域 ──

from yuppie_mcp_lark.tools.sheets_quick import ClearSheetContentInput


def test_clear_sheet_content_required() -> None:
    with pytest.raises(ValidationError):
        ClearSheetContentInput()


def test_clear_sheet_content_defaults() -> None:
    args = ClearSheetContentInput(spreadsheet_token="x", sheet_id="y")
    assert args.keep_header is True
    assert args.data_start == 2
    assert args.before_column is None


def test_clear_sheet_content_with_before_column() -> None:
    args = ClearSheetContentInput(
        spreadsheet_token="x",
        sheet_id="y",
        before_column="F",
    )
    assert args.before_column == "F"
