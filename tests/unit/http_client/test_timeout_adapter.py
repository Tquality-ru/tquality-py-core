"""Юнит-тесты TimeoutHTTPAdapter: подстановка таймаута по умолчанию."""

from __future__ import annotations

import pytest

pytest.importorskip("requests")

from requests import PreparedRequest, Request, Response
from requests.adapters import HTTPAdapter

from tquality_core.http_client import TimeoutHTTPAdapter


@pytest.fixture
def prepared_request() -> PreparedRequest:
    return Request(method="GET", url="https://api.test/").prepare()


@pytest.fixture
def captured_timeout(monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    """Перехватывает таймаут, с которым адаптер вызывает базовый `HTTPAdapter.send`."""
    captured: dict[str, object] = {}

    def fake_send(self: HTTPAdapter, request: PreparedRequest, **kwargs: object) -> Response:
        captured["timeout"] = kwargs.get("timeout")
        return Response()

    monkeypatch.setattr(HTTPAdapter, "send", fake_send)
    return captured


class TestTimeoutHTTPAdapter:
    def test_default_timeout_applied_when_request_omits_it(
        self, prepared_request: PreparedRequest, captured_timeout: dict[str, object]
    ) -> None:
        default = 7.5
        TimeoutHTTPAdapter(timeout=default).send(prepared_request, timeout=None)
        assert captured_timeout["timeout"] == default

    def test_explicit_request_timeout_is_preserved(
        self, prepared_request: PreparedRequest, captured_timeout: dict[str, object]
    ) -> None:
        explicit = 1.0
        TimeoutHTTPAdapter(timeout=99.0).send(prepared_request, timeout=explicit)
        assert captured_timeout["timeout"] == explicit
