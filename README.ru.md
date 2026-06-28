# tquality-py-core

[![PyPI](https://img.shields.io/pypi/v/tquality-py-core)](https://pypi.org/project/tquality-py-core/)
[![License](https://img.shields.io/pypi/l/tquality-py-core)](https://github.com/Tquality-ru/tquality-py-core/blob/master/LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-Tquality--ru%2Ftquality--py--core-blue?logo=github)](https://github.com/Tquality-ru/tquality-py-core)

**Языки:** [English](README.md) · **Русский**

Независимое от драйвера ядро для автоматизации тестирования tquality. Предоставляет
основу, на которой строятся пакеты, специфичные для драйверов (Selenium,
Appium, WinAppDriver).

## Компоненты

- **`BaseConfig`** - конфигурация на основе pydantic-settings с загрузкой из
  `config.json5` (с поддержкой комментариев и висячих запятых через json5),
  переменных окружения и dotenv. Для добавления полей, специфичных для
  драйвера, используется наследование.
- **`Logger`, `LogLevel`, `step`** - журналирование в контексте одного теста
  с интеграцией allure. Уровни шагов: `NORMAL`, `CRITICAL` (снимок экрана в
  конце) и `WITH_SCREENCAST` (видеозапись шага через подключаемый поставщик).
- **`BaseForm`** - базовый класс для страниц и форм (страница - форма с полным
  контекстом).
- **`BaseElement`** - абстрактный интерфейс, который реализуют элементы,
  специфичные для драйвера.
- **`FormattableElement[E]`** - шаблонный элемент с локатором-шаблоном
  (placeholder'ы в синтаксисе `str.format`); `.format(*args, **kwargs)`
  подставляет аргументы в `value` локатора и возвращает готовый
  конкретный элемент `E`.
- **`StringUtils`** - вспомогательные функции разбора строк.
- **`http_client`** *(опционально - extra `http_client`)* - типизированный
  HTTP-клиент поверх `requests` + `pydantic`: `BaseClient` (обёртка над
  `requests.Session` с заголовками, cookies, таймаутом и ретраями на уровне
  клиента) и `ApiResponse[T]`, чьё ленивое потокобезопасное свойство `.data`
  валидирует тело ответа в pydantic-модель. XML-тела - через extra `xml`.
  См. [HTTP-клиент](#http-клиент-опционально).

## Не входит в ядро

- Конкретная интеграция с драйверами (Selenium, Appium, WinAppDriver) -
  живёт в отдельных пакетах, зависящих от этого ядра.
- Типы элементов (`Button`, `Input`, `Label` и т. п.) - реализации,
  специфичные для драйвера, живут рядом с интеграцией драйвера.
- Настройка контейнера внедрения зависимостей - каждый использующий пакет
  собирает свой контейнер через `dependency-injector`, регистрируя службы
  ядра и службы, специфичные для драйвера.

## Контракт интеграции

Использующие пакеты должны:

1. Наследовать `BaseConfig` с полями, специфичными для драйвера.
2. Зарегистрировать функцию получения `Logger` через
   `set_logger_resolver(lambda: YourServices.logger())`, где `YourServices` -
   контейнер использующего пакета. Это нужно, чтобы `step()` из ядра
   находил активный `Logger` в любом модуле.
3. При необходимости реализовать `ScreenshotProvider` / `ScreencastProvider`
   и внедрить их в `Logger` через контейнер, чтобы шаги уровня `CRITICAL`
   прикрепляли снимки экрана, а `WITH_SCREENCAST` - видеозапись (конкретный
   формат - на стороне поставщика, например webm в Selenium) к отчёту
   allure. Без поставщиков шаги проходят с предупреждением в журнал.
4. Предоставить конкретные подклассы `BaseElement` с логикой поиска и
   ожидания.

## Требования

- Python 3.12+

## Установка

Пакет публикуется в [публичный PyPI](https://pypi.org/project/tquality-py-core/).
Это рекомендуемый способ установки для всех потребителей:

```bash
pip install tquality-py-core
```

Или в `pyproject.toml`:

```toml
dependencies = [
    "tquality-py-core>=0.1.5",
]
```

### Альтернатива: установка из GitHub-зеркала

Если нужна сборка из исходников (например, для проверки коммита,
ещё не вышедшего в релиз), пакет также доступен из публичного
GitHub-зеркала по тегу:

```toml
dependencies = [
    "tquality-py-core @ git+https://github.com/Tquality-ru/tquality-py-core.git@v0.1.5",
]
```

Прямые git-ссылки требуют `[tool.hatch.metadata] allow-direct-references = true` у потребителя.

### Опциональные extras

Ядро работает само по себе; эти extras добавляют опциональные компоненты и
их зависимости:

- **`http_client`** - типизированный HTTP-клиент (`tquality_core.http_client`);
  тянет `requests`, `urllib3`.
- **`xml`** - разбор XML-ответов для HTTP-клиента; тянет `pydantic-xml`
  (и `http_client`).
- **`screencast`** - видеозапись шагов; тянет `imageio`, `imageio-ffmpeg`,
  `numpy`, `Pillow`.

```bash
pip install "tquality-py-core[http_client]"
pip install "tquality-py-core[xml]"          # http_client + поддержка XML
```

## CLI

После установки доступна команда `tquality-config`:

```bash
tquality-config init        # сгенерировать config.json5 со значениями по умолчанию
tquality-config schema      # сгенерировать schema/config.schema.json (для контрибьюторов)
```

Сгенерированный `config.json5` включает ссылку на JSON-схему, опубликованную
через jsDelivr. Адрес автоматически привязан к версии пакета: при установке
выпущенной версии (`0.1.3`) → `@v0.1.3`, при установке невыпущенной версии
(`+g...`, `.dev`) → `@master`:

```jsonc
{
    "$schema": "https://cdn.jsdelivr.net/gh/Tquality-ru/tquality-py-core@v0.1.3/schema/config.schema.json",
    // Комментарии поддерживаются - можно пояснить выбор значения.
    "base_url": "http://localhost",
    "waiter": {
        "timeout": 10.0,       // таймаут explicit-wait, секунды
        "poll_interval": 0.5,  // пауза между опросами условия, секунды
    },
    "log_dir": "logs",
    "highlight_elements": false,
}
```

Редакторы с поддержкой JSON Schema (VS Code, JetBrains IDE) автоматически
подсказывают доступные поля и проверяют значения. Синтаксис jsonc/json5
позволяет оставлять комментарии `//` и `/* */` и висячие запятые.

## HTTP-клиент (опционально)

Установите с extra `http_client`, затем наследуйте `BaseClient` и опишите
типизированные эндпоинты. `ApiResponse[T].data` лениво валидирует тело ответа
в вашу pydantic-модель:

```python
from pydantic import BaseModel
from tquality_core.http_client import ApiResponse, BaseClient, ContentType, Headers


class User(BaseModel):
    id: int
    name: str


class ExampleApi(BaseClient):
    def __init__(self, token: str) -> None:
        super().__init__(
            "https://api.example.com",
            persistent_headers=Headers(
                authorization=f"Bearer {token}",
                content_type=ContentType.APPLICATION_JSON,
            ),
            timeout=30,   # секунды; также ретраит 429/5xx через urllib3 Retry
        )

    def get_user(self, user_id: int) -> ApiResponse[User]:
        return self._get(f"/users/{user_id}", User)


user = ExampleApi(token).get_user(1).data   # -> User (валидно); бросает при некорректном теле
```

- **Тип `.data` - ровно `T`.** `None` появляется, только если он явно в модели
  (`User | None`) или модель не передана. Обязательная модель при пустом или
  некорректном теле бросает `pydantic.ValidationError`.
- **`Headers`** сериализует snake_case-поля в канонический `Header-Case`
  (`content_type` → `Content-Type`), пропускает неизвестные заголовки как есть
  и подсказывает частые заголовки в конструкторе (`authorization`, `x_api_key`,
  `x_ibm_client_id`, …).
- **XML API:** установите extra `xml` и используйте модель ответа -
  наследника `pydantic_xml.BaseXmlModel`; тело разбирается из XML-байтов
  автоматически вместо JSON.

Методы запроса `BaseClient` (`_get`/`_post`/`_request`) защищённые: выносите
осмысленные методы-эндпоинты в подкласс, а не зовите их из тестов напрямую.

## Разработка

См. [CONTRIBUTING.md](CONTRIBUTING.md) для инструкций по настройке окружения
разработчика, установке перехватчиков git и проверке типов ty.

## История версий

См. [CHANGELOG.md](CHANGELOG.md). Описание CI/CD - в
[CONTRIBUTING.md](CONTRIBUTING.md).

## Назначение

Отделяет универсальные шаблоны (журналирование, объекты страниц, загрузка
конфигурации) от кода, специфичного для драйвера. Appium и WinAppDriver
повторно используют ту же модель объектов страниц, отчётность по шагам и
конвейер конфигурации без обязательной зависимости от Selenium.
