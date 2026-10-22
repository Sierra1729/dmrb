"""Golden and property tests for BM-T-AR-0004 (trees and shrubs)."""
import json
import pytest
from pathlib import Path
from dmrv_core import CalculationContext
from methodologies.tools.bm_t_ar_0004 import (
    BMTAR0004Tool,
    root_shoot_ratio,
    uncertainty_difference_of_stocks,
    difference_of_stocks,
    annual_change,
    shrub_stratum_biomass,
    shrub_carbon_stock,
    proportionate_crown_cover_baseline_stock,
    proportionate_crown_cover_annual_change,
)


@pytest.fixture
def golden_cases():
    with open("reference/golden_cases.json", "r") as f:
        return json.load(f)


def test_ar0004_root_shoot(golden_cases):
    case = golden_cases["AR0004_root_shoot_function"]
    inputs = case["inputs"]["b_above_ground_t_dm_ha"]
    expected = case["expected"]["R"]

    for b, exp_r in zip(inputs, expected, strict=True):
        r = root_shoot_ratio(b)
        assert pytest.approx(r, rel=1e-9) == exp_r


def test_ar0004_stratified_sampling(golden_cases):
    case = golden_cases["AR0004_stratified_random_sampling"]
    raw_strata = case["inputs"]["strata"]
    strata_list = [
        {"name": k, "area_ha": v["area_ha"], "plot_biomass_list": v["plots_b"]}
        for k, v in raw_strata.items()
    ]

    tool = BMTAR0004Tool()
    ctx = CalculationContext(project_id="test_ar4", scenario="project")
    res = tool.compute(ctx, {"method": "stratified_sampling", "strata": strata_list})

    exp = case["expected"]
    out = res.outputs

    assert pytest.approx(out["b_TREE_t_dm_ha"], rel=1e-9) == exp["b_TREE_t_dm_ha"]
    assert out["t_val_df"] == exp["t_val_df"]
    assert pytest.approx(out["t_val"], rel=1e-9) == exp["t_val"]
    assert pytest.approx(out["u_C_fraction"], rel=1e-9) == exp["u_C_fraction"]
    assert pytest.approx(out["B_TREE_t_dm"], rel=1e-9) == exp["B_TREE_t_dm"]
    assert pytest.approx(out["C_TREE_tCO2e"], rel=1e-9) == exp["C_TREE_tCO2e"]
    assert pytest.approx(out["C_TREE_conservative_project_tCO2e"], rel=1e-9) == exp["C_TREE_conservative_project_tCO2e"]

    # Verify per-stratum outputs
    for s_name, s_exp in exp["per_stratum"].items():
        assert pytest.approx(out["per_stratum"][s_name]["mean"], rel=1e-9) == s_exp["mean"]
        assert pytest.approx(out["per_stratum"][s_name]["s2"], rel=1e-9) == s_exp["s2"]
        assert pytest.approx(out["per_stratum"][s_name]["w"], rel=1e-9) == s_exp["w"]


def test_ar0004_double_sampling(golden_cases):
    case = golden_cases["AR0004_double_sampling"]
    inp = case["inputs"]
    exp = case["expected"]

    tool = BMTAR0004Tool()
    ctx = CalculationContext(project_id="test_ar4_ds", scenario="project")
    res = tool.compute(
        ctx,
        {
            "method": "double_sampling",
            "sub_primary_biomass": inp["sub_sample_biomass"],
            "sub_secondary": inp["sub_sample_secondary"],
            "all_secondary": inp["all_plots_secondary"],
        },
    )
    out = res.outputs
    assert pytest.approx(out["rho"], rel=1e-9) == exp["rho"]
    assert pytest.approx(out["beta"], rel=1e-9) == exp["beta"]
    assert pytest.approx(out["alpha"], rel=1e-9) == exp["alpha"]
    assert pytest.approx(out["mean_secondary_all"], rel=1e-9) == exp["mean_secondary_all"]
    assert pytest.approx(out["mean_secondary_sub"], rel=1e-9) == exp["mean_secondary_sub"]
    assert pytest.approx(out["b_TREE_i"], rel=1e-9) == exp["b_TREE_i"]
    assert pytest.approx(out["s2_i"], rel=1e-9) == exp["s2_i"]


