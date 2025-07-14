import pyvista as pv
from nova.trame.view.components import InputField, RemoteFileInput
from nova.trame.view.layouts import GridLayout, VBoxLayout, HBoxLayout

from NeuXtalViz.components.visualization_panel.view_trame import VisualizationPanel
from NeuXtalViz.view_models.crystal_structure_tools import CrystalStructureViewModel, CrystalStructureAtoms
from NeuXtalViz.views.shared.crystal_structure_plotter import CrystalStructurePlotter


class CrystalStructureView:
    def __init__(self, server, view_model: CrystalStructureViewModel):
        self.server = server
        self.view_model = view_model
        self.view_model.cs_controls_bind.connect("cs_controls")
        self.view_model.cs_cis_file_bind.connect("cs_cif_file")
        self.view_model.cs_atoms_bind.connect(self.on_atoms_update)
        self.view_model.cs_factors_bind.connect("cs_factors")
        self.view_model.cs_equivalents_bind.connect("cs_equivalents")
        self.view_model.cs_scatterers_bind.connect("cs_scatterers")

        plotter = pv.Plotter(off_screen=True)
        plotter.background_color = "#f0f0f0"
        self.plotter = CrystalStructurePlotter(plotter, self.highlight_row)

        self.create_ui()

    def on_atoms_update(self, atoms: CrystalStructureAtoms):
        self.plotter.add_atoms(atoms.atoms_dict)
        self.plotter.draw_cell(atoms.cell)


    def highlight_row(self):
        pass

    @property
    def state(self):
        return self.server.state

    def create_ui(self):
        with GridLayout(classes="bg-white pa-2", columns=2):
            self.visualization_panel = VisualizationPanel("crystal_structure",
                                                          self.plotter.pv_plotter,
                                                          self.view_model.model,
                                                          self.server)
            self.view_model.set_vis_viewmodel(self.visualization_panel.view_model)
            with VBoxLayout():
                with HBoxLayout(valign="center"):
                    InputField(v_model="cs_controls.crystal_system", readonly=True, type="select")
                    InputField(v_model="cs_controls.space_group", items="cs_controls.space_group_options",
                               readonly=True, type="select")
                    InputField(v_model="cs_controls.setting", items="cs_controls.setting_options", readonly=True,
                               type="select")
                    RemoteFileInput(
                        v_model="cs_cif_file.path",
                        base_paths=["/Users/35y/projects/ndip/tool-sources/NeuXtalViz/tests/data", "/HFIR", "/SNS"],
                        extensions=["cif"],
                        input_props={"label": "Load CIF"},
                    )
