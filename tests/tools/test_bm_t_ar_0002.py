"""Golden tests for BM-T-AR-0002 (fire non-CO2 emissions)."""
import json
import pytest
from dmrv_core import CalculationContext
from methodologies.tools.bm_t_ar_0002 import (
    BMTAR0002Tool,
    forest_fire_living_tree_emissions,
    forest_fire_dom_emissions,
    site_prep_fire_emissions,
    harvest_biomass_default,
    harvest_residue_fire_emissions,
)


@pytest.fixture
def golden_cases():
    with open("reference/golden_cases.json", "r") as f:
        return json.load(f)


def test_ar0002_fire_components(golden_cases):
    case = golden_cases["AR0002_fire_components"]
    inp = case["inputs"]
    exp = case["expected"]

    # 1. Forest fire living tree emissions with tool GWP (SAR: CH4 21, N2O 310)
    ff_tree_sar = forest_fire_living_tree_emissions(
        a_burn_ha=inp["forest_fire"]["A_BURN_ha"],
        b_tree_tl=inp["forest_fire"]["b_TREE_tL"],
        comf=inp["forest_fire"]["COMF"],
        ef_ch4_g_kg=inp["forest_fire"]["EF_CH4"],
        ef_n2o_g_kg=inp["forest_fire"]["EF_N2O"],
        gwp_ch4=21.0,
        gwp_n2o=310.0,
    )
    assert pytest.approx(ff_tree_sar, rel=1e-9) == exp["GHG_FF_TREE_tool_GWP_tCO2e"]

    # 2. Forest fire living tree emissions with AR6 GWP (CH4 29.8, N2O 273)
    ff_tree_ar6 = forest_fire_living_tree_emissions(
        a_burn_ha=inp["forest_fire"]["A_BURN_ha"],
        b_tree_tl=inp["forest_fire"]["b_TREE_tL"],
        comf=inp["forest_fire"]["COMF"],
        ef_ch4_g_kg=inp["forest_fire"]["EF_CH4"],
        ef_n2o_g_kg=inp["forest_fire"]["EF_N2O"],
        gwp_ch4=29.8,
        gwp_n2o=273.0,
    )
    assert pytest.approx(ff_tree_ar6, rel=1e-9) == exp["GHG_FF_TREE_AR6_GWP_tCO2e"]

    # 3. Site preparation fire
    sp = inp["site_prep"]
    ghg_spf = site_prep_fire_emissions(
        a_spf_ha=sp["A_SPF"],
        b_tree=sp["b_TREE"],
        cc_shrub=sp["CC_SHRUB"],
        b_forest=sp["B_FOREST"],
        cf_tree=sp["CF_TREE"],
        cf_shrub=sp["CF_SHRUB"],
        bdr_sf=sp["BDR_SF"],
    )
    assert pytest.approx(ghg_spf, rel=1e-9) == exp["GHG_SPF_tCO2e"]

    # 4. Harvest residues
    hr = inp["harvest_residue"]
    b_harvest = harvest_biomass_default(b_forest=hr["B_FOREST"], a_fmf_ha=hr["A_FMF"], bef2=hr["BEF2"])
    assert pytest.approx(b_harvest, rel=1e-9) == exp["B_HARVEST_t_dm"]

    ghg_fmf = harvest_residue_fire_emissions(b_harvest_t_dm=b_harvest, f_bl=hr["f_BL"], cf_tree=hr["CF"])
    assert pytest.approx(ghg_fmf, rel=1e-9) == exp["GHG_FMF_tCO2e"]

    # 5. DOM forest fire
    dom = inp["dom"]
    ghg_dom = forest_fire_dom_emissions(
        a_burn_ha=dom["A_BURN"],
        c_dw_per_ha=dom["c_DW_per_ha"],
        c_li_per_ha=dom["c_LI_per_ha"],
    )
    assert pytest.approx(ghg_dom, rel=1e-9) == exp["GHG_FF_DOM_tCO2e"]

    # 6. Test via Tool compute method
    tool = BMTAR0002Tool()
    ctx = CalculationContext(project_id="test_ar2", scenario="project", errata_flags={"gwp_mode": "tool_as_printed"})
    res = tool.compute(ctx, inp)
    assert pytest.approx(res.outputs["GHG_FF_TREE_tCO2e"], rel=1e-9) == exp["GHG_FF_TREE_tool_GWP_tCO2e"]
    assert pytest.approx(res.outputs["GHG_SPF_tCO2e"], rel=1e-9) == exp["GHG_SPF_tCO2e"]
    assert pytest.approx(res.outputs["GHG_FMF_tCO2e"], rel=1e-9) == exp["GHG_FMF_tCO2e"]
    assert pytest.approx(res.outputs["GHG_FF_DOM_tCO2e"], rel=1e-9) == exp["GHG_FF_DOM_tCO2e"]


def test_ar0002_plugin_methods_and_applicability():
    from methodologies.tools.bm_t_ar_0002.errata import AR0002ErrataFlags
    tool = BMTAR0002Tool()
    ctx = CalculationContext(project_id="test_ar2_plug", scenario="project")

    # Applicability: < 5%
    app_low = tool.applicability(ctx, {"accumulated_burnt_area_ha": 2.0, "project_area_ha": 100.0})
    assert app_low[0].passed is False

    # Applicability: >= 5% and >= 0.05 ha
    app_high = tool.applicability(ctx, {"accumulated_burnt_area_ha": 10.0, "project_area_ha": 100.0})
    assert app_high[0].passed is True
    assert app_high[1].passed is True

    # Required parameters
    params = tool.required_parameters()
    assert any(p.symbol == "non_co2_to_co2_ratio" for p in params)

    # Errata flags
    err = AR0002ErrataFlags()
    assert err.gwp_mode == "project_locked"
    assert err.use_per_hectare_dom is True

