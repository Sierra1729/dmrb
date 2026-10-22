"""Parameter definitions and catalogue bindings for BM-T-AR-0006."""
from dataclasses import dataclass
from typing import Optional

from dmrv_core.parameters import ParameterResolver


@dataclass
class AR0006Params:
    soc_loss_fraction: float = 0.10
    disturbance_threshold_fraction: float = 0.10
    transition_years: int = 20
    max_rate_tC_ha_yr: float = 0.80

    @classmethod
    def load(cls, resolver: Optional[ParameterResolver] = None) -> "AR0006Params":
        if resolver is None:
            return cls()
        return cls(
            soc_loss_fraction=float(resolver.resolve("soc_loss_fraction", "BM-T-AR-0006").value),
            disturbance_threshold_fraction=float(resolver.resolve("disturbance_threshold_fraction", "BM-T-AR-0006").value),
            transition_years=int(resolver.resolve("transition_years", "BM-T-AR-0006").value),
            max_rate_tC_ha_yr=float(resolver.resolve("max_rate_tC_ha_yr", "BM-T-AR-0006").value),
        )
