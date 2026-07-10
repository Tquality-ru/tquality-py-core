from collections.abc import Callable
from typing import Any, cast

from pydantic_settings import BaseSettings

from tquality_core.utils.pydantic_utils._env_proxy import _EnvProxy
from tquality_core.utils.pydantic_utils._model_metadata import ModelMetadata


class SettingsMetadata[T](ModelMetadata[T]):
    """Метаданные модели настроек (`BaseSettings`).

    Расширяет `ModelMetadata`: к alias-именам валидации/сериализации добавляет
    имена переменных окружения, которые читает `pydantic-settings`
    (`get_env_alias`, `env_map`), с учётом `env_prefix`,
    `env_nested_delimiter`, `case_sensitive` и строковых `validation_alias`.
    """

    def __init__(self, model_type: type[T]):
        """Принять класс-наследник `BaseSettings`.

        Поднимает `TypeError`, если переданный объект не является подклассом
        `BaseSettings`.
        """
        super().__init__(model_type)
        if not issubclass(model_type, BaseSettings):
            raise TypeError(f"{model_type!r} is not a BaseSettings subclass")

    def _env(self) -> _EnvProxy:
        settings = cast(type[BaseSettings], self._m)
        return _EnvProxy(settings, settings.model_config)

    def get_env_alias(self, selector: Callable[[T], Any]) -> str:
        """Имя переменной окружения для поля, выбранного селектором.

        Например, `get_env_alias(lambda s: s.waiter.timeout)` →
        `TEST_WAITER__TIMEOUT`.
        """
        return self._resolve(self._env(), selector)

    def env_map(self) -> dict[str, str]:
        """Сопоставить каждое поле с именем переменной окружения: `{путь: ENV_NAME}`.

        Рекурсивно обходит вложенные модели, соединяя имена полей через точку
        (например, `waiter.timeout` → `TEST_WAITER__TIMEOUT`). Удобно для
        генерации `.env.example`, документирования переопределяемых настроек
        или проверки, что env-файл ссылается только на известные переменные.
        """
        return self._env().collect()
