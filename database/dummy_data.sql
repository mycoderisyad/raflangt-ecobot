-- ============================================================================
-- EcoBot Database - Dummy Data
-- ============================================================================
-- File: database/dummy_data.sql
-- Description: Sample data for testing EcoBot features
-- Created: 2025-01-24
-- ============================================================================

-- Clear existing data (optional - uncomment if needed)
-- DELETE FROM users WHERE phone_number IN ('+6281234567890', '+6282345678901', '+6283456789012', '+6284567890123', '+6285678901234');
-- DELETE FROM collection_points WHERE id IN ('CP001', 'CP002', 'CP003', 'CP004', 'CP005');

-- ============================================================================
-- 1. USERS - Sample users with different roles
-- ============================================================================
INSERT OR REPLACE INTO users (
    phone_number, 
    name, 
    address, 
    registration_status, 
    points, 
    first_seen, 
    last_active, 
    total_messages, 
    total_images, 
    role, 
    is_active, 
    preferences
) VALUES 
    ('+6281234567890', 'Budi Santoso', 'Jl. Kampung Hijau No. 12', 'registered', 150, '2025-01-15 08:00:00', '2025-01-24 15:30:00', 25, 8, 'warga', 1, '{"language": "id", "notifications": true}'),
    ('+6282345678901', 'Siti Rahmawati', 'Jl. Kampung Hijau No. 25', 'registered', 320, '2025-01-10 09:15:00', '2025-01-24 14:20:00', 42, 15, 'koordinator', 1, '{"language": "id", "notifications": true}'),
    ('+6283456789012', 'Ahmad Hidayat', 'Jl. Kampung Hijau No. 8', 'registered', 85, '2025-01-18 10:30:00', '2025-01-24 16:45:00', 18, 5, 'warga', 1, '{"language": "id", "notifications": false}'),
    ('+6284567890123', 'Dewi Sartika', 'Jl. Kampung Hijau No. 45', 'registered', 500, '2025-01-05 07:00:00', '2025-01-24 17:00:00', 65, 22, 'admin', 1, '{"language": "id", "notifications": true}'),
    ('+6285678901234', 'Rudi Hermawan', 'Jl. Kampung Hijau No. 33', 'registered', 95, '2025-01-20 11:45:00', '2025-01-24 13:15:00', 22, 7, 'warga', 1, '{"language": "id", "notifications": true}');

-- ============================================================================
-- 2. COLLECTION POINTS - Sample waste collection locations
-- ============================================================================
INSERT OR REPLACE INTO collection_points (
    id, 
    name, 
    type, 
    latitude, 
    longitude, 
    accepted_waste_types, 
    schedule, 
    contact, 
    description
) VALUES 
    ('CP001', 'Bank Sampah Kampung Hijau', 'bank_sampah', -6.2088, 106.8456, '["organik", "plastik", "kertas"]', 'Senin-Jumat 08:00-17:00', '+6281234567890', 'Bank sampah utama kampung'),
    ('CP002', 'Tempat Sampah Terpadu RT 05', 'tempat_sampah', -6.2090, 106.8458, '["organik", "anorganik"]', 'Setiap hari 06:00-22:00', '+6282345678901', 'Tempat sampah terpadu RT 05'),
    ('CP003', 'Bank Sampah Sekolah SDN 01', 'bank_sampah', -6.2085, 106.8450, '["organik", "kertas", "plastik"]', 'Senin-Jumat 07:00-15:00', '+6283456789012', 'Bank sampah sekolah'),
    ('CP004', 'Tempat Sampah Pasar Tradisional', 'tempat_sampah', -6.2095, 106.8460, '["organik", "anorganik"]', 'Setiap hari 05:00-20:00', '+6284567890123', 'Tempat sampah pasar'),
    ('CP005', 'Bank Sampah Masjid Al-Hikmah', 'bank_sampah', -6.2080, 106.8445, '["organik", "kertas", "plastik"]', 'Setiap hari 06:00-21:00', '+6285678901234', 'Bank sampah masjid');

