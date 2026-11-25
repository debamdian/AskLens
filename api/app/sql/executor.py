"""Safe SQL Execution Pipeline.

Coordinates AST validation, cost threshold verification, and read-only execution.
"""

import logging
from typing import Optional
from app.sql.validator import SQLValidator, SQLValidationError
from app.db.connector import PostgresConnector, QueryResult, warehouse_connector
from app.core.config import settings

logger = logging.getLogger(__name__)


class SafeSQLExecutor:
    """Validates and executes SQL queries safely."""

    def __init__(
        self,
        validator: Optional[SQLValidator] = None,
        connector: Optional[PostgresConnector] = None
    ):
        self.validator = validator or SQLValidator()
        self.connector = connector or warehouse_connector

    def execute(self, raw_sql: str, role_name: Optional[str] = None) -> QueryResult:
        """Full pipeline: AST validation -> Cost Estimation -> Read-only DB Execution."""
        # 1. AST Validation, RBAC enforcement & LIMIT injection
        sanitized_sql = self.validator.validate_and_sanitize(raw_sql, role_name=role_name)

        # 2. Pre-execution Cost Check (if database is connected)
        try:
            estimated_cost = self.connector.get_query_cost(sanitized_sql)
            if estimated_cost > settings.MAX_QUERY_COST:
                raise SQLValidationError(
                    f"Query rejected: Estimated cost {estimated_cost:.1f} exceeds threshold {settings.MAX_QUERY_COST:.1f}"
                )
        except SQLValidationError:
            raise
        except Exception as e:
            # If EXPLAIN fails due to table not existing or syntax, catch and log
            logger.warning(f"Cost estimation skipped or failed: {e}")
            estimated_cost = None

        # 3. Read-only Execution
        result = self.connector.execute_read_only(sanitized_sql)
        result.cost_estimate = estimated_cost
        return result


# Global instance
safe_executor = SafeSQLExecutor()
