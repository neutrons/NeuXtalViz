"""Entrypoint for NeuXtalViz."""

import sys
from typing import Any

from trame_server.core import Server

from NeuXtalViz.panel.views.main_view import NeuXtalViz


def start_panel_server(**kwargs) -> None:
    app = NeuXtalViz()
    for arg in sys.argv[2:]:
        try:
            key, value = arg.split("=")
            kwargs[key] = int(value)
        except Exception:
            pass
    app.serve(**kwargs)
