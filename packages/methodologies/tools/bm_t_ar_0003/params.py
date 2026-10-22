"""Parameter definitions and catalogue bindings for BM-T-AR-0003."""
from dataclasses import dataclass
from typing import Optional

from dmrv_core.parameters import ParameterResolver


@dataclass
class AR0003Params:
    CF_TREE: float = 0.50  # DPT 2 (errata E-CF-01: AR-0003 uses 0.5)
    CF_LI: float = 0.37  # DPT 3
    ormerod_coef: float = 0.57
    ormerod_exp: float = 0.80

    @classmethod
    def load(cls, resolver: Optional[ParameterResolver] = None) -> "AR0003Params":
        if resolver is None:
            return cls()
        return cls(
            CF_TREE=float(resolver.resolve("CF_TREE", "BM-T-AR-0003").value),
            CF_LI=float(resolver.resolve("CF_LI", "BM-T-AR-0003").value),
        )
