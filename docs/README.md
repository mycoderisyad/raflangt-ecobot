# Dokumentasi EcoBot

Dokumentasi interaktif lama diganti dengan OpenAPI FastAPI di `/docs`. Halaman ini mencatat arsitektur dan API backend.

## Arsitektur

```text
Telegram polling / webhook
          ↓
FastAPI routers → orchestrator → AI agent / Telegram Bot API
          ↓                         ↓
       PostgreSQL                Resend / PDF
```

`src/api` berisi route dan skema HTTP. `src/core` mengatur intent dan alur pesan. `src/ai` mengelola prompt dan provider. `src/database` memakai PostgreSQL melalui `psycopg2`; migrasi berjalan dari CLI. `src/services` berisi operasi admin, laporan, reminder, registrasi, dan polling Telegram. Semua route yang melakukan operasi sinkron dideklarasikan sebagai fungsi sinkron FastAPI.

## Endpoint publik

| Method | Path | Tujuan |
|---|---|---|
| `GET` | `/` | Nama aplikasi dan status proses |
| `GET` | `/health` | Pemeriksaan liveness sederhana |
| `POST` | `/webhook/telegram` | Menerima Telegram Update saat `TELEGRAM_MODE=webhook` |

Mode webhook wajib memiliki `TELEGRAM_WEBHOOK_SECRET`. Mode polling mengambil update dari Bot API dan mengabaikan webhook. Bila webhook masih terpasang, hapus dengan `python manage.py telegram:webhook:delete` sebelum menyalakan mode polling.

## API admin

Login: `POST /api/v1/auth/login` dengan JSON `username` dan `password`. Respons memuat bearer token yang berlaku 60 menit. Kirim token pada header `Authorization: Bearer <token>` untuk endpoint admin.

| Area | Endpoint |
|---|---|
| Akun admin | `GET /api/v1/auth/me` |
| Dashboard | `GET /api/v1/dashboard` |
| Analitik | `GET /api/v1/analytics` |
| Pengguna | `/api/v1/users` dengan `GET`, `POST`; `/api/v1/users/{user_id}` dengan `GET`, `PATCH`, `DELETE` |
| Titik pengumpulan | `/api/v1/locations` dan `/api/v1/locations/{id}` dengan operasi CRUD |
| Jadwal | `/api/v1/schedules` dan `/api/v1/schedules/{id}` dengan operasi CRUD |
| Siaran Telegram | `GET /api/v1/broadcast/audience`, `POST /api/v1/broadcast` |
| Laporan | `POST /api/v1/reports/send` |
| Konfigurasi aman | `GET /api/v1/settings` |

Endpoint lengkap beserta skema, contoh validasi, dan kemungkinan respons tersedia di `/docs` saat server aktif. Kode status umum: `401` token tidak ada/tidak valid, `404` record tidak ditemukan, `409` record bertabrakan atau terhubung ke riwayat, dan `422` body tidak valid.

## Data dan kompatibilitas

- Nilai identitas user di database tetap disimpan pada kolom `users.phone_number` demi kompatibilitas foreign key; API menamainya `user_id`.
- Catatan jadwal lama yang digabungkan dalam alamat dipindahkan ke kolom baru `notes`. Alamat dan teks catatan dipertahankan.
- Tabel `telegram_updates` menyimpan update Telegram yang telah diproses agar webhook yang dikirim ulang tidak membalas dua kali.
- Tabel `schema_migrations` mencatat file migrasi yang telah diterapkan. `db:migrate` aman dijalankan berulang; migrasi tidak berjalan di startup server.
- Penghapusan user yang sudah memiliki interaksi atau klasifikasi menghasilkan `409`; gunakan status nonaktif agar riwayat tetap terjaga.

## Rekomendasi foto dan laporan titik sampah

Sesudah klasifikasi foto, rekomendasi mencocokkan kategori dengan titik penerimaan dan jadwal aktif di PostgreSQL. Laporan warga dimulai lewat teks atau caption foto, lalu foto dan lokasi Telegram dimasukkan ke satu laporan. Draft menunggu langkah berikutnya selama 24 jam. Pengurus/admin terdaftar menerima foto dan tautan peta; admin memperbarui status melalui API.

Endpoint admin:

- GET /api/v1/site-reports dengan filter status opsional
- GET /api/v1/site-reports/{id}/photo untuk foto
- PATCH /api/v1/site-reports/{id}/status untuk acknowledged, resolved, atau rejected
- DELETE /api/v1/site-reports/{id} untuk menghapus laporan yang sudah resolved/rejected

Foto laporan tersimpan di PostgreSQL sampai admin menghapusnya.

## Konfigurasi

Salin `.env.example` ke `.env`. Variabel utama:

| Variable | Kegunaan |
|---|---|
| `DATABASE_URL` | Koneksi PostgreSQL lokal |
| `AI_PROVIDER`, `AI_API_KEY`, `AI_MODEL` | Provider/model AI |
| `TELEGRAM_ENABLED`, `TELEGRAM_BOT_TOKEN` | Mengaktifkan dan mengautentikasi bot |
| `TELEGRAM_MODE` | `polling` untuk lokal atau `webhook` untuk URL HTTPS publik |
| `TELEGRAM_WEBHOOK_SECRET` | Header verifikasi webhook |
| `API_SECRET_KEY` | Kunci penandatangan JWT; gunakan string acak minimal 32 karakter |
| `ADMIN_USERNAME`, `ADMIN_PASSWORD` | Kredensial login API admin; nama legacy `ADMIN_PANEL_*` tetap dibaca |
| `JWT_TTL_SECONDS` | Umur token, default 3600 detik |
| `CORS_ORIGINS` | Origin frontend yang diizinkan, dipisahkan koma |
| `TIMEZONE` | Zona waktu reminder, default `Asia/Jakarta` |
| `RESEND_API_KEY`, `EMAIL_FROM`, `EMAIL_TO` | Pengiriman laporan email |

Mode production menolak secret dan password kosong, default, atau terlalu lemah. Mode development mengeluarkan peringatan agar server hanya dipakai di localhost sampai rahasia lokal diganti.
