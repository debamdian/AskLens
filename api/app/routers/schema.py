"""Schema Explorer Router.

Allows the frontend to inspect warehouse tables, columns, sample values,
and foreign key relationships.
"""

from fastapi import APIRouter
from app.schema.crawler import crawler

router = APIRouter(prefix="/api/v1/schema", tags=["Schema Explorer"])


@router.get("/warehouse")
def get_warehouse_schema():
    """Returns crawled schema metadata for the warehouse schema."""
    try:
        return crawler.crawl()
    except Exception as e:
        # Fallback offline schema metadata
        return {
            "schema_name": "warehouse",
            "tables": {
                "regions": {"columns": [{"name": "region_id", "type": "int"}, {"name": "name", "type": "varchar"}, {"name": "zone", "type": "varchar"}]},
                "customers": {"columns": [{"name": "customer_id", "type": "int"}, {"name": "first_name", "type": "varchar"}, {"name": "customer_segment", "type": "varchar"}]},
                "products": {"columns": [{"name": "product_id", "type": "int"}, {"name": "name", "type": "varchar"}, {"name": "category", "type": "varchar"}, {"name": "unit_price", "type": "numeric"}]},
                "orders": {"columns": [{"name": "order_id", "type": "int"}, {"name": "order_date", "type": "timestamp"}, {"name": "total_amount", "type": "numeric"}, {"name": "status", "type": "varchar"}]},
                "order_items": {"columns": [{"name": "order_item_id", "type": "int"}, {"name": "quantity", "type": "int"}, {"name": "unit_price", "type": "numeric"}]},
                "returns": {"columns": [{"name": "return_id", "type": "int"}, {"name": "reason", "type": "varchar"}, {"name": "refund_amount", "type": "numeric"}]},
                "marketing_spend": {"columns": [{"name": "spend_id", "type": "int"}, {"name": "channel", "type": "varchar"}, {"name": "amount", "type": "numeric"}]}
            }
        }
