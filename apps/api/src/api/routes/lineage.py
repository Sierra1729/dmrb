"""Sample traced calculation endpoint demonstrating lineage DAG in OpenAPI."""
from typing import Any, Dict, List

from dmrv_core import CalculationContext, equation, t_two_sided
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/lineage", tags=["Lineage & Trace"])


class SampleLineageRequest(BaseModel):
    mean_biomass_t_dm_ha: float = Field(45.328, description="Mean biomass in t d.m./ha (AR-0004 PDF p.4)")
    sd_biomass_t_dm_ha: float = Field(12.776, description="Standard deviation in t d.m./ha")
    plot_count: int = Field(34, description="Number of sample plots")


class SampleLineageResponse(BaseModel):
    standard_error_mean: float
    t_critical_value: float
    uncertainty_pct: float
    is_uncertainty_acceptable: bool
    trace_dag: List[Dict[str, Any]]
    active_errata: List[str]


@equation(
    tool="BM-T-AR-0004",
    version="1.0",
    eq="15",
    page=14,
    doc="u_C = t_VAL * sqrt(sum_i w_i^2 * s_i^2 / n_i) / b_TREE",
    errata_ids=["E-AR4-07"],
)
def compute_uncertainty_sample(
    mean_b: float,
    sd_b: float,
    n: int,
    ctx: CalculationContext,
) -> Dict[str, float]:
    import math

    # Calculate SEM: standard error of the mean
    sem = sd_b / math.sqrt(n)
    t_val = t_two_sided(0.90, n - 1)
    u_pct = (sem * t_val / mean_b) * 100.0

    return {
        "sem": sem,
        "t_val": t_val,
        "uncertainty_pct": u_pct,
    }


@router.post("/sample-calculation", response_model=SampleLineageResponse)
def execute_sample_calculation(req: SampleLineageRequest):
    """Executes a sample traced calculation from BM-T-AR-0004 and returns its full lineage DAG."""
    ctx = CalculationContext(
        project_id="demo_forestry_project",
        scenario="project",
    )

    res = compute_uncertainty_sample(
        req.mean_biomass_t_dm_ha,
        req.sd_biomass_t_dm_ha,
        req.plot_count,
        ctx=ctx,
    )

    return SampleLineageResponse(
        standard_error_mean=round(res["sem"], 4),
        t_critical_value=round(res["t_val"], 4),
        uncertainty_pct=round(res["uncertainty_pct"], 2),
        is_uncertainty_acceptable=res["uncertainty_pct"] <= 10.0,
        trace_dag=ctx.get_trace_dict(),
        active_errata=list(ctx.active_errata_used),
    )
