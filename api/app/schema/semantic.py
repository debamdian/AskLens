"""Semantic Layer Manager.

Loads semantic definitions and injects only the definitions relevant to a specific user question.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from app.core.config import settings

SEMANTIC_YAML_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "semantic_layer.yaml"


class SemanticLayer:
    """Manages business glossary metrics and dimension mappings."""

    def __init__(self, yaml_path: Optional[Path] = None):
        self.yaml_path = yaml_path or SEMANTIC_YAML_PATH
        self.metrics: Dict[str, Any] = {}
        self.dimensions: Dict[str, Any] = {}
        self._load()

    def _load(self):
        if not self.yaml_path.exists():
            return
        with open(self.yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            self.metrics = data.get("metrics", {})
            self.dimensions = data.get("dimensions", {})

    def get_relevant_context(self, question: str) -> str:
        """Finds metrics matching words in the user question and returns minimal context."""
        q_lower = question.lower()
        matched_metrics = []

        for key, metric in self.metrics.items():
            keywords = metric.get("keywords", [key])
            if any(kw in q_lower for kw in keywords):
                matched_metrics.append(metric)

        if not matched_metrics:
            # If no direct keyword matched, return top 2 primary metrics (revenue, orders)
            matched_metrics = [
                self.metrics.get("revenue", {}),
                self.metrics.get("order_count", {})
            ]

        lines = ["Business Metrics Glossary (Use these exact formula expressions):"]
        for m in matched_metrics:
            if not m:
                continue
            lines.append(f"- {m.get('name')}:")
            lines.append(f"    Formula: {m.get('sql_expression')}")
            if m.get("filters"):
                lines.append(f"    Mandatory Filter: {m.get('filters')}")
            if m.get("tables"):
                lines.append(f"    Tables: {', '.join(m.get('tables'))}")

        return "\n".join(lines)


# Global instance
semantic_layer = SemanticLayer()
