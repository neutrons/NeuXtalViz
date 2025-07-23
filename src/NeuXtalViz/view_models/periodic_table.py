from typing import TYPE_CHECKING

from pydantic import BaseModel

from NeuXtalViz.models.periodic_table import PeriodicTableModel
from NeuXtalViz.view_models.crystal_structure_tools import CrystalStructureViewModel

if TYPE_CHECKING:
    from NeuXtalViz.view_models.atom import AtomViewModel

class PeriodicTableParams(BaseModel):
    atom: str = "H"
    show: bool = True


class PeriodicTableViewModel:
    def __init__(self, binding, crystal_view_model: CrystalStructureViewModel):
        self.model = PeriodicTableModel()
        self.model_params = PeriodicTableParams()
        self.binding = binding
        self.crystal_view_model = crystal_view_model
        self.pt_model_bind = binding.new_bind(self.model_params)

    def show_table(self, atom: str):
        self.model_params.atom = atom
        self.model_params.show = True
        self.pt_model_bind.update_in_view(self.model_params)

    def show_atom_dialog(self, atom):
        self.atom_view_model.show_dialog(atom)

    def set_atom_viewmodel(self, atom_view_model: 'AtomViewModel'):
        self.atom_view_model = atom_view_model

    def use_isotope(self, isotope_name):
        self.model_params.show = False
        self.pt_model_bind.update_in_view(self.model_params)
        self.crystal_view_model.update_selected_atom(isotope_name)
