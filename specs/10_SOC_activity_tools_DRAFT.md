# 10. DRAFT: Five SOC Activity Tools (Agricultural Soil Carbon)

Status: **DRAFT** (codes "BM-T-0XXX", dates "XX/XX 2026"). Source:
`/docs/source/DRAFT_SOC_Model_Guidelines_and_5_SOC_Activity_Tools.pdf`, PDF pages 63-160.
All five are **modules of the SOC Framework Methodology (not in pack)**. Implement the
tool-specific rules below; SOC stock quantification itself comes from the SOC FM approaches
(Approach 1 measurement, Approach 2 models per spec 09, Approach 3 default factors) and spec 09.
Golden cases: `SOCAT_*`.

## 1. Common rules (all five tools unless noted)

* India only; mineral soils only (Histosols excluded); no wetlands; managed cropping system for >= 5
  years before start; no land-use change.
* Only the SOC pool is credited. No credit for other pools or for reduced emissions (fuel,
  fertiliser), though increases must be deducted.
* Significant additional emissions (> 5 % of total) must be accounted.
* Baseline = continuation of the last 5 years' practices; baseline data for 5 years (may extend to
  full rotation cycles, avoid rotation fragments).
* Stratify into modelling units (MU); per MU measure (Approach 1) and/or identify and verify model
  parameters (Approach 2/3). "Black box" models not allowed: full transparency of inputs and
  parameters.
* If several SOC practices are combined, the same quantification approach must cover all and avoid
  double counting.
* Missing SD/SE for a parameter: assume SE = 50 % of the value and use t = 3 for confidence limits,
  except constant defaults such as GWPs (cover crops para 36; zero tillage para 32).

## 2. Tool-specific applicability and settings

| Item | Cover crops | Improved tillage | Zero tillage | Biostimulants | Pulp & paper sludge soil improvers |
|---|---|---|---|---|---|
| Activity | Cover crops in fallow periods (legumes, non-legumes, grasses, brassicas; single or mix; annual/biennial/perennial) | Conservation (reduced/minimum) tillage, >= 30 % residue cover after planting | No tillage between harvest and sowing, >= 30 % residue cover | Registered biostimulant (not a pesticide), proven efficacy, no GMO, no adverse effects | Soil improver processed from pulp/paper mill sludge, legal for agriculture, meets fertiliser quality rules, non-fossil |
| Exclusions | Farm used cover crops > 1 season in 5 yrs before start (any field) | No-till, strip-till, direct drill not eligible | > 1 full rotation of zero till in baseline; single-crop: > 2 consecutive zero-till years; a tillage event within 2 yrs before start required | Riparian/buffer zones, conservation set-asides | Riparian/buffer zones, conservation set-asides |
| Other input limits | Non-cover-crop organic C inputs within ±5 % of baseline average (unless stacked with compatible tool); herbicide use <= +5 % | - | Organic C inputs (other than residue) within ±5 %; herbicides <= +5 %; no reversal to tillage (no rotational tillage) | Soil-characteristics indicator improvement (Annex 1) or justification | Heavy-metal markers monitored each 5-yr renewal |
| Approaches allowed | 1, 2, 3 (3.1 Tier 2 stock-change factors; 3.2 IPCC 2019 Tier 2 steady-state) | 1, 2, 3 (3 with project-specific SOC_REF + IPCC factors) | 1, 2 only | 1, 2 | 1 recommended, 2 allowed |
| Crediting period | 10 yrs required; renewable 5 yrs x max 2 renewals (15) | Per draft "Ecosystem-based approaches": 20 fixed or 10 renewable x 3 (30) | 20 fixed | 20 fixed or 10 renewable; start = later of project start or 3 yrs before PD certification | Max 20; 5-year certification cycle |
| Sampling notes (Approach 1) | Same season each time; before organic inputs or tillage; equivalent soil mass; exclude surface residue | SOC FM | Depth 50 cm; avoid resampling same spot (mark, GPS, minimum distance); equivalent soil mass; exclude residue | 0-10 and 10-30 cm minimum (to 1 m optional); at least every 4 yrs, same time of year; intact core or excavation BD | At least every 5 years |
| Model (Approach 2) | Local calibration (>= 5 yrs calibration + 3 yrs independent verification data); no global Q10; sub-annual resolution; re-measure each MU at start and every 5 yrs | SOC FM | Same as cover crops | Replicable, versioned; >= 2 peer-reviewed indexed papers; same parameters baseline and project | Peer-reviewed evidence of conservativeness |
| Leakage | Stratum-level yield leakage, Eq.10 | 0 initially; yield-based if yield drops | Stratum-level, Eq.8 with max(·,0); > 5 % yield drop in 5-yr average is leakage (first 3 yrs may be excepted) | 0 initially; yield-based if drop | 0 in principle; yield-based if drop |

