"""Errata configuration flags for BM AG04.002 per official PDF verification and errata register."""
from dataclasses import dataclass


@dataclass
class AG04002ErrataFlags:
    # E-AG2-01: PE_n sign and N2O-N conversion (44/28)
    use_corrected_pen_sign_and_n2o_conversion: bool = True

    # E-AG2-02: Apply uncertainty deduction (1 - U_d) once in Eq.6, not twice in Eq.6 and Eq.7
    apply_ud_once: bool = True

    # E-AG2-03: Global Warming Potentials (IPCC AR6 defaults)
    gwp_ch4: float = 29.8
    gwp_n2o: float = 273.0
