import sys
from functools import partial
from typing import List

import numpy as np

from qtpy.QtWidgets import (
    QWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLineEdit,
    QLabel,
    QComboBox,
    QPushButton,
    QCheckBox,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
    QTabWidget,
    QFileDialog,
)

from qtpy.QtGui import QDoubleValidator, QIntValidator, QRegExpValidator
from PyQt5.QtCore import Qt, QRegExp
from PyQt5.QtWidgets import QFrame

import pyvista as pv
from pyvistaqt import QtInteractor

from NeuXtalViz.components.visualization_panel.view_qt import VisPanelWidget
from NeuXtalViz.view_models.sample_tools import (
    AbsorptionParameters,
    FaceIndices,
    Goniometer,
    GoniometerTable,
    MaterialParameters,
    Sample,
    SampleViewModel,
)
from NeuXtalViz.views.shared.crystal_structure_plotter import CrystalStructurePlotter


class SampleView(QWidget):
    def __init__(self, view_model: SampleViewModel, parent=None):
        super().__init__(parent)

        self.view_model = view_model
        layout = QHBoxLayout()
        self.frame = QFrame()  # need to store as object variable
        plotter = QtInteractor(self.frame)
        self.vis_widget = VisPanelWidget("s", plotter, view_model.model, parent)
        self.view_model.set_vis_viewmodel(self.vis_widget.view_model)
        self.plotter = CrystalStructurePlotter(plotter, lambda: None)

        layout.addWidget(self.vis_widget)
        self.tab_widget = QTabWidget(self)
        self.sample_tab()
        layout.addWidget(self.tab_widget, stretch=1)
        self.setLayout(layout)

        self.connect_bindings()
        self.connect_widgets()
        self.view_model.init_view()

    def sample_tab(self):
        samp_tab = QWidget()
        self.tab_widget.addTab(samp_tab, "Sample")

        self.sample_combo = QComboBox(self)
        for option in self.view_model.get_sample_shape_option_list():
            self.sample_combo.addItem(option)

        self.add_sample_button = QPushButton("Add Sample", self)
        self.load_UB_button = QPushButton("Load UB", self)

        notation = QDoubleValidator.StandardNotation

        validator = QDoubleValidator(0, 100, 5, notation=notation)

        param1_label = QLabel("Width", self)
        param2_label = QLabel("Height", self)
        param3_label = QLabel("Thickness", self)

        unit_label = QLabel("cm", self)

        self.param1_line = QLineEdit("0.50")
        self.param2_line = QLineEdit("0.50")
        self.param3_line = QLineEdit("0.50")

        self.param1_line.setValidator(validator)
        self.param2_line.setValidator(validator)
        self.param3_line.setValidator(validator)

        param_layout = QHBoxLayout()
        generate_layout = QHBoxLayout()

        generate_layout.addWidget(self.sample_combo)
        generate_layout.addWidget(self.load_UB_button)
        generate_layout.addWidget(self.add_sample_button)

        param_layout.addWidget(param1_label)
        param_layout.addWidget(self.param1_line)

        param_layout.addWidget(param2_label)
        param_layout.addWidget(self.param2_line)

        param_layout.addWidget(param3_label)
        param_layout.addWidget(self.param3_line)

        param_layout.addWidget(unit_label)

        material_layout = QHBoxLayout()

        self.chem_line = QLineEdit()
        self.Z_line = QLineEdit()
        self.V_line = QLineEdit()

        exp = (
            "-^((\(\d+[A-Z][a-z]?\)|[DT]|[A-Z][a-z]?)(\d+(\.\d+)?)?)"
            + "(-((\(\d+[A-Z][a-z]?\)|[DT]|[A-Z][a-z]?)(\d+(\.\d+)?)?))*$"
        )

        regexp = QRegExp(exp)
        validator = QRegExpValidator(regexp)

        validator = QIntValidator(1, 10000, self)

        self.Z_line.setValidator(validator)

        validator = QDoubleValidator(0, 100000, 4, notation=notation)

        self.V_line.setValidator(validator)

        Z_label = QLabel("Z")
        V_label = QLabel("Ω")
        uc_vol_label = QLabel("Å^3")

        material_layout.addWidget(self.chem_line)
        material_layout.addWidget(Z_label)
        material_layout.addWidget(self.Z_line)
        material_layout.addWidget(V_label)
        material_layout.addWidget(self.V_line)
        material_layout.addWidget(uc_vol_label)

        cryst_layout = QGridLayout()

        scattering_label = QLabel("Scattering", self)
        absorption_label = QLabel("Absorption", self)

        sigma_label = QLabel("σ", self)
        mu_label = QLabel("μ", self)

        sigma_unit_label = QLabel("barn", self)
        mu_unit_label = QLabel("1/cm", self)

        self.sigma_a_line = QLineEdit()
        self.sigma_s_line = QLineEdit()

        self.mu_a_line = QLineEdit()
        self.mu_s_line = QLineEdit()

        self.sigma_a_line.setEnabled(False)
        self.sigma_s_line.setEnabled(False)

        self.mu_a_line.setEnabled(False)
        self.mu_s_line.setEnabled(False)

        cryst_layout.addWidget(scattering_label, 0, 1, Qt.AlignCenter)
        cryst_layout.addWidget(absorption_label, 0, 2, Qt.AlignCenter)

        cryst_layout.addWidget(sigma_label, 1, 0)
        cryst_layout.addWidget(self.sigma_a_line, 1, 1)
        cryst_layout.addWidget(self.sigma_s_line, 1, 2)
        cryst_layout.addWidget(sigma_unit_label, 1, 3)

        cryst_layout.addWidget(mu_label, 2, 0)
        cryst_layout.addWidget(self.mu_a_line, 2, 1)
        cryst_layout.addWidget(self.mu_s_line, 2, 2)
        cryst_layout.addWidget(mu_unit_label, 2, 3)

        N_label = QLabel("N", self)
        M_label = QLabel("M", self)
        n_label = QLabel("n", self)
        rho_label = QLabel("rho", self)
        v_label = QLabel("V", self)
        m_label = QLabel("m", self)

        N_unit_label = QLabel("atoms", self)
        M_unit_label = QLabel("g/mol", self)
        n_unit_label = QLabel("1/Å^3", self)
        rho_unit_label = QLabel("g/cm^3", self)
        v_unit_label = QLabel("cm^3", self)
        m_unit_label = QLabel("g", self)

        self.N_line = QLineEdit()
        self.M_line = QLineEdit()
        self.n_line = QLineEdit()
        self.rho_line = QLineEdit()
        self.v_line = QLineEdit()
        self.m_line = QLineEdit()

        self.N_line.setEnabled(False)
        self.M_line.setEnabled(False)
        self.n_line.setEnabled(False)
        self.rho_line.setEnabled(False)
        self.v_line.setEnabled(False)
        self.m_line.setEnabled(False)

        cryst_layout.addWidget(N_label, 3, 0)
        cryst_layout.addWidget(self.N_line, 3, 1)
        cryst_layout.addWidget(N_unit_label, 3, 2)

        cryst_layout.addWidget(M_label, 4, 0)
        cryst_layout.addWidget(self.M_line, 4, 1)
        cryst_layout.addWidget(M_unit_label, 4, 2)

        cryst_layout.addWidget(n_label, 5, 0)
        cryst_layout.addWidget(self.n_line, 5, 1)
        cryst_layout.addWidget(n_unit_label, 5, 2)

        cryst_layout.addWidget(rho_label, 6, 0)
        cryst_layout.addWidget(self.rho_line, 6, 1)
        cryst_layout.addWidget(rho_unit_label, 6, 2)

        cryst_layout.addWidget(v_label, 7, 0)
        cryst_layout.addWidget(self.v_line, 7, 1)
        cryst_layout.addWidget(v_unit_label, 7, 2)

        cryst_layout.addWidget(m_label, 8, 0)
        cryst_layout.addWidget(self.m_line, 8, 1)
        cryst_layout.addWidget(m_unit_label, 8, 2)

        sample_layout = QVBoxLayout()

        a_star_label = QLabel("a*", self)
        b_star_label = QLabel("b*", self)
        c_star_label = QLabel("c*", self)

        face_index_label = QLabel("Face Index", self)
        u_label = QLabel("Along Thickness:", self)
        v_label = QLabel("In-plane Lateral:", self)

        self.hu_line = QLineEdit("0")
        self.ku_line = QLineEdit("0")
        self.lu_line = QLineEdit("1")

        self.hv_line = QLineEdit("1")
        self.kv_line = QLineEdit("0")
        self.lv_line = QLineEdit("0")

        orient_layout = QGridLayout()

        orient_layout.addWidget(face_index_label, 0, 0, Qt.AlignCenter)
        orient_layout.addWidget(a_star_label, 0, 1, Qt.AlignCenter)
        orient_layout.addWidget(b_star_label, 0, 2, Qt.AlignCenter)
        orient_layout.addWidget(c_star_label, 0, 3, Qt.AlignCenter)

        orient_layout.addWidget(u_label, 1, 0)
        orient_layout.addWidget(self.hu_line, 1, 1)
        orient_layout.addWidget(self.ku_line, 1, 2)
        orient_layout.addWidget(self.lu_line, 1, 3)
        orient_layout.addWidget(v_label, 2, 0)
        orient_layout.addWidget(self.hv_line, 2, 1)
        orient_layout.addWidget(self.kv_line, 2, 2)
        orient_layout.addWidget(self.lv_line, 2, 3)

        stretch = QHeaderView.Stretch

        self.gon_table = QTableWidget()

        self.gon_table.setRowCount(3)
        self.gon_table.setColumnCount(6)

        labels = ["name", "x", "y", "z", "sense", "angle"]

        self.gon_table.horizontalHeader().setSectionResizeMode(stretch)
        self.gon_table.setHorizontalHeaderLabels(labels)
        self.gon_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.gon_table.setSelectionBehavior(QTableWidget.SelectRows)

        data = [
            ["ω", 0, 1, 0, 1, 0.0],
            ["χ", 0, 0, 1, 1, 0.0],
            ["φ", 0, 1, 0, 1, 0.0],
        ]

        for row, gon in enumerate(data):
            for col, val in enumerate(gon):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                self.gon_table.setItem(row, col, item)

        goniometer_layout = QHBoxLayout()

        self.name_line = QLineEdit()
        self.x_line = QLineEdit()
        self.y_line = QLineEdit()
        self.z_line = QLineEdit()
        self.sense_line = QLineEdit()
        self.angle_line = QLineEdit()

        self.name_line.setReadOnly(True)

        validator = QIntValidator(-1, 1, self)

        self.x_line.setValidator(validator)
        self.y_line.setValidator(validator)
        self.z_line.setValidator(validator)

        regexp = QRegExp("^-1$|^1$")
        validator = QRegExpValidator(regexp)

        self.sense_line.setValidator(validator)

        validator = QDoubleValidator(-360, 360, 1, notation=notation)

        self.angle_line.setValidator(validator)

        goniometer_layout.addWidget(self.name_line)
        goniometer_layout.addWidget(self.x_line)
        goniometer_layout.addWidget(self.y_line)
        goniometer_layout.addWidget(self.z_line)
        goniometer_layout.addWidget(self.sense_line)
        goniometer_layout.addWidget(self.angle_line)

        sample_layout.addLayout(generate_layout)
        sample_layout.addLayout(param_layout)
        sample_layout.addWidget(self.gon_table)
        sample_layout.addLayout(goniometer_layout)
        sample_layout.addLayout(orient_layout)
        sample_layout.addLayout(material_layout)
        sample_layout.addLayout(cryst_layout)

        samp_tab.setLayout(sample_layout)

    def connect_bindings(self):
        self.view_model.add_sample_bind.connect("s_add_sample", self.plotter.add_sample)
        self.view_model.absorption_parameters_bind.connect(
            "s_absorption_parameters", self.on_absortion_parameters_update
        )
        self.view_model.constraints_bind.connect(
            "s_constraints", self.on_constraints_update
        )
        self.view_model.face_indices_bind.connect(
            "s_face_indices", self.on_face_indices_update
        )
        self.view_model.goniometer_editor_bind.connect(
            "s_goniometer_editor", self.on_goniometer_editor_update
        )
        self.view_model.goniometer_table_bind.connect(
            "s_goniometer_table", self.on_goniometer_table_update
        )
        self.view_model.material_parameters_bind.connect(
            "s_material_parameters", self.on_material_parameters_update
        )
        self.callback_ub = self.view_model.sample_bind.connect(
            "s_sample", self.on_sample_update
        )

    def connect_widgets(self):
        self.sample_combo.activated.connect(
            lambda: self.view_model.set_sample_param(
                "shape", self.sample_combo.currentText()
            )
        )
        self.param1_line.editingFinished.connect(
            lambda: self.view_model.set_sample_param("width", self.param1_line.text())
        )
        self.param2_line.editingFinished.connect(
            lambda: self.view_model.set_sample_param("height", self.param2_line.text())
        )
        self.param3_line.editingFinished.connect(
            lambda: self.view_model.set_sample_param(
                "thickness", self.param3_line.text()
            )
        )
        self.hu_line.editingFinished.connect(
            lambda: self.view_model.set_index("hu", self.hu_line.text())
        )
        self.ku_line.editingFinished.connect(
            lambda: self.view_model.set_index("ku", self.ku_line.text())
        )
        self.lu_line.editingFinished.connect(
            lambda: self.view_model.set_index("lu", self.lu_line.text())
        )
        self.hv_line.editingFinished.connect(
            lambda: self.view_model.set_index("hv", self.hv_line.text())
        )
        self.kv_line.editingFinished.connect(
            lambda: self.view_model.set_index("kv", self.kv_line.text())
        )
        self.lv_line.editingFinished.connect(
            lambda: self.view_model.set_index("lv", self.lv_line.text())
        )
        self.chem_line.editingFinished.connect(
            lambda: self.view_model.set_material_parameter(
                "chemical_formula", self.chem_line.text()
            )
        )
        self.Z_line.editingFinished.connect(
            lambda: self.view_model.set_material_parameter(
                "z_parameter", self.Z_line.text()
            )
        )
        self.V_line.editingFinished.connect(
            lambda: self.view_model.set_material_parameter("volume", self.V_line.text())
        )

        self.gon_table.itemSelectionChanged.connect(
            lambda: self.view_model.highlight_row(self.gon_table.currentRow())
        )
        self.x_line.editingFinished.connect(
            lambda: self.view_model.set_goniometer_table("x", self.x_line.text())
        )
        self.y_line.editingFinished.connect(
            lambda: self.view_model.set_goniometer_table("y", self.y_line.text())
        )
        self.z_line.editingFinished.connect(
            lambda: self.view_model.set_goniometer_table("z", self.z_line.text())
        )
        self.sense_line.editingFinished.connect(
            lambda: self.view_model.set_goniometer_table(
                "sense", self.sense_line.text()
            )
        )
        self.angle_line.editingFinished.connect(
            lambda: self.view_model.set_goniometer_table(
                "angle", self.angle_line.text()
            )
        )

        self.load_UB_button.clicked.connect(self.load_UB)
        self.add_sample_button.clicked.connect(self.view_model.add_sample)

    def load_UB(self):
        filename = self.load_UB_file_dialog()
        self.callback_ub("s_sample.path", filename or "")

    def load_UB_file_dialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog

        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.AnyFile)

        filename, _ = file_dialog.getOpenFileName(
            self, "Load UB file", "", "UB files (*.mat)", options=options
        )

        return filename

    def on_absortion_parameters_update(
        self, absorption_parameters: AbsorptionParameters
    ):
        self.sigma_a_line.setText("{:.4f}".format(absorption_parameters.sigma_a))
        self.sigma_s_line.setText("{:.4f}".format(absorption_parameters.sigma_s))

        self.mu_a_line.setText("{:.4f}".format(absorption_parameters.mu_a))
        self.mu_s_line.setText("{:.4f}".format(absorption_parameters.mu_s))

        self.N_line.setText("{:.4f}".format(absorption_parameters.N))
        self.M_line.setText("{:.4f}".format(absorption_parameters.M))
        self.n_line.setText("{:.4f}".format(absorption_parameters.n))
        self.rho_line.setText("{:.4f}".format(absorption_parameters.rho))
        self.v_line.setText("{:.4f}".format(absorption_parameters.V))
        self.m_line.setText("{:.4f}".format(absorption_parameters.m))

    def on_constraints_update(self, constraints: List[bool]):
        self.param1_line.setDisabled(constraints[0])
        self.param2_line.setDisabled(constraints[1])
        self.param3_line.setDisabled(constraints[2])

    def on_face_indices_update(self, face_indices: FaceIndices):
        self.hu_line.setText(str(face_indices.hu))
        self.ku_line.setText(str(face_indices.ku))
        self.lu_line.setText(str(face_indices.lu))
        self.hv_line.setText(str(face_indices.hv))
        self.kv_line.setText(str(face_indices.kv))
        self.lv_line.setText(str(face_indices.lv))

    def on_goniometer_editor_update(self, goniometer: Goniometer):
        self.name_line.setText(goniometer.name)
        self.x_line.setText(str(goniometer.x))
        self.y_line.setText(str(goniometer.y))
        self.z_line.setText(str(goniometer.z))
        self.sense_line.setText(str(goniometer.sense))
        self.angle_line.setText(str(goniometer.angle))

    def on_goniometer_table_update(self, goniometer_table: GoniometerTable):
        for row, goniometer in enumerate(goniometer_table.get_rows()):
            self.set_goniometer(row, goniometer)

    def on_material_parameters_update(self, material_parameters: MaterialParameters):
        self.Z_line.setText(str(material_parameters.z_parameter))
        self.set_unit_cell_volume(material_parameters.volume)

    def on_sample_update(self, sample: Sample):
        self.param1_line.setText("{:.2f}".format(sample.width))
        self.param2_line.setText("{:.2f}".format(sample.height))
        self.param3_line.setText("{:.2f}".format(sample.thickness))
        self.set_sample_shape(sample.shape)

    def set_goniometer(self, row, goniometer_values):
        for col, value in enumerate(goniometer_values):
            item = QTableWidgetItem(str(value))
            item.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            self.gon_table.setItem(row, col, item)

    def set_sample_shape(self, shape):
        index = self.sample_combo.findText(shape)
        if index >= 0:
            self.sample_combo.setCurrentIndex(index)

    def set_unit_cell_volume(self, vol):
        self.V_line.setText("{:.4f}".format(vol))
