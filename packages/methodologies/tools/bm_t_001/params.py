"""Parameter defaults for BM-T-001 from specs/14_parameter_catalogue.yaml."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class T001Params:
    default_sensitivity_range: float = 0.10  # +/- 10%
    target_similar_facilities_count: int = 10
    max_lifetime_for_no_lockin_years: int = 10
