"""Тесты для ModelMetadata / SettingsMetadata."""

from __future__ import annotations

import pytest
from pydantic import AliasChoices, AliasPath, BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from tquality_core.utils.pydantic_utils import ModelMetadata, SettingsMetadata


class Waiter(BaseModel):
    timeout: float = 10.0


class Plain(BaseModel):
    a: int = 1
    aliased: str = Field("x", validation_alias="inAlias", serialization_alias="outAlias")
    waiter: Waiter = Field(default_factory=Waiter)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TEST_", env_nested_delimiter="__")

    base_url: str = "u"
    flag: bool = False
    waiter: Waiter = Field(default_factory=Waiter)


# --- ModelMetadata: alias-имена для BaseModel ---


def test_validation_alias_uses_alias_else_field_name() -> None:
    meta = ModelMetadata(Plain)
    assert meta.get_validation_alias(lambda s: s.aliased) == "inAlias"
    assert meta.get_validation_alias(lambda s: s.a) == "a"


def test_serialization_alias_uses_alias_else_field_name() -> None:
    meta = ModelMetadata(Plain)
    assert meta.get_serialization_alias(lambda s: s.aliased) == "outAlias"
    assert meta.get_serialization_alias(lambda s: s.a) == "a"


def test_nested_field_resolves_leaf_name() -> None:
    meta = ModelMetadata(Plain)
    assert meta.get_validation_alias(lambda s: s.waiter.timeout) == "timeout"


def test_maps_flatten_dotted_paths() -> None:
    meta = ModelMetadata(Plain)
    assert meta.validation_map() == {"a": "a", "aliased": "inAlias", "waiter.timeout": "timeout"}
    assert meta.serialization_map() == {"a": "a", "aliased": "outAlias", "waiter.timeout": "timeout"}


def test_serialization_map_matches_model_dump_keys() -> None:
    dumped = Plain().model_dump(by_alias=True)
    keys = set(dumped) | set(dumped["waiter"])
    assert set(ModelMetadata(Plain).serialization_map().values()) <= keys


def test_alias_choices_resolves_to_first_string() -> None:
    class M(BaseModel):
        f: str = Field("v", validation_alias=AliasChoices("c1", "c2"))  # type: ignore[pydantic-alias]

    meta = ModelMetadata(M)
    assert meta.get_validation_alias(lambda s: s.f) == "c1"


def test_alias_path_cannot_be_represented() -> None:
    class M(BaseModel):
        f: str = Field("v", validation_alias=AliasPath("a", 0))  # type: ignore[pydantic-alias]

    meta = ModelMetadata(M)
    with pytest.raises(ValueError, match="cannot be represented"):
        meta.get_validation_alias(lambda s: s.f)


def test_selecting_a_nested_model_is_rejected() -> None:
    meta = ModelMetadata(Plain)
    with pytest.raises(TypeError, match="nested model"):
        meta.get_serialization_alias(lambda s: s.waiter)


def test_unknown_field_raises_attribute_error() -> None:
    meta = ModelMetadata(Plain)
    with pytest.raises(AttributeError):
        meta.get_validation_alias(lambda s: s.nope)  # type: ignore[attr-defined]  # ty:ignore[unresolved-attribute]


def test_rejects_non_basemodel() -> None:
    with pytest.raises(TypeError, match="BaseModel"):
        ModelMetadata(int)


def test_accepts_basesettings_as_a_model() -> None:
    meta = ModelMetadata(Settings)
    assert meta.get_validation_alias(lambda s: s.base_url) == "base_url"


# --- SettingsMetadata: env-имена для BaseSettings ---


def test_env_alias_applies_prefix_and_uppercase() -> None:
    meta = SettingsMetadata(Settings)
    assert meta.get_env_alias(lambda s: s.base_url) == "TEST_BASE_URL"


def test_env_alias_nested_uses_delimiter() -> None:
    meta = SettingsMetadata(Settings)
    assert meta.get_env_alias(lambda s: s.waiter.timeout) == "TEST_WAITER__TIMEOUT"


def test_env_map_covers_all_fields() -> None:
    meta = SettingsMetadata(Settings)
    assert meta.env_map() == {
        "base_url": "TEST_BASE_URL",
        "flag": "TEST_FLAG",
        "waiter.timeout": "TEST_WAITER__TIMEOUT",
    }


def test_settings_metadata_inherits_alias_methods() -> None:
    meta = SettingsMetadata(Settings)
    assert meta.get_validation_alias(lambda s: s.base_url) == "base_url"
    assert isinstance(meta, ModelMetadata)


def test_rejects_non_basesettings() -> None:
    with pytest.raises(TypeError, match="BaseSettings"):
        SettingsMetadata(Plain)


def test_env_alias_names_are_what_pydantic_reads(monkeypatch: pytest.MonkeyPatch) -> None:
    meta = SettingsMetadata(Settings)
    monkeypatch.setenv(meta.get_env_alias(lambda s: s.base_url), "http://set")
    monkeypatch.setenv(meta.get_env_alias(lambda s: s.waiter.timeout), "99.5")

    built = Settings(_env_file=None)  # ty:ignore[unknown-argument]
    assert built.base_url == "http://set"
    assert built.waiter.timeout == 99.5
