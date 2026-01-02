"""
Train ML Model

Standalone script to train the Random Forest classifier.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ingestion.alert_loader import AlertLoader
from src.feature_engineering.feature_extractor import FeatureExtractor
from src.ml_engine.model_trainer import ModelTrainer
from config.settings import ALERTS_CSV_PATH
from config.logging_config import logger


def main():
    """Train the ML model"""
    logger.info("=" * 60)
    logger.info("TRAINING ML MODEL")
    logger.info("=" * 60)

    try:
        # Step 1: Load alerts
        logger.info("Step 1/4: Loading alerts...")
        if not ALERTS_CSV_PATH.exists():
            logger.error(f"Alerts file not found: {ALERTS_CSV_PATH}")
            logger.error("Please run 'python scripts/generate_data.py' first")
            sys.exit(1)

        df = AlertLoader.load_csv(ALERTS_CSV_PATH)
        logger.info(f"Loaded {len(df)} alerts")

        # Step 2: Feature engineering
        logger.info("\nStep 2/4: Engineering features...")
        extractor = FeatureExtractor()
        X, y = extractor.fit_transform(df)
        logger.info(f"Extracted {X.shape[1]} features from {X.shape[0]} alerts")

        # Save feature extractor
        extractor.save()
        logger.info("Feature extractor saved")

        # Step 3: Train model
        logger.info("\nStep 3/4: Training Random Forest model...")
        logger.info("This may take a few minutes...")

        trainer = ModelTrainer()
        model = trainer.train(X, y, hyperparameter_tuning=True)

        # Step 4: Save model
        logger.info("\nStep 4/4: Saving model...")
        trainer.save()

        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("TRAINING COMPLETE!")
        logger.info("=" * 60)
        logger.info(f"Model Accuracy: {trainer.training_metrics['accuracy']:.2%}")
        logger.info(f"Malicious Recall: {trainer.training_metrics['recall_malicious']:.2%}")
        logger.info(f"Benign Precision: {trainer.training_metrics['precision_benign']:.2%}")

        logger.info("\nTop 5 Most Important Features:")
        top_features = trainer.training_metrics['feature_importance'].head(5)
        for idx, row in top_features.iterrows():
            logger.info(f"  - {row['feature']}: {row['importance']:.4f}")

        logger.info("\n" + "=" * 60)
        logger.info("Next step: Run 'python scripts/run_dashboard.py' to start the dashboard")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error training model: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
