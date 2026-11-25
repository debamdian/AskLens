"""Seed script for the e-commerce sales warehouse.

Creates realistic 2-year e-commerce data in the 'warehouse' schema:
- regions (including Gujarat, Maharashtra, Karnataka, Tamil Nadu, Delhi NCR, West Bengal)
- customers
- products
- orders & order_items
- returns
- marketing_spend

Engineered Root Cause:
Deliberate sales dip in Gujarat during Q3/Q4 of the most recent year:
1. Marketing spend in Gujarat cut by ~85% (from ₹120k/mo to ₹18k/mo)
2. Stockout on top 2 revenue-generating Electronics products
3. Shipping delivery delays causing return rate surge from 3.5% to 18%
"""

import sys
import os
import random
from datetime import datetime, timedelta, date
from decimal import Decimal
import psycopg2
from psycopg2.extras import execute_values

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.core.config import settings

try:
    from faker import Faker
    fake = Faker("en_IN")
except ImportError:
    # Minimal fallback mock if faker is not yet installed
    class FakeMock:
        def first_name(self): return random.choice(["Aarav", "Priya", "Rahul", "Ananya", "Rohan", "Sneha", "Vikram", "Neha"])
        def last_name(self): return random.choice(["Patel", "Sharma", "Shah", "Mehta", "Deshmukh", "Iyer", "Reddy", "Banerjee"])
        def email(self): return f"user{random.randint(1000, 999999)}@example.com"
        def phone_number(self): return f"+91 {random.randint(70000, 99999)} {random.randint(10000, 99999)}"
    fake = FakeMock()


