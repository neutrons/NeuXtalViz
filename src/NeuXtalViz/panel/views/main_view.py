"""Main file."""

import logging
from typing import Any, Dict

import panel as pn
from nova.mvvm.panel_binding import PanelBinding

from NeuXtalViz.models.crystal_structure_tools import CrystalStructureModel
from NeuXtalViz.panel.views.crystal_structure_view import CrystalStructureView
from NeuXtalViz.view_models.crystal_structure_tools import CrystalStructureViewModel

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class NeuXtalViz():
    """Main application view class."""

    def __init__(self) -> None:
        self.create_ui()

    def create_ui(self) -> None:
        pn.extension()
        binding = PanelBinding()

        self.crystal_structure_view_model = CrystalStructureViewModel(
            CrystalStructureModel(), binding
        )

        cs = CrystalStructureView(self.crystal_structure_view_model)

        tabs = pn.Tabs(('Crystal System', cs), dynamic=True)
        self.template = pn.template.MaterialTemplate(title='NeuXtalViz', main=[tabs])

    def serve(self, **kwargs: Dict[str, Any]) -> None:
        pn.serve(self.template.servable(), port=kwargs.get("--port", 5006))
