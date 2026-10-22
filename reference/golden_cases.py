"""
Golden reference cases for the dMRV calculation engine.

PURPOSE
    Independent, minimal re-implementation of the equations in /specs, used ONLY to
    generate expected values for the engine's test suite (tests/golden/*.json).
    The production engine must NOT import this file. It must reproduce these numbers
    with its own implementation to within the tolerance stated in each case.

RUN
    python -I reference/golden_cases.py            # prints all cases
    python -I reference/golden_cases.py --json out.json

CONVENTIONS
    * Every case cites the source tool, equation number and PDF page.
    * Inputs are deliberately simple so a reviewer can check them by hand.
    * Default tolerance: relative 1e-9 (pure arithmetic) unless stated.
"""
from __future__ import annotations

import json
import math
import sys

from scipy import stats

C_TO_CO2 = 44.0 / 12.0
CASES: dict[str, dict] = {}


def case(name: str, source: str, inputs: dict, outputs: dict, tol: float = 1e-9, note: str = ""):
    CASES[name] = {"source": source, "inputs": inputs, "expected": outputs, "rel_tol": tol, "note": note}


# ---------------------------------------------------------------------------
# Shared statistics
# ---------------------------------------------------------------------------
def t_two_sided_90(df: int) -> float:
    """Two-sided Student t at 90 % confidence == one-sided 95 % quantile."""
    return float(stats.t.ppf(0.95, df))


def uncertainty_discount_fraction(u_pct: float) -> float:
    """BM-T-AR-0004 Appendix 2, Table 1. Returns discount as fraction of the half-width."""
    if u_pct <= 10:
        return 0.0
    if u_pct <= 15:
        return 0.25
    if u_pct <= 20:
        return 0.50
    if u_pct <= 30:
        return 0.75
    return 1.00


def apply_discount(mean: float, half_width: float, scenario: str) -> float:
    u = half_width / mean * 100.0
    d = uncertainty_discount_fraction(u) * half_width
    return mean + d if scenario == "baseline" else mean - d


# ---------------------------------------------------------------------------
# BM-T-AR-0004  Trees and shrubs
# ---------------------------------------------------------------------------
# Definition example, section 2 para 4 (PDF p.4)
n, mean, sd = 34, 45.328, 12.776
sem = sd / math.sqrt(n)
tval = t_two_sided_90(n - 1)
u_pct = sem * tval / mean * 100
case(
    "AR0004_uncertainty_definition_example",
    "BM-T-AR-0004 v1.0, section 2 para 4 (PDF p.4)",
    {"n": n, "mean_t_dm_ha": mean, "sd_t_dm_ha": sd},
    {"sem": round(sem, 3), "t_0.1_33": round(tval, 3), "uncertainty_pct": round(u_pct, 2)},
    tol=1e-3,
    note="Document prints SEM 2.191, t 1.692, U 8.18 %.",
)

# Appendix 2 discount example (PDF p.29): 60 +/- 9
case(
    "AR0004_discount_example",
    "BM-T-AR-0004 v1.0, Appendix 2 Table 1 (PDF p.29)",
    {"mean": 60.0, "half_width_90": 9.0},
    {"U_pct": 15.0, "discount_fraction": 0.25,
     "baseline_conservative": apply_discount(60, 9, "baseline"),
     "project_conservative": apply_discount(60, 9, "project")},
    note="Document prints 62.25 (baseline) and 57.75 (project). Boundary: 10<U<=15 -> 25 %.",
)

# Root-shoot ratio function (Appendix 1, eq. for R_j; also BM-T-AR-0003 DPT7)
def root_shoot(b_ag: float) -> float:
    return math.exp(-1.085 + 0.9256 * math.log(b_ag)) / b_ag


case(
    "AR0004_root_shoot_function",
    "BM-T-AR-0004 v1.0, Appendix 1 (PDF p.26); BM-T-AR-0003 DPT 7",
    {"b_above_ground_t_dm_ha": [10.0, 50.0, 150.0]},
    {"R": [root_shoot(10.0), root_shoot(50.0), root_shoot(150.0)]},
)

