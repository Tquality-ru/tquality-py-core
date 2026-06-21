from pydantic import BaseModel
from pydantic.fields import FieldInfo
from pydantic_settings import SettingsConfigDict

from tquality_core.utils.pydantic_utils._name_proxy import _NameProxy


class _EnvProxy(_NameProxy):
    """Имена переменных окружения, читаемых `pydantic-settings`.

    Лист поля = `env_prefix` + имя валидации, склеенное через
    `env_nested_delimiter` для вложенных моделей, приведённое к верхнему
    регистру при `case_sensitive=False`. Строковый `validation_alias` на
    верхнем уровне заменяет префикс целиком (так делает `pydantic-settings`).
    """

    def __init__(self, model: type[BaseModel], cfg: SettingsConfigDict, prefix: str | None = None) -> None:
        super().__init__(model)
        is_top = prefix is None  # None => top level
        if is_top:
            prefix = cfg.get("env_prefix", "")  # seed prefix from config
        for k, v in dict(_cfg=cfg, _prefix=prefix, _top=is_top).items():
            object.__setattr__(self, k, v)

    def _full(self, field: FieldInfo, name: str) -> str:
        prefix = object.__getattribute__(self, "_prefix")
        top = object.__getattribute__(self, "_top")
        seg = _NameProxy._validation_name(field, name)
        return seg if (top and seg != name) else prefix + seg

    def _descend(self, submodel: type[BaseModel], field: FieldInfo, name: str) -> '_EnvProxy':
        cfg = object.__getattribute__(self, "_cfg")
        delim = cfg.get("env_nested_delimiter", "")
        if not delim:
            raise ValueError(f"{name!r} is a nested model but env_nested_delimiter is not set")
        return _EnvProxy(submodel, cfg, prefix=self._full(field, name) + delim)

    def _leaf(self, field: FieldInfo, name: str) -> str:
        cfg = object.__getattribute__(self, "_cfg")
        full = self._full(field, name)
        return full if cfg.get("case_sensitive", False) else full.upper()
