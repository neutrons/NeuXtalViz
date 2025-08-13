import time
from enum import Enum
from typing import List, Tuple, Dict, Any, Optional

import numpy as np
from pydantic import BaseModel, Field, field_validator, computed_field

from NeuXtalViz.view_models.base_view_model import NeuXtalVizViewModel

class EPInstrumentOptions(str, Enum):
    topaz = "TOPAZ"
    mandi = "MANDI"
    corelli = "CORELLI"
    snap = "SNAP"
    wand2 = "WAND²"
    demand = "DEMAND"

class CrystalSystemOptions(str, Enum):
    triclinic = "Triclinic"
    monoclinic = "Monoclinic"
    orthorhombic = "Orthorhombic"
    tetragonal = "Tetragonal"
    trigonal = "Trigonal"
    hexagonal = "Hexagonal"
    cubic = "Cubic"


class EPSettings(BaseModel):
    instrument: EPInstrumentOptions = Field(default=EPInstrumentOptions.topaz, title="Instrument")
    crystal_system: CrystalSystemOptions = Field(
        default=CrystalSystemOptions.triclinic, title="Crystal System"
    )
    point_group: Optional[str]  = Field(default=None, title="Point Group")
    lattice_centering: Optional[str] = Field(default=None, title="Lattice Centering")

class EPParams(BaseModel):
    wl_min: float = Field(default=0.4, title="Wl(min)", ge=0.2, le=10)
    wl_max: float = Field(default=3.5, title="Wl(max)", ge=0.2, le=10)
    d_min: float = Field(default=0.7, title="d(min)", ge=0.4, le=10)


class ExperimentPlannerViewModel:
    def __init__(self, model, binding):
        self.model = model
        self.vis_viewmodel = None
        self.binding = binding

    def set_vis_viewmodel(self, vis_viewmodel: NeuXtalVizViewModel):
        self.vis_viewmodel = vis_viewmodel
