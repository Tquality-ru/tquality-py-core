"""Интеграционные тесты BaseClient/ApiResponse на реальном JSON-эндпоинте (реальная сеть).

Конкретный эндпоинт - jsonplaceholder.typicode.com.
"""
from __future__ import annotations

from collections.abc import Callable

import pytest

pytest.importorskip("requests")

from pydantic import BaseModel, ConfigDict, Field

from tquality_core.http_client import ApiResponse, BaseClient

pytestmark = pytest.mark.integration

BASE_URL = "https://jsonplaceholder.typicode.com"


class Todo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_id: int = Field(alias="userId")
    id: int
    title: str
    completed: bool


class CreatedPost(BaseModel):
    id: int


class JsonPlaceholderClient(BaseClient):
    def __init__(self) -> None:
        super().__init__(BASE_URL)

    def get_todo(self, todo_id: int) -> ApiResponse[Todo]:
        return self._get(f"/todos/{todo_id}", Todo)

    def create_post(self, title: str, body: str, user_id: int) -> ApiResponse[CreatedPost]:
        return self._post("/posts", CreatedPost, json={"title": title, "body": body, "userId": user_id})


@pytest.fixture(scope="module")
def client(reachable: Callable[[str], None]) -> JsonPlaceholderClient:
    reachable(f"{BASE_URL}/todos/1")
    return JsonPlaceholderClient()


class TestJsonPlaceholder:
    def test_get_todo_returns_typed_model(self, client: JsonPlaceholderClient) -> None:
        todo_id = 1
        response = client.get_todo(todo_id)
        assert response.status_code == 200
        assert response.data.id == todo_id  # сервер вернул запрошенный ресурс
        assert isinstance(response.data.title, str)

    def test_create_post_returns_201_with_generated_id(self, client: JsonPlaceholderClient) -> None:
        response = client.create_post(title="t", body="b", user_id=1)
        assert response.status_code == 201  # реальная семантика создания ресурса
        assert isinstance(response.data.id, int)
