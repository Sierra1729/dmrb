"""DRAFT SOC Activity Tools Equations (Cover crops, Improved tillage, Zero tillage, Biostimulants, Pulp & paper sludge)."""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence

from dmrv_core.equations import CalculationContext, equation


@equation(
    tool="SOC-AT-DRAFT",
    version="1.0",
    eq="2",
    page=75,
    doc="Delta FE: delta_FE = sum_y [ EF_FE,y * sum_a max(FE_PR,y,a - FE_BL,y, 0) ]",
    errata_ids=["E-SOCAT-01"],
)
def delta_fertilizer_emissions(
    FE_PR_kgN_by_year: Sequence[float],
    FE_BL_kgN: float,
    EF_FE_as_printed: float = 0.01,
    EF_FE_converted: float = 0.00429,
    has_baseline_records: bool = True,
    ctx: Optional[CalculationContext] = None,
) -> Dict[str, Any]:
    """Calculate fertilizer increase emissions with printed (0.01) and converted (0.00429) factors."""
    fe_pr = [float(x) for x in FE_PR_kgN_by_year]
    bl_val = float(FE_BL_kgN)

    # 50% baseline cap if undocumented
    # Spec 10: BL_used = min(BL_documented, 0.5 * PR)
    excess_kgN_list: List[float] = []
    for pr_y in fe_pr:
        bl_eff = bl_val if has_baseline_records else min(bl_val, 0.50 * pr_y)
        excess = max(pr_y - bl_eff, 0.0)
        excess_kgN_list.append(excess)

    total_excess_kgN = sum(excess_kgN_list)

    # Calculate both printed and converted
    delta_fe_printed = float(total_excess_kgN * float(EF_FE_as_printed))
    delta_fe_converted = float(total_excess_kgN * float(EF_FE_converted))

    use_printed = True
    if ctx is not None:
        use_printed = ctx.get_flag("use_printed_ef_fe", True)

    chosen_delta = delta_fe_printed if use_printed else delta_fe_converted

    return {
        "total_excess_kgN": total_excess_kgN,
        "delta_FE_tCO2e_as_printed": delta_fe_printed,
        "EF_FE_IPCC_EF1_converted_tCO2e_per_kgN": float(EF_FE_converted),
        "delta_FE_tCO2e_converted": delta_fe_converted,
        "delta_FE_tCO2e": chosen_delta,
        "has_baseline_records": has_baseline_records,
    }


@equation(
    tool="SOC-AT-DRAFT",
    version="1.0",
    eq="8",
    page=150,
    doc="Yield leakage: LK_t0 = sum_y [ max((CY_min,y - CY_t,y)/CY_BL,y, 0) * A_bar_y ] * sum(delta_factors_LA)",
    errata_ids=["E-SOCAT-03", "E-SOCAT-09", "E-SOCAT-12"],
)
def yield_leakage(
    CY_BL: float,
    CY_min_prev: float,
    CY_t: float,
    A_bar: float,
    dBC_LA: float = 0.0,
    dSOC_LA: float = 0.0,
    dFE_LA: float = 0.0,
    dFU_LA: float = 0.0,
    ctx: Optional[CalculationContext] = None,
) -> Dict[str, Any]:
    """Calculate yield leakage per cover crops Eq.10 / zero tillage Eq.8."""
    cy_bl = float(CY_BL)
    cy_min = float(CY_min_prev)
    cy_t = float(CY_t)
    a_bar = float(A_bar)

    if cy_bl <= 0.0:
        raise ValueError("Baseline crop yield CY_BL must be strictly positive")

    # Ratio of yield decline below previous minimum
    decline = (cy_min - cy_t) / cy_bl
    decline_floored = max(decline, 0.0)

    # Affected leakage area
    area_leakage = decline_floored * a_bar

    # Sum of leakage area emission factors (t CO2e / ha)
    factor_sum = float(dBC_LA + dSOC_LA + dFE_LA + dFU_LA)

    lk_t0 = float(area_leakage * factor_sum)

    return {
        "CY_BL": cy_bl,
        "CY_min_prev": cy_min,
        "CY_t": cy_t,
        "yield_decline_fraction": decline_floored,
        "area_leakage_ha": area_leakage,
        "factor_sum_tCO2e_ha": factor_sum,
        "LK_t0_tCO2e": lk_t0,
    }


@equation(
    tool="SOC-AT-DRAFT",
    version="1.0",
    eq="3",
    page=76,
    doc="Fuel and electricity increase: delta_FU = sum_y sum_a [(FU_PR - FU_BL) + (EU_PR - EU_BL)]",
    errata_ids=["E-SOCAT-02", "E-SOCAT-04"],
)
def fuel_and_electricity_increase(
    FU_PR_by_year: Sequence[float],
    FU_BL: float,
    EU_PR_by_year: Sequence[float],
    EU_BL: float,
    FEF: float = 1.0,
    EEF: float = 1.0,
    has_baseline_records: bool = True,
    ctx: Optional[CalculationContext] = None,
) -> Dict[str, Any]:
    """Calculate fuel and electricity emissions increase across calculation period."""
    fu_pr = [float(x) for x in FU_PR_by_year]
    eu_pr = [float(x) for x in EU_PR_by_year]
    fu_bl = float(FU_BL)
    eu_bl = float(EU_BL)

    n_years = max(len(fu_pr), len(eu_pr))
    total_delta_fu = 0.0
    total_delta_eu = 0.0

    for i in range(n_years):
        pr_f = fu_pr[i] if i < len(fu_pr) else 0.0
        pr_e = eu_pr[i] if i < len(eu_pr) else 0.0

        eff_bl_f = fu_bl if has_baseline_records else min(fu_bl, 0.50 * pr_f)
        eff_bl_e = eu_bl if has_baseline_records else min(eu_bl, 0.50 * pr_e)

        diff_f = (pr_f - eff_bl_f) * float(FEF)
        diff_e = (pr_e - eff_bl_e) * float(EEF)

        total_delta_fu += diff_f
        total_delta_eu += diff_e

    # Floored at 0 if no net increase demonstrated
    net_increase = max(total_delta_fu + total_delta_eu, 0.0)

    return {
        "delta_FU_tCO2e": total_delta_fu,
        "delta_EU_tCO2e": total_delta_eu,
        "net_fuel_electricity_increase_tCO2e": net_increase,
    }


@equation(
    tool="SOC-AT-DRAFT",
    version="1.0",
    eq="7",
    page=77,
    doc="Seed production and transport emissions: SPT_PR = sum_c [ (S_PR * A_PR) * (EF_SP + EF_ST * DistST_PR) ]",
    errata_ids=["E-SOCAT-10"],
)
def seed_production_and_transport(
    seed_rate_kg_ha: float,
    area_ha: float,
    ef_seed_production: float,
    ef_seed_transport: float,
    transport_distance_km: float,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Calculate seed production and transport emissions in t CO2e."""
    s_kg = float(seed_rate_kg_ha) * float(area_ha)
    ef_sp = float(ef_seed_production)
    ef_st = float(ef_seed_transport)
    dist = float(transport_distance_km)
    spt = s_kg * (ef_sp + ef_st * dist)
    return float(spt)


__all__ = [
    "delta_fertilizer_emissions",
    "yield_leakage",
    "fuel_and_electricity_increase",
    "seed_production_and_transport",
]
