"""BM WA03.002 Landfill gas flaring or use equations."""
from __future__ import annotations

from typing import Optional
from dmrv_core.equations import CalculationContext, equation


@equation(
    tool="BM-WA03.002",
    version="1.0",
    eq="2",
    page=7,
    doc="Baseline methane emissions: BE_CH4,y = [(1 - OX_top_layer) * F_CH4,PJ,y - F_CH4,BL,y] * GWP_CH4",
)
def baseline_methane_emissions(
    f_ch4_pj_y: float,
    f_ch4_bl_y: float,
    gwp_ch4: float,
    ox_top_layer: float = 0.10,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Calculate baseline methane emissions avoided by landfill gas capture and destruction."""
    net_flow = (1.0 - float(ox_top_layer)) * float(f_ch4_pj_y) - float(f_ch4_bl_y)
    return float(max(0.0, net_flow * float(gwp_ch4)))


@equation(
    tool="BM-WA03.002",
    version="1.0",
    eq="3",
    page=8,
    doc="Total methane captured and destroyed: F_CH4,PJ,y = F_CH4,flared,y + F_CH4,EL,y + F_CH4,HG,y + F_CH4,NG,y",
)
def total_methane_captured(
    f_flared: float,
    f_electricity: float = 0.0,
    f_heat: float = 0.0,
    f_network: float = 0.0,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Calculate total mass of methane destroyed/used in project activity."""
    return float(f_flared + f_electricity + f_heat + f_network)


@equation(
    tool="BM-WA03.002",
    version="1.0",
    eq="5",
    page=9,
    doc="Ex-ante methane capture estimate: F_CH4,PJ,y = eta_PJ * BE_CH4,SWDS,y / GWP_CH4",
)
def ex_ante_methane_capture(
    be_ch4_swds_tco2e: float,
    gwp_ch4: float,
    eta_pj: float = 0.50,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Ex-ante estimated methane capture based on FOD model with default collection efficiency 50%."""
    return float(float(eta_pj) * float(be_ch4_swds_tco2e) / float(gwp_ch4))


@equation(
    tool="BM-WA03.002",
    version="1.0",
    eq="ER",
    page=14,
    doc="Emission Reductions: ER_y = BE_y - PE_y - LE_y",
)
def emission_reductions(
    baseline_emissions: float,
    project_emissions: float = 0.0,
    leakage_emissions: float = 0.0,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Calculate net emission reductions."""
    return float(float(baseline_emissions) - float(project_emissions) - float(leakage_emissions))


__all__ = [
    "baseline_methane_emissions",
    "total_methane_captured",
    "ex_ante_methane_capture",
    "emission_reductions",
]
