# tquality-py-core

Driver-agnostic core for tquality test automation. Provides the foundation
that driver-specific packages (Selenium, Appium, WinAppDriver) build on.

## What's included

- **BaseConfig** — pydantic-settings-based configuration with JSON/env/dotenv
  resolution. Subclass to add driver-specific fields.
- **Logger, LogLevel, step** — per-test-context logging with allure integration.
  CRITICAL steps attach screenshots via a pluggable provider.
- **BaseForm** — base class for pages and forms (page = full-context form).
- **BaseElement** — abstract interface that driver-specific elements implement.
- **StringUtils** — common string parsing helpers.

## What's NOT included

- Concrete driver integration (Selenium, Appium, WinAppDriver) — those live in
  separate packages and depend on this core.
- Element types (Button, Input, Label, etc.) — driver-specific implementations
  live alongside the driver integration.
- DI container wiring — each consuming project builds its own container using
  `dependency-injector`, registering core services and driver-specific services.

## Integration contract

Consuming packages must:

1. Subclass `BaseConfig` with driver-specific fields.
2. Register a Logger resolver via `set_logger_resolver(lambda: Container.logger())`.
3. Register a `ScreenshotProvider` via `set_screenshot_provider(MyDriverProvider())`
   so CRITICAL steps can capture screenshots.
4. Provide concrete `BaseElement` subclasses with find/wait logic.

## Install

```
uv pip install tquality-py-core
```

## Why this exists

Keeps universal patterns (logging, page objects, config loading) separate from
driver-specific code. Appium and WinAppDriver reuse the same page object model,
step reporting, and configuration pipeline without pulling in Selenium.
