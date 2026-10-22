# 11. Project-Type Modules: How Tools Compose into Methodologies

The product is organised by **project type**. Each project type = one methodology plugin that
orchestrates tool plugins. The tool specs (02-10) are complete for the tools in the pack. The
methodology-level equations below were read from the BEE methodology PDFs (links in spec 01). Items
marked **[VERIFY]** came from a machine text extraction of those PDFs in which some equations were
garbled; download the PDF into `/docs/source`, confirm the equation against the page image, then
remove the tag in the same commit that implements it.

Build order (dependencies in hand first): **P1 A/R (FR05.002)** -> **P2 Mangrove (FR05.001)** ->
**P3 Landfill gas (WA03.002 / WA03.001)** -> **P4 Agricultural SOC (DRAFT)** -> P5 Rice (AG04.002) ->
P6 Manure biogas (AG04.001) -> P7 CBG (WA03.003) -> others (EN, IN) after their tools are supplied.

---

## P1. BM FR05.002 Afforestation and reforestation of lands except wetlands

Effective "08/09/2025" as printed (para 9; confirm day/month order on the PDF); derived from UNFCCC
AR-ACM0003.

Applicability: land is not wetland; project soil disturbance <= 10 % of area on (i) organic soils
and (ii) land under baseline land-use/management (pits 0.5 x 0.5 m at 3 x 3 m = 2.78 %, continuous
ploughing = 100 %); applicability of every applied tool. Land need not be degraded.

Pools: above-ground and below-ground tree biomass mandatory; shrubs (used in equations), dead wood,
litter, SOC optional (selected at validation, fixed thereafter). GHG: CH4 and N2O from burning woody
biomass; other sources treated as zero (herbaceous removal, fossil fuel, fertiliser, wood use,
N-fixer litter decomposition, roads, transport).

```
[FR05.002 Eq.1]  ΔC_BSL,t    = ΔC_TREE_BSL,t + ΔC_SHRUB_BSL,t + ΔC_DW_BSL,t + ΔC_LI_BSL,t       (AR-0004, AR-0003)
[FR05.002 Eq.2]  ΔC_ACTUAL,t = ΔC_P,t - GHG_E,t                                               (GHG_E from AR-0002)
[FR05.002 Eq.3]  ΔC_P,t      = ΔC_TREE_PROJ,t + ΔC_SHRUB_PROJ,t + ΔC_DW_PROJ,t + ΔC_LI_PROJ,t + ΔSOC_AL,t   (AR-0004/0003/0006)
[FR05.002 Eq.4]  LK_t        = LK_AGRIC,t                                                     (AR-0005)
[FR05.002 Eq.5]  ΔC_AR,t     = ΔC_ACTUAL,t - ΔC_BSL,t - LK_t
[FR05.002 Eq.6]  tCCC_t2     = Σ_{t=1..t2} ΔC_AR,t
[FR05.002 Eq.7]  lCCC_t2     = Σ_{t=t1+1..t2} ΔC_AR,t           (negative => lCCCs to replace: reversal)
```
Other rules: stratify only if biomass is heterogeneous (baseline by vegetation, crown cover, land
use; ex-ante by planting plan; ex-post by actual implementation, revised after fires etc.);
precision per AR-0004; inventory SOPs national or documented with QA/QC; archive >= 2 years after
last crediting period. The methodology refers to the additionality tool as "BM-T-AR-001"; the BEE
tool list has BM-T-001 only. Use BM-T-001 (E-FR-01).

Engine pipeline per monitoring event (t1 -> t2):
1. Resolve strata, plots, measurements; QA/QC gate.
2. AR-0004 tree and shrub stocks (baseline + project) with uncertainty and discount.
3. AR-0003 dead wood and litter (if selected).
4. AR-0006 SOC (if selected; per-stratum applicability check).
5. AR-0002 fire events in (t1, t2].
6. AR-0005 displacement records in (t1, t2].
7. Annualise per tool (Eq.11 / Eq.10-11 / Eq.16-17 / AR-0006 annual rates); allocate to project years.
8. Methodology Eq.1-5 per year; Eq.6-7 for the verification period; reversal detection.
9. Ex-ante: same pipeline with growth models (AR-0004 5.3), planting schedule and default factors.

## P2. BM FR05.001 Afforestation and reforestation of degraded mangrove habitats

Effective 27 Mar 2025. Applicability: degraded mangrove habitat (waterlogged saline/brackish soil,
cover below forest threshold); > 90 % of area planted with mangrove species; if > 10 % non-mangrove
species, no change to hydrology of the area and connected wetlands; soil disturbance <= 10 %.

