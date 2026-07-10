"""Общие фикстуры для юнит-тестов http_client (без сети)."""

from __future__ import annotations

from collections.abc import Callable

import pytest

pytest.importorskip("requests")  # тесты требуют extra `http_client`

from requests import Response

ResponseFactory = Callable[..., Response]


@pytest.fixture
def make_response() -> ResponseFactory:
    """Собирает `requests.Response` с заданным телом и статусом, без сетевого вызова."""

    def _make(content: bytes = b"", status_code: int = 200) -> Response:
        response = Response()
        response._content = content
        response.status_code = status_code
        response.url = "https://api.test/resource"
        return response

    return _make
