# Changelog

Формат по [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/), версии по
[семантическому версионированию](https://semver.org/lang/ru/).

## [0.1.17] - 2026-06-21

### Добавлено

- **Утилита метаданных pydantic-моделей** (`tquality_core.utils.pydantic_utils`)
  - имена полей по их alias без создания экземпляра модели, удобно вместо
  захардкоженных строк в тестах и для генерации документации/`.env.example`:
  - `ModelMetadata` (для любого `BaseModel`) - имена при валидации и
    сериализации: `get_validation_alias(lambda s: s.nested.field)` и
    `get_serialization_alias(...)` возвращают `str`, плюс `validation_map()` /
    `serialization_map()` (`{путь-через-точку: имя}`) для массового разбора.
  - `SettingsMetadata` (для `BaseSettings`, наследник `ModelMetadata`) -
    дополнительно имена переменных окружения, которые читает
    `pydantic-settings`: `get_env_alias(lambda s: s.waiter.timeout)` →
    `TEST_WAITER__TIMEOUT` (с учётом `env_prefix`, `env_nested_delimiter`,
    `case_sensitive`, строковых `validation_alias`) и `env_map()`.
  - Поле выбирается селектором-лямбдой: её аргумент типизирован как сама
    модель, поэтому путь даёт автодополнение полей и отлов опечаток в IDE, а
    резолвер возвращает честный `str`. `AliasChoices` сводится к первому
    строковому варианту; `AliasPath` и попадание на вложенную модель (не
    лист) дают понятную ошибку.

## [0.1.16] - 2026-06-17

### Добавлено

- **Computed-style / `blur` / псевдоэлементы в JS-слое** (обобщены из
  inline-скриптов `tquality-py-selenium`, чтобы переиспользовались всеми
  платформами, включая webview в `tquality-py-appium`):
  - `JsElementActions.get_computed_style(name)` - вычисленное значение
    CSS-свойства (пустая строка, если его нет).
  - `JsElementActions.get_computed_styles()` - все вычисленные свойства
    элемента одним запросом (выгоднее, чем дёргать `get_computed_style` в
    цикле, например для snapshot-сравнений).
  - `JsElementActions.blur()` - снять фокус: эмитит `blur` на элементе и
    зовёт `blur()` у `document.activeElement` (с проверкой `HTMLElement`).
  - `JSActions.get_pseudo_element_style(selector, pseudo, name)` - вычисленный
    стиль псевдоэлемента (`::before` и т.п.) у первого элемента под
    `selector`; `None`, если элемент не найден. Аргумент `pseudo` типизирован
    `PseudoElement` (`Literal` из CSS-псевдоэлементов).
  - Скрипты: `element/{get_computed_style,get_computed_styles,blur}.js`,
    `document/get_pseudo_element_style.js`; записи реестров
    `CommonElementJSScripts` / `CommonJSScripts` - покрыты тестами целостности.
- **Блок `logging` в `BaseConfig`** (`LoggingConfig`) - настройки
  обработчиков лога теста, раньше зашитые в `Logger`:
  - `stream` (`LogStream`: `stdout`/`stderr`/`none`) - куда направить
    консольный обработчик или отключить его;
  - `stream_level` / `file_level` (`LogLevelName`) - независимые уровни
    для консольного и файлового обработчиков;
  - `file_enabled` - писать ли `<тест>.log` в `log_dir`.
  `Logger` теперь читает `config.logging`: выбирает поток stdout/stderr,
  выставляет уровни обработчиков и уровень самого логгера (минимум среди
  включённых), `propagate=False`.
- **Вспомогательные файловые каналы лога** - `Logger.add_file_channel(name,
  level)` / `close_file_channel(name)` создают/закрывают отдельный файл
  `<тест>.<name>.log` рядом с основным логом (формат - голое сообщение).
  Используются драйверными пакетами для сырых потоков (например, appium
  device/network логи). Публичные `Logger.log_dir` / `Logger.base_name`.

### Исправлено

- **Screencast-вложение теперь с MIME-типом.** `Step` прикреплял запись через
  `extension=` без `attachment_type`, поэтому allure сохранял вложение без
  типа и в отчёте показывал только скачивание (видео не игралось встроенно;
  скачанный файл проигрывался, т.к. тип угадывала ОС). Теперь передаётся
  `attachment_type` (`MP4` / `WEBM` / `OGG` по `mime_type()` провайдера) -
  отчёт рендерит встроенный плеер.
- **`step(...)` уровня модуля стал ленивым.** Раньше `step("…")` сразу резолвил
  активный `Logger`; при использовании как декоратора тестового метода
  (`@step(...)`) это происходило на импорте, когда теста ещё нет, - `Logger`
  строился с именем `unknown` (т.к. `PYTEST_CURRENT_TEST` не выставлен) и не
  тем экземпляром. Теперь `step` возвращает ленивый объект, резолвящий `Logger`
  на входе в `with` или при вызове обёрнутой функции - на прогоне, с верным
  именем теста. Поведение `with step(...)` и `logger.step(...)` не изменилось.

## [0.1.15] - 2026-06-17

### Добавлено

- **Слой JS-действий.** Базовый сервис `BaseJSActions`
  (`tquality_core.services.base_js_actions`) хранит sync/async executor'ы,
  читает скрипт из `str` (буквальный JS) / `Path` / `Traversable` (ресурс
  пакета) через `_to_source` и исполняет его; подклассы переопределяют
  `_prefix_args`, чтобы подставить неявные аргументы перед пользовательскими.
  - `JSActions` (`tquality_core.services.js_actions`) - page/global-scope:
    13 типизированных методов (alert'ы, открытие вкладок/окон, скроллы,
    `is_page_loaded`, поиск по XPath и точке и т.д.). Дефолты бесконечного
    скролла берёт из блока `waiter` переданного `BaseConfig`.
  - `JsElementActions` (`tquality_core.services.js_element_actions`) -
    element-scope: первым аргументом скрипта подставляет текущий элемент
    (`element_getter`), 21 метод (`click`/`hover`/`set_focus`, `highlight`,
    `set_value`, `set_attribute`, чтение текста/xpath/css/чекбокса/combobox,
    скроллы к элементу, `expand_shadow_root` и др.).
  - **`set_value` - надёжный сеттер:** на JS-стороне берёт нативный сеттер
    `value` с прототипа элемента (обходит переопределение React/Vue), на
    `contenteditable` пишет `textContent`, иначе - запасное присваивание;
    затем эмитит `input` и `change`. Тип элемента определяется в JS - снаружи
    ничего указывать не нужно.
  - **`get_combobox_options`** - тексты всех опций combobox, пара к
    `select_combobox_value_by_text`.
- **Реестры JS-скриптов** `CommonJSScripts` (document/global-scope, 13 записей)
  и `CommonElementJSScripts` (element-scope, 21 запись) в
  `tquality_core.models.assets.js_scripts` - значения это `Traversable`-пути к
  `.js`-файлам, содержимое читается через `.read_text()`.
- **JS-ассеты** в `tquality_core/assets/js_scripts/{document,element}/`
  (13 + 21 файл), портированы из aquality-selenium-dotnet с допиленной
  параметризацией и JSDoc-типами; упаковываются в wheel.
- **Тесты JS-слоя** (`tests/test_js_scripts.py`, `tests/test_base_js_actions.py`):
  целостность реестров (каждый `.js` зарегистрирован и наоборот; каждый
  зарегистрированный скрипт покрыт методом-обёрткой) с негативными тестами на
  срабатывание проверок, и диспетчеризация `execute_script` для своего
  литерала / своего `Path` / async-роутинга / порядка префиксных аргументов.

## [0.1.14] - 2026-06-16

### Изменено

- **`per_test_files` авто-смещает директорию поиска конфигов на директорию
  каждого теста.** Плагин (регистрируется сам через entry-point `pytest11`)
  перед каждым тестом ставит `PathUtils.config_search_dir` = директория теста
  и восстанавливает на teardown. Поэтому `config.json5` / `capabilities.json5`
  рядом с тестом (или выше по дереву) подхватываются автоматически - ближе к
  тесту = выше приоритет - без conftest, env-переменных и ручного `override`.
  Раньше директорию смещали только зарегистрированные rebuilder'ы (DI), а
  инлайн построение конфига в тесте шло от CWD pytest.
- **`PathUtils.use_config_search_dir(path)`** - не-контекст-менеджер вариант
  `override_config_search_dir`: возвращает callable, восстанавливающий прежнее
  значение (для `set` на setup / `reset` на teardown в разных местах).
  `override_config_search_dir` теперь обёртка над ним.

### Примечание для downstream-тестов

- Конфиги рядом с тестом подхватываются сами - в большинстве случаев тесту
  ничего настраивать не нужно (положите `config.json5` в директорию теста).
  Если надо нацелить разрешение на другую директорию, используйте
  параллельно-безопасный `PathUtils.override_config_search_dir(dir)` (на базе
  `ContextVar`, изолирован per-context). **Не** правьте это через
  `monkeypatch`/`os.chdir`: они меняют глобальное состояние и не
  параллельно-безопасны (`--threadpool`).

## [0.1.13] - 2026-06-16

### Исправлено

- **`per_test_files`: teardown rebuilder'ов снова проигрывается в
  `pytest_runtest_teardown`, а не через `item.addfinalizer`.** В 0.1.12
  плагин регистрировал teardown через `item.addfinalizer` прямо в
  `pytest_runtest_setup`, но на этом этапе item ещё не на стеке
  pytest-овского `SetupState` - поэтому `addfinalizer` падал ассертом
  (`node in self.stack`) при первом же зарегистрированном rebuilder'е, то
  есть в любом реальном прогоне с `Services.setup()` (grid/девайс-тесты).
  Возвращён робастный двух-хуковый подход: на setup teardown'ы
  складываются на item, на teardown проигрываются в обратном порядке с
  глушением исключений. Затрагивает downstream `tquality-py-selenium` /
  `tquality-py-appium` (их per-test пересборку конфигов).

## [0.1.12] - 2026-06-16

### Добавлено

- **Пакет `tquality_core.models`** - `config.py` (с `BaseConfig` /
  `WaiterConfig`) и `jsonc_settings_source.py` переехали из корня пакета
  в `tquality_core.models`. Импорты верхнего уровня (`tquality_core`)
  сохранены; внутренние пути сменились на `tquality_core.models.config`
  / `tquality_core.models.jsonc_settings_source` (доступны и как
  `tquality_core.models`).
- **Блок `waiter` в конфиге** - `WaiterConfig` (`tquality_core.models`,
  реэкспортирован на верхний уровень `tquality_core`, добавлен в
  `__all__`) с полями `timeout` (таймаут explicit-wait, сек, `> 0`) и
  `poll_interval` (пауза между опросами условия, сек, `> 0`). `Waiter`
  берёт дефолты `until()` из `config.waiter.timeout` /
  `config.waiter.poll_interval` (раньше - из `config.default_timeout`
  и захардкоженной модульной константы `0.5`). Вложенный блок
  мёржится поля-в-поле по цепочке `config.json5` (deep-merge), а
  под-поля переопределяются env-переменными через
  `env_nested_delimiter="__"` (например, `TEST_WAITER__TIMEOUT`).
- **`BaseConfig.CONFIG_FILENAME`** - имя файла конфига теперь `ClassVar`
  модели (`"config.json5"`), а не модульная константа. Подклассы могут
  переопределить его под свой драйвер; цепочка и `tquality-config init`
  используют `cls.CONFIG_FILENAME`.
- **`tquality_core.utils.path_utils.PathUtils`** - файловые хелперы для
  разрешения конфигов (реэкспортирован на верхний уровень
  `tquality_core`, добавлен в `__all__`).
  - `PathUtils.override_config_search_dir(path)` - контекст-менеджер,
    временно делающий `path` стартовой директорией поиска `config.json5`;
    `None` возвращает к `Path.cwd()`. Тред- и процесс-безопасная замена
    `os.chdir`: значение живёт в `ContextVar`, поэтому каждый поток
    (`--threadpool`) и процесс (`-n` / xdist) видит своё, а конкурентные
    сессии не дерутся за общий CWD. Так per-test пересборка конфигов из
    директории теста делается без смены глобального CWD.
  - `PathUtils.config_search_dir()` - текущая стартовая директория (из
    контекста или `Path.cwd()`).
  - `PathUtils.find_project_root(start=None)` - ближайшая вверх директория
    с любым из `PathUtils.PROJECT_MARKERS` (`pyproject.toml` / `setup.py` /
    `requirements.txt`); `PathUtils.find_workspace_root(start=None)` -
    ближайшая вверх директория с одним из `PathUtils.WORKSPACE_MARKERS`
    (uv: `pyproject.toml` с `[tool.uv.workspace]`; poetry: `pyproject.toml`
    с `[tool.poetry]`; conda: `environment.yml` / `environment.yaml`).
  - `PathUtils.resolve_path_chain(start, filename, stop=None)` - сбор
    `filename` вверх по дереву от `start`. `BaseConfig` строит цепочку
    `config.json5` через него.
  - `PathUtils.find_upwards(start, filename, stop_at=None)` - первый
    `filename` вверх по дереву; останавливается на директории с
    `stop_at`-маркером (по умолчанию - `PROJECT_MARKERS`). Перенесён из
    `per_test_files` (там оставлен реэкспорт для совместимости).
- **`tquality_core.models.jsonc_settings_source.JsoncConfigSettingsSource`**
  - публичный pydantic-settings источник, парсящий jsonc/json5
  (комментарии и висячие запятые). Вынесен из `config.py` (был приватный
  `_JsoncConfigSettingsSource`), реэкспортирован на верхний уровень
  `tquality_core`, добавлен в `__all__` - чтобы дочерние пакеты
  (`tquality-py-selenium`, `tquality-py-appium`) переиспользовали его в
  `settings_customise_sources` своих `*Config`.

### Изменено

- **Цепочка `config.json5` останавливается на границе проекта, а не на
  корне ФС.** Раньше при отсутствии uv-workspace (`find_project_root`
  возвращал `None`) обход поднимался до корня файловой системы и мог
  подхватить чужие `config.json5` из домашней директории и выше. Теперь
  `PathUtils.resolve_path_chain` по умолчанию стопает на корне workspace,
  иначе на корне проекта (ближайшая директория с одним из
  `PathUtils.PROJECT_MARKERS` - `pyproject.toml` / `setup.py` /
  `requirements.txt`), иначе на стартовой директории - до корня ФС обход
  не доходит.
- **Минимальная версия `pydantic-settings` поднята до `>=2.2`** (была
  `>=2.0`). `JsoncConfigSettingsSource` наследует `JsonConfigSettingsSource`,
  который появился только в pydantic-settings 2.2.0 - на `2.0` / `2.1`
  импорт падал. Выявлено прогоном тестов на нижней границе версий.
- **`pytest` - runtime-зависимость (`pytest>=8.0`), а не dev.** Пакет
  поставляет pytest11-плагин (`tquality_core.plugins.per_test_files`),
  поэтому pytest нужен в рантайме. Точечный пин `==9.1.0` снят в пользу
  нижней границы (точный пин в библиотеке диктовал бы потребителю версию
  его собственного тест-раннера); дубликат из `dev` убран.
- **`per_test_files` переехал в пакет `tquality_core.plugins`**
  (`tquality_core.plugins.per_test_files`; pytest11-entry-point и импорты
  верхнего уровня `tquality_core` обновлены, публичные имена не менялись).
- **Плагин `per_test_files` упрощён.** Teardown rebuilder'ов теперь
  регистрируется через нативный `item.addfinalizer` (pytest вызывает их
  в обратном порядке и **поднимает их ошибки**, а не глотает молча) -
  убраны второй хук `pytest_runtest_teardown` и ручное складывание
  teardown'ов в атрибут `item`. Рекомендуемый паттерн rebuilder'а смещает
  поиск через `PathUtils.override_config_search_dir(test_dir)` вместо
  `os.chdir`.
- **JSON-схема конфига генерируется в диалекте JSON Schema draft-07**
  (был draft 2020-12). `generate_schema` выставляет
  `$schema: http://json-schema.org/draft-07/schema#`. Контент схемы не
  использует 2020-12-специфичных конструкций, так что меняется только
  объявленный диалект. Причина: meta-схема draft 2020-12 опирается на
  `$dynamicRef` / `$dynamicAnchor`, который часть IDE (JetBrains)
  резолвят неверно и начинают валидировать значения аннотаций
  (`default`) как подсхемы - отсюда ложные «Required one of: boolean,
  object. Actual: integer» на не-boolean дефолтах. draft-07 не содержит
  `$dynamicRef` и одинаково поддерживается всеми валидаторами; на
  JSON5-конфиги диалект не влияет (инстанс парсится в модель данных до
  валидации). Затрагивает схемы downstream-пакетов
  (`tquality-py-selenium`, `tquality-py-appium`), генерируемых через
  ядро.
- **Подключён ruff** (dev-зависимость `ruff>=0.14.0`, секции
  `[tool.ruff]` / `[tool.ruff.lint]`: `line-length = 120`, правила
  `E`, `W`, `F`, `I`, `N`). Импорты по всему пакету отсортированы под
  ruff isort. `mypy` теперь сканирует весь репозиторий (`files = ["."]`)
  с `exclude` скрытых директорий и `__pycache__` - bare `uv run mypy`
  (как его зовёт pre-commit хук) снова получает цель проверки, а новые
  модули в корне покрываются автоматически.
- **Включён `pydantic.mypy`-плагин** (`plugins = ["pydantic.mypy"]`,
  поставляется с `pydantic`) с секцией `[tool.pydantic-mypy]`:
  `init_forbid_extra = true` и `warn_required_dynamic_aliases = true`.
  Модели наполняются через десериализацию (settings-источники,
  `model_validate`), а не прямыми `__init__`-kwargs, поэтому строгие
  проверки на практике не срабатывают - служат сеткой безопасности на
  опечатки в именах полей при ручном конструировании.

### Удалено

- **Поле верхнего уровня `BaseConfig.default_timeout`** - перенесено в
  блок `waiter` (`waiter.timeout`). Ломающее изменение: в `config.json5`
  / env / конструкторе вместо `default_timeout: 10.0` используйте
  `waiter: { timeout: 10.0 }` (env - `TEST_WAITER__TIMEOUT`).
  Downstream-пакеты (`tquality-py-selenium`, `tquality-py-appium`),
  читавшие `config.default_timeout`, должны перейти на
  `config.waiter.timeout`.
- **`per_test_files.cwd`** - удалён `os.chdir`-контекст-менеджер. Замена -
  тред-безопасный `PathUtils.override_config_search_dir(path)`.

## [0.1.11] - 2026-05-31

### Изменено

- **`_Step` переименован в публичный `Step`** (`tquality_core.services.logger`).
  Класс шага передаётся в step-хуки и доступен через
  `Logger.current_step` / `Logger.active_step_stack`, поэтому стал
  частью публичного API. Добавлены публичные геттеры `Step.title` и
  `Step.level` (раньше доступ был только к приватным `_title` / `_level`).
  Обновлены типизации `StepEnterHook` / `StepExitHook` (`"_Step"` →
  `"Step"`), документация хуков и фабрики `step(...)`. `Step`,
  `StepEnterHook`, `StepExitHook` реэкспортированы на верхний уровень
  `tquality_core` и добавлены в `__all__`.

## [0.1.10] - 2026-05-31

### Добавлено

- **Хуки входа/выхода из шага `Logger`** - `StepEnterHook` и
  `StepExitHook` (`tquality_core.services.logger`, реэкспортированы на
  верхний уровень `tquality_core`).
  - `Logger.register_step_enter_hook(hook)` - колбэк `(step,)`,
    вызывается при входе в любой шаг уже после push в стек (внутри
    `logger.current_step is step`). Возвращает unregister-callable.
  - `Logger.register_step_exit_hook(hook)` - колбэк
    `(step, exc_type, exc_val)`, вызывается при выходе из шага до pop
    из стека; по `exc_type` можно судить, упал ли шаг. Возвращает
    unregister-callable.
  - Исключения внутри хуков логируются как warning и не ломают шаг.
  - **Стек активных шагов** per-`Logger`: свойства `Logger.current_step`
    (innermost активный шаг или `None`) и `Logger.active_step_stack`
    (снимок стека от outermost к innermost). Стек и хуки хранятся
    на экземпляре `Logger`, чтобы параллельные прогоны (свой `Logger`
    на тест) не путали «innermost step» между тестами.

## [0.1.9] - 2026-05-26

### Добавлено

- **`tquality_core.per_test_files`** - pytest-плагин и registration
  API для платформо-агностичной пересборки конфигов под директорию
  каждого теста. Регистрируется автоматически через
  `[project.entry-points.pytest11]` (`tquality_core_per_test_files`).
  - `register_per_test_rebuilder(rebuilder)` - зарегистрировать
    функцию `(test_dir: Path) -> teardown | None`; плагин вызывает её
    перед каждым тестом и (если возвращён teardown-колбэк) - в
    обратном порядке после теста. Регистрация идемпотентна:
    одна и та же функция не добавится дважды.
  - `find_upwards(start, filename, stop_at=("pyproject.toml",))` -
    помощник: поднимается по родительским директориям, возвращает
    первый совпавший путь или `None` при достижении маркера
    workspace.
  - `cwd(path)` - chdir-контекст-менеджер; удобно оборачивать
    конструкторы pydantic-settings, читающие файлы относительно CWD.

  Зачем: `BaseConfig` уже умеет цепочку `config.json5` от CWD к корню
  workspace, но pytest-у безразлично, в какой подпапке тест - CWD
  один на весь процесс. Платформенные интеграции (appium, selenium)
  регистрируют свой rebuilder в `Services.setup()` - он chdir'ит в
  `test_dir`, пересобирает свой типизированный `*Config` и делает
  `.override(...)` на DI-провайдере; teardown откатывает override.
  Тем самым `tests/ios/`, `tests/android/`, `tests/integration/`
  могут иметь свои `config.json5` / `capabilities.json5` без env-
  переменных и явных параметров запуска. Реэкспортированы на
  верхний уровень: `tquality_core.register_per_test_rebuilder`,
  `tquality_core.find_upwards`.

## [0.1.8] - 2026-05-26

### Добавлено

- **`tquality_core.elements.element_state`** - перенесён из
  `tquality-py-appium` (тот же `ElementState` enum: `DISPLAYED`,
  `CLICKABLE`, `EXISTS_IN_ANY_STATE`; те же `StatePredicate` и `StateSpec`
  типы). Семантика общая для appium и selenium; маппинг state →
  `wait.until_*` остаётся в платформенном `BaseElement._await_state(...)`,
  чтобы переиспользовать платформенный `ElementWaiter`. Реэкспортирован
  на верхний уровень `tquality_core`.

## [0.1.7] - 2026-05-26

### Добавлено

- **`tquality_core.services.waiter.Waiter`** - платформо-агностичный
  explicit-waiter с собственным polling-циклом. По умолчанию возвращает
  `bool` на таймаут (не кидает исключение); опционально -
  `raise_on_timeout=True` (поднимает `WaitTimeoutError`) либо
  пользовательский класс (`raise_on_timeout=MyError`). Конфигурируется
  `timeout` / `poll_interval` per-call. Конструктор принимает
  `default_raise_cls` и `ignored_exceptions` - чтобы платформенные пакеты
  могли преднастроить «свой» дефолт (например, selenium-
  `TimeoutException` и `NoSuchElementException`-семейство).
- **`WaitTimeoutError(TimeoutError)`** - дефолтный класс исключения
  для `Waiter.until(raise_on_timeout=True)`.
- **`ResolvedWaiter[T]`** - адаптер, прокидывающий лениво-вычисляемый
  объект (driver, browser, контекст) в condition. Принимает core-`Waiter`
  и `resolver: Callable[[], T]`, разворачивает
  `until(Callable[[T], Any])` → `Waiter.until(Callable[[], Any])`.
  Базовый класс для платформенных `DriverWaiter`.
- **`WebDriverScreenshotProvider`** - реализация
  `ScreenshotProvider`-протокола через
  `driver.get_screenshot_as_png()`. Подходит любому объекту с этим
  методом (selenium-WebDriver, appium-WebDriver, undetected-chromedriver).
- **`WebmScreencastRecorder`** - фоновый рекордер скринкаста: PNG-кадры
  через инжектируемый `frame_source` → склейка в webm/VP9 через
  imageio-ffmpeg. Каждый захваченный кадр повторяется в выходе столько
  output-тиков, сколько нужно для покрытия его реальной длительности
  при заданном `output_fps` (паузы остаются паузами). Зависимости
  (`imageio`, `imageio-ffmpeg`, `numpy`, `Pillow`) импортируются лениво
  внутри `stop()` и подключаются через extra-группу `[screencast]`.
- **`LazyElements[E]`** - платформо-агностичная snapshot-кэширующая
  коллекция типизированных элементов. Перенесена из
  `tquality-py-appium`. Driver инжектится через
  `driver_resolver: Callable[[], Any]`; от объекта требуется только
  метод `find_elements(by, value)` (есть у selenium-WebDriver,
  appium-WebDriver, BrowserService, AppiumDriverService).

### Изменено

- `[project.optional-dependencies]` - добавлена группа `screencast`
  (`imageio>=2.34`, `imageio-ffmpeg>=0.5`, `numpy>=1.26`, `Pillow>=10.0`).
  Установить: `pip install tquality-py-core[screencast]`. Платформенные
  пакеты подключают её через `tquality-py-core[screencast]>=0.1.7`.

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
