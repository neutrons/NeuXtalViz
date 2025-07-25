"""Main view for NeuXtalViz."""

from nova.mvvm.trame_binding import TrameBinding
from nova.trame import ThemedApp
from trame.widgets import vuetify3 as vuetify
from trame_server.core import Server
from trame_server.state import State

from NeuXtalViz.models.crystal_structure_tools import CrystalStructureModel
from NeuXtalViz.models.volume_slicer import VolumeSlicerModel
from NeuXtalViz.trame.views.crystal_structure import CrystalStructureView
from NeuXtalViz.trame.views.volume_slicer import VolumeSlicerView
from NeuXtalViz.view_models.crystal_structure_tools import CrystalStructureViewModel
from NeuXtalViz.view_models.volume_slicer import VolumeSlicerViewModel


class NeuXtalViz(ThemedApp):
    """Main view for NeuXtalViz."""

    def __init__(self, server: Server = None) -> None:
        self.server = server
        super().__init__(server=server)

        binding = TrameBinding(self.server.state)

        self.crystal_structure_view_model = CrystalStructureViewModel(
            CrystalStructureModel(), binding
        )
        self.volume_slicer_view_model = VolumeSlicerViewModel(
            VolumeSlicerModel(), binding
        )

        self.create_ui()

    @property
    def state(self) -> State:
        return self.server.state

    def create_ui(self) -> None:
        self.state.trame__title = "NeuXtalViz"
        self.set_theme("CompactTheme")
        self.state.active_app = 0
        with super().create_ui() as layout:
            layout.toolbar_title.set_text("NeuXtalViz")

            with layout.pre_content:
                with vuetify.VTabs(v_model="active_app", classes="pl-6"):
                    vuetify.VTab("Crystal Structure", value=0)
                    vuetify.VTab("Volume Slicer", value=1)
            with layout.content:
                with vuetify.VWindow(v_model="active_app"):
                    with vuetify.VWindowItem(value=0):
                        CrystalStructureView(
                            self.server, self.crystal_structure_view_model
                        )
                    with vuetify.VWindowItem(value=1):
                        VolumeSlicerView(self.server, self.volume_slicer_view_model)
