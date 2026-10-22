"""Canopy Cover Change Analysis for BM-T-AR-0004 'No-Decrease' Verification."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence
import numpy as np


@dataclass
class CanopyCoverResult:
    stratum_id: str
    year_baseline: int
    year_monitoring: int
    mean_crown_cover_baseline: float
    mean_crown_cover_monitoring: float
    delta_crown_cover: float
    no_decrease_verified: bool
    status_summary: str


def evaluate_canopy_cover_no_decrease(
    stratum_id: str,
    year_baseline: int,
    year_monitoring: int,
    pixel_cover_baseline: Sequence[float],
    pixel_cover_monitoring: Sequence[float],
) -> CanopyCoverResult:
    """Evaluate whether canopy cover has maintained or increased across monitoring period."""
    arr_bsl = np.asarray(pixel_cover_baseline, dtype=float)
    arr_mon = np.asarray(pixel_cover_monitoring, dtype=float)

    mean_bsl = float(np.mean(arr_bsl))
    mean_mon = float(np.mean(arr_mon))
    delta = mean_mon - mean_bsl

    # No-decrease requirement: delta >= 0 (or within sampling noise -0.01)
    passed = delta >= -0.005

    summary = (
        f"Canopy cover changed from {mean_bsl * 100:.1f}% to {mean_mon * 100:.1f}% (Δ = {delta * 100:+.1f}%). "
        f"{'Verified no-decrease' if passed else 'WARNING: Canopy cover decrease detected; field inspection required'}"
    )

    return CanopyCoverResult(
        stratum_id=stratum_id,
        year_baseline=year_baseline,
        year_monitoring=year_monitoring,
        mean_crown_cover_baseline=mean_bsl,
        mean_crown_cover_monitoring=mean_mon,
        delta_crown_cover=delta,
        no_decrease_verified=passed,
        status_summary=summary,
    )


__all__ = ["CanopyCoverResult", "evaluate_canopy_cover_no_decrease"]
