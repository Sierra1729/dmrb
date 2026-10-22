# 01. Regulatory Context: Indian Carbon Market (CCTS Offset Mechanism)

The software is an internal dMRV and carbon-accounting tool for projects registered (or to be
registered) under the **Offset Mechanism of the Carbon Credit Trading Scheme, 2023 (CCTS)**.
Administrator: **Bureau of Energy Efficiency (BEE)**, Ministry of Power. Methodologies are issued
jointly with MoEFCC.

## 1. Terminology the UI and reports must use

| Term | Meaning |
|---|---|
| Non-obligated entity | The project proponent registering offset projects (our client) |
| CCC | Carbon Credit Certificate (1 CCC = 1 tCO2e) |
| tCCC / lCCC | Temporary / long-term CCCs for A/R removals (FR05 methodologies) |
| ACVA | Accredited Carbon Verification Agency (validates and verifies) |
| Administrator | BEE |
| NSC-ICM | National Steering Committee for Indian Carbon Market (recommends issuance) |
| ICM Registry / portal | indiancarbonmarket.gov.in |
| PDD | ICM Project Design Document |
| MR | Monitoring Report |

## 2. Rules from the Detailed Procedure for Offset Mechanism that the software must enforce

Source: *Detailed Procedure for Offset Mechanism* (2025 version; confirm the latest on the ICM portal).

| Rule | Value | Software behaviour |
|---|---|---|
| GWP | "Latest GWP100 values as published by IPCC" for all conversions, monitoring, verification and issuance | Global GWP set = IPCC AR6 by default (CH4 = 29.8, N2O = 273, as used in BEE methodologies). Versioned table; per-project lock at registration. See E-GWP-01 for tools that print older values |
| Crediting period (general) | Fixed 10 years, or renewable 5 years with max 2 renewals (15 years total) | Project-level setting; validate per methodology (some tools state other periods, see section 5) |
| Earliest start date | Project activity start date not before 1 Jan 2025; no retrospective projects | Validation error on project creation |
| Validation deadline | Validation completed within 2 years of project start date | Warning at 18 months, error at 24 |
| Monitoring report | Covers full monitoring period, chronological, separate MR per crediting period; negative reductions deducted | MR generator enforces chronology and nets negatives |
| Monitoring frequency | Continuous variables continuously; constants at least annually unless methodology says more often | Data-completeness checks per parameter |
| Measuring equipment | Must meet BIS / national / IEC standards; calibrated by an NABL-accredited body | Instrument register with calibration certificate expiry; block data from expired instruments (flag) |
| Data retention | Archive monitored data electronically for 2 years after the crediting period or last issuance, whichever is later | Retention policy on evidence vault; deletion prevented |
| Validator vs verifier | Verification by a different ACVA from the validator | Data field + check |
| Materiality (verification) | 0.5 % if >= 500,000 tCO2e/yr; 1 % for 300,000-500,000; 2 % if <= 300,000 | Compute and show materiality threshold per MR |
| On-site visit triggers | Validation if > 100,000 tCO2e/yr; first verification; > 3 years since last visit; > 100,000 tCO2e since last visit | Dashboard reminders |
| Issuance requests | Chronological from the first monitoring period; within 2 years after end of crediting period | Timeline guard |
| Non-permanence | ACVA assesses risk of non-permanence and reversal measures at validation | A/R module tracks reversals via lCCC < 0 (see spec 11) |

Rounding of CCCs is not stated in the visible text of the Detailed Procedure. Default: keep full
precision internally; report issuance quantity **rounded down to whole tCO2e** (conservative).
Make it a configurable policy (`issuance_rounding: floor|round_half_down|none`).

## 3. BEE list of approved methodologies (portal "Last Updated On 07 Jul 2026")

Source: https://beeindia.gov.in/view_content.php?lang=1&lid=571 (checked 21 Oct 2026). Download the
PDFs into `/docs/source` before implementing the related module.

