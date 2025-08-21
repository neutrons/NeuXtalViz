import copy
from typing import Any

from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QFileDialog, QTableWidgetItem
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
from matplotlib.figure import Figure
from nova.mvvm.pydantic_utils import validate_pydantic_parameter
from qtpy.QtCore import Qt
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

from NeuXtalViz.view_models.experiment_planner import ExperimentPlannerViewModel, EPSettings, EPParams, EPGoniometers, \
    EPMotors, EPPlan
from NeuXtalViz.views.shared.planner_plots import plot_statistics
from NeuXtalViz.views.shared.planner_plotter import PlannerPlotter


def validate_element(key: str, value: Any, element: Any = None) -> None:
    if element:
        res = validate_pydantic_parameter(key, value)
        if res is not True:
            element.setStyleSheet("border: 1px solid red;")
        else:
            element.setStyleSheet("")


def process_validation(key: str, value: Any, element: Any = None) -> None:
    validate_element(key, value, element)


class EPGoniometerTab(QWidget):
    def __init__(self, view_model: ExperimentPlannerViewModel, parent=None):
        super().__init__(parent)

        self.view_model = view_model
        self.create_gui()
        self.connect_bindings()
        self.connect_widgets()

    def connect_bindings(self):
        self.callback_goniometers = self.view_model.ep_goniometers_bind.connect("ep_goniometers",
                                                                                self.on_goniometers_update)

    def on_goniometers_update(self, goniometers: EPGoniometers):
        self.set_modes(goniometers)
        self.update_table(goniometers)

    def process_goniometers_change(self, key: str, value: Any, element: Any = None) -> None:
        self.callback_goniometers(key, value)

    def set_modes(self, goniometers: EPGoniometers):
        self.mode_combo.blockSignals(True)
        self.mode_combo.clear()
        for mode in goniometers.modes:
            self.mode_combo.addItem(mode)
        self.mode_combo.setCurrentText(goniometers.current_mode)
        self.mode_combo.blockSignals(False)

    def connect_widgets(self):
        self.mode_combo.currentTextChanged.connect(
            lambda value: self.process_goniometers_change("ep_goniometers.current_mode", value)
        )

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
        self.goniometer_table.itemChanged.connect(self.update_goniometer_table)

        self.setLayout(goniometer_layout)

    def update_table(self, goniometers: EPGoniometers):
        self.goniometer_table.blockSignals(True)
        self.goniometer_table.clearContents()
        self.goniometer_table.setRowCount(0)
        self.goniometer_table_data = copy.deepcopy(goniometers.goniometer_table)
        self.goniometer_table.setRowCount(len(self.goniometer_table_data))

        for row, gon in enumerate(self.goniometer_table_data):
            angle, amin, amax, editable = gon["motor"], gon["min"], gon["max"], gon["editable"]
            amin, amax = str(amin), str(amax)
            self.goniometer_table.setItem(row, 0, QTableWidgetItem(angle))
            self.goniometer_table.setItem(row, 1, QTableWidgetItem(amin))
            self.goniometer_table.setItem(row, 2, QTableWidgetItem(amax))
            item = self.goniometer_table.item(row, 0)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            if editable:
                for j in [1, 2]:
                    item = self.goniometer_table.item(row, j)
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        self.goniometer_table.blockSignals(False)

    def update_goniometer_table(self, item):
        row = item.row()
        min = self.goniometer_table.item(row, 1).text()
        max = self.goniometer_table.item(row, 2).text()
        self.goniometer_table_data[row]["min"] = float(min)
        self.goniometer_table_data[row]["max"] = float(max)
        self.process_goniometers_change("ep_goniometers.goniometer_table", self.goniometer_table_data)


