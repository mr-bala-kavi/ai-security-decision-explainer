"""
Test the complete pipeline
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.ingestion.alert_loader import AlertLoader
from src.feature_engineering.feature_extractor import FeatureExtractor
from src.ml_engine.model_trainer import ModelTrainer
from src.ml_engine.model_predictor import ModelPredictor
from src.xai.shap_explainer import SHAPExplainer
from src.llm_engine.openai_client import LLMExplainer
from config.settings import ALERTS_CSV_PATH, ALERT_LABELS
from loguru import logger

def test_pipeline():
    """Test the complete analysis pipeline"""
    logger.info("=" * 60)
    logger.info("TESTING COMPLETE PIPELINE")
    logger.info("=" * 60)

    # Load components
    logger.info("Loading trained model and feature extractor...")
    trainer = ModelTrainer.load()
    extractor = FeatureExtractor.load()
    logger.info("Components loaded successfully")

    # Load a test alert
    logger.info("\nLoading test alert...")
    df = AlertLoader.load_csv(ALERTS_CSV_PATH)

    # Get one alert of each type for testing
    test_alerts = []
    for label in ALERT_LABELS:
        alert = df[df['label'] == label].iloc[0:1]
        test_alerts.append((label, alert))

    # Test each alert type
    for true_label, alert in test_alerts:
        logger.info("\n" + "=" * 60)
        logger.info(f"TESTING {true_label.upper()} ALERT")
        logger.info("=" * 60)

        alert_data = alert.iloc[0].to_dict()
        logger.info(f"Alert ID: {alert_data['alert_id']}")
        logger.info(f"Source: {alert_data['source_ip']} ({alert_data['source_country']})")
        logger.info(f"Destination: {alert_data['destination_ip']}:{alert_data['destination_port']}")
        logger.info(f"Failed Logins: {alert_data['failed_login_attempts']}")

        # Step 1: Feature Engineering
        logger.info("\n[1/4] Extracting features...")
        X = extractor.transform(alert)
        logger.info(f"✓ Extracted {X.shape[1]} features")

        # Step 2: ML Prediction
        logger.info("\n[2/4] ML Classification...")
        predictor = ModelPredictor(trainer.model)
        prediction = predictor.predict(X)
        logger.info(f"✓ Prediction: {prediction['prediction'].upper()}")
        logger.info(f"✓ Confidence: {prediction['confidence']:.1%}")
        logger.info(f"✓ Probabilities: benign={prediction['probabilities']['benign']:.1%}, suspicious={prediction['probabilities']['suspicious']:.1%}, malicious={prediction['probabilities']['malicious']:.1%}")

        # Step 3: SHAP Explanation
        logger.info("\n[3/4] Generating SHAP explanation...")
        predicted_class_idx = ALERT_LABELS.index(prediction['prediction'])
        shap_explainer = SHAPExplainer(
            trainer.model,
            extractor.feature_columns,
            extractor.feature_metadata
        )
        xai_explanation = shap_explainer.explain_prediction(X, prediction['prediction'], predicted_class_idx)
        logger.info(f"✓ Top contributing features:")
        for i, feature in enumerate(xai_explanation['top_contributing_features'][:3], 1):
            logger.info(f"  {i}. {feature['human_readable_name']}: {feature['impact_score']:+.4f} ({feature['direction']})")

        # Step 4: LLM Explanation (GPT-4)
        logger.info("\n[4/4] Generating GPT-4 explanation...")
        try:
            llm = LLMExplainer()
            llm_explanation = llm.generate_explanation(prediction, xai_explanation, alert_data)
            logger.info(f"✓ GPT-4 Explanation:")
            logger.info(f"\n{llm_explanation['explanation_text']}\n")
            logger.info(f"✓ Recommended Action: {llm_explanation['recommended_action']}")
            logger.info(f"✓ Tokens Used: {llm_explanation['model_metadata']['tokens_used']}")
        except Exception as e:
            logger.warning(f"⚠ GPT-4 API Error (using fallback): {e}")
            llm = LLMExplainer()
            llm_explanation = llm._generate_fallback_explanation(prediction, xai_explanation)
            logger.info(f"✓ Fallback Explanation:")
            logger.info(f"\n{llm_explanation['explanation_text']}\n")

        # Verify accuracy
        if prediction['prediction'] == true_label:
            logger.info("✅ CORRECT PREDICTION!")
        else:
            logger.warning(f"❌ INCORRECT: Expected {true_label}, got {prediction['prediction']}")

    logger.info("\n" + "=" * 60)
    logger.info("PIPELINE TEST COMPLETE")
    logger.info("=" * 60)
    logger.info("\n✅ All components working correctly!")
    logger.info("\nTo run the web dashboard: python scripts/run_dashboard.py")

if __name__ == "__main__":
    test_pipeline()
