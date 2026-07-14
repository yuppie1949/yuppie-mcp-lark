"""tools 层 BaseModel 输入校验测试"""

import pytest
from pydantic import ValidationError

from yuppie_mcp_lark.tools.bitable import (
    BatchCreateRecordsInput,
    BatchDeleteRecordsInput,
    BatchGetRecordsInput,
    BatchUpdateRecordsInput,
    CopyAppInput,
    CreateAppInput,
    CreateRecordInput,
    CreateTableInput,
    DeleteRecordInput,
    DeleteTableInput,
    SearchRecordsInput,
    UpdateRecordInput,
)
from yuppie_mcp_lark.tools.bitable_quick import BitableClearInput
from yuppie_mcp_lark.tools.drive import CopyFileInput, DeleteFileInput
from yuppie_mcp_lark.tools.messages import SendMessageInput
from yuppie_mcp_lark.tools.sheets import (
    AddSheetInput,
    AppendDataInput,
    CopySheetInput,
    CreateSpreadsheetInput,
    DeleteDimensionInput,
    DeleteSheetInput,
    GetMetainfoInput,
    ReadRangeInput,
    ReadRangesInput,
    StylesBatchUpdateInput,
    UpdateDimensionInput,
    WriteImageInput,
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


# ── 云文档域 ──

def test_copy_file_required() -> None:
    with pytest.raises(ValidationError):
        CopyFileInput()


def test_copy_file_with_all() -> None:
    args = CopyFileInput(
        file_token="bascnxxx", name="new.docx",
        folder_token="fldxxx", file_type="docx",
    )
    assert args.file_token == "bascnxxx"
    assert args.file_type == "docx"


def test_delete_file_required() -> None:
    with pytest.raises(ValidationError):
        DeleteFileInput()


def test_delete_file_with_all() -> None:
    args = DeleteFileInput(file_token="boxcnxxx", file_type="file")
    assert args.file_token == "boxcnxxx"
    assert args.file_type == "file"

# ── 多维表格域 ──

def test_search_records_required_fields() -> None:
    with pytest.raises(ValidationError):
        SearchRecordsInput()


def test_search_records_allows_only_required() -> None:
    args = SearchRecordsInput(app_token="bascn", table_id="tblxxx")
    assert args.view_id is None
    assert args.page_size is None


def test_create_record_required() -> None:
    with pytest.raises(ValidationError):
        CreateRecordInput()


def test_create_record_with_fields() -> None:
    args = CreateRecordInput(app_token="bascn", table_id="tblxxx", fields={"name": "test"})
    assert args.fields["name"] == "test"


def test_update_record_required() -> None:
    with pytest.raises(ValidationError):
        UpdateRecordInput()


def test_update_record_with_all() -> None:
    args = UpdateRecordInput(
        app_token="bascn", table_id="tblxxx", record_id="recxxx", fields={"name": "new"}
    )
    assert args.record_id == "recxxx"


def test_delete_record_required() -> None:
    with pytest.raises(ValidationError):
        DeleteRecordInput()


def test_batch_create_records_required() -> None:
    with pytest.raises(ValidationError):
        BatchCreateRecordsInput()


def test_batch_create_records_with_data() -> None:
    args = BatchCreateRecordsInput(
        app_token="bascn", table_id="tblxxx", records=[{"fields": {"name": "a"}}]
    )
    assert len(args.records) == 1


def test_batch_update_records_required() -> None:
    with pytest.raises(ValidationError):
        BatchUpdateRecordsInput()


def test_batch_get_records_required() -> None:
    with pytest.raises(ValidationError):
        BatchGetRecordsInput()


def test_batch_get_records_too_many() -> None:
    with pytest.raises(ValidationError):
        BatchGetRecordsInput(
            app_token="bascn",
            table_id="tblxxx",
            record_ids=[f"rec{i}" for i in range(101)],
        )


def test_batch_delete_records_required() -> None:
    with pytest.raises(ValidationError):
        BatchDeleteRecordsInput()


def test_create_app_required() -> None:
    with pytest.raises(ValidationError):
        CreateAppInput()


def test_create_app_optional_fields() -> None:
    args = CreateAppInput(name="test", folder_token="fldxxx", time_zone="Asia/Shanghai")
    assert args.folder_token == "fldxxx"
    assert args.time_zone == "Asia/Shanghai"


def test_copy_app_required() -> None:
    with pytest.raises(ValidationError):
        CopyAppInput()


def test_create_table_required() -> None:
    with pytest.raises(ValidationError):
        CreateTableInput()


def test_create_table_with_definition() -> None:
    args = CreateTableInput(
        app_token="bascn",
        table={"name": "新表", "fields": [{"field_name": "名称", "type": 1}]},
    )
    assert args.table["name"] == "新表"


def test_delete_table_required() -> None:
    with pytest.raises(ValidationError):
        DeleteTableInput()


# ── 多维表格快捷操作域 ──

def test_bitable_clear_required() -> None:
    with pytest.raises(ValidationError):
        BitableClearInput()


def test_bitable_clear_defaults() -> None:
    args = BitableClearInput(app_token="bascn", table_id="tblxxx")
    assert args.filter is None
    assert args.sort is None


def test_bitable_clear_with_options() -> None:
    args = BitableClearInput(
        app_token="bascn",
        table_id="tblxxx",
        filter={"conjunction": "and", "conditions": []},
        sort=[{"field_name": "id", "desc": True}],
    )
    assert args.filter is not None
    assert args.sort is not None



# ── 电子表格域 ──


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


def test_create_spreadsheet_required() -> None:
    with pytest.raises(ValidationError):
        CreateSpreadsheetInput()


def test_create_spreadsheet_with_folder() -> None:
    args = CreateSpreadsheetInput(title="test", folder_token="fldxxx")
    assert args.title == "test"
    assert args.folder_token == "fldxxx"


def test_read_range_required() -> None:
    with pytest.raises(ValidationError):
        ReadRangeInput()


def test_write_range_required() -> None:
    with pytest.raises(ValidationError):
        WriteRangeInput()


def test_write_image_required() -> None:
    with pytest.raises(ValidationError):
        WriteImageInput()


def test_write_image_with_all() -> None:
    args = WriteImageInput(
        spreadsheet_token="x",
        range="sheet1!A1:A1",
        image_base64="iVBORw0KGgo=",
        name="test.png",
    )
    assert args.range == "sheet1!A1:A1"
    assert args.name == "test.png"


def test_read_ranges_required() -> None:
    with pytest.raises(ValidationError):
        ReadRangesInput()


def test_read_ranges_with_defaults() -> None:
    args = ReadRangesInput(spreadsheet_token="x", ranges="sheet1!A1:B2")
    assert args.value_render_option is None
    assert args.date_time_render_option is None
    assert args.user_id_type is None


def test_read_ranges_with_options() -> None:
    args = ReadRangesInput(
        spreadsheet_token="x",
        ranges="sheet1!A1:B2,sheet2!C1:D3",
        value_render_option="FormattedValue",
        date_time_render_option="FormattedString",
        user_id_type="open_id",
    )
    assert args.value_render_option == "FormattedValue"
    assert args.date_time_render_option == "FormattedString"
    assert args.user_id_type == "open_id"


def test_update_dimension_required() -> None:
    with pytest.raises(ValidationError):
        UpdateDimensionInput()


def test_update_dimension_defaults() -> None:
    args = UpdateDimensionInput(
        spreadsheet_token="x", sheet_id="y", start_index=2, end_index=100
    )
    assert args.major_dimension == "ROWS"
    assert args.fixed_size is None
    assert args.visible is None


def test_update_dimension_full() -> None:
    args = UpdateDimensionInput(
        spreadsheet_token="x", sheet_id="y", start_index=1, end_index=50,
        major_dimension="COLUMNS", fixed_size=200, visible=False,
    )
    assert args.major_dimension == "COLUMNS"
    assert args.fixed_size == 200
    assert args.visible is False


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

from yuppie_mcp_lark.tools.sheets_quick import ClearSheetContentInput, QuickWriteImageInput, SetColumnStyleInput, SetRowHeightInput


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


def test_quick_write_image_required() -> None:
    with pytest.raises(ValidationError):
        QuickWriteImageInput()


def test_quick_write_image_with_all() -> None:
    args = QuickWriteImageInput(
        spreadsheet_token="x",
        range="sheet1!A1:A1",
        image_source="https://example.com/img.png",
        name="test.png",
    )
    assert args.image_source == "https://example.com/img.png"
    assert args.name == "test.png"


def test_quick_write_image_name_auto() -> None:
    args = QuickWriteImageInput(
        spreadsheet_token="x",
        range="sheet1!A1:A1",
        image_source="/path/to/photo.jpg",
    )
    assert args.name is None
    args = ClearSheetContentInput(
        spreadsheet_token="x",
        sheet_id="y",
        before_column="F",
    )
    assert args.before_column == "F"


def test_set_row_height_required() -> None:
    with pytest.raises(ValidationError):
        SetRowHeightInput()


def test_set_row_height_defaults() -> None:
    args = SetRowHeightInput(
        spreadsheet_token="x", sheet_id="y", height=50
    )
    assert args.start_row == 2
    assert args.end_row is None


def test_set_row_height_full() -> None:
    args = SetRowHeightInput(
        spreadsheet_token="x", sheet_id="y", height=40,
        start_row=1, end_row=100,
    )
    assert args.height == 40
    assert args.start_row == 1
    assert args.end_row == 100


def test_styles_batch_update_required() -> None:
    with pytest.raises(ValidationError):
        StylesBatchUpdateInput()


def test_styles_batch_update_with_data() -> None:
    args = StylesBatchUpdateInput(
        spreadsheet_token="x",
        data=[{"ranges": ["sheet1!A1:B2"], "style": {"font": {"bold": True}}}],
    )
    assert len(args.data) == 1


def test_set_column_style_required() -> None:
    with pytest.raises(ValidationError):
        SetColumnStyleInput()


def test_set_column_style_defaults() -> None:
    args = SetColumnStyleInput(
        spreadsheet_token="x", sheet_id="y",
        style={"font": {"bold": True}},
    )
    assert args.start_row == 2
    assert args.columns is None


def test_set_column_style_with_columns() -> None:
    args = SetColumnStyleInput(
        spreadsheet_token="x", sheet_id="y",
        style={"backColor": "#ff0000"},
        columns=["A", "C"],
        start_row=1,
    )
    assert args.columns == ["A", "C"]
    assert args.start_row == 1
