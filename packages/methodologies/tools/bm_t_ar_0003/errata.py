"""Errata flags for BM-T-AR-0003 per specs/12_errata_register.md."""
from dataclasses import dataclass


@dataclass
class AR0003ErrataFlags:
    # E-AR3-01: Eq.1 prints (1 + D_j); R_j is in variable list -> (1 + R_j)
    fix_root_shoot_in_eq1: bool = True

    # E-AR3-02: Eq.4 Ormerod exponent precedence: (H_STUMP / (H_STUMP - H_DBH))^0.80
    fix_ormerod_precedence: bool = True

    # E-AR3-04: Eq.9 & 15 DF values are printed in per cent -> divide by 100
    divide_df_by_100: bool = True

    # E-AR3-07: Eq.12 factor 2.5 assumes 4 frames -> 10 / n_frames if n_frames != 4
    generalize_frame_factor: bool = True
