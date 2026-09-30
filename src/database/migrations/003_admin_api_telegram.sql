-- Add admin API fields while preserving the schedule information stored by the old panel.
ALTER TABLE collection_schedules ADD COLUMN IF NOT EXISTS notes TEXT;

UPDATE collection_schedules
SET notes = SUBSTRING(address FROM POSITION(' | Notes: ' IN address) + LENGTH(' | Notes: ')),
    address = SUBSTRING(address FROM 1 FOR POSITION(' | Notes: ' IN address) - 1)
WHERE notes IS NULL AND POSITION(' | Notes: ' IN address) > 0;

CREATE TABLE IF NOT EXISTS telegram_updates (
    update_id BIGINT PRIMARY KEY,
    status TEXT NOT NULL CHECK (status IN ('processed')),
    processed_at TIMESTAMP NOT NULL DEFAULT NOW()
);
