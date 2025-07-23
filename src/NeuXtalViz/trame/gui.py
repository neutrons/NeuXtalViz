"""Entrypoint for NeuXtalViz."""

import sys
from typing import Any

from trame_server.core import Server

from NeuXtalViz.trame.views.main_view import NeuXtalViz


def trame(server: Server = None, *args: Any, **kwargs: Any) -> None:
    app = NeuXtalViz(server)
    for arg in sys.argv[1:]:
        try:
            key, value = arg.split("=")
            kwargs[key] = int(value)
        except Exception:
            pass
    app.server.start(**kwargs, host="0.0.0.0", port=8080, timeout=0)
