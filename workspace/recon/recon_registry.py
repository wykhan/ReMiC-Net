from __future__ import annotations

from dataclasses import dataclass

from workspace.common.protocol import PROTOCOL_V1


@dataclass(frozen=True)
class ReconMethod:
    name: str
    complexity_units: int


METHODS = {
    name: ReconMethod(name=name, complexity_units=units)
    for name, units in PROTOCOL_V1.method_complexity_units.items()
}


def ordered_methods() -> list[ReconMethod]:
    return [METHODS[name] for name in ["ref3", "ref5", "ref7", "ref9", "BP"]]