Pools: AGB and BGB selected; **litter excluded** (tidal export, conservative); dead wood and SOC
optional. CH4/N2O from burning woody biomass included.
```
[FR05.001 Eq.1]  ΔC_BSL,t    = ΔC_TREE_BSL,t + ΔC_SHRUB_BSL,t + ΔC_DW_BSL,t
[FR05.001 Eq.2]  ΔC_ACTUAL,t = ΔC_P,t - GHG_E,t
[FR05.001 Eq.3]  ΔC_P,t      = ΔC_TREE_PROJ,t + ΔC_SHRUB_PROJ,t + ΔC_DW_PROJ,t + ΔSOC_PROJ,t
[FR05.001 Eq.4]  ΔSOC_PROJ,t = 44/12 * Σ A_PLANT,t * dSOC_t * 1 year        [VERIFY summation limits]
                 dSOC_t default 0.50 t C/ha/yr from t_PLANT to t_PLANT + 20, then 0
[FR05.001 Eq.5]  LK_t        = LK_AGRIC,t
[FR05.001 Eq.6]  ΔC_AR,t     = ΔC_ACTUAL,t - ΔC_BSL,t - LK_t
[FR05.001 Eq.7]  tCCC_t2     = Σ_{t=1..t2} ΔC_AR,t
[FR05.001 Eq.8]  lCCC_t2     = Σ_{t=t1+1..t2} ΔC_AR,t
```
Interpretation of Eq.4: cumulative planted cohorts each accrue dSOC for 20 years from their planting
year (cohort accounting: Σ over cohorts c with t_PLANT,c <= t < t_PLANT,c + 20 of A_c * 0.50).
AR-0006 is not used here (wetland). Mangrove-specific soil CH4/N2O are not in the methodology.

## P3. BM WA03.002 Flaring or use of landfill gas (and WA03.001 Landfill methane recovery)

WA03.002 (v1.0, 27 Mar 2025). Applicability: new LFG capture at existing or greenfield SWDS, or
investment in an existing system that previously vented or flared (not used); uses: flare,
electricity, heat (boiler, air heater, glass furnace, brick kiln), gas network, compressed/liquefied
by truck, dedicated pipeline. Not if organic waste otherwise recycled is reduced, or SWDS management
deliberately changed to raise methane. Tools: BM-T-001, -002, -003, -004, -005, -006, -007 (missing),
-011, -012 (missing).

```
[WA03.002 Eq.1]   BE_y      = BE_CH4,y + BE_EC,y + BE_HG,y + BE_NG,y
[WA03.002 Eq.2]   BE_CH4,y  = [ (1 - OX_top_layer) * F_CH4,PJ,y - F_CH4,BL,y ] * GWP_CH4        [VERIFY grouping]
[WA03.002 Eq.3]   F_CH4,PJ,y = F_CH4,flared,y + F_CH4,EL,y + F_CH4,HG,y + F_CH4,NG,y
[WA03.002 Eq.4]   F_CH4,flared,y = F_CH4,sent_flare,y - PE_flare,y / GWP_CH4                    (BM-T-004, BM-T-005)
[WA03.002 Eq.5]   F_CH4,PJ,y (ex-ante) = η_PJ * BE_CH4,SWDS,y / GWP_CH4      η_PJ default 0.5;
                  BE_CH4,SWDS,y from BM-T-011 Application A with f_y = 0, series from first year of SWDS
Baseline destruction F_CH4,BL,y (Eq.6-16):
   Case 1 no requirement, no system             -> 0
   Case 2 requirement, no system                -> F_BL,R,y: stated amount; or ρ_reg,y * F_CH4,PJ,capt,y;
                                                   capture-only requirement -> 0; capture+flare with no rate -> 0.2 * F_PJ,capt,y
   Case 3 no requirement, existing system       -> F_BL,sys,y: separately metered existing flow; else historic
                                                   ratio F_hist,y = (F_BL,x-1 / F_x-1) * F_PJ,y (F_x-1 via BM-T-011); else 0.2 * F_PJ,y
   Case 4 requirement and system                -> max(F_BL,R,y ; F_BL,sys,y)
[WA03.002 Eq.17]  BE_HG,y = NCV_CH4 * Σ_j [ min(1, η_PJ,j,y / η_BL,j) * F_CH4,HG,dest,j,y * EF_CO2,BL,HG,j ]   [VERIFY]
                  NCV_CH4 = 0.0504 TJ/t CH4; fd default 1 (boiler, air heater, glass furnace), 0.9 brick kiln
[WA03.002 Eq.21]  BE_NG,y = 0.0504 * F_CH4,NG,y * EF_CO2,NG,y
[WA03.002 Eq.22]  PE_y = PE_EC,y + PE_FC,y + PE_DT,y + PE_SP,y      (BM-T-003, BM-T-002, BM-T-007, pipeline)
[WA03.002 Eq.24]  PE_leaks,y = GWP_CH4 * ( F_CH4,NG_TR,y - F_CH4,NG-cons,y )
[WA03.002 Eq.25]  PE_SP,y = 0.0504 * DEF_TSP * F_CH4,NG,y        DEF_TSP = 2.2 tCO2e/TJ
Leakage: none.
[WA03.002 Eq.26]  ER_y = BE_y - PE_y
```
Defaults: OX_top_layer 0.1; GWP_CH4 29.8; η_PJ 50 % (ex-ante); EF_CO2 defaults at lower 95 % CI of
IPCC 2006. Monitoring: LFG flow (continuous), CH4 fraction (continuous analyser or periodic at
90/10), T and P (or normalised flow), electricity generated/consumed (continuous), equipment
operation hourly, truck batches, SWDS management changes annually.

