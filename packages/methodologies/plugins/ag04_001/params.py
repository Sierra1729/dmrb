"""Parameter defaults and IPCC 2019 factors for BM AG04.001."""
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class AG04001Params:
    # Net-to-gross adjustment factors
    uf_b_conservative: float = 0.89
    uf_b_high: float = 0.895

    # Physical digester leakage rate (para 15)
    physical_leakage_rate: float = 0.10

    # Density of CH4 under STP (t / m3)
    density_ch4_t_m3: float = 0.67e-3

    # IPCC 2019 default VS excretion rates (kg VS / 1000 kg animal mass / day) - Indian subcontinent
    vs_rates: Dict[str, float] = field(
        default_factory=lambda: {
            "dairy_cattle": 5.1,
            "other_cattle": 4.0,
            "buffalo": 3.9,
            "swine": 8.5,
            "sheep_goat": 4.5,
        }
    )

    # Maximum methane producing capacity B0 (m3 CH4 / kg VS)
    b0_defaults: Dict[str, float] = field(
        default_factory=lambda: {
            "dairy_cattle": 0.24,
            "other_cattle": 0.18,
            "buffalo": 0.20,
            "swine": 0.45,
            "sheep_goat": 0.17,
        }
    )

    # Typical animal masses (kg / head)
    animal_masses: Dict[str, float] = field(
        default_factory=lambda: {
            "dairy_cattle": 350.0,
            "other_cattle": 250.0,
            "buffalo": 400.0,
            "swine": 60.0,
            "sheep_goat": 30.0,
        }
    )
