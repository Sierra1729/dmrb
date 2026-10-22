"""BM AG04.002 Improved Management Practices in Rice Cultivation Equations."""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence

from dmrv_core.equations import CalculationContext, equation


@equation(
    tool="BM-AG04.002",
    version="1.0",
    eq="1",
    page=7,
    doc="Baseline emissions: BE_s = sum_g ( EF_BL,s,g * A_s,g ) * 10^-3 * GWP_CH4",
)
def baseline_ch4_emissions_season(
    ef_bl_kg_ha_season: Sequence[float],
    area_ha: Sequence[float],
    gwp_ch4: float = 29.8,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Calculate seasonal baseline methane emissions in t CO2e."""
    efs = [float(x) for x in ef_bl_kg_ha_season]
    areas = [float(x) for x in area_ha]
    if len(efs) != len(areas):
        raise ValueError("Emission factors and areas must have equal length")

    total_kg_ch4 = sum(ef * a for ef, a in zip(efs, areas))
    return float(total_kg_ch4 * 1e-3 * float(gwp_ch4))


@equation(
    tool="BM-AG04.002",
    version="1.0",
    eq="4",
    page=9,
    doc="Project CH4 emissions: PE_s = sum_g ( EF_P,s,g * A_s,g ) * 10^-3 * GWP_CH4",
)
def project_ch4_emissions_season(
    ef_p_kg_ha_season: Sequence[float],
    area_ha: Sequence[float],
    gwp_ch4: float = 29.8,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Calculate seasonal project methane emissions in t CO2e."""
    efs = [float(x) for x in ef_p_kg_ha_season]
    areas = [float(x) for x in area_ha]
    if len(efs) != len(areas):
        raise ValueError("Emission factors and areas must have equal length")

    total_kg_ch4 = sum(ef * a for ef, a in zip(efs, areas))
    return float(total_kg_ch4 * 1e-3 * float(gwp_ch4))


@equation(
    tool="BM-AG04.002",
    version="1.0",
    eq="21",
    page=9,
    doc="Project N2O emissions: PE_n = sum_g ( Q_n,P,g * A_s,g ) * max(EF_N2O,P - EF_N2O,B, 0) * (44/28) * 10^-3 * GWP_N2O",
    errata_ids=["E-AG2-01"],
)
def project_n2o_emissions(
    q_n_kg_ha: Sequence[float],
    area_ha: Sequence[float],
    ef_n2o_p: float = 0.005,
    ef_n2o_b: float = 0.003,
    gwp_n2o: float = 273.0,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Calculate incremental N2O project emissions in t CO2e with 44/28 N2O-N to N2O conversion."""
    qs = [float(x) for x in q_n_kg_ha]
    areas = [float(x) for x in area_ha]
    if len(qs) != len(areas):
        raise ValueError("Nitrogen rates and areas must have equal length")

    use_corrected = True
    if ctx is not None:
        use_corrected = ctx.get_flag("use_corrected_pen_sign_and_n2o_conversion", True)

    if use_corrected:
        # Corrected sign and 44/28 stoichiometric conversion
        delta_ef = max(float(ef_n2o_p) - float(ef_n2o_b), 0.0)
        conversion_factor = 44.0 / 28.0
    else:
        # Literal printed (gives negative if ef_n2o_p > ef_n2o_b)
        delta_ef = float(ef_n2o_b) - float(ef_n2o_p)
        conversion_factor = 1.0

    total_n_kg = sum(q * a for q, a in zip(qs, areas))
    total_t_co2e = total_n_kg * delta_ef * conversion_factor * 1e-3 * float(gwp_n2o)
    return float(total_t_co2e)


@equation(
    tool="BM-AG04.002",
    version="1.0",
    eq="10",
    page=12,
    doc="Organic amendment scaling factor: SF_o = (1 + sum_i ROA_i * CFOA_i)^0.59",
)
def organic_amendment_scaling_factor(
    roa_by_type: Sequence[float],
    cfoa_by_type: Sequence[float],
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Calculate IPCC organic amendment scaling factor SF_o."""
    roas = [float(x) for x in roa_by_type]
    cfoas = [float(x) for x in cfoa_by_type]
    sum_product = sum(r * c for r, c in zip(roas, cfoas))
    return float(math.pow(1.0 + sum_product, 0.59))


@equation(
    tool="BM-AG04.002",
    version="1.0",
    eq="8-9",
    page=11,
    doc="Tier 1 emission factor: EF = EF_c * SF_w * SF_p * SF_o",
)
def tier1_emission_factor(
    ef_baseline_continuous: float,
    sf_w: float,
    sf_p: float = 1.0,
    sf_o: float = 1.0,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Calculate scaled Tier 1 emission factor in kg CH4/ha/season or kg CH4/ha/day."""
    return float(float(ef_baseline_continuous) * float(sf_w) * float(sf_p) * float(sf_o))


@equation(
    tool="BM-AG04.002",
    version="1.0",
    eq="5",
    page=10,
    doc="Net emission reductions: ER_y = ( BE_y - PE_y ) * ( 1 - U_d )",
    errata_ids=["E-AG2-02"],
)
def net_emission_reductions_rice(
    be_y_tco2e: float,
    pe_y_tco2e: float,
    u_d: float = 0.15,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Calculate net greenhouse gas emission reductions with uncertainty deduction."""
    net = float(be_y_tco2e) - float(pe_y_tco2e)
    if net <= 0.0:
        return 0.0
    u = min(max(float(u_d), 0.0), 1.0)
    return float(net * (1.0 - u))


__all__ = [
    "baseline_ch4_emissions_season",
    "project_ch4_emissions_season",
    "project_n2o_emissions",
    "organic_amendment_scaling_factor",
    "tier1_emission_factor",
    "net_emission_reductions_rice",
]
