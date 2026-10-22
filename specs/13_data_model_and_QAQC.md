# 13. Data Model, Field Data Templates and QA/QC Rules

## 1. Core hierarchy (multi-tenant)

```
Organization (our consultancy)
 └─ Client (non-obligated entity)
     └─ Project  [project_type, methodology_code+version (locked), tool versions (locked),
                  GWP set (locked), start date, crediting period(s), status, ICM ids]
         ├─ ProjectInstance / Site  [geometry MultiPolygon (EPSG:4326), district, state]
         ├─ Stratum / ModellingUnit [scenario BSL|PROJ, geometry, area (geodesic), attributes JSONB
         │                           typed per project type, valid_from, valid_to]
         │    └─ SamplingUnit: Plot | Field | Transect | Chamber | SoilCore ...
         │          └─ Measurement events (typed tables below)
         ├─ Facility (SWDS, digester, flare, plant)  └─ Instrument (meter, analyser) └─ TimeSeries
         ├─ Event registers: FireEvent, HarvestEvent, DisplacementRecord, TillageEvent, InputApplication
         ├─ AdditionalityAssessment (BM-T-001 workflow state, evidence)
         ├─ MonitoringPeriod [start, end, crediting_period_no]
         │    └─ CalculationRun [run_type ex_ante|ex_post|draft, input_snapshot_hash, param_set_hash,
         │                       engine_version, git_sha, methodology_version, status, outputs JSONB,
         │                       trace (equation-level lineage), warnings, errata_applied]
         │         └─ Report (PDD annex, MR tables, ER workbook, validation report)
         └─ Evidence (file in object store, sha256, uploaded_by, captured_at, GPS, linked entities)
```
Every table: `id UUID`, `created_at`, `created_by`, `updated_at`, `version` (optimistic locking),
soft-delete only, full audit log (who / what / before / after). Measurements are append-only;
corrections create a new row that supersedes the old one with a reason code.

## 2. Parameter provenance (applies to every input value)

```
ParameterValue {
  symbol, tool_code, scenario, scope (project|stratum|plot|facility|global),
  value, unit, uncertainty (SE or CI, optional), valid_from, valid_to,
  source_type: measured | project_specific_justified | national_default | ipcc_default | tool_default,
  source_citation (document, page, table/equation), evidence_ids[],
  approved_by, approved_at, conservativeness_note
}
```
Resolution order: measured > project-specific justified (approved) > tool default. A
non-default value without approval cannot be used in an issuance-grade run.

## 3. Field data templates (CSV / XLSX import and XLSForm for ODK/KoboToolbox)

All templates: UTF-8, ISO dates (YYYY-MM-DD), decimal point ".", WGS84 lat/lon with accuracy (m),
surveyor id, device id, photo ids. Headers below; files with examples in `/templates`.

| Template | Key columns |
|---|---|
| `strata.csv` | stratum_id, project_id, scenario, name, area_ha_declared, geometry_wkt, climate_zone, soil_class, land_use, management, input_level, crown_cover_tree, crown_cover_shrub, notes |
| `plots.csv` | plot_id, stratum_id, plot_type (fixed\|variable), shape, radius_m or side_m, plot_area_ha, center_lat, center_lon, gps_accuracy_m, permanent (y/n), measurement_date, team_id |
| `trees.csv` | plot_id, tree_no, species_code, status (live\|dead_leaves_twigs\|dead_small_branches\|dead_other), dbh_cm, height_m, diameter_type (dbh\|rcd\|basal), coppice (y/n), multi_stem_id, remarks |
| `stumps.csv` | plot_id, stump_no, species_code, height_m, dbh_cm (if >= 4 m), mid_diameter_cm (if < 4 m), decay_class (sound\|intermediate\|rotten) |
| `deadwood_transects.csv` | plot_id, line_no, line_length_m, piece_no, species_code, diameter_cm (>= 10), decay_class |
| `litter_samples.csv` | plot_id, sample_date, n_frames, frame_area_m2, composite_wet_kg, subsample_wet_g, subsample_dry_g |
| `shrub_cover.csv` | stratum_id, method (ocular\|line_transect\|relascope), crown_cover_fraction, date |
| `species_params.csv` | species_code, scientific_name, wood_density_t_m3, bef2, root_shoot_method (formula\|value), root_shoot_value, allometric_eq_id, volume_eq_id, source_citation |
| `allometric_equations.yaml` | id, species_codes, form (python expression over named inputs), inputs with units, output unit (AGB), valid_dbh_cm [min,max], source, appropriateness_status |
| `fire_events.geojson` | event_id, date, cause, type (site_prep\|residue\|forest_fire), tree_biomass_burnt (y/n), regrowth_check_date, evidence_ids |
| `displacement.csv` | record_id, year, source_parcel_id, activity (crop\|grazing), area_ha, receiving_land_id or "unidentified", zero_leakage_case (a-e or none), receiving_pre/post land_use, management, input |
| `swds_sites.csv` | site_id, managed (y/n), management_features, depth_m, water_table_present (y/n), climate MAT_C, MAP_mm, PET_mm, start_year |
| `waste_deliveries.csv` | site_id, date, ticket_no, weighbridge_id, waste_stream, mass_t_wet, vehicle_no |
| `waste_composition_samples.csv` | sample_id, site_id, date, total_mass_kg, food_kg, paper_cardboard_kg, textiles_kg, garden_park_kg, wood_kg, inert_kg, other_kg (+ mapping of "other" to a tool waste type) |
| `bmp_tests.csv` | sample_id, waste_type, lab, method_standard, sample_mass_g, bmp_t_ch4_per_t, test_end_date |
| `lfg_timeseries.csv` | instrument_id, timestamp, flow_m3, ch4_vol_frac, temperature_c, pressure_kpa, flare_status, normalised (y/n) |
| `farms.csv`, `fields.geojson` | farm_id, owner (pseudonymised id), consent_id, field_id, geometry, eligible_area_ha, modelling_unit |
| `management_records.csv` | field_id, season, crop, sowing_date, harvest_date, yield_kg_ha, tillage_events, cover_crop_species, seed_kg_ha, n_fert_kg, organic_inputs, fuel_l by machine type, electricity_kwh by source, agrochemicals_kg by product |
| `soil_samples.csv` | sample_id, field_id, lat, lon, gps_accuracy_m, date, depth_top_cm, depth_bottom_cm, composite_n_cores, core_diameter_mm, fine_soil_mass_g, sample_volume_cm3, bd_g_cm3, cfr_pct, soc_pct, method (dry_combustion\|walkley_black), lab_id, lab_se, calibration_or_validation |

