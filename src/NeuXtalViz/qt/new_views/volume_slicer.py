from functools import partial

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QFrame
from pyvistaqt import QtInteractor
from qtpy.QtCore import Qt
from qtpy.QtGui import QDoubleValidator
from qtpy.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QTabWidget,
    QComboBox,
    QLineEdit,
    QSlider,
    QFileDialog,
    QCheckBox,
)

import numpy as np
import pyvista as pv

from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
from matplotlib.figure import Figure
from matplotlib.transforms import Affine2D

from NeuXtalViz.components.visualization_panel.view_qt import VisPanelWidget
from NeuXtalViz.config import colormap
from NeuXtalViz.views.shared.volume_slicer import VolumeSlicerPlotter
from NeuXtalViz.view_models.volume_slicer import (
    CutControls,
    SliceControls,
    VolumeSlicerViewModel,
)

colormap.add_modified()

cmaps = {
    "Sequential": "viridis",
    "Binary": "binary",
    "Diverging": "bwr",
    "Rainbow": "turbo",
    "Modified": "modified",
}

opacities = {
    "Linear": {"Low->High": "linear", "High->Low": "linear_r"},
    "Geometric": {"Low->High": "geom", "High->Low": "geom_r"},
    "Sigmoid": {"Low->High": "sigmoid", "High->Low": "sigmoid_r"},
}


