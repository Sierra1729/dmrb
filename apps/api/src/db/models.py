"""SQLAlchemy 2 database models reflecting specs/13_data_model_and_QAQC.md."""
from __future__ import annotations

import datetime
import uuid

from db.base import Base
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    clients = relationship("Client", back_populates="organization")
    users = relationship("User", back_populates="organization")


class Client(Base):
    __tablename__ = "clients"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    organization = relationship("Organization", back_populates="clients")
    projects = relationship("Project", back_populates="client")


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="CarbonAnalyst")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    organization = relationship("Organization", back_populates="users")


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    client_id = Column(String(36), ForeignKey("clients.id"), nullable=False)
    name = Column(String(255), nullable=False)
    project_type = Column(String(50), nullable=False)  # P1, P2, P3, etc.
    methodology_code = Column(String(50), nullable=False)  # BM FR05.002, etc.
    methodology_version = Column(String(20), nullable=False, default="1.0")
    tool_versions = Column(JSON, default=dict)  # locked tool versions
    locked_gwp_set = Column(String(50), default="AR6", nullable=False)
    start_date = Column(DateTime, nullable=False)
    crediting_period_type = Column(String(50), default="fixed_10_year")  # fixed_10_year or renewable_5_year
    status = Column(String(50), default="concept")  # concept, pdd, validation, registered, monitoring, verification, issuance
    icm_registry_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    client = relationship("Client", back_populates="projects")
    strata = relationship("Stratum", back_populates="project")
    calculation_runs = relationship("CalculationRun", back_populates="project")


class Stratum(Base):
    __tablename__ = "strata"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    scenario = Column(String(20), nullable=False, default="PROJ")  # BSL or PROJ
    area_ha = Column(Float, nullable=False)
    geometry_wkt = Column(Text, nullable=True)  # WKT representation in EPSG:4326
    attributes = Column(JSON, default=dict)  # climate, soil, land use, management, crown cover
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    project = relationship("Project", back_populates="strata")
    plots = relationship("Plot", back_populates="stratum")


class Plot(Base):
    __tablename__ = "plots"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    stratum_id = Column(String(36), ForeignKey("strata.id"), nullable=False)
    plot_number = Column(String(50), nullable=False)
    plot_type = Column(String(50), default="fixed")  # fixed or variable
    plot_area_ha = Column(Float, nullable=False)
    center_lat = Column(Float, nullable=True)
    center_lon = Column(Float, nullable=True)
    gps_accuracy_m = Column(Float, nullable=True)
    permanent = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    stratum = relationship("Stratum", back_populates="plots")


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    file_id = Column(String(100), nullable=False)
    filename = Column(String(255), nullable=False)
    sha256 = Column(String(64), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    uploaded_by = Column(String(255), nullable=False)
    captured_at = Column(DateTime, nullable=True)
    gps_lat = Column(Float, nullable=True)
    gps_lon = Column(Float, nullable=True)
    linked_entity_type = Column(String(50), nullable=True)
    linked_entity_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(255), nullable=False)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String(36), nullable=False)
    changes = Column(JSON, default=dict)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class CalculationRun(Base):
    __tablename__ = "calculation_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    run_type = Column(String(50), default="ex_post")  # ex_ante, ex_post, draft
    status = Column(String(50), default="completed")  # running, completed, reviewed, approved, rejected
    is_issuance_grade = Column(Boolean, default=False)
    engine_version = Column(String(50), default="0.1.0")
    git_sha = Column(String(40), default="HEAD")
    input_snapshot_hash = Column(String(64), nullable=False)
    param_set_hash = Column(String(64), nullable=False)
    outputs = Column(JSON, default=dict)
    trace = Column(JSON, default=list)
    errata_applied = Column(JSON, default=list)
    warnings = Column(JSON, default=list)
    reviewed_by = Column(String(255), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    project = relationship("Project", back_populates="calculation_runs")
