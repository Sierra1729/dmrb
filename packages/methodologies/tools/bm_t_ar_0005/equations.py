"""BM-T-AR-0005: Increase in GHG emissions from displacement of pre-project agricultural activities."""
from __future__ import annotations

from typing import Optional
from dmrv_core.equations import CalculationContext, equation


@equation(
    tool="BM-T-AR-0005",
    version="1.0",
    eq="2",
    page=5,
    doc="Delta_C_BIOMASS,t = [ 1.1 * b_TREE * (1 + R_TREE) + b_SHRUB * (1 + R_S) ] * CF * A_DISP,t",
    errata_ids=["E-AR5-01", "E-AR5-02"],
)
def displacement_biomass_loss(
    b_tree: float,
    b_shrub: float,
    a_disp_ha: float,
    cf: float = 0.47,
    r_tree: float = 0.25,
    r_s: float = 0.40,
    dom_factor: float = 1.1,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Eq.2: Biomass carbon stock loss due to displacement of activity (t C).
    Unit is t C after multiplying by CF per Errata E-AR5-01.
    """
    tree_term = dom_factor * b_tree * (1.0 + r_tree)
    shrub_term = b_shrub * (1.0 + r_s)
    return float((tree_term + shrub_term) * cf * a_disp_ha)


@equation(
    tool="BM-T-AR-0005",
    version="1.0",
    eq="3",
    page=5,
    doc="Delta_SOC_LUC,t = SOC_REF * ( f_LUP * f_MGP * f_INP - f_LUD * f_MGD * f_IND ) * A_DISP,t",
    errata_ids=["E-AR5-01", "E-AR5-03"],
)
def displacement_soc_loss(
    soc_ref: float,
    f_lup: float,
    f_mgp: float,
    f_inp: float,
    f_lud: float,
    f_mgd: float,
    f_ind: float,
    a_disp_ha: float,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Eq.3: Soil organic carbon loss on receiving land due to displacement (t C).
    Unit is t C per Errata E-AR5-01. Negative value -> 0 (no gain counted).
    """
    factors_before = f_lup * f_mgp * f_inp
    factors_after = f_lud * f_mgd * f_ind
    diff = factors_before - factors_after
    if diff <= 0.0:
        return 0.0
    return float(soc_ref * diff * a_disp_ha)


@equation(
    tool="BM-T-AR-0005",
    version="1.0",
    eq="1",
    page=4,
    doc="LK_AGRIC,t = 44/12 * ( Delta_C_BIOMASS,t + Delta_SOC_LUC,t )",
)
def displacement_leakage_total(
    delta_c_biomass_tc: float,
    delta_soc_luc_tc: float,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Eq.1: Total GHG emissions from displacement of pre-project agriculture (t CO2e)."""
    return float((44.0 / 12.0) * (delta_c_biomass_tc + delta_soc_luc_tc))
