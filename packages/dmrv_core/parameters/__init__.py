"""Parameter catalogue loader, GWP registry, and priority resolver."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union, cast

import pint
import yaml

from dmrv_core.units import to_qty


class MissingParameterError(Exception):
    """Raised when a required parameter is missing from the catalogue and project data."""
    def __init__(self, symbol: str, tool: str, message: str = ""):
        super().__init__(message or f"Parameter '{symbol}' for tool '{tool}' is missing. No invented defaults permitted.")
        self.symbol = symbol
        self.tool = tool


class UnapprovedParameterError(Exception):
    """Raised when an unapproved non-default parameter is accessed in an issuance-grade run."""
    def __init__(self, symbol: str, source_type: str):
        super().__init__(f"Parameter '{symbol}' from non-default source '{source_type}' requires reviewer approval for issuance.")
        self.symbol = symbol
        self.source_type = source_type


@dataclass
class ResolvedParameter:
    symbol: str
    tool_code: str
    value: Any
    unit: str
    source_type: Literal["measured", "project_specific_justified", "national_default", "ipcc_default", "tool_default"]
    source_citation: str
    evidence_ids: List[str] = field(default_factory=list)
    approved: bool = True
    conservativeness_note: str = ""

    def as_quantity(self) -> pint.Quantity:
        if self.unit:
            u_str = (
                self.unit.replace("t d.m.", "t_dm")
                .replace("d.m.", "dm")
                .replace("t C", "t_C")
                .replace("t CO2e", "t_CO2e")
            )
            return to_qty(self.value, u_str)
        return to_qty(self.value, "dimensionless")


class ParameterCatalogue:
    """In-memory loaded representation of specs/14_parameter_catalogue.yaml."""

    def __init__(self, raw_data: Dict[str, Any]):
        self.version = raw_data.get("catalogue_version", "unknown")
        self.gwp_sets = raw_data.get("gwp_sets", {})
        self.default_gwp_set = raw_data.get("default_gwp_set", "AR6")
        self.global_params = raw_data.get("global", {})
        self.uncertainty_discount_table = raw_data.get("uncertainty_discount_table", [])
        self.raw_data = raw_data

    @classmethod
    def load_from_file(cls, path: Union[str, Path]) -> ParameterCatalogue:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls(data)

    def get_tool_params(self, tool_code: str) -> Dict[str, Any]:
        params = self.raw_data.get(tool_code, {})
        return dict(params) if isinstance(params, dict) else {}

    def get_gwp(self, gas: str, gwp_set_name: Optional[str] = None) -> float:
        set_name = gwp_set_name or self.default_gwp_set
        gwp_dict = self.gwp_sets.get(set_name, {})
        if gas not in gwp_dict:
            raise MissingParameterError(f"GWP_{gas}", "GLOBAL", f"GWP for {gas} not found in set {set_name}")
        return float(gwp_dict[gas])


class ParameterResolver:
    """Resolves parameters enforcing resolution order:
    measured > project_specific_justified (approved) > tool default (catalogue).
    """

    def __init__(self, catalogue: ParameterCatalogue):
        self.catalogue = catalogue

    def resolve(
        self,
        symbol: str,
        tool: str,
        scenario: str = "project",
        project_overrides: Optional[Dict[str, Any]] = None,
        is_issuance_grade: bool = True,
    ) -> ResolvedParameter:
        overrides = project_overrides or {}

        # 1. Check project-specific overrides (measured or justified)
        if symbol in overrides:
            item = overrides[symbol]
            if isinstance(item, dict):
                src_type = item.get("source_type", "project_specific_justified")
                approved = item.get("approved", False)
                if is_issuance_grade and not approved and src_type != "tool_default":
                    raise UnapprovedParameterError(symbol, src_type)
                return ResolvedParameter(
                    symbol=symbol,
                    tool_code=tool,
                    value=item["value"],
                    unit=item.get("unit", ""),
                    source_type=src_type,
                    source_citation=item.get("source_citation", "Project Record"),
                    evidence_ids=item.get("evidence_ids", []),
                    approved=approved,
                )
            else:
                # Bare value override
                return ResolvedParameter(
                    symbol=symbol,
                    tool_code=tool,
                    value=item,
                    unit="",
                    source_type="project_specific_justified",
                    source_citation="Project Override",
                    approved=True,
                )

        # 2. Check tool-specific defaults in catalogue
        tool_data = self.catalogue.get_tool_params(tool)
        if symbol in tool_data:
            entry = tool_data[symbol]
            if isinstance(entry, dict) and "value" in entry:
                return ResolvedParameter(
                    symbol=symbol,
                    tool_code=tool,
                    value=entry["value"],
                    unit=entry.get("unit", ""),
                    source_type="tool_default",
                    source_citation=entry.get("source", f"{tool} default"),
                    approved=True,
                )
            elif not isinstance(entry, dict):
                return ResolvedParameter(
                    symbol=symbol,
                    tool_code=tool,
                    value=entry,
                    unit="",
                    source_type="tool_default",
                    source_citation=f"{tool} default",
                    approved=True,
                )

        # 3. Check global parameters
        if symbol in self.catalogue.global_params:
            g_entry = self.catalogue.global_params[symbol]
            val = g_entry["value"] if isinstance(g_entry, dict) and "value" in g_entry else g_entry
            unit_str = g_entry.get("unit", "") if isinstance(g_entry, dict) else ""
            cit = g_entry.get("source", "Global catalogue default") if isinstance(g_entry, dict) else "Global default"
            return ResolvedParameter(
                symbol=symbol,
                tool_code="GLOBAL",
                value=val,
                unit=unit_str,
                source_type="tool_default",
                source_citation=cit,
                approved=True,
            )

        raise MissingParameterError(symbol, tool)


__all__ = [
    "MissingParameterError",
    "UnapprovedParameterError",
    "ResolvedParameter",
    "ParameterCatalogue",
    "ParameterResolver",
]
