"""DRAFT SOC Model Validation Report Generator."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence
import numpy as np


@dataclass
class SOCValidationReport:
    project_id: str
    modelling_unit_id: str
    metrics: Dict[str, Any]
    observed: Sequence[float]
    predicted: Sequence[float]
    min_point_distance_m: float = 30.0
    disclaimer: str = "DRAFT METHODOLOGY: NOT VALID FOR ISSUANCE"

    def generate_markdown(self) -> str:
        """Generate structured markdown validation report per spec 09."""
        m = self.metrics
        n = m["n"]

        lines = [
            f"# SOC Model Validation Report — MU {self.modelling_unit_id}",
            f"> **WARNING:** {self.disclaimer}",
            "",
            "## 1. Project & Modelling Unit Summary",
            f"- **Project ID:** {self.project_id}",
            f"- **Modelling Unit:** {self.modelling_unit_id}",
            f"- **Number of Validation Points (n):** {n}",
            f"- **Minimum Separation Distance:** {self.min_point_distance_m:.1f} m (Threshold: $\\ge 30.0$ m)",
            f"- **Validation Data Source:** Category {m.get('validation_data_source', 'A')} (Safety Discount: {m.get('safety_discount', 0.0) * 100:.1f}%)",
            "",
            "## 2. Model Bias Table (Table 3 Eq. 12, 13, 17, 20, 21)",
            "| Metric | Formula / Description | Value | Unit | Threshold / Criterion | Status |",
            "|---|---|---|---|---|---|",
            f"| $\\bar{{X}}_{{\\text{{obs}}}}$ | Observed Mean | {m['mean_obs']:.3f} | t C/ha | — | — |",
            f"| $\\hat{{\\bar{{X}}}}_{{\\text{{pred}}}}$ | Predicted Mean | {m['mean_pred']:.3f} | t C/ha | — | — |",
            f"| $\\text{{SE}}$ | Standard Error of Mean | {m['SE']:.3f} | t C/ha | — | — |",
            f"| $\\text{{MoE}}_{{90}}$ | Margin of Error (90% CI) | {m['MoE_90']:.3f} | t C/ha | — | — |",
            f"| $\\text{{Bias}}$ | $\\hat{{\\bar{{X}}}} - \\bar{{X}}$ | {m['bias']:.3f} | t C/ha | $|\\text{{Bias}}| \\le \\text{{MoE}}_{{90}}$ | {'PASS' if m['pass_bias'] else 'FAIL'} |",
            "",
            "## 3. Accuracy and Goodness of Fit Table (Table 3 Eq. 14, 15, 18, 19)",
            "| Metric | Formula / Description | Value | Unit | Threshold / Criterion | Status |",
            "|---|---|---|---|---|---|",
            f"| $s$ | Sample Std Deviation | {m['s']:.3f} | t C/ha | — | — |",
            f"| $\\text{{RMSE}}$ | Root Mean Square Error | {m['rmse']:.3f} | t C/ha | $\\text{{RMSE}} < s$ | {'PASS' if m['pass_rmse'] else 'FAIL'} |",
            f"| $R^2$ | Coefficient of Determination | {m['R2']:.4f} | — | $R^2 > 0$ | {'PASS' if m['pass_r2'] else 'FAIL'} |",
            "",
            "## 4. Prediction Interval Coverage (PICP) (Table 3 Eq. 22-25)",
            "| Metric | Value | Description |",
            "|---|---|---|",
            f"| $\\text{{PICP}}$ | {m['PICP'] * 100:.1f}% | Prediction Interval Coverage Probability |",
            f"| $s_{{\\text{{PICP}}}}$ | {m['s_PICP']:.4f} | PICP Sample Standard Deviation |",
            f"| $t_{{\\text{{PICP}}}}$ | {m['t_PICP']:.4f} | $t$-statistic vs 90% benchmark |",
            "",
            "## 5. Total Uncertainty Assessment",
            f"- **Model Relative Uncertainty ($UNC$):** {m.get('UNC_fraction', 0.0) * 100:.2f}%",
            f"- **Safety Discount (Source {m.get('validation_data_source', 'A')}):** {m.get('safety_discount', 0.0) * 100:.2f}%",
            f"- **Total Uncertainty ($TU = UNC + \\text{{Safety Discount}}$):** {m.get('total_uncertainty', 0.0) * 100:.2f}%",
            "",
            "## 6. Overall Model Validation Status",
        ]

        all_passed = m["pass_bias"] and m["pass_rmse"] and m["pass_r2"]
        if all_passed:
            lines.append("> **RESULT: VALIDATED (APPROACH 2 ACCEPTED FOR MODELLING)**")
        else:
            lines.append("> **RESULT: FAILED VALIDATION (APPROACH 1 DIRECT MEASUREMENT REQUIRED)**")

        lines.extend([
            "",
            "---",
            f"*Certified: {self.disclaimer}*",
        ])
        return "\n".join(lines)


__all__ = ["SOCValidationReport"]
