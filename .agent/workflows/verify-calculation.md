# Workflow: verify a calculation run before it is used in a PDD or Monitoring Report

1. Confirm the run is issuance-grade: no DRAFT modules, no unverified `[VERIFY]` equations, no
   unapproved non-default parameters, no open ERROR-level QA/QC issues, data locked for the period.
2. Re-run the snapshot with `dmrv run --bundle` in a clean environment; outputs must be bit-identical.
3. Open the XLSX workbook; confirm formulas recompute to engine values (automated check passes).
4. For the five largest contributors to the final number, walk the lineage to the raw measurements and
   evidence files; confirm units and sources.
5. Check errata applied and "ASK BEE" items; confirm the report's Interpretations section lists them.
6. Check uncertainty: values above 10 % have discounts applied with the right direction (baseline up,
   project down).
7. Second reviewer approves in the UI; approval records name, time, and the run hash.
