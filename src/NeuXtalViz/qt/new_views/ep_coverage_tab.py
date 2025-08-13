from PyQt5.QtGui import QIntValidator
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
from matplotlib.figure import Figure
from qtpy.QtGui import QDoubleValidator
from qtpy.QtWidgets import (
    QWidget,
    QTableWidget,
    QHeaderView,
    QLineEdit,
    QLabel,
    QComboBox,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
    QTabWidget,
)

from NeuXtalViz.view_models.experiment_planner import ExperimentPlannerViewModel


class EPGoniometerTab(QWidget):
    def __init__(self, view_model: ExperimentPlannerViewModel, parent=None):
        super().__init__(parent)

        self.view_model = view_model
        self.create_gui()

    def create_gui(self):
        self.goniometer_table = QTableWidget()

        self.goniometer_table.setRowCount(0)
        self.goniometer_table.setColumnCount(3)

        labels = ["Motor", "Min", "Max"]
        resize = QHeaderView.Stretch
        self.goniometer_table.horizontalHeader().setStretchLastSection(True)
        self.goniometer_table.horizontalHeader().setSectionResizeMode(resize)
        self.goniometer_table.setHorizontalHeaderLabels(labels)
        goniometer_layout = QVBoxLayout()
        mode_layout = QHBoxLayout()
        self.mode_combo = QComboBox(self)
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch(1)
        goniometer_layout.addLayout(mode_layout)
        goniometer_layout.addWidget(self.goniometer_table)
        self.setLayout(goniometer_layout)


class EPMotorTab(QWidget):
    def __init__(self, view_model: ExperimentPlannerViewModel, parent=None):
        super().__init__(parent)

        self.view_model = view_model
        self.create_gui()

    def create_gui(self):
        self.motor_table = QTableWidget()
        self.motor_table.setRowCount(0)
        self.motor_table.setColumnCount(2)

        resize = QHeaderView.Stretch

        labels = ["Motor", "Value"]

        self.motor_table.horizontalHeader().setStretchLastSection(True)
        self.motor_table.horizontalHeader().setSectionResizeMode(resize)
        self.motor_table.setHorizontalHeaderLabels(labels)
        cal_layout = QGridLayout()

        self.cal_line = QLineEdit("")
        self.mask_line = QLineEdit("")

        self.cal_browse_button = QPushButton("Detector", self)
        self.mask_browse_button = QPushButton("Mask", self)

        cal_layout.addWidget(self.cal_line, 0, 0)
        cal_layout.addWidget(self.cal_browse_button, 0, 1)

        cal_layout.addWidget(self.mask_line, 1, 0)
        cal_layout.addWidget(self.mask_browse_button, 1, 1)
        motor_layout = QVBoxLayout()
        motor_layout.addLayout(cal_layout)
        motor_layout.addWidget(self.motor_table)
        self.setLayout(motor_layout)


class EPPlanTab(QWidget):
    def __init__(self, view_model: ExperimentPlannerViewModel, parent=None):
        super().__init__(parent)

        self.view_model = view_model
        self.create_gui()

    def create_gui(self):
        plan_layout = QVBoxLayout()

        planning_layout = QHBoxLayout()
        self.title_line = QLineEdit("Scan Title")
        planning_layout.addWidget(self.title_line)
        self.count_combo = QComboBox(self)
        planning_layout.addWidget(self.count_combo)
        self.count_line = QLineEdit("1.0")
        notation = QDoubleValidator.StandardNotation
        validator = QDoubleValidator(0.001, 10000, 5, notation=notation)
        self.count_line.setValidator(validator)
        planning_layout.addWidget(self.count_line)
        self.update_button = QPushButton("Update Highlighted", self)
        planning_layout.addWidget(self.update_button)
        planning_layout.addStretch(1)
        settings_label = QLabel("Settings")
        planning_layout.addWidget(settings_label)
        self.settings_line = QLineEdit("20")
        validator = QIntValidator(1, 1000)
        self.settings_line.setValidator(validator)
        planning_layout.addWidget(self.settings_line)
        self.optimize_button = QPushButton("Optimize Coverage", self)
        planning_layout.addWidget(self.optimize_button)
        plan_layout.addLayout(planning_layout)

        self.plan_table = QTableWidget()
        plan_layout.addWidget(self.plan_table)

        self.mesh_table = QTableWidget()
        self.mesh_table.horizontalHeader().setStretchLastSection(True)
        resize = QHeaderView.Stretch
        self.mesh_table.horizontalHeader().setSectionResizeMode(resize)
        labels = ["Motor", "Min", "Max", "Angles"]
        self.mesh_table.setHorizontalHeaderLabels(labels)
        self.mesh_table.setRowCount(0)
        self.mesh_table.setColumnCount(4)
        plan_layout.addWidget(self.mesh_table)

        save_layout = QHBoxLayout()
        self.delete_button = QPushButton("Delete Highlighted", self)
        save_layout.addWidget(self.delete_button)
        self.highlight_button = QPushButton("Highlight All", self)
        save_layout.addWidget(self.highlight_button)
        self.mesh_button = QPushButton("Add Mesh", self)
        save_layout.addWidget(self.mesh_button)
        save_layout.addStretch(1)
        self.save_plan_button = QPushButton("Save CSV", self)
        save_layout.addWidget(self.save_plan_button)
        self.save_experiment_button = QPushButton("Save Experiment", self)
        save_layout.addWidget(self.save_experiment_button)
        self.load_experiment_button = QPushButton("Load Experiment", self)
        save_layout.addWidget(self.load_experiment_button)
        plan_layout.addLayout(save_layout)

        plan_layout.setStretch(1, 2)
        plan_layout.setStretch(2, 1)

        self.setLayout(plan_layout)


