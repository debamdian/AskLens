"""SQL Self-Correction Loop.

When a query fails AST validation or PostgreSQL execution, this agent sends
the error diagnostic and failed query back to the LLM for automated fixing (up to 3 retries).
"""

import logging
from typing import Tuple
from app.sql.validator import SQLValidator, SQLValidationError
from app.sql.executor import SafeSQLExecutor
from app.db.connector import QueryResult
from app.llm.factory import llm_service
from app.schema.crawler import crawler

logger = logging.getLogger(__name__)

SELF_CORRECT_PROMPT = """You are an Expert PostgreSQL Troubleshooter.
A previously generated SQL query failed with an error. Fix the query so it executes correctly.

USER QUESTION:
{question}

FAILED SQL:
```sql
{failed_sql}
```

ERROR DIAGNOSTIC:
{error_message}

AVAILABLE SCHEMA:
{schema_context}

RULES:
1. Target ONLY the 'warehouse' schema.
2. Return ONLY the corrected SQL wrapped in a ```sql ... ``` code block.
3. No markdown explanations or preamble.
"""


class SQLSelfCorrector:
    """Orchestrates query execution with automatic error feedback loop."""

    def __init__(self, executor: SafeSQLExecutor = None, llm=None, max_retries: int = 3):
        self.executor = executor or SafeSQLExecutor()
        self.llm = llm or llm_service
        self.max_retries = max_retries

    def execute_with_self_correction(
        self,
        question: str,
        initial_sql: str
    ) -> Tuple[QueryResult, str, int]:
        """Executes query, catching validation or DB errors and retrying with LLM feedback.
        
        Returns:
            Tuple of (QueryResult, final_sql_used, retry_count)
        """
        current_sql = initial_sql
        last_error = ""

        for attempt in range(self.max_retries + 1):
            try:
                result = self.executor.execute(current_sql)
                return result, current_sql, attempt

            except Exception as e:
                last_error = str(e)
                logger.warning(
                    f"SQL execution attempt {attempt + 1} failed: {last_error}"
                )

                if attempt == self.max_retries:
                    break

                # Self-correction step: ask LLM to fix the query
                try:
                    schema_ctx = crawler.get_prompt_formatted_schema()
                except Exception:
                    schema_ctx = "warehouse.orders, warehouse.customers, warehouse.products, warehouse.regions"

                prompt = SELF_CORRECT_PROMPT.format(
                    question=question,
                    failed_sql=current_sql,
                    error_message=last_error,
                    schema_context=schema_ctx
                )

                try:
                    fixed_response = self.llm.generate(
                        prompt=prompt,
                        temperature=0.0
                    )
                    # Extract SQL
                    from app.sql.generator import sql_generator
                    current_sql = sql_generator._extract_sql(fixed_response)
                except Exception as llm_err:
                    logger.error(f"Failed to generate self-corrected SQL: {llm_err}")
                    break

        raise RuntimeError(
            f"Query failed after {self.max_retries} correction attempts. Last error: {last_error}"
        )


# Global instance
self_corrector = SQLSelfCorrector()
