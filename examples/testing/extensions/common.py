from collections.abc import Iterator

from hikari.impl.gateway_bot import GatewayBot
from psutil import Process

from kita.commands import command
from kita.data import Inject
from kita.responses import Response, respond


@command("ping", "Responds with the latency!")
def ping(
    app: Inject[GatewayBot],
) -> Response:
    return respond(f"Latency: {int(app.heartbeat_latency * 1000)}ms")


@command("rss", "Responds with the RSS of the app.")
def rss(process: Inject[Process]) -> Response:
    rss = process.memory_full_info().rss
    return respond(f"{round(rss / 1_024**2, 2)}MiB")


@command("raise", "Raise an error")
def raise_() -> Iterator[Response]:
    yield respond("raising an error...")
    raise RuntimeError()
