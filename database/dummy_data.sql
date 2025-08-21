-- ============================================
-- EcoBot Database Dummy Data
-- Test data untuk development dan testing
-- ============================================

-- Clear existing data
DELETE FROM system_logs;
DELETE FROM user_interactions;
DELETE FROM waste_classifications;
DELETE FROM collection_schedules;
DELETE FROM collection_points;
DELETE FROM users;

-- Reset auto increment
DELETE FROM sqlite_sequence WHERE name IN ('users', 'waste_classifications', 'user_interactions', 'collection_schedules', 'system_logs');

-- ============================================
-- DUMMY USERS DATA
-- ============================================

-- Admin Users
INSERT INTO users (phone_number, name, address, role, registration_status, total_messages, total_images, points) VALUES
('6285156084435@c.us', 'Admin Utama', 'Kantor Desa Cukangkawung', 'admin', 'registered', 150, 25, 0),
('6287700001111@c.us', 'Pak Lurah', 'Kantor Kepala Desa', 'admin', 'registered', 89, 10, 0);

-- Koordinator Users
INSERT INTO users (phone_number, name, address, role, registration_status, total_messages, total_images, points) VALUES
('6281300002222@c.us', 'Koordinator RT 01', 'RT 01 RW 03 Cukangkawung', 'koordinator', 'registered', 245, 45, 150),
('6282200003333@c.us', 'Koordinator RT 02', 'RT 02 RW 03 Cukangkawung', 'koordinator', 'registered', 198, 38, 120),
('6283100004444@c.us', 'Koordinator RT 03', 'RT 03 RW 04 Cukangkawung', 'koordinator', 'registered', 167, 29, 95);

-- Warga Users (Regular Citizens)
INSERT INTO users (phone_number, name, address, role, registration_status, total_messages, total_images, points) VALUES
('6281234567890@c.us', 'Ibu Sari Wahyuni', 'Jl. Merdeka No. 15 RT 01', 'warga', 'registered', 67, 23, 230),
('6289876543210@c.us', 'Bapak Joko Susilo', 'Jl. Diponegoro No. 8 RT 02', 'warga', 'registered', 45, 18, 180),
('6287775551234@c.us', 'Ibu Fitri Handayani', 'Jl. Sudirman No. 22 RT 01', 'warga', 'registered', 89, 34, 340),
('6282225556789@c.us', 'Bapak Ahmad Fauzi', 'Jl. Gatot Subroto No. 5 RT 03', 'warga', 'registered', 123, 67, 670),
('6283335559876@c.us', 'Ibu Dewi Lestari', 'Jl. Pahlawan No. 12 RT 02', 'warga', 'registered', 78, 29, 290),
('6284445552468@c.us', 'Bapak Eko Prasetyo', 'Jl. Kartini No. 7 RT 03', 'warga', 'registered', 56, 21, 210),
('6285555551357@c.us', 'Ibu Nina Kurniawati', 'Jl. Cut Nyak Dien No. 18 RT 01', 'warga', 'registered', 92, 41, 410),
('6286666552580@c.us', 'Bapak Rudi Hartono', 'Jl. Hasanudin No. 3 RT 02', 'warga', 'registered', 34, 12, 120);

-- Pending Users
INSERT INTO users (phone_number, name, address, role, registration_status, total_messages, total_images, points) VALUES
('6287777771111@c.us', 'Calon Warga 1', NULL, 'warga', 'pending', 5, 0, 0),
('6288888882222@c.us', 'Calon Warga 2', NULL, 'warga', 'pending', 3, 0, 0);

-- ============================================
-- COLLECTION POINTS DATA
-- ============================================

INSERT INTO collection_points (id, name, type, latitude, longitude, accepted_waste_types, schedule, contact, description) VALUES
('cp_balai_desa', 'Balai Desa Cukangkawung', 'fixed', -6.845695, 107.155123, 
 '["ORGANIK", "ANORGANIK", "B3"]', 'Senin, Rabu, Jumat 07:00-16:00', 
 '0812-3456-7890', 'Titik pengumpulan utama di Balai Desa. Melayani semua jenis sampah.'),

