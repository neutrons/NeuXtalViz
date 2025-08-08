from enum import Enum


class NeuXtalVizSignals(str, Enum):
    """Available signals."""

    SHOW_PERIODIC_TABLE = "pt_table"
    SHOW_ATOM_TABLE = "atom_table"
    ATOM_UPDATE = "atom_update"
