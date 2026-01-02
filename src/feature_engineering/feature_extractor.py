"""
Feature Engineering for Security Alerts

Transforms raw alerts into ML-ready features while preserving security context.
"""
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.preprocessing import StandardScaler, MinMaxScaler, OneHotEncoder
from category_encoders import TargetEncoder
from typing import Tuple, Dict
import pickle
from pathlib import Path
from loguru import logger

from config.settings import FEATURE_NAME_MAPPING, PROCESSED_DATA_DIR


class FeatureExtractor:
    """
    Extracts and engineers features from raw security alerts
    """

    def __init__(self):
        self.scaler = StandardScaler()
        self.minmax_scaler = MinMaxScaler()
        self.target_encoder = TargetEncoder()
        self.onehot_encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')

        self.is_fitted = False
        self.feature_columns = []
        self.feature_metadata = {}

    def fit_transform(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Fit transformers and transform training data

        Args:
            df: Raw alert DataFrame with 'label' column

        Returns:
            Tuple of (features DataFrame, labels Series)
        """
        logger.info("Fitting and transforming features...")

        # Separate features and labels
        labels = df['label'].copy()
        df_features = df.drop(columns=['label', 'alert_id'])

        # Extract temporal features
        df_features = self._extract_temporal_features(df_features)

        # Create risk scoring features
        df_features = self._create_risk_features(df_features)

        # Drop non-feature columns
        df_features = df_features.drop(columns=['timestamp', 'source_ip', 'destination_ip',
                                                  'process_executed', 'encryption_protocol'], errors='ignore')

        # Encode categorical features
        df_features = self._encode_categorical(df_features, labels, fit=True)

        # Normalize numerical features
        df_features = self._normalize_features(df_features, fit=True)

        self.feature_columns = list(df_features.columns)
        self.is_fitted = True

        # Create feature metadata
        self._create_feature_metadata()

        logger.info(f"Feature extraction complete: {len(self.feature_columns)} features")

        return df_features, labels

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform new data using fitted transformers

        Args:
            df: Raw alert DataFrame (without labels)

        Returns:
            Transformed features DataFrame
        """
        if not self.is_fitted:
            raise ValueError("FeatureExtractor must be fitted first")

        logger.info("Transforming features...")

        # Remove label and alert_id if present
        df_features = df.drop(columns=['label', 'alert_id'], errors='ignore')

        # Extract temporal features
        df_features = self._extract_temporal_features(df_features)

        # Create risk scoring features
        df_features = self._create_risk_features(df_features)

        # Drop non-feature columns
        df_features = df_features.drop(columns=['timestamp', 'source_ip', 'destination_ip',
                                                  'process_executed', 'encryption_protocol'], errors='ignore')

        # Encode categorical features
        df_features = self._encode_categorical(df_features, None, fit=False)

        # Normalize numerical features
        df_features = self._normalize_features(df_features, fit=False)

        # Ensure same columns as training
        for col in self.feature_columns:
            if col not in df_features.columns:
                df_features[col] = 0

        df_features = df_features[self.feature_columns]

        return df_features

    def _extract_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract temporal features from timestamp"""
        df = df.copy()

        # Parse timestamp
        df['timestamp_dt'] = pd.to_datetime(df['timestamp'])

        # Extract hour of day (0-23)
        df['hour_of_day'] = df['timestamp_dt'].dt.hour

        # Extract day of week (0=Monday, 6=Sunday)
        df['day_of_week'] = df['timestamp_dt'].dt.dayofweek

        # Is weekend
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)

        # Is night shift (0-6 AM)
        df['is_night_shift'] = ((df['hour_of_day'] >= 0) & (df['hour_of_day'] < 6)).astype(int)

        df = df.drop(columns=['timestamp_dt'])

        return df

    def _create_risk_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create derived risk scoring features"""
        df = df.copy()

        # Login risk score: failed attempts * successful after failures
        df['login_risk_score'] = df['failed_login_attempts'] * df['successful_login_after_failures'].astype(int)

        # Privilege risk: admin escalation during off-hours
        df['privilege_risk'] = (df['admin_privilege_escalation'].astype(int) *
                                df['off_hours_activity'].astype(int))

        # Total threat indicators count
        threat_indicators = [
            'threat_intel_match', 'geo_impossible_travel',
            'user_agent_anomaly', 'lateral_movement_detected'
        ]
        df['threat_indicator_count'] = df[threat_indicators].astype(int).sum(axis=1)

        # Port risk: uncommon ports
        common_ports = [80, 443, 22, 3389, 445]
        df['uncommon_port'] = (~df['destination_port'].isin(common_ports)).astype(int)

        return df

    def _encode_categorical(self, df: pd.DataFrame, labels: pd.Series = None, fit: bool = False) -> pd.DataFrame:
        """Encode categorical features"""
        df = df.copy()

        # High cardinality: Use simple mean encoding for source_country
        high_cardinality = ['source_country']

        if fit and labels is not None:
            for col in high_cardinality:
                if col in df.columns:
                    # Convert labels to numeric for mean encoding
                    label_map = {'benign': 0, 'suspicious': 1, 'malicious': 2}
                    numeric_labels = labels.map(label_map)

                    # Calculate mean encoding manually
                    temp_df = pd.DataFrame({col: df[col], 'target': numeric_labels})
                    means = temp_df.groupby(col)['target'].transform('mean')
                    # Store mapping for later use
                    if not hasattr(self, 'country_encoding'):
                        self.country_encoding = temp_df.groupby(col)['target'].mean().to_dict()
                    df[f'{col}_encoded'] = means
                    df = df.drop(columns=[col])
        else:
            for col in high_cardinality:
                if col in df.columns:
                    # Use stored mapping
                    if hasattr(self, 'country_encoding'):
                        df[f'{col}_encoded'] = df[col].map(self.country_encoding).fillna(0.5)
                    else:
                        df[f'{col}_encoded'] = 0.5  # Default value
                    df = df.drop(columns=[col])

        # Low cardinality: One-hot encoding
        low_cardinality = ['protocol']

        if fit:
            if any(col in df.columns for col in low_cardinality):
                encoded_df = pd.DataFrame(
                    self.onehot_encoder.fit_transform(df[low_cardinality]),
                    index=df.index,
                    columns=self.onehot_encoder.get_feature_names_out(low_cardinality)
                )
                df = pd.concat([df.drop(columns=low_cardinality), encoded_df], axis=1)
        else:
            if any(col in df.columns for col in low_cardinality):
                encoded_df = pd.DataFrame(
                    self.onehot_encoder.transform(df[low_cardinality]),
                    index=df.index,
                    columns=self.onehot_encoder.get_feature_names_out(low_cardinality)
                )
                df = pd.concat([df.drop(columns=low_cardinality), encoded_df], axis=1)

        # Boolean features: Convert to int (0/1)
        boolean_features = [
            'successful_login_after_failures', 'process_hash_known',
            'admin_privilege_escalation', 'off_hours_activity',
            'geo_impossible_travel', 'user_agent_anomaly',
            'threat_intel_match', 'lateral_movement_detected'
        ]
        for col in boolean_features:
            if col in df.columns:
                df[col] = df[col].astype(int)

        return df

    def _normalize_features(self, df: pd.DataFrame, fit: bool = False) -> pd.DataFrame:
        """Normalize numerical features"""
        df = df.copy()

        # Features to standardize (z-score normalization)
        standard_features = [
            'failed_login_attempts', 'data_volume_mb',
            'connection_duration_seconds', 'unique_destinations_count'
        ]
        standard_features = [f for f in standard_features if f in df.columns]

        if standard_features:
            if fit:
                df[standard_features] = self.scaler.fit_transform(df[standard_features])
            else:
                df[standard_features] = self.scaler.transform(df[standard_features])

        # Features to min-max normalize (0-1)
        minmax_features = ['hour_of_day', 'day_of_week']
        minmax_features = [f for f in minmax_features if f in df.columns]

        if minmax_features:
            if fit:
                df[minmax_features] = self.minmax_scaler.fit_transform(df[minmax_features])
            else:
                df[minmax_features] = self.minmax_scaler.transform(df[minmax_features])

        return df

    def _create_feature_metadata(self):
        """Create metadata mapping technical features to human-readable names"""
        self.feature_metadata = {}

        for feature in self.feature_columns:
            # Use predefined mapping if available
            if feature in FEATURE_NAME_MAPPING:
                human_readable = FEATURE_NAME_MAPPING[feature]
            else:
                # Convert snake_case to Title Case
                human_readable = feature.replace('_', ' ').title()

            self.feature_metadata[feature] = {
                'human_readable_name': human_readable,
                'technical_name': feature
            }

    def get_feature_name(self, technical_name: str) -> str:
        """Get human-readable name for a feature"""
        if technical_name in self.feature_metadata:
            return self.feature_metadata[technical_name]['human_readable_name']
        return technical_name.replace('_', ' ').title()

    def save(self, directory: Path = None):
        """Save feature extractor to disk"""
        directory = directory or PROCESSED_DATA_DIR
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)

        save_path = directory / "feature_extractor.pkl"

        with open(save_path, 'wb') as f:
            pickle.dump({
                'scaler': self.scaler,
                'minmax_scaler': self.minmax_scaler,
                'target_encoder': self.target_encoder,
                'onehot_encoder': self.onehot_encoder,
                'feature_columns': self.feature_columns,
                'feature_metadata': self.feature_metadata,
                'is_fitted': self.is_fitted,
                'country_encoding': getattr(self, 'country_encoding', {})
            }, f)

        logger.info(f"FeatureExtractor saved to {save_path}")

    @classmethod
    def load(cls, directory: Path = None) -> 'FeatureExtractor':
        """Load feature extractor from disk"""
        directory = directory or PROCESSED_DATA_DIR
        directory = Path(directory)

        load_path = directory / "feature_extractor.pkl"

        if not load_path.exists():
            raise FileNotFoundError(f"Feature extractor not found: {load_path}")

        with open(load_path, 'rb') as f:
            data = pickle.load(f)

        extractor = cls()
        extractor.scaler = data['scaler']
        extractor.minmax_scaler = data['minmax_scaler']
        extractor.target_encoder = data['target_encoder']
        extractor.onehot_encoder = data['onehot_encoder']
        extractor.feature_columns = data['feature_columns']
        extractor.feature_metadata = data['feature_metadata']
        extractor.is_fitted = data['is_fitted']
        extractor.country_encoding = data.get('country_encoding', {})

        logger.info(f"FeatureExtractor loaded from {load_path}")

        return extractor


if __name__ == "__main__":
    # Test feature extraction
    from src.ingestion.alert_loader import AlertLoader
    from config.settings import ALERTS_CSV_PATH

    # Load alerts
    df = AlertLoader.load_csv(ALERTS_CSV_PATH)

    # Extract features
    extractor = FeatureExtractor()
    X, y = extractor.fit_transform(df)

    print(f"\nFeature extraction complete:")
    print(f"Features shape: {X.shape}")
    print(f"Labels shape: {y.shape}")
    print(f"\nFeature columns:\n{X.columns.tolist()}")
    print(f"\nFirst few rows:\n{X.head()}")

    # Save extractor
    extractor.save()
