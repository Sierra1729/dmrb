"""Parameter definitions and catalogue bindings for BM-T-AR-0005."""
from dataclasses import dataclass
from typing import Optional

from dmrv_core.parameters import ParameterResolver


@dataclass
class AR0005Params:
    CF: float = 0.47
    R_TREE: float = 0.25
    R_S: float = 0.40
    dead_organic_matter_factor: float = 1.1

    @classmethod
    def load(cls, resolver: Optional[ParameterResolver] = None) -> "AR0005Params":
        if resolver is None:
            return cls()
        return cls(
            CF=float(resolver.resolve("CF", "BM-T-AR-0005").value),
            R_TREE=float(resolver.resolve("R_TREE", "BM-T-AR-0005").value),
            R_S=float(resolver.resolve("R_S", "BM-T-AR-0005").value),
            dead_organic_matter_factor=float(resolver.resolve("dead_organic_matter_factor", "BM-T-AR-0005").value),
        )
