from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable, MutableMapping, MutableSequence
from importlib.machinery import ModuleSpec
from types import CodeType
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    Protocol,
    TypeVar,
    override,
)

from hikari.commands import CommandOption, OptionType
from hikari.events.base_events import EventT
from hikari.events.interaction_events import InteractionCreateEvent
from hikari.snowflakes import Snowflakeish
from hikari.undefined import UndefinedOr

if TYPE_CHECKING:
    from importlib.abc import Loader

    from kita.buckets import BucketManager
    from kita.command_handlers import GatewayCommandHandler

__all__ = (
    "BucketHash",
    "CallableProto",
    "CommandCallback",
    "CommandContainer",
    "EventCallback",
    "Extension",
    "ExtensionFinalizer",
    "ExtensionInitializer",
    "HashGetter",
    "ICommandCallback",
    "IExtensionCallback",
    "IGroupCommandCallback",
    "LimitGetter",
    "OptionAware",
    "PeriodGetter",
    "SignatureAware",
    "SubCommandCallback",
    "SubCommandGroupCallback",
)
T = TypeVar("T")


class OptionAware(Protocol):
    options: list[CommandOption]


class CallableT(Protocol[T]):
    __call__: Callable[..., T]


class CallableProto(Protocol):
    __call__: Callable[..., Any]


class SignatureAware(CallableProto, Protocol):
    __signature__: inspect.Signature


class ICommandCallback(OptionAware, SignatureAware, Protocol):
    __type__: UndefinedOr[OptionType]
    __name__: str
    __description__: str
    __code__: CodeType
    __module__: str
    __is_command__: Literal[True]
    __checks__: list[CallableProto]
    __bucket_manager__: BucketManager | None


class IGroupCommandCallback(ICommandCallback, Protocol):
    __sub_commands__: MutableMapping[str, SubCommandCallback | SubCommandGroupCallback]

    @staticmethod
    def command(name: str, description: str) -> Callable[[CallableProto], SubCommandCallback]: ...


class CommandCallback(IGroupCommandCallback, Protocol):
    __guild_ids__: set[Snowflakeish]

    @staticmethod
    def group(
        name: str, description: str
    ) -> Callable[[CallableProto], SubCommandGroupCallback]: ...


class SubCommandCallback(ICommandCallback, Protocol): ...


class SubCommandGroupCallback(IGroupCommandCallback, Protocol):
    __sub_commands__: MutableMapping[str, SubCommandCallback]


CommandContainer = MutableMapping[str, CommandCallback]


class Extension(Protocol):
    __name__: str
    __file__: str | None
    __dict__: dict[str, Any]
    __loader__: Loader | None
    __package__: str | None
    __path__: MutableSequence[str]
    __spec__: ModuleSpec | None
    __einit__: ExtensionInitializer | None
    __edel__: ExtensionFinalizer | None


class IExtensionCallback(Protocol):
    def __call__(self, handler: GatewayCommandHandler) -> Any: ...


class ExtensionInitializer(Protocol):
    __name__: Literal["__einit__"]
    __call__: IExtensionCallback


class ExtensionFinalizer(Protocol):
    __name__: Literal["__edel__"]
    __call__: IExtensionCallback


class _IEventCallback(SignatureAware, Protocol[EventT]):
    __etype__: type[EventT]
    __is_listener__: Literal[True]


class _EventCallback(_IEventCallback[EventT], Protocol):
    async def call(self, event: EventT) -> None: ...


class _EventCallbackWithData(_IEventCallback[EventT], Protocol):
    async def call(self, event: EventT, *args: Any, **kwargs: Any) -> None: ...


EventCallback = _EventCallback[EventT] | _EventCallbackWithData[EventT]
BucketHash = Snowflakeish | tuple[Snowflakeish, ...]


class _SyncHashGetter(CallableT[BucketHash], Protocol):
    def __call__(self, event: InteractionCreateEvent) -> BucketHash: ...


class _SyncHashGetterWithData(CallableT[BucketHash], Protocol):
    def __call__(self, event: InteractionCreateEvent, *args: Any, **kwargs: Any) -> BucketHash: ...


class _AsyncHashGetter(CallableT[Awaitable[BucketHash]], Protocol):
    async def __call__(self, event: InteractionCreateEvent) -> BucketHash: ...


class _AsyncHashGetterWithData(CallableT[Awaitable[BucketHash]], Protocol):
    async def __call__(
        self, event: InteractionCreateEvent, *args: Any, **kwargs: Any
    ) -> BucketHash: ...


class _SyncLimitGetter(CallableT[int], Protocol):
    @override
    def __call__(self, hash: BucketHash) -> int: ...


class _SyncLimitGetterWithData(CallableT[int], Protocol):
    def __call__(self, hash: BucketHash, *args: Any, **kwargs: Any) -> int: ...


class _AsyncLimitGetter(CallableT[Awaitable[int]], Protocol):
    async def __call__(self, hash: BucketHash) -> int: ...


class _AsyncLimitGetterWithData(CallableT[Awaitable[int]], Protocol):
    async def __call__(self, hash: BucketHash, *args: Any, **kwargs: Any) -> int: ...


class _SyncPeriodGetter(CallableT[float], Protocol):
    @override
    def __call__(self, hash: BucketHash) -> float: ...


class _SyncPeriodGetterWithData(CallableT[float], Protocol):
    def __call__(self, hash: BucketHash, *args: Any, **kwargs: Any) -> float: ...


class _AsyncPeriodGetter(CallableT[Awaitable[float]], Protocol):
    async def __call__(self, hash: BucketHash) -> float: ...


class _AsyncPeriodGetterWithData(CallableT[Awaitable[float]], Protocol):
    async def __call__(self, hash: BucketHash, *args: Any, **kwargs: Any) -> float: ...


HashGetter = _SyncHashGetter | _SyncHashGetterWithData | _AsyncHashGetter | _AsyncHashGetterWithData
LimitGetter = (
    _SyncLimitGetter | _SyncLimitGetterWithData | _AsyncLimitGetter | _AsyncLimitGetterWithData
)
PeriodGetter = (
    _SyncPeriodGetter | _SyncPeriodGetterWithData | _AsyncPeriodGetter | _AsyncPeriodGetterWithData
)
