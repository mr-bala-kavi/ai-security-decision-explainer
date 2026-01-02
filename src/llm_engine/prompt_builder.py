"""
Prompt Builder for Claude API

Constructs prompts for generating security alert explanations.
"""
from typing import Dict


class PromptBuilder:
    """
    Builds prompts for Claude API to generate SOC analyst explanations
    """

    @staticmethod
    def build_explanation_prompt(
        prediction_data: Dict,
        xai_data: Dict,
        alert_data: Dict
    ) -> str:
        """
        Build prompt for generating alert explanation

        Args:
            prediction_data: ML model prediction results
            xai_data: SHAP explanation data
            alert_data: Original alert data

        Returns:
            Formatted prompt string
        """
        prediction = prediction_data['prediction']
        confidence = prediction_data['confidence']
        probabilities = prediction_data['probabilities']

        top_features = xai_data['top_contributing_features'][:5]

        # Format top contributing factors
        factors_text = PromptBuilder._format_contributing_factors(top_features)

        # Format alert summary
        alert_summary = PromptBuilder._format_alert_summary(alert_data)

        # Build prompt
        prompt = f"""You are a SOC (Security Operations Center) analyst explaining a security alert classification to a colleague.

ALERT CLASSIFICATION:
- Verdict: {prediction.upper()}
- Confidence: {confidence:.0%}

PROBABILITY BREAKDOWN:
- Benign: {probabilities.get('benign', 0):.0%}
- Suspicious: {probabilities.get('suspicious', 0):.0%}
- Malicious: {probabilities.get('malicious', 0):.0%}

TOP CONTRIBUTING FACTORS:
{factors_text}

ALERT DETAILS:
{alert_summary}

INSTRUCTIONS:
Write a clear, professional explanation (3-4 sentences) that:
1. States the verdict and confidence level
2. Explains the 2-3 most important factors that led to this decision
3. Recommends a specific action:
   - For MALICIOUS: "Investigate immediately" or "Escalate to incident response"
   - For SUSPICIOUS: "Monitor closely" or "Investigate when possible"
   - For BENIGN: "Mark as false positive" or "No action required"
4. Uses SOC terminology, not ML jargon (e.g., say "threat intelligence match" not "SHAP value")

Keep it concise, actionable, and write as if YOU are the analyst making the call. Avoid phrases like "the model thinks" or "AI analysis shows"."""

        return prompt

    @staticmethod
    def _format_contributing_factors(top_features: list) -> str:
        """
        Format top contributing features for prompt

        Args:
            top_features: List of feature dictionaries

        Returns:
            Formatted string
        """
        lines = []
        for i, feature in enumerate(top_features, 1):
            name = feature['human_readable_name']
            direction = feature['direction']
            value = feature['feature_value']
            contribution = feature['contribution_percentage']

            # Format value nicely
            if isinstance(value, bool):
                value_str = "Yes" if value else "No"
            elif isinstance(value, int):
                value_str = str(value)
            elif isinstance(value, float):
                value_str = f"{value:.2f}"
            else:
                value_str = str(value)

            direction_text = "increases" if direction == "increases_risk" else "decreases"

            lines.append(
                f"{i}. {name}: {value_str} ({direction_text} risk, {contribution:.1f}% contribution)"
            )

        return "\n".join(lines)

    @staticmethod
    def _format_alert_summary(alert_data: Dict) -> str:
        """
        Format alert details for prompt

        Args:
            alert_data: Alert data dictionary

        Returns:
            Formatted string
        """
        summary_lines = []

        # Key fields to include
        key_fields = [
            ('timestamp', 'Timestamp'),
            ('source_ip', 'Source IP'),
            ('source_country', 'Source Country'),
            ('destination_ip', 'Destination IP'),
            ('destination_port', 'Destination Port'),
            ('protocol', 'Protocol'),
            ('failed_login_attempts', 'Failed Login Attempts'),
            ('process_executed', 'Process Executed'),
            ('data_volume_mb', 'Data Volume (MB)'),
        ]

        for field, label in key_fields:
            if field in alert_data:
                value = alert_data[field]
                if isinstance(value, float):
                    value = f"{value:.2f}"
                summary_lines.append(f"- {label}: {value}")

        return "\n".join(summary_lines)

    @staticmethod
    def build_batch_summary_prompt(explanations: list) -> str:
        """
        Build prompt for summarizing multiple alert explanations

        Args:
            explanations: List of explanation dictionaries

        Returns:
            Formatted prompt for batch summary
        """
        # Count by verdict
        verdict_counts = {
            'malicious': sum(1 for e in explanations if e['prediction'] == 'malicious'),
            'suspicious': sum(1 for e in explanations if e['prediction'] == 'suspicious'),
            'benign': sum(1 for e in explanations if e['prediction'] == 'benign')
        }

        prompt = f"""You are a SOC analyst summarizing a batch of {len(explanations)} security alerts.

ALERT BREAKDOWN:
- Malicious: {verdict_counts['malicious']}
- Suspicious: {verdict_counts['suspicious']}
- Benign: {verdict_counts['benign']}

Provide a brief executive summary (2-3 sentences) highlighting:
1. Overall threat level
2. Key patterns or concerns
3. Recommended prioritization

Keep it concise and actionable for SOC leadership."""

        return prompt


if __name__ == "__main__":
    # Test prompt builder
    sample_prediction = {
        'prediction': 'malicious',
        'confidence': 0.92,
        'probabilities': {
            'benign': 0.03,
            'suspicious': 0.05,
            'malicious': 0.92
        }
    }

    sample_xai = {
        'top_contributing_features': [
            {
                'human_readable_name': 'Threat Intelligence Match',
                'impact_score': 0.35,
                'direction': 'increases_risk',
                'feature_value': True,
                'contribution_percentage': 35.0
            },
            {
                'human_readable_name': 'Failed Authentication Count',
                'impact_score': 0.22,
                'direction': 'increases_risk',
                'feature_value': 47,
                'contribution_percentage': 22.0
            }
        ]
    }

    sample_alert = {
        'timestamp': '2026-01-02T03:45:22',
        'source_ip': '185.220.101.42',
        'source_country': 'RU',
        'destination_ip': '10.0.1.50',
        'destination_port': 3389,
        'protocol': 'TCP',
        'failed_login_attempts': 47,
        'process_executed': 'mimikatz.exe',
        'data_volume_mb': 125.5
    }

    prompt = PromptBuilder.build_explanation_prompt(
        sample_prediction,
        sample_xai,
        sample_alert
    )

    print("=" * 60)
    print("GENERATED PROMPT:")
    print("=" * 60)
    print(prompt)
