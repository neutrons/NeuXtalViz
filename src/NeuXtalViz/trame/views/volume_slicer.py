from asyncio import create_task, ensure_future, sleep
from functools import partial
from io import BytesIO
from tempfile import NamedTemporaryFile
from threading import Thread

import numpy as np
import pyvista as pv
from matplotlib.figure import Figure
from matplotlib.transforms import Affine2D
from nova.trame.view.components import FileUpload, InputField
from nova.trame.view.components.visualization import MatplotlibFigure
from nova.trame.view.layouts import GridLayout, HBoxLayout, VBoxLayout
from trame.widgets import html
from trame.widgets import vuetify3 as vuetify

from NeuXtalViz.view_models.volume_slicer import VolumeSlicerViewModel
from NeuXtalViz.views.shared.crystal_structure_plotter import CrystalStructurePlotter
from NeuXtalViz.components.visualization_panel.view_trame import VisualizationPanel


class VolumeSlicerView:
    def __init__(self, server, view_model: VolumeSlicerViewModel):
        self.server = server
        self.view_model = view_model
        self.view_model.volume_bind.connect("vs_volume")
        self.view_model.slice_bind.connect("vs_slice")
        self.view_model.cut_bind.connect("vs_cut")
        self.view_model.slice_lim_bind.connect(self.set_slice_lim)
        self.view_model.cut_lim_bind.connect(self.set_cut_lim)
        self.view_model.colorbar_lim_bind.connect(self.update_colorbar_vlims)
        self.view_model.add_histo_bind.connect(self.add_histo)
        self.view_model.add_slice_bind.connect(self.add_slice)
        self.view_model.add_cut_bind.connect(self.add_cut)

        plotter = pv.Plotter(off_screen=True)
        plotter.background_color = "#f0f0f0"
        self.pv_plotter = plotter
        self.plotter = CrystalStructurePlotter(
            self.pv_plotter, self.view_model.interaction_callback
        )

        self.create_ui()

    @property
    def state(self):
        return self.server.state

    def create_ui(self):
        @self.state.change("nxs_file")
        def load_NXS(filename, **kwargs):
            if not filename:
                return

            self.view_model.load_NXS(filename)

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
                        v_model="nxs_file",
                        base_paths=["/HFIR", "/SNS"],
                        extensions=[".nxs"],
                        label="Load NXS",
                        return_contents=False,
                    )

                with HBoxLayout():
                    self.fig_slice = Figure(layout="constrained", figsize=[6.5, 3.0])
                    self.ax_slice = self.fig_slice.subplots(1, 1)
                    self.cb = None

                    self.slice_view = MatplotlibFigure(self.fig_slice, webagg=True)
                    InputField(
                        v_model="vs_slice.vmin",
                        direction="vertical",
                        max=("vs_slice.vlims[1]",),
                        min=("vs_slice.vlims[0]",),
                        type="slider",
                    )
                    InputField(
                        v_model="vs_slice.vmax",
                        direction="vertical",
                        max=("vs_slice.vlims[1]",),
                        min=("vs_slice.vlims[0]",),
                        type="slider",
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
                        self.fig_cut = Figure(layout="constrained", figsize=[7.0, 1.0])
                        self.ax_cut = self.fig_cut.subplots(1, 1)

                        self.cut_view = MatplotlibFigure(self.fig_cut, webagg=True)

                    with HBoxLayout(valign="center"):
                        InputField(v_model="vs_cut.line", type="select")
                        InputField(v_model="vs_cut.value")
                        InputField(v_model="vs_cut.thickness")
                        vuetify.VBtn("Save Cut", click=self.save_cut)
                        InputField(v_model="vs_cut.scale", type="select")

    def add_histo(self, result):
        histo_dict, normal, norm, value, opacity, log_scale, cmap = result
        self.plotter.add_histo(
            histo_dict, normal, norm, value, opacity, log_scale, cmap
        )

    def __format_axis_coord(self, x, y):
        x, y, _ = np.dot(self.T_inv, [x, y, 1])
        return "x={:.3f}, y={:.3f}".format(x, y)

    def add_slice(self, result):
        slice_dict, cmap, scale = result

        x = slice_dict["x"]
        y = slice_dict["y"]

        labels = slice_dict["labels"]
        title = slice_dict["title"]
        signal = slice_dict["signal"]

        vmin = np.nanmin(signal)
        vmax = np.nanmax(signal)

        self.view_model.set_vlims(vmin, vmax)

        if np.isclose(vmax, vmin) or not np.isfinite([vmin, vmax]).all():
            vmin, vmax = (0.1, 1) if scale == "log" else (0, 1)

        T = slice_dict["transform"]
        aspect = slice_dict["aspect"]

        self.T_inv = np.linalg.inv(T)

        self.ax_slice.format_coord = self.__format_axis_coord

        transform = Affine2D(T) + self.ax_slice.transData
        self.transform = transform

        self.xlim = np.array([x.min(), x.max()])
        self.ylim = np.array([y.min(), y.max()])

        if self.cb is not None:
            self.cb.remove()

        self.ax_slice.clear()

        im = self.ax_slice.pcolormesh(
            x,
            y,
            signal,
            norm=scale,
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            shading="flat",
            rasterized=True,
            transform=transform,
        )

        self.im = im
        vmin, self.vmax = self.im.norm.vmin, self.im.norm.vmax

        self.view_model.set_number("vmin", self.im.norm.vmin)
        self.view_model.set_number("vmax", self.im.norm.vmax)
        self.view_model.set_number("xmin", xlim[0])
        self.view_model.set_number("xmax", xlim[1])
        self.view_model.set_number("ymin", ylim[0])
        self.view_model.set_number("ymax", ylim[1])

        self.ax_slice.set_aspect(aspect)
        self.ax_slice.set_xlabel(labels[0])
        self.ax_slice.set_ylabel(labels[1])
        self.ax_slice.set_title(title)
        self.ax_slice.minorticks_on()

        self.ax_slice.xaxis.get_major_locator().set_params(integer=True)
        self.ax_slice.yaxis.get_major_locator().set_params(integer=True)

        self.cb = self.fig_slice.colorbar(self.im, ax=self.ax_slice)
        self.cb.minorticks_on()

        self.slice_view.update(self.fig_slice)

    def add_cut(self, result):
        cut_dict, line_cut, scale, thick = result

        x = cut_dict["x"]
        y = cut_dict["y"]
        e = cut_dict["e"]

        val = cut_dict["value"]

        label = cut_dict["label"]
        title = cut_dict["title"]

        lines = self.ax_slice.get_lines()
        for line in lines:
            line.remove()

        xlim = self.xlim
        ylim = self.ylim

        delta = 0 if thick is None else thick / 2

        if line_cut == "Axis 2":
            l0 = [val - delta, val - delta], ylim
            l1 = [val + delta, val + delta], ylim
        else:
            l0 = xlim, [val - delta, val - delta]
            l1 = xlim, [val + delta, val + delta]

        self.ax_slice.plot(*l0, "w--", linewidth=1, transform=self.transform)
        self.ax_slice.plot(*l1, "w--", linewidth=1, transform=self.transform)

        self.ax_cut.clear()

        self.ax_cut.errorbar(x, y, e)
        self.ax_cut.set_xlabel(label)
        self.ax_cut.set_yscale(scale)
        self.ax_cut.set_title(title)
        self.ax_cut.minorticks_on()

        self.ax_cut.xaxis.get_major_locator().set_params(integer=True)

        self.cut_view.update(self.fig_cut)

    def set_slice_lim(self, lims):
        xlim, ylim = lims

        if self.cb is not None:
            xmin, xmax = xlim
            ymin, ymax = ylim
            T = np.linalg.inv(self.T_inv)
            xmin, ymin, _ = np.dot(T, [xmin, ymin, 1])
            xmax, ymax, _ = np.dot(T, [xmax, ymax, 1])
            self.ax_slice.set_xlim(xmin, xmax)
            self.ax_slice.set_ylim(ymin, ymax)
            self.slice_view.update(self.fig_slice)

    def update_colorbar_vlims(self, vlims):
        vmin, vmax = vlims

        if self.cb is not None:
            self.im.set_clim(vmin=vmin, vmax=vmax)
            self.cb.update_normal(self.im)
            self.cb.minorticks_on()

            self.slice_view.update(self.fig_slice)

    def set_cut_lim(self, lim):
        if self.cb is not None:
            self.ax_cut.set_xlim(*lim)
            self.cut_view.update(self.fig_cut)

    def save_slice(self):
        data = BytesIO()
        self.fig_slice.savefig(data, format="png")
        data.seek(0)
        self.base_view.js_download(("slice.png", data.read()))

    def save_cut(self):
        data = BytesIO()
        self.fig_cut.savefig(data, format="png")
        data.seek(0)
        self.base_view.js_download(("cut.png", data.read()))
