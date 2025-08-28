import pyvista as pv

from matplotlib.figure import Figure
from nova.trame.view.components import FileUpload, InputField, RemoteFileInput
from nova.trame.view.components.visualization import MatplotlibFigure
from nova.trame.view.layouts import GridLayout, HBoxLayout, VBoxLayout
from trame.widgets import html
from trame.widgets import vuetify3 as vuetify

from NeuXtalViz.components.visualization_panel.view_trame import VisualizationPanel
from NeuXtalViz.view_models.experiment_planner import ExperimentPlannerViewModel
from NeuXtalViz.views.shared.planner_plotter import PlannerPlotter
from NeuXtalViz.views.shared.planner_plots import (
    plot_instrument,
    plot_instrument_alternate,
    plot_statistics,
)


class CoverageTab:
    def __init__(self, server, view_model: ExperimentPlannerViewModel):
        self.server = server
        self.server.state.coverage_active_tab = 0
        self.view_model = view_model
        self.view_model.ep_statistics_bind.connect(self.plot_statistics)

        self.fig_cov = Figure(layout="constrained")
        self.ax_cov = self.fig_cov.subplots(3, 1, sharex=True)
        self.ax_cov[2].set_xlabel("Resolution Shell [Å]")
        self.ax_cov[0].set_ylabel("Completeness [%]")
        self.ax_cov[1].set_ylabel("Multiplicity")
        self.ax_cov[2].set_ylabel("Unique Reflections")

        self.create_ui()

    def create_ui(self):
        with GridLayout(columns=4, gap="0.5em"):
            FileUpload(
                v_model="ep_settings.ub_path",
                base_paths=["/HFIR", "/SNS"],
                extensions=[".mat"],
                label="Load UB",
                return_contents=False,
            )
            InputField(v_model="ep_settings.crystal_system", type="select")
            InputField(
                v_model="ep_settings.point_group",
                items=("ep_settings.point_groups",),
                type="select",
            )
            InputField(
                v_model="ep_settings.lattice_centering",
                items=("ep_settings.lattice_centerings",),
                type="select",
            )
        with GridLayout(columns=3, gap="0.5em"):
            InputField(v_model="ep_params.instrument", type="select")
            with HBoxLayout(gap="0.5em"):
                vuetify.VLabel("λ:")
                InputField(v_model="ep_params.wl_min")
                InputField(
                    v_model="ep_params.wl_max",
                    disabled=("ep_params.no_wl_max",),
                )
            with HBoxLayout(gap="0.5em"):
                InputField(v_model="ep_params.d_min")
                vuetify.VLabel("Å")
        with vuetify.VTabs(v_model="coverage_active_tab"):
            vuetify.VTab("Goniometers", value=0)
            vuetify.VTab("Calibration/Motors", value=1)
            vuetify.VTab("Plan", value=2)
        with vuetify.VWindow(v_model="coverage_active_tab"):
            with vuetify.VWindowItem(value=0):
                GoniometersTab(self.server, self.view_model)
            with vuetify.VWindowItem(value=1):
                MotorsTab(self.server, self.view_model)
            with vuetify.VWindowItem(value=2):
                PlanTab(self.server, self.view_model)
        self.stats_view = MatplotlibFigure(
            figure=self.fig_cov, classes="mt-2", webagg=True
        )

    def plot_statistics(self, stats):
        plot_statistics(self.ax_cov, *stats)
        self.stats_view.update(self.fig_cov)


class GoniometersTab:
    def __init__(self, server, view_model: ExperimentPlannerViewModel):
        self.server = server
        self.view_model = view_model

        self.create_ui()

    def create_ui(self):
        with VBoxLayout(classes="h-100", valign="start"):
            with HBoxLayout():
                InputField(
                    "ep_goniometers.current_mode",
                    items=("ep_goniometers.modes",),
                    type="select",
                )
            with HBoxLayout(
                classes="border-lg border-primary rounded-sm",
                valign="start",
            ):
                vuetify.VDataTable(
                    classes="h-100",
                    disable_sort=True,
                    headers=("ep_goniometers.goniometer_headers",),
                    hide_default_footer=True,
                    items=("ep_goniometers.goniometer_table",),
                    items_per_page=-1,
                )


class MotorsTab:
    def __init__(self, server, view_model: ExperimentPlannerViewModel):
        self.server = server
        self.view_model = view_model

        self.create_ui()

    def create_ui(self):
        with VBoxLayout(classes="h-100", valign="start"):
            RemoteFileInput(
                v_model="ep_motors.detector_file",
                base_paths=["/HFIR", "/SNS"],
                return_contents=False,
            )
            RemoteFileInput(
                v_model="ep_motors.mask_file",
                base_paths=["/HFIR", "/SNS"],
                return_contents=False,
            )
            with HBoxLayout(
                classes="border-lg border-primary rounded-sm",
                valign="start",
            ):
                vuetify.VDataTable(
                    classes="h-100",
                    disable_sort=True,
                    headers=("ep_motors.motor_table_headers",),
                    hide_default_footer=True,
                    items=("ep_motors.motor_table",),
                    items_per_page=-1,
                )


