import numpy as np
import pyvista as pv
from io import BytesIO

from nova.mvvm.panel_binding import PanelBinding

import panel as pn


from NeuXtalViz.components.visualization_panel.view_model import VizViewModel
from NeuXtalViz.views.shared.base_plotter import BasePlotter


class VisualizationPanel:
    def __init__(self, name, pv_plotter, model):
        self.name = name
        binding = PanelBinding()
        self.view_model = VizViewModel(model, binding)
        self.camera_position = None
        self.plotter = BasePlotter(pv_plotter)
        self.create_ui()


    def create_ui(self):
        plotter = self.plotter.pv_plotter
        geo_pan_pv = pn.panel(plotter.ren_win)
        self._layout = pn.Row(geo_pan_pv)

    def __panel__(self):
        return self._layout


    def update_view(self, event):
        pass

    def save_screenshot(self):
        pass

    def clear_scene(self):
        self.plotter.clear_scene()

    def reset_camera(self):
        """
        Reset the camera.

        """

        self.plotter.reset_camera()

    def reset_scene(self):
        self.plotter.reset_scene()

    def reset_view(self, negative=False):
        """
        Reset the view.

        """
        self.plotter.reset_view(negative)

    def show_axes(self, data):
        self.plotter.show_axes(data)
        self.update_view(None)


    def change_projection(self, parallel_projection):
        """
        Enable or disable parallel projection.

        """
        self.plotter.change_projection(parallel_projection)

    def view_vector(self, vecs):
        self.plotter.view_vector(vecs)

    def view_up_vector(self, vec):
        self.plotter.view_up_vector(vec)

    def set_position(self, pos):
        self.plotter.set_position(pos)
