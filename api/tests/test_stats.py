"""Unit tests for statistical analysis modules."""

import pytest
from app.analysis.stats import (
    period_over_period_comparison,
    detect_anomalies,
    forecast_metric,
)


def test_period_over_period_comparison():
    rows = [
        {"qtr": "2024-Q1", "revenue": 100000, "category": "Electronics"},
        {"qtr": "2024-Q1", "revenue": 50000, "category": "Apparel"},
        {"qtr": "2024-Q2", "revenue": 40000, "category": "Electronics"},
        {"qtr": "2024-Q2", "revenue": 35000, "category": "Apparel"},
    ]
    res = period_over_period_comparison(
        rows=rows,
        period_col="qtr",
        metric_col="revenue",
        dimension_col="category"
    )
    assert res["direction"] == "decrease"
    assert res["prior_value"] == 150000.0
    assert res["current_value"] == 75000.0
    assert res["percentage_change"] == -50.0
    assert len(res["dimensional_attribution"]) == 2
    # Electronics dropped from 100k to 40k (-60k), so it should be the top contributor
    assert res["dimensional_attribution"][0]["dimension"] == "Electronics"


def test_detect_anomalies_finds_spike_and_drop():
    # Normal data around 100, with one huge outlier 500
    values = [100.0, 102.0, 98.0, 105.0, 99.0, 101.0, 103.0, 500.0]
    res = detect_anomalies(values)
    assert res["anomalies_detected"] is True
    assert 500.0 in res["anomalous_values"]


def test_forecast_metric():
    dates = ["2024-01-01", "2024-02-01", "2024-03-01", "2024-04-01"]
    values = [100.0, 110.0, 120.0, 130.0]
    res = forecast_metric(dates, values, forecast_periods=2)
    assert res["forecast_periods"] == 2
    assert len(res["forecast_values"]) == 2
    # The trend is increasing, so forecasted values should be >= 130
    assert res["forecast_values"][0] >= 125.0
