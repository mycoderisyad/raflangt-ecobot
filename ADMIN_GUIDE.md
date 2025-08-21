# PANDUAN ADMIN ECOBOT

## Overview
Sistem EcoBot memiliki 3 level role dengan hak akses yang berbeda:

### ROLE SYSTEM:
- ADMIN: Full access - CRUD semua data, user management, system monitoring
- KOORDINATOR: Moderate access - View statistics, manage collection points
- WARGA: Basic access - Classification, education, location services

---

## ADMIN COMMANDS

### USER MANAGEMENT

#### List All Users
```
/admin user_list
```
Menampilkan semua user terdaftar, dikelompokkan berdasarkan role.

#### Add New User
```
/admin user_add <phone> <name> [role]
```
Contoh:
- `/admin user_add +6281234567890 "John Doe" koordinator`
- `/admin user_add 08123456789 "Jane Smith"` (default: warga)

#### Delete User
```
/admin user_delete <phone>
```
Contoh: `/admin user_delete +6281234567890`
Catatan: Admin tidak bisa menghapus admin lain (safety)

#### Change User Role
```
/admin user_role <phone> <new_role>
```
Contoh: `/admin user_role +6281234567890 koordinator`
Role tersedia: admin, koordinator, warga

#### User Info Detail
```
/admin user_info <phone>
```
Menampilkan informasi lengkap user + statistik aktivitas

---

### COLLECTION POINT MANAGEMENT

#### List Collection Points
```
/admin point_list
```
Menampilkan semua titik pengumpulan dengan status dan info lengkap.

#### Add Collection Point
```
/admin point_add "<name>" "<address>" "<lat,lng>" "<waste_types>"
```
Contoh:
```
/admin point_add "TPS Utama" "Jl. Merdeka No.123" "-6.123,106.456" "organik,anorganik"
```

Jenis sampah yang valid:
- `organik` - Sisa makanan, daun, kulit buah
- `anorganik` - Plastik, kaleng, kertas, kaca  
- `b3` - Bahan Berbahaya dan Beracun

#### Delete Collection Point
```
/admin point_delete <point_id>
```
Contoh: `/admin point_delete cp_20250821_123456`

#### Update Collection Point
```
/admin point_update <point_id> <field> <value>
```
Field yang bisa diubah:
- `name` - Nama titik pengumpulan
- `address` - Alamat lengkap
- `hours` - Jam operasional (contoh: "07:00-16:00")
- `contact` - Info kontak/PIC
- `status` - Status aktif/nonaktif (aktif/nonaktif)

Contoh:
```
/admin point_update cp_20250821_123456 hours "08:00-17:00"
/admin point_update cp_20250821_123456 status nonaktif
```

---

### SYSTEM MONITORING

#### System Statistics
```
/admin stats
```
Menampilkan statistik lengkap:
- Jumlah user per role
- User aktif hari ini
- Total pesan & foto dianalisis
- Status titik pengumpulan
- Status sistem & uptime

#### System Logs
```
/admin logs [level]
```
Level yang tersedia: INFO, WARNING, ERROR, CRITICAL, ALL

Contoh:
- `/admin logs` (semua log)
- `/admin logs ERROR` (hanya error)

---

### SYSTEM ADMINISTRATION

#### Database Backup
```
/admin backup
```
Membuat backup database dengan timestamp.

#### Reset Statistics
```
/admin reset_stats
```
Reset semua counter statistik (data user tetap aman).

#### Broadcast Message
```
/admin broadcast <message>
```
Kirim pengumuman ke semua user terdaftar.

Contoh:
```
/admin broadcast "Sistem maintenance hari Minggu pukul 02:00 WIB"
```

---

## SECURITY & PERMISSIONS

### Admin Access Control
- Hanya user dengan role `admin` yang bisa menggunakan `/admin` commands
- Admin phones didefinisikan di environment variable `ADMIN_PHONE_NUMBERS`
- Safety mechanism: Admin tidak bisa menghapus admin lain

### Admin Phone Setup
Di file `.env`:
```env
ADMIN_PHONE_NUMBERS=+6281234567890,+6287654321098
KOORDINATOR_PHONE_NUMBERS=+6281234567892,+6281234567893
```

### Auto Role Assignment
- User dengan nomor di `ADMIN_PHONE_NUMBERS` otomatis jadi admin
- User dengan nomor di `KOORDINATOR_PHONE_NUMBERS` otomatis jadi koordinator
- User lain default role: `warga`

---

## USAGE EXAMPLES

### Setup Awal Admin
```
1. /admin user_list
   (Cek user yang sudah terdaftar)

2. /admin user_add +6281234567892 "Pak RT" koordinator
   (Tambah koordinator baru)

3. /admin point_add "TPS Desa" "Balai Desa Cukangkawung" "-6.123,106.456" "organik,anorganik,b3"
   (Tambah titik pengumpulan utama)

4. /admin stats
   (Cek statistik sistem)
```

### Daily Monitoring
```
1. /admin stats
   (Monitor aktivitas harian)

2. /admin logs ERROR
   (Cek ada error tidak)

3. /admin user_list
   (Monitor pertumbuhan user)
```

### Maintenance Tasks
```
1. /admin backup
   (Backup rutin data)

2. /admin reset_stats
   (Reset counter bulanan)

3. /admin broadcast "Maintenance selesai, sistem normal kembali"
   (Informasi ke user)
```

---

## TROUBLESHOOTING

### "Akses ditolak"
- Pastikan nomor HP Anda terdaftar di `ADMIN_PHONE_NUMBERS`
- Restart service setelah mengubah environment variables

### "User tidak ditemukan"
- Gunakan format nomor HP yang konsisten (+62xxx atau 08xxx)
- Cek dengan `/admin user_list` apakah user ada

### "Format tidak valid"
- Perhatikan tanda kutip pada nama dan alamat
- Koordinat harus format: `lat,lng` (pakai koma, tidak ada spasi)
- Jenis sampah dipisah koma: `organik,anorganik`

---

## SUPPORT

Jika ada masalah dengan sistem admin:
1. Cek logs dengan `/admin logs ERROR`
2. Restart service: `sudo systemctl restart ecobot.service`
3. Kontak developer untuk bantuan teknis

---

Happy Administrating! 🚀
