"""BM-T-001 Financial and Investment Analysis Equations."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple
import numpy as np
from scipy.optimize import brentq

from dmrv_core.equations import CalculationContext, equation


@equation(
    tool="BM-T-001",
    version="1.0",
    eq="NPV",
    page=8,
    doc="Net Present Value: NPV(r) = sum_{n=0..N} CF_n / (1 + r)^n",
)
def net_present_value(
    cash_flows: Sequence[float],
    discount_rate: float,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Calculate Net Present Value given periodic cash flows and discount rate r."""
    r = float(discount_rate)
    npv = 0.0
    for n, cf in enumerate(cash_flows):
        npv += float(cf) / ((1.0 + r) ** n)
    return float(npv)


@equation(
    tool="BM-T-001",
    version="1.0",
    eq="IRR",
    page=8,
    doc="Internal Rate of Return: r such that NPV(r) = 0",
)
def internal_rate_of_return(
    cash_flows: Sequence[float],
    lower_bound: float = -0.99,
    upper_bound: float = 10.0,
    ctx: Optional[CalculationContext] = None,
) -> Optional[float]:
    """Calculate IRR using root finding (brentq). Returns None if no sign change exists."""
    cfs = [float(cf) for cf in cash_flows]
    if not cfs or all(c >= 0 for c in cfs) or all(c <= 0 for c in cfs):
        return None

    def f(rate: float) -> float:
        return float(net_present_value(cfs, rate))

    try:
        val_low = f(lower_bound)
        val_high = f(upper_bound)
        if val_low * val_high > 0:
            # Try a narrower standard bracket
            for r_test in [-0.5, 0.0, 0.1, 0.2, 0.5, 1.0, 2.0]:
                v = f(r_test)
                if val_low * v <= 0:
                    return float(brentq(f, lower_bound, r_test, maxiter=200))
                if v * val_high <= 0:
                    return float(brentq(f, r_test, upper_bound, maxiter=200))
            return None
        return float(brentq(f, lower_bound, upper_bound, maxiter=200))
    except (ValueError, RuntimeError):
        return None


@equation(
    tool="BM-T-001",
    version="1.0",
    eq="LCOx",
    page=8,
    doc="Levelised Cost: sum_n Cost_n / (1+r)^n / sum_n Output_n / (1+r)^n",
)
def levelised_cost(
    costs: Sequence[float],
    outputs: Sequence[float],
    discount_rate: float,
    ctx: Optional[CalculationContext] = None,
) -> float:
    """Calculate Levelised Cost of unit output (e.g. INR/kWh, INR/tCO2e)."""
    r = float(discount_rate)
    if len(costs) != len(outputs):
        raise ValueError("Costs and outputs sequences must have equal length")

    pv_costs = sum(float(c) / ((1.0 + r) ** n) for n, c in enumerate(costs))
    pv_outputs = sum(float(o) / ((1.0 + r) ** n) for n, o in enumerate(outputs))

    if pv_outputs == 0.0:
        raise ZeroDivisionError("Discounted output cannot be zero")

    return float(pv_costs / pv_outputs)


@equation(
    tool="BM-T-001",
    version="1.0",
    eq="SENSITIVITY",
    page=9,
    doc="Sensitivity analysis: evaluate financial indicator across variation range +/- delta",
)
def sensitivity_analysis(
    base_cash_flows: Sequence[float],
    param_variations: Sequence[float],
    discount_rate: float,
    benchmark_rate: Optional[float] = None,
    ctx: Optional[CalculationContext] = None,
) -> List[Dict[str, Any]]:
    """Evaluate NPV and IRR across percentage parameter variations (e.g. -0.10, 0.0, +0.10)."""
    results = []
    base_cfs = list(base_cash_flows)

    for pct in param_variations:
        # Scale non-initial cash flows by (1 + pct)
        varied_cfs = [base_cfs[0]] + [cf * (1.0 + pct) for cf in base_cfs[1:]]
        npv = net_present_value(varied_cfs, discount_rate, ctx=ctx)
        irr = internal_rate_of_return(varied_cfs, ctx=ctx)
        is_viable = False
        if benchmark_rate is not None and irr is not None:
            is_viable = irr >= benchmark_rate
        elif benchmark_rate is not None:
            is_viable = npv >= 0.0

        results.append({
            "variation_pct": float(pct),
            "npv": float(npv),
            "irr": float(irr) if irr is not None else None,
            "meets_benchmark": is_viable,
        })
    return results


__all__ = [
    "net_present_value",
    "internal_rate_of_return",
    "levelised_cost",
    "sensitivity_analysis",
]