Stratification criteria to expose as MU attributes: mineral soil type (WRB RSG), climate zone,
cropping system / specific crops and rotation, production period, productivity (NPP or yield),
input levels (fertiliser), tillage practice (depth, frequency, equipment), fallow period, cover-crop
period and type, vegetation cover level, irrigation and other practices.

## 3. Other (project) emissions: stratum-level equations (cover crops Eq.1-9; zero tillage Eq.1-7)

These replace SOC FM Eq.12-18 for these tools.
```
[CC Eq.1]   PE_t-0  = ΔFE_t-0 + ΔFU_t-0 + ΔSPT_t-0 + ΔAE_t-0          (zero tillage: no ΔSPT)
[CC Eq.2]   ΔFE_t-0 = Σ_y [ EF_FE,y * Σ_{a=1..T} ( FE_PR,y,a - FE_BL,y ) ]      floored at 0
[CC Eq.3]   ΔFU_t-0 = Σ_y [ Σ_{a=1..T} ( FU_PR,y,a - FU_BL,y ) + ( EU_PR,y,a - EU_BL,y ) ]
[CC Eq.4]   FU_i,y,a = Σ_MT FUL_i,y,MT,a * FEF_i,y,MT                         (i = BL or PR)
[CC Eq.5]   EU_i,y,a = Σ_SE EUW_i,y,SE,a * EEF_i,y,SE
[CC Eq.6]   ΔSPT_t-0 = Σ_y [ Σ_{a=1..T} SPT_PR,y,a ]                          (baseline SPT = 0)
[CC Eq.7]   SPT_PR,y,a = Σ_c [ ( S_PR,y,a,c * A_PR,y ) * ( EF_SP,y,c + EF_ST,y,c * DistST_PR,y,a,c ) ]
[CC Eq.8]   ΔAE_t-0 = Σ_y [ Σ_{a=1..T} ( AE_PR,y,a - AE_BL,y ) ]
[CC Eq.9]   AE_i,y,a = Σ_ET AQ_i,y,ET,a * AEF_i,y,ET
```
Rules:
* y = stratum, a = year in calculation period, T = years in period.
* ΔFE only for increases; decreases -> 0 (no credit). No synthetic/organic distinction.
* ΔFU, ΔAE: set to 0 only if the entity demonstrates project use <= baseline or not significantly
  different; otherwise compute. Implement the 3-way bracket in Eq.3 as
  `Σ_y Σ_a [ (FU_PR - FU_BL) + (EU_PR - EU_BL) ]` (E-SOCAT-02).
* Units: Eq.4, Eq.5, Eq.9 results are labelled "tCO2e ha-1" but the inputs are totals (litres, kWh,
  kg) for the stratum, so results are tCO2e per stratum (E-SOCAT-04). Implement as totals.
