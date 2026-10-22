"""Errata flags for BM-T-AR-0004 per specs/12_errata_register.md."""
from dataclasses import dataclass


@dataclass
class AR0004ErrataFlags:
    # E-AR4-01: Section 4.3 Note 1 cites paragraph 10, means paragraph 13 (zero baseline tree stock)
    map_para10_to_para13: bool = True

    # E-AR4-03: Variable list mislabels beta and n_i. Beta is regression slope, n_i is sub-sample size
    use_corrected_double_sampling_vars: bool = True

    # E-AR4-06: Shrub crown cover threshold. Exactly 5% undefined. Include exactly 5% in Eq.26
    shrub_cc_zero_below: float = 0.05

    # E-AR4-07: Table labels sample variance as "variance of mean"
    divide_by_ni_in_eq15: bool = True

    # E-AR4-08: Forest threshold crown cover default
    forest_threshold_crown_cover: float = 0.30
