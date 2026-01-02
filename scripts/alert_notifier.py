"""
Alert Notification System
Sends notifications via Email, Slack, Teams, and SMS

Created by Kavi
"""

import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from loguru import logger
from typing import Dict, List
import os


class AlertNotifier:
    """Sends notifications through multiple channels"""

    def __init__(self):
        """Initialize notification channels"""
        # Email configuration
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', 'security-ai@yourcompany.com')

        # Slack configuration
        self.slack_webhook = os.getenv('SLACK_WEBHOOK_URL', '')

        # Microsoft Teams configuration
        self.teams_webhook = os.getenv('TEAMS_WEBHOOK_URL', '')

    def send_email(self, to_addresses: List[str], subject: str, body: str, html: bool = False):
        """
        Send email notification

        Args:
            to_addresses: List of recipient email addresses
            subject: Email subject
            body: Email body
            html: Whether body is HTML
        """
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = ', '.join(to_addresses)
            msg['Subject'] = subject

            if html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            logger.success(f"📧 Email sent to {', '.join(to_addresses)}")

        except Exception as e:
            logger.error(f"Failed to send email: {e}")

    def send_slack_message(self, alert_data: Dict):
        """
        Send Slack notification

        Args:
            alert_data: Alert information dictionary
        """
        if not self.slack_webhook:
            logger.warning("Slack webhook not configured")
            return

        try:
            verdict = alert_data['verdict']
            confidence = alert_data['confidence']

            # Determine color based on verdict
            color_map = {
                'malicious': '#FF0054',  # Red
                'suspicious': '#FFBE0B',  # Yellow
                'benign': '#06FFA5'  # Green
            }
            color = color_map.get(verdict, '#00F5FF')

            # Determine emoji
            emoji_map = {
                'malicious': '🚨',
                'suspicious': '⚠️',
                'benign': '✅'
            }
            emoji = emoji_map.get(verdict, '🔔')

            message = {
                "username": "AI Security Explainer",
                "icon_emoji": ":shield:",
                "attachments": [
                    {
                        "color": color,
                        "title": f"{emoji} Security Alert: {verdict.upper()}",
                        "text": alert_data.get('explanation', ''),
                        "fields": [
                            {
                                "title": "Alert ID",
                                "value": alert_data.get('alert_id', 'N/A'),
                                "short": True
                            },
                            {
                                "title": "Confidence",
                                "value": f"{confidence*100:.1f}%",
                                "short": True
                            },
                            {
                                "title": "Source IP",
                                "value": alert_data.get('alert_data', {}).get('source_ip', 'N/A'),
                                "short": True
                            },
                            {
                                "title": "Process",
                                "value": alert_data.get('alert_data', {}).get('process_executed', 'N/A'),
                                "short": True
                            },
                            {
                                "title": "Recommended Action",
                                "value": alert_data.get('recommended_action', 'Monitor'),
                                "short": False
                            }
                        ],
                        "footer": "Created by Kavi",
                        "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png",
                        "ts": int(alert_data.get('timestamp', 0))
                    }
                ]
            }

            response = requests.post(self.slack_webhook, json=message, timeout=10)
            response.raise_for_status()

            logger.success("💬 Slack notification sent")

        except Exception as e:
            logger.error(f"Failed to send Slack message: {e}")

    def send_teams_message(self, alert_data: Dict):
        """
        Send Microsoft Teams notification

        Args:
            alert_data: Alert information dictionary
        """
        if not self.teams_webhook:
            logger.warning("Teams webhook not configured")
            return

        try:
            verdict = alert_data['verdict']
            confidence = alert_data['confidence']

            # Determine color
            color_map = {
                'malicious': 'attention',  # Red
                'suspicious': 'warning',  # Yellow
                'benign': 'good'  # Green
            }
            theme_color = color_map.get(verdict, 'accent')

            message = {
                "@type": "MessageCard",
                "@context": "https://schema.org/extensions",
                "summary": f"Security Alert: {verdict.upper()}",
                "themeColor": theme_color,
                "title": f"🛡️ AI Security Alert: {verdict.upper()}",
                "sections": [
                    {
                        "activityTitle": "Alert Details",
                        "facts": [
                            {"name": "Alert ID:", "value": alert_data.get('alert_id', 'N/A')},
                            {"name": "Confidence:", "value": f"{confidence*100:.1f}%"},
                            {"name": "Source IP:", "value": alert_data.get('alert_data', {}).get('source_ip', 'N/A')},
                            {"name": "Process:", "value": alert_data.get('alert_data', {}).get('process_executed', 'N/A')},
                            {"name": "Action:", "value": alert_data.get('recommended_action', 'Monitor')}
                        ]
                    },
                    {
                        "activityTitle": "AI Explanation",
                        "text": alert_data.get('explanation', '')
                    }
                ],
                "potentialAction": [
                    {
                        "@type": "OpenUri",
                        "name": "View Dashboard",
                        "targets": [
                            {"os": "default", "uri": "http://your-dashboard-url"}
                        ]
                    }
                ]
            }

            response = requests.post(self.teams_webhook, json=message, timeout=10)
            response.raise_for_status()

            logger.success("📢 Teams notification sent")

        except Exception as e:
            logger.error(f"Failed to send Teams message: {e}")

    def notify_all(self, alert_data: Dict, channels: List[str] = None):
        """
        Send notifications through all configured channels

        Args:
            alert_data: Alert information
            channels: List of channels to use ['email', 'slack', 'teams']
                     If None, uses all available channels
        """
        verdict = alert_data['verdict']

        # Default channels based on severity
        if channels is None:
            if verdict == 'malicious':
                channels = ['email', 'slack', 'teams']
            elif verdict == 'suspicious':
                channels = ['slack', 'email']
            else:
                channels = []  # Don't notify for benign

        # Send to each channel
        if 'email' in channels and self.smtp_username:
            recipients = os.getenv('ALERT_EMAIL_RECIPIENTS', 'soc-team@yourcompany.com').split(',')
            subject = f"🚨 Security Alert: {verdict.upper()}"

            body = f"""
Security Alert Notification
============================

Verdict: {verdict.upper()}
Confidence: {alert_data['confidence']*100:.1f}%

Alert Details:
- Alert ID: {alert_data.get('alert_id', 'N/A')}
- Source IP: {alert_data.get('alert_data', {}).get('source_ip', 'N/A')}
- Process: {alert_data.get('alert_data', {}).get('process_executed', 'N/A')}
- Timestamp: {alert_data.get('timestamp', 'N/A')}

AI Explanation:
{alert_data.get('explanation', '')}

Recommended Action: {alert_data.get('recommended_action', 'Monitor')}

---
This alert was generated by AI Security Decision Explainer
Created by Kavi
            """

            self.send_email(recipients, subject, body)

        if 'slack' in channels:
            self.send_slack_message(alert_data)

        if 'teams' in channels:
            self.send_teams_message(alert_data)


# Example usage
if __name__ == "__main__":
    # Test notification
    notifier = AlertNotifier()

    test_alert = {
        'alert_id': 'test-123',
        'timestamp': '2024-01-01T12:00:00',
        'verdict': 'malicious',
        'confidence': 0.95,
        'explanation': 'This is a test alert for notification system testing.',
        'recommended_action': 'INVESTIGATE',
        'alert_data': {
            'source_ip': '192.168.1.100',
            'process_executed': 'test.exe'
        }
    }

    print("🧪 Testing notification system...")
    print("Configure environment variables:")
    print("  - SMTP_USERNAME")
    print("  - SMTP_PASSWORD")
    print("  - SLACK_WEBHOOK_URL")
    print("  - TEAMS_WEBHOOK_URL")

    # Send test notifications
    notifier.notify_all(test_alert, channels=['slack'])
