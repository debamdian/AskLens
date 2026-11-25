"""Database Connector Abstraction.

Provides a unified interface for executing read-only queries with safety constraints
(statement timeout, row limits, read-only transaction, and EXPLAIN cost estimation).
Ready for PostgreSQL with pluggable support for MySQL.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import time
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from app.core.config import settings


@dataclass
class QueryResult:
    """Standardized result returned by database connectors."""
    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int
    execution_time_ms: float
    cost_estimate: Optional[float] = None
    truncated: bool = False


class BaseConnector(ABC):
    """Abstract interface for database connectors."""

    @abstractmethod
    def execute_read_only(self, sql: str, row_limit: Optional[int] = None) -> QueryResult:
        """Executes a validated read-only SQL query with timeouts and row limits."""
        pass

    @abstractmethod
    def get_query_cost(self, sql: str) -> float:
        """Runs EXPLAIN to compute estimated cost before query execution."""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Checks database connectivity."""
        pass


class PostgresConnector(BaseConnector):
    """PostgreSQL implementation of BaseConnector."""

    def __init__(self, readonly_url: Optional[str] = None, timeout_ms: Optional[int] = None):
        self.readonly_url = readonly_url or settings.sync_warehouse_readonly_url
        self.timeout_ms = timeout_ms or settings.STATEMENT_TIMEOUT_MS
        self.default_row_limit = settings.MAX_ROW_LIMIT

    def _get_connection(self):
        """Creates a dedicated connection using read-only role."""
        return psycopg2.connect(self.readonly_url)

    def test_connection(self) -> bool:
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1;")
                    return cur.fetchone()[0] == 1
        except Exception:
            return False

    def get_query_cost(self, sql: str) -> float:
        """Runs EXPLAIN (FORMAT JSON) to extract the estimated total cost."""
        with self._get_connection() as conn:
            conn.set_session(readonly=True, autocommit=True)
            with conn.cursor() as cur:
                cur.execute(f"SET LOCAL statement_timeout = '{self.timeout_ms}ms';")
                cur.execute(f"EXPLAIN (FORMAT JSON) {sql};")
                plan = cur.fetchone()[0]
                if isinstance(plan, list) and len(plan) > 0:
                    return float(plan[0].get("Plan", {}).get("Total Cost", 0.0))
                return 0.0

    def execute_read_only(self, sql: str, row_limit: Optional[int] = None) -> QueryResult:
        """Executes query within a READ ONLY transaction with timeout and row cap."""
        limit = row_limit or self.default_row_limit
        start_time = time.perf_counter()

        with self._get_connection() as conn:
            # Enforce read-only session
            conn.set_session(readonly=True, autocommit=False)
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                try:
                    # Enforce strict statement timeout
                    cur.execute(f"SET LOCAL statement_timeout = '{self.timeout_ms}ms';")
                    cur.execute(sql)

                    # Fetch rows up to limit + 1 to detect truncation
                    fetched = cur.fetchmany(limit + 1)
                    duration_ms = (time.perf_counter() - start_time) * 1000.0

                    truncated = len(fetched) > limit
                    rows = fetched[:limit]

                    columns = [desc[0] for desc in cur.description] if cur.description else []
                    conn.commit()

                    return QueryResult(
                        columns=columns,
                        rows=[dict(r) for r in rows],
                        row_count=len(rows),
                        execution_time_ms=round(duration_ms, 2),
                        truncated=truncated
                    )
                except Exception as e:
                    conn.rollback()
                    raise RuntimeError(f"Database query error: {str(e)}") from e


# Global connector instance
warehouse_connector = PostgresConnector()