class EPMotorTab(QWidget):
    def __init__(self, view_model: ExperimentPlannerViewModel, parent=None):
        super().__init__(parent)

        self.view_model = view_model
        self.create_gui()
        self.connect_bindings()
        self.connect_widgets()

    def connect_bindings(self):
        self.callback_motors = self.view_model.ep_motors_bind.connect("ep_motors",
                                                                      self.on_motors_update)

    def on_motors_update(self, motors: EPMotors):
        self.mask_line.setText(motors.mask_file)
        self.cal_line.setText(motors.detector_file)
        self.update_table(motors.motor_table)

    def update_table(self, motors):
        self.motor_table.blockSignals(True)
        self.motor_table.clearContents()
        self.motors_table_data = copy.deepcopy(motors)
        self.motor_table.setRowCount(0)
        self.motor_table.setRowCount(len(motors))

        for row, mot in enumerate(motors):
            setting, val = mot["motor"], mot["value"]
            val = str(val)
            self.motor_table.setItem(row, 0, QTableWidgetItem(setting))
            self.motor_table.setItem(row, 1, QTableWidgetItem(val))
            item = self.motor_table.item(row, 0)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)

        self.motor_table.blockSignals(False)

    def update_motors_table(self, item):
        row = item.row()
        value = self.motor_table.item(row, 1).text()
        self.motors_table_data[row]["value"] = float(value)
        self.process_motors_change("ep_motors.motor_table", self.motors_table_data)

    def process_motors_change(self, key: str, value: Any, element: Any = None) -> None:
        self.callback_motors(key, value)

    def connect_widgets(self):
        self.mask_browse_button.clicked.connect(self.load_mask)
        self.mask_line.editingFinished.connect(
            lambda: self.process_motors_change("ep_motors.mask_file", self.mask_line.text(), self.mask_line)
        )
        self.cal_browse_button.clicked.connect(self.load_detector)
        self.cal_line.editingFinished.connect(
            lambda: self.process_motors_change("ep_motors.detector_file", self.cal_line.text(), self.cal_line)
        )

    def load_mask(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog

        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.AnyFile)

        file_filters = "Mask files (*.xml)"

        filename, _ = file_dialog.getOpenFileName(
            self, "Load mask file", self.view_model.get_load_path(), file_filters, options=options
        )
        if filename:
            self.process_motors_change("ep_motors.mask_file", filename)

    def load_detector(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog

        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.AnyFile)

        file_filters = "Calibration files (*.DetCal *.detcal *.xml)"

        filename, _ = file_dialog.getOpenFileName(
            self, "Load calibration file", self.view_model.get_load_path(), file_filters, options=options
        )

        if filename:
            self.process_motors_change("ep_motors.detector_file", filename)

    def create_gui(self):
        self.motor_table = QTableWidget()
        self.motor_table.setRowCount(0)
        self.motor_table.setColumnCount(2)

        resize = QHeaderView.Stretch

        labels = ["Motor", "Value"]

        self.motor_table.horizontalHeader().setStretchLastSection(True)
        self.motor_table.horizontalHeader().setSectionResizeMode(resize)
        self.motor_table.setHorizontalHeaderLabels(labels)
        self.motor_table.itemChanged.connect(self.update_motors_table)

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
        self.plan_table_data = []
        self.create_gui()
        self.create_bindings()
        self.connect_widgets()

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
        self.plan_table.itemChanged.connect(self.handle_plan_table_item_changed)
        self.plan_table.setSelectionBehavior(self.plan_table.SelectRows)
        selection_model = self.plan_table.selectionModel()
        selection_model.selectionChanged.connect(self.on_rows_selected)

        self.mesh_table = QTableWidget()
        self.mesh_table.horizontalHeader().setStretchLastSection(True)
        resize = QHeaderView.Stretch
        self.mesh_table.horizontalHeader().setSectionResizeMode(resize)
        labels = ["Motor", "Min", "Max", "Angles"]
        self.mesh_table.setHorizontalHeaderLabels(labels)
        self.mesh_table.setRowCount(0)
        self.mesh_table.setColumnCount(4)
        plan_layout.addWidget(self.mesh_table)
        self.mesh_table.itemChanged.connect(self.handle_mesh_table_item_changed)

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

    def create_bindings(self):
        self.callback_plan = self.view_model.ep_plan_bind.connect("ep_plan", self.on_plan_update)

    def connect_widgets(self):
        self.optimize_button.clicked.connect(self.view_model.optimize_coverage)
        self.title_line.editingFinished.connect(
            lambda: self.process_plan_change("ep_plan.title", self.title_line.text(), self.title_line)
        )
        self.mesh_button.clicked.connect(self.view_model.mesh_scan)
        self.delete_button.clicked.connect(self.view_model.delete_angles)

    def process_plan_change(self, key: str, value: Any, element: Any = None) -> None:
        validate_element(key, value, element)
        self.callback_plan(key, value)

    def on_plan_update(self, plan: EPPlan):
        self.update_plan_table(plan)
        self.update_mesh_table(plan)
        self.set_counting_options(plan)

    def set_counting_options(self, plan: EPPlan):
        self.count_combo.blockSignals(True)
        self.count_combo.clear()
        for option in plan.counting_options:
            self.count_combo.addItem(option)
        self.count_combo.setCurrentText(plan.counting_option)
        self.count_combo.blockSignals(False)

    def on_rows_selected(self, selected, deselected):
        rows = set(index.row() for index in self.plan_table.selectedIndexes())
        self.process_plan_change("ep_plan.plan_table_selected_rows", rows)


    def add_orientation(self, row_number, plan: EPPlan):
        self.plan_table.blockSignals(True)
        self.plan_table.setSortingEnabled(False)
        self.plan_table.setRowCount(row_number + 1)

        col = 0

        item = QTableWidgetItem(plan.plan_table[row_number]["title"])
        self.plan_table.setItem(row_number, col, item)
        col += 1

        for key, value in plan.plan_table[row_number].items():
            if "angle" in key:
                item = QTableWidgetItem("{:.1f}".format(value))
                self.plan_table.setItem(row_number, col, item)
                col += 1

        self.plan_table.setItem(row_number, col, QTableWidgetItem(plan.plan_table[row_number]["comment"]))
        col += 1

        combobox = QComboBox()
        for option in plan.counting_options:
            combobox.addItem(option)
        if plan.counting_option:
            combobox.setCurrentText(plan.counting_option)
        self.plan_table.setCellWidget(row_number, col, combobox)
        combobox.currentTextChanged.connect(
            lambda text, row=row_number: self.handle_plan_table_combo_changed(text, row))
        col += 1

        val = plan.count
        if val is not None:
            item = QTableWidgetItem("{:.3f}".format(val))
            self.plan_table.setItem(row_number, col, item)
        col += 1

        flags = Qt.ItemIsUserCheckable | Qt.ItemIsEnabled

        checkbox = QTableWidgetItem("")
        checkbox.setText("")
        checkbox.setFlags(flags)
        checkbox.setCheckState(Qt.Checked if plan.plan_table[row_number]["use"] else Qt.Unchecked)
        self.plan_table.setItem(row_number, col, checkbox)

        # todo:
        #        self.set_peak_list(self.get_number_of_orientations())
        self.plan_table.blockSignals(False)
        self.plan_table.setSortingEnabled(True)

    def update_plan_table(self, plan: EPPlan):
        self.plan_table.blockSignals(True)
        self.plan_table.clearContents()
        self.plan_table.setRowCount(0)
        self.plan_table.setColumnCount(0)
        self.plan_table_data = copy.deepcopy(plan.plan_table)

        labels = [val["title"] for val in plan.plan_table_headers]
        self.plan_table.setColumnCount(len(labels))

        resize = QHeaderView.Stretch
        self.plan_table.horizontalHeader().setStretchLastSection(True)
        self.plan_table.horizontalHeader().setSectionResizeMode(resize)
        self.plan_table.setHorizontalHeaderLabels(labels)

        for row_number in range(len(self.plan_table_data)):
            self.add_orientation(row_number, plan)

        self.plan_table.blockSignals(False)

    def update_mesh_table(self, plan: EPPlan):
        self.mesh_table.blockSignals(True)
        self.mesh_table.clearContents()
        self.mesh_table.setRowCount(0)
        self.mesh_table_data = copy.deepcopy(plan.mesh_table)
        self.mesh_table.setRowCount(len(self.mesh_table_data))
        for row, gon in enumerate(self.mesh_table_data):
            motor, amin, amax, angle = gon["motor"], gon["min"], gon["max"], gon["angle"]
            self.mesh_table.setItem(row, 0, QTableWidgetItem(motor))
            item = self.mesh_table.item(row, 0)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.mesh_table.setItem(row, 1, QTableWidgetItem(str(amin)))
            self.mesh_table.setItem(row, 2, QTableWidgetItem(str(amax)))
            self.mesh_table.setItem(row, 3, QTableWidgetItem(str(angle)))
        self.mesh_table.blockSignals(False)

    def handle_mesh_table_item_changed(self, item):
        row = item.row()
        min = self.mesh_table.item(row, 1).text()
        max = self.mesh_table.item(row, 2).text()
        angle = self.mesh_table.item(row, 3).text()
        self.mesh_table_data[row]["min"] = float(min)
        self.mesh_table_data[row]["max"] = float(max)
        self.mesh_table_data[row]["angle"] = int(angle)
        self.process_plan_change("ep_plan.mesh_table", self.mesh_table_data)

    def handle_plan_table_item_changed(self, item):
        self.plan_table.blockSignals(True)

        row = item.row()

        self.plan_table_data[row]["title"] = self.plan_table.item(row, 0).text()
        n_angles = self.plan_table.columnCount() - 5
        for i in range(n_angles):
            self.plan_table_data[row][f"angle{i}"] = float(self.plan_table.item(row, i + 1).text())
        self.plan_table_data[row]["comment"] = self.plan_table.item(row, n_angles + 1).text()

        self.plan_table_data[row]["value"] = float(self.plan_table.item(row, n_angles + 3).text())
        self.plan_table_data[row]["use"] = self.plan_table.item(row, n_angles + 4).checkState() == Qt.Checked

        self.process_plan_change("ep_plan.plan_table", self.plan_table_data)

        self.plan_table.blockSignals(False)

    def handle_plan_table_combo_changed(self, text, row):
        self.plan_table.blockSignals(True)
        self.plan_table_data[row]["wait_for"] = text
        self.process_plan_change("ep_plan.plan_table", self.plan_table_data)
        self.plan_table.blockSignals(False)


