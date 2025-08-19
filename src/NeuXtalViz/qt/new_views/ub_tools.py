from PyQt5.QtWidgets import QFrame
from pyvistaqt import QtInteractor  # type: ignore
from qtpy.QtCore import Qt, QRegExp
from qtpy.QtGui import QDoubleValidator, QIntValidator, QRegExpValidator
from qtpy.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QHBoxLayout,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from NeuXtalViz.components.visualization_panel.view_qt import VisPanelWidget
from NeuXtalViz.view_models.ub_tools import QConversion, UBViewModel
from NeuXtalViz.views.shared.ub_plotter import UBPlotter


class UBView(QWidget):
    def __init__(self, view_model: UBViewModel, parent=None):
        super().__init__(parent)

        self.view_model = view_model
        layout = QHBoxLayout()
        self.frame = QFrame()  # need to store as object variable
        plotter = QtInteractor(self.frame)
        self.vis_widget = VisPanelWidget("ub", plotter, view_model.model, parent)
        self.view_model.set_vis_viewmodel(self.vis_widget.view_model)

        self.plotter = UBPlotter(self.view_model, plotter)

        layout.addWidget(self.vis_widget)
        self.tab_widget = QTabWidget(self)

        self.parameters_tab()

        layout.addWidget(self.tab_widget, stretch=1)
        self.setLayout(layout)

        self.connect_bindings()
        self.connect_widgets()

        self.view_model.switch_instrument()

    def parameters_tab(self):
        ub_peaks_tab = QWidget()
        self.tab_widget.addTab(ub_peaks_tab, "Parameters")

        ub_layout = QVBoxLayout()

        self.save_q_button = QPushButton("Save Q", self)
        self.load_q_button = QPushButton("Load Q", self)

        self.save_peaks_button = QPushButton("Save Peaks", self)
        self.load_peaks_button = QPushButton("Load Peaks", self)

        self.save_ub_button = QPushButton("Save UB", self)
        self.load_ub_button = QPushButton("Load UB", self)

        convert_io_layout = QHBoxLayout()

        convert_io_layout.addStretch(1)
        convert_io_layout.addWidget(self.save_q_button)
        convert_io_layout.addWidget(self.load_q_button)

        peaks_io_layout = QHBoxLayout()

        peaks_io_layout.addStretch(1)
        peaks_io_layout.addWidget(self.save_peaks_button)
        peaks_io_layout.addWidget(self.load_peaks_button)

        ub_io_layout = QHBoxLayout()

        ub_io_layout.addStretch(1)
        ub_io_layout.addWidget(self.save_ub_button)
        ub_io_layout.addWidget(self.load_ub_button)

        convert_tab = self.__init_convert_tab()
        peaks_tab = self.__init_peaks_tab()
        ub_tab = self.__init_ub_tab()
        values_tab = self.__init_values_tab()

        ub_layout.addWidget(convert_tab)
        ub_layout.addLayout(convert_io_layout)

        ub_layout.addWidget(peaks_tab)
        ub_layout.addLayout(peaks_io_layout)

        ub_layout.addWidget(ub_tab)
        ub_layout.addLayout(ub_io_layout)

        ub_layout.addWidget(values_tab)

        ub_peaks_tab.setLayout(ub_layout)

    def __init_convert_tab(self):
        convert_tab = QTabWidget()

        convert_to_q_tab = QWidget()
        convert_to_q_tab_layout = QVBoxLayout()

        experiment_params_layout = QHBoxLayout()
        run_params_layout = QHBoxLayout()
        wavelength_params_layout = QHBoxLayout()
        instrument_params_layout = QGridLayout()

        self.instrument_combo = QComboBox(self)
        self.instrument_combo.addItem("TOPAZ")
        self.instrument_combo.addItem("MANDI")
        self.instrument_combo.addItem("CORELLI")
        self.instrument_combo.addItem("SNAP")
        self.instrument_combo.addItem("WAND²")
        self.instrument_combo.addItem("DEMAND")

        ipts_label = QLabel("IPTS:")
        exp_label = QLabel("Experiment:")
        run_label = QLabel("Runs:")
        filter_time_label = QLabel("Time Stop [s]:")
        angstrom_label = QLabel("Å")

        validator = QIntValidator(1, 1000000000, self)

        self.runs_line = QLineEdit("")

        self.ipts_line = QLineEdit("")
        self.ipts_line.setValidator(validator)

        self.exp_line = QLineEdit("")
        self.exp_line.setValidator(validator)

        self.cal_line = QLineEdit("")
        self.tube_line = QLineEdit("")

        self.wl_min_line = QLineEdit("0.3")
        self.wl_max_line = QLineEdit("3.5")

        wl_label = QLabel("λ:")

        notation = QDoubleValidator.StandardNotation

        validator = QDoubleValidator(0.2, 10, 5, notation=notation)

        self.wl_min_line.setValidator(validator)
        self.wl_max_line.setValidator(validator)

        d_min_label = QLabel("d(min):", self)

        self.convert_min_d_line = QLineEdit("0.7")
        self.convert_min_d_line.setValidator(validator)

        validator = QIntValidator(1, 1000, self)

        self.filter_time_line = QLineEdit("")
        self.filter_time_line.setValidator(validator)

        self.cal_browse_button = QPushButton("Detector", self)
        self.tube_browse_button = QPushButton("Tube", self)

        experiment_params_layout.addWidget(self.instrument_combo)
        experiment_params_layout.addWidget(ipts_label)
        experiment_params_layout.addWidget(self.ipts_line)
        experiment_params_layout.addWidget(exp_label)
        experiment_params_layout.addWidget(self.exp_line)

        run_params_layout.addWidget(run_label)
        run_params_layout.addWidget(self.runs_line)

        wavelength_params_layout.addWidget(wl_label)
        wavelength_params_layout.addWidget(self.wl_min_line)
        wavelength_params_layout.addWidget(self.wl_max_line)
        wavelength_params_layout.addWidget(angstrom_label)

        instrument_params_layout.addWidget(self.cal_line, 1, 0)
        instrument_params_layout.addWidget(self.cal_browse_button, 1, 1)
        instrument_params_layout.addWidget(self.tube_line, 2, 0)
        instrument_params_layout.addWidget(self.tube_browse_button, 2, 1)

        self.convert_to_q_button = QPushButton("Convert", self)

        self.lorentz_box = QCheckBox("Lorentz Correction", self)
        self.lorentz_box.setChecked(True)

        convert_to_q_action_layout = QHBoxLayout()
        convert_to_q_action_layout.addWidget(self.convert_to_q_button)
        convert_to_q_action_layout.addWidget(self.lorentz_box)
        convert_to_q_action_layout.addWidget(filter_time_label)
        convert_to_q_action_layout.addWidget(self.filter_time_line)
        convert_to_q_action_layout.addStretch(1)
        convert_to_q_action_layout.addWidget(d_min_label)
        convert_to_q_action_layout.addWidget(self.convert_min_d_line)
        convert_to_q_action_layout.addLayout(wavelength_params_layout)

        convert_to_q_tab_layout.addLayout(experiment_params_layout)
        convert_to_q_tab_layout.addLayout(run_params_layout)
        convert_to_q_tab_layout.addLayout(wavelength_params_layout)
        convert_to_q_tab_layout.addLayout(instrument_params_layout)
        convert_to_q_tab_layout.addStretch(1)
        convert_to_q_tab_layout.addLayout(convert_to_q_action_layout)

        convert_to_q_tab.setLayout(convert_to_q_tab_layout)

        convert_tab.addTab(convert_to_q_tab, "Convert To Q")

        return convert_tab

    def __init_peaks_tab(self):
        peaks_tab = QTabWidget()

        find_tab = QWidget()
        find_tab_layout = QVBoxLayout()

        max_peaks_label = QLabel("Max Peaks:")
        min_distance_label = QLabel("Min Distance:")
        max_spacing_label = QLabel("Max Spacing:")
        density_threshold_label = QLabel("Min Density:")
        find_edge_label = QLabel("Edge Pixels:")
        distance_unit_label = QLabel("Å⁻¹")
        angstrom_unit_label = QLabel("Å")
        self.aluminum_box = QCheckBox("Avoid Aluminum", self)
        self.aluminum_box.setChecked(True)

        validator = QIntValidator(10, 1000, self)

        self.max_peaks_line = QLineEdit("100")
        self.max_peaks_line.setValidator(validator)

        validator = QIntValidator(1, 100000, self)

        self.density_threshold_line = QLineEdit("100")
        self.density_threshold_line.setValidator(validator)

        notation = QDoubleValidator.StandardNotation

        validator = QDoubleValidator(0.01, 10, 4, notation=notation)

        self.min_distance_line = QLineEdit("0.20")
        self.min_distance_line.setValidator(validator)

        validator = QDoubleValidator(0.1, 100, 4, notation=notation)

        self.max_spacing_line = QLineEdit("31.46")
        self.max_spacing_line.setValidator(validator)

        validator = QIntValidator(0, 64, self)

        self.find_edge_line = QLineEdit("0")
        self.find_edge_line.setValidator(validator)

        find_params_layout = QGridLayout()

        find_params_layout.addWidget(max_peaks_label, 0, 0)
        find_params_layout.addWidget(self.max_peaks_line, 0, 1)
        find_params_layout.addWidget(min_distance_label, 0, 2)
        find_params_layout.addWidget(self.min_distance_line, 0, 3)
        find_params_layout.addWidget(distance_unit_label, 0, 4)
        find_params_layout.addWidget(max_spacing_label, 1, 2)
        find_params_layout.addWidget(self.max_spacing_line, 1, 3)
        find_params_layout.addWidget(angstrom_unit_label, 1, 4)

        find_params_layout.addWidget(density_threshold_label, 1, 0)
        find_params_layout.addWidget(self.density_threshold_line, 1, 1)

        find_params_layout.addWidget(find_edge_label, 2, 0)
        find_params_layout.addWidget(self.find_edge_line, 2, 1)

        self.find_button = QPushButton("Find", self)

        find_action_layout = QHBoxLayout()
        find_action_layout.addWidget(self.find_button)
        find_action_layout.addWidget(self.aluminum_box)
        find_action_layout.addStretch(1)

        find_tab_layout.addLayout(find_params_layout)
        find_tab_layout.addStretch(1)
        find_tab_layout.addLayout(find_action_layout)

        find_tab.setLayout(find_tab_layout)

        index_tab = QWidget()
        index_tab_layout = QVBoxLayout()

        index_tolerance_label = QLabel("Tolerance:")

        notation = QDoubleValidator.StandardNotation

        validator = QDoubleValidator(0.01, 1, 5, notation=notation)

        self.index_sat_box = QCheckBox("Satellite", self)
        self.index_sat_box.setChecked(False)

        self.index_tolerance_line = QLineEdit("0.1")
        self.index_tolerance_line.setValidator(validator)

        self.index_sat_tolerance_line = QLineEdit("0.1")
        self.index_sat_tolerance_line.setValidator(validator)

        index_params_layout = QGridLayout()

        index_params_layout.addWidget(index_tolerance_label, 0, 0)
        index_params_layout.addWidget(self.index_tolerance_line, 0, 1)
        index_params_layout.addWidget(self.index_sat_tolerance_line, 0, 2)
        index_params_layout.addWidget(self.index_sat_box, 1, 2)

        self.round_box = QCheckBox("Round hkl", self)
        self.round_box.setChecked(True)

        self.index_button = QPushButton("Index", self)

        index_action_layout = QHBoxLayout()
        index_action_layout.addWidget(self.index_button)
        index_action_layout.addWidget(self.round_box)
        index_action_layout.addStretch(1)

        index_tab_layout.addLayout(index_params_layout)
        index_tab_layout.addStretch(1)
        index_tab_layout.addLayout(index_action_layout)

        index_tab.setLayout(index_tab_layout)

        centering_label = QLabel("Centering:")

        self.centering_combo = QComboBox(self)
        self.centering_combo.addItem("P")
        self.centering_combo.addItem("I")
        self.centering_combo.addItem("F")
        self.centering_combo.addItem("Robv")
        self.centering_combo.addItem("Rrev")
        self.centering_combo.addItem("A")
        self.centering_combo.addItem("B")
        self.centering_combo.addItem("C")
        self.centering_combo.addItem("H")

        min_d_unit_label = QLabel("Å")

        min_d_label = QLabel("Min d-spacing:")
        predict_edge_label = QLabel("Edge Pixels:")

        self.predict_sat_box = QCheckBox("Satellite", self)
        self.predict_sat_box.setChecked(False)

        notation = QDoubleValidator.StandardNotation

        validator = QDoubleValidator(0.4, 100, 3, notation=notation)

        self.min_d_line = QLineEdit("0.7")
        self.min_d_line.setValidator(validator)

        self.min_sat_d_line = QLineEdit("1.0")
        self.min_sat_d_line.setValidator(validator)

        validator = QIntValidator(0, 64, self)

        self.predict_edge_line = QLineEdit("0")
        self.predict_edge_line.setValidator(validator)

        predict_tab = QWidget()
        predict_tab_layout = QVBoxLayout()

        predict_params_layout = QGridLayout()

        predict_params_layout.addWidget(centering_label, 0, 0)
        predict_params_layout.addWidget(self.centering_combo, 0, 1)
        predict_params_layout.addWidget(min_d_label, 1, 0)
        predict_params_layout.addWidget(self.min_d_line, 1, 1)
        predict_params_layout.addWidget(self.min_sat_d_line, 1, 2)
        predict_params_layout.addWidget(min_d_unit_label, 1, 3)
        predict_params_layout.addWidget(predict_edge_label, 2, 0)
        predict_params_layout.addWidget(self.predict_edge_line, 2, 1)
        predict_params_layout.addWidget(self.predict_sat_box, 2, 2)

        self.predict_button = QPushButton("Predict", self)

        predict_action_layout = QHBoxLayout()
        predict_action_layout.addWidget(self.predict_button)
        predict_action_layout.addStretch(1)

        predict_tab_layout.addLayout(predict_params_layout)
        predict_tab_layout.addStretch(1)
        predict_tab_layout.addLayout(predict_action_layout)

        predict_tab.setLayout(predict_tab_layout)

        self.centroid_box = QCheckBox("Centroid", self)
        self.centroid_box.setChecked(True)

        self.adaptive_box = QCheckBox("Adaptive Envelope", self)
        self.adaptive_box.setChecked(True)

        radius_label = QLabel("Radius:")
        inner_label = QLabel("Inner Factor:")
        outer_label = QLabel("Outer Factor:")
        radius_unit_label = QLabel("Å⁻¹")

        notation = QDoubleValidator.StandardNotation

        validator = QDoubleValidator(0, 1, 3, notation=notation)

        self.radius_line = QLineEdit("0.25")
        self.radius_line.setValidator(validator)

        notation = QDoubleValidator.StandardNotation

        validator = QDoubleValidator(1, 3, 3, notation=notation)

        self.inner_line = QLineEdit("1.5")
        self.inner_line.setValidator(validator)

        self.outer_line = QLineEdit("2")
        self.outer_line.setValidator(validator)

        integrate_tab = QWidget()
        integrate_tab_layout = QVBoxLayout()

        integrate_params_layout = QGridLayout()

        integrate_params_layout.addWidget(radius_label, 0, 0)
        integrate_params_layout.addWidget(self.radius_line, 0, 1)
        integrate_params_layout.addWidget(radius_unit_label, 0, 2)
        integrate_params_layout.addWidget(inner_label, 2, 0)
        integrate_params_layout.addWidget(self.inner_line, 2, 1)
        integrate_params_layout.addWidget(outer_label, 2, 2)
        integrate_params_layout.addWidget(self.outer_line, 2, 3)

        self.integrate_button = QPushButton("Integrate", self)

        integrate_action_layout = QHBoxLayout()
        integrate_action_layout.addWidget(self.integrate_button)
        integrate_action_layout.addWidget(self.centroid_box)
        integrate_action_layout.addWidget(self.adaptive_box)
        integrate_action_layout.addStretch(1)

        integrate_tab_layout.addLayout(integrate_params_layout)
        integrate_tab_layout.addStretch(1)
        integrate_tab_layout.addLayout(integrate_action_layout)

        integrate_tab.setLayout(integrate_tab_layout)

        self.filter_combo = QComboBox(self)
        self.filter_combo.addItem("I/σ")
        self.filter_combo.addItem("d")
        self.filter_combo.addItem("λ")
        self.filter_combo.addItem("Q")
        self.filter_combo.addItem("h^2+k^2+l^2")
        self.filter_combo.addItem("m^2+n^2+p^2")
        self.filter_combo.addItem("Run #")

        self.comparison_combo = QComboBox(self)
        self.comparison_combo.addItem(">")
        self.comparison_combo.addItem("<")
        self.comparison_combo.addItem(">=")
        self.comparison_combo.addItem("<=")
        self.comparison_combo.addItem("=")
        self.comparison_combo.addItem("!=")

        notation = QDoubleValidator.StandardNotation

        validator = QDoubleValidator(-1e6, 1e6, 3, notation=notation)

        self.filter_line = QLineEdit("0")
        self.filter_line.setValidator(validator)

        filter_tab = QWidget()
        filter_tab_layout = QVBoxLayout()

        filter_params_layout = QHBoxLayout()

        filter_params_layout.addWidget(self.filter_combo)
        filter_params_layout.addWidget(self.comparison_combo)
        filter_params_layout.addWidget(self.filter_line)

        self.filter_button = QPushButton("Filter", self)

        filter_action_layout = QHBoxLayout()
        filter_action_layout.addWidget(self.filter_button)
        filter_action_layout.addStretch(1)

        filter_tab_layout.addLayout(filter_params_layout)
        filter_tab_layout.addStretch(1)
        filter_tab_layout.addLayout(filter_action_layout)

        filter_tab.setLayout(filter_tab_layout)

        peaks_tab.addTab(find_tab, "Find Peaks")
        peaks_tab.addTab(index_tab, "Index Peaks")
        peaks_tab.addTab(predict_tab, "Predict Peaks")
        peaks_tab.addTab(integrate_tab, "Integrate Peaks")
        peaks_tab.addTab(filter_tab, "Filter Peaks")

        return peaks_tab

    def __init_ub_tab(self):
        notation = QDoubleValidator.StandardNotation

        validator = QDoubleValidator(0.01, 1, 5, notation=notation)

        ub_tab = QTabWidget()

        calculate_tolerance_label = QLabel("Tolerance:")

        self.calculate_tolerance_line = QLineEdit("0.1")
        self.calculate_tolerance_line.setValidator(validator)

        max_scalar_error_label = QLabel("Max Scalar Error:")

        self.max_scalar_error_line = QLineEdit("0.2")
        self.max_scalar_error_line.setValidator(validator)

        calculate_tab = QWidget()
        calculate_tab_layout = QVBoxLayout()

        calculate_params_layout = QGridLayout()

        calculate_params_layout.addWidget(calculate_tolerance_label, 0, 0)
        calculate_params_layout.addWidget(self.calculate_tolerance_line, 0, 1)
        calculate_params_layout.addWidget(max_scalar_error_label, 0, 2)
        calculate_params_layout.addWidget(self.max_scalar_error_line, 0, 3)

        self.conventional_button = QPushButton("Conventional", self)
        self.niggli_button = QPushButton("Primitive", self)
        self.select_button = QPushButton("Select", self)

        self.form_line = QLineEdit("")
        self.form_line.setReadOnly(True)

        form_label = QLabel("Form:")

        min_const_label = QLabel("Min(a,b,c) [Å]:")
        max_const_label = QLabel("Max(a,b,c) [Å]:")

        self.min_const_line = QLineEdit("5")
        self.max_const_line = QLineEdit("15")

        notation = QDoubleValidator.StandardNotation

        validator = QDoubleValidator(0.1, 1000, 4, notation=notation)

        self.min_const_line.setValidator(validator)
        self.max_const_line.setValidator(validator)

        const_layout = QHBoxLayout()
        const_layout.addWidget(min_const_label)
        const_layout.addWidget(self.min_const_line)
        const_layout.addWidget(max_const_label)
        const_layout.addWidget(self.max_const_line)

        calculate_action_layout = QHBoxLayout()
        calculate_action_layout.addWidget(self.conventional_button)
        calculate_action_layout.addStretch(1)
        calculate_action_layout.addLayout(const_layout)
        calculate_action_layout.addWidget(self.niggli_button)
        calculate_action_layout.addWidget(form_label)
        calculate_action_layout.addWidget(self.form_line)
        calculate_action_layout.addWidget(self.select_button)

        stretch = QHeaderView.Stretch

        self.cell_table = QTableWidget()
        self.cell_table.setRowCount(0)
        self.cell_table.setColumnCount(9)

        header = ["Error", "Bravais", "a", "b", "c", "α", "β", "γ", "V"]

        self.cell_table.horizontalHeader().setSectionResizeMode(stretch)
        self.cell_table.setHorizontalHeaderLabels(header)
        self.cell_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.cell_table.setSelectionBehavior(QTableWidget.SelectRows)
        # self.cell_table.setSortingEnabled(True)

        calculate_tab_layout.addLayout(calculate_params_layout)
        calculate_tab_layout.addWidget(self.cell_table)
        calculate_tab_layout.addLayout(calculate_action_layout)

        calculate_tab.setLayout(calculate_tab_layout)

        transform_tolerance_label = QLabel("Tolerance:")

        self.transform_tolerance_line = QLineEdit("0.1")
        self.transform_tolerance_line.setValidator(validator)

        self.lattice_combo = QComboBox(self)
        self.lattice_combo.addItem("Triclinic")
        self.lattice_combo.addItem("Monoclinic")
        self.lattice_combo.addItem("Orthorhombic")
        self.lattice_combo.addItem("Tetragonal")
        self.lattice_combo.addItem("Rhombohedral")
        self.lattice_combo.addItem("Hexagonal")
        self.lattice_combo.addItem("Cubic")

        self.symmetry_combo = QComboBox(self)
        self.symmetry_combo.addItem("x,y,z")
        self.symmetry_combo.addItem("-x,-y,-z")

        notation = QDoubleValidator.StandardNotation

        validator = QDoubleValidator(-10, 10, 5, notation=notation)

        self.T11_line = QLineEdit("1")
        self.T12_line = QLineEdit("0")
        self.T13_line = QLineEdit("0")

        self.T21_line = QLineEdit("0")
        self.T22_line = QLineEdit("1")
        self.T23_line = QLineEdit("0")

        self.T31_line = QLineEdit("0")
        self.T32_line = QLineEdit("0")
        self.T33_line = QLineEdit("1")

        self.T11_line.setValidator(validator)
        self.T12_line.setValidator(validator)
        self.T13_line.setValidator(validator)

        self.T21_line.setValidator(validator)
        self.T22_line.setValidator(validator)
        self.T23_line.setValidator(validator)

        self.T31_line.setValidator(validator)
        self.T32_line.setValidator(validator)
        self.T33_line.setValidator(validator)

        hp_label = QLabel("h′:")
        kp_label = QLabel("k′:")
        lp_label = QLabel("l′:")

        h_label = QLabel("h")
        k_label = QLabel("k")
        l_label = QLabel("l")

        transform_tab = QWidget()
        transform_tab_layout = QVBoxLayout()

        transform_params_layout = QHBoxLayout()

        transform_params_layout.addWidget(transform_tolerance_label)
        transform_params_layout.addWidget(self.transform_tolerance_line)
        transform_params_layout.addWidget(self.lattice_combo)
        transform_params_layout.addWidget(self.symmetry_combo)

        transform_matrix_layout = QGridLayout()

        transform_matrix_layout.addWidget(h_label, 0, 1, Qt.AlignCenter)
        transform_matrix_layout.addWidget(k_label, 0, 2, Qt.AlignCenter)
        transform_matrix_layout.addWidget(l_label, 0, 3, Qt.AlignCenter)
        transform_matrix_layout.addWidget(hp_label, 1, 0)
        transform_matrix_layout.addWidget(self.T11_line, 1, 1)
        transform_matrix_layout.addWidget(self.T12_line, 1, 2)
        transform_matrix_layout.addWidget(self.T13_line, 1, 3)
        transform_matrix_layout.addWidget(kp_label, 2, 0)
        transform_matrix_layout.addWidget(self.T21_line, 2, 1)
        transform_matrix_layout.addWidget(self.T22_line, 2, 2)
        transform_matrix_layout.addWidget(self.T23_line, 2, 3)
        transform_matrix_layout.addWidget(lp_label, 3, 0)
        transform_matrix_layout.addWidget(self.T31_line, 3, 1)
        transform_matrix_layout.addWidget(self.T32_line, 3, 2)
        transform_matrix_layout.addWidget(self.T33_line, 3, 3)

        self.transform_button = QPushButton("Transform", self)

        transform_action_layout = QHBoxLayout()
        transform_action_layout.addWidget(self.transform_button)
        transform_action_layout.addStretch(1)
        transform_action_layout.addLayout(transform_params_layout)

        transform_tab_layout.addLayout(transform_matrix_layout)
        transform_tab_layout.addStretch(1)
        transform_tab_layout.addLayout(transform_action_layout)

        transform_tab.setLayout(transform_tab_layout)

        refine_tolerance_label = QLabel("Tolerance:")

        notation = QDoubleValidator.StandardNotation

        validator = QDoubleValidator(0.01, 1, 5, notation=notation)

        self.refine_tolerance_line = QLineEdit("0.1")
        self.refine_tolerance_line.setValidator(validator)

        self.optimize_combo = QComboBox(self)
        self.optimize_combo.addItem("Unconstrained")
        self.optimize_combo.addItem("Constrained")
        self.optimize_combo.addItem("Triclinic")
        self.optimize_combo.addItem("Monoclinic")
        self.optimize_combo.addItem("Orthorhombic")
        self.optimize_combo.addItem("Tetragonal")
        self.optimize_combo.addItem("Rhombohedral")
        self.optimize_combo.addItem("Hexagonal")
        self.optimize_combo.addItem("Cubic")

        refine_tab = QWidget()
        refine_tab_layout = QVBoxLayout()

        refine_params_layout = QHBoxLayout()
        refine_params_layout.addWidget(refine_tolerance_label)
        refine_params_layout.addWidget(self.refine_tolerance_line)
        refine_params_layout.addWidget(self.optimize_combo)

        self.refine_button = QPushButton("Refine", self)

        refine_action_layout = QHBoxLayout()
        refine_action_layout.addWidget(self.refine_button)
        refine_action_layout.addStretch(1)

        refine_tab_layout.addLayout(refine_params_layout)
        refine_tab_layout.addStretch(1)
        refine_tab_layout.addLayout(refine_action_layout)

        refine_tab.setLayout(refine_tab_layout)

        ub_tab.addTab(calculate_tab, "Calculate UB")
        ub_tab.addTab(transform_tab, "Transform UB")
        ub_tab.addTab(refine_tab, "Refine UB")

        return ub_tab

    def __init_values_tab(self):
        values_tab = QTabWidget()

        parameters_tab = QWidget()
        orientation_tab = QWidget()
        satellite_tab = QWidget()

        self.a_line = QLineEdit()
        self.b_line = QLineEdit()
        self.c_line = QLineEdit()

        self.alpha_line = QLineEdit()
        self.beta_line = QLineEdit()
        self.gamma_line = QLineEdit()

        pattern = r"^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?(\(\d+\))?$$"
        regex = QRegExp(pattern)
        validator = QRegExpValidator(regex)

        self.a_line.setValidator(validator)
        self.b_line.setValidator(validator)
        self.c_line.setValidator(validator)

        self.alpha_line.setValidator(validator)
        self.beta_line.setValidator(validator)
        self.gamma_line.setValidator(validator)

        a_label = QLabel("a:")
        b_label = QLabel("b:")
        c_label = QLabel("c:")

        alpha_label = QLabel("α:")
        beta_label = QLabel("β:")
        gamma_label = QLabel("γ:")

        angstrom_label = QLabel("Å")
        degree_label = QLabel("°")

        parameters_layout = QGridLayout()

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

        notation = QDoubleValidator.StandardNotation

        validator = QDoubleValidator(-5, 5, 4, notation=notation)

        self.dh1_line = QLineEdit("0.0")
        self.dk1_line = QLineEdit("0.0")
        self.dl1_line = QLineEdit("0.0")

        self.dh2_line = QLineEdit("0.0")
        self.dk2_line = QLineEdit("0.0")
        self.dl2_line = QLineEdit("0.0")

        self.dh3_line = QLineEdit("0.0")
        self.dk3_line = QLineEdit("0.0")
        self.dl3_line = QLineEdit("0.0")

        self.dh1_line.setValidator(validator)
        self.dk1_line.setValidator(validator)
        self.dl1_line.setValidator(validator)

        self.dh2_line.setValidator(validator)
        self.dk2_line.setValidator(validator)
        self.dl2_line.setValidator(validator)

        self.dh3_line.setValidator(validator)
        self.dk3_line.setValidator(validator)
        self.dl3_line.setValidator(validator)

        self.max_order_line = QLineEdit("0")

        mod_vec1_label = QLabel("1:")
        mod_vec2_label = QLabel("2:")
        mod_vec3_label = QLabel("3:")

        dh_label = QLabel("Δh")
        dk_label = QLabel("Δk")
        dl_label = QLabel("Δl")

        max_order_label = QLabel("Max Order")

        self.cross_box = QCheckBox("Cross Terms", self)
        self.cross_box.setChecked(False)

        satellite_layout = QGridLayout()

        satellite_layout.addWidget(dh_label, 0, 1, Qt.AlignCenter)
        satellite_layout.addWidget(dk_label, 0, 2, Qt.AlignCenter)
        satellite_layout.addWidget(dl_label, 0, 3, Qt.AlignCenter)
        satellite_layout.addWidget(max_order_label, 0, 4, Qt.AlignCenter)
        satellite_layout.addWidget(mod_vec1_label, 1, 0)
        satellite_layout.addWidget(self.dh1_line, 1, 1)
        satellite_layout.addWidget(self.dk1_line, 1, 2)
        satellite_layout.addWidget(self.dl1_line, 1, 3)
        satellite_layout.addWidget(self.max_order_line, 1, 4)
        satellite_layout.addWidget(mod_vec2_label, 2, 0)
        satellite_layout.addWidget(self.dh2_line, 2, 1)
        satellite_layout.addWidget(self.dk2_line, 2, 2)
        satellite_layout.addWidget(self.dl2_line, 2, 3)
        satellite_layout.addWidget(self.cross_box, 2, 4)
        satellite_layout.addWidget(mod_vec3_label, 3, 0)
        satellite_layout.addWidget(self.dh3_line, 3, 1)
        satellite_layout.addWidget(self.dk3_line, 3, 2)
        satellite_layout.addWidget(self.dl3_line, 3, 3)

        x_label = QLabel("x:")
        y_label = QLabel("y:")
        z_label = QLabel("z:")

        a_star_label = QLabel("a*")
        b_star_label = QLabel("b*")
        c_star_label = QLabel("c*")

        self.uh_line = QLineEdit()
        self.uk_line = QLineEdit()
        self.ul_line = QLineEdit()

        self.vh_line = QLineEdit()
        self.vk_line = QLineEdit()
        self.vl_line = QLineEdit()

        self.wh_line = QLineEdit()
        self.wk_line = QLineEdit()
        self.wl_line = QLineEdit()

        self.uh_line.setReadOnly(False)
        self.uk_line.setReadOnly(False)
        self.ul_line.setReadOnly(False)

        self.vh_line.setReadOnly(False)
        self.vk_line.setReadOnly(False)
        self.vl_line.setReadOnly(False)

        self.wh_line.setReadOnly(False)
        self.wk_line.setReadOnly(False)
        self.wl_line.setReadOnly(False)

        orientation_layout = QGridLayout()

        orientation_layout.addWidget(a_star_label, 0, 1, Qt.AlignCenter)
        orientation_layout.addWidget(b_star_label, 0, 2, Qt.AlignCenter)
        orientation_layout.addWidget(c_star_label, 0, 3, Qt.AlignCenter)
        orientation_layout.addWidget(y_label, 1, 0)
        orientation_layout.addWidget(self.wh_line, 1, 1)
        orientation_layout.addWidget(self.wk_line, 1, 2)
        orientation_layout.addWidget(self.wl_line, 1, 3)
        orientation_layout.addWidget(z_label, 2, 0)
        orientation_layout.addWidget(self.uh_line, 2, 1)
        orientation_layout.addWidget(self.uk_line, 2, 2)
        orientation_layout.addWidget(self.ul_line, 2, 3)
        orientation_layout.addWidget(x_label, 3, 0)
        orientation_layout.addWidget(self.vh_line, 3, 1)
        orientation_layout.addWidget(self.vk_line, 3, 2)
        orientation_layout.addWidget(self.vl_line, 3, 3)

        lattice_layout = QVBoxLayout()

        lattice_layout.addLayout(parameters_layout)
        lattice_layout.addStretch(1)

        parameters_tab.setLayout(lattice_layout)
        orientation_tab.setLayout(orientation_layout)
        satellite_tab.setLayout(satellite_layout)

        values_tab.addTab(parameters_tab, "Lattice Parameters")
        values_tab.addTab(orientation_tab, "Sample Orientation")
        values_tab.addTab(satellite_tab, "Modulation Parameters")

        return values_tab

    def connect_bindings(self) -> None:
        self.view_model.add_Q_viz_bind.connect("ub_add_q_viz", self.plotter.add_Q_viz)
        self.view_model.q_conversion_bind.connect(
            "ub_q_conversion", self.set_q_conversion
        )

    def connect_widgets(self) -> None:
        self.cal_line.editingFinished.connect(
            lambda: self.view_model.set_q_conversion_field(
                "detector_calibration", self.cal_line.text()
            )
        )
        self.convert_min_d_line.editingFinished.connect(
            lambda: self.view_model.set_q_conversion_field(
                "d_min", self.convert_min_d_line.text()
            )
        )
        self.convert_to_q_button.clicked.connect(self.view_model.convert_Q)
        self.exp_line.editingFinished.connect(
            lambda: self.view_model.set_q_conversion_field(
                "experiment_number", self.exp_line.text()
            )
        )
        self.filter_time_line.editingFinished.connect(
            lambda: self.view_model.set_q_conversion_field(
                "time_stop", self.filter_time_line.text()
            )
        )
        self.instrument_combo.activated.connect(
            lambda: self.view_model.set_q_conversion_field(
                "instrument", self.instrument_combo.currentText()
            )
        )
        self.ipts_line.editingFinished.connect(
            lambda: self.view_model.set_q_conversion_field(
                "ipts_number", self.ipts_line.text()
            )
        )
        self.lorentz_box.clicked.connect(
            lambda: self.view_model.set_q_conversion_field(
                "lorentz_correction", self.lorentz_box.isChecked()
            )
        )
        self.runs_line.editingFinished.connect(
            lambda: self.view_model.set_q_conversion_field(
                "runs", self.runs_line.text()
            )
        )
        self.tube_line.editingFinished.connect(
            lambda: self.view_model.set_q_conversion_field(
                "tube_calibration", self.tube_line.text()
            )
        )
        self.wl_max_line.editingFinished.connect(
            lambda: self.view_model.set_q_conversion_field(
                "wl_max", self.wl_max_line.text()
            )
        )
        self.wl_min_line.editingFinished.connect(
            lambda: self.view_model.set_q_conversion_field(
                "wl_min", self.wl_min_line.text()
            )
        )

    def set_q_conversion(self, q_conversion: QConversion):
        self.cal_line.setText(q_conversion.detector_calibration)
        self.convert_min_d_line.setText(str(round(q_conversion.d_min, 5)))
        if q_conversion.experiment_number:
            self.exp_line.setText(str(q_conversion.experiment_number))
        else:
            self.exp_line.setText("")
        if q_conversion.time_stop:
            self.filter_time_line.setText(str(q_conversion.time_stop))
        else:
            self.filter_time_line.setText("")
        self.instrument_combo.setCurrentText(q_conversion.instrument)
        if q_conversion.ipts_number:
            self.ipts_line.setText(str(q_conversion.ipts_number))
        else:
            self.ipts_line.setText("")
        self.lorentz_box.setChecked(q_conversion.lorentz_correction)
        self.runs_line.setText(",".join(map(str, q_conversion.runs)))
        self.tube_line.setText(q_conversion.tube_calibration)
        self.wl_max_line.setText(str(round(q_conversion.wl_max, 5)))
        self.wl_min_line.setText(str(round(q_conversion.wl_min, 5)))

        self.cal_browse_button.setDisabled(q_conversion.detector_disabled)
        self.cal_line.setDisabled(q_conversion.detector_disabled)
        self.exp_line.setDisabled(q_conversion.experiment_disabled)
        self.filter_time_line.setDisabled(q_conversion.time_stop_disabled)
        self.tube_browse_button.setDisabled(q_conversion.tube_disabled)
        self.tube_line.setDisabled(q_conversion.tube_disabled)
        self.wl_max_line.setDisabled(q_conversion.wl_max_disabled)
