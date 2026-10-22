# 07. BM-T-AR-0006 (printed "BMT-T-AR-0006"): Change in SOC Stocks due to A/R

Status: APPROVED, v1.0, effective 27 March 2025. Source: `/docs/source/BM-T-AR-0006_*.pdf` (12 pp).
Factor-based (IPCC Tier 1 style) estimate. Golden case: `AR0006_soc_tropical_moist_LAC`.

## 1. Applicability (para 4), all must hold per stratum

Land: (i) not wetland; (ii) no organic soils (IPCC GPG-LULUCF glossary); (iii) baseline management
and inputs not in the excluded lists (Table 2 cropland, Table 3 grassland, below).
Project: litter remains on site; soil disturbance (if any) follows soil-conservation practice (e.g.
contours) and is limited to site preparation, not repeated within 20 years.
Note: para 4 joins (i) and (ii) with "or"; implement as AND (all conditions), E-AR6-01.

Assumptions: site preparation and planting within one year; SOC rises from initial level to the
native-vegetation steady state at a constant rate over 20 years from planting.

## 2. Equations

Stratify by climate region and soil type (Table 4), cropland management (Tables 5-6), grassland
management (Table 7). This stratification is for this tool only.
```
[AR0006 Eq.1]  SOC_INITIAL,i = SOC_REF,i * f_LU,i * f_MG,i * f_IN,i                 (t C/ha)
[AR0006 Eq.2]  SOC_LOSS,i    = 0.1 * SOC_INITIAL,i      if project soil disturbance (over and above
                                                         baseline disturbance) > 10 % of stratum area
[AR0006 Eq.3]  SOC_LOSS,i    = 0                         otherwise
[AR0006 Eq.4]  dSOC_t,i = 0                                                  for t <  t_PREP,i
[AR0006 Eq.5]  dSOC_t,i = - SOC_LOSS,i / 1 year                              for t =  t_PREP,i
[AR0006 Eq.6]  dSOC_t,i = ( SOC_REF,i - (SOC_INITIAL,i - SOC_LOSS,i) ) / 20  for t_PREP,i < t <= t_PREP,i + 20
[AR0006 Eq.7]  if dSOC_t,i > 0.8 t C/ha/yr then dSOC_t,i = 0.8
[AR0006 Eq.8]  ΔSOC_AL,t = 44/12 * Σ_i A_i * dSOC_t,i * 1 year                     (t CO2e)
```
* t_PREP,i = year of first soil disturbance in stratum i.
* After t_PREP + 20, dSOC = 0 (steady state reached; implicit, E-AR6-04).
* Eq.7 caps positive rates only; the year-t_PREP loss is not capped.
* The text says values come from "Tables 3-6"; the PDF tables are numbered 4-7 (E-AR6-02). Map by
  content.

## 3. Tables (transcribe exactly into `14_parameter_catalogue.yaml`)

### Table 4: SOC_REF, mineral soils, t C/ha, 0-30 cm (IPCC 2006)

| Climate region | HAC | LAC | Sandy | Spodic | Volcanic |
|---|---|---|---|---|---|
| Boreal | 68 | NA | 10 | 117 | 20 |
| Cold temperate, dry | 50 | 33 | 34 | NA | 20 |
| Cold temperate, moist | 95 | 85 | 71 | 115 | 130 |
| Warm temperate, dry | 38 | 24 | 19 | NA | 70 |
| Warm temperate (moist) | 88 | 63 | 34 | NA | 80 |
| Tropical, dry | 38 | 35 | 31 | NA | 50 |
| Tropical, moist | 65 | 47 | 39 | NA | 70 |
| Tropical, wet | 44 | 60 | 66 | NA | 130 |
| Tropical montane | 88 | 63 | 34 | NA | 80 |

Soil class definitions (WRB / USDA) as in the PDF footnotes (a)-(e); store them as help text and as
a WRB/USDA -> class lookup.

