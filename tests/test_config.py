"""Тесты для BaseConfig."""
from __future__ import annotations

from tquality_core import BaseConfig


def test_defaults() -> None:
    cfg = BaseConfig()
    assert cfg.base_url == "http://localhost"
    assert cfg.default_timeout == 10.0
    assert cfg.log_dir == "logs"
    assert cfg.highlight_elements is False


def test_constructor_overrides_defaults() -> None:
    cfg = BaseConfig(base_url="https://example.com", default_timeout=5.0)
    assert cfg.base_url == "https://example.com"
    assert cfg.default_timeout == 5.0


def test_subclass_adds_fields() -> None:
    class MyConfig(BaseConfig):
        custom_field: str = "default-value"

    cfg = MyConfig()
    assert cfg.custom_field == "default-value"
    assert cfg.base_url == "http://localhost"
