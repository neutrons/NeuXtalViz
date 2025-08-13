from PyQt5.QtWidgets import QFrame
from pyvistaqt import QtInteractor
from qtpy.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QTabWidget,
)

from NeuXtalViz.components.visualization_panel.view_qt import VisPanelWidget
from NeuXtalViz.qt.new_views.ep_coverage_tab import EPCoverageTab
from NeuXtalViz.qt.new_views.ep_peak_tab import EPPeakTab
from NeuXtalViz.view_models.experiment_planner import ExperimentPlannerViewModel
from NeuXtalViz.views.shared.base_plotter import BasePlotter


class ExperimentPlannerView(QWidget):
    def __init__(self, view_model: ExperimentPlannerViewModel, parent=None):
        super().__init__(parent)

        self.view_model = view_model
        layout = QHBoxLayout()
        self.frame = QFrame()
        plotter = QtInteractor(self.frame)
        self.vis_widget = VisPanelWidget("ep", plotter, view_model.model, parent)
        self.view_model.set_vis_viewmodel(self.vis_widget.view_model)
        self.plotter = BasePlotter(plotter)

        layout.addWidget(self.vis_widget)

        self.tab_widget = QTabWidget(self)

        cov_tab = EPCoverageTab(self.view_model)
        self.tab_widget.addTab(cov_tab, "Coverage")

        peak_tab = EPPeakTab(self.view_model)
        self.tab_widget.addTab(peak_tab, "Peak")

        layout.addWidget(self.tab_widget, stretch=1)

        self.setLayout(layout)
