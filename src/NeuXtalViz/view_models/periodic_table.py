from nova.common import events
from pydantic import BaseModel

from NeuXtalViz.models.periodic_table import PeriodicTableModel
from NeuXtalViz.shared.signals import NeuXtalVizSignals


class PeriodicTableParams(BaseModel):
    atom: str = "H"
    show_dialog: bool = False


class PeriodicTableViewModel:
    def __init__(self, binding):
        self.model = PeriodicTableModel()
        self.model_params = PeriodicTableParams()
        self.binding = binding
        self.pt_model_bind = binding.new_bind(self.model_params)
        pt_event = events.get_event(NeuXtalVizSignals.SHOW_PERIODIC_TABLE)
        pt_event.connect(self.show_table)
        atom_event = events.get_event(NeuXtalVizSignals.ATOM_UPDATE)
        atom_event.connect(self.use_isotope)

    def show_table(self, _sender, atom: str):
        self.model_params.atom = atom
        self.model_params.show_dialog = True
        self.pt_model_bind.update_in_view(self.model_params)

    def show_atom_dialog(self, atom):
        event = events.get_event(NeuXtalVizSignals.SHOW_ATOM_TABLE)
        event.send_sync("PeriodicTableViewModel", atom=atom)

    def use_isotope(self, _sender, **_kwargs):
        self.model_params.show_dialog = False
        self.pt_model_bind.update_in_view(self.model_params)
