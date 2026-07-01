"""电子表格域 mixin — 飞书 Sheets 工作表与数据操作"""

from __future__ import annotations

from typing import Any

from .base import _LarkMixinProtocol


class SheetsMixin:
    """电子表格域方法（混入 _LarkBase 子类使用）"""

    async def get_metainfo(self: _LarkMixinProtocol, spreadsheet_token: str) -> dict[str, Any]:
        """获取表格元信息（含工作表列表）

        文档: https://open.feishu.cn/document/server-docs/historic-version/docs/sheets/obtain-spreadsheet-metadata
        """
        return await self._get(
            f"/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/metainfo",
            params={"ext_fields": "protectedRange"},
        )

    async def add_sheet(self: _LarkMixinProtocol, spreadsheet_token: str, title: str) -> str:
        """添加工作表，返回新 sheetId

        文档: https://open.feishu.cn/document/server-docs/docs/sheets-v3/spreadsheet-sheet/operate-sheets
        """
        data = await self._post(
            f"/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/sheets_batch_update",
            json_data={"requests": [{"addSheet": {"properties": {"title": title}}}]},
        )
        replies = data.get("replies", [])
        if not replies:
            raise Exception(f"创建工作表 {title} 失败：无返回")
        sheet_id = replies[0].get("addSheet", {}).get("properties", {}).get("sheetId")
        if not sheet_id:
            raise Exception(f"创建工作表 {title} 失败：缺少 sheetId")
        return str(sheet_id)

    async def delete_sheet(self: _LarkMixinProtocol, spreadsheet_token: str, sheet_id: str) -> None:
        """删除工作表"""
        await self._post(
            f"/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/sheets_batch_update",
            json_data={"requests": [{"deleteSheet": {"sheetId": sheet_id}}]},
        )

    async def copy_sheet(
        self: _LarkMixinProtocol, spreadsheet_token: str, source_sheet_id: str, title: str
    ) -> str:
        """复制工作表，返回新 sheetId"""
        data = await self._post(
            f"/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/sheets_batch_update",
            json_data={
                "requests": [
                    {
                        "copySheet": {
                            "source": {"sheetId": source_sheet_id},
                            "destination": {"title": title},
                        }
                    }
                ]
            },
        )
        replies = data.get("replies", [])
        if not replies:
            raise Exception(f"复制工作表 {title} 失败：无返回")
        sheet_id = replies[0].get("copySheet", {}).get("properties", {}).get("sheetId")
        if not sheet_id:
            raise Exception(f"复制工作表 {title} 失败：缺少 sheetId")
        return str(sheet_id)

    async def read_range(
        self: _LarkMixinProtocol, spreadsheet_token: str, range_str: str
    ) -> list[list[Any]]:
        """读取单个范围数据，返回二维数组

        文档: https://open.feishu.cn/document/server-docs/docs/sheets-v3/data-operation/reading-a-single-range
        """
        data = await self._get(
            f"/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values/{range_str}",
        )
        return data.get("valueRange", {}).get("values", [])  # type: ignore[no-any-return]

    async def write_range(
        self: _LarkMixinProtocol,
        spreadsheet_token: str,
        range_str: str,
        values: list[list[Any]],
    ) -> dict[str, Any]:
        """向单个范围写入数据（≤5000 行、100 列）

        文档: https://open.feishu.cn/document/server-docs/docs/sheets-v3/data-operation/write-data-to-a-single-range
        """
        return await self._put(
            f"/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values",
            json_data={"valueRange": {"range": range_str, "values": values}},
        )

    async def write_multiple_range(
        self: _LarkMixinProtocol,
        spreadsheet_token: str,
        value_ranges: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """向电子表格某个工作表的多个指定范围中写入数据。若指定范围已内有数据，将被新写入的数据覆盖。

        文档: https://open.feishu.cn/document/server-docs/docs/sheets-v3/data-operation/write-data-to-multiple-ranges

        使用限制:
            单次写入数据不得超过 5000 行、100列。
            每个单元格不超过 50,000 字符，推荐不超过 40,000 字符。
        """
        return await self._request(
            "POST",
            f"/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values_batch_update",
            json_data={"valueRanges": value_ranges},
        )

    async def append_data(
        self: _LarkMixinProtocol,
        spreadsheet_token: str,
        sheet_id: str,
        values: list[list[Any]],
        *,
        data_start: int = 2,
    ) -> None:
        """追加数据到工作表（自动找空白位置写入）

        文档: https://open.feishu.cn/document/server-docs/docs/sheets-v3/data-operation/append-data
        """
        col_count = len(values[0]) if values else 1
        end_col = self._index_to_letter(col_count - 1)
        await self._request(
            "POST",
            f"/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values_append",
            params={"insertDataOption": "OVERWRITE"},
            json_data={
                "valueRange": {
                    "range": f"{sheet_id}!A{data_start}:{end_col}",
                    "values": values,
                }
            },
        )

    async def delete_dimension(
        self: _LarkMixinProtocol,
        spreadsheet_token: str,
        sheet_id: str,
        *,
        major_dimension: str = "COLUMNS",
        start_index: int,
        end_index: int,
    ) -> None:
        """删除行/列（1-based 含首尾，单次最多 5000 行/列）

        文档: https://open.feishu.cn/document/server-docs/docs/sheets-v3/sheet-rowcol/-delete-rows-or-columns
        """
        await self._request(
            "DELETE",
            f"/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/dimension_range",
            json_data={
                "dimension": {
                    "sheetId": sheet_id,
                    "majorDimension": major_dimension,
                    "startIndex": start_index,
                    "endIndex": end_index,
                },
            },
        )

    # ── 工作表查找 ──

    async def find_sheet_ids(
        self: _LarkMixinProtocol, spreadsheet_token: str, *titles: str
    ) -> dict[str, str]:
        """一次查询获取多个 sheetId，返回 {title: sheetId}"""
        meta = await self.get_metainfo(spreadsheet_token)
        result = {t: "" for t in titles}
        for s in meta.get("sheets", []):
            t = s.get("title", "")
            if t in result:
                result[t] = str(s.get("sheetId", ""))
        return result

    async def find_sheet_id(self: _LarkMixinProtocol, spreadsheet_token: str, title: str) -> str:
        """查找工作表 ID，未找到返回空字符串"""
        try:
            return await self.get_sheet_id(spreadsheet_token, title)
        except Exception:
            return ""

    async def get_sheet_id(
        self: _LarkMixinProtocol, spreadsheet_token: str, sheet_title: str
    ) -> str:
        """根据工作表标题获取 sheetId，未找到抛异常"""
        metainfo = await self.get_metainfo(spreadsheet_token)
        for s in metainfo.get("sheets", []):
            if s.get("title") == sheet_title:
                return str(s.get("sheetId", ""))
        raise Exception(f"未找到工作表 '{sheet_title}'")

    # ── 辅助方法 ──

    async def _get_sheet_dimensions(
        self: _LarkMixinProtocol, spreadsheet_token: str, sheet_id: str
    ) -> tuple[int, str]:
        """获取工作表实际列数和末尾列字母，返回 (col_count, end_col)"""
        meta = await self.get_metainfo(spreadsheet_token)
        for s in meta.get("sheets", []):
            if str(s.get("sheetId", "")) == sheet_id:
                col_count = s.get("columnCount", 0)
                if col_count > 0:
                    return col_count, self._index_to_letter(col_count - 1)
        return 0, ""

    async def _ensure_column(
        self: _LarkMixinProtocol,
        spreadsheet_token: str,
        sheet_id: str,
        column_name: str,
        *,
        data_start: int = 2,
    ) -> str:
        """确保列存在，不存在则在表头末尾自动创建，返回列字母"""
        header_row = data_start - 1
        try:
            return await self._resolve_column_letter(
                spreadsheet_token, sheet_id, column_name, data_start=data_start,
            )
        except Exception:
            col_count, end_col = await self._get_sheet_dimensions(
                spreadsheet_token, sheet_id
            )
            if col_count > 0:
                headers = await self.read_range(
                    spreadsheet_token, f"{sheet_id}!A{header_row}:{end_col}{header_row}"
                )
                existing = headers[0] if headers else []
                while existing and existing[-1] in (None, ""):
                    existing.pop()
                col_letter = self._index_to_letter(len(existing))
            else:
                col_letter = self._index_to_letter(0)
            await self.write_range(
                spreadsheet_token,
                f"{sheet_id}!{col_letter}{header_row}:{col_letter}{header_row}",
                [[column_name]],
            )
            return col_letter


    async def _resolve_column_letter(
        self: _LarkMixinProtocol,
        spreadsheet_token: str,
        sheet_id: str,
        column_name: str,
        *,
        data_start: int = 2,
    ) -> str:
        """根据列名在表头中的位置解析列字母"""
        header_row = data_start - 1
        col_count, end_col = await self._get_sheet_dimensions(spreadsheet_token, sheet_id)
        if col_count <= 0:
            raise Exception(f"无法获取工作表 {sheet_id} 的列数")
        rng = f"{sheet_id}!A{header_row}:{end_col}{header_row}"
        headers = await self.read_range(spreadsheet_token, rng)
        if not headers:
            raise Exception(f"无法读取表头：{sheet_id}")
        for i, h in enumerate(headers[0]):
            if h == column_name:
                return self._index_to_letter(i)
        raise Exception(f"在表头中未找到列 '{column_name}'")
