# 03. BM-T-AR-0004: Carbon Stocks and Change in Carbon Stocks of Trees and Shrubs (A/R)

Status: APPROVED, v1.0, effective 27 March 2025. Source: `/docs/source/BM-T-AR-0004_*.pdf` (31 pp).
Equations in this PDF are images; the forms below were transcribed from the page images and checked.
Golden cases: `AR0004_*`.

## 1. Outputs

| Symbol | Unit | Meaning |
|---|---|---|
| C_TREE,t | t CO2e | Carbon stock in tree biomass (above + below ground) in project boundary at a point of time in year t |
| ΔC_TREE,t | t CO2e | Change in tree carbon stock in year t |
| C_SHRUB,t | t CO2e | Carbon stock in shrub biomass |
| ΔC_SHRUB,t | t CO2e | Change in shrub carbon stock in year t |

Scenario notation: `C_TREE_BSL,t`, `C_SHRUB_BSL,t`, `ΔC_TREE_BSL,t`, `ΔC_SHRUB_BSL,t`;
`C_TREE_PROJ,t`, `C_SHRUB_PROJ,t`, `ΔC_TREE_PROJ,t`, `ΔC_SHRUB_PROJ,t`.

Definitions: tree biomass and shrub biomass = above-ground + below-ground living biomass.
Uncertainty = SEM expanded at 90 % confidence / mean, in per cent (only sampling uncertainty).

## 2. Zero-accounting rules (section 4.1)

* **Baseline tree stock = 0** if ALL: pre-project trees are not harvested, cleared or removed during
  the crediting period; they suffer no mortality from project competition or damage; they are
  not inventoried with project trees but their continued existence is monitored (para 13).
* **Baseline change in trees and shrubs = 0** if ANY indicator documented (PRA or documents):
  topsoil loss; gully/sheet/rill erosion or mass movement; infertility indicator species; bare
  dunes/bare land; contaminated soils, mine spoils, highly alkaline or saline soils; periodic
  cycles (slash-and-burn, clearing-regrowing); or the para-13 conditions apply (para 14).
* **Ex-ante project shrub change may be 0** (para 15).

UI: checklist per baseline stratum with evidence upload; the engine sets the value and stores the
justification code.

## 3. Change between two points of time (section 4.2): four methods, may be mixed by stratum

### 3.1 Difference of two independent stock estimations (section 4.3)

```
[AR0004 Eq.1]  ΔC_TREE = C_TREE,t2 - C_TREE,t1
[AR0004 Eq.2]  u_ΔC    = sqrt( (u1 * C_TREE,t1)^2 + (u2 * C_TREE,t2)^2 ) / |ΔC_TREE|
```
* At first verification C_TREE,t1 = C_TREE_BSL (pre-project stock), or 0 if the para-13 conditions
  hold (the text says "paragraph 10", see E-AR4-01).
* Always use the **undiscounted** previous estimate C_TREE,t1 (Note 2).
* If u_ΔC > 10 %: apply Appendix-2 discount to ΔC_TREE.

### 3.2 Direct estimation of change by re-measurement of the same plots (section 4.4, ex-post only)

```
[AR0004 Eq.3]  ΔC_TREE  = 44/12 * CF_TREE * ΔB_TREE                 CF_TREE default 0.47
[AR0004 Eq.4]  ΔB_TREE  = A * Δb_TREE
[AR0004 Eq.5]  Δb_TREE  = Σ_{i=1..M} w_i * Δb_TREE,i               w_i = A_i / A
[AR0004 Eq.6]  u_ΔC     = t_VAL * sqrt( Σ_i w_i^2 * s²_Δ,i / n_i ) / |Δb_TREE|
[AR0004 Eq.7]  Δb_TREE,i = Σ_{p=1..n_i} Δb_TREE,p,i / n_i
[AR0004 Eq.8]  s²_Δ,i   = ( n_i * Σ_p Δb²_TREE,p,i - (Σ_p Δb_TREE,p,i)^2 ) / ( n_i * (n_i - 1) )
```
Δb_TREE,p,i = plot biomass (t d.m./ha) at occasion 2 minus occasion 1 for the same plot.
t_VAL = two-sided Student t, 90 % confidence, df = n - M (n = total re-measured plots, M = strata).
Equation (5) is unnumbered in the PDF (between Eq.4 and Eq.6); keep the ID `Eq.5`.
If u_ΔC > 10 %: discount ΔC_TREE (Appendix 2).

