import os
import tempfile

import pyvista as pv
from matplotlib.figure import Figure
from nova.trame.view.components import FileUpload, InputField, RemoteFileInput
from nova.trame.view.layouts import GridLayout, HBoxLayout, VBoxLayout
from trame.widgets import client
from trame.widgets import vuetify3 as vuetify

from NeuXtalViz.components.visualization_panel.view_trame import VisualizationPanel
from NeuXtalViz.view_models.ub_tools import UBViewModel
from NeuXtalViz.views.shared.ub_plotter import UBPlotter


class ParametersTab:
    def __init__(self, view_model: UBViewModel):
        self.view_model = view_model

        self.js_download = client.JSEval(
            exec="utils.download($event[0], $event[1], 'text/plain')"
        ).exec
        self.create_ui()

    def create_ui(self):
        with HBoxLayout(gap="0.5em"):
            vuetify.VLabel("Convert to Q")
            InputField(v_model="ub_q_conversion.instrument", type="select")
            InputField(
                v_model="ub_q_conversion.ipts_number",
                disabled=("ub_q_conversion.ipts_disabled",),
            )
            InputField(
                v_model="ub_q_conversion.experiment_number",
                disabled=("ub_q_conversion.experiment_disabled",),
            )
        with HBoxLayout(gap="0.5em"):
            InputField(
                v_model="ub_q_conversion.runs",
                chips=True,
                multiple=True,
                type="combobox",
            )
            RemoteFileInput(
                v_model="ub_q_conversion.detector_calibration",
                base_paths=["/HFIR", "/SNS"],
                return_contents=False,
            )
            RemoteFileInput(
                v_model="ub_q_conversion.tube_calibration",
                base_paths=["/HFIR", "/SNS"],
                return_contents=False,
            )
        with GridLayout(columns=5, gap="0.5em"):
            InputField(v_model="ub_q_conversion.lorentz_correction", type="checkbox")
            InputField(
                v_model="ub_q_conversion.time_stop",
                disabled=("ub_q_conversion.time_stop_disabled",),
            )
            InputField(v_model="ub_q_conversion.d_min")
            InputField(v_model="ub_q_conversion.wl_min")
            with HBoxLayout():
                InputField(
                    v_model="ub_q_conversion.wl_max",
                    disabled=("ub_q_conversion.wl_max_disabled",),
                )
                vuetify.VLabel("Å")
        with HBoxLayout(gap="0.5em"):
            vuetify.VBtn("Convert", click=self.view_model.convert_Q)
            vuetify.VSpacer()
            vuetify.VBtn("Save Q", click=self.save_Q)
            FileUpload(
                v_model="ub_q_conversion.q_path",
                base_paths=["/HFIR", "/SNS"],
                label="Load Q",
                return_contents=False,
            )

    def save_Q(self):
        fd, path = tempfile.mkstemp(suffix=".nxs")
        os.close(fd)
        self.view_model.save_Q(path)
        with open(path, "rb") as f:
            data = f.read()
            self.js_download(("q.nxs", data))
        os.remove(path)


class PeaksTab:
    def __init__(self, view_model: UBViewModel):
        self.view_model = view_model

        self.create_ui()

    def create_ui(self):
        pass


class ViewsTab:
    def __init__(self, view_model: UBViewModel):
        self.view_model = view_model

        self.create_ui()

    def create_ui(self):
        pass


class ModulationTab:
    def __init__(self, view_model: UBViewModel):
        self.view_model = view_model

        self.create_ui()

    def create_ui(self):
        pass


class UBView:
    def __init__(self, server, view_model: UBViewModel):
        self.server = server
        self.server.state.active_ub_tab = 0
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

        self.connect_bindings()
        self.create_ui()

    def connect_bindings(self):
        self.view_model.q_conversion_bind.connect("ub_q_conversion")
        self.view_model.instrument_bind.connect("ub_instrument")
        self.view_model.peaks_bind.connect("ub_peaks")

        self.view_model.add_Q_viz_bind.connect(self.plotter.add_Q_viz)
        self.view_model.update_instrument_bind.connect(self.update_instrument_view)

    def create_ui(self):
        with GridLayout(classes="bg-white pa-2", columns=2, gap="2em", valign="start"):
            with VBoxLayout():
                self.visualization_panel = VisualizationPanel(
                    "active_ub_tab", self.pv_plotter, self.view_model.model, self.server
                )
                self.view_model.set_vis_viewmodel(self.visualization_panel.view_model)
            with VBoxLayout(classes="h-100"):
                with vuetify.VTabs(v_model="active_ub_tab", classes="pl-2"):
                    vuetify.VTab("Parameters", value=0)
                    vuetify.VTab("Peaks", value=1)
                    vuetify.VTab("Views", value=2)
                    vuetify.VTab("Modulation", value=3)
                with vuetify.VWindow(
                    v_model="active_ub_tab",
                    classes="border-sm border-primary h-100 pa-1 rounded",
                ):
                    with vuetify.VWindowItem(value=0):
                        ParametersTab(self.view_model)
                    with vuetify.VWindowItem(value=1):
                        PeaksTab(self.view_model)
                    with vuetify.VWindowItem(value=2):
                        ViewsTab(self.view_model)
                    with vuetify.VWindowItem(value=3):
                        ModulationTab(self.view_model)

    def update_instrument_view(self, result):
        self.plotter.update_instrument_view(result[0])
        self.plotter.update_roi_view(result[1])
        self.plotter.update_scan_view(result[1])
