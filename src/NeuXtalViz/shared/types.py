from typing import Annotated

from pydantic import PlainSerializer


FloatWithPrecision1 = Annotated[
    float,
    PlainSerializer(lambda x: str(round(float(x), 1)), return_type=str),
]

FloatWithPrecision3 = Annotated[
    float,
    PlainSerializer(lambda x: str(round(float(x), 3)), return_type=str),
]

FloatWithPrecision4 = Annotated[
    float,
    PlainSerializer(lambda x: str(round(float(x), 4)), return_type=str),
]

FloatWithPrecision5 = Annotated[
    float,
    PlainSerializer(lambda x: str(round(float(x), 5)), return_type=str),
]

FloatWithPrecision6 = Annotated[
    float,
    PlainSerializer(lambda x: str(round(float(x), 6)), return_type=str),
]
