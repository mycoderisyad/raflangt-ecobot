ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_username TEXT;

CREATE INDEX IF NOT EXISTS idx_users_telegram_username
    ON users(LOWER(telegram_username))
    WHERE telegram_username IS NOT NULL;
