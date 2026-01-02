// AI Security Decision Explainer - Dashboard JavaScript

let featureChart = null;

// Load alerts on page load
document.addEventListener('DOMContentLoaded', function() {
    loadAlerts();
    setupEventListeners();
});

function setupEventListeners() {
    document.getElementById('analyzeBtn').addEventListener('click', analyzeAlert);
    document.getElementById('toggleDetails').addEventListener('click', toggleDetails);
}

async function loadAlerts() {
    try {
        const response = await fetch('/api/alerts');
        const data = await response.json();

        if (data.success) {
            const select = document.getElementById('alertSelect');
            select.innerHTML = '<option value="">-- Select an alert --</option>';

            data.alerts.forEach(alert => {
                const option = document.createElement('option');
                option.value = alert.alert_id;
                option.textContent = `${alert.timestamp} - ${alert.source_ip} → ${alert.destination_ip} (${alert.true_label})`;
                select.appendChild(option);
            });

            select.addEventListener('change', function() {
                document.getElementById('analyzeBtn').disabled = !this.value;
            });
        }
    } catch (error) {
        console.error('Error loading alerts:', error);
        alert('Failed to load alerts. Please check if the server is running.');
    }
}

async function analyzeAlert() {
    const alertId = document.getElementById('alertSelect').value;
    if (!alertId) return;

    // Show loading
    document.getElementById('loadingSpinner').style.display = 'inline';
    document.getElementById('analyzeBtn').disabled = true;
    document.getElementById('resultsPanel').style.display = 'none';

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ alert_id: alertId })
        });

        const data = await response.json();

        if (data.success) {
            displayResults(data);
        } else {
            alert('Analysis failed: ' + (data.detail || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error analyzing alert:', error);
        alert('Failed to analyze alert. Error: ' + error.message);
    } finally {
        document.getElementById('loadingSpinner').style.display = 'none';
        document.getElementById('analyzeBtn').disabled = false;
    }
}

function displayResults(data) {
    // Show results panel
    document.getElementById('resultsPanel').style.display = 'block';

    // Alert Overview
    document.getElementById('alertId').textContent = data.alert.alert_id;
    document.getElementById('alertTimestamp').textContent = data.alert.timestamp;
    document.getElementById('sourceIp').textContent = data.alert.source_ip;
    document.getElementById('sourceCountry').textContent = data.alert.source_country;
    document.getElementById('destination').textContent = `${data.alert.destination_ip}:${data.alert.destination_port}`;
    document.getElementById('protocol').textContent = data.alert.protocol;

    // Verdict
    const verdict = data.prediction.verdict;
    const confidence = data.prediction.confidence;

    const verdictBadge = document.getElementById('verdictBadge');
    verdictBadge.textContent = verdict.toUpperCase();
    verdictBadge.className = 'verdict-badge verdict-' + verdict;

    // Confidence
    document.getElementById('confidenceLevel').style.width = (confidence * 100) + '%';
    document.getElementById('confidenceText').textContent = (confidence * 100).toFixed(1) + '%';

    // Probabilities
    document.getElementById('probBenign').textContent = (data.prediction.probabilities.benign * 100).toFixed(1) + '%';
    document.getElementById('probSuspicious').textContent = (data.prediction.probabilities.suspicious * 100).toFixed(1) + '%';
    document.getElementById('probMalicious').textContent = (data.prediction.probabilities.malicious * 100).toFixed(1) + '%';

    // Explanation
    document.getElementById('explanationText').textContent = data.explanation.text;
    document.getElementById('recommendedAction').textContent = formatAction(data.explanation.recommended_action);

    // Feature Importance Chart
    renderFeatureChart(data.xai.top_features);

    // Detailed features table
    populateDetailsTable(data.xai.top_features);

    // True label
    const trueLabelBadge = document.getElementById('trueLabel');
    trueLabelBadge.textContent = data.alert.true_label.toUpperCase();
    trueLabelBadge.className = 'true-label-badge verdict-' + data.alert.true_label;

    // Scroll to results
    document.getElementById('resultsPanel').scrollIntoView({ behavior: 'smooth' });
}

function renderFeatureChart(features) {
    const ctx = document.getElementById('featureChart').getContext('2d');

    // Destroy existing chart if any
    if (featureChart) {
        featureChart.destroy();
    }

    // Take top 10 features
    const topFeatures = features.slice(0, 10);

    const labels = topFeatures.map(f => f.human_readable_name);
    const values = topFeatures.map(f => Math.abs(f.impact_score));
    const colors = topFeatures.map(f =>
        f.direction === 'increases_risk' ? 'rgba(220, 53, 69, 0.7)' : 'rgba(40, 167, 69, 0.7)'
    );

    featureChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Impact Score',
                data: values,
                backgroundColor: colors,
                borderColor: colors.map(c => c.replace('0.7', '1')),
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                x: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Absolute Impact Score'
                    }
                },
                y: {
                    ticks: {
                        autoSkip: false
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const feature = topFeatures[context.dataIndex];
                            return [
                                `Impact: ${feature.impact_score.toFixed(4)}`,
                                `Direction: ${feature.direction.replace('_', ' ')}`,
                                `Contribution: ${feature.contribution_percentage.toFixed(1)}%`
                            ];
                        }
                    }
                }
            }
        }
    });
}

function populateDetailsTable(features) {
    const tbody = document.getElementById('detailsTableBody');
    tbody.innerHTML = '';

    features.forEach(feature => {
        const row = tbody.insertRow();

        const cellName = row.insertCell(0);
        cellName.textContent = feature.human_readable_name;

        const cellValue = row.insertCell(1);
        cellValue.textContent = formatFeatureValue(feature.feature_value);

        const cellImpact = row.insertCell(2);
        cellImpact.textContent = feature.impact_score.toFixed(4);
        cellImpact.className = feature.direction === 'increases_risk' ? 'impact-positive' : 'impact-negative';

        const cellContribution = row.insertCell(3);
        cellContribution.textContent = feature.contribution_percentage.toFixed(1) + '%';
    });
}

function formatFeatureValue(value) {
    if (typeof value === 'boolean') {
        return value ? 'Yes' : 'No';
    } else if (typeof value === 'number') {
        return value.toFixed(2);
    } else {
        return value;
    }
}

function formatAction(action) {
    return action.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function toggleDetails() {
    const detailsTable = document.getElementById('detailsTable');
    const toggleBtn = document.getElementById('toggleDetails');

    if (detailsTable.style.display === 'none') {
        detailsTable.style.display = 'block';
        toggleBtn.textContent = 'Hide Details';
    } else {
        detailsTable.style.display = 'none';
        toggleBtn.textContent = 'Show All Details';
    }
}
