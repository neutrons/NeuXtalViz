import numpy as np
from PyQt5.QtCore import Qt, pyqtSignal
from nova.mvvm.pyqt5_binding import PyQt5Binding
from qtpy.QtWidgets import (
    QWidget,
    QPushButton,
    QLabel,
    QComboBox,
    QGridLayout,
)

from NeuXtalViz.view_models.atom import AtomViewModel, AtomParams
from NeuXtalViz.view_models.periodic_table import PeriodicTableViewModel


class AtomView(QWidget):
    selection = pyqtSignal(str)

    def __init__(self, pt_viewmodel: PeriodicTableViewModel):
        super().__init__()

        binding = PyQt5Binding()
        self.view_model = AtomViewModel(binding, pt_viewmodel)
        pt_viewmodel.set_atom_viewmodel(self.view_model)
        self.callback_atom_params = self.view_model.atom_params_bind.connect("atom_model", self.on_atom_params_update)

        card = QGridLayout()

        self.z_label = QLabel("1")
        self.symbol_label = QLabel("H")
        self.name_label = QLabel("Hydrogen")
        self.mass_label = QLabel("1.007825")
        self.abundance_label = QLabel("99.9885")

        self.sigma_coh_label = QLabel("")
        self.sigma_inc_label = QLabel("")
        self.sigma_tot_label = QLabel("")
        self.b_coh_label = QLabel("")
        self.b_inc_label = QLabel("")

        self.isotope_combo = QComboBox(self)

        self.select_button = QPushButton("Use Isotope", self)

        card.addWidget(self.z_label, 0, 0, Qt.AlignCenter)
        card.addWidget(self.isotope_combo, 0, 1, 1, 2)
        card.addWidget(self.symbol_label, 1, 1, 1, 2, Qt.AlignCenter)
        card.addWidget(self.name_label, 2, 1, 1, 2, Qt.AlignCenter)
        card.addWidget(self.mass_label, 3, 1, 1, 2, Qt.AlignCenter)

        card.addWidget(self.abundance_label, 0, 3)
        card.addWidget(self.sigma_tot_label, 1, 3)
        card.addWidget(self.sigma_coh_label, 2, 3)
        card.addWidget(self.sigma_inc_label, 3, 3)
        card.addWidget(self.b_coh_label, 2, 4)
        card.addWidget(self.b_inc_label, 3, 4)
        card.addWidget(self.select_button, 0, 4)

        self.setLayout(card)
        self.selection.connect(self.view_model.update_selection)
        self.select_button.clicked.connect(self.view_model.use_isotope)

    def update_isotope(self, new_value):
        self.callback_atom_params("atom_model.current_isotope", new_value)

    def on_atom_params_update(self, atom_params: AtomParams):
        if atom_params.view_dialog == False:
            self.close()
            return
        self.set_symbol_name(atom_params.symbol, atom_params.name)
        self.set_isotope_numbers(atom_params.isotope_numbers, atom_params.current_isotope)
        self.set_atom_parameters(atom_params.atom_dict, atom_params.neutron_dict)
        self.show()

    def connect_isotopes(self, update_info):
        self.isotope_combo.currentIndexChanged.connect(update_info)

    def set_symbol_name(self, symbol, name):
        self.symbol_label.setText(symbol)
        self.name_label.setText(name)

    def set_isotope_numbers(self, numbers, cur_index):
        try:
            self.isotope_combo.currentIndexChanged.disconnect(self.update_isotope)
        except Exception:
            pass

        self.isotope_combo.clear()
        if numbers is not None:
            self.isotope_combo.addItems(np.array(numbers).astype(str).tolist())
            self.isotope_combo.setCurrentIndex(cur_index)
            self.isotope_combo.currentIndexChanged.connect(self.update_isotope)

    def set_atom_parameters(self, atom, scatt):
        self.z_label.setText(str(atom["z"]))
        self.mass_label.setText(str(atom["mass"]))
        self.abundance_label.setText(str(atom["abundance"]))

        self.sigma_coh_label.setText("σ(coh) = {}".format(scatt["sigma_coh"]))
        self.sigma_inc_label.setText("σ(inc) = {}".format(scatt["sigma_inc"]))
        self.sigma_tot_label.setText("σ(tot) = {}".format(scatt["sigma_tot"]))

        self.b_coh_label.setText(
            "b(coh) = {}+{}i".format(scatt["b_coh_re"], scatt["b_coh_im"])
        )
        self.b_inc_label.setText(
            "b(inc) = {}+{}i".format(scatt["b_inc_re"], scatt["b_inc_im"])
        )
