"""DRAFT SOC Model Guidelines Tool Plugin implementation."""
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
from methodologies.tools.soc_mg_draft import equations
from methodologies.tools.soc_mg_draft.errata import SOCMGErrataFlags
from methodologies.tools.soc_mg_draft.params import SOCMGParams


class SOCModelGuidelinesTool(ToolPlugin):
    code: str = "SOC-MG-DRAFT"
    version: str = "1.0"
    status: Literal["APPROVED", "DRAFT"] = "DRAFT"

    def applicability(self, ctx: CalculationContext, inputs: Dict[str, Any]) -> List[ApplicabilityResult]:
        results: List[ApplicabilityResult] = []

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

        # 2. Managed cropping system for >= 5 years before start
        years_managed = inputs.get("years_managed_prior", 5)
        results.append(
            ApplicabilityResult(
                criterion="Managed cropping system >= 5 years prior to project start",
                passed=years_managed >= 5,
                evidence_summary=f"Prior management history: {years_managed} years",
                reason="Adequate prior management history" if years_managed >= 5 else "Insufficient history (< 5 years)",
            )
        )

        # 3. Minimum distance between calibration and validation points >= 30 m
        min_dist = inputs.get("min_cal_val_distance_m")
        if min_dist is not None:
            results.append(
                ApplicabilityResult(
                    criterion="Minimum spatial separation >= 30 m between calibration and validation points",
                    passed=min_dist >= 30.0,
                    evidence_summary=f"Minimum separation: {min_dist:.1f} m",
                    reason="Sufficient spatial independence" if min_dist >= 30.0 else "Points closer than 30 m",
                )
            )

        # 4. Process gate: validation sample date after prediction submission date
        pred_date = inputs.get("prediction_submission_date")
        val_sample_date = inputs.get("validation_sample_date")
        if pred_date and val_sample_date:
            passed = val_sample_date >= pred_date
            results.append(
                ApplicabilityResult(
                    criterion="Official validation samples taken strictly after model predictions submitted",
                    passed=passed,
                    evidence_summary=f"Predictions submitted: {pred_date}, Samples collected: {val_sample_date}",
                    reason="Temporal sequence valid" if passed else "Validation samples collected before prediction submission",
                )
            )

        return results

    def required_parameters(self, options: Optional[Dict[str, Any]] = None) -> List[ParameterSpec]:
        return [
            ParameterSpec("alpha", "Significance level (default 0.10 for 90% confidence)", "dimensionless", default_value=0.10),
            ParameterSpec("validation_data_source", "Validation source category (A, B, C, D)", "dimensionless", default_value="A"),
            ParameterSpec("interval_halfwidth", "Model prediction interval half-width in t C/ha", "t C / ha", default_value=2.5),
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
            "DRAFT METHODOLOGY: Output calculated under draft guidelines, not valid for credit issuance."
        ]

        # 1. Validation metrics calculation
        if "observed_t_ha" in inputs and "predicted_t_ha" in inputs:
            halfwidth = float(inputs.get("interval_halfwidth", p.get("interval_halfwidth", 2.5)))
            alpha = float(p.get("alpha", 0.10))
            metrics = equations.soc_validation_metrics(
                observed=inputs["observed_t_ha"],
                predicted=inputs["predicted_t_ha"],
                interval_halfwidth=halfwidth,
                alpha=alpha,
                ctx=ctx,
            )
            # Add safety discount based on validation data source
            source_cat = str(p.get("validation_data_source", "A")).upper()
            safety_discount = SOCMGParams().safety_discounts.get(source_cat, 0.0)
            unc_fraction = metrics["MoE_90"] / metrics["mean_obs"] if metrics["mean_obs"] > 0 else 0.0
            total_unc = unc_fraction + safety_discount

            metrics["validation_data_source"] = source_cat
            metrics["safety_discount"] = safety_discount
            metrics["UNC_fraction"] = unc_fraction
            metrics["total_uncertainty"] = total_unc
            outputs["validation_metrics"] = metrics

        # 2. Sample size calculation (Box 5)
        if "s_t_ha" in inputs and "MoE_t_ha" in inputs:
            alpha = float(p.get("alpha", inputs.get("alpha", 0.10)))
            sample_res = equations.sample_size_box5(
                s_t_ha=float(inputs["s_t_ha"]),
                moe_t_ha=float(inputs["MoE_t_ha"]),
                alpha=alpha,
                ctx=ctx,
            )
            outputs["sample_size"] = sample_res

        # 3. Residual trend change (Annex A)
        if "t_n" in inputs and "e_n" in inputs:
            alpha = float(p.get("alpha", 0.10))
            trend_res = equations.residual_trend_change(
                t_n=inputs["t_n"],
                e_n=inputs["e_n"],
                mu_pred_t=float(inputs["mu_pred_t"]),
                mu_pred_t_prime=float(inputs["mu_pred_t_prime"]),
                t=float(inputs["t"]),
                t_prime=float(inputs["t_prime"]),
                alpha=alpha,
                ctx=ctx,
            )
            outputs["residual_trend_change"] = trend_res

        # 4. SOC stock from bulk density
        if "soc_pct" in inputs and "bulk_density_g_cm3" in inputs and "depth_cm" in inputs:
            stock = equations.soc_stock_from_bulk_density(
                soc_pct=float(inputs["soc_pct"]),
                bulk_density_g_cm3=float(inputs["bulk_density_g_cm3"]),
                depth_cm=float(inputs["depth_cm"]),
                cfr_pct=float(inputs.get("cfr_pct", 0.0)),
                ctx=ctx,
            )
            outputs["soc_stock_t_c_ha"] = stock

        return ToolResult(
            tool_code=self.code,
            version=self.version,
            outputs=outputs,
            trace=ctx.get_trace_dict(),
            errata_applied=list(ctx.active_errata_used),
            warnings=warnings,
        )


__all__ = ["SOCModelGuidelinesTool"]
