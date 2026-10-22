"""Unit tests for pure Python dmrv_core package."""
import pytest
from pathlib import Path
from dmrv_core import (
    ureg,
    Q_,
    to_qty,
    strip_unit,
    CalculationContext,
    equation,
    ParameterCatalogue,
    ParameterResolver,
    MissingParameterError,
    UnapprovedParameterError,
    t_two_sided,
    uncertainty_discount_fraction,
    conservative,
    sample_variance,
    regression_slope_and_corr,
    fractional_years,
    allocate_to_calendar_vintages,
)


def test_units_and_quantities():
    q1 = to_qty(10.0, "ha")
    assert q1.magnitude == 10.0
    assert str(q1.units) == "hectare"

    # Convert ha to m2
    q1_m2 = q1.to("meter ** 2")
    assert q1_m2.magnitude == 100000.0

    # Carbon accounting units
    dm_val = to_qty(5.0, "t_dm")
    assert strip_unit(dm_val) == 5.0

    # to_qty with quantity and target unit
    q_converted = to_qty(q1, "meter ** 2")
    assert q_converted.magnitude == 100000.0

    # to_qty without unit on bare float raises ValueError
    with pytest.raises(ValueError, match="Unit string required"):
        to_qty(10.0)


def test_equation_decorator_and_trace():
    ctx = CalculationContext(project_id="test_proj", scenario="project")

    @equation(
        tool="BM-T-TEST",
        version="1.0",
        eq="1",
        page=5,
        doc="Test multiplication: c = a * b",
        errata_ids=["E-TEST-01"],
    )
    def test_calc(a: float, b: float, ctx: CalculationContext) -> float:
        return a * b

    res = test_calc(3.0, 4.0, ctx=ctx)
    assert res == 12.0
    assert len(ctx.nodes) == 1

    node = ctx.nodes[0]
    assert node.tool == "BM-T-TEST"
    assert node.eq == "1"
    assert node.inputs["a"] == 3.0
    assert node.inputs["b"] == 4.0
    assert node.outputs == 12.0
    assert "E-TEST-01" in ctx.active_errata_used

    trace_dict = ctx.get_trace_dict()
    assert len(trace_dict) == 1
    assert trace_dict[0]["eq"] == "1"


def test_parameter_catalogue_and_resolver():
    cat_path = Path("specs/14_parameter_catalogue.yaml")
    assert cat_path.exists()

    catalogue = ParameterCatalogue.load_from_file(cat_path)
    assert catalogue.version == "2026.10-01"
    assert catalogue.get_gwp("CH4", "AR6") == 29.8
    assert catalogue.get_gwp("N2O", "AR6") == 273.0
    assert catalogue.get_gwp("CH4", "SAR_as_printed") == 21.0

    resolver = ParameterResolver(catalogue)

    # 1. Resolve tool default
    cf = resolver.resolve("CF_TREE", "BM-T-AR-0004")
    assert cf.value == 0.47
    assert cf.source_type == "tool_default"
    assert cf.as_quantity().magnitude == 0.47

    # Bare dimensionless parameter
    bare = resolver.resolve("BEF2_ex_post", "BM-T-AR-0004")
    assert bare.as_quantity().magnitude == 1.15

    # 2. Resolve global default
    C_to_CO2 = resolver.resolve("C_to_CO2", "BM-T-AR-0004")
    assert pytest.approx(C_to_CO2.value, 1e-6) == 44.0 / 12.0

    # 3. Resolve project override (approved)
    overrides = {
        "CF_TREE": {
            "value": 0.48,
            "unit": "t C / t d.m.",
            "source_type": "project_specific_justified",
            "approved": True,
            "source_citation": "Laboratory measurement report",
        }
    }
    cf_custom = resolver.resolve("CF_TREE", "BM-T-AR-0004", project_overrides=overrides)
    assert cf_custom.value == 0.48
    assert cf_custom.source_type == "project_specific_justified"

    # 4. Reject unapproved override in issuance grade run
    overrides_unapproved = {
        "CF_TREE": {
            "value": 0.48,
            "source_type": "project_specific_justified",
            "approved": False,
        }
    }
    with pytest.raises(UnapprovedParameterError):
        resolver.resolve("CF_TREE", "BM-T-AR-0004", project_overrides=overrides_unapproved, is_issuance_grade=True)

    # 5. Missing parameter raises error
    with pytest.raises(MissingParameterError):
        resolver.resolve("NON_EXISTENT_PARAM", "BM-T-AR-0004")


