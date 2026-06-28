"""Типизированный HTTP-клиент на `requests` + `pydantic`.

Опциональный компонент — ставится через extra `http_client`:

    pip install "tquality-py-core[http_client]"

Тянет `requests` и `urllib3`; импорт подпакета без extra поднимает `ModuleNotFoundError`.

Публичный API — здесь; модули с префиксом `_` - приватная реализация.
"""

from tquality_core.http_client._base_client import BaseClient
from tquality_core.http_client._content_type import ContentType
from tquality_core.http_client._headers import Headers
from tquality_core.http_client._request_args_dict import RequestArgsDict
from tquality_core.http_client._response import ApiResponse, ModelType
from tquality_core.http_client._timeout_http_adapter import Timeout, TimeoutHTTPAdapter

__all__ = [
    "ApiResponse",
    "BaseClient",
    "ContentType",
    "Headers",
    "ModelType",
    "RequestArgsDict",
    "Timeout",
    "TimeoutHTTPAdapter",
]
