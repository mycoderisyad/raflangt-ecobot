-- ============================================
-- EcoBot PostgreSQL Schema — Initial Migration
-- ============================================

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    phone_number TEXT UNIQUE NOT NULL,
    name TEXT,
    address TEXT,
    role TEXT DEFAULT 'warga' CHECK (role IN ('admin', 'koordinator', 'warga')),
    registration_status TEXT DEFAULT 'pending' CHECK (registration_status IN ('pending', 'registered', 'blocked')),
    first_seen TIMESTAMP DEFAULT NOW(),
    last_active TIMESTAMP DEFAULT NOW(),
    total_messages INTEGER DEFAULT 0,
    total_images INTEGER DEFAULT 0,
    points INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    preferences JSONB
);

CREATE TABLE IF NOT EXISTS collection_points (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('fixed', 'mobile', 'community')),
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    accepted_waste_types JSONB NOT NULL,
    schedule TEXT NOT NULL,
    contact TEXT,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS collection_schedules (
    id SERIAL PRIMARY KEY,
    location_name TEXT NOT NULL,
    address TEXT NOT NULL,
    schedule_day TEXT NOT NULL CHECK (schedule_day IN ('senin','selasa','rabu','kamis','jumat','sabtu','minggu')),
    schedule_time TEXT NOT NULL,
    waste_types JSONB NOT NULL,
    contact TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS waste_classifications (
    id SERIAL PRIMARY KEY,
    user_phone TEXT NOT NULL REFERENCES users(phone_number),
    waste_type TEXT NOT NULL CHECK (waste_type IN ('ORGANIK','ANORGANIK','B3','TIDAK_TERIDENTIFIKASI')),
    confidence REAL NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    image_url TEXT,
    classification_method TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_interactions (
    id SERIAL PRIMARY KEY,
    user_phone TEXT NOT NULL REFERENCES users(phone_number),
    interaction_type TEXT NOT NULL,
    message_content TEXT,
    response_content TEXT,
    success BOOLEAN DEFAULT TRUE,
    response_time REAL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    level TEXT NOT NULL,
    message TEXT NOT NULL,
    module TEXT,
    user_phone TEXT,
    extra_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_memory (
    id SERIAL PRIMARY KEY,
    user_phone TEXT NOT NULL REFERENCES users(phone_number),
    memory_key TEXT NOT NULL,
    memory_value TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (user_phone, memory_key)
);

CREATE TABLE IF NOT EXISTS conversation_history (
    id SERIAL PRIMARY KEY,
    user_phone TEXT NOT NULL REFERENCES users(phone_number),
    message_role TEXT NOT NULL CHECK (message_role IN ('user','assistant','system')),
    message_content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone_number);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_classifications_user_date ON waste_classifications(user_phone, created_at);
CREATE INDEX IF NOT EXISTS idx_interactions_user_date ON user_interactions(user_phone, created_at);
CREATE INDEX IF NOT EXISTS idx_logs_date ON system_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_memory_user ON user_memory(user_phone);
CREATE INDEX IF NOT EXISTS idx_conversation_user ON conversation_history(user_phone, created_at);
