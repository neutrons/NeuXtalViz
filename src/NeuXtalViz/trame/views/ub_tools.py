import pyvista as pv

from matplotlib.figure import Figure
from nova.trame.view.layouts import GridLayout, VBoxLayout

from NeuXtalViz.components.visualization_panel.view_trame import VisualizationPanel
from NeuXtalViz.view_models.ub_tools import UBViewModel
from NeuXtalViz.views.shared.ub_plotter import UBPlotter


class UBView:
    def __init__(self, server, view_model: UBViewModel):
        self.server = server
        self.view_model = view_model

        self.fig_slice = Figure(figsize=(12.8, 12.8))
        self.fig_inst = Figure(constrained_layout=True)
        self.fig_scan = Figure(constrained_layout=True)
        self.fig_clust = Figure(tight_layout=True)

        self.pv_plotter = pv.Plotter(off_screen=True)
        self.pv_plotter.background_color = "#f0f0f0"
        self.plotter = UBPlotter(
            self.view_model,
            self.pv_plotter,
            self.fig_slice,
            self.fig_inst,
            self.fig_scan,
            self.fig_clust,
        )

        self.create_ui()

    def create_ui(self):
        with GridLayout(classes="bg-white pa-2", columns=3, gap="2em", valign="start"):
            with VBoxLayout(column_span=2):
                self.visualization_panel = VisualizationPanel(
                    "ub", self.pv_plotter, self.view_model.model, self.server
                )
                self.view_model.set_vis_viewmodel(self.visualization_panel.view_model)
            with VBoxLayout(classes="h-100"):
                pass
