from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Union

import numpy as np
from pydantic import BaseModel, Field, field_serializer, field_validator

from NeuXtalViz.view_models.base_view_model import NeuXtalVizViewModel
from NeuXtalViz.models.sample_tools import SampleModel


class AbsorptionParameters(BaseModel):
    sigma_a: float = Field(default=0.0, title="Absorption σ")
    sigma_s: float = Field(default=0.0, title="Scattering σ")
    mu_a: float = Field(default=0.0, title="Absorption μ")
    mu_s: float = Field(default=0.0, title="Scattering μ")
    N: float = Field(default=0, title="N")
    M: float = Field(default=0.0, title="M")
    n: float = Field(default=0.0, title="n")
    rho: float = Field(default=0.0, title="rho")
    V: float = Field(default=0.0, title="V")
    m: float = Field(default=0.0, title="m")


class FaceIndices(BaseModel):
    hu: float = Field(default=0, title="a*")
    ku: float = Field(default=0, title="b*")
    lu: float = Field(default=1, title="c*")
    hv: float = Field(default=1, title="a*")
    kv: float = Field(default=0, title="b*")
    lv: float = Field(default=0, title="c*")

    def get_vectors(self):
        return (self.hu, self.ku, self.lu), (self.hv, self.kv, self.lv)


class Goniometer(BaseModel):
    index: int = Field(default=0)
    name: str = Field(default="", title="Name")
    x: int = Field(default=0, ge=-1, le=1, title="x")
    y: int = Field(default=0, ge=-1, le=1, title="y")
    z: int = Field(default=0, ge=-1, le=1, title="z")
    sense: int = Field(default=1, title="Sense")
    angle: Decimal = Field(
        default=Decimal(0.0), ge=-360.0, le=360.0, decimal_places=1, title="Angle"
    )

    @field_validator("sense", mode="after")
    @classmethod
    def validate_sense(cls, value: int) -> int:
        if value not in [-1, 1]:
            raise ValueError("Sense must be set to -1 or 1.")
        return value

    @field_serializer("angle")
    def serialize_angle(self, angle: Decimal) -> str:
        return str(round(float(angle), 1))

    def get_list(self):
        return [self.name, self.x, self.y, self.z, self.sense, self.angle]


class GoniometerTable(BaseModel):
    headers: List[Dict[str, str]] = [
        {"align": "center", "key": "name", "title": "Name"},
        {"align": "center", "key": "x", "title": "x"},
        {"align": "center", "key": "y", "title": "y"},
        {"align": "center", "key": "z", "title": "z"},
        {"align": "center", "key": "sense", "title": "Sense"},
        {"align": "center", "key": "angle", "title": "Angle"},
    ]
    rows: List[Goniometer] = Field(
        default=[
            Goniometer(index=0, name="ω", x=0, y=1, z=0, sense=1, angle=Decimal(0.0)),
            Goniometer(index=1, name="χ", x=0, y=0, z=1, sense=1, angle=Decimal(0.0)),
            Goniometer(index=2, name="φ", x=0, y=1, z=0, sense=1, angle=Decimal(0.0)),
        ]
    )
    selected_index: Union[List[int], int, None] = Field(default=None)

    def get_rows(self):
        return [row.get_list() for row in self.rows]