### 3.3 Proportionate crown cover (section 4.5, ex-ante baseline only)

Applicable only if mean pre-project tree crown cover < 20 % of India's forest threshold crown cover
(30 %) i.e. **< 6 %**.
```
[AR0004 Eq.9]   ΔC_TREE_BSL   = Σ_i ΔC_TREE_BSL,i                         (t CO2e / yr)
[AR0004 Eq.10]  ΔC_TREE_BSL,i = 44/12 * CF_TREE * Δb_FOREST * (1 + R_TREE) * CC_TREE_BSL,i * A_i
```
CF_TREE 0.47; R_TREE 0.25; Δb_FOREST = default mean annual AGB increment in forest of the region
(t d.m. ha-1 yr-1), IPCC GPG-LULUCF Table 3A.1.5 unless justified; CC_TREE_BSL,i fraction measured
once at project start. This gives an annual change directly; Eq.11 does not apply.

### 3.4 Demonstration of "no-decrease" (section 4.6, ex-post only)

ΔC_TREE for a stratum = 0 since last verification if ALL demonstrated: no harvest; no disturbance
(pest, fire) that decreases stock; remote sensing or inventory (incl. participatory) shows crown
cover has not decreased. Store the three evidence items; engine sets 0 with method code `NO_DECREASE`.

## 4. Annual change (section 4.7)

```
[AR0004 Eq.11]  ΔC_TREE,t = ( C_TREE,t2 - C_TREE,t1 ) / T * 1 year     for t1 <= t <= t2
```
T = t2 - t1 in years, need not be integer (4 years 5 months = 4.417). Implementation: compute T
from measurement dates; default `T = days / 365.25`; offer `month_based` (months/12) to reproduce
the PDF example. Allocate per project year pro rata by days when a project year is only partly
inside [t1, t2]. If strata use different methods, C_TREE,t is the sum over strata.

## 5. Stock at a point of time (section 4.8)

Methods: (a) sample plots; (b) growth and stand modelling (ex-ante); (c) proportionate crown cover
(baseline); (d) previous stock + measured change. The **date of the last plot measurement** (or
crown cover estimate) is the date of the estimate, even if fieldwork spans weeks (para 33).

### 5.1 Stratified random sampling (section 4.10)

```
[AR0004 Eq.12]  C_TREE  = 44/12 * CF_TREE * B_TREE
[AR0004 Eq.13]  B_TREE  = A * b_TREE
[AR0004 Eq.14]  b_TREE  = Σ_{i=1..M} w_i * b_TREE,i
[AR0004 Eq.15]  u_C     = t_VAL * sqrt( Σ_i w_i^2 * s_i^2 / n_i ) / b_TREE
[AR0004 Eq.16]  b_TREE,i = Σ_{p=1..n_i} b_TREE,p,i / n_i
[AR0004 Eq.17]  s_i^2   = ( n_i * Σ_p b²_TREE,p,i - (Σ_p b_TREE,p,i)^2 ) / ( n_i * (n_i - 1) )
```
s_i^2 is the sample variance of plot values (the PDF calls it "variance of mean"; it is divided by
n_i in Eq.15). If u_C > 10 %: discount C_TREE (Appendix 2). Plots: systematic with random start
recommended; plot count via the A/R tool "Calculation of the number of sample plots" (not in pack,
see spec 01 section 4).

### 5.2 Double sampling (section 4.11)

