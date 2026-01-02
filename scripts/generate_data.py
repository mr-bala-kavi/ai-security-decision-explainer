"""
Generate Synthetic Security Alerts

Standalone script to generate synthetic SOC alert data.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ingestion.alert_generator import generate_and_save_alerts
from config.logging_config import logger


def main():
    """Generate synthetic alerts"""
    logger.info("=" * 60)
    logger.info("GENERATING SYNTHETIC SECURITY ALERTS")
    logger.info("=" * 60)

    try:
        alerts = generate_and_save_alerts()

        logger.info(f"\nGeneration complete!")
        logger.info(f"Total alerts: {len(alerts)}")
        logger.info(f"\nLabel distribution:")
        for label, count in alerts['label'].value_counts().items():
            percentage = (count / len(alerts)) * 100
            logger.info(f"  {label}: {count} ({percentage:.1f}%)")

        logger.info("\nSample alerts:")
        logger.info(alerts.head(3).to_string())

        logger.info("\n" + "=" * 60)
        logger.info("Data generation successful!")
        logger.info("Next step: Run 'python scripts/train_model.py' to train the ML model")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error generating data: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
