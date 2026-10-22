# Specification Pack: Index and Conventions

This folder is the single source of truth for every calculation the dMRV engine performs.
The PDFs in `/docs/source` are the legal source. These specs restate them in
implementation-ready form and record every ambiguity or error found in the PDFs, with the
resolution to implement.

## Files

| File | Covers | Source status |
|---|---|---|
| `01_regulatory_context.md` | CCTS / Indian Carbon Market rules the software must respect; BEE list of approved methodologies and tools with links | Official (BEE portal, Detailed Procedure) |
| `02_BM-T-001_additionality.md` | Combined tool: baseline scenario + additionality workflow | Approved v1.0 (27 Mar 2025) |
| `03_BM-T-AR-0004_trees_shrubs.md` | Tree and shrub carbon stocks and changes, sampling statistics, uncertainty discount | Approved v1.0 |
| `04_BM-T-AR-0003_deadwood_litter.md` | Dead wood and litter carbon stocks and changes | Approved v1.0 |
| `05_BM-T-AR-0002_fire_nonCO2.md` | Non-CO2 GHG from biomass burning | Approved v1.0 |
| `06_BM-T-AR-0005_leakage_displacement.md` | Leakage from displacement of pre-project agriculture | Approved v1.0 |
| `07_BM-T-AR-0006_soc_AR.md` | SOC change in A/R lands (factor-based) | Approved v1.0 |
| `08_BM-T-011_SWDS.md` | Methane from solid waste disposal sites (FOD model) | Approved v1.0 |
| `09_SOC_model_guidelines_DRAFT.md` | SOC model selection, calibration, validation, uncertainty, verification | DRAFT (not yet adopted) |
| `10_SOC_activity_tools_DRAFT.md` | Cover crops, improved tillage, zero tillage, biostimulants, pulp and paper sludge soil improvers | DRAFT (not yet adopted) |
| `11_project_type_modules.md` | How tools compose into project types (A/R, mangrove, landfill, CBG, rice, manure, agricultural SOC) | Mixed |
| `12_errata_register.md` | Every defect found in the source PDFs and the resolution to implement | Internal |
| `13_data_model_and_QAQC.md` | Entities, field data templates, QA/QC rules, evidence | Internal design |
| `14_parameter_catalogue.yaml` | Machine-readable default values with citations | Derived from PDFs |

## Conventions used in every spec

* **Equation IDs.** `[TOOL Eq.N]`, e.g. `[AR0004 Eq.12]`, always the number printed in the PDF.
  Code must reference this ID in the `@equation` decorator.
* **Indices.** `i` = stratum, `p` = plot, `j` = species or waste type, `k` = individual tree or stump,
  `t` = project year (t = 1 is the first year after project start), `y` = crediting year (BM-T-011),
  `x` = disposal year (BM-T-011), `m` = month.
* **Units.** SI with the PDF's unit stated per variable. `t d.m.` = tonnes dry matter.
  `44/12` converts t C to t CO2. Engine must carry units (pint) and refuse to add incompatible units.
* **Scenario suffixes.** `_BSL` baseline, `_PROJ` project, matching the tools' notation.
* **Status labels.** `APPROVED` = adopted BEE tool. `DRAFT` = consultation or internal draft. A draft
  module must be selectable for internal estimates but must stamp every output "DRAFT METHODOLOGY:
  NOT VALID FOR ISSUANCE".
* **Errata references.** `(see E-XXX-NN)` points to `12_errata_register.md`. Never implement a
  formula differently from this spec without adding an errata entry.
* **Golden tests.** `/reference/golden_cases.json` holds expected values computed independently by
  `/reference/golden_cases.py`. Each spec lists which cases cover it.
