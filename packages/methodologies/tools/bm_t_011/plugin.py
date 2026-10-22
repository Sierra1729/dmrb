"""BM-T-011 Tool Plugin implementation."""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from dmrv_core.equations import CalculationContext
from dmrv_core.plugin import ApplicabilityResult, ParameterSpec, ToolPlugin, ToolResult
from methodologies.tools.bm_t_011 import equations
from methodologies.tools.bm_t_011.errata import T011ErrataFlags
from methodologies.tools.bm_t_011.params import T011Params


class BMT011Tool(ToolPlugin):
    code: str = "BM-T-011"
    version: str = "1.0"
    status: Literal["APPROVED", "DRAFT"] = "APPROVED"

    def applicability(self, ctx: CalculationContext, inputs: Dict[str, Any]) -> List[ApplicabilityResult]:
        is_hazardous = inputs.get("is_hazardous_waste", False)
        is_stockpile = inputs.get("is_stockpile", False)
        vol_surface_ratio = inputs.get("volume_to_surface_area_ratio", 2.0)
        anaerobic_confirmed = inputs.get("anaerobic_conditions_confirmed", True)

        results = [
            ApplicabilityResult(
                criterion="Disposed waste is non-hazardous solid waste",
                passed=not is_hazardous,
                evidence_summary="Waste characterisation / permit documents",
                reason="Hazardous waste excluded from BM-T-011 scope",
            )
        ]

        if is_stockpile:
            stockpile_ok = vol_surface_ratio >= 1.5 and anaerobic_confirmed
            results.append(
                ApplicabilityResult(
                    criterion="Stockpile counts as SWDS: volume/area ratio >= 1.5 and anaerobic conditions confirmed",
                    passed=stockpile_ok,
                    evidence_summary=f"V/A ratio: {vol_surface_ratio}, Anaerobic: {anaerobic_confirmed}",
                    reason="Stockpile qualifying rules per section 1",
                )
            )

        return results

    def required_parameters(self, options: Optional[Dict[str, Any]] = None) -> List[ParameterSpec]:
        return [
            ParameterSpec("OX", "Oxidation factor for methane in top layer", "dimensionless", default_value=0.10),
            ParameterSpec("F", "Fraction of methane in SWDS gas", "dimensionless", default_value=0.50),
            ParameterSpec("DOC_f", "Fraction of DOC that decomposes", "dimensionless", default_value=0.50),
            ParameterSpec("MCF", "Methane correction factor", "dimensionless", default_value=1.0),
            ParameterSpec("GWP_CH4", "Global Warming Potential for methane", "t CO2e / t CH4", default_value=29.8),
        ]

    def compute(
        self,
        ctx: CalculationContext,
        inputs: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None,
    ) -> ToolResult:
        params = T011Params()
        errata = T011ErrataFlags()

        application = inputs.get("application", "B")
        timestep = inputs.get("timestep", "yearly")  # "yearly" or "monthly"
        gwp_ch4 = inputs.get("GWP_CH4", params.GWP_CH4_default)
        ox = inputs.get("OX", params.OX_default)
        f_param = inputs.get("F", params.F_default)
        f_y = inputs.get("f_y", 0.0)

        # 1. Determine phi_y
        phi_y = inputs.get("phi")
        if phi_y is None:
            if "phi_option2_factors" in inputs:
                factors = inputs["phi_option2_factors"]
                v_y = equations.model_uncertainty_vector(
                    factors["a"], factors["b"], factors["c"], factors["d"], factors["e"], factors["g"], ctx=ctx
                )
                phi_y = equations.model_correction_factor_option2(v_y, ctx=ctx)
            else:
                climate = inputs.get("climate", "humid")
                phi_y = params.phi_defaults.get(application, {}).get(climate, 0.85)

        # 2. Determine MCF
        mcf_val = inputs.get("MCF")
        if mcf_val is None:
            if "water_table" in inputs:
                wt = inputs["water_table"]
                mcf_val = equations.mcf_water_table(wt["d_y_m"], wt["h_w_y_m"], ctx=ctx)
            else:
                swds_type = inputs.get("swds_type", "anaerobic_managed")
                mcf_val = params.mcf_defaults.get(swds_type, 1.0)

        # 3. Determine DOC_f
        doc_f_val = inputs.get("DOC_f")
        if doc_f_val is None:
            if "bmp_test" in inputs:
                bmp = inputs["bmp_test"]
                doc_f_res = equations.doc_f_from_bmp_msw(
                    bmp_msw_t_ch4_per_t=bmp["BMP_MSW_tCH4_per_t"],
                    f_param=f_param,
                    p_j=bmp["p_j"],
                    doc_j=bmp.get("doc_j"),
                    ctx=ctx,
                )
                doc_f_val = doc_f_res["DOC_f_y"]
            else:
                doc_f_val = params.DOC_f_default

        # 4. Resolve DOC_j and k_j
        doc_j = inputs.get("doc_j") or {}
        k_j = inputs.get("k_j") or {}
        if "DOC_k" in inputs:
            for k, pair in inputs["DOC_k"].items():
                doc_j[k] = pair[0]
                k_j[k] = pair[1]

        # 5. Execute FOD model
        if timestep == "yearly":
            # Build annual waste streams: list of dicts {waste_type: tonnes}
            waste_streams = []
            if "waste_streams" in inputs:
                waste_streams = inputs["waste_streams"]
            elif "W_x_t_per_year" in inputs and "composition" in inputs:
                w_tot = float(inputs["W_x_t_per_year"])
                comp = inputs["composition"]
                # If years_disposed is 10
                n_yrs = inputs.get("n_years", 10)
                cohort = {j: w_tot * frac for j, frac in comp.items()}
                waste_streams = [cohort] * n_yrs

            emissions_series = equations.yearly_fod_emissions(
                phi_y=phi_y,
                f_y=f_y,
                gwp_ch4=gwp_ch4,
                ox=ox,
                f_param=f_param,
                doc_f_y=doc_f_val,
                mcf_y=mcf_val,
                waste_streams=waste_streams,
                doc_j=doc_j,
                k_j=k_j,
                ctx=ctx,
            )
            outputs = {
                "phi_y": phi_y,
                "MCF_y": mcf_val,
                "DOC_f_y": doc_f_val,
                "BE_CH4_SWDS_tCO2e_y1_to_y10": emissions_series,
                "emissions_by_year_tCO2e": emissions_series,
                "total_emissions_tCO2e": sum(emissions_series),
            }
        else:
            # Monthly model
            monthly_streams = inputs.get("monthly_waste_streams", [])
            emissions_series = equations.monthly_fod_emissions(
                phi_y=phi_y,
                f_y=f_y,
                gwp_ch4=gwp_ch4,
                ox=ox,
                f_param=f_param,
                doc_f_m=doc_f_val,
                mcf_y=mcf_val,
                monthly_waste_streams=monthly_streams,
                doc_j=doc_j,
                k_j=k_j,
                ctx=ctx,
            )
            outputs = {
                "phi_y": phi_y,
                "MCF_y": mcf_val,
                "DOC_f_m": doc_f_val,
                "emissions_by_month_tCO2e": emissions_series,
                "total_emissions_tCO2e": sum(emissions_series),
            }

        return ToolResult(
            tool_code=self.code,
            version=self.version,
            outputs=outputs,
            trace=ctx.get_trace_dict(),
            errata_applied=list(ctx.active_errata_used),
            warnings=list(ctx.warnings),
        )


__all__ = ["BMT011Tool"]
