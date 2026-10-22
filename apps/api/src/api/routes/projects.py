"""Project management API enforcing CCTS regulatory rules."""
import datetime
from typing import Any, Dict, List

from core.security import get_current_user_payload
from db.base import get_db
from db.models import Client, Project
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

router = APIRouter(prefix="/projects", tags=["Projects"])

EARLIEST_START_DATE = datetime.date(2025, 1, 1)


class ProjectCreate(BaseModel):
    client_name: str
    name: str
    project_type: str = Field(..., description="P1 (A/R), P2 (Mangrove), P3 (Waste), etc.")
    methodology_code: str = Field(..., description="e.g. BM FR05.002, BM WA03.002")
    methodology_version: str = "1.0"
    start_date: datetime.date = Field(..., description="Activity start date (>= 2025-01-01)")
    crediting_period_type: str = Field("fixed_10_year", description="fixed_10_year or renewable_5_year")
    locked_gwp_set: str = Field("AR6", description="IPCC GWP set: AR6 or SAR_as_printed")


class ProjectResponse(BaseModel):
    id: str
    name: str
    project_type: str
    methodology_code: str
    methodology_version: str
    start_date: datetime.date
    crediting_period_type: str
    locked_gwp_set: str
    status: str
    created_at: datetime.datetime


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    req: ProjectCreate,
    db: Session = Depends(get_db),
    user_payload: Dict[str, Any] = Depends(get_current_user_payload),
):
    # Rule 30: Project start date not before 1 Jan 2025
    if req.start_date < EARLIEST_START_DATE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CCTS Offset Rule: Project start date ({req.start_date}) cannot be before 1 Jan 2025. No retrospective projects allowed.",
        )

    # Validate crediting period
    if req.crediting_period_type not in ("fixed_10_year", "renewable_5_year"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Crediting period must be 'fixed_10_year' or 'renewable_5_year'.",
        )

    org_id = user_payload.get("org_id", "default_org")
    client = db.query(Client).filter(Client.name == req.client_name).first()
    if not client:
        client = Client(organization_id=org_id, name=req.client_name)
        db.add(client)
        db.commit()
        db.refresh(client)

    project = Project(
        client_id=client.id,
        name=req.name,
        project_type=req.project_type,
        methodology_code=req.methodology_code,
        methodology_version=req.methodology_version,
        locked_gwp_set=req.locked_gwp_set,
        start_date=datetime.datetime.combine(req.start_date, datetime.time.min),
        crediting_period_type=req.crediting_period_type,
        status="concept",
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    return ProjectResponse(
        id=project.id,
        name=project.name,
        project_type=project.project_type,
        methodology_code=project.methodology_code,
        methodology_version=project.methodology_version,
        start_date=project.start_date.date(),
        crediting_period_type=project.crediting_period_type,
        locked_gwp_set=project.locked_gwp_set,
        status=project.status,
        created_at=project.created_at,
    )


@router.get("", response_model=List[ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    return [
        ProjectResponse(
            id=p.id,
            name=p.name,
            project_type=p.project_type,
            methodology_code=p.methodology_code,
            methodology_version=p.methodology_version,
            start_date=p.start_date.date(),
            crediting_period_type=p.crediting_period_type,
            locked_gwp_set=p.locked_gwp_set,
            status=p.status,
            created_at=p.created_at,
        )
        for p in projects
    ]
