"""飞书 MCP Server 配置：从环境变量读取并校验"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

DEFAULT_BASE_URL = "https://open.feishu.cn"

load_dotenv()


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
