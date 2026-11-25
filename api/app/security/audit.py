"""Audit Logger for AskLens.

Records every analyst query, generated SQL, execution status, row count,
latency, and role into `app.audit_logs` (with an in-memory ring-buffer fallback
when PostgreSQL is unavailable).
"""

import asyncio
import logging
import uuid
from collections import deque
from datetime import datetime, timezone
from typing import Any, Deque, Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from app.core.config import settings

logger = logging.getLogger(__name__)


class AuditLogger:
    """Writes structured query audit logs to PostgreSQL and an in-memory buffer."""

    def __init__(self, max_memory_entries: int = 200):
        self._memory_logs: Deque[Dict[str, Any]] = deque(maxlen=max_memory_entries)

    def _write_sync(self, entry: Dict[str, Any]) -> None:
        """Synchronously insert an audit log row into app.audit_logs."""
        try:
            with psycopg2.connect(settings.sync_admin_url) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO app.audit_logs (
                            log_id, user_id, user_email, role, question,
                            generated_sql, execution_status, rows_returned,
                            latency_ms, token_usage, cost_estimate
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            entry["log_id"],
                            entry.get("user_id"),
                            entry.get("user_email"),
                            entry.get("role"),
                            entry["question"],
                            entry.get("generated_sql"),
                            entry["execution_status"],
                            entry.get("rows_returned", 0),
                            entry.get("latency_ms", 0),
                            entry.get("token_usage", 0),
                            entry.get("cost_estimate"),
                        ),
                    )
        except Exception as e:
            logger.debug(f"DB audit insert skipped (using in-memory buffer): {e}")

    async def log_event(
        self,
        question: str,
        execution_status: str,
        role: str = "analyst",
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        generated_sql: Optional[str] = None,
        rows_returned: int = 0,
        latency_ms: int = 0,
        token_usage: int = 0,
        cost_estimate: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Record an audit event in memory and asynchronously persist to Postgres."""
        entry: Dict[str, Any] = {
            "log_id": str(uuid.uuid4()),
            "user_id": user_id,
            "user_email": user_email or "anonymous@asklens.local",
            "role": role,
            "question": question,
            "generated_sql": generated_sql,
            "execution_status": execution_status,
            "rows_returned": rows_returned,
            "latency_ms": latency_ms,
            "token_usage": token_usage,
            "cost_estimate": cost_estimate,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._memory_logs.appendleft(entry)
        asyncio.create_task(asyncio.to_thread(self._write_sync, entry))
        return entry

    def get_recent_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch recent audit logs from PostgreSQL, falling back to in-memory buffer."""
        try:
            with psycopg2.connect(settings.sync_admin_url) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        """
                        SELECT log_id::text, user_id::text, user_email, role,
                               question, generated_sql, execution_status,
                               rows_returned, latency_ms, token_usage,
                               cost_estimate, created_at
                        FROM app.audit_logs
                        ORDER BY created_at DESC
                        LIMIT %s
                        """,
                        (limit,),
                    )
                    rows = cur.fetchall()
                    if rows:
                        return [
                            {
                                **dict(r),
                                "cost_estimate": float(r["cost_estimate"]) if r["cost_estimate"] is not None else None,
                                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                            }
                            for r in rows
                        ]
        except Exception as e:
            logger.debug(f"DB audit fetch failed (returning in-memory logs): {e}")

        return list(self._memory_logs)[:limit]


audit_logger = AuditLogger()
