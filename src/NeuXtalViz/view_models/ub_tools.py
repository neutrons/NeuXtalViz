import re
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
from nova.mvvm.interface import BindingInterface  # type: ignore
from pydantic import BaseModel, Field

from NeuXtalViz.models.ub_tools import UBModel
from NeuXtalViz.view_models.base_view_model import NeuXtalVizViewModel


class InstrumentOptions(str, Enum):
    CORELLI = "CORELLI"
    DEMAND = "DEMAND"
    MANDI = "MANDI"
    SNAP = "SNAP"
    TOPAZ = "TOPAZ"
    WAND2 = "WAND²"


class QConversion(BaseModel):
    d_min: float = Field(default=0.7, title="d(min)")
    detector_calibration: str = Field(default="", title="Detector Calibration")
    detector_disabled: bool = Field(default=False)
    experiment_disabled: bool = Field(default=True)
    experiment_number: Optional[int] = Field(default=None, title="Experiment Number")
    instrument: InstrumentOptions = Field(
        default=InstrumentOptions.TOPAZ, title="Instrument"
    )
    ipts_disabled: bool = Field(default=False)
    ipts_number: Optional[int] = Field(default=None, title="IPTS Number")
    lorentz_correction: bool = Field(default=True, title="Lorentz Correction")
    runs: List[int] = Field(default=[], title="Runs")
    time_stop: Optional[float] = Field(default=None, title="Time Stop (s)")
    time_stop_disabled: bool = Field(default=False)
    tube_calibration: str = Field(default="", title="Tube Calibration")
    tube_disabled: bool = Field(default=True)
    wl_max: float = Field(default=3.5, title="λ(max)")
    wl_max_disabled: bool = Field(default=False)
    wl_min: float = Field(default=0.4, title="λ(min)")


class UBViewModel:
    def __init__(self, model: UBModel, binding: BindingInterface):
        self.model = model
        self.binding = binding

        self.volume_idle = True

        self.q_conversion = QConversion()

        self.add_Q_viz_bind = self.binding.new_bind()
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
                self.q_conversion.time_stop = float(value)
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
