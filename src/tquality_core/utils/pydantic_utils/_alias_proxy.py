from typing import Literal

from pydantic import BaseModel
from pydantic.fields import FieldInfo

from tquality_core.utils.pydantic_utils._name_proxy import _NameProxy

_Kind = Literal["validation", "serialization"]


class _AliasProxy(_NameProxy):
    """Имена полей по их alias - для валидации или сериализации.

    `validation` отдаёт имя, по которому поле читается на входе (строковый
    `validation_alias`, иначе имя поля); `serialization` - ключ, под которым
    поле попадает в `model_dump(by_alias=True)` (`serialization_alias`, иначе
    имя поля). Вложенные модели остаются вложенными (без склейки, как у env).
    """

    def __init__(self, model: type[BaseModel], kind: _Kind) -> None:
        super().__init__(model)
        object.__setattr__(self, "_kind", kind)

    def _descend(self, submodel: type[BaseModel], field: FieldInfo, name: str) -> '_AliasProxy':
        return _AliasProxy(submodel, object.__getattribute__(self, "_kind"))

    def _leaf(self, field: FieldInfo, name: str) -> str:
        if object.__getattribute__(self, "_kind") == "validation":
            return _NameProxy._validation_name(field, name)
        return field.serialization_alias or name
