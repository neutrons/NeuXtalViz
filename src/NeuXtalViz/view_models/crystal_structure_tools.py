from enum import Enum
from typing import List, Tuple, Dict, Any, Optional

from pydantic import BaseModel, Field, field_validator

from NeuXtalViz.view_models.base_view_model import NeuXtalVizViewModel
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from NeuXtalViz.view_models.periodic_table import PeriodicTableViewModel


class CrystalSystemOptions(str, Enum):
    triclinic = "Triclinic"
    monoclinic = "Monoclinic"
    orthorhombic = "Orthorhombic"
    tetragonal = "Tetragonal"
    trigonal = "Trigonal"
    hexagonal = "Hexagonal"
    cubic = "Cubic"


class CrystalStructureScatterers(BaseModel):
    scatterers: List[List[str | float]] = [[]]


class CrystalStructureControls(BaseModel):
    crystal_system: CrystalSystemOptions = Field(default=CrystalSystemOptions.triclinic, title="Crystal System")
    space_group_options: List[str] = []
    space_group: str = ""
    setting_options: List[str] = []
    setting: str = ""
    lattice_constants: Optional[Tuple[float, float, float, float, float, float]] = None
    current_scatterer: Optional[List[str | float]] = None
    current_scatterer_row: Optional[int] = None
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


class SelectedAtom(BaseModel):
    name: Optional[str] = None


class CrystalStructureViewModel():
    def __init__(self, model, binding):
        self.cs_controls = CrystalStructureControls()
        self.cs_atoms = CrystalStructureAtoms()
        self.cs_selected_atom = SelectedAtom()
        self.cs_scatterers = CrystalStructureScatterers()

        self.model = model
        self.vis_viewmodel = None
        self.binding = binding
        self.cs_controls_bind = binding.new_bind(
            self.cs_controls, callback_after_update=self.process_cs_updates
        )
        self.cs_scatterers_bind = binding.new_bind()

        self.cs_atoms_bind = binding.new_bind(
            self.cs_atoms, callback_after_update=self.process_atoms_updates
        )
        self.cs_factors_bind = binding.new_bind()
        self.cs_equivalents_bind = binding.new_bind()

    def key_updated(self, key, partial, results) -> bool:
        for update in results.get("updated", []):
            if partial and (f"{key}." in update or f"{key}[" in update):
                return True
            if not partial and key == update:
                return True
        return False

    def process_cs_updates(self, results):
        if self.key_updated("lattice_constants", True, results):
            self.update_parameters()
        if self.key_updated("current_scatterer_row", False, results):
            self.select_row()
        if self.key_updated("current_scatterer", True, results):
            self.update_atoms()

    def process_atoms_updates(self, results):
        for update in results.get("updated", []):
            match update:
                case "crystal_system":
                    pass

    def update_selected_atom(self, atom_name):
        self.cs_selected_atom.name = atom_name
        self.cs_controls.current_scatterer[0] = self.cs_selected_atom.name
        self.update_atoms()


    def set_vis_viewmodel(self, vis_viewmodel: NeuXtalVizViewModel):
        self.vis_viewmodel = vis_viewmodel

    def set_perioric_table_viewmodel(self, pt_viewmodel: 'PeriodicTableViewModel'):
        self.pt_viewmodel = pt_viewmodel

    def get_crystal_system_option_list(self):
        return [e.value for e in CrystalSystemOptions]

    def select_row(self):
        if self.cs_controls.current_scatterer_row is not None:
            self.cs_controls.current_scatterer = self.cs_scatterers.scatterers[self.cs_controls.current_scatterer_row]
            self.cs_controls_bind.update_in_view(self.cs_controls)

    def update_parameters(self):
        params = self.cs_controls.lattice_constants
        params = self.model.update_parameters(params)
        self.model.update_lattice_parameters(*params)
        self.cs_controls.lattice_constants = params
        vol = self.model.get_unit_cell_volume()
        self.cs_controls.vol = vol
        atom_dict = self.model.generate_atom_positions()
        self.cs_atoms.atoms_dict = atom_dict
        self.cs_atoms.cell = self.model.get_unit_cell_transform()

        self.vis_viewmodel.set_transform(self.model.get_transform())
        self.cs_controls_bind.update_in_view(self.cs_controls)
        self.cs_atoms_bind.update_in_view(self.cs_atoms)

    def generate_groups(self):
        system = self.cs_controls.crystal_system
        self.cs_controls.space_group_options = self.model.generate_space_groups_from_crystal_system(system)

    def generate_settings(self):
        no = self.cs_controls.space_group
        self.cs_controls.setting_options = self.model.generate_settings_from_space_group(no)

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
            self.cs_scatterers.scatterers = self.model.get_scatterers()

            self.generate_groups()
            self.generate_settings()

            self.cs_controls.constrain_parameters = self.model.constrain_parameters()
            self.cs_atoms.atoms_dict = self.model.generate_atom_positions()

            self.vis_viewmodel.update_processing("Loading CIF...", 80)
            self.cs_atoms.cell = self.model.get_unit_cell_transform()

            self.vis_viewmodel.set_transform(self.model.get_transform())

            self.vis_viewmodel.update_oriented_lattice()

            self.cs_controls.formula, self.cs_controls.z = self.model.get_chemical_formula_z_parameter()

            self.vis_viewmodel.update_processing("Loading CIF...", 99)

            self.cs_controls.vol = self.model.get_unit_cell_volume()

            self.cs_controls_bind.update_in_view(self.cs_controls)
            self.cs_atoms_bind.update_in_view(self.cs_atoms)
            self.cs_scatterers_bind.update_in_view(self.cs_scatterers)
            self.vis_viewmodel.update_complete("CIF loaded!")

        else:
            self.vis_viewmodel.update_invalid()

    def update_atoms(self):
        self.cs_scatterers.scatterers[self.cs_controls.current_scatterer_row] = self.cs_controls.current_scatterer
        self.model.set_crystal_structure(self.cs_controls.lattice_constants, self.cs_controls.setting,
                                         self.cs_scatterers.scatterers)

        self.cs_atoms.atoms_dict = self.model.generate_atom_positions()
        self.cs_controls.formula, self.cs_controls.z = self.model.get_chemical_formula_z_parameter()
        self.cs_atoms.cell = self.model.get_unit_cell_transform()

        self.vis_viewmodel.set_transform(self.model.get_transform())
        self.cs_controls_bind.update_in_view(self.cs_controls)
        self.cs_atoms_bind.update_in_view(self.cs_atoms)

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
        if self.cs_controls.current_scatterer is None:
            return
        atom = self.cs_controls.current_scatterer[0]
        if atom:
            self.cs_selected_atom.name = atom
            self.pt_viewmodel.show_table(atom)

    def update_selection(self, data):
        self.view.set_isotope(data)
        self.view.set_atom_table()
        self.update_atoms()

    def save_INS(self, filename):
        if filename:
            self.model.save_ins(filename)

    def save_ins_enabled(self):
        return self.model.has_crystal_structure()
