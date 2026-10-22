"""Tests for DRAFT SOC Model Guidelines and Activity Tools against Golden Cases."""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from dmrv_core.equations import CalculationContext
from dmrv_core.plugin import DraftMethodologyIssuanceError
from methodologies.tools.soc_mg_draft import (
    SOCModelGuidelinesTool,
    residual_trend_change,
    sample_size_box5,
    soc_stock_from_bulk_density,
    soc_validation_metrics,
)
from methodologies.tools.soc_at_draft import (
    SOCActivityTools,
    delta_fertilizer_emissions,
    fuel_and_electricity_increase,
    seed_production_and_transport,
    yield_leakage,
)


@pytest.fixture
def golden_cases() -> dict:
    golden_path = Path("reference/golden_cases.json")
    with open(golden_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_socmg_validation_metrics(golden_cases: dict) -> None:
    case = golden_cases["SOCMG_validation_metrics"]
    inputs = case["inputs"]
    expected = case["expected"]
    tol = case["rel_tol"]

    ctx = CalculationContext(project_id="test_soc", is_issuance_grade=False)
    metrics = soc_validation_metrics(
        observed=inputs["observed_t_ha"],
        predicted=inputs["predicted_t_ha"],
        interval_halfwidth=inputs["interval_halfwidth"],
        ctx=ctx,
    )

    assert metrics["n"] == expected["n"]
    assert pytest.approx(expected["mean_obs"], rel=tol) == metrics["mean_obs"]
    assert pytest.approx(expected["mean_pred"], rel=tol) == metrics["mean_pred"]
    assert pytest.approx(expected["s"], rel=tol) == metrics["s"]
    assert pytest.approx(expected["bias"], rel=tol) == metrics["bias"]
    assert pytest.approx(expected["rmse"], rel=tol) == metrics["rmse"]
    assert pytest.approx(expected["R2"], rel=tol) == metrics["R2"]
    assert pytest.approx(expected["SE"], rel=tol) == metrics["SE"]
    assert pytest.approx(expected["MoE_90"], rel=tol) == metrics["MoE_90"]
    assert pytest.approx(expected["PICP"], rel=tol) == metrics["PICP"]
    assert pytest.approx(expected["s_PICP"], rel=tol) == metrics["s_PICP"]
    assert pytest.approx(expected["t_PICP"], rel=tol) == metrics["t_PICP"]
    assert metrics["pass_bias"] is expected["pass_bias"]
    assert metrics["pass_rmse"] is expected["pass_rmse"]
    assert metrics["pass_r2"] is expected["pass_r2"]


def test_socmg_sample_size(golden_cases: dict) -> None:
    case = golden_cases["SOCMG_sample_size"]
    inputs = case["inputs"]
    expected = case["expected"]
    tol = case["rel_tol"]

    ctx = CalculationContext(project_id="test_soc", is_issuance_grade=False)
    res = sample_size_box5(
        s_t_ha=inputs["s_t_ha"],
        moe_t_ha=inputs["MoE_t_ha"],
        alpha=inputs["alpha"],
        ctx=ctx,
    )

    assert pytest.approx(expected["z_alpha/2"], rel=tol) == res["z_alpha/2"]
    assert pytest.approx(expected["n_raw"], rel=tol) == res["n_raw"]
    assert res["n_required"] == expected["n_required"]


def test_socmg_residual_trend_change(golden_cases: dict) -> None:
    case = golden_cases["SOCMG_residual_trend_change"]
    inputs = case["inputs"]
    expected = case["expected"]
    tol = case["rel_tol"]

    ctx = CalculationContext(project_id="test_soc", is_issuance_grade=False)
    res = residual_trend_change(
        t_n=inputs["t_n"],
        e_n=inputs["e_n"],
        mu_pred_t=inputs["mu_pred_t"],
        mu_pred_t_prime=inputs["mu_pred_t_prime"],
        t=inputs["t"],
        t_prime=inputs["t_prime"],
        ctx=ctx,
    )

    assert pytest.approx(expected["beta1"], rel=tol) == res["beta1"]
    assert pytest.approx(expected["beta0"], rel=tol) == res["beta0"]
    assert pytest.approx(expected["sigma2_resid"], rel=tol) == res["sigma2_resid"]
    assert pytest.approx(expected["mu_delta"], rel=tol) == res["mu_delta"]
    assert pytest.approx(expected["MoE_90"], rel=tol) == res["MoE_90"]


def test_socat_fertiliser_increase(golden_cases: dict) -> None:
    case = golden_cases["SOCAT_fertiliser_increase"]
    inputs = case["inputs"]
    expected = case["expected"]
    tol = case["rel_tol"]

    ctx = CalculationContext(project_id="test_soc", is_issuance_grade=False)
    res = delta_fertilizer_emissions(
        FE_PR_kgN_by_year=inputs["FE_PR_kgN_by_year"],
        FE_BL_kgN=inputs["FE_BL_kgN"],
        EF_FE_as_printed=inputs["EF_FE_as_printed"],
        ctx=ctx,
    )

    assert pytest.approx(expected["delta_FE_tCO2e_as_printed"], rel=tol) == res["delta_FE_tCO2e_as_printed"]
    assert pytest.approx(expected["EF_FE_IPCC_EF1_converted_tCO2e_per_kgN"], rel=tol) == res["EF_FE_IPCC_EF1_converted_tCO2e_per_kgN"]
    assert pytest.approx(expected["delta_FE_tCO2e_converted"], rel=tol) == res["delta_FE_tCO2e_converted"]


def test_socat_yield_leakage(golden_cases: dict) -> None:
    case = golden_cases["SOCAT_yield_leakage"]
    inputs = case["inputs"]
    expected = case["expected"]
    tol = case["rel_tol"]

    ctx = CalculationContext(project_id="test_soc", is_issuance_grade=False)
    res = yield_leakage(
        CY_BL=inputs["CY_BL"],
        CY_min_prev=inputs["CY_min_prev"],
        CY_t=inputs["CY_t"],
        A_bar=inputs["A_bar"],
        dBC_LA=inputs["dBC_LA"],
        dSOC_LA=inputs["dSOC_LA"],
        dFE_LA=inputs["dFE_LA"],
        dFU_LA=inputs["dFU_LA"],
        ctx=ctx,
    )

    assert pytest.approx(expected["LK_t0_tCO2e"], rel=tol) == res["LK_t0_tCO2e"]


def test_soc_stock_unit_correction() -> None:
    # Check: 1 % SOC, BD 1.3 g/cm3, 30 cm, CFR 0 -> 39 t C/ha
    stock = soc_stock_from_bulk_density(soc_pct=1.0, bulk_density_g_cm3=1.3, depth_cm=30.0, cfr_pct=0.0)
    assert pytest.approx(39.0) == stock


def test_draft_gating_raises_on_issuance() -> None:
    mg_tool = SOCModelGuidelinesTool()
    at_tool = SOCActivityTools()

    # Default CalculationContext is issuance-grade (is_issuance_grade=True)
    issuance_ctx = CalculationContext(project_id="issuance_run", is_issuance_grade=True)

    with pytest.raises(DraftMethodologyIssuanceError, match="DRAFT"):
        mg_tool.compute(issuance_ctx, {"s_t_ha": 12.0, "MoE_t_ha": 2.5})

    with pytest.raises(DraftMethodologyIssuanceError, match="DRAFT"):
        at_tool.compute(issuance_ctx, {"FE_PR_kgN_by_year": [1200.0], "FE_BL_kgN": 1100.0})


def test_draft_execution_stamps_disclaimer() -> None:
    mg_tool = SOCModelGuidelinesTool()
    at_tool = SOCActivityTools()

    draft_ctx = CalculationContext(project_id="draft_run", is_issuance_grade=False)

    mg_res = mg_tool.compute(draft_ctx, {"s_t_ha": 12.0, "MoE_t_ha": 2.5})
    assert mg_res.outputs["disclaimer"] == "DRAFT METHODOLOGY: NOT VALID FOR ISSUANCE"
    assert any("DRAFT METHODOLOGY" in w for w in mg_res.warnings)

    at_res = at_tool.compute(draft_ctx, {"FE_PR_kgN_by_year": [1200.0], "FE_BL_kgN": 1100.0})
    assert at_res.outputs["disclaimer"] == "DRAFT METHODOLOGY: NOT VALID FOR ISSUANCE"


def test_soc_applicability_and_undocumented_cap() -> None:
    at_tool = SOCActivityTools()
    ctx = CalculationContext(project_id="test_app", is_issuance_grade=False)

    # 1. Applicability checks
    # Histosol fails
    app_results = at_tool.applicability(ctx, {"soil_type": "histosol", "years_managed_prior": 5})
    assert any(not r.passed and "Histosol" in r.criterion for r in app_results)

    # Managed < 5 years fails
    app_results = at_tool.applicability(ctx, {"soil_type": "mineral", "years_managed_prior": 3})
    assert any(not r.passed and "5 years" in r.criterion for r in app_results)

    # Zero tillage with residue < 30% fails
    app_results = at_tool.applicability(ctx, {
        "activity_type": "zero_tillage",
        "soil_type": "mineral",
        "years_managed_prior": 6,
        "residue_cover_fraction": 0.20,
    })
    assert any(not r.passed and "Residue cover" in r.criterion for r in app_results)

    # 2. Undocumented baseline cap: BL_used = min(BL_doc, 0.5 * PR)
    # Project year is 2000 kg N. Baseline documented is 1800 kg N.
    # If documented: excess = 2000 - 1800 = 200 kg N.
    # If undocumented: baseline capped at 0.5 * 2000 = 1000 kg N -> excess = 2000 - 1000 = 1000 kg N.
    doc_res = delta_fertilizer_emissions(
        FE_PR_kgN_by_year=[2000.0],
        FE_BL_kgN=1800.0,
        has_baseline_records=True,
        ctx=ctx,
    )
    assert doc_res["total_excess_kgN"] == 200.0

    undoc_res = delta_fertilizer_emissions(
        FE_PR_kgN_by_year=[2000.0],
        FE_BL_kgN=1800.0,
        has_baseline_records=False,
        ctx=ctx,
    )
    assert undoc_res["total_excess_kgN"] == 1000.0


def test_soc_validation_report_generation(golden_cases: dict) -> None:
    from reports.soc_validation_report import SOCValidationReport

    case = golden_cases["SOCMG_validation_metrics"]
    inputs = case["inputs"]

    ctx = CalculationContext(project_id="PRJ_AG_001", is_issuance_grade=False)
    metrics = soc_validation_metrics(
        observed=inputs["observed_t_ha"],
        predicted=inputs["predicted_t_ha"],
        interval_halfwidth=inputs["interval_halfwidth"],
        ctx=ctx,
    )
    metrics["validation_data_source"] = "B"
    metrics["safety_discount"] = 0.10
    metrics["UNC_fraction"] = metrics["MoE_90"] / metrics["mean_obs"]
    metrics["total_uncertainty"] = metrics["UNC_fraction"] + 0.10

    report = SOCValidationReport(
        project_id="PRJ_AG_001",
        modelling_unit_id="MU_BLACK_SOIL_01",
        metrics=metrics,
        observed=inputs["observed_t_ha"],
        predicted=inputs["predicted_t_ha"],
        min_point_distance_m=45.2,
    )
    md = report.generate_markdown()
    assert "DRAFT METHODOLOGY: NOT VALID FOR ISSUANCE" in md
    assert "PRJ_AG_001" in md
    assert "MU_BLACK_SOIL_01" in md
    assert "Bias" in md
    assert "RMSE" in md
    assert "VALIDATED (APPROACH 2 ACCEPTED FOR MODELLING)" in md

