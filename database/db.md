# EcoBot Database Documentation

## Overview
Database management system untuk EcoBot - Sistem Pengelolaan Sampah .

## File Structure
```
database/
├── ecobot.db              # Database utama SQLite
├── schema.sql             # Schema database lengkap
├── dummy_data.sql         # Data dummy untuk testing
├── db_manager.sh          # Script management database
├── backups/              # Folder backup otomatis
└── README.md             # Dokumentasi ini
```

## Database Schema

### 1. Table: users
Mengelola akun pengguna dan role

**Columns:**
- `id` (PRIMARY KEY): Auto increment ID
- `phone_number` (UNIQUE): Nomor WhatsApp (format: 628xxx@c.us)
- `name`: Nama lengkap pengguna
- `address`: Alamat lengkap
- `role`: admin | koordinator | warga
- `registration_status`: pending | registered | blocked
- `first_seen`: Timestamp pertama kali dilihat
- `last_active`: Timestamp terakhir aktif
- `total_messages`: Total pesan yang dikirim
- `total_images`: Total gambar yang dikirim
- `points`: Poin reward pengguna
- `is_active`: Status aktif (boolean)
- `preferences`: JSON string untuk preferensi

**Indexes:**
- `idx_users_phone`: Index pada phone_number
- `idx_users_role`: Index pada role
- `idx_users_status`: Index pada registration_status

### 2. Table: collection_points
Titik pengumpulan sampah tetap

**Columns:**
- `id` (PRIMARY KEY): ID unik (string)
- `name`: Nama lokasi
- `type`: fixed | mobile | community
- `latitude`: Koordinat GPS latitude
- `longitude`: Koordinat GPS longitude
- `accepted_waste_types`: JSON array jenis sampah
- `schedule`: String jadwal operasional
- `contact`: Nomor kontak penanggung jawab
- `description`: Deskripsi lokasi
- `is_active`: Status aktif
- `created_at`: Timestamp dibuat
- `updated_at`: Timestamp diupdate

### 3. Table: collection_schedules
Jadwal pengumpulan sampah mobile

**Columns:**
- `id` (PRIMARY KEY): Auto increment ID
- `location_name`: Nama area/lokasi
- `address`: Alamat lengkap
- `schedule_day`: senin | selasa | rabu | kamis | jumat | sabtu | minggu
- `schedule_time`: Format "HH:MM-HH:MM"
- `waste_types`: JSON array jenis sampah
- `contact`: Nomor kontak
- `is_active`: Status aktif
- `created_at`: Timestamp dibuat
- `updated_at`: Timestamp diupdate

### 4. Table: waste_classifications
Hasil klasifikasi sampah AI dan user

**Columns:**
- `id` (PRIMARY KEY): Auto increment ID
- `user_phone`: Nomor WhatsApp user (FOREIGN KEY)
- `waste_type`: ORGANIK | ANORGANIK | B3 | TIDAK_TERIDENTIFIKASI
- `confidence`: Tingkat kepercayaan AI (0.0-1.0)
- `image_url`: Path/URL gambar
- `classification_method`: ai | manual | user_input
- `created_at`: Timestamp klasifikasi

### 5. Table: user_interactions
Track semua interaksi pengguna

**Columns:**
- `id` (PRIMARY KEY): Auto increment ID
- `user_phone`: Nomor WhatsApp (FOREIGN KEY)
- `interaction_type`: message | image | location | menu_selection | admin_command
- `message_content`: Isi pesan
- `response_content`: Isi respons
- `success`: Status berhasil (boolean)
- `response_time`: Waktu respons (detik)
- `created_at`: Timestamp interaksi

### 6. Table: system_logs
Log sistem untuk debugging

**Columns:**
- `id` (PRIMARY KEY): Auto increment ID
- `level`: DEBUG | INFO | WARNING | ERROR | CRITICAL
- `message`: Pesan log
- `module`: Nama modul/file
- `user_phone`: User terkait (optional)
- `extra_data`: JSON string data tambahan
- `created_at`: Timestamp log

## Database Management

### Script: db_manager.sh

**Commands:**
```bash
# Initialize new database
./db_manager.sh init

# Reset database (backup + recreate)
./db_manager.sh reset

# Load dummy data
./db_manager.sh seed

# Create backup
./db_manager.sh backup

# Restore from backup
./db_manager.sh restore

# Show status and statistics
./db_manager.sh status

# Test database integrity
./db_manager.sh test

# Show help
./db_manager.sh help
```

### Manual Database Operations

**Connect to database:**
```bash
sqlite3 /home/azureuser/ecobot/database/ecobot.db
```

**Common queries:**

