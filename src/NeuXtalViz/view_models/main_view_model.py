from nova.mvvm.interface import BindingInterface
from pydantic import BaseModel, Field


class ViewState(BaseModel):
    active_app: str = Field(default="1")


class MainViewModel:
    def __init__(self, binding: BindingInterface) -> None:
        self.view_state = ViewState()

        self.view_state_bind = binding.new_bind(self.view_state)
