"""Errata flags for BM-T-AR-0006 per specs/12_errata_register.md."""
from dataclasses import dataclass


@dataclass
class AR0006ErrataFlags:
    # E-AR6-01: Para 4(a) joins conditions with "or", implement as AND (all conditions required)
    require_all_eligibility_conditions: bool = True

    # E-AR6-03: Table 5 has no f_MG for no-till baselines; block stratum unless user justifies
    block_no_till_without_justification: bool = True

    # E-AR6-04: Eq.6 rate after t_PREP + 20 not stated; zero after t_PREP + 20 (steady state reached)
    zero_rate_after_transition: bool = True

    # E-AR6-05: Tool code printed "BMT-T-AR-0006" -> canonical "BM-T-AR-0006"
    canonical_code: str = "BM-T-AR-0006"
