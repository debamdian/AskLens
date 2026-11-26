"""Senior Analyst Planner Agent.

Decomposes diagnostic "why" questions into systematic hypothesis testing steps:
1. Baseline & Comparison Period delta extraction
2. Multi-dimensional slicing (Region, Product Category, Channel, Segment)
3. Pareto contribution ranking (which driver explains >70% of the shift)
4. Anomaly detection & external correlation (marketing spend, return rates, inventory stockouts)
5. Root-cause hypothesis test
"""

import json
from typing import Dict, Any, List, Optional
from app.llm.factory import llm_service
from app.analysis.stats import period_over_period_comparison, detect_anomalies


PLANNER_DECOMPOSITION_PROMPT = """You are a Principal Data Analyst.
Decompose the user's diagnostic question into a structured, multi-step analysis plan.

USER QUESTION:
{question}

Formulate a 4-step hypothesis testing plan:
1. Baseline vs Comparison period measurement (e.g. QoQ or YoY delta).
2. Dimensional breakdown (Region, Category, Channel).
3. Driver & anomaly identification (e.g., marketing budget changes, stockouts, return spikes).
4. Root cause synthesis.

Output as JSON array of step descriptions:
["Step 1: ...", "Step 2: ...", "Step 3: ...", "Step 4: ..."]
"""


class SeniorAnalystPlanner:
    """Plans and decomposes multi-dimensional diagnostic questions."""

    def __init__(self, llm=None):
        self.llm = llm or llm_service

    def plan_analysis(self, question: str, use_llm: bool = False) -> List[str]:
        """Generates analysis steps for a diagnostic question."""
        if use_llm:
            prompt = PLANNER_DECOMPOSITION_PROMPT.format(question=question)
            try:
                res = self.llm.generate(prompt=prompt, temperature=0.0)
                import re
                json_match = re.search(r"\[[\s\S]*\]", res)
                if json_match:
                    steps = json.loads(json_match.group(0))
                    if isinstance(steps, list) and len(steps) > 0:
                        return [str(s) for s in steps]
            except Exception:
                pass

        # Fast deterministic diagnostic decomposition (<1ms)
        return [
            f"Establish baseline & comparison periods for: '{question}'",
            "Perform dimensional breakdown across regions, product categories, and channels",
            "Examine external drivers: marketing spend shifts, stockouts, and return rate spikes",
            "Quantify driver contribution and synthesize evidence-backed root cause"
        ]


# Global instance
senior_planner = SeniorAnalystPlanner()