# Stratified random sampling, Eq. 12-17 (PDF p.14-15). Two strata.
strata = {
    "S1": {"area_ha": 60.0, "plots_b": [40.0, 44.0, 52.0, 48.0, 36.0]},
    "S2": {"area_ha": 40.0, "plots_b": [20.0, 26.0, 23.0, 31.0]},
}
A = sum(s["area_ha"] for s in strata.values())
M = len(strata)
n_tot = sum(len(s["plots_b"]) for s in strata.values())
b_tree = 0.0
var_term = 0.0
per = {}
for k, s in strata.items():
    x = s["plots_b"]
    ni = len(x)
    mean_i = sum(x) / ni
    s2_i = (ni * sum(v * v for v in x) - sum(x) ** 2) / (ni * (ni - 1))  # Eq.17
    w = s["area_ha"] / A
    b_tree += w * mean_i  # Eq.14
    var_term += w * w * s2_i / ni
    per[k] = {"mean": mean_i, "s2": s2_i, "w": w}
tv = t_two_sided_90(n_tot - M)
uc = tv * math.sqrt(var_term) / b_tree  # Eq.15
B_TREE = A * b_tree  # Eq.13
CF = 0.47
C_TREE = C_TO_CO2 * CF * B_TREE  # Eq.12
half_width_b = uc * b_tree
b_cons = apply_discount(b_tree, half_width_b, "project")
case(
    "AR0004_stratified_random_sampling",
    "BM-T-AR-0004 v1.0, Eq. 12-17 + Appendix 2 (PDF p.14-15, 29)",
    {"strata": strata, "CF_TREE": CF},
    {"per_stratum": per, "b_TREE_t_dm_ha": b_tree, "t_val_df": n_tot - M, "t_val": tv,
     "u_C_fraction": uc, "B_TREE_t_dm": B_TREE, "C_TREE_tCO2e": C_TREE,
     "C_TREE_conservative_project_tCO2e": C_TO_CO2 * CF * A * b_cons},
    note="u_C is a fraction; >10 % triggers Appendix-2 discount. The discount is applied to the mean"
         " (equivalently to C_TREE) using the same half-width.",
)

# Double sampling, Eq. 18-19 + Appendix 3 (PDF p.16-17, 30)
sub_b = [30.0, 42.0, 55.0, 61.0, 38.0, 47.0]  # plot biomass in sub-sample
sub_x = [0.40, 0.52, 0.66, 0.74, 0.47, 0.58]  # secondary variable (e.g. NDVI) in sub-sample
all_x = sub_x + [0.45, 0.50, 0.70, 0.62, 0.55, 0.48, 0.60, 0.68, 0.43, 0.57, 0.51, 0.64]
n_sub = len(sub_b)
mx_sub = sum(sub_x) / n_sub
my_sub = sum(sub_b) / n_sub
mx_all = sum(all_x) / len(all_x)
sxy = sum((a - mx_sub) * (b - my_sub) for a, b in zip(sub_x, sub_b))
sxx = sum((a - mx_sub) ** 2 for a in sub_x)
syy = sum((b - my_sub) ** 2 for b in sub_b)
rho = sxy / math.sqrt(sxx * syy)  # App.3 Eq.2
s_y = math.sqrt(syy / (n_sub - 1))
s_x = math.sqrt(sxx / (n_sub - 1))
beta = rho * s_y / s_x  # App.3 Eq.1
alpha = n_sub / len(all_x)
b_ds = my_sub + beta * (mx_all - mx_sub)  # Eq.18 (x-bar' = all plots, x-bar = sub-sample)
s2_ds = (n_sub * sum(v * v for v in sub_b) - sum(sub_b) ** 2) / (n_sub * (n_sub - 1)) * (1 - (1 - alpha) * rho ** 2)
case(
    "AR0004_double_sampling",
    "BM-T-AR-0004 v1.0, Eq. 18-19, Appendix 3 (PDF p.16-17, 30)",
    {"sub_sample_biomass": sub_b, "sub_sample_secondary": sub_x, "all_plots_secondary": all_x},
    {"rho": rho, "beta": beta, "alpha": alpha, "mean_secondary_all": mx_all,
     "mean_secondary_sub": mx_sub, "b_TREE_i": b_ds, "s2_i": s2_ds},
    note="Eq.19 result s2_i is then used in Eq.15 as s_i^2 / n_i with n_i = sub-sample size.",
)

