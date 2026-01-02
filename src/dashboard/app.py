"""
FastAPI Dashboard Application

Main application for the AI Security Decision Explainer dashboard.
"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from loguru import logger

from config.settings import DEBUG_MODE, DASHBOARD_HOST, DASHBOARD_PORT
from config.logging_config import setup_logging

# Setup logging
setup_logging()

# Initialize FastAPI app
app = FastAPI(
    title="AI Security Decision Explainer",
    description="Trust-first AI security system for SOC environments",
    version="1.0.0",
    debug=DEBUG_MODE
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup static files and templates
dashboard_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=str(dashboard_dir / "static")), name="static")
templates = Jinja2Templates(directory=str(dashboard_dir / "templates"))

# Import routes
from src.dashboard import routes

# Include routes
app.include_router(routes.router)


@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    logger.info("=" * 60)
    logger.info("AI SECURITY DECISION EXPLAINER - Starting up...")
    logger.info("=" * 60)
    logger.info(f"Debug mode: {DEBUG_MODE}")
    logger.info(f"Host: {DASHBOARD_HOST}:{DASHBOARD_PORT}")

    # Load ML components
    try:
        from src.ml_engine.model_trainer import ModelTrainer
        from src.feature_engineering.feature_extractor import FeatureExtractor

        logger.info("Loading ML model and feature extractor...")
        app.state.model_trainer = ModelTrainer.load()
        app.state.feature_extractor = FeatureExtractor.load()
        logger.info("ML components loaded successfully")

    except FileNotFoundError as e:
        logger.warning(f"ML components not found: {e}")
        logger.warning("Please train the model first using scripts/train_model.py")
        app.state.model_trainer = None
        app.state.feature_extractor = None

    logger.info("Dashboard ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down AI Security Decision Explainer...")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": app.state.model_trainer is not None,
        "feature_extractor_loaded": app.state.feature_extractor is not None
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.dashboard.app:app",
        host=DASHBOARD_HOST,
        port=DASHBOARD_PORT,
        reload=DEBUG_MODE,
        log_level="info"
    )
