# Changelog

Формат по [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/), версии по
[семантическому версионированию](https://semver.org/lang/ru/).

## [0.1.3] - не выпущено

### Добавлено

- **LogLevel.WITH_SCREENCAST** - новый уровень шага: запускает активную
  screencast-запись на время выполнения и прикрепляет результат к allure.
- **ScreencastProvider** - интерфейс провайдера экранной записи
  (driver-специфичный, реализуется в пакетах-интеграциях).
- `BaseConfig` поля теперь имеют описания и валидацию: `base_url` -
  regex `^https?://\S+$`, `default_timeout > 0`, `log_dir` non-empty,
  всё с человекочитаемыми `description` в JSON-схеме.
- Поддержка **jsonc/json5** в файлах конфигурации: `//` и `/* */`
  комментарии, висячие запятые. Парсер `json5`, для валидного JSON
  семантика не меняется.

### Изменено

- **ScreenshotProvider и ScreencastProvider теперь инжектятся в Logger
  через DI** (аргументы конструктора), а не регистрируются через
  module-level `set_screenshot_provider()`. Оба опциональны - без них
  соответствующие шаги пропускают захват с предупреждением в лог.
- **Файл конфигурации переименован** `config.json` → `config.json5`
  для явного отражения синтаксиса. `CONFIG_FILENAME` обновлён.

### Удалено

- Module-level `set_screenshot_provider()` и `_screenshot_provider` -
  заменены на DI-инъекцию в Logger.

## [0.1.2] - 2026-04-23

### Добавлено

- CI/CD оптимизации: образ `ghcr.io/astral-sh/uv:python3.12-bookworm`
  (uv + python + git из коробки), кеш `.mypy_cache/` и `.pytest_cache/`,
  `interruptible: true` на check-джобах.

## [0.1.1] - 2026-04-23

### Добавлено

- Первый релиз: `BaseConfig`, `Logger`, `BaseForm`, `BaseElement`,
  `Locator`, `StringUtils`, CLI `tquality-config init/schema`.
- Цепочка config.json от cwd до корня workspace с приоритетом
  от специфичного к общему.
- JSON-схема для BaseConfig, публикация через jsDelivr.
- Динамическое версионирование через `hatch-vcs` от git-тегов.
- Публикация в GitLab Package Registry и зеркалирование master+тег
  в GitHub на git-теге `vX.Y.Z`.
