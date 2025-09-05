import re
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from nova.mvvm.interface import BindingInterface  # type: ignore
from pydantic import BaseModel, Field, computed_field, model_validator
from typing_extensions import Self

from NeuXtalViz.models.ub_tools import UBModel
from NeuXtalViz.shared.types import (
    FloatWithPrecision2,
    FloatWithPrecision3,
    FloatWithPrecision4,
    FloatWithPrecision5,
    FloatWithPrecision6,
)
from NeuXtalViz.components.visualization_panel.view_model import VizViewModel
from NeuXtalViz.shared.utilities import slider_to_value
from NeuXtalViz.view_models.volume_slicer import (
    AxisOptions,
    CMAPS,
    ClipTypeOptions,
    ColorbarOptions,
    SlicePlaneOptions,
)


class CenteringOptions(str, Enum):
    P = "P"
    I = "I"  # noqa
    F = "F"
    Robv = "Robv"
    Rrev = "Rrev"
    A = "A"
    B = "B"
    C = "C"
    H = "H"


class ComparisonOptions(str, Enum):
    gt = ">"
    lt = "<"
    ge = ">="
    le = "<="
    equal = "="
    not_equal = "!="


class FilterOptions(str, Enum):
    i_sigma = "I/σ"
    d = "d"
    _lambda = "λ"
    Q = "Q"
    hkl = "h^2+k^2+l^2"
    mnp = "m^2+n^2+p^2"
    run = "Run #"


class InstrumentOptions(str, Enum):
    CORELLI = "CORELLI"
    DEMAND = "DEMAND"
    MANDI = "MANDI"
    SNAP = "SNAP"
    TOPAZ = "TOPAZ"
    WAND2 = "WAND²"


class LatticeOptions(str, Enum):
    triclinic = "Triclinic"
    monoclinic = "Monoclinic"
    orthorhombic = "Orthorhombic"
    tetragonal = "Tetragonal"
    rhombehedral = "Rhombohedral"
    hexagonal = "Hexagonal"
    cubic = "Cubic"


class OptimizeOptions(str, Enum):
    unconstrained = "Unconstrained"
    constrained = "Constrained"
    triclinic = "Triclinic"
    monoclinic = "Monoclinic"
    orthorhombic = "Orthorhombic"
    tetragonal = "Tetragonal"
    rhombohedral = "Rhombohedral"
    hexagonal = "Hexagonal"
    cubic = "Cubic"


class FindPeaks(BaseModel):
    avoid_aluminum: bool = Field(default=True, title="Avoid Aluminum")
    edge_pixels: int = Field(default=0, ge=0, le=64, title="Edge Pixels")
    max_peaks: int = Field(default=100, ge=10, le=1000, title="Max Peaks")
    max_spacing: FloatWithPrecision4 = Field(
        default=31.46, ge=0.1, le=100, title="Max Spacing (Å)"
    )
    min_density: int = Field(default=100, ge=1, le=100000, title="Min Density")
    min_distance: FloatWithPrecision4 = Field(
        default=0.2, ge=0.01, le=10.0, title="Min Distance (Å⁻¹)"
    )


class IndexPeaks(BaseModel):
    satellite_tolerance: FloatWithPrecision5 = Field(
        default=0.1, ge=0.01, le=1.0, title="Satellite Tolerance"
    )
    round_hkl: bool = Field(default=True, title="Round hkl")
    satellite: bool = Field(default=False, title="Satellite")
    tolerance: FloatWithPrecision5 = Field(
        default=0.1, ge=0.01, le=1.0, title="Tolerance"
    )


class PredictPeaks(BaseModel):
    centering: CenteringOptions = Field(default=CenteringOptions.P, title="Centering")
    edge_pixels: int = Field(default=0, ge=0, le=64, title="Edge Pixels")
    min_d_spacing: FloatWithPrecision3 = Field(
        default=0.7, ge=0.4, le=100.0, title="Min d-spacing (Å)"
    )
    satellite: bool = Field(default=False, title="Satellite")
    satellite_min_d_spacing: FloatWithPrecision3 = Field(
        default=1.0, ge=0.4, le=100.0, title="Satellite Min d-spacing (Å)"
    )


class IntegratePeaks(BaseModel):
    adaptive_envelope: bool = Field(default=True, title="Adaptive Envelope")
    centroid: bool = Field(default=True, title="Centroid")
    inner_factor: FloatWithPrecision3 = Field(
        default=1.5, ge=1.0, le=3.0, title="Inner Factor"
    )
    outer_factor: FloatWithPrecision3 = Field(
        default=2.0, ge=1.0, le=3.0, title="Outer Factor"
    )
    radius: FloatWithPrecision3 = Field(
        default=0.25, ge=0.0, le=1.0, title="Radius (Å⁻¹)"
    )


class FilterPeaks(BaseModel):
    comparison: ComparisonOptions = Field(
        default=ComparisonOptions.gt, title="Comparison"
    )
    filter: FilterOptions = Field(default=FilterOptions.i_sigma, title="Filter")
    value: FloatWithPrecision3 = Field(default=0.0, ge=-1e6, le=1e6, title="Value")


class PeaksControls(BaseModel):
    find: FindPeaks = FindPeaks()
    index: IndexPeaks = IndexPeaks()
    predict: PredictPeaks = PredictPeaks()
    integrate: IntegratePeaks = IntegratePeaks()
    filter: FilterPeaks = FilterPeaks()
    peaks_path: str = Field(default="")


class QConversion(BaseModel):
    d_min: FloatWithPrecision5 = Field(default=0.7, ge=0.2, le=10.0, title="d(min)")
    detector_calibration: str = Field(default="", title="Detector Calibration")
    detector_disabled: bool = Field(default=False)
    experiment_disabled: bool = Field(default=True)
    experiment_number: Optional[int] = Field(
        default=None, ge=1, le=1000000000, title="Experiment Number"
    )
    instrument: InstrumentOptions = Field(
        default=InstrumentOptions.TOPAZ, title="Instrument"
    )
    ipts_disabled: bool = Field(default=False)
    ipts_number: Optional[int] = Field(
        default=None, ge=1, le=1000000000, title="IPTS Number"
    )
    lorentz_correction: bool = Field(default=True, title="Lorentz Correction")
    runs: List[int] = Field(default=[], title="Runs")
    time_stop: Optional[int] = Field(default=None, ge=1, le=1000, title="Time Stop (s)")
    time_stop_disabled: bool = Field(default=False)
    tube_calibration: str = Field(default="", title="Tube Calibration")
    tube_disabled: bool = Field(default=True)
    wl_max: FloatWithPrecision5 = Field(default=3.5, ge=0.2, le=10.0, title="λ(max)")
    wl_max_disabled: bool = Field(default=False)
    wl_min: FloatWithPrecision5 = Field(default=0.4, ge=0.2, le=10.0, title="λ(min)")
    ub_path: str = Field(default="")


class CalculateUB(BaseModel):
    tolerance: FloatWithPrecision5 = Field(
        default=0.1, ge=0.01, le=1.0, title="Tolerance"
    )
    max_scalar_error: FloatWithPrecision5 = Field(
        default=0.2, ge=0.01, le=1.0, title="Max Scalar Error"
    )
    min_const: FloatWithPrecision4 = Field(
        default=5.0, ge=0.1, le=1000.0, title="Min(a,b,c) [Å]"
    )
    max_const: FloatWithPrecision4 = Field(
        default=15.0, ge=0.1, le=1000.0, title="Max(a,b,c) [Å]"
    )
    form: str = Field(default="", title="Form")
    table_headers: List[Dict[str, str]] = [
        {"align": "center", "key": "form", "title": "Form"},
        {"align": "center", "key": "error", "title": "Error"},
        {"align": "center", "key": "bravais", "title": "Bravais"},
        {"align": "center", "key": "a", "title": "a"},
        {"align": "center", "key": "b", "title": "b"},
        {"align": "center", "key": "c", "title": "c"},
        {"align": "center", "key": "alpha", "title": "α"},
        {"align": "center", "key": "beta", "title": "β"},
        {"align": "center", "key": "gamma", "title": "γ"},
        {"align": "center", "key": "V", "title": "V"},
    ]
    table_contents: List[Any] = Field(default=[])
    selected_index: List[int] = Field(default=[])


