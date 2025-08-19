from enum import Enum
from typing import Optional, List, Dict

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
    crystal_system: CrystalSystemOptions = Field(
        default=CrystalSystemOptions.triclinic, title="Crystal System"
    )
    point_groups: List[str] = []
    point_group: Optional[str] = Field(default=None, title="Point Group")
    lattice_centerings: List[str] = []
    lattice_centering: Optional[str] = Field(default=None, title="Lattice Centering")


class EPParams(BaseModel):
    instrument: EPInstrumentOptions = Field(default=EPInstrumentOptions.topaz, title="Instrument")
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


class EPGoniometers(BaseModel):
    goniometer_table: List[Dict[str, str | float | bool]] = []
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

    def get_limits(self):
        limits = [[row["min"], row["max"]] for row in self.goniometer_table]
        return limits


class EPPlan(BaseModel):
    counting_options: Optional[List[str]] = Field(default=None, title="Options")
    counting_option: Optional[str] = Field(default=None)
    title: str = Field(default="Scan Title", title="Title")
    count: float = Field(default=1.0, title="Count", ge=0.001, le=10000)
    settings: int = Field(default=20, title="Count", ge=1, le=1000)
    plan_table: List[Dict[str, str | float | int | bool]] = []
    plan_table_headers: List[Dict[str, str]] = []
    mesh_table: List[Dict[str, str | float | int | bool]] = []
    mesh_table_headers: List[Dict[str, str]] = [
        {"key": "motor", "title": "Motor"},
        {"key": "min", "title": "Min"},
        {"key": "max", "title": "Max"},
        {"key": "angles", "title": "Angles"},
    ]

    def add_orientation(self, title, comment, angles):
        table_row = {"title": title, "comment": comment, "wait_for": self.counting_option, "value": self.count,
                     "use": True}
        for i, angle in enumerate(angles):
            table_row[f"angle{i}"] = angle
        self.plan_table.append(table_row)

    def update_plan_headers(self, title, goniometers: EPGoniometers):
        free = []
        for row in goniometers.goniometer_table:
            motor, amin, amax = row["motor"], row["min"], row["max"]
            if amin != amax:
                free.append(motor)
        self.plan_table_headers = ([{"key": "title", "title": title}] +
                                   [{"key": f"angle{i}", "title": motor} for i, motor in enumerate(free)] +
                                   [{"key": "comment", "title": "Comment"},
                                    {"key": "wait_for", "title": "Wait For"},
                                    {"key": "value", "title": "Value"},
                                    {"key": "use", "title": "Use"},
                                    ])

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


