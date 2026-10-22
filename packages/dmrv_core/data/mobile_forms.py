"""XLSForm Generator for ODK/KoboToolbox and Mobile Sync API models."""
from __future__ import annotations

from dataclasses import dataclass, field
import datetime
import io
from typing import Any, Dict, List, Optional
import openpyxl


@dataclass
class MobileSyncRecord:
    client_uuid: str
    device_id: str
    operator_id: str
    timestamp_utc: datetime.datetime
    gps_lat: float
    gps_lon: float
    gps_accuracy_m: float
    form_type: str  # "trees", "plots", "deadwood", "litter"
    data: Dict[str, Any]


@dataclass
class SyncBatchResult:
    total_records: int
    accepted_records: int
    rejected_records: int
    validation_issues: List[Dict[str, Any]]
    sync_status: str


class XLSFormGenerator:
    """Generates ODK/KoboToolbox-compliant XLSForm workbooks from dMRV schema."""

    @staticmethod
    def generate_forestry_xlsform(
        species_list: Optional[List[str]] = None,
        form_id: str = "dmrv_forestry_trees_v1",
        form_title: str = "dMRV Forestry Tree Measurement Form",
    ) -> bytes:
        """Create an openpyxl Workbook with survey, choices, and settings sheets."""
        wb = openpyxl.Workbook()

        # 1. Survey sheet
        ws_survey = wb.active
        ws_survey.title = "survey"
        survey_headers = ["type", "name", "label", "required", "constraint", "constraint_message"]
        ws_survey.append(survey_headers)

        rows = [
            ("begin_group", "plot_info", "Plot Information", "", "", ""),
            ("text", "stratum_id", "Stratum ID", "yes", "", ""),
            ("text", "plot_id", "Plot ID", "yes", "", ""),
            ("geopoint", "plot_location", "Record Plot Center GPS (< 5m accuracy)", "yes", "", ""),
            ("date", "survey_date", "Date of Measurement", "yes", "", ""),
            ("end_group", "plot_info", "", "", "", ""),
            ("begin_repeat", "tree_records", "Tree Measurements", "", "", ""),
            ("text", "tree_tag", "Tree Tag ID", "yes", "", ""),
            ("select_one species_list", "species", "Tree Species", "yes", "", ""),
            ("decimal", "dbh_cm", "Diameter at Breast Height (DBH in cm)", "yes", ". >= 5.0 and . <= 300.0", "DBH must be between 5.0 and 300.0 cm"),
            ("decimal", "height_m", "Total Tree Height (m)", "yes", ". >= 1.3 and . <= 65.0", "Height must be between 1.3 and 65.0 m"),
            ("select_one tree_health_list", "health_status", "Tree Health Status", "yes", "", ""),
            ("end_repeat", "tree_records", "", "", "", ""),
        ]
        for r in rows:
            ws_survey.append(list(r))

        # 2. Choices sheet
        ws_choices = wb.create_sheet("choices")
        choices_headers = ["list_name", "name", "label"]
        ws_choices.append(choices_headers)

        species = species_list or [
            "Tectona grandis",
            "Shorea robusta",
            "Eucalyptus tereticornis",
            "Dalbergia sissoo",
            "Acacia nilotica",
            "Azadirachta indica",
            "Avicennia marina",
            "Rhizophora mucronata",
        ]
        for sp in species:
            val_name = sp.lower().replace(" ", "_")
            ws_choices.append(["species_list", val_name, sp])

        ws_choices.append(["tree_health_list", "alive_healthy", "Alive - Healthy"])
        ws_choices.append(["tree_health_list", "alive_damaged", "Alive - Damaged/Stressed"])
        ws_choices.append(["tree_health_list", "dead_standing", "Dead - Standing"])

        # 3. Settings sheet
        ws_settings = wb.create_sheet("settings")
        ws_settings.append(["form_title", "form_id", "version", "default_language"])
        ws_settings.append([form_title, form_id, "1.0.0", "English"])

        out = io.BytesIO()
        wb.save(out)
        return out.getvalue()


class MobileSyncEngine:
    """Validates and processes offline field data synchronization."""

    @staticmethod
    def process_sync_batch(records: List[MobileSyncRecord]) -> SyncBatchResult:
        accepted = 0
        rejected = 0
        issues: List[Dict[str, Any]] = []

        seen_tags: set[str] = set()

        for rec in records:
            # Check GPS accuracy
            if rec.gps_accuracy_m > 30.0:
                rejected += 1
                issues.append({
                    "client_uuid": rec.client_uuid,
                    "error": f"GPS accuracy too poor: {rec.gps_accuracy_m:.1f} m (threshold <= 30 m)",
                    "severity": "ERROR",
                })
                continue

            # Check tree data
            if rec.form_type == "trees":
                tag = str(rec.data.get("tree_tag", ""))
                plot = str(rec.data.get("plot_id", ""))
                key = f"{plot}:{tag}"
                if key in seen_tags:
                    rejected += 1
                    issues.append({
                        "client_uuid": rec.client_uuid,
                        "error": f"Duplicate tree tag {tag} in plot {plot}",
                        "severity": "ERROR",
                    })
                    continue
                seen_tags.add(key)

                dbh = float(rec.data.get("dbh_cm", 0.0))
                if dbh < 5.0 or dbh > 300.0:
                    rejected += 1
                    issues.append({
                        "client_uuid": rec.client_uuid,
                        "error": f"DBH out of valid range: {dbh} cm",
                        "severity": "ERROR",
                    })
                    continue

            accepted += 1

        status = "COMPLETED" if rejected == 0 else ("PARTIAL" if accepted > 0 else "FAILED")
        return SyncBatchResult(
            total_records=len(records),
            accepted_records=accepted,
            rejected_records=rejected,
            validation_issues=issues,
            sync_status=status,
        )


__all__ = [
    "MobileSyncRecord",
    "SyncBatchResult",
    "XLSFormGenerator",
    "MobileSyncEngine",
]
