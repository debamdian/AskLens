"""Schema and Golden Query RAG Retriever.

Dynamically selects the top-k relevant tables and few-shot golden examples
to craft minimal, high-precision prompts for the SQL generator.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
import re

GOLDEN_YAML_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "golden_queries.yaml"


class SchemaRetriever:
    """Retrieves relevant schema fragments and golden query examples."""

    def __init__(self, golden_path: Optional[Path] = None):
        self.golden_path = golden_path or GOLDEN_YAML_PATH
        self.golden_queries: List[Dict[str, Any]] = []
        self._load_golden()

    def _load_golden(self):
        if not self.golden_path.exists():
            return
        with open(self.golden_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            self.golden_queries = data.get("golden_queries", [])

    def get_few_shot_examples(self, question: str, max_examples: int = 2) -> str:
        """Finds most relevant golden query examples based on query terms."""
        if not self.golden_queries:
            return ""

        q_tokens = set(re.findall(r"\w+", question.lower()))

        scored = []
        for g in self.golden_queries:
            g_tokens = set(re.findall(r"\w+", g.get("question", "").lower()))
            overlap = len(q_tokens.intersection(g_tokens))
            scored.append((overlap, g))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = [item[1] for item in scored[:max_examples]]

        lines = ["Verified Example Question & SQL Pairs:"]
        for ex in top:
            lines.append(f"Question: {ex.get('question')}")
            lines.append(f"SQL:\n{ex.get('sql').strip()}\n")

        return "\n".join(lines)


# Global instance
schema_retriever = SchemaRetriever()
