from functools import partial

from nova.mvvm.trame_binding import TrameBinding
from trame.widgets import vuetify3 as vuetify

from NeuXtalViz.config.atoms import indexing, groups, isotopes
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
    "Noble Gases": "#B9F2F0",
}  # cyan


class PeriodicTableView:
    def __init__(self, server, crystal_view_model: CrystalStructureViewModel):
        self.server = server
        binding = TrameBinding(self.server.state)
        self.view_model = PeriodicTableViewModel(binding, crystal_view_model)
        self.view_model.pt_model_bind.connect("pt_model")
        self.create_ui()

    def atom_clicked(self, key: str):
        print(key)

    def create_ui(self):
        grid = {}
        for key, (row, col) in indexing.items():
            grid.setdefault(row, {})[col] = key

        with vuetify.VDialog(v_model="pt_model.show", width="auto", update_modelValue="flushState('pt_model')"):
            with vuetify.VCard(classes="text-center"):
                for row_idx in sorted(grid.keys()):
                    with vuetify.VRow(no_gutters=True):
                        for col_idx in range(max(grid[row_idx].keys()) + 1):
                            key = grid[row_idx].get(col_idx)
                            if key:
                                group = groups.get(key)
                                color = colors.get(group, "white")
                                disabled = isotopes.get(key) is None
                                with vuetify.VCol(cols="auto"):
                                    vuetify.VBtn(
                                        key,
                                        style=f"background-color: {color} !important; min-width: 50px; min-height: 50px;",
                                        disabled=disabled,
                                        click=partial(self.atom_clicked, key)),
                            else:
                                vuetify.VCol(cols="auto")  # empty spacer

            with vuetify.VBtn(icon=True, click="pt_model.show = False;flushState('pt_model')"):
                vuetify.VIcon("mdi-close")
