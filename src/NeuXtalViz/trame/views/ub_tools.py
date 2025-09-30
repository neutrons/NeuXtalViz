import os
import tempfile

import pyvista as pv
from matplotlib.backends.backend_webagg import FigureCanvasWebAgg
from matplotlib.figure import Figure
from nova.trame.view.components import FileUpload, InputField, RemoteFileInput
from nova.trame.view.components.visualization import MatplotlibFigure
from nova.trame.view.layouts import GridLayout, HBoxLayout, VBoxLayout
from trame.widgets import client
from trame.widgets import vuetify3 as vuetify

from NeuXtalViz.components.visualization_panel.view_trame import VisualizationPanel
from NeuXtalViz.view_models.ub_tools import UBViewModel
from NeuXtalViz.views.shared.ub_plotter import UBPlotter


class ParametersTab:
    def __init__(self, server, view_model: UBViewModel):
        self.server = server
        self.server.state.ub_parameters_peaks_tab = 0
        self.server.state.ub_parameters_ub_tab = 0
        self.server.state.ub_parameters_info_tab = 0
        self.view_model = view_model

        self.js_download = client.JSEval(
            exec="utils.download($event[0], $event[1], 'text/plain')"
        ).exec
        self.create_ui()

    def create_ui(self):
        with VBoxLayout(classes="border-sm border-primary pa-1 rounded"):
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
                InputField(
                    v_model="ub_q_conversion.lorentz_correction", type="checkbox"
                )
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

        with vuetify.VTabs(v_model="ub_parameters_peaks_tab", classes="pl-2"):
            vuetify.VTab("Find Peaks", value=0)
            vuetify.VTab("Index Peaks", value=1)
            vuetify.VTab("Predict Peaks", value=2)
            vuetify.VTab("Integrate Peaks", value=3)
            vuetify.VTab("Filter Peaks", value=4)
        with vuetify.VWindow(
            v_model="ub_parameters_peaks_tab",
            classes="border-sm border-primary flex-0-1 mb-1 pa-1 rounded",
        ):
            with vuetify.VWindowItem(value=0):
                with GridLayout(columns=7, gap="0.25em"):
                    InputField("ub_peaks_controls.find.max_peaks")
                    InputField("ub_peaks_controls.find.min_distance")
                    InputField("ub_peaks_controls.find.min_density")
                    InputField("ub_peaks_controls.find.max_spacing")
                    InputField("ub_peaks_controls.find.edge_pixels")
                    InputField("ub_peaks_controls.find.avoid_aluminum", type="checkbox")
                    vuetify.VBtn("Find", click=self.view_model.find_peaks)
            with vuetify.VWindowItem(value=1):
                with GridLayout(columns=5, gap="0.25em"):
                    InputField("ub_peaks_controls.index.tolerance")
                    InputField("ub_peaks_controls.index.satellite_tolerance")
                    InputField("ub_peaks_controls.index.satellite", type="checkbox")
                    InputField("ub_peaks_controls.index.round_hkl", type="checkbox")
                    vuetify.VBtn("Index", click=self.view_model.index_peaks)
            with vuetify.VWindowItem(value=2):
                with GridLayout(columns=6, gap="0.25em"):
                    InputField("ub_peaks_controls.predict.centering", type="select")
                    InputField("ub_peaks_controls.predict.min_d_spacing")
                    InputField("ub_peaks_controls.predict.satellite_min_d_spacing")
                    InputField("ub_peaks_controls.predict.satellite", type="checkbox")
                    InputField("ub_peaks_controls.predict.edge_pixels")
                    vuetify.VBtn("Predict", click=self.view_model.predict_peaks)
            with vuetify.VWindowItem(value=3):
                with GridLayout(columns=6, gap="0.25em"):
                    InputField("ub_peaks_controls.integrate.radius")
                    InputField("ub_peaks_controls.integrate.inner_factor")
                    InputField("ub_peaks_controls.integrate.outer_factor")
                    InputField("ub_peaks_controls.integrate.centroid", type="checkbox")
                    InputField(
                        "ub_peaks_controls.integrate.adaptive_envelope",
                        type="checkbox",
                    )
                    vuetify.VBtn("Integrate", click=self.view_model.integrate_peaks)
            with vuetify.VWindowItem(value=4):
                with HBoxLayout(gap="0.25em", valign="center"):
                    InputField("ub_peaks_controls.filter.filter", type="select")
                    InputField("ub_peaks_controls.filter.comparison", type="select")
                    InputField("ub_peaks_controls.filter.value")
                    vuetify.VBtn("Filter", click=self.view_model.filter_peaks)
        with HBoxLayout(gap="0.5em"):
            vuetify.VSpacer()
            vuetify.VBtn("Save Peaks", click=self.save_peaks)
            FileUpload(
                v_model="ub_peaks_controls.peaks_path",
                base_paths=["/HFIR", "/SNS"],
                label="Load Peaks",
                return_contents=False,
            )

        with vuetify.VTabs(v_model="ub_parameters_ub_tab", classes="pl-2"):
            vuetify.VTab("Calculate UB", value=0)
            vuetify.VTab("Transform UB", value=1)
            vuetify.VTab("Refine UB", value=2)
        with vuetify.VWindow(
            v_model="ub_parameters_ub_tab",
            classes="border-sm border-primary flex-1-1 mb-1 pa-1 rounded",
        ):
            with vuetify.VWindowItem(value=0):
                with VBoxLayout(height="100%"):
                    with GridLayout(columns=2, gap="0.5em"):
                        InputField("ub_controls.calculate.tolerance")
                        InputField("ub_controls.calculate.max_scalar_error")
                    with HBoxLayout(
                        classes="border-lg border-primary mb-1 rounded-sm", stretch=True
                    ):
                        vuetify.VDataTable(
                            v_model="ub_controls.calculate.selected_index",
                            classes="flex-1-1 h-100 w-0",
                            disable_sort=True,
                            headers=("ub_controls.calculate.table_headers",),
                            hide_default_footer=True,
                            items=("ub_controls.calculate.table_contents",),
                            items_per_page=-1,
                            item_value="index",
                            select_strategy="single",
                            show_select=True,
                            raw_attrs=[
                                '@click:row="(_, {internalItem, toggleSelect}) => toggleSelect(internalItem)"'
                            ],
                            update_modelValue="flushState('ub_controls')",
                        )
                    with GridLayout(columns=6, gap="0.25em"):
                        vuetify.VBtn(
                            "Conventional", click=self.view_model.find_conventional
                        )
                        InputField("ub_controls.calculate.min_const")
                        InputField("ub_controls.calculate.max_const")
                        vuetify.VBtn("Primitive", click=self.view_model.find_niggli)
                        InputField("ub_controls.calculate.form", readonly=True)
                        vuetify.VBtn("Select", click=self.view_model.select_cell)
            with vuetify.VWindowItem(value=1):
                with GridLayout(columns=3, halign="center"):
                    vuetify.VLabel("h")
                    vuetify.VLabel("k")
                    vuetify.VLabel("l")
                with GridLayout(columns=3, gap="0.5em"):
                    with HBoxLayout():
                        vuetify.VLabel("h':")
                        InputField("ub_controls.transform.t11")
                    InputField("ub_controls.transform.t12")
                    InputField("ub_controls.transform.t13")
                    with HBoxLayout():
                        vuetify.VLabel("k':")
                        InputField("ub_controls.transform.t21")
                    InputField("ub_controls.transform.t22")
                    InputField("ub_controls.transform.t23")
                    with HBoxLayout():
                        vuetify.VLabel("l':")
                        InputField("ub_controls.transform.t31")
                    InputField("ub_controls.transform.t32")
                    InputField("ub_controls.transform.t33")
                with GridLayout(columns=4, gap="0.5em"):
                    vuetify.VBtn("Transform", click=self.view_model.transform_UB)
                    InputField("ub_controls.transform.tolerance")
                    InputField("ub_controls.transform.lattice", type="select")
                    InputField(
                        "ub_controls.transform.symmetry",
                        items=("ub_controls.transform.symmetry_options",),
                        type="select",
                    )
            with vuetify.VWindowItem(value=2):
                with HBoxLayout(gap="0.5em", valign="center"):
                    InputField("ub_controls.refine.tolerance")
                    InputField("ub_controls.refine.optimize", type="select")
                    vuetify.VBtn("Refine", click=self.view_model.refine_UB)
        with HBoxLayout(gap="0.5em"):
            vuetify.VSpacer()
            vuetify.VBtn("Save UB", click=self.save_UB)
            FileUpload(
                v_model="ub_controls.ub_path",
                base_paths=["/HFIR", "/SNS"],
                label="Load UB",
                return_contents=False,
            )

        with vuetify.VTabs(v_model="ub_parameters_info_tab", classes="pl-2"):
            vuetify.VTab("Lattice Parameters", value=0)
            vuetify.VTab("Sample Orientation", value=1)
            vuetify.VTab("Modulation Parameters", value=2)
        with vuetify.VWindow(
            v_model="ub_parameters_info_tab",
            classes="border-sm border-primary flex-0-1 pa-1 rounded",
        ):
            with vuetify.VWindowItem(value=0):
                with GridLayout(columns=3, gap="0.5em"):
                    InputField(v_model="ub_parameters.lattice.a_display")
                    InputField(v_model="ub_parameters.lattice.b_display")
                    InputField(v_model="ub_parameters.lattice.c_display")
                    InputField(v_model="ub_parameters.lattice.alpha_display")
                    InputField(v_model="ub_parameters.lattice.beta_display")
                    InputField(v_model="ub_parameters.lattice.gamma_display")
            with vuetify.VWindowItem(value=1):
                with GridLayout(columns=3, halign="center"):
                    vuetify.VLabel("a*")
                    vuetify.VLabel("b*")
                    vuetify.VLabel("c*")
                with GridLayout(columns=3, gap="0.5em"):
                    with HBoxLayout():
                        vuetify.VLabel("y:")
                        InputField("ub_parameters.sample_directions.wh")
                    InputField("ub_parameters.sample_directions.wk")
                    InputField("ub_parameters.sample_directions.wl")
                    with HBoxLayout():
                        vuetify.VLabel("z:")
                        InputField("ub_parameters.sample_directions.uh")
                    InputField("ub_parameters.sample_directions.uk")
                    InputField("ub_parameters.sample_directions.ul")
                    with HBoxLayout():
                        vuetify.VLabel("x:")
                        InputField("ub_parameters.sample_directions.vh")
                    InputField("ub_parameters.sample_directions.vk")
                    InputField("ub_parameters.sample_directions.vl")
            with vuetify.VWindowItem(value=2):
                with GridLayout(columns=4, halign="center"):
                    vuetify.VLabel("Δh")
                    vuetify.VLabel("Δk")
                    vuetify.VLabel("Δl")
                    vuetify.VLabel("Max Order")
                with GridLayout(columns=4, gap="0.5em"):
                    with HBoxLayout():
                        vuetify.VLabel("1:")
                        InputField("ub_parameters.modulation.dh1")
                    InputField("ub_parameters.modulation.dk1")
                    InputField("ub_parameters.modulation.dl1")
                    InputField("ub_parameters.modulation.max_order")
                    with HBoxLayout():
                        vuetify.VLabel("1:")
                        InputField("ub_parameters.modulation.dh2")
                    InputField("ub_parameters.modulation.dk2")
                    InputField("ub_parameters.modulation.dl2")
                    InputField("ub_parameters.modulation.cross_terms", type="checkbox")
                    with HBoxLayout():
                        vuetify.VLabel("1:")
                        InputField("ub_parameters.modulation.dh3")
                    InputField("ub_parameters.modulation.dk3")
                    InputField("ub_parameters.modulation.dl3")

    def save_peaks(self):
        fd, path = tempfile.mkstemp(suffix=".nxs")
        os.close(fd)
        self.view_model.save_peaks(path)
        with open(path, "rb") as f:
            data = f.read()
            self.js_download(("peaks.nxs", data))
        os.remove(path)

    def save_Q(self):
        fd, path = tempfile.mkstemp(suffix=".nxs")
        os.close(fd)
        self.view_model.save_Q(path)
        with open(path, "rb") as f:
            data = f.read()
            self.js_download(("q.nxs", data))
        os.remove(path)

    def save_UB(self):
        fd, path = tempfile.mkstemp(suffix=".mat")
        os.close(fd)
        self.view_model.save_UB(path)
        with open(path, "rb") as f:
            data = f.read()
            self.js_download(("ub.mat", data))
        os.remove(path)


