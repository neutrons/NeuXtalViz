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

from NeuXtalViz.view_models.experiment_planner import ExperimentPlannerViewModel

class EPPeakTab(QWidget):
    def __init__(self, view_model: ExperimentPlannerViewModel, parent=None):
        super().__init__(parent)

        self.view_model = view_model
        layout = QVBoxLayout()
        self.setLayout(layout)