-- ============================================================================
-- 3. COLLECTION SCHEDULES - Sample collection schedules
-- ============================================================================
INSERT OR REPLACE INTO collection_schedules (
    location_name, 
    address, 
    schedule_day, 
    schedule_time, 
    waste_types, 
    contact
) VALUES 
    ('Bank Sampah Kampung Hijau', 'Jl. Raya Kampung Hijau No. 45', 'Senin', '08:00-12:00', '["organik", "plastik"]', '+6281234567890'),
    ('Tempat Sampah RT 05', 'Jl. Kampung Hijau RT 05', 'Selasa', '14:00-18:00', '["anorganik"]', '+6282345678901'),
    ('Bank Sampah Sekolah', 'Jl. Pendidikan No. 12', 'Rabu', '09:00-11:00', '["organik", "kertas"]', '+6283456789012'),
    ('Tempat Sampah Pasar', 'Jl. Pasar Kampung Hijau', 'Kamis', '16:00-20:00', '["organik", "anorganik"]', '+6284567890123'),
    ('Bank Sampah Masjid', 'Jl. Masjid No. 8', 'Jumat', '07:00-10:00', '["organik", "kertas"]', '+6285678901234');

-- ============================================================================
-- 4. WASTE CLASSIFICATIONS - Sample AI analysis results
-- ============================================================================
INSERT OR REPLACE INTO waste_classifications (
    user_phone, 
    waste_type, 
    confidence, 
    image_url, 
    classification_method, 
    created_at
) VALUES 
    ('+6281234567890', 'organik', 0.95, 'https://example.com/image1.jpg', 'AI_analysis', '2025-01-24 15:30:00'),
    ('+6282345678901', 'plastik', 0.88, 'https://example.com/image2.jpg', 'AI_analysis', '2025-01-24 14:20:00'),
    ('+6283456789012', 'kertas', 0.92, 'https://example.com/image3.jpg', 'AI_analysis', '2025-01-24 16:45:00'),
    ('+6284567890123', 'logam', 0.87, 'https://example.com/image4.jpg', 'AI_analysis', '2025-01-24 17:00:00'),
    ('+6285678901234', 'organik', 0.94, 'https://example.com/image5.jpg', 'AI_analysis', '2025-01-24 13:15:00');

-- ============================================================================
-- 5. USER MEMORY - Sample user facts for AI agent
-- ============================================================================
INSERT OR REPLACE INTO user_memory (
    user_phone, 
    memory_key, 
    memory_value
) VALUES 
    ('+6281234567890', 'user_name', 'Budi'),
    ('+6281234567890', 'preferred_language', 'Bahasa Indonesia'),
    ('+6281234567890', 'location', 'Kampung Hijau'),
    ('+6282345678901', 'user_name', 'Siti'),
    ('+6282345678901', 'role', 'koordinator'),
    ('+6282345678901', 'interests', 'pengelolaan sampah'),
    ('+6283456789012', 'user_name', 'Ahmad'),
    ('+6283456789012', 'location', 'RT 08'),
    ('+6284567890123', 'user_name', 'Dewi'),
    ('+6284567890123', 'role', 'admin'),
    ('+6285678901234', 'user_name', 'Rudi'),
    ('+6285678901234', 'location', 'RT 05');

