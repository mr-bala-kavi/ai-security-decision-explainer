# AI Security Decision Explainer

A **trust-first AI security system** for SOC (Security Operations Center) environments that explains why security alerts are classified as benign, suspicious, or malicious.

This project focuses on **explainability, analyst trust, and auditability**, not blind automation.

## Key Features

- **Explainable AI**: Every decision is backed by SHAP feature importance analysis
- **Human-Readable Explanations**: OpenAI GPT-4 translates technical XAI output into SOC analyst language
- **Transparent Pipeline**: Full visibility from alert ingestion to final verdict
- **Audit-Ready**: All decisions include evidence and reasoning suitable for compliance
- **Analyst-in-the-Loop**: System supports analysts, doesn't replace them

## Architecture

The system uses a 6-layer architecture:

1. **Alert Ingestion Layer** - Accepts SOC alerts (CSV/JSON)
2. **Feature Engineering Layer** - Transforms raw alerts into ML-ready features
3. **ML Risk Classification Engine** - Random Forest classifier (Benign/Suspicious/Malicious)
4. **Explainable AI (XAI) Layer** - SHAP for feature importance
5. **LLM Explanation Engine** - OpenAI GPT-4 for human-readable explanations
6. **SOC Analyst Dashboard** - Web UI for viewing analysis results

## Technology Stack

- **Language**: Python 3.8+
- **ML Framework**: scikit-learn (Random Forest)
- **XAI**: SHAP
- **LLM**: OpenAI GPT-4
- **Web Framework**: FastAPI + HTML/CSS/JavaScript
- **Data**: Synthetic SOC alerts (10,000+ samples)

## Prerequisites

- Python 3.8 or higher
- OpenAI API key (for GPT-4)
- 4GB+ RAM recommended
- Modern web browser

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/mr-bala-kavi/ai-security-decision-explainer.git
cd ai-security-decision-explainer

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=your_api_key_here
```

**Important**: Get your OpenAI API key from [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)

### 3. Generate Synthetic Data

```bash
python scripts/generate_data.py
```

This generates 10,000 synthetic SOC alerts with realistic threat scenarios:
- 60% Benign (normal activity)
- 25% Suspicious (potentially risky)
- 15% Malicious (confirmed threats)

### 4. Train the ML Model

```bash
python scripts/train_model.py
```

This trains a Random Forest classifier with:
- Hyperparameter tuning via GridSearchCV
- SHAP-compatible architecture
- Target: >85% accuracy, >90% malicious recall

Training takes 5-10 minutes depending on your hardware.

### 5. Run the Dashboard

```bash
python scripts/run_dashboard.py
```

The dashboard will be available at: **http://127.0.0.1:8000**

API documentation (Swagger UI): **http://127.0.0.1:8000/docs**

## Usage Guide

### Dashboard Workflow

1. **Select Alert**: Choose an alert from the dropdown menu
2. **Analyze**: Click "Analyze Alert" button
3. **Review Results**:
   - **Verdict**: Benign, Suspicious, or Malicious with confidence score
   - **Explanation**: Human-readable analysis from GPT-4
   - **Evidence**: SHAP feature importance chart showing why the decision was made
   - **Recommendation**: Suggested action for SOC analysts

### Understanding the Results

**Verdict Colors**:
- Green (Benign): No action required
- Yellow (Suspicious): Monitor closely
- Red (Malicious): Investigate immediately

**Confidence Score**: Higher confidence means more certain prediction (aim for >70%)

**Feature Importance**: Shows which alert characteristics most influenced the decision:
- Red bars = Increases risk
- Green bars = Decreases risk

**Recommended Actions**:
- `Investigate Immediately`: Malicious alerts with high confidence
- `Monitor Closely`: Suspicious alerts
- `Mark False Positive`: Benign alerts with high confidence

## Project Structure

```
ai-security-decision-explainer/
├── config/                      # Configuration
│   ├── settings.py             # Centralized settings
│   └── logging_config.py       # Logging configuration
├── data/                        # Data storage
│   ├── raw/                    # Synthetic alerts
│   ├── processed/              # Engineered features
│   └── models/                 # Trained models
├── src/                         # Source code
│   ├── 01_ingestion/           # Alert generation & loading
│   ├── 02_feature_engineering/ # Feature extraction
│   ├── 03_ml_engine/           # ML training & prediction
│   ├── 04_xai/                 # SHAP explainer
│   ├── 05_llm_engine/          # OpenAI API integration
│   └── 06_dashboard/           # FastAPI dashboard
├── scripts/                     # Utility scripts
│   ├── generate_data.py        # Generate synthetic data
│   ├── train_model.py          # Train ML model
│   └── run_dashboard.py        # Run dashboard server
├── tests/                       # Unit tests
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
└── README.md                   # This file
```

## API Endpoints

The dashboard provides RESTful API endpoints:

- `GET /` - Main dashboard UI
- `GET /api/alerts` - List available alerts
- `POST /api/analyze` - Analyze a specific alert
- `GET /api/metrics` - Get model performance metrics
- `GET /api/status` - System health check
- `GET /health` - Simple health endpoint

See full API documentation at `/docs` when running the server.

## Performance Metrics

Target performance for the ML model:

- **Overall Accuracy**: >85%
- **Malicious Recall**: >90% (critical - can't miss real threats)
- **Benign Precision**: >80% (reduce false alarms)
- **API Response Time**: <2 seconds for full pipeline

## Design Principles

1. **Explainability over raw accuracy** - Every decision must be defensible
2. **Analyst-in-the-loop always** - System assists, doesn't replace
3. **No automatic incident response** - Humans make final decisions
4. **Audit-ready decisions** - Suitable for compliance reports
5. **SOC-first design** - Built for security operations, not demos

## Troubleshooting

### Common Issues

**1. Model Not Found Error**
- Solution: Run `python scripts/train_model.py` first

**2. Alerts CSV Not Found**
- Solution: Run `python scripts/generate_data.py` first

**3. OpenAI API Error**
- Solution: Check `.env` file has valid `OPENAI_API_KEY`
- Check your API key at https://platform.openai.com/api-keys

**4. Import Errors**
- Solution: Make sure you're in the virtual environment
- Try: `pip install -r requirements.txt --upgrade`

**5. Port Already in Use**
- Solution: Change `DASHBOARD_PORT` in `.env` file

### Logs

Logs are stored in `logs/` directory:
- `logs/app.log` - All application logs
- `logs/errors.log` - Error logs only

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Adding New Features

The modular architecture makes it easy to extend:

- **New Data Sources**: Add to `src/01_ingestion/`
- **New Features**: Extend `FeatureExtractor` in `src/02_feature_engineering/`
- **Different ML Models**: Replace in `src/03_ml_engine/`
- **Additional XAI Methods**: Add to `src/04_xai/`

## Future Enhancements

Short-term:
- Analyst feedback loop for model retraining
- Batch processing for multiple alerts
- PDF report generation
- Alert prioritization queue

Long-term:
- Real SIEM integration (Splunk/ELK/Sentinel)
- SOAR workflow automation
- Multi-model ensemble
- Advanced counterfactual explanations

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License.

It is intended for:
- Defensive security research
- SOC analysis and alert explainability
- AI transparency and trust building
- Educational and enterprise use

The software is provided "as is", without warranty of any kind.
See the LICENSE file for details.


## Acknowledgments

- Built with OpenAI's GPT-4 API
- SHAP library by Scott Lundberg
- Inspired by the need for transparent AI in security operations

---

**Note**: This system uses synthetic data for demonstration. For production use with real SOC alerts, ensure compliance with your organization's data handling policies and security requirements.
