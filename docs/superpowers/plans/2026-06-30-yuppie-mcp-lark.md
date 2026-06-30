# yuppie-mcp-lark 改造实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将当前从 `yuppie-mcp-mssql` 复制而来的仓库改造为 `yuppie-mcp-lark` —— 一个对接飞书 OpenAPI 的 MCP Server。

**Architecture:** 沿用 mssql 项目的工程骨架（FastMCP + Pydantic + async + ruff/mypy/pytest），底层飞书客户端用 mixin 模式按业务域拆分（`_LarkBase` + `MessagesMixin`/`BitableMixin`/`SheetsMixin` → `LarkClient`），MCP 工具层按域组织（`tools/messages.py`/`tools/bitable.py`/`tools/sheets.py`），`server.py` 用 `Annotated` 参数 + `ToolAnnotations` 注册 10 个工具。

**Tech Stack:** Python ≥3.10、FastMCP（mcp 包）、httpx、pydantic v2、pytest + pytest-asyncio、ruff、mypy。

**Spec:** `docs/superpowers/specs/2026-06-30-yuppie-mcp-lark-design.md`

---

## 文件结构

### 删除
- `src/yuppie_mcp_mssql/`（整个目录）
- `tests/test_sql_guard.py`、`tests/test_export.py`
- `doc/lark_client.py`（Task 10 迁移完成后删除原件）

### 新建
- `src/yuppie_mcp_lark/__init__.py` — 包入口，暴露 `__version__`
- `src/yuppie_mcp_lark/__main__.py` — 支持 `python -m yuppie_mcp_lark`
- `src/yuppie_mcp_lark/server.py` — MCP 入口，注册 10 个工具，`main()` 函数
- `src/yuppie_mcp_lark/utils/__init__.py` — 空包标记
- `src/yuppie_mcp_lark/utils/config.py` — `LarkConfig` 数据类，`from_env()` 工厂
- `src/yuppie_mcp_lark/utils/lark/__init__.py` — 聚合 `LarkClient`
- `src/yuppie_mcp_lark/utils/lark/base.py` — `_LarkBase`：http client、token、`_request`/`_get`/`_post`/`_put`、`_index_to_letter`
- `src/yuppie_mcp_lark/utils/lark/messages.py` — `MessagesMixin`：`send_message`/`send_messages`
- `src/yuppie_mcp_lark/utils/lark/bitable.py` — `BitableMixin`：`search_records`
- `src/yuppie_mcp_lark/utils/lark/sheets.py` — `SheetsMixin`：8 个电子表格方法
- `src/yuppie_mcp_lark/tools/__init__.py` — 空包标记
- `src/yuppie_mcp_lark/tools/messages.py` — 消息域工具
- `src/yuppie_mcp_lark/tools/bitable.py` — 多维表格域工具
- `src/yuppie_mcp_lark/tools/sheets.py` — 电子表格域工具
- `tests/test_config.py` — `LarkConfig` 测试
- `tests/test_lark_client.py` — `_index_to_letter` + `LarkClient` 聚合测试
- `tests/test_tools.py` — 工具 BaseModel 输入校验测试

### 修改
- `pyproject.toml` — 包名、入口、依赖、URL、keywords、classifiers
- `README.md` — 整体重写
- `CLAUDE.md` — 项目概述、命令、架构改为 lark 版本
- `.env.example` — 改为 `LARK_APP_ID`/`LARK_APP_SECRET`/`LARK_BASE_URL`
- `scripts/publish.sh` — 包名引用改为 `yuppie-mcp-lark`

---

## Task 1: 清理 mssql 骨架，创建 lark 包骨架

**Files:**
- Delete: `src/yuppie_mcp_mssql/`（整个目录）
- Delete: `tests/test_sql_guard.py`、`tests/test_export.py`
- Create: `src/yuppie_mcp_lark/__init__.py`、`src/yuppie_mcp_lark/__main__.py`
- Create: `src/yuppie_mcp_lark/utils/__init__.py`、`src/yuppie_mcp_lark/tools/__init__.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: 删除 mssql 源码和测试**

```bash
rm -rf src/yuppie_mcp_mssql
rm -f tests/test_sql_guard.py tests/test_export.py
```

- [ ] **Step 2: 创建 lark 包目录结构**

```bash
mkdir -p src/yuppie_mcp_lark/utils/lark src/yuppie_mcp_lark/tools
```

- [ ] **Step 3: 写 `src/yuppie_mcp_lark/__init__.py`**

```python
"""yuppie-mcp-lark: 飞书 MCP Server"""

__version__ = "0.1.0"
```

- [ ] **Step 4: 写 `src/yuppie_mcp_lark/__main__.py`**

```python
"""允许通过 python -m yuppie_mcp_lark 运行"""

from .server import main

if __name__ == "__main__":
    main()
```

- [ ] **Step 5: 写 `src/yuppie_mcp_lark/utils/__init__.py` 和 `src/yuppie_mcp_lark/tools/__init__.py`**

两个文件都写入空内容（仅用作 Python 包标记），可留空字符串。

- [ ] **Step 6: 修改 `pyproject.toml`**

完整替换为：

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "yuppie-mcp-lark"
version = "0.1.0"
description = "MCP Server for Lark/Feishu OpenAPI"
readme = "README.md"
license = "MIT"
requires-python = ">=3.10"
authors = [
    { name = "yuppie", email = "yidaowanli@gmail.com" }
]
keywords = ["mcp", "model-context-protocol", "lark", "feishu"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
dependencies = [
    "mcp>=1.0.0",
    "httpx>=0.27.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "ruff>=0.4.0",
    "mypy>=1.10.0",
]

[project.urls]
Homepage = "https://github.com/yuppie1949/yuppie-mcp-lark"
Repository = "https://github.com/yuppie1949/yuppie-mcp-lark"

[project.scripts]
yuppie-mcp-lark = "yuppie_mcp_lark.server:main"

[tool.hatch.build.targets.wheel]
packages = ["src/yuppie_mcp_lark"]

[tool.hatch.build.targets.sdist]
include = [
    "/src",
    "/README.md",
    "/LICENSE",
    "/pyproject.toml",
]
exclude = [
    "/.git",
    "/.github",
    "/.venv",
    "/__pycache__",
    "/.pytest_cache",
    "/.mypy_cache",
    "/.ruff_cache",
    "/dist",
    "/build",
    "/.env",
    "/.env.example",
    "/docs",
    "/tests",
    "/.neuralmemory",
    "/scripts",
    "/.DS_Store",
]

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "I", "W"]

[tool.mypy]
python_version = "3.10"
strict = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 7: 重新安装依赖（更新 lock）**

```bash
uv pip install -e ".[dev]"
```

Expected: 安装成功，`httpx` 进入依赖，`python-tds` 移除。

- [ ] **Step 8: 验证包可导入**

```bash
python -c "import yuppie_mcp_lark; print(yuppie_mcp_lark.__version__)"
```

Expected: 输出 `0.1.0`（`__main__.py` 此时 import server 会失败属正常，本步只验证 `__init__.py`）。

- [ ] **Step 9: Commit**

```bash
git add -A
git commit -m "refactor: remove mssql scaffold, init yuppie_mcp_lark package skeleton"
```

---

## Task 2: 实现 `utils/config.py`（TDD）

**Files:**
- Create: `src/yuppie_mcp_lark/utils/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: 写失败测试 `tests/test_config.py`**