1. **Check user roles:**
```sql
SELECT role, COUNT(*) FROM users GROUP BY role;
```

2. **Get active collection points:**
```sql
SELECT name, type, latitude, longitude 
FROM collection_points 
WHERE is_active = 1;
```

3. **Daily classification stats:**
```sql
SELECT waste_type, COUNT(*) 
FROM waste_classifications 
WHERE DATE(created_at) = DATE('now') 
GROUP BY waste_type;
```

4. **User activity today:**
```sql
SELECT COUNT(DISTINCT user_phone) as active_users
FROM user_interactions 
WHERE DATE(created_at) = DATE('now');
```

5. **System errors today:**
```sql
SELECT message, module, created_at 
FROM system_logs 
WHERE level = 'ERROR' 
AND DATE(created_at) = DATE('now');
```

## Data Dummy

File `dummy_data.sql` berisi:
- **15 users**: 2 admin, 3 koordinator, 10 warga
- **7 collection points**: Berbagai jenis dan lokasi
- **13 collection schedules**: Jadwal pengumpulan per area
- **20 waste classifications**: Contoh hasil klasifikasi
- **17 user interactions**: Berbagai jenis interaksi
- **10 system logs**: Log sistem dengan berbagai level

## Backup Strategy

### Automatic Backups
- Backup dibuat otomatis saat reset database
- Format nama: `ecobot_backup_YYYYMMDD_HHMMSS.db`
- Lokasi: `/home/azureuser/ecobot/database/backups/`

### Manual Backup
```bash
# Create backup
./db_manager.sh backup

# List backups
ls -la /home/azureuser/ecobot/database/backups/

# Restore specific backup
cp /path/to/backup.db /home/azureuser/ecobot/database/ecobot.db
```

### Database Maintenance

#### Daily Tasks
1. Check system logs untuk errors:
```bash
./db_manager.sh status
```

2. Monitor user activity dan classifications

#### Weekly Tasks
1. Create manual backup:
```bash
./db_manager.sh backup
```

2. Clean old logs (>30 days):
```sql
DELETE FROM system_logs 
WHERE created_at < DATE('now', '-30 days');
```

3. Check database integrity:
```bash
./db_manager.sh test
```

#### Monthly Tasks
1. Analyze user statistics
2. Update collection schedules jika perlu
3. Archive old data jika database terlalu besar

## Troubleshooting

### Common Issues

1. **Database locked error:**
```bash
# Stop EcoBot service
pkill -f "python3 start.py"
# Wait a moment, then restart
python3 start.py
```

2. **Corrupted database:**
```bash
# Restore from backup
./db_manager.sh restore
```

3. **Performance issues:**
```bash
# Check database size
du -h database/ecobot.db

# Vacuum database
sqlite3 database/ecobot.db "VACUUM;"
```

4. **Missing tables/data:**
```bash
# Test database structure
./db_manager.sh test

# If corrupted, reset with dummy data
./db_manager.sh reset
```

### Recovery Procedures

1. **Complete database recovery:**
```bash
# Stop service
pkill -f "python3 start.py"

# Backup current (if possible)
./db_manager.sh backup

# Reset with clean schema and data
./db_manager.sh reset

# Restart service
python3 start.py
```

2. **Partial data recovery:**
```bash
# Export specific table
sqlite3 database/ecobot.db ".mode csv" ".headers on" ".output users_backup.csv" "SELECT * FROM users;"

# Reset database
./db_manager.sh reset

# Import critical data manually
```

## Performance Monitoring

### Key Metrics
- Total users by role
- Daily active users
- Classification accuracy
- Response times
- Error rates

### Query Performance
- All tables have appropriate indexes
- Use EXPLAIN QUERY PLAN untuk optimize
- Monitor slow queries di logs

### Storage Management
- Regular vacuum untuk kompaksi
- Archive old data sesuai kebutuhan
- Monitor disk space usage

## Security Considerations

1. **File Permissions:**
```bash
chmod 644 database/ecobot.db
chmod 600 database/backups/*.db
```

2. **Access Control:**
- Hanya EcoBot service yang akses database
- Backup files limited access
- No direct database exposure

3. **Data Privacy:**
- Phone numbers sebagai identifiers
- No sensitive personal data stored
- GDPR compliance untuk user deletion

## Integration dengan EcoBot

### Database Models
- `UserModel` → users table
- `CollectionPointModel` → collection_points table
- `SystemModel` → system_logs, user_interactions

### Admin Commands
- Semua admin commands menggunakan database
- Real-time statistics dari database
- User management via database operations

### API Integration
- WhatsApp webhooks update user_interactions
- AI classification results ke waste_classifications
- System events ke system_logs
