from typing import Any, Callable, Optional
from nova.mvvm.pydantic_utils import validate_pydantic_parameter


def validate_element(key: str, value: Any, element: Any = None) -> None:
    if element:
        res = validate_pydantic_parameter(key, value)
        if res is not True:
            element.setStyleSheet("border")
        else:
            element.setStyleSheet("")


def process_change(
    key: str, value: Any, element: Any = None, callback: Optional[Callable] = None
) -> None:
    validate_element(key, value, element)
    if callback is not None:
        callback(key, value)
