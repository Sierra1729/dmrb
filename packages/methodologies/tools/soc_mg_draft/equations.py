"""DRAFT SOC Model Guidelines Equations."""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence
import numpy as np
from scipy import stats

from dmrv_core.equations import CalculationContext, equation
from dmrv_core.statistics import t_two_sided


@equation(
    tool="SOC-MG-DRAFT",
    version="1.0",
    eq="3b",
    page=14,
    doc="SOC stock: SOC_stock = SOC_con[%] * BD[g/cm3] * depth[cm] * (1 - CFR/100)",
    errata_ids=["E-SOCMG-02"],
)
def soc_stock_from_bulk_density(
    soc_pct: float,
    bulk_density_g_cm3: float,
    depth_cm: float,
    cfr_pct: float = 0.0,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Calculate unit-corrected SOC stock in t C/ha."""
    return float(float(soc_pct) * float(bulk_density_g_cm3) * float(depth_cm) * (1.0 - float(cfr_pct) / 100.0))


@equation(
    tool="SOC-MG-DRAFT",
    version="1.0",
    eq="6",
    page=26,
    doc="Sample size Box 5: n = ceil(z_{alpha/2}^2 * s^2 / MoE^2)",
)
def sample_size_box5(
    s_t_ha: float,
    moe_t_ha: float,
    alpha: float = 0.10,
    ctx: Optional[CalculationContext] = None,
) -> Dict[str, Any]:
    """Calculate required sample size for SOC validation per Box 5."""
    if moe_t_ha <= 0.0:
        raise ValueError("Margin of error must be strictly positive")
    z = float(stats.norm.ppf(1.0 - alpha / 2.0))
    n_raw = (z ** 2) * (s_t_ha ** 2) / (moe_t_ha ** 2)
    n_req = int(math.ceil(n_raw))
    return {
        "z_alpha/2": z,
        "n_raw": n_raw,
        "n_required": n_req,
    }


@equation(
    tool="SOC-MG-DRAFT",
    version="1.0",
    eq="12-25",
    page=33,
    doc="SOC Model validation metrics: Bias, RMSE, R2, SE, MoE_90, PICP",
    errata_ids=["E-SOCMG-03", "E-SOCMG-04"],
)
def soc_validation_metrics(
    observed: Sequence[float],
    predicted: Sequence[float],
    interval_halfwidth: float = 2.5,
    alpha: float = 0.10,
    ctx: Optional[CalculationContext] = None,
) -> Dict[str, Any]:
    """Calculate validation metrics per Table 3 Eq. 12-25."""
    obs = np.asarray(observed, dtype=float)
    pred = np.asarray(predicted, dtype=float)
    n = len(obs)
    if n != len(pred):
        raise ValueError("Observed and predicted series must have equal length")
    if n < 2:
        raise ValueError("Need at least 2 points to compute validation metrics")

    mean_obs = float(np.mean(obs))
    mean_pred = float(np.mean(pred))

    # Variance of observed s^2 (ddof=1)
    s2 = float(np.var(obs, ddof=1))
    s = float(math.sqrt(s2))

    # Residuals: r_i = predicted - observed (Eq.16)
    r = pred - obs
    bias = float(np.mean(r))  # or mean_pred - mean_obs

    # RMSE = sqrt( (1/n) * sum(r_i^2) ) (population form in Eq.18)
    rmse = float(math.sqrt(np.mean(r ** 2)))

    # R^2 = 1 - sum(pred - obs)^2 / sum(obs - mean_obs)^2
    ss_res = np.sum(r ** 2)
    ss_tot = np.sum((obs - mean_obs) ** 2)
    r2 = float(1.0 - (ss_res / ss_tot)) if ss_tot > 0 else 0.0

    # Standard Error of mean = s / sqrt(n)
    se = float(s / math.sqrt(n))

    # MoE_90 = SE * t_{0.95, n-1}
    t_val = t_two_sided(1.0 - alpha, n - 1)
    moe_90 = float(se * t_val)

    # PICP (Prediction Interval Coverage Probability)
    # Interval [pred_i - halfwidth, pred_i + halfwidth]
    covered = (obs >= (pred - interval_halfwidth)) & (obs <= (pred + interval_halfwidth))
    picp = float(np.mean(covered))

    # s_PICP sample standard deviation (ddof=1)
    # delta_i are boolean 0 or 1
    deltas = covered.astype(float)
    s_picp = float(np.std(deltas, ddof=1))

    # t_PICP = (PICP - 0.9) / (s_PICP / sqrt(n))
    se_picp = s_picp / math.sqrt(n)
    t_picp = float((picp - 0.90) / se_picp) if se_picp > 0 else 0.0

    # Pass criteria: |Bias| <= MoE; RMSE < s; R^2 > 0
    pass_bias = abs(bias) <= moe_90
    pass_rmse = rmse < s
    pass_r2 = r2 > 0.0

    return {
        "n": n,
        "mean_obs": mean_obs,
        "mean_pred": mean_pred,
        "s": s,
        "bias": bias,
        "rmse": rmse,
        "R2": r2,
        "SE": se,
        "MoE_90": moe_90,
        "PICP": picp,
        "s_PICP": s_picp,
        "t_PICP": t_picp,
        "pass_bias": pass_bias,
        "pass_rmse": pass_rmse,
        "pass_r2": pass_r2,
    }


@equation(
    tool="SOC-MG-DRAFT",
    version="1.0",
    eq="26-35",
    page=56,
    doc="Annex A DSM linear residual trend change: beta1, beta0, sigma2_resid, mu_delta, MoE_90",
)
def residual_trend_change(
    t_n: Sequence[float],
    e_n: Sequence[float],
    mu_pred_t: float,
    mu_pred_t_prime: float,
    t: float,
    t_prime: float,
    alpha: float = 0.10,
    ctx: Optional[CalculationContext] = None,
) -> Dict[str, float]:
    """Calculate residual trend change and uncertainty per Annex A Table A.6 Eq. 26-35."""
    t_arr = np.asarray(t_n, dtype=float)
    e_arr = np.asarray(e_n, dtype=float)
    n = len(t_arr)
    if n != len(e_arr) or n < 3:
        raise ValueError("Need at least 3 points for residual trend estimation")

    t_mean = float(np.mean(t_arr))
    e_mean = float(np.mean(e_arr))

    # Eq.31: beta1 = sum (t_n - t_bar)(e_n - e_bar) / sum (t_n - t_bar)^2
    ss_t = float(np.sum((t_arr - t_mean) ** 2))
    if ss_t <= 0:
        raise ValueError("Time variance must be positive")

    cov_te = float(np.sum((t_arr - t_mean) * (e_arr - e_mean)))
    beta1 = cov_te / ss_t

    # Eq.32: beta0 = e_bar - beta1 * t_bar
    beta0 = e_mean - beta1 * t_mean

    # Eq.33: sigma2_resid = 1/(N-2) * sum (e_n - (beta0 + beta1*t_n))^2
    fitted_e = beta0 + beta1 * t_arr
    resid = e_arr - fitted_e
    sigma2_resid = float(np.sum(resid ** 2) / (n - 2))

    # Eq.34: mu_delta = mu_pred(t') - mu_pred(t) + (t' - t) * beta1
    delta_t = float(t_prime - t)
    mu_delta = float((mu_pred_t_prime - mu_pred_t) + delta_t * beta1)

    # Eq.35: MoE = t_{0.95, N-2} * sqrt( (t' - t)^2 / sum(t_n - t_bar)^2 * sigma2_resid )
    t_crit = t_two_sided(1.0 - alpha, n - 2)
    var_term = ((delta_t ** 2) / ss_t) * sigma2_resid
    moe_90 = float(t_crit * math.sqrt(var_term))

    return {
        "beta1": beta1,
        "beta0": beta0,
        "sigma2_resid": sigma2_resid,
        "mu_delta": mu_delta,
        "MoE_90": moe_90,
    }


__all__ = [
    "soc_stock_from_bulk_density",
    "sample_size_box5",
    "soc_validation_metrics",
    "residual_trend_change",
]
