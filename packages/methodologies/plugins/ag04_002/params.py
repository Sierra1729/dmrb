"""Parameter defaults and scaling factors for BM AG04.002."""
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class AG04002Params:
    # Default uncertainty discount (Section 4.7, para 27)
    u_d_default: float = 0.15

    # IPCC default water regime scaling factors SF_w (Table 3, para 30)
    sf_w_defaults: Dict[str, float] = field(
        default_factory=lambda: {
            "continuously_flooded": 1.0,
            "single_aeration": 0.71,
            "multiple_aeration": 0.55,
        }
    )

    # Pre-season water regime scaling factors SF_p (Table 4, para 31)
    sf_p_defaults: Dict[str, float] = field(
        default_factory=lambda: {
            "non_flooded_lt_180d": 1.00,  # Double cropping
            "non_flooded_gt_180d": 0.89,  # Single cropping
        }
    )

    # N2O emission factors (kg N2O-N / kg N) per paragraph 21
    ef_n2o_baseline: float = 0.003  # Continuously flooded
    ef_n2o_project: float = 0.005   # Single and multiple drainage (AWD)
