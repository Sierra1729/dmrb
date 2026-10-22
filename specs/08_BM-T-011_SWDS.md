# 08. BM-T-011: Emissions from Solid Waste Disposal Sites (SWDS)

Status: APPROVED, v1.0, 27 March 2025. Source: `/docs/source/BM-T-011_*.pdf` (25 pp).
Used by BM WA03.001, WA03.002, WA03.003 (and any avoided-disposal activity, e.g. composting).
Golden cases: `T011_*`.

## 1. Definitions that drive logic

* **Managed SWDS**: controlled placement (directed deposition, some control of scavenging and fires)
  AND at least one of: cover material, mechanical compaction, levelling. Otherwise unmanaged.
* **Stockpile counts as SWDS** if volume/surface-area ratio >= 1.5 AND ACVA visual inspection
  confirms anaerobic conditions (low porosity, moist). Capture both values plus inspection record.
* **MSW** = heterogeneous household, garden/park, commercial/institutional waste.
* **Residual waste** = largely homogeneous (e.g. digestate, compost, biomass residues).
* Hazardous waste is not solid waste for this tool.

## 2. Applications

* **Application A**: project mitigates methane from a specific existing SWDS (capture and flare /
  use, e.g. BM WA03.002). Tool used only for **ex-ante** estimation in the PDD; ex-post uses
  monitored capture. Time series may start before project start (first year the SWDS received waste).
* **Application B**: project avoids (or involves) disposal at an SWDS (e.g. composting, AD, CBG).
  Ex-ante and ex-post. Simplified approaches "in the appendix" are referenced, but **the appendix is
  missing from the PDF** (E-T11-01): do not implement simplified approaches until supplied.
* Apply the tool separately to each residual-waste type and to MSW (para 7).

## 3. Outputs

`BE_CH4,SWDS,y` / `PE_CH4,SWDS,y` / `LE_CH4,SWDS,y` (t CO2e/yr) or the monthly equivalents
`..._m` (t CO2e/month). The engine computes a single function and labels by role.

## 4. First-order decay (FOD) model

Yearly:
```
[T011 Eq.1]  E_y = φ_y * (1 - f_y) * GWP_CH4 * (1 - OX) * 16/12 * F * DOC_f,y * MCF_y
                   * Σ_{x=1..y} Σ_j ( W_j,x * DOC_j * e^{-k_j (y - x)} * (1 - e^{-k_j}) )
```
Monthly:
```
[T011 Eq.2]  E_m = φ_y * (1 - f_y) * GWP_CH4 * (1 - OX) * 16/12 * F * DOC_f,m * MCF_y
                   * Σ_{i=1..m} Σ_j ( W_j,i * DOC_j * e^{-(k_j/12)(m - i)} * (1 - e^{-k_j/12}) )
```
* x = 1 is the first year of the disposal period considered; y is the crediting year (12 months);
  m, i are months; φ_y for a month is that of its year.
* Waste disposed in year x starts emitting in the same year x (term (1 - e^{-k}) at x = y).
* Either model may be used; document the choice and the disposal period in the PDD (para 12-13).

## 5. Parameters and how to determine them (Table 2)

| Parameter | Application A | Application B |
|---|---|---|
| φ_y | Project/leakage: 1. Baseline: default or Option 2 | same |
| OX | default 0.1 | default 0.1 |
| F | default 0.5 | default 0.5 |
| DOC_f | default 0.5 | MSW: default 0.5 or BMP-based once; residual waste: BMP-based once (mandatory) |
| MCF_y | default by SWDS type | monitored if water table above SWDS bottom (Eq.12); else default |
| k_j | default by waste type and climate | same |
| W_j,x | estimated once (site records, area x depth x 1-1.2 t/m3) | calculated from monitored data |
| DOC_j | default by waste type | default or measured once (EN 15169 ignition-loss) |
| f_y | estimated once | monitored annually |

