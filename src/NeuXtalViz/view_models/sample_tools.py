from enum import Enum
from typing import Any, Dict, List

import numpy as np
from pydantic import BaseModel, Field

from NeuXtalViz.view_models.base_view_model import NeuXtalVizViewModel
from NeuXtalViz.models.sample_tools import SampleModel


class FaceIndices(BaseModel):
    hu: float = Field(default=0)
    ku: float = Field(default=0)
    lu: float = Field(default=1)
    hv: float = Field(default=1)
    kv: float = Field(default=0)
    lv: float = Field(default=0)

    def get_vectors(self):
        return (self.hu, self.ku, self.lu), (self.hv, self.kv, self.lv)


class Goniometer(BaseModel):
    name: str = Field(default="")
    x: float = Field(default=0)
    y: float = Field(default=0)
    z: float = Field(default=0)
    sense: float = Field(default=0)
    angle: float = Field(default=0.0)


class Goniometers(BaseModel):
    goniometers: List[Goniometer] = Field(default=[])

    def get_list(self):
        return [[g.name, g.x, g.y, g.z, g.sense, g.angle] for g in self.goniometers]


class MaterialParameters(BaseModel):
    chemical_formula: str = Field(default="")
    z_parameter: float = Field(default=0.0, title="Z")
    volume: float = Field(default=0.0, title="Ω")


class SampleShapeOptions(str, Enum):
    cylinder = "Cylinder"
    plate = "Plate"
    sphere = "Sphere"


class Sample(BaseModel):
    height: float = Field(default=0.50, title="Height")
    path: str = Field(default="")
    shape: SampleShapeOptions = Field(default=SampleShapeOptions.sphere, title="Shape")
    thickness: float = Field(default=0.50, title="Thickness")
    width: float = Field(default=0.50, title="Width")

    def get_params_list(self):
        return [self.width, self.height, self.thickness]


class SampleViewModel:
    def __init__(self, model: SampleModel, binding):
        self.model = model

        self.sample = Sample()
        self.sample_bind = binding.new_bind(
            self.sample, callback_after_update=self.on_sample_update
        )

        self.goniometers = Goniometers()
        self.goniometer_bind = binding.new_bind(self.goniometers)

        self.material_parameters = MaterialParameters()
        self.material_parameters_bind = binding.new_bind(self.material_parameters)

        self.face_indices = FaceIndices()
        self.face_indices_bind = binding.new_bind(self.face_indices)

        self.constraints_bind = binding.new_bind()

        # self.view.connect_row_highligter(self.highlight_row)
        # self.view.connect_goniometer_table(self.set_goniometer_table)

    def add_sample(self):
        mat_dict = shape_dict = None

        axes = self.model.get_goniometer_strings(self.goniometers.get_list())

        if self.material_parameters.chemical_formula:
            mat_dict = self.model.get_material_dict(
                self.material_parameters.chemical_formula,
                self.material_parameters.z_parameter,
                self.material_parameters.volume,
            )

        vectors = self.face_indices.get_vectors()
        angles = 0, 0, 0
        if vectors is not None:
            values = self.model.get_euler_angles(vectors[0], vectors[1])
            if values is not None:
                angles = values
        shape_dict = self.model.get_shape_dict(
            self.sample.shape, self.sample.get_params_list(), *angles
        )

        if np.all([var is not None for var in (shape_dict, mat_dict, axes)]):
            self.model.set_sample(shape_dict, mat_dict, axes)

            abs_dict = self.model.get_absorption_dict()
            self.set_absorption_parameters(abs_dict)
            mesh = self.model.sample_mesh()
            self.vis_viewmodel.add_sample(mesh)
            self.vis_viewmodel.set_transform(self.model.get_transform())

    def get_sample_shape_option_list(self):
        return [e.value for e in SampleShapeOptions]

    def init_view(self):
        self.face_indices_bind.update_in_view(self.face_indices)
        self.material_parameters_bind.update_in_view(self.material_parameters)
        self.sample_bind.update_in_view(self.sample)

    def load_UB(self):
        if self.sample.path:
            self.model.load_UB(self.sample.path)
            vol = self.model.get_volume()
            self.set_unit_cell_volume(vol)
            self.vis_viewmodel.update_oriented_lattice()

    def on_sample_update(self, results: Dict[str, Any]):
        updated = results.get("updated", [])
        for update in updated:
            match update:
                case "path":
                    self.load_UB()

    def set_absorption_parameters(self, absorption_dict):
        print("TODO", absorption_dict)

    def set_sample_height(self, height: str):
        self.sample.height = float(height)
        self.update_sample_parameters()

    def set_sample_shape(self, shape: str):
        self.sample.shape = SampleShapeOptions(shape)
        self.update_sample_parameters()

    def set_sample_thickness(self, thickness: str):
        self.sample.thickness = float(thickness)
        self.update_sample_parameters()

    def set_sample_width(self, width: str):
        self.sample.width = float(width)
        self.update_sample_parameters()

    def set_unit_cell_volume(self, volume):
        self.material_parameters.volume = volume
        self.material_parameters_bind.update_in_view(self.material_parameters)

    def set_vis_viewmodel(self, vis_viewmodel: NeuXtalVizViewModel):
        self.vis_viewmodel = vis_viewmodel

    def update_sample_parameters(self):
        fixed = [False, False, False]

        shape = self.sample.shape
        if shape != SampleShapeOptions.plate:
            self.sample.thickness = self.sample.width
            fixed[2] = True
        if shape != SampleShapeOptions.cylinder and shape != SampleShapeOptions.plate:
            self.sample.height = self.sample.width
            fixed[1] = True

        self.sample_bind.update_in_view(self.sample)
        self.constraints_bind.update_in_view(fixed)

    # def highlight_row(self):
    #     goniometer = self.view.get_goniometer()
    #     self.view.set_angle(goniometer)

    # def set_goniometer_table(self):
    #     self.view.set_goniometer_table()
