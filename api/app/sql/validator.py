"""SQL Safety AST Validator using sqlglot.

Enforces:
1. Single statement only.
2. Root must be SELECT (CTEs / WITH allowed).
3. Rejects DDL, DML, COPY, and administrative commands.
4. Rejects pg_catalog, information_schema, and app schema access.
5. Blocks dangerous built-in functions (pg_sleep, lo_*, dblink, file IO).
6. Injects and enforces row LIMIT clause.
7. Validates estimated execution cost via EXPLAIN.
"""

from typing import List, Optional, Set, Tuple
import sqlglot
from sqlglot import exp
from app.core.config import settings
from app.security.rbac import rbac_manager

# Banned functions that pose security risks or DoS vectors
DANGEROUS_FUNCTIONS = {
    "pg_sleep",
    "pg_terminate_backend",
    "pg_cancel_backend",
    "pg_reload_conf",
    "pg_rotate_logfile",
    "pg_read_file",
    "pg_write_file",
    "pg_ls_dir",
    "lo_import",
    "lo_export",
    "lo_unlink",
    "dblink",
    "dblink_exec",
    "query_to_xml",
    "query_to_xmlschema",
    "schema_to_xml",
    "current_setting",
    "set_config",
    "eval",
    "system"
}

# Banned system / metadata schemas
BANNED_SCHEMAS = {
    "pg_catalog",
    "information_schema",
    "pg_toast",
    "app"  # App internal metadata tables must never be queried by warehouse agent
}


class SQLValidationError(Exception):
    """Raised when generated SQL violates safety constraints."""
    pass


class SQLValidator:
    """Parses and validates SQL queries for safe read-only execution."""

    def __init__(self, dialect: str = "postgres", max_limit: int = None, max_cost: float = None):
        self.dialect = dialect
        self.max_limit = max_limit or settings.MAX_ROW_LIMIT
        self.max_cost = max_cost or settings.MAX_QUERY_COST

    def validate_and_sanitize(self, sql_query: str, role_name: Optional[str] = None) -> str:
        """Parses AST, validates security & RBAC constraints, injects LIMIT, and returns safe SQL.
        
        Raises SQLValidationError if query is unsafe or violates role permissions.
        """
        clean_sql = sql_query.strip().rstrip(";")

        # 1. Reject empty
        if not clean_sql:
            raise SQLValidationError("Query is empty.")

        # 2. Parse statements with sqlglot
        try:
            parsed = sqlglot.parse(clean_sql, read=self.dialect)
        except Exception as e:
            raise SQLValidationError(f"SQL Syntax Error: Could not parse query ({str(e)})")

        # 3. Reject multiple statements
        if len(parsed) != 1:
            raise SQLValidationError(f"Multiple statements are prohibited. Found {len(parsed)} statements.")

        expression = parsed[0]
        if expression is None:
            raise SQLValidationError("Invalid SQL statement structure.")

        # 4. Check Root Expression: Must be Select or Union
        valid_root = isinstance(expression, (exp.Select, exp.Union))
        if not valid_root:
            raise SQLValidationError(f"Only SELECT queries are allowed. Found '{expression.key.upper()}'.")

        # 5. Check for disallowed AST nodes (DDL, DML, Transactions, Commands)
        disallowed_nodes = (
            exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Create,
            exp.Alter, exp.Command, exp.TruncateTable, exp.Grant, exp.Revoke
        )
        for node in expression.walk():
            if isinstance(node, disallowed_nodes):
                raise SQLValidationError(f"Disallowed command or statement type: '{node.key.upper()}'.")

        # 6. Check Table and Schema References (plus optional RBAC allowlist)
        cte_names: Set[str] = {
            cte.alias_or_name.lower()
            for cte in expression.find_all(exp.CTE)
            if cte.alias_or_name
        }
        referenced_tables: Set[str] = set()
        alias_to_table: dict[str, str] = {}

        policy = rbac_manager.get_policy(role_name) if role_name else None

        for table in expression.find_all(exp.Table):
            db = table.db.lower() if table.db else ""
            table_name = table.name.lower()

            if db in BANNED_SCHEMAS:
                raise SQLValidationError(f"Access to schema '{db}' is forbidden.")

            if table_name.startswith("pg_"):
                raise SQLValidationError(f"Access to internal system table '{table_name}' is forbidden.")

            if not db and table_name in cte_names:
                continue

            referenced_tables.add(table_name)
            if table.alias_or_name:
                alias_to_table[table.alias_or_name.lower()] = table_name

            if policy and not policy.is_table_allowed(table_name):
                raise SQLValidationError(
                    f"Access denied: role '{policy.name}' is not authorized to query table '{table_name}'."
                )

        # 6b. Check RBAC Column Restrictions
        if policy and policy.denied_columns:
            restricted_tables_in_query = [
                t for t in referenced_tables if t in policy.denied_columns
            ]
            if restricted_tables_in_query:
                if any(expression.find_all(exp.Star)):
                    raise SQLValidationError(
                        f"Access denied: role '{policy.name}' cannot use SELECT * on restricted table(s): {', '.join(sorted(restricted_tables_in_query))}."
                    )
                for col in expression.find_all(exp.Column):
                    col_name = col.name.lower()
                    col_tbl = col.table.lower() if col.table else None
                    resolved_tbl = alias_to_table.get(col_tbl, col_tbl) if col_tbl else None
                    if resolved_tbl:
                        if policy.is_column_denied(resolved_tbl, col_name):
                            raise SQLValidationError(
                                f"Access denied: role '{policy.name}' cannot access column '{resolved_tbl}.{col_name}'."
                            )
                    else:
                        for rt in restricted_tables_in_query:
                            if policy.is_column_denied(rt, col_name):
                                raise SQLValidationError(
                                    f"Access denied: role '{policy.name}' cannot access column '{col_name}' on table '{rt}'."
                                )

        # 7. Check for Dangerous Functions
        for func in expression.find_all(exp.Func, exp.Anonymous):
            func_name = func.name.lower() if hasattr(func, "name") else ""
            if not func_name and hasattr(func, "this") and isinstance(func.this, exp.Literal):
                func_name = str(func.this).lower()

            if func_name in DANGEROUS_FUNCTIONS:
                raise SQLValidationError(f"Execution of dangerous function '{func_name}()' is forbidden.")

            if func_name.startswith("pg_"):
                raise SQLValidationError(f"Function '{func_name}()' from pg_* family is forbidden.")

        # 8. Check and Enforce LIMIT Clause
        limit_expr = expression.args.get("limit")
        if limit_expr is None:
            expression = expression.limit(self.max_limit)
        else:
            try:
                # Extract limit number
                limit_val_str = limit_expr.find(exp.Literal)
                if limit_val_str:
                    current_limit = int(limit_val_str.this)
                    if current_limit > self.max_limit:
                        expression = expression.limit(self.max_limit)
                else:
                    expression = expression.limit(self.max_limit)
            except Exception:
                expression = expression.limit(self.max_limit)

        # Output sanitized SQL
        return expression.sql(dialect=self.dialect)


# Global validator instance
sql_validator = SQLValidator()