### 5.1 Model correction factor φ_y

Project or leakage emissions: φ = 1. Baseline emissions, Option 1 default:

| | Humid/Wet | Dry |
|---|---|---|
| Application A | 0.75 | 0.75 |
| Application B | 0.85 | 0.80 |

Option 2 (project-specific):
```
[T011 Eq.3]  V_y = sqrt( a^2 + b^2 + c^2 + d^2 + e^2 + g^2 )
[T011 Eq.4]  φ_y = 1 / (1 + V_y)                      (printed "φy=1(1+Vy)", E-T11-02)
```

| Factor | Parameter | Low | High | Use low value when |
|---|---|---|---|---|
| a | W | 2 % | 10 % | Waste weighed on accurate weighbridges (else high, e.g. estimated from depth x area) |
| b | DOC_j | 5 % | 10 % | DOC_j measured (else high for defaults) |
| c | DOC_f | 5 % | 15 % | > 50 % rapidly degradable organics, or tropical climate |
| d | F | 0 % | 5 % | > 50 % rapidly degradable organics |
| e | MCF_y | 0 % | 50 % | Managed SWDS. Unmanaged: high value, or 2/d with d = SWDS depth (m) |
| g | exponential term | 5 % | 20 % | (i) Application B with residual waste and k > 0.2/yr; (ii) Application A with compartments closed < 3 years ago |

Each factor selection is a form field with the rule shown and a justification text. Re-evaluate
annually if conditions change (DPT 17).

### 5.2 Waste quantities by type

Application A: W from SWDS owner records, interviews, compartment data, area x average depth x
1.0-1.2 t/m3 (choose the lower density for conservatism unless evidence).
Application B:
```
[T011 Eq.5]  W_j,x = W_x * p_j,x
[T011 Eq.6]  W_j,i = W_i * p_j,i
[T011 Eq.7]  p_j,x = Σ_{n=1..z_x} p_n,j,x / z_x
[T011 Eq.8]  p_j,i = Σ_{n=1..3} p_n,j,i / 3          (three most recent samples during or before month i)
```
Sampling: minimum three samples every three months (DPT 13-14); wet-basis weights; only needed if
more than one waste type. Single-type residual waste: W_j = W, no sampling.

### 5.3 DOC_f

Application A: default 0.5. Application B, MSW: default 0.5 or BMP-based; residual waste: BMP-based.
```
[T011 Eq.9]   DOC_f,y = 0.7 * 12/16 * BMP_MSW / ( F * Σ_j ( p_j,y * DOC_j ) )
[T011 Eq.10]  DOC_f,m = 0.7 * 12/16 * BMP_MSW / ( F * Σ_j ( p_j,m * DOC_j ) )
[T011 Eq.11]  DOC_f,y = DOC_f,m = 0.7 * 12/16 * BMP_j / ( F * DOC_j )
```
BMP in t CH4 / t waste: fermentation test on >= 500 g sample, run to completion, mean of >= 3
results from different batches; valid for the crediting period.

### 5.4 MCF

Application A: default by SWDS type. Application B: if the water table is above the SWDS bottom:
```
[T011 Eq.12]  MCF_y = max( 1 - 2 / d_y , h_w,y / d_y )
```
d_y = SWDS depth (m), h_w,y = water-table height from base (m), monthly monitoring-well readings,
annual average for the yearly model. Otherwise default:

| SWDS type | MCF_default |
|---|---|
| Anaerobic managed (controlled placement + cover/compaction/levelling) | 1.0 |
| Semi-aerobic managed (controlled placement + permeable cover + leachate drainage + regulating pondage + gas ventilation, all) | 0.5 |
| Unmanaged, deep (>= 5 m) | 0.8 |
| Unmanaged, shallow (< 5 m) or stockpile that counts as SWDS | 0.4 |

### 5.5 Defaults DOC_j (per cent of wet waste; IPCC 2006 Vol.5 Tables 2.4/2.5)

