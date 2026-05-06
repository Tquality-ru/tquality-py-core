# tquality-py-core

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
- **`StringUtils`** — string-parsing helpers.

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

or with [uv](https://docs.astral.sh/uv/):

```bash
uv add tquality-py-core
```

In the consumer's `pyproject.toml`:

```toml
dependencies = [
    "tquality-py-core>=0.1.3",
]
```

### Alternative: install from the GitHub mirror

For a source build (for example, to verify a commit that has not yet
been released), the package is also available from the public GitHub
mirror by tag:

```bash
uv pip install "tquality-py-core @ git+https://github.com/Tquality-ru/tquality-py-core.git@v0.1.3"
```

In that case hatch on the consumer side requires explicit opt-in to
`direct-references`:

```toml
[tool.hatch.metadata]
allow-direct-references = true
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
    "default_timeout": 10.0,
    "log_dir": "logs",
    "highlight_elements": false,
}
```

Editors with JSON Schema support (VS Code, JetBrains IDEs) autocomplete
the available fields and validate values. The jsonc/json5 syntax allows
`//` and `/* */` comments and trailing commas.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for environment setup, git-hook
installation and mypy type checking.

## CI/CD

GitLab CI runs two checks on every MR and on master:

- **`mypy`** — strict mode type checking.
- **`tests`** — pytest with a JUnit report.

On a git tag `vX.Y.Z`:

- **`publish-pypi`** — build (version derived from the tag via
  `hatch-vcs`) and upload to public
  [PyPI](https://pypi.org/project/tquality-py-core/). Requires the
  `PYPI_TOKEN` variable in CI/CD settings (protected, masked).
- **`publish`** — duplicate publication to the GitLab Package Registry
  (internal mirror).
- **`mirror-to-github`** — master and the tag are pushed to
  https://github.com/Tquality-ru/tquality-py-core (`feature/*` branches
  are not copied to the mirror).

Version history lives in [CHANGELOG.md](CHANGELOG.md).

## Why this exists

Separates universal patterns (logging, page objects, configuration
loading) from driver-specific code. Appium and WinAppDriver reuse the
same page-object model, step reporting and configuration pipeline
without a hard dependency on Selenium.
