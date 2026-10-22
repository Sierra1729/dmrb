"""BM-T-AR-0003 Tool Plugin implementation."""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from dmrv_core.equations import CalculationContext
from dmrv_core.plugin import ApplicabilityResult, ParameterSpec, ToolPlugin, ToolResult
from methodologies.tools.bm_t_ar_0003 import equations
from methodologies.tools.bm_t_ar_0003.params import AR0003Params


class BMTAR0003Tool(ToolPlugin):
    code: str = "BM-T-AR-0003"
    version: str = "1.0"
    status: Literal["APPROVED", "DRAFT"] = "APPROVED"

    def applicability(self, ctx: CalculationContext, inputs: Dict[str, Any]) -> List[ApplicabilityResult]:
        # No internal applicability exclusions in AR-0003
        return [
            ApplicabilityResult(
                criterion="Dead wood remains in situ without anthropogenic extraction",
                passed=inputs.get("deadwood_in_situ", True),
                evidence_summary="Field monitoring / PDD monitoring plan",
                reason="Default factors applicable if remains in situ",
            )
        ]

    def required_parameters(self, options: Optional[Dict[str, Any]] = None) -> List[ParameterSpec]:
        return [
            ParameterSpec("CF_TREE", "Carbon fraction of tree biomass", "t C / t d.m.", default_value=0.50),
            ParameterSpec("CF_LI", "Carbon fraction of litter", "t C / t d.m.", default_value=0.37),
        ]

    def compute(
        self,
        ctx: CalculationContext,
        inputs: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None,
    ) -> ToolResult:
        method = inputs.get("method", "plot_measurements")
        params = AR0003Params()
        outputs: Dict[str, Any] = {}

        if method == "plot_measurements":
            # Standing dead trees
            standing = inputs.get("standing", {})
            b_dws = 0.0
            c_dws = 0.0
            if standing and "agb_t_dm" in standing:
                b_dws = equations.standing_dead_biomass_allometric(
                    standing["agb_t_dm"], standing["alpha"], r_j=standing.get("R_j", 0.25), ctx=ctx
                )
                c_dws = equations.standing_dead_carbon(b_dws, cf_tree=params.CF_TREE, ctx=ctx)

            # Stumps
            stump = inputs.get("stump", {})
            d_mid = 0.0
            c_stump = 0.0
            if stump:
                d_mid = equations.stump_mid_diameter(
                    stump["DBH_m"], stump["H_STUMP_m"], h_dbh_m=stump.get("H_DBH_m", 1.3), ctx=ctx
                )
                c_stump = equations.stump_carbon(
                    [d_mid], [stump["H_STUMP_m"]], [stump["beta"]],
                    wood_density=inputs.get("D_j", 0.55),
                    r_j=stump.get("R_j", 0.25),
                    cf_tree=params.CF_TREE,
                    ctx=ctx,
                )

            # Lying dead wood
            lying_pieces = inputs.get("lying_pieces_cm_beta", [])
            c_dwl = 0.0
            if lying_pieces:
                diams = [p[0] for p in lying_pieces]
                betas = [p[1] for p in lying_pieces]
                c_dwl = equations.lying_dead_wood_carbon(
                    plot_area_ha=inputs["a_plot_ha"],
                    transect_length_m=inputs["L_m"],
                    wood_density=inputs["D_j"],
                    diameters_cm=diams,
                    beta_list=betas,
                    cf_tree=params.CF_TREE,
                    ctx=ctx,
                )

            outputs = {
                "C_DWL_tCO2e": c_dwl,
                "D_MID_STUMP_m": d_mid,
                "C_DW_STUMP_tCO2e": c_stump,
                "B_DW_TREE_t_dm": b_dws,
                "C_DWS_TREE_tCO2e": c_dws,
                "total_plot_dw_tCO2e": c_dwl + c_stump + c_dws,
            }

        elif method == "stratum_deadwood":
            a_i = inputs["A_i"]
            a_plot_i = inputs["A_plot_i"]
            plot_total = inputs["plot_total_tCO2e"]
            c_dw_i = equations.stratum_dead_wood_carbon(a_i, a_plot_i, plot_total, ctx=ctx)
            outputs = {"C_DW_i_tCO2e": c_dw_i}

        elif method == "litter_plot":
            c_li_p = equations.litter_plot_carbon(
                b_li_wet_kg=inputs["B_LI_wet_kg"],
                dwr=inputs["DWR"],
                plot_area_ha=inputs["A_p_ha"],
                frame_area_m2=inputs.get("a_p_m2", 0.5),
                cf_li=params.CF_LI,
                ctx=ctx,
            )
            outputs = {"C_LI_plot_tCO2e": c_li_p}

        elif method == "default_factors":
            c_tree = inputs["C_TREE_i_tCO2e"]
            df_dw = inputs.get("DF_DW_pct", 1.0)
            df_li = inputs.get("DF_LI_pct", 1.0)
            c_dw = equations.dead_wood_default_factor(c_tree, df_dw, ctx=ctx)
            c_li = equations.litter_default_factor(c_tree, df_li, ctx=ctx)
            outputs = {
                "DF_DW_pct": df_dw,
                "DF_LI_pct": df_li,
                "C_DW_i_tCO2e": c_dw,
                "C_LI_i_tCO2e": c_li,
            }

        return ToolResult(
            tool_code=self.code,
            version=self.version,
            outputs=outputs,
            trace=ctx.get_trace_dict(),
            errata_applied=list(ctx.active_errata_used),
            warnings=list(ctx.warnings),
        )