```python
"""LarkConfig 环境变量读取与校验测试"""

import pytest

from yuppie_mcp_lark.utils.config import DEFAULT_BASE_URL, LarkConfig


def test_from_env_requires_app_id(monkeypatch):
    monkeypatch.delenv("LARK_APP_ID", raising=False)
    monkeypatch.setenv("LARK_APP_SECRET", "secret")
    with pytest.raises(ValueError, match="LARK_APP_ID"):
        LarkConfig.from_env()


def test_from_env_requires_app_secret(monkeypatch):
    monkeypatch.setenv("LARK_APP_ID", "id")
    monkeypatch.delenv("LARK_APP_SECRET", raising=False)
    with pytest.raises(ValueError, match="LARK_APP_SECRET"):
        LarkConfig.from_env()


def test_from_env_defaults_base_url(monkeypatch):
    monkeypatch.setenv("LARK_APP_ID", "id")
    monkeypatch.setenv("LARK_APP_SECRET", "secret")
    monkeypatch.delenv("LARK_BASE_URL", raising=False)
    cfg = LarkConfig.from_env()
    assert cfg.app_id == "id"
    assert cfg.app_secret == "secret"
    assert cfg.base_url == DEFAULT_BASE_URL


def test_from_env_strips_trailing_slash(monkeypatch):
    monkeypatch.setenv("LARK_APP_ID", "id")
    monkeypatch.setenv("LARK_APP_SECRET", "secret")
    monkeypatch.setenv("LARK_BASE_URL", "https://open.larksuite.com/")
    cfg = LarkConfig.from_env()
    assert cfg.base_url == "https://open.larksuite.com"


def test_from_env_strips_whitespace(monkeypatch):
    monkeypatch.setenv("LARK_APP_ID", "  id  ")
    monkeypatch.setenv("LARK_APP_SECRET", "  secret  ")
    cfg = LarkConfig.from_env()
    assert cfg.app_id == "id"
    assert cfg.app_secret == "secret"
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
uv run pytest tests/test_config.py -v
```

Expected: FAIL，提示 `ModuleNotFoundError: No module named 'yuppie_mcp_lark.utils.config'`。

- [ ] **Step 3: 实现 `src/yuppie_mcp_lark/utils/config.py`**

```python
"""飞书 MCP Server 配置：从环境变量读取并校验"""

from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_BASE_URL = "https://open.feishu.cn"


@dataclass
class LarkConfig:
    """运行配置：飞书应用凭证 + API 域名"""

    app_id: str
    app_secret: str
    base_url: str = DEFAULT_BASE_URL

    @classmethod
    def from_env(cls) -> LarkConfig:
        """从环境变量构造配置，缺少必填项时抛 ValueError"""
        app_id = os.environ.get("LARK_APP_ID", "").strip()
        app_secret = os.environ.get("LARK_APP_SECRET", "").strip()
        base_url = os.environ.get("LARK_BASE_URL", DEFAULT_BASE_URL).strip().rstrip("/")

        if not app_id:
            raise ValueError("缺少必填环境变量 LARK_APP_ID")
        if not app_secret:
            raise ValueError("缺少必填环境变量 LARK_APP_SECRET")

        return cls(app_id=app_id, app_secret=app_secret, base_url=base_url)
```

- [ ] **Step 4: 运行测试，确认通过**

```bash
uv run pytest tests/test_config.py -v
```

Expected: 5 passed。

- [ ] **Step 5: Commit**

```bash
git add src/yuppie_mcp_lark/utils/config.py tests/test_config.py
git commit -m "feat(config): add LarkConfig with env-based validation"
```

---

## Task 3: 实现 `utils/lark/base.py`（TDD 纯函数）

**Files:**
- Create: `src/yuppie_mcp_lark/utils/lark/__init__.py`（临时占位，Task 7 完善）
- Create: `src/yuppie_mcp_lark/utils/lark/base.py`
- Create: `tests/test_lark_client.py`

- [ ] **Step 1: 写失败测试 `tests/test_lark_client.py`**

```python
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
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
uv run pytest tests/test_lark_client.py -v
```

Expected: FAIL，`ModuleNotFoundError: No module named 'yuppie_mcp_lark.utils.lark.base'`。

- [ ] **Step 3: 写临时占位 `src/yuppie_mcp_lark/utils/lark/__init__.py`**

```python
"""LarkClient 包 — Task 7 会聚合 mixin"""
```

（此文件 Task 7 会重写，先放占位让 base.py 能被导入。）

- [ ] **Step 4: 实现 `src/yuppie_mcp_lark/utils/lark/base.py`**

```python
"""飞书 OpenAPI 客户端基类：HTTP 客户端、token 管理、通用请求"""

from __future__ import annotations

import asyncio
import time
from typing import Optional

import httpx


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
        params: dict | None = None,
        json_data: dict | list | None = None,
    ) -> dict:
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
                raise Exception(
                    f"[{method} {path}] 失败(code={code}): {data.get('msg', '')}"
                )
            return data.get("data", {})
        raise Exception(
            f"[{method} {path}] 重试 {max_retries} 次后仍失败: too many request"
        )

    async def _get(self, path: str, *, params: dict | None = None) -> dict:
        return await self._request("GET", path, params=params)

    async def _post(self, path: str, *, json_data: dict | None = None) -> dict:
        return await self._request("POST", path, json_data=json_data)

    async def _put(self, path: str, *, json_data: dict | None = None) -> dict:
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
```

- [ ] **Step 5: 运行测试，确认通过**

```bash
uv run pytest tests/test_lark_client.py -v
```

Expected: 10 passed（9 个 parametrize + 1 个 init）。

- [ ] **Step 6: Commit**

```bash
git add src/yuppie_mcp_lark/utils/lark/__init__.py src/yuppie_mcp_lark/utils/lark/base.py tests/test_lark_client.py
git commit -m "feat(lark): add _LarkBase with token management and request retry"
```

---

## Task 4: 实现 `utils/lark/messages.py`

**Files:**
- Create: `src/yuppie_mcp_lark/utils/lark/messages.py`

> 说明：本任务不写新测试——`send_message`/`send_messages` 是飞书 API 薄包装，按 spec 第 7 节不测网络调用。Task 7 会通过 `LarkClient` 聚合测试验证方法可见性。

