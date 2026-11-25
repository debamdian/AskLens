"""Unit tests for the AST SQL Validator.

Tests strict blocking of:
- Multiple statements
- DDL and DML operations
- System catalog and information_schema probing
- Cross-schema privilege escalation (e.g. accessing 'app' schema)
- Dangerous built-in functions (pg_sleep, dblink, lo_*, file IO)
- Row limit injection and capping
"""

import pytest
from app.sql.validator import SQLValidator, SQLValidationError


@pytest.fixture
def validator():
    return SQLValidator(dialect="postgres", max_limit=500, max_cost=50000.0)


# ==============================================================================
# 1. Valid Query Tests
# ==============================================================================

def test_valid_simple_select(validator):
    sql = "SELECT order_id, total_amount FROM warehouse.orders;"
    result = validator.validate_and_sanitize(sql)
    assert "LIMIT 500" in result
    assert "warehouse.orders" in result


def test_valid_aggregations_and_joins(validator):
    sql = """
    SELECT r.name, SUM(o.total_amount) AS revenue, COUNT(o.order_id) AS total_orders
    FROM warehouse.orders o
    JOIN warehouse.regions r ON o.region_id = r.region_id
    WHERE o.status = 'completed'
    GROUP BY r.name
    ORDER BY revenue DESC
    LIMIT 10;
    """
    result = validator.validate_and_sanitize(sql)
    assert "LIMIT 10" in result
    assert "JOIN" in result


def test_valid_cte_query(validator):
    sql = """
    WITH regional_summary AS (
        SELECT region_id, SUM(total_amount) AS total_sales
        FROM warehouse.orders
        GROUP BY region_id
    )
    SELECT r.name, s.total_sales
    FROM regional_summary s
    JOIN warehouse.regions r ON s.region_id = r.region_id;
    """
    result = validator.validate_and_sanitize(sql)
    assert "WITH" in result
    assert "LIMIT 500" in result


# ==============================================================================
# 2. Multi-Statement Injection Tests
# ==============================================================================

def test_block_stacked_queries(validator):
    sql = "SELECT * FROM warehouse.orders; DROP TABLE warehouse.customers;"
    with pytest.raises(SQLValidationError, match="Multiple statements are prohibited"):
        validator.validate_and_sanitize(sql)


def test_block_harmless_multiple_selects(validator):
    sql = "SELECT 1; SELECT 2;"
    with pytest.raises(SQLValidationError, match="Multiple statements are prohibited"):
        validator.validate_and_sanitize(sql)


# ==============================================================================
# 3. DDL & DML Blocking Tests
# ==============================================================================

@pytest.mark.parametrize("malicious_sql", [
    "DROP TABLE warehouse.orders;",
    "TRUNCATE TABLE warehouse.orders;",
    "DELETE FROM warehouse.orders WHERE order_id > 0;",
    "UPDATE warehouse.products SET unit_price = 0.0;",
    "INSERT INTO warehouse.regions (name, zone) VALUES ('Hacked', 'North');",
    "ALTER TABLE warehouse.customers ADD COLUMN backdoor text;",
    "CREATE TABLE warehouse.evil (id int);",
    "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA warehouse TO public;",
    "REVOKE ALL ON warehouse.orders FROM warehouse_readonly;"
])
def test_block_destructive_commands(validator, malicious_sql):
    with pytest.raises(SQLValidationError):
        validator.validate_and_sanitize(malicious_sql)


# ==============================================================================
# 4. Catalog Probing & Cross-Schema Escalation Tests
# ==============================================================================

def test_block_information_schema_access(validator):
    sql = "SELECT table_name FROM information_schema.tables;"
    with pytest.raises(SQLValidationError, match="forbidden"):
        validator.validate_and_sanitize(sql)


def test_block_pg_catalog_access(validator):
    sql = "SELECT * FROM pg_catalog.pg_user;"
    with pytest.raises(SQLValidationError, match="forbidden"):
        validator.validate_and_sanitize(sql)


def test_block_pg_tables_access(validator):
    sql = "SELECT * FROM pg_tables;"
    with pytest.raises(SQLValidationError, match="forbidden"):
        validator.validate_and_sanitize(sql)


def test_block_app_schema_access(validator):
    sql = "SELECT email, hashed_password FROM app.users;"
    with pytest.raises(SQLValidationError, match="forbidden"):
        validator.validate_and_sanitize(sql)


# ==============================================================================
# 5. Dangerous Functions & DoS Vector Tests
# ==============================================================================

def test_block_pg_sleep(validator):
    sql = "SELECT pg_sleep(10) FROM warehouse.orders;"
    with pytest.raises(SQLValidationError, match="forbidden"):
        validator.validate_and_sanitize(sql)


def test_block_dblink(validator):
    sql = "SELECT * FROM dblink('dbname=other', 'SELECT * FROM secret') AS t(id int);"
    with pytest.raises(SQLValidationError, match="forbidden"):
        validator.validate_and_sanitize(sql)


def test_block_large_object_export(validator):
    sql = "SELECT lo_export(1, '/tmp/malicious');"
    with pytest.raises(SQLValidationError, match="forbidden"):
        validator.validate_and_sanitize(sql)


# ==============================================================================
# 6. LIMIT Clause Enforcement Tests
# ==============================================================================

def test_limit_injected_when_missing(validator):
    sql = "SELECT * FROM warehouse.products"
    result = validator.validate_and_sanitize(sql)
    assert "LIMIT 500" in result


def test_limit_capped_when_excessive(validator):
    sql = "SELECT * FROM warehouse.products LIMIT 50000;"
    result = validator.validate_and_sanitize(sql)
    assert "LIMIT 500" in result


def test_preserves_smaller_limit(validator):
    sql = "SELECT * FROM warehouse.products LIMIT 25;"
    result = validator.validate_and_sanitize(sql)
    assert "LIMIT 25" in result
