# Workspace rules: dMRV carbon accounting (always apply)

1. `specs/` is the source of truth for every calculation. Read the relevant spec and
   `specs/12_errata_register.md` before touching calculation code. Do not edit `specs/` or
   `docs/source/` unless the user explicitly approves the change in chat.
2. Every calculation function carries an `@equation(tool=..., version=..., eq=..., page=...)`
   decorator whose `eq` matches the number printed in the source PDF.
3. Never invent a default value, emission factor, coefficient or threshold. Values come from
   `specs/14_parameter_catalogue.yaml` (with citation) or from user-supplied, evidence-backed project
   data. Missing value -> `raise MissingParameter(...)` and ask.
4. Units: use pint quantities across all engine boundaries. Mixing units without conversion is a bug.
5. Conservative defaults: when the methodology allows alternatives, default to the one that yields
   fewer credits, and expose the alternative as a flag.
6. Errata: implement the documented resolution behind its config flag; list applied errata IDs in
   run outputs and reports. Never "fix" a source formula silently.
7. DRAFT modules (SOC guidelines, SOC activity tools) and any `[VERIFY]` equation: outputs must be
   stamped "DRAFT METHODOLOGY: NOT VALID FOR ISSUANCE"; issuance-grade runs must refuse them.
8. The engine packages (`packages/dmrv_core`, `packages/methodologies`) stay pure: no database,
   network, filesystem or clock access. Pass time and data in explicitly.
9. Golden tests in `reference/golden_cases.json` must pass on every commit. Do not import
   `reference/golden_cases.py` from production code or tests; reproduce values through the engine API.
10. No intermediate rounding. Round only for display and for the issuance quantity per policy.
11. Personal data of farmers and landowners: pseudonymise in analytics and exports; consent ids
    required; follow India's DPDP Act 2023.
12. When a spec is ambiguous or a document is missing, stop and write the question in the open-questions
    artifact instead of choosing an interpretation.
