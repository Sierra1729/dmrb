"""BM FR05.002 Methodology Plugin coordinator."""
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
from methodologies.plugins.fr05_002 import equations
from methodologies.tools.bm_t_ar_0002 import BMTAR0002Tool
from methodologies.tools.bm_t_ar_0003 import BMTAR0003Tool
from methodologies.tools.bm_t_ar_0004 import BMTAR0004Tool
from methodologies.tools.bm_t_ar_0005 import BMTAR0005Tool
from methodologies.tools.bm_t_ar_0006 import BMTAR0006Tool


class BMFR05002Methodology(MethodologyPlugin):
    code: str = "BM-FR05.002"
    version: str = "1.0"
    status: Literal["APPROVED", "DRAFT"] = "APPROVED"
    tools: Dict[str, str] = {
        "BM-T-AR-0002": "1.0",
        "BM-T-AR-0003": "1.0",
        "BM-T-AR-0004": "1.0",
        "BM-T-AR-0005": "1.0",
        "BM-T-AR-0006": "1.0",
        "BM-T-001": "1.0",
    }

    def applicability(self, ctx: CalculationContext, project: Dict[str, Any]) -> List[ApplicabilityResult]:
        """Methodology applicability per para 9-11."""
        is_wetland = project.get("is_wetland", False)
        soil_dist_pct = project.get("soil_disturbance_fraction", 0.0)

        results = [
            ApplicabilityResult(
                criterion="Land is not a wetland or peatland",
                passed=not is_wetland,
                evidence_summary=f"Wetland status: {is_wetland}",
                reason="FR05.002 excludes wetlands per title and applicability rules",
            ),
            ApplicabilityResult(
                criterion="Project soil disturbance does not exceed 10% of area",
                passed=soil_dist_pct <= 0.10,
                evidence_summary=f"Soil disturbance: {soil_dist_pct * 100:.2f}%",
                reason="Para 10 limit: soil disturbance <= 10%",
            ),
        ]
        return results

    def ex_post(
        self,
        ctx: CalculationContext,
        project: Dict[str, Any],
        period_data: Dict[str, Any],
    ) -> MethodologyResult:
        """Run ex-post net GHG removal calculation for monitoring period t1 -> t2."""
        start_date = period_data["start_date"]
        end_date = period_data["end_date"]
        t_years = fractional_years(start_date, end_date)

        # Configured pools & parameters
        pools = project.get("selected_pools", ["tree_biomass"])
        include_shrubs = "shrubs" in pools
        include_deadwood = "dead_wood" in pools
        include_litter = "litter" in pools
        include_soc = "soc" in pools
        buffer_discount = project.get("buffer_reserve_fraction", 0.10)

        tool_results: Dict[str, ToolResult] = {}

        # -------------------------------------------------------------
        # 1. Living Trees & Shrubs (BM-T-AR-0004)
        # -------------------------------------------------------------
        ar4_tool = BMTAR0004Tool()
        ar4_inputs_proj = period_data.get("ar0004_project", {})
        ar4_res_proj = ar4_tool.compute(ctx, ar4_inputs_proj)
        tool_results["AR-0004_PROJ"] = ar4_res_proj

        delta_c_tree_proj = (
            ar4_res_proj.outputs.get("delta_C_TREE_PROJ_tCO2e")
            if ar4_res_proj.outputs.get("delta_C_TREE_PROJ_tCO2e") is not None
            else ar4_res_proj.outputs.get("delta_C", 0.0)
        )
        delta_c_shrub_proj = ar4_res_proj.outputs.get("delta_C_SHRUB_PROJ_tCO2e", 0.0) if include_shrubs else 0.0

        ar4_inputs_bsl = period_data.get("ar0004_baseline", {})
        ar4_res_bsl = ar4_tool.compute(ctx, ar4_inputs_bsl)
        tool_results["AR-0004_BSL"] = ar4_res_bsl
        delta_c_tree_bsl = (
            ar4_res_bsl.outputs.get("delta_C_TREE_BSL_tCO2e")
            if ar4_res_bsl.outputs.get("delta_C_TREE_BSL_tCO2e") is not None
            else ar4_res_bsl.outputs.get("delta_C_per_year", 0.0)
        )
        delta_c_shrub_bsl = ar4_res_bsl.outputs.get("delta_C_SHRUB_BSL_tCO2e", 0.0) if include_shrubs else 0.0

        # -------------------------------------------------------------
        # 2. Dead Wood & Litter (BM-T-AR-0003)
        # -------------------------------------------------------------
        delta_c_dw_proj = 0.0
        delta_c_li_proj = 0.0
        delta_c_dw_bsl = 0.0
        delta_c_li_bsl = 0.0

        if include_deadwood or include_litter:
            ar3_tool = BMTAR0003Tool()
            ar3_inp_proj = period_data.get("ar0003_project", {})
            if ar3_inp_proj:
                ar3_res_proj = ar3_tool.compute(ctx, ar3_inp_proj)
                tool_results["AR-0003_PROJ"] = ar3_res_proj
                if include_deadwood:
                    delta_c_dw_proj = ar3_res_proj.outputs.get("C_DW_i_tCO2e", 0.0)
                if include_litter:
                    delta_c_li_proj = ar3_res_proj.outputs.get("C_LI_i_tCO2e", 0.0)

            ar3_inp_bsl = period_data.get("ar0003_baseline", {})
            if ar3_inp_bsl:
                ar3_res_bsl = ar3_tool.compute(ctx, ar3_inp_bsl)
                tool_results["AR-0003_BSL"] = ar3_res_bsl
                if include_deadwood:
                    delta_c_dw_bsl = ar3_res_bsl.outputs.get("C_DW_i_tCO2e", 0.0)
                if include_litter:
                    delta_c_li_bsl = ar3_res_bsl.outputs.get("C_LI_i_tCO2e", 0.0)

        # -------------------------------------------------------------
        # 3. Soil Organic Carbon (BM-T-AR-0006)
        # -------------------------------------------------------------
        delta_soc_al = 0.0
        if include_soc:
            ar6_tool = BMTAR0006Tool()
            ar6_inp = period_data.get("ar0006", {})
            if ar6_inp:
                ar6_res = ar6_tool.compute(ctx, ar6_inp)
                tool_results["AR-0006"] = ar6_res
                # Use current monitoring year rate or total change
                rates = ar6_res.outputs.get("delta_SOC_AL_tCO2e_by_year", [0.0])
                delta_soc_al = rates[0] if rates else 0.0

        # -------------------------------------------------------------
        # 4. Biomass Burning Emissions (BM-T-AR-0002)
        # -------------------------------------------------------------
        ghg_e = 0.0
        ar2_inp = period_data.get("ar0002")
        if ar2_inp:
            ar2_tool = BMTAR0002Tool()
            ar2_res = ar2_tool.compute(ctx, ar2_inp)
            tool_results["AR-0002"] = ar2_res
            ghg_e = ar2_res.outputs.get("GHG_E_tCO2e", 0.0)

        # -------------------------------------------------------------
        # 5. Agricultural Displacement Leakage (BM-T-AR-0005)
        # -------------------------------------------------------------
        lk = 0.0
        ar5_inp = period_data.get("ar0005")
        if ar5_inp:
            ar5_tool = BMTAR0005Tool()
            ar5_res = ar5_tool.compute(ctx, ar5_inp)
            tool_results["AR-0005"] = ar5_res
            lk = ar5_res.outputs.get("LK_AGRIC_tCO2e", 0.0)

        # -------------------------------------------------------------
        # Methodology Synthesis: Eq. 1 to Eq. 7
        # -------------------------------------------------------------
        delta_c_bsl = equations.baseline_carbon_stock_change(
            delta_c_tree_bsl=delta_c_tree_bsl,
            delta_c_shrub_bsl=delta_c_shrub_bsl,
            delta_c_dw_bsl=delta_c_dw_bsl,
            delta_c_li_bsl=delta_c_li_bsl,
            ctx=ctx,
        )

        delta_c_p = equations.project_carbon_stock_change(
            delta_c_tree_proj=delta_c_tree_proj,
            delta_c_shrub_proj=delta_c_shrub_proj,
            delta_c_dw_proj=delta_c_dw_proj,
            delta_c_li_proj=delta_c_li_proj,
            delta_soc_al=delta_soc_al,
            ctx=ctx,
        )

        delta_c_actual = equations.actual_net_removals(delta_c_p=delta_c_p, ghg_e=ghg_e, ctx=ctx)

        delta_c_ar = equations.net_anthropogenic_removals(
            delta_c_actual=delta_c_actual,
            delta_c_bsl=delta_c_bsl,
            leakage=lk,
            ctx=ctx,
        )

        # Historical removals before this monitoring period
        prior_removals = project.get("prior_cumulative_removals_tCO2e", 0.0)
        t_ccc = prior_removals + delta_c_ar
        l_ccc = delta_c_ar

        # Reversal detection per Eq. 7
        has_reversal = l_ccc < 0.0
        reversal_amount = abs(l_ccc) if has_reversal else 0.0
        if has_reversal:
            ctx.warnings.append(
                f"REVERSAL DETECTED: lCCC is negative ({l_ccc:.2f} tCO2e). Buffer replenishment required."
            )

        # Buffer withholding on positive net removals
        buffer_withholding = max(0.0, delta_c_ar * buffer_discount)
        net_issuable_credits = max(0.0, delta_c_ar - buffer_withholding)

        # Allocate to calendar vintages
        vintage_allocation = allocate_to_calendar_vintages(start_date, end_date, net_issuable_credits)

        annual_results = [
            AnnualResult(
                year=int(str(start_date)[:4]),
                baseline_emissions=0.0,
                baseline_removals=delta_c_bsl,
                project_emissions=ghg_e,
                project_removals=delta_c_p,
                leakage=lk,
                net_credits=net_issuable_credits,
                vintages=vintage_allocation,
            )
        ]

        summary_outputs = {
            "delta_C_BSL_tCO2e": delta_c_bsl,
            "delta_C_P_tCO2e": delta_c_p,
            "GHG_E_tCO2e": ghg_e,
            "delta_C_ACTUAL_tCO2e": delta_c_actual,
            "LK_tCO2e": lk,
            "delta_C_AR_tCO2e": delta_c_ar,
            "tCCC_t2_tCO2e": t_ccc,
            "lCCC_t2_tCO2e": l_ccc,
            "has_reversal": has_reversal,
            "reversal_amount_tCO2e": reversal_amount,
            "buffer_reserve_fraction": buffer_discount,
            "buffer_withholding_tCO2e": buffer_withholding,
            "net_issuable_credits_tCO2e": net_issuable_credits,
            "vintage_allocation": vintage_allocation,
        }

        return MethodologyResult(
            methodology_code=self.code,
            version=self.version,
            tool_results=tool_results,
            annual_results=annual_results,
            total_net_credits=net_issuable_credits,
            vintage_totals=vintage_allocation,
            trace=ctx.get_trace_dict(),
            errata_applied=list(ctx.active_errata_used),
            warnings=list(ctx.warnings),
            summary_outputs=summary_outputs,
        )

    def ex_ante(
        self,
        ctx: CalculationContext,
        project: Dict[str, Any],
        scenario_inputs: Dict[str, Any],
    ) -> MethodologyResult:
        """Run ex-ante projection across crediting period using growth models."""
        projection_years = scenario_inputs.get("projection_years", 20)
        # Baseline assumption: 0 or proportionate crown cover
        # Project assumption: yield table or Chapman-Richards curve
        annual_results: List[AnnualResult] = []
        total_net = 0.0
        vintages: Dict[int, float] = {}

        start_year = project.get("start_year", 2026)
        annual_growth_rate = project.get("ex_ante_growth_tCO2e_per_yr", 100.0)
        buffer_fraction = project.get("buffer_reserve_fraction", 0.10)

        for yr_idx in range(projection_years):
            yr = start_year + yr_idx
            net_yr = annual_growth_rate * (1.0 - buffer_fraction)
            total_net += net_yr
            vintages[yr] = net_yr
            annual_results.append(
                AnnualResult(
                    year=yr,
                    baseline_emissions=0.0,
                    baseline_removals=0.0,
                    project_emissions=0.0,
                    project_removals=annual_growth_rate,
                    leakage=0.0,
                    net_credits=net_yr,
                    vintages={yr: net_yr},
                )
            )

        return MethodologyResult(
            methodology_code=self.code,
            version=self.version,
            tool_results={},
            annual_results=annual_results,
            total_net_credits=total_net,
            vintage_totals=vintages,
            trace=ctx.get_trace_dict(),
            errata_applied=[],
            warnings=[],
            summary_outputs={
                "projected_total_removals_tCO2e": annual_growth_rate * projection_years,
                "projected_net_issuable_credits_tCO2e": total_net,
            },
        )


__all__ = ["BMFR05002Methodology"]
