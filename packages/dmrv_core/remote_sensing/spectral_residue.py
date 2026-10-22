"""Spectral Crop Residue Cover Index for Zero Tillage Compliance (>= 30%)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Sequence, cast
import numpy as np


@dataclass
class ResidueComplianceResult:
    field_id: str
    mean_ndti: float
    estimated_residue_cover_fraction: float
    is_compliant: bool
    status_summary: str


def compute_ndti(swir1: np.ndarray, swir2: np.ndarray) -> np.ndarray:
    """Compute Normalized Difference Tillage Index: NDTI = (SWIR1 - SWIR2) / (SWIR1 + SWIR2)."""
    denom = swir1 + swir2
    denom = np.where(denom == 0.0, 1e-6, denom)
    return cast(np.ndarray, (swir1 - swir2) / denom)


def evaluate_residue_cover_compliance(
    field_id: str,
    swir1_pixels: Sequence[float],
    swir2_pixels: Sequence[float],
    min_cover_threshold: float = 0.30,
) -> ResidueComplianceResult:
    """Evaluate whether crop residue cover meets or exceeds the 30% threshold."""
    s1 = np.asarray(swir1_pixels, dtype=float)
    s2 = np.asarray(swir2_pixels, dtype=float)

    ndti = compute_ndti(s1, s2)
    mean_ndti = float(np.mean(ndti))

    # Empirical calibration: residue cover fraction approx = min(max(mean_ndti * 2.5 + 0.10, 0.0), 1.0)
    cover_fraction = float(min(max(mean_ndti * 2.5 + 0.10, 0.0), 1.0))
    compliant = cover_fraction >= min_cover_threshold

    summary = (
        f"Field {field_id} estimated residue cover: {cover_fraction * 100:.1f}% "
        f"(Threshold: {min_cover_threshold * 100:.0f}%). "
        f"{'COMPLIANT' if compliant else 'NON-COMPLIANT: Residue cover below 30%'}"
    )

    return ResidueComplianceResult(
        field_id=field_id,
        mean_ndti=mean_ndti,
        estimated_residue_cover_fraction=cover_fraction,
        is_compliant=compliant,
        status_summary=summary,
    )


__all__ = ["compute_ndti", "evaluate_residue_cover_compliance", "ResidueComplianceResult"]
