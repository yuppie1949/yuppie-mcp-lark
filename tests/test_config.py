"""LarkConfig 环境变量读取与校验测试"""

import pytest

from yuppie_mcp_lark.utils.config import DEFAULT_BASE_URL, LarkConfig


def test_from_env_requires_app_id(monkeypatch):
    monkeypatch.setenv("LARK_APP_ID", "")
    monkeypatch.setenv("LARK_APP_SECRET", "secret")
    with pytest.raises(ValueError, match="LARK_APP_ID"):
        LarkConfig.from_env()


def test_from_env_requires_app_secret(monkeypatch):
    monkeypatch.setenv("LARK_APP_ID", "id")
    monkeypatch.setenv("LARK_APP_SECRET", "")
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
