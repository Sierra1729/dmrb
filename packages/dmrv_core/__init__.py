"""dmrv_core: Pure Python carbon accounting and dMRV calculation engine.

Zero external IO, strict unit typing via pint, immutable trace DAG.
"""
from dmrv_core.equations import (
    CalculationContext,
    TraceNode,
    equation,
    get_current_context,
    set_current_context,
)
from dmrv_core.parameters import (
    MissingParameterError,
    ParameterCatalogue,
    ParameterResolver,
    ResolvedParameter,
    UnapprovedParameterError,
)
from dmrv_core.plugin import (
    AnnualResult,
    ApplicabilityResult,
    MethodologyPlugin,
    MethodologyResult,
    ParameterSpec,
    PluginRegistry,
    ToolPlugin,
    ToolResult,
)
from dmrv_core.statistics import (
    apply_discount,
    conservative,
    regression_slope_and_corr,
    sample_size_box5,
    sample_variance,
    t_two_sided,
    uncertainty_discount_fraction,
)
from dmrv_core.time import allocate_to_calendar_vintages, fractional_years
from dmrv_core.units import Q_, Quantity, strip_unit, to_qty, ureg

__all__ = [
    "ureg",
    "Q_",
    "Quantity",
    "to_qty",
    "strip_unit",
    "CalculationContext",
    "TraceNode",
    "equation",
    "get_current_context",
    "set_current_context",
    "MissingParameterError",
    "UnapprovedParameterError",
    "ResolvedParameter",
    "ParameterCatalogue",
    "ParameterResolver",
    "t_two_sided",
    "uncertainty_discount_fraction",
    "apply_discount",
    "conservative",
    "sample_variance",
    "regression_slope_and_corr",
    "sample_size_box5",
    "fractional_years",
    "allocate_to_calendar_vintages",
    "ApplicabilityResult",
    "ParameterSpec",
    "ToolResult",
    "AnnualResult",
    "MethodologyResult",
    "ToolPlugin",
    "MethodologyPlugin",
    "PluginRegistry",
]
