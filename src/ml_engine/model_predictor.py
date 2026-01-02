"""
ML Model Prediction

Makes predictions on new security alerts.
"""
import pandas as pd
import numpy as np
from typing import Dict, List
from loguru import logger

from config.settings import ALERT_LABELS


class ModelPredictor:
    """
    Makes predictions using trained Random Forest model
    """

    def __init__(self, model):
        self.model = model

    def predict(self, X: pd.DataFrame) -> Dict:
        """
        Predict on single or multiple alerts

        Args:
            X: Feature matrix (single row or multiple rows)

        Returns:
            Dictionary with predictions and probabilities
        """
        # Ensure X is a DataFrame
        if isinstance(X, pd.Series):
            X = X.to_frame().T

        # Get predictions
        predictions = self.model.predict(X)
        probabilities = self.model.predict_proba(X)

        results = []
        for i in range(len(X)):
            pred = predictions[i]
            proba = probabilities[i]

            # Create probability dictionary
            proba_dict = {
                label: float(prob)
                for label, prob in zip(ALERT_LABELS, proba)
            }

            # Get confidence (max probability)
            confidence = float(max(proba))

            result = {
                'prediction': pred,
                'confidence': confidence,
                'probabilities': proba_dict
            }

            results.append(result)

        # Return single result if single input, otherwise list
        if len(results) == 1:
            return results[0]
        return results

    def predict_single(self, X_single: pd.Series) -> Dict:
        """
        Predict on a single alert

        Args:
            X_single: Feature Series for one alert

        Returns:
            Dictionary with prediction, confidence, and probabilities
        """
        return self.predict(X_single.to_frame().T)


if __name__ == "__main__":
    # Test predictor
    from src.ml_engine.model_trainer import ModelTrainer
    from src.feature_engineering.feature_extractor import FeatureExtractor
    from src.ingestion.alert_loader import AlertLoader
    from config.settings import ALERTS_CSV_PATH

    # Load model and extractor
    trainer = ModelTrainer.load()
    extractor = FeatureExtractor.load()

    # Load test data
    df = AlertLoader.load_csv(ALERTS_CSV_PATH)
    X_test = extractor.transform(df.head(5))

    # Make predictions
    predictor = ModelPredictor(trainer.model)
    results = predictor.predict(X_test)

    print(f"\nPredictions for {len(X_test)} alerts:")
    for i, result in enumerate(results):
        print(f"\nAlert {i + 1}:")
        print(f"  Prediction: {result['prediction']}")
        print(f"  Confidence: {result['confidence']:.2%}")
        print(f"  Probabilities: {result['probabilities']}")
