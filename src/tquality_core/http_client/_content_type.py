from enum import StrEnum


class ContentType(StrEnum):
    """Common `Content-Type` / `Accept` MIME types. Members are the literal header strings."""

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
