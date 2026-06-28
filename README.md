# tquality-py-core

[![PyPI](https://img.shields.io/pypi/v/tquality-py-core)](https://pypi.org/project/tquality-py-core/)
[![License](https://img.shields.io/pypi/l/tquality-py-core)](https://github.com/Tquality-ru/tquality-py-core/blob/master/LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-Tquality--ru%2Ftquality--py--core-blue?logo=github)](https://github.com/Tquality-ru/tquality-py-core)

**Languages:** **English** · [Русский](README.ru.md)

Driver-agnostic core for the tquality test automation framework. Provides
the foundation that driver-specific packages (Selenium, Appium,
WinAppDriver) build on.

## Components

- **`BaseConfig`** — pydantic-settings configuration that loads from
  `config.json5` (with comment and trailing-comma support via json5),
  environment variables and dotenv files. Subclass it to add
  driver-specific fields.
- **`Logger`, `LogLevel`, `step`** — per-test logging with allure
  integration. Step levels: `NORMAL`, `CRITICAL` (screenshot at the
  end), `WITH_SCREENCAST` (step video via a pluggable provider).
- **`BaseForm`** — base class for pages and forms (a page is just a
  form with the full context).
- **`BaseElement`** — abstract interface implemented by driver-specific
  element types.
- **`FormattableElement[E]`** — a template element holding a locator with
  `str.format` placeholders; `.format(*args, **kwargs)` fills the locator
  `value` and returns a ready-to-use concrete element `E`.
- **`StringUtils`** — string-parsing helpers.
- **`http_client`** *(optional — extra `http_client`)* — typed HTTP client on
  top of `requests` + `pydantic`: `BaseClient` (a `requests.Session` wrapper
  with client-level headers, cookies, timeout and retries) and `ApiResponse[T]`
  whose lazy, thread-safe `.data` validates the response body into a pydantic
  model. XML bodies via the `xml` extra. See [HTTP client](#http-client-optional).

## Out of scope

- Concrete driver integrations (Selenium, Appium, WinAppDriver) — live
  in separate packages that depend on this core.
- Element types (`Button`, `Input`, `Label`, etc.) — driver-specific
  implementations sit alongside the corresponding driver integration.
- DI container wiring — every consumer assembles its own container via
  `dependency-injector`, registering both core services and
  driver-specific services.

## Integration contract

Consumer packages must:

1. Subclass `BaseConfig` with driver-specific fields.
2. Register a `Logger` resolver via
   `set_logger_resolver(lambda: YourServices.logger())`, where
   `YourServices` is the consumer package's container. This lets
   `step()` from the core find the active `Logger` from any module.
3. Where needed, implement `ScreenshotProvider` / `ScreencastProvider`
   and inject them into `Logger` through the container, so that
   `CRITICAL` steps attach screenshots and `WITH_SCREENCAST` steps
   attach a recording (the concrete format is up to the provider — for
   example webm in Selenium) to the allure report. Without providers
   the steps still pass, but with a warning in the log.
4. Provide concrete `BaseElement` subclasses with their own lookup and
   wait logic.

## Requirements

- Python 3.12+

## Installation

The package is published to [public PyPI](https://pypi.org/project/tquality-py-core/).
This is the recommended installation path for all consumers:

```bash
pip install tquality-py-core
```

Or in `pyproject.toml`:

```toml
dependencies = [
    "tquality-py-core>=0.1.5",
]
```

### Alternative: install from the GitHub mirror

For a source build (e.g., to verify a commit that has not yet been
released), the package is also available by git tag from the public
GitHub mirror:

```toml
dependencies = [
    "tquality-py-core @ git+https://github.com/Tquality-ru/tquality-py-core.git@v0.1.5",
]
```

Direct git references require `[tool.hatch.metadata] allow-direct-references = true` on the consumer's side.

### Optional extras

The core is usable as-is; these extras add optional components and their
dependencies:

- **`http_client`** — typed HTTP client (`tquality_core.http_client`); pulls
  in `requests`, `urllib3`.
- **`xml`** — XML response parsing for the HTTP client; pulls in
  `pydantic-xml` (and `http_client`).
- **`screencast`** — step video recording; pulls in `imageio`,
  `imageio-ffmpeg`, `numpy`, `Pillow`.

```bash
pip install "tquality-py-core[http_client]"
pip install "tquality-py-core[xml]"          # http_client + XML support
```

## CLI

After installation the `tquality-config` command is available:

```bash
tquality-config init        # generate config.json5 with default values
tquality-config schema      # generate schema/config.schema.json (for maintainers)
```

The generated `config.json5` includes a reference to the JSON Schema
published via jsDelivr. The address is automatically pinned to the
package version: a released install (`0.1.3`) → `@v0.1.3`; an
unreleased install (`+g...`, `.dev`) → `@master`:

```jsonc
{
    "$schema": "https://cdn.jsdelivr.net/gh/Tquality-ru/tquality-py-core@v0.1.3/schema/config.schema.json",
    // Comments are supported — useful to explain the chosen value.
    "base_url": "http://localhost",
    "waiter": {
        "timeout": 10.0,       // explicit-wait timeout, seconds
        "poll_interval": 0.5,  // pause between condition polls, seconds
    },
    "log_dir": "logs",
    "highlight_elements": false,
}
```

Editors with JSON Schema support (VS Code, JetBrains IDEs) autocomplete
the available fields and validate values. The jsonc/json5 syntax allows
`//` and `/* */` comments and trailing commas.

## HTTP client (optional)

Install with the `http_client` extra, then subclass `BaseClient` and declare
typed endpoints. `ApiResponse[T].data` lazily validates the response body into
your pydantic model:

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
            timeout=30,   # seconds; also retries 429/5xx via urllib3 Retry
        )

    def get_user(self, user_id: int) -> ApiResponse[User]:
        return self._get(f"/users/{user_id}", User)


user = ExampleApi(token).get_user(1).data   # -> User (validated); raises on a bad body
```

- **`.data` is typed exactly `T`.** `None` appears only if you include it in
  the model (`User | None`) or pass no model. A required model with an empty or
  invalid body raises `pydantic.ValidationError`.
- **`Headers`** serializes snake_case fields to canonical `Header-Case`
  (`content_type` → `Content-Type`), keeps unknown headers verbatim, and offers
  common headers as constructor hints (`authorization`, `x_api_key`,
  `x_ibm_client_id`, …).
- **XML APIs:** install the `xml` extra and use a `pydantic_xml.BaseXmlModel`
  response model — the body is parsed from XML bytes automatically instead of
  JSON.

The `BaseClient` request methods (`_get`/`_post`/`_request`) are protected:
expose intent-revealing endpoint methods on your subclass rather than calling
them from test code directly.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for environment setup, git-hook
installation and ty type checking.

## Version history

See [CHANGELOG.md](CHANGELOG.md). CI/CD details live in
[CONTRIBUTING.md](CONTRIBUTING.md).

## Why this exists

Separates universal patterns (logging, page objects, configuration
loading) from driver-specific code. Appium and WinAppDriver reuse the
same page-object model, step reporting and configuration pipeline
without a hard dependency on Selenium.
