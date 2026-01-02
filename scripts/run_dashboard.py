"""
Run Dashboard Server

Standalone script to start the FastAPI dashboard server.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import uvicorn
from config.settings import DASHBOARD_HOST, DASHBOARD_PORT, DEBUG_MODE, MODEL_DIR, PROCESSED_DATA_DIR
from config.logging_config import logger


def check_prerequisites():
    """Check if model and data are ready"""
    model_path = MODEL_DIR / "random_forest_model.pkl"
    extractor_path = PROCESSED_DATA_DIR / "feature_extractor.pkl"

    missing = []

    if not model_path.exists():
        missing.append("ML model")

    if not extractor_path.exists():
        missing.append("Feature extractor")

    if missing:
        logger.error("Missing required components: " + ", ".join(missing))
        logger.error("\nPlease run the following scripts first:")
        logger.error("  1. python scripts/generate_data.py")
        logger.error("  2. python scripts/train_model.py")
        return False

    return True


def main():
    """Start the dashboard server"""
    logger.info("=" * 60)
    logger.info("AI SECURITY DECISION EXPLAINER - DASHBOARD")
    logger.info("=" * 60)

    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)

    logger.info("Prerequisites check: OK")
    logger.info(f"\nStarting dashboard server...")
    logger.info(f"Host: {DASHBOARD_HOST}")
    logger.info(f"Port: {DASHBOARD_PORT}")
    logger.info(f"Debug mode: {DEBUG_MODE}")
    logger.info("\n" + "=" * 60)
    logger.info(f"Dashboard URL: http://{DASHBOARD_HOST}:{DASHBOARD_PORT}")
    logger.info(f"API Docs: http://{DASHBOARD_HOST}:{DASHBOARD_PORT}/docs")
    logger.info("=" * 60)
    logger.info("\nPress CTRL+C to stop the server\n")

    try:
        uvicorn.run(
            "src.dashboard.app:app",
            host=DASHBOARD_HOST,
            port=DASHBOARD_PORT,
            reload=DEBUG_MODE,
            log_level="info"
        )
    except KeyboardInterrupt:
        logger.info("\nShutting down dashboard...")
    except Exception as e:
        logger.error(f"Error running dashboard: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