# Proportionate crown cover (baseline stock), Eq. 20-21 (PDF p.18)
pcc = {"CF": 0.47, "b_FOREST": 120.0, "R_TREE": 0.25, "strata": [{"CC": 0.04, "A": 25.0}, {"CC": 0.02, "A": 15.0}]}
c_bsl = sum(C_TO_CO2 * pcc["CF"] * pcc["b_FOREST"] * (1 + pcc["R_TREE"]) * s["CC"] * s["A"] for s in pcc["strata"])
d_bsl = sum(C_TO_CO2 * pcc["CF"] * 3.0 * (1 + pcc["R_TREE"]) * s["CC"] * s["A"] for s in pcc["strata"])
case(
    "AR0004_proportionate_crown_cover",
    "BM-T-AR-0004 v1.0, Eq. 9-10 (change) and Eq. 20-21 (stock) (PDF p.12, 18)",
    {**pcc, "delta_b_FOREST_t_dm_ha_yr": 3.0, "threshold_rule": "mean pre-project CC < 0.20 x 0.30 = 0.06"},
    {"C_TREE_BSL_tCO2e": c_bsl, "delta_C_TREE_BSL_tCO2e_per_yr": d_bsl},
)

# Shrubs, Eq. 26-27 (PDF p.20)
sh = {"CF_S": 0.47, "R_S": 0.40, "BDR_SF": 0.10, "b_FOREST": 120.0,
      "strata": [{"CC": 0.30, "A": 20.0}, {"CC": 0.04, "A": 10.0}]}
c_sh = C_TO_CO2 * sh["CF_S"] * (1 + sh["R_S"]) * sum(
    s["A"] * sh["BDR_SF"] * sh["b_FOREST"] * s["CC"] for s in sh["strata"] if s["CC"] >= 0.05)
case(
    "AR0004_shrubs",
    "BM-T-AR-0004 v1.0, Eq. 26-27, para 67-68 (PDF p.20)",
    sh,
    {"C_SHRUB_tCO2e": c_sh},
    note="Stratum with CC < 5 % is set to zero (para 67). Para 68 says 'greater than 5 %'; exactly 5 % is"
         " treated as non-zero here (see errata E-AR4-06).",
)

# Annual change, Eq. 11 with fractional T (PDF p.13)
case(
    "AR0004_annual_change_fractional_T",
    "BM-T-AR-0004 v1.0, Eq. 11 (PDF p.13)",
    {"C_t1": 1200.0, "C_t2": 2525.0, "T_years": 4 + 5 / 12},
    {"T_rounded_doc": 4.417, "delta_C_per_year": (2525.0 - 1200.0) / (4 + 5 / 12)},
)

# Change uncertainty, Eq. 1-2 and Eq. 22-23
c1, c2, u1, u2 = 1200.0, 2525.0, 0.08, 0.12
dC = c2 - c1
u_dc = math.sqrt((u1 * c1) ** 2 + (u2 * c2) ** 2) / abs(dC)
case(
    "AR0004_difference_method_uncertainty",
    "BM-T-AR-0004 v1.0, Eq. 1-2 (PDF p.7)",
    {"C_t1": c1, "C_t2": c2, "u1": u1, "u2": u2},
    {"delta_C": dC, "u_deltaC": u_dc},
)

