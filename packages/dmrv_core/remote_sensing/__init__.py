"""Remote sensing processing package."""
from dmrv_core.remote_sensing.canopy_cover import (
    CanopyCoverResult,
    evaluate_canopy_cover_no_decrease,
)
from dmrv_core.remote_sensing.connectors import (
    EarthEngineConnector,
    STACClient,
    STACItem,
)
from dmrv_core.remote_sensing.fire_dnbr import (
    BurntAreaPipeline,
    CandidateBurnEvent,
    classify_burn_severity,
    compute_dnbr,
    compute_nbr,
)
from dmrv_core.remote_sensing.ndvi_sampling import (
    compute_ndvi,
    extract_plot_and_population_ndvi,
)
from dmrv_core.remote_sensing.spectral_residue import (
    ResidueComplianceResult,
    compute_ndti,
    evaluate_residue_cover_compliance,
)

__all__ = [
    "STACItem",
    "STACClient",
    "EarthEngineConnector",
    "CandidateBurnEvent",
    "BurntAreaPipeline",
    "compute_nbr",
    "compute_dnbr",
    "classify_burn_severity",
    "CanopyCoverResult",
    "evaluate_canopy_cover_no_decrease",
    "compute_ndvi",
    "extract_plot_and_population_ndvi",
    "ResidueComplianceResult",
    "compute_ndti",
    "evaluate_residue_cover_compliance",
]