class PlanTab:
    def __init__(self, server, view_model: ExperimentPlannerViewModel):
        self.server = server
        self.view_model = view_model

        self.create_ui()

    def create_ui(self):
        with VBoxLayout(classes="h-100", valign="start"):
            with HBoxLayout(gap="0.5em", valign="center"):
                InputField("ep_plan.title")
                InputField(
                    "ep_plan.counting_option",
                    items=("ep_plan.counting_options",),
                    type="select",
                )
                InputField("ep_plan.count")
                vuetify.VBtn(
                    "Update Highlighted",
                    click=self.view_model.update_selected_plan_table_rows,
                )
                InputField("ep_plan.settings")
                vuetify.VBtn(
                    "Optimize Coverage", click=self.view_model.optimize_coverage
                )
            with HBoxLayout(
                classes="border-lg border-primary rounded-sm overflow-y-auto",
                style="max-height: 200px;",
                valign="start",
            ):
                with vuetify.VDataTable(
                    v_model="ep_plan.plan_table_selected_rows",
                    classes="h-100",
                    disable_sort=True,
                    headers=("ep_plan.plan_table_headers",),
                    hide_default_footer=True,
                    items=("ep_plan.plan_table",),
                    items_per_page=-1,
                    item_value="index",
                    select_strategy="multiple",
                    show_select=True,
                    raw_attrs=[
                        '@click:row="(_, {internalItem, toggleSelect}) => toggleSelect(internalItem)"'
                    ],
                    update_modelValue="flushState('ep_plan')",
                ):
                    with vuetify.Template(
                        raw_attrs=['v-slot:item.wait_for="{ item }"']
                    ):
                        with html.Td():
                            vuetify.VSelect(
                                v_if="item",
                                model_value=("item.wait_for",),
                                items=("ep_plan.counting_options",),
                                update_modelValue="ep_plan.plan_table[item.index]['wait_for'] = $event; flushState('ep_plan');",
                            )
            with HBoxLayout(
                classes="border-lg border-primary rounded-sm",
                valign="start",
            ):
                vuetify.VDataTable(
                    classes="h-100",
                    disable_sort=True,
                    headers=("ep_plan.mesh_table_headers",),
                    hide_default_footer=True,
                    items=("ep_plan.mesh_table",),
                    items_per_page=-1,
                )


