# 12. Errata Register: Defects in Source Documents and Implemented Resolutions

Rules for the engine:
1. Every entry with a numeric effect has a config flag. The default is the **Resolution** column.
2. Any run that used a resolution with numeric effect lists the errata IDs in its report
   ("Interpretations applied").
3. Entries marked **ASK BEE** must be raised with BEE / the ACVA; record the answer here and switch the
   default if needed. Never change a formula silently.

Severity: **H** = changes results materially; **M** = could change results in edge cases;
**L** = cosmetic / cross-reference.

## Cross-cutting

| ID | Sev | Document / location | Defect | Resolution (default) | Flag |
|---|---|---|---|---|---|
| E-GWP-01 | H | BM-T-AR-0002 Eq.7 parameter table; BM-T-011 DPT 9 | AR-0002 prints GWP_CH4 = 21, GWP_N2O = 310 (IPCC SAR). Detailed Procedure requires latest IPCC GWP100. BEE methodologies use 29.8 / 273 | Use the project-locked GWP set (default AR6: CH4 29.8, N2O 273). Report also the "as printed" value. ASK BEE | `gwp_mode: project_locked \| tool_as_printed` |
| E-CF-01 | M | AR-0002 (0.50), AR-0003 (0.5), AR-0004 (0.47), AR-0005 (0.47) | Carbon fraction defaults differ between tools | Each tool uses its own printed default; a project-level override needs evidence and applies to all tools with a warning | `cf_policy: per_tool \| project_override` |
| E-AR4-08 | M | AR-0004 paras 26, 56 | States India reported 30 % threshold crown cover (6 % limit for proportionate crown cover). Confirm India's current reported forest definition | Parameter `forest_threshold_crown_cover = 0.30` editable by admin with source. ASK BEE | catalogue |
| E-SOC-00 | H | All SOC drafts | SOC Framework Methodology (UD, BUF, Approach 3 equations, sampling section 14.2, approach-change section 8) is not in the pack | Interfaces only; issuance-grade runs blocked; placeholders stamped DRAFT | `soc_fm_available: false` |

## BM-T-001

| ID | Sev | Location | Defect | Resolution |
|---|---|---|---|---|
| E-T001-01 | L | Para 42 Step 4a | Refers to "measures listed in the definitions section"; none listed | Always run Step 4b |
| E-T001-02 | M | Para 36 | "Methodological tool: Investment Analysis" not supplied | Benchmark / discount rate user-entered with evidence |

## BM-T-AR-0004 (trees and shrubs)

| ID | Sev | Location | Defect | Resolution |
|---|---|---|---|---|
| E-AR4-01 | L | Section 4.3 Note 1 | "conditions specified under paragraph 10" | Means para 13 (zero baseline tree stock) |
| E-AR4-02 | L | Throughout | Stale CDM cross-references: "section 6.2/6.3/6.4/8/10/12", "Table 1" | Map 6.2 -> 4.4, 6.3 -> 4.5, 6.4 -> 4.6, 8 -> 4.8, 10 -> 5.0, 12 -> 6 |
| E-AR4-03 | M | Section 4.11 variable list | β described as "number of plots in sub-sample"; n_i as "tree biomass per hectare" | β = regression slope (App.3), n_i = sub-sample size |
| E-AR4-04 | L | Para 8 | "clean development mechanism (ICM)" | Cosmetic |
| E-AR4-05 | L | Section 4.2 Eq.5 | Equation (5) has no number printed | Keep ID Eq.5 |
| E-AR4-06 | L | Paras 67-68 | "< 5 %" -> zero, Eq.26 for "> 5 %"; exactly 5 % undefined | Exactly 5 % uses Eq.26 (`shrub_cc_zero_below: 0.05`, strict <) |
| E-AR4-07 | L | Para 17/45 | "Variance of mean" label for sample variance | Implement as sample variance; divided by n_i in Eq.15 |

## BM-T-AR-0003 (dead wood and litter)

| ID | Sev | Location | Defect | Resolution |
|---|---|---|---|---|
| E-AR3-01 | H | Eq.1 | Printed `(1 + D_j)`; R_j is defined in the variable list | `(1 + R_j)` |
| E-AR3-02 | M | Eq.4 | `(H_STUMP / H_STUMP - H_DBH)^0.80` precedence ambiguous | `(H_STUMP / (H_STUMP - H_DBH))^0.80` (Ormerod 1973) |
| E-AR3-03 | L | Paras 12-13, 21, 26, 32, 46 | Cross-references "paragraph 14", "23-27", "Section 8" | Categories in para 12; stump method paras 20-24; DF tables in DPT 5-6 |
| E-AR3-04 | M | Eq.9, 15 | DF in per cent | Divide by 100 |
| E-AR3-05 | L | DPT 8-10 | "A1", "A PLOT,1", "ap,1", "DMIDSTIUMP" | Read as A_i, A_PLOT,i, a_p,i, D_MID_STUMP |
| E-AR3-06 | L | Eq.4 vs para 23 | ">= 4 m" vs "more than 4 m" | Use >= 4 m (para 22) |
| E-AR3-07 | M | Eq.12 | 2.5 assumes exactly four frames | If n_frames != 4 use 10 / n_frames and raise QA warning |