# ---------------------------------------------------------------------------
# BM-T-AR-0003  Dead wood and litter
# ---------------------------------------------------------------------------
CF_T = 0.5  # tool default (DPT 2)
# Lying dead wood Eq. 6
a_plot, Dj, L = 0.05, 0.55, 100.0
pieces = [(12.0, 1.00), (15.0, 0.80), (22.0, 0.45)]  # (diameter cm, beta)
c_dwl = a_plot * C_TO_CO2 * CF_T * Dj * (math.pi ** 2 / (8 * L)) * sum(d * d * b for d, b in pieces)
# Stump Eq. 4-5 (stump >= 4 m: mid-height diameter from DBH)
dbh, h_stump, h_dbh = 0.30, 5.0, 1.3
d_mid = 0.57 * dbh * (h_stump / (h_stump - h_dbh)) ** 0.80
R = 0.25
c_stump = C_TO_CO2 * CF_T * Dj * (1 + R) * math.pi / 4 * (d_mid ** 2 * h_stump * 0.80)
# Standing dead tree, allometric Eq. 2-3 (AGB from allometry supplied, t d.m.)
agb = [0.35, 0.60]
alpha_k = [0.975, 0.80]
b_dw_tree = (1 + R) * sum(a * k for a, k in zip(agb, alpha_k))
c_dws = C_TO_CO2 * CF_T * b_dw_tree
case(
    "AR0003_deadwood_plot",
    "BM-T-AR-0003 v1.0, Eq. 2-6 (PDF p.6-9)",
    {"a_plot_ha": a_plot, "D_j": Dj, "L_m": L, "lying_pieces_cm_beta": pieces, "CF_TREE": CF_T,
     "stump": {"DBH_m": dbh, "H_STUMP_m": h_stump, "H_DBH_m": h_dbh, "beta": 0.80, "R_j": R},
     "standing": {"agb_t_dm": agb, "alpha": alpha_k, "R_j": R}},
    {"C_DWL_tCO2e": c_dwl, "D_MID_STUMP_m": d_mid, "C_DW_STUMP_tCO2e": c_stump,
     "B_DW_TREE_t_dm": b_dw_tree, "C_DWS_TREE_tCO2e": c_dws},
    note="Eq.1 as printed shows (1+D_j); implement (1+R_j) (errata E-AR3-01). Eq.4 precedence:"
         " H/(H - H_DBH) (errata E-AR3-02).",
)
# Stratum scaling Eq. 7
A_i, A_plot_i = 50.0, 0.05
case(
    "AR0003_deadwood_stratum",
    "BM-T-AR-0003 v1.0, Eq. 7 (PDF p.9)",
    {"A_i": A_i, "A_plot_i": A_plot_i, "plot_total_tCO2e": c_dwl + c_stump + c_dws},
    {"C_DW_i_tCO2e": A_i / A_plot_i * (c_dwl + c_stump + c_dws)},
)
# Litter Eq. 12-13
B_wet, DWR, A_p, a_p = 2.0, 0.40, 0.05, 0.50
c_lp = C_TO_CO2 * 0.37 * 2.5 * (A_p / a_p) * B_wet * DWR
case(
    "AR0003_litter_plot",
    "BM-T-AR-0003 v1.0, Eq. 12 (PDF p.12)",
    {"B_LI_wet_kg": B_wet, "DWR": DWR, "A_p_ha": A_p, "a_p_m2": a_p, "CF_LI": 0.37},
    {"C_LI_plot_tCO2e": c_lp},
    note="2.5 = (10 000 m2/ha / 1 000 kg/t) / 4 frames.",
)
# Default factor method Eq. 9 / 15
case(
    "AR0003_default_factors",
    "BM-T-AR-0003 v1.0, Eq. 9, 15, DPT 5-6 (PDF p.10, 13, 15-16)",
    {"C_TREE_i_tCO2e": 5000.0, "biome": "Tropical", "elevation": "<2000m", "precip": "1000-1600"},
    {"DF_DW_pct": 1, "DF_LI_pct": 1, "C_DW_i_tCO2e": 5000.0 * 0.01, "C_LI_i_tCO2e": 5000.0 * 0.01},
    note="DF values are printed in per cent; divide by 100.",
)

# ---------------------------------------------------------------------------
# BM-T-AR-0002  Non-CO2 from burning
# ---------------------------------------------------------------------------
gwp_tool = {"CH4": 21.0, "N2O": 310.0}
gwp_ar6 = {"CH4": 29.8, "N2O": 273.0}
ff = {"A_BURN_ha": 10.0, "b_TREE_tL": 80.0, "COMF": 0.46, "EF_CH4": 6.8, "EF_N2O": 0.20}
def ff_tree(g):
    return 0.001 * ff["A_BURN_ha"] * ff["b_TREE_tL"] * ff["COMF"] * (ff["EF_CH4"] * g["CH4"] + ff["EF_N2O"] * g["N2O"])
