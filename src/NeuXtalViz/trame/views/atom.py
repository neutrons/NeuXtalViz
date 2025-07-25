from nova.mvvm.trame_binding import TrameBinding
from nova.trame.view.components import InputField
from nova.trame.view.layouts import GridLayout, HBoxLayout, VBoxLayout
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
        with vuetify.VDialog(
            v_model="atoms.show_dialog",
            width=400,
            update_modelValue="flushState('atoms')",
        ):
            with vuetify.VCard(classes="pa-2", width="100%"):
                with HBoxLayout(halign="right"):
                    vuetify.VBtn(
                        "Close",
                        classes="ma-2",
                        click="atoms.show_dialog = False; flushState('atoms')",
                    )
                with HBoxLayout(valign="center"):
                    vuetify.VLabel(text=("atoms.atom_dict['z']",))
                    InputField(
                        v_model="atoms.current_isotope",
                        items="atoms.isotope_numbers",
                        type="select",
                        variant="outlined",
                    )
                    vuetify.VLabel(
                        text=("atoms.atom_dict['abundance']",), classes="mr-4"
                    )
                    vuetify.VBtn("Use Isotope", click=self.view_model.use_isotope)
                with GridLayout(
                    columns=3, height=100, halign="center", valign="center"
                ):
                    vuetify.VLabel(text=("atoms.symbol",))
                    vuetify.VLabel(
                        text=("`&sigma;(tot) = ${atoms.neutron_dict['sigma_tot']}`",)
                    )
                    vuetify.VSpacer()
                    vuetify.VLabel(text=("atoms.name",))
                    vuetify.VLabel(
                        text=("`&sigma;(coh) = ${atoms.neutron_dict['sigma_coh']}`",)
                    )
                    vuetify.VLabel(
                        text=(
                            "'b(coh) =' + String(atoms.neutron_dict['b_coh_re']) + '+' + String(atoms.neutron_dict['b_coh_im']) + 'i'",
                        )
                    )
                    vuetify.VLabel(text=("atoms.atom_dict['mass']",))
                    vuetify.VLabel(
                        text=("`&sigma;(inc) = ${atoms.neutron_dict['sigma_inc']}`",),
                    )
                    vuetify.VLabel(
                        text=(
                            "'b(inc) =' + String(atoms.neutron_dict['b_inc_re']) + '+' + String(atoms.neutron_dict['b_inc_im']) + 'i'",
                        )
                    )
