from PyQt5.QtCore import Qt, pyqtSignal
from nova.mvvm.pyqt5_binding import PyQt5Binding
from qtpy.QtWidgets import (
    QWidget,
    QPushButton,
    QButtonGroup,
    QLabel,
    QHBoxLayout,
    QGridLayout,
)

from NeuXtalViz.config.atoms import indexing, groups, isotopes
from NeuXtalViz.qt.new_views.atom import AtomView
from NeuXtalViz.view_models.crystal_structure_tools import CrystalStructureViewModel
from NeuXtalViz.view_models.periodic_table import PeriodicTableViewModel, PeriodicTableParams

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


class PeriodicTableView(QWidget):
    selection = pyqtSignal(str)

    def __init__(self, crystal_view_model: CrystalStructureViewModel, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout()

        table = self.__init_table()

        layout.addLayout(table)

        self.setLayout(layout)
        binding = PyQt5Binding()
        self.view_model = PeriodicTableViewModel(binding, crystal_view_model)
        self.view_model.pt_model_bind.connect("pt_model", self.on_show_request)

        self.atom_view = AtomView(self.view_model)
        self.atom_buttons.buttonClicked.connect(self.on_click_atom_button)


    def __init_table(self):
        table = QGridLayout()

        for row in range(7):
            label = QLabel(str(row + 1))
            table.addWidget(label, row + 1, 0, Qt.AlignCenter)

        for col in range(18):
            label = QLabel(str(col + 1))
            table.addWidget(label, 0, col + 1, Qt.AlignCenter)

        self.atom_buttons = QButtonGroup()
        self.atom_buttons.setExclusive(True)

        for key in indexing.keys():
            row, col = indexing[key]
            button = QPushButton(key, self)
            button.setFixedSize(50, 50)
            group = groups.get(key)
            if group is not None:
                color = colors[group]
                button.setStyleSheet("background-color: {}".format(color))
            if isotopes.get(key) is None:
                button.setDisabled(True)
            self.atom_buttons.addButton(button)
            table.addWidget(button, row, col)

        return table

    def on_show_request(self, params: PeriodicTableParams):
        if params.show_dialog:
            self.show()
        else:
            self.close()

    def on_click_atom_button(self, button):
        return self.view_model.show_atom_dialog(button.text())
