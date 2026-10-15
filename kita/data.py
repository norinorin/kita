import inspect
from collections.abc import MutableMapping
from typing import (
    Annotated,
    Any,
    Generic,
    TypeIs,
    TypeVar,
    cast,
    get_args,
    get_origin,
    get_type_hints,
    overload,
)

from hikari.undefined import UNDEFINED, UndefinedOr
from typing_extensions import Self

from kita.typedefs import CallableT
from kita.utils import ensure_signature

__all__ = ("DataContainerMixin", "Inject", "data")
T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)
DataContainerT = TypeVar("DataContainerT", bound="DataContainerMixin")


class _InjectMarker:
    __slots__ = ()


# this is meant to be a singleton,
# but we don't care if it's instantiated more than once
# we'll only use the one we instantiated here: _UNSET.
class _UnsetType:
    def __bool__(self) -> bool:
        return False


_UNSET = _UnsetType()
_INJECT = _InjectMarker()
Inject = Annotated[T, _INJECT]
EMPTY_DICT: MutableMapping[type, Any] = {}


def is_unset(value: object) -> TypeIs[_UnsetType]:
    return value is _UNSET


def data(type_: type[T_co]) -> T_co:
    return cast(T_co, Data(type_))


class Data(Generic[T_co]):
    __slots__ = ("type",)

    def __init__(self, type_: type[T_co]) -> None:
        self.type: type[T_co] = type_


class DataContainerMixin:
    __slots__ = ("_data", "_lookup_cache")

    def __init__(self) -> None:
        self._data: dict[type, Any] = {type(self): self}
        self._lookup_cache: dict[type, Any] = {}

    def set_data(
        self,
        data_: Any,
        *,
        override: bool = False,
        suppress: bool = False,
    ) -> Self:
        type_ = type(data_)
        if not override and type_ in self._data:
            if not suppress:
                raise RuntimeError(f"{type_} already exists.")
            return self

        # exclude the type itself and object
        for sup in type_.mro()[1:-1]:
            if sup in self._lookup_cache:
                self._lookup_cache[sup] = data_

        self._data[type_] = data_
        return self

    @overload
    def get_data(self, type_: type[T_co]) -> T_co | None: ...

    @overload
    def get_data(self, type_: type[T_co], default: Any = None) -> Any: ...

    def get_data(self, type_: Any, default: Any = None) -> Any:
        """Gets the injected data."""
        try:
            return self._get_data(type_, {})
        except LookupError:
            return default

    async def _invoke_callback(
        self,
        callback: CallableT[T_co],
        *args: Any,
        extra_env: UndefinedOr[MutableMapping[type, Any]] = UNDEFINED,
        **kwargs: Any,
    ) -> T_co:
        callback = ensure_signature(callback)
        env = extra_env if extra_env is not UNDEFINED else EMPTY_DICT
        hints = get_type_hints(callback, include_extras=True)

        signatures: dict[str, Any] = {}

        for name, param in callback.__signature__.parameters.items():
            if param.kind is not inspect.Parameter.POSITIONAL_OR_KEYWORD:
                continue

            # legacy data(...) syntax
            if isinstance(param.default, Data):
                signatures[name] = self._get_data(param.default.type, env)
                continue

            # new Annotated injection syntax
            hint = hints.get(name)
            if get_origin(hint) is Annotated:
                base_type, *metadata = get_args(hint)
                if _INJECT in metadata:
                    signatures[name] = self._get_data(base_type, env)

        res = callback(*args, **{**signatures, **kwargs})
        if inspect.isawaitable(res):
            return await res

        return res

    def _resolve_data(
        self, type_: type[T_co], env: MutableMapping[type, Any]
    ) -> _UnsetType | tuple[bool, T_co]:
        maybe_data = {**self._data, **env}.get(type_, _UNSET)
        if maybe_data is not _UNSET:
            return False, maybe_data

        cache = self._lookup_cache.get(type_, _UNSET)
        if not is_unset(cache):
            return False, cache

        for subclass in type_.__subclasses__():
            maybe_data = self._resolve_data(subclass, env)
            if not is_unset(maybe_data):
                return subclass not in env, maybe_data[1]

        return _UNSET

    def _get_data(self, type_: type[T_co], env: MutableMapping[type, Any]) -> T_co:
        maybe_data = self._resolve_data(type_, env)

        if is_unset(maybe_data):
            raise LookupError(f"data of type {type_} can't be found.")

        assert isinstance(maybe_data, tuple)
        is_subclass, data_ = maybe_data
        if is_subclass:
            self._lookup_cache[type_] = data_

        return data_
