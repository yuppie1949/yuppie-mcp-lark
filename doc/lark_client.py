"""飞书 API 客户端 — 直调飞书 OpenAPI

替换 Flow YAML 中所有 FC 节点（bitable.*、sheets.*、quick.*）。
quick.* 为自定义操作，基于飞书 API 在 Python 端实现。
"""

from __future__ import annotations

import asyncio
import time
from typing import Optional
from agentrun.utils.log import logger

import httpx


class LarkClient:
    """飞书操作客户端，通过飞书 OpenAPI 直调"""

    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self._http: Optional[httpx.AsyncClient] = None
        self._tenant_token: str = ""
        self._token_expire_at: float = 0
        self._token_lock = asyncio.Lock()

    def _get_http(self) -> httpx.AsyncClient:
        if self._http is None:
            self._http = httpx.AsyncClient(timeout=120)
        return self._http

    async def _ensure_token(self) -> str:
        """确保 tenant_access_token 有效，必要时自动刷新"""
        if self._tenant_token and time.time() < self._token_expire_at - 60:
            return self._tenant_token
        async with self._token_lock:
            if self._tenant_token and time.time() < self._token_expire_at - 60:
                return self._tenant_token
            resp = await self._get_http().post(
                "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
                json={"app_id": self.app_id, "app_secret": self.app_secret},
            )
            data = resp.json()
            if data.get("code") != 0:
                raise Exception(f"获取 tenant_access_token 失败: {data.get('msg', '')}")
            self._tenant_token = data["tenant_access_token"]
            self._token_expire_at = time.time() + data.get("expire", 7200)
            return self._tenant_token

    async def _request(
        self, method: str, path: str, *,
        params: dict | None = None,
        json_data: dict | list | None = None,
    ) -> dict:
        """通用的飞书 API 请求（含限流重试）"""
        token = await self._ensure_token()
        max_retries = 3
        for attempt in range(max_retries):
            url = f"https://open.feishu.cn{path}"
            resp = await self._get_http().request(
                method, url,
                headers={"Authorization": f"Bearer {token}"},
                params=params,
                json=json_data,
            )
            data = resp.json()
            code = data.get("code", -1)
            if code == 90217:  # too many request
                import asyncio
                wait = 1.5 * (attempt + 1)
                await asyncio.sleep(wait)
                continue
            if code != 0:
                raise Exception(f"[{method} {path}] 失败(code={code}): {data.get('msg', '')}")
            return data.get("data", {})
        raise Exception(f"[{method} {path}] 重试 {max_retries} 次后仍失败: too many request")

    async def _get(self, path: str, *, params: dict | None = None) -> dict:
        return await self._request("GET", path, params=params)

    async def _post(self, path: str, *, json_data: dict | None = None) -> dict:
        return await self._request("POST", path, json_data=json_data)

    async def _put(self, path: str, *, json_data: dict | None = None) -> dict:
        return await self._request("PUT", path, json_data=json_data)

    # ── 消息操作 ──

    async def send_message(
        self, receive_id: str, msg_type: str, content: str,
        *, receive_id_type: str = "open_id",
    ) -> dict:
        """发送消息给单个用户

        文档: https://open.feishu.cn/document/server-docs/im/v1/message/create
        """
        return await self._request(
            "POST", "/open-apis/im/v1/messages",
            params={"receive_id_type": receive_id_type},
            json_data={
                "receive_id": receive_id,
                "msg_type": msg_type,
                "content": content,
            },
        )

    async def send_messages(
        self, receive_ids: list[str], msg_type: str, content: str,
        *, receive_id_type: str = "open_id",
    ) -> list[dict]:
        """批量发送消息，返回 [{receive_id, message_id}] 列表"""
        results = []
        for uid in receive_ids:
            try:
                data = await self.send_message(uid, msg_type, content, receive_id_type=receive_id_type)
                results.append({"receive_id": uid, "message_id": data.get("message_id", "")})
            except Exception as e:
                logger.warning("发送消息失败: uid=%s, %s", uid, e)
                results.append({"receive_id": uid, "message_id": "", "error": str(e)})
        logger.info(f"消息发送完成: 成功 %d, 失败 %d",
                     sum(1 for r in results if r.get("message_id")),
                     sum(1 for r in results if not r.get("message_id")))
        return results

    # ── Bitable 操作 ──

    async def search_records(
        self, app_token: str, table_id: str, *,
        view_id: str | None = None,
        field_names: list[str] | None = None,
        sort: dict | None = None,
        filter: dict | None = None,
        page_token: str | None = None,
        page_size: int | None = None,
        automatic_fields: bool | None = None,
        user_id_type: str | None = None,
    ) -> dict:
        """搜索多维表格记录

        返回 {"items": [...], "has_more": bool, "page_token": str, "total": int}
        支持飞书 Bitable Records Search API 全部参数：
        - view_id: 视图 ID
        - field_names: 指定返回字段名列表
        - sort: 排序规则，如 {"field_name": "xxx", "desc": true}
        - filter: 过滤条件
        - page_token / page_size: 分页
        - automatic_fields: 是否返回自动计算字段
        - user_id_type: 用户 ID 类型 (open_id / user_id / union_id)
        """
        params: dict = {}
        if user_id_type:
            params["user_id_type"] = user_id_type
        if page_token:
            params["page_token"] = page_token
        if page_size is not None:
            params["page_size"] = page_size

        body: dict = {}
        if view_id:
            body["view_id"] = view_id
        if field_names:
            body["field_names"] = field_names
        if sort:
            body["sort"] = sort
        if filter:
            body["filter"] = filter
        if automatic_fields is not None:
            body["automatic_fields"] = automatic_fields

        data = await self._request(
            "POST",
            f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/search",
            params=params or None,
            json_data=body,
        )
        return {
            "items": data.get("items", []),
            "has_more": data.get("has_more", False),
            "page_token": data.get("page_token", ""),
            "total": data.get("total", 0),
        }

    # ── 电子表格 - 工作表 ──
    async def get_metainfo(self, spreadsheet_token: str) -> dict:
        """获取表格元信息
        文档: https://open.feishu.cn/document/server-docs/historic-version/docs/sheets/obtain-spreadsheet-metadata
        """
        return await self._get(
            f"/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/metainfo",
            params={"ext_fields": "protectedRange"},
        )

    async def add_sheet(self, spreadsheet_token: str, title: str) -> str:
        """添加工作表，返回 sheetId
        文档: https://open.feishu.cn/document/server-docs/docs/sheets-v3/spreadsheet-sheet/operate-sheets
        """
        data = await self._post(
            f"/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/sheets_batch_update",
            json_data={"requests": [{"addSheet": {"properties": {"title": title}}}]},
        )
        replies = data.get("replies", [])
        if not replies:
            raise Exception(f"创建工作表 {title} 失败：无返回")
        sheet_id = (
            replies[0].get("addSheet", {}).get("properties", {}).get("sheetId")
        )
        if not sheet_id:
            raise Exception(f"创建工作表 {title} 失败：缺少 sheetId")
        return str(sheet_id)

    async def delete_sheet(self, spreadsheet_token: str, sheet_id: str) -> None:
        """删除工作表
        文档: https://open.feishu.cn/document/server-docs/docs/sheets-v3/spreadsheet-sheet/operate-sheets
        """
        await self._post(
            f"/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/sheets_batch_update",
            json_data={"requests": [{"deleteSheet": {"sheetId": sheet_id}}]},
        )

    async def copy_sheet(
        self, spreadsheet_token: str, source_sheet_id: str, title: str,
    ) -> str:
        """复制工作表，返回新 sheetId
        文档: https://open.feishu.cn/document/server-docs/docs/sheets-v3/spreadsheet-sheet/operate-sheets
        """
        data = await self._post(
            f"/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/sheets_batch_update",
            json_data={"requests": [{
                "copySheet": {
                    "source": {"sheetId": source_sheet_id},
                    "destination": {"title": title},
                },
            }]},
        )
        replies = data.get("replies", [])
        if not replies:
            raise Exception(f"复制工作表 {title} 失败：无返回")
        sheet_id = (
            replies[0].get("copySheet", {}).get("properties", {}).get("sheetId")
        )
        if not sheet_id:
            raise Exception(f"复制工作表 {title} 失败：缺少 sheetId")
        return str(sheet_id)


    # ── 电子表格 - 数据 ──

    async def read_range(self, spreadsheet_token: str, range_str: str) -> list[list]:
        """读取单个范围数据。
        文档: https://open.feishu.cn/document/server-docs/docs/sheets-v3/data-operation/reading-a-single-range
        使用限制：
            - 该接口返回数据的最大限制为 10 MB。
            - 该接口不支持获取跨表引用和数组公式的计算结果。
        """
        data = await self._get(
            f"/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values/{range_str}",
        )
        return data.get("valueRange", {}).get("values", [])

    async def write_range(
        self, spreadsheet_token: str, range_str: str, values: list[list],
    ) -> dict:
        """向单个范围写入数据
        文档: https://open.feishu.cn/document/server-docs/docs/sheets-v3/data-operation/write-data-to-a-single-range
        使用限制：
            - 单次写入数据不得超过 5000 行、100列。
            - 每个单元格不超过 50,000 字符，由于服务端会增加控制字符，因此推荐每个单元格不超过 40,000 字符。
        """
        return await self._put(
            f"/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values",
            json_data={"valueRange": {"range": range_str, "values": values}},
        )

    async def append_data(
        self, spreadsheet_token: str, sheet_id: str, values: list[list],
    ) -> None:
        """追加数据到工作表 — 使用飞书原生 values_append API，自动找空白位置写入

        文档: https://open.feishu.cn/document/server-docs/docs/sheets-v3/data-operation/append-data
        使用限制：
            - 单次不超过 5000 行、100 列，每个单元格不超过 40000 字符
            - API 频率限制：100 次/秒
        """
        col_count = len(values[0]) if values else 1
        end_col = self._index_to_letter(col_count - 1)
        await self._request(
            "POST",
            f"/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values_append",
            params={"insertDataOption": "OVERWRITE"},
            json_data={
                "valueRange": {
                    "range": f"{sheet_id}!A1:{end_col}",
                    "values": values,
                }
            },
        )

    # ── 电子表格 - 行列 ──

    async def delete_dimension(
        self, spreadsheet_token: str, sheet_id: str, *,
        major_dimension: str = "COLUMNS",
        start_index: int, end_index: int,
    ) -> None:
        """删除行列（1-based 含首尾）
        文档: https://open.feishu.cn/document/server-docs/docs/sheets-v3/sheet-rowcol/-delete-rows-or-columns
        使用限制：
            - 单次调用该接口，最多支持删除 5000 行或列。
            - 一个工作表最少需有一行一列。你无法删除所有行或列。
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


    # ── Quick 自定义操作 ──

    async def find_sheet_ids(
        self, spreadsheet_token: str, *titles: str,
    ) -> dict[str, str]:
        """一次查询获取多个 sheetId，返回 {title: sheetId}"""
        meta = await self.get_metainfo(spreadsheet_token)
        result = {t: "" for t in titles}
        for s in meta.get("sheets", []):
            t = s.get("title", "")
            if t in result:
                result[t] = str(s.get("sheetId", ""))
        return result

    async def find_sheet_id(self, spreadsheet_token: str, title: str) -> str:
        """查找工作表 ID，未找到返回空字符串"""
        try:
            return await self.get_sheet_id(spreadsheet_token, title)
        except Exception:
            return ""

    async def get_sheet_id(self, spreadsheet_token: str, sheet_title: str) -> str:
        """根据工作表标题获取 sheetId（字符串标识符）"""
        metainfo = await self.get_metainfo(spreadsheet_token)
        for s in metainfo.get("sheets", []):
            if s.get("title") == sheet_title:
                return str(s.get("sheetId", ""))
        raise Exception(f"未找到工作表 '{sheet_title}'")

    async def filter_sheet_columns(
        self, spreadsheet_token: str, sheet_id: str,
        keep_columns: list[str],
    ) -> str:
        """只保留指定列，删除其余列（包括空白列）

        返回 sheetId（不变）。
        """
        headers = (await self.read_range(
            spreadsheet_token, f"{sheet_id}!A1:ZZZ1",
        ))
        if not headers:
            return sheet_id
        raw_headers = headers[0]

        # 确定要保留的列索引（0-based）
        keep = set()
        for col in keep_columns:
            if col in raw_headers:
                keep.add(raw_headers.index(col))
        if not keep:
            return sheet_id

        # 找到最后一个非空表头的索引，确保 trailing 空白列也被纳入删除范围
        # ZZZ1 读取范围是 18278 列，只处理到实际有数据的列
        # 实际列数通过 metainfo 获取
        meta = await self.get_metainfo(spreadsheet_token)
        sheet_col_count = 0
        for s in meta.get("sheets", []):
            if str(s.get("sheetId", "")) == sheet_id:
                sheet_col_count = s.get("columnCount", 0)
                break
        # 删除范围：从 0 到 sheet_col_count-1 中不在 keep 的列
        drop = sorted(i for i in range(sheet_col_count) if i not in keep)
        if not drop:
            return sheet_id

        logger.info("filter_sheet_columns: keep=%s, sheet_cols=%d, drop_count=%d",
                     keep, sheet_col_count, len(drop))

        # 合并连续区间，从后往前删（飞书 API: 1-based 左闭右闭）
        from itertools import groupby
        groups = []
        for _, g in groupby(enumerate(drop), lambda x: x[1] - x[0]):
            group = list(g)
            s = group[0][1] + 1  # 转 1-based
            e = group[-1][1] + 1
            groups.append((s, e))
        logger.info("filter_sheet_columns: 删除区间(1-based 左闭右闭): %s", groups)
        for s, e in reversed(groups):
            await self.delete_dimension(
                spreadsheet_token, sheet_id,
                major_dimension="COLUMNS",
                start_index=s, end_index=e,
            )

        return sheet_id

    async def set_column_batch_index(
        self, spreadsheet_token: str, sheet_id: str, *,
        batch_column: str = "f_batch_index",
        batch_size: int = 10,
    ) -> None:
        """按列设置批次索引 — 基于 sheets API 实现"""
        # 解析批次列字母
        col_letter = await self._resolve_column_letter(
            spreadsheet_token, sheet_id, batch_column,
        )
        # 读取 SKU 列数据（A 列假设是 SKU/Variant SKU，数据从行2开始）
        data = await self.read_range(spreadsheet_token, f"{sheet_id}!A:A")
        # 计算需要写入的行
        rows_to_write = []
        batch_num = 1
        row_count = 0
        for i in range(1, len(data)):  # 从行2开始（跳过表头）
            sku = data[i][0] if i < len(data) and data[i] else ""
            if sku and sku.strip():
                rows_to_write.append((i + 1, batch_num))
                row_count += 1
                if row_count >= batch_size:
                    batch_num += 1
                    row_count = 0

        if not rows_to_write:
            return

        # 按批次号分组批量写入
        from itertools import groupby
        for batch_val, group in groupby(rows_to_write, key=lambda x: x[1]):
            group_list = list(group)
            write_range_str = f"{sheet_id}!{col_letter}{group_list[0][0]}:{col_letter}{group_list[-1][0]}"
            values = [[str(batch_val)] for _ in group_list]
            await self.write_range(spreadsheet_token, write_range_str, values)


    async def set_header_list(
        self, spreadsheet_token: str, sheet_id: str,
        header_list: list[str], *,
        keep_columns: int | None = None,
    ) -> None:
        """设置 AI 分析表头，从 keep_columns 指定位置开始写入

        Args:
            keep_columns: 保留的原始列数，新表头从该位置后开始写入。为 None 时从 A 列写入
        """
        start_col = keep_columns if keep_columns is not None else 0
        start_letter = self._index_to_letter(start_col)
        end_letter = self._index_to_letter(start_col + len(header_list) - 1)
        range_str = f"{sheet_id}!{start_letter}1:{end_letter}1"
        await self.write_range(spreadsheet_token, range_str, [header_list])

    async def get_last_value(
        self, spreadsheet_token: str, sheet_id: str, column_name: str,
    ) -> int:
        """获取列中最后一个数值（用于确定最大批次）"""
        col_letter = await self._resolve_column_letter(
            spreadsheet_token, sheet_id, column_name,
        )
        data = await self.read_range(spreadsheet_token, f"{sheet_id}!{col_letter}:{col_letter}")
        max_val = 0
        for row in data[1:]:  # 跳过表头
            if row and row[0]:
                try:
                    val = int(float(row[0]))
                    if val > max_val:
                        max_val = val
                except (ValueError, TypeError):
                    pass
        return max_val
    
    async def get_rows_by_batch(
        self, spreadsheet_token: str, sheet_id: str, 
        batch_id: int,
        batch_size: int
    ) -> list[dict]:
        """按批次获取行数据

        根据 batch_id 和 batch_size 计算行范围，只读取对应区间的数据。
        返回行 dict 列表，key 为表头列名，包含 row_number 字段。
        """
        headers_raw = await self.read_range(spreadsheet_token, f"{sheet_id}!A1:ZZZ1")
        if not headers_raw:
            return []
        headers = headers_raw[0]

        start_row = 2 + (batch_id - 1) * batch_size
        end_row = start_row + batch_size - 1
        all_data = await self.read_range(spreadsheet_token, f"{sheet_id}!A{start_row}:ZZZ{end_row}")

        result = []
        for row_offset, row in enumerate(all_data):
            row_dict = {}
            for col_idx, header in enumerate(headers):
                val = row[col_idx] if col_idx < len(row) else ""
                row_dict[header] = val
            row_dict["row_number"] = start_row + row_offset
            result.append(row_dict)

        return result

    async def batch_update_by_batch(
        self, spreadsheet_token: str, sheet_id: str,
        update_data: list[dict], columns: list[str],
    ) -> None:
        """批量更新多行 — 用 values_batch_update 一次请求更新所有行"""
        if not update_data:
            return

        headers = (await self.read_range(spreadsheet_token, f"{sheet_id}!A1:ZZZ1"))[0]
        col_indices = {}
        for i, h in enumerate(headers):
            col_indices[h] = i

        value_ranges = []
        for row in update_data:
            row_number = row.get("row_number")
            if not row_number:
                continue
            try:
                row_number = int(row_number)
            except (ValueError, TypeError):
                continue

            cell_updates = []
            for col_name in columns:
                if col_name not in col_indices:
                    continue
                col_idx = col_indices[col_name]
                col_letter = self._index_to_letter(col_idx)
                value = row.get(col_name, "")
                cell_updates.append((col_letter, value))

            if not cell_updates:
                continue

            start_letter = cell_updates[0][0]
            end_letter = cell_updates[-1][0]
            range_str = f"{sheet_id}!{start_letter}{row_number}:{end_letter}{row_number}"
            values = [[v for _, v in cell_updates]]
            value_ranges.append({"range": range_str, "values": values})

        if value_ranges:
            await self._post(
                f"/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values_batch_update",
                json_data={"valueRanges": value_ranges},
            )

    async def batch_append(
        self, spreadsheet_token: str, sheet_id: str,
        data: list[dict], *,
        batch_size: int = 500,
        batch_interval: int = 2,
    ) -> None:
        """批量追加行到工作表 — 基于 sheets.appendData"""
        # 将 dict 列表转为二维数组
        headers = list(data[0].keys()) if isinstance(data[0], dict) else []
        values = []
        for row in data:
            values.append([str(row.get(h, "")) for h in headers])

        # 分批次追加
        for i in range(0, len(values), batch_size):
            chunk = values[i:i + batch_size]
            await self.append_data(spreadsheet_token, sheet_id, chunk)
            if i + batch_size < len(values) and batch_interval > 0:
                await asyncio.sleep(batch_interval)


    # ── Common Method ──
    @staticmethod
    def _index_to_letter(index: int) -> str:
        """将 0-based 列索引转换为列字母（A, B, ..., Z, AA, AB, ...）"""
        result = ""
        while True:
            result = chr(ord("A") + index % 26) + result
            index = index // 26 - 1
            if index < 0:
                break
        return result

    async def _resolve_column_letter(
        self, spreadsheet_token: str, sheet_id: str, column_name: str,
    ) -> str:
        """根据列名在表头中的位置解析列字母"""
        headers = (await self.read_range(spreadsheet_token, f"{sheet_id}!A1:ZZZ1"))
        if not headers:
            raise Exception(f"无法读取表头：{sheet_id}")
        for i, h in enumerate(headers[0]):
            if h == column_name:
                return self._index_to_letter(i)
        raise Exception(f"在表头中未找到列 '{column_name}'")


    async def close(self):
        if self._http:
            await self._http.aclose()
            self._http = None