| Code | Title | Sector | Uses tools in this pack | PDF |
|---|---|---|---|---|
| BM EN01.001 | Grid-connected electricity generation from renewable sources | Energy | check PDF | https://beeindia.gov.in/WriteReadData/RTF1984/RTF-PDF-7142dfb1cb5c2361_1776061176.pdf |
| BM EN01.002 | Hydrogen production from electrolysis of water | Energy | check PDF | https://beeindia.gov.in/WriteReadData/RTF1984/RTF-PDF-99e511d259391bd9_1776061190.pdf |
| BM EN01.003 | Electricity and heat generation from biomass | Energy | check PDF (likely T-010) | https://beeindia.gov.in/WriteReadData/RTF1984/RTF-PDF-c50f50661b36cf97_1783086824.pdf |
| BM IN02.001 | Energy efficiency and fuel switching measures for industrial facilities | Industry | check PDF | https://beeindia.gov.in/WriteReadData/RTF1984/RTF-PDF-ab06743897d11b58_1776061202.pdf |
| BM IN02.002 | Hydrogen production using methane extracted from biogas | Industry | check PDF | https://beeindia.gov.in/WriteReadData/RTF1984/RTF-PDF-11086e8d63989765_1776061213.pdf |
| BM WA03.001 | Landfill methane recovery | Waste | BM-T-001, **BM-T-011** | https://beeindia.gov.in/WriteReadData/RTF1984/RTF-PDF-90e2162fc0bbcb7c_1776061229.pdf |
| BM WA03.002 | Flaring or use of landfill gas | Waste | BM-T-001, **BM-T-011** | https://beeindia.gov.in/WriteReadData/RTF1984/RTF-PDF-a0e3f856720a5c57_1776061241.pdf |
| BM WA03.003 | Production of Compressed Bio-gas (CBG) | Waste | BM-T-001, **BM-T-011** | https://beeindia.gov.in/WriteReadData/RTF1984/RTF-PDF-56f665ac470e0ca1_1783087085.pdf |
| BM AG04.001 | Methane recovery from livestock and manure management at households and small farms | Agriculture | - | https://beeindia.gov.in/WriteReadData/RTF1984/RTF-PDF-e0da265a40736c0d_1776061252.pdf |
| BM AG04.002 | Emission reduction through improved management practices in rice cultivation | Agriculture | BM-T-001 | https://beeindia.gov.in/WriteReadData/RTF1984/RTF-PDF-6928edf26e7d04da_1783086710.pdf |
| BM FR05.001 | Afforestation and reforestation of degraded mangrove habitats | Forestry | **AR-0002..0005** | https://beeindia.gov.in/WriteReadData/RTF1984/RTF-PDF-0a5abd883df41e53_1776061263.pdf |
| BM FR05.002 | Afforestation and reforestation of lands except wetlands | Forestry | **AR-0002..0006** | https://beeindia.gov.in/WriteReadData/RTF1984/RTF-PDF-497b2256ef03c1de_1776061272.pdf |

## 4. BEE list of approved methodological tools

Non-forestry (in pack: **bold**)

| Code | Title | PDF |
|---|---|---|
| **BM-T-001** | Combined tool to identify the baseline scenario and demonstrate additionality | https://beeindia.gov.in/WriteReadData/RTF1984/RTF-PDF-c3aec9f87c079b9a_1776061527.pdf |
| BM-T-002 | Project or leakage CO2 emissions from fossil fuel combustion | https://beeindia.gov.in/WriteReadData/RTF1984/RTF-PDF-b56f90cf720778bb_1776061539.pdf |
| BM-T-003 | Baseline, project and/or leakage emissions from electricity consumption and monitoring of electricity generation | https://beeindia.gov.in/WriteReadData/RTF1984/RTF-PDF-8c2b4abcf62550a6_1776061548.pdf |
| BM-T-004 | Project emissions from flaring | https://beeindia.gov.in/WriteReadData/RTF1984/RTF-PDF-1c0559f148753b50_1776061566.pdf |
| BM-T-005 | Mass flow of a greenhouse gas in a gaseous stream | https://beeindia.gov.in/WriteReadData/RTF1984/RTF-PDF-157e6104a661d58e_1776061592.pdf |
| BM-T-006 | Baseline efficiency of thermal and electricity systems | https://beeindia.gov.in/WriteReadData/RTF1984/RTF-PDF-9e553b06774d2eec_1776061606.pdf |
| BM-T-008 | Project and leakage emissions from anaerobic digesters | https://beeindia.gov.in/WriteReadData/RTF1984/RTF-PDF-95ad1fffaacae725_1776061617.pdf |
| BM-T-010 | Project and leakage emissions from biomass | https://beeindia.gov.in/WriteReadData/RTF1984/RTF-PDF-10a330f6757ffbdc_1776061631.pdf |
| **BM-T-011** | Emissions from solid waste disposal sites | https://beeindia.gov.in/WriteReadData/RTF1984/RTF-PDF-39324557592c02c2_1776061640.pdf |
| BM-T-013 | Project and leakage emissions from composting | https://beeindia.gov.in/WriteReadData/RTF1984/RTF-PDF-5f949cdf849d668d_1776061649.pdf |
| BM-T-014 | Apportioning emissions from production processes between main product and co- and by-product | https://beeindia.gov.in/WriteReadData/RTF1984/RTF-PDF-033c6ab24338697a_1776061659.pdf |
| BM-T-015 | Remaining lifetime of equipment | https://beeindia.gov.in/WriteReadData/RTF1984/RTF-PDF-39e9d29b0438ec1e_1776061669.pdf |

