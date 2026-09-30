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
SELECT seed.location_name, seed.address, seed.schedule_day, seed.schedule_time, seed.waste_types::jsonb, seed.contact
FROM (VALUES
    ('TPS Desa Utama', 'Jl. Raya Desa No. 1', 'Senin', '07:00-09:00', '["ORGANIK"]', 'Pak RT'),
    ('TPS Desa Utama', 'Jl. Raya Desa No. 1', 'Kamis', '07:00-09:00', '["ANORGANIK"]', 'Pak RT'),
    ('Bank Sampah RT 03', 'Jl. Melati No. 5', 'Sabtu', '08:00-12:00', '["ANORGANIK"]', 'Bu Ani')
) AS seed(location_name, address, schedule_day, schedule_time, waste_types, contact)
WHERE NOT EXISTS (
    SELECT 1 FROM collection_schedules existing
    WHERE existing.location_name = seed.location_name
      AND existing.address = seed.address
      AND existing.schedule_day = seed.schedule_day
      AND existing.schedule_time = seed.schedule_time
      AND existing.waste_types = seed.waste_types::jsonb
      AND COALESCE(existing.contact, '') = COALESCE(seed.contact, '')
);
