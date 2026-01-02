"""
Real-Time Alert Processing Engine
Continuously monitors for new alerts and processes them through the AI pipeline

Created by Kavi
"""

import time
import pandas as pd
from pathlib import Path
from datetime import datetime
from loguru import logger
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingestion.alert_loader import AlertLoader
from src.feature_engineering.feature_extractor import FeatureExtractor
from src.ml_engine.model_trainer import ModelTrainer
from src.ml_engine.model_predictor import ModelPredictor
from src.xai.shap_explainer import SHAPExplainer
from src.llm_engine.claude_client import ClaudeExplainer
from config.settings import ALERTS_CSV_PATH, ALERT_LABELS, PROCESSED_ALERTS_PATH


class RealTimeProcessor:
    """Real-time alert processing engine"""

    def __init__(self):
        """Initialize the processor"""
        logger.info("🚀 Initializing Real-Time AI Security Processor")
        logger.info("Created by Kavi")

        # Load ML components
        try:
            self.model_trainer = ModelTrainer.load()
            self.feature_extractor = FeatureExtractor.load()
            logger.success("✅ ML model and feature extractor loaded")
        except FileNotFoundError:
            logger.error("❌ ML model not found. Please train the model first:")
            logger.error("   python scripts/train_model.py")
            sys.exit(1)

        # Initialize explainers
        self.model = self.model_trainer.model
        self.predictor = ModelPredictor(self.model)
        self.shap_explainer = SHAPExplainer(
            self.model,
            self.feature_extractor.feature_columns,
            self.feature_extractor.feature_metadata
        )
        self.claude_explainer = ClaudeExplainer()

        # Track processed alerts
        self.processed_alerts = set()
        self.load_processed_alerts()

        logger.success("✅ Real-time processor initialized")

    def load_processed_alerts(self):
        """Load list of already processed alert IDs"""
        if PROCESSED_ALERTS_PATH.exists():
            with open(PROCESSED_ALERTS_PATH, 'r') as f:
                self.processed_alerts = set(line.strip() for line in f)
            logger.info(f"📋 Loaded {len(self.processed_alerts)} processed alerts")

    def mark_as_processed(self, alert_id: str):
        """Mark an alert as processed"""
        self.processed_alerts.add(alert_id)

        # Append to file
        with open(PROCESSED_ALERTS_PATH, 'a') as f:
            f.write(f"{alert_id}\n")

    def process_alert(self, alert_row: pd.Series) -> dict:
        """
        Process a single alert through the AI pipeline

        Args:
            alert_row: Alert data as pandas Series

        Returns:
            Complete analysis result
        """
        alert_id = alert_row['alert_id']

        logger.info(f"🔍 Processing alert: {alert_id}")

        # Step 1: Extract features
        alert_df = alert_row.to_frame().T
        X = self.feature_extractor.transform(alert_df)

        # Step 2: ML prediction
        prediction = self.predictor.predict(X)
        verdict = prediction['prediction']
        confidence = prediction['confidence']

        logger.info(f"   Verdict: {verdict.upper()} (confidence: {confidence:.1%})")

        # Step 3: SHAP explanation
        predicted_class_idx = ALERT_LABELS.index(verdict)
        xai_explanation = self.shap_explainer.explain_prediction(
            X, verdict, predicted_class_idx
        )

        # Step 4: LLM explanation
        try:
            llm_explanation = self.claude_explainer.generate_explanation(
                prediction,
                xai_explanation,
                alert_row.to_dict()
            )
        except Exception as e:
            logger.warning(f"   LLM generation failed: {e}. Using fallback.")
            llm_explanation = self.claude_explainer._generate_fallback_explanation(
                prediction, xai_explanation
            )

        # Compile result
        result = {
            'alert_id': alert_id,
            'timestamp': datetime.now().isoformat(),
            'alert_data': alert_row.to_dict(),
            'verdict': verdict,
            'confidence': confidence,
            'probabilities': prediction['probabilities'],
            'top_features': xai_explanation['top_contributing_features'][:5],
            'explanation': llm_explanation['explanation_text'],
            'recommended_action': llm_explanation['recommended_action']
        }

        return result

    def send_notifications(self, result: dict):
        """
        Send notifications based on alert severity

        Args:
            result: Processing result
        """
        verdict = result['verdict']

        if verdict == 'malicious':
            logger.critical(f"🚨 MALICIOUS ALERT DETECTED: {result['alert_id']}")
            self.send_critical_alert(result)

        elif verdict == 'suspicious':
            logger.warning(f"⚠️  SUSPICIOUS ALERT: {result['alert_id']}")
            self.send_warning_alert(result)

        else:
            logger.info(f"✅ Benign alert: {result['alert_id']}")

    def send_critical_alert(self, result: dict):
        """Send critical alert notifications (email, Slack, SMS)"""
        # TODO: Implement email notification
        # TODO: Implement Slack notification
        # TODO: Implement PagerDuty/SMS

        logger.info("   📧 Sending email to SOC team...")
        logger.info("   💬 Sending Slack notification...")

        # For now, just log
        logger.critical(f"""
        ╔═══════════════════════════════════════════════════════════════╗
        ║           🚨 CRITICAL SECURITY ALERT 🚨                       ║
        ╠═══════════════════════════════════════════════════════════════╣
        ║ Alert ID: {result['alert_id']:47} ║
        ║ Verdict:  MALICIOUS                                          ║
        ║ Confidence: {result['confidence']*100:5.1f}%                                       ║
        ║                                                               ║
        ║ Explanation:                                                  ║
        ║ {result['explanation'][:60]:60} ║
        ║                                                               ║
        ║ Recommended Action: {result['recommended_action']:38} ║
        ╚═══════════════════════════════════════════════════════════════╝
        """)

    def send_warning_alert(self, result: dict):
        """Send warning alert notifications"""
        logger.warning(f"""
        ┌─────────────────────────────────────────────────────────────┐
        │           ⚠️  SUSPICIOUS ACTIVITY DETECTED ⚠️               │
        ├─────────────────────────────────────────────────────────────┤
        │ Alert ID: {result['alert_id']:45} │
        │ Confidence: {result['confidence']*100:5.1f}%                                     │
        │ Action: {result['recommended_action']:48} │
        └─────────────────────────────────────────────────────────────┘
        """)

    def run(self, interval_seconds: int = 60):
        """
        Run the real-time processor

        Args:
            interval_seconds: How often to check for new alerts (default: 60)
        """
        logger.info(f"🔄 Starting real-time monitoring (checking every {interval_seconds}s)")
        logger.info("Press Ctrl+C to stop")

        try:
            while True:
                try:
                    # Load current alerts
                    df = AlertLoader.load_csv(ALERTS_CSV_PATH)

                    # Find unprocessed alerts
                    new_alerts = df[~df['alert_id'].isin(self.processed_alerts)]

                    if len(new_alerts) > 0:
                        logger.info(f"📬 Found {len(new_alerts)} new alerts")

                        for idx, alert in new_alerts.iterrows():
                            # Process alert
                            result = self.process_alert(alert)

                            # Send notifications
                            self.send_notifications(result)

                            # Mark as processed
                            self.mark_as_processed(alert['alert_id'])

                    else:
                        logger.debug("No new alerts")

                except Exception as e:
                    logger.error(f"Error processing alerts: {e}", exc_info=True)

                # Wait before next check
                time.sleep(interval_seconds)

        except KeyboardInterrupt:
            logger.info("\n⏹️  Stopping real-time processor")
            logger.info("👋 Goodbye!")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Real-Time AI Security Alert Processor - Created by Kavi"
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Check interval in seconds (default: 60)'
    )

    args = parser.parse_args()

    # Create processor
    processor = RealTimeProcessor()

    # Run
    processor.run(interval_seconds=args.interval)


if __name__ == "__main__":
    main()