def test_ar0004_proportionate_crown_cover(golden_cases):
    case = golden_cases["AR0004_proportionate_crown_cover"]
    inp = case["inputs"]
    exp = case["expected"]

    total_c_stock = 0.0
    total_delta_c = 0.0
    ctx = CalculationContext(project_id="test_pcc", scenario="baseline")

    for s in inp["strata"]:
        c_s = proportionate_crown_cover_baseline_stock(
            inp["b_FOREST"], s["CC"], s["A"], cf_tree=inp["CF"], r_tree=inp["R_TREE"], ctx=ctx
        )
        d_s = proportionate_crown_cover_annual_change(
            inp["delta_b_FOREST_t_dm_ha_yr"], s["CC"], s["A"], cf_tree=inp["CF"], r_tree=inp["R_TREE"], ctx=ctx
        )
        total_c_stock += c_s
        total_delta_c += d_s

    assert pytest.approx(total_c_stock, rel=1e-9) == exp["C_TREE_BSL_tCO2e"]
    assert pytest.approx(total_delta_c, rel=1e-9) == exp["delta_C_TREE_BSL_tCO2e_per_yr"]


def test_ar0004_shrubs(golden_cases):
    case = golden_cases["AR0004_shrubs"]
    inp = case["inputs"]
    exp = case["expected"]

    ctx = CalculationContext(project_id="test_shrub", scenario="project")
    areas = [s["A"] for s in inp["strata"]]
    biomasses = [
        shrub_stratum_biomass(inp["b_FOREST"], s["CC"], bdr_sf=inp["BDR_SF"], shrub_cc_zero_below=0.05, ctx=ctx)
        for s in inp["strata"]
    ]
    # S2 has CC=0.04 < 0.05 -> biomass must be 0
    assert biomasses[1] == 0.0

    total_c = shrub_carbon_stock(areas, biomasses, cf_s=inp["CF_S"], r_s=inp["R_S"], ctx=ctx)
    assert pytest.approx(total_c, rel=1e-9) == exp["C_SHRUB_tCO2e"]


def test_ar0004_annual_change_and_difference(golden_cases):
    # Annual change with fractional T
    case_t = golden_cases["AR0004_annual_change_fractional_T"]
    d_c = annual_change(case_t["inputs"]["C_t1"], case_t["inputs"]["C_t2"], case_t["inputs"]["T_years"])
    assert pytest.approx(d_c, rel=1e-9) == case_t["expected"]["delta_C_per_year"]

    # Difference method uncertainty
    case_u = golden_cases["AR0004_difference_method_uncertainty"]
    inp_u = case_u["inputs"]
    delta = difference_of_stocks(inp_u["C_t2"], inp_u["C_t1"])
    u_diff = uncertainty_difference_of_stocks(inp_u["C_t1"], inp_u["u1"], inp_u["C_t2"], inp_u["u2"], delta)
    assert pytest.approx(delta, rel=1e-9) == case_u["expected"]["delta_C"]
    assert pytest.approx(u_diff, rel=1e-9) == case_u["expected"]["u_deltaC"]


def test_ar0004_plugin_methods_and_applicability():
    from methodologies.tools.bm_t_ar_0004.errata import AR0004ErrataFlags
    tool = BMTAR0004Tool()
    ctx = CalculationContext(project_id="test_plug", scenario="project")

    # Applicability
    app_pass = tool.applicability(ctx, {"cc_tree_bsl": 0.04})
    assert app_pass[0].passed is True
    app_fail = tool.applicability(ctx, {"cc_tree_bsl": 0.10})
    assert app_fail[0].passed is False

    # Required parameters
    params = tool.required_parameters()
    assert any(p.symbol == "CF_TREE" for p in params)

    # Compute: proportionate crown cover
    pcc_res = tool.compute(
        ctx,
        {
            "method": "proportionate_crown_cover",
            "b_forest": 100.0,
            "delta_b_forest": 5.0,
            "cc_tree_bsl": 0.05,
            "area_ha": 50.0,
        },
    )
    assert "C_TREE_BSL_tCO2e" in pcc_res.outputs

    # Compute: shrubs
    shrub_res = tool.compute(
        ctx,
        {
            "method": "shrubs",
            "strata_areas": [10.0, 20.0],
            "strata_cc_shrub": [0.15, 0.03],
            "b_forest": 80.0,
        },
    )
    assert "C_SHRUB_tCO2e" in shrub_res.outputs

    # Compute: annual_change
    ac_res = tool.compute(
        ctx,
        {
            "method": "annual_change",
            "c_t1": 100.0,
            "c_t2": 150.0,
            "t_years": 2.5,
        },
    )
    assert ac_res.outputs["delta_C_per_year"] == 20.0

    # Compute: difference_method
    diff_res = tool.compute(
        ctx,
        {
            "method": "difference_method",
            "c_t1": 100.0,
            "u1": 10.0,
            "c_t2": 150.0,
            "u2": 12.0,
        },
    )
    assert diff_res.outputs["delta_C"] == 50.0

    # Errata flags
    err = AR0004ErrataFlags()
    assert err.shrub_cc_zero_below == 0.05
    assert err.divide_by_ni_in_eq15 is True