-- ============================================================================
-- 6. CONVERSATION HISTORY - Sample chat history for AI context
-- ============================================================================
INSERT OR REPLACE INTO conversation_history (
    user_phone, 
    message_role, 
    message_content
) VALUES 
    ('+6281234567890', 'user', 'Halo, nama saya Budi'),
    ('+6281234567890', 'assistant', 'Halo Budi! Senang berkenalan denganmu. Saya EcoBot, asisten pengelolaan sampah.'),
    ('+6281234567890', 'user', 'Bagaimana cara memilah sampah organik?'),
    ('+6281234567890', 'assistant', 'Sampah organik adalah sisa makanan, daun-daunan, dan bahan yang dapat terurai. Kamu bisa jadikan kompos.'),
    ('+6282345678901', 'user', 'Dimana lokasi bank sampah terdekat?'),
    ('+6282345678901', 'assistant', 'Bank sampah terdekat ada di Jl. Raya Kampung Hijau No. 45, buka Senin-Jumat 08:00-17:00.'),
    ('+6283456789012', 'user', 'Kapan jadwal pengumpulan sampah?'),
    ('+6283456789012', 'assistant', 'Jadwal pengumpulan sampah di RT 05 setiap Selasa 14:00-18:00 untuk sampah anorganik.'),
    ('+6284567890123', 'user', 'Generate report aktivitas user'),
    ('+6284567890123', 'assistant', 'Laporan aktivitas user berhasil dibuat. Total 5 user aktif dengan 150+ interaksi hari ini.'),
    ('+6285678901234', 'user', 'Bagaimana cara daur ulang plastik?'),
    ('+6285678901234', 'assistant', 'Plastik bisa didaur ulang menjadi berbagai produk. Pastikan bersih dan kering sebelum disetor ke bank sampah.');

-- ============================================================================
-- 7. SYSTEM LOGS - Sample system activity logs
-- ============================================================================
INSERT OR REPLACE INTO system_logs (
    level, 
    message, 
    module
) VALUES 
    ('INFO', 'User +6281234567890 berhasil terdaftar', 'User registration'),
    ('INFO', 'Analisis gambar sampah organik berhasil dengan confidence 95%', 'Image analysis'),
    ('INFO', 'Query jadwal pengumpulan sampah untuk RT 05', 'Schedule query'),
    ('INFO', 'Laporan admin berhasil dibuat dan dikirim via email', 'Report generation'),
    ('INFO', 'Query lokasi bank sampah terdekat untuk user +6282345678901', 'Location query'),
    ('INFO', 'AI Agent berhasil memberikan respons kontekstual untuk user +6281234567890', 'AI response'),
    ('INFO', 'User fact updated: user_name = Budi untuk +6281234567890', 'Memory update'),
    ('INFO', 'Backup database berhasil dibuat', 'Database backup');

-- ============================================================================
-- 8. CHAT MESSAGES - Sample WhatsApp messages (if table exists)
-- ============================================================================
-- Note: Uncomment if chat_messages table exists
/*
INSERT OR REPLACE INTO chat_messages (
    user_phone, 
    message_type, 
    content, 
    timestamp, 
    status
) VALUES 
    ('+6281234567890', 'text', 'Halo EcoBot', '2025-01-24 15:30:00', 'received'),
    ('+6281234567890', 'text', 'Bagaimana cara memilah sampah?', '2025-01-24 15:35:00', 'received'),
    ('+6282345678901', 'image', 'Foto sampah organik', '2025-01-24 14:20:00', 'received'),
    ('+6283456789012', 'text', 'Jadwal pengumpulan sampah', '2025-01-24 16:45:00', 'received'),
    ('+6284567890123', 'admin', 'Generate report', '2025-01-24 17:00:00', 'received');
*/

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
-- Uncomment to verify data insertion
/*
SELECT 'Users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'Collection Points', COUNT(*) FROM collection_points
UNION ALL
SELECT 'Collection Schedules', COUNT(*) FROM collection_schedules
UNION ALL
SELECT 'Waste Classifications', COUNT(*) FROM waste_classifications
UNION ALL
SELECT 'User Memory', COUNT(*) FROM user_memory
UNION ALL
SELECT 'Conversation History', COUNT(*) FROM conversation_history
UNION ALL
SELECT 'System Logs', COUNT(*) FROM system_logs;
*/

-- ============================================================================
-- END OF DUMMY DATA
-- ============================================================================
-- Total records: 40+ sample records across 7 tables
-- Use: sqlite3 database/ecobot.db < database/dummy_data.sql
-- ============================================================================
