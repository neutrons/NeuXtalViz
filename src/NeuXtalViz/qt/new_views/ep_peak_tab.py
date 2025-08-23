from typing import Any

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QCheckBox
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
)

from NeuXtalViz.qt.new_views.ep_coverage_tab import validate_element, process_validation
from NeuXtalViz.view_models.experiment_planner import ExperimentPlannerViewModel, EPPeakSettings
from NeuXtalViz.views.shared.planner_plots import plot_instrument, plot_instrument_alternate


class EPCalculator(QWidget):
    def __init__(self, view_model: ExperimentPlannerViewModel, parent=None):
        super().__init__(parent)
        self.view_model = view_model
        self.create_gui()
        self.create_bindings()
        self.connect_widgets()

    def create_gui(self):
        calculator_layout = QGridLayout()
        calculator_layout.setContentsMargins(0, 0, 0, 0)

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

        gamma_label = QLabel("γ [°]", self)
        nu_label = QLabel("ν [°]", self)
        intersect_label = QLabel("λ [Å]", self)

        self.horizontal_line = QLineEdit()
        self.vertical_line = QLineEdit()
        self.intersect_line = QLineEdit()

        self.horizontal_line.setReadOnly(True)
        self.vertical_line.setReadOnly(True)
        self.intersect_line.setReadOnly(True)

        self.horizontal_alt_line = QLineEdit()
        self.vertical_alt_line = QLineEdit()
        self.intersect_alt_line = QLineEdit()

        self.horizontal_alt_line.setReadOnly(True)
        self.vertical_alt_line.setReadOnly(True)
        self.intersect_alt_line.setReadOnly(True)

        self.calculate_single_button = QPushButton("Individual Peak", self)
        self.calculate_double_button = QPushButton("Simultaneous Peaks", self)

        self.calculate_single_alt_button = QPushButton("Individual Peak", self)

        self.equivalents_box = QCheckBox("Allow Equivalents", self)
        self.equivalents_box.setChecked(False)

        calculator_layout.addWidget(h_label, 0, 1, Qt.AlignCenter)
        calculator_layout.addWidget(k_label, 0, 2, Qt.AlignCenter)
        calculator_layout.addWidget(l_label, 0, 3, Qt.AlignCenter)

        calculator_layout.addWidget(peak_1_label, 1, 0)
        calculator_layout.addWidget(self.h1_line, 1, 1)
        calculator_layout.addWidget(self.k1_line, 1, 2)
        calculator_layout.addWidget(self.l1_line, 1, 3)
        calculator_layout.addWidget(self.calculate_single_button, 1, 4)
        calculator_layout.addWidget(self.equivalents_box, 1, 5)

        calculator_layout.addWidget(peak_2_label, 2, 0)
        calculator_layout.addWidget(self.h2_line, 2, 1)
        calculator_layout.addWidget(self.k2_line, 2, 2)
        calculator_layout.addWidget(self.l2_line, 2, 3)
        calculator_layout.addWidget(self.calculate_single_alt_button, 2, 4)
        calculator_layout.addWidget(self.calculate_double_button, 2, 5)

        calculator_layout.addWidget(gamma_label, 0, 6, Qt.AlignCenter)
        calculator_layout.addWidget(nu_label, 0, 7, Qt.AlignCenter)
        calculator_layout.addWidget(intersect_label, 0, 8, Qt.AlignCenter)

        calculator_layout.addWidget(self.horizontal_line, 1, 6)
        calculator_layout.addWidget(self.horizontal_alt_line, 2, 6)

        calculator_layout.addWidget(self.vertical_line, 1, 7)
        calculator_layout.addWidget(self.vertical_alt_line, 2, 7)

        calculator_layout.addWidget(self.intersect_line, 1, 8)
        calculator_layout.addWidget(self.intersect_alt_line, 2, 8)

        self.setLayout(calculator_layout)

    def create_bindings(self):
        self.callback_settings = self.view_model.ep_peak_settings_bind.connect("ep_peak_settings",
                                                                               self.on_settings_update)

    def on_settings_update(self, settings: EPPeakSettings):
        self.set_intersect(settings.intersect)
        self.set_intersect_alternate(settings.intersect_alt)
        self.set_horizontal(settings.horizontal)
        self.set_horizontal_alternate(settings.horizontal_alt)
        self.set_vertical(settings.vertical)
        self.set_vertical_alternate(settings.vertical_alt)

    def set_intersect(self, val):
        value = str(round(val, 2)) if val is not None else ""
        self.intersect_line.setText(value)

    def set_intersect_alternate(self, val):
        value = str(round(val, 2)) if val is not None else ""
        self.intersect_alt_line.setText(value)

    def set_horizontal(self, val):
        value = str(round(val, 2)) if val is not None else ""
        self.horizontal_line.setText(value)

    def set_vertical(self, val):
        value = str(round(val, 2)) if val is not None else ""
        self.vertical_line.setText(value)

    def set_horizontal_alternate(self, val):
        value = str(round(val, 2)) if val is not None else ""
        self.horizontal_alt_line.setText(value)

    def set_vertical_alternate(self, val):
        value = str(round(val, 2)) if val is not None else ""
        self.vertical_alt_line.setText(value)

    def process_settings_change(self, key: str, value: Any, element: Any = None) -> None:
        validate_element(key, value, element)
        self.callback_settings(key, value)

    def connect_widgets(self):
        for element, name in [
            (self.h1_line, "h1"),
            (self.k1_line, "k1"),
            (self.l1_line, "l1"),
            (self.h2_line, "h2"),
            (self.k2_line, "k2"),
            (self.l2_line, "l2"),
            (self.horizontal_line, "horizontal"),
            (self.vertical_line, "vertical"),
            (self.intersect_line, "intersect"),
            (self.horizontal_alt_line, "horizontal_alt"),
            (self.vertical_alt_line, "vertical_alt"),
            (self.intersect_alt_line, "intersect_alt"),

        ]:
            element.textChanged.connect(
                lambda value, e=element, n=name: self.process_settings_change(
                    f"ep_peak_settings.{n}", value, e
                )
            )

        self.equivalents_box.stateChanged.connect(
            lambda: self.process_settings_change("ep_peak_settings.allow_equivalents",
                                                 self.equivalents_box.isChecked())
        )
        self.calculate_single_button.clicked.connect(self.view_model.calculate_single)
        self.calculate_double_button.clicked.connect(self.view_model.calculate_double)
        self.calculate_single_alt_button.clicked.connect(self.view_model.calculate_single_alt)


