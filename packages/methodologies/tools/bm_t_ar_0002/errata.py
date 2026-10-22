"""Errata flags for BM-T-AR-0002 per specs/12_errata_register.md."""
from dataclasses import dataclass


@dataclass
class AR0002ErrataFlags:
    # E-GWP-01: GWP values. Tool prints SAR (21/310), CCTS mandates latest IPCC (AR6 29.8/273)
    gwp_mode: str = "project_locked"  # "project_locked" (AR6) or "tool_as_printed" (SAR)

    # E-AR2-03: Eq.8 DOM stocks C_DW and C_LI must be per-hectare (t CO2e/ha)
    use_per_hectare_dom: bool = True

    # E-AR2-07: Minimum forest area in India's forest definition
    forest_min_area_ha: float = 0.05
