"""Errata configuration flags for BM AG04.001 per official PDF verification and errata register."""
from dataclasses import dataclass


@dataclass
class AG04001ErrataFlags:
    # E-AG1-01: Net-to-gross uncertainty adjustment factor UF_b
    # Text prints 0.895 in para 3.2 but 0.89 in Eq.5 & Table 4. Default: 0.89 (conservative)
    use_conservative_uf_b: bool = True

    # Global warming potential of methane (IPCC AR6 default 29.8)
    gwp_ch4: float = 29.8