class PeakTab:
    def __init__(self, server, view_model: ExperimentPlannerViewModel):
        self.server = server
        self.view_model = view_model
        self.view_model.ep_peak_plot_instrument_bind.connect(self.plot_instrument)
        self.view_model.ep_peak_inst_bind.connect(self.update_inst)

        self.fig_inst = Figure(layout="constrained")
        self.ax_inst = self.fig_inst.subplots(1, 1)
        self.ax_inst.clear()
        self.ax_inst.invert_xaxis()

        self.cb_inst = None
        self.cb_inst_alt = None

        self.create_ui()

    def create_ui(self):
        with HBoxLayout(gap="0.25em", valign="center"):
            InputField("ep_peak_settings.h1")
            InputField("ep_peak_settings.k1")
            InputField("ep_peak_settings.l1")
            vuetify.VBtn("Individual Peak", click=self.view_model.calculate_single)
            InputField("ep_peak_settings.allow_equivalents", type="checkbox")
            InputField("ep_peak_settings.horizontal")
            InputField("ep_peak_settings.vertical")
            InputField("ep_peak_settings.intersect")
        with HBoxLayout(gap="0.25em", valign="center"):
            InputField("ep_peak_settings.h2")
            InputField("ep_peak_settings.k2")
            InputField("ep_peak_settings.l2")
            vuetify.VBtn("Individual Peak", click=self.view_model.calculate_single_alt)
            vuetify.VBtn("Simultaneous Peaks", click=self.view_model.calculate_double)
            InputField("ep_peak_settings.horizontal_alt")
            InputField("ep_peak_settings.vertical_alt")
            InputField("ep_peak_settings.intersect_alt")
        self.inst_view = MatplotlibFigure(self.fig_inst, webagg=True)
        with GridLayout(columns=5):
            InputField(
                "ep_peak_table.angles_option",
                items=("ep_peak_table.angles_options",),
                type="select",
            )
            InputField("ep_peak_table.angles", column_span=3)
            vuetify.VBtn("Add Orientation", click=self.view_model.add_orientation)
        with HBoxLayout(
            classes="border-lg border-primary rounded-sm",
            valign="start",
        ):
            vuetify.VDataTable(
                classes="h-100",
                disable_sort=True,
                headers=("ep_peak_table.peak_table_headers",),
                hide_default_footer=True,
                items=("ep_peak_table.peak_table",),
                items_per_page=-1,
            )

    def plot_instrument(self, res):
        if len(res) == 5:
            self.cb_inst, self.cb_inst_alt = plot_instrument(
                self.fig_inst, self.ax_inst, self.cb_inst, self.cb_inst_alt, *res
            )
        elif len(res) == 8:
            self.cb_inst, self.cb_inst_alt = plot_instrument_alternate(
                self.fig_inst, self.ax_inst, self.cb_inst, self.cb_inst_alt, *res
            )
        self.fig_inst.canvas.mpl_connect("button_press_event", self.on_press_inst)
        self.inst_view.update(self.fig_inst)

    def plot_instrument_alternate(self, res):
        gamma_inst, nu_inst, gamma_1, nu_1, lamda_1, gamma_2, nu_2, lamda_2 = res
        plot_instrument_alternate(
            self.fig_inst,
            self.ax_inst,
            gamma_inst,
            nu_inst,
            gamma_1,
            nu_1,
            lamda_1,
            gamma_2,
            nu_2,
            lamda_2,
        )
        self.fig_inst.canvas.mpl_connect("button_press_event", self.on_press_inst)
        self.inst_view.update(self.fig_inst)

    def on_press_inst(self, event):
        if event.inaxes == self.ax_inst and self.fig_inst.canvas.toolbar.mode == "":
            horz, vert = event.xdata, event.ydata
            self.view_model.process_peak_plot_event(horz, vert)

    def update_inst(self):
        for line in self.ax_inst.lines:
            line.remove()

        horz, vert = (
            self.view_model.peak_settings.horizontal,
            self.view_model.peak_settings.vertical,
        )

        self.ax_inst.axvline(x=horz, color="k", linestyle="--")
        self.ax_inst.axhline(y=vert, color="k", linestyle="--")

        horz_alt = self.view_model.peak_settings.horizontal_alt
        vert_alt = self.view_model.peak_settings.vertical_alt

        if horz_alt is not None and vert_alt is not None:
            self.ax_inst.axvline(x=horz_alt, color="k", linestyle=":")
            self.ax_inst.axhline(y=vert_alt, color="k", linestyle=":")


class ExperimentPlannerView:
    def __init__(self, server, view_model: ExperimentPlannerViewModel):
        self.server = server
        self.server.state.planner_active_tab = 0
        self.view_model = view_model
        self.view_model.ep_goniometers_bind.connect("ep_goniometers")
        self.view_model.ep_motors_bind.connect("ep_motors")
        self.view_model.ep_params_bind.connect("ep_params")
        self.view_model.ep_plan_bind.connect("ep_plan")
        self.view_model.ep_settings_bind.connect("ep_settings")
        self.view_model.ep_peak_bind.connect(self.plot_peak)
        self.view_model.ep_peak_settings_bind.connect("ep_peak_settings")
        self.view_model.ep_peak_table_bind.connect("ep_peak_table")

        self.cb_inst = None
        self.cb_inst_alt = None

        self.pv_plotter = pv.Plotter(off_screen=True)
        self.pv_plotter.background_color = "#f0f0f0"
        self.plotter = PlannerPlotter(self.pv_plotter)

        self.create_ui()
        self.view_model.initialize()

    def create_ui(self):
        with GridLayout(
            classes="bg-white h-100 pa-2", columns=2, gap="2em", valign="start"
        ):
            with VBoxLayout():
                self.visualization_panel = VisualizationPanel(
                    "planner", self.pv_plotter, self.view_model.model, self.server
                )
                self.view_model.set_vis_viewmodel(self.visualization_panel.view_model)
            with VBoxLayout(classes="h-100 overflow-x-scroll"):
                with vuetify.VTabs(v_model="planner_active_tab"):
                    vuetify.VTab("Coverage", value=0)
                    vuetify.VTab("Peak", value=1)
                with vuetify.VWindow(v_model="planner_active_tab", classes="h-100"):
                    with vuetify.VWindowItem(classes="h-100", value=0):
                        CoverageTab(self.server, self.view_model)
                    with vuetify.VWindowItem(value=1):
                        PeakTab(self.server, self.view_model)

    def plot_peak(self, peak_dict):
        self.plotter.add_peaks(peak_dict)
