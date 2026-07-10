"""Юнит-тесты модели Headers (трансформации сериализации, а не значения по умолчанию)."""

from __future__ import annotations

from tquality_core.http_client import ContentType, Headers


class TestHeaders:
    def test_snake_fields_serialize_to_header_case(self) -> None:
        # alias_generator + serialize_by_alias: ключ — Header-Case, snake-имени в выводе нет.
        dumped = Headers().as_dict()
        assert "Content-Type" in dumped
        assert "content_type" not in dumped

    def test_unset_optional_headers_are_omitted(self) -> None:
        # exclude_none: опциональный заголовок без значения не уходит на провод.
        assert "Authorization" not in Headers().as_dict()

    def test_set_optional_header_round_trips(self) -> None:
        token = "Bearer xyz"
        assert Headers(authorization=token).as_dict()["Authorization"] == token

    def test_explicit_field_alias_overrides_generator(self) -> None:
        # Явный alias побеждает генератор: используется ровно объявленное имя,
        # а не то, что выдал бы генератор из snake-имени.
        alias = Headers.model_fields["x_api_key"].alias
        assert alias is not None
        generated = "-".join(part.capitalize() for part in "x_api_key".split("_"))
        dumped = Headers.model_validate({alias: "k"}).as_dict()
        assert dumped[alias] == "k"
        assert generated not in dumped

    def test_extra_headers_pass_through_unchanged(self) -> None:
        # extra="allow": неизвестные заголовки идут как есть, генератор их не трогает
        # (в т.ч. подчёркивания не превращаются в дефисы).
        custom_key, custom_value = "X_Custom_Token", "abc"
        dumped = Headers.model_validate({custom_key: custom_value}).as_dict()
        assert dumped[custom_key] == custom_value

    def test_construct_by_field_name_or_by_alias_are_equivalent(self) -> None:
        value = "text/plain"
        alias = Headers.model_fields["content_type"].alias
        assert alias is not None
        assert Headers(content_type=value).as_dict() == Headers.model_validate({alias: value}).as_dict()

    def test_enum_content_type_is_coerced_to_plain_str(self) -> None:
        # use_enum_values: присваивается строка значения, а не вариант enum.
        value = Headers(content_type=ContentType.APPLICATION_XML).as_dict()["Content-Type"]
        assert value == ContentType.APPLICATION_XML
        assert type(value) is str

    def test_arbitrary_content_type_string_accepted(self) -> None:
        custom = "application/vnd.api+json"
        assert Headers(content_type=custom).as_dict()["Content-Type"] == custom
