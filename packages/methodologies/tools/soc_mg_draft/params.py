"""Parameter defaults and discount schedules for DRAFT SOC Model Guidelines."""
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class SOCMGParams:
    alpha: float = 0.10  # 90% confidence level
    min_point_distance_m: float = 30.0
    min_calibration_points: int = 100
    min_cv_folds: int = 5

    # Safety discount schedule by validation source (A, B, C, D)
    safety_discounts: Dict[str, float] = field(
        default_factory=lambda: {
            "A": 0.0,   # Direct measurements within project area
            "B": 0.10,  # Adjacent similar reference sites
            "C": 0.30,  # Non-adjacent similar sites, same extent
            "D": 0.50,  # Non-adjacent similar sites, different extent
        }
    )
