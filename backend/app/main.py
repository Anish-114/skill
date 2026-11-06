import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.db.init_db import init_db
from app.models import Opportunity, Skill, User
from app.api.v1 import api_v1_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager that ensures schema creation and
    seed data loading on application startup.
    """
    logger.info("Starting SkillBridge AI Backend application...")
    logger.info("Initializing database and verifying seed data...")
    try:
        init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database on startup: {e}")
        raise e
    yield
    logger.info("Shutting down SkillBridge AI Backend application...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Intelligent platform bridging college students to hackathons, coding contests, and career opportunities.",
    lifespan=lifespan
)

# Configure CORS for local development and production
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API v1 Routes (High priority)
app.include_router(api_v1_router, prefix=settings.API_V1_STR)

# Re-exports for backwards compatibility
from app.api.v1.opportunities import list_opportunities
from app.api.v1.skills import list_skills


@app.get("/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint to verify API and DB connectivity."""
    try:
        opportunity_count = db.query(Opportunity).count()
        skill_count = db.query(Skill).count()
        user_count = db.query(User).count()
        return {
            "status": "healthy",
            "database": "connected",
            "stats": {
                "opportunities": opportunity_count,
                "skills": skill_count,
                "users": user_count
            }
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database connection error: {str(exc)}"
        )


def root():
    """Application metadata endpoint helper."""
    return {
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs_url": "/docs",
        "api_v1": settings.API_V1_STR
    }


# Static Files & SPA Routing
static_dir = Path(__file__).parent / "static"
if not static_dir.exists():
    alt_static = Path("/app/backend/app/static")
    if alt_static.exists():
        static_dir = alt_static

index_html_path = static_dir / "index.html"

if static_dir.exists() and index_html_path.exists():
    logger.info(f"Serving frontend SPA from static directory: {static_dir}")
    assets_dir = static_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/", tags=["SPA"], include_in_schema=False)
    def serve_spa_root():
        return FileResponse(str(index_html_path))

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa_catch_all(full_path: str):
        # Do not intercept API, health, or swagger docs
        if full_path.startswith("api/") or full_path in ["health", "docs", "openapi.json", "redoc"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource Not Found")

        file_path = static_dir / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))

        if index_html_path.exists():
            return FileResponse(str(index_html_path))

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page Not Found")
else:
    @app.get("/", tags=["Health"])
    def serve_root_api():
        return root()
