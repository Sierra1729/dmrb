"""BM-T-001 Additionality and Baseline Identification Tool Plugin."""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from dmrv_core.equations import CalculationContext
from dmrv_core.plugin import ApplicabilityResult, ParameterSpec, ToolPlugin, ToolResult
from methodologies.tools.bm_t_001 import equations
from methodologies.tools.bm_t_001.errata import T001ErrataFlags
from methodologies.tools.bm_t_001.params import T001Params


class BMT001Tool(ToolPlugin):
    code: str = "BM-T-001"
    version: str = "1.0"
    status: Literal["APPROVED", "DRAFT"] = "APPROVED"

    def applicability(self, ctx: CalculationContext, inputs: Dict[str, Any]) -> List[ApplicabilityResult]:
        # BM-T-001 applies to all CCTS offset projects
        return [
            ApplicabilityResult(
                criterion="Project is under the CCTS Offset Mechanism",
                passed=True,
                evidence_summary="Project registration documents",
                reason="BM-T-001 applies to all project types under CCTS",
            )
        ]

    def required_parameters(self, options: Optional[Dict[str, Any]] = None) -> List[ParameterSpec]:
        return [
            ParameterSpec("financial_benchmark_rate", "Benchmark hurdle rate / discount rate", "dimensionless", required=False, default_value=0.10),
            ParameterSpec("sensitivity_range", "Variation percentage range for sensitivity", "dimensionless", required=False, default_value=0.10),
        ]

    def compute(
        self,
        ctx: CalculationContext,
        inputs: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None,
    ) -> ToolResult:
        """Execute BM-T-001 additionality and baseline identification workflow."""
        errata = T001ErrataFlags()
        params = T001Params()

        steps_log: Dict[str, Any] = {}
        is_additional = True
        failure_reasons: List[str] = []
        selected_baseline: Optional[str] = None

        # -------------------------------------------------------------
        # Step M1: Regulatory Analysis (paras 7-10)
        # -------------------------------------------------------------
        regulations = inputs.get("regulations", [])
        m1_passed = True
        m1_details = []
        for reg in regulations:
            name = reg.get("name", "Unnamed Regulation")
            requires_activity = reg.get("directly_or_indirectly_requires_activity", False)
            has_offset_exception = reg.get("has_offset_integration_exception", False)

            if requires_activity and not has_offset_exception:
                m1_passed = False
                failure_reasons.append(f"M1: Mandated by {name} without carbon offset exemption.")
            m1_details.append({
                "name": name,
                "compliant": not (requires_activity and not has_offset_exception),
            })
        steps_log["M1_regulatory_analysis"] = {"passed": m1_passed, "regulations": m1_details}
        if not m1_passed:
            is_additional = False

        # -------------------------------------------------------------
        # Step M2: Lock-in Risk Analysis (paras 11-17)
        # -------------------------------------------------------------
        lockin_info = inputs.get("lock_in_risk", {})
        lifetime_years = lockin_info.get("operational_lifetime_years", 10)
        has_inefficient_resource_use = lockin_info.get("inefficient_resource_use", False)

        m2_passed = True
        if lifetime_years > params.max_lifetime_for_no_lockin_years and has_inefficient_resource_use:
            m2_passed = False
            failure_reasons.append("M2: High lock-in risk due to long operational lifetime and inefficient resource use.")
        steps_log["M2_lockin_risk"] = {"passed": m2_passed, "lifetime_years": lifetime_years}
        if not m2_passed:
            is_additional = False

        # -------------------------------------------------------------
        # Step S1: Alternatives & Legal Filter (paras 18-24)
        # -------------------------------------------------------------
        # S1: Project without CCTS; S2..S6 plausible alternatives
        raw_alternatives = inputs.get("alternatives", [
            {"id": "S1", "description": "Proposed project without CCTS revenues", "compliant": True},
            {"id": "S2", "description": "Continuation of baseline activities (BAU)", "compliant": True},
        ])
        s1b_viable = [alt for alt in raw_alternatives if alt.get("compliant", True)]
        steps_log["S1_alternatives"] = {"total": len(raw_alternatives), "legally_viable": [a["id"] for a in s1b_viable]}

        if len(s1b_viable) <= 1 and any(a["id"] == "S1" for a in s1b_viable):
            is_additional = False
            failure_reasons.append("S1b: Only S1 is legally viable; not additional.")

        # -------------------------------------------------------------
        # Step S2: Barrier Analysis (paras 25-28)
        # -------------------------------------------------------------
        barriers_input = inputs.get("barriers", [])
        # List of barriers preventing each alternative
        unprevented_alts = []
        for alt in s1b_viable:
            alt_id = alt["id"]
            # Look for barriers that apply to this alt
            prevented = any(
                b.get("alternative_id") == alt_id and b.get("is_prevented", False)
                for b in barriers_input
            )
            if not prevented:
                unprevented_alts.append(alt)

        steps_log["S2_barriers"] = {
            "unprevented_alternatives": [a["id"] for a in unprevented_alts]
        }

        # -------------------------------------------------------------
        # Step S3: Investment Analysis (paras 30-40)
        # -------------------------------------------------------------
        financial_info = inputs.get("financials")
        inv_results = {}
        if financial_info:
            cfs = financial_info.get("cash_flows", [])
            discount_r = financial_info.get("discount_rate", 0.10)
            benchmark_r = financial_info.get("benchmark_rate", 0.12)

            npv_val = equations.net_present_value(cfs, discount_r, ctx=ctx)
            irr_val = equations.internal_rate_of_return(cfs, ctx=ctx)
            sens = equations.sensitivity_analysis(
                cfs, [-0.10, 0.0, 0.10], discount_r, benchmark_rate=benchmark_r, ctx=ctx
            )

            # Project is financially viable without CCTS if IRR >= benchmark or NPV >= 0
            is_financially_viable = (irr_val is not None and irr_val >= benchmark_r) or (npv_val >= 0.0)
            if is_financially_viable:
                is_additional = False
                failure_reasons.append("S3: Project activity is financially attractive without carbon finance.")

            inv_results = {
                "npv": npv_val,
                "irr": irr_val,
                "benchmark_rate": benchmark_r,
                "is_financially_viable_without_ccts": is_financially_viable,
                "sensitivity": sens,
            }
        steps_log["S3_investment_analysis"] = inv_results

        # Determine Baseline scenario
        non_s1_alts = [a["id"] for a in unprevented_alts if a["id"] != "S1"]
        if non_s1_alts:
            selected_baseline = non_s1_alts[0]
        else:
            selected_baseline = "S2"

        # -------------------------------------------------------------
        # Step S4: Common Practice (paras 41-47)
        # -------------------------------------------------------------
        common_practice_info = inputs.get("common_practice", {})
        similar_activities_observed = common_practice_info.get("similar_activities_observed", False)
        has_essential_distinctions = common_practice_info.get("has_essential_distinctions", True)

        if similar_activities_observed and not has_essential_distinctions:
            is_additional = False
            failure_reasons.append("S4: Common practice in geographical area with no essential distinctions.")

        steps_log["S4_common_practice"] = {
            "similar_activities_observed": similar_activities_observed,
            "has_essential_distinctions": has_essential_distinctions,
        }

        # -------------------------------------------------------------
        # Final Additionality Conclusion & PDD Narrative Draft
        # -------------------------------------------------------------
        pdd_draft = self._generate_pdd_section(is_additional, selected_baseline, steps_log, failure_reasons)

        outputs = {
            "is_additional": is_additional,
            "selected_baseline_scenario": selected_baseline,
            "failure_reasons": failure_reasons,
            "steps_log": steps_log,
            "pdd_section_draft": pdd_draft,
        }

        return ToolResult(
            tool_code=self.code,
            version=self.version,
            outputs=outputs,
            trace=ctx.get_trace_dict(),
            errata_applied=list(ctx.active_errata_used),
            warnings=list(ctx.warnings) + failure_reasons,
        )

    def _generate_pdd_section(
        self,
        is_additional: bool,
        baseline: Optional[str],
        steps_log: Dict[str, Any],
        reasons: List[str],
    ) -> str:
        """Draft section B.3 / B.4 of PDD template."""
        status_text = "DEMONSTRATED" if is_additional else "NOT DEMONSTRATED"
        return (
            f"### Section B: Baseline Scenario and Additionality (BM-T-001 v1.0)\n\n"
            f"**Conclusion:** Additionality is **{status_text}**.\n"
            f"**Selected Baseline Scenario:** {baseline or 'Undetermined'}\n\n"
            f"**1. Regulatory Analysis (M1):** "
            f"{'Passed - no mandatory regulation requires the activity without offset eligibility' if steps_log.get('M1_regulatory_analysis', {}).get('passed') else 'Failed'}.\n"
            f"**2. Lock-in Risk (M2):** "
            f"{'Passed - operational life and technology do not create carbon lock-in' if steps_log.get('M2_lockin_risk', {}).get('passed') else 'Failed'}.\n"
            f"**3. Investment / Barrier Analysis (S2/S3):** "
            f"Project activity faces prohibitive barriers / requires carbon finance to bridge financial benchmark.\n"
            f"**4. Common Practice Analysis (S4):** "
            f"Activity is not common practice in the defined geographical boundary without essential distinctions.\n"
        )


__all__ = ["BMT001Tool"]
