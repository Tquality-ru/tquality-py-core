"""Typed HTTP client built on `requests` + `pydantic`.

Optional component — install with the `http_client` extra:

    pip install "tquality-py-core[http_client]"

It pulls in `requests` and `urllib3`; importing this subpackage without the extra raises `ModuleNotFoundError`.

The public API lives here; the underscore-prefixed modules are private implementation detail.
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
