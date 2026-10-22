"""Errata flags for BM-T-001 per specs/12_errata_register.md."""
from dataclasses import dataclass


@dataclass
class T001ErrataFlags:
    # E-T001-01: Step 4a measures in definition section not listed -> always run Step 4b
    always_run_step_4b: bool = True

    # E-T001-02: Methodological tool for Investment Analysis missing -> benchmark user-entered
    allow_user_entered_benchmark: bool = True
