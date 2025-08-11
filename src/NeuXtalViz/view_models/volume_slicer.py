from decimal import Decimal
from enum import Enum
from typing import Optional

import numpy as np
from nova.mvvm.interface import BindingInterface
from pydantic import BaseModel, Field

from NeuXtalViz.models.volume_slicer import VolumeSlicerModel
from NeuXtalViz.view_models.base_view_model import NeuXtalVizViewModel


CMAPS = {
    "Sequential": "viridis",
    "Binary": "binary",
    "Diverging": "bwr",
    "Rainbow": "turbo",
    "Modified": "modified",
}

OPACITIES = {
    "Linear": {"Low->High": "linear", "High->Low": "linear_r"},
    "Geometric": {"Low->High": "geom", "High->Low": "geom_r"},
    "Sigmoid": {"Low->High": "sigmoid", "High->Low": "sigmoid_r"},
}


class AxisOptions(str, Enum):
    linear = "Linear"
    log = "Log"


class OpacityOptions(str, Enum):
    linear = "Linear"
    geometric = "Geometric"
    sigmoid = "Sigmoid"


class OpacityRangeOptions(str, Enum):
    low_to_high = "Low->High"
    high_to_low = "High->Low"


class ClipTypeOptions(str, Enum):
    minmax = "Min/Max"
    normal = "μ±3×σ"
    boxplot = "Q₃/Q₁±1.5×IQR"


class ColorbarOptions(str, Enum):
    sequential = "Sequential"
    rainbow = "Rainbow"
    binary = "Binary"
    diverging = "Diverging"
    modified = "Modified"


class SlicePlaneOptions(str, Enum):
    one_half = "Axis 1/2"
    one_third = "Axis 1/3"
    two_thirds = "Axis 2/3"


class CutLineOptions(str, Enum):
    axis_one = "Axis 1"
    axis_two = "Axis 2"


class VolumeControls(BaseModel):
    cbar: ColorbarOptions = Field(
        default=ColorbarOptions.sequential, title="Color Scale"
    )
    clip_type: ClipTypeOptions = Field(
        default=ClipTypeOptions.boxplot, title="Clip Type"
    )
    opacity: OpacityOptions = Field(default=OpacityOptions.linear, title="Opacity")
    opacity_range: OpacityRangeOptions = Field(
        default=OpacityRangeOptions.low_to_high, title="Opacity Range"
    )
    idle: bool = Field(default=True)
    scale: AxisOptions = Field(default=AxisOptions.linear, title="Scale")


class SliceControls(BaseModel):
    clip_type: ClipTypeOptions = Field(
        default=ClipTypeOptions.boxplot, title="Clip Type"
    )
    idle: bool = Field(default=True)
    plane: SlicePlaneOptions = Field(default=SlicePlaneOptions.one_half, title="Plane")
    value: Optional[Decimal] = Field(
        default=Decimal(0.0), ge=-100.0, le=100.0, decimal_places=5, title="Slice"
    )
    thickness: Optional[Decimal] = Field(
        default=Decimal(0.1), ge=0.0001, le=100.0, decimal_places=5, title="Thickness"
    )
    scale: AxisOptions = Field(default=AxisOptions.linear, title="Scale")
    vlims: list[float] = Field(default=[0.0, 0.0])
    vmin: Optional[Decimal] = Field(
        default=Decimal(0.0), ge=-1e32, le=1e32, decimal_places=6, title="Color Min"
    )
    vmax: Optional[Decimal] = Field(
        default=Decimal(1.0), ge=-1e32, le=1e32, decimal_places=6, title="Color Max"
    )
    xmin: Optional[Decimal] = Field(
        default=Decimal(0.0), ge=-1e32, le=1e32, decimal_places=6, title="X Min"
    )
    xmax: Optional[Decimal] = Field(
        default=Decimal(0.0), ge=-1e32, le=1e32, decimal_places=6, title="X Max"
    )
    ymin: Optional[Decimal] = Field(
        default=Decimal(0.0), ge=-1e32, le=1e32, decimal_places=6, title="Y Min"
    )
    ymax: Optional[Decimal] = Field(
        default=Decimal(0.0), ge=-1e32, le=1e32, decimal_places=6, title="Y Max"
    )


