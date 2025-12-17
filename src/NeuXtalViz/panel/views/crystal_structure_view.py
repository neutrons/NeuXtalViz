from NeuXtalViz.view_models.crystal_structure_tools import CrystalStructureViewModel
import panel as pn
from panel.viewable import Viewer
import pyvista as pv
from NeuXtalViz.components.visualization_panel.view_panel import VisualizationPanel

from NeuXtalViz.view_models.crystal_structure_tools import (
    CrystalStructureViewModel,
    CrystalStructureAtoms,
)
from NeuXtalViz.views.shared.crystal_structure_plotter import CrystalStructurePlotter

class CrystalStructureView(Viewer):
    def __init__(self, view_model: CrystalStructureViewModel):
        super().__init__()
        self.view_model = view_model
        plotter = pv.Plotter(off_screen=True)
        plotter.background_color = "#f0f0f0"
        self.pv_plotter = plotter

        self.create_ui()

    def create_ui(self):
        self.visualization_panel = VisualizationPanel("crystal_structure", self.pv_plotter, self.view_model.model)
        self.view_model.set_vis_viewmodel(self.visualization_panel.view_model)
        self.password = pn.widgets.PasswordInput(name="Password")

        gstack = pn.GridSpec(sizing_mode='stretch_both')
        gstack[:, 0: 1] = self.visualization_panel
        gstack[:, 1: 2] = None
        self._layout = pn.Row(gstack)
    def __panel__(self):
        return self._layout

