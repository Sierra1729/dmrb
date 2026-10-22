"""Parameter catalogue inspector API."""
from pathlib import Path
from typing import Any, Dict

from dmrv_core import ParameterCatalogue
from fastapi import APIRouter

router = APIRouter(prefix="/catalogue", tags=["Parameter Catalogue"])

_catalogue_cache = None


def get_catalogue() -> ParameterCatalogue:
    global _catalogue_cache
    if _catalogue_cache is None:
        cat_path = Path("specs/14_parameter_catalogue.yaml")
        _catalogue_cache = ParameterCatalogue.load_from_file(cat_path)
    return _catalogue_cache


@router.get("/summary")
def get_catalogue_summary() -> Dict[str, Any]:
    cat = get_catalogue()
    return {
        "version": cat.version,
        "default_gwp_set": cat.default_gwp_set,
        "gwp_sets": cat.gwp_sets,
        "tools_available": [k for k in cat.raw_data.keys() if k.startswith("BM-") or "SOC" in k],
        "global_parameters": cat.global_params,
    }


@router.get("/tool/{tool_code}")
def get_tool_parameters(tool_code: str) -> Dict[str, Any]:
    cat = get_catalogue()
    return cat.get_tool_params(tool_code)
