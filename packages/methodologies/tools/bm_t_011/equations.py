"""BM-T-011 Solid Waste Disposal Site (SWDS) Equations."""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence, Union
import numpy as np

from dmrv_core.equations import CalculationContext, equation


@equation(
    tool="BM-T-011",
    version="1.0",
    eq="3",
    page=8,
    doc="Model uncertainty: V_y = sqrt(a^2 + b^2 + c^2 + d^2 + e^2 + g^2)",
)
def model_uncertainty_vector(
    a: float,
    b: float,
    c: float,
    d: float,
    e: float,
    g: float,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Calculate aggregate model uncertainty vector V_y."""
    return float(math.sqrt(a**2 + b**2 + c**2 + d**2 + e**2 + g**2))


@equation(
    tool="BM-T-011",
    version="1.0",
    eq="4",
    page=8,
    doc="Model correction factor: phi_y = 1 / (1 + V_y)",
    errata_ids=["E-T11-02"],
)
def model_correction_factor_option2(
    v_y: float,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Calculate model correction factor phi_y from uncertainty vector V_y."""
    return float(1.0 / (1.0 + v_y))


@equation(
    tool="BM-T-011",
    version="1.0",
    eq="12",
    page=14,
    doc="MCF with high water table: MCF_y = max(1 - 2/d_y, h_w,y / d_y)",
)
def mcf_water_table(
    d_y_m: float,
    h_w_y_m: float,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Calculate MCF when water table is above the base of the SWDS."""
    if d_y_m <= 0.0:
        raise ValueError("SWDS depth d_y must be strictly positive")
    term1 = 1.0 - (2.0 / d_y_m)
    term2 = h_w_y_m / d_y_m
    return float(max(term1, term2))


@equation(
    tool="BM-T-011",
    version="1.0",
    eq="9",
    page=12,
    doc="DOC_f from BMP: DOC_f,y = 0.7 * (12/16) * BMP_MSW / (F * sum_j(p_j * DOC_j))",
)
def doc_f_from_bmp_msw(
    bmp_msw_t_ch4_per_t: float,
    f_param: float,
    p_j: Dict[str, float],
    doc_j: Optional[Dict[str, float]] = None,
    ctx: Optional[CalculationContext] = None,
) -> Dict[str, float]:
    """Calculate DOC_f for MSW from Biochemical Methane Potential test results."""
    # Standard default DOC_j if not provided
    default_docs = {
        "wood": 0.43,
        "paper_cardboard": 0.40,
        "food": 0.15,
        "textiles": 0.24,
        "garden": 0.20,
        "inert": 0.0,
    }
    docs = doc_j or default_docs

    sum_p_doc = 0.0
    for waste_type, frac in p_j.items():
        doc_val = docs.get(waste_type, 0.0)
        sum_p_doc += float(frac) * float(doc_val)

    if sum_p_doc <= 0.0 or f_param <= 0.0:
        raise ValueError("Denominator in DOC_f equation must be positive")

    doc_f = 0.7 * (12.0 / 16.0) * float(bmp_msw_t_ch4_per_t) / (float(f_param) * sum_p_doc)
    return {
        "sum_p_DOC": float(sum_p_doc),
        "DOC_f_y": float(doc_f),
    }


@equation(
    tool="BM-T-011",
    version="1.0",
    eq="1",
    page=5,
    doc="Yearly FOD model: E_y = phi*(1-f)*GWP*(1-OX)*(16/12)*F*DOC_f*MCF * sum_{x=1..y} sum_j W_{j,x}*DOC_j*e^{-k_j(y-x)}*(1-e^{-k_j})",
)
def yearly_fod_emissions(
    phi_y: float,
    f_y: float,
    gwp_ch4: float,
    ox: float,
    f_param: float,
    doc_f_y: float,
    mcf_y: float,
    waste_streams: Sequence[Dict[str, float]],  # list of {waste_type: tonnes} per disposal year x
    doc_j: Dict[str, float],
    k_j: Dict[str, float],
    ctx: Optional[CalculationContext] = None,
) -> List[float]:
    """Calculate annual methane emissions (tCO2e/yr) across years 1..Y from historical waste cohorts."""
    # Constant multiplier term:
    # C = phi_y * (1 - f_y) * GWP_CH4 * (1 - OX) * (16/12) * F * DOC_f,y * MCF_y
    base_factor = (
        float(phi_y)
        * (1.0 - float(f_y))
        * float(gwp_ch4)
        * (1.0 - float(ox))
        * (16.0 / 12.0)
        * float(f_param)
        * float(doc_f_y)
        * float(mcf_y)
    )

    n_years = len(waste_streams)
    emissions_by_year: List[float] = []

    # Precompute (1 - exp(-k_j)) and exp(-k_j) for each waste type
    waste_types = list(doc_j.keys())
    decay_factors = {j: math.exp(-k_j[j]) if j in k_j else 0.0 for j in waste_types}
    start_emit_factors = {j: (1.0 - math.exp(-k_j[j])) if j in k_j else 0.0 for j in waste_types}

    for y_idx in range(n_years):
        # y is 0-indexed year index (representing crediting year y_idx + 1)
        # Sum over disposal years x from 0 to y_idx
        accumulated_emissions = 0.0

        for x_idx in range(y_idx + 1):
            cohort = waste_streams[x_idx]
            elapsed_years = y_idx - x_idx

            for j in waste_types:
                w_jx = float(cohort.get(j, 0.0))
                if w_jx <= 0.0:
                    continue
                d_j = float(doc_j.get(j, 0.0))
                k_val = float(k_j.get(j, 0.0))
                if d_j <= 0.0 or k_val <= 0.0:
                    continue

                # Term: W_j,x * DOC_j * e^{-k_j(y-x)} * (1 - e^{-k_j})
                term = w_jx * d_j * math.exp(-k_val * elapsed_years) * (1.0 - math.exp(-k_val))
                accumulated_emissions += term

        total_y = base_factor * accumulated_emissions
        emissions_by_year.append(float(total_y))

    return emissions_by_year


@equation(
    tool="BM-T-011",
    version="1.0",
    eq="2",
    page=6,
    doc="Monthly FOD model: E_m = phi*(1-f)*GWP*(1-OX)*(16/12)*F*DOC_f*MCF * sum_{i=1..m} sum_j W_{j,i}*DOC_j*e^{-(k_j/12)(m-i)}*(1-e^{-k_j/12})",
)
def monthly_fod_emissions(
    phi_y: float,
    f_y: float,
    gwp_ch4: float,
    ox: float,
    f_param: float,
    doc_f_m: float,
    mcf_y: float,
    monthly_waste_streams: Sequence[Dict[str, float]],  # list of {waste_type: tonnes} per month
    doc_j: Dict[str, float],
    k_j: Dict[str, float],
    ctx: Optional[CalculationContext] = None,
) -> List[float]:
    """Calculate monthly methane emissions (tCO2e/month) across months 1..M."""
    base_factor = (
        float(phi_y)
        * (1.0 - float(f_y))
        * float(gwp_ch4)
        * (1.0 - float(ox))
        * (16.0 / 12.0)
        * float(f_param)
        * float(doc_f_m)
        * float(mcf_y)
    )

    n_months = len(monthly_waste_streams)
    emissions_by_month: List[float] = []
    waste_types = list(doc_j.keys())

    for m_idx in range(n_months):
        accumulated_emissions = 0.0
        for i_idx in range(m_idx + 1):
            cohort = monthly_waste_streams[i_idx]
            elapsed_months = m_idx - i_idx

            for j in waste_types:
                w_ji = float(cohort.get(j, 0.0))
                if w_ji <= 0.0:
                    continue
                d_j = float(doc_j.get(j, 0.0))
                k_val = float(k_j.get(j, 0.0))
                if d_j <= 0.0 or k_val <= 0.0:
                    continue

                k_monthly = k_val / 12.0
                term = w_ji * d_j * math.exp(-k_monthly * elapsed_months) * (1.0 - math.exp(-k_monthly))
                accumulated_emissions += term

        total_m = base_factor * accumulated_emissions
        emissions_by_month.append(float(total_m))

    return emissions_by_month


__all__ = [
    "model_uncertainty_vector",
    "model_correction_factor_option2",
    "mcf_water_table",
    "doc_f_from_bmp_msw",
    "yearly_fod_emissions",
    "monthly_fod_emissions",
]
