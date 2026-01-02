"""
ML Model Evaluation

Evaluates model performance and generates metrics.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix, roc_auc_score, roc_curve
)
from pathlib import Path
from loguru import logger
from typing import Dict

from config.settings import ALERT_LABELS, MODEL_DIR


class ModelEvaluator:
    """
    Evaluates trained model performance
    """

    @staticmethod
    def evaluate(model, X_test: pd.DataFrame, y_test: pd.Series) -> Dict:
        """
        Comprehensive model evaluation

        Args:
            model: Trained classifier
            X_test: Test features
            y_test: Test labels

        Returns:
            Dictionary of evaluation metrics
        """
        logger.info("Evaluating model performance...")

        # Predictions
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)

        # Calculate metrics
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision_weighted': precision_score(y_test, y_pred, average='weighted', zero_division=0),
            'recall_weighted': recall_score(y_test, y_pred, average='weighted', zero_division=0),
            'f1_weighted': f1_score(y_test, y_pred, average='weighted', zero_division=0)
        }

        # Per-class metrics
        for i, label in enumerate(ALERT_LABELS):
            precision = precision_score(y_test, y_pred, labels=[label], average='binary', zero_division=0)
            recall = recall_score(y_test, y_pred, labels=[label], average='binary', zero_division=0)
            f1 = f1_score(y_test, y_pred, labels=[label], average='binary', zero_division=0)

            metrics[f'precision_{label}'] = precision
            metrics[f'recall_{label}'] = recall
            metrics[f'f1_{label}'] = f1

        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred, labels=ALERT_LABELS)
        metrics['confusion_matrix'] = cm

        # Classification report
        report = classification_report(y_test, y_pred, labels=ALERT_LABELS, target_names=ALERT_LABELS)
        metrics['classification_report'] = report

        logger.info(f"Evaluation complete. Accuracy: {metrics['accuracy']:.4f}")

        return metrics

    @staticmethod
    def plot_confusion_matrix(
        confusion_matrix: np.ndarray,
        save_path: Path = None
    ):
        """
        Plot confusion matrix heatmap

        Args:
            confusion_matrix: Confusion matrix array
            save_path: Optional path to save figure
        """
        plt.figure(figsize=(8, 6))
        sns.heatmap(
            confusion_matrix,
            annot=True,
            fmt='d',
            cmap='Blues',
            xticklabels=ALERT_LABELS,
            yticklabels=ALERT_LABELS
        )
        plt.title('Confusion Matrix')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path)
            logger.info(f"Confusion matrix saved to {save_path}")

        plt.close()

    @staticmethod
    def plot_feature_importance(
        feature_importance: pd.DataFrame,
        top_n: int = 15,
        save_path: Path = None
    ):
        """
        Plot feature importance bar chart

        Args:
            feature_importance: DataFrame with 'feature' and 'importance' columns
            top_n: Number of top features to plot
            save_path: Optional path to save figure
        """
        top_features = feature_importance.head(top_n)

        plt.figure(figsize=(10, 8))
        plt.barh(range(len(top_features)), top_features['importance'])
        plt.yticks(range(len(top_features)), top_features['feature'])
        plt.xlabel('Importance')
        plt.title(f'Top {top_n} Feature Importance')
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path)
            logger.info(f"Feature importance plot saved to {save_path}")

        plt.close()


if __name__ == "__main__":
    # Test evaluator
    from src.ml_engine.model_trainer import ModelTrainer
    from src.feature_engineering.feature_extractor import FeatureExtractor
    from src.ingestion.alert_loader import AlertLoader
    from config.settings import ALERTS_CSV_PATH
    from sklearn.model_split import train_test_split

    # Load data
    df = AlertLoader.load_csv(ALERTS_CSV_PATH)

    # Extract features
    extractor = FeatureExtractor.load()
    X, y = extractor.transform(df), df['label']

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Load model
    trainer = ModelTrainer.load()

    # Evaluate
    evaluator = ModelEvaluator()
    metrics = evaluator.evaluate(trainer.model, X_test, y_test)

    print("\nEvaluation Metrics:")
    print(f"Accuracy: {metrics['accuracy']:.4f}")
    print(f"\nClassification Report:\n{metrics['classification_report']}")

    # Plot confusion matrix
    evaluator.plot_confusion_matrix(
        metrics['confusion_matrix'],
        save_path=MODEL_DIR / "confusion_matrix.png"
    )
