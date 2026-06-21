from collections.abc import Callable
from functools import reduce
from typing import Any, cast

from pydantic import BaseModel

from tquality_core.utils.pydantic_utils._alias_proxy import _AliasProxy
from tquality_core.utils.pydantic_utils._field_ref import _Ref
from tquality_core.utils.pydantic_utils._name_proxy import _NameProxy


class ModelMetadata[T]:
    """Метаданные pydantic-модели (`BaseModel`): имена полей по alias.

    Оборачивает класс модели и даёт доступ к именам полей при валидации и
    сериализации без создания экземпляра. Имя берётся через селектор-лямбду:
    её аргумент статически типизирован как сама модель (`T`), поэтому путь
    `lambda s: s.nested.field` даёт автодополнение полей и отлов опечаток, а
    `get_validation_alias(...)` / `get_serialization_alias(...)` возвращают
    честный `str`. Массовый разбор - через `*_map()`-методы (`dict[str, str]`).

    Для `BaseSettings` берите `SettingsMetadata`: к alias-именам она добавляет
    имена переменных окружения (`get_env_alias`, `env_map`).
    """

    _m: type[T]

    def __init__(self, model_type: type[T]):
        """Принять класс-наследник `BaseModel`.

        Поднимает `TypeError`, если переданный объект не является подклассом
        `BaseModel`.
        """
        if not (isinstance(model_type, type) and issubclass(model_type, BaseModel)):
            raise TypeError(f"{model_type!r} is not a BaseModel subclass")
        self._m = model_type

    @property
    def _model(self) -> type[BaseModel]:
        return cast(type[BaseModel], self._m)

    @staticmethod
    def _resolve(proxy: _NameProxy, selector: Callable[[T], Any]) -> str:
        path = _Ref.path_of(selector(cast(T, _Ref())))
        name = reduce(getattr, path, proxy)
        if not isinstance(name, str):
            raise TypeError(f"{'.'.join(path)!r} points at a nested model, not a leaf field")
        return name

    def get_validation_alias(self, selector: Callable[[T], Any]) -> str:
        """Имя поля при валидации (входной alias) для выбранного поля.

        Строковый `validation_alias`, иначе имя поля (для `AliasChoices` -
        первый строковый вариант).
        """
        return self._resolve(_AliasProxy(self._model, "validation"), selector)

    def get_serialization_alias(self, selector: Callable[[T], Any]) -> str:
        """Имя поля при сериализации (выходной alias) для выбранного поля.

        Ключ, под которым поле попадает в `model_dump(by_alias=True)`:
        `serialization_alias`, иначе имя поля.
        """
        return self._resolve(_AliasProxy(self._model, "serialization"), selector)

    def validation_map(self) -> dict[str, str]:
        """Сопоставить каждое поле с его именем при валидации: `{путь: имя}`.

        Рекурсивно обходит вложенные модели, соединяя имена полей точкой.
        Удобно для документирования принимаемых ключей входных данных.
        """
        return _AliasProxy(self._model, "validation").collect()

    def serialization_map(self) -> dict[str, str]:
        """Сопоставить каждое поле с его именем при сериализации: `{путь: имя}`.

        Рекурсивно обходит вложенные модели, соединяя имена полей точкой.
        Удобно для документирования ключей `model_dump(by_alias=True)`.
        """
        return _AliasProxy(self._model, "serialization").collect()
