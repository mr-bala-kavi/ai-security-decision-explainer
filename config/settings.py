"""
Configuration Management for AI Security Decision Explainer
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# OpenAI API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")

# ML Configuration
RANDOM_SEED = int(os.getenv("RANDOM_SEED", "42"))
TEST_SIZE = float(os.getenv("TEST_SIZE", "0.2"))
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))

# Dashboard Configuration
DASHBOARD_HOST = os.getenv("DASHBOARD_HOST", "127.0.0.1")
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8000"))
DEBUG_MODE = os.getenv("DEBUG_MODE", "True").lower() == "true"

# Data Paths
DATA_DIR = PROJECT_ROOT / os.getenv("DATA_DIR", "data")
MODEL_DIR = PROJECT_ROOT / os.getenv("MODEL_DIR", "data/models")
LOG_DIR = PROJECT_ROOT / os.getenv("LOG_DIR", "logs")

# Create directories if they don't exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Data file paths
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

ALERTS_CSV_PATH = RAW_DATA_DIR / "alerts.csv"
PROCESSED_FEATURES_PATH = PROCESSED_DATA_DIR / "features.csv"
FEATURE_METADATA_PATH = PROCESSED_DATA_DIR / "feature_metadata.pkl"

# Model file paths
MODEL_PATH = MODEL_DIR / "random_forest_model.pkl"
SCALER_PATH = MODEL_DIR / "feature_scaler.pkl"
ENCODER_PATH = MODEL_DIR / "feature_encoder.pkl"

# Synthetic Data Generation Configuration
NUM_ALERTS = 10000
BENIGN_RATIO = 0.60
SUSPICIOUS_RATIO = 0.25
MALICIOUS_RATIO = 0.15

# ML Model Configuration
N_ESTIMATORS_OPTIONS = [100, 200, 300]
MAX_DEPTH_OPTIONS = [10, 20, None]
MIN_SAMPLES_SPLIT_OPTIONS = [2, 5, 10]

# XAI Configuration
TOP_N_FEATURES = 10  # Number of top features to display

# LLM Configuration
LLM_MAX_TOKENS = 300
LLM_TEMPERATURE = 0.3

# Feature name mapping (technical -> human-readable)
FEATURE_NAME_MAPPING = {
    "failed_login_attempts": "Failed Authentication Count",
    "successful_login_after_failures": "Successful Login After Failures",
    "process_hash_known": "Known Process Hash",
    "admin_privilege_escalation": "Administrative Privilege Escalation",
    "off_hours_activity": "Off-Hours Activity",
    "data_volume_mb": "Data Transfer Volume (MB)",
    "connection_duration_seconds": "Connection Duration (seconds)",
    "unique_destinations_count": "Unique Destination Count",
    "geo_impossible_travel": "Geographically Impossible Travel",
    "user_agent_anomaly": "User Agent Anomaly",
    "threat_intel_match": "Threat Intelligence Match",
    "lateral_movement_detected": "Lateral Movement Detected",
    "hour_of_day": "Hour of Day",
    "day_of_week": "Day of Week",
    "is_night_shift": "Night Shift Activity",
    "login_risk_score": "Login Risk Score",
    "privilege_risk": "Privilege Risk Score",
    "threat_indicator_count": "Total Threat Indicators",
}

# Alert labels
LABEL_BENIGN = "benign"
LABEL_SUSPICIOUS = "suspicious"
LABEL_MALICIOUS = "malicious"

ALERT_LABELS = [LABEL_BENIGN, LABEL_SUSPICIOUS, LABEL_MALICIOUS]

# Color coding for dashboard
LABEL_COLORS = {
    LABEL_BENIGN: "#28a745",      # Green
    LABEL_SUSPICIOUS: "#ffc107",  # Yellow
    LABEL_MALICIOUS: "#dc3545"    # Red
}