## 4. QA/QC rule catalogue (minimum set; implement as declarative rules with severity)

Severity: ERROR blocks issuance-grade runs; WARNING requires reviewer acknowledgement; INFO logged.

Forestry
* DBH within species allometric valid range (else WARNING; sapling procedure suggested).
* Height-DBH plausibility per species (robust regression; residual > 3 MAD -> WARNING).
* Duplicate tree numbers within plot (ERROR). Missing species code (ERROR).
* Plot centre inside its stratum polygon (ERROR) and inside project boundary (ERROR).
* Plot area equals the stratum's design plot size ± 1 % (WARNING); variable-area plots require BAF.
* Measurement date inside the monitoring period window (ERROR).
* Remeasured permanent plots: same plot id, location within 10 m (WARNING).
* Growth plausibility: per-plot AGB decrease without a recorded disturbance (WARNING).
* Lying dead wood diameter >= 10 cm; transect total length >= 100 m per plot (ERROR); parallel lines
  >= 20 m apart (WARNING).
* Litter: n_frames = 4 (WARNING otherwise); dry <= wet (ERROR).
* Uncertainty > 10 % -> discount applied (INFO with values).

Waste
* Composition fractions sum to 1 ± 0.01 (ERROR).
* At least 3 composition samples per quarter for Application B multi-type waste (ERROR).
* Weighbridge calibration certificate valid on delivery date (ERROR if expired).
* Daily mass outliers (> 3 MAD from rolling median) (WARNING).
* LFG CH4 fraction in [0, 1]; flow non-negative; timestamps monotonic; gaps > 1 h flagged; flare
  not operating -> destroyed methane 0 for that interval (ERROR-level rule, not just a flag).
* Instrument calibration (NABL) valid (ERROR).

Agricultural SOC
* Calibration vs validation sets: min distance >= 30 m (ERROR); no shared locations (ERROR).
* Sample depth intervals cover the declared depth (ERROR); equivalent-soil-mass inputs present when
  comparing time points (ERROR).
* Sampling before significant organic inputs / tillage in the season (WARNING with evidence).
* Same season / time of year across rounds (WARNING).
* Zero-tillage fields: no tillage event recorded (ERROR on any).
* Baseline records: 5 years available per field, else stratum-average justification (WARNING); missing
  documentation -> 50 % cap rule applied (INFO).
* Model predictions submitted before validation sampling dates (ERROR).

General
* Units present and convertible for every numeric input (ERROR).
* Parameter values from non-default sources need approval (ERROR in issuance runs).
* Evidence attached where the spec requires it (ERROR in issuance runs).

## 5. Privacy and security

* Farmer and landowner personal data falls under India's Digital Personal Data Protection Act, 2023:
  store consent records, pseudonymise in analytics and ACVA exports, role-based access, purpose
  limitation, deletion workflow that preserves audit integrity (pseudonymise rather than delete
  monitoring data needed for retention).
* Roles: OrgAdmin, ProjectManager, FieldSurveyor (mobile, own submissions), DataReviewer (QA/QC),
  CarbonAnalyst (runs), ClientViewer (read-only own projects), ACVAAuditor (time-boxed read-only with
  download of reproducibility bundle).
* Evidence files hashed (SHA-256) at upload; hashes in every report; optional periodic hash anchoring
  (e.g. a signed daily manifest) for tamper evidence.
