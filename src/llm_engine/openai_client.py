"""
OpenAI API Client for Generating Human-Readable Explanations

Translates technical XAI output into SOC analyst-friendly explanations.
"""
import os
from openai import OpenAI
from typing import Dict
from loguru import logger

from config.settings import (
    OPENAI_API_KEY, OPENAI_MODEL,
    LLM_MAX_TOKENS, LLM_TEMPERATURE
)


class LLMExplainer:
    """
    Generates human-readable explanations using OpenAI API
    """

    def __init__(self, api_key: str = None, model: str = None):
        """
        Initialize OpenAI client

        Args:
            api_key: OpenAI API key (default: from environment)
            model: OpenAI model to use (default: from settings)
        """
        self.api_key = api_key or OPENAI_API_KEY
        self.model = model or OPENAI_MODEL

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set. Please set it in .env file")

        self.client = OpenAI(api_key=self.api_key)
        logger.info(f"OpenAI client initialized with model: {self.model}")

    def generate_explanation(
        self,
        prediction_data: Dict,
        xai_data: Dict,
        alert_data: Dict
    ) -> Dict:
        """
        Generate human-readable explanation for a security alert classification

        Args:
            prediction_data: Prediction results from ML model
            xai_data: SHAP explanation data
            alert_data: Original alert data

        Returns:
            Dictionary with explanation text and metadata
        """
        from src.llm_engine.prompt_builder import PromptBuilder

        # Build prompt
        prompt = PromptBuilder.build_explanation_prompt(
            prediction_data,
            xai_data,
            alert_data
        )

        logger.debug(f"Sending prompt to OpenAI API (model: {self.model})")

        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert SOC analyst explaining security alerts."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=LLM_MAX_TOKENS,
                temperature=LLM_TEMPERATURE
            )

            # Extract response
            explanation_text = response.choices[0].message.content

            # Determine recommended action from prediction
            recommended_action = self._determine_action(prediction_data)

            result = {
                'explanation_text': explanation_text,
                'recommended_action': recommended_action,
                'model_metadata': {
                    'llm_model': self.model,
                    'tokens_used': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                }
            }

            logger.info(f"Generated explanation ({response.usage.completion_tokens} tokens)")

            return result

        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            # Return fallback explanation
            return self._generate_fallback_explanation(prediction_data, xai_data)

    def _determine_action(self, prediction_data: Dict) -> str:
        """
        Determine recommended action based on prediction

        Args:
            prediction_data: Prediction results

        Returns:
            Recommended action string
        """
        prediction = prediction_data['prediction']
        confidence = prediction_data['confidence']

        if prediction == 'malicious':
            if confidence >= 0.8:
                return 'investigate_immediately'
            else:
                return 'investigate_soon'
        elif prediction == 'suspicious':
            return 'monitor_closely'
        else:  # benign
            if confidence >= 0.8:
                return 'mark_false_positive'
            else:
                return 'review_later'

    def _generate_fallback_explanation(self, prediction_data: Dict, xai_data: Dict) -> Dict:
        """
        Generate fallback explanation if API call fails

        Args:
            prediction_data: Prediction results
            xai_data: SHAP explanation data

        Returns:
            Fallback explanation dictionary
        """
        prediction = prediction_data['prediction']
        confidence = prediction_data['confidence']
        top_features = xai_data['top_contributing_features'][:3]

        # Simple template-based explanation
        feature_text = ", ".join([f['human_readable_name'] for f in top_features])

        fallback_text = (
            f"This alert is classified as {prediction.upper()} with {confidence:.0%} confidence. "
            f"Key factors: {feature_text}. "
            f"{'Immediate investigation recommended.' if prediction == 'malicious' else 'Monitor for suspicious activity.'}"
        )

        return {
            'explanation_text': fallback_text,
            'recommended_action': self._determine_action(prediction_data),
            'model_metadata': {
                'llm_model': 'fallback_template',
                'tokens_used': 0,
                'total_tokens': 0
            }
        }


# Backward compatibility alias
ClaudeExplainer = LLMExplainer


if __name__ == "__main__":
    # Test OpenAI client
    from src.ml_engine.model_trainer import ModelTrainer
    from src.ml_engine.model_predictor import ModelPredictor
    from src.xai.shap_explainer import SHAPExplainer
    from src.feature_engineering.feature_extractor import FeatureExtractor
    from src.ingestion.alert_loader import AlertLoader
    from config.settings import ALERTS_CSV_PATH, ALERT_LABELS

    # Load components
    trainer = ModelTrainer.load()
    extractor = FeatureExtractor.load()

    # Load test alert
    df = AlertLoader.load_csv(ALERTS_CSV_PATH)
    alert = df.iloc[50:51]
    alert_data = alert.iloc[0].to_dict()

    # Extract features
    X = extractor.transform(alert)

    # Predict
    predictor = ModelPredictor(trainer.model)
    prediction = predictor.predict(X)

    # Generate SHAP explanation
    predicted_class_idx = ALERT_LABELS.index(prediction['prediction'])
    explainer = SHAPExplainer(
        trainer.model,
        extractor.feature_columns,
        extractor.feature_metadata
    )
    xai_explanation = explainer.explain_prediction(X, prediction['prediction'], predicted_class_idx)

    # Generate OpenAI explanation
    logger.info("Generating human-readable explanation with OpenAI...")
    llm = LLMExplainer()
    llm_explanation = llm.generate_explanation(prediction, xai_explanation, alert_data)

    print("\n" + "=" * 60)
    print("OPENAI EXPLANATION:")
    print("=" * 60)
    print(llm_explanation['explanation_text'])
    print(f"\nRecommended Action: {llm_explanation['recommended_action']}")
    print(f"Tokens Used: {llm_explanation['model_metadata']['tokens_used']}")
