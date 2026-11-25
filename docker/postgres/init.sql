-- Enable pgvector and UUID extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create logical schemas
CREATE SCHEMA IF NOT EXISTS warehouse;
CREATE SCHEMA IF NOT EXISTS app;

-- =============================================================================
-- Warehouse Tables (Data Warehouse queried by the AI Analyst)
-- =============================================================================

CREATE TABLE IF NOT EXISTS warehouse.regions (
    region_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL DEFAULT 'India',
    zone VARCHAR(50) NOT NULL, -- West, North, South, East, Central
    tier VARCHAR(20) NOT NULL DEFAULT 'Tier-1',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS warehouse.customers (
    customer_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    phone VARCHAR(30),
    region_id INT REFERENCES warehouse.regions(region_id),
    customer_segment VARCHAR(50) NOT NULL, -- Enterprise, SMB, Consumer, VIP
    signup_date DATE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS warehouse.products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    sku VARCHAR(50) UNIQUE NOT NULL,
    category VARCHAR(100) NOT NULL, -- Electronics, Apparel, Home & Kitchen, Books, Health
    subcategory VARCHAR(100) NOT NULL,
    cost_price NUMERIC(12, 2) NOT NULL,
    unit_price NUMERIC(12, 2) NOT NULL,
    stock_quantity INT NOT NULL DEFAULT 0,
    is_discontinued BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS warehouse.orders (
    order_id SERIAL PRIMARY KEY,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    customer_id INT NOT NULL REFERENCES warehouse.customers(customer_id),
    region_id INT NOT NULL REFERENCES warehouse.regions(region_id),
    order_date TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(50) NOT NULL, -- completed, pending, cancelled, refunded
    payment_method VARCHAR(50) NOT NULL, -- UPI, Credit Card, Net Banking, COD
    shipping_channel VARCHAR(50) NOT NULL, -- Express, Standard, Same Day
    total_amount NUMERIC(12, 2) NOT NULL,
    discount_amount NUMERIC(12, 2) DEFAULT 0.00,
    shipping_fee NUMERIC(12, 2) DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS warehouse.order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES warehouse.orders(order_id) ON DELETE CASCADE,
    product_id INT NOT NULL REFERENCES warehouse.products(product_id),
    quantity INT NOT NULL,
    unit_price NUMERIC(12, 2) NOT NULL,
    total_price NUMERIC(12, 2) NOT NULL,
    discount_amount NUMERIC(12, 2) DEFAULT 0.00,
    cost_amount NUMERIC(12, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS warehouse.returns (
    return_id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES warehouse.orders(order_id),
    order_item_id INT REFERENCES warehouse.order_items(order_item_id),
    return_date DATE NOT NULL,
    reason VARCHAR(200) NOT NULL, -- Defective, Delayed Delivery, Wrong Item, Changed Mind
    refund_amount NUMERIC(12, 2) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'approved' -- approved, rejected, processing
);

CREATE TABLE IF NOT EXISTS warehouse.marketing_spend (
    spend_id SERIAL PRIMARY KEY,
    region_id INT NOT NULL REFERENCES warehouse.regions(region_id),
    channel VARCHAR(100) NOT NULL, -- Google Ads, Meta Ads, Regional Print, Influencer, SEO
    date DATE NOT NULL,
    amount NUMERIC(12, 2) NOT NULL,
    impressions INT DEFAULT 0,
    clicks INT DEFAULT 0,
    conversions INT DEFAULT 0
);

-- =============================================================================
-- Application Tables (App metadata, chat, memory, audit, pgvector)
-- =============================================================================

CREATE TABLE IF NOT EXISTS app.roles (
    role_id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL, -- admin, analyst, sales_manager
    description TEXT,
    allowed_tables JSONB NOT NULL DEFAULT '[]'::jsonb,
    allowed_columns JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app.users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(150) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'analyst',
    assigned_region_id INT REFERENCES warehouse.regions(region_id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app.chat_sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES app.users(user_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL DEFAULT 'New Analysis',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app.messages (
    message_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES app.chat_sessions(session_id) ON DELETE CASCADE,
    sender VARCHAR(20) NOT NULL, -- user, assistant
    content TEXT NOT NULL,
    plan JSONB,
    generated_sql TEXT,
    query_results JSONB,
    chart_spec JSONB,
    latency_ms INT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app.schema_embeddings (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    column_name VARCHAR(100),
    description TEXT NOT NULL,
    embedding vector(384), -- all-MiniLM-L6-v2 dimension
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app.golden_queries (
    id SERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    sql_query TEXT NOT NULL,
    description TEXT,
    category VARCHAR(100),
    verified BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app.audit_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID,
    user_email VARCHAR(150),
    role VARCHAR(50),
    question TEXT NOT NULL,
    generated_sql TEXT,
    execution_status VARCHAR(50) NOT NULL, -- success, validation_error, execution_error, timeout
    rows_returned INT DEFAULT 0,
    latency_ms INT,
    token_usage INT DEFAULT 0,
    cost_estimate NUMERIC(10, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app.feedback (
    feedback_id SERIAL PRIMARY KEY,
    message_id UUID REFERENCES app.messages(message_id) ON DELETE CASCADE,
    user_id UUID,
    rating INT NOT NULL, -- 1 = thumbs down, 5 = thumbs up
    user_sql_correction TEXT,
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- Dedicated Read-Only User Role Setup
-- =============================================================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'warehouse_readonly') THEN
        CREATE ROLE warehouse_readonly WITH LOGIN PASSWORD 'readonly_secure_password_123';
    END IF;
END
$$;

-- Grant usage on warehouse schema only
GRANT USAGE ON SCHEMA warehouse TO warehouse_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA warehouse TO warehouse_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA warehouse GRANT SELECT ON TABLES TO warehouse_readonly;

-- Revoke all access to app schema and dangerous schemas
REVOKE ALL ON SCHEMA app FROM warehouse_readonly;
REVOKE ALL ON SCHEMA public FROM warehouse_readonly;
REVOKE ALL ON ALL TABLES IN SCHEMA app FROM warehouse_readonly;
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM warehouse_readonly;
