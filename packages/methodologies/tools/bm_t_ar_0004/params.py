"""Parameter definitions and catalogue bindings for BM-T-AR-0004."""
from dataclasses import dataclass
from typing import Optional

from dmrv_core.parameters import ParameterResolver


@dataclass
class AR0004Params:
    CF_TREE: float = 0.47
    CF_S: float = 0.47
    R_TREE_baseline: float = 0.25
    R_S: float = 0.40
    BDR_SF: float = 0.10
    BEF2_ex_post: float = 1.15
    C_to_CO2: float = 44.0 / 12.0
    forest_threshold_crown_cover: float = 0.30

    @classmethod
    def load(cls, resolver: Optional[ParameterResolver] = None) -> "AR0004Params":
        if resolver is None:
            return cls()
        return cls(
            CF_TREE=float(resolver.resolve("CF_TREE", "BM-T-AR-0004").value),
            CF_S=float(resolver.resolve("CF_S", "BM-T-AR-0004").value),
            R_TREE_baseline=float(resolver.resolve("R_TREE_baseline", "BM-T-AR-0004").value),
            R_S=float(resolver.resolve("R_S", "BM-T-AR-0004").value),
            BDR_SF=float(resolver.resolve("BDR_SF", "BM-T-AR-0004").value),
            BEF2_ex_post=float(resolver.resolve("BEF2_ex_post", "BM-T-AR-0004").value),
            C_to_CO2=float(resolver.resolve("C_to_CO2", "BM-T-AR-0004").value),
            forest_threshold_crown_cover=float(resolver.resolve("forest_threshold_crown_cover", "GLOBAL").value),
        )
