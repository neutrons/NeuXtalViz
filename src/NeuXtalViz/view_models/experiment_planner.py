from enum import Enum
from typing import Optional, List, Dict, Any

import numpy as np
from pydantic import BaseModel, Field

from NeuXtalViz.view_models.base_view_model import NeuXtalVizViewModel


def key_updated(key, partial, results) -> bool:
    for update in results.get("updated", []):
        if partial and (f"{key}." in update or f"{key}[" in update):
            return True
        if key == update:
            return True
    return False


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
    trigonal_rhombohedral = "Trigonal/Rhombohedral"
    trigonal_hexagonal = "Trigonal/Hexagonal"
    hexagonal = "Hexagonal"
    cubic = "Cubic"


class EPSettings(BaseModel):
    ub_path: str = Field(default="")
    crystal_system: CrystalSystemOptions = Field(
        default=CrystalSystemOptions.triclinic, title="Crystal System"
    )
    point_groups: List[str] = []
    point_group: Optional[str] = Field(default=None, title="Point Group")
    lattice_centerings: List[str] = []
    lattice_centering: Optional[str] = Field(default=None, title="Lattice Centering")


class EPParams(BaseModel):
    instrument: EPInstrumentOptions = Field(
        default=EPInstrumentOptions.topaz, title="Instrument"
    )
    wl_min: float = Field(default=0.4, title="Wl(min)", ge=0.2, le=10)
    wl_max: float = Field(default=3.5, title="Wl(max)", ge=0.2, le=10)
    no_wl_max: bool = False
    d_min: float = Field(default=0.7, title="d(min)", ge=0.4, le=10)

    def set_wavelengths(self, wavelength):
        if type(wavelength) is list:
            self.wl_min = wavelength[0]
            self.wl_max = wavelength[1]
            self.no_wl_max = False
        else:
            self.wl_min = wavelength
            self.wl_max = wavelength
            self.no_wl_max = True

    def get_wavelength(self):
        return [self.wl_min, self.wl_max]


class EPGoniometers(BaseModel):
    goniometer_table: List[Dict[str, str | float | bool | int]] = []
    goniometer_table_headers: List[Dict[str, str]] = [
        {"key": "motor", "title": "Motor"},
        {"key": "min", "title": "Min"},
        {"key": "max", "title": "Max"},
    ]
    modes: Optional[List[str]] = Field(default=None, title="Modes")
    current_mode: Optional[str] = None

    def table_from_goniometers(self, goniometers):
        self.goniometer_table = []
        for row, gon in enumerate(goniometers):
            angle, amin, amax = gon
            table_row = {"motor": angle, "min": amin, "max": amax}
            table_row["editable"] = amin == amax
            self.goniometer_table.append(table_row)

    def set_limits(self, limits):
        for row, limit in enumerate(limits):
            self.goniometer_table[row]["min"] = limit[0]
            self.goniometer_table[row]["max"] = limit[1]

    def get_limits(self):
        return [[row["min"], row["max"]] for row in self.goniometer_table]

    def get_all_angles(self):
        return [row["motor"] for row in self.goniometer_table]

    def get_free_angles(self):
        return [
            row["motor"] for row in self.goniometer_table if row["min"] != row["max"]
        ]