## BM-T-AR-0002 (fire)

| ID | Sev | Location | Defect | Resolution |
|---|---|---|---|---|
| E-AR2-01 | L | Introduction | Text copied from additionality tool | Cosmetic |
| E-AR2-02 | L | DPT A_BURN | Description copied from A_FMF | "Area burnt in stratum i in year t" |
| E-AR2-03 | H | Eq.8 | C_DW and C_LI defined as stratum totals (t CO2e) but multiplied by burnt area | Use per-hectare stocks c = C / A_i (t CO2e/ha) |
| E-AR2-04 | L | Para 5b | "60 % of DOM entirely burnt" not used in equations | No extra factor (0.07 ratio applies) |
| E-AR2-05 | M | B_FOREST | "Tables at the end of this tool" absent | Source hierarchy from DPT: national > neighbouring > global (FAO) > IPCC GPG-LULUCF |
| E-AR2-06 | L | Eq.3 | Left side printed "GHG_SPF,t=i=" | Read as GHG_SPF,t = 0.07 Σ_i ... |
| E-AR2-07 | M | Para 4 | Minimum fire area = India forest-definition minimum area, value not printed | Configurable `forest_min_area_ha`; ASK BEE |
| E-AR2-08 | M | DPT COMF (PDF p.10) | Tropical COMF table is misaligned on the page ("3-5 0.46 6-10 ... 0.67") | Read as 3-5 yr 0.46, 6-10 yr 0.67, 11-17 yr 0.50, >= 18 yr 0.32 (same as the UNFCCC source tool); stands < 3 yr not tabulated: require a project value |

## BM-T-AR-0005 (leakage)

| ID | Sev | Location | Defect | Resolution |
|---|---|---|---|---|
| E-AR5-01 | M | Eq.2-3 units | ΔC_BIOMASS labelled t d.m. (it is t C after × CF); ΔSOC_LUC labelled t C/ha (it is t C after × A) | Units t C |
| E-AR5-02 | L | Text extraction | Footnote markers merge with values (0.471, 0.252, 0.403) | Values are 0.47, 0.25, 0.40 (checked on page images) |
| E-AR5-03 | M | SOC_REF, f-factor references | Cites AR-0006 "Table 3" and "Tables 4, 5, 6" | Map by content to AR-0006 Tables 4, 5, 6, 7 |

## BM-T-AR-0006 (SOC in A/R)

| ID | Sev | Location | Defect | Resolution |
|---|---|---|---|---|
| E-AR6-01 | M | Para 4(a) | Conditions (i) and (ii) joined by "or" | Require all (AND) |
| E-AR6-02 | L | Para 8, 10 | "Tables 1 and 2", "Tables 3-6" vs printed Tables 2-7 | Map by content |
| E-AR6-03 | M | Table 5 | No f_MG for no-till | Block stratum unless justified value supplied (reviewer approval) |
| E-AR6-04 | M | Eq.6 | Rate after t_PREP + 20 not stated | 0 after t_PREP + 20 |
| E-AR6-05 | L | Title | Code printed "BMT-T-AR-0006" | Store canonical code BM-T-AR-0006 with alias |

## BM-T-011 (SWDS)

| ID | Sev | Location | Defect | Resolution |
|---|---|---|---|---|
| E-T11-01 | M | Section 5.1, para 5(b) | "Simplified approaches ... in the appendix" / "detailed in 0": appendix missing | Do not implement simplified approaches; ASK BEE |
| E-T11-02 | M | Eq.4 | Printed "φy=1(1+Vy)" | φ = 1 / (1 + V) |
| E-T11-03 | L | DPT 15 | Monitoring frequency and QA/QC rows swapped | Monthly readings; annual average for yearly model |
| E-T11-04 | L | DPT 7 | Climate class boundaries (MAT = 20 °C, MAP/PET = 1, MAP = 1000 mm) undefined | Choose class giving lower emissions |
| E-T11-05 | L | Para 2, Eq.6 | Incomplete sentence; index x used for months | Cosmetic |

## DRAFT SOC Model Guidelines

