"""Main view for NeuXtalViz."""

from nova.mvvm.trame_binding import TrameBinding
from nova.trame import ThemedApp
from nova.trame.view.layouts import VBoxLayout
from pydantic import BaseModel, Field
from trame.widgets import client
from trame.widgets import vuetify3 as vuetify
from trame_server.core import Server
from trame_server.state import State

from NeuXtalViz.models.crystal_structure_tools import CrystalStructureModel
from NeuXtalViz.models.experiment_planner import ExperimentModel
from NeuXtalViz.models.sample_tools import SampleModel

from NeuXtalViz.models.volume_slicer import VolumeSlicerModel
from NeuXtalViz.models.ub_tools import UBModel
from NeuXtalViz.trame.views.crystal_structure import CrystalStructureView
from NeuXtalViz.trame.views.experiment_planner import ExperimentPlannerView
from NeuXtalViz.trame.views.sample_tools import SampleView
from NeuXtalViz.trame.views.volume_slicer import VolumeSlicerView
from NeuXtalViz.trame.views.ub_tools import UBView
from NeuXtalViz.view_models.crystal_structure_tools import CrystalStructureViewModel
from NeuXtalViz.view_models.experiment_planner import ExperimentPlannerViewModel
from NeuXtalViz.view_models.main_view_model import MainViewModel
from NeuXtalViz.view_models.sample_tools import SampleViewModel
from NeuXtalViz.view_models.volume_slicer import VolumeSlicerViewModel
from NeuXtalViz.view_models.ub_tools import UBViewModel


class NeuXtalViz(ThemedApp):
    """Main view for NeuXtalViz."""

    def __init__(self, server: Server = None) -> None:
        self.server = server
        super().__init__(server=server)

        binding = TrameBinding(self.server.state)

        self.main_view_model = MainViewModel(binding)
        self.main_view_model.view_state_bind.connect("view_state")

        self.crystal_structure_view_model = CrystalStructureViewModel(
            CrystalStructureModel(), binding
        )
        self.sample_view_model = SampleViewModel(SampleModel(), binding)
        self.volume_slicer_view_model = VolumeSlicerViewModel(
            VolumeSlicerModel(), binding
        )
        self.ub_view_model = UBViewModel(UBModel(), binding)
        self.planner_view_model = ExperimentPlannerViewModel(ExperimentModel(), binding)

        self.create_ui()

    @property
    def state(self) -> State:
        return self.server.state

    def create_ui(self) -> None:
        self.state.trame__title = "NeuXtalViz"
        self.set_theme("CompactTheme")
        with super().create_ui() as layout:
            layout.toolbar_title.set_text("NeuXtalViz")

            with layout.pre_content:
                with client.DeepReactive("view_state"):
                    with vuetify.VTabs(v_model="view_state.active_app", classes="pl-6"):
                        vuetify.VTab("Crystal Structure", value=1)
                        vuetify.VTab("Sample", value=2)
                        vuetify.VTab("Volume Slicer", value=3)
                        vuetify.VTab("UB", value=4)
                        vuetify.VTab("Planner", value=5)

            with layout.content:
                with VBoxLayout(v_show="view_state.active_app == 1", stretch=True):
                    CrystalStructureView(self.server, self.crystal_structure_view_model)
                with VBoxLayout(v_show="view_state.active_app == 2", stretch=True):
                    SampleView(self.server, self.sample_view_model)
                with VBoxLayout(v_show="view_state.active_app == 3", stretch=True):
                    VolumeSlicerView(self.server, self.volume_slicer_view_model)
                with VBoxLayout(v_show="view_state.active_app == 4", stretch=True):
                    UBView(self.server, self.ub_view_model)
                with VBoxLayout(v_show="view_state.active_app == 5", stretch=True):
                    ExperimentPlannerView(self.server, self.planner_view_model)
