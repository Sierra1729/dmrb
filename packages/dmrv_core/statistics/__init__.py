"""Statistical utilities, Student-t quantiles, and uncertainty discounting."""
from __future__ import annotations

import math
from typing import Sequence, Tuple

import numpy as np
from scipy import stats


def t_two_sided(conf: float = 0.90, df: int = 1) -> float:
    """Two-sided Student t critical value.
    For conf=0.90, quantile is (1 + 0.90) / 2 = 0.95.
    """
    if df < 1:
        raise ValueError("Degrees of freedom must be >= 1")
    q = (1.0 + conf) / 2.0
    return float(stats.t.ppf(q, df))


def uncertainty_discount_fraction(u_pct: float) -> float:
    """BM-T-AR-0004 Appendix 2 Table 1.
    Returns discount as fraction of the half-width.
    """
    if u_pct <= 10.0:
        return 0.0
    if u_pct <= 15.0:
        return 0.25
    if u_pct <= 20.0:
        return 0.50
    if u_pct <= 30.0:
        return 0.75
    return 1.00


def apply_discount(mean: float, half_width: float, scenario: str) -> float:
    """Apply Appendix 2 uncertainty discount:
    Baseline moves UP (conservative, higher baseline requires more reduction),
    Project moves DOWN (conservative, lower credit issuance).
    """
    if mean == 0.0:
        return 0.0
    u = (half_width / abs(mean)) * 100.0
    d = uncertainty_discount_fraction(u) * half_width
    scen = scenario.lower()
    if scen in ("baseline", "bsl"):
        return mean + d
    elif scen in ("project", "proj", "actual"):
        return mean - d
    else:
        raise ValueError(f"Scenario must be 'baseline' or 'project', got '{scenario}'")


conservative = apply_discount


def sample_variance(values: Sequence[float]) -> float:
    """Compute unbiased sample variance (degrees of freedom n-1)."""
    n = len(values)
    if n < 2:
        return 0.0
    arr = np.asarray(values, dtype=float)
    return float(np.var(arr, ddof=1))


def regression_slope_and_corr(x: Sequence[float], y: Sequence[float]) -> Tuple[float, float]:
    """BM-T-AR-0004 Appendix 3 Eq. 1 and 2.
    Returns (beta, rho) where:
      beta = rho * s_y / s_x
      rho = Pearson correlation
    """
    x_arr = np.asarray(x, dtype=float)
    y_arr = np.asarray(y, dtype=float)
    if len(x_arr) != len(y_arr):
        raise ValueError("x and y series must have equal length")
    if len(x_arr) < 2:
        raise ValueError("Need at least 2 points for regression")

    x_mean = np.mean(x_arr)
    y_mean = np.mean(y_arr)

    x_diff = x_arr - x_mean
    y_diff = y_arr - y_mean

    sum_sq_x = np.sum(x_diff ** 2)
    sum_sq_y = np.sum(y_diff ** 2)

    if sum_sq_x == 0.0 or sum_sq_y == 0.0:
        return 0.0, 0.0

    rho = float(np.sum(x_diff * y_diff) / np.sqrt(sum_sq_x * sum_sq_y))
    s_x = np.sqrt(sum_sq_x / (len(x_arr) - 1))
    s_y = np.sqrt(sum_sq_y / (len(y_arr) - 1))
    beta = float(rho * (s_y / s_x))
    return beta, rho


def sample_size_box5(s2: float, moe: float, alpha: float = 0.10) -> int:
    """SOC Model Guidelines Box 5 sample size:
    n = z_{alpha/2}^2 * s^2 / MoE^2.
    """
    if moe <= 0.0:
        raise ValueError("Margin of error must be positive")
    z = float(stats.norm.ppf(1.0 - alpha / 2.0))
    n_exact = (z ** 2) * s2 / (moe ** 2)
    return int(math.ceil(n_exact))


__all__ = [
    "t_two_sided",
    "uncertainty_discount_fraction",
    "apply_discount",
    "conservative",
    "sample_variance",
    "regression_slope_and_corr",
    "sample_size_box5",
]
