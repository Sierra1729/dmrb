"""Golden tests for BM-T-AR-0003 (dead wood and litter)."""
import json
import pytest
from dmrv_core import CalculationContext
from methodologies.tools.bm_t_ar_0003 import (
    BMTAR0003Tool,
    standing_dead_biomass_allometric,
    standing_dead_carbon,
    stump_mid_diameter,
    stump_carbon,
    lying_dead_wood_carbon,
    stratum_dead_wood_carbon,
    litter_plot_carbon,
    dead_wood_default_factor,
    litter_default_factor,
)


@pytest.fixture
def golden_cases():
    with open("reference/golden_cases.json", "r") as f:
        return json.load(f)


def test_ar0003_deadwood_plot(golden_cases):
    case = golden_cases["AR0003_deadwood_plot"]
    inp = case["inputs"]
    exp = case["expected"]

    ctx = CalculationContext(project_id="test_dw", scenario="project")
    tool = BMTAR0003Tool()

    plot_inputs = dict(inp)
    plot_inputs["method"] = "plot_measurements"
    res = tool.compute(ctx, plot_inputs)
    out = res.outputs

    assert pytest.approx(out["C_DWL_tCO2e"], rel=1e-9) == exp["C_DWL_tCO2e"]
    assert pytest.approx(out["D_MID_STUMP_m"], rel=1e-9) == exp["D_MID_STUMP_m"]
    assert pytest.approx(out["C_DW_STUMP_tCO2e"], rel=1e-9) == exp["C_DW_STUMP_tCO2e"]
    assert pytest.approx(out["B_DW_TREE_t_dm"], rel=1e-9) == exp["B_DW_TREE_t_dm"]
    assert pytest.approx(out["C_DWS_TREE_tCO2e"], rel=1e-9) == exp["C_DWS_TREE_tCO2e"]


def test_ar0003_deadwood_stratum(golden_cases):
    case = golden_cases["AR0003_deadwood_stratum"]
    inp = case["inputs"]
    exp = case["expected"]

    c_dw_i = stratum_dead_wood_carbon(inp["A_i"], inp["A_plot_i"], inp["plot_total_tCO2e"])
    assert pytest.approx(c_dw_i, rel=1e-9) == exp["C_DW_i_tCO2e"]


def test_ar0003_litter_plot(golden_cases):
    case = golden_cases["AR0003_litter_plot"]
    inp = case["inputs"]
    exp = case["expected"]

    c_li_p = litter_plot_carbon(
        inp["B_LI_wet_kg"], inp["DWR"], inp["A_p_ha"], frame_area_m2=inp["a_p_m2"], cf_li=inp["CF_LI"]
    )
    assert pytest.approx(c_li_p, rel=1e-9) == exp["C_LI_plot_tCO2e"]


def test_ar0003_default_factors(golden_cases):
    case = golden_cases["AR0003_default_factors"]
    inp = case["inputs"]
    exp = case["expected"]

    c_tree = inp["C_TREE_i_tCO2e"]
    c_dw = dead_wood_default_factor(c_tree, exp["DF_DW_pct"])
    c_li = litter_default_factor(c_tree, exp["DF_LI_pct"])

    assert pytest.approx(c_dw, rel=1e-9) == exp["C_DW_i_tCO2e"]
    assert pytest.approx(c_li, rel=1e-9) == exp["C_LI_i_tCO2e"]


def test_ar0003_plugin_methods_and_applicability():
    from methodologies.tools.bm_t_ar_0003.errata import AR0003ErrataFlags
    tool = BMTAR0003Tool()
    ctx = CalculationContext(project_id="test_dw_plug", scenario="project")

    # Applicability
    app = tool.applicability(ctx, {"deadwood_in_situ": True})
    assert app[0].passed is True

    # Required parameters
    params = tool.required_parameters()
    assert any(p.symbol == "CF_TREE" for p in params)

    # Compute default factors (5% and 2% entered as 5.0 and 2.0)
    df_res = tool.compute(ctx, {"method": "default_factors", "C_TREE_i_tCO2e": 100.0, "DF_DW_pct": 5.0, "DF_LI_pct": 2.0})
    assert df_res.outputs["C_DW_i_tCO2e"] == 5.0
    assert df_res.outputs["C_LI_i_tCO2e"] == 2.0

    # Compute stratum deadwood
    sd_res = tool.compute(ctx, {"method": "stratum_deadwood", "A_i": 100.0, "A_plot_i": 2.0, "plot_total_tCO2e": 10.0})
    assert sd_res.outputs["C_DW_i_tCO2e"] == 500.0

    # Compute litter plot
    lp_res = tool.compute(ctx, {"method": "litter_plot", "B_LI_wet_kg": 2.0, "DWR": 0.5, "A_p_ha": 0.05, "a_p_m2": 0.5})
    assert lp_res.outputs["C_LI_plot_tCO2e"] > 0

    # Errata flags
    err = AR0003ErrataFlags()
    assert err.fix_ormerod_precedence is True
    assert err.divide_df_by_100 is True