class PeaksTab:
    def __init__(self, view_model: UBViewModel):
        self.view_model = view_model

        self.create_ui()

    def create_ui(self):
        with GridLayout(columns=5, halign="center"):
            vuetify.VLabel("h")
            vuetify.VLabel("k")
            vuetify.VLabel("l")
            vuetify.VLabel("d[Å]")
            vuetify.VLabel("ϕ[°]")
        with GridLayout(columns=5, gap="0.25em"):
            InputField("ub_peaks.h1")
            InputField("ub_peaks.k1")
            InputField("ub_peaks.l1")
            InputField("ub_peaks.d1")
            InputField("ub_peaks.phi")
            InputField("ub_peaks.h2")
            InputField("ub_peaks.k2")
            InputField("ub_peaks.l2")
            InputField("ub_peaks.d2")
            vuetify.VBtn("Calculate", click=self.view_model.calculate_peaks)
        with HBoxLayout(
            classes="border-lg border-primary mb-1 rounded-sm", stretch=True
        ):
            vuetify.VDataTable(
                v_model="ub_peaks.highlighted_peaks",
                classes="flex-1-1 h-100 w-0",
                disable_sort=True,
                headers=("ub_peaks.peaks_headers",),
                hide_default_footer=True,
                items=("ub_peaks.peaks",),
                items_per_page=-1,
                item_value="index",
                select_strategy="single",
                show_select=True,
                raw_attrs=[
                    '@click:row="(_, {internalItem, toggleSelect}) => toggleSelect(internalItem)"'
                ],
                update_modelValue="flushState('ub_peaks')",
            )
        with GridLayout(columns=5):
            InputField("ub_peaks.h")
            InputField("ub_peaks.k")
            InputField("ub_peaks.l")
            InputField("ub_peaks.index", disabled=True)
            InputField("ub_peaks.total", disabled=True)
        with GridLayout(columns=6):
            InputField("ub_peaks.int_h")
            InputField("ub_peaks.int_k")
            InputField("ub_peaks.int_l")
            InputField("ub_peaks.int_m")
            InputField("ub_peaks.int_n")
            InputField("ub_peaks.int_p")
        with GridLayout(columns=4):
            InputField("ub_peaks.intensity")
            InputField("ub_peaks.sigma")
            InputField("ub_peaks.d")
            InputField("ub_peaks.lambda_value")
            InputField("ub_peaks.run")
            InputField("ub_peaks.bank")
            InputField("ub_peaks.row")
            InputField("ub_peaks.col")