class TransformUB(BaseModel):
    t11: FloatWithPrecision5 = Field(default=1, ge=-10.0, le=10.0)
    t12: FloatWithPrecision5 = Field(default=0, ge=-10.0, le=10.0)
    t13: FloatWithPrecision5 = Field(default=0, ge=-10.0, le=10.0)
    t21: FloatWithPrecision5 = Field(default=0, ge=-10.0, le=10.0)
    t22: FloatWithPrecision5 = Field(default=1, ge=-10.0, le=10.0)
    t23: FloatWithPrecision5 = Field(default=0, ge=-10.0, le=10.0)
    t31: FloatWithPrecision5 = Field(default=0, ge=-10.0, le=10.0)
    t32: FloatWithPrecision5 = Field(default=0, ge=-10.0, le=10.0)
    t33: FloatWithPrecision5 = Field(default=1, ge=-10.0, le=10.0)
    tolerance: FloatWithPrecision5 = Field(
        default=0.1, ge=0.01, le=1.0, title="Tolerance"
    )
    lattice: LatticeOptions = Field(default=LatticeOptions.triclinic)
    symmetry: str = Field(default="x,y,z")
    symmetry_options: List[str] = Field(default=["x,y,z", "-x,-y,-z"])

    @model_validator(mode="after")
    def validate_symmetry(self) -> Self:
        if self.symmetry not in self.symmetry_options:
            raise ValueError(
                f"""Invalid symmetry option. Must be one of: {",".join([f'"{option}"' for option in self.symmetry_options])}"""
            )

        return self


class RefineUB(BaseModel):
    tolerance: FloatWithPrecision5 = Field(
        default=0.1, ge=0.01, le=1.0, title="Tolerance"
    )
    optimize: OptimizeOptions = Field(
        default=OptimizeOptions.unconstrained, title="Optimize"
    )


class UBControls(BaseModel):
    calculate: CalculateUB = CalculateUB()
    transform: TransformUB = TransformUB()
    refine: RefineUB = RefineUB()
    ub_path: str = Field(default="")


class LatticeConstants(BaseModel):
    a: float = Field(default=0.0)
    a_error: float = Field(default=0.0)
    b: float = Field(default=0.0)
    b_error: float = Field(default=0.0)
    c: float = Field(default=0.0)
    c_error: float = Field(default=0.0)
    alpha: float = Field(default=0.0)
    alpha_error: float = Field(default=0.0)
    beta: float = Field(default=0.0)
    beta_error: float = Field(default=0.0)
    gamma: float = Field(default=0.0)
    gamma_error: float = Field(default=0.0)

    @computed_field  # type: ignore
    @property
    def a_display(self) -> str:
        return f"a: {self.format_with_error(self.a, self.a_error)}"

    @computed_field  # type: ignore
    @property
    def b_display(self) -> str:
        return f"b: {self.format_with_error(self.b, self.b_error)}"

    @computed_field  # type: ignore
    @property
    def c_display(self) -> str:
        return f"c: {self.format_with_error(self.c, self.c_error)}"

    @computed_field  # type: ignore
    @property
    def alpha_display(self) -> str:
        return f"α: {self.format_with_error(self.alpha, self.alpha_error)}"

    @computed_field  # type: ignore
    @property
    def beta_display(self) -> str:
        return f"β: {self.format_with_error(self.beta, self.beta_error)}"

    @computed_field  # type: ignore
    @property
    def gamma_display(self) -> str:
        return f"γ: {self.format_with_error(self.gamma, self.gamma_error)}"

    def as_list(self) -> List[float]:
        return [self.a, self.b, self.c, self.alpha, self.beta, self.gamma]

    def format_with_error(self, value, error):
        if error <= 0:
            return f"{value}"

        error_order = int(np.floor(np.log10(error)))

        decimal_places = max(0, -error_order)

        rounded_value = round(value, decimal_places)
        rounded_error = round(error, decimal_places)

        error_digits = int(round(rounded_error * (10**decimal_places)))

        formatted_str = f"{rounded_value:.{decimal_places}f}({error_digits})"
        return formatted_str


class ModulationParameters(BaseModel):
    dh1: FloatWithPrecision4 = Field(default=0.0, ge=-5.0, le=5.0)
    dk1: FloatWithPrecision4 = Field(default=0.0, ge=-5.0, le=5.0)
    dl1: FloatWithPrecision4 = Field(default=0.0, ge=-5.0, le=5.0)
    dh2: FloatWithPrecision4 = Field(default=0.0, ge=-5.0, le=5.0)
    dk2: FloatWithPrecision4 = Field(default=0.0, ge=-5.0, le=5.0)
    dl2: FloatWithPrecision4 = Field(default=0.0, ge=-5.0, le=5.0)
    dh3: FloatWithPrecision4 = Field(default=0.0, ge=-5.0, le=5.0)
    dk3: FloatWithPrecision4 = Field(default=0.0, ge=-5.0, le=5.0)
    dl3: FloatWithPrecision4 = Field(default=0.0, ge=-5.0, le=5.0)
    max_order: int = Field(default=0)
    cross_terms: bool = Field(default=False, title="Cross Terms")


class SampleDirections(BaseModel):
    uh: float = Field(default=0.0)
    uk: float = Field(default=0.0)
    ul: float = Field(default=0.0)
    vh: float = Field(default=0.0)
    vk: float = Field(default=0.0)
    vl: float = Field(default=0.0)
    wh: float = Field(default=0.0)
    wk: float = Field(default=0.0)
    wl: float = Field(default=0.0)


class Parameters(BaseModel):
    lattice: LatticeConstants = LatticeConstants()
    modulation: ModulationParameters = ModulationParameters()
    sample_directions: SampleDirections = SampleDirections()


class Peaks(BaseModel):
    h1: FloatWithPrecision5 = Field(default=0.0, ge=-100.0, le=100.0)
    k1: FloatWithPrecision5 = Field(default=0.0, ge=-100.0, le=100.0)
    l1: FloatWithPrecision5 = Field(default=0.0, ge=-100.0, le=100.0)
    h2: FloatWithPrecision5 = Field(default=0.0, ge=-100.0, le=100.0)
    k2: FloatWithPrecision5 = Field(default=0.0, ge=-100.0, le=100.0)
    l2: FloatWithPrecision5 = Field(default=0.0, ge=-100.0, le=100.0)
    d1: FloatWithPrecision4 = Field(default=0.0)
    d2: FloatWithPrecision4 = Field(default=0.0)
    phi: FloatWithPrecision4 = Field(default=0.0)
    peaks_headers: List[Dict[str, str]] = [
        {"align": "center", "key": "hkl[0]", "title": "h"},
        {"align": "center", "key": "hkl[1]", "title": "k"},
        {"align": "center", "key": "hkl[2]", "title": "l"},
        {"align": "center", "key": "d_spacing", "title": "d"},
        {"align": "center", "key": "wavelength", "title": "λ"},
        {"align": "center", "key": "itensity", "title": "I"},
        {"align": "center", "key": "sigma", "title": "I/σ"},
        {"align": "center", "key": "run_number", "title": "#"},
    ]
    peaks: List[Any] = Field(default=[])
    highlighted_peaks: List[int] = Field(default=[])
    last_highlight: int = Field(default=-1)
    position: List[float] = Field(default=[0.0, 0.0, 0.0])
    h: FloatWithPrecision3 = Field(default=0.0, ge=-100.0, le=100.0)
    k: FloatWithPrecision3 = Field(default=0.0, ge=-100.0, le=100.0)
    l: FloatWithPrecision3 = Field(default=0.0, ge=-100.0, le=100.0)  # noqa
    index: int = Field(default=0, title="Indexed")
    total: int = Field(default=0, title="Total")
    int_h: int = Field(default=0, title="h")
    int_k: int = Field(default=0, title="k")
    int_l: int = Field(default=0, title="l")
    int_m: int = Field(default=0, title="m")
    int_n: int = Field(default=0, title="n")
    int_p: int = Field(default=0, title="p")
    intensity: FloatWithPrecision2 = Field(default=0.0, title="I")
    sigma: FloatWithPrecision2 = Field(default=0.0, title="±σ")
    lambda_value: FloatWithPrecision4 = Field(default=0.0, title="λ[Å]")
    d: FloatWithPrecision4 = Field(default=0.0, title="d[Å]")
    run: str = Field(default="", title="Run #")
    bank: str = Field(default="", title="Bank #")
    row: str = Field(default="", title="Row #")
    col: str = Field(default="", title="Col #")

    def get_input_hkls(
        self,
    ) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
        return ((self.h1, self.k1, self.l1), (self.h2, self.k2, self.l2))


