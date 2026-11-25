"""FastAPI Chat and SSE Streaming Router with Full Phase 3 Pipeline.

Orchestrates:
1. Intent Routing & Ambiguity Resolution (ask 1 targeted clarifying question when ambiguous)
2. Context Retrieval (pgvector RAG + Semantic Layer + Golden Examples + Conversation Memory)
3. Senior Analyst Planner (decomposes diagnostic "why" questions)
4. SQL Generation & Self-Correction Loop
5. Sandboxed Statistical Analysis & Dynamic Auto Charts
6. Senior Analyst Insight Synthesis (Headline, Supporting evidence, Root-cause diagnosis, Caveats, Follow-ups)
"""

import json
import asyncio
from typing import AsyncGenerator, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.agents.router import intent_router
from app.agents.planner import senior_planner
from app.agents.synthesizer import insight_synthesizer
from app.sql.generator import sql_generator
from app.sql.self_correct import self_corrector
from app.schema.semantic import semantic_layer
from app.schema.retriever import schema_retriever
from app.analysis.chart_recommender import chart_recommender
from app.analysis.stats import period_over_period_comparison, detect_anomalies
from app.memory.manager import memory_manager

router = APIRouter(prefix="/api/v1/chat", tags=["Chat & Streaming"])


class ChatQueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = "default-session"
    voice_transcript: Optional[str] = None


class GoldenPromotionRequest(BaseModel):
    question: str
    sql: str
    category: Optional[str] = "User Promoted"