class EPMotors(BaseModel):
    mask_file: str = Field(default="", title="Mask File")
    detector_file: str = Field(default="", title="Detector File")
    motor_table: List[Dict[str, str | float]] = []
    motor_table_headers: List[Dict[str, str]] = [
        {"key": "motor", "title": "Motor"},
        {"key": "value", "title": "Value"},
    ]

    def table_from_motors(self, motors):
        self.motor_table = []
        for row in motors:
            table_row = {"motor": row[0], "value": row[1]}
            self.motor_table.append(table_row)

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
        self.draw_idle = True
        return
        #        self.view.connect_switch_instrument(self.switch_instrument)
        #        self.view.connect_update_goniometer(self.update_goniometer)
        #        self.view.connect_switch_crystal(self.switch_crystal)
        #        self.view.connect_switch_point_group(self.switch_group)
        #        self.view.connect_switch_lattice_centering(self.switch_centering)
        #        self.view.connect_wavelength(self.update_wavelength)
        #        self.view.connect_load_mask(self.load_mask)
        #        self.view.connect_load_detector(self.load_detector)

        # self.view.connect_optimize(self.optimize_coverage)
        self.view.connect_mesh(self.mesh_scan)
        self.view.connect_calculate_single(self.calculate_single)
        self.view.connect_calculate_double(self.calculate_double)
        self.view.connect_calculate_single_alt(self.calculate_single_alt)
        self.view.connect_add_orientation(self.add_orientation)
        self.view.connect_delete_angles(self.delete_angles)
        self.view.connect_save_CSV(self.save_CSV)
        self.view.connect_save_experiment(self.save_experiment)
        self.view.connect_load_experiment(self.load_experiment)
        self.view.connect_peak_table(self.update_peaks)

        self.view.connect_roi_ready(self.lookup_angle)
        self.view.connect_viz_ready(self.visualize)

        self.view.connect_update(self.view.update_counting)
        self.view.connect_highlight_angles(self.view.highlight_angles)

        self.switch_instrument()
        self.switch_crystal()

        self.draw_idle = True

    def get_load_path(self):
        inst = self.params.instrument
        return self.model.get_calibration_file_path(inst)

    def switch_instrument(self):
        instrument = self.params.instrument

        self.params.set_wavelengths(self.model.get_wavelength(instrument))
        motors = self.model.get_motors(instrument)
        self.motors.table_from_motors(motors)
        self.goniometers.modes = self.model.get_modes(instrument)
        if self.goniometers.modes and self.goniometers.current_mode not in self.goniometers.modes:
            self.goniometers.current_mode = self.goniometers.modes[0]
        goniometers = self.model.get_goniometers(instrument, self.goniometers.modes[0])
        self.goniometers.table_from_goniometers(goniometers)
        self.plan.counting_options = self.model.get_counting_options(instrument)
        if self.plan.counting_options and self.plan.counting_option not in self.plan.counting_options:
            self.plan.counting_option = self.plan.counting_options[0]

        self.ep_params_bind.update_in_view(self.params)
        self.ep_motors_bind.update_in_view(self.motors)

        self.ep_goniometers_bind.update_in_view(self.goniometers)
        self.update_plan_from_goniometers()
        self.model.remove_instrument()

    def switch_crystal(self):
        point_groups = self.model.get_crystal_system_point_groups(self.settings.crystal_system)
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
        self.goniometers.table_from_goniometers(self.model.get_goniometers(self.params.instrument,
                                                                           self.goniometers.current_mode))
        self.update_plan_from_goniometers()
        #        motors = self.model.get_motors(self.params.instrument)
        #        self.motors.table_from_motors(motors)
        #        self.ep_motors_bind.update_in_view(self.motors)

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
        worker = self.view.worker(self.calculate_single_process)
        worker.connect_result(self.calculate_single_complete)
        worker.connect_finished(self.visualize)
        worker.connect_progress(self.update_processing)

        self.view.start_worker_pool(worker)

    def calculate_single_complete(self, result):
        if result is not None:
            self.view.plot_instrument(self.model.gamma, self.model.nu, *result)

    def calculate_single_process(self, progress):
        hkl_1, hkl_2 = self.view.get_input_hkls()
        wavelength = self.view.get_wavelength()

        hkl = hkl_1 if not self.alt_hkl else hkl_2

        equiv = self.view.use_equivalents()
        pg = self.view.get_point_group()

        instrument = self.view.get_instrument()
        mode = self.view.get_mode()
        axes, polarities = self.model.get_axes_polarities(instrument, mode)

        limits = self.view.get_goniometer_limits()

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
        worker = self.view.worker(self.calculate_double_process)
        worker.connect_result(self.calculate_double_complete)
        worker.connect_finished(self.visualize)
        worker.connect_progress(self.update_processing)

        self.view.start_worker_pool(worker)

    def calculate_double_complete(self, result):
        if result is not None:
            self.view.plot_instrument_alternate(
                self.model.gamma, self.model.nu, *result
            )

    def calculate_double_process(self, progress):
        hkl_1, hkl_2 = self.view.get_input_hkls()
        wavelength = self.view.get_wavelength()

        equiv = self.view.use_equivalents()
        pg = self.view.get_point_group()

        instrument = self.view.get_instrument()
        mode = self.view.get_mode()
        axes, polarities = self.model.get_axes_polarities(instrument, mode)

        limits = self.view.get_goniometer_limits()

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
        row = self.view.get_peak_list()
        if row is not None:
            peak_list = self.model.generate_table(row)
            self.view.update_peaks_table(peak_list)

    def lookup_angle(self):
        gamma = self.view.get_horizontal()
        nu = self.view.get_vertical()

        vals = self.model.get_angles(gamma, nu)
        if vals is not None:
            angles, gamma, nu, lamda, gamma_alt, nu_alt, lamda_alt = vals
            self.view.set_angles(angles)
            self.view.set_horizontal(gamma)
            self.view.set_vertical(nu)
            self.view.set_intersect(lamda)
            self.view.set_horizontal_alternate(gamma_alt)
            self.view.set_vertical_alternate(nu_alt)
            self.view.set_intersect_alternate(lamda_alt)
            self.view.update_inst()

    def delete_angles(self):
        rows = self.view.delete_angles()

        if len(rows) > 0:
            self.model.delete_angles(rows)

        self.visualize()
        self.update_peaks()

    def add_orientation(self):
        worker = self.view.worker(self.add_orientation_process)
        worker.connect_result(self.add_orientation_complete)
        worker.connect_finished(self.visualize)
        worker.connect_progress(self.update_processing)

        self.view.start_worker_pool(worker)

    def add_orientation_complete(self, result):
        angles, all_angles, free_angles = result

        comment = self.model.comment
        update_angles = []
        for angle, angle_name in zip(angles, all_angles):
            if angle_name in free_angles:
                update_angles.append(angle)

        title = self.view.get_title()
        self.plan.add_orientation(title, comment, update_angles)
        self.update_peaks()

    def add_orientation_process(self, progress):
        angles = self.view.get_angles()
        free_angles = self.view.get_free_angles()
        all_angles = self.view.get_all_angles()

        wavelength = self.view.get_wavelength()
        d_min = self.view.get_d_min()
        rows = self.view.get_number_of_orientations()

        if len(angles) > 0:
            progress("Calculating reflections", 5)

            self.model.add_orientation(angles, wavelength, d_min, rows)

            progress("Reflections calculated!", 0)

            return angles, all_angles, free_angles

        else:
            progress("Invalid parameters.", 0)

    def mesh_scan(self):
        worker = self.view.worker(self.mesh_scan_process)
        worker.connect_result(self.mesh_scan_complete)
        worker.connect_finished(self.visualize)
        worker.connect_progress(self.update_processing)

        self.view.start_worker_pool(worker)

    def mesh_scan_complete(self, result):
        title = self.view.get_title()
        if result is not None:
            for angles in result:
                self.plan.add_orientation(title, "Mesh Scan", angles)
            self.update_peaks()

    def mesh_scan_process(self, progress):
        mesh_angles = self.view.get_mesh_angles()
        free_angles = self.view.get_free_angles()
        all_angles = self.view.get_all_angles()

        wavelength = self.view.get_wavelength()
        d_min = self.view.get_d_min()
        rows = self.view.get_number_of_orientations()

        instrument = self.view.get_instrument()
        mode = self.view.get_mode()
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

            peak_dict = self.model.get_coverage_info(
                point_group, lattice_centering
            )
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
            # todo:
