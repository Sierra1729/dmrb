"""Errata flags for BM-T-AR-0005 per specs/12_errata_register.md."""
from dataclasses import dataclass


@dataclass
class AR0005ErrataFlags:
    # E-AR5-01: Eq.2 is labelled t d.m. but multiplies by CF, so it is t C; Eq.3 is labelled t C/ha but multiplies by A, so it is t C
    use_tC_units: bool = True

    # E-AR5-02: Text footnote merge error (0.471, 0.252, 0.403). Confirmed values are 0.47, 0.25, 0.40
    use_cleaned_defaults: bool = True

    # E-AR5-03: Cites AR-0006 Tables 3, 4, 5, 6; mapped by content to Tables 4, 5, 6, 7
    map_ar0006_tables_by_content: bool = True
