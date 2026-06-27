"""Интеграционные тесты XML-разбора ApiResponse против httpbin.org/xml (реальная сеть)."""

from __future__ import annotations

from collections.abc import Callable

import pytest

pytest.importorskip("requests")
pytest.importorskip("pydantic_xml")  # требует extra `xml`

import pydantic_xml

from tquality_core.http_client import ApiResponse, BaseClient

pytestmark = pytest.mark.integration

BASE_URL = "https://httpbin.org"


class Slide(pydantic_xml.BaseXmlModel, tag="slide"):
    title: str = pydantic_xml.element()


class Slideshow(pydantic_xml.BaseXmlModel, tag="slideshow"):
    title: str = pydantic_xml.attr()
    author: str = pydantic_xml.attr()
    slides: list[Slide] = pydantic_xml.element()


class HttpbinXmlClient(BaseClient):
    def __init__(self) -> None:
        super().__init__(BASE_URL)

    def get_slideshow(self) -> ApiResponse[Slideshow]:
        return self._get("/xml", Slideshow)


@pytest.fixture(scope="module")
def client(reachable: Callable[[str], None]) -> HttpbinXmlClient:
    reachable(f"{BASE_URL}/xml")
    return HttpbinXmlClient()


class TestHttpbinXml:
    def test_xml_body_parsed_into_model(self, client: HttpbinXmlClient) -> None:
        response = client.get_slideshow()
        assert response.status_code == 200
        assert isinstance(response.data, Slideshow)
        assert isinstance(response.data.author, str) and response.data.author
        assert isinstance(response.data.slides, list) and response.data.slides
        assert all(isinstance(slide.title, str) for slide in response.data.slides)
