from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

import numpy as np
from pydantic import BaseModel, Field

from NeuXtalViz.view_models.base_view_model import NeuXtalVizViewModel
from NeuXtalViz.models.sample_tools import SampleModel


class AbsorptionParameters(BaseModel):
    sigma_a: float = Field(default=0.0, title="σ")
    sigma_s: float = Field(default=0.0, title="σ")
    mu_a: float = Field(default=0.0, title="μ")
    mu_s: float = Field(default=0.0, title="μ")
    N: int = Field(default=0, title="N")
    M: float = Field(default=0.0, title="M")
    n: float = Field(default=0.0, title="n")
    rho: float = Field(default=0.0, title="rho")
    V: float = Field(default=0.0, title="V")
    m: float = Field(default=0.0, title="m")


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
    x: int = Field(default=0, ge=-1, le=1)
    y: int = Field(default=0, ge=-1, le=1)
    z: int = Field(default=0, ge=-1, le=1)
    sense: Literal[-1, 1] = Field(default=1)
    angle: Decimal = Field(default=Decimal(0.0), ge=-360.0, le=360.0, decimal_places=1)

    def get_list(self):
        return [self.name, self.x, self.y, self.z, self.sense, self.angle]


class GoniometerTable(BaseModel):
    selected_index: Optional[int] = Field(default=None)
    rows: List[Goniometer] = Field(
        default=[
            Goniometer(name="ω", x=0, y=1, z=0, sense=1, angle=Decimal(0.0)),
            Goniometer(name="χ", x=0, y=0, z=1, sense=1, angle=Decimal(0.0)),
            Goniometer(name="φ", x=0, y=1, z=0, sense=1, angle=Decimal(0.0)),
        ]
    )

    def get_rows(self):
        return [row.get_list() for row in self.rows]


class MaterialParameters(BaseModel):
    chemical_formula: str = Field(default="")
    z_parameter: int = Field(default=1, ge=1, le=10000, title="Z")
    volume: Decimal = Field(
        default=Decimal(0.0), ge=0.0, le=100000.0, decimal_places=4, title="Ω"
    )


class SampleShapeOptions(str, Enum):
    cylinder = "Cylinder"
    plate = "Plate"
    sphere = "Sphere"


class Sample(BaseModel):
    height: Decimal = Field(
        default=Decimal(0.50), ge=0, le=100, decimal_places=5, title="Height"
    )
    path: str = Field(default="")
    shape: SampleShapeOptions = Field(default=SampleShapeOptions.sphere, title="Shape")
    thickness: Decimal = Field(
        default=Decimal(0.50), ge=0, le=100, decimal_places=5, title="Thickness"
    )
    width: Decimal = Field(
        default=Decimal(0.50), ge=0, le=100, decimal_places=5, title="Width"
    )

    def get_params_list(self):
        return [float(self.width), float(self.height), float(self.thickness)]


class SampleViewModel:
    def __init__(self, model: SampleModel, binding):
        self.model = model

        # One-way bindings
        self.add_sample_bind = binding.new_bind()
        self.constraints_bind = binding.new_bind()

        # Two-way bindings
        self.absorption_parameters = AbsorptionParameters()
        self.absorption_parameters_bind = binding.new_bind(self.absorption_parameters)
        self.face_indices = FaceIndices()
        self.face_indices_bind = binding.new_bind(self.face_indices)
        self.goniometer_editor = Goniometer()
        self.goniometer_editor_bind = binding.new_bind(self.goniometer_editor)
        self.goniometer_table = GoniometerTable()
        self.goniometer_table_bind = binding.new_bind(self.goniometer_table)
        self.material_parameters = MaterialParameters()
        self.material_parameters_bind = binding.new_bind(self.material_parameters)
        self.sample = Sample()
        self.sample_bind = binding.new_bind(
            self.sample, callback_after_update=self.on_sample_update
        )

    def add_sample(self):
        mat_dict = shape_dict = None

        axes = self.model.get_goniometer_strings(self.goniometer_table.get_rows())

        if self.material_parameters.chemical_formula:
            mat_dict = self.model.get_material_dict(
                self.material_parameters.chemical_formula,
                float(self.material_parameters.z_parameter),
                float(self.material_parameters.volume),
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
            self.add_sample_bind.update_in_view(mesh)
            self.vis_viewmodel.set_transform(self.model.get_transform())

    def get_sample_shape_option_list(self):
        return [e.value for e in SampleShapeOptions]

    def highlight_row(self, row_index: int):
        self.goniometer_table.selected_index = row_index

        self.goniometer_editor = self.goniometer_table.rows[row_index]
        self.goniometer_editor_bind.update_in_view(self.goniometer_editor)

    def init_view(self):
        self.absorption_parameters_bind.update_in_view(self.absorption_parameters)
        self.face_indices_bind.update_in_view(self.face_indices)
        self.goniometer_table_bind.update_in_view(self.goniometer_table)
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
                case "height" | "shape" | "thickness" | "width":
                    self.update_sample_parameters()
                case "path":
                    self.load_UB()

    def set_absorption_parameters(self, absorption_dict):
        self.absorption_parameters.sigma_a = absorption_dict["sigma_a"]
        self.absorption_parameters.sigma_s = absorption_dict["sigma_s"]
        self.absorption_parameters.mu_a = absorption_dict["mu_a"]
        self.absorption_parameters.mu_s = absorption_dict["mu_s"]
        self.absorption_parameters.N = absorption_dict["N"]
        self.absorption_parameters.M = absorption_dict["M"]
        self.absorption_parameters.n = absorption_dict["n"]
        self.absorption_parameters.rho = absorption_dict["rho"]
        self.absorption_parameters.V = absorption_dict["V"]
        self.absorption_parameters.m = absorption_dict["m"]

        self.absorption_parameters_bind.update_in_view(self.absorption_parameters)

    def set_goniometer_table(self, name: str, value: str):
        if self.goniometer_table.selected_index is None:
            return

        row_index = self.goniometer_table.selected_index

        typed_value: Any
        match name:
            case "angle":
                typed_value = Decimal(value)
            case "name":
                typed_value = value
            case _:
                typed_value = int(value)

        setattr(self.goniometer_table.rows[row_index], name, typed_value)
        self.goniometer_table_bind.update_in_view(self.goniometer_table)

    def set_index(self, index: str, value: str):
        setattr(self.face_indices, index, float(value))

    def set_material_parameter(self, name: str, value: str):
        typed_value: Any
        match name:
            case "chemical_formula":
                typed_value = value
            case "z_parameter":
                typed_value = int(value)
            case _:
                typed_value = Decimal(value)

        setattr(self.material_parameters, name, typed_value)

    def set_sample_param(self, name: str, value: str):
        typed_value: Any
        match name:
            case "shape":
                typed_value = SampleShapeOptions(value)
            case _:
                typed_value = Decimal(value)

        setattr(self.sample, name, typed_value)
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