class MaterialParameters(BaseModel):
    add_disabled: bool = Field(default=True)
    chemical_formula: str = Field(default="", title="Element")
    z_parameter: int = Field(default=1, ge=1, le=10000, title="Z")
    volume: Decimal = Field(
        default=Decimal(0.0), ge=0.0, le=100000.0, decimal_places=4, title="Ω"
    )

    @field_serializer("volume")
    def serialize_volume(self, volume: Decimal) -> str:
        return str(round(float(volume), 4))


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

    @field_serializer("height")
    def serialize_height(self, height: Decimal) -> str:
        return str(round(float(height), 5))

    @field_serializer("thickness")
    def serialize_thickness(self, thickness: Decimal) -> str:
        return str(round(float(thickness), 5))

    @field_serializer("width")
    def serialize_width(self, width: Decimal) -> str:
        return str(round(float(width), 5))

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
        self.goniometer_editor_bind = binding.new_bind(
            self.goniometer_editor,
            callback_after_update=self.on_goniometer_editor_update,
        )
        self.goniometer_table = GoniometerTable()
        self.goniometer_table_bind = binding.new_bind(
            self.goniometer_table, callback_after_update=self.on_goniometer_table_update
        )
        self.material_parameters = MaterialParameters()
        self.material_parameters_bind = binding.new_bind(
            self.material_parameters,
            callback_after_update=self.on_material_parameters_update,
        )
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

    def highlight_row(self, row_index: Union[List[int], int]):
        if isinstance(row_index, list):
            row_index = row_index[0]
        self.goniometer_table.selected_index = row_index

        self.goniometer_editor.index = self.goniometer_table.rows[row_index].index
        self.goniometer_editor.name = self.goniometer_table.rows[row_index].name
        self.goniometer_editor.x = self.goniometer_table.rows[row_index].x
        self.goniometer_editor.y = self.goniometer_table.rows[row_index].y
        self.goniometer_editor.z = self.goniometer_table.rows[row_index].z
        self.goniometer_editor.sense = self.goniometer_table.rows[row_index].sense
        self.goniometer_editor.angle = self.goniometer_table.rows[row_index].angle
        self.goniometer_editor_bind.update_in_view(self.goniometer_editor)

    def init_view(self):
        self.absorption_parameters_bind.update_in_view(self.absorption_parameters)
        self.face_indices_bind.update_in_view(self.face_indices)
        self.goniometer_table_bind.update_in_view(self.goniometer_table)
        self.material_parameters_bind.update_in_view(self.material_parameters)

        self.update_sample_parameters()

    def load_UB(self):
        if self.sample.path:
            self.model.load_UB(self.sample.path)
            vol = self.model.get_volume()
            self.set_unit_cell_volume(vol)
            self.vis_viewmodel.update_oriented_lattice()

    def on_goniometer_editor_update(self, results: Dict[str, Any]):
        updated = results.get("updated", [])
        for update in updated:
            match update:
                case "x":
                    self.set_goniometer_table("x", self.goniometer_editor.x)
                case "y":
                    self.set_goniometer_table("y", self.goniometer_editor.y)
                case "z":
                    self.set_goniometer_table("z", self.goniometer_editor.z)
                case "sense":
                    self.set_goniometer_table("sense", self.goniometer_editor.sense)
                case "angle":
                    self.set_goniometer_table("angle", self.goniometer_editor.angle)

    def on_goniometer_table_update(self, results: Dict[str, Any]):
        updated = results.get("updated", [])
        for update in updated:
            match update:
                case "selected_index":
                    if self.goniometer_table.selected_index:
                        self.highlight_row(self.goniometer_table.selected_index)

    def on_material_parameters_update(self, results: Dict[str, Any]):
        updated = results.get("updated", [])
        for update in updated:
            match update:
                case "chemical_formula":
                    if self.material_parameters.chemical_formula:
                        self.material_parameters.add_disabled = False
                    else:
                        self.material_parameters.add_disabled = True

                    self.material_parameters_bind.update_in_view(
                        self.material_parameters
                    )

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

    def set_goniometer_table(self, name: str, value: Any):
        match name:
            case "angle":
                self.goniometer_table.rows[
                    self.goniometer_editor.index
                ].angle = Decimal(value)
            case "name":
                self.goniometer_table.rows[self.goniometer_editor.index].name = value
            case "sense":
                self.goniometer_table.rows[self.goniometer_editor.index].sense = int(
                    value
                )
            case "x":
                self.goniometer_table.rows[self.goniometer_editor.index].x = int(value)
            case "y":
                self.goniometer_table.rows[self.goniometer_editor.index].y = int(value)
            case "z":
                self.goniometer_table.rows[self.goniometer_editor.index].z = int(value)

        self.goniometer_table_bind.update_in_view(self.goniometer_table)

    def set_index(self, index: str, value: str):
        match index:
            case "hu":
                self.face_indices.hu = float(value)
            case "ku":
                self.face_indices.ku = float(value)
            case "lu":
                self.face_indices.lu = float(value)
            case "hv":
                self.face_indices.hv = float(value)
            case "kv":
                self.face_indices.kv = float(value)
            case "lv":
                self.face_indices.lv = float(value)

    def set_material_parameter(self, name: str, value: str):
        match name:
            case "chemical_formula":
                self.material_parameters.chemical_formula = value
            case "volume":
                self.material_parameters.volume = Decimal(value)
            case "z_parameter":
                self.material_parameters.z_parameter = int(value)

    def set_sample_param(self, name: str, value: str):
        match name:
            case "height":
                self.sample.height = Decimal(value)
            case "shape":
                self.sample.shape = SampleShapeOptions(value)
            case "thickness":
                self.sample.thickness = Decimal(value)
            case "width":
                self.sample.width = Decimal(value)

        self.update_sample_parameters()

    def set_unit_cell_volume(self, volume):
        self.material_parameters.volume = Decimal(volume)
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
