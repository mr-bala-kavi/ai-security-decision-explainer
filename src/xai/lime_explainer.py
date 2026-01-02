"""
LIME Explainer (Optional)

Alternative explainability method for validation and comparison.
Currently optional - SHAP is the primary explanation method.
"""
from lime.lime_tabular import LimeTabularExplainer
import pandas as pd
import numpy as np
from typing import Dict
from loguru import logger


class LIMEExplainer:
    """
    LIME-based explainer for model predictions
    """

    def __init__(self, training_data: pd.DataFrame, feature_names: list, class_names: list):
        """
        Initialize LIME explainer

        Args:
            training_data: Training data for LIME reference
            feature_names: List of feature names
            class_names: List of class labels
        """
        self.feature_names = feature_names
        self.class_names = class_names

        self.explainer = LimeTabularExplainer(
            training_data.values,
            feature_names=feature_names,
            class_names=class_names,
            mode='classification',
            verbose=False
        )

        logger.info("LIME explainer initialized")

    def explain_prediction(self, model, X_instance: pd.DataFrame, num_features: int = 10) -> Dict:
        """
        Generate LIME explanation for a single prediction

        Args:
            model: Trained model
            X_instance: Single instance to explain
            num_features: Number of top features to show

        Returns:
            Dictionary with LIME explanation
        """
        # Convert to array
        instance = X_instance.values[0] if isinstance(X_instance, pd.DataFrame) else X_instance

        # Generate explanation
        explanation = self.explainer.explain_instance(
            instance,
            model.predict_proba,
            num_features=num_features
        )

        # Extract feature importance
        feature_importance = explanation.as_list()

        return {
            'explanation_method': 'LIME',
            'feature_importance': feature_importance,
            'local_prediction': explanation.local_pred
        }


# Note: LIME is optional and provided for comparison with SHAP
# The primary explainability method is SHAP (shap_explainer.py)
