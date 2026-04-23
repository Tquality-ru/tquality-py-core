# tquality-py-core

Драйвер-независимое ядро для автоматизации тестирования tquality. Предоставляет
основу, на которой строятся пакеты, специфичные для драйверов (Selenium,
Appium, WinAppDriver).

## Что входит

- **BaseConfig** - конфигурация на базе pydantic-settings с разрешением из
  JSON/env/dotenv. Наследуйте для добавления полей, специфичных для драйвера.
- **Logger, LogLevel, step** - логирование в контексте одного теста с
  интеграцией allure. CRITICAL шаги прикрепляют скриншоты через подключаемый
  провайдер.
- **BaseForm** - базовый класс для страниц и форм (page = форма с полным
  контекстом).
- **BaseElement** - абстрактный интерфейс, который реализуют элементы,
  специфичные для драйвера.
- **StringUtils** - вспомогательные функции парсинга строк.

## Что НЕ входит

- Конкретная интеграция с драйверами (Selenium, Appium, WinAppDriver) -
  живет в отдельных пакетах, зависящих от этого ядра.
- Типы элементов (Button, Input, Label и т.д.) - реализации, специфичные для
  драйвера, живут рядом с интеграцией драйвера.
- Настройка DI-контейнера - каждый использующий проект собирает свой
  контейнер через `dependency-injector`, регистрируя сервисы ядра и
  специфичные для драйвера сервисы.

## Контракт интеграции

Использующие пакеты должны:

1. Наследовать `BaseConfig` с полями, специфичными для драйвера.
2. Зарегистрировать резолвер Logger через `set_logger_resolver(lambda: Container.logger())`.
3. Опционально реализовать `ScreenshotProvider` / `ScreencastProvider`
   и инжектить их в `Logger` через DI-контейнер, чтобы шаги уровня
   `CRITICAL` прикрепляли скриншоты, а `WITH_SCREENCAST` - GIF-запись
   экрана к allure-отчету. Без провайдеров шаги проходят с warning в лог.
4. Предоставить конкретные подклассы `BaseElement` с логикой поиска и ожидания.

## Требования

- Python 3.12+

## Установка

```
uv pip install tquality-py-core
```

## CLI

После установки доступна команда `tquality-config`:

```bash
tquality-config init        # сгенерировать config.json со значениями по умолчанию
tquality-config schema      # сгенерировать schema/config.schema.json (для мейнтейнеров)
```

Сгенерированный `config.json` включает ссылку на JSON-схему, опубликованную
через jsDelivr:

```json
{
    "$schema": "https://cdn.jsdelivr.net/gh/Tquality-ru/tquality-py-core@master/schema/config.schema.json",
    "base_url": "http://localhost",
    "default_timeout": 10.0,
    "log_dir": "logs",
    "highlight_elements": false
}
```

Редакторы с поддержкой JSON Schema (VS Code, JetBrains IDE) автоматически
подсказывают доступные поля и валидируют значения.

## Разработка

См. [CONTRIBUTING.md](CONTRIBUTING.md) для инструкций по настройке окружения
разработчика, установке git-хуков и проверке типов mypy.

## CI/CD

GitLab CI запускает две проверки на каждом MR и на master:

- **mypy** - strict-режим проверки типов
- **tests** - запуск pytest с JUnit-отчетом

При публикации git-тега вида `vX.Y.Z` джоб `mirror-to-github` зеркалирует
репозиторий в https://github.com/Tquality-ru/tquality-py-core.

## Зачем это существует

Отделяет универсальные паттерны (логирование, page object'ы, загрузка
конфигурации) от кода, специфичного для драйвера. Appium и WinAppDriver
переиспользуют ту же модель page object'ов, отчетность по шагам и пайплайн
конфигурации без необходимости тянуть Selenium.
