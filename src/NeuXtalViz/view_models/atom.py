from typing import List, Dict, Any

from nova.common import events
from pydantic import BaseModel

from NeuXtalViz.models.periodic_table import AtomModel
from NeuXtalViz.shared.signals import NeuXtalVizSignals


class AtomParams(BaseModel):
    symbol: str = ""
    name: str = ""
    isotope_numbers: List[int] = []
    current_isotope: int = 0
    atom_dict: Dict[str, Any] = {}
    neutron_dict: Dict[str, Any] = {}
    show_dialog: bool = False


class AtomViewModel:
    def __init__(self, binding):
        self.atom_model = None
        self.atom_params = AtomParams()
        self.atom_params_bind = binding.new_bind(self.atom_params,
                                                 callback_after_update=self.process_atom_params_update)

        atom_event = events.get_event(NeuXtalVizSignals.SHOW_ATOM_TABLE)
        atom_event.connect(self.show_dialog)

    def process_atom_params_update(self, results):
        for update in results.get("updated", []):
            if update == "current_isotope":
                self.update_params_from_model(reset_isotope=False)
                self.atom_params_bind.update_in_view(self.atom_params)

    def update_params_from_model(self, reset_isotope: bool):
        self.atom_params.symbol, self.atom_params.name = self.atom_model.get_symbol_name()
        self.atom_params.isotope_numbers = self.atom_model.get_isotope_numbers()
        if reset_isotope:
            self.atom_params.current_isotope = self.atom_params.isotope_numbers[
                0] if self.atom_params.isotope_numbers else 0
        isotope = self.atom_params.current_isotope
        self.atom_model.generate_data(isotope)
        self.atom_params.atom_dict = self.atom_model.atom_dict
        self.atom_params.neutron_dict = self.atom_model.neutron_dict

    def show_dialog(self, _sender, atom):
        self.atom_model = AtomModel(atom)
        self.update_params_from_model(reset_isotope=True)
        self.atom_params.show_dialog = True
        self.atom_params_bind.update_in_view(self.atom_params)

    def use_isotope(self):
        self.atom_params.show_dialog = False
        self.atom_params_bind.update_in_view(self.atom_params)
        atom_event = events.get_event(NeuXtalVizSignals.ATOM_UPDATE)
        atom_event.send_sync("AtomViewModel", atom_name=self.atom_params.symbol)