class EPSettings(QWidget):
    def __init__(self, view_model: ExperimentPlannerViewModel, parent=None):
        super().__init__(parent)
        self.view_model = view_model
        self.create_gui()

    def create_gui(self):
        settings_layout = QHBoxLayout()
        settings_layout.setContentsMargins(0, 0, 0, 0)
        self.load_UB_button = QPushButton("Load UB", self)
        settings_layout.addWidget(self.load_UB_button)
        self.crystal_combo = QComboBox(self)
        self.crystal_combo.addItem("Triclinic")
        self.crystal_combo.addItem("Monoclinic")
        self.crystal_combo.addItem("Orthorhombic")
        self.crystal_combo.addItem("Tetragonal")
        self.crystal_combo.addItem("Trigonal/Rhombohedral")
        self.crystal_combo.addItem("Trigonal/Hexagonal")
        self.crystal_combo.addItem("Hexagonal")
        self.crystal_combo.addItem("Cubic")
        settings_layout.addWidget(self.crystal_combo)
        self.point_group_combo = QComboBox(self)
        settings_layout.addWidget(self.point_group_combo)
        self.lattice_centering_combo = QComboBox(self)
        settings_layout.addWidget(self.lattice_centering_combo)
        self.setLayout(settings_layout)


class EPParams(QWidget):
    def __init__(self, view_model: ExperimentPlannerViewModel, parent=None):
        super().__init__(parent)
        self.view_model = view_model
        self.create_gui()

    def create_gui(self):
        params_layout = QHBoxLayout()
        params_layout.setContentsMargins(0, 0, 0, 0)
        self.instrument_combo = QComboBox(self)
        self.instrument_combo.addItem("TOPAZ")
        self.instrument_combo.addItem("MANDI")
        self.instrument_combo.addItem("CORELLI")
        self.instrument_combo.addItem("SNAP")
        self.instrument_combo.addItem("WAND²")
        self.instrument_combo.addItem("DEMAND")
        params_layout.addWidget(self.instrument_combo)
        wl_label = QLabel("λ:")
        params_layout.addWidget(wl_label)
        notation = QDoubleValidator.StandardNotation
        validator = QDoubleValidator(0.2, 10, 5, notation=notation)
        self.wl_min_line = QLineEdit("0.4")
        self.wl_min_line.setValidator(validator)
        params_layout.addWidget(self.wl_min_line)
        self.wl_max_line = QLineEdit("3.5")
        self.wl_max_line.setValidator(validator)
        params_layout.addWidget(self.wl_max_line)
        d_min_label = QLabel("d(min):")
        params_layout.addWidget(d_min_label)
        self.d_min_line = QLineEdit("0.7")
        validator = QDoubleValidator(0.4, 10, 5, notation=notation)
        self.d_min_line.setValidator(validator)
        params_layout.addWidget(self.d_min_line)
        angstrom_label = QLabel("Å")
        params_layout.addWidget(angstrom_label)
        self.setLayout(params_layout)


class EPResults(QWidget):
    def __init__(self, view_model: ExperimentPlannerViewModel, parent=None):
        super().__init__(parent)
        self.view_model = view_model
        self.create_gui()

    def create_gui(self):
        result_layout = QVBoxLayout()
        result_layout.setContentsMargins(0, 0, 0, 0)
        values_tab = QTabWidget()
        goniometer_tab = EPGoniometerTab(self.view_model)
        motor_tab = EPMotorTab(self.view_model)
        plan_tab = EPPlanTab(self.view_model)
        values_tab.addTab(goniometer_tab, "Goniometers")
        values_tab.addTab(motor_tab, "Calibration/Motors")
        values_tab.addTab(plan_tab, "Plan")
        result_layout.addWidget(values_tab)

        self.canvas_cov = FigureCanvas(
            Figure(constrained_layout=True, figsize=(6.4, 4.8))
        )
        result_layout.addWidget(NavigationToolbar2QT(self.canvas_cov, self))
        result_layout.addWidget(self.canvas_cov)

        fig = self.canvas_cov.figure
        self.ax_cov = fig.subplots(3, 1, sharex=True)
        self.ax_cov[2].set_xlabel("Resolution Shell [Å]")
        self.ax_cov[0].set_ylabel("Completeness [%]")
        self.ax_cov[1].set_ylabel("Multiplicity")
        self.ax_cov[2].set_ylabel("Unique Reflections")
        self.setLayout(result_layout)


class EPCoverageTab(QWidget):
    def __init__(self, view_model: ExperimentPlannerViewModel, parent=None):
        super().__init__(parent)

        self.view_model = view_model
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.create_gui(layout)

    def create_gui(self, layout):
        settings = EPSettings(self.view_model)
        layout.addWidget(settings)

        params = EPParams(self.view_model)
        layout.addWidget(params)

        results = EPResults(self.view_model)
        layout.addWidget(results)
