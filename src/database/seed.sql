-- ============================================
-- EcoBot v2 — Seed Data
-- ============================================

-- Sample collection points
INSERT INTO collection_points (id, name, type, latitude, longitude, accepted_waste_types, schedule, contact, description)
VALUES
    ('cp-001', 'TPS Desa Utama', 'fixed', -6.9175, 107.6191, '["ORGANIK","ANORGANIK"]', 'Senin-Jumat 07:00-15:00', '', 'Tempat pembuangan utama desa'),
    ('cp-002', 'Bank Sampah RT 03', 'community', -6.9180, 107.6200, '["ANORGANIK"]', 'Sabtu 08:00-12:00', '', 'Bank sampah warga RT 03')
ON CONFLICT (id) DO NOTHING;

-- Sample collection schedules
INSERT INTO collection_schedules (location_name, address, schedule_day, schedule_time, waste_types, contact)
VALUES
    ('TPS Desa Utama', 'Jl. Raya Desa No. 1', 'Senin', '07:00-09:00', '["ORGANIK"]', 'Pak RT'),
    ('TPS Desa Utama', 'Jl. Raya Desa No. 1', 'Kamis', '07:00-09:00', '["ANORGANIK"]', 'Pak RT'),
    ('Bank Sampah RT 03', 'Jl. Melati No. 5', 'Sabtu', '08:00-12:00', '["ANORGANIK"]', 'Bu Ani')
ON CONFLICT DO NOTHING;
