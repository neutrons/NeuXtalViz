import pyvista as pv
from nova.trame.view.layouts import GridLayout

from NeuXtalViz.components.visualization_panel.view_trame import VisualizationPanel
from NeuXtalViz.view_models.crystal_structure_tools import CrystalStructureViewModel
from NeuXtalViz.views.shared.crystal_structure_plotter import CrystalStructurePlotter


class CrystalStructureView:
    def __init__(self, server, view_model: CrystalStructureViewModel):
        self.server = server
        self.view_model = view_model

        plotter = pv.Plotter(off_screen=True)
        plotter.background_color = "#f0f0f0"
        self.plotter = CrystalStructurePlotter(plotter, self.highlight_row)

        self.create_ui()

    def highlight_row(self):
        pass

    @property
    def state(self):
        return self.server.state

    def create_ui(self):
        with GridLayout(classes="bg-white pa-2", columns=2):
            self.visualization_panel = VisualizationPanel("crystal_structure",
                                                          self.plotter.pv_plotter,
                                                          self.view_model.model,
                                                          self.server)
            self.view_model.set_vis_viewmodel(self.visualization_panel.view_model)
            cube = pv.Cube()
            self.plotter.pv_plotter.add_mesh(cube, color='skyblue', show_edges=True)

#            with VBoxLayout():
#               with HBoxLayout(valign="center"):
#                   InputField(v_model="vs_controls.vol_scale", type="select")
