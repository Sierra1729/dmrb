"""BM FR05.001 Mangrove A/R methodology plugin."""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from dmrv_core.equations import CalculationContext
from dmrv_core.plugin import (
    AnnualResult,
    ApplicabilityResult,
    MethodologyPlugin,
    MethodologyResult,
    ToolResult,
)
from dmrv_core.time import allocate_to_calendar_vintages, fractional_years
from methodologies.plugins.fr05_001 import equations
from methodologies.tools.bm_t_ar_0002 import BMTAR0002Tool
from methodologies.tools.bm_t_ar_0003 import BMTAR0003Tool
from methodologies.tools.bm_t_ar_0004 import BMTAR0004Tool
from methodologies.tools.bm_t_ar_0005 import BMTAR0005Tool


class BMFR05001Methodology(MethodologyPlugin):
    code: str = "BM-FR05.001"
    version: str = "1.0"
    status: Literal["APPROVED", "DRAFT"] = "APPROVED"
    tools: Dict[str, str] = {
        "BM-T-AR-0002": "1.0",
        "BM-T-AR-0003": "1.0",
        "BM-T-AR-0004": "1.0",
        "BM-T-AR-0005": "1.0",
        "BM-T-001": "1.0",
    }

    def applicability(self, ctx: CalculationContext, project: Dict[str, Any]) -> List[ApplicabilityResult]:
        is_mangrove_habitat = project.get("is_degraded_mangrove_habitat", True)
        mangrove_species_pct = project.get("mangrove_species_percentage", 100.0)
        soil_dist_pct = project.get("soil_disturbance_fraction", 0.05)

        results = [
            ApplicabilityResult(
                criterion="Land is degraded mangrove habitat (saline/brackish waterlogged soil)",
                passed=is_mangrove_habitat,
                evidence_summary=f"Degraded mangrove: {is_mangrove_habitat}",
                reason="Para 8 requirement: degraded mangrove habitat",
            ),
            ApplicabilityResult(
                criterion="> 90% of area planted with mangrove species",
                passed=mangrove_species_pct > 90.0,
                evidence_summary=f"Mangrove species fraction: {mangrove_species_pct:.1f}%",
                reason="Species composition threshold > 90%",
            ),
            ApplicabilityResult(
                criterion="Project soil disturbance does not exceed 10% of area",
                passed=soil_dist_pct <= 0.10,
                evidence_summary=f"Soil disturbance: {soil_dist_pct * 100:.2f}%",
                reason="Para 9 limit: soil disturbance <= 10%",
            ),
        ]
        return results

    def ex_post(
        self,
        ctx: CalculationContext,
        project: Dict[str, Any],
        period_data: Dict[str, Any],
    ) -> MethodologyResult:
        """Calculate ex-post net removals for mangrove A/R."""
        start_date = period_data["start_date"]
        end_date = period_data["end_date"]
        buffer_discount = project.get("buffer_reserve_fraction", 0.10)

        tool_results: Dict[str, ToolResult] = {}

        # 1. Living Trees & Shrubs (BM-T-AR-0004)
        ar4_tool = BMTAR0004Tool()
        ar4_inp_proj = period_data.get("ar0004_project", {})
        ar4_res_proj = ar4_tool.compute(ctx, ar4_inp_proj)
        tool_results["AR-0004_PROJ"] = ar4_res_proj
        delta_c_tree_proj = ar4_res_proj.outputs.get("delta_C_TREE_PROJ_tCO2e", ar4_res_proj.outputs.get("delta_C", 0.0))
        delta_c_shrub_proj = ar4_res_proj.outputs.get("delta_C_SHRUB_PROJ_tCO2e", 0.0)

        ar4_inp_bsl = period_data.get("ar0004_baseline", {})
        ar4_res_bsl = ar4_tool.compute(ctx, ar4_inp_bsl)
        tool_results["AR-0004_BSL"] = ar4_res_bsl
        delta_c_tree_bsl = ar4_res_bsl.outputs.get("delta_C_TREE_BSL_tCO2e", ar4_res_bsl.outputs.get("delta_C_per_year", 0.0))
        delta_c_shrub_bsl = ar4_res_bsl.outputs.get("delta_C_SHRUB_BSL_tCO2e", 0.0)

        # 2. Dead wood (Litter excluded in mangrove per spec 11)
        delta_c_dw_proj = 0.0
        delta_c_dw_bsl = 0.0
        if "ar0003_project" in period_data:
            ar3_tool = BMTAR0003Tool()
            ar3_res = ar3_tool.compute(ctx, period_data["ar0003_project"])
            tool_results["AR-0003_PROJ"] = ar3_res
            delta_c_dw_proj = ar3_res.outputs.get("C_DW_i_tCO2e", 0.0)

        # 3. Mangrove default SOC accumulation (Eq.4)
        cohort_areas = period_data.get("cohort_areas_ha", [100.0])
        cohort_ages = period_data.get("cohort_ages_years", [1])
        delta_soc_proj = equations.mangrove_soc_accumulation(
            cohort_areas_ha=cohort_areas,
            cohort_ages_years=cohort_ages,
            ctx=ctx,
        )

        # 4. Fire emissions (BM-T-AR-0002)
        ghg_e = 0.0
        if "ar0002" in period_data:
            ar2_tool = BMTAR0002Tool()
            ar2_res = ar2_tool.compute(ctx, period_data["ar0002"])
            tool_results["AR-0002"] = ar2_res
            ghg_e = ar2_res.outputs.get("GHG_E_tCO2e", 0.0)

        # 5. Displacement leakage (BM-T-AR-0005)
        lk = 0.0
        if "ar0005" in period_data:
            ar5_tool = BMTAR0005Tool()
            ar5_res = ar5_tool.compute(ctx, period_data["ar0005"])
            tool_results["AR-0005"] = ar5_res
            lk = ar5_res.outputs.get("LK_AGRIC_tCO2e", 0.0)

        # Removals synthesis
        delta_c_bsl = equations.mangrove_baseline_removals(delta_c_tree_bsl, delta_c_shrub_bsl, delta_c_dw_bsl, ctx=ctx)
        delta_c_p = equations.mangrove_project_removals(delta_c_tree_proj, delta_c_shrub_proj, delta_c_dw_proj, delta_soc_proj, ctx=ctx)
        delta_c_actual = delta_c_p - ghg_e
        delta_c_ar = delta_c_actual - delta_c_bsl - lk

        prior_removals = project.get("prior_cumulative_removals_tCO2e", 0.0)
        t_ccc = prior_removals + delta_c_ar
        l_ccc = delta_c_ar

        has_reversal = l_ccc < 0.0
        reversal_amount = abs(l_ccc) if has_reversal else 0.0
        if has_reversal:
            ctx.warnings.append(f"REVERSAL DETECTED in mangrove project: {l_ccc:.2f} tCO2e")

        buffer_withholding = max(0.0, delta_c_ar * buffer_discount)
        net_issuable = max(0.0, delta_c_ar - buffer_withholding)

        vintages = allocate_to_calendar_vintages(start_date, end_date, net_issuable)

        annual_results = [
            AnnualResult(
                year=int(str(start_date)[:4]),
                baseline_removals=delta_c_bsl,
                project_emissions=ghg_e,
                project_removals=delta_c_p,
                leakage=lk,
                net_reductions_or_removals=net_issuable,
                net_credits=net_issuable,
                vintages=vintages,
            )
        ]

        summary = {
            "delta_C_BSL_tCO2e": delta_c_bsl,
            "delta_C_P_tCO2e": delta_c_p,
            "delta_SOC_PROJ_tCO2e": delta_soc_proj,
            "GHG_E_tCO2e": ghg_e,
            "LK_tCO2e": lk,
            "delta_C_AR_tCO2e": delta_c_ar,
            "tCCC_t2_tCO2e": t_ccc,
            "lCCC_t2_tCO2e": l_ccc,
            "has_reversal": has_reversal,
            "reversal_amount_tCO2e": reversal_amount,
            "buffer_withholding_tCO2e": buffer_withholding,
            "net_issuable_credits_tCO2e": net_issuable,
            "vintage_allocation": vintages,
        }

        return MethodologyResult(
            methodology_code=self.code,
            version=self.version,
            tool_results=tool_results,
            annual_results=annual_results,
            total_net_credits=net_issuable,
            vintage_totals=vintages,
            trace=ctx.get_trace_dict(),
            errata_applied=list(ctx.active_errata_used),
            warnings=list(ctx.warnings),
            summary_outputs=summary,
        )

    def ex_ante(
        self,
        ctx: CalculationContext,
        project: Dict[str, Any],
        scenario_inputs: Dict[str, Any],
    ) -> MethodologyResult:
        """Ex-ante mangrove projection."""
        years = scenario_inputs.get("projection_years", 20)
        annual_growth = project.get("ex_ante_growth_tCO2e_per_yr", 80.0)
        buffer_fraction = project.get("buffer_reserve_fraction", 0.10)

        total_net = 0.0
        annual_results: List[AnnualResult] = []
        vintages: Dict[int, float] = {}
        start_year = project.get("start_year", 2026)

        for i in range(years):
            yr = start_year + i
            net_yr = annual_growth * (1.0 - buffer_fraction)
            total_net += net_yr
            vintages[yr] = net_yr
            annual_results.append(
                AnnualResult(
                    year=yr,
                    project_removals=annual_growth,
                    net_reductions_or_removals=net_yr,
                    net_credits=net_yr,
                    vintages={yr: net_yr},
                )
            )

        return MethodologyResult(
            methodology_code=self.code,
            version=self.version,
            annual_results=annual_results,
            total_net_credits=total_net,
            vintage_totals=vintages,
            trace=ctx.get_trace_dict(),
            summary_outputs={
                "projected_total_removals_tCO2e": annual_growth * years,
                "projected_net_issuable_credits_tCO2e": total_net,
            },
        )


__all__ = ["BMFR05001Methodology"]