- [ ] **Step 1: 实现 `src/yuppie_mcp_lark/utils/lark/messages.py`**

```python
"""消息域 mixin — 飞书 IM 消息发送"""

from __future__ import annotations

from .base import _LarkBase


class MessagesMixin:
    """消息域方法（混入 _LarkBase 子类使用）"""

    async def send_message(
        self: _LarkBase,
        receive_id: str,
        msg_type: str,
        content: str,
        *,
        receive_id_type: str = "open_id",
    ) -> dict:
        """发送消息给单个用户/群

        文档: https://open.feishu.cn/document/server-docs/im/v1/message/create
        """
        return await self._request(
            "POST",
            "/open-apis/im/v1/messages",
            params={"receive_id_type": receive_id_type},
            json_data={
                "receive_id": receive_id,
                "msg_type": msg_type,
                "content": content,
            },
        )

    async def send_messages(
        self: _LarkBase,
        receive_ids: list[str],
        msg_type: str,
        content: str,
        *,
        receive_id_type: str = "open_id",
    ) -> list[dict]:
        """批量发送消息，返回 [{receive_id, message_id, error?}] 列表"""
        results: list[dict] = []
        for uid in receive_ids:
            try:
                data = await self.send_message(
                    uid, msg_type, content, receive_id_type=receive_id_type
                )
                results.append({"receive_id": uid, "message_id": data.get("message_id", "")})
            except Exception as e:
                results.append(
                    {"receive_id": uid, "message_id": "", "error": str(e)}
                )
        return results
```

- [ ] **Step 2: 验证模块可导入**

```bash
python -c "from yuppie_mcp_lark.utils.lark.messages import MessagesMixin; print('ok')"
```

Expected: 输出 `ok`。

- [ ] **Step 3: Commit**

```bash
git add src/yuppie_mcp_lark/utils/lark/messages.py
git commit -m "feat(lark): add MessagesMixin for IM message sending"
```

---

## Task 5: 实现 `utils/lark/bitable.py`

**Files:**
- Create: `src/yuppie_mcp_lark/utils/lark/bitable.py`

- [ ] **Step 1: 实现 `src/yuppie_mcp_lark/utils/lark/bitable.py`**

```python
"""多维表格域 mixin — 飞书 Bitable 记录搜索"""

from __future__ import annotations

from .base import _LarkBase


class BitableMixin:
    """多维表格域方法（混入 _LarkBase 子类使用）"""

    async def search_records(
        self: _LarkBase,
        app_token: str,
        table_id: str,
        *,
        view_id: str | None = None,
        field_names: list[str] | None = None,
        sort: dict | None = None,
        filter: dict | None = None,
        page_token: str | None = None,
        page_size: int | None = None,
        automatic_fields: bool | None = None,
        user_id_type: str | None = None,
    ) -> dict:
        """搜索多维表格记录，返回 {items, has_more, page_token, total}

        文档: https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-record/search
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
```

- [ ] **Step 2: 验证模块可导入**

```bash
python -c "from yuppie_mcp_lark.utils.lark.bitable import BitableMixin; print('ok')"
```

Expected: 输出 `ok`。

- [ ] **Step 3: Commit**

```bash
git add src/yuppie_mcp_lark/utils/lark/bitable.py
git commit -m "feat(lark): add BitableMixin for record search"
```

---

## Task 6: 实现 `utils/lark/sheets.py`

**Files:**
- Create: `src/yuppie_mcp_lark/utils/lark/sheets.py`

> 说明：spec 第 3 节列了 `_resolve_column_letter` 在 SheetsMixin 中，但剔除业务定制方法（`filter_sheet_columns` 等）后无调用方，按 YAGNI 不实现。本任务只实现 8 个通用方法。

- [ ] **Step 1: 实现 `src/yuppie_mcp_lark/utils/lark/sheets.py`**

```python
"""电子表格域 mixin — 飞书 Sheets 工作表与数据操作"""

from __future__ import annotations

from .base import _LarkBase


class SheetsMixin:
    """电子表格域方法（混入 _LarkBase 子类使用）"""

    async def get_metainfo(self: _LarkBase, spreadsheet_token: str) -> dict:
        """获取表格元信息（含工作表列表）

        文档: https://open.feishu.cn/document/server-docs/historic-version/docs/sheets/obtain-spreadsheet-metadata
        """
        return await self._get(
            f"/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/metainfo",
            params={"ext_fields": "protectedRange"},
        )

    async def add_sheet(self: _LarkBase, spreadsheet_token: str, title: str) -> str:
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

    async def delete_sheet(
        self: _LarkBase, spreadsheet_token: str, sheet_id: str
    ) -> None:
        """删除工作表"""
        await self._post(
            f"/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/sheets_batch_update",
            json_data={"requests": [{"deleteSheet": {"sheetId": sheet_id}}]},
        )

    async def copy_sheet(
        self: _LarkBase, spreadsheet_token: str, source_sheet_id: str, title: str
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
        self: _LarkBase, spreadsheet_token: str, range_str: str
    ) -> list[list]:
        """读取单个范围数据，返回二维数组

        文档: https://open.feishu.cn/document/server-docs/docs/sheets-v3/data-operation/reading-a-single-range
        """
        data = await self._get(
            f"/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values/{range_str}",
        )
        return data.get("valueRange", {}).get("values", [])

    async def write_range(
        self: _LarkBase,
        spreadsheet_token: str,
        range_str: str,
        values: list[list],
    ) -> dict:
        """向单个范围写入数据（≤5000 行、100 列）

        文档: https://open.feishu.cn/document/server-docs/docs/sheets-v3/data-operation/write-data-to-a-single-range
        """
        return await self._put(
            f"/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values",
            json_data={"valueRange": {"range": range_str, "values": values}},
        )

    async def append_data(
        self: _LarkBase, spreadsheet_token: str, sheet_id: str, values: list[list]
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
                    "range": f"{sheet_id}!A1:{end_col}",
                    "values": values,
                }
            },
        )

    async def delete_dimension(
        self: _LarkBase,
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
```

- [ ] **Step 2: 验证模块可导入**

```bash
python -c "from yuppie_mcp_lark.utils.lark.sheets import SheetsMixin; print('ok')"
```

Expected: 输出 `ok`。

- [ ] **Step 3: Commit**

```bash
git add src/yuppie_mcp_lark/utils/lark/sheets.py
git commit -m "feat(lark): add SheetsMixin for spreadsheet operations"
```

---

## Task 7: 聚合 `utils/lark/__init__.py`，补全 `LarkClient` 测试

**Files:**
- Modify: `src/yuppie_mcp_lark/utils/lark/__init__.py`
- Modify: `tests/test_lark_client.py`（追加聚合测试）

- [ ] **Step 1: 重写 `src/yuppie_mcp_lark/utils/lark/__init__.py`**

