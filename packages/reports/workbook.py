"""Openpyxl Excel workbook generator with live formulas and lineage audit sheet."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from dmrv_core.plugin import MethodologyResult


class CarbonAccountingWorkbook:
    """Generates issuance-grade XLSX workbooks with live Excel formulas and full lineage."""

    def __init__(self, methodology_result: MethodologyResult, project_metadata: Dict[str, Any]) -> None:
        self.res = methodology_result
        self.meta = project_metadata
        self.wb = openpyxl.Workbook()

    def generate(self, output_path: Union[str, Path]) -> Path:
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)

        # Remove default sheet
        default_sheet = self.wb.active
        if default_sheet is not None:
            self.wb.remove(default_sheet)

        self._build_summary_sheet()
        self._build_annual_trajectory_sheet()
        self._build_lineage_sheet()

        self.wb.save(p)
        return p

    def _build_summary_sheet(self) -> None:
        ws = self.wb.create_sheet(title="Summary")
        ws.views.sheetView[0].showGridLines = True

        header_font = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="1B4D3E", end_color="1B4D3E", fill_type="solid")
        title_font = Font(name="Calibri", size=11, bold=True)

        ws["A1"] = "CCTS Carbon Credit Accounting - Summary Report"
        ws["A1"].font = Font(name="Calibri", size=16, bold=True, color="1B4D3E")

        metadata_rows = [
            ("Project Name:", self.meta.get("name", "A/R Project")),
            ("Project ID:", self.meta.get("project_id", "PRJ-001")),
            ("Methodology:", f"{self.res.methodology_code} v{self.res.version}"),
            ("Crediting Period:", f"{self.meta.get('crediting_period_start', '2026-01-01')} to {self.meta.get('crediting_period_end', '2045-12-31')}"),
            ("Locked GWP Set:", self.meta.get("gwp_set", "AR6")),
            ("Total Net Anthropogenic Removals (tCO2e):", self.res.summary_outputs.get("delta_C_AR_tCO2e", 0.0)),
            ("Buffer Reserve Withholding (10%):", self.res.summary_outputs.get("buffer_withholding_tCO2e", 0.0)),
            ("Net Issuable Carbon Credits (CCCs):", self.res.total_net_credits),
        ]

        for idx, (label, val) in enumerate(metadata_rows, start=3):
            ws.cell(row=idx, column=1, value=label).font = title_font
            ws.cell(row=idx, column=2, value=val)

        # Vintage breakdown table
        v_start = len(metadata_rows) + 5
        ws.cell(row=v_start, column=1, value="Calendar Year Vintage Breakdown").font = Font(name="Calibri", size=12, bold=True)
        ws.cell(row=v_start + 1, column=1, value="Vintage Year").font = header_font
        ws.cell(row=v_start + 1, column=1).fill = header_fill
        ws.cell(row=v_start + 1, column=2, value="Issuable Credits (tCO2e)").font = header_font
        ws.cell(row=v_start + 1, column=2).fill = header_fill

        curr_row = v_start + 2
        for year, credits_amt in sorted(self.res.vintage_totals.items()):
            ws.cell(row=curr_row, column=1, value=year).alignment = Alignment(horizontal="center")
            ws.cell(row=curr_row, column=2, value=credits_amt).number_format = "#,##0.00"
            curr_row += 1

        # Sum formula
        ws.cell(row=curr_row, column=1, value="Total").font = title_font
        ws.cell(row=curr_row, column=2, value=f"=SUM(B{v_start+2}:B{curr_row-1})").font = title_font
        ws.cell(row=curr_row, column=2).number_format = "#,##0.00"

        # Auto-adjust column widths
        ws.column_dimensions["A"].width = 38
        ws.column_dimensions["B"].width = 30

    def _build_annual_trajectory_sheet(self) -> None:
        ws = self.wb.create_sheet(title="Annual_Trajectory")
        ws.views.sheetView[0].showGridLines = True

        headers = [
            "Year",
            "Project Stock Change ΔC_P (tCO2e)",
            "Biomass Burning GHG_E (tCO2e)",
            "Actual Removals ΔC_ACTUAL (tCO2e)",
            "Baseline Removals ΔC_BSL (tCO2e)",
            "Displacement Leakage LK (tCO2e)",
            "Net Removals ΔC_AR (tCO2e)",
            "Cumulative tCCC (tCO2e)",
            "Period lCCC (tCO2e)",
            "Net Issuable (90%)",
        ]

        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="1B4D3E", end_color="1B4D3E", fill_type="solid")

        for col_idx, h in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col_idx, value=h)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", wrap_text=True)

        for row_idx, ann in enumerate(self.res.annual_results, start=2):
            ws.cell(row=row_idx, column=1, value=ann.year).alignment = Alignment(horizontal="center")
            ws.cell(row=row_idx, column=2, value=ann.project_removals).number_format = "#,##0.00"
            ws.cell(row=row_idx, column=3, value=ann.project_emissions).number_format = "#,##0.00"

            # Live Excel Formula for Actual: =B2 - C2
            ws.cell(row=row_idx, column=4, value=f"=B{row_idx}-C{row_idx}").number_format = "#,##0.00"

            ws.cell(row=row_idx, column=5, value=ann.baseline_removals).number_format = "#,##0.00"
            ws.cell(row=row_idx, column=6, value=ann.leakage).number_format = "#,##0.00"

            # Live Excel Formula for Net Removals: =D2 - E2 - F2
            ws.cell(row=row_idx, column=7, value=f"=D{row_idx}-E{row_idx}-F{row_idx}").number_format = "#,##0.00"

            # Cumulative tCCC formula
            if row_idx == 2:
                ws.cell(row=row_idx, column=8, value=f"=G{row_idx}").number_format = "#,##0.00"
            else:
                ws.cell(row=row_idx, column=8, value=f"=H{row_idx-1}+G{row_idx}").number_format = "#,##0.00"

            # Period lCCC
            ws.cell(row=row_idx, column=9, value=f"=G{row_idx}").number_format = "#,##0.00"

            # Net issuable after 10% buffer: =G2 * 0.90
            ws.cell(row=row_idx, column=10, value=f"=MAX(0, G{row_idx}*0.90)").number_format = "#,##0.00"

        # Widths
        for col_idx in range(1, 11):
            ws.column_dimensions[get_column_letter(col_idx)].width = 20

    def _build_lineage_sheet(self) -> None:
        ws = self.wb.create_sheet(title="Lineage_Audit")
        ws.views.sheetView[0].showGridLines = True

        headers = [
            "Node ID",
            "Tool / Methodology",
            "Equation Ref",
            "Page",
            "Inputs JSON",
            "Output Value",
            "Errata Applied",
            "Doc Description",
        ]

        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="333333", end_color="333333", fill_type="solid")

        for col_idx, h in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col_idx, value=h)
            cell.font = header_font
            cell.fill = header_fill

        for row_idx, node in enumerate(self.res.trace, start=2):
            ws.cell(row=row_idx, column=1, value=node.get("node_id", ""))
            ws.cell(row=row_idx, column=2, value=node.get("tool", ""))
            ws.cell(row=row_idx, column=3, value=f"Eq. {node.get('eq', '')}")
            ws.cell(row=row_idx, column=4, value=node.get("page", 0))
            ws.cell(row=row_idx, column=5, value=str(node.get("inputs", {})))
            ws.cell(row=row_idx, column=6, value=str(node.get("outputs", "")))
            ws.cell(row=row_idx, column=7, value=", ".join(node.get("errata_applied", [])))
            ws.cell(row=row_idx, column=8, value=node.get("doc", ""))

        for col_idx in range(1, 9):
            ws.column_dimensions[get_column_letter(col_idx)].width = 25


__all__ = ["CarbonAccountingWorkbook"]
