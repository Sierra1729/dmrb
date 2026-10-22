# 09. DRAFT: Soil Organic Carbon Model Requirements and Guidelines ("BM AGXX.XXXX")

Status: **DRAFT**, v1.0, adoption date "XX/XX/2026". Source:
`/docs/source/DRAFT_SOC_Model_Guidelines_and_5_SOC_Activity_Tools.pdf`, PDF pages 1-60.
Complements the **SOC Framework Methodology (SOC FM)**, which is **not in the pack** (E-SOC-00).
Golden cases: `SOCMG_*`.

Note: sections 3.1-3.2 of the draft were copy-pasted from a fossil-fuel tool (they talk about fuel
combustion). Ignore them; scope is SOC modelling on agricultural land (E-SOCMG-01).

## 1. Quantities from the SOC FM quoted in the guidelines

```
[SOCFM Eq.1]  ER_t-0     = [ ( ΔC_SOC,t-0 * 44/12 ) - PE_t-0 - LK_t-0 ] * (1 - BUF)       (t CO2e)
[SOCFM Eq.2]  ΔC_SOC,t-0 = ( SOC_t - SOC_0 ) * (1 - UD)                                   (t C)
```
* Baseline (default static): SOC_0 = SOC_BL = SOC stock in project boundary at project start,
  equilibrium assumed under business-as-usual (last 5 years' practices).
* UD = uncertainty deduction (SOC FM Section 9, Eq.8-11, not in pack); BUF = buffer (SOC FM, not in
  pack). Implement as pluggable functions that **raise NotImplementedForIssuance** until the SOC FM
  is supplied; allow a user-entered placeholder for internal estimates, stamped DRAFT.
* t-values for SOC FM Eq.8 (Annex C, "Table 6 from the SOC FM") equal the one-sided 95 % Student t
  with df = n_p - 1 (e.g. n = 3 -> 2.920; n >= 200 -> 1.6525). Compute with scipy; keep the table as
  a regression test.

## 2. Three estimation strategies (SOC FM Approach 1 vs 2)

| Strategy | SOC FM approach | Model validation required |
|---|---|---|
| Design-based (sampling); a model may only inform strata and sample size | Approach 1 | No |
| Model-assisted (regression estimator on top of probability sample) | Approach 1 | No |
| Model-based (model predicts mean/total stocks) | Approach 2 | **Yes, strict** (sections 4-6 below) |

Approach 3 (IPCC default factors) is outside these guidelines.

Process gates the software must enforce:
* Modelling objectives submitted to the ICM Administrator **before** the calculation period starts.
* For model-based estimation: calibration + validation report submitted before the calculation
  period; model predictions submitted **before** validation/verification soil sampling; official
  validation only with samples taken **after** predictions were submitted (store submission
  timestamps; block if sample dates precede the prediction submission).
* Reproducibility: model name, version, input data, parameters, random seeds stored; ACVA can rerun.

## 3. Data requirements

### 3.1 SOC stock calculation (Table 2)

As printed:
```
[SOCMG Eq.3a]  FSS        = mass_finesoil[g] / volume_sample[cm3] * depth[cm] * 0.01        "(t/ha)"
[SOCMG Eq.3b]  SOC_stock  = SOC_con_finesoil[%] * FSS                                        "(t/ha)"
[SOCMG Eq.4]   SOC_stock  = SOC_con_finesoil[%] * BD_finesoil[g/cm3] * depth[cm] * (1 - CFR) "(t/ha), CFR in %"
[SOCMG Eq.5a]  M_SOIL(DL) = mass_SAMPLE(DL)[g] / ( π (D/2)^2 * N ) * 1000                    "(Mg/ha), D in mm"
[SOCMG Eq.5b]  M_OC(DL)   = M_SOIL(DL)[Mg/ha] * C_OC(DL)[g/kg]                               (kg/ha)
```
Implement (unit-correct, E-SOCMG-02):
```
FSS [t/ha]        = mass_finesoil[g] / volume_sample[cm3] * depth[cm] * 100
SOC_stock [t C/ha] = SOC[%] / 100 * FSS                       (equivalently SOC[%] * m/V * depth)
SOC_stock [t C/ha] = SOC[%] * BD[g/cm3] * depth[cm] * (1 - CFR/100)        (CFR entered in %)
M_SOIL [Mg/ha]    = mass_sample[g] / (π (D/2)^2 [mm2] * N) * 10 000        (D in mm)
M_OC [kg/ha]      = M_SOIL [Mg/ha] * C_OC [g/kg]
```
Check: 1 % SOC, BD 1.3 g/cm3, 30 cm, CFR 0 -> 39 t C/ha. The printed 0.01 in Eq.3a and 1000 in
Eq.5a do not give t/ha or Mg/ha; use pint, unit tests against these hand values, and show the
discrepancy note in reports.
* **Equivalent soil mass** (Wendt & Hauser 2013) must be applied when comparing time points
  (also required by the activity tools: if project BD increases, reduce layer depth
  proportionally). Implement cumulative-mass interpolation: compare SOC to a fixed reference soil
  mass per layer, not a fixed depth.
* Harmonisation: common depth intervals (e.g. 0-30 cm) via depth-weighted averaging or
  pedotransfer functions; unit harmonisation; document lab method (Walkley-Black vs dry combustion)
  and apply published correction factors where used; full metadata per sample.

### 3.2 Representativeness, independence, sampling units

* Validation data in t C/ha; sampled over the stated depth; directed stratified sampling with
  composites (SOC FM 14.2 or FAO GSOC-MRV Annex 3.2).
* Sampling unit must be nested in the prediction unit; if not, aggregate the finer to the coarser
  before computing metrics. A model is validated only at the granularity of its validation data.
* Calibration and validation sets: mutually exclusive; **min distance 30 m** between any
  validation and calibration point; all depths/time points of one location go to the same set.
  Report min distance and CRS; provide a geospatial file of point locations (values may be withheld).
* Validation data sources and **safety discount** added to UNC:

| Source | Description | Safety discount |
|---|---|---|
| A | Direct measurements within project area | 0 % |
| B | Similar reference sites adjacent, same management change, same spatial/temporal extent | 10 % |
| C | Similar sites not adjacent, same management change and extent | 30 % |
| D | Similar sites not adjacent, same change, different extent | 50 % |

Only Source A is allowed for **verification**.

### 3.3 Sample size (Box 5)

```
[SOCMG Eq.6]  n = z_{α/2}^2 * s^2 / MoE^2        (paired; s^2 = variance of SOC change)
[SOCMG Eq.7]  n = z_{α/2}^2 * s^2 / MoE^2        (independent; s^2 = spatial variance of stock)
```
α = 0.1 (90 % CI), z = 1.645. Round up. Recommend computing this even for model-based projects.

### 3.4 Time-series data (Box 6)

Fixed locations, at least 5-year intervals, composites within a recorded radius >= GNSS accuracy,
same protocol/devices/personnel, equivalent soil mass, duplicates and calibration QC.

## 4. Validation metrics (Table 3)

Let X_i observed, X̂_i predicted, n points.
```
[Eq.12]  X̂_bar = (1/n) Σ X̂_i
[Eq.13]  X_bar = (1/n) Σ X_i
[Eq.14]  s^2   = 1/(n-1) Σ (X_i - X_bar)^2
[Eq.15]  s     = sqrt(s^2)
[Eq.16]  r_i   = X̂_i - X_i
[Eq.17]  Bias  = (1/n) Σ r_i = X̂_bar - X_bar
[Eq.18]  RMSE  = sqrt( (1/n) Σ r_i^2 )
[Eq.19]  R^2   = 1 - Σ (X̂_i - X_i)^2 / Σ (X_bar - X_i)^2
[Eq.20]  SE    = sqrt( s^2 / n )
[Eq.21]  MoE   = SE * t_{(1-0.9)/2, n-1}                    (two-sided 90 %: |t| = t_{0.95, n-1})
[Eq.22]  I_{1-α}(X̂_i) = [a_i, b_i]                         (model-specific prediction interval)
[Eq.23a] PICP  = (1/n) Σ δ(a_i <= X_i <= b_i)
[Eq.23b] δ(t)  = 1 if true else 0
[Eq.24]  s_PICP = sqrt( 1/(n-1) Σ ( δ_i - PICP )^2 )
[Eq.25]  t     = ( PICP - 0.9 ) / ( s_PICP / sqrt(n) )
```
Pass criteria (paras 76-77, 91): |Bias| <= MoE; RMSE < s; R^2 > 0. PICP: report; the draft gives
the statistic but no critical value: default rule "fail if t < -t_{0.90, n-1}" (one-sided test at
10 %), configurable, flagged (E-SOCMG-04). The draft's Example E1.1 shows a half-width of 2.36 for
SE 1.19 (n = 93), which matches 95 %, not 90 %; follow Eq.21 (E-SOCMG-03).

Required report content per modelling unit: Bias table (n, mean prediction, validation mean, SE,
MoE, Bias, optional t-distribution plot); RMSE/R^2 table (n, s, RMSE, R^2); regression plot
(observed on y, predicted on x, fitted line + 1:1) and residual plot (residuals vs predicted + y=0);
heteroscedasticity check and treatment; full prediction/observation data (identifiers may be
withheld).

### 4.1 Cross-validation (Annex B)

At least 5 folds (10 recommended); >= 20 points per fold (LOOCV exception); >= 100 points overall for
calibration; no point in two folds; min distance between points in different folds > 30 m. Report a
fold x fold minimum-distance matrix (or, for LOOCV, the min distance between any two points) and CRS.

## 5. Predictions and uncertainty (section 5.2)

* Outputs: SOC stock prediction for every prediction unit of every modelling unit, and the project
  mean, each with a two-sided 90 % interval (confidence, prediction or credible interval as fits
  the model). Account for spatial, temporal and spatio-temporal autocorrelation.
* Methods: Monte Carlo (process models, credible intervals), bootstrap (confidence intervals),
  quantile regression / QRF / conformalised QR (prediction intervals).
* **UNC** = half-width of the interval around the SOC stock change / total SOC stock change
  estimate (SOC FM Ch.9 Eq.11). **TU = UNC + safety discount** (section 3.2 table). Then continue
  with SOC FM Ch.9 Step 4 (not in pack).

### 5.1 Annex A worked approach: DSM with linear residual trend (Table A.6)

Requires probability samples (SRS or stratified SRS with proportional allocation; independent
locations at each time step).
```
[Eq.26]  e_n      residuals of validation data (observed - predicted per Annex A usage; keep the
                  sign convention explicit in code and report)
[Eq.27]  t_n      sampling times
[Eq.28]  ē = (1/N) Σ e_n
[Eq.29]  t̄ = (1/N) Σ t_n
[Eq.30]  μ_pred(t)  model mean prediction over project area at time t (mean of DSM)
[Eq.31]  β̂1 = Σ (t_n - t̄)(e_n - ē) / Σ (t_n - t̄)^2
[Eq.32]  β̂0 = ē - β̂1 * t̄
[Eq.33]  σ̂²_resid = 1/(N-2) Σ ( e_n - (β̂0 + β̂1 t_n) )^2
[Eq.34]  μ̂_Δ(t, t') = μ_pred(t') - μ_pred(t) + (t' - t) * β̂1
[Eq.35]  MoE = T_{α/2, N-2} * sqrt( (t' - t)^2 / Σ (t_n - t̄)^2 * σ̂²_resid )
```
If validation data exist for only one time point and SOC was at equilibrium for e.g. 5 years before
start, split residuals 50:50 at random and treat half as sampled 5 years earlier.

## 6. Verification (section 5.3)

* Data Source A only; independent of calibration and validation; criteria as section 4.
* At least every 5 years.
* On failure: notify ICM Administrator and ACVA immediately; 90 days for root cause, recalibration,
  revalidation including the failed verification data; else switch to direct measurement
  (Approach 1) until a new model version validates. Over/under-crediting handled per the
  performance-shortfall guideline (not in pack).

## 7. Required outputs and monitored parameters

Project context geospatial file (one row per farm/parcel): unique id, name/address/owner,
exact boundaries of total and eligible area (WKT, single-digit-metre accuracy or report accuracy),
crediting period dates, modelling objective, modelling unit, IPCC 2019 climate zone, soil texture
and clay %, vegetation type, current land use, management history.

Monitored: ΔC_SOC,t-0 (Mg), SOC_t (Mg), UD (ratio), M_OC(DL)/SOC stock (Mg/ha), M_SOIL(DL) (Mg/ha),
C_OC(DL)/SOC_con (%), FSS (Mg/ha), BD (g/cm3, intact core), n, α, X_i, s^2, X_bar, SE, X̂_i, r_i,
Bias, RMSE, R^2, every calculation period. Model selection log: all model classes considered and
reasons for dismissal.
