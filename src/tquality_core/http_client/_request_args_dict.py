from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypedDict

if TYPE_CHECKING:
    from collections.abc import Mapping
    from http.cookiejar import CookieJar

    from requests._types import (
        AuthType,
        CertType,
        DataType,
        FilesType,
        JsonType,
        ParamsType,
        TimeoutType,
        VerifyType,
    )
    from requests.cookies import RequestsCookieJar


class RequestArgsDict(TypedDict, total=False):
    """Типизированные `**kwargs` запроса (без `headers` — это отдельный параметр клиента).

    Типы полей совпадают с тем, что принимает `Session.request` (см. `requests._types`).
    """

    params: ParamsType | Mapping[str, Any]
    data: DataType
    json: JsonType
    cookies: RequestsCookieJar | CookieJar | dict[str, str] | None
    files: FilesType
    auth: AuthType
    timeout: TimeoutType
    allow_redirects: bool
    proxies: dict[str, str] | None
    verify: VerifyType | None
    stream: bool | None
    cert: CertType
