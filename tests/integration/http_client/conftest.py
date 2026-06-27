"""Фикстуры интеграционных тестов http_client (реальная сеть)."""

from __future__ import annotations

from collections.abc import Callable

import pytest

pytest.importorskip("requests")  # требует extra `http_client`

import requests


@pytest.fixture(scope="session")
def reachable() -> Callable[[str], None]:
    """Пропускает тест, если URL недоступен (нет сети / сервис недоступен)."""

    def _check(url: str) -> None:
        try:
            requests.get(url, timeout=10)
        except requests.RequestException as exc:
            pytest.skip(f"нет доступа к {url}: {exc}")

    return _check
