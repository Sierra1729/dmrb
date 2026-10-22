# MASTER BUILD PROMPT: {{PRODUCT_NAME}} dMRV and Carbon Accounting Platform (Indian Carbon Market)

> Paste everything below the horizontal rule into the Antigravity agent (Planning mode). The workspace must
> contain this whole pack: `specs/`, `reference/`, `templates/`, `docs/source/`, `.agent/`.
> Replace `{{PRODUCT_NAME}}` and `{{FIRM_NAME}}` first.

---

## 0. Your role

You are the lead engineer building **{{PRODUCT_NAME}}**, the in-house digital MRV (dMRV) and carbon
accounting platform of **{{FIRM_NAME}}**, a carbon consultancy in India. Our analysts use it to
collect, check and compute project data, and to produce the calculation evidence that goes into
PDDs and Monitoring Reports for projects under the **Offset Mechanism of India's Carbon Credit Trading
Scheme (CCTS)**. The Administrator is the **Bureau of Energy Efficiency (BEE)**; verification is by
**ACVAs**.

The calculation logic must follow the Government of India methodologies and methodological tools
exactly. Those documents are in `docs/source/`. Their implementation-ready restatement, with every
error found in them and the resolution to implement, is in `specs/`. **The specs are your single
source of truth for calculations.** If a spec and a PDF disagree, stop and ask; do not pick one
silently.

## 1. Reading order before you write any code

1. `specs/00_INDEX.md`, `specs/01_regulatory_context.md`
2. `specs/12_errata_register.md` (read fully: it changes how you read the other specs)
3. Tool specs `02`-`10`, then `11_project_type_modules.md`
4. `specs/13_data_model_and_QAQC.md`, `specs/14_parameter_catalogue.yaml`
5. `reference/golden_cases.py` and `reference/golden_cases.json`
6. `.agent/rules/` (non-negotiables) and `.agent/workflows/`

Then produce, as Antigravity artifacts, before coding:
* an **implementation plan** following the phases in section 12,
* a **task list** per phase with acceptance criteria copied from section 12,
* a list of **open questions** for me (anything ambiguous or missing that blocks a phase).

## 2. Non-negotiable principles

1. **Fidelity.** Implement each equation exactly as written in the spec, with the equation ID in code
   (e.g. `[AR0004 Eq.15]`). Where the spec gives an errata resolution, implement the resolution behind
   the named config flag, default as stated, and list the errata ID in every report that used it.
2. **No invented numbers.** Every default value comes from `specs/14_parameter_catalogue.yaml` with
   its citation. If a value you need is not there, add a `TODO(PARAM)` that raises at runtime and ask
   me. Never guess emission factors, densities, allometric coefficients or defaults.
3. **Conservativeness.** Whenever a methodology allows a choice, the engine offers it, but the default
   is the option that gives fewer credits. Uncertainty discounts per BM-T-AR-0004 Appendix 2 are applied
   automatically where the tools require them.
4. **Traceability.** Every number in a report can be traced to: equation ID, input values with units,
   parameter source (measured / justified / default with citation), evidence files (SHA-256), data
   snapshot, engine version and git SHA. One click from a report cell to its lineage.
5. **Reproducibility.** A calculation run is immutable. Re-running the same snapshot with the same
   engine version gives bit-identical outputs. ACVAs can download a reproducibility bundle (inputs,
   parameters, engine version, outputs, trace) and re-run it with a CLI.
6. **Units everywhere.** Use `pint` in the engine. No bare floats cross a module boundary without a
   unit. Unit errors are build failures, not warnings.
7. **Draft gating.** Modules built from DRAFT documents (SOC Model Guidelines and the five SOC activity
   tools) run only in "draft" mode and stamp every output **"DRAFT METHODOLOGY: NOT VALID FOR
   ISSUANCE"**. Issuance-grade runs are blocked for them and for any methodology with `[VERIFY]`
   equations still unverified.
8. **Separation.** The calculation engine (`packages/dmrv_core`, `packages/methodologies`) is pure
   Python with no database, web or file I/O. Everything else calls it.
9. **Security and privacy.** Multi-tenant isolation, RBAC, audit log on every write, India DPDP Act
   2023 handling for farmer and landowner data (consent, pseudonymisation, purpose limitation).

## 3. Scope

### 3.1 Project types (one methodology plugin each)

