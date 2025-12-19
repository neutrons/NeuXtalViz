from typing import Any

import panel as pn
import pyvista as pv
from nova.mvvm.panel_binding import PanelBinding

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
        pvcylinder = pv.Cylinder(resolution=8, direction=(0, 1, 0))
        cylinder_actor = plotter.add_mesh(pvcylinder, color=(1, 0.2, 0.4), smooth_shading=True)
        cylinder_actor.RotateX(30.0)
        cylinder_actor.RotateY(-45.0)
        self.vtk_panel = pn.pane.VTK(plotter.ren_win, width=500, height=500)
        self.vtk_panel.reset_camera()
        self.vtk_panel.synchronize()

        head = pn.GridSpec(sizing_mode='stretch_width')
        head[0, 0] = pn.Column(
            pn.widgets.Button(name='Save Screenshot', sizing_mode='stretch_width'),
            pn.widgets.Button(name='Reset View', sizing_mode='stretch_width', on_click=self.clear_scene),
            pn.widgets.Button(name='Reset Camera', sizing_mode='stretch_width', on_click=self.reset_camera)
        )
        dir_view = pn.GridBox(
            pn.widgets.Button(name='+Qx', sizing_mode='stretch_width'),
            pn.widgets.Button(name='+Qy', sizing_mode='stretch_width'),
            pn.widgets.Button(name='+Qz', sizing_mode='stretch_width'),
            pn.widgets.Button(name='a*', sizing_mode='stretch_width'),
            pn.widgets.Button(name='b*', sizing_mode='stretch_width'),
            pn.widgets.Button(name='c*', sizing_mode='stretch_width'),
            pn.widgets.Button(name='-Qx', sizing_mode='stretch_width'),
            pn.widgets.Button(name='-Qy', sizing_mode='stretch_width'),
            pn.widgets.Button(name='-Qz', sizing_mode='stretch_width'),
            pn.widgets.Button(name='a', sizing_mode='stretch_width'),
            pn.widgets.Button(name='b', sizing_mode='stretch_width'),
            pn.widgets.Button(name='c', sizing_mode='stretch_width'),
            ncols=6,
            sizing_mode='stretch_width'
        )
        man_view = pn.Column(
            pn.Row(
                pn.widgets.Select(name='Axis Type', options=['hkl', 'uvw'], sizing_mode='stretch_width'),
                pn.widgets.Select(name='Up Axis Type', options=['hkl', 'uvw'], sizing_mode='stretch_width')
            ),
            pn.GridBox(
                pn.Row(
                    pn.widgets.FloatInput(name='h', sizing_mode='stretch_width'),
                    pn.widgets.FloatInput(name='k', sizing_mode='stretch_width'),
                    pn.widgets.FloatInput(name='l', sizing_mode='stretch_width'),
                    pn.widgets.Button(name='View Axis', align='center'),
                ),
                pn.Row(
                    pn.widgets.FloatInput(name='h', sizing_mode='stretch_width'),
                    pn.widgets.FloatInput(name='k', sizing_mode='stretch_width'),
                    pn.widgets.FloatInput(name='l', sizing_mode='stretch_width'),
                    pn.widgets.Button(name='View Up Axis', align='center'),
                ),
                ncols=2)
        )
        head[0, 1:4] = pn.Tabs(('Direction View', dir_view), ('Manual View', man_view))

        head[0, 4] = pn.Column(
            pn.widgets.Checkbox(name='Reciprocal Lattice'),
            pn.widgets.Checkbox(name='Show Axes'),
            pn.widgets.Checkbox(name='Parallel Projection')
        )
        lp = pn.Column(
            pn.Row(
                pn.widgets.FloatInput(name='a', sizing_mode='stretch_width'),
                pn.widgets.FloatInput(name='b', sizing_mode='stretch_width'),
                pn.widgets.FloatInput(name='c', sizing_mode='stretch_width'),
                pn.pane.Str("Å", align='center'),
            ),
            pn.Row(
                pn.widgets.FloatInput(name='α', sizing_mode='stretch_width'),
                pn.widgets.FloatInput(name='β', sizing_mode='stretch_width'),
                pn.widgets.FloatInput(name='γ', sizing_mode='stretch_width'),
                pn.pane.Str("°", align='center'),
            )
        )
        so = pn.Column(
            pn.Row(
                pn.pane.Str("u:", align='center'),
                pn.widgets.FloatInput(sizing_mode='stretch_width'),
                pn.widgets.FloatInput(name='', sizing_mode='stretch_width'),
                pn.widgets.FloatInput(name='', sizing_mode='stretch_width'),
            ),
            pn.Row(
                pn.pane.Str("v:", align='center'),
                pn.widgets.FloatInput(sizing_mode='stretch_width'),
                pn.widgets.FloatInput(sizing_mode='stretch_width'),
                pn.widgets.FloatInput(sizing_mode='stretch_width'),
            )
        )
        footer = pn.Tabs(('Lattice Parameters', lp), ('Sample Orientation', so))
        progress = pn.widgets.Tqdm(sizing_mode='stretch_width')

        self._layout = pn.Column(head, self.vtk_panel, footer, progress)

    def __panel__(self):
        return self._layout

    def update_view(self, event):
        pass

    def save_screenshot(self):
        pass

    def clear_scene(self,_):
        self.plotter.clear_scene()
        self.vtk_panel.synchronize()


    def reset_camera(self, event: Any):
        """
        Reset the camera.

        """
        self.vtk_panel.reset_camera()
        self.vtk_panel.synchronize()



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
