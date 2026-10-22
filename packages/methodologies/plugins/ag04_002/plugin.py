"""BM AG04.002 Methodology Plugin: Improved Management Practices in Rice Cultivation."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from dmrv_core.equations import CalculationContext
from dmrv_core.plugin import (
    AnnualResult,
    ApplicabilityResult,
    MethodologyPlugin,
    MethodologyResult,
    ParameterSpec,
)
from methodologies.plugins.ag04_002 import equations
from methodologies.plugins.ag04_002.errata import AG04002ErrataFlags
from methodologies.plugins.ag04_002.params import AG04002Params


@dataclass
class BMAG04002Plugin(MethodologyPlugin):
    code: str = "BM-AG04.002"
    version: str = "1.0"
    tools: Dict[str, str] = field(default_factory=lambda: {"BM-T-001": "1.0"})

    def applicability(self, ctx: CalculationContext, project: Dict[str, Any]) -> List[ApplicabilityResult]:
        results: List[ApplicabilityResult] = []

        # 1. Water regime: predominantly irrigated with controlled drainage
        water_source = project.get("water_source", "irrigated_controlled").lower()
        is_controlled = "irrigated" in water_source and "rainfed" not in water_source and "deep" not in water_source
        results.append(
            ApplicabilityResult(
                criterion="Predominantly irrigated, flooded rice with controlled irrigation and drainage",
                passed=is_controlled,
                evidence_summary=f"Water source: {water_source}",
                reason="Eligible controlled irrigation" if is_controlled else "Upland/rainfed/deep-water excluded",
            )
        )

        # 2. Documented farmer training
        training_documented = project.get("training_and_technical_support_documented", True)
        results.append(
            ApplicabilityResult(
                criterion="Verifiable training in field preparation, irrigation, drainage, and N-fertilization",
                passed=training_documented,
                evidence_summary=f"Training records verified: {training_documented}",
                reason="Documented training program" if training_documented else "Missing verifiable training records",
            )
        )

        # 3. Eligible water regime transition
        activity_type = project.get("activity_type", "AWD").upper()
        eligible_activities = ["AWD", "INTERMITTENT_DRAINAGE", "AEROBIC_RICE", "DSR"]
        is_eligible_act = any(act in activity_type for act in eligible_activities)
        results.append(
            ApplicabilityResult(
                criterion="Eligible management change (AWD, intermittent flooding, aerobic rice, or DSR)",
                passed=is_eligible_act,
                evidence_summary=f"Management change: {activity_type}",
                reason="Eligible practice transition" if is_eligible_act else "Practice change not recognized under methodology",
            )
        )

        return results

    def required_parameters(self) -> List[ParameterSpec]:
        return [
            ParameterSpec("GWP_CH4", "Global warming potential of methane", "t CO2e / t CH4", default_value=29.8),
            ParameterSpec("GWP_N2O", "Global warming potential of nitrous oxide", "t CO2e / t N2O", default_value=273.0),
            ParameterSpec("U_d", "Uncertainty deduction factor", "dimensionless", default_value=0.15),
            ParameterSpec("EF_N2O_B", "Baseline N2O emission factor (continuously flooded)", "kg N2O-N / kg N", default_value=0.003),
            ParameterSpec("EF_N2O_P", "Project N2O emission factor (AWD / drained)", "kg N2O-N / kg N", default_value=0.005),
        ]

    def ex_ante(
        self,
        ctx: CalculationContext,
        project: Dict[str, Any],
        scenario_inputs: Dict[str, Any],
    ) -> MethodologyResult:
        # Tier 1 ex-ante projection
        params = AG04002Params()
        years = scenario_inputs.get("years", [2026])
        area_ha = float(scenario_inputs.get("total_area_ha", 100.0))
        ef_bl_continuous = float(scenario_inputs.get("ef_baseline_continuous_kg_ha", 300.0))
        sf_w_bl = float(scenario_inputs.get("sf_w_bl", params.sf_w_defaults["continuously_flooded"]))
        sf_w_pr = float(scenario_inputs.get("sf_w_pr", params.sf_w_defaults["multiple_aeration"]))
        u_d = float(scenario_inputs.get("u_d", params.u_d_default))

        ef_bl = equations.tier1_emission_factor(ef_bl_continuous, sf_w=sf_w_bl, ctx=ctx)
        ef_pr = equations.tier1_emission_factor(ef_bl_continuous, sf_w=sf_w_pr, ctx=ctx)

        annual_results: List[AnnualResult] = []
        for y in years:
            be_y = (ef_bl * area_ha) * 1e-3 * 29.8
            pe_y = (ef_pr * area_ha) * 1e-3 * 29.8
            net_er = equations.net_emission_reductions_rice(be_y, pe_y, u_d=u_d, ctx=ctx)
            annual_results.append(
                AnnualResult(
                    year=y,
                    baseline_emissions=be_y,
                    project_emissions=pe_y,
                    net_credits=net_er,
                )
            )

        total_er = sum(r.net_credits for r in annual_results)
        return MethodologyResult(
            methodology_code=self.code,
            version=self.version,
            annual_results=annual_results,
            total_net_credits=total_er,
            trace=ctx.get_trace_dict(),
            errata_applied=list(ctx.active_errata_used),
            warnings=ctx.warnings,
        )

    def ex_post(
        self,
        ctx: CalculationContext,
        project: Dict[str, Any],
        period_data: Dict[str, Any],
    ) -> MethodologyResult:
        year = int(period_data.get("year", 2026))
        u_d = float(period_data.get("u_d", 0.15))

        # Baseline emissions from reference fields
        ef_bl_list = period_data.get("ef_bl_kg_ha_season", [300.0])
        area_bl_list = period_data.get("area_ha_by_group", [100.0])
        be_y = equations.baseline_ch4_emissions_season(ef_bl_list, area_bl_list, ctx=ctx)

        # Project CH4 emissions
        ef_p_list = period_data.get("ef_p_kg_ha_season", [165.0])
        pe_ch4 = equations.project_ch4_emissions_season(ef_p_list, area_bl_list, ctx=ctx)

        # Incremental N2O emissions
        q_n_list = period_data.get("nitrogen_applied_kg_ha", [100.0])
        pe_n2o = equations.project_n2o_emissions(q_n_list, area_bl_list, ctx=ctx)

        # Land preparation emissions (if any)
        pe_l = float(period_data.get("pe_land_preparation_tco2e", 0.0))

        pe_y = pe_ch4 + pe_n2o + pe_l
        net_er = equations.net_emission_reductions_rice(be_y, pe_y, u_d=u_d, ctx=ctx)

        res = AnnualResult(
            year=year,
            baseline_emissions=be_y,
            project_emissions=pe_y,
            net_credits=net_er,
        )

        return MethodologyResult(
            methodology_code=self.code,
            version=self.version,
            annual_results=[res],
            total_net_credits=net_er,
            trace=ctx.get_trace_dict(),
            errata_applied=list(ctx.active_errata_used),
            warnings=ctx.warnings,
        )


__all__ = ["BMAG04002Plugin"]