| ID | Project type | Methodology | Tools | Phase |
|---|---|---|---|---|
| P1 | Afforestation / reforestation (non-wetland) | BM FR05.002 | BM-T-001, BM-T-AR-0002..0006 | 2 |
| P2 | Mangrove A/R | BM FR05.001 | BM-T-001, BM-T-AR-0002..0005, mangrove SOC default | 3 |
| P3 | Landfill gas flaring / use; landfill methane recovery | BM WA03.002, WA03.001 | BM-T-001, BM-T-011 (+T-002..006 when added) | 3 |
| P4 | Agricultural soil carbon (DRAFT) | SOC FM (missing) + 5 activity tools | SOC Model Guidelines | 4 |
| P5 | Rice cultivation methane | BM AG04.002 | BM-T-001 | 5 |
| P6 | Household / small-farm manure biogas | BM AG04.001 | (T-002, T-003, T-008, T-010 when added) | 5 |
| P7 | Compressed biogas | BM WA03.003 | BM-T-011 + several tools not yet in pack | later |
| P8 | Energy / industry | EN01.00x, IN02.00x | T-002, T-003, T-006, T-015 | later (slots only) |

### 3.2 Functional modules

1. **Project registry**: clients, projects, sites, crediting periods, methodology and tool versions,
   locked GWP set, status pipeline (concept -> PDD -> validation -> registered -> monitoring ->
   verification -> issuance).
2. **Applicability checker**: per methodology and tool, a rule set with evidence; blocks a project or
   stratum that fails.
3. **Additionality and baseline (BM-T-001)**: guided workflow, barrier matrix, investment analysis
   (NPV/IRR/LCOx, sensitivity), common practice; decision record; PDD section draft.
4. **Geospatial**: project boundaries, strata/modelling units, plots/fields; import KML, KMZ, SHP,
   GeoJSON, GPKG; geodesic areas; overlap and containment checks; map viewer.
5. **Field data capture**: CSV/XLSX import with templates (`templates/`), XLSForm generation for
   ODK/KoboToolbox, sync API; offline-capable PWA in a later phase.
6. **Sensor / time-series ingestion**: LFG flow, CH4 %, T, P, flare status, electricity meters
   (CSV upload, SFTP drop, MQTT/HTTP push); instrument and calibration register.
7. **QA/QC engine**: declarative rules from spec 13 with severities; issue tracker; reviewer
   approvals; data lock per monitoring period.
8. **Calculation engine**: tools and methodology plugins, ex-ante and ex-post runs, uncertainty,
   annualisation, vintages, lineage trace.
9. **Statistics and sampling**: number-of-plots planning (interface only until the BEE tool is
   supplied), stratified and double sampling estimators, SOC validation metrics, cross-validation
   distance checks, sample size (Box 5).
10. **Remote sensing (phase 6)**: crown-cover change for "no-decrease", burnt-area candidates, NDVI
    as a double-sampling secondary variable, residue cover for zero tillage evidence. Remote sensing
    proposes; a reviewer confirms.
11. **Evidence vault**: object storage, hashing, linking to entities, retention per Detailed
    Procedure (2 years after crediting period or last issuance, whichever later).
12. **Reporting**: ER/removal workbook (XLSX with visible formulas and a lineage sheet), PDD
    calculation annex and Monitoring Report tables (DOCX and PDF), monitoring plan, SOC model
    validation report, ACVA reproducibility bundle (ZIP).
13. **Dashboards**: portfolio, per-project ex-ante vs ex-post trajectory, uncertainty, data
    completeness, QA/QC issues, upcoming deadlines (validation within 2 years of start; MR
    chronology; issuance within 2 years after crediting period; on-site visit triggers).
14. **Admin**: users and roles, parameter catalogue versions, methodology versions, GWP sets, errata
    flags, audit log viewer.

## 4. Architecture and stack