class CutControls(BaseModel):
    idle: bool = Field(default=True)
    line: CutLineOptions = Field(default=CutLineOptions.axis_one, title="Line")
    thickness: Optional[Decimal] = Field(
        default=Decimal(0.1), ge=0.0001, le=100.0, decimal_places=5, title="Thickness"
    )
    scale: AxisOptions = Field(default=AxisOptions.linear, title="Scale")
    show: bool = Field(default=False)
    value: Optional[Decimal] = Field(
        default=Decimal(0.0), ge=-100.0, le=100.0, decimal_places=5, title="Cut"
    )


class VolumeSlicerViewModel:
    def __init__(self, model: VolumeSlicerModel, binding: BindingInterface):
        self.model = model
        self.binding = binding

        self.volume = VolumeControls()
        self.slice = SliceControls()
        self.cut = CutControls()

        self.volume_bind = binding.new_bind(
            self.volume, callback_after_update=self.on_volume_update
        )
        self.slice_bind = binding.new_bind(
            self.slice, callback_after_update=self.on_slice_update
        )
        self.cut_bind = binding.new_bind(
            self.cut, callback_after_update=self.on_cut_update
        )

        self.add_histo_bind = binding.new_bind()
        self.add_slice_bind = binding.new_bind()
        self.add_cut_bind = binding.new_bind()
        self.colorbar_lim_bind = binding.new_bind()
        self.cut_lim_bind = binding.new_bind()
        self.slice_lim_bind = binding.new_bind()

    def add_histo(self, result):
        histo, normal, norm, value, trans = result
        opacity = OPACITIES[self.volume.opacity][self.volume.opacity_range]
        log_scale = self.volume.scale == AxisOptions.log
        cmap = CMAPS[self.volume.cbar]

        self.norm = np.array(norm).copy()
        self.P_inv = np.linalg.inv(histo["projection"])

        self.add_histo_bind.update_in_view(
            (histo, normal, norm, value, opacity, log_scale, cmap)
        )

    def add_slice(self, slice_dict):
        cmap = CMAPS[self.volume.cbar]
        scale = self.slice.scale.lower()

        self.add_slice_bind.update_in_view((slice_dict, cmap, scale))

    def add_cut(self, cut_dict):
        line = self.cut.line
        scale = self.cut.scale.lower()
        thickness = float(self.cut.thickness)

        self.add_cut_bind.update_in_view((cut_dict, line, scale, thickness))

    def cut_data(self):
        worker = self.binding.new_worker(self.cut_data_process)
        worker.connect_result(self.cut_data_complete)
        worker.connect_finished(self.vis_viewmodel.update_complete)
        worker.connect_progress(self.vis_viewmodel.update_processing)
        worker.start()

    def cut_data_complete(self, result):
        if result is not None:
            self.add_cut(result)

        self.cut.idle = True

    def cut_data_process(self, progress):
        if self.cut.idle and self.model.is_sliced():
            self.cut.idle = False

            value = float(self.cut.value)
            thick = float(self.cut.thickness)

            axis = self.get_axis()

            if value is not None and thick is not None:
                progress("Processing...", 1)

                progress("Updating cut...", 50)

                progress("Data cut!", 100)

                cut_histo = self.model.get_cut_info(axis, value, thick)

                return cut_histo

    def get_axis(self):
        axis = [1 if not norm else 0 for norm in self.get_normal()]
        ind = [i for i, ax in enumerate(axis) if ax == 1]

        line_cut = self.cut.line

        if line_cut == CutLineOptions.axis_one:
            axis[ind[0]] = 0
        else:
            axis[ind[1]] = 0

        return axis

    def get_clip_method(self, object):
        ctype = object.clip_type

        if ctype == ClipTypeOptions.normal:
            method = "normal"
        elif ctype == ClipTypeOptions.boxplot:
            method = "boxplot"
        else:
            method = None

        return method

    def get_normal(self):
        slice_plane = self.slice.plane

        if slice_plane == SlicePlaneOptions.one_half:
            norm = [0, 0, 1]
        elif slice_plane == SlicePlaneOptions.one_third:
            norm = [0, 1, 0]
        else:
            norm = [1, 0, 0]

        return norm

    def init_view(self) -> None:
        self.volume_bind.update_in_view(self.volume)
        self.slice_bind.update_in_view(self.slice)
        self.cut_bind.update_in_view(self.cut)

    def interaction_callback(self, caller, event):
        orig = caller.GetOrigin()
        # norm = caller.GetNormal()

        # norm /= np.linalg.norm(norm)
        # norm = self.norm

        ind = np.array(self.norm).tolist().index(1)

        value = np.dot(self.P_inv, orig)[ind]

        self.slice.value = Decimal(value)
        self.slice_bind.update_in_view(self.slice)

        self.update_slice()

    def load_NXS(self, filename: str) -> None:
        worker = self.binding.new_worker(self.load_NXS_process, filename)
        worker.connect_result(self.load_NXS_complete)
        worker.connect_finished(self.vis_viewmodel.update_complete)
        worker.connect_progress(self.vis_viewmodel.update_processing)
        worker.start()

    def load_NXS_complete(self, result=None):
        self.vis_viewmodel.update_oriented_lattice()
        self.redraw_data()

    def load_NXS_process(self, filename, progress):
        progress("Processing...", 1)

        progress("Loading NeXus file...", 10)

        self.model.load_md_histo_workspace(filename)

        progress("Loading NeXus file...", 50)

        progress("Loading NeXus file...", 80)

        progress("NeXus file loaded!", 100)

    def on_cut_update(self, results):
        for update in results.get("updated", []):
            match update:
                case "line" | "value" | "thickness" | "scale":
                    self.update_cut()

    def on_slice_update(self, results):
        for update in results.get("updated", []):
            match update:
                case "plane":
                    self.redraw_data()
                case "value" | "thickness" | "scale" | "clip_type":
                    self.update_slice()
                case "xmin" | "xmax" | "ymin" | "ymax":
                    self.update_limits()
                case "vmin" | "vmax":
                    if self.slice.vmin > self.slice.vmax:
                        self.slice.vmin = self.slice.vmax
                        self.slice_bind.update_in_view(self.slice)
                    self.update_cvals()

    def on_volume_update(self, results):
        for update in results.get("updated", []):
            match update:
                case "scale" | "opacity" | "opacity_range" | "clip_type" | "cbar":
                    self.redraw_data()

    def redraw_data(self):
        worker = self.binding.new_worker(self.redraw_data_process)
        worker.connect_result(self.redraw_data_complete)
        worker.connect_finished(self.vis_viewmodel.update_complete)
        worker.connect_progress(self.vis_viewmodel.update_processing)
        worker.start()

    def redraw_data_complete(self, result):
        if result is not None:
            self.add_histo(result)
            self.vis_viewmodel.update_axes()
            self.vis_viewmodel.update_projection()

        self.volume.idle = True
        self.update_slice()

    def redraw_data_process(self, progress):
        if self.volume.idle and self.model.is_histo_loaded():
            self.volume.idle = False

            progress("Processing...", 1)

            progress("Updating volume...", 20)

            norm = self.get_normal()

            histo = self.model.get_histo_info(norm)

            data = histo["signal"]

            data = self.model.calculate_clim(data, self.get_clip_method(self.volume))

            progress("Updating volume...", 50)

            histo["signal"] = data

            value = float(self.slice.value)

            normal = -self.model.get_normal_plane(norm)

            # origin = self.model.get_normal('[hkl]', orig)

            if value is not None:
                progress("Volume drawn!", 100)

                return histo, normal, norm, value, self.model.get_transform()

            else:
                progress("Invalid parameters.", 0)

    def save_cut(self, filename):
        if self.model.is_cut():
            self.model.save_cut(filename)

    def save_slice(self, filename):
        if self.model.is_sliced():
            self.model.save_slice(filename)

    def set_cut_field(self, name, value, skip_update=False):
        match name:
            case "line":
                self.cut.line = CutLineOptions(value)
            case "scale":
                self.cut.scale = AxisOptions(value)
            case "show":
                self.cut.show = True
            case "thickness":
                self.cut.thickness = Decimal(value)
            case "value":
                self.cut.value = Decimal(value)

        if not skip_update:
            self.cut_bind.update_in_view(self.cut)
            self.update_cut()

    def set_slice_field(self, name, value):
        needs_update = False
        match name:
            case "clip_type":
                self.slice.clip_type = value
                needs_update = True
            case "plane":
                self.slice.plane = SlicePlaneOptions(value)
                self.redraw_data()
            case "scale":
                self.slice.scale = AxisOptions(value)
                needs_update = True
            case "thickness":
                self.slice.thickness = Decimal(value)
                needs_update = True
            case "value":
                self.slice.value = Decimal(value)
                needs_update = True
            case "vlims":
                self.slice.vlims = value
            case "vmax":
                if isinstance(value, int):
                    self.slice.vmax = Decimal(
                        self.slice.vlims[0]
                        + (self.slice.vlims[1] - self.slice.vlims[0]) * value / 100
                    )
                else:
                    self.slice.vmax = Decimal(value)

                if self.slice.vmax < self.slice.vmin:
                    self.slice.vmin = self.slice.vmax

                self.update_cvals()
            case "vmin":
                if isinstance(value, int):
                    self.slice.vmin = Decimal(
                        self.slice.vlims[0]
                        + (self.slice.vlims[1] - self.slice.vlims[0]) * value / 100
                    )
                else:
                    self.slice.vmin = Decimal(value)

                if self.slice.vmin > self.slice.vmax:
                    self.slice.vmax = self.slice.vmin

                self.update_cvals()
            case "xmax":
                self.slice.xmax = Decimal(value)
                self.update_limits()
            case "xmin":
                self.slice.xmin = Decimal(value)
                self.update_limits()
            case "ymax":
                self.slice.ymax = Decimal(value)
                self.update_limits()
            case "ymin":
                self.slice.ymin = Decimal(value)
                self.update_limits()

        self.slice_bind.update_in_view(self.slice)
        if needs_update:
            self.update_slice()

    def set_volume_field(self, name, value):
        match name:
            case "cbar":
                self.volume.cbar = value
            case "clip_type":
                self.volume.clip_type = ClipTypeOptions(value)
            case "opacity":
                self.volume.opacity = OpacityOptions(value)
            case "opacity_range":
                self.volume.opacity_range = OpacityRangeOptions(value)
            case "scale":
                self.volume.scale = AxisOptions(value)

        self.volume_bind.update_in_view(self.volume)
        self.redraw_data()

    def set_vis_viewmodel(self, vis_viewmodel: NeuXtalVizViewModel):
        self.vis_viewmodel = vis_viewmodel

    def slice_data(self):
        worker = self.binding.new_worker(self.slice_data_process)
        worker.connect_result(self.slice_data_complete)
        worker.connect_finished(self.vis_viewmodel.update_complete)
        worker.connect_progress(self.vis_viewmodel.update_processing)
        worker.start()

    def slice_data_complete(self, result):
        if result is not None:
            self.add_slice(result)

        self.slice.idle = True
        self.update_cut()

    def slice_data_process(self, progress):
        if self.slice.idle and self.model.is_histo_loaded():
            self.slice.idle = False

            norm = self.get_normal()

            thick = float(self.slice.thickness)
            value = float(self.slice.value)

            if thick is not None and value is not None:
                progress("Processing...", 1)

                progress("Updating slice...", 50)

                slice_histo = self.model.get_slice_info(norm, value, thick)

                data = slice_histo["signal"]

                data = self.model.calculate_clim(data, self.get_clip_method(self.slice))

                slice_histo["signal"] = data

                progress("Data sliced!", 100)

                return slice_histo

    def update_cut(self):
        if self.model.is_histo_loaded():
            self.cut_data()

    def update_cvals(self):
        vmin = float(self.slice.vmin)
        vmax = float(self.slice.vmax)
        if vmin is not None and vmax is not None:
            if vmin <= 0 and self.slice.scale == "log":
                vmin = vmax / 10
            self.colorbar_lim_bind.update_in_view((vmin, vmax))

    def update_limits(self):
        xmin = float(self.slice.xmin)
        xmax = float(self.slice.xmax)
        ymin = float(self.slice.ymin)
        ymax = float(self.slice.ymax)

        if (
            xmin is not None
            and xmax is not None
            and ymin is not None
            and ymax is not None
        ):
            if xmin < xmax and ymin < ymax:
                xlim = [xmin, xmax]
                ylim = [ymin, ymax]
                self.slice_lim_bind.update_in_view((xlim, ylim))
                line_cut = self.cut.line
                lim = xlim if line_cut == CutLineOptions.axis_one else ylim
                self.cut_lim_bind.update_in_view(lim)

    def update_slice(self):
        if self.model.is_histo_loaded():
            self.slice_data()