spf = {"A_SPF": 12.0, "CF_TREE": 0.50, "b_TREE": 5.0, "BDR_SF": 0.10, "CF_SHRUB": 0.50, "CC_SHRUB": 0.30, "B_FOREST": 120.0}
ghg_spf = 0.07 * spf["A_SPF"] * C_TO_CO2 * (spf["CF_TREE"] * spf["b_TREE"] + spf["BDR_SF"] * spf["CF_SHRUB"] * spf["CC_SHRUB"] * spf["B_FOREST"])
b_harv = 120.0 / 1.25 * 8.0
ghg_fmf = 0.07 * C_TO_CO2 * b_harv * 0.25 * 0.50
dom = {"A_BURN": 10.0, "c_DW_per_ha": 6.0, "c_LI_per_ha": 4.0}
ghg_dom = 0.07 * dom["A_BURN"] * (dom["c_DW_per_ha"] + dom["c_LI_per_ha"])
case(
    "AR0002_fire_components",
    "BM-T-AR-0002 v1.0, Eq. 3, 4, 5, 7, 8 (PDF p.4-8)",
    {"forest_fire": ff, "site_prep": spf, "harvest_residue": {"B_FOREST": 120.0, "BEF2": 1.25, "A_FMF": 8.0, "f_BL": 0.25, "CF": 0.5},
     "dom": dom},
    {"GHG_FF_TREE_tool_GWP_tCO2e": ff_tree(gwp_tool), "GHG_FF_TREE_AR6_GWP_tCO2e": ff_tree(gwp_ar6),
     "GHG_SPF_tCO2e": ghg_spf, "B_HARVEST_t_dm": b_harv, "GHG_FMF_tCO2e": ghg_fmf, "GHG_FF_DOM_tCO2e": ghg_dom},
    note="Tool prints GWP 21/310; CCTS Detailed Procedure requires latest IPCC GWP100 (see errata E-GWP-01)."
         " DOM stocks must be per-hectare (errata E-AR2-03).",
)

# ---------------------------------------------------------------------------
# BM-T-AR-0005  Leakage, displacement of agriculture
# ---------------------------------------------------------------------------
lk = {"b_TREE": 30.0, "R_TREE": 0.25, "b_SHRUB": 4.0, "R_S": 0.40, "CF": 0.47, "A_DISP": 15.0,
      "SOC_REF": 47.0, "before": (1.0, 0.97, 1.0), "after": (0.48, 1.00, 0.92)}
dcb = (1.1 * lk["b_TREE"] * (1 + lk["R_TREE"]) + lk["b_SHRUB"] * (1 + lk["R_S"])) * lk["CF"] * lk["A_DISP"]
dsoc = lk["SOC_REF"] * (math.prod(lk["before"]) - math.prod(lk["after"])) * lk["A_DISP"]
dsoc = max(dsoc, 0.0)
case(
    "AR0005_leakage_displacement",
    "BM-T-AR-0005 v1.0, Eq. 1-3 (PDF p.4-6)",
    lk,
    {"delta_C_BIOMASS_tC": dcb, "delta_SOC_LUC_tC": dsoc, "LK_AGRIC_tCO2e": C_TO_CO2 * (dcb + dsoc)},
    note="Receiving land: moderately degraded tropical grassland (fLU 1, fMG 0.97, fIN 1) converted to"
         " long-term cultivated tropical moist cropland, full tillage, low input. Eq.2 multiplies by CF, so"
         " its unit is t C, not t d.m. as printed (errata E-AR5-01).",
)

# ---------------------------------------------------------------------------
# BM-T-AR-0006  SOC in A/R
# ---------------------------------------------------------------------------
def ar_soc_rates(soc_ref, f_lu, f_mg, f_in, disturbed_gt_10pct, t_prep, years):
    soc_init = soc_ref * f_lu * f_mg * f_in
    loss = soc_init * 0.1 if disturbed_gt_10pct else 0.0
    out = []
    for t in years:
        if t < t_prep:
            r = 0.0
        elif t == t_prep:
            r = -loss
        elif t <= t_prep + 20:
            r = (soc_ref - (soc_init - loss)) / 20.0
            r = min(r, 0.8)  # Eq.7 cap
        else:
            r = 0.0
        out.append(r)
    return soc_init, loss, out

