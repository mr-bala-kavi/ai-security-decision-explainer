"""
ML Model Training Pipeline

Trains Random Forest classifier for security alert classification.
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix
)
import pickle
from pathlib import Path
from loguru import logger
from typing import Tuple, Dict

from config.settings import (
    RANDOM_SEED, TEST_SIZE, MODEL_DIR, ALERT_LABELS,
    N_ESTIMATORS_OPTIONS, MAX_DEPTH_OPTIONS, MIN_SAMPLES_SPLIT_OPTIONS
)


class ModelTrainer:
    """
    Trains and evaluates Random Forest classifier
    """

    def __init__(self, random_seed: int = RANDOM_SEED):
        self.random_seed = random_seed
        self.model = None
        self.best_params = None
        self.training_metrics = {}

    def train(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        hyperparameter_tuning: bool = True
    ) -> RandomForestClassifier:
        """
        Train Random Forest classifier

        Args:
            X: Feature matrix
            y: Labels
            hyperparameter_tuning: Whether to perform hyperparameter tuning

        Returns:
            Trained RandomForestClassifier
        """
        logger.info(f"Training Random Forest with {len(X)} samples, {X.shape[1]} features")

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=TEST_SIZE, random_state=self.random_seed, stratify=y
        )

        logger.info(f"Train set: {len(X_train)}, Test set: {len(X_test)}")

        if hyperparameter_tuning:
            logger.info("Performing hyperparameter tuning...")
            self.model = self._hyperparameter_tuning(X_train, y_train)
        else:
            # Use default parameters
            logger.info("Training with default parameters...")
            self.model = RandomForestClassifier(
                n_estimators=200,
                max_depth=20,
                min_samples_split=5,
                class_weight='balanced',
                random_state=self.random_seed,
                n_jobs=-1
            )
            self.model.fit(X_train, y_train)

        # Evaluate on test set
        logger.info("Evaluating model on test set...")
        self.training_metrics = self._evaluate_model(X_test, y_test)

        # Log metrics
        self._log_metrics()

        return self.model

    def _hyperparameter_tuning(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series
    ) -> RandomForestClassifier:
        """
        Perform hyperparameter tuning using GridSearchCV

        Args:
            X_train: Training features
            y_train: Training labels

        Returns:
            Best RandomForestClassifier
        """
        param_grid = {
            'n_estimators': N_ESTIMATORS_OPTIONS,
            'max_depth': MAX_DEPTH_OPTIONS,
            'min_samples_split': MIN_SAMPLES_SPLIT_OPTIONS
        }

        # Base model
        base_model = RandomForestClassifier(
            class_weight='balanced',
            random_state=self.random_seed,
            n_jobs=-1
        )

        # GridSearchCV
        grid_search = GridSearchCV(
            base_model,
            param_grid,
            cv=5,
            scoring='f1_weighted',
            n_jobs=-1,
            verbose=1
        )

        grid_search.fit(X_train, y_train)

        self.best_params = grid_search.best_params_
        logger.info(f"Best parameters: {self.best_params}")

        return grid_search.best_estimator_

    def _evaluate_model(self, X_test: pd.DataFrame, y_test: pd.Series) -> Dict:
        """
        Evaluate model on test set

        Args:
            X_test: Test features
            y_test: Test labels

        Returns:
            Dictionary of metrics
        """
        # Predictions
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)

        # Calculate metrics
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision_weighted': precision_score(y_test, y_pred, average='weighted', zero_division=0),
            'recall_weighted': recall_score(y_test, y_pred, average='weighted', zero_division=0),
            'f1_weighted': f1_score(y_test, y_pred, average='weighted', zero_division=0),
        }

        # Per-class metrics
        precision_per_class = precision_score(y_test, y_pred, average=None, labels=ALERT_LABELS, zero_division=0)
        recall_per_class = recall_score(y_test, y_pred, average=None, labels=ALERT_LABELS, zero_division=0)
        f1_per_class = f1_score(y_test, y_pred, average=None, labels=ALERT_LABELS, zero_division=0)

        for i, label in enumerate(ALERT_LABELS):
            metrics[f'precision_{label}'] = precision_per_class[i]
            metrics[f'recall_{label}'] = recall_per_class[i]
            metrics[f'f1_{label}'] = f1_per_class[i]

        # Confusion matrix
        metrics['confusion_matrix'] = confusion_matrix(y_test, y_pred, labels=ALERT_LABELS)

        # Classification report
        metrics['classification_report'] = classification_report(
            y_test, y_pred, labels=ALERT_LABELS, target_names=ALERT_LABELS
        )

        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': X_test.columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)

        metrics['feature_importance'] = feature_importance

        return metrics

    def _log_metrics(self):
        """Log training metrics"""
        logger.info("=" * 60)
        logger.info("MODEL TRAINING METRICS")
        logger.info("=" * 60)
        logger.info(f"Accuracy: {self.training_metrics['accuracy']:.4f}")
        logger.info(f"Weighted Precision: {self.training_metrics['precision_weighted']:.4f}")
        logger.info(f"Weighted Recall: {self.training_metrics['recall_weighted']:.4f}")
        logger.info(f"Weighted F1-Score: {self.training_metrics['f1_weighted']:.4f}")
        logger.info("")

        logger.info("Per-Class Metrics:")
        for label in ALERT_LABELS:
            logger.info(f"  {label.upper()}:")
            logger.info(f"    Precision: {self.training_metrics[f'precision_{label}']:.4f}")
            logger.info(f"    Recall:    {self.training_metrics[f'recall_{label}']:.4f}")
            logger.info(f"    F1-Score:  {self.training_metrics[f'f1_{label}']:.4f}")
        logger.info("")

        logger.info("Confusion Matrix:")
        logger.info(f"{self.training_metrics['confusion_matrix']}")
        logger.info("")

        logger.info("Classification Report:")
        logger.info(f"\n{self.training_metrics['classification_report']}")
        logger.info("")

        logger.info("Top 10 Most Important Features:")
        top_features = self.training_metrics['feature_importance'].head(10)
        for idx, row in top_features.iterrows():
            logger.info(f"  {row['feature']}: {row['importance']:.4f}")
        logger.info("=" * 60)

    def save(self, directory: Path = None):
        """Save trained model to disk"""
        directory = directory or MODEL_DIR
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)

        model_path = directory / "random_forest_model.pkl"
        metrics_path = directory / "training_metrics.pkl"

        # Save model
        with open(model_path, 'wb') as f:
            pickle.dump(self.model, f)
        logger.info(f"Model saved to {model_path}")

        # Save metrics
        with open(metrics_path, 'wb') as f:
            pickle.dump({
                'metrics': self.training_metrics,
                'best_params': self.best_params
            }, f)
        logger.info(f"Metrics saved to {metrics_path}")

    @classmethod
    def load(cls, directory: Path = None) -> 'ModelTrainer':
        """Load trained model from disk"""
        directory = directory or MODEL_DIR
        directory = Path(directory)

        model_path = directory / "random_forest_model.pkl"
        metrics_path = directory / "training_metrics.pkl"

        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")

        trainer = cls()

        # Load model
        with open(model_path, 'rb') as f:
            trainer.model = pickle.load(f)
        logger.info(f"Model loaded from {model_path}")

        # Load metrics if available
        if metrics_path.exists():
            with open(metrics_path, 'rb') as f:
                data = pickle.load(f)
                trainer.training_metrics = data['metrics']
                trainer.best_params = data.get('best_params')

        return trainer


if __name__ == "__main__":
    # Test training pipeline
    from src.ingestion.alert_loader import AlertLoader
    from src.feature_engineering.feature_extractor import FeatureExtractor
    from config.settings import ALERTS_CSV_PATH

    # Load data
    logger.info("Loading alerts...")
    df = AlertLoader.load_csv(ALERTS_CSV_PATH)

    # Extract features
    logger.info("Extracting features...")
    extractor = FeatureExtractor()
    X, y = extractor.fit_transform(df)
    extractor.save()

    # Train model
    logger.info("Training model...")
    trainer = ModelTrainer()
    model = trainer.train(X, y, hyperparameter_tuning=True)
    trainer.save()

    logger.info("Training complete!")