| Waste type j | DOC_j |
|---|---|
| Wood and wood products | 43 % |
| Pulp, paper and cardboard (other than sludge) | 40 % |
| Food, food waste, beverages and tobacco (other than sludge) | 15 % |
| Textiles | 24 % |
| Garden, yard and park waste | 20 % |
| Glass, plastic, metal, other inert | 0 % |
| Empty fruit bunches (EFB) | use garden value (20 %) |
| Industrial sludge | 9 % (35 % organic dry matter) or 9 x (%ODM / 35) |
| Domestic sludge | 5 % (10 % organic dry matter) or 5 x (%ODM / 10) |

Unlisted or non-MSW-like waste: measure DOC_j (EN 15169 ignition loss, once per type) or choose the
most conservative similar type (lowest emissions).

### 5.6 Defaults k_j (1/yr; IPCC 2006 Vol.5 Table 3.3)

| Waste type j | Boreal/Temperate (MAT <= 20 °C) Dry (MAP/PET < 1) | ... Wet (MAP/PET > 1) | Tropical (MAT > 20 °C) Dry (MAP < 1000 mm) | Tropical Wet (MAP > 1000 mm) |
|---|---|---|---|---|
| Pulp, paper, cardboard (other than sludge), textiles | 0.04 | 0.06 | 0.045 | 0.07 |
| Wood, wood products and straw | 0.02 | 0.03 | 0.025 | 0.035 |
| Other (non-food) organic putrescible garden and park waste | 0.05 | 0.10 | 0.065 | 0.17 |
| Food, food waste, sewage sludge, beverages and tobacco | 0.06 | 0.185 | 0.085 | 0.40 |

EFB: garden values. Pulp and paper industry sludge: k = 0.03 for all climates. Climate class from
long-term MAT, MAP, PET of the SWDS site (document sources). Boundary values (exactly 20 °C, MAP/PET
exactly 1, MAP exactly 1000 mm) are not covered; choose the class giving lower emissions (E-T11-04).

### 5.7 Other defaults

OX = 0.1; F = 0.5; GWP_CH4 = value for the relevant period (CCTS: latest IPCC GWP100; BEE
methodologies use 29.8).

### 5.8 f_y (fraction captured and destroyed at the SWDS)

Maximum of (a) contract/regulation requirement and (b) historic captured data. Application A: once
for the crediting period; Application B: annually. When BM WA03.002 uses this tool ex-ante, set
f_y = 0 there because capture is handled in the methodology (see spec 11).

## 6. Monitoring parameters (section 5.5)

| Parameter | Unit | Frequency | Notes |
|---|---|---|---|
| f_y | - | A: once; B: annual | |
| W_x / W_i | t (wet) | Continuous, aggregated yearly / monthly | Application B |
| W_org,x | t | Continuous, aggregated yearly | Only for missing "simplified" appendix |
| p_n,j,x / p_n,j,i | - | Minimum 3 samples every 3 months | Application B, multi-type waste |
| z_x | count | Annual | |
| d_y, h_w,y | m | Monthly (monitoring well), annual mean for yearly model | DPT 15 swaps "frequency" and "QA/QC" rows (E-T11-03) |
| a..g | % | Annually if conditions change, else once | Option 2 only |

## 7. Engine requirements

* Vectorise over disposal-year cohorts and waste types; support up to 100-year back-series.
* Return per-cohort contributions for audit (which disposal year and waste type contributes what).
* Validate composition fractions sum to 1 ± 0.01 (after including inert); flag otherwise.
* Unit tests: (a) a single cohort decays geometrically by e^{-k} per year; (b) the sum of emissions
  over infinite years for one cohort equals W·DOC·(factors), i.e. Σ_y e^{-k(y-x)}(1-e^{-k}) = 1;
  (c) yearly and monthly models give consistent totals over long horizons (within 2 %).