si, sl, rates = ar_soc_rates(47.0, 0.48, 1.00, 0.92, True, 1, range(1, 24))
A_str = 100.0
case(
    "AR0006_soc_tropical_moist_LAC",
    "BM-T-AR-0006 v1.0, Eq. 1-8, Tables 4-6 (PDF p.4-10)",
    {"SOC_REF": 47.0, "f_LU": 0.48, "f_MG": 1.00, "f_IN": 0.92, "disturbance_gt_10pct": True, "t_PREP": 1,
     "A_i_ha": A_str},
    {"SOC_INITIAL": si, "SOC_LOSS": sl, "dSOC_by_year_t1_to_t23": rates,
     "delta_SOC_AL_tCO2e_by_year": [C_TO_CO2 * A_str * r for r in rates]},
    note="Uncapped rate = (47-(20.7552-2.07552))/20 = 1.416 -> capped at 0.8 tC/ha/yr. Rate is zero after"
         " t_PREP+20 (implicit; errata E-AR6-04).",
)

# ---------------------------------------------------------------------------
# BM-T-011  SWDS first-order decay
# ---------------------------------------------------------------------------
WASTE = {  # j: (DOC_j wet, k tropical wet MAP>1000)
    "food": (0.15, 0.40), "paper_cardboard": (0.40, 0.07), "garden": (0.20, 0.17), "wood": (0.43, 0.035), "inert": (0.0, 0.0),
}
comp = {"food": 0.55, "paper_cardboard": 0.12, "garden": 0.10, "wood": 0.03, "inert": 0.20}
W_x = 10_000.0  # t/yr wet
def fod_year(y, phi, f, gwp, ox, F, docf, mcf):
    s = 0.0
    for x in range(1, y + 1):
        for j, (doc, k) in WASTE.items():
            wjx = W_x * comp[j]
            if doc == 0:
                continue
            s += wjx * doc * math.exp(-k * (y - x)) * (1 - math.exp(-k))
    return phi * (1 - f) * gwp * (1 - ox) * (16 / 12) * F * docf * mcf * s

be = [fod_year(y, 0.85, 0.0, 29.8, 0.1, 0.5, 0.5, 1.0) for y in range(1, 11)]
case(
    "T011_FOD_applicationB_MSW_yearly",
    "BM-T-011 v1.0, Eq. 1 + default tables (PDF p.5, 14-20)",
    {"W_x_t_per_year": W_x, "years_disposed": "x = 1..y (constant stream)", "composition": comp,
     "DOC_k": WASTE, "phi": 0.85, "f_y": 0.0, "GWP_CH4": 29.8, "OX": 0.1, "F": 0.5, "DOC_f": 0.5, "MCF": 1.0},
    {"BE_CH4_SWDS_tCO2e_y1_to_y10": be},
    tol=1e-9,
    note="Application B, baseline, humid tropical (phi_default 0.85), anaerobic managed SWDS (MCF 1.0)."
         " GWP from CCTS rule (latest IPCC GWP100; BEE methodologies use 29.8).",
)
# phi option 2
abcdeg = {"a": 0.02, "b": 0.10, "c": 0.05, "d": 0.00, "e": 0.00, "g": 0.20}
V = math.sqrt(sum(v * v for v in abcdeg.values()))
case(
    "T011_phi_option2",
    "BM-T-011 v1.0, Eq. 3-4, Table 3 (PDF p.8-9)",
    abcdeg,
    {"V_y": V, "phi_y": 1 / (1 + V)},
    note="Eq.4 printed as 'phi=1(1+V)'; implemented as 1/(1+V) (errata E-T11-02).",
)
# MCF with water table, Eq.12
case(
    "T011_MCF_water_table",
    "BM-T-011 v1.0, Eq. 12 (PDF p.14)",
    {"d_y_m": 10.0, "h_w_y_m": 3.0},
    {"MCF_y": max(1 - 2 / 10.0, 3.0 / 10.0)},
)
# DOCf from BMP, Eq.9
pj = {"food": 0.55, "paper_cardboard": 0.12, "garden": 0.10, "wood": 0.03, "inert": 0.20}
sum_pdoc = sum(pj[j] * WASTE[j][0] for j in pj)
case(
    "T011_DOCf_from_BMP",
    "BM-T-011 v1.0, Eq. 9 (PDF p.12)",
    {"BMP_MSW_tCH4_per_t": 0.035, "F": 0.5, "p_j": pj},
    {"sum_p_DOC": sum_pdoc, "DOC_f_y": 0.7 * 12 / 16 * 0.035 / (0.5 * sum_pdoc)},
)

