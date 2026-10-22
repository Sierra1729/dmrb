# 04. BM-T-AR-0003: Carbon Stocks and Change in Dead Wood and Litter (A/R)

Status: APPROVED, v1.0, effective 27 March 2025. Source: `/docs/source/BM-T-AR-0003_*.pdf` (22 pp).
No internal applicability conditions. Golden cases: `AR0003_*`.

## 1. Outputs

| Symbol | Unit | Meaning |
|---|---|---|
| C_DW,t | t CO2e | Dead wood carbon stock in project boundary at a point of time in year t |
| ΔC_DW,t | t CO2e | Change in dead wood carbon stock in year t |
| C_LI,t | t CO2e | Litter carbon stock |
| ΔC_LI,t | t CO2e | Change in litter carbon stock in year t |

Notation with scenario: `C_DW_BSL,t`, `C_LI_BSL,t`, `ΔC_DW_BSL,t`, `ΔC_LI_BSL,t`, and `_PROJ` analogues.
Assumptions: linear change between estimates; root-shoot ratios valid for dead trees. Same strata
and plots as living trees unless a different stratification is justified.

## 2. Dead wood: measurement-based method

Types: standing dead wood (incl. uprooted trees lying on ground, not extracted) and lying dead wood.

### 2.1 Standing dead trees: categories and biomass reduction factor α_k

| Category | α_k |
|---|---|
| Lost only leaves and twigs | 0.975 |
| Lost leaves, twigs and small branches (< 10 cm) | 0.80 |
| Any other dead tree or stump | Use stump / decay-class method (2.3) |

(The PDF's paragraph cross-references "paragraph 14" and "paragraphs 23-27" are off by two; the
categories are in para 12 and the stump method in paras 20-24. See E-AR3-03.)

BEF route:
```
[AR0003 Eq.1]  B_DWS_TREE,j,p,i,t = D_j * BEF2,j * (1 + R_j) * Σ_{k=1..n} ( V_TREE,j(DBH_k, H_k) * α_k )
```
The PDF prints `(1 + D_j)`; implement `(1 + R_j)` (E-AR3-01).

Allometric route:
```
[AR0003 Eq.2]  B_DW_TREE,j,p,i,t = (1 + R_j) * Σ_{k=1..n} ( f_j(DBH_k, H_k) * α_k )
[AR0003 Eq.3]  C_DWS_TREE,j,p,i,t = 44/12 * CF_TREE * B_DWS_TREE,j,p,i,t
```
Volume and allometric equations must pass the appropriateness tools (store status as in spec 03).

### 2.2 Stumps (decay classes by machete test)

| Decay class | Density reduction factor β |
|---|---|
| Sound (blade bounces) | 1.00 |
| Intermediate (blade enters slightly) | 0.80 |
| Rotten (wood falls apart) | 0.45 |

Measurement: stump height < 4 m -> measure mid-height diameter directly. Stump height >= 4 m ->
measure DBH and estimate mid-height diameter:
```
[AR0003 Eq.4]  D_MID_STUMP = 0.57 * DBH_k * ( H_STUMP / (H_STUMP - H_DBH) )^0.80      for H_STUMP >= 4 m
[AR0003 Eq.5]  C_DW_STUMP,j,p,i,t = 44/12 * CF_TREE * D_j * (1 + R_j) * (π/4) * Σ_k ( D_MID_STUMP,k^2 * H_k * β_k )
```
Units: D_MID and H in m, D_j in t d.m./m3. Operator precedence in Eq.4 is shown ambiguously in the
PDF (E-AR3-02); the form above follows the Ormerod bole model the tool cites.

### 2.3 Lying dead wood (line-intersect, Harmon and Sexton 1996)

Two transects, total length >= 100 m, roughly orthogonal, bisecting at plot centre; if parcel too
small, more lines allowed, parallel lines >= 20 m apart. Measure every piece with diameter >= 10 cm
crossing a line; assign decay class (β as in 2.2).
```
[AR0003 Eq.6]  C_DWL,j,p,i,t = a_plot * 44/12 * CF_TREE * D_j * ( π^2 / (8 L) ) * Σ_{n=1..N} ( D_n^2 * β_n )
```
a_plot in ha, L in m, D_n in cm (π² Σ D² / 8L gives m3/ha with these units).