class SliceParameters(BaseModel):
    U1: FloatWithPrecision5 = Field(default=1.0, ge=-10.0, le=10.0)
    V1: FloatWithPrecision5 = Field(default=0.0, ge=-10.0, le=10.0)
    W1: FloatWithPrecision5 = Field(default=0.0, ge=-10.0, le=10.0)
    U2: FloatWithPrecision5 = Field(default=0.0, ge=-10.0, le=10.0)
    V2: FloatWithPrecision5 = Field(default=1.0, ge=-10.0, le=10.0)
    W2: FloatWithPrecision5 = Field(default=0.0, ge=-10.0, le=10.0)
    U3: FloatWithPrecision5 = Field(default=0.0, ge=-10.0, le=10.0)
    V3: FloatWithPrecision5 = Field(default=0.0, ge=-10.0, le=10.0)
    W3: FloatWithPrecision5 = Field(default=1.0, ge=-10.0, le=10.0)
    plane: SlicePlaneOptions = Field(default=SlicePlaneOptions.one_half, title="Plane")
    value: FloatWithPrecision5 = Field(default=0.0, ge=-10.0, le=10.0, title="Value")
    thickness: FloatWithPrecision5 = Field(
        default=0.1, ge=0.0001, le=100.0, title="Thickness"
    )
    width: FloatWithPrecision5 = Field(default=0.5, ge=0.005, le=0.5, title="Width")
    vlims: list[float] = Field(default=[0.0, 1.0])
    vmin: FloatWithPrecision6 = Field(default=0.0, ge=-1e32, le=1e32)
    vmin_slider: int = Field(default=0, ge=0, le=100)
    vmax: FloatWithPrecision6 = Field(default=1.0, ge=-1e32, le=1e32)
    vmax_slider: int = Field(default=100, ge=0, le=100)
    cbar: ColorbarOptions = Field(default=ColorbarOptions.binary, title="Color Scale")
    clip_type: ClipTypeOptions = Field(
        default=ClipTypeOptions.boxplot, title="Clip Type"
    )
    scale: AxisOptions = Field(default=AxisOptions.linear, title="Scale")

    def get_projection_matrix(self):
        return (
            self.U1,
            self.V1,
            self.W1,
            self.U2,
            self.V2,
            self.W2,
            self.U3,
            self.V3,
            self.W3,
        )


class InstrumentParameters(BaseModel):
    data: str = Field(default="")
    data_options: List[str] = Field(default=[""])
    check_h: FloatWithPrecision5 = Field(default=0.0, ge=-100.0, le=100.0)
    check_k: FloatWithPrecision5 = Field(default=0.0, ge=-100.0, le=100.0)
    check_l: FloatWithPrecision5 = Field(default=0.0, ge=-100.0, le=100.0)
    d_min: FloatWithPrecision5 = Field(default=0.0, ge=0.0, title="d(min)")
    d_max: FloatWithPrecision5 = Field(default=0.0, ge=0.0, title="d(max)")
    horizontal_angle: FloatWithPrecision5 = Field(
        default=0.0, ge=-180.0, le=180.0, title="Horizontal Angle"
    )
    horizontal_roi: FloatWithPrecision5 = Field(
        default=0.0, ge=0.0, le=180.0, title="Horizontal ROI"
    )
    vertical_angle: FloatWithPrecision5 = Field(
        default=0.0, ge=-180.0, le=180.0, title="Vertical Angle"
    )
    vertical_roi: FloatWithPrecision5 = Field(
        default=0.0, ge=0.0, le=180.0, title="Vertical ROI"
    )
    diffraction_label: str = Field(default="Axis:")
    diffraction: FloatWithPrecision5 = Field(default=0.0)

    @model_validator(mode="after")
    def validate_data(self) -> Self:
        if self.data not in self.data_options:
            raise ValueError(
                f"""Invalid data option. Must be one of: {",".join([f'"{option}"' for option in self.data_options])}"""
            )

        return self


class ModulationClusters(BaseModel):
    max_distance: FloatWithPrecision5 = Field(
        default=0.025, ge=0.0001, le=10.0, title="Maximum Distance"
    )
    min_samples: int = Field(default=15, ge=1, le=1000, title="Minimum Samples")
    centroids: List[Any] = Field(default=[])
    headers: List[Dict[str, str]] = [
        {"align": "center", "title": "h"},
        {"align": "center", "title": "k"},
        {"align": "center", "title": "l"},
    ]


