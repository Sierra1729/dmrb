"""Parameter definitions and catalogue bindings for BM-T-AR-0002."""
from dataclasses import dataclass
from typing import Optional

from dmrv_core.parameters import ParameterResolver


@dataclass
class AR0002Params:
    non_co2_to_co2_ratio: float = 0.07  # IPCC 2006 Table 2.5 adapted
    CF_TREE: float = 0.50
    CF_SHRUB: float = 0.50
    BDR_SF: float = 0.10
    BEF2_harvest: float = 1.25
    f_BL_tropical: float = 0.25
    f_BL_temperate: float = 0.10
    fire_area_threshold_fraction: float = 0.05
    GWP_CH4_AR6: float = 29.8
    GWP_N2O_AR6: float = 273.0
    GWP_CH4_SAR: float = 21.0
    GWP_N2O_SAR: float = 310.0

    @classmethod
    def load(cls, resolver: Optional[ParameterResolver] = None) -> "AR0002Params":
        if resolver is None:
            return cls()
        return cls(
            non_co2_to_co2_ratio=float(resolver.resolve("non_co2_to_co2_ratio", "BM-T-AR-0002").value),
            CF_TREE=float(resolver.resolve("CF_TREE", "BM-T-AR-0002").value),
            CF_SHRUB=float(resolver.resolve("CF_SHRUB", "BM-T-AR-0002").value),
            BDR_SF=float(resolver.resolve("BDR_SF", "BM-T-AR-0002").value),
            BEF2_harvest=float(resolver.resolve("BEF2_harvest", "BM-T-AR-0002").value),
        )
