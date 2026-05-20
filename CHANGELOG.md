# Changelog

Формат по [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/), версии по
[семантическому версионированию](https://semver.org/lang/ru/).

## [0.1.6] - 2026-05-20

### Добавлено

- **`tquality_core.utils.xpath_utils.XPathUtils`** - driver-agnostic
  хелперы для XPath-строк: `normalize(value)` (приведение `.`/`./foo`/
  `foo` к форме, безопасной для конкатенации с родительским локатором)
  и `literal(value)` (квотирование значений в xpath-предикатах с
  обработкой встроенных кавычек через `concat(...)`). Вынесено из
  `tquality_selenium.utils.locator_utils` для переиспользования
  драйверными пакетами (`tquality-py-selenium`, `tquality-py-appium`).
- **`tquality_core.utils.os_utils.OSUtils`** - driver-agnostic проверки
  текущей платформы: `is_macos()`, `is_windows()`, `is_linux()`,
  `current_platform()`. Вынесено из `tquality_selenium.utils.os_utils`;
  карты поддержки конкретных драйверов остаются в драйверных пакетах.
- **`tquality_core.schema.build_schema_url(package_name, repo_owner,
  repo_name)`** и **`resolve_ref(package_name)`** - публичные хелперы
  для построения схема-URL по версии любого пакета. Драйверные пакеты
  переиспользуют их вместо дублирования логики `_resolve_ref`.
- **`tquality_core.cli.build_cli(prog, description, config_cls,
  schema_url)`** - фабрика `main`-функции CLI. Драйверные пакеты
  собирают свой `tquality-<driver>-config` одной строкой вместо
  копирования argparse-плиты.
- `generate_schema(config_cls, *, schema_url=None)` и
  `write_schema_file(path, config_cls, *, schema_url=None)` принимают
  необязательный `schema_url` - для подстановки URL драйверного пакета.

### Изменено

- **`$schema` в генерируемых JSON-схемах**: `draft-07` →
  `draft/2020-12`. Pydantic 2 эмитит 2020-12-features (`$defs`,
  `prefixItems`), указание устаревшего диалекта вводило валидаторы
  в заблуждение. Файл `schema/config.schema.json` перегенерирован.

## [0.1.5] - 2026-05-06

### Добавлено

- **Двуязычный README**: основной `README.md` переведён на
  английский (для PyPI и GitHub), русская версия вынесена в
  `README.ru.md`. В шапке обоих файлов - переключатель языков.
- `README.ru.md` включён в sdist (`tool.hatch.build.targets.sdist`),
  чтобы попадал в опубликованный пакет.

### Изменено

- `_find_project_root`: явная кодировка `utf-8` при чтении
  `pyproject.toml` - не зависит от локальной кодировки ОС.

## [0.1.4] - 2026-05-05

### Добавлено

- **Публикация в публичный PyPI**: метаданные пакета (`readme`,
  `keywords`, `classifiers`, `project.urls`) приведены к виду,
  ожидаемому PyPI. Установка стала однострочной:
  `pip install tquality-py-core` / `uv add tquality-py-core`.
- CI-джоба **`publish-pypi`** загружает пакет на https://pypi.org
  на git-теге `vX.Y.Z`. Требует переменную `PYPI_TOKEN` в
  настройках CI/CD (protected, masked). GitLab Package Registry
  остаётся как внутреннее зеркало.

### Изменено

- README: PyPI обозначен основным источником установки;
  установка через GitHub-зеркало по тегу осталась как альтернатива
  для проверки невыпущенных коммитов.

## [0.1.3] - 2026-04-24

### Добавлено

- Поддержка **jsonc/json5** в файлах конфигурации: `//` и `/* */`
  комментарии, висячие запятые. Парсер `json5`, для валидного JSON
  семантика не меняется.
- **Динамический `SCHEMA_URL`**: вычисляется из установленной версии
  пакета. Релизная сборка → `@vX.Y.Z`, dev/editable (`+g...`, `.dev`)
  → `@master`. `tquality-config init` на релизной установке запекает
  в `config.json5` пин на тег - схема стабильна между релизами.

### Изменено

- **Файл конфигурации переименован** `config.json` → `config.json5`
  для явного отражения синтаксиса. `CONFIG_FILENAME` обновлён.

## [0.1.2] - 2026-04-23

### Добавлено

- **LogLevel.WITH_SCREENCAST** - новый уровень шага: запускает активную
  screencast-запись на время выполнения и прикрепляет результат к allure.
- **ScreencastProvider** - интерфейс провайдера экранной записи
  (driver-специфичный, реализуется в пакетах-интеграциях).
- `BaseConfig` поля теперь имеют описания и валидацию: `base_url` -
  regex `^https?://\S+$`, `default_timeout > 0`, `log_dir` non-empty,
  всё с человекочитаемыми `description` в JSON-схеме.
- CI/CD оптимизации: образ `ghcr.io/astral-sh/uv:python3.12-bookworm`
  (uv + python + git из коробки), кеш `.mypy_cache/` и `.pytest_cache/`,
  `interruptible: true` на check-джобах.

### Изменено

- **ScreenshotProvider и ScreencastProvider теперь инжектятся в Logger
  через DI** (аргументы конструктора), а не регистрируются через
  module-level `set_screenshot_provider()`. Оба опциональны - без них
  соответствующие шаги пропускают захват с предупреждением в лог.

### Удалено

- Module-level `set_screenshot_provider()` и `_screenshot_provider` -
  заменены на DI-инъекцию в Logger.

## [0.1.1] - 2026-04-23

### Добавлено

- Первый релиз: `BaseConfig`, `Logger`, `BaseForm`, `BaseElement`,
  `Locator`, `StringUtils`, CLI `tquality-config init/schema`.
- Цепочка `config.json` от cwd до корня workspace с приоритетом
  от специфичного к общему.
- JSON-схема для BaseConfig, публикация через jsDelivr.
- Динамическое версионирование через `hatch-vcs` от git-тегов.
- Публикация в GitLab Package Registry и зеркалирование master+тег
  в GitHub на git-теге `vX.Y.Z`.