```python
"""LarkClient — 通过 mixin 聚合消息、多维表格、电子表格能力

对外只暴露 LarkClient 一个类。token、http client 由 _LarkBase 统一管理，
各业务域方法分散在独立模块便于维护。
"""

from __future__ import annotations

from .base import _LarkBase
from .bitable import BitableMixin
from .messages import MessagesMixin
from .sheets import SheetsMixin

__all__ = ["LarkClient"]


class LarkClient(_LarkBase, MessagesMixin, BitableMixin, SheetsMixin):
    """飞书 OpenAPI 客户端"""

    pass
```

- [ ] **Step 2: 在 `tests/test_lark_client.py` 末尾追加聚合测试**

在文件末尾追加（不删除已有测试）：

```python
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
```

- [ ] **Step 3: 运行全部 client 测试**

```bash
uv run pytest tests/test_lark_client.py -v
```

Expected: 12 passed（Task 3 的 10 个 + 新增 2 个）。

- [ ] **Step 4: Commit**

```bash
git add src/yuppie_mcp_lark/utils/lark/__init__.py tests/test_lark_client.py
git commit -m "feat(lark): aggregate LarkClient from mixins and verify method visibility"
```

---

## Task 8: 实现 tools 层（TDD 输入校验）

**Files:**
- Create: `src/yuppie_mcp_lark/tools/messages.py`
- Create: `src/yuppie_mcp_lark/tools/bitable.py`
- Create: `src/yuppie_mcp_lark/tools/sheets.py`
- Create: `tests/test_tools.py`

> 设计：每个 tools 模块持有一个模块级 `_client` 单例和 `set_client()` 注入函数；server.py 启动时注入。BaseModel 用 `ConfigDict(str_strip_whitespace=True, extra="forbid")` 沿用 mssql 风格。

- [ ] **Step 1: 写失败测试 `tests/test_tools.py`**

```python
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
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
uv run pytest tests/test_tools.py -v
```

Expected: FAIL，`ModuleNotFoundError: No module named 'yuppie_mcp_lark.tools.messages'`。

- [ ] **Step 3: 实现 `src/yuppie_mcp_lark/tools/messages.py`**

```python
"""消息域 MCP 工具"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ..utils.lark import LarkClient

_client: LarkClient | None = None


def set_client(client: LarkClient) -> None:
    global _client
    _client = client


def _get_client() -> LarkClient:
    if _client is None:
        raise RuntimeError(
            "LarkClient 未初始化，请检查环境变量 LARK_APP_ID/LARK_APP_SECRET"
        )
    return _client


class SendMessageInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    receive_id: str = Field(..., min_length=1, description="接收者 ID")
    msg_type: str = Field("text", description="消息类型，默认 text")
    content: str = Field(..., min_length=1, description="消息内容 JSON 字符串")
    receive_id_type: str = Field(
        "open_id", description="ID 类型：open_id / user_id / union_id / chat_id"
    )


async def send_message(args: SendMessageInput) -> str:
    client = _get_client()
    try:
        data = await client.send_message(
            args.receive_id,
            args.msg_type,
            args.content,
            receive_id_type=args.receive_id_type,
        )
        return (
            "✅ 发送成功\n\n"
            f"- **message_id**: `{data.get('message_id', '')}`\n"
            f"- **receive_id**: `{args.receive_id}`\n"
            f"- **msg_type**: `{args.msg_type}`"
        )
    except Exception as e:
        return f"❌ 发送失败：{e}"
```

- [ ] **Step 4: 实现 `src/yuppie_mcp_lark/tools/bitable.py`**

```python
"""多维表格域 MCP 工具"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ..utils.lark import LarkClient

_client: LarkClient | None = None


def set_client(client: LarkClient) -> None:
    global _client
    _client = client


def _get_client() -> LarkClient:
    if _client is None:
        raise RuntimeError(
            "LarkClient 未初始化，请检查环境变量 LARK_APP_ID/LARK_APP_SECRET"
        )
    return _client


class SearchRecordsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    app_token: str = Field(..., min_length=1, description="多维表格 app_token")
    table_id: str = Field(..., min_length=1, description="数据表 table_id")
    view_id: str | None = Field(None, description="视图 ID")
    field_names: list[str] | None = Field(None, description="指定返回字段名列表")
    sort: dict | None = Field(None, description="排序规则，如 {field_name, desc}")
    filter: dict | None = Field(None, description="过滤条件")
    page_token: str | None = Field(None, description="分页 token")
    page_size: int | None = Field(None, ge=1, le=500, description="分页大小")
    automatic_fields: bool | None = Field(None, description="是否返回自动计算字段")
    user_id_type: str | None = Field(
        None, description="用户 ID 类型：open_id / user_id / union_id"
    )


async def search_records(args: SearchRecordsInput) -> str:
    client = _get_client()
    try:
        data = await client.search_records(
            args.app_token,
            args.table_id,
            view_id=args.view_id,
            field_names=args.field_names,
            sort=args.sort,
            filter=args.filter,
            page_token=args.page_token,
            page_size=args.page_size,
            automatic_fields=args.automatic_fields,
            user_id_type=args.user_id_type,
        )
    except Exception as e:
        return f"❌ 搜索失败：{e}"

    items = data.get("items", [])
    total = data.get("total", 0)
    has_more = data.get("has_more", False)
    page_token = data.get("page_token", "")
    if not items:
        return "查询完成，无匹配记录"

    keys = list(items[0].keys())
    header = "| " + " | ".join(keys) + " |"
    sep = "| " + " | ".join("---" for _ in keys) + " |"
    body = "\n".join(
        "| " + " | ".join(str(item.get(k, "")) for k in keys) + " |"
        for item in items
    )
    more_hint = (
        f"\n\n> 还有更多数据，page_token=`{page_token}`"
        if has_more
        else ""
    )
    return f"查询完成，共 {total} 条记录\n\n{header}\n{sep}\n{body}{more_hint}"
```

- [ ] **Step 5: 实现 `src/yuppie_mcp_lark/tools/sheets.py`**