Secondary variable x (e.g. basal area, NDVI) measured on all plots; biomass on a sub-sample.
Applicable only if relationship is linear within range. Use Eq.12-15 for aggregation; per stratum
replace Eq.16-17 with:
```
[AR0004 Eq.18]  b_TREE,i = Σ_{p=1..n_i} b_TREE,p,i / n_i + β * ( x̄_all - x̄_sub )
[AR0004 Eq.19]  s_i^2    = ( n_i Σ_p b²_TREE,p,i - (Σ_p b_TREE,p,i)^2 ) / ( n_i (n_i - 1) ) * ( 1 - (1 - α) * ρ^2 )
```
n_i = sub-sample size; α = n_i / (number of plots with x) < 1; β, ρ from Appendix 3 computed on the
sub-sample. The PDF's variable list mislabels β and n_i (E-AR4-03); use the meaning above.
Engine must test linearity (report Pearson ρ and residual plot) and warn if ρ < 0.7 (configurable).

### 5.3 Modelling of growth (paras 49-53, ex-ante only)

Inputs: planting plan (species, density, survival, thinning, pruning schedule), growth curves
(age-diameter, yield tables) adjusted for site. **Not subject to uncertainty control.** Implement as
pluggable growth models: (1) yield-table interpolation by species and site class; (2) user-supplied
age vs AGB curve; (3) Chapman-Richards fit `B(t) = Bmax * (1 - exp(-k t))^c`. Each with source
citation. Output C_TREE_PROJ,t ex-ante by stratum and year.

### 5.4 Proportionate crown cover stock (paras 54-58, baseline pre-project stock)

Applicable if mean pre-project crown cover < 6 % (see 3.3).
```
[AR0004 Eq.20]  C_TREE_BSL   = Σ_{i=1..M} C_TREE_BSL,i
[AR0004 Eq.21]  C_TREE_BSL,i = 44/12 * CF_TREE * b_FOREST * (1 + R_TREE) * CC_TREE_BSL,i * A_i
```
b_FOREST = mean AGB in forest of the region (t d.m./ha, IPCC GPG-LULUCF unless justified);
R_TREE 0.25; CF_TREE 0.47. For slash-and-burn or clearing-regrowing cycles: CC_TREE_BSL = half the
maximum crown cover reached in the cycle (DPT 3).

### 5.5 Update previous stock by measured change (paras 59-61)

```
[AR0004 Eq.22]  C_TREE,t2 = C_TREE,t1 + ΔC_TREE
[AR0004 Eq.23]  u2        = sqrt( (u1 * C_TREE,t1)^2 + (u_ΔC * ΔC_TREE)^2 ) / C_TREE,t2
```
Use undiscounted C_TREE,t1. If u2 > 10 %: discount C_TREE,t2.

## 6. Shrubs (sections 4.12, 4.13, 5.0)

```
[AR0004 Eq.24]  ΔC_SHRUB   = C_SHRUB,t2 - C_SHRUB,t1
[AR0004 Eq.25]  ΔC_SHRUB,t = ( C_SHRUB,t2 - C_SHRUB,t1 ) / T * 1 year
[AR0004 Eq.26]  C_SHRUB,t  = 44/12 * CF_S * (1 + R_S) * Σ_i A_SHRUB,i * b_SHRUB,i
[AR0004 Eq.27]  b_SHRUB,i  = BDR_SF * b_FOREST * CC_SHRUB,i
```
CF_S 0.47; R_S 0.40; BDR_SF 0.10; b_FOREST regional AGB in forest. Strata stratified by shrub crown
cover; strata with cover < 5 % are one stratum with biomass 0 (para 67). Para 68 applies Eq.26-27 to
strata "greater than 5 %"; treat exactly 5 % as included (E-AR4-06). "No decrease" may be applied
to shrubs (para 64). For baseline cyclic land: CC_SHRUB = 0.5 unless justified (DPT 2).

## 7. Appendix 1: plot biomass

