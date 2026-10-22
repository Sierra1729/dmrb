"""Golden tests for BM-T-AR-0005 (agricultural displacement leakage)."""
import json
import pytest
from dmrv_core import CalculationContext
from methodologies.tools.bm_t_ar_0005 import (
    BMTAR0005Tool,
    displacement_biomass_loss,
    displacement_soc_loss,
    displacement_leakage_total,
)


@pytest.fixture
def golden_cases():
    with open("reference/golden_cases.json", "r") as f:
        return json.load(f)


def test_ar0005_leakage_displacement(golden_cases):
    case = golden_cases["AR0005_leakage_displacement"]
    inp = case["inputs"]
    exp = case["expected"]

    # 1. Direct equation checks
    delta_bio = displacement_biomass_loss(
        b_tree=inp["b_TREE"],
        b_shrub=inp["b_SHRUB"],
        a_disp_ha=inp["A_DISP"],
        cf=inp["CF"],
        r_tree=inp["R_TREE"],
        r_s=inp["R_S"],
    )
    assert pytest.approx(delta_bio, rel=1e-9) == exp["delta_C_BIOMASS_tC"]

    before = inp["before"]
    after = inp["after"]
    delta_soc = displacement_soc_loss(
        soc_ref=inp["SOC_REF"],
        f_lup=before[0],
        f_mgp=before[1],
        f_inp=before[2],
        f_lud=after[0],
        f_mgd=after[1],
        f_ind=after[2],
        a_disp_ha=inp["A_DISP"],
    )
    assert pytest.approx(delta_soc, rel=1e-9) == exp["delta_SOC_LUC_tC"]

    lk_total = displacement_leakage_total(delta_bio, delta_soc)
    assert pytest.approx(lk_total, rel=1e-9) == exp["LK_AGRIC_tCO2e"]

    # 2. Tool plugin compute check
    tool = BMTAR0005Tool()
    ctx = CalculationContext(project_id="test_ar5", scenario="project")
    res = tool.compute(ctx, inp)
    assert pytest.approx(res.outputs["delta_C_BIOMASS_tC"], rel=1e-9) == exp["delta_C_BIOMASS_tC"]
    assert pytest.approx(res.outputs["delta_SOC_LUC_tC"], rel=1e-9) == exp["delta_SOC_LUC_tC"]
    assert pytest.approx(res.outputs["LK_AGRIC_tCO2e"], rel=1e-9) == exp["LK_AGRIC_tCO2e"]


def test_ar0005_zero_leakage_grazing():
    tool = BMTAR0005Tool()
    ctx = CalculationContext(project_id="test_ar5_zero", scenario="project")
    res = tool.compute(ctx, {"zero_leakage_grazing_case": "a"})
    assert res.outputs["LK_AGRIC_tCO2e"] == 0.0


def test_ar0005_plugin_methods_and_applicability():
    from methodologies.tools.bm_t_ar_0005.errata import AR0005ErrataFlags
    tool = BMTAR0005Tool()
    ctx = CalculationContext(project_id="test_ar5_plug", scenario="project")

    # Applicability: wetland drainage blocks
    app_fail = tool.applicability(ctx, {"causes_wetland_or_peatland_drainage": True})
    assert app_fail[0].passed is False

    app_pass = tool.applicability(ctx, {"causes_wetland_or_peatland_drainage": False})
    assert app_pass[0].passed is True

    # Required parameters
    params = tool.required_parameters()
    assert any(p.symbol == "CF" for p in params)

    # Errata flags
    err = AR0005ErrataFlags()
    assert err.use_tC_units is True
    assert err.use_cleaned_defaults is True

