from typing import Annotated

from pydantic import PlainSerializer


FloatWithPrecision1 = Annotated[
    float,
    PlainSerializer(lambda x: f"{float(x):.1f}", return_type=str),
]

FloatWithPrecision4 = Annotated[
    float,
    PlainSerializer(lambda x: f"{float(x):.4f}", return_type=str),
]

FloatWithPrecision5 = Annotated[
    float,
    PlainSerializer(lambda x: f"{float(x):.5f}", return_type=str),
]

FloatWithPrecision6 = Annotated[
    float,
    PlainSerializer(lambda x: f"{float(x):.6f}", return_type=str),
]