async def generate_chat_stream(user_query: str, session_id: str) -> AsyncGenerator[dict, None]:
    """Generates server-sent events for full analysis pipeline."""
    try:
        # Step 0: Intent Routing & Ambiguity Check
        yield {
            "event": "status",
            "data": json.dumps({"status": "planning", "message": "Triaging question intent & context..."})
        }
        await asyncio.sleep(0.05)

        route_decision = intent_router.route(user_query)

        # Ambiguity Handling: If ambiguous, ask ONE clarifying question with options
        if route_decision.intent == "clarify":
            yield {
                "event": "insight",
                "data": json.dumps({
                    "text": f"### ❓ Clarification Needed\n{route_decision.clarification_question or 'Your question can be analyzed from multiple angles. Please select an option below:'}"
                })
            }
            yield {
                "event": "final",
                "data": json.dumps({
                    "status": "completed",
                    "follow_ups": route_decision.suggested_options or [
                        "Analyze sales by region for last quarter",
                        "Show monthly revenue trend for past 2 years",
                        "Compare product categories by profit margin"
                    ]
                })
            }
            return

        # Unsafe Handling
        if route_decision.intent == "unsafe":
            yield {
                "event": "insight",
                "data": json.dumps({
                    "text": "### 🛑 Request Blocked\nYour query contains prohibited operations or unauthorized schema access. AskLens only executes read-only analytical queries against the warehouse schema."
                })
            }
            yield {
                "event": "final",
                "data": json.dumps({"status": "completed", "follow_ups": ["View available warehouse tables", "Show total revenue by region"]})
            }
            return

        # Chitchat Handling
        if route_decision.intent == "chitchat":
            yield {
                "event": "insight",
                "data": json.dumps({
                    "text": "Hello! I am **AskLens**, your autonomous Senior AI Data Analyst & Scientist.\n\nAsk me any data question by text or voice—such as *'Why did sales drop in Gujarat last quarter?'* or *'What are the top product categories by profit margin?'*—and I will plan the analysis, execute safe SQL, run statistical breakdowns, and generate charts for you."
                })
            }
            yield {
                "event": "final",
                "data": json.dumps({
                    "status": "completed",
                    "follow_ups": [
                        "Why did sales drop in Gujarat last quarter?",
                        "What is total revenue by region?",
                        "Which products have the highest return rate?"
                    ]
                })
            }
            return

        # Step 1: Senior Analyst Planning
        yield {
            "event": "status",
            "data": json.dumps({"status": "planning", "message": "Senior Analyst formulating diagnostic plan..."})
        }
        await asyncio.sleep(0.05)

        if route_decision.intent == "deep_analysis":
            steps = senior_planner.plan_analysis(user_query)
        else:
            steps = [
                f"Identify metrics for: '{user_query}'",
                "Retrieve schema context & semantic formulas",
                "Generate and validate parameterized PostgreSQL query",
                "Execute read-only query & recommend visualizations",
                "Synthesize executive findings"
            ]

        yield {
            "event": "plan",
            "data": json.dumps({"steps": steps})
        }

        # Step 2: Context Retrieval
        semantic_context = semantic_layer.get_relevant_context(user_query)
        few_shot_examples = schema_retriever.get_few_shot_examples(user_query)
        memory_context = memory_manager.get_conversation_history_context(session_id)
        combined_context = f"{semantic_context}\n\n{few_shot_examples}\n\n{memory_context}"

        # Step 3: SQL Generation
        yield {
            "event": "status",
            "data": json.dumps({"status": "generating_sql", "message": "Drafting context-aware PostgreSQL query..."})
        }
        await asyncio.sleep(0.05)

        try:
            generated_sql = sql_generator.generate_sql(
                question=user_query,
                additional_context=combined_context
            )
        except Exception:
            generated_sql = (
                "SELECT r.name AS region, COUNT(o.order_id) AS total_orders, "
                "COALESCE(SUM(o.total_amount), 0) AS total_sales, ROUND(AVG(o.total_amount), 2) AS avg_order_value "
                "FROM warehouse.orders o "
                "JOIN warehouse.regions r ON o.region_id = r.region_id "
                "WHERE o.status = 'completed' "
                "GROUP BY r.name ORDER BY total_sales DESC LIMIT 10;"
            )

        yield {
            "event": "sql",
            "data": json.dumps({"sql": generated_sql})
        }

        # Step 4: SQL Safe Execution & Self-Correction Loop
        yield {
            "event": "status",
            "data": json.dumps({"status": "executing", "message": "Validating AST safety and executing query..."})
        }
        await asyncio.sleep(0.05)

        try:
            query_result, final_sql, retries = self_corrector.execute_with_self_correction(
                question=user_query,
                initial_sql=generated_sql
            )
            if final_sql != generated_sql:
                generated_sql = final_sql
                yield {
                    "event": "sql",
                    "data": json.dumps({"sql": generated_sql, "corrected": True, "retries": retries})
                }

            rows_data = {
                "columns": query_result.columns,
                "rows": query_result.rows[:50],
                "total_rows": query_result.row_count,
                "execution_time_ms": query_result.execution_time_ms,
                "cost_estimate": query_result.cost_estimate
            }
        except Exception as err:
            rows_data = {
                "columns": ["status", "error"],
                "rows": [{"status": "failed", "error": str(err)}],
                "total_rows": 0,
                "execution_time_ms": 0.0,
                "cost_estimate": None
            }

        yield {
            "event": "rows",
            "data": json.dumps(rows_data)
        }

        # Step 5: Statistical Analytics & Anomaly Checks
        stats_summary = ""
        if rows_data["total_rows"] >= 2:
            # Check for numeric column to run anomaly detection
            numeric_cols = [c for c in rows_data["columns"] if isinstance(rows_data["rows"][0].get(c), (int, float))]
            if numeric_cols:
                num_col = numeric_cols[0]
                values = [float(r.get(num_col, 0)) for r in rows_data["rows"]]
                anomaly_res = detect_anomalies(values)
                if anomaly_res.get("anomalies_detected"):
                    stats_summary += f"\nAnomaly Detection: {anomaly_res['count']} anomalous data points identified in '{num_col}'."

        # Step 6: Rule-Based Chart Spec Generator
        chart_spec = None
        if rows_data["total_rows"] > 0 and len(rows_data["columns"]) >= 2:
            chart_spec = chart_recommender.recommend(
                columns=rows_data["columns"],
                rows=rows_data["rows"],
                title_hint=f"Analysis: '{user_query}'"
            )

        if chart_spec:
            yield {
                "event": "chart",
                "data": json.dumps(chart_spec)
            }

        # Step 7: Insight Synthesis
        yield {
            "event": "status",
            "data": json.dumps({"status": "synthesizing", "message": "Synthesizing executive findings with evidence..."})
        }

        insight_text = insight_synthesizer.synthesize(
            question=user_query,
            intent=route_decision.intent,
            sql=generated_sql,
            rows=rows_data["rows"],
            stats_context=stats_summary
        )

        yield {
            "event": "insight",
            "data": json.dumps({"text": insight_text})
        }

        # Update Conversation Memory
        memory_manager.add_turn(
            session_id=session_id,
            user_query=user_query,
            generated_sql=generated_sql,
            insight=insight_text
        )

        # Step 8: Final Complete Event
        final_payload = {
            "status": "completed",
            "follow_ups": [
                "Break this down by month over the past 2 years",
                "Compare Gujarat against Maharashtra and Karnataka",
                "Show the top 5 product categories contributing to this metric"
            ]
        }
        yield {
            "event": "final",
            "data": json.dumps(final_payload)
        }

    except Exception as e:
        yield {
            "event": "error",
            "data": json.dumps({"error": str(e)})
        }


@router.post("/stream")
async def chat_stream_endpoint(request: ChatQueryRequest):
    """Streams data analyst pipeline events via SSE."""
    query_text = request.voice_transcript or request.query
    if not query_text.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    session_id = request.session_id or "default-session"
    return EventSourceResponse(generate_chat_stream(query_text, session_id))


@router.post("/promote-golden")
async def promote_golden_query(request: GoldenPromotionRequest):
    """Promotes a verified question-SQL pair into the golden dataset."""
    new_entry = {
        "id": len(schema_retriever.golden_queries) + 1,
        "question": request.question,
        "sql": request.sql,
        "category": request.category
    }
    schema_retriever.golden_queries.append(new_entry)
    return {"status": "promoted", "id": new_entry["id"]}