class EPPlan(BaseModel):
    experiment_path: str = Field(default="")
    counting_options: Optional[List[str]] = Field(default=None, title="Options")
    counting_option: Optional[str] = Field(default=None)
    title: str = Field(default="Scan Title", title="Title")
    count: float = Field(default=1.0, title="Count", ge=0.001, le=10000)
    settings: int = Field(default=20, title="Settings", ge=1, le=1000)
    plan_table: List[Dict[str, str | float | bool | int]] = []
    plan_table_selected_rows: List[int] = []
    plan_table_headers: List[Dict[str, str]] = []
    mesh_table: List[Dict[str, str | float | int | bool]] = []
    mesh_table_headers: List[Dict[str, str]] = [
        {"key": "motor", "title": "Motor"},
        {"key": "min", "title": "Min"},
        {"key": "max", "title": "Max"},
        {"key": "angles", "title": "Angles"},
    ]

    def add_orientation(self, title, comment, angles):
        table_row = {
            "index": len(self.plan_table),
            "title": title,
            "comment": comment,
            "wait_for": self.counting_option,
            "value": self.count,
            "use": True,
        }
        for i, angle in enumerate(angles):
            table_row[f"angle{i}"] = float(angle)
        self.plan_table.append(table_row)

    def update_plan_headers(self, title, goniometers: EPGoniometers):
        free = goniometers.get_free_angles()
        self.plan_table_headers = (
            [{"key": "title", "title": title}]
            + [{"key": f"angle{i}", "title": motor} for i, motor in enumerate(free)]
            + [
                {"key": "comment", "title": "Comment"},
                {"key": "wait_for", "title": "Wait For"},
                {"key": "value", "title": "Value"},
                {"key": "use", "title": "Use"},
            ]
        )

    def update_selected_plan_table_rows(self):
        for row in self.plan_table_selected_rows:
            self.plan_table[row]["title"] = self.title
            self.plan_table[row]["wait_for"] = self.counting_option or ""
            self.plan_table[row]["value"] = self.count

    def load_settings(self, titles, settings, comments, counts, values, use):
        self.plan_table = []
        for row, angles in enumerate(settings):
            table_row = {
                "index": row,
                "title": titles[row],
                "comment": comments[row],
                "wait_for": counts[row],
                "value": values[row],
                "use": use[row],
            }
            for i, angle in enumerate(angles):
                table_row[f"angle{i}"] = float(angle)

            self.plan_table.append(table_row)

    def mesh_table_from_goniometers(self, goniometers: EPGoniometers):
        self.mesh_table = []
        for row in goniometers.goniometer_table:
            motor, amin, amax = row["motor"], row["min"], row["max"]
            if amin != amax:
                table_row = {"motor": motor, "min": amin, "max": amax, "angle": 1}
                self.mesh_table.append(table_row)

    def get_orientations_to_use(self):
        return [row["use"] for row in self.plan_table]

    def get_optimized_settings(self):
        return [row["comment"] == "CrystalPlan" for row in self.plan_table]

    def get_angle_setting(self, row):
        angle_count = sum(1 for key in self.plan_table[row] if key.startswith("angle"))
        setting = [None] * angle_count
        for key in self.plan_table[row]:
            if key.startswith("angle"):
                n = int(key[5:])
                setting[n] = self.plan_table[row][key]

        return setting

    def get_number_of_orientations(self):
        return len(self.plan_table)

    def get_all_settings(self):
        settings = []
        for row in range(len(self.plan_table)):
            setting = self.get_angle_setting(row)
            settings.append(setting)

        return settings


class EPPeakSettings(BaseModel):
    h1: Optional[float] = Field(default=None, title="h1", ge=-100, le=100)
    k1: Optional[float] = Field(default=None, title="k1", ge=-100, le=100)
    l1: Optional[float] = Field(default=None, title="l1", ge=-100, le=100)
    h2: Optional[float] = Field(default=None, title="h2", ge=-100, le=100)
    k2: Optional[float] = Field(default=None, title="k2", ge=-100, le=100)
    l2: Optional[float] = Field(default=None, title="l2", ge=-100, le=100)
    horizontal: Optional[float] = Field(default=None, title="γ [°]")
    vertical: Optional[float] = Field(default=None, title="ν [°]")
    intersect: Optional[float] = Field(default=None, title="λ [Å]")
    horizontal_alt: Optional[float] = Field(default=None, title="γ [°] alt")
    vertical_alt: Optional[float] = Field(default=None, title="ν [°] alt")
    intersect_alt: Optional[float] = Field(default=None, title="λ [Å] alt")
    allow_equivalents: bool = Field(default=False, title="Allow Equivalents")

    def get_hlk1(self):
        if self.h1 and self.k1 and self.l1:
            return self.h1, self.k1, self.l1
        else:
            return None

    def get_hlk2(self):
        if self.h2 and self.k2 and self.l2:
            return self.h2, self.k2, self.l2
        else:
            return None


