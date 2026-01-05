"""FastAPI application for AI Lab."""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .routers import models, chat, system, stream, training, openai, optimization, rlm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger = logging.getLogger(__name__)
    logger.info("AI Lab API starting up...")
    yield
    # Shutdown
    logger.info("AI Lab API shutting down...")


# Create FastAPI app
app = FastAPI(
    title="AI Lab API",
    description="REST API for Local LLM Platform",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware for web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(models.router, prefix="/api/models", tags=["models"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(stream.router, prefix="/ws", tags=["streaming"])
app.include_router(training.router, prefix="/api/training", tags=["training"])
app.include_router(optimization.router, prefix="/api/optimization", tags=["optimization"])
app.include_router(system.router, prefix="/api/system", tags=["system"])
app.include_router(openai.router, tags=["openai"])  # OpenAI-compatible endpoints
app.include_router(rlm.router)  # RLM endpoints (prefix defined in router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "AI Lab API",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint with backend availability."""
    # Check if MLX is available
    mlx_available = False
    try:
        import mlx
        mlx_available = True
    except ImportError:
        pass

    return {
        "status": "healthy",
        "version": "1.0.0",
        "mlx_available": mlx_available
    }
