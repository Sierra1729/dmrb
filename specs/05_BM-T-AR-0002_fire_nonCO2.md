# 05. BM-T-AR-0002: Non-CO2 GHG Emissions from Burning of Biomass (A/R)

Status: APPROVED, v1.0, effective 27 March 2025. Source: `/docs/source/BM-T-AR-0002_*.pdf` (13 pp).
CO2 from burning is NOT counted here (it is captured as carbon stock change). Golden case:
`AR0002_fire_components`.

## 1. Applicability and accounting threshold

* Applies to all occurrences of fire within the project boundary.
* Account each fire incidence whose burnt area exceeds the minimum area in India's forest definition
  (store as configurable `forest_min_area_ha`; no value is printed in the tool, so confirm India's
  reported forest-definition minimum area with BEE before go-live), **provided
  the accumulated burnt area in the year is >= 5 % of the project area**. If the yearly total is
  < 5 %, GHG_E,t = 0 for that year (record the test).
* Living-tree AGB counts as not burnt (non-significant) if the fire stays in the understory, or it
  singes trees without mortality with leaf regrowth within 6 months (remote-sensing evidence
  allowed). Engine: per fire event flag `tree_biomass_burnt: bool`.
* Assumption: 60 % of dead organic matter is entirely burnt in all fires (stated in para 5b; the
  equations use the 0.07 ratio instead, see E-AR2-04, no extra factor is applied).

## 2. Total

```
[AR0002 Eq.1]  GHG_E,t = GHG_SPF,t + GHG_FMF,t + GHG_FF,t                        (t CO2e)
```

## 3. Fire in site preparation

```
[AR0002 Eq.2]  GHG_SPF,t = 0
    for land where slash-and-burn is common practice in the baseline AND fire was used at least once
    in the 10 years before project start.
[AR0002 Eq.3]  GHG_SPF,t = 0.07 * Σ_{i=1..M} A_SPF,i,t * 44/12 * ( CF_TREE * b_TREE,i + BDR_SF * CF_SHRUB * CC_SHRUB,i * B_FOREST )
    for all other land.
```
0.07 = ratio of non-CO2 (CH4 + N2O) to CO2 emissions from burning (IPCC 2006 Table 2.5 adapted).
CF_TREE 0.50, CF_SHRUB 0.50, BDR_SF 0.10; b_TREE,i = mean pre-project tree biomass (t d.m./ha) from
BM-T-AR-0004, = 0 if pre-project living trees are not burnt; CC_SHRUB,i measured when fire is used;
B_FOREST = regional AGB of forest (source hierarchy: national inventory > neighbouring > global
(FAO) > IPCC GPG-LULUCF).

## 4. Fire to clear harvest residue before replanting

```
[AR0002 Eq.4]  GHG_FMF,t  = 0.07 * 44/12 * B_HARVEST,t * f_BL * CF_TREE
[AR0002 Eq.5]  B_HARVEST,t = B_FOREST / BEF2 * A_FMF,t          (only when harvest biomass data unavailable)
```
f_BL = 0.25 tropical, 0.10 temperate (timber-harvest ratio used for all harvests, conservative);
BEF2 = 1.25; CF_TREE 0.50.

## 5. Forest fire (not site prep, not residue burning)

```
[AR0002 Eq.6]  GHG_FF,t      = GHG_FF_TREE,t + GHG_FF_DOM,t
[AR0002 Eq.7]  GHG_FF_TREE,t = 0.001 * Σ_i A_BURN,i,t * b_TREE,i,tL * COMF_i * ( EF_CH4,i * GWP_CH4 + EF_N2O,i * GWP_N2O )
[AR0002 Eq.8]  GHG_FF_DOM,t  = 0.07 * Σ_{i=1..M} A_BURN,i,t * ( c_DW,i,tL + c_LI,i,tL )
```
* tL = year of the last verification **before** the fire. At the **first verification**, GHG_FF_TREE
  and GHG_FF_DOM are 0 (no prior verified stock).
* b_TREE,i,tL = mean AGB per ha at tL (t d.m./ha); may be 0 if living trees are not burnt.
* DOM stocks must be **per hectare** (t CO2e/ha): `c_DW,i,tL = C_DW,i,tL / A_i` (the PDF defines them
  as stratum totals in t CO2e, which makes Eq.8 dimensionally wrong; E-AR2-03).
* If the project elected at validation not to account dead organic matter, GHG_FF_DOM,t = 0.
* EF and GWP: EF in g gas per kg dry matter; 0.001 converts to t.

Defaults:

| Parameter | Default |
|---|---|
| COMF tropical forest, mean age 3-5 yr | 0.46 |
| COMF tropical forest, 6-10 yr | 0.67 |
| COMF tropical forest, 11-17 yr | 0.50 |
| COMF tropical forest, 18+ yr | 0.32 |
| COMF boreal forest | 0.40 |
| COMF temperate forest | 0.45 |
| (COMF tropical table is misaligned in the PDF; reading above per E-AR2-08; age < 3 yr not tabulated) | |
| EF_CH4 tropical / other forest | 6.8 / 4.7 g/kg d.m. |
| EF_N2O tropical / other forest | 0.20 / 0.26 g/kg d.m. |
| GWP_CH4 / GWP_N2O as printed | 21 / 310 (IPCC SAR) |

**GWP policy (E-GWP-01):** the CCTS Detailed Procedure requires the latest IPCC GWP100. Default
run uses the project's locked GWP set (AR6: 29.8 / 273). Provide `gwp_mode = "tool_as_printed"`
for reproducing the PDF and show both values in the report until BEE clarifies.

## 6. Monitored parameters

| Parameter | Unit | When |
|---|---|---|
| A_SPF,i,t | ha | Whenever fire is used in site preparation |
| CC_SHRUB,i,t | fraction | Same (ocular or line transect) |
| A_FMF,t | ha | Whenever fire clears harvest residue |
| A_BURN,i,t | ha | Whenever a forest fire occurs; GPS delineation on ground or georeferenced remote sensing |

The PDF's description of A_BURN,i,t is copied from A_FMF (E-AR2-02); use "area burnt in stratum i
in year t".

## 7. dMRV hooks

* Fire event register: polygon, date, cause, stratum intersection, tree-mortality assessment,
  6-month regrowth check task, evidence (photos, satellite scene IDs).
* Optional remote sensing: burnt-area polygons (e.g. Sentinel-2 dNBR, MODIS/VIIRS active fire) as
  candidate events requiring field confirmation; never auto-commit without reviewer approval.
