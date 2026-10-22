"""Forestry field data ingestion, validation, and allometric evaluation."""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import yaml


@dataclass
class StratumData:
    stratum_id: str
    project_id: str
    scenario: str
    name: str
    area_ha: float
    geometry_wkt: str = ""
    climate_zone: str = "tropical_moist"
    soil_class: str = "LAC"
    land_use: str = "plantation"
    management: str = ""
    input_level: str = ""
    crown_cover_tree: float = 0.0
    crown_cover_shrub: float = 0.0


@dataclass
class PlotData:
    plot_id: str
    stratum_id: str
    plot_type: str = "fixed"
    shape: str = "circle"
    radius_m: Optional[float] = None
    side_m: Optional[float] = None
    plot_area_ha: float = 0.04
    center_lat: float = 0.0
    center_lon: float = 0.0
    gps_accuracy_m: float = 3.0
    permanent: bool = True
    measurement_date: str = ""
    team_id: str = ""


@dataclass
class TreeMeasurement:
    plot_id: str
    tree_no: int
    species_code: str
    status: str  # "live", "dead"
    dbh_cm: float
    height_m: Optional[float] = None
    diameter_type: str = "dbh"
    coppice: bool = False
    multi_stem_id: Optional[str] = None
    remarks: str = ""


@dataclass
class StumpMeasurement:
    plot_id: str
    stump_no: int
    species_code: str
    height_m: float
    dbh_cm: Optional[float] = None
    mid_diameter_cm: Optional[float] = None
    decay_class: str = "sound"  # "sound", "intermediate", "rotten"


@dataclass
class DeadwoodTransectPiece:
    plot_id: str
    line_no: int
    line_length_m: float
    piece_no: int
    species_code: str
    diameter_cm: float
    decay_class: str = "sound"


@dataclass
class LitterSample:
    plot_id: str
    sample_date: str
    n_frames: int
    frame_area_m2: float
    composite_wet_kg: float
    subsample_wet_g: float
    subsample_dry_g: float


@dataclass
class ShrubCoverRecord:
    stratum_id: str
    method: str
    crown_cover_fraction: float
    date: str


@dataclass
class SpeciesParam:
    species_code: str
    scientific_name: str
    wood_density_t_m3: float
    bef2: Optional[float] = None
    root_shoot_method: str = "formula"
    root_shoot_value: Optional[float] = None
    allometric_eq_id: Optional[str] = None
    volume_eq_id: Optional[str] = None
    source_citation: str = ""


@dataclass
class AllometricEquation:
    id: str
    species_codes: List[str]
    form: str
    params: Dict[str, float]
    inputs: Dict[str, str]
    output_unit: str  # "kg", "t_dm"
    valid_dbh_cm: List[float] = field(default_factory=lambda: [5.0, 300.0])

    def evaluate(self, dbh_cm: float, height_m: Optional[float] = None) -> float:
        """Safely evaluate allometric expression in a sandbox without arbitrary code execution."""
        # Allowed math functions
        safe_env = {
            "exp": math.exp,
            "ln": math.log,
            "log": math.log,
            "sqrt": math.sqrt,
            "pi": math.pi,
            "dbh_cm": float(dbh_cm),
            "h_m": float(height_m) if height_m is not None else 0.0,
            "h": float(height_m) if height_m is not None else 0.0,
        }
        safe_env.update(self.params)

        # Disallow dangerous builtins
        compiled = compile(self.form, "<allometric_eq>", "eval")
        for name in compiled.co_names:
            if name not in safe_env:
                raise ValueError(f"Unsafe or undefined identifier in equation: {name}")

        val = eval(compiled, {"__builtins__": {}}, safe_env)  # pylint: disable=eval-used
        result = float(val)

        # Convert output unit to t d.m.
        if self.output_unit == "kg":
            return result / 1000.0
        return result


