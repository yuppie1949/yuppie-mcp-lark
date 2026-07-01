"""飞书 OpenAPI 客户端基类：HTTP 客户端、token 管理、通用请求"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Optional, Protocol

import httpx


class _LarkMixinProtocol(Protocol):
    """Mixin 自引用协议——避免 mypy 对 mixin self: _LarkBase 模式的报错"""

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = ...,
        json_data: dict[str, Any] | list[Any] | None = ...,
    ) -> dict[str, Any]: ...

    async def _get(self, path: str, *, params: dict[str, Any] | None = ...) -> dict[str, Any]: ...

    async def _post(
        self, path: str, *, json_data: dict[str, Any] | None = ...
    ) -> dict[str, Any]: ...

    async def _put(
        self, path: str, *, json_data: dict[str, Any] | None = ...
    ) -> dict[str, Any]: ...

    def _index_to_letter(self, index: int) -> str: ...

    async def send_message(
        self,
        receive_id: str,
        msg_type: str,
        content: str,
        *,
        receive_id_type: str = ...,
        uuid: str | None = ...,
    ) -> dict[str, Any]: ...

    # ── SheetsMixin ──
    async def get_metainfo(self, spreadsheet_token: str) -> dict[str, Any]: ...
    async def read_range(self, spreadsheet_token: str, range_str: str) -> list[list[Any]]: ...
    async def write_range(
        self, spreadsheet_token: str, range_str: str, values: list[list[Any]]
    ) -> dict[str, Any]: ...
    async def write_multiple_range(
        self, spreadsheet_token: str, value_ranges: list[dict[str, Any]]
    ) -> dict[str, Any]: ...
    async def append_data(
        self, spreadsheet_token: str, sheet_id: str, values: list[list[Any]],
        *, data_start: int = ...,
    ) -> None: ...
    async def delete_dimension(
        self,
        spreadsheet_token: str,
        sheet_id: str,
        *,
        major_dimension: str = ...,
        start_index: int,
        end_index: int,
    ) -> None: ...
    async def find_sheet_ids(self, spreadsheet_token: str, *titles: str) -> dict[str, str]: ...
    async def find_sheet_id(self, spreadsheet_token: str, title: str) -> str: ...
    async def get_sheet_id(self, spreadsheet_token: str, sheet_title: str) -> str: ...
    async def _resolve_column_letter(
        self, spreadsheet_token: str, sheet_id: str, column_name: str, *, data_start: int = ...
    ) -> str: ...
    async def _get_sheet_dimensions(
        self, spreadsheet_token: str, sheet_id: str
    ) -> tuple[int, str]: ...


    # ── QuickSheetsMixin ──
    async def quick_sheets_filter_columns(
        self, spreadsheet_token: str, sheet_id: str, keep_columns: list[str],
        *, data_start: int = ...,
    ) -> str: ...
    async def quick_sheets_set_batch_index(
        self,
        spreadsheet_token: str,
        sheet_id: str,
        *,
        batch_column: str = ...,
        batch_size: int = ...,
        data_start: int = ...,
    ) -> None: ...
    async def quick_sheets_set_header_list(
        self,
        spreadsheet_token: str,
        sheet_id: str,
        header_list: list[str],
        *,
        keep_columns: int | None = ...,
        data_start: int = ...,
    ) -> None: ...
    async def quick_sheets_get_last_value(
        self, spreadsheet_token: str, sheet_id: str, column_name: str, *, data_start: int = ...
    ) -> dict[str, Any]: ...
    async def quick_sheets_get_rows_by_batch(
        self, spreadsheet_token: str, sheet_id: str, batch_id: int, batch_size: int,
        *, data_start: int = ...,
    ) -> list[dict[str, Any]]: ...
    async def quick_sheets_batch_update(
        self,
        spreadsheet_token: str,
        sheet_id: str,
        update_data: list[dict[str, Any]],
        columns: list[str] | None = ...,
        *,
        data_start: int = ...,
    ) -> None: ...
    async def _ensure_column(
        self, spreadsheet_token: str, sheet_id: str, column_name: str, *, data_start: int = ...
    ) -> str: ...
    async def quick_sheets_batch_append(
        self,
        spreadsheet_token: str,
        sheet_id: str,
        data: list[dict[str, Any]],
        *,
        batch_size: int = ...,
        batch_interval: int = ...,
        data_start: int = ...,
    ) -> None: ...


_FEISHU_ERRORS: dict[int, str] = {
    90215: "指定的 sheet_id 不存在，请检查工作表 ID 是否正确",
    90227: "请求体过大，通常是被操作的工作表数据量超过限制，建议减少数据量重试",
}


class _LarkBase:
    """飞书客户端基类 — 管理 httpx client、tenant_access_token、通用请求与重试

    子类（通过 mixin）继承本类后，直接使用 self._get/_post/_put/_request 调飞书 API。
    """

    def __init__(
        self,
        app_id: str,
        app_secret: str,
        base_url: str = "https://open.feishu.cn",
    ) -> None:
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_url = base_url.rstrip("/")
        self._http: Optional[httpx.AsyncClient] = None
        self._tenant_token: str = ""
        self._token_expire_at: float = 0
        self._token_lock = asyncio.Lock()

    def _get_http(self) -> httpx.AsyncClient:
        if self._http is None:
            self._http = httpx.AsyncClient(timeout=120)
        return self._http

    async def _ensure_token(self) -> str:
        """确保 tenant_access_token 有效，必要时自动刷新（带并发锁）"""
        if self._tenant_token and time.time() < self._token_expire_at - 60:
            return self._tenant_token
        async with self._token_lock:
            if self._tenant_token and time.time() < self._token_expire_at - 60:
                return self._tenant_token
            resp = await self._get_http().post(
                f"{self.base_url}/open-apis/auth/v3/tenant_access_token/internal",
                json={"app_id": self.app_id, "app_secret": self.app_secret},
            )
            data = resp.json()
            if data.get("code") != 0:
                raise Exception(f"获取 tenant_access_token 失败: {data.get('msg', '')}")
            self._tenant_token = data["tenant_access_token"]
            self._token_expire_at = time.time() + data.get("expire", 7200)
            return self._tenant_token

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | list[Any] | None = None,
    ) -> dict[str, Any]:
        """通用飞书 API 请求，含 90217 限流自动重试（最多 3 次）"""
        token = await self._ensure_token()
        max_retries = 3
        for attempt in range(max_retries):
            url = f"{self.base_url}{path}"
            resp = await self._get_http().request(
                method,
                url,
                headers={"Authorization": f"Bearer {token}"},
                params=params,
                json=json_data,
            )
            data = resp.json()
            code = data.get("code", -1)
            if code == 90217:  # too many request
                wait = 1.5 * (attempt + 1)
                await asyncio.sleep(wait)
                continue
            if code != 0:
                hint = _FEISHU_ERRORS.get(code, "")
                msg = data.get("msg", "")
                detail = f"。{hint}" if hint else ""
                raise Exception(f"[{method} {path}] 失败(code={code}): {msg}{detail}")
            return data.get("data", {})  # type: ignore[no-any-return]
        raise Exception(f"[{method} {path}] 重试 {max_retries} 次后仍失败: too many request")

    async def _get(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self._request("GET", path, params=params)

    async def _post(self, path: str, *, json_data: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self._request("POST", path, json_data=json_data)

    async def _put(self, path: str, *, json_data: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self._request("PUT", path, json_data=json_data)

    @staticmethod
    def _index_to_letter(index: int) -> str:
        """0-based 列索引转列字母：0→A, 25→Z, 26→AA, 701→ZZ"""
        result = ""
        while True:
            result = chr(ord("A") + index % 26) + result
            index = index // 26 - 1
            if index < 0:
                break
        return result

    async def close(self) -> None:
        """释放 httpx 客户端连接"""
        if self._http:
            await self._http.aclose()
            self._http = None