WA03.001 (landfill methane recovery; effective 27 Mar 2025) [VERIFY whole equation set]:
```
BE_y = (BE_CH4,SWDS,y - F_CH4,BL,y) * GWP_CH4 * (1 - OX) * (1 - η_PJ)       ex-ante form (verify)
PE_y = PE_Power,y + PE_flare,y + PE_process,y
ER_y,estimated  = BE_y - PE_y - LE_y
ER_y,calculated = [ (F_CH4,PJ,y - F_CH4,BL,y) * GWP_CH4 - (PE_y + LE_y) ] * (1 - OX)   (verify)
F_CH4,PJ,y = Σ_i D_CH4,y * w_CH4,y * LFG_i,y     or     EG_y * 3600 / (NCV_CH4 * EE_y) * D_CH4
```
Defaults: OX 0.1; η_PJ 50 %; NCV_CH4 35.9 MJ/Nm3; EE_y 40 % if no manufacturer value; w_CH4 must be
measured directly (no inference from CO2); PE_Power assumes rated capacity + 10 % losses x 8760 h.

dMRV hooks: SCADA/CSV/MQTT ingestion of flow, CH4 %, T, P, flare temperature/flame status at
>= hourly resolution; gap-filling rules must be conservative (no gap-filling of the claimed flow;
missing hours = 0 destroyed for the project, or as the tool specifies); instrument calibration
register; BM-T-011 ex-ante curve vs measured capture overlay chart.

## P4. Agricultural SOC (DRAFT): SOC FM + activity tools

Gate: all outputs stamped DRAFT until the SOC FM and final tools are adopted.
```
ER_t-0 = [ ΔC_SOC,t-0 * 44/12 - PE_t-0 - LK_t-0 ] * (1 - BUF)                 (SOC FM Eq.1)
ΔC_SOC,t-0 = (SOC_t - SOC_0) * (1 - UD)                                         (SOC FM Eq.2)
PE_t-0, LK_t-0 per activity tool (spec 10 sections 3-6); UD per SOC FM Ch.9 (+ TU safety discount
for model-based, spec 09); BUF per SOC FM (missing)
```
SOC_t / SOC_0 per MU by: Approach 1 (design-based, stratified random sampling, equivalent soil mass);
Approach 2 (validated model, spec 09); Approach 3 (IPCC factors; cover crops 3.1/3.2; improved
tillage with project SOC_REF). Pipeline per calculation period: farms/fields -> MUs -> samples or model
runs -> SOC stocks per MU with CI -> ΔC_SOC with UD -> other emissions -> yield leakage -> ER.

## P5. BM AG04.002 Improved management practices in rice cultivation [VERIFY all]