class ForestryDataset:
    """Container for ingested forestry monitoring data."""

    def __init__(self) -> None:
        self.strata: Dict[str, StratumData] = {}
        self.plots: Dict[str, PlotData] = {}
        self.trees: List[TreeMeasurement] = []
        self.stumps: List[StumpMeasurement] = []
        self.deadwood_pieces: List[DeadwoodTransectPiece] = []
        self.litter_samples: List[LitterSample] = []
        self.shrub_records: List[ShrubCoverRecord] = []
        self.species: Dict[str, SpeciesParam] = {}
        self.allometric_equations: Dict[str, AllometricEquation] = {}

    @classmethod
    def load_from_directory(cls, dir_path: Union[str, Path]) -> ForestryDataset:
        """Ingest all forestry CSVs and YAMLs from a directory."""
        p = Path(dir_path)
        ds = cls()

        # 1. Species params
        if (p / "species_params.csv").exists():
            with open(p / "species_params.csv", mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    sp = SpeciesParam(
                        species_code=r["species_code"].strip(),
                        scientific_name=r.get("scientific_name", "").strip(),
                        wood_density_t_m3=float(r["wood_density_t_m3"]),
                        bef2=float(r["bef2"]) if r.get("bef2") else None,
                        root_shoot_method=r.get("root_shoot_method", "formula").strip(),
                        root_shoot_value=float(r["root_shoot_value"]) if r.get("root_shoot_value") else None,
                        allometric_eq_id=r.get("allometric_eq_id", "").strip() or None,
                        source_citation=r.get("source_citation", "").strip(),
                    )
                    ds.species[sp.species_code] = sp

        # 2. Allometric equations
        if (p / "allometric_equations.yaml").exists():
            with open(p / "allometric_equations.yaml", mode="r", encoding="utf-8") as f:
                raw_eqs = yaml.safe_load(f) or []
                for entry in raw_eqs:
                    eq = AllometricEquation(
                        id=entry["id"],
                        species_codes=entry.get("species_codes", []),
                        form=entry["form"],
                        params=entry.get("params", {}),
                        inputs=entry.get("inputs", {}),
                        output_unit=entry.get("output_unit", "kg"),
                        valid_dbh_cm=entry.get("valid_dbh_cm", [5.0, 300.0]),
                    )
                    ds.allometric_equations[eq.id] = eq

        # 3. Strata
        if (p / "strata.csv").exists():
            with open(p / "strata.csv", mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    s = StratumData(
                        stratum_id=r["stratum_id"].strip(),
                        project_id=r["project_id"].strip(),
                        scenario=r["scenario"].strip(),
                        name=r["name"].strip(),
                        area_ha=float(r["area_ha_declared"]),
                        geometry_wkt=r.get("geometry_wkt", "").strip(),
                        climate_zone=r.get("climate_zone", "tropical_moist").strip(),
                        soil_class=r.get("soil_class", "LAC").strip(),
                        land_use=r.get("land_use", "plantation").strip(),
                        crown_cover_tree=float(r["crown_cover_tree"]) if r.get("crown_cover_tree") else 0.0,
                        crown_cover_shrub=float(r["crown_cover_shrub"]) if r.get("crown_cover_shrub") else 0.0,
                    )
                    ds.strata[s.stratum_id] = s

        # 4. Plots
        if (p / "plots.csv").exists():
            with open(p / "plots.csv", mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    plot = PlotData(
                        plot_id=r["plot_id"].strip(),
                        stratum_id=r["stratum_id"].strip(),
                        plot_type=r.get("plot_type", "fixed").strip(),
                        shape=r.get("shape", "circle").strip(),
                        radius_m=float(r["radius_m"]) if r.get("radius_m") else None,
                        plot_area_ha=float(r.get("plot_area_ha", 0.04)),
                        center_lat=float(r["center_lat"]) if r.get("center_lat") else 0.0,
                        center_lon=float(r["center_lon"]) if r.get("center_lon") else 0.0,
                        gps_accuracy_m=float(r.get("gps_accuracy_m", 3.0)),
                        permanent=r.get("permanent", "y").lower() == "y",
                        measurement_date=r.get("measurement_date", "").strip(),
                        team_id=r.get("team_id", "").strip(),
                    )
                    ds.plots[plot.plot_id] = plot

        # 5. Trees
        if (p / "trees.csv").exists():
            with open(p / "trees.csv", mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    t = TreeMeasurement(
                        plot_id=r["plot_id"].strip(),
                        tree_no=int(r["tree_no"]),
                        species_code=r["species_code"].strip(),
                        status=r.get("status", "live").strip(),
                        dbh_cm=float(r["dbh_cm"]),
                        height_m=float(r["height_m"]) if r.get("height_m") else None,
                        coppice=r.get("coppice", "n").lower() == "y",
                        remarks=r.get("remarks", "").strip(),
                    )
                    ds.trees.append(t)

        # 6. Stumps
        if (p / "stumps.csv").exists():
            with open(p / "stumps.csv", mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    stump = StumpMeasurement(
                        plot_id=r["plot_id"].strip(),
                        stump_no=int(r["stump_no"]),
                        species_code=r["species_code"].strip(),
                        height_m=float(r["height_m"]),
                        dbh_cm=float(r["dbh_cm"]) if r.get("dbh_cm") else None,
                        mid_diameter_cm=float(r["mid_diameter_cm"]) if r.get("mid_diameter_cm") else None,
                        decay_class=r.get("decay_class", "sound").strip(),
                    )
                    ds.stumps.append(stump)

        # 7. Deadwood transects
        if (p / "deadwood_transects.csv").exists():
            with open(p / "deadwood_transects.csv", mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    dw = DeadwoodTransectPiece(
                        plot_id=r["plot_id"].strip(),
                        line_no=int(r["line_no"]),
                        line_length_m=float(r["line_length_m"]),
                        piece_no=int(r["piece_no"]),
                        species_code=r["species_code"].strip(),
                        diameter_cm=float(r["diameter_cm"]),
                        decay_class=r.get("decay_class", "sound").strip(),
                    )
                    ds.deadwood_pieces.append(dw)

        # 8. Litter samples
        if (p / "litter_samples.csv").exists():
            with open(p / "litter_samples.csv", mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    lit = LitterSample(
                        plot_id=r["plot_id"].strip(),
                        sample_date=r.get("sample_date", "").strip(),
                        n_frames=int(r.get("n_frames", 4)),
                        frame_area_m2=float(r.get("frame_area_m2", 0.5)),
                        composite_wet_kg=float(r["composite_wet_kg"]),
                        subsample_wet_g=float(r["subsample_wet_g"]),
                        subsample_dry_g=float(r["subsample_dry_g"]),
                    )
                    ds.litter_samples.append(lit)

        # 9. Shrub cover
        if (p / "shrub_cover.csv").exists():
            with open(p / "shrub_cover.csv", mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    sc = ShrubCoverRecord(
                        stratum_id=r["stratum_id"].strip(),
                        method=r.get("method", "line_transect").strip(),
                        crown_cover_fraction=float(r["crown_cover_fraction"]),
                        date=r.get("date", "").strip(),
                    )
                    ds.shrub_records.append(sc)

        return ds


__all__ = [
    "StratumData",
    "PlotData",
    "TreeMeasurement",
    "StumpMeasurement",
    "DeadwoodTransectPiece",
    "LitterSample",
    "ShrubCoverRecord",
    "SpeciesParam",
    "AllometricEquation",
    "ForestryDataset",
]
