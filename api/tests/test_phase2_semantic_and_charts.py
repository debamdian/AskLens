"""Unit tests for Phase 2: Semantic Layer, Chart Recommender, and Conversation Memory."""

import pytest
from app.schema.semantic import SemanticLayer
from app.schema.retriever import SchemaRetriever
from app.analysis.chart_recommender import ChartRecommender
from app.memory.manager import ConversationMemoryManager


# ==============================================================================
# 1. Semantic Layer Tests
# ==============================================================================

def test_semantic_layer_keyword_matching():
    semantic = SemanticLayer()
    context = semantic.get_relevant_context("What is the total revenue in Gujarat?")
    assert "Total Revenue" in context
    assert "COALESCE(SUM(o.total_amount), 0)" in context
    assert "o.status = 'completed'" in context


def test_semantic_layer_returns_metric():
    semantic = SemanticLayer()
    context = semantic.get_relevant_context("Show me the return rate by category")
    assert "Return Rate" in context
    assert "COUNT(DISTINCT r.order_id)" in context


# ==============================================================================
# 2. Golden Query Few-Shot Tests
# ==============================================================================

def test_golden_query_retrieval():
    retriever = SchemaRetriever()
    examples = retriever.get_few_shot_examples("Why did sales drop in Gujarat?")
    assert "Gujarat" in examples
    assert "SELECT" in examples


# ==============================================================================
# 3. Chart Recommender Tests
# ==============================================================================

def test_chart_recommender_time_series():
    recommender = ChartRecommender()
    cols = ["order_date", "total_sales"]
    rows = [
        {"order_date": "2024-01-01", "total_sales": 150000},
        {"order_date": "2024-02-01", "total_sales": 180000},
        {"order_date": "2024-03-01", "total_sales": 165000}
    ]
    spec = recommender.recommend(cols, rows)
    assert spec is not None
    assert spec["chart_type"] == "line"
    assert spec["xAxis"]["data"] == ["2024-01-01", "2024-02-01", "2024-03-01"]


def test_chart_recommender_small_distribution_pie():
    recommender = ChartRecommender()
    cols = ["category", "sales"]
    rows = [
        {"category": "Electronics", "sales": 50000},
        {"category": "Apparel", "sales": 30000},
        {"category": "Fitness", "sales": 20000}
    ]
    spec = recommender.recommend(cols, rows)
    assert spec is not None
    assert spec["chart_type"] == "pie"
    assert len(spec["series"][0]["data"]) == 3


def test_chart_recommender_large_comparison_bar():
    recommender = ChartRecommender()
    cols = ["region", "revenue"]
    rows = [
        {"region": f"Region {i}", "revenue": 1000 * i} for i in range(10)
    ]
    spec = recommender.recommend(cols, rows)
    assert spec is not None
    assert spec["chart_type"] == "bar"


# ==============================================================================
# 4. Conversation Memory Tests
# ==============================================================================

def test_conversation_memory_follow_up():
    memory = ConversationMemoryManager()
    session_id = "test-session-123"

    memory.add_turn(
        session_id=session_id,
        user_query="What was Gujarat sales last quarter?",
        generated_sql="SELECT SUM(total_amount) FROM warehouse.orders WHERE region_id = 1;"
    )

    context = memory.get_conversation_history_context(session_id)
    assert "Gujarat sales" in context
    assert "SELECT SUM(total_amount)" in context
    assert "modify or extend the previous SQL" in context
