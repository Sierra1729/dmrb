"""BM-T-AR-0006: Change in SOC stocks due to A/R (factor-based)."""
from __future__ import annotations

from typing import Optional, Sequence
from dmrv_core.equations import CalculationContext, equation


@equation(
    tool="BM-T-AR-0006",
    version="1.0",
    eq="1",
    page=5,
    doc="SOC_INITIAL,i = SOC_REF,i * f_LU,i * f_MG,i * f_IN,i",
)
def initial_soil_organic_carbon(
    soc_ref: float,
    f_lu: float,
    f_mg: float,
    f_in: float,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Eq.1: Initial SOC stock in mineral soil (t C/ha)."""
    return float(soc_ref * f_lu * f_mg * f_in)


@equation(
    tool="BM-T-AR-0006",
    version="1.0",
    eq="2",
    page=5,
    doc="SOC_LOSS,i = 0.1 * SOC_INITIAL,i",
)
def soil_disturbance_loss(
    soc_initial: float,
    disturbance_fraction: float,
    threshold: float = 0.10,
    loss_factor: float = 0.10,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Eq.2 & Eq.3: SOC loss from site preparation soil disturbance (t C/ha)."""
    if disturbance_fraction > threshold:
        return float(loss_factor * soc_initial)
    return 0.0


@equation(
    tool="BM-T-AR-0006",
    version="1.0",
    eq="6",
    page=6,
    doc="dSOC_t,i = ( SOC_REF,i - (SOC_INITIAL,i - SOC_LOSS,i) ) / 20",
    errata_ids=["E-AR6-04"],
)
def annual_soc_accumulation_rate(
    soc_ref: float,
    soc_initial: float,
    soc_loss: float,
    transition_years: int = 20,
    max_rate_cap: float = 0.80,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Eq.6 & Eq.7: Annual rate of change in SOC stock during transition (t C/ha/yr).
    Capped at 0.8 t C/ha/yr per Eq.7.
    """
    post_prep_stock = soc_initial - soc_loss
    uncapped_rate = (soc_ref - post_prep_stock) / transition_years
    if uncapped_rate > max_rate_cap:
        return float(max_rate_cap)
    return float(uncapped_rate)


@equation(
    tool="BM-T-AR-0006",
    version="1.0",
    eq="4_5_6",
    page=6,
    doc="dSOC_t,i by project year t",
    errata_ids=["E-AR6-04"],
)
def soc_rate_at_year(
    t: int,
    t_prep: int,
    soc_loss: float,
    accumulation_rate: float,
    transition_years: int = 20,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Eq.4, 5, 6: Annual rate of change dSOC_t,i for a given project year t (t C/ha/yr)."""
    if t < t_prep:
        return 0.0
    elif t == t_prep:
        return -float(soc_loss)
    elif t_prep < t <= t_prep + transition_years:
        return float(accumulation_rate)
    else:
        # After t_PREP + 20: steady state reached, dSOC = 0 (Errata E-AR6-04)
        return 0.0


@equation(
    tool="BM-T-AR-0006",
    version="1.0",
    eq="8",
    page=7,
    doc="Delta_SOC_AL,t = 44/12 * sum_i (A_i * dSOC_t,i * 1_year)",
)
def total_stratum_soc_change(
    stratum_areas_ha: Sequence[float],
    dsoc_rates_t_c_ha_yr: Sequence[float],
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Eq.8: Annual change in SOC stock for the project (t CO2e/yr)."""
    sum_a_dsoc = sum(a * r for a, r in zip(stratum_areas_ha, dsoc_rates_t_c_ha_yr, strict=True))
    return float((44.0 / 12.0) * sum_a_dsoc)