* Baseline means (FE_BL, FU_BL, EU_BL, AE_BL) from 5 years of records. **No adequate records -> the
  baseline value is capped at 50 % of the project value** (conservative). Implement as
  `BL_used = min(BL_documented or +inf, 0.5 * PR)` when documentation flag is false.
* **EF_FE**: printed "0.01 tCO2e/kgN (IPCC 2019 aggregated default)". 0.01 is IPCC EF1 in kg
  N2O-N/kg N. Conversion gives 0.01 * 44/28 * GWP_N2O / 1000 = 0.00429 tCO2e/kgN (GWP 273).
  Default: use the printed 0.01 (more conservative) and show the converted value side by side
  until BEE clarifies (E-SOCAT-01). Disaggregated IPCC 2019 Table 11.1 values allowed if inputs are
  known per fertiliser type.
* Non-CO2 from fuel combustion negligible. On-site fossil generation: compute as fuel, not grid.
* EEF sources: zero-tillage tool: grid -> TOOL05-equivalent (use BM-T-003), mini-grid -> AMS-I.F
  provisions, captive renewable -> 0, captive fossil -> national inventory, else IPCC 2006 Vol.2
  Table 3.3.1. FEF: national inventory, else IPCC 2006 Vol.2 Table 3.3.1.
* Seed transport: field-size-weighted mean distance per stratum (GIS); separate modes (air, sea,
  ground) with separate EFs; if EF_SP already includes transport to distribution centre, use the
  remaining distance only; EF_ST uncertainty 50 % if unknown. EF_SP assessed by an expert in the ACVA
  team at validation.
* AQ unit printed "km" (DPT 3 / DPT 5); correct unit is kg (E-SOCAT-05).

## 4. Yield leakage (cover crops Eq.10; zero tillage Eq.8 printed as "(7)")

```
LK_t-0 = Σ_y [ max( (CY_min,y - CY_t,y) / CY_BL,y , 0 ) * Ā_y,t ] * ( ΔBC_LA + ΔSOC_LA,t-0 + ΔFE_LA,t-0 + ΔFU_LA,t-0 )
```
* CY values are 5-year averages (kg/ha/yr summed over crops); in the project, running mean t-4..t;
  if baseline extended to full rotations, average over equal-length periods. CY_min,y = lowest
  5-year average since project start with baseline years included (year 1: CY_min = CY_BL).
* Interpretation (E-SOCAT-03): as printed CY_min <= CY_t whenever CY_min includes the current period,
  which makes leakage always 0. Implement CY_min from **previously verified periods only**, so the
  current period is charged for the incremental decline below the previous minimum; flag for BEE.
* ΔBC_LA, ΔSOC_LA, ΔFE_LA, ΔFU_LA in tCO2e/ha for the leakage area (remote sensing or public data);
  only increases in emissions counted, never gains (no positive leakage). As printed, one set of
  leakage-area factors multiplies the sum over strata. If leakage areas differ by stratum, allow
  per-stratum factor sets, `Σ_y [ share_y * Ā_y * (ΔBC + ΔSOC + ΔFE + ΔFU)_y ]`, which reduces to the
  printed form when the sets are equal.
* Zero tillage: a > 5 % drop in 5-year average yield is leakage; first 3 years may be excepted
  subject to verifier review (store the exception decision).

## 5. Biostimulants: project emissions (LCA)

```
[BS Eq.1]  PE_t = Σ_n ( A(y) * Q_PR,i,t,y * LCA_i )
```
A(y) stratum area (ha); Q_PR,i,t,y biostimulant type i used before dilution in stratum y in the
period (t/ha); LCA_i life-cycle emissions (tCO2e per t). DPT lists LCA_i unit as tCO2e/kg or tCO2e/L:
make units explicit and convert (E-SOCAT-06). LCA: ISO 14040/14044/14067, PAS 2050 or GHG Protocol
Product Standard; independent review if done by producer or entity; <= 1 year old at project start;
redo at least every 3 years or on > 5 % process change. LCA covers production, transport, application
(and the application-stage fertiliser / agrochemical increase). Application emissions may be
neglected if applied within a baseline operation (e.g. with seeding) with no extra energy; transport
may be omitted if < 5 % of net ER. QA: usage not above prescribed limit; cross-check records with
invoices.

