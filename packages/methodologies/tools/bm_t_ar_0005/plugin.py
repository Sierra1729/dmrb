"""BM-T-AR-0005 Tool Plugin implementation."""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from dmrv_core.equations import CalculationContext
from dmrv_core.plugin import ApplicabilityResult, ParameterSpec, ToolPlugin, ToolResult
from methodologies.tools.bm_t_ar_0005 import equations
from methodologies.tools.bm_t_ar_0005.params import AR0005Params


class BMTAR0005Tool(ToolPlugin):
    code: str = "BM-T-AR-0005"
    version: str = "1.0"
    status: Literal["APPROVED", "DRAFT"] = "APPROVED"

    def applicability(self, ctx: CalculationContext, inputs: Dict[str, Any]) -> List[ApplicabilityResult]:
        drains_wetlands = inputs.get("causes_wetland_or_peatland_drainage", False)
        return [
            ApplicabilityResult(
                criterion="Displacement does NOT cause direct or indirect drainage of wetlands or peatlands",
                passed=not drains_wetlands,
                evidence_summary="Environmental assessment / land-use survey",
                reason="Hard block: not applicable if displacement causes wetland or peatland drainage" if drains_wetlands else "Applicable",
            )
        ]

    def required_parameters(self, options: Optional[Dict[str, Any]] = None) -> List[ParameterSpec]:
        return [
            ParameterSpec("CF", "Carbon fraction of biomass", "t C / t d.m.", default_value=0.47),
            ParameterSpec("R_TREE", "Root-shoot ratio for living trees", "dimensionless", default_value=0.25),
            ParameterSpec("R_S", "Root-shoot ratio for shrubs", "dimensionless", default_value=0.40),
            ParameterSpec("dead_organic_matter_factor", "DOM expansion multiplier", "dimensionless", default_value=1.1),
        ]

    def compute(
        self,
        ctx: CalculationContext,
        inputs: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None,
    ) -> ToolResult:
        params = AR0005Params()

        # Check for zero-leakage grazing cases (a-e in para 9)
        zero_leakage_case = inputs.get("zero_leakage_grazing_case")
        if zero_leakage_case in ("a", "b", "c", "d", "e"):
            return ToolResult(
                tool_code=self.code,
                version=self.version,
                outputs={
                    "delta_C_BIOMASS_tC": 0.0,
                    "delta_SOC_LUC_tC": 0.0,
                    "LK_AGRIC_tCO2e": 0.0,
                    "zero_leakage_case": zero_leakage_case,
                },
                trace=ctx.get_trace_dict(),
                errata_applied=list(ctx.active_errata_used),
                warnings=["Zero leakage applied under grazing exemption case " + zero_leakage_case],
            )

        a_disp = inputs["A_DISP"]
        b_tree = inputs.get("b_TREE", inputs.get("b_tree", 0.0))
        b_shrub = inputs.get("b_SHRUB", inputs.get("b_shrub", 0.0))
        cf = inputs.get("CF", params.CF)
        r_tree = inputs.get("R_TREE", params.R_TREE)
        r_s = inputs.get("R_S", params.R_S)
        dom_factor = inputs.get("dom_factor", params.dead_organic_matter_factor)

        delta_c_bio = equations.displacement_biomass_loss(
            b_tree=b_tree,
            b_shrub=b_shrub,
            a_disp_ha=a_disp,
            cf=cf,
            r_tree=r_tree,
            r_s=r_s,
            dom_factor=dom_factor,
            ctx=ctx,
        )

        # Soil carbon on receiving land
        soc_ref = inputs.get("SOC_REF", 0.0)
        before = inputs.get("before", [1.0, 1.0, 1.0])
        after = inputs.get("after", [1.0, 1.0, 1.0])

        delta_soc = 0.0
        if soc_ref > 0.0:
            delta_soc = equations.displacement_soc_loss(
                soc_ref=soc_ref,
                f_lup=before[0],
                f_mgp=before[1],
                f_inp=before[2],
                f_lud=after[0],
                f_mgd=after[1],
                f_ind=after[2],
                a_disp_ha=a_disp,
                ctx=ctx,
            )

        lk_total = equations.displacement_leakage_total(delta_c_bio, delta_soc, ctx=ctx)

        outputs = {
            "delta_C_BIOMASS_tC": delta_c_bio,
            "delta_SOC_LUC_tC": delta_soc,
            "LK_AGRIC_tCO2e": lk_total,
        }

        return ToolResult(
            tool_code=self.code,
            version=self.version,
            outputs=outputs,
            trace=ctx.get_trace_dict(),
            errata_applied=list(ctx.active_errata_used),
            warnings=list(ctx.warnings),
        )