```
repo/
  apps/
    api/            FastAPI (Python 3.12), Pydantic v2, SQLAlchemy 2, Alembic
    worker/         Celery + Redis: imports, QA/QC, calculation runs, report rendering
    web/            Next.js (TypeScript, App Router), TanStack Query/Table, MapLibre GL, ECharts
  packages/
    dmrv_core/      pure-Python engine: units (pint), equation registry, trace, parameter
                    resolution, statistics (numpy/scipy), annualisation, uncertainty
    methodologies/  plugins: tools/ (bm_t_001, bm_t_011, bm_t_ar_0002 ... 0006, soc_mg_draft,
                    soc_at_draft) and methodologies/ (fr05_002, fr05_001, wa03_002, ...)
    schemas/        shared Pydantic models -> JSON Schema -> generated TS types
    reports/        XLSX (openpyxl), DOCX (python-docx), PDF (WeasyPrint) templates
    cli/            `dmrv run --bundle bundle.zip` for ACVA reproduction
  infra/            docker-compose: postgres16+postgis3.4, redis, minio, api, worker, web
  docs/source/      government PDFs (read-only)
  specs/            this specification pack (read-only unless I approve changes)
  reference/        golden_cases.py (+ json): independent expected values
  tests/            unit, golden, property-based (hypothesis), integration, e2e (Playwright)
```
Quality gates in CI: ruff, mypy `--strict` on `dmrv_core` and `methodologies`, pytest with coverage
>= 95 % on engine packages, golden tests, ESLint + `tsc --noEmit`, Playwright smoke, Alembic
migration check, SBOM and dependency audit.

Geodesy: store geometries in EPSG:4326; compute areas geodesically (pyproj `Geod`), never planar on
lat/lon; record the method.

## 5. Calculation engine design (`packages/dmrv_core`)

### 5.1 Equation registry and trace

```python
@equation(tool="BM-T-AR-0004", version="1.0", eq="15", page=14,
          doc="u_C = t_VAL * sqrt(sum_i w_i^2 * s_i^2 / n_i) / b_TREE")
def tree_stock_uncertainty(w: Seq[Q], s2: Seq[Q], n: Seq[int], b_tree: Q, t_val: float) -> Q:
    ...
```
* The decorator records a `TraceNode(id, tool, eq, inputs{name: (value, unit, source_ref)},
  outputs, errata_applied[], warnings[])` into the active `CalculationContext`.
* Nodes form a DAG; the run stores it; the UI renders it as an expandable tree from any output.
* No intermediate rounding. Rounding only in presentation and in issuance quantity
  (`issuance_rounding` policy, default floor to whole tCO2e).

### 5.2 Parameter resolution

`ParameterResolver.get(symbol, tool, scope, scenario, at_date)` returns a `ResolvedParameter`
(value, unit, uncertainty, source_type, citation, evidence_ids, approval). Order: measured >
project-specific justified and approved > tool default (catalogue). Issuance-grade runs refuse
unapproved non-default values.

### 5.3 Statistics

`stats.t_two_sided(conf=0.90, df)`, stratified estimator (AR-0004 Eq.12-17), double sampling
(Eq.18-19), change estimators (Eq.1-8), `conservative(mean, half_width, scenario)` (Appendix 2),
regression slope/correlation (Appendix 3), SOC metrics (spec 09 Eq.12-25), residual-trend change
estimator (Annex A Eq.26-35), sample size (Box 5).

### 5.4 Time

Project year t = 1 starts at the project start date. Convert measurement dates to fractional years;
`T = days/365.25` default, `month_based` optional. Annualised changes are allocated to project years
and to calendar vintages pro rata by days. Monitoring periods must be contiguous and chronological.

### 5.5 Plugin contract

```python
class ToolPlugin(Protocol):
    code: str                 # "BM-T-AR-0004"
    version: str              # "1.0"
    status: Literal["APPROVED", "DRAFT"]
    def applicability(self, ctx, inputs) -> list[ApplicabilityResult]: ...
    def required_parameters(self, options) -> list[ParameterSpec]: ...
    def compute(self, ctx, inputs, options) -> ToolResult: ...     # pure, traced

class MethodologyPlugin(Protocol):
    code: str                 # "BM FR05.002"
    version: str
    status: Literal["APPROVED", "DRAFT"]
    tools: dict[str, str]     # tool code -> pinned version
    crediting_rules: CreditingRules
    def applicability(self, ctx, project) -> list[ApplicabilityResult]: ...
    def monitoring_plan(self, project) -> MonitoringPlan: ...      # parameters, frequency, QA/QC
    def ex_ante(self, ctx, project, scenario_inputs) -> MethodologyResult: ...
    def ex_post(self, ctx, project, period) -> MethodologyResult: ...
```
`MethodologyResult` holds per-year baseline, project, leakage, net values, tCCC/lCCC (A/R) or ER (others),
uncertainty statements, warnings, errata applied and draft flags.