```python
"""电子表格域 MCP 工具"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from ..utils.lark import LarkClient

_client: LarkClient | None = None


def set_client(client: LarkClient) -> None:
    global _client
    _client = client


def _get_client() -> LarkClient:
    if _client is None:
        raise RuntimeError(
            "LarkClient 未初始化，请检查环境变量 LARK_APP_ID/LARK_APP_SECRET"
        )
    return _client


class GetMetainfoInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_token: str = Field(..., min_length=1, description="电子表格 token")


class AddSheetInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_token: str = Field(..., min_length=1, description="电子表格 token")
    title: str = Field(..., min_length=1, description="新工作表标题")


class DeleteSheetInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_token: str = Field(..., min_length=1, description="电子表格 token")
    sheet_id: str = Field(..., min_length=1, description="工作表 ID")


class CopySheetInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_token: str = Field(..., min_length=1, description="电子表格 token")
    source_sheet_id: str = Field(..., min_length=1, description="源工作表 ID")
    title: str = Field(..., min_length=1, description="新工作表标题")


class ReadRangeInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_token: str = Field(..., min_length=1, description="电子表格 token")
    range_str: str = Field(..., min_length=1, description="范围，如 Sheet1!A1:C10")


class WriteRangeInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_token: str = Field(..., min_length=1, description="电子表格 token")
    range_str: str = Field(..., min_length=1, description="范围")
    values: list[list] = Field(..., description="二维数组")


class AppendDataInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_token: str = Field(..., min_length=1, description="电子表格 token")
    sheet_id: str = Field(..., min_length=1, description="工作表 ID")
    values: list[list] = Field(..., description="二维数组")


class DeleteDimensionInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    spreadsheet_token: str = Field(..., min_length=1, description="电子表格 token")
    sheet_id: str = Field(..., min_length=1, description="工作表 ID")
    major_dimension: str = Field(
        "COLUMNS", description="COLUMNS 或 ROWS，默认 COLUMNS"
    )
    start_index: int = Field(..., ge=1, description="起始索引（1-based 含）")
    end_index: int = Field(..., ge=1, description="结束索引（1-based 含）")


async def get_metainfo(args: GetMetainfoInput) -> str:
    client = _get_client()
    try:
        data = await client.get_metainfo(args.spreadsheet_token)
    except Exception as e:
        return f"❌ 获取元信息失败：{e}"
    sheets = data.get("sheets", [])
    lines = [f"标题: **{data.get('title', '')}**", ""]
    lines.append(f"| 工作表 | sheetId | 行数 | 列数 |")
    lines.append(f"| --- | --- | --- | --- |")
    for s in sheets:
        lines.append(
            f"| {s.get('title', '')} | {s.get('sheetId', '')} | "
            f"{s.get('rowCount', 0)} | {s.get('columnCount', 0)} |"
        )
    return "\n".join(lines)


async def add_sheet(args: AddSheetInput) -> str:
    client = _get_client()
    try:
        sheet_id = await client.add_sheet(args.spreadsheet_token, args.title)
        return f"✅ 工作表已创建\n\n- **title**: `{args.title}`\n- **sheetId**: `{sheet_id}`"
    except Exception as e:
        return f"❌ 创建工作表失败：{e}"


async def delete_sheet(args: DeleteSheetInput) -> str:
    client = _get_client()
    try:
        await client.delete_sheet(args.spreadsheet_token, args.sheet_id)
        return f"✅ 工作表已删除\n\n- **sheetId**: `{args.sheet_id}`"
    except Exception as e:
        return f"❌ 删除工作表失败：{e}"


async def copy_sheet(args: CopySheetInput) -> str:
    client = _get_client()
    try:
        sheet_id = await client.copy_sheet(
            args.spreadsheet_token, args.source_sheet_id, args.title
        )
        return (
            f"✅ 工作表已复制\n\n"
            f"- **source_sheet_id**: `{args.source_sheet_id}`\n"
            f"- **new_sheetId**: `{sheet_id}`"
        )
    except Exception as e:
        return f"❌ 复制工作表失败：{e}"


async def read_range(args: ReadRangeInput) -> str:
    client = _get_client()
    try:
        data = await client.read_range(args.spreadsheet_token, args.range_str)
    except Exception as e:
        return f"❌ 读取失败：{e}"
    if not data:
        return "范围为空"
    rows = len(data)
    cols = max(len(r) for r in data)
    preview_rows = data[:10]
    header = "| " + " | ".join(f"col{i}" for i in range(cols)) + " |"
    sep = "| " + " | ".join("---" for _ in range(cols)) + " |"
    body = "\n".join(
        "| "
        + " | ".join(str(r[i]) if i < len(r) else "" for i in range(cols))
        + " |"
        for r in preview_rows
    )
    truncated = f"\n\n> 共 {rows} 行，仅显示前 10 行" if rows > 10 else ""
    return f"读取完成（{rows} 行 × {cols} 列）\n\n{header}\n{sep}\n{body}{truncated}"


async def write_range(args: WriteRangeInput) -> str:
    client = _get_client()
    try:
        await client.write_range(
            args.spreadsheet_token, args.range_str, args.values
        )
        rows = len(args.values)
        return (
            f"✅ 写入完成\n\n"
            f"- **range**: `{args.range_str}`\n"
            f"- **rows**: `{rows}`"
        )
    except Exception as e:
        return f"❌ 写入失败：{e}"


async def append_data(args: AppendDataInput) -> str:
    client = _get_client()
    try:
        await client.append_data(
            args.spreadsheet_token, args.sheet_id, args.values
        )
        rows = len(args.values)
        return (
            f"✅ 追加完成\n\n"
            f"- **sheet_id**: `{args.sheet_id}`\n"
            f"- **rows**: `{rows}`"
        )
    except Exception as e:
        return f"❌ 追加失败：{e}"


async def delete_dimension(args: DeleteDimensionInput) -> str:
    client = _get_client()
    try:
        await client.delete_dimension(
            args.spreadsheet_token,
            args.sheet_id,
            major_dimension=args.major_dimension,
            start_index=args.start_index,
            end_index=args.end_index,
        )
        return (
            f"✅ 删除完成\n\n"
            f"- **dimension**: `{args.major_dimension}`\n"
            f"- **range**: `{args.start_index}` 到 `{args.end_index}`（1-based 含首尾）"
        )
    except Exception as e:
        return f"❌ 删除失败：{e}"
```

- [ ] **Step 6: 运行测试，确认通过**

```bash
uv run pytest tests/test_tools.py -v
```

Expected: 13 passed。

- [ ] **Step 7: Commit**

```bash
git add src/yuppie_mcp_lark/tools/ tests/test_tools.py
git commit -m "feat(tools): add message/bitable/sheets tools with pydantic validation"
```

---

## Task 9: 实现 `server.py`

**Files:**
- Create: `src/yuppie_mcp_lark/server.py`

> 设计：模块级 `mcp = FastMCP("lark_mcp")`；启动时 `LarkConfig.from_env()` → 实例化 `LarkClient` → 注入到三个 tools 模块。10 个工具用 `@mcp.tool(name=..., annotations=ToolAnnotations(...))` 注册，参数用 `Annotated` 风格（沿用 mssql 项目）。

- [ ] **Step 1: 实现 `src/yuppie_mcp_lark/server.py`**

