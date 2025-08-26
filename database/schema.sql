-- ============================================
-- EcoBot Database Schema
--  Waste Management System
-- ============================================

-- Drop tables if they exist (for clean reinstall)
DROP TABLE IF EXISTS system_logs;
DROP TABLE IF EXISTS user_interactions;
DROP TABLE IF EXISTS waste_classifications;
DROP TABLE IF EXISTS collection_schedules;
DROP TABLE IF EXISTS collection_points;
DROP TABLE IF EXISTS users;

-- ============================================
-- TABLE: users
-- Manages user accounts and roles
-- ============================================
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone_number TEXT UNIQUE NOT NULL,
    name TEXT,
    address TEXT,
    role TEXT DEFAULT 'warga' CHECK (role IN ('admin', 'koordinator', 'warga')),
    registration_status TEXT DEFAULT 'pending' CHECK (registration_status IN ('pending', 'registered', 'blocked')),
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_messages INTEGER DEFAULT 0,
    total_images INTEGER DEFAULT 0,
    points INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    preferences TEXT  -- JSON string for user preferences
);

-- ============================================
-- TABLE: collection_points
-- Fixed collection points with GPS coordinates
-- ============================================
CREATE TABLE collection_points (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('fixed', 'mobile', 'community')),
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    accepted_waste_types TEXT NOT NULL,  -- JSON array: ["ORGANIK", "ANORGANIK", "B3"]
    schedule TEXT NOT NULL,              -- Format: "Senin, Rabu, Jumat 07:00-16:00"
    contact TEXT,
    description TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TABLE: collection_schedules
-- Mobile collection schedules by area
-- ============================================
CREATE TABLE collection_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    location_name TEXT NOT NULL,
    address TEXT NOT NULL,
    schedule_day TEXT NOT NULL CHECK (schedule_day IN ('senin', 'selasa', 'rabu', 'kamis', 'jumat', 'sabtu', 'minggu')),
    schedule_time TEXT NOT NULL,         -- Format: "07:00-09:00"
    waste_types TEXT NOT NULL,           -- JSON array
    contact TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TABLE: waste_classifications
-- AI classification results and user submissions
-- ============================================
CREATE TABLE waste_classifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_phone TEXT NOT NULL,
    waste_type TEXT NOT NULL CHECK (waste_type IN ('ORGANIK', 'ANORGANIK', 'B3', 'TIDAK_TERIDENTIFIKASI')),
    confidence REAL NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    image_url TEXT,
    classification_method TEXT CHECK (classification_method IN ('ai', 'manual', 'user_input')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_phone) REFERENCES users (phone_number)
);

-- ============================================
-- TABLE: user_interactions
-- Track all user interactions for analytics
-- ============================================
CREATE TABLE user_interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_phone TEXT NOT NULL,
    interaction_type TEXT NOT NULL CHECK (interaction_type IN ('message', 'image', 'location', 'menu_selection', 'admin_command')),
    message_content TEXT,
    response_content TEXT,
    success BOOLEAN DEFAULT 1,
    response_time REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_phone) REFERENCES users (phone_number)
);

-- ============================================
-- TABLE: system_logs
-- System logging for debugging and monitoring
-- ============================================
CREATE TABLE system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT NOT NULL CHECK (level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    message TEXT NOT NULL,
    module TEXT,
    user_phone TEXT,
    extra_data TEXT,  -- JSON string
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- INDEXES for Performance
-- ============================================
CREATE INDEX idx_users_phone ON users (phone_number);
CREATE INDEX idx_users_role ON users (role);
CREATE INDEX idx_users_status ON users (registration_status);
CREATE INDEX idx_classifications_user_date ON waste_classifications (user_phone, created_at);
CREATE INDEX idx_classifications_type ON waste_classifications (waste_type);
CREATE INDEX idx_interactions_user_date ON user_interactions (user_phone, created_at);
CREATE INDEX idx_interactions_type ON user_interactions (interaction_type);
CREATE INDEX idx_collection_points_active ON collection_points (is_active);
CREATE INDEX idx_collection_schedules_day ON collection_schedules (schedule_day);
CREATE INDEX idx_logs_date ON system_logs (created_at);
CREATE INDEX idx_logs_level ON system_logs (level);

-- ============================================
-- TRIGGERS for Maintenance
-- ============================================

-- Update last_active when user interacts
CREATE TRIGGER update_user_last_active
    AFTER INSERT ON user_interactions
    BEGIN
        UPDATE users 
        SET last_active = CURRENT_TIMESTAMP,
            total_messages = total_messages + 
                CASE WHEN NEW.interaction_type IN ('message', 'menu_selection') THEN 1 ELSE 0 END,
            total_images = total_images + 
                CASE WHEN NEW.interaction_type = 'image' THEN 1 ELSE 0 END
        WHERE phone_number = NEW.user_phone;
    END;

-- Update collection_points updated_at on changes
CREATE TRIGGER update_collection_points_timestamp
    AFTER UPDATE ON collection_points
    BEGIN
        UPDATE collection_points 
        SET updated_at = CURRENT_TIMESTAMP 
        WHERE id = NEW.id;
    END;

-- Update collection_schedules updated_at on changes
CREATE TRIGGER update_collection_schedules_timestamp
    AFTER UPDATE ON collection_schedules
    BEGIN
        UPDATE collection_schedules 
        SET updated_at = CURRENT_TIMESTAMP 
        WHERE id = NEW.id;
    END;