## 6. Pulp and paper sludge soil improvers: project emissions

```
[PPS Eq.]  PE_y = Σ_i Q_amend,i * A_i * ( EF_trans1 + EF_process + EF_trans2,i + EF_applic,i )
                + Σ_k Q_ingredient,k * ( EF_ingredient,k + EF_trans3,k )
```
* The printed equation omits A_i although Q_amend is in t/ha (E-SOCAT-07); include A_i (MU area).
* EF_trans1 (t CO2e per t sludge) is applied per t sludge in the PDF but multiplied by Q_amend (t
  product): convert with the sludge-to-product mass ratio or compute transport emissions directly from
  fuel data FFC_trans x EF_FFC (preferred, E-SOCAT-08).
* CH4/N2O from processing may be taken as 0. Recycled ingredients: EF_ingredient = 0.
* Fuel EF: IPCC 2019 Refinement Vol.2 Ch.3 Table 3.3.1 (EF_FFC,MT, t CO2e per litre).
* Monitoring: Q_SOC,prod (C content, SFS-EN 13039, independent lab, annual), Q_amend (producer
  bookkeeping, annual), D_trans,industry and D_trans,farm (distance x trips), FFC_trans, FFC_applic,
  FFC_process, Q_ingredient, EF_ingredient, FFC_ingredient (annual), SH_HM,MC heavy-metal markers in
  soil per MU (mg/kg) at least every 5 years; content must not rise significantly.
* Areas leaving the project = full reversal (SOC FM). Long-term storage via reduced tillage and/or
  avoiding bare fallow.
* Optional avoided waste emissions (incineration/landfill) only via a separate ICM methodology
  (e.g. BM-T-011 with an applicable methodology).

## 7. Improved tillage: specific parameters

F_MG,BL,y (tillage factor before start; IPCC defaults or national/local studies preferred) at
project start; F_MG,PR,y annually. Evidence that erosion-prevention measures are in place and that
adequate organic residue/mulch/sod is applied. Annex A gives indicative Indian SOC accumulation rates
(tCO2e/ha/yr): Tropical dry HAC 0.83 (Kurothe 2014); Tropical dry LAC 1.94-2.24 (Bhattacharyya 2009),
0.89-1.38 (Das 2013), 1.36 (Bhattacharyya 2012). These are "rough indications only"; use them only
for screening / ex-ante feasibility, never for crediting.

## 8. Zero tillage: evidence of implementation

Field reports (interventions, dates, machinery), remote-sensing analysis of vegetation and residue
cover, timestamped photos before/during/after season including fallow. Engine: "no tillage event"
assertion per field per season with evidence; any tillage event = non-compliance alert.

## 9. Cover crops: Approach 3.2 Steady-State (IPCC 2019 Vol.4 Ch.5 Tier 2)

Reference pages: description 5.15-5.18, equations 5.18-5.23, step-by-step 5.23-5.26, Tables 5.5A
(model parameters), 5.5B (N and lignin of crops), 5.5C (C:N and lignin of manure), IPCC spreadsheet.
Project-level interpretation: IPCC "grid cell or region" = field stratum or field; include all inputs
(harvested crops in baseline; harvested + cover crops in project; green manure, compost, manure);
tillage changes per IPCC; project-specific data preferred, else IPCC Tier 2 defaults with sensitivity
analysis (min/max); crop, soil and weather data always local; all inputs monitored. Not combinable with
a separate tillage SOC module. **The IPCC equations are not reproduced in the pack**: implement this
sub-module only after adding IPCC 2019 Vol.4 Ch.5 to `/docs/source` and writing spec `10a`.
