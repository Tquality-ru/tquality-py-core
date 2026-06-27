from pydantic import BaseModel, ConfigDict, Field

from tquality_core.http_client._content_type import ContentType


class Headers(BaseModel):
    """Common HTTP request headers.

    Field names are snake_case and serialize to canonical `Header-Case` names
    (e.g. `content_type` -> `Content-Type`). Unknown headers are allowed and pass through verbatim.
    """

    model_config = ConfigDict(
        # snake_case -> Header-Case. Override with an explicit `Field(alias=...)` for headers
        # that need a literal underscore or specific casing (e.g. "X-API-Key").
        alias_generator=lambda field: "-".join(part.capitalize() for part in field.split("_")),
        populate_by_name=True,
        serialize_by_alias=True,
        use_enum_values=True,
        validate_default=True,
        extra="allow",
    )

    # Sent by default on every request.
    accept: ContentType | str = ContentType.APPLICATION_JSON
    accept_encoding: str = "gzip, deflate"
    accept_language: str = "en-US,en;q=0.9"
    content_type: ContentType | str = ContentType.APPLICATION_JSON
    connection: str = "keep-alive"
    user_agent: str = "tquality-py-core"

    # Optional — suggested at construction for discoverability; omitted from output unless set.
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
        """Serialize to a `{Header-Case: value}` dict, omitting unset optional headers."""
        return self.model_dump(exclude_none=True)
