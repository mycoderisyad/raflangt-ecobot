CREATE TABLE IF NOT EXISTS waste_site_reports (
    id BIGSERIAL PRIMARY KEY,
    user_phone TEXT NOT NULL REFERENCES users(phone_number),
    issue_type TEXT NOT NULL CHECK (issue_type IN ('illegal_dump', 'full_site')),
    status TEXT NOT NULL CHECK (status IN (
        'draft_waiting_photo', 'draft_waiting_location', 'new',
        'acknowledged', 'resolved', 'rejected', 'cancelled'
    )),
    latitude DOUBLE PRECISION CHECK (latitude BETWEEN -90 AND 90),
    longitude DOUBLE PRECISION CHECK (longitude BETWEEN -180 AND 180),
    photo_data BYTEA,
    photo_mime TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (
        (status = 'draft_waiting_photo' AND photo_data IS NULL AND latitude IS NULL AND longitude IS NULL)
        OR (status = 'draft_waiting_location' AND photo_data IS NOT NULL AND latitude IS NULL AND longitude IS NULL)
        OR (status IN ('new', 'acknowledged', 'resolved', 'rejected')
            AND photo_data IS NOT NULL AND latitude IS NOT NULL AND longitude IS NOT NULL)
        OR status = 'cancelled'
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_waste_site_reports_one_open_draft
    ON waste_site_reports(user_phone)
    WHERE status IN ('draft_waiting_photo', 'draft_waiting_location');
CREATE INDEX IF NOT EXISTS idx_waste_site_reports_status_created
    ON waste_site_reports(status, created_at DESC);
