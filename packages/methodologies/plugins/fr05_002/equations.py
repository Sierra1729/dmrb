"""BM FR05.002 Methodology-level equations."""
from __future__ import annotations

from typing import List, Optional, Sequence
from dmrv_core.equations import CalculationContext, equation


@equation(
    tool="BM-FR05.002",
    version="1.0",
    eq="1",
    page=10,
    doc="Baseline net GHG removals: ΔC_BSL,t = ΔC_TREE_BSL,t + ΔC_SHRUB_BSL,t + ΔC_DW_BSL,t + ΔC_LI_BSL,t",
)
def baseline_carbon_stock_change(
    delta_c_tree_bsl: float,
    delta_c_shrub_bsl: float = 0.0,
    delta_c_dw_bsl: float = 0.0,
    delta_c_li_bsl: float = 0.0,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Calculate total baseline carbon stock change in year t."""
    return float(delta_c_tree_bsl + delta_c_shrub_bsl + delta_c_dw_bsl + delta_c_li_bsl)


@equation(
    tool="BM-FR05.002",
    version="1.0",
    eq="3",
    page=11,
    doc="Project carbon stock change: ΔC_P,t = ΔC_TREE_PROJ,t + ΔC_SHRUB_PROJ,t + ΔC_DW_PROJ,t + ΔC_LI_PROJ,t + ΔSOC_AL,t",
)
def project_carbon_stock_change(
    delta_c_tree_proj: float,
    delta_c_shrub_proj: float = 0.0,
    delta_c_dw_proj: float = 0.0,
    delta_c_li_proj: float = 0.0,
    delta_soc_al: float = 0.0,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Calculate total project carbon stock change in year t."""
    return float(delta_c_tree_proj + delta_c_shrub_proj + delta_c_dw_proj + delta_c_li_proj + delta_soc_al)


@equation(
    tool="BM-FR05.002",
    version="1.0",
    eq="2",
    page=11,
    doc="Actual net GHG removals: ΔC_ACTUAL,t = ΔC_P,t - GHG_E,t",
)
def actual_net_removals(
    delta_c_p: float,
    ghg_e: float,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Calculate actual net removals by sinks minus biomass burning emissions."""
    return float(delta_c_p - ghg_e)


@equation(
    tool="BM-FR05.002",
    version="1.0",
    eq="5",
    page=12,
    doc="Net anthropogenic GHG removals by sinks: ΔC_AR,t = ΔC_ACTUAL,t - ΔC_BSL,t - LK_t",
)
def net_anthropogenic_removals(
    delta_c_actual: float,
    delta_c_bsl: float,
    leakage: float,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Calculate net anthropogenic GHG removals by sinks in year t."""
    return float(delta_c_actual - delta_c_bsl - leakage)


@equation(
    tool="BM-FR05.002",
    version="1.0",
    eq="6",
    page=12,
    doc="Temporary carbon credit units (cumulative): tCCC_t2 = Σ_{t=1..t2} ΔC_AR,t",
)
def cumulative_temporary_credits(
    removals_series: Sequence[float],
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Calculate cumulative net GHG removals up to year t2."""
    return float(sum(removals_series))


@equation(
    tool="BM-FR05.002",
    version="1.0",
    eq="7",
    page=12,
    doc="Long-term carbon credit units: lCCC_t2 = Σ_{t=t1+1..t2} ΔC_AR,t",
)
def period_longterm_credits(
    removals_period: Sequence[float],
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Calculate net GHG removals during the monitoring period (t1 to t2). Negative indicates reversal."""
    return float(sum(removals_period))


__all__ = [
    "baseline_carbon_stock_change",
    "project_carbon_stock_change",
    "actual_net_removals",
    "net_anthropogenic_removals",
    "cumulative_temporary_credits",
    "period_longterm_credits",
]
