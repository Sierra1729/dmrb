"""BM WA03.002 Flaring or Use of Landfill Gas."""
from methodologies.plugins.wa03_002.equations import (
    baseline_methane_emissions,
    total_methane_captured,
    ex_ante_methane_capture,
    emission_reductions,
)
from methodologies.plugins.wa03_002.plugin import BMWA03002Methodology

__all__ = [
    "BMWA03002Methodology",
    "baseline_methane_emissions",
    "total_methane_captured",
    "ex_ante_methane_capture",
    "emission_reductions",
]