#            self.update_peaks()

    def optimize_coverage_process(self, progress):
        point_group = self.settings.point_group
        lattice_centering = self.settings.lattice_centering
        use = self.plan.get_orientations_to_use()
        opt = self.plan.get_optimized_settings()
        d_min = self.params.d_min
        wavelength = [self.params.wl_min, self.params.wl_max]
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

            values = cp.optimize(
                n_orient, n_indiv, n_gener, n_elite, mutation_rate
            )

            progress("Peaks coverage optimized!", 0)

            return values

        else:
            progress("Invalid parameters.", 0)

    def update_plan(self):
        instrument = self.view.get_instrument()
        cal = self.view.get_detector_calibration()
        mask = self.view.get_mask()
        mode = self.view.get_mode()
        settings = self.view.get_all_settings()
        comments = self.view.get_all_comments()
        counts = self.view.get_all_countings()
        values = self.view.get_all_values()
        use = self.plan.get_orientations_to_use()
        names = self.view.get_free_angles()
        titles = self.view.get_all_titles()
        UB = self.model.get_UB()
        wavelength = self.view.get_wavelength()
        d_min = self.view.get_d_min()
        crysal_system = self.view.get_crystal_system()
        point_group = self.view.get_point_group()
        lattice_centering = self.view.get_lattice_centering()
        motors = self.view.get_motors()
        limits = self.view.get_goniometer_limits()
        pv = self.model.get_scan_log(instrument)
        table = pv, names, titles, settings, comments, counts, values, use
        self.model.create_plan(table)
        self.model.create_sample(instrument, mode, UB, wavelength, d_min)
        self.model.update_sample(crysal_system, point_group, lattice_centering)
        self.model.update_goniometer_motors(limits, motors, cal, mask)

    def save_CSV(self):
        filename = self.view.save_CSV_file_dialog()

        if filename:
            self.update_plan()
            self.model.save_plan(filename)

    def save_experiment(self):
        filename = self.view.save_experiment_file_dialog()

        if filename:
            self.update_plan()
            self.model.save_experiment(filename)

    def load_experiment(self):
        filename = self.view.load_experiment_file_dialog()

        if filename:
            plan, config, symm = self.model.load_experiment(filename)

            titles, settings, comments, counts, values, use = plan
            instrument, mode, wl, d_min, lims, vals, cal, mask = config
            cs, pg, lc = symm

            table = titles, settings, comments, counts, values, use

            self.view.set_instrument(instrument)
            self.switch_instrument()
            self.view.set_mode(mode)
            self.update_oriented_lattice()
            self.view.set_transform(self.model.get_transform())
            self.view.set_wavelength(wl)
            self.view.set_d_min(d_min)
            self.view.set_goniometer_limits(lims)
            self.view.set_motors(vals)
            self.view.set_detector_calibration(cal)
            self.view.set_mask(mask)
            self.view.set_crystal_system(cs)
            self.switch_crystal()
            self.view.set_point_group(pg)
            self.switch_group()
            self.view.set_lattice_centering(lc)
            self.view.add_settings(*table)
            self.add_settings()

    def add_settings(self):
        worker = self.view.worker(self.add_settings_process)
        worker.connect_result(self.add_settings_complete)
        worker.connect_finished(self.visualize)
        worker.connect_progress(self.update_processing)

        self.view.start_worker_pool(worker)

    def add_settings_complete(self, result):
        if result is not None:
            self.update_peaks()

    def add_settings_process(self, progress):
        wavelength = self.view.get_wavelength()
        d_min = self.view.get_d_min()
        rows = self.view.get_number_of_orientations()

        instrument = self.view.get_instrument()
        mode = self.view.get_mode()
        axes, polarities = self.model.get_axes_polarities(instrument, mode)
        self.model.generate_axes(axes, polarities)
        limits = self.view.get_goniometer_limits()

        progress("Initializing instrument", 5)

        self.create_instrument()

        for row in range(rows):
            progress("Calculating settings", 90 // rows * (row + 1) + 5)

            angles = self.view.get_angle_setting(row)

            setting = self.model.get_setting(angles, limits)

            self.model.add_orientation(setting, wavelength, d_min, row)

        progress("Settings calculated!", 0)

        return rows

    def process_settings_updates(self, results):
        for update in results.get("updated", []):
            match update:
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

    def process_goniometers_updates(self, results):
        if key_updated("current_mode", False, results):
            self.update_goniometer()
        elif key_updated("goniometer_table", True, results):
            self.update_plan_from_goniometers()

    def process_plan_updates(self, results):
        print(results)
        pass

    def process_motors_updates(self, results):
        if key_updated("mask_file", False, results) or key_updated("detector_file", False, results):
            self.ep_motors_bind.update_in_view(self.motors)

    def set_vis_viewmodel(self, vis_viewmodel: NeuXtalVizViewModel):
        self.vis_viewmodel = vis_viewmodel

    def load_UB(self, filename: str):
        self.model.load_UB(filename)
        self.vis_viewmodel.update_oriented_lattice()
        self.vis_viewmodel.set_transform(self.model.get_transform())
