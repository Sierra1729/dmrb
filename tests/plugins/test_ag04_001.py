"""Tests for BM AG04.001 Methane Recovery from Livestock and Manure Management."""
from __future__ import annotations

import pytest

from dmrv_core.equations import CalculationContext
from methodologies.plugins.ag04_001 import (
    BMAG04001Plugin,
    baseline_manure_emissions,
    methane_combusted_digesters,
    net_emission_reductions_manure,
    project_physical_leakage,
)


def test_manure_equations() -> None:
    ctx = CalculationContext(project_id="test_manure")

    # 100 dairy cattle: mass 350 kg, VS rate 5.1, B0 0.24, MCF 20%, MS frac 1.0, UF_b 0.89
    # Annual VS = 350/1000 * 5.1 * 365 = 651.525 kg VS / animal / yr
    # Total CH4 m3 = 100 * 651.525 * 0.24 = 15636.6 m3
    # Tonnes CH4 = 15636.6 * 0.67 * 1e-3 = 10.476522 t CH4
    # Emitted with 20% MCF = 2.0953044 t CH4
    # In t CO2e = 2.0953044 * 29.8 * 0.89 = 55.5724 t CO2e
    be = baseline_manure_emissions(
        num_animals=[100.0],
        animal_mass_kg=[350.0],
        vs_rate_kg_per_1000kg_day=[5.1],
        b0_m3_kg_vs=[0.24],
        mcf_pct=[20.0],
        ms_fraction=[1.0],
        uf_b=0.89,
        gwp_ch4=29.8,
        ctx=ctx,
    )
    expected_be = 100.0 * (350.0 / 1000.0) * 5.1 * 365.0 * 0.24 * 0.67 * 1e-3 * 0.20 * 1.0 * 29.8 * 0.89
    assert pytest.approx(expected_be) == be

    # Physical leakage: 10% of unadjusted potential (without UF_b)
    # 10% * (expected_be / 0.89) = 6.244 t CO2e
    pe_pl = project_physical_leakage(
        num_animals_fed=[100.0],
        animal_mass_kg=[350.0],
        vs_rate_kg_per_1000kg_day=[5.1],
        b0_m3_kg_vs=[0.24],
        mcf_pct=[20.0],
        ms_fraction=[1.0],
        leakage_fraction=0.10,
        gwp_ch4=29.8,
        ctx=ctx,
    )
    assert pytest.approx(expected_be / 0.89 * 0.10) == pe_pl

    # Methane combusted: 25 operating digesters, 500 m3 biogas each, 60% CH4
    # Total CH4 = 25 * 500 * 0.60 = 7500 m3 CH4
    # Tonnes CH4 = 7500 * 0.67e-3 = 5.025 t CH4
    # In t CO2e = 5.025 * 29.8 * 0.89 = 133.274 t CO2e
    md = methane_combusted_digesters(
        n_commissioned=[25.0],
        operating_fraction=[1.0],
        biogas_combusted_m3_per_digester=[500.0],
        methane_fraction=[0.60],
        uf_b=0.89,
        ctx=ctx,
    )
    expected_md = 25.0 * 1.0 * 500.0 * 0.60 * 0.67e-3 * 29.8 * 0.89
    assert pytest.approx(expected_md) == md

    # Net ER: min(BE * operating_frac - PE, MD - PE)
    # BE * 0.90 - PE_pl = 55.5724 * 0.90 - 6.244 = 50.015 - 6.244 = 43.77 t CO2e
    # MD - PE_pl = 133.274 - 6.244 = 127.03 t CO2e
    # Min is 43.77 t CO2e
    net_er = net_emission_reductions_manure(
        baseline_emissions_tco2e=be,
        operating_fraction=0.90,
        pe_leakage_tco2e=pe_pl,
        methane_combusted_tco2e=md,
        ctx=ctx,
    )
    assert pytest.approx((be * 0.90) - pe_pl) == net_er


def test_bmag04001_plugin_workflow() -> None:
    plugin = BMAG04001Plugin()
    ctx = CalculationContext(project_id="PRJ_MANURE_001")

    # Applicability check
    app = plugin.applicability(ctx, {
        "project_scale": "small_farm_cooperative",
        "mean_annual_temperature_c": 26.5,
        "baseline_manure_system": "liquid_slurry_pit",
        "digestate_handled_aerobically": True,
    })
    assert all(a.passed for a in app)

    # Ineligible temperature <= 5 °C fails
    app_cold = plugin.applicability(ctx, {
        "project_scale": "small_farm",
        "mean_annual_temperature_c": 4.0,
        "baseline_manure_system": "liquid_slurry",
        "digestate_handled_aerobically": True,
    })
    assert any(not a.passed and "5 °C" in a.criterion for a in app_cold)

    # Ex-ante run
    ex_ante_res = plugin.ex_ante(ctx, {}, {
        "years": [2026, 2027],
        "num_animals": [80.0],
        "animal_mass_kg": [350.0],
        "operating_fraction": 0.95,
    })
    assert len(ex_ante_res.annual_results) == 2
    assert ex_ante_res.total_net_credits > 0.0

    # Ex-post run
    ex_post_res = plugin.ex_post(
        ctx,
        {},
        {
            "year": 2026,
            "num_animals": [80.0],
            "animal_mass_kg": [350.0],
            "operating_fraction": 0.95,
            "biogas_combusted_m3_per_digester": [450.0],
            "n_commissioned": [20.0],
            "digester_operating_fractions": [0.95],
        },
    )
    assert len(ex_post_res.annual_results) == 1
    assert ex_post_res.total_net_credits > 0.0
