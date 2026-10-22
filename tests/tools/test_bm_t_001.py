"""Unit tests for BM-T-001 Additionality and Baseline Identification."""
import pytest
from dmrv_core import CalculationContext
from methodologies.tools.bm_t_001 import (
    BMT001Tool,
    net_present_value,
    internal_rate_of_return,
    levelised_cost,
    sensitivity_analysis,
)


def test_t001_npv_and_irr():
    # Initial investment 100, annual returns of 30 for 5 years
    # Discount rate 10%
    cfs = [-100.0, 30.0, 30.0, 30.0, 30.0, 30.0]
    r = 0.10
    ctx = CalculationContext(project_id="test_npv", scenario="project")
    npv = net_present_value(cfs, r, ctx=ctx)
    assert pytest.approx(npv, 0.01) == 13.72

    # IRR
    irr = internal_rate_of_return(cfs, ctx=ctx)
    assert irr is not None
    assert pytest.approx(irr, 0.001) == 0.1524

    # NPV at IRR must be ~0
    npv_at_irr = net_present_value(cfs, irr)
    assert pytest.approx(npv_at_irr, 1e-4) == 0.0

    # No sign change -> IRR returns None
    assert internal_rate_of_return([10.0, 20.0, 30.0]) is None
    assert internal_rate_of_return([-10.0, -20.0, -30.0]) is None


def test_t001_levelised_cost():
    costs = [100.0, 10.0, 10.0, 10.0]
    outputs = [0.0, 50.0, 50.0, 50.0]
    r = 0.08
    lc = levelised_cost(costs, outputs, r)
    assert lc > 0.0

    with pytest.raises(ValueError, match="equal length"):
        levelised_cost([100.0], [50.0, 50.0], r)

    with pytest.raises(ZeroDivisionError):
        levelised_cost(costs, [0.0, 0.0, 0.0, 0.0], r)


def test_t001_sensitivity():
    cfs = [-100.0, 25.0, 25.0, 25.0, 25.0, 25.0]
    sens = sensitivity_analysis(cfs, [-0.10, 0.0, 0.10], discount_rate=0.10, benchmark_rate=0.10)
    assert len(sens) == 3
    # At +10% cash flows, NPV should increase
    assert sens[2]["npv"] > sens[0]["npv"]


def test_t001_workflow_demonstrating_additionality():
    tool = BMT001Tool()
    ctx = CalculationContext(project_id="test_add", scenario="project")

    inputs = {
        "regulations": [
            {"name": "Forest Conservation Act", "directly_or_indirectly_requires_activity": False}
        ],
        "lock_in_risk": {
            "operational_lifetime_years": 8,
            "inefficient_resource_use": False,
        },
        "alternatives": [
            {"id": "S1", "description": "A/R without CCTS", "compliant": True},
            {"id": "S2", "description": "Continuation of degraded pasture (BAU)", "compliant": True},
        ],
        "barriers": [
            {"alternative_id": "S1", "is_prevented": True, "type": "investment_barrier"}
        ],
        "financials": {
            "cash_flows": [-100.0, 15.0, 15.0, 15.0, 15.0, 15.0],
            "discount_rate": 0.12,
            "benchmark_rate": 0.15,
        },
        "common_practice": {
            "similar_activities_observed": False,
            "has_essential_distinctions": True,
        },
    }

    res = tool.compute(ctx, inputs)
    out = res.outputs
    assert out["is_additional"] is True
    assert out["selected_baseline_scenario"] == "S2"
    assert "DEMONSTRATED" in out["pdd_section_draft"]


def test_t001_workflow_failing_additionality():
    tool = BMT001Tool()
    ctx = CalculationContext(project_id="test_fail", scenario="project")

    # 1. Mandated by law without offset exception
    res_m1 = tool.compute(ctx, {
        "regulations": [
            {"name": "Mandatory Reforestation Order", "directly_or_indirectly_requires_activity": True, "has_offset_integration_exception": False}
        ]
    })
    assert res_m1.outputs["is_additional"] is False
    assert any("M1:" in r for r in res_m1.outputs["failure_reasons"])

    # 2. Profitable without carbon finance
    res_s3 = tool.compute(ctx, {
        "financials": {
            "cash_flows": [-100.0, 50.0, 50.0, 50.0],
            "discount_rate": 0.10,
            "benchmark_rate": 0.12,
        }
    })
    assert res_s3.outputs["is_additional"] is False
    assert any("S3:" in r for r in res_s3.outputs["failure_reasons"])
