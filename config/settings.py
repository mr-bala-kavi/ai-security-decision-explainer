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
PROCESSED_ALERTS_PATH = PROCESSED_DATA_DIR / "processed_alerts.txt"

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

# Real-Time Processing Configuration
REALTIME_CHECK_INTERVAL = int(os.getenv("REALTIME_CHECK_INTERVAL", "60"))  # seconds
REALTIME_ENABLED = os.getenv("REALTIME_ENABLED", "False").lower() == "true"

# Notification Configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "security-ai@yourcompany.com")
ALERT_EMAIL_RECIPIENTS = os.getenv("ALERT_EMAIL_RECIPIENTS", "soc-team@yourcompany.com")

# Slack Configuration
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
SLACK_ENABLED = bool(SLACK_WEBHOOK_URL)

# Microsoft Teams Configuration
TEAMS_WEBHOOK_URL = os.getenv("TEAMS_WEBHOOK_URL", "")
TEAMS_ENABLED = bool(TEAMS_WEBHOOK_URL)

# Alert Routing Rules
NOTIFICATION_RULES = {
    LABEL_MALICIOUS: {
        "channels": ["email", "slack", "teams"],
        "priority": "critical",
        "immediate": True
    },
    LABEL_SUSPICIOUS: {
        "channels": ["slack", "email"],
        "priority": "warning",
        "immediate": False
    },
    LABEL_BENIGN: {
        "channels": [],  # No notifications
        "priority": "info",
        "immediate": False
    }
}
