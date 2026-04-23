# Руководство для контрибьюторов

## Требования

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) для управления окружением и зависимостями

## Настройка окружения

```bash
uv sync
```

Команда создаст `.venv/` и установит зависимости проекта плюс dev-группу
(mypy и др.).

## Установка git-хуков

Для автоматической проверки типов mypy перед каждым коммитом выполните:

```bash
./scripts/install-hooks.sh
```

Скрипт установит pre-commit хук, который запускает `uv run mypy` и блокирует
коммит при ошибках типов.

## Стиль кода

- Все комментарии, docstring, сообщения логов - на русском языке.
- Не используйте m-тире (длинное тире). Используйте обычное тире или
  переформулируйте.
- Не добавляйте строку `Co-Authored-By` в commit-сообщения.

## Формат commit-сообщений

Каждый коммит начинается с одного или нескольких тегов в квадратных скобках
(на английском), затем краткое описание на русском языке.

### Доступные теги

- `[{module}]` - название затронутого модуля: `[Config]`, `[Logger]`, `[BaseForm]`, `[BaseElement]`, `[StringUtils]`, `[CI]`
- `[Docs]` - изменения документации (README, CONTRIBUTING, docstring'и)
- `[Fix]` - исправление бага без привязки к issue
- `[Fix #{issueId}]` - исправление бага по конкретному issue, например `[Fix #42]`
- `[Style]` - только форматирование, без изменения логики (whitespace, импорты)
- `[Feature]` - новая функциональность

### Примеры

```
[Logger] Имена файлов логов на основе pytest node_id
[Config][Feature] Поддержка config.json на уровне workspace
[Fix #12] Исправлен stale element в type_text
[Docs] Обновлен CONTRIBUTING с процессом релиза
[BaseElement][Style] Упорядочены объявления абстрактных методов
[CI][Fix] Unshallow clone перед push'ем в зеркало
```

Теги можно комбинировать, например `[Config][Feature]` или `[BaseForm][Fix]`.
Теги остаются на английском, чтобы легко фильтровать и автоматизировать.

## Проверка типов

Проект использует `mypy` в strict-режиме. Перед push'ем проверьте:

```bash
uv run mypy
```

Ошибки типов блокируют merge в master.

## Запуск тестов

```bash
uv run pytest -v
```

Тесты запускаются автоматически в CI на каждый MR.

## Обновление JSON-схемы

Схема `schema/config.schema.json` должна совпадать со схемой, генерируемой
из `BaseConfig`. Если вы изменили поля `BaseConfig`, обновите схему:

```bash
uv run tquality-config schema
```

Коммит с изменением `BaseConfig` без обновления схемы провалит тест
`test_committed_schema_matches_base_config` в CI.

## Сборка пакета

```bash
uv build
```

Артефакты появятся в `dist/`.

## Релиз

Версия пакета берется из последнего git-тега вида `vX.Y.Z` через
`hatch-vcs`. В `pyproject.toml` версия не указывается (поле `dynamic`),
поэтому рассинхронизация тега и пакета невозможна.

Ставьте тег **только на master** (после merge соответствующего MR).
`mirror-to-github` публикует на GitHub именно то, что на master, и
проверяет, что коммит тега достижим из master. Тег на feature-ветке
провалит зеркалирование.

```bash
git checkout master
git pull
git tag -a v0.2.0 -m "v0.2.0"
git push origin v0.2.0
```

Push тега `vX.Y.Z` триггерит два CI-джоба в stage `release`:

- **`publish`** - сборка (`uv build` получает версию из тега через
  `hatch-vcs`) и публикация пакета в GitLab Package Registry
  (`https://git.tquality.ru/frameworks/python/tquality-py-core/-/packages`).
- **`mirror-to-github`** - пушит `master` и сам тег в
  https://github.com/Tquality-ru/tquality-py-core (feature-ветки и
  служебные refs не зеркалируются).

### Установка пакета из GitLab Package Registry

```bash
uv pip install tquality-py-core \
  --index-url "https://gitlab-ci-token:${GITLAB_TOKEN}@git.tquality.ru/api/v4/projects/42/packages/pypi/simple"
```

Либо добавьте в `pyproject.toml` консьюмера:

```toml
[[tool.uv.index]]
name = "tquality"
url = "https://git.tquality.ru/api/v4/projects/42/packages/pypi/simple"
explicit = true

[tool.uv.sources]
tquality-py-core = { index = "tquality" }
```

### Настройка зеркалирования (однократно)

1. Создать GitHub Personal Access Token с правами `public_repo` (или `repo`
   для приватных).
2. В GitLab: **Settings → CI/CD → Variables** добавить переменную:
   - Key: `GITHUB_MIRROR_TOKEN`
   - Value: токен с GitHub
   - Protected: yes (только для protected refs, включая теги `v*`)
   - Masked: yes

Для публикации в Package Registry дополнительная настройка не нужна: джоб
использует встроенный `CI_JOB_TOKEN`.

## Структура репозитория

```
tquality-py-core/
├── .gitlab-ci.yml          # CI: mypy + pytest на MR и master
├── pyproject.toml          # конфиг проекта, mypy, зависимости
├── scripts/
│   └── install-hooks.sh    # установка git pre-commit хука
├── schema/
│   └── config.schema.json  # JSON-схема BaseConfig (публикуется через jsDelivr)
├── src/tquality_core/
│   ├── cli.py              # CLI: tquality-config init / schema
│   ├── config.py           # BaseConfig
│   ├── schema.py           # генератор JSON-схемы
│   ├── elements/           # BaseElement (ABC)
│   ├── pages/              # BaseForm
│   ├── services/           # Logger, step, ScreenshotProvider
│   └── utils/              # StringUtils
├── tests/                  # pytest тесты
└── README.md
```
