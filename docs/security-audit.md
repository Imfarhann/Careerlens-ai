# Audit Keamanan — CareerLens AI (Fase 6)

Tanggal audit: 10 November 2026. Lingkup: backend FastAPI, konfigurasi Docker,
dan penggunaan data pribadi pada CV.

## Ringkasan temuan

| # | Area | Temuan | Tingkat | Status |
|---|---|---|---|---|
| 1 | JWT secret | Default contoh dipakai tanpa peringatan; aplikasi tetap start di production. | Tinggi | Diperbaiki — `validate_runtime()` menolak start jika production memakai secret contoh/<32 karakter. |
| 2 | CORS | Origin dari config, tetapi nilai compose di-hardcode dan wildcard belum ditolak. | Sedang | Diperbaiki — `CORS_ORIGINS` dapat dikonfigurasi; wildcard ditolak di production; method/header dibatasi. |
| 3 | Rate limit | Tidak ada pembatasan percobaan login/register. | Tinggi | Diperbaiki — limiter in-memory per IP untuk `/auth/login` dan `/auth/register` (default 10/menit) + test. |
| 4 | PII di log | Tidak ditemukan logging aplikasi yang memuat data pribadi. | — | Tidak ada kebocoran; aturan "jangan log PII" ditambahkan ke AGENTS.md. |
| 5 | Ownership | Semua endpoint data memfilter pemilik. | — | Terverifikasi; lihat tabel di bawah. |
| 6 | Cascade hapus | `DELETE /cv` mengandalkan cascade; `job_matches` tidak punya relationship ORM. | Sedang | Diperbaiki untuk hapus akun dengan delete eksplisit berurutan; `DELETE /cv` tetap mengandalkan cascade DB/ORM. |
| 7 | Hapus akun | Belum tersedia. | Sedang | Diperbaiki — `DELETE /auth/me` + tombol frontend + test. |
| 8 | Token di localStorage | Rentan jika ada XSS. | Rendah | Diterima untuk MVP; mitigasi masa depan: httpOnly cookie. |
| 9 | Container | Berjalan sebagai root; kredensial DB default untuk dev. | Rendah | Diterima untuk demo lokal; hardening deployment disarankan. |
| 10 | Upload | Belum ada pemindaian malware. | Rendah | Diterima untuk MVP; validasi tipe/ukuran/magic bytes sudah ada. |

## Ownership endpoint data

| Endpoint | Cek ownership | Catatan |
|---|---|---|
| `POST /auth/register`, `POST /auth/login`, `GET /health` | Publik | Tidak mengembalikan data user lain. |
| `GET /auth/me` | Ya | User dari token. |
| `DELETE /auth/me` | Ya | Menghapus seluruh data milik user. |
| `POST /cv/upload` | Ya | CV ditulis atas `current_user`. |
| `DELETE /cv/{id}` | Ya | Filter `CV.user_id`; 404 jika bukan milik user. |
| `GET /profile/{id}`, `PUT /profile/{id}` | Ya | Join `CV.user_id`. |
| `POST /analysis/{cv_id}` | Ya | `_load_cv` memfilter pemilik. |
| `GET /analysis` | Ya | Join `CV.user_id`. |
| `GET /analysis/{id}` | Ya | Join `CV.user_id`. |
| `GET /analysis/{id}/compare/{other_id}` | Ya | Kedua analisis lewat `load_owned_analysis`. |
| `GET /jobs/match/{analysis_id}` | Ya | `load_owned_analysis`. |
| `GET /skills/gap/{analysis_id}` | Ya | `load_owned_analysis`. |
| `GET /dashboard/{analysis_id}` | Ya | `load_owned_analysis`. |

## Catatan implementasi

- Rate limiter bersifat in-memory dan per proses. Untuk deployment multi-worker
  atau multi-instance, ganti dengan Redis agar batas konsisten.
- `request.client.host` adalah IP koneksi langsung. Di belakang reverse proxy,
  konfigurasikan trusted proxy bila ingin memakai `X-Forwarded-For`.
- Pesan gagal login selalu generik (`Email atau password salah`) agar tidak
  membocorkan apakah email terdaftar.
- Tidak ada logging isi CV, email, nama, atau telepon di kode aplikasi.
