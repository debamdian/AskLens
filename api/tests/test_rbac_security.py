"""Unit tests for RBAC table and column enforcement in SQLValidator."""

import pytest
from app.sql.validator import SQLValidator, SQLValidationError
from app.security.pii_masking import mask_rows


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


def test_pii_masking_masks_sensitive_fields():
    rows = [
        {
            "customer_id": 1,
            "first_name": "Aarav",
            "last_name": "Patel",
            "email": "aarav.patel@example.com",
            "phone": "+91-9876543210",
            "city": "Ahmedabad",
        }
    ]
    masked = mask_rows(rows, mask_pii=True)
    assert masked[0]["first_name"] == "A***"
    assert masked[0]["last_name"] == "P***"
    assert masked[0]["email"] == "a***@example.com"
    assert masked[0]["phone"].endswith("3210")
    assert "987654" not in masked[0]["phone"]
    assert masked[0]["city"] == "Ahmedabad"


def test_pii_masking_bypassed_for_admin():
    rows = [{"email": "aarav.patel@example.com", "first_name": "Aarav"}]
    unmasked = mask_rows(rows, mask_pii=False)
    assert unmasked[0]["email"] == "aarav.patel@example.com"
    assert unmasked[0]["first_name"] == "Aarav"