class EPPeakTable(BaseModel):
    peak_table: List[Dict[str, str | float | int | bool]] = []
    peak_table_headers: List[Dict[str, str]] = [
        {"key": "h", "title": "h"},
        {"key": "k", "title": "k"},
        {"key": "l", "title": "l"},
        {"key": "d", "title": "d"},
        {"key": "lamda", "title": "λ"},
    ]
    angles: Optional[str] = Field(default=None, title="Angles")
    angles_options: List[str] = []
    angles_option: Optional[str] = None

    def from_list(self, rows):
        self.peak_table = []
        for row in rows:
            h, k, l, d, lamda = row
            table_row = {
                "h": float(h),
                "k": float(k),
                "l": float(l),
                "d": float(d),
                "lamda": float(lamda),
            }
            self.peak_table.append(table_row)

    def set_angles(self, values):
        self.angles = "(" + ", ".join(np.array(values).astype(str)) + ")"

    def get_angles(self):
        ang = self.angles
        ang = ang.strip("(").strip(")").split(",")
        return [float(val) for val in ang if val != ""]

    def update_options(self, nrows):
        self.angles_options = ["0: Missing"]
        for row in range(nrows):
            self.angles_options.append(str(row + 1))
        if self.angles_option not in self.angles_options:
            self.angles_option = self.angles_options[0]


class EPMotors(BaseModel):
    mask_file: str = Field(default="", title="Mask File")
    detector_file: str = Field(default="", title="Detector File")
    motor_table: List[Dict[str, str | float | int | bool]] = []
    motor_table_headers: List[Dict[str, str]] = [
        {"key": "motor", "title": "Motor"},
        {"key": "value", "title": "Value"},
    ]

    def table_from_motors(self, motors):
        self.motor_table = []
        for row in motors:
            table_row = {"motor": row[0], "value": row[1]}
            self.motor_table.append(table_row)

    def set_motors(self, values):
        for row, value in enumerate(values):
            self.motor_table[row]["value"] = value

    def motors_from_table(self):
        logs = {}
        for row in self.motor_table:
            setting = row["motor"]
            logs[setting] = row["value"]

        return logs


