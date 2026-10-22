# dMRV Build Pack for Antigravity (Indian Carbon Market / CCTS)

This pack lets Google Antigravity build our in-house dMRV and carbon accounting tool. Its calculation
logic comes from the BEE methodological tools you collected. Prepared 21 Oct 2026.

## What is inside

| Path | What it is |
|---|---|
| `ANTIGRAVITY_MASTER_PROMPT.md` | The prompt to paste into the Antigravity agent |
| `specs/` | Implementation-ready restatement of each tool: equations, parameters, defaults, monitoring, plus the errata register and data model |
| `reference/golden_cases.py` + `.json` | 25 test cases with independently computed expected values |
| `templates/` | Field data templates (CSV/GeoJSON/YAML) for plots, trees, dead wood, litter, waste, LFG, soil samples, farm records |
| `.agent/rules/`, `.agent/workflows/` | Antigravity workspace rules (always-on guardrails) and reusable workflows |
| `docs/source/` | Copies of the 8 source PDFs (7 approved tools + the draft SOC pack) |

## How to use it

1. Create an empty repository, copy this whole folder into its root, and open it in Antigravity.
   (Antigravity reads workspace rules from `.agent/rules/` and workflows from `.agent/workflows/`;
   confirm these paths for your Antigravity version.)
2. Replace `{{PRODUCT_NAME}}` and `{{FIRM_NAME}}` in `ANTIGRAVITY_MASTER_PROMPT.md`.
3. Start an agent in **Planning** mode and paste the master prompt. Review its plan and its open
   questions before letting it code.
4. Download the extra BEE PDFs listed in `specs/01_regulatory_context.md` (sections 3-4) into
   `docs/source/` when you reach the phases that need them.
5. Keep the Phase 1 rule: no phase is done until all golden tests pass.

## Things to settle with BEE / ACVA (from `specs/12_errata_register.md`)

* GWP values: BM-T-AR-0002 prints 21/310; the Detailed Procedure requires the latest IPCC values.
* EF_FE in the SOC activity tools: 0.01 is printed as tCO2e/kgN but is IPCC EF1 in kg N2O-N/kg N.
* Yield-leakage formula (CY_min) in the cover-crop and zero-tillage tools.
* Missing appendix (simplified approaches) in BM-T-011.
* India's forest-definition values used in the A/R tools (30 % crown cover, minimum area).
* The SOC Framework Methodology itself (all five SOC tools depend on it; not in hand).
