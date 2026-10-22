"""Parameter defaults and lookup tables for BM-T-011."""
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class T011Params:
    OX_default: float = 0.10
    F_default: float = 0.50
    DOC_f_default: float = 0.50
    GWP_CH4_default: float = 29.8  # CCTS locked set AR6

    # Model correction factor phi defaults
    # (application, climate) -> phi
    phi_defaults: Dict[str, Dict[str, float]] = field(
        default_factory=lambda: {
            "A": {"humid": 0.75, "dry": 0.75},
            "B": {"humid": 0.85, "dry": 0.80},
        }
    )

    # MCF defaults by SWDS type
    mcf_defaults: Dict[str, float] = field(
        default_factory=lambda: {
            "anaerobic_managed": 1.0,
            "semi_aerobic_managed": 0.5,
            "unmanaged_deep": 0.8,
            "unmanaged_shallow": 0.4,
            "stockpile": 0.4,
        }
    )

    # DOC_j defaults (wet weight basis)
    doc_j_defaults: Dict[str, float] = field(
        default_factory=lambda: {
            "wood": 0.43,
            "paper_cardboard": 0.40,
            "food": 0.15,
            "textiles": 0.24,
            "garden": 0.20,
            "inert": 0.0,
            "industrial_sludge": 0.09,
            "domestic_sludge": 0.05,
        }
    )

    # Decay rate k_j defaults (1/yr) by climate
    k_j_defaults: Dict[str, Dict[str, float]] = field(
        default_factory=lambda: {
            "tropical_wet": {
                "food": 0.40,
                "garden": 0.17,
                "paper_cardboard": 0.07,
                "textiles": 0.07,
                "wood": 0.035,
                "inert": 0.0,
            },
            "tropical_dry": {
                "food": 0.085,
                "garden": 0.065,
                "paper_cardboard": 0.045,
                "textiles": 0.045,
                "wood": 0.025,
                "inert": 0.0,
            },
            "temperate_wet": {
                "food": 0.185,
                "garden": 0.10,
                "paper_cardboard": 0.06,
                "textiles": 0.06,
                "wood": 0.03,
                "inert": 0.0,
            },
            "temperate_dry": {
                "food": 0.06,
                "garden": 0.05,
                "paper_cardboard": 0.04,
                "textiles": 0.04,
                "wood": 0.02,
                "inert": 0.0,
            },
        }
    )
