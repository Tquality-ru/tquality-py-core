"""Юнит-тесты XML-разбора ApiResponse (extra `xml`).

Модели объявлены на уровне модуля: pydantic-xml инициализирует сериализатор
вложенных моделей только для полностью определённых классов (локальные классы
с вложением дают «partially initialized»). Весь модуль пропускается без extra.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

pytest.importorskip("requests")
pytest.importorskip("pydantic_xml")

import pydantic_xml
from requests import Response

from tquality_core.http_client import ApiResponse

ResponseFactory = Callable[..., Response]

_NSMAP = {"c": "http://example.com/catalog"}


class _Order(pydantic_xml.BaseXmlModel, tag="order"):
    id: int = pydantic_xml.element()


class _BaseExampleComModel(pydantic_xml.BaseXmlModel, ns="c", nsmap=_NSMAP):
    """Общая база с пространством имён `c`; наследники задают только `tag`
    (поля наследуют `ns`, отдельный `ns=` на `element()` не нужен)."""


class _Book(_BaseExampleComModel, tag="book"):
    title: str = pydantic_xml.element()


class _Catalog(_BaseExampleComModel, tag="catalog"):
    books: list[_Book] = pydantic_xml.element()


class TestXml:
    def test_flat_xml_model_parsed_from_response_bytes(self, make_response: ResponseFactory) -> None:
        order_id = 7
        parsed = ApiResponse.from_response(make_response(f"<order><id>{order_id}</id></order>".encode()), _Order).data
        assert isinstance(parsed, _Order)
        assert parsed.id == order_id

    def test_namespaced_xml_with_root_element_parsed(self, make_response: ResponseFactory) -> None:
        body = (
            b'<c:catalog xmlns:c="http://example.com/catalog">'
            b"<c:book><c:title>Dune</c:title></c:book>"
            b"<c:book><c:title>Hyperion</c:title></c:book>"
            b"</c:catalog>"
        )
        parsed = ApiResponse.from_response(make_response(body), _Catalog).data
        assert isinstance(parsed, _Catalog)
        # пространство имён корня и вложенных элементов разрешено, порядок сохранён
        assert [book.title for book in parsed.books] == ["Dune", "Hyperion"]