class EPPeakTable(QWidget):
    def __init__(self, view_model: ExperimentPlannerViewModel, parent=None):
        super().__init__(parent)
        self.view_model = view_model
        self.create_gui()
        self.create_bindings()
        self.connect_widgets()

    def create_gui(self):
        peak_layout = QVBoxLayout()
        peak_layout.setContentsMargins(0, 0, 0, 0)

        orientation_layout = QHBoxLayout()

        self.add_button = QPushButton("Add Orientation", self)

        self.angles_line = QLineEdit()

        self.angles_line.setReadOnly(True)

        self.angles_combo = QComboBox(self)

        orientation_layout.addWidget(self.angles_combo)
        orientation_layout.addWidget(self.angles_line)
        orientation_layout.addWidget(self.add_button)

        peak_layout.addLayout(orientation_layout)

        stretch = QHeaderView.Stretch

        self.peaks_table = QTableWidget()
        self.peaks_table.setRowCount(0)
        self.peaks_table.setColumnCount(5)

        header = ["h", "k", "l", "d", "λ"]

        self.peaks_table.horizontalHeader().setSectionResizeMode(stretch)
        self.peaks_table.setHorizontalHeaderLabels(header)
        self.peaks_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.peaks_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.peaks_table.setSortingEnabled(True)

        peak_layout.addWidget(self.peaks_table)

        self.setLayout(peak_layout)

    def set_angles(self, value):
        self.angles_line.setText(value)

    def create_bindings(self):
        pass

    def connect_widgets(self):
        pass