('cp_rt01', 'Pos RT 01', 'community', -6.846123, 107.156789, 
 '["ORGANIK", "ANORGANIK"]', 'Selasa, Kamis, Sabtu 08:00-15:00', 
 '0813-1111-2222', 'Pos pengumpulan sampah komunitas RT 01'),

('cp_rt02', 'Pos RT 02', 'community', -6.847123, 107.157456, 
 '["ANORGANIK", "B3"]', 'Senin, Rabu, Jumat 08:00-15:00', 
 '0813-2222-3333', 'Pos pengumpulan sampah komunitas RT 02'),

('cp_rt03', 'Pos RT 03', 'community', -6.848456, 107.158123, 
 '["ORGANIK", "ANORGANIK"]', 'Selasa, Kamis, Sabtu 07:30-14:30', 
 '0813-3333-4444', 'Pos pengumpulan sampah komunitas RT 03'),

('cp_pasar_tradisional', 'Pasar Tradisional Cukangkawung', 'fixed', -6.849789, 107.159654, 
 '["ORGANIK"]', 'Setiap hari 06:00-18:00', 
 '0814-5555-6666', 'Khusus untuk sampah organik dari pasar tradisional'),

('cp_sekolah_dasar', 'SDN Cukangkawung 01', 'fixed', -6.847890, 107.160123, 
 '["ANORGANIK", "B3"]', 'Senin-Jumat 07:00-14:00', 
 '0815-7777-8888', 'Titik pengumpulan di sekolah untuk edukasi siswa'),

('cp_mobile_01', 'Mobil Sampah Keliling Area Utara', 'mobile', -6.844123, 107.154789, 
 '["ORGANIK", "ANORGANIK"]', 'Senin, Kamis 09:00-11:00', 
 '0816-9999-0000', 'Mobil sampah keliling untuk area utara desa');

-- ============================================
-- COLLECTION SCHEDULES DATA
-- ============================================

INSERT INTO collection_schedules (location_name, address, schedule_day, schedule_time, waste_types, contact) VALUES
('Area Jl. Merdeka', 'Jl. Merdeka RT 01 RW 03', 'senin', '07:00-09:00', '["ORGANIK", "ANORGANIK"]', '0812-1111-1111'),
('Area Jl. Merdeka', 'Jl. Merdeka RT 01 RW 03', 'kamis', '07:00-09:00', '["ORGANIK", "ANORGANIK"]', '0812-1111-1111'),

('Area Jl. Diponegoro', 'Jl. Diponegoro RT 02 RW 03', 'selasa', '08:00-10:00', '["ORGANIK", "ANORGANIK"]', '0812-2222-2222'),
('Area Jl. Diponegoro', 'Jl. Diponegoro RT 02 RW 03', 'jumat', '08:00-10:00', '["ORGANIK", "ANORGANIK"]', '0812-2222-2222'),

('Area Jl. Sudirman', 'Jl. Sudirman RT 01 RW 03', 'rabu', '07:30-09:30', '["ORGANIK", "ANORGANIK"]', '0812-3333-3333'),
('Area Jl. Sudirman', 'Jl. Sudirman RT 01 RW 03', 'sabtu', '07:30-09:30', '["ORGANIK", "ANORGANIK"]', '0812-3333-3333'),

('Area Jl. Gatot Subroto', 'Jl. Gatot Subroto RT 03 RW 04', 'senin', '09:00-11:00', '["ORGANIK", "ANORGANIK"]', '0812-4444-4444'),
('Area Jl. Gatot Subroto', 'Jl. Gatot Subroto RT 03 RW 04', 'kamis', '09:00-11:00', '["ORGANIK", "ANORGANIK"]', '0812-4444-4444'),

('Area Jl. Pahlawan', 'Jl. Pahlawan RT 02 RW 03', 'selasa', '08:30-10:30', '["ORGANIK", "ANORGANIK"]', '0812-5555-5555'),
('Area Jl. Pahlawan', 'Jl. Pahlawan RT 02 RW 03', 'jumat', '08:30-10:30', '["ORGANIK", "ANORGANIK"]', '0812-5555-5555'),

('Area Jl. Kartini', 'Jl. Kartini RT 03 RW 04', 'rabu', '08:00-10:00', '["ORGANIK", "ANORGANIK"]', '0812-6666-6666'),
('Area Jl. Kartini', 'Jl. Kartini RT 03 RW 04', 'sabtu', '08:00-10:00', '["ORGANIK", "ANORGANIK"]', '0812-6666-6666'),