class EPSettings(QWidget):
    def __init__(self, view_model: ExperimentPlannerViewModel, parent=None):
        super().__init__(parent)
        self.view_model = view_model
        self.create_gui()
        self.create_bindings()
        self.connect_widgets()

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

    def create_bindings(self):
        self.callback_settings = self.view_model.ep_settings_bind.connect("ep_settings", self.on_settings_update)

    def on_settings_update(self, settings: EPSettings):
        self.set_crystal_system(settings.crystal_system)
        self.set_point_group(settings)
        self.set_lattice_centering(settings)

    def process_settings_change(self, key: str, value: Any, element: Any = None) -> None:
        validate_element(key, value, element)
        self.callback_settings(key, value)

    def connect_widgets(self):
        self.load_UB_button.clicked.connect(self.load_UB)
        self.crystal_combo.currentTextChanged.connect(
            lambda value: self.process_settings_change("ep_settings.crystal_system", value)
        )
        self.point_group_combo.currentTextChanged.connect(
            lambda value: self.process_settings_change("ep_settings.point_group", value)
        )
        self.lattice_centering_combo.currentTextChanged.connect(
            lambda value: self.process_settings_change("ep_settings.lattice_centering", value)
        )

    def load_UB(self):
        filename = self.load_UB_file_dialog()

        if filename:
            self.view_model.load_UB(filename)

    def load_UB_file_dialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog

        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.AnyFile)

        filename, _ = file_dialog.getOpenFileName(
            self, "Load UB file", "", "UB files (*.mat)", options=options
        )

        return filename

    def set_crystal_system(self, crystal_system):
        index = self.crystal_combo.findText(crystal_system)
        if index >= 0:
            self.crystal_combo.blockSignals(True)
            self.crystal_combo.setCurrentIndex(index)
            self.crystal_combo.blockSignals(False)

    def set_point_group(self, settings: EPSettings):
        self.point_group_combo.blockSignals(True)
        self.point_group_combo.clear()
        for group in settings.point_groups:
            self.point_group_combo.addItem(group)
        index = self.point_group_combo.findText(settings.point_group)
        if index >= 0:
            self.point_group_combo.setCurrentIndex(index)
        self.point_group_combo.blockSignals(False)

    def set_lattice_centering(self, settings: EPSettings):
        self.lattice_centering_combo.blockSignals(True)
        self.lattice_centering_combo.clear()
        for centering in settings.lattice_centerings:
            self.lattice_centering_combo.addItem(centering)
        index = self.lattice_centering_combo.findText(settings.lattice_centering)
        if index >= 0:
            self.lattice_centering_combo.setCurrentIndex(index)
        self.lattice_centering_combo.blockSignals(False)