| ID | Sev | Location | Defect | Resolution |
|---|---|---|---|---|
| E-SOCMG-01 | L | Sections 3.1-3.2 | Scope/applicability copied from a fuel-combustion tool | Ignore |
| E-SOCMG-02 | H | Table 2 Eq.3a, 4, 5a | Unit factors (0.01, CFR in %, 1000) do not give t/ha or Mg/ha | Unit-correct forms in spec 09 section 3.1 |
| E-SOCMG-03 | M | Example E1.1 | Half-width 2.36 for SE 1.19, n 93 corresponds to 95 % | Follow Eq.21 (90 %) |
| E-SOCMG-04 | M | Eq.25 | PICP t statistic without critical value | Fail if t < -t(0.90, n-1); configurable |
| E-SOCMG-05 | L | Sections 5.1.3-5.1.5 | Refer to "4.3.3 / 4.3.4" for metrics | Means 5.1.2 / 5.1.3 |
| E-SOCMG-06 | M | Table 3 Eq.10 | α "typically 0.05 (95 %)" contradicts 90 % CI elsewhere | α = 0.1 |

## DRAFT SOC activity tools

| ID | Sev | Location | Defect | Resolution |
|---|---|---|---|---|
| E-SOCAT-01 | H | Cover crops Eq.2, zero tillage Eq.2, DPT EF_FE | EF_FE "0.01 tCO2e/kgN" is the IPCC EF1 in kg N2O-N/kg N | Default printed 0.01 (conservative); show converted 0.00429 (GWP 273); ASK BEE |
| E-SOCAT-02 | M | Eq.3 | Bracket closes before electricity term | Σ_y Σ_a [(FU_PR - FU_BL) + (EU_PR - EU_BL)] |
| E-SOCAT-03 | H | Cover crops Eq.10, zero tillage Eq.8 | If CY_min includes current period, leakage is always 0 | CY_min from previously verified periods incl. baseline; ASK BEE |
| E-SOCAT-04 | L | Eq.4, 5, 9 units | Results labelled per ha but inputs are totals | Totals per stratum |
| E-SOCAT-05 | L | DPT AQ | Unit "km" | kg |
| E-SOCAT-06 | M | Biostimulants Eq.1 vs DPT | LCA_i tCO2e/t vs tCO2e/kg or L | Explicit unit with conversion; density needed for L |
| E-SOCAT-07 | H | P&P sludge PE eq. | Q_amend in t/ha but no area multiplier | Multiply by MU area |
| E-SOCAT-08 | M | P&P sludge EF_trans1 | Per t sludge, multiplied by t product | Use sludge:product ratio or fuel-based transport emissions |
| E-SOCAT-09 | M | Cover crops Eq.10 | No max(·, 0) (zero tillage has it) | Apply max(·, 0) (no positive leakage) |
| E-SOCAT-10 | L | Cover crops DPT 7, 18 | "Used in Equation 8"; symbol S_PR vs SPT_PR | Eq.10; S_PR,y,a,c = seed rate |
| E-SOCAT-11 | L | Biostimulants numbering | Section numbers 12-18, "4.2 Spatial boundary" is temporal | Cosmetic |
| E-SOCAT-12 | L | Zero tillage Eq.8 | Printed as "(7)" | ID Eq.8 |

## Methodologies (verify when PDFs are added)

| ID | Sev | Location | Defect | Resolution |
|---|---|---|---|---|
| E-FR-01 | L | FR05.001 / FR05.002 | Cite additionality tool as "BM-T-AR-001"; list has BM-T-001 | Use BM-T-001 |
| E-FR-02 | L | FR05.001 | Tool IDs cited inconsistently (AR-004 vs AR-0004) | Canonical IDs |
| E-WA-01 | H | WA03.001 Eq.1, 4, 6; WA03.002 Eq.2, 17 | Machine extraction garbled | [VERIFY] against PDF before coding |
| E-WA-02 | M | WA03.002 Eq.5 | BE_CH4,SWDS unit t CO2e vs CH4 definition | Eq.5 divides by GWP, so treat BE_CH4,SWDS as t CO2e |
| E-AG1-01 | M | AG04.001 | UF_b 0.895 (para 3.2) vs 0.89 (Eq.5, DPT 4) | 0.89 (lower, conservative); ASK BEE |
| E-AG2-01 | H | AG04.002 PE_n | Sign and N2O-N conversion | [VERIFY] before coding |
| E-AG2-02 | M | AG04.002 Eq.7 | (1 - U_d) possibly applied twice | Apply once in Eq.6 |
| E-AG2-03 | L | AG04.002 | GWP_CH4 29.85 vs 29.8 | Project-locked GWP set |
