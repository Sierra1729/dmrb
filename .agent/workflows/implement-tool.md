# Workflow: implement or update a methodological tool plugin

Use when asked to implement a tool (e.g. "implement BM-T-AR-0003").

1. Read `specs/00_INDEX.md`, the tool's spec file, and every row for that tool in
   `specs/12_errata_register.md`. Open the PDF in `docs/source/` for the pages cited.
2. List the tool's outputs, inputs, parameters (with catalogue keys) and equations in a short plan
   artifact. Flag anything missing from `specs/14_parameter_catalogue.yaml`.
3. Create `packages/methodologies/tools/<code_snake>/` with:
   - `plugin.py` (ToolPlugin: code, version, status, applicability, required_parameters, compute)
   - `equations.py` (one decorated function per equation; docstring = equation text from the spec)
   - `params.py` (typed access to catalogue values)
   - `errata.py` (flags with defaults per the register)
4. Write tests first in `tests/tools/<code_snake>/`:
   - golden cases for this tool from `reference/golden_cases.json` built via the public API
   - one test per equation with a hand-computed value in the docstring
   - property tests (units, monotonicity, edge cases: zero area, single plot, n = 1 -> error)
   - applicability tests (each condition true/false)
5. Implement until tests pass; run mypy strict and ruff.
6. Update the plugin registry, API schema, and the monitoring-plan generator for the new parameters.
7. Produce a walkthrough artifact: inputs, outputs, lineage screenshot, errata applied.