class UBViewModel:
    def __init__(self, model: UBModel, binding: BindingInterface):
        self.model = model
        self.binding = binding

        self.slice_idle = True
        self.volume_idle = True

        self.instrument = InstrumentParameters()
        self.modulation_clusters = ModulationClusters()
        self.parameters = Parameters()
        self.peaks = Peaks()
        self.peaks_controls = PeaksControls()
        self.q_conversion = QConversion()
        self.slice = SliceParameters()
        self.ub_controls = UBControls()

        # Two-way bindings
        self.instrument_bind = self.binding.new_bind(
            self.instrument, callback_after_update=self.on_instrument_update
        )
        self.modulation_clusters_bind = self.binding.new_bind(
            self.modulation_clusters, callback_after_update=self.on_modulation_update
        )
        self.parameters_bind = self.binding.new_bind(
            self.parameters, callback_after_update=self.on_parameters_update
        )
        self.peaks_bind = self.binding.new_bind(
            self.peaks, callback_after_update=self.on_peaks_update
        )
        self.peaks_controls_bind = self.binding.new_bind(
            self.peaks_controls, callback_after_update=self.on_peaks_controls_update
        )
        self.q_conversion_bind = self.binding.new_bind(
            self.q_conversion, callback_after_update=self.on_q_conversion_update
        )
        self.slice_bind = self.binding.new_bind(
            self.slice, callback_after_update=self.on_slice_update
        )
        self.ub_controls_bind = self.binding.new_bind(
            self.ub_controls, callback_after_update=self.on_ub_controls_update
        )

        # One-way bindings
        self.add_Q_viz_bind = self.binding.new_bind()
        self.highlight_peak_bind = self.binding.new_bind()
        self.highlight_peaks_bind = self.binding.new_bind()
        self.update_cluster_peaks_bind = self.binding.new_bind()
        self.update_instrument_bind = self.binding.new_bind()
        self.update_slice_bind = self.binding.new_bind()
        self.update_slice_colorbar_bind = self.binding.new_bind()

    def on_instrument_update(self, results: Dict[str, Any]) -> None:
        pass

    def on_modulation_update(self, results: Dict[str, Any]) -> None:
        pass

    def on_parameters_update(self, results: Dict[str, Any]) -> None:
        pass

    def on_peaks_update(self, results: Dict[str, Any]) -> None:
        for update in results.get("updated", []):
            if update.startswith("highlighted_peaks") and self.peaks.highlighted_peaks:
                self.highlight_peak(self.peaks.highlighted_peaks[0])

    def on_peaks_controls_update(self, results: Dict[str, Any]) -> None:
        for update in results.get("updated", []):
            match update:
                case "peaks_path":
                    self.load_peaks(self.peaks_controls.peaks_path)

    def on_q_conversion_update(self, results: Dict[str, Any]) -> None:
        for update in results.get("updated", []):
            match update:
                case "instrument":
                    self.switch_instrument()
                case "wl_min":
                    if (
                        self.q_conversion.wl_max_disabled
                        and self.q_conversion.wl_min != self.q_conversion.wl_max
                    ):
                        self.q_conversion.wl_max = self.q_conversion.wl_min
                        self.q_conversion_bind.update_in_view(self.q_conversion)
                case "ub_path":
                    self.load_Q(self.q_conversion.ub_path)

    def on_slice_update(self, results: Dict[str, Any]) -> None:
        for update in results.get("updated", []):
            match update:
                case (
                    "plane"
                    | "value"
                    | "thickness"
                    | "width"
                    | "cbar"
                    | "clip_type"
                    | "scale"
                ):
                    self.reslice()

    def on_ub_controls_update(self, results: Dict[str, Any]) -> None:
        for update in results.get("updated", []):
            match update:
                case "calculate.selected_index":
                    if self.ub_controls.calculate.selected_index:
                        self.ub_controls.calculate.form = str(
                            self.ub_controls.calculate.table_contents[
                                self.ub_controls.calculate.selected_index[0]
                            ]["form"]
                        )
                        self.ub_controls_bind.update_in_view(self.ub_controls)
                case "ub_path":
                    self.load_UB(self.ub_controls.ub_path)

    def set_instrument_field(self, name: str, value: Any) -> None:
        match name:
            case "data":
                self.instrument.data = value
            case "check_h":
                self.instrument.check_h = float(value)
            case "check_k":
                self.instrument.check_k = float(value)
            case "check_l":
                self.instrument.check_l = float(value)
            case "d_min":
                self.instrument.d_min = float(value)
            case "d_max":
                self.instrument.d_max = float(value)
            case "horizontal_angle":
                self.instrument.horizontal_angle = float(value)
            case "horizontal_roi":
                self.instrument.horizontal_roi = float(value)
            case "vertical_angle":
                self.instrument.vertical_angle = float(value)
            case "vertical_roi":
                self.instrument.vertical_roi = float(value)
            case "diffraction":
                self.instrument.diffraction = float(value)

    def set_modulation_field(self, name: str, value: Any) -> None:
        match name:
            case "max_distance":
                self.modulation_clusters.max_distance = float(value)
            case "min_samples":
                self.modulation_clusters.min_samples = int(value)

    def set_parameters_field(self, name: str, value: Any) -> None:
        match name:
            case "modulation.dh1":
                self.parameters.modulation.dh1 = float(value)
            case "modulation.dk1":
                self.parameters.modulation.dk1 = float(value)
            case "modulation.dl1":
                self.parameters.modulation.dl1 = float(value)
            case "modulation.dh2":
                self.parameters.modulation.dh2 = float(value)
            case "modulation.dk2":
                self.parameters.modulation.dk2 = float(value)
            case "modulation.dl2":
                self.parameters.modulation.dl2 = float(value)
            case "modulation.dh3":
                self.parameters.modulation.dh3 = float(value)
            case "modulation.dk3":
                self.parameters.modulation.dk3 = float(value)
            case "modulation.dl3":
                self.parameters.modulation.dl3 = float(value)
            case "modulation.max_order":
                self.parameters.modulation.max_order = int(value)
            case "modulation.cross_terms":
                self.parameters.modulation.cross_terms = bool(value)

    def set_peaks_field(self, name: str, value: Any) -> None:
        match name:
            case "h1":
                self.peaks.h1 = float(value)
            case "k1":
                self.peaks.k1 = float(value)
            case "l1":
                self.peaks.l1 = float(value)
            case "h2":
                self.peaks.h2 = float(value)
            case "k2":
                self.peaks.k2 = float(value)
            case "l2":
                self.peaks.l2 = float(value)
            case "d1":
                self.peaks.d1 = float(value)
            case "d2":
                self.peaks.d2 = float(value)
            case "phi":
                self.peaks.phi = float(value)

    def set_peaks_controls_field(self, name: str, value: Any) -> None:
        match name:
            case "find.avoid_aluminum":
                self.peaks_controls.find.avoid_aluminum = bool(value)
            case "find.edge_pixels":
                self.peaks_controls.find.edge_pixels = int(value)
            case "find.max_peaks":
                self.peaks_controls.find.max_peaks = int(value)
            case "find.max_spacing":
                self.peaks_controls.find.max_spacing = float(value)
            case "find.min_density":
                self.peaks_controls.find.min_density = int(value)
            case "find.min_distance":
                self.peaks_controls.find.min_distance = float(value)
            case "index.round_hkl":
                self.peaks_controls.index.round_hkl = bool(value)
            case "index.satellite":
                self.peaks_controls.index.satellite = bool(value)
            case "index.satellite_tolerance":
                self.peaks_controls.index.satellite_tolerance = float(value)
            case "index.tolerance":
                self.peaks_controls.index.tolerance = float(value)
            case "predict.centering":
                self.peaks_controls.predict.centering = CenteringOptions(value)
            case "predict.edge_pixels":
                self.peaks_controls.predict.edge_pixels = int(value)
            case "predict.min_d_spacing":
                self.peaks_controls.predict.min_d_spacing = float(value)
            case "predict.satellite":
                self.peaks_controls.predict.satellite = bool(value)
            case "predict.satellite_min_d_spacing":
                self.peaks_controls.predict.satellite_min_d_spacing = float(value)
            case "integrate.adaptive_envelope":
                self.peaks_controls.integrate.adaptive_envelope = bool(value)
            case "integrate.centroid":
                self.peaks_controls.integrate.centroid = bool(value)
            case "integrate.inner_factor":
                self.peaks_controls.integrate.inner_factor = float(value)
            case "integrate.outer_factor":
                self.peaks_controls.integrate.outer_factor = float(value)
            case "integrate.radius":
                self.peaks_controls.integrate.radius = float(value)
            case "filter.comparison":
                self.peaks_controls.filter.comparison = ComparisonOptions(value)
            case "filter.filter":
                self.peaks_controls.filter.filter = FilterOptions(value)
            case "filter.value":
                self.peaks_controls.filter.value = float(value)

    def set_q_conversion_field(self, name: str, value: Any) -> None:
        match name:
            case "d_min":
                self.q_conversion.d_min = float(value)
            case "detector_calibration":
                self.q_conversion.detector_calibration = value
            case "experiment":
                self.q_conversion.experiment_number = int(value)
            case "instrument":
                self.q_conversion.instrument = InstrumentOptions(value)
                self.switch_instrument()
            case "ipts_number":
                self.q_conversion.ipts_number = int(value)
            case "lorentz_correction":
                self.q_conversion.lorentz_correction = bool(value)
            case "runs":
                self.q_conversion.runs = self.runs_string_to_list(value)
            case "time_stop":
                self.q_conversion.time_stop = int(value)
            case "tube_calibration":
                self.q_conversion.tube_calibration = value
            case "wl_max":
                self.q_conversion.wl_max = float(value)
            case "wl_min":
                self.q_conversion.wl_min = float(value)
                if self.q_conversion.wl_max_disabled:
                    self.q_conversion.wl_max = self.q_conversion.wl_min

        self.q_conversion_bind.update_in_view(self.q_conversion)

    def set_slice_field(self, name: str, value: Any) -> None:
        match name:
            case "U1":
                self.slice.U1 = float(value)
            case "V1":
                self.slice.V1 = float(value)
            case "W1":
                self.slice.W1 = float(value)
            case "U2":
                self.slice.U2 = float(value)
            case "V2":
                self.slice.V2 = float(value)
            case "W2":
                self.slice.W2 = float(value)
            case "U3":
                self.slice.U3 = float(value)
            case "V3":
                self.slice.V3 = float(value)
            case "W3":
                self.slice.W3 = float(value)
            case "plane":
                self.slice.plane = SlicePlaneOptions(value)
                self.reslice()
            case "value":
                self.slice.value = float(value)
                self.reslice()
            case "thickness":
                self.slice.thickness = float(value)
                self.reslice()
            case "width":
                self.slice.width = float(value)
                self.reslice()
            case "vlims":
                self.slice.vlims = value
            case "vmin_slider":
                self.slice.vmin_slider = int(value)
                self.slice.vmin = slider_to_value(value, self.slice.vlims)
                self.update_slice_colorbar_bind.update_in_view(
                    (self.slice.vmin, self.slice.vmax)
                )
            case "vmax_slider":
                self.slice.vmax_slider = int(value)
                self.slice.vmax = slider_to_value(value, self.slice.vlims)
                self.update_slice_colorbar_bind.update_in_view(
                    (self.slice.vmin, self.slice.vmax)
                )
            case "cbar":
                self.slice.cbar = ColorbarOptions(value)
                self.reslice()
            case "clip_type":
                self.slice.clip_type = ClipTypeOptions(value)
                self.reslice()
            case "scale":
                self.slice.scale = AxisOptions(value)
                self.reslice()

    def set_ub_controls_field(self, name: str, value: Any) -> None:
        match name:
            case "calculate.tolerance":
                self.ub_controls.calculate.tolerance = float(value)
            case "calculate.max_scalar_error":
                self.ub_controls.calculate.max_scalar_error = float(value)
            case "calculate.min_const":
                self.ub_controls.calculate.min_const = float(value)
            case "calculate.max_const":
                self.ub_controls.calculate.max_const = float(value)
            case "calculate.form":
                self.ub_controls.calculate.form = value
            case "transform.t11":
                self.ub_controls.transform.t11 = float(value)
            case "transform.t12":
                self.ub_controls.transform.t12 = float(value)
            case "transform.t13":
                self.ub_controls.transform.t13 = float(value)
            case "transform.t21":
                self.ub_controls.transform.t21 = float(value)
            case "transform.t22":
                self.ub_controls.transform.t22 = float(value)
            case "transform.t23":
                self.ub_controls.transform.t23 = float(value)
            case "transform.t31":
                self.ub_controls.transform.t31 = float(value)
            case "transform.t32":
                self.ub_controls.transform.t32 = float(value)
            case "transform.t33":
                self.ub_controls.transform.t33 = float(value)
            case "transform.tolerance":
                self.ub_controls.transform.tolerance = float(value)
            case "transform.lattice":
                self.ub_controls.transform.lattice = LatticeOptions(value)
            case "transform.symmetry":
                self.ub_controls.transform.symmetry = value
            case "refine.tolerance":
                self.ub_controls.refine.tolerance = float(value)
            case "refine.optimize":
                self.ub_controls.refine.optimize = OptimizeOptions(value)

        self.ub_controls_bind.update_in_view(self.ub_controls)

    def set_vis_viewmodel(self, view_model: VizViewModel):
        self.vis_viewmodel = view_model

    def convert_Q(self):
        worker = self.binding.new_worker(self.convert_Q_process)
        worker.connect_result(self.convert_Q_complete)
        worker.connect_finished(self.visualize)
        worker.connect_progress(self.vis_viewmodel.update_processing)
        worker.start()

    def convert_Q_complete(self, result):
        if result is not None:
            self.instrument.diffraction_label = "Wavelength" if not result else "Angle"
            self.instrument_bind.update_in_view(self.instrument)

            self.update_instrument_view()

    def convert_Q_process(self, progress):
        instrument = self.q_conversion.instrument
        wavelength = [self.q_conversion.wl_min, self.q_conversion.wl_max]
        tube_cal = self.q_conversion.tube_calibration
        det_cal = self.q_conversion.detector_calibration

        IPTS = self.q_conversion.ipts_number
        runs = self.q_conversion.runs
        exp = self.q_conversion.experiment_number
        lorentz = self.q_conversion.lorentz_correction
        time_stop = self.q_conversion.time_stop
        d_min = self.q_conversion.d_min

        validate = [IPTS, runs, wavelength]

        if instrument == InstrumentOptions.DEMAND:
            validate.append(exp)

        if all(elem is not None for elem in validate):
            mono = np.isclose(wavelength[0], wavelength[1])

            progress("Processing...", 1)

            progress("Data loading...", 10)

            data_load = self.model.load_data(
                instrument,
                IPTS,
                runs,
                exp,
                time_stop,
            )

            if data_load is None:
                progress("Files do not exist.", 0)

            workspace_count = self.model.get_number_workspaces()
            if workspace_count is not None:
                self.instrument.data_options = list(
                    map(str, range(1, workspace_count + 1))
                )
                if self.instrument.data not in self.instrument.data_options:
                    self.instrument.data = "1"
                self.instrument_bind.update_in_view(self.instrument)

            progress("Data loaded...", 40)

            progress("Data calibrating...", 50)

            self.model.calibrate_data(instrument, det_cal, tube_cal)

            progress("Data calibrated...", 60)

            progress("Data converting...", 70)

            self.model.convert_data(instrument, wavelength, lorentz, d_min)

            progress("Data converted...", 99)

            progress("Data converted!", 0)

            return mono
        else:
            progress("Invalid parameters.", 0)

    def filter_peaks(self):
        worker = self.binding.new_worker(self.filter_peaks_process)
        worker.connect_result(self.filter_peaks_complete)
        worker.connect_finished(self.visualize)
        worker.connect_progress(self.vis_viewmodel.update_processing)
        worker.start()

    def filter_peaks_complete(self, result):
        self.model.copy_UB_from_peaks()

    def filter_peaks_process(self, progress):
        name = self.peaks_controls.filter.filter
        operator = self.peaks_controls.filter.comparison
        value = self.peaks_controls.filter.value

        if self.model.has_peaks() and value is not None:
            progress("Processing...", 1)

            progress("Filtering peaks...", 50)

            self.model.filter_peaks(name, operator, value)

            progress("Peaks filtered...", 99)

            progress("Peaks filtered!", 100)

        else:
            progress("Invalid parameters.", 0)

    def find_peaks(self):
        worker = self.binding.new_worker(self.find_peaks_process)
        worker.connect_result(self.find_peaks_complete)
        worker.connect_finished(self.visualize)
        worker.connect_progress(self.vis_viewmodel.update_processing)
        worker.start()

    def find_peaks_complete(self, result):
        self.model.copy_UB_from_peaks()

    def find_peaks_process(self, progress):
        if self.model.has_Q():
            Q_min = self.peaks_controls.find.min_distance
            d_max = self.peaks_controls.find.max_spacing
            params = [
                self.peaks_controls.find.min_density,
                self.peaks_controls.find.max_peaks,
            ]
            edge = self.peaks_controls.find.edge_pixels
            no_al = self.peaks_controls.find.avoid_aluminum

            if Q_min is not None and params is not None:
                progress("Processing...", 1)

                progress("Finding peaks...", 10)

                self.model.find_peaks(Q_min, *params, edge)
                d_min = self.model.get_d_min()

                if no_al and d_min < d_max:
                    self.model.avoid_aluminum_contamination(d_min, d_max)

                progress("Peaks found...", 90)

                progress("Peaks found!", 100)

            else:
                progress("Invalid parameters.", 0)

    def index_peaks(self):
        worker = self.binding.new_worker(self.index_peaks_process)
        worker.connect_result(self.index_peaks_complete)
        worker.connect_finished(self.visualize)
        worker.connect_progress(self.vis_viewmodel.update_processing)
        worker.start()

    def index_peaks_complete(self, result):
        self.model.copy_UB_from_peaks()

    def index_peaks_process(self, progress):
        mod_info = self.get_modulation_info()

        mod_vec_1, mod_vec_2, mod_vec_3, max_order, cross_terms = mod_info

        if self.model.has_peaks() and self.model.has_UB():
            params = [
                self.peaks_controls.index.tolerance,
                self.peaks_controls.index.satellite_tolerance,
            ]
            sat = self.peaks_controls.index.satellite
            round_hkl = self.peaks_controls.index.round_hkl

            if params is not None:
                tol, sat_tol = params

                if not sat:
                    max_order = 0

                progress("Processing...", 1)

                progress("Indexing peaks...", 50)

                self.model.index_peaks(
                    tol,
                    sat_tol,
                    mod_vec_1,
                    mod_vec_2,
                    mod_vec_3,
                    max_order,
                    cross_terms,
                    round_hkl=round_hkl,
                )

                progress("Peaks indexed...", 99)

                progress("Peaks indexed!", 100)

            else:
                progress("Invalid parameters.", 0)

    def integrate_peaks(self):
        worker = self.binding.new_worker(self.integrate_peaks_process)
        worker.connect_result(self.integrate_peaks_complete)
        worker.connect_finished(self.visualize)
        worker.connect_progress(self.vis_viewmodel.update_processing)
        worker.start()

    def integrate_peaks_complete(self, result):
        self.model.copy_UB_from_peaks()

    def integrate_peaks_process(self, progress):
        params = [
            self.peaks_controls.integrate.radius,
            self.peaks_controls.integrate.inner_factor,
            self.peaks_controls.integrate.outer_factor,
        ]

        ellipsoid = self.peaks_controls.integrate.adaptive_envelope

        centroid = self.peaks_controls.integrate.centroid

        if self.model.has_peaks() and self.model.has_Q():
            if params is not None:
                method = "ellipsoid" if ellipsoid else "sphere"

                rad, inner_factor, outer_factor = params

                if inner_factor < 1:
                    inner_factor = 1
                if outer_factor < inner_factor:
                    outer_factor = inner_factor

                progress("Processing...", 1)

                progress("Integrating peaks...", 50)

                self.model.integrate_peaks(
                    rad,
                    inner_factor,
                    outer_factor,
                    method=method,
                    centroid=centroid,
                )

                progress("Peaks integrated...", 99)

                progress("Peaks integrated!", 100)

        else:
            progress("Invalid parameters.", 0)

    def predict_peaks(self):
        worker = self.binding.new_worker(self.predict_peaks_process)
        worker.connect_result(self.predict_peaks_complete)
        worker.connect_finished(self.visualize)
        worker.connect_progress(self.vis_viewmodel.update_processing)
        worker.start()

    def predict_peaks_complete(self, result):
        self.model.copy_UB_from_peaks()

    def predict_peaks_process(self, progress):
        mod_info = self.get_modulation_info()

        mod_vec_1, mod_vec_2, mod_vec_3, max_order, cross_terms = mod_info

        centering = self.peaks_controls.predict.centering

        wavelength = [self.q_conversion.wl_min, self.q_conversion.wl_max]

        params = [
            self.peaks_controls.predict.min_d_spacing,
            self.peaks_controls.predict.satellite_min_d_spacing,
        ]

        edge = self.peaks_controls.predict.edge_pixels

        if self.model.has_peaks() and self.model.has_UB():
            if wavelength is not None and params is not None:
                d_min, sat_d_min = params

                if sat_d_min < d_min:
                    sat_d_min = d_min

                lamda_min, lamda_max = wavelength

                if np.isclose(lamda_min, lamda_max):
                    lamda_min, lamda_max = 0.97 * lamda_min, 1.03 * lamda_max

                progress("Processing...", 1)

                progress("Predicting peaks...", 50)

                self.model.predict_peaks(centering, d_min, lamda_min, lamda_max, edge)

                if self.peaks_controls.predict.satellite:
                    progress("Predicting modulated...", 75)

                    self.model.predict_modulated_peaks(
                        sat_d_min,
                        lamda_min,
                        lamda_max,
                        mod_vec_1,
                        mod_vec_2,
                        mod_vec_3,
                        max_order,
                        cross_terms,
                    )

                progress("Peaks predicted...", 99)

                progress("Peaks predicted!", 100)

            else:
                progress("Invalid parameters.", 0)

    def runs_string_to_list(self, runs_str: str) -> List[int]:
        """
        Convert runs string to list using regex validation.
        Return None for invalid formats.

        Parameters
        ----------
        runs_str : str
            Condensed notation for run numbers.

        Returns
        -------
        runs : list or None
            Integer run numbers or None if the input is invalid.

        """

        pattern = r"^(\d+(?::\d+(?:;\d+)?)?)(,\d+(?::\d+(?:;\d+)?)?)*$"
        if not re.match(pattern, runs_str):
            return []

        runs: List[int] = []
        ranges = runs_str.split(",")

        for part in ranges:
            if ":" in part:
                range_part, *skip_part = part.split(";")
                start, end = map(int, range_part.split(":"))
                skip = int(skip_part[0]) if skip_part else 1

                if start > end or skip <= 0:
                    return []

                runs.extend(range(start, end + 1, skip))
            else:
                runs.append(int(part))

        return runs

    def switch_instrument(self) -> None:
        filepath = self.model.get_raw_file_path(self.q_conversion.instrument)
        wavelength = self.model.get_wavelength(self.q_conversion.instrument)

        self.q_conversion.detector_calibration = ""
        self.q_conversion.detector_disabled = "SNS" not in filepath
        self.q_conversion.experiment_disabled = "exp" not in filepath
        self.q_conversion.experiment_number = None
        self.q_conversion.ipts_number = None
        self.q_conversion.time_stop = None
        self.q_conversion.time_stop_disabled = "SNS" not in filepath
        self.q_conversion.tube_calibration = ""
        self.q_conversion.tube_disabled = "CORELLI" not in filepath
        self.q_conversion.runs = []
        if isinstance(wavelength, list):
            self.q_conversion.wl_max_disabled = False
            self.q_conversion.wl_min, self.q_conversion.wl_max = wavelength
        else:
            self.q_conversion.wl_max_disabled = True
            self.q_conversion.wl_min = self.q_conversion.wl_max = wavelength

        self.q_conversion_bind.update_in_view(self.q_conversion)

    def visualize(self):
        Q_hist = self.model.get_Q_info()

        if Q_hist is not None and self.volume_idle:
            self.volume_idle = False

            self.vis_viewmodel.update_processing()

            self.vis_viewmodel.update_processing("Updating view...", 50)

            self.add_Q_viz_bind.update_in_view(Q_hist)

            if self.model.has_UB():
                self.model.update_UB()

                self.vis_viewmodel.update_oriented_lattice()
                self.vis_viewmodel.set_transform(self.model.get_transform())
                self.update_lattice_info()

            if self.model.has_peaks():
                peaks = self.model.get_peak_info()
                self.peaks.peaks = peaks
                for index, _ in enumerate(self.peaks.peaks):
                    self.peaks.peaks[index]["index"] = index
                self.update_peaks()

            self.vis_viewmodel.update_complete("Data visualized!")

            self.volume_idle = True

    def get_shared_file_path(self) -> str:
        return self.model.get_shared_file_path(
            self.q_conversion.instrument, self.q_conversion.ipts_number
        )

    def load_Q(self, filename) -> None:
        self.model.load_Q(filename)

    def save_Q(self, filename) -> None:
        self.model.save_Q(filename)

    def load_peaks(self, filename) -> None:
        self.model.load_peaks(filename)

    def save_peaks(self, filename) -> None:
        self.model.save_peaks(filename)

    def find_conventional(self):
        worker = self.binding.new_worker(self.find_conventional_process)
        worker.connect_finished(self.visualize)
        worker.connect_progress(self.vis_viewmodel.update_processing)
        worker.start()

    def find_conventional_process(self, progress):
        if self.model.has_peaks():
            params = self.parameters.lattice.as_list()
            tol = self.ub_controls.calculate.tolerance

            if params is not None and tol is not None:
                progress("Processing...", 1)

                progress("Finding UB...", 10)

                self.model.determine_UB_with_lattice_parameters(*params, tol)

                progress("UB found...", 90)

                progress("UB found!", 100)

            else:
                progress("Invalid parameters.", 0)

    def find_niggli(self):
        worker = self.binding.new_worker(self.find_niggli_process)
        worker.connect_result(self.find_niggli_complete)
        worker.connect_finished(self.visualize)
        worker.connect_progress(self.vis_viewmodel.update_processing)
        worker.start()

    def find_niggli_complete(self, result):
        self.show_cells()

    def find_niggli_process(self, progress):
        if self.model.has_peaks():
            params = [
                self.ub_controls.calculate.min_const,
                self.ub_controls.calculate.max_const,
            ]
            tol = self.ub_controls.calculate.tolerance

            if params is not None and tol is not None:
                progress("Processing...", 1)

                progress("Finding UB...", 10)

                self.model.determine_UB_with_niggli_cell(*params, tol)

                progress("UB found...", 90)

                progress("UB found!", 100)

            else:
                progress("Invalid parameters.", 0)

    def show_cells(self):
        worker = self.binding.new_worker(self.show_cells_process)
        worker.connect_result(self.show_cells_complete)
        worker.connect_finished(self.visualize)
        worker.connect_progress(self.vis_viewmodel.update_processing)
        worker.start()

    def show_cells_complete(self, result):
        if result is not None:
            self.ub_controls.calculate.table_contents = []
            for index, cell in enumerate(result):
                self.ub_controls.calculate.table_contents.append(
                    {
                        "index": index,
                        "form": cell[0],
                        "error": cell[1],
                        "bravais": " ".join(cell[2]),
                        "a": cell[3][0],
                        "b": cell[3][1],
                        "c": cell[3][2],
                        "alpha": cell[3][3],
                        "beta": cell[3][4],
                        "gamma": cell[3][5],
                        "V": cell[3][6],
                    }
                )

            self.ub_controls_bind.update_in_view(self.ub_controls)

    def show_cells_process(self, progress):
        if self.model.has_peaks() and self.model.has_UB():
            scalar = self.ub_controls.calculate.max_scalar_error

            if scalar is not None:
                progress("Processing...", 1)

                progress("Finding possible cells...", 50)

                cells = self.model.possible_conventional_cells(scalar)

                progress("Possible cells found!", 100)

                return cells

            else:
                progress("Invalid parameters.", 0)

    def select_cell(self):
        worker = self.binding.new_worker(self.select_cell_process)
        worker.connect_finished(self.visualize)
        worker.connect_progress(self.vis_viewmodel.update_processing)
        worker.start()

    def select_cell_process(self, progress):
        if self.model.has_peaks() and self.model.has_UB():
            form = self.ub_controls.calculate.form
            tol = self.ub_controls.calculate.tolerance

            if form is not None and tol is not None:
                progress("Processing...", 1)

                progress("Selecting cell...", 50)

                self.model.select_cell(form, tol)

                progress("Cell selected...", 99)

                progress("Cell selected!", 100)

            else:
                progress("Invalid parameters.", 0)

    def transform_UB(self):
        worker = self.binding.new_worker(self.transform_UB_process)
        worker.connect_result(self.transform_UB_complete)
        worker.connect_finished(self.visualize)
        worker.connect_progress(self.vis_viewmodel.update_processing)
        worker.start()

    def transform_UB_complete(self, result):
        self.model.copy_UB_from_peaks()

    def transform_UB_process(self, progress):
        if self.model.has_peaks() and self.model.has_UB():
            params = (
                self.ub_controls.transform.t11,
                self.ub_controls.transform.t12,
                self.ub_controls.transform.t13,
                self.ub_controls.transform.t21,
                self.ub_controls.transform.t22,
                self.ub_controls.transform.t23,
                self.ub_controls.transform.t31,
                self.ub_controls.transform.t32,
                self.ub_controls.transform.t33,
            )
            tol = self.ub_controls.transform.tolerance

            if params is not None and tol is not None:
                progress("Processing...", 1)

                progress("Transforming UB...", 50)

                self.model.transform_lattice(params, tol)

                progress("UB transformed...", 99)

                progress("UB transformed!", 100)

            else:
                progress("Invalid parameters.", 0)

    def refine_UB(self):
        worker = self.binding.new_worker(self.refine_UB_process)
        worker.connect_result(self.refine_UB_complete)
        worker.connect_finished(self.visualize)
        worker.connect_progress(self.vis_viewmodel.update_processing)
        worker.start()

    def refine_UB_complete(self, result):
        self.model.copy_UB_from_peaks()

    def refine_UB_process(self, progress):
        if self.model.has_peaks():
            params = self.parameters.lattice.as_list()
            tol = self.ub_controls.refine.tolerance
            option = self.ub_controls.refine.optimize

            if option == "Constrained" and params is not None:
                progress("Processing...", 1)

                progress("Refining orientation...", 50)

                self.model.refine_U_only(*params)

                progress("Orientation refined...", 99)

                progress("Orientation refined!", 100)

            elif tol is not None:
                progress("Processing...", 1)

                progress("Refining UB...", 50)

                if option == "Unconstrained":
                    self.model.refine_UB_without_constraints(tol)
                else:
                    self.model.refine_UB_with_constraints(option, tol)

                progress("UB refined...", 99)

                progress("UB refined!", 100)

            else:
                progress("Invalid parameters.", 0)

    def load_UB(self, filename) -> None:
        self.model.load_UB(filename)
        self.vis_viewmodel.set_transform(self.model.get_transform())

    def save_UB(self, filename) -> None:
        self.model.save_UB(filename)

    def lattice_transform(self):
        cell = self.ub_controls.transform.lattice

        Ts = self.model.generate_lattice_transforms(cell)
        symbols = list(Ts.keys())

        symbol = self.ub_controls.transform.symmetry
        if symbol not in symbols:
            symbol = symbols[0]

        self.ub_controls.transform.symmetry_options = symbols
        self.ub_controls.transform.symmetry = symbol
        self.ub_controls_bind.update_in_view(self.ub_controls)

        self.symmetry_transform()

    def symmetry_transform(self):
        cell = self.ub_controls.transform.lattice

        Ts = self.model.generate_lattice_transforms(cell)

        symbol = self.ub_controls.transform.symmetry

        if symbol in Ts.keys():
            T = Ts[symbol]

            self.ub_controls.transform.t11 = T[0][0]
            self.ub_controls.transform.t12 = T[0][1]
            self.ub_controls.transform.t13 = T[0][2]
            self.ub_controls.transform.t21 = T[1][0]
            self.ub_controls.transform.t22 = T[1][1]
            self.ub_controls.transform.t23 = T[1][2]
            self.ub_controls.transform.t31 = T[2][0]
            self.ub_controls.transform.t32 = T[2][1]
            self.ub_controls.transform.t33 = T[2][2]

            self.ub_controls_bind.update_in_view(self.ub_controls)

    def highlight_cell(self, form):
        self.ub_controls.calculate.form = form
        self.ub_controls_bind.update_in_view(self.ub_controls)

    def update_lattice_info(self):
        params = self.model.get_lattice_constants()
        errors = self.model.get_lattice_constant_errors()
        if params is not None:
            (
                self.parameters.lattice.a,
                self.parameters.lattice.b,
                self.parameters.lattice.c,
                self.parameters.lattice.alpha,
                self.parameters.lattice.beta,
                self.parameters.lattice.gamma,
            ) = params
            (
                self.parameters.lattice.a_error,
                self.parameters.lattice.b_error,
                self.parameters.lattice.c_error,
                self.parameters.lattice.alpha_error,
                self.parameters.lattice.beta_error,
                self.parameters.lattice.gamma_error,
            ) = errors

        params = self.model.get_sample_directions()
        if params is not None:
            u, v, w = params
            self.parameters.sample_directions.uh = float(u[0])
            self.parameters.sample_directions.uk = float(u[1])
            self.parameters.sample_directions.ul = float(u[2])
            self.parameters.sample_directions.vh = float(v[0])
            self.parameters.sample_directions.vk = float(v[1])
            self.parameters.sample_directions.vl = float(v[2])
            self.parameters.sample_directions.wh = float(w[0])
            self.parameters.sample_directions.wk = float(w[1])
            self.parameters.sample_directions.wl = float(w[2])

        self.parameters_bind.update_in_view(self.parameters)

    def get_modulation_info(self):
        mod_info = (
            self.parameters.modulation.max_order,
            self.parameters.modulation.cross_terms,
        )
        if mod_info is not None:
            max_order, cross_terms = mod_info
        else:
            max_order, cross_terms = 0, False

        mod_vec = (
            self.parameters.modulation.dh1,
            self.parameters.modulation.dk1,
            self.parameters.modulation.dl1,
            self.parameters.modulation.dh2,
            self.parameters.modulation.dk2,
            self.parameters.modulation.dl2,
            self.parameters.modulation.dh3,
            self.parameters.modulation.dk3,
            self.parameters.modulation.dl3,
        )
        if mod_vec is not None:
            mod_vec_1 = mod_vec[0:3]
            mod_vec_2 = mod_vec[3:6]
            mod_vec_3 = mod_vec[6:9]

        return mod_vec_1, mod_vec_2, mod_vec_3, max_order, cross_terms

    def calculate_peaks(self):
        hkl_1, hkl_2 = self.peaks.get_input_hkls()
        constants = self.parameters.lattice.as_list()
        if constants is not None:
            d_phi = self.model.calculate_peaks(hkl_1, hkl_2, *constants)
            self.peaks.d1, self.peaks.d2, self.peaks.phi = d_phi
            self.update_peaks()

    def highlight_peaks(self, index):
        self.peaks.highlighted_peaks = []
        for row_index, row in enumerate(self.peaks.peaks, start=1):
            peak_no = row["peak_no"]
            if index == int(peak_no) - 1:
                self.peaks.highlighted_peaks.append(row_index)

        self.update_peaks()
        self.highlight_peaks_bind.update_in_view(self.peaks)

    def highlight_peak(self, row):
        if row is None:
            return

        no = self.peaks.peaks[row].get("peak_no", None)
        if no is not None:
            peak = self.model.get_peak(no)
            if peak is not None:
                self.peaks.h, self.peaks.k, self.peaks.l = peak["hkl"]
                self.peaks.int_h, self.peaks.int_k, self.peaks.int_l = map(
                    int, peak["int_hkl"]
                )
                self.peaks.int_m, self.peaks.int_n, self.peaks.int_p = map(
                    int, peak["int_mnp"]
                )
                self.peaks.d = peak["d_spacing"]
                self.peaks.lambda_value = peak["wavelength"]
                self.peaks.intensity = peak["intensity"]
                self.peaks.sigma = peak["sigma"]
                self.peaks.run = str(peak["run_number"])
                self.peaks.bank = peak["bank"]
                self.peaks.row = str(peak["row"])
                self.peaks.col = str(peak["col"])

                self.peaks.last_highlight = no + 1
                self.peaks.position = peak["Q"]
                self.update_peaks()
                self.highlight_peak_bind.update_in_view(self.peaks)

    def get_normal(self):
        slice_plane = self.slice.plane

        if slice_plane == SlicePlaneOptions.one_half:
            norm = [0, 0, 1]
        elif slice_plane == SlicePlaneOptions.one_third:
            norm = [0, 1, 0]
        else:
            norm = [1, 0, 0]

        return norm

    def reslice(self):
        if self.model.is_sliced():
            self.convert_to_hkl()

    def convert_to_hkl(self):
        if self.slice_idle:
            self.slice_idle = False

            worker = self.binding.new_worker(self.convert_to_hkl_process)
            worker.connect_result(self.convert_to_hkl_complete)
            worker.connect_finished(self.vis_viewmodel.update_complete)
            worker.connect_progress(self.vis_viewmodel.update_processing)
            worker.start()

    def convert_to_hkl_complete(self, result):
        if result is not None:
            self.update_slice_bind.update_in_view(
                (result, CMAPS[self.slice.cbar], self.slice.scale.lower())
            )
        self.slice_idle = True

    def convert_to_hkl_process(self, progress):
        proj = self.slice.get_projection_matrix()

        value = self.slice.value

        thickness = self.slice.thickness

        width = self.slice.width

        validate = [proj, value, thickness, width]

        if all(elem is not None for elem in validate):
            proj = np.array(proj).reshape(3, 3)

            if not np.isclose(np.linalg.det(proj), 0):
                U, V, W = proj

                norm = self.get_normal()

                progress("Processing...", 1)

                slice_histo = self.model.get_slice_info(
                    U, V, W, norm, value, thickness, width
                )

                progress("Updating slice...", 50)

                if slice_histo is not None:
                    signal = slice_histo["signal"]

                    clip = self.model.calculate_clim(signal, self.slice.clip_type)

                    slice_histo["clip"] = clip

                    progress("Slice drawn!", 100)

                    return slice_histo

                else:
                    progress("Invalid parameters.", 0)

        else:
            progress("Invalid parameters.", 0)

    def update_instrument_view(self):
        worker = self.binding.new_worker(self.update_instrument_view_process)
        worker.connect_result(self.update_instrument_view_complete)
        worker.connect_finished(self.visualize)
        worker.connect_progress(self.vis_viewmodel.update_processing)
        worker.start()

    def update_instrument_view_complete(self, result):
        if result is not None:
            self.update_instrument_bind.update_in_view(result)

            self.update_check_hkl()

    def update_instrument_view_process(self, progress):
        if self.model.has_Q():
            ind = int(self.instrument.data) - 1
            d_min = self.instrument.d_min
            d_max = self.instrument.d_max
            horz = self.instrument.horizontal_angle
            vert = self.instrument.vertical_angle
            horz_roi = self.instrument.horizontal_roi
            vert_roi = self.instrument.vertical_roi
            val = self.instrument.diffraction

            validate = [d_min, d_max, horz, vert, horz_roi, vert_roi, val]

            if all(elem is not None for elem in validate):
                progress("Processing...", 1)

                progress("Detector viewing...", 10)

                self.model.calculate_instrument_view(ind, d_min, d_max)

                progress("Detector viewed...", 50)

                self.model.extract_roi(horz, vert, horz_roi, vert_roi, val)

                progress("ROI viewed...", 70)

                progress("Data/ROI viewed!", 0)

                return self.model.inst_view, self.model.roi_view

        else:
            progress("Invalid parameters.", 0)

    def update_check_hkl(self):
        ind = int(self.instrument.data) - 1
        horz = self.instrument.horizontal_angle
        vert = self.instrument.vertical_angle
        val = self.instrument.diffraction

        validate = [horz, vert, val]

        if all(elem is not None for elem in validate):
            hkl = self.model.roi_scan_to_hkl(ind, val, horz, vert)
            if hkl is not None:
                (
                    self.instrument.check_h,
                    self.instrument.check_k,
                    self.instrument.check_l,
                ) = hkl
                self.instrument_bind.update_in_view(self.instrument)

    def add_peak(self):
        if self.model.has_Q():
            ind = int(self.instrument.data) - 1
            horz = self.instrument.horizontal_angle
            vert = self.instrument.vertical_angle
            val = self.instrument.diffraction

            validate = [horz, vert, val]

            if all(elem is not None for elem in validate):
                self.model.add_peak(ind, val, horz, vert)
                self.visualize()

    def calculate_hkl(self):
        if self.model.has_Q():
            ind = int(self.instrument.data) - 1
            hkl = (
                self.instrument.check_h,
                self.instrument.check_k,
                self.instrument.check_l,
            )

            validate = [ind, hkl]

            if all(elem is not None for elem in validate):
                vals = self.model.calculate_hkl_position(ind, *hkl)

                if vals is not None:
                    (
                        self.instrument.diffraction,
                        self.instrument.horizontal_angle,
                        self.instrument.vertical_angle,
                    ) = vals
                    self.instrument_bind.update_in_view(self.instrument)

                    self.update_instrument_view()

    def cluster(self):
        worker = self.binding.new_worker(self.cluster_process)
        worker.connect_result(self.cluster_complete)
        worker.connect_progress(self.vis_viewmodel.update_processing)
        worker.start()

    def cluster_complete(self, result):
        if result is not None:
            self.vis_viewmodel.update_processing("Adding peaks.", 30)

            self.update_cluster_peaks_bind.update_in_view(result)

            centroids = result["satellites"].round(3).astype(str)
            self.modulation_clusters.centroids = centroids
            self.modulation_clusters_bind.update_in_view(self.modulation_clusters)

            self.vis_viewmodel.update_processing("Peaks added!", 0)

    def cluster_process(self, progress):
        params = (
            self.modulation_clusters.max_distance,
            self.modulation_clusters.min_samples,
        )

        if params is not None:
            progress("Invalid parameters.", 0)

            peak_info = self.model.get_cluster_info()
            # print(peak_info)
            if peak_info is not None:
                progress("Clustering peaks.", 25)

                success = self.model.cluster_peaks(peak_info, *params)
                # print(success)

                if success:
                    progress("Peaks clustered!", 100)

                    return peak_info

                else:
                    progress("Invalid cluster.", 0)

        else:
            progress("Invalid parameters.", 0)

    def update_peaks(self):
        ind, tot = 0, 0
        for row, peak in enumerate(self.peaks.peaks):
            ind += peak["ind"]
            tot += 1

        self.peaks.index = ind
        self.peaks.total = tot
        self.peaks_bind.update_in_view(self.peaks)
