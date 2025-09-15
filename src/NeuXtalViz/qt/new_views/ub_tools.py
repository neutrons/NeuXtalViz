from PyQt5.QtWidgets import QFrame
from matplotlib.backends.backend_qtagg import FigureCanvas, NavigationToolbar2QT
from matplotlib.figure import Figure
from pyvistaqt import QtInteractor  # type: ignore
from qtpy.QtCore import Qt, QRegExp
from qtpy.QtGui import QDoubleValidator, QIntValidator, QRegExpValidator
from qtpy.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QHBoxLayout,
    QPushButton,
    QSlider,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from NeuXtalViz.components.visualization_panel.view_qt import VisPanelWidget
from NeuXtalViz.qt.new_views.pydantic_utils import process_change
from NeuXtalViz.view_models.ub_tools import (
    InstrumentParameters,
    ModulationClusters,
    Parameters,
    Peaks,
    QConversion,
    UBControls,
    UBViewModel,
)
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

        self.canvas_slice = FigureCanvas(Figure(figsize=(12.8, 12.8)))
        self.canvas_inst = FigureCanvas(Figure(constrained_layout=True))
        self.canvas_scan = FigureCanvas(Figure(constrained_layout=True))
        self.canvas_clust = FigureCanvas(Figure(tight_layout=True))
        self.plotter = UBPlotter(
            self.view_model,
            plotter,
            self.canvas_slice.figure,
            self.canvas_inst.figure,
            self.canvas_scan.figure,
            self.canvas_clust.figure,
        )

        layout.addWidget(self.vis_widget)
        self.tab_widget = QTabWidget(self)

        self.parameters_tab()
        self.table_tab()
        self.verify_tab()
        self.modulation_tab()

        layout.addWidget(self.tab_widget, stretch=1)
        self.setLayout(layout)

        self.connect_bindings()
        self.connect_widgets()

        self.view_model.switch_instrument()
        self.view_model.lattice_transform()

    def parameters_tab(self):
        ub_peaks_tab = QWidget()
        self.tab_widget.addTab(ub_peaks_tab, "Parameters")

        ub_layout = QVBoxLayout()

        self.save_q_button = QPushButton("Save Q", self)
        self.save_q_button.clicked.connect(self.save_Q)
        self.load_q_button = QPushButton("Load Q", self)
        self.load_q_button.clicked.connect(self.load_Q)

        self.save_peaks_button = QPushButton("Save Peaks", self)
        self.save_peaks_button.clicked.connect(self.save_peaks)
        self.load_peaks_button = QPushButton("Load Peaks", self)
        self.load_peaks_button.clicked.connect(self.load_peaks)

        self.save_ub_button = QPushButton("Save UB", self)
        self.save_ub_button.clicked.connect(self.save_UB)
        self.load_ub_button = QPushButton("Load UB", self)
        self.load_ub_button.clicked.connect(self.load_UB)

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

    def table_tab(self):
        peaks_table_tab = QWidget()
        self.tab_widget.addTab(peaks_table_tab, "Peaks")

        peaks_layout = QVBoxLayout()

        calculator_layout = QGridLayout()

        h_label = QLabel("h", self)
        k_label = QLabel("k", self)
        l_label = QLabel("l", self)

        peak_1_label = QLabel("1:", self)
        peak_2_label = QLabel("2:", self)

        notation = QDoubleValidator.StandardNotation

        validator = QDoubleValidator(-100, 100, 5, notation=notation)

        self.h1_line = QLineEdit()
        self.k1_line = QLineEdit()
        self.l1_line = QLineEdit()

        self.h2_line = QLineEdit()
        self.k2_line = QLineEdit()
        self.l2_line = QLineEdit()

        self.h1_line.setValidator(validator)
        self.k1_line.setValidator(validator)
        self.l1_line.setValidator(validator)

        self.h2_line.setValidator(validator)
        self.k2_line.setValidator(validator)
        self.l2_line.setValidator(validator)

        d_label = QLabel("d [Å]", self)

        phi_label = QLabel("φ [°]", self)

        self.d1_line = QLineEdit()
        self.d2_line = QLineEdit()
        self.phi_line = QLineEdit()

        self.d1_line.setEnabled(False)
        self.d2_line.setEnabled(False)
        self.phi_line.setEnabled(False)

        self.calculate = QPushButton("Calculate", self)

        calculator_layout.addWidget(h_label, 0, 1, Qt.AlignCenter)
        calculator_layout.addWidget(k_label, 0, 2, Qt.AlignCenter)
        calculator_layout.addWidget(l_label, 0, 3, Qt.AlignCenter)
        calculator_layout.addWidget(d_label, 0, 4, Qt.AlignCenter)
        calculator_layout.addWidget(phi_label, 0, 5, Qt.AlignCenter)

        calculator_layout.addWidget(peak_1_label, 1, 0)
        calculator_layout.addWidget(self.h1_line, 1, 1)
        calculator_layout.addWidget(self.k1_line, 1, 2)
        calculator_layout.addWidget(self.l1_line, 1, 3)
        calculator_layout.addWidget(self.d1_line, 1, 4)
        calculator_layout.addWidget(self.phi_line, 1, 5)

        calculator_layout.addWidget(peak_2_label, 2, 0)
        calculator_layout.addWidget(self.h2_line, 2, 1)
        calculator_layout.addWidget(self.k2_line, 2, 2)
        calculator_layout.addWidget(self.l2_line, 2, 3)
        calculator_layout.addWidget(self.d2_line, 2, 4)
        calculator_layout.addWidget(self.calculate, 2, 5)

        stretch = QHeaderView.Stretch

        self.peaks_table = QTableWidget()
        self.peaks_table.setRowCount(0)
        self.peaks_table.setColumnCount(8)

        header = ["h", "k", "l", "d", "λ", "I", "I/σ", "#"]

        self.peaks_table.horizontalHeader().setSectionResizeMode(stretch)
        self.peaks_table.setHorizontalHeaderLabels(header)
        self.peaks_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.peaks_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.peaks_table.setSortingEnabled(True)

        extended_info = QGridLayout()

        d_label = QLabel("d [Å]:", self)
        lambda_label = QLabel("λ [Å]:", self)

        run_label = QLabel("Run #", self)
        bank_label = QLabel("Bank #", self)
        row_label = QLabel("Row #", self)
        col_label = QLabel("Col #", self)

        self.d_line = QLineEdit()
        self.lambda_line = QLineEdit()
        self.run_line = QLineEdit()
        self.bank_line = QLineEdit()
        self.row_line = QLineEdit()
        self.col_line = QLineEdit()

        self.d_line.setEnabled(False)
        self.lambda_line.setEnabled(False)
        self.run_line.setEnabled(False)
        self.bank_line.setEnabled(False)
        self.row_line.setEnabled(False)
        self.col_line.setEnabled(False)

        self.intensity_line = QLineEdit()
        self.sigma_line = QLineEdit()

        self.intensity_line.setEnabled(False)
        self.sigma_line.setEnabled(False)

        intensity_label = QLabel("I: ", self)
        sigma_label = QLabel("± σ:", self)

        extended_info.addWidget(intensity_label, 0, 0)
        extended_info.addWidget(self.intensity_line, 0, 1)
        extended_info.addWidget(sigma_label, 0, 2)
        extended_info.addWidget(self.sigma_line, 0, 3)

        extended_info.addWidget(d_label, 0, 4)
        extended_info.addWidget(self.d_line, 0, 5)
        extended_info.addWidget(lambda_label, 0, 6)
        extended_info.addWidget(self.lambda_line, 0, 7)

        extended_info.addWidget(run_label, 1, 0)
        extended_info.addWidget(self.run_line, 1, 1)
        extended_info.addWidget(bank_label, 1, 2)
        extended_info.addWidget(self.bank_line, 1, 3)
        extended_info.addWidget(row_label, 1, 4)
        extended_info.addWidget(self.row_line, 1, 5)
        extended_info.addWidget(col_label, 1, 6)
        extended_info.addWidget(self.col_line, 1, 7)

        hkl_info = QHBoxLayout()
        peak_info = QGridLayout()

        left_label = QLabel("(", self)
        left_comma_label = QLabel(",", self)
        right_comma_label = QLabel(",", self)
        right_label = QLabel(")", self)

        index_label = QLabel("Indexed:", self)
        total_label = QLabel("Total:", self)

        self.index_line = QLineEdit("0")
        self.total_line = QLineEdit("0")

        self.index_line.setEnabled(False)
        self.total_line.setEnabled(False)

        int_h_label = QLabel("h", self)
        int_k_label = QLabel("k", self)
        int_l_label = QLabel("l", self)

        int_m_label = QLabel("m", self)
        int_n_label = QLabel("n", self)
        int_p_label = QLabel("p", self)

        self.h_line = QLineEdit()
        self.k_line = QLineEdit()
        self.l_line = QLineEdit()

        notation = QDoubleValidator.StandardNotation

        validator = QDoubleValidator(-100, 100, 5, notation=notation)

        self.h_line.setValidator(validator)
        self.k_line.setValidator(validator)
        self.l_line.setValidator(validator)

        validator = QIntValidator(-1000000000, 1000000000, self)

        self.int_h_line = QLineEdit()
        self.int_k_line = QLineEdit()
        self.int_l_line = QLineEdit()

        self.int_h_line.setValidator(validator)
        self.int_k_line.setValidator(validator)
        self.int_l_line.setValidator(validator)

        self.int_m_line = QLineEdit()
        self.int_n_line = QLineEdit()
        self.int_p_line = QLineEdit()

        self.int_m_line.setValidator(validator)
        self.int_n_line.setValidator(validator)
        self.int_p_line.setValidator(validator)

        hkl_info.addWidget(left_label)
        hkl_info.addWidget(self.h_line)
        hkl_info.addWidget(left_comma_label)
        hkl_info.addWidget(self.k_line)
        hkl_info.addWidget(right_comma_label)
        hkl_info.addWidget(self.l_line)
        hkl_info.addWidget(right_label)
        hkl_info.addStretch(1)
        hkl_info.addWidget(index_label)
        hkl_info.addWidget(self.index_line)
        hkl_info.addWidget(total_label)
        hkl_info.addWidget(self.total_line)

        peak_info.addWidget(int_h_label, 0, 0, Qt.AlignCenter)
        peak_info.addWidget(int_k_label, 0, 1, Qt.AlignCenter)
        peak_info.addWidget(int_l_label, 0, 2, Qt.AlignCenter)
        peak_info.addWidget(int_m_label, 0, 3, Qt.AlignCenter)
        peak_info.addWidget(int_n_label, 0, 4, Qt.AlignCenter)
        peak_info.addWidget(int_p_label, 0, 5, Qt.AlignCenter)

        peak_info.addWidget(self.int_h_line, 1, 0)
        peak_info.addWidget(self.int_k_line, 1, 1)
        peak_info.addWidget(self.int_l_line, 1, 2)
        peak_info.addWidget(self.int_m_line, 1, 3)
        peak_info.addWidget(self.int_n_line, 1, 4)
        peak_info.addWidget(self.int_p_line, 1, 5)

        peaks_layout.addLayout(calculator_layout)
        peaks_layout.addWidget(self.peaks_table)
        peaks_layout.addLayout(hkl_info)
        peaks_layout.addLayout(peak_info)
        peaks_layout.addLayout(extended_info)

        peaks_table_tab.setLayout(peaks_layout)

    def verify_tab(self):
        inspect_verify_tab = QTabWidget()
        self.tab_widget.addTab(inspect_verify_tab, "Views")

        inspect_tab = self.__init_inspect_tab()
        verify_tab = self.__init_verify_tab()

        inspect_verify_tab.addTab(inspect_tab, "Slice View")
        inspect_verify_tab.addTab(verify_tab, "Detector View")

    def __init_inspect_tab(self):
        convert_to_hkl_tab = QWidget()
        convert_to_hkl_tab_layout = QVBoxLayout()

        convert_to_hkl_params_layout = QGridLayout()

        notation = QDoubleValidator.StandardNotation

        validator = QDoubleValidator(-10, 10, 5, notation=notation)

        self.U1_line = QLineEdit("1")
        self.U2_line = QLineEdit("0")
        self.U3_line = QLineEdit("0")

        self.V1_line = QLineEdit("0")
        self.V2_line = QLineEdit("1")
        self.V3_line = QLineEdit("0")

        self.W1_line = QLineEdit("0")
        self.W2_line = QLineEdit("0")
        self.W3_line = QLineEdit("1")

        self.U1_line.setValidator(validator)
        self.U2_line.setValidator(validator)
        self.U3_line.setValidator(validator)

        self.V1_line.setValidator(validator)
        self.V2_line.setValidator(validator)
        self.V3_line.setValidator(validator)

        self.W1_line.setValidator(validator)
        self.W2_line.setValidator(validator)
        self.W3_line.setValidator(validator)

        ax1_label = QLabel("1:")
        ax2_label = QLabel("2:")
        ax3_label = QLabel("3:")

        h_label = QLabel("h")
        k_label = QLabel("k")
        l_label = QLabel("l")

        convert_to_hkl_params_layout.addWidget(h_label, 0, 1, Qt.AlignCenter)
        convert_to_hkl_params_layout.addWidget(k_label, 0, 2, Qt.AlignCenter)
        convert_to_hkl_params_layout.addWidget(l_label, 0, 3, Qt.AlignCenter)
        convert_to_hkl_params_layout.addWidget(ax1_label, 1, 0, Qt.AlignCenter)
        convert_to_hkl_params_layout.addWidget(ax2_label, 2, 0, Qt.AlignCenter)
        convert_to_hkl_params_layout.addWidget(ax3_label, 3, 0, Qt.AlignCenter)

        convert_to_hkl_params_layout.addWidget(self.U1_line, 1, 1)
        convert_to_hkl_params_layout.addWidget(self.V1_line, 2, 1)
        convert_to_hkl_params_layout.addWidget(self.W1_line, 3, 1)

        convert_to_hkl_params_layout.addWidget(self.U2_line, 1, 2)
        convert_to_hkl_params_layout.addWidget(self.V2_line, 2, 2)
        convert_to_hkl_params_layout.addWidget(self.W2_line, 3, 2)

        convert_to_hkl_params_layout.addWidget(self.U3_line, 1, 3)
        convert_to_hkl_params_layout.addWidget(self.V3_line, 2, 3)
        convert_to_hkl_params_layout.addWidget(self.W3_line, 3, 3)

        self.convert_to_hkl_button = QPushButton("Convert", self)

        self.clim_combo = QComboBox(self)
        self.clim_combo.addItem("Min/Max")
        self.clim_combo.addItem("μ±3×σ")
        self.clim_combo.addItem("Q₃/Q₁±1.5×IQR")
        self.clim_combo.setCurrentIndex(1)

        self.cbar_combo = QComboBox(self)
        self.cbar_combo.addItem("Sequential")
        self.cbar_combo.addItem("Rainbow")
        self.cbar_combo.addItem("Binary")
        self.cbar_combo.addItem("Diverging")
        self.cbar_combo.addItem("Modified")
        self.cbar_combo.setCurrentIndex(2)

        self.slice_combo = QComboBox(self)
        self.slice_combo.addItem("Axis 1/2")
        self.slice_combo.addItem("Axis 1/3")
        self.slice_combo.addItem("Axis 2/3")
        self.slice_combo.setCurrentIndex(0)

        bar_layout = QHBoxLayout()

        self.min_slider = QSlider(Qt.Vertical)
        self.max_slider = QSlider(Qt.Vertical)

        self.min_slider.setRange(0, 100)
        self.max_slider.setRange(0, 100)

        self.min_slider.setValue(0)
        self.max_slider.setValue(100)

        self.min_slider.setTracking(False)
        self.max_slider.setTracking(False)

        bar_layout.addWidget(self.min_slider)
        bar_layout.addWidget(self.max_slider)

        slice_label = QLabel("Slice:", self)

        self.slice_line = QLineEdit("0.0")
        self.slice_line.setValidator(validator)

        validator = QDoubleValidator(0.0001, 100, 5, notation=notation)

        slice_thickness_label = QLabel("Thickness:", self)

        self.slice_thickness_line = QLineEdit("0.1")
        self.slice_thickness_line.setValidator(validator)

        validator = QDoubleValidator(0.005, 0.5, 5, notation=notation)

        slice_width_label = QLabel("Width:", self)

        self.slice_width_line = QLineEdit("0.05")
        self.slice_width_line.setValidator(validator)

        self.slice_scale_combo = QComboBox(self)
        self.slice_scale_combo.addItem("Linear")
        self.slice_scale_combo.addItem("Log")

        convert_to_hkl_action_layout = QHBoxLayout()
        convert_to_hkl_action_layout.addWidget(self.convert_to_hkl_button)
        convert_to_hkl_action_layout.addWidget(self.slice_combo)
        convert_to_hkl_action_layout.addWidget(slice_label)
        convert_to_hkl_action_layout.addWidget(self.slice_line)
        convert_to_hkl_action_layout.addWidget(slice_thickness_label)
        convert_to_hkl_action_layout.addWidget(self.slice_thickness_line)
        convert_to_hkl_action_layout.addWidget(slice_width_label)
        convert_to_hkl_action_layout.addWidget(self.slice_width_line)

        convert_to_hkl_view_layout = QHBoxLayout()
        convert_to_hkl_view_layout.addWidget(self.cbar_combo)
        convert_to_hkl_view_layout.addWidget(self.clim_combo)
        convert_to_hkl_view_layout.addWidget(self.slice_scale_combo)

        convert_to_hkl_tab_layout.addLayout(convert_to_hkl_params_layout)
        convert_to_hkl_tab_layout.addStretch(1)
        convert_to_hkl_tab_layout.addLayout(convert_to_hkl_action_layout)

        slice_layout = QVBoxLayout()
        slider_layout = QHBoxLayout()

        slice_layout.addWidget(NavigationToolbar2QT(self.canvas_slice, self))
        slice_layout.addWidget(self.canvas_slice)

        slider_layout.addLayout(slice_layout)
        slider_layout.addLayout(bar_layout)

        convert_to_hkl_tab_layout.addLayout(slider_layout)
        convert_to_hkl_tab_layout.addLayout(convert_to_hkl_view_layout)

        convert_to_hkl_tab.setLayout(convert_to_hkl_tab_layout)

        return convert_to_hkl_tab

    def __init_verify_tab(self):
        instrument_tab = QWidget()
        instrument_tab_layout = QVBoxLayout()

        notation = QDoubleValidator.StandardNotation

        self.data_combo = QComboBox(self)

        d_min_label = QLabel("d(min):", self)
        d_max_label = QLabel("d(max):", self)

        validator = QDoubleValidator(0, float("inf"), 5, notation=notation)

        self.d_min_line = QLineEdit("0")
        self.d_min_line.setValidator(validator)

        self.d_max_line = QLineEdit("inf")
        self.d_max_line.setValidator(validator)

        self.check_h_line = QLineEdit()
        self.check_k_line = QLineEdit()
        self.check_l_line = QLineEdit()

        self.check_hkl_button = QPushButton("Check hkl", self)

        notation = QDoubleValidator.StandardNotation

        validator = QDoubleValidator(-100, 100, 5, notation=notation)

        self.check_h_line.setValidator(validator)
        self.check_k_line.setValidator(validator)
        self.check_l_line.setValidator(validator)

        data_layout = QHBoxLayout()
        data_layout.addWidget(self.data_combo)
        data_layout.addWidget(self.check_hkl_button)
        data_layout.addWidget(self.check_h_line)
        data_layout.addWidget(self.check_k_line)
        data_layout.addWidget(self.check_l_line)
        data_layout.addStretch(1)
        data_layout.addWidget(d_min_label)
        data_layout.addWidget(self.d_min_line)
        data_layout.addWidget(d_max_label)
        data_layout.addWidget(self.d_max_line)

        vertical_label = QLabel("Vertical Angle:", self)
        horizontal_label = QLabel("Horizontal Angle:", self)

        vertical_roi_label = QLabel("ROI:", self)
        horizontal_roi_label = QLabel("ROI:", self)

        validator = QDoubleValidator(-180, 180, 5, notation=notation)

        self.vertical_line = QLineEdit("0")
        self.vertical_line.setValidator(validator)

        self.horizontal_line = QLineEdit("0")
        self.horizontal_line.setValidator(validator)

        validator = QDoubleValidator(0, 180, 5, notation=notation)

        self.vertical_roi_line = QLineEdit("2")
        self.vertical_roi_line.setValidator(validator)

        self.horizontal_roi_line = QLineEdit("2")
        self.horizontal_roi_line.setValidator(validator)

        angle_layout = QHBoxLayout()
        angle_layout.addWidget(horizontal_label)
        angle_layout.addWidget(self.horizontal_line)
        angle_layout.addWidget(horizontal_roi_label)
        angle_layout.addWidget(self.horizontal_roi_line)
        angle_layout.addWidget(vertical_label)
        angle_layout.addWidget(self.vertical_line)
        angle_layout.addWidget(vertical_roi_label)
        angle_layout.addWidget(self.vertical_roi_line)

        self.add_peak_button = QPushButton("Add Peak", self)

        self.diffraction_label = QLabel("Axis:", self)

        validator = QDoubleValidator(-float("inf"), float("inf"), 5, notation=notation)

        self.diffraction_line = QLineEdit("0")
        self.diffraction_line.setValidator(validator)

        peak_layout = QHBoxLayout()
        peak_layout.addWidget(self.diffraction_label)
        peak_layout.addWidget(self.diffraction_line)
        peak_layout.addStretch(1)
        peak_layout.addWidget(self.add_peak_button)

        view_layout = QVBoxLayout()

        view_layout.addLayout(data_layout)
        view_layout.addWidget(NavigationToolbar2QT(self.canvas_inst, self))
        view_layout.addWidget(self.canvas_inst)

        view_layout.addLayout(angle_layout)
        view_layout.addWidget(NavigationToolbar2QT(self.canvas_scan, self))
        view_layout.addWidget(self.canvas_scan)

        view_layout.addLayout(peak_layout)

        instrument_tab_layout.addLayout(view_layout)

        instrument_tab.setLayout(instrument_tab_layout)

        return instrument_tab

    def modulation_tab(self):
        mod_tab = QWidget()
        self.tab_widget.addTab(mod_tab, "Modulation")

        modulation_layout = QVBoxLayout()

        self.cluster_button = QPushButton("Cluster", self)

        self.param_eps_line = QLineEdit("0.025")
        self.param_min_line = QLineEdit("15")

        notation = QDoubleValidator.StandardNotation

        validator = QDoubleValidator(0.0001, 10, 5, notation=notation)

        self.param_eps_line.setValidator(validator)

        validator = QIntValidator(1, 1000)

        self.param_min_line.setValidator(validator)

        self.cluster_table = QTableWidget()

        self.cluster_table.setRowCount(0)
        self.cluster_table.setColumnCount(3)

        self.cluster_table.horizontalHeader().setStretchLastSection(True)
        self.cluster_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cluster_table.setHorizontalHeaderLabels(["h", "k", "l"])

        generate_layout = QHBoxLayout()
        generate_layout.addWidget(self.cluster_button)
        generate_layout.addStretch(1)

        cluster_layout = QVBoxLayout()
        params_layout = QHBoxLayout()

        dist_label = QLabel("Maximum distance:", self)
        samp_label = QLabel("Minimum samples:", self)

        params_layout.addWidget(dist_label)
        params_layout.addWidget(self.param_eps_line)
        params_layout.addWidget(samp_label)
        params_layout.addWidget(self.param_min_line)

        cluster_layout.addLayout(params_layout)
        cluster_layout.addWidget(self.cluster_table)

        plot_layout = QVBoxLayout()

        plot_layout.addWidget(NavigationToolbar2QT(self.canvas_clust, self))
        plot_layout.addWidget(self.canvas_clust)

        fig = self.canvas_clust.figure

        self.ax_clust = fig.subplots(3, 1, sharex=True, sharey=True)

        for i in range(3):
            self.ax_clust[i].set_xlim(-1, 1)
            self.ax_clust[i].set_ylim(1, 100)
            self.ax_clust[i].minorticks_on()
            self.ax_clust[i].set_yscale("log")

        self.ax_clust[0].set_xlabel("$[h00]$")
        self.ax_clust[1].set_xlabel("$[0k0]$")
        self.ax_clust[2].set_xlabel("$[00l]$")

        modulation_layout.addLayout(generate_layout)
        modulation_layout.addLayout(cluster_layout)
        modulation_layout.addLayout(plot_layout)

        mod_tab.setLayout(modulation_layout)

    def connect_bindings(self) -> None:
        self.instrument_callback = self.view_model.instrument_bind.connect(
            "ub_instrument", self.set_instrument
        )
        self.modulation_callback = self.view_model.modulation_clusters_bind.connect(
            "ub_modulation_cluster", self.update_cluster_table
        )
        self.parameters_callback = self.view_model.parameters_bind.connect(
            "ub_parameters", self.set_parameters
        )
        self.peaks_callback = self.view_model.peaks_bind.connect(
            "ub_peaks", self.set_peaks
        )
        self.peaks_controls_callback = self.view_model.peaks_controls_bind.connect(
            "ub_peaks_controls", lambda *args: None
        )
        self.q_conversion_callback = self.view_model.q_conversion_bind.connect(
            "ub_q_conversion", self.set_q_conversion
        )
        self.ub_controls_callback = self.view_model.ub_controls_bind.connect(
            "ub_controls", self.set_ub_controls
        )
        self.slice_callback = self.view_model.slice_bind.connect(
            "ub_slice", lambda *args: None
        )

        self.view_model.add_Q_viz_bind.connect("ub_add_q_viz", self.plotter.add_Q_viz)
        self.view_model.highlight_peak_bind.connect(
            "ub_highlight_peak", self.highlight_peak
        )
        self.view_model.highlight_peaks_bind.connect(
            "ub_highlight_peaks", self.highlight_peaks
        )
        self.view_model.update_cluster_peaks_bind.connect(
            "ub_update_cluster_peaks", self.plotter.add_cluster_peaks
        )
        self.view_model.update_instrument_bind.connect(
            "ub_update_instrument", self.update_instrument_view
        )
        self.view_model.update_slice_bind.connect("ub_update_slice", self.update_slice)
        self.view_model.update_slice_colorbar_bind.connect(
            "ub_update_slice_colorbar", self.plotter.update_slice_colorbar
        )

    def connect_widgets(self) -> None:
        self._connect_q_conversion_widgets()

        self._connect_find_peaks_widgets()
        self._connect_index_peaks_widgets()
        self._connect_predict_peaks_widgets()
        self._connect_integrate_peaks_widgets()
        self._connect_filter_peaks_widgets()

        self._connect_calculate_ub_widgets()
        self._connect_transform_ub_widgets()
        self._connect_refine_ub_widgets()

        self._connect_modulation_widgets()

        self._connect_peaks_table_widgets()

        self._connect_slice_view_widgets()
        self._connect_detector_view_widgets()

        self._connect_modulation_clusters_widgets()

    def _connect_q_conversion_widgets(self) -> None:
        self.cal_line.editingFinished.connect(
            lambda: process_change(
                "ub_q_conversion.detector_calibration",
                self.cal_line.text(),
                self.cal_line,
                self.q_conversion_callback,
            )
        )
        self.convert_min_d_line.editingFinished.connect(
            lambda: process_change(
                "ub_q_conversion.d_min",
                self.convert_min_d_line.text(),
                self.convert_min_d_line,
                self.q_conversion_callback,
            )
        )
        self.convert_to_q_button.clicked.connect(self.view_model.convert_Q)
        self.exp_line.editingFinished.connect(
            lambda: process_change(
                "ub_q_conversion.experiment_number",
                self.exp_line.text(),
                self.exp_line,
                self.q_conversion_callback,
            )
        )
        self.filter_time_line.editingFinished.connect(
            lambda: process_change(
                "ub_q_conversion.time_stop",
                self.filter_time_line.text(),
                self.filter_time_line,
                self.q_conversion_callback,
            )
        )
        self.instrument_combo.activated.connect(
            lambda: process_change(
                "ub_q_conversion.instrument",
                self.instrument_combo.currentText(),
                self.instrument_combo,
                self.q_conversion_callback,
            )
        )
        self.ipts_line.editingFinished.connect(
            lambda: process_change(
                "ub_q_conversion.ipts_number",
                self.ipts_line.text(),
                self.ipts_line,
                self.q_conversion_callback,
            )
        )
        self.lorentz_box.clicked.connect(
            lambda: process_change(
                "ub_q_conversion.lorentz_correction",
                self.lorentz_box.isChecked(),
                self.lorentz_box,
                self.q_conversion_callback,
            )
        )
        self.runs_line.editingFinished.connect(
            lambda: process_change(
                "ub_q_conversion.runs",
                self.runs_line.text(),
                self.runs_line,
                self.q_conversion_callback,
            )
        )
        self.tube_line.editingFinished.connect(
            lambda: process_change(
                "ub_q_conversion.tube_calibration",
                self.tube_line.text(),
                self.tube_line,
                self.q_conversion_callback,
            )
        )
        self.wl_max_line.editingFinished.connect(
            lambda: process_change(
                "ub_q_conversion.wl_max",
                self.wl_max_line.text(),
                self.wl_max_line,
                self.q_conversion_callback,
            )
        )
        self.wl_min_line.editingFinished.connect(
            lambda: process_change(
                "ub_q_conversion.wl_min",
                self.wl_min_line.text(),
                self.wl_min_line,
                self.q_conversion_callback,
            )
        )

    def _connect_find_peaks_widgets(self) -> None:
        self.aluminum_box.clicked.connect(
            lambda: process_change(
                "ub_peaks_controls.find.avoid_aluminum",
                self.aluminum_box.isChecked(),
                self.aluminum_box,
                self.peaks_controls_callback,
            )
        )
        self.find_button.clicked.connect(self.view_model.find_peaks)
        self.find_edge_line.editingFinished.connect(
            lambda: process_change(
                "ub_peaks_controls.find.edge_pixels",
                self.find_edge_line.text(),
                self.find_edge_line,
                self.peaks_controls_callback,
            )
        )
        self.max_peaks_line.editingFinished.connect(
            lambda: process_change(
                "ub_peaks_controls.find.max_peaks",
                self.max_peaks_line.text(),
                self.max_peaks_line,
                self.peaks_controls_callback,
            )
        )
        self.max_spacing_line.editingFinished.connect(
            lambda: process_change(
                "ub_peaks_controls.find.max_spacing",
                self.max_spacing_line.text(),
                self.max_spacing_line,
                self.peaks_controls_callback,
            )
        )
        self.density_threshold_line.editingFinished.connect(
            lambda: process_change(
                "ub_peaks_controls.find.min_density",
                self.density_threshold_line.text(),
                self.density_threshold_line,
                self.peaks_controls_callback,
            )
        )
        self.min_distance_line.editingFinished.connect(
            lambda: process_change(
                "ub_peaks_controls.find.min_distance",
                self.min_distance_line.text(),
                self.min_distance_line,
                self.peaks_controls_callback,
            )
        )

    def _connect_index_peaks_widgets(self) -> None:
        self.index_tolerance_line.editingFinished.connect(
            lambda: process_change(
                "ub_peaks_controls.index.tolerance",
                self.index_tolerance_line.text(),
                self.index_tolerance_line,
                self.peaks_controls_callback,
            )
        )
        self.index_sat_tolerance_line.editingFinished.connect(
            lambda: process_change(
                "ub_peaks_controls.index.satellite_tolerance",
                self.index_sat_tolerance_line.text(),
                self.index_sat_tolerance_line,
                self.peaks_controls_callback,
            )
        )
        self.index_sat_box.clicked.connect(
            lambda: process_change(
                "ub_peaks_controls.index.satellite",
                self.index_sat_box.isChecked(),
                self.index_sat_box,
                self.peaks_controls_callback,
            )
        )
        self.round_box.clicked.connect(
            lambda: process_change(
                "ub_peaks_controls.index.round_hkl",
                self.round_box.isChecked(),
                self.round_box,
                self.peaks_controls_callback,
            )
        )
        self.index_button.clicked.connect(self.view_model.index_peaks)

    def _connect_predict_peaks_widgets(self) -> None:
        self.centering_combo.activated.connect(
            lambda: process_change(
                "ub_peaks_controls.predict.centering",
                self.centering_combo.currentText(),
                self.centering_combo,
                self.peaks_controls_callback,
            )
        )
        self.min_d_line.editingFinished.connect(
            lambda: process_change(
                "ub_peaks_controls.predict.min_d_spacing",
                self.min_d_line.text(),
                self.min_d_line,
                self.peaks_controls_callback,
            )
        )
        self.min_sat_d_line.editingFinished.connect(
            lambda: process_change(
                "ub_peaks_controls.predict.satellite_min_d_spacing",
                self.min_sat_d_line.text(),
                self.min_sat_d_line,
                self.peaks_controls_callback,
            )
        )
        self.predict_edge_line.editingFinished.connect(
            lambda: process_change(
                "ub_peaks_controls.predict.edge_pixels",
                self.predict_edge_line.text(),
                self.predict_edge_line,
                self.peaks_controls_callback,
            )
        )
        self.predict_sat_box.clicked.connect(
            lambda: process_change(
                "ub_peaks_controls.predict.satellite",
                self.predict_sat_box.isChecked(),
                self.predict_sat_box,
                self.peaks_controls_callback,
            )
        )
        self.predict_button.clicked.connect(self.view_model.predict_peaks)

    def _connect_integrate_peaks_widgets(self) -> None:
        self.radius_line.editingFinished.connect(
            lambda: process_change(
                "ub_peaks_controls.integrate.radius",
                self.radius_line.text(),
                self.radius_line,
                self.peaks_controls_callback,
            )
        )
        self.inner_line.editingFinished.connect(
            lambda: process_change(
                "ub_peaks_controls.integrate.inner_factor",
                self.inner_line.text(),
                self.inner_line,
                self.peaks_controls_callback,
            )
        )
        self.outer_line.editingFinished.connect(
            lambda: process_change(
                "ub_peaks_controls.filter.outer_factor",
                self.outer_line.text(),
                self.outer_line,
                self.peaks_controls_callback,
            )
        )
        self.centroid_box.clicked.connect(
            lambda: process_change(
                "ub_peaks_controls.filter.centroid",
                self.centroid_box.isChecked(),
                self.centroid_box,
                self.peaks_controls_callback,
            )
        )
        self.adaptive_box.clicked.connect(
            lambda: process_change(
                "ub_peaks_controls.filter.adaptive_envelope",
                self.adaptive_box.isChecked(),
                self.adaptive_box,
                self.peaks_controls_callback,
            )
        )
        self.integrate_button.clicked.connect(self.view_model.integrate_peaks)

    def _connect_filter_peaks_widgets(self) -> None:
        self.filter_combo.activated.connect(
            lambda: process_change(
                "ub_peaks_controls.filter.filter",
                self.filter_combo.currentText(),
                self.filter_combo,
                self.peaks_controls_callback,
            )
        )
        self.comparison_combo.activated.connect(
            lambda: process_change(
                "ub_peaks_controls.filter.comparison",
                self.comparison_combo.currentText(),
                self.comparison_combo,
                self.peaks_controls_callback,
            )
        )
        self.filter_line.editingFinished.connect(
            lambda: process_change(
                "ub_peaks_controls.filter.value",
                self.filter_line.text(),
                self.filter_line,
                self.peaks_controls_callback,
            )
        )
        self.filter_button.clicked.connect(self.view_model.filter_peaks)

    def _connect_calculate_ub_widgets(self) -> None:
        self.calculate_tolerance_line.editingFinished.connect(
            lambda: process_change(
                "ub_controls.calculate.tolerance",
                self.calculate_tolerance_line.text(),
                self.calculate_tolerance_line,
                self.ub_controls_callback,
            )
        )
        self.max_scalar_error_line.editingFinished.connect(
            lambda: process_change(
                "ub_controls.calculate.max_scalar_error",
                self.max_scalar_error_line.text(),
                self.max_scalar_error_line,
                self.ub_controls_callback,
            )
        )
        self.min_const_line.editingFinished.connect(
            lambda: process_change(
                "ub_controls.calculate.min_const",
                self.min_const_line.text(),
                self.min_const_line,
                self.ub_controls_callback,
            )
        )
        self.max_const_line.editingFinished.connect(
            lambda: process_change(
                "ub_controls.calculate.max_const",
                self.max_const_line.text(),
                self.max_const_line,
                self.ub_controls_callback,
            )
        )
        self.cell_table.itemSelectionChanged.connect(self.highlight_cell)
        self.conventional_button.clicked.connect(self.view_model.find_conventional)
        self.niggli_button.clicked.connect(self.view_model.find_niggli)
        self.select_button.clicked.connect(self.view_model.select_cell)

    def _connect_transform_ub_widgets(self) -> None:
        self.transform_tolerance_line.editingFinished.connect(
            lambda: process_change(
                "ub_controls.transform.tolerance",
                self.transform_tolerance_line.text(),
                self.transform_tolerance_line,
                self.ub_controls_callback,
            )
        )
        self.lattice_combo.activated.connect(
            lambda: process_change(
                "ub_controls.transform.lattice",
                self.lattice_combo.currentText(),
                self.lattice_combo,
                self.ub_controls_callback,
            )
        )
        self.symmetry_combo.activated.connect(
            lambda: process_change(
                "ub_controls.transform.symmetry",
                self.symmetry_combo.text(),
                self.symmetry_combo,
                self.ub_controls_callback,
            )
        )
        self.transform_button.clicked.connect(self.view_model.transform_UB)

    def _connect_refine_ub_widgets(self) -> None:
        self.refine_tolerance_line.editingFinished.connect(
            lambda: process_change(
                "ub_controls.refine.tolerance",
                self.refine_tolerance_line.text(),
                self.refine_tolerance_line,
                self.ub_controls_callback,
            )
        )
        self.refine_button.clicked.connect(self.view_model.refine_UB)

    def _connect_modulation_widgets(self) -> None:
        self.dh1_line.editingFinished.connect(
            lambda: process_change(
                "ub_parameters.modulation.dh1",
                self.dh1_line.text(),
                self.dh1_line,
                self.parameters_callback,
            )
        )
        self.dk1_line.editingFinished.connect(
            lambda: process_change(
                "ub_parameters.modulation.dk1",
                self.dk1_line.text(),
                self.dk1_line,
                self.parameters_callback,
            )
        )
        self.dl1_line.editingFinished.connect(
            lambda: process_change(
                "ub_parameters.modulation.dl1",
                self.dl1_line.text(),
                self.dl1_line,
                self.parameters_callback,
            )
        )
        self.dh2_line.editingFinished.connect(
            lambda: process_change(
                "ub_parameters.modulation.dh2",
                self.dh2_line.text(),
                self.dh2_line,
                self.parameters_callback,
            )
        )
        self.dk2_line.editingFinished.connect(
            lambda: process_change(
                "ub_parameters.modulation.dk2",
                self.dk2_line.text(),
                self.dk2_line,
                self.parameters_callback,
            )
        )
        self.dl2_line.editingFinished.connect(
            lambda: process_change(
                "ub_parameters.modulation.dl2",
                self.dl2_line.text(),
                self.dl2_line,
                self.parameters_callback,
            )
        )
        self.dh3_line.editingFinished.connect(
            lambda: process_change(
                "ub_parameters.modulation.dh3",
                self.dh3_line.text(),
                self.dh3_line,
                self.parameters_callback,
            )
        )
        self.dk3_line.editingFinished.connect(
            lambda: process_change(
                "ub_parameters.modulation.dk3",
                self.dk3_line.text(),
                self.dk3_line,
                self.parameters_callback,
            )
        )
        self.dl3_line.editingFinished.connect(
            lambda: process_change(
                "ub_parameters.modulation.dl3",
                self.dl3_line.text(),
                self.dl3_line,
                self.parameters_callback,
            )
        )
        self.max_order_line.editingFinished.connect(
            lambda: process_change(
                "ub_parameters.modulation.max_order",
                self.max_order_line.text(),
                self.max_order_line,
                self.parameters_callback,
            )
        )
        self.cross_box.clicked.connect(
            lambda: process_change(
                "ub_parameters.modulation.cross_terms",
                self.cross_box.isChecked(),
                self.cross_box,
                self.parameters_callback,
            )
        )

    def _connect_peaks_table_widgets(self) -> None:
        self.h1_line.editingFinished.connect(
            lambda: process_change(
                "ub_peaks.h1", self.h1_line.text(), self.h1_line, self.peaks_callback
            )
        )
        self.k1_line.editingFinished.connect(
            lambda: process_change(
                "ub_peaks.k1", self.k1_line.text(), self.k1_line, self.peaks_callback
            )
        )
        self.l1_line.editingFinished.connect(
            lambda: process_change(
                "ub_peaks.l1", self.l1_line.text(), self.l1_line, self.peaks_callback
            )
        )
        self.h2_line.editingFinished.connect(
            lambda: process_change(
                "ub_peaks.h2", self.h2_line.text(), self.h2_line, self.peaks_callback
            )
        )
        self.k2_line.editingFinished.connect(
            lambda: process_change(
                "ub_peaks.k2", self.k2_line.text(), self.k2_line, self.peaks_callback
            )
        )
        self.l2_line.editingFinished.connect(
            lambda: process_change(
                "ub_peaks.l2", self.l2_line.text(), self.l2_line, self.peaks_callback
            )
        )
        self.peaks_table.itemSelectionChanged.connect(
            lambda: self.view_model.highlight_peak(self.peaks_table.currentRow())
        )
        self.calculate.clicked.connect(self.view_model.calculate_peaks)

    def _connect_slice_view_widgets(self) -> None:
        self.U1_line.editingFinished.connect(
            lambda: process_change(
                "ub_slice.U1", self.U1_line.text(), self.U1_line, self.slice_callback
            )
        )
        self.V1_line.editingFinished.connect(
            lambda: process_change(
                "ub_slice.V1", self.V1_line.text(), self.V1_line, self.slice_callback
            )
        )
        self.W1_line.editingFinished.connect(
            lambda: process_change(
                "ub_slice.W1", self.W1_line.text(), self.W1_line, self.slice_callback
            )
        )
        self.U2_line.editingFinished.connect(
            lambda: process_change(
                "ub_slice.U2", self.U2_line.text(), self.U2_line, self.slice_callback
            )
        )
        self.V2_line.editingFinished.connect(
            lambda: process_change(
                "ub_slice.V2", self.V2_line.text(), self.V2_line, self.slice_callback
            )
        )
        self.W2_line.editingFinished.connect(
            lambda: process_change(
                "ub_slice.W2", self.W2_line.text(), self.W2_line, self.slice_callback
            )
        )
        self.U3_line.editingFinished.connect(
            lambda: process_change(
                "ub_slice.U3", self.U3_line.text(), self.U3_line, self.slice_callback
            )
        )
        self.V3_line.editingFinished.connect(
            lambda: process_change(
                "ub_slice.V3", self.V3_line.text(), self.V3_line, self.slice_callback
            )
        )
        self.W3_line.editingFinished.connect(
            lambda: process_change(
                "ub_slice.W3", self.W3_line.text(), self.W3_line, self.slice_callback
            )
        )
        self.slice_combo.activated.connect(
            lambda: process_change(
                "ub_slice.plane",
                self.slice_combo.currentText(),
                self.slice_combo,
                self.slice_callback,
            )
        )
        self.slice_line.editingFinished.connect(
            lambda: process_change(
                "ub_slice.value",
                self.slice_line.text(),
                self.slice_line,
                self.slice_callback,
            )
        )
        self.slice_thickness_line.editingFinished.connect(
            lambda: process_change(
                "ub_slice.thickness",
                self.slice_thickness_line.text(),
                self.slice_thickness_line,
                self.slice_callback,
            )
        )
        self.slice_width_line.editingFinished.connect(
            lambda: process_change(
                "ub_slice.width",
                self.slice_width_line.text(),
                self.slice_width_line,
                self.slice_callback,
            )
        )
        self.min_slider.valueChanged.connect(
            lambda: process_change(
                "ub_slice.vmin_slider",
                self.min_slider.value(),
                self.min_slider,
                self.slice_callback,
            )
        )
        self.max_slider.valueChanged.connect(
            lambda: process_change(
                "ub_slice.vmax_slider",
                self.max_slider.value(),
                self.max_slider,
                self.slice_callback,
            )
        )
        self.cbar_combo.activated.connect(
            lambda: process_change(
                "ub_slice.cbar",
                self.cbar_combo.currentText(),
                self.cbar_combo,
                self.slice_callback,
            )
        )
        self.clim_combo.activated.connect(
            lambda: process_change(
                "ub_slice.clip_type",
                self.clim_combo.currentText(),
                self.clim_combo,
                self.slice_callback,
            )
        )
        self.slice_scale_combo.activated.connect(
            lambda: process_change(
                "ub_slice.scale",
                self.slice_scale_combo.currentText(),
                self.slice_scale_combo,
                self.slice_callback,
            )
        )
        self.convert_to_hkl_button.clicked.connect(self.view_model.convert_to_hkl)

    def _connect_detector_view_widgets(self) -> None:
        self.data_combo.activated.connect(
            lambda: process_change(
                "ub_instrument.data",
                self.data_combo.currentText(),
                self.data_combo,
                self.instrument_callback,
            )
        )
        self.check_h_line.editingFinished.connect(
            lambda: process_change(
                "ub_instrument.check_h",
                self.check_h_line.text(),
                self.check_h_line,
                self.instrument_callback,
            )
        )
        self.check_k_line.editingFinished.connect(
            lambda: process_change(
                "ub_instrument.check_k",
                self.check_k_line.text(),
                self.check_k_line,
                self.instrument_callback,
            )
        )
        self.check_l_line.editingFinished.connect(
            lambda: process_change(
                "ub_instrument.check_l",
                self.check_l_line.text(),
                self.check_l_line,
                self.instrument_callback,
            )
        )
        self.d_min_line.editingFinished.connect(
            lambda: process_change(
                "ub_instrument.d_min",
                self.d_min_line.text(),
                self.d_min_line,
                self.instrument_callback,
            )
        )
        self.d_max_line.editingFinished.connect(
            lambda: process_change(
                "ub_instrument.d_max",
                self.d_max_line.text(),
                self.d_max_line,
                self.instrument_callback,
            )
        )
        self.horizontal_line.editingFinished.connect(
            lambda: process_change(
                "ub_instrument.horizontal_angle",
                self.horizontal_line.text(),
                self.horizontal_line,
                self.instrument_callback,
            )
        )
        self.horizontal_roi_line.editingFinished.connect(
            lambda: process_change(
                "ub_instrument.horizontal_roi",
                self.horizontal_roi_line.text(),
                self.horizontal_roi_line,
                self.instrument_callback,
            )
        )
        self.vertical_line.editingFinished.connect(
            lambda: process_change(
                "ub_instrument.vertical_angle",
                self.vertical_line.text(),
                self.vertical_line,
                self.instrument_callback,
            )
        )
        self.vertical_roi_line.editingFinished.connect(
            lambda: process_change(
                "ub_instrument.vertical_roi",
                self.vertical_roi_line.text(),
                self.vertical_roi_line,
                self.instrument_callback,
            )
        )
        self.diffraction_line.editingFinished.connect(
            lambda: process_change(
                "ub_instrument.diffraction",
                self.diffraction_line.text(),
                self.diffraction_line,
                self.instrument_callback,
            )
        )
        self.check_hkl_button.clicked.connect(self.view_model.calculate_hkl)
        self.add_peak_button.clicked.connect(self.view_model.add_peak)

    def _connect_modulation_clusters_widgets(self):
        self.param_eps_line.editingFinished.connect(
            lambda: process_change(
                "ub_modulation_cluster.max_distance",
                self.param_eps_line.text(),
                self.param_eps_line,
                self.modulation_callback,
            )
        )
        self.param_min_line.editingFinished.connect(
            lambda: process_change(
                "ub_modulation_cluster.min_samples",
                self.param_min_line.text(),
                self.param_min_line,
                self.modulation_callback,
            )
        )
        self.cluster_button.clicked.connect(self.view_model.cluster)

    def set_instrument(self, instrument: InstrumentParameters):
        self.set_data_list(instrument)

        self.check_h_line.setText(str(round(instrument.check_h, 4)))
        self.check_k_line.setText(str(round(instrument.check_k, 4)))
        self.check_l_line.setText(str(round(instrument.check_l, 4)))
        self.horizontal_line.setText(str(round(instrument.horizontal_angle, 2)))
        self.vertical_line.setText(str(round(instrument.vertical_angle, 2)))
        self.diffraction_label.setText(f"{instrument.diffraction_label}:")
        self.diffraction_line.setText(str(round(instrument.diffraction, 3)))

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

    def set_ub_controls(self, ub_controls: UBControls):
        self.form_line.setText(ub_controls.calculate.form)

        self.T11_line.setText("{:.0f}".format(ub_controls.transform.t11))
        self.T12_line.setText("{:.0f}".format(ub_controls.transform.t12))
        self.T13_line.setText("{:.0f}".format(ub_controls.transform.t13))
        self.T21_line.setText("{:.0f}".format(ub_controls.transform.t21))
        self.T22_line.setText("{:.0f}".format(ub_controls.transform.t22))
        self.T23_line.setText("{:.0f}".format(ub_controls.transform.t23))
        self.T31_line.setText("{:.0f}".format(ub_controls.transform.t31))
        self.T32_line.setText("{:.0f}".format(ub_controls.transform.t32))
        self.T33_line.setText("{:.0f}".format(ub_controls.transform.t33))

        self.update_cell_table(ub_controls.calculate.table_contents)

        self.symmetry_combo.clear()
        for symbol in ub_controls.transform.symmetry_options:
            self.symmetry_combo.addItem(symbol)

    def set_parameters(self, parameters: Parameters):
        self.a_line.setText(
            parameters.lattice.format_with_error(
                parameters.lattice.a, parameters.lattice.a_error
            )
        )
        self.b_line.setText(
            parameters.lattice.format_with_error(
                parameters.lattice.b, parameters.lattice.b_error
            )
        )
        self.c_line.setText(
            parameters.lattice.format_with_error(
                parameters.lattice.c, parameters.lattice.c_error
            )
        )
        self.alpha_line.setText(
            parameters.lattice.format_with_error(
                parameters.lattice.alpha, parameters.lattice.alpha_error
            )
        )
        self.beta_line.setText(
            parameters.lattice.format_with_error(
                parameters.lattice.beta, parameters.lattice.beta_error
            )
        )
        self.gamma_line.setText(
            parameters.lattice.format_with_error(
                parameters.lattice.gamma, parameters.lattice.gamma_error
            )
        )

        self.uh_line.setText(str(parameters.sample_directions.uh))
        self.uk_line.setText(str(parameters.sample_directions.uk))
        self.ul_line.setText(str(parameters.sample_directions.ul))
        self.vh_line.setText(str(parameters.sample_directions.vh))
        self.vk_line.setText(str(parameters.sample_directions.vk))
        self.vl_line.setText(str(parameters.sample_directions.vl))
        self.wh_line.setText(str(parameters.sample_directions.wh))
        self.wk_line.setText(str(parameters.sample_directions.wk))
        self.wl_line.setText(str(parameters.sample_directions.wl))

    def set_peaks(self, peaks: Peaks):
        self.d1_line.setText("{:.4f}".format(peaks.d1))
        self.d2_line.setText("{:.4f}".format(peaks.d2))
        self.phi_line.setText("{:.4f}".format(peaks.phi))

        self.update_peaks_table(peaks)

        self.h_line.blockSignals(True)
        self.k_line.blockSignals(True)
        self.l_line.blockSignals(True)

        self.int_h_line.blockSignals(True)
        self.int_k_line.blockSignals(True)
        self.int_l_line.blockSignals(True)

        self.int_m_line.blockSignals(True)
        self.int_n_line.blockSignals(True)
        self.int_p_line.blockSignals(True)

        self.h_line.setText("{:.3f}".format(peaks.h))
        self.k_line.setText("{:.3f}".format(peaks.k))
        self.l_line.setText("{:.3f}".format(peaks.l))

        self.int_h_line.setText("{:.0f}".format(peaks.int_h))
        self.int_k_line.setText("{:.0f}".format(peaks.int_k))
        self.int_l_line.setText("{:.0f}".format(peaks.int_l))

        self.int_m_line.setText("{:.0f}".format(peaks.int_m))
        self.int_n_line.setText("{:.0f}".format(peaks.int_n))
        self.int_p_line.setText("{:.0f}".format(peaks.int_p))

        self.h_line.blockSignals(False)
        self.k_line.blockSignals(False)
        self.l_line.blockSignals(False)

        self.int_h_line.blockSignals(False)
        self.int_k_line.blockSignals(False)
        self.int_l_line.blockSignals(False)

        self.int_m_line.blockSignals(False)
        self.int_n_line.blockSignals(False)
        self.int_p_line.blockSignals(False)

        self.intensity_line.setText("{:.2e}".format(peaks.intensity))
        self.sigma_line.setText("{:.2e}".format(peaks.sigma))

        self.lambda_line.setText("{:.4f}".format(peaks.lambda_value))
        self.d_line.setText("{:.4f}".format(peaks.d))

        self.run_line.setText(str(peaks.run))
        self.bank_line.setText(str(peaks.bank))
        self.row_line.setText(str(peaks.row))
        self.col_line.setText(str(peaks.col))

    def highlight_peak(self, peaks: Peaks):
        self.plotter.highlight_peak(peaks.last_highlight)
        self.vis_widget.set_position(peaks.position)

    def highlight_peaks(self, peaks: Peaks):
        self.peaks_table.blockSignals(True)
        for row, peak in enumerate(peaks.peaks, start=1):
            if row in peaks.highlighted_peaks:
                self.peaks_table.selectRow(row)
        self.peaks_table.blockSignals(False)

    def update_cell_table(self, cells):
        self.cell_table.clearSelection()
        self.cell_table.setRowCount(0)
        self.cell_table.setRowCount(len(cells))

        for row, cell in enumerate(cells):
            data = [
                cell["form"],
                cell["error"],
                cell["bravais"],
                (
                    cell["a"],
                    cell["b"],
                    cell["c"],
                    cell["alpha"],
                    cell["beta"],
                    cell["gamma"],
                    cell["V"],
                ),
            ]
            self.set_cell(row, data)

    def set_cell(self, row, cell):
        form, error, bravais, params = cell
        a, b, c, alpha, beta, gamma, vol = params
        error = "{:.4f}".format(error)
        a = "{:.2f}".format(a)
        b = "{:.2f}".format(b)
        c = "{:.2f}".format(c)
        alpha = "{:.1f}".format(alpha)
        beta = "{:.1f}".format(beta)
        gamma = "{:.1f}".format(gamma)
        vol = "{:.0f}".format(vol)
        self.cell_table.setVerticalHeaderItem(row, QTableWidgetItem(str(form)))
        self.cell_table.setItem(row, 0, QTableWidgetItem(error))
        self.cell_table.setItem(row, 1, QTableWidgetItem(bravais))
        self.cell_table.setItem(row, 2, QTableWidgetItem(a))
        self.cell_table.setItem(row, 3, QTableWidgetItem(b))
        self.cell_table.setItem(row, 4, QTableWidgetItem(c))
        self.cell_table.setItem(row, 5, QTableWidgetItem(alpha))
        self.cell_table.setItem(row, 6, QTableWidgetItem(beta))
        self.cell_table.setItem(row, 7, QTableWidgetItem(gamma))
        self.cell_table.setItem(row, 8, QTableWidgetItem(vol))

    def load_Q(self) -> None:
        path = self.view_model.get_shared_file_path()
        filename = self.load_Q_file_dialog(path)
        if filename:
            self.view_model.load_Q(filename)

    def load_Q_file_dialog(self, path=""):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog

        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.AnyFile)

        filename, _ = file_dialog.getOpenFileName(
            self, "Load Q file", path, "Q files (*.nxs)", options=options
        )

        return filename

    def save_Q(self):
        path = self.view_model.get_shared_file_path()
        filename = self.save_Q_file_dialog(path)
        if filename:
            self.view_model.save_Q(filename)

    def save_Q_file_dialog(self, path=""):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog

        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.AnyFile)

        filename, _ = file_dialog.getSaveFileName(
            self, "Save Q file", path, "Q files (*.nxs)", options=options
        )

        if filename is not None and not filename.endswith(".nxs"):
            filename += ".nxs"

        return filename

    def load_peaks(self):
        path = self.view_model.get_shared_file_path()
        filename = self.load_peaks_file_dialog(path)
        if filename:
            self.view_model.load_peaks(filename)

    def load_peaks_file_dialog(self, path=""):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog

        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.AnyFile)

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Load peaks file",
            path,
            "Peaks files (*.nxs)",
            options=options,
        )

        return filename

    def save_peaks(self):
        path = self.view_model.get_shared_file_path()
        filename = self.save_peaks_file_dialog(path)
        if filename:
            self.view_model.save_peaks(filename)

    def save_peaks_file_dialog(self, path=""):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog

        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.AnyFile)

        filename, _ = file_dialog.getSaveFileName(
            self,
            "Save peaks file",
            path,
            "Peaks files (*.nxs)",
            options=options,
        )

        if filename is not None and not filename.endswith(".nxs"):
            filename += ".nxs"

        return filename

    def load_UB(self):
        path = self.view_model.get_shared_file_path()
        filename = self.load_UB_file_dialog(path)
        if filename:
            self.view_model.load_UB(filename)

    def load_UB_file_dialog(self, path=""):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog

        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.AnyFile)

        filename, _ = file_dialog.getOpenFileName(
            self, "Load UB file", path, "UB files (*.mat)", options=options
        )

        return filename

    def save_UB(self):
        path = self.view_model.get_shared_file_path()
        filename = self.save_UB_file_dialog(path)
        if filename:
            self.view_model.save_UB(filename)

    def save_UB_file_dialog(self, path=""):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog

        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.AnyFile)

        filename, _ = file_dialog.getSaveFileName(
            self, "Save UB file", path, "UB files (*.mat)", options=options
        )

        if filename is not None and not filename.endswith(".mat"):
            filename += ".mat"

        return filename

    def highlight_cell(self) -> None:
        row = self.cell_table.currentRow()
        if row is None:
            return

        header = self.cell_table.verticalHeaderItem(row)
        if header is None:
            return

        self.view_model.highlight_cell(header.text())

    def update_peaks_table(self, peaks: Peaks):
        self.peaks_table.blockSignals(True)
        self.peaks_table.setSortingEnabled(False)
        self.peaks_table.clearSelection()
        self.peaks_table.setRowCount(0)
        self.peaks_table.setRowCount(len(peaks.peaks))

        for row, peak in enumerate(peaks.peaks):
            self.set_peak(row, peak)

        self.index_line.setText("{}".format(peaks.index))
        self.total_line.setText("{}".format(peaks.total))

        self.peaks_table.blockSignals(False)
        self.peaks_table.setSortingEnabled(True)

    def set_peak(self, row, peak):
        hkl = peak["hkl"]
        d = peak["d_spacing"]
        lamda = peak["wavelength"]
        intens = peak["intensity"]
        signal_to_noise = peak["signal_to_noise"]
        peak_no = peak["peak_no"]
        h, k, l = hkl
        h = "{:.3f}".format(h)
        k = "{:.3f}".format(k)
        l = "{:.3f}".format(l)
        d = "{:.4f}".format(d)
        lamda = "{:.4f}".format(lamda)
        intens = "{:.2e}".format(intens)
        signal_to_noise = "{:.2f}".format(signal_to_noise)
        peak_no = str(peak_no + 1)
        self.peaks_table.setItem(row, 0, self.set_item_value(h))
        self.peaks_table.setItem(row, 1, self.set_item_value(k))
        self.peaks_table.setItem(row, 2, self.set_item_value(l))
        self.peaks_table.setItem(row, 3, self.set_item_value(d))
        self.peaks_table.setItem(row, 4, self.set_item_value(lamda))
        self.peaks_table.setItem(row, 5, self.set_item_value(intens))
        self.peaks_table.setItem(row, 6, self.set_item_value(signal_to_noise))
        self.peaks_table.setItem(row, 7, self.set_item_value(peak_no))

    def set_item_value(self, value):
        item = QTableWidgetItem()
        item.setData(Qt.DisplayRole, float(value))
        return item

    def update_slice(self, data):
        self.min_slider.blockSignals(True)
        self.max_slider.blockSignals(True)
        self.min_slider.setValue(0)
        self.max_slider.setValue(100)
        self.min_slider.blockSignals(False)
        self.max_slider.blockSignals(False)

        slice_dict, cmap, scale = data
        self.plotter.update_slice(slice_dict, cmap, scale)

    def set_data_list(self, instrument: InstrumentParameters):
        self.data_combo.clear()
        for item in instrument.data_options:
            self.data_combo.addItem(item)
        self.data_combo.setCurrentText(instrument.data)

    def update_instrument_view(self, result):
        self.plotter.update_instrument_view(result[0])
        self.plotter.update_roi_view(result[1])
        self.plotter.update_scan_view(result[1])

    def update_cluster_table(self, clusters: ModulationClusters):
        self.cluster_table.setRowCount(0)
        self.cluster_table.setRowCount(len(clusters.centroids))

        for row, centroid in enumerate(clusters.centroids):
            self.cluster_table.setItem(row, 0, QTableWidgetItem(centroid[0]))
            self.cluster_table.setItem(row, 1, QTableWidgetItem(centroid[1]))
            self.cluster_table.setItem(row, 2, QTableWidgetItem(centroid[2]))