-- Jadwal khusus sampah B3
('Seluruh Desa - Sampah B3', 'Seluruh wilayah Desa Cukangkawung', 'sabtu', '14:00-16:00', '["B3"]', '0812-7777-7777');

-- ============================================
-- WASTE CLASSIFICATIONS DATA
-- ============================================

INSERT INTO waste_classifications (user_phone, waste_type, confidence, image_url, classification_method) VALUES
-- User Ibu Sari classifications
('6281234567890@c.us', 'ORGANIK', 0.95, '/images/classifications/001.jpg', 'ai'),
('6281234567890@c.us', 'ANORGANIK', 0.87, '/images/classifications/002.jpg', 'ai'),
('6281234567890@c.us', 'ORGANIK', 0.92, '/images/classifications/003.jpg', 'ai'),
('6281234567890@c.us', 'ORGANIK', 0.89, NULL, 'user_input'),

-- User Bapak Joko classifications
('6289876543210@c.us', 'ANORGANIK', 0.91, '/images/classifications/004.jpg', 'ai'),
('6289876543210@c.us', 'B3', 0.78, '/images/classifications/005.jpg', 'ai'),
('6289876543210@c.us', 'ORGANIK', 0.94, '/images/classifications/006.jpg', 'ai'),

-- User Ibu Fitri classifications
('6287775551234@c.us', 'ORGANIK', 0.96, '/images/classifications/007.jpg', 'ai'),
('6287775551234@c.us', 'ORGANIK', 0.93, '/images/classifications/008.jpg', 'ai'),
('6287775551234@c.us', 'ANORGANIK', 0.85, '/images/classifications/009.jpg', 'ai'),
('6287775551234@c.us', 'ANORGANIK', 0.88, '/images/classifications/010.jpg', 'ai'),
('6287775551234@c.us', 'ORGANIK', 0.97, NULL, 'user_input'),

-- User Bapak Ahmad classifications (power user)
('6282225556789@c.us', 'ORGANIK', 0.94, '/images/classifications/011.jpg', 'ai'),
('6282225556789@c.us', 'ANORGANIK', 0.89, '/images/classifications/012.jpg', 'ai'),
('6282225556789@c.us', 'B3', 0.82, '/images/classifications/013.jpg', 'ai'),
('6282225556789@c.us', 'ORGANIK', 0.91, '/images/classifications/014.jpg', 'ai'),
('6282225556789@c.us', 'ANORGANIK', 0.86, '/images/classifications/015.jpg', 'ai'),
('6282225556789@c.us', 'ORGANIK', 0.95, '/images/classifications/016.jpg', 'ai'),
('6282225556789@c.us', 'ANORGANIK', 0.90, NULL, 'user_input'),
('6282225556789@c.us', 'ORGANIK', 0.92, NULL, 'user_input');

-- ============================================
-- USER INTERACTIONS DATA
-- ============================================

INSERT INTO user_interactions (user_phone, interaction_type, message_content, response_content, success, response_time) VALUES
-- Admin interactions
('6285156084435@c.us', 'admin_command', '/admin user_list', 'Menampilkan daftar 15 pengguna terdaftar', 1, 0.45),
('6285156084435@c.us', 'admin_command', '/admin stats', 'Statistik sistem: 15 users, 8 classifications hari ini', 1, 0.67),
('6285156084435@c.us', 'message', 'Status sistem hari ini gimana?', 'Sistem berjalan normal. 23 interaksi hari ini.', 1, 0.23),

-- Koordinator interactions
('6281300002222@c.us', 'message', 'Info jadwal pengumpulan RT 01', 'Jadwal RT 01: Senin & Kamis 07:00-09:00', 1, 0.34),
('6282200003333@c.us', 'image', NULL, 'Sampah terklasifikasi: ANORGANIK (86% confidence)', 1, 1.23),
('6283100004444@c.us', 'location', NULL, 'Lokasi terdekat: Pos RT 03 (150m)', 1, 0.56),