class ViewsTab:
    def __init__(self, server, view_model: UBViewModel, fig_slice, fig_inst, fig_scan):
        self.server = server
        self.server.state.ub_views_tab = 0
        self.view_model = view_model
        self.fig_slice = fig_slice
        self.fig_inst = fig_inst
        self.fig_scan = fig_scan

        self.create_ui()

    def create_ui(self):
        with vuetify.VTabs(v_model="ub_views_tab", classes="pl-2"):
            vuetify.VTab("Slice View", value=0)
            vuetify.VTab("Detector View", value=1)
        with vuetify.VWindow(
            v_model="ub_views_tab",
            classes="border-sm border-primary pa-1 rounded",
        ):
            with vuetify.VWindowItem(value=0):
                with VBoxLayout(height="100%"):
                    with GridLayout(columns=3, halign="center"):
                        vuetify.VLabel("h")
                        vuetify.VLabel("k")
                        vuetify.VLabel("l")
                    with GridLayout(columns=3, gap="0.25em"):
                        with HBoxLayout():
                            vuetify.VLabel("1:")
                            InputField("ub_slice.U1")
                        InputField("ub_slice.V1")
                        InputField("ub_slice.W1")
                        with HBoxLayout():
                            vuetify.VLabel("2:")
                            InputField("ub_slice.U2")
                        InputField("ub_slice.V2")
                        InputField("ub_slice.W2")
                        with HBoxLayout():
                            vuetify.VLabel("3:")
                            InputField("ub_slice.U3")
                        InputField("ub_slice.V3")
                        InputField("ub_slice.W3")
                    with GridLayout(columns=5, gap="0.25em"):
                        vuetify.VBtn("Convert", click=self.view_model.convert_to_hkl)
                        InputField("ub_slice.plane", type="select")
                        InputField("ub_slice.value")
                        InputField("ub_slice.thickness")
                        InputField("ub_slice.width")
                    with HBoxLayout(stretch=True):
                        with HBoxLayout(width="85%", stretch=True):
                            self.slice_view = MatplotlibFigure(
                                self.fig_slice, webagg=True
                            )
                        vuetify.VSlider(
                            model_value=("ub_slice.vmin_slider",),
                            classes="my-6",
                            direction="vertical",
                            max=100,
                            min=0,
                            step=1,
                            type="slider",
                            __events=["end"],
                            end=(
                                self.view_model.set_slider,
                                "['vmin_slider', $event]",
                            ),
                        )
                        vuetify.VSlider(
                            model_value=("ub_slice.vmax_slider",),
                            classes="my-6",
                            direction="vertical",
                            max=100,
                            min=0,
                            step=1,
                            type="slider",
                            __events=["end"],
                            end=(
                                self.view_model.set_slider,
                                "['vmax_slider', $event]",
                            ),
                        )
                    with GridLayout(columns=3, gap="0.25em"):
                        InputField("ub_slice.cbar", type="select")
                        InputField("ub_slice.clip_type", type="select")
                        InputField("ub_slice.scale", type="select")
            with vuetify.VWindowItem(value=1):
                with VBoxLayout(height="100%"):
                    with GridLayout(columns=7, gap="0.25em"):
                        InputField(
                            "ub_instrument.data",
                            items=("ub_instrument.data_options",),
                            type="select",
                        )
                        vuetify.VBtn("Check hkl", click=self.view_model.calculate_hkl)
                        InputField("ub_instrument.check_h")
                        InputField("ub_instrument.check_k")
                        InputField("ub_instrument.check_l")
                        InputField("ub_instrument.d_min")
                        InputField("ub_instrument.d_max")
                    with HBoxLayout(stretch=True):
                        self.inst_view = MatplotlibFigure(self.fig_inst, webagg=True)
                    with GridLayout(columns=4):
                        InputField("ub_instrument.horizontal_angle")
                        InputField("ub_instrument.horizontal_roi")
                        InputField("ub_instrument.vertical_angle")
                        InputField("ub_instrument.vertical_roi")
                    with HBoxLayout(stretch=True):
                        self.scan_view = MatplotlibFigure(self.fig_scan, webagg=True)
                    with HBoxLayout(gap="0.5em", valign="center"):
                        InputField(
                            "ub_instrument.diffraction",
                            label=("ub_instrument.diffraction_label",),
                        )
                        vuetify.VBtn("Add Peak", click=self.view_model.add_peak)


