from pydantic import AliasChoices, BaseModel
from pydantic.fields import FieldInfo


class _NameProxy:
    """Базовый прокси, повторяющий форму модели и отдающий имена полей.

    Обращение к атрибуту = имя поля модели: для поля-вложенной-модели
    возвращается дочерний прокси того же типа, для обычного поля - его
    разрешённое имя (строка). Неизвестное поле даёт `AttributeError`
    (значит, работает `hasattr`). Подклассы задают разрешение имени листа
    (`_leaf`) и спуск во вложенную модель (`_descend`).
    """

    def __init__(self, model: type[BaseModel]) -> None:
        object.__setattr__(self, "_model", model)

    @staticmethod
    def _validation_name(field: FieldInfo, name: str) -> str:
        """Имя, по которому поле читается при валидации (с учётом alias)."""
        va = field.validation_alias
        if va is None:
            return name
        if isinstance(va, str):
            return va
        if isinstance(va, AliasChoices):
            for choice in va.choices:
                if isinstance(choice, str):
                    return choice
        raise ValueError(
            f"field {name!r} uses a {type(va).__name__} validation alias with no "
            f"plain-string choice; it cannot be represented as a single name"
        )

    @staticmethod
    def _model_of(field: FieldInfo) -> type[BaseModel] | None:
        ann = field.annotation
        return ann if isinstance(ann, type) and issubclass(ann, BaseModel) else None

    def _leaf(self, field: FieldInfo, name: str) -> str:
        raise NotImplementedError

    def _descend(self, submodel: type[BaseModel], field: FieldInfo, name: str) -> "_NameProxy":
        raise NotImplementedError

    def __getattr__(self, name: str) -> "str | _NameProxy":
        model = object.__getattribute__(self, "_model")
        try:
            field = model.model_fields[name]
        except KeyError:
            raise AttributeError(name) from None
        sub = _NameProxy._model_of(field)
        if sub is not None:
            return self._descend(sub, field, name)
        return self._leaf(field, name)

    def collect(self, prefix: str = "") -> dict[str, str]:
        """Развернуть прокси в `{путь_поля_через_точку: имя}`.

        Рекурсивно обходит поля-вложенные-модели, соединяя имена полей
        точкой (`waiter.timeout`). Значения листьев - разрешённые имена.
        """
        model = object.__getattribute__(self, "_model")
        out: dict[str, str] = {}
        for name in model.model_fields:
            value = getattr(self, name)
            path = f"{prefix}{name}"
            if isinstance(value, _NameProxy):
                out.update(value.collect(f"{path}."))
            else:
                out[path] = value
        return out