```python
"""飞书 MCP Server 主入口"""

from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .tools import bitable, messages, sheets
from .tools.bitable import SearchRecordsInput
from .tools.messages import SendMessageInput
from .tools.sheets import (
    AddSheetInput,
    AppendDataInput,
    CopySheetInput,
    DeleteDimensionInput,
    DeleteSheetInput,
    GetMetainfoInput,
    ReadRangeInput,
    WriteRangeInput,
)
from .utils.config import LarkConfig
from .utils.lark import LarkClient

mcp = FastMCP("lark_mcp")


def _init_client() -> LarkClient:
    """从环境变量构造 LarkClient 并注入到各 tools 模块"""
    config = LarkConfig.from_env()
    client = LarkClient(config.app_id, config.app_secret, config.base_url)
    messages.set_client(client)
    bitable.set_client(client)
    sheets.set_client(client)
    return client


@mcp.tool(
    name="lark_send_message",
    annotations=ToolAnnotations(
        title="发送飞书消息",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_send_message(
    receive_id: Annotated[str, Field(description="接收者 ID", min_length=1)],
    content: Annotated[str, Field(description="消息内容 JSON 字符串", min_length=1)],
    msg_type: Annotated[str, Field(description="消息类型，默认 text")] = "text",
    receive_id_type: Annotated[
        str,
        Field(description="ID 类型：open_id / user_id / union_id / chat_id"),
    ] = "open_id",
) -> str:
    """发送消息给单个用户或群。

    content 是 JSON 字符串，例如 text 类型消息：'{"text":"你好"}'。
    """
    return await messages.send_message(
        SendMessageInput(
            receive_id=receive_id,
            msg_type=msg_type,
            content=content,
            receive_id_type=receive_id_type,
        )
    )


@mcp.tool(
    name="lark_search_records",
    annotations=ToolAnnotations(
        title="搜索多维表格记录",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def tool_search_records(
    app_token: Annotated[str, Field(description="多维表格 app_token", min_length=1)],
    table_id: Annotated[str, Field(description="数据表 table_id", min_length=1)],
    view_id: Annotated[str | None, Field(description="视图 ID")] = None,
    field_names: Annotated[
        list[str] | None, Field(description="指定返回字段名列表")
    ] = None,
    sort: Annotated[dict | None, Field(description="排序规则")] = None,
    filter: Annotated[dict | None, Field(description="过滤条件")] = None,
    page_token: Annotated[str | None, Field(description="分页 token")] = None,
    page_size: Annotated[
        int | None, Field(description="分页大小（1-500）", ge=1, le=500)
    ] = None,
    automatic_fields: Annotated[
        bool | None, Field(description="是否返回自动计算字段")
    ] = None,
    user_id_type: Annotated[
        str | None,
        Field(description="用户 ID 类型：open_id / user_id / union_id"),
    ] = None,
) -> str:
    """搜索多维表格记录，返回 markdown 表格。支持分页、排序、过滤。"""
    return await bitable.search_records(
        SearchRecordsInput(
            app_token=app_token,
            table_id=table_id,
            view_id=view_id,
            field_names=field_names,
            sort=sort,
            filter=filter,
            page_token=page_token,
            page_size=page_size,
            automatic_fields=automatic_fields,
            user_id_type=user_id_type,
        )
    )


@mcp.tool(
    name="lark_get_spreadsheet_metainfo",
    annotations=ToolAnnotations(
        title="获取电子表格元信息",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def tool_get_metainfo(
    spreadsheet_token: Annotated[
        str, Field(description="电子表格 token", min_length=1)
    ],
) -> str:
    """获取电子表格元信息，含工作表列表（标题、sheetId、行数、列数）。"""
    return await sheets.get_metainfo(GetMetainfoInput(spreadsheet_token=spreadsheet_token))


@mcp.tool(
    name="lark_add_sheet",
    annotations=ToolAnnotations(
        title="添加工作表",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_add_sheet(
    spreadsheet_token: Annotated[
        str, Field(description="电子表格 token", min_length=1)
    ],
    title: Annotated[str, Field(description="新工作表标题", min_length=1)],
) -> str:
    """添加工作表，返回新 sheetId。"""
    return await sheets.add_sheet(
        AddSheetInput(spreadsheet_token=spreadsheet_token, title=title)
    )


@mcp.tool(
    name="lark_delete_sheet",
    annotations=ToolAnnotations(
        title="删除工作表",
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_delete_sheet(
    spreadsheet_token: Annotated[
        str, Field(description="电子表格 token", min_length=1)
    ],
    sheet_id: Annotated[str, Field(description="工作表 ID", min_length=1)],
) -> str:
    """删除指定工作表。"""
    return await sheets.delete_sheet(
        DeleteSheetInput(spreadsheet_token=spreadsheet_token, sheet_id=sheet_id)
    )


@mcp.tool(
    name="lark_copy_sheet",
    annotations=ToolAnnotations(
        title="复制工作表",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_copy_sheet(
    spreadsheet_token: Annotated[
        str, Field(description="电子表格 token", min_length=1)
    ],
    source_sheet_id: Annotated[str, Field(description="源工作表 ID", min_length=1)],
    title: Annotated[str, Field(description="新工作表标题", min_length=1)],
) -> str:
    """复制工作表，返回新 sheetId。"""
    return await sheets.copy_sheet(
        CopySheetInput(
            spreadsheet_token=spreadsheet_token,
            source_sheet_id=source_sheet_id,
            title=title,
        )
    )


@mcp.tool(
    name="lark_read_range",
    annotations=ToolAnnotations(
        title="读取电子表格范围",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def tool_read_range(
    spreadsheet_token: Annotated[
        str, Field(description="电子表格 token", min_length=1)
    ],
    range_str: Annotated[
        str, Field(description="范围，如 Sheet1!A1:C10", min_length=1)
    ],
) -> str:
    """读取单个范围数据，返回 markdown 表格（超过 10 行仅预览前 10 行）。"""
    return await sheets.read_range(
        ReadRangeInput(spreadsheet_token=spreadsheet_token, range_str=range_str)
    )


@mcp.tool(
    name="lark_write_range",
    annotations=ToolAnnotations(
        title="写入电子表格范围",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_write_range(
    spreadsheet_token: Annotated[
        str, Field(description="电子表格 token", min_length=1)
    ],
    range_str: Annotated[str, Field(description="范围", min_length=1)],
    values: Annotated[list[list], Field(description="二维数组")],
) -> str:
    """向单个范围写入数据（≤5000 行、100 列）。"""
    return await sheets.write_range(
        WriteRangeInput(
            spreadsheet_token=spreadsheet_token,
            range_str=range_str,
            values=values,
        )
    )


@mcp.tool(
    name="lark_append_data",
    annotations=ToolAnnotations(
        title="追加电子表格数据",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_append_data(
    spreadsheet_token: Annotated[
        str, Field(description="电子表格 token", min_length=1)
    ],
    sheet_id: Annotated[str, Field(description="工作表 ID", min_length=1)],
    values: Annotated[list[list], Field(description="二维数组")],
) -> str:
    """追加数据到工作表（自动找空白位置写入）。"""
    return await sheets.append_data(
        AppendDataInput(
            spreadsheet_token=spreadsheet_token,
            sheet_id=sheet_id,
            values=values,
        )
    )


@mcp.tool(
    name="lark_delete_dimension",
    annotations=ToolAnnotations(
        title="删除电子表格行列",
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_delete_dimension(
    spreadsheet_token: Annotated[
        str, Field(description="电子表格 token", min_length=1)
    ],
    sheet_id: Annotated[str, Field(description="工作表 ID", min_length=1)],
    start_index: Annotated[int, Field(description="起始索引（1-based 含）", ge=1)],
    end_index: Annotated[int, Field(description="结束索引（1-based 含）", ge=1)],
    major_dimension: Annotated[
        str, Field(description="COLUMNS 或 ROWS，默认 COLUMNS")
    ] = "COLUMNS",
) -> str:
    """删除行或列（1-based 含首尾，单次最多 5000 行/列）。"""
    return await sheets.delete_dimension(
        DeleteDimensionInput(
            spreadsheet_token=spreadsheet_token,
            sheet_id=sheet_id,
            major_dimension=major_dimension,
            start_index=start_index,
            end_index=end_index,
        )
    )


def main() -> None:
    _init_client()
    mcp.run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 验证缺凭据时报清晰错误**

```bash
unset LARK_APP_ID LARK_APP_SECRET
python -c "from yuppie_mcp_lark.server import _init_client; _init_client()"
```

Expected: 抛 `ValueError: 缺少必填环境变量 LARK_APP_ID`（来自 `LarkConfig.from_env()`）。

- [ ] **Step 3: 验证 server 注册了 10 个工具**

```bash
# 源码层：数 @mcp.tool 装饰器数量
grep -c "@mcp.tool" src/yuppie_mcp_lark/server.py
```
Expected: 输出 `10`。

```bash
# 运行时层：带凭据 import 不报错（FastMCP 内部 API 跨版本不稳定，只验证 import 成功）
export LARK_APP_ID=test_id
export LARK_APP_SECRET=test_secret
python -c "from yuppie_mcp_lark.server import mcp, _init_client; _init_client(); print('import ok')"
```
Expected: 输出 `import ok`。

- [ ] **Step 4: 运行全部测试确认无回归**

```bash
uv run pytest -v
```

Expected: 全部通过（test_config 5 + test_lark_client 12 + test_tools 13 = 30 passed）。

- [ ] **Step 5: Commit**

```bash
git add src/yuppie_mcp_lark/server.py
git commit -m "feat(server): register 10 lark tools and bootstrap client from env"
```

---

## Task 10: 更新文档与辅助文件，清理参考代码

**Files:**
- Modify: `README.md`（整体重写）
- Modify: `CLAUDE.md`（整体重写）
- Modify: `.env.example`
- Modify: `scripts/publish.sh`
- Delete: `doc/lark_client.py`

- [ ] **Step 1: 重写 `README.md`**

```markdown
# yuppie-mcp-lark

