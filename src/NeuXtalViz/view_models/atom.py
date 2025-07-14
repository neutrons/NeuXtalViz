from typing import List, Dict, Any

from pydantic import BaseModel

from NeuXtalViz.models.periodic_table import AtomModel
from NeuXtalViz.view_models.periodic_table import PeriodicTableViewModel


class AtomParams(BaseModel):
    symbol: str = ""
    name: str = ""
    isotope_numbers: List[int] = []
    current_isotope: int = 0
    atom_dict: Dict[str, Any] = {}
    neutron_dict: Dict[str, Any] = {}
    view_dialog: bool = False

class AtomViewModel:
    def __init__(self, binding, periodic_table_view_model: PeriodicTableViewModel):
        self.periodic_table_view_model = periodic_table_view_model
        self.atom_model = None
        self.atom_params = AtomParams()
        self.atom_params_bind = binding.new_bind(self.atom_params,
                                                 callback_after_update=self.process_atom_params_update)

    def process_atom_params_update(self, results):
        for update in results.get("updated", []):
            if update == "current_isotope":
                self.update_params_from_model(reset_isotope=False)
                self.atom_params_bind.update_in_view(self.atom_params)

    def update_params_from_model(self, reset_isotope: bool):
        self.atom_params.symbol, self.atom_params.name = self.atom_model.get_symbol_name()
        self.atom_params.isotope_numbers = self.atom_model.get_isotope_numbers()
        if reset_isotope:
            self.atom_params.current_isotope = 0
        isotope = 0
        if self.atom_params.current_isotope < len(self.atom_params.isotope_numbers):
            isotope = self.atom_params.isotope_numbers[self.atom_params.current_isotope]
        self.atom_model.generate_data(isotope)
        self.atom_params.atom_dict = self.atom_model.atom_dict
        self.atom_params.neutron_dict = self.atom_model.neutron_dict

    def show_dialog(self, atom):
        self.atom_model = AtomModel(atom)
        self.update_params_from_model(reset_isotope=True)
        self.atom_params.view_dialog = True
        self.atom_params_bind.update_in_view(self.atom_params)

    def use_isotope(self):
        self.atom_params.view_dialog = False
        self.atom_params_bind.update_in_view(self.atom_params)
        self.periodic_table_view_model.use_isotope(self.atom_params.symbol)
