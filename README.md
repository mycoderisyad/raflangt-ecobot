# EcoBot API

Backend FastAPI untuk chatbot edukasi pengelolaan sampah. Warga berinteraksi lewat Telegram untuk tanya jawab, mengirim foto sampah untuk klasifikasi AI, dan menerima pengingat jadwal. Backend juga menyediakan API admin untuk UI terpisah.

## Stack dan fitur

- FastAPI dan Uvicorn, dengan dokumentasi OpenAPI di `/docs`.
- PostgreSQL untuk pengguna, interaksi, percakapan, jadwal, lokasi, dan klasifikasi sampah.
- Telegram Bot API melalui long polling lokal atau webhook HTTPS.
- Gemini/OpenAI untuk percakapan dan analisis foto.
- API admin berbasis bearer JWT untuk pengguna, titik pengumpulan, jadwal, statistik, laporan, dan broadcast.
- Laporan PDF dan email melalui Resend.

## Menjalankan secara lokal (Windows)

Prasyarat: Python 3.12+, PostgreSQL lokal, token Telegram, dan API key AI untuk fitur percakapan/klasifikasi.

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Isi `.env`: `DATABASE_URL`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ENABLED=true`, `TELEGRAM_MODE=polling`, `AI_API_KEY`, `API_SECRET_KEY`, `ADMIN_USERNAME`, dan `ADMIN_PASSWORD`. Buat secret acak dengan:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Gunakan hasil acak untuk `API_SECRET_KEY` dan `TELEGRAM_WEBHOOK_SECRET`; ganti juga password admin. API development mengikat ke localhost.

Siapkan tabel dan data contoh:

```powershell
python manage.py db:setup
```

Untuk database yang sudah berisi data, jalankan `python manage.py db:migrate` agar perubahan skema diterapkan. Migrasi menambah kolom catatan jadwal dan tabel deduplikasi update Telegram; tidak menghapus data.

Periksa token bot dan mulai server:

```powershell
python manage.py telegram:check
python main.py
```

Buka `http://localhost:8000/health` dan `http://localhost:8000/docs`. Kirim pesan ke bot Telegram untuk menguji balasan. Jalankan satu proses server agar worker polling dan pengingat tidak berjalan ganda.

Jika bot sebelumnya menggunakan webhook, hapus webhook sebelum polling:

```powershell
python manage.py telegram:webhook:info
python manage.py telegram:webhook:delete
```

## Telegram webhook

Webhook memerlukan URL publik HTTPS. Atur `TELEGRAM_MODE=webhook` dan `TELEGRAM_WEBHOOK_SECRET`, daftarkan URL, lalu jalankan server:

```powershell
python manage.py telegram:webhook:set https://domain-publik.example
python main.py
```

Telegram mengirim update ke `POST /webhook/telegram` beserta header secret. Polling dan webhook tidak bisa aktif bersamaan untuk bot yang sama.

## API admin

Login dengan kredensial dari `.env`:

```http
POST /api/v1/auth/login
Content-Type: application/json

{"username":"admin","password":"..."}
```

Pakai `access_token` sebagai `Authorization: Bearer <token>`. Token berlaku 60 menit secara default. Seluruh endpoint admin dan bentuk JSON-nya tersedia di `/docs` setelah server berjalan.

| Area | Endpoint |
|---|---|
| Identitas | `POST /api/v1/auth/login`, `GET /api/v1/auth/me` |
| Ringkasan | `GET /api/v1/dashboard`, `GET /api/v1/analytics`, `GET /api/v1/settings` |
| Pengguna | `GET/POST /api/v1/users`, `GET/PATCH/DELETE /api/v1/users/{user_id}` |
| Lokasi | `GET/POST /api/v1/locations`, `GET/PATCH/DELETE /api/v1/locations/{id}` |
| Jadwal | `GET/POST /api/v1/schedules`, `GET/PATCH/DELETE /api/v1/schedules/{id}` |
| Broadcast | `GET /api/v1/broadcast/audience`, `POST /api/v1/broadcast` |
| Laporan | `POST /api/v1/reports/send` |
| Kesehatan | `GET /health` |

`user_id` adalah ID chat pribadi Telegram. Baris pengguna lama tetap tersimpan; hanya ID numerik yang menjadi penerima pesan Telegram. Pengguna dengan riwayat yang terhubung tidak dapat dihapus permanen; nonaktifkan lewat `PATCH /api/v1/users/{user_id}`.

## Perintah CLI

```text
python manage.py db:create
python manage.py db:migrate
python manage.py db:seed
python manage.py db:setup
python manage.py db:status
python manage.py telegram:check
python manage.py telegram:webhook:set [https://domain-publik.example]
python manage.py telegram:webhook:info
python manage.py telegram:webhook:delete
```

Seed dapat dijalankan ulang tanpa menggandakan jadwal contoh. Migrasi berlangsung melalui CLI dan tidak dieksekusi saat server dimulai.

## Konfigurasi UI terpisah

`CORS_ORIGINS` menerima daftar origin frontend yang dipisahkan koma. Dalam development, origin Vite `http://localhost:5173` dan `http://127.0.0.1:5173` menjadi default. Atur origin deployment eksplisit; kredensial server dan secret bot tidak pernah dikirimkan sebagai konfigurasi frontend.

Referensi rinci ada di [dokumentasi lokal](docs/README.md) dan [catatan keamanan](docs/security.md).