class ModulationTab:
    def __init__(self, view_model: UBViewModel, fig_clust):
        self.view_model = view_model
        self.fig_clust = fig_clust

        self.create_ui()

    def create_ui(self):
        with HBoxLayout(gap="0.5em", valign="center"):
            vuetify.VBtn("Cluster", click=self.view_model.cluster)
            InputField("ub_mod.max_distance")
            InputField("ub_mod.min_samples")
        with HBoxLayout(
            classes="border-lg border-primary mb-1 rounded-sm", stretch=True
        ):
            vuetify.VDataTable(
                classes="flex-1-1 h-100 w-0",
                disable_sort=True,
                headers=("ub_mod.headers",),
                hide_default_footer=True,
                items=("ub_mod.centroids",),
                items_per_page=-1,
            )
        with HBoxLayout(stretch=True):
            MatplotlibFigure(self.fig_clust, webagg=True)


class UBView:
    def __init__(self, server, view_model: UBViewModel):
        self.server = server
        self.server.state.active_ub_tab = 0
        self.view_model = view_model

        self.fig_slice = Figure(layout="constrained")
        self.fig_inst = Figure(layout="constrained")
        self.fig_scan = Figure(layout="constrained")
        self.fig_clust = Figure(layout="constrained")

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
        self.view_model.ub_controls_bind.connect("ub_controls")
        self.view_model.instrument_bind.connect("ub_instrument")
        self.view_model.modulation_clusters_bind.connect("ub_mod")
        self.view_model.parameters_bind.connect("ub_parameters")
        self.view_model.peaks_bind.connect("ub_peaks")
        self.view_model.peaks_controls_bind.connect("ub_peaks_controls")
        self.view_model.q_conversion_bind.connect("ub_q_conversion")
        self.view_model.slice_bind.connect("ub_slice")

        self.view_model.add_Q_viz_bind.connect(self.plotter.add_Q_viz)
        self.view_model.highlight_peak_bind.connect(self.highlight_peak)
        self.view_model.highlight_peaks_bind.connect(lambda *args: None)
        self.view_model.update_cluster_peaks_bind.connect(
            self.plotter.add_cluster_peaks
        )
        self.view_model.update_instrument_bind.connect(self.update_instrument_view)
        self.view_model.update_instrument_bind.connect(self.update_instrument_view)
        self.view_model.update_slice_bind.connect(self.update_slice)
        self.view_model.update_slice_colorbar_bind.connect(
            self.plotter.update_slice_colorbar
        )

    def create_ui(self):
        with GridLayout(
            classes="bg-white pa-2", columns=2, gap="2em", height="100%", stretch=True
        ):
            with VBoxLayout(stretch=True):
                self.visualization_panel = VisualizationPanel(
                    "active_ub_tab", self.pv_plotter, self.view_model.model, self.server
                )
                self.view_model.set_vis_viewmodel(self.visualization_panel.view_model)
            with VBoxLayout(stretch=True):
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
                        with VBoxLayout(height="100%"):
                            ParametersTab(self.server, self.view_model)
                    with vuetify.VWindowItem(value=1):
                        with VBoxLayout(height="100%"):
                            PeaksTab(self.view_model)
                    with vuetify.VWindowItem(value=2):
                        with VBoxLayout(height="100%"):
                            ViewsTab(
                                self.server,
                                self.view_model,
                                self.fig_slice,
                                self.fig_inst,
                                self.fig_scan,
                            )
                    with vuetify.VWindowItem(value=3):
                        with VBoxLayout(height="100%"):
                            ModulationTab(self.view_model, self.fig_clust)

    def update_instrument_view(self, result):
        self.plotter.update_instrument_view(result[0])
        self.plotter.update_roi_view(result[1])
        self.plotter.update_scan_view(result[1])

    def highlight_peak(self, peaks):
        self.plotter.highlight_peak(peaks.last_highlight)
        self.visualization_panel.set_position(peaks.position)

    def update_slice(self, data):
        slice_dict, cmap, scale = data
        vmin, vmax = self.plotter.update_slice(slice_dict, cmap, scale)
        self.view_model.set_vlims(vmin, vmax)
