"""Tests for BM AG04.002 Rice Cultivation Methodology and Closed-Chamber Data Pipeline."""
from __future__ import annotations

import datetime
import math
import pytest

from dmrv_core.data.rice_chamber import (
    ChamberMeasurement,
    ChamberSamplePoint,
    PlotSamplingDay,
    ReferenceFieldSeason,
    compute_group_seasonal_emission_factor,
)
from dmrv_core.equations import CalculationContext
from methodologies.plugins.ag04_002 import (
    BMAG04002Plugin,
    baseline_ch4_emissions_season,
    net_emission_reductions_rice,
    organic_amendment_scaling_factor,
    project_ch4_emissions_season,
    project_n2o_emissions,
    tier1_emission_factor,
)


def test_rice_tier1_scaling_and_reductions() -> None:
    ctx = CalculationContext(project_id="test_rice")

    # Baseline continuously flooded: SF_w = 1.0, pre-season SF_p = 1.0, no amendment SF_o = 1.0
    # Continuous EF = 300 kg CH4/ha/season
    ef_bl = tier1_emission_factor(300.0, sf_w=1.0, sf_p=1.0, sf_o=1.0, ctx=ctx)
    assert pytest.approx(300.0) == ef_bl

    # Project AWD multiple aeration: SF_w = 0.55
    ef_pr = tier1_emission_factor(300.0, sf_w=0.55, sf_p=1.0, sf_o=1.0, ctx=ctx)
    assert pytest.approx(165.0) == ef_pr

    # 100 ha project
    be_y = baseline_ch4_emissions_season([ef_bl], [100.0], gwp_ch4=29.8, ctx=ctx)
    pe_y = project_ch4_emissions_season([ef_pr], [100.0], gwp_ch4=29.8, ctx=ctx)

    # 300 * 100 * 1e-3 * 29.8 = 894 t CO2e
    assert pytest.approx(894.0) == be_y
    # 165 * 100 * 1e-3 * 29.8 = 491.7 t CO2e
    assert pytest.approx(491.7) == pe_y

    # Net ER with 15% uncertainty deduction
    # (894.0 - 491.7) * (1 - 0.15) = 402.3 * 0.85 = 341.955 t CO2e
    net_er = net_emission_reductions_rice(be_y, pe_y, u_d=0.15, ctx=ctx)
    assert pytest.approx(341.955) == net_er


def test_rice_n2o_incremental_emissions_errata_resolution() -> None:
    # Errata E-AG2-01: AWD increases N2O from 0.003 to 0.005 kg N2O-N/kg N
    # 100 ha with 100 kg N/ha = 10,000 kg N
    # Delta EF = 0.005 - 0.003 = 0.002 kg N2O-N/kg N
    # Corrected stoichiometric conversion: 44/28
    # 10,000 * 0.002 * (44/28) * 1e-3 * 273.0 = 8.58 t CO2e
    ctx_corrected = CalculationContext(errata_flags={"use_corrected_pen_sign_and_n2o_conversion": True})
    pe_n_corr = project_n2o_emissions([100.0], [100.0], ctx=ctx_corrected)
    expected_corr = 10000.0 * 0.002 * (44.0 / 28.0) * 1e-3 * 273.0
    assert pytest.approx(expected_corr) == pe_n_corr
    assert pe_n_corr > 0.0

    # Uncorrected printed form would give negative emissions (-0.002 without 44/28)
    ctx_uncorrected = CalculationContext(errata_flags={"use_corrected_pen_sign_and_n2o_conversion": False})
    pe_n_uncorr = project_n2o_emissions([100.0], [100.0], ctx=ctx_uncorrected)
    assert pe_n_uncorr < 0.0


def test_organic_amendment_scaling_factor() -> None:
    # Straw application: ROA = 2 t/ha, CFOA = 0.5
    # SF_o = (1 + 2 * 0.5)^0.59 = 2^0.59 = 1.50525
    ctx = CalculationContext()
    sf_o = organic_amendment_scaling_factor([2.0], [0.5], ctx=ctx)
    assert pytest.approx(math.pow(2.0, 0.59)) == sf_o


def test_closed_chamber_measurement_pipeline() -> None:
    # 1. Test individual chamber measurement slope and flux
    # 3 samples over 30 min (0, 15, 30 min)
    # Concentration: 2.0 ppm -> 4.0 ppm -> 6.0 ppm (linear increase)
    chamber = ChamberMeasurement(
        chamber_id="CH_01",
        chamber_area_m2=0.25,
        chamber_height_m=0.5,
        temperature_c=25.0,
        pressure_atm=1.0,
        samples=[
            ChamberSamplePoint(0.0, 2.0),
            ChamberSamplePoint(15.0, 4.0),
            ChamberSamplePoint(30.0, 6.0),
        ],
    )
    res = chamber.compute_flux_mg_m2_hr()
    assert res["r2"] > 0.99
    assert res["flux_mg_m2_hr"] > 0.0

    # 2. Test plot with 3 chambers
    ch2 = ChamberMeasurement("CH_02", 0.25, 0.5, 25.0, 1.0, [
        ChamberSamplePoint(0.0, 2.0), ChamberSamplePoint(15.0, 4.1), ChamberSamplePoint(30.0, 6.2)
    ])
    ch3 = ChamberMeasurement("CH_03", 0.25, 0.5, 25.0, 1.0, [
        ChamberSamplePoint(0.0, 2.0), ChamberSamplePoint(15.0, 3.9), ChamberSamplePoint(30.0, 5.8)
    ])
    day1 = PlotSamplingDay(datetime.date(2026, 7, 1), [chamber, ch2, ch3])
    day2 = PlotSamplingDay(datetime.date(2026, 7, 15), [chamber, ch2, ch3])
    day3 = PlotSamplingDay(datetime.date(2026, 7, 30), [chamber, ch2, ch3])

    # 3. Test seasonal integration across 3 reference fields
    field1 = ReferenceFieldSeason("RF_01", [day1, day2, day3])
    field2 = ReferenceFieldSeason("RF_02", [day1, day2, day3])
    field3 = ReferenceFieldSeason("RF_03", [day1, day2, day3])

    group_ef = compute_group_seasonal_emission_factor([field1, field2, field3])
    assert group_ef["n_reference_fields"] == 3
    assert group_ef["mean_seasonal_ef_kg_ha"] > 0.0


def test_bmag04002_plugin_workflow() -> None:
    plugin = BMAG04002Plugin()
    ctx = CalculationContext(project_id="PRJ_RICE_001")

    # Applicability check
    app = plugin.applicability(ctx, {
        "water_source": "irrigated_canal",
        "training_and_technical_support_documented": True,
        "activity_type": "AWD",
    })
    assert all(a.passed for a in app)

    # Ex-ante run
    ex_ante_res = plugin.ex_ante(ctx, {}, {
        "years": [2026, 2027],
        "total_area_ha": 150.0,
        "ef_baseline_continuous_kg_ha": 280.0,
    })
    assert len(ex_ante_res.annual_results) == 2
    assert ex_ante_res.total_net_credits > 0.0

    # Ex-post run
    ex_post_res = plugin.ex_post(
        ctx,
        {},
        {
            "year": 2026,
            "ef_bl_kg_ha_season": [280.0],
            "ef_p_kg_ha_season": [154.0],
            "area_ha_by_group": [150.0],
            "nitrogen_applied_kg_ha": [120.0],
            "u_d": 0.15,
        },
    )
    assert len(ex_post_res.annual_results) == 1
    assert ex_post_res.total_net_credits > 0.0