class VolumeSlicerView(QWidget):
    def __init__(self, view_model: VolumeSlicerViewModel, parent=None):
        super().__init__(parent)

        self.view_model = view_model
        layout = QHBoxLayout()
        self.frame = QFrame()  # need to store as object variable
        plotter = QtInteractor(self.frame)
        self.vis_widget = VisPanelWidget("vs", plotter, view_model.model, parent)
        self.view_model.set_vis_viewmodel(self.vis_widget.view_model)

        self.canvas_slice = FigureCanvas(Figure(constrained_layout=True))
        self.canvas_cut = FigureCanvas(
            Figure(constrained_layout=True, figsize=(6.4, 3.2))
        )
        self.fig_slice = self.canvas_slice.figure
        self.fig_cut = self.canvas_cut.figure

        self.plotter = VolumeSlicerPlotter(
            self.view_model,
            plotter,
            self.fig_slice,
            self.update_slice,
            self.fig_cut,
            self.update_cut,
        )

        layout.addWidget(self.vis_widget)
        self.tab_widget = QTabWidget(self)
        self.slicer_tab()
        layout.addWidget(self.tab_widget, stretch=1)
        self.setLayout(layout)

        self.connect_bindings()
        self.connect_widgets()

    def slicer_tab(self):
        slice_tab = QWidget()
        self.tab_widget.addTab(slice_tab, "Slicer")

        notation = QDoubleValidator.StandardNotation

        validator = QDoubleValidator(-100, 100, 5, notation=notation)

        self.container = QWidget()
        self.container.setVisible(False)

        plots_layout = QVBoxLayout()
        slice_params_layout = QHBoxLayout()
        view_params_layout = QHBoxLayout()
        collabsible_layout = QVBoxLayout(self.container)
        cut_params_layout = QHBoxLayout()
        draw_layout = QHBoxLayout()

        self.vol_scale_combo = QComboBox(self)
        self.vol_scale_combo.addItem("Linear")
        self.vol_scale_combo.addItem("Log")
        self.vol_scale_combo.setCurrentIndex(0)

        self.opacity_combo = QComboBox(self)
        self.opacity_combo.addItem("Linear")
        self.opacity_combo.addItem("Geometric")
        self.opacity_combo.addItem("Sigmoid")
        self.opacity_combo.setCurrentIndex(0)

        self.range_combo = QComboBox(self)
        self.range_combo.addItem("Low->High")
        self.range_combo.addItem("High->Low")
        self.range_combo.setCurrentIndex(0)

        self.clim_combo = QComboBox(self)
        self.clim_combo.addItem("Min/Max")
        self.clim_combo.addItem("μ±3×σ")
        self.clim_combo.addItem("Q₃/Q₁±1.5×IQR")
        self.clim_combo.setCurrentIndex(2)

        self.vlim_combo = QComboBox(self)
        self.vlim_combo.addItem("Min/Max")
        self.vlim_combo.addItem("μ±3×σ")
        self.vlim_combo.addItem("Q₃/Q₁±1.5×IQR")
        self.vlim_combo.setCurrentIndex(2)

        self.cbar_combo = QComboBox(self)
        self.cbar_combo.addItem("Sequential")
        self.cbar_combo.addItem("Rainbow")
        self.cbar_combo.addItem("Binary")
        self.cbar_combo.addItem("Diverging")
        self.cbar_combo.addItem("Modified")

        self.load_NXS_button = QPushButton("Load NXS", self)

        draw_layout.addWidget(self.vol_scale_combo)
        draw_layout.addWidget(self.opacity_combo)
        draw_layout.addWidget(self.range_combo)
        draw_layout.addWidget(self.clim_combo)
        draw_layout.addWidget(self.cbar_combo)
        draw_layout.addWidget(self.load_NXS_button)

        self.slice_combo = QComboBox(self)
        self.slice_combo.addItem("Axis 1/2")
        self.slice_combo.addItem("Axis 1/3")
        self.slice_combo.addItem("Axis 2/3")
        self.slice_combo.setCurrentIndex(0)

        self.cut_combo = QComboBox(self)
        self.cut_combo.addItem("Axis 1")
        self.cut_combo.addItem("Axis 2")
        self.cut_combo.setCurrentIndex(0)

        slice_label = QLabel("Slice:", self)
        cut_label = QLabel("Cut:", self)

        self.slice_line = QLineEdit("0.0")
        self.slice_line.setValidator(validator)

        self.cut_line = QLineEdit("0.0")
        self.cut_line.setValidator(validator)

        validator = QDoubleValidator(0.0001, 100, 5, notation=notation)

        slice_thickness_label = QLabel("Thickness:", self)
        cut_thickness_label = QLabel("Thickness:", self)

        self.slice_thickness_line = QLineEdit("0.1")
        self.cut_thickness_line = QLineEdit("0.5")

        self.slice_thickness_line.setValidator(validator)
        self.cut_thickness_line.setValidator(validator)

        self.slice_scale_combo = QComboBox(self)
        self.slice_scale_combo.addItem("Linear")
        self.slice_scale_combo.addItem("Log")

        self.cut_scale_combo = QComboBox(self)
        self.cut_scale_combo.addItem("Linear")
        self.cut_scale_combo.addItem("Log")

        slider_layout = QVBoxLayout()
        bar_layout = QHBoxLayout()

        self.min_slider = QSlider(Qt.Vertical)
        self.max_slider = QSlider(Qt.Vertical)

        self.min_slider.setRange(0, 100)
        self.max_slider.setRange(0, 100)

        self.min_slider.setValue(0)
        self.max_slider.setValue(100)

        self.min_slider.setTracking(False)
        self.max_slider.setTracking(False)

        self.vmin_line = QLineEdit("")
        self.vmax_line = QLineEdit("")

        self.xmin_line = QLineEdit("")
        self.xmax_line = QLineEdit("")

        self.ymin_line = QLineEdit("")
        self.ymax_line = QLineEdit("")

        validator = QDoubleValidator(-1e32, 1e32, 6, notation=notation)

        self.vmin_line.setValidator(validator)
        self.vmax_line.setValidator(validator)

        self.xmin_line.setValidator(validator)
        self.xmax_line.setValidator(validator)

        self.ymin_line.setValidator(validator)
        self.ymax_line.setValidator(validator)

        xmin_label = QLabel("X Min:", self)
        xmax_label = QLabel("X Max:", self)

        ymin_label = QLabel("Y Min:", self)
        ymax_label = QLabel("Y Max:", self)

        vmin_label = QLabel("Min:", self)
        vmax_label = QLabel("Max:", self)

        bar_layout.addWidget(self.min_slider)
        bar_layout.addWidget(self.max_slider)

        self.save_slice_button = QPushButton("Save Slice", self)
        self.save_cut_button = QPushButton("Save Cut", self)

        self.toggle_line_box = QCheckBox("Show Line Cut")
        self.toggle_line_box.setChecked(False)

        slider_layout.addLayout(bar_layout)

        slice_params_layout.addWidget(self.slice_combo)
        slice_params_layout.addWidget(slice_label)
        slice_params_layout.addWidget(self.slice_line)
        slice_params_layout.addWidget(slice_thickness_label)
        slice_params_layout.addWidget(self.slice_thickness_line)
        slice_params_layout.addWidget(self.toggle_line_box)
        slice_params_layout.addStretch(1)
        slice_params_layout.addWidget(self.save_slice_button)
        slice_params_layout.addWidget(self.slice_scale_combo)

        view_params_layout.addWidget(xmin_label)
        view_params_layout.addWidget(self.xmin_line)
        view_params_layout.addWidget(xmax_label)
        view_params_layout.addWidget(self.xmax_line)
        view_params_layout.addWidget(ymin_label)
        view_params_layout.addWidget(self.ymin_line)
        view_params_layout.addWidget(ymax_label)
        view_params_layout.addWidget(self.ymax_line)
        view_params_layout.addStretch(1)
        view_params_layout.addWidget(self.vlim_combo)
        view_params_layout.addWidget(vmin_label)
        view_params_layout.addWidget(self.vmin_line)
        view_params_layout.addWidget(vmax_label)
        view_params_layout.addWidget(self.vmax_line)

        cut_params_layout.addWidget(self.cut_combo)
        cut_params_layout.addWidget(cut_label)
        cut_params_layout.addWidget(self.cut_line)
        cut_params_layout.addWidget(cut_thickness_label)
        cut_params_layout.addWidget(self.cut_thickness_line)
        cut_params_layout.addStretch(1)
        cut_params_layout.addWidget(self.save_cut_button)
        cut_params_layout.addWidget(self.cut_scale_combo)

        plots_layout.addLayout(draw_layout)

        image_layout = QHBoxLayout()
        line_layout = QHBoxLayout()

        fig_2d_layout = QVBoxLayout()
        fig_1d_layout = QVBoxLayout()

        fig_2d_layout.addWidget(NavigationToolbar2QT(self.canvas_slice, self))
        fig_2d_layout.addWidget(self.canvas_slice)

        fig_1d_layout.addWidget(NavigationToolbar2QT(self.canvas_cut, self))
        fig_1d_layout.addWidget(self.canvas_cut)

        image_layout.addLayout(fig_2d_layout)
        image_layout.addLayout(slider_layout)

        line_layout.addLayout(fig_1d_layout)

        plots_layout.addLayout(image_layout)
        plots_layout.addLayout(slice_params_layout)
        plots_layout.addLayout(view_params_layout)

        collabsible_layout.addLayout(line_layout)
        collabsible_layout.addLayout(cut_params_layout)

        plots_layout.addWidget(self.container)

        slice_tab.setLayout(plots_layout)

        self.toggle_line_box.toggled.connect(
            lambda state: self.view_model.set_cut_field("show", state)
        )

    def connect_bindings(self):
        self.view_model.volume_bind.connect("vs_volume", lambda *args: None)
        self.view_model.slice_bind.connect("vs_slice", self.on_slice_update)
        self.view_model.cut_bind.connect("vs_cut", self.on_cut_update)

        self.view_model.add_histo_bind.connect("vs_add_histo", self.plotter.add_histo)
        self.view_model.add_slice_bind.connect("vs_add_slice", self.plotter.add_slice)
        self.view_model.add_cut_bind.connect("vs_add_cut", self.plotter.add_cut)
        self.view_model.colorbar_lim_bind.connect(
            "vs_colorbar_lim", self.plotter.update_colorbar_vlims
        )
        self.view_model.slice_lim_bind.connect(
            "vs_slice_lim", self.plotter.set_slice_lim
        )
        self.view_model.cut_lim_bind.connect("vs_cut_lim", self.plotter.set_cut_lim)

    def connect_widgets(self):
        # Volume controls
        self.clim_combo.currentTextChanged.connect(
            lambda: self.view_model.set_volume_field(
                "clip_type", self.clim_combo.currentText()
            )
        )
        self.cbar_combo.currentTextChanged.connect(
            lambda: self.view_model.set_volume_field(
                "cbar", self.cbar_combo.currentText()
            )
        )
        self.load_NXS_button.clicked.connect(self.load_NXS)
        self.opacity_combo.currentTextChanged.connect(
            lambda: self.view_model.set_volume_field(
                "opacity", self.opacity_combo.currentText()
            )
        )
        self.range_combo.currentTextChanged.connect(
            lambda: self.view_model.set_volume_field(
                "opacity_range", self.range_combo.currentText()
            )
        )
        self.vol_scale_combo.currentTextChanged.connect(
            lambda: self.view_model.set_volume_field(
                "scale", self.vol_scale_combo.currentText()
            )
        )

        # Slice controls
        self.save_slice_button.clicked.connect(self.save_slice)
        self.slice_combo.currentTextChanged.connect(
            lambda: self.view_model.set_slice_field(
                "plane", self.slice_combo.currentText()
            )
        )
        self.slice_line.editingFinished.connect(
            lambda: self.view_model.set_slice_field("value", self.slice_line.text())
        )
        self.slice_scale_combo.currentTextChanged.connect(
            lambda: self.view_model.set_slice_field(
                "scale", self.slice_scale_combo.currentText()
            )
        )
        self.slice_thickness_line.editingFinished.connect(
            lambda: self.view_model.set_slice_field(
                "thickness", self.slice_thickness_line.text()
            )
        )
        self.vlim_combo.currentTextChanged.connect(
            lambda: self.view_model.set_slice_field(
                "clip_type", self.vlim_combo.currentText()
            )
        )
        self.min_slider.valueChanged.connect(
            lambda: self.view_model.set_slice_field(
                "vmin_slider", self.min_slider.value()
            )
        )
        self.max_slider.valueChanged.connect(
            lambda: self.view_model.set_slice_field(
                "vmax_slider", self.max_slider.value()
            )
        )
        self.vmin_line.editingFinished.connect(
            lambda: self.view_model.set_slice_field("vmin", self.vmin_line.text())
        )
        self.vmax_line.editingFinished.connect(
            lambda: self.view_model.set_slice_field("vmax", self.vmax_line.text())
        )
        self.xmin_line.editingFinished.connect(
            lambda: self.view_model.set_slice_field("xmin", self.xmin_line.text())
        )
        self.xmax_line.editingFinished.connect(
            lambda: self.view_model.set_slice_field("xmax", self.xmax_line.text())
        )
        self.ymin_line.editingFinished.connect(
            lambda: self.view_model.set_slice_field("ymin", self.ymin_line.text())
        )
        self.ymax_line.editingFinished.connect(
            lambda: self.view_model.set_slice_field("ymax", self.ymax_line.text())
        )

        # Cut controls
        self.cut_combo.currentTextChanged.connect(
            lambda: self.view_model.set_cut_field("line", self.cut_combo.currentText())
        )
        self.cut_line.textChanged.connect(
            lambda: self.view_model.set_cut_field("value", self.cut_line.text())
        )
        self.cut_line.editingFinished.connect(lambda: self.view_model.update_cut())
        self.cut_scale_combo.currentTextChanged.connect(
            lambda: self.view_model.set_cut_field(
                "scale", self.cut_scale_combo.currentText()
            )
        )
        self.cut_thickness_line.editingFinished.connect(
            lambda: self.view_model.set_cut_field(
                "thickness", self.cut_thickness_line.text()
            )
        )
        self.save_cut_button.clicked.connect(self.save_cut)

    def load_NXS(self):
        filename = self.load_NXS_file_dialog()

        if filename:
            self.view_model.load_NXS(filename)

    def load_NXS_file_dialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog

        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.AnyFile)

        filename, _ = file_dialog.getOpenFileName(
            self, "Load NXS file", "", "NXS files (*.nxs)", options=options
        )

        return filename

    def on_slice_update(self, slice: SliceControls):
        self.slice_line.setText("{:.5f}".format(slice.value))
        self.slice_thickness_line.setText("{:.5f}".format(slice.thickness))

        self.set_sliders(slice.vmin_slider, slice.vmax_slider)

        self.vmax_line.setText("{:.5f}".format(slice.vmax))
        self.vmin_line.setText("{:.5f}".format(slice.vmin))
        self.xmax_line.setText("{:.4f}".format(slice.xmax))
        self.xmin_line.setText("{:.4f}".format(slice.xmin))
        self.ymax_line.setText("{:.4f}".format(slice.ymax))
        self.ymin_line.setText("{:.4f}".format(slice.ymin))

    def on_cut_update(self, cut: CutControls):
        self.container.setVisible(cut.show)
        self.plotter.update_lines(cut.show)
        self.cut_line.setText("{:.5f}".format(cut.value))
        self.cut_thickness_line.setText("{:.5f}".format(cut.thickness))

    def save_slice(self):
        filename = self.save_file_dialog()
        if filename:
            self.view_model.save_slice(filename)

    def save_cut(self):
        filename = self.save_file_dialog()
        if filename:
            self.view_model.save_cut(filename)

    def save_file_dialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog

        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.AnyFile)

        filename, _ = file_dialog.getSaveFileName(
            self, "Save csv file", "", "CSV files (*.csv)", options=options
        )

        return filename

    def set_sliders(self, min, max):
        self.min_slider.blockSignals(True)
        self.max_slider.blockSignals(True)
        self.min_slider.setValue(min)
        self.max_slider.setValue(max)
        self.min_slider.blockSignals(False)
        self.max_slider.blockSignals(False)

    def update_cut(self):
        self.canvas_cut.draw_idle()
        self.canvas_cut.flush_events()

    def update_slice(self):
        self.canvas_slice.draw_idle()
        self.canvas_slice.flush_events()
