# 06. BM-T-AR-0005: Leakage from Displacement of Pre-project Agricultural Activities (A/R)

Status: APPROVED, v1.0, effective 27 March 2025. Source: `/docs/source/BM-T-AR-0005_*.pdf` (8 pp).
Golden case: `AR0005_leakage_displacement`.

## 1. Scope and applicability

* Applies to all A/R ICM projects. **Not applicable** if displacement is expected to cause,
  directly or indirectly, drainage of wetlands or peat lands (hard block in the UI).
* Leakage = decrease in carbon stocks in pools of the land **receiving** the displaced activity.
  Displacement alone is not leakage. Market (secondary) effects = 0.

## 2. Zero-leakage cases for displaced grazing (para 9)

LK = 0 for grazing if animals go to: (a) existing grazing land within carrying capacity (displaced +
existing); (b) existing non-grazing grassland within carrying capacity; (c) cropland abandoned
within last 5 years; (d) forest land with no clearance or crown-cover decrease; (e) zero-grazing
system. UI: per displacement record, select case and attach carrying-capacity evidence.

## 3. Equations (all other cases)

```
[AR0005 Eq.1]  LK_AGRIC,t   = 44/12 * ( ΔC_BIOMASS,t + ΔSOC_LUC,t )                         (t CO2e)
[AR0005 Eq.2]  ΔC_BIOMASS,t = [ 1.1 * b_TREE * (1 + R_TREE) + b_SHRUB * (1 + R_S) ] * CF * A_DISP,t   (t C)
[AR0005 Eq.3]  ΔSOC_LUC,t   = SOC_REF * ( f_LUP * f_MGP * f_INP - f_LUD * f_MGD * f_IND ) * A_DISP,t  (t C)
```
* 1.1 adds dead wood and litter as a fixed share of living tree carbon.
* CF 0.47; R_TREE 0.25; R_S 0.40 (the extracted PDF text shows 0.471, 0.252, 0.403 because footnote
  markers merge with the numbers; the page images confirm 0.47, 0.25, 0.40; E-AR5-02).
* b_TREE, b_SHRUB = mean AGB of the receiving land (t d.m./ha) via BM-T-AR-0004. If receiving land
  is unidentified: b_TREE = regional mean forest AGB from IPCC GPG-LULUCF unless justified.
* Units: Eq.2 multiplies by CF, so ΔC_BIOMASS is t C (PDF says t d.m., E-AR5-01). ΔSOC_LUC is t C
  (the PDF says t C/ha but multiplies by area).
* ΔSOC_LUC,t = 0 if only grazing is received, or if Eq.3 gives a negative value.
* SOC_REF and f-factors: from BM-T-AR-0006 tables. The PDF cites "Table 3" and "Tables 4, 5, 6";
  in BM-T-AR-0006 the content is in Tables 4 (SOC_REF), 5, 6 and 7 (E-AR5-03). Map by content:
  SOC_REF -> AR-0006 Table 4; cropland f_LU and f_MG -> Table 5; cropland f_IN -> Table 6;
  grassland factors -> Table 7.
* `P` = receiving land before receiving the activity; `D` = after.
* Several receiving-land types in a year: apply Eq.1-3 to each and sum (para 11).

## 4. Monitored parameter

A_DISP,t (ha): area from which agricultural activity is displaced in year t; field measurement per
national forest inventory SOPs; monitored at every verification.

## 5. dMRV hooks

Displacement register per year: source parcel polygon (inside project), activity type (crop,
grazing), receiving land (identified polygon or "unidentified"), receiving-land pre/post land use,
management and input classes (drop-downs bound to AR-0006 factor tables), carrying-capacity data
for grazing, evidence (PRA records, interviews, maps).
