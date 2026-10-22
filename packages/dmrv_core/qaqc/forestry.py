"""Forestry QA/QC rule engine per specs/13_data_model_and_QAQC.md."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
from shapely import wkt
from shapely.geometry import Point

from dmrv_core.data.forestry import ForestryDataset


class QASeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"  # Blocks issuance-grade calculation runs


@dataclass
class QAIssue:
    rule_code: str
    severity: QASeverity
    entity_type: str  # "tree", "plot", "stratum", "stump", "deadwood"
    entity_id: str
    message: str
    field_name: Optional[str] = None
    value: Optional[str] = None


@dataclass
class QAQCReport:
    issues: List[QAIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(i.severity == QASeverity.ERROR for i in self.issues)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == QASeverity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == QASeverity.WARNING)


class ForestryQAQCEngine:
    """Evaluates declarative quality rules across forestry dataset."""

    def __init__(self, dataset: ForestryDataset) -> None:
        self.ds = dataset

    def run_all_checks(self) -> QAQCReport:
        report = QAQCReport()

        self._check_tree_measurements(report)
        self._check_species_and_equations(report)
        self._check_plot_boundaries(report)

        return report

    def _check_tree_measurements(self, report: QAQCReport) -> None:
        # Check duplicate tree tags within plots
        seen_tags = set()
        for t in self.ds.trees:
            tag_key = (t.plot_id, t.tree_no)
            if tag_key in seen_tags:
                report.issues.append(
                    QAIssue(
                        rule_code="QA_DUPLICATE_TREE_TAG",
                        severity=QASeverity.ERROR,
                        entity_type="tree",
                        entity_id=f"{t.plot_id}_{t.tree_no}",
                        message=f"Duplicate tree_no {t.tree_no} found in plot {t.plot_id}",
                        field_name="tree_no",
                        value=str(t.tree_no),
                    )
                )
            seen_tags.add(tag_key)

            # DBH range check: 5.0 to 300.0 cm
            if t.dbh_cm <= 0.0 or t.dbh_cm > 300.0:
                report.issues.append(
                    QAIssue(
                        rule_code="QA_DBH_RANGE",
                        severity=QASeverity.ERROR,
                        entity_type="tree",
                        entity_id=f"{t.plot_id}_{t.tree_no}",
                        message=f"DBH {t.dbh_cm} cm is outside physical limits (<=0 or >300 cm)",
                        field_name="dbh_cm",
                        value=str(t.dbh_cm),
                    )
                )
            elif t.dbh_cm < 5.0 or t.dbh_cm > 200.0:
                report.issues.append(
                    QAIssue(
                        rule_code="QA_DBH_RANGE",
                        severity=QASeverity.WARNING,
                        entity_type="tree",
                        entity_id=f"{t.plot_id}_{t.tree_no}",
                        message=f"DBH {t.dbh_cm} cm is unusual (<5 cm or >200 cm)",
                        field_name="dbh_cm",
                        value=str(t.dbh_cm),
                    )
                )

            # Height range and H/DBH ratio check
            if t.height_m is not None:
                if t.height_m < 1.3 or t.height_m > 65.0:
                    report.issues.append(
                        QAIssue(
                            rule_code="QA_HEIGHT_RANGE",
                            severity=QASeverity.ERROR,
                            entity_type="tree",
                            entity_id=f"{t.plot_id}_{t.tree_no}",
                            message=f"Height {t.height_m} m is outside physical limits (<1.3m or >65m)",
                            field_name="height_m",
                            value=str(t.height_m),
                        )
                    )
                else:
                    # Height/DBH ratio: H (m) / (DBH (m))
                    dbh_m = t.dbh_cm / 100.0
                    if dbh_m > 0:
                        ratio = t.height_m / dbh_m
                        if ratio < 20.0 or ratio > 220.0:
                            report.issues.append(
                                QAIssue(
                                    rule_code="QA_HEIGHT_DBH_RATIO",
                                    severity=QASeverity.WARNING,
                                    entity_type="tree",
                                    entity_id=f"{t.plot_id}_{t.tree_no}",
                                    message=f"Height-to-DBH ratio {ratio:.1f} is atypical (normal 20-220)",
                                    field_name="height_m",
                                    value=str(t.height_m),
                                )
                            )

    def _check_species_and_equations(self, report: QAQCReport) -> None:
        for t in self.ds.trees:
            if t.species_code not in self.ds.species:
                report.issues.append(
                    QAIssue(
                        rule_code="QA_MISSING_SPECIES",
                        severity=QASeverity.ERROR,
                        entity_type="tree",
                        entity_id=f"{t.plot_id}_{t.tree_no}",
                        message=f"Species code {t.species_code} not found in species parameters catalogue",
                        field_name="species_code",
                        value=t.species_code,
                    )
                )
            else:
                sp = self.ds.species[t.species_code]
                if sp.allometric_eq_id and sp.allometric_eq_id not in self.ds.allometric_equations:
                    report.issues.append(
                        QAIssue(
                            rule_code="QA_MISSING_ALLOMETRIC",
                            severity=QASeverity.ERROR,
                            entity_type="tree",
                            entity_id=f"{t.plot_id}_{t.tree_no}",
                            message=f"Allometric equation {sp.allometric_eq_id} not defined",
                            field_name="allometric_eq_id",
                            value=sp.allometric_eq_id,
                        )
                    )

    def _check_plot_boundaries(self, report: QAQCReport) -> None:
        for plot_id, plot in self.ds.plots.items():
            # Check geographic bounds for India (lat 6-38, lon 68-98)
            if not (6.0 <= plot.center_lat <= 38.0 and 68.0 <= plot.center_lon <= 98.0):
                report.issues.append(
                    QAIssue(
                        rule_code="QA_COORDINATES_BOUNDS",
                        severity=QASeverity.WARNING,
                        entity_type="plot",
                        entity_id=plot_id,
                        message=f"Plot coordinates ({plot.center_lat}, {plot.center_lon}) outside mainland India bounds",
                    )
                )

            # Check polygon containment if WKT provided
            stratum = self.ds.strata.get(plot.stratum_id)
            if stratum and stratum.geometry_wkt:
                try:
                    poly = wkt.loads(stratum.geometry_wkt)
                    pt = Point(plot.center_lon, plot.center_lat)
                    if not poly.contains(pt):
                        report.issues.append(
                            QAIssue(
                                rule_code="QA_PLOT_BOUNDARY_CONTAINMENT",
                                severity=QASeverity.ERROR,
                                entity_type="plot",
                                entity_id=plot_id,
                                message=f"Plot center is outside stratum {plot.stratum_id} polygon geometry",
                            )
                        )
                except Exception as ex:
                    report.issues.append(
                        QAIssue(
                            rule_code="QA_GEOMETRY_PARSE",
                            severity=QASeverity.WARNING,
                            entity_type="stratum",
                            entity_id=stratum.stratum_id,
                            message=f"Could not parse geometry WKT: {ex}",
                        )
                    )


__all__ = ["QASeverity", "QAIssue", "QAQCReport", "ForestryQAQCEngine"]
