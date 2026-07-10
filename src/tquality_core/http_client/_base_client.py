from http import HTTPMethod, HTTPStatus
from types import NoneType
from typing import Unpack
from urllib.parse import urljoin

import requests
from requests.cookies import RequestsCookieJar
from urllib3.util.retry import Retry

from tquality_core.http_client._headers import Headers
from tquality_core.http_client._request_args_dict import RequestArgsDict
from tquality_core.http_client._response import ApiResponse, ModelType
from tquality_core.http_client._timeout_http_adapter import Timeout, TimeoutHTTPAdapter
from tquality_core.services.logger import Logger, step


class BaseClient:
    _DEFAULT_BACKOFF_FACTOR: float = 0.5
    _RETRY_STATUS_FORCELIST: tuple[HTTPStatus, ...] = (
        HTTPStatus.TOO_MANY_REQUESTS,
        HTTPStatus.INTERNAL_SERVER_ERROR,
        HTTPStatus.BAD_GATEWAY,
        HTTPStatus.SERVICE_UNAVAILABLE,
        HTTPStatus.GATEWAY_TIMEOUT,
    )

    def __init__(
        self,
        base_url: str,
        persistent_headers: Headers | dict[str, str] | None = None,
        cookies: RequestsCookieJar | None = None,
        timeout: Timeout = 30.0,
        retries: int | Retry = 3,
        logger: Logger | None = None,
    ):
        self._client = requests.Session()
        self._base_url = base_url
        self._logger = logger
        if persistent_headers is None:
            persistent_headers = Headers()
        if isinstance(persistent_headers, Headers):
            self._client.headers.update(persistent_headers.as_dict())
        elif isinstance(persistent_headers, dict):
            self._client.headers.update(persistent_headers)
        if cookies is not None:
            self._client.cookies = cookies
        retry = (
            retries
            if isinstance(retries, Retry)
            else Retry(
                total=retries,
                backoff_factor=self._DEFAULT_BACKOFF_FACTOR,
                status_forcelist=self._RETRY_STATUS_FORCELIST,
            )
        )
        adapter = TimeoutHTTPAdapter(timeout=timeout, max_retries=retry)
        self._client.mount("http://", adapter)
        self._client.mount("https://", adapter)

    def _request[T](
        self,
        method: HTTPMethod,
        endpoint: str = "",
        response_model: ModelType[T] = NoneType,
        headers: dict[str, str] | Headers | None = None,
        **kwargs: Unpack[RequestArgsDict],
    ) -> ApiResponse[T]:
        headers = headers if isinstance(headers, dict) else headers.as_dict() if isinstance(headers, Headers) else {}
        url = urljoin(self._base_url, endpoint)
        self._log("→ %s %s", method, url)
        response = self._client.request(method, url, headers=headers, **kwargs)
        self._log("← %s %s [%s] %.0f ms", method, url, response.status_code, response.elapsed.total_seconds() * 1000)
        return ApiResponse.from_response(response, response_model)

    def _log(self, message: str, *args: object) -> None:
        """Логирует через подключённый Logger; если он не задан — через активный
        логгер шагов (если резолвер настроен); иначе no-op. Заголовки и тело
        намеренно не пишем, чтобы не утекали токены/секреты."""
        logger = self._logger or step.current()
        if logger is not None:
            logger.info(message, *args)

    def _get[T](
        self,
        endpoint: str = "",
        response_model: ModelType[T] = NoneType,
        headers: dict[str, str] | Headers | None = None,
        **kwargs: Unpack[RequestArgsDict],
    ) -> ApiResponse[T]:
        return self._request(HTTPMethod.GET, endpoint, response_model, headers=headers, **kwargs)

    def _post[T](
        self,
        endpoint: str = "",
        response_model: ModelType[T] = NoneType,
        headers: dict[str, str] | Headers | None = None,
        **kwargs: Unpack[RequestArgsDict],
    ) -> ApiResponse[T]:
        return self._request(HTTPMethod.POST, endpoint, response_model, headers=headers, **kwargs)

    def _put[T](
        self,
        endpoint: str = "",
        response_model: ModelType[T] = NoneType,
        headers: dict[str, str] | Headers | None = None,
        **kwargs: Unpack[RequestArgsDict],
    ) -> ApiResponse[T]:
        return self._request(HTTPMethod.PUT, endpoint, response_model, headers=headers, **kwargs)

    def _patch[T](
        self,
        endpoint: str = "",
        response_model: ModelType[T] = NoneType,
        headers: dict[str, str] | Headers | None = None,
        **kwargs: Unpack[RequestArgsDict],
    ) -> ApiResponse[T]:
        return self._request(HTTPMethod.PATCH, endpoint, response_model, headers=headers, **kwargs)

    def _delete[T](
        self,
        endpoint: str = "",
        response_model: ModelType[T] = NoneType,
        headers: dict[str, str] | Headers | None = None,
        **kwargs: Unpack[RequestArgsDict],
    ) -> ApiResponse[T]:
        return self._request(HTTPMethod.DELETE, endpoint, response_model, headers=headers, **kwargs)
