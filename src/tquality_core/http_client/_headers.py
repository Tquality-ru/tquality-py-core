from pydantic import BaseModel, ConfigDict, Field

from tquality_core.http_client._content_type import ContentType


class Headers(BaseModel):
    """Частые заголовки HTTP-запроса.

    Имена полей в snake_case и сериализуются в канонический `Header-Case`
    (напр. `content_type` -> `Content-Type`). Неизвестные заголовки разрешены
    и проходят как есть.
    """

    model_config = ConfigDict(
        # snake_case -> Header-Case. Для заголовков, которым нужен буквальный
        # underscore или особый регистр (напр. "X-API-Key"), задайте явный `Field(alias=...)`.
        alias_generator=lambda field: "-".join(part.capitalize() for part in field.split("_")),
        populate_by_name=True,
        serialize_by_alias=True,
        use_enum_values=True,
        validate_default=True,
        extra="allow",
    )

    # Уходят по умолчанию в каждом запросе.
    accept: ContentType | str = ContentType.APPLICATION_JSON
    accept_encoding: str = "gzip, deflate"
    accept_language: str = "en-US,en;q=0.9"
    content_type: ContentType | str = ContentType.APPLICATION_JSON
    connection: str = "keep-alive"
    user_agent: str = "tquality-py-core"

    # Опциональные — подсказаны в конструкторе для наглядности; в вывод не попадают, пока не заданы.
    authorization: str | None = None
    cache_control: str | None = None
    host: str | None = None
    origin: str | None = None
    referer: str | None = None
    if_none_match: str | None = None
    if_modified_since: str | None = None
    x_requested_with: str | None = None
    x_request_id: str | None = None
    x_api_key: str | None = Field(default=None, alias="X-API-Key")
    x_csrf_token: str | None = Field(default=None, alias="X-CSRF-Token")
    x_ibm_client_id: str | None = Field(default=None, alias="X-IBM-Client-Id")
    x_ibm_client_secret: str | None = Field(default=None, alias="X-IBM-Client-Secret")

    def as_dict(self) -> dict[str, str]:
        """Сериализовать в словарь `{Header-Case: value}`, опуская незаданные опциональные заголовки."""
        return self.model_dump(exclude_none=True)
