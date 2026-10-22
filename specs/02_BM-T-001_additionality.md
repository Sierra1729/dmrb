# 02. BM-T-001: Combined Tool to Identify the Baseline Scenario and Demonstrate Additionality

Status: APPROVED, v1.0, 27 March 2025. Source: `/docs/source/BM-T-001_*.pdf` (16 pp).
Applies to: every project type. Not numeric except Step 3; implement as a **guided, evidence-backed
decision workflow** whose output is a signed decision record plus a PDD section draft.

## 1. Workflow (state machine)

```
START
 -> M1 Regulatory analysis (mandatory)          -> fail => NOT ADDITIONAL
 -> M2 Lock-in risk analysis (mandatory)        -> fail => NOT ADDITIONAL
 -> S1a Define alternatives S1..S6
 -> S1b Legal compliance filter
      if only S1 remains                         => NOT ADDITIONAL (stop)
 -> S2a List barriers;  S2b eliminate alternatives prevented by >= 1 barrier
      if only S1 remains                         => NOT ADDITIONAL (stop)
      if exactly one alternative remains (not S1):
           output only by entity                 => BASELINE = that alternative
           output also by others                 => BASELINE = emission benchmark (per methodology)
      if several remain:
           includes S1                           -> S3
           excludes S1 -> user chooses Option 1 (S3) or Option 2 "No investment analysis":
                output only by entity            => BASELINE = lowest-emission remaining alternative
                otherwise                        => BASELINE = emission benchmark
 -> S3 Investment analysis (benchmark | investment comparison | simple cost) + sensitivity
 -> Emission check: if baseline emissions <= emissions of S1               => NOT ADDITIONAL
 -> S4 Common practice (4a if measure listed in definitions -> skip to outcome; else 4b)
      common practice and no essential distinction                          => NOT ADDITIONAL
 -> ADDITIONAL + BASELINE SCENARIO
```

## 2. Step data the UI must capture

**M1 Regulatory analysis (paras 7-10).** For each applicable law/regulation: name, citation,
date, whether it (a) directly requires the activity, (b) indirectly requires it, (c) creates a
support scheme with a quantitative target, applicable to the project, likely to give the same
reductions. Any "yes" without an offset-integration exception fails M1. Store evidence documents.
Re-run at each crediting-period renewal.

**M2 Lock-in risk (paras 11-17).** Fields: technology/practice, technical or operational lifetime
(years, with evidence), emission intensity vs lowest in region, scale, alternatives feasibility,
inefficient use of a climate-relevant resource (yes/no). Rule: lifetime <= 10 years may be
treated as no lock-in risk (para 16) if lifetime evidence is attached.

**S1a Alternatives (paras 18-21).** Fixed list S1-S6 with "applicable" flag and description:
S1 project without ICM; S2 no investment, output from others; S3 continuation without
investment; S4 continuation with investment/expense; S5 other plausible (common practice);
S6 S1 implemented later. Separate alternatives per facility/technology/output when the project
has several (para 20). Geographic area: India by default; if narrowed (state, district), store the
justification. Record the list of similar facilities used to set the area: target 10 facilities,
excluding registered ICM projects; expand area if fewer than 10 (para 21).

**S1b Legal filter (paras 22-24).** For each alternative: complies with mandatory law? If not,
evidence of systematic non-enforcement and widespread non-compliance; else eliminate.

**S2 Barriers (paras 25-28).** Barrier catalogue: investment (grant-only precedent; no capital
available), technological (skilled labour, infrastructure, failure risk, technology unavailable),
other (methodology-specific). Matrix alternative x barrier with evidence type from the list
(a)-(g) in para 28. All alternatives evaluated against the same barrier set.

## 3. Step 3 Investment analysis (paras 30-40), numeric module

Indicators: IRR, NPV, benefit-cost ratio, levelised unit cost (e.g. INR/kWh, INR/GJ).
* Benchmark analysis is mandatory when (a) the project is part of a portfolio supplying power to
  the grid, or (b) the entity is the sole grid power supplier in the area (para 31).
* For S2 or S3 alternatives: NPV = 0; IRR = financial benchmark (para 34).
* Discount rate / benchmark per the BEE "Investment Analysis" tool: **not in pack**. Make the
  benchmark a user-entered, evidence-backed input until that tool is supplied.
* Include all costs (capex, O&M), revenues, subsidies/incentives, ODA; optionally non-market
  costs/benefits for public investors (para 33). Same assumptions across alternatives unless
  justified (para 37).

Implement:
```
NPV(r) = sum_{n=0..N} CF_n / (1 + r)^n
IRR    = r such that NPV(r) = 0      (numpy-financial / brentq; report "no IRR" if no sign change)
LCOx   = sum_n Cost_n/(1+r)^n / sum_n Output_n/(1+r)^n
```
Sensitivity (para 39): vary each critical parameter (capex, O&M, tariff/price, output/PLF, fuel
price, lifetime, discount rate) by a user range (default -10 % / +10 %) and report break-even
variation for each parameter. Conclusion is valid only if the ranking (or the benchmark result) is
robust across the realistic range; otherwise record "sensitivity not conclusive".

Outcome rules (para 40): benchmark analysis chosen -> baseline = emission benchmark scenario.
Investment comparison / simple cost: if sensitivity not conclusive -> baseline = least-emitting
alternative (excluding project); if conclusive -> most attractive alternative; if that is S1 ->
NOT ADDITIONAL. Then the emission check (baseline emissions <= S1 emissions -> NOT ADDITIONAL).

Export the cash-flow model to XLSX **with live formulas** so the ACVA can reproduce it (para 37).

## 4. Step 4 Common practice (paras 41-47)

Capture: list of similar activities (similar scale, comparable environment, same area), excluding
registered ICM projects and those published for consultation; counts; for each, essential
distinctions (with evidence) such as subsidies they had, barriers they did not face, fundamental
and verifiable change in circumstances. Rule: common practice = similar activities observed AND
no essential distinction -> NOT ADDITIONAL.

Note: para 42 refers to "measures listed in the definitions section" (Step 4a), but the definitions
section lists no specific measures (see E-T001-01). Default: always run Step 4b.

## 5. Outputs

* Decision record (JSON + PDF): every step, inputs, evidence hashes, reviewer, timestamp, outcome,
  identified baseline scenario, the methodology's emission benchmark reference if used.
* PDD section draft (DOCX) for "Baseline scenario and additionality".
* Revalidation reminder at each crediting-period renewal.
