"""Rule-Based Chart Recommender Engine.

Analyzes query results (column names, types, cardinality, date patterns)
and emits a declarative chart specification (Bar, Line, Donut, Scatter).
"""

from typing import Any, Dict, List, Optional
import re


class ChartRecommender:
    """Selects the best visualization based on schema and data characteristics."""

    DATE_PATTERNS = ["date", "month", "year", "quarter", "qtr", "day", "week", "period", "timestamp"]

    def recommend(
        self,
        columns: List[str],
        rows: List[Dict[str, Any]],
        title_hint: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Analyzes result rows and returns a declarative ECharts spec."""
        if not rows or len(columns) < 2:
            return None

        # Categorize columns as numeric vs categorical vs temporal
        col_types = {}
        for col in columns:
            is_date = any(p in col.lower() for p in self.DATE_PATTERNS)
            if is_date:
                col_types[col] = "temporal"
                continue

            first_val = next((r[col] for r in rows if r.get(col) is not None), None)
            if isinstance(first_val, (int, float)):
                col_types[col] = "numeric"
            else:
                col_types[col] = "categorical"

        temporal_cols = [c for c, t in col_types.items() if t == "temporal"]
        numeric_cols = [c for c, t in col_types.items() if t == "numeric"]
        categorical_cols = [c for c, t in col_types.items() if t == "categorical"]

        title = title_hint or f"Analysis by {columns[0].replace('_', ' ').title()}"

        # Rule 1: Time Series Trend -> Line Chart
        if temporal_cols and numeric_cols:
            x_col = temporal_cols[0]
            series = []
            colors = ["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6"]

            for i, num_col in enumerate(numeric_cols[:3]):
                series.append({
                    "name": num_col.replace("_", " ").title(),
                    "type": "line",
                    "smooth": True,
                    "data": [r.get(num_col, 0) for r in rows],
                    "itemStyle": {"color": colors[i % len(colors)]}
                })

            return {
                "chart_type": "line",
                "title": title,
                "xAxis": {
                    "type": "category",
                    "data": [str(r.get(x_col, "")) for r in rows]
                },
                "yAxis": {"type": "value"},
                "series": series
            }

        # Rule 2: Small categorical distribution (<= 6 categories) -> Donut / Pie Chart
        if len(categorical_cols) == 1 and len(numeric_cols) >= 1 and 2 <= len(rows) <= 6:
            cat_col = categorical_cols[0]
            val_col = numeric_cols[0]
            return {
                "chart_type": "pie",
                "title": title,
                "series": [{
                    "name": val_col.replace("_", " ").title(),
                    "type": "pie",
                    "radius": ["40%", "70%"],
                    "data": [
                        {"name": str(r.get(cat_col, "Unknown")), "value": r.get(val_col, 0)}
                        for r in rows
                    ]
                }]
            }

        # Rule 3: Categorical Comparisons -> Bar Chart
        if (categorical_cols or temporal_cols) and numeric_cols:
            x_col = categorical_cols[0] if categorical_cols else temporal_cols[0]
            series = []
            colors = ["#3b82f6", "#6366f1", "#0ea5e9"]

            for i, num_col in enumerate(numeric_cols[:2]):
                series.append({
                    "name": num_col.replace("_", " ").title(),
                    "type": "bar",
                    "data": [r.get(num_col, 0) for r in rows[:15]],
                    "itemStyle": {"color": colors[i % len(colors)]}
                })

            return {
                "chart_type": "bar",
                "title": title,
                "xAxis": {
                    "type": "category",
                    "data": [str(r.get(x_col, "")) for r in rows[:15]]
                },
                "yAxis": {"type": "value"},
                "series": series
            }

        return None


# Global instance
chart_recommender = ChartRecommender()
