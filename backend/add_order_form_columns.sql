-- Add order form columns to bot_settings table
ALTER TABLE bot_settings
ADD COLUMN IF NOT EXISTS order_form_template TEXT,
ADD COLUMN IF NOT EXISTS order_confirmation_message TEXT,
ADD COLUMN IF NOT EXISTS order_form_enabled BOOLEAN DEFAULT TRUE;

-- Add order_details column to orders table and make other columns nullable
ALTER TABLE orders
ADD COLUMN IF NOT EXISTS order_details TEXT,
ALTER COLUMN name DROP NOT NULL,
ALTER COLUMN address DROP NOT NULL,
ALTER COLUMN product_name DROP NOT NULL;
