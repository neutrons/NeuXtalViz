from enum import Enum
from typing import List, Tuple, Dict, Any, Optional

from pydantic import BaseModel, Field, field_validator

from NeuXtalViz.presenters.periodic_table import PeriodicTable
from NeuXtalViz.view_models.base_view_model import NeuXtalVizViewModel


class CrystalSystemOptions(str, Enum):
    triclinic = "Triclinic"
    monoclinic = "Monoclinic"
    orthorhombic = "Orthorhombic"
    tetragonal = "Tetragonal"
    trigonal = "Trigonal"
    hexagonal = "Hexagonal"
    cubic = "Cubic"


class CrystalStructureControls(BaseModel):
    crystal_system: CrystalSystemOptions = Field(default=CrystalSystemOptions.triclinic, title="Crystal System")
    space_group_options: List[str] = []
    space_group: str = ""
    setting_options: List[str] = []
    setting: str = ""
    lattice_constants: Optional[Tuple[float, float, float, float, float, float]] = None
    scatterers: List[List[str | float]] = [[]]
    constrain_parameters: List[bool] = []
    formula: str = ""
    z: Any = None
    vol: float = 0
    minimum_d_spacing: Optional[float] = Field(default=None, ge=0.1, le=1000)
    h: Optional[float] = Field(default=None, ge=-100, le=100)
    k: Optional[float] = Field(default=None, ge=-100, le=100)
    l: Optional[float] = Field(default=None, ge=-100, le=100)

    @field_validator("minimum_d_spacing", "h", "k", "l", mode='before')
    @classmethod
    def allow_empty_string(cls, v):
        if v == '':
            return None
        return v


class CrystalStructureAtoms(BaseModel):
    atoms_dict: Dict[Any, Any] = {}
    cell: Any = None


