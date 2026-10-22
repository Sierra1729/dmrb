"""BM WA03.002 Methodology Plugin: Landfill gas flaring or use."""
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
from methodologies.plugins.wa03_002 import equations
from methodologies.tools.bm_t_011 import BMT011Tool


class BMWA03002Methodology(MethodologyPlugin):
    code: str = "BM-WA03.002"
    version: str = "1.0"
    status: Literal["APPROVED", "DRAFT"] = "APPROVED"
    tools: Dict[str, str] = {
        "BM-T-001": "1.0",
        "BM-T-011": "1.0",
    }

    def applicability(self, ctx: CalculationContext, project: Dict[str, Any]) -> List[ApplicabilityResult]:
        swds_exists = project.get("is_existing_or_greenfield_swds", True)
        deliberate_ch4_increase = project.get("deliberate_swds_change_to_raise_ch4", False)

        results = [
            ApplicabilityResult(
                criterion="Activity captures LFG at an existing or greenfield SWDS",
                passed=swds_exists,
                evidence_summary="Site layout and permit records",
                reason="Applicable to new LFG capture or investment in existing venting SWDS",
            ),
            ApplicabilityResult(
                criterion="SWDS management is not deliberately changed to increase methane generation",
                passed=not deliberate_ch4_increase,
                evidence_summary="SWDS operational plan",
                reason="Excludes sites with deliberate management changes to artificially raise methane",
            ),
        ]
        return results

    def ex_post(
        self,
        ctx: CalculationContext,
        project: Dict[str, Any],
        period_data: Dict[str, Any],
    ) -> MethodologyResult:
        """Calculate ex-post emission reductions from metered LFG destruction."""
        start_date = period_data["start_date"]
        end_date = period_data["end_date"]
        gwp_ch4 = project.get("gwp_ch4", 29.8)
        ox_top = project.get("ox_top_layer", 0.10)

        # Metered methane captured and destroyed (t CH4)
        f_flared = period_data.get("F_CH4_flared_t", 0.0)
        f_el = period_data.get("F_CH4_electricity_t", 0.0)
        f_hg = period_data.get("F_CH4_heat_t", 0.0)
        f_ng = period_data.get("F_CH4_network_t", 0.0)

        f_ch4_pj = equations.total_methane_captured(f_flared, f_el, f_hg, f_ng, ctx=ctx)

        # Baseline destruction F_CH4,BL,y (Case 1: 0; Case 2: regulatory target; Case 3: historic)
        baseline_case = project.get("baseline_case", 1)
        f_ch4_bl = 0.0
        if baseline_case == 2:
            reg_rate = project.get("regulatory_destruction_rate", 0.20)
            f_ch4_bl = reg_rate * f_ch4_pj
        elif baseline_case == 3:
            f_ch4_bl = project.get("baseline_historic_flow_t", 0.20 * f_ch4_pj)

        be_ch4 = equations.baseline_methane_emissions(
            f_ch4_pj_y=f_ch4_pj,
            f_ch4_bl_y=f_ch4_bl,
            gwp_ch4=gwp_ch4,
            ox_top_layer=ox_top,
            ctx=ctx,
        )

        pe_total = period_data.get("PE_tCO2e", 0.0)
        le_total = period_data.get("LE_tCO2e", 0.0)
        net_er = equations.emission_reductions(be_ch4, pe_total, le_total, ctx=ctx)

        vintages = allocate_to_calendar_vintages(start_date, end_date, net_er)

        annual_results = [
            AnnualResult(
                year=int(str(start_date)[:4]),
                baseline_emissions=be_ch4,
                project_emissions=pe_total,
                leakage=le_total,
                net_reductions_or_removals=net_er,
                net_credits=net_er,
                vintages=vintages,
            )
        ]

        summary = {
            "F_CH4_PJ_tCH4": f_ch4_pj,
            "F_CH4_BL_tCH4": f_ch4_bl,
            "BE_CH4_tCO2e": be_ch4,
            "PE_tCO2e": pe_total,
            "LE_tCO2e": le_total,
            "ER_tCO2e": net_er,
            "vintage_allocation": vintages,
        }

        return MethodologyResult(
            methodology_code=self.code,
            version=self.version,
            annual_results=annual_results,
            total_net_credits=net_er,
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
        """Ex-ante baseline projection using BM-T-011 Application A."""
        t11_tool = BMT011Tool()
        t11_inp = scenario_inputs.get("bm_t_011_application_a", {})
        t11_res = t11_tool.compute(ctx, t11_inp)

        swds_emissions_series = t11_res.outputs.get("emissions_by_year_tCO2e", [])
        gwp_ch4 = project.get("gwp_ch4", 29.8)
        eta_pj = project.get("lfg_collection_efficiency", 0.50)

        annual_results: List[AnnualResult] = []
        total_er = 0.0
        vintages: Dict[int, float] = {}
        start_year = project.get("start_year", 2026)

        for idx, be_swds in enumerate(swds_emissions_series):
            yr = start_year + idx
            f_pj = equations.ex_ante_methane_capture(be_swds, gwp_ch4, eta_pj=eta_pj, ctx=ctx)
            be_y = equations.baseline_methane_emissions(f_pj, f_ch4_bl_y=0.0, gwp_ch4=gwp_ch4, ctx=ctx)
            total_er += be_y
            vintages[yr] = be_y
            annual_results.append(
                AnnualResult(
                    year=yr,
                    baseline_emissions=be_y,
                    net_reductions_or_removals=be_y,
                    net_credits=be_y,
                    vintages={yr: be_y},
                )
            )

        return MethodologyResult(
            methodology_code=self.code,
            version=self.version,
            tool_results={"BM-T-011": t11_res},
            annual_results=annual_results,
            total_net_credits=total_er,
            vintage_totals=vintages,
            trace=ctx.get_trace_dict(),
            errata_applied=list(ctx.active_errata_used),
            warnings=list(ctx.warnings),
            summary_outputs={
                "projected_total_ER_tCO2e": total_er,
                "swds_emissions_series": swds_emissions_series,
            },
        )


__all__ = ["BMWA03002Methodology"]
