"""Golden tests for BM-T-011 (emissions from solid waste disposal sites)."""
import json
import pytest
from dmrv_core import CalculationContext
from methodologies.tools.bm_t_011 import (
    BMT011Tool,
    model_uncertainty_vector,
    model_correction_factor_option2,
    mcf_water_table,
    doc_f_from_bmp_msw,
    yearly_fod_emissions,
)


@pytest.fixture
def golden_cases():
    with open("reference/golden_cases.json", "r") as f:
        return json.load(f)


def test_t011_phi_option2(golden_cases):
    case = golden_cases["T011_phi_option2"]
    inp = case["inputs"]
    exp = case["expected"]

    ctx = CalculationContext(project_id="test_phi", scenario="project")
    v_y = model_uncertainty_vector(inp["a"], inp["b"], inp["c"], inp["d"], inp["e"], inp["g"], ctx=ctx)
    phi_y = model_correction_factor_option2(v_y, ctx=ctx)

    assert pytest.approx(v_y, rel=1e-9) == exp["V_y"]
    assert pytest.approx(phi_y, rel=1e-9) == exp["phi_y"]


def test_t011_mcf_water_table(golden_cases):
    case = golden_cases["T011_MCF_water_table"]
    inp = case["inputs"]
    exp = case["expected"]

    ctx = CalculationContext(project_id="test_mcf", scenario="project")
    mcf = mcf_water_table(inp["d_y_m"], inp["h_w_y_m"], ctx=ctx)
    assert pytest.approx(mcf, rel=1e-9) == exp["MCF_y"]


def test_t011_docf_from_bmp(golden_cases):
    case = golden_cases["T011_DOCf_from_BMP"]
    inp = case["inputs"]
    exp = case["expected"]

    ctx = CalculationContext(project_id="test_docf", scenario="project")
    res = doc_f_from_bmp_msw(inp["BMP_MSW_tCH4_per_t"], inp["F"], inp["p_j"], ctx=ctx)
    assert pytest.approx(res["sum_p_DOC"], rel=1e-9) == exp["sum_p_DOC"]
    assert pytest.approx(res["DOC_f_y"], rel=1e-9) == exp["DOC_f_y"]


def test_t011_fod_application_b_msw_yearly(golden_cases):
    case = golden_cases["T011_FOD_applicationB_MSW_yearly"]
    inp = case["inputs"]
    exp = case["expected"]

    # 1. Test via Tool compute
    tool = BMT011Tool()
    ctx = CalculationContext(project_id="test_fod", scenario="baseline")
    res = tool.compute(ctx, inp)
    actual_series = res.outputs["BE_CH4_SWDS_tCO2e_y1_to_y10"]
    expected_series = exp["BE_CH4_SWDS_tCO2e_y1_to_y10"]

    assert len(actual_series) == len(expected_series)
    for act, expected in zip(actual_series, expected_series, strict=True):
        assert pytest.approx(act, rel=1e-9) == expected


def test_t011_plugin_methods_and_applicability():
    from methodologies.tools.bm_t_011.errata import T011ErrataFlags
    tool = BMT011Tool()
    ctx = CalculationContext(project_id="test_t11_plug", scenario="project")

    # Applicability: hazardous waste rejected
    app_haz = tool.applicability(ctx, {"is_hazardous_waste": True})
    assert app_haz[0].passed is False

    # Applicability: normal MSW passed
    app_msw = tool.applicability(ctx, {"is_hazardous_waste": False})
    assert app_msw[0].passed is True

    # Applicability: stockpile
    app_stockpile_fail = tool.applicability(ctx, {
        "is_hazardous_waste": False,
        "is_stockpile": True,
        "volume_to_surface_area_ratio": 1.2,  # < 1.5
        "anaerobic_conditions_confirmed": True,
    })
    assert app_stockpile_fail[1].passed is False

    # Required parameters
    params = tool.required_parameters()
    assert any(p.symbol == "OX" for p in params)

    # Monthly FOD model execution
    monthly_inp = {
        "timestep": "monthly",
        "phi": 0.85,
        "monthly_waste_streams": [{"food": 100.0, "wood": 20.0}] * 12,
        "doc_j": {"food": 0.15, "wood": 0.43},
        "k_j": {"food": 0.40, "wood": 0.035},
    }
    m_res = tool.compute(ctx, monthly_inp)
    assert len(m_res.outputs["emissions_by_month_tCO2e"]) == 12

    # Errata flags
    err = T011ErrataFlags()
    assert err.fix_phi_formula is True

    # Test default lookups (phi, MCF, DOC_f)
    default_inp = {
        "application": "A",
        "climate": "dry",
        "swds_type": "semi_aerobic_managed",
        "waste_streams": [{"food": 100.0}],
        "doc_j": {"food": 0.15},
        "k_j": {"food": 0.40},
    }
    def_res = tool.compute(ctx, default_inp)
    assert def_res.outputs["phi_y"] == 0.75
    assert def_res.outputs["MCF_y"] == 0.5
    assert def_res.outputs["DOC_f_y"] == 0.5

