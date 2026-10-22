"""Closed-Chamber Measurement Data Pipeline for Rice Methane Emissions (BM AG04.002)."""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field
import math
from typing import Any, Dict, List, Optional, Sequence
import numpy as np


@dataclass
class ChamberSamplePoint:
    time_minutes: float
    ch4_concentration_ppm: float


@dataclass
class ChamberMeasurement:
    chamber_id: str
    chamber_area_m2: float
    chamber_height_m: float
    temperature_c: float
    pressure_atm: float
    samples: List[ChamberSamplePoint]

    def compute_flux_mg_m2_hr(self) -> Dict[str, float]:
        """Compute flux F in mg CH4 / (m2 * hr) via linear regression slope."""
        if len(self.samples) < 3:
            raise ValueError(f"Chamber {self.chamber_id} requires >= 3 sample points")

        t = np.array([s.time_minutes for s in self.samples], dtype=float)
        # Convert ppm to mg CH4 / m3 using ideal gas law:
        # PV = nRT -> mass/V = P * M / (R * T)
        # R = 0.082057 L*atm/(mol*K), M = 16.04 g/mol
        # 1 ppm = 1e-6 atm partial pressure at 1 atm
        t_kelvin = self.temperature_c + 273.15
        r_gas = 0.082057  # L * atm / (mol * K)
        # mg/m3 = ppm * (M_ch4 / (R * T)) * P
        ppm_to_mg_m3 = (16.04 * 1000.0 / (r_gas * t_kelvin * 1000.0)) * self.pressure_atm * 1000.0
        c_mg_m3 = np.array([s.ch4_concentration_ppm * ppm_to_mg_m3 for s in self.samples], dtype=float)

        # Chamber air volume per unit ground area = chamber_height_m
        # mass in chamber per m2 of ground area = c_mg_m3 * height_m
        mass_ground_mg_m2 = c_mg_m3 * self.chamber_height_m

        # Linear regression slope (mg / (m2 * min))
        t_mean = float(np.mean(t))
        m_mean = float(np.mean(mass_ground_mg_m2))
        ss_t = float(np.sum((t - t_mean) ** 2))
        if ss_t <= 0:
            raise ValueError("Sample time intervals must be distinct")
        slope_mg_m2_min = float(np.sum((t - t_mean) * (mass_ground_mg_m2 - m_mean)) / ss_t)

        # R^2 calculation
        ss_tot = float(np.sum((mass_ground_mg_m2 - m_mean) ** 2))
        predicted = m_mean + slope_mg_m2_min * (t - t_mean)
        ss_res = float(np.sum((mass_ground_mg_m2 - predicted) ** 2))
        r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 1.0

        # Flux per hour: slope * 60 min/hr
        flux_mg_m2_hr = slope_mg_m2_min * 60.0

        return {
            "slope_mg_m2_min": slope_mg_m2_min,
            "r2": float(r2),
            "flux_mg_m2_hr": float(flux_mg_m2_hr),
        }


@dataclass
class PlotSamplingDay:
    date: datetime.date
    measurements: List[ChamberMeasurement]

    def mean_plot_flux_mg_m2_hr(self) -> float:
        """Compute average flux across all chambers for this plot and date."""
        if len(self.measurements) < 3:
            raise ValueError(f"Requires at least 3 chambers per plot, got {len(self.measurements)}")
        fluxes = [m.compute_flux_mg_m2_hr()["flux_mg_m2_hr"] for m in self.measurements]
        return float(np.mean(fluxes))


@dataclass
class ReferenceFieldSeason:
    field_id: str
    sampling_days: List[PlotSamplingDay]

    def integrate_seasonal_emission_kg_ha(self) -> float:
        """Integrate daily plot fluxes over cropping season using trapezoidal rule."""
        if len(self.sampling_days) < 2:
            raise ValueError(f"Field {self.field_id} requires >= 2 sampling dates for integration")

        # Sort chronologically
        days = sorted(self.sampling_days, key=lambda d: d.date)
        total_mg_m2 = 0.0

        for i in range(len(days) - 1):
            d1, d2 = days[i], days[i + 1]
            f1 = d1.mean_plot_flux_mg_m2_hr()
            f2 = d2.mean_plot_flux_mg_m2_hr()
            delta_days = (d2.date - d1.date).days
            delta_hours = delta_days * 24.0

            # Trapezoidal integration in mg/m2
            interval_flux_mg_m2 = ((f1 + f2) / 2.0) * delta_hours
            total_mg_m2 += interval_flux_mg_m2

        # Convert mg/m2 to kg/ha:
        # 1 mg/m2 = 1e-6 kg / 1e-4 ha = 0.01 kg/ha
        kg_ha = total_mg_m2 * 0.01
        return float(max(kg_ha, 0.0))


def compute_group_seasonal_emission_factor(
    reference_fields: Sequence[ReferenceFieldSeason],
) -> Dict[str, Any]:
    """Calculate average seasonal emission factor across reference fields (min 3 required)."""
    if len(reference_fields) < 3:
        raise ValueError(f"BM AG04.002 requires at least 3 reference fields, got {len(reference_fields)}")

    field_efs = [rf.integrate_seasonal_emission_kg_ha() for rf in reference_fields]
    mean_ef = float(np.mean(field_efs))
    sd_ef = float(np.std(field_efs, ddof=1)) if len(field_efs) > 1 else 0.0

    return {
        "n_reference_fields": len(reference_fields),
        "field_seasonal_efs_kg_ha": field_efs,
        "mean_seasonal_ef_kg_ha": mean_ef,
        "sd_seasonal_ef_kg_ha": sd_ef,
    }


__all__ = [
    "ChamberSamplePoint",
    "ChamberMeasurement",
    "PlotSamplingDay",
    "ReferenceFieldSeason",
    "compute_group_seasonal_emission_factor",
]