class EPCanvas(QWidget):
    def __init__(self, view_model: ExperimentPlannerViewModel, parent=None):
        super().__init__(parent)
        self.view_model = view_model
        self.create_gui()
        self.create_bindings()

    def create_gui(self):
        canvas_layout = QVBoxLayout()
        canvas_layout.setContentsMargins(0, 0, 0, 0)

        self.canvas_inst = FigureCanvas(Figure(constrained_layout=True))

        canvas_layout.addWidget(NavigationToolbar2QT(self.canvas_inst, self))
        canvas_layout.addWidget(self.canvas_inst)

        self.fig_inst = self.canvas_inst.figure
        self.ax_inst = self.fig_inst.subplots(1, 1)
        self.ax_inst.clear()
        self.ax_inst.invert_xaxis()

        self.cb_inst = None
        self.cb_inst_alt = None
        self.setLayout(canvas_layout)

    def create_bindings(self):
        self.view_model.ep_peak_plot_instrument_bind.connect("ep_peak_plot", self.plot_instrument)
        self.view_model.ep_peak_inst_bind.connect("ep_peak_inst", self.update_inst)

    def update_inst(self, settings: EPPeakSettings):
        for line in self.ax_inst.lines:
            line.remove()

        horz, vert = settings.horizontal, settings.vertical

        self.ax_inst.axvline(x=horz, color="k", linestyle="--")
        self.ax_inst.axhline(y=vert, color="k", linestyle="--")

        horz_alt = settings.horizontal_alt
        vert_alt = settings.vertical_alt

        if horz_alt is not None and vert_alt is not None:
            self.ax_inst.axvline(x=horz_alt, color="k", linestyle=":")
            self.ax_inst.axhline(y=vert_alt, color="k", linestyle=":")

        self.canvas_inst.draw_idle()
        self.canvas_inst.flush_events()

    def plot_instrument(self, res):
        if len(res) == 5:
            self.cb_inst, self.cb_inst_alt = plot_instrument(self.fig_inst, self.ax_inst, self.cb_inst,
                                                             self.cb_inst_alt, *res)
        elif len(res) == 8:
            self.cb_inst, self.cb_inst_alt = plot_instrument_alternate(self.fig_inst, self.ax_inst, self.cb_inst,
                                                                       self.cb_inst_alt, *res)
        self.fig_inst.canvas.mpl_connect(
            "button_press_event", self.on_press_inst
        )
        self.canvas_inst.draw_idle()
        self.canvas_inst.flush_events()

    def plot_instrument_alternate(self, res):
        gamma_inst, nu_inst, gamma_1, nu_1, lamda_1, gamma_2, nu_2, lamda_2 = res
        plot_instrument_alternate(self.fig_inst, self.ax_inst, gamma_inst, nu_inst, gamma_1, nu_1, lamda_1, gamma_2,
                                  nu_2, lamda_2)
        self.fig_inst.canvas.mpl_connect(
            "button_press_event", self.on_press_inst
        )
        self.canvas_inst.draw_idle()
        self.canvas_inst.flush_events()

    def on_press_inst(self, event):
        if (
                event.inaxes == self.ax_inst
                and self.fig_inst.canvas.toolbar.mode == ""
        ):
            horz, vert = event.xdata, event.ydata
            self.view_model.process_peak_plot_event(horz, vert)


class EPPeakTab(QWidget):
    def __init__(self, view_model: ExperimentPlannerViewModel, parent=None):
        super().__init__(parent)

        self.view_model = view_model
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.create_ui(layout)

    def create_ui(self, layout):
        calculator = EPCalculator(self.view_model)

        layout.addWidget(calculator)

        canvas = EPCanvas(self.view_model)
        layout.addWidget(canvas)

        peak_table = EPPeakTable(self.view_model)
        layout.addWidget(peak_table)
