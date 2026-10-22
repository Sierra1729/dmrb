"""Errata flags for DRAFT SOC Activity Tools per specs/12_errata_register.md."""
from dataclasses import dataclass


@dataclass
class SOCATErrataFlags:
    # E-SOCAT-01: Default printed 0.01 tCO2e/kgN (conservative); if False, use converted 0.00429
    use_printed_ef_fe: bool = True

    # E-SOCAT-02: Eq.3 bracket Σ_y Σ_a [(FU_PR - FU_BL) + (EU_PR - EU_BL)]
    use_corrected_bracket_eq3: bool = True

    # E-SOCAT-03: CY_min from previously verified periods incl. baseline
    use_prev_verified_cy_min: bool = True

    # E-SOCAT-04: Totals per stratum for Eq. 4, 5, 9
    stratum_totals_eq4_5_9: bool = True

    # E-SOCAT-05: AQ unit is kg (not km)
    aq_unit_kg: bool = True

    # E-SOCAT-09: Apply max(·, 0) to yield leakage (no positive leakage credit)
    floor_yield_leakage_at_zero: bool = True
