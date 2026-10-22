"""BM AG04.001 Methane Recovery from Livestock and Manure Management Equations."""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence

from dmrv_core.equations import CalculationContext, equation


@equation(
    tool="BM-AG04.001",
    version="1.0",
    eq="1",
    page=6,
    doc="Baseline emissions: BE_y = sum [ N * (AM/1000) * VS_rate * 365 * B0 * 0.67 * 10^-3 * (MCF/100) * MS_frac * GWP_CH4 * UF_b ]",
    errata_ids=["E-AG1-01"],
)
def baseline_manure_emissions(
    num_animals: Sequence[float],
    animal_mass_kg: Sequence[float],
    vs_rate_kg_per_1000kg_day: Sequence[float],
    b0_m3_kg_vs: Sequence[float],
    mcf_pct: Sequence[float],
    ms_fraction: Sequence[float],
    uf_b: float = 0.89,
    gwp_ch4: float = 29.8,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Calculate baseline manure methane emissions in t CO2e."""
    n_items = len(num_animals)
    total_be = 0.0

    for i in range(n_items):
        n = float(num_animals[i])
        mass = float(animal_mass_kg[i])
        vs_rate = float(vs_rate_kg_per_1000kg_day[i])
        b0 = float(b0_m3_kg_vs[i])
        mcf = float(mcf_pct[i])
        ms = float(ms_fraction[i])

        # VS excreted per year per animal (kg VS/yr)
        annual_vs_head = (mass / 1000.0) * vs_rate * 365.0
        # Methane generation potential in m3 CH4
        ch4_m3 = n * annual_vs_head * b0
        # Convert m3 CH4 to kg CH4 (0.67 kg/m3) and to tonnes (10^-3)
        ch4_tonnes = ch4_m3 * 0.67 * 1e-3
        # Apply MCF and manure management fraction
        methane_emitted = ch4_tonnes * (mcf / 100.0) * ms
        # Convert to t CO2e with UF_b
        emissions_tco2e = methane_emitted * float(gwp_ch4) * float(uf_b)
        total_be += emissions_tco2e

    return float(total_be)


@equation(
    tool="BM-AG04.001",
    version="1.0",
    eq="3",
    page=7,
    doc="Physical digester leakage: PE_PL_y = 0.10 * max_methane_potential (without UF_b)",
)
def project_physical_leakage(
    num_animals_fed: Sequence[float],
    animal_mass_kg: Sequence[float],
    vs_rate_kg_per_1000kg_day: Sequence[float],
    b0_m3_kg_vs: Sequence[float],
    mcf_pct: Sequence[float],
    ms_fraction: Sequence[float],
    leakage_fraction: float = 0.10,
    gwp_ch4: float = 29.8,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Calculate physical digester methane leakage in t CO2e (default 10%)."""
    # Equivalent to baseline equation with UF_b = 1.0 multiplied by leakage_fraction
    unadjusted_be = baseline_manure_emissions(
        num_animals=num_animals_fed,
        animal_mass_kg=animal_mass_kg,
        vs_rate_kg_per_1000kg_day=vs_rate_kg_per_1000kg_day,
        b0_m3_kg_vs=b0_m3_kg_vs,
        mcf_pct=mcf_pct,
        ms_fraction=ms_fraction,
        uf_b=1.0,
        gwp_ch4=gwp_ch4,
        ctx=ctx,
    )
    return float(float(leakage_fraction) * unadjusted_be)


@equation(
    tool="BM-AG04.001",
    version="1.0",
    eq="5",
    page=8,
    doc="Methane combusted: MD_y = sum_k ( N_k_0 * n_k_y * UF_b * BS_k_y * w_CH4 * D_CH4 * GWP_CH4 )",
    errata_ids=["E-AG1-01"],
)
def methane_combusted_digesters(
    n_commissioned: Sequence[float],
    operating_fraction: Sequence[float],
    biogas_combusted_m3_per_digester: Sequence[float],
    methane_fraction: Sequence[float],
    uf_b: float = 0.89,
    density_ch4_t_m3: float = 0.67e-3,
    gwp_ch4: float = 29.8,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Calculate total methane combusted across domestic digester categories in t CO2e."""
    total_md = 0.0
    for i in range(len(n_commissioned)):
        n0 = float(n_commissioned[i])
        n_op = float(operating_fraction[i])
        bs = float(biogas_combusted_m3_per_digester[i])
        w_ch4 = float(methane_fraction[i])

        # Active operating digesters
        active_digesters = n0 * n_op
        # Total CH4 volume combusted in m3
        ch4_vol_m3 = active_digesters * bs * w_ch4
        # Convert to tonnes CH4
        ch4_tonnes = ch4_vol_m3 * float(density_ch4_t_m3)
        # Apply net-to-gross UF_b and GWP
        md_tco2e = ch4_tonnes * float(gwp_ch4) * float(uf_b)
        total_md += md_tco2e

    return float(total_md)


@equation(
    tool="BM-AG04.001",
    version="1.0",
    eq="4",
    page=8,
    doc="Net emission reductions: ER_y = min( BE_y * n_k_y - PE_PL - PE_FC - PE_EC, MD_y - PE_FC - PE_EC - LE_y )",
)
def net_emission_reductions_manure(
    baseline_emissions_tco2e: float,
    operating_fraction: float,
    pe_leakage_tco2e: float,
    pe_fossil_fuel_tco2e: float = 0.0,
    pe_electricity_tco2e: float = 0.0,
    methane_combusted_tco2e: Optional[float] = None,
    leakage_tco2e: float = 0.0,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Calculate net emission reductions as the minimum of adjusted baseline potential and metered combustion."""
    be_adj = float(baseline_emissions_tco2e) * float(operating_fraction)
    pe_total = float(pe_leakage_tco2e) + float(pe_fossil_fuel_tco2e) + float(pe_electricity_tco2e)
    er_potential = max(be_adj - pe_total, 0.0)

    if methane_combusted_tco2e is not None:
        md = float(methane_combusted_tco2e)
        er_metered = max(md - float(pe_fossil_fuel_tco2e) - float(pe_electricity_tco2e) - float(leakage_tco2e), 0.0)
        return float(min(er_potential, er_metered))

    return float(er_potential)


__all__ = [
    "baseline_manure_emissions",
    "project_physical_leakage",
    "methane_combusted_digesters",
    "net_emission_reductions_manure",
]