飞书（Lark / Feishu）MCP Server — 让 AI 助手通过 MCP 协议操作飞书消息、多维表格、电子表格。

## 特性

- 消息：发送单聊/群聊消息
- 多维表格：搜索记录（支持分页、排序、过滤）
- 电子表格：元信息查询、工作表增删复制、范围读写、追加数据、删除行列
- 鉴权：基于飞书应用 `tenant_access_token`，自动刷新
- 部署：仅 stdio，本地 AI 助手友好

## 快速开始

### Claude Code

在 `.mcp.json` 中添加：

```json
{
  "mcpServers": {
    "lark": {
      "type": "stdio",
      "command": "uvx",
      "args": ["yuppie-mcp-lark"],
      "env": {
        "LARK_APP_ID": "cli_xxx",
        "LARK_APP_SECRET": "xxx"
      }
    }
  }
}
```

### Cursor

在 `~/.cursor/mcp.json` 中添加同上配置。

### Cherry Studio / Claude Desktop / OpenCode

参照上方 env 字段，按各自 MCP 配置格式填入即可。

## 环境变量

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `LARK_APP_ID` | 是 | - | 飞书应用 App ID |
| `LARK_APP_SECRET` | 是 | - | 飞书应用 App Secret |
| `LARK_BASE_URL` | 否 | `https://open.feishu.cn` | 国际版设为 `https://open.larksuite.com` |

## 可用工具

| 工具 | 说明 |
|------|------|
| `lark_send_message` | 发送消息 |
| `lark_search_records` | 搜索多维表格记录 |
| `lark_get_spreadsheet_metainfo` | 获取电子表格元信息 |
| `lark_add_sheet` | 添加工作表 |
| `lark_delete_sheet` | 删除工作表 |
| `lark_copy_sheet` | 复制工作表 |
| `lark_read_range` | 读取范围数据 |
| `lark_write_range` | 写入范围数据 |
| `lark_append_data` | 追加数据 |
| `lark_delete_dimension` | 删除行列 |

## 测试与调试

```bash
uv pip install -e ".[dev]"
uv run pytest -v
```

使用 MCP Inspector 调试（需先在 `.env` 配置 `LARK_APP_ID` / `LARK_APP_SECRET`）：

```bash
npx @modelcontextprotocol/inspector uv run yuppie-mcp-lark
```

## License

MIT
```

- [ ] **Step 2: 重写 `CLAUDE.md`**

```markdown
# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## 项目概述

`yuppie-mcp-lark` 是一个 MCP (Model Context Protocol) Server，让 AI 助手通过 MCP 协议操作飞书（Lark / Feishu）。基于飞书 OpenAPI（`tenant_access_token` 鉴权），覆盖消息、多维表格、电子表格三大业务域。

## 开发命令

```bash
# 安装开发依赖
uv pip install -e ".[dev]"

# 运行测试
uv run pytest -v

# 代码检查
ruff check src/
ruff format --check src/

# 类型检查
mypy src/

# 本地运行 MCP Server（stdio 模式）
LARK_APP_ID=cli_xxx LARK_APP_SECRET=xxx uv run yuppie-mcp-lark
```

## 架构设计

### 核心模块

- **`server.py`**: MCP Server 入口，FastMCP 注册 10 个工具；启动时从环境变量构造 `LarkClient` 并注入各 tools 模块
- **`utils/config.py`**: `LarkConfig` 数据类，`from_env()` 读取并校验 `LARK_APP_ID`/`LARK_APP_SECRET`/`LARK_BASE_URL`
- **`utils/lark/`**: 飞书客户端（mixin 模式）
  - `base.py` — `_LarkBase`：httpx client、tenant_access_token 自动刷新、`_request`/`_get`/`_post`/`_put`、`_index_to_letter`、90217 限流重试
  - `messages.py` — `MessagesMixin`：消息发送
  - `bitable.py` — `BitableMixin`：多维表格记录搜索
  - `sheets.py` — `SheetsMixin`：电子表格工作表管理与数据读写
  - `__init__.py` — `LarkClient(_LarkBase, MessagesMixin, BitableMixin, SheetsMixin)` 聚合
