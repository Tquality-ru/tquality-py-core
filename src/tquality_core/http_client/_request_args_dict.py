from typing import Any, TypedDict

from requests.cookies import RequestsCookieJar


class RequestArgsDict(TypedDict, total=False):
    params: dict[str, Any] | list[tuple[str, Any]] | bytes | None
    data: Any
    json: Any
    cookies: RequestsCookieJar | dict[str, str] | None
    files: Any
    auth: Any
    timeout: float | tuple[float, float] | None
    allow_redirects: bool
    proxies: dict[str, str] | None
    verify: bool | str
    stream: bool
    cert: str | tuple[str, str] | None