def seed_database():
    """Populates the PostgreSQL warehouse schema with realistic data."""
    print("Connecting to database for warehouse seeding...")
    conn = psycopg2.connect(settings.sync_admin_url)
    cur = conn.cursor()

    try:
        # Clear existing data in warehouse schema
        print("Clearing existing warehouse data...")
        cur.execute("""
            TRUNCATE TABLE warehouse.returns CASCADE;
            TRUNCATE TABLE warehouse.marketing_spend CASCADE;
            TRUNCATE TABLE warehouse.order_items CASCADE;
            TRUNCATE TABLE warehouse.orders CASCADE;
            TRUNCATE TABLE warehouse.products CASCADE;
            TRUNCATE TABLE warehouse.customers CASCADE;
            TRUNCATE TABLE warehouse.regions CASCADE;
        """)

        # 1. Insert Regions
        print("Seeding regions...")
        regions = [
            ("Gujarat", "India", "West", "Tier-1"),
            ("Maharashtra", "India", "West", "Tier-1"),
            ("Karnataka", "India", "South", "Tier-1"),
            ("Tamil Nadu", "India", "South", "Tier-1"),
            ("Delhi NCR", "India", "North", "Tier-1"),
            ("West Bengal", "India", "East", "Tier-2")
        ]
        cur.executemany("""
            INSERT INTO warehouse.regions (name, country, zone, tier)
            VALUES (%s, %s, %s, %s) RETURNING region_id;
        """, regions)
        conn.commit()

        cur.execute("SELECT region_id, name FROM warehouse.regions;")
        region_map = {name: r_id for r_id, name in cur.fetchall()}
        gujarat_id = region_map["Gujarat"]

        # 2. Insert Products
        print("Seeding products...")
        product_templates = [
            ("Smart Ultra HD 4K Monitor 27-inch", "Electronics", "Monitors", 16000.00, 24999.00),
            ("Wireless Noise-Canceling Headphones", "Electronics", "Audio", 4500.00, 7999.00),
            ("Mechanical RGB Gaming Keyboard", "Electronics", "Accessories", 2200.00, 3999.00),
            ("Ergonomic Mesh Office Chair", "Home & Furniture", "Furniture", 5500.00, 9499.00),
            ("Standing Desk Converter", "Home & Furniture", "Furniture", 6000.00, 10999.00),
            ("Premium Cotton Formal Shirt", "Apparel", "Men", 600.00, 1499.00),
            ("Slim Fit Stretch Denim Jeans", "Apparel", "Men", 800.00, 1999.00),
            ("Designer Festive Kurti", "Apparel", "Women", 500.00, 1299.00),
            ("Smart Fitness Tracking Watch", "Electronics", "Wearables", 1800.00, 3499.00),
            ("Organic Cold Pressed Coconut Oil 1L", "Groceries", "Pantry", 250.00, 499.00),
            ("Arabica Dark Roast Coffee Beans 500g", "Groceries", "Beverages", 350.00, 699.00),
            ("Stainless Steel Thermal Water Bottle", "Home & Kitchen", "Kitchenware", 300.00, 649.00),
            ("Cast Iron Dutch Oven 4.5L", "Home & Kitchen", "Cookware", 1800.00, 3299.00),
            ("Memory Foam Orthopedic Pillow", "Home & Kitchen", "Bedding", 700.00, 1399.00),
            ("Yoga & Fitness Mat Anti-Slip 6mm", "Fitness", "Accessories", 400.00, 899.00)
        ]

        products_data = []
        for i, (name, cat, subcat, cost, price) in enumerate(product_templates):
            sku = f"SKU-{cat[:3].upper()}-{i+101}"
            # Electronics stockout in warehouse for Gujarat anomaly
            stock = 0 if i in [0, 1] else random.randint(40, 500)
            products_data.append((name, sku, cat, subcat, cost, price, stock, False))

        execute_values(cur, """
            INSERT INTO warehouse.products (name, sku, category, subcategory, cost_price, unit_price, stock_quantity, is_discontinued)
            VALUES %s RETURNING product_id, name, unit_price, cost_price, category;
        """, products_data)
        products = cur.fetchall()
        conn.commit()

        # 3. Insert Customers
        print("Seeding customers...")
        customers_data = []
        customer_segments = ["Consumer", "SMB", "Enterprise", "VIP"]
        now = datetime.now()
        start_date = now - timedelta(days=730)

        for _ in range(300):
            r_id = random.choice(list(region_map.values()))
            seg = random.choice(customer_segments)
            signup = start_date + timedelta(days=random.randint(0, 700))
            customers_data.append((
                fake.first_name(),
                fake.last_name(),
                f"cust_{random.randint(10000, 999999)}_{fake.email()}",
                fake.phone_number(),
                r_id,
                seg,
                signup.date(),
                True
            ))

        execute_values(cur, """
            INSERT INTO warehouse.customers (first_name, last_name, email, phone, region_id, customer_segment, signup_date, is_active)
            VALUES %s RETURNING customer_id, region_id;
        """, customers_data)
        customers = cur.fetchall()
        conn.commit()

        cust_by_region = {}
        for c_id, r_id in customers:
            cust_by_region.setdefault(r_id, []).append(c_id)

        # 4. Generate Orders & Order Items across 24 Months
        print("Generating 24 months of orders with engineered Gujarat sales dip...")
        orders_batch = []
        order_items_batch = []
        returns_batch = []
        marketing_batch = []
        order_seq = 0

        # Current reference time = 2024-12-01
        base_date = datetime(2023, 1, 1)
        total_days = 700

        # We simulate day by day
        for day_offset in range(total_days):
            current_date = base_date + timedelta(days=day_offset)
            is_recent_h2 = (current_date >= datetime(2024, 7, 1)) # Q3/Q4 2024

            for r_name, r_id in region_map.items():
                # Daily marketing spend
                if r_name == "Gujarat" and is_recent_h2:
                    # Slashed marketing spend in Gujarat during Q3/Q4: ₹500 - ₹800/day
                    mktg_amt = Decimal(random.randint(400, 800))
                    impressions = random.randint(1500, 3000)
                    clicks = random.randint(50, 120)
                else:
                    # Normal marketing spend: ₹3,500 - ₹5,000/day
                    mktg_amt = Decimal(random.randint(3500, 5200))
                    impressions = random.randint(12000, 25000)
                    clicks = random.randint(450, 900)

                if current_date.day == 1 or current_date.day == 15:
                    marketing_batch.append((
                        r_id,
                        random.choice(["Google Ads", "Meta Ads", "Regional Influencers"]),
                        current_date.date(),
                        mktg_amt * 15,
                        impressions * 15,
                        clicks * 15,
                        int(clicks * 0.08 * 15)
                    ))

                # Number of orders per region per day
                if r_name == "Gujarat" and is_recent_h2:
                    # Steep dip: only 1 to 3 orders/day (was 8-15)
                    num_orders = random.randint(1, 3)
                else:
                    num_orders = random.randint(7, 16)

                region_custs = cust_by_region.get(r_id, [c[0] for c in customers])

                for _ in range(num_orders):
                    order_seq += 1
                    c_id = random.choice(region_custs)
                    order_num = f"ORD-{current_date.strftime('%Y%m%d')}-{order_seq:06d}"
                    order_time = current_date + timedelta(hours=random.randint(8, 21), minutes=random.randint(0, 59))
                    pay_method = random.choice(["UPI", "Credit Card", "Net Banking", "COD"])
                    ship_channel = random.choice(["Express", "Standard", "Same Day"])

                    # Gujarat stockout effect: avoid top electronics in Gujarat H2
                    if r_name == "Gujarat" and is_recent_h2:
                        eligible_products = [p for p in products if p[4] != "Electronics"]
                        status = "completed" if random.random() > 0.18 else "refunded"
                    else:
                        eligible_products = products
                        status = "completed" if random.random() > 0.04 else "refunded"

                    # 1 to 3 items per order
                    item_count = random.randint(1, 3)
                    chosen_items = random.sample(eligible_products, min(item_count, len(eligible_products)))

                    total_amt = Decimal("0.0")
                    total_disc = Decimal("0.0")
                    item_tuples = []

                    for prod in chosen_items:
                        p_id, p_name, u_price, c_price, cat = prod
                        qty = random.randint(1, 2)
                        item_total = Decimal(str(u_price)) * qty
                        item_cost = Decimal(str(c_price)) * qty
                        discount = Decimal(str(round(float(item_total) * random.choice([0.0, 0.05, 0.10]), 2)))

                        item_tuples.append((p_id, qty, u_price, item_total - discount, discount, item_cost))
                        total_amt += (item_total - discount)
                        total_disc += discount

                    orders_batch.append((
                        order_num, c_id, r_id, order_time, status, pay_method, ship_channel, total_amt, total_disc, Decimal("50.00"), item_tuples
                    ))

        # Insert Orders in chunks
        print(f"Inserting {len(orders_batch)} generated orders...")
        order_insert_tuples = [
            (o[0], o[1], o[2], o[3], o[4], o[5], o[6], o[7], o[8], o[9]) for o in orders_batch
        ]

        execute_values(cur, """
            INSERT INTO warehouse.orders (order_number, customer_id, region_id, order_date, status, payment_method, shipping_channel, total_amount, discount_amount, shipping_fee)
            VALUES %s RETURNING order_id, order_number, region_id, status, order_date;
        """, order_insert_tuples)
        inserted_orders = cur.fetchall()
        conn.commit()

        order_map = {row[1]: (row[0], row[2], row[3], row[4]) for row in inserted_orders}

        # Insert Order Items & Returns
        print("Inserting order items and returns...")
        for o in orders_batch:
            ord_num = o[0]
            items = o[10]
            ord_info = order_map.get(ord_num)
            if not ord_info:
                continue
            ord_id, r_id, status, o_date = ord_info

            for itm in items:
                p_id, qty, u_price, tot_price, disc, cost_amt = itm
                cur.execute("""
                    INSERT INTO warehouse.order_items (order_id, product_id, quantity, unit_price, total_price, discount_amount, cost_amount)
                    VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING order_item_id;
                """, (ord_id, p_id, qty, u_price, tot_price, disc, cost_amt))
                order_item_id = cur.fetchone()[0]

                if status == "refunded":
                    # Gujarat monsoons shipping delay surge in H2
                    if r_id == gujarat_id:
                        reason = random.choice(["Delayed Delivery", "Delayed Delivery", "Damaged in Transit", "Defective"])
                    else:
                        reason = random.choice(["Changed Mind", "Defective", "Wrong Size"])

                    returns_batch.append((
                        ord_id, order_item_id, o_date.date() + timedelta(days=random.randint(2, 7)), reason, tot_price, "approved"
                    ))

        if returns_batch:
            execute_values(cur, """
                INSERT INTO warehouse.returns (order_id, order_item_id, return_date, reason, refund_amount, status)
                VALUES %s;
            """, returns_batch)

        if marketing_batch:
            execute_values(cur, """
                INSERT INTO warehouse.marketing_spend (region_id, channel, date, amount, impressions, clicks, conversions)
                VALUES %s;
            """, marketing_batch)

        conn.commit()
        print("Warehouse database seeding completed successfully!")
        print(f"Summary: Regions: {len(regions)}, Products: {len(products)}, Customers: {len(customers)}, Orders: {len(orders_batch)}, Returns: {len(returns_batch)}")

    except Exception as e:
        conn.rollback()
        print(f"Error seeding database: {e}", file=sys.stderr)
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    seed_database()