## 6. Tool coverage required (all in `specs/`)

* BM-T-001 additionality workflow and investment analysis (spec 02).
* BM-T-AR-0004 all four change methods, all stock methods, shrubs, Appendix 1-3 (spec 03).
* BM-T-AR-0003 standing dead trees (BEF and allometric), stumps, lying dead wood, default factors,
  litter (measured and default), changes (spec 04).
* BM-T-AR-0002 site preparation, residue burning, forest fire tree and DOM, thresholds (spec 05).
* BM-T-AR-0005 leakage incl. zero-leakage grazing cases (spec 06).
* BM-T-AR-0006 SOC rates with applicability tables (spec 07).
* BM-T-011 yearly and monthly FOD, φ options, DOC_f from BMP, MCF with water table, all default
  tables (spec 08).
* DRAFT SOC Model Guidelines: data harmonisation, equivalent soil mass, validation metrics, cross-
  validation checks, safety discount, residual-trend change estimator, verification workflow (spec 09).
* DRAFT SOC activity tools: applicability matrices, stratum-level other emissions, yield leakage,
  biostimulant LCA emissions, pulp and paper sludge emissions, evidence rules (spec 10).

## 7. Key workflows (UI + API)

1. **Create project**: client, type, methodology (version pinned), location, start date (>= 2025-01-01),
   crediting period type; GWP set locked.
2. **Applicability**: checklist with evidence; failing items block progress.
3. **Additionality** (BM-T-001) to a signed decision record.
4. **Boundary and stratification**: upload boundaries, define baseline and project strata / MUs with
   attributes required by the tools (climate zone, soil class, land use, management, inputs, crown
   cover); geometry checks.
5. **Ex-ante estimate**: planting plan and growth model (A/R), BM-T-011 projection (waste), SOC
   scenario (draft); produce PDD tables.
6. **Monitoring plan** generated from the plugin: every parameter, unit, frequency, method, QA/QC,
   responsible role.
7. **Data collection**: templates, XLSForms, sensor feeds; submissions land in "pending QA".
8. **QA/QC**: automatic rules, reviewer resolution, lock data for the monitoring period.
9. **Calculation run** (draft -> reviewed -> approved). Second-person review required for approval.
10. **Reports** and ACVA bundle. Track ACVA findings (CAR/CL/FAR) and their closure.
11. **Re-run on correction**: superseding data creates a new run; diffs between runs shown per output
    with the lineage of what changed.

## 8. Screens (web)

Portfolio dashboard; project overview (status, timeline, key numbers, alerts); map workspace (strata,
plots, fire events, fields; layer toggles; click-through to data); data tables with inline QA flags;
import wizard with column mapping and preview; QA/QC issue board; parameter sources table with
approval actions; calculation run page (inputs, outputs per year, uncertainty, warnings, errata,
lineage explorer); ex-ante vs ex-post chart; report centre; additionality workflow; admin. Mobile-
friendly views for field supervisors. Keep the interface professional and calm: neutral palette, clear
typography, dense but readable tables, every number with its unit.

## 9. Reporting requirements

* **ER / removals workbook (XLSX)**: one sheet per tool and per year, cells as Excel formulas
  referencing input cells (so the ACVA can audit in Excel), a "Lineage" sheet mapping each output cell
  to equation IDs, and an "Interpretations" sheet listing errata applied. The XLSX formulas must
  reproduce engine results to 1e-9 relative (test this).
* **PDD annex / MR tables (DOCX + PDF)**: parameter tables in the BEE "Data / Parameter" format (data
  unit, description, source, value applied, measurement procedure, monitoring frequency, QA/QC,
  comment), generated from the parameter registry.
* **SOC model validation report** (draft module): bias table, RMSE/R² table, regression and residual
  plots, cross-validation distance matrix, data-source safety discount.
* **Reproducibility bundle (ZIP)**: snapshot data (CSV/Parquet + GeoPackage), parameters (YAML),
  engine version, trace (JSON), outputs, hashes; `dmrv run --bundle` reproduces outputs.

## 10. Testing and verification

1. **Golden tests**: load `reference/golden_cases.json`; for each case, build inputs through the
   public engine API (not by importing `golden_cases.py`) and compare with `rel_tol`. All 25 must pass
   before any phase is called done.
