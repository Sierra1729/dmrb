"""Tests for BM FR05.001 Mangrove A/R methodology."""
import pytest
from dmrv_core.equations import CalculationContext
from methodologies.plugins.fr05_001 import (
    BMFR05001Methodology,
    mangrove_soc_accumulation,
    mangrove_baseline_removals,
    mangrove_project_removals,
)


def test_fr05_001_equations():
    # Mangrove default SOC accumulation: 0.50 t C/ha/yr for 20 years, converted by 44/12
    # 100 ha cohort at age 5 -> 100 * 0.50 * 44/12 = 50 * 3.6666667 = 183.3333 tCO2e
    soc = mangrove_soc_accumulation([100.0], [5])
    assert pytest.approx(soc, 1e-4) == 50.0 * (44.0 / 12.0)

    # At age 25 (> 20), accumulation must be 0
    soc_old = mangrove_soc_accumulation([100.0], [25])
    assert soc_old == 0.0

    # Baseline & project removals (litter excluded)
    bsl = mangrove_baseline_removals(delta_c_tree_bsl=5.0, delta_c_shrub_bsl=1.0, delta_c_dw_bsl=0.5)
    assert bsl == 6.5

    proj = mangrove_project_removals(delta_c_tree_proj=80.0, delta_c_shrub_proj=5.0, delta_c_dw_proj=2.0, delta_soc_proj=soc)
    assert pytest.approx(proj, 1e-4) == 87.0 + soc


def test_fr05_001_plugin_applicability_and_ex_post():
    plugin = BMFR05001Methodology()
    ctx = CalculationContext(project_id="test_mangrove", scenario="project")

    # Applicability: pass
    app_pass = plugin.applicability(
        ctx,
        {
            "is_degraded_mangrove_habitat": True,
            "mangrove_species_percentage": 95.0,
            "soil_disturbance_fraction": 0.05,
        },
    )
    assert all(a.passed for a in app_pass)

    # Applicability: fail species percentage < 90%
    app_fail = plugin.applicability(
        ctx,
        {
            "is_degraded_mangrove_habitat": True,
            "mangrove_species_percentage": 85.0,
            "soil_disturbance_fraction": 0.05,
        },
    )
    assert not app_fail[1].passed

    # Ex-post run
    period_data = {
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
        "ar0004_project": {
            "method": "annual_change",
            "c_t1": 100.0,
            "c_t2": 300.0,
            "t_years": 1.0,
        },
        "ar0004_baseline": {
            "method": "annual_change",
            "c_t1": 0.0,
            "c_t2": 0.0,
            "t_years": 1.0,
        },
        "cohort_areas_ha": [50.0],
        "cohort_ages_years": [2],
    }
    project = {
        "selected_pools": ["tree_biomass", "soc"],
        "buffer_reserve_fraction": 0.10,
    }
    res = plugin.ex_post(ctx, project, period_data)
    assert res.total_net_credits > 0.0
    assert "delta_SOC_PROJ_tCO2e" in res.summary_outputs
    assert res.summary_outputs["has_reversal"] is False

    # Ex-ante mangrove projection
    ex_ante_res = plugin.ex_ante(ctx, project, {"projection_years": 10})
    assert len(ex_ante_res.annual_results) == 10
    assert ex_ante_res.total_net_credits == 80.0 * 10 * 0.90

    # With dead wood, fire, and leakage
    period_data_all = dict(period_data)
    period_data_all["ar0003_project"] = {
        "method": "default_factors",
        "C_TREE_i_tCO2e": 200.0,
        "DF_DW_pct": 2.0,
    }
    period_data_all["ar0002"] = {
        "accumulated_burnt_area_ha": 0.0,
        "project_area_ha": 50.0,
    }
    period_data_all["ar0005"] = {
        "zero_leakage_grazing_case": "a",
    }
    res_all = plugin.ex_post(ctx, project, period_data_all)
    assert res_all.total_net_credits > 0.0
