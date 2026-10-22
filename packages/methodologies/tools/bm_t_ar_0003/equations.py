"""BM-T-AR-0003: Carbon stocks and change in dead wood and litter (A/R)."""
from __future__ import annotations

import math
from typing import Optional, Sequence
import numpy as np

from dmrv_core.equations import CalculationContext, equation


@equation(
    tool="BM-T-AR-0003",
    version="1.0",
    eq="2",
    page=7,
    doc="B_DW_TREE,j,p,i,t = (1 + R_j) * sum_k (f_j(DBH_k, H_k) * alpha_k)",
)
def standing_dead_biomass_allometric(
    tree_agb_list: Sequence[float],
    alpha_list: Sequence[float],
    r_j: float = 0.25,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Eq.2: Standing dead tree biomass (t d.m.) via allometric route."""
    weighted_agb = sum(b * a for b, a in zip(tree_agb_list, alpha_list, strict=True))
    return float((1.0 + r_j) * weighted_agb)


@equation(
    tool="BM-T-AR-0003",
    version="1.0",
    eq="3",
    page=7,
    doc="C_DWS_TREE,j,p,i,t = 44/12 * CF_TREE * B_DWS_TREE,j,p,i,t",
    errata_ids=["E-CF-01"],
)
def standing_dead_carbon(
    biomass_t_dm: float,
    cf_tree: float = 0.50,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Eq.3: Standing dead tree carbon stock (t CO2e)."""
    return float((44.0 / 12.0) * cf_tree * biomass_t_dm)


@equation(
    tool="BM-T-AR-0003",
    version="1.0",
    eq="4",
    page=8,
    doc="D_MID_STUMP = 0.57 * DBH_k * ( H_STUMP / (H_STUMP - H_DBH) )^0.80",
    errata_ids=["E-AR3-02"],
)
def stump_mid_diameter(
    dbh_m: float,
    h_stump_m: float,
    h_dbh_m: float = 1.3,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Eq.4: Mid-height diameter for stumps with height >= 4 m (Ormerod bole model)."""
    if h_stump_m < 4.0:
        raise ValueError("Eq.4 is only for stump height >= 4 m; for < 4 m measure mid-diameter directly.")
    if h_stump_m <= h_dbh_m:
        raise ValueError("Stump height must exceed DBH measurement height (1.3 m)")
    return float(0.57 * dbh_m * ((h_stump_m / (h_stump_m - h_dbh_m)) ** 0.80))


@equation(
    tool="BM-T-AR-0003",
    version="1.0",
    eq="5",
    page=8,
    doc="C_DW_STUMP = 44/12 * CF_TREE * D_j * (1 + R_j) * (pi/4) * sum_k (D_MID^2 * H * beta_k)",
    errata_ids=["E-CF-01"],
)
def stump_carbon(
    mid_diameters_m: Sequence[float],
    heights_m: Sequence[float],
    beta_list: Sequence[float],
    wood_density: float,
    r_j: float = 0.25,
    cf_tree: float = 0.50,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Eq.5: Carbon stock in stumps in plot (t CO2e)."""
    sum_term = sum(
        (d ** 2) * h * b
        for d, h, b in zip(mid_diameters_m, heights_m, beta_list, strict=True)
    )
    return float((44.0 / 12.0) * cf_tree * wood_density * (1.0 + r_j) * (math.pi / 4.0) * sum_term)


@equation(
    tool="BM-T-AR-0003",
    version="1.0",
    eq="6",
    page=9,
    doc="C_DWL,j,p,i,t = a_plot * 44/12 * CF_TREE * D_j * (pi^2 / (8 L)) * sum_n (D_n^2 * beta_n)",
    errata_ids=["E-CF-01"],
)
def lying_dead_wood_carbon(
    plot_area_ha: float,
    transect_length_m: float,
    wood_density: float,
    diameters_cm: Sequence[float],
    beta_list: Sequence[float],
    cf_tree: float = 0.50,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Eq.6: Lying dead wood carbon in plot via line-intersect method (Harmon & Sexton 1996)."""
    if transect_length_m <= 0.0:
        raise ValueError("Transect length L must be positive")
    sum_d2_beta = sum(
        (d ** 2) * b
        for d, b in zip(diameters_cm, beta_list, strict=True)
    )
    vol_per_ha = (math.pi ** 2 / (8.0 * transect_length_m)) * sum_d2_beta
    return float(plot_area_ha * (44.0 / 12.0) * cf_tree * wood_density * vol_per_ha)


@equation(
    tool="BM-T-AR-0003",
    version="1.0",
    eq="7",
    page=10,
    doc="C_DW,i,t = A_i / A_PLOT,i * sum_p (C_DW,p,i,t)",
)
def stratum_dead_wood_carbon(
    stratum_area_ha: float,
    total_plot_area_ha: float,
    plot_deadwood_carbon_sum: float,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Eq.7: Total dead wood carbon stock in stratum i (t CO2e)."""
    if total_plot_area_ha <= 0.0:
        raise ValueError("Total plot area in stratum must be positive")
    return float((stratum_area_ha / total_plot_area_ha) * plot_deadwood_carbon_sum)


@equation(
    tool="BM-T-AR-0003",
    version="1.0",
    eq="9",
    page=11,
    doc="C_DW,i,t = C_TREE,i,t * DF_DW / 100",
    errata_ids=["E-AR3-04"],
)
def dead_wood_default_factor(
    c_tree_i: float,
    df_dw_pct: float,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Eq.9: Dead wood carbon stock via conservative default factor."""
    return float(c_tree_i * (df_dw_pct / 100.0))


@equation(
    tool="BM-T-AR-0003",
    version="1.0",
    eq="12",
    page=13,
    doc="C_LI,p,i,t = 44/12 * CF_LI * 2.5 * (A_p,i / a_p,i) * B_LI_wet,p,i * DWR_LI,p,i",
    errata_ids=["E-AR3-07"],
)
def litter_plot_carbon(
    b_li_wet_kg: float,
    dwr: float,
    plot_area_ha: float,
    frame_area_m2: float = 0.5,
    n_frames: int = 4,
    cf_li: float = 0.37,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Eq.12: Litter carbon stock in sample plot (t CO2e).
    The factor 2.5 combines conversion factors for exactly 4 frames (10 / 4 = 2.5).
    """
    if frame_area_m2 <= 0.0 or n_frames <= 0:
        raise ValueError("Frame area and frame count must be positive")
    frame_factor = 10.0 / n_frames
    return float((44.0 / 12.0) * cf_li * frame_factor * (plot_area_ha / frame_area_m2) * b_li_wet_kg * dwr)


@equation(
    tool="BM-T-AR-0003",
    version="1.0",
    eq="15",
    page=14,
    doc="C_LI,i,t = C_TREE,i,t * DF_LI / 100",
    errata_ids=["E-AR3-04"],
)
def litter_default_factor(
    c_tree_i: float,
    df_li_pct: float,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Eq.15: Litter carbon stock via conservative default factor."""
    return float(c_tree_i * (df_li_pct / 100.0))
