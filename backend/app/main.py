"""
ResQNet AI - FastAPI Application Factory
Main entry point with lifespan management for database connections,
CORS configuration, and route registration.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging
import sys

from app.config import get_settings
from app.db.mongodb import connect_mongodb, close_mongodb
from app.db.redis_client import connect_redis, close_redis
from app.db.chromadb_client import connect_chromadb, close_chromadb
from app.api.v1.router import router as v1_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Connects to databases on startup, disconnects on shutdown.
    """
    settings = get_settings()
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"   Environment: {settings.ENVIRONMENT}")

    # Connect to databases
    try:
        await connect_mongodb()
        logger.info("✅ MongoDB connected")
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        logger.warning("⚠️  Continuing without MongoDB — some features will be unavailable")

    try:
        await connect_redis()
        logger.info("✅ Redis connected")
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        logger.warning("⚠️  Continuing without Redis — caching and rate limiting disabled")

    try:
        connect_chromadb()
        logger.info("✅ ChromaDB connected")
    except Exception as e:
        logger.error(f"❌ ChromaDB connection failed: {e}")
        logger.warning("⚠️  Continuing without ChromaDB — duplicate detection and RAG disabled")

    # Initialize RAG SOP Database
    try:
        from app.ai.rag_engine import initialize_sop_db
        initialize_sop_db()
        logger.info("✅ RAG SOP database initialized")
    except Exception as e:
        logger.error(f"❌ RAG SOP database initialization failed: {e}")

    # Create upload directory
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"🟢 {settings.APP_NAME} is ready!")
    logger.info(f"   API docs: http://{settings.HOST}:{settings.PORT}/docs")

    yield  # Application runs here

    # Shutdown
    logger.info(f"🔴 Shutting down {settings.APP_NAME}...")
    await close_mongodb()
    await close_redis()
    close_chromadb()
    logger.info("👋 Goodbye!")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "AI-Powered Emergency Response Command Center — "
            "Transforms fragmented emergency reports into actionable intelligence."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routes
    app.include_router(v1_router)

    # Health check endpoint
    @app.get("/health", tags=["System"])
    async def health_check():
        return {
            "status": "healthy",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
        }

    # Mount static files for uploads
    upload_path = Path(settings.UPLOAD_DIR)
    upload_path.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(upload_path)), name="uploads")

    return app


# Create the app instance
app = create_app()
