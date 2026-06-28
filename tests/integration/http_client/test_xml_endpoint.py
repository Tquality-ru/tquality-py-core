"""Интеграционные тесты XML-разбора ApiResponse на реальном XML-эндпоинте (реальная сеть).

Конкретный эндпоинт - note.xml от w3schools: статичная фикстура, стабильнее
httpbin.org/xml (не зависит от доступности httpbin и не меняет схему).
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

pytest.importorskip("requests")
pytest.importorskip("pydantic_xml")  # требует extra `xml`

import pydantic_xml

from tquality_core.http_client import ApiResponse, BaseClient

pytestmark = pytest.mark.integration

BASE_URL = "https://www.w3schools.com"


class Note(pydantic_xml.BaseXmlModel, tag="note"):
    to: str = pydantic_xml.element()
    # `from` - ключевое слово Python, поэтому поле from_ с явным XML-тегом.
    from_: str = pydantic_xml.element(tag="from")
    heading: str = pydantic_xml.element()
    body: str = pydantic_xml.element()


class NoteXmlClient(BaseClient):
    def __init__(self) -> None:
        super().__init__(BASE_URL)

    def get_note(self) -> ApiResponse[Note]:
        return self._get("/xml/note.xml", Note)


@pytest.fixture(scope="module")
def client(reachable: Callable[[str], None]) -> NoteXmlClient:
    reachable(f"{BASE_URL}/xml/note.xml")
    return NoteXmlClient()


class TestNoteXml:
    def test_xml_body_parsed_into_model(self, client: NoteXmlClient) -> None:
        response = client.get_note()
        assert response.status_code == 200
        assert isinstance(response.data, Note)
        assert response.data.to == "Tove"
        assert response.data.from_ == "Jani"
        assert response.data.heading == "Reminder"
        assert response.data.body == "Don't forget me this weekend!"
