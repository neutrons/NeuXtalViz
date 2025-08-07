import pyvista as pv

from nova.trame.view.components import FileUpload, InputField
from nova.trame.view.layouts import GridLayout, HBoxLayout, VBoxLayout
from trame.widgets import html
from trame.widgets import vuetify3 as vuetify

from NeuXtalViz.components.visualization_panel.view_trame import VisualizationPanel
from NeuXtalViz.view_models.sample_tools import SampleViewModel
from NeuXtalViz.views.shared.crystal_structure_plotter import CrystalStructurePlotter


class SampleView:
    def __init__(self, server, view_model: SampleViewModel):
        self.server = server
        self.view_model = view_model
        self.view_model.absorption_parameters_bind.connect("s_absorption_parameters")
        self.view_model.constraints_bind.connect("s_constraints")
        self.view_model.face_indices_bind.connect("s_face_indices")
        self.view_model.goniometer_editor_bind.connect("s_goniometer_editor")
        self.view_model.goniometer_table_bind.connect("s_goniometer_table")
        self.view_model.material_parameters_bind.connect("s_material_parameters")
        self.view_model.sample_bind.connect("s_sample")

        self.pv_plotter = pv.Plotter(off_screen=True)
        self.pv_plotter.background_color = "#f0f0f0"
        self.plotter = CrystalStructurePlotter(self.pv_plotter, lambda *args: None)

        self.view_model.add_sample_bind.connect(self.plotter.add_sample)

        self.view_model.init_view()
        self.create_ui()

    def create_ui(self):
        with GridLayout(classes="bg-white pa-2", columns=3, gap="2em", valign="start"):
            with VBoxLayout(column_span=2):
                self.visualization_panel = VisualizationPanel(
                    "sample", self.pv_plotter, self.view_model.model, self.server
                )
                self.view_model.set_vis_viewmodel(self.visualization_panel.view_model)
            with VBoxLayout(classes="h-100"):
                with GridLayout(columns=3, gap="0.5em"):
                    InputField(v_model="s_sample.shape", type="select")
                    FileUpload(
                        v_model="s_sample.path",
                        base_paths=["/HFIR", "/SNS"],
                        extensions=[".mat"],
                        label="Load UB",
                        return_contents=False,
                    )
                    vuetify.VBtn("Add Sample", click=self.view_model.add_sample)
                with HBoxLayout(gap="0.5em"):
                    InputField("s_sample.width", disabled=("s_constraints[0]",))
                    InputField("s_sample.height", disabled=("s_constraints[1]",))
                    InputField("s_sample.thickness", disabled=("s_constraints[2]",))
                    vuetify.VLabel("cm")
                with HBoxLayout(
                    classes="border-lg border-primary flex-1-1 h-0 overflow-y-auto rounded-sm"
                ):
                    vuetify.VDataTable(
                        v_model="s_goniometer_table.selected_index",
                        classes="h-100",
                        disable_sort=True,
                        headers=("s_goniometer_table.headers",),
                        hide_default_footer=True,
                        items=("s_goniometer_table.rows",),
                        items_per_page=-1,
                        item_value="index",
                        select_strategy="single",
                        show_select=True,
                        raw_attrs=[
                            '@click:row="(_, {internalItem, toggleSelect}) => toggleSelect(internalItem)"'
                        ],
                        update_modelValue="flushState('s_goniometer_table')",
                    )
                with GridLayout(columns=6, gap="0.5em"):
                    InputField("s_goniometer_editor.name", disabled=True)
                    InputField("s_goniometer_editor.x")
                    InputField("s_goniometer_editor.y")
                    InputField("s_goniometer_editor.z")
                    InputField("s_goniometer_editor.sense")
                    InputField("s_goniometer_editor.angle")
                html.Div("Face Indexing", classes="text-center w-100")
                with GridLayout(columns=4):
                    vuetify.VLabel("Along Thickness")
                    InputField("s_face_indices.hu")
                    InputField("s_face_indices.ku")
                    InputField("s_face_indices.lu")
                    vuetify.VLabel("In-plane Lateral")
                    InputField("s_face_indices.hv")
                    InputField("s_face_indices.kv")
                    InputField("s_face_indices.lv")
                with HBoxLayout(gap="0.5em"):
                    InputField("s_material_parameters.chemical_formula")
                    InputField("s_material_parameters.z_parameter")
                    InputField("s_material_parameters.volume")
                    vuetify.VLabel("Å^3")
                with GridLayout(columns=2, gap="0.5em"):
                    InputField("s_absorption_parameters.sigma_s", disabled=True)
                    with HBoxLayout(gap="0.5em"):
                        InputField("s_absorption_parameters.sigma_a", disabled=True)
                        vuetify.VLabel("barn", style="width: 40px")
                    InputField("s_absorption_parameters.mu_s", disabled=True)
                    with HBoxLayout(gap="0.5em"):
                        InputField("s_absorption_parameters.mu_a", disabled=True)
                        vuetify.VLabel("1/cm", style="width: 40px")
                    with HBoxLayout(gap="0.5em"):
                        InputField("s_absorption_parameters.N", disabled=True)
                        vuetify.VLabel("atoms", style="width: 40px")
                    with HBoxLayout(gap="0.5em"):
                        InputField("s_absorption_parameters.M", disabled=True)
                        vuetify.VLabel("g/mol", style="width: 40px")
                    with HBoxLayout(gap="0.5em"):
                        InputField("s_absorption_parameters.n", disabled=True)
                        vuetify.VLabel("1/Å^3", style="width: 40px")
                    with HBoxLayout(gap="0.5em"):
                        InputField("s_absorption_parameters.rho", disabled=True)
                        vuetify.VLabel("g/cm^3", style="width: 40px")
                    with HBoxLayout(gap="0.5em"):
                        InputField("s_absorption_parameters.V", disabled=True)
                        vuetify.VLabel("cm^3", style="width: 40px")
                    with HBoxLayout(gap="0.5em"):
                        InputField("s_absorption_parameters.m", disabled=True)
                        vuetify.VLabel("g", style="width: 40px")
