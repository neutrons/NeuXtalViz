from typing import Any

from PyQt5.QtWidgets import QFrame
from nova.mvvm.pydantic_utils import validate_pydantic_parameter
from pyvistaqt import QtInteractor
from qtpy.QtGui import QDoubleValidator
from qtpy.QtWidgets import (
    QWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLineEdit,
    QLabel,
    QComboBox,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
    QTabWidget,
    QFileDialog,
)

from NeuXtalViz.components.visualizatioin_panel.view_qt import VisPanelWidget
from NeuXtalViz.qt.views.periodic_table import PeriodicTableView
from NeuXtalViz.view_models.crystal_structure_tools import CrystalStructureViewModel, CrystalStructureControls, \
    CrystalStructureAtoms, CrystalStructureScatterers
from NeuXtalViz.views.shared.crystal_structure_plotter import CrystalStructurePlotter


def validate_element(key: str, value: Any, element: Any = None) -> None:
    if element:
        res = validate_pydantic_parameter(key, value)
        if res is not True:
            element.setStyleSheet("border: 1px solid red;")
        else:
            element.setStyleSheet("")


class CrystalStructureView(QWidget):
    def __init__(self, view_model: CrystalStructureViewModel, parent=None):
        super().__init__(parent)

        self.view_model = view_model
        layout = QHBoxLayout()
        self.frame = QFrame()  # need to store as object variable
        plotter = QtInteractor(self.frame)
        self.vis_widget = VisPanelWidget("cs", plotter, view_model.model, parent)
        self.view_model.set_vis_viewmodel(self.vis_widget.view_model)
        self.plotter = CrystalStructurePlotter(plotter, self.highlight)

        self.callback_controls = self.view_model.cs_controls_bind.connect("cs_controls", self.on_controls_update)
        self.view_model.cs_scatterers_bind.connect("cs_scatterers", self.on_scatterers_update)

        self.callback_atoms = self.view_model.cs_atoms_bind.connect("cs_atoms", self.on_atoms_update)

        self.view_model.cs_factors_bind.connect("cs_factors", self.set_factors)
        self.view_model.cs_equivalents_bind.connect("cs_equivalents", self.set_equivalents)

        layout.addWidget(self.vis_widget)
        self.tab_widget = QTabWidget(self)
        self.structure_tab()
        self.factors_tab()
        layout.addWidget(self.tab_widget, stretch=1)
        self.setLayout(layout)
        self.connect_widgets()

    def structure_tab(self):
        struct_tab = QWidget()
        self.tab_widget.addTab(struct_tab, "Structure")

        structure_layout = QVBoxLayout()

        crystal_layout = QHBoxLayout()
        parameters_layout = QGridLayout()

        self.a_line = QLineEdit()
        self.b_line = QLineEdit()
        self.c_line = QLineEdit()

        self.alpha_line = QLineEdit()
        self.beta_line = QLineEdit()
        self.gamma_line = QLineEdit()

        notation = QDoubleValidator.StandardNotation

        validator = QDoubleValidator(0.1, 1000, 4, notation=notation)

        self.a_line.setValidator(validator)
        self.b_line.setValidator(validator)
        self.c_line.setValidator(validator)

        notation = QDoubleValidator.StandardNotation

        validator = QDoubleValidator(10, 170, 4, notation=notation)

        self.alpha_line.setValidator(validator)
        self.beta_line.setValidator(validator)
        self.gamma_line.setValidator(validator)

        a_label = QLabel("a")
        b_label = QLabel("b")
        c_label = QLabel("c")

        alpha_label = QLabel("α")
        beta_label = QLabel("β")
        gamma_label = QLabel("γ")

        angstrom_label = QLabel("Å")
        degree_label = QLabel("°")

        parameters_layout.addWidget(a_label, 0, 0)
        parameters_layout.addWidget(self.a_line, 0, 1)
        parameters_layout.addWidget(b_label, 0, 2)
        parameters_layout.addWidget(self.b_line, 0, 3)
        parameters_layout.addWidget(c_label, 0, 4)
        parameters_layout.addWidget(self.c_line, 0, 5)
        parameters_layout.addWidget(angstrom_label, 0, 6)
        parameters_layout.addWidget(alpha_label, 1, 0)
        parameters_layout.addWidget(self.alpha_line, 1, 1)
        parameters_layout.addWidget(beta_label, 1, 2)
        parameters_layout.addWidget(self.beta_line, 1, 3)
        parameters_layout.addWidget(gamma_label, 1, 4)
        parameters_layout.addWidget(self.gamma_line, 1, 5)
        parameters_layout.addWidget(degree_label, 1, 6)

        self.crystal_system_combo = QComboBox(self)
        for option in self.view_model.get_crystal_system_option_list():
            self.crystal_system_combo.addItem(option)

        self.space_group_combo = QComboBox(self)
        self.setting_combo = QComboBox(self)

        self.crystal_system_combo.setEnabled(False)
        self.space_group_combo.setEnabled(False)
        self.setting_combo.setEnabled(False)

        self.load_CIF_button = QPushButton("Load CIF", self)
        self.save_INS_button = QPushButton("Save INS", self)

        crystal_layout.addWidget(self.crystal_system_combo)
        crystal_layout.addWidget(self.space_group_combo)
        crystal_layout.addWidget(self.setting_combo)
        crystal_layout.addWidget(self.load_CIF_button)
        crystal_layout.addWidget(self.save_INS_button)

        structure_layout.addLayout(crystal_layout)
        structure_layout.addLayout(parameters_layout)

        stretch = QHeaderView.Stretch

        self.atm_table = QTableWidget()

        self.atm_table.setRowCount(0)
        self.atm_table.setColumnCount(6)

        self.atm_table.horizontalHeader().setSectionResizeMode(stretch)
        self.atm_table.setHorizontalHeaderLabels(
            ["atm", "x", "y", "z", "occ", "U"]
        )
        self.atm_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.atm_table.setSelectionBehavior(QTableWidget.SelectRows)

        structure_layout.addWidget(self.atm_table)

        scatterer_layout = QHBoxLayout()

        self.atm_button = QPushButton("", self)

        self.x_line = QLineEdit()
        self.y_line = QLineEdit()
        self.z_line = QLineEdit()
        self.occ_line = QLineEdit()
        self.Uiso_line = QLineEdit()

        validator = QDoubleValidator(-1, 1, 4, notation=notation)

        self.x_line.setValidator(validator)
        self.y_line.setValidator(validator)
        self.z_line.setValidator(validator)

        validator = QDoubleValidator(0, 1, 4, notation=notation)

        self.occ_line.setValidator(validator)

        validator = QDoubleValidator(0, 100, 4, notation=notation)

        self.Uiso_line.setValidator(validator)

        scatterer_layout.addWidget(self.atm_button)
        scatterer_layout.addWidget(self.x_line)
        scatterer_layout.addWidget(self.y_line)
        scatterer_layout.addWidget(self.z_line)
        scatterer_layout.addWidget(self.occ_line)
        scatterer_layout.addWidget(self.Uiso_line)

        sample_layout = QHBoxLayout()

        self.chem_line = QLineEdit()
        self.Z_line = QLineEdit()
        self.V_line = QLineEdit()

        self.chem_line.setReadOnly(True)
        self.Z_line.setReadOnly(True)
        self.V_line.setReadOnly(True)

        Z_label = QLabel("Z")
        V_label = QLabel("Ω")
        uc_vol_label = QLabel("Å^3")

        sample_layout.addWidget(self.chem_line)
        sample_layout.addWidget(Z_label)
        sample_layout.addWidget(self.Z_line)
        sample_layout.addWidget(V_label)
        sample_layout.addWidget(self.V_line)
        sample_layout.addWidget(uc_vol_label)

        structure_layout.addLayout(scatterer_layout)
        structure_layout.addLayout(sample_layout)

        struct_tab.setLayout(structure_layout)

    def factors_tab(self):
        fact_tab = QWidget()
        self.tab_widget.addTab(fact_tab, "Factors")

        factors_layout = QVBoxLayout()

        calculate_layout = QHBoxLayout()

        dmin_label = QLabel("d(min)")
        angstrom_label = QLabel("Å")

        notation = QDoubleValidator.StandardNotation

        validator = QDoubleValidator(0.1, 1000, 4, notation=notation)

        self.dmin_line = QLineEdit()
        self.dmin_line.setValidator(validator)

        self.calculate_button = QPushButton("Calculate", self)

        calculate_layout.addWidget(dmin_label)
        calculate_layout.addWidget(self.dmin_line)
        calculate_layout.addWidget(angstrom_label)
        calculate_layout.addStretch(1)
        calculate_layout.addWidget(self.calculate_button)

        stretch = QHeaderView.Stretch

        self.f2_table = QTableWidget()

        self.f2_table.setRowCount(0)
        self.f2_table.setColumnCount(5)

        self.f2_table.horizontalHeader().setSectionResizeMode(stretch)
        self.f2_table.setHorizontalHeaderLabels(["h", "k", "l", "d", "F²"])
        self.f2_table.setEditTriggers(QTableWidget.NoEditTriggers)

        indivdual_layout = QHBoxLayout()

        notation = QDoubleValidator.StandardNotation

        validator = QDoubleValidator(-100, 100, 5, notation=notation)

        self.h_line = QLineEdit()
        self.k_line = QLineEdit()
        self.l_line = QLineEdit()

        self.h_line.setValidator(validator)
        self.k_line.setValidator(validator)
        self.l_line.setValidator(validator)

        self.individual_button = QPushButton("Calculate", self)

        hkl_label = QLabel("hkl")

        indivdual_layout.addWidget(hkl_label)
        indivdual_layout.addWidget(self.h_line)
        indivdual_layout.addWidget(self.k_line)
        indivdual_layout.addWidget(self.l_line)
        indivdual_layout.addStretch(1)
        indivdual_layout.addWidget(self.individual_button)

        factors_layout.addLayout(calculate_layout)
        factors_layout.addWidget(self.f2_table)
        factors_layout.addLayout(indivdual_layout)

        fact_tab.setLayout(factors_layout)

    def connect_widgets(self):
        self.load_CIF_button.clicked.connect(self.load_CIF)
        self.calculate_button.clicked.connect(self.view_model.calculate_F2)
        self.individual_button.clicked.connect(self.view_model.calculate_hkl)
        self.save_INS_button.clicked.connect(self.save_INS)

        self.crystal_system_combo.currentTextChanged.connect(
            lambda value: self.process_controls_change("cs_controls.crystal_system", value)
        )

        self.dmin_line.textChanged.connect(
            lambda value: self.process_controls_change("cs_controls.minimum_d_spacing", value, self.dmin_line)
        )

        self.h_line.textChanged.connect(
            lambda value: self.process_controls_change("cs_controls.h", value, self.h_line)
        )
        self.k_line.textChanged.connect(
            lambda value: self.process_controls_change("cs_controls.k", value, self.k_line)
        )
        self.l_line.textChanged.connect(
            lambda value: self.process_controls_change("cs_controls.l", value, self.l_line)
        )

        self.connect_lattice_parameters()
        self.connect_atom_table()
        self.atm_table.itemSelectionChanged.connect(self.highlight_row)

    def highlight_row(self):
        self.process_controls_change("cs_controls.current_scatterer_row", self.atm_table.currentRow())

    def on_atoms_update(self, atoms: CrystalStructureAtoms):
        self.add_atoms(atoms.atoms_dict)
        self.draw_cell(atoms.cell)

    def on_scatterers_update(self, scatterers: CrystalStructureScatterers):
        self.set_scatterers(scatterers.scatterers)

    def on_controls_update(self, controls: CrystalStructureControls):
        self.set_crystal_system(controls.crystal_system)
        self.update_space_groups(controls.space_group_options)
        self.set_space_group(controls.space_group)
        self.update_settings(controls.setting_options)
        self.set_setting(controls.setting)
        self.set_lattice_constants(controls.lattice_constants)
        self.set_unit_cell_volume(controls.vol)
        self.set_formula_z(controls.formula, controls.z)
        self.dmin_line.setText(str(controls.minimum_d_spacing or ''))
        self.constrain_parameters(controls.constrain_parameters)
        if controls.current_scatterer_row is not None:
            if controls.current_scatterer is not None:
                self.set_atom_table(controls.current_scatterer_row, controls.current_scatterer)
            self.set_atom(controls.current_scatterer)

    def process_controls_change(self, key: str, value: Any, element: Any = None) -> None:
        validate_element(key, value, element)
        self.callback_controls(key, value)

    def load_CIF(self):
        filename = self.load_CIF_file_dialog()
        self.view_model.load_CIF(filename)

    def save_INS(self):
        if self.view_model.save_ins_enabled():
            filename = self.save_INS_file_dialog()
            self.view_model.save_INS(filename)

    def update_lattice_parameters(self):
        lattice_constants = self.get_lattice_constants()
        self.process_controls_change("cs_controls.lattice_constants", lattice_constants)

    def connect_lattice_parameters(self):
        self.a_line.editingFinished.connect(self.update_lattice_parameters)
        self.b_line.editingFinished.connect(self.update_lattice_parameters)
        self.c_line.editingFinished.connect(self.update_lattice_parameters)
        self.alpha_line.editingFinished.connect(self.update_lattice_parameters)
        self.beta_line.editingFinished.connect(self.update_lattice_parameters)
        self.gamma_line.editingFinished.connect(self.update_lattice_parameters)

    def update_scatterer(self):
        scatterer = self.get_current_scatterer()
        self.process_controls_change("cs_controls.current_scatterer", scatterer)

    def connect_atom_table(self):
        self.x_line.editingFinished.connect(self.update_scatterer)
        self.y_line.editingFinished.connect(self.update_scatterer)
        self.z_line.editingFinished.connect(self.update_scatterer)
        self.occ_line.editingFinished.connect(self.update_scatterer)
        self.Uiso_line.editingFinished.connect(self.update_scatterer)

    def connect_select_isotope(self, select_isotope):
        self.atm_button.clicked.connect(select_isotope)

    def draw_cell(self, A):
        self.plotter.draw_cell(A)

    def load_CIF_file_dialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog

        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.AnyFile)

        filename, _ = file_dialog.getOpenFileName(
            self, "Load CIF file", "", "CIF files (*.cif)", options=options
        )

        return filename

    def save_INS_file_dialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog

        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.AnyFile)

        filename, _ = file_dialog.getSaveFileName(
            self, "Save INS file", "", "INS files (*.ins)", options=options
        )

        return filename

    def get_crystal_system(self):
        return self.crystal_system_combo.currentText()

    def set_crystal_system(self, crystal_system):
        index = self.crystal_system_combo.findText(crystal_system)
        if index >= 0:
            self.crystal_system_combo.setCurrentIndex(index)

    def update_space_groups(self, nos):
        self.space_group_combo.clear()
        for no in nos:
            self.space_group_combo.addItem(no)

    def get_space_group(self):
        return self.space_group_combo.currentText()

    def set_space_group(self, space_group):
        index = self.space_group_combo.findText(space_group)
        if index >= 0:
            self.space_group_combo.setCurrentIndex(index)

    def update_settings(self, settings):
        self.setting_combo.clear()
        for setting in settings:
            self.setting_combo.addItem(setting)

    def get_setting(self):
        return self.setting_combo.currentText()

    def set_setting(self, setting):
        index = self.setting_combo.findText(setting)
        if index >= 0:
            self.setting_combo.setCurrentIndex(index)

    def set_lattice_constants(self, params):
        self.a_line.setText("{:.4f}".format(params[0]))
        self.b_line.setText("{:.4f}".format(params[1]))
        self.c_line.setText("{:.4f}".format(params[2]))

        self.alpha_line.setText("{:.4f}".format(params[3]))
        self.beta_line.setText("{:.4f}".format(params[4]))
        self.gamma_line.setText("{:.4f}".format(params[5]))

    def get_lattice_constants(self):
        params = (
            self.a_line,
            self.b_line,
            self.c_line,
            self.alpha_line,
            self.beta_line,
            self.gamma_line,
        )

        valid_params = all([param.hasAcceptableInput() for param in params])

        if valid_params:
            return [float(param.text()) for param in params]

    def set_unit_cell_volume(self, vol):
        self.V_line.setText("{:.4f}".format(vol))

    def set_scatterers(self, scatterers):
        self.atm_table.clearSelection()
        self.atm_table.setRowCount(0)
        self.atm_table.setRowCount(len(scatterers))

        for row, scatterer in enumerate(scatterers):
            self.set_scatterer(row, scatterer)

    def set_scatterer(self, row, scatterer):
        atm, *xyz, occ, Uiso = scatterer
        xyz = ["{:.4f}".format(val) for val in xyz]
        occ = "{:.4f}".format(occ)
        Uiso = "{:.4f}".format(Uiso)
        self.atm_table.setItem(row, 0, QTableWidgetItem(atm))
        self.atm_table.setItem(row, 1, QTableWidgetItem(xyz[0]))
        self.atm_table.setItem(row, 2, QTableWidgetItem(xyz[1]))
        self.atm_table.setItem(row, 3, QTableWidgetItem(xyz[2]))
        self.atm_table.setItem(row, 4, QTableWidgetItem(occ))
        self.atm_table.setItem(row, 5, QTableWidgetItem(Uiso))

    def get_scatterer(self):
        row = self.atm_table.currentRow()
        if row is not None:
            return self.get_atom_site(row)

    def get_atom_site(self, row):
        atm = self.atm_table.item(row, 0).text()
        x = self.atm_table.item(row, 1).text()
        y = self.atm_table.item(row, 2).text()
        z = self.atm_table.item(row, 3).text()
        occ = self.atm_table.item(row, 4).text()
        Uiso = self.atm_table.item(row, 5).text()
        scatterer = [atm, *[float(val) for val in [x, y, z, occ, Uiso]]]

        return scatterer

    def get_scatterers(self):
        n = self.atm_table.rowCount()

        scatterers = []
        for row in range(n):
            scatterer = self.get_atom_site(row)
            scatterers.append(scatterer)

        return scatterers

    def set_isotope(self, isotope):
        self.atm_button.setText(isotope)

    def get_isotope(self):
        return self.atm_button.text()

    def set_atom(self, scatterer):
        atm, *xyz, occ, Uiso = scatterer
        xyz = ["{:.4f}".format(val) for val in xyz]
        occ = "{:.4f}".format(occ)
        Uiso = "{:.4f}".format(Uiso)

        self.atm_button.setText(atm)
        self.x_line.setText(xyz[0])
        self.y_line.setText(xyz[1])
        self.z_line.setText(xyz[2])
        self.occ_line.setText(occ)
        self.Uiso_line.setText(Uiso)

    def get_current_scatterer(self):
        params = (
            self.x_line,
            self.y_line,
            self.z_line,
            self.occ_line,
            self.Uiso_line,
        )

        valid_params = all([param.hasAcceptableInput() for param in params])

        if valid_params:
            return [
                self.atm_button.text(),
                *[float(param.text()) for param in params],
            ]


    def set_formula_z(self, chemical_formula, z_parameter):
        self.chem_line.setText(chemical_formula)
        self.Z_line.setText(str(z_parameter))

    def constrain_parameters(self, const):
        params = (
            self.a_line,
            self.b_line,
            self.c_line,
            self.alpha_line,
            self.beta_line,
            self.gamma_line,
        )

        for fixed, param in zip(const, params):
            param.setDisabled(fixed)

    def add_atoms(self, atom_dict):
        self.plotter.add_atoms(atom_dict)

    def highlight(self, ind):
        selected = self.atm_table.selectedIndexes()
        if selected:
            selected_row = selected[0].row()
            if selected_row == ind:
                return
        self.atm_table.selectRow(ind)

    def set_factors(self, result):
        (hkls, ds, F2s) = result
        self.f2_table.setRowCount(0)
        self.f2_table.setRowCount(len(hkls))

        for row, (hkl, d, F2) in enumerate(zip(hkls, ds, F2s)):
            hkl = ["{:.0f}".format(val) for val in hkl]
            d = "{:.4f}".format(d)
            F2 = "{:.2f}".format(F2)
            self.f2_table.setItem(row, 0, QTableWidgetItem(hkl[0]))
            self.f2_table.setItem(row, 1, QTableWidgetItem(hkl[1]))
            self.f2_table.setItem(row, 2, QTableWidgetItem(hkl[2]))
            self.f2_table.setItem(row, 3, QTableWidgetItem(d))
            self.f2_table.setItem(row, 4, QTableWidgetItem(F2))

    def set_equivalents(self, result):
        (hkls, d, F2) = result

        self.f2_table.setRowCount(0)
        self.f2_table.setRowCount(len(hkls))

        d = "{:.4f}".format(d)
        F2 = "{:.2f}".format(F2)

        for row, hkl in enumerate(hkls):
            hkl = ["{:.0f}".format(val) for val in hkl]
            self.f2_table.setItem(row, 0, QTableWidgetItem(hkl[0]))
            self.f2_table.setItem(row, 1, QTableWidgetItem(hkl[1]))
            self.f2_table.setItem(row, 2, QTableWidgetItem(hkl[2]))
            self.f2_table.setItem(row, 3, QTableWidgetItem(d))
            self.f2_table.setItem(row, 4, QTableWidgetItem(F2))

    def get_periodic_table(self):
        return PeriodicTableView()

    def set_atom_table(self, row, scatterer):
        self.set_scatterer(row, scatterer)