def test_statistics_and_document_examples():
    # Appendix 2 discount example (PDF p.29): 60 +/- 9 (U = 15%)
    # U = 15% -> discount fraction = 0.25 -> d = 0.25 * 9 = 2.25
    # baseline = 60 + 2.25 = 62.25
    # project = 60 - 2.25 = 57.75
    assert uncertainty_discount_fraction(10.0) == 0.0
    assert uncertainty_discount_fraction(15.0) == 0.25
    assert uncertainty_discount_fraction(20.0) == 0.50
    assert uncertainty_discount_fraction(30.0) == 0.75
    assert uncertainty_discount_fraction(35.0) == 1.00

    assert conservative(60.0, 9.0, "baseline") == 62.25
    assert conservative(60.0, 9.0, "project") == 57.75

    # Student t value
    # df=33, 90% confidence two-sided -> 1.69236
    t_val = t_two_sided(0.90, 33)
    assert round(t_val, 3) == 1.692


def test_time_and_vintages():
    import datetime

    # String, date, datetime handling
    d_obj = datetime.date(2025, 1, 1)
    dt_obj = datetime.datetime(2025, 1, 1, 12, 0, 0)
    t_frac = fractional_years(d_obj, "2026-01-01")
    assert pytest.approx(t_frac, 0.01) == 1.0

    t_frac_dt = fractional_years(dt_obj, "2026-01-01", method="month_based")
    assert pytest.approx(t_frac_dt, 0.01) == 1.0

    with pytest.raises(ValueError, match="cannot be before start date"):
        fractional_years("2026-01-01", "2025-01-01")

    with pytest.raises(ValueError, match="Unknown fractional year method"):
        fractional_years("2025-01-01", "2026-01-01", method="invalid_method")

    with pytest.raises(ValueError, match="cannot be before start date"):
        allocate_to_calendar_vintages("2026-01-01", "2025-01-01", 100.0)

    alloc = allocate_to_calendar_vintages("2025-07-01", "2026-06-30", 100.0)
    assert 2025 in alloc and 2026 in alloc
    assert pytest.approx(alloc[2025] + alloc[2026], 1e-6) == 100.0

    # Single calendar year
    alloc_same = allocate_to_calendar_vintages("2025-01-01", "2025-12-31", 50.0)
    assert len(alloc_same) == 1
    assert pytest.approx(alloc_same[2025], 1e-6) == 50.0


def test_statistics_edge_cases():
    from dmrv_core.statistics import sample_size_box5

    # Sample variance with < 2 elements
    assert sample_variance([5.0]) == 0.0

    # Box 5 sample size
    assert sample_size_box5(s2=10.0, moe=2.0, alpha=0.10) > 0
    with pytest.raises(ValueError, match="Margin of error must be positive"):
        sample_size_box5(s2=10.0, moe=0.0)

    # Regression edge cases
    with pytest.raises(ValueError, match="equal length"):
        regression_slope_and_corr([1.0, 2.0], [1.0])
    with pytest.raises(ValueError, match="at least 2 points"):
        regression_slope_and_corr([1.0], [1.0])

    # Zero variance in x or y returns (0.0, 0.0)
    beta, rho = regression_slope_and_corr([5.0, 5.0, 5.0], [1.0, 2.0, 3.0])
    assert beta == 0.0 and rho == 0.0


def test_plugin_registry_and_quantities():
    from dmrv_core.plugin import PluginRegistry, ToolPlugin, ApplicabilityResult, ParameterSpec, ToolResult
    from dmrv_core.equations import set_current_context, get_current_context

    class DummyTool(ToolPlugin):
        code = "BM-T-DUMMY"
        version = "1.0"
        status = "APPROVED"

        def applicability(self, ctx, inputs):
            return [ApplicabilityResult("test", True, "evidence", "reason")]

        def required_parameters(self, options=None):
            return [ParameterSpec("P1", "dummy param", "dim")]

        def compute(self, ctx, inputs, options=None):
            return ToolResult(tool_code=self.code, version=self.version, outputs={"out": 1})

    tool = DummyTool()
    PluginRegistry.register_tool(tool)
    assert PluginRegistry.get_tool("BM-T-DUMMY") == tool
    assert "BM-T-DUMMY" in PluginRegistry.list_tools()

    # Context get / set
    ctx = CalculationContext()
    set_current_context(ctx)
    assert get_current_context() == ctx
    set_current_context(None)
    assert get_current_context() is None

    # Quantity passthrough
    q = to_qty(10.0, "ha")
    assert to_qty(q) == q
    assert strip_unit(123.4) == 123.4