Forestry (all in pack)

| Code | Title | PDF |
|---|---|---|
| **BM-T-AR-0002** | Non-CO2 GHG emissions from burning of biomass (A/R) | https://beeindia.gov.in/WriteReadData/RTF1984/RTF-PDF-0b574a382aba0e6b_1776061802.pdf |
| **BM-T-AR-0003** | Carbon stocks and change in dead wood and litter (A/R) | https://beeindia.gov.in/WriteReadData/RTF1984/RTF-PDF-4d7a8de20747aee3_1776061816.pdf |
| **BM-T-AR-0004** | Carbon stocks and change of trees and shrubs (A/R) | https://beeindia.gov.in/WriteReadData/RTF1984/RTF-PDF-cbeb6b67d811aec8_1776061824.pdf |
| **BM-T-AR-0005** | Increase in GHG emissions from displacement of pre-project agricultural activities (A/R) | https://beeindia.gov.in/WriteReadData/RTF1984/RTF-PDF-bf23969b1e527913_1776061833.pdf |
| **BMT-T-AR-0006** (sic) | Change in SOC stocks due to A/R | https://beeindia.gov.in/WriteReadData/RTF1984/RTF-PDF-bab2189eb243ca93_1776061843.pdf |

Referenced by methodologies but **not on the BEE list** at time of check (treat as missing
dependencies, request from BEE): BM-T-007 (freight transport), BM-T-009 (upstream fossil fuel
leakage), BM-T-012 (positive list), "Investment Analysis" tool (BM-T-001 para 36), A/R tools
"Calculation of the number of sample plots", "Demonstrating appropriateness of allometric
equations", "Demonstrating appropriateness of volume equations", and the **SOC Framework
Methodology** that all five SOC activity tools depend on.

## 5. Crediting periods stated inside individual tools (override checks)

| Document | Stated crediting period |
|---|---|
| Detailed Procedure (general) | 10 fixed, or 5 renewable x up to 3 periods (15) |
| DRAFT Cover crops tool | "Requires 10 years"; renewable 5-year periods, max 2 renewals (15) |
| DRAFT Improved tillage tool | Refers to draft "Ecosystem-based approaches": 20 fixed, or 10 renewable x up to 3 (30) |
| DRAFT Zero tillage tool | 20 fixed |
| DRAFT Biostimulants tool | 20 fixed or 10 renewable; starts at later of project start or 3 years before Project Design Certification |
| DRAFT Pulp and paper sludge tool | Max 20; 5-year certification cycle |

Implement crediting-period rules as data on each methodology plugin, not hard-coded.

## 6. Draft methodologies seen in consultation (secondary source, verify on portal)

A secondary reference that says it checked the ICM portal on 25 Aug 2026 lists five drafts:
shore-side electricity supply, recovery/recycling of materials from end-of-life vehicles, Mass
Rapid Transit System (BM TR06.00X), cooking energy, accelerated carbon mineralisation using
reactive industrial waste (BM CCUS10.001). The SOC draft pack in `/docs/source` is not on that list.
Treat all of these as future plugins.
