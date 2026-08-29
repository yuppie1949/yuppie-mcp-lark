"""多维表格快捷操作 mixin — 编排型复合操作"""

from __future__ import annotations

from typing import Any

from .base import _LarkMixinProtocol


class QuickBitableMixin:
    """多维表格快捷操作（通过 MRO 调用 BitableMixin 的方法）"""

    async def bitable_clear(
        self: _LarkMixinProtocol,
        app_token: str,
        table_id: str,
        *,
        filter: dict[str, Any] | None = None,
        sort: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """清空多维表格数据

        分页获取所有记录并批量删除。支持筛选条件，只删除符合条件的数据。
        返回处理报告。

        Args:
            app_token: 多维表格 app_token
            table_id: 数据表 table_id
            filter: 筛选条件（可选），格式同 search_records
            sort: 排序条件（可选），格式同 search_records

        Returns:
            {totalDeleted, failedBatches, batchCount, errors}
        """
        _BATCH = 500

        # ── 第一阶段：分页收集所有 record_id ──
        all_record_ids: list[str] = []
        page_token: str | None = None

        while True:
            result = await self.search_records(
                app_token,
                table_id,
                page_size=_BATCH,
                page_token=page_token,
                filter=filter,
                sort=sort,
                field_names=[],  # 只取 record_id，不返回字段数据
            )
            items = result.get("items", [])
            if not items:
                break

            all_record_ids.extend(item["record_id"] for item in items if item.get("record_id"))

            page_token = result.get("page_token")
            if not page_token:
                break

        total = len(all_record_ids)
        if total == 0:
            return {
                "totalDeleted": 0,
                "failedBatches": 0,
                "batchCount": 0,
                "errors": [],
            }

        # ── 第二阶段：批量删除 ──
        total_deleted = 0
        failed_batches = 0
        batch_count = 0
        errors: list[str] = []

        for i in range(0, total, _BATCH):
            batch_count += 1
            batch_ids = all_record_ids[i : i + _BATCH]

            try:
                await self.batch_delete_records(app_token, table_id, batch_ids)
                total_deleted += len(batch_ids)
            except Exception as e:
                failed_batches += 1
                errors.append(f"批次 {batch_count} 删除失败: {e}")

        return {
            "totalDeleted": total_deleted,
            "failedBatches": failed_batches,
            "batchCount": batch_count,
            "errors": errors,
        }