class ExperimentPlannerViewModel:
    def __init__(self, model, binding):
        self.model = model
        self.vis_viewmodel = None
        self.binding = binding
        self.settings = EPSettings()
        self.params = EPParams()
        self.goniometers = EPGoniometers()
        self.plan = EPPlan()
        self.motors = EPMotors()

        self.peak_settings = EPPeakSettings()
        self.peak_table = EPPeakTable()

        self.ep_peak_settings_bind = binding.new_bind(self.peak_settings)

        self.ep_peak_table_bind = binding.new_bind(
            self.peak_table, callback_after_update=self.process_peak_table_updates
        )

        self.ep_settings_bind = binding.new_bind(
            self.settings, callback_after_update=self.process_settings_updates
        )
        self.ep_params_bind = binding.new_bind(
            self.params, callback_after_update=self.process_params_updates
        )
        self.ep_goniometers_bind = binding.new_bind(
            self.goniometers, callback_after_update=self.process_goniometers_updates
        )
        self.ep_plan_bind = binding.new_bind(
            self.plan, callback_after_update=self.process_plan_updates
        )
        self.ep_motors_bind = binding.new_bind(
            self.motors, callback_after_update=self.process_motors_updates
        )

        self.ep_statistics_bind = binding.new_bind()
        self.ep_peak_bind = binding.new_bind()
        self.ep_peak_plot_instrument_bind = binding.new_bind()
        self.ep_peak_inst_bind = binding.new_bind()

        self.draw_idle = True

    def initialize(self):
        self.switch_instrument()
        self.switch_crystal()

    def get_load_path(self):
        inst = self.params.instrument
        return self.model.get_calibration_file_path(inst)

    def switch_instrument(self):
        instrument = self.params.instrument

        self.params.set_wavelengths(self.model.get_wavelength(instrument))
        motors = self.model.get_motors(instrument)
        self.motors.table_from_motors(motors)
        self.goniometers.modes = self.model.get_modes(instrument)
        if (
            self.goniometers.modes
            and self.goniometers.current_mode not in self.goniometers.modes
        ):
            self.goniometers.current_mode = self.goniometers.modes[0]
        goniometers = self.model.get_goniometers(instrument, self.goniometers.modes[0])
        self.goniometers.table_from_goniometers(goniometers)
        self.plan.counting_options = self.model.get_counting_options(instrument)
        if (
            self.plan.counting_options
            and self.plan.counting_option not in self.plan.counting_options
        ):
            self.plan.counting_option = self.plan.counting_options[0]

        self.ep_params_bind.update_in_view(self.params)
        self.ep_motors_bind.update_in_view(self.motors)

        self.ep_goniometers_bind.update_in_view(self.goniometers)
        self.update_plan_from_goniometers()
        self.model.remove_instrument()

    def switch_crystal(self):
        point_groups = self.model.get_crystal_system_point_groups(
            self.settings.crystal_system
        )
        self.settings.point_groups = point_groups
        if self.settings.point_group not in point_groups:
            self.settings.point_group = point_groups[0]
        self.ep_settings_bind.update_in_view(self.settings)

        self.switch_group()

    def switch_group(self):
        pg = self.settings.point_group
        self.settings.lattice_centerings = self.model.get_point_group_centering(pg)
        if self.settings.lattice_centering not in self.settings.lattice_centerings:
            self.settings.lattice_centering = self.settings.lattice_centerings[0]
        self.ep_settings_bind.update_in_view(self.settings)

        self.visualize()

    def switch_centering(self):
        self.visualize()

    def update_plan_from_goniometers(self):
        title = self.model.get_scan_log(self.params.instrument)
        self.plan.mesh_table_from_goniometers(self.goniometers)
        self.plan.update_plan_headers(title, self.goniometers)
        self.ep_plan_bind.update_in_view(self.plan)

    def update_goniometer(self):
        self.goniometers.table_from_goniometers(
            self.model.get_goniometers(
                self.params.instrument, self.goniometers.current_mode
            )
        )
        self.update_plan_from_goniometers()
        self.ep_goniometers_bind.update_in_view(self.goniometers)

    def update_wavelength(self):
        self.ep_params_bind.update_in_view(self.params)

    def create_instrument(self):
        instrument = self.params.instrument
        motors = self.motors.motors_from_table()
        cal = self.motors.detector_file
        mask = self.motors.mask_file

        self.model.initialize_instrument(instrument, motors, cal, mask)

    def calculate_single(self):
        self.alt_hkl = False
        self.calculate_single_hkl()

    def calculate_single_alt(self):
        self.alt_hkl = True
        self.calculate_single_hkl()

    def calculate_single_hkl(self):
        worker = self.binding.new_worker(self.calculate_single_process)
        worker.connect_result(self.calculate_single_complete)
        worker.connect_finished(self.visualize)
        worker.connect_progress(self.vis_viewmodel.update_processing)
        worker.start()

    def calculate_single_complete(self, result):
        if result is not None:
            self.ep_peak_plot_instrument_bind.update_in_view(
                (self.model.gamma, self.model.nu, *result)
            )

    def calculate_single_process(self, progress):
        hkl_1 = self.peak_settings.get_hlk1()
        hkl_2 = self.peak_settings.get_hlk2()
        wavelength = self.params.get_wavelength()

        hkl = hkl_1 if not self.alt_hkl else hkl_2

        equiv = self.peak_settings.allow_equivalents
        pg = self.settings.point_group

        instrument = self.params.instrument
        mode = self.goniometers.current_mode
        axes, polarities = self.model.get_axes_polarities(instrument, mode)

        limits = self.goniometers.get_limits()

        if hkl_1 is not None and self.model.has_UB():
            progress("Initializing instrument", 5)

            self.create_instrument()

            progress("Instrument initialized! ", 10)

            progress("Calculating peak coverage", 15)

            gamma, nu, lamda = self.model.individual_peak(
                hkl,
                wavelength,
                axes,
                polarities,
                limits,
                equiv,
                pg,
            )

            progress("Peak calculated!", 0)

            return gamma, nu, lamda

        else:
            progress("Invalid parameters.", 0)

    def calculate_double(self):
        worker = self.binding.new_worker(self.calculate_double_process)
        worker.connect_result(self.calculate_double_complete)
        worker.connect_finished(self.visualize)
        worker.connect_progress(self.vis_viewmodel.update_processing)
        worker.start()

    def calculate_double_complete(self, result):
        if result is not None:
            self.ep_peak_plot_instrument_bind.update_in_view(
                (self.model.gamma, self.model.nu, *result)
            )

    def calculate_double_process(self, progress):
        hkl_1 = self.peak_settings.get_hlk1()
        hkl_2 = self.peak_settings.get_hlk2()
        wavelength = self.params.get_wavelength()

        equiv = self.peak_settings.allow_equivalents
        pg = self.settings.point_group

        instrument = self.params.instrument
        mode = self.goniometers.current_mode
        axes, polarities = self.model.get_axes_polarities(instrument, mode)

        limits = self.goniometers.get_limits()

        if hkl_1 is not None and hkl_2 is not None and self.model.has_UB():
            progress("Initializing instrument", 5)

            self.create_instrument()

            progress("Instrument initialized! ", 10)

            progress("Calculating peaks coverage", 15)

            peak_1, peak_2 = self.model.simultaneous_peaks(
                hkl_1, hkl_2, wavelength, axes, polarities, limits, equiv, pg
            )

            gamma_1, nu_1, lamda_1 = peak_1
            gamma_2, nu_2, lamda_2 = peak_2

            progress("Peaks calculated!", 0)

            return gamma_1, nu_1, lamda_1, gamma_2, nu_2, lamda_2

        else:
            progress("Invalid parameters.", 0)

    def update_peaks(self):
        self.peak_table.update_options(self.plan.get_number_of_orientations())
        angles_option = self.peak_table.angles_option
        if angles_option is not None:
            row = int(angles_option.split(":")[0]) - 1
            peak_list = self.model.generate_table(row)
            self.peak_table.from_list(peak_list)
            self.ep_peak_table_bind.update_in_view(self.peak_table)

    def process_peak_plot_event(self, horz, vert):
        self.peak_settings.horizontal = horz
        self.peak_settings.vertical = vert
        self.ep_peak_settings_bind.update_in_view(self.peak_settings)
        self.lookup_angle()

    def lookup_angle(self):
        gamma = self.peak_settings.horizontal
        nu = self.peak_settings.vertical

        vals = self.model.get_angles(gamma, nu)
        if vals is not None:
            angles, gamma, nu, lamda, gamma_alt, nu_alt, lamda_alt = vals
            self.peak_table.set_angles(angles)
            self.peak_settings.horizontal = gamma
            self.peak_settings.vertical = nu
            self.peak_settings.intersect = lamda
            self.peak_settings.horizontal_alt = gamma_alt
            self.peak_settings.vertical_alt = nu_alt
            self.peak_settings.intersect_alt = lamda_alt
            self.ep_peak_table_bind.update_in_view(self.peak_table)
            self.ep_peak_settings_bind.update_in_view(self.peak_settings)
            self.ep_peak_inst_bind.update_in_view(self.peak_settings)

    def delete_angles(self):
        rows = sorted(self.plan.plan_table_selected_rows, reverse=True)

        for i in rows:
            del self.plan.plan_table[i]

        if len(rows) > 0:
            self.model.delete_angles(rows)

        self.plan.plan_table_selected_rows = []
        self.ep_plan_bind.update_in_view(self.plan)

        self.visualize()
        self.update_peaks()

    def add_orientation(self):
        worker = self.binding.new_worker(self.add_orientation_process)
        worker.connect_result(self.add_orientation_complete)
        worker.connect_finished(self.visualize)
        worker.connect_progress(self.vis_viewmodel.update_processing)
        worker.start()

    def add_orientation_complete(self, result):
        angles, all_angles, free_angles = result

        comment = self.model.comment
        update_angles = []
        for angle, angle_name in zip(angles, all_angles):
            if angle_name in free_angles:
                update_angles.append(angle)

        title = self.plan.title
        self.plan.add_orientation(title, comment, update_angles)
        self.ep_plan_bind.update_in_view(self.plan)
        self.update_peaks()

    def add_orientation_process(self, progress):
        angles = self.peak_table.get_angles()
        free_angles = self.goniometers.get_free_angles()
        all_angles = self.goniometers.get_all_angles()

        wavelength = self.params.get_wavelength()
        d_min = self.params.d_min
        rows = self.plan.get_number_of_orientations()

        if len(angles) > 0:
            progress("Calculating reflections", 5)

            self.model.add_orientation(angles, wavelength, d_min, rows)

            progress("Reflections calculated!", 0)

            return angles, all_angles, free_angles

        else:
            progress("Invalid parameters.", 0)

    def update_selected_plan_table_rows(self):
        self.plan.update_selected_plan_table_rows()
        self.ep_plan_bind.update_in_view(self.plan)

    def select_all_plan_table_rows(self):
        self.plan.plan_table_selected_rows = list(
            range(self.plan.get_number_of_orientations())
        )
        self.ep_plan_bind.update_in_view(self.plan)

    def mesh_scan(self):
        worker = self.binding.new_worker(self.mesh_scan_process)
        worker.connect_result(self.mesh_scan_complete)
        worker.connect_finished(self.visualize)
        worker.connect_progress(self.vis_viewmodel.update_processing)
        worker.start()

    def mesh_scan_complete(self, result):
        title = self.plan.title
        if result is not None:
            for angles in result:
                self.plan.add_orientation(title, "Mesh Scan", angles)
            self.ep_plan_bind.update_in_view(self.plan)
            self.update_peaks()

    def get_mesh_angles(self):
        all_angles = self.goniometers.get_all_angles()
        n = len(all_angles)

        limits = self.goniometers.get_limits()
        angles = [1] * n

        for mesh_row in self.plan.mesh_table:
            ind = all_angles.index(mesh_row["motor"])
            limits[ind][0] = mesh_row["min"]
            limits[ind][1] = mesh_row["max"]
            angles[ind] = int(mesh_row["angle"])
        return limits, angles

    def mesh_scan_process(self, progress):
        mesh_angles = self.get_mesh_angles()
        free_angles = self.goniometers.get_free_angles()
        all_angles = self.goniometers.get_all_angles()

        wavelength = self.params.get_wavelength()
        d_min = self.params.d_min
        rows = self.plan.get_number_of_orientations()

        instrument = self.params.instrument
        mode = self.goniometers.current_mode
        axes, polarities = self.model.get_axes_polarities(instrument, mode)
        self.model.generate_axes(axes, polarities)

        progress("Initializing instrument", 5)

        self.create_instrument()

        if mesh_angles is not None:
            progress("Calculating reflections", 5)

            angles = self.model.add_mesh(
                mesh_angles, wavelength, d_min, rows, free_angles, all_angles
            )

            progress("Reflections calculated!", 0)

            return angles

        else:
            progress("Invalid parameters.", 0)

    def visualize(self):
        point_group = self.settings.point_group
        lattice_centering = self.settings.lattice_centering
        use = self.plan.get_orientations_to_use()
        d_min = self.params.d_min

        stats = self.model.calculate_statistics(
            point_group, lattice_centering, use, d_min
        )

        if stats is not None and self.model.has_UB() and self.draw_idle:
            self.draw_idle = False

            self.ep_statistics_bind.update_in_view(stats)

            peak_dict = self.model.get_coverage_info(point_group, lattice_centering)
            if peak_dict is not None:
                peak_dict["axis_limit"] = d_min
                self.ep_peak_bind.update_in_view(peak_dict)

            self.draw_idle = True

    def optimize_coverage(self):
        worker = self.binding.new_worker(self.optimize_coverage_process)
        worker.connect_result(self.optimize_coverage_complete)
        worker.connect_finished(self.visualize)
        worker.connect_progress(self.vis_viewmodel.update_processing)
        worker.start()

    def optimize_coverage_complete(self, result):
        title = self.plan.title
        if result is not None:
            for angles in result:
                self.plan.add_orientation(title, "CrystalPlan", angles)
            self.ep_plan_bind.update_in_view(self.plan)
            self.update_peaks()

    def optimize_coverage_process(self, progress):
        point_group = self.settings.point_group
        lattice_centering = self.settings.lattice_centering
        use = self.plan.get_orientations_to_use()
        opt = self.plan.get_optimized_settings()
        d_min = self.params.d_min
        wavelength = self.params.get_wavelength()
        n_orient = self.plan.settings

        n_elite = 2
        n_gener = 10
        n_indiv = 10
        mutation_rate = 0.15

        instrument = self.params.instrument
        mode = self.goniometers.current_mode
        axes = self.model.get_goniometer_axes(instrument, mode)
        limits = self.goniometers.get_limits()

        if self.model.has_UB():
            progress("Initializing instrument", 5)

            self.create_instrument()

            progress("Instrument initialized! ", 10)

            cp = self.model.crystal_plan(
                use,
                opt,
                axes,
                limits,
                wavelength,
                d_min,
                point_group,
                lattice_centering,
            )

            progress("Optimizing peaks coverage", 15)

            values = cp.optimize(n_orient, n_indiv, n_gener, n_elite, mutation_rate)

            progress("Peaks coverage optimized!", 0)

            return values

        else:
            progress("Invalid parameters.", 0)

    def update_plan(self):
        instrument = self.params.instrument
        cal = self.motors.detector_file
        mask = self.motors.mask_file
        mode = self.goniometers.current_mode
        settings = self.plan.get_all_settings()
        comments = [row["comment"] for row in self.plan.plan_table]
        counts = [row["wait_for"] for row in self.plan.plan_table]
        values = [row["value"] for row in self.plan.plan_table]
        use = self.plan.get_orientations_to_use()
        names = self.goniometers.get_free_angles()
        titles = [row["title"] for row in self.plan.plan_table]
        UB = self.model.get_UB()
        wavelength = self.params.get_wavelength()
        d_min = self.params.d_min
        crysal_system = self.settings.crystal_system
        point_group = self.settings.point_group
        lattice_centering = self.settings.lattice_centering
        motors = self.motors.motors_from_table()
        limits = self.goniometers.get_limits()
        pv = self.model.get_scan_log(instrument)
        table = pv, names, titles, settings, comments, counts, values, use
        self.model.create_plan(table)
        self.model.create_sample(instrument, mode, UB, wavelength, d_min)
        self.model.update_sample(crysal_system, point_group, lattice_centering)
        self.model.update_goniometer_motors(limits, motors, cal, mask)

    def save_CSV(self, filename):
        self.update_plan()
        self.model.save_plan(filename)

    def save_experiment(self, filename):
        self.update_plan()
        self.model.save_experiment(filename)

    def load_experiment(self, filename):
        plan, config, symm = self.model.load_experiment(filename)

        titles, settings, comments, counts, values, use = plan
        instrument, mode, wl, d_min, lims, vals, cal, mask = config
        cs, pg, lc = symm

        table = titles, settings, comments, counts, values, use

        self.params.instrument = instrument
        self.switch_instrument()
        self.goniometers.current_mode = mode
        self.vis_viewmodel.update_oriented_lattice()
        self.vis_viewmodel.set_transform(self.model.get_transform())
        self.params.set_wavelengths(wl)
        self.params.d_min = d_min
        self.goniometers.set_limits(lims)
        self.motors.set_motors(vals)
        self.motors.mask_file = mask
        self.motors.detector_file = cal
        self.settings.crystal_system = cs
        self.settings.point_group = pg
        self.settings.lattice_centering = lc
        self.switch_crystal()
        self.plan.load_settings(*table)
        self.ep_params_bind.update_in_view(self.params)
        self.ep_motors_bind.update_in_view(self.motors)
        self.ep_goniometers_bind.update_in_view(self.goniometers)
        self.ep_plan_bind.update_in_view(self.plan)
        self.peak_table.update_options(self.plan.get_number_of_orientations())
        self.add_settings()

    def add_settings(self):
        worker = self.binding.new_worker(self.add_settings_process)
        worker.connect_result(self.add_settings_complete)
        worker.connect_finished(self.visualize)
        worker.connect_progress(self.vis_viewmodel.update_processing)
        worker.start()

    def add_settings_complete(self, result):
        if result is not None:
            self.update_peaks()

    def add_settings_process(self, progress):
        wavelength = self.params.get_wavelength()
        d_min = self.params.d_min
        rows = self.plan.get_number_of_orientations()

        instrument = self.params.instrument
        mode = self.goniometers.current_mode
        axes, polarities = self.model.get_axes_polarities(instrument, mode)
        self.model.generate_axes(axes, polarities)
        limits = self.goniometers.get_limits()

        progress("Initializing instrument", 5)

        self.create_instrument()

        for row in range(rows):
            progress("Calculating settings", 90 // rows * (row + 1) + 5)

            angles = self.plan.get_angle_setting(row)

            setting = self.model.get_setting(angles, limits)

            self.model.add_orientation(setting, wavelength, d_min, row)

        progress("Settings calculated!", 0)

        return rows

    def process_settings_updates(self, results):
        for update in results.get("updated", []):
            match update:
                case "ub_path":
                    self.load_UB(self.settings.ub_path)
                case "crystal_system":
                    self.switch_crystal()
                case "point_group":
                    self.switch_group()
                case "lattice_centering":
                    self.switch_centering()

    def process_params_updates(self, results):
        for update in results.get("updated", []):
            match update:
                case "instrument":
                    self.switch_instrument()
                case "wl_min":
                    self.update_wavelength()

    def process_peak_table_updates(self, results):
        if key_updated("angles_option", False, results):
            self.update_peaks()

    def process_goniometers_updates(self, results):
        if key_updated("current_mode", False, results):
            self.update_goniometer()
        elif key_updated("goniometer_table", True, results):
            self.update_plan_from_goniometers()

    def process_plan_updates(self, results):
        for update in results.get("updated", []):
            if "use" in update:
                self.visualize()
                return
            if update == "experiment_path":
                self.load_experiment(self.plan.experiment_path)

    def process_motors_updates(self, results):
        if key_updated("mask_file", False, results) or key_updated(
            "detector_file", False, results
        ):
            self.ep_motors_bind.update_in_view(self.motors)

    def set_vis_viewmodel(self, vis_viewmodel: NeuXtalVizViewModel):
        self.vis_viewmodel = vis_viewmodel

    def load_UB(self, filename: str):
        self.model.load_UB(filename)
        self.vis_viewmodel.update_oriented_lattice()
        self.vis_viewmodel.set_transform(self.model.get_transform())
