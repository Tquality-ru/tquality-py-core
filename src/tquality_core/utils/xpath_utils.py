"""Driver-agnostic XPath-строковые хелперы.

Логика чисто строковая - не зависит от Selenium, Appium или конкретного
типа локатора. Используется обоими драйверными пакетами как для нормализации
relative-xpath перед конкатенацией, так и для безопасного квотирования
значений в xpath-предикатах.
"""

from __future__ import annotations


class XPathUtils:
    """Stateless-хелперы для манипуляции XPath-строк."""

    @staticmethod
    def normalize(value: str) -> str:
        """Сделать xpath безопасным для конкатенации с родительским локатором.

        `.` → `""` (self нейтрален при склейке: `parent + .` даёт самого
        parent'а), `./foo` → `/foo`, `.//foo` → `//foo`, `foo` → `/foo`.
        Уже абсолютные (`/foo`, `//foo`) - без изменений.
        """
        if value == ".":
            return ""
        if value.startswith(".//"):
            return value[1:]
        if value.startswith("./"):
            return value[1:]
        if not value.startswith("/"):
            return "/" + value
        return value

    @staticmethod
    def literal(value: str) -> str:
        """Квотит `value` как XPath-литерал, корректно обрабатывая
        встроенные кавычки.

        XPath не имеет escape для кавычек, поэтому:
        - нет `'` → оборачиваем в `'…'`;
        - иначе нет `"` → оборачиваем в `"…"`;
        - иначе бьём по `'` и склеиваем через `concat('a', "'", 'b', ...)`.
        """
        if "'" not in value:
            return f"'{value}'"
        if '"' not in value:
            return f'"{value}"'
        parts = (f"'{p}'" for p in value.split("'"))
        return "concat(" + ', "\'", '.join(parts) + ")"
