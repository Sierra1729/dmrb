"""Unit tests for BM FR05.002 Methodology Plugin."""
import pytest
from dmrv_core.equations import CalculationContext
from methodologies.plugins.fr05_002 import (
    BMFR05002Methodology,
    baseline_carbon_stock_change,
    project_carbon_stock_change,
    actual_net_removals,
    net_anthropogenic_removals,
    cumulative_temporary_credits,
    period_longterm_credits,
)


def test_fr05_002_equations():
    bsl = baseline_carbon_stock_change(10.0, 2.0, 1.0, 0.5)
    assert bsl == 13.5

    proj = project_carbon_stock_change(100.0, 5.0, 3.0, 1.0, 20.0)
    assert proj == 129.0

    actual = actual_net_removals(proj, 4.0)
    assert actual == 125.0

    net = net_anthropogenic_removals(actual, bsl, 2.0)
    assert net == 109.5

    cum = cumulative_temporary_credits([50.0, 100.0, 150.0])
    assert cum == 300.0

    period = period_longterm_credits([100.0, 150.0])
    assert period == 250.0


def test_fr05_002_plugin_applicability_and_ex_ante():
    plugin = BMFR05002Methodology()
    ctx = CalculationContext(project_id="test_fr_app", scenario="project")

    # Applicability: pass
    app_pass = plugin.applicability(ctx, {"is_wetland": False, "soil_disturbance_fraction": 0.05})
    assert all(a.passed for a in app_pass)

    # Applicability: fail wetland
    app_wet = plugin.applicability(ctx, {"is_wetland": True, "soil_disturbance_fraction": 0.05})
    assert not app_wet[0].passed

    # Applicability: fail disturbance > 10%
    app_dist = plugin.applicability(ctx, {"is_wetland": False, "soil_disturbance_fraction": 0.15})
    assert not app_dist[1].passed

    # Ex-ante projection
    ex_ante_res = plugin.ex_ante(
        ctx,
        {"start_year": 2026, "ex_ante_growth_tCO2e_per_yr": 200.0, "buffer_reserve_fraction": 0.10},
        {"projection_years": 10},
    )
    assert len(ex_ante_res.annual_results) == 10
    assert ex_ante_res.total_net_credits == 1800.0  # 10 yrs * 200 * 0.9


def test_fr05_002_reversal_detection():
    plugin = BMFR05002Methodology()
    ctx = CalculationContext(project_id="test_reversal", scenario="project")

    # Force a net negative removal (e.g. huge fire emissions or severe biomass loss)
    period_data = {
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
        "ar0004_project": {
            "method": "difference_method",
            "c_t1": 1000.0,
            "u1": 10.0,
            "c_t2": 200.0,  # 800 t loss
            "u2": 10.0,
        },
        "ar0004_baseline": {
            "method": "annual_change",
            "c_t1": 0.0,
            "c_t2": 0.0,
            "t_years": 1.0,
        },
        "ar0002": {
            "accumulated_burnt_area_ha": 0.0,
            "project_area_ha": 100.0,
        },
    }

    res = plugin.ex_post(ctx, {"selected_pools": ["tree_biomass"], "buffer_reserve_fraction": 0.10}, period_data)
    assert res.summary_outputs["has_reversal"] is True
    assert res.summary_outputs["reversal_amount_tCO2e"] > 0.0
    assert any("REVERSAL DETECTED" in w for w in res.warnings)