class CrystalStructureViewModel():
    def __init__(self, model, binding):
        self.cs_controls = CrystalStructureControls()
        self.cs_atoms = CrystalStructureAtoms()

        self.model = model
        self.vis_viewmodel = None
        self.binding = binding
        self.cs_controls_bind = binding.new_bind(
            self.cs_controls, callback_after_update=self.process_cs_updates
        )
        self.cs_atoms_bind = binding.new_bind(
            self.cs_atoms, callback_after_update=self.process_atoms_updates
        )
        self.cs_factors_bind = binding.new_bind()
        self.cs_equivalents_bind = binding.new_bind()


        return
        self.view.connect_hkl_calculator(self.calculate_hkl)
        self.view.connect_row_highligter(self.highlight_row)
        self.view.connect_lattice_parameters(self.update_parameters)
        self.view.connect_atom_table(self.set_atom_table)
        self.view.connect_save_INS(self.save_INS)
        self.view.connect_select_isotope(self.select_isotope)

        self.generate_groups()
        self.generate_settings()

    def process_cs_updates(self, results):
        for update in results.get("updated", []):
            match update:
                case "minimum_d_spacing":
                    print(self.cs_controls.minimum_d_spacing)
                case x if "lattice_constants" in x:
                    print("lattice_constants updated")
                    pass

    def process_atoms_updates(self, results):
        for update in results.get("updated", []):
            match update:
                case "crystal_system":
                    pass

    def set_vis_viewmodel(self, vis_viewmodel: NeuXtalVizViewModel):
        self.vis_viewmodel = vis_viewmodel

    def get_crystal_system_option_list(self):
        return [e.value for e in CrystalSystemOptions]

    def highlight_row(self):
        scatterer = self.view.get_scatterer()
        self.view.set_atom(scatterer)

    def set_atom_table(self):
        self.view.set_atom_table()
        self.update_atoms()

    def update_parameters(self):
        params = self.view.get_lattice_constants()
        params = self.model.update_parameters(params)
        self.model.update_lattice_parameters(*params)
        self.view.set_lattice_constants(params)
        vol = self.model.get_unit_cell_volume()
        self.view.set_unit_cell_volume(vol)

        atom_dict = self.model.generate_atom_positions()
        self.view.add_atoms(atom_dict)

        self.view.draw_cell(self.model.get_unit_cell_transform())
        self.view.set_transform(self.model.get_transform())

    def generate_groups(self):
        system = self.cs_controls.crystal_system
        self.cs_controls.space_group_options = self.model.generate_space_groups_from_crystal_system(system)
        #        self.view.update_space_groups(nos)
        self.generate_settings()

    def generate_settings(self):
        no = self.cs_controls.space_group
        self.cs_controls.setting_options = self.model.generate_settings_from_space_group(no)

    #        self.view.update_settings(settings)

    def load_CIF(self, filename):
        if filename:
            self.vis_viewmodel.update_processing()

            self.vis_viewmodel.update_processing("Loading CIF...", 10)

            self.model.load_CIF(filename)

            self.vis_viewmodel.update_processing("Loading CIF...", 50)
            self.cs_controls.crystal_system = self.model.get_crystal_system()
            self.cs_controls.space_group = self.model.get_space_group()
            self.cs_controls.setting = self.model.get_setting()
            self.cs_controls.lattice_constants = self.model.get_lattice_constants()
            self.cs_controls.scatterers = self.model.get_scatterers()

            #            self.view.set_crystal_system(crystal_system)
            self.generate_groups()
            #            self.view.set_space_group(space_group)
            self.generate_settings()
            #            self.view.set_setting(setting)
            #            self.view.set_lattice_constants(params)
            #            self.view.set_scatterers(scatterers)

            self.cs_controls.constrain_parameters = self.model.constrain_parameters()
            #            self.view.constrain_parameters(params)

            self.cs_atoms.atoms_dict = self.model.generate_atom_positions()

            #            self.view.add_atoms(atom_dict)

            self.vis_viewmodel.update_processing("Loading CIF...", 80)
            self.cs_atoms.cell = self.model.get_unit_cell_transform()

            self.vis_viewmodel.set_transform(self.model.get_transform())

            self.vis_viewmodel.update_oriented_lattice()

            self.cs_controls.formula, self.cs_controls.z = self.model.get_chemical_formula_z_parameter()

            self.vis_viewmodel.update_processing("Loading CIF...", 99)

            self.cs_controls.vol = self.model.get_unit_cell_volume()
            #            self.view.set_unit_cell_volume(vol)

            self.cs_controls_bind.update_in_view(self.cs_controls)
            self.cs_atoms_bind.update_in_view(self.cs_atoms)

            self.vis_viewmodel.update_complete("CIF loaded!")

        else:
            self.vis_viewmodel.update_invalid()

    def update_atoms(self):
        params = self.view.get_lattice_constants()
        setting = self.view.get_setting()
        scatterers = self.view.get_scatterers()

        self.model.set_crystal_structure(params, setting, scatterers)

        atom_dict = self.model.generate_atom_positions()
        self.view.add_atoms(atom_dict)

        form, z = self.model.get_chemical_formula_z_parameter()
        self.view.set_formula_z(form, z)

        self.view.draw_cell(self.model.get_unit_cell_transform())
        self.view.set_transform(self.model.get_transform())

    def calculate_F2(self):
        worker = self.binding.new_worker(self.calculate_F2_process)
        worker.connect_result(self.calculate_F2_complete)
        worker.connect_finished(self.vis_viewmodel.update_complete)
        worker.connect_progress(self.vis_viewmodel.update_processing)
        worker.start()

    def calculate_F2_complete(self, result):
        if result is not None:
            self.cs_factors_bind.update_in_view(result)

    def calculate_F2_process(self, progress):
        d_min = self.cs_controls.minimum_d_spacing

        params = self.cs_controls.lattice_constants

        if params is not None:
            progress("Processing...", 1)
            progress("Calculating factors...", 10)
            if d_min is None:
                d_min = min(params[0:2]) * 0.2

            hkls, ds, F2s = self.model.generate_F2(d_min)

            progress("Factors calculated...", 99)
            progress("Factors calculated!", 100)

            return hkls, ds, F2s

        else:
            progress("Invalid parameters.", 0)

    def calculate_hkl(self):
        worker = self.binding.new_worker(self.calculate_hkl_process)
        worker.connect_result(self.calculate_hkl_complete)
        worker.connect_finished(self.vis_viewmodel.update_complete)
        worker.connect_progress(self.vis_viewmodel.update_processing)
        worker.start()

    def calculate_hkl_complete(self, result):
        if result is not None:
            self.cs_equivalents_bind.update_in_view(result)

    def calculate_hkl_process(self, progress):
        hkl_ok = self.cs_controls.h is not None and self.cs_controls.k is not None and self.cs_controls.l is not None

        if hkl_ok:
            progress("Processing...", 1)

            progress("Calculating equivalents...", 10)

            hkls, d, F2 = self.model.calculate_F2(self.cs_controls.h, self.cs_controls.k, self.cs_controls.l)

            progress("Equivalents calculated...", 99)

            progress("Equivalents calculated!", 100)

            return hkls, d, F2

        else:
            progress("Invalid parameters.", 0)

    def select_isotope(self):
        atom = self.view.get_isotope()

        if atom != "":
            view = self.view.get_periodic_table()
            model = self.model.get_periodic_table(atom)

            self.periodic_table = PeriodicTable(view, model)
            self.periodic_table.view.connect_selected(self.update_selection)
            self.periodic_table.view.show()

    def update_selection(self, data):
        self.view.set_isotope(data)
        self.view.set_atom_table()
        self.update_atoms()

    def save_INS(self, filename):
        if filename:
            self.model.save_ins(filename)

    def save_ins_enabled(self):
        return self.model.has_crystal_structure()
