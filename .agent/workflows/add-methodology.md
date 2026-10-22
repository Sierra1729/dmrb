# Workflow: add a new BEE methodology or tool that is not yet in the pack

1. The user adds the official PDF to `docs/source/` (download links in `specs/01_regulatory_context.md`).
2. Read the PDF page by page. Equations are often images: render pages and read them visually; never
   trust plain text extraction for formulas.
3. Draft a new spec file `specs/NN_<code>.md` in the same structure as the existing specs: status,
   source, applicability, outputs, equations with printed IDs, parameter tables, monitoring table,
   dMRV hooks. Add every defect found to `specs/12_errata_register.md` with a proposed resolution.
4. Add defaults to `specs/14_parameter_catalogue.yaml` with citations.
5. Compute at least two hand-checkable golden cases and add them to `reference/golden_cases.py`.
6. Ask the user to approve the spec changes before writing plugin code.
7. Then follow `implement-tool.md` (for tools) or implement a MethodologyPlugin composing the tools.
