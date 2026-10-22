"""Golden tests for BM-T-AR-0006 (SOC stock change in A/R)."""
import json
import pytest
from dmrv_core import CalculationContext
from methodologies.tools.bm_t_ar_0006 import (
    BMTAR0006Tool,
    initial_soil_organic_carbon,
    soil_disturbance_loss,
    annual_soc_accumulation_rate,
    soc_rate_at_year,
    total_stratum_soc_change,
)


@pytest.fixture
def golden_cases():
    with open("reference/golden_cases.json", "r") as f:
        return json.load(f)


def test_ar0006_soc_tropical_moist_lac(golden_cases):
    case = golden_cases["AR0006_soc_tropical_moist_LAC"]
    inp = case["inputs"]
    exp = case["expected"]

    # 1. Direct equations
    soc_init = initial_soil_organic_carbon(inp["SOC_REF"], inp["f_LU"], inp["f_MG"], inp["f_IN"])
    assert pytest.approx(soc_init, rel=1e-9) == exp["SOC_INITIAL"]

    soc_loss = soil_disturbance_loss(soc_init, 0.15, threshold=0.10, loss_factor=0.10)
    assert pytest.approx(soc_loss, rel=1e-9) == exp["SOC_LOSS"]

    acc_rate = annual_soc_accumulation_rate(inp["SOC_REF"], soc_init, soc_loss, transition_years=20, max_rate_cap=0.80)
    assert pytest.approx(acc_rate, rel=1e-9) == 0.80

    rates_t1_to_t23 = [
        soc_rate_at_year(t, inp["t_PREP"], soc_loss, acc_rate, transition_years=20)
        for t in range(1, 24)
    ]
    for act_r, exp_r in zip(rates_t1_to_t23, exp["dSOC_by_year_t1_to_t23"], strict=True):
        assert pytest.approx(act_r, rel=1e-9) == exp_r

    delta_soc_al = [
        total_stratum_soc_change([inp["A_i_ha"]], [r])
        for r in rates_t1_to_t23
    ]
    for act_d, exp_d in zip(delta_soc_al, exp["delta_SOC_AL_tCO2e_by_year"], strict=True):
        assert pytest.approx(act_d, rel=1e-9) == exp_d

    # 2. Tool plugin compute
    tool = BMTAR0006Tool()
    ctx = CalculationContext(project_id="test_ar6", scenario="project")
    res = tool.compute(ctx, inp)
    out = res.outputs

    assert pytest.approx(out["SOC_INITIAL"], rel=1e-9) == exp["SOC_INITIAL"]
    assert pytest.approx(out["SOC_LOSS"], rel=1e-9) == exp["SOC_LOSS"]
    for act_r, exp_r in zip(out["dSOC_by_year_t1_to_t23"], exp["dSOC_by_year_t1_to_t23"], strict=True):
        assert pytest.approx(act_r, rel=1e-9) == exp_r
    for act_d, exp_d in zip(out["delta_SOC_AL_tCO2e_by_year"], exp["delta_SOC_AL_tCO2e_by_year"], strict=True):
        assert pytest.approx(act_d, rel=1e-9) == exp_d


def test_ar0006_plugin_methods_and_applicability():
    from methodologies.tools.bm_t_ar_0006.errata import AR0006ErrataFlags
    tool = BMTAR0006Tool()
    ctx = CalculationContext(project_id="test_ar6_plug", scenario="project")

    # Applicability: wetland or organic soil not allowed
    app_fail = tool.applicability(ctx, {"is_wetland": True, "is_organic_soil": False})
    assert app_fail[0].passed is False

    app_pass = tool.applicability(ctx, {"is_wetland": False, "is_organic_soil": False})
    assert app_pass[0].passed is True

    # Required parameters
    params = tool.required_parameters()
    assert any(p.symbol == "soc_loss_fraction" for p in params)

    # Errata flags
    err = AR0006ErrataFlags()
    assert err.require_all_eligibility_conditions is True
    assert err.zero_rate_after_transition is True

