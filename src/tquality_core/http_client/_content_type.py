from enum import StrEnum


class ContentType(StrEnum):
    """Частые MIME-типы для `Content-Type` / `Accept`. Варианты enum - это сами строковые значения заголовка."""

    ANY = "*/*"
    APPLICATION_JSON = "application/json"
    APPLICATION_XML = "application/xml"
    APPLICATION_FORM_URLENCODED = "application/x-www-form-urlencoded"
    APPLICATION_OCTET_STREAM = "application/octet-stream"
    APPLICATION_PDF = "application/pdf"
    MULTIPART_FORM_DATA = "multipart/form-data"
    TEXT_PLAIN = "text/plain"
    TEXT_HTML = "text/html"
    TEXT_CSV = "text/csv"
