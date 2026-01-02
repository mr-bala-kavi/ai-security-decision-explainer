"""
FastAPI Routes for Dashboard

API endpoints for alert analysis and dashboard operations.
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from pathlib import Path
from typing import List, Dict
from loguru import logger

from src.ingestion.alert_loader import AlertLoader
from src.ml_engine.model_predictor import ModelPredictor
from src.xai.shap_explainer import SHAPExplainer
from src.llm_engine.claude_client import ClaudeExplainer
from config.settings import ALERTS_CSV_PATH, ALERT_LABELS

# Setup templates
dashboard_dir = Path(__file__).parent
templates = Jinja2Templates(directory=str(dashboard_dir / "templates"))

router = APIRouter()


# Request/Response models
class AnalyzeRequest(BaseModel):
    alert_id: str


class AlertResponse(BaseModel):
    alert_id: str
    timestamp: str
    source_ip: str
    destination_ip: str
    label: str


@router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Serve main dashboard HTML"""
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/api/alerts")
async def get_alerts() -> Dict:
    """
    Get list of available alerts

    Returns:
        Dictionary with alerts list
    """
    try:
        # Load alerts from CSV
        df = AlertLoader.load_csv(ALERTS_CSV_PATH)

        # Convert to list of dictionaries (first 100 for performance)
        alerts_subset = df.head(100)
        alerts_list = []

        for _, row in alerts_subset.iterrows():
            alerts_list.append({
                "alert_id": row['alert_id'],
                "timestamp": row['timestamp'],
                "source_ip": row['source_ip'],
                "destination_ip": row['destination_ip'],
                "true_label": row['label']
            })

        return {
            "success": True,
            "count": len(alerts_list),
            "alerts": alerts_list
        }

    except Exception as e:
        logger.error(f"Error loading alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/analyze")
async def analyze_alert(request: Request, data: AnalyzeRequest) -> Dict:
    """
    Analyze a security alert through the full pipeline

    Pipeline:
    1. Load alert
    2. Engineer features
    3. ML prediction
    4. SHAP explanation
    5. Claude explanation

    Args:
        request: FastAPI request object
        data: Alert ID to analyze

    Returns:
        Complete analysis including prediction, XAI, and LLM explanation
    """
    alert_id = data.alert_id

    # Check if model is loaded
    if request.app.state.model_trainer is None:
        raise HTTPException(
            status_code=503,
            detail="ML model not loaded. Please train the model first."
        )

    try:
        logger.info(f"Analyzing alert: {alert_id}")

        # Step 1: Load alert
        df = AlertLoader.load_csv(ALERTS_CSV_PATH)
        alert_row = AlertLoader.get_alert_by_id(df, alert_id)
        alert_data = alert_row.to_dict()

        logger.info(f"Alert loaded: {alert_data['source_ip']} -> {alert_data['destination_ip']}")

        # Step 2: Engineer features
        feature_extractor = request.app.state.feature_extractor
        alert_df = alert_row.to_frame().T
        X = feature_extractor.transform(alert_df)

        logger.info("Features extracted")

        # Step 3: ML prediction
        model = request.app.state.model_trainer.model
        predictor = ModelPredictor(model)
        prediction = predictor.predict(X)

        logger.info(f"Prediction: {prediction['prediction']} (confidence: {prediction['confidence']:.2%})")

        # Step 4: SHAP explanation
        predicted_class_idx = ALERT_LABELS.index(prediction['prediction'])

        shap_explainer = SHAPExplainer(
            model,
            feature_extractor.feature_columns,
            feature_extractor.feature_metadata
        )

        xai_explanation = shap_explainer.explain_prediction(
            X,
            prediction['prediction'],
            predicted_class_idx
        )

        logger.info("SHAP explanation generated")

        # Step 5: Claude explanation
        try:
            claude = ClaudeExplainer()
            llm_explanation = claude.generate_explanation(
                prediction,
                xai_explanation,
                alert_data
            )
            logger.info("Claude explanation generated")

        except Exception as e:
            logger.warning(f"Claude API error: {e}. Using fallback.")
            llm_explanation = claude._generate_fallback_explanation(prediction, xai_explanation)

        # Combine all results
        result = {
            "success": True,
            "alert": {
                "alert_id": alert_data['alert_id'],
                "timestamp": alert_data['timestamp'],
                "source_ip": alert_data['source_ip'],
                "source_country": alert_data['source_country'],
                "destination_ip": alert_data['destination_ip'],
                "destination_port": alert_data['destination_port'],
                "protocol": alert_data['protocol'],
                "failed_login_attempts": alert_data['failed_login_attempts'],
                "process_executed": alert_data['process_executed'],
                "data_volume_mb": alert_data['data_volume_mb'],
                "true_label": alert_data['label']
            },
            "prediction": {
                "verdict": prediction['prediction'],
                "confidence": prediction['confidence'],
                "probabilities": prediction['probabilities']
            },
            "xai": {
                "method": xai_explanation['explanation_method'],
                "top_features": xai_explanation['top_contributing_features']
            },
            "explanation": {
                "text": llm_explanation['explanation_text'],
                "recommended_action": llm_explanation['recommended_action'],
                "llm_model": llm_explanation['model_metadata']['llm_model']
            }
        }

        logger.info(f"Analysis complete for alert {alert_id}")

        return result

    except ValueError as e:
        logger.error(f"Alert not found: {alert_id}")
        raise HTTPException(status_code=404, detail=f"Alert not found: {alert_id}")

    except Exception as e:
        logger.error(f"Error analyzing alert: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/metrics")
async def get_model_metrics(request: Request) -> Dict:
    """
    Get model performance metrics

    Returns:
        Dictionary with training metrics
    """
    if request.app.state.model_trainer is None:
        raise HTTPException(
            status_code=503,
            detail="ML model not loaded"
        )

    try:
        metrics = request.app.state.model_trainer.training_metrics

        # Format metrics for API response
        return {
            "success": True,
            "metrics": {
                "accuracy": metrics.get('accuracy', 0),
                "precision_weighted": metrics.get('precision_weighted', 0),
                "recall_weighted": metrics.get('recall_weighted', 0),
                "f1_weighted": metrics.get('f1_weighted', 0),
                "per_class": {
                    label: {
                        "precision": metrics.get(f'precision_{label}', 0),
                        "recall": metrics.get(f'recall_{label}', 0),
                        "f1": metrics.get(f'f1_{label}', 0)
                    }
                    for label in ALERT_LABELS
                }
            }
        }

    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/status")
async def get_status(request: Request) -> Dict:
    """
    Get system status

    Returns:
        System status information
    """
    return {
        "success": True,
        "status": "operational",
        "components": {
            "model_loaded": request.app.state.model_trainer is not None,
            "feature_extractor_loaded": request.app.state.feature_extractor is not None,
            "alerts_available": ALERTS_CSV_PATH.exists()
        }
    }
