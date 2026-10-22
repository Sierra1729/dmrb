"""Plugin protocols and result data models for tools and methodologies."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Protocol, runtime_checkable

from dmrv_core.equations import CalculationContext


class DraftMethodologyIssuanceError(RuntimeError):
    """Raised when an issuance-grade calculation run attempts to use a draft methodology or tool."""
    pass


@dataclass
class ApplicabilityResult:
    criterion: str
    passed: bool
    evidence_summary: str = ""
    reason: str = ""


@dataclass
class ParameterSpec:
    symbol: str
    description: str
    unit: str
    required: bool = True
    default_value: Any = None


@dataclass
class ToolResult:
    tool_code: str
    version: str
    outputs: Dict[str, Any]
    uncertainty_pct: Optional[float] = None
    trace: List[Dict[str, Any]] = field(default_factory=list)
    errata_applied: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class AnnualResult:
    year: int
    baseline_emissions: float = 0.0
    baseline_removals: float = 0.0
    project_emissions: float = 0.0
    project_removals: float = 0.0
    leakage: float = 0.0
    net_reductions_or_removals: float = 0.0
    net_credits: float = 0.0
    vintages: Dict[int, float] = field(default_factory=dict)


@dataclass
class MethodologyResult:
    methodology_code: str
    version: str
    status: Literal["APPROVED", "DRAFT"] = "APPROVED"
    tool_results: Dict[str, ToolResult] = field(default_factory=dict)
    annual_results: List[AnnualResult] = field(default_factory=list)
    total_net_credits: float = 0.0
    vintage_totals: Dict[int, float] = field(default_factory=dict)
    tCCC: Optional[float] = None
    lCCC: Optional[float] = None
    reversal_detected: bool = False
    errata_applied: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    draft_notice: str = ""
    trace: List[Dict[str, Any]] = field(default_factory=list)
    summary_outputs: Dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class ToolPlugin(Protocol):
    code: str
    version: str
    status: Literal["APPROVED", "DRAFT"]

    def applicability(self, ctx: CalculationContext, inputs: Dict[str, Any]) -> List[ApplicabilityResult]:
        ...

    def required_parameters(self, options: Optional[Dict[str, Any]] = None) -> List[ParameterSpec]:
        ...

    def compute(self, ctx: CalculationContext, inputs: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> ToolResult:
        ...


@runtime_checkable
class MethodologyPlugin(Protocol):
    code: str
    version: str
    status: Literal["APPROVED", "DRAFT"]
    tools: Dict[str, str]

    def applicability(self, ctx: CalculationContext, project: Dict[str, Any]) -> List[ApplicabilityResult]:
        ...

    def ex_ante(self, ctx: CalculationContext, project: Dict[str, Any], scenario_inputs: Dict[str, Any]) -> MethodologyResult:
        ...

    def ex_post(self, ctx: CalculationContext, project: Dict[str, Any], period_data: Dict[str, Any]) -> MethodologyResult:
        ...


class PluginRegistry:
    """Central registry of discovered and loaded plugins."""
    _tools: Dict[str, ToolPlugin] = {}
    _methodologies: Dict[str, MethodologyPlugin] = {}

    @classmethod
    def register_tool(cls, plugin: ToolPlugin) -> None:
        cls._tools[plugin.code] = plugin

    @classmethod
    def register_methodology(cls, plugin: MethodologyPlugin) -> None:
        cls._methodologies[plugin.code] = plugin

    @classmethod
    def get_tool(cls, code: str) -> Optional[ToolPlugin]:
        return cls._tools.get(code)

    @classmethod
    def get_methodology(cls, code: str) -> Optional[MethodologyPlugin]:
        return cls._methodologies.get(code)

    @classmethod
    def list_tools(cls) -> Dict[str, str]:
        return {code: p.version for code, p in cls._tools.items()}

    @classmethod
    def list_methodologies(cls) -> Dict[str, str]:
        return {code: p.version for code, p in cls._methodologies.items()}


__all__ = [
    "DraftMethodologyIssuanceError",
    "ApplicabilityResult",
    "ParameterSpec",
    "ToolResult",
    "AnnualResult",
    "MethodologyResult",
    "ToolPlugin",
    "MethodologyPlugin",
    "PluginRegistry",
]