-- Regular user interactions
('6281234567890@c.us', 'message', 'Halo, mau tanya jadwal sampah', 'Halo! Jadwal pengumpulan Jl. Merdeka: Senin & Kamis 07:00-09:00', 1, 0.45),
('6281234567890@c.us', 'image', NULL, 'Sampah terklasifikasi: ORGANIK (95% confidence)', 1, 1.45),
('6281234567890@c.us', 'menu_selection', 'Lihat Lokasi', 'Lokasi terdekat: Pos RT 01 (200m dari Anda)', 1, 0.67),

('6289876543210@c.us', 'message', 'Sampah baterai dibuang dimana?', 'Sampah B3 seperti baterai bisa ke Balai Desa atau tunggu mobil khusus Sabtu 14:00-16:00', 1, 0.56),
('6289876543210@c.us', 'image', NULL, 'Sampah terklasifikasi: B3 (78% confidence)', 1, 1.67),

('6287775551234@c.us', 'message', 'Terima kasih infonya sangat membantu', 'Sama-sama! Jangan lupa buang sampah pada tempatnya ya', 1, 0.34),
('6287775551234@c.us', 'image', NULL, 'Sampah terklasifikasi: ORGANIK (96% confidence)', 1, 1.34),
('6287775551234@c.us', 'location', NULL, 'Lokasi terdekat: Pos RT 01 (180m)', 1, 0.45),

('6282225556789@c.us', 'message', 'Hari ini sudah buang sampah 3 kantong', 'Wah hebat! Poin Anda bertambah. Total poin: 670', 1, 0.23),
('6282225556789@c.us', 'image', NULL, 'Sampah terklasifikasi: ANORGANIK (89% confidence)', 1, 1.56),
('6282225556789@c.us', 'menu_selection', 'Lihat Poin', 'Poin Anda saat ini: 670. Ranking: 1 di RT 03!', 1, 0.45);

-- ============================================
-- SYSTEM LOGS DATA
-- ============================================

INSERT INTO system_logs (level, message, module, user_phone, extra_data) VALUES
('INFO', 'System started successfully', 'core.application', NULL, '{"version": "1.0.0", "environment": "production"}'),
('INFO', 'Database connection established', 'database.models', NULL, '{"database": "ecobot.db"}'),
('INFO', 'User classification request processed', 'services.ai_service', '6281234567890@c.us', '{"waste_type": "ORGANIK", "confidence": 0.95}'),
('INFO', 'Admin command executed successfully', 'core.admin_handler', '6285156084435@c.us', '{"command": "user_list", "execution_time": 0.45}'),
('WARNING', 'Low confidence classification detected', 'services.ai_service', '6289876543210@c.us', '{"waste_type": "B3", "confidence": 0.78}'),
('INFO', 'New user registered', 'services.registration_service', '6285555551357@c.us', '{"name": "Ibu Nina Kurniawati", "address": "Jl. Cut Nyak Dien No. 18 RT 01"}'),
('ERROR', 'Failed to process image', 'services.ai_service', '6286666552580@c.us', '{"error": "Image format not supported", "format": "gif"}'),
('INFO', 'Collection schedule updated', 'core.admin_handler', '6285156084435@c.us', '{"location": "Area Jl. Merdeka", "old_time": "08:00-10:00", "new_time": "07:00-09:00"}'),
('INFO', 'Daily statistics generated', 'services.feature_service', NULL, '{"total_users": 15, "active_today": 8, "classifications_today": 12}'),
('DEBUG', 'WhatsApp webhook received', 'services.whatsapp_service', '6282225556789@c.us', '{"message_type": "text", "content_length": 45}');

-- Update sequences to continue from current max values
UPDATE sqlite_sequence SET seq = (SELECT MAX(id) FROM users) WHERE name = 'users';
UPDATE sqlite_sequence SET seq = (SELECT MAX(id) FROM waste_classifications) WHERE name = 'waste_classifications';
UPDATE sqlite_sequence SET seq = (SELECT MAX(id) FROM user_interactions) WHERE name = 'user_interactions';
UPDATE sqlite_sequence SET seq = (SELECT MAX(id) FROM collection_schedules) WHERE name = 'collection_schedules';
UPDATE sqlite_sequence SET seq = (SELECT MAX(id) FROM system_logs) WHERE name = 'system_logs';
