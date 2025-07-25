from functools import partial

from nova.mvvm.trame_binding import TrameBinding
from nova.trame.view.layouts import GridLayout, HBoxLayout
from trame.widgets import vuetify3 as vuetify

from NeuXtalViz.config.atoms import indexing, groups, isotopes
from NeuXtalViz.trame.views.atom import AtomView
from NeuXtalViz.view_models.crystal_structure_tools import CrystalStructureViewModel
from NeuXtalViz.view_models.periodic_table import PeriodicTableViewModel

colors = {
    "Transition Metals": "#A1C9F4",  # blue
    "Alkaline Earth Metals": "#FFB482",  # orange
    "Nonmetals": "#8DE5A1",  # green
    "Alkali Metals": "#FF9F9B",  # red
    "Lanthanides": "#D0BBFF",  # purple
    "Metalloids": "#DEBB9B",  # brown
    "Actinides": "#FAB0E4",  # pink
    "Other Metals": "#CFCFCF",  # gray
    "Halogens": "#FFFEA3",  # yellow
    "Noble Gases": "#B9F2F0",  # cyan
}


class PeriodicTableView:
    def __init__(self, server, crystal_view_model: CrystalStructureViewModel):
        self.server = server
        binding = TrameBinding(self.server.state)
        self.view_model = PeriodicTableViewModel(binding, crystal_view_model)
        crystal_view_model.set_perioric_table_viewmodel(self.view_model)

        self.view_model.pt_model_bind.connect("pt_model")
        self.create_ui()

    def atom_clicked(self, key: str):
        self.view_model.show_atom_dialog(key)

    def create_ui(self):
        grid = {}
        max_col = 0
        for key, (row, col) in indexing.items():
            grid.setdefault(row, {})[col] = key
            max_col = max(max_col, col)

        with vuetify.VDialog(
            v_model="pt_model.show_dialog",
            width="auto",
            update_modelValue="flushState('pt_model')",
        ):
            with vuetify.VCard(classes="text-center"):
                with HBoxLayout(classes="ma-2",halign="right"):
                    vuetify.VBtn(
                        "Close",
                        click="pt_model.show_dialog = False; flushState('pt_model')",
                    )
                with GridLayout(columns=max_col):
                    for row_idx in sorted(grid.keys()):
                        for col_idx in range(max_col):
                            key = grid[row_idx].get(col_idx + 1)
                            if key:
                                group = groups.get(key)
                                bg_color = colors[group]
                                disabled = isotopes.get(key) is None
                                (
                                    vuetify.VBtn(
                                        key,
                                        classes="ma-1",
                                        color=bg_color if not disabled else "lightgrey",
                                        disabled=disabled,
                                        style="height: 50px; width: 50px;",
                                        click=partial(self.atom_clicked, key),
                                    ),
                                )
                            else:
                                vuetify.VSheet()

        AtomView(self.server, self.view_model)
