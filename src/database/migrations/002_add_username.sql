-- ============================================
-- EcoBot Migration 002 — Add username column & default preferences
-- ============================================

ALTER TABLE users ADD COLUMN IF NOT EXISTS username TEXT;

-- Set default preferences for existing users (reminder enabled by default)
UPDATE users SET preferences = '{"reminder_enabled": true}'::jsonb
WHERE preferences IS NULL;
