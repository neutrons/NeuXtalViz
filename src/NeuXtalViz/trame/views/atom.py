from nova.mvvm.trame_binding import TrameBinding
from nova.trame.view.components import InputField
from nova.trame.view.layouts import HBoxLayout, VBoxLayout
from trame.widgets import vuetify3 as vuetify

from NeuXtalViz.view_models.atom import AtomViewModel
from NeuXtalViz.view_models.periodic_table import PeriodicTableViewModel


class AtomView:
    def __init__(self, server, pt_view_model: PeriodicTableViewModel):
        self.server = server
        binding = TrameBinding(self.server.state)
        self.view_model = AtomViewModel(binding, pt_view_model)
        pt_view_model.set_atom_viewmodel(self.view_model)
        self.view_model.atom_params_bind.connect("atoms")
        self.create_ui()

    def create_ui(self):
        with vuetify.VDialog(v_model="atoms.show_dialog", width="500px", update_modelValue="flushState('atoms')"):
            with vuetify.VCard():
                with vuetify.VBtn(icon=True, click="atoms.show_dialog = False;flushState('atoms')"):
                    vuetify.VIcon("mdi-close")
                with HBoxLayout():
                    InputField("atoms.atom_dict['z']", readonly=True)
                    InputField(v_model="atoms.current_isotope", items="atoms.isotope_numbers", type="select")
                    InputField("atoms.atom_dict['abundance']", readonly=True)
                    vuetify.VBtn("Use Isotope", click=self.view_model.use_isotope)
                with HBoxLayout():
                    # if I remove widths, it is a mess
                    with VBoxLayout(width=600):
                        InputField("atoms.symbol", readonly=True)
                        InputField("atoms.name", readonly=True)
                        InputField("atoms.atom_dict['mass']", readonly=True)
                    with VBoxLayout(width=600):
                        InputField("atoms.neutron_dict['sigma_tot']", readonly=True)
                        InputField("atoms.neutron_dict['sigma_coh']", readonly=True)
                        InputField("atoms.neutron_dict['sigma_inc']", readonly=True)
                    with VBoxLayout(width=600):
                        vuetify.VLabel(text=(
                        "String(atoms.neutron_dict['b_coh_re']) + '+' + String(atoms.neutron_dict['b_coh_im']) + 'i'",))
                        vuetify.VLabel(text=(
                        "String(atoms.neutron_dict['b_inc_re']) + '+' + String(atoms.neutron_dict['b_inc_im']) + 'i'",))
