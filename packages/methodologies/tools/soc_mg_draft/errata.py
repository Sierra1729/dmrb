"""Errata flags for DRAFT SOC Model Guidelines per specs/12_errata_register.md."""
from dataclasses import dataclass


@dataclass
class SOCMGErrataFlags:
    # E-SOCMG-01: Scope/applicability text copied from fuel-combustion tool -> ignore
    ignore_fuel_combustion_text: bool = True

    # E-SOCMG-02: Table 2 Eq. 3a, 4, 5a unit correction factors (100 and 10000)
    use_unit_corrected_equations: bool = True

    # E-SOCMG-03: Example E1.1 uses 95% t-value; follow Eq.21 (90% CI)
    use_90pct_ci_for_moe: bool = True

    # E-SOCMG-04: PICP t-statistic test: default fail if t < -t(0.90, n-1)
    fail_picp_if_below_critical: bool = True
