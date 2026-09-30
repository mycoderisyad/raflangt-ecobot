# Keamanan API EcoBot

- Login admin memakai perbandingan constant-time dan menerbitkan JWT HS256 dengan masa berlaku terbatas. Endpoint admin mewajibkan `Authorization: Bearer ...`.
- Login dibatasi ke 5 percobaan per menit dan 20 per jam per alamat klien. Pembatas ini berada di memori proses; jalankan satu worker sesuai konfigurasi polling/reminder.
- Di production, `API_SECRET_KEY` harus berisi setidaknya 32 karakter acak dan password admin (`ADMIN_PASSWORD`) tidak boleh kosong atau memakai nilai contoh.
- CORS memakai origin yang tercantum di `CORS_ORIGINS`. Mode production tidak membuka origin secara default.
- Telegram webhook menolak secret yang hilang atau tidak cocok. Polling memeriksa apakah webhook masih terdaftar agar kedua mode tidak berjalan bersamaan.
- Pesan grup/channel Telegram diabaikan; broadcast dan reminder hanya menargetkan ID chat pribadi numerik.
- Respons admin memakai response models agar nilai internal seperti password, API keys, dan connection string tidak ikut keluar.
- Endpoint hapus user mengembalikan konflik bila percakapan/klasifikasi terkait ada; gunakan `PATCH` untuk menonaktifkan akun dan mempertahankan riwayat.

Simpan `.env` secara privat dan ganti semua rahasia contoh sebelum server dapat diakses dari jaringan publik. Dokumentasi endpoint tersedia pada `/docs` saat server aktif.
