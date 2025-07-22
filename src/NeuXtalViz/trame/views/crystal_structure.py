import os
import tempfile

import pyvista as pv
from nova.trame.view.components import InputField, RemoteFileInput
from nova.trame.view.layouts import GridLayout, VBoxLayout, HBoxLayout
from pyvista import Plotter
from trame.widgets import client
from trame.widgets import vuetify3 as vuetify

from NeuXtalViz.components.visualization_panel.view_trame import VisualizationPanel
from NeuXtalViz.view_models.crystal_structure_tools import CrystalStructureViewModel, CrystalStructureAtoms
from NeuXtalViz.views.shared.crystal_structure_plotter import CrystalStructurePlotter


class StructureTab:
    def __init__(self, server, view_model: CrystalStructureViewModel, pv_plotter: Plotter):
        self.server = server
        self.ctrl = server.controller
        self.server = server
        self.view_model = view_model
        self.view_model.cs_controls_bind.connect("cs_controls")
        self.view_model.cs_cis_file_bind.connect("cs_cif_file")
        self.view_model.cs_atoms_bind.connect(self.on_atoms_update)
        self.view_model.cs_factors_bind.connect("cs_factors")
        self.view_model.cs_equivalents_bind.connect("cs_equivalents")
        self.view_model.cs_scatterers_bind.connect("cs_scatterers")
        self.plotter = CrystalStructurePlotter(pv_plotter, self.highlight_row)

        self.js_download = client.JSEval(
            exec="utils.download($event[0], $event[1], 'text/plain')"
        ).exec
        self.create_ui()

    def on_atoms_update(self, atoms: CrystalStructureAtoms):
        self.plotter.add_atoms(atoms.atoms_dict)
        self.plotter.draw_cell(atoms.cell)

    def highlight_row(self, row):
        self.view_model.select_row(row)

    @property
    def state(self):
        return self.server.state

    def save_ins(self):
        if self.view_model.save_ins_enabled():
            fd, path = tempfile.mkstemp(suffix=".ins")
            os.close(fd)
            self.view_model.save_INS(path)
            with open(path, "rb") as f:
                data = f.read()
                self.js_download(("cs.ins", data))
            os.remove(path)

    def create_ui(self):
        with HBoxLayout(valign="center"):
            InputField(v_model="cs_controls.crystal_system", disabled=True, type="select")
            InputField(v_model="cs_controls.space_group", items="cs_controls.space_group_options",
                       disabled=True, type="select")
            InputField(v_model="cs_controls.setting", items="cs_controls.setting_options", disabled=True,
                       type="select")
            RemoteFileInput(
                v_model="cs_cif_file.path",
                base_paths=["/Users/35y/projects/ndip/tool-sources/NeuXtalViz/tests/data", "/HFIR", "/SNS"],
                extensions=["cif"],
                input_props={"label": "CIF File"},
            )
            vuetify.VBtn("Save INS", click=self.save_ins)
        with HBoxLayout(valign="center"):
            InputField(v_model="cs_controls.lattice_constants.a",
                       debounce=100,
                       disabled=("cs_controls.constrain_parameters[0]",))
            InputField(v_model="cs_controls.lattice_constants.b",
                       debounce=100,
                       disabled=("cs_controls.constrain_parameters[1]",))
            InputField(v_model="cs_controls.lattice_constants.c",
                       debounce=100,
                       disabled=("cs_controls.constrain_parameters[2]",))
        with HBoxLayout(valign="center"):
            InputField(v_model="cs_controls.lattice_constants.alpha",
                       debounce=100,
                       disabled=("cs_controls.constrain_parameters[3]",))
            InputField(v_model="cs_controls.lattice_constants.beta",
                       debounce=100,
                       disabled=("cs_controls.constrain_parameters[4]",))
            InputField(v_model="cs_controls.lattice_constants.gamma",
                       debounce=100,
                       disabled=("cs_controls.constrain_parameters[5]",))
        with HBoxLayout(valign="center"):
            vuetify.VDataTable(
                v_model="cs_controls.current_scatterer_row",
                items=("cs_scatterers.scatterer_dict",),
                item_value='index',
                headers=("cs_scatterers.scatterer_header",),
                select_strategy="single",
                show_select=True,
                update_modelValue=f"flushState('cs_controls')",
                disable_sort=True,
            )
        with HBoxLayout(valign="center"):
            vuetify.VBtn(text=("cs_controls.current_scatterer[0]",), width=50)
            InputField(v_model="cs_controls.current_scatterer[1]")
            InputField(v_model="cs_controls.current_scatterer[2]")
            InputField(v_model="cs_controls.current_scatterer[3]")
            InputField(v_model="cs_controls.current_scatterer[4]")
            InputField(v_model="cs_controls.current_scatterer[5]")
        with HBoxLayout(valign="center"):
            InputField(v_model="cs_controls.formula", readonly=True)
            InputField(v_model="cs_controls.z", readonly=True)
            InputField(v_model="cs_controls.vol", readonly=True)


class CrystalStructureView:
    def __init__(self, server, view_model: CrystalStructureViewModel):
        self.server = server
        self.view_model = view_model
        self.server.state.structure_active_tab = 0
        plotter = pv.Plotter(off_screen=True)
        plotter.background_color = "#f0f0f0"
        self.pv_plotter = plotter

        self.create_ui()

    def create_ui(self):
        with GridLayout(classes="bg-white pa-2", columns=2):
            self.visualization_panel = VisualizationPanel("crystal_structure",
                                                          self.pv_plotter,
                                                          self.view_model.model,
                                                          self.server)
            self.view_model.set_vis_viewmodel(self.visualization_panel.view_model)
            with VBoxLayout():
                with vuetify.VTabs(v_model="structure_active_tab", classes="pl-4", density="compact"):
                    vuetify.VTab("Structure", value=0)
                    vuetify.VTab("Factors", value=1)
                with vuetify.VWindow(v_model="structure_active_tab"):
                    with vuetify.VWindowItem(value=0):
                        StructureTab(self.server, self.view_model, self.pv_plotter)
                    with vuetify.VWindowItem(value=1):
                        pass
