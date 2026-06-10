-- ===========================================================================
-- Migration 005: Password reset + email verification token storage
-- Idempotent.
-- ===========================================================================

ALTER TABLE customers ADD COLUMN IF NOT EXISTS password_reset_token   VARCHAR(255);
ALTER TABLE customers ADD COLUMN IF NOT EXISTS password_reset_expires TIMESTAMPTZ;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS email_verify_token     VARCHAR(255);

CREATE INDEX IF NOT EXISTS ix_customers_password_reset_token ON customers(password_reset_token);
CREATE INDEX IF NOT EXISTS ix_customers_email_verify_token   ON customers(email_verify_token);
