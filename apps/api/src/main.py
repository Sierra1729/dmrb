"""FastAPI Application entrypoint for dMRV Platform."""
from contextlib import asynccontextmanager

from api.routes.auth import router as auth_router
from api.routes.catalogue import router as catalogue_router
from api.routes.lineage import router as lineage_router
from api.routes.projects import router as projects_router
from core.config import settings
from core.security import hash_password
from db.base import Base, SessionLocal, engine
from db.models import Organization, User
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB schema
    Base.metadata.create_all(bind=engine)

    # Seed default organization and admin user for initial access
    db = SessionLocal()
    try:
        org = db.query(Organization).first()
        if not org:
            org = Organization(name=settings.FIRM_NAME)
            db.add(org)
            db.commit()
            db.refresh(org)

        admin = db.query(User).filter(User.email == "admin@carbonbridge.in").first()
        if not admin:
            admin = User(
                organization_id=org.id,
                email="admin@carbonbridge.in",
                hashed_password=hash_password("AdminPass123!"),
                full_name="Platform Administrator",
                role="OrgAdmin",
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()

    yield


app = FastAPI(
    title=f"{settings.PRODUCT_NAME} API",
    description="Digital MRV and Carbon Accounting Platform for the Indian Carbon Market (CCTS Offset Mechanism)",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(projects_router, prefix=settings.API_V1_STR)
app.include_router(lineage_router, prefix=settings.API_V1_STR)
app.include_router(catalogue_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "product": settings.PRODUCT_NAME,
        "firm": settings.FIRM_NAME,
        "version": "0.1.0",
    }


@app.get("/", response_class=HTMLResponse, tags=["Dashboard UI"])
def get_dashboard_ui():
    """Serves the interactive dMRV platform web dashboard."""
    static_file = Path(__file__).parent / "static" / "index.html"
    if static_file.exists():
        return HTMLResponse(content=static_file.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>dMRV Platform</h1>")


# Serve static assets and report downloads
_static_dir = Path(__file__).parent / "static"
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")

