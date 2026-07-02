"""电子表格快捷业务操作 mixin — 跨项目复用，不暴露为 MCP 工具"""

from __future__ import annotations

import asyncio
import csv
import os
from itertools import groupby
from typing import Any

from .base import _LarkMixinProtocol


class QuickSheetsMixin:
    """电子表格业务批量操作

    与 SheetsMixin 共享同一个 LarkClient 实例，通过 self.read_range、
    self.write_range、self.append_data、self.delete_dimension 等调用，
    MRO 会自动找到 SheetsMixin 中的方法。
    """

    async def quick_sheets_filter_columns(
        self: _LarkMixinProtocol,
        spreadsheet_token: str,
        sheet_id: str,
        keep_columns: list[str],
        *,
        data_start: int = 2,
    ) -> str:
        """只保留指定列，删除其余列（包括空白列），返回 sheetId"""
        header_row = data_start - 1
        col_count, end_col = await self._get_sheet_dimensions(spreadsheet_token, sheet_id)
        if col_count <= 0:
            return sheet_id
        rng = f"{sheet_id}!A{header_row}:{end_col}{header_row}"
        headers = await self.read_range(spreadsheet_token, rng)
        if not headers:
            return sheet_id
        raw_headers = headers[0]

        keep = set()
        for col in keep_columns:
            if col in raw_headers:
                keep.add(raw_headers.index(col))
        if not keep:
            return sheet_id

        drop = sorted(i for i in range(col_count) if i not in keep)
        if not drop:
            return sheet_id

        groups: list[tuple[int, int]] = []
        for _, g in groupby(enumerate(drop), lambda x: x[1] - x[0]):
            group_list = list(g)
            s = group_list[0][1] + 1
            e = group_list[-1][1] + 1
            groups.append((s, e))

        for s, e in reversed(groups):
            await self.delete_dimension(
                spreadsheet_token,
                sheet_id,
                major_dimension="COLUMNS",
                start_index=s,
                end_index=e,
            )

        return sheet_id

    async def quick_sheets_set_batch_index(
        self: _LarkMixinProtocol,
        spreadsheet_token: str,
        sheet_id: str,
        *,
        batch_column: str = "f_batch_index",
        batch_size: int = 10,
        data_start: int = 2,
    ) -> None:
        """按列设置批次索引，列不存在时自动创建"""
        col_letter = await self._ensure_column(
            spreadsheet_token, sheet_id, batch_column, data_start=data_start,
        )

        data = await self.read_range(spreadsheet_token, f"{sheet_id}!A:A")

        rows_to_write: list[tuple[int, int]] = []
        batch_num = 1
        row_count = 0
        for i in range(data_start - 1, len(data)):
            val = str(data[i][0]) if i < len(data) and data[i] else ""
            if val.strip():
                rows_to_write.append((i + 1, batch_num))
                row_count += 1
                if row_count >= batch_size:
                    batch_num += 1
                    row_count = 0

        if not rows_to_write:
            return

        value_ranges: list[dict[str, Any]] = []
        for batch_val, group in groupby(rows_to_write, key=lambda x: x[1]):
            group_list = list(group)
            rng = f"{sheet_id}!{col_letter}{group_list[0][0]}:{col_letter}{group_list[-1][0]}"
            vals = [[str(batch_val)] for _ in group_list]
            value_ranges.append({"range": rng, "values": vals})

        await self.write_multiple_range(
            spreadsheet_token,
            value_ranges,
        )

    async def quick_sheets_set_header_list(
        self: _LarkMixinProtocol,
        spreadsheet_token: str,
        sheet_id: str,
        header_list: list[str],
        *,
        keep_columns: int | None = None,
        data_start: int = 2,
    ) -> None:
        """从指定位置写入新表头，keep_columns 为 None 时从 A 列写入"""
        header_row = data_start - 1
        start_col = keep_columns if keep_columns is not None else 0
        start_letter = self._index_to_letter(start_col)
        end_letter = self._index_to_letter(start_col + len(header_list) - 1)
        range_str = f"{sheet_id}!{start_letter}{header_row}:{end_letter}{header_row}"
        await self.write_range(spreadsheet_token, range_str, [header_list])

    async def quick_sheets_get_last_value(
        self: _LarkMixinProtocol,
        spreadsheet_token: str,
        sheet_id: str,
        column_name: str,
        *,
        data_start: int = 2,
    ) -> dict[str, Any]:
        """获取指定列中最后一个非空值和其行号（跳过表头），返回 {value, row_number}"""
        col_letter = await self._resolve_column_letter(
            spreadsheet_token, sheet_id, column_name, data_start=data_start,
        )
        data = await self.read_range(spreadsheet_token, f"{sheet_id}!{col_letter}:{col_letter}")
        for i in range(len(data) - 1, data_start - 2, -1):
            row = data[i]
            if row and row[0] is not None and row[0] != "":
                return {"value": row[0], "row_number": i + 1}
        return {"value": None, "row_number": 0}

    async def quick_sheets_get_rows_by_batch(
        self: _LarkMixinProtocol,
        spreadsheet_token: str,
        sheet_id: str,
        batch_id: int,
        batch_size: int,
        *,
        data_start: int = 2,
    ) -> list[dict[str, Any]]:
        """按批次获取行数据，返回 [{header: value, row_number: int}]"""
        header_row = data_start - 1
        col_count, end_col = await self._get_sheet_dimensions(spreadsheet_token, sheet_id)
        if col_count <= 0:
            return []
        rng = f"{sheet_id}!A{header_row}:{end_col}{header_row}"
        headers_raw = await self.read_range(spreadsheet_token, rng)
        if not headers_raw:
            return []
        headers = headers_raw[0]

        start_row = data_start + (batch_id - 1) * batch_size
        end_row = start_row + batch_size - 1
        all_data = await self.read_range(
            spreadsheet_token, f"{sheet_id}!A{start_row}:{end_col}{end_row}"
        )

        result: list[dict[str, Any]] = []
        for row_offset, row in enumerate(all_data):
            row_dict: dict[str, Any] = {}
            for col_idx, header in enumerate(headers):
                val = row[col_idx] if col_idx < len(row) else ""
                row_dict[header] = val
            row_dict["row_number"] = start_row + row_offset
            result.append(row_dict)

        return result

    async def quick_sheets_batch_update(
        self: _LarkMixinProtocol,
        spreadsheet_token: str,
        sheet_id: str,
        update_data: list[dict[str, Any]],
        columns: list[str] | None = None,
        *,
        data_start: int = 2,
    ) -> None:
        """批量更新多行。columns 为 None 时从第一条数据自动推导列名"""
        if not update_data:
            return
        if columns is None:
            columns = [k for k in update_data[0] if k != "row_number"]

        header_row = data_start - 1
        _col_count, _end_col = await self._get_sheet_dimensions(spreadsheet_token, sheet_id)
        if _col_count <= 0:
            return
        headers = (await self.read_range(
            spreadsheet_token, f"{sheet_id}!A{header_row}:{_end_col}{header_row}"
        ))[0]
        col_indices = {h: i for i, h in enumerate(headers) if h is not None}

        value_ranges: list[dict[str, Any]] = []
        for row in update_data:
            row_number = row.get("row_number")
            if not row_number:
                continue
            try:
                row_number = int(row_number)
            except (ValueError, TypeError):
                continue

            cell_updates: list[tuple[str, Any]] = []
            for col_name in columns:
                if col_name not in col_indices or col_name not in row:
                    continue
                col_idx = col_indices[col_name]
                col_letter = self._index_to_letter(col_idx)
                cell_updates.append((col_letter, row[col_name]))

            if not cell_updates:
                continue

            start_letter = cell_updates[0][0]
            end_letter = cell_updates[-1][0]
            range_str = f"{sheet_id}!{start_letter}{row_number}:{end_letter}{row_number}"
            values = [[v for _, v in cell_updates]]
            value_ranges.append({"range": range_str, "values": values})

        if value_ranges:
            await self.write_multiple_range(spreadsheet_token, value_ranges)

    async def quick_sheets_clear_sheet(
        self: _LarkMixinProtocol,
        spreadsheet_token: str,
        sheet_id: str,
        *,
        keep_header: bool = True,
        data_start: int = 2,
    ) -> None:
        """清空工作表数据，默认保留首行表头"""
        meta = await self.get_metainfo(spreadsheet_token)
        row_count = 0
        for s in meta.get("sheets", []):
            if str(s.get("sheetId", "")) == sheet_id:
                row_count = s.get("rowCount", 0)
                break

        start = data_start if keep_header else 1
        if start > row_count:
            return

        chunk_size = 5000
        for end in range(row_count, start - 1, -chunk_size):
            chunk_start = max(start, end - chunk_size + 1)
            await self.delete_dimension(
                spreadsheet_token,
                sheet_id,
                major_dimension="ROWS",
                start_index=chunk_start,
                end_index=end,
            )

    async def quick_sheets_clear_sheet_content(
        self: _LarkMixinProtocol,
        spreadsheet_token: str,
        sheet_id: str,
        *,
        keep_header: bool = True,
        data_start: int = 2,
        before_column: str | None = None,
    ) -> dict[str, Any]:
        """清空工作表数据内容（不移除行），默认保留首行表头

        before_column 指定列字母（如 "F"），则只清空该列之前的所有列。
        返回 {"col_count": int, "row_count": int, "start_row": int}。
        """
        meta = await self.get_metainfo(spreadsheet_token)
        row_count = 0
        for s in meta.get("sheets", []):
            if str(s.get("sheetId", "")) == sheet_id:
                row_count = s.get("rowCount", 0)
                break

        start = data_start if keep_header else 1
        if start > row_count:
            return {"col_count": 0, "row_count": 0, "start_row": start}

        if before_column:
            upper = before_column.upper().strip()
            before_idx = 0
            for ch in upper:
                before_idx = before_idx * 26 + (ord(ch) - ord("A") + 1)
            if before_idx <= 1:
                return {"col_count": 0, "row_count": 0, "start_row": start}
            clear_count = before_idx - 1  # 清空该列之前的所有列
            end_col = self._index_to_letter(clear_count - 1)
            empty_row = [""] * clear_count
        else:
            meta2 = await self.get_metainfo(spreadsheet_token)
            col_count = 0
            for s in meta2.get("sheets", []):
                if str(s.get("sheetId", "")) == sheet_id:
                    col_count = s.get("columnCount", 0)
                    break
            if col_count <= 0:
                return {"col_count": 0, "row_count": 0, "start_row": start}
            end_col = self._index_to_letter(col_count - 1)
            empty_row = [""] * col_count

        chunk_size = 5000
        for batch_start in range(start, row_count + 1, chunk_size):
            batch_end = min(batch_start + chunk_size - 1, row_count)
            values = [empty_row] * (batch_end - batch_start + 1)
            range_str = f"{sheet_id}!A{batch_start}:{end_col}{batch_end}"
            await self.write_range(spreadsheet_token, range_str, values)

        return {"col_count": len(empty_row), "row_count": row_count - start + 1, "start_row": start}

    async def quick_sheets_sync_from_file(
        self: _LarkMixinProtocol,
        spreadsheet_token: str,
        sheet_id: str,
        file_path: str,
        *,
        batch_size: int = 500,
        batch_interval: int = 2,
        data_start: int = 2,
    ) -> None:
        """从本地 CSV 文件同步数据到工作表

        CSV 第一行为表头，后续行为数据行。
        默认从 data_start 行开始覆盖写入（不清空已有行，仅覆写对应范围）。
        解析后委托 quick_sheets_batch_append 执行写入。
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        with open(file_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            if not fieldnames:
                raise ValueError("CSV 文件缺少表头")
            # list[dict]，key 顺序 = CSV 表头列顺序，传给 quick_sheets_batch_append
            rows = list(reader)

        if not rows:
            raise ValueError("CSV 文件没有数据行")

        await self.quick_sheets_batch_append(
            spreadsheet_token,
            sheet_id,
            rows,
            batch_size=batch_size,
            batch_interval=batch_interval,
            data_start=data_start,
            overwrite_start=True
        )

    async def quick_sheets_batch_append(
        self: _LarkMixinProtocol,
        spreadsheet_token: str,
        sheet_id: str,
        data: list[dict[str, Any]],
        *,
        batch_size: int = 500,
        batch_interval: int = 2,
        data_start: int = 2,
        overwrite_start: int | bool | None = None,
    ) -> None:
        """批量追加行到工作表，自动分片并带间隔

        overwrite_start 为 True 时从 data_start 开始覆写，
        为 int 时从该行开始覆写，为 None 则使用 append 自动寻址。
        """
        if not data:
            return
        headers = list(data[0].keys()) if isinstance(data[0], dict) else []
        values: list[list[str]] = [[str(row.get(h, "")) for h in headers] for row in data]

        if overwrite_start is not None:
            # 从指定行覆盖写入，不用 append_data
            start_row = data_start if overwrite_start is True else overwrite_start  # type: ignore[comparison-overlap]
            col_count = len(headers)
            end_col = self._index_to_letter(col_count - 1)
            for i in range(0, len(values), batch_size):
                chunk = values[i : i + batch_size]
                row_start = start_row + i
                row_end = row_start + len(chunk) - 1
                range_str = f"{sheet_id}!A{row_start}:{end_col}{row_end}"
                await self.write_range(spreadsheet_token, range_str, chunk)
                if i + batch_size < len(values) and batch_interval > 0:
                    await asyncio.sleep(batch_interval)
        else:
            for i in range(0, len(values), batch_size):
                chunk = values[i : i + batch_size]
                await self.append_data(spreadsheet_token, sheet_id, chunk, data_start=data_start)
                if i + batch_size < len(values) and batch_interval > 0:
                    await asyncio.sleep(batch_interval)
