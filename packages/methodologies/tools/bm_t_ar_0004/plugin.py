"""BM-T-AR-0004 Tool Plugin implementation."""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from dmrv_core.equations import CalculationContext
from dmrv_core.plugin import ApplicabilityResult, ParameterSpec, ToolPlugin, ToolResult
from dmrv_core.statistics import conservative, regression_slope_and_corr, t_two_sided
from methodologies.tools.bm_t_ar_0004 import equations
from methodologies.tools.bm_t_ar_0004.errata import AR0004ErrataFlags
from methodologies.tools.bm_t_ar_0004.params import AR0004Params


class BMTAR0004Tool(ToolPlugin):
    code: str = "BM-T-AR-0004"
    version: str = "1.0"
    status: Literal["APPROVED", "DRAFT"] = "APPROVED"

    def applicability(self, ctx: CalculationContext, inputs: Dict[str, Any]) -> List[ApplicabilityResult]:
        results: List[ApplicabilityResult] = []

        # Check proportionate crown cover applicability: mean crown cover < 6%
        if "cc_tree_bsl" in inputs:
            cc = inputs["cc_tree_bsl"]
            limit = 0.06  # 20% of 30% crown cover limit
            passed = cc < limit
            results.append(
                ApplicabilityResult(
                    criterion="Pre-project tree crown cover < 20% of national forest threshold (< 6%)",
                    passed=passed,
                    evidence_summary=f"Measured baseline crown cover: {cc * 100:.2f}%",
                    reason="Applicable for proportionate crown cover estimation" if passed else "Exceeds 6% limit",
                )
            )

        return results

    def required_parameters(self, options: Optional[Dict[str, Any]] = None) -> List[ParameterSpec]:
        return [
            ParameterSpec("CF_TREE", "Carbon fraction of tree biomass", "t C / t d.m.", default_value=0.47),
            ParameterSpec("CF_S", "Carbon fraction of shrub biomass", "t C / t d.m.", default_value=0.47),
            ParameterSpec("R_TREE_baseline", "Root-shoot ratio for baseline trees", "dimensionless", default_value=0.25),
            ParameterSpec("R_S", "Root-shoot ratio for shrubs", "dimensionless", default_value=0.40),
            ParameterSpec("BDR_SF", "Ratio of shrub biomass to forest biomass", "dimensionless", default_value=0.10),
            ParameterSpec("BEF2_ex_post", "Biomass expansion factor for ex-post living trees", "dimensionless", default_value=1.15),
        ]

    def compute(
        self,
        ctx: CalculationContext,
        inputs: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None,
    ) -> ToolResult:
        method = inputs.get("method", "stratified_sampling")
        params = AR0004Params()
        errata = AR0004ErrataFlags()
        outputs: Dict[str, Any] = {}
        uncertainty_pct: Optional[float] = None

        if method == "stratified_sampling":
            strata = inputs["strata"]  # list of dicts: {"name", "area_ha", "plot_biomass_list"}
            total_area = sum(s["area_ha"] for s in strata)
            weights = [s["area_ha"] / total_area for s in strata]

            means = []
            variances = []
            plot_counts = []
            per_stratum_res = {}

            for s, w in zip(strata, weights, strict=True):
                s_name = s["name"]
                vals = s["plot_biomass_list"]
                m = equations.stratum_mean_biomass(vals, ctx=ctx)
                v = equations.stratum_variance(vals, ctx=ctx)
                n = len(vals)
                means.append(m)
                variances.append(v)
                plot_counts.append(n)
                per_stratum_res[s_name] = {"mean": m, "s2": v, "w": w}

            b_tree = equations.stratified_mean_biomass(weights, means, ctx=ctx)
            total_plots = sum(plot_counts)
            df = total_plots - len(strata)
            t_val = t_two_sided(0.90, df)

            u_c = equations.stratified_uncertainty(weights, variances, plot_counts, b_tree, t_val, ctx=ctx)
            b_total = equations.total_biomass_from_mean(total_area, b_tree, ctx=ctx)
            c_tree = equations.carbon_stock_from_biomass(b_total, cf_tree=params.CF_TREE, ctx=ctx)

            # Apply Appendix 2 uncertainty discount if U > 10%
            half_width = u_c * c_tree
            c_tree_discounted = conservative(c_tree, half_width, scenario=ctx.scenario)

            uncertainty_pct = u_c * 100.0
            outputs = {
                "per_stratum": per_stratum_res,
                "b_TREE_t_dm_ha": b_tree,
                "t_val_df": df,
                "t_val": t_val,
                "u_C_fraction": u_c,
                "B_TREE_t_dm": b_total,
                "C_TREE_tCO2e": c_tree,
                "C_TREE_conservative_project_tCO2e": c_tree_discounted,
            }

        elif method == "double_sampling":
            sub_primary = inputs["sub_primary_biomass"]
            sub_sec = inputs["sub_secondary"]
            all_sec = inputs["all_secondary"]

            beta, rho = regression_slope_and_corr(sub_sec, sub_primary)
            mean_sec_all = float(sum(all_sec) / len(all_sec))
            mean_sec_sub = float(sum(sub_sec) / len(sub_sec))
            mean_sub_pri = float(sum(sub_primary) / len(sub_primary))
            s2_sub_pri = equations.stratum_variance(sub_primary, ctx=ctx)

            alpha = len(sub_primary) / len(all_sec)
            b_tree_i = equations.double_sampling_mean(mean_sub_pri, beta, mean_sec_all, mean_sec_sub, ctx=ctx)
            s2_i = equations.double_sampling_variance(s2_sub_pri, alpha, rho, ctx=ctx)

            outputs = {
                "rho": rho,
                "beta": beta,
                "alpha": alpha,
                "mean_secondary_all": mean_sec_all,
                "mean_secondary_sub": mean_sec_sub,
                "b_TREE_i": b_tree_i,
                "s2_i": s2_i,
            }

        elif method == "proportionate_crown_cover":
            b_forest = inputs["b_forest"]
            delta_b_forest = inputs["delta_b_forest"]
            cc = inputs["cc_tree_bsl"]
            area_ha = inputs["area_ha"]

            c_stock = equations.proportionate_crown_cover_baseline_stock(
                b_forest, cc, area_ha, cf_tree=params.CF_TREE, r_tree=params.R_TREE_baseline, ctx=ctx
            )
            delta_c = equations.proportionate_crown_cover_annual_change(
                delta_b_forest, cc, area_ha, cf_tree=params.CF_TREE, r_tree=params.R_TREE_baseline, ctx=ctx
            )
            outputs = {
                "C_TREE_BSL_tCO2e": c_stock,
                "delta_C_TREE_BSL_tCO2e_per_yr": delta_c,
            }

        elif method == "shrubs":
            strata_areas = inputs["strata_areas"]
            cc_shrubs = inputs["strata_cc_shrub"]
            b_forest = inputs["b_forest"]

            biomass_list = [
                equations.shrub_stratum_biomass(
                    b_forest, cc, bdr_sf=params.BDR_SF, shrub_cc_zero_below=errata.shrub_cc_zero_below, ctx=ctx
                )
                for cc in cc_shrubs
            ]
            c_shrub = equations.shrub_carbon_stock(
                strata_areas, biomass_list, cf_s=params.CF_S, r_s=params.R_S, ctx=ctx
            )
            outputs = {
                "C_SHRUB_tCO2e": c_shrub,
            }

        elif method == "annual_change":
            c_t1 = inputs["c_t1"]
            c_t2 = inputs["c_t2"]
            t_years = inputs["t_years"]
            delta = equations.annual_change(c_t1, c_t2, t_years, ctx=ctx)
            outputs = {
                "T_rounded_doc": round(t_years, 3),
                "delta_C_per_year": delta,
            }

        elif method == "difference_method":
            c_t1 = inputs["c_t1"]
            u1 = inputs["u1"]
            c_t2 = inputs["c_t2"]
            u2 = inputs["u2"]
            delta_c = equations.difference_of_stocks(c_t2, c_t1, ctx=ctx)
            u_delta = equations.uncertainty_difference_of_stocks(c_t1, u1, c_t2, u2, delta_c, ctx=ctx)
            outputs = {
                "delta_C": delta_c,
                "u_deltaC": u_delta,
            }

        return ToolResult(
            tool_code=self.code,
            version=self.version,
            outputs=outputs,
            uncertainty_pct=uncertainty_pct,
            trace=ctx.get_trace_dict(),
            errata_applied=list(ctx.active_errata_used),
            warnings=list(ctx.warnings),
        )