- **`tools/`**: MCP 工具层（按域分），每个模块持模块级 client 单例 + `set_client()` 注入
  - 每个工具：Pydantic `BaseModel`（`str_strip_whitespace` + `extra="forbid"`）+ `async def` 实现 + markdown 输出 + try/except 友好错误

### 客户端注入流程

`server.py` 启动 → `LarkConfig.from_env()` → `LarkClient(...)` → `messages.set_client(client)` / `bitable.set_client(...)` / `sheets.set_client(...)` → `mcp.run()`。

工具函数被调用时通过 `_get_client()` 拿到 client，调用 mixin 方法，捕获异常返回 markdown 错误信息。

### 传输模式

仅支持 stdio（MCP 主流用法）。`server.py` 直接 `mcp.run()`，不读传输相关环境变量。

## 代码规范

- 使用 `ruff`（line-length = 100）和 `mypy`（strict = true）
- 异步函数 `async def`，底层 httpx 调用本身即异步
- 所有工具参数通过 Pydantic BaseModel 校验
- 工具返回 markdown 字符串；失败时返回 `❌ ...失败：{异常}`

## 添加新工具

1. 在 `utils/lark/<域>.py` 的 mixin 上加飞书 API 薄包装方法
2. 在 `tools/<域>.py` 加 BaseModel + async 实现 + 模块级 `set_client`/`_get_client`
3. 在 `server.py` 用 `@mcp.tool(name=..., annotations=ToolAnnotations(...))` 注册，参数用 `Annotated[type, Field(...)]`
4. 在 `tests/test_tools.py` 加 BaseModel 校验测试
```

- [ ] **Step 3: 重写 `.env.example`**

```bash
# 飞书应用凭证（必填）
LARK_APP_ID=cli_xxxxxxxxxxxxxxxx
LARK_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# API 域名（可选，国际版设为 https://open.larksuite.com）
# LARK_BASE_URL=https://open.feishu.cn
```

- [ ] **Step 4: 更新 `scripts/publish.sh` 中的包名引用**

现有文件只有两处包名引用（第 38 行和第 56 行），都是 `yuppie-mcp-mssql`，需替换为 `yuppie-mcp-lark`：

第 38 行：
```bash
# 改前
echo "  包名: yuppie-mcp-mssql"
# 改后
echo "  包名: yuppie-mcp-lark"
```

第 56 行：
```bash
# 改前
echo -e "${GREEN}查看: https://pypi.org/project/yuppie-mcp-mssql/${NC}"
# 改后
echo -e "${GREEN}查看: https://pypi.org/project/yuppie-mcp-lark/${NC}"
```

执行替换：
```bash
sed -i '' 's/yuppie-mcp-mssql/yuppie-mcp-lark/g' scripts/publish.sh
```

验证：
```bash
grep -c "yuppie-mcp-mssql" scripts/publish.sh
```
Expected: 输出 `0`（无残留旧包名）。

- [ ] **Step 5: 删除已迁移的参考代码**

```bash
rm -f doc/lark_client.py
rmdir doc 2>/dev/null || true
```

- [ ] **Step 6: 验证 README 和 CLAUDE.md 引用的命令可用**

```bash
# 验证 ruff/mypy/pytest 都能跑
uv run ruff check src/
uv run mypy src/
uv run pytest -v
```

Expected: ruff 无错误，mypy 无错误，pytest 全部通过。

- [ ] **Step 7: Commit**

```bash
git add README.md CLAUDE.md .env.example scripts/publish.sh
git rm -f doc/lark_client.py 2>/dev/null || rm -f doc/lark_client.py
git add -A
git commit -m "docs: rewrite README/CLAUDE for lark, update env example and publish script"
```

---

## Task 11: 最终验证

**Files:** 无修改（除非发现问题）

- [ ] **Step 1: 完整测试矩阵**

```bash
uv run pytest -v
uv run ruff check src/
uv run ruff format --check src/
uv run mypy src/
```

Expected: pytest 全通过（30 passed），ruff/mypy 无错误，format check 无 diff。

- [ ] **Step 2: 验证包构建**

```bash
rm -rf dist/ && uv build
ls dist/
```

Expected: `dist/` 下生成 `yuppie_mcp_lark-0.1.0-py3-none-any.whl` 和 `yuppie_mcp_lark-0.1.0.tar.gz`（注意是 `yuppie_mcp_lark` 不是 `yuppie_mcp_mssql`）。

- [ ] **Step 3: 验证 CLI 入口可执行（缺凭据报错路径）**

```bash
unset LARK_APP_ID LARK_APP_SECRET
uv run yuppie-mcp-lark 2>&1 | head -5
```

Expected: 输出包含 `ValueError: 缺少必填环境变量 LARK_APP_ID`（启动即失败，符合预期）。

- [ ] **Step 4: 验证带凭据可启动（连不上飞书也无所谓，只要 token 请求发出即可）**

```bash
export LARK_APP_ID=test
export LARK_APP_SECRET=test
timeout 3 uv run yuppie-mcp-lark 2>&1 | head -20 || true
```

Expected: 进程正常启动，等待 stdio 输入（timeout 3s 后被杀，正常）。

- [ ] **Step 5: 如有问题则修复并 commit，否则跳过**

如果 Step 1-4 任一步发现问题（类型错误、lint 报错、构建失败），修复后：

```bash
git add -A
git commit -m "fix: address final verification findings"
```

如全部通过，本任务无 commit。

---

## 完成检查

改造完成后，仓库应满足：

- [ ] `src/yuppie_mcp_mssql/` 完全消失，`src/yuppie_mcp_lark/` 完整建立
- [ ] `pyproject.toml` 包名是 `yuppie-mcp-lark`，入口 `yuppie-mcp-lark`，依赖含 `httpx`、不含 `python-tds`
- [ ] `doc/lark_client.py` 已删除
- [ ] `tests/` 下有 `test_config.py`/`test_lark_client.py`/`test_tools.py`，全部通过
- [ ] 10 个 MCP 工具注册：`lark_send_message`、`lark_search_records`、`lark_get_spreadsheet_metainfo`、`lark_add_sheet`、`lark_delete_sheet`、`lark_copy_sheet`、`lark_read_range`、`lark_write_range`、`lark_append_data`、`lark_delete_dimension`
- [ ] `README.md` / `CLAUDE.md` / `.env.example` 全部面向 lark
- [ ] `uv build` 产物包名正确
- [ ] 缺 `LARK_APP_ID` 启动时报清晰错误
