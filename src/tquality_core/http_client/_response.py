from __future__ import annotations

import enum
import threading
from types import NoneType, UnionType
from typing import Any, Literal, cast

from pydantic import TypeAdapter
from requests import Response

_BaseXmlModel: type | None = None  # заполняется, когда установлен опциональный extra `xml`
try:
    from pydantic_xml import BaseXmlModel as _BaseXmlModel
except ImportError:
    pass

type ModelType[T] = type[T | None] | UnionType
"""Конкретный класс модели (`type[T]`) или union-форма (`A | B | None`), в которую валидируется тело ответа."""


class _Sentinel(enum.Enum):
    UNSET = enum.auto()


class ApiResponse[T](Response):
    _data: T | Literal[_Sentinel.UNSET] = _Sentinel.UNSET
    _data_type: ModelType[T]
    _lock: threading.Lock

    def __init__(self, model_type: ModelType[T] = NoneType):
        super().__init__()
        self._data_type = model_type
        self._lock = threading.Lock()

    @classmethod
    def from_response(cls, response: Response, model_type: ModelType[T] = NoneType) -> ApiResponse[T]:
        response.__class__ = cls
        typed = cast("ApiResponse[T]", response)
        typed._data_type = model_type
        typed._lock = threading.Lock()
        return typed

    @property
    def data(self) -> T:
        if self._data is _Sentinel.UNSET and self._data_type is not NoneType:
            with self._lock:
                if self._data is _Sentinel.UNSET:
                    self._data = cast(T, self._parse_body())
        if self._data is _Sentinel.UNSET:
            return cast(T, None)
        return self._data

    def _parse_body(self) -> object:
        model_type = self._data_type
        if _BaseXmlModel is not None and isinstance(model_type, type) and issubclass(model_type, _BaseXmlModel):
            return cast(Any, model_type).from_xml(self.content)
        json = self.json() if self.content else None
        return TypeAdapter(model_type).validate_python(json)
