"""Юнит-тесты BaseClient: сборка запроса и конфигурация сессии (без сети)."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from http import HTTPMethod, HTTPStatus
from typing import Unpack, cast

import pytest

pytest.importorskip("requests")

from pydantic import BaseModel
from requests import Response
from requests.cookies import RequestsCookieJar
from urllib3.util.retry import Retry

from tquality_core.http_client import BaseClient, Headers, RequestArgsDict, TimeoutHTTPAdapter
from tquality_core.services.logger import Logger, set_logger_resolver


class _SpyLogger:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def info(self, message: str, *args: object) -> None:
        self.messages.append(message % args)


class _User(BaseModel):
    id: int


@dataclass
class _Recorded:
    method: object
    url: object
    headers: dict[str, str]
    kwargs: RequestArgsDict


RequestRecorder = Callable[..., list[_Recorded]]


@pytest.fixture
def record_requests(monkeypatch: pytest.MonkeyPatch) -> RequestRecorder:
    """Подменяет Session.request у клиента: записывает вызовы, отдаёт заданное тело."""

    def _attach(client: BaseClient, body: bytes = b"{}", status_code: int = 200) -> list[_Recorded]:
        calls: list[_Recorded] = []
        canned = Response()
        canned._content = body
        canned.status_code = status_code

        def request(
            method: object, url: object, headers: dict[str, str], **kwargs: Unpack[RequestArgsDict]
        ) -> Response:
            calls.append(_Recorded(method=method, url=url, headers=headers, kwargs=kwargs))
            return canned

        monkeypatch.setattr(client._client, "request", request)
        return calls

    return _attach


class TestRequestBuilding:
    def test_get_joins_endpoint_onto_base_url_and_uses_get(self, record_requests: RequestRecorder) -> None:
        client = BaseClient("https://api.test/v1/")
        calls = record_requests(client)
        client._get("users/1")
        assert calls[0].url == "https://api.test/v1/users/1"
        assert calls[0].method == HTTPMethod.GET

    def test_post_uses_post_method(self, record_requests: RequestRecorder) -> None:
        client = BaseClient("https://api.test/v1/")
        calls = record_requests(client)
        client._post("users")
        assert calls[0].method == HTTPMethod.POST

    @pytest.mark.parametrize(
        ("method_name", "expected"),
        [("_put", HTTPMethod.PUT), ("_patch", HTTPMethod.PATCH), ("_delete", HTTPMethod.DELETE)],
    )
    def test_verb_wrappers_dispatch_expected_method(
        self, record_requests: RequestRecorder, method_name: str, expected: HTTPMethod
    ) -> None:
        client = BaseClient("https://api.test/v1/")
        calls = record_requests(client)
        getattr(client, method_name)("users/1")
        assert calls[0].method == expected

    def test_empty_endpoint_targets_base_url(self, record_requests: RequestRecorder) -> None:
        base = "https://api.test/health"
        client = BaseClient(base)
        calls = record_requests(client)
        client._get()
        assert calls[0].url == base

    def test_response_model_drives_data_parsing(self, record_requests: RequestRecorder) -> None:
        client = BaseClient("https://api.test/")
        record_requests(client, body=b'{"id": 5}')
        assert client._get("u", _User).data == _User(id=5)

    def test_headers_model_serialized_per_request(self, record_requests: RequestRecorder) -> None:
        client = BaseClient("https://api.test/")
        calls = record_requests(client)
        token = "Bearer t"
        client._get("u", headers=Headers(authorization=token))
        assert calls[0].headers["Authorization"] == token

    def test_plain_dict_headers_passed_through(self, record_requests: RequestRecorder) -> None:
        client = BaseClient("https://api.test/")
        calls = record_requests(client)
        sent = {"X-Trace-Id": "abc"}
        client._get("u", headers=sent)
        assert calls[0].headers == sent

    def test_absent_headers_send_empty_mapping(self, record_requests: RequestRecorder) -> None:
        client = BaseClient("https://api.test/")
        calls = record_requests(client)
        client._get("u")
        assert calls[0].headers == {}

    def test_extra_request_kwargs_are_forwarded(self, record_requests: RequestRecorder) -> None:
        client = BaseClient("https://api.test/")
        calls = record_requests(client)
        params = {"q": "x"}
        client._get("u", params=params)
        assert calls[0].kwargs["params"] == params


class TestSessionConfiguration:
    def test_persistent_header_model_applied_to_session(self) -> None:
        token = "Bearer t"
        client = BaseClient("https://api.test/", persistent_headers=Headers(authorization=token))
        assert client._client.headers["Authorization"] == token

    def test_persistent_dict_headers_applied_to_session(self) -> None:
        client = BaseClient("https://api.test/", persistent_headers={"X-Env": "stage"})
        assert client._client.headers["X-Env"] == "stage"

    def test_cookies_applied_to_session(self) -> None:
        jar = RequestsCookieJar()
        jar.set("sid", "42")
        client = BaseClient("https://api.test/", cookies=jar)
        assert client._client.cookies is jar

    def test_timeout_adapter_mounted_for_both_schemes(self) -> None:
        client = BaseClient("https://api.test/")
        assert isinstance(client._client.get_adapter("https://x"), TimeoutHTTPAdapter)
        assert isinstance(client._client.get_adapter("http://x"), TimeoutHTTPAdapter)

    def test_adapter_carries_configured_timeout_and_retries(self) -> None:
        timeout, retries = 7.0, 2
        client = BaseClient("https://api.test/", timeout=timeout, retries=retries)
        adapter = client._client.get_adapter("https://x")
        assert isinstance(adapter, TimeoutHTTPAdapter)
        assert adapter._timeout == timeout
        assert isinstance(adapter.max_retries, Retry)
        assert adapter.max_retries.total == retries

    def test_explicit_retry_instance_is_used_as_is(self) -> None:
        retry = Retry(total=5)
        client = BaseClient("https://api.test/", retries=retry)
        adapter = client._client.get_adapter("https://x")
        assert isinstance(adapter, TimeoutHTTPAdapter)
        assert adapter.max_retries is retry

    def test_default_retry_forcelist_includes_retryable_statuses(self) -> None:
        client = BaseClient("https://api.test/")
        adapter = client._client.get_adapter("https://x")
        assert isinstance(adapter, TimeoutHTTPAdapter)
        assert isinstance(adapter.max_retries, Retry)
        forcelist = adapter.max_retries.status_forcelist
        assert forcelist is not None
        assert HTTPStatus.SERVICE_UNAVAILABLE in forcelist
        assert HTTPStatus.TOO_MANY_REQUESTS in forcelist


@pytest.fixture
def step_logger() -> Iterator[_SpyLogger]:
    """Регистрирует резолвер логгера шагов на время теста и снимает после."""
    spy = _SpyLogger()
    set_logger_resolver(lambda: cast(Logger, spy))
    yield spy
    set_logger_resolver(None)


@pytest.fixture
def without_logger_resolver() -> Iterator[None]:
    """Гарантирует отсутствие резолвера (изоляция от глобального состояния)."""
    set_logger_resolver(None)
    yield
    set_logger_resolver(None)


class TestLogging:
    def test_logs_request_and_response_when_logger_wired(self, record_requests: RequestRecorder) -> None:
        spy = _SpyLogger()
        client = BaseClient("https://api.test/", logger=cast(Logger, spy))
        record_requests(client, status_code=204)
        client._get("users/1")
        request_line, response_line = spy.messages
        assert "GET" in request_line and "https://api.test/users/1" in request_line
        assert "204" in response_line  # статус ответа залогирован

    def test_falls_back_to_step_logger_when_none(
        self, record_requests: RequestRecorder, step_logger: _SpyLogger
    ) -> None:
        client = BaseClient("https://api.test/")  # logger=None -> резолвится логгер шагов
        record_requests(client)
        client._get("users/1")
        assert any("GET" in message for message in step_logger.messages)

    def test_silent_when_no_logger_and_no_resolver(
        self, record_requests: RequestRecorder, without_logger_resolver: None
    ) -> None:
        client = BaseClient("https://api.test/")
        record_requests(client)
        client._get("users/1")  # не должно падать и ничего не логирует
