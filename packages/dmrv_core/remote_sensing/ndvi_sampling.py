"""Satellite NDVI Processing for Double Sampling (BM-T-AR-0004 Section 4.11)."""
from __future__ import annotations

from typing import Any, Dict, List, Sequence, cast
import numpy as np


def compute_ndvi(nir: np.ndarray, red: np.ndarray) -> np.ndarray:
    """Compute Normalized Difference Vegetation Index: NDVI = (NIR - Red) / (NIR + Red)."""
    denom = nir + red
    denom = np.where(denom == 0.0, 1e-6, denom)
    return cast(np.ndarray, (nir - red) / denom)


def extract_plot_and_population_ndvi(
    subsample_nir: Sequence[float],
    subsample_red: Sequence[float],
    population_nir: Sequence[float],
    population_red: Sequence[float],
) -> Dict[str, Any]:
    """Extract plot-level and population-level NDVI secondary variables for double sampling."""
    s_nir = np.asarray(subsample_nir, dtype=float)
    s_red = np.asarray(subsample_red, dtype=float)
    p_nir = np.asarray(population_nir, dtype=float)
    p_red = np.asarray(population_red, dtype=float)

    subsample_ndvi = compute_ndvi(s_nir, s_red)
    pop_ndvi = compute_ndvi(p_nir, p_red)

    return {
        "subsample_ndvi_x": subsample_ndvi.tolist(),
        "population_ndvi_mean_X": float(np.mean(pop_ndvi)),
        "subsample_ndvi_mean_x": float(np.mean(subsample_ndvi)),
        "n_subsample": len(subsample_ndvi),
        "n_population": len(pop_ndvi),
    }


__all__ = ["compute_ndvi", "extract_plot_and_population_ndvi"]
