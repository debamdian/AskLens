"""Statistical and Predictive Analytics Modules.

Provides:
- Period-over-Period (PoP) comparison and growth attribution
- Anomaly detection via Z-Score and Interquartile Range (IQR)
- Time-series forecasting (with statsmodels Holt-Winters / linear extrapolation fallback)
- Correlation matrix analysis
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd


def period_over_period_comparison(
    rows: List[Dict[str, Any]],
    period_col: str,
    metric_col: str,
    dimension_col: Optional[str] = None
) -> Dict[str, Any]:
    """Computes comparison between consecutive periods with dimensional attribution."""
    if not rows:
        return {"error": "No data available for period comparison"}

    df = pd.DataFrame(rows)
    if period_col not in df.columns or metric_col not in df.columns:
        return {"error": f"Required columns '{period_col}' or '{metric_col}' not found"}

    df[metric_col] = pd.to_numeric(df[metric_col], errors="coerce").fillna(0)
    periods = sorted(df[period_col].unique())

    if len(periods) < 2:
        return {"error": "Need at least two distinct periods to compute comparison"}

    prior_period = periods[-2]
    current_period = periods[-1]

    prior_val = float(df[df[period_col] == prior_period][metric_col].sum())
    current_val = float(df[df[period_col] == current_period][metric_col].sum())

    delta = current_val - prior_val
    pct_change = round((delta / prior_val * 100), 2) if prior_val != 0 else 0.0

    result: Dict[str, Any] = {
        "prior_period": str(prior_period),
        "current_period": str(current_period),
        "prior_value": prior_val,
        "current_value": current_val,
        "absolute_change": delta,
        "percentage_change": pct_change,
        "direction": "decrease" if delta < 0 else "increase"
    }

    # Dimensional attribution if dimension column (e.g. category) is provided
    if dimension_col and dimension_col in df.columns:
        attribution = []
        dims = df[dimension_col].unique()
        for d in dims:
            p_v = float(df[(df[period_col] == prior_period) & (df[dimension_col] == d)][metric_col].sum())
            c_v = float(df[(df[period_col] == current_period) & (df[dimension_col] == d)][metric_col].sum())
            dim_delta = c_v - p_v
            # Share of overall delta
            share = round((dim_delta / delta * 100), 2) if delta != 0 else 0.0
            attribution.append({
                "dimension": str(d),
                "prior": p_v,
                "current": c_v,
                "delta": dim_delta,
                "contribution_pct": share
            })

        attribution.sort(key=lambda x: abs(x["delta"]), reverse=True)
        result["dimensional_attribution"] = attribution

    return result


def detect_anomalies(
    values: List[float],
    z_threshold: float = 2.0
) -> Dict[str, Any]:
    """Identifies outliers using both parametric Z-Score and non-parametric IQR."""
    if len(values) < 4:
        return {"anomalies_detected": False, "count": 0, "indices": []}

    arr = np.array(values, dtype=float)
    mean = np.mean(arr)
    std = np.std(arr)

    # 1. Z-Score
    z_scores = np.abs((arr - mean) / std) if std > 0 else np.zeros_like(arr)
    z_anomalies = np.where(z_scores > z_threshold)[0].tolist()

    # 2. Interquartile Range (IQR)
    q25, q75 = np.percentile(arr, 25), np.percentile(arr, 75)
    iqr = q75 - q25
    lower_bound = q25 - (1.5 * iqr)
    upper_bound = q75 + (1.5 * iqr)
    iqr_anomalies = np.where((arr < lower_bound) | (arr > upper_bound))[0].tolist()

    # Combined indices
    all_anomalies = sorted(list(set(z_anomalies + iqr_anomalies)))

    return {
        "anomalies_detected": len(all_anomalies) > 0,
        "count": len(all_anomalies),
        "indices": all_anomalies,
        "iqr_bounds": {"lower": round(lower_bound, 2), "upper": round(upper_bound, 2)},
        "anomalous_values": [float(arr[i]) for i in all_anomalies]
    }


def forecast_metric(
    historical_dates: List[str],
    historical_values: List[float],
    forecast_periods: int = 3
) -> Dict[str, Any]:
    """Generates future projections using exponential smoothing or linear trend."""
    if len(historical_values) < 3:
        return {"error": "Need at least 3 historical points for forecasting"}

    try:
        from statsmodels.tsa.holtwinters import SimpleExpSmoothing
        series = pd.Series(historical_values)
        model = SimpleExpSmoothing(series, initialization_method="estimated").fit()
        forecast = model.forecast(forecast_periods).tolist()
    except Exception:
        # Robust linear trend fallback
        x = np.arange(len(historical_values))
        y = np.array(historical_values)
        slope, intercept = np.polyfit(x, y, 1)
        future_x = np.arange(len(historical_values), len(historical_values) + forecast_periods)
        forecast = (slope * future_x + intercept).tolist()

    return {
        "historical_count": len(historical_values),
        "forecast_periods": forecast_periods,
        "forecast_values": [round(float(v), 2) for v in forecast]
    }
