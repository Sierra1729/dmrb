"""Integration tests for FastAPI application endpoints."""
import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure packages and apps/api/src are in sys.path
root_dir = Path(".").resolve()
pkgs_dir = (root_dir / "packages").resolve()
api_src = (root_dir / "apps" / "api" / "src").resolve()

for p in [str(root_dir), str(pkgs_dir), str(api_src)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_dashboard_ui_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "CarbonBridge dMRV" in response.text
    assert "Portfolio & Pipeline" in response.text



def test_auth_and_login(client):
    # Login with seeded admin
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@carbonbridge.in", "password": "AdminPass123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["role"] == "OrgAdmin"


def test_catalogue_summary(client):
    response = client.get("/api/v1/catalogue/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "2026.10-01"
    assert data["default_gwp_set"] == "AR6"
    assert "AR6" in data["gwp_sets"]
    assert data["gwp_sets"]["AR6"]["CH4"] == 29.8


def test_lineage_trace_endpoint(client):
    response = client.post(
        "/api/v1/lineage/sample-calculation",
        json={
            "mean_biomass_t_dm_ha": 45.328,
            "sd_biomass_t_dm_ha": 12.776,
            "plot_count": 34,
        },
    )
    assert response.status_code == 200
    data = response.json()
    # Check values match AR-0004 PDF example: SEM ~2.191, t ~1.692, U ~8.18%
    assert pytest.approx(data["standard_error_mean"], 0.001) == 2.191
    assert pytest.approx(data["t_critical_value"], 0.001) == 1.692
    assert pytest.approx(data["uncertainty_pct"], 0.01) == 8.18
    assert data["is_uncertainty_acceptable"] is True

    # Lineage DAG verified
    assert len(data["trace_dag"]) == 1
    node = data["trace_dag"][0]
    assert node["tool"] == "BM-T-AR-0004"
    assert node["eq"] == "15"
    assert node["page"] == 14
    assert "E-AR4-07" in node["errata_applied"]


def test_project_creation_and_rules(client):
    # Login to get auth token
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@carbonbridge.in", "password": "AdminPass123!"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Reject retrospective start date (< 2025-01-01)
    bad_res = client.post(
        "/api/v1/projects",
        headers=headers,
        json={
            "client_name": "Test Client",
            "name": "Historical Forestry Project",
            "project_type": "P1",
            "methodology_code": "BM FR05.002",
            "start_date": "2024-12-31",
            "crediting_period_type": "fixed_10_year",
            "locked_gwp_set": "AR6",
        },
    )
    assert bad_res.status_code == 400
    assert "2025" in bad_res.json()["detail"]

    # 2. Accept compliant start date (>= 2025-01-01)
    good_res = client.post(
        "/api/v1/projects",
        headers=headers,
        json={
            "client_name": "Tata Carbon Solutions",
            "name": "Western Ghats Reforestation",
            "project_type": "P1",
            "methodology_code": "BM FR05.002",
            "start_date": "2025-03-01",
            "crediting_period_type": "fixed_10_year",
            "locked_gwp_set": "AR6",
        },
    )
    assert good_res.status_code == 201
    proj_data = good_res.json()
    assert proj_data["name"] == "Western Ghats Reforestation"
    assert proj_data["locked_gwp_set"] == "AR6"
    assert proj_data["status"] == "concept"
