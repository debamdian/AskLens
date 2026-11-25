"""Unit tests for RBAC table and column enforcement in SQLValidator."""

import pytest
from app.sql.validator import SQLValidator, SQLValidationError


@pytest.fixture
def validator():
    return SQLValidator(dialect="postgres", max_limit=500)


def test_admin_can_query_all_tables_and_columns(validator):
    sql = "SELECT customer_id, email, phone FROM warehouse.customers LIMIT 10"
    sanitized = validator.validate_and_sanitize(sql, role_name="admin")
    assert "customers" in sanitized.lower()


def test_sales_manager_blocked_from_marketing_spend(validator):
    sql = "SELECT channel, SUM(amount) FROM warehouse.marketing_spend GROUP BY channel"
    with pytest.raises(SQLValidationError, match="not authorized to query table 'marketing_spend'"):
        validator.validate_and_sanitize(sql, role_name="sales_manager")


def test_analyst_allowed_marketing_spend(validator):
    sql = "SELECT channel, SUM(amount) FROM warehouse.marketing_spend GROUP BY channel"
    sanitized = validator.validate_and_sanitize(sql, role_name="analyst")
    assert "marketing_spend" in sanitized.lower()


def test_analyst_blocked_from_customer_email(validator):
    sql = "SELECT c.customer_id, c.email FROM warehouse.customers c"
    with pytest.raises(SQLValidationError, match="cannot access column 'customers.email'"):
        validator.validate_and_sanitize(sql, role_name="analyst")


def test_sales_manager_blocked_from_select_star_on_customers(validator):
    sql = "SELECT * FROM warehouse.customers"
    with pytest.raises(SQLValidationError, match="cannot use SELECT \\*"):
        validator.validate_and_sanitize(sql, role_name="sales_manager")


def test_cte_alias_not_flagged_as_disallowed_table(validator):
    sql = """
    WITH regional_orders AS (
        SELECT region_id, SUM(total_amount) AS rev
        FROM warehouse.orders
        GROUP BY region_id
    )
    SELECT region_id, rev FROM regional_orders
    """
    sanitized = validator.validate_and_sanitize(sql, role_name="sales_manager")
    assert "regional_orders" in sanitized.lower()