Fixed-area plots (same size per stratum, all trees above a minimum dimension measured):
```
[AR0004 App1 Eq.1]  b_TREE,p,i   = B_TREE,p,i / A_PLOT,i                     (t d.m./ha)
[AR0004 App1 Eq.2]  B_TREE,p,i   = Σ_j B_TREE,j,p,i
[AR0004 App1 Eq.3]  B_TREE,j,p,i = Σ_l B_TREE,l,j,p,i
[AR0004 App1 Eq.4]  B_TREE,l,j,p,i = f_j(x1_l, x2_l, ...) * (1 + R_j)                 allometric route
[AR0004 App1 Eq.5]  B_TREE,l,j,p,i = V_TREE,j(x1_l, x2_l, ...) * D_j * BEF2,j * (1 + R_j)   volume route
```
Variable-area (angle-count / relascope) plots:
```
[AR0004 App1 Eq.6]  b_TREE,p,i   = Σ_j b_TREE,j,p,i
[AR0004 App1 Eq.7]  b_TREE,j,p,i = f_j(BA_p,i) * (1 + R_j)
[AR0004 App1 Eq.8]  b_TREE,j,p,i = v_TREE,j(BA_p,i) * D_j * BEF2,j * (1 + R_j)
```
Rules the engine must enforce:
* **Root-shoot ratio default**: `R_j = exp(-1.085 + 0.9256 * ln(b)) / b`, b = above-ground tree
  biomass **per hectare** of the plot (t d.m./ha). Because R depends on plot AGB, compute plot AGB
  first, then R, then total. Coppice: multiply R by max(1, v_HARVEST / v_TREE).
* **Unit-consistent allometry**: each allometric equation is stored with input units, output units
  and valid diameter range; engine converts inputs, evaluates, converts output to t d.m.
  Trees outside the valid range: flag; use sapling procedure (below) or a fallback equation only
  with reviewer approval.
* **Saplings below the allometric range**: count saplings in plot x mean sapling biomass from
  destructive sampling outside plot (note to para 3).
* **D_j** is over-bark density; correct under-bark volume equations to over-bark.
* **BEF2,j**: ex-post conservative default **1.15** unless justified; ex-ante selected by source
  hierarchy (local > national > neighbouring > global). Advisory only (not stated in AR-0004):
  BM-T-AR-0003 DPT1 recommends increasing a closed-canopy BEF by 30 % when applied to open-grown
  trees. Show it as a reviewer prompt; do not apply it automatically.
* Ex-post allometric and volume equations must pass the "Demonstrating appropriateness" tools (not in
  pack): store `appropriateness_status` per equation (`not_tested | passed | failed`), block
  issuance-grade runs if not `passed`, allow draft runs with a warning.

## 8. Appendix 2: uncertainty discount (applies across tools)

When uncertainty U (half-width of 90 % CI / mean, %) > 10 %, move the mean by a fraction of the
half-width, **down** for project quantities, **up** for baseline quantities:

| U | Discount (fraction of half-width) |
|---|---|
| U <= 10 % | 0 |
| 10 < U <= 15 | 0.25 |
| 15 < U <= 20 | 0.50 |
| 20 < U <= 30 | 0.75 |
| U > 30 | 1.00 |

Example: 60 ± 9 (U = 15 %) -> discount 2.25 -> baseline 62.25, project 57.75.
Implementation: `conservative(mean, half_width, scenario)` where scenario in {baseline, project};
the run trace must store both the undiscounted and the discounted value.

## 9. Appendix 3: regression slope and correlation

```
[AR0004 App3 Eq.1]  β = ρ * s_y / s_x
[AR0004 App3 Eq.2]  ρ = Σ (x_i - x̄)(y_i - ȳ) / sqrt( Σ (x_i - x̄)^2 * Σ (y_i - ȳ)^2 )
```

## 10. Monitored parameters

| Parameter | Unit | Frequency | Notes |
|---|---|---|---|
| A_i, A_PLOT,i, plot size | ha | Every verification | National forest inventory SOPs, else handbooks / IPCC GPG |
| CC_SHRUB,i | fraction | Every verification | Ocular, line transect or relascope |
| CC_TREE_BSL,i | fraction | Once at project start | Same methods |
| Tree dimensions (DBH, H, etc.) | as model requires | Each inventory | |

## 11. Defaults (also in `14_parameter_catalogue.yaml`)

CF_TREE 0.47; CF_S 0.47; R_TREE (baseline) 0.25; R_S 0.40; BDR_SF 0.10; BEF2 ex-post 1.15;
India threshold crown cover 30 % -> proportionate-crown-cover limit 6 %; confidence 90 %;
uncertainty threshold 10 %.
