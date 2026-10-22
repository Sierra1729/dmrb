"""Property-based tests using Hypothesis for invariant verification."""
import hypothesis.strategies as st
from hypothesis import given

from dmrv_core.statistics import conservative, uncertainty_discount_fraction
from methodologies.tools.bm_t_ar_0004 import (
    carbon_stock_from_biomass,
    root_shoot_ratio,
    total_biomass_from_mean,
)


@given(
    biomass=st.floats(min_value=0.0, max_value=1e6),
    cf=st.floats(min_value=0.40, max_value=0.60),
)
def test_monotonicity_biomass_to_carbon(biomass: float, cf: float):
    """Monotonicity: Higher biomass never yields lower carbon stock."""
    c1 = carbon_stock_from_biomass(biomass, cf_tree=cf)
    c2 = carbon_stock_from_biomass(biomass * 1.05, cf_tree=cf)
    assert c2 >= c1


@given(
    mean=st.floats(min_value=1.0, max_value=1000.0),
    half_width=st.floats(min_value=0.0, max_value=500.0),
)
def test_uncertainty_discount_properties(mean: float, half_width: float):
    """Conservativeness:
    Project quantity after discount is NEVER higher than original mean.
    Baseline quantity after discount is NEVER lower than original mean.
    """
    proj_disc = conservative(mean, half_width, scenario="project")
    bsl_disc = conservative(mean, half_width, scenario="baseline")

    assert proj_disc <= mean + 1e-9
    assert bsl_disc >= mean - 1e-9


@given(u_pct=st.floats(min_value=0.0, max_value=100.0))
def test_discount_fraction_stepwise(u_pct: float):
    """Discount fraction is monotonic non-decreasing with uncertainty percentage."""
    frac = uncertainty_discount_fraction(u_pct)
    assert 0.0 <= frac <= 1.0

    if u_pct <= 10.0:
        assert frac == 0.0
    elif u_pct <= 15.0:
        assert frac == 0.25
    elif u_pct <= 20.0:
        assert frac == 0.50
    elif u_pct <= 30.0:
        assert frac == 0.75
    else:
        assert frac == 1.00


@given(
    b1=st.floats(min_value=5.0, max_value=100.0),
    b2=st.floats(min_value=101.0, max_value=300.0),
)
def test_root_shoot_decreasing_with_biomass(b1: float, b2: float):
    """Cairns root-shoot power curve: root-to-shoot ratio decreases with higher AGB."""
    r1 = root_shoot_ratio(b1)
    r2 = root_shoot_ratio(b2)
    assert r1 > r2
