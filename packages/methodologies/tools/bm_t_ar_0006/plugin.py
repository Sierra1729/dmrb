"""BM-T-AR-0006 Tool Plugin implementation."""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from dmrv_core.equations import CalculationContext
from dmrv_core.plugin import ApplicabilityResult, ParameterSpec, ToolPlugin, ToolResult
from methodologies.tools.bm_t_ar_0006 import equations
from methodologies.tools.bm_t_ar_0006.errata import AR0006ErrataFlags
from methodologies.tools.bm_t_ar_0006.params import AR0006Params


class BMTAR0006Tool(ToolPlugin):
    code: str = "BM-T-AR-0006"
    version: str = "1.0"
    status: Literal["APPROVED", "DRAFT"] = "APPROVED"

    def applicability(self, ctx: CalculationContext, inputs: Dict[str, Any]) -> List[ApplicabilityResult]:
        errata = AR0006ErrataFlags()
        is_wetland = inputs.get("is_wetland", False)
        is_organic_soil = inputs.get("is_organic_soil", False)

        passed_land = not is_wetland and not is_organic_soil
        return [
            ApplicabilityResult(
                criterion="Land is mineral soil (not wetland, no organic soil)",
                passed=passed_land,
                evidence_summary=f"Wetland: {is_wetland}, Organic Soil: {is_organic_soil}",
                reason="Mineral soils only per para 4",
            )
        ]

    def required_parameters(self, options: Optional[Dict[str, Any]] = None) -> List[ParameterSpec]:
        return [
            ParameterSpec("soc_loss_fraction", "Loss fraction from soil disturbance", "dimensionless", default_value=0.10),
            ParameterSpec("disturbance_threshold_fraction", "Disturbance area threshold", "dimensionless", default_value=0.10),
            ParameterSpec("transition_years", "Transition period in years", "years", default_value=20),
            ParameterSpec("max_rate_tC_ha_yr", "Maximum annual SOC accumulation rate cap", "t C / ha / yr", default_value=0.80),
        ]

    def compute(
        self,
        ctx: CalculationContext,
        inputs: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None,
    ) -> ToolResult:
        params = AR0006Params()
        errata = AR0006ErrataFlags()

        soc_ref = inputs["SOC_REF"]
        f_lu = inputs["f_LU"]
        f_mg = inputs["f_MG"]
        f_in = inputs["f_IN"]
        t_prep = inputs.get("t_PREP", 1)
        a_i = inputs.get("A_i_ha", 1.0)
        dist_gt_10pct = inputs.get("disturbance_gt_10pct", False)
        dist_frac = 0.15 if dist_gt_10pct else inputs.get("disturbance_fraction", 0.0)

        # 1. Initial SOC
        soc_initial = equations.initial_soil_organic_carbon(soc_ref, f_lu, f_mg, f_in, ctx=ctx)

        # 2. Disturbance loss
        soc_loss = equations.soil_disturbance_loss(
            soc_initial, dist_frac, threshold=params.disturbance_threshold_fraction, loss_factor=params.soc_loss_fraction, ctx=ctx
        )

        # 3. Accumulation rate
        acc_rate = equations.annual_soc_accumulation_rate(
            soc_ref, soc_initial, soc_loss, transition_years=params.transition_years, max_rate_cap=params.max_rate_tC_ha_yr, ctx=ctx
        )

        # 4. Multi-year rate calculation (e.g. t = 1 to 23)
        years = inputs.get("evaluation_years", list(range(1, 24)))
        dsoc_by_year = [
            equations.soc_rate_at_year(
                t, t_prep, soc_loss, acc_rate, transition_years=params.transition_years, ctx=ctx
            )
            for t in years
        ]

        delta_soc_al_by_year = [
            equations.total_stratum_soc_change([a_i], [r], ctx=ctx)
            for r in dsoc_by_year
        ]

        outputs = {
            "SOC_INITIAL": soc_initial,
            "SOC_LOSS": soc_loss,
            "annual_accumulation_rate": acc_rate,
            "dSOC_by_year_t1_to_t23": dsoc_by_year,
            "delta_SOC_AL_tCO2e_by_year": delta_soc_al_by_year,
        }

        return ToolResult(
            tool_code=self.code,
            version=self.version,
            outputs=outputs,
            trace=ctx.get_trace_dict(),
            errata_applied=list(ctx.active_errata_used),
            warnings=list(ctx.warnings),
        )
