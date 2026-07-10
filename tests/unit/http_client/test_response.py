"""Юнит-тесты ApiResponse: ленивый разбор тела, кэш, потокобезопасность, семантика None."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable

import pytest
from pydantic import BaseModel, ValidationError, model_validator
from requests import Response

from tquality_core.http_client import ApiResponse

ResponseFactory = Callable[..., Response]


class _User(BaseModel):
    id: int
    name: str


class _Error(BaseModel):
    error: str


class TestParsing:
    def test_validates_json_body_into_model(self, make_response: ResponseFactory) -> None:
        user = _User(id=1, name="Ann")
        parsed = ApiResponse.from_response(make_response(user.model_dump_json().encode()), _User).data
        assert parsed == user

    def test_without_model_data_is_none(self, make_response: ResponseFactory) -> None:
        assert ApiResponse.from_response(make_response(b'{"id": 1, "name": "x"}')).data is None

    def test_union_routes_body_to_matching_member(self, make_response: ResponseFactory) -> None:
        error = _Error(error="boom")
        parsed = ApiResponse.from_response(make_response(error.model_dump_json().encode()), _User | _Error).data
        assert parsed == error

    def test_required_model_with_empty_body_raises(self, make_response: ResponseFactory) -> None:
        with pytest.raises(ValidationError):
            _ = ApiResponse.from_response(make_response(b""), _User).data

    def test_optional_model_with_empty_body_is_none(self, make_response: ResponseFactory) -> None:
        assert ApiResponse.from_response(make_response(b""), _User | None).data is None


class TestCaching:
    def test_body_parsed_once_then_cached(self, make_response: ResponseFactory) -> None:
        validations = 0

        class _Counted(BaseModel):
            id: int

            @model_validator(mode="after")
            def _bump(self) -> _Counted:
                nonlocal validations
                validations += 1
                return self

        response = ApiResponse.from_response(make_response(b'{"id": 1}'), _Counted)
        assert response.data is response.data  # второй доступ берёт кэш
        assert validations == 1


class TestThreadSafety:
    def test_concurrent_access_parses_once(self, make_response: ResponseFactory) -> None:
        validations = 0

        class _Slow(BaseModel):
            id: int

            @model_validator(mode="after")
            def _bump(self) -> _Slow:
                nonlocal validations
                validations += 1
                time.sleep(0.02)  # расширяем окно гонки
                return self

        response = ApiResponse.from_response(make_response(b'{"id": 1}'), _Slow)
        results: list[_Slow] = []
        worker_count = 16
        barrier = threading.Barrier(worker_count)

        def worker() -> None:
            barrier.wait()  # стартуем одновременно
            results.append(response.data)

        threads = [threading.Thread(target=worker) for _ in range(worker_count)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert validations == 1
        assert all(item is results[0] for item in results)


class TestFromResponse:
    def test_reclasses_in_place_preserving_response_state(self, make_response: ResponseFactory) -> None:
        status = 201
        original = make_response(b'{"id": 1, "name": "x"}', status_code=status)
        result = ApiResponse.from_response(original, _User)
        assert result is original  # переклассификация на месте, без копии
        assert isinstance(original, ApiResponse)
        assert original.status_code == status  # состояние Response не затёрто