2. **Document examples**: AR-0004 uncertainty example (SEM 2.191, t 1.692, U 8.18 %); Appendix 2
   example (62.25 / 57.75); SOC Guidelines Annex C t-table (spot-check 10 rows).
3. **Property-based tests** (hypothesis): unit invariance (ha vs m²; cm vs m); monotonicity (more
   biomass never lowers stocks; higher uncertainty never raises a project quantity after discount);
   FOD mass balance (one cohort's emissions sum to its total potential over infinite time);
   stratification invariance (splitting a homogeneous stratum does not change the mean).
4. **Cross-implementation check**: for each A/R and SWDS case, the XLSX formula workbook equals the
   engine output.
5. **Regression snapshots**: frozen end-to-end projects (one A/R, one landfill, one draft SOC) whose
   outputs must not change without an explicit, reviewed snapshot update.
6. **E2E**: Playwright journey for each project type: create project -> import templates -> QA ->
   run -> report download.

## 11. Things you must ask me about (do not guess)

* Any equation marked `[VERIFY]` in spec 11: request the PDF page check result before coding.
* Missing documents: SOC Framework Methodology; BM-T-002, -003, -004, -005, -006, -007, -008, -009,
  -010, -012, -013, -014, -015; the A/R tools for number of sample plots and appropriateness of
  allometric/volume equations; BEE "Investment Analysis" tool; IPCC 2019 Vol.4 Ch.5 (steady-state
  method). Build interfaces and placeholders, then ask.
* Errata marked **ASK BEE** in spec 12: keep the default resolution, surface it in reports.
* Branding, hosting target (on-premise vs cloud region in India), SSO provider.

## 12. Delivery plan and acceptance criteria

**Phase 0: Foundations (week 1-2)**
Monorepo, CI, docker-compose, auth + RBAC skeleton, audit log, evidence vault, parameter catalogue
loader with schema validation, unit system, equation registry + trace, methodology plugin loader.
*Accept:* `docker compose up` gives a working login; catalogue loads; a sample traced equation renders
its lineage in the API; CI green.

**Phase 1: Engine core and A/R tools (week 3-6)**
`dmrv_core` statistics and uncertainty; tools AR-0002, AR-0003, AR-0004, AR-0005, AR-0006 per specs
03-07 with all errata flags; golden tests; property tests.
*Accept:* all `AR*` golden cases pass; document examples pass; mypy strict clean; 95 % coverage.

**Phase 2: A/R project type end to end (week 7-10)**
FR05.002 plugin; data model for strata, plots, trees, dead wood, litter, shrubs, fire, displacement;
CSV/XLSX import with the templates; QA/QC rules (forestry); ex-ante growth models; ex-post run;
tCCC/lCCC with reversal detection; XLSX workbook; PDD/MR tables; map workspace; BM-T-001 workflow.
*Accept:* a synthetic 3-strata project (create it as a committed test fixture) runs from import to report; the
XLSX recomputes to the engine values; lineage available for every reported number.

**Phase 3: Waste and mangrove (week 11-14)**
BM-T-011 complete with golden tests; WA03.002 (and WA03.001) after `[VERIFY]` checks; LFG time-series
ingestion, instrument register, conservative gap handling; FR05.001 plugin.
*Accept:* `T011*` golden cases pass; a synthetic landfill with one year of hourly data produces an ER
report with BM-T-011 ex-ante vs measured overlay.

**Phase 4: Agricultural SOC (DRAFT) (week 15-19)**
Farms/fields/MUs, management records, soil samples with equivalent soil mass, design-based SOC
estimator with CI, model validation module (spec 09), activity-tool other emissions and yield leakage
(spec 10), draft stamping, model-prediction submission timestamps.
*Accept:* `SOCMG*` and `SOCAT*` golden cases pass; validation report generated; issuance runs blocked.

**Phase 5: Rice and manure (week 20-23)** after `[VERIFY]` checks; chamber-measurement data pipeline.

**Phase 6: Remote sensing and mobile (week 24+)** STAC/Earth Engine connectors, candidate events,
offline PWA, XLSForm round-trip.

## 13. Definition of done (every phase)

Specs implemented with equation IDs; errata flags wired and reported; golden + property + regression
tests green; no `TODO(PARAM)` reachable in issuance-grade paths; API documented (OpenAPI); user guide
page for each new screen; a walkthrough artifact showing a real run with screenshots; open questions
updated.
