"""LarkClient — 通过 mixin 聚合消息、多维表格、电子表格能力

对外只暴露 LarkClient 一个类。token、http client 由 _LarkBase 统一管理，
各业务域方法分散在独立模块便于维护。
"""

from __future__ import annotations

from .base import _LarkBase
from .bitable import BitableMixin
from .messages import MessagesMixin
from .sheets import SheetsMixin
from .sheets_quick import QuickSheetsMixin

__all__ = ["LarkClient"]


class LarkClient(_LarkBase, MessagesMixin, BitableMixin, SheetsMixin, QuickSheetsMixin):
    """飞书 OpenAPI 客户端"""

    pass