### 2.4 Aggregation

```
[AR0003 Eq.7]  C_DW,i,t = A_i / A_PLOT,i * Σ_p Σ_j ( C_DWS_TREE,j,p,i,t + C_DW_STUMP,j,p,i,t + C_DWL,j,p,i,t )
[AR0003 Eq.8]  C_DW,t   = Σ_i C_DW,i,t
```
A_PLOT,i = total area of sample plots in stratum i.

## 3. Dead wood: conservative default-factor method

Only if dead wood remains in situ and is not removed by any anthropogenic activity.
```
[AR0003 Eq.9]  C_DW,i,t = C_TREE,i,t * DF_DW / 100
```
C_TREE,i,t from BM-T-AR-0004. DF_DW (per cent):

| Biome | Elevation | Precipitation | DF_DW |
|---|---|---|---|
| Tropical | < 2000 m | < 1000 mm/yr | 2 % |
| Tropical | < 2000 m | 1000-1600 mm/yr | 1 % |
| Tropical | < 2000 m | > 1600 mm/yr | 6 % |
| Tropical | > 2000 m | All | 7 % |
| Temperate/boreal | All | All | 8 % |

## 4. Change in dead wood

```
[AR0003 Eq.10]  dC_DW,(t1,t2) = ( C_DW,t2 - C_DW,t1 ) / T
[AR0003 Eq.11]  ΔC_DW,t       = dC_DW,(t1,t2) * 1 year        for t1 <= t <= t2
```
T fractional allowed (same date handling as spec 03 section 4).

## 5. Litter: measurement-based method

Per plot: four frame samples at random positions, mixed into one composite; weigh wet; oven-dry a
sub-sample for dry-to-wet ratio (DWR).
```
[AR0003 Eq.12]  C_LI,p,i,t = 44/12 * CF_LI * 2.5 * ( A_p,i / a_p,i ) * B_LI_wet,p,i * DWR_LI,p,i
[AR0003 Eq.13]  C_LI,i,t   = A_i / A_PLOT,i * Σ_p C_LI,p,i,t
[AR0003 Eq.14]  C_LI,t     = Σ_i C_LI,i,t
```
CF_LI 0.37; A_p,i plot area in ha; a_p,i frame area in m2 (often 0.50 m2); B in kg. The factor 2.5
combines kg to t, ha to m2 and the four frames. Validation: exactly 4 frames per composite,
otherwise generalise 2.5 to `10 / n_frames` and raise a QA warning.

## 6. Litter: default-factor method

Only if litter remains in situ and is not removed.
```
[AR0003 Eq.15]  C_LI,i,t = C_TREE,i,t * DF_LI / 100
```

| Biome | Elevation | Precipitation | DF_LI |
|---|---|---|---|
| Tropical | < 2000 m | < 1000 mm/yr | 4 % |
| Tropical | < 2000 m | 1000-1600 mm/yr | 1 % |
| Tropical | < 2000 m | > 1600 mm/yr | 1 % |
| Tropical | > 2000 m | All | 1 % |
| Temperate/boreal | All | All | 4 % |

## 7. Change in litter

```
[AR0003 Eq.16]  dC_LI,(t1,t2) = ( C_LI,t2 - C_LI,t1 ) / T
[AR0003 Eq.17]  ΔC_LI,t       = dC_LI,(t1,t2) * 1 year       for t1 <= t <= t2
```

## 8. Parameters

Not measured: BEF2,j (IPCC GPG-LULUCF unless justified; +30 % advisory for open-grown trees);
CF_TREE **0.5** in this tool (AR-0004 uses 0.47, see E-CF-01); CF_LI 0.37; D_j (IPCC GPG-LULUCF);
DF_DW and DF_LI tables; R_j = exp(-1.085 + 0.9256 ln A)/A, A = AGB t d.m./ha.

Measured (monitoring every 5 years since initial verification): A_i, A_PLOT,i, a_p,i,
B_LI_wet,p,i, DBH, D_n, H; T recorded (fractional if months differ).
