from __future__ import annotations

import inspect
from collections.abc import Coroutine
from typing import TYPE_CHECKING, Any, TypeVar

from hikari.events.interaction_events import InteractionCreateEvent
from hikari.impl.gateway_bot import GatewayBot
from hikari.interactions.command_interactions import CommandInteraction
from hikari.messages import Message
from typing_extensions import Self

from kita.responses import Response, defer, edit, respond
from kita.typedefs import ICommandCallback

if TYPE_CHECKING:
    from kita.command_handlers import GatewayCommandHandler

__all__ = ("Context",)
ContextT = TypeVar("ContextT", bound="Context")


class Context:
    __slots__ = (
        "command",
        "deferring",
        "event",
        "handler",
        "last_message",
        "n_message",
    )

    def __init__(self, event: InteractionCreateEvent, handler: GatewayCommandHandler):
        self.event = event
        self.n_message: int = 0
        self.handler = handler
        self.last_message: Message | None = None
        self.command: ICommandCallback | None = None
        self.deferring = False

    def set_command(self, command: ICommandCallback) -> Self:
        self.command = command
        return self

    @property
    def app(self) -> GatewayBot:
        assert isinstance(self.event.app, GatewayBot)
        return self.event.app

    @property
    def interaction(self) -> CommandInteraction:
        assert isinstance(self.event.interaction, CommandInteraction)
        return self.event.interaction

    def defer(
        self, *args: Any, **kwargs: Any
    ) -> Coroutine[Any, Any, Message | None]:
        return defer(*args, **kwargs).execute(self)

    def respond(
        self, *args: Any, **kwargs: Any
    ) -> Coroutine[Any, Any, Message | None]:
        return respond(*args, **kwargs).execute(self)

    def edit(self, *args: Any, **kwargs: Any) -> Coroutine[Any, Any, Message | None]:
        return edit(*args, **kwargs).execute(self)

    async def _resolve_ret_val(self, obj: Any) -> Any:
        if inspect.isawaitable(obj):
            obj = await obj

        if isinstance(obj, Response):
            obj = await obj.execute(self)

        if inspect.isasyncgen(obj) or inspect.isgenerator(obj):
            await self._consume_gen(obj)
            return None

        return obj

    async def _consume_gen(self, gen: Any) -> None:
        if async_gen := inspect.isasyncgen(gen):
            send = gen.asend
        elif inspect.isgenerator(gen):
            send = gen.send
        else:
            await self._resolve_ret_val(gen)
            return

        sent: Any = None

        try:
            while 1:
                val = send(sent)

                if async_gen:
                    val = await val

                sent = await self._resolve_ret_val(val)
        except (StopIteration, StopAsyncIteration):
            pass
