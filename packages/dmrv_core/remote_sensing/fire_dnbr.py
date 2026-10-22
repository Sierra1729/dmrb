"""Sentinel-2 dNBR Burnt Area Pipeline & Reviewer Workflow."""
from __future__ import annotations

from dataclasses import dataclass, field
import datetime
from typing import Any, Dict, List, Literal, Optional, Sequence, cast
import numpy as np


@dataclass
class CandidateBurnEvent:
    event_id: str
    stratum_id: str
    pre_fire_date: datetime.date
    post_fire_date: datetime.date
    estimated_area_ha: float
    mean_dnbr: float
    burn_severity: Literal["UNBURNED", "LOW", "MODERATE", "HIGH"]
    status: Literal["PROPOSED", "CONFIRMED", "REJECTED"] = "PROPOSED"
    reviewer_id: Optional[str] = None
    confirmed_area_ha: Optional[float] = None
    reviewer_notes: Optional[str] = None


def compute_nbr(nir: np.ndarray, swir: np.ndarray) -> np.ndarray:
    """Compute Normalized Burn Ratio: NBR = (NIR - SWIR) / (NIR + SWIR)."""
    denom = nir + swir
    # Avoid zero division
    denom = np.where(denom == 0.0, 1e-6, denom)
    return cast(np.ndarray, (nir - swir) / denom)


def compute_dnbr(nbr_pre: np.ndarray, nbr_post: np.ndarray) -> np.ndarray:
    """Compute Differenced Normalized Burn Ratio: dNBR = NBR_pre - NBR_post."""
    return cast(np.ndarray, nbr_pre - nbr_post)


def classify_burn_severity(dnbr_val: float) -> Literal["UNBURNED", "LOW", "MODERATE", "HIGH"]:
    """Classify burn severity per USGS standard thresholds."""
    if dnbr_val < 0.10:
        return "UNBURNED"
    elif dnbr_val < 0.27:
        return "LOW"
    elif dnbr_val < 0.66:
        return "MODERATE"
    else:
        return "HIGH"


class BurntAreaPipeline:
    """Detects candidate burn scars and manages reviewer approval workflow."""

    @staticmethod
    def detect_candidate_burn_events(
        stratum_id: str,
        pre_fire_date: datetime.date,
        post_fire_date: datetime.date,
        nir_pre: Sequence[float],
        swir_pre: Sequence[float],
        nir_post: Sequence[float],
        swir_post: Sequence[float],
        pixel_area_m2: float = 100.0,  # 10 m x 10 m Sentinel-2 pixel
    ) -> Optional[CandidateBurnEvent]:
        """Process pixel arrays and propose candidate fire polygon if burn detected."""
        arr_nir_pre = np.asarray(nir_pre, dtype=float)
        arr_swir_pre = np.asarray(swir_pre, dtype=float)
        arr_nir_post = np.asarray(nir_post, dtype=float)
        arr_swir_post = np.asarray(swir_post, dtype=float)

        nbr_pre = compute_nbr(arr_nir_pre, arr_swir_pre)
        nbr_post = compute_nbr(arr_nir_post, arr_swir_post)
        dnbr = compute_dnbr(nbr_pre, nbr_post)

        # Burned pixels have dNBR >= 0.10
        burned_mask = dnbr >= 0.10
        n_burned_pixels = int(np.sum(burned_mask))
        if n_burned_pixels == 0:
            return None

        burned_dnbr_mean = float(np.mean(dnbr[burned_mask]))
        area_ha = (n_burned_pixels * pixel_area_m2) / 10000.0
        severity = classify_burn_severity(burned_dnbr_mean)

        event_id = f"BURN_{stratum_id}_{post_fire_date.strftime('%Y%m%d')}"
        return CandidateBurnEvent(
            event_id=event_id,
            stratum_id=stratum_id,
            pre_fire_date=pre_fire_date,
            post_fire_date=post_fire_date,
            estimated_area_ha=area_ha,
            mean_dnbr=burned_dnbr_mean,
            burn_severity=severity,
            status="PROPOSED",
        )

    @staticmethod
    def confirm_candidate_event(
        event: CandidateBurnEvent,
        reviewer_id: str,
        confirmed_area_ha: float,
        notes: str = "Verified against high-resolution imagery and ground report",
    ) -> CandidateBurnEvent:
        """Reviewer confirms candidate event with verified area."""
        event.status = "CONFIRMED"
        event.reviewer_id = reviewer_id
        event.confirmed_area_ha = float(confirmed_area_ha)
        event.reviewer_notes = notes
        return event

    @staticmethod
    def reject_candidate_event(
        event: CandidateBurnEvent,
        reviewer_id: str,
        notes: str = "False positive from seasonal defoliation",
    ) -> CandidateBurnEvent:
        """Reviewer rejects candidate event with justification."""
        event.status = "REJECTED"
        event.reviewer_id = reviewer_id
        event.reviewer_notes = notes
        return event


__all__ = [
    "CandidateBurnEvent",
    "BurntAreaPipeline",
    "compute_nbr",
    "compute_dnbr",
    "classify_burn_severity",
]
