"""
Synthetic SOC Alert Generator

Generates realistic security alerts for training the ML model.
Simulates benign, suspicious, and malicious activities.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import uuid
from typing import List, Dict
from loguru import logger

from config.settings import (
    NUM_ALERTS, BENIGN_RATIO, SUSPICIOUS_RATIO, MALICIOUS_RATIO,
    LABEL_BENIGN, LABEL_SUSPICIOUS, LABEL_MALICIOUS, RANDOM_SEED
)


class AlertGenerator:
    """Generates synthetic SOC security alerts"""

    def __init__(self, num_alerts: int = NUM_ALERTS, seed: int = RANDOM_SEED):
        self.num_alerts = num_alerts
        self.seed = seed
        np.random.seed(seed)

        # Calculate number of alerts per category
        self.num_benign = int(num_alerts * BENIGN_RATIO)
        self.num_suspicious = int(num_alerts * SUSPICIOUS_RATIO)
        self.num_malicious = num_alerts - self.num_benign - self.num_suspicious

        logger.info(f"Initializing AlertGenerator: {num_alerts} total alerts")
        logger.info(f"  Benign: {self.num_benign}, Suspicious: {self.num_suspicious}, Malicious: {self.num_malicious}")

        # Country pools
        self.trusted_countries = ["US", "CA", "GB", "DE", "FR", "AU", "JP"]
        self.suspicious_countries = ["RU", "CN", "KP", "IR", "BR", "IN"]

        # Process pools
        self.legitimate_processes = [
            "chrome.exe", "firefox.exe", "outlook.exe", "teams.exe",
            "excel.exe", "word.exe", "powershell.exe", "python.exe"
        ]
        self.suspicious_processes = [
            "mimikatz.exe", "psexec.exe", "nc.exe", "whoami.exe",
            "net.exe", "rundll32.exe", "regsvr32.exe", "certutil.exe"
        ]

    def generate_alerts(self) -> pd.DataFrame:
        """Generate all synthetic alerts"""
        logger.info("Generating synthetic alerts...")

        benign_alerts = self._generate_benign_alerts(self.num_benign)
        suspicious_alerts = self._generate_suspicious_alerts(self.num_suspicious)
        malicious_alerts = self._generate_malicious_alerts(self.num_malicious)

        # Combine all alerts
        all_alerts = pd.concat([benign_alerts, suspicious_alerts, malicious_alerts], ignore_index=True)

        # Shuffle
        all_alerts = all_alerts.sample(frac=1, random_state=self.seed).reset_index(drop=True)

        logger.info(f"Generated {len(all_alerts)} total alerts")
        logger.info(f"Label distribution:\n{all_alerts['label'].value_counts()}")

        return all_alerts

    def _generate_benign_alerts(self, n: int) -> pd.DataFrame:
        """Generate benign (normal) alerts"""
        alerts = []

        for _ in range(n):
            # Normal business hours (8 AM - 6 PM on weekdays)
            timestamp = self._random_timestamp(business_hours=True)

            alert = {
                "alert_id": str(uuid.uuid4()),
                "timestamp": timestamp.isoformat(),
                "source_ip": self._random_ip(internal=True),
                "source_country": np.random.choice(self.trusted_countries),
                "destination_ip": self._random_ip(internal=True),
                "destination_port": np.random.choice([80, 443, 22, 3389, 445]),
                "protocol": np.random.choice(["TCP", "UDP"], p=[0.8, 0.2]),
                "failed_login_attempts": np.random.choice([0, 1, 2], p=[0.7, 0.2, 0.1]),
                "successful_login_after_failures": False,
                "process_executed": np.random.choice(self.legitimate_processes),
                "process_hash_known": True,
                "admin_privilege_escalation": False,
                "off_hours_activity": False,
                "data_volume_mb": np.random.uniform(0.1, 50),
                "connection_duration_seconds": int(np.random.uniform(10, 300)),
                "unique_destinations_count": np.random.randint(1, 5),
                "geo_impossible_travel": False,
                "user_agent_anomaly": False,
                "threat_intel_match": False,
                "encryption_protocol": np.random.choice(["TLS", "SSL", "None"], p=[0.7, 0.2, 0.1]),
                "lateral_movement_detected": False,
                "label": LABEL_BENIGN
            }
            alerts.append(alert)

        return pd.DataFrame(alerts)

    def _generate_suspicious_alerts(self, n: int) -> pd.DataFrame:
        """Generate suspicious (potentially risky) alerts"""
        alerts = []

        for _ in range(n):
            # Mix of business and off-hours
            timestamp = self._random_timestamp(business_hours=np.random.random() > 0.4)

            alert = {
                "alert_id": str(uuid.uuid4()),
                "timestamp": timestamp.isoformat(),
                "source_ip": self._random_ip(internal=np.random.random() > 0.3),
                "source_country": np.random.choice(self.trusted_countries + self.suspicious_countries),
                "destination_ip": self._random_ip(internal=True),
                "destination_port": np.random.choice([80, 443, 22, 3389, 445, 8080, 1433]),
                "protocol": np.random.choice(["TCP", "UDP"], p=[0.85, 0.15]),
                "failed_login_attempts": np.random.choice([3, 4, 5, 6, 7], p=[0.3, 0.25, 0.2, 0.15, 0.1]),
                "successful_login_after_failures": np.random.random() > 0.6,
                "process_executed": np.random.choice(self.legitimate_processes + self.suspicious_processes[:2]),
                "process_hash_known": np.random.random() > 0.3,
                "admin_privilege_escalation": np.random.random() > 0.8,
                "off_hours_activity": np.random.random() > 0.5,
                "data_volume_mb": np.random.uniform(50, 200),
                "connection_duration_seconds": int(np.random.uniform(300, 1800)),
                "unique_destinations_count": np.random.randint(5, 15),
                "geo_impossible_travel": np.random.random() > 0.85,
                "user_agent_anomaly": np.random.random() > 0.7,
                "threat_intel_match": False,  # Not on threat intel yet
                "encryption_protocol": np.random.choice(["TLS", "SSL", "None"], p=[0.5, 0.3, 0.2]),
                "lateral_movement_detected": np.random.random() > 0.9,
                "label": LABEL_SUSPICIOUS
            }
            alerts.append(alert)

        return pd.DataFrame(alerts)

    def _generate_malicious_alerts(self, n: int) -> pd.DataFrame:
        """Generate malicious (definitely bad) alerts"""
        alerts = []

        for _ in range(n):
            # Mostly off-hours
            timestamp = self._random_timestamp(business_hours=np.random.random() > 0.8)

            # Choose attack type
            attack_type = np.random.choice([
                "brute_force", "data_exfiltration", "lateral_movement",
                "privilege_escalation", "c2_communication"
            ])

            if attack_type == "brute_force":
                alert = self._create_brute_force_alert(timestamp)
            elif attack_type == "data_exfiltration":
                alert = self._create_data_exfiltration_alert(timestamp)
            elif attack_type == "lateral_movement":
                alert = self._create_lateral_movement_alert(timestamp)
            elif attack_type == "privilege_escalation":
                alert = self._create_privilege_escalation_alert(timestamp)
            else:  # c2_communication
                alert = self._create_c2_communication_alert(timestamp)

            alerts.append(alert)

        return pd.DataFrame(alerts)

    def _create_brute_force_alert(self, timestamp: datetime) -> Dict:
        """Create brute force attack alert"""
        return {
            "alert_id": str(uuid.uuid4()),
            "timestamp": timestamp.isoformat(),
            "source_ip": self._random_ip(internal=False),
            "source_country": np.random.choice(self.suspicious_countries),
            "destination_ip": self._random_ip(internal=True),
            "destination_port": np.random.choice([22, 3389, 445]),
            "protocol": "TCP",
            "failed_login_attempts": np.random.randint(20, 150),
            "successful_login_after_failures": np.random.random() > 0.5,
            "process_executed": np.random.choice(self.legitimate_processes),
            "process_hash_known": True,
            "admin_privilege_escalation": np.random.random() > 0.6,
            "off_hours_activity": True,
            "data_volume_mb": np.random.uniform(1, 50),
            "connection_duration_seconds": int(np.random.uniform(1800, 7200)),
            "unique_destinations_count": np.random.randint(1, 3),
            "geo_impossible_travel": np.random.random() > 0.5,
            "user_agent_anomaly": np.random.random() > 0.5,
            "threat_intel_match": np.random.random() > 0.3,
            "encryption_protocol": "None",
            "lateral_movement_detected": False,
            "label": LABEL_MALICIOUS
        }

    def _create_data_exfiltration_alert(self, timestamp: datetime) -> Dict:
        """Create data exfiltration alert"""
        return {
            "alert_id": str(uuid.uuid4()),
            "timestamp": timestamp.isoformat(),
            "source_ip": self._random_ip(internal=True),
            "source_country": np.random.choice(self.trusted_countries),
            "destination_ip": self._random_ip(internal=False),
            "destination_port": np.random.choice([80, 443, 21, 22]),
            "protocol": "TCP",
            "failed_login_attempts": np.random.randint(0, 3),
            "successful_login_after_failures": False,
            "process_executed": np.random.choice(self.suspicious_processes),
            "process_hash_known": False,
            "admin_privilege_escalation": True,
            "off_hours_activity": True,
            "data_volume_mb": np.random.uniform(500, 5000),  # Large data transfer
            "connection_duration_seconds": int(np.random.uniform(3600, 14400)),
            "unique_destinations_count": np.random.randint(1, 5),
            "geo_impossible_travel": False,
            "user_agent_anomaly": True,
            "threat_intel_match": np.random.random() > 0.4,
            "encryption_protocol": np.random.choice(["TLS", "None"], p=[0.6, 0.4]),
            "lateral_movement_detected": False,
            "label": LABEL_MALICIOUS
        }

    def _create_lateral_movement_alert(self, timestamp: datetime) -> Dict:
        """Create lateral movement alert"""
        return {
            "alert_id": str(uuid.uuid4()),
            "timestamp": timestamp.isoformat(),
            "source_ip": self._random_ip(internal=True),
            "source_country": np.random.choice(self.trusted_countries),
            "destination_ip": self._random_ip(internal=True),
            "destination_port": np.random.choice([445, 135, 139, 3389]),
            "protocol": "TCP",
            "failed_login_attempts": np.random.randint(5, 20),
            "successful_login_after_failures": True,
            "process_executed": np.random.choice(self.suspicious_processes),
            "process_hash_known": False,
            "admin_privilege_escalation": True,
            "off_hours_activity": True,
            "data_volume_mb": np.random.uniform(10, 100),
            "connection_duration_seconds": int(np.random.uniform(300, 1800)),
            "unique_destinations_count": np.random.randint(10, 50),  # Many internal hosts
            "geo_impossible_travel": False,
            "user_agent_anomaly": True,
            "threat_intel_match": np.random.random() > 0.5,
            "encryption_protocol": "None",
            "lateral_movement_detected": True,
            "label": LABEL_MALICIOUS
        }

    def _create_privilege_escalation_alert(self, timestamp: datetime) -> Dict:
        """Create privilege escalation alert"""
        return {
            "alert_id": str(uuid.uuid4()),
            "timestamp": timestamp.isoformat(),
            "source_ip": self._random_ip(internal=True),
            "source_country": np.random.choice(self.trusted_countries + self.suspicious_countries),
            "destination_ip": self._random_ip(internal=True),
            "destination_port": np.random.choice([22, 3389, 445]),
            "protocol": "TCP",
            "failed_login_attempts": np.random.randint(8, 25),
            "successful_login_after_failures": True,
            "process_executed": np.random.choice(self.suspicious_processes),
            "process_hash_known": False,
            "admin_privilege_escalation": True,
            "off_hours_activity": True,
            "data_volume_mb": np.random.uniform(5, 50),
            "connection_duration_seconds": int(np.random.uniform(600, 3600)),
            "unique_destinations_count": np.random.randint(2, 8),
            "geo_impossible_travel": np.random.random() > 0.7,
            "user_agent_anomaly": True,
            "threat_intel_match": np.random.random() > 0.4,
            "encryption_protocol": np.random.choice(["TLS", "None"], p=[0.4, 0.6]),
            "lateral_movement_detected": np.random.random() > 0.6,
            "label": LABEL_MALICIOUS
        }

    def _create_c2_communication_alert(self, timestamp: datetime) -> Dict:
        """Create C2 (Command & Control) communication alert"""
        return {
            "alert_id": str(uuid.uuid4()),
            "timestamp": timestamp.isoformat(),
            "source_ip": self._random_ip(internal=True),
            "source_country": np.random.choice(self.trusted_countries),
            "destination_ip": self._random_ip(internal=False),
            "destination_port": np.random.choice([80, 443, 8080, 53]),
            "protocol": np.random.choice(["TCP", "UDP"], p=[0.7, 0.3]),
            "failed_login_attempts": 0,
            "successful_login_after_failures": False,
            "process_executed": np.random.choice(self.suspicious_processes),
            "process_hash_known": False,
            "admin_privilege_escalation": np.random.random() > 0.6,
            "off_hours_activity": True,
            "data_volume_mb": np.random.uniform(0.1, 10),  # Small beacons
            "connection_duration_seconds": int(np.random.uniform(10, 120)),  # Short connections
            "unique_destinations_count": np.random.randint(1, 3),
            "geo_impossible_travel": False,
            "user_agent_anomaly": True,
            "threat_intel_match": True,  # Known C2 server
            "encryption_protocol": np.random.choice(["TLS", "None"], p=[0.7, 0.3]),
            "lateral_movement_detected": np.random.random() > 0.7,
            "label": LABEL_MALICIOUS
        }

    def _random_timestamp(self, business_hours: bool = False) -> datetime:
        """Generate random timestamp"""
        # Random date in the past 30 days
        days_ago = np.random.randint(0, 30)
        base_date = datetime.now() - timedelta(days=days_ago)

        if business_hours:
            # Weekday, 8 AM - 6 PM
            weekday = np.random.randint(0, 5)  # Mon-Fri
            hour = np.random.randint(8, 18)
            base_date = base_date.replace(hour=hour, minute=np.random.randint(0, 60))
            # Set to a weekday
            while base_date.weekday() >= 5:
                base_date -= timedelta(days=1)
        else:
            # Any time, including weekends and nights
            hour = np.random.randint(0, 24)
            base_date = base_date.replace(hour=hour, minute=np.random.randint(0, 60))

        return base_date

    def _random_ip(self, internal: bool = True) -> str:
        """Generate random IP address"""
        if internal:
            # Internal IP ranges: 10.x.x.x or 192.168.x.x
            if np.random.random() > 0.5:
                return f"10.{np.random.randint(0, 256)}.{np.random.randint(0, 256)}.{np.random.randint(1, 256)}"
            else:
                return f"192.168.{np.random.randint(0, 256)}.{np.random.randint(1, 256)}"
        else:
            # External IP (avoiding private ranges)
            octets = [np.random.randint(1, 256) for _ in range(4)]
            # Avoid private ranges
            while octets[0] in [10, 172, 192]:
                octets[0] = np.random.randint(1, 256)
            return ".".join(map(str, octets))


def generate_and_save_alerts(output_path: str = None) -> pd.DataFrame:
    """
    Generate synthetic alerts and save to CSV

    Args:
        output_path: Path to save CSV file (default: from settings)

    Returns:
        DataFrame of generated alerts
    """
    from config.settings import ALERTS_CSV_PATH

    output_path = output_path or str(ALERTS_CSV_PATH)

    generator = AlertGenerator()
    alerts_df = generator.generate_alerts()

    # Save to CSV
    alerts_df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(alerts_df)} alerts to {output_path}")

    return alerts_df


if __name__ == "__main__":
    # Generate alerts when run directly
    alerts = generate_and_save_alerts()
    print(f"\nGenerated {len(alerts)} alerts")
    print(f"\nLabel distribution:\n{alerts['label'].value_counts()}")
    print(f"\nFirst few alerts:\n{alerts.head()}")
