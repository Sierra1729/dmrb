"""Errata flags for BM-T-011 per specs/12_errata_register.md."""
from dataclasses import dataclass


@dataclass
class T011ErrataFlags:
    # E-T11-01: Appendix with simplified approaches is missing from PDF
    simplified_approaches_available: bool = False

    # E-T11-02: Eq.4 printed 'phi=1(1+Vy)' -> 1 / (1 + V_y)
    fix_phi_formula: bool = True

    # E-T11-03: DPT 15 swaps frequency and QA/QC rows
    monthly_readings_annual_mean: bool = True

    # E-T11-04: Climate class boundaries undefined; pick class giving lower emissions
    conservative_climate_boundary: bool = True