# ---------------------------------------------------------------------------
# DRAFT SOC Model Guidelines: validation metrics (Table 3, Eq. 12-25)
# ---------------------------------------------------------------------------
obs = [42.1, 55.3, 38.7, 61.2, 47.5, 50.9, 44.0, 58.6, 39.9, 52.4, 46.8, 49.1, 57.0, 41.3, 53.8,
       45.2, 60.1, 48.4, 43.6, 51.7]
pred = [44.0, 53.1, 40.2, 58.9, 49.0, 49.5, 45.8, 56.0, 42.3, 51.0, 47.9, 50.2, 55.1, 43.0, 52.6,
        46.1, 57.7, 47.3, 45.5, 50.3]
lo = [p - 2.5 for p in pred]
hi = [p + 2.5 for p in pred]
nn = len(obs)
xbar = sum(obs) / nn
xhat_bar = sum(pred) / nn
s2 = sum((x - xbar) ** 2 for x in obs) / (nn - 1)
s = math.sqrt(s2)
resid = [p - o for p, o in zip(pred, obs)]
bias = sum(resid) / nn
rmse = math.sqrt(sum(r * r for r in resid) / nn)
r2 = 1 - sum((p - o) ** 2 for p, o in zip(pred, obs)) / sum((xbar - o) ** 2 for o in obs)
se = math.sqrt(s2 / nn)
moe = se * t_two_sided_90(nn - 1)
ind = [1.0 if a <= o <= b else 0.0 for a, o, b in zip(lo, obs, hi)]
picp = sum(ind) / nn
s_picp = math.sqrt(sum((d - picp) ** 2 for d in ind) / (nn - 1))
t_picp = (picp - 0.9) / (s_picp / math.sqrt(nn)) if s_picp > 0 else float("inf")
case(
    "SOCMG_validation_metrics",
    "DRAFT SOC Model Requirements & Guidelines, Table 3 Eq. 12-25, paras 76-77 (PDF p.33-35)",
    {"observed_t_ha": obs, "predicted_t_ha": pred, "interval_halfwidth": 2.5},
    {"n": nn, "mean_obs": xbar, "mean_pred": xhat_bar, "s": s, "bias": bias, "rmse": rmse, "R2": r2,
     "SE": se, "MoE_90": moe, "PICP": picp, "s_PICP": s_picp, "t_PICP": t_picp,
     "pass_bias": abs(bias) <= moe, "pass_rmse": rmse < s, "pass_r2": r2 > 0},
    note="Residual sign: r_i = predicted - observed (Eq.16), so positive bias = over-estimation."
         " MoE uses two-sided 90 % t with n-1 df (Eq.21). Doc Example E1.1 shows +/-2.36 for SE 1.19,"
         " which matches 95 %, not 90 % - follow Eq.21 (errata E-SOCMG-03).",
)
# Sample size Box 5 Eq. 6/7
z = float(stats.norm.ppf(0.95))
case(
    "SOCMG_sample_size",
    "DRAFT SOC Model Guidelines Box 5 Eq. 6-7 (PDF p.26)",
    {"alpha": 0.1, "s_t_ha": 12.0, "MoE_t_ha": 2.5},
    {"z_alpha/2": z, "n_raw": z * z * 144.0 / 6.25, "n_required": math.ceil(z * z * 144.0 / 6.25)},
)
# Annex A.6 residual-trend change estimator Eq. 26-35
t_n = [2015.0] * 5 + [2020.0] * 5
e_n = [-1.2, 0.4, 0.9, -0.3, 0.1, 0.6, 1.3, -0.2, 0.8, 0.5]
N = len(e_n)
eb = sum(e_n) / N
tb = sum(t_n) / N
b1 = sum((ti - tb) * (ei - eb) for ti, ei in zip(t_n, e_n)) / sum((ti - tb) ** 2 for ti in t_n)
b0 = eb - b1 * tb
s2r = sum((ei - (b0 + b1 * ti)) ** 2 for ti, ei in zip(t_n, e_n)) / (N - 2)
mu_t, mu_tp, t0, t1 = 48.0, 50.5, 2025.0, 2030.0
mu_delta = mu_tp - mu_t + (t1 - t0) * b1
moe_d = float(stats.t.ppf(0.95, N - 2)) * math.sqrt((t1 - t0) ** 2 / sum((ti - tb) ** 2 for ti in t_n) * s2r)
case(
    "SOCMG_residual_trend_change",
    "DRAFT SOC Model Guidelines Annex A Table A.6 Eq. 26-35 (PDF p.56)",
    {"t_n": t_n, "e_n": e_n, "mu_pred_t": mu_t, "mu_pred_t_prime": mu_tp, "t": t0, "t_prime": t1},
    {"beta1": b1, "beta0": b0, "sigma2_resid": s2r, "mu_delta": mu_delta, "MoE_90": moe_d},
    note="T_{alpha/2,N-2} read as the two-sided 90 % critical value (one-sided 0.95 quantile).",
)

