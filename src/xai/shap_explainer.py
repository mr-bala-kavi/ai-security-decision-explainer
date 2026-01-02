"""
SHAP Explainer for Model Interpretability

Generates SHAP explanations for Random Forest predictions.
"""
import pandas as pd
import numpy as np
import shap
from typing import Dict, List
from loguru import logger

from config.settings import TOP_N_FEATURES


class SHAPExplainer:
    """
    Generates SHAP-based explanations for model predictions
    """

    def __init__(self, model, feature_names: List[str], feature_metadata: Dict = None):
        """
        Initialize SHAP explainer

        Args:
            model: Trained RandomForestClassifier
            feature_names: List of feature names
            feature_metadata: Optional mapping of technical to human-readable names
        """
        self.model = model
        self.feature_names = feature_names
        self.feature_metadata = feature_metadata or {}

        # Create TreeExplainer for Random Forest
        logger.info("Initializing SHAP TreeExplainer...")
        self.explainer = shap.TreeExplainer(self.model)
        logger.info("SHAP explainer ready")

    def explain_prediction(
        self,
        X_instance: pd.DataFrame,
        predicted_class: str,
        predicted_class_idx: int
    ) -> Dict:
        """
        Generate SHAP explanation for a single prediction

        Args:
            X_instance: Feature values for single alert (DataFrame with one row)
            predicted_class: Predicted class label
            predicted_class_idx: Index of predicted class

        Returns:
            Dictionary with explanation data
        """
        # Ensure X_instance is DataFrame
        if isinstance(X_instance, pd.Series):
            X_instance = X_instance.to_frame().T

        # Get SHAP values
        shap_values = self.explainer.shap_values(X_instance)

        # For multi-class, shap_values is a list of arrays (one per class)
        # Get SHAP values for the predicted class
        if isinstance(shap_values, list):
            shap_values_class = shap_values[predicted_class_idx][0]
        else:
            shap_values_class = shap_values[0]

        # Get base value (expected value for predicted class)
        if isinstance(self.explainer.expected_value, (list, np.ndarray)):
            base_value = self.explainer.expected_value[predicted_class_idx]
        else:
            base_value = self.explainer.expected_value

        # Create feature importance ranking
        feature_importance = []
        for i, feature_name in enumerate(self.feature_names):
            impact_score = float(shap_values_class[i])
            feature_value = float(X_instance.iloc[0, i])

            # Get human-readable name
            if self.feature_metadata and feature_name in self.feature_metadata:
                human_readable = self.feature_metadata[feature_name]['human_readable_name']
            else:
                human_readable = feature_name.replace('_', ' ').title()

            feature_importance.append({
                'feature': feature_name,
                'human_readable_name': human_readable,
                'impact_score': impact_score,
                'direction': 'increases_risk' if impact_score > 0 else 'decreases_risk',
                'feature_value': feature_value
            })

        # Sort by absolute impact
        feature_importance.sort(key=lambda x: abs(x['impact_score']), reverse=True)

        # Calculate contribution percentages
        total_impact = sum(abs(f['impact_score']) for f in feature_importance)
        if total_impact > 0:
            for f in feature_importance:
                f['contribution_percentage'] = (abs(f['impact_score']) / total_impact) * 100
        else:
            for f in feature_importance:
                f['contribution_percentage'] = 0.0

        # Get top N features
        top_features = feature_importance[:TOP_N_FEATURES]

        explanation = {
            'explanation_method': 'SHAP',
            'predicted_class': predicted_class,
            'base_risk': float(base_value),
            'final_risk': float(base_value + shap_values_class.sum()),
            'top_contributing_features': top_features,
            'all_features': feature_importance
        }

        return explanation

    def explain_multiple(
        self,
        X: pd.DataFrame,
        predictions: List[str],
        predicted_indices: List[int]
    ) -> List[Dict]:
        """
        Generate SHAP explanations for multiple predictions

        Args:
            X: Feature matrix (multiple rows)
            predictions: List of predicted class labels
            predicted_indices: List of predicted class indices

        Returns:
            List of explanation dictionaries
        """
        explanations = []

        for i in range(len(X)):
            X_single = X.iloc[i:i+1]
            explanation = self.explain_prediction(
                X_single,
                predictions[i],
                predicted_indices[i]
            )
            explanations.append(explanation)

        return explanations

    def get_feature_summary(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Get overall feature importance across multiple predictions

        Args:
            X: Feature matrix

        Returns:
            DataFrame with mean absolute SHAP values per feature
        """
        shap_values = self.explainer.shap_values(X)

        # Average absolute SHAP values across all samples and classes
        if isinstance(shap_values, list):
            # Multi-class: average across classes
            mean_abs_shap = np.mean([np.abs(sv).mean(axis=0) for sv in shap_values], axis=0)
        else:
            mean_abs_shap = np.abs(shap_values).mean(axis=0)

        summary_df = pd.DataFrame({
            'feature': self.feature_names,
            'mean_abs_shap_value': mean_abs_shap
        }).sort_values('mean_abs_shap_value', ascending=False)

        return summary_df


if __name__ == "__main__":
    # Test SHAP explainer
    from src.ml_engine.model_trainer import ModelTrainer
    from src.ml_engine.model_predictor import ModelPredictor
    from src.feature_engineering.feature_extractor import FeatureExtractor
    from src.ingestion.alert_loader import AlertLoader
    from config.settings import ALERTS_CSV_PATH, ALERT_LABELS

    # Load model and extractor
    logger.info("Loading model and feature extractor...")
    trainer = ModelTrainer.load()
    extractor = FeatureExtractor.load()

    # Load test alert
    df = AlertLoader.load_csv(ALERTS_CSV_PATH)
    alert = df.iloc[100:101]  # Get one alert

    logger.info(f"Analyzing alert: {alert['alert_id'].values[0]}")
    logger.info(f"True label: {alert['label'].values[0]}")

    # Extract features
    X = extractor.transform(alert)

    # Make prediction
    predictor = ModelPredictor(trainer.model)
    prediction = predictor.predict(X)

    logger.info(f"Predicted: {prediction['prediction']} (confidence: {prediction['confidence']:.2%})")

    # Generate SHAP explanation
    predicted_class_idx = ALERT_LABELS.index(prediction['prediction'])

    explainer = SHAPExplainer(
        trainer.model,
        extractor.feature_columns,
        extractor.feature_metadata
    )

    explanation = explainer.explain_prediction(X, prediction['prediction'], predicted_class_idx)

    logger.info("\nTop Contributing Features:")
    for i, feature in enumerate(explanation['top_contributing_features'][:5], 1):
        logger.info(f"{i}. {feature['human_readable_name']}")
        logger.info(f"   Impact: {feature['impact_score']:+.4f} ({feature['direction']})")
        logger.info(f"   Value: {feature['feature_value']:.4f}")
        logger.info(f"   Contribution: {feature['contribution_percentage']:.1f}%")
