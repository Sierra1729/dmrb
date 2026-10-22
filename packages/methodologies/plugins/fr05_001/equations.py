"""BM FR05.001 Mangrove A/R methodology equations."""
from __future__ import annotations

from typing import Optional, Sequence
from dmrv_core.equations import CalculationContext, equation


@equation(
    tool="BM-FR05.001",
    version="1.0",
    eq="4",
    page=9,
    doc="Mangrove default SOC accumulation: ΔSOC_PROJ,t = (44/12) * sum_c (A_PLANT,c * dSOC_c) * 1 year",
)
def mangrove_soc_accumulation(
    cohort_areas_ha: Sequence[float],
    cohort_ages_years: Sequence[int],
    dsoc_default_t_c_ha_yr: float = 0.50,
    max_accumulation_years: int = 20,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Calculate mangrove annual soil organic carbon accumulation across planted cohorts."""
    if len(cohort_areas_ha) != len(cohort_ages_years):
        raise ValueError("Cohort areas and ages must have equal length")

    total_c_tonnes = 0.0
    for area, age in zip(cohort_areas_ha, cohort_ages_years, strict=True):
        if 0 <= age < max_accumulation_years:
            total_c_tonnes += float(area) * float(dsoc_default_t_c_ha_yr)

    # Convert t C to t CO2e
    return float(total_c_tonnes * (44.0 / 12.0))


@equation(
    tool="BM-FR05.001",
    version="1.0",
    eq="1",
    page=8,
    doc="Baseline mangrove removals: ΔC_BSL,t = ΔC_TREE_BSL,t + ΔC_SHRUB_BSL,t + ΔC_DW_BSL,t (litter excluded)",
)
def mangrove_baseline_removals(
    delta_c_tree_bsl: float,
    delta_c_shrub_bsl: float = 0.0,
    delta_c_dw_bsl: float = 0.0,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Calculate baseline removals for mangrove habitat (litter excluded)."""
    return float(delta_c_tree_bsl + delta_c_shrub_bsl + delta_c_dw_bsl)


@equation(
    tool="BM-FR05.001",
    version="1.0",
    eq="3",
    page=8,
    doc="Project mangrove carbon stock change: ΔC_P,t = ΔC_TREE_PROJ,t + ΔC_SHRUB_PROJ,t + ΔC_DW_PROJ,t + ΔSOC_PROJ,t",
)
def mangrove_project_removals(
    delta_c_tree_proj: float,
    delta_c_shrub_proj: float = 0.0,
    delta_c_dw_proj: float = 0.0,
    delta_soc_proj: float = 0.0,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Calculate project removals for mangrove habitat (litter excluded)."""
    return float(delta_c_tree_proj + delta_c_shrub_proj + delta_c_dw_proj + delta_soc_proj)


__all__ = [
    "mangrove_soc_accumulation",
    "mangrove_baseline_removals",
    "mangrove_project_removals",
]
