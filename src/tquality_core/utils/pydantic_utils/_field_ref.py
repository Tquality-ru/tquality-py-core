class _Ref:
    """Записывает путь обращения к полю для последующего разрешения в имя.

    `meta.ref.waiter.timeout` накапливает путь `("waiter", "timeout")`,
    ничего не вычисляя сам; имя считает резолвер (`get_*_alias`), проигрывая
    путь через соответствующий прокси. Статически `meta.ref` типизирован как
    модель (`-> T`), поэтому путь даёт автодополнение и отлов опечаток, а
    честный `str` возвращает уже резолвер.
    """

    def __init__(self, path: tuple[str, ...] = ()) -> None:
        object.__setattr__(self, "_path", path)

    def __getattr__(self, name: str) -> "_Ref":
        path = object.__getattribute__(self, "_path")
        return _Ref((*path, name))

    @staticmethod
    def path_of(field: object) -> tuple[str, ...]:
        if not isinstance(field, _Ref):
            raise TypeError(f"expected a `meta.ref.<field>` reference, got {field!r}")
        path: tuple[str, ...] = object.__getattribute__(field, "_path")
        if not path:
            raise TypeError("field reference is empty; select a field, e.g. lambda s: s.base_url")
        return path
