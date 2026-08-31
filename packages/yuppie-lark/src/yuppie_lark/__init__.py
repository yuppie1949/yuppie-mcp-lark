"""yuppie-lark: 飞书 OpenAPI 客户端库

对外只暴露 LarkClient 一个类。token、http client 由 _LarkBase 统一管理，
各业务域方法分散在独立模块便于维护。LarkConfig 一并 re-export，
用户 `from yuppie_lark import LarkClient, LarkConfig` 一步到位。
"""

from __future__ import annotations

from .base import _LarkBase
from .bitable import BitableMixin
from .bitable_quick import QuickBitableMixin
from .config import LarkConfig
from .drive import DriveMixin
from .messages import MessagesMixin
from .sheets import SheetsMixin
from .sheets_quick import QuickSheetsMixin
from .webhook import WebhookMixin

__version__ = "0.3.0"

__all__ = ["LarkClient", "LarkConfig"]


class LarkClient(
    _LarkBase,
    MessagesMixin,
    WebhookMixin,
    BitableMixin,
    QuickBitableMixin,
    DriveMixin,
    SheetsMixin,
    QuickSheetsMixin,
):
    """飞书 OpenAPI 客户端"""

    pass
