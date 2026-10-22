"""BM-T-AR-0002 Tool Plugin implementation."""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from dmrv_core.equations import CalculationContext
from dmrv_core.plugin import ApplicabilityResult, ParameterSpec, ToolPlugin, ToolResult
from methodologies.tools.bm_t_ar_0002 import equations
from methodologies.tools.bm_t_ar_0002.errata import AR0002ErrataFlags
from methodologies.tools.bm_t_ar_0002.params import AR0002Params


class BMTAR0002Tool(ToolPlugin):
    code: str = "BM-T-AR-0002"
    version: str = "1.0"
    status: Literal["APPROVED", "DRAFT"] = "APPROVED"

    def applicability(self, ctx: CalculationContext, inputs: Dict[str, Any]) -> List[ApplicabilityResult]:
        errata = AR0002ErrataFlags()
        burn_area = inputs.get("accumulated_burnt_area_ha", 0.0)
        project_area = inputs.get("project_area_ha", 1.0)
        fraction_burnt = burn_area / project_area if project_area > 0 else 0.0

        is_5pct = fraction_burnt >= 0.05
        is_above_min_forest = burn_area >= errata.forest_min_area_ha

        return [
            ApplicabilityResult(
                criterion="Accumulated burnt area >= 5% of project area",
                passed=is_5pct,
                evidence_summary=f"Burnt fraction: {fraction_burnt * 100:.2f}%",
                reason="Account fire emissions if >= 5%, otherwise 0" if is_5pct else "Below 5% threshold: fire emissions = 0",
            ),
            ApplicabilityResult(
                criterion="Fire incidence exceeds forest definition minimum area",
                passed=is_above_min_forest,
                evidence_summary=f"Burnt area: {burn_area} ha, threshold: {errata.forest_min_area_ha} ha",
                reason="Eligible for fire accounting",
            ),
        ]

    def required_parameters(self, options: Optional[Dict[str, Any]] = None) -> List[ParameterSpec]:
        return [
            ParameterSpec("non_co2_to_co2_ratio", "Ratio of non-CO2 to CO2 from burning", "dimensionless", default_value=0.07),
            ParameterSpec("CF_TREE", "Carbon fraction of tree biomass", "t C / t d.m.", default_value=0.50),
            ParameterSpec("CF_SHRUB", "Carbon fraction of shrub biomass", "t C / t d.m.", default_value=0.50),
            ParameterSpec("BEF2_harvest", "Biomass expansion factor for harvest residues", "dimensionless", default_value=1.25),
        ]

    def compute(
        self,
        ctx: CalculationContext,
        inputs: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None,
    ) -> ToolResult:
        params = AR0002Params()
        errata = AR0002ErrataFlags()

        # Check GWP mode
        gwp_mode = ctx.get_flag("gwp_mode", errata.gwp_mode)
        if gwp_mode == "tool_as_printed":
            gwp_ch4 = params.GWP_CH4_SAR
            gwp_n2o = params.GWP_N2O_SAR
        else:
            gwp_ch4 = params.GWP_CH4_AR6
            gwp_n2o = params.GWP_N2O_AR6

        ghg_spf = 0.0
        ghg_fmf = 0.0
        ghg_ff_tree = 0.0
        ghg_ff_dom = 0.0

        # 1. Site prep
        sp_inp = inputs.get("site_prep")
        if sp_inp:
            ghg_spf = equations.site_prep_fire_emissions(
                a_spf_ha=sp_inp["A_SPF"],
                b_tree=sp_inp["b_TREE"],
                cc_shrub=sp_inp["CC_SHRUB"],
                b_forest=sp_inp["B_FOREST"],
                cf_tree=sp_inp.get("CF_TREE", params.CF_TREE),
                cf_shrub=sp_inp.get("CF_SHRUB", params.CF_SHRUB),
                bdr_sf=sp_inp.get("BDR_SF", params.BDR_SF),
                ratio_non_co2=params.non_co2_to_co2_ratio,
                ctx=ctx,
            )

        # 2. Harvest residues
        hr_inp = inputs.get("harvest_residue")
        b_harvest = 0.0
        if hr_inp:
            b_harvest = hr_inp.get("B_HARVEST")
            if b_harvest is None:
                b_harvest = equations.harvest_biomass_default(
                    b_forest=hr_inp["B_FOREST"],
                    a_fmf_ha=hr_inp["A_FMF"],
                    bef2=hr_inp.get("BEF2", params.BEF2_harvest),
                    ctx=ctx,
                )
            ghg_fmf = equations.harvest_residue_fire_emissions(
                b_harvest_t_dm=b_harvest,
                f_bl=hr_inp.get("f_BL", params.f_BL_tropical),
                cf_tree=hr_inp.get("CF", params.CF_TREE),
                ratio_non_co2=params.non_co2_to_co2_ratio,
                ctx=ctx,
            )

        # 3. Forest fire
        ff_inp = inputs.get("forest_fire")
        if ff_inp:
            ghg_ff_tree = equations.forest_fire_living_tree_emissions(
                a_burn_ha=ff_inp["A_BURN_ha"],
                b_tree_tl=ff_inp["b_TREE_tL"],
                comf=ff_inp["COMF"],
                ef_ch4_g_kg=ff_inp["EF_CH4"],
                ef_n2o_g_kg=ff_inp["EF_N2O"],
                gwp_ch4=gwp_ch4,
                gwp_n2o=gwp_n2o,
                ctx=ctx,
            )

        dom_inp = inputs.get("dom")
        if dom_inp:
            ghg_ff_dom = equations.forest_fire_dom_emissions(
                a_burn_ha=dom_inp["A_BURN"],
                c_dw_per_ha=dom_inp["c_DW_per_ha"],
                c_li_per_ha=dom_inp["c_LI_per_ha"],
                ratio_non_co2=params.non_co2_to_co2_ratio,
                ctx=ctx,
            )

        ghg_ff = ghg_ff_tree + ghg_ff_dom
        ghg_total = equations.total_biomass_burning_emissions(ghg_spf, ghg_fmf, ghg_ff, ctx=ctx)

        outputs = {
            "GHG_SPF_tCO2e": ghg_spf,
            "B_HARVEST_t_dm": b_harvest,
            "GHG_FMF_tCO2e": ghg_fmf,
            "GHG_FF_TREE_tCO2e": ghg_ff_tree,
            "GHG_FF_DOM_tCO2e": ghg_ff_dom,
            "GHG_FF_tCO2e": ghg_ff,
            "GHG_E_tCO2e": ghg_total,
        }

        return ToolResult(
            tool_code=self.code,
            version=self.version,
            outputs=outputs,
            trace=ctx.get_trace_dict(),
            errata_applied=list(ctx.active_errata_used),
            warnings=list(ctx.warnings),
        )
