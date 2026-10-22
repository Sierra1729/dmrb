"""Equation registry, lineage trace DAG, and calculation context."""
from __future__ import annotations

import functools
import inspect
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence

import pint


@dataclass
class TraceNode:
    """Represents an executed equation node in the calculation lineage DAG."""
    node_id: str
    tool: str
    version: str
    eq: str
    page: int
    doc: str
    inputs: Dict[str, Any]
    outputs: Any
    errata_applied: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert trace node to JSON-serializable dictionary."""
        def format_val(v: Any) -> Any:
            if isinstance(v, pint.Quantity):
                return {"value": float(v.magnitude), "unit": str(v.units)}
            if isinstance(v, (int, float, str, bool)):
                return v
            if isinstance(v, (list, tuple)):
                return [format_val(x) for x in v]
            if isinstance(v, dict):
                return {k: format_val(val) for k, val in v.items()}
            return str(v)

        return {
            "node_id": self.node_id,
            "tool": self.tool,
            "version": self.version,
            "eq": self.eq,
            "page": self.page,
            "doc": self.doc,
            "inputs": {k: format_val(v) for k, v in self.inputs.items()},
            "outputs": format_val(self.outputs),
            "errata_applied": self.errata_applied,
            "warnings": self.warnings,
        }


class CalculationContext:
    """Context object carrying execution state, lineage DAG, and config flags."""

    def __init__(
        self,
        project_id: str = "default_project",
        scenario: str = "project",  # "project" or "baseline"
        errata_flags: Optional[Dict[str, Any]] = None,
        gwp_mode: str = "project_locked",
        is_issuance_grade: bool = True,
    ) -> None:
        self.project_id = project_id
        self.scenario = scenario
        self.errata_flags = errata_flags or {}
        self.gwp_mode = gwp_mode
        self.is_issuance_grade = is_issuance_grade
        self.nodes: List[TraceNode] = []
        self.active_errata_used: set[str] = set()
        self.warnings: List[str] = list()

    def record_node(self, node: TraceNode) -> None:
        self.nodes.append(node)
        for err_id in node.errata_applied:
            self.active_errata_used.add(err_id)
        for w in node.warnings:
            self.warnings.append(w)

    def get_flag(self, flag_name: str, default: Any = None) -> Any:
        return self.errata_flags.get(flag_name, default)

    def get_trace_dict(self) -> List[Dict[str, Any]]:
        return [node.to_dict() for node in self.nodes]


_CURRENT_CONTEXT: Optional[CalculationContext] = None


def get_current_context() -> Optional[CalculationContext]:
    return _CURRENT_CONTEXT


def set_current_context(ctx: Optional[CalculationContext]) -> None:
    global _CURRENT_CONTEXT
    _CURRENT_CONTEXT = ctx


def equation(
    tool: str,
    version: str,
    eq: str,
    page: int,
    doc: str = "",
    errata_ids: Optional[Sequence[str]] = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for every calculation function mapping verbatim to methodology equations."""
    errata_list = list(errata_ids) if errata_ids else []

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        sig = inspect.signature(fn)

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            inputs_dict = dict(bound.arguments)

            # Check if ctx is passed in arguments or available globally
            ctx = inputs_dict.get("ctx") or get_current_context()

            # Execute the calculation
            result = fn(*args, **kwargs)

            # Record lineage trace
            if ctx is not None:
                # Filter out ctx from logged inputs
                filtered_inputs = {k: v for k, v in inputs_dict.items() if k != "ctx"}
                node = TraceNode(
                    node_id=str(uuid.uuid4()),
                    tool=tool,
                    version=version,
                    eq=eq,
                    page=page,
                    doc=doc or (fn.__doc__ or "").strip(),
                    inputs=filtered_inputs,
                    outputs=result,
                    errata_applied=errata_list,
                )
                ctx.record_node(node)

            return result

        wrapper._equation_meta = {  # type: ignore
            "tool": tool,
            "version": version,
            "eq": eq,
            "page": page,
            "doc": doc,
            "errata_ids": errata_list,
        }
        return wrapper

    return decorator


__all__ = [
    "TraceNode",
    "CalculationContext",
    "get_current_context",
    "set_current_context",
    "equation",
]
