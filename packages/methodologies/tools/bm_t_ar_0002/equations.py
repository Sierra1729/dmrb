"""BM-T-AR-0002: Non-CO2 GHG emissions from biomass burning (A/R)."""
from __future__ import annotations

from typing import Optional, Sequence
from dmrv_core.equations import CalculationContext, equation


@equation(
    tool="BM-T-AR-0002",
    version="1.0",
    eq="3",
    page=5,
    doc="GHG_SPF,t = 0.07 * sum_i A_SPF,i,t * 44/12 * ( CF_TREE * b_TREE,i + BDR_SF * CF_SHRUB * CC_SHRUB,i * B_FOREST )",
)
def site_prep_fire_emissions(
    a_spf_ha: float,
    b_tree: float,
    cc_shrub: float,
    b_forest: float,
    cf_tree: float = 0.50,
    cf_shrub: float = 0.50,
    bdr_sf: float = 0.10,
    ratio_non_co2: float = 0.07,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Eq.3: Non-CO2 emissions from fire in site preparation (t CO2e)."""
    tree_term = cf_tree * b_tree
    shrub_term = bdr_sf * cf_shrub * cc_shrub * b_forest
    return float(ratio_non_co2 * a_spf_ha * (44.0 / 12.0) * (tree_term + shrub_term))


@equation(
    tool="BM-T-AR-0002",
    version="1.0",
    eq="5",
    page=6,
    doc="B_HARVEST,t = B_FOREST / BEF2 * A_FMF,t",
)
def harvest_biomass_default(
    b_forest: float,
    a_fmf_ha: float,
    bef2: float = 1.25,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Eq.5: Harvested biomass (t d.m.) when harvest records unavailable."""
    if bef2 <= 0.0:
        raise ValueError("BEF2 must be positive")
    return float((b_forest / bef2) * a_fmf_ha)


@equation(
    tool="BM-T-AR-0002",
    version="1.0",
    eq="4",
    page=6,
    doc="GHG_FMF,t = 0.07 * 44/12 * B_HARVEST,t * f_BL * CF_TREE",
)
def harvest_residue_fire_emissions(
    b_harvest_t_dm: float,
    f_bl: float = 0.25,
    cf_tree: float = 0.50,
    ratio_non_co2: float = 0.07,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Eq.4: Non-CO2 emissions from burning harvest residues (t CO2e)."""
    return float(ratio_non_co2 * (44.0 / 12.0) * b_harvest_t_dm * f_bl * cf_tree)


@equation(
    tool="BM-T-AR-0002",
    version="1.0",
    eq="7",
    page=7,
    doc="GHG_FF_TREE,t = 0.001 * sum_i A_BURN,i,t * b_TREE,i,tL * COMF_i * ( EF_CH4,i * GWP_CH4 + EF_N2O,i * GWP_N2O )",
    errata_ids=["E-GWP-01"],
)
def forest_fire_living_tree_emissions(
    a_burn_ha: float,
    b_tree_tl: float,
    comf: float,
    ef_ch4_g_kg: float,
    ef_n2o_g_kg: float,
    gwp_ch4: float = 29.8,
    gwp_n2o: float = 273.0,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Eq.7: Non-CO2 emissions from living trees burnt in forest fire (t CO2e)."""
    ghg_factor = ef_ch4_g_kg * gwp_ch4 + ef_n2o_g_kg * gwp_n2o
    return float(0.001 * a_burn_ha * b_tree_tl * comf * ghg_factor)


@equation(
    tool="BM-T-AR-0002",
    version="1.0",
    eq="8",
    page=8,
    doc="GHG_FF_DOM,t = 0.07 * sum_i A_BURN,i,t * ( c_DW,i,tL + c_LI,i,tL )",
    errata_ids=["E-AR2-03"],
)
def forest_fire_dom_emissions(
    a_burn_ha: float,
    c_dw_per_ha: float,
    c_li_per_ha: float,
    ratio_non_co2: float = 0.07,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Eq.8: Non-CO2 emissions from dead organic matter burnt in forest fire (t CO2e).
    c_DW and c_LI must be per-hectare stocks (t CO2e/ha) per Errata E-AR2-03.
    """
    return float(ratio_non_co2 * a_burn_ha * (c_dw_per_ha + c_li_per_ha))


@equation(
    tool="BM-T-AR-0002",
    version="1.0",
    eq="1",
    page=4,
    doc="GHG_E,t = GHG_SPF,t + GHG_FMF,t + GHG_FF,t",
)
def total_biomass_burning_emissions(
    ghg_spf: float,
    ghg_fmf: float,
    ghg_ff: float,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Eq.1: Total non-CO2 GHG emissions from burning of biomass (t CO2e)."""
    return float(ghg_spf + ghg_fmf + ghg_ff)