### Table 5: cropland f_LU and f_MG (20-year net effect)

| Factor | Level | Temperature | Moisture | Value |
|---|---|---|---|---|
| f_LU | Long-term cultivated (> 20 yr) | Temperate/Boreal | Dry | 0.80 |
| f_LU | Long-term cultivated | Temperate/Boreal | Moist | 0.69 |
| f_LU | Long-term cultivated | Tropical | Dry | 0.58 |
| f_LU | Long-term cultivated | Tropical | Moist/Wet | 0.48 |
| f_LU | Long-term cultivated | Tropical montane | n/a | 0.64 |
| f_LU | Short-term (< 20 yr) or set aside (< 5 yr) | Temperate/Boreal and Tropical | Dry | 0.93 |
| f_LU | Short-term or set aside | Temperate/Boreal and Tropical | Moist/Wet | 0.82 |
| f_LU | Short-term or set aside | Tropical montane | n/a | 0.88 |
| f_MG | Full tillage | All | All | 1.00 |
| f_MG | Reduced tillage | Temperate/Boreal | Dry | 1.02 |
| f_MG | Reduced tillage | Temperate/Boreal | Moist | 1.08 |
| f_MG | Reduced tillage | Tropical | Dry | 1.09 |
| f_MG | Reduced tillage | Tropical | Moist/Wet | 1.15 |
| f_MG | Reduced tillage | Tropical montane | n/a | 1.09 |

No f_MG is given for **no-till** baselines (E-AR6-03): block the stratum with a clear message unless
a justified value is supplied by the user with evidence (reviewer approval required).

### Table 6: cropland f_IN

| Level | Temperature | Moisture | Value |
|---|---|---|---|
| Low | Temperate/Boreal | Dry | 0.95 |
| Low | Temperate/Boreal | Moist | 0.92 |
| Low | Tropical | Dry | 0.95 |
| Low | Tropical | Moist/Wet | 0.92 |
| Low | Tropical montane | n/a | 0.94 |
| Medium | All | All | 1.00 |
| High without manure | Temperate/Boreal and Tropical | Dry | 1.04 |
| High without manure | Temperate/Boreal and Tropical | Moist/Wet | 1.11 |
| High without manure | Tropical montane | n/a | 1.08 |

("High with manure" is absent because those baselines are excluded by Table 2.)

### Table 7: grassland

| Factor | Level | Climate | Value |
|---|---|---|---|
| f_LU | All permanent grassland | All | 1.00 |
| f_MG | Non-degraded | All | 1.00 |
| f_MG | Moderately degraded | Temperate/Boreal | 0.95 |
| f_MG | Moderately degraded | Tropical | 0.97 |
| f_MG | Moderately degraded | Tropical montane | 0.96 |
| f_MG | Severely degraded | All | 0.70 |
| f_IN | Low/Medium (no fertiliser) | All | 1.00 |
| f_IN | High (direct fertiliser) | All | 1.11 |

### Table 2 (cropland) and Table 3 (grassland): baselines where the tool is NOT applicable

Encode as a rule table `(climate, land_use, management, input) -> not_applicable`. Transcribe all
rows from PDF pages 7-8. Key points: in all climates "high with manure" cropland under most
management types is excluded; Tropical dry short-term/set-aside: full tillage + high with manure,
reduced tillage + medium / high without manure / high with manure, no-till all cases. Grassland:
"Improved" (all inputs) and "Non-degraded" (all inputs) excluded in every climate (Tropical wet
non-degraded: high only); "Moderately degraded + high input" excluded in every climate except
Tropical dry. The engine must evaluate every stratum against these tables and refuse to run the tool
for excluded strata.

## 4. Climate and moisture mapping

Climate region must follow IPCC climate zones (temperature regime + moisture regime). Provide a
lookup helper from site MAT, MAP, PET and elevation; store the chosen zone with evidence. "Moist/Wet"
for tropical means MAP >= 1000 mm (IPCC convention; confirm in project docs).