Applicability: predominantly irrigated, flooded rice with controlled irrigation and drainage;
upland/rainfed/deep-water excluded; no untested cultivar unless low-emission and no yield loss;
training documented; closed-chamber measurement capacity unless Tier 1. Eligible changes: continuous
-> intermittent flooding / shorter flooding, AWD, aerobic rice, transplanted -> DSR; optional changes
count only if > 5 % change. Leakage negligible. Based on AMS-III.AU.
```
BE_y = Σ_s BE_s ;  BE_s = Σ_g ( EF_BL,s,g * A_s,g ) * 10^-3 * GWP_CH4
PE_y = Σ_s PE_s + PE_n + PE_l ;  PE_s = Σ_g ( EF_P,s,g * A_s,g ) * 10^-3 * GWP_CH4
PE_n = Σ_g ( Q_n,P,g * A_s,g ) * (EF_N2O,B,g - EF_N2O,P,g) * 10^-3 * GWP_N2O    as extracted
       [VERIFY: with EF_N2O,P 0.005 > EF_N2O,B 0.003 kg N2O-N/kg N the printed order gives a
        negative project emission; EFs are in N2O-N, so a 44/28 conversion may also be missing.
        Do not implement until checked against the PDF page.]
ER_y = (BE_y - PE_y) * (1 - U_d)                  U_d default 15 %
Tier 1: ER_y = EF_ER * A_y * L_y * 10^-3 * GWP_CH4 * (1 - U_d) ;  EF_ER = EF_BL - EF_P
        EF_BL = EF_BL,c * SF_BL,w * SF_BL,p * SF_BL,o ;  EF_P = EF_BL,c * SF_P,w * SF_P,p * SF_P,o
        SF_o = (1 + Σ_i ROA_i * CFOA_i)^0.59
SF_w: continuously flooded 1.00; intermittent single aeration 0.71; multiple aeration 0.55
SF_p: non-flooded < 180 d 1.00; > 180 d 0.89
GWP_CH4 29.8 (also 29.85 printed); GWP_N2O 273 (273.06 printed)
```
Measurement annex: closed chambers (>= 3 per plot, >= 3 samples per 30 min, morning, at least weekly,
extra after fertiliser or irrigation; >= 4 hills, ~0.1 m2; GC-FID with daily calibration; >= 3
reference fields per group). Flux = slope of mass vs time (mg/min) x 60 / chamber area; plot mean;
seasonal integration x interval hours; x 0.01 mg/m2 -> kg/ha.

## P6. BM AG04.001 Methane recovery from manure at households and small farms [VERIFY]

Applicability: households/small farms; mean annual temperature > 5 °C; only manure that would decay
anaerobically in baseline (survey); digestate handled aerobically; all biogas combusted. Based on
AMS-III.R.
```
BE_y = Σ ( N_LT,PS,y * AM_LT,PS/1000 * VS_rate * 365 * B0 * 0.67 * 10^-3 * MCF/100 * AWMS * GWP_CH4 * UF_b )
PE_y = PE_PL,y + PE_FC,y + PE_EC,y ;   PE_PL,y = 0.10 x (Eq.1 structure for manure fed to digesters)
ER_y = min{ BE_y * n_k,y - PE_PL,y - PE_FC,y - PE_EC,y ;  MD_y - PE_FC,y - PE_EC,y - LE_y }
MD_y = Σ_k ( N_k,0 * n_k,y * UF_b * BS_k,y * w_CH4,y * D_CH4,y * GWP_CH4 )
```
IPCC 2019 Vol.4 Ch.10 defaults (VS, B0, MCF); UF_b 0.89 (0.895 also printed, E-AG1-01); w_CH4 60 %
default or measured; n_k,y biennial (95/10); BS_k,y annual flow-meter sampling >= 30 days per site.

## P7. BM WA03.003 Production of Compressed Bio-gas (CBG) [VERIFY all]

Baseline: avoided SWDS methane (BM-T-011, Application B), avoided open-lagoon wastewater methane
(MCF method with depth and temperature factors, conservativeness 0.89), displaced grid/fossil
electricity and heat, displaced natural gas / transport fuels; total multiplied by (1 - compliance
rate) where treatment is mandated (compliance must be < 50 %). Project: AD (BM-T-008), composting
(BM-T-013), CBG leakage (default 0.05 m3 per m3), flaring (90 % destruction), electricity and fuel,
biomass cultivation (BM-T-010). Implement after BM-T-008/010/013/014 PDFs are added and this section
is expanded into its own spec.

## P8+. Energy and industry (EN01.001-003, IN02.001-002)

Need BM-T-002, -003, -006, -015 (and -010 for biomass). Reserve plugin slots; no implementation in v1.

---

## Cross-cutting: monitoring periods, vintages, reversals

* Monitoring period = [start, end] dates, chronological, no overlap; one crediting period per MR.
* Annual results allocated to calendar vintages pro rata by days.
* Negative net results are deducted (Detailed Procedure); for A/R, lCCC < 0 signals reversal.
* Every methodology run produces: per-year table, per-tool sub-results, uncertainty statement,
  parameter provenance list, warnings (errata used, draft status), and a frozen snapshot id.
