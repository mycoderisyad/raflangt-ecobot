-- Only counters are stored. Search results remain transient.
CREATE TABLE IF NOT EXISTS web_search_quota (
    usage_day DATE NOT NULL,
    bucket TEXT NOT NULL,
    request_count INTEGER NOT NULL DEFAULT 0 CHECK (request_count >= 0),
    PRIMARY KEY (usage_day, bucket)
);
