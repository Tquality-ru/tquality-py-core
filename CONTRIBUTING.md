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
- Сообщения коммитов - на английском, кратко и по существу.

## Проверка типов

Проект использует `mypy` в strict-режиме. Перед push'ем проверьте:

```bash
uv run mypy
```

Ошибки типов блокируют merge в main.

## Запуск тестов

```bash
uv run pytest -v
```

Тесты запускаются автоматически в CI на каждый MR.

## Сборка пакета

```bash
uv build
```

Артефакты появятся в `dist/`.

## Релиз

Релиз триггерится git-тегом вида `vX.Y.Z`:

```bash
git tag -a v0.2.0 -m "v0.2.0"
git push origin v0.2.0
```

CI-джоб `mirror-to-github` зеркалирует весь репозиторий (все ветки и теги)
в https://github.com/Tquality-ru/tquality-py-core.

### Настройка зеркалирования (однократно)

1. Создать GitHub Personal Access Token с правами `public_repo` (или `repo`
   для приватных).
2. В GitLab: **Settings → CI/CD → Variables** добавить переменную:
   - Key: `GITHUB_MIRROR_TOKEN`
   - Value: токен с GitHub
   - Protected: yes (только для protected refs, включая теги `v*`)
   - Masked: yes

## Структура репозитория

```
tquality-py-core/
├── .gitlab-ci.yml          # CI: mypy + pytest на MR и main
├── pyproject.toml          # конфиг проекта, mypy, зависимости
├── scripts/
│   └── install-hooks.sh    # установка git pre-commit хука
├── src/tquality_core/
│   ├── config.py           # BaseConfig
│   ├── elements/           # BaseElement (ABC)
│   ├── pages/              # BaseForm
│   ├── services/           # Logger, step, ScreenshotProvider
│   └── utils/              # StringUtils
├── tests/                  # pytest тесты
└── README.md
```
