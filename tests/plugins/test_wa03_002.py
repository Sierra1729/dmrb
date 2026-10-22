"""Tests for BM WA03.002 Landfill gas flaring or use."""
import pytest
from dmrv_core.equations import CalculationContext
from methodologies.plugins.wa03_002 import (
    BMWA03002Methodology,
    baseline_methane_emissions,
    total_methane_captured,
    ex_ante_methane_capture,
    emission_reductions,
)


def test_wa03_002_equations():
    f_pj = total_methane_captured(f_flared=100.0, f_electricity=50.0, f_heat=0.0, f_network=0.0)
    assert f_pj == 150.0

    be = baseline_methane_emissions(f_ch4_pj_y=150.0, f_ch4_bl_y=10.0, gwp_ch4=29.8, ox_top_layer=0.10)
    # net = (1 - 0.1)*150 - 10 = 135 - 10 = 125 t CH4
    # 125 * 29.8 = 3725.0
    assert pytest.approx(be, 1e-6) == 3725.0

    er = emission_reductions(baseline_emissions=3725.0, project_emissions=50.0, leakage_emissions=0.0)
    assert er == 3675.0

    ex_ante_f = ex_ante_methane_capture(be_ch4_swds_tco2e=5000.0, gwp_ch4=29.8, eta_pj=0.50)
    # 0.5 * 5000 / 29.8 = 83.8926...
    assert pytest.approx(ex_ante_f, 1e-4) == 2500.0 / 29.8


def test_wa03_002_plugin_ex_post_and_ex_ante():
    plugin = BMWA03002Methodology()
    ctx = CalculationContext(project_id="test_lfg", scenario="project")

    # Applicability
    app = plugin.applicability(ctx, {"is_existing_or_greenfield_swds": True, "deliberate_swds_change_to_raise_ch4": False})
    assert all(a.passed for a in app)

    # Ex-post metered run
    period_data = {
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
        "F_CH4_flared_t": 500.0,
        "F_CH4_electricity_t": 200.0,
        "PE_tCO2e": 120.0,
        "LE_tCO2e": 0.0,
    }
    project = {
        "gwp_ch4": 29.8,
        "ox_top_layer": 0.10,
        "baseline_case": 1,
    }
    res = plugin.ex_post(ctx, project, period_data)
    assert res.total_net_credits > 0.0
    assert "BE_CH4_tCO2e" in res.summary_outputs
    assert res.summary_outputs["F_CH4_PJ_tCH4"] == 700.0

    # Baseline case 2 (regulatory destruction requirement)
    proj_case2 = dict(project)
    proj_case2["baseline_case"] = 2
    proj_case2["regulatory_destruction_rate"] = 0.20
    res_c2 = plugin.ex_post(ctx, proj_case2, period_data)
    assert res_c2.summary_outputs["F_CH4_BL_tCH4"] == 0.20 * 700.0

    # Baseline case 3 (historic baseline)
    proj_case3 = dict(project)
    proj_case3["baseline_case"] = 3
    proj_case3["baseline_historic_flow_t"] = 100.0
    res_c3 = plugin.ex_post(ctx, proj_case3, period_data)
    assert res_c3.summary_outputs["F_CH4_BL_tCH4"] == 100.0

    # Ex-ante projection with BM-T-011 Application A
    scenario_inputs = {
        "bm_t_011_application_a": {
            "application": "A",
            "W_x_t_per_year": 50000.0,
            "composition": {"food": 0.50, "paper_cardboard": 0.20, "garden": 0.10, "wood": 0.05, "inert": 0.15},
            "DOC_k": {
                "food": [0.15, 0.40],
                "paper_cardboard": [0.40, 0.07],
                "garden": [0.20, 0.17],
                "wood": [0.43, 0.035],
                "inert": [0.0, 0.0],
            },
            "n_years": 5,
        }
    }
    ante_res = plugin.ex_ante(ctx, project, scenario_inputs)
    assert len(ante_res.annual_results) == 5
    assert ante_res.total_net_credits > 0.0


def test_synthetic_landfill_ex_ante_vs_measured_overlay(tmp_path):
    import csv
    from pathlib import Path
    from reports.workbook import CarbonAccountingWorkbook

    fixture_path = Path("tests/fixtures/synthetic_landfill/lfg_timeseries.csv")
    assert fixture_path.exists()

    # Parse metered flow and methane concentration
    # Density of CH4 at standard conditions: ~0.7168 kg/m3 (or 0.0007168 t/m3)
    density_ch4_t_m3 = 0.0007168
    total_ch4_mass_tonnes = 0.0

    with open(fixture_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            vol_m3 = float(row["flow_m3"])
            frac = float(row["ch4_vol_frac"])
            ch4_vol = vol_m3 * frac
            ch4_mass = ch4_vol * density_ch4_t_m3
            total_ch4_mass_tonnes += ch4_mass

    assert total_ch4_mass_tonnes > 1000.0  # ~2,280 t CH4

    # Run ex-post evaluation with metered flow
    plugin = BMWA03002Methodology()
    ctx = CalculationContext(project_id="PRJ-LANDFILL-01", scenario="project")
    project = {
        "gwp_ch4": 29.8,
        "ox_top_layer": 0.10,
        "baseline_case": 1,
    }
    period_data = {
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
        "F_CH4_flared_t": total_ch4_mass_tonnes,
        "PE_tCO2e": 50.0,
        "LE_tCO2e": 0.0,
    }
    ex_post_res = plugin.ex_post(ctx, project, period_data)

    # Ex-ante evaluation using BM-T-011 Application A
    scenario_inputs = {
        "bm_t_011_application_a": {
            "application": "A",
            "W_x_t_per_year": 60000.0,
            "composition": {"food": 0.55, "paper_cardboard": 0.15, "garden": 0.10, "wood": 0.05, "inert": 0.15},
            "DOC_k": {
                "food": [0.15, 0.40],
                "paper_cardboard": [0.40, 0.07],
                "garden": [0.20, 0.17],
                "wood": [0.43, 0.035],
                "inert": [0.0, 0.0],
            },
            "n_years": 1,
        }
    }
    ctx_ante = CalculationContext(project_id="PRJ-LANDFILL-01", scenario="baseline")
    ex_ante_res = plugin.ex_ante(ctx_ante, project, scenario_inputs)

    # Verify both produced valid emission reductions
    assert ex_post_res.total_net_credits > 0.0
    assert ex_ante_res.total_net_credits > 0.0

    # Generate XLSX report for the landfill project
    xlsx_path = tmp_path / "landfill_er_report.xlsx"
    wb_gen = CarbonAccountingWorkbook(ex_post_res, {"name": "Synthetic Landfill Gas Project", "project_id": "PRJ-LANDFILL-01"})
    wb_gen.generate(xlsx_path)
    assert xlsx_path.exists()

