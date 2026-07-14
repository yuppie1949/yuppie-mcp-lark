"""云文档域 MCP 工具"""

from __future__ import annotations

import time

from pydantic import BaseModel, ConfigDict, Field

from ..utils.config import LarkConfig
from ..utils.lark import LarkClient

_client: LarkClient | None = None


def _get_client() -> LarkClient:
    global _client
    if _client is None:
        config = LarkConfig.from_env()
        _client = LarkClient(config.app_id, config.app_secret, config.base_url)
    return _client


class CopyFileInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    file_token: str = Field(..., min_length=1, description="源文件 token")
    name: str = Field(..., min_length=1, max_length=256, description="新文件名称")
    folder_token: str = Field(..., min_length=1, description="目标文件夹 token")
    file_type: str = Field(..., description="源文件类型：file/doc/sheet/bitable/docx")
    user_id_type: str | None = Field(None, description="用户 ID 类型")


async def copy_file(args: CopyFileInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        result = await client.copy_file(
            args.file_token, args.name, args.folder_token, args.file_type,
            user_id_type=args.user_id_type,
        )
        _elapsed = time.time() - _t0
    except Exception as e:
        return f"❌ 复制文件失败：{e}"
    f = result.get("file", {})
    return (
        f"✅ 文件已复制\n\n"
        f"- **耗时**: `{_elapsed:.1f}s`\n"
        f"- **name**: `{f.get('name', '')}`\n"
        f"- **parent_token**: `{f.get('parent_token', '')}`\n"
        f"- **token**: `{f.get('token', '')}`\n"
        f"- **type**: `{f.get('type', '')}`\n"
        f"- **url**: {f.get('url', '')}\n"
    )


class DeleteFileInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    file_token: str = Field(..., min_length=1, description="文件或文件夹 token")
    file_type: str = Field(..., description="文件类型：file/doc/sheet/bitable/docx/folder")


async def delete_file(args: DeleteFileInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        result = await client.delete_file(args.file_token, args.file_type)
        _elapsed = time.time() - _t0
    except Exception as e:
        return f"❌ 删除文件失败：{e}"
    lines = [f"✅ 文件已删除", f"- **file_token**: `{args.file_token}`"]
    lines.append(f"- **耗时**: `{_elapsed:.1f}s`")
    task_id = result.get("task_id", "")
    if task_id:
        lines.append(f"- **task_id**: `{task_id}`（异步任务，可用 drive_check_task 查询）")
    return "\n".join(lines)


class CheckTaskInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    task_id: str = Field(..., min_length=1, description="异步任务 ID")


async def check_task(args: CheckTaskInput) -> str:
    try:
        _t0 = time.time()
        client = _get_client()
        data = await client.check_task(args.task_id)
        _elapsed = time.time() - _t0
    except Exception as e:
        return f"❌ 查询任务状态失败：{e}"
    status = data.get("status", "unknown")
    return (
        f"✅ 任务状态查询完成\n\n"
        f"- **耗时**: `{_elapsed:.1f}s`\n"
        f"- **task_id**: `{args.task_id}`\n"
        f"- **status**: `{status}`\n"
    )