"""
Alert Loader

Loads and validates SOC alerts from CSV/JSON files.
"""
import pandas as pd
from pathlib import Path
from loguru import logger
from typing import Union


class AlertLoader:
    """Loads security alerts from files"""

    REQUIRED_COLUMNS = [
        "alert_id", "timestamp", "source_ip", "source_country",
        "destination_ip", "destination_port", "protocol",
        "failed_login_attempts", "successful_login_after_failures",
        "process_executed", "process_hash_known", "admin_privilege_escalation",
        "off_hours_activity", "data_volume_mb", "connection_duration_seconds",
        "unique_destinations_count", "geo_impossible_travel",
        "user_agent_anomaly", "threat_intel_match", "encryption_protocol",
        "lateral_movement_detected", "label"
    ]

    @staticmethod
    def load_csv(file_path: Union[str, Path]) -> pd.DataFrame:
        """
        Load alerts from CSV file

        Args:
            file_path: Path to CSV file

        Returns:
            DataFrame of alerts

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If required columns are missing
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Alert file not found: {file_path}")

        logger.info(f"Loading alerts from {file_path}")
        df = pd.read_csv(file_path)

        # Validate columns
        missing_cols = set(AlertLoader.REQUIRED_COLUMNS) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        logger.info(f"Loaded {len(df)} alerts with {len(df.columns)} columns")
        logger.info(f"Label distribution:\n{df['label'].value_counts()}")

        return df

    @staticmethod
    def load_json(file_path: Union[str, Path]) -> pd.DataFrame:
        """
        Load alerts from JSON file

        Args:
            file_path: Path to JSON file

        Returns:
            DataFrame of alerts
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Alert file not found: {file_path}")

        logger.info(f"Loading alerts from {file_path}")
        df = pd.read_json(file_path)

        # Validate columns
        missing_cols = set(AlertLoader.REQUIRED_COLUMNS) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        logger.info(f"Loaded {len(df)} alerts")

        return df

    @staticmethod
    def get_alert_by_id(df: pd.DataFrame, alert_id: str) -> pd.Series:
        """
        Get a specific alert by ID

        Args:
            df: DataFrame of alerts
            alert_id: Alert ID to find

        Returns:
            Series representing the alert

        Raises:
            ValueError: If alert ID not found
        """
        alert = df[df['alert_id'] == alert_id]

        if len(alert) == 0:
            raise ValueError(f"Alert ID not found: {alert_id}")

        return alert.iloc[0]
