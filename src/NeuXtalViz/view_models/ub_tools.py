import re
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
from nova.mvvm.interface import BindingInterface  # type: ignore
from pydantic import BaseModel, Field

from NeuXtalViz.models.ub_tools import UBModel
from NeuXtalViz.shared.types import (
    FloatWithPrecision3,
    FloatWithPrecision4,
    FloatWithPrecision5,
)
from NeuXtalViz.view_models.base_view_model import NeuXtalVizViewModel


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


class FindPeaks(BaseModel):
    avoid_aluminum: bool = Field(default=True, title="Avoid Aluminum")
    edge_pixels: int = Field(default=0, ge=0, le=64, title="Edge Pixels")
    max_peaks: int = Field(default=100, ge=10, le=1000, title="Max Peaks")
    max_spacing: FloatWithPrecision4 = Field(
        default=31.46, ge=0.1, le=100, title="Max Spacing"
    )
    min_density: int = Field(default=100, ge=1, le=100000, title="Min Density")
    min_distance: FloatWithPrecision4 = Field(
        default=0.2, ge=0.01, le=10.0, title="Min Distance"
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
        default=0.7, ge=0.4, le=100.0, title="Min d-spacing"
    )
    satellite: bool = Field(default=False, title="Satellite")
    satellite_min_d_spacing: FloatWithPrecision3 = Field(
        default=1.0, ge=0.4, le=100.0, title="Min d-spacing"
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
    radius: FloatWithPrecision3 = Field(default=0.25, ge=0.0, le=1.0, title="Radius")


class FilterPeaks(BaseModel):
    comparison: ComparisonOptions = Field(
        default=ComparisonOptions.gt, title="Comparison"
    )
    filter: FilterOptions = Field(default=FilterOptions.i_sigma, title="Filter")
    value: FloatWithPrecision3 = Field(default=0.0, ge=-1e6, le=1e6, title="Value")


class Peaks(BaseModel):
    find: FindPeaks = FindPeaks()
    index: IndexPeaks = IndexPeaks()
    predict: PredictPeaks = PredictPeaks()
    integrate: IntegratePeaks = IntegratePeaks()
    filter: FilterPeaks = FilterPeaks()


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


class UBViewModel:
    def __init__(self, model: UBModel, binding: BindingInterface):
        self.model = model
        self.binding = binding

        self.volume_idle = True

        self.peaks = Peaks()
        self.q_conversion = QConversion()

        self.add_Q_viz_bind = self.binding.new_bind()
        self.peaks_bind = self.binding.new_bind(
            self.peaks, callback_after_update=self.on_peaks_update
        )
        self.q_conversion_bind = self.binding.new_bind(
            self.q_conversion, callback_after_update=self.on_q_conversion_update
        )

    def convert_Q(self):
        worker = self.binding.new_worker(self.convert_Q_process)
        worker.connect_result(self.convert_Q_complete)
        worker.connect_finished(self.visualize)
        worker.connect_progress(self.vis_viewmodel.update_processing)
        worker.start()

    def convert_Q_complete(self, result):
        if result is not None:
            pass
            # TODO
            # self.view.update_diffraction_label(result)
            # self.update_instrument_view()

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

            # TODO
            # self.view.set_data_list(self.model.get_number_workspaces())

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
        name = self.peaks.filter.filter
        operator = self.peaks.filter.comparison
        value = self.peaks.filter.value

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
            Q_min = self.peaks.find.min_distance
            d_max = self.peaks.find.max_spacing
            params = [self.peaks.find.min_density, self.peaks.find.max_peaks]
            edge = self.peaks.find.edge_pixels
            no_al = self.peaks.find.avoid_aluminum

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
            params = [self.peaks.index.tolerance, self.peaks.index.satellite_tolerance]
            sat = self.peaks.index.satellite
            round_hkl = self.peaks.index.round_hkl

            if params is not None:
                tol, sat_tol = params

                if sat == False:
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
            self.peaks.integrate.radius,
            self.peaks.integrate.inner_factor,
            self.peaks.integrate.outer_factor,
        ]

        ellipsoid = self.peaks.integrate.adaptive_envelope

        centroid = self.peaks.integrate.centroid

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

    def on_peaks_update(self, results: Dict[str, Any]) -> None:
        pass

    def on_q_conversion_update(self, results: Dict[str, Any]) -> None:
        for update in results.get("updated", []):
            match update:
                case "d_min":
                    pass
                case "detector_calibration":
                    pass
                case "experiment":
                    pass
                case "instrument":
                    pass
                case "ipts_number":
                    pass
                case "lorentz_correction":
                    pass
                case "runs":
                    pass
                case "time_stop":
                    pass
                case "tube_calibration":
                    pass
                case "wl_max":
                    pass
                case "wl_min":
                    pass

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

        centering = self.peaks.predict.centering

        wavelength = [self.q_conversion.wl_min, self.q_conversion.wl_max]

        params = [
            self.peaks.predict.min_d_spacing,
            self.peaks.predict.satellite_min_d_spacing,
        ]

        edge = self.peaks.predict.edge_pixels

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

                if self.peaks.predict.satellite:
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

    def set_peaks_field(self, name: str, value: Any) -> None:
        match name:
            case "find.avoid_aluminum":
                self.peaks.find.avoid_aluminum = bool(value)
            case "find.edge_pixels":
                self.peaks.find.edge_pixels = int(value)
            case "find.max_peaks":
                self.peaks.find.max_peaks = int(value)
            case "find.max_spacing":
                self.peaks.find.max_spacing = float(value)
            case "find.min_density":
                self.peaks.find.min_density = int(value)
            case "find.min_distance":
                self.peaks.find.min_distance = float(value)
            case "index.round_hkl":
                self.peaks.index.round_hkl = bool(value)
            case "index.satellite":
                self.peaks.index.satellite = bool(value)
            case "index.satellite_tolerance":
                self.peaks.index.satellite_tolerance = float(value)
            case "index.tolerance":
                self.peaks.index.tolerance = float(value)
            case "predict.centroid":
                self.peaks.predict.centroid = bool(value)
            case "predict.edge_pixels":
                self.peaks.predict.edge_pixels = int(value)
            case "predict.min_d_spacing":
                self.peaks.predict.min_d_spacing = float(value)
            case "predict.satellite":
                self.peaks.predict.satellite = bool(value)
            case "predict.satellite_min_d_spacing":
                self.peaks.predict.satellite_min_d_spacing = float(value)
            case "integrate.adaptive_envelope":
                self.peaks.predict.adaptive_envelope = bool(value)
            case "integrate.centering":
                self.peaks.predict.centering = CenteringOptions(value)
            case "integrate.inner_factor":
                self.peaks.integrate.inner_factor = float(value)
            case "integrate.outer_factor":
                self.peaks.integrate.outer_factor = float(value)
            case "integrate.radius":
                self.peaks.integrate.radius = float(value)
            case "filter.comparison":
                self.peaks.filter.comparison = ComparisonOptions(value)
            case "filter.filter":
                self.peaks.filter.filter = FilterOptions(value)
            case "filter.value":
                self.peaks.filter.value = float(value)

        self.peaks_bind.update_in_view(self.peaks)

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

    def set_vis_viewmodel(self, view_model: NeuXtalVizViewModel):
        self.vis_viewmodel = view_model

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

                self.vis_viewmodel.update_lattice_info()

            if self.model.has_peaks():
                peaks = self.model.get_peak_info()

                # TODO
                # self.view.update_peaks_table(peaks)

            self.vis_viewmodel.update_complete("Data visualized!")

            self.volume_idle = True
