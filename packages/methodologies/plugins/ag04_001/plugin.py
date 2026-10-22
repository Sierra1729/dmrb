"""BM AG04.001 Methodology Plugin: Methane Recovery from Livestock and Manure Management."""
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
from methodologies.plugins.ag04_001 import equations
from methodologies.plugins.ag04_001.errata import AG04001ErrataFlags
from methodologies.plugins.ag04_001.params import AG04001Params


@dataclass
class BMAG04001Plugin(MethodologyPlugin):
    code: str = "BM-AG04.001"
    version: str = "1.0"
    tools: Dict[str, str] = field(default_factory=dict)

    def applicability(self, ctx: CalculationContext, project: Dict[str, Any]) -> List[ApplicabilityResult]:
        results: List[ApplicabilityResult] = []

        # 1. Households / small farms livestock holding
        scale = project.get("project_scale", "small_farm").lower()
        is_smallholder = "small" in scale or "house" in scale
        results.append(
            ApplicabilityResult(
                criterion="Target group is households or small farms",
                passed=is_smallholder,
                evidence_summary=f"Project scale: {scale}",
                reason="Eligible smallholder scale" if is_smallholder else "Industrial / large concentrated facility outside scope",
            )
        )

        # 2. Mean annual temperature > 5 °C
        mat = float(project.get("mean_annual_temperature_c", 24.0))
        results.append(
            ApplicabilityResult(
                criterion="Mean annual temperature > 5 °C",
                passed=mat > 5.0,
                evidence_summary=f"Mean annual temperature: {mat:.1f} °C",
                reason="Adequate ambient temperature for biodigestion" if mat > 5.0 else "Temperature <= 5 °C unsuitable",
            )
        )

        # 3. Anaerobic baseline decay
        baseline_awms = project.get("baseline_manure_system", "liquid_slurry").lower()
        is_anaerobic = any(s in baseline_awms for s in ["liquid", "slurry", "deep_pit", "unmanaged_lagoon"])
        results.append(
            ApplicabilityResult(
                criterion="Manure would decay anaerobically in the baseline scenario",
                passed=is_anaerobic,
                evidence_summary=f"Baseline manure management: {baseline_awms}",
                reason="Baseline methane generation demonstrated" if is_anaerobic else "Aerobic baseline system ineligible",
            )
        )

        # 4. Aerobic handling of digestate
        digestate_aerobic = project.get("digestate_handled_aerobically", True)
        results.append(
            ApplicabilityResult(
                criterion="Residual digestate is handled and applied aerobically",
                passed=digestate_aerobic,
                evidence_summary=f"Digestate aerobic application confirmed: {digestate_aerobic}",
                reason="No post-digestion anaerobic emissions" if digestate_aerobic else "Anaerobic digestate handling requires BM-T-008",
            )
        )

        return results

    def required_parameters(self) -> List[ParameterSpec]:
        return [
            ParameterSpec("UF_b", "Net-to-gross adjustment factor", "dimensionless", default_value=0.89),
            ParameterSpec("GWP_CH4", "Global warming potential of methane", "t CO2e / t CH4", default_value=29.8),
            ParameterSpec("leakage_rate", "Physical leakage rate from digesters", "dimensionless", default_value=0.10),
        ]

    def ex_ante(
        self,
        ctx: CalculationContext,
        project: Dict[str, Any],
        scenario_inputs: Dict[str, Any],
    ) -> MethodologyResult:
        params = AG04001Params()
        years = scenario_inputs.get("years", [2026])
        n_animals = scenario_inputs.get("num_animals", [100.0])
        masses = scenario_inputs.get("animal_mass_kg", [350.0])
        vs_rates = scenario_inputs.get("vs_rates", [5.1])
        b0_values = scenario_inputs.get("b0_values", [0.24])
        mcfs = scenario_inputs.get("mcf_pct", [20.0])
        ms_fracs = scenario_inputs.get("ms_fractions", [1.0])
        operating_frac = float(scenario_inputs.get("operating_fraction", 0.90))

        be_y = equations.baseline_manure_emissions(
            num_animals=n_animals,
            animal_mass_kg=masses,
            vs_rate_kg_per_1000kg_day=vs_rates,
            b0_m3_kg_vs=b0_values,
            mcf_pct=mcfs,
            ms_fraction=ms_fracs,
            uf_b=params.uf_b_conservative,
            ctx=ctx,
        )

        pe_pl = equations.project_physical_leakage(
            num_animals_fed=n_animals,
            animal_mass_kg=masses,
            vs_rate_kg_per_1000kg_day=vs_rates,
            b0_m3_kg_vs=b0_values,
            mcf_pct=mcfs,
            ms_fraction=ms_fracs,
            leakage_fraction=params.physical_leakage_rate,
            ctx=ctx,
        )

        net_er = equations.net_emission_reductions_manure(
            baseline_emissions_tco2e=be_y,
            operating_fraction=operating_frac,
            pe_leakage_tco2e=pe_pl,
            ctx=ctx,
        )

        annual_results = [
            AnnualResult(
                year=y,
                baseline_emissions=be_y,
                project_emissions=pe_pl,
                net_credits=net_er,
            )
            for y in years
        ]

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
        params = AG04001Params()
        year = int(period_data.get("year", 2026))

        # Baseline potential
        n_animals = period_data.get("num_animals", [100.0])
        masses = period_data.get("animal_mass_kg", [350.0])
        vs_rates = period_data.get("vs_rates", [5.1])
        b0_values = period_data.get("b0_values", [0.24])
        mcfs = period_data.get("mcf_pct", [20.0])
        ms_fracs = period_data.get("ms_fractions", [1.0])
        operating_frac = float(period_data.get("operating_fraction", 0.90))

        be_y = equations.baseline_manure_emissions(
            num_animals=n_animals,
            animal_mass_kg=masses,
            vs_rate_kg_per_1000kg_day=vs_rates,
            b0_m3_kg_vs=b0_values,
            mcf_pct=mcfs,
            ms_fraction=ms_fracs,
            uf_b=params.uf_b_conservative,
            ctx=ctx,
        )

        pe_pl = equations.project_physical_leakage(
            num_animals_fed=n_animals,
            animal_mass_kg=masses,
            vs_rate_kg_per_1000kg_day=vs_rates,
            b0_m3_kg_vs=b0_values,
            mcf_pct=mcfs,
            ms_fraction=ms_fracs,
            leakage_fraction=params.physical_leakage_rate,
            ctx=ctx,
        )

        pe_fc = float(period_data.get("pe_fossil_fuel_tco2e", 0.0))
        pe_ec = float(period_data.get("pe_electricity_tco2e", 0.0))
        pe_y = pe_pl + pe_fc + pe_ec

        # Metered combustion MD_y if available
        md_y = None
        if "biogas_combusted_m3_per_digester" in period_data:
            n_comm = period_data.get("n_commissioned", [50.0])
            n_ops = period_data.get("digester_operating_fractions", [operating_frac])
            bs_m3 = period_data["biogas_combusted_m3_per_digester"]
            w_ch4 = period_data.get("methane_fractions", [0.60])

            md_y = equations.methane_combusted_digesters(
                n_commissioned=n_comm,
                operating_fraction=n_ops,
                biogas_combusted_m3_per_digester=bs_m3,
                methane_fraction=w_ch4,
                uf_b=params.uf_b_conservative,
                ctx=ctx,
            )

        net_er = equations.net_emission_reductions_manure(
            baseline_emissions_tco2e=be_y,
            operating_fraction=operating_frac,
            pe_leakage_tco2e=pe_pl,
            pe_fossil_fuel_tco2e=pe_fc,
            pe_electricity_tco2e=pe_ec,
            methane_combusted_tco2e=md_y,
            leakage_tco2e=float(period_data.get("leakage_tco2e", 0.0)),
            ctx=ctx,
        )

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


__all__ = ["BMAG04001Plugin"]
