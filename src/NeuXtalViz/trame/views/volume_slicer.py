from asyncio import create_task, ensure_future, sleep
from functools import partial
from io import BytesIO
from tempfile import NamedTemporaryFile
from threading import Thread

import numpy as np
import pyvista as pv
from matplotlib.backends.backend_webagg import FigureCanvasWebAgg
from matplotlib.figure import Figure
from nova.trame.view.components import FileUpload, InputField
from nova.trame.view.components.visualization import MatplotlibFigure
from nova.trame.view.layouts import GridLayout, HBoxLayout, VBoxLayout
from trame.widgets import client, html
from trame.widgets import vuetify3 as vuetify

from NeuXtalViz.view_models.volume_slicer import VolumeSlicerViewModel
from NeuXtalViz.views.shared.volume_slicer import VolumeSlicerPlotter
from NeuXtalViz.components.visualization_panel.view_trame import VisualizationPanel


class VolumeSlicerView:
    def __init__(self, server, view_model: VolumeSlicerViewModel):
        self.server = server
        self.view_model = view_model
        self.view_model.volume_bind.connect("vs_volume")
        self.view_model.slice_bind.connect("vs_slice")
        self.view_model.cut_bind.connect("vs_cut")

        self.canvas_slice = FigureCanvasWebAgg(Figure(constrained_layout=True))
        self.canvas_cut = FigureCanvasWebAgg(
            Figure(constrained_layout=True, figsize=(6.4, 3.2))
        )
        self.fig_slice = self.canvas_slice.figure
        self.fig_cut = self.canvas_cut.figure
        plotter = pv.Plotter(off_screen=True)
        plotter.background_color = "#f0f0f0"
        self.pv_plotter = plotter

        self.create_ui()

        self.plotter = VolumeSlicerPlotter(
            self.view_model,
            self.pv_plotter,
            self.fig_slice,
            self.update_slice,
            self.fig_cut,
            self.update_cut,
        )
        self.view_model.add_histo_bind.connect(self.plotter.add_histo)
        self.view_model.add_slice_bind.connect(self.plotter.add_slice)
        self.view_model.add_cut_bind.connect(self.plotter.add_cut)
        self.view_model.slice_lim_bind.connect(self.plotter.set_slice_lim)
        self.view_model.cut_lim_bind.connect(self.plotter.set_cut_lim)
        self.view_model.colorbar_lim_bind.connect(self.plotter.update_colorbar_vlims)

        self.set_sliders = client.JSEval(
            exec="vs_slice.vmin_slider = $event[0]; vs_slice.vmax_slider = $event[1]; flushState('vs_slice');"
        ).exec
        self.view_model.sliders_bind.connect(self.set_sliders)

    @property
    def state(self):
        return self.server.state

    def create_ui(self):
        with GridLayout(classes="bg-white pa-2", columns=2, gap="2em", valign="start"):
            self.visualization_panel = VisualizationPanel(
                "volume_slicer", self.pv_plotter, self.view_model.model, self.server
            )
            self.view_model.set_vis_viewmodel(self.visualization_panel.view_model)

            with VBoxLayout(classes="v-100"):
                with HBoxLayout(valign="center"):
                    InputField(v_model="vs_volume.scale", type="select")
                    InputField(v_model="vs_volume.opacity", type="select")
                    InputField(v_model="vs_volume.opacity_range", type="select")
                    InputField(v_model="vs_volume.clip_type", type="select")
                    InputField(v_model="vs_volume.cbar", type="select")
                    FileUpload(
                        v_model="vs_volume.nxs_file",
                        base_paths=["/HFIR", "/SNS"],
                        extensions=[".nxs"],
                        label="Load NXS",
                        return_contents=False,
                        use_bytes=True,
                    )

                with HBoxLayout():
                    self.slice_view = MatplotlibFigure(self.fig_slice, webagg=True)
                    vuetify.VSlider(
                        model_value=("vs_slice.vmin_slider",),
                        direction="vertical",
                        max=100,
                        min=0,
                        step=1,
                        type="slider",
                        __events=["end"],
                        end=(
                            self.view_model.set_slice_field,
                            "['vmin_slider', $event]",
                        ),
                    )
                    vuetify.VSlider(
                        model_value=("vs_slice.vmax_slider",),
                        direction="vertical",
                        max=100,
                        min=0,
                        step=1,
                        type="slider",
                        __events=["end"],
                        end=(
                            self.view_model.set_slice_field,
                            "['vmax_slider', $event]",
                        ),
                    )

                with HBoxLayout(valign="center"):
                    InputField(v_model="vs_slice.plane", type="select")
                    InputField(v_model="vs_slice.value")
                    InputField(v_model="vs_slice.thickness")
                    InputField(v_model="vs_cut.show", classes="mr-4", type="checkbox")
                    vuetify.VBtn("Save Slice", click=self.save_slice)
                    InputField(v_model="vs_slice.scale", type="select")

                with HBoxLayout():
                    InputField(v_model="vs_slice.xmin")
                    InputField(v_model="vs_slice.xmax")
                    InputField(v_model="vs_slice.ymin")
                    InputField(v_model="vs_slice.ymax")
                    InputField(v_model="vs_slice.clip_type", type="select")
                    InputField(v_model="vs_slice.vmin")
                    InputField(v_model="vs_slice.vmax")

                with html.Div(v_show="vs_cut.show"):
                    with HBoxLayout():
                        self.cut_view = MatplotlibFigure(self.fig_cut, webagg=True)

                    with HBoxLayout(valign="center"):
                        InputField(v_model="vs_cut.line", type="select")
                        InputField(v_model="vs_cut.value")
                        InputField(v_model="vs_cut.thickness")
                        vuetify.VBtn("Save Cut", click=self.save_cut)
                        InputField(v_model="vs_cut.scale", type="select")

    def save_cut(self):
        data = BytesIO()
        self.fig_cut.savefig(data, format="png")
        data.seek(0)
        self.visualization_panel.js_download(("cut.png", data.read()))

    def save_slice(self):
        data = BytesIO()
        self.fig_slice.savefig(data, format="png")
        data.seek(0)
        self.visualization_panel.js_download(("slice.png", data.read()))

    def update_cut(self):
        self.cut_view.update(self.fig_cut)

    def update_slice(self):
        self.slice_view.update(self.fig_slice)
