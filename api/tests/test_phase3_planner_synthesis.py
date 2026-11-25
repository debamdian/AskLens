"""Unit tests for Phase 3: Senior Analyst Planner and Insight Synthesis."""

import pytest
from app.agents.planner import SeniorAnalystPlanner
from app.agents.synthesizer import InsightSynthesizer
from app.agents.router import IntentRouter


def test_planner_decomposes_why_question():
    planner = SeniorAnalystPlanner()
    steps = planner.plan_analysis("Why did sales drop in Gujarat last quarter?")
    assert len(steps) >= 3
    assert any("Gujarat" in s or "baseline" in s.lower() or "breakdown" in s.lower() for s in steps)


def test_ambiguity_clarify_flow():
    router = IntentRouter()
    # Very vague query should trigger clarification or option choices
    decision = router.route("performance")
    assert decision.intent in ["clarify", "simple_query"]
    if decision.intent == "clarify":
        assert decision.clarification_question is not None


def test_insight_synthesizer_structure():
    synthesizer = InsightSynthesizer()
    rows = [
        {"category": "Electronics", "revenue_drop": -120000, "drop_pct": -68.5},
        {"category": "Apparel", "revenue_drop": -45000, "drop_pct": -42.1}
    ]
    summary = synthesizer.synthesize(
        question="Why did sales drop in Gujarat last quarter?",
        intent="deep_analysis",
        sql="SELECT ...",
        rows=rows
    )
    assert "Headline Finding" in summary
    assert "Key Supporting Evidence" in summary
    assert "Caveats & Confidence" in summary
