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

    # Schedule non-blocking background sync if last sync is > 6 hours old
    async def schedule_startup_events_sync():
        try:
            from app.db.session import SessionLocal
            from app.services.events_sync import EventSyncEngine
            db = SessionLocal()
            try:
                if EventSyncEngine.is_sync_needed(db, max_age_hours=settings.EVENTS_SYNC_INTERVAL_HOURS):
                    logger.info("Startup check: Events sync needed (>6h old or first run). Starting background sync...")
                    engine = EventSyncEngine()
                    res = await engine.run_sync(db)
                    logger.info(
                        f"Startup background sync completed: {res.get('new_events', 0)} new, "
                        f"{res.get('updated_events', 0)} updated, {res.get('expired_events', 0)} expired."
                    )
                else:
                    logger.info("Startup check: Events catalog is fresh (synced within last 6h).")
            finally:
                db.close()
        except Exception as sync_exc:
            logger.error(f"Background startup events sync error (non-fatal): {sync_exc}", exc_info=True)

    import asyncio
    asyncio.create_task(schedule_startup_events_sync())

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
app.include_router(api_v1_router, prefix="/api")

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


@app.get("/api/info", tags=["Health"])
def api_info():
    return root()
