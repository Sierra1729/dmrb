"""Tests for Remote Sensing Connectors, dNBR Fire Pipeline, Canopy Cover, and Spectral Residue."""
from __future__ import annotations

import datetime
import pytest
import numpy as np

from dmrv_core.remote_sensing import (
    BurntAreaPipeline,
    CandidateBurnEvent,
    CanopyCoverResult,
    EarthEngineConnector,
    ResidueComplianceResult,
    STACClient,
    classify_burn_severity,
    compute_dnbr,
    compute_nbr,
    compute_ndti,
    compute_ndvi,
    evaluate_canopy_cover_no_decrease,
    evaluate_residue_cover_compliance,
    extract_plot_and_population_ndvi,
)


def test_stac_and_gee_connectors() -> None:
    stac = STACClient()
    items = stac.search_sentinel2(
        bbox=(77.0, 28.0, 77.5, 28.5),
        date_range=(datetime.date(2026, 1, 1), datetime.date(2026, 1, 15)),
    )
    assert len(items) == 1
    assert "B08" in items[0].assets
    assert items[0].collection == "sentinel-2-l2a"

    gee = EarthEngineConnector(project_id="ccts-dmrv-project")
    coll = gee.get_image_collection("COPERNICUS/S2_SR_HARMONIZED", (77.0, 28.0, 77.5, 28.5), "2026-01-01", "2026-01-15")
    assert coll["status"] == "ready"


def test_sentinel2_dnbr_fire_pipeline_and_reviewer_workflow() -> None:
    # Pre-fire: healthy vegetation (high NIR 0.50, low SWIR 0.10)
    # NBR_pre = (0.5 - 0.1) / (0.5 + 0.1) = 0.4 / 0.6 = 0.667
    nir_pre = [0.50] * 100
    swir_pre = [0.10] * 100

    # Post-fire: charred ground (low NIR 0.10, high SWIR 0.35)
    # NBR_post = (0.1 - 0.35) / (0.1 + 0.35) = -0.25 / 0.45 = -0.556
    # dNBR = 0.667 - (-0.556) = 1.222 (HIGH severity)
    nir_post = [0.10] * 100
    swir_post = [0.35] * 100

    pre_date = datetime.date(2026, 3, 1)
    post_date = datetime.date(2026, 3, 10)

    # 1. Detection proposes candidate event
    event = BurntAreaPipeline.detect_candidate_burn_events(
        stratum_id="STRAT_01",
        pre_fire_date=pre_date,
        post_fire_date=post_date,
        nir_pre=nir_pre,
        swir_pre=swir_pre,
        nir_post=nir_post,
        swir_post=swir_post,
        pixel_area_m2=100.0,
    )

    assert event is not None
    assert event.status == "PROPOSED"
    assert event.burn_severity == "HIGH"
    # 100 pixels * 100 m2 = 10,000 m2 = 1.0 ha
    assert pytest.approx(1.0) == event.estimated_area_ha

    # 2. Reviewer confirms candidate event
    confirmed_event = BurntAreaPipeline.confirm_candidate_event(
        event=event,
        reviewer_id="REV_ANALYST_04",
        confirmed_area_ha=0.95,
        notes="Confirmed with local DFO incident log",
    )
    assert confirmed_event.status == "CONFIRMED"
    assert confirmed_event.reviewer_id == "REV_ANALYST_04"
    assert confirmed_event.confirmed_area_ha == 0.95


def test_canopy_cover_no_decrease_evaluation() -> None:
    # Baseline: 12% crown cover
    pixel_bsl = [0.12] * 50

    # Monitoring period 1: Increased to 18% -> Verified no-decrease
    pixel_mon_gain = [0.18] * 50
    res_gain = evaluate_canopy_cover_no_decrease("S1", 2026, 2027, pixel_bsl, pixel_mon_gain)
    assert res_gain.no_decrease_verified is True
    assert "Verified no-decrease" in res_gain.status_summary

    # Monitoring period 2: Decreased to 6% -> Warning / Failed
    pixel_mon_loss = [0.06] * 50
    res_loss = evaluate_canopy_cover_no_decrease("S1", 2026, 2027, pixel_bsl, pixel_mon_loss)
    assert res_loss.no_decrease_verified is False
    assert "WARNING" in res_loss.status_summary


def test_ndvi_secondary_variable_extraction() -> None:
    # Subsample (3 plots)
    s_nir = [0.60, 0.55, 0.50]
    s_red = [0.10, 0.12, 0.15]
    # Population (10 pixels)
    p_nir = [0.55] * 10
    p_red = [0.12] * 10

    res = extract_plot_and_population_ndvi(s_nir, s_red, p_nir, p_red)
    assert len(res["subsample_ndvi_x"]) == 3
    assert res["n_population"] == 10
    assert res["population_ndvi_mean_X"] > 0.0


def test_spectral_residue_cover_compliance() -> None:
    # Compliant field: high SWIR1 relative to SWIR2 (high NDTI)
    swir1_high = [0.30] * 20
    swir2_low = [0.18] * 20
    res_comp = evaluate_residue_cover_compliance("F_01", swir1_high, swir2_low, min_cover_threshold=0.30)
    assert res_comp.is_compliant is True
    assert "COMPLIANT" in res_comp.status_summary

    # Non-compliant field: low residue cover (low NDTI)
    swir1_low = [0.18] * 20
    swir2_high = [0.22] * 20
    res_noncomp = evaluate_residue_cover_compliance("F_02", swir1_low, swir2_high, min_cover_threshold=0.30)
    assert res_noncomp.is_compliant is False
    assert "NON-COMPLIANT" in res_noncomp.status_summary