# ---------------------------------------------------------------------------
# DRAFT SOC activity tools: other emissions and leakage
# ---------------------------------------------------------------------------
fe = {"EF_FE_as_printed": 0.01, "FE_PR_kgN_by_year": [1200.0, 1300.0, 1250.0, 1400.0, 1350.0], "FE_BL_kgN": 1100.0}
dfe_printed = fe["EF_FE_as_printed"] * sum(v - fe["FE_BL_kgN"] for v in fe["FE_PR_kgN_by_year"])
ef_conv = 0.01 * 44 / 28 * 273 / 1000
case(
    "SOCAT_fertiliser_increase",
    "DRAFT SOC Activity Tool (cover crops) Eq. 2; zero tillage Eq. 2 (PDF p.75, 147)",
    fe,
    {"delta_FE_tCO2e_as_printed": max(0.0, dfe_printed),
     "EF_FE_IPCC_EF1_converted_tCO2e_per_kgN": ef_conv,
     "delta_FE_tCO2e_converted": max(0.0, ef_conv * sum(v - fe["FE_BL_kgN"] for v in fe["FE_PR_kgN_by_year"]))},
    note="0.01 is the IPCC EF1 in kg N2O-N per kg N, not tCO2e/kgN (errata E-SOCAT-01). Default to the"
         " printed (more conservative) value until BEE clarifies; show both in the report.",
)
lkz = {"CY_BL": 4000.0, "CY_min_prev": 3900.0, "CY_t": 3700.0, "A_bar": 120.0,
       "dBC_LA": 0.0, "dSOC_LA": 2.0, "dFE_LA": 0.3, "dFU_LA": 0.1}
lk_val = max((lkz["CY_min_prev"] - lkz["CY_t"]) / lkz["CY_BL"], 0.0) * lkz["A_bar"] * (lkz["dBC_LA"] + lkz["dSOC_LA"] + lkz["dFE_LA"] + lkz["dFU_LA"])
case(
    "SOCAT_yield_leakage",
    "DRAFT SOC Activity Tool (zero tillage) Eq. 8 printed as (7) (PDF p.150-151)",
    lkz,
    {"LK_t0_tCO2e": lk_val},
    note="Interpretation: CY_min = lowest 5-yr running mean in previously verified periods incl. baseline"
         " (so year-1 CY_min = CY_BL); the current period is charged only for the incremental drop below it."
         " Flag for BEE confirmation (errata E-SOCAT-03).",
)


if __name__ == "__main__":
    if "--json" in sys.argv:
        path = sys.argv[sys.argv.index("--json") + 1]
        with open(path, "w") as fh:
            json.dump(CASES, fh, indent=2, default=list)
        print(f"wrote {len(CASES)} cases to {path}")
    else:
        for k, v in CASES.items():
            print(f"\n== {k}  [{v['source']}]")
            for kk, vv in v["expected"].items():
                print(f"   {kk}: {vv}")
