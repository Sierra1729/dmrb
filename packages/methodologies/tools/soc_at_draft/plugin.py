"""DRAFT SOC Activity Tools Plugin implementation."""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from dmrv_core.equations import CalculationContext
from dmrv_core.plugin import (
    ApplicabilityResult,
    DraftMethodologyIssuanceError,
    ParameterSpec,
    ToolPlugin,
    ToolResult,
)
from methodologies.tools.soc_at_draft import equations
from methodologies.tools.soc_at_draft.errata import SOCATErrataFlags
from methodologies.tools.soc_at_draft.params import SOCATParams


class SOCActivityTools(ToolPlugin):
    code: str = "SOC-AT-DRAFT"
    version: str = "1.0"
    status: Literal["APPROVED", "DRAFT"] = "DRAFT"

    def applicability(self, ctx: CalculationContext, inputs: Dict[str, Any]) -> List[ApplicabilityResult]:
        results: List[ApplicabilityResult] = []

        activity = str(inputs.get("activity_type", "cover_crops")).lower()

        # 1. Mineral soils only (Histosols excluded)
        soil_type = inputs.get("soil_type", "mineral").lower()
        is_mineral = "mineral" in soil_type and "histo" not in soil_type
        results.append(
            ApplicabilityResult(
                criterion="Mineral soils only (Histosols excluded)",
                passed=is_mineral,
                evidence_summary=f"Soil type: {soil_type}",
                reason="Eligible mineral soil" if is_mineral else "Histosols / organic soils excluded",
            )
        )

        # 2. Managed cropping system for >= 5 years before project start
        years_managed = inputs.get("years_managed_prior", 5)
        results.append(
            ApplicabilityResult(
                criterion="Managed cropping system >= 5 years prior to project start",
                passed=years_managed >= 5,
                evidence_summary=f"Prior management history: {years_managed} years",
                reason="Adequate prior management history" if years_managed >= 5 else "Insufficient history (< 5 years)",
            )
        )

        # 3. Activity-specific checks
        if "cover_crops" in activity:
            prior_cc_seasons = inputs.get("prior_cover_crop_seasons_in_5yr", 0)
            passed_cc = prior_cc_seasons <= 1
            results.append(
                ApplicabilityResult(
                    criterion="Farm used cover crops <= 1 season in 5 years prior to start",
                    passed=passed_cc,
                    evidence_summary=f"Prior cover crop seasons: {prior_cc_seasons}",
                    reason="Eligible cover cropping history" if passed_cc else "Exceeded prior cover crop threshold (> 1 season)",
                )
            )
        elif "improved_tillage" in activity or "zero_tillage" in activity:
            residue = inputs.get("residue_cover_fraction", 0.35)
            passed_res = residue >= 0.30
            results.append(
                ApplicabilityResult(
                    criterion="Residue cover >= 30% after planting / between harvest and sowing",
                    passed=passed_res,
                    evidence_summary=f"Residue cover: {residue * 100:.1f}%",
                    reason="Meets minimum 30% residue cover" if passed_res else "Residue cover below 30%",
                )
            )
            if "zero_tillage" in activity:
                tillage_within_2yr = inputs.get("tillage_event_within_2yr_prior", True)
                results.append(
                    ApplicabilityResult(
                        criterion="Tillage event occurred within 2 years prior to project start",
                        passed=tillage_within_2yr,
                        evidence_summary=f"Prior tillage event confirmed: {tillage_within_2yr}",
                        reason="Meets zero-tillage transition requirement" if tillage_within_2yr else "No tillage event within 2 years prior",
                    )
                )

        return results

    def required_parameters(self, options: Optional[Dict[str, Any]] = None) -> List[ParameterSpec]:
        return [
            ParameterSpec("EF_FE_as_printed", "Fertilizer emission factor as printed (IPCC EF1)", "t CO2e / kg N", default_value=0.01),
            ParameterSpec("EF_FE_converted", "Fertilizer emission factor converted (IPCC EF1 * GWP)", "t CO2e / kg N", default_value=0.00429),
            ParameterSpec("undocumented_baseline_cap_fraction", "Baseline cap fraction if unverified records", "dimensionless", default_value=0.50),
            ParameterSpec("min_residue_cover", "Minimum residue cover threshold", "dimensionless", default_value=0.30),
        ]

    def compute(
        self,
        ctx: CalculationContext,
        inputs: Dict[str, Any],
        params: Optional[Dict[str, Any]] = None,
    ) -> ToolResult:
        # Strict Draft Gating
        if ctx.is_issuance_grade:
            raise DraftMethodologyIssuanceError(
                f"Tool {self.code} is DRAFT: cannot be used for issuance-grade calculation runs. "
                "Output is stamped 'DRAFT METHODOLOGY: NOT VALID FOR ISSUANCE'."
            )

        p = params or {}
        outputs: Dict[str, Any] = {
            "disclaimer": "DRAFT METHODOLOGY: NOT VALID FOR ISSUANCE",
        }
        warnings: List[str] = [
            "DRAFT METHODOLOGY: Output calculated under draft activity tools, not valid for credit issuance."
        ]

        # 1. Fertilizer emissions increase
        if "FE_PR_kgN_by_year" in inputs and "FE_BL_kgN" in inputs:
            ef_printed = float(inputs.get("EF_FE_as_printed", p.get("EF_FE_as_printed", 0.01)))
            ef_converted = float(inputs.get("EF_FE_converted", p.get("EF_FE_converted", 0.00429)))
            has_records = bool(inputs.get("has_baseline_records", True))
            fe_res = equations.delta_fertilizer_emissions(
                FE_PR_kgN_by_year=inputs["FE_PR_kgN_by_year"],
                FE_BL_kgN=float(inputs["FE_BL_kgN"]),
                EF_FE_as_printed=ef_printed,
                EF_FE_converted=ef_converted,
                has_baseline_records=has_records,
                ctx=ctx,
            )
            outputs["delta_FE"] = fe_res

        # 2. Yield leakage
        if "CY_BL" in inputs and "CY_t" in inputs and "A_bar" in inputs:
            cy_min_prev = float(inputs.get("CY_min_prev", inputs["CY_BL"]))
            lk_res = equations.yield_leakage(
                CY_BL=float(inputs["CY_BL"]),
                CY_min_prev=cy_min_prev,
                CY_t=float(inputs["CY_t"]),
                A_bar=float(inputs["A_bar"]),
                dBC_LA=float(inputs.get("dBC_LA", 0.0)),
                dSOC_LA=float(inputs.get("dSOC_LA", 0.0)),
                dFE_LA=float(inputs.get("dFE_LA", 0.0)),
                dFU_LA=float(inputs.get("dFU_LA", 0.0)),
                ctx=ctx,
            )
            outputs["yield_leakage"] = lk_res

        # 3. Fuel and electricity
        if "FU_PR_by_year" in inputs and "FU_BL" in inputs:
            fu_res = equations.fuel_and_electricity_increase(
                FU_PR_by_year=inputs["FU_PR_by_year"],
                FU_BL=float(inputs["FU_BL"]),
                EU_PR_by_year=inputs.get("EU_PR_by_year", []),
                EU_BL=float(inputs.get("EU_BL", 0.0)),
                FEF=float(inputs.get("FEF", 1.0)),
                EEF=float(inputs.get("EEF", 1.0)),
                has_baseline_records=bool(inputs.get("has_baseline_records", True)),
                ctx=ctx,
            )
            outputs["fuel_electricity"] = fu_res

        # 4. Seed production and transport
        if "seed_rate_kg_ha" in inputs and "area_ha" in inputs:
            spt = equations.seed_production_and_transport(
                seed_rate_kg_ha=float(inputs["seed_rate_kg_ha"]),
                area_ha=float(inputs["area_ha"]),
                ef_seed_production=float(inputs.get("ef_seed_production", 0.0)),
                ef_seed_transport=float(inputs.get("ef_seed_transport", 0.0)),
                transport_distance_km=float(inputs.get("transport_distance_km", 0.0)),
                ctx=ctx,
            )
            outputs["seed_production_transport_tCO2e"] = spt

        return ToolResult(
            tool_code=self.code,
            version=self.version,
            outputs=outputs,
            trace=ctx.get_trace_dict(),
            errata_applied=list(ctx.active_errata_used),
            warnings=warnings,
        )


__all__ = ["SOCActivityTools"]
