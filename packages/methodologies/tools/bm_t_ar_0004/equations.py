"""BM-T-AR-0004: Carbon Stocks and Change in Living Trees and Shrubs (A/R).

All equations decorated and citing source PDF equations verbatim.
"""
from __future__ import annotations

import math
from typing import Optional, Sequence
import numpy as np

from dmrv_core.equations import CalculationContext, equation
from dmrv_core.statistics import sample_variance, t_two_sided


@equation(
    tool="BM-T-AR-0004",
    version="1.0",
    eq="App1_R",
    page=26,
    doc="R_j = exp(-1.085 + 0.9256 * ln(b)) / b",
)
def root_shoot_ratio(b_ag: float, ctx: Optional[CalculationContext] = None) -> float:
    """Default root-shoot ratio from above-ground biomass b (t d.m./ha)."""
    if b_ag <= 0.0:
        raise ValueError("Above-ground biomass must be positive for root-shoot ratio calculation")
    return float(math.exp(-1.085 + 0.9256 * math.log(b_ag)) / b_ag)


@equation(
    tool="BM-T-AR-0004",
    version="1.0",
    eq="1",
    page=7,
    doc="Delta_C_TREE = C_TREE,t2 - C_TREE,t1",
)
def difference_of_stocks(
    c_t2: float,
    c_t1: float,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Eq.1: Carbon stock change as difference of two independent estimates."""
    return float(c_t2 - c_t1)


@equation(
    tool="BM-T-AR-0004",
    version="1.0",
    eq="2",
    page=7,
    doc="u_Delta_C = sqrt((u1 * C_TREE,t1)^2 + (u2 * C_TREE,t2)^2) / |Delta_C_TREE|",
)
def uncertainty_difference_of_stocks(
    c_t1: float,
    u1: float,
    c_t2: float,
    u2: float,
    delta_c: float,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Eq.2: Uncertainty of stock difference."""
    if abs(delta_c) == 0.0:
        return 0.0
    return float(math.sqrt((u1 * c_t1) ** 2 + (u2 * c_t2) ** 2) / abs(delta_c))


@equation(
    tool="BM-T-AR-0004",
    version="1.0",
    eq="11",
    page=11,
    doc="Delta_C_TREE,t = (C_TREE,t2 - C_TREE,t1) / T * 1_year",
)
def annual_change(
    c_t1: float,
    c_t2: float,
    t_years: float,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Eq.11: Annualized stock change over elapsed time T."""
    if t_years <= 0.0:
        raise ValueError("Time interval T must be positive")
    return float((c_t2 - c_t1) / t_years)


@equation(
    tool="BM-T-AR-0004",
    version="1.0",
    eq="12",
    page=12,
    doc="C_TREE = 44/12 * CF_TREE * B_TREE",
)
def carbon_stock_from_biomass(
    b_tree_total: float,
    cf_tree: float = 0.47,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Eq.12: Carbon stock in trees (t CO2e) from total tree biomass (t d.m.)."""
    return float((44.0 / 12.0) * cf_tree * b_tree_total)


@equation(
    tool="BM-T-AR-0004",
    version="1.0",
    eq="13",
    page=12,
    doc="B_TREE = A * b_TREE",
)
def total_biomass_from_mean(
    total_area_ha: float,
    mean_biomass_per_ha: float,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Eq.13: Total biomass (t d.m.) from mean biomass per hectare."""
    return float(total_area_ha * mean_biomass_per_ha)


@equation(
    tool="BM-T-AR-0004",
    version="1.0",
    eq="14",
    page=13,
    doc="b_TREE = sum_i (w_i * b_TREE,i)",
)
def stratified_mean_biomass(
    weights: Sequence[float],
    stratum_means: Sequence[float],
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Eq.14: Stratified mean biomass per hectare (t d.m./ha)."""
    return float(np.sum(np.asarray(weights) * np.asarray(stratum_means)))


@equation(
    tool="BM-T-AR-0004",
    version="1.0",
    eq="15",
    page=14,
    doc="u_C = t_VAL * sqrt(sum_i (w_i^2 * s_i^2 / n_i)) / b_TREE",
    errata_ids=["E-AR4-07"],
)
def stratified_uncertainty(
    weights: Sequence[float],
    stratum_variances: Sequence[float],
    stratum_plot_counts: Sequence[int],
    overall_mean: float,
    t_val: float,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Eq.15: Relative uncertainty of stratified tree biomass estimation."""
    if overall_mean == 0.0:
        return 0.0
    var_terms = [
        (w ** 2) * (s2 / n)
        for w, s2, n in zip(weights, stratum_variances, stratum_plot_counts, strict=True)
    ]
    sem = math.sqrt(sum(var_terms))
    return float(t_val * sem / overall_mean)


@equation(
    tool="BM-T-AR-0004",
    version="1.0",
    eq="16",
    page=14,
    doc="b_TREE,i = sum_p (b_TREE,p,i) / n_i",
)
def stratum_mean_biomass(
    plot_biomass_values: Sequence[float],
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Eq.16: Mean biomass in stratum i."""
    if not plot_biomass_values:
        raise ValueError("plot_biomass_values cannot be empty")
    return float(np.mean(plot_biomass_values))


@equation(
    tool="BM-T-AR-0004",
    version="1.0",
    eq="17",
    page=14,
    doc="s_i^2 = sample_variance(b_TREE,p,i)",
)
def stratum_variance(
    plot_biomass_values: Sequence[float],
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Eq.17: Sample variance of plot biomass in stratum i."""
    return sample_variance(plot_biomass_values)


@equation(
    tool="BM-T-AR-0004",
    version="1.0",
    eq="18",
    page=15,
    doc="b_TREE,i = mean_sub + beta * (x_all - x_sub)",
    errata_ids=["E-AR4-03"],
)
def double_sampling_mean(
    mean_sub: float,
    beta: float,
    mean_sec_all: float,
    mean_sec_sub: float,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Eq.18: Double sampling regression estimate of stratum mean."""
    return float(mean_sub + beta * (mean_sec_all - mean_sec_sub))


@equation(
    tool="BM-T-AR-0004",
    version="1.0",
    eq="19",
    page=15,
    doc="s_i^2 = s_sub^2 * (1 - (1 - alpha) * rho^2)",
    errata_ids=["E-AR4-03"],
)
def double_sampling_variance(
    s2_sub: float,
    alpha: float,
    rho: float,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Eq.19: Double sampling variance."""
    return float(s2_sub * (1.0 - (1.0 - alpha) * (rho ** 2)))


@equation(
    tool="BM-T-AR-0004",
    version="1.0",
    eq="10",
    page=10,
    doc="Delta_C_TREE_BSL,i = 44/12 * CF_TREE * Delta_b_FOREST * (1 + R_TREE) * CC_TREE_BSL,i * A_i",
)
def proportionate_crown_cover_annual_change(
    delta_b_forest: float,
    cc_tree_bsl: float,
    area_ha: float,
    cf_tree: float = 0.47,
    r_tree: float = 0.25,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Eq.10: Annual baseline carbon stock change from proportionate crown cover."""
    return float((44.0 / 12.0) * cf_tree * delta_b_forest * (1.0 + r_tree) * cc_tree_bsl * area_ha)


@equation(
    tool="BM-T-AR-0004",
    version="1.0",
    eq="21",
    page=17,
    doc="C_TREE_BSL,i = 44/12 * CF_TREE * b_FOREST * (1 + R_TREE) * CC_TREE_BSL,i * A_i",
)
def proportionate_crown_cover_baseline_stock(
    b_forest: float,
    cc_tree_bsl: float,
    area_ha: float,
    cf_tree: float = 0.47,
    r_tree: float = 0.25,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Eq.21: Baseline tree carbon stock from proportionate crown cover."""
    return float((44.0 / 12.0) * cf_tree * b_forest * (1.0 + r_tree) * cc_tree_bsl * area_ha)


@equation(
    tool="BM-T-AR-0004",
    version="1.0",
    eq="26",
    page=19,
    doc="C_SHRUB,t = 44/12 * CF_S * (1 + R_S) * sum_i (A_SHRUB,i * b_SHRUB,i)",
    errata_ids=["E-AR4-06"],
)
def shrub_carbon_stock(
    stratum_areas: Sequence[float],
    stratum_shrub_biomass: Sequence[float],
    cf_s: float = 0.47,
    r_s: float = 0.40,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Eq.26: Total shrub carbon stock (t CO2e)."""
    total_shrub_biomass = np.sum(np.asarray(stratum_areas) * np.asarray(stratum_shrub_biomass))
    return float((44.0 / 12.0) * cf_s * (1.0 + r_s) * total_shrub_biomass)


@equation(
    tool="BM-T-AR-0004",
    version="1.0",
    eq="27",
    page=19,
    doc="b_SHRUB,i = BDR_SF * b_FOREST * CC_SHRUB,i",
)
def shrub_stratum_biomass(
    b_forest: float,
    cc_shrub: float,
    bdr_sf: float = 0.10,
    shrub_cc_zero_below: float = 0.05,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Eq.27: Shrub biomass per hectare in stratum i."""
    if cc_shrub < shrub_cc_zero_below:
        return 0.0
    return float(bdr_sf * b_forest * cc_shrub)