class EPParams(QWidget):
    def __init__(self, view_model: ExperimentPlannerViewModel, parent=None):
        super().__init__(parent)
        self.view_model = view_model
        self.create_gui()
        self.create_bindings()
        self.connect_widgets()

    def create_bindings(self):
        self.callback_params = self.view_model.ep_params_bind.connect("ep_params", self.on_params_update)

    def connect_widgets(self):
        self.instrument_combo.currentTextChanged.connect(
            lambda value: self.process_params_change("ep_params.instrument", value)
        )
        self.wl_min_line.editingFinished.connect(
            lambda: self.process_params_change("ep_params.wl_min", self.wl_min_line.text(), self.wl_min_line)
        )
        self.wl_max_line.editingFinished.connect(
            lambda: self.process_params_change("ep_params.wl_max", self.wl_max_line.text(), self.wl_max_line)
        )
        self.d_min_line.editingFinished.connect(
            lambda: self.process_params_change("ep_params.d_min", self.d_min_line.text(), self.d_min_line)
        )
        self.wl_min_line.textChanged.connect(
            lambda value: process_validation("ep_params.wl_min", value, self.wl_min_line)
        )
        self.wl_max_line.textChanged.connect(
            lambda value: process_validation("ep_params.wl_max", value, self.wl_max_line)
        )
        self.d_min_line.textChanged.connect(
            lambda value: process_validation("ep_params.d_min", value, self.d_min_line)
        )

    def on_params_update(self, params: EPParams):
        self.set_wavelength(params)

    def process_params_change(self, key: str, value: Any, element: Any = None) -> None:
        validate_element(key, value, element)
        self.callback_params(key, value)

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

    def set_wavelength(self, params: EPParams):
        self.wl_min_line.blockSignals(True)
        self.wl_max_line.blockSignals(True)
        if params.no_wl_max:
            self.wl_min_line.setText(str(params.wl_min))
            self.wl_max_line.setText(str(params.wl_min))
            self.wl_max_line.setReadOnly(True)
        else:
            self.wl_min_line.setText(str(params.wl_min))
            self.wl_max_line.setText(str(params.wl_max))
            self.wl_max_line.setEnabled(True)
        self.wl_min_line.blockSignals(False)
        self.wl_max_line.blockSignals(False)


class EPResults(QWidget):
    def __init__(self, view_model: ExperimentPlannerViewModel, plotter: PlannerPlotter, parent=None):
        super().__init__(parent)
        self.view_model = view_model
        self.plotter = plotter
        self.create_gui()
        self.create_bindings()

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

    def create_bindings(self):
        self.view_model.ep_statistics_bind.connect("ep_statistics", self.plot_statistics)
        self.view_model.ep_peak_bind.connect("ep_peak", self.plot_peak)

    def plot_peak(self, peak_dict):
        self.plotter.add_peaks(peak_dict)

    def plot_statistics(self, stats):
        plot_statistics(self.ax_cov, *stats)
        self.canvas_cov.draw_idle()
        self.canvas_cov.flush_events()


class EPCoverageTab(QWidget):
    def __init__(self, view_model: ExperimentPlannerViewModel, plotter: PlannerPlotter, parent=None):
        super().__init__(parent)

        self.plotter = plotter
        self.view_model = view_model
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.create_gui(layout)

    def create_gui(self, layout):
        settings = EPSettings(self.view_model)
        layout.addWidget(settings)

        params = EPParams(self.view_model)
        layout.addWidget(params)

        results = EPResults(self.view_model, self.plotter)
        layout.addWidget(results)
