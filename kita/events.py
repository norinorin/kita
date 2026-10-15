from __future__ import annotations

from abc import ABC, abstractmethod

from attr import attrib, attrs
from hikari.events.base_events import Event
from hikari.traits import RESTAware

from kita.contexts import Context
from kita.errors import KitaError

__all__ = (
    "CommandCallEvent",
    "CommandFailureEvent",
    "CommandSuccessEvent",
    "KitaEvent",
)


@attrs(slots=True, weakref_slot=False)
class KitaEvent(Event, ABC):
    _app: RESTAware = attrib(alias="app")

    @property
    def app(self) -> RESTAware:
        return self._app

    @property
    @abstractmethod
    def context(self) -> Context: ...


@attrs(slots=True, weakref_slot=False)
class CommandCallEvent(KitaEvent):
    _context: Context = attrib(alias="context")

    @property
    def context(self) -> Context:
        return self._context


@attrs(slots=True, weakref_slot=False)
class CommandFailureEvent(KitaEvent):
    _context: Context = attrib(alias="context")

    @property
    def context(self) -> Context:
        return self._context

    exception: KitaError = attrib()


@attrs(slots=True, weakref_slot=False)
class CommandSuccessEvent(KitaEvent):
    _context: Context = attrib(alias="context")

    @property
    def context(self) -> Context:
        return self._context
