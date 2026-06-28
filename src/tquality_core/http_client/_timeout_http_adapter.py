import typing

from requests import PreparedRequest, Response
from requests.adapters import DEFAULT_POOLBLOCK, DEFAULT_POOLSIZE, DEFAULT_RETRIES, HTTPAdapter
from urllib3.util.retry import Retry

type Timeout = float | tuple[float | None, float | None] | None
"""Таймаут запроса в **секундах**: одно значение либо пара `(connect, read)` (`None` - ждать бесконечно)."""


class TimeoutHTTPAdapter(HTTPAdapter):
    def __init__(
        self,
        pool_connections: int = DEFAULT_POOLSIZE,
        pool_maxsize: int = DEFAULT_POOLSIZE,
        max_retries: int | Retry = DEFAULT_RETRIES,
        pool_block: bool = DEFAULT_POOLBLOCK,
        *,
        timeout: Timeout = None,
    ) -> None:
        self._timeout = timeout
        super().__init__(
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize,
            max_retries=max_retries,
            pool_block=pool_block,
        )

    @typing.override
    def send(
        self,
        request: PreparedRequest,
        stream: bool = False,
        timeout: Timeout = None,
        verify: bool | str = True,
        cert: str | tuple[str, str] | None = None,
        proxies: dict[str, str] | None = None,
    ) -> Response:
        if timeout is None:
            timeout = self._timeout
        return super().send(request, stream=stream, timeout=timeout, verify=verify, cert=cert, proxies=proxies)
