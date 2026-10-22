"""Parameter definitions and defaults for DRAFT SOC Activity Tools."""
from dataclasses import dataclass


@dataclass
class SOCATParams:
    # Fertilizer emission factors (t CO2e / kg N)
    ef_fe_printed: float = 0.01
    ef_fe_converted: float = 0.00429

    # Baseline cap when records are undocumented (50% of project)
    undocumented_baseline_cap_fraction: float = 0.50

    # Minimum residue cover for conservation / zero tillage
    min_residue_cover: float = 0.30

    # Max yield drop threshold triggering leakage evaluation
    yield_drop_trigger_threshold: float = 0.05
